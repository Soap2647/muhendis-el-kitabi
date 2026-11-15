%% kisim_no: I
%% kisim_ad: Programlama Temelleri
%% bolum_no: 2
%% baslik: C Dili

## Giriş: Belleğin dilini konuşmak

Bölüm 1'de bilgisayarın nasıl düşündüğünü gördün: bitler, bellek segmentleri, komut döngüsü. Ama o dünyayla aranda hâlâ bir çevirmen yok. İşte C, o çevirmen — hem de en az kayıpla çeviren. C'ye "taşınabilir assembly" denmesinin sebebi bu: yazdığın her satırın makine düzeyinde neye dönüştüğünü *tahmin edebilirsin*. Python'da bir listeye eleman eklerken arka planda ne olduğunu bilmezsin; C'de bilmek zorundasın, çünkü o işi yapan sensin.

Peki neden hâlâ C? Çünkü dünyanın altyapısı C ile yazılmış: Linux çekirdeği, Windows'un çekirdeği, Python'un yorumlayıcısı (adı bile CPython), SQLite, Redis, OpenSSL... Hedeflediğin savunma sanayii şirketlerinde de tablo aynı: Aselsan'ın telsizindeki, Roketsan'ın güdüm kitindeki, Baykar'ın uçuş kontrol kartındaki kod büyük oranda C'dir. Gömülü sistemde çöp toplayıcının (garbage collector) keyfine bırakılacak milisaniyeler yoktur; belleği elle yönetirsin. `MertOS` işletim sistemini yazarken bunu zaten hissettin — bu bölüm o hissi sistemli bilgiye çevirecek.

Bu bölümün planı şöyle: önce dilin iskeletini kuracağız — türler, operatörler, kontrol yapıları, fonksiyonlar. Sonra C'yi C yapan asıl konuya, **işaretçilere (pointer)** geleceğiz ve onları Bölüm 1'deki bellek modelinin üstüne oturtacağız. Ardından diziler, stringler, `struct`'lar ve dinamik bellek gelecek. Yol boyunca C'nin ünlü tuzaklarını — taşan tamponlar, sarkan işaretçiler, bellek sızıntıları — birer birer masaya yatıracağız.

::: not
C'yi "eski bir dil" olarak küçümseme tuzağına düşme. C, 1972'de doğdu ama bugün hâlâ TIOBE'nin ilk üçünde. Onu öğrenmek nostalji değil; katmanların altını görebilen mühendis olmanın giriş bileti. C bilen biri Python'u günler içinde söker; tersi yönde geçiş yıllar sürebilir.
:::

## 2.1 İlk program: her satırın hesabı

Geleneği bozmayalım ama klasik "merhaba dünya"yı bir mühendis gözüyle, satır satır hesabını sorarak yazalım:

```c
#include <stdio.h>                 // printf'in bildirimini getirir

int main(void) {                   // programın giriş noktası
    printf("Merhaba, MertOS!\n");  // ekrana yaz; \n satır sonu
    return 0;                      // işletim sistemine "sorun yok" de
}
```

Bu beş satırda üç önemli sözleşme var. **Birincisi:** `#include <stdio.h>` bir kopyala-yapıştır komutudur; derleyicinin ön işlemcisi o başlık dosyasının içeriğini senin dosyana aynen yapıştırır. `printf` orada *bildirilmiştir* (fonksiyonun imzası), *tanımı* ise C kütüphanesindedir ve bağlama (linking) aşamasında gelir — bu süreci Bölüm 4'te parça parça izleyeceğiz. **İkincisi:** her C programı `main`'den başlar; işletim sistemi programını çalıştırırken aslında `main`'i çağırır. **Üçüncüsü:** `return 0`, çıkış kodudur. Kabuk (shell) bu değeri görür; 0 "başarı", sıfır dışı "hata" demektir. Boş bir ayrıntı gibi duran bu sayı, otomasyon betiklerinin programının başarısını anlamasının tek yoludur.

Derleyip çalıştırmak tek komut:

```term
$ gcc merhaba.c -o merhaba
$ ./merhaba
Merhaba, MertOS!
$ echo $?
0
```

`echo $?` son programın çıkış kodunu gösterir — işte `return 0`'ın gittiği yer.

::: baglanti
`gcc`'nin o tek komutun arkasında dört aşaması var: ön işleme → derleme → assembly → bağlama. Bu hattın tamamı, `gdb` ile hata ayıklama ve Makefile yazımı **Bölüm 4**'ün konusu.
:::

## 2.2 Değişkenler ve türler: kutunun boyutu

Bölüm 1'den biliyorsun: bellek, adresli bayt kutularından ibaret. C'de bir değişken tanımlamak, "bana şu boyutta bir kutu ayır ve adını şu koy" demektir. **Tür (type)**, o kutunun kaç bayt olduğunu *ve* içindeki bitlerin nasıl yorumlanacağını söyler — aynı `0100 0101` deseninin `int` olarak 69, `char` olarak `'E'` okunduğunu hatırla.

Temel türlerin tipik bir 64-bit Linux sistemindeki boyutları şöyle:

| Tür | Boyut | Aralık / kullanım |
|---|---|---|
| `char` | 1 bayt | bir karakter ya da küçük sayı (−128…127) |
| `short` | 2 bayt | küçük tam sayı |
| `int` | 4 bayt | varsayılan tam sayı (yaklaşık ±2.1 milyar) |
| `long` | 8 bayt (Linux 64-bit) | büyük tam sayı; Windows 64-bit'te **4 bayt** |
| `float` | 4 bayt | tek duyarlıklı ondalık (~7 anlamlı basamak) |
| `double` | 8 bayt | çift duyarlıklı ondalık (~15 basamak) |

Bu boyutlar standartça sabitlenmemiştir; "en az şu kadar" diye tanımlanır. Bu yüzden gerçek boyutu soran bir operatör vardır: `sizeof`. Gömülü sistemde 2 baytlık `int`'e sahip derleyiciler hâlâ hayatta — `MertOS`'u başka mimariye taşırsan bunu ilk elden görürsün. Kesin genişlik gerektiğinde (donanım register'ları, ağ paketleri) `<stdint.h>` başlığındaki `uint8_t`, `int32_t` gibi türler kullanılır; Bölüm 43'te bare-metal kodda bunlarla yaşayacağız. Sen Windows kullanıyorsun ve bu tablodaki en büyük tuzak `long`: Windows 64-bit'te (LLP64 veri modeli) `long` 4 bayttır, Linux'taki 8 bayt değildir. 64 bit'lik bir değer gerekiyorsa `long` yerine `<stdint.h>` başlığındaki `int64_t` kullan.

Bir değişken tanımı ve ilk değer ataması şöyle görünür:

```c
int   yas = 21;          // tanım + ilk değer
double pi = 3.14159;
char  harf = 'M';        // tek tırnak: TEK karakter
unsigned int sayac = 0;  // yalnız pozitif; aralık ikiye katlanır

const double G = 9.81;   // const: sonradan değiştirilemez
```

::: dikkat
İlk değer verilmemiş **yerel** değişkenin içinde çöp vardır — sıfır değil, o anda stack'te ne kaldıysa o. `int x; printf("%d", x);` her çalıştırmada farklı bir saçmalık basabilir. Global/static değişkenler ise sıfırla başlar (Bölüm 1'deki BSS segmentini hatırla). Bu ayrım, "bende çalışıyor, sende çökmüş" türü hataların klasik kaynağıdır.
:::

### Tür dönüşümü: sessiz ve sesli

C, farklı türleri aynı ifadede kullanmana izin verir ama arka planda **örtük dönüşüm (implicit conversion)** yapar ve bu bazen sessizce canını yakar. En meşhuru tam sayı bölmesidir:

```c
int toplam = 7, adet = 2;
double ort1 = toplam / adet;           // 3.0  — 3.5 değil!
double ort2 = (double)toplam / adet;   // 3.5  — açık dönüşüm (cast)
```

İlk satırda `7 / 2` iki *tam sayının* bölmesidir; sonuç daha `double`'a değmeden 3'e kırpılır. `(double)` yazımı ise **açık dönüşümdür (cast)**: "bu değeri şu türmüş gibi ele al" dersin, bölme ondalıklı yapılır. Kural basit: dönüşümün *ne zaman* olduğunu bil — atamada değil, işlem anında.

