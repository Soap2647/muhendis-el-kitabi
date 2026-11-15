%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 64
%% baslik: Eğitimin Sanatı

## Giriş: Model kurmak kadar eğitmek de bir sanattır

Bölüm 63'te bir sinir ağının nasıl ileri hesaplandığını, kaybın nasıl geri yayıldığını ve yalın gradyan inişinin neden işe yaradığını gördün. Orada ağı eğitmek, öğrenme oranını bir sayı olarak seçip döngüyü çalıştırmaktan ibaretti. Gerçek projede bu yeterli değil. Aynı ağ bir koşuda %97 doğruluğa çıkarken başka bir koşuda hiç öğrenmez; aynı kodu iki kez çalıştırdığında sonuç değişir; daha büyük bir batch kullandığında kayıp düşmek yerine salınır. Eğitim, bu nedenle bir kod yazma işinden çok bir deney yapma işidir.

Savunma sanayiinde bu fark somut bir maliyete dönüşür. Bir İHA'nın hedef tanıma modeli haftalarca eğitilir, sonra bir yazılım sürümünde yeniden eğitilir. Eğitim koşusu pahalıdır, GPU saati ve mühendis zamanı harcanır. Kötü giden bir koşuyu hızlıca teşhis edebilmek ve doğru değişikliği yapabilmek, bu sürecin en değerli becerisidir. Mert'in EV Dashboard projesinde bir sinir ağı batarya hücrelerinin sıcaklık örüntüsünü öğreniyorsa, aynı disiplin tek bir hücrenin neden yanlış tahmin edildiğini bulmak için de gerekir.

Bu bölümün iddiası şudur: iyi bir eğitim, birkaç iyi seçilmiş tekniğin bilinçli bir kombinasyonudur ve her tekniğin ne işe yaradığını ölçerek görebilirsin. Önce optimizasyon algoritmalarını (momentum, Adam, AdamW) ve öğrenme oranı takvimlerini ele alacağız. Sonra başlatmanın (initialization) derin ağlardaki önemini, normalizasyonu (BatchNorm, LayerNorm) ve düzenlileştirmeyi (dropout, ağırlık azaltma, etiket yumuşatma, erken durdurma) göreceğiz. Bölümün kalbi ise eğitim hatası ayıklamadır: loss eğrisine bakarak teşhis koymak, tek bir batch'e aşırı uydurarak kodu sınamak ve kasıtlı hatalarla kendi kendini kontrol etmek.

Bu bölümdeki sayısal iddialar ölçümle desteklenir; ölçmediğimiz yerleri metinde açıkça belirtiyoruz. Veri olarak scikit-learn'ün `load_digits` kümesini kullandık (1797 örnek, 64 özellik, 10 sınıf). Veri her deneyde aynı şekilde %60 eğitim, %20 doğrulama ve %20 test olarak bölündü. Test kümesi, hiçbir karar için kullanılmadı; her karşılaştırma beş tohumla (seed) yapıldı ve sonuçlar ortalama ± sapma olarak verildi. Sayılar tek bir koşuya değil, bu tekrarlara dayanır.

::: not
Bu bölümde PyTorch'u bir ölçüm aracı olarak kullandık, öğretici bir çerçeve olarak değil. Tensörler, autograd ve `nn.Module` ayrıntıları Bölüm 65'in konusu. Burada `torch.optim` ve `torch.nn` yapılarını, yazdığımız NumPy kodunun doğru olduğunu sınamak için kullandık. Eğitim deneylerinin hepsi CPU üzerinde ve sabit tohumla yapıldı; böylece sonuçlar yeniden üretilebilir. GPU ölçümleri Bölüm 65 ve 76'da ele alınacak.
:::

## 64.1 Eğitim bir deney disiplinidir

Bir sinir ağını eğitirken her değişiklik birden fazla şeyi aynı anda etkiler. Öğrenme oranını değiştirdiğinde, aynı zamanda adım büyüklüğünü, gürültü düzeyini ve nihai kararlılığı değiştirirsin. Bu yüzden eğitim, bilimsel bir deney gibi yürütülmelidir: bir kerede tek bir şey değiştir, ölç, tekrar et.

Üç kural bu disiplinin omurgasıdır. Birincisi **tek değişken**: karşılaştırdığın iki koşu yalnızca incelediğin faktörde farklı olmalı. İkincisi **tohum**: sinir ağının başlangıç ağırlıkları ve mini-batch sırası rastgeledir. Tek bir koşudan elde edilen "bu daha iyi" yargısı, tohumun şansı olabilir. Üçüncüsü **ayrı test kümesi**: karar verirken kullandığın ölçü, son raporlanan ölçüden farklı bir veriden gelmeli. Bölüm 57'de gördüğümüz gibi, hiperparametreyi test kümesinde seçersen test skoru artık tarafsız bir tahmin olmaz.

Bu bölümdeki deneylerin hepsinde bu kurallara uyduk. Veri üç parçaya ayrıldı; tohumlar 0'dan 4'e kadar beşer koşu yapıldı; öğrenme oranı seçimleri yalnızca doğrulama kümesinde, ayrı tohumlarla yapıldı. Test kümesi en sonda, seçilen modele bir kez uygulandı.

Eğitimin ilk kontrolü de bir disiplin meselesidir. Her sınıflandırma ağı eğitime başlamadan önce bir beklenen başlangıç kaybına sahiptir. Eğer ağ her sınıfa eşit olasılık veriyorsa, çapraz entropi kaybı ln C olur (Bölüm 51). `C = 10` için bu 2,302585'tir. Başlangıç kaybın bu değerden çok uzaksa, ağın çıkış katmanında ya da veri etiketlerinde bir sorun vardır. Bu kontrolü bölümün sonunda, eğitim hatası ayıklamada tekrar kullanacağız.

## 64.2 Mini-batch, gradyan gürültüsü ve batch boyutu

Bölümdeki tüm deneyler, veri ve eğitim döngüsü için aynı küçük altyapıyı kullanır. Bu dosya ilk deneyden önce verilir: veri bölmesi, MLP kurucu, eğitim döngüsü ve kayıt yardımcıları. Dosyanın başındaki `VERI` yolu, deney çıktılarının yazıldığı klasördür; okur kendi bilgisayarında bu yolu değiştirebilir.

```python
# -*- coding: utf-8 -*-
"""Bolum 64 deneyleri icin ortak veri, model ve egitim dongusu.

Veri: sklearn load_digits (1797 ornek, 8x8 = 64 ozellik, 10 sinif).
Bolme sabit: %60 egitim, %20 dogrulama, %20 test (stratified,
random_state=0). Tohum (seed) yalnizca baslangic agirliklarini ve
mini-batch sirasini degistirir; veri bolmesi her kosuda aynidir.
"""

import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
SEEDS = [0, 1, 2, 3, 4]
torch.set_num_threads(1)
```
```python
def veri():
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).astype(np.float32)
    Xtr, Xg, ytr, yg = train_test_split(
        X, y, test_size=0.4, stratify=y, random_state=0
    )
    Xva, Xte, yva, yte = train_test_split(
        Xg, yg, test_size=0.5, stratify=yg, random_state=0
    )
    t = torch.tensor
    return (t(Xtr), t(ytr), t(Xva), t(yva), t(Xte), t(yte))
```
```python
def mlp(gizli=128, derinlik=2, bn=False, dropout=0.0, giris=64):
    kat, d = [], giris
    for _ in range(derinlik):
        kat.append(nn.Linear(d, gizli))
        if bn:
            kat.append(nn.BatchNorm1d(gizli))
        kat.append(nn.ReLU())
        if dropout > 0:
            kat.append(nn.Dropout(dropout))
        d = gizli
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)
```
```python
@torch.no_grad()
def olc(model, X, y):
    model.eval()
    out = model(X)
    return (
        F.cross_entropy(out, y).item(),
        (out.argmax(1) == y).float().mean().item(),
    )
```
```python
def egit(
    model,
    opt,
    veri_,
    epochs=30,
    batch=32,
    seed=0,
    lr_fn=None,
    klip=None,
    erken=None,
    ls=0.0,
):
    """Egitim dongusu. lr_fn(adim) verilirse her adimda lr ayarlanir.
    Doner: gecmis sozlugu; son adimda dogrulama ve test metrikleri."""
    Xtr, ytr, Xva, yva, Xte, yte = veri_
    g = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    n, adim = len(Xtr), 0
    h = {"tr": [], "va": [], "vacc": [], "lr": [], "gnorm": []}
    en_iyi, en_iyi_ep = 1e9, -1
```
```python
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(n, generator=g)
        top, cnt = 0.0, 0
        for i in range(0, n, batch):
            idx = perm[i : i + batch]
            if lr_fn is not None:
                for pg in opt.param_groups:
                    pg["lr"] = lr_fn(adim)
            opt.zero_grad()
            loss = F.cross_entropy(
                model(Xtr[idx]), ytr[idx], label_smoothing=ls
            )
            loss.backward()
            gn = torch.sqrt(
                sum((p.grad**2).sum() for p in model.parameters())
            ).item()
            if klip is not None:
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), klip
                )
            opt.step()
            adim += 1
            top += loss.item() * len(idx)
            cnt += len(idx)
            h["gnorm"].append(gn)
            h["lr"].append(opt.param_groups[0]["lr"])
        vl, va = olc(model, Xva, yva)
        h["tr"].append(top / cnt)
        h["va"].append(vl)
        h["vacc"].append(va)
        if vl < en_iyi:
            en_iyi, en_iyi_ep = vl, ep
        if erken is not None and ep - en_iyi_ep >= erken:
            break
```
```python
    _, h["test_acc"] = olc(model, Xte, yte)
    _, h["val_acc"] = olc(model, Xva, yva)
    h["adim"] = adim
    h["en_iyi_ep"] = en_iyi_ep
    return h
```
```python
def csv_yaz(ad, satirlar, basliklar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    return yol
```
```python
def ortalama_sapma(xs):
    a = np.array(xs, dtype=float)
    return a.mean(), a.std(ddof=1) if len(a) > 1 else 0.0
```


Bölüm 50'de gradyan inişinin tam veriyle hesaplanan gradyanla ve stokastik (SGD) biçimiyle nasıl farklılaştığını gördük. Tam gradyan, tüm eğitim kümesinin ortalamasıdır. Her adımda bu ortalamayı hesaplamak pahalıdır. Mini-batch SGD, veriden rastgele bir alt küme seçer ve gradyanı yalnızca o alt küme üzerinden hesaplar. Bu tahmin gürültülüdür, ama her adım çok daha ucuzdur.

Gürültünün büyüklüğü batch boyutuna bağlıdır. Tam gradyanı g, batch gradyanını g_b ile gösterelim. Rastgele bir batch'in beklenen kareli hatası kabaca şöyle davranır:

E‖g_b − g‖² ≈ (σ²/b) · (1 − b/N)

Burada σ² tek bir örneğin gradyanının varyansı, b batch boyutu, N ise veri kümesi büyüklüğüdür. Çarpan (1 − b/N), örnekleme sırasında veri kümesi tükendikçe gürültünün azalmasını anlatan sonlu popülasyon düzeltmesidir. Gürültü, batch büyüdükçe ters orantılı olarak düşer. Batch'i 4 kat büyütmek gürültüyü kabaca 4 kat azaltır; ama aynı epoch için yapılan adım sayısı da 4 kat düşer.

Aşağıdaki betik iki ölçümü birlikte yapar. Birinci bölümde başlangıç ağırlıklarında tek bir ağın gradyanını hesaplar ve 300 rastgele batch için tam gradyandan sapmayı ölçer. İkinci bölümde 30 epoch boyunca sabit ve doğrusal ölçekli öğrenme oranlarıyla beş tohumlu eğitimleri tekrarlar. Sonuçlar aşağıdaki tablolarda ve Şekil 64.1'de özetlenir.

```python
# -*- coding: utf-8 -*-
"""Deney 1: batch boyutu, gradyan gurultusu ve ogrenme orani."""

import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import veri, mlp, egit, csv_yaz, SEEDS, ortalama_sapma

D = veri()
Xtr, ytr = D[0], D[1]

# (a) Gradyan gurultusu: tam gradyana gore sapma, batch boyutuna gore
torch.manual_seed(0)
model = mlp()
```
```python
def grad_vec(idx):
    model.zero_grad()
    F.cross_entropy(model(Xtr[idx]), ytr[idx]).backward()
    return torch.cat(
        [p.grad.flatten() for p in model.parameters()]
    ).clone()


tam = grad_vec(torch.arange(len(Xtr)))
g = torch.Generator().manual_seed(1)
gur_satir = []
print("Gradyan gurultusu (init, 300 tekrar):")
for b in [8, 32, 128, 512]:
    fark2 = []
    for _ in range(300):
        idx = torch.randperm(len(Xtr), generator=g)[:b]
        fark2.append(((grad_vec(idx) - tam) ** 2).sum().item())
    ort = np.mean(fark2)
    gur_satir.append((b, ort))
    print("  batch=%4d  E||g_b - g||^2 = %.6f" % (b, ort))
base = gur_satir[0][1]
for b, v in gur_satir:
    print("  batch=%4d  oran (8'e gore) = %.3f" % (b, v / base))
csv_yaz(
    "b64_gurultu.csv",
    [(b, "%.6f" % v) for b, v in gur_satir],
    ["batch", "gurultu"],
)
```
```python
# (b) Sabit epoch, sabit lr vs dogrusal lr olcegi
satirlar = []
print("\nEpoch=30, SGD (momentum yok), 5 tohum:")
for mod, lr_f in [
    ("sabit_lr=0.1", lambda b: 0.1),
    ("dogrusal_olcek", lambda b: 0.1 * b / 32),
]:
    for b in [8, 32, 128, 512]:
        accs, adims = [], []
        for s in SEEDS:
            torch.manual_seed(s)
            m = mlp()
            opt = torch.optim.SGD(m.parameters(), lr=lr_f(b))
            h = egit(m, opt, D, epochs=30, batch=b, seed=s)
            accs.append(h["test_acc"])
            adims.append(h["adim"])
            satirlar.append(
                (mod, b, s, "%.4f" % h["test_acc"], h["adim"])
            )
        mu, sd = ortalama_sapma(accs)
        print(
            "  %-16s batch=%4d adim=%5d  test=%.4f +- %.4f"
            % (mod, b, adims[0], mu, sd)
        )
csv_yaz(
    "b64_batch.csv",
    satirlar,
    ["mod", "batch", "seed", "test_acc", "adim"],
)
```
```term
$ python t01_batch.py
Gradyan gurultusu (init, 300 tekrar):
  batch=   8  E||g_b - g||^2 = 0.386054
  batch=  32  E||g_b - g||^2 = 0.091766
  batch= 128  E||g_b - g||^2 = 0.020654
  batch= 512  E||g_b - g||^2 = 0.003085
  batch=   8  oran (8'e gore) = 1.000
  batch=  32  oran (8'e gore) = 0.238
  batch= 128  oran (8'e gore) = 0.054
  batch= 512  oran (8'e gore) = 0.008

Epoch=30, SGD (momentum yok), 5 tohum:
  sabit_lr=0.1     batch=   8 adim= 4050  test=0.9767 +- 0.0032
  sabit_lr=0.1     batch=  32 adim= 1020  test=0.9633 +- 0.0036
  sabit_lr=0.1     batch= 128 adim=  270  test=0.9356 +- 0.0036
  sabit_lr=0.1     batch= 512 adim=   90  test=0.7744 +- 0.0865
  dogrusal_olcek   batch=   8 adim= 4050  test=0.9656 +- 0.0058
  dogrusal_olcek   batch=  32 adim= 1020  test=0.9633 +- 0.0036
  dogrusal_olcek   batch= 128 adim=  270  test=0.9672 +- 0.0063
  dogrusal_olcek   batch= 512 adim=   90  test=0.1639 +- 0.0844
```

Bunu ölçmek için ağı başlangıç ağırlıklarında tuttuk ve 300 rastgele batch üzerinde tam gradyandan sapmayı hesapladık. Sonuçlar teoriyle uyumludur:

