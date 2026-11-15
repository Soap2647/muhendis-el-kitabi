%% kisim_no: VI
%% kisim_ad: İşletim Sistemi & Mimari
%% bolum_no: 28
%% baslik: File System & I/O

## Giriş: Veri ancak doğru yoldan inerse kalıcıdır

Bir programın yaptığı işlerin çoğu sonunda bir dosyaya dokunur: bir günlük satırı yazılır, bir yapılandırma güncellenir, bir sensör kaydı diske inmeden önce tamponda bekler. Yazılımın dış dünyayla en çok konuştuğu yer burasıdır ve en sık yanlış anlaşıldığı yer de burasıdır. `fprintf` döndü, demek ki veri diskte mi? Hayır. `write` başarılı döndü, demek ki elektrik kesilse de bayt kaybolmaz mı? Hayır. Bu bölüm, bu iki "hayır" cevabının neden doğru olduğunu ve onlarla nasıl başa çıkılacağını anlatır.

Bölüm 2'de C dosya G/Ç'sini `fopen`, `fread` ve `fwrite` ile yapmıştın. Bu fonksiyonlar, işletim sisteminin asıl sözleşmesinin üstünde duran bir kaplamadır. Asıl sözleşme `open`, `read`, `write`, `lseek` ve `close` gibi sistem çağrılarıdır; bunların her biri çekirdeğe bir geçiş yapar. Bölüm 4'te `find`, `chmod` ve izin bitlerini kullandın; bu bölüm izinlerin arkasındaki dosyanın kendisine, yani inode'a, dizin girdilerine ve veri bloklarına iner.

Mülakatlarda "bir dosyayı güvenle nasıl güncellersin?" sorusu sık gelir ve cevap genellikle "geçici dosyaya yaz, `rename` et" ile bitmeye çalışır. Bu cevap doğrudur ama yetersizdir; neden işe yaradığını, hangi adımda `fsync` gerektiğini ve dizinin de ne zaman senkronize edilmesi gerektiğini bilmek gerekir. Savunma sanayiinde bu soru daha da somut bir hâl alır: uçuş kayıt cihazı güç kesintisinden sonra açıldığında son kaydın yarım mı, eksik mi, yoksa tamamen mi kayıtlı olduğunu bilmek zorundadır.

Bölüm boyunca bir dizi ölçüm yapacağız: tampon boyutunun okuma süresine etkisi, `fsync` gecikmesi, `mmap` ile `read` karşılaştırması, `poll` ile `epoll`'un ölçeklenmesi. Her ölçümün kodu kitapta, çıktısı da metinde. Ölçümler, aşağıda belirttiğimiz tek bir makinede alındı; sayıların kendisinden çok, neden o yönde çıktıklarını anlamak önemli.

::: not
Bu bölümdeki her çıktı, kitabın kodundan derlenip çalıştırılarak alındı. Sayılar makineye bağlıdır; kendi bilgisayarında farklı çıkacaktır. Okurun öğrenmesi gereken yön ve nedenlerdir: tampon büyüdükçe sistem çağrısı sayısı düşer, `fsync` disk gecikmesine bağlıdır, `O_APPEND` olmadan paralel yazmalar kayıt kaybettirir.
:::

**Ölçüm ortamı.** Bu bölümdeki ölçümler Windows 11 Pro üzerinde WSL2 ile alındı: Ubuntu 24.04.4, çekirdek 6.6.87.2-microsoft-standard-WSL2, gcc 13.3.0 (`-O2 -Wall -Wextra -std=c11`), 16 mantıksal çekirdek ve 15,6 GB RAM. Dosyalar `/home` altındaki ext4 sanal diskte (`/dev/sdd`, `data=ordered`) tutuldu; Windows tarafındaki `/mnt/c` (NTFS) ölçülmedi. sudo ve `strace` olmadığı için sistem çağrısı sayısı programların kendi sayaçlarıyla alındı. Her ölçüm birden çok turda yapıldı; tabloda en iyi ya da medyan değer verildi.

## 28.1 Dosya soyutlaması: her şey bir tanımlayıcı

Unix'in en eski fikirlerinden biri, bir süreç için dosyaların ve diğer G/Ç kaynaklarının tek bir arayüzle temsil edilmesidir. Süreç bir dosya açtığında çekirdek ona küçük bir tamsayı verir: **dosya tanımlayıcı (file descriptor, fd)**. Bu tamsayı, süreçin kendi fd tablosunda bir girdiyi gösterir. Açık bir dosya yerine boru (pipe), soket ya da bir aygıt da olsa, aynı `read`, `write` ve `close` çağrıları kullanılır.

Bu tasarımın gücü, programın hedefin ne olduğunu bilmeden yazılabilmesidir. Aşağıdaki tabloda üç standart fd görüyorsun; her süreç bu üçüyle başlar:

| fd | Ad | Varsayılan hedef |
|---|---|---|
| 0 | stdin | klavye ya da bir önceki komutun çıktısı |
| 1 | stdout | terminal ya da boru |
| 2 | stderr | terminal (genellikle tamponsuz) |

Bir süreç `open` çağrısıyla yeni bir dosya açtığında, çekirdek kullanılmayan en küçük numarayı verir. Üç standart fd dolu olduğu için ilk açılan dosya genellikle 3 numarayı alır; bunu aşağıdaki çıktıda görüyorsun. Bu, C'de `FILE *` ile çalışırken arka planda olan şeydir: `fopen`, bir fd açar ve onu bir `FILE` yapısında sarar. `FILE`, Bölüm 2'deki tampon katmanıdır; fd ise çekirdeğin verdiği gerçek tanıtıcıdır.

Aynı arayüz, sürücülerin de sistemi aynı şekilde genişletebilmesini sağlar. Bölüm 21'de gördüğün `struct file_operations`, her dosya türünün `read`, `write` ve `open` işlemlerini kendi fonksiyonlarıyla doldurmasına izin verir. Dosya sistemleri, borular ve aygıtlar bu tabloyu farklı doldurur; sistem çağrısı ise tabloya bakıp doğru fonksiyonu seçer. Bu, Bölüm 21'deki açık-kapalı ilkesinin (OCP) ve bağımlılık tersine çevirmenin (DIP) çekirdekteki en yaygın biçimidir. Bölüm 21'de C'de fonksiyon işaretçisi tablosu olarak gördüğün şey, burada tüm G/Ç'nin omurgasıdır.

## 28.2 G/Ç yığını: bir yazma kaç katmandan geçer

Programın `printf("merhaba")` dediğinde bu tek satır, birkaç katmanlı bir yolculuğa çıkar. Her katman bir öncekine yukarıdan bakar ve bir sonrakine istek iletir. Hangi katmanda ne kadar zaman harcandığını bilmek, performans sorunlarını teşhis etmenin ilk adımıdır.

![Şekil 28.1: G/Ç yığını. İstek kullanıcı programından aygıt sürücüsüne iner; her katman bir öncekinin ardından çalışır. Sağdaki notlar her katmanın rolünü özetler.](gorseller/b28_katmanlar.png)

Yukarıdan aşağıya şu katmanlar vardır:

1. **Kullanıcı programı.** `printf`, `fgets`, `fwrite` gibi çağrılar burada yapılır. Yalnızca bellek içinde bir işlev çağrısıdır.
2. **stdio tamponu.** `FILE` yapısının içindeki bellek bloğu. Yazmalar burada birikir; tampon dolunca ya da `fflush` çağrılınca çekirdeğe gider. Tampon, kullanıcı alanında olduğu için bu katmandaki yazma çekirdek geçişi yapmaz.
3. **Sistem çağrısı.** `read`, `write`, `fsync`. Bu, kullanıcı alanından çekirdeğe geçişin gerçekleştiği sınırdır. Her geçiş, durumu kaydetmeyi ve geri yüklemeyi gerektirdiği için maliyetlidir.
4. **VFS (sanal dosya sistemi).** Yolu çözer, dosyanın `inode` ve `dentry` nesnelerini bulur, işlemi doğru dosya sistemine yönlendirir.
5. **Sayfa önbelleği (page cache).** Dosya verisinin RAM'deki kopyası. Okumaların çoğu buradan karşılanır; yazmalar önce buraya yazılır ve sonra arka planda diske gider. Bölüm 25'teki sayfa kavramı bunun temelidir.
6. **Blok katmanı.** Bloklar için istekleri sıralar, birleştirir ve zamanlar.
7. **Aygıt sürücüsü.** Gerçek disk ya da SSD'nin denetleyicisiyle konuşur. Veri çoğunlukla DMA ile taşınır (bkz. 28.13).

Bu yığında iki sonuç önemlidir. Birincisi, `write` çağrısının döndüğü an verinin diske indiği anlamına gelmez; çoğu zaman yalnızca sayfa önbelleğine yazılmıştır. İkincisi, bir sistem çağrısının maliyeti ile bir bellek içi fonksiyon çağrısının maliyeti arasında büyük bir fark vardır. Bu iki gerçeği 28.6 ve 28.7'de ölçerek göreceğiz.

## 28.3 Unix sistem çağrıları: open, read, write, lseek, close

Beş çağrı, Unix G/Ç'sinin tamamını kapsar. `open` bir yolu fd'ye çevirir ve bayrakları (`O_RDONLY`, `O_WRONLY`, `O_CREAT`, `O_TRUNC`, `O_APPEND` gibi) belirler. `read` ve `write` bayt sayar; döndürdükleri değer, kaç baytın gerçekten işlendiğini söyler. `lseek` dosya ofsetini değiştirir veya sorgular. `close` fd'yi serbest bırakır.

Aşağıdaki program bu çağrıların davranışını adım adım gösterir. Önce yeni bir dosya açıp yazıyor, sonra ofseti sorguluyor, ardından `O_APPEND` bayrağıyla bir yazma yapıyor ve dosyayı okuyor. Son olarak kapalı bir fd'ye yazmanın hatasını gösteriyor.

```c
/* b28_1_temel.c: open, write, lseek, read, close ve O_APPEND */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

int main(void)
{
    const char *yol = "deneme.txt";
    unlink(yol);                        /* eski dosya varsa sil */

    int fd = open(yol, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    printf("ilk fd = %d\n", fd);

    ssize_t n = write(fd, "merhaba", 7);
    printf("write -> %zd\n", n);

    off_t p = lseek(fd, 0, SEEK_CUR);   /* ofseti sor, değiştirme */
    printf("lseek(SEEK_CUR) -> %ld\n", (long)p);
    close(fd);

    /* O_APPEND: her yazma önce dosya sonuna gider */
    fd = open(yol, O_WRONLY | O_APPEND);
    if (lseek(fd, 0, SEEK_SET) < 0) return 1;
    if (write(fd, " dunya", 6) != 6) return 1;
    close(fd);

    fd = open(yol, O_RDONLY);
    char buf[64] = {0};
    n = read(fd, buf, sizeof buf - 1);
    printf("read -> %zd, içerik=\"%s\"\n", n, buf);
    n = read(fd, buf, sizeof buf - 1);
    printf("EOF'ta read -> %zd\n", n);
    close(fd);

    if (write(fd, "x", 1) < 0)         /* kapalı fd: EBADF */
        printf("kapalı fd: errno=%d (%s)\n", errno, strerror(errno));
    return 0;
}
```

Programın çıktısı, her çağrının ne yaptığını doğrular:

```term
$ gcc -O2 -Wall -Wextra -std=c11 -o b28_1_temel b28_1_temel.c
```

```term
$ ./b28_1_temel
ilk fd = 3
write -> 7
lseek(SEEK_CUR) -> 7
read -> 13, içerik="merhaba dunya"
EOF'ta read -> 0
kapalı fd: errno=9 (Bad file descriptor)
```

Dikkat edilmesi gereken üç nokta var. Birincisi, `lseek(fd, 0, SEEK_SET)` ofseti başa aldı, ama `O_APPEND` bayrağı açık olduğu için `write` yine dosyanın sonuna yazdı. Bu bayrak, konumu yazmadan hemen önce sona çeker; ofset değerinin bir anlamı yoktur. İkincisi, dosya sonunda `read` sıfır döndürür; bu hatadan değil, EOF (dosya sonu) bilgisinden gelir. Üçüncüsü, kapalı bir fd'ye yazmak `-1` döndürür ve `errno` değeri `EBADF` olur. Hataları her zaman dönüş değerinden kontrol etmek, bu bölümün ilk kuralıdır; `errno` ise hatanın nedenini söyler.

## 28.4 Açık dosya tablosu ve inode: ofset neden paylaşılır

Bir fd'nin ne olduğunu sorduğumuzda çekirdeğin üç ayrı tabloyu birbirine bağladığını görürüz. Bu üçlü, dosya G/Ç'sinin en önemli yapısıdır ve mülakatlarda da sık sorulur.

