## 23.5 Araçlar: biçimlendirme ve statik analiz

İnsanlar biçim konusunda uzun uzun tartışabilir; tartışılacak bir şey kalmamalıdır. Biçimlendirme aracı boşluk, girinti ve parantez yerleşimini tek bir kurala bağlar. Statik analiz aracı ise kodu çalıştırmadan hatalı kalıpları bulur. İkisi de küçük bir kurulum bedeli karşılığında gelir ve kod incelemesinde insanın yapması gereken işi azaltır. Bu alt bölümde ikisini de gerçek dosyalar üzerinde çalıştırıyoruz.

### Biçimlendirme: clang-format ve black

Aşağıdaki C dosyası bilerek dağınık yazıldı: tek satırda birden çok ifade, tutarsız boşluklar, bazı yerlerde süslü parantez yok.

```c
#include <stdio.h>
#include <stdlib.h>
int olc(int *a,int n){int s=0;
for(int i=0;i<n;i++){ if(a[i]>0){s+=a[i];}else{ s-=a[i] ;} }
if(s>100){printf("buyuk %d\n",s);return 1;}
return 0;}
```

clang-format, ayarlarını bir `.clang-format` dosyasından okur. Bu bölümde Linux çekirdeği stiline yakın bir ayar kullandık: girinti 8 ve sekme, açılış parantezi kontrol satırının sonunda, fonksiyon parantezi kendi satırında.

```term
$ cat .clang-format
BasedOnStyle: LLVM
IndentWidth: 8
UseTab: Always
BreakBeforeBraces: Linux
ColumnLimit: 80
$ clang-format kotu_bicim.c
```

Çıktı aşağıda. Sekmeler okunabilirlik için 4 boşlukla gösterildi; gerçek dosyada sekmedir.

```c
#include <stdio.h>
#include <stdlib.h>
int olc(int *a, int n)
{
    int s = 0;
    for (int i = 0; i < n; i++) {
        if (a[i] > 0) {
            s += a[i];
        } else {
            s -= a[i];
        }
    }
    if (s > 100) {
        printf("buyuk %d\n", s);
        return 1;
    }
    return 0;
}
```

Dikkat edilecek nokta, aracın yalnızca biçimi değiştirdiği, mantığa dokunmadığıdır. Biçim aracı bir "temizlik" değil, bir "eşitleme"dir: her geliştirici aynı kuralla yazmış gibi görünür ve incelemede tartışılacak biçim sorusu kalmaz. Python tarafında aynı işi `black` ya da `ruff format` yapar. Aynı dağınıklığın Python karşılığını `black` ile biçimlendirdik (`black dosya.py` komutu dosyayı yerinde değiştirir):

```python
def ort( xs ,ilk = 0 ):
    return sum(xs)/len(xs)  if xs  else ilk
AD=  {"a":1,
  "b":2}
```

Sonuç:

```python
def ort(xs, ilk=0):
    return sum(xs) / len(xs) if xs else ilk


AD = {"a": 1, "b": 2}
```

Biçim araçlarında bir uyarı: aracın biçimi değiştirmesi, dosyanın anlamını değiştirmez ama diff'i büyütür. Bu yüzden biçimlendirmeyi tek bir ayrı commit'te yap; mantık değişikliğiyle karıştırma. Bu, Bölüm 38'de git iş akışında yeniden karşımıza çıkacak.

### Derleyici uyarıları: bedava hata avcısı

Derleyicinin uyarıları, bir hata ayıklayıcının bulacağı şeyleri çalıştırmadan söyler. Aşağıdaki C dosyasında dört ayrı kalıp var. Her biri gerçek bir hataya yol açabilir.

```c
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

int toplam_say(const int *dizi, size_t n)
{
    int toplam = 0;
    for (int i = 0; i < n; i++)
        toplam += dizi[i];
    return toplam;
}

void yuzde_yaz(double oran)
{
    int yuzde = oran * 100;
    printf("%d\n", yuzde);
}

int dogrula(int deger)
{
    int sonuc = 0;
    if (deger > 0) {
        int sonuc = deger * 2;   /* golgeleme */
        (void)sonuc;
    }
    return sonuc;
}

int main(void)
{
    uint8_t sayac = 300;          /* tasma */
    int ilk;
    if (sayac > 10)
        ilk = 1;
    printf("%d %d\n", ilk, dogrula(3));
    yuzde_yaz(0.256);
    return toplam_say(NULL, 0) + sayac;
}
```

