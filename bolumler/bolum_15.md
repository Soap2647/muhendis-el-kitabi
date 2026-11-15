%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 15
%% baslik: Recursion & Backtracking

## Giriş: Kendi yardımcını çağırmak

Bir problemi çözerken "bunu daha küçük bir örnek için nasıl çözerdim?" diye sormak çoğu zaman en doğal yoldur. Bir dizinin toplamını almak için, ilk elemanı alıp kalanın toplamını aynı yöntemle hesaplamak; bir ağaçta bir düğümün altındaki yaprakları saymak için çocukların her birinde aynı sayımı yapmak; bir dosya sisteminde bir klasörün boyutunu bulmak için alt klasörlere girmek. Bu üç işin ortak yanı, fonksiyonun kendi kendini çağırmasıdır. Buna özyineleme (recursion) denir.

Özyineleme yalnızca bir programlama numarası değildir. Bölüm 12'de özyinelemeli bağıntılarla ve Master Teoremi ile karşılaştık; Bölüm 10'da ağaç gezinmelerini özyinelemeyle yazdık; Bölüm 8'de ise bu fonksiyon çağrılarının arkasında çağrı yığınının (call stack) durduğunu gördük. Bu bölümde bu üç fikri birleştiriyoruz: özyinelemeyi doğru yazmayı, ne kadar yığın harcadığını ölçmeyi ve bazı problemlerde bunun üstüne geri izleme (backtracking) ile sistematik bir arama kurmayı öğreniyoruz.

Geri izleme, mülakatta en sık karşına çıkan algoritma kalıplarından biridir. N-Queens, Sudoku, alt küme ve permütasyon sayımı, labirent çözme, bir ifadeye işlem yerleştirme gibi problemlerin hepsi aynı mantıkla çözülür: olası bir çözüm parçasını seç, ilerle, çıkmaza girersen geri al ve başka bir seçeneği dene. Bu yaklaşım, ne kadar akıllıca budanırsa o kadar hızlı çalışır; budamanın etkisini bu bölümde sayısal olarak ölçeceğiz.

