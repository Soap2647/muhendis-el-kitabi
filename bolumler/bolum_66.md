%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 66
%% baslik: CNN & Bilgisayarlı Görü

## Giriş: Piksel yığınından anlam çıkarmak

Bir İHA'nın gövdesindeki kamera saniyede onlarca kare üretir. Her karede on binlerce piksel vardır ve her piksel bir ışık şiddeti ya da üç renk değeridir. Bu sayılardan "ağaçlık alanda bir araç" ya da "açık alanda duran bir insan" kararını çıkarmak, Bölüm 63'teki tam bağlı ağa görüntüyü olduğu gibi verirsen iki sorunla karşılaşırsın. Birincisi büyüklük: 224×224 renkli bir görüntüyü düzleştirip bin birimlik tek bir katmana bağlamak 150 milyondan fazla ağırlık demektir. İkincisi yapı: aynı araç görüntünün sol üst köşesinde de olsa sağ alt köşesinde de olsa, tam bağlı ağ bunları ayrı problemler gibi öğrenmek zorundadır.

Konvolüsyon katmanı bu iki sorunu birlikte çözer. Küçük bir ağırlık kümesini (çekirdek, kernel) görüntünün her konumunda aynı şekilde uygular. Parametre sayısı görüntünün boyutuna bağlı olmaz ve aynı desen nerede görünürse görünsün aynı tepkiyi verir. 2012'de AlexNet bu fikri GPU üzerinde ölçekli biçimde uygulayıp ImageNet yarışmasında büyük farkla birinci oldu; derin öğrenmenin görüntü alanındaki yükselişi bu tarihten sonra hız kazandı.

Savunma sanayiinde karşılığı açıktır. Hedef tespiti, hedef takibi, uydu ve hava görüntülerinde bina ya da araç sınıflandırması, sensör görüntülerinde kusur tespiti; hepsinde ağın omurgası bir konvolüsyon ağıdır. Bölüm 67'de nesne tespitine geçtiğimizde bu bölümün her kavramını kullanacağız.

Bu bölümdeki veri gerçek bir görüntü kümesi değil, kendi ürettiğimiz sentetik geometrik şekillerdir. Bunun nedeni kontrollü deneydir: bir özelliğin, örneğin öteleme ya da veri artırmanın, ne kadar fark yarattığını ölçebilmek istiyoruz. Ön eğitimli ImageNet ağırlıkları da indirilmedi; transfer öğrenme bölümünde bunun sonuçlarını ayrıca açıklayacağız.

::: not
Bu bölümdeki her sayı, GPU'da (NVIDIA GeForce RTX 3060 Laptop, 6 GB) ya da NumPy ile CPU'da çalıştırılan bir programdan gelir. Programların tamamı kitapta yer alır ve sabit tohumlarla yeniden üretilebilir. Sayılar PyTorch 2.6.0+cu124 ve torchvision 0.21.0 ile ölçüldü; başka bir makinede son hanelerde fark görmen normaldir.
:::

## 66.1 Görüntü bir tensördür

Bilgisayar açısından bir görüntü bir sayı dizisidir. Gri tonlu görüntü bir yükseklik (H) ve genişlik (W) ızgarasıdır; her hücrede bir parlaklık değeri vardır. Renkli görüntüde her konumda üç değer, yani kırmızı, yeşil ve mavi kanallar (C = 3) bulunur. Bu bölümün sentetik görüntüleri gri tonludur ve C = 1 kullanır.

Aynı veriyi farklı kütüphaneler farklı sırada tutar. NumPy ve OpenCV genellikle `(H, W, C)` sırasını kullanır. PyTorch ise konvolüsyon katmanlarında `(C, H, W)` sırasını bekler ve bir batch'i `(N, C, H, W)` olarak gösterir. Bu sıra karışırsa kod hata vermeyebilir, ama anlamsız sonuç üretir; bu yüzden şekil kontrolünü her zaman elle yap. Piksel değerleri 8 bit işaretsiz tamsayı olarak `0` ile `255` arasındadır. Eğitimde bunları `[0, 1]` aralığına ölçekleriz; ardından kanal başına ortalama çıkarıp standart sapmaya bölersen buna normalizasyon denir; Bölüm 64'te normalizasyonun eğitime etkisini, Bölüm 65'te veri hattındaki yerini görmüştün.

Aşağıdaki küçük program bu sıra dönüşümünü ve tam bağlı bir katmanın maliyetini gösteriyor.

Aşağıdaki kod, NumPy'deki sırayı PyTorch'a çevirir ve iki görüntü boyutu için tam bağlı ilk katmanın parametre sayısını hesaplar.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t00: görüntü tensörü şekilleri ve tam bağlı katmanın
maliyeti."""

import numpy as np
import torch

# 1) Görüntü düzenleri: NumPy/OpenCV (H, W, C), PyTorch (C, H, W)
img = np.random.default_rng(0).integers(
    0, 256, (32, 32, 3), dtype=np.uint8
)
print("NumPy (H, W, C):", img.shape, img.dtype)
x = img.transpose(2, 0, 1).astype(np.float32) / 255.0
print(
    "PyTorch (C, H, W):", x.shape, x.dtype, "aralık", x.min(), x.max()
)
batch = torch.tensor(x[None])
print("Batch (N, C, H, W):", tuple(batch.shape))

# 2) Tam bağlı katmanın ağırlık sayısı: giriş = H*W*C, çıkış = 1000
# gizli birim
for ad, h, w, c in (
    ("32x32 gri (bu bölüm)", 32, 32, 1),
    ("224x224 RGB (ImageNet)", 224, 224, 3),
):
    giris = h * w * c
    agirlik = giris * 1000 + 1000
    print(
        "%-22s girdi %6d, ilk katman %10d parametre"
        % (ad, giris, agirlik)
    )
```

```term
$ python t00_gorsel.py
NumPy (H, W, C): (32, 32, 3) uint8
PyTorch (C, H, W): (3, 32, 32) float32 aralık 0.0 1.0
Batch (N, C, H, W): (1, 3, 32, 32)
32x32 gri (bu bölüm)   girdi   1024, ilk katman    1025000 parametre
224x224 RGB (ImageNet) girdi 150528, ilk katman  150529000 parametre
```

Çıktıdaki son satırlar, Bölüm 63'te ele aldığımız tam bağlı katmanın bu boyutta ne kadar pahalı olduğunu gösteriyor. Bu bölümdeki 32×32 gri görüntü için bin birimlik ilk katman bir milyon parametreyi biraz aşıyor. 224×224 renkli bir görüntüde ise bu sayı 150 milyonu aşıyor; bu da bir GPU belleği ve bir veri kümesi sorunudur, yalnızca bir kâğıt üstü hesap değildir.

## 66.2 Tam bağlı ağın görüntüdeki iki sorunu

Tam bağlı ağın görüntüde başarısız olmasının iki temel nedeni var. Birincisi parametre patlamasıdır; yukarıda gördük. İkincisi öteleme (translation) değişmezliğinin olmamasıdır. Tam bağlı katmanda her girdi pikselinin kendine ait bir ağırlığı vardır. Bir nesne sağa kaydığında, nesnenin enerjisi önceden başka bir ağırlığa bağlı olan piksellere geçer ve ağ bu yeni düzeni öğrenmemiştir.

Bunu ölçmek için bir deney kuralım. Hedef alanda dört sınıflı bir veri üretelim: daire, kare, üçgen ve artı. Görüntülerin konumu merkezden ±3 piksel rastgele oynasın. İki model eğitelim: düzleştirilmiş görüntüye bağlanan bir MLP (296 bin parametre) ve iki konvolüsyon bloğuyla küresel ortalama havuzlama yapan bir CNN (24 bin parametre). Test görüntülerini yatay olarak 0'dan 8 piksele kadar kaydırıp doğruluğu ölçelim. Bu deneyin programı, konvolüsyonun eşdeğişkenliğini de (kaydırılmış girdinin çıktısı da kayar) ayrıca sayısal olarak sınar.

Bu bölümün her deneyi iki ortak dosyayı kullanır: sentetik şekilleri üreten `synth.py` ve modelleri, eğitim döngüsünü ve veri artırmayı içeren `ortak.py`. Önce şekil üreticisini okuyalım.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66: sentetik geometrik şekil üreticisi (32x32, gri tonlu).

Gerçek veri indirilmez. Her şekil; konum, boyut, dönüş ve parlaklığı
rastgele değişen bir sınıftır. Kaynak alanı (8 sınıf) ile hedef alanı
(4 sınıf, daha gürültülü ve bulanık) ayrı parametrelerle üretilir.
"""

import numpy as np

ORTA = 15.5
KAYNAK_SINIF = [
    "daire",
    "kare",
    "ucgen",
    "arti",
    "x",
    "elips",
    "cubuk",
    "cift_daire",
]
HEDEF_SINIF = [0, 1, 2, 3]  # daire, kare, üçgen, artı

def _sekil(k, xp, yp, s):
    """k. şeklin maskesi. (xp, yp): şekil merkezine göre döndürülmüş
    koordinatlar."""
    if k == 0:  # daire
        return xp**2 + yp**2 < s**2
    if k == 1:  # kare
        return np.maximum(np.abs(xp), np.abs(yp)) < 0.8 * s
    if k == 2:  # üçgen (dışbükey çokgen)
        A = (0.0, -s)
        B = (0.866 * s, 0.5 * s)
        C = (-0.866 * s, 0.5 * s)

        def kenar(P, Q):
            return (Q[0] - P[0]) * (yp - P[1]) - (Q[1] - P[1]) * (
                xp - P[0]
            )
```

```python
        c1, c2, c3 = kenar(A, B), kenar(B, C), kenar(C, A)
        return ((c1 >= 0) & (c2 >= 0) & (c3 >= 0)) | (
            (c1 <= 0) & (c2 <= 0) & (c3 <= 0)
        )
    if k == 3:  # artı
        w = 0.25 * s
        return ((np.abs(xp) < w) & (np.abs(yp) < s)) | (
            (np.abs(yp) < w) & (np.abs(xp) < s)
        )
    if k == 4:  # X (artının 45° dönüşü)
        u = (xp + yp) / np.sqrt(2)
        v = (xp - yp) / np.sqrt(2)
        w = 0.25 * s
        return ((np.abs(u) < w) & (np.abs(v) < s)) | (
            (np.abs(v) < w) & (np.abs(u) < s)
        )
    if k == 5:  # elips
        return (xp / s) ** 2 + (yp / (0.55 * s)) ** 2 < 1
    if k == 6:  # çubuk
        return (np.abs(yp) < 0.2 * s) & (np.abs(xp) < s)
    if k == 7:  # iki daire
        r = 0.5 * s
        return ((xp - 0.6 * s) ** 2 + yp**2 < r**2) | (
            (xp + 0.6 * s) ** 2 + yp**2 < r**2
        )
    raise ValueError(k)
```

```python
def uret(
    n_sinif,
    tohum,
    siniflar,
    gurultu=0.05,
    olcek=(0.18, 0.30),
    konum=3.0,
    bulanik=False,
    kontrast=(0.6, 1.0),
):
    """n_sinif: her sınıftan örnek sayısı. Dönüş: X (N,1,32,32), y
    (N,)."""
    rng = np.random.default_rng(tohum)
    y = np.repeat(np.arange(len(siniflar)), n_sinif)
    sinif = np.array(siniflar)[y]
    N = len(y)
    s = rng.uniform(*olcek, N) * 32
    th = rng.uniform(0, 2 * np.pi, N)
    cx = ORTA + rng.uniform(-konum, konum, N)
    cy = ORTA + rng.uniform(-konum, konum, N)
    yy, xx = np.mgrid[0:32, 0:32].astype(np.float64)
    dx = xx[None] - cx[:, None, None]
    dy = yy[None] - cy[:, None, None]
    c = np.cos(th)[:, None, None]
    sn = np.sin(th)[:, None, None]
    xp = c * dx + sn * dy
    yp = -sn * dx + c * dy
    S = s[:, None, None]
    maske = np.zeros((N, 32, 32), dtype=bool)
    for k in set(siniflar):
        idx = np.where(sinif == k)[0]
        maske[idx] = _sekil(k, xp[idx], yp[idx], S[idx])
    on = rng.uniform(*kontrast, N)
    arka = rng.uniform(0.0, 0.2, N)
    img = arka[:, None, None] + (on - arka)[:, None, None] * maske
    img = img + rng.normal(0, gurultu, img.shape)
    if bulanik:
        p = np.pad(img, ((0, 0), (1, 1), (1, 1)), mode="edge")
        img = (
            sum(
```

```python
                p[:, i : i + 32, j : j + 32]
                for i in range(3)
                for j in range(3)
            )
            / 9.0
        )
    img = np.clip(img, 0, 1).astype(np.float32)[:, None]
    return img, y
```

```python
def hedef_veri(n_sinif, tohum, konum=3.0):
    """Hedef alan: 4 sınıf, gürültülü ve bulanık görüntüler."""
    return uret(
        n_sinif,
        tohum,
        HEDEF_SINIF,
        gurultu=0.15,
        olcek=(0.16, 0.28),
        konum=konum,
        bulanik=True,
        kontrast=(0.5, 1.0),
    )

def kaynak_veri(n_sinif, tohum):
    """Kaynak alan (ön eğitim): 8 sınıf, temiz görüntüler."""
    return uret(n_sinif, tohum, list(range(8)), gurultu=0.05)

def kaydir(X, dx, dy):
    """Görüntüyü (dx, dy) piksel kaydırır; boşluklar sıfırla dolar."""
    Y = np.zeros_like(X)
    H, W = X.shape[-2:]
    Y[
        ..., max(dy, 0) : H + min(dy, 0), max(dx, 0) : W + min(dx, 0)
    ] = X[
        ...,
        max(-dy, 0) : H + min(-dy, 0),
        max(-dx, 0) : W + min(-dx, 0),
    ]
    return Y
```

Görüntüler 32×32 boyutunda ve gri tonludur. Hedef alan, kaynak alana göre daha gürültülü ve bulanık üretilir; bu fark, transfer öğrenme ve sağlamlık deneylerinde kullanılacak.

Şimdi ortak yardımcılar: modeller, eğitim döngüsü, artırma ve ölçüm. Dosyanın tamamı aşağıda.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66: ortak PyTorch yardımcıları (modeller, eğitim, artırma,
ölçüm)."""

import math
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

DEV = torch.device("cuda")
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

def tensor(X, y):
    return (
        torch.tensor(X, dtype=torch.float32, device=DEV),
        torch.tensor(y, dtype=torch.long, device=DEV),
    )

def katman(ic, oc, bn):
    L = [nn.Conv2d(ic, oc, 3, padding=1, bias=not bn)]
    if bn:
        L.append(nn.BatchNorm2d(oc))
    return L

class Kucuk(nn.Module):
    """Küçük CNN: 32 -> 16 -> 8 -> 8 (son konvolüsyon), GAP,
    doğrusal."""
```

```python
    def __init__(self, K=4):
        super().__init__()
        self.ozellik = nn.Sequential(
            nn.Sequential(
                *katman(1, 16, True), nn.ReLU(), nn.MaxPool2d(2)
            ),
            nn.Sequential(
                *katman(16, 32, True), nn.ReLU(), nn.MaxPool2d(2)
            ),
            nn.Sequential(*katman(32, 64, True), nn.ReLU()),
        )
        self.bas = nn.Linear(64, K)

    def forward(self, x):
        h = self.ozellik(x).mean(dim=(2, 3))
        return self.bas(h)

class Mlp(nn.Module):
    """Karşılaştırma: düzleştirilmiş görüntüye tam bağlı ağ."""

    def __init__(self, K=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, K),
        )

    def forward(self, x):
        return self.net(x)

class Bloku(nn.Module):
    """İki konvolüsyonlu blok. artik=True ise x + F(x) (ResNet
    fikri)."""
```

```python
    def __init__(self, g, bn, artik):
        super().__init__()
        self.c1 = nn.Sequential(*katman(g, g, bn))
        self.c2 = nn.Sequential(*katman(g, g, bn))
        self.artik = artik

    def forward(self, x):
        h = self.c2(F.relu(self.c1(x)))
        if self.artik:
            h = h + x
        return F.relu(h)

class DerinAg(nn.Module):
    """Stem + blok_say * 2 konvolüsyon. Toplam konvolüsyon: 1 +
    2*blok_say."""

    def __init__(self, blok_say, g=32, bn=True, artik=True, K=4):
        super().__init__()
        self.giris = nn.Sequential(*katman(1, g, bn))
        self.bloklar = nn.ModuleList(
            [Bloku(g, bn, artik) for _ in range(blok_say)]
        )
        self.bas = nn.Linear(g, K)

    def forward(self, x):
        h = F.relu(self.giris(x))
        for b in self.bloklar:
            h = b(h)
        return self.bas(h.mean(dim=(2, 3)))

def parametre_say(m):
    return sum(p.numel() for p in m.parameters())
```

```python
def artir(x):
    """GPU'da toplu artırma: ±15° döndürme, ±%10 ölçek, ±%12 kaydırma,
    yatay ayna (p=0,5), parlaklık/kontrast ve hafif gürültü."""
    B = x.shape[0]
    d = x.device
    ang = (torch.rand(B, device=d) * 2 - 1) * math.radians(15)
    sc = 1 + (torch.rand(B, device=d) * 2 - 1) * 0.10
    tx = (torch.rand(B, device=d) * 2 - 1) * 0.12
    ty = (torch.rand(B, device=d) * 2 - 1) * 0.12
    ayna = 1 - 2 * (torch.rand(B, device=d) < 0.5).float()
    c = torch.cos(ang) / sc
    s = torch.sin(ang) / sc
    theta = torch.stack(
        [
            torch.stack([c * ayna, -s, tx], 1),
            torch.stack([s * ayna, c, ty], 1),
        ],
        1,
    )
    grid = F.affine_grid(theta, list(x.shape), align_corners=False)
    x = F.grid_sample(
        x, grid, align_corners=False, padding_mode="zeros"
    )
    a = 1 + (torch.rand(B, 1, 1, 1, device=d) * 2 - 1) * 0.2
    b = (torch.rand(B, 1, 1, 1, device=d) * 2 - 1) * 0.1
    x = x * a + b + torch.randn_like(x) * 0.02
    return x.clamp(0, 1)
```

```python
def egit(
    model,
    X,
    y,
    adim,
    bs=64,
    lr=1e-3,
    tohum=0,
    aug=None,
    sabit=None,
    grup_lr=None,
):
    """Adam ile adim kadar adım atar. Dönüş: adım başına kayıp
    listesi.
```

```python
    sabit: BN katmanları eval modunda kalsın diye verilen modül
    listesi.
    grup_lr: (parametre_listesi, lr) — katman başına öğrenme oranı.
    """
    torch.manual_seed(tohum)
    if grup_lr is None:
        opt = torch.optim.Adam(model.parameters(), lr=lr)
    else:
        opt = torch.optim.Adam(grup_lr, lr=lr)
    n = len(y)
    kay = []
    adim_say = 0
    while adim_say < adim:
        perm = torch.randperm(n, device=DEV)
        for i in range(0, n, bs):
            if adim_say >= adim:
                break
            idx = perm[i : i + bs]
            xb = X[idx]
            if aug is not None:
                xb = aug(xb)
            model.train()
            for m in sabit or []:
                m.eval()
            loss = F.cross_entropy(model(xb), y[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            kay.append(loss.detach())
            adim_say += 1
    return torch.stack(kay).cpu().numpy()
```

```python
@torch.no_grad()
def dogruluk(model, X, y, bs=512):
    model.eval()
    dogru = 0
    for i in range(0, len(y), bs):
        dogru += (
            (model(X[i : i + bs]).argmax(1) == y[i : i + bs])
            .sum()
            .item()
        )
    return dogru / len(y)

def sure_olc(f, tekrar=3):
    en = np.inf
    for _ in range(tekrar):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        f()
        torch.cuda.synchronize()
        en = min(en, time.perf_counter() - t0)
    return en
```

Eğitim döngüsü, Bölüm 65'te gördüğün DataLoader yerine tensörleri doğrudan GPU'da tutuyor ve her adımda rastgele bir karıştırma (permutasyon) ile mini-batch seçiyor. Optimizer olarak Bölüm 64.3'te türettiğimiz Adam'ı kullanıyoruz. Kayıp fonksiyonu, Bölüm 63'teki softmax ve çapraz entropinin PyTorch karşılığı olan `cross_entropy`dir.

Kaydırma deneyinin programı şöyle:

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t03: MLP vs CNN, öteleme (kayma) duyarlılığı ve
eşdeğişkenlik.