Önce yalnızca `-Wall -Wextra` ile derleyelim. Komutu WSL içinde çalıştırıyoruz; bu bölümdeki C komutlarının hepsi aynı ortamda:

```term
$ gcc -std=c11 -O2 -Wall -Wextra -c uyari.c
uyari.c:8:23: warning: comparison of integer expressions
  of different signedness: 'int' and 'size_t' [-Wsign-compare]
uyari.c:31:21: warning: unsigned conversion from 'int' to
  'uint8_t' changes value from '300' to '44' [-Woverflow]
```

İki uyarı görünüyor. Şimdi katı bayrakları ekleyelim: `-Wshadow` iç içe tanımlanan aynı isimli değişkenleri, `-Wconversion` sessiz tip dönüşümlerini yakalar:

```term
$ gcc -std=c11 -O2 -Wall -Wextra -Wshadow \
    -Wconversion -c uyari.c
uyari.c:8:23: warning: comparison of integer expressions
  of different signedness: 'int' and 'size_t' [-Wsign-compare]
uyari.c:15:17: warning: conversion from 'double' to 'int'
  may change value [-Wfloat-conversion]
uyari.c:23:13: warning: declaration of 'sonuc' shadows
  a previous local [-Wshadow]
uyari.c:31:21: warning: unsigned conversion from 'int' to
  'uint8_t' changes value from '300' to '44' [-Woverflow]
```

Uyarı metinleri terminalde çok uzun olduğu için satır sonlarından bölündü; içerikleri değiştirilmedi.

Dört uyarının her biri bir hataya işaret eder. Şimdi programı çalıştırıp bu hataların sonucunu görelim:

```term
$ gcc -std=c11 -O0 -g -fsanitize=address,undefined \
    -w -o uyari_asan uyari.c && ./uyari_asan
1 0
25
```

Üç gözlem:

- `dogrula(3)` 6 döndürmesi gerekirken 0 döndürdü. İç bloktaki `int sonuc` dış `sonuc`'u gölgeledi; `return sonuc` dış değişkeni okudu. Bu, `-Wshadow` uyarısının tam olarak yakaladığı türden bir hatadır ve test edilmesi kolay değildir, çünkü çoğu zaman sonuç "makul görünür".
- `yuzde_yaz(0.256)` 26 değil 25 yazdırdı. `0.256 * 100` değeri 25.6'dır ve `int`'e atanırken kesildi (yuvarlanmadı). Bu bir sessiz kesmedir; `-Wfloat-conversion` bunu gösterir.
- `uint8_t sayac = 300;` değeri 44'e indi (300 mod 256). Derleyici bunu sabit değerde bildiği için uyardı; değer dışarıdan gelseydi uyarı çıkmayabilirdi.

Ayrıca `-Wsign-compare` uyarısının arkasında gerçek bir risk var. `int i` ile `size_t n` karşılaştırıldığında `i` işaretsiz tipe çevrilir. Bu bellek bloğu büyüdüğünde, `n` `INT_MAX`'ı aşarsa `i` de taşar; işaretli tamsayıda taşma tanımsız davranıştır (UB). Tanımsız davranış, tipik olarak "yanlış sonuç" ya da "çökme" ile sonuçlanabilir, ama bunu garanti etmez: derleyici optimizasyonda döngüyü beklenmedik biçimlerde yeniden yazabilir. Doğru çözüm `i`'yi de `size_t` yapmak ya da `n`'yi uygun bir tipte almaktır.

::: ipucu
Derleyici uyarılarını `-Werror` ile hataya çevirmek, ekip olarak uyarı toleransını sıfırlamanın en basit yoludur. Ama önce uyarıların neden çıktığını anla; yoksa `-Wno-...` ile susturmaya başlarsın ve asıl hatayı kaçırırsın.
:::

### clang-tidy: kalıp tanıyan ikinci göz

Derleyici uyarıları tip ve sözdizimi odaklıdır. clang-tidy daha çok kalıp ve okunabilirlik kurallarını uygular; ayrıca clang'in statik analizörünün bellek kontrollerini çalıştırabilir. Aynı `uyari.c` üzerinde yalnızca `bugprone` ve `readability` kontrol gruplarını çalıştırdık ve çıktıdan ilgili satırları aldık:

