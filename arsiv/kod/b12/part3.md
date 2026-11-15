
## 12.9 Özyinelemeli bağıntılar: yerine koyma, ağaç, Master Teoremi

Özyinelemeli bir algoritmanın maliyeti, kendi küçük örneklerinin maliyetine bağlıdır. Bu ilişki bir **özyinelemeli bağıntı (recurrence)** ile yazılır. Merge sort'u düşünelim: `n` elemanı ikiye böl, iki yarıyı ayrı ayrı sırala, sonra `n` adımda birleştir. Maliyet şöyle yazılır:

`T(n) = 2T(n/2) + n`, `T(1) = 1`

Bu bağıntıyı çözmenin üç yolu vardır. Hangisinin uygun olduğu, bağıntının biçimine bağlıdır.

**Yerine koyma (substitution).** Bir büyüme tahmini yap, bunu bağıntıya koyup tümevarımla doğrula. Örneğin `T(n) = T(n−1) + 1` için `T(n) = n` tahmin edilirse, `T(n−1) = n − 1` yerine konunca `T(n) = n` çıkar; taban durum `T(1) = 1` de tutar. Tahmini bulmak için genellikle birkaç adım açarak örüntüyü görürüz.

**Özyineleme ağacı.** Bağıntıyı bir ağaç olarak çizeriz: kök, ilk çağrının maliyetini; çocuklar, alt çağrıların maliyetini taşır. Her seviyenin toplam maliyetini topla, seviyeleri topla. Merge sort için her seviyenin toplamı `n`'dir ve seviye sayısı `log₂ n + 1`'dir. Şekil 12.4'te `n = 8` için bu gösterilmiştir.

![Şekil 12.4: T(n) = 2T(n/2) + n için özyineleme ağacı, n = 8. Her seviye toplam n iş yapar; 4 seviye vardır. Toplam 4·8 = 32 = n·(log₂ n + 1), T(8) değeriyle eşleşir.](gorseller/b12_agac.png)

Ağaçtan çıkan formül `T(n) = n log₂ n + n`dir. Bunu kontrol edelim: `n = 8` için `8·3 + 8 = 32`; `n = 1024` için `1024·10 + 1024 = 11 264`. Deneyde `T(n)` özyinelemeyle hesaplandığında `n = 2, 8, 32, 1024` için sırasıyla `4, 32, 192, 11 264` çıktı; formül tüm değerlerle tutuyor.

**Master Teoremi.** Biçimi `T(n) = a·T(n/b) + f(n)` olan bağıntılar için bir tarif kitabıdır. Burada `a ≥ 1` alt problem sayısı, `b > 1` küçülme oranıdır. `c = log_b a` diyelim. Üç durum vardır:

1. `f(n) = O(n^(c−ε))` (bazı `ε > 0` için): `T(n) = Θ(n^c)`. İşin büyük kısmı yaprakta.
2. `f(n) = Θ(n^c)`: `T(n) = Θ(n^c · log n)`. Her seviye eşit iş yapar, seviye sayısı `log n`.
3. `f(n) = Ω(n^(c+ε))` ve düzenlilik koşulu `a·f(n/b) ≤ δ·f(n)` (bazı `δ < 1` için): `T(n) = Θ(f(n))`. İş köktedir.

Her durumun sezgisi şöyledir: ağacın iki ucu (kök ve yapraklar) ile seviyelerin dengesi. `n^c` yaprak sayısının (`a^(log_b n) = n^c`) ölçüsüdür. Eğer `f`, yapraklardan yavaş büyürse yapraklar baskındır (1); aynı hızda büyürse her seviye eşittir (2); hızlı büyürse kök baskındır (3).

Şekil 12.5, üç durumun `a = 2, b = 2, c = 1` seçimi için `f(n)` ile `n^c`'nin nasıl kıyaslandığını gösterir.

