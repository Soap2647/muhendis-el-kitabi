%% kisim_no: VI
%% kisim_ad: İşletim Sistemi & Mimari
%% kisim_ayrac: evet
%% bolum_no: 24
%% baslik: CPU Mimarisi

## Giriş: Saatin içinde ne oluyor?

Bölüm 1'de işlemciyi bir döngü olarak tanıdık: komutu getir, çöz, yürüt, sonra bir sonrakine geç. O döngü hâlâ doğru, ama ona iki soru sormadık. Birincisi, "3 GHz" yazan bir kutu saniyede üç milyar kez tıklıyorsa, neden her tıkta bir komut bitmiyor da yüzlerce komut aynı anda ilerliyormuş gibi görünüyor? İkincisi, aynı C kodu bir sefer sıralı bir dizide, bir sefer karışık bir dizide çalıştırıldığında neden iki kat farklı hızda çalışıyor?

Bu soruların cevabı işlemcinin **mikromimarisinde** saklı. Mülakatlarda sık gelen iki soru tam buradan çıkar: "Dizi neden bağlı listeden hızlı?" ve "Bir döngüyü neden `if` yerine dalsız yazmak isteyebilirsin?". Birinci sorunun önbellek kısmı Bölüm 25'in konusu; ikinci sorunun dal kısmı bu bölümün ağırlık merkezi.

Savunma sanayiinde bu konu doğrudan işe yarar. Gerçek zamanlı bir uçuş kontrol döngüsünün en kötü durum süresini (worst-case execution time) tahmin etmek, işlemcinin dal tahmini, önbellek ve boru hattı davranışını bilmeden mümkün değildir. Gömülü tarafta Cortex-M4'ün DSP komutları ve isteğe bağlı kayan nokta birimi, sensör füzyonu gibi işlerde hızı doğrudan belirler. Bu bölümde hem bu donanımın neyi sağladığını (komut kümesi sözleşmesi) hem de altındaki tasarım kararlarını (boru hattı, dal tahmini, süperskalar yürütme, SIMD) göreceksin.

Bu bölümde iddiaların çoğunu ölçtük. Ölçüm ortamı şöyle: AMD Ryzen 7 6800H (Zen 3+ mimarisi), WSL2 üzerinde Ubuntu 24.04, gcc 13.3.0. Bu makinede `perf` yok ve `sudo` ile kurulum yapılamadı; bu yüzden donanım sayaçlarıyla (IPC, dal yanlış tahmin sayısı) doğrudan ölçüm yapamadık. ARM için çapraz derleyici ve Windows için MinGW/MSVC bu ortamda yoktu. Metinde bu nedenle bir bilginin **ölçüldü**, **derleyiciden doğrulandı** ya da **genel bilgi** olduğunu açıkça belirttik.

::: not
Bu bölümdeki her program WSL2 sanal makinesinde, tek bir CPU çekirdeğine (taskset -c 3) sabitlenmiş olarak çalıştırıldı. Her ölçüm en az beş kez tekrarlandı ve en küçük süre (ya da iki koşunun ortalaması) raporlandı. Bir sanal makinede zamanlama gürültüsü birkaç yüzde olabilir; bu yüzden tabloların tamamında değerler yerine yönü ve oranı yorumla.
:::

## 24.1 ISA ve mikromimari: sözleşme ile uygulama

Bir işlemciyi anlamak için iki ayrı şeyi birbirinden ayırmak gerekir. **Komut kümesi mimarisi (ISA, Instruction Set Architecture)** yazılımın gördüğü sözleşmedir: hangi komutlar var, kaç yazmaç var, bellek nasıl adreslenir, hangi ayrıcalık seviyeleri tanımlı. **Mikromimari** ise bu sözleşmeyi gerçekleştiren iç tasarımdır: komutlar kaç aşamalı bir boru hattından geçer, dallar nasıl tahmin edilir, kaç komut aynı anda çalıştırılabilir.

Bir restoran benzetmesi işe yarar. Menü ISA'dır: "köfte" dediğinde ne geleceğini bilirsin. Mutfak mikromimaridir: aynı köfte, bir mutfakta on dakikada, başka bir mutfakta yirmi dakikada çıkabilir. Müşteri (yazılım) menüye bakar, mutfağın içini görmez; ama mutfağın tasarımı yemeğin ne kadar hızlı geleceğini belirler.

Bu ayrımın pratik sonucu şudur: **ISA'yı değiştirmek yazılımı kırar, mikromimariyi değiştirmek yazılımı yavaşlatabilir ya da hızlandırabilir.** Aynı x86-64 ikili dosyası hem bir Intel hem bir AMD işlemcide çalışır, çünkü iki üretici de aynı ISA'yı gerçekleştirir; ama iki işlemcinin hızı farklı olabilir, çünkü mikromimarileri farklıdır.

![Şekil 24.1: ISA ile mikromimarinin katmanları. Yazılım derleyiciye, derleyici ISA'ya kadar iner. ISA, yazılımın gördüğü sözleşmedir; altındaki mikromimari (boru hattı, dal tahmini, önbellek, süperskalar birimler) bu sözleşmeyi farklı donanımlarda gerçekleştirir.](gorseller/b24_isa_katman.png)

Derleyici bu katmanlar arasındaki köprüdür. `gcc -march=native` derlediğinde derleyici, derlemenin yapıldığı makinenin mikromimarisine uygun komutlar (örneğin AVX2) kullanabilir; `-march=x86-64` dersen yalnızca her x86-64 işlemcinin bildiği komutlara izin verirsin. Bu seçim ISA'yı değiştirmez, ama hangi komutların üretileceğini belirler. Sonraki bölümlerde bu seçimin hızı nasıl etkilediğini göreceğiz.

Bölüm 1'deki `LOAD`, `ADD`, `STORE` sözde-assembly'si bu ISA kavramının bir taslağıydı. Gerçek ISA'lar aynı fikri çok daha zengin bir dille anlatır. Bu bölümde sana gerçek bir ISA'nın (x86-64) makine kodunu okutacağız.

| Kavram | ISA (sözleşme) | Mikromimari (uygulama) |
|---|---|---|
| Ne bilinir? | Komutların anlamı, yazmaç sayısı | Boru hattı derinliği, önbellek boyutu |
| Yazılım için önemi | Derleyici hangi komutu üreteceğini bilir | Komutların ne kadar sürdüğünü belirler |
| Değişince ne olur? | Eski ikili dosya çalışmaz | Aynı ikili dosya daha hızlı ya da yavaş çalışır |
| Örnekler | x86-64, AArch64, RISC-V | Zen 3+, Cortex-A78, Cortex-M4 |

::: ipucu
Bir programın "neden yavaş" olduğunu sorarken önce hangi katmanda sorunun olduğunu ayır. Komut sayısı çok ise sorun derleyicide ya da algoritmada olabilir. Komut sayısı makul ama her komut uzun sürüyorsa, sorun mikromimari düzeyindedir: bellek erişimi, dal yanlış tahmini ya da bağımlılık zinciri.
:::

## 24.2 CISC ve RISC: x86-64, ARM ve RISC-V

ISA tasarımında iki büyük felsefe vardır. **CISC (Complex Instruction Set Computer)** komutların karmaşık olmasına izin verir: tek bir komut hem bellekten okuyabilir, hem topla, hem de sonucu belleğe yazabilir. **RISC (Reduced Instruction Set Computer)** ise komutları küçük ve düzenli tutar: bellekle yalnızca yükleme (load) ve saklama (store) komutları konuşur, aritmetik komutlar yazmaçlar üzerinde çalışır.

x86-64 tipik bir CISC'tir. `add eax, [rbx+8]` tek bir komutta bellekten okur ve toplar. Komut uzunlukları değişkendir: bir komut 1 ile 15 bayt arasında olabilir. Bu esneklik kod yoğunluğunu artırır, ama komutların nerede bittiğini bulmayı zorlaştırır. AArch64 ve RISC-V ise tipik RISC'lerdir. ARM AArch64 her komutu 32 bit olarak kodlar; RISC-V'nin temel komutları da 32 bit'tir, isteğe bağlı sıkıştırılmış (C uzantısı) 16 bit komutlarla birlikte gelir.

Bu ayrım eskisi kadar keskin değildir. Modern x86 işlemciler karmaşık komutları iç işlemlerde (mikro-op) parçalar ve bu işlemler RISC benzeri bir yürütme birimine gider. Bu, genel bilgi olarak bilinen bir gerçektir; biz bunu ölçmedik. Yine de programcı açısından yazmaç sayısı, argüman geçirme kuralları ve komut uzunluğu hâlâ ISA'nın doğrudan gördüğü şeylerdir.

![Şekil 24.2: x86-64 genel amaçlı yazmaçları. Mavi argüman yazmaçlarıdır (System V), sarı korunan yazmaçlardır (fonksiyon dönmeden önce değerleri geri yüklenmelidir), yeşil geçici yazmaçlardır, pembe yığın ve çerçeve yazmaçlarıdır.](gorseller/b24_yazmac.png)

Şekil 24.2, x86-64'ün on altı genel amaçlı yazmacını gösteriyor. Her biri 64 bit; ama `eax`, `ax` ve `al` gibi alt parçalarıyla da erişilebilir. `eax` yazıldığında üst 32 bit sıfırlanır; bu, derleyicinin sık kullandığı bir kuraldır ve assembly okurken bunu bilmek gerekir. Yazmaçların rolleri (argüman, dönüş değeri, korunan) çağrı kuralının parçasıdır; bunu 24.4'te ayrıntılı göreceğiz.

Gömülü ve savunma dünyasında ISA seçimi projeye bağlıdır. Aşağıdaki tablo, dört yaygın ISA'nın programcının gördüğü temel farklarını özetliyor. Bu tabloyu okuduğunda, bir ISA'nın hangi yazılımı nasıl etkilediğini düşünebilirsin.

| Özellik | x86-64 | AArch64 | RISC-V (RV64I) | ARMv7-M (Cortex-M4) |
|---|---|---|---|---|
| Komut uzunluğu | 1-15 bayt | 32 bit | 32 bit (C ile 16 bit) | 16/32 bit (Thumb-2) |
| Genel amaçlı yazmaç | 16 | 31 + SP | 32 (x0 sabit sıfır) | 13 + SP, LR, PC |
| Argüman yazmaçları | rdi, rsi, rdx, rcx, r8, r9 (SysV) | x0-x7 | a0-a7 (x10-x17) | R0-R3 |
| Dönüş değeri | rax | x0 | a0 | R0 |
| Dönüş adresi | yığında (`call` iter) | x30 (LR) | ra (x1) | LR (R14) |

Tablo, bu ISA'ların ayrıntılarını özetler: x86-64 dönüş adresini yığına iter, ARM ve RISC-V ise dönüş adresini bir yazmaca (LR veya ra) koyar. Bu, Bölüm 8.2'de gördüğümüz çağrı yığını anlatısının x86'ya özgü tarafıdır; STM32 gibi bir Cortex-M işlemcide dönüş adresi LR'dedir ve fonksiyon başka bir çağrı yapacaksa LR'yi yığına kendisi kaydeder. MertOS x86-64 hedefli olduğu için bu bölümdeki assembly örnekleri x86-64'tür; ARM tarafını genel bilgi olarak anlatıyoruz.

::: dikkat
ARM AArch64 ve Cortex-M tarafındaki bilgilerin tamamı genel bilgidir; bu ortamda ARM çapraz derleyicisi bulunamadığı için bu bölümde ARM makine kodu üretip okumadık. Bu bilgileri bir ARM derleyicisiyle kendin doğrulamanı öneririz (`arm-none-eabi-gcc -S`).
:::

Burada önemli bir not: tablo hangi ISA'nın "daha iyi" olduğunu söylemez. Sayılar, komut uzunlukları ve yazmaç sayıları bir tasarım kararının sonuçlarıdır; her birinin bir bedeli vardır. Büyük yazmaç sayısı derleyiciye daha fazla seçenek verir (daha az yığın trafiği), ama daha çok bağlam kaydetme maliyeti anlamına gelir (Bölüm 26'da göreceğin süreç geçişleri). Sabit uzunluklu komutlar kodu çözmeyi kolaylaştırır, ama kod yoğunluğunu düşürür; gömülü sistemlerde flash belleğin dar olması bu takası önemli kılar.

## 24.3 Assembly okumak: C'den makine koduna

Assembly yazmak nadiren gerekir; ama assembly okumak neredeyse her gün işe yarar. Bir programın yavaş olmasının nedenini ararken, bir hata ayıklayıcıda (debugger) `disassemble` çıktısına bakarken ya da bir mülakatta "bu fonksiyon makinede ne yapıyor?" diye sorulduğunda, makine kodunu okuyabilmen gerekir. Bu bölümde kendi yazdığımız küçük bir C dosyasını derleyip çıktısını satır satır okuyacağız.

Önce deneyin kendisi. Aşağıdaki dosyada beş küçük fonksiyon var: bir dizi toplayan, bir kare hesaplayan, iki sayının büyüğünü bulan, başka bir fonksiyonu çağıran ve bir dal içeren fonksiyon.

```c
/* Bolum 24 - assembly okuma ornekleri */
int toplam(const int *a, int n)
{
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}

long kare_arti(long x, long y)
{
    return x * x + y;
}

int maks(int a, int b)
{
    return a > b ? a : b;
}

int cagiran(int x)
{
    return kare_arti(x, 7) + toplam(&x, 1);
}

int yaprak(int x, int y)
{
    int t = x * 3 + y;
    return t - 2;
}

int g(int x, int y)
{
    return x > y ? 3 * x + y : x - 2 * y;
}
```

Bu dosyayı iki farklı optimizasyon düzeyinde derledik: `-O0` (hiçbir optimizasyon yok, hata ayıklama için) ve `-O2` (gerçek üretim düzeyi). Her ikisi için de `-S` seçeneği derleyiciye makine kodunu değil, okunabilir assembly metnini üretmesini söyler. Ubuntu'nun gcc'si varsayılan olarak `endbr64` komutunu ekler (Intel CET ile uyumlu dallanma hedef işaretçisi); bu komut bir kontrol noktasıdır ve okurken yok sayabilirsin. Metinde gösterilen çıktılarda `.cfi` yönergelerini kaldırmak için `-fno-asynchronous-unwind-tables` kullandık.

Assembly metninin iki sözdizimi vardır. Varsayılan **AT&T** sözdiziminde kaynak önce, hedef sonra yazılır; yazmaçların önünde `%`, sabit değerlerin önünde `$` bulunur; komutun sonuna işlem boyutunu gösteren bir harf eklenir (`l` 32 bit, `q` 64 bit). **Intel** sözdiziminde ise hedef önce gelir ve yazmaçların önünde işaret yoktur. Aynı komut iki sözdiziminde şöyle görünür: AT&T'de `movl -4(%rbp), %eax`, Intel'de `mov eax, DWORD PTR [rbp-4]`. Derleyiciye `-masm=intel` vererek Intel sözdizimini isteyebilirsin; biz bu bölümde AT&T'yi kullanıyoruz, çünkü Linux araçlarının (objdump, gdb) varsayılanı budur.

Şimdi `toplam` fonksiyonunun `-O0` çıktısına bakalım. Derleyici her değişkeni yığında bir yere koyar ve her işlemi bellek üzerinden yapar. Çıktı şöyle:

```asm
toplam:
        endbr64
        pushq   %rbp
        movq    %rsp, %rbp
        movq    %rdi, -24(%rbp)
        movl    %esi, -28(%rbp)
        movl    $0, -8(%rbp)
        movl    $0, -4(%rbp)
        jmp     .L2
        movl    -4(%rbp), %eax
        cltq
        leaq    0(,%rax,4), %rdx
        movq    -24(%rbp), %rax
        addq    %rdx, %rax
        movl    (%rax), %eax
        addl    %eax, -8(%rbp)
        addl    $1, -4(%rbp)
        movl    -4(%rbp), %eax
        cmpl    -28(%rbp), %eax
        jl      .L3
        movl    -8(%rbp), %eax
        popq    %rbp
        ret
```

Bu çıktıyı satır satır okuyalım. Önce fonksiyonun çerçevesini kurar: `pushq %rbp` ve `movq %rsp, %rbp` eski çerçeve işaretçisini kaydeder ve yeni çerçeveyi açar. `movq %rdi, -24(%rbp)` ve `movl %esi, -28(%rbp)` ilk iki argümanı (dizinin adresi `rdi`, uzunluk `esi`) yığına kopyalar; `-O0`'da derleyici argümanları bile bellekte saklar. `movl $0, -8(%rbp)` toplam değişkeni `s`'yi, `movl $0, -4(%rbp)` döngü sayacı `i`'yi sıfırlar. Ardından `jmp .L2` koşul kontrolüne atlar.

Döngü gövdesi `.L3` etiketindedir. `movl -4(%rbp), %eax` ve `cltq` sayacı `eax`'e alır ve 64 bit'e genişletir. `leaq 0(,%rax,4), %rdx` bayt ofsetini hesaplar (her `int` 4 bayt, bu yüzden `i*4`). `movq -24(%rbp), %rax` dizinin adresini yığından okur, `addq %rdx, %rax` elemanın adresini bulur ve `movl (%rax), %eax` elemanın değerini yazmaca koyar. Asıl toplama `addl %eax, -8(%rbp)` ile yapılır: değer doğrudan bellekte duran `s`'ye eklenir. Son olarak `addl $1, -4(%rbp)` sayacı artırır. `.L2` bloğu koşulu sınar: `cmpl -28(%rbp), %eax` ile `i` ile `n`'yi karşılaştırır ve `jl .L3` ile döngüye geri döner.

