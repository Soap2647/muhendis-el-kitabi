
## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Ölçüm kodu ve karmaşıklık tahmini, ancak kendi elinle yazdığında gerçekten öğrenilir. Bir ölçüm sonucu beklediğinden farklı çıktığında nedenini bulmak, bu bölümün asıl eğitimidir.
:::

### Proje 1 (★★): Karmaşıklık dedektifi

**Amaç:** Verilen bir fonksiyonun girdi boyutuna göre çalışma süresini ölçen ve log-log eğiminden büyüme sınıfını tahmin eden bir araç yazmak. Araç, 12.10'daki protokolü uygulasın.

**Yapılacak / Beklenen davranış:**

1. Bir `olc(fonk, boyutlar, tekrar)` fonksiyonu yaz. Her `n` için girdi üretici bir fonksiyonla bir test verisi oluştur, `fonk`'u çalıştır ve en iyi süreyi al.
2. Log-log doğrusunun eğimini en küçük kareler ile hesapla ve ekrana yazdır.
3. Eğime göre basit bir sınıflandırma yap: `0,2` altı sabit, `0,8`–`1,2` doğrusal, `1,8`–`2,2` karesel gibi aralıklar kullan. Aralıkları kendi denemelerinle gerekçelendir.
4. Altı bilinen fonksiyonla test et: sabit zamanlı sözlük araması, doğrusal toplam, `sorted`, iç içe karşılaştırma, ikili arama (`bisect`), iki iç içe döngüden oluşan bir üçlü sayaç.

**Önerilen yaklaşım:** Ölçüm için `time.perf_counter()` kullan ve her ölçümü birkaç kez tekrarla. Sabit tohumla (`random.seed(42)`) veri üret, böylece iki koşu arasında veri değişmesin. Doğrusal ve `n log n` farkını görmek için `n`'i en az üç büyüklük mertebesi boyunca değiştir. Sabit yükün küçük `n`'lerde eğimi bozduğunu gözlemlersen, en küçük `n` değerini artır.

**Başarı kriterleri:**

- Altı fonksiyonun en az beşinde tahmin edilen sınıf, beklenen sınıfla eşleşir.
- Her ölçüm için makine bilgisi, Python sürümü ve tohum çıktıda yazılıdır.
- Aynı programın iki koşusunda eğimler `0,05`'ten fazla farklı çıkmaz.
- Sözlük araması için eğimin neden sıfırdan farklı çıktığını önbellek ile açıklayan bir paragraf yazılır.

### Proje 2 (★★★): Büyüme stratejisi simülatörü

**Amaç:** Dinamik dizide kapasite büyüme stratejisinin (`+1`, `×1,5`, `×2`) ekleme başına toplam kopyalama maliyetini simüle etmek ve sonucu amortize analizle karşılaştırmak. Bir de "küçülme" (shrink) stratejisinin neden dikkatli seçilmesi gerektiğini göstermek.

**Yapılacak / Beklenen davranış:**

1. Bir `DinamikDizi` sınıfı yaz. Büyüme çarpanını kurucu parametre olarak al. Ekleme (`ekle`) ve kopyalama sayacı tut.
2. `n = 10³, 10⁴, 10⁵` ekleme için her üç stratejinin toplam kopyalama sayısını ve ekleme başına ortalamasını tablola.
3. `+1` stratejisinin ortalamasının `n` ile doğrusal büyüdüğünü, `×2` stratejisinin ise sabit kaldığını grafikle göster.
4. Küçülme ekle: eleman silindiğinde kapasiteyi yarıya indir. Bir sekanslı ekle-sil-ekle-sil dizisi kur ve her işlemin kopyalama sayısını say. Dolu/boş eşiğini değiştirerek "titreme" (thrashing) davranışını gözlemle.