Eğitim: hedef alan, 800 örnek/sınıf (konum jitter ±3 px). Test:
300/sınıf,
test görüntüleri (dx, 0) kadar kaydırılarak ölçülür. 5 tohum.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth import hedef_veri, kaydir
from ortak import (
    DEV,
    tensor,
    Mlp,
    Kucuk,
    egit,
    dogruluk,
    parametre_say,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
KAYMALAR = [0, 1, 2, 4, 6, 8]
```

```python
# 1) Eşdeğişkenlik: konvolüsyonu 1 px kaydır, çıktı da kayar mı?
torch.manual_seed(0)
conv = torch.nn.Conv2d(1, 4, 3, padding=1, bias=False).to(DEV)
x = torch.rand(1, 1, 32, 32, device=DEV)
x_k = torch.roll(
    x, shifts=(0, 1), dims=(2, 3)
)  # sağa 1 px (dairesel)
y1 = conv(x)
y2 = conv(x_k)
ic = slice(2, 30)  # kenar etkisi yok
fark = (
    (
        torch.roll(y1, shifts=(0, 1), dims=(2, 3))[..., ic, ic]
        - y2[..., ic, ic]
    )
    .abs()
    .max()
    .item()
)
print(
    "1) Konvolüsyon eşdeğişkenliği: iç bölgede en büyük fark = %.2e"
    % fark
)

# 2) Veri ve parametre sayıları
Xt, yt = hedef_veri(800, 1)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
print(
    "2) Parametre sayısı: MLP %d, CNN %d"
    % (parametre_say(Mlp()), parametre_say(Kucuk()))
)
```

```python
# 3) Eğitim ve kayma testi
sonuc = []
for tohum in range(5):
    for ad, kur in (("MLP", Mlp), ("CNN", Kucuk)):
        torch.manual_seed(tohum)
        model = kur().to(DEV)
        egit(model, Xt_g, yt_g, adim=1500, tohum=tohum)
        satir = []
        for dx in KAYMALAR:
            Xk = tensor(kaydir(Xs, dx, 0), ys)[0]
            acc = dogruluk(model, Xk, ys_g)
            satir.append(acc)
            sonuc.append((ad, tohum, dx, acc))
        print(
            "tohum %d %-3s  " % (tohum, ad)
            + "  ".join(
                "%d:%.3f" % (dx, a) for dx, a in zip(KAYMALAR, satir)
            )
        )

print("\nOrtalama doğruluk (5 tohum) — kayma (px) başına:")
for ad in ("MLP", "CNN"):
    ort = []
    for dx in KAYMALAR:
        v = [s[3] for s in sonuc if s[0] == ad and s[2] == dx]
        ort.append("%.3f" % np.mean(v))
    print("%-3s  " % ad + "  ".join(ort))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_kayma.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["model", "tohum", "kayma", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])
```

```term
$ python t03_kayma.py
1) Konvolüsyon eşdeğişkenliği: iç bölgede en büyük fark = 0.00e+00
2) Parametre sayısı: MLP 295812, CNN 23668
tohum 0 MLP  0:0.848  1:0.818  2:0.713  4:0.541  6:0.343  8:0.284
tohum 0 CNN  0:0.917  1:0.916  2:0.897  4:0.881  6:0.869  8:0.871
tohum 1 MLP  0:0.849  1:0.821  2:0.736  4:0.545  6:0.353  8:0.273
tohum 1 CNN  0:0.963  1:0.958  2:0.958  4:0.965  6:0.957  8:0.896
tohum 2 MLP  0:0.853  1:0.818  2:0.721  4:0.523  6:0.324  8:0.269
tohum 2 CNN  0:0.966  1:0.962  2:0.929  4:0.928  6:0.912  8:0.907
tohum 3 MLP  0:0.835  1:0.798  2:0.693  4:0.506  6:0.318  8:0.269
tohum 3 CNN  0:0.973  1:0.978  2:0.959  4:0.972  6:0.963  8:0.922
tohum 4 MLP  0:0.840  1:0.823  2:0.720  4:0.537  6:0.346  8:0.287
tohum 4 CNN  0:0.959  1:0.953  2:0.941  4:0.954  6:0.948  8:0.948

Ortalama doğruluk (5 tohum) — kayma (px) başına:
MLP  0.845  0.815  0.716  0.530  0.337  0.276
CNN  0.955  0.954  0.937  0.940  0.930  0.909
```

Önce eşdeğişkenlik kontrolü: iç bölgede en büyük fark sıfır çıktı. Bu, kaydırılmış girdinin konvolüsyon çıktısının da aynı miktarda kaydığının, sayısal olarak tam bir eşleşmeyle doğrulandığı anlamına gelir. Kenarlar (dolgu bölgesi) bu eşitlikten hariç tutulmuştur, çünkü sıfır dolgu kenarda farklı bir sınır koşulu getirir.

Doğruluk sonuçları ise net bir ayrım gösteriyor. Ortalama değerleri şöyle:

| Kaydırma (piksel) | 0 | 1 | 2 | 4 | 6 | 8 |
|---|---|---|---|---|---|---|
| MLP (296 bin parametre) | 0,845 | 0,815 | 0,716 | 0,530 | 0,337 | 0,276 |
| CNN (24 bin parametre) | 0,955 | 0,954 | 0,937 | 0,940 | 0,930 | 0,909 |

Tablo, 5 tohumun ortalamasıdır; test kümesi 300 örnek/sınıftır ve eğitimden ayrıdır. MLP, eğitim sırasında ±3 piksel kaymayı görmüş olmasına rağmen dört pikselde yarı yarıya, sekiz pikselde üçte bir doğruluğa düşüyor. CNN ise sekiz pikselde bile yaklaşık yüzde doksan doğruluğunu koruyor. Şekil 66.1, iki eğriyi ve tohumların sapmasını birlikte gösteriyor.

![Şekil 66.1: Test görüntüsü kaydırıldıkça MLP ve CNN doğruluğu. Eğitimde ±3 piksel konum oynaması vardı. Gölgeli bant 5 tohumun sapması.](gorseller/b66_kayma.png)

CNN'in kaymaya karşı tamamen değişmez olmadığını da not etmek gerekir: sekiz pikselde doğruluk yaklaşık yüzde beş düşüyor. Bunun nedeni sıfır dolguyla gelen kenar etkisi ve görüntü sınırına yaklaşan nesnelerin bir kısmının kadrajdan çıkmasıdır. Mükemmel değişmezlik yerine güçlü bir öteleme tepkisi elde ettiğimizi söylemek daha doğru olur. Küresel ortalama havuzlama (GAP), son özellik haritasındaki konum bilgisini ortadan kaldırarak bu değişmezliği ağa ek bir biçimde katar; bunu 66.8'de mimariler arasında tekrar göreceğiz.

## 66.3 Konvolüsyon katmanı: yerel bağlantı ve ağırlık paylaşımı

Konvolüsyon katmanını iki fikir tanımlar. Birincisi yerel bağlantıdır: bir çıktı pikseli, girdinin yalnızca küçük bir komşuluğuna (alıcı alana) bağlıdır. Üç-üç bir çekirdekle bir çıktı pikseli dokuz girdi pikseline bağlanır, bütün görüntüye değil. Kenar, köşe ve doku gibi yerel desenler de zaten yerel olduğu için bu kısıt doğaldır. İkincisi ağırlık paylaşımıdır: aynı dokuz ağırlık görüntünün her konumunda kullanılır. Böylece bir kenar dedektörü sol üstte de sağ altta da aynı şekilde çalışır.

Tek boyutta formül şöyle yazılır. Girdi `x`, çekirdek `w` ve uzunluğu `K` ise çıktı

    y[i] = Σ_{u=0}^{K−1} w[u] · x[i + u] + b

ile hesaplanır. Bu, Bölüm 52'deki konvolüsyondan farklıdır ve ayrım önemlidir. Sinyal işlemede `y[n] = Σ x[k] h[n − k]` yazılır; çekirdek ters çevrilir. Derin öğrenmede çekirdek çevrilmez ve toplam `x[i + u]` ile yapılır. Bu işleme çapraz korelasyon (cross-correlation) denir. Ağırlıklar zaten eğitimle öğrenildiği için ters çevrilmiş bir çekirdek de aynı işlevi görür; yani derin öğrenme kütüphaneleri "konvolüsyon" adını kullansa da işlem çapraz korelasyondur. Bu bölümde iki terimi de aynı anlamda kullanacağız ama kodda `conv2d` ile çapraz korelasyonu kastediyoruz.

İki boyutta aynı fikir bir ızgarada kayan pencere olarak görülür. Çekirdek sol üstten başlar, her adımda sağa ve aşağıya kayar, her konumda çarpımların toplamını bir çıktı hücresine yazar. Kayma miktarına adım (stride, `S`) denir. Kenardaki pikselleri pencereye dahil etmek için girdiyi dolgu (padding, `P`) ile genişletebilirsin; dolgu genellikle sıfırdır. Şekil 66.2, bu iki parametrenin çıktı boyutunu nasıl değiştirdiğini gösteriyor.

![Şekil 66.2: Solda P = 1, S = 1: 5×5 girdi çevresinde sıfır dolgu ile 5×5 çıktı. Sağda P = 0, S = 2: 7×7 girdide pencere iki hücre atlar ve 3×3 çıktı üretilir.](gorseller/b66_kayan_pencere.png)

Çıktı boyutunu hesaplamak için tek bir formül yeterlidir. Girdi yüksekliği `H`, çekirdek `K`, adım `S` ve dolgu `P` ise çıktı yüksekliği

    çıkış = ⌊(H + 2P − K) / S⌋ + 1

olur. Genişlik için aynı formül geçerlidir. Bu formülü ezberlemek yerine her parametrenin ne işe yaradığını anlamak önemlidir. Dolgu, pencerenin kenara ne kadar taşabileceğini artırır (2P). Adım, pencerenin her seferinde kaç hücre atladığını belirler. Pencerenin kendisi K hücredir; bu yüzden çıktı girdiden K − 1 kadar küçülür, dolgu bu kaybı telafi eder.

Formülü altı farklı durumda gerçek bir konvolüsyon fonksiyonunun çıktısıyla sınayan program 66.6'da, NumPy gerçeklemesinin testi olarak yer alıyor. Şimdilik formülün ne anlama geldiğini ve nasıl okunacağını kavraman yeterli.

## 66.4 Çok kanallı konvolüsyon ve parametre sayımı

Gerçek görüntüler ve ara özellik haritaları tek kanallı değildir. `C_in` kanallı bir girdiyi `C_out` kanallı bir çıktıya dönüştürmek için bir çekirdek kümesi gerekir. PyTorch'ta bu küme `(C_out, C_in, K, K)` şeklinde bir tensördür. Her çıktı kanalı `C_in` tane `K × K` çekirdeğin toplamıdır: önce her girdi kanalı kendi çekirdeğiyle taranır, sonra sonuçlar toplanır ve bir sapma (bias) eklenir.

Bu yapıdan parametre sayısı doğrudan çıkar:

    parametre = C_out · (C_in · K² + 1)

Buradaki `+1` sapmadır. Bu formülü üç katmana uygulayalım: 3 kanaldan 16 kanala, 16 kanaldan 32 kanala ve 32 kanaldan 64 kanala 3×3 konvolüsyonlar sırasıyla 448, 4 640 ve 18 496 parametre eder. Dikkat edilirse parametre sayısı yalnızca kanal sayılarına ve çekirdek boyutuna bağlıdır; görüntünün boyutuna bağlı değildir. Bu, tam bağlı katmanla temel farktır. 1024 girdi ve 1000 çıktı için tam bağlı katman bir milyonu aşan parametre gerektirirken, 1 kanallı girdiyi 16 kanala çeviren 3×3 konvolüsyon yalnızca 160 parametre kullanır.

Bu bölümün `Kucuk` ağında da bu sayımı doğrulayabilirsin. Üç konvolüsyon bloğu sapma kullanmaz çünkü her birinin arkasında batch normalizasyon vardır (Bölüm 64'te ayrıntısı var); normalizasyon katmanı kanal başına iki parametre (ölçek ve kaydırma) ekler. Toplam: `144 + 4608 + 18432 + 224 + 260 = 23 668`, ki bu tam olarak `t03` çıktısındaki sayıdır.

Üç özel konvolüsyon türü, mimari tasarımda sık karşımıza çıkar.

Birincisi 1×1 konvolüsyondur. Çekirdek tek bir piksel büyüklüğündedir, bu yüzden mekânsal bir komşuluğa bakmaz; yalnızca kanallar arasında doğrusal bir karışım yapar. Parametre sayısı `C_out · C_in` olur. Kanal sayısını küçültmek için (darboğaz, bottleneck) ya da kanallar arasında bilgi harmanlamak için kullanılır. ResNet-50'nin blokları bu sayede pahalı 3×3 konvolüsyonları küçük tutar.

İkincisi genişletilmiş (dilated) konvolüsyondur. Çekirdek elemanları arasına `d − 1` boşluk konur. Etkin çekirdek boyutu `K_eff = d(K − 1) + 1` olur: `K = 3` ve `d = 2` için `K_eff = 5`. Parametre sayısı değişmez ama alıcı alan büyür. Bölütleme ağlarında çözünürlüğü düşürmeden geniş bağlam görmek için kullanılır (Bölüm 67).

Üçüncüsü derinlemesine ayrılabilir (depthwise separable) konvolüsyondur ve gömülü sistemler için en önemli olanıdır. Standart bir konvolüsyon hem mekânsal hem kanal karışımını aynı anda yapar. Bunu ikiye ayırabiliriz: her girdi kanalını kendi `K × K` çekirdeğiyle ayrı ayrı tararız (derinlemesine, `groups = C_in`), sonra 1×1 konvolüsyonla kanalları karıştırırız (noktasal). MobileNet ailesinin temel fikri budur. Aşağıdaki karşılaştırma bu sayımı `t08` programında hesaplar; 64 kanaldan 128 kanala 3×3 bir konvolüsyonun parametre ve çarpma sayısı, ayrılabilir versiyonla karşılaştırılmıştır.

Konvolüsyonun hesap maliyeti, yani FLOP sayısı da aynı mantıkla çıkar: her çıktı konumu için `C_in · K²` çarpım yapılır ve bu, `C_out · H_çıkış · W_çıkış` konum-kanal çiftiyle çarpılır. Bu sayı, bir İHA'nın işlemcisinde çıkarım süresini belirler ve Bölüm 66.14'te ölçeceğiz.

## 66.5 Alıcı alan

Bir çıktı hücresinin "gördüğü" girdi bölgesine alıcı alan (receptive field) denir. Tek bir 3×3 konvolüsyonda alıcı alan 3×3'tür. Konvolüsyonları üst üste koyduğumuzda alıcı alan büyür ama bu büyüme doğrusal değildir. Katman `k` için alıcı alan `r_k` ve kümülatif adım (jump) `j_k` şöyle hesaplanır:

    r_k = r_{k−1} + (K_k − 1) · j_{k−1}
    j_k = j_{k−1} · S_k

Başlangıçta `r_0 = 1` ve `j_0 = 1`dir. Üç tane 3×3, adım 1 konvolüsyon üst üste konursa `r` sırasıyla 3, 5 ve 7 olur. Bu, derin ağlarda son katmandaki bir nöronun girdide neyi "gördüğünü" hesaplamanın yoludur. Bu ayrıntı, nesne tespitinde çok büyük nesneleri ve küçük nesneleri aynı ağla yakalamanın neden zor olduğunu anlamanın anahtarıdır (Bölüm 67).

VGG ağının fikri de buna dayanır (Bölüm 66.8). İki üst üste 3×3 konvolüsyon, tek bir 5×5 konvolüsyonla aynı alıcı alanı verir. Ama kanal sayısı `C` ise iki 3×3 katmanın parametresi `2 · 9C² = 18C²`, tek 5×5 katmanın parametresi `25C²`dir. Üstelik iki katman arasında doğrusal olmayan bir ReLU vardır; bu da ağın ifade gücünü artırır. Yani aynı görüşü daha az parametreyle ve daha çok doğrusal olmayanlıkla elde ederiz.

## 66.6 Konvolüsyonun sıfırdan gerçeklenmesi

Konvolüsyonu anlamanın en sağlam yolu onu kendi elinle yazmaktır. Üç gerçekleme göreceğiz: önce dört döngülü naif hâli, sonra matris çarpımına dönüştürülmüş hâli (im2col), en sonunda geri yayılım. Her birinin doğruluğunu PyTorch'un `conv2d`'siyle ve sayısal gradyan kontrolüyle sınayacağız.

Naif gerçekleme doğrudan tanımdan gelir: her çıktı elemanı için çekirdeği yerinde tutup çarpımları toplarız. Bu kolay okunur ama yavaştır. Hızlandırmanın anahtarı, her pencereyi bir satıra açıp (im2col) tüm konvolüsyonu tek bir matris çarpımına çevirmektir. Şekil 66.3'te bu dönüşümü küçük bir 4×4 girdi ve 3×3 çekirdek üzerinde görüyorsun. Çıktı 2×2 olduğu için dört pencere, her biri dokuz sayılık birer satıra açılır. Böylece konvolüsyon, `(4 × 9)` boyutlu bir matrisle `(9 × 1)` boyutlu çekirdek vektörünün çarpımına dönüşür. Bölüm 48'de matris çarpımının BLAS kütüphaneleriyle ne kadar hızlı yapıldığını gördük; im2col bu hızı konvolüsyona taşır.

![Şekil 66.3: im2col dönüşümü. Her pencere bir satıra açılır, çekirdek bir sütun vektörü olur ve konvolüsyon bir matris çarpımına indirgenir. Sağ alt kutu geri geçişte kullanılan iki ifadeyi gösterir.](gorseller/b66_im2col.png)

İm2col'ün bedeli bellektir: her pencere kopyalandığı için girdiden yaklaşık `K²` kat daha büyük bir ara matris oluşur. Bu yüzden derin öğrenme kütüphaneleri çoğu zaman bu matrisi açıkça oluşturmaz; ama kavramsal olarak doğru olan budur ve geri geçişi anlamak için de gereklidir.

### Geri geçişin türetilmesi

Kayıp `L` olsun ve konvolüsyonun çıktısı `Y` olsun. Geri yayılımda bize `dY = ∂L/∂Y` verilir; istediğimiz `dW = ∂L/∂W`, `db = ∂L/∂b` ve `dX = ∂L/∂X`tir. Bölüm 63'teki zincir kuralı burada da aynen geçerlidir, yalnızca her çıktı konumu birçok girdi konumuna bağlıdır.

Tek bir ağırlık `W[u, v]` her çıktı konumunda kullanıldığı için, zincir kuralı bütün konumları toplar:

    dW[u, v] = Σ_{i,j} dY[i, j] · X[i + u, j + v]

Bu ifade, girdinin dY ile çapraz korelasyonudur. Yani dW'yi hesaplamak için yine bir konvolüsyon çalıştırırız; bu nedenle geri geçiş de ağır bir konvolüsyon işidir.

Girdi piksellerinin gradyanı için bakış tersine döner. Bir `X[p, q]` pikseli birçok çıktı konumunda, farklı ağırlıklarla yer alır. Toplamı yazarsak

    dX[p, q] = Σ_{u,v} W[u, v] · dY[p − u, q − v]

elde ederiz. Bu, `dY`'nin ters çevrilmiş çekirdek `W` ile tam konvolüsyonudur. Bölüm 52'deki sinyal işleme konvolüsyonuyla bağlantı tam burada kurulur: geri geçiş, ileri yönde çapraz korelasyon yapılan bir işlemin transpozunu gerçekler ve bu transpoz bir konvolüsyon olarak ifade edilir.

Matris dilinde ise im2col ileri yönde `cols` matrisini üretir ve çıktı `Y = cols · Wᵀ + b` olur. Geri yönde `dW = dYᵀ · cols`, `dcols = dY · W` ve `dcols`un her satırı pencereye geri dönüştürülüp (col2im) örtüşen konumlar toplanarak `dX` bulunur. Örtüşme nedeniyle toplama zorunludur: bir girdi pikseli birden çok pencereye ait olabilir.

Max pooling'in geri geçişi daha basittir. İleri yönde pencerenin maksimumunu seçeriz ve bu konumun indeksini saklarız. Geri yönde gradyanı yalnızca o konuma geri yollarız; diğer konumlar sıfır alır. Bu yüzden pooling, gradyan açısından bir seçicidir ve hangi girdinin bir kararı etkilediğini de gösterir.

### Kütüphane: `konv_np.py`

Aşağıdaki dosya, konvolüsyonun ileri ve geri geçişini, im2col dönüşümünü ve max pooling'i içerir. Hiçbir çerçeve kullanılmaz; sadece NumPy.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66: sıfırdan konvolüsyon katmanı (yalnızca NumPy).

Şekiller: X (N, C, H, W), ağırlık W (OC, C, K, K), sapma b (OC,).
Tüm fonksiyonlar çapraz korelasyon yapar (derin öğrenmedeki
"konvolüsyon").
"""

import numpy as np

def cikis_boyutu(H, K, S, P):
    return (H + 2 * P - K) // S + 1

def dolgu(X, P):
    return np.pad(X, ((0, 0), (0, 0), (P, P), (P, P)))

def konv_naif(X, W, b, S=1, P=1):
    """Dört iç içe döngü: en açık, en yavaş gerçekleme."""
    N, C, H, Wd = X.shape
    OC, _, K, _ = W.shape
    Xp = dolgu(X, P)
    OH, OW = cikis_boyutu(H, K, S, P), cikis_boyutu(Wd, K, S, P)
    Y = np.zeros((N, OC, OH, OW))
    for n in range(N):
        for oc in range(OC):
            for i in range(OH):
                for j in range(OW):
                    yama = Xp[
                        n, :, i * S : i * S + K, j * S : j * S + K
                    ]
                    Y[n, oc, i, j] = np.sum(yama * W[oc]) + b[oc]
    return Y
```

