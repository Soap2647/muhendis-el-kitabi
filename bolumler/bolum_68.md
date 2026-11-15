%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 68
%% baslik: Dizi Modelleri & Zaman Serisi

## Giriş: Zamanın sırası bilgidir

Bir İHA'nın uçuş bilgisayarı saniyede on kez irtifa, hız, yuvarlanma açısı ve motor akımını ölçer. Bu sayıların her biri tek başına çok az şey söyler. Anlamı, önündeki birkaç saniyeyle birlikte okunduğunda ortaya çıkar. Motor akımı bir anda yükselirse bu bir rüzgâr gustu mu, yoksa bir rulmanın bozulmaya başladığının işareti mi? Cevap, akımın son birkaç saniyedeki davranışına ve diğer kanallara bakmayı gerektirir. Bu tür veriye zaman serisi denir ve sıranın önemli olduğu her veri bu sınıfa girer.

Bölüm 66'da görüntüdeki yerel ve uzamsal yapıyı konvolüsyonla yakaladık. Bu bölümde aynı fikri zaman boyutu için kuruyoruz. Ya bir gizli durumu adım adım taşıyan RNN, LSTM ve GRU ile, ya da nedensel genişletilmiş konvolüsyonla (TCN). Bölüm 62'de gördüğümüz HMM ve Kalman filtresi de zamanı ele alıyordu, ama onlarda sistemin davranışı elle yazılmış bir modelle tanımlanıyordu. Burada model yapısını veriden öğreniyoruz. Esneklik kazanıyoruz, ama iki tehlike de geliyor: zamanın sırasını bozan bir değerlendirme (sızıntı) ve baz modelden daha kötü olduğu hâlde karmaşık bir modeli seçme eğilimi.

Savunma sanayiinde bu konu her yerde karşımıza çıkar. Bir İHA telemetrisinde kısa vadeli tahmin, beklenen değerden sapan örüntüyü (sensör arızası, rulman bozulması, bataryanın aşırı ısınması) erken yakalamanın temelidir. Bölüm 61'deki anomali tespiti burada zamansal bir bağlam kazanır. Bölüm 35'te telemetrinin zaman serisi deposunda nasıl saklandığını, Bölüm 41'de bu veriyi yer istasyonuna nasıl taşıdığımızı konuşmuştuk. Bölüm 35'in sonunda söz verdiğimiz gibi şimdi bu veri üzerinde modeller kuruyoruz. Bölüm 33'te tasarladığımız EV Dashboard ölçüm tablosu da aynı mantığa dayanır: her ölçüm bir zaman damgasıyla sıralanmış bir dizinin parçasıdır.

Bu bölümün dört özelliği var. Birincisi, her derin modeli baz modellerle (naif tahmin, mevsimsel naif, hareketli ortalama ve otoregresif AR) yan yana koyuyoruz. Bu baz modelleri geçemeyen bir derin model, yalnızca daha pahalı bir modeldir. İkincisi, bütün deneyler CPU'da yapıldı. Bu boyuttaki modeller ve veriler için CPU yeterlidir; GPU'nun hızı ve bellek sınırları üzerine Bölüm 65'te konuştuk. Üçüncüsü, veri internetten indirilmedi. İki sentetik üretici kullanıyoruz: İHA telemetrisi ve batarya hücresi. Dördüncüsü, her sonuç üç tohum üzerinden ortalama ± sapma olarak verilir. Tek bir koşu, bu bölümde bir iddia olarak sunulmaz.

::: not
Bir derin modelin başarısını tek başına değerlendirme. Zaman serisinde asıl soru "model ne kadar iyi?" değil, "model basit bir kuraldan ne kadar iyi?" sorusudur. Baz modeller bu kuralı verir. Bunu geçemiyorsan sorun modelin kapasitesinde değil, veri ya da değerlendirme düzeninde olabilir.
:::

## 68.1 Dizi verisi türleri ve görevler