**Önerilen yaklaşım:** Kopyalama sayacını yalnızca yeniden tahsis sırasında artır; gerçek bellek tahsisi yapmana gerek yok. Küçülme için kapasiteyi yarıya indirmek yerine, boy kapasitenin dörtte birine düştüğünde yarıya indirmek, titreme sorununu nasıl çözdüğünü gözlemle. Sonucu amortize potansiyel `Φ` ile açıklamaya çalış: ekleme ve silme için ayrı ayrı `Φ` tanımlayabilir misin?

**Başarı kriterleri:**

- `+1` stratejisi için `n = 10⁵`'te ekleme başına ortalama kopyalama `n/2`'ye yakın çıkar; `×2` için `2`'nin altındadır.
- Titreme senaryosunda, eşik seçimini yanlış yaptığında toplam kopyalama sayısının `O(n)`'den `O(n²)`'ye çıktığını gösteren bir tablo vardır.
- Her ölçüm için tohum ve test dizisi yazılıdır; kod WSL içinde `-fsanitize=address,undefined` ile de çalıştırılır (C kullanırsan).

### Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kendin düşün, sonra kâğıtta analiz yap, en son gerekirse ölçümle doğrula.

1. ★ `for (i = n; i > 1; i /= 3)` döngüsünün tur sayısını `n` cinsinden bul. Tabanın büyüme sınıfına etkisini açıkla.
2. ★ `for i in 1..n` ve `for j in 1..n` iç içe döngülerinde yalnızca `i·j ≤ n` olduğunda gövde çalışsın. Gövde sayısını `Σ ⌊n/i⌋` olarak yaz ve büyüme sınıfını söyle. (Mülakat)
3. ★★ Bir `f(n) = f(n−1) + f(n−2)` özyinelemesinin (naif Fibonacci) neden üstel büyüdüğünü, çağrı ağacının seviyelerini sayarak açıkla. Bu yapıyı Bölüm 16'daki dinamik programlama ile nasıl hızlandırırsın? (Mülakat)
4. ★★ `T(n) = 3T(n/3) + n` bağıntısını Master Teoremi ile çöz; hangi durumda olduğunu ve `c` değerini belirt.
5. ★★ `T(n) = 4T(n/2) + n` ve `T(n) = 4T(n/2) + n²` bağıntılarını karşılaştır. Hangisinin daha hızlı büyüdüğünü ve neden olduğunu Master Teoremi'nin `c` değeriyle açıkla. (Mülakat)
6. ★★ Sıralı olmayan bir dizide iki elemanın toplamının `k` olduğu bir çift olup olmadığını sor. Naif çözümün ve sıralama + iki işaretçi çözümünün karmaşıklığını karşılaştır. (Mülakat)
7. ★★ Dinamik dizi büyüme çarpanı `1,5` ise, amortize maliyetin sabit kalması için potansiyel `Φ = c·boy − kapasite` biçimindeki bir fonksiyonun `c` katsayısını bul.
8. ★★ Sıralı bir dizide tekrar eden değerleri yerinde silen algoritmanın zaman ve uzay karmaşıklığını yaz. Yardımcı bellek kullanıp kullanmadığını açıkla. (Mülakat)
9. ★★★ `Σ_{i=1}^{n} ⌊n/i⌋ = Θ(n log n)` olduğunu kanıtla. İpucu: harmonik toplamı `n · Hₙ` ile sınırla, `⌊x⌋ ≤ x` ve `x − 1 < ⌊x⌋` kullan. (Mülakat)
10. ★★★ Bağlı listede birleştirmeli sıralamanın (merge sort) yardımcı belleğinin neden `O(1)` yapılabildiğini, dizi sürümünün ise `O(n)` gerektirdiğini açıkla.
11. ★★★ Her `push`, `pop` ve `min` işleminin `O(1)` olduğu bir yığın tasarla. Min'i tutmanın bellek maliyeti nedir, bu maliyet hangi durumda kabul edilemez hâle gelir? (Mülakat)
12. ★★★ Bir min-heap'te bir elemanın değerini azaltmak (decrease-key) neden en kötü durumda `O(log n)`'dir? Değeri artırmakta ise durum nasıldır? Bölüm 10.7'deki sift-up ve sift-down'u kullanarak açıkla.

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir kaynağı okuyacaksın: CPython 3.12.10'un standart kütüphanesindeki `bisect.py` dosyası. Dosya, GitHub'daki `python/cpython` deposunun `v3.12.10` etiketinden indirildi ve yerel Python 3.12.10 kurulumundaki `Lib\bisect.py` ile birebir aynı olduğu doğrulandı. Aşağıdaki kesitlerde docstring'ler, yorumlar ve `key` parametresi için olan dallar çıkarılmıştır; kalan satırlar kaynaktan birebir alınmıştır.

