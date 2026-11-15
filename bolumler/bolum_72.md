%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 72
%% baslik: Üretken Modeller

## Giriş: Modelden örneğe

Bölüm 70'te bir dil modelinin bir sonraki belirteç için olasılık dağılımı verdiğini gördük. Bölüm 71'de bu dağılımın etrafına örülen sistemi, yani istemleri, geri getirmeyi ve araçları kurduk. Bu bölümde sorunun yönünü çeviriyoruz. Artık modelden bir cevap istemiyoruz; modelden yeni bir örnek istiyoruz: bir el yazısı rakam, bir sensör sinyali, bir görüntü ya da bir ses parçası. Bir modelin veri dağılımını öğrenip o dağılımdan örnek çekebilmesine **üretken model** diyoruz.

Üretken modeller günlük hayatta her yerde. Bir fotoğraf düzenleyicideki "eksik bölgeyi doldur" özelliği, bir ses sentezleyicinin konuşması, bir ilaç tasarımında yeni molekül önerisi, hepsi bu ailenin ürünüdür. Savunma sanayiinde iki kullanım öne çıkar. Birincisi **veri kıtlığı**: bir hedef tespit sistemini eğitecek gerçek İHA görüntüsü azdır, ama üretken bir modelle sentetik görüntü üretip modeli çeşitlendirebilirsin (bu bölümde bunu ölçeceğiz). İkincisi **anomali**: bir sensörün normal davranışını öğrenmiş bir model, normalden sapan bir okumayı yeniden üretemez ve bu yeniden üretme hatası bir alarm sinyali olur. Bölüm 61'de anomali tespitini yoğunluk ve PCA ile görmüştük; burada aynı fikri derin ağlarla yapacağız.

Bu bölümün bir de başka, daha az konuşulan yönü var. Mert'in ÖZCE projesi, semantik iletişimde verinin anlamını taşıyan kısa bir gizil kodu iletir. Bu, bir autoencoder'ın gizil uzayının kanaldan geçirilmesi demektir ve Bölüm 46'da işaret ettiğimiz "uçta kodlama" fikrinin tam karşılığıdır. ÖZCE'nin kendi dosyalarına bu bölümde dokunmuyoruz; yalnızca kavramsal olarak ona bağlanan küçük bir deneyle, bit bütçesi ile görev doğruluğu arasındaki ilişkiyi kendi verimizde ölçeceğiz.

::: not
Üretken modeller bir dağılımın **örneğini** üretir; ayırt edici modeller ise bir girdi için **etiketini** tahmin eder. Bu ayrım bölümün ilk konusudur ve sonraki her ailenin neyi, neden ve nasıl öğrendiğini belirler. Bu bölümdeki her model iki ayrı sayısal kanıtla doğrulanacak: önce küçük ve tamamen bilinen bir dağılımda (iki boyutlu halka), sonra gerçek bir veri kümesinde (`load_digits`). Her ölçüm için tohum ve veri bölmesi metinde verilmiştir.
:::

## 72.1 Ayırt edici ile üretken: p(y|x) ve p(x)

Bölüm 62'de Bayes kuralını ve iki yaklaşımı tanıdık. Bir ayırt edici (discriminative) model, verilen bir `x` girdisi için `y` etiketinin koşullu olasılığını öğrenir: `p(y|x)`. Lojistik regresyon, destek vektör makineleri ve sınıflandırıcı sinir ağları bu gruba girer. Bir üretken (generative) model ise `x` ile `y` birlikte dağılımı, yani `p(x, y)` ya da etiketsiz veri için `p(x)` öğrenir. Bayes kuralı `p(x, y) = p(y|x) p(x)` olduğu için bir üretken model, `p(y|x)` için de bir çıkarım yolu verir; tersi her zaman doğru değildir.

Bu fark pratikte önemlidir. Ayırt edici bir model sınır çizer; sınırın dışında ne olduğu, modelin bilmek zorunda olduğu bir şey değildir. Üretken bir model ise bütün veri dağılımını kapsamak zorundadır. Bu yüzden üretken model öğrenmek daha zordur, ama daha fazla şey yapar: örnek üretir, eksik veriyi doldurur, bir girdinin "ne kadar olağan" olduğunu ölçer.

Üretken bir modelde `p(x)` değerini hesaplayabiliyorsak ona **olabilirlik** (likelihood) değerlendirmesi yapabiliyoruz deriz. Bu, anomali tespitinin temelidir: düşük olabilirlikli bir girdi, eğitim dağılımına uymayan bir girdidir. Ama Bölüm 72'nin ilerleyen kısımlarında göreceğimiz gibi her üretken model bu değeri açıkça hesaplayamaz. GAN'lar `p(x)` değerini vermez; difüzyon modelleri onu ancak yaklaşık olarak verir. Bu yüzden "bir modelin ne yaptığını" sorarken hangi soruya cevap verdiğini bilmek gerekir: olabilirlik mi, örnek kalitesi mi, çeşitlilik mi.

::: baglanti
Bölüm 62'de `p(y|x)` ile `p(x, y)` arasındaki farkı Bayes sınıflandırıcısı üzerinden görmüştük. Bu bölüm aynı ayrımı derin ağlarda, veri dağılımının kendisini öğrenme düzeyinde yeniden kurar.
:::

## 72.2 Üretken model aileleri haritası

Üretken modelleri birbirinden ayıran temel soru, dağılımı **nasıl** temsil ettikleridir. Şekil 72.1 beş ailenin ana fikrini özetler. Her ailenin bu kitapta hangi bölümde ele alındığını da gösterir.

![Şekil 72.1: Üretken model aileleri ve bu bölümdeki yerleri](gorseller/b72_aileler_harita.png)

**Otoregresif modeller** olasılığı zincir kuralıyla parçalar: `p(x) = Π p(x_i | x_<i)`. Her öğeyi önceki öğelere koşullu tahmin ederek üretirsin. Bölüm 70'teki dil modelleri tam olarak bu ailedendir; piksel düzeyinde çalışan modeller de öyledir. Olabilirlik açıkça hesaplanır, ama üretim sıralıdır ve yavaştır: her öğe bir öncekine bağlıdır.

**Gizil değişkenli modeller** gözlemlenmeyen bir `z` değişkeni varsayar ve `x`'i `z`'den üretir. Autoencoder ve VAE bu ailededir. Burada yoğunluk genellikle doğrudan hesaplanamaz; onun yerine bir alt sınır (ELBO) optimize edilir.

**Çekişmeli modeller** (GAN) bir üretici ile bir ayırt ediciyi birbirine karşı eğitir. Üretici sahte örnek üretir, ayırt edici gerçek ile sahteyi ayırmaya çalışır. Olabilirlik hesaplanmaz; kalite ve çeşitlilik yalnızca örneklerden ölçülür.

**Akış (flow) modelleri** tersinir ve hesaplanabilir Jacobian'a sahip bir dönüşüm zinciriyle veriyi basit bir dağılıma eşler. Olabilirlik tam olarak hesaplanır. Bu bölümde ayrıntıya girmiyoruz; genel bilgi olarak bilmen yeterli.

**Skor ve difüzyon modelleri** veriye gürültü ekleyen ileri bir süreç ve bu gürültüyü adım adım geri alan bir ters süreç tanımlar. Modelin öğrendiği şey, gürültülü bir girdide "gürültü nedir" sorusunun cevabıdır. DDPM ve DDIM bu ailenin örnekleridir.

::: not
Haritadaki sınırlar kesin değildir. Bir VAE'nin kodlayıcısını bir otoregresif akışla değiştirebilirsin; difüzyon modelleri de bir tür gizil değişkenli modeldir. Haritanın amacı hangi sorunun hangi araçla çözüldüğünü görmektir, sistematik bir taksonomi değil.
:::

## 72.3 Değerlendirme zorluğu ve ölçütler

Bir üretken modeli değerlendirmek sınıflandırıcıyı değerlendirmekten zordur. Bir sınıflandırıcının doğruluğu, tahminin etiketle eşleşip eşleşmediğine bakarak ölçülür. Üretken bir modelde ise tek bir doğru cevap yoktur. Üç ayrı özelliğe bakmak gerekir.

**Olabilirlik.** Model test verisine ne kadar yüksek olasılık veriyor? Bu yalnızca olabilirlik değerlendirmesi yapabilen ailelerde (VAE için ELBO, otoregresif modeller için doğrudan) anlamlıdır. Bir VAE'de ELBO bir alt sınırdır, asıl olabilirlik ondan büyüktür; yani ELBO'yu raporlarken "alt sınır" demek gerekir.

**Kalite.** Üretilen örnekler gerçek görünüyor mu? Bu, gerçek dağılımın destekleyeceği bölgede olmakla ilgilidir. Kesinlik (precision) bu ölçütün sayısal karşılığıdır: üretilen örneklerin kaçı gerçek dağılımın "içinde" kalıyor?

**Çeşitlilik.** Model dağılımın tüm bölgelerini üretiyor mu? Geri çağırma (recall) bu ölçütün karşılığıdır: gerçek örneklerin kaçı üretilen dağılımın yakınında? Bir GAN yalnızca bir iki rakam üretip ikisini mükemmel yapabilir; kesinlik yüksek, geri çağırma düşük olur. Bu, Bölüm 72.8'de göreceğimiz **mod çöküşü**nün ölçülebilir hâlidir.

Görüntüde sık kullanılan **Fréchet başlangıç mesafesi** (FID) bu üç özelliği tek bir sayıda birleştirmeye çalışır. Gerçek ve üretilen örneklerin özellik vektörlerinin ortalama ve kovaryanslarını alır, iki Gauss arasındaki Fréchet mesafesini hesaplar:

FID = |m₁ − m₂|² + tr(Σ₁ + Σ₂ − 2 (Σ₁ Σ₂)^{1/2})

Burada m ortalama, Σ kovaryans, (Σ₁Σ₂)^{1/2} matrisin karekökü. Matris karekökü, Bölüm 48'deki özdeğer ayrışımıyla hesaplanır. Gerçek FID özellik çıkarıcı olarak büyük bir Inception ağı kullanır; bu bölümde internetten ağırlık indirmiyoruz. Bunun yerine, kendi eğittiğimiz küçük sınıflandırıcının 32 boyutlu gizli katmanını kullanacağız ve buna **mini-FID** diyeceğiz. Bu bir FID değildir; ölçtüğümüz şey aynı matematiksel mesafenin farklı bir özellik uzayındaki karşılığıdır, ve sonuçları bu nedenle yalnızca bu bölümün kendi deneylerinde karşılaştırabiliriz.

Kodun tamamı `b72_metrik.py` dosyasındadır. Üç ölçüt burada tanımlanır: mini-FID (`frechet`), kNN tabanlı kesinlik ve geri çağırma (`kesinlik_geri_cagirma`) ve ezber ölçüsü (`tam_olcut` içindeki oran). Kesinlik ve geri çağırma için Kynkäänniemi ve arkadaşlarının (2019) kullandığı kNN yarıçapı fikrini kullanıyoruz; bu bir genel bilgi, ve burada kendi küçük sürümümüzü yazıyoruz.

```python
# -*- coding: utf-8 -*-
"""Uretken model olcutleri (mini-FID, kesinlik/geri cagirma,
ezberleme). Ozellikler, b72_veri'deki sinif-landiricinin
gizli katmanindan (32 boyut) alinir."""
import numpy as np
import torch
from scipy import linalg
from scipy.spatial.distance import cdist

@torch.no_grad()
def ozellik(model, x):
    t = torch.as_tensor(x, dtype=torch.float32)
    return model.ozellik(t).numpy()

def frechet(f1, f2):
    """Frechet (FID) mesafesi: |m1-m2|^2 + tr(S1+S2-2(S1 S2)^1/2)."""
    m1, m2 = f1.mean(0), f2.mean(0)
    s1 = np.cov(f1, rowvar=False)
    s2 = np.cov(f2, rowvar=False)
    # Tekil kovaryans olabilir (olu ozellik boyutlari): kucuk bir
    # kosegen ekleme standart uygulamadir.
    off = 1e-6 * np.eye(s1.shape[0])
    kok, _ = linalg.sqrtm((s1 + off) @ (s2 + off), disp=False)
    if np.iscomplexobj(kok):
        kok = kok.real
    return float(((m1 - m2) ** 2).sum() + np.trace(s1 + s2 - 2 * kok))

def kesinlik_geri_cagirma(gercek, sahte, k=3):
    """Kynkaanniemi (2019) tarzi kNN tabanli kesinlik ve geri
    cagirma. Her nokta icin k. komsu uzakligi 'yaricap' olur;
    kesinlik: sahte orneklerin gercek topluluk toplarinda oranı."""
    def yaricap(a):
        d = cdist(a, a)
        np.fill_diagonal(d, np.inf)
        return np.sort(d, axis=1)[:, k - 1]
```

Aşağıdaki parça `en_yakin`, `entropi`, `tam_olcut` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
    def kapsama(a, b, ra):
        d = cdist(b, a)
        return float((d <= ra[None, :]).any(axis=1).mean())

    ra = yaricap(gercek)
    rb = yaricap(sahte)
    return kapsama(gercek, sahte, ra), kapsama(sahte, gercek, rb)

def en_yakin(a, b):
    """a'daki her ornegin b icindeki en yakin komsu uzakligi."""
    return cdist(a, b).min(axis=1)

def entropi(etiketler, sinif=10):
    p = np.bincount(etiketler, minlength=sinif) / len(etiketler)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())

def tam_olcut(x, xtr, clf, xte):
    """Uretilen ornekler x (n, 64, [0,1]) icin tek seferde olcutler.
    Referans: egitim kumesi xtr. Ezber orani: uretilen orneklerin
    egitime en yakin uzakliginin medyani / test orneklerinin egitime
    en yakin uzakliginin medyani (~1: ezber yok; <<1: ezber var)."""
    import b72_veri
    fx = ozellik(clf, x)
    ftr = ozellik(clf, xtr)
    p, r = kesinlik_geri_cagirma(ftr, fx)
    yhat = b72_veri.tahmin(clf, x)
    ezber = float(np.median(en_yakin(x, xtr)) /
                  np.median(en_yakin(xte, xtr)))
    return {"fid": frechet(fx, ftr), "precision": p, "recall": r,
            "entropi": entropi(yhat), "ezber": ezber}
```

Ezber ölçüsü, üretilen örneklerin eğitim kümesine olan uzaklığını test örneklerininkiyle karşılaştırır. Bir model eğitim örneklerini aynen tekrarlıyorsa üretilen örneklerin eğitim kümesine uzaklığı çok küçük olur; oran 1'in çok altına düşer. Oran 1 civarındaysa model yeni örnekler üretiyor demektir. Bu ölçü mükemmel değildir (ezberlemek yerine eğitim verisine çok yakın ama farklı örnek üretmek de mümkündür), ama ezberlemeyi kabaca yakalar.

::: dikkat
Bir üretken modelin tek bir sayıyla değerlendirilmesi sık görülen bir hatadır. FID düşük olabilir ama model yalnızca gerçek veriyi ezberlemiş olabilir; kesinlik yüksek olabilir ama çeşitlilik sıfır olabilir. Bu bölümdeki her karşılaştırmada üç ölçütü birlikte ve ezber oranıyla birlikte veriyoruz. Bunu sen de yap.
:::

## 72.4 Autoencoder: darboğaz, yeniden yapılandırma ve PCA

Bir **autoencoder** (otomatik kodlayıcı) iki ağdan oluşur. Kodlayıcı `f_φ` girdiyi düşük boyutlu bir `z` gizil kodunu dönüştürür; çözücü `g_θ` bu kodu tekrar girdi uzayına döndürür. Eğitim hedefi girdinin kendisini yeniden üretmektir:

L = ||x − g_θ(f_φ(x))||²

Bu hedefte "etiket" yoktur; girdi hem girdi hem hedeftir. Öğretici olan kısım **darboğazdır**: `z`'nin boyutu `x`'in boyutundan küçükse ağ bilgiyi sıkıştırmak zorunda kalır. Sıkıştırmada neyi koruyup neyi atacağına veri öğrenir. Şekil 72.2 bu mimariyi ve VAE'nin yeniden parametrelendirmesini yan yana gösterir. Şimdilik soldaki autoencoder'a odaklan; sağdaki kısmı 72.7'de ayrıntılı açıklayacağız.

![Şekil 72.2: Autoencoder darboğazı (solda) ve VAE yeniden parametrelendirmesi (sağda)](gorseller/b72_ae_vae_mimari.png)

Doğrusal bir autoencoder'ın ne öğrendiğini anlamak için en basit durumu ele alalım: kodlayıcı ve çözücü doğrusal, kayıp ortalama karesel hata. Bu durumda öğrenilen alt uzay, Bölüm 61'deki PCA'nın ana bileşenlerinin uzayıyla aynıdır. Yani doğrusal bir autoencoder, PCA'nın öğrendiğini öğrenir; sadece koordinatların seçimi (ve dolayısıyla bileşenlerin dönüşü) farklı olabilir. Bunu kanıtlamak için derin bir ağa ihtiyaç yok; kendi verimiz üzerinde doğrusal bir AE eğitip PCA ile karşılaştıralım.

Veri olarak `load_digits` kullanıyoruz: 1797 adet 8×8 el yazısı rakam, her piksel 0 ile 16 arasında, biz 16'ya bölüp [0, 1] aralığına getiriyoruz. Veri %80 eğitim, %20 test olarak tabakalı bölünüyor. Bu ortak yardımcı kod `b72_veri.py` dosyasında. Bu dosya ayrıca bu bölümün sınıflandırıcısını da içerir; sınıflandırıcı daha sonra üretilen örneklerin "rakam olarak okunup okunmadığını" ölçmek için kullanılacak.

```python
# -*- coding: utf-8 -*-
"""Bolum 72 ortak yardimcilari: digits verisi, sinif-landirici,
2B halka verisi ve mod olcutu."""
import os
import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
os.makedirs(OUT, exist_ok=True)

def digits_bol(seed=0):
    """8x8 el yazisi rakamlari, [0,1] araliginda; %80 egitim,
    %20 test (siniflara gore tabakali)."""
    d = load_digits()
    x = (d.data / 16.0).astype(np.float32)
    y = d.target.astype(np.int64)
    xtr, xte, ytr, yte = train_test_split(
        x, y, test_size=0.2, random_state=seed, stratify=y)
    return xtr, ytr, xte, yte

class Siniflandirici(nn.Module):
    """64 -> 128 -> 32 (ozellik) -> 10 (sinif)."""

    def __init__(self):
        super().__init__()
        self.ozellik = nn.Sequential(
            nn.Linear(64, 128), nn.ReLU(),
            nn.Linear(128, 32), nn.ReLU())
        self.cikis = nn.Linear(32, 10)

    def forward(self, x):
        return self.cikis(self.ozellik(x))
```

Aşağıdaki parça `sinif_egit`, `clf_yukle`, `tahmin` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def sinif_egit(x, y, seed=0, epoch=60):
    torch.manual_seed(seed)
    m = Siniflandirici()
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    X = torch.as_tensor(x)
    Y = torch.as_tensor(y)
    for _ in range(epoch):
        p = torch.randperm(len(X))
        for i in range(0, len(X), 64):
            b = p[i:i + 64]
            kayip = nn.functional.cross_entropy(m(X[b]), Y[b])
            opt.zero_grad()
            kayip.backward()
            opt.step()
    m.eval()
    return m

def clf_yukle(xtr, ytr):
    """Olcum sinifiricisi: bir kez egitilir, out/clf.pt'ye yazilir."""
    yol = os.path.join(OUT, "clf.pt")
    m = Siniflandirici()
    if os.path.exists(yol):
        m.load_state_dict(torch.load(yol, weights_only=True))
    else:
        m = sinif_egit(xtr, ytr, seed=0)
        torch.save(m.state_dict(), yol)
    m.eval()
    return m

@torch.no_grad()
def tahmin(m, x):
    t = torch.as_tensor(x, dtype=torch.float32)
    return m(t).argmax(1).numpy()
```

Aşağıdaki parça `halka_veri`, `mod_olcutu` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
# ---- 2B halka verisi: 8 Gauss, yaricap 2, sigma 0.02 ----
MERKEZ = 2.0 * np.stack(
    [np.cos(2 * np.pi * np.arange(8) / 8),
     np.sin(2 * np.pi * np.arange(8) / 8)], 1)

def halka_veri(n, rng, sigma=0.02):
    k = rng.integers(0, 8, n)
    x = MERKEZ[k] + sigma * rng.standard_normal((n, 2))
    return x.astype(np.float32), k

def mod_olcutu(x, yaricap=0.2, esik=0.01):
    """Kapsanan mod sayisi ve yuksek kaliteli oran.
    Bir mod 'kapsandi' sayilir: en az esik*n ornek merkezine
    yaricap icinde duser. Kalite: herhangi bir merkeze yaricap
    icinde dusen orani."""
    d = np.linalg.norm(x[:, None, :] - MERKEZ[None], axis=2)
    en = d.argmin(1)
    yakin = d.min(1) <= yaricap
    kapsanan = 0
    for j in range(8):
        if ((en == j) & yakin).sum() >= esik * len(x):
            kapsanan += 1
    return kapsanan, float(yakin.mean())
```

Aşağıdaki betik, `k` gizil boyutu için 2, 4, 8 ve 16 değerlerinde doğrusal bir autoencoder'ı 4000 tam-toplu Adam adımında eğitir. Her `k` için PCA'nın test hatasını ve autoencoder'ın test hatasını, ayrıca iki alt uzay arasındaki en büyük **ana açıyı** (principal angle) hesaplar. Ana açı, iki uzayın ne kadar aynı olduğunun ölçüsüdür: 0 derece aynı uzay, 90 derece dik uzay demektir. Alt uzayları karşılaştırmak için `scipy.linalg.subspace_angles` kullanıyoruz.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.4: dogrusal autoencoder ile PCA ayni alt uzayi bulur mu?
Veri: load_digits (64 boyut). Her k ve tohum icin test hatasi ve
iki alt uzay arasindaki en buyuk ana aci olculur."""
import csv
import numpy as np
import torch
import torch.nn as nn
from scipy.linalg import subspace_angles
from sklearn.decomposition import PCA
from b72_veri import digits_bol, VERI

KS = [2, 4, 8, 16]
TOHUMLAR = [0, 1, 2]
ADIM = 4000

xtr, ytr, xte, yte = digits_bol(seed=0)
Xtr = torch.tensor(xtr)
Xte = torch.tensor(xte)

def dogrusal_ae(k, seed):
    torch.manual_seed(seed)
    enc = nn.Linear(64, k)
    dec = nn.Linear(k, 64)
    opt = torch.optim.Adam(
        list(enc.parameters()) + list(dec.parameters()), lr=1e-2)
    for _ in range(ADIM):
        kayip = ((dec(enc(Xtr)) - Xtr) ** 2).mean()
        opt.zero_grad()
        kayip.backward()
        opt.step()
    return enc, dec
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
satirlar = []
print("== Dogrusal AE vs PCA (test MSE, en buyuk ana aci) ==")
print("k    PCA_mse    AE_mse(ort)  AE_sapma   aci_max(ort)")
for k in KS:
    pca = PCA(n_components=k).fit(xtr)
    rec = pca.inverse_transform(pca.transform(xte))
    pca_mse = float(((rec - xte) ** 2).mean())
    ae_mse, acilar = [], []
    for s in TOHUMLAR:
        enc, dec = dogrusal_ae(k, s)
        with torch.no_grad():
            r = dec(enc(Xte)).numpy()
        ae_mse.append(float(((r - xte) ** 2).mean()))
        # Decoder agirliklari (64 x k) ile PCA bilesenleri (64 x k)
        W = dec.weight.detach().numpy()
        P = pca.components_.T
        ac = subspace_angles(W, P)
        acilar.append(float(np.degrees(ac).max()))
    m_ae, s_ae = np.mean(ae_mse), np.std(ae_mse)
    m_ac, s_ac = np.mean(acilar), np.std(acilar)
    print(f"{k:<4} {pca_mse:.6f}  {m_ae:.6f}  {s_ae:.6f}  "
          f"{m_ac:6.3f}+-{s_ac:.3f}")
    satirlar.append([k, pca_mse, m_ae, s_ae, m_ac, s_ac])

with open(VERI + "/b72_pca_ae.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["k", "pca_mse", "ae_mse", "ae_sd", "aci_deg",
                "aci_sd"])
    for r in satirlar:
        w.writerow([f"{v:.6f}" if isinstance(v, float) else v
                    for v in r])
print("CSV yazildi:", VERI + "/b72_pca_ae.csv")
```