Dikkat et: döngünün tek bir iterasyonunda `s` iki kez bellekte değiştiriliyor (`addl %eax, -8(%rbp)`) ve sayaç iki kez bellekte değiştiriliyor. Bellekte bir değeri değiştirmek, yazmaçta değiştirmekten çok daha yavaştır; bunun neden ve nasıl hızlandığını Bölüm 25'te göreceksin. Şimdilik bilmen gereken, `-O0` çıktısının ne kadar "gereksiz" işlem içerebileceğidir.

Aynı fonksiyonun `-O2` çıktısı ise çok farklı görünür:

```asm
toplam:
        endbr64
        testl   %esi, %esi
        jle     .L4
        movslq  %esi, %rsi
        xorl    %eax, %eax
        leaq    (%rdi,%rsi,4), %rdx
        addl    (%rdi), %eax
        addq    $4, %rdi
        cmpq    %rdx, %rdi
        jne     .L3
        ret
        xorl    %eax, %eax
        ret
```

Bu çıktıda çerçeve kurulumu yok, yerel değişkenler yazmaçlarda, döngü tek bir `addl (%rdi), %eax` komutuyla toplamı yapıyor. Derleyici `n <= 0` durumunu başta kontrol ediyor (`testl %esi, %esi` ve `jle .L4`), dizinin sonunu `leaq (%rdi,%rsi,4), %rdx` ile önceden hesaplıyor, döngü sayacı yerine işaretçiyi (`addq $4, %rdi`) ilerletiyor. Sayılar bunu özetler: `-O0`'da döngü iterasyonu başına on bir komut vardır; `-O2`'de dört. Toplam komut sayısı da yaklaşık yirmi ikiden on üçe düşer.

::: ipucu
Assembly okurken her satırı ezberlemeye çalışma. Üç soru sor: Bu komut bir **değeri** mi taşıyor (`mov`), bir **hesap** mı yapıyor (`add`, `lea`), yoksa **akışı** mı değiştiriyor (`jmp`, `jl`, `call`)? Akış komutlarını bulursan fonksiyonun dallarını ve döngülerini çıkarabilirsin.
:::

`maks` fonksiyonuna bakarsak, `-O2` çıktısında bir `if` yerine koşullu taşıma (cmov) görürsün. Bu, dal yerine yazmaçlar arasında koşullu bir kopyalamadır. Çıktının ilgili kısmı şu:

```asm
maks:
        endbr64
        cmpl    %edi, %esi
        movl    %edi, %eax
        cmovge  %esi, %eax
        ret
```

`cmpl %edi, %esi` komutu `esi - edi`'yi hesaplar ve bayrakları günceller; `cmovge %esi, %eax` ise `esi >= edi` ise `esi`'yi `eax`'e kopyalar. Dal yoktur, yani işlemci hangi yolu seçeceğini tahmin etmek zorunda kalmaz. 24.6'da bu farkın neden önemli olduğunu göreceğiz. Aynı kaynağın `-O0` hâlinde ise karşılaştırma ve atlama komutları vardır; bu, dalın derleyici tarafından açıkça korunduğu anlamına gelir.

Şimdi tersine okuma alıştırması için bir fonksiyon daha: `g`. Bu fonksiyonun `-O2` çıktısı bir dal içeriyor. Kaynağı görmeden ne yaptığını çıkarabilmek, assembly okumanın asıl becerisidir; bunu Çözümlü Örnek 2'de yapacaksın.

```asm
g:
        endbr64
        cmpl    %esi, %edi
        jle     .L12
        leal    (%rdi,%rdi,2), %edi
        leal    (%rdi,%rsi), %eax
        ret
        addl    %esi, %esi
        movl    %edi, %eax
        subl    %esi, %eax
        ret
```

Son olarak, Intel sözdiziminde aynı `maks` fonksiyonunun çıktısına bak. Bu, sözdizimini tanıman için yeterli:

```asm
maks:
        endbr64
        cmp     esi, edi
        mov     eax, edi
        cmovge  eax, esi
        ret
```

Bu iki çıktı aynı makine kodunu anlatır; yalnızca yazım farklıdır. Bundan sonra metinde çoğunlukla AT&T kullanacağız, ama Intel yazımı da görmek istersen `-masm=intel` ile her zaman üretebilirsin.

## 24.4 Çağrı kuralları: System V AMD64 ve Windows x64

Bir fonksiyon başka bir fonksiyonu çağırdığında iki taraf da bir sözleşmeye uymak zorundadır: çağıran hangi değerleri nereye koyacağını, çağrılan hangi yazmaçları bozmadan geri döneceğini bilmelidir. Bu sözleşmeye **çağrı kuralı (calling convention)** denir ve bir ABI'nin (Application Binary Interface) parçasıdır. Çağrı kuralı yanlış uygulanırsa, derleyiciler arası ya da dil arası çağrılar sessizce bozulur.

Linux ve diğer Unix benzeri sistemlerde x86-64 için kullanılan kural **System V AMD64 ABI**'dir. Windows'ta ise **Microsoft x64** kuralı geçerlidir. İkisi arasındaki farklar aşağıdaki gibidir (Windows tarafı için genel bilgi; bu makinede MinGW ya da MSVC yoktu, ancak GCC'nin `ms_abi` niteliğiyle kuralın kodunu üretip doğruladık):

| Konu | System V AMD64 (Linux) | Microsoft x64 (Windows) |
|---|---|---|
| Tamsayı argümanları | rdi, rsi, rdx, rcx, r8, r9 | rcx, rdx, r8, r9 |
| Kalan argümanlar | yığında | yığında (5. ve sonrası) |
| Dönüş değeri | rax | rax |
| Gölge alan | yok | çağıran 32 bayt ayırır |
| Kırmızı bölge (red zone) | rsp'nin altında 128 bayt | yok (genel bilgi) |
| Korunan (callee-saved) | rbx, rbp, r12-r15 | rbx, rbp, rdi, rsi, r12-r15 |

Önce kendi gözümüzle doğrulayalım. Aşağıdaki program beş argümanlı iki fonksiyon yazıyor: biri System V, öbürü `ms_abi` niteliğiyle Windows x64 kuralıyla. Ayrıca bir yaprak fonksiyon (kırmızı bölgeyi göreceğiz) ve bir sistem çağrısı (`syscall`) içeriyor. Program hem kendi sonuçlarını hem de sistem çağrısının sonucunu yazdırır.

```c
/* Çağrı kuralları ve sistem çağrısı (x86-64, GCC) */
#include <stdio.h>
#include <unistd.h>

/* System V AMD64 (Linux, varsayılan) */
long sysv_bes(long a, long b, long c, long d, long e)
{
    return a + 2 * b + 3 * c + 4 * d + 5 * e;
}

/* Windows x64 kuralı: GCC'nin ms_abi uygulaması */
__attribute__((ms_abi))
long ms_bes(long a, long b, long c, long d, long e)
{
    return a + 2 * b + 3 * c + 4 * d + 5 * e;
}

/* yaprak fonksiyon: yığın işaretçisini değiştirmez */
int yaprak_tampon(int x)
{
    volatile int t[2];
    t[0] = x;
    t[1] = x + 1;
    return t[0] + t[1];
}

```

```c
/* syscall: getppid (x86-64'te numara 110) */
static inline long sistem_getppid(void)
{
    long r;
    __asm__ volatile("syscall"
                     : "=a"(r)
                     : "a"(110L)
                     : "rcx", "r11", "memory");
    return r;
}

int main(void)
{
    printf("sysv=%ld ms=%ld tampon=%d\n",
           sysv_bes(1, 2, 3, 4, 5), ms_bes(1, 2, 3, 4, 5),
           yaprak_tampon(4));
    printf("ppid_syscall=%ld\n", sistem_getppid());
    return 0;
}
```

Derleyip çalıştırdığımızda çıktı şöyle:

```term
$ gcc -O2 abi.c -o abi && ./abi
sysv=55 ms=55 tampon=9
ppid_syscall=52064
```

Sonuçlar beklediğimiz gibi: `1 + 2·2 + 3·3 + 4·4 + 5·5 = 55`, ve iki kural da aynı sonucu verir. Fakat argümanların nereden okunduğu farklıdır. `sysv_bes` fonksiyonunun assembly'si şöyledir:

```asm
sysv_bes:
        endbr64
        leaq    (%rdi,%rsi,2), %rax
        leaq    (%rdx,%rdx,2), %rdx
        addq    %rdx, %rax
        leaq    (%r8,%r8,4), %rdx
        leaq    (%rax,%rcx,4), %rax
        addq    %rdx, %rax
        ret
```

Beşinci argüman `e`, `r8` yazmacındadır (`leaq (%r8,%r8,4), %rdx` içinde `5*e` hesaplanır). Windows kuralında aynı fonksiyon şöyle derlenir:

```asm
ms_bes:
        endbr64
        movq    %rdx, %rax
        movq    40(%rsp), %rdx
        leaq    (%rcx,%rax,2), %rax
        leaq    (%r8,%r8,2), %rcx
        addq    %rcx, %rax
        leaq    (%rdx,%rdx,4), %rdx
        leaq    (%rax,%r9,4), %rax
        addq    %rdx, %rax
        ret
```

Burada ilk dört argüman `rcx`, `rdx`, `r8`, `r9`'dadır; beşinci argüman ise `movq 40(%rsp), %rdx` ile yığından okunur. Neden 40? Çünkü giriş anında yığının tepesinde dönüş adresi vardır (8 bayt), onun üstünde ise çağıranın ayırdığı 32 baytlık gölge alan vardır: 8 + 32 = 40. Bu gölge alanın amacı, çağrılan fonksiyonun ilk dört argümanı istediği zaman bellekte kaydedebilmesidir; hata ayıklayıcılar ve çalışma zamanı bunu kullanır.

Bu ayrımın pratik bir sonucu vardır: Windows'ta yazılmış bir DLL'i Linux'tan doğrudan çağırmak, çağrı kuralı farkı nedeniyle sessizce yanlış sonuç verebilir. Platformlar arası kütüphanelerde (örneğin bir sensör sürücüsünü hem Linux hem Windows'ta kullanacaksan) bu konu karşına çıkar. Çözüm, dışarıya açılan arayüzde kuralı açıkça belirtmek ve `__attribute__((ms_abi))` ya da `__stdcall`/`__cdecl` gibi niteliklerle sınır noktalarını işaretlemektir.

### Yığın çerçevesi ve kırmızı bölge

Çağrı kuralının bir parçası da yığın çerçevesidir. System V'de çağrı anında yığın işaretçisi `rsp` 16 bayta hizalı olmalıdır; çağrı komutu dönüş adresini (8 bayt) yığına iter, böylece çağrılan fonksiyonun girişinde `rsp` 16'nın 8 fazlasıdır. Fonksiyon kendi yerel değişkenleri için `rsp`'yi aşağı indirir ve çıkarken eski değerine döndürür. Şekil 24.3 bu çerçeveyi iki kuralda yan yana gösteriyor.