```term
$ clang-tidy uyari.c -checks='bugprone-*,readability-*' -- -std=c11
uyari.c:15:17: warning: narrowing conversion from 'double' to
  'int' [bugprone-narrowing-conversions]
uyari.c:31:21: warning: implicit conversion from 'int' to
  'uint8_t' changes value from 300 to 44
  [clang-diagnostic-constant-conversion]
uyari.c:15:24: warning: 100 is a magic number; consider
  replacing it with a named constant [readability-magic-numbers]
```

Sihirli sayı uyarısına Bölüm 23.7'de geri döneceğiz. Bellek sızıntısı için clang-tidy'nin analizör kontrolleri gerçekten işe yarar. Bölüm 23.6'daki `kayit_oku` örneğini `clang-analyzer-*` kontrolleriyle çalıştırdığımızda şu uyarıları aldık (yol kırpılmıştır):

```term
ex3_eski.c:14:17: warning: Opened stream never closed.
  Potential resource leak [clang-analyzer-unix.Stream]
ex3_eski.c:21:17: warning: Potential leak of memory pointed
  to by 'tampon' [clang-analyzer-unix.Malloc]
```

Windows'ta çalıştırdığımız için clang-tidy, MSVC'ye özgü `fopen_s` önerisi gibi CRT uyarıları da üretti. Taşınabilir kod yazıyorsan bu uyarıları bilinçli olarak yok sayabilirsin; ama bunların kaynağını bilmek, uyarıyı gerçek sorundan ayırmanı sağlar.

### Python: ruff ve mypy

Python'da aynı işi `ruff` (hızlı linter) ve `mypy` (tip denetleyicisi) yapar. Aşağıdaki dosya bilerek kötü yazıldı: kullanılmayan importlar, değiştirilebilir varsayılan argüman, çıplak `except`, Python'da olmayan adlandırma.

```python
import os
import sys


def getUser(id, list=[]):
    for u in list:
        if u["id"] == id:
            return u
    return None


def ort(xs):
    try:
        return sum(xs) / len(xs)
    except:
        pass


def is_ok(x):
    if x == None:
        return False
    return True
```

`ruff` kurallarını (E, F, B, N, SIM) seçip çalıştırdığımızda:

```term
$ ruff check --select E,F,B,N,SIM --output-format concise kotu_py.py
kotu_py.py:1:8: F401 `os` imported but unused
kotu_py.py:2:8: F401 `sys` imported but unused
kotu_py.py:5:5: N802 Function name `getUser` should be lowercase
kotu_py.py:5:22: B006 Do not use mutable data structures for argument defaults
kotu_py.py:15:5: E722 Do not use bare `except`
kotu_py.py:20:5: SIM103 Return the condition `x != None` directly
kotu_py.py:20:13: E711 Comparison to `None` should be `cond is None`
Found 7 errors.
```

Bu çıktıda en tehlikeli olan `E722`'dir: çıplak `except:` her hatayı, klavye kesmesini (Ctrl+C) bile yakalar ve `pass` ile sessizce yutar. Bölüm 23.6'da bunun neden kötü olduğunu ayrıntılı göreceğiz. `B006`'daki değiştirilebilir varsayılan (`list=[]`) ise aynı listenin tüm çağrılar arasında paylaşılmasına yol açar; bu bir yan etki kaynağıdır.

Tip denetimi ise çalıştırmadan bir hatayı yakalar. Aşağıdaki dosyada `kullanici_bul` bir kullanıcı bulamazsa `None` döndürebilir; `selam` fonksiyonu bunu unutmuş:

```python
from typing import Optional


def kullanici_bul(kimlik: int) -> Optional[str]:
    isimler = {1: "Ayse", 2: "Mert"}
    return isimler.get(kimlik)


def selam(kimlik: int) -> str:
    isim = kullanici_bul(kimlik)
    return "Merhaba " + isim.upper()


def selam_guvenli(kimlik: int) -> str:
    isim = kullanici_bul(kimlik)
    if isim is None:
        return "Merhaba misafir"
    return "Merhaba " + isim.upper()
```

`mypy --strict` bu dosyayı şöyle raporlar:

