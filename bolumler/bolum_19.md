%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 19
%% baslik: Divide & Conquer

## Giriş: Problemi ikiye bölüp kazanmak

Bölüm 13'te birleştirme sıralamasını (merge sort) gördüğünde bir şeyi fark etmiş olabilirsin: dizi ikiye bölünüyor, her yarı ayrı ayrı sıralanıyor, sonra iki sıralı yarı tek bir sıralı diziye birleştiriliyor. Bu düşünce biçimi bir sıralama hilesi değil. Büyük bir problemi aynı türden daha küçük problemlere bölüp, küçük sonuçlardan büyük sonucu kurma stratejisidir. Adı **böl ve fethet** (divide and conquer, D&C) olarak bilinir ve Kısım IV'ün son bölümünde bu stratejiyi sistematik olarak inceliyoruz.

Bölüm 16'da dinamik programlamayı (DP) gördük. Orada aynı alt problemler tekrar tekrar çözülüyordu ve tabloda saklamak yeterliydi. Bu bölümde ise alt problemler genellikle birbirinden bağımsızdır; hiçbiri diğerinin sonucunu kullanmaz. Bu fark, hangi tekniğin seçileceğini belirler. Bölüm 19.3'te bu karar için bir tablo vereceğiz.

D&C'nin mülakattaki yeri çok büyük. "Bir diziyi iki parçaya ayır, her parçada ne yapacağını düşün, sonra birleştir" cümlesi birçok sorunun ilk fikridir: en yakın nokta çifti, maksimum alt dizi, çoğunluk elemanı, polinom çarpımı. Adayın bu soruda sorulan şeyi görmesi kadar, birleştirme adımının maliyetini doğru hesaplaması da değerlendirilir.

Savunma sanayiinde de bu fikir yaygındır. Radar ve sinyal işlemede hızlı Fourier dönüşümü (FFT) polinom çarpımını ve konvolüsyonu O(n log n) zamanda yapar; bunun temelinde D&C vardır. Bölüm 52'de DSP tarafında bu bağlantıyı tekrar kuracağız. Bir İHA'nın görüntüsünde en yakın iki hedefi bulmak, bir harita üzerinde yakın nokta sorgularını hızlandırmak, büyük sayısal hesaplarda matris çarpımını hızlandırmak da aynı kalıba oturur.

Mert'in projelerine de doğal bir bağlantı var. EV Dashboard'daki sensör kayıtları üzerinde bir kayan ortalama filtresi yazarsan, bu bir konvolüsyondur ve uzun kayıtlarda FFT ile hızlanır. Bu bölümün Kendin Yap bölümünde bunu yapacaksın.

::: not
Bu bölümdeki tüm programlar Python 3.12.10 ile çalıştırıldı; sayılar `random.Random(42)` tohumu ile üretildi, bu yüzden aynı kodu çalıştırdığında rastgele girdiler aynı olur. Süre ölçümleri makineye bağlıdır; kitaptaki sayıları kendi bilgisayarında tekrar üretebilirsin, ama değerler farklı çıkacaktır. C programları WSL'de gcc 13.3 ile `-std=c11 -Wall -Wextra` uyarıları açık olarak derlendi ve `-fsanitize=address,undefined` ile de çalıştırıldı. Windows'ta `long` 4 bayttır (LLP64); bu yüzden C kodunda boyutları `size_t` ve `double` ile açıkça seçtik.
:::

## 19.1 Böl, çöz, birleştir: şablon

Her D&C algoritması aynı üç adımdan oluşur. Önce **böl** (divide): problemi daha küçük, aynı türden alt problemlere ayır. Sonra **çöz** (conquer): alt problemleri özyineleme ile çöz. Son olarak **birleştir** (combine): alt problemlerin sonuçlarını, büyük problemin sonucuna dönüştür. Taban durumda, yani problem yeterince küçükken, sonucu doğrudan hesaplarız.

Bunu günlük bir örnekle düşünelim. Bir kutu dolusu karışık kartı sıralamak istiyorsun. Kartları iki yığına bölersin, her yığını kendi başına sıralarsın ve sonra iki sıralı yığını tek bir sıralı dizide birleştirirsin. Birleştirme adımı, iki yığının en üstündeki kartları karşılaştırıp küçük olanı alarak yapılır. Maliyetin bir kısmı bölme sırasında, büyük kısmı ise birleştirmede ortaya çıkar. Bölüm 19.2'de bu gözlemi sayılarla göreceğiz.

Bölüm 13'teki iki sıralama zaten D&C'dir. Birleştirme sıralaması (Bölüm 13.4), dizi ortadan ikiye bölünür, iki yarı sıralanır ve birleştirilir. Hızlı sıralama (Bölüm 13.5) ise tersini yapar: bölme adımı ağır, birleştirme adımı yoktur; pivotun etrafında parçalama (partition) yapılır, sonra iki yarı sıralanır ve birleştirme gerekmez. Quickselect de bu ailedendir: tek bir yarıya inerek k. elemanı bulur. İkili arama (Bölüm 14.2) ise D&C'nin dejenere halidir: her adımda yalnızca bir alt problem vardır ve birleştirme yapılmaz.

![Şekil 19.1: Böl, çöz, birleştir şablonu. Maliyet, yukarı giden oklardaki birleştirme adımında biriken işin toplamıdır.](gorseller/b19_dc_sablon.png)

Şablonu bir iskelet olarak yazabiliriz. Aşağıdaki gövde, herhangi bir D&C çözümünün dış hatlarıdır; gerçek problemde `bol`, `birlestir` ve taban durum farklı olur. Bu iskeletin amacı, kodu yazmadan önce üç soruyu cevaplamanı sağlamaktır: taban durum ne, bölme nasıl, birleştirme ne kadar pahalı.

```python
def coz(problem):
    if taban_durum_mu(problem):       # temel: cevap bilinir
        return taban_cevap(problem)
    sol, sag = bol(problem)           # iki (ya da k) alt problem
    s1 = coz(sol)                     # ozyineleme
    s2 = coz(sag)
    return birlestir(s1, s2)          # maliyet burada
```

Bu iskelette `coz` her seviyede iki kez kendini çağırır. Çağrı sayısı ve her çağrının kendi işi birlikte toplam maliyeti verir. Bölüm 19.2'de bu toplamı özyineleme ağacı ile hesaplayacağız.

## 19.2 Maliyet birleştirmede saklanır: özyineleme ağacı ve Master Teoremi

D&C algoritmasının genel bağıntısı şöyle yazılır: `T(n) = a·T(n/b) + f(n)`. Burada `n` problem boyutudur, `a` her adımda kaç alt problem çağrıldığı, `b` her alt problemin boyutunun kaç katı küçüldüğü, `f(n)` ise bölme ve birleştirme için harcanan iştir. Bölüm 12.9'da bu bağıntıyı yerine koyma, özyineleme ağacı ve Master Teoremi ile çözmeyi gördük. Burada yeniden türetmek yerine uygulayacağız.

Birleştirme sıralamasında `a = 2`, `b = 2`, `f(n) = Θ(n)`'dir. Özyineleme ağacının her seviyesinde toplam iş `n` kadardır ve seviye sayısı `log₂ n`'dir. Toplam `Θ(n log n)`'dir. Bu, maliyetin her seviyeye eşit dağıldığı bir durumdur. Ama birleştirme adımı daha ağırsa, örneğin `f(n) = n log n` ise seviyeler arasındaki iş değişir ve sonuç da değişir. Aşağıdaki şekil, `n = 16` için bu ağacı gösteriyor. Bağıntı `T(n) = 2T(n/2) + n log₂ n`, taban `T(1) = 0`.

![Şekil 19.2: T(n) = 2T(n/2) + n log n için özyineleme ağacı (n = 16). Her seviyenin toplamı n(log n - i) ile azalır; toplam T(16) = 160.](gorseller/b19_ozyineleme_agaci.png)

Şekildeki sayılar bağıntıdan elle çıkar: seviye `i`'de `2^i` düğüm vardır, her düğüm `n/2^i` boyutludur ve `(n/2^i) log₂(n/2^i)` iş yapar. Bir seviyenin toplamı `n(log n - i)`'dir. Bu toplamları `i = 0`'dan `log n - 1`'e kadar topladığımızda `n(log n)(log n + 1)/2` elde ederiz. Bu ifade `Θ(n log² n)`'dir. Bu sonucu bir programla da doğrulayalım. Aşağıdaki kod bağıntıyı doğrudan özyinelemeli hesaplar ve `T(n) / (n log² n)` oranına bakar.

Bu kodu çalıştırmadan önce şunu bil: `lru_cache` her `n` için sonucu saklar, böylece aynı çağrı tekrar hesaplanmaz. Bu, Bölüm 16'daki memoization'ın küçük bir uygulamasıdır.

```python
# rec_tree.py: T(n) = 2T(n/2) + n log2 n icin olcek kontrolu
import math
from functools import lru_cache


@lru_cache(maxsize=None)
def T(n):
    if n <= 1:
        return 0.0
    return 2 * T(n // 2) + n * math.log2(n)


if __name__ == "__main__":
    print("   k      n        T(n)    T(n)/(n log^2 n)")
    for k in (4, 8, 12, 16, 20):
        n = 2 ** k
        print("%3d %7d %12.0f %12.4f"
              % (k, n, T(n), T(n) / (n * math.log2(n) ** 2)))
```

Programı çalıştırdığında oranın 0,5'e yaklaştığını göreceksin:

```term
$ python rec_tree.py
   k      n        T(n)    T(n)/(n log^2 n)
  4      16          160       0.6250
  8     256         9216       0.5625
 12    4096       319488       0.5417
 16   65536      8912896       0.5312
 20 1048576    220200960       0.5250
```

Oran 0,5'e doğru düşüyor; bu, `T(n) ≈ (1/2) n log² n` anlamına gelir. Tablo bir ispat değildir, ama analitik sonuçla birebir uyumludur ve tahminini doğrulamanın en hızlı yoludur. Bu teknik sana Bölüm 12.10'daki log-log eğimi yöntemini de hatırlatmalı.

**Master Teoremi uygulaması.** Bölüm 12.9'daki üç durumu hatırla. `log_b a` ile `f(n)`'nin büyüklüğünü karşılaştırırsın: `f(n)` daha yavaş büyüyorsa toplam `Θ(n^(log_b a))`, eşitse `Θ(n^(log_b a) log n)`, `f(n)` daha hızlı büyüyorsa (ve düzenlilik koşulu sağlanırsa) toplam `Θ(f(n))`. Bu bölümdeki algoritmaların hepsini tabloya döküyoruz.

| Algoritma | Bağıntı | log_b a | f(n) | Durum | Sonuç |
|---|---|---|---|---|---|
| İkili arama | T(n/2) + Θ(1) | 0 | Θ(1) | 2 | Θ(log n) |
| Hızlı üs | T(n/2) + Θ(1) | 0 | Θ(1) | 2 | Θ(log n) |
| Birleştirme sıralaması | 2T(n/2) + Θ(n) | 1 | Θ(n) | 2 | Θ(n log n) |
| Karatsuba | 3T(n/2) + Θ(n) | log₂3 ≈ 1,585 | Θ(n) | 1 | Θ(n^1,585) |
| Strassen | 7T(n/2) + Θ(n²) | log₂7 ≈ 2,807 | Θ(n²) | 1 | Θ(n^2,807) |
| En yakın çift | 2T(n/2) + Θ(n) | 1 | Θ(n) | 2 | Θ(n log n) |
| Maksimum alt dizi (D&C) | 2T(n/2) + Θ(n) | 1 | Θ(n) | 2 | Θ(n log n) |
| Skyline | 2T(n/2) + Θ(n) | 1 | Θ(n) | 2 | Θ(n log n) |
| FFT | 2T(n/2) + Θ(n) | 1 | Θ(n) | 2 | Θ(n log n) |

Tablodaki "Durum" sütunu Bölüm 12.9'daki durum numarasını gösterir. Strassen ve Karatsuba'da `f(n)` iki durumdan birine düşer; durum 1 koşulunu (ε > 0 için `f(n) = O(n^(log_b a - ε))`) kontrol etmek için ε'yi seçmelisin. Karatsuba'da `f(n) = n = O(n^(1,585 - 0,5))` diyebileceğimiz için ε = 0,5 alınır; Strassen'de `f(n) = n² = O(n^(2,807 - 0,5))` yazılır.

Master Teoremi her bağıntıya uymaz. Şimdi bunu bir örnekte görelim. `T(n) = 2T(n/2) + n log n` bağıntısında `log_b a = 1`, `f(n) = n log n`'dir. `f(n)` her yönden `n`'den büyüktür ama polinom olarak büyümez: `n log n` ile `n^(1+ε)` arasındaki oran `log n / n^ε` ile sıfıra gider, bu yüzden ne durum 2 ne de durum 3'e girer. Bu durumda özyineleme ağacı yapılır: yukarıda hesapladığımız `Θ(n log² n)` sonucu bulunur. Bu, Master'ın uygulanamadığı durumda ağacın neden hâlâ işe yaradığını gösteren klasik bir örnektir.

Medyanların medyanı algoritması (Bölüm 19.9) da Master'a uymaz, çünkü iki farklı alt problem boyutu vardır: `n/5` ve `7n/10`. Orada yerine koyma yöntemi kullanacağız.

## 19.3 D&C mi, DP mi, greedy mi? Karar tablosu

Bir problemi gördüğünde hangi tekniği seçeceğini kısa bir soruyla belirleyebilirsin: alt problemler birbirinden bağımsız mı, tekrar eden mi, yoksa yerel bir seçim ile global çözüm ilerleyebilir mi? Bu üç ayrım, sırasıyla D&C, DP ve greedy'nin ana koşullarıdır.

| Soru | Evet ise | Örnek |
|---|---|---|
| Alt problemler birbirinden bağımsız mı? | D&C | Birleştirme sıralaması, en yakın çift |
| Alt problemler tekrar ediyor mu? | DP (Bölüm 16) | Fibonacci, matris zinciri, LCS |
| Her adımda yerel en iyi seçim global optimumu veriyor mu? | Greedy (Bölüm 18) | Aktivite seçimi, Huffman |

Bu ayrımın neden önemli olduğunu bir örnekle görelim. Fibonacci'yi D&C ile hesaplamaya çalışırsan, `fib(n) = fib(n-1) + fib(n-2)` ağacında `fib(n-2)` iki kez hesaplanır. Bu, alt problemlerin bağımsız olmadığını gösterir ve D&C burada kötü seçimdir; bunun için tabloya dönüşüm (Bölüm 16.3) gerekir. Öte yandan Bölüm 19.4'te göreceğimiz matris üssü yaklaşımı, Fibonacci'yi D&C ile çözer; çünkü `M^n` hesabında kare alma adımları birbirinden bağımsızdır ve her yarı yalnızca bir kez kullanılır.