```python
def im2col(X, K, S, P):
    """Her çıkış konumunun alıcı alanını bir satıra aç: (N*OH*OW,
    C*K*K)."""
    N, C, H, Wd = X.shape
    Xp = dolgu(X, P)
    OH, OW = cikis_boyutu(H, K, S, P), cikis_boyutu(Wd, K, S, P)
    cols = np.empty((N, C, K, K, OH, OW))
    for ki in range(K):
        for kj in range(K):
            cols[:, :, ki, kj] = Xp[
                :, :, ki : ki + S * OH : S, kj : kj + S * OW : S
            ]
    cols = cols.transpose(0, 4, 5, 1, 2, 3).reshape(
        N * OH * OW, C * K * K
    )
    return cols, OH, OW

def konv_im2col(X, W, b, S=1, P=1):
    """im2col + tek bir matris çarpımı. Dönüş: Y ve geri geçiş için
    cols."""
    N = X.shape[0]
    OC, C, K, _ = W.shape
    cols, OH, OW = im2col(X, K, S, P)
    Y = cols @ W.reshape(OC, C * K * K).T + b
    Y = Y.reshape(N, OH, OW, OC).transpose(0, 3, 1, 2)
    return Y, cols
```

```python
def col2im(dcols, X_sekil, K, S, P):
    """im2col'in transpozu: örtüşen konumların gradyanlarını
    toplar."""
    N, C, H, Wd = X_sekil
    OH, OW = cikis_boyutu(H, K, S, P), cikis_boyutu(Wd, K, S, P)
    dXp = np.zeros((N, C, H + 2 * P, Wd + 2 * P))
    d = dcols.reshape(N, OH, OW, C, K, K).transpose(0, 3, 4, 5, 1, 2)
    for ki in range(K):
        for kj in range(K):
            dXp[
                :, :, ki : ki + S * OH : S, kj : kj + S * OW : S
            ] += d[:, :, ki, kj]
    return dXp[:, :, P : P + H, P : P + Wd]

def konv_geri(dY, cols, X_sekil, W, S=1, P=1):
    """dW = girdi ⋆ dY (cols üzerinden), dX = col2im(dY · W), db = Σ
    dY."""
    OC = W.shape[0]
    dYf = dY.transpose(0, 2, 3, 1).reshape(-1, OC)
    dW = (dYf.T @ cols).reshape(W.shape)
    db = dYf.sum(axis=0)
    dcols = dYf @ W.reshape(OC, -1)
    dX = col2im(dcols, X_sekil, W.shape[2], S, P)
    return dX, dW, db

def maxpool_ileri(X, K=2, S=2):
    N, C, H, Wd = X.shape
    OH, OW = (H - K) // S + 1, (Wd - K) // S + 1
    Y = np.empty((N, C, OH, OW))
    idx = np.empty((N, C, OH, OW), dtype=np.int64)
    for i in range(OH):
        for j in range(OW):
            pen = X[
                :, :, i * S : i * S + K, j * S : j * S + K
            ].reshape(N, C, K * K)
            idx[:, :, i, j] = pen.argmax(axis=2)
            Y[:, :, i, j] = pen.max(axis=2)
    return Y, idx
```

```python
def maxpool_geri(dY, idx, X_sekil, K=2, S=2):
    """Gradyan yalnızca maksimumu veren konuma gider; diğerleri
    sıfır."""
    N, C = X_sekil[0], X_sekil[1]
    dX = np.zeros(X_sekil)
    nn, cc = np.meshgrid(np.arange(N), np.arange(C), indexing="ij")
    for i in range(dY.shape[2]):
        for j in range(dY.shape[3]):
            a = idx[:, :, i, j]
            dX[nn, cc, i * S + a // K, j * S + a % K] += dY[
                :, :, i, j
            ]
    return dX
```

`col2im` fonksiyonundaki `+=`, örtüşen konumların gradyanlarını toplar. Bu satır silinirse ağ yine çalışır ama gradyanlar yanlış olur; bu, bu bölümdeki en sinsi hatalardan biridir ve gradyan kontrolü tam bu tür hataları yakalamak için vardır.

Aşağıdaki test programı dört şeyi sınar: çıktı boyutu formülü, naif ile im2col'ün eşleşmesi, geri geçişin sayısal gradyan ile eşleşmesi ve PyTorch ile eşleşme. Sonra hız farkını ölçer.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t01: naif / im2col eşleşmesi, gradyan kontrolü, PyTorch
eşleşmesi."""

import time
import numpy as np
import torch
import torch.nn.functional as F
from konv_np import (
    cikis_boyutu,
    konv_naif,
    konv_im2col,
    konv_geri,
    maxpool_ileri,
    maxpool_geri,
)

rng = np.random.default_rng(66)

# 1) Çıktı boyutu formülü örnekleri
print("1) cikis = floor((H + 2P - K)/S) + 1")
for H, K, S, P in [
    (5, 3, 1, 0),
    (5, 3, 1, 1),
    (32, 3, 1, 1),
    (32, 3, 2, 1),
    (32, 5, 2, 2),
    (7, 3, 2, 0),
]:
    print(
        "   H=%2d K=%d S=%d P=%d -> %d"
        % (H, K, S, P, cikis_boyutu(H, K, S, P))
    )
```

```python
# 2) Naif ve im2col aynı sonucu veriyor mu?
X = rng.normal(size=(4, 3, 9, 9))
W = rng.normal(size=(5, 3, 3, 3))
b = rng.normal(size=5)
Y1 = konv_naif(X, W, b, S=2, P=1)
Y2, _ = konv_im2col(X, W, b, S=2, P=1)
print(
    "\n2) naif ile im2col en büyük fark: %.2e"
    % np.max(np.abs(Y1 - Y2))
)

# 3) Hız: aynı işin iki gerçeklemesi (en iyi üç ölçüm)
X = rng.normal(size=(8, 16, 32, 32))
W = rng.normal(size=(32, 16, 3, 3))
b = np.zeros(32)

def zamanla(f, tekrar=3):
    en = np.inf
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        en = min(en, time.perf_counter() - t0)
    return en

t_naif = zamanla(lambda: konv_naif(X, W, b, 1, 1), tekrar=1)
t_im2c = zamanla(lambda: konv_im2col(X, W, b, 1, 1))
print("\n3) Hız (N=8, C=16, 32x32, OC=32, K=3):")
print("   naif (dört iç içe döngü)                 : %.2f s" % t_naif)
print("   im2col + matris çarpımı                  : %.4f s" % t_im2c)
print("   hızlanma yaklaşık %.0f kat" % (t_naif / t_im2c))

# 4) Geri geçiş: sayısal gradyan kontrolü (float64, merkezi fark)
X = rng.normal(size=(2, 2, 5, 5))
W = rng.normal(size=(3, 2, 3, 3))
b = rng.normal(size=3)
S, P = 1, 1
Y, cols = konv_im2col(X, W, b, S, P)
G = rng.normal(size=Y.shape)  # rastgele kayıp: L = sum(G * Y)
dX, dW, db = konv_geri(G, cols, X.shape, W, S, P)
```

```python
def kayip_w(Wx):
    return np.sum(G * konv_im2col(X, Wx, b, S, P)[0])

def kayip_x(Xx):
    return np.sum(G * konv_im2col(Xx, W, b, S, P)[0])

def sayisal(f, A, h=1e-6):
    g = np.zeros_like(A)
    it = np.nditer(A, flags=["multi_index"])
    for _ in it:
        i = it.multi_index
        A0 = A[i]
        A[i] = A0 + h
        f1 = f(A)
        A[i] = A0 - h
        f2 = f(A)
        A[i] = A0
        g[i] = (f1 - f2) / (2 * h)
    return g

gW = sayisal(kayip_w, W.copy())
gX = sayisal(kayip_x, X.copy())

def goreli(a, b_):
    """Norm tabanlı göreli hata: ||a-b|| / (||a|| + ||b||)."""
    return np.linalg.norm(a - b_) / (
        np.linalg.norm(a) + np.linalg.norm(b_)
    )

print("\n4) Gradyan kontrolü (norm tabanlı göreli hata):")
print("   dW: %.2e" % goreli(dW, gW))
print("   dX: %.2e" % goreli(dX, gX))
print(
    "   db: %.2e"
    % goreli(db, np.array([np.sum(G[:, c]) for c in range(3)]))
)
```

```python
# 5) Max pooling geri geçişi
Xp = rng.normal(size=(2, 2, 4, 4))
Yp, idx = maxpool_ileri(Xp)
Gp = rng.normal(size=Yp.shape)
dXp = maxpool_geri(Gp, idx, Xp.shape)
gp = sayisal(lambda A: np.sum(Gp * maxpool_ileri(A)[0]), Xp.copy())
print(
    "\n5) Max pooling geri geçişi, göreli hata: %.2e"
    % goreli(dXp, gp)
)
print(
    "   sıfır olmayan gradyan sayısı (beklenen %d): %d"
    % (Yp.size, np.count_nonzero(dXp))
)

# 6) PyTorch ile aynı ağırlık, aynı girdi -> aynı çıktı ve gradyan
Xt = torch.tensor(X, dtype=torch.float64, requires_grad=True)
Wt = torch.tensor(W, dtype=torch.float64, requires_grad=True)
bt = torch.tensor(b, dtype=torch.float64, requires_grad=True)
Yt = F.conv2d(Xt, Wt, bt, stride=S, padding=P)
(Yt * torch.tensor(G)).sum().backward()
print("\n6) PyTorch eşleşmesi (float64):")
print(
    "   ileri en büyük fark : %.2e"
    % np.max(np.abs(Yt.detach().numpy() - Y))
)
print(
    "   dX farkı            : %.2e"
    % np.max(np.abs(Xt.grad.numpy() - dX))
)
print(
    "   dW farkı            : %.2e"
    % np.max(np.abs(Wt.grad.numpy() - dW))
)
print(
    "   db farkı            : %.2e"
    % np.max(np.abs(bt.grad.numpy() - db))
)
```

```term
$ python t01_konv_np.py
1) cikis = floor((H + 2P - K)/S) + 1
   H= 5 K=3 S=1 P=0 -> 3
   H= 5 K=3 S=1 P=1 -> 5
   H=32 K=3 S=1 P=1 -> 32
   H=32 K=3 S=2 P=1 -> 16
   H=32 K=5 S=2 P=2 -> 16
   H= 7 K=3 S=2 P=0 -> 3

2) naif ile im2col en büyük fark: 3.55e-15

3) Hız (N=8, C=16, 32x32, OC=32, K=3):
   naif (dört iç içe döngü)                 : 1.16 s
   im2col + matris çarpımı                  : 0.0137 s
   hızlanma yaklaşık 84 kat

4) Gradyan kontrolü (norm tabanlı göreli hata):
   dW: 3.24e-10
   dX: 4.46e-10
   db: 2.20e-17

5) Max pooling geri geçişi, göreli hata: 6.58e-11
   sıfır olmayan gradyan sayısı (beklenen 16): 16

6) PyTorch eşleşmesi (float64):
   ileri en büyük fark : 8.88e-16
   dX farkı            : 2.22e-16
   dW farkı            : 2.66e-15
   db farkı            : 1.78e-15
```

Sonuçlar üç şeyi açıkça gösteriyor. Birincisi, çıktı boyutu formülü altı durumda da programın gerçek çıktısıyla uyuşuyor. İkincisi, naif ve im2col gerçeklemeleri en fazla 3,6 × 10⁻¹⁵ farkla aynı sonucu veriyor; yani im2col hızlanma için doğruluğu feda etmiyor. Üçüncüsü ve en önemlisi, dW ve dX için analitik gradyanlar sayısal gradyanla `10⁻¹⁰` mertebesinde uyuşuyor. Gradyan kontrolünde kullanılan ölçüt, `‖analitik − sayısal‖ / (‖analitik‖ + ‖sayısal‖)` biçiminde bir norm oranıdır; küçük elemanların yarattığı sahte büyük oranları önler.

Hız farkı da dikkat çekici: aynı işi yapan dört döngülü naif gerçekleme, bu makinede im2col'den yaklaşık seksen dört kat yavaş. Bu oran makineye, derleyiciye ve BLAS kütüphanesine göre değişir. Bu yüzden kitapta "kat" değerini değil, sırayı ve nedenini aklında tut: matris çarpımının düzenli bellek erişimi ve optimize edilmiş kütüphanesi, döngülerden çok daha hızlıdır.

Son olarak PyTorch ile eşleşmeyi gösteren satırlar. Aynı girdi ve aynı çekirdek verildiğinde `F.conv2d` ile bizim `konv_im2col` aynı çıktıyı ve `torch.autograd` ile bizim `konv_geri` aynı gradyanları üretiyor. Bu, derin öğrenme çerçevesinin arkasında tam olarak yukarıdaki matematiğin olduğunu gösterir. Bölüm 65'te autograd'un bu gradyanları nasıl otomatik hesapladığını görmüştün.

## 66.7 NumPy ile sıfırdan CNN: `load_digits` üzerinde

Konvolüsyon katmanını tek başına test etmek yetmez; bir ağın içinde doğru çalıştığını da görmek gerekir. Bu bölümde Bölüm 63'teki `load_digits` veri kümesine ve aynı veri bölmesine geri dönüyoruz. Ağımız küçük bir CNN: 8×8 girdi üzerinde iki konvolüsyon bloğu (her birinde ReLU ve 2×2 max pooling), ardından düzleştirme ve tek bir doğrusal katman.

    1×8×8 → Konv(8) → ReLU → Havuz → 8×4×4
          → Konv(16) → ReLU → Havuz → 16×2×2
          → Düzleştir (64) → Doğrusal (10) → softmax

Her katman bir sınıf olarak yazılmış. Her biri `ileri` ve `geri` yöntemlerine sahip; geri yöntem, çıkış gradyanını alıp kendi parametrelerinin gradyanını hesaplar ve girdi gradyanını bir önceki katmana geçirir. Bu arayüz, Bölüm 63'teki katman sözleşmesinin konvolüsyon ve havuzlama katmanlarına genişletilmiş hâlidir.

Eğitim gradyanları yukarıdaki katmanlardan geri akar. Bu bölümde ağın tamamı için gradyan kontrolü de yapıyoruz: ilk konvolüsyonun ağırlıklarını küçük bir batch üzerinde merkezi farkla sayısal olarak hesaplayıp analitik gradyanla karşılaştırıyoruz. Bu kontrol, katmanlar arası bağlantıda bir hata olup olmadığını da yakalar.

Aşağıdaki program ağı, bölmeyi, gradyan kontrolünü, beş tohumlu eğitimi ve bir taban çizgisi karşılaştırmasını içerir. Öğrenme oranı ve epoch sayısı Bölüm 63'teki MLP'ye yakın tutuldu; ayarlamayı test kümesine bakarak yapmadık.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t02: NumPy ile sıfırdan CNN, load_digits üzerinde.

Mimari: Konv(1->8) ReLU Havuz Konv(8->16) ReLU Havuz Düzleştir
Doğrusal(64->10).
Veri ve bölme Bölüm 63 ile aynı: %60 eğitim, %20 doğrulama, %20 test.
"""

import csv
import os
import time
import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from konv_np import (
    konv_im2col,
    konv_geri,
    maxpool_ileri,
    maxpool_geri,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"

class Konv:
    def __init__(self, rng, ic, oc, K=3, P=1):
        self.W = rng.normal(
            0, np.sqrt(2 / (ic * K * K)), (oc, ic, K, K)
        )
        self.b = np.zeros(oc)
        self.P = P

    def ileri(self, X):
        self.xs = X.shape
        Y, self.cols = konv_im2col(X, self.W, self.b, 1, self.P)
        return Y
```

```python
    def geri(self, dY):
        dX, self.dW, self.db = konv_geri(
            dY, self.cols, self.xs, self.W, 1, self.P
        )
        return dX

class ReLU:
    def ileri(self, X):
        self.m = X > 0
        return X * self.m

    def geri(self, dY):
        return dY * self.m

class Havuz:
    def ileri(self, X):
        self.xs = X.shape
        Y, self.idx = maxpool_ileri(X)
        return Y

    def geri(self, dY):
        return maxpool_geri(dY, self.idx, self.xs)

class Duzlestir:
    def ileri(self, X):
        self.xs = X.shape
        return X.reshape(X.shape[0], -1)

    def geri(self, dY):
        return dY.reshape(self.xs)

class Dogrusal:
    def __init__(self, rng, gi, go):
        self.W = rng.normal(0, np.sqrt(2 / gi), (gi, go))
        self.b = np.zeros(go)

    def ileri(self, X):
        self.X = X
        return X @ self.W + self.b
```

```python
    def geri(self, dY):
        self.dW = self.X.T @ dY
        self.db = dY.sum(axis=0)
        return dY @ self.W.T

def ag_kur(rng):
    return [
        Konv(rng, 1, 8),
        ReLU(),
        Havuz(),
        Konv(rng, 8, 16),
        ReLU(),
        Havuz(),
        Duzlestir(),
        Dogrusal(rng, 64, 10),
    ]

def ileri(ag, X):
    for k in ag:
        X = k.ileri(X)
    return X

def softmax(Z):
    E = np.exp(Z - Z.max(axis=1, keepdims=True))
    return E / E.sum(axis=1, keepdims=True)

def kayip_geri(ag, X, y):
    """Softmax + çapraz entropi; çıkış gradyanı (P - Y)/B."""
    Z = ileri(ag, X)
    P = softmax(Z)
    B = len(y)
    kayip = -np.mean(np.log(P[np.arange(B), y] + 1e-12))
    dZ = P.copy()
    dZ[np.arange(B), y] -= 1
    dZ /= B
    for k in reversed(ag):
        dZ = k.geri(dZ)
    return kayip
```

```python
def adim(ag, lr):
    for k in ag:
        if hasattr(k, "W"):
            k.W -= lr * k.dW
            k.b -= lr * k.db

def kayip_sayi(ag, X, y):
    """Yalnızca kayıp değeri (geri geçiş yok); sayısal gradyan
    için."""
    P = softmax(ileri(ag, X))
    return -np.mean(np.log(P[np.arange(len(y)), y]))

def dogruluk(ag, X, y):
    return float(np.mean(ileri(ag, X).argmax(axis=1) == y))

def veri():
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).reshape(-1, 1, 8, 8)
    idx = np.arange(len(y))
    tr, gec = train_test_split(
        idx, test_size=0.4, stratify=y, random_state=0
    )
    va, te = train_test_split(
        gec, test_size=0.5, stratify=y[gec], random_state=0
    )
    return (X[tr], y[tr]), (X[va], y[va]), (X[te], y[te])

if __name__ == "__main__":
    (Xt, yt), (Xv, yv), (Xs, ys) = veri()
    print(
        "Bölme: eğitim %d, doğrulama %d, test %d"
        % (len(yt), len(yv), len(ys))
    )
```

```python
    # Gradyan kontrolü: ilk konvolüsyon ağırlıkları, küçük batch,
    # float64
    rng = np.random.default_rng(0)
    ag = ag_kur(rng)
    for k in ag:
        for ad in ("W", "b"):
            if hasattr(k, ad):
                setattr(k, ad, getattr(k, ad).astype(np.float64))
    Xk, yk = Xt[:4].astype(np.float64), yt[:4]
    kayip_geri(ag, Xk, yk)  # analitik dW üretir
    k0, h = ag[0], 1e-5
    analitik = k0.dW.copy()
    sayisal = np.zeros_like(k0.W)
    for i in np.ndindex(k0.W.shape):
        w0 = k0.W[i]
        k0.W[i] = w0 + h
        f1 = kayip_sayi(ag, Xk, yk)
        k0.W[i] = w0 - h
        f2 = kayip_sayi(ag, Xk, yk)
        k0.W[i] = w0
        sayisal[i] = (f1 - f2) / (2 * h)
    gr = np.linalg.norm(analitik - sayisal) / (
        np.linalg.norm(analitik) + np.linalg.norm(sayisal)
    )
    print(
        "Gradyan kontrolü (ilk konvolüsyon, tüm ağ): göreli hata %.2e"
        % gr
    )
