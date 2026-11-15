%% kisim_no: XVI
%% kisim_ad: ML Mühendisliği & Araştırma
%% bolum_no: 78
%% baslik: Güvenilir & Güvenli AI

## Giriş: Doğru olmak yetmez, ne zaman yanıldığını bilmek gerekir

Bölüm 54'te bir ML pipeline'ının nasıl kurulduğunu gördük ve modelin doğruluğunu ayrı bir test kümesinde ölçmeyi öğrendik. Bölüm 57'de bu ölçümün de bir sözleşme olduğunu, yani "yüzde doksan beş doğru" demenin hangi koşullarda bir anlam taşıdığını konuştuk. Bu bölüm o sözleşmenin devamıdır. Soru artık "model ne kadar doğru?" değil, "model yanıldığında ne olur, bunu nasıl fark ederiz?" sorusudur.

Bir modelin "yüzde doksan beş doğru" olması, o yüzde beşin nerede olduğunu, emin olduğu yanlışlarda nasıl davrandığını ve hiç görmediği bir girdiyle karşılaştığında ne yaptığını söylemez. Bu üç soru, sistemin güvenliğinin asıl kısmıdır.

Savunma sanayiinde bu ayrım doğrudan can güvenliğiyle ilgilidir. Bir İHA'nın görüntü sınıflandırıcısı, hiç görmediği bir aydınlatma koşulundaki bir kareye "hedef" yanıtı verirse bunun sonucu bir ölçüm hatasından ibaret değildir. Aynı sistem, bir düşmanın tasarladığı küçük bir bozulmayla da yanıltılabilir. Mülakatta "modelin doğruluğu neden yeterli değil?" sorusunun cevabı çoğu zaman bu iki noktada toplanır.

Bu bölümde dört soruyu sırayla yanıtlıyoruz. Birincisi, güvenilir bir AI'nın hangi boyutlardan oluştuğu (78.1). İkincisi, model tanımadığı girdiyi nasıl fark eder (78.3) ve ne kadar emin olduğunu nasıl bildirir (78.4). Üçüncüsü, sistem emin olmadığında ne yapar: kararı reddeder ve operatöre devreder (78.5). Dördüncüsü, modeli kasıtlı olarak zorladığımızda sağlamlığı nasıl ölçülür ve bir savunmanın gerçekten işe yarayıp yaramadığı nasıl kanıtlanır (78.6 ve 78.7).

Çerçeveyi baştan netleştirelim. Bu bölümde çekişmeli örnekler (adversarial examples) yalnızca kitabın kendi küçük modelleri üzerinde, sağlamlığı ölçmek ve savunmayı değerlendirmek için kullanılır. FGSM ve PGD, sağlamlık değerlendirmesinin standart araçlarıdır. Üçüncü taraf sistemlere, gerçek ürünlere ya da fiziksel dünyaya yönelik bir saldırı tarifi vermiyoruz; tehdit modelini ve savunmayı kavramsal düzeyde anlatıyoruz. Güvenliğin genel çerçevesi için Bölüm 32'ye bakın; dil modellerindeki prompt enjeksiyonu savunmaları Bölüm 71'de ele alındı.

::: not
Bu bölümdeki tüm ölçümler tek bir Windows 11 makinesinde, yalnızca CPU üzerinde alındı; GPU kullanılmadı. Veri olarak scikit-learn'ün 8 × 8 piksellik `load_digits` kümesini kullandık. Her deney üç tohumla tekrarlandı ve sonuçlar ortalama ± sapma olarak verildi. Dağılım dışı (OOD) girdiler kitabın kendi ürettiği gürültü ve pürüzlü leke görüntüleridir. Sayılar bu kurulum ve bu küçük ölçek için geçerlidir. Büyük bir sistemde büyüklükler değişir; yöntemin mantığı ve sınama disiplini ise aynı kalır.
:::

## 78.1 Güvenilir AI'nın boyutları

Güvenilir (trustworthy) yapay zekâ tek bir sayı değildir. Bir sistem, aşağıdaki yedi boyutun her birinde kabul edilebilir bir düzeye ulaşmadan güvenilir sayılmaz. Bu boyutlar birbiriyle örtüşür ve çoğu zaman birbirinin karşısına geçer.

**Doğruluk (accuracy).** Belirlenmiş bir dağılımda, belirlenmiş bir ölçütle ölçülen doğru yanıt oranı. Bölüm 57'de gördük ki tek bir sayı yetmez: sınıf başına hata, güven aralığı ve ölçümün hangi dilimde yapıldığı da önemlidir.

**Sağlamlık (robustness).** Girdi küçük ya da beklenmedik biçimde değiştiğinde doğruluğun ne kadar düştüğü. Sensör bozulması, gürültü ve kayma bu kategoridedir. Doğal bozulmalara karşı sağlamlık Bölüm 66'da bozulma testleriyle ölçüldü. Kasıtlı saldırılar bu bölümün 78.6 kısmında.

**Kalibrasyon.** Modelin "yüzde seksen eminim" dediği tahminlerin gerçekten yüzde seksen oranında doğru olması. Bölüm 57'deki ECE ve güvenilirlik diyagramı bu boyutun ölçüsüdür.

**Açıklanabilirlik.** Kararın hangi girdilere dayandığının insan tarafından incelenebilir olması. Bölüm 58'de katsayıları okunabilen bir doğrusal modelin bu konuda kendiliğinden avantajlı olduğunu gördük. Derin ağlarda aynı şeyi sağlamak için ayrı bir araç setine ihtiyaç var (78.8).

**Adalet.** Farklı grupların (cinsiyet, bölge, sensör tipi, ekipman) hata oranlarının karşılaştırılabilir olması. Bölüm 57'deki dilim analizi bu boyutun ilk adımıdır (78.9).

**Güvenlik (security).** Sistemin kötü niyetli girdilere, veri zehirlemeye ve model sızıntısına karşı korunması. Bölüm 32'deki savunma ilkeleri ML sistemine de uygulanır, ama ML'e özgü yeni yüzeyler vardır (78.10).

**İzlenebilirlik.** Bir modelin hangi veriyle, hangi kodla ve hangi sürümle eğitildiğinin, bir kararın hangi modelle verildiğinin ve bu kararların sonradan incelenebilmesinin kaydı. Bölüm 77'de model kartları ve denetim izi bu boyutun araçları olarak ele alınıyor.

Şekil 78.1, bu yedi boyutu ve aralarındaki ayrımı gösteriyor.

![Şekil 78.1: Güvenilir AI yedi boyuttan oluşur; üst sıra model davranışını, alt sıra toplumsal etkiyi ve süreci ölçer.](gorseller/b78_guvenilir_boyutlar.png)

