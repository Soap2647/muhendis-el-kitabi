%% kisim_no: XIV
%% kisim_ad: Makine Öğrenmesi
%% bolum_no: 59
%% baslik: Ağaçlar & Ensemble

## Giriş: Tek bir ağaç zayıftır, ormanın gücü çeşitliliğindedir

Bir İHA'nın bakım kayıtlarında hangi uçağın yakın zamanda arızalanacağını tahmin etmek istediğini düşün. Veride sayısal ölçümler var (motor sıcaklığı, titreşim, akım), kategorik bilgiler var (görev tipi, çalışma ortamı), bazı sütunlar da hiç kullanılmamalı olan kimlik numaraları. Bu tür tablo verisi, derin öğrenmenin en çok konuşulduğu görüntü ve metin alanlarından çok farklıdır. Sayılar farklı ölçeklerde gelir, kategoriler sıralı değildir, bazı etkileşimler (titreşim yüksek *ve* ortam tozlu) doğrusal bir modelin kaçırdığı kadar keskindir. Tablo verisi üzerine kurulu yarışmalarda ve birçok endüstriyel uygulamada en sık tercih edilen modeller karar ağaçları ve bunların topluluklarıdır: rastgele orman ve gradyan artırma (genel bilgi).

Karar ağacı, insanın zaten yaptığı bir şeyi tekrarlar: bir soru sorar, cevaba göre ikiye ayrılır, her parçada yeniden sorar. Kuralı kimse yazmaz; veriden çıkar. Bu sezgi basittir, ama tek bir ağacın kendi başına kötü genelleme yapması da kolay görünür. Ağaç derinleştikçe eğitim verisini ezberler; veriyi biraz değiştirince yapısı tamamen değişir. Ensemble (topluluk) fikri bu zayıflığa verilmiş cevaptır: çok sayıda ağacın tahminini birleştir, her birinin hatasını birbirinden bağımsız hâle getir, ortalama hatayı düşür. Bölüm 49'da gördüğün bağımsız örneklerin ortalamasının varyansının küçülmesi burada doğrudan çalışır.

Bu bölümde karar ağacını sıfırdan yazacağız: safsızlık ölçütleri, en iyi bölmeyi bulma, özyinelemeli büyütme ve tahmin. Sonra torbalama (bagging) ve rastgele orman, gradyan artırmanın (gradient boosting) fonksiyon uzayında gradyan inişi olduğunu göreceğiz. XGBoost ve LightGBM gibi modern kütüphanelerin hangi ek hilelerle daha hızlı olduğunu genel hatlarıyla anlatacağız; sayılarını kendi verimizde ölçeceğiz. Son bölümde bu modellerin neden hâlâ tablo verisinde kral olduğunu, ne zaman derin ağlara yenildiklerini ve bir ağacı gömülü bir C fonksiyonuna nasıl çevireceğini göreceğiz. Gömülü bir uçuş bilgisayarında bellek ve işlemci sınırlıdır; küçük bir ağaç bu kısıtlara çok iyi uyar. Bölüm 46 ve 75'te bu kısıtların ayrıntısı gelecek.

Bölümdeki her ölçüm sabit tohumla yapıldı ve test verisi hiçbir ayar için kullanılmadı. Python 3.12.10, numpy 2.3.5, scikit-learn 1.8.0, XGBoost 3.4.1 ve LightGBM 4.7.0 ile çalıştırıldı; XGBoost ve LightGBM bu bölüm için pip ile kuruldu. Veri olarak yerleşik breast cancer veri seti, sentetik bir regresyon kıyaslaması (friedman1) ve kendi ürettiğimiz bir İHA bakım tablosu kullanılacak. Sentetik veriler kontrollü bir deneyin sonucudur; gerçek bir filonun arıza istatistiği değildir.

::: not
Bu bölümde her sayı bir betiğin çıktısıdır ve her betik metindedir. Süre ölçümleri (saniye) makineye bağlıdır; oranlar ve sıralar genelde korunur, mutlak değerler farklı çıkabilir. Doğruluk ve hata değerleri ise sabit tohum yüzünden birebir tekrar üretilebilir. Bir sayıyı kendi makinende üretemezsen önce ortam sürümlerini karşılaştır, sonra betiği oku.
:::

## 59.1 Karar ağacı sezgisi: yirmi soru oyunu

Yirmi soru oyununu hatırla. Biri aklında bir şey tutar, sen evet-hayır sorularıyla onu bulmaya çalışırsın. İyi bir oyuncu "hayvan mı?" diye sormaz, çünkü cevap neredeyse hiçbir şey eklemez. "Memeli mi?" sorusu olasılık kümesini yarıya indirir. Her soru, kalan adayları mümkün olduğunca dengeli ikiye bölmeye çalışır. Karar ağacı tam olarak bu stratejidir: her düğüm bir soru sorar, her dal bir cevaba karşılık gelir, yaprakta bir tahmin durur.

Bir ağaçta soru her zaman tek bir özniteliğe (feature) ve bir eşik değerine bağlıdır: "titreşim ≤ 0,8 mi?" gibi. Bu yüzden ağacın bölmeleri verinin uzayında eksenlere paralel dikdörtgenler çizer. Şekil 59.1'in solunda küçük bir ağaç var, sağında aynı mantığın 2B bir veri kümesinde ürettiği dikdörtgen bölgeler. Her yaprak bir dikdörtgene karşılık gelir ve o dikdörtgenin içindeki çoğunluk sınıfı tahmin olarak döner.

Bu yapının üç sonucu var. Birincisi, ağaç her özniteliği tek tek ele alır; ölçekleme (standardizasyon) gerekmez, çünkü "x ≤ 5" sorusu x'in birimine bakmaz. İkincisi, ağaç doğal olarak etkileşimleri yakalar: bir dalda ikinci soru yalnızca birinci sorunun cevabına bağlıdır. Üçüncüsü, sınırlar eksenlere paraleldir; çapraz bir sınırı yakalamak için ağacın birçok küçük basamak çizmesi gerekir. Bölüm 59.6'da bu eksiğin sonuçlarını ölçeceğiz.

![Şekil 59.1: Solda bir karar ağacı yapısı (şematik); sağda 2B veride derinlik 3 ağacın eksene paralel bölmeleri. Kesikli çizgiler iç bölmeleri, koyu noktalar iki sınıfı gösterir.](gorseller/b59_agac_bolme.png)

## 59.2 Safsızlık ölçütleri: Gini ve entropi

Ağaç büyütürken "en iyi soru hangisi?" diye sormamız gerekir. Bunu ölçmek için bir düğümün ne kadar karışık olduğunu sayan bir **safsızlık** (impurity) ölçütü tanımlarız. Bir düğümde tüm örnekler aynı sınıfa aitse safsızlık sıfırdır; sınıflar eşit karışmışsa en büyüktür.

İki klasik ölçüt var. **Gini safsızlığı** bir düğümdeki sınıf olasılıkları p_k için şöyle tanımlanır:

Gini = 1 − Σ p_k²

İkili sınıflamada, pozitif sınıfın olasılığı p ise Gini = 2p(1 − p) olur ve en büyük değeri p = 0,5'te 0,5'tir. **Entropi** ise Bölüm 51'de gördüğün bilgi teorisi entropisidir:

H = −Σ p_k log₂ p_k

Entropinin ikili hâli de p = 0,5'te en büyüktür ve değeri 1 bittir. İki ölçüt birbirine çok benzer; Şekil 59.2 ikisini de yanıltıcı olmayan bir ölçekte çizer. Bölüm 51.2'de entropinin "beklenen şaşırma" olduğunu görmüştük; burada aynı kavram bir düğümdeki belirsizliği ölçmek için kullanılıyor. Gini safsızlığı bilgi teorisinde doğrudan bir karşılığa sahip değildir (istatistikte Simpson çeşitlilik indeksiyle aynı ifadedir), ama hesaplaması basittir ve logaritma gerektirmez; bu yüzden sklearn'in varsayılanıdır.

Bir bölünmenin kalitesi, ebeveyn düğümün safsızlığından iki çocuğun ağırlıklı ortalama safsızlığının çıkarılmasıyla ölçülür. Buna **bilgi kazancı** (information gain) ya da safsızlık azalması denir:

kazanç = S(ebeveyn) − (n_sol/n) S(sol) − (n_sağ/n) S(sağ)

Burada S, seçtiğin safsızlık ölçütüdür. Regresyonda sınıf yerine sayısal bir değer tahmin ettiğimiz için safsızlık yerine kareler toplamı (SSE) kullanılır. Ortalamaya göre kareler toplamı, kare hata (MSE) ile aynı kapıya çıkar: n·MSE = SSE. Bu yüzden bölme ölçütü regresyonda SSE azalması olur.