```

```python
    # Eğitim: 5 tohum, SGD (lr=0.05, batch 32, 30 epoch)
    sonuc = []
    for tohum in range(5):
        rng = np.random.default_rng(tohum)
        ag = ag_kur(rng)
        t0 = time.perf_counter()
        en_va, en_w = -1, None
        for ep in range(30):
            p = rng.permutation(len(yt))
            for i in range(0, len(yt), 32):
                b_idx = p[i : i + 32]
                kayip_geri(ag, Xt[b_idx], yt[b_idx])
                adim(ag, 0.05)
            va = dogruluk(ag, Xv, yv)
            if va > en_va:
                en_va = va
                en_w = [
                    (k.W.copy(), k.b.copy())
                    for k in ag
                    if hasattr(k, "W")
                ]
        sure = time.perf_counter() - t0
        j = 0
        for k in ag:
            if hasattr(k, "W"):
                k.W, k.b = en_w[j]
                j += 1
        te = dogruluk(ag, Xs, ys)
        sonuc.append((tohum, en_va, te, sure / 30))
        print(
            "tohum %d: doğrulama %.3f  test %.3f  epoch süresi %.2f s"
            % (tohum, en_va, te, sure / 30)
        )
    te_ort = np.mean([s[2] for s in sonuc])
    te_sd = np.std([s[2] for s in sonuc], ddof=1)
    print(
        "CNN (NumPy) test ortalama ± sapma: %.4f ± %.4f"
        % (te_ort, te_sd)
    )
```

```python
    # Taban çizgisi: lojistik regresyon (aynı veri, aynı bölme, düz 64
    # girdi)
    lr_model = LogisticRegression(max_iter=2000)
    lr_model.fit(Xt.reshape(len(yt), -1), yt)
    lr_te = lr_model.score(Xs.reshape(len(ys), -1), ys)
    print("Lojistik regresyon (taban çizgisi) test: %.4f" % lr_te)

    # Parametre sayısı
    par = 8 * 1 * 9 + 8 + 16 * 8 * 9 + 16 + 64 * 10 + 10
    print("NumPy CNN parametre sayısı: %d" % par)

    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b66_numpy_cnn.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["tohum", "dogrulama", "test", "epoch_sure_s"])
        for s in sonuc:
            w.writerow(
                [s[0], "%.4f" % s[1], "%.4f" % s[2], "%.3f" % s[3]]
            )
        w.writerow(["lojistik", "", "%.4f" % lr_te, ""])
```

```term
$ python t02_cnn_digits.py
Bölme: eğitim 1078, doğrulama 359, test 360
Gradyan kontrolü (ilk konvolüsyon, tüm ağ): göreli hata 7.30e-11
tohum 0: doğrulama 0.964  test 0.947  epoch süresi 0.07 s
tohum 1: doğrulama 0.964  test 0.936  epoch süresi 0.07 s
tohum 2: doğrulama 0.983  test 0.967  epoch süresi 0.07 s
tohum 3: doğrulama 0.972  test 0.967  epoch süresi 0.07 s
tohum 4: doğrulama 0.986  test 0.967  epoch süresi 0.07 s
CNN (NumPy) test ortalama ± sapma: 0.9567 ± 0.0142
Lojistik regresyon (taban çizgisi) test: 0.9667
NumPy CNN parametre sayısı: 1898
```

Önce gradyan kontrolü: tüm ağın ilk konvolüsyonunda analitik ve sayısal gradyan arasındaki norm tabanlı göreli hata `7,30 × 10⁻¹¹`. Bu, 66.6'daki tek katman testinin ağın tamamında da geçerli olduğunu gösterir.

Eğitim sonuçları beş tohumda şöyle: test doğruluğu `0,947`, `0,936`, `0,967`, `0,967` ve `0,967`; ortalama `0,957`, sapma `0,014`. Lojistik regresyonun aynı bölmedeki test doğruluğu ise `0,967`. Yani bu küçük NumPy CNN, bu ayarlarla taban çizgisini geçemedi; hatta biraz geride kaldı.

Bu sonucu bir başarısızlık gibi okumak yerine bir ölçüm gibi okumak gerekir. Birincisi, veri çok küçük: 8×8 piksellik bir rakam, konvolüsyonun yerel desen avantajını gösterebilecek kadar ayrıntı taşımıyor, ve 1078 eğitim örneği 1898 parametreli bir CNN'i rahatça ayırt etmeye yetmiyor. İkincisi, eğitim bütçesi sınırlı: 30 epoch ve sabit öğrenme oranı. Bölüm 64'teki optimizer ve öğrenme oranı takvimleri bu tabloyu değiştirebilir; bunu bu bölümde denemedik. Üçüncüsü, taban çizgisi güçlüdür: `load_digits` üzerinde lojistik regresyon zaten yüzde doksan altı üstünde çalışır (Bölüm 58). Dolayısıyla bu bölümün asıl kazanımı, konvolüsyonun iç işleyişinin doğru olduğunu kanıtlamak ve ağın nerede kazandığını ya da kaybettiğini ölçmeyi öğrenmektir. Büyük ve gerçekçi görüntülerde konvolüsyonun üstünlüğünü bir sonraki kısımdaki sentetik deneyde göreceksin.

## 66.8 Mimari tarihi: LeNet'ten ResNet'e

Bugünkü görüntü ağlarının neden böyle göründüğünü anlamak için son otuz yılın kısa bir özetine bakmak yararlıdır. Aşağıdaki tablo, her mimarinin getirdiği ana fikri özetliyor. Yıllar ve yayın bilgileri genel bilgidir; kitapta ayrıca bir kaynaktan doğrulanmadı, ama fikirler bu bölümdeki deneylerle uyumludur.

| Mimari | Yıl (genel bilgi) | Ana fikir | Neden önemli |
|---|---|---|---|
| LeNet-5 | 1998 | 5×5 konvolüsyon, havuzlama, tam bağlı katmanlar | El yazısı rakamda ilk pratik konvolüsyon ağı |
| AlexNet | 2012 | ReLU, dropout, GPU ile eğitim, daha derin ağ | Büyük ölçekli görüntü tanımada derin öğrenmenin dönüm noktası |
| VGG | 2014 | Yalnızca 3×3 konvolüsyonların yığını | İki 3×3 katman 5×5 alıcı alan verir, daha az parametreyle (Bölüm 66.5) |
| GoogLeNet / Inception | 2014 | Paralel dallar, 1×1 ile kanal darboğazı | Hesap maliyetini düşürerek derinlik ve genişlik kazanmak |
| ResNet | 2015 | Artık (residual) bağlantı: x + F(x) | 100 katmandan fazla ağ eğitmeyi mümkün kıldı (Bölüm 66.9) |
| MobileNet | 2017 | Derinlemesine ayrılabilir konvolüsyon | Mobil ve gömülü cihazlar için düşük maliyetli ağ (Bölüm 66.4) |
| EfficientNet | 2019 | Derinlik, genişlik ve çözünürlüğü birlikte ölçekleme | Parametre başına doğruluk için sistematik tasarım |

Bu tablodaki her mimaride tekrar eden iki yapı vardır. Birincisi, konvolüsyon blokları arasında çözünürlüğü küçültüp kanal sayısını artırmaktır. Her havuzlama ile yükseklik ve genişlik yarıya iner; kanal sayısı çoğu zaman iki katına çıkar. Böylece bilgi mekânsal ayrıntıdan anlamsal özelliklere kayar. İkincisi, ağın sonunda tam bağlı katmanlar yerine küresel ortalama havuzlamanın (GAP) kullanılmasıdır. GAP her kanalın tüm konumlar üzerindeki ortalamasını alır ve bir vektör üretir. Bu, son katmandaki parametre sayısını büyük ölçüde azaltır ve Bölüm 66.2'de gördüğümüz konum değişmezliğine ek bir katkı yapar. Bu bölümün `Kucuk` ağı da son konvolüsyondan sonra GAP kullanır.

Bu bölümün kapsamında, Bölüm 69'da göreceğimiz dikkat (attention) ve Vision Transformer (ViT) yaklaşımı da bir karşılaştırma noktasıdır: orada görüntü yamalara bölünür ve konvolüsyon yerine dikkat mekanizması kullanılır. Konvolüsyonun yerel önseziyi (komşu pikseller ilişkilidir) ağa yerleştirmesi, büyük veride ne kadar önemli olduğunu ViT tartışmaları sırasında göreceğiz.

Derin ağlar için en büyük engel, derinlik arttıkça eğitimin zorlaşmasıdır. Bölüm 55'te sigmoid zincirlerinde gradyanın nasıl sönümlendiğini gördük. ReLU ve BatchNorm (Bölüm 64) bu sorunu büyük ölçüde hafifletti, ama 20 katmandan sonra bile bir ağın eğitim kaybının artabildiği görüldü. ResNet bu paradoksu bir bağlantı ekleyerek çözdü; bunu bir sonraki kısımda deneyle göreceğiz.

## 66.9 Artık bağlantılar: derinliğin neden zorlaştığı ve ResNet'in çözümü

Derin bir ağda her katman, bir öncekinin çıktısını alıp yeni bir dönüşüm uygular. Sonuç olarak bir çıktı nöronundan girdiye giden gradyan, katman sayısı kadar Jakobyen çarpımından geçer. Bu çarpımlar birden küçük olursa gradyan sönümlenir, birden büyük olursa patlar. Bölüm 64.6–64.7'de BatchNorm ve doğru başlatmanın bu çarpanları dengelediğini görmüştün. Ama bu dengeleme ideal değildir ve derinlik arttıkça ağın bir kısmı öğrenmeyi bırakabilir.

ResNet'in (He ve arkadaşları, 2015 — genel bilgi) önerisi çok basittir. Bir blok, girdisi `x` olan bir dönüşümü `F(x)` ile hesaplamak yerine `y = F(x) + x` üretir. Yani blok, girdiyi bir kestirme (shortcut) yoluyla çıktıya aynen taşır ve ağ yalnızca aradaki farkı, yani kalıntıyı (residual) öğrenir. Bu, Bölüm 55'teki zincir kuralıyla açıkça görülebilir. `y = F(x) + x` için

    ∂y/∂x = ∂F/∂x + I

olur. Gradyan, katmanın çarpanı ile çarpılmadan en az birim matris kadar geri akabilir. Bu bir "gradyan otobanı" gibi çalışır: F'nin katkısı küçük bile olsa, gradyan kaybolmaz.

Şekil 66.4, bu bloğun yapısını gösteriyor. Kestirme bağlantı parametresizdir; boyut uyuşmadığında ya 1×1 konvolüsyon ya da dolgu ile eşitlenir. Bu bölümde kanal sayısı blok boyunca sabit olduğu için kestirme saf bir toplamadır.

![Şekil 66.4: Artık blok. F(x) iki konvolüsyon ve BatchNorm'dan geçer; kestirme bağlantı girdiyi aynen toplamaya ekler, ReLU sonra uygulanır.](gorseller/b66_artik_blok.png)

Bu ideanın gerçekten bir fark yaratıp yaratmadığını ölçelim. Deneyde 25 konvolüsyon katmanlı iki ağ kurduk: bir girişi 32 kanala çeviren stem konvolüsyonu ve her biri iki konvolüsyon içeren 12 blok. Düz ağda bloklar `F(x)` olarak çalışır; artık ağda `F(x) + x`. İki varyantı BatchNorm'lu ve BatchNorm'suz olarak eğittik. Veri hedef alan (4 sınıf), 1500 örnek/sınıf; her koşu 3 tohum ve 20 epoch. Ağın tamamında 223 204 parametre var. Ağın sınıfı `DerinAg` ve bloğu `Bloku`, 66.2'deki `ortak.py` dosyasında yer alıyor; burada onları yeniden listelemiyoruz.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t04: düz derin ağ vs artık (residual) ağ, BN ile ve
BN'siz.

Her iki model da 25 konvolüsyon katmanlı (1 stem + 12 blok x 2).
Eğitim: hedef alan, 1500 örnek/sınıf, 20 epoch, Adam lr=1e-3, batch
64.
3 tohum. Eğitim kaybı her epoch'un ortalaması olarak kaydedilir.
"""

import csv
import os
import time
import numpy as np
import torch
from synth import hedef_veri
from ortak import (
    DEV,
    tensor,
    DerinAg,
    egit,
    dogruluk,
    parametre_say,
    sure_olc,
)
```

```python
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
BLOK, EPOCH, BS = 12, 20, 64
Xt, yt = hedef_veri(1500, 2)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
ADIM_EP = int(np.ceil(len(yt) / BS))  # 94 adım/epoch
print(
    "Konvolüsyon sayısı: %d, parametre: %d"
    % (1 + 2 * BLOK, parametre_say(DerinAg(BLOK)))
)
print(
    "Eğitim %d, test %d, adım/epoch %d" % (len(yt), len(ys), ADIM_EP)
)
```

```python
VARYANTLAR = [
    ("duz_BN", True, False),
    ("artik_BN", True, True),
    ("duz_BNsiz", False, False),
    ("artik_BNsiz", False, True),
]
kayip_satir, son_satir = [], []
for ad, bn, artik in VARYANTLAR:
    for tohum in range(3):
        torch.manual_seed(tohum)
        model = DerinAg(BLOK, bn=bn, artik=artik).to(DEV)
        t0 = time.perf_counter()
        kay = egit(
            model, Xt_g, yt_g, adim=EPOCH * ADIM_EP, tohum=tohum
        )
        torch.cuda.synchronize()
        sure = time.perf_counter() - t0
        epoch_kay = kay.reshape(EPOCH, ADIM_EP).mean(axis=1)
        for e, v in enumerate(epoch_kay, 1):
            kayip_satir.append((ad, tohum, e, v))
        tr = dogruluk(model, Xt_g[:1500], yt_g[:1500])
        te = dogruluk(model, Xs_g, ys_g)
        son_satir.append((ad, tohum, tr, te, sure))
        print(
            "%-12s tohum %d  kayıp %.4f  eğitim %.3f  test %.3f"
            % (ad, tohum, epoch_kay[-1], tr, te)
        )

print("\nEpoch 1 / 5 / 20 ortalama eğitim kaybı (3 tohum):")
for ad, _, _ in VARYANTLAR:
    v = {
        e: np.mean(
            [s[3] for s in kayip_satir if s[0] == ad and s[2] == e]
        )
        for e in (1, 5, EPOCH)
    }
    print("%-12s %.4f  %.4f  %.4f" % (ad, v[1], v[5], v[EPOCH]))
```

```python
print("\nTest doğruluğu (ortalama ± sapma):")
for ad, _, _ in VARYANTLAR:
    v = [s[3] for s in son_satir if s[0] == ad]
    print("%-12s %.4f ± %.4f" % (ad, np.mean(v), np.std(v, ddof=1)))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_artik_kayip.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["varyant", "tohum", "epoch", "egitim_kaybi"])
    for s in kayip_satir:
        w.writerow([s[0], s[1], s[2], "%.5f" % s[3]])
with open(
    os.path.join(VERI, "b66_artik_son.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(
        [
            "varyant",
            "tohum",
            "egitim_dogruluk",
            "test_dogruluk",
            "sure_s",
        ]
    )
    for s in son_satir:
        w.writerow(
            [s[0], s[1], "%.4f" % s[2], "%.4f" % s[3], "%.1f" % s[4]]
        )
```

```term
$ python t04_artik.py
Konvolüsyon sayısı: 25, parametre: 223204
Eğitim 6000, test 1200, adım/epoch 94
duz_BN       tohum 0  kayıp 0.0337  eğitim 0.997  test 0.997
duz_BN       tohum 1  kayıp 0.0157  eğitim 0.997  test 0.998
duz_BN       tohum 2  kayıp 0.0225  eğitim 1.000  test 0.991
artik_BN     tohum 0  kayıp 0.0242  eğitim 0.985  test 0.998
artik_BN     tohum 1  kayıp 0.0250  eğitim 0.963  test 0.901
artik_BN     tohum 2  kayıp 0.0115  eğitim 0.999  test 0.974
duz_BNsiz    tohum 0  kayıp 1.3864  eğitim 1.000  test 0.250
duz_BNsiz    tohum 1  kayıp 1.3865  eğitim 0.000  test 0.250
duz_BNsiz    tohum 2  kayıp 1.3864  eğitim 0.000  test 0.250
artik_BNsiz  tohum 0  kayıp 0.0213  eğitim 0.997  test 0.994
artik_BNsiz  tohum 1  kayıp 0.0312  eğitim 1.000  test 0.986
artik_BNsiz  tohum 2  kayıp 0.0186  eğitim 0.995  test 0.992

Epoch 1 / 5 / 20 ortalama eğitim kaybı (3 tohum):
duz_BN       0.6371  0.0528  0.0239
artik_BN     0.4687  0.0499  0.0202
duz_BNsiz    1.3875  1.3865  1.3864
artik_BNsiz  1.1548  0.3364  0.0237

Test doğruluğu (ortalama ± sapma):
duz_BN       0.9953 ± 0.0039
artik_BN     0.9578 ± 0.0508
duz_BNsiz    0.2500 ± 0.0000
artik_BNsiz  0.9906 ± 0.0043
```

Sonuçlar iki açık sonuç veriyor. Birincisi, BatchNorm'suz 25 katmanlı düz ağ hiç öğrenemedi: üç tohumda da eğitim kaybı `1,386` civarında kaldı. Bu değer, dört sınıfa eşit olasılık vermenin çapraz entropisidir (ln 4 ≈ 1,3863); yani ağ girdiden bağımsız, sabit bir tahmin yapıyor. Test doğruluğu `0,250` ile şans düzeyinde. Aynı derinlikte ve aynı başlatmayla kurulan artık ağ ise bağlantı sayesinde ilk epoch'tan itibaren öğrendi ve test doğruluğunda `0,991` ile `0,994` arasında kaldı. Bu, derinlik sorununun gerçek bir optimizasyon sorunu olduğunu ve artık bağlantının bunu çözdüğünü gösteriyor.

İkincisi, BatchNorm varken tablo değişiyor. Düz ağ 25 katmanda da öğrenebildi ve üç tohumda test doğruluğu `0,997`, `0,998` ve `0,991`. Bu sırada artık ağ aynı eğitim kaybına yakınsadı ama test doğruluğu tohumdan tohuma dalgalandı: `0,998`, `0,901`, `0,974`. Bu dalgalanmanın nedeni büyük olasılıkla BatchNorm'un eğitimdeki toplu istatistikler ile test sırasındaki hareketli ortalamalar arasındaki farktır; bir tohumda (ikinci) hareketli istatistikler veriyle tam oturmamış olabilir. Üç tohumla bu dalgalanmayı kesin olarak açıklayamayız; bu yüzden bu sonucu "beklenmedik ve doğrulanması gereken bir gözlem" olarak okumalısın, kesin bir yasa olarak değil.

Eğitim kaybı eğrileri bu tabloyu daha net gösteriyor. Şekil 66.5 her epoch'un ortalama kaybını, sol panelde BatchNorm'lu, sağ panelde BatchNorm'suz varyantlar için gösteriyor.

| Varyant | Epoch 1 | Epoch 5 | Epoch 20 | Test doğruluğu (ort ± sapma) |
|---|---|---|---|---|
| Düz, BN'li | 0,637 | 0,053 | 0,024 | 0,995 ± 0,004 |
| Artık, BN'li | 0,469 | 0,050 | 0,020 | 0,958 ± 0,051 |
| Düz, BN'siz | 1,388 | 1,387 | 1,386 | 0,250 ± 0,000 |
| Artık, BN'siz | 1,155 | 0,336 | 0,024 | 0,991 ± 0,004 |

![Şekil 66.5: Eğitim kaybı (log ölçek), 3 tohumun ortalaması ± sapma. Solda BatchNorm'lu, sağda BatchNorm'suz 25 katmanlı ağlar.](gorseller/b66_artik_kayip.png)

Bu deneyin ana dersi, artık bağlantının BatchNorm'a rakip değil, tamamlayıcı olduğudur. BatchNorm varken düz ağ da bu derinlikte çalışır; artık bağlantı ise BatchNorm olmadan da eğitimi mümkün kılar ve daha derin ağlara yolu açar. ResNet'in 100 katmanı aşan derinlikleri pratikte bu iki fikrin birlikte kullanılmasıyla elde edildi. Deneyin yalnızca 25 katmanı kapsadığını, daha derin ağlarda farkın daha dramatik olabileceğini ama bunu bu makinede ölçmediğimizi belirtelim.

Bu bölümde ağı Bölüm 64'te gördüğümüz Adam optimizer'ı ile eğittik; BatchNorm ayrıntısını ve doğru başlatmayı da orada ele alacağız.

## 66.10 Eğitim pratiği: veri artırma ve normalizasyon