İkinci klasik tuzak, Bölüm 1'deki taşmanın C'deki yüzüdür: `int`'in sınırındayken bir adım daha atarsan, işaretli (signed) taşma **tanımsız davranıştır (UB)**. Derleyicinin bunu iki'ye tümleyen gibi saracağı garanti edilmez; optimizasyon yüzünden beklenmedik sonuçlar bile doğabilir. İşaretsiz (unsigned) türlerde ise taşma **tanımlıdır**: değer 2^n modülosuna göre sarar (`unsigned char x = 255; x++;` sonrası `x` değeri 0 olur). Sınıra yaklaşan sayaçlarda `long` ya da `unsigned` seçimini baştan yap.

## 2.3 Operatörler ve kontrol yapıları

Aritmetik (`+ - * / %`), karşılaştırma (`== != < > <= >=`) ve mantık (`&& || !`) operatörlerinin çoğu tanıdık. C'ye özgü püf noktaları öne çekelim.

**`%` yalnız tam sayılarla çalışır** ve kalanı verir: `13 % 4 == 1`. Döngüsel yapılarda (saat, dairesel tampon) vazgeçilmezdir — `MertOS`'un klavye tamponunda göreceğin `(kuyruk + 1) % BOYUT` deseni budur.

**`++` önek/sonek farkı** ifade içinde ortaya çıkar: `x++` değeri *kullandıktan sonra*, `++x` *kullanmadan önce* artırır. Tek başına satırdayken fark yoktur; karmaşık ifadeler içinde ise okunabilirlik hızla ölür — bu yüzden bu kitapta `dizi[i++]` gibi kalıpları yalnız yerleşik deyimlerde göreceksin.

**Atama `=` ile karşılaştırma `==` farklıdır** ve `if (x = 5)` yazmak geçerli C'dir: 5 atanır, 5 "doğru" sayılır, blok her zaman çalışır. Derleyici uyarılarını açık tut (`gcc -Wall`), bu tuzağı derleyicin yakalasın.

**Kısa devre (short-circuit):** `&&` solda yanlış görürse sağı hiç çalıştırmaz; `||` solda doğru görürse aynı şekilde. Bu bir performans ayrıntısı değil, bir *koruma kalıbıdır*:

```c
if (p != NULL && p->deger > 0) { ... }  // p NULL ise sağ HİÇ çalışmaz
```

Sıra kontrol akışında. `if/else` bildiğin gibi; `switch` ise bir değeri sabitlerle karşılaştırırken temizdir ama bir tuzağı vardır — **düşme (fallthrough)**:

```c
switch (komut) {
    case 'w': ileri_git();  break;
    case 's': geri_git();   break;
    case 'q':               // break YOK: bilinçli düşme
    case 'Q': kapat();      break;
    default:  bilinmeyen();
}
```

`break` yazmadığın `case`, bir alttakine "düşer". Yukarıda `'q'` ve `'Q'` için bu bilinçli bir tercih; ama unutulmuş bir `break`, sessizce iki dalı birden çalıştırır. Kural: düşme istiyorsan yorumla belli et, istemiyorsan `break`'i refleks yap.

Döngülerde `for` sayarken, `while` koşul beklerken, `do-while` "önce yap sonra sor" gerektiğinde (örneğin menüyü en az bir kez göster) kullanılır. `break` döngüyü keser, `continue` o turu atlar. Hepsi şu üçlünün varyasyonu:

```c
for (int i = 0; i < n; i++) { ... }   // sayaçlı

while (veri_var()) { ... }            // koşullu

do { goster_menu(); } while (secim != 'q');  // en az bir tur
```

### Bit operatörleri

Bölüm 1'de bitlerin bayt kutusunun içinde durduğunu gördün. C, bu bitleri doğrudan değiştirmene izin veren operatörler sunar; gömülü sürücülerde register bitlerini okuyup yazmanın yolu budur (Bölüm 43). Tabloda `a = 12` (0000 1100) ve `b = 10` (0000 1010) kullanıyorum:

| İfade | Ne yapar | Sonuç (a=12, b=10) |
|---|---|---|
| `a & b` | iki bit de 1 ise 1 (maskeleme) | 8 |
| `a \| b` | bitlerden biri 1 ise 1 (birleştirme) | 14 |
| `a ^ b` | bitler farklıysa 1 (ters çevirme) | 6 |
| `~a` | her biti ters çevirir | -13 (int'te) |
| `a << 1` | sola 1 kaydırır (her kaydırma ×2) | 24 |
| `a >> 2` | sağa 2 kaydırır (işaretsizde ÷4) | 3 |

Bit düzeyinde işlemin standart kalıbı **maske**dir: `1u << n` tek bitlik bir maske üretir; onu bir operatörle birleştirerek o bite dokunursun:

```c
#define BIT(n)  (1u << (n))      // n. bit maskesi: BIT(3) == 8

unsigned int r = 0;
r |= BIT(3);             // set:    3. bit 1 olur
r &= ~BIT(3);            // clear:  3. bit 0 olur
r ^= BIT(3);             // toggle: 3. bit ters çevrilir
if (r & BIT(3)) { ... }  // test:   3. bit 1 mi?
```

## 2.4 Fonksiyonlar: sözleşme ve çerçeve

Bir fonksiyon üç parçadan oluşur: **imza** (ne alır, ne döner), **gövde** (ne yapar) ve çağrı anında stack'te açılan **çerçeve** (Bölüm 1'deki stack frame). C'de kritik bir sözleşme vardır ve her şeyi belirler: **parametreler değerle geçer (pass by value)**. Fonksiyona bir değişken verdiğinde, fonksiyon onun *kopyasıyla* çalışır.

Bunu kanıtlayan mini deney:

```c
#include <stdio.h>

int kare_al(int x) {     // x, çağrıdaki n'in KOPYASI
    x = x * x;           // yalnız kopya değişti
    return x;
}

int main(void) {
    int n = 5;
    int k = kare_al(n);
    printf("n=%d k=%d\n", n, k);   // n=5 k=25 — n bozulmadı
    return 0;
}
```

Çağrı anında olan biteni Bölüm 1'in stack modeliyle izleyelim:

![Şekil 2.1: Fonksiyon çağrısında yığın. `kare_al(5)` çağrılınca yığına yeni bir çerçeve (parametre kopyası, yerel değişkenler, dönüş adresi) eklenir; fonksiyon dönünce çerçeve tek hamlede atılır ve `main` kaldığı yerden devam eder.](gorseller/b02_stack.png)