- **Süreç fd tablosu.** Her süreçte bir tablo; girdileri fd numarasıyla indekslenir ve açık dosya tablosundaki bir girdiyi gösterir.
- **Açık dosya tablosu.** Çekirdek genelinde; her girdi (Linux'ta `struct file`) dosyanın açıldığı andaki durumunu tutar: ofset, açma bayrakları ve bir referans sayacı. Aynı dosya iki kez açıldığında iki ayrı girdi oluşur.
- **inode tablosu.** Dosyanın kalıcı meta verisi: boyut, izinler, veri bloklarının konumu. Dosyanın adı burada tutulmaz; ad, dizin girdisinde yaşar (28.9).

Bu ayrım, bir sonucu açıklar: `fork` sonrası iki süreç aynı açık dosya girdisini paylaşır ve dolayısıyla **ofset ortaktır**. Bunu bir kez birinin okuması, diğerinin kaldığı yerden devam etmesi demektir. Aşağıdaki program bunu iki durumda gösterir: fork sonrası paylaşılan fd ve iki ayrı `open` çağrısıyla açılmış fd.

```c
/* b28_4_ofset.c: fork sonrası paylaşılan dosya ofseti */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/wait.h>

int main(void)
{
    const char *harf = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    char buf[8];

    int w = open("harf.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (write(w, harf, 26) != 26) return 1;
    close(w);

    int fd = open("harf.txt", O_RDONLY);     /* açık dosya A */
    int fd2 = open("harf.txt", O_RDONLY);    /* ayrı açık dosya B */

    pid_t pid = fork();
    if (pid == 0) {
        if (read(fd, buf, 5) != 5) _exit(1);
        buf[5] = '\0';
        printf("çocuk fd okudu: %s\n", buf);
        fflush(stdout);
        _exit(0);
    }
    wait(NULL);

    if (read(fd, buf, 5) != 5) return 1;
    buf[5] = '\0';
    printf("ana fd okudu:   %s\n", buf);

    if (read(fd2, buf, 5) != 5) return 1;
    buf[5] = '\0';
    printf("fd2 okudu:      %s\n", buf);

    printf("lseek(fd)  = %ld\n", (long)lseek(fd, 0, SEEK_CUR));
    printf("lseek(fd2) = %ld\n", (long)lseek(fd2, 0, SEEK_CUR));
    close(fd);
    close(fd2);
    return 0;
}
```

Çıktı, paylaşımı ve ayrımı birlikte gösterir:

```term
$ ./b28_4_ofset
çocuk fd okudu: ABCDE
ana fd okudu:   FGHIJ
fd2 okudu:      ABCDE
lseek(fd)  = 10
lseek(fd2) = 5
```

Çocuk süreç ilk beş harfi okudu. Ana süreç beklediği için (`wait`), ofset 5'ten devam etti ve `FGHIJ`'yi okudu; yani çocuğun okuması ana sürecin ofsetini de ilerletti. Oysa `fd2` ayrı bir `open` ile açıldığı için kendi ofsetini taşır ve `ABCDE`'den başlar. Bölüm 26'da fd tablosunu süreç bazında, `dup2` ile fd yönlendirmesini ve `fork`'un kopyalama mantığını ayrıntılı göreceksin; burada yalnızca dosya tarafına bakıyoruz.

![Şekil 28.2: Süreç fd tablosu, açık dosya tablosu ve inode tablosu. Ana ve çocuk süreç aynı açık dosya girdisini (X) paylaşır, bu yüzden ofset ortaktır; ayrı açılan Y girdisinin ofseti bağımsızdır.](gorseller/b28_fd_tablolar.png)

Şekil 28.2 bu üçlüyü gösterir. Süreç A'nın fd 3'ü ile çocuğun fd 3'ü aynı X girdisine işaret eder; sayaç 2'dir, çünkü iki fd bu girdiyi referans eder. Y girdisinin sayacı 1'dir. Her iki açık dosya da aynı inode'a da bağlanabilir; bu, iki ayrı `open`'ın aynı dosyayı göstermesi anlamına gelir.

## 28.5 Kısa okuma ve kısa yazma

`read` ve `write` istenen baytın tamamını işlemeyebilir. Bu, hata değildir; sözleşmenin parçasıdır. `read(fd, buf, 8000)` çağrısı 1000 bayt döndürebilir ve bu, dosyanın bittiği anlamına gelmez. Kısa okuma (short read) ve kısa yazma (short write) şu durumlarda olur: boru ya da soket verisi parça parça gelirken, bir sinyal işlem ortasında kesildiğinde, dosya sonuna yaklaşıldığında ya da aygıt tek seferde daha az kabul ettiğinde.

Bu yüzden her G/Ç döngüsü, istenen miktarı alana kadar tekrar etmelidir. Aşağıdaki kod, bu döngüyü iki yardımcı fonksiyonla yazar: `tam_oku` ve `tam_yaz`. Her ikisi de `EINTR` durumunda (bir sinyal yüzünden kesilme) yeniden dener; EOF'a ulaşıldığında ya da gerçek bir hata olduğunda durur.

```c
/* b28_2_kisa_io.c: kısa okuma ve tam_oku / tam_yaz */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/wait.h>

/* Tüm n baytı okur; kısa okumada tekrar dener. */
ssize_t tam_oku(int fd, void *tampon, size_t n)
{
    size_t toplam = 0;
    while (toplam < n) {
        ssize_t r = read(fd, (char *)tampon + toplam, n - toplam);
        if (r < 0) {
            if (errno == EINTR) continue;   /* sinyal: tekrar dene */
            return -1;                       /* gerçek hata */
        }
        if (r == 0) break;                   /* EOF */
        toplam += (size_t)r;
    }
    return (ssize_t)toplam;
}

/* Tüm n baytı yazar; kısa yazmada tekrar dener. */
ssize_t tam_yaz(int fd, const void *tampon, size_t n)
{
    size_t toplam = 0;
    while (toplam < n) {
        ssize_t w = write(fd,
                          (const char *)tampon + toplam, n - toplam);
        if (w < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        toplam += (size_t)w;
    }
    return (ssize_t)toplam;
}
```

Asıl test, bir boru üzerinden parça parça gelen veridir. Çocuk süreç her 30 milisaniyede bir 1000 baytlık parça yazar; ana süreç bir kerede 8000 bayt istemesine rağmen ilk `read` yalnızca 1000 bayt alır. Kalan veriyi `tam_oku` toplar:

```c
int main(void)
{
    int boru[2];
    if (pipe(boru) < 0) { perror("pipe"); return 1; }

    pid_t pid = fork();
    if (pid == 0) {                      /* yazıcı çocuk */
        close(boru[0]);
        char parca[1000];
        memset(parca, 'a', sizeof parca);
        for (int i = 0; i < 8; i++) {
            tam_yaz(boru[1], parca, sizeof parca);
            usleep(30000);               /* 30 ms bekle */
        }
        close(boru[1]);
        _exit(0);
    }
    close(boru[1]);

    char tampon[8000];
    ssize_t r = read(boru[0], tampon, sizeof tampon);
    printf("tek read: istenen=%zu, dönen=%zd\n", sizeof tampon, r);

    ssize_t kalan = tam_oku(boru[0], tampon + r, sizeof tampon - r);
    printf("tam_oku kalan=%zd bayt okudu\n", kalan);

    ssize_t son = tam_oku(boru[0], tampon, 1);
    printf("EOF sonrası tam_oku=%zd\n", son);

    close(boru[0]);
    wait(NULL);
    return 0;
}
```

```term
$ ./b28_2_kisa_io
tek read: istenen=8000, dönen=1000
tam_oku kalan=7000 bayt okudu
EOF sonrası tam_oku=0
```

İlk `read` çağrısının 1000 bayt döndürmesi, çocuğun ilk parçayı yazmasından hemen sonra okunmasının sonucudur; bu, zamanlamaya bağlı olsa da belirleyici bir davranıştır çünkü parça 30 milisaniyede bir gelir. `tam_oku` kalan 7000 baytı toplar. Sonraki çağrı, çocuk kapattığı için sıfır döndürür: bu EOF'tur.

Linux'ta bir borunun `PIPE_BUF` (genellikle 4096 bayt) değerinden küçük yazmaları atomiktir; yani bu boyuta kadar olan tek bir `write`, başka bir sürecin yazmasıyla iç içe geçmez. Bu, genel bir Linux ve POSIX bilgisidir ve yalnızca borular için geçerlidir; diskteki dosyalar için aynı garanti yoktur. Bunu çözümlü Örnek 3'te eşzamanlı yazmalarla göreceksin.

**Kısa yazma için de aynı mantık geçerlidir.** `tam_yaz` döngüsü, çekirdeğin yalnızca bir kısmını kabul ettiği durumda kalan kısmı tekrar gönderir. Kısa yazmayı yakalamadan yazılmış bir kod, büyük çıktılarda sessizce veri kaybeder ve bu hata yalnızca yük altında ortaya çıkar.

## 28.6 Arabellekleme: stdio, çekirdek önbelleği ve tampon boyutu

G/Ç'de tampon iki yerde yaşar. Birincisi kullanıcı alanındaki stdio tamponudur (28.2'de 2 numaralı katman); ikincisi çekirdeğin sayfa önbelleğidir (5 numaralı katman). Birincisi sistem çağrısı sayısını azaltır, ikincisi diske gitmeyi geciktirir. İkisini ayırt etmek, "neden çıktım hiç görünmedi?" ve "neden disk hızlı ama program yavaş?" sorularının cevabıdır.

### Stdio tamponu ve fork tuzağı

