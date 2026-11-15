%% kisim_no: VI
%% kisim_ad: İşletim Sistemi & Mimari
%% bolum_no: 26
%% baslik: Process & Thread

## Giriş: Aynı anda birden çok iş

Bilgisayarında bu satırı okurken arka planda tarayıcı, bir müzik uygulaması, belki bir derleyici ve birkaç sistem servisi çalışıyor olabilir. Oysa işlemci çekirdeklerinin sayısı sınırlıdır ve her çekirdek bir anda yalnızca bir komut akışını yürütebilir. Aradaki farkı kapatan şey işletim sistemidir. Çalışan her programı bir **süreç (process)** olarak tanımlar, süreçleri CPU'ya sırayla atar ve her birine kendi adres uzayını verir. Süreç içindeki yürütme akışlarına ise **iş parçacığı (thread)** denir.

Bu konu mülakatın vazgeçilmezidir: "süreç ile iş parçacığı arasındaki fark nedir?", "bağlam değişimi neden pahalıdır?", "iki iş parçacığı aynı sayacı artırınca ne olur?" soruları neredeyse her sistem ve backend mülakatında çıkar. Savunma ve gömülü sistemlerde de aynı mekanizma vardır: bir İHA'da sensör okuma, kontrol döngüsü ve haberleşme ayrı görevler olarak zamanlanır ve bunlardan birinin gecikmesi uçuşu doğrudan etkiler. Mert'in **MertOS** çekirdeğinde de bir `ProcessManager` sınıfı süreçleri round-robin bir zamanlayıcıyla yönetiyor; kaynağını aşağıda inceleyeceğiz.

Bölüm 4'te `ps`, `kill`, `&`, `jobs`, `fg` ve `bg` komutlarını zaten kullandın; bu bölümde o komutların gösterdiği süreç dünyasının kendisini açacağız. Bölüm 8'deki çağrı yığını her sürecin kendi yığınına sahip olmasının nedenini, Bölüm 18'deki açgözlü zamanlama kuralları ise zamanlayıcının kararlarının matematiksel temelini verir.

::: not
Bu bölümdeki deneylerin çoğunu WSL2 üzerinde Ubuntu 24.04, gcc 13.3 ile yaptık; zamanlama ölçümlerini ve Python deneylerini ise Windows üzerinde Python 3.12.10 ile çalıştırdık. Zamanlama sayıları sanal makinenin yüküne ve donanıma bağlı olarak değişir. Kitaptaki sayıları "bu ortamda şu kadar" diye okumalı, kendi makinende aynı betiklerle yeniden ölçmelisin.
:::

## 26.1 Program, süreç ve süreç kontrol bloğu

Program ile süreç arasındaki fark ilk bakışta küçük görünür, ama her şeyin başlangıcıdır. **Program**, diskte duran pasif bir dosyadır. Linux'ta bu dosya genellikle ELF biçimindedir ve makine komutlarını, başlangıç verisini ve yükleyici için bilgiyi taşır. Program kendi başına hiçbir şey yapamaz; CPU onu okumaz.

**Süreç**, o programın çalışan bir örneğidir. Aynı programı üç kez başlatırsan üç ayrı süreç elde edersin; her birinin kendi yazmaçları, kendi bellek alanı ve kendi kimliği (PID) vardır. Bir sürecin bileşenleri şunlardır:

- **Adres uzayı:** kod (text), başlangıç değerli veri (data), sıfırlanmış veri (bss), yığın (stack) ve yığın alanı (heap). Bu bölgelerin ayrıntısı Bölüm 25'te, sanal bellek bağlamında işlenecek.
- **Yazmaçlar ve program sayacı:** CPU'nun o an hangi komutta olduğu ve ara değerler.
- **Açık kaynaklar:** açık dosyalar, borular, soketler. Bunlar dosya tanımlayıcı (file descriptor) adıyla anılır; Bölüm 28'de derinleşecek.
- **Kimlik ve izinler:** PID, ebeveynin kimliği (PPID), kullanıcı ve grup kimlikleri.

İşletim sistemi bu bilgileri bir yapıda tutar. Bu yapıya **süreç kontrol bloğu (PCB, Process Control Block)** denir. Kavram her işletim sisteminde aynıdır; Linux çekirdeğinde bu yapı `task_struct` adıyla anılır (genel bilgi: `include/linux/sched.h`). Şekil 26.1, bir programın diskten belleğe nasıl taşındığını ve PCB'nin süreci nasıl temsil ettiğini gösteriyor.

![Şekil 26.1: Program diskte pasif bir dosyadır; exec() ile bellekte bir süreç olur. PCB, süreç hakkındaki bilgileri (PID, durum, yazmaçlar, açık dosyalar) tutar.](gorseller/b26_program_surec.png)

Terminalde bir komut yazdığında arka planda ne olduğunu Bölüm 4'te gördük: kabuk önce kendini kopyalar (`fork`), sonra yeni programı yükler (`exec`) ve sonucu bekler (`wait`). Bu üç adım, bu bölümün ana konusu olan Linux süreç API'sinin çekirdeğidir.

## 26.2 Süreç durumları ve geçişler

Bir süreç hayatı boyunca farklı durumlardan geçer. Bu durumlar, zamanlayıcının neyi neden seçtiğini ve bazı süreçlerin neden "takılı" göründüğünü açıklar. Genel model beş durum içerir:

- **YENİ (new):** süreç oluşturuldu ama henüz çalışmaya başlamadı.
- **HAZIR (ready):** çalışmaya hazır; yalnızca bir CPU boşalmasını bekliyor.
- **ÇALIŞIYOR (running):** şu an bir CPU çekirdeğinde yürütülüyor.
- **BEKLİYOR (waiting/blocked):** bir olayı bekliyor: disk okuması, ağ paketi, bir sinyal ya da bir kilit. CPU'ya ihtiyacı yoktur.
- **ZOMBİ (zombie):** süreç sonlandı, ama ebeveyni henüz çıkış durumunu almadı. Bellek büyük ölçüde geri verildi; geriye PCB'nin küçük bir kısmı kaldı.

Şekil 26.2 bu durumlar arasındaki geçişleri gösteriyor. Süreç bir G/Ç isteğinde bulunduğunda CPU'yu kendisi bırakır: ÇALIŞIYOR'dan doğrudan BEKLİYOR'a geçer. Bekleme bitince HAZIR'a döner ve zamanlayıcının onu seçmesini bekler. Zamanlayıcı ise dilim dolduğunda ya da daha öncelikli bir süreç hazır olduğunda çalışan süreci HAZIR'a geri koyar.

