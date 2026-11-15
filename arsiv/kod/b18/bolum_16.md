%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 16
%% baslik: Dynamic Programming

## Giriş: Aynı işi ikinci kez yapmamak

Bölüm 15'te fib ağacında aynı alt problemin defalarca çözüldüğünü gördük. `fib(3)` ağacın birden fazla yerinde çıkıyor, her seferinde sıfırdan hesaplanıyor. Bu bölümde o tekrarı bir kez yapıp sonucu saklamayı öğreneceğiz. Bu fikrin adı dinamik programlamadır (dynamic programming, DP). Terimi Richard Bellman bulmuştur; ad bir programlama tekniğinden çok, çözümü aşamalara bölme biçimini anlatır.

DP, Bölüm 12'de gördüğümüz karmaşıklık analizinin en kullanışlı uygulamalarından biridir. Üstel süren bir özyinelemeyi, durum sayısı ile geçiş maliyetinin çarpımı kadar sürecek bir hesaba çevirir. Fibonacci'de bu, `2^n`'den `n`'e düşmek demektir. Bölüm 12'deki Big-O dilini burada somut bir karara dönüştürüyoruz: hangi alt problemler gerçekten hesaplanmalı, hangileri saklanmalı?

Mülakatta DP soruları çoğu zaman "en az", "en çok", "kaç yol" ya da "bu seçimlerden hangisi en iyisi" kalıbıyla gelir. Adayın ilk tepkisi genellikle kaba kuvvetle başlamaktır. DP'yi bilmek, o kaba kuvvetin neden aynı şeyi tekrar hesapladığını görüp onu tabloya dönüştürebilmek demektir. Savunma sanayiinde de benzer problemler var: bir İHA'nın rotasında yakıtı en az tutan yolu bulmak, bir sensör kaydını bir referans dizisine hizalamak ya da bir sinyal modelinde en olası durum dizisini çıkarmak DP ile çözülür. Bölüm 62'deki HMM ve Viterbi algoritması bu bölümün doğrudan devamıdır.

Mert'in projelerine de yakın bir bağlantı var. Bu bölümün sonunda kendi `diff` aracını yazacaksın; bu araç iki metin dosyasının en uzun ortak altdizisini bulmak için LCS'i kullanır. Mert Studio Code'daki Türkçe parser'a eklenebilecek bir yazım denetimi ise edit distance ile yapılır. EV Dashboard'daki batarya enerji bütçesi de bir sırt çantası problemidir.

::: not
Bu bölümdeki her program Python 3.12.10 ile çalıştırıldı. C programları WSL'de gcc 13.3 ile `-std=c11` ve `-Wall -Wextra` uyarılarıyla derlendi; bellek hataları için `-fsanitize=address,undefined` ile de denendi. Kodlardaki rastgele örnekler `random.Random(42)` tohumuyla üretildi, böylece sayılar sizde de aynı çıkar. Windows'ta `long` 4 bayttır (LLP64), bu yüzden C kodunda tamsayı boyutlarını `long long` ve `size_t` ile açıkça seçtik.
:::

## 16.1 İki koşul: örtüşen alt problemler ve optimal alt yapı

Bir problem DP ile çözülebilmek için iki koşulu birlikte sağlamalıdır. Birincisi **örtüşen alt problemler** (overlapping subproblems): aynı alt problem, çözümün farklı dallarında tekrar tekrar ortaya çıkar. İkincisi **optimal alt yapı** (optimal substructure): büyük problemin en iyi çözümü, alt problemlerin en iyi çözümlerinden kurulabilir.

Birinci koşulu görmek için Bölüm 15'teki ağaca tekrar bakalım. Aşağıdaki şekil `fib(5)` çağrısının ağacını gösteriyor. Düğümlerdeki sayı `n`'dir; kırmızı düğümler birden çok kez çağrılır.