Önce ikili arama yapan `bisect_right`:

```python
def bisect_right(a, x, lo=0, hi=None, *, key=None):
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid]:
                hi = mid
            else:
                lo = mid + 1
    return lo
```

Her turda aralık ikiye bölünür: `lo` ya da `hi` değişir. Aralık uzunluğu `n`'den başlar ve her turda kabaca yarıya iner; tur sayısı `⌈log₂(n + 1)⌉` civarındadır. Bu, Bölüm 5'teki ikili aramanın kendisidir; kaynak bunu bir `while` döngüsüyle yazıyor.

Sonra ekleme yapan `insort_right`:

```python
def insort_right(a, x, lo=0, hi=None, *, key=None):
    if key is None:
        lo = bisect_right(a, x, lo, hi)
    a.insert(lo, x)
```

Bu iki fonksiyonu birlikte okuduğunda önemli bir ayrım görürsün: yer bulmak `O(log n)`, ama elemanı yerleştirmek `a.insert(lo, x)` çağrısıyla yapılır ve bu çağrı, `lo`'dan sonraki elemanları bir kaydırır. Liste üzerinde bu kaydırma `O(n)`dir. Yani `insort_right`'ın toplam maliyeti `O(log n + n) = O(n)`dir. Arama ile ekleme aynı fonksiyonda olsa da karmaşıklıkları aynı değildir.

Son olarak, dosyanın sonunda şu bloğu bulursun:

```python
try:
    from _bisect import *
except ImportError:
    pass
```

Bu blok, Python'daki `bisect_right` ve `insort_right` tanımlarının C ile yazılmış `_bisect` modülüyle üzerine yazıldığını söyler. Yani gerçek programda çoğunlukla bu Python kodu değil, C gerçeklemesi çalışır. Bu bölümde C gerçeklemesinin ayrıntılarını doğrulamadık; yalnızca Python kaynağının algoritmasını ve karmaşıklığını okuduk.

**Sorular — cevaplamadan geçme:**