Çerçeve modeli üç soruyu kökten cevaplar. *Yerel değişken neden fonksiyon bitince ölür?* Çerçevesiyle birlikte atıldığı için. *Recursion neden stack taşırabilir?* Her çağrı yeni çerçeve eklediği için (derinlemesine Bölüm 15'te). *Fonksiyon çağrısının maliyeti nedir?* Bir çerçeve kurup yıkma maliyeti — çoğu zaman önemsiz, sıcak döngüde ölçmeye değer.

Bir de görgü kuralı: fonksiyonu kullanmadan önce derleyicinin onun imzasını görmesi gerekir. Ya tanımı yukarı yazarsın ya da dosyanın başına **prototip** koyarsın:

```c
int kare_al(int x);   // prototip: "böyle bir fonksiyon var"
```

Büyük projelerde prototipler `.h` başlık dosyalarında yaşar; `#include` ile herkes aynı sözleşmeyi görür. `MertOS`'ta `kstring.hpp`'nin yaptığı tam olarak budur.

## 2.5 İşaretçiler: adresi elinde tutmak

Geldik C'nin kalbine. İşaretçi hakkındaki bütün gizem tek cümlede çözülür: **işaretçi, içinde bellek adresi tutan bir değişkendir.** O kadar. Bölüm 1'de her bayt kutusunun bir numarası (adresi) olduğunu görmüştün; işaretçi o numarayı saklayan kutudur.

İki operatör bu dünyanın kapısını açar. `&` "adresini ver" der; `*` "bu adresteki kutuya git" der. Kod ve resmi yan yana koyalım:

```c
int x = 42;
int *p = &x;    // p, x'in adresini tutuyor: "p, x'i gösteriyor"

printf("%d\n", *p);   // 42 — p'nin gösterdiği kutunun İÇİ
*p = 99;              // x artık 99! p üzerinden x'i değiştirdik
```

![Şekil 2.2: İşaretçinin bellekteki gerçeği. `x` kutusunda 42 durur; `p` kutusunda ise `x`'in adresi. `p = &x` ataması "göstermek" dediğimiz ilişkiyi kurar; `*p` o adresteki kutuya erişir.](gorseller/b02_pointer.png)

`int *p` yazımındaki `*` "bu değişken bir `int`'in adresini tutar" demektir; ifade içindeki `*p` ise "adresi izle" işlemidir. Aynı sembolün iki rolü başta kafa karıştırır; ayrım şu: *tanımda* tür bilgisi, *ifadede* operatör.

Şimdi 2.4'teki `kare_al` sınırını kırabiliriz. Değerle geçiş yüzünden fonksiyon, çağıranın değişkenini değiştiremiyordu. Ama değişkenin *adresini* verirsen, fonksiyon o adrese gidip aslını değiştirebilir — birazdan Örnek 1'de meşhur `swap` ile bunu yapacağız.

::: dikkat
Hiçbir yeri göstermeyen işaretçi `NULL` ile işaretlenir. `NULL`'u izlemek (`*p`) **tanımsız davranıştır (UB)**: tipik olarak işletim sistemi programı segmentation fault ile sonlandırır; ama bu bir garanti değildir. Yine de hata en azından oluştuğu yerde görünür eğilimdedir. Asıl bela, rastgele çöp adres tutan başlatılmamış işaretçidir; o *bazen* çalışır, *bazen* başka veriyi ezer. Kural: her işaretçi ya geçerli bir adresle ya `NULL` ile doğsun.
:::

### İşaretçi aritmetiği: adım uzunluğunu tür belirler

İşaretçiye 1 eklemek, adrese 1 bayt eklemek *değildir*. `p + 1`, "bir sonraki **eleman**" demektir; kaç bayt atlanacağını işaretçinin türü söyler. `int*` için 4 bayt, `double*` için 8, `char*` için 1:

![Şekil 2.3: İşaretçi aritmetiği. `int` dizisinde her eleman 4 bayt olduğundan `p+1` adresi 4 artırır, `p+3` on iki bayt ileridedir. Aritmetiğin birimi bayt değil, elemandır.](gorseller/b02_ptr_arith.png)

Bu tasarım tesadüf değil: `p[i]` yazımı, dilin tanımı gereği `*(p + i)`'nin kısaltmasıdır. Yani köşeli parantezle yaptığın her dizi erişimi, aslında işaretçi aritmetiği + adres izlemedir. Diziyle işaretçinin neden bu kadar iç içe olduğu bir sonraki başlıkta netleşecek.

## 2.6 Diziler ve stringler: bitişik bellek

**Dizi (array)**, aynı türden elemanların bellekte **bitişik** dizilişidir. `int dizi[5]` dediğinde derleyici 20 baytlık tek parça yer ayırır. Bitişiklik iki büyük sonuç doğurur: `dizi[i]`'nin adresi çarpma-toplama ile anında hesaplanır (rastgele erişim O(1)) ve elemanlar cache'e arka arkaya girer — Bölüm 25'te bunun performans anlamını göreceğiz.

C dizilerinin sert gerçeği: **sınır kontrolü yoktur.** `dizi[5]`'e — yani olmayan altıncı elemana — yazarsan C sesini çıkarmaz; komşu belleği ezersin. Dizinin uzunluğunu da kimse saklamaz; programcı bilmek zorundadır. Eleman sayısını hesaplamanın deyimsel yolu şudur:

```c
int dizi[] = {3, 1, 4, 1, 5, 9};
size_t n = sizeof(dizi) / sizeof(dizi[0]);   // 24 / 4 = 6 eleman
```

Ama dikkat: bu numara yalnız dizinin *tanımlandığı kapsamda* çalışır. Diziyi bir fonksiyona geçirdiğin anda dizi, ilk elemanının adresine **bozunur (decay)** — fonksiyona giden şey koca dizi değil, bir işaretçidir. Bölüm 1'in şablonundaki uyarının açıklaması budur: fonksiyon içinde `sizeof(dizi)` sana işaretçi boyutunu (8) verir. Bu yüzden C'de diziler fonksiyonlara hep *adres + uzunluk* ikilisi olarak taşınır:

```c
int topla(const int *dizi, size_t n) {   // adres + eleman sayısı
    int t = 0;
    for (size_t i = 0; i < n; i++) t += dizi[i];
    return t;
}
```

İmzadaki `const`, "bu fonksiyon diziyi okur ama değiştirmez" sözleşmesidir — hem derleyici denetler hem okuyan mühendis rahatlar.

### String: sonlandırıcılı char dizisi

C'de ayrı bir string türü yoktur. **String, sonu `'\0'` (sıfır baytı) ile işaretlenmiş bir `char` dizisidir.** Bütün string dünyası bu tek kurala dayanır:

![Şekil 2.4: C string'inin anatomisi. `"Mert"` dört harf + bir sonlandırıcıdır; `strlen` sonlandırıcıyı görene kadar sayar. Sonlandırıcıdan sonraki kutuların içeriği tanımsızdır.](gorseller/b02_string.png)

`strlen` neden O(n)? Çünkü uzunluk hiçbir yerde yazmaz; fonksiyon `'\0'` görene dek tek tek yürür. `"Mert"` neden 5 bayt yer ister? Dört harf + sonlandırıcı. Sonlandırıcıyı ezersen ne olur? `strlen` ve arkadaşları senin belleğinin bittiği yeri bilemez, çöpün içinde `'\0'` arayarak yürümeye devam eder — işte klasik C güvenlik açıklarının doğduğu nokta.

Bir ayrıntı daha, Bölüm 1'in bellek haritasına bağlanır: `char *s = "sabit";` yazdığında o metin **salt-okunur** bölgede (rodata) durur; `s[0] = 'S'` **tanımsız davranıştır (UB)**; tipik olarak çökmeyle sonuçlanır. `char s[] = "kopya";` ise metni stack'e *kopyalar*, değiştirebilirsin. İşaretçi-dizi farkının en somut hâli budur.

### Tampon taşması: farkındalık

Sınır kontrolünün olmaması + uzunluğu programcının takip etmesi = C'nin en ünlü hata sınıfı: **tampon taşması (buffer overflow)**. Tarihin en pahalı güvenlik açıklarının çoğu bu ailedendir. Savunma sanayiine giden biri için bu konu "bilsen iyi olur" değil, işe alım kriteridir — güvenli kod yazma yönergeleri (MISRA C gibi) sektörde sözleşme maddesidir.

Sorunlu ve güvenli okuma yan yana. `gets`, C99'da standart kütüphanedeydi; C11'de standarttan kaldırıldı. Sınır bilgisi alamadığı için hiçbir zaman güvenli değildi:

```c
char ad[16];

gets(ad);                     // ASLA: sınır yok; C11'de kaldırıldı
scanf("%s", ad);              // AYNI DERECEDE tehlikeli: sınır yok

fgets(ad, sizeof(ad), stdin); // DOĞRU: en fazla 15 karakter + '\0'
```

`fgets`'e tamponun boyutunu söylersin; fazlasını okumaz. Kopyalamada da aynı ilke: `strcpy` yerine boyut alan güvenli kalıpları kullan (`snprintf(hedef, sizeof(hedef), "%s", kaynak)` en taşınabilir olanıdır). Genel kural şu: **bir tampona yazan her satır, tamponun boyutunu bilmek zorunda.**

::: baglanti
Taşmanın bir saldırgan elinde neden koda dönüşebildiğini — stack'teki dönüş adresinin ezilmesini — Bölüm 1'in çerçeve modeliyle şimdiden sezebilirsin. Güvenlik tarafının tamamı (OWASP, savunma teknikleri) **Bölüm 32**'de.
:::

## 2.7 struct, union, enum: kendi türünü kur

Gerçek veriler tek değişkene sığmaz: bir öğrencinin adı, numarası ve ortalaması *birlikte* anlamlıdır. **`struct`**, ilişkili alanları tek türde paketler:

```c
struct Ogrenci {
    char  ad[32];
    int   no;
    double ort;
};

struct Ogrenci o1 = {"Mert", 361, 3.42};
o1.ort = 3.55;                      // alan erişimi: nokta

struct Ogrenci *p = &o1;
p->no = 362;                        // işaretçi üzerinden: ok (->)
```

`p->no` yazımı `(*p).no`'nun kısaltmasıdır; C kodunun her yerinde bu ok ile karşılaşacaksın. Her yerde `struct Ogrenci` yazmamak için `typedef struct { ... } Ogrenci;` kalıbı kullanılır.

### sizeof sürprizi: hizalama ve dolgu

`char + int + char` alanlı bir struct'ın boyu 1+4+1 = 6 mı? Hayır — muhtemelen 12. Çünkü donanım, `int` gibi türlerin kendi boyutunun katı adreslerde durmasını ister (**hizalama, alignment**); derleyici de alanların arasına görünmez **dolgu (padding)** baytları ekler:

![Şekil 2.5: Hizalamanın bedeli. `char a; int b; char c;` dizilişinde derleyici `b`'yi 4'ün katı adrese oturtmak için 3 bayt, struct dizilerde hizayı korumak için sona 3 bayt daha dolgu ekler: sizeof 12 olur. Alanları büyükten küçüğe sıralamak (int, char, char) boyutu 8'e indirir.](gorseller/b02_struct_pad.png)

Masaüstünde bu çoğu zaman önemsizdir; gömülüde ve ağ protokollerinde değildir. Bir donanım register haritasını ya da paket başlığını struct'la modellediğinde her baytın yeri sözleşmedir — dolgu araya girerse haberleşme bozulur. Bölüm 45'te UART/SPI paketlerini kurarken bu şekle geri döneceksin.

**`union`** ise alanlarının *aynı belleği paylaştığı* yapıdır; boyutu en büyük alanı kadardır. Aynı baytlara bazen sayı bazen bayt dizisi olarak bakmak istediğinde kullanılır — tipik örnek, bir 32-bit register'a hem bütün hem bayt bayt erişmek (Bölüm 43'ün ekmek kapısı). Gündelik veri modellemede nadiren gerekir; "hangi alan dolu" bilgisini ayrıca taşımak zorunda olduğunu unutma.

**`enum`**, isimli sabitler kümesidir ve kodun okunabilirliğini bir anda değiştirir:

```c
enum Durum { BEKLIYOR, CALISIYOR, BITTI, HATA };

enum Durum d = CALISIYOR;
if (d == HATA) { ... }      // sihirli sayı 3 yerine isim
```

Durum makineleri — `MertOS`'un klavye sürücüsündeki "normal / shift basılı / escape dizisi" gibi — `enum + switch` ikilisiyle yazılır. Bölüm 22'deki State Pattern, bu fikrin nesne yönelimli büyütülmüş hâlidir.

## 2.8 Dinamik bellek: malloc sözleşmesi

Şimdiye dek boyutları derleme anında belliydi. Ama kullanıcının kaç kayıt gireceğini çalışma anında öğrenirsin. Bölüm 1'deki **heap** tam bunun için vardı; C'de kapısı `malloc`/`free` ikilisidir:

```c
#include <stdlib.h>

int *dizi = malloc(n * sizeof(int));   // heap'ten n int'lik yer iste
if (dizi == NULL) {                    // yer YOK ise NULL döner
    fprintf(stderr, "bellek yetersiz\n");
    return 1;
}
// ... kullan ...
free(dizi);                            // işin bitince GERİ VER
dizi = NULL;                           // sarkmayı önle (alışkanlık)
```

Sözleşmenin maddeleri net: `malloc` sana *başlatılmamış* (çöp dolu) bir blok verir, başarısızlıkta `NULL` döner ve **her `malloc`'un tam bir `free` eşi olmalıdır**. Sıfırlanmış bellek istersen `calloc(n, boyut)`, mevcut bloğu büyütmek istersen `realloc` kullanırsın — Örnek 4'te `realloc` ile büyüyen dizi kuracağız.

Sözleşmeyi ihlalin üç klasik yolu, üç ayrı hata sınıfıdır:

**Bellek sızıntısı (leak):** `free` etmeyi unutursun. Program çalıştıkça heap şişer. Kısa ömürlü araçlarda göze batmaz; 7/24 çalışan sunucuda ve `MertOS` gibi bir çekirdekte ölümcüldür.

**Sarkan işaretçi (dangling pointer):** `free` edersin ama işaretçi eski adresi tutmaya devam eder. Blok artık senin değil; sistem onu başkasına verebilir:

![Şekil 2.6: Sarkan işaretçi. `free(p)` bloğu sisteme iade eder ama `p`'nin içindeki adres değişmez. Bu adresi izlemek (*p) tanımsız davranıştır: bazen çalışır, bazen başka veriyi ezer, bazen çöker — en tehlikelisi de "bazen çalışması"dır.](gorseller/b02_dangling.png)

**Çifte serbest bırakma (double free):** aynı bloğu iki kez `free` edersin; heap yöneticisinin defterini bozarsın. `free` sonrası işaretçiyi `NULL`'a çekme alışkanlığı bu iki hatayı birden törpüler — `free(NULL)` tanımlı ve zararsızdır.

::: ipucu
Bu hataların hiçbirini gözle bulmak zorunda değilsin: `valgrind` aracı sızıntıyı, sarkan erişimi ve taşmayı satır numarasıyla söyler. Valgrind bir Linux aracıdır; sen Windows'ta **WSL2 içinde** çalıştıracaksın. Bölüm 4'te kuracağız; Kendin Yap projelerinde "valgrind temiz" bir başarı kriteri olacak.
:::

## 2.9 Dosya Girişi/Çıkışı: veriyi kalıcılaştırmak

Şimdiye kadar tüm verilerimiz RAM'de yaşadı ve program kapanınca buhar oldu. Gerçek programlar iz bırakır: ayar okur, log yazar, kayıt saklar. C'de bu işin kapısı `FILE*` — dosyayla aranda duran, tamponlu bir aracı nesne:

![Şekil 2.7: C dosya G/Ç mimarisi. Program dosyayla doğrudan değil, RAM'deki FILE* tamponu üzerinden konuşur; tampon dolunca (ya da fflush/fclose ile) işletim sistemi diske yazar. fclose unutulursa tampondaki son veriler diske hiç inmeyebilir.](gorseller/b02_file_io.png)

Sözleşme üç adımdır: `fopen` ile aç (mod belirterek), oku/yaz, `fclose` ile kapat. Modlar küçük bir tablodur:

| Mod | Anlamı | Dosya yoksa | Varsa |
|---|---|---|---|
| `"r"` | oku | `NULL` döner | baştan okur |
| `"w"` | yaz | yaratır | **SİLİP** baştan yazar |
| `"a"` | ekle | yaratır | sonuna ekler |
| `"rb"` / `"wb"` | ikili (binary) oku/yaz | yukarıdakiler gibi | yukarıdakiler gibi |

Metin tabanlı tam bir yaz-oku turu şöyle görünür — `malloc` sözleşmesindeki disiplinin aynısı burada da geçerli (aç → kontrol et → kullan → kapat):

```c
#include <stdio.h>

int main(void) {
    FILE *f = fopen("notlar.txt", "w");     // yazmak için aç
    if (f == NULL) {                    // açılamadı mı? (izin, disk)
        perror("notlar.txt");               // sebebi stderr'e yazar
        return 1;
    }
    fprintf(f, "78 85 91\n");          // printf'in dosyalı kardeşi
    fclose(f);                              // tamponu boşalt, kapat

    f = fopen("notlar.txt", "r");           // şimdi okumak için
    if (f == NULL) { perror("okuma"); return 1; }

    int a, b, c;
    if (fscanf(f, "%d %d %d", &a, &b, &c) == 3)   // 3 değer var mı?
        printf("ortalama: %.1f\n", (a + b + c) / 3.0);
    fclose(f);
    return 0;
}
```

Satır okumak içinse `fgets(satir, sizeof(satir), f)` kullanılır — Bölüm 2.6'daki güvenli okuma refleksinin dosya hâli; dosya bitince `NULL` döner, klasik okuma döngüsü `while (fgets(...) != NULL)` kalıbıdır.

**İkili (binary) G/Ç** ise struct'ları olduğu gibi, bayt bayt diske döker: `fwrite(&kayit, sizeof kayit, 1, f)` yazar, `fread` aynı imzayla okur. Metinden kat kat hızlı ve kompakttır; bedeli taşınabilirliktir — 2.7'deki dolgu baytları ve az önce öğrendiğin endianness dosyaya da aynen yazılır, dolayısıyla ikili format farklı mimariler arasında ancak bilinçli bir sözleşmeyle taşınır (gerçek dünyanın çözümleri Bölüm 40'taki JSON gibi metin formatları ya da sabit sıralı ikili protokollerdir).

::: dikkat
`"w"` modu acımasızdır: dosya varsa içeriği *anında* silinir — `fopen` başarılı olduğu an, tek satır yazmadan önce bile. Log ve veri dosyalarında niyetin ekleme ise `"a"` kullan. Bir de `fclose` disiplinini `free` disiplini kadar ciddiye al: tamponda bekleyen son satırlar, kapatmayan programın elektrik kesintisinde kaybettiği satırlardır.
:::

## 2.10 Fonksiyon işaretçileri: davranışı parametre yapmak

Bölüm 1'den biliyorsun: fonksiyonlar da bellekte (text segmentinde) duran komut dizileridir — yani onların da *adresi* vardır. O adresi bir değişkende tutabiliyorsan, bir fonksiyona "hangi işi yapacağını" parametre olarak geçirebilirsin demektir. Bu, C'nin en güçlü ve en az öğretilen özelliğidir.

Sözdizimi ilk bakışta ürkütür ama tek kalıptır: `int (*isim)(int, int)` — "iki `int` alıp `int` döndüren bir fonksiyonun adresini tutan `isim` adlı işaretçi". Parantezler önemli: `int *isim(int)` bambaşka bir şeydir (işaretçi döndüren fonksiyon bildirimi).

```c
#include <stdio.h>

int topla(int a, int b) { return a + b; }
int carp (int a, int b) { return a * b; }

int uygula(int (*islem)(int, int), int x, int y) {
    return islem(x, y);              // adresteki fonksiyonu çağır
}

int main(void) {
    int (*f)(int, int) = topla;   // ad, adresine bozunur
    printf("%d\n", uygula(f, 3, 4));     // 7
    printf("%d\n", uygula(carp, 3, 4));  // 12 — davranış parametre
    return 0;
}
```

Bu desenin standart kütüphanedeki yıldızı `qsort`'tur: her türden diziyi sıralayabilir, çünkü "hangisi önce gelir?" sorusunu *sana* sorar — bir **karşılaştırıcı (comparator)** fonksiyon istersin. İmzası anlaşmalıdır: iki `const void*` alır (her türe uyabilsin diye), negatif/sıfır/pozitif döndürür (küçük/eşit/büyük). Örnek 3'te struct dizisini iki farklı ölçüte göre sıralayarak bunu ete kemiğe büründüreceğiz.

Aynı fikrin öbür adı **geri çağırma (callback)**: "şu olay olunca şu fonksiyonumu çağır" diye adres bırakmak. Bölüm 44'te kesme (interrupt) işleyicileri, Bölüm 31'de socket olayları, GUI dünyasında her düğme — hepsi callback'tir. `MertOS`'ta klavye sürücüsünün "tuşa basılınca çağrılacak fonksiyon" kaydı da tam olarak bu desendir.

## 2.11 Ön işlemci ve büyük proje düzeni

Bölüm 4'te ön işlemcinin `#` satırlarını nasıl açtığını göreceksin; burada onun *doğru kullanım* kurallarını koyalım, çünkü çok dosyalı her C projesi (MertOS dahil) bu kurallarla ayakta durur.

**`#define` iki işe yarar ve ikincisi tuzaklıdır.** Sabit tanımı masumdur: `#define MAX_KAYIT 100`. Makro ise metin yapıştırmadır ve parantezsiz yazılırsa seni arkandan vurur:

```c
#define KARE_YANLIS(x)  x * x
#define KARE_DOGRU(x)   ((x) * (x))

int a = KARE_YANLIS(2 + 3);   // 2 + 3 * 2 + 3 = 11  (!!)
int b = KARE_DOGRU(2 + 3);    // ((2+3) * (2+3)) = 25
```

Ön işlemci matematik bilmez, *metin* yapıştırır: `x` gördüğü her yere `2 + 3` koyar ve operatör önceliği faciası doğar. Kural: makro parametrelerini ve gövdenin tamamını paranteze al — ya da modern C'de çoğu zaman daha iyisi, makro yerine fonksiyon yaz.

**Include guard, başlıkların emniyet kilididir.** Aynı başlık, dolaylı yollarla bir dosyaya iki kez dahil olursa (a.h → b.h → c.h zincirlerinde kaçınılmazdır) tanımlar çakışır. Her `.h` dosyası şu zırhla yazılır:

```c
#ifndef MAT_H          /* MAT_H tanımlı değilse... */
#define MAT_H          /* şimdi tanımla ve içeriği işle */

int kare(int x);
double ortalama(const int *dizi, size_t n);

#endif                 /* ikinci gelişte blok komple atlanır */
```

**`static` ve `extern`, isimlerin görünürlük ayarıdır.** Dosya düzeyinde `static` "bu isim yalnız bu dosyanın malı" der — başka dosyayla isim çakışmasını keser ve niyetini belgeler (yardımcı fonksiyonlarını `static` yap). `extern` ise tersidir: "bu global değişken başka dosyada tanımlı, ben yalnız kullanıyorum." Altın kural şu: **başlık dosyasına bildirim yazılır, tanım asla** — `.h`'ye konan bir global tanım, onu include eden her `.o`'da birer kopya yaratır ve bağlayıcı "multiple definition" ile isyan eder. Bölüm 4'teki bağlama aşamasını görünce bu hatanın mekaniği tamamen netleşecek.

## Çözümlü Örnekler

### Örnek 1 (★): swap neden çalışmaz?

**Adım 1 — Anla.** İki değişkenin değerini takas eden `takas` fonksiyonu yazılmış ama çalışmıyor. Neden? Düzelt. Fonksiyon şöyle:

```c
void takas(int a, int b) {      // KOPYALAR gelir
    int gecici = a;
    a = b;
    b = gecici;                 // yalnız kopyalar takas oldu
}
```

**Adım 2 — Örnekle.** Somut değerlerle deneyelim: `x = 3`, `y = 7`. `takas(x, y)` çağrısından sonra `x` ve `y` hâlâ 3 ve 7'dir; fonksiyonun içindeki `a` ve `b` ise 7 ve 3 olmuştur. Takas fonksiyonun içinde gerçekleşti, ama `main` bunu göremiyor. Nedenini bulalım.

**Adım 3 — Kaba çöz.** İlk fikir şu: `takas`'ın içini nasıl değiştirirsem değiştireyim, `a` ve `b` çerçevedeki kopyalar olduğu için sonuç dışarı çıkmaz. Dışarı ulaşmanın tek yolu, fonksiyona orijinallerin *adresini* vermektir.

**Adım 4 — Örüntü.** 2.4'ün sözleşmesi: parametreler değerle geçer. Demek ki bir değişkeni değiştirecek fonksiyonun imzası `int *` almalı ve çağıran `&x`, `&y` ile adres vermeli. Örüntü şu: *değiştirmek istediğin kutunun adresini ver.*

**Adım 5 — İyileştir.** Aynı fonksiyonun işaretçili doğrusu ve kullanımı şöyle:

```c
#include <stdio.h>

void takas(int *a, int *b) {    // adresler gelir
    int gecici = *a;            // a'nın gösterdiği kutunun içi
    *a = *b;                    // x'in kutusuna y'nin değeri
    *b = gecici;
}

int main(void) {
    int x = 3, y = 7;
    takas(&x, &y);              // ADRESLERİ veriyoruz
    printf("x=%d y=%d\n", x, y);
    return 0;
}
```

**Adım 6 — Doğrula.** `takas(&x, &y)` çağrısında `*a` ve `*b`, doğrudan `main`'in `x` ve `y` kutularını gösterir. Elle izleyelim:

| Aşama | gecici | x (`*a`) | y (`*b`) |
|---|---|---|---|
| başlangıç | — | 3 | 7 |
| `gecici = *a` | 3 | 3 | 7 |
| `*a = *b` | 3 | 7 | 7 |
| `*b = gecici` | 3 | 7 | 3 |

Derleyip çalıştırdığında gerçek çıktı tabloyla eşleşir:

```term
$ gcc takas.c -o takas && ./takas
x=7 y=3
```

Şekil 2.1'in diliyle: bozuk sürümde takas, `takas` çerçevesinin *içinde* olup çerçeveyle birlikte çöpe gitti. Doğru sürümde çerçeveye kopyalanan şey adresler; `*a` ile çerçevenin dışına, `main`'in kutularına uzandık.

**Bunu AI'sız yazabilir misin?** Boş dosyada, bu sayfaya bakmadan: önce bozuk sürümü yaz, çalışmadığını gör, sonra düzelt. "Neden `&` ile çağırıyorum?" sorusuna tek cümlelik cevabın hazır olsun.

### Örnek 2 (★★): String'i yerinde ters çevir

**Adım 1 — Anla.** Bir string'i ek bellek kullanmadan (yerinde, in-place) ters çeviren `ters_cevir` fonksiyonunu yaz. `"kalem"` → `"melak"`.

**Adım 2 — Örnekle.** `"kalem"` beş karakter; indeksleri 0'dan 4'e. Ters çevirmede ilk ve son karakter yer değiştirir (`k` ↔ `m`), sonra ikinci ve sondan ikinci (`a` ↔ `e`); ortadaki `l` yerinde kalır.

**Adım 3 — Kaba çöz.** İki parmak hayal ederim: biri başta, biri sonda. Karakterleri takas eder, parmakları birbirine yürütürüm; ortada buluşunca iş biter. Son karakterin indeksi `strlen - 1` — sonlandırıcıyı takas etmeye kalkmak klasik acemi hatası.

**Adım 4 — Örüntü.** Takası zaten Örnek 1'de yazdım. Burada yalnız indekslerle çalışan bir örüntü var: `sol` soldan, `sag` sağdan başlar, `sol < sag` olduğu sürece takas yapılıp ikisi birer adım içeri gelir.

**Adım 5 — İyileştir.** Kodu şöyle yazıyorum:

```c
#include <stdio.h>
#include <string.h>

void ters_cevir(char *s) {
    size_t sol = 0;
    size_t sag = strlen(s);          // uzunluk
    if (sag == 0) return;            // boş string: iş yok
    sag--;                           // son karakterin indeksi
    while (sol < sag) {
        char gecici = s[sol];
        s[sol] = s[sag];
        s[sag] = gecici;
        sol++;
        sag--;                       // parmaklar ortaya yürür
    }
}

int main(void) {
    char kelime[] = "kalem";         // dizi: değiştirilebilir kopya
    ters_cevir(kelime);
    printf("%s\n", kelime);          // melak
    return 0;
}
```

**Adım 6 — Doğrula.** `"kalem"` için elle iz sürelim; her satır bir turun sonundaki durumdur:

| Aşama | sol | sag | s |
|---|---|---|---|
| başlangıç | 0 | 4 | `kalem` |
| tur 1: `k` ↔ `m` | 1 | 3 | `malek` |
| tur 2: `a` ↔ `e` | 2 | 2 | `melak` |
| `sol < sag` yanlış, dur | 2 | 2 | `melak` |

Döngü koşulu `sol < sag`: eşitlendiklerinde (tek uzunlukta ortadaki karakter) takasa gerek yok. Dikkat çekmek istediğim asıl satır `char kelime[] = "kalem";` — 2.6'daki ayrım burada iş başında: `char *kelime = "kalem"` yazsaydık salt-okunur metni değiştirmeye kalkar, çökerdik.

**Bunu AI'sız yazabilir misin?** Ek soru: `sag` neden `size_t` ve boş string kontrolü neden `sag--`'dan *önce*? (İpucu: `size_t` işaretsizdir; 0'dan bir eksiği Bölüm 1'deki çemberde nereye düşer?)

### Örnek 3 (★★): qsort ile kayıtları sıralamak

**Adım 1 — Anla.** `Ogrenci` struct dizisini önce ortalamaya göre (büyükten küçüğe), sonra ada göre (alfabetik) sırala — sıralama algoritması yazmadan, `qsort` ile.

**Adım 2 — Örnekle.** Üç öğrenci var: Mert 3.42, Ada 3.91, Can 3.42. Ortalamaya göre azalan sırada Ada en önde olmalı. Mert ile Can'ın ortalaması eşit; dolayısıyla aralarındaki sıra bu ölçütle belirlenemez. Bu noktaya Açıklama'da döneceğiz.

**Adım 3 — Kaba çöz.** Kaba yol, iki iç içe döngüyle kendi sıralamamı yazmak olurdu; ama bu örnek algoritmayı `qsort`'a bırakmamı istiyor. `qsort` dört şey ister: dizinin adresi, eleman sayısı, bir elemanın boyutu ve karşılaştırıcı. Karşılaştırıcının imzası sabit: `int f(const void*, const void*)`. İçeride `void*`'ları kendi türüme çevirip alanları kıyaslarım. Ortalama `double` olduğundan `a - b` numarası çalışmaz (sonuç `int`'e kırpılır); açık karşılaştırma yazarım.

**Adım 4 — Örüntü.** Mekanik ile ölçüt ayrılıyor: `qsort` hangi elemanın önce geleceğini bilmez, karşılaştırıcıya sorar. Ölçüt değişince yalnız karşılaştırıcı değişir; dizinin kendisi ve `qsort` aynı kalır. Bu, 2.10'daki "davranışı parametre yap" fikrinin ta kendisi.

**Adım 5 — İyileştir.** Çözüm kodu şöyle:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char ad[24]; double ort; } Ogrenci;

int ort_azalan(const void *a, const void *b) {
    const Ogrenci *x = a, *y = b;        // void* -> Ogrenci*
    if (x->ort < y->ort) return  1;      // büyük olan öne
    if (x->ort > y->ort) return -1;
    return 0;
}

int ada_gore(const void *a, const void *b) {
    const Ogrenci *x = a, *y = b;
    return strcmp(x->ad, y->ad);         // strcmp zaten -/0/+ döner
}

int main(void) {
    Ogrenci sinif[] = {{"Mert", 3.42}, {"Ada", 3.91}, {"Can", 3.42}};
    size_t n = sizeof(sinif) / sizeof(sinif[0]);

    qsort(sinif, n, sizeof(Ogrenci), ort_azalan);
    for (size_t i = 0; i < n; i++)
        printf("%-6s %.2f\n", sinif[i].ad, sinif[i].ort);

    qsort(sinif, n, sizeof(Ogrenci), ada_gore);  // başka ölçüt
    for (size_t i = 0; i < n; i++)
        printf("%-6s %.2f\n", sinif[i].ad, sinif[i].ort);
    return 0;
}
```

**Adım 6 — Doğrula.** `qsort`'un hangi çiftleri hangi sırayla soracağı kütüphaneye bağlıdır; biz karşılaştırıcının tek tek çiftlerdeki sonucuna bakarız:

| Çift (x, y) | x->ort | y->ort | dönüş | yorum |
|---|---|---|---|---|
| Mert, Ada | 3.42 | 3.91 | 1 | Ada öne geçer |
| Ada, Can | 3.91 | 3.42 | -1 | Ada öne kalır |
| Mert, Can | 3.42 | 3.42 | 0 | eşit: sıra belirsiz |

Derleyip çalıştırdığında terminal şöyle görünür:

Çıktının ilk üç satırı ortalamaya göre, sonraki üç satırı ada göre sıralı olanıdır. Aşağıdaki çıktı Ubuntu 24.04 üzerinde, glibc 2.39 ile WSL2'de gerçekten çalıştırılarak alındı:

```term
$ gcc -Wall sirala.c -o sirala && ./sirala
Ada    3.91
Mert   3.42
Can    3.42
Ada    3.91
Can    3.42
Mert   3.42
```

Bu çıktı *bir* çıktıdır. **`qsort` kararlı (stable) değildir**: C standardı, eşit elemanların göreli sırasını koruyacağını garanti etmez. glibc 2.39 `qsort`'u (`stdlib/qsort.c`) bellek yeterliyse birleştirmeli sıralama ile çalıştırır; bu yüzden burada Mert ile Can'ın sırası korunmuş görünür. Ama bu bir garanti değildir: başka bir derleyici ya da C kütüphanesi (ör. Windows'taki) farklı bir sıra üretebilir. Buna güvenmemelisin; kararlı bir sonuç istiyorsan eşitlik durumunda ikinci ölçütü (ada) karşılaştırıcıya eklemelisin.

**Açıklama:** İşin özü şu: sıralama *mekaniği* (`qsort`'un içindeki algoritma) ile sıralama *ölçütü* (senin karşılaştırıcın) birbirinden ayrıldı — 2.10'daki "davranışı parametre yap" fikrinin standart kütüphanedeki hâli. `const void*` imzası, `qsort`'un her türle çalışabilmesinin bedeli: tür bilgisini sen geri kazandırıyorsun. Dikkat edilecek incelik `double` karşılaştırması: `return x->ort - y->ort` yazsaydık 0.49'luk fark `int`'e kırpılıp 0 olur, sıralama sessizce bozulurdu.

**Bunu AI'sız yazabilir misin?** Üçüncü bir karşılaştırıcı ekle: önce ortalamaya, ortalamalar eşitse ada göre (Mert/Can çifti deterministik sıralansın). Hangi karşılaştırıcıyı hangisinin *içinden* çağırırsın?

### Örnek 4 (★★★): realloc ile büyüyen dizi

**Adım 1 — Anla.** Kullanıcıdan sayı okuyup (kaç tane geleceği bilinmiyor, 0 bitirir) hepsini saklayan, sonra ortalamayı basan program yaz. Sabit boyutlu dizi yasak; bellek gerektikçe büyüsün.

**Adım 2 — Örnekle.** Girdi `5 8 2 9 0` ise dört sayı saklanır ve ortalama `(5+8+2+9) / 4 = 6.00` çıkar. Girdi yalnızca `0` ise hiç sayı yoktur; program ortalama basmadan çıkmalıdır.

**Adım 3 — Kaba çöz.** En kaba yol her sayıda bir eleman daha yer istemek: `realloc(veri, (adet + 1) * sizeof(int))`. Doğru çalışır, ama her eklemede bir büyütme çağrısı yapılır. Bilinmeyen boyut = heap + `realloc`; asıl soru, *ne sıklıkla* büyüteceğimiz.

**Adım 4 — Örüntü.** Klasik strateji **kapasiteyi ikiye katlamak**: 4'le başla, dolunca 8, 16, 32... Bölüm 7'de bu stratejinin neden "amortize O(1)" olduğunu kanıtlayacağız; bugün deseni kuralım. `realloc` başarısız olursa `NULL` döner ama eski blok yaşar — sonucu *geçici* işaretçiye almak şart, yoksa elindeki tek adresi ezip sızıntı yaratırsın.

**Adım 5 — İyileştir.** Kodu şöyle yazıyorum:

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t kapasite = 4, adet = 0;
    int *veri = malloc(kapasite * sizeof(int));
    if (veri == NULL) return 1;

    int okunan;
    while (scanf("%d", &okunan) == 1 && okunan != 0) {
        if (adet == kapasite) {              // yer bitti: ikiye katla
            size_t yeni_kap = kapasite * 2;
            int *yeni = realloc(veri, yeni_kap * sizeof(int));
            if (yeni == NULL) {              // büyütme başarısız
                free(veri);              // eski blok bizim: bırak
                return 1;
            }
            veri = yeni;                     // ancak şimdi güncelle
            kapasite = yeni_kap;
        }
        veri[adet++] = okunan;
    }

    if (adet > 0) {
        long toplam = 0;
        for (size_t i = 0; i < adet; i++) toplam += veri[i];
        printf("%zu sayi, ort %.2f\n", adet, (double)toplam / adet);
    }
    free(veri);
    return 0;
}
```

**Adım 6 — Doğrula.** Terminaldeki `5 8 2 9 0` girdisinde büyütme hiç tetiklenmez (4 sayı, kapasite 4). Kapasitenin büyüdüğünü görmek için girdiyi `5 8 2 9 1 0` yapıp elle izleyelim:

| Okunan | adet (önce) | kapasite (önce) | adet = kapasite? | işlem | adet (sonra) | kapasite (sonra) |
|---|---|---|---|---|---|---|
| 5 | 0 | 4 | hayır | `veri[0] = 5` | 1 | 4 |
| 8 | 1 | 4 | hayır | `veri[1] = 8` | 2 | 4 |
| 2 | 2 | 4 | hayır | `veri[2] = 2` | 3 | 4 |
| 9 | 3 | 4 | hayır | `veri[3] = 9` | 4 | 4 |
| 1 | 4 | 4 | **evet** | `realloc` 4 → 8, `veri[4] = 1` | 5 | 8 |
| 0 | 5 | 8 | — | `0` geldi, döngü biter | 5 | 8 |

Bu girdide son durum `adet = 5`, toplam 25; ortalama 5.00 olur. Terminal örneğinin (4 sayı) çıktısı ise şöyledir:

```term
$ gcc ortalama.c -o ortalama
$ ./ortalama
5 8 2 9 0
4 sayi, ort 6.00
```

**Açıklama:** Üç ayrıntı bu kodu "öğrenci kodu"ndan ayırır. (1) `realloc` sonucu önce `yeni`'ye alınır; `NULL` gelirse `veri` hâlâ geçerlidir ve `free` edilebilir. (2) Ortalama `(double)toplam / adet` — 2.2'deki tam sayı bölmesi tuzağına düşmedik. (3) Tek çıkış disiplini: hangi yoldan çıkarsak çıkalım blok ya `free` edildi ya hiç alınamadı — sızıntı yok. `adet == kapasite` anında büyütmenin `veri[adet++]`'tan *önce* olması da taşmayı kökten engelliyor.

**Bunu AI'sız yazabilir misin?** Asıl sınav kodu ezberlemek değil: "neden geçici işaretçi?", "neden ikiye katlama?" sorularını kâğıda kendi cümlelerinle yazabilmek.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan kod üretmek değil, C'nin bellek modelini parmaklarına işlemek. Takıl, kâğıda çiz, `printf`'le izle — ama çözümü dışarıdan alma.
:::

### Proje 1 (★★): Kendi string kütüphaneni yaz

**Amaç:** `<string.h>`'yi yasakla ve dört temel fonksiyonu sıfırdan yaz: `benim_strlen`, `benim_strcpy`, `benim_strcat`, `benim_strcmp`. `MertOS`'un `kstring.hpp`'sinde bu ailenin C++ akrabalarını zaten kullanıyorsun — şimdi çekirdeğin altındaki mantığı kendin kur.

**Beklenen davranış:** Standart kütüphaneyle aynı sözleşmeler: `strlen` sonlandırıcıyı saymaz; `strcpy` sonlandırıcıyı da kopyalar ve hedefi döndürür; `strcmp` sözlük sırasına göre negatif/0/pozitif döner.

**Önerilen yaklaşım:** Hepsinin iskeleti aynı: `'\0'` görene kadar yürü. `strcat` için önce sonu bul, sonra oradan kopyala. `strcmp` için farkı bulduğun ilk karakterde `s1[i] - s2[i]` döndür. Test programında kendi fonksiyonlarını gerçek `<string.h>` ile karşılaştır (test dosyasında include serbest).

**Başarı kriterleri:** Boş string, tek karakter ve uzun stringlerde standartla birebir aynı sonuç; `benim_strcpy(hedef, "")` doğru çalışıyor; hiçbir fonksiyonda sabit boyut varsayımı yok.

### Proje 2 (★★★): Dinamik öğrenci kayıt sistemi

**Amaç:** Bu bölümün tüm silahlarını tek projede birleştir: `struct + malloc/realloc + fgets + enum`. Menülü bir konsol uygulaması: öğrenci ekle, listele, numarayla ara, çık.

**Beklenen davranış:** Kayıt sayısı sınırsız (kapasite ikiye katlanarak büyür). İsimler boşluk içerebilir (`fgets` ile oku, sondaki `\n`'i temizle). Çıkışta tüm bellek serbest bırakılır.

**Önerilen yaklaşım:** `typedef struct { char ad[64]; int no; double ort; } Ogrenci;` + ayrı bir `Kayitlar` struct'ı (işaretçi, adet, kapasite) tasarla. Menü `enum Secim` + `switch` olsun. Büyütme mantığını Örnek 4'ten *bakmadan* yeniden kur.

**Başarı kriterleri:** 1000 kayıt eklemek sorunsuz; `valgrind` (kurabildiysen) "0 bytes lost" diyor; 70 karakterlik isim girildiğinde taşma değil, düzgün kırpma oluyor; arama bulamayınca çökmek yerine mesaj veriyor.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak.

1. **★ — Boyutlar.** `char s[] = "abc";` için `sizeof(s)` ile `strlen(s)` kaç eder? Aynı `s`'yi bir fonksiyona `char *p` olarak verirsen `sizeof(p)` ne döner ve neden?
2. **★ — İşaretçi mi dizi mi?** `int a[5];` ve `int *p = a;` için `a + 1` ile `&a + 1` ifadelerinin adres olarak farkını açıkla. `sizeof(a)` ile `sizeof(p)` neden farklıdır?
3. **★ — Hizalama.** `struct { char a; short b; char c; }` yapısının `sizeof` değeri kaçtır? Alanları yeniden sıralayarak boyutu 4 bayta indirebilir misin?
4. **★★ — Yerel dizi döndürmek.** `int *olustur(void) { int x[10]; return x; }` neden tehlikelidir? Çağıran taraf bu işaretçiyle ne yaparsa tanımsız davranışa girer?
5. **★★ — Mülakat: boşlukları sil.** Bir `char` dizisindeki tüm boşlukları ek bellek kullanmadan, yerinde sil. Sonlandırıcıyı ve yeni uzunluğu nasıl korursun?
6. **★★ — Mülakat: bit sayma.** Bir `unsigned int` içindeki 1 bitlerinin sayısını bul. `n &= n - 1` ifadesinin her adımda ne yaptığını anlatıp döngü sayısını 1 bitlerinin sayısı kadar tut.
7. **★★ — Mülakat: 2'nin kuvveti mi?** Bir tamsayının 2'nin kuvveti olup olmadığını döngü kullanmadan tek bir bit işlemiyle kontrol et. 0 için cevabın ne olması gerektiğini tartış.
8. **★★ — Mülakat: XOR ile takas.** Geçici değişken kullanmadan iki `int`'in değerini `^` ile takas et. Yöntem neden iki *farklı* bellek konumu için çalışır, aynı konum için neden çalışmaz?
9. **★★ — Mülakat: iki işaretçiyle toplam.** Sıralı bir `int` dizisinde toplamı `T` olan iki eleman var mı? İki işaretçiyi uçlardan içeri yürüterek bunu O(n) zamanda ve sabit ek bellekte bul.
10. **★★★ — Mülakat: ilk tekrarsız karakter.** Bir `char` dizisinde tekrar etmeyen ilk karakteri bul. 256 elemanlı bir sayaç dizisiyle çöz; `char` işaretliyse sayaç indeksinde neden dikkat gerektiğini açıkla.
11. **★★★ — Mülakat: n×m matris.** `malloc` ile satır işaretçileri dizisi ve her satır için ayrı bir blok kullanarak bir `int` matrisi oluştur ve sızıntı olmadan serbest bırak. Hangi `NULL` kontrolünü unutursan hangi bloklar sızar?
12. **★★★ — Bit ters çevirme.** Bir `unsigned int`'in 32 bitini ters sırada üreten fonksiyonu yaz (en düşük bit en yüksek olur). Kaç iterasyon gerektiğini ve her iterasyonda hangi maske ile kaydırma kullanacağını kâğıtta belirle.

## Kod Okuma Egzersizi

Bu bölümün egzersizi, Linux çekirdeğinin tek bir dosyasından iki gerçek fonksiyon: `lib/string.c` (Linux v6.6 etiketi). İlki `strlen`. Aşağıdaki kesit sadeleştirilmiştir: `#ifndef __HAVE_ARCH_STRLEN` koruması ve `EXPORT_SYMBOL` satırı çıkarılmış, gövde ise aynen korunmuştur:

```c
size_t strlen(const char *s)
{
    const char *sc;

    for (sc = s; *sc != '\0'; ++sc)
        /* nothing */;
    return sc - s;
}
```

İkincisi aynı dosyadaki `strcpy` (`lib/string.c`, Linux v6.6). Bu kesit de sadeleştirilmiştir: `#ifndef __HAVE_ARCH_STRCPY` koruması ve `EXPORT_SYMBOL` satırı çıkarılmıştır:

```c
char *strcpy(char *dest, const char *src)
{
    char *tmp = dest;

    while ((*dest++ = *src++) != '\0')
        /* nothing */;
    return tmp;
}
```

**Sorular — cevaplamadan geçme:**

- Linux `strlen`'inde döngünün gövdesi neden boş? İşin tamamı nerede yapılıyor?
- `sc - s` ifadesi ne hesaplar? İki işaretçiyi çıkarmak neden "eleman sayısı" verir (Şekil 2.3'ü düşün)?
- `strcpy`'de döngü ne zaman durur? İpucu: atama ifadesinin *değeri*, atanan değerdir; `'\0'` atandığı an koşul ne olur?
- `*dest++ = *src++` ifadesinde sağdaki `*src` ile `src++` hangi sırayla değerlendirilir? Sonek `++`'ın 2.3'teki tanımı burada neden kritik? (Döngü gövdesi boş; tüm iş bu ifadede.)
- Fonksiyon neden `tmp`'yi döndürür, `dest`'i neden doğrudan döndürmez?
- Bu `strcpy` neden tehlikeli sayılır ve modern kodda yerine ne kullanılır (2.6'ya dön)?

## Bölüm Özeti

Bu bölümde C'nin çekirdeğini, Bölüm 1'in bellek modelinin üstüne inşa ettik:

- **Tür = kutunun boyutu + bitlerin yorumu.** `sizeof` gerçek boyutu söyler; örtük dönüşümler (özellikle tam sayı bölmesi) sessiz hata kaynağıdır; işaretli tamsayı taşması C'de tanımsız davranıştır (UB); işaretsiz türler ise modulo sarar.
- **Kontrol yapılarında** `=`/`==` karışması, `switch` düşmesi ve kısa devrenin koruma gücü — üçü de mülakat ve gerçek kod klasiği.
- **Fonksiyonlar değerle çağrılır**; her çağrı stack'te çerçeve açar, dönüş çerçeveyi yıkar. Orijinali değiştirmenin yolu adres geçirmektir.
- **İşaretçi = adres tutan değişken.** `&` adres alır, `*` adresi izler; aritmetiğin birimi bayt değil elemandır; `p[i]` aslında `*(p+i)`'dir.
- **Dizi bitişik bellektir**, fonksiyona geçerken işaretçiye bozunur; **string, `'\0'` sonlandırıcılı char dizisidir.** Sınır kontrolü yoktur — tampona yazan her satır tamponun boyutunu bilmek zorundadır (`fgets`, `snprintf`).
- **`struct`** ilişkili veriyi paketler (hizalama dolgusuna dikkat), **`union`** aynı belleğe farklı gözlükler takar, **`enum`** sihirli sayıları isimlendirir.
- **`malloc` sözleşmesi:** başlatılmamış blok, başarısızlıkta `NULL`, her bloğa tam bir `free`. Üç büyük ihlal: sızıntı, sarkan işaretçi, çifte serbest bırakma.
- **Dosya G/Ç** aynı disiplinle çalışır: `fopen` (mod!) → kontrol → kullan → `fclose`. `"w"` dosyayı siler, `fgets` döngüsü satır okur, `fwrite/fread` struct'ı ikili döker — dolgu ve endianness ikili formatın taşınabilirlik bedelidir.
- **Fonksiyon işaretçisi** davranışı parametre yapar: `int (*f)(int,int)`; `qsort`'un karşılaştırıcısı ve tüm callback dünyası bu desendir.
- **Ön işlemci disiplini:** makro parametrelerini parantezle, her başlığa include guard, yardımcılara `static`, başlığa bildirim — tanım asla.

**Sonraki bölümde:** Öğrendiğin her şeyi yanına alıp Python'a geçiyoruz — ama turist olarak değil, C bilen biri olarak. Referanslar ile işaretçilerin, çöp toplayıcı ile `free`'nin, `list` ile dizinin hesabını soracağız: **Bölüm 3 — Python**.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. `int *p` tanımındaki `*` ile `*p = 5` ifadesindeki `*` arasındaki fark nedir?
2. Dizi ile işaretçi aynı şey midir? `sizeof` ikisinde neden farklı davranır?
3. `char *s = "abc"` ile `char s[] = "abc"` arasındaki fark nedir; hangisi değiştirilebilir, neden?
4. `malloc` ile `calloc`'un farkı nedir? `realloc` başarısız olursa eski bloğa ne olur?
5. Şu kodda kaç hata var: `char *f() { char t[8]; gets(t); return t; }` (İpucu: en az üç.)
6. `qsort`'un karşılaştırıcısı neden `const void*` alır ve `double` alanları karşılaştırırken `a - b` döndürmek neden hatadır?
7. Include guard ne sorunu çözer? Başlık dosyasına global değişken *tanımı* koymak neden "multiple definition" hatasıyla biter?
:::