Matris zinciri çarpımı (Bölüm 16.9) DP'nin tipik bir örneğidir: `[i..j]` aralığının en iyi parantezlemesi, `[i..k]` ve `[k+1..j]` aralıklarının en iyilerinden kurulur, ama bu aralıklar birçok farklı `(i, j)` çiftinde tekrar kullanılır. Bu yüzden D&C ile yazılırsa aynı aralık tekrar tekrar hesaplanır. Bölüm 16.9'daki sonda bu bağlantıya değinmiştik; şimdi nedenini biliyorsun.

Greedy (Bölüm 18) ise her adımda yerel olarak en iyi seçimi yapar ve geri dönmez. Greedy'nin doğru çalışması için bir ispat gerekir; bu ispat çoğu zaman bir değiş tokuş (exchange) argümanıdır. Bu bölümde greedy'ye girmiyoruz, ama D&C ile karıştırılmaması için tabloda yer verdik.

Bu tabloyu bir sınav sorusunda kullanmanın yolu şudur: problem "bölünebilir mi?" diye sorulduğunda, alt problemlerin tekrarlanıp tekrarlanmadığını kontrol et. Tekrar varsa DP, yoksa D&C düşün, sonra her iki durumda da birleştirme maliyetini hesapla.

## 19.4 Hızlı üs ve matris üssüyle Fibonacci

`x^n`'i hesaplamak için en basit yöntem `n` kez çarpmaktır; bu `Θ(n)` çarpım gerektirir. Ama bir tamsayı üssünü ikili gösterimine göre hızlı hesaplayabiliriz: `x^n = (x^(n/2))²` (n çiftse), `x^n = x · (x^((n-1)/2))²` (n tekse). Her adımda üs yarıya iner. Bu, `T(n) = T(n/2) + Θ(1)` bağıntısıdır ve Master durum 2 ile `Θ(log n)` verir.

Bu fikir büyük sayılarda ve modüler aritmetikte çok önemlidir. Kriptografide (RSA gibi) `x^n mod m` hesapları binlerce bit uzunluğunda sayılarla yapılır; bu yüzden hızlı üs alma bir zorunluluktur. Aşağıdaki fonksiyon, D&C yapısını açıkça gösterir: her çağrı yalnızca tek bir alt çağrı yapar, bu yüzden ağaç bir zincirdir.

Şekil 19.3, `x^13` hesabını gösteriyor. 13'ün ikili gösterimi `1101`'dir: her adımda `n//2` alınır, son bit (tek/çift) hangi ek çarpımın yapılacağını belirler.

![Şekil 19.3: x^13 hesabının zinciri. Her adım üssü yarıya indirir; tek üslerde bir ek x çarpımı yapılır.](gorseller/b19_hizli_us.png)

Matris üssüyle Fibonacci hesabı, aynı fikri bir matrise uygular. Şu eşitlik vardır:

`[[1, 1], [1, 0]]^n = [[F(n+1), F(n)], [F(n), F(n-1)]]`

Bu matrisi `n` üssüne yükseltmek için 2×2 matris çarpımını kullanırız; her çarpım sabit sayıda aritmetik işlem gerektirir. Bu nedenle `O(log n)` çarpım yapılır. Burada `n` bir üstteki boyuttur ve `F(n)` sayıları `O(n)` bit uzunluğundadır; ama modulo `m` ile çalıştığımız için sayılar hep sabit boyutta kalır ve maliyet analizi temiz kalır. Bölüm 15'te `fib(30)` gibi değerler için üstel ağacı görmüştük; burada `fib(10^18)`'i hesaplamak mümkündür.

Fast doubling adı verilen ikinci yöntem, aynı sonucu iki sayı üzerinde yürütür: `F(2k) = F(k)·(2F(k+1) - F(k))` ve `F(2k+1) = F(k)² + F(k+1)²`. İki yöntem birbirinden bağımsız olduğu için sonuçlarını karşılaştırmak iyi bir doğrulamadır. Aşağıdaki programın üç bölümü vardır: üs alma, iki Fibonacci yöntemi ve doğrulama.

```python
# fastpow.py: hizli us, matris ustu ve fast doubling ile Fibonacci
import random

CAGRI = 0


def us_ozyineli(x, n, m):
    """x^n mod m. Her cagri tek bir alt cagri yapar."""
    global CAGRI
    CAGRI += 1
    if n == 0:
        return 1 % m
    yarim = us_ozyineli(x, n // 2, m)     # T(n/2)
    sonuc = yarim * yarim % m             # O(1) birlestirme
    if n % 2 == 1:
        sonuc = sonuc * x % m             # tek us: bir ek carpim
    return sonuc


def mat_carp(A, B, m):
    """2x2 matrislerin carpimi, her eleman mod m."""
    return [[(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % m,
             (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % m],
            [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % m,
             (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % m]]


def fib_matris(n, m):
    """[[1,1],[1,0]]^n = [[F(n+1), F(n)], [F(n), F(n-1)]]."""
    sonuc = [[1, 0], [0, 1]]              # birim matris
    taban = [[1, 1], [1, 0]]
    while n > 0:
        if n & 1:
            sonuc = mat_carp(sonuc, taban, m)
        taban = mat_carp(taban, taban, m)
        n >>= 1
    return sonuc[0][1]                    # F(n)
```

Bu ilk parçada `us_ozyineli` yalnızca bir çağrı yapar; bu yüzden ağacı bir zincirdir. `fib_matris` ise iteratiftir: ikili üs döngüsünü açıkça yazar. İki yaklaşımın aynı sonucu verdiğini programın ilerleyen bölümünde kontrol edeceğiz.

Aşağıdaki ikinci parça, fast doubling ve doğrulama referansını ekler.

```python
def fib_cift(n, m):
    """Fast doubling: (F(n), F(n+1)) dondurur."""
    if n == 0:
        return 0, 1
    a, b = fib_cift(n // 2, m)            # a = F(k), b = F(k+1)
    c = a * (2 * b - a) % m               # F(2k)
    d = (a * a + b * b) % m               # F(2k+1)
    if n % 2 == 0:
        return c, d
    return d, (c + d) % m                 # F(2k+2) = F(2k) + F(2k+1)


def iteratif(n):
    """Tam sayi Fibonacci; kucuk n icin dogrulama referansi."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

Doğrulama bölümünde iki şeyi kontrol ediyoruz. Birincisi, küçük `n` için (0 ile 300 arası) mod'u çok büyük bir sayı yaparak modüler aritmetiği devre dışı bırakıp tam sayı sonucunu karşılaştırmak. İkincisi, rastgele `n` ve `m` için mod sonucunu iteratif yöntemle karşılaştırmak. Üçüncüsü, `us_ozyineli`'yi yerleşik `pow(x, n, m)` ile karşılaştırmak.

```python
if __name__ == "__main__":
    rnd = random.Random(42)
    BIG = 10 ** 400                       # mod'u tam sayi gibi kullan
    for n in range(0, 301):
        assert fib_matris(n, BIG) == iteratif(n)
        assert fib_cift(n, BIG)[0] == iteratif(n)
    print("n = 0..300: matris ve fast doubling tam sayi ile esit")
    for _ in range(300):
        n = rnd.randint(1, 10 ** 4)
        m = rnd.randint(2, 10 ** 9)
        ref = iteratif(n) % m
        assert fib_matris(n, m) == ref
        assert fib_cift(n, m)[0] == ref
    print("300 rastgele (n <= 10^4, m <= 10^9): mod sonucu esit")
    for _ in range(200):
        x = rnd.randint(2, 10 ** 9)
        n = rnd.randint(0, 10 ** 18)
        m = 10 ** 9 + 7
        assert us_ozyineli(x, n, m) == pow(x, n, m)
    print("200 rastgele us: us_ozyineli == pow(x, n, m)")
    m = 10 ** 9 + 7
    CAGRI = 0
    print("us_ozyineli cagri sayisi (n = 10^18):", end=" ")
    us_ozyineli(2, 10 ** 18, m)
    print(CAGRI)
    f1 = fib_matris(10 ** 18, m)
    f2 = fib_cift(10 ** 18, m)[0]
    print("F(10^18) mod (10^9+7), matris :", f1)
    print("F(10^18) mod (10^9+7), cift   :", f2)
    assert f1 == f2
```

Programı çalıştırdığında şu çıktıyı alırsın:

```term
$ python fastpow.py
n = 0..300: matris ve fast doubling tam sayi ile esit
300 rastgele (n <= 10^4, m <= 10^9): mod sonucu esit
200 rastgele us: us_ozyineli == pow(x, n, m)
us_ozyineli cagri sayisi (n = 10^18): 61
F(10^18) mod (10^9+7), matris : 209783453
F(10^18) mod (10^9+7), cift   : 209783453
```

Çıktıdaki `us_ozyineli` çağrı sayısı 61'dir. `10^18` yaklaşık `2^59,8` olduğu için ikili gösterimi 60 bit tutar; her bit için bir çağrı ve taban için bir çağrı yapılır. Bu, `log₂ n`'in sabit bir katıdır. Fibonacci sonucu ise `10^18`'den çok büyük bir sayı olan `F(10^18)`'in modulo `10^9 + 7` kalanıdır. İki yöntem aynı değeri verdi; bu, bağımsız iki hesabın birbiriyle uyumlu olduğunu gösterir, ama değerin doğru olduğunu tek başına kanıtlamaz. Bunun için Python'un büyük tamsayılarıyla `n ≤ 300` için tam kontrolü yaptık ve rastgele `n ≤ 10^4` kümesinde iteratif referansla karşılaştırdık.


## 19.5 Karatsuba çarpımı

İki `n` basamaklı sayıyı okul yönteminde çarpmak için her basamak çiftini çarpıp sonuçları kaydırarak toplarsın. Bu `n²` basamak çarpımı yapar; 1000 basamaklı iki sayı için bir milyona yakın çarpma demektir. Python'da büyük tamsayılarla çalışmış olabilirsin ve `x * y` çok hızlı görünür. Bu hız, CPython'un içinde Karatsuba algoritmasının kullanılmasından gelir. Bu bölümde onu kendi elimizle yazacağız ve kaynağına bakacağız.

Karatsuba algoritması (1960'ların başında Anatolii Karatsuba bulmuştur; genel bilgi) şu fikirle çalışır. Her sayıyı ortadan ikiye böl: `a = a1·B + a0`, `b = b1·B + b0`, burada `B = 10^m` (ya da bilgisayar için 2^k). Okul yönteminde `a·b = a1b1·B² + (a1b0 + a0b1)·B + a0b0` olur ve dört çarpım gerekir. Karatsuba'nın gözlemi şudur: orta terim için iki çarpım yerine tek bir çarpım yeter:

`z1 = (a0 + a1)(b0 + b1) - z0 - z2`, burada `z0 = a0b0`, `z2 = a1b1`.

Açılımı kontrol edelim: `(a0 + a1)(b0 + b1) = a0b0 + a0b1 + a1b0 + a1b1`. Buradan `z0` ve `z2`'yi çıkarırsak tam olarak `a0b1 + a1b0` kalır. Böylece çarpım sayısı dörtten üçe düşer. Bu, bir çarpımda tasarruf gibi görünebilir, ama özyineleme ile birleşince büyük fark yaratır.

![Şekil 19.4: Okul yöntemi dört, Karatsuba üç alt çarpım yapar. Üçüncü çarpımdan iki çarpım çıkarılarak orta terim elde edilir.](gorseller/b19_karatsuba.png)

Bağıntı şöyle yazılır: `T(n) = 3T(n/2) + Θ(n)`. Buradaki `Θ(n)` ayırma, toplama ve çıkarma işlerinin maliyetidir. Master Teoremi'nde `a = 3`, `b = 2`, `log₂ 3 ≈ 1,585` ve `f(n) = n = O(n^(1,585 - 0,5))` olduğu için durum 1 geçerlidir. Sonuç `Θ(n^1,585)` olur. Okul yönteminin `n²` ile karşılaştırıldığında, büyük `n` için kazanç bir sabit değil, bir üs farkıdır.

Pratikte bu algoritma küçük sayılarda yavaştır, çünkü özyineleme ve geçici sayı ayırmanın ek yükü vardır. Bu yüzden her gerçek gerçeklemede bir **eşik** (threshold) bulunur: sayı yeterince küçükse okul yöntemine dönülür. Aşağıdaki kodda bu eşik `ESIK = 32` basamaktır. Kodu üç ayrı bölümde okuyacağız: sayı işlemleri, okul yöntemi ve Karatsuba'nın kendisi.

Programda sayılar, her basamağı `TABAN = 10^4` olan bir liste olarak tutulur (en düşük basamak önde). Bu, Python'un kendi tamsayılarından bağımsız bir gerçeklemedir; böylece okul yöntemini ve Karatsuba'yı yerleşik `*` ile karıştırmadan ölçebiliriz.

```python
# karatsuba.py: okul yontemi ve Karatsuba (sayilar 10^4 tabanli)
import random
import sys
import time

TABAN = 10 ** 4
ESIK = 32                 # bu uzunlukun altinda okul yontemi


def normal(a):
    """Sondaki sifir basamaklari at; en az bir basamak kalir."""
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def topla(a, b):
    c, elde = [], 0
    for i in range(max(len(a), len(b))):
        s = elde
        if i < len(a):
            s += a[i]
        if i < len(b):
            s += b[i]
        c.append(s % TABAN)
        elde = s // TABAN
    if elde:
        c.append(elde)
    return normal(c)


def cikar(a, b):
    """a - b, a >= b varsayilir."""
    c, borc = [], 0
    for i in range(len(a)):
        s = a[i] - borc - (b[i] if i < len(b) else 0)
        borc = 1 if s < 0 else 0
        c.append(s + borc * TABAN)
    return normal(c)


```

Eşik ve dönüş ilişkisine dikkat et: `karatsuba` kendi içinde `okul`'u çağırır, `okul` ise hiçbir özyineleme yapmaz. Aşağıdaki parçada iki yöntemi ve `bol` yardımcısını görüyoruz.

```python
def kaydir(a, k):
    """a * TABAN^k (sola k basamak ekle)."""
    return [0] * k + a


def okul(a, b):
    """O(n*m) okul yontemi: her basamak ciftini carp, topla."""
    c = [0] * (len(a) + len(b))
    for i, x in enumerate(a):
        elde = 0
        for j, y in enumerate(b):
            t = c[i + j] + x * y + elde
            c[i + j] = t % TABAN
            elde = t // TABAN
        c[i + len(b)] += elde
    return normal(c)


def bol(a, m):
    """a = high * TABAN^m + low; iki parcayi dondurur."""
    low = normal(a[:m]) or [0]
    high = normal(a[m:]) or [0]
    return low, high


def karatsuba(a, b):
    if min(len(a), len(b)) <= ESIK:
        return okul(a, b)
    m = max(len(a), len(b)) // 2
    a0, a1 = bol(a, m)
    b0, b1 = bol(b, m)
    z0 = karatsuba(a0, b0)                       # a0 * b0
    z2 = karatsuba(a1, b1)                       # a1 * b1
    z1 = karatsuba(topla(a0, a1), topla(b0, b1))  # (a0+a1)(b0+b1)
    z1 = cikar(cikar(z1, z0), z2)                # a0*b1 + a1*b0
    sonuc = topla(z0, kaydir(z1, m))
    return topla(sonuc, kaydir(z2, 2 * m))