Savunma ve gömülü sistemlerde de bu tekniklerin yeri var. Bir görev planlayıcının kısıtlı bir atama problemini (hangi görev hangi kaynağa, hangi sırayla) çözmesi, bir ayrıştırıcının bir komut dilini okuması ya da bir dosya sisteminin ağacını taraması, özyineleme ya da onu açık yığına çevirmiş bir yapıyla yapılır. Gömülü tarafta ise özyinelemenin en büyük riski vardır: yığın bellekte sınırlıdır ve derin özyineleme, bir mikrodenetleyicide sessiz bir çökmeye yol açabilir (Bölüm 43'te bare-metal yığın sınırlarına döneceğiz).

::: not
Bu bölümdeki C programları WSL içinde Ubuntu 24.04 üzerinde, gcc 13.3 ile `-std=c11 -Wall -Wextra` bayraklarıyla derlendi. Sanitizer denemeleri `-fsanitize=address,undefined` ile yapıldı. Python programları Python 3.12.10 ile çalıştırıldı. Verilen tüm sayılar bu programların çıktısıdır; bir sayıyı metinde görürsen onu üreten program aşağıda ya da bölümün dosyalarında var.
:::

## 15.1 Güven sıçraması: özyinelemeli düşünmenin üç sorusu

Özyinelemeli bir fonksiyon yazmanın en zor kısmı, fonksiyonun kendisini nasıl izleyeceğini düşünmeye başlamaktır. Bunun yerine şu zihinsel hamleyi yap: fonksiyonun daha küçük bir girdi için doğru çalıştığını **varsay**, sonra sadece bu varsayımı kullanarak büyük girdi için doğru sonucu nasıl üretebileceğini düşün. Buna güven sıçraması (leap of faith) diyoruz.

Bu sıçrama, Bölüm 14'teki döngü değişmezi düşüncesinin bir uzantısıdır, ama bir farkla. Döngüde değişmezi her turda kontrol ederiz. Özyinelemede değişmezi bir çağrı için kurarız: "`n - 1` için doğruysa, `n` için de doğrudur." Bu, matematikteki tümevarımla birebir aynıdır. Tümevarımda iki şey gösterilir: taban durumu (en küçük durum) doğrudur ve bir durumun doğruluğu bir öncekinin doğruluğundan çıkar. Özyinelemeli bir fonksiyonun doğruluğu da aynı iki parçaya dayanır.

Her özyinelemeli fonksiyon için şu üç soruyu sırayla sor:

1. **Taban durum:** Hangi girdi için cevap doğrudan, çağrı yapmadan bulunabilir? Bu, girdinin en küçük olduğu durumdur (ör. `n = 0` ya da boş dizi).
2. **Küçültme:** Her özyinelemeli çağrıda girdi taban durumuna doğru gerçekten küçülüyor mu? Eğer küçülmüyorsa çağrılar bitmez.
3. **Birleştirme:** Alt problemin sonucu elimizdeyken, büyük problemin cevabını nasıl kurarız? Bu adım, güven sıçramasının kullandığı tek yerdir.

Üç soruyu toplamaya uygulayalım. Aşağıdaki Python kodu, `n` sayısına kadar olan tam sayıların toplamını iki farklı biçimde hesaplar: `derin` her çağrıda sonucu geri dönüşte ekler, `topla` ise birikimi (accumulator) argüman olarak taşır.

```python
def derin(n):
    return 0 if n == 0 else 1 + derin(n - 1)


def topla(n, birikim=0):
    if n == 0:
        return birikim
    return topla(n - 1, birikim + n)
```

`derin` için üç soru şöyle cevaplanır. Taban durum `n == 0`, cevap `0`. Küçültme `n - 1`. Birleştirme: `1 + derin(n - 1)`; alt problemin sonucuna bir ekleniyor. Bu fonksiyon doğrudur, çünkü `derin(n)` aslında `n`'in kendisidir ve alt problemin doğruluğu bunu garanti eder.

Bu kodun önemli bir özelliği var: `derin` çağrısı döndükten sonra hâlâ iş yapıyor (`1 +` işlemi). Bu, çağrının bir **bekleme** gerektirdiği anlamına gelir; yığında her seviye için bir çerçeve kalır. `topla` ise yalnızca kendini çağırıp sonucu olduğu gibi döndürür; bu biçimi bölüm 15.4'te kuyruk özyinelemesi olarak ayrıca inceleyeceğiz. Şimdilik iki fonksiyonun da üç soruya cevap verdiğini ve doğru olduğunu kabul et.

::: ipucu
Özyinelemeli bir fonksiyon yazmadan önce taban durumu kâğıda yaz. Taban durumunu yanlış yazarsan, geri kalan bütün mantık yanlış bir dayanağa oturur. Bölüm 15.2'de taban durum hatalarının bir kataloğunu çıkaracağız.
:::

## 15.2 Çağrı yığını: çerçeve çerçeve bir özyineleme

Bölüm 8'de çağrı yığınını bir yığın veri yapısı olarak tanıttık: her fonksiyon çağrısı bir **çerçeve** (stack frame) iter; çerçeve parametreleri, yerel değişkenleri ve dönüş adresini tutar. Fonksiyon döndüğünde çerçeve yığından çıkar. Özyinelemede her çağrı yeni bir çerçeve demektir, dolayısıyla `n` derinliğindeki bir özyineleme, `n` çerçeveyi aynı anda bellekte tutar.

Bunu gözle görmek için `faktoriyel` fonksiyonuna her çağrıda kendi yerel değişkeninin adresini yazdıran bir sürüm ekledik. Bu adres, yığında çerçevenin yerini gösterir. Gerçek adresler çalışmadan çalışmaya değişir (adres alanı rastgeleleştirmesi yüzünden), bu yüzden program en dıştaki çerçeveye göre farkı, yani "taban'dan uzaklık" değerini yazar. Bu fark her çalıştırmada aynıdır.

```c
#include <stdint.h>
#include <stdio.h>

static uintptr_t taban = 0;

long faktoriyel(int n) {
    volatile int yerel = n;
    uintptr_t adres = (uintptr_t)&yerel;
    if (taban == 0)
        taban = adres;
    printf("n=%d  taban'dan uzaklik=%ld bayt\n", n,
           (long)(taban - adres));
    if (n <= 1)
        return 1;
    return n * faktoriyel(n - 1);
}

int main(void) {
    printf("faktoriyel(4) = %ld\n", faktoriyel(4));
    return 0;
}
```

Programı `-O0` ile, yani optimizasyonsuz derledik; böylece çerçeveler derleyicinin dokunmadığı hâlde kalır. Çıktı:

```term
$ gcc -O0 -Wall -Wextra -std=c11 cerceve.c -o cerceve
$ ./cerceve
n=4  taban'dan uzaklik=0 bayt
n=3  taban'dan uzaklik=80 bayt
n=2  taban'dan uzaklik=160 bayt
n=1  taban'dan uzaklik=240 bayt
faktoriyel(4) = 24
```

Her çağrı 80 bayt daha aşağı iniyor. Bu, `-O0` ile derlenen bu fonksiyonun çerçevesinin 80 bayt olduğu anlamına gelir: içinde yerel değişken `yerel`, kaydedilmiş yazmaçlar ve dönüş adresi vardır. Dönüş adresinin tam yerini objdump ile gösterebiliriz. Aşağıda, aynı binary'nin `faktoriyel` fonksiyonunun başlangıcı ve çağrı/dönüş satırları yer alıyor (listenin tamamı 47 satır; burada başlangıç ve `call`, `ret` içeren satırlar gösteriliyor):

```term
$ objdump -d cerceve
0000000000001169 <faktoriyel>:
    1169:       endbr64
    116d:       push   %rbp
    116e:       mov    %rsp,%rbp
    1171:       push   %rbx
    1172:       sub    $0x38,%rsp
    11cf:       call   1070 <printf@plt>
    11ef:       call   1169 <faktoriyel>
    1207:       call   1060 <__stack_chk_fail@plt>
    1210:       leave
    1211:       ret
```

`call 1169 <faktoriyel>` satırı, x86-64'te `call` komutunun dönüş adresini (bu komutun hemen sonrasındaki adresi) yığına **ittiğini** gösterir. `ret` komutu bu adresi yığından çekip programın sayacına yükler. Yani her özyineleme seviyesi, bir dönüş adresi ve yerel verilerle birlikte yığında bir yer tutar. ARM tabanlı mikrodenetleyicilerde (ör. STM32, Cortex-M) davranış farklıdır: `BL` komutu dönüş adresini LR yazmacına koyar, fonksiyon başka bir fonksiyon çağıracaksa LR'yi yığına kendisi iter (Bölüm 10'daki not). Bu yüzden "dönüş adresi yığında durur" cümlesini her mimaride doğru kabul etmek yerine, hedef mimariyi kontrol et.

Şekil 15.1, `faktoriyel(4)` çağrısının yığın üzerindeki durumunu gösterir. Her kutu bir çerçeve; sağdaki sayılar ölçtüğümüz ofsetler.

![Şekil 15.1: faktoriyel(4) çağrı yığını (-O0). Her çerçeve 80 bayt; en alttaki çerçeve (n = 1) yığın tepesidir. Ofsetler cerceve.c çıktısıdır.](gorseller/b15_cagri_yigini.png)

### Özyineleme neden bellek yer: stack overflow

Her çerçeve sabit boyutludur, ama derinlik büyüdükçe toplam çarpılır. Yığının boyutu işletim sisteminde sınırlıdır; WSL'de varsayılan 8 MB (`ulimit -s` çıktısı 8192 KB). Bu sınırı aşan özyineleme, işletim sisteminin yığın sayfasına erişimi reddetmesiyle çöker ve bu duruma **stack overflow** denir. Aşağıdaki program, her çerçevede yaklaşık 100 baytlık bir tampon taşıyan bir özyinelemeyi derinliğe göre çalıştırır:

```c
#include <stdio.h>
#include <stdlib.h>

/* Her çerçeve ~100 bayt yerel veri taşır. */
long derin(long n) {
    volatile char tampon[100];
    tampon[0] = (char)n;
    if (n == 0)
        return 0;
    return 1 + derin(n - 1) + tampon[0] * 0;
}

int main(int argc, char **argv) {
    if (argc != 2)
        return 1;
    long n = atol(argv[1]);
    printf("derin(%ld) = %ld\n", n, derin(n));
    return 0;
}
```

```term
$ gcc -O0 -Wall -Wextra -std=c11 derin.c -o derin_O0
$ ./derin_O0 10000
derin(10000) = 10000
cikis=0
$ ./derin_O0 100000
cikis=139
```

`-O0` ile derlenmiş `derin` her çerçevede 128 bayt yerel alan ayırır (objdump'taki `add $0xffffffffffffff80,%rsp` komutu bunu gösterir); buna 8 bayt dönüş adresi ve 8 bayt kaydedilmiş `rbp` eklenir, çerçeve başına 144 bayt eder. `10000` derinlik yaklaşık 1,4 MB yığın tutar ve çalışır. `100000` derinlik ise yaklaşık 14 MB ister; `-O0` ile derlenmiş program bunu kaldıramaz ve segmentation fault ile sonlanır (çıkış kodu 139 = 128 + SIGSEGV'in 11 numarası). Bu sayıların tam sınırı derleyiciye, bayraklara ve mimariye göre değişir; önemli olan, sınırın var olduğunu ve bu sınırın bir programın "çalışıyor" görünmesini bile bozabileceğini görmektir.

::: dikkat
Bu bölümdeki C kodlarını WSL'de derledik. Windows'ta `long` tipi 4 bayttır (LLP64 modeli); Linux'ta 64-bit'te 8 bayttır. Bu yüzden bu bölümde `long` ile yazdığımız toplamlar (ör. 5·10^13) Windows'ta taşar. Aynı kodu Windows'ta derlersen sonuçlar değişir: `long` yerine `long long` ya da `int64_t` kullan.
:::

### Taban durum hataları kataloğu

Yığın sınırı, özyinelemeli kodun en görünür sonucudur. Asıl sık görülen hata ise taban durumunun eksik ya da yanlış olmasıdır. Aşağıdaki program, taban durumu hiç olmayan bir `faktoriyel` içerir. Kodu hem `-O0` hem `-O2` ile derleyip ASan ile de denedik:

```c
#include <stdio.h>
#include <stdlib.h>

/* HATA: taban durumu yok. Her çağrı kendini çağırır. */
long faktoriyel(int n) {
    return n * faktoriyel(n - 1);
}

int main(int argc, char **argv) {
    if (argc != 2)
        return 1;
    printf("%ld\n", faktoriyel(atoi(argv[1])));
    return 0;
}
```

Derleme ve çalıştırma sonuçları üç farklı davranış gösterdi. Önce `-Wall` ile derlemenin uyarısını gör:

```term
$ gcc -O0 -Wall -Wextra -std=c11 tabansiz.c -o tab_O0
tabansiz.c:5:6: warning: infinite recursion detected
$ ./tab_O0 5
cikis=139
$ gcc -O2 -Wall -Wextra -std=c11 tabansiz.c -o tab_O2
$ timeout 3 ./tab_O2 5
cikis=124
$ objdump -d tab_O2
0000000000001180 <faktoriyel>:
    1180:       endbr64
    1184:       nopl   0x0(%rax)
    1188:       jmp    1188 <faktoriyel+0x8>
```

Üç sonucu dikkatle oku. `-O0` ile derlenen program yığın sınırını aştı ve segmentation fault ile çöktü (139). `-O2` ile derlenen program ise çökmedi, 3 saniye sonunda `timeout` tarafından sonlandırıldı (124). Objdump, bunun nedenini gösteriyor: derleyici `faktoriyel` fonksiyonunu tek bir `jmp` komutuna indirgemiş; fonksiyon kendi kendine dönen sonsuz bir döngü hâline gelmiş ve yığın hiç büyümüyor. Yani "taban durum yok" hatası her zaman çökmeye yol açmaz; bazen sessiz bir takılmaya dönüşür. C standardı bu durumun ne olacağını tanımlamaz; derleyicinin verdiği kod ise bu tür özyinelemeyi döngüye çevirmiştir. Ne olduğunu bilmeden "çöker" varsayımına güvenme.

Üçüncü sonuç, ASan'ın bu durumu yakalayışıdır. Sanitizer'ı yığın taşmasını tespit edecek şekilde derlediğimizde ilk satırlar şöyle olur:

```term
$ gcc -O0 -g -fsanitize=address,undefined -std=c11 tabansiz.c -o tab_asan
$ ./tab_asan 5
==PID==ERROR: AddressSanitizer: stack-overflow on address 0xADRES
    #0 0xADRES in faktoriyel tabansiz.c:5
    #1 0xADRES in faktoriyel tabansiz.c:6
    #2 0xADRES in faktoriyel tabansiz.c:6
```

Adresler ve süreç kimliği her çalıştırmada değişir; bu yüzden onları `0xADRES` ve `==PID==` ile değiştirdik, dosya yolunu da kısalttık. Hata türü (`stack-overflow`) ve hatanın yapıldığı satır (`tabansiz.c:6`) aynıdır.

Taban durum ve çağrı hatalarını bir tabloda topladık. Özyinelemeli kod yazarken bu tabloyu bir kontrol listesi gibi kullan:

| Hata | Belirti | Önlem |
|---|---|---|
| Taban durum yok | `-O0`'da yığın taşması (139); `-O2`'de sonsuz döngü (124); ASan'da `stack-overflow` | Her dalda bir çıkış yolu olduğunu kontrol et |
| Yanlış taban (`n == 1`, oysa girdi `0` olabilir) | `faktoriyel(0)` sonsuz gider | Taban durumunu girdi alanının en küçük değerine göre yaz |
| Küçülmeyen çağrı (`f(n)` ya da `f(n+1)` çağrısı) | Sonsuz özyineleme | Her çağrıda argüman taban durumuna doğru yaklaşmalı |
| Geçersiz girdi (negatif `n`) | Taban hiç ulaşılmaz | Girdiyi çağrıdan önce doğrula |
| Birleştirme hatası | Hata vermeden yanlış sonuç | Küçük girdide sonucu elle hesapla ve karşılaştır |

Python'da durum biraz farklıdır: sınır sistemin yığını değil, Python'un kendi sayacıdır. `sys.getrecursionlimit()` varsayılanda 1000'dir ve aşıldığında `RecursionError` fırlatılır. Bu sayaç, yığın bellek sınırından önce devreye girer; yani Python'da sonsuz özyineleme genellikle sessizce çökmez, bir hata mesajıyla durur. Bu davranışı Bölüm 15.4'te kuyruk özyinelemesiyle birlikte ölçeceğiz.

## 15.3 Doğrusal ve ağaç özyineleme: tekrar eden iş

Özyinelemeli çağrıların yapısına göre iki temel tür vardır. **Doğrusal özyineleme**de her çağrı kendini tek kez çağırır; `derin`, `topla` ve `faktoriyel` böyledir. Çağrı zinciri bir çizgi gibidir: `n` çağrı, `n` derinlik, `n` çerçeve. **Ağaç özyinelemesi**de bir çağrı birden fazla kez kendini çağırır. Bunun en bilinen örneği Fibonacci sayılarıdır:

`fib(0) = 0`, `fib(1) = 1`, `fib(n) = fib(n - 1) + fib(n - 2)`

Taban durum iki değerdir (`n = 0` ve `n = 1`); ikisini de yazmayı unutmamak gerekir. Asıl soru ise çağrı sayısıdır. Aşağıdaki program, `fib` çağrılarını sayar ve sonucu birkaç `n` için yazar:

```python
import sys

cagri = 0


def fib(n):
    global cagri
    cagri += 1
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


if __name__ == "__main__":
    for n in (5, 10, 20, 25):
        cagri = 0
        sonuc = fib(n)
        print("fib(%2d) = %6d  cagri = %8d" % (n, sonuc, cagri))
    cagri = 0
    fib(30)
    print("fib(30) cagri =", cagri)
```

```term
$ python py_fib.py
fib( 5) =      5  cagri =       15
fib(10) =     55  cagri =      177
fib(20) =   6765  cagri =    21891
fib(25) =  75025  cagri =   242785
fib(30) cagri = 2692537
```

Çağrı sayıları, `fib(n)` için `2·F(n+1) - 1` formülüyle eşleşir (`F` Fibonacci sayısını gösterir: `F(6) = 8`, `2·8 - 1 = 15`). Formülü kullanarak `n = 30` için çağrı sayısını (2 692 537) önceden hesaplayabilirsin; `n = 5` için 15 olan bu sayı, `n = 30`'da milyonlara çıkar. Çağrı sayısı üstel olarak büyür; çünkü her çağrı iki yeni çağrı üretir ve bunların çoğu aynı işi tekrar eder.

Şekil 15.2, `fib(5)` çağrısının ağacını gösterir. Sarı düğümler, aynı argümanla birden fazla kez çağrılan alt problemlerdir: `fib(3)` iki kez, `fib(2)` üç kez, `fib(1)` beş kez, `fib(0)` üç kez.

![Şekil 15.2: fib(5) özyineleme ağacı. Sarı düğümler tekrar eden çağrılardır; toplam çağrı sayısı 15'tir.](gorseller/b15_fib_agac.png)

Bu tekrar, özyinelemenin en önemli zayıflığıdır. Ağacın kendisi değil, ağaçtaki tekrar eden iş sorundur: aynı `fib(3)` değeri üç kez hesaplanıyor, her hesaplama kendi alt ağacını yeniden kuruyor. Bölüm 12.9'da gördüğümüz özyinelemeli bağıntı biçimini düşün: `T(n) = T(n-1) + T(n-2) + 1` bir Master Teoremi biçimi değildir, çünkü bölme yoktur; sonuç üstel büyümedir. Bu tekrarı ortadan kaldırmanın yolu, her alt problemin sonucunu bir kez hesaplayıp saklamaktır. Bu fikir Dinamik Programlama'nın (Bölüm 16) başlangıcıdır; burada yalnızca tekrarın ne kadar büyük olduğunu ölçüyoruz.

::: baglanti
Bu bölümdeki `fib` ağacı, Bölüm 16'da "tekrar eden alt problemler" olarak adlandıracağımız durumun en küçük örneğidir. Çözüm yöntemini (memoization ve tabulation) Bölüm 16'da göreceğiz.
:::

## 15.4 Kuyruk özyinelemesi ve derleyicinin payı

Bir çağrının **kuyruk pozisyonunda** olduğunu söyleriz, eğer fonksiyonun yaptığı son iş o çağrının sonucunu olduğu gibi döndürmekse. `topla_kuyruk` böyledir: `topla_kuyruk(n - 1, birikim + n)` çağrısının sonucu doğrudan döndürülür, hiçbir şey eklenmez. `topla_derin` ise `n + topla_derin(n - 1)` yazar; çağrı bittikten sonra `n` eklenmek zorundadır, dolayısıyla kuyrukta değildir.

Kuyruk özyinelemesinin pratik önemi şudur: çağrı bitince, çağıran fonksiyonun yerel verilerine artık ihtiyaç yoktur. Derleyici bu durumda çağrıyı bir **atlama** (jump) ile değiştirebilir; yeni bir çerçeve açmaya gerek kalmaz ve özyineleme bir döngüye dönüşür. Buna kuyruk çağrısı optimizasyonu (tail-call optimization, TCO) denir.

Bu optimizasyonun uygulanması derleyiciye ve ayarlara bağlıdır. Önce Python'a bakalım: Python **kuyruk çağrısı optimizasyonu yapmaz**. `sys.getrecursionlimit()` değeri 1000 olduğundan, `topla` fonksiyonunu 5000 derinlikte çalıştırmak `RecursionError` ile durur; kod kuyruk biçiminde olmasına rağmen. Bunu bölüm başındaki `py_ozyineleme.py` programıyla ölçtük:

```term
$ python py_ozyineleme.py
getrecursionlimit = 1000
en buyuk derin(n) = 997
topla(500) = 125250
topla(5000): RecursionError: maximum recursion depth exceeded
```

Çıktıdaki `en büyük derin(n)` değeri, `derin` fonksiyonunun Python'un çağrı sayacına göre çalışabildiği en büyük `n`'dir. Bu sayı, hangi çağrı katmanında ölçüldüğüne bağlıdır: betik içinde yazdığımız yardımcı fonksiyonlar da sayaçta yer kaplar. Değer 997'dir; `topla(500)` ise çalışır. Bu sonuçlar, Python'da derin özyinelemenin neden ayrı bir sınırla karşılaştığını gösterir.

C tarafına dönelim. Aşağıdaki program aynı toplamı iki biçimde hesaplar: `topla_kuyruk` (kuyruk biçimi) ve `topla_derin` (kuyruk değil). Programı `-O0` ve `-O2` ile derledik:

```c
#include <stdio.h>
#include <stdlib.h>

/* Kuyruk özyinelemesi: çağrı, fonksiyonun son işi. */
long topla_kuyruk(long n, long birikim) {
    if (n == 0)
        return birikim;
    return topla_kuyruk(n - 1, birikim + n);
}

/* Kuyruk değil: 1 + ... sonucu çağrıdan sonra eklenir. */
long topla_derin(long n) {
    if (n == 0)
        return 0;
    return n + topla_derin(n - 1);
}

int main(int argc, char **argv) {
    if (argc != 3)
        return 1;
    long n = atol(argv[2]);
    if (argv[1][0] == 'k')
        printf("kuyruk(%ld) = %ld\n", n, topla_kuyruk(n, 0));
    else
        printf("derin(%ld) = %ld\n", n, topla_derin(n));
    return 0;
}
```

```term
$ gcc -O0 -Wall -Wextra -std=c11 kuyruk.c -o kuyruk_O0
$ ./kuyruk_O0 k 100000
kuyruk(100000) = 5000050000
cikis=0
$ ./kuyruk_O0 k 10000000
cikis=139
$ gcc -O2 -Wall -Wextra -std=c11 kuyruk.c -o kuyruk_O2
$ ./kuyruk_O2 k 10000000
kuyruk(10000000) = 50000005000000
cikis=0
$ ./kuyruk_O2 d 10000000
derin(10000000) = 50000005000000
cikis=0
```

`-O0` ile derlenmiş program, kuyruk biçimli bile olsa `10^7` derinlikte yığını aşıp çöktü (139). `-O2` ile derlenen program ise hem kuyruk biçimini hem de kuyruk olmayan `topla_derin` biçimini `10^7` derinlikte çalıştırdı. Bu ikinci sonuç dikkat çekicidir: `n + f(n - 1)` biçimi kuyruk değildir, ama gcc bunu da döngüye çevirdi (toplama işlemini bir birikim değişkenine taşıyarak). Objdump, derleyicinin bunu gerçekten yaptığını gösteriyor:

```term
$ objdump -d kuyruk_O2
0000000000001220 <topla_kuyruk>:
    1220:       endbr64
    1224:       mov    %rsi,%rax
    1227:       test   %rdi,%rdi
    122a:       je     1253 <topla_kuyruk+0x33>
    122c:       lea    -0x1(%rdi),%rdx
    1230:       test   $0x1,%dil
    1234:       je     1248 <topla_kuyruk+0x28>
    1236:       add    %rdi,%rax
    1239:       mov    %rdx,%rdi
    123c:       test   %rdx,%rdx
    123f:       je     1254 <topla_kuyruk+0x34>
    1241:       nopl   0x0(%rax)
    1248:       lea    -0x1(%rax,%rdi,2),%rax
    124d:       sub    $0x2,%rdi
    1251:       jne    1248 <topla_kuyruk+0x28>
    1253:       ret
    1254:       ret
    1255:       data16 cs nopw 0x0(%rax,%rax,1)
```

Fonksiyonun içinde `call` yok; `jne` komutu başa dönerek bir döngü kuruyor. Bu, `-O2`'de derleyicinin özyinelemeyi tamamen ortadan kaldırdığı anlamına gelir.

::: dikkat
Derleyici optimizasyonuna güvenme. Aynı kod `-O0`'da çöker, `-O2`'de çalışır; Python'da hiç çalışmaz; başka bir derleyicide ya da başka bir fonksiyon biçiminde farklı davranabilir. Güvenilir yol, özyinelemeyi açıkça bir döngüye yazmaktır. Mülakatta "kuyruk özyinelemesi yazdım, derleyici optimize eder" demek, bu bilginin yalnızca bir kısmıdır.
:::

Özet olarak: kuyruk özyinelemesi, döngüye dönüştürülmesi kolay bir özyinelemedir. Bu dönüşümü elle yapmayı ise bölüm 15.5'te, yığını açıkça yönettiğimiz bir örnekle göreceğiz.

## 15.5 Özyinelemeden yinelemeye: açık yığınla dönüşüm

Özyinelemenin yığını, yapısı gereği dildeki çağrı mekanizmasına bağlıdır. Yığını kendimiz yönetirsek, hem sınırı hem de davranışı kontrol ederiz. Dönüşüm üç adımdan oluşur:

1. Her çağrının argümanlarını ve kalan işini bir **çerçeve** olarak temsil et.
2. Özyinelemeli çağrı yerine çerçeveyi kendi yığınımıza it.
3. Yığın boşalana kadar bir döngü çalıştır: çerçeveyi çek, işle, gerekiyorsa yeni çerçeveler it.

Bu dönüşümü bir **flood fill** (sel doldurma) problemi üzerinde yapıyoruz. Bir ızgarada başlangıç hücresinden erişilebilen tüm boş hücreleri doldurmak, bir resim düzenleyicideki "kovayla doldur" aracının ya da bir oyundaki bölge tespitinin temelidir. Ayrıca her hücreden dört yöne (yukarı, aşağı, sağ, sol) dallanan bir gezinmedir; yani her hücre bir ağaç düğümü gibi davranır ve derinlik, en kötü durumda hücre sayısı kadar olabilir.

Önce özyinelemeli sürüm:

```c
#include <stdio.h>
#include <stdlib.h>

/* 0 = bos, 1 = duvar, 2 = doldurulmus. Izgara n x n. */
static int n;
static unsigned char *izgara;
static long doldu = 0, derinlik = 0, en_derin = 0;

/* Ozyinelemeli flood fill: her cagri bir hucre. */
static void doldur(int r, int c) {
    if (r < 0 || c < 0 || r >= n || c >= n)
        return;
    if (izgara[r * n + c] != 0)
        return;
    izgara[r * n + c] = 2;
    doldu++;
    derinlik++;
    if (derinlik > en_derin)
        en_derin = derinlik;
    doldur(r + 1, c);
    doldur(r - 1, c);
    doldur(r, c + 1);
    doldur(r, c - 1);
    derinlik--;
}
```

Derinlik, gezinme sırasında yığını ne kadar büyüttüğümüzü ölçer. Açık ızgarada, `(0, 0)` hücresinden aşağı doğru ilerleyen bir yol neredeyse tüm hücreleri içerir; yani en kötü durumda derinlik `n²` olur. Bu yüzden `n = 500` için derinlik 250 000'dir. Aynı problemi yığınla yazan sürüm şöyle:

```c

/* Yigin tabanli surum: cagri yigini yerine kendi yiginimiz.
   Hucre itilirken isaretlenir; boylece her hucre en fazla
   bir kez yiginda olur ve yigin n*n cifti asmaz. */
static void doldur_yigin(int r0, int c0) {
    int *yigin = malloc((size_t)n * n * 2 * sizeof *yigin);
    if (yigin == NULL)
        return;
    int dr[4] = {1, -1, 0, 0};
    int dc[4] = {0, 0, 1, -1};
    long tepe = 0;
    izgara[r0 * n + c0] = 2;
    doldu++;
    yigin[tepe++] = r0;
    yigin[tepe++] = c0;
    while (tepe > 0) {
        int c = yigin[--tepe];
        int r = yigin[--tepe];
        for (int k = 0; k < 4; k++) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= n || nc >= n)
                continue;
            if (izgara[nr * n + nc] != 0)
                continue;
            izgara[nr * n + nc] = 2;
            doldu++;
            yigin[tepe++] = nr;
            yigin[tepe++] = nc;
        }
    }
    free(yigin);
}
```

Burada çağrı yığını yoktur; hücre koordinatları `yigin` dizisinde tutulur. Her hücreyi **itmeden önce** işaretliyoruz; böylece aynı hücre yığında birden çok kez bulunmaz ve yığın en fazla `n²` hücre taşır. Bu, tam olarak 2·n² `int` yer demektir. Ana program şöyle:

```c

int main(int argc, char **argv) {
    if (argc != 3)
        return 1;
    int yigin_modu = argv[1][0] == 'y';
    n = atoi(argv[2]);
    if (n <= 0) {
        printf("n=%d doldu=0\n", n);
        return 0;
    }
    izgara = calloc((size_t)n * n, 1);
    if (izgara == NULL)
        return 1;
    if (yigin_modu) {
        doldur_yigin(0, 0);
        printf("n=%d doldu=%ld\n", n, doldu);
    } else {
        doldur(0, 0);
        printf("n=%d doldu=%ld en_derin=%ld\n", n, doldu, en_derin);
    }
    free(izgara);
    return 0;
}
```

Çalıştırdığımızda iki sürüm aynı sonucu verir; sınır değerlerde davranışları farklıdır:

```term
$ gcc -O0 -Wall -Wextra -std=c11 sel.c -o sel_O0
$ gcc -O2 -Wall -Wextra -std=c11 sel.c -o sel_O2
$ ./sel_O0 r 500
n=500 doldu=250000 en_derin=250000
cikis=0
$ ./sel_O0 r 600
cikis=139
$ ./sel_O2 r 1000
cikis=139
$ ./sel_O2 y 1000
n=1000 doldu=1000000
cikis=0
```

Ölçüm, sınırın yerini gösterir. `-O0` ile özyinelemeli sürüm `n = 500`'de (derinlik 250 000) çalışır, `n = 600`'de çöker. `-O2` ile derlenen özyinelemeli sürüm de `n = 1000`'de çöker; bu fonksiyonda derleyici özyinelemeyi döngüye çevirmedi. Yığın sürümü ise `n = 1000` için, yani bir milyon hücre için sorunsuz çalışır.

Yığın sürümünün belleği `n²` ile büyür, ama çağrı yığınının dışında. Bu, çağrı yığınının sabit ve küçük (8 MB) olmasından farklı olarak, bu yapıyı kendi belleğimizde ve kontrollü biçimde büyütebileceğimizi gösterir.

Sanitizer ile sınır durumlarını da denedik. Boş ızgara (`n = 0`) ve tek hücre (`n = 1`) için iki sürüm de doğru sonuç verir; ASan bellek hatası raporlamaz:

```term
$ gcc -O1 -g -fsanitize=address,undefined -std=c11 sel.c -o sel_asan
$ ./sel_asan y 0
n=0 doldu=0
cikis=0
$ ./sel_asan r 1
n=1 doldu=1 en_derin=1
cikis=0
```

Burada iki hatayı da paylaşmak gerekiyor, çünkü ikisi de sınır durumlarından çıktı. Yığın sürümünün ilk yazımında hücreyi yığından **çıkarırken** işaretliyorduk. Aynı hücre yığında birden çok kez bulunabildiği için yığın `n²` sınırını aşıyor ve program `n = 100` gibi küçük bir ızgarada bile çöküyordu (çıkış kodu 139). Düzeltme, işaretlemeyi itme anına taşımaktı. İkinci yazımda ise `n = 0` için ızgara sıfır boyutluydu, ama kod yine de ilk hücreye yazıyordu; ASan bunu `heap-buffer-overflow` olarak raporladı. Çözüm, `n <= 0` için erken dönüş eklemekti. Sınır durumlarını test etmeden bir sürümü bitmiş saymak yanıltıcıdır.

::: ipucu
Özyinelemeyi yığına çevirirken, özyinelemeli sürümü referans olarak tut. İki sürümün her girdi için aynı sonucu verdiğini küçük ızgaralarda (ör. rastgele 5×5 duvarlı ızgaralarda) karşılaştır. Dönüşüm hatalarının çoğu böyle yakalanır.
:::

## 15.6 Geri izleme şablonu: seç, keşfet, geri al

Özyinelemenin en güçlü kullanımı, bir **arama** yapmaktır. Birçok problemde çözüm, bir dizi karardan oluşur: her adımda bir seçenek seçersin. Tüm kararların oluşturduğu ağaca **durum uzayı ağacı** diyoruz. Kökten başlayıp yaprağa inen her yol, bir olası çözümü temsil eder; yapraklar ya çözümdür ya da çıkmazdır.

Geri izleme, bu ağacı derinlemesine (DFS) gezen bir özyinelemedir ve her düğümde aynı üç adımı tekrarlar:

1. **Seç:** Bir aday seç ve kısmi çözüme ekle.
2. **Keşfet:** Özyinelemeli olarak bir sonraki karara geç.
3. **Geri al:** Dönüşte seçimi kısmi çözümden çıkar; böylece aynı yapı, bir sonraki aday için temiz kalır.

Şekil 15.3 bu döngüyü ve kesme noktalarını gösterir. Kutular her düğümde yapılan işi, alt kutular ise geri izleme kararlarını özetler.

![Şekil 15.3: Geri izleme döngüsü. Her düzeyde seç, keşfet, geri al; alt kutular çözüm, budama ve aday kalmaması durumlarını gösterir.](gorseller/b15_geri_izleme_dongu.png)

Geri al adımı, geri izlemeyi "kör deneme"den ayıran şeydir. Seçimi geri almazsan, bir dal için eklediğin eleman diğer dallara sızar ve sonuçlar bozulur. Bu yüzden her `ekle` çağrısının karşısında bir `çıkar` çağrısı olmalıdır; bu, Bölüm 8'deki yığın mantığının aynısıdır: son giren ilk çıkar.

### Alt kümeler

Bir kümenin tüm alt kümelerini bulmak için her eleman için iki karar vardır: seçmek ya da seçmemek. Yani `n` elemanlı bir kümenin `2^n` alt kümesi vardır ve durum uzayı ağacı ikili bir ağaçtır. Aşağıdaki program, bu ağacı `dfs(i)` ile gezer; `i`, bu düzeydeki elemanın indeksidir:

```python
"""Geri izleme (backtracking): alt kumeler, permutasyonlar,
kombinasyonlar ve kombinasyon toplami."""


def altkumeler(a):
    sonuc = []
    secili = []

    def dfs(i):
        if i == len(a):
            sonuc.append(secili[:])
            return
        dfs(i + 1)              # a[i] secilmez
        secili.append(a[i])     # sec
        dfs(i + 1)              # kesfet
        secili.pop()            # geri al

    dfs(0)
    return sonuc

```

Şekil 15.4, `{1, 2, 3}` için durum uzayı ağacını gösterir. Her düzey bir elemanla ilgili kararı temsil eder; yapraklar tüm alt kümelerdir.

![Şekil 15.4: {1, 2, 3} için alt küme durum uzayı ağacı. Yapraklar 8 alt kümedir (2^3).](gorseller/b15_alt_kume_agac.png)

Boş küme de bir alt kümedir ve kodda `dfs(0)` ile `i == len(a)` durumunda ilk kez eklenir. Bu, taban durumunun doğru seçildiğinin bir göstergesidir.

### Tekrarsız permütasyonlar

Bir kümenin permütasyonlarında her eleman tam bir kez kullanılır ve sıra önemlidir. Kök düğümden her seviyede henüz kullanılmamış her eleman bir dal olur. Eleman tekrarı varsa işler karışır: `[1, 1, 2]` için iki `1`'in her ikisini de seçersek aynı permütasyonu iki kez üretiriz. Çözüm, elemanları sıralamak ve bir kuralla tekrarlı dalı atlamaktır: aynı değerin önceki kopyası bu dalda kullanılmadıysa, bu kopyayı seçme.

```python
def tekrarsiz_permutasyonlar(a):
    a = sorted(a)
    n = len(a)
    kullanildi = [False] * n
    yol = []
    sonuc = []

    def dfs():
        if len(yol) == n:
            sonuc.append(yol[:])
            return
        for i in range(n):
            if kullanildi[i]:
                continue
            # Ayni deger, onceki kopyasi bu dalda
            # kullanilmadiysa atlanir: tekrar yok.
            if i > 0 and a[i] == a[i - 1] and not kullanildi[i - 1]:
                continue
            kullanildi[i] = True
            yol.append(a[i])
            dfs()
            yol.pop()
            kullanildi[i] = False

    dfs()
    return sonuc
```

Şekil 15.5 `[1, 1, 2]` için ağacı gösterir. Kesik kutu, tekrar kuralı yüzünden atlanan dalı işaretler; üç yaprak üç farklı permütasyondur. Bu kural doğru olduğunu programda `itertools.permutations` ile karşılaştırarak test ettik; küçük rastgele dizilerde kümeler birebir eşleşti.

![Şekil 15.5: [1, 1, 2] için tekrarsız permütasyon ağacı. Kesik kutu, tekrar nedeniyle atlanan dalı gösterir.](gorseller/b15_permutasyon_agac.png)

Permütasyon sayısı `n!` ile büyür: `n = 10` için 3,6 milyon, `n = 12` için 479 milyon. Bu yüzden bir permütasyon problemini çözerken önce çıktının boyutunu hesapla; ağacın tamamını dolaşmak zorunda kalıp kalmayacağını buna göre anla.

### Kombinasyonlar

Kombinasyon, sırası önemsiz seçimdir: `n` elemandan `k` tanesini seçmek. Ağacı bir **başlangıç indeksi** ile daraltırız: bir seçim yaptıktan sonra yalnızca daha büyük indeksli elemanlara bakarız. Böylece `[1, 2]` ile `[2, 1]` aynı dal olmaz, ikinci kez üretilmez.

```python
def kombinasyonlar(n, k):
    sonuc = []
    yol = []

    def dfs(baslangic):
        if len(yol) == k:
            sonuc.append(yol[:])
            return
        for v in range(baslangic, n + 1):
            yol.append(v)
            dfs(v + 1)
            yol.pop()

    dfs(1)
    return sonuc
```

Kombinasyon toplamında, yani bir aday listesinden toplamı hedefe eşit olan (tekrara izinli) seçimleri bulmakta, aynı yapı budama ile birleşir. Bu ölçümü aşağıda, budama bölümünde yorumluyoruz.

## 15.7 Budama ve etkisinin ölçümü

Durum uzayı ağacının tamamını dolaşmak çoğu zaman gereksizdir. **Budama** (pruning), bir dalın hiçbir çözüm üretemeyeceğini erken fark edip o dalı hiç açmamaktır. Budamanın gücü, durum uzayını ne kadar erken kestiğine bağlıdır.

Kombinasyon toplamında budama kuralı basit: aday listesini sıraladığımız için, bir aday kalan hedeften büyükse, sonrakiler de büyüktür; döngüyü o noktada kır. Aşağıdaki kod, budamalı ve budamasız sürümü aynı parametrelerle çalıştırır ve düğüm sayısını sayar. Düğüm sayısı, her `dfs` çağrısının sayısıdır: yani yapılan iş miktarının ölçüsüdür.

```python
def kombinasyon_toplami(adaylar, hedef, buda=True):
    a = sorted(adaylar)
    sonuc = []
    yol = []
    dugum = [0]

    def dfs(i, kalan):
        dugum[0] += 1
        if kalan == 0:
            sonuc.append(yol[:])
            return
        if kalan < 0:
            return
        for j in range(i, len(a)):
            if buda and a[j] > kalan:
                break               # sirali: sonrakiler de buyuk
            yol.append(a[j])
            dfs(j, kalan - a[j])    # ayni aday tekrar secilebilir
            yol.pop()

    dfs(0, hedef)
    return sonuc, dugum[0]
```

Budamasız sürümde döngü bütün adayları dener ve negatif kalanla çağrılan dallar hemen geri döner; bu dalların her biri yine de bir düğüm sayılır. Ana program bu ikisini aynı girdide karşılaştırır:

```python
if __name__ == "__main__":
    print("altkumeler([1, 2, 3]):")
    for s in altkumeler([1, 2, 3]):
        print(" ", s)
    print("tekrarsiz([1, 1, 2]):",
          tekrarsiz_permutasyonlar([1, 1, 2]))
    print("kombinasyonlar(4, 2):", kombinasyonlar(4, 2))
    print("toplam([2, 3, 6, 7], 7):",
          kombinasyon_toplami([2, 3, 6, 7], 7)[0])
    aday = [2, 3, 5, 7, 11, 13, 17, 19]
    for buda in (False, True):
        sonuc, dugum = kombinasyon_toplami(aday, 40, buda)
        print("budama=%-5s cozum=%4d dugum=%6d"
              % (buda, len(sonuc), dugum))
```

```term
$ python geri_izleme.py
altkumeler([1, 2, 3]):
  []
  [3]
  [2]
  [2, 3]
  [1]
  [1, 3]
  [1, 2]
  [1, 2, 3]
tekrarsiz([1, 1, 2]): [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
kombinasyonlar(4, 2): [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]
toplam([2, 3, 6, 7], 7): [[2, 2, 3], [7]]
budama=False cozum= 274 dugum=  9445
budama=True  cozum= 274 dugum=  2551
```

Çıktı üç şeyi gösteriyor. Alt kümeler, permütasyonlar ve kombinasyonlar beklenen sırayla üretildi. Kombinasyon toplamında `[2, 3, 6, 7]` ve hedef `7` için iki çözüm çıktı (`[2, 2, 3]` ve `[7]`). Son iki satır ise budamanın etkisidir: aynı 274 çözüm, budamalı sürümde 2551 düğümde, budamasız sürümde 9445 düğümde bulundu. Yani budama, bu girdide düğüm sayısını yaklaşık 3,7 kat azalttı. Oran girdiye bağlıdır; budamanın etkisini her problemde ayrıca ölçmek gerekir.

Geri izlemede budamanın en görünür örneği N-Queens problemidir. Şekil 15.6, `N = 4` için budanmış ağacı gösterir. Kesik çizgilerle işaretli `x` sembolleri, o satırda güvensiz olduğu için hiç ziyaret edilmeyen sütunlardır. Ağacın ziyaret edilen düğümleri 17 tanedir; aynı problemin budamasız (yalnızca sütun çakışmasını engelleyen) sürümü ise 65 düğüm üretir.

![Şekil 15.6: N = 4 için budanmış N-Queens ağacı. Kesik çizgiler ve x işaretleri budanan sütunlardır; ziyaret edilen düğüm sayısı 17'dir.](gorseller/b15_budama_agac.png)

Budamanın N arttıkça ne kadar önem kazandığı Bölüm 15.8'de N-Queens ölçümleriyle birlikte görülecek.

::: dikkat
Budama, doğruluğu bozmamalıdır. Her budama kuralını, budanan dalda gerçekten çözüm olmadığını kanıtlayarak yaz. Kombinasyon toplamında kural, sıralı aday listesine dayanır: liste sıralı değilse `break` yanlış sonuç üretir. Doğruluğunu brute force ile karşılaştırarak doğrula.
:::

## 15.8 N-Queens: sekiz vezirin çözümü

N-Queens problemi şöyledir: `N × N` bir tahtaya `N` vezir öyle yerleştir ki hiçbir ikisi aynı satırda, sütunda ya da köşegende olmasın. Vezirler satır satır yerleştirilir; bu yüzden her satır için bir sütun seçmek yeterlidir ve durum uzayı, satır başına bir karar olarak yazılır.

Python sürümü her satır için sütunları dener ve `guvenli` ile önceki vezirlerle çakışmayı kontrol eder. Kontrol, sütun ve iki köşegen için yapılır: satır farkı, sütun farkının mutlak değerine eşitse aynı köşegendedirler.

```python
"""N vezir: budamali ve budamasiz geri izleme."""


def guvenli(yerler, satir, sutun):
    for r, c in enumerate(yerler):
        if c == sutun or abs(c - sutun) == satir - r:
            return False
    return True


def cozumler(n):
    sonuc = []
    yerler = []

    def dfs(satir):
        if satir == n:
            sonuc.append(yerler[:])
            return
        for s in range(n):
            if guvenli(yerler, satir, s):
                yerler.append(s)
                dfs(satir + 1)
                yerler.pop()

    dfs(0)
    return sonuc
```

Budamalı ve budamasız sayım fonksiyonlarını yazdık. Budamasız sürüm, her satıra farklı bir sütun koyar (yani sütun çakışmasını hiç denemez) ve köşegen kontrolünü yalnızca yaprakta yapar. Bu, `N!` yaprağa sahip bir ağaçtır; budamalı sürüm ise yalnızca güvenli dalları açar.

```python
def budamali_say(n):
    """Dugum sayisi: her cagri bir dugum."""
    cozum = [0]
    dugum = [0]
    yerler = []

    def dfs(satir):
        dugum[0] += 1
        if satir == n:
            cozum[0] += 1
            return
        for s in range(n):
            if guvenli(yerler, satir, s):
                yerler.append(s)
                dfs(satir + 1)
                yerler.pop()

    dfs(0)
    return cozum[0], dugum[0]
```

```python
def budamasiz_say(n):
    """Her satira farkli sutun koy (sutun cakismasi budanmaz),
    capraz kontrolu yalnizca yaprakta yap."""
    cozum = [0]
    dugum = [0]
    kullanildi = [False] * n
    yerler = []

    def dfs(satir):
        dugum[0] += 1
        if satir == n:
            if guvenli_son(yerler):
                cozum[0] += 1
            return
        for s in range(n):
            if not kullanildi[s]:
                kullanildi[s] = True
                yerler.append(s)
                dfs(satir + 1)
                yerler.pop()
                kullanildi[s] = False

    dfs(0)
    return cozum[0], dugum[0]
```

```python
def guvenli_son(yerler):
    n = len(yerler)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(yerler[i] - yerler[j]) == j - i:
                return False
    return True


if __name__ == "__main__":
    print("N  cozum  budamali  budamasiz")
    for n in range(4, 9):
        c1, d1 = budamali_say(n)
        c2, d2 = budamasiz_say(n)
        print("%d %6d %9d %10d" % (n, c1, d1, d2))
    print("ilk cozum (n=8):", cozumler(8)[0])
```

```term
$ python vezir.py
N  cozum  budamali  budamasiz
4      2        17         65
5     10        54        326
6      4       153       1957
7     40       552      13700
8     92      2057     109601
ilk cozum (n=8): [0, 4, 7, 5, 2, 6, 1, 3]
```

Çıktıdaki çözüm sayıları (2, 10, 4, 40, 92) bilinen değerlerdir, ve iki sürüm her `N` için aynı sayıda çözüm bulur. Düğüm sayılarında fark, `N` büyüdükçe açılır: `N = 8` için budamalı 2057, budamasız 109601 düğüm. Şekil 15.7 bu ölçümü log ölçekte gösterir.

![Şekil 15.7: N-Queens için budamalı ve budamasız düğüm sayıları (log ölçek). Fark N arttıkça hızla büyür.](gorseller/b15_budama_olcum.png)

Bit maskeli sürüm, aynı geri izlemeyi çok daha hızlı yapar. Her satırın dolu sütunlarını, sol köşegenini ve sağ köşegenini birer tamsayının bitleriyle tutarız. Bir sütunun boş olup olmadığını `tum & ~(cols | ld | rd)` ifadesi tek seferde verir; en düşük boş biti `bos & (0u - bos)` ile alırız. İşaretsiz tamsayılar kullanıyoruz, çünkü işaretli taşma tanımsız davranıştır (Bölüm 14.3).

```c
#include <stdint.h>
#include <stdio.h>

static long cozum = 0;
static long dugum = 0;

/* cols: dolu sutunlar; ld: sol capraz; rd: sag capraz.
   Her bit bir sutun (ya da capraz) konumunu temsil eder. */
static void dene(uint32_t tum, uint32_t cols,
                 uint32_t ld, uint32_t rd) {
    dugum++;
    if (cols == tum) {
        cozum++;
        return;
    }
    uint32_t bos = tum & ~(cols | ld | rd);
    while (bos != 0) {
        uint32_t bit = bos & (0u - bos);   /* en dusuk 1 biti */
        bos ^= bit;
        dene(tum, cols | bit,
             ((ld | bit) << 1) & tum,
             (rd | bit) >> 1);
    }
}

int main(void) {
    printf("N  cozum  dugum\n");
    for (uint32_t n = 1; n <= 10; n++) {
        cozum = 0;
        dugum = 0;
        dene((1u << n) - 1u, 0, 0, 0);
        printf("%2u %6ld %6ld\n", n, cozum, dugum);
    }
    return 0;
}
```

```term
$ gcc -O2 -Wall -Wextra -std=c11 vezir_bit.c -o vezir_bit
$ ./vezir_bit
N  cozum  dugum
 1      1      2
 2      0      3
 3      0      6
 4      2     17
 5     10     54
 6      4    153
 7     40    552
 8     92   2057
 9    352   8394
10    724  35539
```

Bu program `N = 1..10` için bilinen çözüm sayılarını verir: `1, 0, 0, 2, 10, 4, 40, 92, 352, 724`. Düğüm sayıları, Python sürümünün `N = 4..8` için verdiği değerlerle aynıdır (`N = 8`'de 2057). Programı `-fsanitize=address,undefined` ile de çalıştırdık; ASan ve UBSan herhangi bir hata raporlamadı.

Şekil 15.8, `N = 8` için ilk çözümü (`[0, 4, 7, 5, 2, 6, 1, 3]`, yani 1-indeksli olarak 1., 5., 8., 6., 3., 7., 2., 4. sütunlar) bir tahta üzerinde gösterir.

![Şekil 15.8: 8-vezir problemi için bir çözüm. Her satırda bir vezir, hiçbir ikisi aynı sütunda ya da köşegende değil.](gorseller/b15_vezir8.png)

## 15.9 Sudoku: kısıtlar, sezgi ve düğüm sayısı

Sudoku, geri izlemenin bir kısıt problemi olarak nasıl düşünüldüğünü gösterir. Her boş hücre için bir **aday** kümesi vardır: satırında, sütununda ve `3 × 3` kutusunda henüz kullanılmamış rakamlar. Bir hücreye aday ekledikçe diğer hücrelerin adayları daralır; bu da aramayı kısıtlar.

Aşağıdaki program aday hesabını ve geri izlemeyi yazar. Şekil 15.9'daki ölçüm için iki karar kuralı vardır. **Naif sıra** ilk boş hücreyi alır. **MRV** (Minimum Remaining Values, en kısıtlı hücre) ise en az adayı olan boş hücreyi seçer; bir hücrenin adayı yoksa dal hemen çıkmazdır.

```python
"""Sudoku cozucu: naif sira ve en kisitli hucre (MRV) sezgisi."""
import sys


def adaylar(tahta, r, c):
    kullanilan = set(tahta[r])
    kullanilan.update(tahta[i][c] for i in range(9))
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(3):
        for j in range(3):
            kullanilan.add(tahta[br + i][bc + j])
    return [d for d in range(1, 10) if d not in kullanilan]


```

Çözücünün ana fonksiyonu, düğüm sayacını ve bir sınırı taşır. Sınır, bir bulmacada ölçümün sonsuza gitmesini engeller; sınır aşılırsa bunu ayrıca bildiririz:

```python
def coz(tahta, mrv, sinir):
    """Dondurur: (cozum_tahtasi veya None, dugum, asildi_mi)."""
    dugum = [0]
    asildi = [False]

    def dfs():
        dugum[0] += 1
        if dugum[0] > sinir:
            asildi[0] = True
            return False
        secim = None
        secim_adaylar = None
        for r in range(9):
            for c in range(9):
                if tahta[r][c] != 0:
                    continue
                ad = adaylar(tahta, r, c)
                if not mrv:
                    secim, secim_adaylar = (r, c), ad
                    break
                if secim is None or len(ad) < len(secim_adaylar):
                    secim, secim_adaylar = (r, c), ad
            if secim is not None and not mrv:
                break
        if secim is None:
            return True                 # bos hucre kalmadi
        r, c = secim
        for d in secim_adaylar:
            tahta[r][c] = d
            if dfs():
                return True
            if asildi[0]:
                break
        tahta[r][c] = 0                 # geri al
        return False

    ok = dfs()
    return (tahta if ok else None), dugum[0], asildi[0]
```

Bulmacaları okuyup bir çözümün geçerliliğini kontrol eden yardımcı fonksiyonlar:

```python
def ayristir(metin):
    return [[int(metin[9 * r + c]) for c in range(9)]
            for r in range(9)]


def gecerli(tahta, metin):
    kume = set(range(1, 10))
    satirlar = all(set(s) == kume for s in tahta)
    sutunlar = all(set(tahta[r][c] for r in range(9)) == kume
                   for c in range(9))
    kutular = all(
        set(tahta[br + i][bc + j] for i in range(3) for j in range(3))
        == kume
        for br in (0, 3, 6) for bc in (0, 3, 6))
    verilen = ayristir(metin)
    korunur = all(verilen[r][c] in (0, tahta[r][c])
                  for r in range(9) for c in range(9))
    return satirlar and sutunlar and kutular and korunur


```

Ölçüm için kullandığımız iki bulmaca ve ana program:

```python
PULMACALAR = {
    "kolay": "530070000600195000098000060800060003400803001"
             "700020006060000280000419005000080079",
    "zor": "800000000003600000070090200050007000000045700"
           "000100030001000068008500010090000400",
}

if __name__ == "__main__":
    sinir = int(sys.argv[1]) if len(sys.argv) > 1 else 300000
    for ad, metin in PULMACALAR.items():
        for mrv in (False, True):
            tahta = ayristir(metin)
            cozum, dugum, asildi = coz(tahta, mrv, sinir)
            if asildi:
                durum = "sinir asildi"
            else:
                durum = ("gecerli" if gecerli(cozum, metin)
                     else "HATALI")
            print("%-6s mrv=%-5s dugum=%7d  %s"
                  % (ad, mrv, dugum, durum))
```

```term
$ python sudoku.py
kolay  mrv=False dugum=   4209  gecerli
kolay  mrv=True  dugum=     52  gecerli
zor    mrv=False dugum=  49559  gecerli
zor    mrv=True  dugum=  10102  gecerli
```

Çıktı, iki sezginin etkisini gösteriyor. Kolay bulmacada MRV, naif sıraya göre 4209 yerine 52 düğümle çözdü. Zor bulmacada fark daha küçüktür: 49559'a karşı 10102. İki bulmacada da bulunan çözüm, satır, sütun ve kutu kurallarını sağlıyor ve verilen rakamları değiştirmiyor (kod bunu `gecerli` ile denetler).

![Şekil 15.9: Sudoku çözücüde düğüm sayısı, naif sıra ve MRV için (log ölçek). Veriler sudoku.py çıktısıdır.](gorseller/b15_sudoku_olcum.png)

Dikkat edilecek iki nokta var. Birincisi, MRV düğüm başına daha fazla iş yapar: her düğümde tüm boş hücrelerin adaylarını hesaplar. Bu yüzden ölçtüğümüz şey düğüm sayısıdır; süre ölçümü değildir ve düğüm başına maliyeti ayrıca hesaba katmak gerekir. İkincisi, burada uyguladığımız yalnızca en kısıtlı hücre sezgisidir. Adaylar tek elemana indiğinde o değeri hemen yazan **kısıt yayılımı** (constraint propagation) bu sayıyı daha da düşürür; bu, bölümün Kendin Yap projesinde senin yapacağın bir genişlemedir.

## 15.10 Gerçek dünyada özyineleme ve geri izleme

Izgara ve ağaç yapıları, özyinelemenin en doğal alanıdır. Üç örnek üzerinden bu bölümü kapatıyoruz.

### Labirent: yol bulma ve yol sayma

Bir labirentte başlangıçtan çıkışa giden bir yol bulmak, geri izlemenin doğrudan uygulamasıdır: bir yöne git, çıkmaza girersen geri dön. Aynı ızgarada kendini kesmeyen yolları saymak ise geri izlemenin "tüm çözümleri say" biçimidir. Aşağıdaki program ikisini de yapar: köşeden köşeye yolları sayar, sonra örnek labirentte bir yol bulur.

```python
"""Labirent: geri izleme ile yol bulma ve kendini kesmeyen
yollari sayma."""

YONLER = [(0, 1), (1, 0), (0, -1), (-1, 0)]

HARITA = [
    "S#.....",
    ".#.###.",
    ".#...#.",
    ".####.#",
    "......E",
]


def konum(harita, isaret):
    for r, satir in enumerate(harita):
        if isaret in satir:
            return r, satir.index(isaret)
    raise ValueError("isaret yok: " + isaret)


```

```python
def yol_bul(harita):
    n, m = len(harita), len(harita[0])
    bas = konum(harita, "S")
    son = konum(harita, "E")
    ziyaret = set()
    yol = []

    def dfs(r, c):
        yol.append((r, c))
        if (r, c) == son:
            return True
        ziyaret.add((r, c))
        for dr, dc in YONLER:
            nr, nc = r + dr, c + dc
            if (0 <= nr < n and 0 <= nc < m
                    and harita[nr][nc] != "#"
                    and (nr, nc) not in ziyaret):
                if dfs(nr, nc):
                    return True
        ziyaret.discard((r, c))
        yol.pop()                   # cikmaz: geri al
        return False

    if dfs(*bas):
        return yol
    return None

```

```python
def kose_yol_sayisi(k):
    """k x k dugumlu izgarada (0,0)'dan (k-1,k-1)'a
    kendini kesmeyen yollarin sayisi."""
    ziyaret = set()
    say = [0]

    def dfs(r, c):
        if (r, c) == (k - 1, k - 1):
            say[0] += 1
            return
        ziyaret.add((r, c))
        for dr, dc in YONLER:
            nr, nc = r + dr, c + dc
            if (0 <= nr < k and 0 <= nc < k
                    and (nr, nc) not in ziyaret):
                dfs(nr, nc)
        ziyaret.discard((r, c))

    dfs(0, 0)
    return say[0]
```

```python
if __name__ == "__main__":
    for k in range(2, 6):
        print("%d x %d dugum: %6d yol" % (k, k, kose_yol_sayisi(k)))
    yol = yol_bul(HARITA)
    print("yol uzunlugu:", len(yol) - 1, "adim")
    izgara = [list(s) for s in HARITA]
    for r, c in yol:
        if izgara[r][c] == ".":
            izgara[r][c] = "*"
    for satir in izgara:
```

```term
$ python labirent.py
2 x 2 dugum:      2 yol
3 x 3 dugum:     12 yol
4 x 4 dugum:    184 yol
5 x 5 dugum:   8512 yol
yol uzunlugu: 10 adim
S#.....
*#.###.
*#...#.
*####.#
******E
```

Köşeden köşeye yol sayıları 2, 12, 184, 8512'dir; bu sayılar `k = 2..5` için `k × k` düğümlü ızgaraların kendini kesmeyen yollarıdır ve `k = 3` için 12'yi elle de sayabilirsin. Labirent çıktısı, `S`'den `E`'ye yolu `*` ile işaretler; yol 10 adımdır. Yol bulma, bulunduğu anda durur; sayma ise tüm dalları gezer.

### Özyinelemeli iniş ile ayrıştırıcı

Bir derleyici ya da bir komut dilinin ayrıştırıcısı, ifadeyi dilbilgisi kurallarına göre okur. **Özyinelemeli iniş** (recursive descent) bu kuralları, her kural için bir fonksiyon yazarak uygular. Kural kendini içerdiğinde (parantez içinde ifade) fonksiyon kendini çağırır. Aşağıdaki ayrıştırıcı, dört işlem, parantez ve tekli eksi işaretini destekler. Dilbilgisi, dosyanın başındaki yorumdadır.

```python
"""Ozyinelemeli inis (recursive descent) ile aritmetik ifade.

Dilbilgisi:
    ifade := terim (('+' | '-') terim)*
    terim := carpan (('*' | '/') carpan)*
    carpan := SAYI | '(' ifade ')' | '-' carpan
"""


class AyristiHatasi(Exception):
    pass


def belirtecle(metin):
    sonuc = []
    i = 0
    while i < len(metin):
        c = metin[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(metin) and metin[j].isdigit():
                j += 1
            sonuc.append(metin[i:j])
            i = j
        elif c in "+-*/()":
            sonuc.append(c)
            i += 1
        else:
            raise AyristiHatasi("beklenmeyen karakter %r" % c)
    return sonuc


```

```python
class Ayristirici:
    def __init__(self, metin):
        self.belirtec = belirtecle(metin)
        self.konum = 0

    def _bak(self):
        if self.konum < len(self.belirtec):
            return self.belirtec[self.konum]
        return None

    def _al(self):
        t = self._bak()
        self.konum += 1
        return t

    def ifade(self):
        deger = self.terim()
        while self._bak() in ("+", "-"):
            op = self._al()
            sag = self.terim()
            deger = deger + sag if op == "+" else deger - sag
        return deger

    def terim(self):
        deger = self.carpan()
        while self._bak() in ("*", "/"):
            op = self._al()
            sag = self.carpan()
            if op == "*":
                deger = deger * sag
            else:
                if sag == 0:
                    raise AyristiHatasi("sifira bolme")
                deger = deger / sag
        return deger

```

```python
    def carpan(self):
        t = self._al()
        if t is None:
            raise AyristiHatasi("beklenmeyen ifade sonu")
        if t == "-":
            return -self.carpan()
        if t == "(":
            deger = self.ifade()
            if self._al() != ")":
                raise AyristiHatasi("')' bekleniyordu")
            return deger
        if t.isdigit():
            return int(t)
        raise AyristiHatasi("beklenmeyen belirtec %r" % t)


```

```python
def hesapla(metin):
    p = Ayristirici(metin)
    deger = p.ifade()
    if p.konum != len(p.belirtec):
        raise AyristiHatasi("fazla belirtec: %r" % p._bak())
    return deger


def en_derin_parantez():
    lo, hi = 1, 2000
    while lo < hi:
        orta = (lo + hi + 1) // 2
        try:
            hesapla("(" * orta + "1" + ")" * orta)
            lo = orta
        except RecursionError:
            hi = orta - 1
    return lo


```

```python
if __name__ == "__main__":
    ornekler = [
        "2 + 3 * 4",
        "(2 + 3) * 4",
        "10 - 4 - 3",
        "-(2 + 3) * 2",
        "7 / 2",
        "(2 + 3",
        "",
        "8 / (4 - 4)",
        "2 $ 3",
    ]
    for metin in ornekler:
        try:
            sonuc = hesapla(metin)
        except AyristiHatasi as hata:
            sonuc = "HATA: " + str(hata)
        print("%-14r -> %s" % (metin, sonuc))
    for d in (100, 500, 1000):
        metin = "(" * d + "1" + ")" * d
        try:
            print("%4d parantez -> %s" % (d, hesapla(metin)))
        except RecursionError:
            print("%4d parantez -> RecursionError" % d)
    print("en derin calisan parantez:", en_derin_parantez())
```

```term
$ python ayristirici.py
'2 + 3 * 4'    -> 14
'(2 + 3) * 4'  -> 20
'10 - 4 - 3'   -> 3
'-(2 + 3) * 2' -> -10
'7 / 2'        -> 3.5
'(2 + 3'       -> HATA: ')' bekleniyordu
''             -> HATA: beklenmeyen ifade sonu
'8 / (4 - 4)'  -> HATA: sifira bolme
'2 $ 3'        -> HATA: beklenmeyen karakter '$'
 100 parantez -> 1
 500 parantez -> RecursionError
1000 parantez -> RecursionError
en derin calisan parantez: 330
```

Öncelik, dilbilgisi kurallarının iç içe geçmesinden gelir: `terim` çarpımı, `ifade` toplamayı bağlar; bu yüzden `2 + 3 * 4` sonucu 14'tür. Çıktı, parantezin ve sıfıra bölmenin hatalarını da yakalar. En dikkat çekici satır, parantez derinliğiyle ilgilidir: her parantez seviyesi üç fonksiyon çerçevesi (`ifade`, `terim`, `carpan`) harcar, bu yüzden ayrıştırıcı yaklaşık 330 seviyeden sonra `RecursionError` ile durur. Bu sayı betiğin çağrı yığınına bağlıdır; bir derleyici ayrıştırıcısında bu sınırı bilmek, derin iç içe yapılarda hangi hatayı bekleyeceğini gösterir. Mert Studio Code gibi bir Türkçe ayrıştırıcı yazarken bu teknik kullanılabilir; Bölüm 37'de derleyicilerin sözdizimi çözümlemesini (parsing) bu temel üzerine kuracağız.

Shunting-yard algoritmasını Bölüm 8'de aynı problem için yazdık; oradaki yığın tabanlı yaklaşım ile bu özyinelemeli yaklaşım aynı dilbilgisini farklı biçimlerde okur. Kendin Yap projesinde ikisini karşılaştıracaksın.

### JSON ağacı ve dosya sistemi

JSON, iç içe sözlük ve listelerden oluşan bir ağaçtır. Derinliği ve anahtarların sayısını bulmak, ağacı özyinelemeyle gezmenin basit bir örneğidir:

```python
import json


def derinlik(veri):
    if isinstance(veri, dict):
        return 1 + max((derinlik(v) for v in veri.values()),
                       default=0)
    if isinstance(veri, list):
        return 1 + max((derinlik(v) for v in veri), default=0)
    return 0


def anahtar_say(veri):
    if isinstance(veri, dict):
        return len(veri) + sum(anahtar_say(v)
                               for v in veri.values())
    if isinstance(veri, list):
        return sum(anahtar_say(v) for v in veri)
    return 0


if __name__ == "__main__":
    metin = ('{"kullanici": {"ad": "Mert", "roller": '
             '["ogrenci", {"seviye": 3}]}, "aktif": true}')
    veri = json.loads(metin)
    print("derinlik =", derinlik(veri))
    print("anahtar  =", anahtar_say(veri))
    print(json.dumps(veri, ensure_ascii=False, indent=1))
```

```term
$ python json_derinlik.py
derinlik = 4
anahtar  = 5
{
 "kullanici": {
  "ad": "Mert",
  "roller": [
   "ogrenci",
   {
    "seviye": 3
   }
  ]
 },
 "aktif": true
}
```

Derinlik 4'tür: en dıştaki sözlük, `kullanici` sözlüğü, `roller` listesi ve içindeki `{"seviye": 3}` sözlüğü. Anahtar sayısı 5'tir (`kullanici`, `ad`, `roller`, `aktif`, `seviye`). Dosya sistemi de benzer bir ağaçtır: klasörler dallar, dosyalar yapraklardır. Python'un standart kütüphanesindeki `os.walk` bu gezinmeyi yapar; sürüme göre özyinelemeli ya da yinelemeli olabilir. Bunu Kod Okuma egzersizinde CPython kaynağından doğrulayacaksın.

## Çözümlü Örnekler

Her örnek Bölüm 5'in altı adımını izler. Adım 6'da elle iz sürme tablosu vardır; kodu yazmadan önce tabloyu kâğıtta kendin doldurmayı dene.

### Örnek 1 (★): Hızlı üs alma

**Problem.** `taban^n` değerini, `n ≥ 0` tam sayı olmak üzere hesapla. `n` kez çarpmak `O(n)` çarpım yapar. Büyük `n` için bunu daha az çarpımla yapabilir miyiz?

**Adım 1 — Anla.** Girdi iki sayıdır: taban ve üs. Çıktı tek bir sayıdır. Taban durum `n = 0`, cevap `1`'dir (`taban^0 = 1`).

**Adım 2 — Örnekle.** `2^10 = 1024`, `3^5 = 243`, `7^0 = 1`. Üs çift ise `2^10 = (2^5)^2`, tek ise `3^5 = (3^2)^2 · 3` biçiminde yazılabileceğini gözle.

**Adım 3 — Kaba çöz.** Döngüyle `n` kez çarp. Bu, `O(n)` çarpım ve doğru bir çözümdür.

**Adım 4 — Örüntü.** Üs yarıya indiğinde, taban değişmeden kalır ve yalnızca bir kez karesi alınır. Üs tekse bir fazla taban çarpılır. Her adımda üs yarıya inmektedir; bu, Bölüm 14'teki ikili aramanın da izlediği küçülmedir ve derinlik `log₂ n` olur.

**Adım 5 — İyileştir.** Örüntüyü özyinelemeli olarak yazalım:

```python
def us(taban, n):
    if n == 0:
        return 1
    yari = us(taban, n // 2)
    if n % 2 == 0:
        return yari * yari
    return yari * yari * taban


if __name__ == "__main__":
    print(us(2, 10))
    print(us(3, 5))
    print(us(7, 0))
```

Her özyineleme seviyesinde bir karesi alma, en fazla bir ek çarpma yapılır. Derinlik `log₂ n` olduğundan toplam çarpım `O(log n)`'dir. Bunu Bölüm 12'deki `T(n) = T(n/2) + O(1)` bağıntısıyla da görürsün (Master Teoremi'nin `a = 1`, `b = 2` durumu).

**Adım 6 — Doğrula.** Program `us(2, 10)`, `us(3, 5)` ve `us(7, 0)` için şu çıktıyı verdi:

```term
$ python ornek1.py
1024
243
1
```

`us(2, 10)` için elle iz sürme tablosu:

| Çağrı | `n` | Yarı (`us(taban, n // 2)`) | `n` çift mi | Dönüş |
|---|---|---|---|---|
| `us(2, 10)` | 10 | 32 | çift | 32 · 32 = 1024 |
| `us(2, 5)` | 5 | 4 | tek | 4 · 4 · 2 = 32 |
| `us(2, 2)` | 2 | 2 | çift | 2 · 2 = 4 |
| `us(2, 1)` | 1 | 1 | tek | 1 · 1 · 2 = 2 |
| `us(2, 0)` | 0 | — | — | 1 (taban durum) |

Tablo, dört çağrı içinde 10'un 0'a indiğini ve sonucun doğru olduğunu gösteriyor. Ayrıca `taban` negatif olabilir; Python'da büyük tam sayılar taşmaz, C'de ise sonuç taşar ve bu bir **tanımsız davranıştır** (Bölüm 14.3).

**Bunu AI'sız yazabilir misin?** Negatif üs (`taban^(-n)`) için fonksiyonu nasıl genişletirsin ve kesirli sonucu hangi veri tipinde saklarsın?

### Örnek 2 (★★): Geçerli parantez üretimi

**Problem.** `n` çift parantez çiftini kullanarak, her açılan parantezin kapanan bir parantezle eşleştiği bütün dizileri üret. `n = 2` için `(())` ve `()()` geçerlidir.

**Adım 1 — Anla.** Çıktı, uzunluğu `2n` olan geçerli dizilerin listesidir. Bir dizi geçerlidir, eğer her önekte kapanan parantez sayısı açılandan fazla değilse ve sonunda sayılar eşitse.

**Adım 2 — Örnekle.** `n = 1`: `()`. `n = 2`: `(())` ve `()()`. `n = 3`: beş dizi. Bu beş sayıyı elle yazmayı dene: `((()))`, `(()())`, `(())()`, `()(())`, `()()()`.

**Adım 3 — Kaba çöz.** Bütün `2n` uzunluklu açılan/kapanan dizilerini üret ve geçerli olanları seç. Bu `2^(2n)` aday üretir; `n = 10` için bu bir milyonu aşar.

**Adım 4 — Örüntü.** Her adımda iki seçenek vardır: `(` ya da `)`. Ama her seçim geçerliliği korumalıdır. Bu yüzden iki kural koyarız: açılan sayısı `n`'i geçemez, kapanan sayısı açılan sayısını geçemez. Bu iki kural, budamanın tam kendisidir.

**Adım 5 — İyileştir.** Kuralları özyinelemeye koyalım:

```python
def parantezler(n):
    sonuc = []

    def dfs(yol, acik, kapali):
        if len(yol) == 2 * n:
            sonuc.append("".join(yol))
            return
        if acik < n:
            yol.append("(")
            dfs(yol, acik + 1, kapali)
            yol.pop()
        if kapali < acik:
            yol.append(")")
            dfs(yol, acik, kapali + 1)
            yol.pop()

    dfs([], 0, 0)
    return sonuc


if __name__ == "__main__":
    print(parantezler(3))
    for n in range(1, 6):
        print(n, len(parantezler(n)))
```

Üretilen dal sayısı, geçersiz dizilerin dallarını hiç açmadan geçerli olanlara iner. Sayı, Catalan sayılarıdır (`C(n) = (2n)! / ((n + 1)! n!)`); bu büyüme, `n` çift sayılı olsa da üstel değil, yaklaşık `4^n / n^1.5` mertebesindedir.

**Adım 6 — Doğrula.** `n = 3` için program şu çıktıyı verdi; altındaki satırlar `n = 1..5` için sayıları gösteriyor:

```term
$ python ornek2.py
['((()))', '(()())', '(())()', '()(())', '()()()']
1 1
2 2
3 5
4 14
5 42
```

`n = 2` için iz tablosu:

| Yol | Açık | Kapalı | Karar |
|---|---|---|---|
| `(` | 1 | 0 | devam |
| `((` | 2 | 0 | açık = n, yalnızca `)` eklenir |
| `(()` | 2 | 1 | devam |
| `(())` | 2 | 2 | uzunluk 4: kaydet |
| `()` | 1 | 1 | devam |
| `()(` | 2 | 1 | devam |
| `()()` | 2 | 2 | uzunluk 4: kaydet |

Çıktı iki sonucu da verdi, sayılar 1, 2, 5, 14, 42 (Catalan dizisinin ilk beş terimi) ve bu dizi, programın ürettiği sayılarla eşleşiyor.

**Bunu AI'sız yazabilir misin?** Aynı kuralları kullanarak, açılan ve kapanan parantezlerin dışında `[` ve `]` çiftini de içeren geçerli dizileri nasıl üretirsin? Her iki çifti birlikte düşünürken hangi kural yeni olur?

### Örnek 3 (★★): Izgarada kelime arama

**Problem.** Harflerden oluşan bir ızgarada bir kelimenin, her hücresini en fazla bir kez kullanarak yatay ya da dikey komşu hücrelerle izlenip izlenemeyeceğini bul.

**Adım 1 — Anla.** Girdi bir matris ve bir kelimedir. Çıktı `True` ya da `False`'tur. Bir hücre aynı yolda iki kez kullanılamaz.

**Adım 2 — Örnekle.** Örnek ızgara:

```
A B C E
S F C S
A D E E
```

`SEE` var: `S(1,3)`, `E(2,3)`, `E(2,2)`. `ABCB` yok: üçüncü `C`'den sonra `B` gelebilecek komşu yoktur, ikinci `B` ise zaten kullanılmıştır.

**Adım 3 — Kaba çöz.** Her hücreden başlayıp kelimenin tamamını dene. Bu, tüm yolları numaralamaktır; kelime uzunluğu `L` ise `O(n·m·4^L)` olur.

**Adım 4 — Örüntü.** Bir hücreden başlayan arama, o hücredeki harfin kelimenin `k`. harfine eşit olup olmadığını kontrol eder; eşitse dört komşuya özyinelemeli olarak `k + 1` ile devam eder. Hücreyi ziyaret edilmiş işaretleyip, dallar bittiğinde geri al (geri izleme!).

**Adım 5 — İyileştir.** Kod, ızgara sınırlarını ve harf uyumsuzluğunu aynı yerde keser: hücre dışarıdaysa, ziyaret edilmişse ya da harf tutmuyorsa dal hemen döner.

```python
IZGARA = [
    ["A", "B", "C", "E"],
    ["S", "F", "C", "S"],
    ["A", "D", "E", "E"],
]


def var_mi(izgara, kelime):
    n, m = len(izgara), len(izgara[0])
    ziyaret = [[False] * m for _ in range(n)]

    def dfs(r, c, k):
        if k == len(kelime):
            return True
        if not (0 <= r < n and 0 <= c < m):
            return False
        if ziyaret[r][c] or izgara[r][c] != kelime[k]:
            return False
        ziyaret[r][c] = True
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            if dfs(r + dr, c + dc, k + 1):
                return True
        ziyaret[r][c] = False
        return False

    for r in range(n):
        for c in range(m):
            if dfs(r, c, 0):
                return True
    return False


if __name__ == "__main__":
    for kelime in ("ABCCED", "SEE", "ABCB"):
        print(kelime, var_mi(IZGARA, kelime))
```

**Adım 6 — Doğrula.** Program `ABCCED`, `SEE` ve `ABCB` için şu çıktıyı verdi:

```term
$ python ornek3.py
ABCCED True
SEE True
ABCB False
```

`SEE` için iz tablosu (başlangıç hücresi `S(1,0)` önce denenir ve başarısız olur):

| Adım | Hücre | Harf | `k` | Karar |
|---|---|---|---|---|
| 1 | `(1,0)` | `S` | 0 | eşleşir; komşular (`F`, `A`, `A`) tutmaz; geri al |
| 2 | `(1,3)` | `S` | 0 | eşleşir; komşuya gir |
| 3 | `(2,3)` | `E` | 1 | eşleşir; sol komşu `(2,2)` aranır |
| 4 | `(2,2)` | `E` | 2 | eşleşir; `k = 3 = len(kelime)`: `True` |

**Bunu AI'sız yazabilir misin?** Aynı ızgarada bir kelimenin *kaç farklı yolla* bulunabileceğini nasıl sayarsın? Sayma için dönüş değerini nasıl değiştirirsin ve bu sayının ne zaman çok büyüyeceğini nasıl tahmin edersin?

### Örnek 4 (★★★): Rakamlara işlem ekleyerek hedefi bulmak

**Problem.** Bir rakam dizisindeki rakamlar arasına `+`, `-`, `*` koyarak ve rakamları birleştirerek (`12` gibi) hedef değeri veren bütün ifadeleri üret. Çarpma öncelikli olduğu için, ifadeyi sadece soldan sağa değerlendirmek yetmez.

**Adım 1 — Anla.** Girdi bir dizi (`"123"`) ve bir hedef (`6`) olsun. Çıktı, hedefe eşit değer veren ifadelerin listesidir. Sayılar birleştirilebilir; `0` ile başlayan çok basamaklı sayı (`05`) yasaktır.

**Adım 2 — Örnekle.** `"123"`, `6`: `1+2+3` ve `1*2*3`. `"105"`, `5`: `1*0+5` ve `10-5`. Elle deneyerek, `1+2*3`'ün 7 verdiğini görürsün, çünkü çarpma önce yapılır.

**Adım 3 — Kaba çöz.** Her ayrım (rakamlar arası, boşluk/birleşme) ve her operatör dizisi için ifadeyi üret ve Python'un `eval` fonksiyonuyla değerlendir. Bu üstel bir yoldur, ama doğruluk referansı için yararlıdır.

**Adım 4 — Örüntü.** Son eklenen terimi (`son`) ve toplamı (`toplam`) birlikte tutarsak, `*` için yeni toplam `toplam - son + son · v` olur: son terim düzeltilip çarpılır. Bu, öncelik kuralını tek bir geri izleme adımına indirir.

**Adım 5 — İyileştir.** Kod, her dal için üç seçeneği (`+`, `-`, `*`) ayrı bir özyineleme çağrısıyla dener ve `son`'u her seferinde günceller.

```python
def ifadeler(rakam, hedef):
    sonuc = []

    def dfs(i, yol, toplam, son):
        if i == len(rakam):
            if toplam == hedef:
                sonuc.append(yol)
            return
        for j in range(i + 1, len(rakam) + 1):
            parca = rakam[i:j]
            if len(parca) > 1 and parca[0] == "0":
                break
            v = int(parca)
            if i == 0:
                dfs(j, parca, v, v)
            else:
                dfs(j, yol + "+" + parca, toplam + v, v)
                dfs(j, yol + "-" + parca, toplam - v, -v)
                dfs(j, yol + "*" + parca,
                    toplam - son + son * v, son * v)

    dfs(0, "", 0, 0)
    return sonuc


if __name__ == "__main__":
    print(ifadeler("123", 6))
    print(ifadeler("232", 8))
    print(ifadeler("105", 5))
```

**Adım 6 — Doğrula.** Program üç örnek için şu çıktıyı verdi:

```term
$ python ornek4.py
['1+2+3', '1*2*3']
['2+3*2', '2*3+2']
['1*0+5', '10-5']
```

`"123"`, `6` için iz tablosu:

| Adım | İfade | `toplam` | `son` | Karar |
|---|---|---|---|---|
| 1 | `1` | 1 | 1 | başlangıç |
| 2 | `1+2` | 3 | 2 | devam |
| 3 | `1+2*3` | 3 − 2 + 6 = 7 | 6 | 7 ≠ 6: kabul edilmez |
| 4 | `1*2` | 2 | 2 | devam |
| 5 | `1*2*3` | 2 − 2 + 6 = 6 | 6 | 6 = hedef: kaydet |

Doğrulamayı brute force ile yaptık: rastgele 400 rakam dizisi ve hedef için, tüm ayrım ve operatör kombinasyonlarını `eval` ile değerlendirip sonuç kümesini karşılaştırdık; her durumda küme birebir eşleşti.

**Bunu AI'sız yazabilir misin?** Operatör kümesine bölme (`/`) eklediğinde `son` mantığı nasıl değişir ve hangi ek sınır durumlarını (sıfıra bölme, tam olmayan bölme) hangi sırayla kontrol edersin?

## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi bir yapay zekâ aracının kodunu kopyalayarak değil, kendi kâğıdında tasarlayıp sıfırdan yazarak yap. Önce taban durumları ve dilbilgisi kurallarını elle yaz; kodu bunların üstüne kur. Bölüm 15'in amacı, özyinelemeyi boş bir IDE'de yazabilmektir.
:::

### Proje 1 (★★): Üs ve değişken destekli ayrıştırıcı

**Amaç:** 15.10'daki özyinelemeli iniş ayrıştırıcısına sağdan birleşmeli üs operatörü (`^`) ve tek harfli değişkenleri (`x`, `y`) ekle. Sonuçları Bölüm 8'deki shunting-yard çözücüsüyle aynı ifadeler üzerinde karşılaştır.

**Beklenen davranış:**

1. `2 ^ 3 ^ 2` ifadesi 512 olmalıdır (sağdan birleşme: `2 ^ (3 ^ 2) = 2 ^ 9`). Soldan birleşirse 64 çıkar; bu yanlıştır.
2. Değişkenler bir sözlükten okunur. `x = 3` iken `x * x + 1` 10 olmalıdır.
3. Tanımsız bir değişken, eşleşmeyen parantez ya da sıfıra bölme açık bir hata ile bildirilir; sessizce `0` dönmez.
4. Üs operatörü tekli eksi ile birleşince davranış tanımlı olmalıdır: `-2 ^ 2` için hangi kuralı seçtiğini yaz ve gerekçesini belirt.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Dilbilgisine yeni bir kural ekle ve bunu özyinelemeli tanımla: `guc := carpan ('^' guc)?`. Sağ özyineleme, birleşmenin yönünü kendiliğinden verir. Değişkenler için `belirtecle` fonksiyonunda harfleri tanı ve değerlendirme sırasında sözlükten oku. Test için rastgele 200 ifade üret, Python'un `eval` fonksiyonuyla karşılaştır (`^` yerine `**` yaz) ve farklılıkları incele.

**Başarı kriterleri:**

- 200 rastgele geçerli ifadede sonuç, `eval` ile birebir aynıdır.
- `2 ^ 3 ^ 2` = 512; `x * x + 1` (`x = 3`) = 10.
- Tanımsız değişken, eksik parantez ve sıfıra bölme için üç ayrı hata mesajı; hiçbiri sessiz sonuç üretmez.
- Shunting-yard ile aynı 50 ifade için iki çözücünün çıktısı eşleşir ve farklılık gösteren ifade kalmaz (ya da farkın nedeni açıklanır).

### Proje 2 (★★★): Sudoku zorluk ölçeri

**Amaç:** 15.9'daki çözücüye kısıt yayılımı ekle (en az bir adayı kalmış hücreyi ve tek adayı olan hücreyi, yani "naked single" kuralını, hemen yaz) ve bulmacaların zorluğunu düğüm sayısına göre sınıflandıran bir ölçüm aracı yaz.

**Beklenen davranış:**

1. Çözücü, her düğümde tek adayı olan hücreleri döngüyle yazar; bu yazım adaylar yeniden hesaplanarak yayılır.
2. Çözücü, her bulmaca için düğüm sayısını, MRV ile ve MRV + yayılım ile ayrı ayrı raporlar.
3. Bir bulmacanın tek çözümü olup olmadığını (çözümü bulduktan sonra ikinci bir çözüm aranarak) denetleyen bir fonksiyon yazılır.
4. Aracın çıktısı, bulmacaları üç sınıfa ayıran bir tablo olur (kolay, orta, zor) ve eşik değerlerini sen belirlersin; eşikleri gerekçesiyle yaz.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Her düğümde adayları bir kez hesapla ve bir `aday[r][c]` kümesi tut; bir hücreye değer yazıldığında aynı satır, sütun ve kutudaki adayları güncelle. Tek adayı olan hücre kalmayana kadar yayılımı tekrarla. Düğüm sayacını yalnızca gerçek geri izleme dallarında artır; yayılım adımlarını ayrıca say ve raporla.

**Başarı kriterleri:**

- En az 20 farklı bulmacada, üretilen her çözüm `gecerli` kontrolünden geçer.
- Her bulmaca için MRV + yayılım düğüm sayısı, yalnızca MRV'ye göre daha az ya da eşit olur; istisnaları açıkla.
- Tek çözümlülük denetimi, bilinen çözümlü iki bulmacada doğru sonuç verir.
- Zorluk tablosu, hangi düğüm sayısı aralığının hangi sınıfa girdiğini gösterir ve bu aralıklar 20 bulmacada tutarlıdır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta çöz, sonra gerekirse kodla doğrula. Mülakat etiketli olanlar klasik mülakat sorularıdır.

1. ★ Bir dizinin elemanlarını ters çeviren özyinelemeli bir fonksiyon yaz. Taban durumunu ve küçültme adımını ilk iki satırda açıkça belirt.
2. ★ `n` basamaklı, yalnızca `0` ve `1`'den oluşan bütün dizileri üret (`2^n` tane). Bunu bir geri izleme ağacı olarak çiz. (Mülakat)
3. ★ Bir sayının basamaklarının toplamını özyinelemeyle hesapla. Derinliğin basamak sayısına eşit olduğunu bir örnekle doğrula.
4. ★★ Bir dizinin alt kümelerinden toplamı `k` olanların sayısını geri izlemeyle bul. Tekrarlı ve tekrarsız elemanlar için kaç farklı kod gerektiğini açıkla. (Mülakat)
5. ★★ Tekrarlı bir dizinin permütasyonlarını, tekrar kuralı olmadan üret; kuralı olan sürümle çıktı sayısını karşılaştır. Fazla çıktıların nereden geldiğini ağaçta göster.
6. ★★ 5×5 bir ızgarada (0 boş, 1 duvar) sol üstten sağ alta giden kendini kesmeyen yol sayısını geri izlemeyle say. (Mülakat)
7. ★★ N-Queens'in çözümlerini, ilk satırdaki vezirin sütununu 1 ile sınırlayarak say ve sonucu tüm çözüm sayısıyla karşılaştır.
8. ★★ Labirentte en kısa yolu bulmak için geri izlemeyi BFS ile karşılaştır. Hangi ızgarada DFS tabanlı geri izleme, en kısa olmayan bir yol bulur? (Mülakat)
9. ★★★ Bir dizinin her elemanına `+` ya da `-` işareti vererek toplamı sıfır olan bütün işaret dizilerini bul. `n = 20` için kaç düğüm ziyaret edilir? Budama bu sayıyı nasıl etkiler?
10. ★★★ Bölüm 15.2'deki `derin` fonksiyonunu açık yığınla yeniden yaz ve iki sürümü `10^6` derinlikte karşılaştır. Yığın sürümünün bellek tüketimini ayrıca ölç.
11. ★★★ Hanoi kulesinde `n` disk için hamle sayısını ve hamleleri özyinelemeyle üret. Hamle sayısının `2^n - 1` olduğunu tümevarımla kanıtla. (Mülakat)
12. ★★ Kelime arama (Örnek 3) için 8 yönlü komşuluğu ekle; sonuçların değiştiği bir ızgara örneği bul ve nedenini açıkla.

## Kod Okuma Egzersizi

Bu egzersizde Python'un standart kütüphanesindeki `os.walk` fonksiyonunun iki sürümünü karşılaştıracaksın. Kaynaklar resmi CPython deposundan indirildi: `https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/os.py` ve `v3.11.9/Lib/os.py`. Aşağıdaki kesitler birebir kopyadır. 3.12.10 kesitinde iki parça gösterildi; aradaki 427–430 satırları, yorum satırları olduğu için atlandı ve `...` ile işaretlendi.

**CPython 3.12.10, `Lib/os.py`, satır 348–352 (dizin yığınının başlangıcı):**

```python
    stack = [fspath(top)]
    islink, join = path.islink, path.join
    while stack:
        top = stack.pop()
        if isinstance(top, tuple):
```

**CPython 3.12.10, `Lib/os.py`, satır 421–426 ve 431–432 (yukarıdan aşağı gezinme):**

```python
        if topdown:
            # Yield before sub-directory traversal if going top down
            yield top, dirs, nondirs
            # Traverse into sub-directories
            for dirname in reversed(dirs):
                new_path = join(top, dirname)
```

...

```python
                if followlinks or not islink(new_path):
                    stack.append(new_path)
```

**CPython 3.11.9, `Lib/os.py`, satır 407–419 (aynı gezinmenin 3.11 sürümü):** Aşağıdaki kesitte dört uzun yorum satırı ve bir çağrı satırı sayfa genişliği için iki satıra bölündü; sözcükler ve kod değişmedi.

```python
    if topdown:
        yield top, dirs, nondirs

        # Recurse into sub-directories
        islink, join = path.islink, path.join
        for dirname in dirs:
            new_path = join(top, dirname)
            # Issue #23605: os.path.islink() is used instead of
            # caching
            # entry.is_symlink() result during the loop on
            # os.scandir() because
            # the caller can replace the directory entry during the
            # "yield"
            # above.
            if followlinks or not islink(new_path):
                yield from _walk(new_path, topdown, onerror,
                                  followlinks)
```

**Sorular — cevaplamadan geçme:**

1. 3.12.10 kesitinde `stack = [fspath(top)]` ve `while stack:` döngüsü var. Bu yapı, 15.5'te yazdığımız açık yığınla flood fill'e nasıl benziyor? Hangi veriler yığında tutuluyor?
2. `for dirname in reversed(dirs):` döngüsü neden ters sırayla yazılmış? Yığından (`pop`) çıkan sıranın, dizin listesindeki sırayla eşleşmesi için bu gerekli mi?
3. 3.11.9 kesitinde `yield from _walk(new_path, ...)` çağrıları vardır. Derin bir dizin ağacında bu çağrılar çağrı yığınında nasıl bir zincir oluşturur? Bu zincirin uzunluğu neye bağlıdır?
4. 3.11.9'dan 3.12.10'a geçişte yinelemeli yapıya dönüşün gerekçesini kaynakta ara. Bulamazsan varsayım yapma. Derin dizinlerde 3.11.9 sürümünün `RecursionError` verip vermeyeceğini ölçmek için hangi deneyi tasarlardın? Biz bu deneyi çalıştırmadık; kaynaktan çıkan yalnızca iki sürümün yapısının farklı olduğudur.
5. 3.12.10 kesitinde `followlinks or not islink(new_path)` kontrolü neden her dal için yeniden yapılıyor ve yorumda neden "önbelleğe alınmıyor" denmiş? (Yorum satırlarını 427–430'dan oku.)
6. (Mülakat) Bir dizin ağacını yinelemeli gezen bir fonksiyon yazarken, yığında tutulan veri yapısının bellek maliyeti ağacın hangi özelliğine bağlıdır: derinliğine mi, genişliğine mi, düğüm sayısına mı?

## Bölüm Özeti

Bu bölümde özyinelemeyi bir çağrı yığınının davranışı olarak, geri izlemeyi ise o yığının arama için kullanılması olarak gördük:

- **Güven sıçraması**: Fonksiyonun daha küçük girdide doğru çalıştığını varsayıp büyük girdiye geçmek, tümevarımla aynı mantıktır. Her özyinelemeli fonksiyon için taban durum, küçültme ve birleştirme sorularını sor.
- **Çağrı yığını** çerçevelerden oluşur; `-O0`'da bir çerçeve, ölçtüğümüz programda 80 ile 144 bayt arasında yer tutar. Derinlik yığın sınırını aşarsa program çöker; taban durum eksikse `-O0`'da çökme, `-O2`'de sonsuz döngü ya da ASan'da `stack-overflow` görülebilir.
- **Kuyruk özyinelemesi** bir döngüye dönüştürülebilir; gcc `-O2` bunu bu bölümdeki örneklerde yaptı, Python ise yapmaz. Güvenilir yol, döngüye elle çevirmektir.
- **Açık yığın**, özyinelemeyi kendi belleğimizde yeniden yazmamızı sağlar; flood fill bunun iyi bir örneğidir ve sınır durumlarını (n = 0) test etmek zorunludur.
- **Geri izleme** seç, keşfet, geri al döngüsüdür. Alt küme, permütasyon ve kombinasyon, aynı döngünün farklı durum uzaylarıdır.
- **Budama**, erken kesilen dallarla düğüm sayısını düşürür. Kombinasyon toplamında bu, yaklaşık 3,7 kat; N = 8 N-Queens'te 53 kat azalma sağladı. Budamanın doğruluğu her zaman ayrıca kanıtlanmalıdır.
- **N-Queens** ve **Sudoku** geri izlemenin klasik örnekleridir; bit maskeleme ve en kısıtlı hücre sezgisi düğüm sayısını ciddi biçimde düşürür.
- **Özyinelemeli iniş**, dilbilgisi kurallarını fonksiyonlara çevirir; derinlik sınırı bir derleyicinin iç işleyişinde önemli bir sınırdır.

**Sonraki bölümde:** Bu bölümde fib ağacındaki tekrar eden alt problemleri gördük ve onları ortadan kaldırmayı erteledik. Bölüm 16'da Dinamik Programlama'da bu fikri ele alacağız: her alt problemi bir kez çözüp sonucu saklamak (memoization) ve bağımlılık sırasına göre tablo doldurmak (tabulation). Fibonacci'den başlayıp 0/1 sırt çantası, LCS ve edit distance gibi problemlere geçeceğiz.

::: mulakat
Klasik sorular; her birini birkaç dakika kâğıtta düşündükten sonra cevapla:

1. Bir özyinelemeli fonksiyonda taban durumu yanlış yazılırsa, sonuç hangi durumlarda yanlış, hangi durumlarda sonsuz döngü olur? Bir örnekle göster.
2. Kuyruk özyinelemesi nedir? `n + f(n - 1)` ile `f(n - 1) + n` arasında kuyruk özyinelemesi açısından fark var mı?
3. `fib(n)` için özyinelemeli çözümün zaman karmaşıklığı nedir? Tekrar eden çağrıları saklasaydın hangi karmaşıklığa inerdin?
4. Geri izlemede "geri al" adımı neden zorunludur? Bu adımı unutursan hangi tür hatayı görürsün?
5. Budama, doğruluğu bozabilir mi? Kombinasyon toplamında sıralama olmadan `break` kullanmak neden yanlış olur?
6. N-Queens'te satır satır yerleştirmek, neden her hücreyi tek tek denemekten daha verimlidir? Durum uzayının iki yaklaşımdaki büyüklüğünü karşılaştır.
7. Recursive descent ayrıştırıcıda operatör önceliği nasıl kodlanır? Çarpma ile toplama arasındaki önceliği hangi fonksiyonların çağrı sırası belirler?
8. Özyinelemeyi açık yığına çevirmek her zaman bellek kullanımını azaltır mı? Flood fill örneğinde yığının boyutu neye bağlıdır?
:::