```term
$ mypy --strict tip_ornek.py
tip_ornek.py:11: error: Item "None" of "str | None" has no
  attribute "upper"  [union-attr]
Found 1 error in 1 file (checked 1 source file)
```

Hata `selam` içinde, `isim.upper()` satırındadır; `selam_guvenli` ise `None` durumunu açıkça ele aldığı için temizdir. Bu, çalışma zamanında `AttributeError` olarak ortaya çıkacak bir hatanın, daha kodu çalıştırmadan yakalanmasıdır. Birçok ekip bu denetimi derleme aşamasının bir parçası yapar. Aynı disiplin, Kısım XIV ve XV'teki büyük ML kod tabanlarında tensör ve veri şekilleri için de geçerli olacak.

## 23.6 Hata yönetimi: yutma, kaynağı unutma, bağlam ver

Hata yönetimi, kodun en çok ihmal edilen kısmıdır. Mutlu yol (happy path) genellikle düzgün yazılır; hatalı yol ise son dakikada, bir şey patladıktan sonra eklenir. Oysa gerçek sistemlerde hata yolu, kodun önemli bir kısmıdır: dosya bulunamaz, bellek biter, sensör veri göndermez, ağ kopar. Bu alt bölümde dört dile özgü kalıbı ele alıyoruz ve sonunda ortak bir kural çıkarıyoruz.

### C: dönüş kodları ve sözleşme

C'de istisna (exception) yoktur; hata, dönüş değeriyle bildirilir. Bunun en yaygın biçimi, başarıda 0 ve hatada negatif bir hata kodu döndürmektir. Bu, Bölüm 23.2'deki adlandırma kuralıyla birlikte düşünülmelidir: eylem adlı fonksiyon hata kodu, yüklem adlı fonksiyon boolean döndürür.

Dönüş değerini yok saymak en sık görülen hatadır. `fclose(f)` çağrısının sonucunu kontrol etmemek, yazma sırasındaki bir hatayı (disk doldu gibi) gizler. Bölüm 6'daki "erken patla" ilkesi burada da geçerlidir: hata, oluştuğu yerde bildirilmeli ya da çağırana iletilmelidir; sessizce yutulmamalıdır.

### C: goto ile tek çıkış noktası

Bir fonksiyon birden çok yerden çıkıyorsa ve bu çıkışların her biri farklı kaynakları serbest bırakması gerekiyorsa, her çıkış yolunda temizlik kodunu tekrarlamak hata üretir. Bir yolda `free` unutulur, bir başkasında iki kez çağrılır. Linux çekirdeğinin kodlama belgesi, birden çok çıkışı olan ve ortak temizlik gerektiren fonksiyonlarda `goto` kullanmanın işe yaradığını söyler: çıkışlar tek bir etikette toplanır, temizlik orada bir kez yazılır. Belge etiket adları için de bir kural koyar: etiket, `goto`'nun ne yaptığını söylemelidir.

![Şekil 23.3: goto ile merkezi çıkış. Hata yolları, açık kalan kaynakları ters sırada kapatan etiketlere atlar.](gorseller/b23_goto_cikis.png)

Şekil iki kuralı gösterir. Birincisi, etiketler adlarıyla yapılacak işi söyler (`cik_tampon`, `cik_dosya`); `err1`, `err2` gibi numaralı adlar, çıkış yolları değiştiğinde yeniden numaralandırmayı gerektirir ve doğruluğu kontrol etmeyi zorlaştırır. İkincisi, kaynaklar edinildikleri sırayla ters sırada serbest bırakılır: önce tampon (sonra alındı), sonra dosya (önce alındı). Tam kod ve doğrulama Örnek 3'te; buradaki iskelet yalnızca mantığı gösterir.

Belge ayrıca tipik bir hatayı da tarif eder: tek bir hata etiketinin, bazı çıkış yollarında henüz ayrılmamış bir işaretçiyi serbest bırakmaya çalıştığı durum. Çözüm, etiketi iki parçaya bölmektir; her etiket yalnızca o noktaya kadar gerçekten ayrılmış kaynakları serbest bırakır. Bu tam olarak Örnek 3'te yaptığımız şeydir.

### C++: RAII ile kaynağı nesneye bağlamak