```term
$ python b72_02_ae_pca.py
== Dogrusal AE vs PCA (test MSE, en buyuk ana aci) ==
k    PCA_mse    AE_mse(ort)  AE_sapma   aci_max(ort)
2    0.053175  0.053175  0.000001   0.037+-0.025
4    0.037942  0.037943  0.000002   0.069+-0.045
8    0.024646  0.024822  0.000246   0.346+-0.284
16   0.011609  0.011620  0.000007   0.190+-0.046
CSV yazildi: D:/Mevcut Projeler/Kitap/engine/veri/b72_pca_ae.csv
```

Çıktıda iki şey dikkat çekicidir. Birincisi, PCA ve doğrusal AE'nin test hataları neredeyse birebir aynı: `k = 4` için ikisi de 0,0379 civarında. İkincisi, en büyük ana açı her `k` için birkaç derecenin altında kalıyor; `k = 8` için ortalama 0,35 derece, tohumlar arasında 0,28 derece sapma. Ağırlıklar farklı başlatıldığında aynı alt uzaya yakınsıyor, ama bu yakınsamanın Adam'ın 4000 adımda ne kadar yakınsadığına bağlı olduğunu da unutmayalım: `k = 8` için AE'nin test hatası PCA'dan 0,00018 kadar büyük, yani eğitim tam olarak bitmemiş. Bu, öğretici bir uyarıdır: "aynı çözüm" iddiası ancak optimizasyonun yakınsadığını gösteren bir ölçümle birlikte geçerlidir.

Şekil 72.3 aynı sonucu grafikte verir.

![Şekil 72.3: Doğrusal AE ile PCA: test hatası (solda) ve alt uzay açısı (sağda)](gorseller/b72_pca_ae.png)

Derin bir autoencoder ise doğrusal olmayan bir alt uzay öğrenir. Bu, bir veri kümesinin eğri üzerinde yattığı durumda PCA'nın göremeyeceği yapıyı yakalamanın yoludur. Aynı gizil boyut `k = 8` için PCA ile derin AE'yi karşılaştıralım; derin AE 64-128-8-128-64 mimarisinde, ReLU ve son katmanda sigmoid ile çalışıyor. Bir de gürültü giderici (denoising) autoencoder deneyeceğiz: girdiye Gauss gürültüsü ekleyip temiz hedefi tahmin etmesini istiyoruz. Bu, ağın yalnızca kopyalamak değil, veri yapısını öğrenmek zorunda olmasını sağlar. Bu iki deneyi ve 72.5'teki anomali tespitini tek bir betikte topluyoruz.

::: ipucu
Gizil boyut seçimi sıkıştırma oranını ve hatayı doğrudan belirler. `k` küçükse hata büyür; `k` büyükse ağ girdiyi neredeyse olduğu gibi kopyalar ve öğrendiği bir şey kalmaz. Test kümesinde ölçmediğin bir `k` seçimine güvenme.
:::

## 72.5 Anomali tespiti: yeniden yapılandırma hatası

Bölüm 61'de anomali tespitini yoğunluk tahminiyle ve PCA'nın artık (residual) hatasıyla görmüştük. Autoencoder aynı fikri doğrudan uygular: normal veriyle eğitilmiş bir autoencoder, normal girdileri iyi yeniden üretir; normal dışı bir girdiyi ise iyi üretemez. Yeniden yapılandırma hatası, bu nedenle, bir anomali skorudur.

Bu fikrin tuzağı şudur: autoencoder'ın her girdiyi iyi yeniden üretmesi de mümkündür (kimliğe yakın bir fonksiyon öğrenebilir). Bu durumda anomali ile normal arasında bir fark kalmaz. Darboğaz ve eğitim verisinin yapısı bu tuzağı önler; yine de bunu ölçerek görmek gerekir.

Deneyimiz savunma sanayiinden esinlenen sentetik bir sensör sinyali üzerinde. Her pencere 128 örnek uzunluğunda; normal sinyal iki sinüsün toplamı, frekansları 3-5 ve 10-12 çevrim/pencere arasında rastgele seçiliyor, üzerine küçük bir Gauss gürültüsü biniyor. Anomali üç türde üretiliyor:

- **Sıçrama (spike):** tek bir noktaya 1,0 ile 1,5 arasında ani bir değer eklenir.
- **Frekans kayması:** 17 çevrimlik yeni bir bileşen eklenir; normal sinyalin frekans bandının dışındadır.
- **Yavaş kayma:** pencereye doğrusal bir trend eklenir.

Eğitim yalnızca normal pencerelerle yapılıyor. Eşik, normal doğrulama kümesinin hata dağılımının %99'udur. Test kümesinde 500 normal ve 500 anomali pencere var. Karşılaştırma için aynı gizil boyutta (8) bir PCA kullanıyoruz; PCA da yalnızca normal veriyle eğitiliyor. Ölçütler: ROC eğrisi altındaki alan (AUC), eşikteki kesinlik, geri çağırma ve F1, ayrıca her anomali türü için tespit oranı.

Aşağıdaki betik üç deneyi birleştirir: (a) derin autoencoder ile PCA karşılaştırması, (b) gürültü giderici autoencoder ve (c) sensör anomali tespiti.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.4-72.5: derin AE (load_digits), gurultu giderici AE ve
sentetik sensor sinyalinde yeniden yapilandirma hatasiyla anomali
tespiti (PCA tabanli karsilastirma ile)."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
from b72_veri import digits_bol

TOHUMLAR = [0, 1, 2]

def mlp_ae(giris, gizil, gizli=128, cikis_sig=True):
    enc = nn.Sequential(nn.Linear(giris, gizli), nn.ReLU(),
                        nn.Linear(gizli, gizil))
    son = [nn.Linear(gizil, gizli), nn.ReLU(),
           nn.Linear(gizli, giris)]
    if cikis_sig:
        son.append(nn.Sigmoid())
    return enc, nn.Sequential(*son)
```

Aşağıdaki parça `egit`, `mse` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def egit(enc, dec, X, hedef, epoch, seed, gurultu=0.0, lr=1e-3):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(list(enc.parameters()) +
                           list(dec.parameters()), lr=lr)
    n = len(X)
    for _ in range(epoch):
        p = torch.randperm(n)
        for i in range(0, n, 128):
            b = p[i:i + 128]
            g = X[b]
            if gurultu > 0:
                g = g + gurultu * torch.randn_like(g)
            kayip = ((dec(enc(g)) - hedef[b]) ** 2).mean()
            opt.zero_grad()
            kayip.backward()
            opt.step()
    return enc, dec

def mse(a, b):
    return float(((a - b) ** 2).mean())

# ---------- (a) derin AE ve PCA (k=8) ----------
xtr, ytr, xte, yte = digits_bol(seed=0)
Xtr, Xte = torch.tensor(xtr), torch.tensor(xte)
print("== (a) Derin AE (64-128-8-128-64) vs PCA k=8, test MSE ==")
pca = PCA(n_components=8).fit(xtr)
pca_mse = mse(pca.inverse_transform(pca.transform(xte)), xte)
derin = []
for s in TOHUMLAR:
    enc, dec = mlp_ae(64, 8)
    enc, dec = egit(enc, dec, Xtr, Xtr, 200, s)
    with torch.no_grad():
        derin.append(mse(dec(enc(Xte)).numpy(), xte))
print(f"PCA k=8        : {pca_mse:.5f}")
print(f"Derin AE (ort) : {np.mean(derin):.5f} +- {np.std(derin):.5f}"
      f"  (3 tohum)")
```

Aşağıdaki parça `normal_pencere` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
# ---------- (b) gurultu giderici AE ----------
print()
print("== (b) Gurultu giderici AE: gurultulu test -> temiz test ==")
sigma = 0.3
rng = np.random.default_rng(123)
gur_te = (xte + sigma * rng.standard_normal(xte.shape))
gur_te = gur_te.astype(np.float32)
Gte = torch.tensor(gur_te)
sonuc_normal, sonuc_gd = [], []
for s in TOHUMLAR:
    enc, dec = mlp_ae(64, 16, cikis_sig=True)
    enc, dec = egit(enc, dec, Xtr, Xtr, 200, s)
    with torch.no_grad():
        sonuc_normal.append(mse(dec(enc(Gte)).numpy(), xte))
    enc2, dec2 = mlp_ae(64, 16, cikis_sig=True)
    enc2, dec2 = egit(enc2, dec2, Xtr, Xtr, 200, s, gurultu=sigma)
    with torch.no_grad():
        sonuc_gd.append(mse(dec2(enc2(Gte)).numpy(), xte))
print(f"Normal AE (gurultulu girdi): {np.mean(sonuc_normal):.5f}"
      f" +- {np.std(sonuc_normal):.5f}")
print(f"Gurultu giderici AE        : {np.mean(sonuc_gd):.5f}"
      f" +- {np.std(sonuc_gd):.5f}")
print(f"Gurultulu girdinin kendisi : {mse(gur_te, xte):.5f}")

# ---------- (c) sentetik sensor sinyali: anomali tespiti ----------
L = 128
t = np.arange(L) / L

def normal_pencere(rng):
    f1 = rng.uniform(3, 5)
    f2 = rng.uniform(10, 12)
    a1 = rng.uniform(0.9, 1.1)
    a2 = rng.uniform(0.4, 0.6)
    ph = rng.uniform(0, 2 * np.pi)
    s = a1 * np.sin(2 * np.pi * f1 * t) + a2 * np.sin(
        2 * np.pi * f2 * t + ph)
    return s + rng.normal(0, 0.05, L)
```

Aşağıdaki parça `anomali_pencere`, `ae_skor` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def anomali_pencere(rng, tur):
    s = normal_pencere(rng)
    if tur == 0:      # tek noktada sicrama (spike)
        i = rng.integers(10, L - 10)
        s[i] += rng.choice([-1, 1]) * rng.uniform(1.0, 1.5)
    elif tur == 1:    # frekans kaymasi: bilesen 17 cevrime cikar
        s = s + 0.6 * np.sin(2 * np.pi * 17 * t + rng.uniform(0, 6))
    else:             # yavas kayma (dogrusal trend)
        s = s + rng.uniform(0.6, 1.0) * (t - 0.5) * 2
    return s

rng = np.random.default_rng(0)
Ntr, Nval, Nte = 2000, 500, 500
X_tr = np.stack([normal_pencere(rng) for _ in range(Ntr)])
X_val = np.stack([normal_pencere(rng) for _ in range(Nval)])
X_te_n = np.stack([normal_pencere(rng) for _ in range(Nte)])
tur_te = rng.integers(0, 3, Nte)
X_te_a = np.stack([anomali_pencere(rng, k) for k in tur_te])
X_te = np.concatenate([X_te_n, X_te_a]).astype(np.float32)
y_te = np.concatenate([np.zeros(Nte), np.ones(Nte)]).astype(int)
tur_all = np.concatenate([np.full(Nte, -1), tur_te])

Str = torch.tensor(X_tr, dtype=torch.float32)
Sval = torch.tensor(X_val, dtype=torch.float32)
Ste = torch.tensor(X_te)
ortalama = Str.mean(0)
ssd = Str.std()
Ztr = (Str - ortalama) / ssd
Zval = (Sval - ortalama) / ssd
Zte = (Ste - ortalama) / ssd

def ae_skor(enc, dec, Z):
    with torch.no_grad():
        r = dec(enc(Z))
    return ((r - Z) ** 2).mean(1).numpy()
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
print()
print("== (c) Sensor anomalisi: esik = normal dogrulamanin %99'u ==")
print(f"Egitim: {Ntr} normal pencere; test: {Nte} normal + "
      f"{Nte} anomali")
print("tur: 0 spike, 1 frekans kaymasi, 2 kayma")
print("model        AUC    prec   recall  F1    tur0  tur1  tur2")
sonuc = {"AE": [], "PCA": []}
for s in TOHUMLAR:
    enc, dec = mlp_ae(128, 8, gizli=32, cikis_sig=False)
    Zt = Ztr.clone()
    enc, dec = egit(enc, dec, Zt, Zt, 150, s, lr=1e-3)
    sk_val = ae_skor(enc, dec, Zval)
    sk_te = ae_skor(enc, dec, Zte)
    p_ae = PCA(n_components=8).fit(Ztr.numpy())
    z_val = Zval.numpy()
    z_te = Zte.numpy()
    r_val = ((p_ae.inverse_transform(p_ae.transform(z_val)) - z_val)
             ** 2).mean(1)
    r_te = ((p_ae.inverse_transform(p_ae.transform(z_te)) - z_te)
            ** 2).mean(1)
    sonuc["AE"].append((sk_val, sk_te))
    sonuc["PCA"].append((r_val, r_te))
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
for ad in ["AE", "PCA"]:
    aucs, precs, recs, f1s, turler = [], [], [], [], []
    for sval, ste in sonuc[ad]:
        esik = np.quantile(sval, 0.99)
        tahmin = (ste > esik).astype(int)
        tp = ((tahmin == 1) & (y_te == 1)).sum()
        fp = ((tahmin == 1) & (y_te == 0)).sum()
        fn = ((tahmin == 0) & (y_te == 1)).sum()
        pr = tp / max(tp + fp, 1)
        rc = tp / max(tp + fn, 1)
        f1 = 2 * pr * rc / max(pr + rc, 1e-12)
        aucs.append(roc_auc_score(y_te, ste))
        precs.append(pr)
        recs.append(rc)
        f1s.append(f1)
        turler.append([tahmin[tur_all == k].mean() for k in range(3)])
    tm = np.mean(turler, 0)
    print(f"{ad:<12} {np.mean(aucs):.3f}  {np.mean(precs):.3f}"
          f"  {np.mean(recs):.3f}   {np.mean(f1s):.3f}"
          f"  {tm[0]:.2f}  {tm[1]:.2f}  {tm[2]:.2f}")
print("(degerler 3 tohumun ortalamasi; tur-x sutunu: "
      "o turun tespit orani)")
```

```term
$ python b72_03_derin_ae_anomali.py
== (a) Derin AE (64-128-8-128-64) vs PCA k=8, test MSE ==
PCA k=8        : 0.02465
Derin AE (ort) : 0.01328 +- 0.00040  (3 tohum)

== (b) Gurultu giderici AE: gurultulu test -> temiz test ==
Normal AE (gurultulu girdi): 0.04273 +- 0.00101
Gurultu giderici AE        : 0.01939 +- 0.00010
Gurultulu girdinin kendisi : 0.09014

== (c) Sensor anomalisi: esik = normal dogrulamanin %99'u ==
Egitim: 2000 normal pencere; test: 500 normal + 500 anomali
tur: 0 spike, 1 frekans kaymasi, 2 kayma
model        AUC    prec   recall  F1    tur0  tur1  tur2
AE           0.993  0.984  0.803   0.885  0.45  1.00  1.00
PCA          0.900  0.976  0.648   0.779  0.01  1.00  1.00
(degerler 3 tohumun ortalamasi; tur-x sutunu: o turun tespit orani)
```

(a) bölümünde derin autoencoder, 8 boyutlu gizil ile PCA'nın test hatasının yaklaşık yarısını veriyor (0,0133'e karşı 0,0247). Doğrusal olmayan bir darboğaz, eğri üzerinde yatan rakam yapısını doğrusal bir düzlemden daha iyi yakalıyor.

(b) bölümünde gürültü giderici autoencoder, gürültülü girdiden (0,0901) temiz rakama 0,0194 hata ile geri dönüyor; gürültüsüz eğitilmiş normal bir autoencoder ise gürültülü girdide 0,0427 hata yapıyor. Gürültü gidericinin öğrendiği şey, gürültünün dağılımına karşı bir "filtre" olmasıdır.

(c) bölümünde AUC farkı en dikkat çekici sonuç. Yeniden yapılandırma hatasına dayanan derin autoencoder 0,993 AUC veriyor, PCA ise 0,900. Ama tür bazında bakınca tablo daha öğretici: PCA tek noktalı sıçramaların neredeyse hiçbirini yakalayamıyor (tespit oranı 0,01), autoencoder ise bunların %45'ini yakalıyor. Neden? PCA bir sıçramayı, en büyük varyans yönleri boyunca yeniden yapılandırmaya çalışır; sıçrama çok dar olduğu için bu yönlerde zaten küçük bir bileşene dönüşür ve yeniden yapılandırma hatasında belirgin bir iz bırakmaz. Doğrusal olmayan autoencoder ise normal sinyal kalıbını daha yerelde öğrendiği için sıçramayı uyumsuz bir bölge olarak görür. Frekans kaymasında ve kaymada iki yöntem de tespit oranı 1,00'e ulaşıyor; bu türler gürültüye göre çok büyük bir sapma oluşturuyor.

Bu sonuçta **dürüst sınır** de var. Eşik normal doğrulama kümesinin %99'una göre seçildi, yani yanlış alarm oranı yaklaşık %1 olmalı; ama test kümesinde kesinlik 0,984, geri çağırma 0,803. Yani kaçırdığımız anomalilerin yaklaşık beşte biri, çoğunlukla sıçramalar. Sensör sisteminde bir kaçırılan sıçrama ile bir yanlış alarm aynı maliyette değildir (Bölüm 78'de bu maliyet asimetrisini savunma bağlamında ele alacağız). Eşik, bu maliyete göre seçilmeli; %99 sabit bir kural değildir.

::: dikkat
Anomali tespitinde tek bir AUC değeri yanıltıcıdır. Sistemin işletilebilir olması için eşiği bir hedef yanlış alarm oranına göre seçmen ve her anomali türünü ayrı ayrı raporlaman gerekir. Bu bölümde yaptığımız gibi.
:::

## 72.6 Öğrenilmiş sıkıştırma ve ÖZCE köprüsü

Bölüm 51'de bilgi kuramında oran–bozulma (rate–distortion) takasını gördük: bir kaynağı `R` bit ile kodlarsan, yeniden yapılandırmadaki bozulma `D(R)` için bir alt sınır vardır ve bu sınır `R` büyüdükçe küçülür. Klasik kodlamada bu sınıra yaklaşmak için JPEG gibi sabit dönüşümler (DCT) ve entropi kodlama kullanılır. Öğrenilmiş sıkıştırmada ise dönüşümü de veri öğrenir: kodlayıcı bir autoencoder'dır, gizil kodu kuantize edilip bit olarak iletilir, alıcıdaki çözücü de görüntüyü yeniden üretir.

Burada iki ayrı "bozulma" kavramı var ve birbirini garanti etmez. Birincisi **piksel bozulması** (MSE): her pikselin ne kadar değiştiği. İkincisi **anlam bozulması**: görevin, örneğin rakamın kim olduğunun, ne kadar korunduğu. Bölüm 46'da semantik iletişimi tanıtırken bu ayrımı işaret etmiştik. Bir semantik kodekin amacı birincisini tam olarak korumak değil, ikincisini düşük bit bütçesinde korumaktır. Kendi kodeğimiz için soru şu: aynı bit bütçesinde, öğrenilmiş bir gizil kod, PCA ve DCT'ye göre piksel hatasında mı, görev doğruluğunda mı daha iyi?

Bu deney Mert'in ÖZCE projesinin **kavramsal** bir yeniden üretimidir. ÖZCE'nin dosyalarına bu bölümde erişmedik ve kopyalamadık; yalnızca bölüm boyunca anılan çerçeveyi (öğrenilmiş kodlayıcı, gizil kuantizasyon, kanal gürültüsü altında görev doğruluğu) kendi verimizde ölçtük. Sonuçlar ÖZCE hakkında bir iddia değildir; yalnızca bu çerçevenin sayısal bir örneğidir.

Deney düzeneği şöyle. Her görüntü 16 boyutlu gizil koda sıkıştırılır (kodlayıcı 64-64-16). Her gizil boyut `b` bit ile düzgün bir kuantizasyonla kodlanır; toplam bit bütçesi `R = 16 · b`'dir. Kuantizasyon aralığı eğitim kümesinin %0,1 ve %99,9 yüzdelikleriyle belirlenir. Kanal, her biti bağımsız olarak `p` olasılıkla çeviren ikili simetrik bir kanaldır (BSC). Bunun için iki temel alternatif var:

- **PCA:** aynı 16 ana bileşen katsayısı, aynı `b` bit ile kuantize edilir.
- **DCT:** 8×8 görüntünün ayrık kosinüs dönüşümü alınır, köşegen (zigzag) sırasıyla ilk 16 katsayı tutulur, aynı kuantizasyon uygulanır.

Görev doğruluğunu ölçmek için kuantizasyonsuz temiz görüntüler üzerinde (yalnızca eğitim kümesiyle) ayrı bir sınıflandırıcı eğitiyoruz. Bu sınıflandırıcı yeniden yapılandırılmış test görüntülerine uygulanıyor. Böylece bir kodek ne kadar iyi görüntü koruyorsa değil, rakamın kimliğini ne kadar koruyorsa o kadar iyi puan alıyor.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.6: ogrenilmis sikistirma (semantik kodek prototipi).
Gizli kod 16 boyutlu; her boyut b bit ile kuantize edilir; ikili
kanal her biti p olasiligiyla cevirir. Baseline: PCA (16 katsayi) ve
DCT (zigzag 16 katsayi), ayni bit butcesi. Olcu: yeniden yapilandirma
MSE'si ve ayri egitilmis siniflandiricinin dogrulugu."""
import csv
import numpy as np
import torch
import torch.nn as nn
from scipy.fft import dctn, idctn
from sklearn.decomposition import PCA
from b72_veri import digits_bol, clf_yukle, tahmin, VERI

D = 16
BITLER = [1, 2, 3, 4, 6, 8]
PS = [0.0, 0.02, 0.05]
TOHUMLAR = [0, 1, 2]

xtr, ytr, xte, yte = digits_bol(seed=0)
Xtr, Xte = torch.tensor(xtr), torch.tensor(xte)
clf = clf_yukle(xtr, ytr)

def zigzag(n=8):
    idx = [(i, j) for i in range(n) for j in range(n)]
    idx.sort(key=lambda q: (q[0] + q[1],
                            q[1] if (q[0] + q[1]) % 2 else q[0]))
    return idx

ZZ = zigzag()[:D]

def dct_katsayi(X):
    img = X.reshape(-1, 8, 8)
    c = dctn(img, axes=(1, 2), norm="ortho")
    return np.stack([c[:, i, j] for i, j in ZZ], 1)
```

Aşağıdaki parça `dct_geri`, `kuantle`, `coz`, `kanal` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def dct_geri(K):
    c = np.zeros((len(K), 8, 8))
    for n, (i, j) in enumerate(ZZ):
        c[:, i, j] = K[:, n]
    return idctn(c, axes=(1, 2), norm="ortho").reshape(len(K), 64)

def kuantle(z, lo, hi, b):
    L = 2 ** b
    u = np.clip((z - lo) / (hi - lo), 0, 1 - 1e-9)
    return np.floor(u * L).astype(np.int64)

def coz(idx, lo, hi, b):
    L = 2 ** b
    return lo + (idx + 0.5) / L * (hi - lo)

def kanal(idx, b, p, rng):
    """Her bit bagimsiz p olasiligiyla cevrilir (BSC)."""
    if p == 0:
        return idx
    out = idx.copy()
    for j in range(b):
        maske = (rng.random(idx.shape) < p).astype(np.int64)
        out ^= maske << j
    return out
```

Aşağıdaki parça `ae_egit`, `olc`, `kodek_dene` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def ae_egit(seed):
    torch.manual_seed(seed)
    enc = nn.Sequential(nn.Linear(64, 64), nn.ReLU(),
                        nn.Linear(64, D))
    dec = nn.Sequential(nn.Linear(D, 64), nn.ReLU(),
                        nn.Linear(64, 64),
                        nn.Sigmoid())
    opt = torch.optim.Adam(list(enc.parameters()) +
                           list(dec.parameters()), lr=1e-3)
    for _ in range(200):
        p = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), 128):
            b = p[i:i + 128]
            kayip = ((dec(enc(Xtr[b])) - Xtr[b]) ** 2).mean()
            opt.zero_grad()
            kayip.backward()
            opt.step()
    return enc, dec

def olc(rekons):
    mse = float(((rekons - xte) ** 2).mean())
    acc = float((tahmin(clf, rekons) == yte).mean())
    return mse, acc