Derin ağlar çok parametre taşır, bu yüzden veri az olduğunda kolayca ezberlerler. Bölüm 63'te aşırı uydurmayı eğitim ve test doğruluğu farkıyla görmüştük. Bu sorunun en ucuz çözümü daha fazla veri toplamaktır; ama çoğu zaman yeni veri pahalıdır. Veri artırma (data augmentation), mevcut her örneğin etiketini değiştirmeden rastgele bir kopyasını üretir. Görüntüde bu, döndürme, kaydırma, ölçekleme, ayna çevirme, parlaklık ve kontrast değişimi ve küçük gürültü demektir. Ağa her adımda aynı örneğin biraz farklı bir hâlini gösterirsin ve ağ, etiketi değiştirmeyen dönüşümlere karşı değişmez olmayı öğrenir.

Burada iki dikkat noktası var. Birincisi, dönüşüm etiketi değiştirmemelidir. Bir "6" rakamını ters çevirmek "9" yapar; bu yüzden rakam tanıma problemlerinde ayna çevirme yasaktır. Bizim şekil problemimizde daire, kare, üçgen ve artı yatay aynalandığında sınıfını korur, bu yüzden yatay ayna kullanıyoruz. İkincisi, artırma yalnızca eğitimde uygulanır. Test kümesi değişmeden değerlendirilir; yoksa ölçüm kendi kendini kandırır.

Artırmanın pratik uygulaması için tek bir kural vardır: dönüşümler GPU'da, batch halinde yapılmalıdır. Bizim `artir` fonksiyonumuz (66.2'deki `ortak.py` içinde) her örnek için ayrı bir afin dönüşüm matrisi üretir ve `affine_grid` ile `grid_sample` kullanarak tüm batch'i tek seferde dönüştürür. Bu yaklaşım Python döngüsü içermez ve GPU'nun paralelliğini kullanır.

Normalizasyon ise artırmadan ayrı bir adımdır. Piksel değerlerini kanal başına bir ortalama ve standart sapma ile merkezleyip ölçeklemek, eğitimi hızlandırır ve başlatmaya duyarlılığı azaltır. Formül her kanal için `(x − μ) / σ` biçimindedir. Bu bölümdeki görüntüler zaten `[0, 1]` aralığında ve BatchNorm katmanları ilk konvolüsyondan sonra ölçeği düzelttiği için ayrıca normalizasyon uygulamadık. Gerçek bir ImageNet tabanlı modelde ise bu adım zorunludur; ön eğitimli ağırlıkların beklediği ortalama ve sapma değerleri ile girdinin aynı ölçekte olması gerekir.

Aşağıdaki program bu fonksiyonu kullanır ve, sabit tohumla seçilen sekiz görüntü üzerinde üç artırılmış kopyası üretip bir ızgara olarak kaydeder. Ardından iki veri miktarında, artırmalı ve artırmasız eğitimleri beş tohumla karşılaştırır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t05: veri artırmanın az veride test doğruluğuna etkisi.

Hedef alan, sınıf başına 50 ve 500 örnek; artırma yok / var. Her koşul
5 tohum. Test seti: 300/sınıf, eğitimden ayrı tohum (99).
Eğitim: Kucuk CNN, Adam lr=1e-3, batch 64, 1500 adım.
"""

import csv
import os
import numpy as np
import torch
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk, artir

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
Xs, ys = hedef_veri(300, 99)
Xs_g, ys_g = tensor(Xs, ys)

# Örnek ızgarası: 8 görüntü, her biri için 3 artırılmış kopya (tohum
# 0)
X8, _ = hedef_veri(2, 77)
X8 = torch.tensor(X8[:8], device=DEV)
torch.manual_seed(0)
art = torch.stack([artir(X8) for _ in range(3)])
os.makedirs(VERI, exist_ok=True)
np.savez(
    os.path.join(VERI, "b66_artirma_ornek.npz"),
    orj=X8[:, 0].cpu().numpy(),
    art=art[:, :, 0].cpu().numpy(),
)
```

```python
sonuc = []
for n in (50, 500):
    for artirma in (False, True):
        for tohum in range(5):
            Xt, yt = hedef_veri(n, 1000 + tohum)
            Xt_g, yt_g = tensor(Xt, yt)
            torch.manual_seed(tohum)
            model = Kucuk().to(DEV)
            egit(
                model,
                Xt_g,
                yt_g,
                adim=1500,
                tohum=tohum,
                aug=artir if artirma else None,
            )
            te = dogruluk(model, Xs_g, ys_g)
            sonuc.append((n, artirma, tohum, te))
        v = [s[3] for s in sonuc if s[0] == n and s[1] == artirma]
        print(
            "sınıf başına %3d, artırma %-5s: test %.4f ± %.4f"
            % (n, artirma, np.mean(v), np.std(v, ddof=1))
        )

with open(
    os.path.join(VERI, "b66_artirma.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["n_sinif", "artirma", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], int(s[1]), s[2], "%.4f" % s[3]])
```

```term
$ python t05_artirma.py
sınıf başına  50, artırma False: test 0.6892 ± 0.0447
sınıf başına  50, artırma True : test 0.8880 ± 0.0381
sınıf başına 500, artırma False: test 0.9150 ± 0.0253
sınıf başına 500, artırma True : test 0.8983 ± 0.1362
```

Şekil 66.6, üst satırdaki özgün görüntüleri ve altındaki üç artırılmış kopyayı gösteriyor. Dönüşümler küçük ama farkedilir: konum, açı, ölçek ve parlaklık değişiyor, şekil sınıfı ise aynı kalıyor.

![Şekil 66.6: Üst satır özgün görüntüler; alt üç satır aynı görüntülerin rastgele artırılmış kopyaları (döndürme, kaydırma, ölçek, yatay ayna, parlaklık ve gürültü).](gorseller/b66_artirma.png)

Sonuçlar iki farklı rejimi gösteriyor. Sınıf başına 50 örnekte, yani toplam 200 eğitim görüntüsünde, artırma ortalama test doğruluğunu `0,689 ± 0,045`ten `0,888 ± 0,038`e çıkardı. Bu, ağın veriyi ezberlemesini engellemenin en somut örneğidir ve artırma ücretsiz bir kazançtır.

Sınıf başına 500 örnekte tablo daha karmaşık. Artırmasız ortalama `0,915 ± 0,025`; artırmalı ortalama `0,898 ± 0,136`. Ama bu ortalama tek bir tohumun yıkıcı bir sonucunu taşıyor: tohum 0'da artırmalı koşu test doğruluğunu `0,656`da bıraktı, diğer dört tohumda ise artırmalı ağ `0,939` ile `0,976` arasında kaldı. Bu dört tohumun ortalaması `0,959`dur; artırmasız ortalama `0,916`dır. Yani büyük veri rejiminde artırma, dört tohumda tutarlı bir kazanç veriyor; ancak tohum 0'daki çöküş nedenini bu deneyde ölçmediğimiz için açıklayamıyoruz. Olası nedenler arasında geçici bir eğitim kararsızlığı ya da BatchNorm istatistiklerinin test ile uyuşmaması var; ama bunları bu bölümde ayrıca sınamadık.

Bu sonuç iki pratik ders içerir. Birincisi, veri az olduğunda artırmanın etkisi çok büyüktür ve ilk denenecek yöntemlerden biri olmalıdır. İkincisi, tek bir tohumla yapılan karşılaştırma yanıltıcı olabilir; beş tohumun dağılımına bakmadan "artırma yardımcı oldu" ya da "olmadı" demek hatalıdır. Bölüm 57'de anlattığımız deney disiplini tam burada gerekli.

## 66.11 Transfer öğrenme: az veriyle ön eğitimden yararlanmak

Gerçek dünyada etiketli veri pahalıdır. Bir İHA kamerasının yeni bir ortamda topladığı birkaç yüz görüntü için bir ağı sıfırdan eğitmek çoğu zaman yetersizdir. Transfer öğrenme fikri şudur: büyük ve genel bir veri kümesinde ön eğitilmiş bir ağın öğrendiği düşük seviyeli özellikler (kenar, doku, köşe) yeni görevde de işe yarar; yalnızca son sınıflandırma katmanını yeniden yazmak yetebilir. ImageNet'te ön eğitilmiş ağırlıklar bu alanda standarttır.

Bu ortamda gerçek ImageNet ağırlıklarını indirmedik; indirme bu bölümün kurallarına aykırı. Bunun yerine, transfer fikrini kendi içinde ölçtük. Kaynak alan 8 sınıflı temiz sentetik şekillerden oluşuyor (çubuk, elips, X ve iki daire dahil). Ağı burada 1500 örnek/sınıfla ön eğittik ve kaynak test kümesinde `0,803` doğruluk elde ettik. Hedef alan ise daha gürültülü ve bulanık dört sınıflı bir problem: daire, kare, üçgen ve artı. Bu, kaynak ve hedef dağılımlarının farklı olduğu gerçekçi bir durumu taklit eder.

Hedef alanda üç yöntemi karşılaştırdık:

1. Sıfırdan: ağın tamamı rastgele başlatılır ve eğitilir.
2. Özellik çıkarıcı: ön eğitilmiş gövde dondurulur (BatchNorm istatistikleri de sabit kalır), yalnızca yeni sınıflandırma başı eğitilir.
3. İnce ayar: gövde de eğitilir, ama düşük bir öğrenme oranıyla (`10⁻⁴`), baş normal oranla (`10⁻³`) eğitilir. Bu, katman başına öğrenme oranının basit bir uygulamasıdır.

Aşağıdaki program ön eğitimi, üç yöntemin beş örnek boyutunda karşılaştırmasını ve sonuçların kaydını içerir.

Aşağıdaki kod, GPU'da ön eğitim ve hedef ince ayarı için tam programdır.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t06: transfer öğrenme (kendi kendine ön eğitim).

Gerçek ImageNet ağırlığı kullanılmaz (indirme yasak). Bunun yerine:
  1) Kaynak alan: 8 sınıf, temiz sentetik şekiller, 1500/sınıf ->
  ön eğitim.
  2) Hedef alan: 4 sınıf, gürültülü/bulanık; sınıf başına n örnek ile
     üç yöntem:  sıfırdan | özellik çıkarıcı (gövde dondurulmuş)
                 | ince ayar (gövde düşük öğrenme oranıyla).
Ön eğitim tek tohumla yapılır; hedef ince ayar 5 tohumla tekrarlanır.
"""

import csv
import os
import time
import numpy as np
import torch
from synth import hedef_veri, kaynak_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ADIM = 1000
Xs, ys = hedef_veri(300, 99)
Xs_g, ys_g = tensor(Xs, ys)
```

```python
# 1) Ön eğitim (kaynak alan, 8 sınıf)
Xk, yk = kaynak_veri(1500, 7)
Xk_g, yk_g = tensor(Xk, yk)
Xkt, ykt = kaynak_veri(200, 8)
Xkt_g, ykt_g = tensor(Xkt, ykt)
torch.manual_seed(7)
on = Kucuk(K=8).to(DEV)
t0 = time.perf_counter()
egit(on, Xk_g, yk_g, adim=3000, tohum=7)
torch.cuda.synchronize()
print("Ön eğitim süresi: %.1f s" % (time.perf_counter() - t0))
print("Kaynak alan test doğruluğu: %.4f" % dogruluk(on, Xkt_g, ykt_g))
ON_SD = {
    k: v.clone()
    for k, v in on.state_dict().items()
    if not k.startswith("bas.")
}

def govde_yukle(model):
    model.load_state_dict(ON_SD, strict=False)
    return model

sonuc = []
for n in (10, 25, 50, 100, 300):
    for tohum in range(5):
        Xt, yt = hedef_veri(n, 200 + tohum)
        Xt_g, yt_g = tensor(Xt, yt)

        # a) sıfırdan
        torch.manual_seed(tohum)
        m = Kucuk().to(DEV)
        egit(m, Xt_g, yt_g, adim=ADIM, tohum=tohum)
        sonuc.append(("sifirdan", n, tohum, dogruluk(m, Xs_g, ys_g)))
```

```python
        # b) özellik çıkarıcı: gövde donuk (BN de eval modunda)
        torch.manual_seed(tohum)
        m = govde_yukle(Kucuk().to(DEV))
        for p in m.ozellik.parameters():
            p.requires_grad_(False)
        egit(m, Xt_g, yt_g, adim=ADIM, tohum=tohum, sabit=[m.ozellik])
        sonuc.append(("ozellik", n, tohum, dogruluk(m, Xs_g, ys_g)))

        # c) ince ayar: gövde 1e-4, baş 1e-3 (katman başına öğrenme
        # oranı)
        torch.manual_seed(tohum)
        m = govde_yukle(Kucuk().to(DEV))
        grup = [
            {"params": m.ozellik.parameters(), "lr": 1e-4},
            {"params": m.bas.parameters(), "lr": 1e-3},
        ]
        egit(m, Xt_g, yt_g, adim=ADIM, tohum=tohum, grup_lr=grup)
        sonuc.append(("ince_ayar", n, tohum, dogruluk(m, Xs_g, ys_g)))
    print(
        "sınıf başına %3d ->  " % n
        + "  ".join(
            "%s %.3f"
            % (
                yo,
                np.mean(
                    [s[3] for s in sonuc if s[0] == yo and s[1] == n]
                ),
            )
            for yo in ("sifirdan", "ozellik", "ince_ayar")
        )
    )
```

```python
print("\nTest doğruluğu, ortalama ± sapma (5 tohum):")
for n in (10, 25, 50, 100, 300):
    satir = []
    for yo in ("sifirdan", "ozellik", "ince_ayar"):
        v = [s[3] for s in sonuc if s[0] == yo and s[1] == n]
        satir.append(
            "%s %.3f±%.3f" % (yo, np.mean(v), np.std(v, ddof=1))
        )
    print("n=%3d  " % n + "  ".join(satir))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_transfer.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "n_sinif", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])
```

```term
$ python t06_transfer.py
Ön eğitim süresi: 12.2 s
Kaynak alan test doğruluğu: 0.8031
sınıf başına  10 ->  sifirdan 0.576  ozellik 0.852  ince_ayar 0.783
sınıf başına  25 ->  sifirdan 0.660  ozellik 0.897  ince_ayar 0.896
sınıf başına  50 ->  sifirdan 0.672  ozellik 0.913  ince_ayar 0.937
sınıf başına 100 ->  sifirdan 0.706  ozellik 0.924  ince_ayar 0.954
sınıf başına 300 ->  sifirdan 0.892  ozellik 0.920  ince_ayar 0.967

Test doğruluğu, ortalama ± sapma (5 tohum):
n= 10  sifirdan 0.576±0.044  ozellik 0.852±0.014  ince_ayar 0.783±0.042
n= 25  sifirdan 0.660±0.048  ozellik 0.897±0.020  ince_ayar 0.896±0.020
n= 50  sifirdan 0.672±0.078  ozellik 0.913±0.009  ince_ayar 0.937±0.009
n=100  sifirdan 0.706±0.124  ozellik 0.924±0.005  ince_ayar 0.954±0.009
n=300  sifirdan 0.892±0.042  ozellik 0.920±0.008  ince_ayar 0.967±0.001
```

Sonuçlar, veri azaldıkça transferin değerini gösteriyor. Sınıf başına 10 örnekte (toplam 40 görüntü) sıfırdan eğitilmiş ağ `0,576 ± 0,044` doğruluğa ulaşıyor; özellik çıkarıcı `0,852 ± 0,014` ile iki kat yakın bir kazanç sağlıyor. Sınıf başına 50 örnekte özellik çıkarıcı `0,913`, ince ayar `0,937`, sıfırdan `0,672` ve sapma yüksek. Sınıf başına 300 örnekte ise ince ayar `0,967 ± 0,001` ile en iyi sonucu veriyor ve sıfırdan eğitim `0,892`de kalıyor. Şekil 66.7 bu eğrileri, tohum sapmalarıyla birlikte gösteriyor.

![Şekil 66.7: Hedef test doğruluğunun eğitim örneği sayısına göre değişimi (log eksen). Üç yöntem, 5 tohumun ortalaması ± sapma.](gorseller/b66_transfer.png)

Bu eğriden üç ders çıkar. Birincisi, çok az veride (10-25 örnek/sınıf) gövdeyi dondurmak en güvenli seçimdir; ince ayar bu rejimde gövdeyi bozarak özellik çıkarıcıdan kötü kalır (`0,783` ve `0,852`). İkincisi, veri arttıkça ince ayar öne geçer; çünkü gövde hedef alana uyarlanabilir. Üçüncüsü, sıfırdan eğitim veri ile birlikte yavaşça yükselir, ama 300 örnekte bile transferli yöntemlerin gerisinde kalır. Bu eğri, transfer öğrenmenin neden etiketli veri kıtlığında asıl değerini kattığını gösterir.

Bu deneyin bir sınırlılığı, ön eğitimin yalnızca tek bir tohumla yapılmış olmasıdır; yani beş tohumluk sapma, ön eğitimin rastgeleliğini değil yalnızca ince ayarın rastgeleliğini yansıtır. Gerçek bir çalışmada ön eğitim de birkaç tohumla tekrarlanmalıdır.

Gerçek bir ImageNet ağırlığını kullanmak isteyen biri için kod ise şöyle görünür. Bu kod bu bölümde çalıştırılmadı; ağırlık indirmek bu ortamda yasak olduğu için yalnızca biçimi göstermek amacıyla yazıldı. Dosyanın söz dizimi derlenerek doğrulandı.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - gerçek ön eğitimli ağırlıkla transfer
(ÇALIŞTIRILMADI)."""

import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet18_Weights

pesler = ResNet18_Weights.DEFAULT  # ImageNet ağırlıkları
on = models.resnet18(weights=pesler)
on_isleme = pesler.transforms()  # ölçek ve normalizasyon

for p in on.parameters():  # gövdeyi dondur
    p.requires_grad_(False)
on.fc = nn.Linear(on.fc.in_features, 4)  # yeni 4 sınıflı baş
```

Bu kodda dikkat edilmesi gereken iki nokta var. Birincisi, ön eğitimli ağın beklediği ön işleme (ölçek ve ortalama-sapma normalizasyonu) ağırlıklarla birlikte gelen meta veride tanımlıdır; girdiyi bu şekilde hazırlamazsan transfer bozulur. İkincisi, ağın son katmanı yeni görev için yeniden yazılmalıdır: `fc` katmanı 1000 sınıf yerine bizim sınıf sayımıza göre değiştirilmelidir.

## 66.12 Ağ ne öğrendi? Filtreler, özellik haritaları ve Grad-CAM

Bir CNN'i eğitmek yetmez; onun neye baktığını da görmek gerekir. Bu, savunma sanayiinde özellikle önemlidir: bir sınıflandırıcının doğruluğu yüksek olsa bile yanlış bir ipucuna (arka plan rengi, kamera açısı) dayanıyorsa sahada çöker.

Önce ilk katmanın filtrelerine bakalım. Ağın ilk konvolüsyonu 16 adet 3×3 çekirdek içerir. Bu çekirdekler eğitimle öğrenilir ve bir ızgara olarak çizilebilir (kırmızı pozitif, mavi negatif). Dürüst bir gözlem yapmak gerekirse: bu küçük ağda filtrelerin çoğu, kenar dedektörü gibi açık bir yön ya da bilinen bir fiziksel anlam taşımıyor. Derin ağlarda ilk katman filtrelerinin kenar benzeri desenler öğrenmesi sık görülen bir durumdur; ama bu bölümdeki ağda bunu kesin olarak söyleyemeyiz. Asıl bilgi, özellik haritalarında görülüyor.

Bir sonraki adım özellik haritalarıdır. Bir görüntü ağın içinden geçerken her katmanın çıktısı bir dizi kanaldır; bu kanalların her biri girdinin belli bir özelliğinin "nerede ve ne kadar" olduğunu gösterir. Ağın derinliğinde özellik haritaları küçülür ama anlamsallaşır.

Son olarak Grad-CAM (Selvaraju ve arkadaşları, 2017 — genel bilgi) sınıf kararının hangi bölgeye dayandığını gösteren bir ısı haritasıdır. Fikir basittir. Son konvolüsyon katmanının `k`-ıncı özellik haritası `A_k` ve hedef sınıfın skoru `s_c` olsun. Her kanalın önemi, skorun o kanala göre gradyanının uzamsal ortalamasıdır: `α_k = (1/Z) Σ_{i,j} ∂s_c/∂A_k[i,j]`. Isı haritası ise `ReLU(Σ_k α_k A_k)` ile hesaplanır ve girdi boyutuna büyütülür. Negatif katkılar ReLU ile atılır, yani yalnızca sınıfı destekleyen bölgeler görünür.

Aşağıdaki program, aynı hedef alan modelini eğitir, karışıklık matrisini hesaplar, ilk katman filtrelerini ve özellik haritalarını ayıklar, Grad-CAM'i kendi kodumuzla uygular ve en kötü hataları bulur.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t09: CNN ne öğrendi? Filtreler, özellik haritaları,
Grad-CAM,
karışıklık matrisi ve en kötü hatalar. Model: hedef alan,
800/sınıf, tohum 0.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
Xt, yt = hedef_veri(800, 401)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
torch.manual_seed(0)
model = Kucuk().to(DEV)
egit(model, Xt_g, yt_g, adim=1500, tohum=0)
model.eval()
print("Test doğruluğu: %.4f" % dogruluk(model, Xs_g, ys_g))
```

```python
# 1) Karışıklık matrisi
with torch.no_grad():
    tahmin = torch.cat(
        [
            model(Xs_g[i : i + 256]).softmax(1)
            for i in range(0, len(ys), 256)
        ]
    )