C++'ta aynı sorunun çözümü `goto` değil, RAII (Resource Acquisition Is Initialization, kaynak edinimi başlatmadır) kalıbıdır. Kuralı şudur: kaynak bir nesnenin kurucusunda alınır, yıkıcısında serbest bırakılır. Kapsam (scope) bittiğinde, normal dönüşte de istisnada da yıkıcı çalışır. Standart kütüphanedeki `std::unique_ptr` bu kalıbın hazır bir uygulamasıdır:

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>

void kullan(bool hata) {
    auto veri = std::make_unique<double[]>(10);
    veri[0] = 1.0;
    if (hata) throw std::runtime_error("bozuk girdi");
    std::printf("tamam\n");
}

int main() {
    try {
        kullan(false);
        kullan(true);
    } catch (const std::exception& e) {
        std::printf("yakalandi: %s\n", e.what());
    }
    return 0;
}
```

`kullan(true)` çağrısında fonksiyon istisna fırlatır, ama `veri` dizisi yığından çıkarken serbest kalır. Programı ASan ve LeakSanitizer ile çalıştırdığımızda hiçbir sızıntı raporu çıkmadı:

```term
$ g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined \
    -o raii raii.cpp && ./raii
tamam
yakalandi: bozuk girdi
```

C'deki `goto cleanup` ile C++'taki RAII aynı sorunu çözer; fark, doğruluğu nerede garantilediğindir. `goto`'da doğruluk, programcının her yolu elle doğru sıraya koymasına dayanır. RAII'de doğruluk, derleyicinin kapsam sonunda yıkıcıyı çağırmasına dayanır. Bu yüzden C++ kodunda ham `new`/`delete` ya da `malloc`/`free` yazmak, bugün çoğu ekipte bir kod kokusu sayılır.

### Python: istisnalar ve bağlam

Python'da hatalar istisnadır ve kodun akışını doğal olarak keser. Asıl risk, istisnayı yakalayıp anlamını kaybettirmektir. Yukarıdaki `ruff` çıktısındaki `E722` ve `pass` kalıbı bunun en kötü biçimidir. Doğru yaklaşım üç şeydir: yalnızca beklediğin istisnayı yakala, istisnayı anlamlı bir yeni istisnaya çevirirken nedenini koru, ve mesajda bağlamı (hangi kimlik, hangi dosya) yaz.

```python
def kullanici_bul(kimlik):
    if kimlik != 1:
        raise KeyError(kimlik)
    return "Ayse"


def ad_getir(kimlik):
    try:
        return kullanici_bul(kimlik).upper()
    except KeyError as hata:
        raise ValueError("kimlik %d yok" % kimlik) from hata


print(ad_getir(1))
try:
    ad_getir(7)
except ValueError as e:
    print("hata:", e, "| neden:", repr(e.__cause__))
```

Çıktı:

```term
$ python ustu.py
AYSE
hata: kimlik 7 yok | neden: KeyError(7)
```

`raise ... from hata` ifadesi, orijinal `KeyError`'ı `__cause__` olarak saklar. Üst katmanda hata ayıklarken iki bilgi birlikte görünür: "kimlik 7 yok" (ne olduğu) ve `KeyError(7)` (nereden geldiği). `from` olmadan yeni bir istisna fırlatsaydın, zincirin ilk halkası kaybolurdu.

### Ortak kural: hatayı yutma, bağlamla bildir

Dört dilde de aynı iki kural geçerlidir. Birincisi: **hatayı yutma.** Dönüş kodunu yok saymak, `except: pass` yazmak, boş bir `catch` bloğu bırakmak, hatanın yerini gizler ve yanlış durumda programın devam etmesine yol açar. İkincisi: **hatayı bağlamla bildir.** "Hata oluştu" mesajı işe yaramaz; "kayit.bin açılamadı (errno 2: No such file or directory)" ya da "kimlik 7 yok" gibi mesajlar, hatanın nerede ve neden olduğunu söyler. C'de `strerror(errno)`, Python'da `repr` ve `__cause__` bu bağlamı taşımanın araçlarıdır.

::: dikkat
Bölüm 6'da `assert`'ü programcı hatası için, dönüş kodunu ya da istisnayı dış dünyadaki beklenen hatalar için kullanmayı öğrendik. Burada aynı ayrım yeniden önemli: bir dosyanın olmaması beklenen bir durumdur ve normal hata yolundan geçer; bir indeksin negatif olmaması ise bir programcı varsayımıdır ve `assert` ile yakalanır.
:::