def kodek_dene(ad, b, p, rng, kod_tr, kod_te, geri):
    lo = np.quantile(kod_tr, 0.001, axis=0)
    hi = np.quantile(kod_tr, 0.999, axis=0)
    idx = kuantle(kod_te, lo, hi, b)
    idx = kanal(idx, b, p, rng)
    zq = coz(idx, lo, hi, b)
    return olc(geri(zq))
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# ---- Sinirsiz referanslar ----
pca = PCA(n_components=D).fit(xtr)
pca_tr = pca.transform(xtr)
pca_te = pca.transform(xte)
print("== Referans: kuantizasyonsuz ==")
m, a = olc(pca.inverse_transform(pca_te))
print(f"PCA-16 (float)    : MSE={m:.5f}  dogruluk={a:.4f}")
dtr = dct_katsayi(xtr)
dte = dct_katsayi(xte)
m, a = olc(dct_geri(dte))
print(f"DCT-zigzag-16     : MSE={m:.5f}  dogruluk={a:.4f}")

# ---- Ogrenilmis kodek: 3 tohum ----
AE = {s: ae_egit(s) for s in TOHUMLAR}
ae_tr = {}
ae_te = {}
for s, (enc, dec) in AE.items():
    with torch.no_grad():
        ae_tr[s] = enc(Xtr).numpy()
        ae_te[s] = enc(Xte).numpy()
m_ae, a_ae = [], []
for s, (enc, dec) in AE.items():
    with torch.no_grad():
        m, a = olc(dec(enc(Xte)).numpy())
    m_ae.append(m)
    a_ae.append(a)
print(f"AE-16 (float)     : MSE={np.mean(m_ae):.5f}  "
      f"dogruluk={np.mean(a_ae):.4f}")
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# ---- Bit butcesi taramasi ----
satirlar = []
for p in PS:
    for b in BITLER:
        R = D * b
        sonuc = {"AE": [], "PCA": [], "DCT": []}
        for s in TOHUMLAR:
            rng = np.random.default_rng(100 + s)
            dec = AE[s][1]
            geri_ae = lambda z, d=dec: d(torch.tensor(
                z, dtype=torch.float32)).detach().numpy()
            sonuc["AE"].append(kodek_dene(
                "AE", b, p, rng, ae_tr[s], ae_te[s], geri_ae))
            sonuc["PCA"].append(kodek_dene(
                "PCA", b, p, rng, pca_tr, pca_te,
                pca.inverse_transform))
            sonuc["DCT"].append(kodek_dene(
                "DCT", b, p, rng, dtr, dte, dct_geri))
        for ad in ["AE", "PCA", "DCT"]:
            M = np.array([x[0] for x in sonuc[ad]])
            A = np.array([x[1] for x in sonuc[ad]])
            satirlar.append([ad, b, R, p, M.mean(), M.std(),
                             A.mean(), A.std()])

print()
print("== Bit butcesi taramasi (16 boyut, 3 tohum ortalamasi) ==")
for p in PS:
    print(f"-- kanal bit cevirme olasiligi p = {p}")
    print("b  R(bit)  AE_mse   AE_dog   PCA_mse  PCA_dog  "
          "DCT_mse  DCT_dog")
    for b in BITLER:
        r = {x[0]: x for x in satirlar if x[1] == b and x[3] == p}
        print(f"{b:<2} {D * b:<6} {r['AE'][4]:.5f}  {r['AE'][6]:.4f}"
              f"   {r['PCA'][4]:.5f}  {r['PCA'][6]:.4f}"
              f"   {r['DCT'][4]:.5f}  {r['DCT'][6]:.4f}")
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
with open(VERI + "/b72_kodek.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codec", "b", "R", "p", "mse", "mse_sd", "acc",
                "acc_sd"])
    for r in satirlar:
        w.writerow([r[0], r[1], r[2], r[3]] +
                   [f"{v:.6f}" for v in r[4:]])
print("CSV yazildi:", VERI + "/b72_kodek.csv")
```

```term
$ python b72_04_kodek.py
== Referans: kuantizasyonsuz ==
PCA-16 (float)    : MSE=0.01161  dogruluk=0.9611
DCT-zigzag-16     : MSE=0.04635  dogruluk=0.7611
AE-16 (float)     : MSE=0.00864  dogruluk=0.9472

== Bit butcesi taramasi (16 boyut, 3 tohum ortalamasi) ==
-- kanal bit cevirme olasiligi p = 0.0
b  R(bit)  AE_mse   AE_dog   PCA_mse  PCA_dog  DCT_mse  DCT_dog
1  16     0.03952  0.7574   0.05038  0.6778   0.06965  0.5389
2  32     0.01746  0.9000   0.02085  0.8889   0.05174  0.6972
3  48     0.01101  0.9380   0.01392  0.9472   0.04771  0.7444
4  64     0.00925  0.9491   0.01219  0.9500   0.04670  0.7694
6  96     0.00868  0.9481   0.01165  0.9611   0.04638  0.7556
8  128    0.00865  0.9472   0.01161  0.9611   0.04636  0.7611
-- kanal bit cevirme olasiligi p = 0.02
b  R(bit)  AE_mse   AE_dog   PCA_mse  PCA_dog  DCT_mse  DCT_dog
1  16     0.04396  0.7324   0.05598  0.6370   0.07241  0.5111
2  32     0.02724  0.8324   0.03092  0.8185   0.05834  0.6389
3  48     0.02123  0.8843   0.02655  0.8500   0.05358  0.6694
4  64     0.01987  0.8926   0.02279  0.8667   0.05312  0.7037
6  96     0.02079  0.8611   0.02251  0.8750   0.05246  0.6898
8  128    0.01901  0.8815   0.02416  0.8685   0.05334  0.6935
-- kanal bit cevirme olasiligi p = 0.05
b  R(bit)  AE_mse   AE_dog   PCA_mse  PCA_dog  DCT_mse  DCT_dog
1  16     0.05130  0.6630   0.06453  0.5676   0.07688  0.4704
2  32     0.04171  0.7231   0.04594  0.6972   0.06701  0.5620
3  48     0.03655  0.7769   0.04330  0.7361   0.06300  0.6046
4  64     0.03508  0.7917   0.03899  0.7593   0.06327  0.6065
6  96     0.03571  0.7593   0.04089  0.7361   0.06223  0.5880
8  128    0.03412  0.7704   0.04212  0.7352   0.06286  0.6231
CSV yazildi: D:/Mevcut Projeler/Kitap/engine/veri/b72_kodek.csv
```

Önce referanslara bakalım. Kuantizasyonsuz PCA-16 test hatası 0,0116, doğruluğu 0,961. Kuantizasyonsuz AE-16 hatası 0,0086, ama doğruluğu 0,947. DCT-16 ise hem hatada (0,0464) hem doğrulukta (0,761) belirgin biçimde geride. Yani autoencoder piksel hatasında en iyisi, görev doğruluğunda ise PCA'dan küçük bir miktar gerisinde. Bu ilk bulgu zaten "bit değil anlam" fikrinin basit bir uyarısıdır: piksel hatası düşük olan bir kodek, görevi her zaman daha iyi korumaz.

Bit bütçesi taramasında (kanal gürültüsüz, `p = 0`) iki farklı rejim görüyoruz. Düşük bütçede (1–3 bit/boyut, yani 16–48 bit/görüntü) autoencoder hem hatada hem doğrulukta belirgin biçimde önde: `b = 1` için doğruluk 0,757'ye karşı PCA'nın 0,678'i ve DCT'nin 0,539'u. Bütçe büyüdüğünde ise PCA'nın doğruluğu AE'yi geçiyor (`b = 4`: 0,950'ye karşı 0,949; `b = 6`: 0,961'e karşı 0,948). Bu, öğrenilmiş kodun düşük bütçede kritik bilgiyi önceliklendirdiğini, yüksek bütçede ise doğrusal bir dönüşümün (PCA) gizil uzayda daha bilgilendirici bir koordinat kurabildiğini gösterir. Bu sonuç bir "her zaman üstünlük" değil, bir bütçeye bağlı takas.

Asıl sınav kanal gürültüsüdür. Şekil 72.4'ün sağ paneli `p = 0,05` (her bit yüzde beş olasılıkla çevriliyor) için doğruluğu kesik çizgilerle gösteriyor. Bu rejimde autoencoder, `b = 4` ve üzerinde PCA'yı açık biçimde geçiyor: `b = 4` için 0,792'ye karşı 0,759; `b = 8` için 0,770'e karşı 0,735. Hata tarafında da aynı yön var: `b = 4` için MSE 0,0351 (AE) ve 0,0390 (PCA). Neden? PCA katsayıları ikili gösterimde bitlerin ağırlığı çok farklı olan ölçeklerde kodlanmıştır; yüksek anlamlı bir bitin çevrilmesi büyük bir sıçrama yaratır. Autoencoder'ın gizil koordinatları ise kuantizasyon aralığına göre daha düzenli dağılmış olabilir ve bu, gürültüye karşı daha az hassas bir temsil üretebilir. Bu bir sezgidir; kanıtlamak için kodu Gray kodlamayla ve bit düzeyinde ağırlık ayarlamasıyla yeniden denemek gerekir. Bu bölümün Kendin Yap Proje 2'ye bırakıyoruz.

Ama dikkat: AE'nin kanal dayanıklılığı sınırlıdır. `p = 0,05` ile bile doğruluk 0,79 seviyesinde kalıyor; kuantizasyonsuz 0,95'ten çok uzak. Gerçek bir sistemde bunun çözümü kanal kodlamasıdır (bit düzeyinde hata düzeltme), ya da eğitimde kanal gürültüsünü de modele katmaktır (kuantizasyon farkındalıklı eğitim). Bu, Bölüm 75'te ve Bölüm 78'de ele alınacak konulara bağlanır.

![Şekil 72.4: Bit bütçesine göre bozulma (solda) ve görev doğruluğu, kanalsız ve p = 0,05 (sağda)](gorseller/b72_kodek_oran.png)

::: ipucu
Oran–bozulma ve oran–görev eğrilerini bir arada okumak, bir kodeği değerlendirmenin doğru yoludur. Tek bir bütçede "en iyi" demek yetmez; kanal bozulmasını ve görev hedefini de eğriye koymak gerekir.
:::

::: baglanti
Bu deneyde ölçtüğümüz bit bütçesi ve bozulma takası, Bölüm 51'deki oran–bozulma çerçevesinin kavramsal bir uygulamasıdır. Bölüm 51'de bu çerçevenin ÖZCE projesiyle ilişkisine kısaca değinmiştik; bu bölüm onu sayısal bir deneyle somutlaştırıyor.
:::

## 72.7 Değişimsel otomatik kodlayıcı (VAE)

Bir autoencoder'ın gizil uzayı bir **nokta** kümesidir: her girdi tek bir `z` kodu üretir. Bu gizil uzayda rastgele bir nokta seçip çözücüye verirsen, eğitim sırasında hiç görmediğin bir "boşluğa" düşebilirsin ve anlamsız bir çıktı alırsın. Üretken model istediğimiz şey, gizil uzaydan **rastgele** örnekleme yapabilmek ve her noktanın anlamlı bir görüntü üretmesidir.

**Değişimsel otomatik kodlayıcı** (variational autoencoder, VAE) bu sorunu bir olasılık modeliyle çözer. Gizil değişkene önsel bir dağılım koyarız: `p(z) = N(0, I)`. Veri şu şekilde üretilir: önce `z ~ p(z)`, sonra `x ~ p(x|z)`. `p(x|z)` çözücüdür. Sorun, bu modelde `p(z|x)` posteriorunun ve `p(x)` marjinalinin hesaplanamamasıdır: `p(x) = ∫ p(x|z) p(z) dz` integrali pratikte çözülemez. Çözüm, `p(z|x)`'i öğrenilebilir bir `q(z|x)` ile yaklaştırmaktır.

Türetmeyi açık yazalım. Herhangi bir `q(z|x)` için:

log p(x) = E_q[log p(x|z)] − KL(q(z|x) ‖ p(z)) + KL(q(z|x) ‖ p(z|x))

Son terim negatif olmayan bir KL'dir (Bölüm 51), dolayısıyla

log p(x) ≥ E_q[log p(x|z)] − KL(q(z|x) ‖ p(z)) = ELBO(x)

Sağdaki büyüklüğe **kanıt alt sınırı** (evidence lower bound, ELBO) denir. Eşitlik yalnızca `q(z|x) = p(z|x)` olduğunda sağlanır; yani ELBO, posterior yaklaşımının ne kadar iyi olduğuna bağlı bir alt sınırdır. Eğitimde ELBO'yu maksimize ederiz. Birinci terim yeniden yapılandırmayı, ikinci terim gizil uzayın önsel dağılımdan ne kadar saptığını cezalandırır. Bu ikisi arasındaki denge VAE'nin tüm davranışını belirler.

Kodlayıcı, `q(z|x)`'i bir Gauss olarak parametrelendirir: `q(z|x) = N(μ(x), diag(σ²(x)))`. Ağ `μ(x)` ve `log σ²(x)` çıkarır. İki Gauss arasındaki KL'nin kapalı formu, Bölüm 51'de türettiğimiz gibi, dağılımın ortalamasını ve varyansını doğrudan içerir. Standart normal önselle KL şöyledir (tek boyut için):

KL(N(μ, σ²) ‖ N(0, 1)) = ½ (σ² + μ² − 1 − ln σ²)

Çok boyutta bu, boyutlar üzerinden toplanır. Bu kapalı form kodda doğrudan kullanılıyor. Bu formülü ve ELBO türetmesini aşağıdaki küçük betikte iki farklı yolla doğruluyoruz: kapalı form ile Monte Carlo tahmini, ve iki boyutlu bir doğrusal Gauss modelinde ELBO'nun log p(x)'i gerçekten alttan sınırlayıp sınırlamadığı.

Ama bir sorun var: `z` bir örnekleme işlemiyle üretilir ve örnekleme **türevlenebilir değildir**. `z ~ N(μ, σ²)` yazdığında gradyan μ ve σ'dan geçmez. Çözüm **yeniden parametrelendirme** (reparameterization trick) hilesidir: rastgeleliği dışarı çıkarırız.

z = μ + σ ⊙ ε,  ε ~ N(0, I)

Artık `z`, μ ve σ'nın türevlenebilir bir fonksiyonu; rastgelelik yalnızca ε'dedir ve ε'ye göre gradyan almayız. Bölüm 55'te otomatik türev ile zincir kuralını gördük; bu hile sayesinde gradyan, örnekleme adımının içinden hesaplanabilir.

Aşağıdaki betik üç şeyi gösterir: KL'nin kapalı formu ve Monte Carlo ile karşılaştırması, `sample()` ile `rsample()` arasındaki gradyan farkı (PyTorch'un yeniden parametrelendirmeyi kendisi nasıl yaptığı), ve ELBO'nun log p(x) altında kalıp posteriorda eşitlendiği.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.7: KL'nin kapali formu, yeniden parametrelendirme
hilesi ve ELBO'nun log p(x) alt siniri oldugunun sayisal
dogrulamasi."""
import math
import torch
from torch.distributions import Normal, kl_divergence

torch.manual_seed(0)

def kl_kapali(mu, sig):
    """KL(N(mu, sig^2) || N(0, 1)), nat cinsinden."""
    return 0.5 * (sig**2 + mu**2 - 1.0 - math.log(sig**2))

def kl_mc(mu, sig, n=2_000_000):
    """Ayni KL'yi Monte Carlo ile: E_q[log q(z) - log p(z)]."""
    q = Normal(mu, sig)
    p = Normal(0.0, 1.0)
    z = q.sample((n,))
    return (q.log_prob(z) - p.log_prob(z)).mean().item()

print("== 1. KL: kapali form, MC ve torch ==")
for mu, sig in [(1.5, 0.5), (0.0, 1.0), (-0.8, 2.0)]:
    k = kl_kapali(mu, sig)
    m = kl_mc(mu, sig)
    t = kl_divergence(Normal(mu, sig), Normal(0.0, 1.0)).item()
    print(f"mu={mu:+.2f} s={sig:.2f} kapali={k:.6f} "
          f"MC={m:.6f} torch={t:.6f}")
```

Aşağıdaki parça `rec_kapali`, `elbo` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
print()
print("== 2. Yeniden parametrelendirme: gradyan geciyor mu? ==")
mu = torch.tensor(0.5, requires_grad=True)
sig = torch.tensor(0.8, requires_grad=True)
z_s = Normal(mu, sig).sample((100_000,))
print("sample():  z.requires_grad =", z_s.requires_grad)
try:
    ((z_s - 2.0) ** 2).mean().backward()
except RuntimeError as hata:
    print("sample() ile geri yayilim: HATA ->", type(hata).__name__)

z_r = Normal(mu, sig).rsample((100_000,))
print("rsample(): z.requires_grad =", z_r.requires_grad)
kayip = ((z_r - 2.0) ** 2).mean()
kayip.backward()
print(f"d kayip/d mu  = {mu.grad.item():+.4f}  "
      f"(kapali: 2(mu-2) = -3)")
print(f"d kayip/d sig = {sig.grad.item():+.4f}  "
      f"(kapali: 2 sig = 1.6)")

print()
print("== 3. ELBO <= log p(x): tek boyutlu dogrusal Gauss ==")
x = 1.0
# Model: p(z) = N(0,1), p(x|z) = N(z,1)  =>  p(x) = N(0,2)
log_px = Normal(0.0, math.sqrt(2.0)).log_prob(torch.tensor(x)).item()
print(f"log p(x) kesin = {log_px:.6f}")

def rec_kapali(m, s):
    """E_q[log N(x; z, 1)] kapali form: E[(x-z)^2] = (x-m)^2 + s^2."""
    return -0.5 * math.log(2 * math.pi) - 0.5 * ((x - m) ** 2 + s**2)

def elbo(m, s):
    return rec_kapali(m, s) - kl_kapali(m, s)
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
q = Normal(0.3, 0.9)
z = q.rsample((1_000_000,))
rec_mc = Normal(z, 1.0).log_prob(torch.tensor(x)).mean().item()
print(f"rec MC (0.3, 0.9) = {rec_mc:.6f}  "
      f"kapali = {rec_kapali(0.3, 0.9):.6f}")

for m, s in [(0.0, 1.0), (0.3, 0.9), (0.5, 0.5**0.5), (0.8, 0.5)]:
    e = elbo(m, s)
    print(f"q: m={m:.2f} s={s:.4f} ELBO={e:.6f} "
          f"bosluk={log_px - e:.6f}")
```

```term
$ python b72_01_kl_yeniden.py
== 1. KL: kapali form, MC ve torch ==
mu=+1.50 s=0.50 kapali=1.443147 MC=1.442502 torch=1.443147
mu=+0.00 s=1.00 kapali=0.000000 MC=0.000000 torch=0.000000
mu=-0.80 s=2.00 kapali=1.126853 MC=1.124845 torch=1.126853

== 2. Yeniden parametrelendirme: gradyan geciyor mu? ==
sample():  z.requires_grad = False
sample() ile geri yayilim: HATA -> RuntimeError
rsample(): z.requires_grad = True
d kayip/d mu  = -3.0075  (kapali: 2(mu-2) = -3)
d kayip/d sig = +1.6124  (kapali: 2 sig = 1.6)

== 3. ELBO <= log p(x): tek boyutlu dogrusal Gauss ==
log p(x) kesin = -1.515512
rec MC (0.3, 0.9) = -1.568702  kapali = -1.568939
q: m=0.00 s=1.0000 ELBO=-1.918939 bosluk=0.403426
q: m=0.30 s=0.9000 ELBO=-1.624299 bosluk=0.108787
q: m=0.50 s=0.7071 ELBO=-1.515512 bosluk=0.000000
q: m=0.80 s=0.5000 ELBO=-1.702086 bosluk=0.186574
```

İlk bölüm KL'nin kapalı formunun iki yöntemle aynı çıktığını gösteriyor. Monte Carlo sapması 2·10⁶ örnekle bile 10⁻³ mertebesinde; bu, tahminin beklenen değerinin doğru olduğunu gösterir. İkinci bölümde `sample()` ile üretilen `z`'nin `requires_grad` değeri `False` çıkıyor ve geri yayılım bir `RuntimeError` veriyor. `rsample()` ise gradyan taşıyor ve μ ile σ için türevler kapalı formla (−3 ve 1,6) uyumlu, Monte Carlo gürültüsüyle birlikte (−3,0075 ve 1,6124). Bu, yeniden parametrelendirmenin tam olarak neyi çözdüğünü gösteriyor.

Üçüncü bölümde, `log p(x) = −1,515512` ile posterior `q(z|x) = N(0,5; 0,7071²)` (yani `m = 0,5`, `s = 0,7071`) için ELBO tam olarak eşitleniyor: boşluk 0. Diğer `q` seçimleri ELBO'yu daha düşük tutuyor ve boşluk pozitif. Kodun VAE'de yaptığı şey budur: ELBO'yu büyütmek, `q`'yu gerçek posteriora yaklaştırmak demektir.

::: dikkat
`rsample()` ile `sample()` arasındaki fark yalnızca bir yöntem adı değildir. VAE'nin eğitimi ile ilgili en sık yapılan hata, örnekleme adımını `sample()` ile yapıp gradyanın sessizce kaybolmasıdır. Kodda `RuntimeError` almadıysan bile gradyanın kesildiği bir yerde olabilirsin; `z.requires_grad` değerini kontrol et.
:::

### VAE'yi eğitmek ve β takası

Aşağıdaki betik, `load_digits` üzerinde VAE'yi sıfırdan eğitir. Kayıp, ikili çapraz entropi ile yeniden yapılandırma (her piksel için Bernoulli benzeri) ve KL terimlerinin toplamıdır. β-VAE'de KL terimi β ile çarpılır: `kayıp = rec + β · KL`. β büyüdükçe model gizil uzayı daha sıkı önsele zorlar; yeniden yapılandırmadan ödün verilir. Betik β ∈ {0,5; 1; 4} için 3 tohumla eğitir ve test kümesinde yeniden yapılandırma, KL, ELBO ve **aktif birim** sayısını raporlar. Aktif birim, `Var_x[μ_i(x)] > 0,01` olan gizil boyutlarıdır; aktif olmayan bir boyut posterior çöküşünün işaretidir.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.7: VAE (load_digits), beta-VAE, kosullu VAE ve gizil
uzay. Ciktilar: out/ (model, ornek) ve engine/veri (sekiller)."""
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b72_veri import digits_bol, clf_yukle, tahmin, OUT, VERI

TOHUMLAR = [0, 1, 2]
EPOCH = 300

class VAE(nn.Module):
    def __init__(self, d=8, h=256, kosul=0):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(64 + kosul, h), nn.ReLU())
        self.mu = nn.Linear(h, d)
        self.lv = nn.Linear(h, d)
        self.dec = nn.Sequential(nn.Linear(d + kosul, h), nn.ReLU(),
                                 nn.Linear(h, 64))

    def kodla(self, x, c=None):
        if c is not None:
            x = torch.cat([x, c], 1)
        h = self.enc(x)
        return self.mu(h), self.lv(h)

    def coz(self, z, c=None):
        """Logit dondurur; piksel olasiligi = sigmoid(logit)."""
        if c is not None:
            z = torch.cat([z, c], 1)
        return self.dec(z)
```

Aşağıdaki parça `kayip`, `egit`, `degerlendir` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def kayip(model, x, c, beta):
    mu, lv = model.kodla(x, c)
    # Yeniden parametrelendirme: z = mu + sigma * eps
    z = mu + torch.exp(0.5 * lv) * torch.randn_like(mu)
    logit = model.coz(z, c)
    rec = F.binary_cross_entropy_with_logits(
        logit, x, reduction="none").sum(1)
    kl = -0.5 * (1 + lv - mu ** 2 - lv.exp()).sum(1)
    return rec.mean(), kl.mean()

def egit(model, X, C, beta, seed=0, lr=1e-3):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(X)
    for _ in range(EPOCH):
        p = torch.randperm(n)
        for i in range(0, n, 128):
            b = p[i:i + 128]
            cb = None if C is None else C[b]
            rec, kl = kayip(model, X[b], cb, beta)
            loss = rec + beta * kl
            opt.zero_grad()
            loss.backward()
            opt.step()
    return model

@torch.no_grad()
def degerlendir(model, X, C=None):
    """Test kumesinde: yeniden yapilandirma (nat), KL (nat), ELBO
    (= -(rec+KL)) ve aktif birim sayisi (Var_x[mu_i(x)] > 0,01)."""
    mu, lv = model.kodla(X, C)
    rec, kl = kayip(model, X, C, 1.0)
    au = int((mu.var(0) > 0.01).sum())
    return rec.item(), kl.item(), -(rec.item() + kl.item()), au
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
xtr, ytr, xte, yte = digits_bol(seed=0)
X = torch.tensor(xtr)
Xte = torch.tensor(xte)
clf = clf_yukle(xtr, ytr)