| Batch boyutu | E‖g_b − g‖² (ölçüm) | Oran (8'e göre) | Teorik oran |
|---|---|---|---|
| 8 | 0,386054 | 1,000 | 1,000 |
| 32 | 0,091766 | 0,238 | 0,246 |
| 128 | 0,020654 | 0,054 | 0,055 |
| 512 | 0,003085 | 0,008 | 0,013 |

Teorik oran, (1/b − 1/N) farkının 8'e göre oranından hesaplanmıştır; N = 1078 eğitim örneği. Ölçüm ile teori arasındaki küçük fark, 300 tekrarın istatistiksel dalgalanmasından gelir.

Bu gürültü neden önemlidir? Küçük batch'te gürültü, optimizasyonu bir düzenlileştirme gibi de etkiler: gradyan rastgele salındığı için ağ dar ve keskin bir minimumdan çıkıp daha geniş bir çukura geçebilir. Bu sezgi, büyük batch'in test performansını neden düşürebildiğini kısmen açıklar. Ama asıl pratik sonuç daha basittir: batch boyutu ve öğrenme oranı birlikte seçilmelidir. Aşağıdaki deneyde sabit bir öğrenme oranıyla (0,1) ve doğrusal ölçekli bir öğrenme oranıyla (0,1 · b/32) batch boyutunu değiştirdik. Her koşu 30 epoch sürdü ve beş tohumla yapıldı.

| Mod | Batch | Adım sayısı | Test doğruluğu (ortalama ± sapma) |
|---|---|---|---|
| Sabit lr = 0,1 | 8 | 4050 | 0,9767 ± 0,0032 |
| Sabit lr = 0,1 | 32 | 1020 | 0,9633 ± 0,0036 |
| Sabit lr = 0,1 | 128 | 270 | 0,9356 ± 0,0036 |
| Sabit lr = 0,1 | 512 | 90 | 0,7744 ± 0,0865 |
| Doğrusal ölçek | 8 | 4050 | 0,9656 ± 0,0058 |
| Doğrusal ölçek | 32 | 1020 | 0,9633 ± 0,0036 |
| Doğrusal ölçek | 128 | 270 | 0,9672 ± 0,0063 |
| Doğrusal ölçek | 512 | 90 | 0,1639 ± 0,0844 |

Tablo üç şeyi gösteriyor. Sabit öğrenme oranıyla batch büyüdükçe adım sayısı düşer ve 512'lik batch'te model 90 adımda yetersiz kalır. Doğrusal ölçekleme, 128'e kadar işe yarar ve 270 adımda 0,967'ye ulaşır. Ama 512 batch ile öğrenme oranı 1,6'ya çıktığında model çöker: 0,16 doğruluk şans düzeyine yakındır. Yani "batch'i büyüt, öğrenme oranını orantılı artır" kuralı sonsuza kadar geçerli değildir; öğrenme oranının da bir kararlılık sınırı vardır. Bu sınır, gradyan inişinin kararlılık koşulunu hatırlatır (Bölüm 50). Büyük batch'lerde öğrenme oranını artırmak için ısınma (warmup) kullanılır; bunu 64.5'te ele alacağız.

Şekil 64.1, gürültünün batch boyutuyla düşüşünü ve iki öğrenme oranı stratejisinin davranışını birlikte gösteriyor.

![Şekil 64.1: Sol: gradyan gürültüsü batch boyutuyla ters orantılı azalır. Sağ: batch büyüdükçe sabit ve doğrusal ölçekli öğrenme oranlarının farkı.](gorseller/b64_gurultu_batch.png)

## 64.3 Momentum, Nesterov, AdaGrad, RMSProp ve Adam

Gradyan inişinin sorunu, kötü koşullu yüzeylerde zikzak çizmesidir. Bölüm 50'de gördüğümüz gibi, eğrilik bir yönde büyük, başka bir yönde küçük olduğunda tek bir öğrenme oranı ya dik yönde salındırır ya da düz yönde çok yavaş ilerletir. Bu sorunu çözmek için iki temel fikir geliştirildi: geçmiş adımların bir kısmını hatırlamak (momentum) ve her parametre için öğrenme oranını ayrı ayarlamak (uyarlamalı yöntemler).

**Momentum**, hızın (v) bir sönümlü birikim olmasını önerir. Her adımda hız, gradyanın kendisine ve bir önceki hızın μ katına göre güncellenir; parametre bu hızla hareket eder:

v ← μv + g
θ ← θ − η · v

Dik yönde gradyan işaret değiştirdiği için hız bu salınımları birbirini sönümleyerek azaltır; düz yönde ise gradyan hep aynı işaretteyse hız birikir ve ilerleme hızlanır. μ genelde 0,9 alınır. **Nesterov**, gradyanı mevcut konumda değil, hızın gösterdiği yeni konumda hesaplamayı önerir. Pratikte PyTorch'un kullandığı biçim, güncellemede gradyanı biraz öne çekerek uygular:

v ← μv + g
θ ← θ − η · (g + μv)

Sıfırdan yazdığımız optimizasyon güncellemeleri `egitim_np.py` dosyasındadır. Dosyanın başı ile momentum ve Nesterov güncellemeleri aşağıdadır:

```python
# -*- coding: utf-8 -*-
"""Bolum 64 - egitim tekniklerinin NumPy ile sifirdan gerceklemesi.

Her fonksiyon kendi basina test edilebilir. PyTorch karsiliklari
test_np64.py icinde gradyan denetimi ve esleme testleriyle kontrol
edilir.
"""

import math
import numpy as np

# ---------- 1. Optimizasyon algoritmalari ----------


def sgd_momentum(theta, g, v, lr=0.01, mu=0.9):
    """Momentum: hiz v birikir, theta hizla guncellenir."""
    v = mu * v + g
    return theta - lr * v, v


def sgd_nesterov(theta, g, v, lr=0.01, mu=0.9):
    """Nesterov: once hizla ileri bak, sonra gradyan hesapla.
    Burada PyTorch'un nesterov=True bicimi kullanilir."""
    v = mu * v + g
    return theta - lr * (g + mu * v), v
```

**AdaGrad** her parametrenin geçmiş gradyan karelerini toplar ve öğrenme oranını bu toplamın karekökü ile böler. Sık değişen parametreler yavaşlar, nadir değişenler hızlanır. Toplam sürekli büyüdüğü için öğrenme oranı zamanla sıfıra yaklaşır; bu bir avantaj gibi görünse de derin ağlarda erken durmaya neden olabilir. **RMSProp**, toplamı üstel bir ortalamayla değiştirerek bu sorunu giderir: geçmiş kareler hızla unutulur.

**Adam** (Kingma ve Ba, 2014), momentumu ve RMSProp'un uyarlamasını birleştirir. İki hareketli ortalama tutar: birinci moment m (gradyanın ortalaması, yani momentum) ve ikinci moment v (gradyan karesinin ortalaması). Güncelleme şöyledir:

m ← β₁m + (1 − β₁)g
v ← β₂v + (1 − β₂)g²
m̂ = m / (1 − β₁ᵗ),   v̂ = v / (1 − β₂ᵗ)
θ ← θ − η · m̂ / (√v̂ + ε)

Burada β₁ = 0,9, β₂ = 0,999 ve ε = 10⁻⁸ tipik değerlerdir. Dikkat edilmesi gereken bölüm, m̂ ve v̂ ile yapılan **sapma düzeltmesidir** (bias correction). m ve v sıfır ile başlatılır. İlk adımlarda hareketli ortalama, gerçek gradyan ortalamasına değil, sıfıra doğru çekilmiş bir değere yaklaşır. Düzeltme olmadan, ilk birkaç yüz adımda v küçük kalır ve adım boyu gereğinden büyük olur. Düzeltme, 1 − β₂ᵗ paydasıyla bu sıfıra çekilmeyi telafi eder. t büyüdükçe 1 − β₂ᵗ → 1 olduğu için düzeltme kendiliğinden kaybolur.

Bunu elle görmek için tek parametreli bir örneği ele alalım: θ₀ = 1,0, η = 0,1 ve gradyan dizisi 0,5, −0,2, 0,1. Aşağıdaki program Adam'ın ilk üç adımını NumPy ile hesaplar. Program `egitim_np.py` dosyasındaki `adam_adim` fonksiyonunu kullanır ve bu fonksiyonun tam kodu bölümün sonunda Kod Okuma kısmında PyTorch'un kendi kaynağıyla karşılaştırılır.

Aşağıdaki kod Adam'ın tek adımını tanımlar. Sapma düzeltmesi, güncellemeden önce m ve v'nin ayrı ayrı bölünmesiyle yapılır:

```python
def adam_adim(theta, g, m, v, t, lr=1e-3, b1=0.9, b2=0.999, eps=1e-8):
    """Bir Adam adimi. t, bu noktaya kadar yapilan adim sayisi."""
    t = t + 1
    m = b1 * m + (1 - b1) * g
    v = b2 * v + (1 - b2) * g * g
    mh = m / (1 - b1**t)  # sapma duzeltmesi
    vh = v / (1 - b2**t)
    theta = theta - lr * mh / (np.sqrt(vh) + eps)
    return theta, m, v, t
```

Aşağıdaki program aynı fonksiyonu üç adım boyunca çağırır ve ara değerleri yazdırır. Böylece her satırı elle kontrol edebilirsin:

```python
# -*- coding: utf-8 -*-
"""Adam'in ilk uc adimini elle izlemek icin: tek parametre."""

import numpy as np
from egitim_np import adam_adim

theta, m, v, t = 1.0, 0.0, 0.0, 0
gradyanlar = [0.5, -0.2, 0.1]
print("adim     g       m        v        m_hat    v_hat    theta")
for g in gradyanlar:
    theta, m, v, t = adam_adim(theta, g, m, v, t, lr=0.1)
    m_hat = m / (1 - 0.9**t)
    v_hat = v / (1 - 0.999**t)
    print(
        "%d  %+.2f  %.5f  %.6f  %.5f  %.5f  %.6f"
        % (t, g, m, v, m_hat, v_hat, theta)
    )
```

Program şu çıktıyı verir:

```term
$ python adam_iz.py
adim     g       m        v        m_hat    v_hat    theta
1  +0.50  0.05000  0.000250  0.50000  0.25000  0.900000
2  -0.20  0.02500  0.000290  0.13158  0.14495  0.865439
3  +0.10  0.03250  0.000299  0.11993  0.09992  0.827500
```

İlk adımda sapma düzeltmesi tam olarak gradyanı verir: m̂ = 0,5 ve v̂ = 0,25 (yani √v̂ = 0,5). Güncelleme 0,1 · 0,5/0,5 = 0,1 kadar yapılır ve θ 0,9 olur. Bu, Adam'ın her parametreyi kabaca η büyüklüğünde hareket ettirdiğini gösterir; adım gradyanın mutlak büyüklüğünden bağımsızdır. Bu özellik, ölçeği farklı parametreler arasında Adam'ı güçlü kılar; ama aynı zamanda Adam'ın, kaybın ölçeğine karşı SGD kadar duyarlı olmadığı anlamına gelir. Üçüncü satırda gradyan işaret değiştirdiğinde m küçülür ve adım yönü dengelenir.

**AdamW** (Loshchilov ve Hutter, 2019; genel bilgi) bir ince ama önemli ayrıntıyı düzeltir. Adam'da ağırlık azaltma (weight decay) genellikle L2 düzenlileştirme olarak uygulanır: gradyana λθ eklenir. Adam'ın uyarlamalı ölçeği bu eklenen terimi de normalize ettiği için, büyük gradyanlı parametrelerde azaltma etkisi zayıflar. AdamW ise azaltmayı gradyandan ayırır ve doğrudan ağırlığa uygular: θ ← θ(1 − ηλ), ardından normal Adam adımı atılır. Farkı PyTorch kaynağında görebilirsin (Kod Okuma bölümünde). Aşağıdaki kod her iki biçimi yan yana tanımlar:

```python
def adamw_adim(
    theta, g, m, v, t, lr=1e-3, wd=1e-2, b1=0.9, b2=0.999, eps=1e-8
):
    """AdamW: azaltma gradyana karismaz, dogrudan uygulanir."""
    theta = theta * (1 - lr * wd)
    return adam_adim(theta, g, m, v, t, lr, b1, b2, eps)


def adam_l2_adim(
    theta, g, m, v, t, lr=1e-3, wd=1e-2, b1=0.9, b2=0.999, eps=1e-8
):
    """Adam + L2: azaltma gradyana eklenir (Adam'in eski bicimi)."""
    g = g + wd * theta
    return adam_adim(theta, g, m, v, t, lr, b1, b2, eps)
```

Bu iki fonksiyonun ayrımını test etmek için PyTorch'un `torch.optim.AdamW` ve `torch.optim.Adam(weight_decay=...)` sınıflarıyla karşılaştırdık. Sayısal fark makine hassasiyeti düzeyinde kaldı (en fazla 2,2 × 10⁻¹⁶), yani NumPy gerçeklemesi PyTorch ile aynı güncellemeyi yapıyor. Momentum ve Nesterov için de aynı test yapıldı ve fark sıfır çıktı.

Bu bölümde kullandığımız NumPy kodunun tamamı (`egitim_np.py`) ve PyTorch ile eşleşme testi (`test_np64.py`, 19 kontrol) 64.12'de verilmiştir. Tüm kontroller geçti: Adam, AdamW, momentum, BatchNorm ileri ve geri geçişi, dropout, zamanlayıcılar ve gradyan kırpma PyTorch ile eşleşti; BatchNorm'un gradyanı sayısal fark ile de doğrulandı (en büyük fark 1,4 × 10⁻⁹).

## 64.4 Optimizer karşılaştırması: aynı ağ, aynı veri, adil bir seçim

Hangi optimizer'ın daha iyi olduğu sorusu, öğrenme oranı seçimi yapılmadan cevaplanamaz. Her optimizer'ın kendi kararlılık aralığı vardır. Adil bir karşılaştırma, her optimizer'a kendi öğrenme oranı ızgarasını (1e-4'ten 1e-1'e) tanır ve en iyi lr'yi yalnızca doğrulama kümesinde seçer. Seçim için ayrı üç tohum (10, 11, 12) kullanıldı. Sonra seçilen lr ile beş tohumla test ölçüldü. Test kümesi seçim sürecinde hiç kullanılmadı.

Ağ iki gizli katmanlı (128 birim, ReLU) bir MLP'dir; eğitim 30 epoch ve batch 32 ile yapıldı. Sonuçlar aşağıda:

Optimizer karşılaştırmasını yapan betik aşağıdadır. Önce her optimizer için yedi öğrenme oranı yalnızca doğrulama kümesinde (tohum 10–12) denenir; sonra seçilen lr ile test kümesi beş tohumda (0–4) ölçülür.

```python
# -*- coding: utf-8 -*-
"""Deney 2: optimizer karsilastirmasi.

Her optimizer icin ogrenme orani YALNIZCA dogrulama
kumesinde secilir (secim tohumlari 10,11,12). Secilen lr ile
test kumesi 5 tohumda olculur (tohumlar 0-4). Test kumesi
secimde kullanilmaz.
"""

import numpy as np
import torch
from ortak64 import veri, mlp, egit, csv_yaz, SEEDS, ortalama_sapma

D = veri()
SECIM = [10, 11, 12]
LRS = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]

OPT = {
    "SGD": lambda p, lr: torch.optim.SGD(p, lr=lr),
    "Momentum": lambda p, lr: torch.optim.SGD(p, lr=lr, momentum=0.9),
    "Nesterov": lambda p, lr: torch.optim.SGD(
        p, lr=lr, momentum=0.9, nesterov=True
    ),
    "AdaGrad": lambda p, lr: torch.optim.Adagrad(p, lr=lr),
    "RMSProp": lambda p, lr: torch.optim.RMSprop(p, lr=lr),
    "Adam": lambda p, lr: torch.optim.Adam(p, lr=lr),
    "AdamW": lambda p, lr: torch.optim.AdamW(
        p, lr=lr, weight_decay=0.01
    ),
}


def kos(ad, lr, seed):
    torch.manual_seed(seed)
    m = mlp()
    opt = OPT[ad](m.parameters(), lr)
    return egit(m, opt, D, epochs=30, batch=32, seed=seed)


print("Adim 1: lr secimi (yalnizca dogrulama, tohum 10-12)")
secilen = {}
grid_satir = []
```
```python
for ad in OPT:
    skor = {}
    for lr in LRS:
        vals = [kos(ad, lr, s)["val_acc"] for s in SECIM]
        skor[lr] = np.mean(vals)
        grid_satir.append((ad, lr, "%.4f" % skor[lr]))
    en = max(skor, key=skor.get)
    secilen[ad] = en
    print(
        "  %-9s en iyi lr = %-7g dogrulama = %.4f"
        % (ad, en, skor[en])
    )
csv_yaz(
    "b64_lr_izgara.csv", grid_satir, ["optimizer", "lr", "val_acc"]
)
```
```python
print("\nAdim 2: secilen lr ile test (tohum 0-4)")
satir = []
for ad in OPT:
    testler, egriler, vlosses = [], [], []
    for s in SEEDS:
        h = kos(ad, secilen[ad], s)
        testler.append(h["test_acc"])
        egriler.append(h["vacc"])
        vlosses.append(h["va"])
    mu, sd = ortalama_sapma(testler)
    print(
        "  %-9s lr=%-7g test=%.4f +- %.4f" % (ad, secilen[ad], mu, sd)
    )
    E = np.array(egriler)
    L = np.array(vlosses)
    for ep in range(E.shape[1]):
        satir.append(
            (
                ad,
                ep + 1,
                "%.5f" % E[:, ep].mean(),
                "%.5f" % E[:, ep].std(ddof=1),
                "%.5f" % L[:, ep].mean(),
                "%.5f" % L[:, ep].std(ddof=1),
            )
        )
csv_yaz(
    "b64_optim_egri.csv",
    satir,
    [
        "optimizer",
        "epoch",
        "vacc_ort",
        "vacc_sd",
        "vloss_ort",
        "vloss_sd",
    ],
)
for k, v in secilen.items():
    print("secim %-9s lr=%g" % (k, v))
```
```term
$ python t02_optim.py
Adim 1: lr secimi (yalnizca dogrulama, tohum 10-12)
  SGD       en iyi lr = 0.1     dogrulama = 0.9712
  Momentum  en iyi lr = 0.1     dogrulama = 0.9814
  Nesterov  en iyi lr = 0.1     dogrulama = 0.9814
  AdaGrad   en iyi lr = 0.03    dogrulama = 0.9777
  RMSProp   en iyi lr = 0.001   dogrulama = 0.9814
  Adam      en iyi lr = 0.003   dogrulama = 0.9842
  AdamW     en iyi lr = 0.003   dogrulama = 0.9851

Adim 2: secilen lr ile test (tohum 0-4)
  SGD       lr=0.1     test=0.9633 +- 0.0036
  Momentum  lr=0.1     test=0.9767 +- 0.0042
  Nesterov  lr=0.1     test=0.9767 +- 0.0025
  AdaGrad   lr=0.03    test=0.9789 +- 0.0015
  RMSProp   lr=0.001   test=0.9611 +- 0.0252
  Adam      lr=0.003   test=0.9739 +- 0.0025
  AdamW     lr=0.003   test=0.9744 +- 0.0030
secim SGD       lr=0.1
secim Momentum  lr=0.1
secim Nesterov  lr=0.1
secim AdaGrad   lr=0.03
secim RMSProp   lr=0.001
secim Adam      lr=0.003
secim AdamW     lr=0.003
```

| Optimizer | Seçilen lr | Doğrulama (seçim) | Test (5 tohum) |
|---|---|---|---|
| SGD | 0,1 | 0,9712 | 0,9633 ± 0,0036 |
| Momentum (0,9) | 0,1 | 0,9814 | 0,9767 ± 0,0042 |
| Nesterov (0,9) | 0,1 | 0,9814 | 0,9767 ± 0,0025 |
| AdaGrad | 0,03 | 0,9777 | 0,9789 ± 0,0015 |
| RMSProp | 0,001 | 0,9814 | 0,9611 ± 0,0252 |
| Adam | 0,003 | 0,9842 | 0,9739 ± 0,0025 |
| AdamW (wd 0,01) | 0,003 | 0,9851 | 0,9744 ± 0,0030 |

Tablodan üç sonuç çıkıyor. Birincisi, bu küçük MLP ve veri kümesinde optimizer farkları küçüktür: en iyi (AdaGrad, 0,9789) ile en kötü ortalama (RMSProp, 0,9611) arasındaki fark yaklaşık %2'dir. Ama RMSProp'un sapması (± 0,0252) çok büyük: beş tohumdan birinin belirgin biçimde düşük olduğunu gösteriyor (bu tohumun neden düşük kaldığını incelemedik). Yani tek bir tohumla "RMSProp kötüdür" ya da "AdaGrad en iyidir" demek yanıltıcı olurdu. İkincisi, doğrulamada en yüksek skoru veren AdamW, testte de Adam'dan biraz yüksek çıktı; ama bu fark sapmalar içinde kalıyor. Üçüncüsü ve en önemlisi, seçim sırasında kullanılan doğrulama skoru ile test skoru arasında sıralama her zaman aynı değil; bu da küçük kümelerde karşılaştırmanın kendisinin ne kadar gürültülü olduğunu gösterir.

Yörüngeleri üreten betik aşağıdadır. Aynı başlangıç noktasından üç optimizer 60 adım yürütülür; her adımın konumu ve kaybı CSV dosyasına yazılır. Şekil 64.2 bu dosyadan çizilmiştir.

```python
# -*- coding: utf-8 -*-
"""Deney 3a: kayip yuzeyinde optimizer yorungeleri.

f(x, y) = 0.5 (x^2 + 10 y^2) kotu kosullu bir ikinci dereceden
fonksiyondur. SGD, momentum ve Adam ayni baslangic noktasindan
baslar; her adimin konumu ve kaybi CSV'ye yazilir."""

import numpy as np
from egitim_np import sgd_momentum, adam_adim
from ortak64 import csv_yaz


def grad(p):
    return np.array([p[0], 10.0 * p[1]])


p0 = np.array([-4.0, 1.0])
ADIM = 60
yol = {}
yol["SGD"] = [p0.copy()]
p = p0.copy()
for _ in range(ADIM):
    p = p - 0.09 * grad(p)
    yol["SGD"].append(p.copy())
yol["Momentum"] = [p0.copy()]
p, v = p0.copy(), np.zeros(2)
for _ in range(ADIM):
    p, v = sgd_momentum(p, grad(p), v, lr=0.09, mu=0.9)
    yol["Momentum"].append(p.copy())
yol["Adam"] = [p0.copy()]
p, m, vv, t = p0.copy(), np.zeros(2), np.zeros(2), 0
for _ in range(ADIM):
    p, m, vv, t = adam_adim(p, grad(p), m, vv, t, lr=0.3)
    yol["Adam"].append(p.copy())
```
```python
satir = []
for ad, pts in yol.items():
    for k, q in enumerate(pts):
        f = 0.5 * (q[0] ** 2 + 10 * q[1] ** 2)
        satir.append(
            (ad, k, "%.6f" % q[0], "%.6f" % q[1], "%.6f" % f)
        )
    print(
        "%-9s son nokta=(%.4f, %.4f)  f=%.2e"
        % (
            ad,
            pts[-1][0],
            pts[-1][1],
            0.5 * (pts[-1][0] ** 2 + 10 * pts[-1][1] ** 2),
        )
    )
csv_yaz(
    "b64_yorunge.csv", satir, ["optimizer", "adim", "x", "y", "f"]
)
```
```term
$ python t03a_yorunge.py
SGD       son nokta=(-0.0139, 0.0000)  f=9.73e-05
Momentum  son nokta=(-0.1411, 0.0066)  f=1.02e-02
Adam      son nokta=(-0.0158, 0.0135)  f=1.04e-03
```

Şekil 64.2, aynı deneyin yörüngelerini ayrı bir kayıp yüzeyinde gösteriyor. Kayıp f(x, y) = ½(x² + 10y²) gibi kötü koşullu bir ikinci dereceden fonksiyondur. Üç optimizer aynı başlangıç noktasından (−4, 1) başlar. SGD ve momentum için öğrenme oranı 0,09, Adam için 0,3 seçildi.

![Şekil 64.2: Sol: üç optimizerin kötü koşullu bir kayıp yüzeyindeki yörüngeleri. Sağ: adım adım kayıp (log ölçek).](gorseller/b64_yorunge.png)

Şekil 64.2'de SGD, dik yönde salınmadan ama yavaş ilerliyor ve 60 adımda f ≈ 10⁻⁴ düzeyine iniyor. Momentum aynı öğrenme oranında daha hızlı yön değiştiriyor ama dik yönde salınıyor; 60 adımda kayıp daha yüksek kalıyor. Bu, momentumun her zaman hız kazandırmadığını, öğrenme oranıyla birlikte ayarlanması gerektiğini gösteriyor. Adam'ın yörüngesi adım büyüklüğünü gradyan ölçeğinden bağımsız tuttuğu için düz eksende de dik eksende de benzer hızla ilerliyor.

Şekil 64.3, beş tohumun doğrulama eğrilerini ve son değerleri gösteriyor. Eğrilerin gölgeli bantları ortalamanın ± bir standart sapmasını gösterir.

![Şekil 64.3: Sol: optimizer başına doğrulama doğruluğu eğrileri (5 tohum, ortalama ± sapma). Sağ: son epoch doğrulama doğruluğu.](gorseller/b64_optim_egri.png)

Eğriler, SGD'nin yaklaşık 15. epoch'a kadar geride kaldığını gösteriyor. Adam ve AdamW'nin erken yakınsaması, uyarlamalı ölçeğin ilk adımlarda öğrenme oranını etkin biçimde yükseltmesinden gelir. Ama eğriler 25. epoch'tan sonra neredeyse düzleşiyor: bu veri kümesinde optimizer seçimi, doğru öğrenme oranıyla karşılaştırıldığında, nihai doğruluğu fazla değiştirmiyor. Büyük ve zor görev ve modellerde bu tablo farklı olabilir; bu yüzden bir optimizer'ı varsayılan olarak seçmek yerine her projede kendi ızgarasıyla karşılaştırmak gerekir.

## 64.5 Öğrenme oranı: en önemli hiperparametre ve zamanlayıcılar

Öğrenme oranı (η), eğitimin en hassas hiperparametresidir. Bu bölümdeki deneylerde de en büyük etkiyi o gösterdi: SGD ile 0,0001 kullanıldığında kayıp neredeyse hiç düşmedi (B vakası, 64.10'da), 2,0 kullanıldığında ise ağ tamamen çöktü. Bölüm 63'te gördüğümüz gibi, öğrenme oranı 2,0 iken 64 gizli birimden 63'ü ölüyordu; ReLU birimi bir kez negatif tarafa itilirse gradyanı sıfır olur ve bir daha öğrenmez.

Bu nedenle öğrenme oranını rastgele seçmek yerine ölçmek gerekir. Bunun bir yolu **LR aralık testi**dir (Smith, genel bilgi). Öğrenme oranını çok küçük bir değerden (10⁻⁷) çok büyük bir değere (10) doğru her adımda üstel olarak artırırsın ve kaybı izlersin. Kayıp başlangıçta yavaş düşer, sonra bir noktadan sonra hızla artar. Kaybın en hızlı düştüğü veya en düşük olduğu bölge, kullanılabilir öğrenme oranlarının üst sınırını verir; pratik öneri bu değerin 10 kat altıdır.

LR aralık testini yapan betik aşağıdadır. Öğrenme oranı her adımda çarpanla artırılır ve kayıp izlenir.

```python
# -*- coding: utf-8 -*-
"""Deney 3b: LR aralik testi (Smith, genel bilgi).

Ogrenme orani 1e-7'den 10'a kadar ustel olarak artirilir; her
adimda tek bir mini-batch (64 ornek) ile SGD (momentum 0,9)
guncellemesi yapilir. Kayip, 0,98 ustel ortalama ile yumusatilir
ve sapma duzeltmesi uygulanir. Tohum 0."""

import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import veri, mlp, csv_yaz
```
```python
# ---- (b) LR aralik testi: lr ustel artar, kayip izlenir
D = veri()
Xtr, ytr = D[0], D[1]
torch.manual_seed(0)
m = mlp()
opt = torch.optim.SGD(m.parameters(), lr=1e-7, momentum=0.9)
ADIM_LR = 300
lr_min, lr_max = 1e-7, 10.0
g = torch.Generator().manual_seed(0)
ema, en_iyi = None, 1e9
satir = []
for k in range(ADIM_LR):
    lr = lr_min * (lr_max / lr_min) ** (k / (ADIM_LR - 1))
    for pg in opt.param_groups:
        pg["lr"] = lr
    idx = torch.randperm(len(Xtr), generator=g)[:64]
    opt.zero_grad()
    loss = F.cross_entropy(m(Xtr[idx]), ytr[idx])
    loss.backward()
    opt.step()
    L = loss.item()
    ema = L if ema is None else 0.98 * ema + 0.02 * L
    ema_duz = ema / (1 - 0.98 ** (k + 1))  # sapma duzeltmesi
    en_iyi = min(en_iyi, ema_duz)
    satir.append((k, "%.4e" % lr, "%.5f" % L, "%.5f" % ema_duz))
    if ema_duz > 4 * en_iyi and k > 10:
        break
csv_yaz(
    "b64_lr_aralik.csv", satir, ["adim", "lr", "kayip", "kayip_ema"]
)
kayit = np.array([float(r[3]) for r in satir])
lrs = np.array([float(r[1]) for r in satir])
kmin = int(np.argmin(kayit))
print("LR aralik testi: adim sayisi=%d" % len(satir))
print(
    "  en dusuk EMA kayip: lr=%.3e  kayip=%.4f"
    % (lrs[kmin], kayit[kmin])
)
print("  onerilen (en dusuk / 10): lr=%.3e" % (lrs[kmin] / 10))
print("  son adimlarda lr=%.3e kayip=%.4f" % (lrs[-1], kayit[-1]))
```
```term
$ python t03b_lr_aralik.py
LR aralik testi: adim sayisi=264
  en dusuk EMA kayip: lr=6.649e-01  kayip=1.5565
  onerilen (en dusuk / 10): lr=6.649e-02
  son adimlarda lr=1.088e+00 kayip=42.6557
```

Aşağıdaki deney, 0,9 momentumlu SGD ile batch 64 kullanarak 264 adımlık bir aralık taraması yaptı. Öğrenme oranı 10⁻⁷'den 10'a kadar her adımda çarpanla artırıldı. Taramanın özeti: en düşük düzeltilmiş EMA kaybı lr = 0,665 (kayıp 1,5565) noktasında görüldü; önerilen değer 0,0665'tir. Son adımlarda lr ≈ 1,09 iken kayıp 42,7'ye çıktı. Bu tek koşuda en düşük kayıp 0,66 civarında görüldü ve öneri 0,066 oldu. Bu değer, 0,9 momentumlu SGD için makul bir aralıktadır; ama tek bir koşu gürültülüdür, çünkü her öğrenme oranı yalnızca bir mini-batch ile denenir. Bu yüzden öneriyi bir başlangıç noktası olarak kullan ve kısa bir ızgara ile doğrula. Şekil 64.4, taramadaki EMA kaybını ve önerilen değeri gösteriyor.

![Şekil 64.4: LR aralık testi: öğrenme oranına karşı düzeltilmiş EMA kaybı. En düşük nokta ile önerilen değer (÷10) işaretlendi.](gorseller/b64_lr_aralik.png)

**Zamanlayıcılar (schedules).** Sabit bir öğrenme oranı eğitimin başında büyük adım atıp sonda gürültü yapmak zorunda kalır. Bu yüzden eğitim boyunca öğrenme oranını değiştiririz. En yaygın üç takvim şunlardır. **Basamaklı (step)** takvim, belirli aralıklarla öğrenme oranını bir katsayıyla çarpar. **Üstel (exponential)** takvim, her adımda sabit bir oranla küçültür. **Kosinüs (cosine)** takvim, öğrenme oranını bir kosinüs eğrisiyle maksimumdan minimuma indirir:

η(t) = η_min + ½(η_max − η_min)(1 + cos(πt/T))

Kosinüs takvimi, başta ve sonda yavaş, ortada hızlı değişir. Bu, eğitimin başında geniş bir alanı tarayıp sonda dar bir çukurun dibine inmeye karşılık gelir. Aşağıdaki kod üç takvimi ve ısınma (warmup) ile kosinüsü tanımlar:

```python
def lr_adim_kurali(t, lr0, gamma=0.5, adim=100):
    """Her 'adim' adimda lr'yi gamma ile carpar (basamakli)."""
    return lr0 * gamma ** (t // adim)


def lr_ustel(t, lr0, gamma=0.99):
    return lr0 * gamma**t


def lr_kosinus(t, T, lr_max, lr_min=0.0):
    """Kosinus: t=0'da lr_max, t=T'de lr_min."""
    return lr_min + 0.5 * (lr_max - lr_min) * (
        1 + math.cos(math.pi * min(t, T) / T)
    )


def lr_isinma_kosinus(t, W, T, lr_max, lr_min=0.0):
    """Once W adim dogrusal artis, sonra kosinus azalma."""
    if t < W:
        return lr_max * (t + 1) / W
    return lr_kosinus(t - W, T - W, lr_max, lr_min)
```

Bu fonksiyonlar PyTorch'un `StepLR`, `ExponentialLR` ve `CosineAnnealingLR` zamanlayıcılarıyla birebir eşleşti (en büyük fark 5 × 10⁻¹⁸). Isınma ve kosinüsü birleştiren `lr_isinma_kosinus` ise bizim tanımımızdır; ilk W adımda öğrenme oranı 0'dan η_max'a doğrusal çıkar, sonra kosinüs başlar.

Takvim şekillerini, takvim karşılaştırmasını ve derin ağ deneyini üreten betik aşağıdadır. İlk bölüm 300 adımlık takvim dizilerini yazar ve kosinüs takvimini PyTorch ile karşılaştırır; ikinci bölüm MLP üzerinde üç takvimi beş tohumla eğitir; üçüncü bölüm 12 katmanlı ağda ısınmanın etkisini ölçer.

```python
# -*- coding: utf-8 -*-
"""Deney 4: ogrenme orani takvimleri ve isinmanin (warmup) etkisi."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from egitim_np import (
    lr_adim_kurali,
    lr_ustel,
    lr_kosinus,
    lr_isinma_kosinus,
)
from ortak64 import veri, mlp, egit, csv_yaz, SEEDS, ortalama_sapma

T = 300
# (a) Takvim sekilleri (2x2 sekil icin)
satir = []
for t in range(T):
    satir.append(
        (
            t,
            "%.6f" % 0.01,
            "%.6f" % lr_adim_kurali(t, 0.01, 0.5, 100),
            "%.6f" % lr_ustel(t, 0.01, 0.993),
            "%.6f" % lr_kosinus(t, T, 0.01, 0.0),
            "%.6f" % lr_isinma_kosinus(t, 30, T, 0.01, 0.0),
        )
    )
csv_yaz(
    "b64_takvim.csv",
    satir,
    [
        "adim",
        "sabit",
        "basamak",
        "ustel",
        "kosinus",
        "isinma_kosinus",
    ],
)
```
```python
# Torch karsilastirmasi (kosinus): sayisal farki yazdir
w = nn.Parameter(torch.zeros(1))
opt = torch.optim.SGD([w], lr=0.01)
sch = torch.optim.lr_scheduler.CosineAnnealingLR(
    opt, T_max=T, eta_min=0.0
)
tor = []
for t in range(T):
    tor.append(opt.param_groups[0]["lr"])
    opt.step()
    sch.step()
mine = [lr_kosinus(t, T, 0.01, 0.0) for t in range(T)]
print(
    "Kosinus: torch ile max fark = %.2e"
    % np.max(np.abs(np.array(tor) - mine))
)
print(
    "Isinma adim 0,29,30: %.6f %.6f %.6f"
    % (
        lr_isinma_kosinus(0, 30, T, 0.01),
        lr_isinma_kosinus(29, 30, T, 0.01),
        lr_isinma_kosinus(30, 30, T, 0.01),
    )
)
```
```python
# (b) Sig MLP, Adam, 30 epoch, 5 tohum: takvim karsilastirmasi
D = veri()
ADIM_TOP = 30 * int(np.ceil(len(D[0]) / 32))
TAKVIM = {
    "sabit": lambda t: 1e-3,
    "kosinus": lambda t: lr_kosinus(t, ADIM_TOP, 3e-3, 0.0),
    "isinma+kosinus": lambda t: lr_isinma_kosinus(
        t, 100, ADIM_TOP, 3e-3, 0.0
    ),
}
satir = []
for ad, fn in TAKVIM.items():
    tes = []
    for s in SEEDS:
        torch.manual_seed(s)
        m = mlp()
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        h = egit(m, opt, D, epochs=30, batch=32, seed=s, lr_fn=fn)
        tes.append(h["test_acc"])
    mu, sd = ortalama_sapma(tes)
    print("MLP %-15s test = %.4f +- %.4f" % (ad, mu, sd))
    satir.append((ad, "%.4f" % mu, "%.4f" % sd))
csv_yaz(
    "b64_takvim_test.csv", satir, ["takvim", "test_ort", "test_sd"]
)
```
```python
# (c) Derin ag (12 katman, BN yok), Adam lr=1e-2: isinmanin kararlilik
def derin_ag():
    kat, d = [], 64
    for _ in range(12):
        kat += [nn.Linear(d, 128), nn.ReLU()]
        d = 128
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)
```
```python
satir = []
print("\nDerin ag (12 katman), Adam lr=1e-2, 10 epoch (~340 adim):")
for ad, W in [("isinmasiz", 0), ("isinma 200 adim", 200)]:
    kayiplar = []
    for s in SEEDS:
        torch.manual_seed(s)
        m = derin_ag()
        opt = torch.optim.Adam(m.parameters(), lr=1e-2)
        if W == 0:
            fn = lambda t: 1e-2
        else:
            fn = lambda t, W=W: lr_isinma_kosinus(
                t, W, 2000, 1e-2, 1e-4
            )
        h = egit(m, opt, D, epochs=10, batch=32, seed=s, lr_fn=fn)
        kayiplar.append(
            (max(h["tr"][:3]), h["tr"][-1], h["test_acc"])
        )
    arr = np.array(kayiplar)
    print(
        "  %-16s tepe=%.3f son=%.3f test=%.3f"
        % (ad, arr[:, 0].mean(), arr[:, 1].mean(), arr[:, 2].mean())
    )
    satir.append(
        (
            ad,
            "%.4f" % arr[:, 0].mean(),
            "%.4f" % arr[:, 1].mean(),
            "%.4f" % arr[:, 2].mean(),
        )
    )
csv_yaz(
    "b64_isinma_derin.csv",
    satir,
    ["mod", "ilk3_tepe", "son_egitim_kayip", "test"],
)
```
```term
$ python t04_takvim.py
Kosinus: torch ile max fark = 5.20e-18
Isinma adim 0,29,30: 0.000333 0.010000 0.010000
MLP sabit           test = 0.9728 +- 0.0046
MLP kosinus         test = 0.9761 +- 0.0015
MLP isinma+kosinus  test = 0.9767 +- 0.0015

Derin ag (12 katman), Adam lr=1e-2, 10 epoch (~340 adim):
  isinmasiz        tepe=2.309 son=1.669 test=0.346
  isinma 200 adim  tepe=2.305 son=1.207 test=0.452
```

Şekil 64.5 sol üstte dört takvimi, sağ üstte üç takvimle eğitilmiş MLP'nin test doğruluğunu gösteriyor. Sağ altta ise bir derin ağın ısınma ile ve ısınmadan eğitim kaybını görüyorsun.

![Şekil 64.5: Sol üst: takvim şekilleri (η_max = 0,01, 300 adım). Sağ üst: MLP, Adam, test doğruluğu (5 tohum). Sol alt: 12 katmanlı ağda ısınmanın ilk üç epoch tepe kaybı ve son kayba etkisi. Sağ alt: okuma notu.](gorseller/b64_takvimler.png)

MLP deneyinde sabit öğrenme oranı (10⁻³) 0,9728 ± 0,0046, kosinüs (η_max = 0,003) 0,9761 ± 0,0015 ve ısınma + kosinüs 0,9767 ± 0,0015 test doğruluğu verdi. Fark küçük ama sapmalara göre tutarlı: takvim, sabit öğrenme oranından yaklaşık 0,3 ile 0,4 puan iyi, ama bu veri kümesinde kazanç kendi başına büyük değil.

**Neden ısınma (warmup)?** Derin ve büyük ağlarda, eğitimin ilk adımlarında Adam'ın ikinci moment tahmini v̂ henüz güvenilir değildir; sadece birkaç gradyan karesinin ortalamasıdır. Bu durumda büyük bir öğrenme oranı, tahmin dengelenmeden büyük adımlar atar ve ağı kararsız bir bölgeye iter. Isınma, ilk adımlarda öğrenme oranını küçük tutarak tahminin oturmasına izin verir. Bölüm 50'de gördüğümüz gibi, büyük modellerde kararlılık sınırı daha dardır; bu yüzden ısınma neredeyse standart bir bileşen hâline gelmiştir.

Derin ağ deneyinde bu etki açıkça görülüyor. 12 gizli katmanlı, BatchNorm'suz bir ReLU ağını Adam ile η = 0,01 kullanarak 10 epoch (yaklaşık 340 adım) eğittik. Isınma kullanılmadığında ilk üç epoch'un en yüksek kaybı 2,309 oldu (ağ öğrenmeye hiç başlayamadı), son eğitim kaybı 1,669 ve test doğruluğu 0,346 kaldı. 200 adımlık ısınma ile son eğitim kaybı 1,207 ve test 0,452 oldu. Her iki koşu da zayıf: bu ağ için η = 0,01 zaten büyük. Ama karşılaştırma yönü açık: ısınma, aynı öğrenme oranında daha kararlı bir başlangıç sağlar.

## 64.6 Başlatma (initialization): sinyal derin ağda nerede kayboluyor?

Bölüm 63'te ağırlıkların rastgele ama uygun ölçekte başlatılması gerektiğini ve bunun için Xavier ve He başlatma sezgisini gördük. Burada aynı fikri derin bir ağda ölçüyoruz. Ağ 20 gizli katmandan oluşuyor (her biri 256 birim, ReLU). Girdi olarak 512 eğitim örneği kullandık ve her katmanın aktivasyonlarının standart sapmasını (ileri geçiş) ve ağırlık gradyanlarının normunu (geri geçiş) ölçtük.

Başlatma deneyini yapan betik aşağıdadır. İlk bölüm, her katmanın aktivasyon standart sapmasını ve ağırlık gradyan normunu ölçer; ikinci bölüm dört başlatma yöntemini 20 epoch eğitir.

```python
# -*- coding: utf-8 -*-
"""Deney 5: derin agda baslatma (init) ve BatchNorm'un etkisi.

20 gizli katman (256 birim, ReLU). Her katman icin ileri geçişte
aktivasyon standart sapmasi ve geri geçişte agirlik gradyani normu
olculur. Olcum tek bir 512 orneklik batch uzerinde (tohum 0)."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, egit, csv_yaz, SEEDS, ortalama_sapma

D = veri()
Xtr, ytr = D[0], D[1]
X = Xtr[:512]
Y = ytr[:512]
DERIN = 20
```
```python
def ag(init, bn):
    kat, d = [], 64
    lin_list = []
    for k in range(DERIN):
        L = nn.Linear(d, 256)
        lin_list.append(L)
        kat.append(L)
        if bn:
            kat.append(nn.BatchNorm1d(256))
        kat.append(nn.ReLU())
        d = 256
    L = nn.Linear(d, 10)
    lin_list.append(L)
    kat.append(L)
    model = nn.Sequential(*kat)
    for L in lin_list:
        if init == "kucuk":
            nn.init.normal_(L.weight, std=0.01)
        elif init == "xavier":
            nn.init.xavier_normal_(L.weight)
        elif init == "he":
            nn.init.kaiming_normal_(L.weight, nonlinearity="relu")
        nn.init.zeros_(L.bias)
    return model, lin_list
```
```python
def olc(init, bn, seed=0):
    torch.manual_seed(seed)
    model, lins = ag(init, bn)
    model.train()
    act = []
    h = X
    for mod in model:
        h = mod(h)
        if isinstance(mod, nn.ReLU):
            act.append(h.std().item())
    model.zero_grad()
    F.cross_entropy(model(X), Y).backward()
    gn = [L.weight.grad.norm().item() for L in lins]
    return act, gn
```
```python
satir = []
print("Katman 1 / 10 / 20 icin aktivasyon std ve gradyan normu:")
for init in ["kucuk", "xavier", "he"]:
    for bn in [False, True]:
        act, gn = olc(init, bn)
        ad = "%s%s" % (init, "+BN" if bn else "")
        for k in range(DERIN):
            a = act[k] if k < len(act) else float("nan")
            satir.append((ad, k + 1, "%.6e" % a, "%.6e" % gn[k]))
        print(
            "  %-10s act: %.2e %.2e %.2e"
            % (ad, act[0], act[9], act[19])
        )
        print(
            "  %-10s grad W1=%.2e W10=%.2e W20=%.2e cikis=%.2e"
            % (ad, gn[0], gn[9], gn[19], gn[-1])
        )
csv_yaz(
    "b64_baslatma.csv",
    satir,
    ["init", "katman", "aktivasyon_std", "gradyan_norm"],
)

# Egitim: 20 katman, SGD lr=0.05, 20 epoch, 3 tohum, test dogrulugu
```
```python
print("\nEgitim (20 katman, SGD lr=0.05, 20 epoch, 3 tohum):")
satir = []
for init, bn in [
    ("kucuk", False),
    ("xavier", False),
    ("he", False),
    ("he", True),
]:
    tes = []
    for s in SEEDS[:3]:
        torch.manual_seed(s)
        model, _ = ag(init, bn)
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        h = egit(model, opt, D, epochs=20, batch=32, seed=s)
        tes.append(h["test_acc"])
    mu, sd = ortalama_sapma(tes)
    ad = "%s%s" % (init, "+BN" if bn else "")
    print("  %-10s test = %.4f +- %.4f" % (ad, mu, sd))
    satir.append((ad, "%.4f" % mu, "%.4f" % sd))
csv_yaz(
    "b64_baslatma_egitim.csv", satir, ["init", "test_ort", "test_sd"]
)
```
```term
$ python t05_baslatma.py
Katman 1 / 10 / 20 icin aktivasyon std ve gradyan normu:
  kucuk      act: 2.37e-02 1.00e-10 5.14e-20
  kucuk      grad W1=5.01e-20 W10=4.92e-20 W20=4.94e-20 cikis=4.71e-20
  kucuk+BN   act: 5.71e-01 5.94e-01 5.99e-01
  kucuk+BN   grad W1=1.81e+01 W10=2.93e+00 W20=5.07e-01 cikis=4.89e-01
  xavier     act: 1.88e-01 1.15e-02 5.38e-04
  xavier     grad W1=5.75e-04 W10=7.14e-04 W20=7.16e-04 cikis=4.92e-04
  xavier+BN  act: 5.78e-01 5.95e-01 5.99e-01
  xavier+BN  grad W1=2.03e+01 W10=4.26e+00 W20=8.49e-01 cikis=1.49e+00
  he         act: 4.20e-01 5.84e-01 8.71e-01
  he         grad W1=1.94e+00 W10=7.41e+00 W20=8.40e+00 cikis=9.54e+00
  he+BN      act: 5.78e-01 5.95e-01 5.99e-01
  he+BN      grad W1=9.32e+00 W10=3.08e+00 W20=6.13e-01 cikis=1.51e+00

Egitim (20 katman, SGD lr=0.05, 20 epoch, 3 tohum):
  kucuk      test = 0.1028 +- 0.0000
  xavier     test = 0.3306 +- 0.1302
  he         test = 0.7426 +- 0.1998
  he+BN      test = 0.9648 +- 0.0042
```

Dört başlatma biçimi karşılaştırıldı: küçük sabit std (0,01), Xavier (Glorot) normal, He normal ve He + BatchNorm. Aşağıdaki tablo üç katmandaki değerleri veriyor:

| Başlatma | Aktivasyon std (1. / 10. / 20. katman) | Gradyan normu (W1 / W20) |
|---|---|---|
| Küçük (0,01) | 2,4 × 10⁻² / 1,0 × 10⁻¹⁰ / 5,1 × 10⁻²⁰ | 5,0 × 10⁻²⁰ / 4,9 × 10⁻²⁰ |
| Xavier | 1,9 × 10⁻¹ / 1,2 × 10⁻² / 5,4 × 10⁻⁴ | 5,8 × 10⁻⁴ / 7,2 × 10⁻⁴ |
| He | 4,2 × 10⁻¹ / 5,8 × 10⁻¹ / 8,7 × 10⁻¹ | 1,9 / 8,4 |
| He + BN | 5,8 × 10⁻¹ / 5,9 × 10⁻¹ / 6,0 × 10⁻¹ | 9,3 / 0,61 |

Tablo açık bir hikâye anlatıyor. Küçük sabit başlatmada sinyal katmanlar boyunca ortalama her katmanda yaklaşık 8 kat küçülüyor ve 20. katmanda 10⁻²⁰ düzeyine düşüyor. Gradyan da aynı şekilde sönüyor: ilk katmanın gradyanı 10⁻²⁰, yani hiçbir öğrenme olmaz. Bu, Bölüm 55'te gördüğümüz kaybolan gradyanın en saf biçimi: çarpanların her biri 1'den küçük olduğu için zincirin uzunluğu sinyali yok eder. Xavier, ReLU için tasarlanmadığından sinyali daha yavaş sönümlendiriyor; 20 katmanda 5 × 10⁻⁴'e düşüyor. He başlatma ise ReLU'nun yarısını sıfırlamasını hesaba katar (Bölüm 63'teki sezgi) ve aktivasyon düzeyini katmanlar boyunca korur. Tabloda He'nin std değerleri yaklaşık 0,4'ten 0,9'a çıkıyor; bu, girdinin ölçeğiyle ve ilk katmandaki sapma etkisiyle birlikte olan kabaca dengeli bir artıştır.

Eğitim sonuçları aynı hikâyeyi destekliyor. Aynı 20 katmanlı ağ, SGD (η = 0,05), 20 epoch ve üç tohumla eğitildiğinde test doğrulukları şöyle oldu:

| Başlatma | Test doğruluğu |
|---|---|
| Küçük (0,01) | 0,1028 ± 0,0000 |
| Xavier | 0,3306 ± 0,1302 |
| He | 0,7426 ± 0,1998 |
| He + BN | 0,9648 ± 0,0042 |

Küçük başlatma ağı hiç öğrenemedi (şans düzeyi 0,10). He tek başına tutarsızdı (üç tohum arasındaki sapma 0,20 idi). BatchNorm ile birleşince tutarlı biçimde 0,96'ya çıktı. Bu, başlatmanın gerekli ama tek başına yeterli olmadığını gösterir: derin ağda normalizasyon, sinyal ölçeğini her katmanda yeniden ayarlayarak başlatmanın etkisini sürdürür. Bunu bir sonraki bölümde BatchNorm ile ayrıntılı göreceğiz.

Şekil 64.6, aynı başlatma deneyinin katman katman değerlerini gösteriyor. Sol panelde aktivasyon standart sapması, sağ panelde ağırlık gradyanı normu logaritmik ölçekte çizildi.

![Şekil 64.6: 20 katmanlı ağda başlatma ve BatchNorm'un etkisi. Sol: ileri geçişte aktivasyon std. Sağ: geri geçişte ağırlık gradyanı normu.](gorseller/b64_baslatma.png)

Şekil 64.6'da bir ayrıntı dikkat çekicidir: He başlatmada gradyan normu, ilk katmandan son katmana doğru artıyor (1,9'dan 8,4'e). Bu tam bir "dengeli" durum değildir; ama patlama da değildir. BatchNorm ile birlikte gradyan normları ilk katmanda daha büyük ve son katmanda daha küçük hâle gelir. Yani normalizasyon, katmanlar arası gradyan ölçeğini de değiştirir. Öğrenme oranını seçerken bu farkı akılda tutmak gerekir: ilk katmanın öğrenme hızı ile son katmanınki aynı olmak zorunda değildir.

## 64.7 Normalizasyon: BatchNorm, LayerNorm ve GroupNorm

Normalizasyon, bir katmanın çıktısını (ya da girdisini) yeniden ölçekleyerek dağılımını sabit tutma fikridir. Derin ağlarda her katmanın girdisinin dağılımı, önceki katmanların ağırlıkları değiştikçe kayar. Bu olguya **iç kovaryans kayması** denir ve eski tanımıyla BatchNorm'un ilk gerekçesiydi. Güncel açıklama daha çok kayıp yüzeyinin pürüzlülüğünü azaltmasıdır: normalizasyon, optimizasyonun daha geniş ve daha düzgün bir yüzeyde ilerlemesini sağlar. Hangi açıklama doğru olursa olsun, pratik etki ölçülebilir ve büyüktür.

**Batch normalizasyon (BatchNorm)**, bir mini-batch içinde her özellik (her sütun) için ortalama ve varyansı hesaplar. Eğitim modunda girdi, bu batch istatistikleriyle normalize edilir ve öğrenilebilir iki parametreyle ölçeklenir ve kaydırılır:

μ = (1/N) Σᵢ xᵢ,    σ² = (1/N) Σᵢ (xᵢ − μ)²
x̂ᵢ = (xᵢ − μ) / √(σ² + ε)
yᵢ = γ x̂ᵢ + β

γ ve β, ağın öğrendiği parametrelerdir. Normalizasyon sonrası dağılımın her zaman sıfır ortalama ve birim varyanslı olmasını zorunlu kılmazlar; eğer ağ gerekli görürse bu dağılımı geri kaydırabilir. Şekil 64.7'nin sol paneli bu veri akışını gösteriyor.

Eğitimde BatchNorm'un en önemli yönü geri geçişidir. Çıktıya bağlı kayıp gradyanı dy verildiğinde, girdi gradyanı dx batch'teki tüm örneklere bağlıdır. Türetmenin sonucu şudur:

dγ = Σᵢ dyᵢ x̂ᵢ,    dβ = Σᵢ dyᵢ
dx = (γ / (N σ)) · (N dyᵢ − Σⱼ dyⱼ − x̂ᵢ Σⱼ dyⱼ x̂ⱼ)

Bu formülün önemli bir sonucu, dx'in batch içinde toplamının sıfır olmasıdır: BatchNorm, batch ortalamasının kaymasına karşı gradyanı da düzeltir. Aşağıdaki kod ileri ve geri geçişi tanımlar:

```python
def bn_ileri(x, gamma, beta, eps=1e-5):
    """Egitim modu: mini-batch istatistikleri kullanilir.
    x: (N, D). Doner: y, onbellek (geri gecis icin), mu, var."""
    mu = x.mean(axis=0)
    var = x.var(axis=0)  # bolen N (yanli tahmin)
    xh = (x - mu) / np.sqrt(var + eps)
    y = gamma * xh + beta
    return y, (xh, var, eps, gamma), mu, var


def bn_geri(dy, onbellek):
    """BatchNorm geri gecisi: dx, dgamma, dbeta."""
    xh, var, eps, gamma = onbellek
    n = dy.shape[0]
    dgamma = (dy * xh).sum(axis=0)
    dbeta = dy.sum(axis=0)
    dxh = dy * gamma
    inv = 1.0 / np.sqrt(var + eps)
    dx = (inv / n) * (
        n * dxh - dxh.sum(axis=0) - xh * (dxh * xh).sum(axis=0)
    )
    return dx, dgamma, dbeta
```

Çıkarım modu için BatchNorm fonksiyonu, eğitimde biriken hareketli ortalamaları kullanır:

```python
def bn_cikarim(x, gamma, beta, run_mu, run_var, eps=1e-5):
    """Degerlendirme modu: egitimde biriken hareketli ortalamalar."""
    return gamma * (x - run_mu) / np.sqrt(run_var + eps) + beta
```

Bu iki fonksiyonun doğruluğunu iki bağımsız yolla sınadık. İlk olarak PyTorch'un `nn.BatchNorm1d` katmanının ileri ve geri geçişiyle karşılaştırdık; fark 10⁻¹⁵ düzeyinde kaldı. İkinci olarak sayısal gradyanla (merkezi fark, h = 10⁻⁶) karşılaştırdık; en büyük fark 1,4 × 10⁻⁹. Bu iki kontrol, türetmenin ve kodun doğru olduğunu gösterir.

Aşağıdaki küçük örnek, dört sayılık bir batch üzerinde ileri ve geri geçişi gösterir. Girdi x = [1, 3, 5, 7], γ = 2, β = 1 seçildi.

```python
# -*- coding: utf-8 -*-
"""BatchNorm'un 4 orneklik batch uzerinde ileri ve geri gecisi."""

import numpy as np
from egitim_np import bn_ileri, bn_geri

x = np.array([[1.0], [3.0], [5.0], [7.0]])
gamma, beta = np.array([2.0]), np.array([1.0])
y, cache, mu, var = bn_ileri(x, gamma, beta)
print("mu = %.4f   sigma^2 = %.4f" % (mu[0], var[0]))
print("xhat =", np.round(cache[0].ravel(), 4))
print("y    =", np.round(y.ravel(), 4))
dy = np.array([[1.0], [0.0], [0.0], [0.0]])
dx, dgamma, dbeta = bn_geri(dy, cache)
print("dgamma = %.4f   dbeta = %.4f" % (dgamma[0], dbeta[0]))
print("dx =", np.round(dx.ravel(), 4))
print("sum(dx) = %.2e  (BN gradyani toplami sifirdir)" % dx.sum())
```

Program şu çıktıyı verir:

```term
$ python bn_ornek.py
mu = 4.0000   sigma^2 = 5.0000
xhat = [-1.3416 -0.4472  0.4472  1.3416]
y    = [-1.6833  0.1056  1.8944  3.6833]
dgamma = -1.3416   dbeta = 1.0000
dx = [ 0.2683 -0.3578 -0.0894  0.1789]
sum(dx) = 0.00e+00  (BN gradyani toplami sifirdir)
```

Çıktı, elle yapılan hesabı doğrular. Ortalama 4, yanlı varyans 5'tir (değerler 1, 3, 5, 7 için (9 + 1 + 1 + 9)/4). x̂ değerleri ±1,3416 ve ±0,4472'dir. γ = 2, β = 1 ile y = 2x̂ + 1 olur. Geri geçişte yalnızca ilk örneğe 1 gradyanı verildiğinde dβ = 1 ve dγ = x̂₁ = −1,3416 çıkar. dx'in toplamı sıfırdır; bu, BatchNorm'un sabit bir kaymaya karşı duyarsız olmasının bir sonucudur.

**Eğitim ve çıkarım modu.** Çıkarımda (tek bir örnek için tahmin yaparken) batch istatistiklerine güvenemeyiz: batch yoktur ya da bir örneklik batch ile istatistik anlamsızdır. Bu yüzden eğitim sırasında μ ve σ²'nin hareketli ortalamaları (μ_run, σ²_run) tutulur ve çıkarımda bunlar kullanılır. PyTorch'ta varsayılan momentum 0,1'dir: her eğitim adımında μ_run ← 0,9 μ_run + 0,1 μ. Bir ayrıntı dikkat gerektirir: PyTorch, `running_var`'ı Bessel düzeltmeli (N/(N−1)) varyansla günceller, ama normalizasyonun kendisinde yanlı varyans kullanır. Bu fark, batch büyüdükçe önemsizleşir; ama NumPy kodunda bunu kendi testinle sınamalısın (testimiz bu farkı doğruladı).

Bu ayrım, sık yapılan bir hatanın kaynağıdır. Eğer çıkarım yapmadan önce `model.eval()` çağrılmazsa, BatchNorm hâlâ batch istatistiklerini kullanır. Tek bir örnek için bu istatistikler anlamsızdır; büyük bir doğrulama batch'i için ise sonuç yalnızca az değişir. Bunu bölümün sonundaki tek-batch testinde ölçeceğiz.

BatchNorm'un el örneğini, batch deneyini ve eğitim–çıkarım farkını ölçen betik aşağıdadır.

```python
# -*- coding: utf-8 -*-
"""Deney 6: BatchNorm - el ornegi, batch boyutu,
egitim/cikarim farki."""

import numpy as np
import torch
import torch.nn as nn
from egitim_np import bn_ileri
from ortak64 import veri, egit, csv_yaz, SEEDS, ortalama_sapma

# (a) El ornegi: N=4, D=1, gamma=2, beta=1
x = np.array([[1.0], [3.0], [5.0], [7.0]])
y, _, mu, var = bn_ileri(x, np.array([2.0]), np.array([1.0]))
print("mu =", mu, " var (N'e bolunmus) =", var)
print("xhat =", np.round((x - mu) / np.sqrt(var + 1e-5), 4).ravel())
print("y    =", np.round(y, 4).ravel())
```
```python
# (b) Kucuk batch: BN'li MLP, egitim batch boyutu
D = veri()
satir = []
print("\nBN'li MLP (2 gizli katman), 20 epoch, 5 tohum:")
for b in [2, 8, 32, 128]:
    tes = []
    for s in SEEDS:
        torch.manual_seed(s)
        from ortak64 import mlp

        m = mlp(bn=True)
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        h = egit(m, opt, D, epochs=20, batch=b, seed=s)
        tes.append(h["test_acc"])
    mu_, sd = ortalama_sapma(tes)
    print("  batch=%4d  test = %.4f +- %.4f" % (b, mu_, sd))
    satir.append((b, "%.4f" % mu_, "%.4f" % sd))
csv_yaz("b64_bn_batch.csv", satir, ["batch", "test_ort", "test_sd"])

# (c) Egitim ve cikarim modu: BN istatistiklerinin farki
torch.manual_seed(0)
from ortak64 import mlp

m = mlp(bn=True)
opt = torch.optim.Adam(m.parameters(), lr=1e-3)
egit(m, opt, D, epochs=10, batch=32, seed=0)
Xva = D[2][:64]
m.eval()
with torch.no_grad():
    cik = m(Xva).argmax(1)
m.train()
with torch.no_grad():
    egt = m(Xva).argmax(1)  # yanlis: batch istatistikleri kullanilir
print(
    "\nAyni 64 dogrulama orneginde tahmin farki "
    "(eval vs train modu): "
    "%d / 64" % (cik != egt).sum().item()
)
```
```term
$ python t06_bn.py
mu = [4.]  var (N'e bolunmus) = [5.]
xhat = [-1.3416 -0.4472  0.4472  1.3416]
y    = [-1.6833  0.1056  1.8944  3.6833]

BN'li MLP (2 gizli katman), 20 epoch, 5 tohum:
  batch=   2  test = 0.8683 +- 0.0315
  batch=   8  test = 0.9811 +- 0.0093
  batch=  32  test = 0.9856 +- 0.0030
  batch= 128  test = 0.9833 +- 0.0056

Ayni 64 dogrulama orneginde tahmin farki (eval vs train modu): 2 / 64
```

**Küçük batch sorunu.** BatchNorm, batch istatistiklerinin güvenilir olmasını gerektirir. Küçük batch'te μ ve σ² gürültülüdür ve eğitim ile çıkarım arasında tutarsızlık büyür. Aşağıdaki deneyde, iki gizli katmanlı BatchNorm'lu bir MLP'yi farklı batch boyutlarıyla 20 epoch eğittik (beş tohum):

| Batch | Test doğruluğu (ortalama ± sapma) |
|---|---|
| 2 | 0,8683 ± 0,0315 |
| 8 | 0,9811 ± 0,0093 |
| 32 | 0,9856 ± 0,0030 |
| 128 | 0,9833 ± 0,0056 |

Batch 2'de model belirgin biçimde kötü ve daha kararsız. 8 ve üstünde ise BatchNorm sorunsuz çalışıyor. Bu nedenle, bellek sınırı yüzünden batch'i çok küçük tutmak zorunda kalırsan BatchNorm yerine GroupNorm ya da LayerNorm düşünmelisin. Aynı deneyde eğitim ve çıkarım modu arasındaki fark, 64 doğrulama örneğinde 2 tahminle ölçüldü; batch 32 ile eğitilmiş ağda bu fark 360 örnekte 0 çıktı, çünkü hareketli ortalamalar batch istatistiklerine yakındı. Fark, batch küçüldükçe ve veri dağılımı kaydıkça büyür.

**LayerNorm.** Transformer'larda (Bölüm 69) BatchNorm yerine LayerNorm kullanılır. LayerNorm, normalizasyonu batch yerine tek bir örneğin özellikleri üzerinden yapar: μ ve σ², bir örneğin D özelliği üzerinden hesaplanır. Bu, batch boyutundan bağımsızdır, eğitim ve çıkarım arasında fark yoktur ve dizi uzunluğu değişken olan modellerde uygundur. Dizi modellerinde her zaman aynı tüm batch'in istatistikleri anlamlı değildir; bu yüzden LayerNorm oradaki standarttır. Sadece bu noktada bir ayrım: LayerNorm'un formülü aynıdır, sadece ortalama ve varyans farklı eksende alınır.

**GroupNorm.** Özellikleri birkaç gruba bölüp her grup için normalizasyon yapar. Batch'ten bağımsızdır, küçük batch'te veya tek örnekle çalışır. Görüntü modellerinde (Bölüm 66) bellek sınırlı olduğunda tercih edilir. Bu bölümde yalnızca adını ve yerini bilmen yeterli; ayrıntıları ilgili bölümde göreceğiz.

Şekil 64.7, BatchNorm ve dropout'un veri akışını yan yana gösteriyor. Dropout'u aşağıda, düzenlileştirme bölümünde ele alıyoruz.

![Şekil 64.7: Sol: BatchNorm'un eğitim sırasındaki veri akışı ve hareketli ortalamaların rolü. Sağ: dropout'ta eğitim (maske ve ölçekleme) ile çıkarım (kimlik) farkı.](gorseller/b64_bn_dropout_sema.png)

## 64.8 Düzenlileştirme: dropout, ağırlık azaltma, etiket yumuşatma, erken durdurma

Bir ağ, eğitim verisini ezberleyebilecek kadar büyükse aşırı uydurur (Bölüm 57). Düzenlileştirme, ağın ezberlemesini zorlaştıran yöntemlerin genel adıdır. Bu bölümde dört temel yöntemi ölçtük.

**Dropout** (Srivastava ve diğerleri, 2014), eğitimde her ileri geçişte her aktivasyonu 1 − p olasılıkla tutar ve p olasılıkla sıfırlar. Kalan değerleri 1/(1 − p) ile ölçekleriz. Bu **ters ölçekleme** (inverted dropout) yöntemidir: eğitimde beklenen değer aynı kalır, böylece çıkarımda hiçbir değişiklik gerekmez. Çıkarımda dropout kapalıdır ve girdi olduğu gibi geçer. Dropout'un bir ensemble yorumu da vardır: her ileri geçiş, paylaşılan ağırlıklarla farklı bir alt ağı eğitir; çıkarım ise bu alt ağların kabaca ortalamasıdır (genel bilgi).

Aşağıdaki kod, dropout'un ileri geçişini tanımlar:

```python
def dropout_ileri(x, p, egitim, rng):
    """Egitimde her ogeyi 1-p olasilikla tutar, 1/(1-p) ile olceklar.
    Cikarimda hicbir sey yapmaz."""
    if not egitim or p == 0.0:
        return x, None
    maske = (rng.random(x.shape) >= p) / (1.0 - p)
    return x * maske, maske
```

Bu fonksiyon, PyTorch'un `F.dropout(..., training=True)` çıktısıyla aynı maske verildiğinde birebir eşleşti. Ters ölçeklemenin doğruluğunu ayrıca, 200 000 örnek üzerinde ortalamanın korunmasıyla kontrol ettik: E[y] ≈ E[x] (0,0047 ve 0,0039, ikisi de sıfıra yakın, çünkü girdi standart normal).

**Ağırlık azaltma (weight decay)** ağırlıkların büyüklüğünü kısıtlar. Adam'da bunu AdamW ile ayrık uyguladığımızı gördük (64.3). Düzenlileştirme etkisini ölçmek için AdamW'yi 0,1 ağırlık azaltmayla da test ettik.

**Etiket yumuşatma (label smoothing)**, hedef etiketi tek sıcak (one-hot) vektör yerine biraz yumuşatılmış bir dağılım olarak verir: ε = 0,1 için doğru sınıfın hedefi 0,9 + 0,01, diğer sınıfların her biri 0,01 olur. Bu, ağı aşırı kendinden emin olmaktan alıkoyar. Bölüm 57'de gördüğümüz **kalibrasyon** bu yüzden ilgi konusudur: model 0,99 güvenle tahmin ettiğinde, gerçekte bu tahminin doğru olma oranı 0,99 olmalıdır. Kalibrasyonu ölçmek için **beklenen kalibrasyon hatası (ECE)** kullanılır: tahminler güvenlik düzeyine göre 15 kutuya ayrılır ve her kutuda ortalama güven ile doğruluk arasındaki fark ağırlıklı olarak toplanır.

**Erken durdurma (early stopping)**, doğrulama kaybı artmaya başladığında eğitimi durdurur ya da en iyi noktayı geri yükler. Bu, eğitim sürecine uygulanmış bir düzenlileştirmedir (Bölüm 57'deki doğrulama uyarısını hatırla).

Düzenlileştirme deneyini yapan betik aşağıdadır. Her varyant için MLP, Adam ile 60 epoch eğitilir; eğitim doğruluğu eğitim kümesinde çıkarım modunda, test doğruluğu ve ECE test kümesinde ölçülür.

```python
# -*- coding: utf-8 -*-
"""Deney 7: dropout, agirlik azaltma, etiket yumusatma,
erken durdurma.

Her varyant 5 tohumla. 'Egitim dogrulugu' egitim kumesinde (cikarim
modu) olculur; test sonucu ayri, hic secimde kullanilmamis kumedendir.
"""

import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import (
    veri,
    mlp,
    egit,
    olc,
    csv_yaz,
    SEEDS,
    ortalama_sapma,
)


def ece(model, X, y, kutu=15):
    """Beklenen kalibrasyon hatasi (ECE): guven ile dogruluk farki."""
    model.eval()
    with torch.no_grad():
        p = F.softmax(model(X), dim=1)
    guven, tahmin = p.max(1)
    dogru = (tahmin == y).float()
    e = 0.0
    for b in range(kutu):
        lo, hi = b / kutu, (b + 1) / kutu
        m = (guven > lo) & (guven <= hi)
        if m.any():
            e += m.float().mean().item() * abs(
                dogru[m].mean().item() - guven[m].mean().item()
            )
    return e
```
```python
D = veri()
VARYANT = {
    "temel (dropout 0, wd 0)": dict(dropout=0.0, wd=0.0, ls=0.0),
    "dropout 0.2": dict(dropout=0.2, wd=0.0, ls=0.0),
    "dropout 0.5": dict(dropout=0.5, wd=0.0, ls=0.0),
    "AdamW wd=0.1": dict(dropout=0.0, wd=0.1, ls=0.0),
    "etiket yumusatma 0.1": dict(dropout=0.0, wd=0.0, ls=0.1),
}
```
```python
satir = []
print("256x2 MLP, Adam lr=1e-3, batch 32, 60 epoch, 5 tohum")
print("(test kumesi: 360 ornek; egitim dogrulugu: cikarim modu)\n")
```
```python
for ad, c in VARYANT.items():
    tr_acc, te_acc, ec, en_iyi = [], [], [], []
    for s in SEEDS:
        torch.manual_seed(s)
        m = mlp(gizli=256, dropout=c["dropout"])
        if c["wd"] > 0:
            opt = torch.optim.AdamW(
                m.parameters(), lr=1e-3, weight_decay=c["wd"]
            )
        else:
            opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        h = egit(m, opt, D, epochs=60, batch=32, seed=s, ls=c["ls"])
        m.eval()
        with torch.no_grad():
            tr_acc.append(
                (m(D[0]).argmax(1) == D[1]).float().mean().item()
            )
        te_acc.append(h["test_acc"])
        ec.append(ece(m, D[4], D[5]))
        en_iyi.append(h["en_iyi_ep"])
    a, sa = ortalama_sapma(tr_acc)
    b, sb = ortalama_sapma(te_acc)
    e, se = ortalama_sapma(ec)
    print("%-24s egitim=%.4f+-%.4f" % (ad, a, sa))
    print("%24s test=%.4f+-%.4f ECE=%.4f+-%.4f" % ("", b, sb, e, se))
    print("%24s en iyi ep (val)=%s" % ("", en_iyi))
    satir.append(
        (
            ad,
            "%.4f" % a,
            "%.4f" % b,
            "%.4f" % sb,
            "%.4f" % e,
            "%.4f" % se,
        )
    )
csv_yaz(
    "b64_duzenlilestirme.csv",
    satir,
    [
        "varyant",
        "egitim_acc",
        "test_ort",
        "test_sd",
        "ece_ort",
        "ece_sd",
    ],
)
```
```term
$ python t07_duzenlilestirme.py
256x2 MLP, Adam lr=1e-3, batch 32, 60 epoch, 5 tohum
(test kumesi: 360 ornek; egitim dogrulugu: cikarim modu)

temel (dropout 0, wd 0)  egitim=1.0000+-0.0000
                         test=0.9733+-0.0025 ECE=0.0195+-0.0030
                         en iyi ep (val)=[45, 57, 59, 48, 43]
dropout 0.2              egitim=0.9998+-0.0004
                         test=0.9756+-0.0023 ECE=0.0164+-0.0011
                         en iyi ep (val)=[33, 55, 51, 59, 53]
dropout 0.5              egitim=1.0000+-0.0000
                         test=0.9783+-0.0023 ECE=0.0152+-0.0021
                         en iyi ep (val)=[45, 57, 59, 59, 43]
AdamW wd=0.1             egitim=1.0000+-0.0000
                         test=0.9722+-0.0020 ECE=0.0167+-0.0027
                         en iyi ep (val)=[57, 56, 53, 48, 54]
etiket yumusatma 0.1     egitim=1.0000+-0.0000
                         test=0.9878+-0.0032 ECE=0.1136+-0.0053
                         en iyi ep (val)=[55, 45, 44, 57, 55]
```

Aşağıdaki deney, 256 gizli birimli iki katmanlı MLP'yi Adam (η = 0,001) ile 60 epoch, beş tohumla eğitti. "Eğitim doğruluğu" eğitim kümesi üzerinde çıkarım modunda ölçüldü; test kümesi ise yalnızca raporlama için kullanıldı.

| Varyant | Eğitim doğruluğu | Test doğruluğu | ECE (test) |
|---|---|---|---|
| Temel | 1,0000 | 0,9733 ± 0,0025 | 0,0195 ± 0,0030 |
| Dropout 0,2 | 0,9998 | 0,9756 ± 0,0023 | 0,0164 ± 0,0011 |
| Dropout 0,5 | 1,0000 | 0,9783 ± 0,0023 | 0,0152 ± 0,0021 |
| AdamW wd = 0,1 | 1,0000 | 0,9722 ± 0,0020 | 0,0167 ± 0,0027 |
| Etiket yumuşatma 0,1 | 1,0000 | 0,9878 ± 0,0032 | 0,1136 ± 0,0053 |

Sonuçlar üç açıdan öğretici. Birincisi, temel model eğitim kümesini tamamen ezberledi (eğitim doğruluğu 1,0000) ama test 0,973'te kaldı: bu, aşırı uydurmanın tipik bir görünümüdür. İkincisi, dropout 0,5 test doğruluğunu 0,978'e çıkardı ve ECE'yi düşürdü; ağırlık azaltma ise bu veri kümesinde anlamlı bir etki yapmadı. Üçüncüsü ve en şaşırtıcı olanı: etiket yumuşatma test doğruluğunu en yüksek seviyeye (0,9878) çıkardı ama ECE'yi 0,11'e yükseltti. Yani model daha doğru tahmin etti, ama güvenini gerçek doğruluğun altına çekti: olası bir açıklama, yumuşatılmış hedeflerin en kolay örnekler için bile güveni yaklaşık 0,9'da tutmasıdır (bu açıklamayı ayrıca sınamadık). Bu, etiket yumuşatmanın kalibrasyonu her zaman iyileştirmediğini gösterir. Kalibrasyon hedefin için önemliyse, yumuşatma seçimini ECE ile birlikte değerlendirmelisin; yalnızca doğruluğa bakmak yetmez.

Erken durdurma bu tabloda ayrı bir sütun değil, ama koşuların en iyi doğrulama epoch'ları bilgi veriyor: temel ve dropout 0,5 varyantlarında en iyi epoch'lar 43 ile 59 arasında. Birçok koşuda en iyi nokta son epoch'lara denk geliyor; yani 60 epoch bu koşularda eğitimi sınırlıyor olabilir. Her projede erken durdurma için doğrulama kaybını bir sabırla (patience) izlemek standart bir uygulamadır.

**Veri artırma (data augmentation)**, eğitim örneklerini döndürerek, kaydırarak veya gürültü ekleyerek çoğaltır. Görüntü modellerinde en güçlü düzenlileştirmelerden biridir. Bu bölümde denemedik; Bölüm 66'da CNN ile birlikte ele alacağız.

**Çift iniş (double descent)** (genel bilgi): modelin kapasitesi arttıkça test hatası önce artıp sonra yeniden düşebilir. Bu, klasik bias-variance eğrisinin tek bir U şekli olmadığını gösterir. Bunu bu bölümde ölçmedik; yalnızca bilmen gereken bir olgu olarak not ediyoruz. Büyük modellerde ezberleme ve genelleme arasındaki ilişki, klasik sezgiden farklı olabilir.

## 64.9 Gradyan sorunları: kırpma ve artık bağlantılar

Kaybolan gradyanı (Bölüm 55) ve başlatmayı (64.6) gördük. Diğer uç, **patlayan gradyan**dır: gradyan normu zincirin çarpanları büyük olduğu için kontrolsüz büyür ve tek bir adımda ağırlıkları yok edecek kadar büyük bir güncelleme yapar. Yaygın çözüm **gradyan kırpmadır** (gradient clipping): tüm parametrelerin gradyanlarının birleşik L2 normu bir eşiği (max_norm) aşarsa, bütün gradyanlar aynı oranda küçültülür. Yön korunur, yalnızca boy kısılır.

```python
def norm_kirp(gradlar, max_norm):
    """Tum gradyanlarin birlesik L2 normunu max_norm'a indirir.
    Yonu degistirmez; yalnizca boyu kisar."""
    toplam = math.sqrt(sum(float((g * g).sum()) for g in gradlar))
    if toplam > max_norm:
        s = max_norm / (toplam + 1e-6)
        gradlar = [g * s for g in gradlar]
    return gradlar, toplam
```

Gradyan deneylerini yapan betik aşağıdadır: (a) patlayan gradyan ve kırpma, (b) ilk katmanın gradyanı, artık bloğu ve sıfır başlatma.

```python
# -*- coding: utf-8 -*-
"""Deney 8: gradyan sorunlari.
(a) Patlayan gradyan ve norm kirpma (20 katman, BN yok, SGD lr=0.5).
(b) Kaybolan gradyan: 30 katman, varsayilan init vs He vs artik
    (residual) baglanti; ilk katmanin gradyan normu (init'te)."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, csv_yaz

D = veri()
Xtr, ytr = D[0], D[1]
```
```python
def derin(katman, he=True):
    kat, d = [], 64
    for _ in range(katman):
        L = nn.Linear(d, 128)
        if he:
            nn.init.kaiming_normal_(L.weight, nonlinearity="relu")
            nn.init.zeros_(L.bias)
        kat += [L, nn.ReLU()]
        d = 128
    kat.append(nn.Linear(d, 10))
    return nn.Sequential(*kat)
```
```python
# (a) patlayan gradyan
def patlat(klip, lr=0.5, adim=200, seed=0):
    torch.manual_seed(seed)
    m = derin(20)
    opt = torch.optim.SGD(m.parameters(), lr=lr)
    g = torch.Generator().manual_seed(seed)
    gn_l, loss_l, nan_ilk = [], [], None
    for k in range(adim):
        idx = torch.randperm(len(Xtr), generator=g)[:32]
        opt.zero_grad()
        loss = F.cross_entropy(m(Xtr[idx]), ytr[idx])
        loss.backward()
        gn = torch.sqrt(
            sum((p.grad**2).sum() for p in m.parameters())
        ).item()
        if klip is not None:
            torch.nn.utils.clip_grad_norm_(m.parameters(), klip)
        opt.step()
        gn_l.append(gn)
        loss_l.append(loss.item())
        if nan_ilk is None and not np.isfinite(loss.item()):
            nan_ilk = k
            break
    return gn_l, loss_l, nan_ilk


gn0, l0, n0 = patlat(None)
gn1, l1, n1 = patlat(1.0)
print("Kirpmasiz: NaN adimi=%s, son kayip=%.3f" % (n0, l0[-1]))
print("  en buyuk norm=%.3g" % max(gn0))
print("Kirpmali (max_norm=1): NaN adimi=%s" % n1)
print("  son kayip=%.3f, en buyuk norm=%.3g" % (l1[-1], max(gn1)))
satir = []
for k in range(len(l0)):
    satir.append(("kirpmasiz", k, "%.5g" % gn0[k], "%.5g" % l0[k]))
for k in range(len(l1)):
    satir.append(("kirpmali", k, "%.5g" % gn1[k], "%.5g" % l1[k]))
csv_yaz(
    "b64_klip.csv", satir, ["mod", "adim", "gradyan_norm", "kayip"]
)
```
```python
# (b) kaybolan gradyan: ilk katman gradyani (init'te, tek batch)
torch.manual_seed(0)
X = Xtr[:256]
Y = ytr[:256]
sat2 = []
print("\nIlk katman agirlik gradyan normu (init, 256 ornek):")
for ad, model in [
    ("varsayilan 30 katman", None),
    ("He 30 katman", derin(30, he=True)),
]:
    if model is None:
        torch.manual_seed(0)
        model = derin(30, he=False)
    model.zero_grad()
    F.cross_entropy(model(X), Y).backward()
    g1 = model[0].weight.grad.norm().item()
    gson = model[-1].weight.grad.norm().item()
    print(
        "  %-22s ilk katman=%.3e   son katman=%.3e" % (ad, g1, gson)
    )
    sat2.append((ad, "%.6e" % g1, "%.6e" % gson))


# artik (residual) blok: h = h + W2 relu(W1 h), He init
```
```python
class Artik(nn.Module):
    def __init__(self, n, katman, zero_son=False):
        super().__init__()
        self.giris = nn.Linear(64, n)
        self.bloklar = nn.ModuleList()
        for _ in range(katman):
            a = nn.Linear(n, n)
            b = nn.Linear(n, n)
            for L in (a, b):
                nn.init.kaiming_normal_(L.weight, nonlinearity="relu")
                nn.init.zeros_(L.bias)
            if zero_son:
                nn.init.zeros_(b.weight)  # dal sifirdan baslar
            self.bloklar.append(nn.ModuleList([a, b]))
        self.cikis = nn.Linear(n, 10)

    def forward(self, x):
        h = self.giris(x)
        for a, b in self.bloklar:
            h = h + b(F.relu(a(h)))
        return self.cikis(h)


for ad, zs in [
    ("artik He (30 katman)", False),
    ("artik, dal son=0 (30)", True),
]:
    torch.manual_seed(0)
    art = Artik(128, 15, zero_son=zs)  # 30 dogrusal katman
    art.zero_grad()
    F.cross_entropy(art(X), Y).backward()
    g1 = art.giris.weight.grad.norm().item()
    gs = art.cikis.weight.grad.norm().item()
    print("  %-22s ilk katman=%.3e   son katman=%.3e" % (ad, g1, gs))
    sat2.append((ad, "%.6e" % g1, "%.6e" % gs))
csv_yaz(
    "b64_residual.csv",
    sat2,
    ["model", "ilk_katman_grad", "son_katman_grad"],
)
```
```term
$ python t08_gradyan.py
Kirpmasiz: NaN adimi=None, son kayip=2.261
  en buyuk norm=23.5
Kirpmali (max_norm=1): NaN adimi=None
  son kayip=1.329, en buyuk norm=51.1

Ilk katman agirlik gradyan normu (init, 256 ornek):
  varsayilan 30 katman   ilk katman=1.429e-12   son katman=2.132e-02
  He 30 katman           ilk katman=3.173e-01   son katman=1.206e+00
  artik He (30 katman)   ilk katman=3.949e+03   son katman=8.205e+03
  artik, dal son=0 (30)  ilk katman=2.907e-01   son katman=4.136e-01
```

Bu fonksiyon PyTorch'un `clip_grad_norm_` fonksiyonuyla birebir eşleşti. Bir deneyde 20 katmanlı ağı SGD ile 0,5 öğrenme oranında, batch 32 kullanarak 200 adım eğittik. Kırpmasız koşuda gradyan normu 23,5'e kadar çıktı; kırpmalı koşuda (max_norm = 1) ise kırpmadan önceki normlar 51'e kadar ulaştı ama her adımda kırpıldığı için ağ bu sıçramalara rağmen öğrenmeye devam etti. Kırpmasız koşunun 200 adımdan sonraki tek batch kaybı 2,26 (ağ hâlâ şans düzeyine yakın); kırpmalı koşuda 1,33 idi. Bu tek bir batch değeri olduğu için gürültülüdür; Şekil 64.8'in sağ panelindeki eğri, kaybın genel seyrini daha iyi gösteriyor.

![Şekil 64.8: Sol: gradyan normu (kırpmadan önce) kırpmasız ve kırpmalı koşularda. Sağ: mini-batch kaybı; kırpma eğitimin raydan çıkmasını engeller.](gorseller/b64_klip.png)

Şekil 64.8'in sol panelinde kırpmasız koşunun birkaç adımda 10⁰'ın üzerine çıkan normları ile kırpmalı koşunun sürekli yüksek normlarını görebilirsin. Her iki eğride de norm kırpmadan önce ölçüldüğü için kırpmalı koşunun norm eğrisi de yüksek kalabiliyor; fark, kırpmalı koşuda bu normların her adımda max_norm ile sınırlanmasıdır. Sağ paneldeki kayıp ise kırpmalı koşuda daha kararlı bir düşüş gösteriyor.

**Artık bağlantılar (residual connections)** ise kaybolan gradyana karşı yapısal bir çözümdür. Her bloğun çıktısını girdisine ekleriz: h ← h + F(h). Bu toplamın türevi (1 + F'(h)) olduğu için gradyan, çarpımsal zincir yerine doğrudan bir yoldan geri akar. Bölüm 66'da ResNet ile ayrıntılı göreceğiz; burada etkisini ölçüyoruz.

Aşağıdaki tabloda ilk katmanın gradyan normu, başlatma biçimine göre 30 katmanlı ağlarda ölçüldü (tek batch, 256 örnek, başlangıç ağırlıkları):

| Model | İlk katman gradyanı | Son katman gradyanı |
|---|---|---|
| Varsayılan PyTorch başlatma, 30 katman | 1,4 × 10⁻¹² | 2,1 × 10⁻² |
| He başlatma, 30 katman | 0,32 | 1,2 |
| Artık, He başlatma (dal son katmanı He) | 3,9 × 10³ | 8,2 × 10³ |
| Artık, dal son katmanı sıfır | 0,29 | 0,41 |

Tablo iki şey gösteriyor. Birincisi, varsayılan başlatmada 30 katmanlı ağın ilk katmanı neredeyse hiç gradyan almıyor (10⁻¹²). Bu, kaybolan gradyanın derin bir ağda ne kadar şiddetli olabileceğinin sayısal bir örneğidir. İkincisi, artık bağlantıyı He ile kurduğumuzda gradyan patladı (3,9 × 10³). Çünkü her artık blok eklediği dalın çıktısını girdiye ekler ve 15 blok bu eklemeleri üst üste biriktirir; bu büyümenin kaba bir sezgisi vardır, ölçüm yalnızca sonucu gösteriyor. Çözüm, her artık dalın son katmanını sıfırla başlatmaktır: dal başta sıfır çıktı verir, ağ bir kimlik fonksiyonu olarak başlar ve gradyan olduğu gibi akar. Bu sonuç 0,29 ile sağlıklı bir ölçektedir. Yani artık bağlantı, başlatma ile birlikte düşünüldüğünde işe yarar; tek başına bir sihir değildir.

## 64.10 Eğitim hatası ayıklama: loss eğrisini okumak

Bu bölümün kalbi budur. Bir eğitim koşusu başarısız olduğunda, hatanın kaynağı genellikle üç yerdedir: öğrenme oranı ve optimizer, model ve veri, ya da kodun kendisi. Hangi yerde olduğunu anlamak için iki temel araç kullanılır: loss eğrisi ve tek batch'e aşırı uydurma testi.

Kayıp kataloğunu üreten betik aşağıdadır. Önce başlangıç kaybı kontrolü yapılır; ardından yedi vakanın her biri 40 epoch boyunca eğitilir ve kayıp eğrileri CSV dosyasına yazılır.

```python
# -*- coding: utf-8 -*-
"""Deney 9: egitim hatasi ayiklama katalogu - gercek kosularda loss
egrileri. Her vaka icin egitim/dogrulama kaybi ve dogruluk olculur.
Test kumesi yalnizca son raporda kullanilir."""

import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, mlp, egit, csv_yaz

D = veri()
Xtr, ytr, Xva, yva, Xte, yte = D
torch.manual_seed(0)

# (0) Baslangic kaybi kontrolu: C=10 sinif -> -ln(1/10)
sifir = mlp()
nn.init.zeros_(sifir[-1].weight)
nn.init.zeros_(sifir[-1].bias)
with torch.no_grad():
    l0 = F.cross_entropy(sifir(Xva), yva).item()
print(
    "Sifir cikis agirligi ile baslangic kaybi = %.6f  (ln10 = %.6f)"
    % (l0, math.log(10))
)
torch.manual_seed(0)
rast = mlp()
with torch.no_grad():
    print(
        "Varsayilan init baslangic kaybi = %.4f"
        % F.cross_entropy(rast(Xva), yva).item()
    )
```
```python
satir = []
sonuc = []


def kaydet(ad, h, m=None):
    for ep in range(len(h["tr"])):
        satir.append(
            (
                ad,
                ep + 1,
                "%.5g" % h["tr"][ep],
                "%.5g" % h["va"][ep],
                "%.4f" % h["vacc"][ep],
            )
        )
    nan_ep = next(
        (
            i + 1
            for i, v in enumerate(h["tr"])
            if not math.isfinite(v)
        ),
        None,
    )
    son_tr = h["tr"][-1]
    sonuc.append((ad, son_tr, h["va"][-1], h["vacc"][-1], nan_ep))
    print(
        "%-18s tr=%.4g va=%.4g acc=%.4f nan=%s"
        % (ad, son_tr, h["va"][-1], h["vacc"][-1], nan_ep)
    )
```
```python
EP = 40
# A. Yuksek ogrenme orani
torch.manual_seed(0)
m = mlp()
kaydet(
    "A_yuksek_lr",
    egit(
        m,
        torch.optim.SGD(m.parameters(), lr=2.0),
        D,
        epochs=EP,
        seed=0,
    ),
)
# B. Cok dusuk ogrenme orani
torch.manual_seed(0)
m = mlp()
kaydet(
    "B_dusuk_lr",
    egit(
        m,
        torch.optim.SGD(m.parameters(), lr=1e-4),
        D,
        epochs=EP,
        seed=0,
    ),
)
# C. Asiri uydurma: 100 egitim ornegi, buyuk model,
# duzenlilestirme yok
Dk = (Xtr[:100], ytr[:100], Xva, yva, Xte, yte)
torch.manual_seed(0)
m = mlp(gizli=512)
kaydet(
    "C_asiri_uydurma",
    egit(
        m,
        torch.optim.Adam(m.parameters(), lr=1e-3),
        Dk,
        epochs=EP,
        batch=32,
        seed=0,
    ),
)
```
```python
# D. Yetersiz uydurma: cok kucuk model
torch.manual_seed(0)
m = mlp(gizli=2, derinlik=1)
kaydet(
    "D_yetersiz",
    egit(
        m,
        torch.optim.SGD(m.parameters(), lr=0.1),
        D,
        epochs=EP,
        seed=0,
    ),
)
```
```python
# E. Veri sizintisi: egitim ve dogrulamada etiket
# bilgisi ozellige sizar,
# test kumesinde bu ozellik sifirlanir (boru hatti hatasi)
def sizinti_ekle(X, y, aktif):
    oh = F.one_hot(y, 10).float() * 1.0
    if not aktif:
        oh = torch.zeros_like(oh)
    return torch.cat([X, oh], dim=1)


Ds = (
    sizinti_ekle(Xtr, ytr, True),
    ytr,
    sizinti_ekle(Xva, yva, True),
    yva,
    sizinti_ekle(Xte, yte, False),
    yte,
)
torch.manual_seed(0)
m = mlp(giris=74)
h = egit(
    m,
    torch.optim.Adam(m.parameters(), lr=1e-3),
    Ds,
    epochs=EP,
    seed=0,
)
kaydet("E_sizinti", h)
print(
    "   sizinti: dogrulama=%.4f  TEST=%.4f"
    % (h["val_acc"], h["test_acc"])
)
```
```python
# F. Etiket karisikligi: egitim etiketlerinin %30'u rastgele
g = torch.Generator().manual_seed(7)
ygur = ytr.clone()
secim = torch.rand(len(ytr), generator=g) < 0.30
ygur[secim] = torch.randint(0, 10, (int(secim.sum()),), generator=g)
Dg = (Xtr, ygur, Xva, yva, Xte, yte)
torch.manual_seed(0)
m = mlp()
kaydet(
    "F_etiket_karisik",
    egit(
        m,
        torch.optim.Adam(m.parameters(), lr=1e-3),
        Dg,
        epochs=EP,
        seed=0,
    ),
)
print(
    "   etiket karisik: %.1f%% etiket degistirildi"
    % (100 * secim.float().mean())
)
```
```python
# G. Sayisal kararsizlik: cok buyuk lr (Adam)
torch.manual_seed(0)
m = mlp()
kaydet(
    "G_nan_adam_lr1e3",
    egit(
        m,
        torch.optim.Adam(m.parameters(), lr=1e3),
        D,
        epochs=5,
        seed=0,
    ),
)

csv_yaz(
    "b64_teshis.csv",
    satir,
    ["vaka", "epoch", "tr_loss", "va_loss", "va_acc"],
)
csv_yaz(
    "b64_teshis_ozet.csv",
    [
        (a, "%.5g" % b, "%.5g" % c, "%.4f" % d, e if e else "")
        for a, b, c, d, e in sonuc
    ],
    ["vaka", "son_tr", "son_va", "son_va_acc", "nan_epoch"],
)
```
```term
$ python t09_teshis.py
Sifir cikis agirligi ile baslangic kaybi = 2.302585  (ln10 = 2.302585)
Varsayilan init baslangic kaybi = 2.3073
A_yuksek_lr        tr=2.321 va=2.316 acc=0.0975 nan=None
B_dusuk_lr         tr=2.304 va=2.304 acc=0.0780 nan=None
C_asiri_uydurma    tr=0.01127 va=0.3032 acc=0.8914 nan=None
D_yetersiz         tr=1.694 va=1.706 acc=0.2423 nan=None
E_sizinti          tr=0.0001602 va=0.0003869 acc=1.0000 nan=None
   sizinti: dogrulama=1.0000  TEST=0.9611
F_etiket_karisik   tr=0.9745 va=0.5544 acc=0.9192 nan=None
   etiket karisik: 31.5% etiket degistirildi
G_nan_adam_lr1e3   tr=485.8 va=508.2 acc=0.1003 nan=None
```

**Loss eğrisi kataloğu.** Eğitim ve doğrulama kaybını her epoch kaydederek, koşunun belirtilerini okuyabilirsin. Aşağıdaki yedi vakanın hepsi gerçek koşulardan alındı (MLP, Adam ya da SGD, digits verisi, 40 epoch, tohum 0). Şekil 64.9, altı vakayı kayıp eğrileriyle gösteriyor; yedinci vaka (NaN) metin ve tabloda ayrıca ele alındı.

![Şekil 64.9: Eğitim hatası kataloğu: altı gerçek koşunun eğitim (kırmızı) ve doğrulama (lacivert kesikli) kaybı. E panelinde log ölçek kullanıldı.](gorseller/b64_teshis_katalog.png)

| Vaka | Yapılan | Son eğitim kaybı | Son doğrulama kaybı | Doğruluk | Belirti ve teşhis |
|---|---|---|---|---|---|
| A: yüksek lr | SGD, η = 2,0 | 2,321 | 2,316 | 0,0975 | Kayıp ln 10 civarında düz; ağ öğrenmiyor. Bölüm 63'te aynı öğrenme oranında ölü ReLU birimleri görülmüştü; bu koşuda birim sayısını ölçmedik. |
| B: düşük lr | SGD, η = 10⁻⁴ | 2,3045 | 2,3039 | 0,0780 | Kayıp neredeyse hiç düşmüyor; ağ öğreniyor ama yavaş. Çözüm lr'yi artırmak ya da daha çok adım. |
| C: aşırı uydurma | 100 örnek, 512 birim | 0,0113 | 0,3032 | 0,8914 | Eğitim kaybı sıfıra yakın, doğrulama kaybı yüksek ve sonra düz. Klasik ezberleme. |
| D: yetersiz uydurma | 2 birimlik darboğaz | 1,694 | 1,706 | 0,2423 | İki kaybın da yüksek ve birbirine yakın olması: model yetersiz. Kapasiteyi artır. |
| E: veri sızıntısı | Etiket bilgisi özelliğe sızdı, test için sıfırlandı | 1,6 × 10⁻⁴ | 3,9 × 10⁻⁴ | 1,0000 (doğrulama) | Doğrulama mükemmel ama test 0,9611. Doğrulama skoru gerçek olamayacak kadar iyi: sızıntı şüphesi. |
| F: etiket karışıklığı | Eğitim etiketlerinin yaklaşık %31'i rastgele | 0,9745 | 0,5544 | 0,9192 | Eğitim kaybı yüksek kalıyor, doğrulama makul; etiket gürültüsünün tipik imzası. |
| G: NaN | Adam, η = 10³ | 485,8 | 508,2 | 0,1003 | Beş epoch'ta NaN çıkmadı ama kayıp devasa; kararsızlık. (Aşağıda NaN'ın nasıl oluştuğunu ayrıca gösteriyoruz.) |

Tablo, belirtileri teşhise nasıl çevireceğimizi gösteriyor. **Aşırı uydurma (C)**da eğitim ve doğrulama kayıpları ilk epoch'larda birlikte düşer, sonra ayrılır: doğrulama kaybı düz kalır ya da yükselir. **Yetersiz uydurma (D)**da iki kayıp birbirine yakın ve yüksektir. **Veri sızıntısı (E)**nda doğrulama, eğitimden bile iyi görünür ve gerçek bir kümede (test) düşer; bu, doğrulama kümesinin eğitimle aynı bilgiyi taşıdığının işaretidir. Bu vakada etiket bilgisi özelliğe doğrudan sızdığı için doğrulama 1,0 oldu.

Vaka F'de eğitim kaybının yüksek kalması, etiket gürültüsünün bir imzasıdır: ağ yanlış etiketleri ezberleyemez, bu yüzden eğitim kaybı yüksek kalır, ama doğru etiketlerin çoğunluğunu öğrendiği için doğrulama düşük kalır. Vaka A ve B'nin ayrımı da öğreticidir: ikisinde de ağ öğrenmiyor, ama A'da kayıp ln 10'un çevresinde salınır, B'de ise yavaşça iner. Bu iki belirti aynı şikâyet gibi görünse de düzeltmesi zıt yönlüdür.

**Başlangıç kaybı kontrolü.** Her eğitim koşusunun ilk adımında kayıp, teorik başlangıç değerine yakın olmalıdır. C sınıf için bu değer ln C'dir. Sıfır başlatılmış son katmanlı bir ağda kayıp tam olarak ln 10 = 2,302585 çıkar; bizim ölçümümüz de 2,302585 verdi. Varsayılan başlatmada ise 2,3073 bulundu, yani aynı düzeyde. Eğer ilk kaybın 2,3'ten çok farklıysa (örneğin 10 ya da 0,01 gibi), çıkış katmanında ya da veri etiketlerinde bir hata vardır. Bu kontrol 10 saniye sürer ve birçok hatayı en başta yakalar.

**NaN'ın iki yolu.** Eğitimde NaN, genellikle sayısal taşmanın sonucudur (Bölüm 63.14). Tipik hata, çapraz entropiyi softmax'in ardından ayrı ayrı hesaplamaktır: softmax çıktısı tam sıfır olursa log(0) = −∞ olur. Aşağıdaki program, aynı veri ve aynı ağ üzerinde iki yolu karşılaştırır: ayrık `log(softmax)` ile `F.cross_entropy` (ki bu log-sumexp ile kararlı hesaplanır). Öğrenme oranını bilerek 10³ aldık.

```python
# -*- coding: utf-8 -*-
"""Deney 9b: NaN'in iki yolu. (1) ayrik log(softmax) ile log(0);
(2) kayip degeri sonsuz (inf) olunca gradyan NaN'a donusur."""

import torch
import torch.nn.functional as F
from ortak64 import veri, mlp

D = veri()
Xtr, ytr = D[0], D[1]
torch.manual_seed(0)
m = mlp()
opt = torch.optim.SGD(m.parameters(), lr=1e3)
for k in range(6):
    opt.zero_grad()
    out = m(Xtr[:32])
    p = torch.softmax(out, 1)
    loss = -torch.log(p.gather(1, ytr[:32, None])).mean()  # ayrik log
    loss.backward()
    print(
        "adim %d  kayip=%s  logit_maks=%.3g"
        % (k, loss.item(), out.abs().max().item())
    )
    opt.step()
print("\nKararli: F.cross_entropy ayni veride:")
torch.manual_seed(0)
m = mlp()
opt = torch.optim.SGD(m.parameters(), lr=1e3)
for k in range(6):
    opt.zero_grad()
    loss = F.cross_entropy(m(Xtr[:32]), ytr[:32])
    loss.backward()
    print("adim %d  kayip=%s" % (k, loss.item()))
    opt.step()
```

Program, ayrık yöntemde ilk adımdan sonra kaybın sonsuza gittiğini ve iki adım sonra NaN'a dönüştüğünü gösterir. Kararlı yöntemde ise kayıp büyük ama sonlu kalır:

```term
$ python t09b_nan.py
adim 0  kayip=2.311190128326416  logit_maks=0.152
adim 1  kayip=inf  logit_maks=4.61e+05
adim 2  kayip=nan  logit_maks=nan
adim 3  kayip=nan  logit_maks=nan
adim 4  kayip=nan  logit_maks=nan
adim 5  kayip=nan  logit_maks=nan

Kararli: F.cross_entropy ayni veride:
adim 0  kayip=2.311189889907837
adim 1  kayip=205397.140625
adim 2  kayip=4.678431854611661e+16
adim 3  kayip=388077092864.0
adim 4  kayip=491.6092224121094
adim 5  kayip=457.5995178222656
```

Dikkat edilmesi gereken nokta, ayrık yöntemde logit büyüklüğünün 4,6 × 10⁵'e çıkmasıdır; softmax bu değerlerde 1 ile 0 arasında tam sıfırlar üretir ve log(0) sonsuza gider. `F.cross_entropy` de aynı büyük logitlerle sonlu bir kayıp verir çünkü log-sumexp'i maksimumu çıkararak hesaplar. Bu iki yol, sayısal kararlılığın algoritma seçimine bağlı olduğunu gösterir. Pratik kural: çapraz entropiyi her zaman ham logitlerden hesapla, softmax'i önce uygulama.

**Bir tarif olarak eğitim.** Karpathy'nin "A Recipe for Training Neural Networks" (2019, blog yazısı; genel bilgi) yazısı, eğitim hatalarını ayıklamak için bir sıra önerir: önce veriyi gözle incele, sonra basit bir baseline kur, ilk kaybın beklenen değerde olduğunu doğrula, ağı tek bir batch'e aşırı uydurmayı dene, ardından kapasiteyi artırıp düzenlileştir ve en son hiperparametreleri ayarla. Bu bölümdeki sıra da büyük ölçüde bu tarife uyar.

Tek batch testini ve eval modu kontrollerini yapan betik aşağıdadır. Dört varyant aynı 32 örnek üzerinde 500 adım çalışır; ardından dropout ve BatchNorm için eval modu farkı ölçülür.

```python
# -*- coding: utf-8 -*-
"""Deney 10: tek batch'e asiri uydurma testi ve kasitli hatalar.

Ayni 32 ornek, ayni model, ayni optimizer; yalnizca bir hata enjekte
edilir. Dogru kod sifira yakin kayip vermeli; hata varsa belirti olcu-
lur. Tohum 0."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, mlp, csv_yaz

D = veri()
Xtr, ytr = D[0][:32], D[1][:32]
ADIM = 500
```
```python
def kos(ad, hata=None, adim=ADIM):
    torch.manual_seed(0)
    m = mlp(gizli=128)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    x, y = Xtr, ytr
    if hata == "etiket_kaydi":
        y = ytr[
            torch.randperm(
                32, generator=torch.Generator().manual_seed(3)
            )
        ]
    gecmis = []
    for k in range(adim):
        if hata != "zero_grad_yok":
            opt.zero_grad()
        out = m(x)
        if hata == "cift_softmax":
            out = torch.softmax(out, 1)
        loss = F.cross_entropy(out, y)
        loss.backward()
        opt.step()
        if k % 100 == 0 or k == adim - 1:
            gecmis.append((k, loss.item()))
    acc = (m(x).argmax(1) == y).float().mean().item()
    print("%-13s %s" % (ad, " ".join("%d:%.3f" % g for g in gecmis)))
    print("%-13s dogruluk=%.3f" % ("", acc))
    return gecmis, acc
```
```python
print("Tek batch testi (32 ornek, Adam 1e-3, 500 adim):")
sat = []
for ad, hata in [
    ("dogru", None),
    ("cift_softmax", "cift_softmax"),
    ("etiket_kaydi", "etiket_kaydi"),
    ("zero_grad_yok", "zero_grad_yok"),
]:
    gec, acc = kos(ad, hata)
    for k, l in gec:
        sat.append((ad, k, "%.6f" % l))
csv_yaz("b64_tek_batch.csv", sat, ["vaka", "adim", "kayip"])
```
```python
# Eval modu unutulursa: dropout ve BN
torch.manual_seed(0)
m = mlp(gizli=256, dropout=0.5)
opt = torch.optim.Adam(m.parameters(), lr=1e-3)
Xa, ya = veri()[0], veri()[1]
for ep in range(10):
    m.train()
    for i in range(0, len(Xa), 32):
        opt.zero_grad()
        F.cross_entropy(m(Xa[i : i + 32]), ya[i : i + 32]).backward()
        opt.step()
```
```python
Xv = veri()[2]
m.train()  # eval() unutuldu
p1 = m(Xv).argmax(1)
p2 = m(Xv).argmax(1)
print(
    "\nDropout acik (eval unutuldu): tahmin farki = %d / 360"
    % (p1 != p2).sum().item()
)
m.eval()
q1 = m(Xv).argmax(1)
q2 = m(Xv).argmax(1)
print(
    "Dogru eval modu: iki tahmin arasi fark = %d"
    % (q1 != q2).sum().item()
)

torch.manual_seed(0)
bn = mlp(gizli=128, bn=True)
opt = torch.optim.Adam(bn.parameters(), lr=1e-3)
for ep in range(10):
    bn.train()
    for i in range(0, len(Xa), 32):
        opt.zero_grad()
        F.cross_entropy(bn(Xa[i : i + 32]), ya[i : i + 32]).backward()
        opt.step()
bn.train()
t_mod = bn(Xv).argmax(1)
bn.eval()
e_mod = bn(Xv).argmax(1)
print(
    "BN: train modunda ve eval modunda tahmin farki = %d / 360"
    % (t_mod != e_mod).sum().item()
)
bn.train()
ya_acc = (bn(Xv).argmax(1) == veri()[3]).float().mean().item()
bn.eval()
yb_acc = (bn(Xv).argmax(1) == veri()[3]).float().mean().item()
print(
    "BN dogrulama dogrulugu: train modunda=%.4f, eval modunda=%.4f"
    % (ya_acc, yb_acc)
)
```
```term
$ python t10_tek_batch.py
Tek batch testi (32 ornek, Adam 1e-3, 500 adim):
dogru         0:2.311 100:0.020 200:0.003 300:0.001 400:0.001 499:0.000
              dogruluk=1.000
cift_softmax  0:2.303 100:1.676 200:1.613 300:1.492 400:1.491 499:1.491
              dogruluk=0.969
etiket_kaydi  0:2.305 100:0.066 200:0.007 300:0.003 400:0.002 499:0.001
              dogruluk=1.000
zero_grad_yok 0:2.311 100:0.961 200:0.575 300:0.291 400:0.383 499:0.052
              dogruluk=0.969

Dropout acik (eval unutuldu): tahmin farki = 23 / 360
Dogru eval modu: iki tahmin arasi fark = 0
BN: train modunda ve eval modunda tahmin farki = 0 / 360
BN dogrulama dogrulugu: train modunda=0.9833, eval modunda=0.9833
```

**Tek batch'e aşırı uydurma testi.** Bu, bütün eğitim kodunu sınamanın en hızlı yoludur. Tek bir küçük batch (burada 32 örnek) seçer, ağı ona aşırı uydurmaya çalışırsın. Doğru kurulmuş bir ağ ve kod, birkaç yüz adımda kaybı sıfıra yakın düşürmelidir ve doğruluk 1,0 olmalıdır. Eğer kayıp düşmüyorsa, hata modelde, kayıp fonksiyonunda, optimizasyonda ya da verinin etiketlenmesinde demektir. Aşağıdaki deneyde aynı 32 örnek ve aynı Adam (η = 10⁻³) ile 500 adım koştuk; her seferinde tek bir hata enjekte ettik.

| Vaka | Kayıp (adım 0 → 499) | Doğruluk | Yorum |
|---|---|---|---|
| Doğru kod | 2,311 → 0,0004 | 1,000 | Test geçti. |
| Çift softmax (softmax, sonra CE) | 2,303 → 1,491 | 0,969 | Kayıp 1,49'da takıldı; belirti: kayıp yüksek düzlükte kalıyor. |
| Batch içinde etiket karıştırma | 2,305 → 0,0010 | 1,000 | Test GEÇTİ. Aşağıda neden. |
| `zero_grad` yok | 2,311 → 0,0519 | 0,969 | Kayıp salınımlı (adım 200'de 0,575, 300'de 0,291, 400'de 0,383); gradyanlar birikiyor. |

Çift softmax hatası, kaybı bir düzlüğe kilitler: softmax çıktısını bir daha softmax'lemek olasılıkları düzleştirir ve bu da gradyanları küçültür (bu bir sezgidir; gradyan normunu bu deneyde ölçmedik). Yüksek kalan kayıp ve düşük doğruluk, bu hatanın imzasıdır. `zero_grad` eksikliği ise gradyanların her adımda birikmesine yol açar; kayıp düşer ama salınır ve yakınsamaz. Bu iki hatayı tek batch testi kolayca yakaladı.

Ama tabloda dikkat çeken bir sonuç var: batch içinde etiketleri karıştırdığımız vaka da testi geçti. Etiketler yanlış eşlenmiş olmasına rağmen 128 birimli ağ, 32 örneği ezberleyebildi. Bu, tek batch testinin **gerekli ama yeterli olmadığını** gösterir. Ağ yeterince büyükse, rastgele etiketleri bile ezberleyebilir. Etiket hatalarını yakalamak için başka bir araç gerekir: doğrulama kümesinde beklenen doğruluğu ölçmek, etiket dağılımını kontrol etmek ve (en önemlisi) verinin hangi kaynaktan geldiğini ve nasıl hizalandığını denetlemek. Bu nedenle tek batch testini, eğitim kodunun mekanik olarak çalıştığını sınamak için kullan; veri doğruluğu için ayrı bir kontrol yap.

**Eval modu ve dropout.** Dropout ve BatchNorm, eğitim ile çıkarım arasında davranış farkı yaratır. Eğer eğitimden sonra `model.eval()` çağrılmazsa, tahmin yaparken dropout hâlâ maske uygular ve BatchNorm batch istatistiklerini kullanır. Bunun belirtisi, aynı girdinin iki kez tahmininin farklı çıkmasıdır. 360 doğrulama örneği üzerinde yapılan ölçümde, dropout 0,5'li bir ağda eval unutulduğunda iki tahmin arasında 23 fark çıktı; `model.eval()` ile fark 0 oldu. BatchNorm ağında, 32 batch ile eğitilmiş modelde train ve eval modu arasında tahmin farkı 0/360 çıktı (doğruluk 0,9833 her iki modda da). Yani BatchNorm'un tehlikesi, batch çok küçük olduğunda ve veri dağılımı kaydığında ortaya çıkar; büyük batch'te fark gizli kalabilir. Bu yüzden değerlendirme kodunu her zaman `model.eval()` ile ve `torch.no_grad()` içinde yaz.

**Kasıtlı hata enjeksiyonu: Çözümlü Örnek 4.** Bu teknikleri bir araya getiren bir alıştırma, 3 hatalı bir eğitim betiğinin ayıklanmasıdır. Aşağıdaki betik bir MLP'yi digits verisi üzerinde eğitir ve her epoch'ta eğitim kaybını ve "doğrulama" doğruluğunu yazdırır. Betiğin sonunda test doğruluğu da yazılır. Önce kodu ve çıktıyı oku, sonra hataları bul; çözüm bölümde yer alıyor.

```python
# -*- coding: utf-8 -*-
"""Bolum 64 - Cozumlu Ornek 4 icin bozuk egitim betigi (3 hata)."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri

Xtr, ytr, Xva, yva, Xte, yte = veri()
torch.manual_seed(0)
model = nn.Sequential(
    nn.Linear(64, 128),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(128, 128),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(128, 10),
)
opt = torch.optim.Adam(model.parameters(), lr=1e-2)


def dogruluk(X, y):
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


for ep in range(15):
    perm = torch.randperm(len(Xtr))
    kayip = 0.0
    for i in range(0, len(Xtr), 32):
        idx = perm[i : i + 32]
        loss = F.cross_entropy(model(Xtr[idx]), ytr[idx])
        loss.backward()
        opt.step()
        kayip += loss.item()
    print(
        "ep %2d  kayip=%.4f  dogrulama=%.4f"
        % (ep + 1, kayip / (len(Xtr) / 32), dogruluk(Xtr, ytr))
    )
print("son test dogrulugu = %.4f" % dogruluk(Xte, yte))
```

Çıktı:

```term
$ python bozuk_egitim.py
ep  1  kayip=2.1490  dogrulama=0.3451
ep  2  kayip=2.4869  dogrulama=0.2004
ep  3  kayip=2.4335  dogrulama=0.2022
ep  4  kayip=2.7738  dogrulama=0.1104
ep  5  kayip=2.4035  dogrulama=0.1011
ep  6  kayip=2.4348  dogrulama=0.1058
ep  7  kayip=2.4438  dogrulama=0.1011
ep  8  kayip=2.4546  dogrulama=0.1011
ep  9  kayip=2.4319  dogrulama=0.1002
ep 10  kayip=2.4683  dogrulama=0.0993
ep 11  kayip=2.5498  dogrulama=0.1020
ep 12  kayip=2.5597  dogrulama=0.0965
ep 13  kayip=2.4764  dogrulama=0.1011
ep 14  kayip=2.4695  dogrulama=0.0993
ep 15  kayip=2.5592  dogrulama=0.0993
son test dogrulugu = 0.0972
```

Betiğin doğru hâlinde üç hata düzelir: `opt.zero_grad()` her adımdan önce çağrılır, doğruluk hesabında `model.eval()` kullanılır ve doğrulama `Xva, yva` üzerinden yapılır. Düzeltilmiş dosyada ayrıca her epoch başında `model.train()` çağrılır; bu, her epoch'un eğitim modunda başlamasını garanti eder. Düzeltilmiş betik 15 epoch sonunda doğrulamada 0,9526, test kümesinde 0,9472 doğruluk verdi; eğitim kaybı 1,52'den 0,29'a düştü.

Çözüm: Bu hatalar, çıktıda üç farklı belirti bırakır. (1) Kayıp düşmüyor, aksine 2,1'den 2,5'e çıkıp salınıyor. Bu belirti, gradyanların birikmesine (zero_grad eksik) işaret eder; kaybın 15 epoch boyunca düşmemesi birikmiş gradyanların Adam adımlarını bozmasıyla tutarlıdır (bu bir yorumdur; zero_grad'ın tek başına etkisini bu betikte ayrıca ölçmedik). (2) "Doğrulama" doğruluğu, eğitim kümesi üzerinden hesaplanıyor (Xtr, ytr): bu, rakamın neden kendi kaybıyla tutarlı olmadığını ve doğrulama kümesinin hiç kullanılmadığını açıklar. (3) Dropout ile hesaplanan doğruluk, eval modu kapalıyken yapılıyor: aynı girdi her çağrıda farklı tahmin üretebilir ve ölçüm gürültülüdür. Bu üçüncü hata, ikinci hatanın üzerine biner; ama yalnızca ikisi düzeltildiğinde bile bu betik eğitim verisini ölçtüğü için yanıltıcı olurdu. Düzeltilmiş betikte eğitim kaybı 0,75'ten 0,29'a düşüyor, doğrulama 0,95'e çıkıyor ve test kümesi de benzer bir değere ulaşıyor; bu tutarlılık sağlıklı bir eğitimin göstergesidir.

Bu örneğin asıl dersi şudur: bir eğitim betiğinde hata varsa, belirtilerin farklı yerlerde görünür. Kayıp eğrisi bazı hataları, doğrulama ölçümü bazılarını, test ile doğrulamanın tutarlılığı bazılarını gösterir. Üç soruyu aklında tut: Kayıp beklenen yönde mi düşüyor? Doğrulama kaybı ile eğitim kaybı makul bir ilişki içinde mi? Ölçtüğün şey gerçekten doğrulama kümesi mi?

## 64.11 Hiperparametre arama ve deney kaydı

Bir ağda birçok hiperparametre vardır: öğrenme oranı, batch boyutu, dropout, ağırlık azaltma, katman sayısı, birim sayısı. Bunları sistematik biçimde aramanın iki temel yolu vardır: **ızgara arama** (grid search), her boyutta eşit aralıklı değerleri deneyerek tüm kombinasyonları tarar; **rastgele arama** (random search), aynı bütçede değerleri rastgele seçer (Bergstra ve Bengio, 2012; genel bilgi).

Rastgele aramanın üstünlüğü, yalnızca birkaç boyutun gerçekten önemli olduğu durumlarda ortaya çıkar. Izgarada her boyut için az sayıda değer denersen, önemli boyutta kaç farklı değer test ettiğin de azalır. Rastgele aramada ise her deneme önemli boyutta yeni bir değer getirir. Bu deneyde bunu sınadık. Öğrenme oranı (log ölçekte 7 değer, 10⁻⁴ ile 10⁻¹ arası) ve dropout (6 değer, 0 ile 0,5 arası) boyutlarını 42 yapılandırmada tarayıp doğrulama doğruluğunu iki tohumla ölçtük (15 epoch). Sonra gerçek arama bütçesi olarak 9 yapılandırmayı iki yöntemle seçtik ve her seçimde dogrulamada en iyi olanı aldık. Arama süreci 300 kez tekrarlandı ve seçilen yapılandırmanın test skoru raporlandı.

Arama deneyini yapan betik aşağıdadır. Önce 42 yapılandırma iki tohumla eğitilip bir tablo oluşturulur; sonra ızgara ve rastgele arama bu tablo üzerinde 300 kez simüle edilir.

```python
# -*- coding: utf-8 -*-
"""Deney 11: izgara arama vs rastgele arama (Bergstra-Bengio 2012,
genel bilgi). Once 7 (lr) x 6 (dropout) = 42 yapilandirma, her biri
2 tohumla, 15 epoch; dogrulama skoru kaydedilir. Arama simulasyonu
bu onceden hesaplanmis tablo uzerinde yapilir:
  - izgara: lr 3 noktada x dropout 3 noktada = 9 yapilandirma
  - rastgele: 9 yapilandirma, tablodan tekrarsiz rastgele
Her arama 300 kez tekrarlanir; secilen (dogrulamada en iyi)
yapilandirmanin
TEST skoru raporlanir. Test skoru secimde KULLANILMAZ."""

import itertools
import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import veri, mlp, egit, csv_yaz

D = veri()
LR = [10**e for e in np.linspace(-4, -1, 7)]
DO = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
SEEDS2 = [20, 21]
```}
```python
tablo = {}
satir = []
for lr, do in itertools.product(range(7), range(6)):
    va, te = [], []
    for s in SEEDS2:
        torch.manual_seed(s)
        m = mlp(gizli=128, dropout=DO[do])
        opt = torch.optim.Adam(m.parameters(), lr=LR[lr])
        h = egit(m, opt, D, epochs=15, batch=32, seed=s)
        va.append(h["val_acc"])
        te.append(h["test_acc"])
    tablo[(lr, do)] = (np.mean(va), np.mean(te))
    satir.append(
        (LR[lr], DO[do], "%.4f" % np.mean(va), "%.4f" % np.mean(te))
    )
    print(
        "lr=%.1e dropout=%.1f  val=%.4f test=%.4f"
        % (LR[lr], DO[do], np.mean(va), np.mean(te))
    )
csv_yaz(
    "b64_arama_tablo.csv", satir, ["lr", "dropout", "val", "test"]
)
```
```python
rng = np.random.default_rng(64)
izgara = [(a, b) for a in (0, 3, 6) for b in (0, 2, 5)]
kumeler = list(tablo.keys())


def sec(konf):
    return max(konf, key=lambda k: tablo[k][0])


rs = []
for _ in range(300):
    idx = rng.choice(len(kumeler), size=9, replace=False)
    rs.append(tablo[sec([kumeler[i] for i in idx])][1])
ig_all = [tablo[sec(izgara)][1]]
en_iyi_test = max(t for _, t in tablo.values())
print(
    "\nTum tablonun en iyi TEST skoru (referans): %.4f" % en_iyi_test
)
print("Izgara (9 yapilandirma)  secilen test = %.4f" % ig_all[0])
print(
    "Rastgele (9, 300 tekrar) secilen test ort = %.4f" % np.mean(rs)
)
print(
    "  sd = %.4f, en kotu = %.4f" % (np.std(rs, ddof=1), np.min(rs))
)
lr_etki = np.ptp([tablo[(a, 0)][0] for a in range(7)])
do_etki = np.ptp([tablo[(3, b)][0] for b in range(6)])
print(
    "Dogrulama skor araligi: lr boyunca=%.4f, dropout boyunca=%.4f"
    % (lr_etki, do_etki)
)
```
```term
$ python t11_arama.py
lr=1.0e-04 dropout=0.0  val=0.8552 test=0.9000
lr=1.0e-04 dropout=0.1  val=0.8524 test=0.8931
lr=1.0e-04 dropout=0.2  val=0.8468 test=0.8847
lr=1.0e-04 dropout=0.3  val=0.8398 test=0.8819
lr=1.0e-04 dropout=0.4  val=0.8259 test=0.8611
lr=1.0e-04 dropout=0.5  val=0.7911 test=0.8389
lr=3.2e-04 dropout=0.0  val=0.9429 test=0.9528
lr=3.2e-04 dropout=0.1  val=0.9345 test=0.9486
lr=3.2e-04 dropout=0.2  val=0.9318 test=0.9486
lr=3.2e-04 dropout=0.3  val=0.9248 test=0.9458
lr=3.2e-04 dropout=0.4  val=0.9123 test=0.9431
lr=3.2e-04 dropout=0.5  val=0.8928 test=0.9250
lr=1.0e-03 dropout=0.0  val=0.9568 test=0.9694
lr=1.0e-03 dropout=0.1  val=0.9638 test=0.9597
lr=1.0e-03 dropout=0.2  val=0.9638 test=0.9625
lr=1.0e-03 dropout=0.3  val=0.9610 test=0.9611
lr=1.0e-03 dropout=0.4  val=0.9554 test=0.9583
lr=1.0e-03 dropout=0.5  val=0.9471 test=0.9500
lr=3.2e-03 dropout=0.0  val=0.9708 test=0.9764
lr=3.2e-03 dropout=0.1  val=0.9666 test=0.9764
lr=3.2e-03 dropout=0.2  val=0.9749 test=0.9722
lr=3.2e-03 dropout=0.3  val=0.9680 test=0.9639
lr=3.2e-03 dropout=0.4  val=0.9666 test=0.9764
lr=3.2e-03 dropout=0.5  val=0.9610 test=0.9750
lr=1.0e-02 dropout=0.0  val=0.9290 test=0.9194
lr=1.0e-02 dropout=0.1  val=0.9624 test=0.9639
lr=1.0e-02 dropout=0.2  val=0.9624 test=0.9708
lr=1.0e-02 dropout=0.3  val=0.9526 test=0.9736
lr=1.0e-02 dropout=0.4  val=0.9638 test=0.9764
lr=1.0e-02 dropout=0.5  val=0.9554 test=0.9625
lr=3.2e-02 dropout=0.0  val=0.9206 test=0.9278
lr=3.2e-02 dropout=0.1  val=0.9457 test=0.9556
lr=3.2e-02 dropout=0.2  val=0.9387 test=0.9486
lr=3.2e-02 dropout=0.3  val=0.9192 test=0.9236
lr=3.2e-02 dropout=0.4  val=0.9401 test=0.9389
lr=3.2e-02 dropout=0.5  val=0.8677 test=0.8833
lr=1.0e-01 dropout=0.0  val=0.8008 test=0.8319
lr=1.0e-01 dropout=0.1  val=0.1811 test=0.1833
lr=1.0e-01 dropout=0.2  val=0.4234 test=0.4403
lr=1.0e-01 dropout=0.3  val=0.2019 test=0.2028
lr=1.0e-01 dropout=0.4  val=0.1003 test=0.0986
lr=1.0e-01 dropout=0.5  val=0.1003 test=0.1000

Tum tablonun en iyi TEST skoru (referans): 0.9764
Izgara (9 yapilandirma)  secilen test = 0.9722
Rastgele (9, 300 tekrar) secilen test ort = 0.9710
  sd = 0.0059, en kotu = 0.9486
Dogrulama skor araligi: lr boyunca=0.1699, dropout boyunca=0.0139
```

Şekil 64.10, 42 yapılandırmanın doğrulama doğruluğunu ısı haritasında gösteriyor. Kırmızı kareler, ızgara aramasının seçtiği 9 noktayı işaretliyor.

![Şekil 64.10: Öğrenme oranı ve dropout'un doğrulama doğruluğu üzerindeki etkisi (2 tohum, 15 epoch). Kırmızı kareler ızgara aramasının 9 noktası.](gorseller/b64_arama_isi.png)

Sonuçlar şunları gösteriyor. Doğrulama skoru, öğrenme oranı boyunca 0,17 aralığında değişiyor, dropout boyunca ise yalnızca 0,014. Yani bu problemde öğrenme oranı baskın boyuttur; dropout'un etkisi gürültü düzeyinde. Izgara arama öğrenme oranını yalnızca 3 değerde (10⁻⁴, 3,2 × 10⁻³, 10⁻¹) tararken, rastgele arama 9 denemenin her birinde 7 düzeyli öğrenme oranı ızgarasının tamamından seçim yapabildi. Sonuçta ızgara, test kümesinde 0,9722 doğruluklu bir yapılandırma seçti; rastgele aramanın 300 tekrarında ortalama seçim 0,9710 ± 0,0059 (en kötü 0,9486) çıktı. Tablodaki en iyi yapılandırma 0,9764 idi. Bu fark küçük ve bu deneyde belirleyici değil. Rastgele aramanın sonuçları ise daha geniş bir dağılıma sahip (en kötü 0,9486). Bunun asıl pratik sonucu şudur: önce hangi boyutun önemli olduğunu bilmiyorsan, rastgele arama genellikle daha güvenli bir başlangıçtır; önemli boyut bilinirse ızgara daha hızlı bir kesinlik sağlar.

**Doğrulama disiplini.** Aramayı yalnızca doğrulama kümesinde yap. Test kümesi, arama sürecinin hiçbir aşamasında kullanılmamalıdır; aksi hâlde seçilen yapılandırmanın skoru iyimser olur (Bölüm 57'de gösterildi). Aramanın bütçesini (kaç yapılandırma denendi) raporla: 9 yapılandırmadan seçilen en iyi skor ile 300 yapılandırmadan seçilen en iyi skor aynı şey değildir.

**Tohum sapması.** Tek bir koşunun sonucunu raporlama. Bu bölümdeki her karşılaştırma beş tohumla yapıldı ve ortalama ± sapma verildi. Hiçbir tek koşu "daha iyi" yargısının kanıtı sayılmamalı; sapma, karşılaştırmanın güvenilirliğini gösterir.

**Karışık hassasiyet (mixed precision)** (kısa not): Ağırlıkların ve aktivasyonların bir kısmını 16 bit kayan noktayla hesaplamak, GPU bellek kullanımını ve hızını iyileştirir. Gradyan ölçeklemesi gibi ayrıntılar gerektirir ve sayısal taşma riskini artırır. Bölüm 65'te PyTorch ile uygulamasını göreceğiz; burada yalnızca bu bölümde bildiğimiz NaN ve taşma sorunlarının 16 bitte daha da kolay ortaya çıktığını not ediyoruz (genel bilgi).

**Deney kaydı.** Her koşunun hiperparametrelerini, tohumunu, veri bölme bilgisini ve her epoch'un metriklerini bir dosyaya (JSON satırları ya da CSV) yazmak, bu bölümün bütün ölçümlerini yeniden üretebilmenin şartıdır. Bu bölümdeki her tablo ve şekil, ilgili deney betiği ve veri dosyasından üretildi; kitabın kendisi ölçüm verisini `engine/veri` klasöründen okur. Bir ekip olarak, ölçüm verisini ve kodu birlikte saklamayı alışkanlık hâline getir.




## 64.12 PyTorch ile eşleşme: NumPy kodunun doğrulanması

Sıfırdan yazdığımız her parçanın doğru olduğunu PyTorch ile sınadık. Aşağıdaki betik 19 kontrol yapar: Adam, AdamW, L2 ile azaltma, momentum ve Nesterov güncellemeleri; BatchNorm'un ileri ve geri geçişi (PyTorch ve sayısal gradyan ile), running istatistikleri ve çıkarım modu; dropout'un ters ölçeklemesi; kosinüs, basamaklı ve üstel takvimler; gradyan kırpma. Her kontrol mutlak farkı yazar ve eşiği aşarsa HATA der. Genel eşik 10⁻⁶'dır; takvimler için 10⁻⁹ ve 10⁻¹² kullanılmıştır.

```python
# -*- coding: utf-8 -*-
"""Bolum 64 - NumPy gerceklemelerinin PyTorch ve sayisal gradyan
ile dogrulanmasi. Calistirma: python test_np64.py"""

import math
import numpy as np
import torch
import torch.nn.functional as F
from egitim_np import (
    sgd_momentum,
    sgd_nesterov,
    adam_adim,
    adamw_adim,
    adam_l2_adim,
    bn_ileri,
    bn_geri,
    bn_cikarim,
    dropout_ileri,
    lr_kosinus,
    lr_adim_kurali,
    lr_ustel,
    norm_kirp,
)

rng = np.random.default_rng(64)
sonuc = []
```
```python
def kontrol(ad, fark, esik=1e-6):
    tamam = fark <= esik
    sonuc.append(tamam)
    print(
        "%-38s max fark = %.3e   %s"
        % (ad, fark, "TAMAM" if tamam else "HATA")
    )
```
```python
# ---- A. Adam / AdamW / L2 / momentum: torch ile ayni adimlar ----
def optim_karsilastir(kur_np, kur_torch, ad):
    th0 = rng.standard_normal(7)
    gs = rng.standard_normal((100, 7))
    p = torch.tensor(th0, dtype=torch.float64, requires_grad=True)
    opt = kur_torch([p])
    th, m, v, t = th0.copy(), np.zeros(7), np.zeros(7), 0
    v_mom = np.zeros(7)
    en_kotu = 0.0
    for k in range(100):
        p.grad = torch.tensor(gs[k], dtype=torch.float64)
        opt.step()
        if ad.startswith("momentum"):
            th, v_mom = sgd_momentum(th, gs[k], v_mom, 0.05, 0.9)
        elif ad.startswith("nesterov"):
            th, v_mom = sgd_nesterov(th, gs[k], v_mom, 0.05, 0.9)
        elif ad.startswith("adamw"):
            th, m, v, t = adamw_adim(th, gs[k], m, v, t, 0.01, 0.05)
        elif ad.startswith("adam_l2"):
            th, m, v, t = adam_l2_adim(th, gs[k], m, v, t, 0.01, 0.05)
        else:
            th, m, v, t = adam_adim(th, gs[k], m, v, t, 0.01)
        en_kotu = max(
            en_kotu, np.max(np.abs(th - p.detach().numpy()))
        )
```
```python
    kontrol(ad, en_kotu)


optim_karsilastir(
    None,
    lambda ps: torch.optim.SGD(ps, lr=0.05, momentum=0.9),
    "momentum (torch SGD)",
)
optim_karsilastir(
    None,
    lambda ps: torch.optim.SGD(
        ps, lr=0.05, momentum=0.9, nesterov=True
    ),
    "nesterov (torch SGD)",
)
optim_karsilastir(
    None,
    lambda ps: torch.optim.Adam(ps, lr=0.01),
    "adam (torch Adam)",
)
optim_karsilastir(
    None,
    lambda ps: torch.optim.AdamW(ps, lr=0.01, weight_decay=0.05),
    "adamw (torch AdamW)",
)
optim_karsilastir(
    None,
    lambda ps: torch.optim.Adam(ps, lr=0.01, weight_decay=0.05),
    "adam_l2 (torch Adam+wd)",
)
```
```python
# ---- B. Adam'in ilk 3 adimi (kitaptaki iz tablosu icin) ----
print("\nAdam iz tablosu: theta0=1.0, lr=0.1, g=[0.5,-0.2,0.1]")
th, m, v, t = 1.0, 0.0, 0.0, 0
for g in [0.5, -0.2, 0.1]:
    th_onceki = th
    th, m, v, t = adam_adim(th, g, m, v, t, lr=0.1)
    mh = m / (1 - 0.9**t)
    vh = v / (1 - 0.999**t)
    print(
        "t=%d g=%+.2f m=%.5f v=%.6f mh=%.5f vh=%.6f theta=%.6f"
        % (t, g, m, v, mh, vh, th)
    )
```
```python
# ---- C. BatchNorm: ileri, geri, gradyan denetimi ----
N, D = 16, 5
x = rng.standard_normal((N, D))
gam = rng.standard_normal(D)
bet = rng.standard_normal(D)
dy = rng.standard_normal((N, D))
y_np, cache, mu, var = bn_ileri(x, gam, bet)
xt = torch.tensor(x, dtype=torch.float64, requires_grad=True)
bn = torch.nn.BatchNorm1d(D, eps=1e-5).double()
with torch.no_grad():
    bn.weight.copy_(torch.tensor(gam))
    bn.bias.copy_(torch.tensor(bet))
yt = bn(xt)
kontrol(
    "BN ileri (egitim) vs torch",
    np.max(np.abs(y_np - yt.detach().numpy())),
)
yt.backward(torch.tensor(dy))
dx, dg, db = bn_geri(dy, cache)
kontrol(
    "BN dx vs torch autograd", np.max(np.abs(dx - xt.grad.numpy()))
)
kontrol(
    "BN dgamma vs torch", np.max(np.abs(dg - bn.weight.grad.numpy()))
)
kontrol(
    "BN dbeta vs torch", np.max(np.abs(db - bn.bias.grad.numpy()))
)
```
```python
# sayisal gradyan (float64): kaybi L = sum(dy * y)
def kayip(xx):
    yy, _, _, _ = bn_ileri(xx, gam, bet)
    return float(np.sum(dy * yy))


h = 1e-6
sayisal = np.zeros_like(x)
for i in range(N):
    for j in range(D):
        e = np.zeros_like(x)
        e[i, j] = h
        sayisal[i, j] = (kayip(x + e) - kayip(x - e)) / (2 * h)
kontrol(
    "BN dx sayisal gradyan (merkezi fark)",
    np.max(np.abs(sayisal - dx)),
    esik=1e-6,
)
```
```python
# running istatistikler: torch running_var BESSEL duzeltmeli
rm = 0.1 * mu
rv = 0.9 * np.ones(D) + 0.1 * var * N / (N - 1)
bn2 = torch.nn.BatchNorm1d(D).double()
bn2.train()
bn2(torch.tensor(x, dtype=torch.float64))
kontrol(
    "BN running_mean vs torch",
    np.max(np.abs(bn2.running_mean.numpy() - rm)),
)
kontrol(
    "BN running_var vs torch (N-1 duzeltmeli)",
    np.max(np.abs(bn2.running_var.numpy() - rv)),
)
bn2.eval()
yc = bn_cikarim(
    x,
    np.ones(D),
    np.zeros(D),
    bn2.running_mean.numpy(),
    bn2.running_var.numpy(),
)
kontrol(
    "BN cikarim (eval) vs torch",
    np.max(np.abs(yc - bn2.eval()(torch.tensor(x)).detach().numpy())),
)
```
```python
# ---- D. Dropout: ters olcekleme ----
p = 0.3
xd = rng.standard_normal((4, 6))
yt_d = F.dropout(torch.tensor(xd), p=p, training=True)
maske_t = np.where(yt_d.numpy() != 0, 1 / (1 - p), 0.0)
ornek = xd * maske_t
kontrol(
    "Dropout ters-olcek (ayni maske)",
    np.max(np.abs(ornek - yt_d.numpy())),
)
y_e, _ = dropout_ileri(xd, p, False, rng)
kontrol("Dropout cikarimda kimlik", np.max(np.abs(y_e - xd)))
buyuk = rng.standard_normal((200000,))
ort = dropout_ileri(buyuk, p, True, rng)[0].mean()
print(
    "Dropout beklenen deger kontrolu: E[y]=%.4f, E[x]=%.4f"
    % (ort, buyuk.mean())
)
```
```python
# ---- E. Ogrenme orani takvimleri: torch ile karsilastirma ----
w = torch.nn.Parameter(torch.zeros(1))
opt = torch.optim.SGD([w], lr=0.1)
sch = torch.optim.lr_scheduler.CosineAnnealingLR(
    opt, T_max=100, eta_min=0.001
)
cos_t, cos_n = [], []
for t in range(100):
    cos_t.append(opt.param_groups[0]["lr"])
    cos_n.append(lr_kosinus(t, 100, 0.1, 0.001))
    opt.step()
    sch.step()
kontrol(
    "Kosinus zamanlayici vs torch",
    np.max(np.abs(np.array(cos_t) - cos_n)),
    1e-9,
)
opt = torch.optim.SGD([w], lr=0.1)
sch = torch.optim.lr_scheduler.StepLR(opt, step_size=30, gamma=0.5)
st_t = []
for t in range(90):
    st_t.append(opt.param_groups[0]["lr"])
    opt.step()
    sch.step()
st_n = [lr_adim_kurali(t, 0.1, 0.5, 30) for t in range(90)]
kontrol(
    "Basamakli (StepLR) vs torch",
    np.max(np.abs(np.array(st_t) - st_n)),
    1e-12,
)
opt = torch.optim.SGD([w], lr=0.1)
sch = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.98)
ex_t = []
for t in range(90):
    ex_t.append(opt.param_groups[0]["lr"])
    opt.step()
    sch.step()
ex_n = [lr_ustel(t, 0.1, 0.98) for t in range(90)]
kontrol(
    "Ustel (ExponentialLR) vs torch",
    np.max(np.abs(np.array(ex_t) - ex_n)),
    1e-12,
)
```
```python
# ---- F. Gradyan kirpma: torch ile ----
gl = [rng.standard_normal((3, 4)) * 5, rng.standard_normal(7) * 5]
kirp_np, nrm = norm_kirp([g.copy() for g in gl], 1.0)
ps = [torch.tensor(g.copy(), requires_grad=True) for g in gl]
for pt, g in zip(ps, gl):
    pt.grad = torch.tensor(g.copy())
tn = torch.nn.utils.clip_grad_norm_(ps, 1.0)
fark = max(
    np.max(np.abs(a - b.grad.numpy())) for a, b in zip(kirp_np, ps)
)
kontrol("Gradyan kirpma vs torch clip_grad_norm_", fark)
print("norm (onceki):", round(nrm, 4), " torch:", round(float(tn), 4))

print("\nTOPLAM: %d/%d kontrol gecti" % (sum(sonuc), len(sonuc)))
```
```term
$ python test_np64.py
momentum (torch SGD)                   max fark = 0.000e+00   TAMAM
nesterov (torch SGD)                   max fark = 0.000e+00   TAMAM
adam (torch Adam)                      max fark = 1.110e-16   TAMAM
adamw (torch AdamW)                    max fark = 2.220e-16   TAMAM
adam_l2 (torch Adam+wd)                max fark = 2.220e-16   TAMAM

Adam iz tablosu: theta0=1.0, lr=0.1, g=[0.5,-0.2,0.1]
t=1 g=+0.50 m=0.05000 v=0.000250 mh=0.50000 vh=0.250000 theta=0.900000
t=2 g=-0.20 m=0.02500 v=0.000290 mh=0.13158 vh=0.144947 theta=0.865439
t=3 g=+0.10 m=0.03250 v=0.000299 mh=0.11993 vh=0.099920 theta=0.827500
BN ileri (egitim) vs torch             max fark = 8.882e-16   TAMAM
BN dx vs torch autograd                max fark = 6.661e-16   TAMAM
BN dgamma vs torch                     max fark = 1.776e-15   TAMAM
BN dbeta vs torch                      max fark = 8.882e-16   TAMAM
BN dx sayisal gradyan (merkezi fark)   max fark = 1.440e-09   TAMAM
BN running_mean vs torch               max fark = 6.939e-18   TAMAM
BN running_var vs torch (N-1 duzeltmeli) max fark = 0.000e+00   TAMAM
BN cikarim (eval) vs torch             max fark = 4.441e-16   TAMAM
Dropout ters-olcek (ayni maske)        max fark = 0.000e+00   TAMAM
Dropout cikarimda kimlik               max fark = 0.000e+00   TAMAM
Dropout beklenen deger kontrolu: E[y]=0.0047, E[x]=0.0039
Kosinus zamanlayici vs torch           max fark = 3.469e-17   TAMAM
Basamakli (StepLR) vs torch            max fark = 0.000e+00   TAMAM
Ustel (ExponentialLR) vs torch         max fark = 1.388e-17   TAMAM
Gradyan kirpma vs torch clip_grad_norm_ max fark = 0.000e+00   TAMAM
norm (onceki): 14.9651  torch: 14.9651

TOPLAM: 19/19 kontrol gecti
```

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'te tarif edilen altı adımlı yöntemi izler. Her örnekte önce problemi anlarsın, küçük bir girdiyle denersin, kaba bir çözüm bulur, bu çözümdeki örüntüyü görür, iyileştirir ve sonunda elle yaptığın izle doğrularsın.

### Örnek 1 (★): Adam'ın ilk üç adımını elle izlemek

**Adım 1 — Anla.** Tek bir parametre θ, başlangıçta 1,0'dır. Öğrenme oranı η = 0,1, β₁ = 0,9, β₂ = 0,999 ve ε = 10⁻⁸ alınır. İlk üç adımda gradyanlar sırasıyla 0,5, −0,2 ve 0,1'dir. Soru: her adımda θ ne olur ve sapma düzeltmesi neyi değiştirir?

**Adım 2 — Örnekle.** İlk adımın değerlerini elle yap: m = 0,1 · 0,5 = 0,05; v = 0,001 · 0,25 = 0,00025. Sapma düzeltmesinden sonra m̂ = 0,05 / (1 − 0,9) = 0,5 ve v̂ = 0,00025 / (1 − 0,999) = 0,25. Güncelleme η · m̂/√v̂ = 0,1 · 0,5/0,5 = 0,1, yani θ = 0,9.

**Adım 3 — Kaba çöz.** Her adımda m, v ve ardından m̂ ve v̂ hesaplanır; θ, η m̂/(√v̂ + ε) kadar değişir. Bu, her adımı aynı yolla sürdürmek demektir.

**Adım 4 — Örüntü.** İkinci adımda gradyan işaret değiştirdi, m azaldı (0,05'ten 0,025'e). Üçüncü adımda gradyan tekrar pozitif ama küçük. Sapma düzeltmesi, ilk adımlarda 1 − β₁ᵗ ve 1 − β₂ᵗ paydalarının küçük olmasından dolayı m̂ ve v̂'yi büyütür; t büyüdükçe bu büyütme azalır.

**Adım 5 — İyileştir.** Kaba çözüm zaten doğrudur; ama adım büyüklüğünü ölçeğe bağımlı olmayacak biçimde görmek için v̂'nin kökünü ve m̂'yi birlikte takip etmek yeterlidir. İyileştirme yerine ölçü birimi kontrolü yap: bu güncelleme birimsizdir (η'nın birimi dışında), yani gradyan 100 kat büyüse de adım aynı kalır.

**Adım 6 — Doğrula.** Aşağıdaki tabloyu programın çıktısıyla karşılaştır.

| Adım t | g | m | v | m̂ | v̂ | θ |
|---|---|---|---|---|---|---|
| 1 | +0,50 | 0,05000 | 0,000250 | 0,50000 | 0,25000 | 0,900000 |
| 2 | −0,20 | 0,02500 | 0,000290 | 0,13158 | 0,14495 | 0,865439 |
| 3 | +0,10 | 0,03250 | 0,000299 | 0,11993 | 0,09992 | 0,827500 |

İkinci adımda elle hesap: m = 0,9 · 0,05 + 0,1 · (−0,2) = 0,025 ✓; v = 0,999 · 0,00025 + 0,001 · 0,04 = 0,00028975 ✓; m̂ = 0,025/0,19 = 0,13158 ✓; v̂ = 0,00028975/0,001999 = 0,14495 ✓; θ = 0,9 − 0,1 · 0,13158/√0,14495 = 0,9 − 0,03456 = 0,86544 ✓.

**Bunu AI'sız yazabilir misin?** Gradyan dizisini 0,5, −0,2, 0,1 yerine −1, −1, −1 yap ve θ'nın her adımda neden aynı büyüklükte değiştiğini açıkla. Sapma düzeltmesi olmadan aynı adım ne olurdu?

### Örnek 2 (★★): Dört örneklik batch'te BatchNorm'un ileri ve geri geçişi

**Adım 1 — Anla.** Dört skaler girdi x = [1, 3, 5, 7] var. BatchNorm çıktısı y = γx̂ + β, γ = 2, β = 1. Hem ileri geçişi hem de geri geçişte dβ, dγ ve dx'i hesaplamak gerekir; geri geçişte yalnızca ilk örneğe 1 gradyanı verildiğini varsay.

**Adım 2 — Örnekle.** Ortalama μ = (1 + 3 + 5 + 7)/4 = 4. Sapmalar −3, −1, 1, 3; kareleri 9, 1, 1, 9; yanlı varyans σ² = 20/4 = 5. √5 ≈ 2,2361.

**Adım 3 — Kaba çöz.** x̂ᵢ = (xᵢ − 4)/2,2361 → [−1,3416, −0,4472, 0,4472, 1,3416]. y = 2x̂ + 1 → [−1,6833, 0,1056, 1,8944, 3,6833]. Geri geçiş için dγ = Σ dy x̂ = x̂₁ = −1,3416, dβ = 1, dx'i türev formülüyle hesapla.

**Adım 4 — Örüntü.** Girdinin ölçeği ne olursa olsun x̂ aynı ölçekte kalır ve dx'in toplamı sıfırdır; bu, BatchNorm'un batch ortalamasına bağlı bir kaymaya karşı duyarsız olduğunun cebirsel nedenidir. Bu örnekte dx₁ en büyük pozitif, dx₂ ise en büyük negatif değerdir; gradyan batch içinde birbirini dengeleyen bir dağılım olarak paylaşılır.

**Adım 5 — İyileştir.** Geri geçiş formülünü her seferinde tüm batch'ten topluca hesaplamak yerine, dxᵢ = (γ/(Nσ))(N dyᵢ − Σdy − x̂ᵢ Σ dy x̂) biçiminde yazmak, hem hesabı hem de sıfır toplam özelliğini açıkça gösterir.

**Adım 6 — Doğrula.** Programın çıktısı şu:

| i | xᵢ | x̂ᵢ | yᵢ | dxᵢ (dy = [1,0,0,0]) |
|---|---|---|---|---|
| 1 | 1 | −1,3416 | −1,6833 | 0,2683 |
| 2 | 3 | −0,4472 | 0,1056 | −0,3578 |
| 3 | 5 | 0,4472 | 1,8944 | −0,0894 |
| 4 | 7 | 1,3416 | 3,6833 | 0,1789 |

Elle dx₁ hesabı: dxh₁ = γ · 1 = 2; Σdxh = 2; Σ(dxh x̂) = 2 · (−1,3416) = −2,6833. dx₁ = (1/(4 · 2,2361)) · (4 · 2 − 2 − (−1,3416)(−2,6833)) = (1/8,944) · (8 − 2 − 3,6) = 2,4/8,944 = 0,2683 ✓. Toplam: 0,2683 − 0,3578 − 0,0894 + 0,1789 = 0 ✓.

**Bunu AI'sız yazabilir misin?** Aynı girdiyle γ = 2 yerine γ = 0 yap; dx ne olur ve neden? Bu sonuç, γ'nın gradyan akışında oynadığı rolü gösterir.

### Örnek 3 (★★): Isınma + kosinüs takviminin belirli adımlardaki değerleri

**Adım 1 — Anla.** W = 30 adım ısınma, toplam T = 300 adım, η_max = 0,01 ve η_min = 0 alınır. Ön ısınmada öğrenme oranı doğrusal artar, sonra kosinüs ile azalır. Soru: t = 0, 29, 30, 165 ve 299 adımlarında öğrenme oranı nedir?

**Adım 2 — Örnekle.** t = 0'da ısınma formülü η_max · (t + 1)/W = 0,01 · 1/30 = 0,000333. t = 29'da 0,01 · 30/30 = 0,01 (ısınmanın son adımı). t = 30'da kosinüs başlar: ilerleme (t − W)/(T − W) = 0, yani η = η_max = 0,01.

**Adım 3 — Kaba çöz.** Kosinüs kısmı η(t) = η_min + ½(η_max − η_min)(1 + cos(π · ilerleme)) formülüdür. t = 165 için ilerleme = (165 − 30)/270 = 0,5 ve cos(π/2) = 0; η = ½ · 0,01 · (1 + 0) = 0,005.

**Adım 4 — Örüntü.** Isınma ile kosinüs arasında bir süreklilik vardır: ısınmanın sonunda η_max'a ulaşılır ve kosinüs tam bu değerden başlar. Kosinüsün bitişinde ise η sıfıra yaklaşır; t = 299'da ilerleme 269/270'tir ve cos(π · 0,9963) ≈ −0,99993, dolayısıyla η ≈ 3 × 10⁻⁷.

**Adım 5 — İyileştir.** Formülü her adım için yeniden hesaplamak yerine yalnızca bu iki bölgeyi (ısınma ve kosinüs) ayrı tutmak yeterlidir; kod da zaten böyle.

**Adım 6 — Doğrula.** Aşağıdaki program aynı değerleri üretir (`takvim_ornek.py`). Çıktı da kontrol için yazdırıldı.

```python
# -*- coding: utf-8 -*-
"""Isinma + kosinus takviminin secilen adimlardaki degerleri."""

from egitim_np import lr_isinma_kosinus

W, T, lr_max = 30, 300, 0.01
for t in [0, 1, 15, 29, 30, 165, 299]:
    lr = lr_isinma_kosinus(t, W, T, lr_max, 0.0)
    print("adim %3d   lr = %.6f" % (t, lr))
```

```term
$ python takvim_ornek.py
adim   0   lr = 0.000333
adim   1   lr = 0.000667
adim  15   lr = 0.005333
adim  29   lr = 0.010000
adim  30   lr = 0.010000
adim 165   lr = 0.005000
adim 299   lr = 0.000000
```

Elle hesap ile tablo eşleşiyor: t = 0 ve t = 165 değerleri, Adım 2 ve Adım 3'teki hesaplarla aynı. t = 299 için sıfıra çok yakın bir değer çıkar (yuvarlamada 0,000000 görünür).

**Bunu AI'sız yazabilir misin?** Isınmayı 0'dan değil de 0,001'den başlatmak için formülü nasıl değiştirirsin? Kosinüsün son değerinin η_min'e ulaşması için T'yi nasıl seçmelisin?

### Örnek 4 (★★★): Bozuk bir eğitim betiğini ayıklamak

**Adım 1 — Anla.** Yukarıdaki betik, iki katmanlı bir dropout'lu MLP'yi 15 epoch eğitiyor. Çıktıda eğitim kaybı yükselmiş, doğruluk şans düzeyine (0,10) düşmüş. Görev: en az üç hatayı bul ve her birinin hangi belirtiye yol açtığını açıkla.

**Adım 2 — Örnekle.** İlk iki epoch'a bak: kayıp 2,149'dan 2,487'ye çıkıyor. Doğrulama doğruluğu 0,345'ten 0,200'e düşüyor. Bu kadar erken bir düşüş, öğrenme oranının ya da birikmiş gradyanların sonucu olabilir.

**Adım 3 — Kaba çöz.** Kodu satır satır oku. Üç olası hata: (a) `opt.zero_grad()` çağrısı yok; (b) doğruluk fonksiyonunda `model.eval()` yok; (c) "dogrulama" ölçümü `Xtr, ytr` ile yapılıyor.

**Adım 4 — Örüntü.** (a) Gradyanlar her adımda birikiyor. Adam'ın ikinci momenti bu biriken büyük gradyanları yakalayınca adım boyları patlıyor ve kayıp salınıyor. (b) Doğruluk hesabı dropout maskesi altında yapılıyor; bu yüzden aynı betik her çalıştırmada biraz farklı doğruluk verir. (c) Ölçüm eğitim verisi üzerinde yapıldığı için rakam bir doğrulama değil, eğitim doğruluğudur; test kümesi ile bir tutarsızlık ancak bu hatalar düzeltildiğinde görünür olur.

**Adım 5 — İyileştir.** Düzeltme üç değişiklik gerektirir: `opt.zero_grad()` her adımdan önce; doğruluk hesabında `model.eval()`; doğrulama için `Xva, yva`. Düzeltilmiş betik (`bozuk_egitim_duzeltilmis.py`) ayrıca her epoch başında `model.train()` içerir.

Düzeltilmiş betik aşağıdadır; üç hatanın düzeltilmiş hâlini içerir. Çıktı, bozuk betikle aynı ölçümleri verir:

```python
# -*- coding: utf-8 -*-
"""Bolum 64 - Cozumlu Ornek 4: duzeltilmis egitim betigi."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri

Xtr, ytr, Xva, yva, Xte, yte = veri()
torch.manual_seed(0)
model = nn.Sequential(
    nn.Linear(64, 128),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(128, 128),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(128, 10),
)
opt = torch.optim.Adam(model.parameters(), lr=1e-2)


def dogruluk(X, y):
    model.eval()
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


for ep in range(15):
    model.train()
    perm = torch.randperm(len(Xtr))
    kayip = 0.0
    for i in range(0, len(Xtr), 32):
        idx = perm[i : i + 32]
        opt.zero_grad()
        loss = F.cross_entropy(model(Xtr[idx]), ytr[idx])
        loss.backward()
        opt.step()
        kayip += loss.item()
    print(
        "ep %2d  kayip=%.4f  dogrulama=%.4f"
        % (ep + 1, kayip / (len(Xtr) / 32), dogruluk(Xva, yva))
    )
print("son test dogrulugu = %.4f" % dogruluk(Xte, yte))
```
```term
$ python bozuk_egitim_duzeltilmis.py
ep  1  kayip=1.5160  dogrulama=0.7521
ep  2  kayip=0.7175  dogrulama=0.8942
ep  3  kayip=0.4754  dogrulama=0.9415
ep  4  kayip=0.4046  dogrulama=0.9359
ep  5  kayip=0.3373  dogrulama=0.9443
ep  6  kayip=0.3519  dogrulama=0.9415
ep  7  kayip=0.3247  dogrulama=0.9415
ep  8  kayip=0.2941  dogrulama=0.9471
ep  9  kayip=0.2451  dogrulama=0.9638
ep 10  kayip=0.2880  dogrulama=0.9359
ep 11  kayip=0.2865  dogrulama=0.9359
ep 12  kayip=0.2790  dogrulama=0.9582
ep 13  kayip=0.2117  dogrulama=0.9499
ep 14  kayip=0.3422  dogrulama=0.9610
ep 15  kayip=0.2895  dogrulama=0.9526
son test dogrulugu = 0.9472
```

**Adım 6 — Doğrula.** Düzeltilmiş betiğin sonucu: 15 epoch sonunda eğitim kaybı 0,29, doğrulama doğruluğu 0,9526, test doğruluğu 0,9472. Eğitim kaybı 1. epoch'ta 1,516 iken 15. epoch'ta 0,29'a düşüyor. Bozuk betiğin sonunda test 0,0972 idi. İki betiğin farkı birkaç satırdır; çıktıdaki her değişikliği bu satırlara bağlayabiliyorsun.

**Bunu AI'sız yazabilir misin?** Betiğe, doğrulama kaybı üç epoch boyunca düşmezse eğitimi durduran bir erken durdurma ekle. Hangi değişkenleri her epoch kaydetmek gerektiğini ve bunların neden olduğunu açıkla.

## Kendin Yap Projeleri

::: dikkat
Aşağıdaki projelerde yapay zekâ aracı kullanmadan çalış. Amaç, eğitim döngüsünü, optimizer güncellemelerini ve teşhis mantığını kendi elinle kurmaktır. Bir hata çıktığında hatayı önce kendin bulmaya çalış, sonra kayıp eğrisine ve kod satırlarına dön. Yardım istemeden önce kendi ölçümlerini ve notlarını topla.
:::

### Proje 1 (★★): NumPy çatısına Adam, AdamW, BatchNorm, dropout ve zamanlayıcı eklemek

**Amaç.** Bölüm 63'teki NumPy MLP'sini (sinir ağı çatısı) bu bölümde gördüğün teknikleriyle genişlet. Ağ, her gizli katmandan sonra isteğe bağlı BatchNorm ve dropout içermeli; optimizer olarak SGD, momentum, Adam ve AdamW seçilebilmeli; öğrenme oranı bir zamanlayıcıdan gelmeli.

**Yapılacak / Beklenen davranış.** (1) Her optimizer için bir güncelleme fonksiyonu yaz ve ayrı bir test dosyasında PyTorch'un `torch.optim` karşılığıyla 50 adım boyunca karşılaştır; fark 10⁻⁹'dan küçük olmalı. (2) BatchNorm'un ileri ve geri geçişini yaz; sayısal gradyan denetimi (merkezi fark) ve PyTorch `nn.BatchNorm1d` ile eşleşmesini göster. (3) Dropout'u ters ölçekli yaz; eğitim ve çıkarım modunu bir `egitim` bayrağıyla ayır. (4) Kosinüs ve ısınma takvimini uygula; PyTorch zamanlayıcısıyla karşılaştır. (5) Bu parçaları `load_digits` üzerinde bir MLP ile birleştir ve 3 tohumla test doğruluğu raporla.

**Önerilen yaklaşım.** Her güncelleme fonksiyonunu saf bir fonksiyon olarak yaz: girdi olarak parametreyi, gradyanı ve durumu al; yeni parametre ve durumu döndür. Sapma düzeltmesi için adım sayacını durumun içinde tut. BatchNorm'un geri geçişinde önbelleğe aldığın değerlerin (x̂, σ², γ) hangi adımda kullanıldığını bir çizimle düşün. Test dosyasında her karşılaştırmayı tek bir fonksiyonla yap ki hangi kontrolün başarısız olduğu hemen görünsün.

**Başarı kriterleri.** (a) Dört optimizer için PyTorch ile fark 10⁻⁹'dan küçük. (b) BatchNorm dx sayısal gradyanla 10⁻⁶'dan küçük fark. (c) Dropout'un çıkarım modunda kimlik olduğu test edilmiş. (d) Test doğruluğu üç tohum ortalama ± sapma olarak raporlanmış ve test kümesi hiçbir karar için kullanılmamış. (e) Her deney için tohum, lr ve batch bilgisini içeren bir kayıt dosyası üretilmiş.

### Proje 2 (★★★): Eğitim doktoru — kural tabanlı teşhis aracı

**Amaç.** Bir eğitim koşusunun kayıt dosyasını (her epoch için eğitim kaybı, doğrulama kaybı, doğrulama doğruluğu, öğrenme oranı ve gradyan normu) okuyan ve olası sorunları teşhis eden bir araç yaz. Araç, bu bölümde gördüğün belirtileri kurallara dökmeli: yüksek lr, düşük lr, aşırı uydurma, yetersiz uydurma, veri sızıntısı şüphesi, etiket gürültüsü ve NaN.

**Yapılacak / Beklenen davranış.** Araç bir CSV dosyası alır ve bir teşhis raporu üretir. Her teşhis için hangi kuralın tetiklendiğini, hangi epoch'ta ve hangi değerle tetiklendiğini yazar. Kurallar birbiriyle çelişmemeli ve en az bir tanesi "sağlıklı" çıktısı vermeli. Aracı, bu bölümdeki yedi vakanın gerçek kayıtlarıyla (engine/veri içindeki `b64_teshis.csv`) ve ayrıca kasıtlı olarak bozulmuş beş yeni kayıtla test et. Her bozulmuş kayıt için aracın doğru teşhisi bulup bulmadığını raporla.

**Önerilen yaklaşım.** Kuralları küçük ve bağımsız fonksiyonlar olarak yaz: her biri bir kayıt dizisi alıp bir teşhis ya da `None` döndürsün. Eşikleri (ör. "doğrulama kaybı son 10 epoch'ta yükseliyor") sabit değerler olarak değil parametre olarak tanımla ve farklı eşiklerle hangi teşhislerin kararlı kaldığını gözle. NaN'ı kontrol etmeyi en başa koy. Her kural için yanlış pozitif riskini düşün: sızıntı kuralı, doğrulama ile test arasındaki farkı ölçmeden çalışamaz; bu yüzden aracın test kaydını da girdi olarak alabilmesi gerekebilir.

**Başarı kriterleri.** (a) Yedi gerçek vakanın en az altısında doğru ana teşhis. (b) Beş kasıtlı bozulmuş kayıtta en az dördünde doğru teşhis. (c) Sağlıklı bir koşu için hiçbir kural tetiklenmiyor. (d) Her teşhis, dayandığı epoch ve değeri raporluyor. (e) Eşiklerin değişimine karşı hangi teşhisin kararlı olduğunu gösteren kısa bir analiz.

### Ek Alıştırmalar

1. ★ Adam'da β₁ = 0,9 iken ilk gradyan g = 2 ise ilk adımdan sonra m ve sapma düzeltmeli m̂ değerlerini hesapla.
2. ★ Momentum μ = 0,9 ve sabit gradyan g iken hızın kararlı değeri nedir? (İpucu: v = μv + g denklemini sabit noktada çöz.)
3. ★★ Mülakat: Adam neden sapma düzeltmesi yapar? β₂ = 0,999 için 1000. adımda 1 − β₂ᵗ ne kadardır ve v̂ hangi oranda büyür?
4. ★★ Mülakat: BatchNorm'un eğitim ve çıkarım davranışı neden farklıdır? `model.eval()` unutulursa tahminler neden değişir?
5. ★★ Mülakat: Loss NaN oldu. İlk olarak hangi üç şeyi kontrol edersin ve neden bu sırayla?
6. ★★ Bir batch'te N = 4 ve D = 1 için BatchNorm'un dx toplamının sıfır olduğunu cebirle göster.
7. ★★ Dropout p = 0,5 ile ters ölçekleme yapılırken bir aktivasyonun eğitimdeki beklenen değeri neden değişmez? Varyansı nasıl değişir?
8. ★★ Mülakat: Eğitim kaybı düşerken doğrulama kaybı yükseliyor. İki olası neden ve bunlara karşı üç müdahale nedir?
9. ★★★ Kosinüs takviminde ısınma adımı W = 0 olursa (t + 1)/W ifadesi ne olur? Isınma olmadan kosinüs takvimi kullanmanın kararlılık riskini açıkla.
10. ★★★ Mülakat: Derin bir ağda ilk katmanın gradyanı 10⁻¹² mertebesinde. Olası nedenleri ve düzeltme yollarını sırala.
11. ★★★ Bir koşuda doğrulama doğruluğu tek bir epoch'ta 0,95'ten 0,10'a düştü. Üç olası neden ve her biri için yapılacak bir ölçüm öner.
12. ★★★ Mülakat: Izgara ve rastgele arama arasında hangi koşulda ızgara daha iyidir? Bu bölümdeki deneyden bir örnek ver.

## Kod Okuma Egzersizi

Bu bölümde Adam ve AdamW'nin güncelleme kuralını teoride ve NumPy'de gördük. Şimdi aynı kuralın PyTorch'taki uygulamasına bakalım. Kaynak: PyTorch 2.6.0, `torch/optim/adam.py` dosyası, `_single_tensor_adam` fonksiyonu (yerel kurulum: `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\optim\adam.py`, satır 423 – 478). Aşağıdaki alıntı, fonksiyonun tek tensörlü yolundan alındı. Kaynak satırları birebir kopyalandı; yalnızca iki şey yapıldı: capturable/differentiable dalı ile amsgrad dalı bu bölümün kapsamı dışında olduğu için yorumla atlandı, ve 70 karakterlik kitap genişliği için iki satır kırıldı (ifade değişmedi).

```python
        # Decay the first and second moment running average
        # coefficient
        exp_avg.lerp_(grad, 1 - device_beta1)

        exp_avg_sq.mul_(beta2).addcmul_(
            grad, grad.conj(), value=1 - beta2
        )

        # ... capturable/differentiable dali atlandi (satir 427-459)

        else:
            step = _get_value(step_t)

            bias_correction1 = 1 - beta1**step
            bias_correction2 = 1 - beta2**step

            step_size = lr / bias_correction1

            bias_correction2_sqrt = bias_correction2**0.5

            # ... amsgrad dali atlandi (satir 469-474)

            denom = (
                exp_avg_sq.sqrt() / bias_correction2_sqrt
            ).add_(eps)

            param.addcdiv_(exp_avg, denom, value=-step_size)
```

İlk satır birinci momenti `lerp_` ile günceller: exp_avg ← exp_avg + (1 − β₁)(grad − exp_avg). Bu, β₁m + (1 − β₁)g ile aynıdır. İkinci satır ikinci momenti aynı biçimde günceller. Sapma düzeltmesi `bias_correction1` ve `bias_correction2` ile yapılır; bunlar 1 − β₁ᵗ ve 1 − β₂ᵗ değerleridir. Adım boyu `step_size = lr / bias_correction1` olarak alınır ve paydadaki `denom`, √v / √(1 − β₂ᵗ) + ε'dir. Son satır `addcdiv_(exp_avg, denom, value=-step_size)` ile güncellemeyi uygular: sonuç −η · (m/(1 − β₁ᵗ)) / (√v/√(1 − β₂ᵗ) + ε), yani −η · m̂ / (√v̂ + ε). ε, düzeltilmiş kökün dışında eklenir; bu, NumPy kodumuzdaki `np.sqrt(vh) + eps` ifadesiyle aynıdır.

**Weight decay'in yeri.** Adam'da ağırlık azaltma, bu alıntıdan önce, `adam.py` içinde `if weight_decay != 0: grad = grad.add(param, alpha=weight_decay)` satırıyla gradyana eklenir (yaklaşık 397–398. satırlar). AdamW'de ise gradyanlara dokunulmadan önce ağırlık doğrudan küçültülür: `param.mul_(1 - lr * weight_decay)` (`adamw.py` içinde, yaklaşık 405. satır). Bu tek satır, Adam ile AdamW arasındaki farkın özüdür.

**Sorular — cevaplamadan geçme:**

1. `exp_avg.lerp_(grad, 1 - device_beta1)` ifadesi, `β₁ m + (1 − β₁) g` ile matematiksel olarak eşdeğer mi? Hangi tür yuvarlama farkı oluşabilir?
2. Sapma düzeltmesi paydası `1 - beta2**step` ile `step` büyüdüğünde ne olur? Bu, erken adımlar ile geç adımlar arasındaki farkı nasıl değiştirir?
3. Adam'da L2 azaltması gradyanı değiştirir: grad.add(param, alpha=wd). Bu eklemenin v (ikinci moment) üzerindeki etkisini açıkla. Büyük gradyanlı bir parametrede azaltma neden zayıflar?
4. AdamW'de `param.mul_(1 - lr * weight_decay)` adımı, gradyanın ikinci momentine hiç girmez. Bu, azaltmanın hangi parametrelerde daha güçlü olacağı konusunda ne anlama gelir?
5. Kaynakta `step` değişkeni `_get_value(step_t)` ile alınır. Bu adım sayacı neden bir tensör olarak tutulur, düz bir Python tamsayısı olarak değil? (İpucu: `capturable` modu ve GPU üzerinde CUDA grafiği.)
6. Eğer `eps` değerini 10⁻⁸ yerine 10⁻¹⁵ alırsan, hangi koşulda sonuç gözle görülür biçimde değişir? Bu bir sayısal kararlılık sorunu mudur?

## Bölüm Özeti

- Eğitim bir deney disiplinidir: tek değişken, tohum tekrarı ve ayrı test kümesi. Başlangıç kaybını (C sınıf için ln C) kontrol etmek ilk teşhis adımıdır.
- Mini-batch gradyan gürültüsü batch ile ters orantılı azalır; batch ve öğrenme oranı birlikte seçilir. Büyük batch'te doğrusal ölçek bile kararsızlaşabilir.
- Momentum ve Nesterov hız biriktirir; Adam gradyan ölçeğinden bağımsız adım boyu verir ve sapma düzeltmesi ilk adımları telafi eder. AdamW, ağırlık azaltmayı gradyandan ayırır ve bunun farkı PyTorch kaynağında tek satırdır.
- Öğrenme oranı en önemli hiperparametredir. LR aralık testi üst sınırı ölçer; kosinüs ve ısınma + kosinüs, derin ve büyük ağlarda kararlılığı artırır.
- Başlatma sinyali derin ağda korumak zorundadır: küçük sabit başlatma 20 katmanda sinyali sıfıra çökertir; He ve BatchNorm sinyali korur. Artık bağlantılarda son katmanı sıfır başlatmak gradyanı sağlıklı tutar.
- BatchNorm'un ileri ve geri geçişi türetilip sayısal ve PyTorch ile doğrulandı; eval modu ve küçük batch tuzakları ölçüldü. Dropout ters ölçeklemeyle eğitimde uygulanır; etiket yumuşatma doğruluğu artırabilir ama kalibrasyonu bozabilir.
- Gradyan kırpma patlayan gradyanı yönünü koruyarak sınırlar; artık bağlantı kaybolan gradyanı yapısal olarak giderir.
- Eğitim hatası ayıklamada loss eğrisi kataloğu (yüksek ve düşük lr, aşırı ve yetersiz uydurma, sızıntı, etiket gürültüsü, NaN) ve tek batch'e aşırı uydurma testi temel araçlardır. Tek batch testi gerekli ama yeterli değildir: etiket kaymasını yakalamaz.
- Hiperparametre aramasında öğrenme oranı baskın boyuttur; doğrulama disiplinini koru ve bütçeyi raporla.

**Sonraki bölümde:** Bölüm 65, PyTorch Derinlemesine, bu bölümde yalnızca ölçüm aracı olarak kullandığımız çerçeveyi ele alıyor. Tensörleri, autograd'u, `nn.Module` yapısını, Dataset ve DataLoader'ı, mixed precision'ı, checkpoint'leri ve tekrarlanabilirliği göreceksin. Bu bölümde yazdığımız NumPy MLP'sinin neden PyTorch'ta tek satırla yazılabildiğini de orada anlayacaksın.

::: mulakat
1. Adam'da sapma düzeltmesi neden gereklidir? İlk adımda m̂ ve v̂ hangi değerleri alır ve bu güncelleme büyüklüğünü neden etkiler?
2. Eğitim sırasında BatchNorm ile çıkarım sırasında BatchNorm arasındaki fark nedir? Modeli çıkarıma almadan önce `model.eval()` çağrılmazsa ne olur?
3. Loss NaN oldu. İlk olarak hangi üç şeyi kontrol edersin ve neden?
4. L2 düzenlileştirme ile ağırlık azaltma (weight decay) Adam'da neden farklı sonuç verir? AdamW bu farkı nasıl düzeltir?
5. Eğitim kaybı düşüyor ama doğrulama kaybı 10 epoch'tır yükseliyor. Bu nasıl bir durum, neden olabilir ve hangi üç müdahaleyi denersin?
6. Derin bir ağda ilk katmanın gradyanı 10⁻¹² mertebesinde. Sorunun kaynağını nasıl ayırt edersin: başlatma mı, aktivasyon mu, yoksa öğrenme oranı mı?
7. Bir ekip, tek bir batch'e aşırı uydurma testinin geçtiğini söylüyor ama test doğruluğu şans düzeyinde. Hangi hatanın tek batch testini geçebileceğini ve bunu nasıl ayırt edeceğini açıkla.
8. Hiperparametre aramasında rastgele aramanın ızgara aramaya göre avantajı nedir? Hangi koşulda ızgara yine daha iyi olur?
:::