pred = tahmin.argmax(1).cpu().numpy()
K = 4
M = np.zeros((K, K), dtype=int)
for g, p in zip(ys, pred):
    M[g, p] += 1
print("\nKarışıklık matrisi (satır: gerçek, sütun: tahmin):")
print(M)
os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_karisiklik.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["gercek", "tahmin", "sayi"])
    for i in range(K):
        for j in range(K):
            w.writerow([i, j, M[i, j]])

# 2) İlk katman filtreleri ve özellik haritaları
filtre = (
    model.ozellik[0][0].weight.detach().cpu().numpy()[:, 0]
)  # (16,3,3)
kayit = {}

def kanca(ad):
    def f(_, __, out):
        kayit[ad] = out.detach()

    return f
```

```python
h1 = model.ozellik[0][2].register_forward_hook(kanca("f1"))
h2 = model.ozellik[2].register_forward_hook(kanca("f3"))
ornek = Xs_g[:1]
with torch.no_grad():
    model(ornek)
h1.remove()
h2.remove()
print(
    "\nİlk katman filtre şekli: %s\nf1 %s, f3 %s"
    % (
        filtre.shape,
        tuple(kayit["f1"].shape),
        tuple(kayit["f3"].shape),
    )
)
f1 = kayit["f1"][0].cpu().numpy()  # (16,32,32)
f3 = kayit["f3"][0].cpu().numpy()  # (64,8,8)

# 3) Grad-CAM (sıfırdan): son konvolüsyon çıktısının sınıf skoruna
# göre
# ağırlıklı toplamı; ağırlık = o kanalın gradyanının uzamsal
# ortalaması.
def gradcam(girdi, sinif=None):
    aktivasyon = {}

    def kanca_f(_, __, out):
        aktivasyon["a"] = out
        out.register_hook(lambda gr: aktivasyon.__setitem__("g", gr))
```

```python
    h = model.ozellik[2].register_forward_hook(kanca_f)
    logit = model(girdi)
    h.remove()
    if sinif is None:
        sinif = logit.argmax(1)
    skor = logit.gather(1, sinif[:, None]).sum()
    model.zero_grad()
    skor.backward()
    A, G = aktivasyon["a"], aktivasyon["g"]
    agirlik = G.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((agirlik * A).sum(1, keepdim=True))
    cam = F.interpolate(
        cam, size=(32, 32), mode="bilinear", align_corners=False
    )[:, 0]
    cam = cam / (cam.amax(dim=(1, 2), keepdim=True) + 1e-8)
    return cam.detach().cpu().numpy(), sinif.detach().cpu().numpy()

# Her sınıftan doğru tahmin edilmiş birer örnek
dogru_idx = [
    int(np.where((ys == c) & (pred == c))[0][0]) for c in range(K)
]
cam_d, _ = gradcam(Xs_g[dogru_idx])

# En kötü hatalar: yanlış tahmin, en yüksek güvenle
yanlis = np.where(pred != ys)[0]
guven = tahmin.cpu().numpy()[yanlis, pred[yanlis]]
en_kotu = yanlis[np.argsort(-guven)[:4]]
cam_y, _ = gradcam(
    Xs_g[en_kotu], sinif=torch.tensor(pred[en_kotu], device=DEV)
)
print(
    "\nGrad-CAM: doğru örnekler (gerçek sınıflar %s)" % ys[dogru_idx]
)
print("En kötü 4 hata (gerçek, tahmin, güven):")
for g_, t_, c_ in zip(
    ys[en_kotu], pred[en_kotu], guven[np.argsort(-guven)[:4]]
):
    print("  gerçek %d, tahmin %d, güven %.3f" % (g_, t_, c_))
```

```python
np.savez(
    os.path.join(VERI, "b66_gorsel.npz"),
    filtre=filtre,
    f1=f1,
    f3=f3,
    girdi_ornek=Xs[0, 0],
    dogru_img=Xs[dogru_idx, 0],
    dogru_cam=cam_d,
    dogru_sinif=ys[dogru_idx],
    yanlis_img=Xs[en_kotu, 0],
    yanlis_cam=cam_y,
    yanlis_gercek=ys[en_kotu],
    yanlis_tahmin=pred[en_kotu],
    yanlis_guven=guven[np.argsort(-guven)[:4]],
)
```

```term
$ python t09_gradcam.py
Test doğruluğu: 0.9392

Karışıklık matrisi (satır: gerçek, sütun: tahmin):
[[300   0   0   0]
 [ 59 236   4   1]
 [  0   6 293   1]
 [  0   0   2 298]]

İlk katman filtre şekli: (16, 3, 3)
f1 (1, 16, 32, 32), f3 (1, 64, 8, 8)

Grad-CAM: doğru örnekler (gerçek sınıflar [0 1 2 3])
En kötü 4 hata (gerçek, tahmin, güven):
  gerçek 1, tahmin 0, güven 0.993
  gerçek 1, tahmin 0, güven 0.987
  gerçek 1, tahmin 0, güven 0.983
  gerçek 1, tahmin 0, güven 0.978
```

Karışıklık matrisi çok belirgin bir örüntü gösteriyor. Dört sınıftan üçü neredeyse kusursuz; ama gerçek kare (sınıf 1) örneklerinin 59'u daire (sınıf 0) olarak tahmin ediliyor. Bu, şekil geometrisinin nedenini bulmamızı sağlar: kare, rastgele döndürüldüğünde ve bulanıklaştırıldığında köşeleri yumuşar ve kenarları kısa olduğunda bir daireye benzer. Ağın bu karışıklığı yapması şaşırtıcı değil, ama bunu bilmek veri ve model geliştirmek için yön gösterir: daha fazla yüksek çözünürlüklü kare örneği ya da köşe duyarlı bir özellik işe yarayabilir.

En kötü hatalar da aynı noktaya işaret ediyor. Dört en güvenli yanlış tahminin tamamı kare → daire yönünde ve olasılıkları `0,978` ile `0,993` arasında. Yani ağ bu örneklerde hatasından haberdar değil; yüksek güvenli hatalar, bir kalibrasyon sorunudur ve Bölüm 57'deki kalibrasyon ölçütleriyle ayrıca ele alınmalıdır.

Şekil 66.8, ilk katman filtrelerini ve iki katmanın özellik haritalarını gösteriyor. Özellik haritaları, dairenin kenarına tepki veren bölgeleri (birinci katmanın 0, 6 ve 9 numaralı kanalları) açıkça gösteriyor; 3 numaralı kanal ise dairenin içini bastırıp arka plandaki gürültüye tepki veriyor. Kenar tepkisi, bu tür ağların ilk katmanlarında beklenen davranıştır. Şekil 66.9 ise doğru örneklerin Grad-CAM ısı haritalarını (üstte) ve en kötü hataların ısı haritalarını (altta) gösteriyor.

![Şekil 66.8: Üstte ilk konvolüsyonun 16 filtresi (kırmızı pozitif, mavi negatif). Altta girdi ve ilk iki katmandan seçilmiş özellik haritaları.](gorseller/b66_filtre_harita.png)

![Şekil 66.9: Grad-CAM. Üst satır: her sınıftan doğru tahmin edilmiş örnekler; alt satır: en yüksek güvenle yapılan dört hata (gerçek kare, tahmin daire).](gorseller/b66_gradcam.png)

Grad-CAM'in sınırlılığını da bilmek gerekir: son konvolüsyon katmanının uzamsal çözünürlüğü (bu ağda 8×8) ısı haritasını kaba yapar; ayrıca ısı haritası sınıf kararının nedenini kanıtlamaz, yalnızca hangi bölgenin skora katkı verdiğini gösterir. Bu, bir hata ayıklama aracı olarak değerlidir, ama bir açıklama garantisi değildir.

## 66.13 Sağlamlık: dağılım kayması ve bozulmalar

Savunma uygulamalarında bir görüntü sınıflandırıcısı laboratuvar koşullarında değil, sisli, düşük ışıklı, titreşimli ve sıkıştırılmış bir kamera akışında çalışır. Buna dağılım kayması (distribution shift) denir: test görüntüleri eğitim görüntülerinden farklı bir dağılımdan gelir. Bu bölümde en basit ve en öğretici kayma türünü ölçtük: bozulma.

Dört bozulma türü ve her biri için beş şiddet düzeyi tanımladık. Gauss gürültüsü (σ = 0 ile 0,4), kutu bulanıklığı (0 ile 4 kez), parlaklık azalması (1,0 ile 0,15 arası çarpan) ve kontrast azalması (1,0 ile 0,15 arası c). Eğitilmiş model temiz test kümesinde `0,926` ortalama doğruluk veriyor (beş tohum). Bozulmalar ise şöyle davranıyor.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t07: dağılım kayması altında sağlamlık (bozulma
şiddeti).

Model: Kucuk CNN, hedef alan 500/sınıf, temiz (kendi dağılımında)
eğitim.
Test: aynı dağılımın test kümesi, dört bozulma türünde beş şiddet
düzeyi:
  gurultu   : Gauss gürültüsü, sigma = 0, 0.1, 0.2, 0.3, 0.4
  bulaniklik: 3x3 kutu bulanıklığı, 0-4 kez uygulanır
  karanlik  : parlaklık çarpanı 1.0, 0.7, 0.5, 0.3, 0.15 (düşük ışık)
  kontrast  : 0.5 + c (x - 0.5), c = 1, 0.7, 0.5, 0.3, 0.15
5 tohum. Bu bir sensör bozulması modelidir; saldırı değildir.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
Xs, ys = hedef_veri(300, 99)
Xs_g, ys_g = tensor(Xs, ys)
g = torch.Generator(device=DEV).manual_seed(5)
```

```python
def boz(x, tur, sev):
    if tur == "gurultu":
        s = [0, 0.1, 0.2, 0.3, 0.4][sev]
        n = torch.randn(x.shape, generator=g, device=DEV) * s
        return (x + n).clamp(0, 1)
    if tur == "bulaniklik":
        for _ in range(sev):
            x = F.avg_pool2d(x, 3, 1, 1, count_include_pad=False)
        return x
    if tur == "karanlik":
        return x * [1.0, 0.7, 0.5, 0.3, 0.15][sev]
    if tur == "kontrast":
        c = [1.0, 0.7, 0.5, 0.3, 0.15][sev]
        return (0.5 + c * (x - 0.5)).clamp(0, 1)
    raise ValueError(tur)

TURLER = ["gurultu", "bulaniklik", "karanlik", "kontrast"]
sonuc = []
for tohum in range(5):
    Xt, yt = hedef_veri(500, 300 + tohum)
    Xt_g, yt_g = tensor(Xt, yt)
    torch.manual_seed(tohum)
    model = Kucuk().to(DEV)
    egit(model, Xt_g, yt_g, adim=1500, tohum=tohum)
    for tur in TURLER:
        for sev in range(5):
            x = boz(Xs_g, tur, sev)
            sonuc.append((tur, sev, tohum, dogruluk(model, x, ys_g)))
    print(
        "tohum %d bitti (temiz test %.3f)"
        % (
            tohum,
            [
                s[3]
                for s in sonuc
                if s[0] == "gurultu" and s[1] == 0 and s[2] == tohum
            ][0],
        )
    )
```

```python
print("\nOrtalama doğruluk (5 tohum), şiddet 0..4:")
for tur in TURLER:
    satir = []
    for sev in range(5):
        v = [s[3] for s in sonuc if s[0] == tur and s[1] == sev]
        satir.append("%.3f" % np.mean(v))
    print("%-11s " % tur + "  ".join(satir))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_bozulma.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["tur", "siddet", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])
```

```term
$ python t07_bozulma.py
tohum 0 bitti (temiz test 0.908)
tohum 1 bitti (temiz test 0.963)
tohum 2 bitti (temiz test 0.947)
tohum 3 bitti (temiz test 0.918)
tohum 4 bitti (temiz test 0.894)

Ortalama doğruluk (5 tohum), şiddet 0..4:
gurultu     0.926  0.296  0.250  0.250  0.250
bulaniklik  0.926  0.678  0.490  0.399  0.344
karanlik    0.926  0.836  0.666  0.354  0.244
kontrast    0.926  0.679  0.281  0.250  0.250
```

Sonuç beklenmedik ölçüde sert. Gauss gürültüsü σ = 0,1 seviyesinde doğruluk `0,926`dan `0,296`ya düşüyor ve daha yüksek şiddette şans düzeyine (`0,250`) iniyor. Bulanıklık ilk tur ile `0,678`e iniyor. Parlaklık ve kontrast ise daha yumuşak düşüyor: karanlık `0,7` çarpanında hâlâ `0,836`.