# ---------- (a) beta-VAE: yeniden yapilandirma - KL takasi ----------
print("== (a) beta-VAE, d=8, test kumesi (3 tohum ortalamasi) ==")
print("beta  rec(nat)        KL(nat)         ELBO           AU")
for beta in [0.5, 1.0, 4.0]:
    R, K, E, A = [], [], [], []
    for s in TOHUMLAR:
        torch.manual_seed(s)
        m = egit(VAE(d=8), X, None, beta, seed=s)
        r, k, e, a = degerlendir(m, Xte)
        R.append(r)
        K.append(k)
        E.append(e)
        A.append(a)
    print(f"{beta:<5} {np.mean(R):7.2f} +- {np.std(R):5.2f}  "
          f"{np.mean(K):6.2f} +- {np.std(K):4.2f}  "
          f"{np.mean(E):8.2f}   {np.mean(A):.1f}")

# ---------- (b) kosullu VAE: sinif kosullu uretim ----------
print()
print("== (b) Kosullu VAE (beta=1, d=8): sinif dogrulugu ==")
Ctr = torch.nn.functional.one_hot(torch.tensor(ytr), 10).float()
cvae = egit(VAE(d=8, kosul=10), X, Ctr, 1.0, seed=0)
torch.save(cvae.state_dict(), OUT + "/cvae.pt")
torch.manual_seed(7)
hedef = np.repeat(np.arange(10), 100)
Ch = torch.nn.functional.one_hot(torch.tensor(hedef), 10).float()
with torch.no_grad():
    z = torch.randn(1000, 8)
    ornek_c = torch.sigmoid(cvae.coz(z, Ch)).numpy()
pred = tahmin(clf, ornek_c)
print(f"Her sinif 100 ornek: dogruluk = {(pred == hedef).mean():.4f}")
np.savez(OUT + "/cvae_ornek.npz", x=ornek_c, y=hedef)
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# ---------- (c) kosulsuz VAE (aile karsilastirmasi icin) ----------
print()
print("== (c) Kosulsuz VAE (d=8, beta=1) ==")
vae = egit(VAE(d=8), X, None, 1.0, seed=0)
torch.save(vae.state_dict(), OUT + "/vae.pt")
torch.manual_seed(11)
with torch.no_grad():
    z = torch.randn(1000, 8)
    ornek = torch.sigmoid(vae.coz(z)).numpy()
np.save(OUT + "/vae_ornek.npy", ornek)
t0 = time.perf_counter()
for _ in range(5):
    with torch.no_grad():
        _ = torch.sigmoid(vae.coz(torch.randn(1000, 8)))
ms = (time.perf_counter() - t0) / 5 / 1000 * 1e3
with open(OUT + "/zaman_vae.txt", "w") as f:
    f.write(f"{ms:.6f}")
print(f"Ornekleme suresi (CPU, ornek basina): {ms:.4f} ms")
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# ---------- (d) 2B gizil uzay, manifold ve enterpolasyon ----------
print()
print("== (d) 2B gizil VAE: manifold ve enterpolasyon ==")
v2 = egit(VAE(d=2), X, None, 1.0, seed=0)
with torch.no_grad():
    mu2, _ = v2.kodla(Xte)
    gx = np.linspace(-2, 2, 15)
    zz = torch.tensor([[gx[j], gx[i]] for i in range(15)
                       for j in range(15)], dtype=torch.float32)
    grid = torch.sigmoid(v2.coz(zz)).numpy().reshape(15, 15, 8, 8)
ia = int(np.where(yte == 0)[0][0])
ib = int(np.where(yte == 7)[0][0])
with torch.no_grad():
    ma, _ = vae.kodla(Xte[ia:ia + 1])
    mb, _ = vae.kodla(Xte[ib:ib + 1])
    ts = torch.linspace(0, 1, 10).view(-1, 1)
    zi = (1 - ts) * ma + ts * mb
    ezgi = torch.sigmoid(vae.coz(zi)).numpy().reshape(10, 8, 8)
np.savez(VERI + "/b72_vae2d.npz", mu2=mu2.numpy(),
         y2=yte, grid=grid, ezgi=ezgi, uc_a=xte[ia].reshape(8, 8),
         uc_b=xte[ib].reshape(8, 8))
r2, k2, e2, a2 = degerlendir(v2, Xte)
print(f"d=2 VAE test ELBO = {e2:.2f}, AU = {a2}")
print(f"Enterpolasyon: test ornekleri {ia} (etiket 0) ve {ib} "
      f"(etiket 7), 10 adim")
```

```term
$ python b72_05_vae.py
== (a) beta-VAE, d=8, test kumesi (3 tohum ortalamasi) ==
beta  rec(nat)        KL(nat)         ELBO           AU
0.5     18.52 +-  0.07    6.60 +- 0.10    -25.12   8.0
1.0     20.67 +-  0.11    3.51 +- 0.07    -24.18   6.3
4.0     27.21 +-  0.01    0.00 +- 0.00    -27.22   0.0

== (b) Kosullu VAE (beta=1, d=8): sinif dogrulugu ==
Her sinif 100 ornek: dogruluk = 1.0000

== (c) Kosulsuz VAE (d=8, beta=1) ==
Ornekleme suresi (CPU, ornek basina): 0.0009 ms

== (d) 2B gizil VAE: manifold ve enterpolasyon ==
d=2 VAE test ELBO = -24.69, AU = 2
Enterpolasyon: test ornekleri 24 (etiket 0) ve 0 (etiket 7), 10 adim
```

β takası tablosu öğretici. β = 0,5'te model 8 boyutun 8'ini kullanıyor (aktif birim 8,0), KL 6,6 nat, yeniden yapılandırma 18,5 nat. β = 1'de yeniden yapılandırma 20,7'ye çıkıyor, KL 3,5'e düşüyor ve 6,3 boyut aktif kalıyor. β = 4'te ise tam çöküş var: KL 0,00, aktif birim 0,0. Model gizil uzayı tamamen yok sayıyor ve her girdiye aynı ortalama rakamı üretiyor; yani bir "ortalama rakam" yeniden üreticisine dönüşüyor. Bu, **posterior çöküşü**nün ölçülebilir hâlidir. Kodeki bir boyutun çöküp çökmediğini aktif birimle takip edebilirsin.

ELBO'nun son değerine dikkat edelim. β = 1 için test ELBO'su −24,2 nat (`−(rec + KL)`), yani ELBO'nun bir alt sınır olduğunu ve yeniden yapılandırma ile KL arasındaki takasın sonucunu burada görüyoruz. ELBO bir yoğunluk değil, bir alt sınırdır; bunu raporlarken bu nedenle "alt sınır" ya da "ELBO" yazmak, "log-olabilirlik" yazmaktan farklıdır.

Şekil 72.5 eğitilmiş 2 boyutlu bir VAE'nin gizil uzayını gösterir: test örneklerinin ortalamaları sınıflarına göre renklendirilmiş (a), gizil ızgaranın çözücüyle üretilen görüntüleri (b) ve iki farklı rakam arasında doğrusal enterpolasyon (c). 2 boyutlu gizil uzayda sınıflar kısmen ayrışıyor ama üst üste biniyor; bu, çok düşük boyutun ayrım gücünü sınırladığını gösterir. Enterpolasyon, gizil uzayın sürekli olduğunu gösterir: bir rakamdan diğerine geçerken ara görüntüler anlamlı biçimde değişir.

![Şekil 72.5: 2B VAE gizil uzayı (a), gizil ızgara çözümü (b) ve iki rakam arasında enterpolasyon (c)](gorseller/b72_vae_gizil.png)

Koşullu VAE (cVAE) aynı yapıyı sınıf bilgisiyle birlikte kullanır: kodlayıcının ve çözücünün girdisine sınıfın one-hot kodu eklenir. Bu sayede modele "şu rakamı üret" diyebilirsin. Betikteki (b) bölümü her sınıf için 100 örnek üretip bir sınıflandırıcıyla kontrol eder. Bu ölçüt bir sınıf tutarlılığı ölçüsüdür, gerçekçiliği değil; sınıflandırıcının doğruluğu yüksek olabilir ama üretilen görüntüler gerçek olmayabilir. Bu ayrımı akılda tut.

::: not
Betikte VAE çıktısı olarak sigmoid ile alınan piksel olasılıklarını (ortalama görüntüleri) kullanıyoruz; ikili örnekleme (her pikseli bir Bernoulli çekimiyle belirleme) yapmıyoruz. Bu, örneklerin biraz daha "yumuşak" görünmesine yol açar ve sınıflandırıcı doğruluğunu da yükseltir. Örnekleme değişikliği sonucu etkiler; raporlarken bunu belirt.
:::

## 72.8 Çekişmeli üretken ağlar (GAN)

GAN'ın fikri bir oyundur. Üretici `G`, gizil bir `z ~ N(0, I)` gürültüsünü veri uzayına eşler. Ayırt edici `D`, bir girdinin gerçek veriden mi yoksa `G`'den mi geldiğini tahmin eder. `D` gerçeği sahteden ayırmakta iyileştikçe `G` daha gerçekçi örnek üretmeye zorlanır; `G` iyileştikçe `D` daha ince ayrım yapmak zorunda kalır. Denge noktasında `G`'nin dağılımı gerçek dağılımla çakışır ve `D` her yerde 1/2 olasılık verir.

Goodfellow ve arkadaşlarının (2014) amacı bir minimaks problemidir:

min_G max_D V(D, G) = E_{x~p_veri}[log D(x)] + E_{z~p_z}[log(1 − D(G(z)))]

Optimal ayırt ediciyi kendi başına çözebiliriz. Sabit bir `G` için `V`'nin `D(x)`'e göre türevi sıfıra eşitlenirse, her `x` için optimal ayırt edici:

D*(x) = p_veri(x) / (p_veri(x) + p_g(x))

Bu değeri `V`'ye koyduğumuzda, GAN'ın üretici tarafında minimize ettiği şeyin Jensen–Shannon ıraksamasının iki katı olduğunu görürüz (genel bilgi, Goodfellow 2014):

V(D*, G) = −log 4 + 2 JS(p_veri ‖ p_g)

JS ıraksaması, KL'nin simetrik ve sınırlı bir sürümüdür (Bölüm 51): JS(p ‖ q) = ½ KL(p ‖ m) + ½ KL(q ‖ m), m = (p + q)/2. Bu bağlantı, iki dağılım aynı olduğunda JS'nin sıfır, farklı olduğunda ise en fazla log 2 olduğunu söyler; yani GAN'ın hedefi teorik olarak anlamlıdır. Pratikte ise hedef, `D`'nin sınırlı kapasitesi ve sonlu örnekler nedeniyle yalnızca yaklaşık olarak optimizedir.

Ama üretici kaybında pratik bir sorun vardır. Minimaks biçiminde `G`, `log(1 − D(G(z)))` terimini minimize eder. Eğitimin başında `D` sahteyi kolayca ayırt eder ve `D(G(z))` çok küçüktür. Bu bölgede `log(1 − D)` fonksiyonunun türevi küçüktür: `D` kendinden emin olduğunda gradyan sıfıra yakın olur. Bu **doyma** (saturation) sorunudur. Doymayan (non-saturating) kayıp `−log D(G(z))`'yi minimize eder; aynı optimal noktaya götürür ama bu bölgede gradyanı güçlüdür.

Bu farkı sayısal olarak doğrulayalım. Ayırt edicinin ham çıktısı (logit) `l` ise `D(G(z)) = σ(l)`. Doyan kayıp `log(1 − σ(l))`'in `l`'ye göre türevi `−σ(l)`, doymayan kayıp `−log σ(l)`'nin türevi `−(1 − σ(l))`'dir. Aşağıdaki betik bu iki büyüklüğü farklı `l` değerleri için hem analitik hem otomatik türevle hesaplar (ilk tablo) ve sonra 1B ayrık bir örnekte optimal ayırt ediciyi ve JS bağlantısını doğrular (ikinci bölüm).

```python
# -*- coding: utf-8 -*-
"""Bolum 72.8: GAN. (A) doymayan kayip gradyani, (B) optimal
ayirt edici ve JS, (C) 8 Gauss halkasinda minimaks, doymayan ve
WGAN-GP egitimi; mod cokmesi olcumu (3 tohum)."""
import csv
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b72_veri import halka_veri, mod_olcutu, VERI

ZD = 8
ITER = 4000
TOHUMLAR = [0, 1, 2]
LOG = 250

# ---------- (A) doymayan kayip: gradyan karsilastirmasi ----------
print("== A. Uretici kaybi: dL/dl (l = ayirt edicinin logit'i) ==")
l = torch.tensor([-6.0, -4.0, -2.0, 0.0, 2.0], requires_grad=True)
doyan = -F.softplus(l)           # log(1 - sigmoid(l))
doymayan = F.softplus(-l)        # -log(sigmoid(l))
g1, = torch.autograd.grad(doyan.sum(), l)
g2, = torch.autograd.grad(doymayan.sum(), l)
print("   l     D(G(z))   |dL_doyan|  |dL_doymayan|")
for i in range(5):
    d = torch.sigmoid(l[i]).item()
    print(f"{l[i].item():+5.1f}  {d:9.5f}  {abs(g1[i].item()):10.5f}"
          f"  {abs(g2[i].item()):12.5f}")
```

Aşağıdaki parça `ureteci`, `ayirt_edici` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
# ---------- (B) optimal ayirt edici ve JS (1B, ayrik) ----------
print()
print("== B. Optimal ayirt edici D*(x) = p/(p+q) ve JS ==")
p = np.array([0.5, 0.3, 0.2])
q = np.array([0.1, 0.4, 0.5])
Dst = p / (p + q)
V = np.sum(p * np.log(Dst)) + np.sum(q * np.log(1 - Dst))
m = (p + q) / 2
kl = lambda a, b: np.sum(a * np.log(a / b))
JS = 0.5 * kl(p, m) + 0.5 * kl(q, m)
rng0 = np.random.default_rng(0)
Dr = rng0.uniform(1e-6, 1 - 1e-6, (20000, 3))
vals = (p * np.log(Dr)).sum(1) + (q * np.log(1 - Dr)).sum(1)
print("D* =", np.round(Dst, 4))
print(f"V(D*)          = {V:.6f}")
print(f"-log4 + 2JS    = {-np.log(4) + 2 * JS:.6f}  (JS = {JS:.6f})")
print(f"Rastgele 20000 D icinde en buyuk V = "
      f"{vals.max():.6f} <= V(D*)")

# ---------- (C) egitim: minimaks, doymayan, WGAN-GP ----------
Xall, _ = halka_veri(200000, np.random.default_rng(1))
Xall = torch.tensor(Xall)

def ureteci():
    return nn.Sequential(nn.Linear(ZD, 128), nn.ReLU(),
                         nn.Linear(128, 128), nn.ReLU(),
                         nn.Linear(128, 2))

def ayirt_edici(giris=2):
    return nn.Sequential(nn.Linear(giris, 128), nn.LeakyReLU(0.2),
                         nn.Linear(128, 128), nn.LeakyReLU(0.2),
                         nn.Linear(128, 1))
```