![Şekil 16.1: fib(5) özyineleme ağacı. Kırmızı düğümler (fib(3) ve fib(2)) birden çok kez hesaplanır; ağaçta toplam 15 çağrı vardır, ama farklı alt problem sayısı yalnızca 6'dır.](gorseller/b16_fib_agac.png)

Bu ağaç yanlış bir şey yapmıyor; her çağrı doğru cevabı döndürüyor. Sorun verimde. Ağacı büyütmek, aynı düğümü her seferinde yeniden hesaplamak demek. Eğer her alt problemi yalnızca bir kez hesaplar ve sonucunu saklarsak, `n = 5` için 6 hesap yeter. Bunu Bölüm 16.3'te yapacağız.

Şimdi ikinci koşulu ele alalım. Optimal alt yapıya sahip bir problemde şu kural geçerlidir: büyük problemin en iyisini, alt problemlerin en iyilerini birleştirerek bulabilirsin. En kısa yol problemi bu koşulu sağlar. A'dan C'ye giden en kısa yol bir B noktasından geçiyorsa, A'dan B'ye giden parça da mutlaka A-B arasının en kısa yoludur. Aksi halde o parçayı değiştirip daha kısa bir yol bulurduk.

En uzun basit yol problemi ise bu koşulu sağlamaz. "Basit" yol, hiçbir köşeyi iki kez kullanmayan yoldur. Üç köşeli bir üçgen düşünelim: köşeler `s`, `v`, `t` ve her biri diğer ikisine bağlı. `s`'den `t`'ye en uzun basit yol `s - v - t`'dir; uzunluğu 2'dir. Şimdi bu yolu ortadaki `v` köşesinden bölelim. `s`'den `v`'ye en uzun basit yol `s - t - v`'dir (uzunluk 2) ve `v`'den `t`'ye en uzun basit yol `v - s - t`'dir (uzunluk 2). İki parçayı birleştirirsek `s - t - v - s - t` elde ederiz; bu yol `s`, `t` köşelerini iki kez kullanır, yani basit değildir. Alt problemlerin en iyileri birleşmiyor, çünkü parçalar birbirinin köşelerini kullanıyor.

Bu yüzden DP'nin uygulanabilmesi için alt problemlerin en iyi çözümlerinin birleşip geçerli bir çözüm verebilmesi gerekir. En uzun basit yol problemi genel grafta NP-zordur ve bilinen kesin çözümler üstel zaman tutar; yani DP'nin "tablo" fikri burada işe yaramaz. Koşul sağlanmadığında tabloya dökmek yanlış sonuç verir; önce koşulu kanıtla, sonra tabloyu kur.

## 16.2 DP tasarım protokolü: altı soru

Her DP çözümü, sırası değişmeyen altı soruya cevap verir. Bu sorular bir hile değil, bir düşünme sırasıdır. Çoğu hata, bu sıradan birini atlamaktan çıkar.

| Adım | Soru | Merdiven örneği (1 ya da 2 basamak) |
|---|---|---|
| 1. Durum | Hangi sayı, cevabın tamamını özetler? | `dp[i]`: `i`. basamağa çıkmanın yol sayısı |
| 2. Geçiş | `dp[i]`'yi daha küçük durumlardan nasıl kurarsın? | `dp[i] = dp[i-1] + dp[i-2]` |
| 3. Taban | En küçük durumlar nedir, değerleri ne? | `dp[0] = 1`, `dp[1] = 1` |
| 4. Sıra | Durumlar hangi sırayla hesaplanmalı? | `i` = 2'den `n`'ye, artan |
| 5. Cevap | Cevap tablonun neresinde? | `dp[n]` |
| 6. Maliyet | Durum sayısı × geçiş maliyeti nedir? | `n` durum × 2 geçiş = `O(n)` |

İlk adımın en önemli olduğunu vurgulamak gerekir. Durumu bir cümleyle tanımlayamıyorsan, tabloda neyi sakladığını bilmiyorsun demektir. "`dp[i]`, `i`. basamağa çıkmanın yol sayısıdır" cümlesi, sonraki her adımın anlamını belirler. Bu cümleyi yazmadan kod yazmaya başlamak, DP'de en sık yapılan hatadır.

İkinci adım, durumu alt durumlara bağlayan bağıntıdır. Merdivende son adım ya 1 ya da 2 basamaklıktır. Son adım 1 basamaklıksa `i-1`'e kadar olan yollar bir kez daha sayılır; son adım 2 basamaklıksa `i-2`'ye kadar olan yollar. Toplam `dp[i-1] + dp[i-2]`'dir. Bu bağıntı Fibonacci dizisiyle aynıdır; Bölüm 16.6'da bunun sebebini göreceğiz.

Üçüncü ve dördüncü adımlar birlikte düşünülmelidir. Bağıntı `dp[i]` için `dp[i-1]` ve `dp[i-2]`'ye ihtiyaç duyuyorsa, bu değerler `dp[i]`'den önce hesaplanmalıdır. Taban durumlar, bağıntının dayandığı başlangıç değerleridir. Yanlış taban durum, bütün tabloyu yanlış yapar; bu yüzden Bölüm 16.6'daki sayma problemlerinde taban durumların anlamını ayrıca açıklayacağız.

Beşinci adımda cevabın nerede olduğunu bilmek gerekir: son hücrede mi, tablonun en büyük değerinde mi, yoksa bir satırın içinde mi? En uzun artan altdizi (LIS) bunun iyi bir örneğidir. `dp[i]`, `a[i]`'de biten en uzun artan altdizinin uzunluğu olsun. Dizinin sonu her zaman en uzun altdizinin sonu değildir, çünkü son eleman küçük olabilir. Cevap bu yüzden `dp[n-1]` değil, tüm `dp` değerlerinin en büyüğüdür. Altıncı adımda maliyeti ölçmek, algoritmanın gerçekten pratik olup olmadığını söyler. Durum sayısı çoğu zaman tablonun boyutuna eşittir; geçiş maliyeti ise bağıntıdaki `min`, `max` ya da toplamın kaç terimli olduğudur.

Bu protokol sayma ve en iyileme problemlerinde aynıdır. Fark yalnızca geçişte ortaya çıkar: sayma problemlerinde geçiş toplamdır, en iyileme problemlerinde `min` ya da `max`. Bölüm 16.6'da bu farkı para bozma problemiyle gösteriyoruz.

## 16.3 Memoization ve tabulation: üstten alta mı, alttan üste mi?

Tekrar eden alt problemleri bir kez hesaplamanın iki yolu vardır. **Memoization** (not alma, ezberleme) üstten alta çalışır: özyinelemeli fonksiyon bir alt problemi ilk kez çözdüğünde sonucu bir önbelleğe yazar, sonraki çağrılarda hesap yapmadan döndürür. **Tabulation** (tablo doldurma) alttan üste çalışır: taban durumlardan başlayıp tabloyu bir döngüyle sırayla doldurur, özyineleme kullanmaz.

İki yöntem aynı sonucu verir; farkı dört boyutta görmek önemlidir. Önce kavramı tek bir noktada gösterelim. Aşağıdaki şekil, memo ile `fib(5)`'in alt problem bağımlılıklarını gösteriyor. Her düğüm tek bir kez hesaplanır; ok, bir düğümün hangi düğüme ihtiyaç duyduğunu gösterir.

![Şekil 16.2: Memo'nun alt problem DAG'ı. fib(n), fib(n-1) ve fib(n-2) değerlerine ihtiyaç duyar; her düğüm bir kez hesaplanır. Ağaçtaki 15 çağrı yerine 6 hesap yapılır.](gorseller/b16_fib_dag.png)

DAG, yönlü çevrimsiz graf (directed acyclic graph) demektir. Burada "çevrimsiz" önemlidir: bir alt problem kendisine bağlı olamaz, yoksa tanımsız bir hesap olurdu. DP'nin her çözümünde bağımlılıklar bu şekilde bir DAG oluşturur; hesaplama sırası, DAG'ın topolojik sıralamasıdır. Bölüm 17'de topolojik sıralamayı grafların içinde ayrıntılı göreceğiz.

Aşağıdaki program üç yöntemi yan yana koyar: naif özyineleme, memo ve tablo. Program her üç yöntemin de aynı değeri verdiğini `assert` ile doğrular; ardından çağrı sayılarını yazdırır.

Kodun ilk yarısı üç fonksiyonu tanımlar. `fib_memo`'nun üstündeki `@functools.cache` süsleyicisi (decorator), Python'un standart kütüphanesindeki bir önbellektir; Python 3.9'dan beri bulunur ve `lru_cache(maxsize=None)` ile aynı davranışa sahiptir. Önbelleğe yazılan her sonuç bir daha hesaplanmaz; bu yüzden fonksiyonun gövdesi her `n` için bir kez çalışır.

```python
# fib_olcum.py: naif, memo ve tablo; cagri sayilari
import functools
import sys

sayac = {"naif": 0, "memo": 0}


def fib_naif(n):
    sayac["naif"] += 1
    if n < 2:
        return n
    return fib_naif(n - 1) + fib_naif(n - 2)


@functools.cache
def fib_memo(n):
    sayac["memo"] += 1           # yalnizca gercek hesapta artar
    if n < 2:
        return n
    return fib_memo(n - 1) + fib_memo(n - 2)


def fib_tablo(n):
    t = [0, 1] + [0] * max(0, n - 1)
    for i in range(2, n + 1):
        t[i] = t[i - 1] + t[i - 2]
    return t[n]

```

Programın ikinci yarısı ölçümleri yapar. `sayac` sözlüğü, naif fonksiyonun her çağrısında, memo fonksiyonunun ise yalnızca gerçek hesapta arttırılır. Tablo sürümünde bir sayaç yoktur; döngü zaten `n` adımdır.

```python

def main():
    print("Python", sys.version.split()[0])
    for n in (10, 20, 30):
        sayac["naif"] = sayac["memo"] = 0
        fib_memo.cache_clear()
        a = fib_naif(n)
        b = fib_memo(n)
        c = fib_tablo(n)
        assert a == b == c
        print(f"n={n:2d} fib={a:>7d} naif_cagri={sayac['naif']:>8d}"
              f" memo_hesap={sayac['memo']:>3d}")
    # Yigin derinligi: memo n kadar ic ice cagri yapar
    fib_memo.cache_clear()
    for n in (900, 1200):
        try:
            fib_memo(n)
            print(f"memo n={n}: tamam")
        except RecursionError:
            print(f"memo n={n}: RecursionError")
        fib_memo.cache_clear()
    print("tablo n=1200 basamak:", len(str(fib_tablo(1200))))
    print("recursion limit:", sys.getrecursionlimit())


if __name__ == "__main__":
    main()
```

Programı çalıştırdık. Çıktıdaki `naif_cagri` ile `memo_hesap` sütunlarını karşılaştır:

```term
$ python fib_olcum.py
Python 3.12.10
n=10 fib=     55 naif_cagri=     177 memo_hesap= 11
n=20 fib=   6765 naif_cagri=   21891 memo_hesap= 21
n=30 fib= 832040 naif_cagri= 2692537 memo_hesap= 31
memo n=900: tamam
memo n=1200: RecursionError
tablo n=1200 basamak: 251
recursion limit: 1000
```

Sonuçlar iki şeyi açıkça gösteriyor. Naif yöntemde çağrı sayısı büyüklük olarak Fibonacci sayısının kendisine yakındır: `n = 30` için 2692537 çağrı, yani `fib(30)` değerinin (832040) üç katından fazla. Bu, `2 * fib(n+1) - 1` formülüyle uyumludur; üstel büyüme buradan gelir. Memo sürümünde gerçek hesap sayısı yalnızca `n + 1`'dir, çünkü `fib(0)`'dan `fib(n)`'e kadar her değer bir kez hesaplanır.

Ölçüm grafiği bu farkı tüm `n` aralığında gösterir. Dikey eksen logaritmiktir; naif eğri bir doğru gibi görünüyorsa, bu üstel büyümenin işaretidir.

![Şekil 16.3: Fibonacci için naif çağrı sayısı (kırmızı) ve memo hesap sayısı (mavi), n = 1..25. Dikey eksen logaritmik; naif büyüme bir doğru gibi, memo ise neredeyse düz kalır.](gorseller/b16_olcum.png)

Memo'nun bir bedeli var: özyineleme yığını. `fib_memo(n)` ilk çağrıda `fib_memo(n-1)`'i çağırır, o da `fib_memo(n-2)`'yi; derinlik `n`'e ulaşır. Python'da varsayılan özyineleme sınırı 1000'dir ve programın çıktısındaki iki satır bunu gösteriyor: `n = 900` başarılı oldu, `n = 1200` `RecursionError` verdi. Tabulation'da böyle bir derinlik sorunu yoktur; `fib_tablo(1200)` 251 basamaklı bir sayı üretir ve sorunsuz biter. Python'un büyük tamsayıları otomatik desteklemesi (Bölüm 3) bu programda taşmayı önler, ama C'de bu bedava değildir.

C'de aynı hesap farklı davranır. Aşağıdaki program `fib(92)`'den `fib(94)`'e kadar değerleri 64-bit işaretsiz (`unsigned long long`) tamsayıda hesaplar. İşaretsiz tamsayılarda taşma tanımlı davranıştır: değer 2^64 modülüne göre sarar. İşaretli tamsayıda aynı taşma **tanımsız davranıştır (UB)**: derleyici bunu optimizasyonda kendi lehine kullanabilir, dolayısıyla sonucu garanti edemezsin. Tanımsız davranış her zaman çökme anlamına gelmez; tipik olarak yanlış değer üretir, ama garanti değildir.

```c
/* fib_tasma.c: Fibonacci tablosu ve tamsayi tasmasi */
#include <stdio.h>

int main(void) {
    unsigned long long f[95];
    f[0] = 0;
    f[1] = 1;
    for (int i = 2; i < 95; i++)
        f[i] = f[i - 1] + f[i - 2];  /* unsigned: sarma (tanimli) */
    for (int i = 92; i <= 94; i++)
        printf("F(%d) = %llu\n", i, f[i]);
    printf("unsigned long long maksimum: %llu\n", ~0ULL);
    return 0;
}
```

Programı WSL içinde derledik ve çalıştırdık. Windows dosyasına WSL'den `/mnt/c/...` yolu üzerinden erişilir:

```term
$ gcc -O2 -Wall -Wextra -std=c11 fib_tasma.c -o fib_tasma
$ ./fib_tasma
F(92) = 7540113804746346429
F(93) = 12200160415121876738
F(94) = 1293530146158671551
unsigned long long maksimum: 18446744073709551615
```

`F(94)` değeri 2^64'ü aştığı için sarmıştır; çıktıdaki `1293530146158671551` gerçek `F(94)` değerinin 2^64 ile bölümünden kalan sayıdır. Bu değer yanlış görünüyor, çünkü yanlıştır, ama bu yanlışlık tanımlı bir sarmadır. İşaretli `long long` ile aynı kodu yazsaydık, `F(93)`'ten sonra UB başlardı ve sonuç hiçbir şekilde güvenilir olmazdı.

Şimdi tablo ile memo arasındaki dört farkı tek bir tabloda toplayalım:

| Özellik | Memoization | Tabulation |
|---|---|---|
| Yön | Üstten alta (özyineleme) | Alttan üste (döngü) |
| Yığın derinliği | En kötü `O(n)` çağrı yığını | Yığın kullanmaz |
| Gereksiz durumlar | Yalnızca ihtiyaç duyulanlar hesaplanır | Tüm tablo hesaplanır |
| Bellek | Önbellek ve yığın birlikte | Tablo; genelde daha az yük |
| Kod | Bağıntıyı doğrudan yazarsın | Sıra ve taban durumlarını sen kurarsın |

"Gereksiz durumlar" satırı önemli bir ayrımdır. Bazı problemlerde yalnızca küçük bir alt küme gerçekten gerekir; örneğin tek bir hedef hücreye giden yolların sayısı. Bu durumda memo yalnızca ulaşılabilir durumları hesaplar, tablo ise hepsini hesaplar. Diğer yandan tablo, hesaplama sırasını açıkça kontrol ettiği için bellek ve önbellek davranışını tahmin etmeyi kolaylaştırır. Pratikte iki yaklaşımı da bilmek gerekir: önce memo ile doğruluğu kontrol et, sonra yığın sorunu veya hız gerekirse tabloya geç.

## 16.4 Bellek optimizasyonu ve döngü yönü

Tabulation tablosu çoğu problemde gereğinden büyüktür. Sırt çantası için `n` eşya ve `W` kapasite varsa tablo `(n+1) × (W+1)` hücre tutar. Ama `dp[i]` satırı yalnızca `dp[i-1]` satırına bakar. Yani geçmiş satırları saklamak zorunda değilsin; tek bir satırı yerinde güncellemek yeter. Buna **yuvarlanan dizi** (rolling array) denir. Tablo boyutu `O(nW)`'den `O(W)`'ye iner.

Yerinde güncelleme tuzaklıdır. Tek bir diziyle çalışırken `dp[c]`'yi güncellediğinde, o değeri bir sonraki hesapta kullanmak isteyebilirsin ya da istemeyebilirsin. 0/1 sırt çantasında her eşya en fazla bir kez alınabilir; bunun için `dp[c - w]` değeri, eşyayı eklemeden önceki hâliyle kullanılmalıdır. Bunu sağlamanın yolu kapasiteleri **büyükten küçüğe** taramaktır: `dp[c]`'yi yazmadan önce `dp[c - w]` henüz bu eşyayla güncellenmemiştir, çünkü `c - w < c`.

Eşyanın sınırsız kez alınabildiği (unbounded) problemde ise tam tersini istersin. Kapasiteleri küçükten büyüğe tararsan, `dp[c - w]` bu eşyayla zaten güncellenmiş olur ve eşya tekrar alınabilir. Yani döngü yönü, problemin türünü belirler. Bu farkı, programın içinde ayrı bir fonksiyon olarak deneyeceğiz.

Aşağıdaki program dört şeyi yapar: 0/1 çözümünü iki yönle hesaplar, sınırsız çözümü ayrı bir fonksiyonla kurar, geri izleme için tam tablo üretir ve her şeyi kaba kuvvetle karşılaştırır. Kaba kuvvet, tüm alt kümeleri (0/1 için) ya da tüm sayı kombinasyonlarını (sınırsız için) dener; küçük girdilerde doğru cevabı garanti eder. Programın ilk parçası tek boyutlu tabloyu içerir.

```python
# sirt_canta.py: 0/1 ve sinirsiz sirt cantasi, kaba kuvvet kontrolu
import itertools
import random


def sirtcanta_01(agirlik, deger, W, yon="ters"):
    # dp[c]: kapasite c icin ulasilabilen en iyi deger
    dp = [0] * (W + 1)
    aralik = range(W, -1, -1) if yon == "ters" else range(W + 1)
    for w, v in zip(agirlik, deger):
        for c in aralik:
            if w <= c and dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[W]


def sinirsiz(agirlik, deger, W):
    dp = [0] * (W + 1)
    for c in range(1, W + 1):
        for w, v in zip(agirlik, deger):
            if w <= c and dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return dp[W]


```

`sirtcanta_01` fonksiyonunun iç döngüsü `for c in aralik` ile yalnızca bir kez kapasite üzerinde gider; `yon` parametresi döngü sırasını seçer. `sinirsiz` ise ayrı bir fonksiyondur ve kapasiteleri artan sırayla tarar, her kapasitede tüm eşyaları dener. İki fonksiyonun da bir `dp` dizisi vardır; `dp[c]`, "kapasite en fazla `c`" için ulaşılabilen en iyi değerdir. Bu yüzden `dp[W]` doğrudan cevaptır: kapasite tam dolmasa bile en iyisi zaten orada tutulur.

Bir sonraki parça tam tabloyu ve geri izleme fonksiyonunu içerir; onları Bölüm 16.5'te açıklayacağız.

```python
def tablo_01(agirlik, deger, W):
    # dp[i][c]: ilk i esya ile kapasite c; geri izleme icin tam tablo
    n = len(agirlik)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = agirlik[i - 1], deger[i - 1]
        for c in range(W + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c and dp[i - 1][c - w] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - w] + v
    return dp


def secilenler(dp, agirlik, W):
    secim, c = [], W
    for i in range(len(agirlik), 0, -1):
        if dp[i][c] != dp[i - 1][c]:   # esya i alinmis olmali
            secim.append(i - 1)
            c -= agirlik[i - 1]
    return sorted(secim)


```

Kaba kuvvet fonksiyonları, DP'nin doğruluğunu bağımsız olarak kontrol etmek için yazıldı. `kaba_01` `2^n` altkümeyi tek tek dener; bu yüzden yalnızca küçük `n` için uygundur. Bu bir hata değil, bir ölçüm araçtır: her zaman küçük örneklerle DP'yi kaba kuvvete karşı test et.

```python
def kaba_01(agirlik, deger, W):
    best = 0
    n = len(agirlik)
    for mask in range(1 << n):
        w = sum(agirlik[i] for i in range(n) if mask >> i & 1)
        v = sum(deger[i] for i in range(n) if mask >> i & 1)
        if w <= W:
            best = max(best, v)
    return best


def kaba_sinirsiz(agirlik, deger, W):
    best = 0
    k = len(agirlik)
    sinir = [W // w for w in agirlik]
    for sayilar in itertools.product(*[range(s + 1) for s in sinir]):
        w = sum(s * a for s, a in zip(sayilar, agirlik))
        v = sum(s * d for s, d in zip(sayilar, deger))
        if w <= W:
            best = max(best, v)
    return best


```

Ana fonksiyon, önce ters ve ileri yönün aynı örnekte nasıl farklı sonuç verdiğini gösterir. Ardından 300 rastgele örnekte iki DP'nin de kaba kuvvetle eşleştiğini doğrular. Sonunda kenar durumları (kapasite 0, boş eşya listesi) ve geri izleme örneğini yazdırır.

```python
def main():
    print("ornek: w=[2,3] v=[3,4] W=4")
    w, v = [2, 3], [3, 4]
    print("0/1 ters  :", sirtcanta_01(w, v, 4, "ters"))
    print("0/1 ileri :", sirtcanta_01(w, v, 4, "ileri"))
    print("sinirsiz  :", sinirsiz(w, v, 4))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(1, 7)
        w = [rnd.randint(1, 6) for _ in range(n)]
        v = [rnd.randint(1, 9) for _ in range(n)]
        W = rnd.randint(0, 15)
        if sirtcanta_01(w, v, W) != kaba_01(w, v, W):
            hata += 1
        if sinirsiz(w, v, W) != kaba_sinirsiz(w, v, W):
            hata += 1
    print("300 rastgele ornek, 0/1 ve sinirsiz hata:", hata)
    # kapasite 0 ve bos esya kenar durumlari
    print("W=0:", sirtcanta_01([2], [5], 0), sinirsiz([2], [5], 0))
    print("bos:", sirtcanta_01([], [], 5), sinirsiz([], [], 5))
    w, v = [1, 3, 4, 5], [1, 4, 5, 7]
    dp = tablo_01(w, v, 7)
    print("0/1 W=7 en iyi:", dp[-1][-1], "secilen:",
          secilenler(dp, w, 7))


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python sirt_canta.py
ornek: w=[2,3] v=[3,4] W=4
0/1 ters  : 4
0/1 ileri : 6
sinirsiz  : 6
300 rastgele ornek, 0/1 ve sinirsiz hata: 0
W=0: 0 0
bos: 0 0
0/1 W=7 en iyi: 9 secilen: [1, 2]
```

Çıktının ilk üç satırı, döngü yönünün önemini tek bir örnekte gösteriyor. Eşyalar `(ağırlık, değer)` olarak `(2, 3)` ve `(3, 4)`, kapasite 4. 0/1 kuralında, iki eşyadan en fazla biri alınabilir: en iyi değer `4`'tür (yalnız ikinci eşya). Ters döngü bunu doğru bulur. İleri döngü `6` verir, yani birinci eşyayı iki kez alır (`2 + 2 = 4`, değer `3 + 3 = 6`). Yani ileri döngü, sessizce 0/1 problemini sınırsız probleme çevirmiş oldu. Bu bir hata mesajı vermez, sadece yanlış cevap verir; bu yüzden döngü yönünü anlamadan 0/1 çözümü yazmamalısın.

Rastgele testte hata sayısının sıfır çıkması, DP'nin iki sürümünün de kaba kuvvetle uyumlu olduğunu gösterir. Bu test sonucu bir kanıt değildir; yalnızca `random.Random(42)` ile üretilen 300 örnekte doğrulamadır. Doğruluk kanıtı için ayrı bir argüman gerekir: 0/1 için döngü değişmezi, her eşyada `dp[c]`'nin "ilk `i` eşya ile kapasite en fazla `c`" anlamını koruduğunu söyler.

Kenar durumlarına da bakalım. `W = 0` için kapasite sıfırdır ve hiçbir eşya sığmaz; cevap 0 olmalıdır. Boş eşya listesinde de cevap 0'dır. Programın çıktısı ikisini de doğru yazıyor. Bu iki durumu her DP'de ayrıca kontrol etmek, Bölüm 16.2'deki taban durumların doğruluğunu sınamanın en ucuz yoludur.

## 16.5 Çözümü geri kurmak: değer yetmez, seçimi de bil

DP çoğu zaman yalnızca bir sayı üretir: en yüksek değer, en az maliyet, en uzun uzunluk. Pratikte ise çoğu zaman *hangi* eşyaların alındığını, *hangi* hizalamanın yapıldığını ya da *hangi* düzenlemelerin gerektiğini de istersin. Bu soruyu cevaplamak için tablonun yalnızca son hücresini değil, hesabın izini de tutmak gerekir.

Yaygın yöntem geri izlemedir (backtracking, Bölüm 15'te gördüğümüz terim buradaki anlamla karıştırılmamalı). Tablo tamamen doldurulduktan sonra, cevabın son hücreden başlayarak her adımda "bu değere nasıl gelindi?" sorusunu sorarız. Her adımda tablodaki iki komşuya bakarak hangi bağıntının geçerli olduğunu buluruz ve oradan geriye gideriz.

Sırt çantasında bu basittir. `dp[i][c]` ile `dp[i-1][c]` aynıysa, `i`. eşya alınmamıştır: değer, eşya olmadan da aynı şekilde elde edilmiştir. Farklıysa eşya alınmıştır ve kalan kapasite `c - w_i`'dir. Aşağıdaki şekil, `W = 7` ve dört eşyalık örnekte tabloyu ve geri izleme yolunu gösteriyor.

![Şekil 16.4: 0/1 sırt çantası tablosu (eşyalar ağırlık-değer: (1,1), (3,4), (4,5), (5,7); W = 7). Bordo hücreler, eşyanın alındığı adımlardır; açık yeşil hücreler geri izleme yolunu oluşturur. Seçilen eşyalar 2. ve 3. (ağırlık 3 ve 4) ve toplam değer 9'dur.](gorseller/b16_knap_tablo.png)

Şekildeki yolu programın fonksiyonuyla izleyelim. `secilenler` fonksiyonu `dp[i][c] != dp[i-1][c]` koşulunu kullanır ve alınan eşyanın indeksini döndürür. Bu yüzden onu sırt çantası programının ikinci parçasında gördük:

```python
def secilenler(dp, agirlik, W):
    secim, c = [], W
    for i in range(len(agirlik), 0, -1):
        if dp[i][c] != dp[i - 1][c]:   # esya i alinmis olmali
            secim.append(i - 1)
            c -= agirlik[i - 1]
    return sorted(secim)

```

Bu fonksiyon tam tabloyu okuduğu için, tablonun tamamının saklı olması şarttır. Yuvarlanan dizi (Bölüm 16.4) bunu sağlamaz: tek satır kullanıldığında eski satırlar yok olur ve geri izleme yapılamaz. Bu bir ödünleşmedir. Ya `O(nW)` bellek ödersin ve geri izlersin, ya da `O(W)` bellekle yalnızca değeri hesaplarsın. Bellek kritikse üçüncü bir yol vardır: Hirschberg tipi bölme-fethetme, geri izlemeyi tablo saklamadan yapar. Bu yöntem LCS için de geçerlidir; ama uygulaması bu kitabın kapsamı için karmaşıktır, konuyu kendi projen için ileri okumaya bırak.

Geri izlemede bir ayrıntı daha önemlidir: eşitlik durumu. Birden fazla en iyi çözüm varsa, `secilenler` hangisini seçtiğini kendi koşuluyla belirler. Bu, "tek doğru cevap" beklentisini bozar. Mülakatta "bu çözüm tek mi?" diye sorulduğunda, eşitlik durumlarını tek tek saymak gerekir.

Tablo ile yolu birlikte düşünmek, hatayı bulmanın da en hızlı yoludur. Eğer geri izlemenin sonucu `dp[n][W]` değerine eşit bir toplam vermiyorsa, ya tablo ya da geri izleme yanlıştır. Programın ana fonksiyonunda bu kontrolü yapmadık, çünkü kaba kuvvet karşılaştırması yeterlidir. Ama kendi kodunda değer ile seçilen eşyaların toplamını ayrıca karşılaştırmayı alışkanlık hâline getir.

## 16.6 Sayma ve en iyileme: Fibonacci, merdiven ve para bozma

DP'nin iki büyük ailesi vardır. Birincisi **sayma** problemleridir: kaç farklı yol, kaç farklı kombinasyon var? İkincisi **en iyileme** problemleridir: en az ya da en çok ne? İkisi aynı protokolü kullanır (Bölüm 16.2); geçişteki işlem değişir. Sayma geçişi toplamdır, en iyileme `min` ya da `max`.

Merdiven problemi sayma örneğidir. `n` basamaklı bir merdivene 1 ya da 2 basamak atlayarak kaç farklı yolla çıkılır? Bölüm 16.2'deki protokol ile `dp[i] = dp[i-1] + dp[i-2]`, `dp[0] = 1`, `dp[1] = 1` olur. Bu dizi Fibonacci dizisidir; `n` basamak için cevap `fib(n+1)`'dir. Yani Bölüm 16.3'teki Fibonacci ölçümü aslında bir sayma problemiydi.

Para bozma ise hem sayma hem en iyileme olarak sorulabilir. Elinde `1`, `2`, `5` birimlik madeni paralar olsun ve `tutar` kadar parayı tam olarak toplamak istiyorsun. Üç soru sorulabilir: En az kaç parayla toplanır? Kaç farklı şekilde toplanır? Ve şekil sırası önemli mi? Son soru çoğu zaman gözden kaçar ve asıl tuzak oradadır.

Aşağıdaki program üç fonksiyonla bu soruları cevaplar. İlk fonksiyon en az madeni parayı bulur. Tutarı `inf` (sonsuz yerine `tutar + 1`, çünkü en fazla `tutar` adet para gerekebilir) ile başlatır ve `dp[t]`'yi `dp[t - p] + 1`'den küçükse günceller.

```python
# para_bozma.py: en az madeni para ve yol sayilari
import random


def en_az_madeni(paralar, tutar):
    inf = tutar + 1               # tutar'i asla asmaz: sonsuz yerine
    dp = [0] + [inf] * tutar      # dp[t]: t'yi toplayan en az adet
    for t in range(1, tutar + 1):
        for p in paralar:
            if p <= t and dp[t - p] + 1 < dp[t]:
                dp[t] = dp[t - p] + 1
    return dp[tutar] if dp[tutar] < inf else -1


def yol_kombinasyon(paralar, tutar):
    # once madeni para, sonra tutar: siralama onemsiz (kombinasyon)
    ways = [1] + [0] * tutar
    for p in paralar:
        for t in range(p, tutar + 1):
            ways[t] += ways[t - p]
    return ways[tutar]


def yol_permutasyon(paralar, tutar):
    # once tutar, sonra madeni para: siralama onemli (permutasyon)
    ways = [1] + [0] * tutar
    for t in range(1, tutar + 1):
        for p in paralar:
            if p <= t:
                ways[t] += ways[t - p]
    return ways[tutar]


```

Kalan iki fonksiyon, yolların sayısını hesaplar; aralarındaki tek fark döngülerin iç içe geçiş sırasıdır. `yol_kombinasyon` önce madeni paraları, sonra tutarı dolaşır: her madeni para için tabloyu bir kez günceller. Bu, paraların sırasını göz ardı eder; yani `1 + 2` ile `2 + 1` aynı sayılır. `yol_permutasyon` ise önce tutarı, sonra madeni paraları dolaşır: her tutar için tüm paraları dener. Bu da sıralı dizileri sayar; `1 + 2` ile `2 + 1` ayrı sayılır.

```python
def kaba_kombinasyon(paralar, tutar, bas=0):
    if tutar == 0:
        return [()]
    sonuc = []
    for i in range(bas, len(paralar)):
        if paralar[i] <= tutar:
            kalan_listesi = kaba_kombinasyon(paralar,
                                             tutar - paralar[i], i)
            for kalan in kalan_listesi:
                sonuc.append((paralar[i],) + kalan)
    return sonuc


def kaba_permutasyon(paralar, tutar):
    if tutar == 0:
        return 1
    return sum(kaba_permutasyon(paralar, tutar - p)
               for p in paralar if p <= tutar)


```

Bu iki sayma biçimi, DP'nin en sık karıştırılan iki sorusudur. "Kaç farklı kombinasyon" sorusu için madeni para döngüsü dışta, "kaç farklı sıralı dizi" sorusu için tutar döngüsü dışta olmalıdır. Döngü yerini değiştirmek, bir problemi diğerine dönüştürür. Ana fonksiyon bunu sayılarla gösterir ve kaba kuvvet karşılaştırması yapar.

```python
def main():
    paralar = [1, 2, 5]
    for t in (0, 3, 5, 11):
        print(f"tutar={t:2d} en_az={en_az_madeni(paralar, t):2d}",
              f"kombinasyon={yol_kombinasyon(paralar, t):2d}",
              f"permutasyon={yol_permutasyon(paralar, t):2d}")
    print("paralar [2], tutar 3 -> en_az =", en_az_madeni([2], 3))
    rnd = random.Random(42)
    hata = 0
    for _ in range(200):
        k = rnd.randint(1, 4)
        p = sorted(rnd.sample(range(1, 8), k))
        t = rnd.randint(0, 12)
        if yol_kombinasyon(p, t) != len(kaba_kombinasyon(p, t)):
            hata += 1
        if yol_permutasyon(p, t) != kaba_permutasyon(p, t):
            hata += 1
    print("200 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python para_bozma.py
tutar= 0 en_az= 0 kombinasyon= 1 permutasyon= 1
tutar= 3 en_az= 2 kombinasyon= 2 permutasyon= 3
tutar= 5 en_az= 1 kombinasyon= 4 permutasyon= 9
tutar=11 en_az= 3 kombinasyon=11 permutasyon=218
paralar [2], tutar 3 -> en_az = -1
200 rastgele ornek, hata: 0
```

Tutar 5 satırı, kombinasyon ile permütasyonun farkını açıkça gösteriyor. Kombinasyon sayısı 4'tür: `{5}`, `{2,2,1}`, `{2,1,1,1}`, `{1,1,1,1,1}`. Permütasyon sayısı 9'dur, çünkü `{2,2,1}` 3 farklı sıralanır, `{2,1,1,1}` 4 farklı sıralanır ve diğer ikisi 1'er tanedir. Aynı tutarın en az madeni para sayısı ise 1'dir (tek bir 5 birimlik para). Üç soru üç farklı cevap verir; hangi sorunun sorulduğunu önce anlamak gerekir.

`tutar = 3` için `[2]` madeni parası yalnız başına yetmez; program `-1` döndürür. Bu, "çözüm yok" durumunun da tabloda `inf` olarak taşındığını gösterir. Kaba kuvvet kontrolü 200 rastgele örnekte iki sayma fonksiyonunu da doğruladı.

Para bozmada bir gerçek daha var: sıralı dizi sayısı üstel büyür. `tutar = 11` için kombinasyon sayısı 11 iken permütasyon sayısı 218'dir; tutar büyüdükçe bu değerler hızla artar. Bu yüzden sonuçları büyük tutarlarda tam sayı olarak saklamak için Python'un büyük tamsayılarını ya da bir mod (örneğin `10^9 + 7`) kullanmak gerekebilir. Mod kullanıldığında sonuç yalnızca kalanı verir; bu, soruyu değiştirir ve bunu açıkça belirtmek gerekir.

Son olarak bağlantıya bak: merdiven sayısı, yalnızca 1 ve 2 paralarıyla sıralı permütasyon saymaktır. `yol_permutasyon([1, 2], 5)` çağrısı 8 verir; bu `fib(6) = 8` ile aynıdır. Yani merdiven, para bozmanın özel bir durumudur ve Bölüm 16.2'deki protokolün iki kez kullanıldığını görürsün.

## 16.7 Sırt çantası ailesi: 0/1, sınırsız ve çubuk kesimi

Sırt çantası problemi, DP'nin en çok karşılaşacağın kalıptır. Ortak yapı şudur: bir kapasite (ağırlık, uzunluk, bütçe) var ve her öğenin bir maliyeti ve bir getirisi var. Amaç, kapasiteyi aşmadan en büyük toplam getiriyi bulmaktır. Bu ailenin üyeleri, öğelerin kaç kez kullanılabildiğine göre ayrılır.

Bölüm 16.4'te 0/1 ve sınırsız iki sürümü programda gördük. Burada farkı tabloyla özetleyelim:

| Problem | Her öğe için kısıt | Kapasite döngüsü | Kaba kuvvet |
|---|---|---|---|
| 0/1 sırt çantası | En fazla bir kez | Büyükten küçüğe | `2^n` altküme |
| Sınırsız sırt çantası | Sınırsız kopya | Küçükten büyüğe | Sayı kombinasyonları |
| Çubuk kesimi | Uzunluk parçaları sınırsız | Küçükten büyüğe | Parça bölümleri |

Son satır, sınırsız sırt çantasının farklı bir kılığıdır. Bir çubuğu `n` birim uzunlukta düşün; `k` birimlik parçanın satış fiyatı `fiyat[k]` olsun. Çubuğu parçalara kesmek ve en yüksek geliri elde etmek istiyorsun. Her parça bir "öğe" (ağırlık `k`, değer `fiyat[k]`), toplam uzunluk ise "kapasite"dir. Parçalar sınırsız kez kullanılabilir, çünkü aynı uzunlukta birden fazla parça satabilirsin. Yani çubuk kesimi, sınırsız sırt çantasının tam karşılığıdır.

Protokolü uygulayalım. `dp[u]`, uzunluğu `u` olan çubuğun en yüksek gelirini tutsun. Son parçayı `k` seçersen, kalan `u - k` için en iyi gelir `dp[u - k]`'dır. Bu yüzden `dp[u] = max(fiyat[k] + dp[u - k])` olur, `k` 1'den `u`'ya kadar. Taban durum `dp[0] = 0`'dır: sıfır uzunluk sıfır gelir.

Aşağıdaki program bu bağıntıyı uygular, kaba kuvvetle karşılaştırır ve örnek fiyat tablosu için sonuçları yazdırır. Bu fiyat tablosu, bu alanda sık kullanılan bir örnekle aynıdır (Cormen ve arkadaşlarının algoritma kitabında yer alır).

```python
# cubuk.py: cubuk kesimi (rod cutting) ve kaba kuvvet kontrolu
import random


def cubuk_kes(fiyat, n):
    # fiyat[k]: k uzunluktaki parcanin fiyati (fiyat[0] = 0)
    dp = [0] * (n + 1)          # dp[u]: uzunluk u icin en iyi gelir
    for u in range(1, n + 1):
        for k in range(1, min(u, len(fiyat) - 1) + 1):
            dp[u] = max(dp[u], fiyat[k] + dp[u - k])
    return dp[n]


def kaba(fiyat, n):
    if n == 0:
        return 0
    return max(fiyat[k] + kaba(fiyat, n - k)
               for k in range(1, min(n, len(fiyat) - 1) + 1))


def main():
    fiyat = [0, 1, 5, 8, 9, 10, 17, 17, 20]
    for n in range(1, 9):
        print(f"uzunluk {n}: gelir {cubuk_kes(fiyat, n)}")
    rnd = random.Random(42)
    hata = 0
    for _ in range(200):
        m = rnd.randint(1, 8)
        f = [0] + [rnd.randint(1, 20) for _ in range(m)]
        n = rnd.randint(0, 10)
        if cubuk_kes(f, n) != kaba(f, n):
            hata += 1
    print("200 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python cubuk.py
uzunluk 1: gelir 1
uzunluk 2: gelir 5
uzunluk 3: gelir 8
uzunluk 4: gelir 10
uzunluk 5: gelir 13
uzunluk 6: gelir 17
uzunluk 7: gelir 18
uzunluk 8: gelir 22
200 rastgele ornek, hata: 0
```

Uzunluk 4 için en iyi gelir 10'dur: çubuğu iki parçaya (`2 + 2`) bölmek `5 + 5 = 10` verir; tek parça ise `9` verir. Uzunluk 8 için cevap 22'dir ve bunu `2 + 6` parçalarıyla elde edersin: `5 + 17 = 22`. Kaba kuvvet, rastgele fiyat tablolarında yaptığı 200 karşılaştırmanın hiçbirinde farklı sonuç vermedi.

Programda bir ayrıntıya dikkat et. Fiyat dizisi `fiyat[k]`, ancak `k` uzunluğu için fiyat tanımlı değilse o parça hiç kesilemez. Bu yüzden döngü üst sınırı `min(u, len(fiyat) - 1)` olarak alındı. İlk sürümde bu sınır yoktu ve rastgele testte `IndexError` aldık; düzeltme, gerçek problemin sınırını kodda açıkça yazmaktı. Bu, DP'de sık yapılan bir hatadır: tablonun ve girdinin boyutlarını birbirinden bağımsız varsaymak.

Son olarak, sınırsız sırt çantasının çalışma zamanına bak. Kapasite döngüsü `W` adım, her adımda `n` eşya; toplam `O(nW)`. Çubuk kesiminde `n` uzunluk, her uzunlukta en fazla `n` parça denenir; toplam `O(n^2)`. Bu, bağıntıdaki iç içe iki döngüden gelir: dış döngü uzunlukta, iç döngü kesim boyunda ilerler.

## 16.8 Dizi DP'leri: LCS, edit distance ve LIS

Dizi DP'leri, iki diziyi (ya da tek bir diziyi) karşılaştırır. Üç klasik problem bu ailenin temelidir: en uzun ortak altdizi (LCS), iki dizgi arasındaki düzenleme mesafesi (edit distance) ve en uzun artan altdizi (LIS). Üçü de tabloyu satır satır ya da köşegen boyunca doldurur.

Önce bir ayrımı netleştirelim, çünkü mülakatta ve kendi projende karıştırılır. **Altdizi** (subsequence) elemanları sırasını koruyarak, ama aralarını atlayarak seçtiğin dizidir. **Altdizge** (substring) ise ardışık elemanlardan oluşan bir parçadır. LCS altdizi ile ilgilenir, bu bölümde ele alacağımız problem budur. Kod Okuma Egzersizi'nde göreceğimiz difflib kodu ise ardışık eşleşmeyi, yani altdizgiyi arar.

### LCS: en uzun ortak altdizi

`a` ve `b` dizgileri için `dp[i][j]`, `a`'nın ilk `i` karakteri ile `b`'nin ilk `j` karakteri arasındaki LCS uzunluğu olsun. Geçiş iki durumludur. Eğer `a[i-1] == b[j-1]` ise bu karakter LCS'e girebilir ve `dp[i][j] = dp[i-1][j-1] + 1` olur. Değilse, iki karakterden en az birini atlamak gerekir ve `dp[i][j] = max(dp[i-1][j], dp[i][j-1])` olur. Taban durumlar boş bir önek için 0'dır.

Aşağıdaki program tabloyu doldurur, geri izleyerek LCS dizgisini yazdırır ve küçük örneklerde kaba kuvvetle karşılaştırır. Kaba kuvvet, `a`'nın tüm altdizilerini üretip `b` içinde arar.

```python
# lcs.py: en uzun ortak altdizi, tablo ve geri izleme
import itertools


def lcs_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def geri_izle(dp, a, b):
    i, j, harf = len(a), len(b), []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            harf.append(a[i - 1])
            i, j = i - 1, j - 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(harf))


def kaba(a, b):
    best = 0
    for k in range(len(a) + 1):
        for alt in itertools.combinations(a, k):
            s = "".join(alt)
            it = iter(b)
            if all(ch in it for ch in s):   # s, b'nin altdizisi mi?
                best = max(best, k)
    return best


```

Ana fonksiyonun çıktısı, tabloyu bir matris olarak gösterir; üst satır ve sol sütun sıfırlardan oluşan taban durumlardır. Geri izleme kuralı şöyledir: eşleşen karakterde köşegenden gel ve karakteri al; eşleşmeyen karakterde, değeri büyük olan komşuya git (eşitse yukarı).

```python
def main():
    a, b = "ABCBDAB", "BDCABA"
    dp = lcs_tablo(a, b)
    print("     " + " ".join(f"{ch:>2}" for ch in " " + b))
    for i, row in enumerate(dp):
        ch = " " if i == 0 else a[i - 1]
        print(f"{ch:>2}  " + " ".join(f"{x:>2}" for x in row))
    s = geri_izle(dp, a, b)
    print("LCS uzunlugu:", dp[-1][-1], "LCS:", s)
    import random
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        x = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 7)))
        y = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 7)))
        t = lcs_tablo(x, y)
        g = geri_izle(t, x, y)
        if t[-1][-1] != kaba(x, y) or len(g) != t[-1][-1]:
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python lcs.py
         B  D  C  A  B  A
     0  0  0  0  0  0  0
 A   0  0  0  0  1  1  1
 B   0  1  1  1  1  2  2
 C   0  1  1  2  2  2  2
 B   0  1  1  2  2  3  3
 D   0  1  2  2  2  3  3
 A   0  1  2  2  3  3  4
 B   0  1  2  2  3  4  4
LCS uzunlugu: 4 LCS: BCBA
300 rastgele ornek, hata: 0
```

Sonucun `BCBA` olduğunu tablodan elle de doğrulayabilirsin. Son hücre 4 ve geri izleme dört eşleşme yapar. Bu tablonun ve yolun şekli aşağıda.

![Şekil 16.5: LCS tablosu, a = ABCBDAB ve b = BDCABA. Açık yeşil hücreler geri izleme yolunu gösterir; köşegen adımlar, eşleşen harfleri (A, B, C, B) işaretler.](gorseller/b16_lcs_tablo.png)

LCS'in gerçek hayattaki karşılığı, satır bazlı `diff`'tir. İki dosyanın satırlarını birer dizi olarak düşün; ortak satırların en uzun altdizisi LCS'tir. LCS'e dahil olmayan satırlar silinmiş ya da eklenmiş sayılır. Bu yorumla `diff`'in çıktısı, LCS'in tümleyenidir. GNU `diff` bu hesabı tabloyla değil Myers algoritmasıyla yapar; tanım aynıdır, hız farklıdır. Bu bölümün kendi projesi tam olarak bu fikri kullanır.

C'de aynı algoritmanın belleği elle yönetilen sürümü şöyle görünür. Tablo tek bir `calloc` bloğunda, satır-sütun indeksleriyle tutulur. `calloc` bellekteki her değeri sıfırlar, bu da taban durumların elle doldurulmasını gereksiz kılar. Burada `(n+1) * (m+1)` çarpımının taşmaması için girdi boyutlarının makul olduğunu varsayıyoruz; gerçek bir kodda bu kontrol edilmelidir.

```c
/* lcs.c: en uzun ortak altdizi, tablo ve geri izleme (C11) */
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* dp[i][j]: a'nin ilk i, b'nin ilk j karakteri icin LCS */
static size_t *tablo_olustur(const char *a, const char *b,
                             size_t n, size_t m) {
    size_t w = m + 1;
    size_t *dp = calloc((n + 1) * w, sizeof *dp);
    if (dp == NULL)
        return NULL;
    for (size_t i = 1; i <= n; i++) {
        for (size_t j = 1; j <= m; j++) {
            if (a[i - 1] == b[j - 1])
                dp[i * w + j] = dp[(i - 1) * w + (j - 1)] + 1;
            else if (dp[(i - 1) * w + j] >= dp[i * w + (j - 1)])
                dp[i * w + j] = dp[(i - 1) * w + j];
            else
                dp[i * w + j] = dp[i * w + (j - 1)];
        }
    }
    return dp;
}

/* Geri izleme: LCS dizgisini sonuc tamponuna yazar. */
static void geri_izle(const size_t *dp, const char *a, const char *b,
                      size_t n, size_t m, char *sonuc) {
    size_t w = m + 1, i = n, j = m, k = dp[n * w + m];
    sonuc[k] = '\0';
    while (i > 0 && j > 0) {
        if (a[i - 1] == b[j - 1]) {
            sonuc[--k] = a[i - 1];
            i--;
            j--;
        } else if (dp[(i - 1) * w + j] >= dp[i * w + (j - 1)]) {
            i--;
        } else {
            j--;
        }
    }
}

int main(void) {
    const char *a = "ABCBDAB";
    const char *b = "BDCABA";
    size_t n = strlen(a), m = strlen(b);
    size_t *dp = tablo_olustur(a, b, n, m);
    if (dp == NULL)
        return 1;
    size_t uzunluk = dp[n * (m + 1) + m];
    char *sonuc = malloc(uzunluk + 1);
    if (sonuc == NULL) {
        free(dp);
        return 1;
    }
    geri_izle(dp, a, b, n, m, sonuc);
    printf("LCS uzunlugu: %zu\n", uzunluk);
    printf("LCS: %s\n", sonuc);
    free(sonuc);
    free(dp);
    return 0;
}
```

Programı WSL'de iki kez derledik: önce normal, sonra `-fsanitize=address,undefined` ile. Sanitizer, bellek taşmasını ve tanımsız davranışı çalışma zamanında yakalar. Çıktıda sanitizer uyarısı yoksa program bu girdi için temizdir:

```term
$ gcc -O2 -Wall -Wextra -std=c11 lcs.c -o lcs
$ ./lcs
LCS uzunlugu: 4
LCS: BCBA
$ gcc -g -O1 -Wall -Wextra -fsanitize=address,undefined lcs.c -o lcs_asan
$ ./lcs_asan
LCS uzunlugu: 4
LCS: BCBA
```

Sanitizer'ın temiz çıkması, bu bir kanıt değildir; yalnızca çalışan yollar için bir sinyaldir. Diziyi sınır dışına taşıran bir girdi için aynı program ASan raporu verirdi. Bu, C'de DP tablolarının indekslerini her zaman iki kez kontrol etmenin nedenidir.

### Edit distance: yazım denetimi ve düzenleme mesafesi

İki dizgi arasındaki düzenleme mesafesi, birinciyi ikinciye dönüştürmek için gereken en az işlem sayısıdır. İşlemler üçtür: bir karakter ekle, sil ya da değiştir. Bu tanıma Levenshtein mesafesi de denir. Yazım denetimi (spell check), en yakın sözcüğü bulmak için bu mesafeyi kullanır; Mert Studio Code'daki Türkçe parser'a benzer bir öneri motoru bu yolla yazılabilir (Çözümlü Örnekler'in dördüncüsünde bunu deneyeceksin).

`dp[i][j]`, `a`'nın ilk `i` karakterini `b`'nin ilk `j` karakterine çevirmenin en az maliyetidir. Taban durumlar: `dp[i][0] = i` (hepsini sil), `dp[0][j] = j` (hepsini ekle). Geçiş: `a[i-1] == b[j-1]` ise maliyet değişmez, `dp[i][j] = dp[i-1][j-1]`. Değilse, üç seçeneğin en küçüğüne 1 eklenir: değiştir (`dp[i-1][j-1]`), sil (`dp[i-1][j]`) ve ekle (`dp[i][j-1]`).

Programın ilk parçası tabloyu ve işlem dizisini geri izleyerek üretir. Geri izleme sırasında her adımda hangi işlemin kullanıldığını kaydederiz; bu yüzden yalnızca mesafeyi değil, dönüşümün kendisini de elde ederiz.

```python
# edit.py: edit distance, islem dizisi ve BFS ile dogrulama
import random
from collections import deque


def edit_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i                    # a'nin i harfini silmek
    for j in range(m + 1):
        dp[0][j] = j                    # bos diziye j harf eklemek
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1],   # degistir
                                   dp[i - 1][j],       # sil
                                   dp[i][j - 1])       # ekle
    return dp


def islemler(a, b, dp):
    i, j, adim = len(a), len(b), []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            adim.append(f"ESLE {a[i - 1]}")
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            adim.append(f"DEGISTIR {a[i - 1]}->{b[j - 1]}")
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            adim.append(f"SIL {a[i - 1]}")
            i -= 1
        else:
            adim.append(f"EKLE {b[j - 1]}")
            j -= 1
    return list(reversed(adim))


```

Programın ikinci parçası, işlem dizisini `a` üzerinde uygular ve sonucun `b`'ye eşit olduğunu doğrular. Bu, geri izlemenin doğruluğunu kanıtlayan en iyi testtir: işlemleri yürütmek sonucu üretmeliyse, geri izleme doğrudur. Ayrıca `bfs` fonksiyonu, düzenleme işlemlerinin tüm dizgi uzayında en kısa yolunu bulur. Bu, DP'den bağımsız bir kontroldür; DP'nin tablo bağıntısını hiç kullanmaz.

```python
def uygula(a, adim):
    # Islemleri soldan sağa a'ya uygular; sonucu dondurur.
    cikti, p = [], 0
    for op in adim:
        if op.startswith("ESLE"):
            cikti.append(a[p]); p += 1
        elif op.startswith("DEGISTIR"):
            cikti.append(op[-1]); p += 1
        elif op.startswith("SIL"):
            p += 1
        else:
            cikti.append(op[-1])
    assert p == len(a)
    return "".join(cikti)


def bfs(a, b, alfabe="ab"):
    # Ust sinir: uzunluk en fazla max(|a|,|b|)+2 olan dizgiler
    sinir = max(len(a), len(b)) + 2
    kuyruk, gorulen = deque([(a, 0)]), {a}
    while kuyruk:
        s, d = kuyruk.popleft()
        if s == b:
            return d
        komsu = []
        for k in range(len(s) + 1):
            for c in alfabe:
                komsu.append(s[:k] + c + s[k:])          # ekle
        for k in range(len(s)):
            komsu.append(s[:k] + s[k + 1:])              # sil
            for c in alfabe:
                komsu.append(s[:k] + c + s[k + 1:])      # degistir
        for t in komsu:
            if len(t) <= sinir and t not in gorulen:
                gorulen.add(t)
                kuyruk.append((t, d + 1))
    return -1


```

Ana fonksiyon `kitten` → `sitting` örneğini çözer ve 150 rastgele örnekte üç kontrolü birlikte yapar: BFS mesafesi, işlemlerin uygulanması ve düzenleme sayısı. Düzenleme sayısını sayarken `ESLE` (eşleşme) işlemlerini dışarıda bırakmak gerekir; çünkü onlar maliyet taşımaz.

```python
def main():
    a, b = "kitten", "sitting"
    dp = edit_tablo(a, b)
    print("mesafe:", dp[-1][-1])
    for op in islemler(a, b, dp):
        print("  ", op)
    print("uygula:", uygula(a, islemler(a, b, dp)))
    rnd = random.Random(42)
    hata = 0
    for _ in range(150):
        x = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 4)))
        y = "".join(rnd.choice("ab")
                    for _ in range(rnd.randint(0, 4)))
        t = edit_tablo(x, y)
        adim = islemler(x, y, t)
        if t[-1][-1] != bfs(x, y) or uygula(x, adim) != y:
            hata += 1
        duzenleme = [o for o in adim if not o.startswith("ESLE")]
        if len(duzenleme) != t[-1][-1]:
            hata += 1
    print("150 rastgele ornek (BFS ve uygulama), hata:", hata)
    print("bos-bos:", edit_tablo("", "")[0][0], "bos-abc:",
          edit_tablo("", "abc")[0][3])


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python edit.py
mesafe: 3
   DEGISTIR k->s
   ESLE i
   ESLE t
   ESLE t
   DEGISTIR e->i
   ESLE n
   EKLE g
uygula: sitting
150 rastgele ornek (BFS ve uygulama), hata: 0
bos-bos: 0 bos-abc: 3
```

Çıktı üç düzenleme gösteriyor: `k` harfi `s` ile değiştirilir, `e` harfi `i` ile değiştirilir ve sona `g` eklenir. Toplam maliyet 3'tür. Aşağıdaki şekil bu yolu tabloda gösterir.

![Şekil 16.6: kitten'den sitting'e edit distance tablosu. Yeşil yol, üç düzenlemeye (k->s, e->i, ekle g) karşılık gelen hücrelerdir; son hücre 3'tür.](gorseller/b16_edit_tablo.png)

Edit distance'ın bir hatası çok sinsidir: maliyet doğru olsa bile geri izleme yanlış işlem dizisi üretebilir. Bu yüzden iki ayrı kontrol gerekir: sayı (BFS ile) ve işlem dizisi (uygulayarak). Programda ikisi de yapılıyor.

### LIS: en uzun artan altdizi

Bir dizinin en uzun artan altdizisi (LIS), sırasını koruyan ve kesin artan olan en uzun altdizidir. `dp[i]` = `a[i]`'de biten en uzun artan altdizinin uzunluğu olsun; `dp[i] = 1 + max(dp[j])`, `j < i` ve `a[j] < a[i]` için. Bu, `O(n^2)` bir DP'dir. Bölüm 16.2'de gördüğümüz gibi cevap tüm `dp` değerlerinin en büyüğüdür.

Daha hızlı bir yol vardır: sabır sıralaması (patience sorting). Her adımda bir kuyruk dizisi tutarız; `kuyruk[k]`, uzunluğu `k + 1` olan artan altdizilerin en küçük son elemanıdır. Yeni bir `x` geldiğinde, `x`'ten küçük olmayan ilk konumu ikili aramayla buluruz (Bölüm 14.2'deki alt sınır). Bu konum kuyruğun sonundaysa dizi uzar; değilse o konumdaki değer `x` ile değiştirilir. Bu değiştirme, aynı uzunluktaki altdizilerin en küçük son elemanını korur, bu yüzden sonraki adımlar için daha iyidir. Her eleman için `O(log n)` iş yapıldığından toplam `O(n log n)` olur.

Aşağıdaki program iki sürümü çalıştırır, sabır izini yazdırır ve kaba kuvvetle karşılaştırır. `bisect.bisect_left` Python'un standart ikili arama fonksiyonudur; Bölüm 14'teki alt sınır tanımıyla aynıdır.

```python
# lis.py: en uzun artan altdizi, O(n^2) ve sabir (O(n log n))
import bisect
import itertools
import random


def lis_n2(a):
    n = len(a)
    L = [1] * n                 # L[i]: a[i]'de biten en uzun LIS
    for i in range(n):
        for j in range(i):
            if a[j] < a[i] and L[j] + 1 > L[i]:
                L[i] = L[j] + 1
    return max(L, default=0)


def lis_nlogn(a, izle=False):
    kuyruk = []                 # kuyruk[k]: k+1 uzunluk icin en kucuk
    for x in a:
        k = bisect.bisect_left(kuyruk, x)
        if k == len(kuyruk):
            kuyruk.append(x)
        else:
            kuyruk[k] = x
        if izle:
            print(f"  x={x:2d} -> {kuyruk}")
    return len(kuyruk)


def kaba(a):
    best = 0
    for k in range(len(a) + 1):
        for alt in itertools.combinations(a, k):
            if all(alt[i] < alt[i + 1] for i in range(len(alt) - 1)):
                best = max(best, k)
    return best


```

Ana fonksiyon, `[3, 1, 4, 1, 5, 9, 2, 6]` dizisi için sabır izini yazdırır ve iki sürümün sonuçlarını karşılaştırır.

```python
def main():
    a = [3, 1, 4, 1, 5, 9, 2, 6]
    print("dizi:", a)
    print("sabir izi:")
    print("LIS (n^2):", lis_n2(a),
          " LIS (n log n):", lis_nlogn(a, True))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        x = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 9))]
        if not (lis_n2(x) == lis_nlogn(x) == kaba(x)):
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python lis.py
dizi: [3, 1, 4, 1, 5, 9, 2, 6]
sabir izi:
  x= 3 -> [3]
  x= 1 -> [1]
  x= 4 -> [1, 4]
  x= 1 -> [1, 4]
  x= 5 -> [1, 4, 5]
  x= 9 -> [1, 4, 5, 9]
  x= 2 -> [1, 2, 5, 9]
  x= 6 -> [1, 2, 5, 6]
LIS (n^2): 4  LIS (n log n): 4
300 rastgele ornek, hata: 0
```

İzde kuyruk dizisinin **uzunluğu** LIS uzunluğunu verir: 4'tür. Ama kuyruktaki değerler tek bir artan altdizi değildir. Son adımda kuyruk `[1, 2, 5, 6]` olur; fakat bu dizi bir altdizi değildir, çünkü `2`, `a`'da `5`'ten sonra gelir. Kuyruk, her uzunluk için ayrı ayrı "en küçük son" değerlerini tutar ve bu değerler farklı altdizilerden gelebilir. Gerçek LIS elemanlarını geri kurmak için her elemanın kuyruktaki önceki elemanını da kaydetmen gerekir; bu, geri izleme kalıbının aynısıdır.

Aşağıdaki şekil aynı izi sütunlar hâlinde gösterir; her satır bir eleman geldikten sonraki kuyruk dizisidir.

![Şekil 16.7: LIS sabır sıralaması, a = [3, 1, 4, 1, 5, 9, 2, 6]. Her satır bir eleman eklendikten sonraki kuyruk dizisidir; bordo kutu, o adımda değiştirilen ya da eklenen konumdur.](gorseller/b16_lis_sabir.png)

Sabır sıralamasında kuyruğun sıralı kalması, ikili aramanın doğruluğunun temelidir. Kuyruk her zaman kesin artan olduğu için `bisect_left` her seferinde doğru konumu bulur. Bu sıralılık değişmezi, Bölüm 14'teki döngü değişmezinin bir başka örneğidir.

Bu üç problemi bir arada görmek, DP'de sık görülen bir kalıbı açıklar: bir dizi üzerinde iki indeks ya da tek indeks ve bir yardımcı yapı (kuyruk, tablo, geri izleme dizisi). Sorunun hangi biçimde olduğunu tanımak, hangi tabloyu kuracağına karar vermenin ilk adımıdır.

## 16.9 Aralık DP: matris zinciri çarpımı

Şimdiye kadarki tablolarda alt problemler önekler (`a`'nın ilk `i` karakteri) ya da kapasiteler gibi tek boyutlu bir parametreyle tanımlanıyordu. Matris zinciri çarpımında alt problem bir **aralıktır**: `A_i, A_{i+1}, ..., A_j` matrislerinin çarpımı. Bu tür DP'ye aralık DP denir.

Problem şudur. Matrislerin çarpımı birleşmelidir ama değişmeli değildir: `(AB)C` ile `A(BC)` aynı sonucu verir, ama işlem maliyeti farklı olabilir. Bir `p × q` matrisi ile `q × r` matrisini çarpmak `p·q·r` skaler çarpım yapar. Dolayısıyla çarpma sırası, toplam maliyeti değiştirir. Örneğin `10 × 100` boyutlu `A`, `100 × 5` boyutlu `B` ve `5 × 50` boyutlu `C` için `(AB)C` önce `AB` (10·100·5 = 5000) sonra `(AB)C` (10·5·50 = 2500) yapar; toplam 7500 çarpma. `A(BC)` ise önce `BC` (100·5·50 = 25000), sonra `A(BC)` (10·100·50 = 50000) yapar; toplam 75000 çarpma. Aynı sonuç, on kat farklı maliyet.

Protokolü uygulayalım. `m[i][j]`, `A_i ... A_j` aralığını çarpmanın en az skaler çarpım sayısı olsun. Durum: bir aralık. Geçiş: aralığı `k` noktasından bölmek; sol parça `A_i..A_k`, sağ parça `A_{k+1}..A_j`, ve iki parçayı çarpmanın maliyeti `p[i] · p[k+1] · p[j+1]`. Yani `m[i][j] = min_k (m[i][k] + m[k+1][j] + p[i] · p[k+1] · p[j+1])`. Taban durum: tek matris (`i = j`) için maliyet 0'dır. Sıra: aralığın uzunluğu 2'den `n`'ye artan; çünkü `m[i][j]`'yi hesaplamak için daha kısa aralıklar gerekir.

Bu sıralama, aralık DP'nin özüdür: alt problemler uzunluklarına göre hesaplanır. Bir aralığın içindeki her bölünme, iki daha kısa aralığa bağlıdır, dolayısıyla uzunluk sırası doğru sıradır.

Aşağıdaki program, CLRS'nin klasik örneğini çözer: `p = [30, 35, 15, 5, 10, 20, 25]`, yani altı matris. Aynı zamanda bölme noktasını `s[i][j]` tablosunda saklar, böylece parantezlemeyi geri kurabilir.

```python
# matris.py: matris zinciri carpimi (aralik DP) ve kontrol
import random

INF = 10 ** 18


def matris_zinciri(p):
    # A_i (0 tabanli, ekranda A{i+1}): boyut p[i] x p[i+1]; len(p)=n+1
    n = len(p) - 1
    m = [[0] * n for _ in range(n)]   # m[i][j]: en az maliyet
    s = [[0] * n for _ in range(n)]   # s[i][j]: en iyi bolme noktasi
    for uzunluk in range(2, n + 1):
        for i in range(n - uzunluk + 1):
            j = i + uzunluk - 1
            m[i][j] = INF
            for k in range(i, j):
                q = m[i][k] + m[k + 1][j] + p[i] * p[k + 1] * p[j + 1]
                if q < m[i][j]:
                    m[i][j] = q
                    s[i][j] = k
    return m, s


def parantez(s, i, j):
    if i == j:
        return f"A{i + 1}"
    k = s[i][j]
    return f"({parantez(s, i, k)} x {parantez(s, k + 1, j)})"


```

```python
def tum_agaclar(p, i, j):
    # Tum parantezlemeleri (Catalan sayisi kadar) uretir:
    # (maliyet, ifade) ciftleri
    if i == j:
        return [(0, f"A{i + 1}")]
    sonuc = []
    for k in range(i, j):
        for c1, e1 in tum_agaclar(p, i, k):
            for c2, e2 in tum_agaclar(p, k + 1, j):
                c = c1 + c2 + p[i] * p[k + 1] * p[j + 1]
                sonuc.append((c, f"({e1} x {e2})"))
    return sonuc


```

Ana fonksiyon, yazdırılan en az maliyetin doğruluğunu, rastgele örneklerde tüm parantezlemeleri numaralandırarak kontrol eder. Altı matrisli bir zincirde parantezleme sayısı Catalan sayısıdır (`C_5 = 42`); bu yüzden kaba kuvvet küçük `n` için yeterince hızlıdır.

```python
def main():
    p = [30, 35, 15, 5, 10, 20, 25]     # A1..A6
    m, s = matris_zinciri(p)
    print("en az skaler carpim:", m[0][-1])
    print("parantezleme:", parantez(s, 0, len(p) - 2))
    rnd = random.Random(42)
    hata = 0
    for _ in range(200):
        n = rnd.randint(1, 6)
        q = [rnd.randint(1, 9) for _ in range(n + 1)]
        m, _ = matris_zinciri(q)
        en_az = min(c for c, _ in tum_agaclar(q, 0, n - 1))
        if n >= 1 and m[0][n - 1] != en_az:
            hata += 1
    print("200 rastgele ornek (tum agaclar), hata:", hata)


if __name__ == "__main__":
    main()
```

Programı çalıştırdık:

```term
$ python matris.py
en az skaler carpim: 15125
parantezleme: ((A1 x (A2 x A3)) x ((A4 x A5) x A6))
200 rastgele ornek (tum agaclar), hata: 0
```

Çıktıdaki en az maliyet `15125` ve parantezleme `((A1 x (A2 x A3)) x ((A4 x A5) x A6))`'dır. En dıştaki bölünme `A1..A3` ile `A4..A6` arasındadır; bu, `s[0][5]` hücresinde saklı `k = 2` değeridir (0 tabanlı indeks). Tablonun tamamı aşağıda.

![Şekil 16.8: Matris zinciri tablosu m[i][j], p = [30, 35, 15, 5, 10, 20, 25]. Satırlar ve sütunlar A1..A6; sağ üst köşe tüm zincirin maliyetidir (kırmızı çerçeve, 15125). Renkler aralık uzunluğuna göre: açık gri üçgenin altı kullanılmaz.](gorseller/b16_matris_aralik.png)

Tabloyu köşegen boyunca okumak en kolayıdır. Köşegenler uzunluğa göre dizilir: ilk köşegen tek matrislerdir (`0`), ikinci köşegen iki matrisli çarpımlardır (`15750`, `2625`, ...). Sağ üst köşe, en uzun aralıktır ve cevabı verir. Bir hücreyi hesaplamak için soldaki ve aşağıdaki hücrelere, yani daha kısa aralıklara bakarsın; bu, sıralamanın doğruluğunu görsel olarak gösterir.

Karmaşıklık, üç iç içe döngüden gelir: uzunluk (`n`), başlangıç (`n`) ve bölme noktası (`n`). Zaman `O(n^3)`, bellek `O(n^2)`'dir. `n = 6` için bu küçüktür, ama bin matrisli bir zincir için bu hesap pahalıdır. Derin öğrenmede benzer problemler tensör çarpım sıralamasında ortaya çıkar; `einsum` gibi araçlar bu sıralamayı otomatik seçmeye çalışır.

Matris zinciri, aralık DP'nin tipik şablonudur: bir dizinin bir parçasını (aralığı) durum olarak alırsın, bölme noktasını geçiş olarak seçersin ve hesabı uzunluk sırasıyla yaparsın. Bölüm 19'da (Divide & Conquer) aynı "böl ve birleştir" düşüncesini bir kez daha göreceksin; fark, orada alt problemlerin tekrar etmemesidir.

## 16.10 Sözde-polinomluk, DP'yi tanımak ve gerçek dünya

Sırt çantası çözümümüzün karmaşıklığı `O(nW)`'dir. Bu ifade, sayıya bakınca polinomdur gibi görünür; ama bir ayrım gerekir. `W` bir **değerdir**, girdinin uzunluğu değildir. Kapasiteyi `W` yazmak için yalnızca `log W` bit gerekir. Dolayısıyla `O(nW)`, girdi uzunluğu cinsinden üstel olabilir. Buna sözde-polinom (pseudo-polynomial) denir.

Rakamla bak: `n = 100` eşya ve `W = 10^9` kapasite için tablo `10^11` hücredir. Bu bellek ve süre açısından uygulanamaz. Girdi ise çok küçük: `W`'nin ikilik gösterimi 30 bit, değer ve ağırlıklar birkaç bitlik sayılar. `W`'ye yalnızca bir bit eklemek onu iki katına çıkarır ve tabloyu da yaklaşık iki katına çıkarır; girdinin uzunluğu ise bir bit artar.

Bu yüzden 0/1 sırt çantasının karar sürümü (değeri en az `V` olan bir seçim var mı?) NP-tamdır; Karp'ın 1972 listesinde yer alır. DP burada bir çözüm sağlar, ama genel bir polinom zamanlı çözüm değildir. Mülakatta bu soru geldiğinde "DP `O(nW)` ile çözer" demek yetmez: ayrıca "W girdinin uzunluğuna göre üstel" demen beklenir.

### DP'yi tanıma sinyalleri

DP sorularını tanımak, kod yazmaktan daha zordur. Aşağıdaki sinyaller, bir problemin DP olabileceğini gösterir; kesin bir kural değildir.

- Sorunun cevabı bir **en iyi değer** (en az, en çok) ya da bir **sayım** (kaç yol, kaç çözüm).
- Problem, **sıralı kararlardan** oluşur: her adımda bir seçim yapılır ve sonraki seçenekler öncekine bağlıdır.
- Girdi bir **dizi**, bir **aralık** ya da bir **kapasite** içerir ve alt problemler bu girdinin önekleri ya da alt aralıklarıdır.
- Aynı alt problem farklı yollarla tekrar tekrar gelir (16.1'deki ağaç).
- Açgözlü (greedy) bir seçim bazen yanlış sonuç verir; ama yanlışlığı bir karşı örnekle gösterebilirsen DP'ye geçmek doğru olabilir.

Son madde önemlidir. Açgözlü algoritma, her adımda en iyi görünen seçimi yapar. Bu hızlıdır, ama her problemde doğru değildir: 0/1 sırt çantasında en değerli-ağırlık oranlı eşyayı seçmek yanlış olabilir. Bölüm 18'de açgözlü algoritmanın ne zaman doğru olduğunu kanıtlamayı göreceksin; bu bölümdeki karşı örnek, DP'ye geçmenin gerekçesidir.

### Gerçek dünyada DP

DP, yalnızca ders kitabında kalan bir teknik değildir. Dört alanda doğrudan karşına çıkar.

**Diff ve sürüm kontrolü.** Git'te dosyalar arası farkı hesaplamanın temelinde LCS fikri vardır. Bir birleştirme (merge) sırasında hangi satırların iki tarafta da değiştiğini anlamak için kullanılan karşılaştırmalar da aynı ailedendir. Bölüm 38'de Git'i derinlemesine göreceksin; orada gördüğün `diff` çıktıları, bu bölümdeki LCS fikrine dayanır.

**Biyoinformatik.** İki DNA ya da protein dizisini hizalamak, DP'nin en büyük uygulamalarından biridir. Needleman–Wunsch, iki dizinin tamamını (global hizalama) hizalamak için edit distance'a benzer bir tabloyu kullanır; Smith–Waterman ise yalnızca en iyi yerel eşleşmeyi arar. Hizalama skoru, eşleşme, uyumsuzluk ve boşluk cezalarının toplamıdır; yani edit distance'ın ağırlıklı bir türüdür.

**Viterbi ve HMM.** Gizli Markov Modelinde (HMM), gözlemlenen bir dizinin en olası gizli durum dizisini bulmak için Viterbi algoritması kullanılır. Bu algoritma, durumlar üzerinden zamana bağlı bir tablo doldurur: her zaman adımı ve her durum için en olası önceki durumu tutar, sonunda geri izleme yapar. Yapısı, bu bölümdeki LCS ve sırt çantası tabloları ile aynıdır. Bölüm 62'de HMM'yi ve Viterbi'yi ayrıntılı göreceksin.

**Pekiştirmeli öğrenme.** Bir ajanın ödülünü en büyüten politikayı bulmak için Bellman denklemi kullanılır. Bir durumun değeri, o durumda en iyi eylemi seçtiğinde alınacak anlık ödülle, sonraki durumun (indirgenmiş, yani bir indirim katsayısıyla çarpılmış) değerinin toplamıdır. Bu denklem, bir DP geçişinin tam olarak aynısıdır: durum, geçiş ve hesaplama sırası. Bölüm 74'te (Pekiştirmeli Öğrenme) bu denklemden Q-learning ve policy gradient yöntemlerine geçeceğiz.

Bu dört örnekte ortak olan şey, problemin bir **alt problemler tablosu** olarak düşünülebilmesidir. Bu düşünce biçimini kazandığında, yeni bir problemle karşılaştığında önce durumunu tanımlayabilirsin ve Bölüm 16.2'deki protokol ile ilerlersin.

## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler örnekte verilen programın çıktısıyla aynıdır. Çözüm kodunu okumadan önce her örneğin ilk üç adımını kendi kâğıdında dene.

### Örnek 1 (★): Engelli ızgarada yol sayma

**Problem:** `n × m` boyutunda bir ızgara var. Boş hücreler `0`, engeller `1` ile gösterilir. Sol üst köşeden sağ alt köşeye, yalnızca sağa ya da aşağı hareket ederek kaç farklı yol var? Engelli hücreden geçilemez.

**Adım 1 — Anla.** Girdi bir 0/1 matrisidir; çıktı bir sayıdır. Kenar durumlar: başlangıç ya da bitiş hücresi engelli ise cevap 0'dır; tek hücrelik ızgarada cevap 1'dir (hücre boşsa).

**Adım 2 — Örnekle.** Bu örnekte kullanacağımız ızgara 4 × 4'tür:

```
0 0 0 0
0 1 0 0
0 0 0 1
1 0 0 0
```

Bu ızgarada üç yol vardır: `DDRDRR`, `DDRRDR` ve `RRDDDR` (`D` aşağı, `R` sağa). Yolların hiçbiri `(1,1)`, `(2,3)` ya da `(3,0)` hücrelerinden geçmez.

**Adım 3 — Kaba çöz.** Her hücrede iki seçenek var: sağa ya da aşağı. Tüm dalları özyinelemeyle dene ve hedefe ulaşanları say. Bu doğrudur, ama her çağrı iki dala ayrılır; derinlik `n + m - 2` olduğu için çağrı sayısının üst sınırı `2^(n+m-2)`'dir ve aynı hücreler birçok kez hesaplanır.

**Adım 4 — Örüntü.** `(i, j)` hücresine yalnızca yukarıdan ya da soldan gelinebilir. Bu yüzden `dp[i][j]`, `dp[i-1][j]` ve `dp[i][j-1]` toplamıdır; engelli hücrede `dp[i][j] = 0`. Taban: `dp[0][0] = 1` (boşsa). Bu, Bölüm 16.2'deki protokolün tam uygulamasıdır: durum, bağıntı, taban ve sıra.

**Adım 5 — İyileştir.** Hesabı satır satır, soldan sağa, yukarıdan aşağıya yap. Her hücre yalnızca daha önce hesaplanmış iki komşuya bakar; bu yüzden tek bir döngü yeter, toplam `O(nm)`. Programın ilk kısmı tabloyu üretir, ikinci kısmı kaba kuvvetle karşılaştırır.

```python
# ornek1.py: engelli izgarada yol sayisi (tabulation + kaba kuvvet)
import random


def yol_say(izgara):
    n, m = len(izgara), len(izgara[0])
    dp = [[0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            if izgara[i][j] == 1:           # engel: yol yok
                continue
            if i == 0 and j == 0:
                dp[i][j] = 1
                continue
            yukari = dp[i - 1][j] if i > 0 else 0
            sol = dp[i][j - 1] if j > 0 else 0
            dp[i][j] = yukari + sol
    return dp[n - 1][m - 1], dp


def kaba(izgara):
    n, m = len(izgara), len(izgara[0])
    def git(i, j):
        if i >= n or j >= m or izgara[i][j] == 1:
            return 0
        if (i, j) == (n - 1, m - 1):
            return 1
        return git(i + 1, j) + git(i, j + 1)
    return git(0, 0)


```

Ana fonksiyon sabit ızgarayı çözer, tabloyu yazdırır ve 300 rastgele ızgarada kaba kuvvetle eşleşmeyi doğrular.

```python
def main():
    izgara = [[0, 0, 0, 0],
              [0, 1, 0, 0],
              [0, 0, 0, 1],
              [1, 0, 0, 0]]
    sayi, dp = yol_say(izgara)
    print("yol sayisi:", sayi)
    for satir in dp:
        print(" ".join(f"{x:2d}" for x in satir))
    print("kaba kuvvet:", kaba(izgara))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n, m = rnd.randint(1, 5), rnd.randint(1, 5)
        g = [[1 if rnd.random() < 0.2 else 0 for _ in range(m)]
             for _ in range(n)]
        if yol_say(g)[0] != kaba(g):
            hata += 1
    print("300 rastgele izgara, hata:", hata)


if __name__ == "__main__":
    main()
```

**Adım 6 — Doğrula.** Programı çalıştırdık:

```term
$ python ornek1.py
yol sayisi: 3
 1  1  1  1
 1  0  1  2
 1  1  2  0
 0  1  3  3
kaba kuvvet: 3
300 rastgele izgara, hata: 0
```

Aşağıdaki tablo, `dp` matrisinin elle doldurulmuş hâlidir; satırlar `i` (0'dan 3'e), sütunlar `j` (0'dan 3'e). Programın çıktısıyla birebir aynıdır ve son hücre `3` yazar: Adım 2'deki üç yolla uyumlu.

| `i \ j` | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 |
| 1 | 1 | 0 (engel) | 1 | 2 |
| 2 | 1 | 1 | 2 | 0 (engel) |
| 3 | 0 (engel) | 1 | 3 | 3 |

Tablonun elle doğrulanması şöyle yapılır. İlk satırda hiçbir engel yok, bu yüzden her hücre 1'dir. İkinci satırda `(1,1)` engel olduğu için 0; `(1,2)`, `dp[0][2] + dp[1][1] = 1 + 0 = 1` ve `(1,3)`, `dp[0][3] + dp[1][2] = 1 + 1 = 2`. Son hücre `dp[3][3] = dp[2][3] + dp[3][2] = 0 + 3 = 3`'tür; `(2,3)` engelli olduğu için `0` alındı.

**Bunu AI'sız yazabilir misin?** Hareketlerin yalnızca sağa ve aşağı değil, dört yöne (sol ve sağ dahil) izinli olduğunu düşün. Bu durumda tablo bağıntısı neden çalışmaz? Hangi yapısal değişiklik (ör. bir döngü ya da ziyaret kümesi) gerekir?

### Örnek 2 (★★): Ev soygunu, dairesel varyant

**Problem:** Bir sokakta `n` ev var; her evin içinde `v_i` değerinde bir mal var. Komşu iki ev aynı gece soyulursa alarm çalar. Ev dizisi dairesel olsun: ilk ev ile son ev de komşudur. Alarm çalmadan en çok ne kadar mal alınabilir?

**Adım 1 — Anla.** Girdi negatif olmayan tamsayılar dizisidir. Kısıt: seçilen evlerin indeksleri arasında fark en az 2 olmalı ve ilk ile son birlikte seçilemez. Çıktı en büyük toplamdır. Kenar durum: `n = 1` ise tek ev alınabilir.

**Adım 2 — Örnekle.** `[2, 3, 2]` dairesel dizisinde ilk ve son ev komşudur. Doğrusal düşünürsek `2 + 2 = 4` (evler 0 ve 2) seçilebilir. Dairesel kısıtla bu yasaktır; en iyi seçim `3`'tür (yalnızca orta ev).

**Adım 3 — Kaba çöz.** Tüm `2^n` alt kümeyi dene, komşuluk kısıtını ve dairesellik kısıtını uygula, en büyük toplamı al. Doğru, ama `n` büyüdükçe kullanışsız.

**Adım 4 — Örüntü.** Doğrusal sürüm için `dp[i]`, `i`. eve kadar (dahil) olan evlerden alınabilecek en büyük toplamdır. Bağıntı: `dp[i] = max(dp[i-1], dp[i-2] + v_i)`; ya `i`. evi atlarsın, ya da alır ve `i-1`'i atlarsın. Dairesel durumda ilk ve son ev birlikte seçilemez; bu yüzden iki doğrusal problemin en büyüğünü alırız: ya ilk evi atlayıp `[1..n-1]`'i, ya son evi atlayıp `[0..n-2]`'yi çözeriz.

**Adım 5 — İyileştir.** Doğrusal DP yalnızca iki değişkenle tutulabilir (`onceki`, `simdiki`), bu yüzden bellek `O(1)`'dir. Dairesel sürüm iki doğrusal çağrının maksimumudur; toplam `O(n)`.

```python
# ornek2.py: ev soygunu, dairesel varyant (iki dogrusal DP)
import random


def dogrusal(degerler):
    onceki, simdiki = 0, 0          # iki onceki ve onceki sonuc
    for v in degerler:
        onceki, simdiki = simdiki, max(simdiki, onceki + v)
    return simdiki


def dairesel(degerler):
    n = len(degerler)
    if n == 1:
        return degerler[0]
    return max(dogrusal(degerler[:-1]), dogrusal(degerler[1:]))


def kaba(degerler, dairesel_mi):
    n = len(degerler)
    best = 0
    for mask in range(1 << n):
        secim = [i for i in range(n) if mask >> i & 1]
        ok = all(b - a > 1 for a, b in zip(secim, secim[1:]))
        if dairesel_mi and n > 1 and 0 in secim and n - 1 in secim:
            ok = False
        if ok:
            best = max(best, sum(degerler[i] for i in secim))
    return best


```

Ana fonksiyon `[2, 3, 2]` ve `[1, 2, 3, 1]` örneklerini çözer, rastgele 300 dizide kaba kuvvetle karşılaştırır.

```python
def main():
    evler = [2, 3, 2]
    print("dairesel [2,3,2]:", dairesel(evler))
    evler = [1, 2, 3, 1]
    print("dairesel [1,2,3,1]:", dairesel(evler))
    print("dogrusal [1,2,3,1]:", dogrusal(evler))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(1, 8)
        d = [rnd.randint(0, 20) for _ in range(n)]
        if dogrusal(d) != kaba(d, False):
            hata += 1
        if dairesel(d) != kaba(d, True):
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
```

**Adım 6 — Doğrula.** Programı çalıştırdık:

```term
$ python ornek2.py
dairesel [2,3,2]: 3
dairesel [1,2,3,1]: 4
dogrusal [1,2,3,1]: 4
300 rastgele ornek, hata: 0
```

`[2, 3, 2]` için iki doğrusal çağrının iz tablosu:

| Çağrı | Eleman `v` | `onceki` | `simdiki` (yeni) |
|---|---|---|---|
| `dogrusal([2, 3])` | 2 | 0 | 2 |
| | 3 | 2 | 3 |
| `dogrusal([3, 2])` | 3 | 0 | 3 |
| | 2 | 3 | 3 |

İki çağrı da 3 verir; dairesel cevap `max(3, 3) = 3`'tür. Aynı dizi için doğrusal çözüm `4` verir (`2 + 2`), ki bu dairesel kısıtta yasaktır. Bu fark, dairesel varyantın neden ayrı bir kontrol gerektirdiğini gösterir.

**Bunu AI'sız yazabilir misin?** `n = 1` durumunda kod neden ayrı bir dal içeriyor? `dairesel([v])` için `dogrusal(degerler[:-1])` ve `dogrusal(degerler[1:])` ikisi de boş dizi üzerinde çalışır mı, yoksa sonuç yanlış mı olur?

### Örnek 3 (★★): Kelime bölme ve geri kurma

**Problem:** Bir `s` dizgisi ve bir sözlük (kelime kümesi) verilsin. `s`'yi sözlükteki kelimelerin ardışık birleşimine bölebilir misin? Bölebiliyorsan, bir bölmeyi kelime listesi olarak döndür; bölemiyorsan `None` döndür.

**Adım 1 — Anla.** Girdi bir dizgi ve bir kümedir; çıktı bir liste ya da `None`'dır. Kenar durumlar: `s` boşsa bölme boş listedir; sözlükte hiçbir kelime `s`'nin başıyla eşleşmiyorsa `None`'dır. Geri kurma istendiği için yalnızca "var" demek yetmez.

**Adım 2 — Örnekle.** `s = "yazilimmuhendisligi"` ve sözlük `{yazi, yazilim, muhendis, ligi, li, gi}` için iki bölme vardır: `yazilim | muhendis | ligi` ve `yazilim | muhendis | li | gi`. `"yazilimx"` için bölme yoktur.

**Adım 3 — Kaba çöz.** `s`'nin başından her önekin sözlükte olup olmadığına bak; varsa kalanı özyinelemeyle böl. Bu, kesim noktalarının tüm kombinasyonlarını (`2^(n-1)` tane) dener.

**Adım 4 — Örüntü.** `dp[i]` = `s[:i]` bölünebilir mi? Bağıntı: `dp[i]` doğrudur, eğer bir `j < i` için `dp[j]` doğru ve `s[j:i]` sözlüktedir. Bölünebilirlik yetmez, geri kurmak için `j`'yi de saklamalısın: `kaynak[i] = j`. Böylece sondan başa giderek bölmeyi çıkarabilirsin.

**Adım 5 — İyileştir.** Tek bir `kaynak` dizisi hem "bölünebilir mi" bilgisini (`None` değil mi) hem de geri kurma bilgisini taşır. Her `i` için en fazla bir `j` tutulur: ilk bulunan. Döngüler `O(n^2)` denetim yapar; her denetim bir dilim oluşturduğu için pratikte biraz daha maliyetlidir.

```python
# ornek3.py: kelime bolme (word break) ve geri kurma
import random


def kelime_bol(s, sozluk):
    n = len(s)
    kaynak = [None] * (n + 1)   # kaynak[i]: s[:i] icin kesim noktasi
    kaynak[0] = -1              # bos onek bolunebilir
    for i in range(1, n + 1):
        for j in range(i):
            if kaynak[j] is not None and s[j:i] in sozluk:
                kaynak[i] = j
                break
    if kaynak[n] is None:
        return None, kaynak
    parcalar, i = [], n
    while i > 0:
        j = kaynak[i]
        parcalar.append(s[j:i])
        i = j
    return parcalar[::-1], kaynak


def tum_bolmeler(s, sozluk):
    if s == "":
        return [[]]
    sonuc = []
    for i in range(1, len(s) + 1):
        if s[:i] in sozluk:
            for kalan in tum_bolmeler(s[i:], sozluk):
                sonuc.append([s[:i]] + kalan)
    return sonuc


```

Ana fonksiyon örneği çözer, erişilebilir `kaynak` değerlerini yazdırır ve 300 rastgele küçük sözlükte kaba kuvvet ile karşılaştırır.

```python
def main():
    sozluk = {"yazi", "yazilim", "muhendis", "ligi", "li", "gi"}
    s = "yazilimmuhendisligi"
    parcalar, kaynak = kelime_bol(s, sozluk)
    print("bolme:", parcalar)
    erisim = {i: k for i, k in enumerate(kaynak) if k is not None}
    print("kaynak:", erisim)
    print("yok:", kelime_bol("yazilimx", sozluk)[0])
    rnd = random.Random(42)
    harfler = "abc"
    hata = 0
    for _ in range(300):
        sz = {"".join(rnd.choice(harfler)
                      for _ in range(rnd.randint(1, 3)))
              for _ in range(rnd.randint(1, 5))}
        t = "".join(rnd.choice(harfler)
                    for _ in range(rnd.randint(0, 8)))
        p, _ = kelime_bol(t, sz)
        var = len(tum_bolmeler(t, sz)) > 0
        if (p is not None) != var:
            hata += 1
        if p is not None and ("".join(p) != t or
                              any(w not in sz for w in p)):
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
```

**Adım 6 — Doğrula.** Programı çalıştırdık:

```term
$ python ornek3.py
bolme: ['yazilim', 'muhendis', 'ligi']
kaynak: {0: -1, 4: 0, 6: 4, 7: 0, 15: 7, 17: 15, 19: 15}
yok: None
300 rastgele ornek, hata: 0
```

Programın yazdırdığı `kaynak` sözlüğü (`{0: -1, 4: 0, 6: 4, 7: 0, 15: 7, 17: 15, 19: 15}`) erişilebilir indeksleri verir. Bunu iz tablosu olarak düzenledik:

| `i` | `kaynak[i]` | `s[kaynak[i]:i]` | Anlamı |
|---|---|---|---|
| 0 | -1 | (boş) | Boş önek bölünebilir |
| 4 | 0 | `yazi` | `s[:4]` bir kelime |
| 6 | 4 | `li` | `s[:6]` = yazi + li |
| 7 | 0 | `yazilim` | `s[:7]` bir kelime |
| 15 | 7 | `muhendis` | `s[:15]` = yazilim + muhendis |
| 17 | 15 | `li` | `s[:17]` = ... + li |
| 19 | 15 | `ligi` | Tüm dizgi |

Geri kurma son satırdan başlar: `19 → 15` (`ligi`), `15 → 7` (`muhendis`), `7 → 0` (`yazilim`). Okunuşu tersten yapınca `yazilim | muhendis | ligi` çıkar. Programın çıktısı da aynı bölmeyi verdi. Dikkat: `19`'a `17` üzerinden de ulaşılabilir (`s[17:19] = gi`, `kaynak[17] = 15`), ama `kaynak` her `i` için yalnızca ilk bulunan `j`'yi tutar. Bu yüzden program tek bir bölme döndürür; ikinci bölme `yazilim | muhendis | li | gi` de geçerlidir. Tek bir bölme bulmak ile tüm bölmeleri listelemek farklı sorulardır.

**Bunu AI'sız yazabilir misin?** `kaynak[i]` her `i` için tek bir `j` tutuyor. Tüm olası bölmeleri listelemek istesen, bu yapıyı nasıl değiştirirsin? Ve bölme sayısını (kaç farklı bölme var?) bulmak için `kaynak` yerine hangi dizi gerekir?

### Örnek 4 (★★★): Yazım denetimi: en yakın sözcükler ve işlem dizisi

**Problem:** Kullanıcının yazdığı bozuk bir sözcük (`kitp`) ve bir sözlük verilsin. En yakın üç sözcüğü, düzenleme mesafeleriyle birlikte bul; en yakın sözcüğe giden düzenleme işlemlerini de yaz. Düzenleme işlemleri ekleme, silme ve değiştirmedir; her biri 1 birim maliyetlidir.

**Adım 1 — Anla.** Girdi bir dizgi ve bir sözcük listesidir; çıktı üç çift `(mesafe, sözcük)` ve bir işlem dizisidir. Kenar durumlar: girdi boşsa mesafe sözcük uzunluğudur; sözcük girdiyle aynıysa mesafe 0'dır ve işlem listesi yalnızca eşleşmelerden oluşur.

**Adım 2 — Örnekle.** `kitp` ile sözlük `kitap, kapi, kopya, kedi, kitle, kapak` için mesafeler: `kitap` 1, `kitle` 2, `kapi` 3. En yakın `kitap`'a giden tek işlem `a` eklemektir.

**Adım 3 — Kaba çöz.** Her sözcük için rekürsif bir `mesafe(i, j)` fonksiyonu yaz; üç seçeneği (değiştir, sil, ekle) dene. Bu, her çağrının üç çağrıya dallandığı bir ağaç üretir; aynı `(i, j)` çiftleri tekrar tekrar hesaplanır.

**Adım 4 — Örüntü.** Bu, Bölüm 16.8'deki tablonun aynısıdır. `dp[i][j]`, `kitp`'nin ilk `i` karakterinin, sözcüğün ilk `j` karakterine dönüşmesinin maliyetidir. Geri izleme için her hücrede hangi seçeneğin geçerli olduğunu bilmek gerekir: eşleşme, değiştirme, silme ya da ekleme.

**Adım 5 — İyileştir.** Her sözcük için bir tablo doldurulur. Üç komşu hücreye bakılır; geri izleme ise tablo üzerinde ters yönde yürür. Her sözcük için `O(nm)` iş vardır; sözlük `k` sözcükse toplam `O(k · nm)`.

```python
# ornek4.py: yazim denetimi, en yakin sozcukler ve islem dizisi
def mesafe_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j],
                                   dp[i][j - 1])
    return dp


def islemler(a, b, dp):
    i, j, adim = len(a), len(b), []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            adim.append(f"{a[i - 1]}->{b[j - 1]}")
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            adim.append(f"sil {a[i - 1]}")
            i -= 1
        else:
            adim.append(f"ekle {b[j - 1]}")
            j -= 1
    return list(reversed(adim))


```

Ana fonksiyon her sözcük için tabloyu hesaplar, mesafeye göre sıralar, ilk üçü yazdırır ve en iyi adayın tablosunu gösterir.

```python
def main():
    sozluk = ["kitap", "kapi", "kopya", "kedi", "kitle", "kapak"]
    girdi = "kitp"
    adaylar = []
    for w in sozluk:
        dp = mesafe_tablo(girdi, w)
        adaylar.append((dp[-1][-1], w, dp))
    adaylar.sort()
    for d, w, dp in adaylar[:3]:
        print(f"{girdi} -> {w}: mesafe {d}")
    d, w, dp = adaylar[0]
    print("islemler:", islemler(girdi, w, dp))
    print("tablo (en iyi aday):")
    for satir in dp:
        print(" ".join(f"{x:2d}" for x in satir))


if __name__ == "__main__":
    main()
```

**Adım 6 — Doğrula.** Programı çalıştırdık:

```term
$ python ornek4.py
kitp -> kitap: mesafe 1
kitp -> kitle: mesafe 2
kitp -> kapi: mesafe 3
islemler: ['ekle a']
tablo (en iyi aday):
 0  1  2  3  4  5
 1  0  1  2  3  4
 2  1  0  1  2  3
 3  2  1  0  1  2
 4  3  2  1  1  1
```

`kitp` ile `kitap` arasındaki tablo (satırlar `kitp`, sütunlar `kitap`):

| | `""` | `k` | `i` | `t` | `a` | `p` |
|---|---|---|---|---|---|---|
| `""` | 0 | 1 | 2 | 3 | 4 | 5 |
| `k` | 1 | 0 | 1 | 2 | 3 | 4 |
| `i` | 2 | 1 | 0 | 1 | 2 | 3 |
| `t` | 3 | 2 | 1 | 0 | 1 | 2 |
| `p` | 4 | 3 | 2 | 1 | 1 | 1 |

Son hücre 1'dir. Son satırda `p` ile `p` eşleşir (`dp[4][5] = dp[3][4] = 1`), yani sondan başlayan geri izleme köşegenden gider ve `a` için bir ekleme işlemi üretir. Tablonun köşegeni `k`, `i`, `t` eşleşmelerini gösterir ve sıfırlarla ilerler. İşlem listesi `ekle a` olarak çıktı.

**Bunu AI'sız yazabilir misin?** Ekleme ve silme maliyetini 1 yerine 2 yapsaydın, `dp` bağıntısında neyi değiştirirdin? Değiştirme ile sil-ekle çiftinin maliyeti eşit olduğunda hangi işlem geri izlemede tercih edilir ve bu neden önemli olabilir?

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. DP'nin asıl eğitimi, tabloyu kendi elinle kurmak ve kendi hatanı bulmaktır. Bir aracın yazdığı tablo doğru görünse bile, sınır durumlarını (boş girdi, tek eleman, tüm eşitler) sen test etmedikçe bilmiyorsun.
:::

### Proje 1 (★★): Kendi `diff` aracın

**Amaç:** İki metin dosyasını satır satır karşılaştıran ve farkı `+` (eklenen) ve `-` (silinen) satırlarla yazdıran bir komut satırı aracı yazmak. Karşılaştırmanın çekirdeği LCS olacak: ortak satırların en uzun altdizisi, değişmeyen satırları verir; geri kalanlar değişikliktir.

**Yapılacak / Beklenen davranış:**

1. Dosyaların satırlarını oku ve her satırı bir "sembol" olarak ele al. Satır sonu karakterlerini (`\r\n` ve `\n`) önce normalize et; Windows'ta bu fark sahte değişiklik üretir.
2. Satırlar arasında LCS tablosunu doldur ve geri izleyerek ortak satırları bul.
3. LCS'e girmeyen eski satırları `-`, yeni satırları `+` ile yazdır. Sıra, dosyadaki sırayı korumalı.
4. Tek bir dosya boş olabilir; iki dosya da aynıysa çıktı boş olmalı; bir dosya tamamen yeniyse tüm satırlar `+` olmalı.
5. Aynı girdiler için GNU `diff --minimal` ile karşılaştır.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Bölüm 16.8'deki LCS tablosunu satırlar üzerinde kur; `a` ve `b` artık karakter değil, satır dizileridir. Geri izlemeyi, yazdırma sırasını koruyacak şekilde yap. Bellek ihtiyacı `O(nm)` satır sayısına bağlıdır; büyük dosyalarda bu bir sorundur. Bu sorunu çözmek için Bölüm 16.5'teki Hirschberg fikrini araştırabilirsin, ama önce küçük dosyalarla doğru çalıştığından emin ol. Tablo değerlerini yazdırıp Bölüm 16.8'deki şekille karşılaştır.

**Başarı kriterleri:**

- 300 satırlık rastgele iki dosyada (tohum `42`), çıkan `+` ve `-` satır sayıları toplamı `diff --minimal` ile aynıdır.
- Boş dosya, tek satırlık dosya ve tamamen aynı dosyalar için çıktı elle beklediğinle birebir eşleşir.
- Çalışma süresi 2000 satırlık dosyada bir saniyenin altındadır (ölç, tahmin etme).
- Kodda tüm tablo bağıntısı tek bir fonksiyonda toplanmıştır ve her satırda ne yaptığını açıklayan bir yorum vardır.

### Proje 2 (★★★): Batarya enerji bütçesi: sırt çantası

**Amaç:** EV Dashboard'a benzer bir sistemde, bir batarya şarjı içinde en çok faydayı sağlayan görev kümesini seçen bir planlayıcı yazmak. Her görevin (sensör okuma, veri gönderimi, ısıtma, kalibrasyon) bir enerji maliyeti ve bir fayda değeri vardır; bütçe bir enerji miktarıdır.

**Yapılacak / Beklenen davranış:**

1. Enerjiyi tam sayı birimlerle (ör. `0.1 Wh`) temsil et; kayan nokta bütçesi DP'de sorun çıkarır.
2. 0/1 sırt çantasıyla her görevin en fazla bir kez çalışmasını sağla. En büyük faydayı ve seçilen görevleri döndür.
3. İkinci bir mod ekle: aynı görev birden fazla kez çalışabilsin (sınırsız sırt çantası). Bu iki modu tek bir programda seçilebilir yap.
4. Bütçe 0 ve görev listesi boş olduğunda sonuç 0 olmalı; hiçbir görev bütçeye sığmıyorsa sonuç 0 ve seçilen görev listesi boş olmalı.
5. 20 görevli bir örnekte kaba kuvvetle (`2^20`, yani bir milyondan fazla altküme; süreyi ölç) karşılaştır.

**Önerilen yaklaşım (ipucu):** Bölüm 16.4'te gördüğün tek boyutlu tabloyla başla; sonra geri kurma gerektiğinde tam tabloya (Bölüm 16.5) geç. Kapasiteyi `W` birim olarak düşün: her enerji birimi bir kapasite birimidir. Sınırsız mod için döngü yönünü değiştirmenin neyi değiştirdiğini kendi testinde göster. Bütçe büyüdüğünde bellek ve süre nasıl büyüyor? Bunu tabloyla ölç.

**Başarı kriterleri:**

- 300 rastgele küçük örnekte (tohum `42`), DP sonucu kaba kuvvetle eşleşir; her iki mod için de.
- Seçilen görev listesinin toplam enerjisi bütçeyi aşmaz ve toplam faydası DP sonucuna eşittir. Bu iki kontrol birbirinden bağımsız yazılmalıdır.
- Bütçe `W = 10^4` birim ve `n = 100` görev için çalışma süresi ölçülmüş ve raporlanmıştır; sonuç "sözde-polinom" tartışmasıyla (Bölüm 16.10) yorumlanmıştır.

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün; son çare olarak kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ `fib(n)`'i yalnızca iki değişkenle, `O(n)` zamanda hesapla. Bu sürüm Bölüm 16.3'teki tablodan hangi açıdan farklıdır? (Mülakat)
2. ★ Merdiven problemini 1, 2 ve 3 basamak atlama için genelleştir. Taban durumlarını yazmadan önce `dp[0]`'ın anlamını bir cümleyle tanımla.
3. ★ Para bozmada en az madeni para sayısını ve bu sayıyı veren madeni paraların listesini geri kur. Tutarın kendisi için birden fazla çözüm varsa hangisini döndüreceğine karar ver ve bunu açıkla. (Mülakat)
4. ★★ 0/1 sırt çantasında yalnızca tek bir satır tutarak en iyi değeri hesaplayabilirsin; ama seçilen eşyaları bu tek satırla geri kuramazsın. Nedenini bir örnekle göster.
5. ★★ Sınırlı sırt çantasında her eşyanın en fazla `k_i` kez alınabildiğini düşün. Eşyayı `k_i` ayrı kopya olarak yazmak yerine, ikilik bölmeyle (1, 2, 4, ... kopya) kaç yeni eşya gerekir? (Mülakat)
6. ★★ Bir `s` dizgisinin en uzun palindrom altdizisinin uzunluğunu, `s` ile `reverse(s)` arasındaki LCS olarak hesapla. Bu eşitliği küçük örneklerde kaba kuvvetle doğrula. (Mülakat)
7. ★★ Edit distance'da yalnızca ekleme ve silme izinli olsun (değiştirme yok). Bu mesafenin LCS ile ilişkisini kur ve `m + n - 2 * LCS` formülünü küçük örneklerde doğrula.
8. ★★ "Ev soygunu" problemini ağaç üzerinde çöz: her ev bir düğüm, komşuluk kenarları ağacın kenarlarıdır. Her düğüm için "alındı" ve "alınmadı" durumlarını tanımla ve bağıntıyı yaz. (Mülakat)
9. ★★ Bir `n × m` ikili matriste yalnızca 1'lerden oluşan en büyük kareyi `O(nm)` ile bul. Bu, Bölüm 16.2'deki altı adımla nasıl eşleşir? (Mülakat)
10. ★★ Bir dizide en uzun bitonik altdizi (önce artan, sonra azalan) uzunluğunu bul. Hangi iki LIS hesabını birleştirmen gerektiğini açıkla.
11. ★★★ Matris zinciri için `n = 40` matrisli rastgele boyutlarda, tüm parantezlemeleri sayan bir fonksiyon yaz. Tahminin neden tutmayacağını Catalan sayısıyla açıkla. (Mülakat)
12. ★★★ Bir `s` dizgisinin en az kaç karakter eklenerek palindrom yapılabileceğini bul. Cevabın `n - LPS(s)` olduğunu kanıtlamaya çalış ve küçük örneklerde doğrula.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10'un standart kütüphanesindeki `Lib/difflib.py` dosyası. Kaynak, `v3.12.10` etiketinden alındı (`https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/difflib.py`). Aşağıdaki kesit, `SequenceMatcher.find_longest_match` yönteminin içinden, dosyanın 368–388. satırlarıdır. Yorumlar dahil birebir kopyalandı; yalnızca iki uzun yorum satırı, sayfa genişliği için ikiye bölündü; bölünen parçaların başına yalnızca `#` eklendi, başka hiçbir karakter değiştirilmedi.

Bu kesit, iki satır arasındaki en uzun ortak **ardışık** eşleşmeyi bulur; yani LCS (altdizi) değil, ortak altdizge (substring) arar. Dinamik programlamanın bir biçimidir: `j2len`, bir önceki `i` satırının değerlerini tutar ve her `i` için yalnızca eşleşen `j`'ler üzerinde güncellenir.

```python
        besti, bestj, bestsize = alo, blo, 0
        # find longest junk-free match
        # during an iteration of the loop, j2len[j] =
        # length of longest
        # junk-free match ending with a[i-1] and b[j]
        j2len = {}
        nothing = []
        for i in range(alo, ahi):
            # look at all instances of a[i] in b; note that because
            # b2j has no junk keys, the loop is skipped if
            # a[i] is junk
            j2lenget = j2len.get
            newj2len = {}
            for j in b2j.get(a[i], nothing):
                # a[i] matches b[j]
                if j < blo:
                    continue
                if j >= bhi:
                    break
                k = newj2len[j] = j2lenget(j-1, 0) + 1
                if k > bestsize:
                    besti, bestj, bestsize = i-k+1, j-k+1, k
            j2len = newj2len
```

**Sorular — cevaplamadan geçme:**

1. `j2len` bir dizi değil bir sözlüktür. Bu seçim, `b2j` ile birlikte hangi girdilerde bellek ve zaman kazandırır? Hangi girdide bu bir kazanç olmaz?
2. Döngüde `newj2len` her `i` için yeniden oluşturulur, sonra `j2len = newj2len` ile değiştirilir. Bu, Bölüm 16.4'teki yuvarlanan dizi fikriyle hangi açıdan aynıdır, hangi açıdan farklıdır?
3. `k = newj2len[j] = j2lenget(j-1, 0) + 1` satırında `j-1` neden kullanılır? LCS tablosundaki `dp[i-1][j-1] + 1` ile bu satırı karşılaştır: eşleşmeyen durumda LCS neden `max` alır, burada ise hücre neden sıfırlanır (yani sözlükte hiç yazılmaz)?
4. Belgelendirme metni, aynı uzunlukta birden fazla eşleşme varsa `a`'da en erken başlayanın döndürüldüğünü söyler. Bu tie-break kuralı için kodda hangi satır sorumludur ve `k > bestsize` (`>=` değil) neden önemlidir?
5. `autojunk` ve popüler öğe mantığı (`__chain_b`) `len(b) >= 200` için devreye girer. Bu eşiğin üzerinde en uzun eşleşme neden tam olarak doğru olmayabilir? Bunu kısa bir örnekle göster; sonucu `SequenceMatcher(None, a, b, autojunk=False)` ile karşılaştır.
6. (Mülakat) Bu kesitin en kötü durum karmaşıklığı nedir? İki dizgi de tek bir karakterden oluşuyorsa ne olur? Bunu, `b2j` listelerinin uzunluğu cinsinden yaz.

## Bölüm Özeti

Bu bölümde dinamik programlamayı bir teknik olarak değil, bir düşünme protokolü olarak öğrendik:

- DP, **örtüşen alt problemler** ve **optimal alt yapı** koşullarının ikisi birden sağlandığında uygulanır. En uzun basit yol, ikinci koşulu sağlamadığı için tabloya dökülemez.
- Protokol altı sorudan oluşur: durum (bir cümleyle), geçiş, taban, sıra, cevabın yeri ve maliyet. Durumu cümleyle tanımlayamıyorsan kod yazma.
- **Memoization** üstten alta ve yığın kullanır; **tabulation** alttan üste ve döngüyle çalışır. Python'da memo derinlik sınırına (varsayılan 1000) takılır; tablo takılmaz.
- Bellek yalnızca bir önceki satıra bağlıysa tek boyuta indirilir; 0/1 sırt çantasında kapasiteler **büyükten küçüğe** taranmalıdır, aksi halde eşya tekrar alınır.
- Geri izleme, değerin yanında seçimleri de verir; bunun için tam tablo gerekir ya da bölme-fethetme ile bellek ödünleşilir.
- Sayma (toplam) ve en iyileme (min/max) aynı protokolü kullanır; döngü sırası, kombinasyon ve permütasyon sayımını belirler.
- Sırt çantası ailesi (0/1, sınırsız, çubuk kesimi) bir kapasite ve öğeler üzerinde çalışır. `O(nW)` sözde-polinomdur; girdi uzunluğu cinsinden üstel olabilir.
- Dizi DP'leri (LCS, edit distance, LIS) iki diziyi ya da bir diziyi tabloyla hizalar; LIS'in `O(n log n)` sürümü sabır sıralamasıdır ve ikili aramaya dayanır.
- Aralık DP (matris zinciri) alt problemleri aralıklar olarak tanımlar ve hesabı uzunluk sırasıyla yapar.

**Sonraki bölümde:** Bu bölümde tabloları sıralı alt problemler üzerinde kurduk. Bölüm 17'de (Graph Algoritmaları) problem bir grafa dönüşür: BFS ve DFS ile dolaşmayı, Dijkstra ve Bellman-Ford ile en kısa yolu, Kruskal ve Prim ile minimum örten ağacı öğreneceğiz. Topolojik sıralama, bu bölümde gördüğümüz DAG'ın hesaplama sırası olduğunu ortaya çıkaracak.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir problemin DP ile çözülebilmesi için hangi iki koşul gerekir? Her birinin sağlanmadığını gösteren bir örnek ver.
2. Memoization ile tabulation arasında ne zaman birini diğerine tercih edersin? Yığın derinliği ve gereksiz durumlar bu kararı nasıl etkiler?
3. 0/1 sırt çantasında kapasiteleri neden büyükten küçüğe taramalısın? Yanlış yönde taranırsa hangi problem çözülmüş olur?
4. Sözde-polinom ne demektir? `O(nW)` ifadesinin neden girdi uzunluğu cinsinden üstel olduğunu bir sayıyla açıkla.
5. LCS ile en uzun ardışık ortak altdizgi arasındaki fark nedir? Hangisi `diff` için doğru tanımdır ve neden?
6. LIS'in `O(n log n)` sabır sıralaması kuyruk dizisini geri kurmadan neden yalnızca uzunluğu verir? Gerçek LIS'i geri kurmak için ne eklenmelidir?
7. Matris zinciri çarpımında iki parantezleme aynı sonucu verir ama maliyetleri farklıdır. Bu bir DP probleminin ne tür bir alt yapısını gösterir?
8. Açgözlü algoritma bir problemde doğru çalışıyor gibi görünüyorsa, DP'ye geçmeden önce hangi karşı örneği aramalısın?
:::