1. `bisect_right` döngüsünde `hi = mid` ve `lo = mid + 1` neden iki farklı yönde ilerler? `x` eşit olduğunda hangi yöne gidilir ve bu, "sağdan ekleme" anlamına nasıl karşılık gelir?
2. Dizi `n = 1000` elemanlı olsun. Döngü en fazla kaç tur çalışır? Cevabını `⌈log₂(n + 1)⌉` ile karşılaştır ve farkın nedenini açıkla.
3. `insort_right` içinde `a.insert(lo, x)` çağrısının `O(n)` olduğunu nasıl gösterirsin? Bir Python listesinin bellek düzenini (Bölüm 7'deki dinamik dizi) düşünerek açıkla.
4. Bu nedenle `insort` ile `n` elemanı sıralı bir listeye eklemek toplamda `O(n²)` iş yapar. Bunu `n` ekleme için kanıtla. Aynı işi yapmanın daha hızlı bir yolu var mı?
5. `bisect_left` ile `bisect_right` yalnızca eşitlik durumunda hangi konumu verir? Bu fark, Bölüm 14'teki alt sınır ve üst sınır aramasının temelidir; neden?
6. `_bisect` C modülü bu algoritmanın yerine geçerse karmaşıklık değişir mi? Hangi değişir, hangisi değişmez? Sabit çarpan açısından ne beklersin ve bunu nasıl ölçerdin?

## Bölüm Özeti

Bu bölümde algoritmaların ne kadar hızlı olduğunu değil, girdi büyüdükçe nasıl büyüdüğünü ölçmeyi öğrendik:

- **RAM modeli ve adım sayma**, süreyi donanımdan bağımsız bir adım sayısına çevirir. Model önbelleği görmez; bu yüzden tahmindir.
- **O, Ω, Θ** tanımları sabitler ve eşikle biçimselleşir. Θ hem üst hem alt sınırdır. O, durum analizi değildir.
- **Büyüme kuralları:** toplam ve çarpım kuralı, baskın terim, log tabanının önemsizliği. `4ⁿ`'nin `2ⁿ`'den farklı olduğunu unutma.
- **Döngü analizi:** iç içe, bağımlı, logaritmik ve harmonik (`n log n`) kalıpları; sayaçlı C programı formüllerle doğrulandı.
- **En iyi, en kötü, ortalama** durum girdiye bağlıdır. Doğrusal arama `Θ(1)`, `Θ(n)`, `Θ(n)` verir; naif quicksort sıralı girdide `Θ(n²)`dir.
- **Amortize analiz** toplam, muhasebe ve potansiyel yöntemleriyle yapılır. Dinamik dizi ve çoklu pop yığını bunun örnekleridir. Amortize garanti bir ortalama varsayımı değildir.
- **Master Teoremi** `T(n) = aT(n/b) + f(n)` biçimini üç durumla çözer; uygulanamayan bağıntılar da vardır.
- **Deneysel doğrulama:** log-log eğimi üssü tahmin eder. Sözlük aramasında eğim 0,34 çıktı; bu önbellek etkisidir.
- **Big-O'nun yanılttığı yerler:** sabit çarpan, önbellek düzeni, dil ve girdi dağılımı.

**Sonraki bölümde:** Bu bölümde ölçtüğümüz büyüme sınıflarının en önemli uygulamalarından biri sıralamadır. Bölüm 13'te bubble, selection, insertion, merge, quick, heap, counting ve radix sıralamalarını göreceğiz. Her birinin karmaşıklığını bu bölümün araçlarıyla çözeceğiz; quicksort'un ortalama `Θ(n log n)` ve en kötü `Θ(n²)` olmasının nedenini ve kararlılık (stability) kavramını ayrıntılı işleyeceğiz.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir `for` döngüsü `i` değişkenini `i *= 2` ile artırıyor ve `i < n` iken çalışıyor. Döngü kaç kez çalışır ve neden? Aynı döngü `i += 2` ile yazılırsa sınıf değişir mi?
2. Big-O ile en kötü durum aynı şey midir? Bir algoritmanın en kötü durum süresi `O(n²)`, en iyi durum süresi `Θ(1)` olabilir mi? Bu iki bilgiyi birlikte nasıl ifade edersin?
3. Dinamik diziye eleman eklemek amortize `O(1)`, ama tek bir ekleme `O(n)` olabilir. Bu bir gerçek zamanlı sistemde neden sorun olabilir ve bunu nasıl çözersin?
4. Master Teoremi `T(n) = 2T(n/2) + n log n` için neden doğrudan uygulanamaz? Hangi genişletilmiş biçim gerekir?
5. Bir ağacın gezinmesi `O(n)` sürer. Özyinelemeli gezinmenin uzay maliyeti neden ağacın şekline bağlıdır? Dengeli ve dengesiz ağaçlar için ne olur?
6. Bir hash tablosunda ortalama `O(1)` arama varsa, neden her zaman hash tablosu kullanılmaz? Ortalama ve en kötü durum arasındaki fark burada neden önemlidir?
7. Bir algoritmanın süresini ölçtüğünde log-log eğimi 1,2 çıktı. Bu, algoritmanın `O(n log n)` olduğunu kanıtlar mı? Hangi ek bilgi ve hangi ölçümler gerekir?
8. Mülakatta "bu çözüm O(n²) ama n ≤ 10⁵" diye bir kısıt görürsen ne yaparsın? Bu kısıt, hangi çözüm sınıflarını elemene yardımcı olur?
:::