![Şekil 59.2: Gini, entropi ve yanlış sınıflama oranının pozitif sınıf olasılığına göre değişimi. Gini ve entropi p = 0,5'te tepe yapar; yanlış sınıflama ise köşeli bir üçgendir.](gorseller/b59_gini_entropi.png)

::: ipucu
Gini ve entropi çoğu zaman aynı bölmeyi seçer. Fark küçüktür ve genellikle ağacın doğruluğunu anlamlı biçimde değiştirmez. Yanlış sınıflama oranını bölme ölçütü olarak kullanma: bu ölçüt düz bir üçgendir, bölmelerin ağırlıklı değişimini yakalamada yetersiz kalır. Gini ve entropi ise tepe noktası düzgün olduğu için "daha saf" bir bölmeyi daha yüksek puanlar.
:::

## 59.3 En iyi bölmeyi bulmak: sırala, say, tara

Ağaç büyütmenin kalbi, bir düğümde en iyi bölmeyi bulmaktır. Bir öznitelik için olası eşikler, o özniteliğin ayrık değerleri arasındaki orta noktalardır. `n` örnekli bir düğümde `n − 1` eşik adayı vardır. Her eşik için sol ve sağ çocuğun sınıf sayılarını yeniden saymak, naif bir yaklaşımdır: her aday için `O(n)` iş, toplam `O(n²)`.

Bu iş kolaylaştırılabilir. Önce örnekleri özniteliğe göre sıralarız (`O(n log n)`, Bölüm 13'teki sıralama). Sonra soldan sağa tek bir geçişte sol tarafın sınıf sayılarını birikimli olarak güncelleriz: her yeni örnek sol tarafa geçer, sağ tarafın sayıları ise toplamdan çıkarılır. Bu sayede her eşik için safsızlık `O(1)` ile hesaplanır (sınıf sayısı sabit kabul edilirse). Toplam maliyet sıralamanın maliyetine iner: `O(n log n)`.

Bu, Bölüm 12'deki büyüme sınıfları dilinde açık bir kazançtır. Ama önce doğruluğunu kontrol etmemiz gerekir: iki yöntem aynı bölmeyi mi seçiyor? Aşağıdaki betik rastgele 2000 küçük veri üzerinde iki yöntemin en iyi kazancını ve eşiğini karşılaştırır. Betik ayrıca tek özniteliğin n büyüdükçe süresini ölçer.

Önce naif yöntemi, eşitlik kontrolünü ve süre ölçümünü içeren betik. Naif fonksiyon her aday eşik için tüm örnekleri yeniden sayar, bu yüzden yavaştır ama doğrudur; hızlı sürümle karşılaştırmak için referans olarak kullanılır.

```python
# hiz_olcum.py -- naif O(n^2) ve sirali O(n log n) bolme
import time
import numpy as np
from agac import en_iyi_bolme_siniflama


def naif_en_iyi(x, y, k):
    # Her aday esik icin tum ornekleri yeniden say
    u = np.unique(x)
    en_iyi = (-np.inf, None)
    n = len(y)
    toplam = np.bincount(y, minlength=k).astype(float)
    ust = 1.0 - np.sum((toplam / n) ** 2)
    for i in range(len(u) - 1):
        t = (u[i] + u[i + 1]) / 2
        sol = x <= t
        cl = np.bincount(y[sol], minlength=k).astype(float)
        cr = np.bincount(y[~sol], minlength=k).astype(float)
        gl = 1.0 - np.sum((cl / cl.sum()) ** 2)
        gr = 1.0 - np.sum((cr / cr.sum()) ** 2)
        g = ust - (cl.sum() * gl + cr.sum() * gr) / n
        if g > en_iyi[0]:
            en_iyi = (g, t)
    return en_iyi


def esit_mi(a, b):
    if a is None or b[1] is None:
        return a is None and b[1] is None
    return (abs(a[0] - b[0]) < 1e-12
            and abs(a[1] - b[1]) < 1e-12)


rng = np.random.default_rng(59)
esles = 0
for _ in range(2000):
    n = rng.integers(2, 40)
    x = rng.integers(0, 8, n).astype(float)   # bilerek cok bag
    y = rng.integers(0, 3, n)
    a = en_iyi_bolme_siniflama(x, y, 3, "gini", 1)
    if esit_mi(a, naif_en_iyi(x, y, 3)):
        esles += 1
print("esit sonuc veren deneme: %d / 2000" % esles)
print()
for n in [500, 1000, 2000, 4000]:
    x = rng.normal(size=n)
    y = (x + rng.normal(0, 0.5, n) > 0).astype(int)
    t0 = time.perf_counter()
    en_iyi_bolme_siniflama(x, y, 2, "gini", 1)
    hizli = time.perf_counter() - t0
    t0 = time.perf_counter()
    naif_en_iyi(x, y, 2)
    naif = time.perf_counter() - t0
    print("n=%5d  hizli %.5f s  naif %.4f s  oran %4.0fx"
          % (n, hizli, naif, naif / hizli))
```

Betiğin çıktısı önce eşitlik kontrolünü, sonra iki yöntemin büyüme hızını gösteriyor:

```term
$ python hiz_olcum.py
esit sonuc veren deneme: 2000 / 2000

n=  500  hizli 0.00018 s  naif 0.0100 s  oran   54x
n= 1000  hizli 0.00029 s  naif 0.0226 s  oran   79x
n= 2000  hizli 0.00045 s  naif 0.0534 s  oran  120x
n= 4000  hizli 0.00081 s  naif 0.1826 s  oran  225x
```

Süre oranı n büyüdükçe artıyor. `n = 4000` için naif yöntem hızlı sürümden yüz kat ve daha fazla yavaştır. Bu oran tek bir koşuda kesin değildir; bölümün tekrar eden çalıştırmalarında oran 50 ile 230 arasında değişti. Asıl sonuç yönseldir: naif yöntemin süresi karesel, sıralamalı yöntemin süresi neredeyse doğrusal büyür.

Aşağıda hızlı bölme kodunun kendisi. Önce bölme fonksiyonları, sonra tüm ağacı kuran sınıf gelecek. Bu parça, bölümün ilk kod bloğudur. Ağacın tamamı `agac.py` dosyasında birleşir.

## 59.4 Ağacı sıfırdan kurmak: özyineleme, durdurma, tahmin

Hızlı bölme fonksiyonlarını hazırladık. Şimdi ağacın kendisi: bir düğümde en iyi bölmeyi bul, iki çocuğa ayır, her çocuk için aynı işlemi yinele. Bu, Bölüm 15'teki özyineleme şablonudur: temel durum (durdurma koşulu) ve her adımda daha küçük bir alt probleme inme. Yapıyı bir ağaç veri yapısı (Bölüm 10) olarak tutarız: her düğüm bir sınıf örneği, çocuklar ise `sol` ve `sag` işaretçileridir.

Durdurma koşulları, aşırı uydurmayı kontrol eden ilk araçlardır (Bölüm 59.5'te ayrıntılı). Burada üç koşul var: düğümde yeterli örnek yoksa, düğüm zaten saf ise veya maksimum derinliğe ulaşıldıysa, düğüm yaprak olur. Ek olarak en iyi kazanç sıfıra çok yakınsa bölmeyi yapmayız; bölmek bir şey kazandırmıyorsa ağacı gereksiz büyütürüz.

Kod, ağacın tek bir dosyada tamamı. Önce küçük yardımcılar: düğüm sınıfı ve safsızlık hesabı.

```python
# agac.py -- sifirdan karar agaci (CART): siniflandirma ve regresyon
import numpy as np


class Dugum:
    def __init__(self, derinlik, n, deger):
        self.derinlik = derinlik   # kokten uzaklik
        self.n = n                 # bu dugume dusen ornek sayisi
        self.deger = deger         # yaprak: olasilik veya ortalama
        self.ozellik = None        # bolunen ozellik indeksi
        self.esik = None           # bolme esigi: x <= esik -> sol
        self.sol = None
        self.sag = None


def saf_matris(C, olcut):
    # C: (m, k) sinif sayilari. Her satir icin safsizlik.
    n = C.sum(axis=1, keepdims=True)
    p = C / np.maximum(n, 1)
    if olcut == "gini":
        return 1.0 - np.sum(p * p, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(p > 0, p * np.log2(p), 0.0)
    return -np.sum(t, axis=1)
```

Sıralı bölme fonksiyonları, sınıflama için. Her özniteliğin sıralaması bir kez yapılır; sonra kümülatif sayımlar her eşiği verir. `min_yaprak` koşulu, çok küçük çocukların oluşmasını engeller.

```python
def en_iyi_bolme_siniflama(x, y, k, olcut, min_yaprak):
    # Sirala, sonra kumulatif sayimla tum esikleri tek geciste bul.
    s = np.argsort(x, kind="stable")
    xs, ys = x[s], y[s]
    n = len(xs)
    E = np.zeros((n, k))
    E[np.arange(n), ys] = 1.0
    sol = np.cumsum(E, axis=0)[:-1]        # ilk i+1 ornek sola
    sag = E.sum(axis=0) - sol
    nl = np.arange(1, n, dtype=float)
    nr = n - nl
    ust = saf_matris(E.sum(axis=0, keepdims=True), olcut)[0]
    agirlikli = (nl * saf_matris(sol, olcut)
                 + nr * saf_matris(sag, olcut)) / n
    kazanc = ust - agirlikli
    gecerli = ((xs[1:] > xs[:-1]) & (nl >= min_yaprak)
               & (nr >= min_yaprak))
    kazanc = np.where(gecerli, kazanc, -np.inf)
    i = int(np.argmax(kazanc))
    if not np.isfinite(kazanc[i]):
        return None
    return kazanc[i], (xs[i] + xs[i + 1]) / 2
```

Regresyon için aynı fikir, ama safsızlık yerine kareler toplamı (SSE) kullanılır. Toplamlar ve kareler toplamları da kümülatif olarak tutulur; SSE'nin açılımı sayesinde her eşik sabit zamanda değerlendirilir.

```python
def en_iyi_bolme_regresyon(x, y, min_yaprak):
    # MSE: kareler toplamini (SSE) kumulatif toplamlarla hesapla.
    s = np.argsort(x, kind="stable")
    xs, ys = x[s], y[s]
    n = len(xs)
    nl = np.arange(1, n, dtype=float)
    nr = n - nl
    T1, T2 = ys.sum(), (ys * ys).sum()
    sl, kl = np.cumsum(ys)[:-1], np.cumsum(ys * ys)[:-1]
    sr, kr = T1 - sl, T2 - kl
    sse_ust = T2 - T1 * T1 / n
    sse = (kl - sl * sl / nl) + (kr - sr * sr / nr)
    kazanc = sse_ust - sse
    gecerli = ((xs[1:] > xs[:-1]) & (nl >= min_yaprak)
               & (nr >= min_yaprak))
    kazanc = np.where(gecerli, kazanc, -np.inf)
    i = int(np.argmax(kazanc))
    if not np.isfinite(kazanc[i]):
        return None
    return kazanc[i], (xs[i] + xs[i + 1]) / 2
```

Şimdi ağacın kendisi. Kurucu, kullanıcı seçimlerini (sınıflama mı regresyon mu, hangi ölçüt, hangi durdurma sınırları) saklar. `max_ozellik` alanı, Bölüm 59.9'da rastgele orman için her düğümde yalnızca rastgele seçilmiş bir öznitelik alt kümesine bakmak için eklendi.

```python
class KararAgaci:
    def __init__(self, mod="sinif", olcut="gini", max_derinlik=None,
                 min_bolme=2, min_yaprak=1, max_ozellik=None,
                 rng=None, k=None):
        self.mod = mod
        self.olcut = olcut
        self.max_derinlik = max_derinlik
        self.min_bolme = min_bolme
        self.min_yaprak = min_yaprak
        self.max_ozellik = max_ozellik
        if rng is None:
            rng = np.random.default_rng(0)
        self.rng = rng
        self.k = k

    def fit(self, X, y):
        if self.mod == "sinif" and self.k is None:
            self.k = int(y.max()) + 1
        self.kok = self._buyut(X, y, 0)
        return self

    def _yaprak(self, y):
        if self.mod == "sinif":
            return np.bincount(y, minlength=self.k) / len(y)
        return float(y.mean())

    def _saf(self, y):
        if self.mod == "sinif":
            return np.all(y == y[0])
        return np.ptp(y) == 0

    def _bol(self, x, y):
        if self.mod == "sinif":
            return en_iyi_bolme_siniflama(x, y, self.k,
                                          self.olcut, self.min_yaprak)
        return en_iyi_bolme_regresyon(x, y, self.min_yaprak)
```

Eğitimin özü `_buyut` yöntemidir. Her çağrı bir düğüm oluşturur, durdurma koşullarını kontrol eder, aday özniteliklerin en iyi bölmesini seçer ve iki alt kümeye ayırıp kendini iki kez çağırır. Bu, Bölüm 15'te öğrendiğin "taban durum, sonra küçük alt problemler" kalıbının birebir uygulamasıdır.

```python
    def _buyut(self, X, y, d):
        dugum = Dugum(d, len(y), self._yaprak(y))
        if (len(y) < self.min_bolme or self._saf(y)
                or (self.max_derinlik is not None
                    and d >= self.max_derinlik)):
            return dugum
        adaylar = np.arange(X.shape[1])
        if self.max_ozellik is not None:
            adaylar = self.rng.choice(adaylar, self.max_ozellik,
                                      replace=False)
        en = None
        for j in adaylar:
            sonuc = self._bol(X[:, j], y)
            if sonuc is not None and (en is None or sonuc[0] > en[0]):
                en = (sonuc[0], j, sonuc[1])
        if en is None or en[0] <= 1e-12:
            return dugum
        _, j, t = en
        sol = X[:, j] <= t
        dugum.ozellik, dugum.esik = j, t
        dugum.sol = self._buyut(X[sol], y[sol], d + 1)
        dugum.sag = self._buyut(X[~sol], y[~sol], d + 1)
        return dugum
```

Tahmin, kökten başlayıp her düğümde bir karşılaştırma yaparak yaprağa inmekle olur. Bir yaprak için olasılık vektörü (sınıflama) ya da ortalama (regresyon) saklanır. Yaprak sayısı ve derinlik gibi yapısal özet işlevleri en sonda.

```python
    def _yaprak_bul(self, x):
        d = self.kok
        while d.sol is not None:
            d = d.sol if x[d.ozellik] <= d.esik else d.sag
        return d

    def olasilik(self, X):
        return np.array([self._yaprak_bul(x).deger for x in X])

    def tahmin(self, X):
        if self.mod == "sinif":
            return np.argmax(self.olasilik(X), axis=1)
        return self.olasilik(X)

    def yaprak_sayisi(self):
        def say(d):
            if d.sol is None:
                return 1
            return say(d.sol) + say(d.sag)
        return say(self.kok)

    def derinlik(self):
        def en_derin(d):
            if d.sol is None:
                return d.derinlik
            return max(en_derin(d.sol), en_derin(d.sag))
        return en_derin(self.kok)
```

Kodu sklearn'in `DecisionTreeClassifier` sınıfıyla aynı veride karşılaştıracağız. Aynı hiperparametreler (derinlik) verildiğinde iki ağaç aynı yaprak sayısına ve benzer doğruluğa ulaşmalı. Fakat birebir aynı olmasını beklememeliyiz; sebebi bir sonraki betikte ortaya çıkıyor.

```python
# sklearn_karsilastir.py -- benim agacim ile sklearn DecisionTree
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from agac import KararAgaci

X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
for d in [2, 3, 4, 5, None]:
    benim = KararAgaci(max_derinlik=d).fit(Xtr, ytr)
    sk = DecisionTreeClassifier(max_depth=d, random_state=0)
    sk.fit(Xtr, ytr)
    pb = benim.tahmin(Xte)
    ps = sk.predict(Xte)
    print("derinlik=%-4s benim=%.4f sklearn=%.4f yaprak=%d/%d "
          "ayni=%d/%d" % (d, np.mean(pb == yte), sk.score(Xte, yte),
          benim.yaprak_sayisi(), sk.get_n_leaves(),
          np.sum(pb == ps), len(ps)))

# Esitlik bagi: kokun sag cocugundaki iki adayin kazanci
from agac import en_iyi_bolme_siniflama
benim = KararAgaci(max_derinlik=2).fit(Xtr, ytr)
kok = benim.kok
alt = Xtr[:, kok.ozellik] > kok.esik
for j in [11, 21]:
    kz = en_iyi_bolme_siniflama(Xtr[alt, j], ytr[alt], 2, "gini", 1)
    print("ozellik %2d kazanc=%.5f esik=%.3f" % (j, kz[0], kz[1]))
```

Karşılaştırmanın çıktısı, yaprak sayılarının eşleştiğini, doğruluk değerlerinin ise çoğu derinlikte birbirinden biraz farklı olduğunu gösteriyor. Son iki satır eşitlik bağı kontrolüdür; bunu aşağıda açıklıyoruz:

```term
$ python sklearn_karsilastir.py
derinlik=2    benim=0.9298 sklearn=0.9240 yaprak=4/4 ayni=166/171
derinlik=3    benim=0.9181 sklearn=0.9181 yaprak=8/8 ayni=165/171
derinlik=4    benim=0.9357 sklearn=0.9240 yaprak=11/11 ayni=169/171
derinlik=5    benim=0.9240 sklearn=0.9064 yaprak=14/14 ayni=154/171
derinlik=None benim=0.9298 sklearn=0.9123 yaprak=19/19 ayni=160/171
ozellik 11 kazanc=0.05759 esik=0.528
ozellik 21 kazanc=0.05759 esik=18.445
```

Yaprak sayısı her derinlikte aynı. Farklı olan, test kümesindeki 171 tahminin ne kadarının iki modelde aynı çıktığıdır (`ayni` sütunu): 154 ile 169 arasında değişiyor. Bu farkın kaynağını bir örnekle gösterelim: derinlik 2 ağacın kökünün sağ çocuğunda, 11 ve 21 numaralı iki öznitelik tam aynı kazancı veriyor. Sklearn bu iki adayı rastgele bir sırada değerlendirir (özniteliklerin sırası karıştırılır), ben ise sıralamada önce gelen aday olan 11'i seçerim. İki bölme ölçü olarak tam eşit olduğu için bu seçim bir hata değil, bir eşitlik bağıdır (tie). Bu sırayla eğitim sürdüğünde alt ağaçlar da ayrışır ve test sonuçları birbirinden birkaç örnek kadar sapar.

Betiğin son iki satırı bu iddiayı kontrol ediyor: iki adayın Gini kazancı da 0,05759 çıkıyor, eşitlik gerçektir. Benim kodum bağı önce gelen öznitelikle kırar; eşik değerleri (0,528 ve 18,445) farklı olsa da kazanç aynıdır. Eğitim safsızlığı toplamına bakınca da (Bölüm 59.5'te gösterdiğim gibi) derinlik 2 ve 4'te iki ağaç birebir aynı çıkar; derinlik 3'te benim ağacım daha düşük toplam safsızlığa ulaşır. Tek bir ağaç için "daha iyi" demek yanıltıcıdır: eşit kazançlı seçimler sonraki düğümleri değiştirir ve açgözlü algoritma bunu geri alamaz.

::: dikkat
Ağaç kodunu yazarken en sık yapılan hata, eğitim verisi üzerindeki doğruluğu raporlamaktır. Bu bölümde her doğruluk değeri ya da hata değeri ayrı bir test kümesinden gelir. Eğitim hatasını raporladığında bunu açıkça "eğitim" diye etiketle.
:::

## 59.5 Aşırı uydurma ve budama

Bir ağacı derinleştirdikçe eğitim hatası düşer. Yeterince derin bir ağaç her eğitim örneğini kendi yaprağına koyabilir ve eğitim hatası sıfıra iner. Bu ezberlemedir: yeni bir örnekte ağaç rastgele bir yaprağa düşer ve genelleme kötüleşir. Bölüm 54'teki sapma-varyans dengesinde, derin ağaç düşük sapma ama yüksek varyans taşır. Sığ ağaç ise tersini yapar.

Bu dengeyi görmek için breast cancer veri setinde, derinliği 1'den 10'a kadar değiştirip her derinlik için beş ayrı bölmede eğitim ve test hatasını ölçtük. Eğitim hatası derinlik arttıkça monoton olarak düşer; test hatası ise belli bir noktadan sonra yatay kalır ya da yükselir. Şekil 59.3 bu iki eğriyi hata çubuklarıyla gösteriyor.

Aşağıdaki betik, derinlik taramasını ve budama yolunu birlikte çalıştırır. Önce derinlik taraması gelir; budama bu bölümün ilerisinde ele alınacak.

```python
# derinlik_budama.py -- derinlik egrisi ve budama (ccp_alpha)
import csv
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from agac import KararAgaci

X, y = load_breast_cancer(return_X_y=True)
print("== Derinlik: egitim ve test hatasi (5 tohum)")
satirlar = []
for d in range(1, 11):
    etr, ete = [], []
    for sd in range(5):
        a, b, c, e = train_test_split(X, y, test_size=0.3,
                                      random_state=sd, stratify=y)
        m = KararAgaci(max_derinlik=d).fit(a, c)
        etr.append(np.mean(m.tahmin(a) != c))
        ete.append(np.mean(m.tahmin(b) != e))
    satirlar.append((d, np.mean(etr), np.std(etr),
                     np.mean(ete), np.std(ete)))
    print("d=%2d egitim %.4f +- %.4f  test %.4f +- %.4f"
          % satirlar[-1])
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_derinlik.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derinlik", "egitim_ort", "egitim_ss", "test_ort",
                "test_ss"])
    w.writerows(satirlar)
```

Derinlik taramasının sonucu, betiğin çıktısının ilk on satırında. Budamayla ilgili satırları sonraki bölümde ele alacağız. eğitim hatası sıfıra iniyor, ama test hatası 0,069 civarında sabitleniyor. Derinlik 4 ile 5 arası en düşük test hatasına yakın, fakat beş tohum arasındaki standart sapma (yaklaşık 0,01) bu farkı kesin bir seçim yapmaya yetmez. Hata çubukları bu nedenle önemlidir: tek bir bölmede en iyi görünen derinlik, başka bir bölmede farklı çıkabilir.

![Şekil 59.3: Ağaç derinliğine göre eğitim ve test hatası (breast cancer, 5 tohum ortalaması ± standart sapma). Eğitim hatası sıfıra iner, test hatası belli bir noktadan sonra yatay kalır.](gorseller/b59_derinlik.png)

Budamanın amacı, ağacı önce büyütüp sonra gereksiz dalları kesmektir. En yaygın yöntem **maliyet-karmaşıklık budamasıdır** (cost-complexity pruning). Her alt ağaç T için şu amaç fonksiyonunu tanımlarız:

R_α(T) = R(T) + α · |T|

Burada R(T) ağacın eğitim hatası (yaprakların toplam safsızlığı), |T| yaprak sayısı, α ise karmaşıklığa verilen cezanın ağırlığıdır. α = 0 ise ağaç olduğu gibi kalır. α büyüdükçe yaprak sayısını azaltan alt ağaçlar tercih edilir. Sklearn bu yolu `ccp_alpha` parametresi ve `cost_complexity_pruning_path` yöntemiyle sunar. Burada α'yı seçmenin doğru yolu, test kümesine bakmadan, yalnızca eğitim verisinde çapraz doğrulamayla seçmektir (Bölüm 57.9'da çapraz doğrulamanın derinliğini tartışıyoruz).

Betiğin ikinci bölümü bu seçimi yapar: α adayları budama yolundan alınır, her biri 5 katlı çapraz doğrulamayla değerlendirilir ve en yüksek ortalama doğruluk veren α seçilir. Test kümesi ancak seçimden sonra kullanılır.

```python
print("\n== Budama: alfa secimi (yalnizca egitim verisinde CV)")
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
yol = DecisionTreeClassifier(random_state=0)
alfalar = yol.cost_complexity_pruning_path(Xtr, ytr).ccp_alphas
alfalar = np.unique(np.round(alfalar[:-1], 5))
cv = [cross_val_score(DecisionTreeClassifier(ccp_alpha=a,
      random_state=0), Xtr, ytr, cv=5).mean() for a in alfalar]
i = int(np.argmax(cv))
t = DecisionTreeClassifier(ccp_alpha=alfalar[i], random_state=0)
t.fit(Xtr, ytr)
print("secilen alfa=%.5f  CV=%.4f" % (alfalar[i], cv[i]))
print("secilen alfa ile test=%.4f yaprak=%d"
      % (t.score(Xte, yte), t.get_n_leaves()))
t0 = DecisionTreeClassifier(random_state=0).fit(Xtr, ytr)
print("budamasiz test=%.4f yaprak=%d"
      % (t0.score(Xte, yte), t0.get_n_leaves()))
```

Betiğin tam çıktısı aşağıda. Son üç satırda seçilen α, onunla budanmış ağacın test sonucu ve budamasız ağacın sonucu var:

```term
$ python derinlik_budama.py
== Derinlik: egitim ve test hatasi (5 tohum)
d= 1 egitim 0.0744 +- 0.0044  test 0.0959 +- 0.0102
d= 2 egitim 0.0457 +- 0.0074  test 0.0760 +- 0.0203
d= 3 egitim 0.0251 +- 0.0032  test 0.0760 +- 0.0133
d= 4 egitim 0.0131 +- 0.0019  test 0.0690 +- 0.0101
d= 5 egitim 0.0040 +- 0.0020  test 0.0702 +- 0.0083
d= 6 egitim 0.0005 +- 0.0010  test 0.0702 +- 0.0105
d= 7 egitim 0.0000 +- 0.0000  test 0.0690 +- 0.0119
d= 8 egitim 0.0000 +- 0.0000  test 0.0690 +- 0.0119
d= 9 egitim 0.0000 +- 0.0000  test 0.0690 +- 0.0119
d=10 egitim 0.0000 +- 0.0000  test 0.0690 +- 0.0119

== Budama: alfa secimi (yalnizca egitim verisinde CV)
secilen alfa=0.00654  CV=0.9347
secilen alfa ile test=0.9181 yaprak=6
budamasiz test=0.9123 yaprak=19
```

Seçilen α = 0,00654 ile ağaç 6 yaprağa iniyor ve test doğruluğu 0,9181 oluyor; budamasız ağaç 19 yaprakla 0,9123 veriyor. Fark 171 test örneğinde yalnızca bir örnek kadardır. Bu yüzden budamanın "daha iyi" olduğunu söylemek yerine şunu söyleyelim: budama modeli sadeleştirdi ve test doğruluğunu bozmadı. Bu sadeleşme, Bölüm 59.15'te C koduna çevirirken ayrıca önemli olacak: daha az yaprak daha az karşılaştırma demektir.

::: dikkat
Budama seçimini test kümesi üzerinde yaparsan, test doğruluğu iyimser çıkar. Bu, Bölüm 57'deki "seçimi ve değerlendirmeyi aynı veriyle yapmak" hatasının ta kendisidir. Her zaman üç ayrı rol düşün: eğitim (ağacı kurmak), doğrulama (α ve derinliği seçmek), test (sonucu yalnızca bir kez raporlamak).
:::

## 59.6 Ağaçların artıları ve eksileri: kararsızlık

Ağacın artılarını sayalım. Ölçekleme gerekmez, çünkü her bölme tek bir özniteliğe bakar. Sayısal ve kategorik özniteliklerin karışımını doğal olarak işler (kategorikler için kodlama gerekir, bunu Bölüm 59.14'te konuşacağız). Etkileşimleri kendiliğinden yakalar. Sonucu bir soru zinciri olarak okuyabilirsin, bu yüzden yorumlanabilirlik yüksektir. Tahmin hızlıdır: derinlik kadar karşılaştırma yaparsın.

Eksileri de aynı derecede önemlidir. En büyüğü **yüksek varyanstır**: veriyi biraz değiştirdiğinde ağacın yapısı tamamen değişebilir. Bunu göstermek için 400 noktalı bir 2B veri kümesinde (iki yarım ay) yarısını rastgele seçtik ve iki ayrı ağaç eğitip karar sınırlarını karşılaştırdık. Kod ve çıktı:

```python
# kararsizlik.py -- alt orneklerde kok bolunmesi ve karar siniri
import csv
import numpy as np
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from agac import KararAgaci

X, y = make_moons(n_samples=400, noise=0.3, random_state=59)
Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.3,
                                  random_state=59)
kokler = []
for sd in range(50):
    r = np.random.default_rng(sd)
    idx = r.choice(len(Xa), size=len(Xa) // 2, replace=False)
    t = DecisionTreeClassifier(max_depth=3, random_state=0)
    t.fit(Xa[idx], ya[idx])
    kokler.append((int(t.tree_.feature[0]),
                   round(float(t.tree_.threshold[0]), 2)))
farkli = sorted(set(kokler), key=lambda k: -kokler.count(k))
print("50 alt ornekte farkli kok bolme sayisi:", len(farkli))
for k in farkli[:3]:
    print("ozellik=%d esik=%.2f : %d / 50"
          % (k[0], k[1], kokler.count(k)))
```

Betiğin ilk bölümü, 50 farklı alt örnekte kökteki bölmenin ne kadar değiştiğini sayıyor. Kodun ikinci bölümü, tam veriyle yarım veriden eğitilen iki ağacın karar sınırlarını bir ızgarada karşılaştırır.

```python
# Tam veri ile yarim veri agaclari arasindaki karar siniri farki
rng = np.random.default_rng(59)
yarim = rng.choice(len(X), size=len(X) // 2, replace=False)
tam = KararAgaci(max_derinlik=5).fit(X, y)
alt = KararAgaci(max_derinlik=5).fit(X[yarim], y[yarim])
gx, gy = np.meshgrid(np.linspace(-1.5, 2.5, 120),
                     np.linspace(-1.0, 1.5, 90))
G = np.column_stack([gx.ravel(), gy.ravel()])
pa, pb = tam.tahmin(G), alt.tahmin(G)
print("izgarada iki agacin ayristigi oran: %.4f" % np.mean(pa != pb))
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_karar_siniri.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["x1", "x2", "tam_agac", "alt_ornek_agac"])
    for i in range(len(G)):
        w.writerow(["%.4f" % G[i, 0], "%.4f" % G[i, 1], int(pa[i]),
                    int(pb[i])])
```

```term
$ python kararsizlik.py
50 alt ornekte farkli kok bolme sayisi: 12
ozellik=1 esik=0.44 : 20 / 50
ozellik=1 esik=0.29 : 10 / 50
ozellik=1 esik=0.31 : 5 / 50
izgarada iki agacin ayristigi oran: 0.1465
```

Elli alt örnekte kök bölme 12 farklı kombinasyona dağıldı. En sık seçilen bölme (özniteliğin 1 numaralı olduğu, eşiği 0,44 olan) bile yalnızca 50 denemenin 20'sinde çıktı. Veriyi yarıya indirmek bile ağacın tepesini değiştirmeye yetti. Izgarada iki ağacın ayrıştığı oran yaklaşık yüzde 15'tir: karar sınırının yüzde 15'lik kısmı yalnızca bir veri alt kümesi değiştiğinde kayıyor.

![Şekil 59.4: Aynı veriyle eğitilen iki ağacın karar sınırı. Solda tam veri (400 örnek), sağda rastgele yarısı. Renkli alanlar iki sınıfı, noktalar eğitim örneklerini gösterir.](gorseller/b59_karar_kararsiz.png)

Şekil 59.4'ün her iki panelinde de sınırlar dikdörtgen basamaklarla çizilmiş. Bu, eksene paralel bölmenin ikinci eksiğidir: iki sınıf arasındaki eğri bir çapraz sınır olduğunda ağaç onu merdiven gibi yaklaştırır. Merdiven basamakları veri arttıkça inceltilebilir, ama her basamak yeni bir bölmedir ve ağacı derinleştirir. Bu nedenle ağaçların tek başına bir çapraz sınırı yakalaması pahalıdır. Topluluk yöntemleri bu iki eksiği de hafifletir: basamakları birçok ağacın ortalamasıyla yumuşatır ve kararsızlığı ortalama yoluyla azaltır. Bunun matematiğine şimdi geçiyoruz.

## 59.7 Topluluk fikri: bağımsız hataların ortalaması

Bölüm 49'da bağımsız rastgele değişkenlerin ortalamasının varyansının `σ²/n` olduğunu görmüştük. Topluluk fikri bu gözlemi ağaçlara uygular: her ağacın tahmini gürültülü bir ölçüm gibidir, ortalama alınca gürültü azalır. Ama ağaçlar tamamen bağımsız değildir. Aynı veriden eğitildikleri için tahminleri bir miktar korelasyonlu olur.

Varsayalım her ağacın tahmininin varyansı σ², aralarındaki korelasyon ρ, ve B ağacın ortalamasını alıyoruz. Varyans formülü şöyledir:

Var(ortalama) = ρσ² + (1 − ρ)σ²/B

Bu formülün iki ucunu düşün. ρ = 0 ise tamamen bağımsızdır ve varyans σ²/B'ye düşer: ağaç sayısı arttıkça varyans sıfıra gider. ρ = 1 ise hepsi aynı ağaçtır ve ortalama almak hiçbir şey kazandırmaz: varyans σ² kalır. Gerçek hayatta ρ bu iki ucun arasındadır ve topluluk kazancının sınırı ρσ² terimidir. Bu terim, korelasyon ne kadar düşük olursa o kadar küçük olur. Rastgele ormanın tüm fikri bu sınırı küçültmektir (Bölüm 59.9).

Formülü simülasyonla doğrulayalım. Her ρ ve B için 20000 tekrarda B korelasyonlu normal değişkenin ortalamasını hesapladık ve bu ortalamaların varyansını ölçtük.

```python
# korelasyon.py -- rho ve B ile ortalamanin varyansi
import csv
import numpy as np

rng = np.random.default_rng(59)
R = 20000                                # tekrar sayisi
satirlar = []
print("rho    B   formul   simulasyon")
for rho in [0.0, 0.3, 0.6, 0.9]:
    for B in [1, 2, 5, 10, 25, 50, 100, 200]:
        Z0 = rng.standard_normal((R, 1))  # ortak faktor
        E = rng.standard_normal((R, B))   # ozgul hatalar
        X = np.sqrt(rho) * Z0 + np.sqrt(1 - rho) * E
        sim = X.mean(axis=1).var()
        form = rho + (1 - rho) / B        # sigma^2 = 1
        satirlar.append((rho, B, form, sim))
        if B in (1, 10, 100):
            print("%.1f %4d   %.4f   %.4f" % (rho, B, form, sim))
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_korelasyon.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rho", "B", "formul", "simulasyon"])
    w.writerows(satirlar)
```

Çıktı formülle simülasyonun neredeyse birebir uyduğunu gösteriyor:

```term
$ python korelasyon.py
rho    B   formul   simulasyon
0.0    1   1.0000   0.9941
0.0   10   0.1000   0.1008
0.0  100   0.0100   0.0099
0.3    1   1.0000   1.0127
0.3   10   0.3700   0.3618
0.3  100   0.3070   0.3069
0.6    1   1.0000   1.0169
0.6   10   0.6400   0.6387
0.6  100   0.6040   0.6063
0.9    1   1.0000   0.9939
0.9   10   0.9100   0.9113
0.9  100   0.9010   0.9061
```

ρ = 0,3 ve B = 10 için formül 0,3700, simülasyon 0,3618 veriyor. ρ = 0,9 için B = 10'dan B = 100'e çıkmak varyansı yalnızca 0,910'dan 0,901'e indirir; korelasyonlu ağaçlarda ağaç sayısı artışının kazancı hızla tükenir. Şekil 59.5 aynı ilişkiyi tüm ρ değerleri için çizer.

![Şekil 59.5: Ağaç sayısı B'ye göre ortalamanın varyansı. Çizgiler formül, noktalar simülasyon. Yüksek korelasyonda (ρ = 0,9) B artınca varyans tabana yaklaşır.](gorseller/b59_korelasyon.png)

Bu grafik, bölümün ana tasarım kararını açıklıyor. Ağaçları birbirine benzer yapmak (aynı veri, aynı öznitelikler) ρ'yu büyütür ve topluluk kazancını öldürür. Çeşitliliği artırmanın iki yolu var: her ağacı farklı bir bootstrap örneğiyle eğitmek (bagging, Bölüm 59.8) ve her bölmede öznitelik alt kümesi seçmek (rastgele orman, Bölüm 59.9). Bu iki hile ρ'yu düşürür.

::: not
Topluluk yöntemleri **varyansı** düşürür; **sapmayı** düşürmez. Her ağaç kendi başına yanlıysa ortalaması da yanlı olur. Bu yüzden topluluğun tek başına bir ağaçtan kötü olmasının imkânı yoktur ama daha iyi olması da kendiliğinden değildir. Gradyan artırma (59.10) tersine sapmayı düşürmek için tasarlanmıştır.
:::

## 59.8 Torbalama (bagging) ve OOB hatası

**Torbalama** (bootstrap aggregating, bagging), her ağacı farklı bir bootstrap örneğiyle eğitip tahminleri ortalamadır. Bootstrap, Bölüm 49.9'da gördüğün yöntemdir: `n` örnekten, iade ile yeniden `n` örnek çekeriz. Bu yeni kümede bazı örnekler birden fazla kez, bazıları hiç yer almaz. Büyük `n` için bir örneğin bir bootstrap kümesinde hiç seçilmeme olasılığı `(1 − 1/n)^n`'in limiti olan e⁻¹ ≈ 0,368'dir.

Bu, bedava bir doğrulama kümesi verir. Bir ağaç bir örneği eğitmede kullanmadıysa, o örnek o ağacın **torba dışı** (out-of-bag, OOB) örneğidir. Her örnek için yalnızca onu görmemiş ağaçların tahminini toplayıp ortalamasını alırsak, ayrı bir doğrulama kümesi olmadan hata tahmini elde ederiz. Bu OOB hatasıdır. Önce küçük bir örnekle mekanizmayı görelim: 6 örnekli bir veriyle üç bootstrap çekimi.

```python
# ornek_oob.py -- 6 ornekli bootstrap ve OOB kumesi (sabit tohum)
import numpy as np

rng = np.random.default_rng(59)
n = 6
for b in range(3):
    ornek = rng.integers(0, n, n)           # iadeli ornekleme
    sayim = np.bincount(ornek, minlength=n)
    oob = np.setdiff1d(np.arange(n), ornek)  # secilmeyenler
    print("agac %d: ornek=%s" % (b + 1, ornek.tolist()))
    print("        sayim=%s  OOB=%s" % (sayim.tolist(), oob.tolist()))
print("tek ornegin bir bootstrapte secilmeme olasiligi: %.4f"
      % ((1 - 1 / n) ** n))
```

Çıktıda her ağaç için hangi örneklerin seçildiğini ve hangilerinin dışarıda kaldığını görüyorsun:

```term
$ python ornek_oob.py
agac 1: ornek=[4, 3, 4, 4, 3, 0]
        sayim=[1, 0, 0, 2, 3, 0]  OOB=[1, 2, 5]
agac 2: ornek=[4, 2, 2, 1, 0, 0]
        sayim=[2, 1, 2, 0, 1, 0]  OOB=[3, 5]
agac 3: ornek=[5, 0, 5, 5, 5, 0]
        sayim=[2, 0, 0, 0, 0, 4]  OOB=[1, 2, 3, 4]
tek ornegin bir bootstrapte secilmeme olasiligi: 0.3349
```

Örnek 0 üç ağacın üçünde de seçilmiş (sayım sütunları 1 ya da daha fazla), bu yüzden hiçbir ağacın OOB kümesinde yok. Örnek 1 ise ikinci ağaçta hiç seçilmemiş, bu yüzden onun OOB tahmini yalnızca o ağacın tahmininden gelir. Tek bir örneğin bir bootstrap'te seçilmeme olasılığı n = 6 için 0,3349'dur; sayının büyük `n` için e⁻¹'e yakınsadığını görüyorsun. Şimdi bu mekanizmanın kodu. Torbalama sınıfı, rastgele orman için de aynı kodu kullanır (`max_ozellik` sayı verilirse her düğümde öznitelik alt kümesi seçilir).

```python
# orman.py -- torbalama (bagging) ve rastgele orman, sifirdan
import numpy as np
from agac import KararAgaci


class Torba:
    # max_ozellik=None: saf torbalama; sayi verilirse rastgele orman
    def __init__(self, B=50, max_ozellik=None, seed=0):
        self.B = B
        self.max_ozellik = max_ozellik
        self.seed = seed

    def fit(self, X, y):
        self.k = int(y.max()) + 1
        rng = np.random.default_rng(self.seed)
        n = len(y)
        self.agaclar = []
        # OOB olasilik toplami ve oy sayisi
        self.oob_toplam = np.zeros((n, self.k))
        self.oob_say = np.zeros(n)
        for _ in range(self.B):
            ornek = rng.integers(0, n, n)         # iadeli ornekleme
            disarda = np.setdiff1d(np.arange(n), ornek)
            agac = KararAgaci(max_ozellik=self.max_ozellik, rng=rng,
                              k=self.k)
            agac.fit(X[ornek], y[ornek])
            self.agaclar.append(agac)
            if len(disarda) > 0:
                p = agac.olasilik(X[disarda])
                self.oob_toplam[disarda] += p
                self.oob_say[disarda] += 1
        return self
```

Sınıfın geri kalanı, tahmini ve OOB hesabını içerir:

```python
    def olasilik(self, X):
        return sum(a.olasilik(X) for a in self.agaclar) / self.B

    def tahmin(self, X):
        return np.argmax(self.olasilik(X), axis=1)

    def oob_hatasi(self, y):
        var = self.oob_say > 0
        pred = np.argmax(self.oob_toplam[var], axis=1)
        return np.mean(pred != y[var]), var.mean()
```

Şimdi torbalamanın gerçekten tek bir ağaçtan iyi olup olmadığına bakalım. Betik, aynı üç veri bölmesinde (tohum 0, 1, 2) tek ağacı, torbalamayı, rastgele ormanı ve sklearn'in `RandomForestClassifier`'ını karşılaştırır; ayrıca her torba için OOB hatasını test hatasıyla yan yana yazar. Veri, 20 öznitelikli `make_classification` kümesidir.

```python
# torba_oob.py -- torbalama, RF, OOB ve sklearn kiyasi
import time
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from agac import KararAgaci
from orman import Torba


def veri(sd):
    X, y = make_classification(n_samples=1200, n_features=20,
                               n_informative=6, n_redundant=4,
                               n_clusters_per_class=2, flip_y=0.05,
                               random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd,
                            stratify=y)


print("tohum  tek agac  torba(B=50)  RF(B=50, sqrt=4)  sklearn RF")
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    tek = np.mean(KararAgaci().fit(Xtr, ytr).tahmin(Xte) != yte)
    t0 = time.perf_counter()
    torba = Torba(B=50, seed=sd).fit(Xtr, ytr)
    sure = time.perf_counter() - t0
    rf = Torba(B=50, max_ozellik=4, seed=sd).fit(Xtr, ytr)
    sk = RandomForestClassifier(n_estimators=50, random_state=sd,
                                n_jobs=1).fit(Xtr, ytr)
    print("%5d  %.4f    %.4f       %.4f            %.4f"
          % (sd, tek, np.mean(torba.tahmin(Xte) != yte),
             np.mean(rf.tahmin(Xte) != yte), 1 - sk.score(Xte, yte)))
    print("       OOB(torba)=%.4f  OOB(RF)=%.4f  torba suresi=%.2fs"
          % (torba.oob_hatasi(ytr)[0], rf.oob_hatasi(ytr)[0], sure))
```

```term
$ python torba_oob.py
tohum  tek agac  torba(B=50)  RF(B=50, sqrt=4)  sklearn RF
    0  0.1972    0.1250       0.0944            0.1000
       OOB(torba)=0.1345  OOB(RF)=0.1238  torba suresi=4.38s
    1  0.2083    0.1250       0.0917            0.0972
       OOB(torba)=0.1167  OOB(RF)=0.1083  torba suresi=4.04s
    2  0.1722    0.0833       0.0833            0.0917
       OOB(torba)=0.1155  OOB(RF)=0.0940  torba suresi=3.97s
```

Üç tohumda da tek ağaç yaklaşık yüzde 17-21 hata yapıyor. Torbalama (B = 50) bunu yaklaşık yüzde 8-13'e indiriyor. Rastgele orman (aynı B ile, her bölmede 4 öznitelik) ortalama yüzde 9 civarında. Sklearn'in RF'si aynı bölmelerde yüzde 9-10 hata veriyor; yani benim torbalama ve RF kodum sklearn'in sonuçlarıyla aynı düzeyde ve üstünlük iddiası yapamayacağımız kadar yakın. OOB hataları test hatasını izliyor. RF'de OOB hatası her tohumda biraz yüksek çıkıyor; torbalamada ise fark işaret değiştiriyor. Nedeni şu: bir örneğin OOB tahmini yalnızca yaklaşık yüzde 37'si kadar ağacın oyuyla yapılır, test tahmini ise tüm ağaçlarla. Daha az ağaçla yapılan ortalama biraz daha gürültülüdür; bu yüzden OOB hatası B için hafif kötümser bir tahmindir.

::: dikkat
Tahminlerini eğitim verisi üzerinde ölçmek (ağacı kurduğun veriyle tahmin yapmak) OOB değildir. OOB tahmini her zaman yalnızca eğitimde o örneği görmemiş ağaçlardan gelir. Kodda bu seçici ortalama `oob_toplam` ve `oob_say` dizileriyle yapılır.
:::

## 59.9 Rastgele orman: öznitelik alt örnekleme

Torbalama, bootstrap ile ağaçları birbirinden biraz farklılaştırır. Ama bir öznitelik çok güçlüyse, her bootstrap'te her ağacın ilk bölmesi aynı öznitelik olur ve ağaçlar yine çok benzer kalır: ρ yüksek kalır. **Rastgele orman** (random forest) buna bir adım ekler: her bölmede tüm öznitelikleri değil, rastgele seçilmiş bir alt kümeyi değerlendirir. Sınıflamada varsayılan alt küme boyutu √d'dir; d = 20 için 4. Böylece güçlü bir öznitelik bazı bölmelerde kullanılamaz ve diğer öznitelikler de söz sahibi olur. Bu, ρ'yu düşürür ve Bölüm 59.7'deki formüle göre varyans kazancını büyütür.

Rastgele ormanı torbalamanın bir parametresi olarak uyguladık: `Torba(B, max_ozellik=4)`. Ağaç sayısına göre test hatasının nasıl değiştiğini görmek için sklearn'in RF'sini beş tohumda, B = 1'den 200'e kadar tarayan bir betik çalıştırıyoruz.

```python
# rf_egri.py -- sklearn RF: agac sayisina gore test hatasi (5 tohum)
import csv
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def veri(sd):
    X, y = make_classification(n_samples=1200, n_features=20,
                               n_informative=6, n_redundant=4,
                               n_clusters_per_class=2, flip_y=0.05,
                               random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd,
                            stratify=y)


satirlar = []
for B in [1, 2, 5, 10, 20, 50, 100, 200]:
    e = []
    for sd in range(5):
        Xtr, Xte, ytr, yte = veri(sd)
        rf = RandomForestClassifier(n_estimators=B, random_state=sd,
                                    n_jobs=-1).fit(Xtr, ytr)
        e.append(1 - rf.score(Xte, yte))
    satirlar.append((B, np.mean(e), np.std(e)))
    print("B=%3d  test hatasi %.4f +- %.4f" % satirlar[-1])
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_rf_agac.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["agac_sayisi", "test_hata_ort", "test_hata_ss"])
    w.writerows(satirlar)
```

Çıktı, ağaç sayısının belli bir noktadan sonra test hatasını pek değiştirmediğini gösteriyor:

```term
$ python rf_egri.py
B=  1  test hatasi 0.2317 +- 0.0510
B=  2  test hatasi 0.2322 +- 0.0250
B=  5  test hatasi 0.1406 +- 0.0163
B= 10  test hatasi 0.1283 +- 0.0138
B= 20  test hatasi 0.1128 +- 0.0054
B= 50  test hatasi 0.1067 +- 0.0130
B=100  test hatasi 0.1078 +- 0.0212
B=200  test hatasi 0.1022 +- 0.0181
```

B = 1'de hata yaklaşık yüzde 23 ve tohumlar arası sapma büyük (0,051). B = 5'te hata yüzde 14'e iniyor; B = 50'den sonra 0,102 ile 0,108 arasında kalıyor. B = 200 ile B = 50 arasındaki fark tohum sapmasının içinde. Yani pratikte "ne kadar ağaç" sorusunun cevabı, eğrinin düzleştiği yerdir; bu veride birkaç yüz ağaç gereksizdir. Şekil 59.6 eğriyi hata çubuklarıyla gösteriyor.

![Şekil 59.6: Rastgele ormanda ağaç sayısına göre test hatası (5 tohum, ortalama ± standart sapma). Eğri B = 50 civarında düzleşir.](gorseller/b59_rf_agac.png)

Rastgele ormanın bir diğer güzel özelliği, ek bir doğrulama kümesi olmadan OOB hatasının test hatasına yakın olmasıdır: yukarıdaki çıktıda RF'nin OOB hatası her tohumda test hatasından 0,01 ile 0,03 arasında yüksek. Bu, RF'yi küçük veri kümelerinde pratik kılar. Ama bu özelliğin kesin bir ölçüm olmadığını unutma: yalnızca yaklaşık bir tahmindir ve bağımsız bir test kümesinin yerini tutmaz.

## 59.10 Gradyan artırma: fonksiyon uzayında gradyan inişi

Torbalama ve rastgele orman ağaçları paralel eğitir ve ortalamalarını alır; varyansı düşürürler. Gradyan artırma (gradient boosting) ise ağaçları **sıralı** eğitir: her yeni ağaç, şimdiye kadarki topluluğun hatalarını düzeltmeye çalışır. Böylece sapmayı azaltır.

Fikri Bölüm 50'deki gradyan inişiyle düşün. Orada bir parametre vektörü θ'yı güncelliyorduk: θ ← θ − η∇L(θ). Burada parametre bir sayı vektörü değil, bir **fonksiyondur**: F(x), şimdiye kadarki topluluğun tahminidir. Amaç, kayıp L'yi azaltacak yönde F'yi güncellemek. Fonksiyon uzayında gradyan, her örnekte ∂L/∂F(x_i) değerlerinden oluşan vektördür ve negatifi, **artık** (pseudo-residual) denen yönü verir:

r_i = −∂L(y_i, F(x_i)) / ∂F(x_i)

Gradyan inişinde bu yönü bir ağaçla yaklaşık olarak temsil ederiz: yeni ağaç h_t, artıklara en iyi uyan bölge-sabit fonksiyondur. Güncelleme şöyle:

F_t(x) = F_{t−1}(x) + η · h_t(x)

Burada η öğrenme oranıdır (shrinkage): her ağacın katkısını küçültür. Kare kayıp için L = (y − F)²/2 olduğunda r_i = y_i − F(x_i), yani artık tam olarak hatanın kendisidir. Bu yüzden gradyan artırmanın regresyon versiyonu, "artıklara ağaç uydur ve ekle" döngüsüdür. Log-kayıp (ikili sınıflama) için artık r_i = y_i − p_i olur, p_i = σ(F(x_i)); burada ağacın yaprak değeri için Newton adımı kullanılır: γ = Σg / Σh, g_i = y_i − p_i ve h_i = p_i(1 − p_i).

Aşağıdaki sınıf her iki durumu da kodlar. Kurucuda öğrenme oranı, derinlik ve yaprak alt sınırı vardır. `fit` her turda artığı hesaplar, yeni ağacı kurar ve `F` dizisini günceller. Log-kayıp dalı ise yaprak değerlerini Newton adımıyla yeniden hesaplar.

```python
# gbm.py -- gradyan artirma (gradient boosting), sifirdan
import numpy as np
from agac import KararAgaci


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def yaprak_newton(agac, X, g, h):
    # Log-kayip icin yaprak degeri: gamma = sum(g) / sum(h)
    topla = {}
    for i, x in enumerate(X):
        d = agac._yaprak_bul(x)
        a = topla.setdefault(id(d), [d, 0.0, 0.0])
        a[1] += g[i]
        a[2] += h[i]
    for d, sg, sh in topla.values():
        d.deger = sg / sh if sh > 1e-12 else 0.0


class GradyanArtirma:
    def __init__(self, T=100, eta=0.1, derinlik=3,
                 mod="regresyon", min_yaprak=5):
        self.T = T
        self.eta = eta
        self.derinlik = derinlik
        self.mod = mod
        self.min_yaprak = min_yaprak

    def _ag(self):
        return KararAgaci(mod="regresyon",
                          max_derinlik=self.derinlik,
                          min_yaprak=self.min_yaprak)
```

Eğitim döngüsü: her turda artık hesabı, ağaç kurulumu ve `F` güncellemesi. Doğrulama kümesi verildiğinde her turda eğitim ve doğrulama kaybı kaydedilir; bu kayıt erken durdurma için kullanılacak.

```python
    def fit(self, X, y, Xv=None, yv=None):
        n = len(y)
        if self.mod == "regresyon":
            self.f0 = float(y.mean())
        else:
            p0 = y.mean()
            self.f0 = float(np.log(p0 / (1 - p0)))
        F = np.full(n, self.f0)
        self.agaclar = []
        if Xv is not None:
            Fv = np.full(len(yv), self.f0)
        self.gecmis = []
        for t in range(self.T):
            if self.mod == "regresyon":
                r = y - F                  # negatif gradyan = artik
                agac = self._ag().fit(X, r)
            else:
                p = sigmoid(F)
                g = y - p                  # -gradyan (log-kayip)
                agac = self._ag().fit(X, g)
                yaprak_newton(agac, X, g, p * (1 - p))
            self.agaclar.append(agac)
            F = F + self.eta * agac.olasilik(X)
            if Xv is not None:
                Fv = Fv + self.eta * agac.olasilik(Xv)
                self.gecmis.append((self._kayip(y, F),
                                    self._kayip(yv, Fv)))
        return self
```

Son kısım kayıp hesabı ve tahmin fonksiyonlarını içerir. `ham` ham skoru (log-odds ya da regresyon değeri) döndürür; `tahmin` sınıflamada bunu olasılığa çevirip 0,5 eşiğiyle karar verir.

```python
    def _kayip(self, y, F):
        if self.mod == "regresyon":
            return float(np.mean((y - F) ** 2))
        p = np.clip(sigmoid(F), 1e-12, 1 - 1e-12)
        kayip = y * np.log(p) + (1 - y) * np.log(1 - p)
        return float(-np.mean(kayip))

    def ham(self, X, T=None):
        T = self.T if T is None else T
        F = np.full(len(X), self.f0)
        for agac in self.agaclar[:T]:
            F = F + self.eta * agac.olasilik(X)
        return F

    def tahmin(self, X, T=None):
        F = self.ham(X, T)
        if self.mod == "regresyon":
            return F
        return (sigmoid(F) >= 0.5).astype(int)
```

Önce bu kodun doğruluğunu sınıflama tarafında sklearn ile karşılaştıralım. Breast cancer veri setinde iki model de 100 ağaç, öğrenme oranı 0,1, derinlik 3 ve yaprak alt sınırı 5 ile eğitildi:

```python
# gbm_sinif.py -- log-kayipli GBM: benim surum vs sklearn
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss
from gbm import GradyanArtirma, sigmoid

X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
benim = GradyanArtirma(T=100, eta=0.1, derinlik=3, mod="sinif",
                       min_yaprak=5).fit(Xtr, ytr)
p = sigmoid(benim.ham(Xte))
sk = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1,
                                max_depth=3, min_samples_leaf=5,
                                random_state=0).fit(Xtr, ytr)
print("benim:   dogruluk=%.4f  log-kayip=%.4f"
      % (np.mean((p >= 0.5) == yte), log_loss(yte, p)))
p_sk = sk.predict_proba(Xte)[:, 1]
print("sklearn: dogruluk=%.4f  log-kayip=%.4f"
      % (sk.score(Xte, yte), log_loss(yte, p_sk)))
```

```term
$ python gbm_sinif.py
benim:   dogruluk=0.9532  log-kayip=0.0932
sklearn: dogruluk=0.9591  log-kayip=0.0993
```

Benim sürümüm ile sklearn'in sürümü aynı aralıkta: benim log-kayıp 0,0932, sklearn 0,0993. Doğruluk farkı (0,9532'ye karşı 0,9591) 171 test örneğinde bir ya da iki örnek kadar. Sklearn ayrıca ağaçları friedman_mse ölçütüyle büyütür ve yaprak değerlerini kendi yaklaşımıyla hesaplar; bu fark beklenen bir farktır, bir hata değil.

Şimdi öğrenme adımının etkisini görelim. Bölüm 50'deki gibi, adım büyüklüğü her şeyi belirler: büyük adım hızlı ama kararsız, küçük adım yavaş ama dengeli. Boyutu ve gürültüsü kontrollü bir regresyon verisi için friedman1 üzerinde öğrenme oranlarını deniyoruz. Burada gürültü, Bayes hatasını (en iyi olası MSE) 1,0 civarına sabitler; test MSE'nin bu değerin üstünde kalan kısmı, modelin hatasıdır.

Ama önce bir adım: 1B oyuncak veriyle üç turun adım izini çizen betik. Bu betik şeklin verisini üretir.

```python
# gbm_adim.py -- 1B oyuncak veride gradyan artirma adim izi (CSV)
import csv
import numpy as np
from gbm import GradyanArtirma

rng = np.random.default_rng(59)
x = np.sort(rng.uniform(0, 6, 40))
y = np.sin(x) + rng.normal(0, 0.2, 40)
X1 = x.reshape(-1, 1)
m = GradyanArtirma(T=3, eta=1.0, derinlik=2, min_yaprak=3)
m.fit(X1, y)
F = np.full(len(y), m.f0)
kol = {"x": x, "y": y, "F0": F.copy()}
for t in range(3):
    kol["r%d" % t] = y - F                 # artik
    F = F + m.agaclar[t].olasilik(X1)      # adim: F += h_t(x)
    kol["F%d" % (t + 1)] = F.copy()
for t in range(3):
    print("adim %d: artik kare ort.=%.4f  adimdan sonra MSE=%.4f"
          % (t + 1, np.mean(kol["r%d" % t] ** 2),
             np.mean((y - kol["F%d" % (t + 1)]) ** 2)))
ad = list(kol.keys())
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_gbm_adim.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(ad)
    for i in range(len(x)):
        w.writerow(["%.5f" % kol[k][i] for k in ad])
```

```term
$ python gbm_adim.py
adim 1: artik kare ort.=0.4842  adimdan sonra MSE=0.0640
adim 2: artik kare ort.=0.0640  adimdan sonra MSE=0.0531
adim 3: artik kare ort.=0.0531  adimdan sonra MSE=0.0473
```

Her adımda hata düşüyor: ilk adımdan önce artığın ortalama karesi 0,4842 iken adımdan sonra MSE 0,0640'a iniyor; sonraki adımlarda 0,0531 ve 0,0473. Şekil 59.7 bu üç adımın ne yaptığını gösteriyor: her ağaç bir önceki artığı kendi küçük basamaklarıyla yaklaşıyor ve F eğrisi giderek veriye yaklaşıyor.

![Şekil 59.7: Gradyan artırmanın üç adımı (1B veri, derinlik 2 ağaçlar, η = 1). (a) başlangıç F₀ ortalaması; (b) artık ve ilk ağacın uyumu; (c) ikinci adımın yeni artığı; (d) üç adım sonra F₃.](gorseller/b59_gbm_adim.png)

Şimdi bu betiğin büyük ölçekli kardeşi: friedman1 verisinde η ∈ {1,0; 0,3; 0,1; 0,03} için T = 400 ağaca kadar test MSE eğrisi. Betik, erken durdurma deneyini de içerir: öğrenme oranı 0,1 için T, eğitimin %20'lik ayrılmış doğrulama kümesinde en düşük kaybı veren tur olarak seçilir. Test kümesi yalnızca seçilen T'yi raporlamak için kullanılır.

```python
# gbm_deney.py -- ogrenme orani, agac sayisi, erken durdurma
import csv
import numpy as np
from sklearn.datasets import make_friedman1
from sklearn.model_selection import train_test_split
from gbm import GradyanArtirma


def veri(sd):
    X, y = make_friedman1(n_samples=1000, n_features=10, noise=1.0,
                          random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd)


print("== Ogrenme orani x agac sayisi (3 tohum, test MSE)")
T = 400
egri = {}
for eta in [1.0, 0.3, 0.1, 0.03]:
    kayit = []
    for sd in range(3):
        Xtr, Xte, ytr, yte = veri(sd)
        m = GradyanArtirma(T=T, eta=eta, derinlik=3, min_yaprak=5)
        m.fit(Xtr, ytr, Xte, yte)
        kayit.append([g[1] for g in m.gecmis])
    egri[eta] = np.array(kayit).mean(axis=0)
    e = egri[eta]
    print("eta=%.2f  T=50: %.3f  T=100: %.3f  T=400: %.3f  "
          "en iyi T=%d (%.3f)" % (eta, e[49], e[99], e[399],
          int(np.argmin(e)) + 1, e.min()))
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_gbm_egri.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["agac_sayisi", "eta", "test_mse_ort"])
    for eta in egri:
        for t in range(T):
            w.writerow([t + 1, eta, "%.5f" % egri[eta][t]])
```

```python
print("\n== Erken durdurma (eta=0.1): T dogrulamayla secilir")
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    a, v, c, dv = train_test_split(Xtr, ytr, test_size=0.2,
                                   random_state=sd)
    m = GradyanArtirma(T=400, eta=0.1, derinlik=3, min_yaprak=5)
    m.fit(a, c, v, dv)
    tb = int(np.argmin([g[1] for g in m.gecmis])) + 1
    print("tohum %d: secilen T=%3d  test(T secilen)=%.3f  "
          "test(T=400)=%.3f"
          % (sd, tb, np.mean((yte - m.ham(Xte, tb)) ** 2),
             np.mean((yte - m.ham(Xte, 400)) ** 2)))
```

```term
$ python gbm_deney.py
== Ogrenme orani x agac sayisi (3 tohum, test MSE)
eta=1.00  T=50: 6.212  T=100: 6.311  T=400: 6.343  en iyi T=11 (5.122)
eta=0.30  T=50: 2.290  T=100: 2.304  T=400: 2.438  en iyi T=63 (2.235)
eta=0.10  T=50: 3.078  T=100: 2.355  T=400: 2.074  en iyi T=269 (2.061)
eta=0.03  T=50: 7.963  T=100: 4.554  T=400: 2.143  en iyi T=400 (2.143)

== Erken durdurma (eta=0.1): T dogrulamayla secilir
tohum 0: secilen T=249  test(T secilen)=2.094  test(T=400)=2.088
tohum 1: secilen T=278  test(T secilen)=2.497  test(T=400)=2.550
tohum 2: secilen T=321  test(T secilen)=2.202  test(T=400)=2.219
```

Sonuç üç şeyi gösteriyor. Birincisi, η = 1,0 ile model ilk 11 ağaçta en iyi test hatasına (5,122) ulaşıyor ve sonra hata 6,3 civarında yükselip sabitleniyor. Büyük adım, her ağacın artığın tamamını (gürültüsünü de) öğrenmesine yol açar ve model ezberler. İkincisi, η küçüldükçe en iyi T büyür: 0,3'te 63, 0,1'de 269; 0,03'te ise 400 turda hâlâ iyileşme vardı (en iyi T = 400). Yani öğrenme oranı ile ağaç sayısı birbirine bağlıdır; ikisini birlikte ayarlamak gerekir. Üçüncüsü, erken durdurma her zaman kazandırmıyor. Üç tohumda doğrulamayla seçilen T'ler 249, 278 ve 321 çıktı. Test MSE'leri 400 ağaçlık modele göre bir tohumda küçük bir kötüleşme, iki tohumda ise küçük bir iyileşme verdi. Bu sonuç, erken durdurmanın bir sigorta olduğunu, bir hız garantisi olmadığını hatırlatır.

![Şekil 59.8: Öğrenme oranına göre test MSE eğrisi (friedman1, 3 tohum ortalaması). Büyük η hızlı ama erken kararsızlaşır; küçük η yavaş ama daha çok ağaçla iyileşir.](gorseller/b59_gbm_eta.png)

::: ipucu
Pratik kural: önce öğrenme oranını makul küçük bir değere (0,05 ile 0,1 arası) sabitle, sonra en uygun T'yi doğrulama kümesinden bul. Bu, iki parametreyi birlikte aramaktan çok daha ucuzdur.
:::

## 59.11 Modern GBM'ler: XGBoost, LightGBM, CatBoost ve HistGB

Bu bölümdeki kendi gradyan artırma kodumuz çalışır, ama yavaştır: her bölme için her özniteliği sıralar ve Python döngüleri kullanır. Endüstride kullanılan kütüphaneler aynı fikri birkaç güçlü hileyle hızlandırır. Bu hileleri genel hatlarıyla anlatacağız; sayıların kendileri ölçtüğümüz kodlardan gelecek.

**XGBoost** (eXtreme Gradient Boosting) kayıp fonksiyonuna ikinci dereceden bir Taylor açılımı uygular. Her yaprağın değeri gradyan ve Hessian'dan hesaplanır (bizim log-kayıp dalındaki Newton adımının genel hâli). Amaç fonksiyonuna bir düzenlileştirme terimi eklenir: Ω(f) = γT + ½λΣw², yani yaprak sayısına ve yaprak değerlerinin karesine ceza. Bölme seçiminde histogram tabanlı yaklaşım kullanılır (özniteliğin değerleri birkaç yüz kovaya bölünür), bu da sıralamayı hızlandırır. Genel bilgi olarak: XGBoost eksik değerleri öğrenilen bir yöne yönlendirerek kendiliğinden işler.

**LightGBM** aynı fikri iki farklı tasarımla uygular. İlki, histogram tabanlı bölme ile bellek ve süreyi düşürmektir. İkincisi, ağaçları düzey düzey (level-wise) değil **yaprak öncelikli** (leaf-wise) büyütmesidir: her adımda en büyük kayıp azalmasını veren yaprak bölünür. Bu, aynı yaprak sayısında daha düşük kayıp verir, ama ağaçları dengesiz hâle getirip aşırı uydurmaya yol açabilir; bu yüzden `num_leaves` ve `min_data_in_leaf` gibi parametreler kritiktir. Genel bilgi olarak LightGBM ayrıca büyük veride örnek ve öznitelik azaltma (GOSS ve EFB) teknikleri kullanır.

**CatBoost** kategorik öznitelikleri doğrudan işler: her kategori için hedefin (sıralı, kayan) ortalamasını hesaplar ve sızıntıyı önlemek için sıralı boosting kullanır. Bu kütüphane bu bölümde kurulmadı; yalnızca genel bilgi olarak anılıyor.

**HistGradientBoosting** sklearn'in kendi histogram tabanlı gradyan artırmasıdır. XGBoost ve LightGBM'e benzer biçimde çalışır, eksik değerleri doğal olarak işler ve sklearn API'siyle kullanılır.

Bu bölümde XGBoost 3.4.1 ve LightGBM 4.7.0 kuruldu. Karşılaştırmayı kurmak için, gerçek bir İHA bakım tablosuna ihtiyacımız var: sentetik olsa da bir arıza olasılığı, sayısal ve kategorik öznitelikler, bir doğrusal olmayan etkileşim ve gürültü içeren bir tablo. Aşağıdaki kod bu tabloyu üretir.

```python
# uav.py -- sentetik IHA bakim tablosu (sabit tohum)
import numpy as np
import pandas as pd


def uav_veri(n=4000, seed=59, p_dondur=False):
    rng = np.random.default_rng(seed)
    motor = rng.normal(55, 8, n)  # motor sicakligi C
    titresim = 0.3 + rng.gamma(2.0, 0.12, n)  # RMS, g
    akim = rng.normal(15, 2.5, n)  # ortalama akim, A
    gerilim = np.abs(rng.normal(0.25, 0.08, n))  # gerilim dusumu, V
    saat = rng.uniform(0, 600, n)  # toplam ucus saati
    dongu = rng.uniform(0, 800, n)  # batarya dongusu
    gorev = rng.choice(["kesif", "gozetleme", "tasima"], n,
                       p=[0.4, 0.4, 0.2])
    ortam = rng.choice(["ilimli", "sicak", "tozlu"], n,
                       p=[0.5, 0.3, 0.2])
    seri = rng.permutation(100000)[:n]  # tekil kimlik
    # gizli dogru risk: dogrusal olmayan ve etkilesimli
    z = (-2.2 + 0.08 * (motor - 60) + 4.0 * (titresim - 0.5)
         + 3.0 * (titresim > 0.8) * (ortam == "tozlu")
         + 0.004 * np.maximum(saat - 350, 0)
         + 0.8 * (gorev == "tasima") + 0.002 * (dongu - 400) / 4)
    p = 1 / (1 + np.exp(-z))
    ariza = (rng.random(n) < p).astype(int)  # 7 gun ariza
    df = pd.DataFrame({
        "motor_sicaklik": motor, "titresim_rms": titresim,
        "akim_ort": akim, "gerilim_dusum": gerilim,
        "ucus_saati": saat, "batarya_dongu": dongu,
        "gorev": gorev, "ortam": ortam, "seri_no": seri,
    })
    if p_dondur:
        return df, ariza, p
    return df, ariza


if __name__ == "__main__":
    df, y = uav_veri()
    print("satir sayisi:", len(df), " sutun sayisi:", df.shape[1])
    print("ariza orani: %.3f" % y.mean())
```

Veri 4000 kayıt, 9 sütun içerir: motor sıcaklığı, titreşim RMS, ortalama akım, gerilim düşümü, toplam uçuş saati, batarya çevrim sayısı, görev tipi (keşif, gözetleme, taşıma), ortam (ılımlı, sıcak, tozlu) ve bir seri numarası. Seri numarası bilerek eklendi: hedefle hiçbir ilişkisi yok ve tekil bir kimlik. Arıza (7 gün içinde) olasılığı, bu özniteliklerin doğrusal olmayan bir fonksiyonundan gelir: titreşim 0,8 üstünde *ve* ortam tozluysa risk sıçrar, uçuş saati 350'yi geçince risk artar. Arıza oranı yüzde 16'dır.

Karşılaştırma, her model için beş ayrı bölmede (tohum 0–4, yüzde 30 test) aynı protokolü uygular. Kategorik öznitelikler one-hot kodlanır (Bölüm 56'da ayrıntısı var), sayısal öznitelikler olduğu gibi kalır. Taban model, en sık sınıfı her zaman tahmin eden modeldir: İHA tablosunda doğruluğu yüzde 84, AUC'si 0,5'tir; her model bunu aşmak zorunda. Hiperparametreler sabit ve sezgisel seçildi; ayarlanmış sürümü ayrıca vereceğiz.

```python
# kiyas.py -- modellerin test performansi (5 tohum, ayni bolunmeler)
import csv
import time
import warnings
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from uav import uav_veri

warnings.filterwarnings("ignore")
KAT = ["gorev", "ortam"]
```

```python
def modeller():
    return {
        "taban": DummyClassifier(strategy="prior"),
        "lojistik": make_pipeline(StandardScaler(),
                                  LogisticRegression(max_iter=2000)),
        "MLP(32)": make_pipeline(StandardScaler(),
            MLPClassifier((32,), max_iter=1000, random_state=0,
                          early_stopping=True)),
        "RF": RandomForestClassifier(n_estimators=300, random_state=0,
                                     n_jobs=-1),
        "HistGB": HistGradientBoostingClassifier(random_state=0),
        "XGBoost": XGBClassifier(n_estimators=300, max_depth=4,
                                 learning_rate=0.05, random_state=0,
                                 n_jobs=4),
        "LightGBM": LGBMClassifier(n_estimators=300, max_depth=4,
                                   learning_rate=0.05, random_state=0,
                                   verbose=-1, n_jobs=4),
    }


def kat_donustur(m):
    # Kategorik sutunlar icin one-hot kodlama (sadece UAV verisinde)
    ct = make_column_transformer(
        (OneHotEncoder(handle_unknown="ignore"), KAT),
        remainder="passthrough")
    return make_pipeline(ct, m)
```

```python
df, y_u = uav_veri()
bc = load_breast_cancer(as_frame=True)
veriler = [
    ("meme kanseri", bc.frame.drop(columns="target"),
     bc.frame["target"].values, False),
    ("IHA bakim", df.drop(columns=["seri_no"]), y_u, True),
]
satirlar = []
for ad, X, y, katli in veriler:
    print("== %s" % ad)
    for mad in modeller():
        acc, auc, sure = [], [], []
        for sd in range(5):
            a, b, c, d = train_test_split(X, y, test_size=0.3,
                                          random_state=sd, stratify=y)
            m = modeller()[mad]
            if katli:
                m = kat_donustur(m)
            t0 = time.perf_counter()
            m.fit(a, c)
            sure.append(time.perf_counter() - t0)
            p = m.predict_proba(b)[:, 1]
            acc.append(accuracy_score(d, (p >= 0.5).astype(int)))
            auc.append(roc_auc_score(d, p))
        satirlar.append((ad, mad, np.mean(acc), np.std(acc),
                         np.mean(auc), np.std(auc), np.mean(sure)))
        print("%-8s acc=%.4f+-%.4f  AUC=%.4f+-%.4f  sure=%.3fs"
              % satirlar[-1][1:])
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_model_karsilastirma.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["veri", "model", "dogruluk_ort", "dogruluk_ss",
                "auc_ort", "auc_ss", "sure_ort_s"])
    for r in satirlar:
        w.writerow([r[0], r[1]] + ["%.5f" % v for v in r[2:]])
```

```term
$ python kiyas.py
== meme kanseri
taban    acc=0.6257+-0.0000  AUC=0.5000+-0.0000  sure=0.000s
lojistik acc=0.9673+-0.0108  AUC=0.9929+-0.0040  sure=0.006s
MLP(32)  acc=0.8854+-0.0340  AUC=0.9522+-0.0215  sure=0.025s
RF       acc=0.9579+-0.0101  AUC=0.9863+-0.0050  sure=0.335s
HistGB   acc=0.9567+-0.0088  AUC=0.9904+-0.0020  sure=0.388s
XGBoost  acc=0.9591+-0.0064  AUC=0.9892+-0.0037  sure=0.441s
LightGBM acc=0.9567+-0.0102  AUC=0.9906+-0.0034  sure=0.041s
== IHA bakim
taban    acc=0.8400+-0.0000  AUC=0.5000+-0.0000  sure=0.004s
lojistik acc=0.8568+-0.0062  AUC=0.7817+-0.0142  sure=0.007s
MLP(32)  acc=0.8563+-0.0062  AUC=0.7678+-0.0184  sure=0.158s
RF       acc=0.8563+-0.0050  AUC=0.7606+-0.0087  sure=0.402s
HistGB   acc=0.8452+-0.0038  AUC=0.7406+-0.0172  sure=0.169s
XGBoost  acc=0.8517+-0.0054  AUC=0.7445+-0.0218  sure=0.103s
LightGBM acc=0.8515+-0.0038  AUC=0.7421+-0.0203  sure=0.048s
```

Sonuçlar iki veri setinde de aynı yönü gösteriyor. Breast cancer'da lojistik regresyon en yüksek AUC'yi veriyor (0,9929); ağaç topluluklarının AUC'si 0,986 ile 0,991 arasında. İHA bakım tablosunda lojistik regresyon (0,7817) ve küçük MLP (0,7678) en üstte; ağaç topluluklarının AUC'si 0,741 ile 0,761 arasında. Yani veride doğrusal ve yumuşak doğrusal olmayan bir model, ağaçlardan iyi çalıştı. Sürelerde LightGBM ve lojistik regresyon en hızlı; RF ise 0,3 saniyenin üzerinde. Burada dikkat: modeller varsayılan hiperparametrelerle çalıştı, gerçek bir ayarlama yapılmadı. Ayarlamayı bir sonraki betikte, yalnızca eğitim kümesi içinde çapraz doğrulamayla yapıyoruz.

```python
# kiyas_ayarli.py -- tavan (gercek p ile AUC) ve CV ile ayarli GBM
import warnings
import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from uav import uav_veri

warnings.filterwarnings("ignore")
KAT = ["gorev", "ortam"]
df, y, p_gercek = uav_veri(p_dondur=True)
print("gercek olasilik p ile AUC (tavan): %.4f"
      % roc_auc_score(y, p_gercek))

izgara = {"max_depth": [2, 3, 4], "n_estimators": [100, 300],
          "learning_rate": [0.03, 0.1]}
X = df.drop(columns=["seri_no"])
```

```python
for ad, taban, on in [
        ("XGBoost", XGBClassifier(random_state=0, n_jobs=4),
         "xgbclassifier"),
        ("LightGBM", LGBMClassifier(random_state=0, verbose=-1,
                                    n_jobs=4), "lgbmclassifier")]:
    acc, auc = [], []
    for sd in range(5):
        a, b, c, d = train_test_split(X, y, test_size=0.3,
                                      random_state=sd, stratify=y)
        ct = make_column_transformer(
            (OneHotEncoder(handle_unknown="ignore"), KAT),
            remainder="passthrough")
        m = make_pipeline(ct, taban)
        # Ayar yalnizca egitim kumesinde, 3 katli CV ile yapilir
        gs = GridSearchCV(m, {on + "__" + k: v
                              for k, v in izgara.items()},
                          cv=3, scoring="roc_auc")
        gs.fit(a, c)
        p = gs.predict_proba(b)[:, 1]
        acc.append(accuracy_score(d, (p >= 0.5).astype(int)))
        auc.append(roc_auc_score(d, p))
    print("%-8s CV ayarli: acc=%.4f+-%.4f  AUC=%.4f+-%.4f"
          % (ad, np.mean(acc), np.std(acc), np.mean(auc),
             np.std(auc)))
```

```term
$ python kiyas_ayarli.py
gercek olasilik p ile AUC (tavan): 0.7822
XGBoost  CV ayarli: acc=0.8575+-0.0046  AUC=0.7748+-0.0130
LightGBM CV ayarli: acc=0.8587+-0.0047  AUC=0.7758+-0.0132
```

Ayarlama, boosting modellerini biraz iyileştirdi: XGBoost AUC'si 0,7445'ten 0,7748'e, LightGBM 0,7421'den 0,7758'e çıktı. Ama lojistik regresyonun 0,7817'si hâlâ önde. Betiğin üst satırı, tavanı veriyor: veriyi üreten gerçek olasılıkların (p) kendisi AUC'de 0,7822 veriyor. Yani hiçbir model, veri üreticinin bildiğinden fazlasını öğrenemez; lojistik regresyon bu tavana neredeyse ulaşmış durumda.

## 59.12 Tablo verisinde neden hâlâ kral?

Derin öğrenme görüntü ve dil alanında ağaç topluluklarını geride bıraktı. Tablo verisinde ise ağaç tabanlı modeller hâlâ çoğu zaman en güçlü başlangıç noktasıdır. Genel bilgi olarak, bu gözlemi sistematik bir karşılaştırmayla raporlayan çalışmalar var (Grinsztajn, Oyallon ve Varoquaux, 2022); bu bölümde o çalışmanın sonuçlarını yeniden üretmedik, ama kendi küçük kıyasımız aynı yönü gösteriyor. Bunun nedenleri üç başlıkta toplanabilir.

Birincisi, tablo verisinin öznitelikleri heterojendir. Bir sütun sıcaklık, bir sütun görev tipi, bir sütun sayım olabilir. Ağaç bu karışımı kendiliğinden işler; sinir ağı ise her sütunu ölçeklemek ve kodlamak zorundadır, ve bu kodlamanın kalitesi sonucu belirler. İkincisi, tablo verisinin etkileşimleri genellikle birkaç öznitelik düzeyindedir: "titreşim yüksek ve ortam tozlu" gibi. Ağaç bunu doğrudan bir yol olarak yakalar. Üçüncüsü, tablo veri setleri genellikle küçüktür (birkaç bin satır); bu ölçekte derin ağlar aşırı uydurmaya ve hiperparametre hassasiyetine açıktır, ağaçlar ise daha kararlı çalışır.

Ama aynı kıyas bir uyarı da içerir. Şekil 59.9'da iki veri setini yan yana koyduk. Breast cancer'da lojistik regresyon, doğrusal olmayan topluluklardan daha iyi çıktı. Bunun nedeni, veri setinin sınıflarının büyük ölçüde doğrusal olarak ayrılabilmesi. İHA tablosunda da lojistik regresyon tavana yakın çıktı, ama bunun bir kısmı kendi üretim sürecimizden kaynaklanıyor: riskin logit'i büyük ölçüde doğrusal terimlerden oluşuyor (her terim bilerek eklendi). Yani bu veride doğrusal modelin kazanması beklenirdi; gerçek bir İHA filosunda etkileşimler ve eşikler daha belirgin olabilir. Bu nedenle sonucu "lojistik her zaman daha iyi" diye değil, "bu veride doğrusal model tavana yaklaştı" diye okumalısın.

![Şekil 59.9: İki veri setinde yedi modelin test AUC değerleri (5 tohum ortalaması ± standart sapma). Taban model 0,5'te; breast cancer'da doğrusal ve topluluk modelleri birbirine çok yakın; İHA tablosunda lojistik regresyon tavana en yakın olan.](gorseller/b59_model_karsilastirma.png)

Bu bölümün dersi şu: tablo verisinde önce basit ve güçlü bir taban (lojistik regresyon ya da varsayılan RF) kur, sonra topluluk modelleriyle karşılaştır. Derin bir ağın tablo verisinde kazanması için belirgin bir sebep gerekir: çok büyük veri, yüksek boyutlu özniteliklerin yapısı ya da bir öznitelik öğrenme (embedding) ihtiyacı. Bu sebepler yoksa, derin ağ maliyeti artırır, açıklanabilirliği düşürür, ama kazandırmaz.

## 59.13 Yorumlanabilirlik: önem ölçütleri ve kısmi bağımlılık

Bir modelin hangi öznitelikleri kullandığını bilmek, mühendislik için hem hata ayıklama hem de güven için gereklidir. Ağaç topluluklarında iki temel önem ölçütü vardır. **Safsızlık önemi** (impurity importance, sklearn'de `feature_importances_`), her öznitelik için eğitim sırasında sağlanan toplam safsızlık azalmasını sayar. Hesabı ucuzdur, ama yanlıdır: çok değerli (yüksek kardinaliteli) öznitelikler, yani çok sayıda farklı değer alan sürekli ya da kimlik benzeri sütunlar, eğitim verisini kolayca ezberletir ve yanıltıcı biçimde yüksek önem alır. **Permütasyon önemi** (permutation importance) ise bir öznitelik sütununu test kümesinde karıştırır ve performans düşüşünü ölçer. Eğitim verisinden bağımsız olduğu için bu yanlılığa sahip değildir, ama her öznitelik için modeli yeniden değerlendirir.

Aşağıdaki betik, seri numarasının iki ölçütte nasıl göründüğünü gösterir ve ayrıca titreşimin kısmi bağımlılık grafiğini (PDP) hesaplar. PDP, bir özniteliğin tüm diğerleri üzerinden ortalanmış etkisini gösterir: x eksenindeki değeri sabitleyip, diğer öznitelikleri veri üzerinde gezdirip tahminlerin ortalamasını alır.

```python
# onem.py -- safsizlik onemi, permutasyon onemi ve kismi bagimlilik
import csv
import warnings
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.inspection import partial_dependence
from uav import uav_veri

warnings.filterwarnings("ignore")
df, y = uav_veri()
a, b, c, d = train_test_split(df, y, test_size=0.3, random_state=0,
                              stratify=y)
ct = make_column_transformer(
    (OneHotEncoder(handle_unknown="ignore"), ["gorev", "ortam"]),
    remainder="passthrough")
Xa = ct.fit_transform(a)
Xb = ct.transform(b)
isim = [s.split("__")[-1] for s in ct.get_feature_names_out()]
rf = RandomForestClassifier(n_estimators=300, random_state=0,
                            n_jobs=-1).fit(Xa, c)
saf = rf.feature_importances_
per = permutation_importance(rf, Xb, d, n_repeats=20, random_state=0,
                             scoring="roc_auc")
sira = np.argsort(-saf)
```

```python
print("%-18s %10s %12s" % ("oznitelik", "safsizlik", "permutasyon"))
for i in sira:
    print("%-18s %10.4f %12.4f"
          % (isim[i], saf[i], per.importances_mean[i]))
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_onem.csv", "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["oznitelik", "safsizlik_onemi", "permutasyon_onemi",
                "permutasyon_ss"])
    for i in sira:
        w.writerow([isim[i], "%.5f" % saf[i],
                    "%.5f" % per.importances_mean[i],
                    "%.5f" % per.importances_std[i]])
```

```python
# Kismi bagimlilik: titresim_rms (seri_no olmadan, HistGB)
maske = np.array([n != "seri_no" for n in isim])
hg = HistGradientBoostingClassifier(random_state=0)
hg.fit(Xa[:, maske], c)
j = list(np.array(isim)[maske]).index("titresim_rms")
pdp = partial_dependence(hg, Xa[:, maske], features=[j],
                         grid_resolution=8, kind="average",
                         response_method="predict_proba",
                         method="brute")
for g, v in zip(pdp["grid_values"][0], pdp["average"][0]):
    print("titresim=%.3f  ortalama olasilik=%.4f" % (g, v))
```

```term
$ python onem.py
oznitelik           safsizlik  permutasyon
titresim_rms           0.2256       0.1640
motor_sicaklik         0.1417       0.0548
ucus_saati             0.1209       0.0169
batarya_dongu          0.1112       0.0033
seri_no                0.1094       0.0015
akim_ort               0.1066      -0.0047
gerilim_dusum          0.1058      -0.0082
ortam_tozlu            0.0172       0.0027
gorev_tasima           0.0149       0.0011
ortam_ilimli           0.0138      -0.0003
ortam_sicak            0.0119      -0.0003
gorev_gozetleme        0.0109       0.0002
gorev_kesif            0.0101      -0.0005
titresim=0.343  ortalama olasilik=0.0584
titresim=0.415  ortalama olasilik=0.0477
titresim=0.488  ortalama olasilik=0.1140
titresim=0.560  ortalama olasilik=0.1385
titresim=0.633  ortalama olasilik=0.1358
titresim=0.705  ortalama olasilik=0.2343
titresim=0.778  ortalama olasilik=0.3319
titresim=0.850  ortalama olasilik=0.4872
```

Seri numarası safsızlık önemi listesinde beşinci sırada (0,1094) geliyor; motor sıcaklığı, uçuş saati ve batarya çevrimiyle aynı büyüklük mertebesinde. Permütasyon önemi ise onu neredeyse sıfıra indiriyor (0,0015). Bunun nedeni, seri numarasının eğitim verisinde ezber için kullanılabilmesi: her kayıt farklı bir kimlik taşıdığı için ağaç bu sütunla yaprakları saflaştırabilir, ama test kümesinde bu bilgi bir şey öğretmez. Bu, safsızlık önemi için bilinen bir yanlılıktır (Strobl ve arkadaşları, 2007; genel bilgi). Şekil 59.10 iki ölçütü yan yana koyuyor.

Titreşim önemi her iki ölçütte de en büyük. Kısmi bağımlılık tablosu, titreşim 0,34'ten 0,85'e çıktıkça tahmin edilen arıza olasılığının 0,058'den 0,487'ye yükseldiğini gösteriyor. Eğri monoton değil; 0,41'de küçük bir düşüş var, bu da sınırlı veriden gelen bir gürültü olabilir. Sonuç, titreşimle arıza arasındaki ilişkinin kabaca artan ama doğrusal olmayan olduğunu düşündürüyor. Kısmi bağımlılığın iki sınırı var: öznitelikler birbirine bağlıysa ortalama, gerçekte hiç gözlenmeyen kombinasyonlara dayanabilir; ve bir eğri yalnızca ortalama etkiyi gösterir, bireysel bir tahmini açıklamaz.

![Şekil 59.10: İHA bakım tablosunda iki önem ölçütü. Mavi çubuklar eğitim safsızlığı önemi, kırmızı çubuklar test kümesinde permütasyon önemi (AUC düşüşü). Seri numarası yalnızca safsızlıkta yükselir.](gorseller/b59_onem.png)

Bireysel tahminleri açıklamak için SHAP gibi yöntemler kullanılır (genel bilgi). SHAP, Shapley değerlerini kullanarak bir tahminin her öznitelik katkısına bölünmesini sağlar; bu bölümde kurmadık. Savunma uygulamalarında, bir kararın gerekçesinin denetlenebilir olması gerektiğinde bu tür açıklama araçları önemlidir; bu konu Bölüm 78'de ele alınacak.

## 59.14 Pratik: hiperparametreler, kategorik veri, eksik değer ve dengesizlik

Bir ağaç topluluğu üretim ortamına girmeden önce birkaç pratik karar verilmelidir. Hiperparametreler arasında en etkili olanlar tabloda özetlenmiştir. Bunları seçerken Bölüm 57'deki iç içe çapraz doğrulama disiplinini uygula: ayarlamayı yalnızca eğitim kümesi içinde yap, test kümesini son raporlamaya sakla. Bu bölümdeki `kiyas_ayarli.py` betiği bunu yapar.

| Parametre | Ne kontrol eder | Yükselince | Tipik başlangıç |
|---|---|---|---|
| derinlik (max_depth) | Ağacın karmaşıklığı | Sapma düşer, varyans artar | 3–6 (boosting), sınırsız (RF) |
| öğrenme oranı (η) | Her ağacın katkısı | Hızlı ama kararsız | 0,03–0,1 |
| ağaç sayısı (T) | Toplam tur | Eğitim süresi, aşırı uydurma riski | η ile birlikte ayarla |
| min_samples_leaf | Yaprak alt sınırı | Düzgünleşme, sapma artar | 1–20 |
| max_features | Her bölmede öznitelik | Ağaçlar benzeşir | √d (sınıflama) |

Kategorik öznitelikler için iki yol var. One-hot kodlama her kategoriyi ayrı bir ikili sütun yapar; bu bölümde kullandığımız yol budur ve kategori sayısı küçük olduğunda iyi çalışır. Kategori sayısı büyüdüğünde sütun sayısı patlar; bu durumda hedef kodlama (target encoding) ya da CatBoost'un yerleşik işleyişi kullanılır. Hedef kodlama sızıntıya açıktır: kodlamayı eğitim kümesi dışında yaparsan (ya da iç içe katlarla) sızıntıyı önlersin. Kategorik işleme ve sızıntı Bölüm 56 ve 57'de ayrıntılı ele alınacak.

Eksik değerler ağaçlar için bir sorun değildir: XGBoost ve HistGradientBoosting, eksik değerler için bir yön öğrenir. Ama eksik değerin bir anlamı varsa (sensör kapalıysa, ölçüm yapılmadıysa) bunu ayrı bir ikili öznitelik olarak da eklemek faydalıdır; yoksa model "eksik" bilgisini kaybedebilir.

Sınıf dengesizliği, arıza tespitinde olduğu gibi, tipik bir durumdur: yüzde 16 pozitif sınıf. Bu veride taban doğruluk yüzde 84'tür ve doğruluk tek başına yanıltıcıdır. Çözüm üç yoldan biridir: sınıf ağırlığı vermek (`class_weight`), karar eşiğini değiştirmek (olasılık çıktısının 0,5 yerine maliyete göre seçilmiş bir eşik) ya da değerlendirmeyi AUC ve kesinlik-duyarlılık eğrisiyle yapmak. Bölüm 57.5 ve 57.6, eşiğin maliyetle nasıl seçileceğini gösteriyor.

## 59.15 Gömülü çıkarım: ağacı C if-else koduna çevirmek

Bir karar ağacının en büyük avantajı, eğitildikten sonra bir fonksiyon gibi çalışmasıdır: girdi, bir dizi karşılaştırma ve dalla yaprağa iner. Bu, bir mikrodenetleyicide düşük bellek ve deterministik süreyle uygulanabilir. Bölüm 46'da TinyML'nin bu tür küçük modelleri nasıl taşıdığını gördük; bu bölümde bir ağacı doğrudan C kaynak koduna çeviriyoruz.

Dönüşüm bir özyinelemeli fonksiyonla yapılır: her iç düğüm bir `if (x[i] <= eşik)` karşılaştırmasına, her yaprak bir `return` ifadesine dönüşür. Ayrıca iki yardımcı var: eşikleri float32'ye yuvarlar (C'de `float` karşılaştırmasıyla Python'un `float64` karşılaştırması aynı sonucu vermelidir) ve aynı sınıfa giden iki yaprağı tek yapraklı bir düğüme sadeleştirir.

```python
# c_uret.py -- egitilmis KararAgaci'ni C if-else koduna cevirir
import numpy as np


def c_kodu_uret(kok, ad="agac_tahmin", ozellik_say=3):
    satirlar = []
    satirlar.append("/* otomatik uretildi: c_uret.py */")
    satirlar.append("#include <stdint.h>")
    satirlar.append("")
    satirlar.append("uint8_t %s(const float x[%d]) {"
                    % (ad, ozellik_say))

    def yaz(d, girinti):
        bosluk = "    " * girinti
        if d.sol is None:
            sinif_no = int(np.argmax(d.deger))
            satirlar.append(bosluk + "return %d;" % sinif_no)
            return
        kosul = "if (x[%d] <= %.9gf) {" % (d.ozellik, float(d.esik))
        satirlar.append(bosluk + kosul)
        yaz(d.sol, girinti + 1)
        satirlar.append(bosluk + "} else {")
        yaz(d.sag, girinti + 1)
        satirlar.append(bosluk + "}")

    yaz(kok, 1)
    satirlar.append("}")
    return "\n".join(satirlar) + "\n"
```

```python
def esigi_float32_yap(kok):
    # C'de float karsilastirmasi icin esikleri float32 yap
    d = [kok]
    while d:
        n = d.pop()
        if n.sol is not None:
            n.esik = float(np.float32(n.esik))
            d.extend([n.sol, n.sag])


def ayni_yapraklari_birlestir(d):
    # Ayni sinifa giden iki yaprak varsa dugumu yaprak yap
    if d.sol is None:
        return d
    d.sol = ayni_yapraklari_birlestir(d.sol)
    d.sag = ayni_yapraklari_birlestir(d.sag)
    if (d.sol.sol is None and d.sag.sol is None
            and int(np.argmax(d.sol.deger))
            == int(np.argmax(d.sag.deger))):
        d.sol = None
        d.sag = None
    return d
```

Üretici kodu çalıştıran betik, derinlik 3 bir ağacı üç özniteliğle (titreşim, motor sıcaklığı, uçuş saati) eğitir, C dosyasını yazar ve Python tahminlerini bir test girdisi kümesine karşı kaydeder. Test girdisi, öznitelik aralıklarında düzgün dağılmış 20000 rastgele noktadır; böylece yalnızca eğitim dağılımına bağlı kalmayan bir karşılaştırma yapılır.

```python
# uret_c.py -- agaci C koduna cevir, test girdisi ve Python cevabi yaz
import numpy as np
from agac import KararAgaci
from c_uret import c_kodu_uret, esigi_float32_yap
from uav import uav_veri

df, y = uav_veri()
X = df[["titresim_rms", "motor_sicaklik", "ucus_saati"]].values
X = X.astype(np.float32)
agac = KararAgaci(max_derinlik=3).fit(X[:3000], y[:3000])
esigi_float32_yap(agac.kok)            # C ile ayni (float32) esikler
with open("agac_gomulu.c", "w", encoding="utf-8", newline="\n") as f:
    f.write(c_kodu_uret(agac.kok, ozellik_say=3))
print("yaprak:", agac.yaprak_sayisi(), " derinlik:", agac.derinlik())

r = np.random.default_rng(59)
lo, hi = X.min(axis=0), X.max(axis=0)
G = (lo + (hi - lo) * r.random((20000, 3))).astype(np.float32)
with open("girdi2.txt", "w") as f:
    for row in G:
        f.write("%.9g %.9g %.9g\n" % tuple(row))
py = agac.tahmin(G.astype(np.float64)).astype(int)
with open("py_cikti2.txt", "w") as f:
    f.write("\n".join(str(v) for v in py) + "\n")
print("python sinif 1 sayisi:", int(py.sum()))
```

```term
$ python uret_c.py
yaprak: 7  derinlik: 3
python sinif 1 sayisi: 8707
```

Üretilen C dosyası, yedi yapraklı bir ağacın tamamıdır:

```c
/* otomatik uretildi: c_uret.py */
#include <stdint.h>

uint8_t agac_tahmin(const float x[3]) {
    if (x[0] <= 0.822449803f) {
        if (x[1] <= 60.3237228f) {
            if (x[0] <= 0.697952151f) {
                return 0;
            } else {
                return 0;
            }
        } else {
            if (x[0] <= 0.460168988f) {
                return 0;
            } else {
                return 0;
            }
        }
    } else {
        if (x[0] <= 1.21619737f) {
            if (x[1] <= 43.5918274f) {
                return 0;
            } else {
                return 1;
            }
        } else {
            return 1;
        }
    }
}
```

Derleyici ve test kodu için küçük bir C sürücüsü yazıyoruz. Okuduğu her satırdaki üç float'ı ağaca verir ve sonucu yazar. Bu sürücü, ağacın kendisinden ayrı olarak derlenir.

```c
/* harness.c -- girdi.txt ornekleri icin agac_tahmin */
#include <stdio.h>
#include <stdint.h>

uint8_t agac_tahmin(const float x[3]);

int main(void) {
    float x[3];
    while (scanf("%f %f %f", &x[0], &x[1], &x[2]) == 3) {
        printf("%u\n", (unsigned)agac_tahmin(x));
    }
    return 0;
}
```

Derlemeyi iki yoldan yapıyoruz. Önce Windows ortamındaki WSL'de gcc ile, bellek hatalarını ve tanımsız davranışı yakalayan AddressSanitizer ve UndefinedBehaviorSanitizer açık olarak. Sonra ARM Cortex-M4 (STM32 ailesi) için GNU Arm araç zinciriyle, optimizasyon düzeyi `-Os` ile. Bölüm 43'te gömülü C'nin kısıtlarını gördük; burada ayrıca makine kodu boyutunu ölçüyoruz.

```term
$ wsl gcc -O2 -Wall -Wextra -std=c11 \
    -fsanitize=address,undefined harness.c agac_gomulu.c \
    -o harness_asan
$ wsl ./harness_asan < girdi2.txt > c_cikti2.txt
$ python karsilastir_c.py
ornek: 20000  C: 20000  uyusmayan: 0  C sinif1: 8707
```

Derleme uyarısız geçti ve ASan ile UBSan hiçbir hata raporlamadı; 20000 girdinin tamamında C ve Python aynı sınıfı verdi. Sınıf 1 sayısı 8707 olduğu için test, iki sınıfı da yeterince kapsıyor. Şimdi ARM tarafı:

```term
$ arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb \
    -mfloat-abi=hard -mfpu=fpv4-sp-d16 -Os -std=c11 \
    -c agac_gomulu.c -o agac_gomulu.o
$ arm-none-eabi-size agac_gomulu.o
   text   data    bss    dec    hex filename
     76      0      0     76     4c agac_gomulu.o
```

Fonksiyonun `.text` bölümü 76 bayt tutuyor. Bu, yedi yaprağın tamamı ve kayan nokta karşılaştırmaları dâhil. Bir mikrodenetleyicinin birkaç yüz kilobaytlık flash'ına kıyasla bu ihmal edilebilir. Asıl kısıt zamandır: bu ağaç en fazla üç karşılaştırma yapar, yani sabit ve çok kısa bir süre.

Sadeleştirme bu ölçümde ilginç bir sonuç veriyor. Bu ağacın bir düğümünün iki dalı da aynı sınıfa (0) gidiyor; bu dal kaynak kodda gereksiz. Sadeleştirilmiş sürümü ürettiğimizde yaprak sayısı yediden dörde düştü. Ama makine kodu tarafında fark yok: iki sürümde de üç karşılaştırma ve üç dönüş komutu var. Derleyici `-Os` ile zaten gereksiz dalı siliyor. Yani kaynak sadeleşmesi, derleyicinin yaptığını elle yapmış oluyor: okunabilirlik kazanılıyor, makine kodu aynı kalıyor. Bu, Bölüm 24'teki dal tahmininin sınırlarıyla da ilgilidir: dalların sayısı kadar, dallar yanlış tahmin edilirse ceza da artar; bu yüzden tablo tabanlı ya da dalsız gerçeklemeler (Bölüm 24.6) büyük ağaçlarda tercih edilebilir.

::: dikkat
Bir ağacı gömülü koda çevirdiğinde kendi başına bir doğruluk garantisi yoktur. Gömülü versiyonun Python versiyonuyla aynı girdilerde aynı sonucu verdiğini ölçmek zorundasın, özellikle eşiklerin float32'ye yuvarlanmasıyla. Bu bölümde bunu yaptık; kendi projenizde de yap.
:::

## Çözümlü Örnekler

Aşağıdaki dört örnek, Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Her örneğin sonunda elle izlenebilecek bir tablo ve bir varyasyon sorusu var. Sayıların hepsi bu bölümdeki betiklerin çıktısıdır.

### Örnek 1 (★): Sıcaklık eşiğini Gini ile elle seçmek

**Adım 1 — Anla.** Sekiz motor kaydı var: sıcaklık (°C) ve arıza durumu (1: arıza, 0: normal). Soru: kökte tek bir eşik bölmesi yapacaksak, Gini kazancına göre en iyi eşik nedir? Kökteki safsızlık için dört arıza, dört normal olduğu için Gini = 1 − (0,5² + 0,5²) = 0,5.

**Adım 2 — Örnekle.** Veriyi sıcaklığa göre sıralayıp komşu değerlerin orta noktalarını aday eşik yapıyoruz. Yedi aday var:

| Sıcaklık | 62 | 70 | 74 | 78 | 83 | 88 | 92 | 97 |
|---|---|---|---|---|---|---|---|---|
| Arıza | 0 | 0 | 1 | 0 | 1 | 1 | 1 | 0 |

**Adım 3 — Kaba çöz.** Her aday için sol ve sağ tarafın Gini'sini hesapla, ağırlıklı ortalamayı al, kazancı kökteki 0,5'ten çıkar.

| Eşik t | Sol (n, arıza) | Sağ (n, arıza) | G_sol | G_sağ | Ağırlıklı | Kazanç |
|---|---|---|---|---|---|---|
| 66,0 | 1, 0 | 7, 4 | 0,0000 | 0,4898 | 0,4286 | 0,0714 |
| 72,0 | 2, 0 | 6, 4 | 0,0000 | 0,4444 | 0,3333 | 0,1667 |
| 76,0 | 3, 1 | 5, 3 | 0,4444 | 0,4800 | 0,4667 | 0,0333 |
| 80,5 | 4, 1 | 4, 3 | 0,3750 | 0,3750 | 0,3750 | 0,1250 |
| 85,5 | 5, 2 | 3, 2 | 0,4800 | 0,4444 | 0,4667 | 0,0333 |
| 90,0 | 6, 3 | 2, 1 | 0,5000 | 0,5000 | 0,5000 | 0,0000 |
| 94,5 | 7, 4 | 1, 0 | 0,4898 | 0,0000 | 0,4286 | 0,0714 |

Örneğin t = 72 satırında: sol iki örnek (62 ve 70) ikisi de normal, Gini = 0. Sağ altı örnekte dört arıza var, p = 2/3, Gini = 1 − (4/9 + 1/9) = 4/9 ≈ 0,4444. Ağırlıklı ortalama (2·0 + 6·0,4444)/8 = 0,3333 ve kazanç 0,5 − 0,3333 = 0,1667.

**Adım 4 — Örüntü.** En büyük kazanç t = 72'de. Dikkat et: kazancı büyük yapan şey, sol tarafın tamamen saf (yalnızca normal) olması. t = 80,5'te de kazanç 0,1250 ile yüksek; orada iki taraf da karışık, ama daha dengeli. Gini, "tek bir saf yaprak" ile "dengeli iki karışık yaprak" arasında saf olanı tercih eder; bu yüzden tek bir saf küme olan sol taraf kazandı.

**Adım 5 — İyileştir.** Burada yedi aday elle sayıldı. Veri büyüdükçe bu tablo büyür, ama Bölüm 59.3'teki yöntem aynı işi tek geçişle yapar: sıralama bir kez, kümülatif sayımlar her aday için sabit iş. Bu yüzden n büyüdükçe fark açılır.

**Adım 6 — Doğrula.** Elle bulunan sonucu kodla karşılaştıralım: `en_iyi_bolme_siniflama` fonksiyonu bu veri için eşik 72,0 ve kazanç 0,16667 döndürmelidir. Bu fonksiyon Bölüm 59.4'teki `agac.py` dosyasında tanımlı; betiği yazmadan kendi elinle yaptığın tabloyla çıktıyı karşılaştır. Eşleşiyorsa Gini kazancı hesabını anlamışsın demektir.

**Bunu AI'sız yazabilir misin?** Sekiz örneğin sıcaklığı yerine iki özniteliği olsaydı (sıcaklık ve titreşim), kökte hangi özniteliği seçersin ve bunun için hangi tabloyu çizersin? Kağıt üzerinde iki özniteliğin en iyi kazancını karşılaştırmak için hangi üç bilgiye ihtiyacın var?

### Örnek 2 (★★): Torbalamada varyans azalması ve OOB kümesi

**Adım 1 — Anla.** Her ağacın tahmininin varyansı σ² = 1 ve aralarındaki korelasyon ρ olan B ağacın ortalamasını alıyoruz. Soru iki yönlü: (a) ortalamanın varyansı B ve ρ ile nasıl değişir? (b) Bir bootstrap'te bir örnek hangi olasılıkla hiç seçilmez ve bu OOB kümesini nasıl oluşturur?

**Adım 2 — Örnekle.** Formül: Var = ρσ² + (1 − ρ)σ²/B. Üç ρ ve üç B için değerleri önce kendi kendine hesaplayalım:

| ρ | B = 1 | B = 10 | B = 100 |
|---|---|---|---|
| 0 | 1,000 | 0,100 | 0,010 |
| 0,3 | 1,000 | 0,370 | 0,307 |
| 0,9 | 1,000 | 0,910 | 0,901 |

**Adım 3 — Kaba çöz.** Birkaç hücreyi elle doğrula. ρ = 0,3, B = 10: 0,3 + 0,7/10 = 0,37. ρ = 0,9, B = 100: 0,9 + 0,1/100 = 0,901. ρ = 0, B = 10: 0 + 1/10 = 0,1. OOB tarafında: n = 6 için bir örneğin bir bootstrap'te seçilmeme olasılığı (5/6)⁶ ≈ 0,3349.

**Adım 4 — Örüntü.** Sütunlara bakınca ρ'nun sınır koyduğunu görüyorsun: ρ = 0,9 satırında B = 1'den 100'e çıkmak varyansı yalnızca 1,000'den 0,901'e indiriyor; ρ'nun payı kalıcı. ρ = 0 satırında ise her B artışı kazandırıyor. Demek ki topluluğun kazancı, ağaçların birbirinden ne kadar farklı olduğuna bağlı.

**Adım 5 — İyileştir.** ρ'yu düşürmenin yolu her bölmede öznitelik alt örneklemesidir: sınıflamada √d (d = 20 için 4). Bu, Bölüm 59.9'daki rastgele ormanın tam amacıdır. Ayrıca OOB kümesi bedavadır; doğrulama kümesi ayırmana gerek kalmaz.

**Adım 6 — Doğrula.** Simülasyon değerleri (`korelasyon.py` çıktısı) formülle uyuşuyor: ρ = 0,3, B = 10 için simülasyon 0,3618, formül 0,3700. OOB kümesini de elle doğrulayalım. Bölüm 59.8'deki `ornek_oob.py` çıktısındaki üç bootstrap için, her örneğin kaç ağaçta OOB olduğunu sayan tablo:

| Örnek | Ağaç 1 (sayım) | Ağaç 2 (sayım) | Ağaç 3 (sayım) | OOB ağaç sayısı |
|---|---|---|---|---|
| 0 | 1 | 2 | 2 | 0 |
| 1 | OOB (0) | 1 | OOB (0) | 2 |
| 2 | OOB (0) | 2 | OOB (0) | 2 |
| 3 | 2 | OOB (0) | OOB (0) | 2 |
| 4 | 3 | 1 | OOB (0) | 1 |
| 5 | OOB (0) | OOB (0) | 4 | 2 |

Örnek 0 üç ağacın üçünde de seçilmiş; OOB tahmini için kullanılabilecek bir ağaç yok. Bu örnekler için OOB tahmini tanımsızdır, bu yüzden OOB hatası yalnızca oy alan örnekler üzerinden hesaplanır (kodda `oob_say > 0` koşulu).

**Bunu AI'sız yazabilir misin?** B = 25 ağaç ve ρ = 0,5 için varyansı hesapla. Sonra ρ = 0,5'te B'yi 25'ten 250'ye çıkarmanın kazancının neden 0,02'den küçük olduğunu açıklayabilir misin?

### Örnek 3 (★★): Gradyan artırmanın üç adımı

**Adım 1 — Anla.** Beş noktalı bir regresyon verisi var ve kare kayıpla gradyan artırma yapacağız. Öğrenme oranı η = 0,5, her ağaç bir karar kütüğü (derinlik 1). Soru: üç adım sonra tahmin ne olur ve artık nasıl küçülür?

**Adım 2 — Örnekle.** Veri: x = 1, 2, 3, 4, 5 ve y = 2,0; 2,2; 1,8; 4,1; 4,3. İlk tahmin F₀, tüm y'lerin ortalamasıdır: (2,0 + 2,2 + 1,8 + 4,1 + 4,3)/5 = 2,88.

**Adım 3 — Kaba çöz.** Birinci adımda artık r = y − F₀ = [−0,88; −0,68; −1,08; 1,22; 1,42]. En iyi kütük eşiği 3,5'tir (sol üç örnek, sağ iki örnek). Sol yaprak ortalaması (−0,88 − 0,68 − 1,08)/3 = −0,88; sağ yaprak (1,22 + 1,42)/2 = 1,32. F₁ = F₀ + 0,5·h₁: sol üç için 2,88 − 0,44 = 2,44; sağ iki için 2,88 + 0,66 = 3,54.

**Adım 4 — Örüntü.** Her adımda eşik aynı kalıyor (3,5) ve artık ortalamaya yaklaşıyor. İkinci adımın artıkları [−0,44; −0,24; −0,64; 0,56; 0,76]: yani kalan hata yarıya inmiş. Bu, F'in her adımda hedefe bir öncekinin yarısı kadar yaklaşmasının sonucu. Adım büyüklüğü η bu hızı belirliyor.

**Adım 5 — İyileştir.** η = 0,5, tam adım (η = 1) yerine daha yavaş ama dengeli. Bölüm 59.10'daki friedman1 deneyinde η = 0,1 en iyi sonucu verdi ve η = 0,03 T = 400'de henüz yakınsamamıştı. Burada beş noktada bunu görmek için üç adım yeter; pratikte yüzlerce adım gerekir.

**Adım 6 — Doğrula.** Aşağıdaki betik elle yaptığımız hesabı kodla yapar. Kod, bu bölümdeki `gbm.py` içindeki `GradyanArtirma` sınıfının değil, tek bir `KararAgaci` kütüğünün kullanıldığı açık bir döngü.

```python
# ornek_gbm.py -- 5 noktada 3 adimlik gradyan artirma izi (eta=0.5)
import numpy as np
from agac import KararAgaci

x = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
y = np.array([2.0, 2.2, 1.8, 4.1, 4.3])
eta = 0.5
F = np.full(5, y.mean())
print("F0 =", np.round(F, 4).tolist())
for t in range(3):
    r = y - F                 # artik (negatif gradyan)
    agac = KararAgaci(mod="regresyon", max_derinlik=1,
                      min_yaprak=1).fit(x, r)
    h = agac.olasilik(x)  # yaprak ortalamalari
    F = F + eta * h
    print("adim %d: r=%s" % (t + 1, np.round(r, 2).tolist()))
    print("        h=%s" % np.round(h, 3).tolist())
    print("        F=%s" % np.round(F, 3).tolist())
```

```term
$ python ornek_gbm.py
F0 = [2.88, 2.88, 2.88, 2.88, 2.88]
adim 1: r=[-0.88, -0.68, -1.08, 1.22, 1.42]
        h=[-0.88, -0.88, -0.88, 1.32, 1.32]
        F=[2.44, 2.44, 2.44, 3.54, 3.54]
adim 2: r=[-0.44, -0.24, -0.64, 0.56, 0.76]
        h=[-0.44, -0.44, -0.44, 0.66, 0.66]
        F=[2.22, 2.22, 2.22, 3.87, 3.87]
adim 3: r=[-0.22, -0.02, -0.42, 0.23, 0.43]
        h=[-0.22, -0.22, -0.22, 0.33, 0.33]
        F=[2.11, 2.11, 2.11, 4.035, 4.035]
```

Çıktı elle hesabımızla birebir: F₀ = 2,88, artıklar, kütük değerleri ve F güncellemeleri eşleşiyor. Ortalama kare hata da düşüyor: ilk durumda artığın ortalama karesi 1,1816; birinci adımdan sonra 0,3104, ikinci adımdan sonra 0,0926 ve üçüncüden sonra 0,0381. Bu sayılar, bu bölümde kodla doğruladığımız bir iz tablosudur:

| Adım | r (artık) | h (kütük) | F (η = 0,5) |
|---|---|---|---|
| 0 | — | — | 2,88 2,88 2,88 2,88 2,88 |
| 1 | −0,88 −0,68 −1,08 1,22 1,42 | −0,88 −0,88 −0,88 1,32 1,32 | 2,44 2,44 2,44 3,54 3,54 |
| 2 | −0,44 −0,24 −0,64 0,56 0,76 | −0,44 −0,44 −0,44 0,66 0,66 | 2,22 2,22 2,22 3,87 3,87 |
| 3 | −0,22 −0,02 −0,42 0,23 0,43 | −0,22 −0,22 −0,22 0,33 0,33 | 2,11 2,11 2,11 4,035 4,035 |

**Bunu AI'sız yazabilir misin?** Aynı veride η = 1 alsaydın, üçüncü adımdan sonra F hangi değerleri alırdı? Bu sonuç, η küçültüldüğünde gerekli adım sayısının neden arttığını açıklamanı istiyor.

### Örnek 4 (★★★): Eğitilmiş ağacı C'ye çevirmek ve bir girdinin yolunu izlemek

**Adım 1 — Anla.** Bölüm 59.15'te üretilen `agac_gomulu.c` dosyası üç öznitelikli, derinlik 3 bir ağacın C karşılığı. Soru iki parçalı: (a) iki girdi için ağaç hangi yolu izler ve hangi sınıfı döndürür? (b) Gereksiz dalları silmek makine kodunu değiştirir mi?

**Adım 2 — Örnekle.** Kaynak kodu tekrar okuyalım: kökteki koşul `x[0] <= 0.822449803f`. İki test girdisi:
- A = (0,9; 58,0; 300): titreşim 0,9, motor sıcaklığı 58,0, uçuş saati 300.
- B = (0,5; 70,0; 100): titreşim 0,5, motor sıcaklığı 70,0, uçuş saati 100.

Uçuş saati her iki girdide de bu ağaçta hiç kullanılmıyor; sadece titreşim ve motor sıcaklığı karar veriyor.

**Adım 3 — Kaba çöz.** Her girdi için karşılaştırmaları sırayla yap ve izle:

| Girdi | Adım | Düğüm | Karşılaştırma | Sonuç | Sonraki |
|---|---|---|---|---|---|
| A | 1 | kök | 0,9 ≤ 0,8224 ? | hayır | sağ |
| A | 2 | sağ | 0,9 ≤ 1,2162 ? | evet | sol |
| A | 3 | sağ-sol | 58,0 ≤ 43,5918 ? | hayır | return 1 |
| B | 1 | kök | 0,5 ≤ 0,8224 ? | evet | sol |
| B | 2 | sol | 70,0 ≤ 60,3237 ? | hayır | sağ |
| B | 3 | sol-sağ | 0,5 ≤ 0,4602 ? | hayır | return 0 |

A için tahmin 1, B için tahmin 0. Üç karşılaştırma, ağacın derinliği kadar; bu yüzden tahmin süresi girdinin değerinden bağımsız olarak sabittir.

**Adım 4 — Örüntü.** Ağacın yedi yaprağı var, ama sol-sol ve sol-sağ alt dallarının ikisi de 0 döndürüyor. Bu tür "iki çocuğu da aynı yaprak" durumları eğitimde nadir değildir, çünkü ağaç kendi içinde bir bölmenin işe yaramadığını bilmez. Sadeleştirme (`ayni_yapraklari_birlestir`) bu tür düğümleri yapraklara çevirir ve yaprak sayısını yediden dörde düşürür. Sadeleştirilmiş kodun kararları değişmez: test girdilerinde fark sıfırdır.

**Adım 5 — İyileştir.** Asıl soru: sadeleştirme makine kodunu küçültür mü? Sadeleştirilmiş sürüm, aynı ağaca `ayni_yapraklari_birlestir` uygulanarak üretildi. Derlenmiş iki sürümde karşılaştırma (`cmp`) komutlarını sayıp `.text` boyutunu ölçelim:

```term
$ arm-none-eabi-objdump -d agac_gomulu_ham.o | grep -c cmp
3
$ arm-none-eabi-objdump -d agac_gomulu_sade.o | grep -c cmp
3
$ arm-none-eabi-size agac_gomulu_ham.o agac_gomulu_sade.o
   text   data    bss    dec    hex filename
     76      0      0     76     4c agac_gomulu_ham.o
     76      0      0     76     4c agac_gomulu_sade.o
```

Sonuç çarpıcı: her iki sürümde de üç karşılaştırma ve üç dönüş var, boyut 76 bayt. Derleyici `-Os` ile zaten gereksiz dalı kaldırmış. Yani kaynak sadeleştirmesi okunabilirlik kazandırır, makine kodunu değiştirmez; bu ölçüm bunu doğruluyor. Bu sonuç, boyut tartışmasında ölçmeden konuşmanın tehlikesini de gösteriyor.

**Adım 6 — Doğrula.** Elle yaptığımız iki izi Python ağacının tahminiyle karşılaştıralım. Python `agac.tahmin` fonksiyonu A için 1, B için 0 veriyor (`uret_c.py` ile aynı eşikler). Ayrıca 20000 rastgele girdinin tamamında C ile Python aynı sınıfı verdi (Bölüm 59.15). Bu iki kontrol birlikte, ağacın C'ye doğru çevrildiğine dair kanıttır.

**Bunu AI'sız yazabilir misin?** Derinlik 3 ağacın C kodunu, yaprakları sayılarla değil, sınıf adlarıyla döndürecek şekilde değiştir. Sonra bir girdinin yolunu, yani hangi karşılaştırmalardan geçtiğini, sayı olarak yazdıran bir yardımcı fonksiyon yaz. Bu iki değişiklikte hangi satırların değişmesi gerekir, hangisi değişmez?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde karar ağacı, torbalama, rastgele orman ya da gradyan artırma için hazır bir kütüphane (sklearn, XGBoost, LightGBM) kullanma. Kendi kodunu yaz, sklearn'i yalnızca karşılaştırma için kullan. Bu bölümdeki `agac.py`, `orman.py` ve `gbm.py` dosyalarını bile referans alma; önce kendi sürümünü kur, sonra karşılaştır.
:::

### Proje 1 (★★): Mini bir ensemble kütüphanesi

**Amaç.** Dört bileşenden oluşan küçük bir topluluk kütüphanesi yazmak: (1) sınıflama ve regresyon karar ağacı (Gini ve MSE, sıralama ile hızlı bölme), (2) torbalama ve OOB hatası, (3) rastgele orman (öznitelik alt örneklemesi), (4) gradyan artırma (MSE ve log-kayıp, erken durdurma).

**Yapılacak.** Her bileşen için bir `fit` ve bir `predict` (ya da `predict_proba`) yöntemi olsun. Kütüphane, sklearn'in karşılık gelen sınıflarıyla aynı girdi biçimini kabul etsin. En az üç veri setinde (breast cancer, friedman1 ve kendi sentetik bir tablon) test et.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Ağacı yazmadan önce tek bir bölmeyi, yani en iyi eşiği bulan fonksiyonu yaz ve bunu naif O(n²) ile karşılaştır. Sonra özyinelemeyi ekle. Torbalama için bootstrap indekslerini bir kez üret ve OOB kümesini bunlardan çıkar. Gradyan artırmada yaprak değerlerini log-kayıpta Newton adımıyla (Σg/Σh) hesapla; bu, bu bölümdeki `yaprak_newton` fonksiyonunun fikridir.

**Başarı kriterleri.**
- Tek ağaç, aynı derinlikte sklearn `DecisionTreeClassifier` ile test doğruluğu farkı 0,02'den küçük; eşitlik bağlarını raporla.
- Rastgele orman, 5 tohumda sklearn RF ile test hatası farkı 0,01'den küçük.
- OOB hatası ile test hatası arasındaki fark 0,03'ten küçük (3 veri setinde).
- Gradyan artırma log-kayıp değeri sklearn'den en fazla yüzde 10 daha kötü.
- Her karşılaştırma için süre oranını ve tohum sapmasını yaz.

### Proje 2 (★★★): İHA bakım tablosunda uçtan uca tahmin

**Amaç.** Bu bölümün sentetik İHA bakım tablosunda (`uav.py`) tam bir veri hattı kurmak: veri hazırlığı, eğitim ve doğrulama ayrımı, model karşılaştırması, öznitelik önemi ve sonunda seçilen ağacın C'ye aktarılması.

**Yapılacak.** (1) Veriyi eğitim, doğrulama ve test olarak üçe ayır; test kümesini yalnızca en sonda kullan. (2) Lojistik regresyon, rastgele orman ve gradyan artırmayı (XGBoost ya da LightGBM) doğrulama üzerinde ayarla. (3) Test kümesinde AUC, doğruluk ve log-kayıp raporla; taban modeli ve gerçek olasılıkların AUC tavanını da ekle. (4) Permütasyon önemini test kümesinde hesapla; kimlik sütununu (seri numarası) bilerek dahil edip sonucu yorumla. (5) En iyi yorumlanabilir modelin bir sürümünü (derinlik 4 ağaç) C'ye çevir, derle ve Python ile karşılaştır.

**Önerilen yaklaşım (ipucu).** Kısmi bağımlılık grafiğini tek öznitelik için değil, yalnızca doğru bir sonuç vereceğini düşündüğün iki öznitelik için çiz. Gömülü ağacın eşiklerini float32'ye yuvarlamayı unutma; yoksa Python ve C sonuçları birkaç örnekte ayrılır. Sadeleştirmeden önce ve sonra yaprak sayısını ve derlenmiş boyutu ölç.

**Başarı kriterleri.**
- Seçilen modelin test AUC'si, gerçek olasılıklardan hesaplanan tavanın (0,78 civarı) 0,03 altında olsun.
- Doğrulama ve test sonuçları arasında 0,02'den büyük bir sapma olmasın; olursa nedenini açıkla.
- Gömülü ağacın 20000 rastgele girdide Python ile uyuşmazlığı sıfır olsun ve ASan/UBSan temiz geçsin.
- Derlenmiş `.text` boyutunu ve en kötü durum karşılaştırma sayısını raporla.
- Raporun bir paragrafı şunu açıklasın: test kümesine hiç bakmadan verdiğin kararlar nelerdi?

### Ek Alıştırmalar

1. ★ İkili bir düğümde pozitif oranı 0,3 ise Gini ve entropi (bit) değerlerini hesapla. Hangisi daha büyük ve neden?
2. ★ Bir düğümde 10 örnek var, 6'sı pozitif. Eşik adaylarının sayısı nedir ve neden n − 1'den fazla değildir?
3. ★★ Regresyon ağacında MSE azalması ile SSE azalması aynı sonucu neden verir? İspatını bir satırla yaz.
4. ★★ Derinliği sınırsız bir karar ağacının eğitim hatası neden sıfıra iner? Bu, hangi koşulda sıfır olmayabilir? (Mülakat)
5. ★★ Bootstrap'te bir örneğin seçilmeme olasılığının büyük n için e⁻¹'e yakınsamasını ispatla. (Mülakat)
6. ★★ Torbalamada B → ∞ olduğunda varyans neye yakınsar? ρ > 0 ise bu sınırın neden tek bir ağacın varyansından küçük olmadığını açıkla. (Mülakat)
7. ★★ Bir OOB tahmininin test kümesi olmadan neden güvenilir bir hata tahmini olabildiğini, ama yine de bağımsız test kümesinin yerini tutmadığını açıkla.
8. ★★★ İki öznitelik eşit kazanç veriyorsa, sonucun deterministik olması için bir tiebreak kuralı öner. Bu kuralın sklearn'in rastgele sırasından nasıl farklı olduğunu açıkla. (Mülakat)
9. ★★ Gradyan artırmada η = 1 ile η = 0,1 arasındaki farkı, Bölüm 50'deki gradyan inişi öğrenme oranıyla karşılaştırarak anlat.
10. ★★★ Log-kayıplı gradyan artırmada yaprak değerinin γ = Σg / Σh olduğunu, ikinci dereceden Taylor açılımından türet. (Mülakat)
11. ★★ Rastgele ormanda ağaç sayısı arttıkça neden aşırı uydurmaz? Bu özelliğin hangi koşulda bozulacağını düşün. (Mülakat)
12. ★★★ 128 KB flash'a sığacak bir ağaç topluluğunu bir İHA uçuş bilgisayarında kullanmak istiyorsun. Ağaç sayısı, derinlik ve eşik kodlama için bir bütçe hesabı yap; sonuçta hangi parametreleri seçersin ve neden? (Mülakat)

## Kod Okuma Egzersizi

Okuyacağın kaynak, bu bölümde bootstrap örneklemenin scikit-learn'deki gerçek karşılığıdır. Kaynak: scikit-learn 1.8.0, dosya `sklearn/ensemble/_forest.py` (yerel kurulumdaki birebir dosya). İki kesit aldık; bunlar kaynağın birebir kopyasıdır. Yalnızca iki satırı 70 karakter sınırına sığsın diye parantez içinde böldük; sözcükler ve işlem sırası değişmedi.

Birinci kesit, `_generate_sample_indices` fonksiyonudur (kaynak satır 124–133):

```python
def _generate_sample_indices(
    random_state, n_samples, n_samples_bootstrap
):
    """
    Private function used to _parallel_build_trees function."""

    random_instance = check_random_state(random_state)
    sample_indices = random_instance.randint(
        0, n_samples, n_samples_bootstrap, dtype=np.int32
    )

    return sample_indices
```

İkinci kesit, `_parallel_build_trees` fonksiyonunun bootstrap dalıdır (kaynak satır 168–179). Fonksiyonun geri kalanı, sınıf ağırlıklarını ele alan dallar ve ağacın `_fit` çağrısıdır; bunları kısalttık.

```python
    if bootstrap:
        n_samples = X.shape[0]
        if sample_weight is None:
            curr_sample_weight = np.ones(
                (n_samples,), dtype=np.float64
            )
        else:
            curr_sample_weight = sample_weight.copy()

        indices = _generate_sample_indices(
            tree.random_state, n_samples, n_samples_bootstrap
        )
        sample_counts = np.bincount(indices, minlength=n_samples)
        curr_sample_weight *= sample_counts
```

**Sorular — cevaplamadan geçme:**

1. `_generate_sample_indices` neden `np.random.randint` yerine `check_random_state(random_state)` ile bir rastgele örnekleyici alır? Bu, tohumun her ağaç için neden ayrı olmasını sağlıyor?
2. Örnek indeksleri `np.bincount(indices, minlength=n_samples)` ile sayıya çevrilip `curr_sample_weight` ile çarpılıyor. Bu, bootstrap'i ağırlıklı bir eğitime dönüştürmenin yolu. Bu sayede bir örnek üç kez seçildiyse, ağaç ona neden üç kat ağırlık verir?
3. Kodda bootstrap örneklemesi `n_samples` kadar çekiliyor, ama bu bölümdeki `orman.py` de aynı şekilde `rng.integers(0, n, n)` kullanıyor. İki kodun ortak noktası ve farkı nedir?
4. `n_samples_bootstrap` değişkeni neden çoğu zaman `n_samples` ile aynı; `max_samples` parametresi bu değeri hangi durumda değiştirir?
5. Bu kodda OOB örnekleri nerede hesaplanıyor? (İpucu: `_generate_unsampled_indices` fonksiyonu; kesitin dışında.) Bu hesap, kendi `oob_hatasi` fonksiyonumuzla aynı mantıkta mı?
6. Kesitin çevresindeki kaynak paralel eğitim, sınıf ağırlıkları, eksik değer ve hata ayıklama gibi katmanlar içeriyor. Bunlardan hangileri gerçek bir kütüphanenin gereksinimi, hangisi olmadan modelin doğru çalışmazdı, hangisi bu bölümdeki kendi kodumuzda eksik? Kendi ağacına hangi ayrıntıyı eklemen gerekirdi?

## Bölüm Özeti

- Karar ağacı, veriyi eksene paralel bölmelerle parçalara ayırır; her düğüm bir soru sorar ve yaprak bir tahmin döndürür.
- En iyi bölmeyi, Gini ya da entropi (sınıflama) ve SSE (regresyon) azalmasıyla seçeriz. Sıralama ve kümülatif sayımla bu arama O(n log n) olur; naif yöntem O(n²)'dir.
- Tek bir ağaç yüksek varyanslıdır: veri biraz değiştiğinde yapısı değişebilir. Ağaç derinleştikçe eğitim hatası sıfıra iner; budama (cost-complexity, ccp_alpha) α'yı çapraz doğrulamayla seçerek bunu sınırlar.
- Topluluklar ağaçların hatalarının ortalamasını alarak varyansı düşürür. Varyans formülü ρσ² + (1 − ρ)σ²/B, ağaçlar arası korelasyonun kazancı nasıl sınırladığını gösterir.
- Torbalama bootstrap ile ağaçları farklılaştırır ve OOB hatasını bedava verir. Rastgele orman her bölmede öznitelik alt örneklemesiyle ρ'yu düşürür.
- Gradyan artırma, fonksiyon uzayında gradyan inişidir: her ağaç artığa uyar ve η ile katkısı küçültülür. Erken durdurma T'yi doğrulamayla seçer.
- Modern kütüphaneler (XGBoost, LightGBM) histogram bölme ve ikinci dereceden yaklaşım gibi hilelerle hızlanır; sayılarını kendi verimizle ölçtük, lojistik regresyon tabloda tavana yaklaştı.
- Önem ölçütleri birbirinden farklıdır: safsızlık önemi çok değerli öznitelikleri kayırır, permütasyon önemi test kümesinde ölçer. Derinlik 3 bir ağaç, bir mikrodenetleyicide 76 bayt kodla çalışabilir.

**Sonraki bölümde:** Bölüm 60'ta SVM ve kernel yöntemlerini göreceğiz. Bu bölümde karar sınırını eksenlere paralel basamaklarla çizdik; orada aynı problemi tamamen farklı bir geometriyle, bir hiper düzlemin marj maksimizasyonuyla ele alacağız. Kernel fikri, özniteliklerin doğrusal olmayan dönüşümlerini örtük olarak nasıl kullandığını gösterecek ve bu, bu bölümdeki etkileşim yakalama sorusuyla doğrudan ilişkili olacak.

::: mulakat
1. Gini ve entropi neden çoğu zaman aynı bölmeyi seçer? İki ölçütün eğrilerinin hangi bölgesinde farklılaşırlar?
2. Karar ağacında budama olmadan aşırı uydurmayı önlemek için hangi üç parametreyi seçersin ve her biri neyi kontrol eder?
3. Torbalama ve rastgele orman arasındaki fark nedir? Öznitelik alt örneklemesi olmasaydı RF ne zaman torbalamayla aynı sonucu verirdi?
4. Gradyan artırma neden sapmayı düşürürken torbalama varyansı düşürür? Bu ayrımı bir sayı ile göster.
5. XGBoost ile sklearn'in GradientBoosting'i arasındaki temel fark nedir? Büyük veride hangisini ve neden seçersin?
6. Permütasyon önemi test kümesinde hesaplanırken, neden eğitim kümesinde hesaplanmaz? Kimlik sütununun iki ölçütte farklı davranmasını açıkla.
7. Bir ağacı C if-else koduna çevirdiğinde doğruluk garantisi neden kendiliğinden gelmez? Hangi iki kontrolü yaparsın?
:::