```

Karatsuba fonksiyonunun kalbi `z1` satırındadır. Üç özyinelemeli çağrı yapılır: `z0`, `z2` ve `(a0+a1)(b0+b1)`. Sonuçlar `kaydir` ile doğru basamak konumuna taşınır ve toplanır. Burada `cikar` negatif olmayan bir sonuç üretir, çünkü `z1`'in gerçek değeri `a0b1 + a1b0 ≥ 0`'dır.

```python
def deger(a):
    return sum(d * TABAN ** i for i, d in enumerate(a))


def digitler(n):
    d = []
    while n:
        d.append(n % TABAN)
        n //= TABAN
    return d or [0]


```

```python
if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(400):
        a = [rnd.randrange(TABAN) for _ in range(rnd.randint(1, 300))]
        b = [rnd.randrange(TABAN) for _ in range(rnd.randint(1, 300))]
        ref = digitler(deger(a) * deger(b))
        assert okul(a, b) == ref
        assert karatsuba(a, b) == ref
    print("400 rastgele cift: okul == karatsuba == tam sayi carpimi")
    print("TABAN =", TABAN, "| bit/basamak (CPython):",
          sys.int_info.bits_per_digit)
    print("\nlimb  ondalik  okul(s)  karats(s)  yerlesik(s)")
    rows = []
    for L in (128, 256, 512, 1024, 2048):
        a = [rnd.randrange(TABAN) for _ in range(L)]
        b = [rnd.randrange(TABAN) for _ in range(L)]
        t0 = time.perf_counter()
        okul(a, b)
        t1 = time.perf_counter()
        karatsuba(a, b)
        t2 = time.perf_counter()
        x, y = deger(a), deger(b)
        t3 = time.perf_counter()
        x * y
        t4 = time.perf_counter()
        r = (L, 4 * L, t1 - t0, t2 - t1, t4 - t3)
        rows.append(r)
        print("%4d  %7d  %7.3f  %9.3f  %11.6f" % r)
    csv_ad = "karatsuba_olcum.csv"
    if len(sys.argv) > 1:
        csv_ad = sys.argv[1]
    with open(csv_ad, "w", encoding="utf-8") as f:
        f.write("limb,ondalik,okul,karatsuba,yerlesik\n")
```

Doğrulama, üç yöntemin de aynı sonucu verdiğini kontrol eder. Rastgele uzunluklu 400 çifti, yerleşik tamsayı çarpımının (CPython'un kendi işleyişi) sonucuyla karşılaştırıyoruz. Tablo, sayı uzunluğu iki katına çıktığında her iki yöntemin süresini ölçer. Yerleşik çarpım için ayrıca `int_info` ile sayının bit/basamak değerini yazdırıyoruz; bu, CPython'un iç temsilinin 30 bitlik basamaklar kullandığını gösterir.

```term
$ python karatsuba.py
400 rastgele cift: okul == karatsuba == tam sayi carpimi
TABAN = 10000 | bit/basamak (CPython): 30
limb  ondalik  okul(s)  karats(s)  yerlesik(s)
 128      512    0.002      0.002     0.000004
 256     1024    0.009      0.005     0.000012
 512     2048    0.039      0.015     0.000031
1024     4096    0.160      0.046     0.000091
2048     8192    0.711      0.144     0.000273
```

Tablodaki `limb` sütunu bizim `TABAN = 10^4` basamaklarımızın sayısıdır; her limb yaklaşık 4 ondalık basamağa karşılık gelir. Süreler makineye bağlıdır, ama eğilim açıktır: uzunluk iki katına çıktığında okul yöntemi yaklaşık dört kat, Karatsuba yaklaşık üç kat yavaşlamalıdır (`n²` ve `n^1,585`'in beklenen oranları, 2^1,585 ≈ 3). Tabloda bu oranlar 512 limb'den itibaren görülür. 128 limb'de sürelerin çoğu ölçüm gürültüsü içinde kalır; bu uzunlukta Karatsuba yine de daha hızlıdır. Eşik 32 limb bir tasarım seçimidir; bu makinede kesin kırılma noktasını ayrıca ölçmedik. Sayılar CPython'un kendi işleyişiyle karşılaştırılamaz, çünkü bizim gerçeklememiz her basamak için saf Python döngüsü kullanır.

Aşağıdaki grafik, aynı verileri log-log ölçeğinde gösterir. Eğrinin eğimi, yöntemin büyüme üssünü verir: okul yönteminde yaklaşık 2, Karatsuba'da 1,6 ile 1,8 arasında okunur (küçük ölçümlerdeki gürültü nedeniyle).

![Şekil 19.5: Okul yöntemi, Karatsuba ve yerleşik çarpımın süreleri (log-log). Yerleşik çarpım C'de yazıldığı için en altta kalır.](gorseller/b19_karatsuba_olcum.png)

Şekil 19.5'teki yerleşik çarpım eğrisi, bizim Python gerçeklememizle doğrudan karşılaştırılmamalıdır. CPython'da int çarpımı C ile yazılmıştır ve bizim saf Python döngülerimizden onlarca kat hızlıdır. Asıl karşılaştırma iki Python eğrisi arasındadır: okul yöntemi ile Karatsuba. Bu iki eğri bizim algoritmamızın büyüme davranışını ölçer.

**CPython kaynağında Karatsuba.** Python 3.12.10'un kaynağında (`Objects/longobject.c`) Karatsuba `k_mul` fonksiyonunda gerçeklenmiştir ve eşik `KARATSUBA_CUTOFF` makrosu ile tanımlanır. Dosyayı `https://raw.githubusercontent.com/python/cpython/v3.12.10/Objects/longobject.c` adresinden indirdik ve tanımı doğruladık: `#define KARATSUBA_CUTOFF 70`. Bu sayı 70 **dahili basamak**tır; CPython'da her dahili basamak 30 bittir (`sys.int_info` çıktısında `bits_per_digit=30`). Yani 70 basamak yaklaşık 2100 bittir ve ondalık olarak yaklaşık 632 basamağa karşılık gelir (70·30·log₁₀2 ≈ 632,2). Bu uzunluğun altında CPython okul yöntemini (`x_mul`) kullanır. Kod kesitini Kod Okuma bölümünde ayrıntılı göreceksin.

## 19.6 Strassen matris çarpımı

Matris çarpımında `n × n` iki matrisin çarpımı, her sonuç elemanı için `n` çarpım gerektirir ve toplam `n³` çarpım yapılır. Bu, Bölüm 12'de gördüğümüz standart algoritmadır. Strassen (1969) fikri, 2×2 blok matrislerde çarpımların sayısını 8'den 7'ye düşürmektir. Blok bölme ile `A = [[A11, A12], [A21, A22]]` ve `B = [[B11, B12], [B21, B22]]` yazıldığında, C'nin blokları şu yedi çarpımdan hesaplanabilir:

- M1 = (A11 + A22)(B11 + B22)
- M2 = (A21 + A22) B11
- M3 = A11 (B12 - B22)
- M4 = A22 (B21 - B11)
- M5 = (A11 + A12) B22
- M6 = (A21 - A11)(B11 + B12)
- M7 = (A12 - A22)(B21 + B22)

Sonra şu toplamlarla C'nin blokları elde edilir: `C11 = M1 + M4 - M5 + M7`, `C12 = M3 + M5`, `C21 = M2 + M4`, `C22 = M1 - M2 + M3 + M6`. Bu formüllerin doğruluğunu el ile kontrol etmek sana iyi bir alıştırma olur; program da bunu bizim için yapacak.