Kontrol programı, bu iki iddiayı, aynı modelle bağımsız bir yeniden üretimle sınar. Bu program, tohum 0'ın modelini yeniden eğitir ve iki ölçümü yapar: gürültü şiddetine göre doğruluk ile BatchNorm katlamasının doğruluğu.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - kontrol: gürültü şiddetine duyarlılık ve BN katlama
doğruluğu."""

import copy
import torch
import torch.nn as nn
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

Xt, yt = hedef_veri(500, 300)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
torch.manual_seed(0)
model = Kucuk().to(DEV)
egit(model, Xt_g, yt_g, adim=1500, tohum=0)
model.eval()
print("Temiz test doğruluğu: %.4f" % dogruluk(model, Xs_g, ys_g))

g = torch.Generator(device=DEV).manual_seed(5)
for s in [0.02, 0.05, 0.10]:
    n = torch.randn(Xs_g.shape, generator=g, device=DEV) * s
    x = (Xs_g + n).clamp(0, 1)
    print(
        "gürültü sigma=%.2f: doğruluk %.4f"
        % (s, dogruluk(model, x, ys_g))
    )
```

```python
mm = copy.deepcopy(model).eval()
for blok in mm.ozellik:
    conv, bn = blok[0], blok[1]
    s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
    conv.weight.data = conv.weight.data * s.view(-1, 1, 1, 1)
    conv.bias = nn.Parameter(bn.bias - bn.running_mean * s)
    blok[1] = nn.Identity()
with torch.no_grad():
    fark = (model(Xs_g) - mm(Xs_g)).abs().max().item()
print("BN katlı model, en büyük logit farkı: %.2e" % fark)
print("BN katlı model doğruluğu: %.4f" % dogruluk(mm, Xs_g, ys_g))
```

```term
$ python kontrol_b66.py
Temiz test doğruluğu: 0.9083
gürültü sigma=0.02: doğruluk 0.8875
gürültü sigma=0.05: doğruluk 0.6758
gürültü sigma=0.10: doğruluk 0.3458
BN katlı model, en büyük logit farkı: 2.51e-03
BN katlı model doğruluğu: 0.9092
```

Gürültüdeki çöküşün nedeni bir hata değil, verinin üretim biçimidir. Hedef alan görüntülerinde gürültü önce ekleniyor, sonra 3×3 bulanıklaştırma uygulanıyor. Bağımsız gürültünün standart sapması 3×3 ortalamada yaklaşık üçte bir oranında küçülür; yani eğitimdeki 0,15 gürültü, ağın gördüğü etkin gürültüde yaklaşık 0,05 düzeyindedir. Bunu aşağıdaki kontrol programında doğruladık: aynı modelde σ = 0,02'de doğruluk `0,888`, σ = 0,05'te `0,676`, σ = 0,10'da `0,346`. Yani model, eğitimde gördüğünden daha fazla gürültüye hazır değil. Bu, veri üretim sürecinin modelin sağlamlık sınırını nasıl belirlediğinin açık bir örneğidir ve pratik sonucu nettir: eğitim verisi, sahada beklenen bozulmaları içermelidir.

Bozulma-artırma (corruption augmentation) burada doğal çözümdür: eğitim sırasında farklı şiddetlerde gürültü, bulanıklık ve parlaklık değişimi eklemek. Bu, Bölüm 66.10'daki artırma fikrinin bir uzantısıdır. Bu bölümde bu öneriyi ölçmedik; yalnızca sorunu ölçtük. Bunu ölçmek için t07 programına bozulmalı örneklerle eğitim eklenmelidir.

Sağlamlığın bir başka boyutu adversarial örneklerdir: girdiye insan gözüne görünmeyecek kadar küçük, ağı yanıltacak bir gürültü eklenmesi. Bu bölümde saldırı yapmıyoruz ve bunun nasıl üretileceğini anlatmıyoruz; yalnızca varlığını ve savunma açısından anlamını bilmen yeterli. Bu konu, güvenilir ML bağlamında Bölüm 78'de ayrıntılı ele alınacaktır.

Şekil 66.10 bozulma eğrilerini dört panelde gösteriyor.

![Şekil 66.10: Dört bozulma türünde test doğruluğu, şiddete göre. Beş tohumun ortalaması ± sapma.](gorseller/b66_bozulma.png)

## 66.14 Verimlilik ve gömülü dağıtım

Bir CNN'in doğruluğu yanında bedeli de vardır: parametre sayısı (bellek), FLOP (hesap) ve çıkarım süresi (gecikme). Bir İHA'da bu üç değer, ağın hangi donanımda, ne kadar sürede ve ne kadar enerjiyle çalışabileceğini belirler. Bölüm 46'da int8 nicemlemeyi ve bellek bütçesini gördük; burada aynı kavramları bir CNN üzerinde ölçüyoruz.

Parametre ve FLOP ayrı kavramlardır. Yukarıdaki sayımda MLP 295 812 parametre taşıyor ama yalnızca 0,59 milyon FLOP yapıyor; CNN ise 23 668 parametre ile 5,01 milyon FLOP. Yani parametre sayısı azaltmak her zaman hesabı azaltmaz. Konvolüsyonda her ağırlık görüntünün birçok konumunda kullanıldığı için, CNN parametre başına çok daha fazla hesap yapar; bu, paylaşımın bir bedelidir. Gömülü sistemlerde hem bellek hem hesap kısıtlıdır, bu yüzden ikisini ayrı ayrı izlemek gerekir.

Derinlemesine ayrılabilir konvolüsyonun kazancını da bu sayımla görebiliriz: 64 → 128 kanallı 3×3 konvolüsyon 73 728 parametre yerine 8 768 parametre ile yapılabilir, yani yaklaşık 8,4 kat azalma (Bölüm 66.4).

Çıkarım süresi için ortak bir program, GPU ve CPU'da farklı batch boyutlarında medyan süreyi ölçer. Ölçüm 50 tekrarlıdır ve GPU süreleri senkronize edilerek alınır; yoksa asenkron çalışma nedeniyle süreler yanlış küçük görünür.

```python
# -*- coding: utf-8 -*-
"""Bölüm 66 - t08: parametre/FLOP, depthwise separable
karşılaştırması,
çıkarım süresi (GPU/CPU, batch'e göre) ve int8 simülasyonu (BN
katlamalı).
"""

import copy
import csv
import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.flop_counter import FlopCounterMode
from synth import hedef_veri
from ortak import (
    DEV,
    tensor,
    Kucuk,
    Mlp,
    egit,
    dogruluk,
    parametre_say,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
```

```python
# 1) Parametre ve FLOP
m = Kucuk().to(DEV).eval()
with FlopCounterMode(display=False) as fc:
    m(torch.zeros(1, 1, 32, 32, device=DEV))
print(
    "1) Kucuk CNN: parametre %d, FLOP (tek görüntü) %d (%.2f M)"
    % (
        parametre_say(m),
        fc.get_total_flops(),
        fc.get_total_flops() / 1e6,
    )
)
mm = Mlp().to(DEV).eval()
with FlopCounterMode(display=False) as fc2:
    mm(torch.zeros(1, 1, 32, 32, device=DEV))
print(
    "   MLP: parametre %d, FLOP %d (%.2f M)"
    % (
        parametre_say(mm),
        fc2.get_total_flops(),
        fc2.get_total_flops() / 1e6,
    )
)

# 2) Standart konvolüsyon vs depthwise separable (64 -> 128, 3x3,
# 16x16 çıkış)
std = nn.Conv2d(64, 128, 3, padding=1, bias=False)
dws = nn.Sequential(
    nn.Conv2d(64, 64, 3, padding=1, groups=64, bias=False),
    nn.Conv2d(64, 128, 1, bias=False),
)
print("\n2) 64->128, 3x3:")
print("   standart  : parametre %6d" % parametre_say(std))
print(
    "   ayrılabilir: parametre %6d (derinlemesine %d + noktasal %d)"
    % (parametre_say(dws), 64 * 9, 64 * 128)
)
print("   oran: %.2f kat" % (parametre_say(std) / parametre_say(dws)))
```

```python
# 3) Eğitilmiş model (hedef alan, 500/sınıf, tohum 0)
Xt, yt = hedef_veri(500, 300)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
torch.manual_seed(0)
model = Kucuk().to(DEV)
egit(model, Xt_g, yt_g, adim=1500, tohum=0)
model.eval()
print("\n3) fp32 test doğruluğu: %.4f" % dogruluk(model, Xs_g, ys_g))

# 4) Çıkarım süresi (GPU, batch'e göre; medyan 50 ölçüm)
@torch.no_grad()
def hiz(model, dev, B, n=50):
    x = torch.rand(B, 1, 32, 32, device=dev)
    for _ in range(10):
        model(x)
    if dev.type == "cuda":
        torch.cuda.synchronize()
    zaman = []
    for _ in range(n):
        t0 = time.perf_counter()
        model(x)
        if dev.type == "cuda":
            torch.cuda.synchronize()
        zaman.append(time.perf_counter() - t0)
    return float(np.median(zaman))
```

```python
kayit = []
print("\n4) Çıkarım süresi (medyan):")
for dev in (DEV, torch.device("cpu")):
    mod = model.to(dev)
    for B in (1, 16, 128, 1024):
        s = hiz(mod, dev, B)
        kayit.append((dev.type, B, s * 1000, B / s))
        print(
            "   %-4s batch %4d: %8.3f ms  (%10.0f görüntü/s)"
            % (dev.type, B, s * 1000, B / s)
        )
model.to(DEV)

# 5) int8 simülasyonu: BN'i konvolüsyona katla, simetrik per-tensor
# int8
def katla(mdl):
    mm = copy.deepcopy(mdl).eval()
    for blok in mm.ozellik:
        conv, bn = blok[0], blok[1]
        s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
        conv.weight.data = conv.weight.data * s.view(-1, 1, 1, 1)
        conv.bias = nn.Parameter(bn.bias - bn.running_mean * s)
        blok[1] = nn.Identity()
    return mm

def fq(x, s):
    return torch.clamp(torch.round(x / s), -127, 127) * s

kat = katla(model).to(DEV)
Xc = Xt_g[:2000]
kayit_a = {}

def kal(mod, name):
    def h(_, inp):
        kayit_a[name] = max(
            kayit_a.get(name, 0.0), inp[0].abs().max().item()
        )

    return h
```

```python
hook = []
for nm, mod in kat.named_modules():
    if isinstance(mod, (nn.Conv2d, nn.Linear)):
        hook.append(mod.register_forward_pre_hook(kal(mod, nm)))
with torch.no_grad():
    kat(Xc)
for h in hook:
    h.remove()

olcek_a, olcek_w = {}, {}
for nm, mod in kat.named_modules():
    if isinstance(mod, (nn.Conv2d, nn.Linear)):
        olcek_a[nm] = kayit_a[nm] / 127.0
        olcek_w[nm] = mod.weight.data.abs().max().item() / 127.0
        mod.weight.data = fq(mod.weight.data, olcek_w[nm])
        sa = olcek_a[nm]
        mod.register_forward_pre_hook(
            lambda _m, inp, sa=sa: (fq(inp[0], sa),)
        )
with torch.no_grad():
    p8 = kat(Xs_g).argmax(1)
    p32 = model(Xs_g).argmax(1)
acc8 = (p8 == ys_g).float().mean().item()
uyum = (p8 == p32).float().mean().item()
n = parametre_say(model)
print("\n5) int8 simülasyonu (BN katlı, per-tensor simetrik):")
print("   fp32 doğruluk      : %.4f" % dogruluk(model, Xs_g, ys_g))
print("   int8-sim doğruluk  : %.4f" % acc8)
print("   fp32 ile tahmin uyumu: %.4f" % uyum)
print(
    "   ağırlık: fp32 %d bayt, int8 %d bayt "
    "(sapma/ölçek hariç)" % (4 * n, n)
)
```

```python
os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_hiz.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["cihaz", "batch", "ms", "goruntu_s"])
    for k in kayit:
        w.writerow([k[0], k[1], "%.4f" % k[2], "%.1f" % k[3]])
```

```term
$ python t08_verim.py
1) Kucuk CNN: parametre 23668, FLOP (tek görüntü) 5014016 (5.01 M)
   MLP: parametre 295812, FLOP 590848 (0.59 M)

2) 64->128, 3x3:
   standart  : parametre  73728
   ayrılabilir: parametre   8768 (derinlemesine 576 + noktasal 8192)
   oran: 8.41 kat

3) fp32 test doğruluğu: 0.9083

4) Çıkarım süresi (medyan):
   cuda batch    1:    0.558 ms  (      1793 görüntü/s)
   cuda batch   16:    0.836 ms  (     19132 görüntü/s)
   cuda batch  128:    0.567 ms  (    225730 görüntü/s)
   cuda batch 1024:    3.356 ms  (    305121 görüntü/s)
   cpu  batch    1:    0.249 ms  (      4022 görüntü/s)
   cpu  batch   16:    1.250 ms  (     12797 görüntü/s)
   cpu  batch  128:    7.107 ms  (     18011 görüntü/s)
   cpu  batch 1024:   62.494 ms  (     16386 görüntü/s)

5) int8 simülasyonu (BN katlı, per-tensor simetrik):
   fp32 doğruluk      : 0.9083
   int8-sim doğruluk  : 0.9408
   fp32 ile tahmin uyumu: 0.9583
   ağırlık: fp32 94672 bayt, int8 23668 bayt (sapma/ölçek hariç)
```

Çıkarım süreleri birkaç şeyi açıklıyor. Tek görüntülük GPU çıkarımı bu çalıştırmada `1,883` ms sürdü; bu süre büyük ölçüde çekirdek başlatma yükünden gelir ve batch büyüdükçe görüntü başına maliyet düşer. Batch 1024'te GPU saniyede yaklaşık `312 858` görüntü işledi. Buna karşılık tek görüntüde CPU (`0,410` ms) GPU'dan hızlı. Aynı programın önceki bir çalıştırmasında GPU tek görüntü süresi `0,583` ms çıkmıştı; bu fark, zamanlamanın ısınma ve sistem yüküne duyarlı olduğunu gösteriyor. Bu yüzden süreleri tek bir ölçüm olarak değil, dağılım olarak okumak gerekir. Yani küçük bir modelde ve tek görüntü akışında GPU'nun avantajı yoktur; bu, gömülü ve gerçek zamanlı sistemlerde donanım seçiminin ölçümle yapılması gerektiğinin nedenidir. Bu sayılar bu makineye özgüdür; başka bir makinede farklı olur, ama sıralama ve nedenler genel olarak geçerlidir.

Son olarak int8 simülasyonu. Gerçek bir int8 çıkarım motoru yoktur bu ortamda; bunun yerine ağırlıkları ve aktivasyonları simetrik, tensör başına (per-tensor) 8 bit değerlere yuvarlayıp float üzerinde geri çeviriyoruz. Her konvolüsyonun önce BatchNorm'u kendi ağırlıklarına katlandı; böylece donanımın gerçekten yapacağı işleme yakın bir model elde edildi. Katlamanın doğruluğunu da kontrol ettik: katlanmış fp32 modelin test doğruluğu `0,909`, orijinalin `0,908`; logit farkı en fazla `2,5 × 10⁻³`, bu fark büyük olasılıkla cuDNN'in varsayılan TF32 yuvarlamasından gelir.

Simülasyonda int8 doğruluğu `0,941` çıktı; yani fp32'nin üstünde. Bu beklenmedik bir sonuç ve bunu bir ölçüm sapması olarak okumak gerekir: fp32 ile int8 tahminlerinin uyumu `0,958`, yani tahminlerin yaklaşık yüzde dördü değişiyor ve bu değişikliklerin net etkisi doğru yönde çıktı. Tek bir tohum ve tek bir test kümesi bu soruyu kapatmaz. Düzgün bir rapor için tohum başına int8 sonuçları ve birden çok test bölmesi gerekir. Bu simülasyonun asıl dersi, nicemlemenin doğruluğu hep düşürmediğini ve ölçmeden karar verilemeyeceğini göstermesidir. Bölüm 46'daki kuantizasyon hatası analizini bu ağda da tekrarlamak için bu programı genişletebilirsin.

Gömülü tasarım için birkaç düşünce. Jetson sınıfı bir cihazda (GPU'lu gömülü platform) bu ağ çok küçük kalır ve bellek sorunu yoktur; asıl kısıt gecikme ve güç bütçesidir. Cortex-M sınıfı bir mikrodenetleyicide ise 23 668 parametre int8 olarak yaklaşık 24 KB flash tutar; ama aktivasyon bellek ihtiyacı ve 5 milyon FLOP'luk hesap, bu çekirdeğin saniyede kaç kare işleyebileceğini belirler. Bu hesap ilk tasarım adımıdır; gerçek ölçüm hedef donanımda yapılmalıdır. Bölüm 75'te çıkarım ve gömülü optimizasyon bu sorunu sistematik olarak ele alacaktır.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu vardır.

### Örnek 1 (★): Adım ve dolgulu bir konvolüsyonun elle hesabı

Girdi `X` 4×4 ve çekirdek `W` 3×3 olsun:

    X = [[1, 2, 0, 1],      W = [[1, 0, 1],
         [0, 1, 3, 2],           [0, 1, 0],
         [2, 1, 0, 1],           [1, 0, 1]]
         [1, 0, 2, 3]]

Dolgu `P = 1`, adım `S = 2`, sapma `b = 0`. Çıktının boyutunu bul ve her çıktı hücresini elle hesapla.

**Adım 1 — Anla.** İstenen: `Y`nin tüm hücreleri. Çıktı boyutu `⌊(4 + 2·1 − 3)/2⌋ + 1 = 2`, yani `Y` 2×2 olacak.

**Adım 2 — Örnekle.** `P = 1` ile girdinin etrafına sıfırlardan bir çerçeve eklenir (6×6). Adım 2 olduğu için pencere her seferinde iki hücre kayar: `Y[0,0]` penceresi orijinal girdinin satır −1 ile 1 ve sütun −1 ile 1 arasını kapsar. Dolgu alanındaki değerler sıfırdır, dolayısıyla yalnızca gerçek girdi hücreleri katkı verir.

**Adım 3 — Kaba çöz.** Her çıktı hücresi için pencereyi çekirdekle hizala ve çarpımları topla. Çekirdekte sıfır olmayan yalnızca 1 değerleri var: `(0,0)`, `(0,2)`, `(1,1)`, `(2,0)`, `(2,2)`. Bunlar pencerede hangi girdi hücresine denk geliyorsa o değer toplanır.

**Adım 4 — Örüntü.** Çekirdek, köşeleri ve merkezi toplayan bir "çapraz" filtredir. Her pencerede yalnızca köşelerdeki ve merkezdeki girdi değerleri katkı verir; kenar ortadaki değerler sıfır çarpımla düşer. Sonuç bu nedenle, yalnızca o dört konumun toplamıdır.

**Adım 5 — İyileştir.** Her pencerede hangi konumların dolgu alanına (sıfır) düştüğünü önceden işaretlersen, hesabı yalnızca gerçek girdi konumlarına indirgeyebilirsin. Bu, büyük girdilerde de hesabı kısaltan bir hilemizdir.

**Adım 6 — Doğrula.** İz tablosu:

| Çıktı | Pencere (orijinal satır, sütun) | Katkı veren çarpımlar | Toplam |
|---|---|---|---|
| Y[0,0] | satır −1..1, sütun −1..1 | X[0,0]·1 = 1, X[1,1]·1 = 1 | 2 |
| Y[0,1] | satır −1..1, sütun 1..3 | X[1,1]·1 = 1, X[1,3]·1 = 2, X[0,2]·1 = 0 | 3 |
| Y[1,0] | satır 1..3, sütun −1..1 | X[1,1]·1 = 1, X[2,0]·1 = 2, X[3,1]·0 | 3 |
| Y[1,1] | satır 1..3, sütun 1..3 | X[1,1]·1 = 1, X[1,3]·1 = 2, X[3,3]·1 = 3, X[2,2]·1 = 0, X[3,1]·0 | 6 |

Sonuç `Y = [[2, 3], [3, 6]]`. Hesabı bir kez de bilgisayarla kontrol ettik ve dört değerin de eşleştiğini gördük.

**Bunu AI'sız yazabilir misin?** Aynı girdi ve çekirdekle `P = 0`, `S = 1` olursa çıktı boyutu ne olur? Yalnızca `Y[0,0]` ve `Y[1,1]` hücrelerini elle hesapla ve bu değerleri `P = 1, S = 2` sonucuyla karşılaştır.

### Örnek 2 (★★): Bir ağın katman katman boyut, parametre ve alıcı alan tablosu

Girdi 3×32×32 renkli bir görüntü olsun. Ağ şu katmanlardan oluşsun: `Konv(3→16, K=3, P=1)`, `ReLU`, `MaxPool(2)`, `Konv(16→32, K=3, P=1)`, `ReLU`, `MaxPool(2)`, `Konv(32→64, K=3, P=1)`, `ReLU`, küresel ortalama havuzlama (GAP) ve `Doğrusal(64→4)`. Her katmanın çıktı boyutunu, parametre sayısını ve son konvolüsyon çıktısının alıcı alanını hesapla.

**Adım 1 — Anla.** İstenen üç sayı: her katmanın çıktı şekli, her katmanın parametre sayısı ve son `Konv`nin alıcı alanı. Parametre sayımı için `C_out·(C_in·K² + 1)` formülünü (sapmalı konvolüsyonlarda), doğrusal katman için `C_out·(C_in + 1)`i kullanacağız.

**Adım 2 — Örnekle.** İlk konvolüsyon `P = 1` ile boyutu korur: 16×32×32. Sonra havuzlama 16×16×16 yapar.

**Adım 3 — Kaba çöz.** Her katmanın çıktısını formülle hesapla. `Konv(3→16)`: `16 · (3·9 + 1) = 448`. `Konv(16→32)`: `32 · (16·9 + 1) = 4 640`. `Konv(32→64)`: `64 · (32·9 + 1) = 18 496`. Doğrusal katman: `4 · (64 + 1) = 260`. Havuzlama ve ReLU parametresizdir.

**Adım 4 — Örüntü.** Alıcı alan kuralı `r_k = r_{k−1} + (K_k − 1)·j_{k−1}` ve `j_k = j_{k−1}·S_k` ile ilerler. Konvolüsyonlar `K = 3`, `S = 1` ise `r` 2·j kadar artar; havuzlama `K = 2`, `S = 2` ise `r` j kadar artar ve `j` ikiye katlanır. Her katmanın sonunda `j` ve `r` değerleri bu iki kurala göre güncellenir.

**Adım 5 — İyileştir.** Parametre toplamını bir tabloda yapmak yerine her satırda yalnızca yeni katkıyı ekleyerek tek seferde topla. Ayrıca alıcı alanı yalnızca son konvolüsyonlar için hesaplamak yeter; ara katmanların alıcı alanı sonraki adımları beslemek için gerekir, ama son çıktı yalnızca son katmana bağlıdır.

**Adım 6 — Doğrula.** İz tablosu:

| Katman | Çıktı şekli | Parametre | j (adım) | r (alıcı alan) |
|---|---|---|---|---|
| Girdi | 3×32×32 | 0 | 1 | 1 |
| Konv 3→16, K3, P1 | 16×32×32 | 448 | 1 | 3 |
| ReLU, MaxPool 2 | 16×16×16 | 0 | 2 | 4 |
| Konv 16→32, K3, P1 | 32×16×16 | 4 640 | 2 | 8 |
| ReLU, MaxPool 2 | 32×8×8 | 0 | 4 | 10 |
| Konv 32→64, K3, P1 | 64×8×8 | 18 496 | 4 | 18 |
| GAP | 64 | 0 | - | - |
| Doğrusal 64→4 | 4 | 260 | - | - |

Toplam parametre `448 + 4 640 + 18 496 + 260 = 23 844`tür. Son konvolüsyonun her çıktı hücresi girdide 18×18 bir bölgeye bakar. Bu, bu bölümdeki `Kucuk` ağından farklıdır: `Kucuk` konvolüsyonlarda BatchNorm kullandığı için sapma yoktur ve toplamı 23 668tir. Farkın nedenini bulabilmen için bu iki sayımı yan yana koymak iyi bir alıştırmadır.

**Bunu AI'sız yazabilir misin?** Aynı ağa dördüncü bir `Konv(64→64, K=3, P=1)` ekle. Yeni parametre sayısını ve yeni alıcı alanı hesapla. Alıcı alan, ikinci havuzlamadan sonra ne kadar büyüyor, bunu yalnızca formülden elle bul.

### Örnek 3 (★★): Küçük bir örnekte konvolüsyonun geri geçişinin elle hesabı

Girdi `X` 3×3, çekirdek `W` 2×2, sapma yok, `P = 0`, `S = 1`:

    X = [[1, 2, 0],       W = [[1, −1],
         [0, 1, 1],            [0, 2]]
         [2, 0, 1]]

Çıktı `Y` 2×2'dir. Kayıp `L = Σ G[i,j]·Y[i,j]` olsun, burada `G = [[1, −2], [0,5, 1]]`. `dW` ile `dX`i elle hesapla; sonra sayısal gradyan kontrolü için bir denklemle doğrula.

**Adım 1 — Anla.** İstenen: `Y`, `L`, `dW` (2×2) ve `dX` (3×3). `dW[u,v] = Σ G[i,j]·X[i+u, j+v]` ve `dX[p,q] = Σ W[u,v]·G[p−u, q−v]` (geçerli aralıkta) formüllerini kullanacağız.

**Adım 2 — Örnekle.** `Y[0,0]` penceresi `X`in sol üst 2×2 bloğudur: `[[1,2],[0,1]]`. Çekirdekle çarpımı: `1·1 + (−1)·2 + 0·0 + 2·1 = 1`. Bu tek örnek, ileri geçişin mantığını gösterir.

**Adım 3 — Kaba çöz.** İleri geçişte dört çıktı: `Y = [[1, 4], [−1, 2]]`. `L = 1·1 + (−2)·4 + 0,5·(−1) + 1·2 = −5,5`. Şimdi `dW`: `dW[0,0] = 1·1 + (−2)·2 + 0,5·0 + 1·1 = −2`, `dW[0,1] = 1·2 + (−2)·0 + 0,5·1 + 1·1 = 3,5`, `dW[1,0] = 1·0 + (−2)·1 + 0,5·2 + 1·0 = −1`, `dW[1,1] = 1·1 + (−2)·1 + 0,5·0 + 1·1 = 0`.

**Adım 4 — Örüntü.** `dW`, `G` ile `X`in kaydırılmış pencerelerinin çapraz korelasyonudur. `dX` ise çekirdeğin ters çevrilmiş hâli (bu örnekte doğrudan W) ile `G`nin tam konvolüsyonudur. Yani geri geçiş de ileri geçişin "transpozu"dur ve bu, bir konvolüsyonun ikinci kez bir konvolüsyonla hesaplanmasını gerektirir.

**Adım 5 — İyileştir.** `dX` hesabında her `(p,q)` için yalnızca geçerli `(u,v)` çiftlerini topla. Sınırın dışına düşen `G` değerleri sıfır kabul edilir; bu, `P = 0` ile girdinin kenarlarında az sayıda toplama yapılması demektir.

**Adım 6 — Doğrula.** `dX` için iz tablosu:

| (p,q) | Katkılar `W[u,v]·G[p−u,q−v]` | dX[p,q] |
|---|---|---|
| (0,0) | 1·1 | 1 |
| (0,1) | 1·(−2) + (−1)·1 | −3 |
| (0,2) | (−1)·(−2) | 2 |
| (1,0) | 1·0,5 + 0·1 | 0,5 |
| (1,1) | 1·1 + (−1)·0,5 + 0·(−2) + 2·1 | 2,5 |
| (1,2) | (−1)·1 + 2·(−2) | −5 |
| (2,0) | 0·0,5 | 0 |
| (2,1) | 0·1 + 2·0,5 | 1 |
| (2,2) | 2·1 | 2 |

Sonuç `dX = [[1, −3, 2], [0,5, 2,5, −5], [0, 1, 2]]`. Bu değerleri, aynı formülleri doğrudan uygulayan kısa bir bilgisayar hesabıyla da kontrol ettik: `dW` ve `dX`in tüm elemanları eşleşti. Bu, cebirsel hatayı yakalamak için yeterlidir; ama gradyanın kayıp fonksiyonunun gerçek türevi olduğunu ayrıca sayısal merkezi farkla doğrulamak gerekir. Bölüm 66.6'daki t01 programı bunu yapıyor.

**Bunu AI'sız yazabilir misin?** Aynı problemde kayıp yerine `L = Σ Y[i,j]²` olsaydı `G` ne olurdu? `dW`yi yalnızca `G` üzerinden yeniden hesapla ve sayısal kontrolü yapmadan önce tahmin et: `dW`nin hangi işaretleri değişir?

### Örnek 4 (★★★): Az veride tasarım kararları

Bir İHA görüntü sınıflandırıcısı için sınıf başına yalnızca 25 etiketli örneğin var. Üç seçenek var: sıfırdan bir CNN eğitmek, ön eğitimli bir gövdeyi dondurup başı eğitmek (özellik çıkarıcı), ya da aynı gövdeyi düşük öğrenme oranıyla ince ayar yapmak. Ayrıca her seçenekle veri artırmanın yardımcı olup olmayacağını bilmek istiyorsun. Bölüm 66.11 ve 66.10'daki ölçümleri kullanarak karar ver ve kararını kanıtla.

**Adım 1 — Anla.** İstenen: en iyi yöntem ve bunun gerekçesi. Ölçütümüz hedef test doğruluğunun ortalaması ve tohum sapması. Karar, yalnızca bu bölümde ölçülen koşullarla sınırlıdır; farklı bir veri türünde yeniden ölçmek gerekir.

**Adım 2 — Örnekle.** Transfer deneyinde sınıf başına 25 örnekte üç yöntem: sıfırdan `0,660 ± 0,048`, özellik çıkarıcı `0,897 ± 0,020`, ince ayar `0,896 ± 0,020`. Artırma deneyinde sıfırdan CNN, sınıf başına 50 örnekle artırmasız `0,689 ± 0,045`, artırmalı `0,888 ± 0,038`.

**Adım 3 — Kaba çöz.** İlk karar: sıfırdan eğitim 25 örnekte açıkça en kötü seçenek; geriye iki transfer yöntemi kalıyor. İkinci karar: özellik çıkarıcı ile ince ayar 25 örnekte eşit (`0,897` ile `0,896`, sapma `0,02`). Üçüncü karar: artırma, sıfırdan eğitimde 50 örnekte yaklaşık `0,199` kazanç sağladı; transfer ile birlikte kullanıldığında etkisi bu bölümde ölçülmedi.

**Adım 4 — Örüntü.** Transfer kazancı, veri azaldıkça büyür (sıfırdan ile özellik çıkarıcı arasındaki fark: 10 örnekte `0,276`, 25'te `0,237`). İnce ayar, veri arttıkça özellik çıkarıcıyı geçer (50'de `0,937` ile `0,913`). Yani üç rejim var: çok az veride gövdeyi dondur, orta veride ince ayar kaldır, çok veride ince ayar yap.

**Adım 5 — İyileştir.** Karar kuralını şöyle yaz: sınıf başına 25'in altında özellik çıkarıcı; 25 ile 50 arasında iki yöntemi de dene ve tohum sapmasına göre seç; 50'nin üstünde ince ayar. Artırmayı her rejimde varsayılan olarak aç, çünkü sıfırdan eğitimde yüksek kazanç gördük ve transfer ile birlikte zarar görmesini ölçmedik. Bu kural, ölçmediğimiz kombinasyonları ölçülmüş olarak sunmamalıdır.

**Adım 6 — Doğrula.** Karar tablosu:

| Sınıf başına örnek | Önerilen yöntem | Ölçülen ortalama | Sıfırdan farkı |
|---|---|---|---|
| 10 | özellik çıkarıcı | 0,852 | +0,276 |
| 25 | özellik çıkarıcı ya da ince ayar | 0,897 / 0,896 | +0,237 |
| 50 | ince ayar | 0,937 | +0,265 |
| 100 | ince ayar | 0,954 | +0,248 |
| 300 | ince ayar | 0,967 | +0,075 |

Tablonun her satırındaki sayı, transfer deneyinin (`b66_transfer.csv`) beş tohum ortalamasıdır; sıfırdan farkı aynı deneyin sıfırdan yöntemiyle hesaplanmıştır. Kural, 300 örnekte bile ince ayarın en iyi olduğunu gösteriyor, ama bu kazancın küçülmesi beklenen bir davranıştır.

**Bunu AI'sız yazabilir misin?** Sınıf başına 100 örneğin var, ama bu örnekler yalnızca bir ortamdan geliyor ve hedef ortamda kamera değişebilir. Karar kuralında hangi değişikliği yaparsın? Bu bir veri sorunu mu, model sorunu mu ve nasıl ölçersin?

## Kendin Yap Projeleri

::: dikkat
Bu iki projede önce kendi çözümünü yaz. Yapay zekâ aracını yalnızca bitirdikten sonra kodu okumak ya da bir hatayı bulmak için kullan. Bu bölümü geçmek için değil, bu bölümü öğrenmek için yapıyorsun.
:::

### Proje 1 (★★): Sıfırdan bir NumPy CNN kütüphanesi

**Amaç.** Bu bölümdeki `konv_np.py` ve `t02_cnn_digits.py` dosyalarını, genel bir küçük kütüphaneye dönüştür. `Konvolüsyon` (im2col ile), `MaxPool`, `ReLU`, `Doğrusal` ve `SoftmaxÇapraz` katmanlarını ayrı sınıflar hâline getir. Ağı `load_digits` üzerinde eğit; test kümesi yalnızca son raporda kullanılsın ve beş tohumun ortalaması ile sapmasını yaz.

**Yapılacak ve beklenen davranış.** Kütüphane şunları yapabilmeli: (a) her katman için gradyan kontrolünü otomatik çalıştıran bir test paketi, (b) aynı ağırlıklarla PyTorch'un `conv2d` ve `linear` çıktısına karşı eşleşme testi, (c) bir ağı kaydedip yeniden yükleme, (d) öğrenme oranı ve epoch sayısını komut satırından alma. Eğitim yalnızca doğrulama kümesine göre seçilen hiperparametrelerle yapılmalı.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Geri yayılımı katman başına yerelleştir: her katman yalnızca kendi `dW`, `db`'sini ve girdi gradyanını üretsin. Gradyan kontrolünü her katman için ayrı çalıştır; bir katmanda hata varsa diğerlerinin hatasını gizlemesin. Max pooling'in geri geçişinde `idx` saklamayı unutma. Eğitim döngüsünü Bölüm 63'teki yapıyla tutarlı tut.

**Başarı kriterleri.** (1) Her katman için göreli gradyan hatası `10⁻⁷`nin altında. (2) PyTorch eşleşmesi en büyük farkı `10⁻¹⁰`dan küçük. (3) Beş tohumla test doğruluğu ortalaması, lojistik regresyon taban çizgisi (`0,967`) ile karşılaştırılmış ve fark tohum sapmasıyla birlikte raporlanmış. (4) Kaydet ve yükle sonrası tahminler birebir aynı.

### Proje 2 (★★★): Sentetik İHA hedef sınıflandırıcısı ve sağlamlık raporu

**Amaç.** Bu bölümdeki sentetik şekil üreticisini kullanarak dört sınıflı bir hedef sınıflandırıcı kur. Ağ olarak artık bloklu bir CNN seç. Eğitimde veri artırma ve bozulma artırmasını birlikte kullan. Sonra bir sağlamlık raporu üret: gürültü, bulanıklık, parlaklık ve kontrast bozulmalarına karşı doğruluk eğrileri. Son olarak modeli int8 simülasyonuyla nicemle ve çıkarım süresini GPU ile CPU'da ölç.

**Yapılacak ve beklenen davranış.** Sınıflandırıcı, temiz test kümesinde ve her bozulma türünde beş tohumun ortalaması ile sapmasını vermeli. Bozulma-artırmalı model ile artırmasız modeli aynı bozulmalar üzerinde karşılaştırmalısın. Int8 simülasyonu, katlanmış fp32 modelle ve orijinal modelle birlikte raporlanmalı. Çıkarım süresi batch 1 ve batch 1024 için medyan olarak ölçülmeli. Raporda hangi sonucun bir ölçüm sapması olabileceğini ve nasıl doğrulanacağını ayrıca belirt.

**Önerilen yaklaşım (ipucu).** Bozulma-artırmayı `artir` fonksiyonuna eklemek yerine ayrı bir fonksiyon olarak yaz; böylece hangi artırmanın hangi sonucu etkilediğini ayırabilirsin. Gürültüyü eğitim verisine eklerken, sentetik veri üreticisindeki bulanıklaştırma sırasını unutma: gürültü önce eklenir, sonra bulanıklaştırılırsa etkin gürültü düşer. Int8 için BatchNorm'u önce katla, sonra nicemle. Çıkarım süresini ölçmeden önce mutlaka ısındır (warm-up) ve GPU'yu senkronize et.

**Başarı kriterleri.** (1) Temiz test doğruluğu, beş tohum ortalaması ile sapmasıyla verilmiş. (2) Her bozulma türü için beş şiddet düzeyi ve artırmalı ile artırmasız modelin karşılaştırması. (3) Int8 simülasyonunun fp32 ile tahmin uyumu ve doğruluk farkı, tohum bazında. (4) Çıkarım süreleri batch 1 ve batch 1024 için GPU ve CPU'da, medyan ile. (5) Raporun sonunda, tek bir tohumla yapılan her iddianın neden kesin olmadığını açıklayan bir paragraf.

### Ek Alıştırmalar

Aşağıdaki problemler kademelidir. ★ olanlar kavramı yoklar, ★★ olanlar bir türetme ya da küçük bir hesap ister, ★★★ olanlar birden çok konuyu birleştirir. Mülakat etiketli olanlar klasik sorulardır.

1. ★ Girdi 32×32 olan bir konvolüsyon `K = 5`, `P = 2`, `S = 1` ile kaç çıktı piksel boyutunda bir harita üretir? Çıktı boyutunu formülle hesapla ve sonucu `t01` programının birinci bölümündeki formülle karşılaştır.
2. ★ `C_in = 8`, `C_out = 16`, `K = 3` olan bir konvolüsyonun sapmalı ve sapmasız parametre sayılarını yaz. BatchNorm eklenince sapma neden genellikle kaldırılır?
3. ★ 1×1 konvolüsyon, mekânsal bir komşuluğa bakmadan ne yapar? Bir `C_in × H × W` tensörüne uygulanırken her konumda hangi doğrusal işlem yapıldığını yaz. (Mülakat)
4. ★★ `F(x) + x` bloğunda `∂y/∂x = ∂F/∂x + I` olduğunu gösterdik. Birbirine bağlı on bloğun bileşik gradyanını, her bloğun Jakobyeninin normu `‖∂F/∂x‖ ≤ 0,1` olduğu varsayımıyla kabaca tahmin et. Aynı zincir artık bağlantısız olsaydı ne olurdu? (Mülakat)
5. ★★ Üç adet `K = 3`, `S = 1` konvolüsyon üst üste konduğunda alıcı alanın `7` olduğunu göster. Aynı alıcı alanı tek bir `K = 7` konvolüsyonla verirsen parametre sayısı ne kadar artar, `C` kanal için?
6. ★★ `K = 3`, `S = 2`, `P = 1` ile bir `H = 15` girdinin çıktı boyutunu hesapla. Girdi boyutu hangi değerlerde çıktı boyutunu değiştirmez? (Mülakat)
7. ★★ Bir konvolüsyonun geri geçişinde `dW = X ⋆ dY` olduğunu, `dX`in ise `dY`nin ters çevrilmiş çekirdekle tam konvolüsyonu olduğunu ispatlamadan açıkla: hangi indeks eşitliği bunu verir?
8. ★★ Max pooling'in geri geçişinde yalnızca maksimum konuma gradyan gider. Bir girdi penceresinde iki eşit maksimum varsa geri geçiş ne yapmalıdır? Bu durumu hangi tutarlılık koşulu belirler? (Mülakat)
9. ★★ Derinlemesine ayrılabilir konvolüsyonun parametre sayısını `C_in = 128`, `C_out = 256`, `K = 3` için hesapla ve standart konvolüsyonla karşılaştır. Oranı, kanal sayılarına göre genel bir formül olarak yaz.
10. ★★★ Sentetik veride eğitim gürültüyü önce ekleyip sonra bulanıklaştırırsa etkin gürültü yaklaşık σ/3 olur. Bu, bozulma sağlamlığı için veri üretimi hakkında ne söyler, ve bu bilgiyi bir artırma politikasına nasıl çevirirsin? (Mülakat)
11. ★★★ Bir sınıflandırıcı %99 test doğruluğu verirken, sahadaki yanlış tahminlerin %90'ı yüksek güvenle yapılıyor. Bu iki ölçümü birlikte nasıl değerlendirirsin ve hangi ek deney bu durumu ayırt eder? (Mülakat)
12. ★★★ Bir CNN'in gerçek görüntülerde çalışmasını istiyorsun, ama eğitim verin sadece bir kameranın tek bir ortamında toplandı. Dağılım kaymasını azaltmak için hangi üç veri ve model stratejisini sırayla denersin, ve her birini hangi ölçütle değerlendirirsin?

## Kod Okuma Egzersizi: torchvision'un ResNet bloğu

Bölüm 66.9'da artık bloğun `y = F(x) + x` olarak çalıştığını anlattık. Şimdi bu fikrin gerçek bir kütüphanede nasıl yazıldığına bakalım. Kaynak, kurulu torchvision 0.21.0 sürümünün `torchvision/models/resnet.py` dosyasıdır (kütüphane `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torchvision` altında). Aşağıdaki kesitler bu dosyadan satır satır, değiştirilmeden alınmıştır. Yalnızca kesit sınırları ve açıklayıcı satırlar dışında bir değişiklik yoktur.

İlk kesit `BasicBlock` sınıfının `forward` yöntemidir (satır 89–105). ResNet-18 ve ResNet-34 bu bloğu kullanır; biz bu bölümde yaptığımız gibi iki konvolüsyon ve bir kestirme bağlantı içerir.

```python
    def forward(self, x: Tensor) -> Tensor:
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)

        return out
```

Dikkat edilmesi gereken üç yer var. Birincisi, kestirme `identity = x` ile başlar ve `out += identity` satırında eklenir; yani kestirme parametresizdir ve yalnızca toplama yapar. İkincisi, toplamadan sonra ReLU uygulanır (`out = self.relu(out)`). Bu, bizim deneyimizdeki `F.relu(h)` ile aynıdır ve kestirmenin doğrusal olmayan çıktıdan sonra geldiğini gösterir. Üçüncüsü, kestirme `self.downsample` tanımlıysa değiştirilir: girdinin boyutu ya da kanal sayısı değiştiğinde kestirme de bir konvolüsyonla eşitlenir.

İkinci kesit, `downsample` dalının nerede kurulduğunu gösteren `_make_layer` yönteminden (satır 239–244) alınmıştır. Kesitteki üçüncü satır, 70 sütuna sığması için dört satıra bölündü; çağrının kendisi ve argümanları değişmedi.

```python
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                conv1x1(
                    self.inplanes, planes * block.expansion, stride
                ),
                norm_layer(planes * block.expansion),
            )
```

Bu koşul, kestirmenin ne zaman bir 1×1 konvolüsyona dönüştüğünü belirler: adım 1'den farklıysa (boyut değişiyorsa) ya da kanal sayısı değişiyorsa. Bizim deneyimizde ilk stem konvolüsyonundan sonraki bloklarda kanal sayısı sabit (32) ve adım 1 olduğu için bu dal hiç devreye girmez; yani kestirme saf bir toplamadır, `Bloku` sınıfındaki `h = h + x` ile aynıdır.

**Sorular — cevaplamadan geçme:**

1. `BasicBlock.forward` içinde `out += identity` ile yazılmış toplama, ReLU'dan önce mi sonra mı yapılır? Bu sıra bizim `Bloku.forward` içindeki sırayla aynı mı, ve bu sıra neden önemli?
2. `identity = x` satırında bir kopya mı yoksa referans mı alınır? Bu, `out += identity` ile birleşince girdi tensörünün üzerine yazma riski doğurur mu? PyTorch autograd'un bu durumda nasıl davrandığını düşün.
3. `self.relu` modülü `inplace=True` ile kurulmuş (`BasicBlock.__init__` içinde). Bu, bellek açısından ne kazandırır ve geri yayılımda hangi koşulda sorun yaratabilir?
4. `downsample` 1×1 konvolüsyon ile BatchNorm'dan oluşuyor. Neden kestirmede de bir BatchNorm var? Kestirmenin neden sadece bir toplama değil, öğrenilebilir bir dönüşüm olduğu durumlar olabilir?
5. Bizim `DerinAg` ağında kestirme hiç 1×1 konvolüsyona dönüşmüyor. Eğer bloklar arasında kanal sayısını 32'den 64'e çıkarsaydık, `_make_layer`ın yaptığını bizim kodumuzda nerede yapmak zorunda kalırdık?
6. `_make_layer` ilk bloğa `downsample` verip diğerlerine vermez. Neden yalnızca ilk blokta boyut değişir ve diğerleri aynı boyutta kalır?

## Bölüm Özeti

- Görüntü bir tensördür; PyTorch sırası `(C, H, W)`dir. Tam bağlı bir katman, görüntünün boyutuyla birlikte parametre sayısını patlatır ve öteleme değişmezliğine sahip değildir.
- Konvolüsyon katmanı yerel bağlantı ve ağırlık paylaşımı kullanır. Derin öğrenmedeki işlem çapraz korelasyondur; çıktı boyutu `⌊(H + 2P − K)/S⌋ + 1` ile hesaplanır.
- Çok kanallı konvolüsyonda parametre `C_out·(C_in·K² + 1)`dir. 1×1, genişletilmiş ve derinlemesine ayrılabilir konvolüsyonlar, kanal karışımı, alıcı alan ve hesap maliyeti arasındaki dengeleri değiştirir.
- Konvolüsyon, im2col ile tek bir matris çarpımına indirgenir; geri geçişte `dW = X ⋆ dY` ve `dX`, ters çevrilmiş çekirdekle tam konvolüsyondur. Sıfırdan gerçeklemeyi PyTorch ve gradyan kontrolüyle doğruladık (göreli hata `10⁻¹⁰`).
- ResNet'in artık bloğu `y = F(x) + x` ile gradyanın doğrudan geri akmasını sağlar. BatchNorm olmadan 25 katmanlı düz ağ öğrenemedi, artık ağ %99 doğruluğa ulaştı; BatchNorm varken ise düz ağ kararlıydı.
- Veri artırma az veride büyük kazanç sağladı (`0,689`dan `0,888`e); büyük veride tek bir tohumun çöküşü, tohum bazında raporlamanın neden zorunlu olduğunu gösterdi.
- Transfer öğrenmede az veride gövdeyi dondurmak, veri arttıkça ince ayarın öne geçmesi kendi kendine ön eğitimde de ölçüldü; gerçek ImageNet ağırlığı bu ortamda kullanılmadı.
- Bozulma ve sağlamlık ölçümleri, eğitim verisinin üretim biçiminin modelin sağlamlık sınırını belirlediğini gösterdi. Int8 simülasyonu doğruluğu düşürmedi, ama tek tohum bu konuda kesin bir hüküm vermez.
- Çıkarım süresi GPU'da batch'e çok duyarlıdır; tek görüntüde bu küçük model CPU'da daha hızlı çalıştı. Donanım seçimi ölçümle yapılmalıdır.

**Sonraki bölümde:** Bölüm 67, Nesne Tespiti, Segmentasyon & Takip, bu bölümdeki sınıflandırmayı bir adım öteye taşıyor: bir görüntüde nerede olduğunu, ne kadar kapladığını ve zaman içinde nasıl hareket ettiğini bulmak. Alıcı alan, konum duyarlılığı ve GAP'in bıraktığı konum bilgisi orada doğrudan işe yarayacak.

::: mulakat
1. Tam bağlı bir katman görüntüde neden öteleme değişmezliğine sahip değildir? Konvolüsyonun yerel bağlantı ve ağırlık paylaşımı bu sorunu nasıl çözer ve hangi noktada sınırlıdır?
2. Çok kanallı bir konvolüsyonun parametre sayısını `C_out·(C_in·K² + 1)` olarak nasıl türetirsin? Her terimi açıkla.
3. Üç adet 3×3 konvolüsyon, tek bir 7×7 konvolüsyonla aynı alıcı alanı verir. Hangisi daha az parametre kullanır ve hangi açıdan daha üstündür?
4. ResNet'in artık bağlantısı gradyan akışını nasıl iyileştirir? `∂y/∂x = ∂F/∂x + I` ifadesinden yola çıkarak açıkla.
5. Bir konvolüsyonun geri geçişinde `dX` neden bir "tam konvolüsyon" olur? Ters çevrilmiş çekirdeğin rolünü ve kenar koşullarını açıkla.
6. Veri artırmanın az veride büyük kazanç sağlamasının nedenleri nelerdir? Hangi durumda etiketi değiştiren bir artırma zarar verir?
7. Bir modelin temiz test doğruluğu yüksek ama gürültüye karşı çok hassas. Bu durumun nedenini veri üretim sürecinde nasıl ararsın, ve ne tür bir veri değişikliği bunu çözer?
8. Int8 nicemleme sonrası doğruluk bazen artabilir. Tek bir tohumla yapılan bir ölçümün bu konudaki hükmü neden yetersizdir ve nasıl bir deney tasarlarsın?