Aşağıdaki parça `egit` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def egit(varyant, seed, B=256):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    G, D = ureteci(), ayirt_edici()
    if varyant == "wgan":
        oG = torch.optim.Adam(G.parameters(), 1e-4, betas=(0.5, 0.9))
        oD = torch.optim.Adam(D.parameters(), 1e-4, betas=(0.5, 0.9))
    else:
        lrG = 1e-3 if varyant == "dogal_yl" else 2e-4
        oG = torch.optim.Adam(G.parameters(), lrG, betas=(0.5, 0.999))
        oD = torch.optim.Adam(D.parameters(), 2e-4,
                              betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()
    one = torch.ones(B, 1)
    zero = torch.zeros(B, 1)
    gecmis = []
    for it in range(1, ITER + 1):
        if varyant == "wgan":
            for _ in range(5):
                xr = Xall[torch.randint(0, len(Xall), (B,))]
                with torch.no_grad():
                    xf = G(torch.randn(B, ZD))
                e = torch.rand(B, 1)
                xh = (e * xr + (1 - e) * xf).requires_grad_(True)
                gr = torch.autograd.grad(D(xh).sum(), xh,
                                         create_graph=True)[0]
                gp = ((gr.norm(2, dim=1) - 1) ** 2).mean()
                kd = D(xf).mean() - D(xr).mean() + 10 * gp
                oD.zero_grad()
                kd.backward()
                oD.step()
            kg = -D(G(torch.randn(B, ZD))).mean()
            oG.zero_grad()
            kg.backward()
            oG.step()
        else:
            xr = Xall[torch.randint(0, len(Xall), (B,))]
            with torch.no_grad():
                xf = G(torch.randn(B, ZD))
            kd = bce(D(xr), one) + bce(D(xf), zero)
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
            oD.zero_grad()
            kd.backward()
            oD.step()
            lo = D(G(torch.randn(B, ZD)))
            if varyant == "doyan":
                kg = -F.softplus(lo).mean()   # minimaks: log(1-D)
            else:
                kg = bce(lo, one)             # doymayan: -log D
            oG.zero_grad()
            kg.backward()
            oG.step()
        if it % LOG == 0:
            with torch.no_grad():
                x = G(torch.randn(2000, ZD)).numpy()
            mo, hq = mod_olcutu(x)
            gecmis.append((it, mo, hq))
    with torch.no_grad():
        son = G(torch.randn(2000, ZD)).numpy()
    return son, gecmis

VARYANTLAR = ["doyan", "dogal", "dogal_yl", "wgan"]
ad = {"doyan": "minimaks (doyan)", "dogal": "doymayan",
      "dogal_yl": "doymayan, G lr=1e-3", "wgan": "WGAN-GP"}
tum = {}
satirlar = []
ornekler = {}
for v in VARYANTLAR:
    for s in TOHUMLAR:
        son, gec = egit(v, s)
        tum[(v, s)] = gec
        for it, mo, hq in gec:
            satirlar.append([v, s, it, mo, f"{hq:.4f}"])
        if s == 0:
            ornekler[v] = son
        print(f"[{ad[v]} tohum {s}] son: modes={gec[-1][1]} "
              f"hq={gec[-1][2]:.3f}", flush=True)
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
print()
print("== Son durum (4000 iterasyon, 3 tohum) ==")
print("varyant                  modes(ort+-sd)  min   hq(ort+-sd)")
for v in VARYANTLAR:
    mo = np.array([tum[(v, s)][-1][1] for s in TOHUMLAR])
    hq = np.array([tum[(v, s)][-1][2] for s in TOHUMLAR])
    print(f"{ad[v]:<24} {mo.mean():4.2f} +- {mo.std():4.2f}   "
          f"{mo.min():d}     {hq.mean():.3f} +- {hq.std():.3f}")

with open(VERI + "/b72_gan_mod.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["varyant", "tohum", "iterasyon", "modes", "hq"])
    w.writerows(satirlar)
np.savez(VERI + "/b72_gan_ornek.npz", **ornekler)
print("CSV ve ornekler yazildi.")
```

```term
$ python b72_06_gan_2d.py
== A. Uretici kaybi: dL/dl (l = ayirt edicinin logit'i) ==
   l     D(G(z))   |dL_doyan|  |dL_doymayan|
 -6.0    0.00247     0.00247       0.99753
 -4.0    0.01799     0.01799       0.98201
 -2.0    0.11920     0.11920       0.88080
 +0.0    0.50000     0.50000       0.50000
 +2.0    0.88080     0.88080       0.11920

== B. Optimal ayirt edici D*(x) = p/(p+q) ve JS ==
D* = [0.8333 0.4286 0.2857]
V(D*)          = -1.167161
-log4 + 2JS    = -1.167161  (JS = 0.109567)
Rastgele 20000 D icinde en buyuk V = -1.167849 <= V(D*)
[minimaks (doyan) tohum 0] son: modes=8 hq=0.615
[minimaks (doyan) tohum 1] son: modes=8 hq=0.658
[minimaks (doyan) tohum 2] son: modes=8 hq=0.656
[doymayan tohum 0] son: modes=8 hq=0.274
[doymayan tohum 1] son: modes=6 hq=0.794
[doymayan tohum 2] son: modes=8 hq=0.754
[doymayan, G lr=1e-3 tohum 0] son: modes=1 hq=0.027
[doymayan, G lr=1e-3 tohum 1] son: modes=0 hq=0.000
[doymayan, G lr=1e-3 tohum 2] son: modes=0 hq=0.000
[WGAN-GP tohum 0] son: modes=8 hq=0.374
[WGAN-GP tohum 1] son: modes=8 hq=0.363
[WGAN-GP tohum 2] son: modes=7 hq=0.277

== Son durum (4000 iterasyon, 3 tohum) ==
varyant                  modes(ort+-sd)  min   hq(ort+-sd)
minimaks (doyan)         8.00 +- 0.00   8     0.643 +- 0.020
doymayan                 7.33 +- 0.94   6     0.608 +- 0.237
doymayan, G lr=1e-3      0.33 +- 0.47   0     0.009 +- 0.013
WGAN-GP                  7.67 +- 0.47   7     0.338 +- 0.043
CSV ve ornekler yazildi.
```

İlk tablo doyma sorununu rakamlarla gösteriyor. `l = −6`'da ayırt edici sahteyi kesin reddediyor, `D = 0,00247`. Doyan kaybın gradyanı 0,00247, doymayan kaybın gradyanı 0,998. Yani üretici, ayırt edici en çok kendinden emin olduğu anda en az öğreniyor. Bu, GAN'ın eğitimin başında neden zorlandığını açıklar.

İkinci bölüm `p = (0,5; 0,3; 0,2)` ve `q = (0,1; 0,4; 0,5)` için optimal ayırt ediciyi `D* = (0,8333; 0,4286; 0,2857)` olarak verir. `V(D*) = −1,167161` ile `−log 4 + 2JS = −1,167161` (JS = 0,109567) eşleşiyor. Rastgele 20 000 ayırt edici denediğimizde hiçbiri bu değeri aşmıyor: en büyük değer −1,167849. Bu, D*'ın maksimum olduğunu sayısal olarak doğrular.

Asıl deney, bir GAN'ın **2B dağılımı** nasıl öğrendiğidir. Veri, yarıçapı 2 olan bir çemberin üzerine eşit aralıkla yerleştirilmiş sekiz Gauss bileşeninden oluşur (her bileşenin σ'sı 0,02). Bu dağılım, mod çöküşünü ölçmek için ideal bir oyuncaktır: sekiz "mod"u da yakalamak zorundasın, ve bir modu kaçırmak veri dağılımının önemli bir parçasını kaybetmek demektir. Bir mod, merkezine 0,2 uzaklıkta en az örneklerin %1'i (2000 örnekte 20) düşerse "kapsanmış" sayılır. Yüksek kaliteli oran, herhangi bir merkeze 0,2 içinde düşen örneklerin oranıdır.

Betik dört varyantı üç tohumla eğitir. **Minimaks (doyan)** ve **doymayan** kayıplar standart DCGAN benzeri ayarla (Adam, öğrenme oranı 2·10⁻⁴). **Doymayan, G lr=10⁻³** aynı kaybı, üreticinin öğrenme oranını beş kat büyüterek çalıştırır; bu bilinçli olarak eğitimi kararsızlaştıran bir ayardır. **WGAN-GP** (Arjovsky ve arkadaşları 2017; Gulrajani ve arkadaşları 2017) ayırt ediciyi bir eleştirmen olarak eğitir ve Wasserstein mesafesini gradyan cezasıyla yaklaşık hesaplar; her üretici adımında beş eleştirmen adımı yapılır. WGAN-GP burada genel bilgi olarak kullanılıyor; burada tam bir türetme yapmıyoruz.

Son durum tablosu (4000 üretici iterasyonu, 3 tohum):

| Varyant | Kapsanan mod (ort ± sd) | En az | Yüksek kalite oranı |
|---|---|---|---|
| Minimaks (doyan) | 8,00 ± 0,00 | 8 | 0,643 ± 0,020 |
| Doymayan | 7,33 ± 0,94 | 6 | 0,608 ± 0,237 |
| Doymayan, G lr = 10⁻³ | 0,33 ± 0,47 | 0 | 0,009 ± 0,013 |
| WGAN-GP | 7,67 ± 0,47 | 7 | 0,338 ± 0,043 |

Bu tablo üç şey söylüyor. Birincisi, minimaks ve doymayan varyantlar bu basit dağılımda sekiz modu da çoğu zaman yakalıyor; ama doymayan varyant tohum 0 ve 2'de yüksek kalite oranı bakımından çok farklı (0,274 ve 0,754): yani mod kapsamı tam olsa bile örneklerin ne kadarının modların üzerinde kaldığı tohuma çok bağlı. İkincisi, öğrenme oranını artırınca (G lr = 10⁻³) model tamamen çöküyor: üretici tek bir noktaya yakın örnekler üretiyor ve neredeyse hiçbir mod kapsanmıyor. Üçüncüsü, WGAN-GP mod kapsamında güçlü ama yüksek kalite oranında zayıf; 4000 iterasyon WGAN için muhtemelen yetersiz. Bu sonuç, GAN ailesinin "daha iyi kayıp" iddialarını kaba ölçütlerle değil, bu tür ayrıntılı tablolarla okumanın gerektiğini gösteriyor.

Şekil 72.6 eğitim boyunca mod kapsamını (üst) ve üç varyantın son örneklerini (alt) gösterir. Öğrenme oranı yüksek varyantın tek bir bölgeye sıkıştığını nokta bulutundan açıkça görürsün.

![Şekil 72.6: 8 Gauss halkasında mod kapsamı (üst) ve son örnekler (alt): minimaks, yüksek öğrenme oranlı doymayan ve WGAN-GP](gorseller/b72_gan_modcoek.png)

::: dikkat
Bir GAN'ın "çalıştığına" karar verirken tek bir görsel ya da tek bir kayıp değerine bakma. Kayıp değerleri iki ağın birbirine göre ölçüldüğü için tek başına anlamsızdır. Mod kapsamı ve kalite oranı gibi bağımsız ölçütleri birlikte kullan.
:::

### DCGAN: konvolüsyonlu üretici ve ayırt edici

Yukarıdaki 2B GAN'lar MLP idi. Görüntü için konvolüsyonlu bir mimari gerekir: üretici transpoze konvolüsyonlarla (Bölüm 66) gizil vektörü görüntüye büyütür, ayırt edici konvolüsyonlarla görüntüyü özelliğe indirger. DCGAN (Radford ve arkadaşları 2015, genel bilgi) bu mimari ailesinin standart ilk örneğidir: BatchNorm kullanılır, havuzlama yerine adımlı konvolüsyon kullanılır ve üretici çıkışında sigmoid vardır.

Aşağıdaki betik 8×8 rakamlar üzerinde küçük bir DCGAN eğitir: üretici `z (32) → 128×2×2 → 64×4×4 → 1×8×8`, ayırt edici `1×8×8 → 64×4×4 → 128×2×2 → logit`. Kayıp dogal (doymayan) üretici kaybıdır. 60 epoch sonunda ayırt edicinin gerçek örneklerde ortalama olasılığı 0,661, sahte örneklerde 0,340. Bu değerler birbirine yakın ama aynı değil: ayırt edici hâlâ bir fark görüyor, fakat ağır bir üstünlüğü yok; bu sağlıklı bir denge işaretidir.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.8: kucuk DCGAN, load_digits (8x8). Evrisimli uretici ve
ayirt edici, BatchNorm, dogal (doymayan) uretici kaybi."""
import time
import numpy as np
import torch
import torch.nn as nn
from b72_veri import digits_bol, OUT

ZD = 32
EPOCH = 60
B = 64
torch.manual_seed(0)

class Uretici(nn.Module):
    """z(32) -> 128x2x2 -> 64x4x4 -> 1x8x8 (sigmoid, [0,1])."""

    def __init__(self):
        super().__init__()
        self.lin = nn.Sequential(nn.Linear(ZD, 128 * 2 * 2),
                                 nn.BatchNorm1d(128 * 2 * 2),
                                 nn.ReLU())
        self.net = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 1, 4, 2, 1), nn.Sigmoid())

    def forward(self, z):
        h = self.lin(z).view(-1, 128, 2, 2)
        return self.net(h)

class Ayirt(nn.Module):
    """1x8x8 -> 64x4x4 -> 128x2x2 -> logit."""
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 64, 4, 2, 1), nn.LeakyReLU(0.2),
            nn.Conv2d(64, 128, 4, 2, 1), nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2), nn.Flatten(), nn.Linear(512, 1))

    def forward(self, x):
        return self.net(x)

if __name__ == "__main__":
    xtr, ytr, xte, yte = digits_bol(seed=0)
    X = torch.tensor(xtr).view(-1, 1, 8, 8)
    G, D = Uretici(), Ayirt()
    oG = torch.optim.Adam(G.parameters(), 2e-4, betas=(0.5, 0.999))
    oD = torch.optim.Adam(D.parameters(), 2e-4, betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()
    t0 = time.perf_counter()
    print("== DCGAN (digits, 8x8), 60 epoch ==")
    print("epoch  D_kayip  G_kayip  D(gercek)  D(sahte)")
    for ep in range(1, EPOCH + 1):
        p = torch.randperm(len(X))
        dk, gk, dr, df = [], [], [], []
        for i in range(0, len(X) - B + 1, B):
            xr = X[p[i:i + B]]
            z = torch.randn(B, ZD)
            xf = G(z).detach()
            lr_ = D(xr)
            lf = D(xf)
            kd = bce(lr_, torch.ones(B, 1)) + \
                bce(lf, torch.zeros(B, 1))
            oD.zero_grad()
            kd.backward()
            oD.step()
            lo = D(G(torch.randn(B, ZD)))
            kg = bce(lo, torch.ones(B, 1))   # doymayan kayip
            oG.zero_grad()
            kg.backward()
            oG.step()
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
            dk.append(kd.item())
            gk.append(kg.item())
            dr.append(torch.sigmoid(lr_).mean().item())
            df.append(torch.sigmoid(lf).mean().item())
        if ep % 10 == 0 or ep == 1:
            print(f"{ep:>5}  {np.mean(dk):7.4f}  {np.mean(gk):7.4f}"
                  f"  {np.mean(dr):9.3f}  {np.mean(df):8.3f}")
    G.eval()
    with torch.no_grad():
        ornek = G(torch.randn(1000, ZD)).view(-1, 64).numpy()
    np.save(OUT + "/dcgan_ornek.npy", ornek)
    torch.save(G.state_dict(), OUT + "/dcgan_g.pt")
    t1 = time.perf_counter()
    for _ in range(5):
        with torch.no_grad():
            _ = G(torch.randn(1000, ZD))
    ms = (time.perf_counter() - t1) / 5 / 1000 * 1e3
    with open(OUT + "/zaman_dcgan.txt", "w") as f:
        f.write(f"{ms:.6f}")
    print(f"Egitim suresi: {time.perf_counter() - t0:.1f} s")
    print(f"Ornekleme suresi (CPU, ornek basina): {ms:.4f} ms")
    print(f"Uretilen ornek: {ornek.shape}, aralik "
          f"[{ornek.min():.3f}, {ornek.max():.3f}]")
```

```term
$ python b72_07_dcgan_digits.py
== DCGAN (digits, 8x8), 60 epoch ==
epoch  D_kayip  G_kayip  D(gercek)  D(sahte)
    1   0.7810   1.5809      0.665     0.298
   10   0.9789   1.2750      0.630     0.368
   20   1.0266   1.1388      0.616     0.385
   30   1.0043   1.2024      0.640     0.370
   40   0.9120   1.2263      0.655     0.354
   50   0.9099   1.2936      0.662     0.345
   60   0.9056   1.2395      0.661     0.340
Egitim suresi: 31.0 s
Ornekleme suresi (CPU, ornek basina): 0.0106 ms
Uretilen ornek: (1000, 64), aralik [0.000, 1.000]
```

Eğitim kaybı tablosu uzun süreli dengeyi gösteriyor: 10. epochtan sonra `D_kayıp` yaklaşık 0,9–1,0 ve `G_kayıp` 1,2–1,3 aralığında kalıyor. Tek bir koşu olduğu için bu bir istatistik değil, bir gözlemdir. Ölçütleri 72.10'da, diğer ailelerle birlikte vereceğiz.

::: baglanti
DCGAN'da konvolüsyonlu üretici ve ayırt edici, Bölüm 66'daki CNN ve transpoze konvolüsyon kavramlarının doğrudan uygulamasıdır. BatchNorm'un eğitimdeki rolünü Bölüm 64'te görmüştük.
:::

### Koşullu GAN ve iyileştirmeler: kısa bakış

Koşullu GAN (cGAN, Mirza ve Osindero 2014, genel bilgi) üretici ve ayırt ediciye sınıf etiketini ekler. Üretici `G(z, c)` ile belirli bir sınıftan örnek üretebilir; ayırt edici de hem gerçekliği hem sınıfla uyumu değerlendirir. VAE'deki cVAE ile aynı fikirdir ve bu bölümde cVAE'yi ölçtük.

WGAN ve gradyan cezası 2B deneyde zaten kullanıldı. Bu ailenin bir başka önemli iyileştirmesi spektral normalizasyon ve ölçeklendirilmiş eğitimdir; bunlar ayrıntılı genel bilgi olarak kalıyor.

::: not
GAN'ın bir eksiği daha: `p(x)` değerini vermez, yani "bu örnek ne kadar olası?" sorusunu cevaplayamaz. Bu nedenle GAN'ları anomali tespitinde doğrudan kullanmak zordur; bu, gizil değişkenli ve difüzyon modellerinin belli bir avantajıdır.
:::

## 72.9 Difüzyon modelleri: gürültüyü geri almak

GAN'ın doğrudan `G(z) → x` eşlemesi, eğitimde kararsızlık ve mod çöküşü sorunlarını getirdi. Difüzyon modelleri farklı bir yoldan gider: veriyi yavaşça gürültüye gömen sabit bir **ileri süreç** tanımlar, sonra bu sürecin tersini, yani gürültüden veriye giden **ters süreci** bir ağla öğrenir. Ağın işi, her adımda eklenmiş gürültüyü tahmin etmektir. Bu küçük ve yinelemeli görev, bir GAN'ın tek hamlede yaptığı dağılım eşlemesini parçalara böler.

### İleri süreç ve kapalı form

Veri `x_0` ile başlar. `t = 1, ..., T` adımlarında her adım küçük bir gürültü ekler:

x_t = √(1 − β_t) x_{t−1} + √β_t ε_t,  ε_t ~ N(0, I)

Burada `β_t` (gürültü takvimi) her adımda eklenen gürültü miktarıdır. Her adım önceki duruma bağlıdır, ama tüm adımları tek seferde hesaplamak için kapalı bir formül vardır. `α_t = 1 − β_t` ve `ᾱ_t = Π_{s≤t} α_s` tanımlarsak:

q(x_t | x_0) = N(√ᾱ_t x_0, (1 − ᾱ_t) I)

Bu formül, tüm eğitimin bir kolaylığıdır: herhangi bir `t` için `x_t`'yi `x_0`'dan ve tek bir Gauss örneğinden doğrudan üretebiliriz. Türetme, Gauss'ların toplamının ortalama ve varyansının eklenmesine dayanır (Bölüm 49'da Gauss'ların doğrusal dönüşümünü görmüştük). Kapalı formu bu bölümde MC ile doğruluyoruz.

Takvim iki biçimde seçilebilir. **Doğrusal** takvim `β_t`'yi bir aralıkta doğrusal artırır; **kosinüs** takvimi (Nichol ve Dhariwal 2021, genel bilgi) `ᾱ_t`'yi bir kosinüs karesiyle tanımlar ve gürültüyü uç adımlarda daha yavaş ekler. Kosinüs takvimi, özellikle düşük çözünürlüklü verilerde daha iyi ayrım sağlar.

### Gürültü tahmincisi ve kayıp

Ters süreçte modelin bildiği şey `x_t` ve `t`'dir; bilinmeyen gürültü `ε`'dur. DDPM (Ho ve arkadaşları 2020, genel bilgi) bunu basit bir amaca indirir: `ε_θ(x_t, t)` ağı `ε`'yu tahmin etsin.

L = E_{t, x_0, ε} [ ||ε − ε_θ(√ᾱ_t x_0 + √(1 − ᾱ_t) ε, t)||² ]

Bu kayıp, ε'yu tahmin etmenin `x_{t−1}`'i tahmin etmekle eşdeğer olduğu bir türetmeden gelir; DDPM bu eşdeğerliği kullanıp ağırlığı basitleştirir. Kayıp, Bölüm 63'teki eğitim döngüsünün tanıdık bir hâlidir: rastgele `t` ve `ε` seçilir, bir gürültülü girdi oluşturulur, ağ tahmin eder, ortalama kare hata alınır.

Ters süreç, `ε_θ`'yı kullanarak her adımda `x_t`'den `x_{t−1}`'e geçer. DDPM'de bu, bir Gauss'tan örnek çekmek gibidir ve her adımda gürültü eklenir. Bu **ancestral örnekleme** T adım gerektirir. Deterministik bir alternatif olan DDIM (Song ve arkadaşları 2021, genel bilgi) aynı eğitilmiş ağı kullanır, ama gürültü eklemez ve adımların bir alt kümesinde ilerleyebilir; bu da örneklemeyi hızlandırır.

Aşağıdaki ortak modül (`b72_difuzyon.py`) iki biçimi de içerir: takvim üretimi, sinüzoidal zaman gömmesi, 2B veriler için MLP ve `load_digits` için küçük bir U-Net (Bölüm 67'deki U-Net'in 8×8 ölçeğinde bir sürümü), eğitim döngüsü ve iki örnekleme yöntemi. Ortak kod burada, ilk kullanımından önce veriliyor.

```python
# -*- coding: utf-8 -*-
"""Gurultu giderme difuzyon modeli icin ortak parcalar: takvim,
gurultu tahmincisi aglari, egitim ve iki ornekleme yontemi
(DDPM ve DDIM). t = 0 temiz veri, t = T tam gurultu."""
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

def zamanlama(T, tur="lineer"):
    """beta_t, alfa_t, abar_t dizileri; indeks t = 0..T.
    beta[0] kullanilmaz (x_0 icin yok)."""
    if tur == "lineer":
        b = np.linspace(1e-4, 0.2, T)
    else:
        adim = np.arange(T + 1) / T
        f = np.cos((adim + 0.008) / 1.008 * np.pi / 2) ** 2
        ab = f / f[0]
        b = np.minimum(1 - ab[1:] / ab[:-1], 0.999)
    beta = np.concatenate([[0.0], b])
    alfa = 1.0 - beta
    alfa[0] = 1.0
    abar = np.cumprod(alfa)
    return beta, alfa, abar

def sinus_gomme(t, dim):
    """Adim numarasi icin sinuzoidal zaman gomulmesi."""
    yari = dim // 2
    f = torch.exp(-math.log(10000.0) * torch.arange(yari) / yari)
    a = t.float()[:, None] * f[None]
    return torch.cat([torch.sin(a), torch.cos(a)], 1)

class MLP2D(nn.Module):
    """2B veri icin gurultu tahmincisi. nc>0 ise sinif kosulu
    (nc indeksi 'kosulsuz' anahtarıdır)."""
```

Aşağıdaki parça `Blok`, `UNet8` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
    def __init__(self, tdim=32, nc=0, h=256):
        super().__init__()
        self.tdim = tdim
        self.nc = nc
        self.cemb = nn.Embedding(nc + 1, tdim) if nc > 0 else None
        giris = 2 + tdim + (tdim if nc > 0 else 0)
        self.net = nn.Sequential(
            nn.Linear(giris, h), nn.SiLU(),
            nn.Linear(h, h), nn.SiLU(),
            nn.Linear(h, h), nn.SiLU(),
            nn.Linear(h, 2))

    def forward(self, x, t, c=None):
        parca = [x, sinus_gomme(t, self.tdim)]
        if self.cemb is not None:
            parca.append(self.cemb(c))
        return self.net(torch.cat(parca, 1))

class Blok(nn.Module):
    def __init__(self, cin, cout, tch):
        super().__init__()
        self.c1 = nn.Conv2d(cin, cout, 3, padding=1)
        self.n1 = nn.GroupNorm(8, cout)
        self.t = nn.Linear(tch, cout)
        self.c2 = nn.Conv2d(cout, cout, 3, padding=1)
        self.n2 = nn.GroupNorm(8, cout)

    def forward(self, x, te):
        h = F.silu(self.n1(self.c1(x)))
        h = h + self.t(te)[:, :, None, None]
        return F.silu(self.n2(self.c2(h)))

class UNet8(nn.Module):
    """8x8 goruntuler icin kucuk U-Net: 8x8 -> 4x4 -> 8x8, atlama
    baglantisi, zaman gomulmesi her blokta eklenir."""
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
    def __init__(self, k=32, tdim=64):
        super().__init__()
        self.tdim = tdim
        self.tm = nn.Sequential(nn.Linear(tdim, 128), nn.SiLU(),
                                nn.Linear(128, 128))
        self.giris = nn.Conv2d(1, k, 3, padding=1)
        self.b1 = Blok(k, k, 128)
        self.asagi = nn.Conv2d(k, 2 * k, 4, 2, 1)
        self.b2 = Blok(2 * k, 2 * k, 128)
        self.yukari = nn.ConvTranspose2d(2 * k, k, 4, 2, 1)
        self.b3 = Blok(2 * k, k, 128)
        self.cikis = nn.Conv2d(k, 1, 3, padding=1)

    def forward(self, x, t, c=None):
        te = self.tm(sinus_gomme(t, self.tdim))
        h1 = self.b1(self.giris(x), te)
        h2 = self.b2(self.asagi(h1), te)
        u = self.yukari(h2)
        h3 = self.b3(torch.cat([u, h1], 1), te)
        return self.cikis(h3)
```

Aşağıdaki parça `egit`, `eps_tahmin` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
def egit(model, veri, T, abar, iters, batch=512, lr=1e-3,
         etiket=None, p_dusur=0.1, seed=0, nc=0):
    """Basitlestirilmis kayip: ||eps - eps_teta(x_t, t)||^2.
    etiket verilirse kosullu egitim; kosulsuz anahtar nc'dir."""
    torch.manual_seed(seed)
    ab = torch.tensor(abar, dtype=torch.float32)
    X = torch.as_tensor(veri, dtype=torch.float32)
    Y = None if etiket is None else torch.as_tensor(etiket)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(X)
    kayip_gecmisi = []
    for it in range(iters):
        i = torch.randint(0, n, (batch,))
        x0 = X[i]
        t = torch.randint(1, T + 1, (batch,))
        eps = torch.randn_like(x0)
        a = ab[t].view(-1, *([1] * (x0.dim() - 1)))
        xt = a.sqrt() * x0 + (1 - a).sqrt() * eps
        c = None
        if Y is not None:
            c = Y[i].clone()
            c[torch.rand(batch) < p_dusur] = nc
        tahmin = model(xt, t, c)
        kayip = F.mse_loss(tahmin, eps)
        opt.zero_grad()
        kayip.backward()
        opt.step()
        kayip_gecmisi.append(kayip.item())
    return kayip_gecmisi

@torch.no_grad()
def eps_tahmin(model, x, t, c=None, w=0.0, nc=None):
    """Sinifsiz yonlendirme: w>0 ise (1+w) e(x,c) - w e(x,null)."""
    if c is None or w == 0.0:
        return model(x, t, c)
    ec = model(x, t, c)
    eu = model(x, t, torch.full_like(c, nc))
    return (1 + w) * ec - w * eu
```

Aşağıdaki parça `ornekle_ddpm` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
@torch.no_grad()
def ornekle_ddpm(model, n, sekil, T, beta, abar, c=None, w=0.0,
                 nc=None, clip=None, anlik=None, seed=0):
    """Ancestral DDPM ornekleme: T adim, her adimda gurultu.
    clip verilirse kirpma x_0 tahmininde yapilir
    (standart uygulama)."""
    torch.manual_seed(seed)
    x = torch.randn(n, *sekil)
    for t in range(T, 0, -1):
        tt = torch.full((n,), t, dtype=torch.long)
        eps = eps_tahmin(model, x, tt, c, w, nc)
        x0 = (x - math.sqrt(1 - abar[t]) * eps) / math.sqrt(abar[t])
        if clip is not None:
            x0 = x0.clamp(-clip, clip)
        ap = abar[t - 1]
        c0 = math.sqrt(ap) * beta[t] / (1 - abar[t])
        ct = math.sqrt(1 - beta[t]) * (1 - ap) / (1 - abar[t])
        x = c0 * x0 + ct * x
        if t > 1:
            var = beta[t] * (1 - ap) / (1 - abar[t])
            x = x + math.sqrt(var) * torch.randn_like(x)
        if anlik is not None:
            anlik(t, x)
    return x
```

Aşağıdaki parça `ornekle_ddim` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
@torch.no_grad()
def ornekle_ddim(model, n, sekil, T, abar, S, c=None, w=0.0,
                 nc=None, clip=None, seed=0):
    """DDIM (eta = 0): deterministik; T adimin S'lik alt kumesinde."""
    torch.manual_seed(seed)
    taus = [0] + list(np.round(np.linspace(0, T, S + 1)[1:])
                      .astype(int))
    x = torch.randn(n, *sekil)
    for i in range(S, 0, -1):
        t, s = taus[i], taus[i - 1]
        tt = torch.full((n,), t, dtype=torch.long)
        eps = eps_tahmin(model, x, tt, c, w, nc)
        x0 = (x - math.sqrt(1 - abar[t]) * eps) / math.sqrt(abar[t])
        if clip is not None:
            x0 = x0.clamp(-clip, clip)
        x = math.sqrt(abar[s]) * x0 + math.sqrt(1 - abar[s]) * eps
    return x
```

### 2B halkada difüzyon: süreci gözle izlemek

Önce 2B sekiz Gauss halkası üzerinde küçük bir difüzyon modeli eğitelim. Bu veri 72.8'de GAN için kullandığımız veriyle aynıdır, böylece karşılaştırma yapabiliriz. Betik şunları yapar. (A) Doğrusal ve kosinüs takvimlerinde `ᾱ_t` değerlerini verir, ileri sürecin kapalı formunu MC ile doğrular: `x_0 = (2, 0)` ve `t = 50` için örneklerin ortalaması ve varyansı formülle uyuşuyor. (B) `T = 100` adımlık doğrusal takvim (β ∈ [10⁻⁴, 0,2]) ile MLP gürültü tahmincisini 15 000 iterasyonda eğitir. (C) DDPM ve üç DDIM adım sayısıyla 2000 örnek üretir ve mod kapsamını ölçer.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.9: 2B halka uzerinde difuzyon. (A) takvimler ve ileri
surecin kapali formu, (B) gurultu tahmincisi egitimi, (C) DDPM ve
DDIM ornekleme, mod kapsami. Ciktilar engine/veri/b72_diff2d.npz."""
import math
import numpy as np
import torch
torch.set_num_threads(2)
from b72_veri import halka_veri, mod_olcutu, VERI, OUT
from b72_difuzyon import (zamanlama, MLP2D, egit, ornekle_ddpm,
                          ornekle_ddim)

T = 100
ITER = 15000
torch.manual_seed(0)

# ---------- (A) takvimler ve ileri surecin kapali formu ----------
beta_l, alfa_l, abar_l = zamanlama(T, "lineer")
beta_k, alfa_k, abar_k = zamanlama(T, "kosinus")
print("== A. Gurultu takvimleri: abar_t = prod(1 - beta_s) ==")
print("t     lineer abar_t   kosinus abar_t")
for t in [1, 10, 25, 50, 75, 100]:
    print(f"{t:<4}  {abar_l[t]:.6f}      {abar_k[t]:.6f}")
print(f"beta_1..beta_T araligi (lineer): {beta_l[1]:.4f} .. "
      f"{beta_l[T]:.4f}")
print(f"abar_T lineer = {abar_l[T]:.2e}  (sinyal neredeyse yok)")
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# Kapali form dogrulamasi: q(x_t|x_0) ortalama = sqrt(abar) x0,
# varyans = 1 - abar
t = 50
x0 = np.array([2.0, 0.0], dtype=np.float32)
rng = np.random.default_rng(0)
eps = rng.standard_normal((200000, 2)).astype(np.float32)
xt = math.sqrt(abar_l[t]) * x0 + math.sqrt(1 - abar_l[t]) * eps
print()
print(f"== Kapali form kontrolu: t={t}, x0={x0.tolist()} ==")
print("ortalama MC:", xt.mean(0).round(4).tolist())
print("ortalama kapali:",
      (math.sqrt(abar_l[t]) * x0).round(4).tolist())
print("varyans MC:", xt.var(0).round(4).tolist())
print(f"varyans kapali: {1 - abar_l[t]:.4f}")

# ---------- (B) egitim ----------
xr, _ = halka_veri(20000, np.random.default_rng(2), sigma=0.02)
model = MLP2D(tdim=32)
print()
print(f"== B. Gurultu tahmincisi egitimi: {ITER} iterasyon ==")
kg = egit(model, xr, T, abar_l, ITER, batch=512, lr=1e-3, seed=0)
print(f"kayip ort. ilk 500: {np.mean(kg[:500]):.4f}  "
      f"son 500: {np.mean(kg[-500:]):.4f}")
torch.save(model.state_dict(), OUT + "/diff2d.pt")
```

Aşağıdaki parça `anlik` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
# ---------- (C) ornekleme ve mod kapsami ----------
model.eval()
N = 2000
print()
print("== C. Ornekleme (2000 ornek; "
      "mod = merkeze 0,2 icinde >=%1) ==")
print("yontem            adim   modes   hq (merkeze 0,2 icinde)")
rows = []
x_ddpm = ornekle_ddpm(model, N, (2,), T, beta_l, abar_l,
                      clip=3.0, seed=1)
mo, hq = mod_olcutu(x_ddpm.numpy())
print(f"DDPM (ancestral)  {T:>4}   {mo:>3}     {hq:.3f}")
rows.append(("DDPM", T, mo, hq))
for S in [10, 20, 100]:
    xd = ornekle_ddim(model, N, (2,), T, abar_l, S, clip=3.0, seed=1)
    mo, hq = mod_olcutu(xd.numpy())
    print(f"DDIM (eta=0)      {S:>4}   {mo:>3}     {hq:.3f}")
    rows.append(("DDIM", S, mo, hq))

# ---------- Figur verisi: ileri ve ters surec ----------
ring, _ = halka_veri(500, np.random.default_rng(5), sigma=0.02)
fwd_t = [0, 25, 50, 75, 100]
fwd = []
for t in fwd_t:
    e = np.random.default_rng(10 + t).standard_normal(ring.shape)
    fwd.append(math.sqrt(abar_l[t]) * ring
               + math.sqrt(1 - abar_l[t]) * e)
rev_t = [100, 75, 50, 25, 1]
rev = {}

def anlik(tt, x):
    if tt in rev_t:
        rev[tt] = x.numpy().copy()
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
_ = ornekle_ddpm(model, 500, (2,), T, beta_l, abar_l, clip=3.0,
                 anlik=anlik, seed=2)
np.savez(VERI + "/b72_diff2d.npz",
         fwd=np.stack(fwd).astype(np.float32),
         rev=np.stack([rev[t] for t in rev_t]).astype(np.float32),
         rev_t=np.array(rev_t), fwd_t=np.array(fwd_t),
         ring=ring)
import csv
with open(VERI + "/b72_diff2d_adim.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "modes", "hq"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], f"{r[3]:.4f}"])
print("Ciktilar yazildi.")
```

```term
$ python b72_08_diff_2d.py
== A. Gurultu takvimleri: abar_t = prod(1 - beta_s) ==
t     lineer abar_t   kosinus abar_t
1     0.999900      0.999369
10    0.911686      0.972093
25    0.538718      0.847012
50    0.076876      0.493844
75    0.002697      0.144272
100   0.000021      0.000000
beta_1..beta_T araligi (lineer): 0.0001 .. 0.2000
abar_T lineer = 2.14e-05  (sinyal neredeyse yok)

== Kapali form kontrolu: t=50, x0=[2.0, 0.0] ==
ortalama MC: [0.5558000206947327, -0.0008999999845400453]
ortalama kapali: [0.5544999837875366, 0.0]
varyans MC: [0.9261999726295471, 0.9251000285148621]
varyans kapali: 0.9231

== B. Gurultu tahmincisi egitimi: 15000 iterasyon ==
kayip ort. ilk 500: 0.3462  son 500: 0.1923

== C. Ornekleme (2000 ornek; mod = merkeze 0,2 icinde >=%1) ==
yontem            adim   modes   hq (merkeze 0,2 icinde)
DDPM (ancestral)   100     8     0.980
DDIM (eta=0)        10     8     0.769
DDIM (eta=0)        20     8     0.902
DDIM (eta=0)       100     8     0.964
Ciktilar yazildi.
```

Takvim tablosu kosinüs ile doğrusal arasındaki farkı gösteriyor. Doğrusal takvimde `t = 50`'de `ᾱ` 0,077 kalır, yani veri yalnızca yüzde yedi kadar sinyal taşıyor; kosinüs takvimde aynı noktada 0,494. Kosinüs takvimi gürültüyü adımların ortasında daha dengeli dağıtıyor. `T = 100` için doğrusal takvimde `ᾱ_T = 2,1·10⁻⁵`: son durumda sinyal neredeyse sıfır, yani ters sürecin başlangıç noktası gerçekten saf gürültüdür. Bu koşul önemli: `ᾱ_T` yeterince küçük değilse, örneklemeye saf gürültüden başlamak bir tutarsızlık yaratır.

Kapalı form kontrolü `t = 50` için ortalama `0,5545`'i (formül) ve MC'de `0,5558`'i veriyor; varyans formül `0,9231`, MC `0,9262`. 200 000 örnekle MC hatası 10⁻³ mertebesinde olduğu için bu eşleşme kapalı formun doğru olduğunu gösterir.

Eğitim kaybı 0,346'dan 0,192'ye iniyor: model gürültüyü giderek daha iyi tahmin ediyor. Ama kaybın kendisi örnek kalitesi hakkında doğrudan bilgi vermez; asıl ölçüt mod kapsamı ve kalite oranıdır. DDPM (T = 100) 2000 örneğin %98,0'ini bir modun 0,2 yakınına yerleştiriyor ve sekiz modu da kapsıyor. DDIM ile adım sayısı 10'dan 20'ye ve 100'e çıktığında kalite oranı 0,769'den 0,902'ye ve 0,964'e yükseliyor. DDIM'in az adımda kaliteyi kaybetmesi, deterministik bir ODE çözümünün kaba adımlarda hataya açık olmasıyla tutarlıdır.

Şekil 72.7 bu sürecin iki yönünü gösterir: üst sıra ileri süreci, `t = 0`'da halkadan başlayıp `t = 100`'de neredeyse saf gürültüye dönüşümü; alt sıra ters süreci, `t = 100`'de gürültüden başlayıp `t = 1`'de halkaya geri dönüşü gösterir. Ters sürecin ara adımlarında örnekler önce kaba bir daire oluşturur, sonra modlar ayrışır. Bu evrimi görmek, difüzyonun "yavaş yavaş netleşme" sezgisini somutlaştırır.

![Şekil 72.7: 2B halka üzerinde ileri (üst) ve ters (alt) süreç: t = 0, 25, 50, 75, 100 ve t = 100, 75, 50, 25, 1](gorseller/b72_difuzyon_2d.png)

### Sınıf kosullu yönlendirme: sınıfsız yönlendirme

Difüzyon modellerinin bir başka güçlü özelliği **yönlendirmedir** (guidance). Model bir koşul `c` (örneğin hangi moda ait olduğu) ile eğitilebilir; bu koşul örneklemede kullanılır. Sınıfsız yönlendirme (classifier-free guidance, Ho ve Salimans 2022, genel bilgi) ayrı bir sınıflandırıcıya ihtiyaç duymadan koşulun etkisini güçlendirir. Eğitimde koşul rastgele bir oranda (burada %10) bir "kosulsuz" simgesiyle değiştirilir; böylece aynı ağ hem koşullu hem koşulsuz tahmin yapabilir. Örneklemede tahmin şöyle birleştirilir:

ε̃ = (1 + w) ε_θ(x_t, t, c) − w ε_θ(x_t, t, ∅)

`w = 0` yalnızca koşullu tahmindir; `w > 0` koşulun etkisini güçlendirir. Bu, koşullu dağılımdan daha "keskin" örnekler üretme eğilimindedir ama çeşitliliği azaltabilir ve aşırı `w` örnekleri veri dağılımının dışına itebilir. Aşağıdaki deney bunu 2B halkada ölçer. Her hedef mod için 250 örnek üretiyoruz; isabet hedef moda en yakın ve 0,2 içinde olan örneklerin oranıdır. `r_ort` ve `r_sd` ise hedef moda uzaklığın ortalaması ve sapmasıdır; veri dağılımında bu değerler yaklaşık 0,025 ve 0,015'tir (σ = 0,02 için).

```python
# -*- coding: utf-8 -*-
"""Bolum 72.9: kosullu difuzyon ve sinifsiz yonlendirme (classifier-
free guidance) 2B halka uzerinde. Kosul: hedef mod (0..7); kosulsuz
anahtar: 8. Egitimde kosul %10 oraninda dusurulur."""
import csv
import numpy as np
import torch
from b72_veri import halka_veri, mod_olcutu, MERKEZ, VERI, OUT
from b72_difuzyon import (zamanlama, MLP2D, egit, ornekle_ddpm)

T = 100
NC = 8
ITER = 15000
torch.manual_seed(0)

beta, alfa, abar = zamanlama(T, "lineer")
X, k = halka_veri(20000, np.random.default_rng(3), sigma=0.02)
model = MLP2D(tdim=32, nc=NC)
print(f"== Kosullu egitim: {ITER} iterasyon, kosul dusurme = %10 ==")
kg = egit(model, X, T, abar, ITER, batch=512, lr=1e-3,
          etiket=k, p_dusur=0.1, seed=0, nc=NC)
print(f"kayip ort. ilk 500: {np.mean(kg[:500]):.4f}  "
      f"son 500: {np.mean(kg[-500:]):.4f}")
torch.save(model.state_dict(), OUT + "/cfg2d.pt")
model.eval()
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# Her hedef mod icin 250 ornek; isabet = en yakin merkez hedef ve
# merkeze 0,2 icinde.
print()
print("== Yonlendirme olcegi w: hedef moda uzaklik ==")
print("(veri: sigma=0.02; radyal ort. ~0,025, sd ~0,015)")
print("w     isabet        hq      r_ort (hedef)  r_sd (hedef)")
satirlar = []
for w in [0.0, 1.0, 3.0]:
    isabet, hqs, ro, rs = [], [], [], []
    for h in range(NC):
        c = torch.full((250,), h, dtype=torch.long)
        x = ornekle_ddpm(model, 250, (2,), T, beta, abar, c=c, w=w,
                         nc=NC, clip=3.0, seed=100 + h).numpy()
        d = np.linalg.norm(x[:, None, :] - MERKEZ[None], axis=2)
        en = d.argmin(1)
        yakin = d.min(1) <= 0.2
        isabet.append(float(((en == h) & yakin).mean()))
        hqs.append(float(yakin.mean()))
        dh = np.linalg.norm(x - MERKEZ[h], axis=1)
        sec = dh <= 0.2
        ro.append(float(dh[sec].mean()))
        rs.append(float(dh[sec].std()))
    print(f"{w:<4}  {np.mean(isabet):.3f} +- {np.std(isabet):.3f}"
          f"  {np.mean(hqs):.3f}  {np.mean(ro):.4f}         "
          f"{np.mean(rs):.4f}")
    satirlar.append([w, f"{np.mean(isabet):.4f}",
                     f"{np.mean(hqs):.4f}",
                     f"{np.mean(ro):.4f}", f"{np.mean(rs):.4f}"])

with open(VERI + "/b72_cfg2d.csv", "w", newline="",
          encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["w", "isabet", "hq", "r_ort", "r_sd"])
    wr.writerows(satirlar)
print("CSV yazildi.")
```

```term
$ python b72_09_cfg_2d.py
== Kosullu egitim: 15000 iterasyon, kosul dusurme = %10 ==
kayip ort. ilk 500: 0.1400  son 500: 0.0357

== Yonlendirme olcegi w: hedef moda uzaklik ==
(veri: sigma=0.02; radyal ort. ~0,025, sd ~0,015)
w     isabet        hq      r_ort (hedef)  r_sd (hedef)
0.0   1.000 +- 0.000  1.000  0.0266         0.0116
1.0   1.000 +- 0.000  1.000  0.0387         0.0090
3.0   0.984 +- 0.026  0.984  0.0635         0.0274
CSV yazildi.
```

Sonuç beklenenden farklı ve öğretici. Koşullu model (`w = 0`) hedef modu neredeyse kusursuz buluyor: isabet 1,000, uzaklık ortalaması 0,0266 (veri ile uyumlu). `w = 1` uzaklığı 0,0387'ye çıkarıyor; `w = 3` ise 0,0635 ve sapma 0,0274 ile örnekleri merkezden belirgin biçimde uzaklaştırıyor, isabet de 0,984'e düşüyor. Yani bu basit 2B veride yönlendirme keskinleştirmiyor; aşırı yönlendirme örnekleri veri manifolduna dışarıdan iten bir kayma yaratıyor. Bu, yönlendirmenin bir "kalite düğmesi" olmadığını, bir takas olduğunu gösterir: `w` büyüdükçe koşula uyum artabilir ama dağılım sadakati bozulur. Gerçek görüntülerde bu takası ölçmek için ayrı bir kalite ölçütü (ör. mini-FID) ve çeşitlilik ölçütü birlikte kullanılmalıdır.

::: dikkat
Yönlendirme ölçeği `w`'yi, bir görüntünün "daha iyi" göründüğüne bakarak seçme. Bu, çeşitliliği ve dağılım sadakatini sessizce kaybetmene yol açar. `w`'yi her zaman hem koşula uyum hem de dağılım ölçütleriyle birlikte seç.
:::

### Digits üzerinde difüzyon: U-Net ve adım sayısı

2B veride tek bir sayıyla konuşabiliriz; gerçek bir veri kümesinde ise örnekler bir ızgara olarak görülür ve kaliteyi ölçmek zorlaşır. Burada `load_digits` üzerinde küçük bir U-Net (228 161 parametre) ile 200 adımlık kosinüs takvimi kullanıyoruz. Veri `[−1, 1]` aralığına ölçeklenir. Eğitim 6000 iterasyon (batch 128) sürer.

Ölçütler bu bölümde tanımlanan ortak fonksiyonla (`tam_olcut`) hesaplanır: mini-FID (gerçek eğitim kümesine göre), kesinlik ve geri çağırma, sınıflandırıcı entropisi (en fazla log₂ 10 = 3,32 bit; yüksekse sınıflar dengeli), ezber oranı ve ornekleme süresi. Test kümesi (360 örnek) ezber karşılaştırması için kullanılır.

```python
# -*- coding: utf-8 -*-
"""Uretken model olcutleri (mini-FID, kesinlik/geri cagirma,
ezberleme). Ozellikler, b72_veri'deki sinif-landiricinin
gizli katmanindan (32 boyut) alinir."""
import numpy as np
import torch
from scipy import linalg
from scipy.spatial.distance import cdist

@torch.no_grad()
def ozellik(model, x):
    t = torch.as_tensor(x, dtype=torch.float32)
    return model.ozellik(t).numpy()

def frechet(f1, f2):
    """Frechet (FID) mesafesi: |m1-m2|^2 + tr(S1+S2-2(S1 S2)^1/2)."""
    m1, m2 = f1.mean(0), f2.mean(0)
    s1 = np.cov(f1, rowvar=False)
    s2 = np.cov(f2, rowvar=False)
    # Tekil kovaryans olabilir (olu ozellik boyutlari): kucuk bir
    # kosegen ekleme standart uygulamadir.
    off = 1e-6 * np.eye(s1.shape[0])
    kok, _ = linalg.sqrtm((s1 + off) @ (s2 + off), disp=False)
    if np.iscomplexobj(kok):
        kok = kok.real
    return float(((m1 - m2) ** 2).sum() + np.trace(s1 + s2 - 2 * kok))

def kesinlik_geri_cagirma(gercek, sahte, k=3):
    """Kynkaanniemi (2019) tarzi kNN tabanli kesinlik ve geri
    cagirma. Her nokta icin k. komsu uzakligi 'yaricap' olur;
    kesinlik: sahte orneklerin gercek topluluk toplarinda oranı."""
    def yaricap(a):
        d = cdist(a, a)
        np.fill_diagonal(d, np.inf)
        return np.sort(d, axis=1)[:, k - 1]
```

Aşağıdaki parça `en_yakin`, `entropi`, `tam_olcut` tanımlarını içerir; önceki parçada gelen değişkenler bu tanımlarda kullanılır.

```python
    def kapsama(a, b, ra):
        d = cdist(b, a)
        return float((d <= ra[None, :]).any(axis=1).mean())

    ra = yaricap(gercek)
    rb = yaricap(sahte)
    return kapsama(gercek, sahte, ra), kapsama(sahte, gercek, rb)

def en_yakin(a, b):
    """a'daki her ornegin b icindeki en yakin komsu uzakligi."""
    return cdist(a, b).min(axis=1)

def entropi(etiketler, sinif=10):
    p = np.bincount(etiketler, minlength=sinif) / len(etiketler)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())

def tam_olcut(x, xtr, clf, xte):
    """Uretilen ornekler x (n, 64, [0,1]) icin tek seferde olcutler.
    Referans: egitim kumesi xtr. Ezber orani: uretilen orneklerin
    egitime en yakin uzakliginin medyani / test orneklerinin egitime
    en yakin uzakliginin medyani (~1: ezber yok; <<1: ezber var)."""
    import b72_veri
    fx = ozellik(clf, x)
    ftr = ozellik(clf, xtr)
    p, r = kesinlik_geri_cagirma(ftr, fx)
    yhat = b72_veri.tahmin(clf, x)
    ezber = float(np.median(en_yakin(x, xtr)) /
                  np.median(en_yakin(xte, xtr)))
    return {"fid": frechet(fx, ftr), "precision": p, "recall": r,
            "entropi": entropi(yhat), "ezber": ezber}
```

```python
# -*- coding: utf-8 -*-
"""Bolum 72.9: load_digits uzerinde kucuk U-Net ile DDPM egitimi ve
DDIM ile adim sayisina gore kalite. Olcutler: mini-FID, kesinlik/
geri cagirma, sinif entropisi, ezber orani ve ornekleme suresi."""
import csv
import time
import numpy as np
import torch
from b72_veri import digits_bol, clf_yukle, OUT, VERI
from b72_difuzyon import zamanlama, UNet8, egit, ornekle_ddpm, \
    ornekle_ddim
from b72_metrik import tam_olcut

T = 200
ITER = 6000
N = 1000
torch.manual_seed(0)

xtr, ytr, xte, yte = digits_bol(seed=0)
clf = clf_yukle(xtr, ytr)
beta, alfa, abar = zamanlama(T, "kosinus")
net = UNet8(k=32)
print("abar_T (kosinus, T=200) =", f"{abar[T]:.3e}")
print("U-Net parametre sayisi:",
      sum(p.numel() for p in net.parameters()))
print(f"== DDPM egitimi: kosinus takvimi, T={T}, {ITER} iterasyon ==")
Xs = (xtr * 2 - 1).reshape(-1, 1, 8, 8)
kg = egit(net, Xs, T, abar, ITER, batch=128, lr=2e-3, seed=0)
print(f"kayip ort. ilk 500: {np.mean(kg[:500]):.4f}  "
      f"son 500: {np.mean(kg[-500:]):.4f}")
torch.save(net.state_dict(), OUT + "/ddpm_unet.pt")
net.eval()

def geri(x):
    """[-1,1] uzayindan [0,1] piksel uzayina."""
    return ((x.numpy() + 1) / 2).clip(0, 1).reshape(len(x), 64)
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
satirlar = []
print()
print("== Ornekleme yontemi ve adim sayisi (N=1000) ==")
print("yontem      adim  mini-FID  kesin.  geri-c.  "
      "entropi  ezber  ms/ornek")
ornek_ddpm = None
for yontem, S in [("DDPM", T), ("DDIM", 5), ("DDIM", 10),
                  ("DDIM", 20), ("DDIM", 50), ("DDIM", 100),
                  ("DDIM", 200)]:
    t0 = time.perf_counter()
    if yontem == "DDPM":
        x = ornekle_ddpm(net, N, (1, 8, 8), T, beta, abar, clip=1.0,
                         seed=1)
    else:
        x = ornekle_ddim(net, N, (1, 8, 8), T, abar, S, clip=1.0,
                         seed=1)
    ms = (time.perf_counter() - t0) / N * 1e3
    g = geri(x)
    o = tam_olcut(g, xtr, clf, xte)
    print(f"{yontem:<10} {S:>4}  {o['fid']:8.2f}  "
          f"{o['precision']:.3f}"
          f"   {o['recall']:.3f}   {o['entropi']:.3f}"
          f"  {o['ezber']:.3f}"
          f"  {ms:7.3f}")
    satirlar.append([yontem, S, f"{o['fid']:.4f}",
                     f"{o['precision']:.4f}", f"{o['recall']:.4f}",
                     f"{o['entropi']:.4f}", f"{o['ezber']:.4f}",
                     f"{ms:.4f}"])
    if yontem == "DDPM":
        ornek_ddpm = g
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
np.save(OUT + "/ddpm_ornek.npy", ornek_ddpm)
with open(OUT + "/zaman_ddpm.txt", "w") as f:
    f.write(satirlar[0][-1])
with open(VERI + "/b72_adim_kalite.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "fid", "precision", "recall",
                "entropi", "ezber", "ms"])
    w.writerows(satirlar)
print("CSV yazildi:", VERI + "/b72_adim_kalite.csv")
```

```term
$ python b72_10_ddpm_digits.py
abar_T (kosinus, T=200) = 6.072e-08
U-Net parametre sayisi: 228161
== DDPM egitimi: kosinus takvimi, T=200, 6000 iterasyon ==
kayip ort. ilk 500: 0.2157  son 500: 0.1279

== Ornekleme yontemi ve adim sayisi (N=1000) ==
yontem      adim  mini-FID  kesin.  geri-c.  entropi  ezber  ms/ornek
DDPM        200      2.80  0.912   0.875   3.299  0.954   13.661
DDIM          5      5.16  0.870   0.795   3.288  1.023    0.533
DDIM         10      3.16  0.848   0.866   3.304  1.011    0.840
DDIM         20      2.43  0.847   0.914   3.304  1.033    1.993
DDIM         50      1.92  0.807   0.939   3.303  1.104    4.727
DDIM        100      2.12  0.757   0.949   3.306  1.196    7.908
DDIM        200      3.39  0.681   0.969   3.298  1.312   17.098
CSV yazildi: D:/Mevcut Projeler/Kitap/engine/veri/b72_adim_kalite.csv
```

Tablo iki şey gösteriyor. Birincisi, DDPM (200 adım, ancestral) 2,80 mini-FID ile DDIM'in 50 adımlık sürümüyle (1,92) yakın ama daha kötü; DDIM'de en iyi nokta 50 adım civarıdır (100 adımda 2,12, 200 adımda 3,39), adım sayısı arttıkça kalite bir noktadan sonra yine düşer. Bu bir çelişki değil: DDIM ile 200 adım yaklaşık ODE çözümüdür ve gürültü tahmini hatası birikir; ayrıca mini-FID'in özellik uzayı için kullanılan sınıflandırıcı da küçük ve kendi ölçümünde zayıftır. İkincisi, adım sayısı arttıkça geri çağırma yükseliyor (0,866'dan 0,969'a) ama kesinlik düşüyor (0,848'den 0,681'e). Yani daha çok adım, daha geniş bir dağılımı kapsıyor ama örneklerin daha fazlası gerçek dağılımın dışına çıkıyor. Bu, kesinlik–geri çağırma takasının yöntem seçiminde nasıl göründüğünü açıkça gösterir.

Ezber oranı 0,95–1,31 arasında; yani üretilen örnekler eğitim kümesine test örneklerinden daha yakın değil. Bu, modelin eğitim örneklerini ezberlemediğinin bir kanıtıdır. Ama oran 1,3'ü aşmaya başladığında (DDIM 200) bu, üretilen örneklerin eğitime test örneklerinden bile daha uzak olduğu anlamına gelir; bu durumda da modelin veri dağılımını kapsamadığı düşünülebilir.

Süre sütunu, ancestral DDPM'in (200 ağ değerlendirmesi) DDIM-5'e göre yaklaşık 26 kat daha yavaş olduğunu gösteriyor (13,66 ms ile 0,53 ms örnek başına). Bu, CPU ve toplu işlem ile ölçülmüş bir değerdir; GPU'da oran farklı olabilir.

Şekil 72.8 üç ailenin ve gerçek test örneklerinin 16'şar örneğini yan yana gösterir: gerçek (solda), VAE, DCGAN ve DDPM.

![Şekil 72.8: Aynı veri üzerinde gerçek örnekler, VAE, DCGAN ve DDPM örnekleri](gorseller/b72_digits_uretim.png)

Adım sayısı–kalite ilişkisini bir grafikte görmek için Şekil 72.9'a bakalım: solda DDIM'in mini-FID'i (log ölçekli adım ekseninde) ve DDPM noktası, sağda kesinlik ve geri çağırma.

![Şekil 72.9: DDIM adım sayısına göre mini-FID (solda) ve kesinlik–geri çağırma (sağda)](gorseller/b72_adim_kalite.png)

::: not
Bu bölümde FID'in "düşük olması" için ayrı bir kural yoktur; mini-FID aynı sınıflandırıcıyla aynı veri kümesinde karşılaştırıldığında anlamlıdır. Farklı özellik çıkarıcılarla ya da farklı veri bölmeleriyle hesaplanmış iki değeri doğrudan karşılaştırma.
:::

## 72.10 Aileleri karşılaştırmak: aynı veri, dört ölçüt

Şimdi üç ailenin, VAE, DCGAN ve DDPM'in, aynı veri kümesinde ve aynı ölçütlerle karşılaştırmasını yapalım. Her aileden 1000 örnek alınıyor; gerçek test kümesi (360 örnek) referans satırı olarak ekleniyor. Ölçüt olarak mini-FID, kesinlik, geri çağırma, sınıf entropisi, ezber oranı ve örnek başına süre kullanıyoruz. Süre, her aile için toplu (1000 örnek) üretimde ölçüldü: VAE tek bir çözücü geçişi, DCGAN tek bir üretici geçişi, DDPM ise 200 adımlık ağ değerlendirmesi.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.10: uretken model aileleri (VAE, DCGAN, DDPM) ayni veri
(digits) uzerinde; mini-FID, kesinlik/geri cagirma, sinif entropisi,
ezber orani ve ornekleme suresi.
Gercek test kumesi referans satiri."""
import csv
import numpy as np
from b72_veri import digits_bol, clf_yukle, OUT, VERI
from b72_metrik import tam_olcut

xtr, ytr, xte, yte = digits_bol(seed=0)
clf = clf_yukle(xtr, ytr)

def sure(ad):
    with open(OUT + "/zaman_%s.txt" % ad) as f:
        return float(f.read())

ailer = [
    ("VAE (d=8)", np.load(OUT + "/vae_ornek.npy"), sure("vae")),
    ("DCGAN", np.load(OUT + "/dcgan_ornek.npy"), sure("dcgan")),
    ("DDPM (T=200)", np.load(OUT + "/ddpm_ornek.npy"), sure("ddpm")),
    ("Gercek test", xte, 0.0),
]

print("== Ailer karsilastirmasi (digits, N=1000; test icin N=360) ==")
print("aile            mini-FID  kesin.  geri-c.  "
      "entropi  ezber  ms/ornek")
satirlar = []
for ad, x, ms in ailer:
    o = tam_olcut(x, xtr, clf, xte)
    print(f"{ad:<15} {o['fid']:8.2f}  {o['precision']:.3f}   "
          f"{o['recall']:.3f}   {o['entropi']:.3f}  {o['ezber']:.3f}"
          f"  {ms:.4f}")
    satirlar.append([ad, f"{o['fid']:.4f}", f"{o['precision']:.4f}",
                     f"{o['recall']:.4f}", f"{o['entropi']:.4f}",
                     f"{o['ezber']:.4f}", f"{ms:.6f}"])
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
with open(VERI + "/b72_aileler.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["aile", "fid", "precision", "recall", "entropi",
                "ezber", "ms"])
    w.writerows(satirlar)

# Izgara: her aileden 16 ornek + 16 gercek (figur icin)
rng = np.random.default_rng(0)
gercek = xte[rng.choice(len(xte), 16, replace=False)]
np.savez(VERI + "/b72_digits_izgara.npz",
         vae=ailer[0][1][:16].reshape(16, 8, 8),
         dcgan=ailer[1][1][:16].reshape(16, 8, 8),
         ddpm=ailer[2][1][:16].reshape(16, 8, 8),
         gercek=gercek.reshape(16, 8, 8))
print("CSV ve izgara yazildi.")
```

```term
$ python b72_11_aileler.py
== Ailer karsilastirmasi (digits, N=1000; test icin N=360) ==
aile            mini-FID  kesin.  geri-c.  entropi  ezber  ms/ornek
VAE (d=8)          10.44  0.831   0.384   3.269  1.099  0.0009
DCGAN               1.86  0.547   0.928   3.298  1.373  0.0106
DDPM (T=200)        2.80  0.912   0.875   3.299  0.954  13.6615
Gercek test         0.70  0.883   0.923   3.319  1.000  0.0000
CSV ve izgara yazildi.
```

| Aile | mini-FID ↓ | Kesinlik ↑ | Geri çağırma ↑ | Entropi | Ezber | ms/örnek |
|---|---|---|---|---|---|---|
| VAE (d = 8) | 10,44 | 0,831 | 0,384 | 3,269 | 1,099 | 0,0009 |
| DCGAN | 1,86 | 0,547 | 0,928 | 3,298 | 1,373 | 0,0106 |
| DDPM (T = 200) | 2,80 | 0,912 | 0,875 | 3,299 | 0,954 | 13,661 |
| Gerçek test (referans) | 0,70 | 0,883 | 0,923 | 3,319 | 1,000 | — |

Tablo, tek bir ölçütün hiçbir ailenin tamamını anlatamadığını gösteriyor. VAE'nin mini-FID'i en yüksek (10,44): örnekleri bulanık ve gerçek dağılımdan uzak. Ama kesinliği 0,831 ve geri çağırması 0,384: düşük geri çağırma, VAE'nin dağılımın bazı bölgelerini üretemediğini (ortalama görüntüye çekilme) gösterir. DCGAN'ın mini-FID'i (1,86) en düşük üretilen aileler arasında, geri çağırması (0,928) çok yüksek; ama kesinliği 0,547. Yani DCGAN geniş bir kapsama sahip, fakat örneklerinin önemli bir kısmı gerçek dağılımın dışında. Bu, GAN'larda kalite ile kapsamın ayrı yönler olduğunu ve burada kapsama ile kalitenin dengesinin kaydırıldığını gösterir. DDPM, dört ölçütün en dengelisi: kesinlik 0,912 (gerçek test ile yakın), geri çağırma 0,875, mini-FID 2,80. Bunun bedeli süre: örnek başına 13,7 ms, yani VAE'nin yaklaşık 15 000 katı (CPU, toplu).

Ezber sütunu da dikkat çekici: DCGAN'ın 1,373 değeri, üretilen örneklerin eğitim kümesine test kümesinden daha uzak olduğunu söylüyor. Yani DCGAN ezberlemiyor; ama 1,37 aynı zamanda eğitim dağılımının dışına savrulmanın işareti olabilir. Ezber göstergesi tek başına bir güvenlik kriteri değildir; kesinlik ile birlikte okunmalıdır.

Entropi sütunu sınıf dengesini ölçer. Dört ailenin de entropisi 3,27–3,32 arasında, yani üretilen örnekler sınıflar arasında dengeli. Bu, mod çöküşünün sınıf düzeyindeki bir biçimi olan "tek sınıf üretme"nin burada olmadığını gösterir. Ama sınıf dengesi, bir sınıf içindeki çeşitliliği ölçmez; bu nedenle kesinlik ve geri çağırma ile birlikte okunmalıdır.

::: dikkat
Bu tabloda her aile tek bir tohumla eğitildi (DCGAN ve DDPM için). Farklar tohum değişimi ile değişebilir; bu bölümün 2B GAN deneyinde tohum sapması (örneğin doymayan varyantta 0,274 ile 0,754 arasında kalite oranı) bunu açıkça gösteriyor. Aileler arası kesin bir sıralama iddiası için tohum sayısını artır.
:::

Şekil 72.10 aynı sonuçları dört panelde gösterir.

![Şekil 72.10: Üç üretken aile ve gerçek test kümesi: mini-FID, kesinlik, geri çağırma ve örnek başına süre](gorseller/b72_aile_karsilastirma.png)

## 72.11 Sentetik veriyle veri artırma ve sorumlu kullanım

Üretken modellerin en pratik kullanımlarından biri **veri artırmadır** (data augmentation): az sayıda gerçek örnekle eğitilmiş bir sınıflandırıcıya sentetik örnek eklemek. Savunma sanayiinde bu, nadir bir hedef sınıfı (ör. belirli bir İHA tipinin nadir bir görünümü) için gerçek veri toplamanın zor olduğu durumlarda değerlidir. Ama sentetik veri sihirli değildir; etkisi ölçülmelidir.

Deney şöyle. Eğitim kümesinin %10'u (144 örnek, sınıf tabakalı) ile bir sınıflandırıcı eğitiyoruz. Üç koşul ekliyoruz: (B) cVAE'den sınıf başına 50 etiketli örnek (500 toplam); (C) DDPM'den üretilmiş örnekler, ama DDPM etiketsiz olduğu için etiketleri, yalnızca %10'luk alt kümeyle eğitilmiş ayrı bir sınıflandırıcıyla verilir ve yalnızca güven değeri 0,9'un üstündeki örnekler alınır (en fazla 500). Karşılaştırma için tüm eğitim kümesiyle (%100) eğitilmiş referans da var. Test 360 gerçek örnektir. Üç tohum (alt küme seçimi ve eğitim) için ortalama ve sapma verilir.

Önemli bir ayrıntı: etiketleyici yalnızca küçük alt kümeyle eğitilir. Tam eğitim kümesiyle eğitilmiş bir etiketleyici kullansaydık, etiket bilgisi sızmış olurdu ve sonuç geçersiz olurdu. Bu, gerçek bir sistemde veri sızıntısını (Bölüm 54) önlemenin tipik bir örneğidir.

```python
# -*- coding: utf-8 -*-
"""Bolum 72.12: sentetik veriyle veri artirma. Az veri (%10 = 144
ornek) sinifiricisi; (B) cVAE ornekleri (etiketli), (C) DDPM
ornekleri (etiketsiz; kucuk alt kume ile etiketlenir, guven > 0,9).
Test: 360 gercek ornek. 3 tohum."""
import csv
import numpy as np
from sklearn.model_selection import train_test_split
from b72_veri import digits_bol, sinif_egit, tahmin, OUT, VERI

xtr, ytr, xte, yte = digits_bol(seed=0)
cv = np.load(OUT + "/cvae_ornek.npz")
ddpm = np.load(OUT + "/ddpm_ornek.npy")
TOHUMLAR = [0, 1, 2]
rows = {"A: yalniz gercek (%10)": [], "B: + cVAE (500, etiketli)": [],
        "C: + DDPM (etiketlenmis, guven>0,9)": [],
        "D: tam egitim (%100, referans)": []}
kabul = []
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
for s in TOHUMLAR:
    sub_x, _, sub_y, _ = train_test_split(
        xtr, ytr, train_size=0.1, stratify=ytr, random_state=s)
    # cVAE: sinif basina 50 ornek
    idx = np.concatenate([np.where(cv["y"] == c)[0][:50]
                          for c in range(10)])
    cx, cy = cv["x"][idx], cv["y"][idx]
    # DDPM: alt kumeyle egitilmis etiketleyici, guven > 0,9
    etik = sinif_egit(sub_x, sub_y, seed=s)
    import torch
    with torch.no_grad():
        p = torch.softmax(etik(torch.tensor(ddpm)), 1).numpy()
    ok = p.max(1) > 0.9
    dx, dy = ddpm[ok][:500], p.argmax(1)[ok][:500]
    kabul.append(int(ok.sum()))
    kosullar = {
        "A: yalniz gercek (%10)": (sub_x, sub_y),
        "B: + cVAE (500, etiketli)": (
            np.concatenate([sub_x, cx]), np.concatenate([sub_y, cy])),
        "C: + DDPM (etiketlenmis, guven>0,9)": (
            np.concatenate([sub_x, dx]), np.concatenate([sub_y, dy])),
        "D: tam egitim (%100, referans)": (xtr, ytr),
    }
    for ad, (x, y) in kosullar.items():
        m = sinif_egit(x, y, seed=s)
        rows[ad].append(float((tahmin(m, xte) == yte).mean()))
    print(f"tohum {s}: DDPM guven>0,9 kabul = {ok.sum()} / 1000",
          flush=True)
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
print()
print("== Sinif dogrulugu (test 360, 3 tohum) ==")
out = []
for ad, v in rows.items():
    v = np.array(v)
    print(f"{ad:<38} {v.mean():.4f} +- {v.std():.4f}")
    out.append([ad, f"{v.mean():.4f}", f"{v.std():.4f}"])
print("DDPM kabul sayilari:", kabul)
with open(VERI + "/b72_artirma.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kosul", "dogruluk", "sd"])
    w.writerows(out)
print("CSV yazildi.")
```

```term
$ python b72_12_veri_artirma.py
tohum 0: DDPM guven>0,9 kabul = 444 / 1000
tohum 1: DDPM guven>0,9 kabul = 367 / 1000
tohum 2: DDPM guven>0,9 kabul = 377 / 1000

== Sinif dogrulugu (test 360, 3 tohum) ==
A: yalniz gercek (%10)                 0.8796 +- 0.0293
B: + cVAE (500, etiketli)              0.9213 +- 0.0086
C: + DDPM (etiketlenmis, guven>0,9)    0.8824 +- 0.0198
D: tam egitim (%100, referans)         0.9694 +- 0.0023
DDPM kabul sayilari: [444, 367, 377]
CSV yazildi.
```

Sonuçlar iki açıdan öğretici. cVAE örnekleri (etiketli) doğruluğu %88,0'den %92,1'e çıkarıyor (sapma 0,9 puan); bu, 144 gerçek örneğe sınıf başına 50 sentetik örnek eklemenin gerçek bir kazanım sağladığını gösteriyor. Ama tam eğitim (%96,9) ile arasında hâlâ belirgin bir fark var; sentetik veri gerçek veriyi tam olarak yerine koymaz. DDPM'den etiketlenmiş örnekler ise kazanç sağlamıyor (88,24 ± 1,98; yalnız-gerçek taban çizgisi 87,96 ± 2,93; fark tohum sapmasının içinde kalıyor). Neden? DDPM örneklerinin 1000'de yalnızca 367–444'ü 0,9 güven eşiğini geçiyor ve bu eşiği geçenler sınıfları dengeli dağılmamış olabilir; ayrıca etiketleyici %10'luk kümeyle eğitildiği için kendi hatalarını örneklere aktarıyor. Yani sentetik verinin kalitesi kadar, etiketinin güvenilirliği de belirleyici.

Bu sonuç, veri artırmada bir kural koyuyor: sentetik örneğin **etiket doğruluğu**, sayısı kadar önemlidir. Etiketi bilinen bir üretici (cVAE) bu avantajı sağlar; etiketsiz bir üretici, etiketleme hatasını da sisteme sokar.

### Sorumlu kullanım: sahte içerik, işaretleme ve doğrulama

Üretken modeller, gerçekçi ama sahte görüntü, ses ve video üretmeyi kolaylaştırır. Bunun iki yönü var. Birincisi, **derin sahte** (deepfake) üretimi: kimliği taklit eden ya da olmayan bir olayı gösteren içerik. Savunma ve kamu güvenliği bağlamında bu, dezenformasyon ve operasyonel aldatma riski demektir. İkincisi, bu içeriğin **tespit edilmesi**: üretilmiş içeriği ayırt eden sınıflandırıcılar, ama bu bir silahlanma yarışıdır; üretici gelişir, tespitçi de geliştirilmek zorunda kalır.

Bir teknik çözüm olarak **filigranlama** (watermarking) kavramı var: üretilen içeriğe, insanın algılamadığı ama bir doğrulayıcının okuyabildiği bir işaret gömülür. Filigran, üretim sırasında (ör. modelin çıktısına) ya da üretimden sonra eklenebilir. Filigranın dayanıklılığı, sıkıştırmaya ve düzenlemeye karşı ne kadar dayandığına bağlıdır. Bu, genel bilgi düzeyinde bir kavramdır; bu bölümde bir filigran uygulamıyoruz.

Savunma sanayiinde üretken modellerin meşru kullanımı da önemlidir: simülasyon için sentetik sensör verisi üretmek ve sistemi uç durumlarda test etmek. Bu kullanımın bir koşulu vardır: sentetik verinin gerçek dağılımı temsil ettiği **doğrulanmalıdır**. Bu bölümdeki ölçütler (mini-FID, kesinlik, geri çağırma, ezber) tam olarak bu doğrulamanın araçlarıdır. Sentetik veriyle eğitilmiş bir sistemin gerçek sahada başarısızlığı, sentetik verinin dağılım sadakatsizliğinden kaynaklanabilir; bu yüzden doğrulama adımı atlanmamalıdır.

::: dikkat
Bu bölümdeki yöntemler herkese açık tekniklerdir ve burada yalnızca bir kütüphane sınıflandırıcısının eğitim verisini genişletmek için kullanılıyor. Gerçek kişilerin yüzlerini, seslerini ya da kimliklerini taklit eden bir sistem kurmak bu bölümün kapsamının dışındadır ve bu tür uygulamaları önermiyoruz.
:::

## Çözümlü Örnekler

Aşağıdaki dört örnek artan zorlukta. Her birinde önce elle, sonra bilgisayarla kontrol ediyoruz. Örneklerdeki sayılar, bu bölümdeki betiklerin ve `b72_13_ornek_dogrula.py`'nin çıktısıyla birebir uyuşur.

### Örnek 1 (★): İki Gauss arasında KL

`q = N(1,5; 0,5²)` ve `p = N(0; 1)` için KL(q ‖ p) değerini hesapla. Bu, VAE'nin kayıp teriminin tek boyuttaki hâlidir.

**Adım 1 — Anla.** İstenen `KL(q ‖ p)`, `q`'nun ortalaması `μ = 1,5`, standart sapması `σ = 0,5` (varyansı `σ² = 0,25`). Önsel `p` standart normal. Sıralama önemlidir: KL asimetriktir.

**Adım 2 — Örnekle.** Önce bu değerleri yerine koyabileceğimiz kapalı formu düşünelim: `½ (σ² + μ² − 1 − ln σ²)`.

**Adım 3 — Kaba çöz.** `σ² = 0,25`, `μ² = 2,25`, `ln 0,25 = −1,386294`. Parantez içi: `0,25 + 2,25 − 1 + 1,386294 = 2,886294`. Yarısı: `1,443147`.

**Adım 4 — Örüntü.** Formül ancak `μ = 0` ve `σ = 1` olduğunda sıfır verir; her sapma pozitif katkı yapar. Çarpan ½ dışında her terim ya bir kareden (μ² ve σ²) ya da `−ln σ²`'dan gelir. `σ` küçüldükçe `−ln σ²` büyür: dar bir posterior önselden çok uzak demektir.

**Adım 5 — İyileştir.** Tersi yön olan `KL(p ‖ q)` farklı bir değer verir; bu yüzden VAE'de yön `KL(q ‖ p)`'dir. Kapalı formu bu yönde kullanmak doğrudur.

**Adım 6 — Doğrula.** Elle sonuç `1,443147`. Bilgisayar kapalı form `1,443147`, Monte Carlo (2 milyon örnek) `1,442502`, `torch.distributions.kl_divergence` `1,443147`.

| Adım | Girdi | Ara değer | Sonuç |
|---|---|---|---|
| Kapalı form, σ² | σ = 0,5 | 0,25 | — |
| μ² | μ = 1,5 | 2,25 | — |
| −ln σ² | σ² = 0,25 | 1,386294 | — |
| Parantez | 0,25 + 2,25 − 1 + 1,386294 | 2,886294 | — |
| KL | ½ · 2,886294 | — | 1,443147 |
| Monte Carlo | 2·10⁶ örnek | — | 1,442502 |

**Bunu AI'sız yazabilir misin?** `N(−1; 2²)` ile `N(0; 1)` arasındaki KL'yi kapalı formla hesapla ve elde ettiğin değeri MC ile doğrula.

### Örnek 2 (★★): Gürültü takvimi ve ileri sürecin ortalaması

`β_1 = 0,1` ve `β_2 = 0,2` olan iki adımlık bir takvimde, `x_0 = 2` için `q(x_1 | x_0)` ve `q(x_2 | x_0)` dağılımlarını bul.

**Adım 1 — Anla.** İstenen, `x_1` ve `x_2`'nin koşullu ortalaması ve varyansı. Kapalı form `q(x_t | x_0) = N(√ᾱ_t x_0, (1 − ᾱ_t))` idi.

**Adım 2 — Örnekle.** `α_1 = 1 − 0,1 = 0,9`, `α_2 = 1 − 0,2 = 0,8`. `ᾱ_1 = α_1 = 0,9`, `ᾱ_2 = α_1 α_2 = 0,72`.

**Adım 3 — Kaba çöz.** `t = 1`: ortalama `√0,9 · 2 = 1,8974`, varyans `1 − 0,9 = 0,1`. `t = 2`: ortalama `√0,72 · 2 = 1,6971`, varyans `0,28`.

**Adım 4 — Örüntü.** Varyans `1 − ᾱ_t`'nin `t` ile arttığını görüyoruz; ortalama `√ᾱ_t` ile küçülüyor. İki büyüklük birlikte, sinyal–gürültü oranını (`ᾱ_t / (1 − ᾱ_t)`) belirler. `t = 1`'de oran `9`, `t = 2`'de `2,57`: gürültü her adımda artıyor.

**Adım 5 — İyileştir.** Doğrudan `x_2`'yi ilk adımlardan zincirleyerek bulmak yerine kapalı formu kullandık; bu `T` büyüdükçe çok daha ucuzdur. Dikkat: `ᾱ`'yı `β`'lerden çarpımla hesaplamak gerekir, toplamla değil.

**Adım 6 — Doğrula.** Bilgisayar: `t = 1` için kapalı ortalama `1,8974`, MC `1,8974`; varyans `0,1` ve MC `0,1003`. `t = 2`: ortalama `1,6971` ve MC `1,6971`; varyans `0,28` ve MC `0,2808`.

| t | β_t, α_t, ᾱ_t | Ortalama: kapalı / MC | Varyans: kapalı / MC |
|---|---|---|---|
| 1 | 0,1; 0,9; 0,9 | 1,8974 / 1,8974 | 0,10 / 0,1003 |
| 2 | 0,2; 0,8; 0,72 | 1,6971 / 1,6971 | 0,28 / 0,2808 |

**Bunu AI'sız yazabilir misin?** `β_1 = 0,05`, `β_2 = 0,15`, `β_3 = 0,3` için `ᾱ_3`'ü ve `x_0 = −1` için `q(x_3 | x_0)`'ın ortalamasını hesapla.

### Örnek 3 (★★): Optimal ayırt edici ve JS

Ayrık üç noktalı bir uzayda `p = (0,5; 0,3; 0,2)` ve `q = (0,1; 0,4; 0,5)` olsun. Optimal ayırt ediciyi bul ve `V(D*)` değerinin `−log 4 + 2JS` ile eşleştiğini göster.

**Adım 1 — Anla.** İstenen, `D*(x) = p(x)/(p(x) + q(x))` ve bu `D*` ile `V(D) = Σ [p log D + q log(1 − D)]` değeri. Eşitlik iddiası, GAN'ın Jensen–Shannon bağlantısının sayısal kontrolüdür.

**Adım 2 — Örnekle.** Üç nokta için `D*` hesaplanır, sonra `V` terim terim toplanır. JS için karışım `m = (p + q)/2` gerekir.

**Adım 3 — Kaba çöz.** `D* = (0,5/0,6; 0,3/0,7; 0,2/0,7)`: `(0,8333; 0,4286; 0,2857)`. `m = (0,3; 0,35; 0,35)`.

**Adım 4 — Örüntü.** `D*` büyük olduğu yerde `p > q`: birinci noktada `D*` yüksek, üçüncüde düşük. Bu, `V`'nin her noktadaki katkısının `p`'nin ağırlığıyla sıralandığını gösterir. Eşitlik, `D*`'ın her nokta için `p/(p+q)` olarak seçilmesinden gelir; her nokta kendi katkısını en büyük yapacak değeri alır.

**Adım 5 — İyileştir.** `V` yalnızca `D`'ye bağlıdır; `D*`'ı yerine koymak yerine her noktanın katkısını ayrı ayrı yazmak hataları yakalamayı kolaylaştırır.

**Adım 6 — Doğrula.** Terim terim `V(D*)`:

| x | p | q | D* | p log D* | q log(1 − D*) | Toplam |
|---|---|---|---|---|---|---|
| 1 | 0,5 | 0,1 | 0,8333 | −0,0912 | −0,1792 | −0,2703 |
| 2 | 0,3 | 0,4 | 0,4286 | −0,2542 | −0,2239 | −0,4780 |
| 3 | 0,2 | 0,5 | 0,2857 | −0,2506 | −0,1682 | −0,4188 |

Toplam `−1,1672`. JS: `KL(p ‖ m) = 0,0972`, `KL(q ‖ m) = 0,1219`, `JS = ½(0,0972 + 0,1219) = 0,1096`; `−log 4 + 2 · 0,1096 = −1,3863 + 0,2191 = −1,1672`. Bilgisayar `V(D*) = −1,167161` ve `−log 4 + 2JS = −1,167161` verdi; rastgele 20 000 ayırt edicide en büyük değer `−1,167849` çıktı, yani `D*` maksimumdur.

**Bunu AI'sız yazabilir misin?** `p = (0,6; 0,4)` ve `q = (0,5; 0,5)` için `D*`'ı ve `JS`'yi hesapla. `JS`'nin neden sıfır olmadığını açıkla.

### Örnek 4 (★★★): Gizil kodun bit bütçesi ve beklenen bozulma

Bir autoencoder'ın 16 boyutlu gizil kodu `z ∈ [−1, 1]^16` aralığında tekdüze dağılmış olsun (basitleştirme; gerçek gizil kodlar tekdüze değildir). Her boyutu `b` bit ile düzgün kuantize edersek (a) toplam bit bütçesi nedir, (b) boyut başına beklenen kare hata nedir, (c) 64 bitlik bütçede hangi `b` seçilmeli?

**Adım 1 — Anla.** İstenen üç sayı: `R = d · b`, beklenen kare hata `E[(z − ẑ)²]`, ve bütçe ile hata arasındaki takasın yorumu. Tekdüze dağılımda kuantizasyon hatası aralığa bağlıdır.

**Adım 2 — Örnekle.** `b = 2` için aralık `2 / 2² = 0,5` genişliğinde dört hücre; `b = 4` için `0,125`; `b = 8` için `0,00781`. Hücre genişliği `Δ = 2 / 2^b`.

**Adım 3 — Kaba çöz.** Hücre içinde yeniden yapılandırma noktası merkezde seçilir. Tekdüze bir hücrede hatanın ortalama karesi `Δ²/12`'dir (Bölüm 49'daki tekdüze dağılımın varyansından: genişliği `Δ` olan bir tekdüze dağılımın varyansı `Δ²/12`). `b = 2`: `0,25/12 = 0,02083`; `b = 4`: `0,015625/12 = 0,001302`; `b = 8`: `0,0000610/12 = 5,09·10⁻⁶`. Toplam `R = 16 · b`: `32`, `64`, `128` bit.