Boyutlar arası takaslar gerçektir. Bir sınıflandırıcının eşiğini değiştirmek yanlış alarm ile kaçırma arasında bir denge kurar (Bölüm 57'deki PR eğrisi). Grup başına farklı bir eşik seçmek adalet açısından genel doğruluğu biraz düşürebilir (78.9). Sağlamlık için yapılan çekişmeli eğitim, temiz doğruluğu da değiştirebilir (78.7). Bu yüzden güvenilirlik bir "maksimum" değil, uygulamaya göre seçilmiş bir dengedir. Denge yazılı olarak tanımlanmalıdır. Bu bölümdeki her deneyde, takasın hangi tarafının ölçüldüğünü belirttik.

## 78.2 Deney ortamı: veri, model ve ölçütler

Bu bölümdeki deneyler aynı küçük altyapıyı kullanır. Veri olarak `load_digits` kümesini aldık: 1797 örnek, 8 × 8 piksel, 10 sınıf. Pikselleri 16'ya bölerek [0, 1] aralığına getirdik. Bölme sabit tutuldu: yüzde 50 eğitim (898 örnek), yüzde 15 doğrulama (269), yüzde 15 kalibrasyon (270) ve yüzde 20 test (360).

Doğrulama kümesi sıcaklık ölçeklemesi ve OOD eşikleri için, kalibrasyon kümesi conformal tahmin için kullanıldı. Test kümesi yalnızca raporlama içindir; hiçbir eşik test üzerinde seçilmedi. Bu, Bölüm 54'teki veri sızıntısı kuralının doğrudan uygulamasıdır.

Model 64 → 128 → 64 → 10 boyutlu bir çok katmanlı algılayıcıdır (MLP). Gizli katmanlardan sonra dropout uygulanır; deneye göre oranı 0,2 ya da 0 seçildi. Eğitim Adam ile 60 dönem ve 64'lük yığınlarla yapıldı. Test doğruluğu yaklaşık yüzde 95. Bir CNN için bu düşük sayılır, ama bu bölümün amacı için yeterlidir: hataların var olması zaten bu bölümün konusudur.

Her eğitimin tohumu açıkça verilir ve ağırlıklar bu tohumdan kurulur. Her deney üç tohumla (0, 1, 2) tekrarlanır. Derin topluluk için her tohumda beş üye daha eğitilir.

Ortak modül aşağıda. İçinde veri hazırlığı, model, eğitim döngüsü, ölçütler (ECE, AUROC, FPR@95), sentetik OOD üreticisi ve FGSM/PGD saldırıları var. Her deney betiği bu modülü içe aktarır.

```python
# -*- coding: utf-8 -*-
"""Bolum 78 ortak modulu: veri, model, egitim, olcut, saldiri."""

import os

os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.ndimage import gaussian_filter
from scipy.special import logsumexp
from sklearn.datasets import load_digits
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

torch.set_num_threads(4)
SEEDS = [0, 1, 2]
VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


```

```python
def veri_hazirla():
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).astype(np.float32)  # piksel olcegi [0, 1]
    Xtr, Xr, ytr, yr = train_test_split(
        X, y, test_size=0.5, stratify=y, random_state=42
    )
    Xva, Xr2, yva, yr2 = train_test_split(
        Xr, yr, test_size=0.7, stratify=yr, random_state=42
    )
    Xca, Xte, yca, yte = train_test_split(
        Xr2, yr2, test_size=20 / 35, stratify=yr2, random_state=42
    )
    return dict(
        Xtr=Xtr,
        ytr=ytr,
        Xva=Xva,
        yva=yva,
        Xca=Xca,
        yca=yca,
        Xte=Xte,
        yte=yte,
    )


def ood_uret(n):
    """Sentetik OOD: (a) duzgun gurultu, (b) puruzlu lekeler."""
    rng = np.random.default_rng(999)
    gur = rng.uniform(0, 1, size=(n, 64)).astype(np.float32)
    ham = rng.normal(size=(n, 8, 8))
    lek = np.stack([gaussian_filter(h, 1.0) for h in ham])
    lo = lek.min(axis=(1, 2), keepdims=True)
    hi = lek.max(axis=(1, 2), keepdims=True)
    lek = ((lek - lo) / (hi - lo)).reshape(n, 64).astype(np.float32)
    return gur, lek


class MLP(nn.Module):
    """64 -> 128 -> 64 -> 10. p: gizli katmanlardan sonra dropout."""

```

```python
    def __init__(self, p=0.2):
        super().__init__()
        self.f1 = nn.Linear(64, 128)
        self.f2 = nn.Linear(128, 64)
        self.cik = nn.Linear(64, 10)
        self.drop = nn.Dropout(p)

    def ozellik(self, x):
        h = self.drop(F.relu(self.f1(x)))
        return F.relu(self.f2(h))

    def forward(self, x):
        return self.cik(self.drop(self.ozellik(x)))


def standart_kayip(model, xb, yb, ep, E):
    return F.cross_entropy(model(xb), yb)


def egit(
    model, X, y, seed, kayip=standart_kayip, epoch=60, lr=1e-3, bs=64
):
    """Adam ile mini-batch egitim. kayip(model, xb, yb, ep, E)."""
    torch.manual_seed(seed)
    for m in model.modules():  # agirliklari tohumdan kur
        if hasattr(m, "reset_parameters"):
            m.reset_parameters()
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    Xt, yt = torch.tensor(X), torch.tensor(y)
    for ep in range(epoch):
        model.train()
        perm = rng.permutation(len(X))
        for i in range(0, len(X), bs):
            idx = torch.tensor(perm[i : i + bs])
            loss = kayip(model, Xt[idx], yt[idx], ep, epoch)
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
```

```python
    return model


def softmax_np(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def logit_np(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(X)).numpy()


def feat_np(model, X):
    model.eval()
    with torch.no_grad():
        return model.ozellik(torch.tensor(X)).numpy()


def topluluk_egit(D, s, M=5):
    """Derin topluluk: tohumu s'ye bagli M bagimsiz model."""
    return [
        egit(MLP(0.2), D["Xtr"], D["ytr"], seed=100 * (s + 1) + m)
        for m in range(M)
    ]


```

```python
def ece(p, y, kutu=15):
    guven = p.max(axis=1)
    dogru = (p.argmax(axis=1) == y).astype(float)
    kenar = np.linspace(0.0, 1.0, kutu + 1)
    toplam = 0.0
    for lo, hi in zip(kenar[:-1], kenar[1:]):
        m = (guven > lo) & (guven <= hi)
        if m.any():
            toplam += m.mean() * abs(
                dogru[m].mean() - guven[m].mean()
            )
    return float(toplam)


def guvenilirlik_kutulari(p, y, kutu=15):
    guven = p.max(axis=1)
    dogru = (p.argmax(axis=1) == y).astype(float)
    kenar = np.linspace(0.0, 1.0, kutu + 1)
    satir = []
    for lo, hi in zip(kenar[:-1], kenar[1:]):
        m = (guven > lo) & (guven <= hi)
        if m.any():
            satir.append(
                (
                    lo,
                    hi,
                    guven[m].mean(),
                    dogru[m].mean(),
                    int(m.sum()),
                )
            )
    return satir


def auroc(s_id, s_ood):
    """Yuksek skor = icerida (ID). Donus: ROC egrisi altinda alan."""
    et = np.r_[np.ones(len(s_id)), np.zeros(len(s_ood))]
    return float(roc_auc_score(et, np.r_[s_id, s_ood]))


```

```python
def fpr95(s_id, s_ood):
    """ID'nin %95'ini tutan esikte OOD'un yuzde kaci kabul edilir."""
    esik = np.percentile(s_id, 5)
    return float(np.mean(s_ood >= esik))


def csv_yaz(ad, baslik, satirlar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8") as f:
        f.write(",".join(baslik) + "\n")
        for s in satirlar:
            f.write(",".join(str(v) for v in s) + "\n")
    return yol


def kayip_hesapla(z, yt, kayip):
    """Maksimize edilecek kayip (ornek basina)."""
    if kayip == "ce":  # log_softmax ile dogru capraz entropi
        return F.cross_entropy(z, yt, reduction="none")
    if kayip == "naif":  # softmax -> log: doygunlukta gradyan 0
        p = torch.softmax(z, 1).gather(1, yt[:, None]).squeeze(1)
        return -torch.log(p)
    # "marj": en iyi yanlis sinif - dogru sinif (logit uzayi)
    zy = z.gather(1, yt[:, None]).squeeze(1)
    diger = z.clone()
    diger[torch.arange(len(yt)), yt] = -1e9
    return diger.max(1).values - zy


```

```python
def pgd(
    model,
    X,
    y,
    eps,
    adim_say=40,
    kayip="ce",
    rastgele=True,
    seed=0,
    adim=None,
):
    """L-inf PGD. FGSM icin adim_say=1, adim=eps, rastgele=False."""
    g = torch.Generator().manual_seed(seed)
    x0, yt = torch.tensor(X), torch.tensor(y)
    a = adim if adim is not None else 2.5 * eps / adim_say
    model.eval()
    x = x0.clone()
    if rastgele:
        x = x + (torch.rand(x.shape, generator=g) * 2 - 1) * eps
        x = x.clamp(0, 1)
    for _ in range(adim_say):
        x.requires_grad_(True)
        L = kayip_hesapla(model(x), yt, kayip).sum()
        (gx,) = torch.autograd.grad(L, x)
        x = x.detach() + a * gx.sign()
        x = torch.min(torch.max(x, x0 - eps), x0 + eps).clamp(0, 1)
    return x.detach().numpy()


def dogruluk(model, X, y):
    return float((logit_np(model, X).argmax(1) == y).mean())
```


Modülde iki nokta dikkat ister. Birincisi `egit` fonksiyonu ağırlıkları tohumdan yeniden kurar. İlk sürümde model, tohum ayarlanmadan önce kuruluyordu ve aynı tohumla yapılan iki çalıştırma farklı sonuç verdi. Bunu ölçümleri tekrarlarken fark ettik ve düzelttik. Tekrarlanabilirlik, ölçümün kendisinin parçasıdır: sonuçları iki kez üretip karşılaştırmadan bir sayıya güvenmemek gerekir.

İkincisi `pgd` fonksiyonu üç kayıp türünü destekler. `ce` log-softmax ile hesaplanan doğru çapraz entropidir. `naif` softmax sonrasında logaritma alır; softmax doyduğunda gradyanı sıfırlanır. 78.6'da bunun neden yanıltıcı olduğunu göreceğiz. `marj` ise doğru sınıf ile en iyi yanlış sınıf arasındaki logit farkıdır.

## 78.3 Dağılım dışı girdiler (OOD)

Eğittiğimiz model yalnızca gördüğü dağılımdaki girdiler hakkında güvenilir olabilir. Bir rakam sınıflandırıcısına bir kedi fotoğrafı ya da düzgün gürültüden oluşan bir görüntü verilirse, model yine on sınıftan birini seçer. Soru şudur: model bu girdinin tanıdık olmadığını fark edebiliyor mu? Buna dağılım dışı (out-of-distribution, OOD) tespiti denir. Dağılım kaymasıyla (Bölüm 54 ve 57) karıştırılmamalı: kayma, tüm veri akışının zamanla değişmesidir; OOD ise tek tek girdilerin eğitim dağılımının dışına düşmesidir.

Üç tespit skoru karşılaştıracağız. Skorun yüksek olması, girdinin içeride (ID) olduğu anlamına gelir.

**Maksimum softmax olasılığı (MSP).** Tahminin en büyük olasılığı. Hendrycks ve Gimpel'in 2017 çalışmasından beri temel bir taban çizgisidir (genel bilgi). Basittir, ama yüksek güvenli yanlışlara karşı zayıftır: softmax, eğitimde görmediği girdilerde de yüksek olasılık verebilir.

**Enerji skoru.** Logit'lerin log-toplam-üstelinin negatifi, E(x) = −log Σ exp(z_k). Büyük logit'ler, girdinin bir sınıfa güçlü biçimde bağlandığını ima eder. Softmax'ın normalizasyonunu atar ve logit ölçeğini korur. Liu ve arkadaşlarının 2020 çalışmasında enerji tabanlı OOD tespiti önerildi (genel bilgi).

**Mahalanobis uzaklığı.** Son gizli katmanın öznitelik uzayında, her sınıf ortalamasına ve ortak kovaryansa göre en küçük karesel uzaklık. Bu, Bölüm 61'deki Gauss karışım modelinin tek bir ortak kovaryansla kurulmuş hâlidir. Öznitelik uzayında ID verisi sıkı bir bulut oluşturur; OOD girdiler bu bulutun dışına düşer. Lee ve arkadaşlarının 2018 çalışmasında bu yaklaşım kullanılmıştır (genel bilgi).

Ölçüt olarak iki şey kullanacağız. AUROC, ROC eğrisinin altındaki alandır: rastgele bir ID girdisinin rastgele bir OOD girdisinden daha yüksek skor alma olasılığıdır. FPR@95 ise daha doğrudan bir güvenlik sorusuna cevap verir: gerçek girdilerin yüzde 95'ini kabul eden eşikte, OOD girdilerin yüzde kaçı yine kabul edilir? Bir kapı için bu, AUROC'tan daha anlamlı bir karşılıktır.

Deneyde sentetik OOD kümesi iki türden oluşur. Birincisi düzgün gürültüdür: her piksel [0, 1] aralığında bağımsız olarak çekilir. İkincisi pürüzlü lekelerdir: rastgele bir alan Gauss filtresinden geçirilip [0, 1] aralığına ölçeklenir. Her tohumda 360 gerçek test örneği ile 720 OOD girdisi karşılaştırıldı. OOD kümesi her tohumda aynıdır; böylece yöntemler aynı rakip girdiler üzerinde yarışır.

```python
# -*- coding: utf-8 -*-
"""Deney 1: dagilim disi (OOD) skorlari: MSP, enerji, Mahalanobis."""

import numpy as np
from scipy.special import logsumexp
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    ood_uret,
    MLP,
    egit,
    softmax_np,
    logit_np,
    feat_np,
    auroc,
    fpr95,
    csv_yaz,
)


def mahalanobis_fit(Ftr, ytr):
    """Sinif ortalamalari + ortak kovaryans (Bolum 61, GMM)."""
    mu = np.stack([Ftr[ytr == c].mean(0) for c in range(10)])
    artik = Ftr - mu[ytr]
    sigma = artik.T @ artik / len(Ftr)
    prec = np.linalg.pinv(sigma + 1e-3 * np.eye(sigma.shape[0]))
    return mu, prec


def mahalanobis_skor(Fz, mu, prec):
    """En yakin sinifa karesel uzaklik; yuksek = icerida."""
    d = []
    for c in range(10):
        r = Fz - mu[c]
        d.append(np.einsum("ij,jk,ik->i", r, prec, r))
    return -np.min(np.stack(d, axis=1), axis=1)


```

```python
def skorlar(model, X, mu, prec):
    z = logit_np(model, X)
    return {
        "MSP": softmax_np(z).max(1),
        "Enerji": logsumexp(z, axis=1),
        "Mahalanobis": mahalanobis_skor(feat_np(model, X), mu, prec),
    }


def main():
    D = veri_hazirla()
    gur, lek = ood_uret(len(D["Xte"]))
    turler = {
        "gurultu": gur,
        "leke": lek,
        "birlesik": np.r_[gur, lek],
    }
    satirlar, dagilim = [], []
    print("tohum  test_dogruluk")
    for s in SEEDS:
        model = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        acc = (logit_np(model, D["Xte"]).argmax(1) == D["yte"]).mean()
        print("%5d  %13.4f" % (s, acc))
        Ftr = feat_np(model, D["Xtr"])
        mu, prec = mahalanobis_fit(Ftr, D["ytr"])
        s_id = skorlar(model, D["Xte"], mu, prec)
        for tur, Xo in turler.items():
            s_ood = skorlar(model, Xo, mu, prec)
            for yon in s_id:
                a = auroc(s_id[yon], s_ood[yon])
                f = fpr95(s_id[yon], s_ood[yon])
                satirlar.append((s, yon, tur, "%.4f" % a, "%.4f" % f))
                if tur == "birlesik" and s == 0:
                    dagilim += [(yon, "id", v) for v in s_id[yon]]
                    dagilim += [(yon, "ood", v) for v in s_ood[yon]]
    print("\nOOD ayrisma (birlesik, 3 tohum ortalama +- sapma)")
    print("yontem        AUROC          FPR@95")
    for yon in ["MSP", "Enerji", "Mahalanobis"]:
        a = np.array(
            [
```

```python
                float(r[3])
                for r in satirlar
                if r[1] == yon and r[2] == "birlesik"
            ]
        )
        f = np.array(
            [
                float(r[4])
                for r in satirlar
                if r[1] == yon and r[2] == "birlesik"
            ]
        )
        print(
            "%-12s  %.3f +- %.3f   %.3f +- %.3f"
            % (yon, a.mean(), a.std(), f.mean(), f.std())
        )
    print("\nOOD turu bazinda AUROC (3 tohum ortalama):")
    for tur in turler:
        for yon in ["MSP", "Enerji", "Mahalanobis"]:
            a = [
                float(r[3])
                for r in satirlar
                if r[1] == yon and r[2] == tur
            ]
            print("%-9s %-12s %.3f" % (tur, yon, np.mean(a)))
    csv_yaz(
        "b78_ood_auroc.csv",
        ["tohum", "yontem", "ood_turu", "auroc", "fpr95"],
        satirlar,
    )
    csv_yaz(
        "b78_ood_skor.csv",
        ["yontem", "grup", "skor"],
        [(a, b, "%.6f" % c) for a, b, c in dagilim],
    )


if __name__ == "__main__":
    main()
```


```term
$ python b78_01_ood.py
tohum  test_dogruluk
    0         0.9472
    1         0.9500
    2         0.9556

OOD ayrisma (birlesik, 3 tohum ortalama +- sapma)
yontem        AUROC          FPR@95
MSP           0.795 +- 0.028   0.716 +- 0.028
Enerji        0.696 +- 0.015   0.819 +- 0.004
Mahalanobis   0.982 +- 0.005   0.073 +- 0.023

OOD turu bazinda AUROC (3 tohum ortalama):
gurultu   MSP          0.828
gurultu   Enerji       0.731
gurultu   Mahalanobis  0.987
leke      MSP          0.763
leke      Enerji       0.661
leke      Mahalanobis  0.978
birlesik  MSP          0.795
birlesik  Enerji       0.696
birlesik  Mahalanobis  0.982
```


Sonuçlara bakalım. Mahalanobis, iki OOD türünde de MSP ve enerjiden belirgin biçimde üstün çıktı: AUROC 0,982 ± 0,005 ve FPR@95 0,073. MSP'nin AUROC'u 0,795 ± 0,028, FPR@95'i 0,716'dır. Yani MSP'yi bir kapı olarak kullanırsak, gerçek girdilerin yüzde 95'ini kabul ederken OOD girdilerin yaklaşık yüzde 72'si de geçer. Enerji skoru bu modelde en zayıf çıkan yöntemdir (AUROC 0,696). Bu, enerjinin "kötü" bir yöntem olduğu anlamına gelmez; yalnızca bu modelde ve bu OOD kümesinde ölçüldü. Bir yöntemin genel üstünlüğü için çok daha fazla model ve veri gerekir.

Şekil 78.2 dağılımları ve AUROC değerlerini gösteriyor.

![Şekil 78.2: MSP ve enerji skorlarında ID ile OOD kümeleri büyük ölçüde iç içe; Mahalanobis skorunda iki küme belirgin biçimde ayrılıyor.](gorseller/b78_ood_skor.png)

MSP histogramında ID ve OOD kümeleri 1,0'a yakın bir tepede birleşiyor. Softmax, OOD girdilere de çoğu zaman yüksek güven verebilir. Bu, softmax'ı tek başına bir güvenlik kapısı yapmanın neden yanıltıcı olduğunu gösterir. Mahalanobis'te ayrım, öznitelik uzayının yapısından gelir. Dolayısıyla ayrım gücü eğitilmiş temsilin kalitesine bağlıdır. Bölüm 73'teki temsil öğrenmenin sağlamlık sorunları burada da geçerlidir: temsil kısa yollara (shortcut) dayanıyorsa, OOD dedektörü de o kısa yolları ölçer.

## 78.4 Belirsizlik: aleatorik ve epistemik, kalibrasyon

Bir tahminin ne kadar emin olduğu iki farklı kaynaktan gelebilir. Aleatorik belirsizlik verinin kendisindeki rastgeleliktir. Bir "1" ile bir "7" birbirine çok benzeyen gürültülü görüntüler olabilir; hiçbir model bunları her zaman mükemmel ayıramaz. Bu belirsizlik daha fazla veriyle azalmaz. Epistemik belirsizlik ise modelin bilgi eksikliğidir: eğitimde hiç görmediğimiz bir bölgede model, kendi parametrelerinin ne olması gerektiğini bilmez. Bu belirsizlik daha fazla veri ve daha iyi bir modelle azalır. Bölüm 49 ve 62'deki Bayesçi bakış açısında bu ayrım, sonsal dağılımın yayılımının iki bileşenidir.

Bu ayrımı bir topluluk (ensemble) üzerinden ölçebiliriz. M model aynı veriyle, farklı tohumlarla eğitilir ve her biri bir olasılık dağılımı p_m(y | x) üretir. Ortalama dağılım p̄ = (1/M) Σ p_m olsun. Toplam belirsizlik H[p̄] ile ölçülür (Shannon entropisi). Aleatorik kısım üyelerin kendi entropilerinin ortalamasıdır: (1/M) Σ H[p_m]. Epistemik kısım ikisinin farkıdır: H[p̄] − (1/M) Σ H[p_m]. Bu fark, karşılıklı bilgi (mutual information) ile aynıdır. Üyeler birbirinden farklı tahmin verdiğinde epistemik kısım büyür; hepsi aynı şeyi söylediğinde küçülür.

Dört yöntemi karşılaştıracağız:

- **Tek model.** Temel referans; softmax olasılığı.
- **Sıcaklık ölçekleme.** Tek modelin logit'lerini bir T değerine bölüp doğrulama kümesinde negatif log-olasılığı (NLL) en küçük yapan T'yi bulmak. Guo ve arkadaşlarının 2017 çalışmasında önerildi (genel bilgi). Bölüm 57'deki kalibrasyon sorununa doğrudan bir çözümdür ve sınıf sırasını değiştirmez; yalnızca güveni yeniden ölçekler.
- **MC dropout.** Eğitimde kullanılan dropout'u test sırasında da açık tutup T = 30 ileri geçiş yapmak. Ortalama olasılık tahmindir; geçişlerin saçılımı epistemik kısmı verir. Gal ve Ghahramani'nin 2016 yaklaşımıdır (genel bilgi). Bölüm 64'teki dropout'un bir yorumudur.
- **Derin topluluk.** Aynı mimari, farklı tohumlarla beş bağımsız model. Lakshminarayanan ve arkadaşlarının 2017 çalışmasında önerildi (genel bilgi). Pahalıdır, ama genellikle güçlü bir taban verir.

Kalibrasyonu ECE ile ölçüyoruz: 15 eşit genişlikli güven kutusunda, kutu içindeki doğruluk ile ortalama güven arasındaki farkın kutu ağırlıklı ortalaması. Güvenilirlik diyagramı kutu başına doğruluğu güvene karşı çizer; köşegen mükemmel kalibrasyondur.

Aşağıdaki betik dört yöntemi üç tohumda karşılaştırır. Sıcaklık T'yi doğrulama kümesinde bulur; test kümesine dokunmaz.

```python
# -*- coding: utf-8 -*-
"""Deney 2: kalibrasyon ve belirsizlik (sicaklik, MC, topluluk)."""

import numpy as np
from scipy.optimize import minimize_scalar
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    ood_uret,
    MLP,
    egit,
    softmax_np,
    logit_np,
    topluluk_egit,
    ece,
    guvenilirlik_kutulari,
    auroc,
    csv_yaz,
)


def sicaklik_bul(z_va, y_va):
    """Dogrulama kumesinde NLL'i en kucuk yapan T."""

    def nll(log_t):
        p = softmax_np(z_va / np.exp(log_t))
        return -np.mean(np.log(p[np.arange(len(y_va)), y_va] + 1e-12))

    r = minimize_scalar(
        nll, bounds=(np.log(0.05), np.log(10.0)), method="bounded"
    )
    return float(np.exp(r.x))


def mc_dropout(model, X, T=30, seed=0):
    """Egitimdeki dropout'u test aninda acik tut; T gecis."""
    import torch

```

```python
    torch.manual_seed(seed + 7)
    model.train()
    with torch.no_grad():
        P = [
            softmax_np(model(torch.tensor(X)).numpy())
            for _ in range(T)
        ]
    model.eval()
    return np.stack(P)


def ayristir(P):
    """P: (T, n, K). Toplam = H[ortalama]; aleatorik = ort(H);
    epistemik = toplam - aleatorik (karsilikli bilgi)."""

    def H(q):
        return -np.sum(q * np.log(q + 1e-12), axis=-1)

    ort = P.mean(0)
    toplam = H(ort)
    ale = H(P).mean(0)
    return ort, ale, toplam - ale


```

```python
def main():
    D = veri_hazirla()
    gur, lek = ood_uret(len(D["Xte"]))
    Xo = np.r_[gur, lek]
    satirlar, kutular = [], []
    print("yontem         acc    ECE    AUROC(guven)  AUROC(epi)")
    for s in SEEDS:
        base = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        zva = logit_np(base, D["Xva"])
        T = sicaklik_bul(zva, D["yva"])
        ens = topluluk_egit(D, s)
        sonuc = {}
        # tek model
        p_te = softmax_np(logit_np(base, D["Xte"]))
        p_oo = softmax_np(logit_np(base, Xo))
        sonuc["Tek model"] = (p_te, p_oo, None, None)
        # sicaklik olcekleme
        sonuc["Sicaklik"] = (
            softmax_np(logit_np(base, D["Xte"]) / T),
            softmax_np(logit_np(base, Xo) / T),
            None,
            None,
        )
        # MC dropout
        Pt = mc_dropout(base, D["Xte"])
        Po = mc_dropout(base, Xo)
        ort_t, ale_t, epi_t = ayristir(Pt)
        ort_o, ale_o, epi_o = ayristir(Po)
        sonuc["MC dropout"] = (
            ort_t,
            ort_o,
            (ale_t, epi_t),
            (ale_o, epi_o),
        )
        # derin topluluk (M = 5)
        Et = np.stack(
            [softmax_np(logit_np(m, D["Xte"])) for m in ens]
        )
        Eo = np.stack([softmax_np(logit_np(m, Xo)) for m in ens])
        ort_t, ale_t, epi_t = ayristir(Et)
```

```python
        ort_o, ale_o, epi_o = ayristir(Eo)
        sonuc["Topluluk"] = (
            ort_t,
            ort_o,
            (ale_t, epi_t),
            (ale_o, epi_o),
        )
        n_te = len(D["Xte"])
        for yon, (pt, po, bt, bo) in sonuc.items():
            acc = (pt.argmax(1) == D["yte"]).mean()
            e = ece(pt, D["yte"])
            a_g = auroc(pt.max(1), po.max(1))
            if bt is not None:
                a_e = auroc(-bt[1], -bo[1])
                ale_id, epi_id = bt[0].mean(), bt[1].mean()
                ale_ood, epi_ood = bo[0].mean(), bo[1].mean()
            else:
                a_e, ale_id, epi_id, ale_ood, epi_ood = (
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            satirlar.append(
                (
                    s,
                    yon,
                    "%.4f" % acc,
                    "%.4f" % e,
                    "%.4f" % a_g,
                    "%.4f" % a_e if a_e != "" else "",
                    "%.5f" % ale_id if ale_id != "" else "",
                    "%.5f" % epi_id if epi_id != "" else "",
                    "%.5f" % ale_ood if ale_ood != "" else "",
                    "%.5f" % epi_ood if epi_ood != "" else "",
                )
            )
            if s == 0:
                for lo, hi, g, d, k in guvenilirlik_kutulari(
```

```python
                    pt, D["yte"]
                ):
                    kutular.append(
                        (
                            yon,
                            "%.4f" % lo,
                            "%.4f" % hi,
                            "%.4f" % g,
                            "%.4f" % d,
                            k,
                        )
                    )
            ae = "%.3f" % a_e if a_e != "" else "   -  "
            print(
                "%-13s %.3f  %.4f  %.3f         %s   (tohum %d)"
                % (yon, acc, e, a_g, ae, s)
            )
        print("  sicaklik T =", round(T, 3), " test n =", n_te)
    print("\nOrtalama +- sapma (3 tohum):")
    for yon in ["Tek model", "Sicaklik", "MC dropout", "Topluluk"]:
        r = [x for x in satirlar if x[1] == yon]
        ec = np.array([float(x[3]) for x in r])
        ag = np.array([float(x[4]) for x in r])
        ae = [float(x[5]) for x in r if x[5] != ""]
        txt = "%.3f +- %.3f" % (ag.mean(), ag.std())
        if ae:
            txt += "  epi %.3f +- %.3f" % (np.mean(ae), np.std(ae))
        print(
            "%-11s ECE %.4f +- %.4f  AUROC %s"
            % (yon, ec.mean(), ec.std(), txt)
        )
    csv_yaz(
        "b78_belirsizlik.csv",
        [
            "tohum",
            "yontem",
            "acc",
            "ece",
            "auroc_guven",
            "auroc_epi",
```

```python
            "ale_id",
            "epi_id",
            "ale_ood",
            "epi_ood",
        ],
        satirlar,
    )
    csv_yaz(
        "b78_kalibrasyon.csv",
        ["yontem", "alt", "ust", "guven", "dogruluk", "sayi"],
        kutular,
    )


if __name__ == "__main__":
    main()
```


```term
$ python b78_02_belirsizlik.py
yontem         acc    ECE    AUROC(guven)  AUROC(epi)
Tek model     0.947  0.0218  0.814            -     (tohum 0)
Sicaklik      0.947  0.0334  0.817            -     (tohum 0)
MC dropout    0.950  0.0276  0.822         0.826   (tohum 0)
Topluluk      0.953  0.0253  0.843         0.910   (tohum 0)
  sicaklik T = 0.78  test n = 360
Tek model     0.950  0.0196  0.816            -     (tohum 1)
Sicaklik      0.950  0.0236  0.819            -     (tohum 1)
MC dropout    0.950  0.0357  0.820         0.819   (tohum 1)
Topluluk      0.953  0.0161  0.836         0.877   (tohum 1)
  sicaklik T = 0.804  test n = 360
Tek model     0.956  0.0173  0.756            -     (tohum 2)
Sicaklik      0.956  0.0294  0.761            -     (tohum 2)
MC dropout    0.953  0.0384  0.794         0.825   (tohum 2)
Topluluk      0.953  0.0171  0.862         0.938   (tohum 2)
  sicaklik T = 0.671  test n = 360

Ortalama +- sapma (3 tohum):
Tek model   ECE 0.0196 +- 0.0018  AUROC 0.795 +- 0.028
Sicaklik    ECE 0.0288 +- 0.0040  AUROC 0.799 +- 0.027
MC dropout  ECE 0.0339 +- 0.0046  AUROC 0.812 +- 0.013  epi 0.823 +- 0.003
Topluluk    ECE 0.0195 +- 0.0041  AUROC 0.847 +- 0.011  epi 0.908 +- 0.025
```


Üç tohumun ortalaması şöyle: tek modelde ECE 0,0196 ± 0,0018, güvene dayalı AUROC 0,795 ± 0,028. Sıcaklık ölçeklemede ECE 0,0288 ± 0,0040 ve AUROC 0,799. MC dropout'ta ECE 0,0339 ± 0,0046, güvene dayalı AUROC 0,812 ve epistemik AUROC 0,823. Topluluğun ECE'si 0,0195 ± 0,0041, güvene dayalı AUROC 0,847 ve epistemik AUROC 0,908 ± 0,025.

Üç gözlem öne çıkıyor.

Birincisi, sıcaklık ölçeklemesi bu veride ECE'yi düşürmedi, artırdı. Doğrulama NLL'sini en küçük yapan T değerleri (0,67 ile 0,80 arası) modelin biraz fazla değil, biraz az özgüvenli olduğunu gösterdi. Yine de test ECE'si yükseldi. Nedeni, 360 örnek ve 15 kutu ile ölçülen ECE'nin gürültülü olması ve NLL ile ECE'nin farklı şeyleri optimize etmesidir. Bu, tek bir kalibrasyon ölçütüne körü körüne güvenmemek gerektiğinin kanıtıdır.

İkincisi, MC dropout epistemik belirsizliği ayırt ediyor (AUROC 0,823) ama kalibrasyonu bozuyor (ECE 0,034). Dropout maskeleri eğitilmiş ağırlıkların bağımsız örnekleri değildir; geçişler arasındaki saçılım, gerçek posterior yayılımının yalnızca kısmi bir tahminidir.

Üçüncüsü, topluluk bu veride hem kalibrasyonda hem OOD ayrımında en güçlü tabandır. Maliyeti M katına çıkar, ama bir taban olarak ölçülmeye değerdir.

Şekil 78.3 güvenilirlik diyagramını ve kalibrasyon hatasını gösteriyor. Diyagramda yalnızca en az beş örnek içeren kutular çizildi; kenar kutularındaki gürültü bu yüzden azaldı.

![Şekil 78.3: Topluluk güvenilirlik diyagramında köşegene en yakın seyreder; sıcaklık ölçekleme bu veride ECE'yi düşürmedi, MC dropout ise kalibrasyonu en çok bozan yöntem oldu.](gorseller/b78_belirsizlik.png)

Bu bölümde bir kuralı tekrar edelim: belirsizlik tahmini bir garanti değildir. İyi bir sıralama üretir: daha belirsiz girdiler üstte, daha emin olanlar altta. Bir sonraki adımda bu sıralamayı bir kapı olarak kullanıp sonlu örneklemde gerçek bir garanti verip veremeyeceğimize bakacağız (78.5).

## 78.5 Uygun tahmin ve seçici tahmin

Önceki bölümdeki yöntemler "ne kadar eminim" sorusuna bir sayı verir. Ama bu sayı bir garanti değildir: yüzde doksan emin olmak, yüzde doksan doğru olmak anlamına gelmez. Uygun tahmin (conformal prediction) başka bir soru sorar: "gerçek etiketi yüzde doksan olasılıkla içerecek küme nedir?" Ve bu soruya, değişim (exchangeability) denen zayıf bir varsayım altında, sonlu örneklemde bile geçerli bir cevap verir.

Bölünmüş (split) conformal yöntemi üç adımda işler. Önce kalibrasyon kümesindeki her örnek için bir uyumsuzluk skoru hesaplanır. En yaygın ve en basit seçim, s = 1 − p(y_gerçek | x) skorudur. İkinci adımda n kalibrasyon skoru sıralanır ve hata düzeyi α'ya göre k = ⌈(n + 1)(1 − α)⌉ inci en küçük değer eşik q olarak alınır. Üçüncü adımda yeni bir girdi için küme, 1 − p_k(x) ≤ q koşulunu sağlayan bütün sınıflardan oluşur. Küme boş da olabilir; bu, modelin hiçbir sınıfa güvenmediği anlamına gelir.

Garanti şudur: eğitim, kalibrasyon ve test örnekleri aynı dağılımdan bağımsız çekildiyse, P(y ∈ C(x)) ≥ 1 − α. Ama bu garanti marjinaldir. Yani bütün olası kalibrasyon kümeleri ve test örnekleri üzerinden ortalamadır; tek bir kalibrasyon kümesi için kapsamanın yüzde doksanın altında kalması mümkündür. Bu ayrım aşağıdaki deneyde görünür olacak.

Seçici tahmin (selective prediction) farklı bir kapı sunar: model güvenilir olmadığı girdilerde karar vermeyi reddeder. Kabul edilen girdilerin oranına (kapsam) karşı, kabul edilenlerdeki hata oranına (risk) bakarız. Bu ilişkiye risk–kapsam eğrisi denir. Güvenlik kritik bir sistemde bu eğri, "kaç girdiye karar veriyoruz ve bu kararlarda hata oranı ne?" sorusunun cevabıdır. Reddedilen girdi operatöre devredilir. Bölüm 46'da anlatılan güvenli varsayılan ve insan onayı ilkesi bu tasarımın ruhudur.

Deneyde üç tohumun topluluk olasılıklarını kullandık. Kalibrasyon kümesi (270 örnek) eşiği belirledi, test kümesi (360 örnek) ölçtü. Ayrıca 200 rastgele bölme ile kapsamanın dağılımına baktık.

```python
# -*- coding: utf-8 -*-
"""Deney 3: bolunmus conformal ve secici tahmin (risk-kapsam)."""

import numpy as np
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    topluluk_egit,
    softmax_np,
    logit_np,
    csv_yaz,
)

ALFALAR = [0.01, 0.05, 0.10, 0.20, 0.30]


def konformal_esik(p_cal, y_cal, alpha):
    """Sinif-temelli skor s = 1 - p(dogru sinif). Sonlu ornek
    duzeltmesi: k = ceil((n + 1)(1 - alpha)) inci kucuk skor."""
    n = len(y_cal)
    s = np.sort(1.0 - p_cal[np.arange(n), y_cal])
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return float(s[k - 1]) if k <= n else np.inf


def konformal_kume(p, q):
    """C(x) = {k : 1 - p_k(x) <= q}; boolean matris (n, K)."""
    return (1.0 - p) <= q


def risk_kapsam(guven, hatali, izgara):
    """Kabul oranina gore risk (kabul edilenlerde hata orani)."""
    n = len(hatali)
    out = []
    for k in izgara:
        m = max(1, int(np.ceil(k * n)))
        sec = np.argsort(-guven, kind="stable")[:m]
        out.append((k, hatali[sec].mean()))
    return out

```

```python
def main():
    D = veri_hazirla()
    print(
        "Bolunme: egitim %d, dogrulama %d, kalibrasyon %d, test %d"
        % (len(D["ytr"]), len(D["yva"]), len(D["yca"]), len(D["yte"]))
    )
    izgara = np.round(np.linspace(1.0, 0.3, 15), 3)
    satirlar, rk, tekrar_say = [], [], []
    for s in SEEDS:
        ens = topluluk_egit(D, s)
        Pca = np.mean(
            [softmax_np(logit_np(m, D["Xca"])) for m in ens], 0
        )
        Pte = np.mean(
            [softmax_np(logit_np(m, D["Xte"])) for m in ens], 0
        )
        for a in ALFALAR:
            q = konformal_esik(Pca, D["yca"], a)
            K = konformal_kume(Pte, q)
            kap = K[np.arange(len(D["yte"])), D["yte"]].mean()
            boy = K.sum(1)
            satirlar.append(
                (
                    s,
                    a,
                    "%.4f" % kap,
                    "%.4f" % boy.mean(),
                    "%.4f" % (boy == 1).mean(),
                    "%.4f" % (1 - a),
                )
            )
        # secici tahmin: guven = maks. olasilik; alt. = kume boyu
        hatali = (Pte.argmax(1) != D["yte"]).astype(float)
        boy = konformal_kume(
            Pte, konformal_esik(Pca, D["yca"], 0.10)
        ).sum(1)
        for yon, anahtar in [
            ("maks_olasilik", Pte.max(1)),
            ("kume_boyu", -boy + Pte.max(1)),
        ]:
```

```python
            for k, r in risk_kapsam(anahtar, hatali, izgara):
                rk.append((s, yon, "%.3f" % k, "%.4f" % r))
        if s == 0:
            # sonlu ornek: 200 rastgele kalibrasyon/test bolmesi
            P = np.r_[Pca, Pte]
            y = np.r_[D["yca"], D["yte"]]
            rng = np.random.default_rng(1)
            for _ in range(200):
                perm = rng.permutation(len(y))
                i_c, i_t = (
                    perm[: len(D["yca"])],
                    perm[len(D["yca"]) :],
                )
                q = konformal_esik(P[i_c], y[i_c], 0.10)
                K = konformal_kume(P[i_t], q)
                tekrar_say.append(
                    K[np.arange(len(i_t)), y[i_t]].mean()
                )
    print("\nalfa  nominal  kapsama(ort+-sd)  kume_boyu  tekil")
    for a in ALFALAR:
        r = np.array(
            [
                [float(x[2]), float(x[3]), float(x[4])]
                for x in satirlar
                if x[1] == a
            ]
        )
        print(
            "%.2f   %.2f     %.4f +- %.4f    %.3f      %.3f"
            % (
                a,
                1 - a,
                r[:, 0].mean(),
                r[:, 0].std(),
                r[:, 1].mean(),
                r[:, 2].mean(),
            )
        )
    t = np.array(tekrar_say)
    print("\n200 yeniden bolme (alfa = 0.10, tohum 0):")
```

```python
    print("  kapsama ort = %.4f  sd = %.4f" % (t.mean(), t.std()))
    print(
        "  en dusuk = %.4f  %%5 = %.4f  %%95 = %.4f"
        % (t.min(), np.percentile(t, 5), np.percentile(t, 95))
    )
    print(
        "  nominal 0.90 altinda kalan bolme: %d / 200"
        % (t < 0.9).sum()
    )
    print("\nRisk-kapsam (tohum 0, maks_olasilik ve kume_boyu):")
    for yon in ["maks_olasilik", "kume_boyu"]:
        r = [x for x in rk if x[0] == 0 and x[1] == yon]
        for x in r[::4]:
            print("  %-14s kapsam %s  risk %s" % (yon, x[2], x[3]))
    csv_yaz(
        "b78_conformal.csv",
        [
            "tohum",
            "alfa",
            "kapsama",
            "kume_boyu",
            "tekil_oran",
            "nominal",
        ],
        satirlar,
    )
    csv_yaz(
        "b78_conformal_tekrar.csv",
        ["kapsama"],
        [("%.5f" % v,) for v in t],
    )
    csv_yaz(
        "b78_riskkapsam.csv",
        ["tohum", "yontem", "kapsam", "risk"],
        rk,
    )


if __name__ == "__main__":
    main()
```


```term
$ python b78_03_conformal.py
Bolunme: egitim 898, dogrulama 269, kalibrasyon 270, test 360

alfa  nominal  kapsama(ort+-sd)  kume_boyu  tekil
0.01   0.99     0.9908 +- 0.0013    1.182      0.868
0.05   0.95     0.9417 +- 0.0099    0.976      0.976
0.10   0.90     0.8732 +- 0.0047    0.880      0.880
0.20   0.80     0.7621 +- 0.0151    0.765      0.765
0.30   0.70     0.6843 +- 0.0086    0.687      0.687

200 yeniden bolme (alfa = 0.10, tohum 0):
  kapsama ort = 0.8992  sd = 0.0258
  en dusuk = 0.8139  %5 = 0.8554  %95 = 0.9390
  nominal 0.90 altinda kalan bolme: 89 / 200

Risk-kapsam (tohum 0, maks_olasilik ve kume_boyu):
  maks_olasilik  kapsam 1.000  risk 0.0472
  maks_olasilik  kapsam 0.800  risk 0.0035
  maks_olasilik  kapsam 0.600  risk 0.0000
  maks_olasilik  kapsam 0.400  risk 0.0000
  kume_boyu      kapsam 1.000  risk 0.0472
  kume_boyu      kapsam 0.800  risk 0.0556
  kume_boyu      kapsam 0.600  risk 0.0694
  kume_boyu      kapsam 0.400  risk 0.1042
```


Ölçüm sonuçlarını tabloda topladık. Değerler üç tohumun ortalaması ± standart sapma.

| α | Nominal kapsama | Ölçülen kapsama | Ort. küme boyu | Tekil küme oranı |
|---|---|---|---|---|
| 0,01 | 0,99 | 0,9908 ± 0,0013 | 1,182 | 0,868 |
| 0,05 | 0,95 | 0,9417 ± 0,0099 | 0,976 | 0,976 |
| 0,10 | 0,90 | 0,8732 ± 0,0047 | 0,880 | 0,880 |
| 0,20 | 0,80 | 0,7621 ± 0,0151 | 0,765 | 0,765 |
| 0,30 | 0,70 | 0,6843 ± 0,0086 | 0,687 | 0,687 |

Tablo üç şeyi söylüyor. Birincisi, α = 0,10 için üç tohumun tamamında ölçülen kapsama 0,90'ın altında kaldı (ortalama 0,873). Bu bir garanti ihlali midir? Hayır. 200 rastgele bölmenin ortalaması 0,899 (sapma 0,026); yani garanti ortalamada tutuyor. Ama 200 bölmenin 89'unda kapsama yüzde doksanın altında kaldı. Bu, tek bir kalibrasyon kümesinden çıkan sonucu "garanti bozuldu" diye okumamak gerektiğini gösterir. Tek bir kalibrasyon kümesi için koşullu garanti gerekiyorsa, PAC tipi ayrı bir yöntem gerekir (genel bilgi). Bu deneyde bu yöntem yok.

İkincisi, α ≥ 0,05 için ortalama küme boyu ile tekil küme oranı birbirine eşit çıktı. Bu, çoklu etiketli kümenin neredeyse hiç oluşmadığı anlamına gelir: küme ya tek bir sınıf içerir ya da boştur. α = 0,01'de ise küme boyu (1,182) tekil oranı (0,868) geçiyor; sıkı garantinin bedeli, bazı girdilerde "bu iki sınıftan biri olabilir" yanıtıdır.

Üçüncüsü, 200 bölmenin dağılımı sınırlı genişliktedir. Kapsama 5. yüzdelikte 0,855, 95. yüzdelikte 0,939. Bu aralık, tek bir ölçümün ne kadar oynayabileceğini gösterir ve bu yüzden tek bir kapsama sayısını kesin bir değer gibi sunmak yanıltıcı olur.

Şekil 78.4 kapsamanın nominal değere göre nasıl durduğunu ve küme boyunun α ile nasıl değiştiğini gösteriyor.

![Şekil 78.4: Ölçülen kapsama nominal değerin hemen altında kalıyor; küme boyu ve tekil oran α küçüldükçe ayrışıyor.](gorseller/b78_conformal_kapsama.png)

Seçici tahmin için iki sıralama karşılaştırdık. Birincisi en büyük olasılığa göre sıralama (kabul edilecek en emin girdiler önce). İkincisi küme boyuna göre sıralama (küçük küme önce, eşitlikte olasılığa bakılır). Tohum 0 için sonuçlar:

- En büyük olasılık sıralamasında kapsam 1,0 iken risk 0,0472'dir (360 örnekte 17 hata). Kapsam yüzde 80'e düştüğünde risk 0,0035'e iner.
- Küme boyu sıralamasında kapsam yüzde 80 iken risk 0,0556, yüzde 40 iken 0,1042'dir.

Bu veride en büyük olasılık sıralaması küme boyu sıralamasından belirgin biçimde üstündür. Küme boyu, olasılık vektörünün kaba bir özetidir ve bu deneyde ek bir bilgi getirmedi. Hangi sıralamanın kullanılacağı, her zaman bir deneyle seçilmelidir.

Şekil 78.5, risk–kapsam eğrisini üç tohumun ortalaması olarak gösteriyor.

![Şekil 78.5: Risk–kapsam eğrisi: kapsam düştükçe en büyük olasılık sıralamasının riski hızla sıfıra iner; küme boyu sıralaması ise riski artırır.](gorseller/b78_risk_kapsam.png)

Bu eğriyi bir tasarım aracı olarak kullanın. Hangi riski kabul edeceğinize, reddedilen girdilerin operatöre ne kadar yük getireceğine karar verirken eğrinin üzerindeki noktayı seçersiniz. Bu karar bir mühendislik kararıdır ama bir maliyet kararıdır da. Bölüm 72'de sensör örneğinde gördüğümüz gibi, kaçırılan bir olayın maliyeti yanlış alarmdan çoğu zaman çok daha büyüktür. Eşik bu asimetriye göre seçilmelidir; yüzde 95 gibi bir sabit kural, bir sistemin gerçek gereksinimlerinin yerine geçmez.

## 78.6 Çekişmeli sağlamlık: ölçmek

Bölüm 66'da çekişmeli örneklerin varlığından ve insan gözüne görünmeyen küçük değişikliklerle bir modelin yanıltılabildiğinden kavramsal olarak söz etmiştik. Burada bunu bir ölçüme çeviriyoruz. Amacımız bir saldırganın işine yarayacak bir araç yapmak değil. Amacımız, bir modelin hangi büyüklükteki değişikliklerde çöktüğünü ölçmek ve bir savunmanın gerçekten işe yarayıp yaramadığını göstermektir.

Bir saldırıyı tanımlamadan önce tehdit modelini yazarız. Üç soruya cevap verilir. Bilgi: saldırgan modelin iç yapısına (ağırlıklar, gradyanlar) mı erişiyor (beyaz kutu), yoksa yalnızca çıktıları mı görüyor (kara kutu)? Değerlendirmede beyaz kutu en kötü durum olduğu için savunmayı bu senaryoya göre ölçeriz. Bütçe: girdiye ne kadarlık bir değişiklik yapılabilir? Bizim seçimimiz L∞ normudur: her piksel en fazla ε kadar değişebilir. Bu normun matematiği Bölüm 48'deki vektör normlarıdır. Hedef: yalnızca yanlış bir sınıfa düşürmek mi (yanlış sınıflandırma), yoksa belirli bir sınıfı hedeflemek mi? Bu bölümde yalnızca yanlış sınıflandırmayla ilgileniyoruz.

L∞ ε-topu, x'in her bileşeni en fazla ε kadar oynayabilen komşuluğudur: B(x, ε) = {x' : ‖x' − x‖∞ ≤ ε}. Sağlam doğruluk, bu topun içindeki her girdide doğru sınıflandırılan örneklerin oranıdır. Bu bir en kötü durum ölçüsüdür ve bir alt sınır (sertifika) hedefler.

İki standart saldırı kullanacağız. FGSM (Goodfellow ve arkadaşları, 2015; genel bilgi), kayıp fonksiyonunun girdiye göre gradyanının işaretini tek adımda uygular: x' = kırp(x + ε · sign(∇ₓL), 0, 1). Hızlı ama zayıftır. PGD (Madry ve arkadaşları, 2018; genel bilgi), FGSM'in çok adımlı ve rastgele başlangıçlı biçimidir. Her adımda küçük bir hareket yapılır ve sonuç her adımda ε-topuna geri izdüşürülür. Sağlamlık değerlendirmesinde standart "güçlü" saldırı budur.

Bir ilke baştan belirlenmelidir: bir saldırıyla ölçülen sağlam doğruluk, gerçek sağlam doğruluğun bir üst sınırıdır. Saldırı yalnızca kendi bulabildiği çekişmeli örnekleri sayar; daha güçlü bir saldırı daha fazla yanıltıcı girdi bulabilir. Bu yüzden zayıf bir saldırıyla ölçülen sağlamlık her zaman iyimser çıkar. Bir savunmayı değerlendirirken yapılacak ilk iş, saldırıyı güçlendirmektir.

Aşağıdaki betik ilk olarak standart modeli ε'nun yedi değerinde FGSM ve PGD (40 adım, CE kaybı) ile ölçer. Bu betikte ayrıca iki deney daha var; onları 78.6'nın gradyan maskeleme kısmında ve 78.7'de açıklayacağız. Betik, çekişmeli eğitimi tanımlayan `at_kayip` fonksiyonunu da içerir.

```python
# -*- coding: utf-8 -*-
"""Deney 4: FGSM/PGD ile saglamlik olcumu, gradyan maskeleme
ornegi ve PGD ile cekismeli egitim (degerlendirme amacli)."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    MLP,
    egit,
    pgd,
    dogruluk,
    csv_yaz,
)

EPSLER = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
AT_EPS, AT_ADIM = 0.10, 7


class Olcekli(nn.Module):
    """Logitleri k ile carpar: argmax degismez, softmax doyar."""

    def __init__(self, m, k):
        super().__init__()
        self.m, self.k = m, k

    def forward(self, x):
        return self.m(x) * self.k


```

```python
def at_kayip(model, xb, yb, ep, E):
    """Madry tarzi: her grupta PGD ornegiyle egit."""
    xa = pgd(
        model,
        xb.numpy(),
        yb.numpy(),
        AT_EPS,
        adim_say=AT_ADIM,
        seed=int(np.random.randint(10**6)),
    )
    model.train()
    return F.cross_entropy(model(torch.tensor(xa)), yb)


def eps_egrisi(model, X, y, saldiri, kayip="ce"):
    out = []
    for e in EPSLER:
        if e == 0.0:
            out.append(dogruluk(model, X, y))
            continue
        if saldiri == "FGSM":
            Xa = pgd(
                model,
                X,
                y,
                e,
                adim_say=1,
                adim=e,
                rastgele=False,
                kayip=kayip,
            )
        else:
            Xa = pgd(model, X, y, e, adim_say=40, kayip=kayip)
        out.append(dogruluk(model, Xa, y))
    return out


```

```python
def main():
    D = veri_hazirla()
    X, y = D["Xte"], D["yte"]
    satirlar = []
    print("1) Standart model: eps'a gore dogruluk (ce kaybi)")
    print("tohum saldiri  " + "  ".join("%.2f" % e for e in EPSLER))
    for s in SEEDS:
        std = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        for sal in ["FGSM", "PGD"]:
            c = eps_egrisi(std, X, y, sal)
            print(
                "%5d %-6s " % (s, sal)
                + "  ".join("%.3f" % v for v in c)
            )
            for e, v in zip(EPSLER, c):
                satirlar.append((s, "standart", sal, e, "%.4f" % v))
    print("\n2) Gradyan maskeleme ornegi (tohum 0, k = 10^4)")
    std = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=0)
    mas = Olcekli(std, 1e4)
    xt, yt = torch.tensor(X), torch.tensor(y)
    xt.requires_grad_(True)
    kayip = -torch.log(
        torch.softmax(mas(xt), 1).gather(1, yt[:, None]).squeeze(1)
    )
    (gx,) = torch.autograd.grad(kayip.sum(), xt)
    sifir = float((gx.abs().sum(1) == 0).float().mean())
    print(
        "  naif kaybin girdi gradyani tam sifir orani: %.3f" % sifir
    )
    for ad, mod, sal_kay, rast, a in [
        ("standart", std, "ce", False, 1),
        ("maskeli", mas, "naif", False, 1),
        ("maskeli", mas, "naif", True, 40),
        ("maskeli", mas, "marj", True, 40),
    ]:
        for e in [0.05, 0.10]:
            Xa = pgd(
                mod,
                X,
                y,
```

```python
                e,
                adim_say=a,
                kayip=sal_kay,
                rastgele=rast,
                adim=(e if a == 1 else None),
            )
            v = dogruluk(mod, Xa, y)
            ad2 = "FGSM" if a == 1 else "PGD"
            if sal_kay == "naif":
                ad2 += "-naif"
            elif sal_kay == "marj":
                ad2 += "-marj"
            print(
                "  %-8s %-10s eps=%.2f  dogruluk=%.3f"
                % (ad, ad2, e, v)
            )
            satirlar.append(
                (0, "maskeleme_" + ad, ad2, e, "%.4f" % v)
            )
    print("\n3) PGD ile cekismeli egitim (eps = 0.10, 7 adim)")
    print("tohum  model     temiz   eps=0.05  eps=0.10  eps=0.20")
    for s in SEEDS:
        at = egit(
            MLP(0.2), D["Xtr"], D["ytr"], seed=s, kayip=at_kayip
        )
        std = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        for ad, m in [("standart", std), ("PGD-AT", at)]:
            c = eps_egrisi(m, X, y, "PGD")
            print(
                "%5d  %-8s %.3f   %.3f    %.3f    %.3f"
                % (s, ad, c[0], c[2], c[3], c[5])
            )
            for e, v in zip(EPSLER, c):
                satirlar.append((s, ad, "PGD", e, "%.4f" % v))
    csv_yaz(
        "b78_saglamlik.csv",
        ["tohum", "model", "saldiri", "eps", "dogruluk"],
        satirlar,
    )

```

```python
if __name__ == "__main__":
    main()
```


```term
$ python b78_04_saldiri.py
1) Standart model: eps'a gore dogruluk (ce kaybi)
tohum saldiri  0.00  0.02  0.05  0.10  0.15  0.20  0.30
    0 FGSM   0.947  0.922  0.811  0.500  0.172  0.022  0.000
    0 PGD    0.947  0.919  0.797  0.411  0.081  0.000  0.000
    1 FGSM   0.950  0.936  0.819  0.494  0.178  0.019  0.000
    1 PGD    0.950  0.936  0.814  0.422  0.089  0.000  0.000
    2 FGSM   0.956  0.917  0.817  0.517  0.186  0.050  0.000
    2 PGD    0.956  0.917  0.794  0.444  0.097  0.003  0.000

2) Gradyan maskeleme ornegi (tohum 0, k = 10^4)
  naif kaybin girdi gradyani tam sifir orani: 0.947
  standart FGSM       eps=0.05  dogruluk=0.811
  standart FGSM       eps=0.10  dogruluk=0.500
  maskeli  FGSM-naif  eps=0.05  dogruluk=0.947
  maskeli  FGSM-naif  eps=0.10  dogruluk=0.947
  maskeli  PGD-naif   eps=0.05  dogruluk=0.950
  maskeli  PGD-naif   eps=0.10  dogruluk=0.944
  maskeli  PGD-marj   eps=0.05  dogruluk=0.803
  maskeli  PGD-marj   eps=0.10  dogruluk=0.467

3) PGD ile cekismeli egitim (eps = 0.10, 7 adim)
tohum  model     temiz   eps=0.05  eps=0.10  eps=0.20
    0  standart 0.947   0.797    0.411    0.000
    0  PGD-AT   0.950   0.892    0.789    0.283
    1  standart 0.950   0.814    0.422    0.000
    1  PGD-AT   0.944   0.886    0.764    0.289
    2  standart 0.956   0.794    0.444    0.003
    2  PGD-AT   0.947   0.897    0.761    0.269
```


Üç tohumun ortalamasını ε'ya göre tabloya koyduk (doğruluk):

| Saldırı | 0 | 0,02 | 0,05 | 0,10 | 0,15 | 0,20 |
|---|---|---|---|---|---|---|
| FGSM | 0,951 | 0,925 | 0,816 | 0,504 | 0,179 | 0,031 |
| PGD-40 | 0,951 | 0,924 | 0,802 | 0,426 | 0,089 | 0,001 |

Tablo açıktır: ε = 0,02 (piksel aralığının yüzde ikisi) doğruluğu yalnızca yüzde üç düşürüyor. ε = 0,10'da doğruluk yarıya iniyor (PGD ile 0,43). ε = 0,20'de standart model neredeyse hiç doğru tahmin yapamıyor. PGD her ε'da FGSM'den düşük ya da ona eşit çıkar; ε = 0,05'te fark küçüktür (0,014), ε = 0,10'da belirgindir (0,078). Fark, FGSM'in tek adım olmasının sonucudur. Ölçümün ilkesi yine aynıdır: saldırı ne kadar güçlüyse ölçülen sağlamlık o kadar gerçeğe yakındır.

### 78.6.1 Gradyan maskeleme: sahte güvenlik

Bazı savunmalar gerçek sağlamlık kazanmaz; saldırının kullandığı gradyanı bilgilendirici olmaktan çıkarırlar. Gradyan tabanlı saldırı kör olunca ölçüm yüksek sağlamlık gösterir, ama bu sağlamlık gerçek değildir. Athalye ve arkadaşları 2018'de bu durumun birçok önerilen savunmada görüldüğünü gösterdi (genel bilgi).

Mekanizma softmax'ın doygunluğudur. Logit'ler büyüdüğünde softmax olasılığı kayan nokta hassasiyetinde tam 1,0 olur; doğru sınıfın olasılığının logaritması sıfırlanır ve gradyan kesin olarak sıfır çıkar. Gradyanın işareti sıfır olunca FGSM hiçbir hareket yapmaz. Sonuç olarak saldırı "başarısız" görünür.

Deneyin ikinci bölümü bunu gösteriyor. Standart modelin logit'lerini k = 10⁴ ile çarpıyoruz. Argmax değişmediği için model aynı kararları verir, yani gerçekte hiçbir şey değişmez. Ama softmax doyar. Naif kayıpla (softmax sonrası log) yapılan FGSM ve PGD bu modelde sahte bir sağlamlık ölçer. Marj kaybı (logit uzayında doğru sınıf ile en iyi yanlış sınıf arasındaki fark) doygunluktan etkilenmez ve gerçek değere yakın bir sonuç verir.

Aşağıdaki tablo tohum 0 için sonuçları özetliyor. Doygunluk nedeniyle naif kayıpla hesaplanan gradyanın tam sıfır olduğu örneklerin oranı 0,947'dir; bu, doğru sınıflandırılan örneklerin oranıyla aynıdır.

| Model | Saldırı | ε = 0,05 | ε = 0,10 |
|---|---|---|---|
| Standart | FGSM (CE) | 0,811 | 0,500 |
| Maskeli | FGSM-naif | 0,947 | 0,947 |
| Maskeli | PGD-naif | 0,950 | 0,944 |
| Maskeli | PGD-marj | 0,803 | 0,467 |

Ders açıktır. Naif kaybın gösterdiği 0,947 sağlamlık yanılsamadır; marj kaybıyla PGD ise standart modelin gerçek değerine (0,467 ile 0,500 arası) yakın bir sonuç verir. Bir savunmayı değerlendirirken en az bir gradyan tabanlı olmayan ya da marj tabanlı saldırı eklemeli ve gradyanın sıfır olup olmadığını kontrol etmelisiniz. Bugün standart değerlendirme paketleri (AutoAttack gibi, genel bilgi) bu yüzden birden çok saldırıyı birleştirir.

Gradyan maskelemenin dersi kısadır: bir savunmanın sağlamlığını, yalnızca kendi ürettiği gradyanla ölçmek yeterli değildir. Ölçüm, savunmadan bağımsız bir saldırıyla yapılmalıdır.

## 78.7 Savunmalar: çekişmeli eğitim, sertifikalı sağlamlık

Savunmaları üç sınıfa ayırabiliriz. Birincisi eğitimde sağlamlık: modeli en kötü durum girdileriyle eğitmek. İkincisi sertifikalı sağlamlık: belirli bir yarıçap içinde kararın değişmediğini matematiksel olarak kanıtlamak. Üçüncüsü tespit: 78.3–78.5'te gördüğümüz OOD ve belirsizlik kapıları. Tespit saldırıyı engellemez; ama saldırıyı ya da olağandışı girdiyi fark edip kararı reddedebilir.

### Çekişmeli eğitim (PGD-AT)

Madry ve arkadaşlarının 2018 önerisine göre (genel bilgi) her eğitim grubundaki girdiler, ε-topunun içinde PGD ile en kötü hâle getirilir ve model bu girdilerle eğitilir: min_θ max_{‖δ‖∞ ≤ ε} L(θ, x + δ, y). İç maksimizasyon saldırıdır, dış minimizasyon savunmadır. Bölüm 50'deki optimizasyon çerçevesiyle okunan bir min–max problemidir. Takasın iki yanı vardır: temiz doğruluk çoğu zaman biraz düşer; eğitim maliyeti de PGD adım sayısı kadar artar.

Deneyde ε = 0,10 ve 7 adımlı PGD ile eğitilmiş bir modeli standart modelle karşılaştırdık. Tablo üç tohumun ortalamasıdır.

| Model | Temiz | ε = 0,05 | ε = 0,10 | ε = 0,20 |
|---|---|---|---|---|
| Standart | 0,951 | 0,802 | 0,426 | 0,001 |
| PGD-AT | 0,947 | 0,892 | 0,771 | 0,281 |

Çekişmeli eğitim bu veride temiz doğruluğu yalnızca 0,004 düşürdü, ama ε = 0,10'da sağlam doğruluğu 0,43'ten 0,77'ye çıkardı. Bu tablodaki temiz doğruluk kaybını genellemek tehlikelidir: 8 × 8 piksellik bu kolay veri kümesinde takas küçük kaldı; büyük ve karmaşık görevlerde temiz doğruluk kaybı genellikle daha belirgindir (genel bilgi). Eğitimde kullanılmayan ε = 0,20'de de durum değişti: standart modelin sağlam doğruluğu 0,001 iken PGD-AT modeli 0,281 verdi. Yani eğitim, kullanılan ε'nun çevresinde bir miktar genelleme sağladı, ama bu genelleme sınırsız değildir.

Şekil 78.6 hem eğrileri hem de gradyan maskeleme sonuçlarını gösteriyor.

![Şekil 78.6: Sol: PGD-AT, ε arttıkça standart modelden çok daha yavaş düşer. Sağ: naif kayıpla ölçülen sağlamlık sahte bir yüksek değer verir; marj kaybı gerçek düşüşü gösterir.](gorseller/b78_saglamlik.png)

### Sertifikalı sağlamlık: rastgele düzgünleştirme

Saldırı ölçümü bir alt sınır vermez: daha güçlü bir saldırı bulunabilir. Sertifika ise bir üst sınır (yanlış karar vermeyeceğine dair kanıt) verir. Rastgele düzgünleştirme (randomized smoothing), Cohen ve arkadaşlarının 2019 önerisine göre (genel bilgi), bunu büyük bir sınıflandırıcıdan sağlar.

Yöntem şöyledir. Girdiye Gauss gürültüsü N(0, σ²I) eklenip ağ birçok kez çalıştırılır ve en çok oy alan sınıf seçilir: g(x) = argmax_c P(f(x + δ) = c). En büyük sınıfın olasılığının alt sınırı p_A > 1/2 ise, ‖δ‖₂ < R = σ · Φ⁻¹(p_A) yarıçapında g(x) sabit kalır. Φ⁻¹ normal dağılımın ters kümülatif fonksiyonudur. Burada ikinci en olası sınıfın olasılığını 1 − p_A ile sınırlıyoruz; bu, R'yi biraz küçültür ve güvenli taraftadır.

Dikkat: bu sertifika L2 normunda konuşur, L∞'da değil. İki sertifika farklı tehdit modellerine aittir ve doğrudan karşılaştırılamaz. Ayrıca yarıçap, p_A'nın üst sınırıyla sınırlıdır: n = 1000 örnekle ve α = 0,001 güven düzeyinde p_A en fazla yaklaşık 0,993 olabilir ve bu da σ = 0,25 için R ≈ 0,62 üst sınırını verir.

Deneyde gürültü ile eğitilmiş modeller (σ = 0,25) üzerinde 100 test örneğini sertifikaladık. Seçim için 100, tahmin için 1000 örnek kullandık ve alt sınırı Clopper–Pearson yöntemiyle hesapladık. Üç tohumun ortalaması:

| r (L2) | 0,0 | 0,1 | 0,2 | 0,3 | 0,4 | 0,5 |
|---|---|---|---|---|---|---|
| Sertifikalı doğruluk | 0,903 | 0,860 | 0,780 | 0,683 | 0,540 | 0,373 |

Sertifikalı doğruluk r ile düşer, çünkü R = σΦ⁻¹(p_A) olduğundan büyük bir yarıçapa ulaşmak için p_A'nın daha yüksek olması gerekir; gürültülü örneklerde bu olasılık düşer. r = 0 satırındaki 0,903, çekimserlerin yanlış sayıldığı düzgünleştirilmiş sınıflandırıcının doğruluğudur. Her tohumda 100 örnekten 4 ya da 5'i çekimser kaldı: alt sınır 0,5'i geçemedi ve karar verilmedi. Bu örnekler sertifikalı doğrulukta yanlış sayılır.

### Aralık sınırı yayılımı (IBP)

Rastgele düzgünleştirme bir olasılık deneyine dayanır. Aralık sınırı yayılımı (interval bound propagation, IBP) ise deterministik bir yöntemdir ve tek bir geçişte çalışır. Girdi, [x − ε, x + ε] kutusu olarak düşünülür ve her katmanda bu kutu bir kutuya dönüşür.

Bir doğrusal katman y = Wx + b için kutunun orta noktası c ve yarıçapı r olsun. Çıkış kutusunun orta noktası Wc + b, yarıçapı |W| r olur. Yarıçap |W| ile çarpılır: her ağırlığın mutlak değeri, girdideki belirsizliğin çıkışa ne kadar taşındığını söyler. ReLU kutuyu [l, u] → [max(l, 0), max(u, 0)] biçiminde keser. Çıkıştaki logit kutularında doğru sınıfın alt sınırı, diğer sınıfların üst sınırlarının hepsinden büyükse, ε yarıçapındaki her girdi için karar sabittir ve bu sertifikadır.

IBP hızlıdır ama gevşektir. Her katmanda iki girdi arasındaki bağımlılığı yok sayar. Aşağıdaki çözümlü örnekte bu gevşekliği elle göreceğiz. Gevşeklik bir engel gibi görünse de IBP'nin sertifikalı eğitimde kayıp olarak kullanılmasının nedeni budur. Gowal ve arkadaşları 2018'de (genel bilgi) modeli, yayılım sınırı dar kalacak biçimde eğittiler. Böylece sınır, eğitimin kendisinin hedefi hâline geldi.

Bu bölümde iki şey yaptık: IBP'yi sıfırdan numpy ile yazdık, sonra torch sürümüyle karşılaştırdık ve rastgele noktalarla sınırları doğruladık. Ardından IBP ile eğitilmiş bir model ile standart modeli sertifikalı doğrulukta karşılaştırdık.

```python
# -*- coding: utf-8 -*-
"""Deney 5: sertifikali saglamlik. (A) rastgele duzgunlestirme,
(B) IBP: sifirdan sinir yayilimi, dogrulama ve IBP egitimi."""

import numpy as np
import torch
import torch.nn.functional as F
from scipy.stats import beta, norm
from b78_ortak import SEEDS, veri_hazirla, MLP, egit, pgd, csv_yaz

SIGMA = 0.25  # Gauss gurultu olcegi (piksel birimi, L2)
IBP_EPS = 0.03  # IBP egitiminde L-inf yaricapi
EPS_IBP = [0.005, 0.01, 0.02, 0.03]


def gurultu_kayip(model, xb, yb, ep, E):
    xn = xb + SIGMA * torch.randn_like(xb)
    return F.cross_entropy(model(xn), yb)


def ibp_torch(model, x, eps):
    """Egitim icin tensor surumu: [x - eps, x + eps] kutusunun
    logit sinirlari. Her dogrusal katmanda orta/yaricap."""
    lo, hi = x - eps, x + eps
    for lin, relu in [
        (model.f1, True),
        (model.f2, True),
        (model.cik, False),
    ]:
        orta, yar = (hi + lo) / 2, (hi - lo) / 2
        orta = lin(orta)
        yar = yar @ lin.weight.abs().T
        lo, hi = orta - yar, orta + yar
        if relu:
            lo, hi = lo.clamp(min=0), hi.clamp(min=0)
    return lo, hi


```

```python
def ibp_kayip(model, xb, yb, ep, E):
    """Gowal tarzi karma kayip: kappa 1 -> 0.5, eps 0 -> IBP_EPS."""
    r = min(1.0, ep / (0.5 * E))
    eps, kap = IBP_EPS * r, 1.0 - 0.5 * r
    lo, hi = ibp_torch(model, xb, eps)
    kotu = torch.where(F.one_hot(yb, 10).bool(), lo, hi)
    return kap * F.cross_entropy(model(xb), yb) + (
        1 - kap
    ) * F.cross_entropy(kotu, yb)


def ibp_np(agirliklar, lo, hi):
    """Sifirdan numpy IBP: W, b katman listesi; ReLU sonrasi."""
    son = len(agirliklar) - 1
    for k, (W, b) in enumerate(agirliklar):
        orta, yar = (lo + hi) / 2, (hi - lo) / 2
        orta = orta @ W.T + b
        yar = yar @ np.abs(W).T
        lo, hi = orta - yar, orta + yar
        if k < son:
            lo, hi = np.maximum(lo, 0), np.maximum(hi, 0)
    return lo, hi


def agirliklar_np(model):
    return [
        (
            l.weight.detach().double().numpy(),
            l.bias.detach().double().numpy(),
        )
        for l in [model.f1, model.f2, model.cik]
    ]


```

```python
def sertifiye(lo, hi, y):
    """Dogru sinifin alt siniri, diger siniflarin ust sinirlarindan
    buyukse ornek sertifikalidir."""
    idx = np.arange(len(y))
    ust = hi.copy()
    ust[idx, y] = -np.inf
    return lo[idx, y] > ust.max(1)


def rs_sertifika(model, x, n0=100, n=1000, alfa=0.001, rng=None):
    """Cohen (2019) yaklasimi: secim ornekleri ile sinifi sec,
    tahmin ornekleriyle pA alt sinirini Clopper-Pearson ile bul."""

    def oy(k):
        g = rng.normal(0, SIGMA, size=(k, 64)).astype(np.float32)
        with torch.no_grad():
            tahmin = model(torch.tensor(x + g)).argmax(1).numpy()
        return np.bincount(tahmin, minlength=10)

    c = int(oy(n0).argmax())
    k = int(oy(n)[c])
    pa = beta.ppf(alfa, k, n - k + 1) if k > 0 else 0.0
    if pa < 0.5:
        return -1, 0.0  # cekimser
    return c, SIGMA * norm.ppf(pa)


```

```python
def main():
    D = veri_hazirla()
    Xe, ye = D["Xte"][:100], D["yte"][:100]
    satirlar = []
    print(
        "A) Rastgele duzgunlestirme (sigma = %.2f, 100 test ornegi)"
        % SIGMA
    )
    r_izg = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    for s in SEEDS:
        m = egit(
            MLP(0.0), D["Xtr"], D["ytr"], seed=s, kayip=gurultu_kayip
        )
        rng = np.random.default_rng(s)
        sonuc = [
            rs_sertifika(m, Xe[i : i + 1], rng=rng)
            for i in range(len(Xe))
        ]
        c = np.array([a for a, _ in sonuc])
        R = np.array([b for _, b in sonuc])
        dogru = c == ye
        cek = []
        for r in r_izg:
            v = float(np.mean(dogru & (R >= r)))
            cek.append(v)
            satirlar.append((s, "rs", "%.2f" % r, "%.4f" % v))
        print(
            "  tohum %d: sertifikali =" % s,
            " ".join("%.2f" % v for v in cek),
            " cekimser = %d" % int((c == -1).sum()),
        )
    print("  r sirasi: " + " ".join("%.1f" % r for r in r_izg))
    print(
        "\nB1) Sifirdan IBP: el ornegi ag (2 girdi, 2 gizli, 2 cikti)"
    )
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]])
    b1 = np.array([0.0, -0.2])
    W2 = np.array([[1.0, 1.0], [-1.0, 0.5]])
    b2 = np.zeros(2)
    el = [(W1, b1), (W2, b2)]
```

```python
    x0 = np.array([[0.6, 0.4]])
    for eps in [0.10, 0.15]:
        lo, hi = ibp_np(el, x0 - eps, x0 + eps)
        marj_lo = lo[0, 0] - hi[0, 1]
        # kaba kuvvet: 401 x 401 izgarada gercek minimum marj
        g = np.linspace(-eps, eps, 401)
        A, B = np.meshgrid(g, g)
        P = np.stack([x0[0, 0] + A.ravel(), x0[0, 1] + B.ravel()], 1)
        h = np.maximum(P @ W1.T + b1, 0)
        z = h @ W2.T + b2
        kaba = (z[:, 0] - z[:, 1]).min()
        print(
            "  eps=%.2f  IBP alt marj=%+.4f  "
              "kaba kuvvet min marj=%+.4f"
            % (eps, marj_lo, kaba)
        )
    print("\nB2) Dogrulama: sinirlar gercek cikislari kapsiyor mu?")
    rng = np.random.default_rng(0)
    base = egit(MLP(0.0), D["Xtr"], D["ytr"], seed=0)
    ag = agirliklar_np(base)
    ihlal, genislik = 0, []
    for i in range(20):
        x = D["Xte"][i : i + 1].astype(np.float64)
        lo, hi = ibp_np(ag, x - 0.02, x + 0.02)
        U = x + rng.uniform(-0.02, 0.02, size=(5000, 64))
        Z = ibp_np(ag, U, U)[0]
        ihlal += int(np.sum((Z < lo - 1e-9) | (Z > hi + 1e-9)))
        genislik.append(float(np.mean(hi - lo)))
    print(
        "  20 ornek x 5000 rastgele nokta: sinir ihlali = %d" % ihlal
    )
    print(
        "  ortalama kutu genisligi (logit): %.3f" % np.mean(genislik)
    )
    Zt = ibp_torch(base, torch.tensor(D["Xte"][:50]), 0.02)
    lo_n, hi_n = ibp_np(
        ag,
        D["Xte"][:50].astype(np.float64) - 0.02,
        D["Xte"][:50].astype(np.float64) + 0.02,
    )
```

```python
    fark = max(
        np.abs(Zt[0].detach().numpy() - lo_n).max(),
        np.abs(Zt[1].detach().numpy() - hi_n).max(),
    )
    print("  torch ve numpy IBP en buyuk fark = %.2e" % fark)
    print(
        "\nB3) IBP egitimi (eps_egitim = %.2f) ve sertifikali "
        "dogruluk" % IBP_EPS
    )
    print(
        "tohum model     temiz "
        + " ".join("c%.3f" % e for e in EPS_IBP)
        + " PGD0.02"
    )
    for s in SEEDS:
        for ad, kay in [("standart", None), ("IBP", ibp_kayip)]:
            if kay is None:
                m = egit(MLP(0.0), D["Xtr"], D["ytr"], seed=s)
            else:
                m = egit(
                    MLP(0.0), D["Xtr"], D["ytr"], seed=s, kayip=kay
                )
            ag = agirliklar_np(m)
            temiz = float(
                np.mean(
                    np.argmax(
                        ibp_np(
                            ag,
                            D["Xte"].astype(np.float64),
                            D["Xte"].astype(np.float64),
                        )[0],
                        1,
                    )
                    == D["yte"]
                )
            )
            cert = []
            for e in EPS_IBP:
                lo, hi = ibp_np(ag, D["Xte"] - e, D["Xte"] + e)
                c = sertifiye(lo, hi, D["yte"])
```

```python
                cert.append(float(c.mean()))
                satirlar.append(
                    (s, ad, "%.3f" % e, "%.4f" % c.mean())
                )
            Xp = pgd(m, D["Xte"], D["yte"], 0.02, adim_say=40)
            pg = float(
                (
                    np.argmax(
                        ibp_np(
                            ag,
                            Xp.astype(np.float64),
                            Xp.astype(np.float64),
                        )[0],
                        1,
                    )
                    == D["yte"]
                ).mean()
            )
            print(
                "%5d %-9s %.3f  " % (s, ad, temiz)
                + "  ".join("%.3f   " % v for v in cert)
                + "%.3f" % pg
            )
    csv_yaz(
        "b78_rs_ibp.csv",
        ["tohum", "yontem", "r_veya_eps", "deger"],
        satirlar,
    )


if __name__ == "__main__":
    main()
```


```term
$ python b78_05_savunma.py
A) Rastgele duzgunlestirme (sigma = 0.25, 100 test ornegi)
  tohum 0: sertifikali = 0.91 0.85 0.77 0.67 0.56 0.36  cekimser = 5
  tohum 1: sertifikali = 0.91 0.88 0.79 0.69 0.55 0.36  cekimser = 4
  tohum 2: sertifikali = 0.89 0.85 0.78 0.69 0.51 0.40  cekimser = 5
  r sirasi: 0.0 0.1 0.2 0.3 0.4 0.5

B1) Sifirdan IBP: el ornegi ag (2 girdi, 2 gizli, 2 cikti)
  eps=0.10  IBP alt marj=+0.0250  kaba kuvvet min marj=+0.2750
  eps=0.15  IBP alt marj=-0.0875  kaba kuvvet min marj=+0.2376

B2) Dogrulama: sinirlar gercek cikislari kapsiyor mu?
  20 ornek x 5000 rastgele nokta: sinir ihlali = 0
  ortalama kutu genisligi (logit): 21.495
  torch ve numpy IBP en buyuk fark = 6.80e-06

B3) IBP egitimi (eps_egitim = 0.03) ve sertifikali dogruluk
tohum model     temiz c0.005 c0.010 c0.020 c0.030 PGD0.02
    0 standart  0.950  0.667     0.136     0.000     0.000   0.919
    0 IBP       0.956  0.944     0.936     0.886     0.825   0.939
    1 standart  0.950  0.675     0.147     0.000     0.000   0.903
    1 IBP       0.953  0.939     0.925     0.889     0.800   0.933
    2 standart  0.950  0.700     0.133     0.000     0.000   0.914
    2 IBP       0.953  0.944     0.936     0.881     0.811   0.942
```


B1 bölümünde el örneğinin iki sayısını (ε = 0,10 ve ε = 0,15) IBP ve kaba kuvvet ızgarasıyla hesapladık. ε = 0,10'da IBP alt sınırı +0,025 verdi ve sertifika yapılabildi; kaba kuvvet ızgarası gerçek minimum marjini +0,275 olarak buldu. ε = 0,15'te IBP marjini −0,0875 verdi, yani sertifika yapılamadı. Kaba kuvvet ise +0,2376 buldu: gerçekte karar sabit. IBP güvenli taraftadır: hesaplanan sınır yanlış bir sertifika vermez; ama gevşektir.

B2 bölümünde sınırların doğruluğunu test ettik. 20 test örneği için her birinde 5000 rastgele nokta üretildi ve hiçbir çıkışın IBP sınırının dışına düşmediği görüldü (ihlal sayısı 0). Torch ile numpy IBP arasındaki en büyük fark 6,8 × 10⁻⁶ oldu. Eğitilmemiş standart modelde ε = 0,02 kutusunun ortalama genişliği 21,5 logit birimi: yani gevşeklik, eğitilmemiş ağlarda çok büyüktür. Bu sayı, IBP'nin neden tek başına yeterli olmadığını ve neden IBP eğitimine ihtiyaç duyulduğunu gösterir.

B3 bölümünde IBP eğitimini (ε_eğitim = 0,03) standart modelle karşılaştırdık. Tablo üç tohumun ortalamasıdır; PGD sütunu ε = 0,02'de ampirik doğruluktur.

| ε | Standart (sertifikalı) | IBP (sertifikalı) |
|---|---|---|
| 0,005 | 0,681 | 0,943 |
| 0,010 | 0,139 | 0,932 |
| 0,020 | 0,000 | 0,885 |
| 0,030 | 0,000 | 0,812 |
| PGD, ε = 0,02 | 0,912 | 0,938 |

Temiz doğrulukta fark yok denecek kadar küçüktür: standart 0,950, IBP 0,954. Ama sertifikalı doğrulukta büyük fark var. Standart modelde ε = 0,02'de hiçbir örnek sertifikalanamadı. Bu, modelin o ε'da gerçekten yanıldığı anlamına gelmez: PGD ölçümü 0,912 doğruluk veriyor. Sertifika bir alt sınır değildir, bir kanıttır; sertifika yoksa "güvensiz" değil, "kanıtlanamadı" demektir. Bu ayrım, güvenlik analizinde en sık yapılan hatalardan biridir.

Tabloda kontrol edilmesi gereken bir şey daha var: sertifikalı doğruluk, aynı ε'daki PGD doğruluğunu hiçbir zaman aşmamalıdır. IBP modeli ε = 0,02'de 0,885 sertifikalı ve 0,938 PGD doğruluğuna sahip; bu tutarlıdır. Eğer sertifika ampirik ölçümü aşsaydı, ya sertifika ya da saldırı hatalıdır.

Şekil 78.7, IBP sınır yayılımının el örneğindeki adımlarını gösteriyor.

![Şekil 78.7: Girdi kutusu katmanlardan geçerken her nöronun aralığı genişliyor. Sertifika, doğru sınıfın alt sınırının rakip sınıfın üst sınırını geçmesiyle verilir.](gorseller/b78_ibp_yayilim.png)

Bölüm 47'de SAT çözücülerin bir sistemin bütün çalışma kombinasyonlarını doğrulamak için nasıl kullanıldığını konuşmuştuk. Sinir ağları için de benzer bir yol vardır: ağı bir SMT ya da karışık tamsayılı programlamaya çevirip ε-topunu tam olarak kontrol etmek. Bu yöntemler kesin cevap verir ama ölçekleri küçüktür; bu bölümde ayrıntıya girmiyoruz (genel bilgi).

Son bir not: kuantizasyon (Bölüm 75) modelin ağırlıklarını ve aktivasyonlarını küçülttüğünde sağlamlık da değişir. Sıkıştırılmış bir model, sıkıştırmadan önce ölçülen sağlamlığı taşımaz; sağlamlık, sıkıştırma sonrasında yeniden ölçülmelidir. Bölüm 72'deki kuantizasyon farkındalıklı eğitim ile dayanıklılığın nasıl birlikte eğitilebileceğini de düşünebilirsiniz.

## 78.8 Açıklanabilirlik

Bölüm 58'de bir doğrusal modelin tahmininin her özniteliğe ağırlık × değer olarak bölündüğünü gördük. Derin bir ağda bu bölünme doğrudan yoktur; katmanlar arasında karışan on binlerce parametre vardır. Açıklanabilirlik (explainability), bu karmaşıklığı bir insanın inceleyebileceği bir özete indirgeme çabasıdır. Bölüm 59'daki permütasyon önemi ise genel bir açıklamadır: bir özniteliğin bütün veri üzerinde ne kadar önemli olduğunu söyler. Burada ise tek bir kararın gerekçesiyle ilgileniyoruz: "bu rakam neden 3 olarak sınıflandırıldı?"

Açıklama yöntemlerini iki eksende düşünmek işe yarar. Birincisi yerel (tek bir girdi için) ya da genel (veri kümesi için). İkincisi modele özgü (gradyanlara erişim gerektirir) ya da modelden bağımsız (yalnızca girdi-çıktı ilişkisi yeterlidir). Bu bölümde dört yöntemi ele alıyoruz.

**Gradyan × girdi (GxI).** Bölüm 55'teki gradyanın bir sonucudur: a_i = x_i · ∂z_c/∂x_i. Sınıf logit'i z_c'nin her pikselin değişimine duyarlılığını, piksel değeriyle çarpar. Hesabı çok ucuzdur. Ama ReLU ağlarında gradyan parçalı sabittir ve doyma bölgelerinde sıfıra yakın olabilir; bu yüzden harita gürültülü çıkar.

**Entegre gradyanlar (IG).** Sundararajan ve arkadaşlarının 2017 önerisine göre (genel bilgi), bir taban girdi x' ile x arasındaki doğru boyunca gradyanların ortalaması alınır: IG_i(x) = (x_i − x'_i) ∫₀¹ ∂z_c(x' + α(x − x'))/∂x_i dα. Bu yöntemin güzel bir özelliği tamlık (completeness) aksiyomudur: bütün öznitelik katkılarının toplamı, çıktının taban ile girdi arasındaki farkına eşittir, Σ IG_i = z_c(x) − z_c(x'). Bu, açıklamanın "kaybolmadığını" garanti eder. Integral sayısal olarak m adımlık bir orta nokta toplamıyla hesaplanır; dolayısıyla tamlık yalnızca yaklaşık sağlanır ve bunu ölçmek gerekir.

**Shapley değerleri.** Oyun teorisindeki Shapley değeri (Shapley, 1953; genel bilgi), bir oyuncunun her koalisyona katkısının ağırlıklı ortalamasıdır: φ_i = Σ_{S ⊆ N, i ∉ S} |S|! (n − |S| − 1)! / n! · [v(S ∪ {i}) − v(S)]. Makine öğreniminde oyuncular öznitelikler, v(S) ise yalnızca S'deki öznitelikleri gerçek değerleriyle, geri kalanları bir arka plan (ortalama) değeriyle tutan modelin çıktısıdır. SHAP (Lundberg ve Lee, 2017; genel bilgi) bu fikri makine öğrenmesi için düzenler. Öznitelik sayısı büyüdükçe tam hesap üstel olarak pahalılaşır; bu yüzden örnekleme yaklaşımları kullanılır.

**Açıklamanın sanity kontrolü.** Bir açıklama yöntemi, modelin öğrendiği bilgiye bağlı değilse bir sanat eserinden farksızdır. Adebayo ve arkadaşları 2018'de (genel bilgi), modelin ağırlıkları rastgeleleştirildiğinde açıklama haritasının değişmesi gerektiğini önerdi. Değişmiyorsa yöntem modelden değil, girdinin kendisinden (kenar algılama gibi) bilgi çıkarıyordur.

Deneyde dört test örneğini (her sınıftan birer tane, test kümesinden) kullandık: indeks 19 (rakam 0), 34 (3), 18 (5) ve 3 (8). Model tohum 0'daki standart modeldir ve dört örneğin tamamı doğru tahmin edildi. Shapley için 8 × 8 görüntünün her satırını bir oyuncu saydık: sekiz oyuncu, 256 koalisyon. Bu küçük sayı tam hesabı mümkün kılar ve örnekleme tahminini tam değerle karşılaştırmamıza izin verir.

```python
# -*- coding: utf-8 -*-
"""Deney 6: aciklama yontemleri: gradyan x girdi, entegre gradyan,
Shapley (tam ve ornekleme), aciklamanin sanity kontrolu."""

import copy
import itertools
import math
import numpy as np
import torch
from scipy.stats import spearmanr
from b78_ortak import SEEDS, veri_hazirla, MLP, egit, csv_yaz


def z_sinif(model, X, c):
    """Tahmin edilen sinifin logiti (torch, gradyan icin)."""
    return model(X)[:, c]


def gradyan(model, x, c):
    xt = torch.tensor(x, dtype=torch.float32, requires_grad=True)
    z = z_sinif(model, xt[None], c).sum()
    (g,) = torch.autograd.grad(z, xt)
    return g.numpy()


def entegre_gradyan(model, x, c, taban, m=50):
    """Orta nokta Riemann toplami; toplam z(x)-z(taban) vermeli."""
    alf = (np.arange(m) + 0.5) / m
    g = np.zeros_like(x)
    for a in alf:
        g += gradyan(model, taban + a * (x - taban), c)
    return (x - taban) * g / m


```

```python
def shapley_tum(model, x, c, arka, satir=8):
    """8 satir oyuncu; v(S) = z_c; S satirlari x, digerleri arka.
    256 koalisyonun hepsi: v[mask] tablosu."""
    n = satir
    kopyalar = []
    for mask in range(2**n):
        xs = arka.copy().reshape(8, 8)
        for i in range(n):
            if mask >> i & 1:
                xs[i] = x.reshape(8, 8)[i]
        kopyalar.append(xs.ravel())
    with torch.no_grad():
        Z = model(torch.tensor(np.array(kopyalar, dtype=np.float32)))
    return Z[:, c].numpy().astype(np.float64)


def shapley_exact(V, n=8):
    phi = np.zeros(n)
    for i in range(n):
        for mask in range(2**n):
            if mask >> i & 1:
                continue
            k = bin(mask).count("1")
            w = math.factorial(k) * math.factorial(n - k - 1)
            w /= math.factorial(n)
            phi[i] += w * (V[mask | (1 << i)] - V[mask])
    return phi


```

```python
def shapley_ornek(V, m, rng, n=8):
    """m rastgele permutasyon; marjinal katkilarin ortalamasi."""
    phi = np.zeros(n)
    for _ in range(m):
        perm = rng.permutation(n)
        mask = 0
        for i in perm:
            yeni = mask | (1 << i)
            phi[i] += V[yeni] - V[mask]
            mask = yeni
    return phi / m


def rastgele_kopya(model, katman, seed=5):
    """Ust katmandan baslayarak 'katman' tane katmani sifirla."""
    m = copy.deepcopy(model)
    torch.manual_seed(seed)
    for L in [m.f1, m.f2, m.cik][3 - katman :]:
        L.reset_parameters()
    m.eval()
    return m


```

```python
def main():
    D = veri_hazirla()
    model = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=0)
    arka = D["Xtr"].mean(0)
    idx = [int(np.where(D["yte"] == c)[0][0]) for c in [0, 3, 5, 8]]
    satirlar = []
    print("1) Ornekler (test): indeks, gercek sinif, tahmin")
    tahmin = {}
    for i in idx:
        x = D["Xte"][i]
        c = int(
            np.argmax(model(torch.tensor(x[None])).detach().numpy())
        )
        tahmin[i] = c
        print("   %4d  gercek=%d  tahmin=%d" % (i, D["yte"][i], c))
    print("\n2) Entegre gradyan tamlik kontrolu (ornek %d)" % idx[0])
    x = D["Xte"][idx[0]].astype(np.float64)
    c = tahmin[idx[0]]
    with torch.no_grad():
        z_x = model(torch.tensor(x[None].astype(np.float32)))[
            0, c
        ].item()
        z_0 = model(torch.zeros(1, 64))[0, c].item()
    print("   z(x) - z(0) = %.5f" % (z_x - z_0))
    for m in [5, 20, 50, 200]:
        ig = entegre_gradyan(
            model,
            x.astype(np.float32),
            c,
            np.zeros(64, np.float32),
            m,
        )
        print(
            "   m=%3d  sum(IG) = %.5f  hata = %.2e"
            % (m, ig.sum(), abs(ig.sum() - (z_x - z_0)))
        )
    print("\n3) Ornekler uzerinde yontemler")
    for i in idx:
        x = D["Xte"][i]
        c = tahmin[i]
```

```python
        gxi = x * gradyan(model, x, c)
        ig = entegre_gradyan(model, x, c, np.zeros(64, np.float32))
        ig5 = entegre_gradyan(
            model, x, c, np.full(64, 0.5, np.float32)
        )
        for ad, v in [
            ("girdi", x),
            ("GxI", gxi),
            ("IG_0", ig),
            ("IG_gri", ig5),
        ]:
            for p, val in enumerate(v):
                satirlar.append((i, D["yte"][i], ad, p, "%.6f" % val))
        print(
            "   ornek %4d: GxI en buyuk pikseller %s"
            % (i, np.argsort(-np.abs(gxi))[:4])
        )
    print("\n4) Shapley: tam hesap (256 koalisyon) ve ornekleme")
    x = D["Xte"][idx[0]]
    c = tahmin[idx[0]]
    V = shapley_tum(model, x, c, arka)
    phi = shapley_exact(V)
    deger = " ".join("%.3f" % v for v in phi)
    print("   phi (satir gruplari):", deger)
    print(
        "   verimlilik: sum(phi) = %.4f, v(N)-v({}) = %.4f"
        % (phi.sum(), V[-1] - V[0])
    )
    print("   m   hata_ort   hata_sd   (5 tohum, ornekleme)")
    sk = []
    for m in [5, 20, 50, 200]:
        hata = []
        for t in range(5):
            ph = shapley_ornek(V, m, np.random.default_rng(t))
            hata.append(np.mean(np.abs(ph - phi)))
        hata = np.array(hata)
        print("  %4d   %.4f    %.4f" % (m, hata.mean(), hata.std()))
        sk.append((m, "%.6f" % hata.mean(), "%.6f" % hata.std()))
    print(
        "\n5) Sanity: rastgele agirliklarla aciklama degisiyor mu?"
```

```python
    )
    print("   katman  Spearman(ort)  sd")
    kayitlar = []
    for katman in [1, 2, 3]:
        rho = []
        m2 = rastgele_kopya(model, katman)
        for i in idx:
            x = D["Xte"][i]
            c = tahmin[i]
            a = x * gradyan(model, x, c)
            b = x * gradyan(m2, x, c)
            rho.append(spearmanr(a, b).correlation)
        rho = np.array(rho)
        print(
            "   %d       %+.3f        %.3f"
            % (katman, rho.mean(), rho.std())
        )
        kayitlar.append(
            (katman, "%.4f" % rho.mean(), "%.4f" % rho.std())
        )
    csv_yaz(
        "b78_aciklama.csv",
        ["ornek", "gercek", "yontem", "piksel", "deger"],
        satirlar,
    )
    csv_yaz("b78_shap.csv", ["m", "hata_ort", "hata_sd"], sk)
    csv_yaz("b78_sanity.csv", ["katman", "spearman", "sd"], kayitlar)


if __name__ == "__main__":
    main()
```


```term
$ python b78_06_aciklama.py
1) Ornekler (test): indeks, gercek sinif, tahmin
     19  gercek=0  tahmin=0
     34  gercek=3  tahmin=3
     18  gercek=5  tahmin=5
      3  gercek=8  tahmin=8

2) Entegre gradyan tamlik kontrolu (ornek 19)
   z(x) - z(0) = 9.62186
   m=  5  sum(IG) = 9.57520  hata = 4.67e-02
   m= 20  sum(IG) = 9.63345  hata = 1.16e-02
   m= 50  sum(IG) = 9.63809  hata = 1.62e-02
   m=200  sum(IG) = 9.62219  hata = 3.31e-04

3) Ornekler uzerinde yontemler
   ornek   19: GxI en buyuk pikseller [21 18 26 10]
   ornek   34: GxI en buyuk pikseller [45 28  4 53]
   ornek   18: GxI en buyuk pikseller [ 4  5 10 11]
   ornek    3: GxI en buyuk pikseller [35 27 58 50]

4) Shapley: tam hesap (256 koalisyon) ve ornekleme
   phi (satir gruplari): 0.337 0.242 1.584 3.700 3.612 1.358 1.255 0.361
   verimlilik: sum(phi) = 12.4496, v(N)-v({}) = 12.4496
   m   hata_ort   hata_sd   (5 tohum, ornekleme)
     5   0.1903    0.0853
    20   0.0868    0.0362
    50   0.0669    0.0263
   200   0.0336    0.0086

5) Sanity: rastgele agirliklarla aciklama degisiyor mu?
   katman  Spearman(ort)  sd
   1       +0.079        0.340
   2       +0.036        0.296
   3       +0.057        0.078
```


İlk bölümde tamlık kontrolü yaptık. Örnek 19 için z(x) − z(0) = 9,62186. Orta nokta toplamıyla hesaplanan IG toplamları ise şöyle: m = 5 için 4,67 × 10⁻², m = 20 için 1,16 × 10⁻², m = 50 için 1,62 × 10⁻² ve m = 200 için 3,31 × 10⁻⁴. Hata m ile genel olarak düşüyor, ama m = 50'de m = 20'den büyük. Bu, orta nokta kuralının hatasının integrali alınan fonksiyonun eğriliğine bağlı olmasından kaynaklanır; hata her m için monoton azalmaz. Ders: tamlık hatası her açıklama için ölçülmeli, yalnızca "teorik olarak doğru" demek yetmez.

Shapley bölümünde tam hesapla (256 koalisyon) ve örnekleme ile karşılaştırma yaptık. Tam hesapta sekiz satır grubunun değerleri [0,337; 0,242; 1,584; 3,700; 3,612; 1,358; 1,255; 0,361]. Toplam 12,4496 ve v(N) − v(∅) de 12,4496: verimlilik özelliği tam olarak sağlandı. En büyük katkı merkezdeki satırlardan geliyor. Rakam 0'ın ortasındaki boşluk bu sonucu akla getirir, ama bu bir yorumdur; yöntem bize nedensellik söylemez.

Örnekleme tahmini (m permütasyon) ile tam değer arasındaki ortalama mutlak hata, beş tohumun ortalamasıyla şöyle: m = 5 için 0,190 ± 0,085; m = 20 için 0,087 ± 0,036; m = 50 için 0,067 ± 0,026; m = 200 için 0,034 ± 0,009. Hata permütasyon sayısıyla azalıyor, ama bu azalma yavaştır: hatayı yarıya indirmek için dört kat daha fazla permütasyon gerekti. Öznitelik sayısı yüzlerce olduğunda bu maliyet kabul edilebilir olmaktan çıkar.

Sanity kontrolü için ağın üst katmanlarından başlayarak ağırlıkları rastgeleleştirdik. Gradyan × girdi haritaları ile rastgele model haritaları arasındaki Spearman korelasyonu şöyle çıktı: çıkış katmanı rastgele ise 0,079 ± 0,340; son iki katman rastgele ise 0,036 ± 0,296; bütün katmanlar rastgele ise 0,057 ± 0,078. Ortalama korelasyon sıfıra çok yakın; yani harita öğrenilmiş modelin bilgisini taşıyor. Ama sapma büyük: tek bir örnekte korelasyon ±0,3 gibi değerlere çıkabiliyor. Bu yüzden sanity kontrolü tek bir görselle değil, birçok örnek üzerinden sayısal olarak yapılmalı.

Şekil 78.8 dört örnekte dört görünümü gösteriyor. Sıfır tabanlı IG, gradyan × girdiye çok benzer. Gri tabanlı IG (0,5 değerli taban) ise belirgin biçimde farklı ve daha gürültülü bir harita veriyor. Yani IG de taban bağımlıdır; "hangi taban?" sorusu açıklamanın bir parçasıdır.

![Şekil 78.8: Dört rakam örneğinde girdi, gradyan × girdi ve iki farklı tabanlı entegre gradyan. Kırmızı pozitif, mavi negatif katkı.](gorseller/b78_ig_izgara.png)

Açıklamalar hakkında son bir uyarı. Bir ısı haritası ikna edici görünebilir, ama bir insanın haritaya bakıp "model doğru düşünüyor" demesi bir kanıt değildir. Açıklama, modelin davranışının bir ölçümüdür; doğru olup olmadığı yine sağlamlık, kalibrasyon ve sanity testleriyle sınanmalıdır. Savunma uygulamalarında, bir kararın gerekçesinin denetlenebilir olması gerektiğinde bu testler zorunludur.

## 78.9 Adalet

Adalet, güvenilir AI'nın en çok tartışılan boyutudur ve burada yalnızca kısa bir çerçeve veriyoruz. Temel soru şudur: bir sistemin hataları farklı gruplar arasında eşit dağılıyor mu? Bölüm 57'deki dilim analizi bu sorunun ilk adımıdır.

Üç ölçüt yaygındır. Demografik eşitlik (demographic parity) pozitif kararların oranının gruplar arasında eşit olmasını ister: P(ŷ = 1 | g = 0) = P(ŷ = 1 | g = 1). Eşit fırsat (equal opportunity) gerçek pozitiflerin yakalanma oranının (TPR) eşit olmasını ister. Eşit yanlış pozitif oranı (FPR) ise yanlış alarmların eşitlenmesini hedefler. Hardt ve arkadaşlarının 2016 çalışması bu eşit fırsat ölçütünü resmileştirdi (genel bilgi).

Bu ölçütler aynı anda her zaman sağlanamaz. Chouldechova'nın 2017'deki sonucu (genel bilgi), grupların temel pozitif oranları farklıysa, grup içinde kalibrasyon ile FPR ve FNR eşitliğinin aynı anda sağlanamayacağını gösterir. Bu bir matematik sonucudur, bir ihmal değildir: adalet bir takas problemidir ve hangi ölçütün hangi zararı azalttığı, uygulamanın etik ve hukuki bağlamına bağlıdır.

Deneyde sentetik bir veri kümesi kullandık. Grup g = 1 oranı yüzde 30; bu grubun öznitelikleri −0,6 kayık ve pozitif sınıfın temel oranı logit olarak −0,8 daha düşük. Sınıflandırıcı bir lojistik regresyon; grup bilgisini girdi olarak almıyor. Yine de öznitelik kayması nedeniyle skorlar gruplara göre farklı dağılıyor. Üç karar kuralı karşılaştırdık: tek bir eşik (0,5), eşit fırsat için grup başına eşik (TPR'yi genel TPR'ye eşitleyen) ve demografik eşitlik için grup başına eşik (kabul oranını eşitleyen).

```python
# -*- coding: utf-8 -*-
"""Deney 7: adalet metrikleri ve esik takasi (sentetik veri)."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from b78_ortak import SEEDS, csv_yaz


def veri_uret(n, rng):
    """Grup g in {0,1}; g=1 grubunun ozellikleri kayik (-0.6) ve
    temel pozitif orani daha dusuk (logit -0.8)."""
    g = (rng.uniform(size=n) < 0.3).astype(int)
    X = rng.normal(size=(n, 4)) + np.where(g[:, None] == 1, -0.6, 0.0)
    w = np.array([1.0, -0.8, 0.5, 0.3])
    logit = X @ w - 0.2 - 0.8 * g
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y, g


def esik_tpr(s, y, hedef):
    """Pozitiflerin yaklasik 'hedef' oranini yakalayan esik."""
    return np.quantile(s[y == 1], 1 - hedef)


def olc(yhat, y, g):
    tpr = [yhat[(g == k) & (y == 1)].mean() for k in (0, 1)]
    fpr = [yhat[(g == k) & (y == 0)].mean() for k in (0, 1)]
    pr = [yhat[g == k].mean() for k in (0, 1)]
    return {
        "dogruluk": (yhat == y).mean(),
        "DP": abs(pr[0] - pr[1]),
        "EO": abs(tpr[0] - tpr[1]),
        "FPR": abs(fpr[0] - fpr[1]),
    }


```

```python
def main():
    sonuc = {}
    for s in SEEDS:
        rng = np.random.default_rng(10 + s)
        X, y, g = veri_uret(6000, rng)
        tr, te = slice(0, 3000), slice(3000, 6000)
        clf = LogisticRegression(max_iter=1000).fit(X[tr], y[tr])
        p = clf.predict_proba(X[te])[:, 1]
        yt, gt = y[te], g[te]
        # 1) tek esik 0.5
        y1 = (p >= 0.5).astype(int)
        # 2) grup-bazli esik: iki grupta da TPR = global TPR (EO)
        tpr_hedef = (y1[yt == 1]).mean()
        y2 = np.zeros_like(y1)
        for k in (0, 1):
            m = gt == k
            e = esik_tpr(p[m], yt[m], tpr_hedef)
            y2[m] = (p[m] >= e).astype(int)
        # 3) grup-bazli esik: iki grupta da kabul orani esit (DP)
        oran = y1.mean()
        y3 = np.zeros_like(y1)
        for k in (0, 1):
            m = gt == k
            e = np.quantile(p[m], 1 - oran)
            y3[m] = (p[m] >= e).astype(int)
        for ad, yh in [
            ("tek esik 0.5", y1),
            ("EO esigi", y2),
            ("DP esigi", y3),
        ]:
            sonuc.setdefault(ad, []).append(olc(yh, yt, gt))
    print(
        "Kural            dogruluk      DP fark     EO fark"
        "     FPR fark"
    )
    satirlar = []
    for ad, lst in sonuc.items():
        v = {k: np.array([d[k] for d in lst]) for k in lst[0]}
        print(
            "%-15s  %.3f+-%.3f  %.3f+-%.3f  %.3f+-%.3f  %.3f+-%.3f"
```

```python
            % (
                ad,
                v["dogruluk"].mean(),
                v["dogruluk"].std(),
                v["DP"].mean(),
                v["DP"].std(),
                v["EO"].mean(),
                v["EO"].std(),
                v["FPR"].mean(),
                v["FPR"].std(),
            )
        )
        satirlar.append(
            (
                ad,
                "%.4f" % v["dogruluk"].mean(),
                "%.4f" % v["DP"].mean(),
                "%.4f" % v["EO"].mean(),
                "%.4f" % v["FPR"].mean(),
            )
        )
    print("\n(3 veri tohumu; test n = 3000 her tohumda)")
    csv_yaz(
        "b78_adalet.csv",
        ["kural", "dogruluk", "dp_fark", "eo_fark", "fpr_fark"],
        satirlar,
    )


if __name__ == "__main__":
    main()
```


```term
$ python b78_07_adalet.py
Kural            dogruluk      DP fark     EO fark     FPR fark
tek esik 0.5     0.744+-0.003  0.169+-0.015  0.080+-0.044  0.062+-0.014
EO esigi         0.737+-0.003  0.111+-0.032  0.001+-0.001  0.043+-0.005
DP esigi         0.721+-0.003  0.000+-0.000  0.117+-0.043  0.090+-0.021

(3 veri tohumu; test n = 3000 her tohumda)
```


| Karar kuralı | Doğruluk | DP farkı | EO farkı | FPR farkı |
|---|---|---|---|---|
| Tek eşik 0,5 | 0,744 ± 0,003 | 0,169 ± 0,015 | 0,080 ± 0,044 | 0,062 ± 0,014 |
| EO eşiği | 0,737 ± 0,003 | 0,111 ± 0,032 | 0,001 ± 0,001 | 0,043 ± 0,005 |
| DP eşiği | 0,721 ± 0,003 | 0,000 ± 0,000 | 0,117 ± 0,043 | 0,090 ± 0,021 |

Tablo takası açıkça gösteriyor. Eşit fırsat eşiği, fırsat farkını 0,080'den 0,001'e indirdi ve doğrulukta yalnızca 0,7 puan kaybettirdi. Demografik eşitlik eşiği kabul oranlarını birebir eşitledi (DP = 0), ama bu sefer gerçek pozitiflerdeki fark 0,117'ye çıktı. Yani bir ölçütü sıfırlamak, diğerini büyütebilir.

Bu takas, seçimi bir mühendislik kararı olmaktan çıkarır. Kaçırılan gerçek bir olayın maliyeti yüksekse (örneğin bir tehdit tespitinde), eşit fırsat daha savunulabilir görünür. Kabul oranlarının grup bazında eşit olması gerekiyorsa (örneğin bir işe alım sürecinde), demografik eşitlik öne çıkar. Her iki durumda da grup başına farklı eşik kullanmak, karar anında grup bilgisine ihtiyaç duyar. Bunun hukuki ve etik sonuçları vardır ve teknik bir ayar gibi sunulmamalıdır (genel bilgi).

Bu deney üç veri tohumuyla ve sentetik bir kümeyle yapıldı; gerçek bir sistemin adalet denetimi yerine geçmez. Ama çerçeve aynıdır: önce ölçütleri ve zararı tanımla, sonra eşikleri bu zarara göre seç, son olarak takasları yazılı olarak kaydet.

## 78.10 Güvenlik tehditleri: veri, model ve LLM

Bölüm 32'de yazılım güvenliğinin temel ilkelerini (en az yetki, girdi doğrulama, savunmalı tasarım) gördük. ML sistemleri bu ilkelere ek olarak yeni bir yüzey açar: eğitim verisi, model dosyası ve model çıktısının kendisi. Bu bölümde tehditleri kavramsal olarak tanımlıyor, savunmaların nasıl düşünüldüğünü anlatıyoruz. Bu konularda uygulamalı bir tarif yoktur.

**Veri zehirlenmesi (data poisoning).** Saldırgan eğitim verisine kötü niyetli örnekler ekler. Hedefli zehirlemede amaç, belirli bir girdi için yanlış çıktı üretmektir; genel zehirlemede ise modelin doğruluğunu bozmaktır. Savunma veri kökeninden (data lineage) başlar: her örneğin nereden geldiği, kim tarafından değiştirildiği ve hangi sürümde kullanıldığı izlenmelidir. Anomali tespiti (Bölüm 61) ve veri sürümlemesi (Bölüm 77) bu savunmanın araçlarıdır. Eğitim verisini tek bir kaynağa bağlamak, risk yüzeyini daraltır.

**Arka kapı (backdoor).** Eğitimde küçük bir tetikleyici (örneğin görüntünün köşesindeki sabit bir desen) ile model, tetikleyici göründüğünde belirli bir sınıfa yönelecek şekilde öğretilir. Temiz test verisinde model normal görünür; bu yüzden standart doğruluk ölçümü bu tehdidi yakalamaz. Savunma, eğitim verisinin ve model davranışının tetikleyici aramasını, bağımsız bir test kümesini ve modelin imzasını (hash) içerir. Bu bölümde bir arka kapı kurmuyoruz; tehdidin varlığını bilmek, tespit testi tasarlamak için yeterlidir.

**Model çıkarma (model extraction).** Kara kutu erişimi olan bir saldırgan, çok sayıda sorgu ile modelin davranışını taklit eden bir model eğitebilir. Bu hem fikri mülkiyet kaybıdır hem de başka bir saldırının (çekişmeli örnek üretimi gibi) kapısını açar. Savunma, sorgu hızını sınırlamayı, yalnızca etiket döndürmeyi ve olağandışı sorgu örüntülerini izlemeyi içerir.

**Üyelik çıkarımı (membership inference).** Bir kaydın eğitim kümesinde olup olmadığını tahmin etmek. Shokri ve arkadaşlarının 2017 çalışması bu tehdidi gösterdi (genel bilgi). Aşırı öğrenmiş modeller (Bölüm 64'teki düzenlileştirme ve erken durdurma konusu) bu tehdide daha açıktır. Savunmalar düzenlileştirme ve diferansiyel gizlilik içerir. DP-SGD (Abadi ve arkadaşları, 2016; genel bilgi), gradyanları kırpıp gürültü ekleyerek bir kaydın modele etkisini sınırlar; bunun bedeli doğrulukta bir düşüştür ve gizlilik bütçesiyle ölçülür.

**Prompt enjeksiyonu.** Dil modelleri için tehdit, girdinin içinde gizlenmiş talimatlardır: sistem talimatı ile kullanıcının verisi aynı kanaldan geldiğinde model veriyi talimat sanabilir. Bu tehdit ve savunmaları (talimat ile veriyi ayırmak, araç çağrılarını kısıtlamak, çıktıyı şemaya bağlamak) Bölüm 71'de ayrıntılı olarak ele alındı.

**Model sızıntısı.** Model dosyası kendisi hassas bilgi taşıyabilir: eğitim verisinden parçalar, ticari bir sır ya da bir kişiye ait bilgi. Model dağıtımı, bir veri sızıntısı gibi yönetilmelidir: erişim kontrolü, dosya bütünlüğü ve sürümlü dağıtım.

Bu tehditlerin ortak dersi şudur: ML sistemi, verisi, modeli ve çıktısıyla birlikte bir güvenlik sınırı oluşturur ve her sınır izlenmelidir. Bölüm 77'de MLOps tarafındaki izleme ve denetim izi bu sınırların uygulamadaki karşılığıdır.

## 78.11 Savunma sanayiinde doğrulama ve sertifikasyon

Savunma ve havacılık yazılımında bir sistemin "çalıştığını" söylemek için bir kanıt paketi gerekir. Bu paketin kalbinde standartlar vardır. DO-178C havacılık yazılımı için, IEC 61508 ise işlevsel güvenlik için kullanılan genel standartlardır (genel bilgi). Bu standartlar deterministik yazılım varsayar: aynı girdi aynı çıktıyı verir; gereksinimden koda ve testlere uzanan izlenebilirlik kurulur; yapısal kapsama (dallar, koşullar) ölçülür.

Makine öğrenmesi bileşeni bu varsayımlarla çatışır. Parametreleri yazılmamış, veriden öğrenilmiştir; kendi "kodu" bir ağırlık tablosudur ve davranışı eğitim verisinin dağılımına bağlıdır. Aynı ağırlıklarla farklı bir veri kümesinde farklı davranabilir. Bu yüzden ML bileşenine doğrudan kod standardı uygulamak anlamsızdır; önce sorunun yeniden tanımlanması gerekir.

Havacılık otoriteleri, ML için sertifikasyon yol haritaları yayımladı (genel bilgi; madde numaralarına bu bölümde girilmiyor). Bu yol haritalarında tekrar eden birkaç fikir vardır. İlki işlemsel tasarım alanı (operational design domain, ODD): sistemin hangi koşullarda (hava, aydınlatma, irtifa, hedef türü) çalışmak üzere tasarlandığının açık tanımı. ODD dışındaki girdiler için sistemin davranışı da tanımlanmalıdır. İkincisi veri gereksinimleri: eğitim ve test verisinin ODD'yi temsil ettiğinin kanıtı. Üçüncüsü bağımsız doğrulama ve son olarak çalışma zamanı izleme.

Gereksinim tabanlı test ML'de de işe yarar, ama gereksinimler ölçülebilir olmalıdır. "Sistem iyi tanır" bir gereksinim değildir. "ODD içindeki rakam görüntülerinde, bozulma düzeyi σ ≤ 0,2 iken doğru tanıma oranı en az yüzde 95" ölçülebilir bir gereksinimdir. Test kümesinin dağılımı bu gereksinimlerin ODD'sini kapsamalıdır; aksi halde test geçer ama sistem kullanımda çöker.

Kapsama ölçütleri de bir tuzaktır. Nöron kapsamı gibi ölçütler, bir test kümesinin ağın nöronlarını ne kadar "uyardığını" sayar. Bu sayı yüksekse test kümesinin iyi olduğu anlamına gelmez: kapsama, karar sınırını ya da ODD'yi temsil etmez. Bu tür ölçütler bir ipucu olabilir, bir kanıt değil (genel bilgi).

Sonuç olarak güvenlik kritik bir ML bileşeni, tek başına sertifikalanmaz; sistem mimarisi içinde sınırlandırılır. Bölüm 74'teki güvenlik kalkanı (safety shield) fikri burada geçerlidir: öğrenen bileşen bir öneri üretir, bağımsız ve deterministik bir katman bu öneriyi denetler ve gerekirse geçersiz kılar. Bölüm 75'te edge'e taşınan modeller de bu güvence paketine yeniden girmelidir; kuantize edilmiş model, sertifikası yapılmış modelin kendisi değildir.

### Çalışma zamanı güvence mimarisi

Bu bölümde tasarladığımız mimari şu fikre dayanır: model her girdide bir karar önerir, ama karar yalnızca üç bağımsız kapıdan geçerse kabul edilir. Kapılar, farklı hata modlarını yakalamak için seçilmiştir. OOD kapısı, öznitelik uzayında eğitim verisinden uzak girdileri (ODD dışı) yakalar. Belirsizlik kapısı, topluluk üyelerinin birbirinden ayrıldığı (epistemik belirsizlik yüksek) girdileri yakalar. Conformal kapısı, kalibre edilmiş bir kümenin tek etiketten oluşup oluşmadığını denetler; küme boşsa ya da birden fazla etiket içeriyorsa model emin değildir.

Kapılardan biri bile başarısız olursa karar reddedilir ve güvenli geri dönüş (fallback) devreye girer. Bir İHA'da bu, sınıflandırma kararını askıya alıp hedef takibini sürdürmek ve operatöre bildirmek olabilir. Geri dönüşün ne olacağı uygulamaya bağlıdır; ama tasarımda önceden yazılmalıdır, çalışma anında düşünülmemelidir.

Mimarinin tasarım kararlarını açıkça yazalım. Eşikler yalnızca ID doğrulama kümesinden seçildi: OOD eşiği ID skorlarının yüzde 5'i, belirsizlik eşiği yüzde 95'i olacak şekilde. Böylece eşiğin seçiminde dağılım dışı veri kullanılmaz. Conformal kapısı α = 0,10 ile kalibrasyon kümesinden kuruldu. OOD dedektörü olarak enerji yerine Mahalanobis seçildi, çünkü Deney 1'de AUROC'u 0,982'ye karşı enerjinin 0,696 olduğu görüldü.

Şekil 78.9 mimariyi gösteriyor.

![Şekil 78.9: Hedef sınıflandırıcının kararı üç bağımsız kapıdan geçer; herhangi bir kapı başarısız olursa karar reddedilir ve güvenli geri dönüş devreye girer. Her karar denetim izine yazılır.](gorseller/b78_calisma_zamani.png)

### İHA hedef sınıflandırıcısı için sentetik doğrulama

Gerçek bir İHA sistemi kurmadık; ama mimariyi bir sentetik akışla sınadık. Hedef sınıflandırıcı, 5 üyeli topluluktur (rakam tanıma, üç tohum). Test akışı 1080 girdiden oluşur: 360 temiz test örneği (ID), 360 bozulmuş örnek (σ = 0,35 gürültü; Bölüm 66'daki bozulma sağlamlığı fikri) ve 360 OOD girdi (gürültü ve leke karışımı). Bozulmuş örnekler "ODD içinde ama kötü koşullarda" girdilere karşılık gelir; OOD girdiler ise ODD dışıdır.

Ölçülen her politika için dört sayı alıyoruz: ID kabul oranı, bozulmuş girdi kabul oranı, OOD kabul oranı ve tehlikeli kabul oranı. Tehlikeli kabul, bir girdinin yanlış sınıfla kabul edilmesi ya da bir OOD girdinin kabul edilmesidir. Kabul edilen girdilerdeki hata, tehlikeli kabulün kabul oranına bölümüdür.

```python
# -*- coding: utf-8 -*-
"""Deney 8: calisma zamani guvence katmani (OOD + belirsizlik +
conformal + reddetme/geri donus) ile sentetik hedef akisi testi."""

import numpy as np
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    ood_uret,
    softmax_np,
    logit_np,
    feat_np,
    topluluk_egit,
    csv_yaz,
)
from b78_01_ood import mahalanobis_fit, mahalanobis_skor
from b78_03_conformal import konformal_esik

ALFA = 0.10
BOZULMA_SIGMA = 0.35


def H(q):
    return -np.sum(q * np.log(q + 1e-12), axis=-1)


def olcum(models, X, mu, prec):
    """Mahalanobis (ilk uye, ozellik uzayi), ortalama olasilik ve
    epistemik belirsizlik (karsilikli bilgi, MI)."""
    P = np.stack([softmax_np(logit_np(m, X)) for m in models])
    ort = P.mean(0)
    mi = H(ort) - H(P).mean(0)
    mah = mahalanobis_skor(feat_np(models[0], X), mu, prec)
    return ort, mah, mi


```

```python
def main():
    D = veri_hazirla()
    gur, lek = ood_uret(len(D["Xte"]))
    satirlar = []
    print(
        "tohum politika        ID    bozuk   OOD    tehlikeli  hata"
    )
    for s in SEEDS:
        ens = topluluk_egit(D, s)
        mu, prec = mahalanobis_fit(
            feat_np(ens[0], D["Xtr"]), D["ytr"]
        )
        rng = np.random.default_rng(50 + s)
        Xb = np.clip(
            D["Xte"] + rng.normal(0, BOZULMA_SIGMA, D["Xte"].shape),
            0,
            1,
        )
        Xo = np.r_[gur[:180], lek[:180]]
        X = np.r_[D["Xte"], Xb, Xo].astype(np.float32)
        tur = np.r_[
            np.zeros(len(D["Xte"])),
            np.ones(len(Xb)),
            2 * np.ones(len(Xo)),
        ]
        y = np.r_[D["yte"], D["yte"], -np.ones(len(Xo), int)]
        # esikler yalnizca dogrulama (ID) ve kalibrasyon kumesinden
        Pva, Dva, Mva = olcum(ens, D["Xva"], mu, prec)
        Pca, _, _ = olcum(ens, D["Xca"], mu, prec)
        e_esik = np.percentile(Dva, 5)
        m_esik = np.percentile(Mva, 95)
        q = konformal_esik(Pca, D["yca"], ALFA)
        P, D2, M = olcum(ens, X, mu, prec)
        kume = (1.0 - P) <= q
        boy = kume.sum(1)
        hata = (P.argmax(1) != y) & (tur < 2)
        kural = {
            "koruma yok": np.ones(len(X), bool),
            "OOD": D2 >= e_esik,
            "OOD+MI": (D2 >= e_esik) & (M <= m_esik),
```

```python
            "OOD+MI+konf.": (D2 >= e_esik)
            & (M <= m_esik)
            & (boy == 1),
        }
        for ad, kab in kural.items():
            k_id = kab[tur == 0].mean()
            k_bz = kab[tur == 1].mean()
            k_oo = kab[tur == 2].mean()
            # tehlikeli kabul: yanlis sinif kabulu veya OOD kabulu
            tehlikeli = np.mean(kab & (hata | (tur == 2)))
            kabul_hata = tehlikeli / max(kab.mean(), 1e-12)
            satirlar.append(
                (
                    s,
                    ad,
                    "%.4f" % k_id,
                    "%.4f" % k_bz,
                    "%.4f" % k_oo,
                    "%.4f" % tehlikeli,
                    "%.4f" % kabul_hata,
                )
            )
            print(
                "%5d %-13s %.3f    %.3f       %.3f     %.3f"
                "     %.3f"
                % (s, ad, k_id, k_bz, k_oo, tehlikeli, kabul_hata)
            )
    csv_yaz(
        "b78_iha.csv",
        [
            "tohum",
            "politika",
            "kabul_id",
            "kabul_bozuk",
            "kabul_ood",
            "tehlikeli",
            "kabul_hata",
        ],
        satirlar,
    )
```

```python
if __name__ == "__main__":
    main()
```


```term
$ python b78_08_iha.py
tohum politika        ID    bozuk   OOD    tehlikeli  hata
    0 koruma yok    1.000    1.000       1.000     0.429     0.429
    0 OOD           0.975    0.683       0.114     0.104     0.176
    0 OOD+MI        0.922    0.392       0.069     0.037     0.080
    0 OOD+MI+konf.  0.858    0.372       0.069     0.030     0.068
    1 koruma yok    1.000    1.000       1.000     0.431     0.431
    1 OOD           0.953    0.600       0.058     0.070     0.131
    1 OOD+MI        0.914    0.439       0.044     0.039     0.083
    1 OOD+MI+konf.  0.856    0.378       0.042     0.024     0.057
    2 koruma yok    1.000    1.000       1.000     0.435     0.435
    2 OOD           0.950    0.650       0.144     0.104     0.178
    2 OOD+MI        0.928    0.483       0.050     0.044     0.089
    2 OOD+MI+konf.  0.844    0.408       0.050     0.026     0.060
```


Üç tohumun ortalamasını dört politika için tabloya koyduk.

| Politika | Kabul (ID) | Kabul (bozulmuş) | Kabul (OOD) | Tehlikeli kabul | Kabul edilenlerde hata |
|---|---|---|---|---|---|
| Koruma yok | 1,000 | 1,000 | 1,000 | 0,432 | 0,432 |
| OOD (Mahalanobis) | 0,959 | 0,644 | 0,106 | 0,093 | 0,162 |
| OOD + belirsizlik | 0,921 | 0,438 | 0,055 | 0,040 | 0,084 |
| OOD + belirsizlik + conformal | 0,853 | 0,386 | 0,054 | 0,027 | 0,062 |

Koruma yok politikasında her girdi kabul edildi ve akışın yüzde 43'ü tehlikeli bir karar oldu. Üç kapılı sistemde tehlikeli kabul yüzde 2,7'ye indi; kabul edilen kararların hata oranı yüzde 43'ten yüzde 6'ya düştü. Bu, sahte bir iyileşme değil: üç tohumda tehlikeli kabul 0,027 ± 0,002 bandında kaldı.

Bedeli de tabloda: ID kabulü yüzde 100'den yüzde 85'e düştü. Yani gerçek bir hedefin yaklaşık yüzde 15'i, sistem güvensiz diye reddedildi. Bu bir takas: güvenlik kapısı sıkılaştıkça kullanılabilirlik düşer. Bu takas bir mühendislik ve operasyon kararıdır; yalnızca teknik bir sayı değildir.

Bir gözlem daha: bozulmuş girdilerin kabul oranı yüzde 64'ten yüzde 39'a düştü. Bu, sistemin kötü koşullarda daha temkinli davrandığını gösterir. Ama bozulmuş girdilerin bir kısmı yine kabul edildi ve yanlış sınıflandırıldı. Hiçbir kapı tek başına yeterli değil; kapıların birlikte çalışması, her birinin tek başına yakalayamadığı hataları yakalamasıyla anlam kazanır.

Bu deneyin sınırlarını belirtelim. Sentetik veri, rakam tanıma ve kitabın kendi bozulma ve OOD üreticileri kullanıldı. Conformal garanti değişim varsayımına dayanır; OOD girdiler bu varsayımı bozar, bu yüzden conformal kapısı OOD'a karşı tek başına koruma değildir. Gerçek bir sistemde ODD'nin tanımı, veri toplama ve saha testi bu tablonun yerini alır.

## 78.12 Bölüm sonunda bir kontrol listesi

Bir ML sistemini savunma ya da güvenlik kritik bir ortamda kullanmadan önce, en azından şu soruların cevabı yazılı olmalıdır: ODD nedir ve ODD dışı girdi ne yapar? Eğitim ve test verisinin ODD'yi temsil ettiğinin kanıtı nedir? Kalibrasyon ve belirsizlik ölçümleri hangi veride yapıldı? OOD eşikleri nasıl seçildi ve dağılım dışı veri eşik seçiminde kullanıldı mı? Sağlamlık hangi saldırılarla (naif kayıp dışında) ölçüldü? Reddedilen kararın geri dönüşü nedir ve kim bilgilendirilir? Her karar hangi sürüm, hangi eşik ve hangi skorla verildi, bu kayıt tutuluyor mu?

Bu sorular cevapsız kalıyorsa sistem henüz kullanıma hazır değildir. Bölüm 77'de model kartlarının bu soruların bir kısmını nasıl yapılandırdığını göreceğiz.

## Çözümlü Örnekler

### Örnek 1 (★): Doğrusal sınıflandırıcıda L∞ ε-topunda en kötü marj

Doğrusal bir sınıflandırıcı f(x) = w·x + b ile tanımlansın. w = (3, −2), b = 1. Bir girdi x = (0,5; 0,2) ve f(x) > 0 ise sınıf pozitif. Bu girdinin her bileşeni en fazla ε kadar değişebiliyorsa (L∞ topu), kararın değişmediği en büyük ε nedir?

**Adım 1 — Anla.** Marj f(x)'tir. En kötü durum, ε-topunun içinde f(x + δ) değerini en küçük yapan δ'dır. Kararın değişmediği en büyük ε'yu bulacağız.

**Adım 2 — Örnekle.** f(x) = 3 · 0,5 − 2 · 0,2 + 1 = 2,1. ε = 0,3 için bir köşe deneyelim: δ = (0,3; −0,3). Bu noktada f = 3 · 0,8 − 2 · (−0,1) + 1 = 3,6, yani marj artıyor. Ters köşe δ = (−0,3; 0,3) ise f = 3 · 0,2 − 2 · 0,5 + 1 = 0,6: marj azaldı. Demek ki en kötü köşe ters yöndedir.

**Adım 3 — Kaba çöz.** En kötü yön, gradyanın tersi yönüdür: ∇f = (3, −2) olduğundan δ = −ε · sign(w) = (−ε, +ε). Bu, bir köşedir. Bu noktada f = 2,1 − 3ε − 2ε = 2,1 − 5ε.

**Adım 4 — Örüntü.** Doğrusal bir fonksiyonun ε-topundaki minimumu, her bileşen için |w_i| · ε toplamı kadar düşer: f_min = f(x) − ε · ‖w‖₁. Burada ‖w‖₁ = |3| + |−2| = 5. Kararın değişeceği ε*, f(x) = 5ε* eşitliğinden: ε* = 2,1 / 5 = 0,42.

**Adım 5 — İyileştir.** Bu sonuç Bölüm 48'deki normlarla Bölüm 55'teki gradyanın birleşimidir: marjı gradyanın ‖·‖₁ normuna bölmek, L∞ sağlamlık yarıçapını verir. Doğrusal modelde FGSM'in bulduğu yön tam olarak en kötü yöndür (genel bilgi). Derin ağlarda bu yalnızca bir yaklaşımdır; doğrusal örnekte ise kesindir.

**Adım 6 — Doğrula.** Aşağıdaki iz tablosu her ε için en kötü noktayı ve formülle hesaplanan değeri karşılaştırır.

| ε | δ = −ε·sign(w) | x + δ | f(x + δ) | 2,1 − 5ε | Karar |
|---|---|---|---|---|---|
| 0,10 | (−0,10; 0,10) | (0,40; 0,30) | 1,6 | 1,6 | değişmez |
| 0,30 | (−0,30; 0,30) | (0,20; 0,50) | 0,6 | 0,6 | değişmez |
| 0,42 | (−0,42; 0,42) | (0,08; 0,62) | 0,0 | 0,0 | sınır |
| 0,50 | (−0,50; 0,50) | (0,00; 0,70) | −0,4 | −0,4 | değişir |

Tablodaki sütunlar birbirini doğruluyor. ε = 0,42'de marj tam sıfırdır: karar sınırı bu noktadan geçer ve ε bu değeri aştığında sınıf değişir.

**Bunu AI'sız yazabilir misin?** w = (2, −1), b = 1,5, x = (1; 0,5) için f(x) ve ‖w‖₁ değerlerini hesapla. ε* kaç? ε = 0,4 ve ε = 1,2 için en kötü marjı ve kararın değişip değişmediğini yaz.

### Örnek 2 (★★): Bölünmüş conformal eşiğinin ve tahmin kümesinin elle hesabı

Bir sınıflandırıcının kalibrasyon kümesinde n = 9 örnek var. Her örnek için uyumsuzluk skoru s = 1 − p(gerçek sınıf | x) hesaplanmış: 0,05; 0,12; 0,31; 0,22; 0,08; 0,40; 0,15; 0,27; 0,19. Hata düzeyi α = 0,20. Eşik q nedir? Test girdileri p = (0,75; 0,15; 0,06; 0,04) ve p = (0,55; 0,40; 0,03; 0,02) için tahmin kümeleri nelerdir?

**Adım 1 — Anla.** Hedef: gerçek etiketi yüzde 80 olasılıkla içeren küme. Eşik q, kalibrasyon skorlarının belirli bir sırasıdır. Test girdisi için küme, 1 − p_k ≤ q olan sınıflardan oluşur.

**Adım 2 — Örnekle.** Küçük bir durum: n = 3 ve α = 0,5. Skorlar 0,1; 0,2; 0,3 olsun. k = ⌈(3 + 1) · 0,5⌉ = 2. Eşik ikinci en küçük skor olan 0,2'dir. Üçüncü skor (0,3) bu eşiğin dışında kalır. Bu tam olarak "k-inci en küçük değer" kuralıdır.

**Adım 3 — Kaba çöz.** Sıralı skorlar: 0,05; 0,08; 0,12; 0,15; 0,19; 0,22; 0,27; 0,31; 0,40. k = ⌈(9 + 1) · 0,8⌉ = 8. Sekizinci değer 0,31'dir: q = 0,31.

**Adım 4 — Örüntü.** Genel kural: sıralı skorların k-ıncı değeri, k = ⌈(n + 1)(1 − α)⌉. Bu, sonlu örnek düzeltmesidir: n + 1 terimi, kalibrasyon kümesi kendi test noktasını da içerirmiş gibi davranır. Eğer k > n ise q = ∞ ve küme tüm sınıfları içerir.

**Adım 5 — İyileştir.** α = 0,05 denersek k = ⌈10 · 0,95⌉ = ⌈9,5⌉ = 10 > 9 olur ve q = ∞ çıkar: her küme tüm dört sınıfı içerir. Bu, kapsamayı garanti eder ama işe yaramaz bir küme verir. Genel olarak k ≤ n koşulu n ≥ 1/α − 1 demektir: α = 0,05 için en az n = 19 gerekir. Küçük kalibrasyon kümesi, sıkı hata düzeyinde bilgisiz bir sonuç verir.

**Adım 6 — Doğrula.** İz tablosu iki test girdisini gösteriyor.

| Girdi | p | 1 − p | 1 − p ≤ 0,31 olan sınıflar | Küme | Yorum |
|---|---|---|---|---|---|
| A | (0,75; 0,15; 0,06; 0,04) | (0,25; 0,85; 0,94; 0,96) | sınıf 0 | {0} | tekil, karar verilebilir |
| B | (0,55; 0,40; 0,03; 0,02) | (0,45; 0,60; 0,97; 0,98) | yok | {} | boş, reddet |

Girdi B'nin kümesi boştur: model hiçbir sınıfa yeterince güvenmiyor. Bu bir hata değildir; güvenli bir "emin değilim" cevabıdır ve reddedilip operatöre devredilmelidir (78.5). Eşik 0,31 olduğu için bir sınıfın kümeye girmesi p ≥ 0,69 gerektirir. Bu yüzden olasılığı 0,55 olan sınıf 0 bile dışarıda kaldı.

**Bunu AI'sız yazabilir misin?** Aynı kalibrasyon skorlarıyla α = 0,10 için k ve q değerini bul. Sonra p = (0,50; 0,45; 0,03; 0,02) için kümeyi yaz. Küme iki elemanlı olabilir mi? Bunun için hangi iki sınıfın 1 − p ≤ q koşulunu sağlaması gerekir?

### Örnek 3 (★★): İki katmanlı ReLU ağında IBP ile çıktı sınırlarının elle yayılımı

Girdi x = (x₁, x₂) iki boyutlu, gizli katman iki ReLU nöronlu ve çıktı iki logit. Ağırlıklar: W₁ = [[1, −1], [0,5, 1]], b₁ = (0, −0,2), W₂ = [[1, 1], [−1, 0,5]], b₂ = (0, 0). Nominal girdi x₀ = (0,6; 0,4) ve sınıf 0. Sertifika: ε-kutusunun her noktasında z₀ > z₁ olacak mı?

**Adım 1 — Anla.** Kutu [x₀ − ε, x₀ + ε] (bileşen bazında). Sertifika, IBP ile hesaplanan z₀ alt sınırı z₁ üst sınırından büyükse verilir. Bu yalnızca bir kanıt yöntemidir; gerçek minimum daha iyi olabilir.

**Adım 2 — Örnekle.** Nominal değerler: h₁ = x₁ − x₂ = 0,2; h₂ = 0,5 · 0,6 + 0,4 − 0,2 = 0,5. ReLU değişmez. z₀ = h₁ + h₂ = 0,7; z₁ = −h₁ + 0,5 h₂ = 0,05. Sınıf 0 doğru.

**Adım 3 — Kaba çöz.** ε = 0,10 için kutu x₁ ∈ [0,5; 0,7], x₂ ∈ [0,3; 0,5]. Her katmanda orta ve yarıçap hesaplanır; yarıçap |W| ile çarpılır. Aşağıdaki tablo, IBP'nin her adımını gösteriyor.

| Adım | İfade | Orta | Yarıçap | Aralık |
|---|---|---|---|---|
| Girdi | x₁, x₂ | (0,6; 0,4) | (0,1; 0,1) | kutu |
| h₁ | x₁ − x₂ | 0,2 | 0,1 + 0,1 = 0,2 | [0; 0,4] |
| h₂ | 0,5x₁ + x₂ − 0,2 | 0,5 | 0,05 + 0,1 = 0,15 | [0,35; 0,65] |
| ReLU | max(·, 0) | — | — | h₁: [0; 0,4], h₂: [0,35; 0,65] |
| z₀ | h₁ + h₂ | 0,7 | 0,2 + 0,15 = 0,35 | [0,35; 1,05] |
| z₁ | −h₁ + 0,5h₂ | 0,05 | 0,2 + 0,075 = 0,275 | [−0,225; 0,325] |

**Adım 4 — Örüntü.** Sertifika koşulu: alt(z₀) = 0,35 > üst(z₁) = 0,325. Fark 0,025 pozitif; ε = 0,10 için sertifika verildi. Yayılım her katmanda yarıçapı bir miktar büyütür. Bu büyütme, iki nöronun girdiye aynı bileşenler üzerinden bağlı olduğu bilgisini yok sayar (her katman bağımsız varsayılır). Bu yüzden sınır gevşektir.

**Adım 5 — İyileştir.** ε = 0,15 için aynı hesap: kutu x₁ ∈ [0,45; 0,75], x₂ ∈ [0,25; 0,55]. h₁ ∈ [−0,1; 0,5] → ReLU sonrası [0; 0,5]; h₂ ∈ [0,275; 0,725]. z₀ ∈ [0,275; 1,225], z₁ ∈ [−0,3625; 0,3625]. Sertifika koşulu 0,275 − 0,3625 = −0,0875 < 0: IBP başarısız. Oysa kesin hesap farklıdır: z₀ − z₁ = 2 · relu(h₁) + 0,5 · relu(h₂). Bu fonksiyonun kutudaki minimumu x = (0,45; 0,45) noktasındadır. Orada h₁ = 0 (relu = 0) ve h₂ = 0,475. Marj 0,5 · 0,475 = 0,2375 > 0: sertifika aslında mümkündür.

**Adım 6 — Doğrula.** Aşağıdaki tablo IBP sınırını kaba kuvvet ızgarasıyla (401 × 401) karşılaştırır. Bu, Deney 5'in B1 bölümünün yaptığı kontroldür.

| ε | IBP alt marjı | Kaba kuvvet minimumu | Sertifika (IBP) | Gerçek durum |
|---|---|---|---|---|
| 0,10 | +0,0250 | +0,2750 | var | sertifikalı |
| 0,15 | −0,0875 | +0,2376 | yok | sertifikalı (IBP gevşek) |

IBP hiçbir zaman yanlış bir sertifika vermez; ama yanlış bir "sertifika yok" da verebilir. Burada da öyle oldu. Gerçek minimum (0,45; 0,45) noktasında olduğundan, tek bir gizli nöron üzerinden düşünen bir yöntem onu bulamaz. Bu, sertifikasyon yöntemleri arasındaki takasın somut bir örneğidir: hız ile sıkılık.

**Bunu AI'sız yazabilir misin?** Aynı ağda x₀ = (0,6; 0,4) ve ε = 0,12 için IBP alt marjını ve kaba kuvvet minimumunu tahmin et. İkisini de hesapla ve hangisinin daha büyük olduğunu söyle.

### Örnek 4 (★★★): İHA sınıflandırıcısı için çalışma zamanı güvence mimarisi

Bir İHA görüntü sınıflandırıcısı, hedefleri on sınıfa ayırıyor (burada rakam tanıma ile sadeleştirildi). Gereksinimler: (a) tehlikeli kabul oranı (yanlış sınıf ya da ODD dışı girdi kabulü) en fazla yüzde 3 olacak; (b) ODD içindeki gerçek hedeflerin en az yüzde 80'i kabul edilecek. Mimariyi tasarla, eşikleri seç ve sentetik akışta doğrula.

**Adım 1 — Anla.** İki gereksinim birbiriyle çelişir: (a) reddi artırır, (b) kabulü azaltır. Sistemin ne kadar seçici olacağı, tehlikeli kabulün bir sonucudur; bu takasın sınırı açıkça yazılmalıdır.

**Adım 2 — Örnekle.** Üç tipik girdi düşün: (i) temiz bir "7"; (ii) gürültüye boğulmuş bir "7" (σ = 0,35); (iii) bir OOD lekesi. Tek bir model olasılık eşiği (örneğin en büyük olasılık ≥ 0,9) bu üç girdinin hepsinde yüksek güven verebilir mi? Deney 1'de MSP'nin AUROC'u yalnızca 0,795 idi, yani evet: softmax OOD'da da yüksek güven verir.

**Adım 3 — Kaba çöz.** En basit kapı en büyük olasılık eşiğidir. Bu, (iii) durumunu kaçırır ve gereksinim (a)'yı karşılamaz. İkinci kaba çözüm, bir tek kapı olarak Mahalanobis uzaklığı olabilir: bu, (iii)'ü yakalar ama (ii)'yi, bozulmuş ama ODD içinde olan girdiyi, reddedebilir. Gereksinim (b) bu durumda zarar görür.

**Adım 4 — Örüntü.** Farklı hata modları farklı kapılarla yakalanır. OOD kapısı (ODD dışı), belirsizlik kapısı (topluluk üyeleri ayrışıyor) ve conformal kapısı (küme tekil değil) birbirinden bağımsız üç kanıttır. Üçü AND ile birleşirse kabul seçici olur. Bu, her kapının kabul oranını çarpmak anlamına gelmez, çünkü kapılar birbirini kısmen tekrar eder; ama tehlikeli kabulü belirgin biçimde azaltır.

**Adım 5 — İyileştir.** Eşikler yalnızca ID doğrulama kümesinden seçilir: OOD eşiği yüzde 5, belirsizlik eşiği yüzde 95 yüzdeliği. Dağılım dışı veri eşik seçiminde kullanılmaz. Conformal α'sı 0,10 seçilir. OOD dedektörü Deney 1'e göre Mahalanobis'tir. Geri dönüş tanımlanır: karar yok, hedef takibi sürer, operatöre bilgi gider.

**Adım 6 — Doğrula.** Deney 8'in üç tohumlu sonuçlarını gereksinimlere karşı kontrol ediyoruz.

| Politika | Tehlikeli kabul | Gereksinim (a): ≤ %3 | ID kabulü | Gereksinim (b): ≥ %80 |
|---|---|---|---|---|
| Koruma yok | 0,432 | sağlanmıyor | 1,000 | sağlanıyor |
| OOD | 0,093 | sağlanmıyor | 0,959 | sağlanıyor |
| OOD + belirsizlik | 0,040 | sağlanmıyor | 0,921 | sağlanıyor |
| OOD + belirsizlik + conformal | 0,027 | sağlanıyor | 0,853 | sağlanıyor |

Yalnızca üç kapılı politika gereksinim (a)'yı sağladı (0,027 ≤ 0,03). Dört politikanın hepsi (b)'yi sağladı (ID kabulü ≥ 0,80). Bu, tasarımın gereksinimleri karşıladığını gösterir; ama gereksinim (a) yüzde 3 sınırına yalnızca 0,003 pay bırakıyor. Üç tohumun tehlikeli kabul sapması 0,002 olduğu için bu pay ince.

**Bunu AI'sız yazabilir misin?** Bir sonraki soru: ID doğrulama kümesinde OOD eşiği yüzde 95 kabul sağlayacak şekilde seçildiyse, neden üç kapılı sistemde ID kabul oranı yüzde 85'e düştü ve yüzde 95 olmadı? Cevabı, üç kapının birlikte nasıl çalıştığını düşünerek yaz.

## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi yapay zekâ aracı olmadan yap. Önce kağıtta tasarımı çiz, eşikleri ve sınırları elle hesapla, sonra kodla. Ölçümler için bu bölümdeki betiklerin yaptığı gibi üç tohum kullan ve test kümesini eşik seçiminde kullanma. Kendi değerlendirme kodunu yaz; bu bölümdeki kodu kopyalayıp yalnızca çalıştırmak öğrenmek sayılmaz.
:::

### Proje 1 (★★): Tek komutla güvenilirlik değerlendirme paketi

**Amaç.** Bir sınıflandırıcı ve bir OOD kümesi verildiğinde tek bir komutla şu raporu üreten bir araç yazmak: kalibrasyon (ECE ve güvenilirlik diyagramı), OOD ayrımı (AUROC ve FPR@95), conformal kapsama (α için) ve PGD ile sağlam doğruluk eğrisi. Rapor hem bir CSV dosyası hem de okunabilir bir metin özeti üretmeli.

**Yapılacaklar / beklenen davranış.** Komut, model dosyasını ve veri kümesini girdi olarak alır. Veri bölmelerini sabit tohumla yapar. Dört bölüm için ayrı sayılar üretir ve hepsini aynı çalıştırmada üç tohumla tekrarlar. Test kümesi hiçbir eşik seçiminde kullanılmaz; bu kural kodda zorlanmalıdır.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Bu bölümdeki `ece`, `auroc`, `fpr95`, `konformal_esik` ve `pgd` fonksiyonlarını yeniden kullan, ama onları bir modül dosyasında topla. Her bölümü ayrı bir fonksiyon yap ve sonuçları bir sözlükte topla. Raporu yazarken bütün sayıları ortalama ± sapma olarak yaz.

**Başarı kriterleri.** (1) Komut tek bir satırla çalışıyor ve üç tohumun her biri için aynı sonucu iki kez üretiyor. (2) Eşik seçimi yalnızca doğrulama kümesini kullanıyor; bunu kodda gösteren bir test var. (3) Sağlam doğruluk eğrisi, en az üç ε değeri ve ε = 0 için temiz doğruluğu içeriyor. (4) Rapor, her sayının hangi tohumlardan geldiğini belirtiyor.

### Proje 2 (★★★): Sertifikalı küçük model: IBP eğitimi ile rastgele düzgünleştirmenin karşılaştırılması

**Amaç.** Aynı küçük veri kümesinde (rakam tanıma) iki sertifikalı sağlamlık yöntemini karşılaştırmak: IBP ile eğitilmiş bir ağın sertifikalı doğruluğu ile gürültü ile eğitilmiş bir modelin rastgele düzgünleştirme sertifikası. İki yöntemin farklı tehdit modelleri (L∞ ve L2) olduğunu hesaba katan bir karşılaştırma tasarla.

**Yapılacaklar / beklenen davranış.** IBP eğitimi için ε_eğitim değerini ve κ takvimini seç, hem IBP hem standart modeli üç tohumla eğit. Rastgele düzgünleştirme için σ seç ve 100 test örneğini sertifikala. Sonuçları iki ayrı eğride göster; ortak bir eksende ama açıkça etiketlenmiş iki norm ile. Sonunda hangi yöntemin hangi ε ya da r'de daha iyi olduğunu tartış.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** IBP için bu bölümdeki `ibp_torch` ve `ibp_kayip` fonksiyonlarını kullan; numpy doğrulamasını `ibp_np` ile yap. Rastgele düzgünleştirme için `rs_sertifika` fonksiyonu hazır; σ'yı değiştirerek r_max'in σΦ⁻¹(α^{1/n}) ile sınırlı olduğunu kendi sayılarında doğrula. Karşılaştırmada L∞ ile L2'yi doğrudan eşleştirmeye çalışma: her biri için ayrı bir tehdit yarıçapı belirle.

**Başarı kriterleri.** (1) Hiçbir ε'da IBP sertifikalı doğruluğu, aynı ε'daki PGD doğruluğunu aşmıyor. (2) Rastgele düzgünleştirmede tüm r değerleri için r ≤ σΦ⁻¹(α^{1/n}) koşulu sağlanıyor ve üst sınır doğrulanıyor. (3) İki yöntemin temiz doğrulukları ve eğitim maliyetleri aynı tabloda raporlanıyor. (4) Rapor, iki sertifikanın neden doğrudan karşılaştırılamayacağını açıklıyor.

### Ek Alıştırmalar

1. (★) Test kümesi 360 örnek ve doğruluk 0,95 ise, binom standart hatası nedir? Bu hata, iki modelin doğruluk farkını yorumlamak için neden önemlidir?
2. (★) Bir kalibrasyon kümesinde n = 99 ve α = 0,05 için k değerini hesapla. Eşik q, sıralı skorların hangi değeridir?
3. (★) Doğrusal bir modelin w = (0,5; −1,5; 2) vektörü, b = 0 ve x = (1; 1; 1) girdisi için, L∞ ε-topunda kararın değişmediği en büyük ε değerini hesapla.
4. (★) Randomized smoothing'te n = 100 tahmin örneği ve α = 0,001 için p_A'nın alt sınırı en fazla ne olabilir? Bu sınırla σ = 0,5 için R'yi hesapla.
5. (★★) Bir topluluk üyeleri tahmin olasılıklarını aynı verdiğinde epistemik belirsizlik ne olur? Aleatorik ve toplam belirsizlik arasındaki ilişkiyi yaz.
6. (★★) Bir gradyan maskeleme şüphesi: naif kayıpla FGSM sıfır değişiklik üretiyor. Bunun doygunluktan mı yoksa gerçek sağlamlıktan mı kaynaklandığını ayırt eden iki kontrol öner.
7. (★★) Bir OOD dedektörünün FPR@95 değeri 0,6 ise, ID verisinin yüzde 5'ini reddedip OOD'un yüzde 40'ını kabul ettiğini söyleyebilir miyiz? Cevabını gerekçelendir.
8. (★★) Shapley değerlerinde 10 öznitelik için tam hesap kaç koalisyon gerektirir? Örnekleme için 50 permütasyon ne kadar koalisyon ölçümü yapar (her permütasyonda n + 1 değer gerektiğini düşün)?
9. (★★★) Mülakat: Bir ekip, modelinin doğruluğunu yüzde 98 olarak raporladı ve "güvenli" dediğini söyledi. Bu bölümdeki hangi üç soruyu sorarsın?
10. (★★) Mülakat: Conformal tahmin neden "garanti" verir ama bir kalibrasyon kümesi için koşullu garanti vermez? Bu ikisinin pratikte farkı nedir?
11. (★★★) Mülakat: Bir savunma sistemi için ML bileşeninin sertifikasyonunda, deterministik yazılım standartlarının hangi varsayımı ML ile çelişir? Bu çelişkiye karşı iki mimari önerin olsun.
12. (★★) Mülakat: Adalet ölçütleri neden aynı anda sağlanamaz? Savunma uygulamasında hangi ölçütü neden seçersin?

## Kod Okuma Egzersizi

Aşağıdaki kesit scikit-learn 1.8.0 kaynağından alındı: `sklearn/calibration.py`, yerel kurulumda `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\sklearn\calibration.py`. Sınıf `_SigmoidCalibration` ve ona bağlı `_sigmoid_calibration` fonksiyonudur. Kesit üç parçadır. Birinci parçada docstring'ler ve boş satırlar kaldırıldı. İkinci ve üçüncü parçalar aynı fonksiyondan alındı; arada `loss_grad` iç fonksiyonunun gövdesi (kayıp ve gradyan hesabı) yer kaybı için atlandı, bu yüzden üçüncü parça ona doğrudan çağrı yapan bir satırla başlıyor gibi görünür. Ayrıca fonksiyonun sonundaki üç uzun yorum satırı kesitte yer almıyor. Bunların hepsi kısaltmadır; kod satırları birebir kopyalanmıştır.

Önce sınıfın kabuğu: ayrı bir eğitim ve tahmin yüzeyi var. `fit` kalibrasyon parametrelerini öğrenir, `predict` ise bir logit benzeri girdiyi sigmoid ile olasılığa çevirir.

```python
class _SigmoidCalibration(RegressorMixin, BaseEstimator):
    def fit(self, X, y, sample_weight=None):
        X = column_or_1d(X)
        y = column_or_1d(y)
        X, y = indexable(X, y)
        self.a_, self.b_ = _sigmoid_calibration(X, y, sample_weight)
        return self
    def predict(self, T):
        T = column_or_1d(T)
        return expit(-(self.a_ * T + self.b_))
```


Sayısal kalibrasyon işi `_sigmoid_calibration` içinde yapılır. Önce hedef değerler, yani "Platt'ın Bayesçi önselleri" hesaplanır. Pozitif ve negatif örnek sayılarına göre hedef olasılık 1'den ve 0'dan kaydırılır. Bu, sonsuz güven isteyen bir kalibrasyonu önler.

```python
    # Bayesian priors (see Platt end of section 2.2):
    # It corresponds to the number of samples, taking into account the
    # `sample_weight`.
    mask_negative_samples = y <= 0
    if sample_weight is not None:
        prior0 = (sample_weight[mask_negative_samples]).sum()
        prior1 = (sample_weight[~mask_negative_samples]).sum()
    else:
        prior0 = float(np.sum(mask_negative_samples))
        prior1 = y.shape[0] - prior0
    T = np.zeros_like(y, dtype=predictions.dtype)
    T[y > 0] = (prior1 + 1.0) / (prior1 + 2.0)
    T[y <= 0] = 1.0 / (prior0 + 2.0)
```


Son parça ise parametreleri bir optimizasyonla bulur: L-BFGS-B ile kayıp minimize edilir ve sonuç ölçek ile kaydırma değerleri olarak döndürülür.

```python
    AB0 = np.array([0.0, log((prior0 + 1.0) / (prior1 + 1.0))])

    opt_result = minimize(
        loss_grad,
        AB0,
        method="L-BFGS-B",
        jac=True,
        options={
            "gtol": 1e-6,
            "ftol": 64 * np.finfo(float).eps,
        },
    )
    AB_ = opt_result.x

    return AB_[0] / scale_constant, AB_[1]
```


**Sorular — cevaplamadan geçme:**

1. `predict` fonksiyonundaki `expit(-(self.a_ * T + self.b_))` ifadesinde eksi işaretinin nedeni nedir? Bu, logit ile olasılık arasındaki hangi ilişkiyle tutarlıdır?
2. Bayesçi önsel hedefleri T'de (1 + 1) ve (N + 2) paydalarıyla neden hesaplanıyor? Pozitif örnek sayısı sıfır olduğunda ne olur?
3. Bu fonksiyon bir sıcaklık ölçekleme (Bölüm 78.4) midir? Hangi açıdan benzer, hangi açıdan farklıdır? Yalnızca sıcaklık değil, bir kayma parametresi de öğreniyor; bunun bir sonucu nedir?
4. `minimize` çağrısında `jac=True` ne anlama gelir? Kayıp fonksiyonu gradyanı kendisi döndürmeseydi optimizasyon nasıl yapılırdı?
5. Bu bölümdeki `ece` fonksiyonumuz kutu ağırlıklı bir ortalama hesaplıyordu. Scikit-learn'ün `calibration_curve` fonksiyonu (1.8.0) kutuları eşit genişlikte mi yoksa eşit sayıda örnekli mi kurar? İki yaklaşımın ECE üzerindeki farkı ne olabilir?
6. Eğer kalibrasyon kümesi küçükse (örneğin 30 örnek), bu tür bir parametrik kalibrasyon ile sıralı (isotonic) kalibrasyon arasında nasıl bir seçim yaparsın? Bu bölümdeki ölçümlerle nasıl doğrularsın?

## Bölüm Özeti

- Güvenilir AI yedi boyuttan oluşur: doğruluk, sağlamlık, kalibrasyon, açıklanabilirlik, adalet, güvenlik ve izlenebilirlik. Bu boyutlar birbirleriyle takas içindedir ve takas yazılı olarak tanımlanmalıdır.
- Dağılım dışı tespitte, bu veride, Mahalanobis uzaklığı (AUROC 0,982) MSP (0,795) ve enerji skorundan (0,696) belirgin biçimde üstündü. Softmax olasılığı OOD girdilerde de yüksek güven verebilir.
- Epistemik belirsizlik, topluluk üyelerinin ayrışmasından ölçülür (AUROC 0,908). Sıcaklık ölçekleme her zaman ECE'yi düşürmez; ölçüt seçimi ve örneklem büyüklüğü sonucu değiştirir.
- Conformal tahmin, sınıf-temelli bir eşikle marjinal kapsama garantisi verir. Tek bir kalibrasyon kümesinde kapsama nominal değerin altına inebilir; garanti süreç düzeyindedir.
- Çekişmeli sağlamlık, bir alt sınır değil bir üst sınır ölçüsüdür. Saldırı zayıfsa sağlamlık yanıltıcı biçimde yüksek görünür. Naif kayıpla gradyan maskelemesi bu yanılsamanın tipik bir kaynağıdır.
- Çekişmeli eğitim (PGD-AT) ε = 0,10'da sağlam doğruluğu 0,43'ten 0,77'ye çıkardı; temiz doğruluktaki kayıp bu veride 0,004 kadardı.
- IBP sertifikası hiçbir zaman yanlış bir sertifika vermez ama gevşek olabilir. Eğitimde IBP kullanımı, sertifikalı doğruluğu ε = 0,02'de 0'dan 0,885'e çıkardı.
- Açıklamalar bir ölçümdür; tamlık (IG) ve sanity kontrolleriyle sınanmalıdır. Shapley'nin tam hesabı 8 öznitelikte 256 koalisyon gerektirir.
- Savunma sanayiinde ML bileşeni tek başına sertifikalanmaz; ODD, bağımsız kapılar, güvenli geri dönüş ve denetim izi ile bir sistem mimarisi içinde sınırlandırılır. Bu bölümdeki İHA mimarisinde tehlikeli kabul yüzde 43'ten yüzde 2,7'ye indi, ama ID kabulü yüzde 85'e düştü.

**Sonraki bölümde:** Bölüm 79'da (Makale Okuma & Araştırma Yöntemi) bu bölümdeki her iddianın hangi kanıtla desteklendiğini okumayı, bir makalenin deneyini nasıl yeniden üreteceğimizi ve sonuçlarımızı nasıl yazacağımızı göreceğiz. Bu bölümde yaptığımız gibi tohumlu tekrar, ayrı test kümesi ve açık takas raporu, bu yöntemin temel parçalarıdır.

::: mulakat
1. Bir modelin doğruluğu yüzde 98 ama AUROC'u 0,70. Bu iki sayı birbirini nasıl çelişmeden açıklar ve hangisi güvenlik kapısı için daha önemlidir?
2. Softmax olasılığı neden OOD girdilerde yüksek güven verebilir? Logit'lerin ölçeği ile bu davranış arasında bir bağlantı kurabilir misin?
3. Topluluk üyeleri birbirine çok benziyorsa epistemik belirsizlik neden düşük çıkar? Bu bir güvence midir?
4. Conformal tahmin ile sıcaklık ölçekleme aynı problemi çözmez. Hangi durumda hangisini seçersin ve neden?
5. L∞ ve L2 sertifikaları neden doğrudan karşılaştırılamaz? Bir girdinin hangi geometrik ayrımı bu iki normu farklı kılar?
6. Bir IBP sertifikası "yok" diyorsa, modelin gerçekten yanıldığını söyleyebilir miyiz? Cevabını bu bölümdeki ε = 0,02 sonucuyla açıkla.
7. Bir savunmanın sağlamlığını ölçmek için hangi üç farklı saldırı ailesini kullanmalısın ve neden her birini ekliyorsun?
8. Güvenlik kritik bir sistemde reddetme oranı yüzde 15'e çıktı. Bunu bir kusur mu yoksa bir özellik mi olarak raporlarsın? Hangi veriye dayanarak karar verirsin?
:::