![Şekil 19.6: Strassen'de blok bölme ve yedi çarpım. Her M çarpımı n/2 boyutlu iki matrisin çarpımıdır; toplama ve çıkarmalar O(n²) iştir.](gorseller/b19_strassen.png)

Her M çarpımı, kendisi de n/2 boyutlu matrislerle bir Strassen çağrısı olabilir. Bu yüzden bağıntı `T(n) = 7T(n/2) + Θ(n²)`'dir. Master Teoremi'nde `log₂ 7 ≈ 2,807` ve `f(n) = n² = O(n^(2,807 - 0,5))` olduğu için durum 1 geçerlidir ve sonuç `Θ(n^2,807)`'dir. Okul yöntemi `n³` idi, Strassen `n^2,807` olduğundan büyük `n` için üs farkı küçük ama gerçektir. Yukarıda kurduğumuz bağıntı bu sonucu verir.

Strassen'in gerçek dünyada kullanımı sınırlıdır. Birincisi, `n` küçük olduğunda ek bellek ayırma, kopyalama ve toplama maliyeti kazancı yer. İkincisi, toplama ve çıkarmalar sayısal kararlılığı etkiler: büyük ve küçük sayıların çıkarılması hata birikimini artırabilir; hata sınırlarının klasik algoritmadan kötü olduğu bilinir (genel bilgi, bu bölümde ayrıca ölçmedik). Üçüncüsü, BLAS gibi yüksek performanslı kütüphaneler genellikle Strassen kullanmaz; önbellek davranışı ve SIMD için optimize edilmiş klasik blok çarpımı tercih edilir (genel bilgi). Bu nedenle Strassen'i bir **eşik** ile birlikte kullanmak ve eşiği ölçerek seçmek gerekir.

Aşağıdaki C programı Strassen'i C11 ile gerçekler. Dört fonksiyonu olduğu gibi okuyacağız: `naif` referans çarpımdır, `ceyrek_al` ve `ceyrek_yaz` bloklar arasında kopyalama yapar, `strassen` ana algoritmadır. Matrisler satır sıralı tek boyutlu `double` dizileridir; `n` her zaman 2'nin kuvvetidir. Rastgele sayılar kendi xorshift üreteçimizle üretilir, böylece platformdan bağımsız tohumlanır.

```c
/* strassen.c: naif carpim ve Strassen (C11) */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

static unsigned long long durum = 42; /* xorshift64, tohum 42 */

static double rastgele(void)
{
    durum ^= durum << 13;
    durum ^= durum >> 7;
    durum ^= durum << 17;
    return (double)(durum % 2000001ULL) / 1000000.0 - 1.0;
}

/* c = a * b, n x n, satir sirali. O(n^3). */
static void naif(const double *a, const double *b, double *c,
                 size_t n)
{
    memset(c, 0, n * n * sizeof *c);
    for (size_t i = 0; i < n; i++)
        for (size_t k = 0; k < n; k++) {
            double aik = a[i * n + k];
            for (size_t j = 0; j < n; j++)
                c[i * n + j] += aik * b[k * n + j];
        }
}

/* n x n matrisin (qi, qj) ceyregini d'ye (n/2 x n/2) kopyala. */
```

Yukarıdaki başlıkta iki noktaya dikkat et. Birincisi `size_t` ve `double` ile boyutları açıkça seçtik; `long` Windows'ta 4 bayttır, bu yüzden dizi indekslerinde `long` kullanmadık. İkincisi `naif` fonksiyonu `memset` ile sonucu sıfırlar; bu, `c +=` ile biriktirme yaptığımız için zorunludur. Sonraki parçada blok kopyalama fonksiyonları vardır.

```c
static void ceyrek_al(const double *a, size_t n, size_t qi,
                      size_t qj, double *d)
{
    size_t h = n / 2;
    for (size_t i = 0; i < h; i++)
        memcpy(d + i * h, a + (qi * h + i) * n + qj * h,
               h * sizeof *d);
}

static void ceyrek_yaz(double *c, size_t n, size_t qi, size_t qj,
                       const double *s)
{
    size_t h = n / 2;
    for (size_t i = 0; i < h; i++)
        memcpy(c + (qi * h + i) * n + qj * h, s + i * h,
               h * sizeof *s);
}

/* c = a * b. n <= esik ise naif, aksi halde Strassen.
   Donus: 0 basarili, -1 bellek hatasi. */
```

Ana algoritma tek bir malloc ile 17 bloklık bir arena ayırır: 8 alt matris, 7 çarpım sonucu ve 2 geçici blok. Bu, her özyinelemede ayrı ayrı ayırmanın yükünü azaltır. Hata durumunda `-1` döndürülür ve `NULL` kontrolü yapılır.

```c
static int strassen(const double *a, const double *b, double *c,
                    size_t n, size_t esik)
{
    if (n <= esik) {
        naif(a, b, c, n);
        return 0;
    }
    size_t h = n / 2, hh = h * h;
    /* 8 alt matris + 7 carpim + 2 gecici = 17 blok */
    double *buf = malloc(17 * hh * sizeof *buf);
    if (!buf)
        return -1;
    double *A11 = buf, *A12 = buf + hh, *A21 = buf + 2 * hh;
    double *A22 = buf + 3 * hh;
    double *B11 = buf + 4 * hh, *B12 = buf + 5 * hh;
    double *B21 = buf + 6 * hh, *B22 = buf + 7 * hh;
    double *M[7];
    for (int t = 0; t < 7; t++)
        M[t] = buf + (8 + t) * hh;
    double *T1 = buf + 15 * hh, *T2 = buf + 16 * hh;

```

Aşağıdaki parçada yedi çarpım sırayla hesaplanır. Her `strassen(T1, T2, M[k], h, esik)` çağrısı yardımcı geçici blokları girdi olarak alır; özyinelemenin kendi bellek ayırması olduğu için bu iki geçici blok üzerine yazılmaz.

```c
    ceyrek_al(a, n, 0, 0, A11); ceyrek_al(a, n, 0, 1, A12);
    ceyrek_al(a, n, 1, 0, A21); ceyrek_al(a, n, 1, 1, A22);
    ceyrek_al(b, n, 0, 0, B11); ceyrek_al(b, n, 0, 1, B12);
    ceyrek_al(b, n, 1, 0, B21); ceyrek_al(b, n, 1, 1, B22);
    int hata = 0;
    /* M1 */
    for (size_t i = 0; i < hh; i++) {
        T1[i] = A11[i] + A22[i]; T2[i] = B11[i] + B22[i]; }
    hata |= strassen(T1, T2, M[0], h, esik);
    /* M2 */
    for (size_t i = 0; i < hh; i++) T1[i] = A21[i] + A22[i];
    hata |= strassen(T1, B11, M[1], h, esik);
    /* M3 */
    for (size_t i = 0; i < hh; i++) T1[i] = B12[i] - B22[i];
    hata |= strassen(A11, T1, M[2], h, esik);
    /* M4 */
    for (size_t i = 0; i < hh; i++) T1[i] = B21[i] - B11[i];
    hata |= strassen(A22, T1, M[3], h, esik);
    /* M5 */
    for (size_t i = 0; i < hh; i++) T1[i] = A11[i] + A12[i];
    hata |= strassen(T1, B22, M[4], h, esik);
    /* M6 */
    for (size_t i = 0; i < hh; i++) {
        T1[i] = A21[i] - A11[i]; T2[i] = B11[i] + B12[i]; }
    hata |= strassen(T1, T2, M[5], h, esik);
    /* M7 */
    for (size_t i = 0; i < hh; i++) {
        T1[i] = A12[i] - A22[i]; T2[i] = B21[i] + B22[i]; }
```

```c
    hata |= strassen(T1, T2, M[6], h, esik);
    /* Sonuc ceyrekleri */
    for (size_t i = 0; i < hh; i++)
        T1[i] = M[0][i] + M[3][i] - M[4][i] + M[6][i];
    for (size_t i = 0; i < hh; i++)
        T2[i] = M[2][i] + M[4][i];
    ceyrek_yaz(c, n, 0, 0, T1); ceyrek_yaz(c, n, 0, 1, T2);
    for (size_t i = 0; i < hh; i++)
        T1[i] = M[1][i] + M[3][i];
    for (size_t i = 0; i < hh; i++)
        T2[i] = M[0][i] - M[1][i] + M[2][i] + M[5][i];
    ceyrek_yaz(c, n, 1, 0, T1); ceyrek_yaz(c, n, 1, 1, T2);
    free(buf);
    return hata ? -1 : 0;
}
```

Son adım sonuç bloklarını birleştirir: `C11` ve `C12` ile `C21` ve `C22` iki kez kullanılan geçici bloklara yazılır, ardından `ceyrek_yaz` ile doğru konumlara kopyalanır. `free(buf)` ile arenayı serbest bırakırız; bu satır atlanırsa ASan bellek sızıntısı raporlar.

Programın ana fonksiyonu üç boyutta doğrulama yapar: `n = 8`, `64` ve `128`. Eşik olarak 8 seçilmiştir, böylece `n = 64` ve `128` için birkaç özyineleme seviyesi gerçekleşir. Kontrol, `naif` ile `strassen` sonuçları arasındaki en büyük mutlak farktır. Zaman ölçümü yalnızca `./strassen olcum` ile yapılır.

```c

static double maks_fark(const double *x, const double *y, size_t m)
{
    double d = 0.0;
    for (size_t i = 0; i < m; i++)
        if (fabs(x[i] - y[i]) > d)
            d = fabs(x[i] - y[i]);
    return d;
}

static void doldur(double *m, size_t cnt)
{
    for (size_t i = 0; i < cnt; i++)
        m[i] = rastgele();
}
```

```c
int main(int argc, char **argv)
{
    (void)argv;
    size_t boyut[] = {8, 64, 128};
    for (size_t t = 0; t < 3; t++) {
        size_t n = boyut[t], m = n * n;
        double *a = malloc(m * sizeof *a), *b = malloc(m * sizeof *b);
        double *c1 = malloc(m * sizeof *c1);
        double *c2 = malloc(m * sizeof *c2);
        if (!a || !b || !c1 || !c2)
            return 1;
        doldur(a, m);
        doldur(b, m);
        naif(a, b, c1, n);
        if (strassen(a, b, c2, n, 8) != 0)  /* esik 8 */
            return 1;
        printf("n=%4zu maks_fark=%.3e\n", n, maks_fark(c1, c2, m));
        free(a); free(b); free(c1); free(c2);
    }
    if (argc > 1) {                          /* olcum modu */
        size_t n = 512, m = n * n;
        double *a = malloc(m * sizeof *a), *b = malloc(m * sizeof *b);
        double *c = malloc(m * sizeof *c);
        doldur(a, m);
        doldur(b, m);
        clock_t t0 = clock();
        naif(a, b, c, n);
        clock_t t1 = clock();
        strassen(a, b, c, n, 64);
        clock_t t2 = clock();
        printf("n=512 naif=%.3f s strassen(esik=64)=%.3f s\n",
               (double)(t1 - t0) / CLOCKS_PER_SEC,
               (double)(t2 - t1) / CLOCKS_PER_SEC);
        free(a); free(b); free(c);
    }
    return 0;
```

WSL içinde programı şöyle derledik: `gcc -O2 -Wall -Wextra -std=c11 -o strassen strassen.c -lm`. Derleme uyarısız geçti. Ardından `olcum` argümanıyla çalıştırdık:

```term
$ ./strassen olcum
n=   8 maks_fark=0.000e+00
n=  64 maks_fark=1.799e-14
n= 128 maks_fark=6.928e-14
n=512 naif=0.041 s strassen(esik=64)=0.041 s
```

Fark değerleri (`maks_fark`) 10^-14 mertebesindedir; bu, kayan noktalı aritmetik hatasının beklenen büyüklüğüdür ve iki yöntem arasında fark olmadığı anlamına gelmez. Süre satırı önemli bir sonuç verir: `n = 512` ve eşik 64 için bizim Strassen gerçeklememiz klasik naif çarpımdan **daha hızlı değildir**; iki süre de bu makinede yaklaşık 0,04 saniyedir. Bunun nedeni, 512'lik matrisin altında kalan 64'lük bloklarda özyineleme ve bellek ayırma yükünün, kazanılan çarpım sayısından büyük olmasıdır. Eşiği 512'ye çıkarırsan Strassen hiç çalışmaz; eşiği 16'ya indirirsen bellek ayırma sayısı artar. Gerçek kazancı görmek için eşiği ölçerek seçmelisin; bu, Strassen'in pratik kullanımının neden dikkatli bir ayar gerektirdiğini gösterir.

Bellek hatalarını bulmak için programı ASan ve UBSan ile de derledik. Komut `gcc -g -O1 -Wall -Wextra -std=c11 -fsanitize=address,undefined -fno-omit-frame-pointer -o strassen_asan strassen.c -lm` idi. Çalıştırma çıktısı şöyle:

```term
$ ./strassen_asan
n=   8 maks_fark=0.000e+00
n=  64 maks_fark=1.799e-14
n= 128 maks_fark=6.928e-14
```

Çıktıda sanitize raporu yoktur ve program sıfırla çıkar; bu, bellek sızıntısı ve sınır dışı erişim bulunmadığını gösterir. Bu kontrolü WSL2 içinde yaptık; ASan ve valgrind gibi araçlar Linux üzerinde çalışır ve Windows'ta doğrudan kullanılamaz. Ayrıca, bu C kodu `double` ile yazıldığından `long` boyutu sorunu buradan doğmaz.

## 19.7 En yakın nokta çifti

Düzlemde `n` nokta verildiğinde en küçük Öklid uzaklığına sahip iki noktayı bulmak, yakın nokta sorgularının temelidir. Bir İHA'nın radar kayıtlarında iki hedefin çakışıp çakışmadığını anlamak, bir harita üzerinde en yakın istasyonu bulmak ya da kümeleme algoritmalarında komşuları hızlıca belirlemek bu probleme indirgenebilir. Kaba kuvvet her çift için uzaklığı hesaplar: `n(n-1)/2` çift, yani `O(n²)`.

D&C çözümü şöyle işler. Noktaları x koordinatına göre sıralayıp ortadan ikiye böleriz; bölme çizgisinin solundaki ve sağındaki en yakın çiftleri özyinelemeyle buluruz. Sol tarafta en küçük uzaklık `dL`, sağda `dR` olsun ve `δ = min(dL, dR)` diyelim. Şimdi yalnızca bölme çizgisinin iki yanında `δ` genişliğinde bir **şerit** içindeki noktalar ilgilenir: bölme çizgisine uzaklığı `δ`'dan küçük olan noktalar. Bu noktaların hepsini y koordinatına göre sıralarız ve her nokta için yalnızca y'de `δ`'ya kadar yakın olan sonraki noktalarla karşılaştırma yaparız.

Bu adımın neden doğru olduğunu anlamak için bir sayım argümanı kullanılır. Şeridi, bölme çizgisinin iki yanında `2δ` genişliğinde ve `δ` yüksekliğinde bir dikdörtgen olarak düşün. Dikdörtgen `δ/2` kenarlı sekiz kareye bölünebilir. Her kare tamamen sol ya da tamamen sağ yarının içinde kalır. Bir karede iki nokta olsaydı, ikisi de aynı yarıda olduğundan aralarındaki uzaklık en fazla `δ/√2 < δ` olurdu. Oysa `δ` her yarı içindeki en küçük uzaklıktan büyük değildir; bu bir çelişkidir. Demek ki her kare en fazla bir nokta içerir. Şeritteki `p` noktası kendi karesini doldurur; geriye `p` için en fazla 7 aday kare kalır.

![Şekil 19.7: En yakın çift şeridi. 2δ x δ dikdörtgen sekiz kareye bölünür; her karede en fazla bir nokta olabilir, bu yüzden p için en fazla 7 aday bakılır.](gorseller/b19_closest_serit.png)

Bu gözlem, şerit işleminin `O(n)` olmasını sağlar: her nokta sabit sayıda komşuyla karşılaştırılır. Şeridin y'ye göre sıralı olması için özyineleme sırasında y-sıralı listeleri birleştiririz; bu birleştirme her seviyede `O(n)` iştir. Böylece bağıntı `T(n) = 2T(n/2) + Θ(n)`'dir ve Master durum 2 ile `Θ(n log n)` verir. Başlangıçtaki x-sıralaması bir kez `O(n log n)` ile yapılır ve toplam değişmez.

Aşağıdaki Python programı bu algoritmanın tam gerçeklemesidir. `ISARET` sözlüğü, şerit içinde bir noktanın kaç komşuyla karşılaştırıldığının en büyük değerini tutar; böylece 7 sınırının pratikte nasıl göründüğünü ölçebiliriz.

```python
# closest.py: en yakin nokta cifti, kaba kuvvet ve bol-fethet
import heapq
import math
import random
import time

ISARET = {"max_komsu": 0}


def mesafe(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def kaba(P):
    """Tum ciftler: O(n^2). Dogrulama referansi."""
    en = (math.inf, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = mesafe(P[i], P[j])
            if d < en[0]:
                en = (d, (P[i], P[j]))
    return en


```

```python
def bol_fethet(px):
    """px x'e gore sirali. Donus: (d, cift, y sirali liste)."""
    n = len(px)
    if n <= 3:
        d, cift = kaba(px)
        return d, cift, sorted(px, key=lambda p: p[1])
    mid = n // 2
    xm = px[mid][0]                                  # bolme cizgisi
    dl, cl, yl = bol_fethet(px[:mid])
    dr, cr, yr = bol_fethet(px[mid:])
    d, cift = (dl, cl) if dl <= dr else (dr, cr)
    y = list(heapq.merge(yl, yr, key=lambda p: p[1]))  # birlestir
    serit = [p for p in y if abs(p[0] - xm) < d]
    for i, p in enumerate(serit):
        sayac = 0
        for q in serit[i + 1:]:
            if q[1] - p[1] >= d:   # y farki d'den buyuk
                break
            sayac += 1
            dd = mesafe(p, q)
            if dd < d:
                d, cift = dd, (p, q)
        ISARET["max_komsu"] = max(ISARET["max_komsu"], sayac)
    return d, cift, y


```

```python
def en_yakin(P):
    px = sorted(P)                                   # once x'e gore
    d, cift, _ = bol_fethet(px)
    return d, cift


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(2, 60)
        P = [(rnd.randint(0, 500), rnd.randint(0, 500))
             for _ in range(n)]
        d1, _ = kaba(P)
        d2, _ = en_yakin(P)
        assert abs(d1 - d2) < 1e-12, (d1, d2)
    print("300 rastgele kume: bol-fethet == kaba kuvvet")
    print("serit icinde bir noktanin en fazla komsu sayisi:",
          ISARET["max_komsu"])
    for n in (500, 2000):
        P = [(rnd.random(), rnd.random()) for _ in range(n)]
        t0 = time.perf_counter()
        d1, _ = kaba(P)
        t1 = time.perf_counter()
        d2, _ = en_yakin(P)
        t2 = time.perf_counter()
        print("n=%5d kaba=%.3fs bol-fethet=%.3fs"
```

Doğrulama iki şey yapar: rastgele 300 küme için D&C sonucu kaba kuvvetle eşleşiyor mu, ve kaç komşu karşılaştırıldı. Zaman ölçümü için 500 ve 2000 noktalı kümeler kullanılır.

```term
$ python closest.py
300 rastgele kume: bol-fethet == kaba kuvvet
serit icinde bir noktanin en fazla komsu sayisi: 2
n=  500 kaba=0.019s bol-fethet=0.002s
n= 2000 kaba=0.275s bol-fethet=0.009s
```

Çıktı, D&C sonucunun kaba kuvvetle 300 rastgele kümede tam eşleştiğini gösterir. Şerit içinde bir noktanın karşılaştırıldığı en fazla komşu sayısı 2'dir; bu, 7 sınırının altındadır ama 7'nin asla aşılmayacağı anlamına gelmez, sadece bu girdilerde görülen en büyük değerdir. Süreler, `n` iki kat artınca kaba kuvvetin yaklaşık dört kat, D&C'nin ise yaklaşık `n log n` oranında arttığını gösterir. `n = 2000` için kaba kuvvet yaklaşık 0,28 saniye, D&C yaklaşık 0,009 saniye sürer. Bu fark makineye bağlıdır; oran ise tutarlıdır.

**Bunu not et:** Bu algoritma sayılar üzerinde tam kesinlik ister; kayan noktalı uzaklıklar `math.hypot` ile hesaplanır. Çok yakın noktalarda ve çok büyük koordinatlarda yuvarlama hataları, aynı çift için farklı sonuç verebilir. Bu bölümdeki testler tamsayı koordinatlarla ve rastgele ondalıklarla geçti; kesin sayısal garanti için ek analiz gerekir.

## 19.8 Maksimum alt dizi toplamı: D&C ve Kadane

Bir sayı dizisi verildiğinde, ardışık bir parçasının toplamının en büyük olduğu aralığı bulmak, borsa verilerinde en iyi alım-satım aralığını ya da bir sensörün en büyük birikimli sapmasını bulmakla eşdeğerdir. Bu problemi D&C ile çözebiliriz. Dizi ortadan ikiye bölünür. En iyi aralık üç yerde olabilir: tamamen sol yarıda, tamamen sağ yarıda, ya da ortayı kesen bir aralıkta.

Ortayı kesen aralık için D&C'nin asıl hilesi vardır. Sol yarıda ortadan geriye doğru genişleyen en iyi son eki (suffix) ve sağ yarıda ortadan ileriye doğru genişleyen en iyi öneki (prefix) ayrı ayrı bulunur. Bu ikisinin toplamı ortayı kesen en iyi aralığı verir. Her iki hesap da `O(n)` iştir; bu yüzden bağıntı `T(n) = 2T(n/2) + Θ(n)` olur ve sonuç `Θ(n log n)`'dir.

Kadane algoritması ise aynı problemi tek bir geçişte çözer. Bu bir dinamik programlamadır (Bölüm 16): `dp[i]`, `a[i]` ile biten en büyük alt dizi toplamı olarak tanımlanır. Geçiş bağıntısı `dp[i] = max(a[i], dp[i-1] + a[i])`'dir: ya önceki birikime devam edersin ya da yeni bir aralık başlatırsın. Cevap `dp` değerlerinin en büyüğüdür. Her eleman yalnızca bir kez işlenir, bu yüzden Kadane `O(n)`'dir.

Bu iki algoritmayı yan yana koymanın öğretici yanı şudur: D&C her seviyede her elemanın son ek toplamını yeniden tarar, bu yüzden toplam `n log n` iş yapar. Kadane ise `dp[i]` değerini yalnızca `dp[i-1]`'den hesaplar ve tekrar taramaz. Yani aynı problem, D&C ile çözüldüğünde gereksiz bir tekrar içerir. Bu, Bölüm 19.3'teki karar tablosunun sınırının bulanık olduğunu gösterir: alt problemler bağımsız görünse de birleştirme adımında ortak bilgi olabilir.

Aşağıdaki programda üç fonksiyon var: D&C (`dc_max`), Kadane (`kadane`) ve doğrulama için `O(n²)` kaba kuvvet (`brute`).

```python
# maxsub.py: maksimum alt dizi toplami: D&C ve Kadane
import random
import time


def dc_max(a, lo, hi):
    """a[lo:hi] icinde (toplam, bas, son) dondurur; son exclusive."""
    if hi - lo == 1:
        return a[lo], lo, lo + 1
    mid = (lo + hi) // 2
    sol = dc_max(a, lo, mid)
    sag = dc_max(a, mid, hi)
    # Ortayi kesen en iyi aralik: sol kisim mid'den geriye,
    # sag kisim mid'den ileriye dogru genisler.
    bl_top, bl_bas, s = -10 ** 18, mid, 0
    for i in range(mid - 1, lo - 1, -1):
        s += a[i]
        if s > bl_top:
            bl_top, bl_bas = s, i
    br_top, br_son, s = -10 ** 18, mid, 0
    for j in range(mid, hi):
        s += a[j]
        if s > br_top:
            br_top, br_son = s, j + 1
    orta = (bl_top + br_top, bl_bas, br_son)
    return max(sol, sag, orta, key=lambda t: t[0])


```

```python
def kadane(a):
    """dp[i] = en buyuk toplam, a[i] ile biten aralik."""
    dp, bas = a[0], 0
    en = (a[0], 0, 1)
    for i in range(1, len(a)):
        if dp > 0:    # onceki birikimi surdur
            dp += a[i]
        else:                         # yeni aralik baslat
            dp, bas = a[i], i
        if dp > en[0]:
            en = (dp, bas, i + 1)
    return en


def brute(a):
    """O(n^2): tum (i, j) cifti icin on toplamlarla."""
    on = [0]
    for x in a:
        on.append(on[-1] + x)
    n = len(a)
    return max(on[j] - on[i] for i in range(n)
               for j in range(i + 1, n + 1))

```

```python

if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(500):
        n = rnd.randint(1, 40)
        a = [rnd.randint(-20, 20) for _ in range(n)]
        ref = brute(a)
        t1, l1, r1 = dc_max(a, 0, n)
        t2, l2, r2 = kadane(a)
        assert t1 == ref and sum(a[l1:r1]) == ref
        assert t2 == ref and sum(a[l2:r2]) == ref
    print("500 rastgele dizi: D&C = Kadane = O(n^2)")
    a = [rnd.randint(-10 ** 6, 10 ** 6) for _ in range(10 ** 5)]
    t0 = time.perf_counter()
    r1 = dc_max(a, 0, len(a))
    t1 = time.perf_counter()
    r2 = kadane(a)
    t2 = time.perf_counter()
    print("n = 10^5: D&C %.3f s, Kadane %.3f s" % (t1 - t0, t2 - t1))
```

Programın doğrulama bölümü, 500 rastgele diziyi (negatif sayılar dahil, tohum 42) üç yöntemle karşılaştırır: değer ve döndürdüğü aralığın toplamı kaba kuvvetle eşleşmelidir. Zaman ölçümü `10^5` uzunluklu bir dizi üzerinde yapılır.

```term
$ python maxsub.py
500 rastgele dizi: D&C = Kadane = O(n^2)
n = 10^5: D&C 0.157 s, Kadane 0.006 s
ayni toplam: True | toplam = 255405595
```

Sonuç açıktır: D&C ve Kadane aynı değeri verir, ama `10^5` elemanda D&C yaklaşık 160 milisaniye sürerken Kadane yaklaşık 6 milisaniye sürer. Bu, `n log n` ile `n` arasındaki farkı ve DP'nin tek geçişli avantajını gösterir. Mülakatta bu soruyu D&C ile çözmek kabul edilir; ama soru "en hızlı yöntem" diye sorulursa Kadane'yi söylemen beklenir ve neden doğrusal olduğunu açıklamalısın.

Son olarak `dc_max` içindeki birleştirme adımı hakkında bir not: aralık sınırları `bl_bas` (dahil) ve `br_son` (hariç) olarak tutulur. Bu, Python'un dilim (slice) kuralıyla uyumludur: `a[bas:son]` aralığın kendisidir. Doğrulama bu aralığın toplamını da kontrol eder, böylece yalnızca değeri değil aralığı da test etmiş oluruz.


## 19.9 Medyanların medyanı: deterministik seçim

Bölüm 13.5'te quickselect'i gördük: rastgele bir pivot seçer, diziyi ona göre böler ve yalnızca bir tarafa iner. Ortalama süre `O(n)`'dir, ama pivot kötü seçilirse `O(n²)` olur. Bölüm 13'teki kötü durum, sıralı ya da neredeyse sıralı girdilerde ve sabit bir pivot kuralında ortaya çıkar. Medyanların medyanı algoritması (Blum, Floyd, Pratt, Rivest, Tarjan, 1973) pivotu öyle seçer ki kötü durum garanti altına alınır: her zaman `O(n)`.

Fikir şudur. Diziyi 5'erli gruplara böl; her grubun medyanını bul (5 elemanlık bir grupta medyanı sabit sayıda karşılaştırmada bulabilirsin). Bu medyanların medyanını özyinelemeyle bul ve onu pivot olarak kullan. Bu pivot, her iki yönde de elemanların kabaca yüzde 30'unu geçmez; bu yüzden bir sonraki özyineleme en fazla yaklaşık `7n/10` boyutlu olur.

Bu garantiyi bir sayımla görelim. Her 5'li grubun medyanı, grubun en az üç elemanından büyük ya da eşittir; medyanların yaklaşık yarısı (`n/10` kadar) bu büyük gruplardan gelir ve her biri kendi grubunda en az iki eleman daha büyük yapar. Böylece pivottan büyük en az `3n/10` eleman vardır. Simetrik olarak pivottan küçük en az `3n/10` eleman vardır. Yani en kötü durumda her yanda en fazla yaklaşık `7n/10` eleman kalır.

Bağıntı şöyle yazılır: `T(n) ≤ T(n/5) + T(7n/10) + Θ(n)`. Bu bağıntı, grupların medyanlarını bulma (`T(n/5)`), bir alt problem (`T(7n/10)`) ve bölme (`Θ(n)`) adımlarını yansıtır. Bu bağıntı Master Teoremi'nin biçimine uymaz, çünkü iki farklı alt problem boyutu vardır. Bunu yerine koyma ile çözeriz: `T(n) ≤ cn` olduğunu varsayalım. Sağ tarafı yazarsak

`T(n) ≤ c(n/5) + c(7n/10) + an = cn(9/10) + an`

elde ederiz. Bunun `cn`'den küçük ya da eşit olması için `an ≤ cn/10`, yani `c ≥ 10a` yeter. Bu, `T(n) = Θ(n)` sonucunu verir. Bölüm 12'deki yerine koyma yönteminin tipik bir uygulamasıdır.

Aşağıdaki programda `sec(dizi, k)` fonksiyonu, dizinin `k`. en küçük elemanını (0 tabanlı) döndürür. Pivot eşit elemanları ayırmak için üç parçaya (küçük, eşit, büyük) bölünür; bu, tekrarlı değerlerde sonsuz özyinelemeyi önler.

```python
# medyan.py: deterministik O(n) secim (medyanlarin medyani)
import random
import time


def sec(dizi, k):
    """Sirali dizinin k. elemani (0 tabanli), kotu durumda O(n)."""
    n = len(dizi)
    if n <= 5:
        return sorted(dizi)[k]
    # 1) 5'erli gruplarin medyanlari
    medyanlar = []
    for i in range(0, n, 5):
        grup = sorted(dizi[i:i + 5])
        medyanlar.append(grup[len(grup) // 2])
    # 2) medyanlarin medyani (ozyinelemeli): pivot
    piv = sec(medyanlar, (len(medyanlar) - 1) // 2)
    # 3) pivota gore uc parcaya bol
    sol = [x for x in dizi if x < piv]
    orta = [x for x in dizi if x == piv]
    sag = [x for x in dizi if x > piv]
    # 4) hangi parcada?
    if k < len(sol):
        return sec(sol, k)
    if k < len(sol) + len(orta):
        return piv
    return sec(sag, k - len(sol) - len(orta))


```

```python
if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(1, 80)
        a = [rnd.randint(0, 15) for _ in range(n)]   # cok tekrar
        s = sorted(a)
        for k in range(n):
            assert sec(a, k) == s[k]
    print("300 rastgele dizi, tum k: sec == sorted()[k] (tekrarli)")
    a = [rnd.random() for _ in range(10 ** 5)]
    t0 = time.perf_counter()
    m = sec(a, len(a) // 2)
    t1 = time.perf_counter()
    s = sorted(a)[len(a) // 2]
    t2 = time.perf_counter()
    print("n = 10^5 medyan: sec %.3f s, sorted %.3f s"
          % (t1 - t0, t2 - t1))
```

Doğrulama, 300 rastgele diziyi (değerler 0 ile 15 arasında, bolca tekrar) her `k` için `sorted(a)[k]` ile karşılaştırır. Zaman ölçümünde ise `10^5` elemanlı bir dizinin medyanını hesaplarız.

```term
$ python medyan.py
300 rastgele dizi, tum k: sec == sorted()[k] (tekrarli)
n = 10^5 medyan: sec 0.042 s, sorted 0.012 s
ayni deger: True
```

Sonuç doğrudur, ama dürüst bir not gerekir: Python'un `sorted`'ı C'de yazılmış ve çok optimize edilmiştir; bu yüzden medyanı bulmak için tüm diziyi sıralamak bu ölçümde daha hızlıdır. Medyanların medyanı algoritmasının değeri asimptotik garantidedir, sabit faktörlerde değil. Pratikte kütüphaneler genellikle introselect gibi, kötü durumu da koruyan ama sabiti küçük algoritmalar kullanır (genel bilgi).

## 19.10 Skyline problemi

Bir şehirde binaların kenar koordinatları ve yükseklikleri verildiğinde, binaların dış hatlarını birleştiren siluetin köşe noktalarını bulmak istiyoruz. Her bina `(sol, yükseklik, sağ)` üçlüsüyle temsil edilir. Sonuç, yükseklik değişen noktaların listesidir. Bu problem bir harita çizimi, bir radar ufuk hattı hesabı ya da bir İHA'nın engellerden kaçınma profilinin çıkarılmasında karşımıza çıkar.

D&C çözümü basittir. Binaları ortadan ikiye bölüp her yarı için siluet hesaplarız; sonra iki siluetin birleştirmesini yaparız. Birleştirme, iki siluetin köşe noktalarını x'e göre tarar. Herhangi bir x'te yeni siluetin yüksekliği, iki siluetin o andaki yüksekliklerinin en büyüğüdür. Yükseklik değişmiyorsa nokta yazılmaz. Birleştirme her seviyede toplam `O(n)` iştir; bu yüzden bağıntı `T(n) = 2T(n/2) + Θ(n)` ve sonuç `Θ(n log n)`'dir.

![Şekil 19.8: Solda ve ortada iki bağımsız siluet, sağda birleşim. Birleşimde her x'te iki yükseklikten büyüğü alınır; yükseklik değişmeyen noktalar atılır.](gorseller/b19_skyline_birlestir.png)

Aşağıdaki program D&C ile siluet hesaplar ve sonucu her birim aralık için kaba kuvvet yüksekliğiyle karşılaştırır. Kaba kuvvette her `x` için `x` noktasını içeren binaların en büyük yüksekliği alınır.

```python
# skyline.py: bina siluetleri, D&C birlestirme ve kaba kuvvet
import random


def birlestir(A, B):
    """Iki siluetin noktalarini x'e gore tara; max yukseklik."""
    i = j = 0
    h1 = h2 = 0          # A ve B'nin o andaki yukseklikleri
    sonuc = []
    while i < len(A) or j < len(B):
        xa = A[i][0] if i < len(A) else float("inf")
        xb = B[j][0] if j < len(B) else float("inf")
        x = min(xa, xb)
        if xa == x:
            h1 = A[i][1]
            i += 1
        if xb == x:
            h2 = B[j][1]
            j += 1
        h = max(h1, h2)
        if not sonuc or sonuc[-1][1] != h:  # degisti mi?
            sonuc.append((x, h))
    return sonuc


```

```python
def sil(binalar):
    """binalar: (sol, yukseklik, sag). Donus: [(x, h), ...]."""
    if not binalar:
        return []
    if len(binalar) == 1:
        L, H, R = binalar[0]
        return [(L, H), (R, 0)]
    mid = len(binalar) // 2
    return birlestir(sil(binalar[:mid]), sil(binalar[mid:]))


def taban_yukseklik(binalar, x):
    """Birim aralik [x, x+1) icin kaba kuvvet yuksekligi."""
    return max((h for L, h, R in binalar if L <= x < R), default=0)


def sil_yukseklik(s, x):
    h = 0
    for xk, hk in s:
        if xk <= x:
            h = hk
        else:
            break
    return h


```

```python
if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(1, 25)
        binalar = []
        for _ in range(n):
            L = rnd.randint(0, 40)
            R = L + rnd.randint(1, 15)
            binalar.append((L, rnd.randint(1, 30), R))
        s = sil(binalar)
        for x in range(0, 60):
            assert sil_yukseklik(s, x) == taban_yukseklik(binalar, x)
    print("300 rastgele bina seti: D&C siluet == kaba kuvvet")
    ornek = [(1, 11, 5), (2, 6, 7), (3, 13, 9), (12, 7, 16),
             (14, 3, 25), (19, 18, 22), (23, 13, 29), (24, 4, 30)]
    print("Ornek siluet (Bolum 19.10'daki sekil):")
    for x, h in sil(ornek):
```

```term
$ python skyline.py
300 rastgele bina seti: D&C siluet == kaba kuvvet
Ornek siluet (Bolum 19.10'daki sekil):
x= 1  h=11
x= 3  h=13
x= 9  h= 0
x=12  h= 7
x=16  h= 3
x=19  h=18
x=22  h= 3
x=23  h=13
x=29  h= 4
x=30  h= 0
```

Çıktıda 300 rastgele bina setinin D&C ile kaba kuvvet arasında tutarlı olduğunu görüyorsun. Son satır, verilen örnek için siluetin köşe listesini gösterir: `(1, 11)` ilk binanın yüksekliğiyle başlar, `(9, 0)` ise 9. noktada siluetin yere indiğini söyler. Dikkat edilmesi gereken nokta: birleştirme sonucu yalnızca yüksekliğin değiştiği x değerlerini tutar; her x'te bir yükseklik olduğu varsayımıyla yazılmaz.

## 19.11 FFT ile polinom çarpımı

İki polinomu katsayılarıyla çarpmak için her katsayı çiftini çarpıp toplamak gerekir: `n` katsayılı iki polinom için `n²` çarpım. Bu, DSP'de konvolüsyonun doğrudan hesabıdır ve sinyal işlemede her saniye milyonlarca kez yapılabilir. Hızlı Fourier dönüşümü (FFT), bu işi `O(n log n)` zamanda yapar ve D&C'nin en önemli uygulamalarından biridir.

Fikir şudur. Bir polinomu `n` farklı noktada değerlendirirsen, değerlerden polinomu geri kurabilirsin; bu bir interpolasyondur. İki polinomun çarpımı, değerlendirme noktalarında değerlerin çarpımıdır. Yani: (1) iki polinomu `n` noktada değerlendir, (2) değerleri noktasal çarp, (3) sonuç polinomunu interpolasyonla geri kur. Adımlar (1) ve (3) naif yapılırsa yine `n²` olur; ama noktalar özel seçilirse, birim köklerin (`ω = e^(-2πi/n)`) kuvvetleri, bir D&C yapısıyla hızlıca hesaplanabilir.

Cooley ve Tukey'nin (1965) algoritması bunu şöyle yapar: katsayı dizisini çift ve tek indisli iki diziye ayırır, her birinde FFT'yi özyinelemeyle çalıştırır, sonra iki sonucu birleştirir. Birleştirme adımı `k = 0 ... n/2 - 1` için şu kelebek (butterfly) işlemidir: `X[k] = E[k] + ω^k O[k]` ve `X[k + n/2] = E[k] - ω^k O[k]`. Burada `E` çift, `O` tek indisli alt sonuçlardır. Bağıntı `T(n) = 2T(n/2) + Θ(n)` olduğundan sonuç `Θ(n log n)`'dir.

![Şekil 19.9: n = 8 için FFT kelebek diyagramı. Giriş bit-ters sırada, her aşamada dört kelebek, üç aşama vardır.](gorseller/b19_fft_kelebek.png)

Şekil 19.9'da girişin sırası bit-tersinedir: `x0, x4, x2, x6, x1, x5, x3, x7`. Bunun nedeni özyinelemenin çift-tek ayrımının sonuçlarını bu sıraya göre birleştirmesidir. Her kelebek, iki girişi alır ve iki çıkış üretir; çapraz çizgiler `ω^k` ile çarpılan kanaldır.

Aşağıdaki program özyinelemeli FFT'yi gerçekler, konvolüsyonu bu FFT ile hesaplar ve sonucu hem dogrudan çarpımla hem de `numpy.convolve` ile karşılaştırır. Girdi katsayıları tam sayı olduğu için, sonuç kayan noktadan yuvarlanarak tam sayıya çevrilir. Bu yuvarlama, katsayılar küçük ve `n` makul olduğu sürece hatasızdır; büyük katsayılarda kayan nokta hatası yuvarlamayı bozabilir.

```python
# fft_poly.py: Cooley-Tukey FFT ile polinom carpimi
import cmath
import random
import time

import numpy as np


def fft(a):
    """Uzunluk 2'nin kuvveti. O(n log n)."""
    n = len(a)
    if n == 1:
        return a[:]
    cift = fft(a[0::2])                 # cift indisler
    tek = fft(a[1::2])                  # tek indisler
    sonuc = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * cmath.pi * k / n) * tek[k]
        sonuc[k] = cift[k] + t          # kelebek: ust kanat
        sonuc[k + n // 2] = cift[k] - t  # kelebek: alt kanat
    return sonuc


```

```python
def ters_fft(F):
    n = len(F)
    g = fft([z.conjugate() for z in F])
    return [z.conjugate() / n for z in g]


def carp_fft(p, q):
    """Katsayi listeleri p, q; carpim katsayilari (yuvarlanmis)."""
    boyut = len(p) + len(q) - 1
    n = 1
    while n < boyut:
        n *= 2
    P = fft([complex(x) for x in p] + [0j] * (n - len(p)))
    Q = fft([complex(x) for x in q] + [0j] * (n - len(q)))
    R = [x * y for x, y in zip(P, Q)]    # noktasal carpim
    r = ters_fft(R)
    return [round(z.real) for z in r[:boyut]]


def carp_direkt(p, q):
    c = [0] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            c[i + j] += x * y            # O(n^2)
    return c


```

```python
if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        p = [rnd.randint(0, 9) for _ in range(rnd.randint(1, 40))]
        q = [rnd.randint(0, 9) for _ in range(rnd.randint(1, 40))]
        ref = carp_direkt(p, q)
        assert carp_fft(p, q) == ref
        assert list(np.convolve(p, q)) == ref
    print("300 rastgele cift: FFT == dogrudan == numpy.convolve")
    for n in (512, 1024, 2048):
        p = [rnd.randint(0, 9) for _ in range(n)]
        q = [rnd.randint(0, 9) for _ in range(n)]
        t0 = time.perf_counter()
        carp_direkt(p, q)
        t1 = time.perf_counter()
        carp_fft(p, q)
        t2 = time.perf_counter()
        print("n=%5d direkt=%.3fs fft=%.3fs" % (n, t1 - t0, t2 - t1))
```

```term
$ python fft_poly.py
300 rastgele cift: FFT == dogrudan == numpy.convolve
n=  512 direkt=0.018s fft=0.006s
n= 1024 direkt=0.077s fft=0.013s
n= 2048 direkt=0.316s fft=0.028s
```

300 rastgele polinom çifti için üç yöntem de aynı sonucu verdi. Süreler, `n` iki katına çıktığında doğrudan çarpımın yaklaşık dört kat, FFT'nin ise iki katın biraz üzerinde arttığını gösterir; bu, `n log n` büyümesinin beklenen davranışıdır. Bizim FFT'miz saf Python'dur ve `numpy.fft`'nin C kodundan çok yavaştır; ama büyüme eğrisi aynıdır. Bölüm 52'de DSP tarafında bu konvolüsyonun sinyal işlemedeki yerini ve gerçek zamanlı filtrelemedeki yükünü tekrar ele alacağız.

## 19.12 Paralellik ve gerçek dünya

D&C'nin en doğal özelliklerinden biri paralelleşmeye uygun olmasıdır. Alt problemler bağımsız olduğu için, sol ve sağ yarıyı aynı anda farklı işlemcilerde çözebilirsin. Bu modele **fork-join** denir: bir noktada iş ikiye ayrılır (fork), her parça bağımsız çalışır ve sonunda sonuçlar birleşir (join). Bölüm 53'te iş parçacıkları ve eşzamanlılık ile bu modelin ayrıntılarına döneceğiz.

Paralel D&C'yi analiz etmek için iki ölçü kullanılır. **İş** (work) `T1`, tek işlemcide toplam iştir. **Yol uzunluğu** ya da span `T∞`, sınırsız işlemci olsa bile değişmeyen en uzun bağımlılık zinciridir. Birleştirme sıralaması için iş `Θ(n log n)`'dir; ama birleştirme adımı seri olarak yapılırsa span `Θ(n)`'de kalır, çünkü her seviyenin birleşimi kendi içinde sıralıdır ve paralel değildir. Paralel birleştirme (iki sıralı diziyi bölerek birleştirme) span'i `O(log² n)`'e indirir (genel bilgi, bu bölümde ayrıca ölçmedik). Sonuç olarak paralellik, birleştirme adımının ne kadar paralelleştirilebildiğine bağlıdır.

Gerçek dünya örnekleri şunlardır. MapReduce, büyük veriyi parçalara bölen, her parçayı bağımsız işleyen ve sonuçları birleştiren bir D&C modelidir (genel bilgi). GMP gibi büyük sayı kütüphaneleri, çok büyük tamsayı çarpımında Karatsuba'dan daha karmaşık D&C tabanlı algoritmalar kullanır (genel bilgi). Görüntü işlemede quadtree, bir görüntüyü dört kareye bölüp uzaysal arama yapmak için D&C kullanır (genel bilgi). FFT ise her ses, radar ve haberleşme işlemesinin çekirdeğindedir; bu, Bölüm 52'nin ana konusudur.

## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler örneğin programının çıktısıyla aynıdır. Çözüm kodunu okumadan önce her örneğin ilk üç adımını kendi kâğıdında dene.

### Örnek 1 (★): 3^13 mod 1000 ve hızlı üs izi

**Problem:** `x^n mod m` değerini, Bölüm 19.4'teki D&C yaklaşımıyla, ara değerleri göstererek hesapla. Örnek olarak `x = 3`, `n = 13`, `m = 1000` alalım.

**Adım 1 — Anla.** Girdi üç tamsayıdır (`x`, `n`, `m`); çıktı `x^n`'in `m` ile bölümünden kalandır. Kenar durum: `n = 0` için sonuç `1 mod m`'dir; `m = 1` için sonuç her zaman 0'dır.

**Adım 2 — Örnekle.** `3^13 = 1594323`'tür; mod 1000 ile sonuç `323`'tür. Bu değeri kendi hesabınla bulabiliyor musun? Şimdi bunu D&C ile adım adım yapalım.

**Adım 3 — Kaba çöz.** Doğrudan `3 · 3 · ... · 3` (13 kez) çarpımı yapılır. Her çarpımdan sonra `mod 1000` alırsan, 12 çarpım ve 13 mod işlemi gerekir. Bu, `Θ(n)` ve doğru ama yavaştır.

**Adım 4 — Örüntü.** `13 = 1101` (ikili). `x^13 = x^12 · x = (x^6)² · x`, `x^6 = (x^3)²`, `x^3 = (x^1)² · x`. Her adımda üs yarıya iner. Bu, `T(n) = T(n/2) + Θ(1)` bağıntısıdır; sonuç `Θ(log n)`'dir.

**Adım 5 — İyileştir.** Her ara sonucu hemen `mod m` ile küçült; böylece sayılar `m²`'yi geçmez. Programda `us_iz` fonksiyonu, her çağrının `yarım`, `kare` ve `sonuç` değerlerini yazdırır.

```python
# ex1.py: 3^13 mod 1000 hesabinin iz tablosu (Ornek 1)
def us_iz(x, n, m, derin=0):
    if n == 0:
        print("  " * derin + "n=0: sonuc = 1")
        return 1 % m
    yarim = us_iz(x, n // 2, m, derin + 1)
    kare = yarim * yarim % m
    sonuc = kare
    if n % 2 == 1:
        sonuc = kare * x % m
    print("  " * derin + "n=%d: yarim=%d kare=%d sonuc=%d"
          % (n, yarim, kare, sonuc))
    return sonuc


if __name__ == "__main__":
    print("3^13 mod 1000 (izli cagri):")
    s = us_iz(3, 13, 1000)
    print("sonuc =", s, "| pow ile =", pow(3, 13, 1000))
    assert s == pow(3, 13, 1000)
```

**Adım 6 — Doğrula.** Program `pow(3, 13, 1000)` ile karşılaştırır. Aşağıdaki tablo, izleri elle takip ettiğimizde programın çıktısıyla birebir uyar.

```term
$ python ex1.py
3^13 mod 1000 (izli cagri):
        n=0: sonuc = 1
      n=1: yarim=1 kare=1 sonuc=3
    n=3: yarim=3 kare=9 sonuc=27
  n=6: yarim=27 kare=729 sonuc=729
n=13: yarim=729 kare=441 sonuc=323
sonuc = 323 | pow ile = 323
```

| Çağrı n | yarım = x^(n//2) mod m | kare = yarım² mod m | sonuç |
|---|---|---|---|
| 0 | — | — | 1 |
| 1 | 1 | 1 | 1 · 3 = 3 |
| 3 | 3 | 9 | 9 · 3 = 27 |
| 6 | 27 | 729 | 729 (çift) |
| 13 | 729 | 441 | 441 · 3 = 1323 → 323 |

Son satırda `729² = 531441`, `mod 1000 = 441`; tek olduğu için `441 · 3 = 1323`, `mod 1000 = 323`. Sonuç `pow` ile aynıdır.

**Bunu AI'sız yazabilir misin?** `x^n mod m`'i hem özyinelemeli hem de döngüsel (iteratif) olarak yaz; hangisinin özyinelemeye daha uygun olduğunu, hangisinin çağrı yığını kullanmadığını açıkla.

### Örnek 2 (★★): Çoğunluk elemanı: D&C ve Boyer–Moore

**Problem:** `n` elemanlı bir dizide, `n/2`'den fazla tekrar eden bir eleman varsa onu bul. Yoksa ne döndüreceğini belirt.

**Adım 1 — Anla.** Girdi bir tamsayı dizisidir; çıktı çoğunluk elemanı ya da "yok". Kenar durumlar: tek elemanlı dizi; iki eşit ya da farklı eleman.

**Adım 2 — Örnekle.** `[2, 2, 1, 1, 1, 2, 2]` dizisinde 2 dört kez geçer, `7/2 = 3,5`'ten büyüktür; çoğunluk elemanı 2'dir.

**Adım 3 — Kaba çöz.** Her elemanın kaç kez geçtiğini say. Bu `O(n²)` (her eleman için tüm diziyi tara) ya da `O(n log n)` (sırala, ortadaki elemanı al) ile yapılır.

**Adım 4 — Örüntü.** Çoğunluk elemanı varsa, diziyi ikiye böldüğünde ya sol ya sağ yarıda çoğunluktadır. Yani iki yarının adayları arasında doğru cevap vardır. Her yarının adayını özyinelemeyle bul; iki aday aynıysa onu döndür, farklıysa her ikisinin tüm aralıkta sayısını karşılaştır. Bu, `T(n) = 2T(n/2) + Θ(n)` ile `Θ(n log n)`'dir.

**Adım 5 — İyileştir.** Boyer–Moore oylaması ile tek geçişte `O(n)` ve `O(1)` bellek yeter: bir aday ve bir sayaç tut; eşleşen elemanda sayacı artır, eşleşmeyende azalt, sayaç sıfıra düşünce yeni aday al. Bu, D&C'nin birleştirme adımını bir sayaca dönüştürür. Programda iki yöntemi de çalıştırıyoruz.

```python
# ex2.py: cogunluk elemani, D&C ve Boyer-Moore
import random
from collections import Counter


def cogunluk_dc(a, lo, hi, iz=False):
    """[lo, hi) icinde bir aday dondurur; cogunluk varsa odur."""
    if hi - lo == 1:
        return a[lo]
    mid = (lo + hi) // 2
    sol = cogunluk_dc(a, lo, mid, iz)
    sag = cogunluk_dc(a, mid, hi, iz)
    if sol == sag:
        return sol
    cs = sum(1 for x in a[lo:hi] if x == sol)
    cg = sum(1 for x in a[lo:hi] if x == sag)
    aday = sol if cs > cg else sag
    if iz:
        print("[%d,%d) sol=%d sag=%d cs=%d cg=%d -> %d"
              % (lo, hi, sol, sag, cs, cg, aday))
    return aday


def boyer_moore(a):
    aday, sayac = None, 0
    for x in a:
        if sayac == 0:
            aday = x
        sayac += 1 if x == aday else -1
    return aday


```

```python
if __name__ == "__main__":
    rnd = random.Random(42)
    a = [2, 2, 1, 1, 1, 2, 2]
    print("Iz (n=7):")
    cogunluk_dc(a, 0, len(a), iz=True)
    for _ in range(300):
        n = rnd.randint(1, 30)
        b = [rnd.randint(0, 3) for _ in range(n)]
        ad = cogunluk_dc(b, 0, n)
        sayi = Counter(b).most_common(1)[0]
        if sayi[1] * 2 > n:
            assert ad == sayi[0] == boyer_moore(b)
    print("300 rastgele dizi: D&C ve Boyer-Moore cogunlugu bulur")
```

**Adım 6 — Doğrula.** Aşağıdaki tablo, programın ürettiği izi gösterir. Her satır, iki adayın farklı olduğu bir çağrıdır; aynı adaylı çağrılar programda yazdırılmaz ve son satır bunu gösterir.

```term
$ python ex2.py
Iz (n=7):
[1,3) sol=2 sag=1 cs=1 cg=1 -> 1
[0,3) sol=2 sag=1 cs=2 cg=1 -> 2
[3,7) sol=1 sag=2 cs=2 cg=2 -> 2
300 rastgele dizi: D&C ve Boyer-Moore cogunlugu bulur
```

| Aralık [lo, hi) | sol aday | sağ aday | cs | cg | seçilen |
|---|---|---|---|---|---|
| [1, 3) | 2 | 1 | 1 | 1 | 1 (eşitlikte sağ) |
| [0, 3) | 2 | 1 | 2 | 1 | 2 |
| [3, 7) | 1 | 2 | 2 | 2 | 2 (eşitlikte sağ) |
| [0, 7) | 2 | 2 | — | — | 2 (eşit adaylar, yazdırılmaz) |

Son satırda iki aday aynı olduğu için doğrudan 2 döndürülür. Programın doğrulaması, rastgele 300 dizi için sonucun gerçek çoğunluk elemanıyla (sayılması kolay) eşleştiğini kontrol eder. Çoğunluk yoksa sonucun sorumluluğu çağıranda kalır; bu yüzden doğrulamayı yalnızca çoğunluk olduğunda yaptık.

**Bunu AI'sız yazabilir misin?** Boyer–Moore'un neden çoğunluk yoksa bile bir aday döndürdüğünü ve bu adayın doğruluğunu nasıl doğrulayacağını açıkla. Bu doğrulama neden `O(n)` ek geçiş gerektirir?

### Örnek 3 (★★): 1234 × 5678 ve Karatsuba izi

**Problem:** Bölüm 19.5'teki Karatsuba'yı, iki basamaklı parçalarla (taban 100) elle izle. Girdi `x = 1234`, `y = 5678`.

**Adım 1 — Anla.** Girdi iki pozitif tam sayı; çıktı çarpımları. Kenar durum: her iki sayı 100'den küçükse doğrudan çarp (taban durum).

**Adım 2 — Örnekle.** `1234 · 5678 = 7006652` (bunu zaten biliyoruz, doğrulama için kullanacağız).

**Adım 3 — Kaba çöz.** Dört basamaklı bir çarpımı okul yöntemiyle yapmak 16 basamak çarpımı gerektirir. Bu, `n²` ile orantılıdır.

**Adım 4 — Örüntü.** `x = a1·100 + a0`, `y = b1·100 + b0`. Burada `a1 = 12`, `a0 = 34`, `b1 = 56`, `b0 = 78`. Karatsuba: `z0 = a0·b0`, `z2 = a1·b1`, `z1 = (a0+a1)(b0+b1) - z0 - z2`. Sonuç `z2·100² + z1·100 + z0`.

**Adım 5 — İyileştir.** Üç çarpım (z0, z2 ve (a0+a1)(b0+b1)) yeterlidir. Her sayı iki basamaklı olduğu için alt çarpımlar taban duruma iner.

```python
# ex3.py: 1234 x 5678 Karatsuba izi (Ornek 3)
def kar_adim(x, y, ust=True):
    if x < 100 and y < 100:
        return x * y
    m = 100                              # 10^2 ile bol
    a1, a0 = divmod(x, m)
    b1, b0 = divmod(y, m)
    z0 = kar_adim(a0, b0, False)
    z2 = kar_adim(a1, b1, False)
    z1 = kar_adim(a0 + a1, b0 + b1, False) - z0 - z2
    if ust:
        print("a1=%d a0=%d b1=%d b0=%d" % (a1, a0, b1, b0))
        print("z0=%d z1=%d z2=%d" % (z0, z1, z2))
    return z2 * m * m + z1 * m + z0


if __name__ == "__main__":
    s = kar_adim(1234, 5678)
    print("1234 * 5678 =", s, "| dogrudan =", 1234 * 5678)
    assert s == 1234 * 5678
```

**Adım 6 — Doğrula.** Program `1234 * 5678` ile karşılaştırır ve hem ara değerleri hem sonucu yazdırır.

```term
$ python ex3.py
a1=12 a0=34 b1=56 b0=78
z0=2652 z1=2840 z2=672
1234 * 5678 = 7006652 | dogrudan = 7006652
```

| Adım | Değer | Hesap |
|---|---|---|
| a1, a0 | 12, 34 | 1234 = 12·100 + 34 |
| b1, b0 | 56, 78 | 5678 = 56·100 + 78 |
| z0 | 2652 | 34 · 78 |
| z2 | 672 | 12 · 56 |
| z1 | 2840 | (46)(134) - 2652 - 672 = 6164 - 3324 |
| sonuç | 7006652 | 672·10^4 + 2840·10² + 2652 |

Son satır: `6720000 + 284000 + 2652 = 7006652`. Dört çarpım yerine üç çarpım yaptık; bu küçük örnekte kazanç yok gibi görünebilir, ama özyineleme derinleştikçe üç çarpımın üssü fark yaratır (Bölüm 19.5).

**Bunu AI'sız yazabilir misin?** Aynı çarpımı taban 10 yerine taban 2 ile (ikili basamaklarla) yap. Hangi bölme noktasını seçtiğini ve neden `m = n/2`'nin güvenli olduğunu açıkla.

### Örnek 4 (★★★): En yakın nokta çifti: ağaç izi

**Problem:** Sekiz noktanın en yakın çiftini D&C ile bul. Noktalar: `(1,7), (4,2), (6,9), (8,4), (9,1), (12,8), (13,3), (15,6)`.

**Adım 1 — Anla.** Girdi sekiz noktadır; çıktı en küçük uzaklıklı çift ve uzaklık. Kenar durumlar: aynı noktalar (uzaklık 0), tek nokta (çift yok), birbirine çok yakın noktalar bölme çizgisinin iki yanında.

**Adım 2 — Örnekle.** Kaba kuvvetle 28 çift vardır. Bu örneğin cevabı `(8,4)` ile `(9,1)`'dir, uzaklık `√10 ≈ 3,162`.

**Adım 3 — Kaba çöz.** Her çifti hesapla ve en küçüğünü seç. Bu `O(n²)`'dir.

**Adım 4 — Örüntü.** Noktaları x'e göre sırala; ortadan böl. Sol ve sağda özyinelemeyle `dL` ve `dR` bul; `δ = min(dL, dR)`. Bölme çizgisine `δ`'dan daha yakın noktalar şeridi oluşturur; şeritte y'ye göre sıralı en fazla 7 aday karşılaştırılır.

**Adım 5 — İyileştir.** Y-sıralı listeleri özyineleme sırasında birleştir; böylece her seviye `O(n)` olur ve toplam `O(n log n)`'dir. Program, her çağrıda `n`, `xm`, `dL`, `dR`, `δ` ve şerit boyunu yazdırır.

```python
# ex4.py: en yakin nokta cifti, bol-fethet izi (Ornek 4)
import math


def mesafe(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def kaba(P):
    en = (math.inf, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = mesafe(P[i], P[j])
            if d < en[0]:
                en = (d, (P[i], P[j]))
    return en


def iz(px, derin=0):
    n = len(px)
    pad = "  " * derin
    if n <= 3:
        d, c = kaba(px)
        print(pad + "taban n=%d d=%.3f" % (n, d))
        return d, c, sorted(px, key=lambda p: p[1])
    mid = n // 2
    xm = px[mid][0]
    dl, cl, yl = iz(px[:mid], derin + 1)
    dr, cr, yr = iz(px[mid:], derin + 1)
    d, c = (dl, cl) if dl <= dr else (dr, cr)
    y = sorted(yl + yr, key=lambda p: p[1])
    serit = [p for p in y if abs(p[0] - xm) < d]
    once = d
    for i, p in enumerate(serit):
        for q in serit[i + 1:]:
            if q[1] - p[1] >= d:
                break
            dd = mesafe(p, q)
            if dd < d:
                d, c = dd, (p, q)
    print(pad + "n=%d xm=%d dL=%.3f dR=%.3f delta=%.3f serit=%d"
          % (n, xm, dl, dr, once, len(serit)))
    return d, c, y


```

```python
if __name__ == "__main__":
    P = [(1, 7), (4, 2), (6, 9), (8, 4), (9, 1), (12, 8), (13, 3),
         (15, 6)]
    px = sorted(P)
    d, c, _ = iz(px)
    print("en yakin:", c, "mesafe = %.3f" % d)
    assert abs(d - kaba(P)[0]) < 1e-12
```

**Adım 6 — Doğrula.** Programın izi aşağıdaki tabloya dönüşür. Her satır bir özyineleme çağrısıdır; `Çıkan d` sütunu çağrının döndürdüğü en küçük uzaklıktır.

```term
$ python ex4.py
    taban n=2 d=5.831
    taban n=2 d=5.385
  n=4 xm=6 dL=5.831 dR=5.385 delta=5.385 serit=4
    taban n=2 d=7.616
    taban n=2 d=3.606
  n=4 xm=13 dL=7.616 dR=3.606 delta=3.606 serit=3
n=8 xm=9 dL=4.472 dR=3.606 delta=3.606 serit=4
en yakin: ((9, 1), (8, 4)) mesafe = 3.162
```

| Çağrı | n | xm | dL | dR | δ | Şerit | Çıkan d |
|---|---|---|---|---|---|---|---|
| (1,7),(4,2) | 2 | taban | — | — | — | — | 5,831 |
| (6,9),(8,4) | 2 | taban | — | — | — | — | 5,385 |
| sol yarı | 4 | 6 | 5,831 | 5,385 | 5,385 | 4 | 4,472 |
| (9,1),(12,8) | 2 | taban | — | — | — | — | 7,616 |
| (13,3),(15,6) | 2 | taban | — | — | — | — | 3,606 |
| sağ yarı | 4 | 13 | 7,616 | 3,606 | 3,606 | 3 | 3,606 |
| tüm küme | 8 | 9 | 4,472 | 3,606 | 3,606 | 4 | 3,162 |

Son satırda şerit, `x ∈ (5,394; 12,606)` aralığındaki dört noktayı içerir: `(6,9)`, `(8,4)`, `(9,1)`, `(12,8)`. Y'ye göre sıralı şeritte `(9,1)` ile `(8,4)` arasındaki uzaklık `√10 ≈ 3,162` ve `δ = 3,606`'dan küçüktür; bu çifti bulur. Kaba kuvvetle eşleşme programda `assert` ile kontrol edildi.

**Bunu AI'sız yazabilir misin?** Şerit adımında neden y-sıralı karşılaştırma kullanıldığını ve `q[y] - p[y] >= δ` koşulunda döngüden neden çıkabildiğini açıkla. Bu koşul yanlış olsaydı hangi çift kaçardı?


## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. D&C'nin asıl eğitimi, bölme ve birleştirme sınırlarını kendi elinle kurmak ve kendi hatanı bulmaktır. Bir aracın yazdığı kod doğru görünse bile, taban durumları ve kenar durumları (boş dizi, tek eleman, eşit değerler, sınır indeksleri) sen test etmedikçe bilmiyorsun.
:::

### Proje 1 (★★): Kendi büyük tamsayı çarpım kütüphanen

**Amaç:** Bölüm 19.5'teki Karatsuba'yı kendi veri yapınla yeniden yazmak; okul yöntemi ile karşılaştırıp kesişme noktasını (eşiği) kendi makinende ölçmek.

**Yapılacak / Beklenen davranış:**

1. Sayıları taban `10^4` (ya da `2^16`) basamaklı bir liste olarak tut; en düşük basamak önde olsun ve sondaki sıfırları temizle.
2. Toplama, çıkarma ve okul yöntemi çarpımını yaz. Negatif sayılar bu projede yok; ama çıkarmada sonucun negatif olmadığını bir `assert` ile koru.
3. Karatsuba'yı yaz. Bölme noktasını `max(len(a), len(b)) // 2` seç. Kısa girdilerde okul yöntemine dön.
4. 500 rastgele çift için (tohum `42`) sonucun Python'un `*` operatörüyle aynı olduğunu kontrol et.
5. Eşik değerini 8, 16, 32, 64, 128 için dene; her biri için 1024 ve 2048 basamaklı sayılarda süreyi ölç. Kesişme noktası ne?

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Önce okul yöntemini ve testlerini tamamla; Karatsuba'yı ancak o zaman yaz. Üç özyinelemeli çağrının sonuçlarını basamak kaydırarak birleştirmek için bir `kaydir(a, k)` yardımcısı işine yarar. Negatif sonuç çıkmasın diye `z1 = (a0+a1)(b0+b1) - z0 - z2` çıkarmasını bu sırayla yap. Zamanlamayı `time.perf_counter()` ile ölç ve her ölçümü birkaç kez tekrar et.

**Başarı kriterleri:**

- 500 rastgele çiftte sonuçlar Python'un `*` ile tamamen aynıdır.
- Boş ya da tek basamaklı girdilerde ve tüm basamakları `0` olan sayıda doğru sonuç döner (`0`).
- Karatsuba ile okul yöntemi arasındaki kesişme noktası, kendi makinende ölçülmüş olarak bir tabloda raporlanır; raporda kullandığın tohum ve eşik değerleri yazılır.
- Büyüme eğrisinin eğimi (log-log) okul yöntemi için yaklaşık 2, Karatsuba için 1,5 ile 1,8 arasında olur; bu aralık dışına çıkarsa nedenini açıkla.

### Proje 2 (★★★): EV Dashboard sensör sinyalinde FFT ile konvolüsyon

**Amaç:** EV Dashboard'daki STM32 sensör akışına benzeyen bir sinyale, uzun bir kayan ortalama filtresini FFT tabanlı konvolüsyonla uygulamak ve sonucu doğrudan konvolüsyonla karşılaştırmak.

**Yapılacak / Beklenen davranış:**

1. Tohum `42` ile `n = 4096` örnekli bir sinyal üret: taşıyıcı bir sinüs, bir miktar gürültü ve birkaç ani sıçrama. Sinyalin ne olduğunu bir grafikle göster.
2. Uzunluğu `L = 64` olan bir kayan ortalama çekirdeği (her katsayı `1/L`) tanımla.
3. Sonucu iki yolla hesapla: (a) doğrudan konvolüsyon, `O(nL)`; (b) Bölüm 19.11'deki `carp_fft` benzeri bir FFT konvolüsyonu. İki sonucun en büyük mutlak farkını raporla.
4. Parçalı (overlap-add) yaklaşımı dene: sinyali `512` örnekli bloklara böl, her bloğu FFT ile filtrele ve sonuçları üst üste ekleyerek birleştir. Bu, uzun akışlarda gerçek bir sistemde nasıl çalışır?
5. Her iki yöntemin süresini `n` ve `L` değiştikçe ölç ve hangisinin ne zaman daha hızlı olduğunu tabloya dök.

**Önerilen yaklaşım (ipucu):** Konvolüsyonun boyutu `n + L - 1`'dir; FFT boyutunu bu değerden büyük en küçük 2'nin kuvveti seç. Sıfır dolgu (zero padding) yapmazsan dairesel konvolüsyon elde edersin ve uçlar bozulur. Parçalı yöntemde bloklar arası örtüşme `L - 1` örnektir; bunu nasıl yönettiğini bir çizimle açıkla. Kayan nokta hatasını ölçmek için iki yöntemin farkını her zaman raporla.

**Başarı kriterleri:**

- Doğrudan ve FFT konvolüsyonunun farkı `10^-9`'un altındadır (katsayılar ondalık olduğu için yuvarlama yapma).
- Parçalı yöntemin çıktısı tek seferde yapılan FFT ile `10^-9` içinde eşleşir ve sinyalin başında ve sonunda bloklar arası bozulma yoktur.
- Süre tablosu en az üç farklı `n` ve iki farklı `L` için ölçülmüştür; hangi durumda FFT'nin kazandığı tartışılmıştır.
- Kodun her fonksiyonu için bir test vardır; testler tohumla tekrarlanabilir.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün, sonra kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ `n` elemanlı bir dizinin toplamını D&C ile hesapla ve bağıntıyı yaz. Bu problemde birleştirme adımı neden `O(1)`'dir? (Mülakat)
2. ★ Bir dizide en büyük ve en küçük elemanı aynı anda bul. Karşılaştırma sayısını D&C ile azaltabilir misin? `3n/2 - 2` sınırını açıkla. (Mülakat)
3. ★ İkili arama (Bölüm 14.2) hangi D&C şablonuna uyar? Bölme, çözme ve birleştirme adımlarını ayrı ayrı yaz.
4. ★★ `n` yıldız (tüm noktalar tek bir çizgide) için en yakın nokta çiftini bulan D&C'nin şerit adımı neye dönüşür? Bu özel durumda sıralama maliyetini nasıl azaltırsın?
5. ★★ `x^n` hesabı için tabanı `k` tabanına (üçlü ya da dörtlü) bölen bir yöntem düşün. Çarpım sayısı nasıl değişir? İkili yöntemle karşılaştır. (Mülakat)
6. ★★ Quickselect'in ortalama süresi `O(n)`'dir. Pivotu her zaman medyan seçen ideal bir quickselect'in kötü durumda ne olduğunu bağıntıyla yaz ve çöz.
7. ★★ Bir dizide ters çevrim sayısını (Bölüm 13'te gördün) birleştirme sıralamasıyla bulmanın birleştirme adımını ayrıca açıkla. Neden her seviyede toplam `O(n)` iş yapılır?
8. ★★ Bir dizide "iki toplamı hedefe eşit olan" bir çift var mı? Sırala, sonra iki işaretçi kullan. Bu bir D&C mi, yoksa tek geçişli bir yöntem mi? Neden? (Mülakat)
9. ★★ Bir polinomu `p(x) = E(x²) + x·O(x²)` biçiminde çift ve tek kuvvetlere ayıran bir D&C yaz. `n` çift ve `ω = e^(-2πi/n)` iken `ω^(k+n/2) = -ω^k` eşitliğini kullanarak bu ayrımın FFT'nin kelebek adımını nasıl ürettiğini açıkla.
10. ★★★ `T(n) = 3T(n/3) + n` bağıntısını Master Teoremi ile çöz. Sonra `T(n) = 2T(n/2) + n / log n` için Master'ın neden uygulanmadığını açıkla ve özyineleme ağacıyla yaklaşık sonucu bul. (Mülakat)
11. ★★★ Bir `n × n` matris için en büyük alt matris toplamını D&C ile çöz (üç durum: sadece üst yarı, sadece alt yarı, ortayı kesen). Bağıntıyı yaz ve sonucu `O(n³)` kaba kuvvetle karşılaştır. (Mülakat)
12. ★★★ Bir dizide "sayılar sıralı değilken inversiyon sayısı" için Bölüm 13'teki yöntemi tekrar ele al: birleştirme sırasında sağdaki bir elemanın solda kaç büyük eleman karşıladığını nasıl sayarsın? Kodunu yaz ve kaba kuvvetle test et.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10'un `Objects/longobject.c` dosyasındaki `k_mul` fonksiyonu, yani Python'un büyük tamsayı çarpımının Karatsuba gerçeklemesi. Kaynak `https://raw.githubusercontent.com/python/cpython/v3.12.10/Objects/longobject.c` adresinden indirildi; `KARATSUBA_CUTOFF` tanımı dosyanın 74. satırında (`#define KARATSUBA_CUTOFF 70`) bulunur. Aşağıdaki kesit, `k_mul` fonksiyonunun imzasından, eşik kontrolünden, ayırma (split) adımından ve üçüncü çarpımdan oluşur. Atlanan satır aralıkları yorum satırı olarak işaretlenmiştir; bu bir **sadeleştirilmiş kesit**tir. Kod satırlarının hiçbiri değiştirilmedi.

```c
static PyLongObject *
k_mul(PyLongObject *a, PyLongObject *b)
{
    /* ... 3711-3742: degisken bildirimleri atlandi ... */
    /* Use gradeschool math when either number is too small. */
    i = a == b ? KARATSUBA_SQUARE_CUTOFF : KARATSUBA_CUTOFF;
    if (asize <= i) {
        if (asize == 0)
            return (PyLongObject *)PyLong_FromLong(0);
        else
            return x_mul(a, b);
    }

    /* ... 3752-3757: lopsided yorum atlandi ... */
    if (2 * asize <= bsize)
        return k_lopsided_mul(a, b);

    /* Split a & b into hi & lo pieces. */
    shift = bsize >> 1;
    if (kmul_split(a, shift, &ah, &al) < 0) goto fail;
    /* ... 3764-3796: ah, al, bh, bl ayrintilari atlandi ... */
    if ((t1 = k_mul(ah, bh)) == NULL) goto fail;
    /* ... 3798-3832: sonucu doldurma ve cikarma atlandi ... */
    /* 6. t3 <- (ah+al)(bh+bl), and add into result. */
    if ((t1 = x_add(ah, al)) == NULL) goto fail;
    /* ... 3835-3849: (bh+bl) atlandi ... */
    t3 = k_mul(t1, t2);
    /* ... 3851-: t3'un eklenmesi ve geri kalan kisim atlandi ... */
```

**Sorular — cevaplamadan geçme:**

1. `i = a == b ? KARATSUBA_SQUARE_CUTOFF : KARATSUBA_CUTOFF;` satırında eşik, iki sayı aynı nesne olduğunda neden iki katına çıkıyor? Kesitte atlanan satırlarda `a == b` dalının ikinci bölme işlemini neden yapmadığını kaynakta bulup açıkla.
2. `if (2 * asize <= bsize) return k_lopsided_mul(a, b);` dalı, bir sayı diğerinden çok kısa olduğunda ne yapar? Bu durumda ayrı bir Karatsuba bölmesi neden verimsiz olurdu? (Kesitteki atlanan yorum bu konuyu açıklıyor; kendi kelimelerinle yaz.)
3. `shift = bsize >> 1;` satırında bölme noktası `bsize`'a göre seçilir. Kesitin üst kısmındaki değiş tokuşa bakarak `asize <= bsize` garantisinin bu seçimi neden güvenli kıldığını açıkla.
4. `if ((t1 = k_mul(ah, bh)) == NULL) goto fail;` satırı `ah*bh`'yi hesaplar. Kesitte gördüğün `(ah+al)(bh+bl)` çarpımı kaçıncı adımdır ve neden üç çarpım yalnızca bu sırada gerçekleşir?
5. `t3 = k_mul(t1, t2);` satırı Karatsuba'nın `z1` çarpımına karşılık gelir. Kendi Python kodundaki (`karatsuba.py`) `z1` satırıyla karşılaştır: hangi değişkenler hangi rolü oynuyor?
6. (Mülakat) Bu kesitte `if (asize == 0) return ...PyLong_FromLong(0);` satırı neden gereklidir? Bu satır olmasa hangi durumda sorun çıkardı?

## Bölüm Özeti

Bu bölümde böl ve fethet stratejisini bir şablon, bir maliyet modeli ve bir karar aracı olarak öğrendik:

- D&C üç adımdan oluşur: böl, çöz (özyinele), birleştir. Maliyet genellikle birleştirme adımında saklanır; bu, özyineleme ağacının her seviyesinin toplamını belirler.
- Master Teoremi (Bölüm 12.9) bağıntıların çoğunu çözer, ama `n log n` gibi bağıntılarda uygulanamaz; bu durumda özyineleme ağacı (`Θ(n log² n)` örneği) ile çözülür.
- D&C, DP ve greedy'yi ayıran soru, alt problemlerin bağımsız mı, tekrar eden mi, yoksa yerel seçim ile çözülebilir mi olmasıdır (Bölüm 19.3).
- Hızlı üs ve matris üssü ile Fibonacci `O(log n)` zamanda çözülür; mod alma sayıları sabit boyutta tutar. İki bağımsız yöntemin (matris ve fast doubling) karşılaştırılması güçlü bir doğrulama yoludur.
- Karatsuba, üç özyinelemeli çarpımla `Θ(n^1,585)` verir; CPython bunu `KARATSUBA_CUTOFF = 70` (30 bitlik dahili basamak) eşiğiyle kullanır. Strassen, yedi çarpımla `Θ(n^2,807)` verir; küçük bloklarda eşiğin ayarı kritiktir.
- En yakın nokta çifti `O(n log n)` zamanda çözülür; şeridin 8 kareli sayım argümanı, her noktanın yalnızca sabit sayıda komşuyla karşılaştırılmasını garanti eder.
- Maksimum alt dizi toplamı D&C ile `O(n log n)`, Kadane ile `O(n)`'dir; ikisi de aynı değeri verir. Kadane bir DP'dir.
- Medyanların medyanı pivot seçimiyle seçimi `O(n)` kötü durumda garanti eder; bağıntı Master'a uymadığı için yerine koyma ile çözülür.
- FFT, polinom çarpımını ve konvolüsyonu `O(n log n)` zamanda yapar; kelebek diyagramı ve birim kökler temel yapı taşlarıdır. DSP ve Bölüm 52'nin temelidir.

### Kısım IV'ün kapanışı: Bölüm 12'den 19'a

Kısım IV'ü tek bir soruyla özetleyebiliriz: bir algoritmanın süresini nasıl tahmin eder ve bu tahmini nasıl doğrularsın? Bölüm 12 bu soruya dilin ve ölçümün temelini verdi (Big-O, amortize analiz, Master Teoremi). Bölüm 13 sıralamayı, Bölüm 14 aramayı, Bölüm 15 özyinelemeyi öğretti; Bölüm 16 aynı alt problemleri tekrar etmemeyi (DP), Bölüm 17 grafları, Bölüm 18 yerel seçimleri, Bölüm 19 bağımsız alt problemleri bölmeyi anlattı. Her bölümde iki şeyi tekrar et: önce teoriyi kendi kelimelerinle yaz, sonra kaba kuvvet ile küçük girdilerde doğrula.

Mülakat hazırlığı için bu kısmı tekrar ederken şu sırayı izleyebilirsin: önce her bölümün "Bölüm Özeti" maddelerini kapat ve maddeleri kendin açıkla; sonra her bölümün Ek Alıştırmalarından ★★ ve üzerini cevapsız çöz; son olarak her bölümde bir programı boş bir dosyada, tohumlu rastgele testlerle yeniden yaz. Bu üç adım, kitabın hedeflediği "yapay zekâ olmadan çözebilme" becerisini doğrudan çalıştırır.

**Sonraki bölümde:** Bölüm 20 (OOP Temelleri) ile Kısım V — OOP ve Yazılım Tasarımı başlıyor. Şimdiye kadar algoritmaları fonksiyonlarla yazdık; Kısım V'te verinin ve davranışın birlikte nasıl paketleneceğini, C++ ve Python'da sınıflar, kalıtım ve çok biçimlilik ile göreceksin. Bölüm 19'daki karatsuba.py ile FFT kodlarının neden birbirinden bağımsız fonksiyonlar olarak yazıldığını, OOP'de bir arayüz (interface) ile sarmalamanın neye benzeyeceğini bu kısımda tartışacağız.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir problemin D&C ile çözülebilmesi için hangi özellik gerekir? Alt problemlerin bağımsız olması neden önemlidir; bağımsız olmadığında ne olur?
2. `T(n) = 2T(n/2) + n log n` bağıntısı Master Teoremi'ne neden uymaz? Özyineleme ağacıyla hangi sonuca ulaşırsın ve bu sonucu nasıl doğrularsın?
3. Karatsuba'nın üç çarpımı, okul yönteminin dört çarpımından neden daha az iş yapar? Eşik değeri neden sıfır olamaz?
4. En yakın nokta çiftinde şeritteki her noktanın yalnızca sabit sayıda komşuyla karşılaştırılmasını neden garanti edebilirsin? Bu argümanda hangi gözlem kilit rol oynar?
5. Maksimum alt dizi toplamı için D&C ile Kadane arasında hangisini seçersin ve neden? Kadane'nin neden bir DP olduğunu açıkla.
6. Medyanların medyanı algoritması pivot seçimini neden iyileştirir? Pivotun en az yüzde 30 kadar her iki yönde dengeli olduğunu bir sayımla göster.
7. FFT ile polinom çarpımında `n` iki katına çıktığında süre neden tam olarak dört kat artmaz? Burada `n log n` büyümesini nasıl okursun?
8. Strassen algoritması matris çarpımını hızlandırırken neden her zaman daha hızlı değildir? Eşiği nasıl seçerdin ve bunu hangi ölçümle doğrulardın?
:::