![Şekil 12.5: Master Teoremi üç durumu (a = 2, b = 2, c = 1). Soldan sağa: f(n) = √n (durum 1, sonuç Θ(n)), f(n) = n (durum 2, Θ(n log n)), f(n) = n² (durum 3, Θ(n²)). Gri kesik çizgi n^c'yi gösterir.](gorseller/b12_master.png)

Üç durumu uygulayalım:

- **Merge sort:** `a = 2, b = 2`, `c = 1`, `f(n) = n = Θ(n¹)`. Durum 2 (`k = 0`): `T(n) = Θ(n log n)`. Şekil 12.4'teki ağacın sonucu budur.
- **İkili arama:** `a = 1, b = 2`, `c = 0`, `f(n) = 1 = Θ(n⁰)`. Durum 2: `T(n) = Θ(log n)`.
- **`T(n) = 4T(n/2) + n`:** `c = 2`, `f(n) = n = O(n^(2−ε))` (`ε = 1`). Durum 1: `T(n) = Θ(n²)`.
- **`T(n) = 2T(n/2) + n²`:** `c = 1`, `f(n) = n² = Ω(n^(1+ε))`. Düzenlilik: `2·(n/2)² = n²/2 = 0,5·f(n)`, yani `δ = 0,5`. Durum 3: `T(n) = Θ(n²)`. Deneyde `T(n)/n²` oranı `n = 2⁴`'te 1,94, `n = 2¹⁶`'da 1,99998'e ulaştı; yani `T(n) → 2n²`dir ve sabit `2` bu durumda sınırın kendisidir.
- **Strassen matris çarpımı:** `T(n) = 7T(n/2) + Θ(n²)`. `c = log₂ 7 ≈ 2,807`, `f(n) = Θ(n²) = O(n^(2,807−ε))`. Durum 1: `T(n) = Θ(n^2,807)`. Bu algoritma Bölüm 19'da yer alır.

Master Teoremi her bağıntıya uygulanmaz. Üç tipik örnek:

- **`T(n) = 2T(n/2) + n log n`:** `f(n) = n log n` ne `Θ(n^c)` (`c = 1`) ne de polinom farkıyla ayrılır; üç durumun hiçbiri tam olarak uymaz. Bu bağıntı için sadeleştirilmemiş bir teknik gerekir.
- **`T(n) = 2T(n/2) + n / log n`:** `f(n)`, `n^c = n`'den polinom olarak küçük de değil, büyük de değildir (`1/log n` bir polinom farkı değildir). Bu bir "boşluktur" ve temel üç durum bunu kapsamaz.
- **`T(n) = T(n−1) + n`:** küçülme `n/b` biçiminde değil, `n − 1` biçimindedir. Master Teoremi yerine açarak çöz: `T(n) = n + (n−1) + ... + 1 = Θ(n²)`.

::: dikkat
Master Teoremi ezberlerken en sık yapılan hata, `a` ve `b` değerlerini karıştırmaktır. `c = log_b a` olduğunu, yani `a` alt problem sayısı ve `b` küçülme oranı olduğunu her zaman kontrol et. `T(n) = 2T(n/2) + n`de `c = log₂ 2 = 1`dir; `c`'yi `log₂ n` ile karıştırırsan sonuç çöker.
:::

## 12.10 Deneysel doğrulama: log-log grafiği ve eğim

Teori bize bir büyüme sınıfı verir; deney onu sınar. Bir algoritmanın süresini farklı `n` değerlerinde ölçersek, `T(n) ≈ c · n^k` ilişkisinde `k`'yı bulabiliriz. Bunun için iki eksenin de logaritmik olduğu bir grafik kullanılır. `log T = k · log n + log c` olduğundan, veri noktaları bir doğru üzerine düşer ve doğrunun eğimi `k`'dır. Bu eğim, **üssün tahminidir**.

Protokol şöyledir ve her adımı tekrarlanabilir olmalıdır:

1. **Tohum:** Rastgele veri üretirken sabit bir tohum kullan (`random.seed(42)`). Böylece aynı girdi her koşuda aynıdır.
2. **Isınma ve tekrar:** İlk çalıştırmayı (önbellek, JIT, sayfa tahsisi) atla. Her ölçümü birkaç kez tekrarla ve **en iyi süreyi** al; ortalama, arka plan gürültüsünü taşır, en iyi süre ise algoritmanın kendi maliyetine yakındır.
3. **Makine bilgisi:** Ölçümle birlikte işlemciyi, bellek boyutunu, işletim sistemini ve dil sürümünü yaz.
4. **Aralık:** `n`'i birkaç büyüklük mertebesi boyunca değiştir. Çok küçük `n`'lerde sabit yükü görürsün; çok büyük `n`'lerde önbellek etkisi girer.
5. **Eğim:** Log-log doğrusunun en küçük kareler eğimini hesapla.

Aşağıdaki iki yardımcı fonksiyon, ölçüm ve eğim hesabını yapar. `en_iyi_sure`, bir fonksiyonu tekrar tekrar çalıştırıp en küçük süreyi döndürür; `egim` ise `numpy.polyfit` ile log-log doğrusunu uydurur:

```python
import time
import numpy as np

def en_iyi_sure(fonk, tekrar=5):
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fonk()
        en = min(en, time.perf_counter() - t0)
    return en

def egim(xs, ys):
    lx = np.log2(np.array(xs, dtype=float))
    ly = np.log2(np.array(ys, dtype=float))
    return float(np.polyfit(lx, ly, 1)[0])
```

Deneyi bu iki fonksiyonla şu makinede yaptık: AMD Ryzen 7 6800H (8 çekirdek, 16 iş parçacığı, en yüksek saat 3201 MHz), 32 GB bellek, Windows 11, Python 3.12.10 ve numpy 2.3.5. Her ölçüm için en iyi süre alındı. Dört algoritma için sonuçlar şöyle:

| Algoritma | Ölçülen n aralığı | Eğim (koşu 1 / koşu 2) |
|---|---|---|
| O(n) Python döngüsü ile toplam | 4 096 – 1 048 576 | 1,009 / 0,999 |
| O(n log n) `sorted` | 4 096 – 1 048 576 | 1,195 / 1,193 |
| O(n²) iç içe karşılaştırma | 250 – 2 000 | 2,061 / 2,057 |
| O(1) sözlük araması (100 000 arama) | 1 024 – 1 048 576 | 0,341 / 0,341 |

Üç satır beklenen sonucu verir. Doğrusal toplamın eğimi 1,00'dır. Karesel çift karşılaştırma 2,06'dır; sabit payı yüzde birkaç düzeyinde saptırır. `sorted` için eğim 1,19–1,20'dir ve bu beklenenden biraz büyüktür. Nedeni `n log n`'in kendisidir: log-log eğimi `1 + 1/ln n` kadar fazladır ve `n = 10⁶` civarında bu yaklaşık 0,07'dir. Küçük fark, büyük `n`'de artan önbellek maliyetiyle de birleşir. Yani log-log eğimi `n log n` ile `n`'i kesin olarak ayırt etmez; `n log n` için 1,2 eğimi bir ipucudur, kanıt değildir.

Dördüncü satır en öğretici olanıdır. Sözlük araması teoride `O(1)`dir, eğimi ise 0,34'tür. Şekil 12.6 bunu gösterir: sözlük küçük iken tüm verisi önbelleğe sığar ve süre sabittir; sözlük büyüdükçe rastgele erişimler önbellek dışına taşar ve süre artar. Bu, "O(1) eğimi sıfır olmalı" beklentisini yanıltır.

![Şekil 12.6: Dört işlemin log-log ölçümü. Doğrusal (1,01), n log n (1,20) ve karesel (2,06) serilerin eğimleri teoriyle uyumludur. O(1) sözlük serisi (0,34) önbellek taşması nedeniyle sabit değildir.](gorseller/b12_loglog.png)

::: not
Zaman ölçümü tam olarak tekrarlanamaz: iki koşu arasında mutlak süreler değişir. Ama eğim, mutlak süreye değil oranlara dayandığı için iki koşuda da yaklaşık aynı çıkar (en fazla 0,01 fark). Bu yüzden rapor ederken süre yerine eğimi ve ölçüm koşullarını birlikte yaz.
:::

## 12.11 Big-O'nun yalan söylediği yerler

Asimptotik analiz doğrudur, ama tek başına karar vermek için eksiktir. Dört yerde büyük O, pratik gerçeği gizler.

**Sabit çarpanlar.** `100n` ve `n²` farklı büyüme sınıflarındadır, ama `n = 100`'e kadar `100n` daha pahalıdır. Şekil 12.7, iki eğrinin kesiştiği noktayı gösterir: `n > 100`'de `n²` daha pahalıdır. Bu, küçük `n` için sabit çarpanın belirleyici olabileceğinin bir örneğidir. Bu yüzden sıralama algoritmaları, küçük dizilerde kendi karmaşıklıklarından daha basit yöntemlere geçer; Bölüm 13'te bunu göreceğiz. Python'un `sort` fonksiyonu, `minrun` denilen 32–64 aralığındaki küçük parçaları ikili eklemeli sıralama ile sıralar (CPython 3.12 `Objects/listsort.txt` tasarım notu).

![Şekil 12.7: Sabit çarpan. 100n (koyu mavi) ve n² (kırmızı) n = 100'de kesişir. Bu noktadan sonra n² daha pahalıdır; daha küçük n için tersi geçerlidir.](gorseller/b12_sabit_carpan.png)

**Önbellek.** RAM modeli her erişimi eşit sayar. Gerçekte bellek hiyerarşisi vardır (Bölüm 25) ve ardışık erişim, rastgele erişimden çok daha hızlıdır. Aynı `O(n)` toplamı iki farklı sırayla yaptık: bir `int` dizisinin 16 milyon elemanını önce sırayla (`a[i]`), sonra bir rastgele permütasyonla (`a[p[i]]`) topladık. Her iki döngü de aynı sayıda işlem yapar; C'de `-O2` ile WSL'de derlendiğinde sonuç şöyleydi:

```c
for (unsigned int i = 0; i < N; i++)
    s += a[i];                /* sirali erisim */

for (unsigned int i = 0; i < N; i++)
    s += a[p[i]];             /* rastgele erisim */
```

Kodun tamamı, 64 MB'lık `a` ve 64 MB'lık `p` dizilerini ayırıp `rand()` ile Fisher-Yates karıştırması yapan bir programdır; süreler `clock()` ile en iyi üç dört tekrardan alınmıştır. Sonuç, 16 777 216 eleman için:

```term
$ ./onbellek
N = 16777216 (64 MB dizi)
sirali erisim   :     3.17 ms
rastgele erisim :   102.56 ms
oran            :    32.34
```

Oran yaklaşık 32'dir; aynı `O(n)` iki kez çalıştı. Bu, mikro bir ölçümdür ve makineye bağlıdır: 64 MB'lık dizi, tipik bir masaüstü işlemcinin son seviye önbelleğinden kat kat büyüktür. Rastgele döngü `p` dizisini de sırayla okur; yani farkın tamamı `a`'ya rastgele erişimden değil, bu erişimlerin önbellek kaçırmalarından gelir. Derleyici sıralı döngüyü vektörleştirebilir de; bu da farkı büyütür. Yine de mesaj nettir: büyük O, bellek düzenini söylemez.

![Şekil 12.8: Aynı O(n) toplamın iki erişim düzeni. Sıralı erişim 3,17 ms, rastgele erişim 102,56 ms sürdü (Ryzen 7 6800H, Windows 11, WSL gcc -O2).](gorseller/b12_onbellek.png)

**Küçük `n` ve dil.** Python'daki `for` döngüsü, C'deki aynı döngüden onlarca kat yavaştır. Bu fark sabit çarpandır ve büyük O'da görünmez. Mülakatta "Python'da bu yavaş olur" demek, C'de yazsan bile aynı büyüme sınıfının farklı bir süre vereceğini bilmek demektir.

**Girdi dağılımı.** Bölüm 10'da sıralı girdiyle bir BST'nin bağlı listeye dönüştüğünü gördük. Aynı algoritma, rastgele girdide `O(log n)` olur. Girdi dağılımı, hangi büyüme sınıfının gerçekleşeceğini belirler. Bölüm 9'daki hash flooding saldırısı da bu tür bir yanılgıyı sömürür: ortalama durum varsayımı kötü niyetli bir girdiyle bozulur.

::: ipucu
Bir algoritmanın büyük O'sunu öğrendikten sonra iki soru sor: "girdi büyüdüğünde hangi bellek düzeni kullanılıyor?" ve "sabit çarpan bu aralıkta ne kadar?". İlk soru önbelleği, ikincisi dili ve küçük `n`'i kapsar.
:::

## 12.12 Mülakatta karmaşıklık anlatma protokolü

Mülakatta kod yazmak kadar, karmaşıklığı anlatmak da değerlendirilir. Bu bir konuşma protokolüdür; her adımın bir nedeni var.

1. **Önce kaba çözümü söyle ve karmaşıklığını hesapla.** "İki döngüyle her çifti deneyebilirim; bu `O(n²)`." Kaba çözüm, referanstır (Bölüm 5'teki Adım 3).
2. **Darboğazı göster.** "İç döngüde her seferinde tüm diziyi tarıyorum; bu tarama gereksiz." Darboğazı adlandırmadan iyileştirme yapma.
3. **İyileştirmeyi ve nedenini söyle.** "Tarama yerine bir hash tablosu kullanırsam her arama `O(1)` ortalama olur; toplam `O(n)`." Ortalama mı, en kötü mü, amortize mi olduğunu belirt.
4. **Bellek maliyetini ekle.** "Hash tablosu `O(n)` ek bellek kullanır." Zaman-uzay takasını açıkça yaz.
5. **Girdi kısıtıyla karşılaştır.** Kabaca bir kural: basit işlemler saniyede yaklaşık `10⁸`–`10⁹` olabilir. `n ≤ 10⁵` için `O(n log n)` rahatça yetişir; `O(n²)`, `10¹⁰` işlemle yetişmez. Bu bir kestirimdir; kesin değildir.
6. **Sınır durumlarını söyle.** Boş girdi, tek eleman, tekrarlı değerler, taşma ihtimali.

Bu protokolü bir konuşmada görelim:

> Aday: Kaba çözüm her çifti denemek; bu `O(n²)`. `n` en fazla `10⁵` olduğu için bu yetmez. Gereksiz olan, her aday için tüm diziyi taramam. Bir tabloda gördüğüm değerleri tutarsam her arama ortalama `O(1)` olur, toplam `O(n)` ve ek bellek `O(n)`. Boş dizi için döngü hiç çalışmaz.

Bu konuşmanın değeri "O(n) buldum" cümlesinde değil, neden o sonuca ulaştığını gösteren adımlarda yatar.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, ★ zorluğundan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Burada adımlar bir **analiz** problemine uygulanır: çözüm bir algoritma değil, bir büyüme sınıfı ve kanıtıdır. Doğrulama adımında her zaman bir elle iz tablosu kullanacağız.

### Örnek 1 (★): İç içe döngünün sayımı

**Problem:** Aşağıdaki fonksiyonun döndürdüğü `s` değerinin `n` cinsinden formülünü ve Big-O sınıfını bul. Fonksiyon iki bölümden oluşur: `n(n−1)/2` gövdeli bağımlı bir döngü ve `n` gövdeli basit bir döngü.

```python
def sayac_b(n):
    s = 0
    for i in range(n):
        for j in range(i):
            s += 1
    for k in range(n):
        s += 1
    return s
```

**Adım 1 — Anla.** Girdi tamsayı `n ≥ 1`, çıktı `s`. `s`'nin kaç kez arttığını saymak istiyoruz. Kenar durum: `n = 1` (iç döngü hiç çalışmaz, ikinci döngü bir kez çalışır). Büyüme sınıfını istiyoruz, tam formülü de isteyebiliriz.

**Adım 2 — Örnekle.** `n = 3` için dış döngü `i = 0, 1, 2`'dir. İç döngü `i` kez çalışır: `0 + 1 + 2 = 3`. İkinci döngü `3` kez. Toplam `6`. Elle sayıp görelim; sonuç da bu.

**Adım 3 — Kaba çöz.** Her `i` için iç döngünün kaç kez çalıştığını topla: `Σ_{i=0}^{n−1} i = n(n−1)/2`. Üstüne `n` eklenir. Bu bir "toplamı formülle yazmak" yaklaşımıdır, adım adım sayım değildir.

**Adım 4 — Örüntü.** Bağımlı döngü (`j < i`) klasik `1 + 2 + ... + (n−1)` toplamıdır; kapalı formu `n(n−1)/2`dir. Bu örüntü, Bölüm 12.5'te gördüğümüz bağımlı döngü kalıbıdır.

**Adım 5 — İyileştir.** Büyüme sınıfı için sabitler atılır: `n(n−1)/2 + n = (n² + n)/2`, yani `Θ(n²)`. Burada iyileştirme, daha sıkı bir sınır değil, gereksiz terimleri atmaktır.

**Adım 6 — Doğrula.** Her `n` için formülü fonksiyonun gerçek çıktısıyla karşılaştır:

| n | iç döngü n(n−1)/2 | dış döngü n | toplam | (n² + n)/2 |
|---|---|---|---|---|
| 1 | 0 | 1 | 1 | 1 |
| 2 | 1 | 2 | 3 | 3 |
| 3 | 3 | 3 | 6 | 6 |
| 4 | 6 | 4 | 10 | 10 |
| 5 | 10 | 5 | 15 | 15 |

Her satırda sütunlar tutuyor. Yani `s(n) = (n² + n)/2 = Θ(n²)`.

**Bunu AI'sız yazabilir misin?** Bu fonksiyonun döngü gövdesini `s += i` ile değiştirirsen toplam ne olur? Kâğıtta `Σ i` formülünü kurup, `n = 4` için elle hesapla ve sonucu kodla karşılaştır.

### Örnek 2 (★★): Çoklu pop yığınının amortize analizi

**Problem:** Bir yığında üç işlem olsun: `push(x)`, `pop()` ve `multipop(k)` (en fazla `k` elemanı çıkarır, yığın boşsa durur). Bir işlem dizisinin toplam maliyeti `O(n)` ise, her işlemin amortize maliyeti nedir?

```python
class YiginCokPop:
    def __init__(self):
        self.veri = []
    def push(self, x):
        self.veri.append(x)
        return 1
    def multipop(self, k):
        c = 0
        while self.veri and c < k:
            self.veri.pop()
            c += 1
        return c
```

**Adım 1 — Anla.** Girdi bir işlem dizisi, çıktı toplam maliyet. Tek bir `multipop` `O(n)` olabilir (tüm yığını boşaltır). Soru, bunun uzun vadede ne kadar pahalı olduğunu bilmek.

**Adım 2 — Örnekle.** Dört `push`, sonra `multipop(3)`: `multipop` üç pop yapar, maliyet 3. Sonra `multipop(10)` kalan tek elemanı çıkarır, maliyet 1. Tek tek bakınca pahalı görünen `multipop`, aslında önceki `push`'ların bıraktığı iş birikimini boşaltıyor.

**Adım 3 — Kaba çöz.** Her işlemin en kötü maliyetini topla: `n` işlemin toplamı `O(n²)` gibi görünür (her `multipop` `O(n)`). Bu bir üst sınırdır ama gereğinden kötüdür.

**Adım 4 — Örüntü.** Her eleman en fazla bir kez çıkarılabilir, ve bir kez yığına girer. Bu, potansiyel yönteminin tipik örüntüsüdür: potansiyel = yığındaki eleman sayısı. Her `push` potansiyeli 1 artırır; her `pop` potansiyeli 1 azaltır.

**Adım 5 — İyileştir.** Amortize maliyetleri tanımla. `push` için gerçek 1, `ΔΦ = +1`, amortize `2`. `multipop(k)` için gerçek `c` (çıkarılan eleman sayısı), `ΔΦ = −c`, amortize `c − c = 0`. Yani `push` 2, `multipop` 0; her ikisi de sabit.

**Adım 6 — Doğrula.** Aşağıdaki dizi için gerçek maliyet, potansiyel ve amortize maliyeti kodla hesapladık (`Φ` = yığın boyu):

| işlem | gerçek c | Φ önce | Φ sonra | amortize = c + ΔΦ |
|---|---|---|---|---|
| push(1) | 1 | 0 | 1 | 2 |
| push(2) | 1 | 1 | 2 | 2 |
| push(3) | 1 | 2 | 3 | 2 |
| push(4) | 1 | 3 | 4 | 2 |
| multipop(3) | 3 | 4 | 1 | 0 |
| push(5) | 1 | 1 | 2 | 2 |
| multipop(10) | 2 | 2 | 0 | 0 |

Toplam gerçek maliyet `10`, toplam amortize maliyet `10`. Teorem `Σ ĉ = Σ c + Φ_son − Φ_ilk` der; `Φ_son = Φ_ilk = 0` olduğundan iki toplam eşittir. Tek bir `multipop` `O(n)` olabilir, ama her işlemin amortize maliyeti sabittir.

**Bunu AI'sız yazabilir misin?** `multipop` yerine `pop`'u her seferinde bir eleman için çağıran bir döngü yaz ve toplam maliyeti hesapla. Hangi durumda dizinin uzunluğu ile toplam maliyet arasında bir fark kalır?

### Örnek 3 (★★): Tournament ile maksimum ve yinelenen bağıntı

**Problem:** `n = 2^k` elemanlı bir dizinin maksimumunu, diziyi ikiye bölüp iki yarının maksimumlarını karşılaştırarak bul. Karşılaştırma sayısı `T(n)` için bağıntıyı kur ve çöz.

```python
def maks_bol(a, lo, hi, sayac):
    if hi - lo == 1:
        return a[lo]
    orta = (lo + hi) // 2
    sol = maks_bol(a, lo, orta, sayac)
    sag = maks_bol(a, orta, hi, sayac)
    sayac[0] += 1
    return sol if sol >= sag else sag
```

**Adım 1 — Anla.** Girdi dizi ve sınırlar, çıktı maksimum. Ölçülen şey karşılaştırma sayısı. Taban durum tek eleman: karşılaştırma yok.

**Adım 2 — Örnekle.** `[3, 9, 1, 7, 4, 8, 2, 6]` dizisi için `9` bulunur. Özyinelemenin yaptığı karşılaştırmalar sırayla: `(3,9)`, `(1,7)`, `(9,7)`, `(4,8)`, `(2,6)`, `(8,6)`, son olarak `(9,8)`. Toplam 7 karşılaştırma. `n = 8` için `n − 1 = 7`.

**Adım 3 — Kaba çöz.** Her elemanı mevcut maksimumla karşılaştırmak: `n − 1` karşılaştırma. Bu zaten doğrusal; bağıntı yöntemine ihtiyaç yok gibi görünür. Ama bunun ne kadar iyi olduğunu bağıntı ile kanıtlamak, yöntemi öğretir.

**Adım 4 — Örüntü.** Bağıntı: `T(n) = 2T(n/2) + 1`, `T(1) = 0`. Bu, Master Teoremi'nin biçimine uyar: `a = 2`, `b = 2`, `c = 1`, `f(n) = 1 = O(n^(1−ε))` (`ε = 1` alarak `n⁰`). Durum 1: `T(n) = Θ(n)`.

**Adım 5 — İyileştir.** Master Teoremi'ne gerek kalmadan, özyineleme ağacında her seviye sabit sayıda karşılaştırma yapar ve seviyeler bir artar. Toplam `1 + 2 + 4 + ... + n/2 = n − 1`. Yani tam olarak `n − 1` karşılaştırma; bu, en iyi olası sınırdır (her eleman en az bir kez karşılaştırılmalı).

**Adım 6 — Doğrula.** `n = 8` için seviye seviye karşılaştırma sayısı, kodun sayacıyla birebir eşleşir:

| seviye | düğüm sayısı | düğüm başına karşılaştırma | seviye toplamı |
|---|---|---|---|
| 0 (kök, aralık 0–8) | 1 | 1 | 1 |
| 1 (aralık 0–4, 4–8) | 2 | 1 | 2 |
| 2 (dört aralık) | 4 | 1 | 4 |
| 3 (yapraklar) | 8 | karşılaştırma yok | 0 |
| toplam | | | 7 = n − 1 |

Kodun bu dizi için sayacı `7` döndürdü ve `max` doğruydu. `n = 1000` ve `n = 1024` için de sayaç `n − 1` çıktı. Sonuç, `T(n) = n − 1 = Θ(n)`.

**Bunu AI'sız yazabilir misin?** Aynı bağıntıyı `n` tek bir sayı olmayan bir diziye (ör. `n = 10`) uyarladığında ne olur? `T(n) = T(⌊n/2⌋) + T(⌈n/2⌉) + 1` biçimini yaz ve `n = 10` için elle hesapla; bu, `n − 1` sonucunu veriyor mu?

### Örnek 4 (★★★): Heapify'ın O(n) olduğunun kanıtı

**Problem:** Bölüm 10.7'de `n` elemanlı bir dizinin heapify'ının `O(n)` olduğunu söyledik ama kanıtlamadık. `n` elemanlı bir ikili yığında, her düğüm için sift-down'un yaptığı en fazla takas sayısını toplayarak toplam sınırı bul ve `O(n)` olduğunu kanıtla.

**Adım 1 — Anla.** Girdi `n` elemanlı bir dizi; heapify, yapı `n/2`'den `0`'a kadar her iç düğüm için sift-down çağırır. Ölçülen: toplam takas sayısı. Kenar durumlar: `n = 1` (iş yok), `n` ikinin kuvveti olmayan tam ağaçlar.

**Adım 2 — Örnekle.** `n = 15` (tam bir yığın, yükseklik 3). Kökün sift-down'u en fazla 3 takas yapabilir; yaprakların hiçbiri takas yapmaz. Ara düğümler arada bir yer alır.

**Adım 3 — Kaba çöz.** Her düğüm için sift-down maliyeti `O(log n)`, düğüm sayısı `n/2`. Toplam `O(n log n)`: bu bir üst sınırdır ama gereğinden kötüdür; heapify'ı `n` kez ekleme ile yapmak da aynı sınıra gelir.

**Adım 4 — Örüntü.** Yüksekliği `h` olan düğümlerin sayısı en fazla `⌈n/2^(h+1)⌉`dir (CLRS'deki sayım lemması). Yüksekliği `h` olan bir düğümün sift-down maliyeti en fazla `h`'dir. Yani toplam, her yükseklik için `h · n/2^(h+1)` terimlerinin toplamıdır. Çarpan `1/2^h` hızla küçülür ve `h` yalnızca lineer büyür; bu seriyi sınırlamak mümkündür.

**Adım 5 — İyileştir.** Seriyi açıkça sınırla: `Σ_{h≥0} h/2^h = 2` (standart geometrik-aritmetik seri). Böylece toplam `≤ n · (1/2) · Σ h/2^h = n · (1/2) · 2 = n`. Heapify `O(n)`dir. Naif `O(n log n)` tahminimiz, en kötü her düğümün yükseklik kadar takas yaptığını varsayan gevşek bir sınırdı; yaprakların çoğu yükseklik 0'dadır.

**Adım 6 — Doğrula.** Perfect bir ağaçta (`n = 2^(H+1) − 1`) yüksekliği `h` olan düğüm sayısı tam olarak `2^(H−h)`dir. Seviye tablosu:

| h | düğüm sayısı 2^(H−h) | düğüm başına üst sınır h | katkı h · 2^(H−h) |
|---|---|---|---|
| 0 | 8 | 0 | 0 |
| 1 | 4 | 1 | 4 |
| 2 | 2 | 2 | 4 |
| 3 | 1 | 3 | 3 |
| toplam | | | 11 (n = 15) |

`H = 3` için toplam 11 ≤ 15 = n. Aynı hesap `H = 4` (`n = 31`) için 26, `H = 10` (`n = 2047`) için 2036 verir; oran `toplam/n` 1'e yaklaşır, yani sınır `n`'dir. Gerçek takaslar bu üst sınırın altındadır: rastgele girdilerde `n = 1000`, `10 000` ve `100 000` için takas/n değerleri sırasıyla 0,722, 0,741 ve 0,743 çıktı. Şekil 12.9, perfect ağaçtaki seviye katkılarını gösterir: her seviye kendi içinde küçülür ve toplam `n`'i aşmaz.

![Şekil 12.9: Heapify'ın seviye katkıları (H = 10, n = 2047). Yükseklik 1 ve 2 en büyük katkıyı verir; sonra katkı hızla düşer. Toplam 2036, yani n'den küçük.](gorseller/b12_heapify.png)

**Bunu AI'sız yazabilir misin?** `Σ_{h≥0} h/2^h = 2` eşitliğini kanıtla: `S = Σ h x^h` için `S − xS` hesabı yap, `x = 1/2` koy. Sonra bu kanıtın neden "her düğüm en fazla yükseklik kadar takas yapar" varsayımına dayandığını, ve gerçek takas sayısının neden bundan küçük olduğunu açıkla.