Dizi, sırası anlamlı olan veridir. Üç ana biçimi vardır. Zaman serisi, eşit ya da yaklaşık eşit aralıklarla alınmış sayısal ölçümlerdir: İHA telemetrisi, hava sıcaklığı, bir hisse fiyatı. Metin, kelime ya da karakter dizisidir; sırası sözdizimini ve anlamı taşır (Bölüm 70'te ele alınır). Olay dizisi, düzensiz zaman damgalı olayların listesidir: bir sisteme giriş, bir alarm, bir komut. Bu bölümde ağırlıklı olarak sayısal zaman serisini işleyeceğiz. Olay dizileri ve metin, aynı tekrarlayan modellere farklı bir girdi kodlamasıyla bağlanır.

Bir dizi modeli, bir dizi girdiyi bir çıktıya ya da bir çıktı dizisine çevirir. Bu çeviri farklı görevlerde farklı biçim alır. Aşağıdaki tablo, İHA telemetrisi üzerinden dört temel görevi gösteriyor.

| Görev | Girdi | Çıktı | İHA örneği |
|---|---|---|---|
| Tahmin (forecasting) | geçmiş pencere | gelecekteki değer(ler) | bir sonraki akım değeri |
| Dizi sınıflandırma | bir pencere ya da tüm dizi | sınıf etiketi | batarya sağlıklı mı, bozulmuş mu |
| Dizi-dizi | bir dizi | bir dizi (farklı uzunlukta olabilir) | son 6 saniyeden sonraki 1 saniye |
| Anomali tespiti | pencere ya da gözlenen değer | normal ya da olağandışı | rulman bozulmasının başlangıcı |

Tabloda dördüncü sütuna dikkat et. Aynı zaman serisi, görevi değiştirdiğinde farklı bir kayıp fonksiyonu ve farklı bir değerlendirme ölçütü ister. Tahminde hatayı akımın birimi (amper) cinsinden ölçersin. Sınıflandırmada doğruluk ya da duyarlılık, anomali tespitinde ise yanlış alarm oranı önemlidir. Bu ayrım, bölümün ilerleyen kısımlarında her deneyde ayrı ayrı yapılacaktır.

## 68.2 Zaman serisi temelleri: trend, mevsimsellik, durağanlık

Bir zaman serisini anlamanın ilk adımı onu bileşenlerine ayırmaktır. Klasik model şöyledir: x_t = trend_t + mevsim_t + gürültü_t. Trend, uzun vadeli yönü verir; irtifanın yavaşça artması gibi. Mevsimsellik, sabit bir periyotla tekrarlayan örüntüdür; bir devriye turunun her 60 saniyede tekrarlaması gibi. Gürültü, geriye kalan rastgele bileşendir. Gerçek sensör verisinde bu ayrımı kesin yapamazsın. Ama modelin neyi öğrendiğini anlamak için bileşenleri bilerek ürettiğin bir seri üzerinde deney yapmak çok öğreticidir.

Bir seri durağan (stationary) ise ortalaması ve varyansı zamanla değişmez, iki zaman noktası arasındaki ilişki yalnızca aradaki gecikmeye bağlıdır. Trend varsa durağanlık bozulur. Bu durumda model, eğitim aralığının istatistiğini öğrenir ve o aralığın dışında kötü tahmin yapar. Resmi durağanlık testleri (genişletilmiş Dickey-Fuller gibi) bu bölümün kapsamı dışında kalır; burada yalnızca bir sezgi kullanıyoruz: serinin ilk yarısının ortalaması ve sapması ile ikinci yarısının ortalaması ve sapması karşılaştırılır. Trend içeren seride ortalama yarıdan yarıya belirgin biçimde değişir. Saf AR(1) serisinde değişmez. Aşağıdaki program bu sezgiyi sayılarla gösterir.

Zaman serisinin geçmişle ilişkisini ölçen araç otokorelasyon fonksiyonudur (ACF). Gecikme k için örneklem ACF şöyle tanımlanır: r_k = Σ (x_t − m)(x_{t+k} − m) / Σ (x_t − m)². Burada m örneklem ortalamasıdır, toplamlar uygun aralıkta alınır. r_0 her zaman 1'dir. Beyaz gürültü için r_k, n büyük olduğunda sıfır civarında dağılır ve yaklaşık %95 bant ±1,96/√n ile verilir. ACF'nin bu banddan çıktığı gecikmeler, serinin ne kadar geçmişe bağlı olduğunu söyler. Bölüm 52'deki sinyal işleme dilinde, otokorelasyonun Fourier dönüşümü güç spektrumudur (Wiener-Khinchin ilişkisi, genel bilgi). Burada ACF'yi bir sezgi aracı olarak kullanıyoruz: AR(p) modelinde p'yi ACF'ye bakarak kabaca tahmin edebilirsin, ama kesin değerini doğrulama kümesinde seçeceğiz.

Aşağıdaki program 600 adımlık bir seri üretir. Seri bir trend (0,02 t), 50 adımlık bir sinüs bileşeni ve AR(1) gürültüsünden (katsayı 0,6) oluşur. Ayrıca aynı uzunlukta bir beyaz gürültü serisinin ACF'sini karşılaştırmak için hesaplar. Tohum 7 sabittir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.1: zaman serisi bileşenleri, durağanlık sezgisi, ACF."""
import numpy as np
from ortak import yaz_csv

rng = np.random.default_rng(7)
n = 600
t = np.arange(n)
trend = 0.02 * t
mevsim = 3.0 * np.sin(2 * np.pi * t / 50)
gurultu = np.zeros(n)
e = rng.normal(0, 1.0, n)
for i in range(1, n):                      # AR(1), phi = 0,6
    gurultu[i] = 0.6 * gurultu[i - 1] + e[i]
seri = trend + mevsim + gurultu


def acf(x, K):
    """Örneklem ACF: r_k = sum (x_t-m)(x_{t+k}-m) / sum (x_t-m)^2."""
    m = x.mean()
    d = x - m
    payda = np.sum(d * d)
    return np.array([np.sum(d[:len(x) - k] * d[k:]) / payda
                     for k in range(K + 1)])
```

Programın devamı aşağıdadır.

```python
r = acf(seri, 60)
beyaz = acf(e, 60)
band = 1.96 / np.sqrt(n)
print("ACF (seri), gecikme 1,5,10,25,50:")
print(" ", [round(float(r[k]), 3) for k in (1, 5, 10, 25, 50)])
print("ACF (beyaz gürültü), gecikme 1,5,10:")
print(" ", [round(float(beyaz[k]), 3) for k in (1, 5, 10)])
print("Yaklaşık %%95 bant: +-%.3f" % band)

# Durağanlık sezgisi: iki yarının ortalaması ve sapması
for ad, x in [("trend", seri),
              ("AR(1)", gurultu)]:
    a, b = x[:n // 2], x[n // 2:]
    print("%-8s ilk: ort=%6.2f sd=%5.2f | ikinci: ort=%6.2f sd=%5.2f"
          % (ad, a.mean(), a.std(), b.mean(), b.std()))

yaz_csv("b68_bilesen.csv",
         ["t", "seri", "trend", "mevsim", "gurultu"],
         [(i, round(seri[i], 4), round(trend[i], 4),
           round(mevsim[i], 4), round(gurultu[i], 4))
          for i in range(n)])
yaz_csv("b68_acf.csv", ["gecikme", "acf_seri", "acf_beyaz", "bant"],
        [(k, round(r[k], 4), round(beyaz[k], 4), round(band, 4))
         for k in range(61)])
```

Programın çıktısı şöyledir. Serinin ACF'si 1 ile 25 gecikme arasında güçlü ve azalan bir yapı gösterir; 50 gecikmede tekrar yükselir çünkü sinüs periyodu 50'dir. Beyaz gürültünün ACF'si ise bant içinde kalır.

```term
$ python t00_bilesenler.py
ACF (seri), gecikme 1,5,10,25,50:
  [0.963, 0.864, 0.727, 0.358, 0.693]
ACF (beyaz gürültü), gecikme 1,5,10:
  [-0.006, -0.019, 0.023]
Yaklaşık %95 bant: +-0.080
trend    ilk: ort=  2.66 sd= 2.77 | ikinci: ort=  8.65 sd= 2.73
AR(1)    ilk: ort= -0.33 sd= 1.16 | ikinci: ort= -0.34 sd= 1.11
```

Trend içeren seride iki yarının ortalaması 2,66 ile 8,65 arasında değişiyor; saf AR(1) serisinde ise −0,33 ile −0,34 arasında kalıyor. Sapmalar iki durumda da benzer. Bu, trendin ortalamayı kaydırdığını, gürültünün ise değişmediğini gösterir. Şekil 68.1 sol panelde trendi ve mevsimselliği, sağ panelde ACF'yi çizer.

![Şekil 68.1: Sol: trend ve trend+mevsim bileşenleri. Sağ: trend+mevsimsel serinin ACF'si (koyu) ve beyaz gürültünün ACF'si; kesikli çizgi %95 bandı.](gorseller/b68_bilesen_acf.png)

ACF'nin 50 gecikmedeki yükselişi önemli bir ders içeriyor. Mevsimsellik, tam o periyotta bir örüntü bırakır. Bir modele "ne kadar geçmişe bakmalı?" diye sorduğunda cevap bu periyodu kapsamalıdır. Bölüm 68.4'te göreceğimiz mevsimsel naif tahmin de tam bu bilgiyi kullanır; İHA telemetri verisinde ise bu periyodun bir devriye turuna karşılık geldiğini göreceğiz.

## 68.3 Kayan pencere, zamana göre bölme ve sızıntı

Zaman serisini denetimli öğrenme problemine çevirmenin en yaygın yolu kayan pencere (sliding window) yöntemidir. Pencere uzunluğu W olsun. i. örnek, x_i, x_{i+1}, ..., x_{i+W-1} değerlerinden oluşan girdiye ve x_{i+W} hedefine sahip olur. n uzunluğunda bir dizi, n − W örnek verir. Bu dönüşümle Bölüm 54'teki (X, y) biçimi geri gelir. Tek fark, X'in satırlarının birbirine sıkı biçimde bağlı olmasıdır: iki komşu pencere W − 1 değeri paylaşır. Bu ortak yapı, aşağıda göreceğimiz sızıntının kaynağıdır.

Dönüşümü doğru yapmak için üç kurala uymak gerekir. Birincisi, test kümesi eğitimden sonra gelmelidir; yani zamana göre bölme yaparsın ve rastgele bölmeyi kullanmazsın. İkincisi, ölçekleme (ortalama ve sapma) yalnızca eğitim aralığından öğrenilir; test verisinin istatistiği eğitime sızmaz. Üçüncüsü, bir pencerenin girdisindeki her değer hedeften önce gelmelidir. Bu üçüncü kural, Bölüm 56'da gördüğün shift(1) düzeninin pencereli hâlidir: hedefin kendisi ya da onun sonrasındaki bir değer girdiye girmemelidir.

Rastgele bölmenin neden yanlış olduğunu bir örnekle görelim. Bir test penceresinin zamanda hemen yanında, yani bir adım önce ya da sonra, eğitim penceresi bulunur. İki pencere W − 1 değer paylaşır, hedefleri de birbirine yakındır. Rastgele bölme bu komşuluğu test kümesine taşır ve model, eğitimde gördüğü "neredeyse aynı pencereyi" hatırlayarak iyi görünür. Bu bir öğrenme değil, bir kopya kontrolü başarısızlığıdır. Zamana göre bölmede ise test dönemi eğitimde hiç görülmemiş bir zaman aralığıdır; model kopya bulamaz ve genelleme gücü ölçülür.

Bu bölümün bütün deneylerinde ortak araçlar kullanıyoruz. Aşağıdaki ortak.py dosyasının ilk kısmı veriyi üretir, pencereleri oluşturur, zamana göre üçe böler, ölçeklemeyi yalnızca eğitimden yapar, hata ölçütlerini tanımlar ve baz modelleri içerir. Sinir ağı sınıfları ve eğitim döngüsü, ilk kez kullanıldıkları bölümde (68.9) ayrıca açıklanacaktır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68 ortak araçları: sentetik telemetri, pencereleme, baz
modeller ve küçük bir eğitim döngüsü. Tüm işler CPU'da yapılır."""
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(4)
VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
DT = 0.1        # İHA telemetrisi 10 Hz
PERIYOT = 600   # bir devriye turu 60 s = 600 örnek
HEDEF = 3       # tahmin edilen kanal: motor akımı


def iha_telemetri(n=24000, seed=11):
    """Sentetik İHA telemetrisi, anomalisiz.
    Kanallar: irtifa (m), hız (m/s), yuvarlanma (derece), akım (A)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    faz = 2 * np.pi * t / PERIYOT
    e = rng.normal(0.0, 1.0, n)
    ruzgar = np.zeros(n)
    for i in range(1, n):                 # AR(1) türbülans
        ruzgar[i] = 0.97 * ruzgar[i - 1] + 0.25 * e[i]
    irtifa = 100 + 0.0015 * t + 6 * np.sin(faz) + 0.6 * ruzgar
    hiz = 15 + 2.5 * np.sin(faz + 0.4) + 0.4 * rng.normal(size=n)
    yuv = 22 * np.sin(faz) + 1.5 * ruzgar + 0.5 * rng.normal(size=n)
    akim = (6 + 0.35 * hiz + 0.05 * np.abs(yuv)
            + 0.15 * rng.normal(size=n))
    return np.stack([irtifa, hiz, yuv, akim], axis=1)
```

Programın devamı aşağıdadır.

```python

def ariza_ekle(seri, bas, son, seed=5):
    """[bas, son) aralığına arıza enjekte eder, etiket döner.
    (1) 5 tekil akım sıçraması (+3 A).
    (2) 400 örnek boyunca doğrusal artan kayma (en fazla +1,5 A),
        ardından 300 örnek sabit kalır."""
    rng = np.random.default_rng(seed)
    x = seri.copy()
    etiket = np.zeros(len(x), dtype=int)
    konum = rng.choice(np.arange(bas, son - 10), size=5,
                       replace=False)
    for k in konum:
        x[k, HEDEF] += 3.0
        etiket[k] = 1
    d0 = bas + (son - bas) // 2
    seg = np.concatenate([np.linspace(0.0, 1.5, 400),
                          np.full(300, 1.5)])
    m = min(len(seg), len(x) - d0)
    x[d0:d0 + m, HEDEF] += seg[:m]
    etiket[d0:d0 + m] = 1
    return x, etiket


def olcek(Z, ntr):
    """Ortalama ve sapmayı YALNIZCA eğitim satırlarından öğrenir."""
    mu = Z[:ntr].mean(axis=0)
    sd = Z[:ntr].std(axis=0) + 1e-8
    return (Z - mu) / sd, mu, sd
```

Programın devamı aşağıdadır.

```python

def pencere(Z, W, H=1):
    """X[i] = Z[i:i+W] (tüm kanallar); Y[i] = hedef kanalın
    Z[i+W : i+W+H] değerleri."""
    m = len(Z) - W - H + 1
    X = Z[np.arange(W)[None, :] + np.arange(m)[:, None]]
    Y = Z[np.arange(H)[None, :] + np.arange(m)[:, None] + W, HEDEF]
    return X.astype(np.float32), Y.astype(np.float32)


def veri_bol(Z, W, H, ntr, nva):
    """Pencereleri HEDEFİN konumuna göre üçe böler: eğitim, doğrulama,
    test. Girdi pencereleri bir önceki kümeden taşabilir; bu sızıntı
    değildir, çünkü yalnızca geçmiş değerler kullanılır."""
    X, Y = pencere(Z, W, H)
    hb = np.arange(len(X)) + W
    tr = hb < ntr
    va = (hb >= ntr) & (hb < nva)
    te = hb >= nva
    return (X[tr], Y[tr]), (X[va], Y[va]), (X[te], Y[te])


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))
```

Programın devamı aşağıdadır.

```python
def rmse(a, b):
    d = np.asarray(a) - np.asarray(b)
    return float(np.sqrt(np.mean(d ** 2)))


# ---------- baz modeller (ham hedef dizisi s) ----------
def naif_tahmin(s, idx):
    return s[idx - 1]                        # son değer


def mevsimsel_naif(s, idx, P=PERIYOT):
    return s[idx - P]                        # bir periyot önce


def hareketli_ort(s, idx, k=10):
    return np.array([s[t - k:t].mean() for t in idx])


def ar_egit(s, ntr, p):
    """AR(p): s_t = c + a1 s_{t-1} + ... + ap s_{t-p}.
    Katsayılar en küçük kareler ile bulunur."""
    rows = np.arange(p, ntr)
    A = np.column_stack([np.ones(len(rows))]
                        + [s[rows - j] for j in range(1, p + 1)])
    kat, *_ = np.linalg.lstsq(A, s[rows], rcond=None)
    return kat
```

Programın devamı aşağıdadır.

```python

def ar_1adim(s, kat, idx):
    p = len(kat) - 1
    A = np.column_stack([np.ones(len(idx))]
                        + [s[idx - j] for j in range(1, p + 1)])
    return A @ kat


def ar_sec(s, ntr, nva, dereceler=(1, 2, 5, 10, 20, 40)):
    """Derece seçimi doğrulama MAE'siyle yapılır; test'e bakılmaz."""
    idx_va = np.arange(ntr, nva)
    en = None
    for p in dereceler:
        kat = ar_egit(s, ntr, p)
        h = mae(s[idx_va], ar_1adim(s, kat, idx_va))
        if en is None or h < en[0]:
            en = (h, p, kat)
    return en[1], en[2]
```

Şimdi bu sızıntının sayısal boyutunu ölçelim. Aşağıdaki t01 programı İHA telemetrisinin akım kanalını, son on örnekteki dört kanalın değerleriyle (40 özellik) bir adım ileri tahmin eder. İki model kullanır: beş komşulu en yakın komşu regresyonu (kNN) ve doğrusal regresyon. Her biri için iki bölme yapar: zamana göre (ilk %60 eğitim, son %20 test) ve rastgele (%20 test). Ayrıca iki yanlış uygulama ekler. Birincisi, ölçeklemeyi tüm veriden yapar. İkincisi, hedef zamanın merkezli kayan ortalamasını (hedef ve komşu iki değerin ortalaması) bir özellik olarak ekler; bu özellik gelecekteki bir değeri içerir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.4: rastgele ve zamana göre bölme, sızıntı ölçümü."""
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from ortak import iha_telemetri, pencere, mae, rmse, yaz_csv, HEDEF

n, W = 24000, 10
Z = iha_telemetri(n, seed=11)
X, Y = pencere(Z, W, 1)
m = len(X)
y = Y[:, 0]
F = X.reshape(m, -1)
hb = np.arange(m) + W                     # hedefin zaman indeksi
ntr, nva = int(0.6 * n), int(0.8 * n)
zt_tr, zt_te = hb < ntr, hb >= nva        # zamana göre bölme

rng = np.random.default_rng(3)
perm = rng.permutation(m)
rt_te = np.zeros(m, bool)
rt_te[perm[:int(0.2 * m)]] = True         # rastgele: %20 test
rt_tr = ~rt_te


def olcekle(Fx, tr, mu=None, sd=None):
    if mu is None:
        mu, sd = Fx[tr].mean(0), Fx[tr].std(0) + 1e-8
    return (Fx - mu) / sd, mu, sd
```

Programın devamı aşağıdadır.

```python

def deney(tr, te, model, Fx):
    A, _, _ = olcekle(Fx, tr)
    model.fit(A[tr], y[tr])
    p = model.predict(A[te])
    return mae(y[te], p), rmse(y[te], p)


sonuc = []
for ad, mdl in [("kNN (k=5)", lambda: KNeighborsRegressor(5)),
                ("Doğrusal", lambda: LinearRegression())]:
    for bolme, tr, te in [("zaman", zt_tr, zt_te),
                          ("rastgele", rt_tr, rt_te)]:
        a, r = deney(tr, te, mdl(), F)
        sonuc.append((ad, bolme, a, r))

# Geleceği gören özellik: merkezli pencere ortalaması
# (merkezli kayan ortalama: rolling(center=True) hatası)
g = Z[:, HEDEF]
gelecek = (g[hb - 1] + g[hb] + g[np.minimum(hb + 1, n - 1)]) / 3
F2 = np.column_stack([F, gelecek])
a, r = deney(zt_tr, zt_te, LinearRegression(), F2)
sonuc.append(("Doğrusal+gelecek", "zaman", a, r))

# Ölçekleme sızıntısı: ortalama ve sapma tüm veriden
A_all, _, _ = olcekle(F, np.ones(m, bool))
lr = LinearRegression().fit(A_all[zt_tr], y[zt_tr])
p = lr.predict(A_all[zt_te])
sonuc.append(("Doğrusal (tüm veriyle ölçek)", "zaman",
              mae(y[zt_te], p), rmse(y[zt_te], p)))
```

Programın devamı aşağıdadır.

```python
print("%-28s %-9s %8s %8s" % ("Yöntem", "bölme", "MAE", "RMSE"))
for ad, b, a, r in sonuc:
    print("%-28s %-9s %8.4f %8.4f" % (ad, b, a, r))
print("test boyutu zaman=%d rastgele=%d" % (zt_te.sum(), rt_te.sum()))

yaz_csv("b68_bolme_sonuc.csv", ["yontem", "bolme", "mae", "rmse"],
        [(a, b, round(c, 5), round(d, 5)) for a, b, c, d in sonuc])
yaz_csv("b68_bolme_maske.csv", ["hb", "rastgele_test", "zaman_test"],
        [(i, int(rt_te[i]), int(zt_te[i]))
         for i in range(14000, 20000)])
```

```term
$ python t01_bolme.py
Yöntem                       bölme          MAE     RMSE
kNN (k=5)                    zaman       0.2344   0.2940
kNN (k=5)                    rastgele    0.1942   0.2424
Doğrusal                     zaman       0.1793   0.2258
Doğrusal                     rastgele    0.1835   0.2289
Doğrusal+gelecek             zaman       0.1171   0.1469
Doğrusal (tüm veriyle ölçek) zaman       0.1794   0.2259
test boyutu zaman=4800 rastgele=4798
```

Program bu sonucu üretir. kNN için rastgele bölme 0,1942 verirken zamana göre bölme 0,2344 verir. Yani rastgele bölme modeli daha iyi gösterir, ve bu yanıltıcıdır. Doğrusal modelde fark tersine ve küçüktür (0,1835 ile 0,1793); doğrusal model ezberleyemediği için sızıntı zayıf kalır. Tüm veriyle ölçeklemenin etkisi bu veride 0,0001 kadardır, yani ihmal edilebilir; ama kural yine de yanlıştır, çünkü bir başka seride ya da bir trend içeren seride bu fark büyüyebilir. Geleceği gören özellik ise hata değerini 0,1171'e düşürür. Bu bir model başarısı değil, değerlendirme hatasıdır: gerçek zamanlı çalışan bir sistem o özelliği hiçbir zaman üretemez.

![Şekil 68.2: Üst: eğitim sonrası test noktalarının zaman ekseni üzerindeki dağılımı; rastgele bölmenin testi tüm aralığa serpiştirilmiş, zamana göre bölmenin testi son %20'dedir. Alt: aynı kNN ve doğrusal modelin test MAE'si iki bölmede.](gorseller/b68_bolme_sizinti.png)

Şekil 68.2 bu farkı gösterir. Üst panelde rastgele test noktaları eğitim aralığının içinde de yer alıyor; her test noktasının yanında bir eğitim noktası var. Alt panelde kNN'in hatası rastgele bölmede düşük, zamana göre bölmede yüksektir. Bölüm 68.14'te göreceğimiz anomali tespiti ve Bölüm 68.13'teki çok adımlı tahmin de aynı disiplini kullanır.

## 68.4 Baz modeller: derin modeli neyle karşılaştıracağız

Derin bir modelin başarısını ölçmek için önce dört basit modeli çalıştırmalıyız. Naif tahmin, bir sonraki değeri şimdiki değere eşitler. Durağan olmayan birçok seride bile şaşırtıcı derecede güçlüdür, çünkü her adımda yalnızca bir değişimi hata olarak öder. Mevsimsel naif tahmin, bir sonraki değeri bir periyot öncekine eşitler; bu veride periyot 600 örnektir. Hareketli ortalama, son on değerin ortalamasıdır; gürültüyü yumuşatır ama değişimleri geriden izler. AR(p) modeli ise şu biçimdedir: s_t = c + a_1 s_{t−1} + ... + a_p s_{t−p}. Katsayılar en küçük kareler yöntemiyle bulunur; bu, Bölüm 58'deki doğrusal regresyonun özelliklerinin geçmiş değerler olduğu durumdur. Derece p, doğrulama kümesinde seçilir; test kümesine dokunulmaz.

Bu dört model iyi bir çıta oluşturur. Derin bir modelin bu çıtayı geçmesi, yalnızca doğrusal bir AR modelini geçmek anlamına gelir. Aşağıdaki programda üç tohum için (11, 12, 13) üç farklı telemetri gerçekleşmesi üretilir ve son %20 üzerinde MAE ile RMSE hesaplanır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.4: baz modeller (naif, mevsimsel naif, hareketli
ortalama, AR(p)). Tohum 11, 12, 13: her biri ayrı bir telemetri
gerçekleşmesi."""
import numpy as np
from ortak import (iha_telemetri, HEDEF, PERIYOT, mae, rmse,
                   naif_tahmin, mevsimsel_naif, hareketli_ort,
                   ar_sec, ar_egit, ar_1adim, yaz_csv)

n = 24000
ntr, nva = int(0.6 * n), int(0.8 * n)
satir, ozet = [], {}
for seed in (11, 12, 13):
    Z = iha_telemetri(n, seed=seed)
    s = Z[:, HEDEF]
    te = np.arange(nva, n)
    p, kat = ar_sec(s, ntr, nva)
    tahminler = {
        "naif": naif_tahmin(s, te),
        "mevsimsel naif": mevsimsel_naif(s, te),
        "hareketli ort. (10)": hareketli_ort(s, te, 10),
        "AR(%d)" % p: ar_1adim(s, kat, te),
    }
    for ad, pr in tahminler.items():
        a, r = mae(s[te], pr), rmse(s[te], pr)
        satir.append((seed, ad, round(a, 5), round(r, 5)))
        ozet.setdefault(ad, []).append((a, r))
```

Programın devamı aşağıdadır.

```python
print("Test (son %%20), H=1, hedef: akım (A). Periyot=%d" % PERIYOT)
print("%-22s %16s %16s" % ("Model", "MAE ort+-sd", "RMSE ort+-sd"))
for ad, v in ozet.items():
    a = np.array([x[0] for x in v])
    r = np.array([x[1] for x in v])
    print("%-22s %8.4f+-%.4f %8.4f+-%.4f"
          % (ad, a.mean(), a.std(ddof=1), r.mean(), r.std(ddof=1)))
print("AR derece seçimi (tohum 11, doğrulama MAE):")
Z = iha_telemetri(n, seed=11)
for q in (1, 2, 5, 10, 20, 40):
    k2 = ar_egit(Z[:, HEDEF], ntr, q)
    va = np.arange(ntr, nva)
    pr = ar_1adim(Z[:, HEDEF], k2, va)
    print("  p=%2d  MAE=%.4f" % (q, mae(Z[va, HEDEF], pr)))
yaz_csv("b68_baz.csv", ["tohum", "model", "mae", "rmse"], satir)
```

Çıktı şöyledir. Tablo, son yirmi yüzde test kümesinde, üç tohumun ortalamasını ve sapmasını verir. AR derece taraması, doğrulama MAE'sinin p büyüdükçe azaldığını, p = 20 ile p = 40 arasında ise neredeyse durduğunu gösterir.

```term
$ python t02_baz.py
Test (son %20), H=1, hedef: akım (A). Periyot=600
Model                       MAE ort+-sd     RMSE ort+-sd
naif                     0.2345+-0.0024   0.2929+-0.0032
mevsimsel naif           0.2500+-0.0023   0.3145+-0.0050
hareketli ort. (10)      0.1819+-0.0003   0.2275+-0.0012
AR(40)                   0.1777+-0.0002   0.2221+-0.0009
AR derece seçimi (tohum 11, doğrulama MAE):
  p= 1  MAE=0.2323
  p= 2  MAE=0.2047
  p= 5  MAE=0.1844
  p=10  MAE=0.1799
  p=20  MAE=0.1797
  p=40  MAE=0.1780
```

Tablodan üç şey çıkıyor. Birincisi, naif tahmin 0,2345 ile hiç de kötü değil; bu seride değişim küçük ve tahmin hatası büyük ölçüde gürültüden kaynaklanıyor. İkincisi, mevsimsel naif (0,2500) naif tahminden kötü. Nedeni şu: sinüs bileşeni tam periyodik olsa da rüzgâr türbülansı AR(1) biçiminde, periyodik değildir. Mevsimsel naif, bir periyot önceki gürültüyü de kopyalar, dolayısıyla hata iki gürültü değerinin farkı kadar büyür. Üçüncüsü, AR(40) (0,1777 ± 0,0002) en güçlü baz modeldir ve sapması çok küçüktür. Derin modellerin bu çıtayı ne kadar geçtiğini Bölüm 68.12'de göreceğiz.

Bu tabloda bir uyarı var: AR derecesi, eğitimde (test değil) doğrulamada seçildi, ama p = 40 gibi yüksek bir derece, bu seri için bir "gecikme penceresi" gibi davranır. Gerçek bir sistemde derece, yalnızca doğrulama hatası değil, çıkarım gecikmesi ve bellek de göz önüne alınarak seçilmelidir.

## 68.5 RNN: gizli durum ve parametre paylaşımı

Bir MLP (Bölüm 63) girdisini tek seferde görür: tüm özellikler aynı anda gelir ve ağ onları birlikte işler. Zaman serisinde bu yetersizdir, çünkü anlam sırada yatar. Ağın geçmişi bir şekilde taşıması gerekir. Basit bir fikir yeterlidir: her adımda, şimdiki girdiyle birlikte, bir önceki adımın gizli durumunu da al ve yeni bir gizli durum üret. Bu, yinelemeli sinir ağı (recurrent neural network, RNN) fikridir.

Tek adımlık kural şöyledir: h_t = tanh(W_x x_t + W_h h_{t−1} + b), y_t = W_y h_t + b_y. Burada x_t girdi vektörü, h_t gizli durum, y_t çıktıdır. Dikkat edilecek iki nokta var. Birincisi, h_t bir bellektir: h_{t−1} üzerinden bütün geçmiş değerlerin bir özetini taşır, ama sınırlı boyutludur. İkincisi, W_x, W_h, W_y ve b her adımda aynıdır. Bu parametre paylaşımıdır ve iki işe yarar. Modelin parametre sayısı dizinin uzunluğuna bağlı olmaz ve model, bir örüntüyü dizinin neresinde görürse görsün aynı biçimde tanır. Bölüm 66'daki konvolüsyonun ağırlık paylaşımı ile aynı fikirdir; yalnızca paylaşım zaman boyunca değil, durum üzerinden yapılır.

Zaman içinde açma (unrolling) bir RNN'i düz bir ağ gibi görmenin yoludur. T adımlık bir dizi için RNN, T kopya hücreden oluşan derin bir ağ gibi çizilebilir; kopyaların ağırlıkları aynıdır. Şekil 68.3 üç adımı gösterir. Bu bakış, eğitimin nasıl yapılacağını da söyler: kopyalar üzerinden geri yayılım yaparsın, ama aynı ağırlıkların gradyanlarını toplayarak. Bunun adı zamanda geri yayılımdır (BPTT).

![Şekil 68.3: RNN'in açılımı. Her adım aynı üç ağırlık matrisini (W_x, W_h, W_y) kullanır; gizli durum h_t adımdan adıma geçer.](gorseller/b68_rnn_acilim.png)

Bölüm 63'teki MLP'nin ağırlıkları her katmanda farklıydı. Burada aynı ağırlıklar T kez kullanılır, bu yüzden bir ağırlığın gradyanı T adımın katkısının toplamıdır. Bu özellik hem güç (her adımda öğrenilen kural tekrar kullanılır) hem de sorundur (aşağıda göreceğimiz kaybolan ve patlayan gradyan).

## 68.6 Zamanda geri yayılım (BPTT) türetmesi

Kaybı her adımın toplamı olarak tanımlayalım: L = Σ_t ½ ||y_t − d_t||². Burada d_t adım t için hedeftir. Amacımız, W_h'nin gradyanı dL/dW_h'yi bulmak. Zincir kuralını bir kez daha uygularız, ama bu sefer bir gizli durumun etkisi hem kendi çıktısından hem de sonraki bütün adımlardan gelir. Tanımlayalım: δ_t = ∂L/∂h_t. Bu, h_t'nin kendi çıktısı üzerinden gelen katkı ile gelecek adımlardan gelen katkının toplamıdır:

δ_t = W_yᵀ (y_t − d_t) + W_hᵀ (δ_{t+1} ⊙ (1 − h_{t+1}²)).

Burada ⊙ eleman eleman çarpımdır ve tanh'ın türevi 1 − h² olarak kullanılmıştır. Son adımda ikinci terim yoktur (δ_{T+1} = 0). Bu bir geriye doğru özyinelemedir: δ'yı sondan başa doğru hesaplarız. Ağırlık gradyanları, her adımın katkılarının toplamıdır:

∂L/∂W_h = Σ_t (δ_t ⊙ (1 − h_t²)) h_{t−1}ᵀ, ∂L/∂W_x = Σ_t (δ_t ⊙ (1 − h_t²)) x_tᵀ.

Bu formüller, ileri geçişte kaydedilen gizli durumları gerektirir. Bu yüzden BPTT bellek harcar: T adımlık bir dizi için her h_t'yi saklamalısın. Uzun dizilerde bu pahalıdır; kesik BPTT (truncated BPTT) gradyanı yalnızca son k adım için geriye yayar. Bu, bellek ve hesabı sınırlar ama uzun vadeli bağımlılıkları da kısaltır. Bu bölümde kesik BPTT uygulamadık, yalnızca tam BPTT'yi kurduk.

Önce skaler bir RNN üzerinde elle izleyebileceğin bir örnek yapalım. Ağırlıklar W_x = 0,5, W_h = 0,8, b = 0; girdi dizisi 1, 0, −1; başlangıç h_0 = 0; kayıp L = ½ (h_3 − d)² ve d = 0,5. Aşağıdaki programın ilk kısmı ileri geçişi ve bu skaler gradyanları hesaplar; ikinci kısmı, vektör RNN için her parametre elemanını sayısal türevle karşılaştırarak bir gradient check yapar.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.6: skaler RNN'in elle izi, NumPy ile BPTT ve gradient
check."""
import numpy as np

# ---- 1. Skaler RNN: h_t = tanh(wx*x_t + wh*h_{t-1} + b) ----
wx, wh, b = 0.5, 0.8, 0.0
x = [1.0, 0.0, -1.0]
h = [0.0]                                  # h_0 = 0
for t, xt in enumerate(x, 1):
    h.append(np.tanh(wx * xt + wh * h[-1] + b))
    print("h_%d = tanh(%.1f*%.1f + %.1f*%.4f) = %.4f"
          % (t, wx, xt, wh, h[t - 1], h[t]))

# ---- 2. Skaler BPTT: L = 0.5*(h_3 - d)^2, d = 0,5 ----
d = 0.5
dL_dh3 = h[3] - d
g_wh = 0.0
g_wx = 0.0
dh_next = dL_dh3                           # dL/dh_t
for t in (3, 2, 1):
    da = dh_next * (1 - h[t] ** 2)         # tanh'(a_t) = 1 - h_t^2
    g_wh += da * h[t - 1]
    g_wx += da * x[t - 1]
    dh_next = da * wh                      # dL/dh_{t-1}
print("dL/dwh = %.6f   dL/dwx = %.6f" % (g_wh, g_wx))
```

Programın devamı aşağıdadır.

```python
def kayip(wx_, wh_):
    hh = 0.0
    for xt in x:
        hh = np.tanh(wx_ * xt + wh_ * hh + b)
    return 0.5 * (hh - d) ** 2

eps = 1e-6
sayi_wh = (kayip(wx, wh + eps) - kayip(wx, wh - eps)) / (2 * eps)
sayi_wx = (kayip(wx + eps, wh) - kayip(wx - eps, wh)) / (2 * eps)
print("sayisal dL/dwh = %.6f   dL/dwx = %.6f" % (sayi_wh, sayi_wx))
print("bagil hata wh: %.2e  wx: %.2e" % (
    abs(g_wh - sayi_wh) / max(abs(g_wh), 1e-12),
    abs(g_wx - sayi_wx) / max(abs(g_wx), 1e-12)))

# ---- 3. Vektör RNN, her adımda kayıp, gradient check ----
def ileri(p, X):
    H = p["Wh"].shape[0]
    hs = np.zeros((len(X) + 1, H))
    for t in range(len(X)):
        hs[t + 1] = np.tanh(p["Wx"] @ X[t] + p["Wh"] @ hs[t] + p["b"])
    Y = hs[1:] @ p["Wy"].T + p["by"]
    return hs, Y

def kayip_v(p, X, D):
    _, Y = ileri(p, X)
    return 0.5 * np.sum((Y - D) ** 2)
```

Programın devamı aşağıdadır.

```python
def geri(p, X, D):
    hs, Y = ileri(p, X)
    T, H = len(X), p["Wh"].shape[0]
    dY = Y - D                             # dL/dy_t
    g = {k: np.zeros_like(v) for k, v in p.items()}
    g["Wy"] = dY.T @ hs[1:]
    g["by"] = dY.sum(axis=0)
    dh_next = np.zeros(H)                  # gelecekten gelen gradyan
    for t in reversed(range(T)):
        dh = dY[t] @ p["Wy"] + dh_next     # ileri ve geri katkı
        da = dh * (1 - hs[t + 1] ** 2)
        g["Wx"] += np.outer(da, X[t])
        g["Wh"] += np.outer(da, hs[t])
        g["b"] += da
        dh_next = p["Wh"].T @ da
    return g

rng = np.random.default_rng(0)
H, I, O, T = 3, 2, 1, 5
p = {"Wx": rng.normal(0, 0.5, (H, I)),
     "Wh": rng.normal(0, 0.5, (H, H)),
     "b": np.zeros(H),
     "Wy": rng.normal(0, 0.5, (O, H)),
     "by": np.zeros(O)}
X = rng.normal(size=(T, I))
D = rng.normal(size=(T, O))
g = geri(p, X, D)
en_kotu = 0.0
for ad in p:
    e = np.zeros_like(p[ad])
    dene = []
    for idx in np.ndindex(p[ad].shape):
        orj = p[ad][idx]
        p[ad][idx] = orj + 1e-6; lp = kayip_v(p, X, D)
        p[ad][idx] = orj - 1e-6; lm = kayip_v(p, X, D)
        p[ad][idx] = orj
        dene.append((lp - lm) / 2e-6)
    e = np.array(dene).reshape(p[ad].shape)
    pay = np.abs(g[ad] - e)
    bagil = pay / np.maximum(np.abs(g[ad]) + np.abs(e), 1e-12)
```

Programın devamı aşağıdadır.

```python
    en_kotu = max(en_kotu, bagil.max())
    print("%-3s  en büyük bağıl hata = %.2e" % (ad, bagil.max()))
print("GENEL en büyük bağıl hata = %.2e" % en_kotu)
```

Çıktıda ilk üç satır ileri geçişi, sonraki iki satır skaler gradyanları ve sayısal türevi verir. Son satırlar vektör RNN'in gradient check sonucudur.

```term
$ python t03_bptt.py
h_1 = tanh(0.5*1.0 + 0.8*0.0000) = 0.4621
h_2 = tanh(0.5*0.0 + 0.8*0.4621) = 0.3537
h_3 = tanh(0.5*-1.0 + 0.8*0.3537) = -0.2137
dL/dwh = -0.461209   dL/dwx = 0.381173
sayisal dL/dwh = -0.461209   dL/dwx = 0.381173
bagil hata wh: 3.28e-11  wx: 9.71e-11
Wx   en büyük bağıl hata = 4.07e-09
Wh   en büyük bağıl hata = 4.03e-09
b    en büyük bağıl hata = 1.18e-10
Wy   en büyük bağıl hata = 6.42e-10
by   en büyük bağıl hata = 4.51e-11
GENEL en büyük bağıl hata = 4.07e-09
```

Bağıl hata, dört parametre grubunda da 10⁻⁸ mertebesinde kaldı. Bu, türetmenin ve kodun uyumlu olduğunu gösterir. Gradient check her zaman kullanılması gereken bir araçtır: bir geri yayılım kodu yanlışsa, ağ yine de öğrenebilir gibi görünür ama yanlış yönde adım atar. Sayısal türev (merkezi fark) ile analitik gradyan arasındaki fark, yaklaşık bir hata olarak 10⁻⁶ düzeyinde beklenir; daha büyük fark bir hata işaretidir.

## 68.7 Kaybolan ve patlayan gradyan

BPTT'nin formülünde dikkat çekici bir yapı var. δ_t, her adımda W_hᵀ ile ve tanh türevi ile çarpılarak geriye taşınır. T adımdan sonra başlangıca giden gradyan, bu Jacobyenlerin çarpımıdır:

∂h_T/∂h_0 = Π_t diag(1 − h_t²) W_h.

Bu çarpımın normu iki şekilde davranabilir. Eğer W_h'nin spektral yarıçapı (en büyük özdeğerin mutlak değeri) 1'den küçükse, çarpım üssel olarak sönümlenir: uzak geçmişin gradyanı ulaşamaz. Bu, kaybolan gradyan sorunudur. Eğer yarıçap 1'den büyükse, başlangıçta büyüme görülebilir; bu patlayan gradyan sorunudur. Bölüm 55'te sigmoid zincirinde gördüğümüz olgu burada da vardır: σ'(z) en fazla 1/4 olduğu için her katman gradyanı küçültür. tanh'ın türevi en fazla 1'dir, ama 1'e yakın olması için girdinin sıfıra yakın olması gerekir; uzun dizilerde gizli durumların çoğu tanh'ın doygun bölgesindedir ve türev küçüktür.

Aşağıdaki t04 programı bu olguyu ölçer. Gizli boyut 32 ve spektral yarıçap ρ ∈ {0,9; 1,0; 1,1} için 20 rastgele tohumla h_t = tanh(W h_{t−1}) yinelemesini çalıştırır ve J_t = diag(1 − h_t²) W çarpımının spektral normunu T = 1..100 için kaydeder.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.2: adım sayısına göre Jacobian çarpımının normu.
h_t = tanh(W h_{t-1}); P_T = J_T ... J_1, J_t = diag(1-h_t^2) W.
Ölçüm: ||P_T||_2, 20 tohum üzerinden medyan."""
import numpy as np
from ortak import yaz_csv

H, T_MAX, TOHUM = 32, 100, 20


def kumulatif_norm(rho, tohum):
    rng = np.random.default_rng(tohum)
    G = rng.normal(0, 1, (H, H))
    yaricap = np.max(np.abs(np.linalg.eigvals(G)))
    W = G * (rho / yaricap)                     # yarıçap = rho
    h = np.tanh(rng.normal(0, 1, H))
    P = np.eye(H)
    norm = []
    for _ in range(T_MAX):
        h = np.tanh(W @ h)
        J = (1 - h ** 2)[:, None] * W
        P = J @ P
        norm.append(np.linalg.norm(P, 2))
    return np.array(norm)
```

Programın devamı aşağıdadır.

```python
rhos = (0.9, 1.0, 1.1)
tablo = {}
for rho in rhos:
    M = np.array([kumulatif_norm(rho, s) for s in range(TOHUM)])
    tablo[rho] = np.median(M, axis=0)

print("T    " + "  ".join("rho=%.1f" % r for r in rhos))
for T in (1, 2, 5, 10, 20, 50, 100):
    satir = ["%9.2e" % tablo[r][T - 1] for r in rhos]
    print("%-4d " % T + "  ".join(satir))
basl = ["T"] + ["rho_%.1f" % r for r in rhos]
yaz_csv("b68_gradyan_adim.csv", basl,
        [(T,) + tuple("%.6e" % tablo[r][T - 1] for r in rhos)
         for T in range(1, T_MAX + 1)])
```

Çıktı, adım sayısına göre medyan normu gösterir.

```term
$ python t04_gradyan_adim.py
T    rho=0.9  rho=1.0  rho=1.1
1     1.35e+00   1.48e+00   1.61e+00
2     1.23e+00   1.45e+00   1.65e+00
5     7.74e-01   1.14e+00   1.56e+00
10    4.38e-01   9.28e-01   1.73e+00
20    1.41e-01   7.89e-01   2.22e+00
50    6.01e-03   6.39e-01   5.05e-01
100   3.01e-05   5.07e-01   5.28e-02
```

ρ = 0,9 için norm 1 adımda 1,35 iken 50 adımda 6·10⁻³, 100 adımda 3·10⁻⁵ olur. Bu, üssel sönümlenmenin tipik görüntüsüdür; 0,9^100 ≈ 2,7·10⁻⁵ değeri ile uyumludur. ρ = 1,0 için norm yavaşça azalır (100 adımda 0,51). Burada yarıçap 1 ama tanh doyumu gradyanı küçültür. ρ = 1,1 için norm ilk yirmi adımda büyür (20 adımda 2,22), ama 50 adımda 0,51'e, 100 adımda 0,053'e düşer. Yani patlama her zaman sürmez: tanh doygun bölgeye girdiğinde türevler sıfıra yaklaşır ve çarpım yeniden sönümlenir. Bu, "yarıçap 1'den büyükse patlar" sezgisinin eksik olduğunu gösterir. Patlama gerçektir ama kararlı değildir; bu yüzden eğitimde patlamaya karşı bir önlem olarak gradyan kırpma kullanılır.

Şekil 68.4 aynı sonucu log ölçeğinde gösterir. Kesikli eğri 0,9^T referansıdır; ρ = 0,9 eğrisinin bu referansa yakın olması, zincirin gerçekten yarıçap kadar sönümlendiğini gösterir.

![Şekil 68.4: Adım sayısına göre ||∂h_T/∂h_0||₂ (medyan, 20 tohum), log ölçeğinde. ρ = 0,9 üssel olarak söner; ρ = 1,1 başlangıçta büyür, sonra doygunluk nedeniyle söner.](gorseller/b68_gradyan_adim.png)

Bu ölçüm iki sonuç çıkarır. Birincisi, vanilla RNN'de uzun bağımlılık öğrenmek zordur: kaybolan gradyan, geçmişteki bilgiye giden öğrenme sinyalini yok eder. İkincisi, gradyan kırpma (Bölüm 64) patlamaya karşı etkilidir. Bu bölümdeki bütün eğitimlerde gradyan normunu 1,0'da kırptık. Kaybolan gradyanı kırpma çözmez; bunun için kapılı hücreler gerekir, bir sonraki bölümde LSTM'yi bu yüzden inceliyoruz.

## 68.8 LSTM: kapılar ve hücre durumu

LSTM (long short-term memory), 1997'de Hochreiter ve Schmidhuber'in önerdiği hücredir. Fikri basittir: gizli duruma ek olarak, adımdan adıma doğrusal biçimde akan bir hücre durumu c_t ekler ve her adımda bu duruma neyin yazılacağını, neyin silineceğini ve neyin dışarı verileceğini üç kapıyla (gate) yönetir. Kapılar sigmoid ile üretilen 0 ile 1 arasında değerlerdir; 1 "tamamen geçir", 0 "tamamen kes" anlamına gelir.

Denklemler şöyledir. Girdi x_t ve önceki gizli durum h_{t−1} birlikte bir ön aktivasyona girer:

f_t = σ(W_f x_t + U_f h_{t−1} + b_f)   (unutma kapısı)
i_t = σ(W_i x_t + U_i h_{t−1} + b_i)   (giriş kapısı)
g_t = tanh(W_g x_t + U_g h_{t−1} + b_g)   (aday değer)
o_t = σ(W_o x_t + U_o h_{t−1} + b_o)   (çıkış kapısı)
c_t = f_t ⊙ c_{t−1} + i_t ⊙ g_t
h_t = o_t ⊙ tanh(c_t).

Asıl fikir hücre durumu satırındadır: c_t = f_t ⊙ c_{t−1} + i_t ⊙ g_t. Bu bir toplamdır, çarpım zinciri değildir. Geriye giden gradyan, ∂c_t/∂c_{t−1} = f_t, yani yalnızca unutma kapısıyla çarpılır. Unutma kapısı 1'e yakın kalırsa, gradyan çok adım boyunca neredeyse değişmeden akar. Bu, vanilla RNN'deki W_h çarpım zincirine karşı bir "otoyoldur". Şekil 68.5 bu yolu koyu çizgi olarak gösterir.

Bu, kaybolan gradyanı ortadan kaldırmaz; yalnızca azaltır. Unutma kapısı 1'den küçükse (ki sigmoid çıkışı çoğu zaman öyledir) gradyan yine sönümlenir, ama bu sönümlenme ağın kendisi tarafından öğrenilir ve hücre tarafından kontrol edilir. Kapılar, bir sinyalin ne kadar süre taşınacağına ağın karar vermesine izin verir. Bu nedenle LSTM, vanilla RNN'den daha uzun bağımlılıkları yakalayabilir. Ama bu kazanım garanti değildir; aşağıdaki deneyde bunu görüyorsun.

![Şekil 68.5: LSTM hücresi. Üstteki koyu çizgi hücre durumu c_t yoludur; alttaki üç kapı (σ, σ, tanh) ve çıkış kapısı [h_{t−1}, x_t] girdisinden beslenir.](gorseller/b68_lstm_hucre.png)

LSTM'in PyTorch'taki kapı sırası i, f, g, o'dur (giriş, unutma, aday, çıkış); birçok kaynak f, i, o, g sıralar, ama PyTorch belgesi ve kodu bu sırayı kullanır. Bir başka ayrıntı, PyTorch'un iki sapma vektörü tutmasıdır: bias_ih ve bias_hh. Bunlar toplanır ve tek bir sapma gibi davranır. Aşağıdaki t05 programı bu sıralamayı NumPy ile sıfırdan yazılmış bir LSTM ileri geçişiyle karşılaştırır. Aynı ağırlıkları iki uygulamaya verdiğimizde çıktılar 10⁻¹⁶ düzeyinde aynı çıkmalıdır; bu, sıralamanın doğru eşlendiğinin kanıtıdır. Ayrıca parametre sayılarını ölçer ve çift yönlü, iki katmanlı bir LSTM'in çıktı şeklini gösterir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.3 ve 68.6: LSTM ileri geçişi (NumPy) ile PyTorch'un
nn.LSTM'i aynı ağırlıklarla eşleşiyor mu; kapı sırası i,f,g,o.
Ayrıca skaler bir LSTM adımının elle hesabı (Örnek 3)."""
import numpy as np
import torch
import torch.nn as nn

sig = lambda z: 1.0 / (1.0 + np.exp(-z))


def lstm_ileri(x, Wih, Whh, bih, bhh):
    """x: (T, I). Kapılar sırayla i, f, g, o (PyTorch sırası)."""
    H = Whh.shape[1]
    h, c = np.zeros(H), np.zeros(H)
    hs = []
    for xt in x:
        a = Wih @ xt + bih + Whh @ h + bhh          # (4H,)
        i = sig(a[0:H])
        f = sig(a[H:2 * H])
        g = np.tanh(a[2 * H:3 * H])
        o = sig(a[3 * H:4 * H])
        c = f * c + i * g                           # hücre "otoyolu"
        h = o * np.tanh(c)
        hs.append(h)
    return np.array(hs), h, c
```

Programın devamı aşağıdadır.

```python

# ---- 1. Eşleşme testi: I=5, H=32, T=20 (float64) ----
torch.manual_seed(0)
I, H, T = 5, 32, 20
lstm = nn.LSTM(I, H).double()
x = np.random.default_rng(1).normal(size=(T, I))
with torch.no_grad():
    out, (hn, cn) = lstm(torch.tensor(x).unsqueeze(1))
out = out[:, 0].numpy()
hs, h_son, c_son = lstm_ileri(
    x, lstm.weight_ih_l0.detach().numpy(),
    lstm.weight_hh_l0.detach().numpy(),
    lstm.bias_ih_l0.detach().numpy(),
    lstm.bias_hh_l0.detach().numpy())
print("max|h_numpy - h_torch| = %.2e" % np.abs(hs - out).max())
print("max|c_son - c_torch| = %.2e"
      % np.abs(c_son - cn[0, 0].numpy()).max())

# ---- 2. Parametre sayıları (I=5, H=32) ----
def say(m):
    return sum(p.numel() for p in m.parameters())

print("parametre sayisi (I=5, H=32):")
print("  RNN  :", say(nn.RNN(I, H)))
print("  GRU  :", say(nn.GRU(I, H)))
print("  LSTM :", say(nn.LSTM(I, H)))
print("formul LSTM 4(HI+H^2+2H) =", 4 * (H * I + H * H + 2 * H))
print("formul GRU  3(HI+H^2+2H) =", 3 * (H * I + H * H + 2 * H))
```

Programın devamı aşağıdadır.

```python
# ---- 3. Çift yönlü, 2 katmanlı LSTM şekilleri ----
bl = nn.LSTM(5, 32, num_layers=2, bidirectional=True,
             batch_first=True)
y, (hn2, cn2) = bl(torch.zeros(4, 20, 5))
print("cift yonlu cikti:", tuple(y.shape), " h_n:", tuple(hn2.shape))

# ---- 4. Skaler LSTM adımı (Örnek 3) ----
wih = np.array([[0.5], [0.9], [1.2], [0.7]])     # i, f, g, o
whh = np.array([[0.2], [-0.3], [0.4], [0.1]])
bih = np.array([0.1, 0.2, 0.0, -0.1])
bhh = np.zeros(4)
x1, h0, c0 = np.array([1.0]), 0.5, 0.4
a = wih @ x1 + bih + whh @ np.array([h0]) + bhh
i_, f_, g_, o_ = sig(a[0]), sig(a[1]), np.tanh(a[2]), sig(a[3])
c1 = f_ * c0 + i_ * g_
h1 = o_ * np.tanh(c1)
print("a = %s" % np.round(a, 4))
print("i=%.4f f=%.4f g=%.4f o=%.4f" % (i_, f_, g_, o_))
print("c1=%.4f h1=%.4f" % (c1, h1))
cell = nn.LSTMCell(1, 1).double()
with torch.no_grad():
    cell.weight_ih.copy_(torch.tensor(wih))
    cell.weight_hh.copy_(torch.tensor(whh))
    cell.bias_ih.copy_(torch.tensor(bih))
    cell.bias_hh.copy_(torch.tensor(bhh))
    d64 = torch.float64
    h_t, c_t = cell(torch.tensor([[1.0]], dtype=d64),
                    (torch.tensor([[h0]], dtype=d64),
                     torch.tensor([[c0]], dtype=d64)))
print("torch: h1=%.4f c1=%.4f" % (h_t.item(), c_t.item()))
```

Çıktı, eşleşme hatasını, parametre sayılarını, çift yönlü şekli ve skaler bir LSTM adımını verir.

```term
$ python t05_lstm_gru.py
max|h_numpy - h_torch| = 5.55e-17
max|c_son - c_torch| = 5.55e-17
parametre sayisi (I=5, H=32):
  RNN  : 1248
  GRU  : 3744
  LSTM : 4992
formul LSTM 4(HI+H^2+2H) = 4992
formul GRU  3(HI+H^2+2H) = 3744
cift yonlu cikti: (4, 20, 64)  h_n: (4, 4, 32)
a = [0.7  0.95 1.4  0.65]
i=0.6682 f=0.7211 g=0.8854 o=0.6570
c1=0.8800 h1=0.4641
torch: h1=0.4641 c1=0.8800
```

Eşleşme hatası 5,55·10⁻¹⁷ olarak çıktı: NumPy ve PyTorch aynı sonucu üretti. Parametre sayısı LSTM için 4(HI + H² + 2H)'dir; I = 5, H = 32 için 4992. Bu formül, dört kapının her birinin ayrı bir W, U ve iki sapma taşımasından gelir. Çift yönlü ve iki katmanlı LSTM'in çıktısı (4, 20, 64) şeklindedir: son boyut, iki yönün gizli durumlarının yan yana konmasıyla 2H = 64 olur. Gizli durum h_n'nin ilk boyutu 4'tür, yani 2 katman × 2 yön.

Son bölümde skaler bir LSTM adımının elle hesabı var; bu Çözümlü Örnek 3'ün verisidir. Girdi x = 1, önceki durum h = 0,5, c = 0,4 ve ağırlıklar programda verilmiş. Ön aktivasyonlar [0,7; 0,95; 1,4; 0,65] çıkar; kapılar i = 0,6682, f = 0,7211, g = 0,8854, o = 0,6570. Hücre durumu c_1 = 0,8800, gizli durum h_1 = 0,4641. PyTorch'un LSTMCell'i aynı sonucu verir.

## 68.9 GRU ve uzun bağımlılık deneyi

GRU (gated recurrent unit), 2014'te Cho ve arkadaşlarının önerdiği, LSTM'in sadeleştirilmiş bir biçimidir. Hücre durumunu ve çıkış kapısını kaldırır, iki kapı kullanır: güncelleme kapısı z ve sıfırlama kapısı r. PyTorch belgesindeki denklemler şöyledir:

r_t = σ(W_ir x_t + b_ir + W_hr h_{t−1} + b_hr)
z_t = σ(W_iz x_t + b_iz + W_hz h_{t−1} + b_hz)
n_t = tanh(W_in x_t + b_in + r_t ⊙ (W_hn h_{t−1} + b_hn))
h_t = (1 − z_t) ⊙ n_t + z_t ⊙ h_{t−1}.

Bu yapıda z_t, yeni adayla eski durum arasında bir karışım katsayısıdır: z = 0 ise h_t doğrudan adayı alır, z = 1 ise durumu olduğu gibi korur. Bu, LSTM'deki unutma ve giriş kapılarının tek bir kapıda birleşmesidir. Parametre sayısı 3(HI + H² + 2H)'dir; I = 5, H = 32 için 3744. Bu, LSTM'in 4992'sinden yaklaşık %25 azdır, ama her iki model de vanilla RNN'in (1248) çok üstündedir. Hangisinin kazanacağı, görevin yapısına ve eğitim bütçesine bağlıdır; bunu aşağıda ölçüyoruz.

Şimdi bir uzun bağımlılık görevi tanımlayalım. Her dizinin ilk adımında ±1 işareti vardır; sonraki T − 1 adımda yalnızca küçük gürültü vardır. Model son adımda ilk işareti tahmin etmelidir. Bilgi yalnızca ilk adımda var, ve gizli durum o bilgiyi T − 1 adım boyunca taşımalıdır. Bu, kaybolan gradyanın doğrudan bir ölçüsüdür. Deney, T ∈ {10, 20, 40, 80} için RNN, LSTM ve GRU'yu üç tohumla eğitir: gizli boyut 16, 2500 adım, batch 64, Adam (öğrenme oranı 3·10⁻³), gradyan kırpma 1,0. Dizi uzunluğu eğitimde ve testte aynıdır. Test kümesi her tohum için 2000 yeni örnekten oluşur.

Bu programın ortak.py'deki Tekrarli sınıfını kullanabilmesi için ortak.py'nin sinir ağı kısmını da burada veriyoruz. Bu kısım RNN, LSTM ve GRU'yu tek bir sarmalayıcıda toplar ve eğitim döngüsünü tanımlar. TCN sınıfını 68.11'de ayrıca açıklayacağız.

```python
# ---------- sinir ağları ----------
class Tekrarli(nn.Module):
    """RNN, LSTM ya da GRU üzerine doğrusal baş; son gizli durum."""

    def __init__(self, tip, c, h=32, cikis=1):
        super().__init__()
        sinif = {"rnn": nn.RNN, "lstm": nn.LSTM, "gru": nn.GRU}[tip]
        self.rnn = sinif(c, h, batch_first=True)
        self.bas = nn.Linear(h, cikis)

    def forward(self, x):
        cikti, _ = self.rnn(x)
        return self.bas(cikti[:, -1])


class TCNBlok(nn.Module):
    """İki nedensel genişletilmiş konvolüsyon + artık bağlantı."""

    def __init__(self, cgir, ccik, k, d):
        super().__init__()
        self.pad = (k - 1) * d
        self.c1 = nn.Conv1d(cgir, ccik, k, dilation=d)
        self.c2 = nn.Conv1d(ccik, ccik, k, dilation=d)
        self.yan = (nn.Conv1d(cgir, ccik, 1)
                    if cgir != ccik else nn.Identity())
```

Programın devamı aşağıdadır.

```python
    def forward(self, x):
        h = F.relu(self.c1(F.pad(x, (self.pad, 0))))
        h = self.c2(F.pad(h, (self.pad, 0)))
        return F.relu(h + self.yan(x))


class TCN(nn.Module):
    """Girdi (B, L, C); çıktı son zaman adımından."""

    def __init__(self, c, kanal=32, k=3, dil=(1, 2, 4, 8), cikis=1):
        super().__init__()
        bl, g = [], c
        for d in dil:
            bl.append(TCNBlok(g, kanal, k, d))
            g = kanal
        self.bloklar = nn.Sequential(*bl)
        self.bas = nn.Linear(kanal, cikis)
        self.k, self.dil = k, dil

    def alici_alan(self):
        return 1 + sum(2 * (self.k - 1) * d for d in self.dil)

    def forward(self, x):
        h = self.bloklar(x.transpose(1, 2))
        return self.bas(h[:, :, -1])
```

Programın devamı aşağıdadır.

```python

def egit(model, Xtr, ytr, Xva, yva, epoch=40, lr=2e-3, bs=128,
         sabir=6, seed=0):
    """Adam + MSE. Doğrulama kaybı en düşük olan ağırlıklar geri
    yüklenir (erken durdurma). Gradyan normu 1.0'da kırpılır."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    Xt, yt = torch.tensor(Xtr), torch.tensor(ytr)
    Xv, yv = torch.tensor(Xva), torch.tensor(yva)
    en = (np.inf, None, -1)
    bekle = 0
    for ep in range(epoch):
        model.train()
        sira = rng.permutation(len(Xt))
        for b in range(0, len(sira), bs):
            j = sira[b:b + bs]
            opt.zero_grad()
            kayip = F.mse_loss(model(Xt[j]), yt[j])
            kayip.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        model.eval()
        with torch.no_grad():
            va = F.mse_loss(model(Xv), yv).item()
        if va < en[0] - 1e-6:
            en = (va, {k: v.clone()
                       for k, v in model.state_dict().items()}, ep)
            bekle = 0
        else:
            bekle += 1
            if bekle >= sabir:
                break
    model.load_state_dict(en[1])
    return en[0], en[2]
```

Programın devamı aşağıdadır.

```python

def tahmin(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(X)).numpy()


def yaz_csv(yol, basliklar, satirlar):
    os.makedirs(VERI, exist_ok=True)
    with open(os.path.join(VERI, yol), "w", encoding="utf-8") as f:
        f.write(",".join(basliklar) + "\n")
        for r in satirlar:
            f.write(",".join(str(x) for x in r) + "\n")
```

Aşağıdaki t06 programı, görevi ve eğitim döngüsünü tanımlar. Görev üretimi, eğitim (ikili çapraz entropi, gradyan kırpma) ve değerlendirme ayrı fonksiyonlardadır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.3: uzun bağımlılık görevi. İlk adımdaki işaret (+1/-1)
T-1 adım sonra tahmin edilir. RNN, LSTM, GRU; 3 tohum; CPU."""
import time
import numpy as np
import torch
import torch.nn.functional as F
from ortak import Tekrarli, yaz_csv

torch.set_num_threads(4)


def gorev(n, T, rng):
    s = rng.choice([-1.0, 1.0], size=n)
    X = np.zeros((n, T, 1), np.float32)
    X[:, 0, 0] = s
    X[:, 1:, 0] = 0.1 * rng.normal(size=(n, T - 1))   # gürültü
    return torch.tensor(X), torch.tensor((s > 0).astype(np.float32))


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        p = (model(X)[:, 0] > 0).float()
    return (p == y).float().mean().item()
```

Programın devamı aşağıdadır.

```python

def calistir(tip, T, tohum, adim=2500):
    torch.manual_seed(tohum)
    rng = np.random.default_rng(100 + tohum)
    model = Tekrarli(tip, 1, h=16, cikis=1)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    for _ in range(adim):
        X, y = gorev(64, T, rng)
        model.train()
        opt.zero_grad()
        kayip = F.binary_cross_entropy_with_logits(model(X)[:, 0], y)
        kayip.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    Xt, yt = gorev(2000, T, np.random.default_rng(999 + tohum))
    return dogruluk(model, Xt, yt)


satir = []
print("%-5s %-4s %s" % ("model", "T", "test doğruluğu (3 tohum)"))
t0 = time.time()
for tip in ("rnn", "lstm", "gru"):
    for T in (10, 20, 40, 80):
        acc = [calistir(tip, T, s) for s in (1, 2, 3)]
        for s, a in zip((1, 2, 3), acc):
            satir.append((tip, T, s, round(a, 4)))
        print("%-5s %-4d %.3f +- %.3f  [%s]" % (
            tip, T, np.mean(acc), np.std(acc, ddof=1),
            " ".join("%.3f" % a for a in acc)))
print("toplam sure: %.0f s" % (time.time() - t0))
yaz_csv("b68_uzun_bagimlilik.csv",
         ["model", "T", "tohum", "dogruluk"], satir)
```

Çıktı, her model ve T için üç tohumun doğruluğunu verir.

```term
$ python t06_uzun.py
model T    test doğruluğu (3 tohum)
rnn   10   1.000 +- 0.000  [1.000 1.000 1.000]
rnn   20   1.000 +- 0.000  [1.000 1.000 1.000]
rnn   40   0.667 +- 0.288  [0.493 1.000 0.509]
rnn   80   0.668 +- 0.287  [0.495 1.000 0.511]
lstm  10   1.000 +- 0.000  [1.000 1.000 1.000]
lstm  20   1.000 +- 0.000  [1.000 1.000 1.000]
lstm  40   0.505 +- 0.011  [0.493 0.513 0.509]
lstm  80   0.505 +- 0.011  [0.493 0.513 0.509]
gru   10   1.000 +- 0.000  [1.000 1.000 1.000]
gru   20   1.000 +- 0.000  [1.000 1.000 1.000]
gru   40   0.505 +- 0.011  [0.493 0.513 0.509]
gru   80   0.505 +- 0.011  [0.493 0.513 0.509]
toplam sure: 1054 s
```

Sonuçlar beklediğimizden farklıdır, ve bunu olduğu gibi raporluyoruz. T = 10 ve T = 20'de üç model de (RNN dahil) bütün tohumlarda %100 doğruluk verdi; bu adım sayısında görev kolaydır. T = 40'ta RNN üç tohumun birinde (tohum 2) mükemmel öğrendi, diğer ikisinde şans düzeyinde kaldı (0,49–0,51). LSTM ve GRU ise T = 40 ve 80'de üç tohumun hiçbirinde öğrenemedi: doğruluk 0,49–0,51 aralığında kaldı. Yani bu bütçede kapılı hücrelerin üstünlüğü görülmedi. Olası nedenler şunlar: 2500 adım, T = 40 için yetersiz olabilir; sigmoid kapıların başlangıçta yarı açık olması unutmayı zorlaştırır; ve bu görevde yalnızca tek bir bilginin korunması gerekir, kapıların bunu bulması optimizasyon için zordur. Kesin nedeni bu deneyden çıkarmıyoruz. Dersi şu: LSTM'in uzun bağımlılığı öğrenebilmesi bir kapı tasarımından gelir, ama bu öğrenme eğitim bütçesine ve başlatmaya bağlıdır. Bir mimariyi, yalnızca teorisine dayanarak "daha iyi" diye seçmek yerine, aynı görevde ölçmek gerekir.

Şekil 68.6, T'ye göre ortalama doğruluğu ve tohum sapmasını gösterir.

![Şekil 68.6: Uzun bağımlılık görevinde T'ye göre test doğruluğu (3 tohum ortalaması ve sapma). Kesikli çizgi şans düzeyidir (0,5).](gorseller/b68_uzun_bagimlilik.png)

Bu sonucu Bölüm 68.16'da akış ve kapılı hücrelerin maliyeti tartışmasında hatırla: LSTM ve GRU, bu basit görevde RNN'den üstün değildi, ama sahada daha karmaşık görevlerde (tahmin, Bölüm 68.12) durum değişebilir. Bu bölümün tahmin deneyinde GRU, kendi tohumlarında en iyi çıkıyor.

Bu sonuç için iki açıklama denemesi yaptık ve ikisini de ayrı bir koşuda ölçtük. İlkinde LSTM'in unutma kapısının sapmasını 1 ile başlattık. Bu, Jozefowicz ve arkadaşlarının 2015'te önerdiği bir pratiktir (genel bilgi). PyTorch'ta LSTM'in sapma vektörü dört kapının sırasıyla (i, f, g, o) dizilmiş 4H uzunluğunda bir vektördür; unutma kapısının dilimi bu yüzden H ile 2H arasıdır. İkincisinde eğitimi 8000 adıma çıkardık. Aşağıdaki program yalnızca LSTM'i ve yalnızca T = 40 ile T = 80'i çalıştırır; üç tohum kullanılır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.9 ek deney: LSTM unutma kapısı sapması 1 ile başlatılır
(Jozefowicz ve ark. 2015, genel bilgi). PyTorch'ta kapı sırası i,f,g,o
olduğundan unutma kapısının sapması bias_ih_l0[H:2H]'dir. Eğitim
8000 adım; T = 40 ve 80; 3 tohum; CPU."""
import time
import numpy as np
import torch
import torch.nn.functional as F
from ortak import Tekrarli

torch.set_num_threads(4)


def gorev(n, T, rng):
    s = rng.choice([-1.0, 1.0], size=n)
    X = np.zeros((n, T, 1), np.float32)
    X[:, 0, 0] = s
    X[:, 1:, 0] = 0.1 * rng.normal(size=(n, T - 1))
    return torch.tensor(X), torch.tensor((s > 0).astype(np.float32))


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        p = (model(X)[:, 0] > 0).float()
    return (p == y).float().mean().item()
```

Programın devamı aşağıdadır.

```python

def calistir(T, tohum, adim=8000, unutma_sapma=1.0):
    torch.manual_seed(tohum)
    rng = np.random.default_rng(100 + tohum)
    model = Tekrarli("lstm", 1, h=16, cikis=1)
    H = 16
    if unutma_sapma is not None:
        with torch.no_grad():
            model.rnn.bias_ih_l0[H:2 * H].fill_(unutma_sapma)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    for _ in range(adim):
        X, y = gorev(64, T, rng)
        model.train()
        opt.zero_grad()
        kayip = F.binary_cross_entropy_with_logits(model(X)[:, 0], y)
        kayip.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    Xt, yt = gorev(2000, T, np.random.default_rng(999 + tohum))
    return dogruluk(model, Xt, yt)


print("LSTM, unutma kapisi sapmasi = 1, 8000 adim")
print("%-4s %s" % ("T", "test dogrulugu (3 tohum)"))
t0 = time.time()
for T in (40, 80):
    acc = [calistir(T, s) for s in (1, 2, 3)]
    print("%-4d %.3f +- %.3f  [%s]" % (
        T, np.mean(acc), np.std(acc, ddof=1),
        " ".join("%.3f" % a for a in acc)))
print("toplam sure: %.0f s" % (time.time() - t0))
```

Çıktı şöyledir.

```term
$ python t06b_unutma.py
LSTM, unutma kapisi sapmasi = 1, 8000 adim
T    test dogrulugu (3 tohum)
40   1.000 +- 0.000  [1.000 1.000 1.000]
80   0.501 +- 0.012  [0.507 0.487 0.509]
toplam sure: 1139 s
```

T = 40'ta üç tohumun üçü de %100 doğruluk verdi. Önceki 2500 adımlık koşuda aynı T'de LSTM şans düzeyinde kalmıştı (0,505). Yani sapma ve bütçe birlikte, bu görevde T = 40'ta öğrenmeyi sağladı. T = 80'de ise sonuç yine şans düzeyindedir (0,501 ± 0,012). Burada iki değişikliği birbirinden ayırmadık; bu nedenle farkın hangisinden geldiğini söyleyemeyiz. Ayrıca T = 80 için farklı bir öğrenme oranı, daha uzun eğitim ya da kısa diziden uzuna bir eğitim sırası denenmeden, kapılı hücrenin bu uzunlukta öğrenemediği sonucuna varılamaz.

## 68.10 Çift yönlü, çok katmanlı ve dizi-dizi modeller; öğretmen zorlaması

Şimdiye kadar tek yönlü ve tek katmanlı modellere baktık. Pratikte üç değişiklik sık kullanılır. Çift yönlü (bidirectional) RNN, diziyi iki yönde okur: bir katman soldan sağa, diğeri sağdan sola çalışır ve çıktılar birleştirilir. Bu, tüm dizi elimizdeyse, örneğin bir uçuşun kayıtlarını sonradan analiz ederken, bağlamı artırır. Ama bir çıktı üretmek için geleceğe bakması gerekir; gerçek zamanlı tahminde kullanılamaz. Bu yüzden 68.16'daki akış çıkarımında yalnızca tek yönlü modeller uygundur. Çok katmanlı (stacked) RNN, bir katmanın çıktı dizisini bir sonraki katmanın girdisi yapar. Bölüm 68.8'deki çift yönlü ve iki katmanlı LSTM'in çıktı şekli (4, 20, 64) bunu gösteriyordu: son boyut iki yönün birleşimidir, ilk boyut katman ve yön sayısının çarpımıdır.

Dizi-dizi (sequence-to-sequence, seq2seq) modeli iki parçalıdır. Kodlayıcı (encoder) girdi dizisini okuyup son gizli durumu üretir; kod çözücü (decoder) bu durumdan başlayarak çıktı dizisini adım adım üretir. Çeviri bu yapının en bilinen örneğidir. Zaman serisinde aynı yapı, geçmiş bir pencereden gelecek bir pencere üretmek için kullanılır. Kodlayıcı-kod çözücü yapısında kod çözücünün her adımda bir önceki çıktısını girdi olarak alması gerekir. Eğitimde bu önceki değer iki şekilde verilebilir. Birincisi modelin kendi önceki tahmini, ikincisi gerçek (bilinen) önceki değerdir. İkincisine öğretmen zorlaması (teacher forcing) denir: model, öğretmenin verdiği doğru cevabı görerek bir sonraki adımı öğrenir.

Öğretmen zorlamasının avantajı, eğitimin kararlı olmasıdır: hata birikmez, her adımda kod çözücü doğru bir bağlamla çalışır. Dezavantajı, eğitim ile çıkarım arasında bir uyumsuzluk yaratmasıdır. Çıkarımda kod çözücü kendi tahminini kullanır ve bu tahmin hatalıysa, bir sonraki adımın girdisi de hatalı olur. Eğitimde hiç görmediği bu durum, maruz kalma (exposure bias) sorunudur. Bu sorunu çözmek için eğitim sırasında bazı adımlarda modelin kendi tahminini kullanmak (zamanlanmış örnekleme, scheduled sampling) gibi yöntemler vardır; biz bunları uygulamadık.

Aşağıdaki t13 programı küçük bir kodlayıcı-kod çözücü GRU kurar ve her biri 10 adımlık bir çıktı üretir. Üç eğitim senaryosu karşılaştırılır: öğretmen zorlamasıyla eğitim, serbest (kendi tahminiyle) eğitim ve her ikisinin test ölçümü. Test her zaman serbest çıkarımla yapılır; ayrıca öğretmen zorlamalı eğitilmiş modelin test ölçümünü bir de öğretmen zorlamayla yaparak iyimser bir sayı gösteriyoruz. Ölçekleme yalnızca eğitimden yapılır, tohum 11, 12 ve 13 kullanılır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.10: kodlayıcı-kod çözücü GRU. Öğretmen zorlaması
(teacher forcing) ile eğitilen model, çıkarımda kendi tahminini
kullanınca ne olur? Tohum 11, 12, 13; CPU."""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak import iha_telemetri, HEDEF, mae, yaz_csv

n, W, H = 24000, 32, 10
ntr, nva = int(0.6 * n), int(0.8 * n)


class Seq2Seq(nn.Module):
    def __init__(self, h=32):
        super().__init__()
        self.enc = nn.GRU(1, h, batch_first=True)
        self.dec = nn.GRUCell(1, h)
        self.cik = nn.Linear(h, 1)

    def forward(self, x, hedef=None):
        _, h = self.enc(x)
        h = h[0]
        giris = x[:, -1, :]          # son gözlenen değer
        cikti = []
        for k in range(H):
            h = self.dec(giris, h)
            yk = self.cik(h)
            cikti.append(yk)
            giris = hedef[:, k:k + 1] if hedef is not None else yk
        return torch.cat(cikti, dim=1)
```

Programın devamı aşağıdadır.

```python

def pencere(x, i_lo, i_hi):
    i = np.arange(i_lo, i_hi)
    X = x[i[:, None] + np.arange(W)][:, :, None]
    Y = x[i[:, None] + W + np.arange(H)]
    return (torch.tensor(X, dtype=torch.float32),
            torch.tensor(Y, dtype=torch.float32))


def egit(tf, tohum, epoch=15):
    torch.manual_seed(tohum)
    rng = np.random.default_rng(tohum)
    Xtr, Ytr = pencere(u, 0, ntr - W - H + 1)
    m = Seq2Seq()
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    for _ in range(epoch):
        m.train()
        sira = rng.permutation(len(Xtr))
        for b in range(0, len(sira), 128):
            j = sira[b:b + 128]
            opt.zero_grad()
            p = m(Xtr[j], Ytr[j] if tf else None)
            F.mse_loss(p, Ytr[j]).backward()
            nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step()
    return m
```

Programın devamı aşağıdadır.

```python

def olc(m, tf):
    Xte, Yte = pencere(u, nva - W, n - W - H + 1)
    m.eval()
    with torch.no_grad():
        p = m(Xte, Yte if tf else None).numpy()
    g = Yte.numpy()
    return mae(g * sd + mu, p * sd + mu)


satir = []
print("%-26s %8s %8s %8s" % ("egitim / test", "tohum11", "tohum12",
                             "tohum13"))
sonuc = {}
for tohum in (11, 12, 13):
    s = iha_telemetri(n, seed=tohum)[:, HEDEF]
    mu, sd = s[:ntr].mean(), s[:ntr].std()
    u = (s - mu) / sd
    for ad, tf, tt in [("TF egitim, serbest test", True, False),
                       ("TF egitim, TF test (iyimser)", True, True),
                       ("serbest egitim, serbest test", False,
                        False)]:
        m = egit(tf, tohum)
        a = olc(m, tt)
        sonuc.setdefault(ad, []).append(a)
        satir.append((tohum, ad, round(a, 5)))
for ad, v in sonuc.items():
    print("%-26s %8.4f %8.4f %8.4f" % (ad, *v))
yaz_csv("b68_tf.csv", ["tohum", "senaryo", "mae"], satir)
```

Çıktı üç senaryonun MAE değerlerini verir. İlk satır, öğretmen zorlamalı eğitilmiş modelin gerçek (serbest) çıkarımdaki hatasıdır; ikinci satır aynı modelin öğretmen zorlamalı ölçümü, yani iyimser sonucudur; üçüncü satır serbest eğitilmiş modelin serbest çıkarım hatasıdır.

```term
$ python t13_tf.py
egitim / test               tohum11  tohum12  tohum13
TF egitim, serbest test      0.1820   0.1836   0.1843
TF egitim, TF test (iyimser)   0.1766   0.1772   0.1769
serbest egitim, serbest test   0.1823   0.1837   0.1835
```

Üç tohumun sonuçları birbirine çok yakındır. Öğretmen zorlamayla eğitilen modelin serbest çıkarımdaki hatası (ortalama yaklaşık 0,1833 A) ile serbest eğitilen modelin hatası (yaklaşık 0,1832 A) arasındaki fark yaklaşık 0,0001 A’dır; bu veri ve bu küçük model için maruz kalma etkisi gözlemlenmedi. Buna karşılık öğretmen zorlamalı test (yaklaşık 0,1769 A) serbest çıkarımdan belirgin biçimde iyi görünüyor. Bu, eğitim ile çıkarım arasındaki farkın bir değerlendirme hatası yaratabileceğini gösterir: kod çözücüye doğru önceki değeri verip test ettiğinde, gerçek kullanımda olmayacak bir bilgi kullanmış olursun.

Bu sonuç, öğretmen zorlamanın her zaman kötü olduğu anlamına gelmez. Bu deneyde 10 adımlık ufuk kısa, model küçük ve veri düzenli bir sinüs-benzeri akımdı. Maruz kalma sorununun asıl belirgin olduğu durumlar daha uzun ufuklarda ve daha karmaşık dizilerde ortaya çıkar. Burada gösterdiğimiz kural şudur: çıkarım sonuçlarını her zaman serbest çıkarımla raporla ve öğretmen zorlamalı ölçümü yalnızca bir teşhis olarak kullan.

Bu bölümün dizi-dizi bakışı, Bölüm 69'da attention mekanizmasının asıl motivasyonudur: kod çözücü, tek bir sabit gizli durum yerine kodlayıcının tüm adım çıktılarına bakabilirse, uzun dizilerde bilgi kaybı azalır.

## 68.11 TCN: nedensel ve genişletilmiş konvolüsyon

Zaman boyutunda konvolüsyon, Bölüm 66'daki görüntü konvolüsyonunun tek boyutlu hâlidir: bir çekirdek (kernel) dizinin her konumunda aynı biçimde uygulanır. Bu yaklaşımın iki sorunu var ve TCN (temporal convolutional network) bu iki sorunu çözmek için tasarlanmıştır. Birincisi nedenselliktir: bir çıktı t anında yalnızca t ve öncesindeki girdilere bağlı olmalıdır. Gelecekteki bir girdi, eğitimde de çıkarımda da modele sızmamalıdır. İkincisi bellektir: çekirdeği büyütmeden geniş bir geçmişi görmek istersin.

Nedensellik için konvolüsyonun sol tarafına sıfır dolgu (left padding) eklenir; dolgu uzunluğu (K − 1)d'dir. Böylece çıktı uzunluğu girdi uzunluğuna eşit kalır ve her t konumu yalnızca x_{t}, x_{t−1}, ... değerlerini görür. Ortadaki bir konvolüsyon "merkez" varsayımıyla simetrik dolgu kullanırdı ve gelecekteki değerleri görürdü.

Geniş bir geçmiş için genişletme (dilation) kullanılır. Genişletilmiş konvolüsyonda çekirdek elemanları d adım arayla okunur. K = 3 ve d = 1, 2, 4, 8 gibi bir yığında her katman geçmişi üstel olarak daha geniş görür. Bir konvolüsyon katmanı kaç adım geriye bakıyorsa, o katmanın alıcı alanı odur. Bir blokta iki konvolüsyon (her biri K ve aynı d) varsa, bloğun alıcı alanına her iki konvolüsyon katkı yapar. Bu durumda toplam alıcı alan şöyledir:

RF = 1 + 2 (K − 1) Σ_b d_b.

Burada toplam, bloklar üzerinden alınır. Şekil 68.7 bu yapıyı tek konvolüsyonlu bir yığın için gösterir ve her çıktı konumunun hangi geçmiş girdilere bağlı olduğunu oklarla çizer.

![Şekil 68.7: Nedensel genişletilmiş konvolüsyon yığını (K = 3, d = 1, 2, 4, 8). Son çıktı y_t yalnızca geçmiş girdilere bağlıdır; tek konvolüsyonlu bu yığında alıcı alan 31 adımdır. Her blokta iki konvolüsyon olunca alan 61 olur.](gorseller/b68_tcn_yigin.png)

Bir TCN bloğu iki genişletilmiş nedensel konvolüsyon, aralarında ReLU ve bir artık (residual) bağlantıdan oluşur. Artık bağlantı, girdi kanal sayısı çıktıyla farklıysa 1×1 konvolüsyonla eşitlenir. Bölüm 66'daki artık blok fikri burada zamanda çalışır. Yığını derinleştirmek, alıcı alanı genişletirken eğitimi kararlı tutar.

Bu bölümün ortak.py'deki TCN sınıfında ayrıca bir önemli ayrıntı var: 1 boyutlu nedensel dolgu, konvolüsyon katmanının kendi çıktısına da uygulanır. Bu yüzden ikinci konvolüsyonun girdisi de sol dolgulu olmalıdır, yoksa bloğun çıktısı gelecekten bilgi taşır. Aşağıdaki t07 programı iki şeyi ölçer. Birincisi, gradyan ile alıcı alanın gerçek uzunluğu (formülde verilen RF'ye eşit olmalı). İkincisi, nedensellik: gelecekteki girdiyi değiştirdiğimizde geçmişteki gizli çıktılar değişmemeli. Dizi uzunluğunu 160 seçtik, çünkü 125 adımlık alıcı alanı ölçebilmek için dizinin en az o kadar uzun olması gerekir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.7: TCN'in alıcı alanı ve nedenselliği ölçülüyor."""
import torch
import torch.nn as nn
from ortak import TCN

torch.manual_seed(0)
torch.set_num_threads(4)
L = 160
for dil in [(1, 2, 4, 8), (1, 2, 4, 8, 16)]:
    net = TCN(1, kanal=8, k=3, dil=dil)
    RF = net.alici_alan()
    x = torch.randn(1, L, 1, requires_grad=True)
    y = net(x)[0, 0]                       # son adımın çıktısı
    g, = torch.autograd.grad(y, x)
    etki = g[0, :, 0].abs()
    ilk = (etki > 0).nonzero().min().item()  # en eski etkili girdi
    gecikme = L - 1 - ilk                  # en uzak etkili gecikme
    print("dilation=%s" % (dil,))
    print("  formul alici alan = 1 + 2(k-1) sum(d) = %d" % RF)
    print("  olculen en uzak etkili gecikme   = %d (RF-1 = %d)"
          % (gecikme, RF - 1))
    print("  parametre sayisi (kanal=8)       = %d"
          % sum(p.numel() for p in net.parameters()))

# Nedensellik: gelecekteki girdiyi değiştirmek geçmiş çıktıyı
# değiştirmemeli. Tüm zaman adımlarındaki gizli çıktıyı kullanırız.
net = TCN(1, kanal=8, k=3, dil=(1, 2, 4, 8)).eval()
x = torch.randn(1, L, 1)
x2 = x.clone()
x2[0, 60:, 0] += 5.0                       # t >= 60 değişti
with torch.no_grad():
    h1 = net.bloklar(x.transpose(1, 2))
    h2 = net.bloklar(x2.transpose(1, 2))
fark = (h1 - h2).abs().amax(dim=(0, 1))    # her adım için
print("nedensellik: t<60 için en büyük fark = %.2e"
      % fark[:60].max().item())
print("t>=60 için en büyük fark           = %.2e"
      % fark[60:].max().item())
print("LSTM (H=32, I=4) param = %d, TCN (kanal=32, C=4) param = %d"
```

Programın devamı aşağıdadır.

```python
      % (sum(p.numel() for p in nn.LSTM(4, 32).parameters()),
         sum(p.numel() for p in TCN(4, 32).parameters())))
```

Çıktı, formülle ölçülen alıcı alanı, nedensellik farkını ve parametre sayılarını verir.

```term
$ python t07_tcn.py
dilation=(1, 2, 4, 8)
  formul alici alan = 1 + 2(k-1) sum(d) = 61
  olculen en uzak etkili gecikme   = 60 (RF-1 = 60)
  parametre sayisi (kanal=8)       = 1457
dilation=(1, 2, 4, 8, 16)
  formul alici alan = 1 + 2(k-1) sum(d) = 125
  olculen en uzak etkili gecikme   = 124 (RF-1 = 124)
  parametre sayisi (kanal=8)       = 1857
nedensellik: t<60 için en büyük fark = 0.00e+00
t>=60 için en büyük fark           = 6.18e+00
LSTM (H=32, I=4) param = 4864, TCN (kanal=32, C=4) param = 22337
```

Ölçülen en uzak etkili gecikme, formülle eşleşti: 60 (RF = 61) ve 124 (RF = 125). Gelecek girdisi değiştirilen dizide t < 60 için geçmiş gizli çıktı farkı tam sıfırdır; bu, nedenselliğin kanıtıdır. t ≥ 60 için fark büyüktür, çünkü o adımlar değiştirilen girdiye bağlıdır. Parametre sayısı, kanal sayısının karesiyle büyür: kanal 8 için 1457, kanal 32 ve girdi kanalı 4 için 22 337. Bu, LSTM'in (H = 32, I = 4) 4864 parametresinin yaklaşık dört buçuk katıdır. TCN'in paralel olarak hesaplanabilmesi, bu parametre maliyetine karşılık gelir; hangisinin pratikte daha iyi olduğu sonraki deneylerde ölçülecek.

## 68.12 Uygulama: İHA telemetrisinde kısa vadeli tahmin

Bu bölümün ana deneyi, Bölüm 68.4'te gördüğümüz baz modellerle derin modelleri aynı veride, aynı bölmeyle karşılaştırmaktır. Veri, 24 000 örnekli (10 Hz, yaklaşık 40 dakika) sentetik İHA telemetrisidir; hedef motor akımıdır. Girdi olarak son 64 örneğin dört kanalı (irtifa, hız, yuvarlanma, akım) kullanılır. İlk %60 eğitim, sonraki %20 doğrulama, son %20 testtir. Ölçekleme yalnızca eğitimden öğrenilir. Sinir ağları için eğitim, doğrulama kaybına göre erken durdurma kullanır; test kümesi tek bir kez, en iyi modele uygulanır. Üç tohum (11, 12, 13) üç farklı telemetri gerçekleşmesi üretir.

Modeller şunlardır: RNN, LSTM ve GRU (gizli boyut 32), nedensel TCN (kanal 32, dilation 1, 2, 4, 8; alıcı alan 61, girdi penceresi 64'ten küçük olduğu için tüm çıktı görülebilir) ve baz modeller. Derin modellerin eğitim süreleri aynı makinede, diğer koşularla paralel çalışırken ölçüldü; bu nedenle süreler yalnızca kaba bir karşılaştırma verir.

Aşağıdaki t08 programı, veri üretimini, baz modelleri, sinir ağlarını ve sonuç tablosunu içerir. Sinir ağı mimarisi ve eğitim döngüsü Bölüm 68.9'da, TCN sınıfı Bölüm 68.11'de açıklandı.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.8: İHA telemetrisinde 1 adım ileri akım tahmini.
Baz modeller ve RNN/LSTM/GRU/TCN; tohum 11, 12, 13; CPU; zamana
göre bölme; ölçekleme yalnızca eğitimden; test yalnızca bir kez."""
import time
import numpy as np
import torch
from ortak import (iha_telemetri, olcek, veri_bol, HEDEF, mae, rmse,
                   naif_tahmin, hareketli_ort, ar_sec, ar_1adim,
                   Tekrarli, TCN, egit, tahmin, yaz_csv)

n, W = 24000, 64
ntr, nva = int(0.6 * n), int(0.8 * n)
te_idx = np.arange(nva, n)
satir, ornek = [], None
ozet = {}


def kaydet(tohum, ad, pred, params, sure, s_te):
    a, r = mae(s_te, pred), rmse(s_te, pred)
    satir.append((tohum, ad, round(a, 5), round(r, 5), params,
                  round(sure, 1)))
    ozet.setdefault(ad, []).append((a, r, sure))


for tohum in (11, 12, 13):
    Z = iha_telemetri(n, seed=tohum)
    s = Z[:, HEDEF]
    s_te = s[te_idx]
    # baz modeller (ham ölçekte)
    kaydet(tohum, "naif", naif_tahmin(s, te_idx), 0, 0, s_te)
    kaydet(tohum, "hareketli ort. (10)", hareketli_ort(s, te_idx),
           0, 0, s_te)
    p, kat = ar_sec(s, ntr, nva)
    kaydet(tohum, "AR(%d)" % p, ar_1adim(s, kat, te_idx), p + 1, 0,
           s_te)
    # sinir ağları (ölçekli)
    Zs, mu, sd = olcek(Z.astype(np.float32), ntr)
    (Xtr, ytr), (Xva, yva), (Xte, yte) = veri_bol(Zs, W, 1, ntr, nva)
    for ad, mk in [
```

Programın devamı aşağıdadır.

```python
        ("RNN", lambda: Tekrarli("rnn", 4, 32)),
        ("LSTM", lambda: Tekrarli("lstm", 4, 32)),
        ("GRU", lambda: Tekrarli("gru", 4, 32)),
        ("TCN", lambda: TCN(4, 32, 3, (1, 2, 4, 8)))]:
        torch.manual_seed(tohum)
        m = mk()
        t0 = time.time()
        en, ep = egit(m, Xtr, ytr, Xva, yva, seed=tohum)
        sure = time.time() - t0
        pr = tahmin(m, Xte)[:, 0] * sd[HEDEF] + mu[HEDEF]
        npar = sum(q.numel() for q in m.parameters())
        kaydet(tohum, ad, pr, npar, sure, s_te)
        print("tohum %d %-5s en iyi epoch=%2d  sure=%5.1f s  param=%d"
              % (tohum, ad, ep, sure, npar))
        if tohum == 11 and ad == "GRU":
            ornek = {"gercek": s_te[:400], "GRU": pr[:400]}
        if tohum == 11 and ad == "TCN":
            ornek["TCN"] = pr[:400]
    if tohum == 11:
        ornek["AR"] = ar_1adim(s, kat, te_idx)[:400]

print()
print("%-22s %-18s %-18s" % ("Model", "MAE ort+-sd", "RMSE ort+-sd"))
for ad, v in ozet.items():
    a = np.array([x[0] for x in v])
    r = np.array([x[1] for x in v])
    print("%-22s %6.4f+-%.4f  %6.4f+-%.4f" % (
        ad, a.mean(), a.std(ddof=1), r.mean(), r.std(ddof=1)))
yaz_csv("b68_tahmin.csv",
        ["tohum", "model", "mae", "rmse", "param", "egitim_s"], satir)
yaz_csv("b68_tahmin_ornek.csv",
        ["adim", "gercek", "GRU", "TCN", "AR"],
        [(i, round(float(ornek["gercek"][i]), 4),
          round(float(ornek["GRU"][i]), 4),
          round(float(ornek["TCN"][i]), 4),
          round(float(ornek["AR"][i]), 4)) for i in range(400)])
```

Çıktı, her tohum için her sinir ağının en iyi epoch'unu, süresini ve parametre sayısını, ardından üç tohumun ortalama ve sapma tablosunu verir.

```term
$ python t08_tahmin.py
tohum 11 RNN   en iyi epoch= 7  sure= 58.8 s  param=1249
tohum 11 LSTM  en iyi epoch=17  sure=157.3 s  param=4897
tohum 11 GRU   en iyi epoch=10  sure=166.3 s  param=3681
tohum 11 TCN   en iyi epoch= 6  sure= 62.3 s  param=22337
tohum 12 RNN   en iyi epoch=14  sure=138.1 s  param=1249
tohum 12 LSTM  en iyi epoch=14  sure=194.0 s  param=4897
tohum 12 GRU   en iyi epoch=23  sure=264.8 s  param=3681
tohum 12 TCN   en iyi epoch= 6  sure= 54.1 s  param=22337
tohum 13 RNN   en iyi epoch=13  sure= 64.4 s  param=1249
tohum 13 LSTM  en iyi epoch= 5  sure= 28.3 s  param=4897
tohum 13 GRU   en iyi epoch=28  sure=255.2 s  param=3681
tohum 13 TCN   en iyi epoch=13  sure= 82.7 s  param=22337
Model                  MAE ort+-sd        RMSE ort+-sd
naif                   0.2345+-0.0024  0.2929+-0.0032
hareketli ort. (10)    0.1819+-0.0003  0.2275+-0.0012
AR(40)                 0.1777+-0.0002  0.2221+-0.0009
RNN                    0.1789+-0.0055  0.2241+-0.0076
LSTM                   0.1746+-0.0007  0.2183+-0.0008
GRU                    0.1732+-0.0018  0.2167+-0.0030
TCN                    0.1767+-0.0016  0.2205+-0.0015
```

Tablo bu bölümün en dikkatli okunması gereken sonucudur. En iyi ortalama GRU'dur (MAE 0,1732 ± 0,0018), ardından LSTM (0,1746 ± 0,0007), TCN (0,1767 ± 0,0016), AR(40) (0,1777 ± 0,0002) ve RNN (0,1789 ± 0,0055) gelir. Dört derin modelin dördü de naif tahminden (0,2345) ve hareketli ortalamadan (0,1819) iyidir. Ama farklar küçüktür: GRU ile AR(40) arasındaki fark yaklaşık 0,0045 A'dır, yani bir amperin binde dördü kadar. Bu farkın yalnızca ortalamada görünüp görünmediğine bakmak için tohum bazında sonuçlara bakalım. AR(40), tohum 11, 12 ve 13'te sırasıyla 0,1775, 0,1779 ve 0,1779 verdi. GRU bu üçünde de daha düşüktür (0,1753, 0,1723, 0,1722); LSTM de üçünde AR(40)'ı geçer (0,1741, 0,1744, 0,1754). TCN ise tohum 12'de AR(40)'ı geçemedi (0,1786), diğer ikisinde geçti. RNN'in sonucu tohuma çok bağlıdır: tohum 11'de en kötü model (0,1852), tohum 12 ve 13'te ise AR'ye yakın (0,1753 ve 0,1760).

Bu sonuçtan çıkan dürüst cümle şudur: bu telemetri verisinde kapılı RNN'ler (LSTM ve GRU) AR(40)'ı üç tohumun üçünde de hafifçe geçiyor, ama kazanç ufak ve bir modelin tek bir tohumdaki sonucu bu kadar küçük bir farkı belirlemeye yetmez. Üç tohumla bile bu fark, sapmanın birkaç katıdır, ama nüfus düzeyinde kesin bir ispat değildir. Ayrıca gözlemlediğimiz gürültü tabanı yaklaşık 0,12 A'dır (akım gürültüsünün sapması 0,15 A'nın 0,8 katı); bu tabanın üstündeki sonuçların hepsi, modelin geçmişten çıkarabildiği kısmın küçük bir payını ölçer.

Eğitim süreleri, bu tablo için bir kıyas aracı değildir. Aynı makinede diğer işlerle paralel çalışırken ölçüldüler; GRU'nun 166 saniyeden 265 saniyeye kadar çıkması, paralel yük nedeniyledir, mimarinin gerçek maliyeti değildir. Bu süreleri Bölüm 65'teki ölçüm disiplini ile (boş makinede, tekrarlı ölçümle) yeniden almak gerekir.

![Şekil 68.8: Sol: tohum 11'de ilk 150 test adımında gerçek akım ve AR(40), GRU, TCN tahminleri. Sağ: üç tohumun test MAE ortalaması ve sapması, naif ve hareketli ortalama dahil.](gorseller/b68_tahmin.png)

Şekil 68.8'in sol panelinde modeller gerçek eğriye yakın durur; zor kısımlar, akımın yuvarlanmayla hızlı değiştiği dönemlerdedir. Sağ panelde ise sapma çubukları, farkların neden dikkatli okunması gerektiğini gösterir.

## 68.13 Çok adımlı tahmin: özyinelemeli ve doğrudan

Şimdiye kadar yalnızca bir adım ileri tahmin ettik. Pratikte genellikle birkaç adım ileriyi bilmek istersin: on adım sonra akım ne olacak? Bunun iki yolu vardır. Özyinelemeli (recursive) yöntem, bir adım modeli eğitir, sonra tahmini girdiye geri koyarak tekrar tekrar kullanır. Doğrudan (direct) yöntem, her ufuk için ayrı bir model eğitir ya da tek bir modelin on çıkışı olur. Özyinelemeli yöntemin sorunu hata birikimidir: her adımda küçük bir hata yapılır ve bu hata bir sonraki adımın girdisine dönüşür. Doğrudan yöntemin sorunu, uzun ufukta modelin her çıkış için ayrı bir öğrenme gerektirmesi ve bu tahminlerin birbiriyle tutarsız olabilmesidir.

Bu bölümde AR(40) ve GRU ile iki yöntemi de deneyeceğiz. Tohum 11 kullanılır. Test orijinleri, test kümesindeki her uygun pencere başlangıcıdır ve her orijinden ufka kadar gerçek değerlerle karşılaştırılır. Tek adımlı GRU özyinelemeli yöntemde kullanılır; on çıkışlı GRU doğrudan yöntemde kullanılır. Her iki GRU da tek kanallı (yalnızca akım) girdiyle çalışır, çünkü özyinelemeli çıkarımda her adımda yalnızca akımı tahmin ediyoruz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.13: çok adımlı tahmin. Özyinelemeli (recursive) ile
doğrudan (direct) yöntemler. Hata ufka göre artar mı? Tohum 11."""
import numpy as np
import torch
from ortak import (iha_telemetri, HEDEF, mae, Tekrarli, egit, tahmin,
                   yaz_csv)

n, W, HMAX, P = 24000, 64, 10, 40
ntr, nva = int(0.6 * n), int(0.8 * n)
s = iha_telemetri(n, seed=11)[:, HEDEF]
mu, sd = s[:ntr].mean(), s[:ntr].std()
u = (s - mu) / sd


def uni(x, W, H):
    """Tek kanallı pencereler: X_i = x[i:i+W], Y_i = x[i+W:i+W+H]."""
    m = len(x) - W - H + 1
    X = x[np.arange(W)[None, :] + np.arange(m)[:, None]]
    Y = x[np.arange(H)[None, :] + np.arange(m)[:, None] + W]
    return X[:, :, None].astype(np.float32), Y.astype(np.float32)


# Test orijinleri: i = nva-W .. n-W-HMAX (son bilinen indeks = i+W-1)
i_te = np.arange(nva - W, n - W - HMAX + 1)
o_te = i_te + W - 1                      # son bilinen indeks
gercek = np.stack([s[o_te + k] for k in range(1, HMAX + 1)], axis=1)
```

Programın devamı aşağıdadır.

```python
# ---- AR(40) ----
def ar_ozellik(o, p):
    return np.column_stack([np.ones(len(o))]
                           + [s[o - j] for j in range(p)])

ar_rec = np.zeros((len(o_te), HMAX))
kat1 = np.linalg.lstsq(ar_ozellik(np.arange(P - 1, ntr - 1), P),
                       s[P:ntr], rcond=None)[0]
hist = np.column_stack([s[o_te - j] for j in range(P)])   # yeni->eski
for k in range(HMAX):
    A = np.column_stack([np.ones(len(hist))]
                        + [hist[:, j] for j in range(P)])
    pr = A @ kat1
    ar_rec[:, k] = pr
    hist = np.column_stack([pr, hist[:, :-1]])
ar_dir = np.zeros_like(ar_rec)
for k in range(1, HMAX + 1):
    o_tr = np.arange(P - 1, ntr - k)
    A = ar_ozellik(o_tr, P)
    kat = np.linalg.lstsq(A, s[o_tr + k], rcond=None)[0]
    ar_dir[:, k - 1] = ar_ozellik(o_te, P) @ kat

# ---- GRU: özyinelemeli (H=1) ve doğrudan (H=10) ----
def gru_egit(H):
    X, Y = uni(u, W, H)
    tr = np.arange(len(X)) + W < ntr
    hb = np.arange(len(X)) + W
    va = (hb >= ntr) & (hb < nva)
    torch.manual_seed(11)
    m = Tekrarli("gru", 1, 32, cikis=H)
    egit(m, X[tr], Y[tr], X[va], Y[va], seed=11)
    return m
```

Programın devamı aşağıdadır.

```python
m1 = gru_egit(1)
Xte, _ = uni(u, W, HMAX)
Xte = Xte[i_te]
cur = torch.tensor(Xte.copy())
gru_rec = np.zeros((len(i_te), HMAX))
with torch.no_grad():
    m1.eval()
    for k in range(HMAX):
        p = m1(cur)[:, 0]
        gru_rec[:, k] = p.numpy() * sd + mu
        cur = torch.cat([cur[:, 1:], p.view(-1, 1, 1)], dim=1)

mD = gru_egit(HMAX)
gru_dir = tahmin(mD, Xte) * sd + mu

print("%-3s %-9s %-9s %-9s %-9s" % ("k", "AR-rec", "AR-dir",
                                    "GRU-rec", "GRU-dir"))
satir = []
for k in range(1, HMAX + 1):
    r = [mae(gercek[:, k - 1], v[:, k - 1])
         for v in (ar_rec, ar_dir, gru_rec, gru_dir)]
    print("%-3d %-9.4f %-9.4f %-9.4f %-9.4f" % (k, *r))
    satir.append((k, *[round(x, 5) for x in r]))
yaz_csv("b68_cok_adim.csv", ["k", "ar_rec", "ar_dir", "gru_rec",
                              "gru_dir"], satir)
```

Çıktı, ufka göre MAE değerlerini verir. Her sütun bir yöntem, her satır bir ufuktur.

```term
$ python t09_cok_adim.py
k   AR-rec    AR-dir    GRU-rec   GRU-dir
1   0.1776    0.1776    0.1760    0.1744
2   0.1792    0.1794    0.1772    0.1755
3   0.1807    0.1807    0.1782    0.1760
4   0.1822    0.1822    0.1793    0.1766
5   0.1834    0.1833    0.1801    0.1780
6   0.1844    0.1843    0.1807    0.1775
7   0.1860    0.1857    0.1819    0.1788
8   0.1881    0.1876    0.1834    0.1787
9   0.1914    0.1904    0.1855    0.1809
10  0.1934    0.1925    0.1868    0.1807
```

Tablodan üç sonuç çıkar. Birincisi, kısa ufukta (k = 1) yöntemler neredeyse aynıdır: AR özyinelemeli 0,1776, GRU özyinelemeli 0,1760. İkincisi, hata ufukla birlikte artar ama artış her yöntemde aynı hızda değildir: AR özyinelemeli k = 1'den k = 10'a 0,1776'dan 0,1934'e çıkar (yaklaşık yüzde 9); GRU doğrudan ise 0,1744'ten 0,1807'ye (yaklaşık yüzde 4) çıkar. Üçüncüsü, uzun ufukta GRU doğrudan en iyi yöntemdir (k = 10'da 0,1807), GRU özyinelemeli ikinci (0,1868) ve AR yöntemleri en kötüdür. Yani bu veride, özyinelemeli yöntemin hata birikimi, doğrudan yöntemin tutarlılık avantajından daha ağır basar.

![Şekil 68.9: Ufka göre test MAE'si: AR ve GRU, özyinelemeli ve doğrudan yöntem. Hata ufukla birlikte artar; GRU doğrudan en yavaş artan eğridir.](gorseller/b68_cok_adim.png)

Şekil 68.9, bu farkları görsel olarak verir. Dikkat edilecek nokta, AR'nin iki yönteminin neredeyse üst üste binmesidir: doğrusal modelde özyinelemeli ve doğrudan yöntem, teoride aynı ufuk için aynı tahmini verir (doğrusal bir AR için iki yöntemin farkı yalnızca eğitim koşullarındadır). GRU'da ise iki yöntem ayrılır, çünkü özyinelemeli yöntem doğrusal olmayan bir modelin kendi çıktısını girdi olarak almasını gerektirir. Bu, "hata birikimi" kavramının doğrusal olmayan modellerde daha belirgin olduğunu gösterir.

Pratik çıkarım şudur: uzun ufuklu tahminde doğrudan yöntem, en azından bu veride, özyinelemeli yöntemden daha tutarlıdır; ama her ufuk için ayrı bir çıkış gerekir ve bu çıkışların birbiriyle tutarsız olabileceğini (örneğin k = 3 ve k = 4 arasında kesik bir sıçrama) ayrıca kontrol etmelisin. Özyinelemeli yöntem daha az parametreyle çalışır ve her ufku aynı modelle üretir; bu, bellek kısıtlı bir cihazda avantajdır.

## 68.14 Anomali tespiti: tahmin artığı ile arıza yakalamak

Bölüm 61'de anomali tespitini, verinin normal yapısından sapmayı bulmak olarak tanımlamıştık. Zaman serisinde bu sapmayı bulmanın doğal yolu, bir modelin tahminini gerçek değerle karşılaştırıp artığa (residual) bakmaktır. Normal veride artık küçük ve tahmin edilemez, arıza sırasında büyük ya da sistematik olur. Eşik, yalnızca anomalisiz verinin artık dağılımından seçilir; test kümesi eşik için kullanılmaz. Bu bölümde iki tür arıza enjekte ediyoruz: test kümesinde beş tekil akım sıçraması (+3 A) ve 700 örnek süren bir rulman kayması (0'dan 1,5 A'ya doğrusal artış, sonra sabit).

Burada önemli bir ayrım var. Zamansal artık, geçmiş gözlenen akımdan bir sonraki değeri tahmin eder. Bu tür bir model, yavaş değişen bir kaymayı kendi geçmişinin bir parçası olarak öğrenir ve artığı sıfıra yakın tutar. Bu yüzden kaymayı kaçırır. Bağlamsal artık ise aynı andaki diğer kanallardan (hız ve |yuvarlanma|) akımı tahmin eder. Akımın bu kanallarla ilişkisi, bizim sentetik veri üretiminde doğrusal bir fizikle tanımlandığı için, kaymayı görünür kılar. Bu bağlam, gerçek bir İHA'da da geçerlidir: motor akımı, hız ve yük ilişkisiyle bağlıdır; bir rulman bozulması bu ilişkiyi kırar. Yine de bu, sentetik veride tanımlanmış bir ilişkidir ve gerçek veride doğrulanması gerekir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.10: tahmin artığına dayalı anomali tespiti.
Eşikler YALNIZCA anomalisiz eğitim/doğrulama artıklarından; test'te
arızalar (5 sıçrama + kayma) enjekte edilmiş; tohum 11; CPU."""
import numpy as np
from ortak import (iha_telemetri, ariza_ekle, HEDEF, ar_egit,
                   ar_1adim, yaz_csv)

n = 24000
ntr, nva = int(0.6 * n), int(0.8 * n)
Z = iha_telemetri(n, seed=11)
Zf, etiket = ariza_ekle(Z, nva, n, seed=5)
s = Zf[:, HEDEF]                          # gözlenen (arızalı) akım
rng = np.random.default_rng(5)          # ariza_ekle ile aynı çekiliş
sicrama = rng.choice(np.arange(nva, n - 10), size=5, replace=False)
sm = np.zeros(n, bool)
sm[sicrama] = True
km = (etiket == 1) & ~sm                  # kayma örnekleri
va, te = np.arange(ntr, nva), np.arange(nva, n)
Q, K = 0.9995, 20


def hareketli(r, k=K):
    cs = np.concatenate([[0.0], np.cumsum(r)])
    out = np.full(len(r), np.nan)
    out[k - 1:] = (cs[k:] - cs[:-k]) / k
    return out
```

Programın devamı aşağıdadır.

```python

# Zamansal artık: AR(p), tahmin geçmiş GÖZLENEN akımdan
def zamansal(p):
    kat = ar_egit(Z[:, HEDEF], ntr, p)
    r = np.full(n, np.nan)
    idx = np.arange(p, n)
    r[idx] = s[idx] - ar_1adim(s, kat, idx)
    return r

# Bağlamsal artık: akım, aynı andaki hız ve |yuvarlanma| ile tahmin
def baglamsal():
    A = np.column_stack([np.ones(n), Z[:, 1], np.abs(Z[:, 2])])
    kat, *_ = np.linalg.lstsq(A[:ntr], Z[:ntr, HEDEF], rcond=None)
    return s - A @ kat, kat


def degerlendir(ad, r):
    nan = np.isnan(r)
    e = np.quantile(np.abs(r[va][~np.isnan(r[va])]), Q)
    al = (np.abs(r) > e)[te] & ~nan[te]
    y = etiket[te].astype(bool)
    tp, fp = np.sum(al & y), np.sum(al & ~y)
    rs = np.sum(al & sm[te]) / sm[te].sum()
    rk = np.sum(al & km[te]) / km[te].sum()
    print("%-26s %6.3f %6.3f %7.3f %8.2f %6.2f %8.1f"
          % (ad, e, tp / max(al.sum(), 1), tp / y.sum(), rs, rk,
             fp / (~y).sum() * 36000))
    return np.abs(r), e
```

Programın devamı aşağıdadır.

```python

print("%-26s %6s %6s %7s %8s %6s %8s" % (
    "Detektör", "esik", "prec", "recall", "sicrama", "kayma",
    "FAR/s"))
kayit = {}
for ad, r in [("zamansal AR(5)", zamansal(5)),
              ("zamansal AR(40)", zamansal(40))]:
    kayit[ad] = degerlendir(ad, r)
rb, kat = baglamsal()
kayit["bağlamsal"] = degerlendir("bağlamsal (v, |yuv|)", rb)
mb = hareketli(np.nan_to_num(rb))
kayit["bağlamsal MA20"] = degerlendir("bağlamsal + MA20", mb)
print("bağlamsal katsayılar (sabit, v, |yuv|):", np.round(kat, 4))

yaz_csv("b68_anomali.csv",
        ["t", "etiket", "zaman_ar40", "baglam", "baglam_ma20"],
        [(t, int(etiket[t]),
          round(float(kayit["zamansal AR(40)"][0][t]), 4),
          round(float(kayit["bağlamsal"][0][t]), 4),
          round(float(kayit["bağlamsal MA20"][0][t]), 4))
         for t in te])
yaz_csv("b68_anomali_esik.csv", ["detektor", "esik"],
        [(ad, round(float(kayit[ad][1]), 4))
         for ad in ("zamansal AR(40)", "bağlamsal",
                    "bağlamsal MA20")])
```

Çıktı, her dedektör için eşiği, kesinliği (precision), duyarlılığı (recall), sıçrama ve kayma için ayrı duyarlılığı ve saatte yanlış alarm sayısını verir. Test kümesinde 4095 normal ve 705 etiketli örnek vardır.

```term
$ python t10_anomali.py
Detektör                     esik   prec  recall  sicrama  kayma    FAR/s
zamansal AR(5)              0.751  0.222   0.009     1.00   0.00    184.6
zamansal AR(40)             0.725  0.368   0.010     1.00   0.00    105.5
bağlamsal (v, |yuv|)        0.483  0.980   0.817     1.00   0.82    105.5
bağlamsal + MA20            0.125  0.862   0.929     1.00   0.93    923.1
bağlamsal katsayılar (sabit, v, |yuv|): [5.9753 0.3514 0.0502]
```

Sonuçlar üç şey söyler. Birincisi, zamansal AR(40) yalnızca sıçramaları yakalar (sıçrama duyarlılığı 1,00) ama kaymayı hiç yakalamaz (0,00). Kesinlik de düşüktür (0,368). İkincisi, bağlamsal artık kaymanın %82'sini yakalar, sıçramaların hepsini de yakalar ve kesinliği 0,980'dir. Üçüncüsü, MA20 (20 örnek üzerinden ortalama artık) kaymayı %93 yakalar ama yanlış alarm oranı saatte 923'e çıkar. Bunun nedeni şudur: bir sıçrama, ortalama artığı 20 örnek boyunca yükseltir, ve bu sürenin tamamında normal örnekler alarm verir. Yani MA20 kuralı, sıçrama sonrası bir alarm kuyruğu üretir.

Bu tablo, eşik seçiminin bir değerlendirme sorusu olduğunu da gösterir. Bağlamsal artık ile zamansal AR(40) aynı yanlış alarm sayısına (saatte 105,5, yani 4095 normal örnekte 12 alarm) sahiptir. Bunu tesadüf sanabilirsin; ama bu sadece bu sayının eşitliğidir, iki dedektörün yanlış alarm yerleri farklıdır. Asıl ayrım kayma duyarlılığındadır. Eşik seçiminde test kümesine bakılmadığını da hatırlat: eşikler yalnızca doğrulama artıklarından (yüzdelik 0,9995) geldi.

Şekil 68.10 bağlamsal artığın davranışını gösterir: üst panel, kayma başlamadan önce artığın eşiğin altında kaldığını, kayma sırasında yükseldiğini ve sıçramaların tek nokta olarak göründüğünü gösterir. Alt panel MA20'nin sıçrama sonrası kuyruğunu gösterir.

![Şekil 68.10: Üst: bağlamsal artığın mutlak değeri (test, 21000–23000), eşik ve enjekte kayma bölgesi. Alt: MA20 ortalaması; kayma bölgesinde yükselir, sıçramalar 20 örnek boyunca kuyruk bırakır.](gorseller/b68_anomali.png)

Son bir uyarı: eşik, doğrulama artıklarından seçildiği için bu sonuçlar, gerçek bir sistemde beklenen yanlış alarm oranına yakın bir tahmin verir; ama sentetik verinin gürültü dağılımı Gauss'a yakındır. Gerçek sensör verisinde kuyruklar daha ağır olabilir ve eşik buna göre yeniden seçilmelidir.

## 68.15 Batarya hücresi: sağlıklı ve bozulmuş sınıflandırması

Bu son uygulama, Mert'in EV Dashboard projesinde karşılaşılabilecek bir problemi, batarya hücresinin gerilim serisinden sağlık sınıflandırmasını, kavramsal olarak ele alır. Projeye yalnızca kavramsal atıf yapıyoruz; o depoya dokunmuyoruz ve veri de sentetiktir. Her hücre, dakikada bir örnek (dt = 1 s), 3000 örnek üretir. Gerilim, açık devre gerilimi (SOC'ye bağlı) eksi akım çarpı iç direnç ve gürültüdür; sıcaklık, akımın karesiyle iç direnç çarpımına bağlı bir ısınma içerir. Sağlıklı hücrede iç direnç 0,018–0,024 Ω, bozulmuşta 0,030–0,036 Ω aralığındadır. Hücrenin kapasitesi ve başlangıç SOC'si hücreye özgüdür; bu, bir hücrenin "kimliğini" gerilim serisinden çıkarabilmek anlamına gelir.

Bu, Bölüm 68.3'teki sızıntı dersinin doğrudan bir uygulamasıdır. Pencereler arasında komşuluk olduğu için rastgele pencere bölmesi, aynı hücrenin pencerelerini hem eğitime hem teste koyar; model hücrenin kimliğini ezberleyerek iyi görünür. Gerçek genelleme, hücre düzeyinde bölme ile ölçülür: test hücreleri eğitimde hiç görülmemiştir. Bu nedenle deney iki bölme kullanır: grup (hücre) bölmesi ve rastgele pencere bölmesi. Üç tohum kullanılır; her tohumda 60 hücre üretilir (30 sağlıklı, 30 bozulmuş). Grup bölmesinde sınıf içinde 21 hücre eğitim, 4 hücre doğrulama, 5 hücre test kümesine ayrılır (her sınıf için). Girdi, 60 örneklik pencere ve üç kanaldır (gerilim, akım, sıcaklık). Ayrıca hiç öğrenme gerektirmeyen bir fiziksel yöntem vardır: pencere içinde gerilimin akıma göre regresyon eğiminden iç direnç tahmin edilir ve bir eşikle sınıflandırılır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.10 (uygulama): sentetik batarya hücresi gerilim serisinde
sağlıklı/bozulmuş sınıflandırması. Grup (hücre) bölmesi ile rastgele
pencere bölmesi karşılaştırılır. Tohum 11, 12, 13; CPU."""
import numpy as np
from ortak import Tekrarli, egit, tahmin, yaz_csv

W, ADIM, N_HUCRE = 60, 20, 60


def hucre(rng, bozuk):
    """Dakikada 1 örnek (dt=1 s). Gerilim = OCV(SOC) - I*R + gürültü.
    Bozulmuş hücrede iç direnç R daha büyüktür."""
    n = 3000
    Q = rng.uniform(2.8, 3.2)           # kapasite (Ah), hücreye özgü
    soc = rng.uniform(0.85, 0.95)
    R = (rng.uniform(0.030, 0.036) if bozuk
         else rng.uniform(0.018, 0.024))
    Tamb = rng.uniform(23, 27)
    mu_c = rng.uniform(-0.5, 1.0)          # ortalama akım (A)
    ar = 0.0
    V, I, T = np.zeros(n), np.zeros(n), np.zeros(n)
    for t in range(n):
        ar = 0.95 * ar + rng.normal(0, 0.6)
        I[t] = np.clip(mu_c + ar, -4, 8)
        V[t] = 3.0 + 1.2 * soc - I[t] * R + rng.normal(0, 0.005)
        T[t] = Tamb + 0.8 * I[t] ** 2 * R + rng.normal(0, 0.05)
        soc = np.clip(soc - I[t] / (3600 * Q), 0.0, 1.0)
    return np.column_stack([V, I, T]), bozuk
```

Programın devamı aşağıdadır.

```python

def pencereler(seriler):
    X, y, g = [], [], []
    for cid, (Z, b) in enumerate(seriler):
        for i in range(0, len(Z) - W + 1, ADIM):
            X.append(Z[i:i + W]); y.append(int(b)); g.append(cid)
    return (np.array(X, np.float32), np.array(y, np.float32),
            np.array(g))


def fiziksel_r(X):
    """Her pencerede V'yi I'ya regrese et; eğim = -R tahmini."""
    out = []
    for w in X:
        A = np.column_stack([np.ones(W), w[:, 1]])
        kat, *_ = np.linalg.lstsq(A, w[:, 0], rcond=None)
        out.append(-kat[1])
    return np.array(out)


def calistir(tohum):
    rng = np.random.default_rng(tohum)
    seriler = [hucre(rng, k >= N_HUCRE // 2) for k in range(N_HUCRE)]
    # grup bölmesi: sınıf içinde hücre tabanlı 70/15/15
    rs = np.random.default_rng(tohum + 1)
    sag = [k for k in range(N_HUCRE // 2)]
    bz = [k for k in range(N_HUCRE // 2, N_HUCRE)]
    rs.shuffle(sag); rs.shuffle(bz)
    grp = {"tr": sag[:21] + bz[:21], "va": sag[21:25] + bz[21:25],
           "te": sag[25:] + bz[25:]}
    Xa, ya, ga = pencereler(seriler)
    res = {}
    # 1) grup bölmesi
    tr = np.isin(ga, grp["tr"]); va = np.isin(ga, grp["va"])
    te = np.isin(ga, grp["te"])
    res["grup"] = deney(Xa, ya, tr, va, te, tohum)
    # 2) rastgele pencere bölmesi (aynı hücreler her yerde)
    perm = rs.permutation(len(Xa))
    k1, k2 = int(0.7 * len(Xa)), int(0.85 * len(Xa))
    tr2 = np.zeros(len(Xa), bool); tr2[perm[:k1]] = True
```

Programın devamı aşağıdadır.

```python
    va2 = np.zeros(len(Xa), bool); va2[perm[k1:k2]] = True
    te2 = np.zeros(len(Xa), bool); te2[perm[k2:]] = True
    res["rastgele"] = deney(Xa, ya, tr2, va2, te2, tohum)
    # 3) fiziksel özellik: eğim tabanlı eşik (eğitimde seçilir)
    r = fiziksel_r(Xa)
    esikler = np.linspace(0.02, 0.04, 201)
    acc = [np.mean((r[tr] > e) == ya[tr]) for e in esikler]
    e = esikler[int(np.argmax(acc))]
    res["fiziksel R eşiği (grup)"] = (np.mean((r[te] > e) == ya[te]))
    return res


def deney(X, y, tr, va, te, tohum):
    flat = X[tr].reshape(-1, 3)
    mu, sd = flat.mean(0), flat.std(0)
    Xs = (X - mu) / sd
    m = Tekrarli("gru", 3, 32, cikis=1)
    egit(m, Xs[tr], y[tr][:, None], Xs[va], y[va][:, None],
         epoch=30, seed=tohum)
    p = (tahmin(m, Xs[te])[:, 0] > 0.5).astype(int)
    return np.mean(p == y[te])


satir = []
print("%-24s %8s %8s %8s"
      % ("yöntem", "tohum11", "tohum12", "tohum13"))
sonuclar = {}
for tohum in (11, 12, 13):
    for ad, a in calistir(tohum).items():
        sonuclar.setdefault(ad, []).append(a)
        satir.append((tohum, ad, round(float(a), 4)))
for ad, v in sonuclar.items():
    print("%-24s %8.3f %8.3f %8.3f   ort=%.3f" % (ad, *v, np.mean(v)))
yaz_csv("b68_batarya.csv", ["tohum", "yontem", "test_dogruluk"],
         satir)
```

Çıktı, üç yöntemin tohum bazında test doğruluğunu ve ortalamasını verir.

```term
$ python t11_batarya.py
yöntem                    tohum11  tohum12  tohum13
grup                        0.980    0.429    0.997   ort=0.802
rastgele                    0.986    0.992    0.992   ort=0.990
fiziksel R eşiği (grup)     0.998    0.995    0.997   ort=0.997
```

Sonuçların ana cümlesi şudur: fiziksel yöntem, yani gerilim-akım eğimi, üç tohumda da %99,5 ve üzeri doğru sınıflandırır (ortalama 0,997) ve grup bölmesinde hiçbir öğrenme gerektirmez. GRU, grup bölmesinde tohum 11 ve 13'te %98 ve %99,7 doğruluk verirken, tohum 12'de yalnızca %42,9 verdi. Rastgele pencere bölmesinde ise GRU %98,6 ve üzeri doğruluk verir, çünkü hücre kimliğini ezberlemiştir. Yani rastgele bölmenin yüksek doğruluğu bir öğrenme başarısı değil, bir sızıntı ürünüdür; grup bölmesi bu sızıntıyı kaldırdığında tohum 12'de model genelleyemedi.

Tohum 12'deki çöküşün nedenini bu deneyde incelemedik. Olası nedenler arasında, 10 test hücresinin dağılımının eğitimden farklı olması, GRU'nun 30 epoch'ta yetersiz kalması ya da bir eşik kayması vardır; ama hiçbirini ölçmedik, bu yüzden bunları iddia olarak değil, incelenmesi gereken sorular olarak yazıyoruz.

Bu deneyin tekrarlanabilirliği ile ilgili bir ders de var. Tohum 11 için ilk koşuda GRU grup bölmesinde 0,970 vermişti; aynı kodla tekrar koşulduğunda 0,980 çıktı. Kodda tohum sabit olduğu hâlde sonuç değişti. Bunun en olası nedeni, PyTorch'un çok iş parçacıklı CPU işlemlerinde kayan nokta toplama sırasının koşudan koşuya değişebilmesidir (genel bilgi). Bu tür küçük farklar, bir eşiğin ya da bir karar sınırının etrafında ayrı bir sonuç üretebilir. Bundan sonraki koşularda betiğin başında torch.set_num_threads(1) ve torch.use_deterministic_algorithms(True) kullanmak, sonuçları birebir tekrarlanabilir kılar; bunun tam anlamı ve sınırları için Bölüm 65'in tekrarlanabilirlik bölümüne bak. Bu bölümdeki diğer sonuçlar, bu tekrar farkının büyüklüğü içinde değerlendirilmelidir: tahmin tablosundaki 0,0045 A'lık fark, bu makinede gözlenen tekrar farklarının (batarya için 0,01) yanında küçük kalır.

## 68.16 Akış (streaming) ve gömülü çıkarım

Gerçek zamanlı bir sistemde model, her yeni örnekte bir çıktı üretmelidir. Bu, eğitim sırasındaki toplu (batch) hesaptan farklı bir gereksinimdir. Bir RNN için bu çok doğal bir şekilde yapılır: gizli durumu bir sonraki çağrıya taşırsın. Bir TCN için ise alıcı alanı kadar bir tampon tutmak gerekir; her yeni örnekte tamponu kaydırır ve tüm ağı tamponun üzerinde bir kez çalıştırırsın. Burada iki soru vardır: çıktılar toplu hesapla aynı mı, ve adım başına süre ve bellek ne kadar? Aşağıdaki t12 programı, GRU ve TCN için eşleşmeyi ve süreyi ölçer; ayrıca LSTM'i ve parametre/bellek hesabını verir. Ağırlıklar rastgele başlatılmıştır; eşleşme bir eğitim sonucuna bağlı değildir.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68.11: akış (streaming) çıkarımı. (1) Durumlu GRU ve TCN
tamponu toplu (batch) sonuçla eşleşiyor mu? (2) Adım başına gecikme
ve bellek; ölçüm bu makinede, CPU'da yapılır."""
import time
import numpy as np
import torch
import torch.nn as nn
from ortak import TCN

torch.set_num_threads(4)
torch.manual_seed(0)
T, C = 300, 4
x = torch.randn(1, T, C)

# (1a) GRU: toplu ve adım adım (gizli durum taşınarak)
gru = nn.GRU(C, 16, batch_first=True).eval()
with torch.no_grad():
    toplu, _ = gru(x)
    h = torch.zeros(1, 1, 16)
    adim = []
    for t in range(T):
        y, h = gru(x[:, t:t + 1], h)
        adim.append(y[:, 0])
    adim = torch.stack(adim, dim=1)
print("GRU  toplu ve adim farki = %.2e" % (toplu - adim).abs().max())
```

Programın devamı aşağıdadır.

```python
# (1b) TCN: son RF örneklik kaydırmalı tampon; baş kısmı sıfır
tcn = TCN(C, 32, 3, (1, 2, 4, 8)).eval()
RF = tcn.alici_alan()
with torch.no_grad():
    tam = tcn.bloklar(x.transpose(1, 2)).transpose(1, 2)
    tampon = torch.zeros(1, RF, C)
    fark = []
    for t in range(T):
        tampon = torch.cat([tampon[:, 1:], x[:, t:t + 1]], dim=1)
        y = tcn.bloklar(tampon.transpose(1, 2))[:, :, -1]
        fark.append((y - tam[:, t]).abs().max().item())
fark = torch.tensor(fark)
print("TCN  t<%d en buyuk fark   = %.2e"
      % (RF - 1, fark[:RF - 1].max()))
print("TCN  t>=%d en buyuk fark  = %.2e  (RF=%d)"
      % (RF - 1, fark[RF - 1:].max(), RF))

# (2) Gecikme: adım başına ortanca süre (mikro saniye)
def olc(fn, adim_say=2000, tekrar=5):
    sonuc = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        for _ in range(adim_say):
            fn()
        sonuc.append((time.perf_counter() - t0) / adim_say)
    return np.median(sonuc) * 1e6
```

Programın devamı aşağıdadır.

```python
xt = torch.randn(1, 1, C)
hh = torch.zeros(1, 1, 16)
gru32 = nn.GRU(C, 32, batch_first=True).eval()
hh32 = torch.zeros(1, 1, 32)
lstm = nn.LSTM(C, 32, batch_first=True).eval()
lh = (torch.zeros(1, 1, 32), torch.zeros(1, 1, 32))
buf = torch.zeros(1, RF, C)
with torch.no_grad():
    g16 = olc(lambda: gru(xt, hh))
    g32 = olc(lambda: gru32(xt, hh32))
    l32 = olc(lambda: lstm(xt, lh))
    t_adim = olc(lambda: tcn.bloklar(
        torch.cat([buf[:, 1:], xt], dim=1).transpose(1, 2)), 500)
print("adim basi sure (us, medyan):")
print("  GRU  H=16 : %7.1f" % g16)
print("  GRU  H=32 : %7.1f" % g32)
print("  LSTM H=32 : %7.1f" % l32)
print("  TCN  tampon(RF=%d): %7.1f" % (RF, t_adim))

# (3) Bellek: parametre ve float32/int8 boyutu
def say(m):
    return sum(q.numel() for q in m.parameters())
gru16 = nn.GRU(C, 16)
print("GRU(I=4,H=16) parametre = %d; float32=%d B, int8~%d B"
      % (say(gru16), 4 * say(gru16), say(gru16)))
print("TCN tampon bellegi (RF x C float32) = %d B" % (RF * C * 4))
```

Çıktı, GRU'nun toplu ve adım adım sonuç farkını, TCN'in tampon farkını, her model için adım başına medyan süreyi ve bellek boyutlarını verir.

```term
$ python t12_akis.py
GRU  toplu ve adim farki = 8.94e-08
TCN  t<60 en buyuk fark   = 1.87e-01
TCN  t>=60 en buyuk fark  = 0.00e+00  (RF=61)
adim basi sure (us, medyan):
  GRU  H=16 :   105.5
  GRU  H=32 :   106.7
  LSTM H=32 :   207.9
  TCN  tampon(RF=61):  1716.7
GRU(I=4,H=16) parametre = 1056; float32=4224 B, int8~1056 B
TCN tampon bellegi (RF x C float32) = 976 B
```

GRU'nun adım adım sonucu toplu sonuçla 9·10⁻⁸ farkla eşleşir; bu, float32 yuvarlamasının beklenen büyüklüğüdür. TCN için tampon yönteminde, ilk 60 adımda fark 0,19'dur. Nedeni şudur: tam modelde ara çıktılar, başlangıçtaki sıfır dolgu ile hesaplanır; tampon ise başlangıçta sıfır dolu bir girdi tutar ve bu girdiden ara katmanların bias'ı ile sıfırdan farklı değerler üretir. Yani tampon, dizinin başında tam modelle aynı ara durumu taşımaz. Alıcı alanı kadar örnek geçtikten sonra (t ≥ 60) fark tam sıfırdır. Akış TCN'i kullanacaksan bu kısa başlangıç dönemini ya da ara katmanların durumunu açıkça yönetmelisin: ya ilk 60 çıktıyı atarsın, ya da her katmanın durumunu ayrı bir tamponda tutarsın.

Süreler, bu makinede CPU üzerinde adım başına (tek örnek) medyan değerlerdir: GRU (H = 16) yaklaşık 106 µs, GRU (H = 32) 107 µs, LSTM (H = 32) 208 µs, TCN tamponu (alıcı alanı 61) 1717 µs. Bu sayılar makineye ve o anki yüke bağlıdır; ama sıralama açıktır: tamponlu TCN, her adımda tüm alıcı alanını yeniden hesapladığı için adım başına belirgin biçimde daha pahalıdır. Gömülü bir cihazda bu fark daha da önemlidir. Bölüm 46'da TinyML'in bellek bütçesini gördün: GRU (I = 4, H = 16) 1056 parametre taşır, float32 ile 4224 bayt, int8 ile yaklaşık 1056 bayt. Bu, bir mikrodenetleyicinin RAM'inde rahatça yer kaplar. TCN tamponu ise yalnızca 976 bayttır (61 × 4 × 4), ama TCN'in ağırlıkları bunun çok üstündedir.

## 68.17 Sınırlar ve Transformer'a geçiş

Bu bölümde gördüğümüz dizi modelleri üç sınırla karşılaşır. Birincisi, paralellik sınırıdır. RNN'de her adım bir öncekinin gizli durumunu bekler; eğitimde zaman boyutu paralel hesaplanamaz. Bu, GPU'nun büyük bir bölümünü boşta bırakır ve uzun dizilerde eğitimi yavaşlatır. TCN bu sınırı aşar, çünkü konvolüsyonlar zaman boyunca paralel çalışır; ama alıcı alanı yalnızca katman sayısı ve genişlemeyle büyüdüğü için, çok uzun bağlamlar için derin bir yığın gerekir.

İkincisi, bağlam sınırıdır. Gizli durum, tüm geçmişi sabit boyutlu bir vektöre sıkıştırır. Bölüm 68.5'teki gizli durum fikri burada bir darboğaz olur: uzun bir dizinin tüm bilgisi tek bir vektörde taşınmak zorundadır. LSTM ve GRU kapılarla bunu hafifletir, ama sınırı kaldırmaz; Bölüm 68.13'teki uzun ufuk tablosu, kapılı modellerin bile uzun ufukta hatayı yavaş da olsa biriktirdiğini gösterir.

Üçüncüsü, bilgiye erişim sınırıdır. Bir çıktı, geçmişteki belirli bir olaya doğrudan erişemez; bilgi adım adım taşınmak zorundadır. Dikkat (attention) mekanizması bu sınırı doğrudan aşar: her çıktı, girdinin her konumuna bir ağırlıkla bakabilir. Bölüm 69'da bu mekanizmayı sıfırdan kuracağız, konumsal kodlama ve maskeleme dahil. Dikkatli bir okur şunu fark etmiş olmalı: dikkat, Bölüm 68.11'deki nedensellik fikrini korumak için maskeleme kullanır; yani gelecek konumlara bakılmasın diye bir üst-üçgen maske uygulanır, tıpkı TCN'deki sol dolgu gibi.

Bu bölümün son uyarısı şudur: bu bölümdeki en büyük yanılgı, modelin karmaşıklığını başarıyla eş tutmaktır. Telemetri deneyinde AR(40) ile GRU arasındaki fark küçük çıktı; batarya deneyinde fiziksel bir eşik, öğrenen bir ağdan daha iyi çıktı. Derin bir model, kullanacağın yöntemin doğru seçimi ve değerlendirmenin dürüst olması şartıyla anlam kazanır.

## Çözümlü Örnekler

Bu bölümdeki dört örnek zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu vardır. Her örneğin sonunda, bir yapay zekâ aracı kullanmadan çözebileceğin bir varyasyon sorusu bulunur.

### Örnek 1 (★): Skaler bir RNN'in ileri geçişini elle izlemek

Skaler bir RNN düşün: h_t = tanh(W_x x_t + W_h h_{t−1} + b). Burada W_x = 0,5, W_h = 0,8, b = 0. Girdi dizisi x = (1, 0, −1), başlangıç durumu h_0 = 0.

**Adım 1 — Anla.** İstenen: h_1, h_2, h_3 değerleri. Her adımda önce a_t = W_x x_t + W_h h_{t−1} hesaplanır, sonra h_t = tanh(a_t).

**Adım 2 — Örnekle.** Bu küçük bir örnek; her adımı ayrı ayrı yazabiliriz. Girdi her adımda bir değer taşır, ama h_0 = 0 olduğu için ilk adım yalnızca girdiyle belirlenir.

**Adım 3 — Kaba çöz.** İlk adım: a_1 = 0,5 · 1 + 0,8 · 0 = 0,5, h_1 = tanh(0,5). İkinci adım: a_2 = 0,5 · 0 + 0,8 · h_1. Üçüncü adım: a_3 = 0,5 · (−1) + 0,8 · h_2.

**Adım 4 — Örüntü.** Her adımda aynı iki katsayı kullanılır ama girdi değişir. Gizli durum, geçmişin ağırlıklı ve sıkıştırılmış bir özetidir. Girdi sıfır olduğunda bile (ikinci adım) h_1'in etkisi h_2'ye taşınır; bu, RNN'in belleğidir.

**Adım 5 — İyileştir.** Hesabı tekrar tekrar tanh ile yapmak yerine her adımın a_t değerini ve h_t değerini bir tabloda tut. Böylece bir önceki adımın sonucunu doğrudan kullanırsın ve hata kolayca izlenir.

**Adım 6 — Doğrula.** İz tablosu:

| t | x_t | h_{t−1} | a_t = 0,5·x_t + 0,8·h_{t−1} | h_t = tanh(a_t) |
|---|---|---|---|---|
| 1 | 1 | 0 | 0,5 | 0,4621 |
| 2 | 0 | 0,4621 | 0,3697 | 0,3537 |
| 3 | −1 | 0,3537 | −0,2170 | −0,2137 |

Bu değerler Bölüm 68.6'daki t03 programının ileri geçiş çıktısıyla aynıdır (h_1 = 0,4621, h_2 = 0,3537, h_3 = −0,2137).

**Bunu AI'sız yazabilir misin?** Aynı ağırlıklarla girdi x = (0, 0, 1) ve h_0 = 0,5 olsaydı h_3'ü hesapla. Tabloyu tekrar oluştur ve h_0'ın h_3 üzerindeki etkisini ilk adımda değil son adımda ölç.

### Örnek 2 (★★): Aynı RNN'de zamanda geri yayılımı elle hesaplamak

Örnek 1'deki ağ ve girdi kullanılsın. Kayıp yalnızca son adımda olsun: L = ½ (h_3 − d)², d = 0,5. Hedef, ∂L/∂W_h ve ∂L/∂W_x değerlerini elle bulmak.

**Adım 1 — Anla.** İstenen iki gradyan. Zincir kuralı, son adımdan geriye doğru uygulanacak.

**Adım 2 — Örnekle.** Önce h_3 = −0,2137 ve kaybın türevi: ∂L/∂h_3 = h_3 − d = −0,7137. Gradyan üç adımın üzerinden akar.

**Adım 3 — Kaba çöz.** Her adımda δ_t = ∂L/∂h_t, bir sonraki adımdan gelen katkıyla birlikte hesaplanır. Sonra da da_t = δ_t (1 − h_t²), ve bu da_t, W_h ve W_x'in katkısını taşır: ∂L/∂W_h = Σ da_t h_{t−1}, ∂L/∂W_x = Σ da_t x_t.

**Adım 4 — Örüntü.** Gradyan geriye doğru çarpılan iki faktör taşır: W_h (= 0,8) ve tanh türevi (1 − h²). İkisi de 1'den küçük olduğu için, geriye gittikçe δ küçülür. Bu, Bölüm 68.7'deki sönümlenmenin küçük bir örneğidir.

**Adım 5 — İyileştir.** Tabloyu tek bir geriye geçişte doldur; her satırda δ_t, da_t ve iki katkıyı tut. Toplamı en son yaz.

**Adım 6 — Doğrula.** İz tablosu:

| t | δ_t | 1 − h_t² | da_t | h_{t−1} | katkı (W_h) | x_t | katkı (W_x) |
|---|---|---|---|---|---|---|---|
| 3 | −0,7137 | 0,9543 | −0,6811 | 0,3537 | −0,2409 | −1 | 0,6811 |
| 2 | −0,5449 | 0,8749 | −0,4767 | 0,4621 | −0,2203 | 0 | 0,0000 |
| 1 | −0,3814 | 0,7864 | −0,2999 | 0 | 0,0000 | 1 | −0,2999 |

Toplam: ∂L/∂W_h = −0,4612 ve ∂L/∂W_x = 0,3812. Bu değerler t03 programının çıktısıyla eşleşir (−0,461209 ve 0,381173; küçük fark yuvarlamadan). Sayısal türev de aynı sonucu verir; bu, elle hesabın ve kodun doğru olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** Kaybı yalnızca t = 1'de tanımla (L = ½ (h_1 − d)²) ve ∂L/∂W_h'yi yeniden hesapla. Bu durumda geçmiş adımlar gradyana katkı yapmaz mı? Cevabını tabloyla kanıtla.

### Örnek 3 (★★): Tek bir LSTM hücresi adımının elle hesabı

Girdi x = 1, önceki gizli durum h_0 = 0,5, önceki hücre durumu c_0 = 0,4. Ağırlıklar (tek boyutlu, PyTorch kapı sırası i, f, g, o): W_i = 0,5, U_i = 0,2, b_i = 0,1; W_f = 0,9, U_f = −0,3, b_f = 0,2; W_g = 1,2, U_g = 0,4, b_g = 0; W_o = 0,7, U_o = 0,1, b_o = −0,1. Hedef: c_1 ve h_1.

**Adım 1 — Anla.** İstenen: h_1 ve c_1. Dört kapı ve aday değeri hesaplayıp hücre güncellemesini yapmalıyız.

**Adım 2 — Örnekle.** Yalnızca bir adım var, ama dört ön aktivasyon ayrı ayrı hesaplanmalı.

**Adım 3 — Kaba çöz.** Ön aktivasyonlar a = W x + U h_0 + b: a_i = 0,5 + 0,1 + 0,1 = 0,7; a_f = 0,9 − 0,15 + 0,2 = 0,95; a_g = 1,2 + 0,2 + 0 = 1,4; a_o = 0,7 + 0,05 − 0,1 = 0,65.

**Adım 4 — Örüntü.** Hücre güncellemesi c_1 = f c_0 + i g toplamıdır; h_1 = o tanh(c_1). Kapılar sigmoid ile, aday tanh ile üretilir; sonuç her zaman 0 ile 1 arasında bir karışım ve −1 ile 1 arasında bir aday içerir.

**Adım 5 — İyileştir.** Önce dört kapıyı, sonra c_1'i, en son h_1'i hesapla. Ara sonuçları tek bir tabloda tut.

**Adım 6 — Doğrula.** İz tablosu:

| Büyüklük | Hesap | Değer |
|---|---|---|
| a_i, a_f, a_g, a_o | 0,7; 0,95; 1,4; 0,65 | (ön aktivasyon) |
| i | σ(0,7) | 0,6682 |
| f | σ(0,95) | 0,7211 |
| g | tanh(1,4) | 0,8854 |
| o | σ(0,65) | 0,6570 |
| c_1 | 0,7211 · 0,4 + 0,6682 · 0,8854 | 0,8800 |
| h_1 | 0,6570 · tanh(0,8800) | 0,4641 |

Bu değerler Bölüm 68.8'deki t05 programının çıktısıyla ve PyTorch LSTMCell sonucuyla eşleşir. Çıktı kapı sırası i, f, g, o'ya göre okunmuştur; sırayı karıştırsaydın c_1 ve h_1 farklı çıkardı.

**Bunu AI'sız yazabilir misin?** Aynı girdi ve ağırlıklarla unutma kapısının bias'ını b_f = −2 yap. Hangi kapı bu değişiklikten en çok etkilenir ve c_1 hangi yöne kayar? Yaklaşık değerleri elle hesapla, sonra kendi sonucunla karşılaştır.

### Örnek 4 (★★★): Sızıntılı bir değerlendirme betiğini düzeltmek

Bir ekip, İHA telemetrisinin akım kanalını son on örnekten tahmin eden bir kNN modeli kurdu. Raporladıkları test hatası 0,18 A'dı ve model "baz modeli geçti" diye sunuldu. Betik, üç hata içeriyordu: (a) test kümesi zaman açısından eğitimle iç içe rastgele seçildi, (b) ölçekleme ortalaması ve sapması tüm veriden hesaplandı, (c) özellik olarak hedef zamanın merkezli kayan ortalaması (hedef ve iki komşu değerin ortalaması) kullanıldı. Görevin, hatalı değerlendirmenin neden yanlış olduğunu bulmak ve her hatanın etkisini ayrı ayrı ölçerek düzeltilmiş sonucu vermek.

**Adım 1 — Anla.** İstenen: betikteki hataları bulmak, her birinin test hatasına etkisini ölçmek, düzeltilmiş sonucu raporlamak. Raporlanan 0,18'in gerçek bir genelleme hatası olup olmadığı sorusu cevaplanmalı.

**Adım 2 — Örnekle.** Her hata bir değerlendirme sorusuna karşılık gelir. (a) "Test noktaları eğitimin gelecekte mi, yoksa içinde mi?" (b) "Ölçek parametreleri kimden öğrenildi?" (c) "Bir özellik hedefin kendisini içeriyor mu?" Her soruya tek tek bakarak düzeltme yapacağız.

**Adım 3 — Kaba çöz.** Dört adımlı bir ayrıştırma yap: hatalı betikten başla, her seferinde bir hatayı düzelt ve test hatasının nasıl değiştiğini ölç. Bu, her hatanın katkısını ayırmanın en basit yoludur.

**Adım 4 — Örüntü.** Üç hata da aynı yönde çalışır: test kümesini eğitime yaklaştırır, test istatistiğini eğitime sokar ve hedefi özelliğe taşır. Birincisi kopya kontrolünü bozar, ikincisi ölçeği yanlış yerden alır, üçüncüsü ise gerçek zamanlı çalışmada hiç bulunmayacak bir bilgi verir. Tablodaki en büyük tek sıçrama ölçek adımındadır; özellik adımı ise canlı sistemde hiç üretilemeyecek bir bilgiyi çıkarır.

**Adım 5 — İyileştir.** Betiği, her düzeltmeyi açıkça ayrı bir adım olarak yazacak şekilde düzenle. Böylece hangi adımın hangi kazancı getirdiği tek bir tabloda görünür.

**Adım 6 — Doğrula.** Aşağıdaki program dört adımı sırayla uygular.

```python
# -*- coding: utf-8 -*-
"""Bölüm 68, Örnek 4: sızıntılı bir değerlendirmenin hatalarını
tek tek düzeltiyoruz. Her adımda test MAE'si yeniden ölçülür
(tohum 11)."""
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from ortak import iha_telemetri, pencere, HEDEF, mae

n, W = 24000, 10
ntr, nva = int(0.6 * n), int(0.8 * n)
Z = iha_telemetri(n, seed=11)
X, Y = pencere(Z, W, 1)
y = Y[:, 0]
m = len(X)
hb = np.arange(m) + W                 # hedefin zaman indeksi
F = X.reshape(m, -1)
g = Z[:, HEDEF]
gelecek = (g[hb - 1] + g[hb] + g[np.minimum(hb + 1, n - 1)]) / 3


def degerlendir(bolme, tum_veri_olcek, gelecek_var):
    if bolme == "rastgele":
        rng = np.random.default_rng(3)
        te = np.zeros(m, bool)
        te[rng.permutation(m)[:int(0.2 * m)]] = True
        tr = ~te
    else:
        tr = hb < ntr
        te = hb >= nva
    A = np.column_stack([F, gelecek]) if gelecek_var else F
    kaynak = A if tum_veri_olcek else A[tr]
    mu, sd = kaynak.mean(axis=0), kaynak.std(axis=0) + 1e-8
    A = (A - mu) / sd
    model = KNeighborsRegressor(5).fit(A[tr], y[tr])
    return mae(y[te], model.predict(A[te]))
```

Programın devamı aşağıdadır.

```python

adimlar = [
    ("0. hatalı: rastgele, tüm veri ölçek, gelecek özelliği",
     "rastgele", True, True),
    ("1. rastgele -> zamana göre bölme", "zaman", True, True),
    ("2. ölçek yalnızca eğitimden", "zaman", False, True),
    ("3. geleceği gören özelliği kaldır", "zaman", False, False),
]
print("%-52s %8s" % ("adım", "test MAE"))
for ad, bolme, tum, gel in adimlar:
    print("%-52s %8.4f" % (ad, degerlendir(bolme, tum, gel)))
```

```term
$ python t14_sizinti.py
adım                                                 test MAE
0. hatalı: rastgele, tüm veri ölçek, gelecek özelliği   0.1797
1. rastgele -> zamana göre bölme                       0.1923
2. ölçek yalnızca eğitimden                            0.2149
3. geleceği gören özelliği kaldır                      0.2344
```

Tablo, her düzeltmenin test hatasını nasıl değiştirdiğini gösterir.

| Adım | Açıklama | Test MAE (A) |
|---|---|---|
| 0 | Hatalı: rastgele bölme, tüm veriyle ölçek, gelecek özelliği | 0,1797 |
| 1 | Rastgele bölme yerine zamana göre bölme | 0,1923 |
| 2 | Ölçek yalnızca eğitimden | 0,2149 |
| 3 | Geleceği gören özelliği kaldır | 0,2344 |

Düzeltilmiş hata 0,2344 A'dır. Raporlanan 0,18 A, sızıntının yarattığı yapay bir iyileşmedir; fark yaklaşık %23'tür. Adımların katkıları sırasıyla 0,0126, 0,0226 ve 0,0195 A; toplam 0,0547 A eder. Bu paylar adım sırasına bağlıdır, çünkü etkiler birbiriyle etkileşir. Sonuç, betiğin bir daha çalıştırılması gerektiğini değil, raporlanan sayının anlamını değiştirdiğini gösterir. Zamana göre bölmede kNN ile doğrusal modelin hatası da aynı aralıktadır (Bölüm 68.3, t01 çıktısı).

**Bunu AI'sız yazabilir misin?** Betikte ek bir hata olduğunu düşün: test kümesi seçildikten sonra en iyi k'yı test hatasına bakarak seçmek. Bunu düzeltmek için hangi kümeye ihtiyacın olur ve bu düzeltme sonucu nasıl etkiler?

## Kendin Yap Projeleri

::: dikkat
Bu iki projede önce kendi çözümünü yaz. Yapay zekâ aracını yalnızca bitirdikten sonra, bir hatayı bulmak ya da kodunu karşılaştırmak için kullan. Bu bölümü geçmek için değil, bu bölümü öğrenmek için yapıyorsun.
:::

### Proje 1 (★★): İHA telemetri izleme sistemi

**Amaç.** Bu bölümdeki t08, t10 ve t12 programlarını tek bir izleme sistemine birleştir. Sistem akım kanalını çok değişkenli girdiyle (irtifa, hız, yuvarlanma, akım) bir adım ileri tahmin etsin, tahmin artığından bir alarm üretsin ve bu alarmın doğruluğunu ölçsün.

**Yapılacak ve beklenen davranış.** Sistem üç şey yapmalı: (a) eğitimi ilk %60'ta, eşik seçimini doğrulamada, değerlendirmeyi son %20'de yapmalı; (b) hem zamansal artığı (geçmiş gözlenen akım) hem bağlamsal artığı (aynı andaki hız ve yuvarlanma) kullanan iki detektör içermeli; (c) bir akış modu olmalı: her yeni örnek geldiğinde tahmin ve alarm yalnızca o örneği ve bir tamponu kullanarak üretilmeli, bütün diziyi yeniden işlememeli.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce her detektör için yanlış alarm oranını ve kaçırma oranını ayrı ayrı yazan bir tablo oluştur. Eşiği, anomalisiz doğrulama artıklarının yüksek bir yüzdeliğinden seç, test kümesine bakmadan. Akış modu için bir tampon ve bir durum tut; GRU kullanıyorsan gizli durumu adım adım taşı ve toplu sonuçla karşılaştır. Sıçrama sonrası MA20 detektörünün neden 20 örnek boyunca alarm verdiğini düşün.

**Başarı kriterleri.** (1) Her detektör için doğruluk, duyarlılık ve saatlik yanlış alarm oranı, üç tohum ortalaması ve sapmasıyla verilmiş. (2) Sıçrama ve kayma için ayrı duyarlılık raporlanmış. (3) Akış modunun toplu sonuçla eşleştiği sayısal olarak gösterilmiş. (4) Raporun sonunda, eşiğin neden test kümesinden seçilmemesi gerektiğini ve bu hatanın raporlanan performansı nasıl şişireceğini açıklayan bir paragraf var.

### Proje 2 (★★★): Sıfırdan NumPy LSTM, BPTT ve gradient check

**Amaç.** Bölüm 68.8'deki LSTM ileri geçişini NumPy ile yaz, ardından geriye yayılımını (BPTT) türet ve uygula. Her parametre grubu için sayısal türevle karşılaştır. Son olarak aynı ağırlıklarla PyTorch'un nn.LSTM'i ile eşleşmeyi doğrula.

**Yapılacak ve beklenen davranış.** Kod şunları yapabilmeli: (a) kapı sırası i, f, g, o ile ileri geçiş; (b) tüm parametreler için gradyan hesabı; (c) gradient check, bağıl hata 10⁻⁶'nın altında; (d) PyTorch çıktısı ile en büyük fark 10⁻¹⁰'dan küçük; (e) T = 50 gibi uzun bir dizide kayıp azalır. Eğitim, t06'daki görevle, yani ilk işaretin tahmini ile yapılabilir.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Her kapının türevini ayrı yaz: sigmoid için σ(1 − σ), tanh için 1 − tanh². Geriye giden δ'yı hücre durumu yolu ile gizli durum yolunu ayırarak taşı: ∂c_t/∂c_{t−1} = f_t. Bu ayrım, Bölüm 68.8'deki "otoyol" fikrinin gradyana nasıl yansıdığını görmeni sağlar. Sayısal türevi merkezi fark ile hesapla ve ε değerini birkaç farklı büyüklükte dene.

**Başarı kriterleri.** Yukarıdaki beş madde, her biri ayrı bir tabloda raporlanmış olmalı. Ayrıca raporda, hangi gradyan bileşeninin en büyük bağıl hatayı verdiğini ve bunun bir kodlama hatası mı yoksa sayısal bir sınır mı olduğunu tartışan bir paragraf bulunmalı.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Bir RNN'in gizli boyutu H = 16, girdi boyutu I = 4 ise parametre sayısı kaçtır? Bias'ları da say ve formülünü yaz. PyTorch'un iki bias kullanmasını hesaba kat.
2. ★ Bir GRU ile bir LSTM aynı H ve I ile kurulduğunda, hangisi daha az parametre içerir ve oranı yaklaşık kaçtır? Oranı H ve I cinsinden yaz.
3. ★ Skaler bir RNN'de W_h = 1 ve tanh yerine kimlik fonksiyonu kullanılsın. T adımdan sonra ∂h_T/∂h_0 kaçtır? Bu sonuç patlamayı mı, sönümlenmeyi mi gösterir?
4. ★★ Unutma kapısının f_t = 0,5 sabit olduğu bir LSTM'de, c_0'ın c_10 üzerindeki etkisi ne kadardır? f_t = 0,99 olursa ne olur? Bu hesabı hücre durumu yoluyla yap, gizli durum yolu ile değil.
5. ★★ Yığınlanmış bir RNN'de (iki katman) gradyan, bir kat daha uzun yoldan geçer. Bu, kaybolan gradyanı nasıl değiştirir? Bir katmanın gradyan yolunu ve iki katmanın yolunu karşılaştır. (Mülakat)
6. ★★ Bir TCN'de K = 5 ve d = 1, 2, 4, 8, 16 ile iki konvolüsyonlu bloklar kullanılıyor. Alıcı alanı hesapla. Aynı alıcı alanını tek bir konvolüsyon yığınında (blok yok) elde etmek için kaç katman gerekir?
7. ★★ Zaman serisinde neden rastgele bölme yapılmaz? Tek bir cümleyle ve bir sayısal örnekle açıkla. (Mülakat)
8. ★★ LSTM neden kaybolan gradyanı azaltır? Hücre durumu güncellemesinin türevini kullanarak, bir adımlık gradyan akışının hangi koşulda sönümlenmediğini göster. (Mülakat)
9. ★★ Teacher forcing nedir ve eğitimde hangi sorunu çözer? Çıkarımda hangi yeni sorun ortaya çıkar? Bu iki durumu bir örnekle açıkla. (Mülakat)
10. ★★★ Özyinelemeli çok adımlı tahmin, bir adımlık modeli tekrar tekrar kullanır. Her adımdaki hatanın bağımsız ve sabit varyanslı olduğunu varsayarsan, k adım sonraki hata varyansı nasıl büyür? Bu varsayımların gerçek bir sensör verisinde neden sağlanmayabileceğini tartış. (Mülakat)
11. ★★★ Bir anomali detektörünün eşiği doğrulamada %99,95 yüzdeliğine göre seçildi. Test kümesinde yanlış alarm oranı beklenenden çok daha yüksek çıkıyor. Bunun olası üç nedenini ve her birini nasıl ayırt edeceğini yaz.
12. ★★★ Bir modelin test MAE'si AR(40) baz modelinden %0,5 daha iyi. Bu farkın gerçek bir kazanç olup olmadığını nasıl anlarsın? Üç tohumla yapılan bir deneyin sonucunu nasıl yorumlarsın? (Mülakat)

## Kod Okuma Egzersizi: PyTorch 2.6.0 LSTM

Bölüm 68.8'de LSTM'in kapı sırasını ve iki sapma vektörünü gördük. Şimdi bu ayrıntıların gerçek bir kütüphanede nasıl yazıldığına bakalım. Kaynak, kurulu PyTorch 2.6.0+cu124 sürümünün `torch/nn/modules/rnn.py` dosyasıdır (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\nn\modules\rnn.py`). Aşağıdaki iki kesit bu dosyadan satır satır alınmıştır; hiçbir satır değiştirilmemiştir.

İlk kesit, `RNNBase.__init__` içinde kapı sayısının belirlendiği satırlardır (145–154). Bu blok, dört kapılı LSTM'de kapı boyutunu 4H, GRU'da 3H, basit RNN'de H olarak seçer.

```python
        if mode == "LSTM":
            gate_size = 4 * hidden_size
        elif mode == "GRU":
            gate_size = 3 * hidden_size
        elif mode == "RNN_TANH":
            gate_size = hidden_size
        elif mode == "RNN_RELU":
            gate_size = hidden_size
        else:
            raise ValueError("Unrecognized RNN mode: " + mode)
```

Bu seçimin sonucu, Bölüm 68.8'deki parametre formülünün kaynağıdır: W_ih'nin satır sayısı gate_size, sütun sayısı girdi boyutudur. Kapılar tek bir büyük matriste üst üste dizilir; yani W_ih'nin ilk H satırı giriş kapısının, sonraki H satırı unutma kapısının ağırlığıdır. Bu, PyTorch'un i, f, g, o sırasının kodda nasıl sabitlendiğidir.

İkinci kesit, `LSTM.forward` içinde yerel kütüphaneye yapılan çağrıdır (satır 1124–1135). Python tarafı girdiyi doğrular ve başlangıç durumlarını hazırlar; asıl hesabı C++ ile yazılmış `_VF.lstm` yapar.

```python
            result = _VF.lstm(
                input,
                hx,
                self._flat_weights,  # type: ignore[arg-type]
                self.bias,
                self.num_layers,
                self.dropout,
                self.training,
                self.bidirectional,
                self.batch_first,
            )
        else:
```

Dikkat edilecek üç yer var. Birincisi, `hx` başlangıç durumudur ve açıkça verilmezse sıfırlarla doldurulur; bu yüzden Bölüm 68.8'deki skaler hücre örneğinde başlangıç durumunu açıkça verdik. İkincisi, `self._flat_weights` tüm katman ağırlıklarını tek bir listede toplar; çift yönlü ve çok katmanlı durumda bu listede her yön ve katman için ayrı ağırlık bulunur. Üçüncüsü, `self.bias` bayrağı sapmaların kullanılıp kullanılmayacağını belirler; bu parametre `bias=False` ile kapatılabilir ve o durumda kapı formülü sapmasız çalışır. Kodda hesabın kendisi görünmez, çünkü onu `_VF.lstm` yapar. Bu yüzden Bölüm 68.8'deki NumPy karşılaştırması, kütüphanenin doğruluğunu bağımsız olarak doğrulamanın tek yoludur.

**Sorular — cevaplamadan geçme:**

1. `gate_size` için `RNN_TANH` ve `RNN_RELU` aynı değeri veriyor. Bu iki mod arasındaki fark kodun neresinde ve hangi aktivasyonda ortaya çıkar? Dosyada aramak için ipucu: `mode` değişkeni `RNNBase.__init__` çağrısında nasıl belirleniyor?
2. Kapı sırası kodda açıkça yazılmamış. W_ih'nin ilk H satırının giriş kapısı olduğunu, bu kesitten hangi tek satıra bakarak doğrulayabilirsin? Yazılı kanıt nerede olurdu?
3. `_VF.lstm` çağrısına `hx` olarak bir tuple geçiyor. Bu tuple'ın iki elemanı hangileri ve boyutları neye bağlı? Bölüm 68.8'deki çift yönlü örnekte `h_n` şeklini (4, 4, 32) olarak görmüştük; bu şekli açıklayan parametreler hangileri?
4. `self._flat_weights` ile `self.bias` ayrı tutuluyor. Neden ağırlıklar ile sapmalar aynı listede değil? Bu tasarım, `bias=False` ile kurulan bir modelin parametre sayısını nasıl etkiler?
5. Bu kesitte bir kütüphane hatası ya da belirsizlik var mı? Yorum satırındaki `type: ignore[arg-type]` ne anlama geliyor ve neden bu kod güvenlidir?
6. Kendi NumPy LSTM'in (Bölüm 68.8) ile bu kütüphane çağrısı arasında hangi bilgi eksik kalır? Eksik bilgiyi tamamlamak için hangi ölçümü yapardın?

## Bölüm Özeti

- Zaman serisi, sırası anlamlı bir veridir. Görevler tahmin, dizi sınıflandırma, dizi-dizi ve anomali tespitidir; her birinin kayıp fonksiyonu ve ölçütü farklıdır.
- Kayan pencere, sayısal bir zaman serisini (X, y) biçimine çevirir. Komşu pencereler örtüştüğü için rastgele bölme, kopya kontrolünü bozar ve hatayı yapay olarak düşürür. Zamana göre bölme, ölçeklemenin yalnızca eğitimden öğrenilmesi ve hedefin geleceğini gören özelliklerin dışarıda tutulması zorunludur.
- Baz modeller (naif, mevsimsel naif, hareketli ortalama, AR(p)) her derin model için bir çıtadır. Bu veride AR(40) en güçlü baz modeldi (0,1777 ± 0,0002); mevsimsel naif, gürültüyü kopyaladığı için naiften kötüydü.
- RNN, gizli durum üzerinden bellek taşır ve parametrelerini zamanda paylaşır. BPTT gradyanı her adımın katkısının toplamı olarak verir; gradient check ile doğrulandı (bağıl hata 4·10⁻⁹'un altında).
- Jacobian çarpımı, yarıçap 0,9 iken üssel olarak sönümlenir. Yarıçap 1,1 iken de tanh doygunluğu nedeniyle norm sonunda küçülür: kaybolan gradyan ile patlama, yalnızca yarıçapla değil, aktivasyonun doygunluğuyla da belirlenir.
- LSTM'in hücre durumu, gradyan için bir toplam yolu sağlar. NumPy ile yazdığımız ileri geçiş, PyTorch'un nn.LSTM'i ile 10⁻¹⁶ düzeyinde eşleşti; kapı sırası i, f, g, o'dur. Uzun bağımlılık görevinde LSTM ve GRU bu bütçede T = 40 ve 80'de öğrenemedi, RNN ise bir tohumda öğrendi: kapılı hücrenin üstünlüğü garanti değildir.
- TCN, nedensel dolgu ve genişletilmiş konvolüsyonla alıcı alanı üstel olarak büyütür; alıcı alanı 1 + 2(K − 1)Σd formülüyle verilir ve bu, ölçülen değerle (61 ve 125) eşleşti.
- İHA telemetrisinde tahmin deneyinde GRU, üç tohumun ortalamasında AR(40)'ı ve diğer modelleri geçti, ama fark küçüktür; anomali tespitinde yalnızca zamansal artık, yavaş kaymayı görmez, bağlamsal artık (aynı andaki hız ve yuvarlanmaya dayalı) görür.
- Akış çıkarımında GRU'nun gizli durumunu adım adım taşımak, toplu sonuçla birebir eşleşir; TCN için bir tampon gerekir ve tam eşleşme yalnızca alıcı alanı kadar geçtikten sonra başlar.

**Sonraki bölümde:** Bölüm 69, Attention ve Transformer'a geçiyor. Bu bölümde gördük ki RNN'ler her adımda bir öncekine bağlı olduğu için paralel hesaplanamaz ve uzun bağlamı tek bir gizli durumla taşır. Dikkat mekanizması, her çıktıyı tüm girdilere doğrudan bağlayarak bu iki sınırı aşmayı dener. Konumsal kodlama ve maskeleme, TCN'deki nedensellik fikrinin dikkat katmanındaki karşılığıdır.

::: mulakat
1. Vanilla RNN'de uzun bağımlılığın neden zor olduğunu, gizli durumun Jacobian çarpımı üzerinden açıklar mısın? Yarıçapın hangi değeri sönümlenmeye yol açar?
2. LSTM'de hücre durumu güncellemesi neden gradyan için bir "otoyol" sağlar? ∂c_t/∂c_{t−1} ifadesinden yola çıkarak açıkla.
3. GRU ile LSTM arasındaki temel mimari farkları nelerdir? Parametre sayılarını H ve I cinsinden karşılaştır.
4. Zaman serisinde neden rastgele train/test bölmesi yanlıştır? Kopya kontrolü kavramını bir örnekle anlat.
5. TCN'de nedensellik nasıl sağlanır? Sol dolgunun ikinci konvolüsyon için de gerekli olmasının nedenini açıkla.
6. Teacher forcing nedir, neden eğitimi kolaylaştırır ve çıkarımda hangi sorunu yaratır?
7. Özyinelemeli ve doğrudan çok adımlı tahmin arasındaki farkı, hata birikimi açısından açıkla. Hangisi ne zaman tercih edilir?
8. Bir anomali detektörünün eşiğini test kümesinden seçmek neden hatalıdır? Doğru eşik seçimi için hangi üç küme gerekir?