![Şekil 26.2: Süreç durum makinesi. Zamanlayıcı HAZIR ile ÇALIŞIYOR arasında karar verir; G/Ç veya olay beklemesi süreci BEKLİYOR'a taşır.](gorseller/b26_durum_makinesi.png)

Linux'un `ps` komutu bu durumları `STAT` sütununda gösterir. Man sayfasına göre başlıca harfler `R` (çalışıyor veya hazır), `S` (kesilebilir uyku), `D` (kesilemez uyku, genellikle disk), `T` (durdurulmuş) ve `Z` (zombi). Bu bölümde zombi durumunu bizzat göreceğiz. Mert'in MertOS çekirdeğinde ise aynı fikir `ProcessState` numaralandırmasıyla kodlanmış. `kernel/process/process.hpp` dosyasında 27–35. satırlarda yedi değerli bir enum var: `UNUSED`, `CREATED`, `RUNNING`, `READY`, `BLOCKED`, `SLEEPING` ve `ZOMBIE`. Linux'taki beş durumun iki ek ayrıntısı (`CREATED` ve `SLEEPING`) MertOS'ta açıkça görünüyor; bu ayrım zamanlayıcının kodunu okunur kılar.

## 26.3 Linux süreç API'si: fork, exec, wait

Linux'ta yeni süreç oluşturmanın standart yolu iki sistem çağrısıdır: `fork()` mevcut süreci kopyalar, `exec*()` ailesi ise süreci yeni bir programla değiştirir. Bu ayrım ilk bakışta gereksiz görünür, ama kabuğun boru ve yönlendirme yapabilmesi tam olarak bu ayrımdan gelir: çocuk süreç, `exec`'ten önce kendi dosya tanımlayıcılarını ayarlayabilir.

### fork(): iki süreç, bir çağrı

`fork()` çağrıldığında çekirdek yeni bir PCB oluşturur ve adres uzayını kopyalar. Çağrı **iki kez** döner: ebeveynde yeni çocuğun PID'sini, çocukta ise `0`'ı döndürür. Hata durumunda `-1` döner ve `errno` nedenini belirtir. Bu dönüş değeri farkı, iki sürecin aynı kodu farklı dallardan izlemesini sağlar.

Kopyalama maliyetli görünse de Linux bunu **kopyala-yazarken-kopyala (copy-on-write, COW)** ile erteler. Fork anında fiziksel sayfalar paylaşılır ve her iki sürecin sayfa tablosunda salt-okunur işaretlenir. Süreçlerden biri bir sayfaya yazmaya kalktığında CPU bir sayfa hatası (page fault) üretir; çekirdek o sayfanın kopyasını ayırır, yazanın sayfa tablosunu yeni kopyaya yönlendirir ve yazma işlemini yeniden dener. Sayfa tablosu ve sayfa hatasının ayrıntısı Bölüm 25'te; burada sonucu kullanacağız. Şekil 26.3 bu mekanizmayı iki aşamada gösteriyor.

![Şekil 26.3: Fork sonrası COW. Önce iki süreç aynı fiziksel sayfayı görür; çocuk yazdığında yalnızca onun sayfası kopyalanır.](gorseller/b26_fork_cow.png)

Aşağıdaki program, fork sonrası değişkenlerin bağımsız olduğunu gösterir. Çocuk `sayac`'ı 15'e çıkarır, ebeveyn ise 10'da kalır: iki süreç aynı sanal adresi kullansa da değerler birbirinden ayrılmıştır.

```c
/* fork_temel.c: fork sonrası değişken bağımsızlığı.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int sayac = 10;
    setvbuf(stdout, NULL, _IONBF, 0); /* tampon karışıklığını önle */

    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {                   /* çocuk: fork 0 döndürdü */
        sayac += 5;
        printf("çocuk : pid=%d ppid=%d sayac=%d\n",
               (int)getpid(), (int)getppid(), sayac);
        return 0;
    }

    int durum = 0;
```

Programın kalan kısmı ebeveynindir: çocuğu bekler ve sonucu yazdırır.

```c
    /* çocuğu bekle: zombi bırakma */
    waitpid(pid, &durum, 0);
    printf("ebeveyn: pid=%d çocuk=%d sayac=%d\n",
           (int)getpid(), (int)pid, sayac);
    return 0;
}
```

Derleyip çalıştırdığında şunu görürsün. PID değerleri her çalıştırmada değişir, ama satır sırası ve sayaç değerleri değişmez:

```term
$ gcc -O2 -Wall -Wextra -std=c11 fork_temel.c -o fork_temel
$ ./fork_temel
çocuk : pid=74544 ppid=74543 sayac=15
ebeveyn: pid=74543 çocuk=74544 sayac=10
```

Burada iki nokta dikkat çekiyor. Birincisi, `setvbuf` ile tamponu kapattık; bunun nedenini 26.3'ün sonunda göreceksin. İkincisi, ebeveyn çocuğu `waitpid` ile bekler; aksi hâlde çocuk zombi olabilir.

### exec() ailesi: süreci yeni programla değiştirmek

`exec*()` ailesi (`execv`, `execvp`, `execl` ve benzerleri) çağıran sürecin bellek görüntüsünü yeni bir programla değiştirir. Başarılı bir `exec` **geri dönmez**: kod ve veri yeni programınkiyle yer değiştirir, ama PID aynı kalır ve kapatma bayrağı ayarlanmamış açık dosya tanımlayıcıları miras kalır. Bu miras, kabuğun `dup2` ile ayarladığı boruların yeni programa ulaşmasını sağlar. Bölüm 4'teki `gcc`'nin dört aşamasını hatırla: `gcc` sürücüsü de kendi içinde `exec` ile `cc1`, `as` ve bağlayıcıyı çalıştırır.

Hata durumunda `exec` `-1` döner ve kod devam eder. Bu yüzden çocuk kodunda `exec` çağrısından sonra gelen satırlar hata işleme içindir: kabuğumuz bunu `perror` ve `_exit(127)` ile yapar.

### wait() ailesi ve çıkış durumu

Çocuk sona erdiğinde ebeveynin bunu öğrenmesi gerekir: çıkış kodunu almak ve PCB'yi serbest bırakmak için `wait` veya `waitpid` çağrılır. Çıkış durumu tek bir `int` içinde kodlanır ve doğrudan okunmamalıdır; makrolar kullanılır:

- `WIFEXITED(durum)`: süreç `exit` veya `return` ile normal bitti mi?
- `WEXITSTATUS(durum)`: normal bitişte çıkış kodu.
- `WIFSIGNALED(durum)`: süreç bir sinyal ile mi sonlandı?
- `WTERMSIG(durum)`: bu durumda sinyal numarası.

Bu kodlama `man 2 wait` belgesinde tanımlıdır. Normal çıkışta çıkış kodu durum değerinin 8 ila 15. bitlerinde, sinyal ile sonlanmada ise sinyal numarası düşük yedi bitte durur. Makroları kullanmak, bit düzeni değişse bile kodunun bozulmamasını sağlar.

### Zombi ve yetim süreçler

Bir çocuk sonlandığında ebeveyn `wait` çağırmazsa çocuğun PCB'si bellekte kalır ve süreç **zombi** olur. Zombinin bellek ve dosya kaynakları serbest bırakılmıştır, ama süreç tablosunda bir girişi yer kaplar; çok sayıda zombi biriktiğinde PID'ler tükenebilir. Aşağıdaki program iki senaryoyu kurar: `zombi` modunda ebeveyn 20 saniye boyunca `wait` çağırmadan uyur; `yetim` modunda ise ebeveyn önce çıkar ve çocuk yetim kalır.

```c
/* zombi_yetim.c:
 *   ./zombi_yetim zombi -> çocuk çıkar, ebeveyn 20 sn
 *                          wait çağırmadan uyur (zombi oluşur)
 *   ./zombi_yetim yetim -> ebeveyn önce çıkar, çocuk yetim
 *                          kalır ve yeni ebeveyne devredilir */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 2) {
        fprintf(stderr, "kullanım: %s zombi|yetim\n", argv[0]);
        return 1;
    }

    pid_t pid = fork();
    if (pid == 0) {
        if (strcmp(argv[1], "zombi") == 0) {
            printf("çocuk %d: çıkıyorum\n", (int)getpid());
            /* ebeveyn wait etmezse zombi olur */
            return 0;
        }
```

Programın son kısmı, ebeveynin iki moda göre farklı davranışını yazar: zombi modunda çocuğu sonunda toplar, yetim modunda ise çıkar.

```c
        /* yetim senaryosu: ebeveyn çıkana kadar bekle */
        sleep(3);
        printf("yetim %d: yeni ebeveyn ppid=%d\n",
               (int)getpid(), (int)getppid());
        sleep(10);
        return 0;
    }

    if (strcmp(argv[1], "zombi") == 0) {
        printf("ebeveyn %d: çocuk=%d, 20 sn uyuyorum (wait yok)\n",
               (int)getpid(), (int)pid);
        sleep(20);                    /* bu sürede ps ile bak */
        waitpid(pid, NULL, 0);        /* sonunda topla */
    } else {
        printf("ebeveyn %d: çıkıyorum, çocuk=%d yetim kalacak\n",
               (int)getpid(), (int)pid);
    }
    return 0;
}
```

Programı arka plana alıp `ps` ile baktığında zombiyi görürsün. Çıktıdaki `Z` durumu, çocuğun çıkmış ama toplanmamış olduğunu gösterir:

```term
$ ./zombi_yetim zombi &
ebeveyn 53010: çocuk=53012, 20 sn uyuyorum (wait yok)
çocuk 53012: çıkıyorum
$ ps -eo pid,ppid,stat,comm | grep zombi_yetim
  53010   52999 S+   zombi_yetim
  53012   53010 Z+   zombi_yetim
```

Yetim senaryosunda çocuğun ebeveyni değişir. Linux, ebeveyni çıkmış süreçleri varsayılan olarak PID 1'e (init veya systemd) devreder; böylece yetim sürecin sonunda toplanması garanti altına alınır. Bizim WSL ortamımızda ise yetim süreç PID 1 yerine ebeveynin üst zincirindeki bir süreçle devredildi (`ppid=52998`). Bunun nedeni, bir sürecin `PR_SET_CHILD_SUBREAPER` ile kendisini yetimlerin toplayıcısı (subreaper) ilan edebilmesidir; WSL'in iç süreç yapısı böyle bir toplayıcı içeriyor olabilir. Yani PID 1'in ebeveyn olması bir garanti değil, varsayılan davranıştır. Bu ayrıntı Bölüm 42'de konteyner içindeki PID 1 sorununda karşımıza çıkacak.

::: dikkat
Zombi süreci öldürerek temizleyemezsin: zaten ölüdür. Onu yalnızca ebeveynin `wait` çağrısı kaldırır. Ebeveyn takılmışsa zombi de ebeveyn çıkana kadar kalır.
:::

### Fork bombası: çalıştırmadan anla

Bir sürecin kendini sürekli kopyalaması süreç tablosunu birkaç saniyede doldurabilir. Klasik "fork bombası", bunu bilerek yapan bir kabuk satırıdır: her süreç iki süreç üretir ve sayı üstel büyür. Sistem, kullanıcının süreç sınırına (`ulimit -u`) ya da cgroup'un `pids` denetleyicisine takılana kadar yanıt vermez hâle gelir. Bu kitapta böyle bir programı **çalıştırmanı istemiyoruz**. Anlamak için yeterli olan şey, bir sürecin kendi kopyasını iki kez başlatmasının üstel büyüme demek olduğudur. 26.3'ün sonunda aynı mantığı kontrollü bir ölçekte göreceğiz.

### Döngüde fork: süreç ağacı ve tampon tuzağı

Bir döngü içinde `fork` çağırdığında süreç sayısı her turda ikiye katlanır. Aşağıdaki program üç tur çalışır; her sürecin bir `x` satırı yazdığını ve toplam satır sayısını ölçtüğümüzü düşün.

```c
/* fork_agac.c: döngü içinde fork; her sürecin bir printf'i var.
 * Kullanım: ./fork_agac      (tamponlu stdout)
 *           ./fork_agac -u   (stdout tamponsuz) */
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "-u") == 0)
        setvbuf(stdout, NULL, _IONBF, 0);

    for (int i = 0; i < 3; i++) {
        /* her turda süreç sayısı ikiye katlanır */
        fork();
        printf("x\n");
    }
    return 0;
}
```

Programı iki çıktı moduyla çalıştırıp satırları sayalım. Tamponsuz modda (`-u`) her süreç tek satırı hemen yazar. Tamponlu modda ise `printf` çıktıyı bir tamponda biriktirir; boru ya da dosyaya yönlendirildiğinde tampon yalnızca dolduğunda ya da süreç çıktığında boşaltılır:

```term
$ ./fork_agac -u | wc -l
14
$ ./fork_agac | wc -l
24
```

Tamponsuz sonucu kolayca açıklarız: tur 1'de 2 süreç, tur 2'de 4 süreç ve tur 3'te 8 süreç birer satır yazar; toplam `2 + 4 + 8 = 14`. Tamponlu sonuç ise 24'tür, çünkü `fork` anında ebeveynin tamponunda henüz boşaltılmamış satırlar çocuğa kopyalanır. Her süreç, `fork`'a kadar biriken satırları kendi tamponunda taşır ve çıkarken hepsini yazar. Şekil 26.4, sekiz sürecin nasıl oluştuğunu ve tamponsuz toplamın nasıl hesaplandığını gösteriyor.

![Şekil 26.4: Süreç ağacı. Üç turda sekiz süreç oluşur; kenar etiketi fork'un hangi turda yapıldığını gösterir.](gorseller/b26_fork_agaci.png)

Bu tuzak, `fork`'tan önce `stdout`'a yazılmış verinin neden iki kez göründüğünü de açıklar ve gizemli çift çıktılara yol açar. Çözüm, `fork`'tan önce `fflush(stdout)` çağırmak ya da tamponsuz moda geçmektir; bu bölümdeki `zombi_yetim.c`, `sig.c` ve `fork_temel.c` programları bunun için `setvbuf` kullanır.

## 26.4 Mini kabuk: fork, exec, wait, boru ve yönlendirme

Terminalde her gün kullandığın kabuğun çekirdeği, yukarıdaki sistem çağrılarının bir araya gelmesidir. Bu bölümde bunu kendi ellerinle yazacaksın. Kabuğumuz şu özellikleri destekler: argümanlı komutlar, `|` ile boru hattı, `<` ve `>` ile yönlendirme, sonda `&` ile arka plan çalıştırma, `cd` ve `exit`.

Tasarımın üç kuralı var. Birincisi, `cd` gibi komutlar **kabuğun içinde** çalıştırılmalıdır: çocuk süreç kendi çalışma dizinini değiştirirse ebeveyn etkilenmez. İkincisi, boru hattındaki her komut kendi çocuk sürecinde çalışır ve dosya tanımlayıcıları `dup2` ile birbirine bağlanır. Üçüncüsü, arka plan çocukları zombi kalmamalıdır; bunları `SIGCHLD` sinyali ve `waitpid(-1, ..., WNOHANG)` ile toplayacağız.

Programı parça parça inceleyeceğiz. İlk parça başlıkları, komut yapısını ve `SIGCHLD` işleyicisini içerir:

```c
/* msh.c: minik kabuk. Destek: argümanlar, |, <, >, &, cd, exit.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L msh.c -o msh
 * HATA_ACIK tanımlanırsa ebeveyn boru yazma ucunu kapatmaz. */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_ARG   64
#define MAX_KOMUT 8

typedef struct {
    char *argv[MAX_ARG];
    char *giris;               /* < dosyası, NULL ise yok */
    char *cikis;               /* > dosyası, NULL ise yok */
} Komut;

static volatile sig_atomic_t g_cocuk_bitti = 0;

/* İşleyici yalnızca bayrak kaldırır: printf, malloc
 * gibi async-signal-safe olmayan işlere girilmez. */
static void on_chld(int sig)
{
    (void)sig;
    g_cocuk_bitti = 1;
}
```

İkinci parça, satırı komutlara ayıran ayrıştırıcıdır. `echo a | tr a-z A-Z > cikti` gibi bir satır için bu fonksiyon iki komut, bir çıkış dosyası ve arka plan bayrağı üretir:

```c
/* Satırı boru/yönlendirme/arka plan işaretlerine göre böler.
 * Dönüş: komut sayısı (>0), 0 boş satır, -1 sözdizimi hatası. */
static int ayristir(char *satir, Komut kom[], int *arka)
{
    int k = 0, a = 0;
    *arka = 0;
    memset(kom, 0, sizeof(Komut) * MAX_KOMUT);
    char *tok = strtok(satir, " \t\n");
    while (tok) {
        if (strcmp(tok, "|") == 0) {
            if (a == 0 || k + 1 >= MAX_KOMUT) return -1;
            kom[k].argv[a] = NULL;
            k++;
            a = 0;
        } else if (strcmp(tok, "<") == 0 || strcmp(tok, ">") == 0) {
            char *dosya = strtok(NULL, " \t\n");
            if (!dosya) return -1;
            if (tok[0] == '<') kom[k].giris = dosya;
            else               kom[k].cikis = dosya;
        } else if (strcmp(tok, "&") == 0) {
            *arka = 1;
        } else {
            if (a >= MAX_ARG - 1) return -1;
            kom[k].argv[a++] = tok;
        }
        tok = strtok(NULL, " \t\n");
    }
    if (a == 0)                  /* "ls |" gibi eksik komut */
        return (k == 0) ? 0 : -1;
    kom[k].argv[a] = NULL;
    return k + 1;
}
```

Üçüncü parça, ön plan çocuğunu bekleyen ve bitmiş arka plan süreçlerini toplayan yardımcılardır. İki bekleme türü farklıdır: ön plan süreci belirli bir PID için bloke olarak beklenir; arka plan süreçleri ise `WNOHANG` ile, bloke olmadan toplanır.

```c
/* Ebeveyn bir çocuğu bekler. EINTR gelirse yeniden dener. */
static void bekle(pid_t pid)
{
    int durum = 0;
    while (waitpid(pid, &durum, 0) < 0 && errno == EINTR)
        ;
    if (WIFEXITED(durum) && WEXITSTATUS(durum) != 0)
        printf("[çıkış kodu %d]\n", WEXITSTATUS(durum));
    else if (WIFSIGNALED(durum))
        printf("[sinyal %d ile sonlandı]\n", WTERMSIG(durum));
}

/* Bitmiş arka plan çocuklarını topla (zombi temizliği).
 * WNOHANG: bitmiş çocuk yoksa asla bekleme yapma. */
static void arka_plan_topla(void)
{
    int durum;
    pid_t p;
    while ((p = waitpid(-1, &durum, WNOHANG)) > 0)
        printf("[arka plan %d bitti]\n", (int)p);
}
```

Dördüncü parça kabuğun kalbidir: `calistir` her komut için bir boru ve bir çocuk oluşturur. Fonksiyonun başı, her komut için boru açıp `fork` çağırır:

```c
/* Boru hattını kur: her komut için fork. Komut i'nin
 * stdin'i önceki borudan, stdout'u sonraki boruya gelir. */
static void calistir(Komut kom[], int adet, int arka)
{
    pid_t pids[MAX_KOMUT];
    int onceki_oku = -1;

    for (int i = 0; i < adet; i++) {
        int boru[2] = {-1, -1};
        if (i < adet - 1 && pipe(boru) < 0) {
            perror("pipe");
            return;
        }
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork");
            return;
        }
```

Çocuk, `exec`'ten önce stdin ve stdout'u ayarlar. `dup2(onceki_oku, STDIN_FILENO)` satırı, bir önceki komutun çıktısını bu komutun girdisi yapar; `exec` başarısız olursa `perror` ve `_exit(127)` çalışır.

```c
        if (pid == 0) {          /* ÇOCUK: exec öncesi ayar */
            if (onceki_oku != -1) {
                dup2(onceki_oku, STDIN_FILENO);
                close(onceki_oku);
            }
            if (i < adet - 1) {
                dup2(boru[1], STDOUT_FILENO);
                close(boru[1]);
                close(boru[0]);
            }
            if (kom[i].giris) {
                int fd = open(kom[i].giris, O_RDONLY);
                if (fd < 0) { perror(kom[i].giris); _exit(127); }
                dup2(fd, STDIN_FILENO);
                close(fd);
            }
            if (kom[i].cikis) {
                int fd = open(kom[i].cikis,
                              O_WRONLY | O_CREAT | O_TRUNC, 0644);
                if (fd < 0) { perror(kom[i].cikis); _exit(127); }
                dup2(fd, STDOUT_FILENO);
                close(fd);
            }
            execvp(kom[i].argv[0], kom[i].argv);
            /* exec dönerse buraya gelinir */
            perror(kom[i].argv[0]);
            _exit(127);          /* exit değil: tamponu boşaltma */
        }
```

Ebeveyn tarafı yalnızca ihtiyaç duymadığı boru uçlarını kapatır ve bir sonraki komut için okuma ucunu saklar. Bu kapatma adımı, aşağıda göreceğimiz askıda kalma hatasının tek çaresidir.

```c
        /* EBEVEYN: artık gerekmeyen uçları kapat */
        pids[i] = pid;
        if (onceki_oku != -1) close(onceki_oku);
        if (boru[1] != -1) {
#ifndef HATA_ACIK
            close(boru[1]);
#endif
        }
        onceki_oku = boru[0];
    }
```

Tüm komutlar başlatıldıktan sonra kabuk, arka plan işaretliyse hemen döner; değilse her çocuğu tek tek bekler.

```c
    if (arka) {
        printf("[arka plan pid=%d]\n", (int)pids[adet - 1]);
        return;
    }
    for (int i = 0; i < adet; i++)
        bekle(pids[i]);
}
```

Son parça, komut satırını okuyan ana döngüdür. Döngü önce bitmiş arka plan süreçlerini toplar, sonra prompt'u yazar ve bir satır okur. `cd` ve `exit` yerleşik olarak burada ele alınır.

```c
int main(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_chld;
    /* SA_RESTART: yarım kalan sistem çağrısı devam eder */
    sa.sa_flags = SA_RESTART;
    sigaction(SIGCHLD, &sa, NULL);
```

Döngünün gövdesinde satır ayrıştırılır, yerleşikler çalıştırılır ve gerisi `calistir`'a devredilir:

```c
    char satir[512];
    Komut kom[MAX_KOMUT];
    for (;;) {
        arka_plan_topla();
        printf("msh> ");
        fflush(stdout);
        if (!fgets(satir, sizeof satir, stdin))
            break;               /* Ctrl+D */

        int arka = 0;
        int adet = ayristir(satir, kom, &arka);
        if (adet == 0) continue;
        if (adet < 0) {
            printf("sözdizimi hatası\n");
            continue;
        }
        if (strcmp(kom[0].argv[0], "exit") == 0) break;
        if (strcmp(kom[0].argv[0], "cd") == 0 && adet == 1) {
            /* cd bir yerleşik: çocukta yapılsa ebeveyn
             * dizini değişmez */
            const char *hedef = kom[0].argv[1];
            if (!hedef) hedef = getenv("HOME");
            if (chdir(hedef) < 0) perror("cd");
            continue;
        }
        calistir(kom, adet, arka);
    }
    return 0;
}
```

Derleyip çalıştıralım. Komutları bir dosyaya yazıp kabuğa girdi olarak verirsek, kabuk satırları yankılamaz; yalnızca prompt yazar:

```term
$ gcc -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L msh.c -o msh
$ printf "echo merhaba dunya | tr a-z A-Z\n" > giris.txt
$ printf "echo ucuncu > cikti.txt\nsort < cikti.txt\nfalse\n" >> giris.txt
$ printf "cat < yok_dosya\ncd /tmp\npwd\nls | | wc\nexit\n" >> giris.txt
$ ./msh < giris.txt
msh> MERHABA DUNYA
msh> msh> ucuncu
msh> [çıkış kodu 1]
msh> yok_dosya: No such file or directory
[çıkış kodu 127]
msh> msh> /tmp
msh> sözdizimi hatası
msh> 
```

Çıktıyı okurken önemli bir ayrıntıya dikkat et: prompt `msh> ` her komuttan önce yazılır ve yeni satır basmaz, komutun çıktısı da prompt'un yanına düşer. Girdi bir dosyadan geldiği için komut yankılanmaz. Bu yüzden `msh> msh> ucuncu` satırı iki prompt'un birleşmesidir: ilk prompt `echo ucuncu > cikti.txt` satırına, ikincisi `sort < cikti.txt` satırına aittir ve `ucuncu`, `sort`'un çıktısıdır. `yok_dosya` hatası çocuk sürecin `stderr`'ine yazılır; `perror` mesajı bu yüzden doğrudan ekrana düşer. Çocuk `_exit(127)` ile çıktığında kabuk bunu `[çıkış kodu 127]` olarak bildirir. `cd /tmp` komutundan sonra `pwd`'nin `/tmp` yazması, `cd`'nin gerçekten kabuğun içinde çalıştığını gösterir.

### SIGCHLD ve arka plan zombisinin ömrü

Arka plan komutu (`sleep 1 &`) bittiğinde çocuk zombi olur ve kabuk bunu yalnızca bir sonraki prompt'ta toplar. Bunu gözlemlemek için kabuğu bir FIFO'dan besleriz: kabuk `fgets` ile girdi beklerken arka plan çocuğu bitmiş ama toplanmamış olur. Komutların çalıştırılış sırası aşağıdaki gibidir:

```term
$ mkfifo ff
$ (./msh < ff > zomb.out &)
$ exec 4>ff && echo "sleep 1 &" >&4
$ sleep 3; ps -eo pid,ppid,stat,comm | grep -E "sleep|msh"
  53969   52999 S+   msh
  53971   53969 Z+   sleep
$ echo "" >&4
$ cat zomb.out
msh> [arka plan pid=53971]
msh> [arka plan 53971 bitti]
```

`ps` çıktısında `sleep` süreci `Z` durumundadır ve ebeveyni `msh`'dir. Boş bir satır göndermek kabuğu bir sonraki prompt'a getirir; döngünün başındaki `arka_plan_topla` zombiyi toplar ve `[arka plan 53971 bitti]` mesajını basar.

`SIGCHLD` işleyicisinin yalnızca bir bayrak kaldırdığına dikkat et; zombiyi işleyicinin içinde toplamıyoruz. Bunun iki nedeni var. Birincisi, işleyici ön plan çocuğunu da yakalayabilir: ön plan için `waitpid(pid, ...)` bekleyen kod, çocuğu işleyici zaten toplamışsa `ECHILD` hatası alır ve yanlış bir sonuç yorumlar. İkincisi, işleyicide yalnızca **async-signal-safe** işlemler güvenlidir; bu kavramı aşağıda sinyaller bölümünde açıklayacağız.

### Kapatılmayan uçlar: askıda kalma

Boru hattında her ebeveyn kopyasını kapatmalıdır. Bunun nedeni, bir borunun okuma tarafının **dosya sonu (EOF)** görebilmesi için yazma ucunun **her** kopyasının kapatılmış olmasıdır. Kabuğumuzun bu adımı atlayan sürümü, `HATA_ACIK` tanımıyla derlenir. Böyle bir kabuğa `echo a | sort` satırı verildiğinde süreçler şöyle görünür:

```term
$ gcc -O2 -Wall -Wextra -std=c11 -DHATA_ACIK msh.c -o msh_hata
  53935   52999 S+   msh_hata
  53938   53935 S+   sort
```

Her iki süreç de `S` (uyku) durumundadır: `sort` EOF bekliyor, kabuk ise `sort`'un bitmesini bekliyor. EOF hiç gelmez, çünkü yazma ucu hâlâ ebeveynde açık. Bu tür kilitlenme, boru yazmanın en sık yapılan hatasıdır ve hata ayıklaması zordur. Kural basittir: `dup2`'den sonra kullanılmayan her boru ucunu, her süreçte kapat.

## 26.5 Süreçler arası iletişim (IPC)

Süreçler kendi bellek alanlarına sahiptir; birbirlerinin değişkenlerini doğrudan göremezler. Bu izolasyon güvenlik ve kararlılık için değerlidir, ama süreçlerin veri alışverişi yapması da gerekir. İşletim sistemi bunun için birkaç mekanizma sunar: borular, adlandırılmış borular (FIFO), paylaşılan bellek, sinyaller ve soketler. Her birinin maliyeti ve kullanım alanı farklıdır.

### Boru (pipe) ve dup2

`pipe()` çağrısı iki dosya tanımlayıcısı döndürür: `boru[0]` okuma ucu, `boru[1]` yazma ucu. Yazılan veri çekirdekte bir tamponda tutulur ve okuma ucundan aynı sırayla çıkar. Linux'ta bu tampon varsayılan olarak 64 KiB'dir (genel bilgi); tampon dolduğunda yazan süreç bloke olur.

Bir programın `stdout`'unu diğerinin `stdin`'ine bağlamak için `dup2(eski, yeni)` kullanılır: `yeni` dosya tanımlayıcısı artık `eski`'nin gösterdiği yeri gösterir. Şekil 26.5, `grep` çocuğunun dosya tanımlayıcı tablosunu `dup2` öncesi ve sonrası gösteriyor.

![Şekil 26.5: dup2 öncesi ve sonrası dosya tanımlayıcı tablosu. grep'in stdin'i p1'in okuma ucuna, stdout'u p2'nin yazma ucuna bağlanır; fazla uçlar kapatılır.](gorseller/b26_boru_fd.png)

Önce en sade örneği çalıştıralım: bir ebeveyn sayıları boruya yazar, çocuk okuyup toplar. Bu örnekte boru EOF'un nasıl çalıştığını görürsün: ebeveyn yazma ucunu kapatınca çocuğun `read` çağrısı `0` döndürür ve döngü biter.

```c
/* uretici_tuketici.c: ebeveyn 1..10 sayılarını bir boruya
 * yazar, çocuk okuyup toplar. Boru EOF'u, yazma ucu
 * kapanınca gelir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int boru[2];
    if (pipe(boru) < 0) {
        perror("pipe");
        return 1;
    }
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
```

```c
    if (pid == 0) {                  /* TÜKETİCİ */
        close(boru[1]);     /* yazma ucu bu süreçte gereksiz */
        int x, toplam = 0;
        while (read(boru[0], &x, sizeof x)
               == (ssize_t)sizeof x) {
            printf("aldı: %d\n", x);
            toplam += x;
        }                   /* read 0 dönünce EOF */
        printf("toplam=%d\n", toplam);
        close(boru[0]);
        return 0;
    }

    close(boru[0]);         /* okuma ucu bu süreçte gereksiz */
    for (int i = 1; i <= 10; i++) {
        if (write(boru[1], &i, sizeof i)
            != (ssize_t)sizeof i) {
            perror("write");
            break;
        }
    }
    close(boru[1]);         /* EOF'u tetikler */
    waitpid(pid, NULL, 0);
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 uretici_tuketici.c -o uretici_tuketici
$ ./uretici_tuketici
aldı: 1
aldı: 2
aldı: 3
aldı: 4
aldı: 5
aldı: 6
aldı: 7
aldı: 8
aldı: 9
aldı: 10
toplam=55
```

Şimdi `cat | grep | wc` boru hattını C'de kuralım. Her komut kendi çocuk sürecinde çalışır ve iki boru bu üç süreci birbirine bağlar. Kod, kabuğun yaptığı işin açık hâlidir:

```c
/* boru3.c: cat /etc/passwd | grep -E "^root" | wc -l
 * Süreç 1: cat   stdout -> p1 yazma
 * Süreç 2: grep  stdin <- p1 okuma, stdout -> p2 yazma
 * Süreç 3: wc    stdin <- p2 okuma
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L boru3.c
 * -DHATA_ACIK: ebeveyn boruların uçlarını kapatmaz. */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int p1[2], p2[2];
    if (pipe(p1) < 0 || pipe(p2) < 0) {
        perror("pipe");
        return 1;
    }

    pid_t c1 = fork();
    if (c1 == 0) {                   /* cat */
        dup2(p1[1], STDOUT_FILENO);
        close(p1[0]); close(p1[1]);
        close(p2[0]); close(p2[1]);
        execlp("cat", "cat", "/etc/passwd", (char *)NULL);
        _exit(127);
    }
```

Ortadaki `grep` ve sondaki `wc` süreçleri de aynı kalıpla kurulur: her biri kendi girdisini ve çıktısını dup2 ile ayarlar, sonra tüm boru uçlarını kapatır ve `exec` eder. Son bölüm, ebeveynin kendi boru uçlarını kapattığı ve üç çocuğu beklediği yerdir.

```c
    pid_t c2 = fork();
    if (c2 == 0) {                   /* grep */
        dup2(p1[0], STDIN_FILENO);
        dup2(p2[1], STDOUT_FILENO);
        close(p1[0]); close(p1[1]);
        close(p2[0]); close(p2[1]);
        execlp("grep", "grep", "-E", "^root", (char *)NULL);
        _exit(127);
    }

    pid_t c3 = fork();
    if (c3 == 0) {                   /* wc */
        dup2(p2[0], STDIN_FILENO);
        close(p1[0]); close(p1[1]);
        close(p2[0]); close(p2[1]);
        execlp("wc", "wc", "-l", (char *)NULL);
        _exit(127);
    }

#ifndef HATA_ACIK
    /* ebeveyn kopyaları da kapatır */
    close(p1[0]); close(p1[1]);
    close(p2[0]); close(p2[1]);
#endif
    waitpid(c1, NULL, 0);
    waitpid(c2, NULL, 0);
    waitpid(c3, NULL, 0);
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 boru3.c -o boru3
$ ./boru3
1
```

Çıktı `1`dir: `/etc/passwd` içinde `^root` ile başlayan tek satır vardır. Bu programın ayrıntılı izini Çözümlü Örnek 4'te süreceğiz.

### Adlandırılmış boru (FIFO)

Pipe yalnızca ilişkili süreçler arasında çalışır: `pipe()` ile oluşturulmuş uçları miras alabilen süreçler gibi. Birbirinden bağımsız iki programın iletişim kurması için **adlandırılmış boru (FIFO)** kullanılır. FIFO, dosya sisteminde özel bir dosya olarak görünür ve `mkfifo` ile oluşturulur; veri diske yazılmaz, bellekte akar.

```term
$ mkfifo /tmp/borum
$ echo merhaba > /tmp/borum &
$ cat /tmp/borum
merhaba
$ ls -l /tmp/borum | cut -c1
p
```

`ls -l` çıktısındaki baştaki `p` harfi, dosyanın bir FIFO olduğunu gösterir. Bu bölümde FIFO'yu kabuğumuzu bekletmek için de kullandık: bir FIFO'ya yazan süreç, okuyan taraf gelene kadar bloke olur.

### Paylaşılan bellek

Paylaşılan bellek, iki sürecin aynı fiziksel sayfayı kendi sanal adres uzaylarına eşlemesidir. Veri kopyalanmaz, bu yüzden büyük veri için en hızlı IPC yöntemidir. Ama senkronizasyonu tamamen sana bırakır: iki süreç aynı anda yazarsa yarış koşulu oluşur (Bölüm 27). POSIX API'si üç adım kullanır: `shm_open` ile adlı bir bellek nesnesi açılır, `ftruncate` ile boyutu ayarlanır ve `mmap` ile adres uzayına eşlenir. Aşağıdaki program bu üç adımı ve çocuk–ebeveyn paylaşımını gösterir.

```c
/* shm_demo.c: POSIX paylaşılan bellek. Çocuk yazar, ebeveyn okur.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -D_DEFAULT_SOURCE */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define AD "/b26_demo"
#define BOY 4096

int main(void)
{
    int fd = shm_open(AD, O_CREAT | O_RDWR, 0600);
    if (fd < 0) { perror("shm_open"); return 1; }
    if (ftruncate(fd, BOY) < 0) { perror("ftruncate"); return 1; }

    char *p = mmap(NULL, BOY, PROT_READ | PROT_WRITE,
                   MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    pid_t pid = fork();     /* çocuk aynı fiziksel sayfayı görür */
    if (pid == 0) {
        strcpy(p, "çocuk yazdı");
        _exit(0);
    }
    waitpid(pid, NULL, 0);
    printf("ebeveyn okudu: \"%s\"\n", p);

    munmap(p, BOY);
    close(fd);
    shm_unlink(AD);         /* ad sistemden kaldırılır */
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 -D_DEFAULT_SOURCE shm_demo.c -o shm_demo
$ ./shm_demo
ebeveyn okudu: "çocuk yazdı"
```

Çocuk, `fork` ile miras aldığı eşlemeyi kullanır ve yazdığı metin ebeveyne ulaşır. `shm_unlink` çağrısı adı sistemden kaldırır; mevcut eşlemeler ise hepsi kapanana kadar bellekte kalır. Kontrol için `/dev/shm` dizini bu adlı nesneleri gösterir.

### Sinyaller

Sinyal, çekirdeğin bir sürece gönderdiği kısa bir bildirimdir: `SIGINT` (Ctrl+C), `SIGTERM` (nazik sonlandırma isteği), `SIGKILL` (zorla öldürme) ve `SIGCHLD` (çocuk durum değiştirdi) bunların en bilinenleridir. Bölüm 4'te `kill` ile bunları göndermiştik. Sinyal geldiğinde süreç ya varsayılan eylemi uygular (çoğu durumda sonlanır), ya da kendi **işleyicisini (handler)** çalıştırır. İşleyici `sigaction` ile kurulur.

İki kural önemlidir. Birincisi, `SIGKILL` ve `SIGSTOP` yakalanamaz ve yok sayılamaz; çekirdek bunları her zaman uygular. İkincisi, işleyici kesintiyi programın herhangi bir yerinde, herhangi bir komutun ortasında yakalayabilir. Bu yüzden işleyicide yalnızca **async-signal-safe** işlevler çağrılmalıdır. POSIX bu işlevlerin bir listesini verir ve `write(2)` bu listededir. `printf` listede değildir: `stdio` tamponu ve kilitleri ana programla paylaşılır; işleyici, ana program bu kilide zaten sahipken çalışırsa kendi kendini bekleyebilir.

`sig.c` programı bu kuralları üç senaryoda sınar: `SIGTERM` yakalanır ve işleyici bir mesaj yazar; `SIGKILL` için `sigaction` hata verir; `SIGKILL` gönderilen süreç çıkış koduyla değil sinyal numarasıyla sonlanır.

```c
/* sig.c: SIGTERM yakalanır; SIGKILL yakalanamaz.
 * Ebeveyn iki çocuk oluşturur ve sinyalleri kendisi gönderir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 sig.c -o sig */
#define _DEFAULT_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static volatile sig_atomic_t g_dur = 0;

/* İşleyici: yalnızca bayrak kaldırır ve write(2)
 * kullanır. printf burada async-signal-safe değildir. */
static void on_term(int sig)
{
    static const char m[] = "[çocuk] SIGTERM alındı\n";
    (void)sig;
    g_dur = 1;
    ssize_t r = write(STDOUT_FILENO, m, sizeof m - 1);
    (void)r;
}

static void cocuk_bekle_term(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_term;
    sigaction(SIGTERM, &sa, NULL);
    while (!g_dur)
        pause();             /* sinyal gelene kadar uyu */
    printf("[çocuk] temiz kapanış\n");
    exit(3);
}
```

```c
int main(void)
{
    struct sigaction sa;
    int durum = 0;
    /* fork öncesi tampon kopyalanmasın */
    setvbuf(stdout, NULL, _IONBF, 0);
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_term;
    if (sigaction(SIGKILL, &sa, NULL) < 0)
        printf("SIGKILL için sigaction: %s\n", strerror(errno));

    pid_t c1 = fork();
    if (c1 == 0)
        cocuk_bekle_term();
    /* çocuğun işleyiciyi kurmasını bekle */
    usleep(200000);
    kill(c1, SIGTERM);
    waitpid(c1, &durum, 0);
    if (WIFEXITED(durum))
        printf("çocuk1 normal çıktı, kod=%d\n", WEXITSTATUS(durum));

    pid_t c2 = fork();
    if (c2 == 0) {
        pause();
        _exit(0);
    }
    usleep(200000);
    kill(c2, SIGKILL);       /* yakalanamaz: zorla öldürülür */
    waitpid(c2, &durum, 0);
    if (WIFSIGNALED(durum))
        printf("çocuk2 sinyal ile sonlandı: %d\n", WTERMSIG(durum));
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 -D_DEFAULT_SOURCE sig.c -o sig
$ ./sig
SIGKILL için sigaction: Invalid argument
[çocuk] SIGTERM alındı
[çocuk] temiz kapanış
çocuk1 normal çıktı, kod=3
çocuk2 sinyal ile sonlandı: 9
```

İşleyicide `write` kullanmamızın nedeni budur. Ana akışta ise `printf` güvenlidir, çünkü orada sinyal kesintisi ile kilit çakışması yoktur. Bu programda `setvbuf` ile tamponu da kapattık; böylece `fork` öncesinde tampona yazılmış metnin çocuklara kopyalanması engellenir.

### Soketler

Ağ üzerinden ya da aynı makinede iki süreç soketlerle konuşur. Soket de bir dosya tanımlayıcıdır; `read` ve `write` ile kullanılabilir. Bu bölümde yalnızca yerini belirtiyoruz: ağ soketleri, adresleme ve TCP/UDP ayrıntıları Bölüm 31'de; soketin dosya tanımlayıcı tarafı ve `epoll` ile olay güdümlü çoklama Bölüm 28'de işlenecek.

## 26.6 Windows farkı: fork yok, CreateProcess var

Windows'ta `fork()` yoktur. Yeni bir süreç, `CreateProcess` ile **sıfırdan** oluşturulur: çalıştırılabilir dosya adı, komut satırı ve başlatma bilgileri verilir; sistem yeni bir adres uzayı kurup programı yükler. Ebeveyn–çocuk ilişkisi, miras alınabilen tutamaçlar (handle) ve `WaitForSingleObject` ile beklenen bir nesne olarak ortaya çıkar. Yani süreç Linux'taki gibi "önce kopyala, sonra değiştir" modeliyle değil, "doğrudan yeni süreç oluştur" modeliyle kurulur.

Bu fark kabuk tasarımını da etkiler: Windows'ta boru ve yönlendirme, `CreateProcess` çağrısına verilen `STARTUPINFO` yapısıyla kurulur; Linux'taki gibi `fork` ile çocuğu ayarlayıp `exec` etmek yoktur. Bu bölümde Windows üzerinde C deneyi yapmadık; bu bilgi genel bilgidir. Farkı pratikte görmek için WSL2 kullanabilirsin: WSL içindeki süreçler gerçek bir Linux çekirdeğinde çalışır ve bu bölümün `fork` deneylerinin hepsi orada yapıldı.

## 26.7 Zamanlama: CPU'yu kime vereceksin?

CPU tek ve sınırlıyken çalışmak isteyen süreçler birbirleriyle yarışır. Zamanlayıcı (scheduler) her karar anında hangi hazır sürecin çalışacağını seçer. Bu seçim, sistemin hissedilen hızını doğrudan belirler: tarayıcının tıklamaya hemen tepki vermesi, müziğin takılmaması, bir derlemenin ne kadar sürdüğü, hepsi bu karara bağlıdır.

Bir zamanlama algoritmasını karşılaştırmak için üç ölçüt kullanılır. **Bekleme süresi**, süreç hazır olduğu halde CPU'yu beklediği toplam süredir. **Dönüş süresi**, sürecin varışından bitişine kadar geçen süredir: dönüş = bitiş − varış. **Yanıt süresi**, sürecin ilk kez CPU'ya girdiği ana kadar geçen süredir; etkileşimli programlar için en önemlisidir. Bekleme süresi, dönüş süresinden sürecin toplam CPU ihtiyacı çıkarılarak bulunur: bekleme = dönüş − süre.

Bu ölçütler birbiriyle çelişir. Kısa işleri önce yaparsan ortalama bekleme düşer, ama uzun bir iş açlıktan ölebilir. Her sürece kısa dilimler verirsen yanıt süresi iyileşir, ama her dilim değişiminde bağlam değişimi maliyeti ödenir (26.9). Bu yüzden zamanlayıcı tasarımı bir ödünleşim (trade-off) problemidir.

Altı temel algoritma vardır:

- **FCFS (First-Come, First-Served):** varış sırasına göre çalıştırır ve kesmez. En basit algoritmadır, ama uzun bir iş kısa işlerin arkasında bekler (konvoy etkisi).
- **SJF (Shortest Job First):** hazır süreçler arasından en kısa süreni seçer ve kesmez. Tüm süreçler aynı anda gelirse ortalama beklemeyi en aza indirir. Bunun kanıtı Bölüm 18.5'teki Smith kuralının özel bir durumudur: ağırlıkların hepsi 1 olduğunda oran `p/w = p` olur, yani en kısa işi önce yap.
- **SRTF (Shortest Remaining Time First):** SJF'in kesintili hâli. Yeni bir süreç geldiğinde kalan süresi mevcut sürecin kalan süresinden kısaysa CPU'yu ona verir.
- **Öncelik (priority):** en yüksek öncelikli hazır süreci seçer. Düşük öncelikli süreçler sonsuza dek bekleyebilir (açlık); yaşlandırma (aging) bunu çözer.
- **Round Robin (RR):** her hazır süreci sabit bir `q` dilimi boyunca sırayla çalıştırır, dilim dolunca kuyruğun sonuna koyar. Yanıt süresi iyidir, ama `q` küçükse bağlam değişimi sayısı artar.
- **MLFQ (çok seviyeli geri beslemeli kuyruk):** birkaç seviyeli kuyruk kullanır. Yeni süreç en üst seviyeye girer; dilimini tamamen kullanan süreç bir alt seviyeye iner; belli aralıklarla her şey en üst seviyeye yükseltilir. Amaç, uzunluğu bilinmeyen işlerde bile kısa etkileşimli işleri hızlı tutmak ve uzun işleri zamanla kısıtlamaktır.

Bu algoritmaları bir simülatörle karşılaştırmak, kâğıt üzerindeki hesabı sınar ve yanlış anlamaları ortaya çıkarır. Aşağıdaki Python programı tek CPU'lu bir simülasyondur: her tick bir CPU birimidir ve hangi sürecin o tick'te çalıştığı bir liste olarak tutulur. Böylece bekleme ve dönüş süreleri, bu tick dizisinden doğrudan hesaplanır. Program önce kitap örneğini (`P1=24`, `P2=3`, `P3=3`) çalıştırır, sonra iki klasik örneği ve rastgele bir doğrulamayı yapar.

Simülatörün ortak çerçevesi ve `SUREC` listesi, her sürecin adını, varış zamanını, süresini ve önceliğini taşır. Bu kısım dosyanın başıdır:

```python
# sched_sim.py: CPU zamanlayıcı simülatörü (birim-tick, tek CPU).
# Algoritmalar: FCFS, SJF (kesintisiz), SRTF (kesintili SJF),
# Öncelik (kesintisiz), Round Robin (q), MLFQ (3 seviye + boost).
# Her tick bir CPU birimi. Süreç: (ad, varış, süre, öncelik).
# Çalıştırma: python sched_sim.py   -> sonuçları yazar ve CSV üretir.
import csv
import itertools
import os
import random
import textwrap
from collections import deque

SUREC = [  # kitap örneği
    {"ad": "P1", "varis": 0, "sure": 24, "oncelik": 3},
    {"ad": "P2", "varis": 0, "sure": 3,  "oncelik": 1},
    {"ad": "P3", "varis": 0, "sure": 3,  "oncelik": 2},
]
```

Kesintisiz algoritmalar (FCFS, SJF ve öncelik) tek bir ortak çekirdekle yazılır. Bu çekirdek süreç bitene kadar CPU'yu bırakmaz; yalnızca bir süreç bittiğinde yeni karar verir. Hangi sürecin seçileceğini ise dışarıdan verilen `sec` fonksiyonu belirler. Bu ayrım, kodun tekrarını önler ve algoritmanın yalnızca seçim kuralına bağlı olduğunu gösterir:

```python
def kesintisiz(sur, sec):
    """Süreç bitene kadar bırakılmaz. sec: hazır -> seçilen."""
    kalan = {p["ad"]: p["sure"] for p in sur}
    bitti, tl, t, cur = set(), [], 0, None
    while len(bitti) < len(sur):
        if cur is None:
            hazir = [p for p in sur if p["ad"] not in bitti
                     and p["varis"] <= t]
            if not hazir:
                tl.append(None)
                t += 1
                continue
            cur = sec(hazir)
        tl.append(cur["ad"])
        kalan[cur["ad"]] -= 1
        t += 1
        if kalan[cur["ad"]] == 0:
            bitti.add(cur["ad"])
            cur = None
    return tl


def fcfs(sur):
    def sec(h):
        return min(h, key=lambda p: p["varis"])
    return kesintisiz(sur, sec)
```

FCFS, yukarıdaki parçada görünen tek seçim kuralıdır: en erken varanı seçer. SJF ve öncelik için yalnızca seçim anahtarı değişir: süre ya da öncelik. SRTF kesintili olduğu için kendi döngüsünü kullanır: her tick, kalan süresi en kısa olan hazır süreci seçer.

```python
def sjf(sur):
    def sec(h):
        return min(h, key=lambda p: (p["sure"], p["varis"]))
    return kesintisiz(sur, sec)


def oncelik(sur):
    def sec(h):
        return min(h, key=lambda p: (p["oncelik"], p["varis"]))
    return kesintisiz(sur, sec)


def srtf(sur):
    """Her tick en kısa kalan süreli hazır süreç çalışır."""
    kalan = {p["ad"]: p["sure"] for p in sur}
    tl, t = [], 0
    while any(v > 0 for v in kalan.values()):
        hazir = [p for p in sur
                 if p["varis"] <= t and kalan[p["ad"]] > 0]
        if not hazir:
            tl.append(None)
        else:
            sec = min(hazir,
                      key=lambda p: (kalan[p["ad"]], p["varis"]))
            tl.append(sec["ad"])
            kalan[sec["ad"]] -= 1
        t += 1
    return tl
```

Round Robin'de kuyruk önemlidir. Bir tick'te yeni varan süreçler, dilimi biten sürecin kuyruğa dönmesinden **önce** kuyruğa eklenir. Bu sıra, kuyruk disiplinini tanımlar ve kitap örneğindeki bekleme sürelerini doğrudan etkiler.

```python
def round_robin(sur, q):
    """Yeni varışlar, kesilen süreçten ÖNCE kuyruğa girer."""
    kalan = {p["ad"]: p["sure"] for p in sur}
    eklendi, kuyruk, tl = set(), deque(), []
    t, cur, dilim = 0, None, 0
    while any(v > 0 for v in kalan.values()):
        for p in sur:
            if p["varis"] == t and p["ad"] not in eklendi:
                kuyruk.append(p["ad"])
                eklendi.add(p["ad"])
        if cur is not None and (dilim == q or kalan[cur] == 0):
            if kalan[cur] > 0:
                kuyruk.append(cur)
            cur = None
        if cur is None:
            if not kuyruk:
                tl.append(None)
                t += 1
                continue
            cur, dilim = kuyruk.popleft(), 0
        tl.append(cur)
        kalan[cur] -= 1
        dilim += 1
        t += 1
    return tl
```

MLFQ'da üç kural uygulanır. Yeni süreç en üst seviyeye girer. Her 20 tick'te (`boost`) bütün süreçler en üst seviyeye çıkarılır; böylece alt seviyedeki bir süreç sonsuza dek bekleyemez. Aşağıdaki ilk parça, kuyrukların kurulmasını ve bu yükseltmeyi içerir.

```python
def mlfq(sur, kuantum=(2, 4, 8), boost=20):
    """Çok seviyeli geri beslemeli kuyruk. Tam dilim kullanan süreç
    bir alt seviyeye iner; her 'boost' tick'te hepsi en üste çıkar."""
    n = len(kuantum)
    kuy = [deque() for _ in range(n)]
    kalan = {p["ad"]: p["sure"] for p in sur}
    seviye, eklendi, tl = {}, set(), []
    t, cur, dilim = 0, None, 0
    while any(v > 0 for v in kalan.values()):
        for p in sur:
            if p["varis"] == t and p["ad"] not in eklendi:
                kuy[0].append(p["ad"])
                seviye[p["ad"]] = 0
                eklendi.add(p["ad"])
        if t > 0 and t % boost == 0:
            for k in range(1, n):
                while kuy[k]:
                    ad = kuy[k].popleft()
                    seviye[ad] = 0
                    kuy[0].append(ad)
```

Sonraki parça kesme ve indirme kurallarını uygular. Üst seviyede hazır bir süreç varsa çalışan süreç kesilir; dilimini tamamen kullanan süreç bir alt seviyeye iner. Bu üç kuralın birlikte nasıl çalıştığını Şekil 26.7'de göreceksin.

```python
        if cur is not None:
            L = seviye[cur]
            if kalan[cur] == 0:
                cur = None
            elif any(kuy[k] for k in range(L)):   # üst seviye hazır
                kuy[L].append(cur)
                cur = None
            elif dilim == kuantum[L]:             # dilim doldu: indir
                seviye[cur] = min(L + 1, n - 1)
                kuy[seviye[cur]].append(cur)
                cur = None
        if cur is None:
            for k in range(n):
                if kuy[k]:
                    cur, dilim = kuy[k].popleft(), 0
                    break
        if cur is None:
            tl.append(None)
            t += 1
            continue
        tl.append(cur)
        kalan[cur] -= 1
        dilim += 1
        t += 1
    return tl
```

`olc` tick dizisinden bekleme, dönüş ve yanıt sürelerini hesaplar. Bir sürecin bitiş anı, tick dizisindeki son görülme konumudur; ilk görülme ise yanıt süresini verir.

```python
def olc(sur, tl):
    """Tick dizisinden bekleme, dönüş ve yanıt sürelerini hesaplar."""
    sonuc = {}
    for p in sur:
        idx = [i for i, a in enumerate(tl) if a == p["ad"]]
        bit = idx[-1] + 1
        ilk = idx[0]
        donus = bit - p["varis"]
        sonuc[p["ad"]] = {"bitis": bit, "donus": donus,
                          "bekleme": donus - p["sure"],
                          "yanit": ilk - p["varis"]}
    n = len(sur)
    sonuc["ORT_BEKLEME"] = sum(sonuc[p["ad"]]["bekleme"]
                               for p in sur) / n
    return sonuc
```

`gantt_satirlari` ardışık tick'leri tek parça hâline getirir. Bu parçalar Gantt şemasının kutularıdır; metin çıktısının yanı sıra Şekil 26.6 ve 26.7'nin de verisidir.

```python
def gantt_satirlari(tl):
    """Ardışık aynı tick'leri tek parça (ad, baş, son) yapar."""
    parca, bas = [], 0
    for i in range(1, len(tl) + 1):
        if i == len(tl) or tl[i] != tl[bas]:
            parca.append((tl[bas] or "-", bas, i))
            bas = i
    return parca
```

Çıktı biçimlendirme fonksiyonu, uzun Gantt satırlarını 66 karakterde kaydırır. Böylece çizgi terminal genişliğini aşmadan okunabilir kalır.

```python
def ozet_yaz(ad, tl, sur):
    o = olc(sur, tl)
    metin = "  ".join(
        "%s[%d-%d)" % (x, b, s) for x, b, s in gantt_satirlari(tl))
    satirlar = textwrap.wrap(metin, width=66)
    print("%-8s" % ad, satirlar[0])
    for devam in satirlar[1:]:
        print(" " * 8, devam)
    print("         bekleme: " + ", ".join(
        "%s=%d" % (p["ad"], o[p["ad"]]["bekleme"]) for p in sur),
        " ORT=%.2f" % o["ORT_BEKLEME"])
    return o
```

`brute_force_sjf` ile SJF'in doğruluğunu sınarız: tüm süreç sıralarını (permütasyonlar) deneyip en küçük ortalama beklemeyi buluruz. Bu, Bölüm 18'deki kaba kuvvet doğrulamasının aynısıdır.

```python
def brute_force_sjf(sur):
    """Tüm sıralı planlarda en iyi ortalama bekleme (varış=0)."""
    en_iyi = None
    for sira in itertools.permutations(sur):
        t, top = 0, 0
        for p in sira:
            top += t
            t += p["sure"]
        if en_iyi is None or top < en_iyi:
            en_iyi = top
    return en_iyi / len(sur)
```

Ana fonksiyon önce kitap örneğini çalıştırır: üç algoritmanın Gantt çizgisini ve bekleme sürelerini yazdırır.

```python
def main():
    print("== Kitap örneği: P1=24, P2=3, P3=3 (hepsi t=0) ==")
    ornek = {
        "FCFS": fcfs(SUREC),
        "SJF": sjf(SUREC),
        "RR q=4": round_robin(SUREC, 4),
    }
    for ad, tl in ornek.items():
        ozet_yaz(ad, tl, SUREC)
```

Ardından klasik örnek A gelir: SJF ve SRTF aynı süreç kümesinde karşılaştırılır. Son satırlarda rastgele doğrulama için tohumlu bir üreteç oluşturulur.

```python
    print("\n== Klasik örnek A: kesintisiz SJF (Silberschatz) ==")
    A = [{"ad": "P1", "varis": 0, "sure": 8, "oncelik": 1},
         {"ad": "P2", "varis": 1, "sure": 4, "oncelik": 1},
         {"ad": "P3", "varis": 2, "sure": 9, "oncelik": 1},
         {"ad": "P4", "varis": 3, "sure": 5, "oncelik": 1}]
    ozet_yaz("SJF", sjf(A), A)
    ozet_yaz("SRTF", srtf(A), A)

    rnd = random.Random(26)
```

Rastgele doğrulamada `random.Random(26)` tohumu kullanılır; böylece her çalıştırmada aynı 500 örnek üretilir. Her örnekte `n` 2 ile 6 arasında, her sürecin süresi 1 ile 12 arasındadır. SJF'in ortalama beklemesi brute-force optimumla karşılaştırılır ve farklı çıkan örnekler sayılır.

```python
    print("\n== 500 rastgele örnek: SJF = brute-force optimum ==")
    hata = 0
    for _ in range(500):
        n = rnd.randint(2, 6)
        s = [{"ad": "P%d" % i, "varis": 0,
              "sure": rnd.randint(1, 12), "oncelik": 1}
             for i in range(n)]
        if abs(olc(s, sjf(s))["ORT_BEKLEME"]
               - brute_force_sjf(s)) > 1e-9:
            hata += 1
    print("SJF farkı (hata sayısı):", hata)
```

Altı süreçlik ikinci iş yükü, yedi algoritmayı aynı girdiyle karşılaştırmak için kullanılır. `F` en geç varan iş olduğu için ve `E` `t=9`'da geldiği için, MLFQ'nun boost ve kesme davranışı bu iş yükünde görünür hâle gelir.

```python
    print("\n== Altılı süreç: 7 algoritma, aynı iş yükü ==")
    S6 = [{"ad": "A", "varis": 0, "sure": 5, "oncelik": 2},
          {"ad": "B", "varis": 1, "sure": 3, "oncelik": 1},
          {"ad": "C", "varis": 2, "sure": 8, "oncelik": 3},
          {"ad": "D", "varis": 3, "sure": 2, "oncelik": 2},
          {"ad": "E", "varis": 9, "sure": 4, "oncelik": 1},
          {"ad": "F", "varis": 10, "sure": 6, "oncelik": 3}]
    tablo = [("FCFS", fcfs(S6)), ("SJF", sjf(S6)), ("SRTF", srtf(S6)),
             ("Öncelik", oncelik(S6)), ("RR q=2", round_robin(S6, 2)),
             ("RR q=4", round_robin(S6, 4)),
             ("MLFQ", mlfq(S6))]
```

Her algoritmanın sonuçları, bekleme, dönüş ve yanıt değerleriyle birlikte bir satır listesinde toplanır. Bu liste sonunda CSV'ye yazılacak.

```python
    satirlar = []
    for ad, tl in tablo:
        o = ozet_yaz(ad, tl, S6)
        for p in S6:
            satirlar.append({"algoritma": ad, "surec": p["ad"],
                             "varis": p["varis"], "sure": p["sure"],
                             "bekleme": o[p["ad"]]["bekleme"],
                             "donus": o[p["ad"]]["donus"],
                             "yanit": o[p["ad"]]["yanit"]})
```

Son kısım, sonuçları iki CSV dosyasına yazar: biri süreç bazlı ölçümler, diğeri Gantt parçaları için. Bu dosyalar, bölümdeki şekillerin tek veri kaynağıdır.

```python
    veri = r"D:\Mevcut Projeler\Kitap\engine\veri"
    os.makedirs(veri, exist_ok=True)
    yol = os.path.join(veri, "b26_zamanlama.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)

    # Gantt verisi (şekil için): örnek, algoritma, süreç, baş, son
    gantt = []
    gruplar = [("kitap", ornek), ("altili", dict(tablo))]
    for ornek_ad, algo_tl in gruplar:
        for algo, tl in algo_tl.items():
            for ad, bas, son in gantt_satirlari(tl):
                if ad != "-":
                    gantt.append({"ornek": ornek_ad,
                                  "algoritma": algo,
                                  "surec": ad, "bas": bas,
                                  "son": son})
    gyol = os.path.join(veri, "b26_gantt.csv")
    with open(gyol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gantt[0].keys()))
        w.writeheader()
        w.writerows(gantt)
    print("\nCSV:", yol)
    print("Gantt CSV:", gyol)


if __name__ == "__main__":
    main()
```

Programı çalıştırdığında aşağıdaki çıktıyı alırsın. Her Gantt parçası `algoritma[başlangıç-bitiş)` biçimindedir: köşeli parantezin sol ucu dahil, sağ ucu hariçtir.

```term
$ python sched_sim.py
== Kitap örneği: P1=24, P2=3, P3=3 (hepsi t=0) ==
FCFS     P1[0-24)  P2[24-27)  P3[27-30)
         bekleme: P1=0, P2=24, P3=27  ORT=17.00
SJF      P2[0-3)  P3[3-6)  P1[6-30)
         bekleme: P1=6, P2=0, P3=3  ORT=3.00
RR q=4   P1[0-4)  P2[4-7)  P3[7-10)  P1[10-30)
         bekleme: P1=6, P2=4, P3=7  ORT=5.67

== Klasik örnek A: kesintisiz SJF (Silberschatz) ==
SJF      P1[0-8)  P2[8-12)  P4[12-17)  P3[17-26)
         bekleme: P1=0, P2=7, P3=15, P4=9  ORT=7.75
SRTF     P1[0-1)  P2[1-5)  P4[5-10)  P1[10-17)  P3[17-26)
         bekleme: P1=9, P2=0, P3=15, P4=2  ORT=6.50

== 500 rastgele örnek: SJF = brute-force optimum ==
SJF farkı (hata sayısı): 0

== Altılı süreç: 7 algoritma, aynı iş yükü ==
FCFS     A[0-5)  B[5-8)  C[8-16)  D[16-18)  E[18-22)  F[22-28)
         bekleme: A=0, B=4, C=6, D=13, E=9, F=12  ORT=7.33
SJF      A[0-5)  D[5-7)  B[7-10)  E[10-14)  F[14-20)  C[20-28)
         bekleme: A=0, B=6, C=18, D=2, E=1, F=4  ORT=5.17
SRTF     A[0-1)  B[1-4)  D[4-6)  A[6-10)  E[10-14)  F[14-20)  C[20-28)
         bekleme: A=5, B=0, C=18, D=1, E=1, F=4  ORT=4.83
Öncelik  A[0-5)  B[5-8)  D[8-10)  E[10-14)  C[14-22)  F[22-28)
         bekleme: A=0, B=4, C=12, D=5, E=1, F=12  ORT=5.67
RR q=2   A[0-2)  B[2-4)  C[4-6)  A[6-8)  D[8-10)  B[10-11)  C[11-13)
         A[13-14)  E[14-16)  F[16-18)  C[18-20)  E[20-22)  F[22-24)
         C[24-26)  F[26-28)
         bekleme: A=9, B=7, C=16, D=5, E=9, F=12  ORT=9.67
RR q=4   A[0-4)  B[4-7)  C[7-11)  D[11-13)  A[13-14)  E[14-18)  F[18-22)
         C[22-26)  F[26-28)
         bekleme: A=9, B=3, C=16, D=8, E=5, F=12  ORT=8.83
MLFQ     A[0-2)  B[2-4)  C[4-6)  D[6-8)  A[8-9)  E[9-11)  F[11-13)
         B[13-14)  C[14-18)  A[18-20)  E[20-22)  F[22-24)  C[24-26)
         F[26-28)
         bekleme: A=15, B=10, C=16, D=3, E=9, F=12  ORT=10.83

CSV: D:\Mevcut Projeler\Kitap\engine\veri\b26_zamanlama.csv
Gantt CSV: D:\Mevcut Projeler\Kitap\engine\veri\b26_gantt.csv
```

Çıktının üst kısmı, kitap örneğindeki ortalama beklemeleri doğrular: FCFS için `(0 + 24 + 27) / 3 = 17`, SJF için `(6 + 0 + 3) / 3 = 3`, RR (`q=4`) için `(6 + 4 + 7) / 3 = 5,67`. Bu üç değeri el ile de hesaplayabilirsin; simülatörün ilk sınaması budur. Klasik örnekte süreçler farklı zamanlarda gelir ve SRTF'nin kesintisiz SJF'ten daha iyi sonuç verdiği görülür: `6,50` ve `7,75`. Bu iki sayı ders kitaplarında da yer alır; simülatör bunları tutturuyor.

Şekil 26.6, kitap örneğindeki üç algoritmanın Gantt şemasını yan yana gösteriyor. FCFS'te uzun `P1` kısa süreçleri bekletir; SJF'te kısa süreçler önce biter, `P1` en sona kalır; RR'de ise her süreç dilim dilim ilerler ve bekleme dağılır.

![Şekil 26.6: Kitap örneği için FCFS, SJF ve RR (q=4) Gantt şemaları. Sağdaki sayılar ortalama bekleme süreleridir.](gorseller/b26_gantt_kitap.png)

Altı süreçlik iş yükünde RR (q=2) ve MLFQ'yu karşılaştıran Şekil 26.7 farkı daha açık gösterir: MLFQ, uzun `C` işini alt seviyelere iterken kısa ve etkileşimli `D` ile `E` süreçlerini üst seviyede tutar. Ortalama bekleme değeri tek başına MLFQ'yu en iyi yapmaz; bu, ölçütlerin çelişmesinin bir örneğidir.

![Şekil 26.7: Altılı iş yükünde RR (q=2) ve MLFQ Gantt şemaları. MLFQ kısa işleri üst seviyede tutar; ortalama beklemenin tamamen iyileşmediğine dikkat et.](gorseller/b26_gantt_altili.png)

Rastgele 500 örnekte SJF'in ortalama beklemesi, tüm sıralı planların en küçüğüne eşit çıktı; hata sayısı 0'dır. SJF'in optimalliği bu nedenle yalnızca birkaç el örneğine değil, rastgele bir örnek kümesinde kaba kuvvetle doğrulanmış bir sonuçtur.

Bu simülatör bilerek basit tutuldu: tek CPU, bağlam değişimi maliyeti yok, G/Ç yok. Gerçek bir zamanlayıcı bu varsayımların hepsini bozar. Yine de temel kararlar (kısa işi önceleme, dilim seçimi ve kuyruk disiplini) gerçek sistemde ne yaptığını anlamak için yeterlidir.

## 26.8 Linux zamanlayıcısı: CFS'ten EEVDF'e

Linux'un sıradan (SCHED_NORMAL) süreçleri için kullandığı zamanlayıcı, 2007'de Linux 2.6.23 ile tanıtılan **CFS (Completely Fair Scheduler)** idi (genel bilgi). CFS'in fikri sade ve güzeldir: her sürece adil bir CPU payı vermek. Bunu her süreç için bir **sanal çalışma süresi (vruntime)** tutarak yapar. Bir süreç CPU'da çalıştıkça vruntime'ı artar; zamanlayıcı her zaman en düşük vruntime'a sahip süreci seçer. Böylece uzun süredir az CPU alan süreç öne geçer. Süreçlerin önceliği, `nice` değeriyle vruntime'ın artış hızını değiştirerek ayarlanır.

Kaynak kodda bu mekanizma hâlâ görünür. Linux v6.6 `kernel/sched/fair.c` dosyasında `update_curr` fonksiyonu, çalışan sürecin vruntime'ını artıran satırı içerir (satır 1176):

```c
curr->vruntime += calc_delta_fair(delta_exec, curr);
```

Burada `delta_exec` son güncellemeden bu yana geçen gerçek çalışma süresidir ve `calc_delta_fair` bunu sürecin ağırlığına göre ölçekler. Yani aynı süre, yüksek ağırlıklı (düşük nice) süreç için vruntime'ı daha az artırır; bu süreç daha sık seçilir.

Aynı dosyanın başlığında hâlâ "Completely Fair Scheduling (CFS) Class" yazar. Ama v6.6'da seçim mantığı değişmiştir: dosyada `Earliest Eligible Virtual Deadline First` (EEVDF) açıklaması vardır ve `pick_eevdf` fonksiyonu (satır 969) bir sonraki süreci seçer. EEVDF iki ölçüte bakar: süreç **uygun (eligible)** olmalıdır, yani kendisine borçlu olunan hizmeti almış olmalı; uygun süreçler arasından ise **en erken sanal son teslimi (virtual deadline)** olan seçilir. Bu, Bölüm 18'deki EDF (en erken son teslim) fikrinin sanal zamanda uygulanmasıdır. Yorumun tam metni Kod Okuma bölümünde yer alıyor.

Pratikte bir süreç zamanlayıcıyı `nice` ve gerçek zamanlı sınıflarla etkiler. `nice` değeri normal süreçlerin CPU payını ayarlar; değer `-20` (en öncelikli) ile `19` (en düşük) arasındadır (genel bilgi). WSL'de `nice` ile başlatılan bir komut ve `ps` çıktısı şöyledir:

```term
$ nice -n 5 sleep 0 && echo nice_ok
nice_ok
$ ps -o pid,ni,cls,rtprio,comm -p $$
    PID  NI CLS RTPRIO COMMAND
  27452   0  TS      - bash
```

`NI` sütunu nice değerini, `CLS` sütunu zamanlayıcı sınıfını gösterir. `TS` (time-sharing) normal süreçtir. Kabuğun kendisi `nice 0` ile çalışıyor; `nice -n 5` yalnızca yeni başlatılan `sleep` sürecini etkiler.

Gerçek zamanlı sınıflar ise başka bir mantıkla çalışır. `SCHED_FIFO` ve `SCHED_RR` sınıfındaki süreçler normal süreçlerden her zaman önce gelir: hazır bir gerçek zamanlı süreç varken normal süreçler CPU'yu alamaz. Önceliği 1 ile 99 arasındadır. `chrt` komutu bu sınıfları ayarlar. Denememizde sıradan bir kullanıcı olarak çalışıyorduk ve sonuç şöyleydi:

```term
$ chrt -m
SCHED_OTHER min/max priority	: 0/0
SCHED_FIFO min/max priority	: 1/99
SCHED_RR min/max priority	: 1/99
$ chrt -f -p 10 $$
chrt: failed to set pid 27452's policy: Operation not permitted
```

Gerçek zamanlı bir sınıfa geçmek, süreci CPU'nun tekelindeki bir öncelikle donatmak demektir; bu yüzden çekirdek bunu yalnızca yetkili süreçlere (CAP_SYS_NICE yeteneği olan ya da root) izin verir. Savunma ve gömülü sistemlerde bu sınıflar önemlidir: bir uçuş kontrol döngüsünün her 10 milisaniyede bir çalışması gerekiyorsa, onu normal süreçlerle paylaştırmak gecikme garantisini bozar. Bu konu Bölüm 44'te kesmeler ve zamanlayıcı kesmesiyle yeniden ele alınacak.

## 26.9 Bağlam değişimi ve sistem çağrısı maliyeti

Zamanlayıcı bir süreci bırakıp diğerini çalıştırdığında **bağlam değişimi (context switch)** olur. Çekirdek çalışan sürecin yazmaçlarını PCB'ye kaydeder, hedef sürecin yazmaçlarını yükler ve süreçler farklı adres uzaylarındaysa sayfa tablosu kökünü (x86-64'te CR3) değiştirir. MertOS'taki `switchContext` tam olarak bunu yapar: callee-saved yazmaçları ve RSP'yi kaydedip yükler, CR3'ü ise yalnızca farklıysa değiştirir (`kernel/process/context_switch.asm`).

Bu işlemin maliyeti üç kaynaktan gelir. Birincisi, yazmaç kayıtlarının kendisi; bu nispeten küçük bir sabittir. İkincisi, adres uzayı değişimi: CR3 değişince TLB (çeviri önbelleği) geçersizleşebilir ve yeni sürecin sayfalarına erişim ilk seferde yavaşlar (Bölüm 25). Üçüncüsü ve belki en önemlisi, önbellek soğumasıdır: yeni süreç, eski sürecin işine yaramayan verileri önbellekte bulur ve kendi verilerini bellekten yeniden getirmek zorunda kalır. Bu son etki, ölçümde görünen süreden çok daha büyük olabilir.

Maliyeti ölçmek için üç deney tasarladık. İlki bir sistem çağrısının (`getppid`) süresi: çekirdeğe gidip dönmenin maliyeti. İkincisi, iki süreç arasında bir boru üzerinden **ping-pong**: her tur iki yazma, iki okuma ve dolayısıyla iki bağlam değişimi içerir. Üçüncüsü, aynı ping-pong'un iki iş parçacığıyla yapılması ve süreç/iş parçacığı oluşturma süreleridir. Ölçümde iki tarafı da CPU 0'a sabitledik (`sched_setaffinity`); böylece her geçiş gerçekten bir bağlam değişimi olur.

Ölçüm programı aşağıdadır. Önce zaman ölçümü ve CPU sabitleme yardımcıları gelir.

```c
/* ctx_olcum.c: sistem çağrısı, bağlam değişimi (boru ping-pong)
 * ve süreç/iş parçacığı oluşturma maliyetini ölçer. Çıktı CSV'dir.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread
 * Kullanım: ./ctx_olcum [tekrar]  (varsayılan 5) */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define N_PINGPONG 100000L
#define N_SYSCALL  2000000L
#define N_OLUSTUR  2000L

static double simdi_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

/* Bu çağrıyı yapan iş parçacığını CPU 0'a sabitler. */
static void tek_cpu(void)
{
    cpu_set_t c;
    CPU_ZERO(&c);
    CPU_SET(0, &c);
    sched_setaffinity(0, sizeof c, &c);
}

/* İki boru: ba = ebeveyn->çocuk, bb = çocuk->ebeveyn */
static int ba[2], bb[2];
```

Zamanlama için `CLOCK_MONOTONIC` saati kullanılır; bu saat sistem saati ayarlamalarından etkilenmez. `tek_cpu`, bu çağrıyı yapan iş parçacığını (Linux'ta tek bir görev) yalnızca CPU 0'da çalışmaya kısıtlar. İki boru, ebeveyn–çocuk ve çocuk–ebeveyn yönlerini taşır.

Sıradaki fonksiyon, ping-pong'un çocuk tarafında çalışan döngüdür: gelen bir bayt okur ve aynı baytı geri yazar.

```c
static void *is_yanki(void *arg)
{
    char c;
    (void)arg;
    for (long i = 0; i < N_PINGPONG; i++) {
        if (read(ba[0], &c, 1) != 1) break;
        if (write(bb[1], &c, 1) != 1) break;
    }
    return NULL;
}

/* Tur başına ortalama süre (ns).
 * Bir tur: 2 bağlam değişimi + 4 sistem çağrısı. */
```

Süreç ping-pong'u, ebeveyn ile çocuk arasında iki boru üzerinden tur atar. Çocuk süreç fork'tan itibaren ebeveynin affinity'sini miras alır; bu yüzden iki taraf da aynı çekirdektedir. Tur ölçümü, toplam süreyi tur sayısına bölerek tek tur maliyetini verir.

```c
static double ping_surec(void)
{
    char c = 'x';
    tek_cpu();              /* çocuk fork'tan affinity miras alır */
    if (pipe(ba) < 0 || pipe(bb) < 0) exit(1);
    pid_t pid = fork();
    if (pid == 0) {
        is_yanki(NULL);
        _exit(0);
    }
    double t0 = simdi_ns();
    for (long i = 0; i < N_PINGPONG; i++) {
        if (write(ba[1], &c, 1) != 1) break;
        if (read(bb[0], &c, 1) != 1) break;
    }
    double t1 = simdi_ns();
    waitpid(pid, NULL, 0);
    return (t1 - t0) / N_PINGPONG;
}
```

İş parçacığı sürümü aynı boru ve aynı döngüyü kullanır; yalnızca çocuk yerine bir `pthread` iş parçacığı vardır. Aradaki fark, iş parçacıklarının aynı adres uzayını paylaşmasından gelir: CR3 değişmez.

```c
static double ping_is(void)
{
    char c = 'x';
    pthread_t t;
    tek_cpu();
    if (pipe(ba) < 0 || pipe(bb) < 0) exit(1);
    pthread_create(&t, NULL, is_yanki, NULL);
    double t0 = simdi_ns();
    for (long i = 0; i < N_PINGPONG; i++) {
        if (write(ba[1], &c, 1) != 1) break;
        if (read(bb[0], &c, 1) != 1) break;
    }
    double t1 = simdi_ns();
    pthread_join(t, NULL);
    return (t1 - t0) / N_PINGPONG;
}
```

Sistem çağrısı ölçümünde `syscall(SYS_getppid)` kullanılır. glibc `getppid`'i önbelleğe almaz; her çağrı çekirdeğe gider. Döngüye `volatile` bir toplam eklemek, derleyicinin çağrıyı atmasını engeller.

```c
static double syscall_ns(void)
{
    volatile long sonuc = 0;
    double t0 = simdi_ns();
    for (long i = 0; i < N_SYSCALL; i++)
        sonuc += syscall(SYS_getppid);
    /* glibc getppid'i önbelleklemez: her çağrı çekirdeğe gider */
    double t1 = simdi_ns();
    return (t1 - t0) / N_SYSCALL;
}
```

Oluşturma ölçümü, süreç ve iş parçacığının tam ömrünü (oluştur, bekle) zamanlar. Aşağıdaki boş iş parçacığı fonksiyonu, yalnızca oluşturma maliyetini ölçmek için kullanılır.

```c
static void *bos_is(void *arg)
{
    (void)arg;
    return NULL;
}
```

Süreç oluşturma döngüsünde her turda `fork`, çocukta hemen `_exit`, ebeveynde `waitpid` çağrılır. Bu, çıkış ve toplama dahil olmak üzere süreç ömrünün maliyetini verir.

```c
static double surec_olustur_ns(void)
{
    double t0 = simdi_ns();
    for (long i = 0; i < N_OLUSTUR; i++) {
        pid_t p = fork();
        if (p == 0) _exit(0);
        waitpid(p, NULL, 0);
    }
    return (simdi_ns() - t0) / N_OLUSTUR;
}
```

İş parçacığı oluşturma döngüsü aynı yapıdadır: `pthread_create` ve `pthread_join`. Böylece iki ölçüm eşit işi yapar ve sonuçları doğrudan karşılaştırılabilir.

```c
static double is_olustur_ns(void)
{
    double t0 = simdi_ns();
    for (long i = 0; i < N_OLUSTUR; i++) {
        pthread_t t;
        pthread_create(&t, NULL, bos_is, NULL);
        pthread_join(t, NULL);
    }
    return (simdi_ns() - t0) / N_OLUSTUR;
}
```

Ana fonksiyon, her ölçümü tekrar sayısı kadar çalıştırır ve sonucu CSV satırı olarak basar.

```c
int main(int argc, char **argv)
{
    int tekrar = (argc > 1) ? atoi(argv[1]) : 5;
    printf("olcum,tekrar,deger_ns\n");
    for (int k = 1; k <= tekrar; k++) {
        printf("syscall_getppid,%d,%.1f\n", k, syscall_ns());
        printf("pingpong_surec_cpu0,%d,%.1f\n", k, ping_surec());
        printf("pingpong_is_cpu0,%d,%.1f\n", k, ping_is());
        printf("olustur_surec,%d,%.1f\n", k, surec_olustur_ns());
        printf("olustur_is,%d,%.1f\n", k, is_olustur_ns());
    }
    return 0;
}
```

Programı derleyip çalıştırdığımızda beş tekrarın CSV çıktısı şöyle oluştu:

```term
$ gcc -O2 -Wall -Wextra -std=c11 -pthread ctx_olcum.c -o ctx_olcum
$ ./ctx_olcum 5 > ctx_olcum.csv
$ cat ctx_olcum.csv
olcum,tekrar,deger_ns
syscall_getppid,1,295.1
pingpong_surec_cpu0,1,9468.8
pingpong_is_cpu0,1,8695.9
olustur_surec,1,253102.7
olustur_is,1,49851.6
syscall_getppid,2,217.6
pingpong_surec_cpu0,2,8740.4
pingpong_is_cpu0,2,8517.3
olustur_surec,2,220180.5
olustur_is,2,44383.7
syscall_getppid,3,208.9
pingpong_surec_cpu0,3,8261.7
pingpong_is_cpu0,3,8023.1
olustur_surec,3,223246.5
olustur_is,3,43435.4
syscall_getppid,4,207.8
pingpong_surec_cpu0,4,8588.9
pingpong_is_cpu0,4,8152.3
olustur_surec,4,223696.5
olustur_is,4,45774.5
syscall_getppid,5,207.7
pingpong_surec_cpu0,5,8697.7
pingpong_is_cpu0,5,8183.7
olustur_surec,5,235293.2
olustur_is,5,47492.9
```

Bu çıktıdaki ilk tekrar diğerlerinden belirgin biçimde yavaş: bu, ilk ölçümde önbelleklerin ve sayfa tablolarının ısınmamış olmasının etkisidir. Bu yüzden tek bir uç değere bağlı kalmamak için ortancayı (medyan) kullanırız. Beş tekrarın ortancaları şöyledir:

| Ölçüm | Ortanca | Yorum |
|---|---|---|
| `getppid` sistem çağrısı | 207 ns | çekirdeğe gidip dönmek |
| Boru ping-pong, iş parçacığı | 7,8 µs | 2 bağlam değişimi + 4 sistem çağrısı |
| Boru ping-pong, süreç | 8,3 µs | aynı, ama adres uzayı da değişir |
| İş parçacığı oluştur + bekle | 44 µs | `pthread_create` + `pthread_join` |
| Süreç oluştur (fork) + bekle | 221 µs | `fork` + çıkış + `wait` |

Şekil 26.8, bu ortancaları logaritmik ölçekte gösteriyor. Dikkat edilecek nokta, bir sistem çağrısı (0,2 µs) ile bir süreç oluşturma (221 µs) arasında yaklaşık üç büyüklük mertebesi olmasıdır. Bu fark, yüksek performanslı sunucuların neden her bağlantı için yeni süreç yerine iş parçacığı veya olay döngüsü kullanmaya yöneldiğinin ilk kanıtıdır (26.13).

![Şekil 26.8: Sistem çağrısı, bağlam değişimi ve oluşturma maliyetleri (ortanca, log ölçek). Değerler WSL2 üzerinde ölçüldü; mutlak değerler donanıma göre değişir.](gorseller/b26_maliyet.png)

Bu sayıları yorumlarken üç sınırı akılda tut. Birincisi, ortam bir sanal makine: WSL2 çekirdeği bir Hyper-V sanal makinesinde çalışır ve sistem çağrılarının maliyeti yerel Linux'tan farklı olabilir. İkincisi, ping-pong ölçümü yalnızca bağlam değişimi değildir: her tur bir sistem çağrısı ve bir uyandırma (wakeup) içerir. Bu yüzden 8 µs, bağlam değişiminin tek başına maliyeti sayılmaz; bir üst sınırdır. Üçüncüsü, süreç ve iş parçacığı ping-pong'u arasındaki fark (8,3 ile 7,8 µs) küçüktür ve bu ölçümle adres uzayı değişiminin payını ayırt edemeyiz; bu, ancak donanım sayaçlarıyla (örneğin `perf`) netleştirilebilir.

Son olarak, bu deneyin mesajı bir ödünleşimdir: RR'de küçük bir `q` yanıt süresini iyileştirir, ama her dilimde bu maliyeti öder. Bağlam değişimini ölçtüğünde, bir zamanlayıcının dilim uzunluğunu neden milisaniyelerle sınırladığını sayılarla görmüş olursun.

## 26.10 İş parçacıkları: süreçten ne eksik, ne fazla?

Bir süreç içinde birden çok yürütme akışı olabilir: buna **iş parçacığı (thread)** denir. Bir iş parçacığı kendi yazmaçlarına, kendi yığınına ve kendi program sayacına sahiptir; ama aynı süreçteki diğer iş parçacıklarıyla adres uzayını, açık dosyalarını ve sinyal işleyicilerini paylaşır. Yani iş parçacığı, sürecin kaynak sahipliğinde değil, yürütme akışında ayrılmış bir bileşendir.

Aşağıdaki tablo, neyin paylaşıldığını ve neyin her iş parçacığına özel olduğunu özetler:

| Bileşen | Süreçte | İş parçacığı içinde |
|---|---|---|
| Adres uzayı (kod, global veri, heap) | süreç başına bir tane | **paylaşılır** |
| Açık dosya tanımlayıcıları | süreç başına | **paylaşılır** |
| Sinyal işleyicileri | süreç başına | **paylaşılır** |
| PID | süreç başına bir tane | aynı (süreç kimliği) |
| Yığın (stack) | süreç başına bir ana yığın | **her iş parçacığına özel** |
| Yazmaçlar ve program sayacı | | **her iş parçacığına özel** |
| Thread-local depolama (TLS) | | **her iş parçacığına özel** |
| Kendi TID'si | | **her iş parçacığına özel** |

Bu tablonun mantığı, iş parçacıklarının neden hızlı, neden tehlikeli olduğunu birlikte açıklar. Paylaşım sayesinde iki iş parçacığı veri alışverişini bir değişkene yazarak yapar; kopyalama gerekmez. Ama aynı değişkene aynı anda yazan iki iş parçacığı, Bölüm 27'de göreceğimiz yarış koşulunu oluşturur. Şekil 26.9, iki sürecin ayrı adres uzaylarını ve bir sürecin iki iş parçacığını yan yana gösteriyor.

![Şekil 26.9: Sol: iki süreç, iki ayrı adres uzayı (kopyalanır veya ayrılır). Sağ: bir süreç, iki iş parçacığı; kod, global veri ve heap paylaşılır, yığınlar ve yazmaçlar ayrıdır.](gorseller/b26_bellek_resmi.png)

Linux'ta iş parçacığı oluşturmanın standart yolu POSIX `pthread` kütüphanesidir: `pthread_create` yeni bir iş parçacığı başlatır, `pthread_join` onun bitmesini bekler. Aşağıdaki program, paylaşım kurallarını gerçekte gözlemlemek için yazıldı. Her iş parçacığı yerel bir değişken tanımlar ve global değişkenin ile yerel değişkenin adresini yazdırır.

```c
/* threads.c: iş parçacıkları ile süreç kaynaklarının
 * karşılaştırılması.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -pthread threads.c */
#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

/* veri bölümünde; tüm iş parçacıkları görür */
int global_sayi = 42;

static void *is(void *arg)
{
    int yerel = 7;           /* kendi yığınında yaşar */
    printf("%s: pid=%d tid=%ld global=%p yerel=%p\n",
           (const char *)arg, (int)getpid(),
           (long)syscall(SYS_gettid),
           (void *)&global_sayi, (void *)&yerel);
    return NULL;
}

int main(void)
{
    pthread_attr_t attr;
    size_t yigin;
    pthread_attr_init(&attr);
    pthread_attr_getstacksize(&attr, &yigin);
    printf("varsayılan iş parçacığı yığını: %zu KB\n",
           yigin / 1024);
    pthread_attr_destroy(&attr);

    printf("ana: pid=%d tid=%ld\n",
           (int)getpid(), (long)syscall(SYS_gettid));

    pthread_t a, b;
    pthread_create(&a, NULL, is, "A");
    pthread_create(&b, NULL, is, "B");
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    return 0;
}
```

Programın çıktısı şöyledir. PID, iş parçacıkları arasında aynıdır; TID ise her iş parçacığı için farklıdır. Global değişkenin adresi iki iş parçacığında da aynıdır; yerel değişkenlerin adresleri ise farklıdır, çünkü her iş parçacığının yığını ayrıdır:

```term
$ gcc -O2 -Wall -Wextra -std=c11 -pthread threads.c -o threads
$ ./threads
varsayılan iş parçacığı yığını: 8192 KB
ana: pid=74590 tid=74590
A: pid=74590 tid=74591 global=0x55d16c107010 yerel=0x7da1d4dfeea4
B: pid=74590 tid=74592 global=0x55d16c107010 yerel=0x7da1d45fdea4
```

İki satır da PID olarak `74590`'ı paylaşır; TID'ler ise `74591` ve `74592`'dir. Global adres `0x55d16c107010` ortaktır. Yerel adresler (`0x7da1d4dfeea4` ve `0x7da1d45fdea4`) farklıdır; aralarındaki fark yaklaşık 8 MB, yani varsayılan yığın boyutudur. Bu boyut `pthread_attr_getstacksize` ile 8192 KB olarak okundu; genellikle `ulimit -s` değerine eşittir (genel bilgi). A ve B satırlarının sırası çalıştırmadan çalıştırmaya değişebilir; iki iş parçacığı bağımsız çalışır.

Burada bir kavram ayrımı gerekir. Kullanıcı tarafında çalışan iş parçacığı kütüphanesi ile çekirdeğin gördüğü iş parçacığı farklı şeylerdir. **1:1 modelinde** her kullanıcı iş parçacığı bir çekirdek görevine karşılık gelir; Linux'un NPTL kütüphanesi bu modeli kullanır (genel bilgi). **M:N modelinde** birçok kullanıcı iş parçacığı az sayıda çekirdek görevine çoklanır; bu model kullanıcı alanında daha ucuz geçiş sağlar ama karmaşıktır ve Go'nun goroutine'leri gibi sistemlerde kullanılır (genel bilgi).

### Linux'ta süreç ile iş parçacığı aynı mekanizma

Linux'ta `fork` ve `pthread_create` çekirdekte aynı işi yapar: `clone()` sistem çağrısını kullanırlar. Fark, `clone`'a verilen **bayraklarda** yatar; hangi kaynakların paylaşılacağını bayraklar belirler. `fork` bu paylaşım bayraklarını vermez; `pthread_create` ise paylaşımı ister.

Linux v6.6 çekirdeğinde bu bayrak kurallarının denetlendiği kod `kernel/fork.c` içindeki `copy_process` fonksiyonudur. Bir iş parçacığının bayrakları tutarlı olmak zorundadır: `CLONE_THREAD` sinyal tablosunun paylaşılmasını, sinyal paylaşımı da adres uzayının paylaşılmasını gerektirir. Çekirdek bu kuralları aşağıdaki gibi denetler; kesit, Kod Okuma bölümünde ayrıntılı ele alınacak.

```c
  /*
   * Thread groups must share signals as well, and detached threads
   * can only be started up within the thread group.
   */
  if ((clone_flags & CLONE_THREAD) && !(clone_flags & CLONE_SIGHAND))
    return ERR_PTR(-EINVAL);

  /*
   * Shared signal handlers imply shared VM. By way of the above,
   * thread groups also imply shared VM. Blocking this case allows
   * for various simplifications in other code.
   */
  if ((clone_flags & CLONE_SIGHAND) && !(clone_flags & CLONE_VM))
    return ERR_PTR(-EINVAL);
```

Aynı fonksiyonda iş parçacığı kimliklerinin atandığı yer de önemlidir: `CLONE_THREAD` bayrağı varsa yeni görev, mevcut görevin `tgid`'ini (süreç kimliği) miras alır; yoksa kendi `tgid`'ini alır. `ps`'in bir süreç içindeki iş parçacıklarını tek bir süreç altında toplamasının nedeni budur; `ps -eLf` komutuyla iş parçacıklarını ayrı satırlarda görebilirsin.

```c
  if (clone_flags & CLONE_THREAD) {
    p->group_leader = current->group_leader;
    p->tgid = current->tgid;
  } else {
    p->group_leader = p;
    p->tgid = p->pid;
  }
```

Kısa bir kesit olmasına rağmen mantık açıktır: `CLONE_THREAD` varsa grup lideri ve `tgid` mevcut görevinkiyle aynıdır; yoksa yeni görev kendi grubunun lideri olur. Bayrakların tam listesi `clone(2)` kılavuz sayfasındadır.

Mert'in MertOS çekirdeğinde iş parçacığı desteği yok; yalnızca çekirdek süreçleri (`createProcess`) var. Her süreç 16 KB'lik bir çekirdek yığını ve bir `CpuContext` taşır. Bu, iş parçacığı eklemek için iyi bir başlangıç noktasıdır: iki çekirdek görevi aynı CR3'ü paylaşıp yalnızca yığınlarını ve yazmaçlarını ayırabilir.

## 26.11 Yarış koşulu: neden senkronizasyon gerekir?

İki iş parçacığı aynı değişkene yazdığında ne olur? Bu bölümün amacı sonucu sayılarla görmek; çözümü ise Bölüm 27'ye bırakıyoruz. Aşağıdaki program iki iş parçacığını aynı `sayac` değişkenini on milyon kez artırmak için çalıştırır. Her artış tek bir `sayac++` ifadesidir; kilit ya da atomik işlem yoktur.

```c
/* race.c: iki iş parçacığı aynı sayacı kilitsiz artırır.
 * Derleme: gcc -O0 -Wall -Wextra -std=c11 -pthread race.c
 * Kayıp sayısı her çalıştırmada değişebilir:
 * bu bir yarış koşuludur. */
#include <pthread.h>
#include <stdio.h>

#define N 10000000L

static long sayac = 0;       /* iki iş parçacığı da yazar */

static void *artir(void *arg)
{
    (void)arg;
    for (long i = 0; i < N; i++)
        sayac++;             /* oku, artır, yaz: bölünemez */
    return NULL;
}

int main(void)
{
    pthread_t a, b;
    if (pthread_create(&a, NULL, artir, NULL) != 0 ||
        pthread_create(&b, NULL, artir, NULL) != 0) {
        fprintf(stderr, "pthread_create başarısız\n");
        return 1;
    }
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    printf("beklenen=%ld gerçekleşen=%ld kayıp=%ld\n",
           2 * N, sayac, 2 * N - sayac);
    return 0;
}
```

Programı `-O0` ile derleyip üç kez çalıştırdık. Sonuçlar her seferinde farklı; kayıp sayısı hep sıfırdan büyük:

```term
$ gcc -O0 -Wall -Wextra -std=c11 -pthread race.c -o race0
$ ./race0
beklenen=20000000 gerçekleşen=11196955 kayıp=8803045
$ ./race0
beklenen=20000000 gerçekleşen=10683176 kayıp=9316824
$ ./race0
beklenen=20000000 gerçekleşen=10335378 kayıp=9664622
```

Kayıp neden olur? `sayac++` tek bir komut değildir. Derleyici bunu üç işleme ayırır: değeri bellekten oku, bir artır, sonucu belleğe yaz. İki iş parçacığı bu üç adımı iç içe geçirdiğinde bir artış kaybolur. Aşağıdaki iz tablosu bunun en kısa örneğidir: her iki iş parçacığı da artışı aynı eski değerden hesaplar.

| Adım | İş parçacığı A | İş parçacığı B | `sayac` (bellekte) |
|---|---|---|---|
| 1 | `sayac` değerini okur: 5 | | 5 |
| 2 | | `sayac` değerini okur: 5 | 5 |
| 3 | 5 + 1 = 6 hesaplar, yazar | | 6 |
| 4 | | 5 + 1 = 6 hesaplar, yazar | 6 (bir artış kayboldu) |

Dört adımda iki artış yapıldı ama sayaç yalnızca bir arttı. Bu tür hata deneme sayısına ve zamanlamaya bağlı olduğu için her çalıştırmada başka sonuç verir; yakalaması bu yüzden zordur. Yukarıdaki üç sonucun her biri farklıdır, çünkü iki iş parçacığının ne zaman iç içe geçeceği rastgeledir.

Aynı programı `-O2` ile derlediğimizde sonuç sıfır kayıptı: `beklenen=20000000 gerçekleşen=20000000 kayıp=0`. Bu, kodun doğru olduğu anlamına **gelmez**. Derleyici çıktısına baktığımızda döngünün tek bir komuta indirildiği görülüyor:

```term
$ gcc -O2 -pthread -S race.c -o race_O2.s
$ awk "/artir:/,/ret/" race_O2.s
artir:
.LFB24:
	.cfi_startproc
	endbr64
	addq	$10000000, sayac(%rip)
	xorl	%eax, %eax
	ret
```

Derleyici on milyon artışı tek bir `addq` ile yapmıştır; her iş parçacığı yalnızca tek bir bellek işlemi yapar ve çakışma penceresi neredeyse kapanır. C11 standardına göre iki iş parçacığının aynı bellek konumuna senkronizasyonsuz ve en az birinin yazdığı eşzamanlı erişimi bir **veri yarışıdır** ve tanımsız davranıştır (UB). Tanımsız davranış hem doğru hem yanlış sonuca izin verir. Testte doğru çıkması, kodun güvenli olduğunu kanıtlamaz; derleyici sürümü, bayraklar ya da yük değişince hata geri gelebilir.

Bu deneyden çıkan ders, senkronizasyonun neden gerektiğidir. Bir değişkenin okunması ile yazılması arasında bir boşluk varsa, iki iş parçacığı bu boşlukta birbirinin işini ezer. Çözüm, karşılıklı dışlama (mutex), atomik işlemler ve bellek sıralaması gibi araçlarla bu bölünemez bölgeleri tanımlamaktır. Bunları Bölüm 27'de, bu programı düzelterek göreceğiz.

## 26.12 Python: GIL, thread ve process

Python'da iş parçacıkları vardır, ama CPython'da (en yaygın Python gerçekleştirimi) aynı anda yalnızca bir iş parçacığı Python bayt kodu çalıştırabilir. Bu kısıt **GIL (Global Interpreter Lock)** adı verilen tek bir kilittir. GIL'in nedeni, CPython'un bellek yönetimini basitleştirmektir: nesnelerin referans sayaçları GIL altında güvenle güncellenebilir (genel bilgi).

GIL'in sonucu şudur: saf Python ile yazılmış bir CPU-bağlı (CPU-bound) iş, birden çok iş parçacığına bölünse de paralel çalışmaz. Ama G/Ç-bağlı (I/O-bound) işlerde durum farklıdır: bir iş parçacığı disk, ağ ya da `sleep` beklerken GIL'i bırakır ve diğerleri çalışabilir. Bu bölümün deneyi iki durumu da ölçer.

Deneyin girdileri şöyledir. CPU-bağlı iş, sabit bir döngüde toplam alır; sekiz iş, `random.Random(26)` tohumuyla seçilmiş farklı büyüklüklerde döngüler içerir. G/Ç-bağlı iş ise `time.sleep(0.2)` ile bir G/Ç beklemesini taklit eder (`sleep` GIL'i bırakır). Her senaryo üç kez ölçülür ve ortalaması alınır.

```python
# gil_olcum.py: CPU-bağlı ve G/Ç-bağlı (simüle) işlerde
# thread ve process karşılaştırması.
# Python 3.12 (CPython, GIL'li). Çalıştırma: python gil_olcum.py
# Çıktı: engine\veri\b26_gil.csv (senaryo, tekrar, sure_s)
import csv
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
```

Dosyanın başı, GIL'in ne olduğunu ve neyi ölçtüğümüzü açıklayan yorumları ve gerekli içe aktarmaları içerir.

```python
def cpu_is(n):
    """Saf Python döngüsü: GIL'i tutar, CPU'yu tek başına kullanır."""
    s = 0
    for i in range(n):
        s += (i * i) % 7
    return s
```

`cpu_is`, tipik bir CPU-bağlı işi temsil eder: her turda bir çarpma, bir mod alma ve bir toplama. Bu döngü GIL'i tutar.

```python
def io_is(saniye):
    """G/Ç beklemesi taklidi: time.sleep GIL'i bırakır."""
    time.sleep(saniye)
    return saniye
```

`io_is` ise yalnızca bir `sleep` çağrısıdır. Burada gerçek bir ağ isteği değil, bir G/Ç beklemesi taklidi kullanıyoruz; amaç GIL'in bırakılmasının etkisini ölçmektir.

```python
def sure_olc(fn, argumanlar, havuz_sinifi, isci):
    if havuz_sinifi is None:              # sıralı referans
        t0 = time.perf_counter()
        for a in argumanlar:
            fn(a)
        return time.perf_counter() - t0
    with havuz_sinifi(max_workers=isci) as ex:
        list(ex.map(fn, [argumanlar[0]] * isci))  # süreçleri başlat
        t0 = time.perf_counter()
        list(ex.map(fn, argumanlar))
        return time.perf_counter() - t0
```

`sure_olc`, havuzu ve iş sayısını alır, havuzu önceden ısıtır (süreçlerin başlaması zaman alır) ve yalnızca iş sürelerini ölçer. Sıralı referans için havuz `None` olarak verilir.

```python
def main():
    rnd = random.Random(26)
    cpu_args = [rnd.randint(3_000_000, 5_000_000) for _ in range(8)]
    io_args = [0.2] * 8
    print("mantıksal çekirdek:", os.cpu_count(), "| Python:",
          sys.version.split()[0])
```

Ana fonksiyon altı senaryoyu üç tekrarla çalıştırır. Önce girdiler tohumlu üreteçle oluşturulur ve sistemin mantıksal çekirdek sayısı basılır.

```python
    senaryolar = [
        ("cpu_sirali", cpu_is, cpu_args, None, 1),
        ("cpu_thread4", cpu_is, cpu_args, ThreadPoolExecutor, 4),
        ("cpu_process4", cpu_is, cpu_args, ProcessPoolExecutor, 4),
        ("io_sirali", io_is, io_args, None, 1),
        ("io_thread8", io_is, io_args, ThreadPoolExecutor, 8),
        ("io_process8", io_is, io_args, ProcessPoolExecutor, 8),
    ]
```

Senaryo listesi her senaryonun adını, işi, havuz sınıfını ve iş parçacığı ya da süreç sayısını tutar. Havuz sınıfları `ThreadPoolExecutor` ile `ProcessPoolExecutor`'dır; ikisi de `concurrent.futures` kütüphanesinin aynı arayüzünü paylaşır.

```python
    satirlar = []
    for tekrar in range(1, 4):
        for ad, fn, args, havuz, isci in senaryolar:
            s = sure_olc(fn, args, havuz, isci)
            satirlar.append({"senaryo": ad, "tekrar": tekrar,
                             "sure_s": round(s, 3)})
            print("%-14s tekrar=%d  %.3f s" % (ad, tekrar, s))
```

Döngü her senaryoyu ve tekrarı çalıştırır, sonucu ekrana yazar ve listeye ekler.

```python
    yol = r"D:\Mevcut Projeler\Kitap\engine\veri\b26_gil.csv"
    with open(yol, "w", newline="", encoding="utf-8") as f:
        alanlar = ["senaryo", "tekrar", "sure_s"]
        w = csv.DictWriter(f, fieldnames=alanlar)
        w.writeheader()
        w.writerows(satirlar)
    print("CSV:", yol)


if __name__ == "__main__":
    main()
```

Programın çıktısı ölçümün ham hâlidir:

```term
$ python gil_olcum.py
mantıksal çekirdek: 16 | Python: 3.12.10
cpu_sirali     tekrar=1  2.078 s
cpu_thread4    tekrar=1  1.962 s
cpu_process4   tekrar=1  0.593 s
io_sirali      tekrar=1  1.603 s
io_thread8     tekrar=1  0.201 s
io_process8    tekrar=1  0.202 s
cpu_sirali     tekrar=2  2.040 s
cpu_thread4    tekrar=2  2.075 s
cpu_process4   tekrar=2  0.624 s
io_sirali      tekrar=2  1.603 s
io_thread8     tekrar=2  0.201 s
io_process8    tekrar=2  0.202 s
cpu_sirali     tekrar=3  2.225 s
cpu_thread4    tekrar=3  2.051 s
cpu_process4   tekrar=3  0.601 s
io_sirali      tekrar=3  1.602 s
io_thread8     tekrar=3  0.201 s
io_process8    tekrar=3  0.202 s
CSV: D:\Mevcut Projeler\Kitap\engine\veri\b26_gil.csv
```

Üç tekrarın ortalamasını alırsak: CPU-bağlı sıralı iş 2,11 s sürdü; dört iş parçacığıyla 2,03 s (neredeyse hiç hızlanma yok); dört süreçle 0,61 s (yaklaşık 3,5 kat). G/Ç-bağlı işte ise sıralı 1,60 s, sekiz iş parçacığıyla 0,20 s ve sekiz süreçle 0,20 s sürdü. Şekil 26.10 bu sonucu gösteriyor.

![Şekil 26.10: CPU-bağlı ve G/Ç-bağlı işlerde sıralı, iş parçacığı ve süreç havuzu süreleri (üç tekrarın ortalaması, hata çubukları min–maks yarısı).](gorseller/b26_gil.png)

Sonuçların yorumu şöyledir. CPU-bağlı işte iş parçacıkları GIL yüzünden paralel çalışamaz; çalışma süresi, iş parçacıklarının GIL için sıra beklemesiyle geçer. Süreçlerin ayrı yorumlayıcıları ve ayrı GIL'leri vardır; bu yüzden dört çekirdekte gerçekten paralel çalışırlar. G/Ç-bağlı işte ise iş parçacıkları yeterlidir, çünkü bekleme sırasında GIL serbest kalır; süreç havuzunun ek maliyeti (süreç başlatma, nesnelerin serileştirilmesi) bu durumda gereksizdir.

Python 3.13 ile birlikte GIL'siz (free-threaded) bir derleme deneysel olarak sunuldu: `python3.13t` ile çalışan bu sürüm GIL'i isteğe bağlı kılarak iş parçacıklarının CPU-bağlı işte paralel çalışmasını hedefler (PEP 703; genel bilgi). Bu bölümde Python 3.12 kullandık ve GIL'siz derlemeyi denemedik; üretim kodunda olgunluğunu sürüm notlarından kontrol etmelisin.

## 26.13 Gerçek dünya: sunucu modelleri ve tarayıcılar

Bir ağ sunucusu aynı anda binlerce bağlantıyı karşılamalıdır. Bu, süreç, iş parçacığı ve olay döngüsü arasında bir seçim gerektirir. Üç klasik model vardır (genel bilgi):

- **Süreç başına bağlantı:** her yeni bağlantı için bir `fork`. Yalıtım çok iyidir: bir süreçteki çökme diğerlerini etkilemez. Ama 26.9'da ölçtüğümüz gibi süreç oluşturma yüzlerce mikrosaniye sürer ve her süreç kendi bellek alanını taşır. Eski Apache `prefork` modeli bunu kullanır.
- **İş parçacığı başına bağlantı:** her bağlantı için bir iş parçacığı. Oluşturma maliyeti süreçten düşüktür ve bellek paylaşılır. Ama binlerce iş parçacığı yığın belleği ve zamanlayıcı yükü getirir; paylaşılan veriye erişimde senkronizasyon gerekir.
- **Olay döngüsü:** tek ya da az sayıda iş parçacığı, `epoll` gibi bir mekanizmayla çok sayıda bağlantının hazır olup olmadığını sorar ve yalnızca hazır olanlara bakar. Nginx ve Node.js bu modeli kullanır; on bin eşzamanlı bağlantı (C10K) probleminin çözümünün temelidir. `epoll` ve dosya tanımlayıcı tarafı Bölüm 28'de, soketler Bölüm 31'de işlenecek.

Hangi model seçilirse seçilsin bağlam değişimi maliyeti ve bellek tüketimi bir ödünleşim oluşturur. Bu bölümün ölçümleri (26.9) bu ödünleşimin sayılarını verir: sistem çağrısı 0,2 µs, süreç oluşturma 221 µs, iş parçacığı oluşturma 44 µs.

Tarayıcılar da benzer bir ayrıma dayanır (genel bilgi): modern tarayıcılar sekmeleri veya siteleri ayrı süreçlerde çalıştırır. Amaç, bir sekmedeki çökmenin ya da kötü niyetli kodun diğer sekmelere ve ana tarayıcıya sıçramasını önlemektir. Bunun bedeli bellek ve süreç sayısıdır; güvenlik kazancı ise bu bedelden büyüktür.

Mert'in MertOS çekirdeğinde süreç yönetimi, bu bölümde gördüğümüz kavramların küçük bir gerçekleşimidir. `ProcessManager` en fazla 32 süreci tutar (`MAX_PROCESSES = 32`), her sürece 10 tick'lik bir dilim verir (`DEFAULT_TIME_SLICE = 10`) ve `schedule()` (`kernel/process/process.cpp`, 125. satır) mevcut süreçten sonra gelen ilk hazır süreci seçer: kaynakta saf bir round-robin var. Bağlam değişimi `contextSwitch` fonksiyonundan yapılır ve yazmaç kaydetme ile yüklemesi `switchContext` assembly'sinde gerçekleşir.

Kaynağı okurken bir tutarsızlık dikkatimi çekti ve bunu bir alıştırma olarak bırakıyorum. Yeni bir sürecin ilk çalışma noktası `process_entry_wrapper`'dır ve bu fonksiyon `call rax` ile giriş fonksiyonunu çağırır (`kernel/process/context_switch.asm`, 75. satır). Ama `ProcessManager::createProcess`'te yorum "RAX'a entry adresi koyuyoruz" der; kodda ise giriş adresi `rbx`'e atanıyor (`kernel/process/process.cpp`, 104 ve 107. satırlar). Dahası `switchContext`, yeni sürecin CR3 değerini CR3 karşılaştırması için `rax`'a yükler ve bu yazmacı ilk çalıştırmada temizlemez. Kodu okuyan biri, ilk `call rax`'ın giriş fonksiyonu yerine sayfa tablosu adresine atlayacağını düşünebilir. Bunu kendi derlemenle, bir QEMU ya da hata ayıklayıcı oturumunda doğrulamanı öneririm; bu hatanın yakalanması, bağlam değişiminin hangi yazmaçları koruduğunu tam olarak bilmeyi gerektirir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her birinde Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler, örnekte verilen programın çıktısıyla aynıdır. Önce kendi kâğıdında ilk üç adımı dene; çözümü okumadan önce tahminini yaz.

### Örnek 1 (★): Döngüde fork kaç süreç üretir?

**Problem:** Aşağıdaki döngü `fork` çağırıp her sürecin bir satır `x` yazmasını sağlıyor (`fork_agac.c`, 26.3). Döngü üç kez çalıştığında kaç süreç oluşur ve terminale toplam kaç satır yazılır? Çıktı tamponsuz ve tamponlu modda nasıl değişir?

**Adım 1 — Anla.** Girdi yok; çıktı iki sayı: süreç sayısı ve yazılan satır sayısı. Tamponlu ve tamponsuz modu ayrı ayrı yanıtlamalıyız. Kenar durum: döngü sıfır kez çalışırsa tek süreç vardır ve tek satır yazılır.

**Adım 2 — Örnekle.** Döngü bir kez çalışsın. Başta bir süreç var. `fork` sonrası iki süreç olur ve ikisi de `x` yazar: iki satır. İki kez çalışsın. İlk turdan sonra iki süreç var; ikinci turda her biri bir kez daha `fork` yapar, dört süreç olur ve dördü de `x` yazar. Toplam `2 + 4 = 6` satır.

**Adım 3 — Kaba çöz.** Her turda o ana kadar var olan süreçlerin sayısını ikiye katla ve yazılan satırları topla. Üç turda `2 + 4 + 8 = 14` satır. Tamponlu modda ise çocuklar `fork`'tan önce tampon içeriğini de kopyalar; bu yüzden kopya sayısı ile tamponda kalan satır sayısı çarpılır. Kaba tahmin şimdilik `14` ya da `24` olabilir; hangisinin doğru olduğunu Adım 6'da göreceğiz.

**Adım 4 — Örüntü.** Döngünün `i`'inci turunda (0'dan başlayarak) `fork`'tan önce `2^i` süreç vardır; `fork`'tan sonra `2^(i+1)` süreç olur ve her biri bir satır yazar. Tamponsuz toplam `n` tur için `2 + 4 + ... + 2^n = 2^(n+1) - 2`'dir. Tamponlu durumda son `2^n` sürecin her biri, `fork`'lardan önce biriken `n` satırı taşır; toplam `2^n · n` olur. `n = 3` için bu, tamponsuz `14` ve tamponlu `8 · 3 = 24` eder.

**Adım 5 — İyileştir.** Programı değiştirmeden doğru sonucu almak için iki yol var: `setvbuf(stdout, NULL, _IONBF, 0)` ile tamponu kapatmak ya da her `fork`'tan önce `fflush(stdout)` çağırmak. İkisi de aynı sonucu verir; ama `fflush` daha seçici olduğu için büyük çıktılarda tercih edilebilir. Yalnızca `stdout` boşaltılmalıdır; `stderr` zaten tamponsuzdur.

**Adım 6 — Doğrula.** Her turun izini elle sür:

| Tur `i` | `fork` öncesi süreç | `fork` sonrası süreç | Her sürecin tamponundaki satır (önceki turlardan) | Tamponsuz yazılan satır |
|---|---|---|---|---|
| 0 | 1 | 2 | 0 | 2 |
| 1 | 2 | 4 | 1 | 4 |
| 2 | 4 | 8 | 2 | 8 |
| Toplam | | | | 14 |

Tamponlu durumda her turda oluşan süreçler, bu turda biriken satırı da kopyalar. Son turdan sonra 8 sürecin her birinde 3 satır vardır: `8 · 3 = 24`. Gerçek çalıştırma bu sonucu doğruladı:

```term
$ ./fork_agac -u | wc -l
14
$ ./fork_agac | wc -l
24
```

**Bunu AI'sız yazabilir misin?** Döngüyü dört kez çalıştırsaydın tamponsuz toplam kaç satır olurdu? Bunu formülle hesapla, sonra programı derleyip doğrula. Tamponlu toplamın formülünü de yaz ve bir kez deneyerek kontrol et.

### Örnek 2 (★★): Round Robin Gantt şeması ve ortalama bekleme

**Problem:** Üç süreç aynı anda, `t = 0`'da gelir: `P1` 24 birim, `P2` 3 birim, `P3` 3 birim. Zaman dilimi `q = 4`. Gantt şemasını çiz, her sürecin bekleme ve dönüş süresini bul, ortalama beklemeyi hesapla. Sonucu simülatörle (26.7) doğrula.

**Adım 1 — Anla.** Çıktı bir Gantt şeması ve üç bekleme süresinin ortalamasıdır. Dönüş süresi `bitiş − varış`, bekleme ise `dönüş − süre`'dir. Kenar durum yok; ama sürecin süresi `q`'dan küçükse dilim erken biter, bunu unutma.

**Adım 2 — Örnekle.** `P1` ilk dilimde 4 birim çalışır ve 20 birim kalır. `P2` ve `P3` kısa; her biri tek dilimde biter. Kuyruk sırası ilk turda `P1 → P2 → P3`'tür.

**Adım 3 — Kaba çöz.** Kuyrukta döngü yap: her seferinde baştaki süreci en fazla 4 birim çalıştır, bitmediyse arkaya at. Sonuç: `P1` 0–4, `P2` 4–7, `P3` 7–10, sonra `P1` kalan 20 birimi bitirir.

**Adım 4 — Örüntü.** Tüm süreçler `t=0`'da geldiğinden, bekleme süresi, sürecin ilk dilimine kadar beklediği zamanın toplamıdır. Her süreç kuyruktan ilk kez çıkarken geçen zamanı ve sonraki dilimlerdeki bekleme zamanını ayrı ayrı topla. Daha basiti: bitiş zamanını bul ve sürecin süresini çıkar.

**Adım 5 — İyileştir.** Kuyruğu bir dairesel liste gibi düşünebiliriz; her dilim sonunda süreç arkaya gider. Programlama tarafında bir `deque` yeterlidir. Ayrıca `q`'yu değiştirmenin etkisini görmek için simülatörde yalnızca tek parametreyi değiştirmek yeterlidir.

**Adım 6 — Doğrula.** Elle iz tablosu:

| Tick aralığı | Çalışan | Kalan süre sonrası | Kuyruk (sonraki sıra) |
|---|---|---|---|
| 0–4 | P1 | P1: 20 | P2, P3, P1 |
| 4–7 | P2 | P2: 0 (bitti, bitiş 7) | P3, P1 |
| 7–10 | P3 | P3: 0 (bitti, bitiş 10) | P1 |
| 10–30 | P1 | P1: 0 (bitti, bitiş 30) | (boş) |

Bekleme süreleri: `P1 = 30 − 24 = 6`, `P2 = 7 − 3 = 4`, `P3 = 10 − 3 = 7`. Ortalama `(6 + 4 + 7) / 3 = 5,67`. Simülatör aynı tabloyu verir:

```term
RR q=4   P1[0-4)  P2[4-7)  P3[7-10)  P1[10-30)
         bekleme: P1=6, P2=4, P3=7  ORT=5.67
```

**Bunu AI'sız yazabilir misin?** Aynı üç süreçte FCFS ve SJF'in ortalama beklemelerini de elle hesapla. Sonra `q = 1` için iz tablosunu yaz. `q` küçüldükçe ortalama bekleme nasıl değişir ve neden? Yanıtını bağlam değişimi maliyetiyle (26.9) ilişkilendir.

### Örnek 3 (★★): Üretici–tüketici ve pipe'ın EOF mekanizması

**Problem:** Ebeveyn 1'den 10'a kadar tam sayıları bir boruya yazar; çocuk bunları okur, yazdırır ve toplar. Kod bölüm 26.5'te tamamen verildi (`uretici_tuketici.c`). Çıktıda toplam kaç satır var, son satır ne ve programın sonlanması neye bağlı?

**Adım 1 — Anla.** Çıktı on `aldı:` satırı ve bir `toplam=` satırıdır. Asıl soru, okuyan tarafın döngüden ne zaman çıktığıdır. Kenar durum: ebeveyn hiç yazmazsa çocuk ne yapar? Cevap: hemen EOF alır ve toplam 0 yazar.

**Adım 2 — Örnekle.** `1, 2, 3` yazılsın. Çocuk önce `1`'i okur, sonra `2`'yi, sonra `3`'ü. Dördüncü `read` ne döndürür? Yazma ucu hâlâ açıksa çocuk beklemeye devam eder; kapalıysa `0` döner.

**Adım 3 — Kaba çöz.** Ebeveyn yazma bitince yazma ucunu kapatır; çocuk okuma ucunda bekleyip `0` gördüğünde döngüden çıkar. Bu, sistemin "bu boruya artık yazan yok" bilgisini verme yoludur.

**Adım 4 — Örüntü.** Borunun EOF'u, **tüm** yazma uçlarının kapalı olmasıyla oluşur. Fork sonrası her iki süreçte de iki uç da bulunur; bu yüzden her süreç kendi kullanmadığı ucu kapatmalıdır. Çocuk yazma ucunu, ebeveyn okuma ucunu kapatır. Ebeveynin yazma ucunu kapatması çocuğa EOF'u verir.

**Adım 5 — İyileştir.** Okuma ve yazma tamponlarını bayt yerine tam sayı olarak yazmak, her çağrıda `sizeof` kullanmak yeterlidir; bu program zaten bunu yapar. Büyük veri için bir arabellekte toplu yazma yapılabilir; `write` çağrısı sayısı düşer.

**Adım 6 — Doğrula.** Süreçlerin uç durumlarını elle izle (fd numaraları örnektir; ortama göre değişebilir):

| Adım | Ebeveyn | Çocuk | Açık uçlar (ebeveyn / çocuk) | Olay |
|---|---|---|---|---|
| 1 | `pipe()` → okuma 3, yazma 4 | | 3, 4 / — | boru oluşur |
| 2 | `fork()` | kopyalanır | 3, 4 / 3, 4 | iki süreçte de iki uç |
| 3 | `close(3)` | `close(4)` | 4 / 3 | rol dağılımı |
| 4 | `write` ×10 | `read` → 1, 2, ..., 10 | 4 / 3 | veri akar |
| 5 | `close(4)` | `read` → 0 (EOF) | — / 3 | yazma ucu kapalı, EOF |
| 6 | `waitpid` | `toplam=55` yazar, `close(3)` | — / — | süreç sonu |

Toplam `1 + 2 + ... + 10 = 55`'tir ve gerçek çıktıyla birebir eşleşir:

```term
$ ./uretici_tuketici | tail -2
aldı: 10
toplam=55
```

**Bunu AI'sız yazabilir misin?** Aynı iki sürecin arasında hem ebeveyn→çocuk hem çocuk→ebeveyn yönlü iki boru kur; çocuk her sayıyı alır almaz bir onay (`ack`) göndersin. Hangi durumda iki süreç birbirini sonsuza dek bekler (kilitlenme)? Bu kilitlenmeyi önlemek için hangi sıra kuralı gerekir?

### Örnek 4 (★★★): Üç aşamalı boru hattını C'de kurmak

**Problem:** `cat /etc/passwd | grep -E "^root" | wc -l` komutunu C'de kur. Kod bölüm 26.5'te verildi (`boru3.c`). Çıktı `1` olmalı. Ayrıca `HATA_ACIK` sürümünün neden asılı kaldığını açıkla ve süreçleri `ps` ile gözlemle.

**Adım 1 — Anla.** Üç çocuk süreç ve iki boru gerekir: `cat → grep` için `p1`, `grep → wc` için `p2`. Girdi dosyası sabit, çıktı tek sayı. Kenar durum: `grep` hiç eşleşme bulmazsa `wc` `0` yazar; boru hattı yine çalışır.

**Adım 2 — Örnekle.** `/etc/passwd` dosyasında yalnızca bir satır `root` ile başlıyorsa `grep` çıktısı tek satırdır ve `wc` bunu sayar. Bizim ortamımızda `grep -c "^root" /etc/passwd` komutu da `1` verdi; yani beklenen çıktıyı bağımsız olarak doğruladık.

**Adım 3 — Kaba çöz.** Her komut için bir `fork` ve bir `execlp`; komutların arasını dup2 ile birleştir. Her çocukta kullanılmayan uçları kapat; ebeveyn de tüm boru uçlarını kapatıp çocukları beklemeli.

**Adım 4 — Örüntü.** Her çocuk şu kalıbı izler: önce girdiyi ve çıktıyı `dup2` ile ayarla, sonra bütün boru uçlarını kapat, sonra `exec` et. Son adım gereklidir: `dup2` yaptıktan sonra orijinal uçlar yedek olarak kalır ve EOF'u engelleyebilir.

**Adım 5 — İyileştir.** Kapatma satırlarını tek bir `kapat_borular()` fonksiyonunda toplamak kodu okunur kılar. Üç çocuk için tekrar eden kalıbı döngüye almak da mümkündür, ama üç aşamalı örnekte açık yazmak öğretici olduğu için bu bölümde açık tuttuk.

**Adım 6 — Doğrula.** Her çocuğun dosya tanımlayıcılarını izle (numaralar tipik değerlerdir):

| Süreç | stdin (0) | stdout (1) | Kapatılan uçlar | `exec` |
|---|---|---|---|---|
| `cat` | klavye | `p1` yazma (dup2) | `p1` okuma, `p2` iki uç | `cat /etc/passwd` |
| `grep` | `p1` okuma (dup2) | `p2` yazma (dup2) | `p1` iki uç, `p2` okuma | `grep -E ^root` |
| `wc` | `p2` okuma (dup2) | ekran | `p1` iki uç, `p2` yazma | `wc -l` |

Hatalı sürümde (`HATA_ACIK`) ebeveyn `p2`'nin yazma ucunu açık tutar. `wc` EOF bekler, ama bu uç hâlâ açık olduğu için EOF gelmez. Gerçek bir denemede üç süreç de uyku durumunda kaldı:

```term
$ ./boru3_hata &
$ ps -eo pid,ppid,stat,comm | grep -E "boru3|wc"
  53950   52999 S+   boru3_hata
  53954   53950 S+   wc
```

Doğru sürümde ebeveyn tüm uçları kapatır ve çıktı `1` olur. Bu iz tablosu, her boru ucunun kimde açık olduğunu sayarak kilitlenmeyi tahmin etmeyi öğretir.

**Bunu AI'sız yazabilir misin?** `ls | sort | uniq -c` boru hattını C'de kur. Kaç `pipe()` çağrısı gerekir, her çocukta hangi uçlar `dup2` edilir, hangi uçlar kapatılır? Önce kâğıt üzerinde tabloyu doldur, sonra derle.

## Kendin Yap Projeleri

::: dikkat
Kural değişmedi: yapay zekâ araçları **yasak**. Bu iki proje, bölümde yazdığın kabuğu ve zamanlayıcı simülatörünü gerçek bir sisteme yaklaştırıyor. Kodu kendi ellerinle yaz; takıldığında yalnızca ipucu bölümüne dön, tam çözüm arama.
:::

### Proje 1 (★★): Kabuğu genişlet

**Amaç:** Bölüm 26.4'teki `msh.c` kabuğuna üç yeni özellik ekle: `$VAR` ortam değişkeni genişletmesi, `2>` ile stderr yönlendirmesi ve önceki komutun çıkış koduna bağlı `&&` ve `||` zincirleri.

**Beklenen davranış:** `echo $HOME` kullanıcının ev dizinini yazmalı. `ls /yok 2> hata.txt` hatayı `hata.txt`'ye yazmalı, terminale hiçbir şey düşmemeli. `false && echo a` hiçbir şey yazmamalı; `false || echo b` `b` yazmalı. Her durumda çıkış kodu bir sonraki komutun kararında kullanılmalı.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Ortam genişletmesini ayrıştırıcıda, her `argv` öğesi için yapabilirsin; `getenv` bu iş için yeterlidir. `2>` ayrıştırıcısı `<` ve `>` ile aynı kalıbı izler ama farklı bir dosya tanımlayıcısını (2) `dup2` ile ayarlar. Koşullu zincirler için `calistir` fonksiyonunun bir durum değeri döndürmesi gerekir; bekle fonksiyonu bunu zaten `WEXITSTATUS` ile okuyor. Dikkat et: `&&` ve `||` boru hattından daha düşük önceliklidir; ayrıştırıcının bunu nasıl ele alacağını önceden kâğıtta çiz.

**Başarı kriterleri:**
- `echo $HOME` çıktısı `$HOME` ortam değişkeninin değerine eşit.
- `ls /yok 2> hata.txt; cat hata.txt` yazdığı hata metni, `ls`'in stderr çıktısıyla bayt bayt aynı.
- `false && echo a` boş çıktı; `false || echo b` yalnızca `b`.
- 100 arka plan komutu (`sleep 0 &`) çalıştırıp `ps` ile kontrol ettiğinde `Z` durumunda süreç kalmaz.
- Kabuk, `HATA_ACIK` benzeri bir kapatma hatası olmadan boru hattı kurduğunda asılı kalmaz (`cat /etc/hostname | cat | wc -l` 1 yazmalı).

### Proje 2 (★★★): Zamanlayıcı laboratuvarı

**Amaç:** Bölüm 26.7'deki `sched_sim.py` simülatörünü G/Ç patlamalarını (I/O burst) destekleyecek şekilde genişlet. Bir süreç CPU'da bir süre çalıştıktan sonra G/Ç için bloke olur (birkaç tick bekler), sonra tekrar hazır olur. Bu koşulda MLFQ'nun boost (yükseltme) aralığının bekleme ve yanıt sürelerine etkisini ölç ve sonuçları bir grafikle göster.

**Beklenen davranış:** Her süreç bir G/Ç isteği tanımlayabilmeli (ör. "3 tick çalış, 2 tick bloke ol, 4 tick daha çalış"). Bloke süreç CPU'ya aday değildir. Simülatör, her süreç için bekleme, dönüş ve yanıt sürelerini ve tüm algoritmalar için ortalama bekleme değerini yazmalıdır. `boost` aralığı (ör. 10, 20 ve sonsuz) parametre olarak verilebilmelidir.

**Önerilen yaklaşım (ipucu):** Süreç durumlarını `hazir`, `bloke`, `bitti` olarak takip et. Her tick başında bloke olanların sayaçlarını azalt; sayaç sıfıra inince süreci tekrar `hazir` yap. Mevcut `kesintisiz`, `round_robin` ve `mlfq` fonksiyonlarını bir arayüz altında birleştirmek, testlerin tekrar yazılmasını önler. Grafik için `b26_gantt.csv`'ye benzer bir çıktı üret ve matplotlib ile Gantt çiz. Değişiklikten önce mevcut sonuçları kaydet; yeni kod eski sonuçları değiştirmemeli.

**Başarı kriterleri:**
- Bloke süre sıfır verildiğinde yeni simülatör, bu bölümdeki eski çıktıyla birebir aynı sonuçları üretir (regresyon testi).
- MLFQ'da `boost = ∞` ile `boost = 20` arasında ortalama yanıt süresi farkı tablo olarak raporlanır ve farkın yönü yazılır.
- Rastgele 300 örnekte (`random.Random(26)`), G/Ç olmayan durumda SJF'in brute-force optimumla eşleştiği doğrulanır.
- Gantt grafiği üretilir ve her G/Ç bloke aralığı grafikte ayrı bir renkle gösterilir.

### Ek Alıştırmalar

Aşağıdaki on iki problemin cevabı bu bölümde yok; bilerek kısa tuttum. Önce kendin düşün, sonra terminalde ya da kâğıtta dene. Mülakat sorusu olanlar **(mülakat)** etiketiyle işaretli.

1. **★** `for (int i = 0; i < 2; i++) fork();` döngüsünün kaç süreç oluşturduğunu tahmin et. Tamponsuz çıktıda kaç satır görürsün? Önce yaz, sonra çalıştır.
2. **★ (mülakat)** `fork()` sonrası çocuk ve ebeveyn aynı global değişkeni okuyor. Biri değeri değiştirirse diğeri bunu görür mü? Neden? Copy-on-write'ın bu soruya cevabı nasıl bağladığını açıkla.
3. **★★** Bir süreç ağacında (her çocuk kendi çocuklarını üretiyor) tüm alt süreçleri `waitpid(-1, ...)` ile toplayan bir program yaz. Program hiçbir zombi bırakmamalı; bunu `ps` ile kanıtla.
4. **★★ (mülakat)** Zombi bir sürecin PCB'si neden bellekte kalır? Ebeveyn `wait` çağırmadan çıkarsa zombi ne olur? Yetim süreçleri bu bağlamda açıkla.
5. **★★** Bir pipe'ın kapasitesini aşan miktarda veri yazan bir üretici ve yavaş bir tüketici yaz. Üretici hangi noktada bloke olur? `read`'in yavaşlığını değiştirerek bu noktayı ölç.
6. **★★ (mülakat)** Ebeveyn bir dosyayı açıp `fork` yapıyor; ebeveyn ve çocuk aynı dosyadan okuyor. Dosya okuma konumu (offset) paylaşılır mı? `dup` ile `open` arasındaki farkı bu bağlamda açıkla.
7. **★★** Bir sinyal işleyicisinde `printf` kullanmanın neden tehlikeli olduğunu açıkla. Bu hatayı güvenilir biçimde tetikleyen bir program kurmak neden zordur? Yanıtını bir iz tablosuyla destekle.
8. **★★★ (mülakat)** Round Robin'de `q = 1` ile `q = ∞` arasında ortalama yanıt süresi ve bağlam değişimi sayısı nasıl değişir? Simülatörle beş farklı `q` değeri için bir tablo çıkar ve grafikle göster.
9. **★★** Konvoy etkisini gösteren bir iş yükü bul: bir çok uzun süreç ve birkaç kısa süreç. FCFS ile SJF'in ortalama beklemesini karşılaştır ve farkın nereden geldiğini açıkla.
10. **★★★ (mülakat)** Öncelikli bir zamanlayıcıda açlığı (starvation) önlemek için yaşlandırma (aging) nasıl çalışır? Bir formül öner, simülatörde uygula ve düşük öncelikli sürecin bekleme süresinin nasıl değiştiğini ölç.
11. **★★** İki iş parçacığı ile 1'den 10^6'ya kadar olan sayıların toplamını hesapla. Tek iş parçacığından her zaman hızlı olması gerekmez; nedenlerini (paylaşılan önbellek satırı, bellek bant genişliği, iş parçacığı oluşturma maliyeti) ölçümle ayırt etmeye çalış.
12. **★★ (mülakat)** `pthread_join` yerine `pthread_detach` kullanırsan ne değişir? Ana iş parçacığı çıkarsa diğer iş parçacıklarına ne olur? Bunu bir programla gözlemle.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir Linux çekirdeği kaynağını okuyacaksın. Kaynak, Linux **v6.6** etiketinden alındı: `kernel/sched/fair.c` ve `kernel/fork.c`. GitHub'ın ham dosya sunucusu bu oturumda hız sınırına takıldığı için dosyalar `kernel.googlesource.com` üzerindeki aynı etiketten indirildi (Linux'un resmî git aynası); içerik ile dosya yolu birebir aynıdır. Aşağıdaki üç kesit birebir kopyalanmıştır. Girintiler çekirdeğin tab karakteri yerine iki boşlukla gösterildi; hiçbir kod satırı değiştirilmedi.

Birinci kesit, EEVDF'in tanımlandığı açıklama yorumudur (`kernel/sched/fair.c`, 856–870. satırlar). Yorumun 871. satırı (`se->min_deadline = min(...)`) sayfa genişliğini aştığı için bu kesite alınmadı; onun anlamını aşağıdaki soruda ele alıyoruz:

```c
/*
 * Earliest Eligible Virtual Deadline First
 *
 * In order to provide latency guarantees for different request sizes
 * EEVDF selects the best runnable task from two criteria:
 *
 *  1) the task must be eligible (must be owed service)
 *
 *  2) from those tasks that meet 1), we select the one
 *     with the earliest virtual deadline.
 *
 * We can do this in O(log n) time due to an augmented RB-tree. The
 * tree keeps the entries sorted on service, but also functions as a
 * heap based on the deadline by keeping:
 *
```

İkinci kesit, çalışan sürecin sanal çalışma süresinin güncellendiği yerdir (`kernel/sched/fair.c`, 1173–1178. satırlar):

```c
  curr->sum_exec_runtime += delta_exec;
  schedstat_add(cfs_rq->exec_clock, delta_exec);

  curr->vruntime += calc_delta_fair(delta_exec, curr);
  update_deadline(cfs_rq, curr);
  update_min_vruntime(cfs_rq);
```

Üçüncü kesit, `fork` ile `pthread_create`'in ortak fonksiyonu olan `copy_mm`'de adres uzayının paylaşılıp paylaşılmayacağına karar veren dalıdır (`kernel/fork.c`, 1731–1738. satırlar):

```c
  if (clone_flags & CLONE_VM) {
    mmget(oldmm);
    mm = oldmm;
  } else {
    mm = dup_mm(tsk, current->mm);
    if (!mm)
      return -ENOMEM;
  }
```

**Sorular — cevaplamadan geçme:**

1. EEVDF açıklamasında "eligible" (uygun) süreç ne demek? Yorumdaki iki ölçütten hangisi önce uygulanır ve bu neden önemlidir?
2. Yorum, seçimin `O(log n)` olduğunu söylüyor. Bu süreye hangi veri yapısı izin veriyor? Yorumun devamındaki `se->min_deadline = min(se->deadline, se->{left,right}->min_deadline)` satırı, bu alanın ne taşıdığını ve bu sayede hangi aramanın yapıldığını açıklar; açıkla.
3. `update_curr` içinde `calc_delta_fair(delta_exec, curr)` çağrısı, aynı gerçek çalışma süresi için iki süreçte farklı vruntime artışına neden olur? Düşük `nice` değerinin bu hesapta hangi yöne etki ettiğini açıkla.
4. `copy_mm` içinde `CLONE_VM` varken neden `mmget(oldmm)` çağrılıyor? Bu, sayfa tablosunun paylaşımı ile referans sayacı arasında nasıl bir ilişki kurar?
5. `CLONE_VM` yokken `dup_mm` çağrılıyor. Bu dal, 26.3'te gördüğümüz fork'un copy-on-write davranışıyla nasıl bağlantılıdır? Yanıtında Bölüm 25'teki sayfa tablosu kavramını kullan.
6. Mert'in MertOS'una iş parçacığı desteği eklesen, bu kodun hangi kurallarını (ör. paylaşım bayrakları ile adres uzayı tutarlılığı) kendi tasarımına taşırdın? Hangisini gereksiz bulurdun?

## Bölüm Özeti

- Program diskte pasif bir dosyadır; süreç, onun çalışan bir örneğidir ve çekirdek onu PCB ile temsil eder (Linux'ta `task_struct`).
- Süreç durumları YENİ, HAZIR, ÇALIŞIYOR, BEKLİYOR ve ZOMBİ'dir; ZOMBİ, ebeveyn `wait` çağırana kadar kalır.
- `fork` çağrısı iki kez döner; COW sayesinde kopya sayfa yazıldığında yapılır. `fork` öncesi tampon çocuklara kopyalanır ve çıktıyı çoğaltır.
- Kabuk, `fork` + `dup2` + `exec` + `wait` ile boru hattı kurar; boru EOF'u için bütün yazma uçlarının kapatılması zorunludur.
- IPC mekanizmaları borular, FIFO, paylaşılan bellek, sinyaller ve soketlerdir; sinyal işleyicilerinde yalnızca async-signal-safe işlevler kullanılır.
- Zamanlama algoritmaları ortalama bekleme, dönüş ve yanıt süresi arasında ödünleşim yapar; SJF ortalama beklemeyi en aza indirir, RR yanıtı iyileştirir, MLFQ ikisini dengelemeye çalışır.
- Linux CFS'ten EEVDF'e geçti (v6.6); gerçek zamanlı sınıflar ayrıcalık ister ve gecikme garantisi için kullanılır.
- Bağlam değişimi ve oluşturma maliyeti ölçülebilir: sistem çağrısı yüzlerce nanosaniye, süreç oluşturma yüzlerce mikrosaniye.
- İş parçacıkları adres uzayını paylaşır, yığını ve yazmaçları ayırır; paylaşılan değişkende yarış koşulu ve tanımsız davranış oluşabilir (Bölüm 27).
- CPython'da GIL CPU-bağlı işte iş parçacığı paralelliğini engeller; G/Ç-bağlı işte ise iş parçacıkları yeterlidir.

**Sonraki bölümde:** Bu bölümde iki iş parçacığının aynı değişkene yazınca neden kayıp güncelleme yaptığını gördük. Bölüm 27 — Senkronizasyon, bu sorunu çözmek için araçları tanıtacak: yarış koşullarının ayrıntılı analizi, karşılıklı dışlama (mutex), semafor, koşul değişkenleri (condvar), kilitlenme (deadlock) ve üç koşulu, atomik işlemleri ve bellek sıralamasını. Bu bölümdeki `race.c` programını Bölüm 27'de düzelteceğiz ve kayıp sayısının sıfıra indiğini ölçeceğiz.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Süreç ile iş parçacığı arasındaki farkı, paylaşılan kaynaklar ve bağlam değişimi maliyeti üzerinden anlat. Hangisini ne zaman seçersin?
2. `fork()` çağrısı neden iki kez döner ve ebeveyn ile çocuk bu iki dönüş değerini nasıl ayırt eder?
3. Copy-on-write nedir? Fork'tan hemen sonra bellek kullanımı neden düşük kalır, ama çocuk bir sayfa yazınca ne olur?
4. Bir pipe'ın okuma ucunun EOF görmesi için hangi koşul gerekir? Ebeveyn ve çocuk birbirine bağlıyken bir uç açık unutulursa ne olur?
5. Round Robin'de dilim uzunluğunu çok küçük seçmenin bedeli nedir? Bağlam değişimi maliyetini sayısal bir örnekle hesapla.
6. Yarış koşulu nedir ve `sayac++` gibi basit bir ifade neden bölünemez değildir? Derleyici optimizasyonu bu sorunu gizleyebilir mi?
7. CPython'da GIL varken CPU-bağlı bir işi iş parçacıklarıyla hızlandırmak neden başarısız olur? Hangi işte iş parçacıkları yine de yardımcı olur?
8. Bir sinyal işleyicisinde neden `printf` yerine `write` kullanılmalı? Async-signal-safe ne demek ve neden önemlidir?
:::