**Adım 4 — Örüntü.** Her ek bit `Δ`'yı yarıya indirir, dolayısıyla `Δ²`'yi dörtte bire düşürür: hata her bit için 4 kat azalır. İki bit eklemek (`b = 2`'den `b = 4`'e) hatayı `0,02083 / 0,001302 = 16` kat azaltır. Hata bit sayısında üstel olarak düşer; bu yüzden küçük bir bütçe artışı, küçük bütçede büyük bir kazanç verebilir.

**Adım 5 — İyileştir.** Toplam bütçe sabitken hangi boyuta kaç bit verileceği bir optimizasyon sorusudur: bilgi taşıyan boyutlara daha çok bit vermek gerekir (PCA'nın öz değerleri ya da öğrenilmiş kodun varyansı bu sıralamayı verir). Tekdüze varsayımda ise bit eşit dağıtılır.

**Adım 6 — Doğrula.** Bilgisayar: `b = 2`: `Δ = 0,50000`, teorik `2,083·10⁻²`, MC `2,084·10⁻²`. `b = 4`: `Δ = 0,12500`, teorik `1,302·10⁻³`, MC `1,302·10⁻³`. `b = 8`: `Δ = 0,00781`, teorik `5,086·10⁻⁶`, MC `5,091·10⁻⁶`. Bit bütçeleri: `R = 32`, `64`, `128`.

| b | R = 16b (bit) | Δ | Teorik MSE (Δ²/12) | MC MSE |
|---|---|---|---|---|
| 2 | 32 | 0,5000 | 2,083·10⁻² | 2,084·10⁻² |
| 4 | 64 | 0,1250 | 1,302·10⁻³ | 1,302·10⁻³ |
| 8 | 128 | 0,0078 | 5,086·10⁻⁶ | 5,091·10⁻⁶ |

64 bitlik bütçede (`b = 4`) beklenen boyut başına hata `1,3·10⁻³`'tür. Gerçek kodekimizde bu tekdüze varsayım geçerli değildir; ama bu örnek, bit bütçesi–bozulma eğrisinin neden üstel bir düşüş gösterdiğini ve 72.6'daki kodek eğrilerinde bu düşüşün neden görüldüğünü açıklar.

**Bunu AI'sız yazabilir misin?** `d = 8` boyutlu, tekdüze `[0, 2]` gizil kod için toplam bütçesi 24 bit olan bir kuantizasyon tasarla. Her boyuta kaç bit verdiğini, ve bu tasarımın beklenen toplam kare hatasını yaz.

Örnek 2 ve Örnek 4'ün sayılarını doğrulayan betik aşağıda. Betik yalnızca bu iki örneğin hesaplarını kontrol eder.

```python
# -*- coding: utf-8 -*-
"""Bolum 72 Cozumlu Ornekler: (2) iki adimli beta takvimi icin abar
ve ileri surecin ortalama/varyansi; (4) gizil kodun 2, 4, 8 bitle
kuantizasyonu ve bit butcesi."""
import math
import numpy as np

# ---------- Ornek 2: beta_1 = 0,1, beta_2 = 0,2 ----------
b1, b2 = 0.1, 0.2
a1, a2 = 1 - b1, 1 - b2
ab1, ab2 = a1, a1 * a2
print("== Ornek 2: abar_1, abar_2 ==")
print(f"abar_1 = {ab1:.4f}   abar_2 = {ab2:.4f}")
x0 = 2.0
for t, ab in [(1, ab1), (2, ab2)]:
    mu = math.sqrt(ab) * x0
    var = 1 - ab
    rng = np.random.default_rng(0)
    e = rng.standard_normal(400000)
    xt = math.sqrt(ab) * x0 + math.sqrt(var) * e
    print(f"t={t}: kapali ort={mu:.4f} var={var:.4f} | "
          f"MC ort={xt.mean():.4f} var={xt.var():.4f}")
```

Kodun devamı: aşağıdaki satırlar, önceki parçada kurulan değişkenleri ve modelleri kullanarak işi tamamlar.

```python
# ---------- Ornek 4: tekduzgun gizil kod, b bit ----------
print()
print("== Ornek 4: U[-1,1] kuantizasyonu, bit basina MSE ==")
rng = np.random.default_rng(1)
z = rng.uniform(-1, 1, 1_000_000)
for b in [2, 4, 8]:
    L = 2 ** b
    delta = 2.0 / L
    idx = np.clip(np.floor((z + 1) / delta), 0, L - 1)
    zq = -1 + (idx + 0.5) * delta
    mse_mc = float(((z - zq) ** 2).mean())
    print(f"b={b}: delta={delta:.5f} teorik={delta**2 / 12:.3e} "
          f"MC={mse_mc:.3e}")
d = 16
print()
print("== Bit butcesi: d = 16 boyut ==")
for b in [2, 4, 8]:
    print(f"b={b}: R = d*b = {d * b} bit / ornek")
```

```term
$ python b72_13_ornek_dogrula.py
== Ornek 2: abar_1, abar_2 ==
abar_1 = 0.9000   abar_2 = 0.7200
t=1: kapali ort=1.8974 var=0.1000 | MC ort=1.8974 var=0.1003
t=2: kapali ort=1.6971 var=0.2800 | MC ort=1.6971 var=0.2808

== Ornek 4: U[-1,1] kuantizasyonu, bit basina MSE ==
b=2: delta=0.50000 teorik=2.083e-02 MC=2.084e-02
b=4: delta=0.12500 teorik=1.302e-03 MC=1.302e-03
b=8: delta=0.00781 teorik=5.086e-06 MC=5.091e-06

== Bit butcesi: d = 16 boyut ==
b=2: R = d*b = 32 bit / ornek
b=4: R = d*b = 64 bit / ornek
b=8: R = d*b = 128 bit / ornek
```

## Kendin Yap Projeleri

::: dikkat
Aşağıdaki projelerde bir yapay zekâ aracından kod üretmeden önce kendi çözümünü yaz. Bu bölümdeki betikler size bir başlangıç verir; ama projenin amacı, bir üretken modelin eğitimini, örneklemesini ve ölçümünü kendi elinle kurmaktır. Kodun bir kısmını bir araçtan alırsan, ne yaptığını satır satır açıklayabildiğinden emin ol.
:::

### Proje 1 (★★): 2B'de farklı bir dağılım için difüzyon

**Amaç.** Bu bölümde 8 Gauss halkası için bir DDPM ve DDIM kurduk. Aynı süreci farklı bir 2B dağılım üzerinde yeniden kur ve takvim ile örnekleme adım sayısının etkisini ölç. Önerilen dağılım: iki ay (iki yarım daire) ya da üç merkezli Gauss kümesi.

**Yapılacak.** (1) İki farklı gürültü takvimi (doğrusal ve kosinüs) ile `T = 100` adımlık bir model eğit. (2) Her takvim için DDPM (T adım) ve DDIM (S = 5, 10, 20, 50, 100) ile 2000 örnek üret. (3) Her örnekleme için kapsanan mod sayısını, yüksek kaliteli oranı ve (varsa) dağılım sınırlarına uzaklığı raporla. (4) Gürültü tahmincisinin eğitim kaybını ve "ᾱ_T ≈ 0" koşulunun sağlanıp sağlanmadığını göster.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Kapalı formu MC ile doğrulayarak başla. Kayıp fonksiyonunda `t`'nin `1..T` aralığından seçildiğinden emin ol; `0` indeksi temiz veriye karşılık gelir. DDPM örneklemesinde gürültü yalnızca `t > 1` için eklenir. Mod kapsamı ölçütünü bu bölümdeki `mod_olcutu`'ya benzer biçimde yaz ama dağılımının merkezlerini kendin belirle.

**Başarı kriterleri.** (a) Kapalı form ortalama ve varyansı MC ile 200 000 örnekte %1 göreli hata içinde eşleşiyor. (b) DDPM ile örnekleme, dağılımın tüm bileşenlerini kapsıyor (kapsama ≥ %1). (c) DDIM adım sayısı–kalite eğrisi tek bir tepe noktası gösteriyor ya da monoton artıyor; eğrinin nedenini bir paragrafta açıkladın. (d) Üç tohum için sapma verildi.

### Proje 2 (★★★): Öğrenilmiş semantik kodek: ÖZCE fikrinin küçük bir yeniden üretimi

**Amaç.** Bu bölümde autoencoder, PCA ve DCT'yi aynı bit bütçesinde, gürültülü bir kanal üzerinden karşılaştırdık. Bu projede aynı çerçeveyi farklı bir görevle yeniden kur. ÖZCE'nin dosyalarına erişmeden, yalnızca kavramsal çerçeveyi kendi verinde uygula. Görev olarak 0 ile 1 rakamlarını ayıran ikili bir sınıflandırma, ya da 72.5'teki sensör sinyalinde bir anomali kararı seç.

**Yapılacak.** (1) Kodlayıcıyı görev kaybıyla birlikte eğit: sınıflandırma kaybını gizil kod üzerine ekleyebilirsin. (2) Gizil kodu `b` bit ile kuantize et; kanal bit çevirme olasılığı `p` olsun. (3) Ayrı bir kanal-farkındalıklı eğitim (eğitimde rastgele bit çevirme) ile kanal-farkındalıksız eğitimi karşılaştır. (4) PCA ve DCT baseline'larını aynı bit bütçesinde ekle. (5) Oran–bozulma ve oran–görev doğruluğu eğrilerini çiz.

**Önerilen yaklaşım (ipucu).** Gray kodlamasıyla ikili indeksleme yaparak ikili gösterimde komşu seviyelerin yalnızca bir bitinin farklı olmasını sağla; bu, bit çevirme sırasında büyük sıçramaları azaltabilir. Kuantizasyon aralığını eğitim verisinden hesapla, test verisinden değil. Her ölçüm için en az üç tohum kullan ve bunların ortalama ile sapmasını ver.

**Başarı kriterleri.** (a) Üç tohumla, her `(b, p)` çifti için ortalama ve sapma raporlanmış. (b) Kanal-farkındalıklı ve farkındalıksız eğitim arasında, `p = 0,05` için görev doğruluğu farkı ölçülmüş ve yorumlanmış. (c) PCA ve DCT ile aynı bit bütçesinde karşılaştırma yapılmış. (d) Hangi bütçede hangi kodeğin üstün olduğunu gösteren bir karar kuralı yazılmış; "her zaman üstün" iddiası yok.

### Ek Alıştırmalar

1. ★ (Mülakat) VAE'de yeniden parametrelendirme neden gereklidir? `sample()` ile `rsample()` arasındaki farkı gradyan akışıyla açıkla.
2. ★ (Mülakat) ELBO'yu Jensen eşitsizliğinden yararlanarak türet ve hangi koşulda eşitliğe ulaştığını yaz.
3. ★★ (Mülakat) Mod çöküşü nedir? Bu bölümdeki 2B halka deneyinde hangi ölçüt onu ortaya koyar ve neden tek başına "sekiz mod var" bilgisi yetmez?
4. ★★ (Mülakat) Bir difüzyon modeli temiz bir örneği nasıl gürültüye çevirir ve ters yönde nasıl örnek üretir? Gürültü tahmincisinin rolünü açıkla.
5. ★ (Mülakat) VAE, GAN ve difüzyon modellerini olabilirlik, örnek kalitesi, çeşitlilik ve örnekleme hızı açısından karşılaştır.
6. ★ Doğrusal bir autoencoder'ın PCA ile aynı alt uzayı öğrendiğini ama koordinat sisteminin farklı olabileceğini neden söyleyebiliriz? Bu bölümdeki ana açı ölçümü neyi kanıtlar, neyi kanıtlamaz?
7. ★★ İki çok boyutlu Gauss arasındaki KL(N(μ₁, Σ₁) ‖ N(μ₂, Σ₂)) için kapalı formu türet; kovaryansları köşegen alarak tek boyutlu duruma indirgediğinde Bölüm 72.7'deki formülü elde ettiğini göster.
8. ★★ β-VAE'de β = 4 posterior çöküşüne yol açtı. Çöküşü azaltmak için hangi üç yöntemi denersin ve her birinin hangi varsayımı değiştirdiğini belirt.
9. ★★ DDIM'de η parametresi nedir ve η = 0 ne anlama gelir? η = 1 değerinde süreç hangi ancestral örneklemeye yaklaşır?
10. ★★★ Sınıfsız yönlendirmede `w = 3` neden örnekleri merkezden uzaklaştırdı? ε̃ = (1 + w) ε_c − w ε_∅ ifadesindeki iki terimin farkını inceleyerek açıkla.
11. ★ Mini-FID'i adım adım yaz: ortalama farkı, kovaryansların çarpımının karekökü, izi. Neden kovaryans çarpımının karekökü gerekir, ortalamanın ortalaması yetmez mi?
12. ★★ Bir sensör anomali sisteminde eşiği hangi ölçüte göre seçersin? Yanlış alarm ve kaçırılan anomali maliyetlerini nasıl bir araya getirirsin?

## Kod Okuma Egzersizi

Bu bölümde kendi kapalı form KL'mizi ve yeniden parametrelendirmemizi yazdık. PyTorch 2.6.0'ın kurulu paketinde aynı işi yapan kod, dağılım kütüphanesinde bulunur. Kaynak: PyTorch 2.6.0+cu124, `torch/distributions/kl.py` (satır 466–470) ve `torch/distributions/normal.py` (satır 75–78). Kodu yerel kurulu paketten birebir kopyaladık; bölme yok.

Önce KL'nin iki Gauss arasındaki hesabı:

```python
@register_kl(Normal, Normal)
def _kl_normal_normal(p, q):
    var_ratio = (p.scale / q.scale).pow(2)
    t1 = ((p.loc - q.loc) / q.scale).pow(2)
    return 0.5 * (var_ratio + t1 - 1 - var_ratio.log())
```

Bu fonksiyon, bizim `kl_kapali` fonksiyonumuzun genel hâlidir. `p = N(μ, σ)` ve `q = N(0, 1)` alınırsa `var_ratio = σ²`, `t1 = μ²`, ve sonuç `½ (σ² + μ² − 1 − ln σ²)` olur: bu, bu bölümdeki formülle aynıdır. Kütüphane kodu iki farkla daha genel çalışır: ölçekleri ve ortalamaları ayrı ayrı alır, ve `log` yerine `var_ratio.log()` kullanır. Dikkat edilecek nokta, `var_ratio`'nun varyans oranı olduğu, standart sapma oranı olmadığıdır; bu yüzden karesi alınmıştır.

Şimdi yeniden parametrelendirmenin kütüphanedeki karşılığı:

```python
    def rsample(self, sample_shape: _size = torch.Size()
            ) -> torch.Tensor:
        shape = self._extended_shape(sample_shape)
        eps = _standard_normal(shape, dtype=self.loc.dtype,
                               device=self.loc.device)
        return self.loc + eps * self.scale
```

Aşağıdaki iki kesitte iki satır, 70 karakter sınırına sığsın diye bölündü; anlam değişmedi. `rsample`, `loc + eps * scale` ile yeniden parametrelendirmeyi uygular; `eps` standart normal örnektir ve `loc`, `scale` üzerinden türevlenebilir bir ifadeye girer. Bu, bizim `z = μ + σ ⊙ ε` ifademizin birebir karşılığıdır. `sample` yönteminin ise (satır 72–73 civarında, `torch.normal` çağrısıyla) bir türev grafiği kurmadığını bu bölümdeki deneyde `requires_grad = False` ile gördük.

**Sorular — cevaplamadan geçme:**

1. `_kl_normal_normal` içinde `var_ratio` ile `t1` neden ayrı ayrı hesaplanıyor? Bu ayrım, ortalamanın ve varyansın farklı ölçeklerde olduğu bir durumda hangi hatayı önler?
2. Kodun sonucu `0.5 * (...)` ile ölçekleniyor. Bu ½ katsayısı hangi Gauss türevinden gelir ve Bölüm 72.7'deki kapalı form türetmesinde nerede görünür?
3. `rsample` içinde `eps` neden `self.loc.dtype` ve `self.loc.device` ile üretiliyor? Bu parametreler yanlış cihaz ve tip verilseydi ne olurdu?
4. `loc + eps * scale` ifadesi, türevi `loc` ve `scale`'e göre nasıl taşır? Bu ifadede `eps`'nin türevinin alınmadığını neden söyleyebiliyoruz?
5. `_kl_normal_normal` bir `@register_kl` dekoratörü ile kaydedilmiş. Bu mekanizmanın amacı nedir ve `KL(p, q)`'nun hangi `p` ve `q` türünde çağrılacağını nasıl belirler?
6. Kütüphane `KL(N(μ, σ²) ‖ N(0,1))` yerine tersini (`KL(N(0,1) ‖ N(μ, σ²))`) hesaplasaydı formül nasıl değişirdi? Bunu kendi kâğıdında türet ve kodla karşılaştır.

## Bölüm Özeti

- Üretken modeller `p(x)` ya da `p(x, y)` öğrenir; ayırt edici modeller `p(y|x)`'i öğrenir. Üretken model, örnek üretme ve olabilirlik değerlendirme yeteneği için daha zordur ama daha çok iş görür.
- Beş ana aile vardır: otoregresif (Bölüm 70), gizil değişkenli (AE, VAE), çekişmeli (GAN), akış ve skor/difüzyon. Her biri dağılımı farklı bir yolla temsil eder ve farklı ölçütlerle değerlendirilir.
- Üretken modeller tek bir sayıyla değerlendirilmez: kalite (kesinlik), çeşitlilik (geri çağırma), olabilirlik ve ezber birlikte okunmalıdır. Mini-FID, Fréchet mesafesinin kendi özellik uzayımızdaki karşılığıdır.
- Doğrusal bir autoencoder PCA'nın alt uzayını öğrenir (ana açı ile doğrulanır); derin bir autoencoder doğrusal olmayan bir alt uzay öğrenir ve sensör anomali tespitinde PCA'dan belirgin biçimde iyi çalışır, ama spike türündeki anomaliler için de sınırlıdır.
- Öğrenilmiş kodekte bit bütçesi ve kanal gürültüsü birlikte değerlendirilmeli. Kuantizasyonsuz piksel hatası en düşük autoencoder, görev doğruluğunda her zaman en iyi değildir; düşük bütçede ve gürültüde üstünlüğü görülür.
- VAE, ELBO'yu maksimize ederek `q(z|x)`'i posteriora yaklaştırır; yeniden parametrelendirme gradyanı taşıyabilmek için rastgeleliği dışarı çıkarır. β büyüdükçe posterior çöküşü görülür.
- GAN, minimaks bir oyunla örneklenmiş dağılımı eşleştirir; optimal ayırt edici JS ıraksamasını ortaya çıkarır. Doymayan kayıp eğitim başında gradyanı korur. Mod çöküşü ve öğrenme oranı kararsızlığı kapsam ve kaliteyi birlikte ölçerek görülür.
- Difüzyon modelleri gürültülendirme ve ters süreç ile çalışır; `q(x_t|x_0)` kapalı formu eğitimi ucuzlatır, gürültü tahmini basit bir kayıpla öğrenilir. DDIM daha az adımla örneklemeyi sağlar; adım sayısı kalite ve kapsam arasında bir takas üretir. Sınıfsız yönlendirmenin `w`'si aşırıya kaçarsa dağılım sadakatini bozar.
- Sentetik veriyle veri artırmada etiket doğruluğu, sayı kadar önemlidir; etiketleyici için veri sızıntısı önlenmelidir. Üretken modeller için sorumlu kullanım, tespit ve doğrulama bir teknik gerekliliktir.

**Sonraki bölümde:** Bölüm 73, Temsil Öğrenme ve Kendi Kendini Denetleme (self-supervised), bu bölümde karşılaştığımız gizil uzayı ayrı bir amaçla kurmaya bakacak. Bu bölümde gizil kodu yeniden yapılandırma için öğrendik; Bölüm 73'te gizil uzayın kendi başına anlamlı olması için, etiket olmadan, karşılaştırmalı kayıplarla nasıl öğrenileceğini göreceğiz. Autoencoder'ın gizil kodu ile kontrastif bir temsilin farkı, Bölüm 73'ün ana sorusu olacak.

::: mulakat
1. VAE'nin kayıp fonksiyonunda KL terimi neden var? Onu kaldırırsan model ne öğrenir ve üretken olarak neden işe yaramaz hâle gelir?
2. Yeniden parametrelendirme hilesi nedir? Örneklemeyi türevlenebilir hâle getirmek için rastgeleliği hangi değişkene taşıdık?
3. GAN'da mod çöküşü nedir? Bir üretici sekiz modun yalnızca ikisini üretirse bu hangi ölçütlerle fark edilir?
4. Doymayan üretici kaybı neden minimaks kaybından daha kullanışlıdır? Ayırt edici sahteyi kesin reddettiğinde gradyanlara ne olur?
5. Difüzyon modeli eğitiminde kayıp fonksiyonu neden gürültüyü tahmin etmeye indirgenir ve bu, ters süreçte hangi bilgiyi kullanır?
6. Sınıfsız yönlendirmede `w` büyüdükçe kalite mi, çeşitlilik mi, yoksa dağılım sadakati mi bozulur? Bunu nasıl ölçersin?
7. Bir autoencoder ile PCA aynı alt uzayı öğrenirse, aralarında hangi kullanım farkı kalır? Anomali tespitinde derin autoencoder neden PCA'dan farklı davranabilir?
:::