![Şekil 24.3: System V ve Windows x64 çağrı çerçeveleri. Yığın yüksek adresten düşük adrese büyür. Windows'ta çağıran, çağrılan fonksiyon için 32 baytlık gölge alanı çerçevenin hemen üstünde ayırır. System V'de ise yaprak fonksiyon rsp'nin altındaki 128 baytlık kırmızı bölgeyi kullanabilir.](gorseller/b24_cagri.png)

Kırmızı bölge (red zone) System V'nin ilginç bir optimizasyonudur. Bir **yaprak fonksiyon** (başka bir fonksiyon çağırmayan fonksiyon) yerel verisini `rsp`'nin altındaki 128 bayta yerleştirebilir ve `rsp`'yi hiç değiştirmez. Böylece yığın işaretçisini ayarlamak için gereken komutlar kaybolur. Bunu görmek için şu küçük fonksiyonu kullanalım. Dikkat: içindeki `volatile` niteliği derleyiciyi diziyi gerçekten bellekte tutmaya zorlar; yoksa derleyici diziyi tamamen yazmaçlarda tutup hiçbir şey üretmeyebilir.

```c
/* Kırmızı bölge: yaprak fonksiyon rsp'yi değiştirmeden kullanır */
int kirmizi(int x)
{
    volatile int t[2];   /* volatile: bellekte kalmak zorunda */
    t[0] = x;
    t[1] = x + 1;
    return t[0] + t[1];
}
```

Derleyicinin ürettiği kod, stack protector kapalıyken şöyle:

```asm
kirmizi:
        endbr64
        movl    %edi, -8(%rsp)
        addl    $1, %edi
        movl    %edi, -4(%rsp)
        movl    -8(%rsp), %eax
        movl    -4(%rsp), %edx
        addl    %edx, %eax
        ret
```

Bu fonksiyonda `subq $24, %rsp` yok. Değerler doğrudan `-8(%rsp)` ve `-4(%rsp)` adreslerine yazılıyor, yani yerel alan `rsp`'nin altında, kırmızı bölgede duruyor. Çağrı yapmayan bir fonksiyon için bu güvenlidir; çünkü hiçbir çağrı bu bölgenin üzerine yazmaz. Kırmızı bölge yalnızca yaprak fonksiyonlar için geçerlidir; fonksiyon bir çağrı yaparsa dönüş adresi bu bölgenin içine yazılırdı ve veri bozulurdu.

Bu optimizasyon çekirdek kodunda sorun çıkarabilir. Bir kesme (interrupt) geldiğinde işlemci donanım olarak yığına veri iter ve bu, kırmızı bölgedeki verinin üstüne yazabilir. Bu nedenle Linux çekirdeği, genel bilgi olarak, `-mno-red-zone` ile derlenir. Bizim `abi.c` örneğinde ise yaprak fonksiyon `yaprak_tampon` stack protector nedeniyle `rsp`'yi ayarlıyor; bu yüzden kırmızı bölgeyi göstermek için koruyucuyu kapattık.

Kırmızı bölgenin doğrulamasını yapmak için kirmizi.c'yi bir test programıyla birlikte derledik. Test programı aynı zamanda `syscall` komutunu da kullanıyor; bu sistem çağrısının CPU tarafını 24.10'da ele alacağız.

```c
#include <stdio.h>
#include <unistd.h>

int kirmizi(int x);

static inline long sistem_getppid(void)
{
    long r;
    __asm__ volatile("syscall"
                     : "=a"(r)
                     : "a"(110L)
                     : "rcx", "r11", "memory");
    return r;
}

int main(void)
{
```

```term
$ gcc -O2 kirmizi.c kirmizi_test.c -o kirmizi_test && ./kirmizi_test
kirmizi(4)=9
syscall_ppid=52064 getppid=52064 eslesme=evet
```

Sistem çağrısı sonucu (`getppid`) libc'nin `getppid()` sonucuyla eşleşiyor. Bu, `syscall` komutunun, çağrı numarasını `rax` yazmacına koyarak, Linux çekirdeğine doğrudan nasıl gidildiğini gösteriyor. Çağrı numarası 110 Linux x86-64'te `getppid` anlamına gelir; bunu çekirdeğin sistem çağrı tablosundan biliyoruz. Yazmaçların hangi değerleri koruduğu, sistem çağrıları için ayrı bir kuraldır: `syscall` komutu `rcx` ve `r11` yazmaçlarını bozar; bu yüzden inline assembly'de bunları `clobber` listesine yazdık.

### Gerçek bir örnek: bağlam değiştirme

Çağrı kurallarının pratik sonucunu, MertOS'un bağlam değiştirme kodunda da görebilirsin. Bir işletim sistemi iki süreç arasında geçiş yaparken, geçişin yapıldığı fonksiyon tarafından bozulmayan (korunan) yazmaçları kaydetmek zorundadır; çünkü geçişten sonra başka bir süreç o yazmaçları kendi değerleriyle kullanacaktır. MertOS'un `switchContext` fonksiyonu bunu yapar:

```asm
switchContext:
    ; ============================================================
    ; 1. Mevcut context'i 'old_ctx'a kaydet (rdi)
    ; ============================================================
    mov  [rdi + 0],  r15
    mov  [rdi + 8],  r14
    mov  [rdi + 16], r13
    mov  [rdi + 24], r12
    mov  [rdi + 32], rbx
    mov  [rdi + 40], rbp

    ; RSP kaydet (call'dan önceki stack pointer)
    ; NOT: 'call switchContext' RSP'yi -8 yaptı (return addr push)
```

Kesitin 35. satırı bir yorumdur ve 70 karakter sınırını aştığı için atlandı; yorumu kaynak dosyada okuyabilirsin. Kalan kısım:

```asm
    mov  [rdi + 48], rsp

    ; CR3 kaydet (mevcut page table)
    mov  rax, cr3
    mov  [rdi + 56], rax
```

Dosyanın başındaki açıklama, neden assembly kullanıldığını açıklıyor: C çağrı kuralı yalnızca bazı yazmaçları korur, ama bağlam değiştirme bir fonksiyon çağrısı gibi görünür ve iki bağlamın kendi yazmaçlarını ayrı ayrı saklaması gerekir. Buradaki `rbx`, `rbp`, `r12`-`r15` yazmaçları System V'nin korunan yazmaçlarıdır; `rsp` ve `cr3` ise bağlamın yığın ve sayfa tablosu bilgisidir. Sayfa tablosu (`cr3`) kaydetmenin neden gerektiğini Bölüm 25'te, süreçlerin tanımını ise Bölüm 26'da göreceksin.

Bu kodun eksik bir yanı da var ve bunu açıkça söyleyelim: bu blok yalnızca yazmaçları kaydedip yükler; kayan nokta yazmaçları (`xmm`) ve durum bayrakları burada ele alınmamıştır. Eğer bu iki bağlamda kayan nokta kullanılıyorsa, bu parçalar da kaydedilmelidir. Gerçek işletim sistemleri kayan nokta durumunu ayrıca ele alır; bu ayrıntı, süreç geçişlerini anlattığımız Bölüm 26'da yeniden karşımıza çıkacak.

## 24.5 Boru hattı (pipeline): beş aşama ve tehlikeler

Bölüm 1'deki getir-çöz-yürüt döngüsünü hatırla: her komut sırayla getirilir, çözülür, yürütülür ve sonucu yazılır. Bu döngüyü basit bir şekilde uygularsan, her komut bitmeden bir sonraki başlamaz. Donanımın büyük bir kısmı o anda boşta kalır. **Boru hattı (pipeline)** bu boşluğu doldurmak için döngüyü aşamalara böler ve her aşamayı kendi donanımına verir. Böylece bir komut bitmeden ikinci komut başlayabilir, üçüncü komut onun da arkasından gelir.

Bir çamaşırhane benzetmesi işe yarar. Tek bir çamaşır makinesi, yıkama bitene kadar kurutmaya geçmez. İki makine ve bir kurutucu olan bir hat ise her çamaşır beş yerine yalnızca bir "dönem" bekler; bir çamaşırın yıkanması hâlâ beş dönem sürer (gecikme), ama her dönemde bir çamaşır çıkar (verim). Boru hattının da temel ikilemi budur: **tek bir komutun ne kadar sürdüğü (gecikme) değişmez, ama saniyede kaç komut bittiği (verim) artar.**

Klasik bir RISC boru hattı beş aşamadan oluşur. Bu, ders kitaplarında en çok anlatılan tasarımdır ve modern işlemcilerin gerçek boru hatları çok daha derindir; yine de tehlike türleri ve çözümleri aynı ilkelere dayanır:

| Aşama | Kısaltma | Ne yapar? |
|---|---|---|
| Getir | IF (Instruction Fetch) | PC'nin gösterdiği komutu bellekten (önbellekten) okur |
| Çöz | ID (Instruction Decode) | Komutu çözer, yazmaçları okur |
| Yürüt | EX (Execute) | ALU işlemi yapar, adres hesaplar, dalın sonucunu belirler |
| Bellek | MEM (Memory) | Yükleme ya da saklama komutu belleğe erişir |
| Yaz | WB (Write Back) | Sonucu hedef yazmaca yazar |

Şekil 24.4, dört komutun bu boru hattında nasıl ilerlediğini gösteriyor. İlk komut bir `lw` (yükleme): bellekten `r1`'e bir değer okur. İkinci komut `add`, `r1`'in değerini kullanmak istiyor. İşte bu bağımlılık bir tehlike yaratır.

![Şekil 24.4: Beş aşamalı boru hattı ve yükleme-kullanma tehlikesi. I1 bir lw komutudur; I2 onun sonucu olan r1'i kullanır. Veri MEM aşamasının sonunda hazır olur, bu yüzden I2 en erken c5'te EX'e girebilir ve iki çevrim bekler (boş işler). Diğer komutlar da bu bekleme yüzünden bir çevrim kayar.](gorseller/b24_boru.png)

Şekildeki bekleme tek bir çevrimden ibarettir. Ama önemli olan, bu bekleyişin neden zorunlu olduğudur: `lw` komutunun değeri MEM aşamasında bellekten gelir, ve `add`'in EX aşamasında o değere ihtiyacı vardır. Değer ancak MEM'in sonunda elimizdedir; `add`, EX'e en erken o andan sonra girebilir. Bu, **yükleme-kullanma (load-use)** tehlikesi olarak bilinir. İletme çoğu veri bağımlılığını çözer, ama bu durumu tek başına çözemez; bu yüzden hemen hemen her boru hattı tasarımında bu tür bir bekleme bulunur.

### Üç tehlike türü

Boru hattı tehlikeleri üç ana sınıfa ayrılır. Hepsini bilmek, bir programın neden yavaş olabileceğini düşünmek için yeterlidir.

**Yapısal tehlike (structural hazard).** İki komut aynı donanım birimine aynı anda ihtiyaç duyduğunda ortaya çıkar. Örneğin tek bir bellek portu olan bir işlemcide hem bir komutu getirmek (IF) hem bir veriyi okumak (MEM) aynı çevrimde mümkün olmayabilir. Çözüm, donanımı çoğaltmaktır: ayrı komut ve veri önbelleği (Harvard benzeri ayrım) bu sorunu çözer.

**Veri tehlikesi (data hazard).** Bir komut, önceki bir komutun henüz yazmadığı bir değere ihtiyaç duyduğunda ortaya çıkar. Bu, en yaygın tehlikedir. Çözümünün ilk adımı **iletme (forwarding, bypass)**'dır: EX aşamasının sonucu (EX/MEM yazmacından) ve MEM aşamasının sonucu (MEM/WB yazmacından) doğrudan EX'in girişine geri beslenir. Böylece sonuç yazmaca yazılıp okunmadan da kullanılabilir. Yalnızca yükleme-kullanma durumunda iletme bile yeterli değildir, çünkü değer MEM'in sonunda çıkar; bu durumda bir çevrimlik bekleme (balonca) kaçınılmazdır.

**Kontrol tehlikesi (control hazard).** Bir dal (branch) komutu, hangi komutun sırada geleceğini değiştirir. Dal sonucu EX aşamasında belli olur; ama o zamana kadar boru hattı, dalın hedefinden *sonraki* komutları zaten getirmiştir. Dal alınırsa bu komutlar atılır ve boru hattı boşaltılır (flush). Klasik beş aşamalı tasarımda bu, dalın alınması durumunda iki çevrimlik bir kayıp demektir (genel bilgi). Bu kaybı azaltmak için dal tahmini kullanılır; bunu 24.6'da göreceğiz.

::: not
Bu bölümde ölçtüğümüz bir boru hattı yok; Şekil 24.4 klasik beş aşamalı tasarımın kavramsal bir çizimidir. Gerçek bir işlemcinin boru hattının derinliğini ve her aşamanın çevrim sayısını bu ortamda ölçemedik; `perf` ve donanım sayaçları olmadan bunu güvenilir biçimde yapamazsın.
:::

### Boru hattı ne kadar hızlandırır?

İdeal bir beş aşamalı boru hattında, her çevrimde bir komut tamamlanır; yani verim bir komut/çevrimdir. Ama ilk komutun bitmesi beş çevrim sürer: boru hattı dolana kadar tam hız yoktur. `N` komutlu bir programın çevrim sayısı kabaca `5 + (N - 1)`'dir. Tehlikeler bu sayıya bekleme çevrimleri ekler. Tehlikesiz bir dizi için `N = 1000` komut yaklaşık 1004 çevrim tutar; ama her beş komutta bir yükleme-kullanma tehlikesi varsa, her beş komut için bir çevrim eklenir ve toplam yaklaşık 1204 çevrime çıkar.

Bu hesap bize bir ilke öğretir: **boru hattı, bağımsız komutlarla beslendiğinde en iyi çalışır.** Bağımlı bir zincir (her komut bir öncekinin sonucunu bekler) boru hattını boşa çıkarır. Bu fikir, 24.7'de süperskalar ve sıra dışı yürütmeye, ardından ILP ölçümümüze uzanacak.

## 24.6 Dal tahmini ve dalsız programlama

Bir program içindeki dalların çoğu, aslında veriye bağlı değildir: döngü sonunda "devam et mi?" sorusunun cevabı genelde "evet"tir. Ama bazı dallar tamamen veriye bağlıdır: "bu eleman 128'den büyük mü?" gibi. İşlemci, bir dalın sonucunu EX aşamasında bilir; ama boru hattını doldurmak için IF aşamasında, dalın alınıp alınmayacağına karar vermek zorundadır. Bu karar bir **tahmin** olmak zorundadır, ve yanlış tahmin ceza olarak boru hattının boşaltılmasına yol açar.

Modern işlemcilerde ceza, klasik beş aşamalı tasarımın iki çevrimini çok aşar; bunun kesin rakamı işlemciye bağlıdır ve genel bilgi olarak "birkaç ondan fazla çevrim" diyebiliriz. Tahmin doğruysa ceza sıfırdır. Bu yüzden dal tahmin birimi (branch predictor) işlemcinin en çok uğraşılan parçalarından biridir.

### Tahmin nasıl yapılır?

En basit tahminci, her dal için tek bir bit tutar: son seferde alındıysa "alınacak" der. Bu bit, bir döngünün son iterasyonunda hata yapar ve bir sonraki çağrıda yine hata yapar; her döngü çıkışında iki hata demektir. Bunun yerine **iki bitlik doygun sayaç (2-bit saturating counter)** kullanılır: dört durum vardır (0, 1, 2, 3); 2 ve üzeri "alınacak" tahmini verir. Alınırsa sayaç bir artar (en fazla 3), alınmazsa bir azalır (en az 0). Tek bir sapma, güçlü bir eğilimi hemen tersine çevirmez:

| Mevcut durum | Tahmin | Dal alındıysa sonraki durum | Dal alınmadıysa sonraki durum |
|---|---|---|---|
| 0 (kesin alınmaz) | alınmaz | 1 | 0 |
| 1 (zayıf alınmaz) | alınmaz | 2 | 0 |
| 2 (zayıf alınır) | alınır | 3 | 1 |
| 3 (kesin alınır) | alınır | 3 | 2 |

Gerçek tahmin birimleri bu temel fikri birçok biçimde genişletir. **Küresel geçmiş (global history)** tabanlı tahminciler, son birkaç dalın sonucunu bir örüntü olarak kullanır: "önceki iki dal alındıysa bu da alınır" gibi. Dolaylı dallar (`call *%rax` gibi, hedefi bir yazmaçta olan çağrılar) için **dal hedef tamponu (BTB, Branch Target Buffer)** son hedefi hatırlar. Fonksiyon dönüşleri için bir **dönüş yığını tamponu (RSB)** kullanılır. Bu üç parça birlikte çalıştığında, sık görülen kalıplar çoğunlukla doğru tahmin edilir.

Bu bağlamda Bölüm 20'de yaptığımız ölçümü hatırlayalım. Sanal çağrı, derleyicinin dolaylı bir atlama olarak üretir; hedef tahmin edilebildiği sürece (tek tür nesneler) yalnızca küçük bir ek yük getirir, tahmin edilemediğinde (karışık tipler) bu yük büyür. Bölüm 20.10'daki tek türlü ölçümde sanal çağrı yaklaşık 2,7 ns, dallı sürüm yaklaşık 0,9 ns çıkmıştı; oradaki yorumumuzu da burada, dal tahmininin mekanizmasını gördükten sonra daha doğru kurabiliriz. Yine de ölçümü dal yanlış tahmini sayaçlarıyla doğrulayamadık, bu yüzden bu bağı bir yorum olarak sunuyoruz.

### Deney: sıralı dizi mi, sırasız dizi mi?

Dal tahmininin etkisini görmenin klasik yolu şudur: aynı toplamı, aynı dizide, yalnızca elemanların sırasını değiştirerek hesapla. Program 32768 tam sayıdan oluşan bir dizi üretir (sabit tohum 42, değerler 0 ile 255 arasında, yaklaşık yarısı 128 ve üzeri). Sonra aynı dizinin sıralanmış bir kopyasını alır. İki diziyi de aynı fonksiyonla toplar: `dalli`, 128 ve üzeri olanları bir `if` ile toplar; `dalsiz`, aynı işi bir maskeyle yapar.

Önemli bir tuzak var ve deneyin asıl konusu da budur: `-O2` ile derlediğinde derleyici `dalli`'nin dalını `cmov` ile değiştirebilir. Bu durumda dal kalmaz ve sonuç farklı görünmez. Bu yüzden deneyde iki derleme yaptık: birincisinde if-dönüşümünü (if-conversion) ve vektörleştirmeyi kapatarak dalın korunmasını sağladık (`-fno-if-conversion -fno-if-conversion2 -fno-tree-vectorize`), ikincisinde ise `-O2`'nin kendi kararına bıraktık. Dalın gerçekten kaldığını makine kodundan doğruladık:

```c
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define N 32768
#define TEKRAR 4000
#define OLCUM 7

static uint64_t durum = 42;   /* sabit tohum: tekrarlanabilir */

static uint32_t rnd(void)
{
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (uint32_t)(durum >> 32);
}

static int karsilastir(const void *a, const void *b)
{
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

static volatile long sink;    /* sonucu kullan: derleyici silmesin */

__attribute__((noinline))
long dalli(const int *v, int n)
{
    long s = 0;
    for (int i = 0; i < n; i++) {
        if (v[i] >= 128)      /* veriye bağlı dal */
            s += v[i];
    }
    return s;
}
```

```c

__attribute__((noinline))
long dalsiz(const int *v, int n)
{
    long s = 0;
    for (int i = 0; i < n; i++) {
        int m = -(v[i] >= 128);   /* 0 ya da -1 (bütün bitler 1) */
        s += v[i] & m;
    }
    return s;
}

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static int cmp_dbl(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

typedef long (*fn_t)(const int *, int);
```

```c

static void olc(const char *derleme, const char *ad, fn_t f,
                const int *v, const char *dizi, long *bek)
{
    double t[OLCUM];
    long sonuc = 0;
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_ms();
        for (int r = 0; r < TEKRAR; r++)
            sonuc = f(v, N);
        t[k] = simdi_ms() - b;
        sink = sonuc;
    }
    if (*bek < 0)
        *bek = sonuc;
    if (sonuc != *bek) {
        fprintf(stderr, "HATA: toplam uyusmuyor\n");
        exit(1);
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    double en = t[0], med = t[OLCUM / 2];
    printf("%s,%s,%s,%.2f,%.2f,%.3f,%ld\n", derleme, ad, dizi,
           en, med, en * 1e6 / ((double)TEKRAR * N), sonuc);
}
```

```c

int main(int argc, char **argv)
{
    const char *derleme = argc > 1 ? argv[1] : "bilinmiyor";
    static int v[N], s[N];
    for (int i = 0; i < N; i++)
        v[i] = (int)(rnd() % 256);  /* yaklaşık yarısı >= 128 */
    for (int i = 0; i < N; i++)
        s[i] = v[i];
    qsort(s, N, sizeof s[0], karsilastir);

    long bek = -1;
    printf("derleme,fonksiyon,dizi,en_az_ms,medyan_ms,"
           "ns_per_eleman,toplam\n");
    olc(derleme, "dalli", dalli, v, "sirasiz", &bek);
    olc(derleme, "dalli", dalli, s, "sirali", &bek);
    bek = -1;
    olc(derleme, "dalsiz", dalsiz, v, "sirasiz", &bek);
    olc(derleme, "dalsiz", dalsiz, s, "sirali", &bek);
    return 0;
}
```

Kontrollü derlemede `dalli` fonksiyonunun makine kodu, veri bağımlı bir atlama (`jle`) içerir:

```asm
00000000000013d0 <dalli>:
    13d0:   endbr64
    13d4:   test   %esi,%esi
    13d6:   jle    1400 <dalli+0x30>
    13d8:   movslq %esi,%rsi
    13db:   xor    %edx,%edx
    13dd:   lea    (%rdi,%rsi,4),%rcx
    13e1:   nopl   0x0(%rax)
    13e8:   movslq (%rdi),%rax
    13eb:   cmp    $0x7f,%eax
    13ee:   jle    13f3 <dalli+0x23>
    13f0:   add    %rax,%rdx
    13f3:   add    $0x4,%rdi
    13f7:   cmp    %rcx,%rdi
    13fa:   jne    13e8 <dalli+0x18>
    13fc:   mov    %rdx,%rax
    13ff:   ret
```

Doğal `-O2` derlemesinde ise aynı kaynak kodu şuna dönüşür:

```asm
00000000000013d0 <dalli>:
    13d0:   endbr64
    13d4:   test   %esi,%esi
    13d6:   jle    1408 <dalli+0x38>
    13d8:   movslq %esi,%rsi
    13db:   xor    %edx,%edx
    13dd:   lea    (%rdi,%rsi,4),%rsi
    13e1:   nopl   0x0(%rax)
    13e8:   movslq (%rdi),%rax
    13eb:   mov    %rax,%rcx
    13ee:   add    %rdx,%rax
    13f1:   cmp    $0x7f,%ecx
    13f4:   cmovg  %rax,%rdx
    13f8:   add    $0x4,%rdi
    13fc:   cmp    %rdi,%rsi
    13ff:   jne    13e8 <dalli+0x18>
    1401:   mov    %rdx,%rax
    1404:   ret
```

`cmovg` komutu bir atlama değildir; koşul yazmaçlar arasında bir kopyalama olarak yürütülür. İşlemci hangi yolu seçeceğini tahmin etmez. Bu iki kod parçasının farkı, deneyin tüm anlamıdır.

Kontrollü derlemeyi bir kez çalıştırdığımızda çıktı şöyle oluyor (satırlar sırasıyla: fonksiyon, dizi ve en küçük süre, medyan süre, eleman başına nanosaniye, toplam):

```term
$ ./dal_kontrollu kontrollu
derleme,fonksiyon,dizi,en_az_ms,medyan_ms,ns_per_eleman,toplam
kontrollu,dalli,sirasiz,289.23,307.04,2.207,3157346
kontrollu,dalli,sirali,52.19,57.09,0.398,3157346
kontrollu,dalsiz,sirasiz,60.95,64.94,0.465,3157346
kontrollu,dalsiz,sirali,66.49,68.24,0.507,3157346
```

Aynı deneyi iki koşuda tekrarlayıp ortalamasını aldığımızda eleman başına süreler şöyle çıktı:

| Derleme | Fonksiyon | Sıralı dizi (ns/eleman) | Sırasız dizi (ns/eleman) | Oran |
|---|---|---|---|---|
| Kontrollü (dal korunmuş) | dalli | 0,37 | 2,12 | yaklaşık 5,7 |
| Kontrollü | dalsiz | 0,43 | 0,43 | 1,0 |
| Doğal -O2 | dalli | 0,42 | 0,42 | 1,0 |
| Doğal -O2 | dalsiz | 0,41 | 0,42 | 1,0 |

Tablo üç şey söylüyor. Birincisi, dallı toplamada sırasız dizi, sıralı diziden yaklaşık altı kat yavaş. Bunun nedeni şudur: sıralı dizide 128'den küçük elemanlar ve büyük elemanlar uzun bloklar halinde gelir, dal tahmincisi her blokta yalnızca birkaç kez yanılır. Sırasız dizide ise dal, rastgele bir bit dizisi gibi davranır ve en iyi tahminci bile yaklaşık yarısında yanılır. İkincisi, dalsız sürümde iki dizi de aynı hızdadır; çünkü dal yoktur. Üçüncüsü ve belki en önemlisi, doğal `-O2` derlemesinde fark kaybolmuştur: derleyici dalı zaten `cmov`'a çevirmiştir. Dal tahmininin etkisi, kodun gerçekte hangi komutlara derlendiğine bağlıdır; kaynağa bakıp "bu dallı" demek yetmez, assembly'ye bakmak gerekir.

::: dikkat
Bu deneyde "dalsız" sürümün her zaman daha hızlı olduğunu söylemiyoruz. Dalın tahmini başarılıysa (örneğin neredeyse her zaman alınıyorsa) dallı kod daha hızlıdır, çünkü dalsız sürüm her elemanda bütün işi yapar. Dalsız programlama, tahmin edilemeyen dallarda ve gerçekten yarı yarıya rastgele koşullarda anlamlıdır.
:::

Şekil 24.5, bu sonuçları grafik olarak gösteriyor. Grafik, ölçüm dosyasındaki iki koşunun ortalamasını çizer.

![Şekil 24.5: Dal tahmininin ölçümü. Kontrollü dallı sürümde sırasız dizi (kırmızı) sıralı diziden (lacivert) yaklaşık altı kat yavaştır. Dalsız sürüm ve doğal -O2 derlemesi her iki dizide de aynı hızdadır.](gorseller/b24_dal.png)

### Dalsız programlama

Dalsız programlama, koşulu bir dal yerine aritmetikle ya da koşullu taşımayla ifade etmektir. Bu, tahmin edilemeyen dallardan kaçınmanın yoludur. Üç temel araç vardır: bir karşılaştırmanın sonucu olan 0 ya da 1 değerini bir maskeye dönüştürmek (`-(x >= 128)` 0 ya da -1 verir, yani bütün bitleri 1 olan bir maske), maskeyle AND/XOR yaparak değer seçmek, ve derleyicinin `cmov` üretmesine güvenmek.

Aşağıdaki küçük program, mutlak değer ve maksimum için dallı ve dalsız sürümleri yazıyor, bir milyon rastgele çiftte karşılaştırıyor.

```c
/* Dalsız mutlak değer ve maksimum; dallı sürümle karşılaştırma */
#include <stdio.h>
#include <stdint.h>

/* dallı sürümler */
int mutlak_dalli(int x)
{
    return x < 0 ? -x : x;
}

int maks_dalli(int a, int b)
{
    return a > b ? a : b;
}

/* dalsız sürümler: işaret maskesi ile */
int mutlak_dalsiz(int x)
{
    int m = x >> 31;             /* 0 ya da -1 (işaretli kaydırma) */
    return (x ^ m) - m;
}

int maks_dalsiz(int a, int b)
{
    int m = -(a < b);            /* a<b ise -1, değilse 0 */
    return a ^ ((a ^ b) & m);
}

```

```c
int main(void)
{
    uint32_t durum = 42;  /* sabit tohum: hep aynı sayılar */
    long hata = 0;
    for (int i = 0; i < 1000000; i++) {
        durum ^= durum << 13;
        durum ^= durum >> 17;
        durum ^= durum << 5;
        int a = (int)(durum % 2001u) - 1000;   /* -1000..1000 */
        durum ^= durum << 13;
        durum ^= durum >> 17;
        durum ^= durum << 5;
        int b = (int)(durum % 2001u) - 1000;
        if (mutlak_dalli(a) != mutlak_dalsiz(a)) hata++;
        if (maks_dalli(a, b) != maks_dalsiz(a, b)) hata++;
    }
    printf("uyusmazlik=%ld\n", hata);
    printf("mutlak(-7)=%d maks(3,9)=%d\n",
           mutlak_dalsiz(-7), maks_dalsiz(3, 9));
    return 0;
}
```

```term
$ ./dalsiz_ornek
uyusmazlik=0
mutlak(-7)=7 maks(3,9)=9
```

Program hiçbir uyuşmazlık bildirmedi. Yani dalsız sürümler, dallı olanların tam karşılığıdır. Dikkat edilecek nokta, derleyicinin `mutlak_dalli` ve `maks_dalsiz` yazımlarını `-O2`'de de `cmov`'a dönüştürmesidir:

```asm
mutlak_dalli:
        endbr64
        movl    %edi, %eax
        negl    %eax
        cmovs   %edi, %eax
        ret
```

```asm
maks_dalsiz:
        endbr64
        cmpl    %esi, %edi
        movl    %esi, %eax
        cmovge  %edi, %eax
        ret
```

Derleyici hem dallı hem dalsız yazılmış kodu aynı koşullu komutlara çevirebiliyor. Bu nedenle dalsız yazmanın hız kazandırması, derleyicinin dalı zaten kaldırmadığı durumlarda anlamlıdır. Bunun için kendi kodunu hem dallı hem dalsız derlemek ve assembly'sini okumak en sağlam yöntemdir.

`mutlak_dalsiz` fonksiyonu, işaretli sağa kaydırma (`x >> 31`) ile bir maske üretir. `(x ^ m) - m` ifadesi negatif sayıda tümleyeni alır ve 1 ekler, pozitif sayıya dokunmaz. Burada bir tuzak var: `INT_MIN` için `-INT_MIN` taşar ve bu tanımsız davranıştır (UB). İşaretli bir tamsayı taşması, C standardında tanımsızdır; derleyici bunu varsayarak kodu değiştirebilir. Ayrıca işaretli sayıya `>>` uygulamak uygulamaya bağlıdır (implementation-defined); GCC ve Clang aritmetik kaydırma yapar, ama taşınabilir kodda bunu bilerek kullanmalısın.

::: ipucu
Dalsız kod okunabilirliği düşürebilir. Önce ölç, sonra dönüştür. Bir döngüde dal yanlış tahmin oranı yüksekse ve gerçekten bu döngü darboğazsa, dalsız sürümü dene. Değilse, okunabilir dallı kod daha iyidir; derleyici zaten birçok durumda bunu senin yerine yapar.
:::

## 24.7 Süperskaler ve sıra dışı yürütme: komut düzeyi paralellik

Boru hattı, komutları üst üste bindirerek çevrim başına bir komut tamamlar. Peki bir çevrimde birden fazla komut tamamlanabilir mi? Evet: **süperskaler (superscalar)** işlemciler bir çevrimde birden çok komutu getirir, çözer ve yürütür. Bunun için donanımda birden çok ALU, birden çok yükleme/saklama birimi ve birden çok kayan nokta birimi bulunur. Bir çevrimde kaç komut başlatılabildiğine **genişlik (issue width)** denir.

Süperskaler yürütmenin sınırı, programdaki **komut düzeyi paralellik (ILP, Instruction-Level Parallelism)**'tir. İki komut birbirinden bağımsızsa, aynı çevrimde ya da üst üste yürütülebilirler. Bağımlıysa, ikincisi birincinin sonucunu beklemek zorundadır. Bir programın ILP'si, bu bağımlılık grafiğinin ne kadar geniş ve kısa olduğunu gösterir.

Bağımlılığın kendisi de iki farklı türdedir. **Gerçek bağımlılık (RAW, Read After Write)** tam anlamıyla veri akışıdır: `b = a + 1; c = b * 2;` gibi, ikinci komut birincinin sonucunu okur. Bu bağımlılık kaçınılmazdır. **Sahte bağımlılıklar (WAR ve WAW)** ise yalnızca aynı yazmacı yeniden kullanmaktan doğar: iki bağımsız hesap aynı `eax`'i kullanıyorsa, sanki birbirine bağlıymışlar gibi sıralanmak zorunda kalabilirler. Modern işlemcilerin **yazmaç yeniden adlandırma (register renaming)** donanımı, her yeni yazmaç yazımını fiziksel bir yeni yuvaya koyar ve bu sahte bağımlılıkları ortadan kaldırır.

**Sıra dışı yürütme (out-of-order execution)** ise daha ileri gider: işlemci, bekleyen bir komutun arkasındaki bağımsız komutları, programdaki sırayı bozarak, o anda çalıştırabilir. Komutlar bir **yeniden sıralama tamponunda (ROB, Reorder Buffer)** tutulur ve sonuçlar programın sırasıyla emekliye ayrılır; böylece dışarıdan bakıldığında program sıralı çalışmış gibi görünür. Bu, işlemcinin içindeki en karmaşık mekanizmalardan biridir ve genel bilgi olarak bilinen tasarım ilkelerine dayanır.

Bu ilkeleri ölçmek için bir toplama döngüsü kullanacağız. Toplamanın sırası önemlidir: her toplama bir öncekinin sonucunu bekliyorsa, işlemci tek bir zincirle sınırlıdır. Aynı işi dört bağımsız toplayıcıya (akümülatöre) bölersek, dört zincir paralel ilerleyebilir. Burada iki noktaya dikkat etmek gerekir. Birincisi, kayan nokta toplaması birleşmeli değildir: `(a+b)+c` ile `a+(b+c)` farklı sonuç verebilir. GCC, `-ffast-math` gibi bir bayrak vermeden kayan nokta toplamasını yeniden sıralamaz. Bu yüzden akümülatörleri kendimiz ayırdık. İkincisi, toplamayı tam sayı değerlerle yaptık (0 ile 999 arası, tam sayı olarak saklanan `double`lar); böylece toplam bütün sıralarda aynı kalır ve doğruluk kontrolü kesin olur. Dizi 1024 elemanlıktır ve L1 önbelleğine sığar; böylece ölçüm bellek hızına değil işlemci yürütmesine bağlı kalır (önbellek hiyerarşisi Bölüm 25'in konusudur).

```c
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define N 1024                /* 8 KB: tamamen L1 önbelleğinde */
#define TEKRAR 200000
#define OLCUM 7

static uint64_t durum = 42;

static uint32_t rnd(void)
{
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (uint32_t)(durum >> 32);
}

static volatile double sink;

/* tek zincir: her toplama bir öncekinin sonucunu bekler */
__attribute__((noinline))
double topla1(const double *a, int n)
{
    double s0 = 0.0;
    for (int i = 0; i < n; i++)
        s0 += a[i];
    return s0;
}
```

```c

__attribute__((noinline))
double topla2(const double *a, int n)
{
    double s0 = 0.0, s1 = 0.0;
    for (int i = 0; i < n; i += 2) {
        s0 += a[i];
        s1 += a[i + 1];
    }
    return s0 + s1;
}

__attribute__((noinline))
double topla4(const double *a, int n)
{
    double s0 = 0.0, s1 = 0.0, s2 = 0.0, s3 = 0.0;
    for (int i = 0; i < n; i += 4) {
        s0 += a[i];
        s1 += a[i + 1];
        s2 += a[i + 2];
        s3 += a[i + 3];
    }
    return (s0 + s1) + (s2 + s3);
}
```

```c

__attribute__((noinline))
double topla8(const double *a, int n)
{
    double s0 = 0.0, s1 = 0.0, s2 = 0.0, s3 = 0.0;
    double s4 = 0.0, s5 = 0.0, s6 = 0.0, s7 = 0.0;
    for (int i = 0; i < n; i += 8) {
        s0 += a[i];
        s1 += a[i + 1];
        s2 += a[i + 2];
        s3 += a[i + 3];
        s4 += a[i + 4];
        s5 += a[i + 5];
        s6 += a[i + 6];
        s7 += a[i + 7];
    }
    return ((s0 + s1) + (s2 + s3)) + ((s4 + s5) + (s6 + s7));
}
```

```c

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static int cmp_dbl(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

typedef double (*fn_t)(const double *, int);

static void olc(const char *derleme, const char *ad, int akum,
                fn_t f, const double *a, double *bek)
{
    double t[OLCUM], sonuc = 0.0;
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_ms();
        for (int r = 0; r < TEKRAR; r++)
            sonuc = f(a, N);
        t[k] = simdi_ms() - b;
        sink = sonuc;
    }
    if (*bek < 0.0)
        *bek = sonuc;
    if (sonuc != *bek) {
        fprintf(stderr, "HATA: %s toplam uyusmuyor\n", ad);
        exit(1);
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    double eleman = (double)TEKRAR * N;
    printf("%s,%s,%d,%.2f,%.2f,%.4f\n", derleme, ad, akum,
           t[0], t[OLCUM / 2], t[0] * 1e6 / eleman);
}
```

```c

int main(int argc, char **argv)
{
    const char *derleme = argc > 1 ? argv[1] : "bilinmiyor";
    static double a[N];
    for (int i = 0; i < N; i++)
        a[i] = (double)(rnd() % 1000);   /* tam sayı: toplam kesin */

    double bek = -1.0;
    printf("derleme,fonksiyon,akumulator,en_az_ms,"
           "medyan_ms,ns_per_eleman\n");
    olc(derleme, "topla1", 1, topla1, a, &bek);
    olc(derleme, "topla2", 2, topla2, a, &bek);
    olc(derleme, "topla4", 4, topla4, a, &bek);
    olc(derleme, "topla8", 8, topla8, a, &bek);
    return 0;
}
```

Dört akümülatörlü sürümün makine kodunu inceleyelim. Derleyici, `topla4` içindeki dört toplamayı dört ayrı `addsd` komutu olarak üretmiştir (paketlenmiş `addpd` değil), yani dört bağımsız zincir vardır:

```asm
00000000000013e0 <topla4>:
    13e0:   endbr64
    13e4:   test   %esi,%esi
    13e6:   jle    1440 <topla4+0x60>
    13e8:   sub    $0x1,%esi
    13eb:   pxor   %xmm2,%xmm2
    13ef:   movapd %xmm2,%xmm1
    13f3:   shr    $0x2,%esi
    13f6:   movapd %xmm2,%xmm3
    13fa:   movapd %xmm2,%xmm0
    13fe:   shl    $0x5,%rsi
    1402:   lea    0x20(%rdi,%rsi,1),%rax
    1407:   nopw   0x0(%rax,%rax,1)
    1410:   addsd  (%rdi),%xmm0
    1414:   addsd  0x8(%rdi),%xmm3
    1419:   add    $0x20,%rdi
    141d:   addsd  -0x10(%rdi),%xmm1
    1422:   addsd  -0x8(%rdi),%xmm2
    1427:   cmp    %rdi,%rax
    142a:   jne    1410 <topla4+0x30>
    142c:   addsd  %xmm3,%xmm0
    1430:   addsd  %xmm2,%xmm1
    1434:   addsd  %xmm1,%xmm0
    1438:   ret
```

Döngünün gövdesinde `addsd` komutları farklı kayan nokta yazmaçlarında (`xmm0`, `xmm1`, `xmm2`, `xmm3`) duruyor. Her biri yalnızca kendi zincirinin önceki değerini bekler; dört zincir birbirini beklemez. Bu, derleyicinin bizim yapısal değişikliğimize uyduğunu ve ek bir dönüşüm uygulamadığını gösterir.

Programı iki koşuda çalıştırdığımızda, akümülatör sayısına göre eleman başına süre şöyle çıktı:

| Akümülatör | Ortalama (ns/eleman) | Birinciye göre hızlanma |
|---|---|---|
| 1 (tek zincir) | 0,570 | 1,00 |
| 2 | 0,298 | 1,91 |
| 4 | 0,152 | 3,75 |
| 8 | 0,105 | 5,44 |

Tablo, bağımlı zincirin ne kadar pahalı olduğunu gösteriyor. Tek zincirden dörde geçişte yaklaşık dört kat kazanç var; sekize çıkınca kazanç yaklaşık beş buçuğa ulaşıyor. Kazanç doğrusal değil, çünkü bir noktadan sonra yürütme birimlerinin kendi kapasitesi sınır olur: ne kadar bağımsız zincir eklersen ekle, aynı çevrimde yalnızca belirli sayıda toplama başlatılabilir. Bu tavanı, Çözümlü Örnek 4'te basit bir model kurarak ayrıntılı hesaplayacağız.

Şekil 24.6, aynı ölçümü grafik olarak gösteriyor.

![Şekil 24.6: Toplama döngüsünde komut düzeyi paralellik. Tek bağımlı zincir (kırmızı) en yavaş; akümülatör sayısı arttıkça eleman başına süre düşer, ama kazanç sekiz akümülatörde birden sınırlanır.](gorseller/b24_ilp.png)

Burada bir gerçek daha var: aynı mantıkla bu kodu önbellek dışına taşıdığımızda (büyük bir dizi), kazanç bellek hızına takılır. Hız kazanmak için kod yazarken hangi kısmın darboğaz olduğunu bilmek gerekir. Bu, performans mühendisliğinin ilk sorusudur.

::: dikkat
Bu deneyin tek bir dizide ve tek bir makinede yapıldığını unutma. Sekiz akümülatörlü sürümün kazancı, işlemcinin toplama birimlerinin sayısına ve yazmaç sayısına bağlıdır; başka bir işlemcide sonuç farklı olabilir. Ölçüm tekrarlanabilir, ama genelleme yapmadan önce kendi makinende aynı programı çalıştır.
:::

## 24.8 SIMD: tek komut, çok veri

Süperskaler yürütme, farklı komutları aynı çevrimde çalıştırır. **SIMD (Single Instruction, Multiple Data)** ise tek bir komutun bir yazmaçtaki birden çok veri üzerinde aynı işlemi yapmasıdır. Bir `float` dizisini toplarken her elemanı ayrı ayrı işlemek yerine, dört ya da sekiz elemanı bir yazmaçta tutup tek komutla toplayabilirsin.

x86-64'te SIMD yazmaçları ve komutları birkaç nesille gelişti. SSE, 128 bitlik `xmm` yazmaçlarını ve dört tek duyarlıklı kayan nokta sayısını (`float`) aynı anda işler; x86-64'te temel ISA'nın parçasıdır, yani her x86-64 işlemcide bulunur. AVX, yazmaçları 256 bite (`ymm`) genişletir ve sekiz `float` işler. AVX2, 256 bit tam sayı işlemlerini ekler ve birçok yeni komut getirir. FMA (Fused Multiply-Add), çarpma ve toplamayı tek bir yuvarlamayla yapar ve ayrı bir CPUID özelliği olarak sorgulanır. AVX-512 ise 512 bit yazmaçlar sunar; bu makinede `/proc/cpuinfo` içinde `avx2` bayrağı var, `avx512f` yok.

Şekil 24.7, aynı sekiz float üzerinde üç yaklaşımın kaç komutla çalıştığını gösteriyor.

![Şekil 24.7: Skaler, SSE ve AVX2 ile işlenen eleman sayısı. Aynı sekiz elemanlık iş skaler yolda sekiz, SSE'de iki, AVX2'de bir komutla yapılır.](gorseller/b24_simd_serit.png)

İki yol vardır. Birincisi, **otomatik vektörleştirme**: derleyici döngüyü SIMD komutlarına kendisi çevirir. `-O3` bunu açar; GCC 12 ve sonrasında `-O2` de sınırlı biçimde vektörleştirme yapabilir. Hangi döngülerin vektörleştiğini `-fopt-info-vec-optimized` ile görebilirsin. İkincisi, **intrinsics**: C'de `_mm256_loadu_ps` gibi fonksiyonlar, belirli bir SIMD komutunu doğrudan çağırmanı sağlar. Bu yöntem daha fazla kontrol verir, ama daha fazla kod ve daha fazla dikkat gerektirir.

Deneyde `y[i] = a * x[i] + y[i]` (AXPY, bir sabitle bir vektörü çarpıp başka bir vektöre ekleme) işlemini üç yolla yaptık: skaler referans (vektörleştirme kapalı), `-O3` ile otomatik vektörleştirilmiş ve elle yazılmış AVX2 + FMA. Skaler referans, ayrı bir çeviri biriminde tutuldu ve `-fno-tree-vectorize` ile derlendi; böylece derleyicinin onu gizlice vektörleştirmediğinden emin olduk.

```c
/* SIMD deneyi: skaler referans (vektörleşme kapalı derlenir) */
void axpy_skaler(float *y, const float *x, float a, int n)
{
    for (int i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}
```

```c
#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h>

#define N 2048                /* 2 x 8 KB: L1 önbelleğinde kalır */
#define TEKRAR 50000
#define OLCUM 5

void axpy_skaler(float *y, const float *x, float a, int n);

/* Otomatik vektörleşme adayı: -O3 ile SSE kodu üretebilir */
__attribute__((noinline))
void axpy_oto(float *y, const float *x, float a, int n)
{
    for (int i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}

/* Elle yazılmış AVX2 + FMA: 8 float tek yazmaçta (256 bit) */
__attribute__((noinline, target("avx2,fma")))
void axpy_avx2(float *y, const float *x, float a, int n)
{
    __m256 va = _mm256_set1_ps(a);
    int i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256 vx = _mm256_loadu_ps(x + i);
        __m256 vy = _mm256_loadu_ps(y + i);
        vy = _mm256_fmadd_ps(va, vx, vy);
        _mm256_storeu_ps(y + i, vy);
    }
    for (; i < n; i++)        /* kalan elemanlar */
        y[i] = a * x[i] + y[i];
}

```

```c
static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static int cmp_dbl(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static float x[N], y0[N], y[N];

typedef void (*fn_t)(float *, const float *, float, int);

```

```c
static void olc(const char *derleme, const char *ad, fn_t f)
{
    double t[OLCUM];
    /* doğruluk: tek geçiş, tam sayı değerler (kesin toplanır) */
    for (int i = 0; i < N; i++)
        y[i] = y0[i];
    f(y, x, 0.5f, N);
    for (int i = 0; i < N; i++) {
        float bek = 0.5f * x[i] + y0[i];
        if (y[i] != bek) {
            fprintf(stderr, "HATA: %s i=%d\n", ad, i);
            exit(1);
        }
    }
    for (int k = 0; k < OLCUM; k++) {
        for (int i = 0; i < N; i++)
            y[i] = y0[i];
        double b = simdi_ms();
        for (int r = 0; r < TEKRAR; r++)
            f(y, x, 0.5f, N);
        t[k] = simdi_ms() - b;
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    double eleman = (double)TEKRAR * N;
    printf("%s,%s,%.2f,%.4f\n", derleme, ad, t[0],
           t[0] * 1e6 / eleman);
}
```

```c

int main(int argc, char **argv)
{
    const char *derleme = argc > 1 ? argv[1] : "bilinmiyor";
    for (int i = 0; i < N; i++) {
        x[i] = (float)(i % 37);
        y0[i] = (float)(i % 11);
    }
    printf("derleme,surum,en_az_ms,ns_per_eleman\n");
    olc(derleme, "skaler", axpy_skaler);
    olc(derleme, "oto_vektor", axpy_oto);
    if (__builtin_cpu_supports("avx2") &&
        __builtin_cpu_supports("fma"))
        olc(derleme, "avx2_fma", axpy_avx2);
    else
        printf("%s,avx2_fma,atlandi,0\n", derleme);
    return 0;
}
```

`axpy_avx2` içinde `__attribute__((target("avx2,fma")))` niteliği, yalnızca bu fonksiyonun AVX2 ve FMA komutlarıyla derlenmesini sağlar; böylece dosyanın geri kalanı genel x86-64 olarak kalır. Çağrıdan önce `__builtin_cpu_supports` ile işlemcinin bu komutları desteklediğini kontrol ediyoruz; desteklemiyorsa program çalışmaya devam etmek için skaler yola düşebilir. Bu, çalışma zamanında yapılan **dinamik dağıtımın (dispatch)** en basit biçimidir.

FMA kullanmanın bir sonucu var: `a*x + y` iki ayrı yuvarlamayla değil, tek yuvarlamayla hesaplanır. Yani sonuç, skaler yoldan bit düzeyinde farklı olabilir. Bu yüzden doğruluk kontrolünü tam sayı değerlerle yaptık; bu değerlerde iki yöntem de kesin sonuç verir ve `!=` karşılaştırması güvenilirdir.

`-O3` ile derlediğimizde derleyici `axpy_oto` döngüsünü vektörleştirdi. Derleyici raporunun ilgili satırları şöyle (uzun "versioned" yan satırları yer kazanmak için çıkarıldı):

```term
$ gcc -O3 -fopt-info-vec-optimized -c simd.c
simd.c:17:23: optimized: loop vectorized using 16 byte vectors
simd.c:17:23: optimized: loop vectorized using 8 byte vectors
simd.c:33:14: optimized: loop vectorized using 32 byte vectors
simd.c:33:14: optimized: loop vectorized using 16 byte vectors
simd.c:85:23: optimized: loop vectorized using 16 byte vectors
```

Rapor, genel x86-64 hedefinde (`-march` verilmeden) derleyicinin yalnızca SSE2'nin 128 bitlik vektörlerini kullandığını gösteriyor (`16 byte vectors`). AVX2 yalnızca `target` niteliği olan fonksiyonda (`axpy_avx2`) 32 baytlık vektörlere izin veriliyor (`33:14` satırı). Yani aynı derleyici bile hedef ISA'ya göre farklı genişlikte kod üretir; bu, 24.1'deki ISA-mikromimari ayrımının bir örneğidir.

Ölçümü iki biçimde yaptık: birincisinde derleme ve bağlama normal haliyle yaptık, ikincisinde her fonksiyonu 64 baytlık sınırlara hizaladık (`-falign-functions=64 -falign-loops=64`). Hizalamasız ölçümde beklenmedik bir sonuç çıktı: aynı skaler kod, iki derlemede iki kat farklı hızda çalıştı. Assembly'yi inceleyince fark anlaşıldı: iki ikilide de döngünün komutları aynıydı, yalnızca bağlayıcının fonksiyonu yerleştirdiği adres farklıydı. Hızlı derlemede döngü tek bir 64 baytlık blok içinde kalıyor, yavaş derlemede ise döngünün sonu bir blok sınırını geçiyordu:

```asm
0000000000002af0 <axpy_skaler>:
    2af0:   endbr64
    2af4:   test   %edx,%edx
    2af6:   jle    2b24 <axpy_skaler+0x34>
    2af8:   movslq %edx,%rdx
    2afb:   xor    %eax,%eax
    2afd:   shl    $0x2,%rdx
    2b01:   nopl   0x0(%rax)
    2b08:   movss  (%rsi,%rax,1),%xmm1
    2b0d:   mulss  %xmm0,%xmm1
    2b11:   addss  (%rdi,%rax,1),%xmm1
    2b16:   movss  %xmm1,(%rdi,%rax,1)
    2b1b:   add    $0x4,%rax
    2b1f:   cmp    %rax,%rdx
```

```asm
0000000000002710 <axpy_skaler>:
    2710:   endbr64
    2714:   test   %edx,%edx
    2716:   jle    2744 <axpy_skaler+0x34>
    2718:   movslq %edx,%rdx
    271b:   xor    %eax,%eax
    271d:   shl    $0x2,%rdx
    2721:   nopl   0x0(%rax)
    2728:   movss  (%rsi,%rax,1),%xmm1
    272d:   mulss  %xmm0,%xmm1
    2731:   addss  (%rdi,%rax,1),%xmm1
    2736:   movss  %xmm1,(%rdi,%rax,1)
    273b:   add    $0x4,%rax
    273f:   cmp    %rax,%rdx
```

Bu, kesin bir kanıt değil, bir gözlem ve makul bir açıklamadır: perf ve donanım sayaçları olmadığı için komut getirme ve önbellek davranışını doğrudan ölçemedik. Ama hizalama eklendiğinde, iki derlemedeki skaler döngü de aynı hıza (0,21 ns/eleman) geldi. Hizalamasız ölçümde ayrıca AVX2 sürümü de belirgin biçimde yavaştı (0,054 ns'ye karşı 0,029). Sonuç şudur: **kod yerleşimi, bu makinede, ölçüm sonucunu iki kata kadar değiştirebilir.** Güvenilir kıyas yapmak için ölçtüğün kodu hizala ve birden çok derlemeyle karşılaştır.

Hizalı ölçümlerin sonuçları şöyle (beş koşunun en küçük süresi, eleman başına nanosaniye):

| Sürüm | Derleme | ns/eleman | Skalere göre hızlanma |
|---|---|---|---|
| Skaler | -O3 (hizalı) | 0,210 | 1,0 |
| Otomatik vektör (SSE) | -O3 (hizalı) | 0,063 | yaklaşık 3,3 |
| AVX2 + FMA | -O3 (hizalı) | 0,029 | yaklaşık 7,2 |

Şekil 24.8, hem hizalı sonuçları hem de hizalamanın skaler döngüye etkisini gösteriyor.

![Şekil 24.8: SIMD ölçümleri. Sol panelde hizalı -O3 derlemesinde skaler, otomatik SSE ve AVX2 + FMA sürümlerinin eleman başına süreleri. Sağ panelde aynı skaler kodun hizalamasız iki derlemede (kırmızı) ve hizalı iki derlemede (lacivert) süreleri; hizalı olunca fark kayboluyor.](gorseller/b24_simd_olcum.png)

Dikkat edilecek bir nokta daha var: bu deneyde dizi 2048 `float`tır, yani 16 KB; iki dizi birlikte L1 önbelleğine sığar. Dizi büyüdüğünde SIMD'nin sağladığı hız, bellekten veri getirme hızına takılır. SIMD yalnızca hesap yoğun işlerde sihirli bir hızlandırmadır; bellek bağlı işlerde (örneğin büyük vektörleri toplamak) kazanç azalır. Bu, Bölüm 25'te göreceğin bellek hiyerarşisinin doğrudan sonucudur.

Gömülü dünyada bu fikrin karşılığı DSP komutlarıdır. Cortex-M4 çekirdeği, tek bir komutla çarpma ve toplama yapabilen ve kenetlenmiş (saturating) aritmetik sunan DSP komut kümesini içerir. Bu, genel bilgi olarak bir sensör filtresinin ya da FFT'nin iç döngüsünü hızlandırmak için kullanılır. Hangi komutların bir hedef için mevcut olduğunu öğrenmenin yolu, o işlemcinin referans kılavuzunu okumaktır.

## 24.9 Saat, IPC ve ölçüm: döngüleri nasıl sayarsın?

Bu bölümün başında "3 GHz" dedik. Bu rakam, işlemcinin saat sinyalinin saniyede üç milyar kez değiştiğini söyler; yani bir çevrim yaklaşık üç nanosaniyedir. Bir komutun kaç çevrim sürdüğü ise programın hızını belirler. Bunun bir ölçüsü **IPC (Instructions Per Cycle, çevrim başına komut)** ya da tersi **CPI (Cycles Per Instruction)**'dır. Yüksek IPC, boru hattının ve süperskalar birimlerin iyi beslendiği anlamına gelir; düşük IPC ise bellek beklemesi, dal yanlış tahmini ya da bağımlılık zinciri gibi bir darboğaz olduğunu gösterir.

Bu iki sayıyı ölçmenin en doğru yolu donanım performans sayaçlarıdır: Linux'ta `perf stat` komutu, işlemcinin gerçekten yürüttüğü komut sayısını (instructions retired) ve çevrim sayısını (cycles) okur. Bu bölümü hazırlarken bu makinede `perf` yoktu ve `sudo` ile kurulum yapamadık. Bu yüzden IPC'yi ölçemedik; burada elde edebildiğimiz şeyler, zaman ve oran üzerinden çıkarılan tahminlerdir.

Zaman ölçümünde iki araç kullandık. `clock_gettime(CLOCK_MONOTONIC)` işletim sistemine bağlı, nanosaniye çözünürlüklü bir saat verir; ölçümlerimizde varsayılan olarak bunu kullandık. `rdtsc` komutu ise **TSC (Time Stamp Counter)** değerini okur. TSC, sabit bir hızla artar; bu hız işlemcinin o anki çekirdek frekansı değildir, genellikle nominal (taban) frekansa karşılık gelir. Ölçümümüzde TSC hızı 3,34 ile 3,41 GHz arasında çıktı; bu, çekirdek frekansından ayrı bir değerdir.

Çekirdek frekansını tahmin etmek için bir numara kullanabiliriz. Bir `add $1, %rax` komutu, bir öncekinin sonucunu beklediği için bağımlı bir zincir oluşturur. Basit bir tamsayı toplamasının gecikmesi genel bilgi olarak bir çevrimdir. Bu varsayım doğruysa, bin tane bağımlı `add` içeren bir döngünün süresi, çekirdek frekansını verir. Varsayım bozulursa (ör. bazı işlemciler bu tür komutları özel olarak hızlandırabilir) tahmin de bozulur; bu nedenle sonucu bir kesin değer değil, bir yaklaşım olarak okumalısın.

```c
/* Saat frekansı tahmini, rdtsc, sistem çağrısı maliyeti (Linux) */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <x86intrin.h>

#define ZINCIR_TEKRAR 1000000   /* her turda 1000 bağımlı add */
#define OLCUM 5
#define SYS_TEKRAR 3000000

static volatile long sink;

static double simdi_s(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}

/* 1000 bağımlı 'add': her biri bir öncekinin sonucunu bekler */
static inline uint64_t zincir1000(uint64_t x)
{
    __asm__ volatile(
        ".rept 1000\n\t"
        "add $1, %0\n\t"
        ".endr"
        : "+r"(x));
    return x;
}

__attribute__((noinline))
static long kucuk(long x)
{
    return x + 1;
}

```

```c
static int cmp_dbl(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(void)
{
    double t[OLCUM], ts[OLCUM], sys_t[OLCUM], cag_t[OLCUM];
    double dt[OLCUM];
    uint64_t tsc0, tsc1;
    uint64_t x = 0;

    /* 1) bağımlı add zinciri: varsayım her add 1 çevrim */
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        for (long r = 0; r < ZINCIR_TEKRAR; r++)
            x = zincir1000(x);
        t[k] = simdi_s() - b;
    }
    /* 2) aynı döngü rdtsc ile */
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        tsc0 = __rdtsc();
        for (long r = 0; r < ZINCIR_TEKRAR; r++)
            x = zincir1000(x);
        tsc1 = __rdtsc();
        ts[k] = simdi_s() - b;
        sys_t[k] = (double)(tsc1 - tsc0);
    }
```

```c
    /* 3) sistem çağrısı getppid ve doğrudan çağrı */
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        for (long r = 0; r < SYS_TEKRAR; r++)
            sink = syscall(SYS_getppid);
        cag_t[k] = simdi_s() - b;
    }
    for (int k = 0; k < OLCUM; k++) {
        double b = simdi_s();
        for (long r = 0; r < SYS_TEKRAR; r++)
            sink = kucuk((long)r);
        dt[k] = simdi_s() - b;
    }
    qsort(t, OLCUM, sizeof t[0], cmp_dbl);
    qsort(ts, OLCUM, sizeof ts[0], cmp_dbl);
    qsort(sys_t, OLCUM, sizeof sys_t[0], cmp_dbl);
    qsort(cag_t, OLCUM, sizeof cag_t[0], cmp_dbl);
    qsort(dt, OLCUM, sizeof dt[0], cmp_dbl);

    double adim = (double)ZINCIR_TEKRAR * 1000.0;
    printf("olcum,deger\n");
    printf("add_zinciri_en_az_s,%.4f\n", t[0]);
    printf("frekans_tahmini_GHz,%.3f\n", adim / t[0] / 1e9);
    printf("tsc_hizi_GHz,%.3f\n", sys_t[0] / ts[0] / 1e9);
    printf("syscall_getppid_ns,%.2f\n", cag_t[0] * 1e9 / SYS_TEKRAR);
    printf("dogrudan_cagri_ns,%.2f\n", dt[0] * 1e9 / SYS_TEKRAR);
    (void)x;
    return 0;
}
```

Programın bir koşudaki çıktısı şöyle:

```term
$ ./cpu_sayac
olcum,deger
add_zinciri_en_az_s,0.2175
frekans_tahmini_GHz,4.598
tsc_hizi_GHz,3.347
syscall_getppid_ns,197.33
dogrudan_cagri_ns,0.99
```

Programı iki kez daha çalıştırdığımızda (toplam üç koşu) çekirdek frekansı tahmini 4,6 ile 4,8 GHz arasında kaldı; bu aralık, sanal makinenin ve turbo davranışının gürültüsüdür. Üç ayrı koşuda da değerler birkaç yüzde dalgalandı. Bu dalgalanma, ölçümde tekrarın neden önemli olduğunu gösteriyor: tek bir koşuya güvenme, birden çok koşunun en küçüğünü ya da ortalamasını al. Metinde kullandığımız tablo, iki koşunun değerlerini gösteriyor:

| Ölçüm | Koşu 1 | Koşu 2 | Yorum |
|---|---|---|---|
| Bağımlı add zinciri (en az süre, sn) | 0,2089 | 0,2093 | 1000 add/tur, 10^6 tur |
| Tahmini çekirdek frekansı (GHz) | 4,788 | 4,777 | Varsayım: her add 1 çevrim |
| TSC hızı (GHz) | 3,413 | 3,343 | Nominal, çekirdek değil |
| Sistem çağrısı getppid (ns/çağrı) | 197,98 | 200,96 | 3 milyon çağrı |
| Doğrudan fonksiyon çağrısı (ns/çağrı) | 1,05 | 1,07 | Aynı döngü, noinline |

Son iki satır, sistem çağrısının pahalılığını gösteriyor. Aynı sayıda `getppid` çağrısı yaklaşık 200 ns sürerken, doğrudan bir fonksiyon çağrısı bir nanosaniyenin biraz üzerindedir. Bu fark iki şeyden gelir: sistem çağrısı işlemcinin ayrıcalık seviyesini değiştirir ve çekirdekte bir dizi iş yapılır (bunu 24.10'da göreceksin). Ayrıca bu sanal makinede ve WSL2'de çekirdek, Spectre ve Meltdown azaltımlarını uyguluyor olabilir; bu da çağrı maliyetini artırır. 200 ns, bu makineye özgü bir değerdir; başka bir sistemde farklı olabilir ve genelleme yapmak yanlış olur.

Bu bölümdeki her ölçümde kullandığımız ortak yöntem şöyle özetlenebilir:

- Ölçülen kod, derleyicinin silemeyeceği bir yere yazılır (`volatile` bir `sink` değişkeni).
- Ölçülen fonksiyon `noinline` ile sarılır; böylece derleyici çağrıyı döngünün dışına çıkaramaz.
- Rastgele veri sabit bir tohumla üretilir (örneğin 42) ve her sürümün sonucu doğrulanır: sonuçlar uyuşmuyorsa program hata verir.
- Her ikili, `taskset -c 3` ile tek bir çekirdeğe sabitlenir ve birden çok kez çalıştırılır; en küçük süre ya da ortalama raporlanır.
- Derleme bayrakları metinde açıkça yazılır, çünkü aynı kaynak farklı bayraklarla farklı makine kodu üretir.

::: ipucu
Bir kıyas sonucu şaşırtıcıysa önce derlenmiş kodu incele. Bu bölümün 24.8'deki hizalama olayı gibi, ölçtüğün şey bazen algoritma değil bağlayıcının yerleşim kararıdır. objdump ile iki ikiliyi yan yana koy: aynı komutları mı çalıştırıyorlar?
:::

## 24.10 Ayrıcalık seviyeleri, sistem çağrısı ve spekülasyon

Bir işletim sistemi, uygulamaların donanıma ve birbirlerinin belleğine istediği gibi erişmesini engellemek zorundadır. Bu, işlemcinin **ayrıcalık seviyeleriyle** sağlanır. x86-64'te bu seviyeler halkalar (ring) olarak adlandırılır: halka 0 en ayrıcalıklı olandır ve çekirdek orada çalışır; halka 3 en kısıtlı olandır ve kullanıcı programları orada çalışır. Geçerli seviye (CPL, Current Privilege Level) kod segmenti yazmacının düşük iki bitinde tutulur. Linux yalnızca halka 0 ve 3'ü kullanır; halka 1 ve 2 kullanılmaz. Bu durum Şekil 24.9'da gösteriliyor.

![Şekil 24.9: Ayrıcalık seviyeleri. Solda x86-64 halkaları: çekirdek (halka 0) merkezde, kullanıcı programı (halka 3) dışta; Linux yalnızca bu iki halkayı kullanır. Sağda ARM AArch64 Exception Level'ları: EL0 kullanıcı, EL1 işletim sistemi çekirdeği, EL2 hipervizör, EL3 güvenli monitör.](gorseller/b24_halka.png)

ARM tarafında aynı fikir **Exception Level (EL)** ile anlatılır: EL0 kullanıcı programları, EL1 işletim sistemi çekirdeği, EL2 hipervizör (sanallaştırma), EL3 güvenli monitördür. Cortex-M gibi küçük gömülü işlemcilerde ise daha sade bir model vardır: iş parçacığı (thread) modu ve kesme (handler) modu vardır ve iş parçacığı modunda `CONTROL` yazmacı ile ayrıcalıklı ve ayrıcalıksız çalışma seçilebilir. Bu, genel bilgi olarak bilinir; bu bölümde Cortex-M üzerinde ölçüm yapmadık.

Peki bir kullanıcı programı çekirdeğe nasıl geçer? İki yol vardır. Birincisi **sistem çağrısı**dır: program bilerek çekirdeğe bir istek gönderir (dosya okuma, bellek ayırma gibi). İkincisi **kesme (interrupt)**dir: donanım (zamanlayıcı, klavye, ağ kartı) çekirdeğin dikkatini ister. Kesmelerin ayrıntısı Bölüm 44'te, yalnızca kavramsal düzeyde burada.

Sistem çağrısının CPU tarafı `syscall` komutuyla başlar. Donanım, dönüş adresini `rcx` yazmacına, bayrakları `r11`'e koyar, ayrıcalık seviyesini 0'a çeker ve çekirdeğin giriş adresine atlar (bu adres `IA32_LSTAR` adlı bir model-özel yazmaçta tanımlıdır; genel bilgi). Çekirdek işini bitirince `sysret` komutu, `rcx`'teki adrese döner, `r11`'deki bayrakları geri yükler ve ayrıcalık seviyesini 3'e çevirir. Bu ayrıntılar, bir sistem çağrısının neden bir fonksiyon çağrısından yavaş olduğunu açıklar: ayrıcalık geçişi, koruma kontrolleri ve çekirdekte yapılan işler.

Aşağıdaki çıktı, abi.c içindeki `sistem_getppid` fonksiyonunun inline assembly'siyle üretilen `syscall` komutunu gösteriyor. Komut numarası (110) `mov $0x6e,%eax` ile `rax`'e konuyor.

```asm
    10c8:   xor    %eax,%eax
    10ca:   call   1070 <__printf_chk@plt>
    10cf:   mov    $0x6e,%eax
    10d4:   syscall
```

Şekil 24.10, bu yolu adım adım gösteriyor: kullanıcı kodu, `syscall`, çekirdeğin giriş noktası, sistem çağrısı tablosu ve dönüş.

![Şekil 24.10: Bir sistem çağrısının CPU tarafı. Kullanıcı kodu getppid'i çağırır, syscall komutu CPL'yi 0'a çevirir ve çekirdek girişine atlar; çekirdek işi bitirince sysret ile kullanıcı moduna döner.](gorseller/b24_syscall.png)

Çekirdek girişinin gerçek kodunu Kod Okuma bölümünde Linux'un kaynağından okuyacaksın. Orada `swapgs` ile GS tabanının çekirdeğin kendi verisine çevrildiğini, yığın işaretçisinin değiştirildiğini ve çağrı numarasına göre bir tablodan işlevin seçildiğini göreceksin.

### Spekülatif yürütme ve güvenlik bedeli

Dal tahmini, işlemcinin bir dalın sonucunu beklemeden tahmin edilen yoldan devam etmesini sağlar. Bu yol doğruysa kazanç büyüktür; yanlışsa işlemci, yaptığı işi **geri alır** (squash). Ama geri alma, yalnızca mimari durumu geri alır: yazmaçlar ve bellek eski haline döner. **Mikromimari yan etkiler** geri alınmaz. Örneğin spekülatif olarak yüklenen bir bellek satırı önbelleğe girmiş olabilir ve bu, bir zamanlama ölçümüyle (örneğin bir önbellek isabeti ile kaçırma arasındaki fark) sonradan okunabilir.

Bu fikir 2018'de iki dikkat çekici güvenlik açığı olarak ortaya çıktı: **Meltdown** ve **Spectre** (genel bilgi). Meltdown, bazı işlemcilerde spekülatif yükleme sırasında ayrıcalık kontrolünün sonucunun ancak daha sonra uygulanmasından yararlanır. Spectre, dal tahmininin eğitilebilmesinden (Spectre v2 için dolaylı dal hedefi, Spectre v1 için sınır kontrolü) yararlanır. Bu bölümde saldırı kodu yazmıyoruz; yalnızca bu tasarımın nasıl bir güvenlik maliyeti olduğunu anlamak için kavramsal bir çerçeve kuruyoruz.

Azaltımlar da bu bilgiye dayanır. Meltdown'a karşı Linux, etkinleştirildiğinde (KPTI, Kernel Page Table Isolation) çekirdek ve kullanıcı için ayrı sayfa tabloları kullanır; sistem çağrısı girişinde `CR3` değiştirilir. Bu adımı, Kod Okuma bölümünde gerçek kodda `SWITCH_TO_KERNEL_CR3` makrosu olarak göreceksin. Spectre v2 için ise dolaylı dal tahmininin kullanıcı ve çekirdek arasında paylaşılmasını engelleyen mekanizmalar ve derleyici yapıları (retpoline gibi) kullanılır; genel bilgi olarak bunlar her işletim sisteminde ve derleyicide farklı biçimlerde yer alır.

Bu bilginin pratik sonucu şudur: güvenlik ve performans arasında gerçek bir takas vardır. Azaltımlar, sistem çağrılarını ve kesmeleri daha pahalı hâle getirir; bu da 24.9'da ölçtüğümüz 200 ns'lik `getppid`'in bir parçasını açıklar. Güvenlik açığının kapatılması hızdan ödenir.

### Gerçek bir önyükleme: MertOS

Bu bölümün son gerçek örneği MertOS'un önyükleme kodudur. Bir işletim sistemi açıldığında işlemci, donanımın belirlediği bir moddan başlar ve çekirdeğin çalışabilmesi için bir dizi mod geçişi yapılmalıdır. MertOS, GRUB Multiboot2 önyükleyicisi üzerinden başlar; GRUB makineyi 32 bit korumalı moda almıştır, çekirdeğin giriş kodu (`entry.asm`) ise 64 bit uzun moda geçer. Bu repoda gerçek mod (16 bit) kodu yoktur; bu geçişi GRUB yapar (genel bilgi).

Uzun moda geçiş, kodun belirli sırayla yazılmış kontrol yazmaçlarına değer koymasını gerektirir. Aşağıdaki kesit, MertOS'un `entry.asm` dosyasından alınmıştır (dosya başına göre 96-111 satırları):

```asm
    ; Long Mode'u EFER MSR'de aktif et
    mov ecx, 0xC0000080         ; EFER MSR
    rdmsr
    or  eax, (1 << 8)           ; LME (Long Mode Enable)
    wrmsr

    ; Paging'i aktif et + Protection Enable
    mov eax, cr0
    or  eax, (1 << 31) | (1 << 0)  ; PG | PE
    mov cr0, eax

    ; GDT yükle (64-bit code segment)
    lgdt [gdt64.pointer]

    ; Far jump → 64-bit code segment'e gir
    jmp gdt64.code:long_mode_start
```

Bu sıra önemlidir. Önce `CR4`'te PAE (Physical Address Extension, bit 5) açılır; sonra `EFER` model-özel yazmacında LME (Long Mode Enable, bit 8) açılır (`rdmsr` ve `wrmsr` ile, yazmaç numarası 0xC0000080); en son `CR0`'da PG (paging, bit 31) ve PE (protected mode, bit 0) birlikte açılır. Bu üç adımdan sonra işlemci uzun modda çalışmaya hazırdır, ama henüz 64 bit kod segmentinde değildir; bu yüzden `lgdt` ile yeni bir GDT yüklenir ve `jmp gdt64.code:long_mode_start` ile 64 bit kod segmentine uzak atlama yapılır. Sayfa tablolarının nasıl kurulduğunu Bölüm 25'te göreceksin; GDT ve segment kavramını ise kesmelerle birlikte Bölüm 44'te ele alacağız.

Bu kesitin bir yanı da dikkat çekici: `mov cr0, eax` komutu sayfalamayı açtığı anda, o ana kadar kullanılan adresler artık sanal adres olarak yorumlanır. Bu yüzden kod, sayfa tablolarını bu adım öncesinde hazırlar ve identity mapping (sanal = fiziksel) ile başlar. Bu tür bir sıra hatası çoğu zaman sessiz bir çöküş olarak görünür; hata ayıklaması zordur. Gömülü işlemcilerde (Cortex-M gibi, MMU'su olmayan) bu adımların hiçbiri yoktur; yazılım doğrudan fiziksel adreslerle çalışır. Bu da her iki dünyada da kodun neyi varsaydığını bilmenin önemini artırır.

Son olarak, bu bölümün ölçümlerinden çıkan ana fikir: işlemci, kodun yazılma biçimine çok duyarlıdır. Komut sayısı, dallanma yapısı, bağımlılık zinciri, veri hizalaması ve sistem çağrısı sıklığı, aynı algoritmanın hızını birkaç kat değiştirebilir. Bu duyarlılığı hem tasarımda hem ölçümde hesaba katmak, savunma sanayiinde gerçek zamanlı kodu güvenilir kılmanın ilk adımıdır.

## Çözümlü Örnekler

Bu bölümdeki örnekler, Bölüm 5'te öğrendiğin altı adımı izler: Anla, Örnekle, Kaba çöz, Örüntü, İyileştir, Doğrula. Her örnekte son adım bir elle iz sürme tablosu içerir. Örnekleri okurken kâğıt ve kalem kullan; tabloyu sen doldurmadan sonuca bakma.

### Örnek 1 (★): `toplam` fonksiyonunu yazmaçlarla izlemek

Bölüm 24.3'te `toplam` fonksiyonunun `-O0` ve `-O2` assembly'sini gördün. Bu örnekte yalnızca `-O0` çıktısını kullanarak fonksiyonun ne yaptığını izleyeceksin.

**Adım 1 — Anla.** Fonksiyon bir `int` dizisinin ilk `n` elemanını toplar ve toplamı döndürür. Assembly'de bilmemiz gereken üç şey var: toplamın nerede tutulduğu (yazmaç mı, bellek mi?), döngü sayacının nerede olduğu ve dönüş değerinin hangi yazmaçta olduğu.

**Adım 2 — Örnekle.** `a = {3, 5, 7}` ve `n = 3` alalım. Beklenen sonuç `3 + 5 + 7 = 15`'tir. Ayrıca `n = 0` için sonucun 0 olması gerektiğini de not et; bunu sonunda kontrol edeceğiz.

**Adım 3 — Kaba çöz.** Assembly'i yukarıdan aşağı okursak: önce `s` ve `i` yığında sıfırlanır (`-8(%rbp)` ve `-4(%rbp)`), sonra `.L2` koşuluna atlanır. Koşul sağlanıyorsa `.L3` gövdesi çalışır: `i`'nin 4 katı ofsetle dizi elemanının adresi bulunur, eleman okunur, `s`'ye eklenir ve `i` artırılır. Koşul sağlanmadığında `s`, `eax`'e alınır ve fonksiyon döner.

**Adım 4 — Örüntü.** Gövde her iterasyonda aynı beş işi yapar: adres hesapla, elemanı yükle, belleğe toplayarak ekle, sayacı artır, karşılaştır ve gerekirse dallan. Her iterasyonda `s` ve `i` yığında güncellenir; yani bir iterasyonun sonucu sonrakinin girişidir.

**Adım 5 — İyileştir.** `-O0` çıktısında gereksiz işler var: `s` ve `i`'nin her iterasyonda bellekten okunup yazılması. `-O2` çıktısında bu işler yazmaçlara taşınmış ve döngü iterasyonu başına on bir komuttan dörde inmiştir. Bu fark, "derleyici ne yapıyor?" sorusunun cevabının kaynak koddan değil assembly'den okunduğunu gösterir.

**Adım 6 — Doğrula.** Aşağıdaki tabloda her satır bir iterasyon sonrası durumdur. `s` ve `i` değerleri, `-O0` çıktısındaki bellek konumlarına (`-8(%rbp)` ve `-4(%rbp)`) karşılık gelir.

| Adım | `i` (-4) | `s` (-8) | Okunan eleman | Koşul `i < 3` |
|---|---|---|---|---|
| Başlangıç | 0 | 0 | - | doğru |
| 1. iterasyon | 1 | 3 | a[0] = 3 | doğru |
| 2. iterasyon | 2 | 8 | a[1] = 5 | doğru |
| 3. iterasyon | 3 | 15 | a[2] = 7 | yanlış, çıkış |
| Dönüş | - | 15 | - | `eax` = 15 |

Tablo `15`'i verdi, beklenen sonuçla eşleşiyor. `n = 0` durumunda ise başlangıçtaki koşul ilk anda yanlış olur, gövde hiç çalışmaz ve `s = 0` döner; bu da beklentiyle uyumludur.

**Bunu AI'sız yazabilir misin?** `toplam` fonksiyonunun `-O0` assembly'sine bakarak C kodunu geri yaz. Sonra `n` negatif olduğunda hangi sonucu vereceğini önce kâğıt üzerinde tahmin et, ardından kendi kodunla test et.

### Örnek 2 (★★): `g` fonksiyonunu tersine okumak

Şimdi kaynak kodu görmeden yalnızca assembly'den C'yi geri çıkaracaksın. Aşağıdaki çıktı, Bölüm 24.3'te gördüğün `g` fonksiyonunun `-O2` çıktısıdır.

```asm
g:
        endbr64
        cmpl    %esi, %edi
        jle     .L12
        leal    (%rdi,%rdi,2), %edi
        leal    (%rdi,%rsi), %eax
        ret
        addl    %esi, %esi
        movl    %edi, %eax
        subl    %esi, %eax
        ret
```

**Adım 1 — Anla.** İki argüman var: `edi` (x) ve `esi` (y). Dönüş değeri `eax`'te. Fonksiyonun bir dalı var; amacımız dalın iki yolunu ve her yolda ne hesaplandığını bulmak.

**Adım 2 — Örnekle.** İki test çifti seçelim: `(x, y) = (5, 2)` ve `(x, y) = (1, 4)`. Bu iki çift dalın iki yolunu da kapsar. Assembly'nin ne döndürdüğünü tahmin etmeden önce kendi kâğıdında her yol için bir hesap yap.

**Adım 3 — Kaba çöz.** `cmpl %esi, %edi` komutu `x - y`'yi hesaplar ve bayrakları günceller. `jle .L12` komutu `x <= y` ise `.L12`'ye atlar. Atlamıyorsa (yani `x > y`) yol şöyledir: `edi` 3 katına çıkar, `eax`'e `3x + y` yazılır, dönülür. `.L12` yolunda `esi` iki katına çıkar, `eax`'e `x` kopyalanır, `x - 2y` hesaplanır ve dönülür.

**Adım 4 — Örüntü.** İki yol da birer doğrusal ifadedir: biri `3x + y`, öbürü `x - 2y`. Koşul `x > y`. Bu, üçlü operatörle yazılmış bir C ifadesinin tipik assembly'sidir: karşılaştırma, bir atlama ve iki bağımsız hesap bloğu.

**Adım 5 — İyileştir.** Tahminimizi C'ye yazalım: `return x > y ? 3 * x + y : x - 2 * y;`. Derleyici burada `cmov` yerine bir dal bıraktı. Bu bir maliyet kararıdır ve her zaman en iyi karar olmayabilir; kendi kodunda bu kararı görmek ve gerekirse ölçmek için assembly'ye bakmak gerekir.

**Adım 6 — Doğrula.** Her iki test çiftini hem assembly'nin mantığıyla hem de C ifadesiyle hesaplayıp karşılaştıralım.

| `(x, y)` | `x > y` | Yol | Assembly mantığı | C ifadesi | Eşleşme |
|---|---|---|---|---|---|
| (5, 2) | doğru | `3x + y` | 3·5 + 2 = 17 | 3·5 + 2 = 17 | evet |
| (1, 4) | yanlış | `x - 2y` | 1 - 2·4 = -7 | 1 - 2·4 = -7 | evet |

İki test çifti de eşleşti. Tek bir test her iki yolu kapsamadığı için iki çift seçmek bu sonucun güvenilirliğini artırır; yine de kesin doğrulama için rastgele çiftlerle karşılaştırma yapmak gerekir.

**Bunu AI'sız yazabilir misin?** `3 * x` hesabı `x = INT_MIN` için taşar. Bu taşma neden tanımsız davranıştır (UB)? Bu soruyu, C standardının işaretli tamsayı taşması kuralına bakarak kâğıtta yanıtla; sonra fonksiyonu `unsigned` tiplerle yazmanın bu sorunu nasıl değiştirdiğini düşün.

### Örnek 3 (★★): dal tahmini deneyini tasarlamak ve yorumlamak

Bir arkadaşın şöyle bir iddiası var: "Diziyi önce sıralarsan, koşullu toplama döngüsü hızlanır." Bu iddiayı test etmek için bir deney tasarlamalı ve sonucu yorumlamalısın.

**Adım 1 — Anla.** İddiayı ölçülebilir bir soruya çevirelim: Aynı diziyi aynı derleyici ve aynı kodla toplarken, sıralı ve sırasız sürümler arasındaki süre farkı nedir? Yanıt, dal tahmininin etkisine bağlıdır.

**Adım 2 — Örnekle.** Küçük bir örnek: `{200, 10, 150, 20}` dizisinde 128 ve üzeri elemanlar `200` ve `150`'dir. Sıralı hâli `{10, 20, 150, 200}`'dür. İki dizide de aynı toplam elde edilir (350), ama dal örüntüsü farklıdır: sırasız dizide `aldı, almadı, aldı, almadı`; sıralı dizide `almadı, almadı, aldı, aldı`.

**Adım 3 — Kaba çöz.** Deneyin değişkenleri: dizi düzeni (sıralı ya da sırasız), derleme (dallı ya da dalsız) ve ölçüm. Kontrol edilmesi gerekenler: aynı dizi (aynı tohum), aynı derleyici ve bayraklar, aynı toplam (doğruluk). Ölçüm için birden çok koşu ve en küçük süre ya da ortalama. Dalsız sürüm bir kontrol olarak kullanılır: dal yoksa sıra da önemsiz olmalıdır.

**Adım 4 — Örüntü.** Dal tahmincisi, ardışık benzer sonuçlarda başarılıdır. Sıralı dizide dal sonucu uzun bloklar halinde değişir; tahminci her blok geçişinde birkaç kez yanılır. Sırasız dizide, rastgele bir bit dizisi gibi davranır ve tahminci en iyi durumda yarı yarıya yanılır. Bu örüntü, iki bitlik sayacın durum geçişleriyle açıklanabilir.

**Adım 5 — İyileştir.** Tahminciyi sayaçla modelleyelim: durum 0-3, tahmin 2 ve üzeri ise "alınır". Gerçek bir dal dizisi için yanlış tahmin sayısını hesaplayalım.

**Adım 6 — Doğrula.** Dal sonuçları `T, T, N, T, T, N, N, T` olsun (T: alınır, N: alınmaz). Başlangıç durumunu 1 (zayıf alınmaz) seçelim.

| Sıra | Dal | Durum (önce) | Tahmin | Doğru mu? | Durum (sonra) |
|---|---|---|---|---|---|
| 1 | T | 1 | N | yanlış | 2 |
| 2 | T | 2 | T | doğru | 3 |
| 3 | N | 3 | T | yanlış | 2 |
| 4 | T | 2 | T | doğru | 3 |
| 5 | T | 3 | T | doğru | 3 |
| 6 | N | 3 | T | yanlış | 2 |
| 7 | N | 2 | T | yanlış | 1 |
| 8 | T | 1 | N | yanlış | 2 |

Tabloda sekiz dalda beş yanlış tahmin var. Sırasız diziye benzer bu rastgele örüntüde yanlış oranı yüksek. Şimdi sıralı diziye benzeyen bir örüntü düşün: `N` bir süre gelip sonra `T` bloğu gelsin. Tahminci, durumu `0`'a kadar indirmiş olur; `T` geçişinde ilk iki `T` yanlış tahmin edilir (durum 0'dan 1'e, sonra 2'ye çıkar), üçüncüsünden itibaren doğru. Yani her geçiş yaklaşık iki yanlış tahmindir ve uzun bloklarda bu sayı çok küçüktür. Dallı toplamadaki ölçümümüz bu iki durumun farkını yansıtıyor: sıralı dizide yanlış tahmin az, sırasızda yarı yarıya.

**Bunu AI'sız yazabilir misin?** Dalsız bir `dalsiz_toplam` fonksiyonu yaz (maske kullan), sıralı ve sırasız dizilerde aynı toplamı verdiğini doğrula. Sonra dallı sürümün dalsız sürümden **daha hızlı** olacağı bir dizi düzeni tarif et ve nedenini dal tahmini ile açıkla.

### Örnek 4 (★★★): komut düzeyi paralellik için bir model kurmak

Bölüm 24.7'deki toplama ölçümünü bir modelle açıklayabilir miyiz? Bu örnekte basit bir model kuracak ve ölçümle karşılaştıracaksın.

**Adım 1 — Anla.** 1000 elemanlı bir `double` dizisinin toplamı için, `k` akümülatör kullanan üç sürüm var: `k = 1, 4, 8` (ve `k = 2`). Soru: eleman başına kaç çevrim gerekir ve bu neden akümülatör sayısına bağlıdır?

**Adım 2 — Örnekle.** `k = 1` için her toplama bir öncekini bekler; 1000 toplama zinciri var. `k = 4` için her zincir 250 toplamadır ve dört zincir paralel ilerleyebilir. Hangisinin daha hızlı olacağını tahmin et ve gerekçelendir.

**Adım 3 — Kaba çöz.** Model için varsayımlar (genel bilgi, doğrulanmadı): bir kayan nokta toplamasının gecikmesi 3 çevrim; işlemcinin her çevrimde başlatabileceği en fazla 2 toplama var (yani iki toplama birimi, her biri boru hatlı); yükleme ve döngü yükü ihmal edilir. Bu varsayımlarla iki sınır vardır: zincirin gecikme sınırı ve birimlerin verim sınırı.

**Adım 4 — Örüntü.** `k` akümülatörle her zincirin uzunluğu `1000/k` toplamadır, gecikme sınırı `3 · 1000/k` çevrimdir. Verim sınırı ise `1000 / 2 = 500` çevrimdir. Gerçek süre bu iki sınırın büyüğüdür: `max(3000/k, 500)`. Bu formül, `k` küçükken gecikmenin, `k` büyükken verimin belirleyici olduğunu söyler.

**Adım 5 — İyileştir.** Kazanç `k = 8`'den sonra durur, çünkü verim sınırı devreye girer (500 çevrim). Daha fazla kazanç için yürütme birimlerinin kendisi değil, işi azaltmak gerekir: SIMD (24.8) bir komutta birden çok toplama yapar. Yani model, hangi darboğazın hangi tasarım değişikliğiyle aşılabileceğini de gösterir.

**Adım 6 — Doğrula.** Modelin ürettiği çevrim sayılarını 4,78 GHz varsayımıyla nanosaniyeye çevirip ölçümle karşılaştıralım. Ayrıca `k = 8` için ilk sekiz elemanın başlama çevrimlerini elle izleyelim (iki birim, her çevrimde en fazla iki başlatma).

| `k` | Gecikme sınırı (çevrim/eleman) | Verim sınırı (çevrim/eleman) | Model (çevrim/eleman) | Model (ns, 4,78 GHz) | Ölçüm (ns) | Fark |
|---|---|---|---|---|---|---|
| 1 | 3,00 | 0,50 | 3,00 | 0,628 | 0,570 | yaklaşık -9% |
| 2 | 1,50 | 0,50 | 1,50 | 0,314 | 0,298 | yaklaşık -5% |
| 4 | 0,75 | 0,50 | 0,75 | 0,157 | 0,152 | yaklaşık -3% |
| 8 | 0,375 | 0,50 | 0,50 | 0,105 | 0,105 | yaklaşık 0% |

Model, ölçümü yüzde on içinde tahmin ediyor. Tek zincirde model biraz yüksek çıkıyor; bu, gecikme değerinin ya da frekansın tam değerinin farkından gelebilir, ama bunu kesin olarak ayırt etmek için donanım sayaçları gerekir.

İlk sekiz elemanın başlama çevrimlerini iki durum için izleyelim:

| Eleman | `k = 2`: akümülatör | `k = 2`: başlama çevrimi | `k = 8`: akümülatör | `k = 8`: başlama çevrimi |
|---|---|---|---|---|
| 0 | s0 | 0 | s0 | 0 |
| 1 | s1 | 0 | s1 | 0 |
| 2 | s0 | 3 | s2 | 1 |
| 3 | s1 | 3 | s3 | 1 |
| 4 | s0 | 6 | s4 | 2 |
| 5 | s1 | 6 | s5 | 2 |
| 6 | s0 | 9 | s6 | 3 |
| 7 | s1 | 9 | s7 | 3 |

`k = 2`'de her zincir, önceki toplamanın bitmesini (3 çevrim) bekler; bu yüzden başlama çevrimleri 0, 3, 6, 9 diye gider ve sekiz eleman yaklaşık 12 çevrimde biter. `k = 8`'de her zincir, kendi önceki toplamasını beklemeden başlayabilir; ama iki birim yalnızca çevrim başına iki başlatma yapabildiği için başlama çevrimleri 0, 0, 1, 1, 2, 2, 3, 3 olur. Sekiz eleman 3 çevrimde başlatılır ve son toplamanın bitmesi yaklaşık 6 çevrim sürer. Bu tablo, modeldeki iki sınırın gerçekten nasıl devreye girdiğini gösteriyor.

**Bunu AI'sız yazabilir misin?** `k = 8` akümülatörlü bir toplama fonksiyonu yaz; dizi uzunluğu 8'in katı değilse kalan elemanları ayrıca topla. Doğruluğunu tam sayı değerli bir dizi üzerinde (sonuç kesin bilindiğinde) test et ve sonra ölçümünü Bölüm 24.7'deki gibi yap.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma: ne kod yazdırma, ne hata ayıklattırma, ne de kod parçası istemek. Önce kâğıda tasarımını çiz, sonra kendi editöründe yaz. Takıldığında önce bu bölümdeki kodları ve ölçüm yöntemini yeniden oku. Bu projelerin amacı, bilginin senin parmaklarında olması; bir aracın çıktısını kopyalamak bu amacı bozar.
:::

### Proje 1 (★★): Mikro-kıyas laboratuvarı

**Amaç.** Bu bölümdeki üç fenomeni (dal tahmini, komut düzeyi paralellik ve SIMD) kendi makinende, tekrarlanabilir biçimde ölç ve sonuçları kendi cümlelerinle yorumla.

**Yapılacak.** Tek bir C programı yaz (birden çok dosya olabilir) ve şu üç deneyi içersin. (1) Dal deneyi: 32768 elemanlı bir dizi üret, elemanların 128 ve üzeri olma oranını p = 0,1, 0,5 ve 0,9 olarak değiştir (her oran için sabit tohumla üret); bu oranların her birinde dallı ve dalsız toplamayı ölç. (2) ILP deneyi: bir toplama döngüsünü 1, 2, 4, 8 ve 16 akümülatörle yaz ve eleman başına süreyi ölç. (3) SIMD deneyi: AXPY işlemini skaler ve AVX2 + FMA (intrinsics) olarak yaz; `__builtin_cpu_supports` ile kontrol et.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Her ölçüm fonksiyonunu `noinline` ile sar ve sonucunu `volatile` bir değişkene yaz. Her derlemenin makine kodunu `objdump -d` ile kontrol et; dal deneyinde `jcc` komutunun gerçekten bulunduğunu, dalsız ya da cmov'a dönüşmüş sürümde bulunmadığını doğrula. Ölçümleri `taskset` ile tek bir çekirdeğe sabitle ve her ölçümü en az beş kez tekrarla. Hizalamanın etkisini görmek için bir derleme daha yap ve `-falign-functions=64 -falign-loops=64` ile karşılaştır. Sonuçları CSV olarak kaydet ve grafiği bir betikle çiz.

**Başarı kriterleri.**
- Her deney için iki bağımsız koşudaki değerler birbirinden yüzde on'dan fazla sapmıyor (sapma büyükse nedenini yaz).
- Her sürümün toplamı (ya da sonucu) diğer sürümlerle eşleşiyor ve program uyuşmazlıkta hata veriyor.
- Dal deneyinde hangi derlemenin dal içerdiğini `objdump` çıktısıyla kanıtladın.
- Dal oranı p ile sırasız dizi süresi arasındaki ilişkiyi bir grafikte gösterdin ve yorumladın: p = 0,5 civarında neden en yüksek süre görülüyor?
- Raporunda "ölçüldü", "doğrulandı" ve "varsayım" ayrımını açıkça yaptın.

### Proje 2 (★★★): Kendi küçük ISA'n ve sanal makinen

**Amaç.** Bir komut kümesi tasarlamak, onu çalıştıracak bir yorumlayıcı yazmak ve fetch-decode-execute döngüsünü, Bölüm 1'deki sözde-assembly'den daha ciddi bir ortamda kendin kurmak.

**Yapılacak.** Her komutu 16 bit olarak kodla: üst 8 bit işlem kodu (opcode), alt 8 bit işlenen. Sekiz genel amaçlı yazmacın (r0-r7), bir program sayacının (PC), bir yığın işaretçisinin (SP) ve 256 baytlık bir belleğin olduğu bir makine tanımla. En az şu komutları destekle: `LOADI` (bir yazmaca anlık değer), `ADD`, `SUB`, `JMP`, `JZ` (sıfırsa atla), `CALL`, `RET`, `PUSH`, `POP`, `PRINT` ve `HALT`. Bir assembler yaz: metin dosyasını bayt dizisine çevirsin ve etiketleri iki geçişte çözsün. Yorumlayıcıyı C ya da C++ ile yaz; her komutun kaç döngü aldığını say.

**Önerilen yaklaşım (ipucu).** Komut kodlarını bir tablo olarak tanımla (`opcode`, `ad`, `işlenen sayısı`). Yorumlayıcının ana döngüsü üç adımdan oluşsun: `getir` (PC'den 16 bit oku, PC'yi ilerlet), `coz` (üst ve alt baytı ayır), `yurut` (bir `switch` ile işlemi yap). Özyinelemeli faktöriyeli `CALL` ve `RET` ile yaz; bu, yığının nasıl kullanıldığını Bölüm 8'deki çağrı yığınıyla karşılaştırmanı sağlar. Assembler'da etiket çözümü için ilk geçişte etiketlerin adreslerini topla, ikinci geçişte dallanma hedeflerini yaz.

**Başarı kriterleri.**
- `faktöriyel(10) = 3628800` doğru sonucu veriyor ve `faktöriyel(0)` de doğru çalışıyor.
- Bilinmeyen bir işlem kodu geldiğinde yorumlayıcı çökmek yerine açık bir hata mesajı veriyor.
- Yığın taşması (SP sınırın dışına çıkması) denetleniyor ve bir hata olarak raporlanıyor.
- Çalıştırılan toplam komut sayısını ve bir programın kaç komutta bittiğini raporlayabiliyorsun.
- Bir testin neden geçtiğini ya da kaldığını, yalnızca "çalıştı" demeden, bayt düzeyinde gösterebiliyorsun.

### Ek Alıştırmalar

1. ★ `-O0` ve `-O2` ile derlenmiş `toplam` fonksiyonlarında döngü gövdesinde hangi işlemler kayboldu? Her biri için nedenini bir cümleyle yaz.
2. ★ Bir fonksiyon yedi tamsayı argümanı alıyor. System V AMD64'te yedinci argüman nerede geçer? Windows x64'te bu sayı nasıl değişir? (Mülakat)
3. ★★ `|a - b|` değerini hiçbir dal kullanmadan hesapla. Taşma durumunda neyin tanımsız olduğunu da belirt. (Mülakat)
4. ★★ Bir dal tahmincisinin doğruluğu yüzde doksan ve yanlış tahmin cezası on beş çevrim. Dal başına ortalama ek çevrim kaçtır? Bu hesabın hangi durumda yanıltıcı olduğunu açıkla.
5. ★★ Bir sayının ikilik gösterimindeki 1 bitlerini, dal kullanmadan ve `x &= x - 1` numarasıyla say. Bu numaranın neden her adımda en düşük 1 biti sildiğini açıkla. (Mülakat)
6. ★★ Bir dizinin toplamını dört akümülatörle yaz. Tam sayı toplamda sonucun sıradan bağımsız olduğunu, kayan noktada ise neden olmadığını açıkla. (Mülakat)
7. ★★ Her elemanı ikiyle çarpan bir SIMD döngüsünde dizi uzunluğu sekizin katı değilse kalan elemanları nasıl işlersin? Skaler kuyruk döngüsü ile maskeli yükleme arasındaki farkı tartış.
8. ★★★ Bir yaprak fonksiyon kırmızı bölgede 200 bayt yerel veri tutmak istiyor. Derleyici bunu nasıl yapar? Çekirdek kodunda kırmızı bölge neden kapatılır? (Mülakat)
9. ★★ `syscall` komutu hangi yazmaçları bozar? Linux'ta dördüncü sistem çağrısı argümanı neden `rcx` yerine `r10`'da geçer? (Mülakat)
10. ★★★ Gömülü bir kesme işleyicisinde kayan nokta birimi kullanmak neden dikkat ister? Bağlam kaydetme sırasında hangi yazmaçların kaydedilmesi gerektiğini tartış. (Bölüm 44'e bağlan.)
11. ★★★ Spekülatif yürütme neden bir güvenlik sorunu olabilir? "Önbellek kanalı" kavramını, bir zamanlama ölçümünün hangi bilgiyi sızdırabileceğini örnek vererek açıkla. (Mülakat)
12. ★ `maks` fonksiyonunun `-O0` ve `-O2` çıktılarında dal var mı? Hangisinde cmov kullanılmış ve neden bu sürüm daha az dal içeriyor?

## Kod Okuma Egzersizi

Linux çekirdeğinin x86-64 sistem çağrısı giriş noktasını okuyacaksın. Kaynak, Linux çekirdeğinin **v6.6** etiketindeki `arch/x86/entry/entry_64.S` dosyasıdır. Dosya, raw.githubusercontent.com üzerinden 429 (hız sınırı) yanıtı aldığı için jsdelivr aynası (cdn.jsdelivr.net/gh/torvalds/linux@v6.6) üzerinden indirildi; içerik aynı etikete aittir. Aşağıdaki kesit 87-112 ve 114-120 satırlarını içerir. Yalnızca 113. satır atlandı, çünkü 70 karakter sınırını aşıyor ve bir yorumdan ibaret. Sekmeler dört boşlukla değiştirildi; başka hiçbir değişiklik yoktur.

```c
SYM_CODE_START(entry_SYSCALL_64)
    UNWIND_HINT_ENTRY
    ENDBR

    swapgs
    /* tss.sp2 is scratch space. */
    movq    %rsp, PER_CPU_VAR(cpu_tss_rw + TSS_sp2)
    SWITCH_TO_KERNEL_CR3 scratch_reg=%rsp
    movq    PER_CPU_VAR(pcpu_hot + X86_top_of_stack), %rsp

SYM_INNER_LABEL(entry_SYSCALL_64_safe_stack, SYM_L_GLOBAL)
    ANNOTATE_NOENDBR

    /* Construct struct pt_regs on stack */
    pushq    $__USER_DS                /* pt_regs->ss */
    pushq    PER_CPU_VAR(cpu_tss_rw + TSS_sp2)    /* pt_regs->sp */
    pushq    %r11                    /* pt_regs->flags */
    pushq    $__USER_CS                /* pt_regs->cs */
    pushq    %rcx                    /* pt_regs->ip */
SYM_INNER_LABEL(entry_SYSCALL_64_after_hwframe, SYM_L_GLOBAL)
    pushq    %rax                    /* pt_regs->orig_ax */

    PUSH_AND_CLEAR_REGS rax=$-ENOSYS

    /* IRQs are off. */
    movq    %rsp, %rdi
... (113. satır atlandı: 70 karakteri aşıyor) ...
    movslq    %eax, %rsi

    /* clobbers %rax, make sure it is after saving the syscall nr */
    IBRS_ENTER
    UNTRAIN_RET

    call    do_syscall_64        /* returns with IRQs disabled */
```

Bu kesit, `entry_SYSCALL_64` etiketinin başlangıcıdır. Sistem çağrısı CPU tarafından `syscall` ile buraya gelir; ama çekirdek girişi, donanımın bıraktığı durumu kendi kullanımı için toparlamak zorundadır. Kesitteki komutların her birini bu bölümde konuştuğumuz kavramlarla eşleştirmeyi dene: ayrıcalık geçişi, yığın işaretçisi, kayıt (pt_regs) yapısı ve tablo üzerinden işleve dallanma.

**Sorular — cevaplamadan geçme:**

1. `swapgs` komutu ne yapar? Kullanıcı modundayken ve çekirdek modundayken GS tabanı neden farklı olmak zorundadır? Bu bilgi, 24.10'daki ayrıcalık anlatımıyla nasıl ilişkilidir?
2. `pushq $__USER_DS`, `pushq %r11`, `pushq %rcx` gibi komutlar neden bu sırayla itilir? Yığında oluşan çerçevenin alanlarını (`pt_regs->ss`, `->flags`, `->cs`, `->ip`) yorumlara bakarak say. Bu sıra, donanımın kesme sırasında yığına ittiği çerçeveye neden benziyor olabilir?
3. `movq %rsp, %rdi` ve `movslq %eax, %rsi` ne işe yarar? Çekirdekteki `do_syscall_64` fonksiyonunun ilk iki argümanı, bu iki komutun çekirdeğe hangi bilgiyi aktardığını söyler mi? `movslq` komutunun `eax`'i 64 bit'e işaret genişleterek (sign extend) ele almasının neden önemli olduğunu düşün.
4. `SWITCH_TO_KERNEL_CR3` makrosu hangi güvenlik açığına karşı bir azaltım olabilir? Bu makro etkin değilken ne olurdu? (24.10'daki Meltdown anlatımına bak; genel bilgi düzeyinde yanıtla.)
5. `pushq` ile oluşturulan çerçevede `pt_regs->ip` değerinin kaynağı nedir? Kodda bu değerin `rcx`'ten geldiği hangi satırda görülüyor? Bu bilgi, `syscall` komutunun dönüş adresini hangi yazmaca koyduğuyla nasıl ilişkilidir?
6. `IBRS_ENTER` ve `UNTRAIN_RET` satırları ne amaçla çağrılıyor? Yorumlarından ve Bölüm 24.10'daki Spectre anlatımından yola çıkarak yanıtla. `call do_syscall_64` satırının yorumu ne diyor: çağrıdan döndüğünde hangi durum beklenir? Bu durumu kodun devamında (kesitin dışında, kaynağın 121. satırından itibaren) nasıl kontrol ettiğini okumaya çalış.

## Bölüm Özeti

- **ISA ile mikromimari ayrı katmanlardır.** ISA yazılımın gördüğü sözleşmedir (komutlar, yazmaçlar, bellek modeli); mikromimari o sözleşmeyi gerçekleştirir. Aynı ISA, farklı mikromimarilerde farklı hızda çalışır.
- **CISC ve RISC arasındaki fark eskisi kadar keskin değildir.** x86-64 değişken uzunluklu komutlar ve zengin adresleme kullanır; AArch64 ve RISC-V 32 bit sabit uzunluklu komutlar ve yükle-sakla mimarisi kullanır. Gömülü dünyada Cortex-M'nin Thumb-2 ve DSP komutları önemlidir.
- **Assembly okumak, derleyici çıktısını doğrulamanın en güvenilir yoludur.** `-O0` ile `-O2` arasındaki farklar, dal ve cmov kararları, kaynak koda bakarak görülemez.
- **Çağrı kuralları ABI'nin parçasıdır.** System V'de argümanlar rdi, rsi, rdx, rcx, r8, r9'da; Windows x64'te rcx, rdx, r8, r9'da ve gölge alan vardır. Kırmızı bölge yaprak fonksiyonlara özgü bir optimizasyondur.
- **Boru hattı verimi artırır, gecikmeyi değiştirmez.** Yükleme-kullanma, veri, yapısal ve kontrol tehlikeleri; iletme ve balonca ile yönetilir.
- **Dal tahmini, veriye bağlı dallarda performansı belirler.** Sıralı ve sırasız dizi deneyi bunu gösterir; ama derleyici dalı cmov'a çevirirse fark kaybolur. Dalsız programlama, tahmin edilemeyen dallarda anlamlıdır.
- **Komut düzeyi paralellik akümülatörle açığa çıkar.** Bağımlı zincir gecikmeyle sınırlanır; bağımsız zincirler birimlerin verim sınırına kadar hızlanır. Basit bir model bu sınırları ölçümle yüzde on içinde tahmin edebilir.
- **SIMD ve hizalama, hız üzerinde büyük etkiye sahiptir.** Aynı kodun bağlayıcı yerleşimi bile ölçümü iki kat değiştirebilir; ölçümde hizalamayı ve derleme bayraklarını açıkça belirt.
- **Ayrıcalık seviyeleri ve sistem çağrısı CPU'nun iş bölümünü tanımlar.** `syscall` ayrıcalığı değiştirir ve çekirdeğe atlar; Spectre ve Meltdown ise spekülatif yürütmenin güvenlik bedelini gösterir ve azaltımlar performansla takas edilir.

**Sonraki bölümde:** Bölüm 25 (Bellek Hiyerarşisi) ile devam ediyoruz. Bu bölümde bir işlemcinin neden bu kadar hızlı olduğunu anlatırken bellek erişimini hep bir varsayım olarak bıraktık. Bölüm 25'te önbelleklerin (L1, L2, L3), TLB'nin, sanal belleğin ve sayfalamanın, bu bölümdeki dal ve ILP ölçümlerinin neden önbelleğe sığan dizilerle yapıldığını açıklayacağını göreceksin. Bölüm 24'teki ölçüm yöntemini de (tekrar, hizalama, sabitleme) orada kullanacağız.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Dizi ile bağlı liste arasındaki farkı yalnızca Big-O ile açıklamak neden yetersizdir? Bu farkı bir işlemcinin hangi mekanizmaları açıklar?
2. Sıralı ve sırasız bir dizide aynı toplamayı yapan kod neden farklı hızda çalışabilir? Derleyici sonucu nasıl değiştirebilir?
3. ILP nedir? Tek bir toplama zinciri neden dört akümülatörlü sürümden yavaştır, ama on altı akümülatör neden her zaman daha hızlı değildir?
4. Yükleme-kullanma tehlikesi nedir? İletme (forwarding) neden bu tehlikeyi tek başına çözemez?
5. System V ile Windows x64 çağrı kuralları arasındaki en az üç farkı say. Bir Linux kütüphanesini Windows'ta yanlış çağrı kuralıyla çağırırsan hangi hata sessizce oluşabilir?
6. Kırmızı bölge nedir? Bir çekirdek kodu neden onu kapatmak isteyebilir?
7. `syscall` ile normal bir fonksiyon çağrısı arasında CPU'nun neyi değiştirdiğini açıkla. Bu geçişin maliyeti neden yalnızca "ek bir komut" değildir?
8. Spectre ve Meltdown neden yalnızca yazılım hatası değildir? Yazılım tarafında hangi azaltımlar mümkündür ve bunların bedeli nedir?
:::