stdio tamponunun davranışı çıktı hedefine bağlıdır. Terminale yazılırken çıktı genellikle satır tamponludur: `\n` görünce boşaltılır. Bir boruya ya da dosyaya yazılırken ise tam tamponludur: tampon dolana kadar (genellikle dosyanın blok boyutu kadar, ext4'te 4096 bayt) ya da program bitene kadar bekler. Bu fark, bir hata ayıklama yanlışlığının kaynağıdır: program çökmeden önce `printf` çıktısı neden yok?

Asıl tuzak `fork` ile birlikte gelir. `fork` anında tampon da kopyalanır; çocuk ve ana süreç, kendi tamponlarında aynı bekleyen veriyi taşır. İkisi de çıkışta tamponlarını boşalttığında veri iki kez yazılır. Aşağıdaki program bunu üç kipte çalıştırır: varsayılan, `fflush` ile fork öncesi boşaltma ve satır tamponu (`setvbuf`).

```c
/* b28_3_stdio_fork.c: stdio tamponu ve fork: çift çıktı */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char **argv)
{
    const char *kip = argc > 1 ? argv[1] : "varsayilan";

    if (strcmp(kip, "satir") == 0)
        setvbuf(stdout, NULL, _IOLBF, 0);   /* satır tamponu */

    printf("merhaba\n");
    if (strcmp(kip, "flush") == 0)
        fflush(stdout);                     /* fork'tan önce boşalt */

    /* tampon iki sürece kopyalanır */
    pid_t pid = fork();
    if (pid < 0)
        return 1;
    if (pid == 0)
        return 0;                  /* çocuk: çıkışta boşaltır */

    wait(NULL);
    return 0;                       /* ana: çıkışta boşaltır */
}
```

Çıktıyı görmek için programı bir boruya bağladık; böylece stdout tam tamponlu olur:

```term
$ ./b28_3_stdio_fork | cat
merhaba
merhaba
```

Aynı programı `fflush` ve satır tamponu kipleriyle çalıştırınca çıktı şöyle değişir:

```term
$ ./b28_3_stdio_fork flush | cat
merhaba
```

```term
$ ./b28_3_stdio_fork satir | cat
merhaba
```

Varsayılan kipte `merhaba` iki kez çıktı. `fflush` çağrısı fork'tan önce tamponu boşaltınca tek satır kaldı. Satır tamponu (`_IOLBF`) da `\n` gördüğü için fork öncesi boşaltır ve tek satır üretir. Bu ayrımı çözümlü Örnek 2'de elle izleyeceksin.

### Tampon boyutu: sistem çağrısı sayısı ve süre

Tamponun boyutu, `read` çağrısı sayısını doğrudan belirler. Bir dosyayı 1 baytlık tamponla okumak, dosya boyutu kadar sistem çağrısı yapmak demektir; her biri bir çekirdek geçişidir. Aşağıdaki program 8 MiB'lık bir dosyayı 1 bayttan 1 MiB'a kadar farklı tampon boyutlarıyla okur, sistem çağrısı sayısını sayar ve en iyi üç turu alır. Son satırda aynı dosya `fgetc` ile bayt bayt, stdio tamponu üzerinden okunur.

Sistem çağrısı sayısını sayan kendi sayacımızdır: sudo olmadığı ve `strace` kurulu olmadığı için dış bir araç kullanamadık. Dosya, WSL'in ext4 dosya sisteminde ve sayfa önbelleğinde (sıcak önbellek) tutulur, yani disk gecikmesi ölçülmez; yalnızca çekirdek geçişinin ve kopyalamanın maliyeti görülür.

```c
/* b28_7_tampon_olcum.c: read() tampon boyutunun etkisi.
 * Kullanım: ./b28_7_tampon_olcum veri.bin
 * Çıktı: tur,boyut,syscall,sure_ms (en iyi 3 tur) */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

#define TUR 3

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

/* Dosyayı 'boyut' parçalar hâlinde okur; çağrı sayısını döner. */
static long oku_parcali(const char *yol, size_t boyut,
                        unsigned *sag)
{
    char *tampon = malloc(boyut);
    int fd = open(yol, O_RDONLY);
    long cagri = 0;
    unsigned toplam = 0;
    ssize_t r;
    while ((r = read(fd, tampon, boyut)) > 0) {
        cagri++;
        /* optimizasyon engeli: her sayfadan bir bayt al */
        for (ssize_t i = 0; i < r; i += 4096)
            toplam += (unsigned char)tampon[i];
    }
    close(fd);
    free(tampon);
    *sag = toplam;
    return cagri;
}
```

Dosyayı okuyan yardımcı fonksiyon ve ölçüm döngüsü aşağıda. Döngüdeki `i += 4096` adımı, derleyicinin okumayı yok saymasını engellemek için sayfa başına bir bayt toplar.

```c
/* stdio: fgetc ile bayt bayt; glibc kendi tamponunu kullanır. */
static void oku_fgetc(const char *yol, unsigned *sag)
{
    FILE *f = fopen(yol, "rb");
    unsigned toplam = 0;
    int c;
    while ((c = fgetc(f)) != EOF)
        toplam += (unsigned char)c;
    fclose(f);
    *sag = toplam;
}

int main(int argc, char **argv)
{
    const char *yol = argc > 1 ? argv[1] : "veri.bin";
    size_t boyutlar[] = {1, 16, 64, 256, 1024, 4096, 16384,
                         65536, 262144, 1048576};
    int m = sizeof boyutlar / sizeof boyutlar[0];
    unsigned sag = 0;

    printf("tur,boyut,syscall,sure_ms\n");
    for (int k = 0; k < m; k++) {
        double en_iyi = 1e18;
        long cagri = 0;
        for (int t = 0; t < TUR; t++) {
            double t0 = simdi_ms();
            cagri = oku_parcali(yol, boyutlar[k], &sag);
            double dt = simdi_ms() - t0;
            if (dt < en_iyi) en_iyi = dt;
        }
        printf("read,%zu,%ld,%.2f\n", boyutlar[k], cagri, en_iyi);
    }

    double en_iyi = 1e18;
    for (int t = 0; t < TUR; t++) {
        double t0 = simdi_ms();
        oku_fgetc(yol, &sag);
        double dt = simdi_ms() - t0;
        if (dt < en_iyi) en_iyi = dt;
    }
    printf("stdio_fgetc,1,-1,%.2f\n", en_iyi);
    fprintf(stderr, "# sağ=%u\n", sag);
    return 0;
}
```

Bu programın çıktısı, ölçümün ham hâlidir:

```term
$ ./b28_7_tampon_olcum veri.bin
tur,boyut,syscall,sure_ms
read,1,8388608,4647.49
read,16,524288,309.35
read,64,131072,78.65
read,256,32768,19.24
read,1024,8192,5.05
read,4096,2048,1.70
read,16384,512,0.77
read,65536,128,0.53
read,262144,32,0.43
read,1048576,8,0.55
stdio_fgetc,1,-1,22.62
```

Sonuçları özetleyen tablo (üç turdan en iyi süre):

| Tampon (bayt) | read çağrısı | süre (ms) | çağrı başına (µs, yaklaşık) |
|---|---|---|---|
| 1 | 8 388 608 | 4 647 | 0,55 |
| 16 | 524 288 | 309 | 0,59 |
| 256 | 32 768 | 19,2 | 0,59 |
| 4 096 | 2 048 | 1,70 | 0,83 |
| 65 536 | 128 | 0,53 | 4,1 |
| 1 048 576 | 8 | 0,55 | 69 |
| stdio fgetc (1 bayt) | — | 22,6 | — |

Tablo, iki gerçeği açıkça gösterir. Birincisi, küçük tamponlarda (1 bayttan 4 KiB'a kadar) çağrı başına maliyet yaklaşık 0,55–0,85 µs ile neredeyse sabittir; süre, sistem çağrısı sayısıyla orantılıdır. İkincisi, tampon büyüdükçe çağrı sayısı düşer, ama her çağrının içindeki kopyalama işi büyür: 1 MiB'lık bir çağrı yaklaşık 69 µs sürer, bu da kabaca 15 GB/s'lik bir kopyalama hızına karşılık gelir. Bu yüzden 64 KiB civarında kazanç belirgin biçimde azalır ve sonrası yalnızca küçük iyileşmelerdir.

Ölçüm birkaç çalıştırmada 1 bayt için 4,6 ile 5,3 saniye arasında değişti. Bu, makine yükü ve önbellek durumuna bağlı normal bir dalgalanmadır; bu yüzden her değer üç turun en iyisidir.

Stdio'nun `fgetc` ile okuması (22,6 ms) 1 baytlık `read` döngüsünden (4647 ms) yaklaşık iki yüz kat hızlıdır. Nedeni, `fgetc` her bayt için bir sistem çağrısı yapmaz; glibc tamponu tek bir `read` ile doldurur ve `fgetc` bu tampondan okur. Bu, Bölüm 2'deki `FILE` yapısının tam amacıdır.

![Şekil 28.3: 8 MiB dosyanın read() ile okunma süresi, tampon boyutuna göre (log-log). Kesikli çizgi stdio fgetc ile bayt bayt okumanın süresidir.](gorseller/b28_tampon_olcum.png)

Şekil 28.3, aynı veriyi log-log ölçekte gösterir. Eğrinin 1 bayttan 4 KiB'a kadar neredeyse düz bir eğim izlemesi, süreyi belirleyen şeyin çağrı sayısı olduğunu doğrular. Bu eğrinin dirseği, tamponun sistem çağrısı maliyetini kopyalama maliyetinin altına düşürdüğü noktadır.

## 28.7 Kalıcılık: fsync, fdatasync ve yazma sırası

`write` çağrısı döndüğünde verinin sayfa önbelleğine girdiğini biliyorsun (28.2). Veri bu noktada hâlâ RAM'de olabilir; elektrik kesilirse kaybolur. Veriyi diske kalıcı olarak göndermek için `fsync(fd)` çağrılır: çekirdek bu dosyanın kirli sayfalarını ve gerekli meta veriyi (boyut, blok konumları) diske yazana kadar döner. `fdatasync(fd)` ise meta verinin yalnızca gerekli kısmını yazar; boyut değişmemişse zaman damgası gibi alanları atlayabilir (genel bilgi).

Bu iki çağrı arasındaki fark, bu makinede ölçümlerin gösterdiği kadar büyük değildir; ikisi de disk yazma gecikmesine bağlıdır. Önemli olan, `fsync`'in disk gecikmesi kadar pahalı olduğudur ve bunu bir döngüde her yazmada çağırmak performansı çökertir.

Aşağıdaki program 4 KiB'lık bir bloğu 300 kez yazar; her yazmayı üç kipte ölçer: yalnız `write`, `write` + `fdatasync`, `write` + `fsync`. Her kipte 20 tur ısınma yapılır ve bunlar kaydedilmez.

```c
/* b28_6_fsync_olcum.c: 4 KiB yazma ve kalıcılık gecikmesi.
 * Çıktı: mod,iter,us (her satır bir yazma turu) */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

#define N      300     /* ölçülen tur sayısı */
#define ISIN   20      /* ısınma turları, yazılmaz */
#define BLOK   4096

static double simdi_us(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e6 + t.tv_nsec / 1e3;
}
```

Ölçüm döngüsü, her kipte ve her turda süreyi mikrosaniye hassasiyetle alır:

```c
/* kip: 0 yalnız write, 1 fdatasync, 2 fsync */
static void olc(const char *mod, int kip)
{
    static char blok[BLOK];
    memset(blok, 'x', sizeof blok);
    int fd = open("fsync_test.dat",
                  O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); exit(1); }

    for (int i = 0; i < N + ISIN; i++) {
        double t0 = simdi_us();
        if (write(fd, blok, BLOK) != BLOK) {
            perror("write"); exit(1);
        }
        if (kip == 1 && fdatasync(fd) < 0) {
            perror("fdatasync"); exit(1);
        }
        if (kip == 2 && fsync(fd) < 0) {
            perror("fsync"); exit(1);
        }
        double t1 = simdi_us();
        if (i >= ISIN)
            printf("%s,%d,%.1f\n", mod, i - ISIN, t1 - t0);
    }
    close(fd);
    unlink("fsync_test.dat");
}

int main(void)
{
    printf("mod,iter,us\n");
    olc("yalniz_write", 0);
    olc("fdatasync", 1);
    olc("fsync", 2);
    return 0;
}
```

Programın çıktısını `./b28_6_fsync_olcum > fsync.csv` ile bir dosyaya yazdık; her satır bir tur (`mod,iter,us`). Toplam 900 satırın özeti şu tabloda:

| Kip | Medyan (µs) | 95. yüzdelik (µs) | En büyük (µs) |
|---|---|---|---|
| yalnız write | 4 | 7 | 32 |
| write + fdatasync | 1 325 | 1 935 | 2 204 |
| write + fsync | 1 484 | 2 190 | 3 051 |

Tablo, yazma ile kalıcılık arasındaki uçurumu gösterir: yalnız `write` yaklaşık 4 mikrosaniyede biter, oysa her yazmadan sonra `fsync` yaklaşık 1,4 milisaniye sürer; yani kalıcılık üç yüzden fazla kat pahalıdır. Bu sayı, WSL2'nin sanal diskine ve ana makinenin önbelleğine bağlıdır. Gerçek bir SSD'de veya başka bir sanal diskte rakamlar farklı olacaktır; ama oran yönü ve nedeni aynıdır: `fsync` bir aygıt komutunun tamamlanmasını bekler.

Bu makinede `fdatasync` ile `fsync` arasında belirgin bir fark çıkmadı. Birkaç çalıştırmada `fdatasync` bazen daha yavaş, bazen daha hızlı çıktı; bu, farkın gürültü düzeyinde olduğunu gösterir. Dosya büyüdüğü için her iki çağrı da boyut meta verisini yazmak zorundadır; `fdatasync`'in tasarruf ettiği zaman damgası güncellemesi bu durumda ihmal edilebilir. Dolayısıyla "fdatasync her zaman daha hızlıdır" demek, bu ölçümde desteklenmez.

![Şekil 28.4: 300 yazma turu için 4 KiB yazma gecikmeleri (log ölçek). Yalnız write mikrosaniye, fdatasync ve fsync birkaç milisaniyenin altında birikir.](gorseller/b28_fsync_olcum.png)

### Yazma sırası: veri önce, kayıt sonra

`fsync` tek başına bir sıralama garantisi vermez; bir çok dosyalı güncellemede sıralamayı sen kurarsın. Kural basittir: önce veriyi `fsync` ile kalıcı yap, sonra onu işaret eden kaydı (commit, işaretçi, dizin girdisi) yaz ve onu da `fsync` ile kalıcı yap. Ters sırada yapılırsa, kayıt verinin henüz diske inmediği bir anda kalıcılaşabilir ve sonraki açılışta kayıt, var olmayan veriyi gösterir. Veritabanlarının günlüğü (WAL) bu kuralın en bilinen uygulamasıdır (Bölüm 33–35'te göreceksin).

## 28.8 Atomik dosya güncelleme

Bir yapılandırma dosyasını güncellemek, en yaygın ama en çok hata yapılan işlemlerden biridir. Dosyayı yerinde açıp sıfırlayıp yeniden yazarsan, yazma sırasında çökme olursa dosya yarım kalır: ne eski ne yeni, bozuk bir hâlde. Bunun karşılığı atomik güncellemedir: yeni içeriği geçici bir dosyaya yaz, kalıcı yap, sonra tek bir `rename` ile eskisinin yerine koy.

Atomik kalıp beş adımdan oluşur:

1. Geçici dosyayı aç ve yeni içeriği yaz.
2. Yazma bitene kadar devam et; kısa yazma döngüsü 28.5'teki `tam_yaz` gibi davranmalıdır.
3. `fsync(tmp)` ile geçici dosyanın verisini diske indir.
4. `rename(tmp, hedef)` ile dosyayı yer değiştir. Aynı dosya sisteminde `rename` tek adımdır: okuyan ya eski dosyayı, ya da yeni dosyayı görür; arası yoktur (POSIX sözleşmesi).
5. Yeni adın dizin girdisinin kalıcı olması için dizinin kendisini `fsync` et. `rename` bir dizin işlemidir; dizin senkronize olmadan çökme, eski adı geri getirebilir.

Aşağıdaki program bu kalıbı ve yerinde yazmayı çökme noktalarında sınar. Çökme, süreci `_exit` ile anında sonlandırarak simüle edilir: kısmi yazma, `fsync` öncesi, `rename` öncesi ve sonrası. Her denemede yapılandırma dosyasının eski ya da yeni sürümden biri olması gerekir; bunun dışındaki her durum bozuktur.

```c
/* b28_5_atomik.c: yerinde yazma ve atomik yazmanın çökme testi */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>

#define YOL   "yapi.conf"
#define ESKI  "surum=1 esik=10 aktif=1\n"
#define YENI  "surum=2 esik=25 aktif=1 yeni=abcdefgh\n"

/* Kırılgan yöntem: dosyayı yerinde aç, sıfırla, yaz. */
static void yerinde_yaz(const char *veri, size_t n, int kir)
{
    int fd = open(YOL, O_WRONLY | O_TRUNC | O_CREAT, 0644);
    size_t yarim = n / 2;
    if (write(fd, veri, yarim) < 0) _exit(2);
    if (kir == 1) _exit(7);            /* yarım yazıldı: çökme */
    if (write(fd, veri + yarim, n - yarim) < 0) _exit(2);
    close(fd);
}

/* Atomik yöntem: geçici dosya, fsync, rename, dizin fsync. */
static void atomik_yaz(const char *veri, size_t n, int kir)
{
    const char *tmp = YOL ".tmp";
    int fd = open(tmp, O_WRONLY | O_TRUNC | O_CREAT, 0644);
    size_t yarim = n / 2;
    if (write(fd, veri, yarim) < 0) _exit(2);
    if (kir == 1) _exit(7);            /* geçici dosya yarım */
    if (write(fd, veri + yarim, n - yarim) < 0) _exit(2);
    if (kir == 2) _exit(7);            /* tam yazıldı, fsync yok */
    if (fsync(fd) < 0) _exit(2);
    close(fd);
    if (kir == 3) _exit(7);            /* rename'den önce */
    if (rename(tmp, YOL) < 0) _exit(2);
    if (kir == 4) _exit(7);            /* rename'den sonra */
    int dfd = open(".", O_RDONLY);
    if (dfd >= 0) { fsync(dfd); close(dfd); }
}
```

Yerinde yazma, dosyayı `O_TRUNC` ile sıfırlar ve yazar; atomik yazma ise geçici dosya üzerinden çalışır. Çökme noktaları `kir` değişkeniyle seçilir:

```c
/* 0: ESKI, 1: YENI, -1: ne eski ne yeni (bozuk) */
static int dogrula(void)
{
    char tampon[128] = {0};
    int fd = open(YOL, O_RDONLY);
    if (fd < 0) return -1;
    ssize_t r = read(fd, tampon, sizeof tampon - 1);
    close(fd);
    if (r < 0) return -1;
    if (strcmp(tampon, ESKI) == 0) return 0;
    if (strcmp(tampon, YENI) == 0) return 1;
    return -1;
}

static void sifirla(void)
{
    int fd = open(YOL, O_WRONLY | O_TRUNC | O_CREAT, 0644);
    if (write(fd, ESKI, strlen(ESKI)) < 0) _exit(2);
    close(fd);
}
```

Denemeleri yürüten `main` her turda dosyayı eski sürümle yeniden kurar, bir çocuk süreçte yazmayı çalıştırır ve çocuğun sonucunu ana süreçte doğrular:

```c
int main(int argc, char **argv)
{
    int atomik = argc > 1 && strcmp(argv[1], "atomik") == 0;
    int deneme = 500;
    int eski = 0, yeni = 0, bozuk = 0;

    for (int i = 0; i < deneme; i++) {
        sifirla();
        int kir = i % 5;               /* 0..4: çökme noktası */
        /* yerinde yazmada yalnız 0 ve 1 noktaları var */
        if (!atomik && kir > 1) kir = 0;

        pid_t pid = fork();
        if (pid == 0) {
            if (atomik) atomik_yaz(YENI, strlen(YENI), kir);
            else        yerinde_yaz(YENI, strlen(YENI), kir);
            _exit(0);
        }
        int durum;
        waitpid(pid, &durum, 0);

        int s = dogrula();
        if (s == 0) eski++;
        else if (s == 1) yeni++;
        else bozuk++;
    }
    printf("yöntem=%s deneme=%d eski=%d yeni=%d bozuk=%d\n",
           atomik ? "atomik" : "yerinde", deneme, eski, yeni, bozuk);
    return 0;
}
```

```term
$ ./b28_5_atomik yerinde; ./b28_5_atomik atomik
yöntem=yerinde deneme=500 eski=0 yeni=400 bozuk=100
yöntem=atomik deneme=500 eski=300 yeni=200 bozuk=0
```

Sonuç açık: yerinde yazmada 500 denemenin 100'ü bozuk çıktı; bu, beşte birlik kısmi yazma noktasının (kir=1) doğrudan sonucudur. Atomik yazmada bozuk sonuç sıfırdır. Her çökme noktası ayrı ayrı şöyle sonuçlanır:

| Çökme noktası | Ne olur? | yapi.conf |
|---|---|---|
| 0: çökme yok | rename tamamlanır | YENİ |
| 1: geçici dosya yarım | rename hiç yapılmaz | ESKİ |
| 2: tam yazıldı, fsync yok | rename hiç yapılmaz | ESKİ |
| 3: fsync sonrası, rename öncesi | rename hiç yapılmaz | ESKİ |
| 4: rename sonrası | yeni ad görünür | YENİ |

![Şekil 28.5: Atomik güncelleme zaman çizelgesi. Yapılandırma dosyası, rename adımına kadar eski sürümünü korur; rename tek adımda yeni sürüme geçer.](gorseller/b28_atomik_zaman.png)

Burada dürüst bir sınır var. `_exit` yalnızca süreci sonlandırır; çekirdeğin sayfa önbelleğindeki yazmalar yine diske gider. Yani bu test, süreç çökmesine karşı atomikliği kanıtlar, ama **elektrik kesintisine** karşı değil. Güç kesintisinde `fsync` çağrılmamış veri kaybolabilir ve dizin senkronize edilmemişse `rename` geri alınabilir. Gerçek güç kesintisi testi, bir sanal makinede disk yazmasını kesmeyi ya da özel bir donanım düzeneğini gerektirir; bu makinede yapmadık. Ama kuralın kendisi (fsync, rename, dizin fsync) bu boşluğu kapatmak için vardır.

## 28.9 Dosya sistemi yapısı: süper blok, inode, bloklar, dizinler

Bir dosya sistemi diskte kabaca dört bölge tutar. En başta **süper blok** dosya sisteminin kimliğini, blok ve inode sayısını, blok boyutunu ve bitmap'lerin konumunu tanımlar. Ardından **inode tablosu** gelir: her dosya ya da dizinin meta verisi (tür, izinler, sahip, boyut, zaman damgaları, veri bloklarının konumu). Sonra **veri blokları** gelir: dosyaların gerçek içeriği. Dizinler de bir dosyadır: içerikleri ad ve inode numarası çiftlerinden oluşan bir tablodur.

Süper bloğu ve inode'ları doğrudan okumak için kök yetkisi (ham aygıt erişimi) gerekir; bu makinede sudo olmadığı için `dumpe2fs` ve `debugfs` çalıştıramadık. Yerine, kullanıcı yetkisiyle görülebilen bilgileri topladık: blok boyutu, toplam ve boş blok, inode sayısı ve kullanımı.

```term
$ df -i . | tail -1; stat -f -c 'blok=%S toplam=%b bos=%f' .
/dev/sdd       67108864 225352 66883512    1% /
blok=4096 toplam=263940717 bos=261833858
```

### inode: dosyanın kimliği

Bir dosyanın adı inode'da değildir; ad dizin girdisindedir. inode, dosyanın kendisini tanımlar. `stat` komutu bu kimliği gösterir:

```term
$ printf 'merhaba dunya\n' > a.txt; stat a.txt
  File: a.txt
  Size: 14        	Blocks: 8          IO Block: 4096   regular file
Device: 8,48	Inode: 44341       Links: 1
Access: (0644/-rw-r--r--)  Uid: ( 1000/   merty)   Gid: ( 1000/   merty)
Access: 2026-10-19 01:12:06.832347804 +0300
Modify: 2026-10-19 01:12:06.832347804 +0300
Change: 2026-10-19 01:12:06.832347804 +0300
 Birth: 2026-10-19 01:12:06.832347804 +0300
```

`Inode` satırındaki numara, dosya sisteminde bu dosyayı benzersiz kılar. `Links: 1` alanı bağlantı sayısıdır: kaç dizin girdisinin bu inode'a işaret ettiğini söyler. `Size` dosyanın bayt boyutudur; `Blocks` ise ayrılmış 512 baytlık birim sayısıdır ve `IO Block` çekirdeğin tercih ettiği G/Ç birimidir (4096). `Birth` zaman damgası ext4'te oluşturulma anıdır. Bu alanların hepsi meta veridir; veriyle birlikte diske yazılır.

### Dizinler: ad → inode eşlemesi

Dizin, içeriği ad ve inode numarası çiftlerinden oluşan özel bir dosyadır. Bu yüzden iki dosyanın aynı inode'a işaret etmesi mümkündür: dizin girdisi yalnızca bir ad tutar, veriye bir işaretçi taşımaz.

```term
$ mkdir dizin && touch dizin/x dizin/y && ls -i dizin
44343 x
44344 y
```

Şekil 28.6, bir inode'un içeriğini, veri bloğunu ve dizin girdilerini birlikte gösterir.

![Şekil 28.6: inode, veri bloğu ve dizin girdileri. Dizin, adları inode numaralarına bağlar; dosya adı inode'un içinde durmaz.](gorseller/b28_inode_bloklar.png)

### Sabit ve sembolik bağlar

`ln` komutu iki farklı bağ türü üretir. **Sabit bağ (hard link)**, aynı inode'a ikinci bir dizin girdisi ekler; bağlantı sayısı artar. **Sembolik bağ (symbolic link)** ise kendi inode'u olan ayrı bir dosyadır ve içeriği hedefin adıdır. Aşağıdaki komutlar her iki durumu da ve birinin silinmesinin sonucunu gösterir:

```term
$ ln a.txt b.txt; ln -s a.txt s.txt; ls -li a.txt b.txt s.txt
44341 -rw-r--r-- 2 merty merty 14 Oct 19 01:12 a.txt
44341 -rw-r--r-- 2 merty merty 14 Oct 19 01:12 b.txt
44345 lrwxrwxrwx 1 merty merty  5 Oct 19 01:12 s.txt -> a.txt
```

```term
$ rm a.txt; cat b.txt; stat -c '%h' b.txt; rm b.txt; cat s.txt
merhaba dunya
1
cat: s.txt: No such file or directory
```

İlk `ls -li` çıktısında `a.txt` ve `b.txt` aynı inode numarasını (44341) ve bağlantı sayısını 2 olarak gösterir; `s.txt` ayrı bir inode'dur (44345) ve bir ok ile hedefe işaret eder. `rm a.txt` yalnızca bir dizin girdisini kaldırdı; inode'un bağlantı sayısı 1'e düştü ve içerik `b.txt` üzerinden hâlâ okunabiliyor. Sembolik bağ ise hedefin adını tutar ve hedef silinince kırılır: son `cat` hata verir.

![Şekil 28.7: Sabit bağ ve sembolik bağ. Sabit bağlar aynı inode'a iki ad verir; sembolik bağ ayrı bir inode'dur ve hedef adını metin olarak tutar.](gorseller/b28_baglar.png)

### Silmek aslında unlink'tir

`rm` komutu bir dosyayı "siler" gibi görünür, ama aslında `unlink` sistem çağrısını yapar: dizin girdisini kaldırır ve inode'un bağlantı sayısını azaltır. Veri, bağlantı sayısı sıfıra düşmekle ve hiçbir süreç dosyayı açık tutmamakla serbest kalır. Bu ayrım, açık bir dosya silindiğinde ne olduğunu açıklar. Aşağıdaki program bunu süreç içinde gösterir:

```c
/* b28_10_unlink.c: açık dosya silinince ne olur? */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>

static void goster(const char *etiket, int fd)
{
    struct stat st;
    if (fstat(fd, &st) < 0) { perror("fstat"); return; }
    printf("%-18s ino=%lu nlink=%lu boyut=%ld\n", etiket,
           (unsigned long)st.st_ino, (unsigned long)st.st_nlink,
           (long)st.st_size);
}
```

```c
int main(void)
{
    const char *yol = "gecici.txt";
    char tampon[64] = {0};

    int fd = open(yol, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    if (write(fd, "silinecek veri\n", 15) != 15) return 1;
    goster("silmeden önce:", fd);

    if (unlink(yol) < 0) { perror("unlink"); return 1; }
    printf("ad var mı?        %s\n",
           access(yol, F_OK) == 0 ? "evet" : "hayır");
    goster("unlink sonrası:", fd);

    if (lseek(fd, 0, SEEK_SET) < 0) return 1;
    ssize_t r = read(fd, tampon, sizeof tampon - 1);
    printf("fd hâlâ okuyor:   %zd bayt -> \"%.14s\"\n", r, tampon);

    if (write(fd, "yeni\n", 5) != 5) return 1;
    goster("yazdıktan sonra:", fd);

    close(fd);
    int acilamadi = open(yol, O_RDONLY) < 0 && errno == ENOENT;
    printf("close sonrası ad yok: %s\n",
           acilamadi ? "evet" : "hayır");
    return 0;
}
```

```term
$ ./b28_10_unlink
silmeden önce:    ino=44293 nlink=1 boyut=15
ad var mı?        hayır
unlink sonrası:   ino=44293 nlink=0 boyut=15
fd hâlâ okuyor:   15 bayt -> "silinecek veri"
yazdıktan sonra:  ino=44293 nlink=0 boyut=20
close sonrası ad yok: evet
```

Dosya silindikten sonra da fd üzerinden okunabiliyor ve yazılabiliyor, çünkü açık dosya girdisi inode'u hâlâ referans ediyor. `nlink` 0 olduğunda ise dosya adı artık yoktur; close'dan sonra çekirdek veri bloklarını serbest bırakır. Bu yüzden büyük bir günlük dosyası silinip uygulama yeniden başlatılmadığında "disk dolu ama dosya yok" durumu görülür: silinen ama hâlâ açık olan dosya yer kaplamaya devam eder.

### Veri blokları, extent ve gecikmeli ayırma

Eski ext2 ve ext3 dosya sistemleri her veri bloğunun konumunu inode içinde ayrı işaretçilerle tutardı; büyük dosyalar için dolaylı (indirect) işaretçiler gerekirdi. ext4, bunun yerine **extent** kullanır: bitişik blok dizisini tek bir girdiyle (mantıksal başlangıç, uzunluk, fiziksel başlangıç) anlatır. Bu, büyük ve ardışık dosyalar için hem daha az meta veri hem de daha iyi sıralı okuma demektir (genel bilgi).

ext4 ayrıca **gecikmeli ayırma (delayed allocation)** yapar: yazma sayfa önbelleğine girerken fiziksel blok atanmaz; atama, çekirdek yazmayı diske boşaltmaya karar verene kadar ertelenir. Bu, çekirdeğe daha iyi bir yerleşim seçme fırsatı verir. Ölçüm bunu doğrudan gösterir:

```term
$ dd if=/dev/urandom of=buyuk.bin bs=1M count=1 status=none
```

```term
$ filefrag -v buyuk.bin | sed 's/  */ /g'
Filesystem type is: ef53
File size of buyuk.bin is 1048576 (256 blocks of 4096 bytes)
 ext: logical_offset: physical_offset: length: expected: flags:
 0: 0.. 255: 0.. 0: 0: last,unknown_loc,delalloc,eof
buyuk.bin: 1 extent found
```

Fiziksel konum (`physical_offset`) sütununda `0` ve `delalloc` bayrağı görülüyor: blokların henüz atanmadığı, veri hâlâ sayfa önbelleğinde olduğu anlamına geliyor. Çıktıyı okunur kılmak için tablo boşluklarını `sed` ile sıkıştırdık. Diski boşaltıp aynı dosyayı yeniden ölçtüğümüzde:

```term
$ sync
```

```term
$ filefrag -v buyuk.bin | sed 's/  */ /g'
Filesystem type is: ef53
File size of buyuk.bin is 1048576 (256 blocks of 4096 bytes)
 ext: logical_offset: physical_offset: length: expected: flags:
 0: 0.. 255: 134169856.. 134170111: 256: last,eof
buyuk.bin: 1 extent found
```

Artık tek bir extent var: 256 mantıksal bloğu (1 MiB) fiziksel 134169856 numaralı bloktan başlayan 256 bitişik blok izliyor. Bu extent, Şekil 28.6'daki "veri bloğu işaretçisi" kavramının ext4'teki karşılığıdır.

### Günlükleme (journaling)

Bir dosya sisteminin meta verisi birden fazla blokta yazılır: inode, bitmap, dizin bloğu. Bu yazmalar arasında elektrik kesilirse dosya sistemi tutarsız kalabilir. **Günlükleme**, değişiklikleri önce ayrı bir günlük alanına yazarak bu sorunu çözer; açılışta günlük tekrar oynatılır. ext4'ün üç kipi vardır:

| Kip | Ne günlüklenir? | Güvence |
|---|---|---|
| journal | meta veri ve veri | en güçlü, en yavaş |
| ordered (varsayılan) | yalnız meta veri; veri, meta veriden önce diske iner | dengeli |
| writeback | yalnız meta veri; veri sırası garanti değil | en hızlı, en zayıf |

Bu makinedeki bağlama seçeneklerinde `data=ordered` görülüyor:

```term
$ grep ' / ' /proc/mounts
/dev/sdd / ext4 rw,relatime,discard,errors=remount-ro,data=ordered 0 0
```

Kipin adı, veri bloklarının meta veriden önce diske yazılmasını sağladığını söyler; böylece meta veri bir dosyanın henüz diske inmemiş verisini göstermez. Bu, yaygın "boş dosya" sorununu önler. Ama `ordered` bile bir uygulamanın kendi `fsync` disiplinini ortadan kaldırmaz: 28.7'deki kural yine geçerlidir.

### Kopyala-yaz dosya sistemleri

btrfs ve ZFS gibi dosya sistemleri, bir bloğu değiştirmek yerine yeni bir kopyasını yazar ve üst işaretçileri yeniden bağlar (kopyala-yaz, copy-on-write). Eski veri, yeni durum kalıcılaşana kadar yerinde kalır; bu, güç kesintisine karşı doğal bir dayanıklılık sağlar ve anlık görüntüleri (snapshot) ucuzlatır. Bedeli, parçalanma ve rastgele yazma davranışıdır (genel bilgi). Bu bölümde bu sistemleri ölçmedik.

### FAT: zincirle izlenen kümeler

Gömülü sistemlerde, SD kartlarda, USB bellekte ve eski Windows sürümlerinde karşına çıkan dosya sistemi FAT'tir. FAT'ın temel fikri basittir: veri **kümeler** (cluster) halinde tutulur ve bir dosyanın kümeleri, bir **FAT tablosundaki** zincirle birbirine bağlanır. Dizin girdisi dosyanın ilk kümesini gösterir; her kümenin FAT'taki girdisi bir sonraki kümenin numarasını tutar; zincirin sonu özel bir EOF değeriyle işaretlenir.

Şekil 28.8 bu zinciri şematik olarak gösterir. Bu bir örnektir; bu ortamda FAT görüntüsü oluşturacak `mkfs.fat` aracı yoktu, bu yüzden gerçek bir FAT diski okumadık ve ölçüm yapmadık.

![Şekil 28.8: FAT zinciri (şematik örnek). rapor.txt dizin girdisi, ilk kümeyi (2) gösterir; FAT girdileri 2 → 3 → 5 → EOF zincirini kurar. Kümeler 4 ve 6 boş, 7 bozuktur.](gorseller/b28_fat_zincir.png)

FAT'ın avantajı yapısal sadeliğidir: uygulaması küçük, bellek ayak izi düşüktür. Dezavantajı, zincir boyunca yürümenin rastgele erişimi pahalı kılması ve parçalanmadır. FAT32 kümelerin numaralarını 32 bitlik girdilerde tutar (genel bilgi); dosya boyutunun 4 GiB sınırı da bu tasarımın bir sonucudur.

### NTFS, kısaca

Windows'un varsayılan dosya sistemi NTFS'tir. Meta verinin merkezinde **MFT (Master File Table)** vardır; her dosya ve dizin için bir kayıt tutar. NTFS da günlükleme yapar (`$LogFile`). Bu bölümün ölçümleri WSL'in ext4 dosya sistemi üzerinde alındı; Windows tarafındaki NTFS davranışını ölçmedik. Ancak `/mnt/c` altında WSL'den erişilen NTFS dosyaları, ext4'ten farklı bir sürücü katmanından geçer; bu yüzden bölümün tüm ölçümleri `/home` altında yapıldı.

## 28.10 VFS: Bölüm 21'in file_operations'ından dosya nesnelerine

28.2'deki yığında VFS katmanı, farklı dosya sistemlerini tek bir arayüz altında toplar. Bu katmanın ana nesneleri üçtür: **inode** (dosyanın kalıcı kimliği), **dentry** (dizin girdisinin bellekteki önbelleği; bir yolun bir parçasının inode'a çözümlenmesi), **file** (açık dosya; ofset, bayraklar ve `f_op` tablosu). Bölüm 21'deki `file_operations` tablosu `file` nesnesinin içindedir: `f_op` işaretçisi, bu açık dosyanın hangi sürücü fonksiyonlarını kullanacağını belirler.

Bir `open("/home/a/b.txt")` çağrısı kabaca şu sırayla çözülür: yol bileşenleri tek tek dentry önbelleğinde aranır; son bileşen bir inode'a bağlanır; çekirdek bu inode için yeni bir `struct file` oluşturur ve `f_op`'u dosya sisteminin tablosundan doldurur; fd tablosuna bir girdi eklenir. Sonraki `read` çağrıları artık yolu hiç görmez; yalnızca `f_op->read_iter` gibi işaretçilerle konuşur.

Bu yapıyı bir C++ projesinde zaten kurdun. MertOS'un sanal dosya sistemi, bellek içi bir ağaç olarak yazılmıştır ve tek bir `INode` yapısı tüm dosya ve dizinleri temsil eder:

```cpp
struct INode {
    char     name[64];          // Dosya/dizin adı
    bool     is_dir;            // true = dizin, false = dosya
    uint8_t* data;              // Dosya içeriği (dizin için nullptr)
    uint64_t size;              // Veri boyutu (byte)
    INode*   parent;            // Üst dizin (root için nullptr)
    INode*   children[16];      // Alt düğümler (sadece dizin için)
    uint8_t  child_count;       // Mevcut alt düğüm sayısı
};
```

Burada `children[16]` ve `child_count`, bir dizinin en fazla 16 çocuk taşıyabileceğini söyler; `vfs.cpp` içinde bu sınır `mkdir` (103. satır) ve `create` (141. satır) fonksiyonlarında denetlenir. Linux'taki `dentry` önbelleği ve `inode` ayrımı bu tek yapıyı ikiye böler: ad çözme bilgisi ile dosya kimliği farklı yaşam döngülerine sahiptir ve bu ayrım önbelleğin etkin çalışmasını sağlar. MertOS'ta `create` içerik işaretçisini kopyalamadan saklar (`vfs.hpp` satır 39); gerçek dosya sisteminde ise veri, sayfa önbelleği aracılığıyla yönetilir. Bu fark, MertOS'un neden bellek içi olduğunu ve neden diske kalıcılık taşımadığını da açıklar.

Bölüm 21'de yazdığın bağımlılık tersine çevirme ile burada gördüğün `f_op` tablosu aynı fikirdir: üst katman (sistem çağrısı) alt katmanın somut fonksiyonlarına değil, bir sözleşmeye (tablo) bağlıdır. Bu yüzden yeni bir dosya sistemi eklemek, çekirdeğin geri kalanını değiştirmeden mümkündür.

## 28.11 mmap ile dosya: sayfa, kopya ve paylaşım

`read` çağrısı, veriyi sayfa önbelleğinden kendi tamponuna kopyalar. `mmap` farklı bir yol izler: dosyanın sayfalarını doğrudan süreçin sanal adres uzayına eşler. Dosyaya bir işaretçiyle erişirsin; ilk dokunuş bir **sayfa hatası** (page fault) üretir, çekirdek sayfayı önbellekten bulup sayfa tablosuna ekler ve program kaldığı yerden devam eder. Sayfa tablosu ve sanal bellek kavramları Bölüm 25'in konusudur; burada yalnızca dosya tarafına bakıyoruz.

İki eşleme kipi vardır. `MAP_PRIVATE` ile eşlenen sayfalara yazmak, süreç için bir kopya üretir (kopyala-yaz, copy-on-write); dosya değişmez. `MAP_SHARED` ile eşlenen sayfalara yazmak ise doğrudan sayfa önbelleğindeki sayfayı değiştirir; başka süreçler aynı dosyayı eşlemişse onlar da değişikliği görür. Bu değişikliğin diske ne zaman ineceği çekirdeğe bağlıdır; `msync` ile zorlayabilirsin, aksi hâlde 28.7'deki kalıcılık kuralı geçerlidir.

Aşağıdaki program, aynı 8 MiB dosyayı bir kez `read` ile (64 KiB tamponla), bir kez `mmap` ile okur ve her biri için süre ile küçük sayfa hatası (minor fault) sayısını alır. Son bölümde `MAP_SHARED` ile yazılan bir baytın `read` ile görülüp görülmediğini sınar.

```c
/* b28_8_mmap_olcum.c: read() ile mmap() karşılaştırması ve
 * MAP_SHARED. Çıktı: yontem,sure_ms,minflt (en iyi 3 tur) */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/resource.h>

#define TUR 3
#define TAMPON (64 * 1024)

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

/* Bu süreçteki küçük sayfa hatası (minor fault) sayısı */
static long minflt(void)
{
    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
    return ru.ru_minflt;
}
```

Okuma fonksiyonları ve `mmap` tarafı aşağıda. `toplam_mmap` her sayfadan bir bayt okuyarak sayfa hatalarını tetikler; `toplam_read` aynı işi bir tamponla yapar.

```c
static unsigned toplam_read(const char *yol)
{
    static char t[TAMPON];
    unsigned s = 0;
    int fd = open(yol, O_RDONLY);
    ssize_t r;
    while ((r = read(fd, t, TAMPON)) > 0)
        for (ssize_t i = 0; i < r; i += 4096)
            s += (unsigned char)t[i];
    close(fd);
    return s;
}

static unsigned toplam_mmap(const char *yol)
{
    int fd = open(yol, O_RDONLY);
    struct stat st;
    fstat(fd, &st);
    const unsigned char *p = mmap(NULL, st.st_size, PROT_READ,
                                  MAP_PRIVATE, fd, 0);
    unsigned s = 0;
    for (off_t i = 0; i < st.st_size; i += 4096)
        s += p[i];
    munmap((void *)p, st.st_size);
    close(fd);
    return s;
}
```

```c
static void olc(const char *ad, unsigned (*f)(const char *),
                const char *yol)
{
    double en_iyi = 1e18;
    long hata = 0;
    unsigned s = 0;
    for (int t = 0; t < TUR; t++) {
        long f0 = minflt();
        double t0 = simdi_ms();
        s = f(yol);
        double dt = simdi_ms() - t0;
        long df = minflt() - f0;
        if (dt < en_iyi) { en_iyi = dt; hata = df; }
    }
    printf("%s,%.2f,%ld\n", ad, en_iyi, hata);
    fprintf(stderr, "# %s sağ=%u\n", ad, s);
}

/* MAP_SHARED: sayfa, dosyanın önbellek kopyasıdır; yazılan bayt
 * msync'ten sonra read() ile görülür. */
static void paylasimli_demo(void)
{
    const char *yol = "paylasim.bin";
    int fd = open(yol, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (ftruncate(fd, 4096) < 0) return;
    char *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                   MAP_SHARED, fd, 0);
    memcpy(p, "merhaba", 7);
    p[0] = 'Z';
    msync(p, 4096, MS_SYNC);
    munmap(p, 4096);
    lseek(fd, 0, SEEK_SET);
    char b[8] = {0};
    if (read(fd, b, 7) != 7) return;
    printf("MAP_SHARED: read() görünümü = \"%s\"\n", b);
    close(fd);
}
```

```c
int main(int argc, char **argv)
{
    const char *yol = argc > 1 ? argv[1] : "veri.bin";
    printf("yontem,sure_ms,minflt\n");
    olc("read_64K", toplam_read, yol);
    olc("mmap", toplam_mmap, yol);
    paylasimli_demo();
    return 0;
}
```

```term
$ ./b28_8_mmap_olcum veri.bin
yontem,sure_ms,minflt
read_64K,0.40,0
mmap,0.92,128
MAP_SHARED: read() görünümü = "Zerhaba"
```

Sonuç tabloda: bu sıcak önbellek ve sıralı okuma senaryosunda `read` daha hızlıdır (0,40 ms, `mmap` 0,92 ms). Bunun nedeni, `read`'in tek bir büyük kopyayı verimli yapması, `mmap`'in ise her yeni sayfa için sayfa tablosu girdisi kurmak zorunda kalmasıdır. `mmap` 2048 sayfa için yalnızca 128 küçük sayfa hatası üretti: Linux, bir dosya hatasında çevredeki 16 sayfayı da eşler (fault-around; genel bilgi), yani her hatada 16 sayfa. `read` ise hiç sayfa hatası üretmedi çünkü tamponu zaten eşlenmiş belleğe kopyaladı.

Bu sonuç "mmap hızlıdır" ya da "read hızlıdır" demek değildir. `mmap`'in asıl kazancı, kopyanın olmaması ve seyrek erişimdir: dosyanın yalnızca bir kısmına rastgele bakan bir veritabanı indeksi ya da büyük bir ikili dosyanın içinde zıplayan bir ayrıştırıcı, `read` ile tüm veriyi kopyalamak yerine yalnızca gereken sayfaları çeker. Her iki yaklaşımın maliyetini de ölçümle görmek, bu bölümün ana fikridir.

Son satır, `MAP_SHARED`'in davranışını gösterir: `Z` yazıldı, `read` ile okunan dosya içeriği `Zerhaba` oldu. Yani eşlenmiş sayfa ile dosyanın önbellek kopyası aynı şeydir; `msync` ise bu değişikliği diske göndermek için kullanılır.

## 28.12 G/Ç modelleri: engelleme, çoğullama ve asenkron

Bir ağ sunucusu ya da çok kaynaklı bir program aynı anda birçok G/Ç beklemek zorundadır. Bunu yapmanın dört temel modeli vardır ve farkları, bir iş parçacığının ne zaman uyuduğunda yatar.

| Model | Çağrı | İş parçacığı ne yapar? | Tipik kullanım |
|---|---|---|---|
| Engelleyen (blocking) | `read` | veri gelene kadar uyur | basit araçlar |
| Engellemeyen (non-blocking) | `read` + `O_NONBLOCK` | hemen döner; `EAGAIN` ile yoklar | döngü içinde denetim |
| Çoğullama (multiplexing) | `select`, `poll`, `epoll_wait` | birçok fd'yi tek çağrıda bekler | sunucular, olay döngüleri |
| Asenkron | `io_uring` | işi gönderir, tamamlanmayı kuyruktan alır | yüksek hacimli G/Ç |

![Şekil 28.9: Dört G/Ç modeli. Engelleyen model çekirdekte uyur; engellemeyen model hemen döner; çoğullama tek çağrıyla birçok fd'yi bekler; asenkron model işi gönderir ve tamamlanmayı ayrıca alır.](gorseller/b28_gg_modelleri.png)

Engelleyen model en kolay olanıdır ve çoğu zaman yeterlidir. Sorun, tek bir iş parçacığının birden fazla kaynağı aynı anda dinlemek istediğinde ortaya çıkar: ilk `read` çağrısında uyursa, öteki kaynaktaki veri gelse bile fark edilmez. Çoğullama bu soruna cevaptır: çekirdeğe "bu fd'lerden herhangi biri hazır olunca bana haber ver" dersin. Linux'ta bunun modern biçimi `epoll`'dur; `select` ve `poll` ise daha eski ve farklı ölçeklenen çağrılardır.

Aşağıdaki program üç şeyi gösterir: seviye tetikleme (LT), kenar tetikleme (ET) ve engellemeyen okumada `EAGAIN`. Programın başlığı ve yardımcı fonksiyonlar aşağıdadır; çoğullama kipinin `main` fonksiyonu Örnek 4'te yer alır.

```c
/* b28_9_epoll.c: G/Ç çoğullama. Kipler:
 *   tetik      seviye/kenar tetikleme ve EAGAIN
 *   olcek N    poll ve epoll, N pipe, tek aktif fd (ns/çağrı)
 *   olay       N=1000 pipe'ı tek epoll döngüsünde dinle */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <poll.h>
#include <sys/epoll.h>
#include <sys/resource.h>

static void boru_ac(int b[2])
{
    if (pipe(b) < 0) { perror("pipe"); exit(1); }
}

static double simdi_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e9 + t.tv_nsec;
}
```

```c
static void tetik(void)
{
    int bl[2];
    struct epoll_event ev, out;
    char c;

    /* Seviye tetikleme (LT): veri kaldıysa tekrar bildirir */
    boru_ac(bl);
    int ep = epoll_create1(0);
    ev.events = EPOLLIN; ev.data.fd = bl[0];
    epoll_ctl(ep, EPOLL_CTL_ADD, bl[0], &ev);
    if (write(bl[1], "ab", 2) != 2) return;
    epoll_wait(ep, &out, 1, 0);
    if (read(bl[0], &c, 1) != 1) return;     /* yalnız 1 bayt */
    int n2 = epoll_wait(ep, &out, 1, 0);
    printf("LT: ikinci epoll_wait hazır=%d (1 bayt kaldı)\n", n2);
    close(ep); close(bl[0]); close(bl[1]);

    /* Kenar tetikleme (ET): yalnız yeni veri gelişinde bildirir */
    boru_ac(bl);
    ep = epoll_create1(0);
    ev.events = EPOLLIN | EPOLLET; ev.data.fd = bl[0];
    epoll_ctl(ep, EPOLL_CTL_ADD, bl[0], &ev);
    if (write(bl[1], "ab", 2) != 2) return;
    epoll_wait(ep, &out, 1, 0);
    if (read(bl[0], &c, 1) != 1) return;
    int n3 = epoll_wait(ep, &out, 1, 0);
    printf("ET: ikinci epoll_wait hazır=%d (1 bayt kaldı!)\n", n3);
    close(ep); close(bl[0]); close(bl[1]);

    /* EAGAIN: boş, engellemeyen pipe'tan okuma */
    boru_ac(bl);
    fcntl(bl[0], F_SETFL, O_NONBLOCK);
    ssize_t r = read(bl[0], &c, 1);
    printf("boş pipe read=%zd errno=%s\n", r,
           errno == EAGAIN ? "EAGAIN" : "diğer");
    close(bl[0]); close(bl[1]);
}
```

```term
$ ./b28_9_epoll tetik
LT: ikinci epoll_wait hazır=1 (1 bayt kaldı)
ET: ikinci epoll_wait hazır=0 (1 bayt kaldı!)
boş pipe read=-1 errno=EAGAIN
```

Çıktı, iki tetikleme modunun farkını açıkça gösterir. Seviye tetiklemede bir baytı okuduktan sonra kalan bir bayt olduğu için `epoll_wait` yeniden hazır bildirir. Kenar tetiklemede ise hazır olma olayı yalnızca **yeni veri geldiğinde** bir kez bildirilir; okumadığın veri orada dursa da çekirdek bunu tekrar söylemez. Bu, kenar tetiklemenin en sık yapılan hatasıdır: her olayda okumayı `EAGAIN` alana kadar sürdürmek zorundasın. Üçüncü satır, boş bir engellemeyen pipe'tan okumanın `EAGAIN` döndürdüğünü gösterir; bu, "şu an veri yok, sonra tekrar dene" anlamına gelir.

Şimdi ölçeği görelim. Aşağıdaki kip, `N` adet pipe oluşturur ve yalnızca sonuncusunu aktif tutar. `poll` her çağrıda `N` fd'yi tarar; `epoll_wait` ise yalnızca hazır olanları döndürür. Her çağrının süresi ölçülür.

```c
static void olcek(int n)
{
    int (*bl)[2] = malloc(n * sizeof *bl);
    struct pollfd *pf = malloc(n * sizeof *pf);
    int ep = epoll_create1(0);
    for (int i = 0; i < n; i++) {
        boru_ac(bl[i]);
        pf[i].fd = bl[i][0];
        pf[i].events = POLLIN;
        struct epoll_event ev = { .events = EPOLLIN, .data.u32 = i };
        epoll_ctl(ep, EPOLL_CTL_ADD, bl[i][0], &ev);
    }
    int son = n - 1;                 /* tek aktif fd: sonuncusu */
    const int R = 2000;
    double tp = 0, te = 0;
    struct epoll_event out;
    char c;
    for (int r = 0; r < R; r++) {
        if (write(bl[son][1], "x", 1) != 1) return;
        double t0 = simdi_ns();
        poll(pf, n, 0);
        tp += simdi_ns() - t0;
        if (read(bl[son][0], &c, 1) != 1) return;

        if (write(bl[son][1], "x", 1) != 1) return;
        t0 = simdi_ns();
        epoll_wait(ep, &out, 1, 0);
        te += simdi_ns() - t0;
        if (read(bl[son][0], &c, 1) != 1) return;
    }
    printf("%d,%.0f,%.0f\n", n, tp / R, te / R);
    for (int i = 0; i < n; i++) {
        close(bl[i][0]); close(bl[i][1]);
    }
    close(ep);
    free(bl); free(pf);
}
```

Ölçüm sonuçları (her nokta 2000 çağrının ortalaması):

| Pipe sayısı n | poll (ns/çağrı) | epoll (ns/çağrı) |
|---|---|---|
| 10 | 613 | 506 |
| 100 | 3 521 | 489 |
| 1 000 | 33 398 | 568 |
| 5 000 | 190 554 | 667 |
| 10 000 | 441 749 | 694 |

![Şekil 28.10: Tek aktif fd ile n fd'yi izlemenin çağrı başına süresi. poll doğrusal büyür; epoll neredeyse sabit kalır.](gorseller/b28_epoll_olcek.png)

Tablo ve Şekil 28.10, çoğullamanın asıl farkını gösterir: `poll` her çağrıda tüm listeyi kullanıcı alanından çekirdeğe kopyalayıp tarar, maliyeti `n` ile doğrusal büyür. `epoll` ise izlenen fd'leri çekirdekte kalıcı bir yapıda tutar ve yalnızca hazır olanları döndürür; maliyeti izlenen toplam sayıya değil, hazır olay sayısına bağlıdır. Bu yüzden on binlerce bağlantı taşıyan sunucular `epoll` kullanır.

Son olarak iki modern model hakkında genel bilgi. `io_uring` (Linux 5.1 ve sonrası; bu makinenin çekirdeği 6.6) iki halkalı bir kuyruk kullanır: gönderme kuyruğuna istek yazılır, tamamlanma kuyruğundan sonuç alınır; çoğu durumda sistem çağrısı sayısı azalır. Bu bölümde `io_uring`'i ölçmedik ve kodunu yazmadık. Ayrıca `O_DIRECT` bayrağı, sayfa önbelleğini atlayarak doğrudan aygıta G/Ç yapar; veritabanları kendi önbelleğini yönetmek istediğinde kullanır, ama hizalama ve blok boyutu kurallarına uymak zorundasın (genel bilgi).

Python'un `selectors` modülü bu çekirdek çağrıları sarar. CPython 3.12.10 kaynağında `Lib/selectors.py` dosyasının 442. satırındaki `EpollSelector` sınıfı, `select()` içinde doğrudan `epoll` nesnesinin `poll` yöntemini çağırır; `asyncio` olay döngüsü de bu soyutlamanın üstünde çalışır. Yani Python'daki `async` kodu, C'de yazdığın `epoll_wait` döngüsünün bir sarmalayıcısıdır.

## 28.13 Cihaz G/Ç: karakter, blok ve kesme

`/dev` altındaki dosyalar gerçek aygıtları temsil eder. `ls -l` çıktısındaki ilk harf aygıt türünü söyler: `c` karakter aygıtı, `b` blok aygıtıdır. Ayrıca iki sayı görürsün: **major** (sürücüyü tanımlar) ve **minor** (aynı sürücüdeki aygıtı).

```term
$ ls -l /dev/null /dev/sdd /dev/tty
crw-rw-rw- 1 root root 1,  3 Oct 18 21:51 /dev/null
brw-rw---- 1 root disk 8, 48 Oct 18 21:51 /dev/sdd
crw-rw-rw- 1 root tty  5,  0 Oct 18 21:51 /dev/tty
```

Karakter aygıtı (`/dev/null`, `/dev/tty`) bayt akışı gibi davranır: sıralı okur ve yazar, rastgele erişim genellikle yoktur. Blok aygıtı (`/dev/sdd`) ise sabit boyutlu bloklarla ve rastgele erişimle çalışır; üstüne bir dosya sistemi kurulabilir. Bu makinedeki `/dev/sdd` WSL'in ext4 sanal diskidir ve kök izinleri gerektirir.

Donanım tarafında veri akışı genellikle şöyle olur. CPU, aygıta bir komut yazar (ör. "şu bloğu oku ve belleğe koy"). Aygıt işi kendi denetleyicisiyle yapar; veriyi, CPU'yu meşgul etmeden, **DMA** (Direct Memory Access) ile doğrudan bellekteki bir tampona taşır. İş bitince aygıt bir **kesme** (interrupt) üretir ve CPU, kesme işleyicisine dallanarak sonucu işler. Bu, sürekli yoklamaya (polling) göre CPU zamanını korur ama kesme yükü getirir. Kesmelerin ayrıntıları Bölüm 44'te, UART, SPI ve I2C gibi bu tür aygıtların protokolleri ise Bölüm 45'te, bare-metal bir gömülü hedefte ise Bölüm 43'te yer alıyor. Burada gördüğün `read` çağrısı, arka planda tam bu yolu çalıştırır.

## 28.14 Gerçek dünya: veritabanı, günlük ve uçuş kayıt cihazı

Veritabanları, bu bölümdeki kalıcılık kurallarını en ciddi biçimde uygular. Bir işlemin "kalıcı" sayılması için önce işlemin günlüğe (write-ahead log, WAL) yazılması ve `fsync` ile diske inmesi gerekir; veri dosyasının kendisi sonradan güncellenebilir. Güç kesilirse açılışta günlük tekrar oynatılır. Bu, 28.7'deki "önce veri, sonra kayıt" sırasının doğrudan uygulamasıdır. Bölüm 33–35'te ilişkisel modeli, SQL'i ve dizinleri gördükçe bu günlüğün neden her zaman bir adım önde olduğunu anlayacaksın.

Bölüm 14'teki log projesinde zaman damgalı bir dosyada bayt ofsetine `seek` ile gidip satır başına ilerlemiştin; o okuma tarafıydı. Günlük yazma tarafında ise tampon seçimi de önemlidir. Bir uygulama `stdout`'u dosyaya yönlendirdiğinde (28.6), çıktı tam tamponlu olur; çökme anında son satırlar tamponda kalabilir. Bu yüzden kritik hata günlükleri genellikle her satırdan sonra boşaltılır (`fflush`) ya da satır tamponu kullanılır. Performans ile kayıp arasındaki denge, uygulamanın ne kadar veri kaybını kabul edebileceğine bağlıdır.

Mert'in savunma sanayiinde karşılaşabileceği bir örnek: bir uçuş kayıt cihazı (veri kaydedici) güç kesintisinden sonra açılmak zorundadır ve son kaydın bütün ya da yarım olduğunu güvenle ayırt etmelidir. Böyle bir tasarımın genel ilkeleri şunlardır: kayıtlar yalnızca eklenir (append-only); her kaydın sonunda bir sağlama değeri (CRC) bulunur; belirli aralıklarla `fsync` yapılır; açılışta dosya baştan taranır, bozuk son kayıt kırpılır. Bu ilkelerin bir uygulamasını Kendin Yap Projesi 1'de kuracaksın. Bu bölümde yalnızca ilkeleri verdik; gerçek bir sistemde kullanılacak donanım ve sertifikasyon gereksinimleri ayrı bir uzmanlık alanıdır.

## Çözümlü Örnekler

### Örnek 1 (★): Satır sayarken tampon sınırı

**Adım 1 — Anla.** Bir dosyadaki satır sayısını bulan bir fonksiyon yazılacak. Kısıt: dosya belleğe tamamen alınmamalı, yalnızca sabit boyutlu bir tampon kullanılmalı. Tampon boyutu ne olursa olsun, sonuç aynı kalmalı.

**Adım 2 — Örnekle.** `ab\ncd\nef\n` içeriğindeki dosyanın dokuz baytı ve üç satır sonu vardır. Tampon dört bayt olursa, bir satır sonu iki okuma arasında bölünebilir: `ab\nc` ve `d\nef` gibi. Satır sayarken satırların bütünlüğünü değil, satır sonu baytlarını sayıyoruz. Bir satır sonu iki okumaya bölünse bile her bayt yalnız bir okumada görülür; yeter ki hiçbir bayt atlanmasın ya da iki kez sayılmasın.

**Adım 3 — Kaba çöz.** En basit yol: dosyayı `read` ile parça parça oku; her parçada `\n` sayısını topla. Döngüyü `read` sıfır dönene kadar sürdür; `-1` gelirse `EINTR` ise tekrar dene, değilse hata dön.

**Adım 4 — Örüntü.** Örüntü şudur: *her bayt tam bir kez görülür*. Bu, parçaların sınırlarından bağımsız olarak doğru sonuç vermesini sağlar. Kısa okuma da burada zararsızdır çünkü her çağrı sadece kendi aldığı baytları sayar ve bir sonraki çağrı kaldığı yerden devam eder.

**Adım 5 — İyileştir.** Aşağıdaki sürümde tampon boyutu parametredir; `read` döngüsü `EINTR`'ı ayırt eder. Dosya açılamazsa ya da bellek alınamazsa `-1` döner.

```c
/* b28_12_satir_say.c: sınırlı tamponla satır sayma */
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

/* Dosyadaki '\n' sayısını döner; hata olursa -1. */
long satir_say(const char *yol, size_t tampon_boyu)
{
    char *t = malloc(tampon_boyu);
    if (!t) return -1;
    int fd = open(yol, O_RDONLY);
    if (fd < 0) { free(t); return -1; }

    long satir = 0;
    for (;;) {
        ssize_t r = read(fd, t, tampon_boyu);
        if (r < 0) {
            if (errno == EINTR) continue;
            satir = -1;
            break;
        }
        if (r == 0) break;                   /* EOF */
        for (ssize_t i = 0; i < r; i++)
            if (t[i] == '\n') satir++;
    }
    close(fd);
    free(t);
    return satir;
}
```

Ana fonksiyon aynı dosyayı üç farklı tampon boyutuyla sayar:

```c
int main(void)
{
    const char *yol = "satirlar.txt";
    int fd = open(yol, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) return 1;
    if (write(fd, "ab\ncd\nef\n", 9) != 9) return 1;
    close(fd);

    size_t boylar[] = {1, 4, 100};
    for (int i = 0; i < 3; i++)
        printf("tampon=%3zu -> satır=%ld\n",
               boylar[i], satir_say(yol, boylar[i]));
    return 0;
}
```

**Adım 6 — Doğrula.** Dokuz baytlık dosyayı dört baytlık tamponla elle izleyelim:

| Okuma | r (dönen) | tampon içeriği | satır sonu | toplam |
|---|---|---|---|---|
| 1 | 4 | `ab\nc` | 1 | 1 |
| 2 | 4 | `d\nef` | 1 | 2 |
| 3 | 1 | `\n` | 1 | 3 |
| 4 | 0 | (EOF) | 0 | 3 |

Gerçek çıktı, her tampon boyutunda aynı sonucu verir:

```term
$ ./b28_12_satir_say
tampon=  1 -> satır=3
tampon=  4 -> satır=3
tampon=100 -> satır=3
```

**Bunu AI'sız yazabilir misin?** Boş bir dosyada, bu sayfaya bakmadan: önce dosyayı açıp `read` döngüsünü, sonra satır sonlarını saymayı yaz. Ardından sınır koşullarını dene: boş dosya, tek satır, satır sonu olmayan son satır, bir baytlık tampon. Her birini elle izleyip sonucu tahmin et, sonra çalıştır.

### Örnek 2 (★★): printf ve fork: çift çıktının izi

**Adım 1 — Anla.** Aşağıdaki program "A" yazdırıp `fork` çağırıyor, sonra her süreç "B" ve satır sonu yazıyor. Pipe'a yönlendirdiğimizde çıktı iki satır oluyor: `AB` iki kez. Neden?

**Adım 2 — Örnekle.** Program şu:

```c
/* b28_13_fork_tampon.c: fork öncesi tampon ve çift çıktı */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

int main(int argc, char **argv)
{
    int bosalt = argc > 1 && strcmp(argv[1], "flush") == 0;

    printf("A");                     /* satır sonu yok */
    if (bosalt)
        fflush(stdout);

    pid_t pid = fork();
    printf("B\n");
    if (pid == 0)
        return 0;                    /* çocuk: çıkışta boşaltır */

    wait(NULL);
    return 0;
}
```

Program, 28.6'daki tampon kalıbının küçültülmüş hâlidir; burada `fflush` isteğe bağlıdır. Hangi veri nerede olduğunu izleyelim.

**Adım 3 — Kaba çöz.** Tahmin: `fork` iki süreç yarattığı için iki kez yazılmış olmalı. Ama hangi veri kopyalanıyor? Burada "tampon nerede?" sorusu kilit: tampon bellekte, `fork` belleği kopyalar.

**Adım 4 — Örüntü.** Örüntü: *fork anında tampondaki bekleyen veri her iki sürece de geçer; ikisi de çıkışta boşaltırsa aynı veri iki kez çıkar.* Satır sonu olmayan `A` tamponda beklediği için kopyalanır. Oysa `fflush` ile `A`'yı önceden boşaltırsak kopyalanacak bir şey kalmaz.

**Adım 5 — İyileştir.** Düzeltme bir disiplindir: `fork`tan önce `fflush` ile tamponu boşalt. Çocuk hemen `exec` ile yeni bir programa geçerse, `exec` süreç belleğini değiştirdiği için çocuğun tamponundaki kopya atılır ve çift çıktı olmaz. Ama bu, programın davranışını `exec`'e bağlamak demektir; asıl güvence, `fork` öncesinde tamponu boşaltmaktır.

**Adım 6 — Doğrula.** İki kipi elle izleyelim (tampon içeriği):

| Adım | Ana süreç tamponu | Çocuk tamponu | Pipe'a çıkan |
|---|---|---|---|
| `printf("A")` | `A` | — | — |
| `fork()` (flush yok) | `A` | `A` (kopya) | — |
| ana: `printf("B\n")` | `AB\n` | — | — |
| çocuk: `printf("B\n")` | — | `AB\n` | — |
| çocuk çıkar | — | boşalır | `AB\n` |
| ana `wait`, çıkar | boşalır | — | `AB\n` |

Flush kipinde `fork`'tan önce `A` pipe'a çıkar, ana ve çocuk tamponları boş başlar; sonuç `A` + `B\n` + `B\n`'dir. Gerçek çıktılar da bu izle örtüşüyor:

```term
$ ./b28_13_fork_tampon | cat
AB
AB
```

```term
$ ./b28_13_fork_tampon flush | cat
AB
B
```

**Bunu AI'sız yazabilir misin?** Boş bir dosyada, bu sayfaya bakmadan: `printf("A")` yerine `printf("A\n")` yazarsan çıktı değişir mi, neden? Önce tahminini kâğıda yaz, sonra çalıştır. Ardından `printf` yerine `write(1, "A", 1)` kullanan bir sürüm yaz ve çıktısını tahmin et.

### Örnek 3 (★★): Ortak bir günlüğe eşzamanlı yazma

**Adım 1 — Anla.** Dört süreç, aynı günlük dosyasına her biri 2000 kayıt (her kayıt 100 bayt) ekleyecek. Doğru sonuç: dosya tam 800 000 bayt olmalı, her (süreç, kayıt) çifti tam bir kez ve bozulmadan görünmeli.

**Adım 2 — Örnekle.** İki yöntem deneyelim: (a) `O_APPEND` ile tek bir `write` çağrısı; (b) önce `lseek(fd, 0, SEEK_END)`, sonra `write`. İkisi de "sona yaz" gibi görünür ama ikincisinde iki adım vardır ve araya bir başka süreç girebilir.

**Adım 3 — Kaba çöz.** Basit bir çözüm (b) ile yazılabilir. Ama iki süreç aynı anda `lseek` yaparsa ikisi de aynı konumu (ör. 1000) görür ve ikisi de oraya yazar; biri diğerinin kaydının üstüne yazar.

**Adım 4 — Örüntü.** Örüntü: *konumu bulmak ile yazmak tek bir atomik işlem olmalı.* `O_APPEND` bayrağı bunu çekirdeğe bırakır: konum bulma ve yazma aynı kilit altında yapılır (Linux'ta yerel dosya sistemleri için; genel bilgi).

**Adım 5 — İyileştir.** Aşağıdaki program iki kipi (`ekle` ve `konum`) tek kodda tutar ve sonucu doğrular: her satırın biçimi, boyut ve her çiftin tam bir kez görülmesi.

```c
/* b28_11_append.c: O_APPEND ile eşzamanlı kayıt ekleme.
 *   ./b28_11_append ekle   tek write() ile O_APPEND (doğru)
 *   ./b28_11_append konum  lseek(SEEK_END) + write (yanlış) */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/stat.h>

#define SUREC   4
#define KAYIT   2000
#define BOY     100     /* bir kayıt: satır sonu dahil bayt */

static void surec_yaz(const char *yol, int s, int ekle)
{
    int fd = open(yol, O_WRONLY | (ekle ? O_APPEND : 0));
    char kayit[BOY];
    for (int i = 0; i < KAYIT; i++) {
        int n = snprintf(kayit, sizeof kayit, "surec=%d kayit=%05d ",
                         s, i);
        memset(kayit + n, '.', BOY - 1 - n);
        kayit[BOY - 1] = '\n';
        if (!ekle)
            lseek(fd, 0, SEEK_END);      /* ayrı adım: yarış */
        if (write(fd, kayit, BOY) != BOY) _exit(2);
    }
    close(fd);
}
```

```c
/* Her satırı kontrol et: biçimi doğru mu, her (süreç, kayıt)
 * çiftinden tam bir tane var mı? */
static void dogrula(const char *yol)
{
    static int gorulen[SUREC][KAYIT];
    char satir[BOY + 1];
    struct stat st;
    stat(yol, &st);
    FILE *f = fopen(yol, "r");
    int dogru = 0, bozuk = 0;
    while (fgets(satir, sizeof satir, f)) {
        int s, i;
        if (strlen(satir) == BOY &&
            sscanf(satir, "surec=%d kayit=%d", &s, &i) == 2 &&
            s >= 0 && s < SUREC && i >= 0 && i < KAYIT) {
            gorulen[s][i]++;
            dogru++;
        } else {
            bozuk++;
        }
    }
    fclose(f);
    int eksik = 0;
    for (int s = 0; s < SUREC; s++)
        for (int i = 0; i < KAYIT; i++)
            if (gorulen[s][i] != 1) eksik++;
    printf("boyut=%ld (beklenen %d)\n", (long)st.st_size,
           SUREC * KAYIT * BOY);
    printf("dogru=%d bozuk=%d eksik/fazla=%d\n", dogru, bozuk, eksik);
}
```

```c
int main(int argc, char **argv)
{
    int ekle = !(argc > 1 && strcmp(argv[1], "konum") == 0);
    const char *yol = "kayitlar.log";
    int fd0 = open(yol, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd0 < 0) return 1;
    close(fd0);

    for (int s = 0; s < SUREC; s++) {
        pid_t pid = fork();
        if (pid == 0) {
            surec_yaz(yol, s, ekle);
            _exit(0);
        }
    }
    while (wait(NULL) > 0)
        ;
    printf("mod=%s\n", ekle ? "O_APPEND" : "lseek+write");
    dogrula(yol);
    return 0;
}
```

**Adım 6 — Doğrula.** `lseek+write` kipinde iki süreç arasındaki bir yarışı elle izleyelim (mekanizmayı göstermek için; gerçek sayılar aşağıda):

| Zaman | Süreç A | Süreç B | Dosya boyu | Sonuç |
|---|---|---|---|---|
| t1 | `lseek` → 1000 | | 1000 | — |
| t2 | | `lseek` → 1000 | 1000 | — |
| t3 | `write` 100 bayt @1000 | | 1100 | A'nın kaydı kalıcı |
| t4 | | `write` 100 bayt @1000 | 1100 | **A'nın kaydının üstüne yazdı** |

`O_APPEND` kipinde ise adım t1-t2 yoktur; çekirdek konumu ve yazmayı tek seferde yapar. Gerçek çıktılar:

```term
$ ./b28_11_append ekle
mod=O_APPEND
boyut=800000 (beklenen 800000)
dogru=8000 bozuk=0 eksik/fazla=0
```

```term
$ ./b28_11_append konum
mod=lseek+write
boyut=316000 (beklenen 800000)
dogru=3160 bozuk=0 eksik/fazla=4840
```

`O_APPEND` kipinde 8000 kaydın tamamı doğru ve boyut tam. `lseek+write` kipinde ise binlerce kayıt kayboldu: bu çalıştırmada 3160 doğru, 4840 eksik ya da fazla. Sayılar her çalıştırmada değişir, ama yönü hiç değişmedi. Bu, eşzamanlılık hatasının en sinsi türüdür: tek süreçle test ederken hiçbir hata görülmez.

**Bunu AI'sız yazabilir misin?** Boş bir dosyada: iki süreç için `O_APPEND` olmadan çalışan bir sürüm yaz, sonra kayıt sayısını doğrulayan bir kontrol ekle. Hatayı bulduktan sonra `O_APPEND` ile düzelt ve yeniden çalıştır. Son soru: `O_APPEND` NFS üzerindeki bir dosyada aynı garantiyi verir mi? Bu soruyu kendi cevabınla kapat.

### Örnek 4 (★★★): Tek iş parçacığında 1000 pipe'ı epoll ile dinlemek

**Adım 1 — Anla.** Bir süreç 1000 pipe'ın okuma ucunu dinlesin. Her turda birkaç rastgele pipe'a veri yazılır. Tek bir iş parçacığı, hangi pipe'ların hazır olduğunu bulup yalnızca onları okumalı. Kısıt: her turda 1000 pipe'ı tek tek sormak yerine tek bir çağrıyla hazır olanları almalı.

**Adım 2 — Örnekle.** İlk turda beş pipe'a veri yazıldı, diyelim 131, 849, 32, 128, 644 numaralı. `epoll_wait` bunların hepsini ve yalnızca bunları döndürmeli. Okuma sonrası hazır listesi boşalmalı.

**Adım 3 — Kaba çöz.** Her pipe için `read` denemek (1000 çağrı) çalışır ama `poll` ile aynı ölçek sorununu yaşar. Daha iyi: `epoll` kaydı bir kez yap, her turda `epoll_wait` çağır, yalnızca dönenleri oku.

**Adım 4 — Örüntü.** Örüntü: *kaydı bir kez yap, olayları döngüde tüket.* Okuyucular `EAGAIN` ile kenar tetiklemeye karşı korunur: hazır bir pipe, okuma `EAGAIN` alana kadar boşaltılır.

**Adım 5 — İyileştir.** Kodun ilk kısmı (başlıklar, `boru_ac`, zamanlama) 28.12'de. Aşağıdaki `olay` fonksiyonu ve `main`, aynı dosyanın devamıdır:

```c
static void olay(void)
{
    enum { N = 1000, TUR = 20, K = 5 };
    int (*bl)[2] = malloc(N * sizeof *bl);
    int ep = epoll_create1(0);
    for (int i = 0; i < N; i++) {
        boru_ac(bl[i]);
        fcntl(bl[i][0], F_SETFL, O_NONBLOCK);
        struct epoll_event ev = { .events = EPOLLIN, .data.u32 = i };
        epoll_ctl(ep, EPOLL_CTL_ADD, bl[i][0], &ev);
    }
    srand(28);
    long yazilan = 0, okunan = 0, hazir = 0;
    struct epoll_event olaylar[64];
    char t[64];
    for (int tur = 0; tur < TUR; tur++) {
        for (int k = 0; k < K; k++) {        /* K rastgele yazma */
            int id = rand() % N;
            if (write(bl[id][1], "veri", 4) == 4) yazilan += 4;
        }
        int m = epoll_wait(ep, olaylar, 64, 0);
        hazir += m;
        for (int i = 0; i < m; i++) {        /* hazırları boşalt */
            int id = (int)olaylar[i].data.u32;
            ssize_t r;
            while ((r = read(bl[id][0], t, sizeof t)) > 0)
                okunan += r;
        }
    }
    printf("N=%d pipe, tur=%d, toplam hazır olay=%ld\n",
           N, TUR, hazir);
    printf("yazılan=%ld bayt, okunan=%ld bayt, doğru=%d\n",
           yazilan, okunan, yazilan == okunan);
    for (int i = 0; i < N; i++) {
        close(bl[i][0]); close(bl[i][1]);
    }
    close(ep);
    free(bl);
}
```

```c
int main(int argc, char **argv)
{
    struct rlimit rl;
    getrlimit(RLIMIT_NOFILE, &rl);
    rl.rlim_cur = rl.rlim_max;
    setrlimit(RLIMIT_NOFILE, &rl);

    const char *kip = argc > 1 ? argv[1] : "tetik";
    if (strcmp(kip, "tetik") == 0) tetik();
    else if (strcmp(kip, "olcek") == 0) {
        if (argc < 3) return 1;
        olcek(atoi(argv[2]));
    }
    else if (strcmp(kip, "olay") == 0) olay();
    return 0;
}
```

**Adım 6 — Doğrula.** Aynı kodun izleme kopyasıyla ilk dört turu döktük (bu kopya yalnızca döküm için çıktı veriyor; kitaptaki `olay` ile aynı tohum ve aynı `rand` sırasını kullanır). Her tur beş yazma, her biri ayrı bir pipe:

| Tur | Yazılan pipe'lar | `epoll_wait` dönüşü | Okunan pipe'lar |
|---|---|---|---|
| 0 | 131, 849, 32, 128, 644 | 5 | 131, 849, 32, 128, 644 |
| 1 | 77, 590, 985, 697, 778 | 5 | 77, 590, 985, 697, 778 |
| 2 | 172, 305, 361, 178, 317 | 5 | 172, 305, 361, 178, 317 |
| 3 | 655, 320, 20, 171, 338 | 5 | 655, 320, 20, 171, 338 |

Yirmi turun tamamında toplam 100 hazır olay sayıldı ve 400 baytın tamamı okundu; çıktı şöyle:

```term
$ ./b28_9_epoll olay
N=1000 pipe, tur=20, toplam hazır olay=100
yazılan=400 bayt, okunan=400 bayt, doğru=1
```

Dikkat: bu sayılar `rand()`'ın glibc uygulamasına ve tohuma bağlıdır; başka bir kütüphanede aynı tablo çıkmaz. Ama mantık aynıdır: `epoll_wait` her turda yalnızca yazılan pipe'ları döndürdü, `poll` olsaydı 1000 girdiyi her turda taramak zorunda kalırdı.

**Bunu AI'sız yazabilir misin?** Boş bir dosyada: 1000 pipe'ı kuran, rastgele yazmalar yapan ve yalnızca hazır olanları okuyan bir döngü yaz. Doğrulama için yazılan toplam baytın okunan toplama eşit olduğunu kontrol et. Ardından kenar tetikleme (`EPOLLET`) ekle ve okumayı `EAGAIN`'e kadar sürdürmezsen neyin kaybolduğunu göster.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir dosya kaydedici ya da dosya sistemi üretmek değil, kalıcılık, sıralama ve bozuk verinin ayıklanması konusunda kendi kararlarını vermek. Takıl, kâğıda çiz, küçük testler yaz; çözümü dışarıdan alma.
:::

### Proje 1 (★★): Güç kesintisine dayanıklı telemetri kaydedici

**Amaç:** Bir sensörden gelen ölçümleri (zaman damgası ve birkaç sayı) ekle-yaz (append-only) bir günlük dosyasına kaydeden bir kütüphane yaz. Kayıtlar kalıcı olmalı; program ya da sistem aniden kapansa bile açılışta tutarlı bir durum elde edilmeli.

**Beklenen davranış:** Her kayıt bir uzunluk alanı, yük ve bir CRC ile biter. Yazma `write` ile yapılır; belirli aralıklarla (ör. her 50 kayıtta bir) `fsync` çağrılır. Açılışta dosya baştan taranır: geçerli kayıtlar okunur, sonda yarım ya da CRC'si tutmayan son kayıt kırpılır (`ftruncate`). Ortadaki bir bozuk kayıt görülürse bu bir hata olarak raporlanır, sessizce atlanmaz.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Kayıt biçimini önce kâğıda çiz: `[uzunluk:4][CRC:4][yük...]`. CRC için basit bir sağlama (ör. CRC-32 ya da kendi yazdığın bir toplam) yeter. Kırpma kararını yalnızca dosyanın son kaydına uygula. `kill -9` testi için ayrı bir süreç yazıp rastgele zamanda öldür; ardından kayıt sayısını ve bütünlüğü doğrula. `fsync`'in aralığını değiştirerek kayıp penceresi ile performans arasındaki dengeyi ölç ve bir tablo çıkar.

**Başarı kriterleri:**
- 500 rastgele `kill -9` denemesinin hiçbirinde açılış çökmüyor ve hiçbir bozuk kayıt "geçerli" olarak okunmuyor.
- Kabul edilmiş (yazma döndü ve `fsync` sonrası) her kayıt açılışta mevcut; kayıp, yalnızca son `fsync`'ten sonraki kayıtlarla sınırlı.
- Her `fsync` aralığı için kayıp penceresi ve yazma hızı ölçülmüş ve raporlanmış.

### Proje 2 (★★★): Basit bir dosya sistemi görüntüsü

**Amaç:** Tek bir dosyada tutulan (dosya sistemi görüntüsü) küçük bir dosya sistemi yaz. İçinde süper blok, inode tablosu, blok bitmap'i ve tek seviyeli bir dizin olsun. Blok boyutu 512 bayt. Program dosyaları oluşturabilmeli, okuyabilmeli, silebilmeli ve görüntü dosyasını kapatıp yeniden açtığında içerik aynı kalmalı.

**Beklenen davranış:** `oluştur`, `yaz`, `oku`, `sil`, `listele` komutları. Her dosyanın bir inode'u, bir dizin girdisi (ad, inode numarası) ve bir veri blok listesi var. Silme, dizin girdisini kaldırır, inode'u ve blokları bitmap'te serbest bırakır. Bir `dogrula` komutu tutarlılığı denetler: her kullanılan bloğun bitmap'te işaretli olması, her dizin girdisinin geçerli bir inode'a işaret etmesi, bağlantı sayılarının doğruluğu.

**Önerilen yaklaşım (ipucu):** Önce diskteki düzeni kâğıda çiz: süper blok (blok 0), inode bitmap, blok bitmap, inode tablosu, veri blokları. Her yapıyı sabit boyutlu bir C struct'ı olarak tanımla ve `pread`/`pwrite` ile belirli bir bloğa git. Dosya boyutu bir bloktan büyükse ikinci bir dolaylı blok ihtiyacı doğar; ilk sürümde doğrudan blok sayısını sınırla ve bunu belgele. Bu projede FAT'taki zincir fikrini mi, yoksa bir blok listesini mi kullanacağına kendin karar ver ve gerekçesini yaz.

**Başarı kriterleri:**
- 1000 dosya oluşturulup yarısı silindikten sonra `dogrula` hata vermiyor.
- Görüntü kapatılıp açıldıktan sonra tüm dosya içerikleri birebir aynı.
- Bitmap'te sızıntı yok: silinen dosyaların blokları yeniden kullanılabiliyor.
- Görüntü dosyası üzerinde bir bayt rastgele bozulduğunda `dogrula` bunu yakalıyor (bir sağlama alanı ekleyerek ya da tutarsızlığı bularak).

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Açık ama silinmiş.** Bir dosyayı açıp `unlink` ettikten sonra `close` yapmadan `fstat` çağırırsan `st_nlink` kaç olur? `close`'dan sonra inode'un serbest kalması için hangi koşulların birlikte sağlanması gerekir?
2. **★ — Ofset kimin?** İki süreç aynı açık dosya girdisini paylaşıyorsa biri `lseek` yaptığında diğeri ne görür? `dup(fd)` ile aynı sonucu alır mısın?
3. **★ — Kısa okuma sayımı.** Bir borudan 10 000 bayt okuyan bir döngü, borunun her seferinde en fazla 4096 bayt verdiğini varsayarsa en az kaç `read` çağrısı yapar? Döngüyü yazmadan önce tahmin et.
4. **★★ — Tampon ve yazma sayısı.** Bir programın `fwrite` ile 1 bayt yazan 1 milyon döngüsü, tampon 4096 bayt iken kaç `write` sistem çağrısı üretir? Tamponu 1 MiB yaparsan bu sayı nasıl değişir?
5. **★★ — Mülakat: atomik rename.** `rename` tek başına yeterli değildir. Hedef dosyanın verisi `fsync` edilmemişse ne olabilir? Dizin `fsync` edilmemişse ne olabilir?
6. **★★ — Mülakat: iki kez açmanın bedeli.** Aynı dosyayı bir süreç iki kez `open` ederse ve biri yazıyor, diğeri okuyorsa okuyucu yazılanları ne zaman görür? Bu, `O_APPEND` ile ilişkili midir?
7. **★★ — Mülakat: büyük dosya ve ofset.** `off_t` 32 bitlik olsaydı 4 GiB'ı aşan bir dosyada `lseek` ne yapardı? `_FILE_OFFSET_BITS=64` tanımının amacını açıkla.
8. **★★ — Mülakat: kenar tetikleme tuzağı.** Kenar tetiklemeli `epoll` ile bir soketten okuyan bir sunucu, her olayda yalnızca bir `read` yapıyor. Hangi koşulda veri sonsuza dek okunmadan kalır?
9. **★★ — Mülakat: açık dosya ve disk alanı.** Bir günlük dosyası silindi ama uygulama hâlâ onu açık tutuyor. `df` ve `du` neden farklı sonuç verir? Hangi komutla silinen ama açık dosyaları bulursun?
10. **★★★ — Mülakat: fsync hatası.** Bir `fsync` çağrısı `EIO` döndürdü. Bir sonraki `fsync` çağrısı neden başarılı dönebilir? Uygulama bu durumda ne yapmalı?
11. **★★★ — Mülakat: dizin girdisi.** Sabit bağlar dizinler için neden yasaktır? Bir dizine iki ad bağlansaydı hangi döngü ve tutarlılık sorunları ortaya çıkardı?
12. **★★★ — Mülakat: mmap ile sıralı okuma.** Büyük bir dosyayı baştan sona tek seferde okuyup bir toplam hesaplayan bir program için `mmap` ile `read` arasında hangisini seçersin? Seçimini sayfa hatası ve kopyalama maliyetiyle gerekçelendir.

## Kod Okuma Egzersizi

Bugünkü kesit, Linux çekirdeğinin dosya nesnelerinin en merkezi yapısı olan `struct file`'dan alındı. Kaynak: Linux **v6.6**, `include/linux/fs.h`, 992–1031. satırlar. Dosya, `torvalds/linux` deposunun v6.6 etiketinden (jsDelivr aynası üzerinden) indirildi ve kesit birebir alındı. **Sadeleştirme:** `union` bloğu ile `CONFIG_SECURITY` ve `CONFIG_EPOLL` koşullu alanları çıkarıldı; çoğu açıklama yorumu kaldırıldı. Kalan üç not orijinalde olduğu gibi korundu: `f_inode` satırındaki `cached value`, `private_data` üstündeki `needed for tty driver` ve `f_sb_err` satırındaki `for syncfs`. Sekmeler boşluğa çevrildi.

```c
struct file {
 spinlock_t f_lock;
 fmode_t f_mode;
 atomic_long_t f_count;
 struct mutex f_pos_lock;
 loff_t f_pos;
 unsigned int f_flags;
 struct fown_struct f_owner;
 const struct cred *f_cred;
 struct file_ra_state f_ra;
 struct path f_path;
 struct inode *f_inode; /* cached value */
 const struct file_operations *f_op;

 u64 f_version;
 /* needed for tty driver, and maybe others */
 void *private_data;

 struct address_space *f_mapping;
 errseq_t f_wb_err;
 errseq_t f_sb_err; /* for syncfs */
} __randomize_layout
  __attribute__((aligned(4)));
```

Bu yapı, 28.4'teki üçlünün açık dosya tablosu tarafıdır. Bölüm 21'de gördüğün `struct file_operations` ise `f_op` alanıyla buraya bağlanır (fs.h içinde 1852. satır).

**Sorular — cevaplamadan geçme:**

1. `f_pos` ofseti ile `f_pos_lock` mutex'i ayrı alanlardır. Ofset okuma ve yazma sırasında neden kilitli tutulur? İki süreç aynı `struct file`'ı paylaştığında bu kilit hangi yarışı önler? (Bölüm 27'deki senkronizasyon kavramlarına bağla.)
2. `f_count` bir `atomic_long_t`'dir. `fork` ve `dup` çağrıları bu sayacı nasıl etkiler ve sayaç sıfıra düştüğünde hangi işlemler yapılır? Bu sayaç olmasaydı hangi bellek hatası ortaya çıkardı?
3. `f_inode` alanı "cached value" olarak işaretlenmiş. Bu, `f_path` içindeki dentry'den de inode'a ulaşılabileceği anlamına mı gelir? Önbelleklemenin hız kazancı ile tutarlılık riski arasındaki dengeyi açıkla.
4. Yapının sonundaki `__randomize_layout` niteliği ile Bölüm 21'deki sabit ofset varsayımı nasıl çelişir? Sürücü modülleri bu yapının alanlarına doğrudan ofsetle erişmek zorunda olsaydı ne olurdu?
5. `private_data` alanı `void *` tipindedir. Bir sürücü bu alana kendi durum yapısını koyduğunda, çekirdek bu yapının tipini nasıl bilir? C'de genel amaçlı işaretçinin bu kullanımı, Bölüm 21'deki OCP tartışmasıyla nasıl ilişkilidir?
6. `f_wb_err` ve `f_sb_err` alanları yazma hatalarını takip eder. Bir `fsync` hatası bildirildikten sonra, aynı dosya için sonraki bir `fsync` neden başarılı dönebilir? Bu, Bölüm 28.7'deki kalıcılık kuralını nasıl etkiler?

## Bölüm Özeti

- G/Ç, her şeyi bir dosya tanımlayıcısı (fd) üzerinden yapmanın Unix sözleşmesidir; `read`, `write`, `lseek` ve `close` bu sözleşmenin çekirdeğidir.
- Süreç fd tablosu, açık dosya tablosu (`struct file`) ve inode tablosu üç ayrı katmandır; `fork` sonrası paylaşılan açık dosya girdisi ofseti de paylaşır, ayrı `open` ise ayrı ofset verir.
- Kısa okuma ve kısa yazma bir hata değil sözleşmenin parçasıdır; her G/Ç için `tam_oku` ve `tam_yaz` tarzı bir döngü gerekir.
- Tampon iki yerdedir: stdio (kullanıcı alanı) sistem çağrısı sayısını azaltır, sayfa önbelleği diske inişi geciktirir. `fork` öncesi tamponu boşaltmazsan çift çıktı alırsın.
- `write` veriyi kalıcı yapmaz; `fsync` yapar ve disk gecikmesi kadar pahalıdır. Kalıcılıkta sıra önemlidir: önce veri, sonra kayıt.
- Atomik güncelleme kalıbı (geçici dosya, `fsync`, `rename`, dizin `fsync`) süreç çökmelerine karşı güvenlidir; güç kesintisi için de aynı adımların tamamı gerekir.
- Dosya sistemi meta veriyi inode'da, adı dizinde, içeriği veri bloklarında tutar; silmek `unlink`'tir ve açık dosyanın verisi bağlantı sayısı sıfırlanana kadar yaşar.
- ext4 extent, gecikmeli ayırma ve `data=ordered` günlüklemesi; FAT ise küme zinciri ile çalışır. VFS katmanı bu farklı dosya sistemlerini `file`, `inode` ve `dentry` nesneleri ile tek arayüzde toplar.
- `mmap`, dosyayı sanal belleğe eşler; kopyayı ortadan kaldırır ama sayfa hatası maliyeti getirir. `epoll` ise çok sayıda fd'de yalnızca hazır olanları döndürerek `poll`'un doğrusal maliyetini aşar.

**Kısım VI'nın kapanışı.** Bu bölümle Kısım VI tamamlandı. Bir programın hayatını takip ettiysen zincir şöyle: CPU komutları çalıştırır (Bölüm 24), veri bellekte yaşar (Bölüm 25), her çalışan birim bir süreç ya da iş parçacığıdır (Bölüm 26), paylaşılan kaynaklar senkronizasyonla korunur (Bölüm 27) ve sonuç dış dünyaya ancak G/Ç yoluyla çıkar (Bölüm 28). G/Ç, bu zincirin en yavaş halkasıdır ve en çok hata yapılan halkasıdır: her ölçümde görüldüğü gibi, milisaniyeler ile mikrosaniyeler arasındaki fark, hatalı bir tamponun ya da eksik bir `fsync`'in bedelidir.

**Sonraki bölümde:** Bölüm 29 (OSI & TCP/IP) ile Kısım VII — Ağ başlıyor. Bu bölümde gördüğün `read` ve `write` sözleşmesi soketlerde de geçerli olacak; kısa okumanın ve `epoll`'un ağ tarafındaki karşılığı, bağlantı yönetiminin temelini oluşturacak. Dosya ile soket arasındaki ortak arayüz, Unix'in "her şey bir dosyadır" fikrinin bugüne kadar taşınmasının nedenidir.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. `write` döndü ve sıfırdan büyük bir değer verdi. Verinin elektrik kesintisinden sonra da kalacağını söyleyebilir misin? Hangi adım eksikse veri kaybolabilir?
2. `fork` sonrası iki süreç aynı dosyayı kullanıyor. Biri `lseek` yaparsa diğerine ne olur? İki ayrı `open` çağrısı bu davranışı nasıl değiştirir?
3. Bir yapılandırma dosyasını atomik olarak güncelleyen kalıbı adım adım yaz. `rename`'den önce `fsync` neden gerekli, `rename`'den sonra dizin `fsync`'i neden gerekli?
4. Seviye tetikleme ile kenar tetikleme arasındaki fark nedir? Kenar tetiklemeli bir okuyucu neden `EAGAIN` alana kadar okumak zorundadır?
5. Açık bir dosya silindiğinde disk alanı ne zaman geri kazanılır? `df` ile `du` aynı sonucu vermeyebilir; bu fark neden olur?
6. `mmap` ile `read` arasında bir seçim yapman gerekseydi, hangi iş yükü için hangisini seçerdin ve bunu hangi ölçümle doğrulardın?
7. Sabit bağ ile sembolik bağ arasındaki fark nedir? Sabit bağın bir dizine yapılmasını çekirdek neden yasaklar?
8. Bir veritabanı günlüğünde `fsync` çağrısı yavaş. Bu yavaşlığı azaltmak için hangi tasarım seçeneklerin var ve her birinin dayanıklılık bedeli ne?
:::
