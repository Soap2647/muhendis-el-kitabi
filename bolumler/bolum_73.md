%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 73
%% baslik: Temsil Öğrenme & Self-Supervised

## Giriş: Etiketsiz veriden gösterim öğrenmek

Bir İHA'nın kamerası her gün on binlerce kare kaydeder. Bu karelerin hangisinde bir araç, hangisinde bir ağaç gölgesi, hangisinde bir insan olduğunu bilen kimse yoktur. Bir uzman her kareye etiket yazarsa bu iş haftalar sürer ve ancak küçük bir kısmı etiketlenebilir. Sonuç bilinen bir darboğazdır: veri bol, etiket pahalı.

Bu darboğaz savunma sanayiinde özellikle serttir. Kızılötesi görüntüde bir hedefi etiketlemek uzmanlık ister; yeni bir sensör ya da yeni bir ortam geldiğinde etiketli veri neredeyse sıfırdan başlar. Bölüm 66'da transfer öğrenmeyi gördük: ImageNet'te ön eğitilmiş bir ağın özellikleri yeni göreve taşınabiliyordu. Ama ImageNet etiketleriyle eğitilmişti ve bizim sensörümüzün görüntüleri ImageNet'e benzemeyebilir. Soru şu olur: etiket olmadan, yalnızca elimizdeki bol görüntüden iyi bir gösterim öğrenebilir miyiz?

Bu soruya verilen cevap öz-denetimli öğrenmedir (self-supervised learning). Fikir, etiketi verinin kendisinden üretmektir. Bir görüntünün iki bozulmuş kopyası aynı nesneye aittir; bir cümlenin bir kelimesini gizleyip çevresinden tahmin ettirebilirsin. Bu sahte görevler gerçek bir amaç için değil, iyi bir iç gösterim öğrenmek için kurulur. Bölüm 70'te kelime gömmelerinde ve maskeli dil modellerinde bu fikrin metindeki hâlini gördük. Bu bölümde aynı fikri görüntüye, kontrastif kayıplara ve son olarak metin–görüntü çiftlerine taşıyacağız.

Mülakatta bu konu iki soruyla karşına çıkar: "Kontrastif öğrenme neden negatif örnek ister?" ve "Bir gösterim öğrenmenin iyi olduğunu nasıl bilirsin?" İkinci sorunun cevabı bu bölümün ana iskeleti olacak: temsili etiket bulmadan ölçmeyeceğiz; doğrusal yoklama, k-NN ve az etiketle ince ayar gibi ölçütlerle ölçeceğiz.

::: not
Bu bölümdeki sayılar, PyTorch 2.6.0+cu124 ile çalıştırılan programlardan gelir. Veri, 32×32 renkli sentetik şekillerden oluşur; indirilmiş hiçbir veri ya da ağırlık kullanılmadı. Etiket eğrisi (73.2) üç tohumla ve ortalama ± sapma olarak verildi. Artırma ablasyonu, sıcaklık ve batch taraması, sağlamlık ve CLIP deneyleri tek tohumla yapıldı; metinde ayrıca işaretlendi. Ön eğitimin bir kısmı önceki oturumda GPU'da, geri kalan deneyler dört iş parçacıklı CPU'da çalıştırıldı.
:::

## 73.1 İyi bir temsil nedir?

Temsil (representation), bir girdiyi sonraki görevin işini kolaylaştıran bir sayı vektörüne çeviren fonksiyondur: `h = f(x)`, `h ∈ ℝ^d`. Bölüm 63'te bir MLP'nin gizli katmanlarının bu işi yaptığını gördük; Bölüm 66'da konvolüsyon katmanlarının kenarlardan dokuya, oradan nesne parçalarına doğru daha soyut özellikler ürettiğini izledik. Temsil öğrenme, bu fonksiyonu bir sınıflandırma kaybına bağlı kalmadan öğrenme sorunudur.

İyi bir temsili üç özellikle tarif edebiliriz.

**Değişmezlik ve eşdeğişkenlik.** Bir uçağın görüntüsü hafifçe kaydırılmış, parlaklığı değişmiş ya da biraz döndürülmüşse, nesnenin kimliği değişmez. Temsilin bu değişimlere karşı kararlı olması beklenir: `f(T(x)) ≈ f(x)`. Bazı bilgiler ise değişime eşlik etmelidir: görüntü döndüğünde yönelim bilgisi de dönmelidir. Buna eşdeğişkenlik denir: `f(T(x)) ≈ T′(f(x))`. Hangi değişimlere değişmez, hangilerine eşdeğişken olması gerektiği göreve bağlıdır.

**Ayrıştırılabilirlik.** Bir sahnede renk, şekil, konum ve boyut gibi bağımsız faktörler vardır. İyi bir temsilde her faktör ayrı bir yöne ya da boyut grubuna düşer; kötü bir temsilde hepsi birbirine karışır ve küçük bir değişiklik her boyutu birden etkiler. Ayrıştırılabilirlik, doğrusal yoklamanın neden işe yaradığını da açıklar: faktörler doğrusal olarak ayrılabilirse basit bir sınıflandırıcı yeter.

**Aktarılabilirlik.** Asıl ölçüt, temsilin görev değiştiğinde de işe yarayıp yaramadığıdır. Elimizde yalnızca etiketsiz bir kayıt olsa bile, ön eğitilmiş bir gösterimin az sayıda etiketle yeni bir görevi öğrenebilmesi gerekir.

### Etiket darboğazı

Denetimli öğrenmede her örnek için bir etiket alırsın. Bir örnek `C` sınıftan birine ait olduğunda, etiket en fazla `log₂ C` bit bilgi taşır. Dört sınıflı bu bölümün problemi için bu 2 bittir. Oysa aynı örnek ham hâlde `32 × 32 × 3 = 3072` pikselden oluşur ve her piksel 8 bitle kodlanırsa `3072 × 8 = 24 576` bit eder. Bu iki rakam bilgi kuramsal bir ölçü değildir (görüntünün entropisi bu kadar değildir); ama ana noktayı gösterir: etiket, veriyle karşılaştırıldığında çok dar bir kanaldır. Denetimli öğrenme bu dar kanaldan öğrenir; etiketsiz veriyi ise kullanmaz.

Öz-denetimli öğrenme bu darboğazı aşmaya çalışır. Etiketsiz veriden bir sahte görev kurulur ve ağ, bu görevi çözerken veri hakkında bir şeyler öğrenir. Bu öğrenilen şey, daha sonra az etiketle çözülecek görevlerin temeli olur. Bölümün bir kısmı, bu sahte görevlerin gerçekten işe yarayan temsiller üretip üretmediğini ölçmeye ayrılmıştır.

Şekil 73.1, bu bölümde göreceğimiz yöntemleri tek bir haritada gösterir. Haritanın sol tarafında etiketli öğrenme ve öz-denetimli öğrenme ayrılır; sağ tarafta öz-denetimli yöntemlerin dört ailesi ve çok modlu öğrenme yer alır. Haritadaki sayılar ilgili alt bölümü gösterir.

![Şekil 73.1: Temsil öğrenme yöntemleri haritası. Etiketsiz verideki sahte görev ailesine göre gruplanmıştır; her kutunun yanındaki numara, yöntemin işlendiği alt bölümdür.](gorseller/b73_yontemler.png)

### Gösterimi nasıl ölçeriz?

Bir gösterimin iyi olup olmadığını doğrudan görmek mümkün değildir. Üç ölçüt kullanacağız ve üçünü de bu bölümde tekrar tekrar kullanacağız.

1. **Doğrusal yoklama (linear probe).** Ağın özellik çıkarıcısını dondurursun; üstüne yalnızca bir lojistik regresyon koyarsın (Bölüm 58.10). Yoklamanın doğruluğu, gösterimdeki bilgiye doğrudan doğrusal erişimi ölçer.
2. **k-NN değerlendirmesi.** Her test örneği için etiketli kümedeki en yakın `k` komşuya bakarsın. Eğitim gerektirmez; gösterimin uzayında sınıfların kümelenip kümelenmediğini ölçer.
3. **Az etiketle ince ayar.** Ağı baştan sona, çok az etiketle eğitirsin. Bu ölçüt, gösterimin başlangıç olarak ne kadar değerli olduğunu söyler.

Bu üç ölçütün hepsinde etiket sayısı önemlidir. Bu yüzden sonuçları tek bir sayı olarak değil, sınıf başına etiket sayısına göre bir eğri olarak raporlayacağız. Bölüm 57'de öğrendiğimiz gibi, tek bir tohumla yapılan karşılaştırma yanıltıcı olabilir; bu bölümün her ana ölçümü üç tohumla tekrarlanır.

﻿## 73.2 Temsili ölçmek: etiket eğrisi ve baseline'lar

Yöntemleri karşılaştırmadan önce bir deney düzeni kurmamız gerekir. Bu düzende üç veri kümesi vardır ve birbirinden ayrıdır. Birincisi **etiketsiz** havuzdur (20 000 görüntü). Öz-denetimli yöntemler yalnızca bu görüntüleri görür; etiketlere hiç dokunmazlar. İkincisi **etiketli** havuzdur (sınıf başına 500 örnek). Üçüncüsü **test** kümesidir (2000 örnek, dört sınıfın her kombinasyonunu içerir). Test kümesi hiçbir eğitimde kullanılmaz; bu, Bölüm 54'te konuştuğumuz veri sızıntısını önlemek içindir.

Görüntüleri Bölüm 66'daki gibi kendimiz üretiyoruz. Her görüntü, bir şekil (daire, kare, üçgen, artı), bir renk (dört renk), bir boyut (küçük, büyük) ve bir konum (dört köşe ve merkez) ile tanımlanır. Şeklin dönüklüğü rastgeledir, arka plan ve gürültü her görüntüde değişir. Sınıf etiketi yalnızca şekildir; renk, boyut ve konum birer gürültü kaynağıdır. Bu yapı, bir İHA kamerasında hedef sınıfını, ama hedefin rengini, ölçeğini ve konumunu bilmeden öğrenme problemini taklit eder.

Aynı üretici, her örneğin Türkçe açıklamasını da üretir ("kırmızı büyük daire sol üstte"). Açıklama, parametrelerden otomatik kurulur; bu sayede 73.10'da kullanacağımız metin–görüntü çiftleri de aynı kaynaktan gelir. Üretici kodu aşağıda tam olarak verilmiştir.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - sentetik goruntu ve Turkce aciklama ureticisi.

Her ornek: 32x32 RGB, bir renk, bir boyut, bir sekil, bir konum.
Aciklama ayni parametrelerden kurulur: "kirmizi buyuk daire sol
ustte".
"""

import numpy as np

RENK_AD = ["kırmızı", "yeşil", "mavi", "sarı"]
RENK_RGB = np.array(
    [
        [0.90, 0.10, 0.10],
        [0.10, 0.75, 0.20],
        [0.15, 0.30, 0.95],
        [0.95, 0.85, 0.10],
    ],
    np.float32,
)
SEKIL_AD = ["daire", "kare", "üçgen", "artı"]
BOYUT_AD = ["küçük", "büyük"]
BOYUT_R = np.array([5.0, 9.0], np.float32)
KONUM_AD = [
    "sol üstte",
    "sağ üstte",
    "sol altta",
    "sağ altta",
    "ortada",
]
KONUM_XY = np.array(
    [[9, 9], [23, 9], [9, 23], [23, 23], [16, 16]], np.float32
)

Y, X = np.mgrid[0:32, 0:32].astype(np.float32)


def maske(sekil, r, th, dx, dy):
    c, s = np.cos(th), np.sin(th)
    xr = c * dx + s * dy
```

```python
    yr = -s * dx + c * dy
    if sekil == 0:  # daire
        return xr**2 + yr**2 <= r * r
    if sekil == 1:  # kare
        return (np.abs(xr) <= 0.8 * r) & (np.abs(yr) <= 0.8 * r)
    if sekil == 2:  # üçgen
        return (np.abs(yr) <= 0.8 * r) & (
            np.abs(xr) <= (yr + 0.8 * r) / 2
        )
    return ((np.abs(xr) <= 0.3 * r) & (np.abs(yr) <= r)) | (  # artı
        (np.abs(yr) <= 0.3 * r) & (np.abs(xr) <= r)
    )


def ciz(rng, r_i, b_i, s_i, k_i, gurultu=0.03, dik=False):
    jx, jy = rng.uniform(-1.5, 1.5, 2)
    th = rng.uniform(0, 2 * np.pi)
    if dik:
        th = 0.0
    r = BOYUT_R[b_i] * rng.uniform(0.9, 1.1)
    m = maske(
        s_i,
        r,
        th,
        X - (KONUM_XY[k_i, 0] + jx),
        Y - (KONUM_XY[k_i, 1] + jy),
    )
    bg = (
        rng.uniform(0.15, 0.35, 3).astype(np.float32).reshape(3, 1, 1)
    )
    col = RENK_RGB[r_i].reshape(3, 1, 1)
    img = bg + m[None] * (col - bg)
    img = img + gurultu * rng.standard_normal(img.shape).astype(
        np.float32
    )
    return np.clip(img, 0, 1)


def ornekler(
    n,
```

```python
    rng,
    izin=None,
    sekil_sabit=None,
    sekil_renk=None,
    p_kural=0.0,
    dik=False,
):
    """n ornek uretir. izin: (renk, sekil) cift kumesi (None: hepsi).
    sekil_sabit: tum sekiller bu deger (siniflandirma etiketi icin).
    sekil_renk: sekle ozgu renk ipucu (kisa yol deneyi), p_kural
    olasilikla.
    """
    X_out = np.zeros((n, 3, 32, 32), np.float32)
    R = np.zeros(n, int)
    S = np.zeros(n, int)
    B = np.zeros(n, int)
    K = np.zeros(n, int)
    i = 0
    while i < n:
        s = (
            sekil_sabit
            if sekil_sabit is not None
            else rng.integers(4)
        )
        r = rng.integers(4)
        if sekil_renk is not None and rng.random() < p_kural:
            r = sekil_renk[s]
        if izin is not None and (r, s) not in izin:
            continue
        b = rng.integers(2)
        k = rng.integers(5)
        X_out[i] = ciz(rng, r, b, s, k, dik=dik)
        R[i], S[i], B[i], K[i] = r, s, b, k
        i += 1
    return X_out, R, S, B, K


def aciklama(r, b, s, k):
    return "%s %s %s %s" % (
        RENK_AD[r],
```

```python
        BOYUT_AD[b],
        SEKIL_AD[s],
        KONUM_AD[k],
    )


KELIMELER = ["<pad>"] + sorted(
    set(" ".join(RENK_AD + BOYUT_AD + SEKIL_AD + KONUM_AD).split())
)
KIMLIK = {w: i for i, w in enumerate(KELIMELER)}
UZUN = 5


def belirtec(metin):
    ids = [KIMLIK[w] for w in metin.split()][:UZUN]
    return ids + [0] * (UZUN - len(ids))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    Xs, R, S, B, K = ornekler(8, rng)
    for i in range(8):
        print(aciklama(R[i], B[i], S[i], K[i]), Xs[i].mean().round(3))
    print(KELIMELER, len(KELIMELER))
    print(belirtec(aciklama(0, 1, 2, 3)))
```



Üreticide iki nokta dikkatini çeksin. Birincisi `ciz` fonksiyonundaki gürültü: her piksele küçük bir Gauss gürültüsü eklenir, böylece ağ tek bir piksele bakarak sınıfı çözemez. İkincisi `KELIMELER` sözlüğü: sıralı bir liste olduğu için kelime kimlikleri her çalıştırmada aynıdır. Kısa bir kontrol için birkaç örnek çizdik ve şekillerin, renklerin ve konumların üretici tanımıyla uyuştuğunu gözle doğruladık.


### Dört ölçüt, bir eğri

Bir gösterimin değerini tek bir etiket sayısında ölçmek yanıltıcıdır. Etiket çok azken iyi bir gösterim bile kötü görünebilir; etiket çok çokken ise her yöntem düzelir. Bu yüzden her yöntemi **sınıf başına etiket sayısına** (n = 10, 50, 100, 500) karşı çizeriz. Bu eğrinin şekli, yöntemin hangi rejimde değerli olduğunu söyler.

Karşılaştırılan yöntemler şunlardır:

- **Ham piksel:** görüntünün 3072 pikseli doğrudan lojistik regresyona girer. En basit taban çizgisi.
- **PCA(50):** Bölüm 61.9'da gördüğümüz temel bileşenler, ilk 50 bileşenle. Doğrusal ve denetimsiz bir gösterim.
- **Rastgele ağ:** Aynı kodlayıcı, hiç eğitilmeden. Şaşırtıcı biçimde güçlü bir taban çizgisi olabilir; bunu ölçmek istiyoruz.
- **SimCLR, VICReg, SimSiam:** Öz-denetimli üç yöntem; her biri 6000 adımda ön eğitilir ve sonra dondurulup doğrusal yoklama uygulanır.
- **Denetimli (sıfırdan):** Kodlayıcı ve sınıflandırıcı birlikte, yalnızca etiketli örneklerle, artırmalı olarak eğitilir. Bu, etiket darboğazının ölçüsüdür.
- **SimCLR + ince ayar:** Öz-denetimli ağırlıklarla başlayıp tüm ağı az etiketle eğitmek.

Kodlayıcı, Bölüm 66'daki CNN'in küçük bir türevidir: dört konvolüsyon katmanı, her biri 2 adım atlayarak 32×32'den 2×2'ye iner, ardından kanal başına ortalama alınır (küresel ortalama havuzlama). Çıktı 256 boyutlu bir vektördür. Kodlayıcının ve yardımcı fonksiyonların tamamı `ortak73.py` içindedir; aşağıda parça parça veriyoruz.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - ortak kutuphane.

Veri, kodlayici, artirma, kayiplar ve olcumler.
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from synth73 import ornekler

torch.set_num_threads(4)
# GPU Bolum 76'ya ayrildi: varsayilan CPU; GPU yalniz BOLUM73_GPU=1
# ile.
AYG = torch.device(
    "cuda"
    if os.environ.get("BOLUM73_GPU") == "1"
    and torch.cuda.is_available()
    else "cpu"
)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
YOL = os.path.dirname(os.path.abspath(__file__))
ONBELLEK = os.path.join(YOL, "veri73.npz")
TUM = {"kirp": True, "renk": True, "gri": True, "flip": True}


def tekrar(n=40):
    """GPU paylasimi nedeniyle gelen gecici hatalarda (cuDNN, bellek
    dolulugu)
    bellegi bosaltip bekleyerek ayni (tohumlu, deterministik) cagriyi
    yeniden
    dener."""
    import time

    def sar(f):
```

```python
        def dene(*a, **k):
            for i in range(n):
                try:
                    return f(*a, **k)
                except RuntimeError as e:
                    msg = str(e)
                    if (
                        "cuDNN" not in msg
                        and "out of memory" not in msg
                    ) or i == n - 1:
                        raise
                    torch.cuda.empty_cache()
                    print(
                        "GPU gecici hata, yeniden deneniyor:",
                        i + 1,
                        flush=True,
                    )
                    time.sleep(15)

        return dene

    return sar


def veri_uret():
    rng = np.random.default_rng(73)
    U = ornekler(20000, rng)  # etiketsiz; yalniz goruntu
    Ltr = [ornekler(500, rng, sekil_sabit=s) for s in range(4)]
    Lx = np.concatenate([a[0] for a in Ltr])
    Ly = np.repeat(np.arange(4), 500)
    rt = np.random.default_rng(7300)
    T = ornekler(2000, rt)  # test: tum kombinasyonlar
    return dict(
        Ux=U[0],
        Ur=U[1],
        Us=U[2],
        Ub=U[3],
        Uk=U[4],
        Lx=Lx,
        Ly=Ly,
```

```python
        Tx=T[0],
        Tr=T[1],
        Ts=T[2],
        Tb=T[3],
        Tk=T[4],
    )


def yukle():
    if not os.path.exists(ONBELLEK):
        np.savez_compressed(ONBELLEK, **veri_uret())
    d = np.load(ONBELLEK)
    return {k: d[k] for k in d.files}


class Enkoder(nn.Module):
    """Kucuk evrisimli govde: 32->16->8->4->2, sonra kuresel
    ortalama."""

    def __init__(self):
        super().__init__()
        ch = [3, 32, 64, 128, 256]
        L = []
        for a, b in zip(ch[:-1], ch[1:]):
            L += [
                nn.Conv2d(a, b, 3, 2, 1, bias=False),
                nn.BatchNorm2d(b),
                nn.ReLU(inplace=True),
            ]
        self.govde = nn.Sequential(*L)

    def forward(self, x):
        return self.govde(x).mean((2, 3))


def kafa(a, b, orta=256):
    return nn.Sequential(
        nn.Linear(a, orta, bias=False),
        nn.BatchNorm1d(orta),
        nn.ReLU(inplace=True),
```

```python
        nn.Linear(orta, b),
    )


def artir(x, cfg=TUM):
    """Vektorize artirma: kirpma+aynalama, renk, gri, gurultu."""
    n, d = x.shape[0], x.device
    if cfg["kirp"]:
        s = torch.empty(n, device=d).uniform_(0.5, 1.0)
        tx = (torch.rand(n, device=d) * 2 - 1) * (1 - s)
        ty = (torch.rand(n, device=d) * 2 - 1) * (1 - s)
        if cfg["flip"]:
            f = 1 - 2 * (torch.rand(n, device=d) < 0.5).float()
        else:
            f = torch.ones(n, device=d)
        th = torch.zeros(n, 2, 3, device=d)
        th[:, 0, 0] = s * f
        th[:, 1, 1] = s
        th[:, 0, 2] = tx
        th[:, 1, 2] = ty
        g = F.affine_grid(th, x.shape, align_corners=False)
        x = F.grid_sample(
            x, g, align_corners=False, padding_mode="border"
        )
    if cfg["renk"]:
        on = (torch.rand(n, 1, 1, 1, device=d) < 0.8).float()
        b = torch.empty(n, 1, 1, 1, device=d).uniform_(0.6, 1.4)
        c = torch.empty(n, 1, 1, 1, device=d).uniform_(0.6, 1.4)
        sat = torch.empty(n, 1, 1, 1, device=d).uniform_(0.2, 1.8)
        y = x * b
        m = y.mean((1, 2, 3), keepdim=True)
        y = (y - m) * c + m
        gr = y.mean(1, keepdim=True)
        y = gr + (y - gr) * sat
        x = (on * y + (1 - on) * x).clamp(0, 1)
    if cfg["gri"]:
        on = (torch.rand(n, 1, 1, 1, device=d) < 0.2).float()
        x = on * x.mean(1, keepdim=True) + (1 - on) * x
    return (x + 0.03 * torch.randn_like(x)).clamp(0, 1)
```

```python

def nt_xent(z1, z2, tau):
    """NT-Xent: 2N gorunumde pozitif = esi, gerisi negatif."""
    n = z1.shape[0]
    z = F.normalize(torch.cat([z1, z2]), dim=1)
    s = z @ z.t() / tau
    eye = torch.eye(2 * n, dtype=torch.bool, device=z.device)
    s = s.masked_fill(eye, -1e9)
    hedef = torch.cat([torch.arange(n, 2 * n), torch.arange(0, n)])
    return F.cross_entropy(s, hedef.to(z.device))


def vicreg(z1, z2, lam=25.0, mu=25.0, nu=1.0):
    inv = F.mse_loss(z1, z2)

    def var_t(z):
        sd = torch.sqrt(z.var(0) + 1e-4)
        return F.relu(1 - sd).mean()

    def cov_t(z):
        z = z - z.mean(0)
        c = (z.t() @ z) / (z.shape[0] - 1)
        off = c - torch.diag(torch.diag(c))
        return (off**2).sum() / z.shape[1]

    return (
        lam * inv
        + mu * 0.5 * (var_t(z1) + var_t(z2))
        + nu * (cov_t(z1) + cov_t(z2))
    )


def simsiam_kayip(p1, p2, z1, z2, durdur=True):
    """Negatif kosinus; durdur=True ise hedef taraf stop-gradient."""
    if durdur:
        z1, z2 = z1.detach(), z2.detach()
    c1 = F.cosine_similarity(p1, z2, dim=1).mean()
    c2 = F.cosine_similarity(p2, z1, dim=1).mean()
    return -0.5 * (c1 + c2)
```

```python

@tekrar()
def egit(
    yontem,
    Ux,
    tohum,
    adim=6000,
    bs=256,
    tau=0.2,
    lr=1e-3,
    cfg=TUM,
    durdur=True,
    geri_cagri=None,
    cagri_adim=500,
):
    """Oz-denetimli on egitim. Doner: egitilmis Enkoder (eval
    modunda).
    geri_cagri(adim_no, enc, bas) her cagri_adim adimda cagrilir."""
    torch.manual_seed(tohum)
    enc = Enkoder().to(AYG)
    X = torch.as_tensor(Ux, device=AYG)
    ps = list(enc.parameters())
    if yontem == "rastgele":
        return enc.eval()
    bas = kafa(256, 128).to(AYG)
    ps += list(bas.parameters())
    if yontem == "simsiam":
        pred = kafa(128, 128, 64).to(AYG)
        ps += list(pred.parameters())
    opt = torch.optim.Adam(ps, lr=lr, weight_decay=1e-6)
    enc.train()
    g = torch.Generator(device="cpu").manual_seed(tohum)
    for it in range(adim):
        idx = torch.randint(0, X.shape[0], (bs,), generator=g).to(AYG)
        xb = X[idx]
        x1, x2 = artir(xb, cfg), artir(xb, cfg)
        z = bas(enc(torch.cat([x1, x2])))
        if yontem == "simclr":
            loss = nt_xent(z[:bs], z[bs:], tau)
        elif yontem == "vicreg":
```

```python
            loss = vicreg(z[:bs], z[bs:])
        else:
            p = pred(z)
            loss = simsiam_kayip(
                p[:bs], p[bs:], z[:bs], z[bs:], durdur
            )
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if geri_cagri is not None and (it + 1) % cagri_adim == 0:
            geri_cagri(it + 1, enc, bas)
    return enc.eval()


@tekrar()
def ozellik(enc, X, bs=1000):
    enc.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(X), bs):
            xb = torch.as_tensor(X[i : i + bs], device=AYG)
            out.append(enc(xb).cpu().numpy())
    return np.concatenate(out)


def yoklama(Ftr, ytr, Fte, yte, C=1.0, seed=0):
    """Dondurulmus ozellik uzerinde lojistik regresyon
    (dogrusal yoklama)."""
    sc = StandardScaler().fit(Ftr)
    clf = LogisticRegression(C=C, max_iter=3000, random_state=seed)
    clf.fit(sc.transform(Ftr), ytr)
    return clf.score(sc.transform(Fte), yte)


def knn(Ftr, ytr, Fte, yte, k=5):
    a = Ftr / np.linalg.norm(Ftr, axis=1, keepdims=True)
    b = Fte / np.linalg.norm(Fte, axis=1, keepdims=True)
    idx = np.argsort(-(b @ a.T), axis=1)[:, :k]
    oy = np.eye(int(ytr.max()) + 1)[ytr[idx]].sum(1)
    return float((oy.argmax(1) == yte).mean())
```

```python


def hizalama_tekduzelik(Z1, Z2, Zt, t=2.0):
    """Wang & Isola (2020): hizalama ve tekduzelik (kucuk = iyi)."""
    z1 = Z1 / np.linalg.norm(Z1, axis=1, keepdims=True)
    z2 = Z2 / np.linalg.norm(Z2, axis=1, keepdims=True)
    zt = Zt / np.linalg.norm(Zt, axis=1, keepdims=True)
    align = float(((z1 - z2) ** 2).sum(1).mean())
    d2 = np.maximum(2.0 - 2.0 * (zt @ zt.T), 0.0)  # birim vektorler
    n = len(zt)
    uni = float(np.log(np.exp(-t * d2[np.triu_indices(n, 1)]).mean()))
    return align, uni


def std_olcu(Z):
    """SimSiam olcusu: birim vektorlerin boyut basina std'si *
    sqrt(d).
    1 = cokme yok, 0 = tam cokme."""
    z = Z / np.linalg.norm(Z, axis=1, keepdims=True)
    return float(z.std(0).mean() * np.sqrt(z.shape[1]))


def bozulma(X, tur, siddet, rng):
    """Alan kaymasi: gurultu, kontrast azaltma, bulaniklik."""
    if tur == "gurultu":
        y = X + siddet * rng.standard_normal(X.shape)
        return np.clip(y, 0, 1).astype(np.float32)
    if tur == "kontrast":
        m = X.mean((1, 2, 3), keepdims=True)
        return (m + (X - m) * (1 - siddet)).astype(np.float32)
    from scipy.ndimage import uniform_filter

    k = 2 * siddet + 1
    return uniform_filter(X, size=(1, 1, k, k)).astype(np.float32)
```





Ön eğitimin adım sayısı önemlidir. İlk pilot denemelerimizde SimCLR'ı 2000 adım eğittiğimizde, sınıf başına 500 etiketle doğrusal yoklama belirgin biçimde düşük kaldı; aynı kodu 6000 adım eğittiğimizde doğruluk yaklaşık 0,9'a çıktı. Denetimli taban da 500 adımla yetersiz kaldı, 3000 adımda ise çok daha yüksek doğruluğa ulaştı. Bu, öz-denetimli yöntemlerin çoğu zaman sandığımızdan çok daha uzun eğitim istediğini gösterir; karşılaştırmayı yapmadan önce her yöntemi doygunluğa yakın eğittiğimizi kontrol etmek gerekir. Nihai koşularda ön eğitim 6000, denetimli ve ince ayar 3000 adımdır.

Aşağıdaki betik bütün eğriyi üretir: üç tohum, her tohumda öz-denetimli yöntemler, ayrıca denetimli ve ince ayar. Tohum sabittir ve sonuçlar CSV'ye yazılır.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t02: etiket sayisina gore dogruluk egrisi (3 tohum).

Yontemler: ham piksel, PCA, rastgele ag, SimCLR, VICReg, SimSiam
(hepsi dogrusal yoklama), denetimli (sifirdan, uctan uca) ve
SimCLR baslatmali ince ayar. Test: 2000 ornek (ayri tohum).
"""

import copy
import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.decomposition import PCA
from ortak73 import (
    AYG,
    TUM,
    Enkoder,
    artir,
    egit,
    ozellik,
    yoklama,
    yukle,
    tekrar,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
os.makedirs(CK, exist_ok=True)
NS = (10, 50, 100, 500)
TOHUM = (0, 1, 2)

d = yukle()
U, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]


def alt(n):
    """Her siniftan ilk n ornek (etiket butcesi)."""
```

```python
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def sinif_dogruluk(enc, head, X, y):
    enc.eval()
    with torch.no_grad():
        p = head(enc(torch.as_tensor(X, device=AYG))).argmax(1)
    return float((p.cpu().numpy() == y).mean())


@tekrar()
def uctan_uca(
    enc, head, X, y, tohum, adim=3000, bs=64, lr=1e-3, lr_govde=None
):
    """Uctan uca egitim: govde + bas birlikte (artirma ile)."""
    torch.manual_seed(tohum)
    Xt = torch.as_tensor(X, device=AYG)
    yt = torch.as_tensor(y, device=AYG)
    opt = torch.optim.Adam(
        [
            {"params": enc.parameters(), "lr": lr_govde or lr},
            {"params": head.parameters(), "lr": lr},
        ]
    )
    enc.train()
    for _ in range(adim):
        idx = torch.randint(0, len(Xt), (bs,), device=AYG)
        loss = F.cross_entropy(
            head(enc(artir(Xt[idx], TUM))), yt[idx]
        )
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return enc.eval()


def denetimli_sifirdan(X, y, tohum):
    torch.manual_seed(tohum)
```

```python
    enc = Enkoder().to(AYG)
    head = nn.Linear(256, 4).to(AYG)
    uctan_uca(enc, head, X, y, tohum)
    return sinif_dogruluk(enc, head, Tx, Ts)


def ince_ayar(enc0, X, y, tohum):
    enc = copy.deepcopy(enc0)
    torch.manual_seed(tohum)
    head = nn.Linear(256, 4).to(AYG)
    uctan_uca(enc, head, X, y, tohum, lr_govde=1e-4)
    return sinif_dogruluk(enc, head, Tx, Ts)


sonuc = []
# Deterministik taban cizgiler: ham piksel ve PCA(50)
Pf = U.reshape(len(U), -1)
pca = PCA(50, random_state=0).fit(Pf)
Tpix = Tx.reshape(len(Tx), -1)
for n in NS:
    i = alt(n)
    sonuc.append(
        (
            "piksel",
            n,
            0,
            yoklama(Lx[i].reshape(len(i), -1), Ly[i], Tpix, Ts),
        )
    )
    sonuc.append(
        (
            "pca",
            n,
            0,
            yoklama(
                pca.transform(Lx[i].reshape(len(i), -1)),
                Ly[i],
                pca.transform(Tpix),
                Ts,
            ),
```

```python
        )
    )
    print("taban n=%d tamam" % n, flush=True)

for tohum in TOHUM:
    for yontem in ("rastgele", "simclr", "vicreg", "simsiam"):
        enc = egit(yontem, U, tohum)
        if yontem == "simclr":
            torch.save(
                enc.state_dict(),
                os.path.join(CK, "simclr_s%d.pt" % tohum),
            )
        Fl = ozellik(enc, Lx)
        Ft = ozellik(enc, Tx)
        for n in NS:
            i = alt(n)
            sonuc.append(
                (yontem, n, tohum, yoklama(Fl[i], Ly[i], Ft, Ts))
            )
        print(yontem, "tohum", tohum, "tamam", flush=True)
        if yontem == "simclr":
            for n in NS:
                i = alt(n)
                sonuc.append(
                    (
                        "simclr_ince",
                        n,
                        tohum,
                        ince_ayar(enc, Lx[i], Ly[i], tohum),
                    )
                )
    for n in NS:
        i = alt(n)
        sonuc.append(
            (
                "denetimli",
                n,
                tohum,
                denetimli_sifirdan(Lx[i], Ly[i], tohum),
            )
```

```python
        )
    print("tohum", tohum, "denetimli ve ince ayar tamam", flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_etiket_egri.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "n_sinif", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])

print(
    "\nTest dogrulugu, ortalama +- sapma "
    "(tohum sayisi 3; piksel/PCA tek)"
)
for yo in (
    "piksel",
    "pca",
    "rastgele",
    "simclr",
    "vicreg",
    "simsiam",
    "simclr_ince",
    "denetimli",
):
    satir = []
    for n in NS:
        v = [s[3] for s in sonuc if s[0] == yo and s[1] == n]
        if len(v) > 1:
            satir.append(
                "%.3f+-%.3f" % (np.mean(v), np.std(v, ddof=1))
            )
        else:
            satir.append("%.3f      " % v[0])
    print("%-12s" % yo + "  ".join(satir))
print("sutunlar: n = 10, 50, 100, 500 (sinif basina)")
```



```term
$ python t02_egri.py
taban n=10 tamam
taban n=50 tamam
taban n=100 tamam
taban n=500 tamam
rastgele tohum 0 tamam
simclr tohum 0 tamam
vicreg tohum 0 tamam
simsiam tohum 0 tamam
tohum 0 denetimli ve ince ayar tamam
rastgele tohum 1 tamam
simclr tohum 1 tamam
vicreg tohum 1 tamam
simsiam tohum 1 tamam
tohum 1 denetimli ve ince ayar tamam
rastgele tohum 2 tamam
simclr tohum 2 tamam
vicreg tohum 2 tamam
simsiam tohum 2 tamam
tohum 2 denetimli ve ince ayar tamam

Test dogrulugu, ortalama +- sapma (tohum sayisi 3; piksel/PCA tek)
piksel      0.273        0.307        0.330        0.387
pca         0.286        0.310        0.338        0.360
rastgele    0.291+-0.013  0.313+-0.011  0.323+-0.006  0.390+-0.017
simclr      0.494+-0.036  0.733+-0.035  0.814+-0.035  0.909+-0.019
vicreg      0.348+-0.005  0.454+-0.026  0.535+-0.024  0.647+-0.024
simsiam     0.336+-0.028  0.445+-0.048  0.518+-0.060  0.643+-0.080
simclr_ince 0.503+-0.017  0.824+-0.014  0.933+-0.006  0.956+-0.004
denetimli   0.378+-0.016  0.834+-0.023  0.958+-0.014  0.981+-0.002
sutunlar: n = 10, 50, 100, 500 (sinif basina)
```


Sonuçları okurken önce taban çizgilere bak. Ham piksel ve PCA, dört sınıflı bu problemde `0,27`-`0,39` arasında kalıyor; yani rengin, konumun ve gürültünün piksel uzayında doğrusal olarak sınıfı bozduğu açık. Rastgele kodlayıcı ise piksel tabanına yakın (`0,29`-`0,39`); mimarinin kendisi, eğitilmeden, yalnızca çok az yapısal bilgi taşıyor. Öz-denetimli gösterim bu tabanın belirgin biçimde üstüne çıkıyor. SimCLR, doğrusal yoklamada n = 10'da `0,494`, n = 100'de `0,814`, n = 500'de `0,909` doğruluğa ulaşıyor. VICReg ve SimSiam ise daha düşük kalıyor (n = 500'de sırasıyla `0,647` ve `0,643`); SimSiam'ın tohumlar arası sapması da büyük. Bu fark 73.7'de çökme kavramıyla açıklanacak.

Asıl sonuç, denetimli eğriyle karşılaştırıldığında ortaya çıkıyor. Etiket çok az olduğunda (n = 10, toplam 40 örnek) SimCLR ile başlatılıp ince ayarlanan ağ `0,503` ile sıfırdan denetimli eğitimin `0,378` doğruluğunun belirgin biçimde üstünde. Etiket arttıkça tablo değişiyor: n = 50'de denetimli `0,834`, SimCLR + ince ayar `0,824`; n = 100'de denetimli `0,958`, ince ayar `0,933`; n = 500'de ikisi de `0,96`-`0,98` bandında. Yani öz-denetimli ön eğitimin değeri, etiketlerin darboğaz olduğu rejimde ortaya çıkıyor ve etiket sayısı sınıf başına birkaç onu geçtiğinde kayboluyor. Doğrusal yoklama (SimCLR, dondurulmuş gövde) ise ince ayarın gerisinde kalıyor; bu, Bölüm 66.11'de gördüğümüz "az veride dondur, çok veride ince ayar" dersiyle uyumlu, ama burada gövde tamamen öz-denetimli bir gösterimdir ve kayıp, gösterimin doğrusal ayrılabilirliğini değil, artırmalara karşı değişmezliği optimize eder.

Tohumlar arası sapmaya dikkat et: SimCLR ince ayarında n = 10 için sapma `0,017`, sıfırdan denetimli eğitimde ise `0,016`; ama SimSiam'da n = 500'de sapma `0,080`. Üç tohumla bile karşılaştırmanın kesin bir sıralama vermediği durumlar var; bunları metinde ayrıca işaretliyoruz.

![Şekil 73.2: Test doğruluğunun sınıf başına etiket sayısına göre değişimi (log eksen). Eğriler üç tohumun ortalaması, gölge ± bir sapma. Kesikli taban çizgisi şans düzeyidir.](gorseller/b73_etiket_egrisi.png)

## 73.3 Ön metin görevleri: dönüşüm tahmini

Öz-denetimli öğrenmenin en eski fikirlerinden biri, ağa bir girdinin **nasıl dönüştürüldüğünü** tahmin ettirmektir. Gidaris ve arkadaşları (2018; genel bilgi) görüntüyü 0°, 90°, 180° ya da 270° döndürüp hangi dönüşün uygulandığını tahmin ettirdiler. Ağ bunu doğru yapabilmek için nesnelerin doğal yönünü, yani gökyüzünün nerede olduğunu, insanların dik durduğunu, anlamak zorundadır. Bu yönelim bilgisi, sınıflandırma için de faydalı bir ipucudur.

Bu fikir bir **isaret varsa** çalışır. Dönüşüm tahmini, girdinin doğal bir yönü olduğunda anlamlıdır. Bizim şekillerimiz ise dönüklüğü rastgele olan geometrik nesnelerdir. Bir kare için 90° dönüş görüntüde fark yaratır, ama o karenin "doğru" yönünün ne olduğunu hiçbir şey söylemez. Bu nedenle iki ayrı veri kümesiyle deney yaptık: yönlendirilmiş (dik) şekiller, yani üçgenin tepesi yukarıda olan ve dönmemiş görüntüler; ve rastgele dönmüş şekiller, yani kullandığımız ana veri.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t06: on-gorev (pretext) deneyleri.

(a) Dondurme tahmini (Gidaris 2018 fikri): yonlendirilmis (dik)
sekiller
    ve rastgele donmus sekiller. Dondurme tahmini bir isaret
    gerektirir.
(b) Kucuk maskeli goruntu modeli (MAE fikri): 4x4 yamalar, %75
maskeleme,
    piksel yeniden olusturma. Kucuk bir transformer ile.
Her iki gorev icin: dogrusal yoklama (n = 100, 500 / sinif).
"""

import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak73 import AYG, Enkoder, ozellik, yoklama, yukle, tekrar
from synth73 import ornekler

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
Ud = ornekler(20000, np.random.default_rng(74), dik=True)[0]
Tdik = ornekler(2000, np.random.default_rng(7401), dik=True)[0]


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


@tekrar()
def dondur_egit(X_np, tohum, adim=3000, bs=64):
    torch.manual_seed(tohum)
    enc = Enkoder().to(AYG)
    bas = nn.Linear(256, 4).to(AYG)
```

```python
    X = torch.as_tensor(X_np, device=AYG)
    opt = torch.optim.Adam(
        list(enc.parameters()) + list(bas.parameters()), lr=1e-3
    )
    enc.train()
    etiket = torch.arange(4, device=AYG).repeat_interleave(bs)
    for _ in range(adim):
        xb = X[torch.randint(0, len(X), (bs,), device=AYG)]
        xs = torch.cat([torch.rot90(xb, k, (2, 3)) for k in range(4)])
        loss = F.cross_entropy(bas(enc(xs)), etiket)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return enc.eval(), bas


def dondur_dogruluk(enc, bas, X_np):
    xs = torch.as_tensor(X_np, device=AYG)
    dogru = 0
    with torch.no_grad():
        for k in range(4):
            tahmin = bas(enc(torch.rot90(xs, k, (2, 3)))).argmax(1)
            dogru += (tahmin == k).sum().item()
    return dogru / (4 * len(X_np))


class MaskeliModel(nn.Module):
    """Yama (4x4x3 = 48 boyut) -> 64 belirtec; kodlayici 16 gorunur
    yama,
    kod cozucu tum dizi (maske belirteci ile); kayip maskeli
    yamalarda.
    """

    def __init__(self, d=128, maske=0.75):
        super().__init__()
        self.maske = maske
        self.gom = nn.Linear(48, d)
        self.konum = nn.Parameter(0.02 * torch.randn(1, 64, d))
        self.mb = nn.Parameter(torch.zeros(1, 1, d))
        self.kod = nn.TransformerEncoder(
```

```python
            nn.TransformerEncoderLayer(d, 4, 256, batch_first=True),
            2,
            enable_nested_tensor=False,
        )
        self.coz = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d, 4, 256, batch_first=True),
            1,
            enable_nested_tensor=False,
        )
        self.cik = nn.Linear(d, 48)

    @staticmethod
    def yama(x):
        n = x.shape[0]
        return (
            x.reshape(n, 3, 8, 4, 8, 4)
            .permute(0, 2, 4, 1, 3, 5)
            .reshape(n, 64, 48)
        )

    def forward(self, x):
        P = self.yama(x)
        n = P.shape[0]
        k = int(64 * (1 - self.maske))
        sira = torch.rand(n, 64, device=x.device).argsort(1)
        gor, mas = sira[:, :k], sira[:, k:]
        h = self.gom(P) + self.konum
        z = self.kod(
            torch.gather(
                h, 1, gor.unsqueeze(-1).expand(-1, -1, h.shape[-1])
            )
        )
        full = self.mb.expand(n, 64, h.shape[-1]).scatter(
            1, gor.unsqueeze(-1).expand(-1, -1, z.shape[-1]), z
        )
        rec = self.cik(self.coz(full + self.konum))
        m = torch.ones(n, 64, device=x.device).scatter(1, gor, 0.0)
        return (((rec - P) ** 2).mean(-1) * m).sum() / m.sum()

    def ozellik(self, x):
```

```python
        P = self.yama(x)
        return self.kod(self.gom(P) + self.konum).mean(1)


@tekrar()
def maske_egit(X_np, tohum, adim=3000, bs=256):
    torch.manual_seed(tohum)
    m = MaskeliModel().to(AYG)
    X = torch.as_tensor(X_np, device=AYG)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    m.train()
    for _ in range(adim):
        xb = X[torch.randint(0, len(X), (bs,), device=AYG)]
        loss = m(xb)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return m.eval()


def maske_ozellik(m, X_np):
    out = []
    with torch.no_grad():
        for i in range(0, len(X_np), 500):
            xb = torch.as_tensor(X_np[i : i + 500], device=AYG)
            out.append(m.ozellik(xb).cpu().numpy())
    return np.concatenate(out)


satirlar = []
enc, bas = dondur_egit(Ud, 0)
satirlar.append(
    (
        "dondurme_dik",
        "rotasyon_dogruluk",
        dondur_dogruluk(enc, bas, Tdik),
    )
)
Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
satirlar.append(
```

```python
    (
        "dondurme_dik",
        "yoklama100",
        yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
    )
)
satirlar.append(
    (
        "dondurme_dik",
        "yoklama500",
        yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
    )
)
for r in satirlar[-3:]:
    print("%-18s %-18s %.4f" % r, flush=True)

enc, bas = dondur_egit(Ux, 0)
satirlar.append(
    (
        "dondurme_rastgele",
        "rotasyon_dogruluk",
        dondur_dogruluk(enc, bas, Tx),
    )
)
Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
satirlar.append(
    (
        "dondurme_rastgele",
        "yoklama100",
        yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
    )
)
satirlar.append(
    (
        "dondurme_rastgele",
        "yoklama500",
        yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
    )
)
for r in satirlar[-3:]:
```

```python
    print("%-18s %-18s %.4f" % r, flush=True)

for ad, egit_fn in (
    ("maske", lambda: maske_egit(Ux, 0)),
    ("maske_rastgele", lambda: MaskeliModel().to(AYG).eval()),
):
    m = egit_fn()
    Fl, Ft = maske_ozellik(m, Lx), maske_ozellik(m, Tx)
    satirlar.append(
        (
            ad,
            "yoklama100",
            yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
        )
    )
    satirlar.append(
        (
            ad,
            "yoklama500",
            yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
        )
    )
    for r in satirlar[-2:]:
        print("%-18s %-18s %.4f" % r, flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_on_gorev.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["gorev", "olcut", "deger"])
    for s in satirlar:
        w.writerow([s[0], s[1], "%.4f" % s[2]])
```

```term
$ python t06_on_gorev.py
dondurme_dik       rotasyon_dogruluk  0.5815
dondurme_dik       yoklama100         0.5045
dondurme_dik       yoklama500         0.5705
dondurme_rastgele  rotasyon_dogruluk  0.3922
dondurme_rastgele  yoklama100         0.4245
dondurme_rastgele  yoklama500         0.4920
maske              yoklama100         0.3900
maske              yoklama500         0.4500
maske_rastgele     yoklama100         0.3535
maske_rastgele     yoklama500         0.3810
```

Sonuç açıktır. Yönlendirilmiş şekillerde dönüşüm tahmini `0,58` doğrulukla yapılıyor (şans `0,25`). Bu ön görevden öğrenilen gösterimin doğrusal yoklaması ise n = 100'de `0,50`, n = 500'de `0,57`: rastgele ağın (`0,32` ve `0,39`) üstünde, ama SimCLR'ın (`0,85` ve `0,91`) çok altında. Yani görev bir sinyal bulduğunda bile, ondan çıkan gösterim sınıf bilgisini SimCLR kadar taşımıyor.

Rastgele dönmüş şekillerde tahmin `0,39` doğruluğa ulaştı. Bu şans üstü, ama öğrenilmiş bir yönelim anlamına gelmiyor. Olası açıklama, `torch.rot90`'ın dönüşü dizinin merkezi (15,5) etrafında yapması, şekil konumlarının ise 9, 23 ve 16 merkezli olmasıdır: köşe konumları dönünce ızgaranın öteki tarafına kayıyor ve ağ bu kaymayı ayırt edebiliyor. Bu açıklamayı doğrulamadık; ama sonuç şunu gösteriyor: bir ön görevin işe yaradığını sanmadan önce, çözülebilirliğin gerçek sinyalden mi yoksa veri üretiminin bir artefaktından mı geldiğini ölçmek gerekir. Düzeltme, konumları ızgara merkezine göre simetrik tanımlamaktır.

Ders şudur: bir ön görevi seçmek, verinin o görev için bilgi taşıdığını kontrol etmek anlamına gelir. Bu kontrol yapılmadan kurulan ön görev, eğitim kaybı düştükçe bile işe yaramaz bir gösterim üretebilir.

## 73.4 Maskeli modelleme: BERT'ten MAE'ye

Bölüm 70'te gördüğümüz maskeli dil modelinde, bir cümlenin bazı kelimeleri gizlenir ve ağ bunları çevreden tahmin eder. Görüntü için aynı fikir **maskeli görüntü modelleme**dir. He ve arkadaşları (2021; genel bilgi), Masked Autoencoder (MAE) ile görüntünün yamalarının yüzde 75'ini gizleyip gizli yamaların piksellerini yeniden oluşturmanın güçlü bir gösterim verdiğini gösterdiler. Yüksek maskeleme oranı, görevi zorlaştırır ve ağı yalnızca yakın komşuluğa değil, daha geniş yapılara bakmaya iter.

Küçük bir MAE'nin mimarisi şöyledir. Görüntü 4×4 piksellik 64 yamaya bölünür; her yama 48 değerden oluşur. Yamaların %75'i (48 tanesi) gizlenir ve kodlayıcı yalnızca kalan 16 yamayı görür. Kod çözücü, gizli yerlere öğrenilebilir bir maske belirteci koyar ve tüm diziyi yeniden kurar. Kayıp yalnızca gizli yamalarda, piksel düzeyinde ortalama karesel hata olarak hesaplanır. Eğitimden sonra kodlayıcı, tam bir görüntünün yamalarıyla çalıştırılır ve belirteçlerin ortalaması gösterim olur.


Bu deneyde küçük ölçekli bir MAE kullandığımızı açıkça belirtmek gerekir. Gerçek MAE büyük bir ViT ile büyük veride eğitilir; burada yalnızca yöntemin mantığını 3000 adımlık bir eğitimle gösteriyoruz. Ölçüm, maskeli modelin gösteriminin rastgele bir transformer'a göre ne kadar bilgi taşıdığıdır: yoklama doğrulukları `0,390` (n = 100) ve `0,450` (n = 500), rastgele transformer için `0,354` ve `0,381`. Bu sonuç bir şampiyonluk iddiası değil, bir yöntem tanıtımıdır: maskeli modelleme, görüntü ön eğitiminin güçlü bir yolu olsa da, küçük ölçekte ve kısa eğitimde kontrastif SimCLR'ın önüne geçemeyebilir.

Kod okurken dikkat edilecek iki nokta var. Birincisi, `MaskeliModel.forward` her adımda rastgele bir gizleme sırası üretir (`argsort`); böylece aynı görüntü her seferinde farklı yamalarla görülür. İkincisi, `ozellik` yönteminde tüm yamalar görünür yapılır. Eğitimde kodlayıcı yalnızca 16 yama gördü; test anında 64 yama görür. Bu uyumsuzluk MAE'nin bilinen bir özelliğidir ve gerçek uygulamalarda kodlayıcının çıktısı ayrıca dikkatle ölçülür.

## 73.5 Kontrastif öğrenme ve InfoNCE

Doğrusal yoklama bize gösterimin değerini söyler, ama gösterimi nasıl öğreneceğimizi söylemez. Kontrastif öğrenmenin fikri çok sadedir: bir örneğin iki görünümü birbirine yakın, farklı örneklerin görünümleri birbirinden uzak olsun. "Yakın" ve "uzak" ölçüsü gösterim uzayındaki benzerliktir (Bölüm 48.2'de gördüğümüz kosinüs benzerliği). Bu fikrin iki bileşeni vardır: **pozitif çiftler** (aynı kaynağın iki görünümü) ve **negatif çiftler** (farklı kaynaklar).

Pozitif çifti oluşturan şey artırmadır (augmentation). Aynı görüntünün kırpılmış ve renkleri değiştirilmiş iki kopyasını alırsan, ağ bu iki kopyanın aynı nesneye ait olduğunu öğrenmek zorundadır. Bu nedenle artırma yalnızca bir veri zenginleştirme aracı değil, öz-denetimli öğrenmenin **hedef tanımıdır**: hangi değişimlere değişmez olması gerektiğini sen seçersin. Bölüm 73.9'da bu seçimin ne kadar önemli olduğunu ölçeceğiz.

### Kayıp fonksiyonu: softmax olarak

Bir `q` çapa (anchor) vektörü, bir `k⁺` pozitif ve `K` tane `k⁻ⱼ` negatif olsun. Benzerlik `s(u, v) = sim(u, v) / τ` olsun; burada `sim` kosinüs benzerliği ve `τ > 0` bir sıcaklık parametresidir. **InfoNCE** kaybı şöyledir:

```
L = − log( exp(s(q, k⁺)) / [ exp(s(q, k⁺)) + Σⱼ exp(s(q, k⁻ⱼ)) ] )
```

Bu ifadeyi tanıyacaksın: `K + 1` aday arasından doğru olanı seçen bir softmax'in negatif log-olabilirliğidir. Yani bir çapraz entropidir (Bölüm 51.9-51.10). Hedef sınıf, pozitif adayın indeksidir ve hedef dağılım tek bir noktada yığılmıştır. Bölüm 51'de bu kaybın bir sınıflandırma kaybı olduğunu gördük; burada "sınıf" yerine "aday" vardır ve aday sayısı batch boyutuna bağlıdır.

Bu bağlantının bilgi kuramsal yüzü de vardır. Oord ve arkadaşları (2018), InfoNCE'nin `N` aday için şu alt sınırı kanıtladıklarını söylerler (genel bilgi): `I(q; k⁺) ≥ log N − L`. Burada `I` karşılıklı bilgidir (Bölüm 51.4). Kaybı küçültmek, karşılıklı bilgi için bir alt sınırı büyütmek demektir. Ayrıca bu sınır `log N` ile tavanlanmıştır: aday sayısı az olduğunda, kayıp ne kadar küçük olursa olsun, karşılıklı bilgi ölçülemeyecek kadar küçük bir üst sınır taşır. Bu, batch boyutunun neden önemli olduğunu açıklayan kuramsal bir gerekçedir.

Sıcaklığın etkisini türev ile görelim. `p⁺` ve `pⱼ`, softmax olasılıkları olsun. Kaybın benzerliğe göre türevi:

```
∂L/∂sim(q, k⁺) = (1/τ) (p⁺ − 1)
∂L/∂sim(q, k⁻ⱼ) = (1/τ) pⱼ
```

`τ` küçüldükçe `1/τ` büyür ama asıl etki olasılıklarda ortaya çıkar. Küçük `τ` ile softmax keskinleşir ve gradyanın büyük kısmı en yüksek benzerlikli, yani **zor (hard) negatiflere** düşer. Büyük `τ` ile dağılım düzleşir ve bütün negatifler benzer katkı verir. Bu bir değiş tokuştur: düşük `τ` daha ayırt edici bir gösterim verir, ama aşırı düşük `τ` eğitimi kararsız kılar ve aynı sınıftan olan "yanlış negatifleri" aşırı cezalandırır.

### Negatifler neden gerekli?

Negatif olmadan kayıp yalnızca pozitifleri birbirine yaklaştırır. O zaman en kolay çözüm, bütün girdileri aynı vektöre göndermektir: `f(x) = c` sabit. Bu durumda `sim = 1` ve kayıp minimumdadır; ama gösterim hiçbir bilgi taşımaz. Buna **çökme (collapse)** denir ve 73.7'de ayrıntısıyla göreceğiz. Negatifler, bu çözümü cezalandırarak ağı farklı örnekleri ayırt etmeye zorlar. Ama negatifler de bir bedel getirir: batch içindeki aynı sınıftan örnekler "yanlış negatif" olur ve onları ayırmaya çalışmak zararlıdır. Bu sorun, 73.10'da CLIP'te aynı açıklamayı paylaşan görüntülerle karşımıza çıkacak.

## 73.6 SimCLR: sıfırdan bir kontrastif hat

SimCLR (Chen ve arkadaşları, 2020; genel bilgi), yukarıdaki fikri üç basit parçayla uygular: güçlü bir artırma hattı, bir kodlayıcı ve küçük bir projeksiyon başlığı, ve NT-Xent kaybı. NT-Xent yalnızca InfoNCE'nin, bir batch içindeki bütün görünümlerin birbirine göre simetrik kullanıldığı biçimidir. Batch `N` örnek içeriyorsa, her örneğin iki görünümü olur; bu `2N` görünümde her görünüm için pozitif yalnızca eşidir, geri kalan `2N − 2` görünüm negatiftir.

Mimari aşağıdaki şekilde özetlenebilir. Önemli nokta şudur: kayıp projeksiyon başlığının çıktısı üzerinden hesaplanır, ama bizim kullanacağımız temsil `h = f(x)`, yani başlıktan önceki kodlayıcı çıktısıdır.

![Şekil 73.3: SimCLR'ın yapısı. Bir görüntünün iki artırılmış görünümü aynı kodlayıcıdan geçer; projeksiyon başlığı z vektörlerini üretir ve NT-Xent kaybı pozitif çifti negatiflere karşı ayırt eder. Eğitimden sonra başlık atılır.](gorseller/b73_simclr.png)

NT-Xent'in vektörleştirilmiş kodu `ortak73.py` içindedir ve yukarıda tamamı verildi. `nt_xent` fonksiyonu, `2N` görünümün benzerlik matrisini bir kez hesaplar, köşegeni (her görünümün kendisiyle benzerliği) çok küçük bir değerle maskeler ve pozitif indekslerini bir hedef vektöre koyar. Sonra bu, `F.cross_entropy` ile hesaplanır; yani kaybın bir çapraz entropi olduğunu kodda da görürsün.

Kodun tamamı yukarıda verilmişti; burada yalnızca ilgili bölümü anılıyor.


Bu kodun doğru olduğunu nasıl bilebiliriz? Aşağıdaki betik, vektörleştirilmiş sürümü, her çapayı tek tek ele alan bir döngülü referansla karşılaştırır. Referans, pozitifin softmax olasılığını elle hesaplar ve `−log` alır. İki sürüm `10⁻¹⁷` düzeyinde eşleşir; yani fark, çift duyarlıklı kayan nokta gürültüsünden ibarettir.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t01: NT-Xent kaybinin dogrulanmasi ve tau etkisi.

(a) Vektorlestirilmis nt_xent, dongulu referans gerceklemesiyle
eslesir mi?
(b) El ornegi: 2 pozitif cift, tau = 0.5, benzerlik matrisi ve kayip.
(c) Tau taramasi: pozitifler hizali / rastgele; kayip ne zaman
log(2N-1)?
"""

import math
import numpy as np
import torch
from ortak73 import nt_xent


def dongu(z1, z2, tau):
    """Referans: normalize et; her capa icin
    -log(pozitif / tum digerleri)."""
    z = torch.cat([z1, z2]).double()
    z = [v / v.norm() for v in z]
    n = len(z1)
    toplam = 0.0
    for a in range(2 * n):
        p = (a + n) % (2 * n)
        pay = math.exp(float(z[a] @ z[p]) / tau)
        payda = sum(
            math.exp(float(z[a] @ z[j]) / tau)
            for j in range(2 * n)
            if j != a
        )
        toplam += -math.log(pay / payda)
    return toplam / (2 * n)


torch.manual_seed(73)
z1 = torch.randn(8, 16, dtype=torch.float64)
z2 = z1 + 0.5 * torch.randn(8, 16, dtype=torch.float64)
print("(a) vektorlestirilmis ve dongulu kayip (N = 8, D = 16)")
for tau in (0.1, 0.5):
```

```python
    v = nt_xent(z1, z2, tau).item()
    r = dongu(z1, z2, tau)
    print(
        "tau=%.1f  vektor=%.10f  dongu=%.10f  fark=%.1e"
        % (tau, v, r, abs(v - r))
    )

print("\n(b) el ornegi: N = 2, birim vektorler, tau = 0.5")
a = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.float64)
b = torch.tensor([[0.8, 0.6], [0.6, 0.8]], dtype=torch.float64)
z = torch.cat([a, b])
print("benzerlik matrisi (sira: a0 a1 b0 b1):")
print(np.round((z @ z.T).numpy(), 2))
print("kayip (vektor) = %.6f" % nt_xent(a, b, 0.5).item())
print("kayip (dongu)  = %.6f" % dongu(a, b, 0.5))

print("\n(c) tau taramasi, N = 128, D = 64, sabit tohum")
rng = np.random.default_rng(73)
n = 128
Z1 = torch.as_tensor(rng.standard_normal((n, 64)))
Zh = torch.as_tensor(Z1.numpy() + 0.1 * rng.standard_normal((n, 64)))
Zr = torch.as_tensor(rng.standard_normal((n, 64)))
print("log(2N-1) = %.4f" % math.log(2 * n - 1))
print("tau    hizali   rastgele")
for tau in (0.05, 0.1, 0.2, 0.5, 1.0):
    print(
        "%.2f   %.4f   %.4f"
        % (
            tau,
            nt_xent(Z1, Zh, tau).item(),
            nt_xent(Z1, Zr, tau).item(),
        )
    )
```


```term
$ python t01_nt_xent.py
(a) vektorlestirilmis ve dongulu kayip (N = 8, D = 16)
tau=0.1  vektor=0.0622822516  dongu=0.0622822516  fark=2.1e-17
tau=0.5  vektor=1.4441975240  dongu=1.4441975240  fark=0.0e+00

(b) el ornegi: N = 2, birim vektorler, tau = 0.5
benzerlik matrisi (sira: a0 a1 b0 b1):
[[1.   0.   0.8  0.6 ]
 [0.   1.   0.6  0.8 ]
 [0.8  0.6  1.   0.96]
 [0.6  0.8  0.96 1.  ]]
kayip (vektor) = 0.870714
kayip (dongu)  = 0.870714

(c) tau taramasi, N = 128, D = 64, sabit tohum
log(2N-1) = 5.5413
tau    hizali   rastgele
0.05   0.0000   8.5615
0.10   0.0264   6.3922
0.20   1.1456   5.7794
0.50   3.6091   5.5906
1.00   4.5624   5.5582
```

Kontrolün ikinci kısmı, elle hesabı yapılabilecek küçük bir örnektir. Bunu Çözümlü Örnek 1'de adım adım yapacağız. Üçüncü kısım ise sıcaklığın ve rastgele gömmelerin kayıp üzerindeki etkisini gösterir. Rastgele, birbirinden bağımsız gömmelerde kayıp `log(2N − 1)` civarında olmalıdır, çünkü tek bir pozitif `2N − 1` aday arasından rastgele seçilmiş gibidir. Tablo bunu doğrular: `τ = 0.5` ve `τ = 1.0` için kayıp `5.59` ve `5.56` çıkıyor; `log 255 = 5.54` ile uyumlu. Ancak `τ = 0.05` için rastgele gömmelerde kayıp `8.56`ya çıkıyor, yani **şans düzeyinin de üstünde**. Bunun nedeni, düşük sıcaklıkta birkaç rastgele negatifin benzerliğinin pozitiften bile yüksek çıkmasıdır: softmax bu negatifleri cezalandırır. Bu, sıcaklığı sıfıra yakın seçmenin neden tehlikeli olduğunu gösteren bir ölçümdür.

![Şekil 73.4: Sıcaklığın ve batch boyutunun doğrusal yoklama doğruluğuna etkisi. Sol: sıcaklık taraması (n = 100 ve n = 500). Sağ: batch boyutu (adım sayısı sabit tutuldu).](gorseller/b73_tau_batch.png)

Ablasyon, bu sıcaklık etkisini kendi veri kümemizde ölçtü (3000 adım, tek tohum, CPU). Sonuçlar Şekil 73.4'te: sıcaklık düştükçe doğruluk artıyor. τ = 0,05 ve 0,1 için n = 500 yoklaması `0,859` ve `0,833`, τ = 0,5 ve 1,0 için `0,607` ve `0,598`; referans τ = 0,2 ise `0,760`. Bu, 0,1'in altındaki değerlerin burada kararsızlık yaratmadığını gösteriyor; ama 0,05'in altını denemedik, o bölgede kararsızlığın nerede başladığını bu veri bilmiyor.

Batch boyutu da benzer bir soruyu getiriyor. Batch 64, 256 ve 512 için n = 500 doğruluğu sırasıyla `0,543`, `0,760` ve `0,867`. Ama adım sayısını sabit tuttuğumuz için büyük batch'te bir adımda daha çok negatif, dolayısıyla toplamda daha çok örnek çifti görülüyor. Bu yüzden bu tablo "batch büyüdükçe kazanç" diyor, ama hesaplama ile örnek sayısı etkisini ayırmıyor; ayırmak için toplam örnek sayısını sabitleyen ayrı bir deney gerekir.

## 73.7 Çökme (collapse) ve negatifsiz yöntemler

Negatifler çökmeyi önler, ama bedelini de gördük: büyük batch ya da büyük bellek bankası gerektirirler. Bu yüzden 2020'lerin ikinci yarısında negatifsiz yöntemler ortaya çıktı. Bunların her biri, çökmeyi farklı bir mekanizmayla engeller. Önce çökmenin ne olduğunu netleştirelim.

Çökme, kodlayıcının ya da projeksiyon başlığının girdiden bağımsız, neredeyse sabit bir çıktı üretmesidir. Böyle bir gösterimde pozitif çiftlerin benzerliği maksimumdur ve kayıp küçüktür; ama sınıflar birbirinden ayrılamaz. Çökmeyi tespit etmenin bir yolu, birim vektörlerin her boyuttaki standart sapmasına bakmaktır. Bu ölçütü **std ölçütü** diye adlandıracağız: gösterim vektörleri birim küreye normalleştirilir, her boyutun standart sapması alınır ve sonuç `√d` ile çarpılır. Bağımsız ve düzgün dağılmış vektörlerde bu değer yaklaşık 1'dir; tam çökmede 0'a yaklaşır. Ölçüt, SimSiam makalesinde (Chen ve Hé, 2021; genel bilgi) kullanılan ölçüttür.

### SimSiam: stop-gradient ile çökmeyi önlemek

SimSiam, negatifleri, momentum kodlayıcıyı ve büyük batch'i tamamen atar. İki görünüm `x₁` ve `x₂` aynı kodlayıcıdan geçer, sonra bir projeksiyon `z` ve bir **tahmin başlığı** `p` üretilir. Kayıp, `p₁` ile `z₂` arasındaki negatif kosinüstür; simetrik olması için iki yön ortalanır. Kritik nokta **stop-gradient** operatörüdür: hedef taraf olan `z`, gradyan akışından koparılır. Yani `z₂` bir sabit gibi davranır.

Bunun neden çökmeyi önlediğini sezgisel olarak anlamak için şöyle düşün: tahmin başlığı, bir sabit hedefe yaklaşmaya çalışır; hedefin kendisi ağın parametrelerine bağlı değilse, ağ hedefi kendi sabit çıktısına çekemez. Stop-gradient olmadan ise kayıp iki tarafta da küçülür ve en kolay çözüm, her şeyi sabit bir vektöre göndermektir. Aşağıdaki kayıp fonksiyonu, stop-gradient'i bir bayrakla açıp kapatır; bu sayede aynı kodla iki durumu da deneyebiliriz.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t03: cokme (collapse) izleme.

SimSiam stop-gradient ile ve stop-gradient olmadan; referans olarak
SimCLR. Her 500 adimda: projeksiyon ciktisinin SimSiam std olcusu ve
500 ornekli etiketli kumede k-NN dogrulugu (test kumesinde olcum).
"""

import csv
import os
import torch
from ortak73 import AYG, egit, knn, ozellik, std_olcu, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
kayit = []


def izle(ad):
    def cagri(adim, enc, bas):
        bas.eval()
        with torch.no_grad():
            z = (
                bas(enc(torch.as_tensor(Tx, device=AYG)))
                .cpu()
                .numpy()
            )
        bas.train()
        f_t, f_l = ozellik(enc, Tx), ozellik(enc, Lx)
        enc.train()
        kayit.append((ad, adim, std_olcu(z), knn(f_l, Ly, f_t, Ts)))
        print(
            ad,
            adim,
            "std=%.3f knn=%.3f" % (kayit[-1][2], kayit[-1][3]),
            flush=True,
        )
```

```python
    return cagri


for ad, yontem, durdur in (
    ("simsiam_dur", "simsiam", True),
    ("simsiam_dursuz", "simsiam", False),
    ("simclr", "simclr", True),
):
    enc = egit(yontem, Ux, 0, durdur=durdur, geri_cagri=izle(ad))
    torch.save(enc.state_dict(), os.path.join(CK, "%s_s0.pt" % ad))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_cokme.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "std", "knn"])
    for r in kayit:
        w.writerow([r[0], r[1], "%.4f" % r[2], "%.4f" % r[3]])
```

Deneyde tohum 0 ile üç koşu yaptık: SimSiam stop-gradient ile, SimSiam stop-gradient olmadan ve referans olarak SimCLR. Her 500 adımda projeksiyon çıktısının std ölçütünü ve yine 500 etiketli örnekle k-NN doğruluğunu kaydettik.

```term
$ python t03_coll.py
simsiam_dur 500 std=0.809 knn=0.451
simsiam_dur 1000 std=0.837 knn=0.390
simsiam_dur 1500 std=0.852 knn=0.398
simsiam_dur 2000 std=0.878 knn=0.388
simsiam_dur 2500 std=0.879 knn=0.343
simsiam_dur 3000 std=0.902 knn=0.358
simsiam_dur 3500 std=0.899 knn=0.367
simsiam_dur 4000 std=0.895 knn=0.366
simsiam_dur 4500 std=0.912 knn=0.365
simsiam_dur 5000 std=0.915 knn=0.373
simsiam_dur 5500 std=0.916 knn=0.381
simsiam_dur 6000 std=0.916 knn=0.380
simsiam_dursuz 500 std=0.017 knn=0.481
simsiam_dursuz 1000 std=0.011 knn=0.483
simsiam_dursuz 1500 std=0.009 knn=0.478
simsiam_dursuz 2000 std=0.007 knn=0.484
simsiam_dursuz 2500 std=0.006 knn=0.485
simsiam_dursuz 3000 std=0.005 knn=0.483
simsiam_dursuz 3500 std=0.004 knn=0.483
simsiam_dursuz 4000 std=0.004 knn=0.490
simsiam_dursuz 4500 std=0.003 knn=0.470
simsiam_dursuz 5000 std=0.003 knn=0.491
simsiam_dursuz 5500 std=0.002 knn=0.502
simsiam_dursuz 6000 std=0.002 knn=0.513
simclr 500 std=0.989 knn=0.343
simclr 1000 std=0.990 knn=0.338
simclr 1500 std=0.991 knn=0.337
simclr 2000 std=0.990 knn=0.352
simclr 2500 std=0.992 knn=0.366
simclr 3000 std=0.993 knn=0.401
simclr 3500 std=0.993 knn=0.414
simclr 4000 std=0.994 knn=0.424
simclr 4500 std=0.994 knn=0.439
simclr 5000 std=0.995 knn=0.434
simclr 5500 std=0.995 knn=0.473
simclr 6000 std=0.996 knn=0.476
```

Tablo çökmeyi açıkça gösteriyor, ama iki ölçütün ne ölçtüğünü ayırmak gerekiyor. Stop-gradient ile SimSiam'da projeksiyon çıktısının std ölçütü 6000. adımda `0,916` ve yüksek kalıyor; k-NN ise `0,380`. Stop-gradient kaldırıldığında std ölçütü ilk kayıtta (500. adım) zaten `0,017`, 6000. adımda `0,002` oluyor: gösterim vektörleri neredeyse tek bir yöne çökmüş. Buna karşılık kodlayıcı özelliklerinde k-NN doğruluğu şans düzeyine (`0,25`) inmiyor; `0,481`-`0,513` bandında kalıyor.

Bu bir ayrım gerektiriyor. Çökme, projeksiyon başlığında (z) ölçülüyor; kodlayıcı çıktısı (h) bu çökmeden kısmen korunabiliyor. Yani std ölçütü çökmenin varlığını ve yerini gösteriyor, k-NN ise bilginin ne kadarının kodlayıcıda kaldığını ölçüyor. Bu koşuda k-NN'e bakarak "çökme yok" sonucuna varmak yanlış olurdu; Örnek 4'te bu tuzağı ayrıntılı göreceğiz. Bir not daha: k-NN burada standartlaştırılmamış özellikler üzerinde kosinüs benzerliğiyle hesaplandı ve değerleri mutlak olarak düşük; yalnızca koşular arasında karşılaştırmak için kullanılmalı. Stop-gradient'li koşuda k-NN'in düşük (`0,38`) çıkması da bu ölçümün zayıf yanına işaret ediyor.

![Şekil 73.5: SimSiam'ın çökmesi. Solda projeksiyon çıktısının std ölçütü (1 = çökme yok); sağda etiketli kümede k-NN doğruluğu. Stop-gradient olmadan ölçüt sıfıra gider ve doğruluk şans düzeyine iner.](gorseller/b73_cokme.png)

### VICReg: varyans ve kovaryans düzenlileştirmesi

Barlow Twins ve VICReg (Bardes ve arkadaşları, 2022; genel bilgi), çökmeyi kayıp fonksiyonunun içinde açıkça cezalandırır. VICReg üç terim toplar. **Benzerlik** terimi (`MSE`) pozitif çiftleri yaklaştırır. **Varyans** terimi, her boyutun standart sapmasını bir eşiğin (1) üstünde tutar: `max(0, 1 − std)`. **Kovaryans** terimi, boyutlar arasındaki kovaryansın köşegen dışı elemanlarını sıfıra iter; böylece boyutlar birbirinin kopyası olmaz. Terimler `25, 25, 1` katsayılarıyla birleşir.

Bu yaklaşımın felsefesi, çökmeyi bir mimari hilesiyle değil, gösterimin geometrisini doğrudan kontrol ederek engellemektir. Varyans terimi çökmeyi (std → 0) doğrudan cezalandırır; kovaryans terimi ise boyutların bilgiyi tekrarlamasını önler.

### MoCo ve DINO: kavramsal not

Momentum Contrast (MoCo; He ve arkadaşları, 2020, genel bilgi), negatifleri bir kuyrukta saklar ve hedef kodlayıcıyı, çevrimiçi kodlayıcının üstel hareketli ortalamasıyla güncelleştirir. Böylece büyük bir negatif kümesi, büyük batch olmadan kullanılabilir. DINO (Caron ve arkadaşları, 2021; genel bilgi) ise kendi kendine damıtmayı kullanır: bir öğrenci ağ, momentum ile güncellenen bir öğretmen ağın çıktısını taklit eder, ve çökme, öğretmen çıktısının ortalamasının merkezlenmesi ile sivri dağılımlı bir softmax ile önlenir. Bu iki yöntemi bu bölümde kodlamadık; kavramlarını anlamanın yeterli olduğunu düşünüyoruz. Kodlamak istersen SimSiam kodunun hedef tarafına momentum kodlayıcı eklemek iyi bir başlangıç olur.

## 73.8 Hizalama ve tekdüzelik: gösterimin geometrisi

Bir gösterimin kalitesini tek bir ölçütle özetlemek kolay değildir. Wang ve Isola (2020; genel bilgi), iyi bir kontrastif gösterimin iki özelliğini ayrı ayrı ölçen iki sayı önerdi. **Hizalama** (alignment), aynı kaynağın iki görünümünün gösterimde ne kadar yakın olduğunu ölçer:

```
hizalama = E[ || f(x₁) − f(x₂) ||² ]
```

Burada `f` birim küreye normalleştirilmiş gösterimdir ve beklenti pozitif çiftler üzerindedir. Küçük hizalama, pozitiflerin yakın olduğu anlamına gelir.

**Tekdüzelik** (uniformity), gösterimin birim küre üzerinde ne kadar düzgün yayıldığını ölçer:

```
tekdüzelik = log E[ exp(−t · || f(x) − f(y) ||²) ]
```

Beklenti, bağımsız iki örnek üzerindedir ve `t = 2` alınmıştır. Vektörler küre üzerinde toplanırsa, çoğu çift birbirine yakın olur ve üstel terimler büyür; tekdüzelik yükselir (daha kötü). Düzgün yayılmış vektörler için tekdüzelik düşüktür. Bu iki ölçüt birlikte okunmalıdır: hizalama tek başına, bütün noktaları bir yerde toplayarak kolayca "iyileştirilebilir"; tekdüzelik bunu cezalandırır.

Aşağıdaki sonuç tablosu, bu iki ölçütü tohum 0 üzerinde ham piksel, rastgele ağ, SimCLR, VICReg ve SimSiam için verir. Pozitif çiftler için artırma yine aynı sabit tohumla üretilmiştir.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t04: hizalama, tekduzelik, k-NN, yoklama ve t-SNE.

Tohum 0. Pikseller, rastgele ag, SimCLR, VICReg ve SimSiam (stop-
grad).
Hizalama icin ayni testten iki artirilmis gorunum (sabit tohum).
"""

import csv
import os
import numpy as np
import torch
from sklearn.manifold import TSNE
from ortak73 import (
    AYG,
    TUM,
    Enkoder,
    artir,
    egit,
    hizalama_tekduzelik,
    knn,
    ozellik,
    yoklama,
    yukle,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
i100 = np.concatenate(
    [np.arange(c * 500, c * 500 + 100) for c in range(4)]
)

torch.manual_seed(123)
Tg = torch.as_tensor(Tx, device=AYG)
V1 = artir(Tg, TUM).cpu().numpy()
V2 = artir(Tg, TUM).cpu().numpy()
```

```python
def yukle_enc(yol):
    e = Enkoder().to(AYG)
    e.load_state_dict(
        torch.load(
            os.path.join(CK, yol), map_location=AYG, weights_only=True
        )
    )
    return e.eval()


encs = {
    "rastgele": egit("rastgele", Ux, 0),
    "simclr": yukle_enc("simclr_s0.pt"),
    "vicreg": egit("vicreg", Ux, 0),
    "simsiam": yukle_enc("simsiam_dur_s0.pt"),
}

satirlar = []
a, u = hizalama_tekduzelik(
    V1.reshape(len(V1), -1),
    V2.reshape(len(V2), -1),
    Tx.reshape(len(Tx), -1),
)
Fl = Lx.reshape(len(Lx), -1)
Ft = Tx.reshape(len(Tx), -1)
satirlar.append(
    (
        "piksel",
        a,
        u,
        knn(Fl, Ly, Ft, Ts),
        yoklama(Fl[i100], Ly[i100], Ft, Ts),
    )
)
print("piksel  hiz=%.4f tek=%.4f" % satirlar[-1][1:3], flush=True)
for ad, enc in encs.items():
    a, u = hizalama_tekduzelik(
        ozellik(enc, V1), ozellik(enc, V2), ozellik(enc, Tx)
    )
    Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
```

```python
    satirlar.append(
        (
            ad,
            a,
            u,
            knn(Fl, Ly, Ft, Ts),
            yoklama(Fl[i100], Ly[i100], Ft, Ts),
        )
    )
    print(
        "%-8s hiz=%.4f tek=%.4f" % ((ad,) + satirlar[-1][1:3]),
        flush=True,
    )

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_hizalama.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(
        ["yontem", "hizalama", "tekduzelik", "knn500", "yoklama100"]
    )
    for s in satirlar:
        w.writerow(
            [
                s[0],
                "%.4f" % s[1],
                "%.4f" % s[2],
                "%.4f" % s[3],
                "%.4f" % s[4],
            ]
        )

# t-SNE: 1000 test ornegi, sekle gore renk
rng = np.random.default_rng(73)
idx = rng.choice(len(Tx), 1000, replace=False)
izdusum = [("piksel", Tx.reshape(len(Tx), -1)[idx])]
```

```python
for ad in ("rastgele", "simclr", "vicreg", "simsiam"):
    izdusum.append((ad, ozellik(encs[ad], Tx)[idx]))
with open(
    os.path.join(VERI, "b73_tsne.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "x", "y", "sekil"])
    for ad, F in izdusum:
        p = TSNE(
            n_components=2, perplexity=30, init="pca", random_state=0
        ).fit_transform(F)
        for (x, y), s in zip(p, Ts[idx]):
            w.writerow([ad, "%.3f" % x, "%.3f" % y, int(s)])
        print("tsne %s tamam" % ad, flush=True)
```

```term
$ python t04_olcum.py
piksel  hiz=0.2736 tek=-0.8227
rastgele hiz=0.0483 tek=-0.1542
simclr   hiz=0.4187 tek=-2.0816
vicreg   hiz=0.4529 tek=-2.1858
simsiam  hiz=0.4056 tek=-1.7747
tsne piksel tamam
tsne rastgele tamam
tsne simclr tamam
tsne vicreg tamam
tsne simsiam tamam
```

Sonuçlar, bu iki ölçütün çökmeyle nasıl ilişkili olduğunu gösteriyor. Rastgele ağ hizalamada en iyi görünüyor (`0,048`), ama tekdüzeliği yalnızca `−0,154`: çıktıları birbirine yakın yığılmış, yani hizalama düşük olsa da yayılım kötü. SimCLR (hizalama `0,419`, tekdüzelik `−2,082`) ve VICReg (`0,453`, `−2,186`) tekdüzelikte belirgin üstün. VICReg'in tekdüzeliği en iyi olmasına rağmen, n = 100 yoklama doğruluğu (`0,482`) SimCLR'ın (`0,846`) çok altında. Bu, tekdüzeliğin tek başına yeterli olmadığını gösteriyor: VICReg noktaları küreye düzgün yayıyor ama sınıf bilgisini bu koşuda SimCLR kadar ayırmıyor. Önemli bir uyarı: hizalama ve tekdüzelik, yoklama doğruluğunu tek başına belirlemez. Bu ölçütler gösterimin **geometrisini** tarif eder; hangi bilginin orada olduğunu değil. Bu yüzden bu bölümde ölçütleri her zaman yoklama ve k-NN ile birlikte raporluyoruz.

![Şekil 73.6: Hizalama–tekdüzelik düzlemi. Sol alt köşe (küçük hizalama, küçük tekdüzelik) idealdir. Her nokta bir yöntemi tohum 0 üzerinde gösterir; etiketlerdeki k-NN doğruluğu parantez içindedir.](gorseller/b73_hizalama.png)

### t-SNE ile görsel bakış

Bölüm 61.10'da t-SNE ve UMAP'in yüksek boyutlu verileri iki boyuta indirgediğini ve bu izdüşümlerin yorumlanmasında dikkat gerektirdiğini gördük. Burada, 1000 test örneğinin gösterimlerine t-SNE uyguladık ve noktaları şekle göre renklendirdik. Bu, bir gösterimin sınıfları kümeleyip kümelemediğini hızlıca görmek için kullanışlıdır; ama bir kümenin görünmesi, kümenin bilgi olarak doğrusal ayrılabilir olduğu anlamına gelmez. Bulgu açık: şekle göre renklendirildiğinde dört yöntemde de sınıflar kümelenmiyor. Ham piksellerdeki küçük kümeler karışık renkte; SimCLR ve VICReg panellerinde kümeler daha sıkı olsa da sınıfları ayırmıyor. Bu, t-SNE kümelerinin bu veride şekil dışı bir faktöre (büyük olasılıkla renk ya da konum; doğrulanmadı) göre oluştuğunu düşündürüyor. Doğrusal yoklamada SimCLR'ın şekli iyi ayırması, bu nedenle t-SNE'nin sınıf ayrışmasını göstermemesiyle çelişmez: t-SNE yerel komşuluğu gösterir, doğrusal ayrılabilirliği değil.

```term
$ python t04_olcum.py

```

![Şekil 73.7: Test örneklerinin t-SNE izdüşümleri (1000 örnek, şekle göre renk). Hiçbir panelde dört şekil ayrı kümelere ayrılmıyor; küçük kümeler karışık renklidir.](gorseller/b73_tsne.png)

## 73.9 Artırma: pozitif çiftin tanımı ve kısa yollar

Kontrastif öğrenmede artırma, pozitif çifti tanımlar. Bu yüzden hangi artırmanın kullanıldığı, gösterimin neyi öğreneceğini doğrudan belirler. Bir artırma, ağa bir değişmezliği öğretir: kırpma konuma, renk bozma renge, gri tonlamaya renk bilgisine karşı değişmezlik. Bu iyi bir şey olabilir (göreve ait olmayan bilgiyi atar) ya da kötü olabilir (göreve ait bilgiyi de atar).

Artırmaların üç kategorisi vardır. **Geometrik** artırmalar (kırpma, aynalama, döndürme) konum ve yönelime değişmezlik öğretir. **Renk** artırmaları (parlaklık, kontrast, doygunluk) ve **gri tonlama** renge değişmezlik öğretir. **Gürültü** artırması ise piksel düzeyinde değişmezlik öğretir. Bu kategorileri ayrı ayrı kapatıp ablasyon yapmak, hangi değişmezliğin temsili nasıl şekillendirdiğini gösterir.

Ablasyon deneyi, tohum 0 ile altı koşudan oluşur: tam artırma, kırpma yok, renk yok, gri yok, aynalama yok ve hiçbiri. "Hiçbiri" koşusu, yalnızca gürültü içeren bir kontrol grubudur. Ölçüm doğrusal yoklama (n = 100 ve n = 500) ile yapılır.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t05: artirma ablasyonu, tau ve batch taramasi (tohum 0).

Her kosu 3000 adim SimCLR on egitimidir (CPU; GPU Bolum 76'ya
ayrildi).
Referans yapilandirma (tam artirma, tau = 0.2, batch = 256) bir kez
egitilir ve artirma, tau ve batch tablolarinda kullanilir.
Olcum: n = 100 ve n = 500 (sinif basina) dogrusal yoklama; k-NN (n =
500).
"""

import csv
import os
import numpy as np
from ortak73 import TUM, egit, knn, ozellik, yoklama, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ADIM = 3000
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def olc(enc):
    Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
    return (
        yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
        yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
        knn(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
    )


sonuc = []
```

```python
def kaydet(grup, deger, enc):
    p100, p500, k = olc(enc)
    sonuc.append((grup, deger, p100, p500, k))
    print(grup, deger, "%.3f %.3f %.3f" % (p100, p500, k), flush=True)


YOK = {"kirp": False, "renk": False, "gri": False, "flip": False}
ref = egit("simclr", Ux, 0, adim=ADIM)
kaydet("artirma", "tam", ref)
for ad, cfg in (
    ("kirpma_yok", {**TUM, "kirp": False}),
    ("renk_yok", {**TUM, "renk": False}),
    ("gri_yok", {**TUM, "gri": False}),
    ("aynalama_yok", {**TUM, "flip": False}),
    ("hicbiri", YOK),
):
    kaydet("artirma", ad, egit("simclr", Ux, 0, cfg=cfg, adim=ADIM))

for tau in (0.05, 0.1, 0.5, 1.0):
    kaydet("tau", str(tau), egit("simclr", Ux, 0, tau=tau, adim=ADIM))
kaydet("tau", "0.2", ref)

for bs in (64, 512):
    kaydet("batch", str(bs), egit("simclr", Ux, 0, bs=bs, adim=ADIM))
kaydet("batch", "256", ref)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_ablasyon.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(
        ["grup", "deger", "yoklama100", "yoklama500", "knn500"]
    )
    for s in sonuc:
        w.writerow(
            [s[0], s[1], "%.4f" % s[2], "%.4f" % s[3], "%.4f" % s[4]]
```

```python
        )
```

```term
$ python t05_ablasyon.py
artirma tam 0.620 0.760 0.400
artirma kirpma_yok 0.639 0.802 0.858
artirma renk_yok 0.402 0.501 0.300
artirma gri_yok 0.385 0.513 0.303
artirma aynalama_yok 0.605 0.741 0.372
artirma hicbiri 0.493 0.615 0.500
tau 0.05 0.729 0.859 0.485
tau 0.1 0.739 0.833 0.432
tau 0.5 0.491 0.607 0.360
tau 1.0 0.479 0.598 0.361
tau 0.2 0.620 0.760 0.400
batch 64 0.418 0.543 0.362
batch 512 0.760 0.867 0.441
batch 256 0.620 0.760 0.400
```

Sonuçlar, 3000 adımlık tek tohumlu koşularda şöyle: referans (tam artırma) n = 100'de `0,620`, n = 500'de `0,760`. Kırpmayı kapatmak doğruluğu artırıyor (`0,639` ve `0,802`); aynalamayı kapatmak etkisiz (`0,605` ve `0,741`). Renk bozmayı (`0,402` ve `0,501`) ya da gri tonlamayı (`0,385` ve `0,513`) kapatmak ise belirgin biçimde düşürüyor. Hiçbir artırma olmadığında ise `0,493` ve `0,615`.

Kırpmanın zararlı çıkması şaşırtıcı görünebilir, ama bu veri kümesinde açıklanabilir: kırpma ölçeği `0,5`-`1` aralığında seçiliyor ve 9 piksel yarıçaplı büyük bir şekil kırpıldığında sınıfın görünen parçası azalıyor. Bu durumda "kırpmaya karşı değişmezlik" öğretilen şey, sınıfı kısmen silen bir dönüşüm oluyor. Renk ve gri tonlama ise kısa yolu kırmak için gerekli görünüyor: renk bozma yoksa ağ rengi, gri tonlama yoksa kanal bilgisini daha kolay kullanıyor. Bu bir gözlem; mekanizma için ayrı bir deney gerekir. Ayrıca k-NN sütununda kırpma kapalıyken `0,858` görülüyor; bu da bu ölçümün standartlaştırılmamış olmasının sonucu olabilir ve yorumlanırken dikkat edilmelidir.

![Şekil 73.8: Artırma ablasyonu. Her çubuk, ilgili artırmanın kapatıldığı SimCLR koşusunun doğrusal yoklama doğruluğudur (tohum 0).](gorseller/b73_artirma.png)

### Kısa yol: renk ipucu

Artırmanın bir başka rolü, kısa yolları (shortcut) kırmaktır. Kısa yol, ağın göreve ait olmayan ama eğitim verisinde güçlü bir ipucu olan bir özelliği öğrenmesidir. Bunu yapay bir durumla gösterelim. Ön eğitim verisinde şekil ile renk %90 oranında birbirine bağlıdır: daireler kırmızı, kareler yeşil, üçgenler mavi, artılar sarıdır. Test verisinde ise renkler rastgeledir. Ağ, şekli öğrenmek yerine rengi öğrenirse, rengi okuyarak bir ön görevi çözebilir; bu durumda gösterim şekle bakmaz.

Bu deneyde iki ön eğitim koşusu yaptık: tam artırma (renk bozma açık) ve renk bozma kapalı. Ölçüm, şekil yoklaması ve renk yoklamasıdır. Renk yoklaması için test kümesinin yarısıyla eğitip diğer yarısında ölçüm yapıyoruz.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t10: kisa yol (shortcut) ogrenme ve renk artirmasi.

Oz-denetimli veri: sekil ile renk %90 oraninda iliskili (daire-
kirmizi,
kare-yesil, ucgen-mavi, arti-sari). Test verisinde renkler rastgele.
Iki egitim: tam artirma (renk bozma acik) ve renk bozma kapali.
Olcum: sekil yoklamasi (n = 10, 100, 500) ve renk yoklamasi.
"""

import csv
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from synth73 import ornekler
from ortak73 import TUM, egit, ozellik, yoklama, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
d = yukle()
Lx, Ly, Tx, Ts, Tr = d["Lx"], d["Ly"], d["Tx"], d["Ts"], d["Tr"]
Uk = ornekler(
    20000,
    np.random.default_rng(76),
    sekil_renk=[0, 1, 2, 3],
    p_kural=0.9,
)[0]
i_ayir = np.arange(1000)
i_test = np.arange(1000, 2000)


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def renk_yoklamasi(F):
    sc = StandardScaler().fit(F[i_ayir])
    clf = LogisticRegression(max_iter=3000, random_state=0)
```

```python
    clf.fit(sc.transform(F[i_ayir]), Tr[i_ayir])
    return clf.score(sc.transform(F[i_test]), Tr[i_test])


sonuc = []
YOK_RENK = {**TUM, "renk": False}
for ad, cfg in (("tam_artirma", TUM), ("renk_bozma_yok", YOK_RENK)):
    enc = egit("simclr", Uk, 0, cfg=cfg, adim=3000)
    Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
    for m in (10, 100, 500):
        sonuc.append(
            (
                ad,
                "sekil_n%d" % m,
                yoklama(Fl[alt(m)], Ly[alt(m)], Ft, Ts),
            )
        )
    sonuc.append((ad, "renk_yoklama", renk_yoklamasi(Ft)))
    for s in sonuc[-4:]:
        print(s[0], s[1], "%.3f" % s[2], flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_kisa_yol.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["artirma", "olcut", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], "%.4f" % s[2]])
```

```term
$ python t10_kisa_yol.py
tam_artirma sekil_n10 0.344
tam_artirma sekil_n100 0.531
tam_artirma sekil_n500 0.679
tam_artirma renk_yoklama 1.000
renk_bozma_yok sekil_n10 0.303
renk_bozma_yok sekil_n100 0.395
renk_bozma_yok sekil_n500 0.462
renk_bozma_yok renk_yoklama 0.997
```

Renk yoklaması iki koşuda da neredeyse mükemmel (`1,000` ve `0,997`): renk bilgisi her iki gösterimde de var. Asıl fark şekil yoklamasında: renk bozma kapalıyken n = 500 doğruluğu `0,679`'dan `0,462`'ye düşüyor. Yani renk, şekil öğrenmesini gölgeliyor. Renk bozma açıkken bile ipucu ortadan kalkmıyor; doygunluk ve parlaklık bozmaları tonu tamamen silmiyor, gri tonlama da yalnızca yüzde yirmi olasılıkla uygulanıyor. Artırma, ipucunu yok etmek yerine onun ağırlığını azaltıyor. Bu deney tek tohumlu ve tek bir kısa yol üzerinde; yine de yönü açık.

Bu deney, artırma tasarımının bir **veri varsayımı** olduğunu gösterir. Renk bozmayı kapatmak, "renk şekil hakkında bilgi taşımaz" varsayımını sessizce kabul etmek demektir. Gerçek bir İHA veri kümesinde bu varsayım, hava koşullarıyla ya da kamera ayarlarıyla kolayca bozulabilir. Bu yüzden artırma seçimini bir hiperparametre gibi değil, bir modelleme kararı gibi ele almak gerekir.

## 73.10 Çok modlu öğrenme ve CLIP

Şimdiye kadar yalnızca görüntülerle çalıştık. Ama dünyada görüntüler çoğu zaman bir dille birlikte gelir: bir fotoğrafın altyazısı, bir uydu görüntüsünün raporu, bir radar kaydının etiketi. Radford ve arkadaşları (2021; genel bilgi) CLIP ile şunu gösterdiler: görüntü ve metin için iki ayrı kodlayıcı, ortak bir gömme uzayında hizalanabilir ve bu hizalama, eğitimde görülmemiş sınıflara **sıfır atışlı** (zero-shot) genelleme yapabilir.

Yapı basittir. Bir görüntü kodlayıcı ve bir metin kodlayıcı, ikisi de birim kürede bitmiş vektörler üretir. Eğitimde bir batch içindeki `N` görüntü–metin çifti için benzerlik matrisi `S = (görüntü gömmeleri)(metin gömmeleri)ᵀ` hesaplanır; `S`'nin köşegeni pozitiftir. Kayıp, hem görüntüden metne hem metinden görüntüye bir InfoNCE kaybının ortalamasıdır: simetrik kontrastif kayıp.

![Şekil 73.9: Mini-CLIP'in yapısı. Görüntü ve metin ayrı kodlayıcılardan geçer, ortak birim küre uzayında hizalanır; sıfır atışlı sınıflandırmada sınıf adlarından üretilen istemlerin gömmeleri, görüntü gömmesiyle karşılaştırılır.](gorseller/b73_clip_sema.png)

Bir uyarı: CLIP'in orijinal eğitiminde kullanılan veri, milyonlarca internet çiftidir ve ağırlıkları bu ortamda indirmek yasaktır. Biz, aynı mekanizmayı küçük ve tamamen sentetik bir veriyle sıfırdan eğittik. Görüntü kodlayıcı, bu bölümdeki konvolüsyonlu gövdedir; metin kodlayıcı ise iki katmanlı küçük bir transformer'dır (Bölüm 69'daki dikkat bloğu). Metin, 16 kelimelik bir sözlükle kelime düzeyinde kodlanır; en fazla beş belirteçlik açıklama, ortalama alınarak tek bir vektöre indirgenir.

### Yinelenen açıklamalar sorunu

Sentetik açıklamaların sayısı sınırlıdır: 4 renk × 4 şekil × 2 boyut × 5 konum, yani 160 farklı açıklama. Bir batch 256 çift içerdiğinde aynı açıklamanın birden çok kez görünmesi kaçınılmazdır. Naif InfoNCE bu iki örneği birbirinin negatifi sayar; oysa aynı açıklamaya sahip iki görüntü anlamca aynıdır. Biz bu sorunu iki yolla karşılaştırdık: **naif** varyantta her yinelenen çift negatif, **maskeli** varyantta aynı açıklamaya sahip bütün çiftler pozitif kabul edilir ve hedef dağılım, bu pozitiflerin üzerine düz bir olasılık olarak yayılır.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t07: mini-CLIP egitimi (sentetik goruntu-metin
ciftleri).

Egitim kumesinde (mavi, ucgen) kombinasyonu HIC yoktur (bilesimsel
genelleme testi icin). Iki varyant:
  naif   : ayni aciklamali ornekler birbirinin negatifi sayilir,
  maskeli: ayni aciklamali ornekler pozitif kabul edilir (yumusak
  hedef).
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from synth73 import KELIMELER, UZUN, aciklama, belirtec, ornekler
from ortak73 import AYG, Enkoder, tekrar

CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
MAVI, UCGEN = 2, 2
izin = {(r, s) for r in range(4) for s in range(4)} - {(MAVI, UCGEN)}
rng = np.random.default_rng(75)
Xp, R, S, B, K = ornekler(20000, rng, izin=izin)
METIN = [aciklama(R[i], B[i], S[i], K[i]) for i in range(len(R))]
TOK = np.array([belirtec(m) for m in METIN])
CID = R * 40 + B * 20 + S * 5 + K  # ayni aciklama <=> ayni kimlik


class GoruntuKod(nn.Module):
    def __init__(self):
        super().__init__()
        self.govde = Enkoder()
        self.cik = nn.Linear(256, 128)

    def forward(self, x):
        return self.cik(self.govde(x))


class MetinKod(nn.Module):
```

```python
    def __init__(self, V, d=128):
        super().__init__()
        self.gom = nn.Embedding(V, d, padding_idx=0)
        self.konum = nn.Parameter(0.02 * torch.randn(1, UZUN, d))
        self.kod = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d, 4, 256, batch_first=True),
            2,
            enable_nested_tensor=False,
        )
        self.cik = nn.Linear(d, 128)

    def forward(self, ids):
        pad = ids == 0
        h = self.kod(
            self.gom(ids) + self.konum, src_key_padding_mask=pad
        )
        keep = (~pad).float().unsqueeze(-1)
        ort = (h * keep).sum(1) / keep.sum(1).clamp(min=1.0)
        return self.cik(ort)


@tekrar()
def egit_clip(maskeli, adim=4000, bs=256, tohum=0):
    torch.manual_seed(tohum)
    gk = GoruntuKod().to(AYG)
    mk = MetinKod(len(KELIMELER)).to(AYG)
    ls = nn.Parameter(
        torch.tensor(float(np.log(1 / 0.07)), device=AYG)
    )
    ps = list(gk.parameters()) + list(mk.parameters()) + [ls]
    opt = torch.optim.Adam(ps, lr=3e-4)
    X = torch.as_tensor(Xp, device=AYG)
    T = torch.as_tensor(TOK, device=AYG)
    C = torch.as_tensor(CID, device=AYG)
    gk.train()
    mk.train()
    for _ in range(adim):
        idx = torch.randint(0, len(X), (bs,), device=AYG)
        zi = F.normalize(gk(X[idx]), dim=1)
        zt = F.normalize(mk(T[idx]), dim=1)
```

```python
        logit = ls.exp().clamp(max=100.0) * (zi @ zt.t())
        if maskeli:
            P = (C[idx][:, None] == C[idx][None, :]).float()
        else:
            P = torch.eye(bs, device=AYG)
        P = P / P.sum(1, keepdim=True)
        kayip = (
            -(P * F.log_softmax(logit, 1)).sum(1).mean() / 2
            - (P * F.log_softmax(logit.t(), 1)).sum(1).mean() / 2
        )
        opt.zero_grad(set_to_none=True)
        kayip.backward()
        opt.step()
    gk.eval()
    mk.eval()
    return gk, mk


if __name__ == "__main__":
    print("kalan benzersiz aciklama:", len(set(METIN)))
    print(
        "egitim cifti:",
        len(METIN),
        " (mavi ucgen yok:",
        not np.any((R == MAVI) & (S == UCGEN)),
        ")",
    )
    for ad, maskeli in (("naif", False), ("maskeli", True)):
        gk, mk = egit_clip(maskeli)
        torch.save(
            {"gk": gk.state_dict(), "mk": mk.state_dict()},
            os.path.join(CK, "clip_%s.pt" % ad),
        )
        print(ad, "kaydedildi", flush=True)
```

Bu eğitim kodunda kritik satır, hedef matrisi `P` hesaplayan satırdır: `maskeli` seçeneği, kimlik eşitliğiyle bir maske üretir. Kaybın yumuşak hedefli biçimi `−Σ P log softmax` olarak yazılır; `P` tek tek kayıtlar olduğunda bu, klasik InfoNCE'ye indirgenir.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t08: mini-CLIP olcumleri.

Sifir atisli sekil siniflandirmasi (istem sablonu etkisi), renk+sekil
bilesimi (goerulmemis mavi ucgen dahil), geri getirme (Recall@k, 500
ornekli galeri), modalite boslugu ve goruntu ozellikleri uzerinde
dogrusal yoklama. Her iki egitim varyanti (naif ve maskeli) olculur.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth73 import KELIMELER, RENK_AD, SEKIL_AD, aciklama, belirtec
from ortak73 import AYG, ozellik, yoklama, yukle
from t07_clip_egit import GoruntuKod, MetinKod

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Tx, Tr, Ts, Tb, Tk = d["Tx"], d["Tr"], d["Ts"], d["Tb"], d["Tk"]
Lx, Ly = d["Lx"], d["Ly"]
MAVI, UCGEN = 2, 2
gorulmemis = (Tr == MAVI) & (Ts == UCGEN)


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def yukle_clip(ad):
    p = torch.load(
        os.path.join(CK, "clip_%s.pt" % ad),
        map_location=AYG,
        weights_only=True,
    )
    gk = GoruntuKod().to(AYG)
```

```python
    mk = MetinKod(len(KELIMELER)).to(AYG)
    gk.load_state_dict(p["gk"])
    mk.load_state_dict(p["mk"])
    return gk.eval(), mk.eval()


def gom_emb(gk, X):
    with torch.no_grad():
        z = gk(torch.as_tensor(X, device=AYG))
    return F.normalize(z, dim=1).cpu().numpy()


def metin_emb(mk, cumleler):
    ids = torch.as_tensor(
        np.array([belirtec(c) for c in cumleler]), device=AYG
    )
    with torch.no_grad():
        z = mk(ids)
    return F.normalize(z, dim=1).cpu().numpy()


def sinif_emb(mk, istemler):
    """Her sinif icin istem gomesi (birim vektor); liste -> (C, d)."""
    return metin_emb(mk, istemler)


def en_yakin(I, T):
    return (I @ T.T).argmax(1)


def olcum(ad):
    gk, mk = yukle_clip(ad)
    satirlar = []
    I = gom_emb(gk, Tx)

    # 1) sekil siniflandirmasi: istem sablonu etkisi
    sablonlar = [
        "{s}",
        "büyük {s}",
        "{s} ortada",
```

```python
        "küçük {s} sol üstte",
    ]
    for sb in sablonlar:
        T = sinif_emb(mk, [sb.format(s=s) for s in SEKIL_AD])
        dog = (en_yakin(I, T) == Ts).mean()
        satirlar.append(("sekil_sablon", sb, dog))

    # 2) bilesimsel genelleme: 16 sinif (renk x sekil)
    sinif_ad = [(r, s) for r in range(4) for s in range(4)]
    T1 = sinif_emb(
        mk, ["%s %s" % (RENK_AD[r], SEKIL_AD[s]) for r, s in sinif_ad]
    )
    T2 = []
    for r, s in sinif_ad:
        ornek = [
            aciklama(r, b, s, k) for b in range(2) for k in range(5)
        ]
        v = metin_emb(mk, ornek).mean(0)
        T2.append(v / np.linalg.norm(v))
    T2 = np.array(T2)
    yc = Tr * 4 + Ts
    for ad2, T in (("renk_sekil", T1), ("tam_cumle_topluluk", T2)):
        p = en_yakin(I, T)
        ok = p == yc
        satirlar.append(
            ("bilesim", ad2 + "_gorulen", ok[~gorulmemis].mean())
        )
        satirlar.append(
            ("bilesim", ad2 + "_gorulmemis", ok[gorulmemis].mean())
        )

    # 3) geri getirme: 500 ornekli galeri
    n = 500
    caps = [aciklama(Tr[i], Tb[i], Ts[i], Tk[i]) for i in range(n)]
    Ig = I[:n]
    Tg = metin_emb(mk, caps)
    Sm = Ig @ Tg.T
    for k in (1, 5):
        i2t = np.mean(
            [
```

```python
                any(
                    caps[j] == caps[i] for j in np.argsort(-Sm[i])[:k]
                )
                for i in range(n)
            ]
        )
        t2i = np.mean(
            [
                any(
                    caps[i] == caps[j]
                    for i in np.argsort(-Sm[:, j])[:k]
                )
                for j in range(n)
            ]
        )
        satirlar.append(
            ("geri_getirme", "gorsel_metin_R@%d" % k, i2t)
        )
        satirlar.append(
            ("geri_getirme", "metin_gorsel_R@%d" % k, t2i)
        )

    # 4) modalite boslugu
    fark = np.linalg.norm(Ig.mean(0) - Tg.mean(0))
    eslesen = np.mean(np.diag(Sm))
    rast = np.mean(
        [
            Sm[i, j]
            for i in range(n)
            for j in range(n)
            if caps[i] != caps[j]
        ]
    )
    satirlar.append(("modalite", "ort_vektor_farki", fark))
    satirlar.append(("modalite", "eslesen_cos", eslesen))
    satirlar.append(("modalite", "rastgele_cos", rast))

    # 5) goruntu ozellikleri uzerinde dogrusal yoklama (sekil)
    Fl, Ft = ozellik(gk.govde, Lx), ozellik(gk.govde, Tx)
    for m in (100, 500):
```

```python
        satirlar.append(
            (
                "yoklama",
                "n%d" % m,
                yoklama(Fl[alt(m)], Ly[alt(m)], Ft, Ts),
            )
        )
    return satirlar, Sm[:4, :4], caps[:4]


if __name__ == "__main__":
    tum = []
    for ad in ("naif", "maskeli"):
        sat, mat, ornek = olcum(ad)
        for s in sat:
            tum.append((ad,) + s[:2] + ("%.4f" % s[2],))
            print(ad, s[0], s[1], "%.4f" % s[2], flush=True)
        if ad == "maskeli":
            os.makedirs(VERI, exist_ok=True)
            with open(
                os.path.join(VERI, "b73_clip_matris.csv"),
                "w",
                newline="",
                encoding="utf-8",
            ) as f:
                w = csv.writer(f)
                w.writerow(["ornek"] + ["%d" % i for i in range(4)])
                for i in range(4):
                    w.writerow(
                        [ornek[i]] + ["%.4f" % v for v in mat[i]]
                    )
            for o in ornek:
                print("ornek:", o, flush=True)
    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b73_clip.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
```

```python
        w = csv.writer(f)
        w.writerow(["varyant", "grup", "olcut", "deger"])
        for r in tum:
            w.writerow(list(r))
    print("gorulmemis test ornegi sayisi:", int(gorulmemis.sum()))
```

Ölçüm betiği beş şeyi ölçer. Birincisi, sıfır atışlı şekil siniflandırmasıdır; burada istemin biçimi, yani **istem şablonu**, sonucu etkiler. İkincisi, bileşimsel genellemedir: 16 sınıflı (renk × şekil) problemde mavi üçgen kombinasyonu eğitimde hiç görülmedi ve test kümesinde görünüyor. Üçüncüsü, geri getirmedir: 500 örnekli bir galeride görüntüden metne ve metinden görüntüye Recall@k. Dördüncüsü, modalite boşluğudur: görüntü ve metin gömmelerinin ortalamalarının ne kadar uzak olduğu. Beşincisi, CLIP'in görüntü özellikleri üzerinde doğrusal yoklamadır.

```term
$ python t07_clip_egit.py
kalan benzersiz aciklama: 150
egitim cifti: 20000  (mavi ucgen yok: True )
naif kaydedildi
maskeli kaydedildi
```

```term
$ python t08_clip_olcum.py
naif sekil_sablon {s} 0.8910
naif sekil_sablon büyük {s} 0.8925
naif sekil_sablon {s} ortada 0.9030
naif sekil_sablon küçük {s} sol üstte 0.8270
naif bilesim renk_sekil_gorulen 0.9803
naif bilesim renk_sekil_gorulmemis 0.5455
naif bilesim tam_cumle_topluluk_gorulen 0.9808
naif bilesim tam_cumle_topluluk_gorulmemis 0.5041
naif geri_getirme gorsel_metin_R@1 0.9660
naif geri_getirme metin_gorsel_R@1 1.0000
naif geri_getirme gorsel_metin_R@5 0.9920
naif geri_getirme metin_gorsel_R@5 1.0000
naif modalite ort_vektor_farki 0.0844
naif modalite eslesen_cos 0.9531
naif modalite rastgele_cos 0.0000
naif yoklama n100 0.9695
naif yoklama n500 0.9805
maskeli sekil_sablon {s} 0.8990
maskeli sekil_sablon büyük {s} 0.8950
maskeli sekil_sablon {s} ortada 0.9130
maskeli sekil_sablon küçük {s} sol üstte 0.8440
maskeli bilesim renk_sekil_gorulen 0.9899
maskeli bilesim renk_sekil_gorulmemis 0.4711
maskeli bilesim tam_cumle_topluluk_gorulen 0.9941
maskeli bilesim tam_cumle_topluluk_gorulmemis 0.4463
maskeli geri_getirme gorsel_metin_R@1 0.9740
maskeli geri_getirme metin_gorsel_R@1 1.0000
maskeli geri_getirme gorsel_metin_R@5 0.9940
maskeli geri_getirme metin_gorsel_R@5 1.0000
maskeli modalite ort_vektor_farki 0.0562
maskeli modalite eslesen_cos 0.9625
maskeli modalite rastgele_cos -0.0027
maskeli yoklama n100 0.9775
maskeli yoklama n500 0.9830
ornek: kırmızı küçük kare sol üstte
ornek: yeşil küçük kare sol üstte
ornek: mavi büyük üçgen sol altta
ornek: yeşil küçük üçgen sol üstte
gorulmemis test ornegi sayisi: 121
```

Sıfır atışlı şekil sınıflandırması, eğitimde görülmemiş bir istem olsa da iyi çalışıyor: maskeli eğitimle `0,899` (istem `{s}`), `0,895` (`büyük {s}`), `0,913` (`{s} ortada`); yalnızca daha uzun ve konum içeren istem (`küçük {s} sol üstte`) `0,844`e düşüyor. Şablon, sonucu belirgin biçimde değiştiriyor. Naif eğitimle sonuçlar benzer (`0,827`-`0,903`).

Bu sonuca ihtiyatla bakmak gerekiyor. Dört şeklin dördü de eğitim açıklamalarında geçiyor; yani bu gerçek anlamda yeni sınıfa sıfır atış değil. Asıl bileşimsel test, mavi üçgenin hiç görülmediği 121 test görüntüsünde yapılıyor: 16 sınıflı doğruluk `0,471` (naif: `0,546`), şans düzeyi `0,0625`. Görülmüş kombinasyonlarda ise `0,990`. Yani model yeni bileşimi, şansın yedi katından fazla doğrulukla çözüyor, ama görülmüş kombinasyonlara göre belirgin bir düşüş var. Dikkat: bu sonuçta naif ve maskeli varyantlar arasında anlamlı bir fark yok; yinelenen açıklamaların zararı bu küçük ve sentetik veride ölçülebilir bir fark yaratmadı. Bu, "maskeli hedef daha iyidir" iddiasını desteklemiyor.

Geri getirmede 500 görüntülük galeride görüntüden metne Recall@1 `0,974`, Recall@5 `0,994`. Metinden görüntüye ise Recall@1 `1,000`; ancak bu oran lehte bir ölçüm: galeride aynı açıklamayı taşıyan yaklaşık üç görüntü olduğu için, doğru açıklamayı taşıyan herhangi bir görüntünün ilk sırada olması yeterli sayılıyor. Modalite boşluğu, eşleşen çiftlerde ortalama kosinüs `0,963` iken rastgele çiftlerde `−0,003`; ortalama vektörlerin farkı `0,056`. Yani iki modalite ayrı bölgelerde toplanıyor (boşluk küçük, ama sıfır değil), ve eşleşme net biçimde ayrışıyor.

Son olarak, CLIP'in görüntü özellikleri üzerinde doğrusal yoklama n = 100'de `0,978`, n = 500'de `0,983`. Bu, SimCLR'ın (`0,846` ve `0,909`) üstünde. Ancak dürüst olmak gerekirse, CLIP'in eğitimi sınıf adlarını içeren açıklamalarla yapıldı; bu saf öz-denetimli bir öğrenme değil, metin üzerinden dolaylı bir denetimdir. Kıyaslamanın adil olması için bu farkı her zaman hatırlamak gerekir.

![Şekil 73.10: Mini-CLIP sonuçları. Solda dört örnek açıklama için benzerlik matrisi (maskeli eğitim); sağda 16 sınıflı bileşim doğruluğu, naif ve maskeli varyantlar, kesikli çizgi şans düzeyi (1/16).](gorseller/b73_clip.png)

## 73.11 Uygulamalar: az etiketli hedef sınıflandırma, sağlamlık ve kopya tespiti

Bütün bu yöntemlerin pratik değeri, az etiketle hedef sınıflandırmaya nasıl yardımcı olduklarındadır. Senaryo şöyle: büyük bir etiketsiz İHA kaydın var, ama bir uzman yalnızca sınıf başına 10 ya da 100 hedefi etiketleyebilir. Seçenekler üçtür: denetimli sıfırdan eğitim, öz-denetimli ön eğitim ardından doğrusal yoklama, ve öz-denetimli ön eğitim ardından ince ayar. 73.2'deki etiket eğrisi bu üç seçeneğin tam karşılaştırmasını verdi. Burada onu iki kısa bulguyla tamamlıyoruz.

Birincisi, **sağlamlık** (robustness). Modeli temiz verilerle eğitip bozulmuş test verisinde ölçmek, Bölüm 66.13'te gördüğümüz dağılım kayması testidir. Bozulmalar üç türdür: Gauss gürültüsü, kontrast azaltma ve bulanıklık. Sınıflandırıcı, temiz verinin n = 100 örneğiyle eğitilir; sonra aynı sınıflandırıcı bozulmuş test verisinde değerlendirilir. Karşılaştırılan yöntemler ham piksel, rastgele ağ ve SimCLR'dır.

```python
# -*- coding: utf-8 -*-
"""Bolum 73 - t09: saglamlik (alan kaymasi) ve gomme tabanli kopya
tespiti.

(a) Siniflandirici temiz egitim verisinin n = 100 / sinif ornegiyle
    egitilir; test kumesi gurultu, kontrast ve bulaniklikla bozulur.
(b) Kopya tespiti: 2000 ornekli galeride her sorgu, ayni resmin
    bozulmus kopyasidir; en yakin komsu dogru mu?
"""

import csv
import os
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from ortak73 import AYG, Enkoder, bozulma, egit, ozellik, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
idx100 = np.concatenate(
    [np.arange(c * 500, c * 500 + 100) for c in range(4)]
)

simclr = Enkoder().to(AYG)
simclr.load_state_dict(
    torch.load(
        os.path.join(CK, "simclr_s0.pt"),
        map_location=AYG,
        weights_only=True,
    )
)
simclr.eval()
rastgele = egit("rastgele", Ux, 0)
ozel = {"piksel": None, "rastgele": rastgele, "simclr": simclr}


def oz(yontem, X):
```

```python
    if yontem == "piksel":
        return X.reshape(len(X), -1)
    return ozellik(ozel[yontem], X)


def sinif_egit(F, y):
    sc = StandardScaler().fit(F)
    clf = LogisticRegression(max_iter=3000, random_state=0)
    clf.fit(sc.transform(F), y)
    return lambda G, yy: clf.score(sc.transform(G), yy)


BOZ = [
    ("temiz", 0.0),
    ("gurultu", 0.1),
    ("gurultu", 0.2),
    ("gurultu", 0.3),
    ("kontrast", 0.3),
    ("kontrast", 0.6),
    ("bulaniklik", 1),
    ("bulaniklik", 2),
]
rng = np.random.default_rng(77)
satirlar = []
for yontem in ("piksel", "rastgele", "simclr"):
    skor = sinif_egit(oz(yontem, Lx[idx100]), Ly[idx100])
    for tur, s in BOZ:
        Xc = bozulma(Tx, tur, s, rng) if tur != "temiz" else Tx
        acc = skor(oz(yontem, Xc), Ts)
        satirlar.append(("saglamlik", yontem, tur, s, acc))
        print(yontem, tur, s, "%.3f" % acc, flush=True)

# Kopya tespiti: sorgu = galeri ornegi + bozulma; en yakin komsu
# (top-1)
kop = []
for yontem in ("piksel", "rastgele", "simclr"):
    G = oz(yontem, Tx)
    G = G / np.linalg.norm(G, axis=1, keepdims=True)
    for tur, s in (("gurultu", 0.2), ("kontrast", 0.5)):
        Q = bozulma(Tx[:500], tur, s, rng)
```

```python
        Qf = oz(yontem, Q)
        Qf = Qf / np.linalg.norm(Qf, axis=1, keepdims=True)
        top1 = (np.argmax(Qf @ G.T, axis=1) == np.arange(500)).mean()
        kop.append((yontem, tur, s, top1))
        print("kopya", yontem, tur, s, "%.3f" % top1, flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_saglamlik.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["grup", "yontem", "tur", "siddet", "dogruluk"])
    for r in satirlar:
        w.writerow([r[0], r[1], r[2], r[3], "%.4f" % r[4]])
    for r in kop:
        w.writerow(["kopya", r[0], r[1], r[2], "%.4f" % r[3]])
```

```term
$ python t09_saglamlik.py
piksel temiz 0.0 0.330
piksel gurultu 0.1 0.314
piksel gurultu 0.2 0.288
piksel gurultu 0.3 0.290
piksel kontrast 0.3 0.325
piksel kontrast 0.6 0.323
piksel bulaniklik 1 0.326
piksel bulaniklik 2 0.328
rastgele temiz 0.0 0.326
rastgele gurultu 0.1 0.280
rastgele gurultu 0.2 0.279
rastgele gurultu 0.3 0.254
rastgele kontrast 0.3 0.316
rastgele kontrast 0.6 0.272
rastgele bulaniklik 1 0.333
rastgele bulaniklik 2 0.336
simclr temiz 0.0 0.846
simclr gurultu 0.1 0.241
simclr gurultu 0.2 0.240
simclr gurultu 0.3 0.240
simclr kontrast 0.3 0.763
simclr kontrast 0.6 0.488
simclr bulaniklik 1 0.670
simclr bulaniklik 2 0.484
kopya piksel gurultu 0.2 1.000
kopya piksel kontrast 0.5 0.822
kopya rastgele gurultu 0.2 0.590
kopya rastgele kontrast 0.5 0.406
kopya simclr gurultu 0.2 0.006
kopya simclr kontrast 0.5 0.942
```

Temiz testte SimCLR yoklaması `0,846` veriyor; ama standart sapması `0,1` olan Gauss gürültüsünde `0,241` ile şans düzeyine iniyor ve piksel tabanının (`0,314`) bile altında kalıyor. Kontrast azaltmada (`0,3`: `0,763`; `0,6`: `0,488`) ve bulanıklıkta (3×3: `0,670`; 5×5: `0,484`) düşüş daha yumuşak. Yani temsil kontrast ve bulanıklığa kısmen sağlam, gürültüye ise son derece kırılgan. Nedeni büyük olasılıkla artırma hattındaki gürültünün `0,03` olmasıdır; test gürültüsü bunun üç katından büyük. Düzeltme yolu, eğitim artırmasına daha güçlü gürültü eklemek ve sağlamlığı ön eğitim hedefinin bir parçası yapmaktır (genel bilgi). Bu sonuç tek tohumla ve sabit bir yoklama ile elde edildi; kesin bir büyüklük değil, bir yön olarak okunmalı.

İkincisi, **kopya tespiti**. Gömme uzayında bir sorguya en yakın komşuyu bulmak, bir arşivde benzer görüntü aramanın ve kopya ya da anomali tespitinin temelidir (Bölüm 71.5'te vektör indekslerini gördük). Burada sorgu, galeri görüntüsünün gürültülü ya da kontrastı azaltılmış bir kopyasıdır; amaç, doğru orijinali ilk sırada bulmaktır. Kopya tespiti, öz-denetimli gösterimin tam olarak eğitildiği türden bir değişmezlik sorusudur: bozulmaya karşı değişmez olmalı, ama içeriği ayırt edebilmeli.

Gürültülü kopya (σ = `0,2`) aramasında piksel kosinüsü sorguların tamamını doğru buluyor (`1,000`), SimCLR ise yalnızca `0,006` buluyor. Gürültü, SimCLR gömmesini tümüyle bozuyor. Kontrast kopyasında tablo tersine dönüyor: SimCLR `0,942`, piksel `0,822`. Yani gösterim kontrast değişimine karşı öğrenilmiş bir değişmezlik taşıyor, gürültüye karşı taşımıyor. Pratik sonuç açık: bir arama sistemi için gömme seçerken, sorguların bozulma türünü eğitim artırmasıyla karşılaştırmak gerekiyor. Piksel kosinüsünün başarısı da abartılmamalı: 2000 görüntülük bu galeride arka plan rengi ve şekil konumu görüntüleri zaten ayırt ediyor; daha homojen bir veri kümesinde bu yöntem aynı sonucu vermez.

### Bu deneylerin sınırı

Bu bölümdeki bütün uygulama ölçümleri sentetik ve küçük ölçeklidir: 32×32 görüntüler, dört sınıf, tek bir artırma seti. Gerçek bir İHA kamerasında sensörün gürültüsü, ortamın ışığı ve hedeflerin ölçeği çok daha değişkendir. Bu sonuçlar bir **yöntem tanıtımıdır**, saha performansı tahmini değildir. Saha için aynı kurgu, kendi sensör verinle ve bağımsız bir test kümesiyle tekrarlanmalıdır. Bölüm 78'de bu tür doğrulamanın savunma sanayiinde nasıl yapılması gerektiğine döneceğiz.

## 73.12 Sınırlar ve maliyet

Öz-denetimli öğrenmenin üç temel sınırı vardır.

**Hesaplama maliyeti.** Kontrastif yöntemler büyük batch ya da büyük negatif kümesi ister; bu da bellek ve süre demektir. Bu bölümde en büyük batch 512 idi; 3000 adımlık bir CPU koşusu (4 iş parçacığı) yaklaşık on dakika sürdü. Ön eğitim koşularının bir kısmı ise önceki oturumda GPU'da yapıldı. Gerçek ölçekte aynı yöntem, binlerce GPU-saati gerektirebilir. Batch'in etkisini ölçtüğümüz 73.4'te adım sayısını sabit tuttuk; ama bu, toplam gördüğü örnek sayısını da değiştirdi. Hesaplamayı kazançtan ayırmak için toplam örnek sayısını sabitlemek gerekir.

**Önyargı.** Gösterim, eğitim verisinin istatistiklerini öğrenir. Bölüm 73.9'daki renk kısa yolu bunun küçük bir örneğidir. Gerçek veride bu önyargı, belirli bir coğrafyanın, bir sensörün ya da bir hava koşulunun izlerini taşır ve görünmez biçimde karar sınırlarını kaydırır. Önyargıyı ölçmek için test kümesini, eğitim kümesinden bilinçli olarak farklı seçmek gerekir.

**Ölçüm hilesi.** Bir öz-denetimli yöntemin başarısı, hangi etiket kümesiyle ve hangi yoklama protokolüyle ölçüldüğüne bağlıdır. Test kümesine bakarak artırma ya da sıcaklık seçersen, sonuç yine de iyimser çıkar. Bu yüzden bu bölümde her seçimi (artırma, sıcaklık, batch) ya ayrı bir ablasyonla raporladık ya da test kümesinden bağımsız bir karar olarak sabitledik. Bölüm 57'deki çok tohum ve istatistiksel anlamlılık disiplini burada da geçerlidir.

Öz-denetimli temsil öğrenmenin ana vaadi, etiketin pahalı olduğu yerde değer üretmesidir. Ama bu vaat, her yöntemin kendi varsayımlarının ve maliyetlerinin ölçülmesiyle gerçekleşir. Bu bölümün asıl kazanımı belki de budur: bir gösterimi övmeden önce, onu neyle, nasıl ve hangi sınırlarla ölçtüğünü sormak.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, Bölüm 5'te tarif ettiğimiz altı adımı izler. Her birinde elle iz sürmen beklenir; programlara başvurmadan sayıları kendin hesapla, sonra bu bölümün betikleriyle karşılaştır.

### Örnek 1 (★): İki pozitif çiftle NT-Xent'in elle hesabı

İki görüntünün her biri iki görünüme sahip. Dört birim vektör var: `a₀ = (1, 0)`, `a₁ = (0, 1)` iki görüntünün birinci görünümleri, `b₀ = (0,8; 0,6)`, `b₁ = (0,6; 0,8)` ikinci görünümleridir. Pozitif çiftler `(a₀, b₀)` ve `(a₁, b₁)`dir. Sıcaklık `τ = 0,5`. NT-Xent kaybının ortalamasını bul.

**Adım 1 — Anla.** Kayıp, her çapa için "doğru eş hangisi" diye soran bir softmax'in negatif log-olabilirliğinin ortalamasıdır. Dört çapa var; her birinin pozitifi, kendi çiftinin karşı tarafındaki vektördür.

**Adım 2 — Örnekle.** `a₀` çapasının pozitifi `b₀`'dır. Negatifler `a₁`, `b₁`'dir. Benzerlikler: `sim(a₀, b₀) = 0,8`, `sim(a₀, b₁) = 0,6`, `sim(a₀, a₁) = 0`.

**Adım 3 — Kaba çöz.** Her çapa için: pozitifin üstel değerini, bütün diğer adayların üstel değerlerinin toplamına böl ve `−log` al. Sonra dört çapanın kaybını ortala.

**Adım 4 — Örüntü.** Dört çapa simetrik: `a₀` ile `a₁`, `b₀` ile `b₁` aynı kaybı verir. Yani iki farklı değer hesaplamak yeter.

**Adım 5 — İyileştir.** Benzerlikleri `τ = 0,5`e bölmek yerine iki ile çarpmak yeterli: `s/τ = 2·sim`. Böylece üstel değerler `e^{1,6}`, `e^{1,2}`, `e^{1,92}` gibi küçük bir tabloya iner.

**Adım 6 — Doğrula.** Aşağıdaki iz tablosu, iki yolla da aynı sonucu verir: elle hesap ve `t01_nt_xent.py`.

| Çapa | Pozitif (s/τ) | Negatifler (s/τ) | Üstel toplam | p₊ | Kayıp |
|---|---|---|---|---|---|
| a₀ | b₀ (1,60) | a₁ (0), b₁ (1,20) | 1 + 4,953 + 3,320 = 9,273 | 0,534 | 0,6271 |
| a₁ | b₁ (1,60) | a₀ (0), b₀ (1,20) | 9,273 | 0,534 | 0,6271 |
| b₀ | a₀ (1,60) | a₁ (1,20), b₁ (1,92) | 4,953 + 3,320 + 6,821 = 15,094 | 0,328 | 1,1143 |
| b₁ | a₁ (1,60) | a₀ (1,20), b₀ (1,92) | 15,094 | 0,328 | 1,1143 |

Ortalama kayıp: `(0,6271 · 2 + 1,1143 · 2) / 4 = 0,8707`. Betik aynı değeri `0,870714` olarak verir. Dikkat et: `b₀` çapası, `b₀` ile `b₁` arasındaki yüksek benzerlik (0,96) yüzünden kendi pozitifinden çok `b₁`'e kayıyor ve kaybı büyüyor. Bu, NT-Xent'in aynı tarafta kalan vektörleri de ayırmaya çalıştığını gösterir.

**Bunu AI'sız yazabilir misin?** Üç pozitif çiftli bir batch için (`a₀, a₁, a₂` ile `b₀, b₁, b₂`) aynı tabloyu, benzerlikleri sen seçerek kur ve kaybı hesapla. Pozitif ile en yakın negatif arasındaki farkın kayba etkisini tartış.

### Örnek 2 (★★): Hizalama ve tekdüzelik, dağılmış ve çökmüş kümede

Dört birim vektör: `u₁ = (1, 0)`, `u₂ = (0, 1)`, `v₁ = (0,8; 0,6)`, `v₂ = (−0,6; 0,8)`. Pozitif çiftler `(u₁, v₁)` ve `(u₂, v₂)`. Hizalamayı ve `t = 2` için tekdüzeliği hesapla. Sonra dört vektörün hepsi `(1, 0)` olsaydı ne olurdu, bunu da yorumla.

**Adım 1 — Anla.** Hizalama, pozitif çiftlerin ortalama kare uzaklığıdır (küçük = iyi). Tekdüzelik, bütün vektör çiftlerinin `exp(−2 d²)` ortalamasının logaritmasıdır (küçük = iyi). İkisi birlikte okunmalıdır.

**Adım 2 — Örnekle.** Pozitif çiftler: `|u₁ − v₁|² = 0,2² + 0,6² = 0,40` ve `|u₂ − v₂|² = 0,6² + 0,2² = 0,40`.

**Adım 3 — Kaba çöz.** Hizalama, iki pozitif uzaklığın ortalamasıdır: `(0,40 + 0,40)/2 = 0,40`. Tekdüzelik için dört noktadan `C(4,2) = 6` ikili almak gerekir.

**Adım 4 — Örüntü.** Altı ikili uzaklık: `u₁v₁ = 0,40`, `u₂v₂ = 0,40`, `u₁u₂ = 2,00`, `u₁v₂ = 3,20`, `v₁u₂ = 0,80`, `v₁v₂ = 2,00`. Yakın çiftler küçük, karşıt çiftler büyük değerler veriyor.

**Adım 5 — İyileştir.** `exp(−2d²)` değerlerini tabloya koy; ortalamanın logaritmasını al. Çökmüş durumda bütün `d²` sıfır olduğundan her terim `1` olur ve tekdüzelik `log 1 = 0` çıkar.

**Adım 6 — Doğrula.** İz tablosu:

| Çift | d² | exp(−2d²) |
|---|---|---|
| u₁v₁ | 0,40 | 0,4493 |
| u₂v₂ | 0,40 | 0,4493 |
| u₁u₂ | 2,00 | 0,0183 |
| v₁v₂ | 2,00 | 0,0183 |
| v₁u₂ | 0,80 | 0,2019 |
| u₁v₂ | 3,20 | 0,0017 |

Toplam `1,1388`, altı ortalaması `0,1898`, logaritması `−1,6617`. Betik aynı değerleri (`hizalama = 0,4000`, `tekdüzelik = −1,6617`) verir. Çökmüş durumda ise hizalama `0,0000` ve tekdüzelik `0,0000`dır: hizalama mükemmel görünür, tekdüzelik ise en kötü değeri verir. Bu, iki ölçütün neden birlikte okunması gerektiğinin en açık örneğidir.

**Bunu AI'sız yazabilir misin?** Dört noktayı kare köşelerine (`(±1, 0)`, `(0, ±1)`) yerleştir. Tekdüzeliği elle hesapla ve sonucu çökmüş durumla karşılaştır. Hangi konfigürasyonda tekdüzelik daha düşük çıkar ve neden?

### Örnek 3 (★★): 3×3 görüntü–metin matrisinde simetrik CLIP kaybı ve sıfır atış

Üç görüntü ve üç metin için kosinüs benzerlik matrisi:

```
S = | 0,9  0,1  0,2 |
    | 0,3  0,7  0,1 |
    | 0,2  0,7  0,6 |
```

Satır görüntü, sütun metindir; köşegen eşleşen çiftlerdir. Sıcaklık `τ = 0,5` ile logit `S / τ`. Görüntüden metne ve metinden görüntüye kayıpların ortalamasını hesapla, simetrik kaybı bul. Sonra her görüntü için sıfır atışlı tahmini (en yüksek benzerlik) yap ve doğru olup olmadığına bak.

**Adım 1 — Anla.** Simetrik kayıp iki çapraz entropinin ortalamasıdır: her satırın (görüntü) doğru metni seçmesi ve her sütunun (metin) doğru görüntüyü seçmesi.

**Adım 2 — Örnekle.** Logit matrisi `2S`dir: `[[1,8, 0,2, 0,4], [0,6, 1,4, 0,2], [0,4, 1,4, 1,2]]`.

**Adım 3 — Kaba çöz.** Her satır için `−log(e^{köşegen} / Σ e^{satır})`; sonra her sütun için aynısı.

**Adım 4 — Örüntü.** Üçüncü satırda köşegenden (`1,2`) daha büyük bir değer (`1,4`, ikinci sütun) var. Yani üçüncü görüntü, kendi metninden çok ikinci metni tercih ediyor. Bu, hem görüntüden metne kaybını hem de sıfır atış tahminini etkileyecek; bunu sayılarla doğrula.

**Adım 5 — İyileştir.** Büyük değerlerin üstel toplamda baskın olduğunu görürsün; kayıplar ancak köşegen en büyükse küçülür. Kaybın kaynağı, yanlış tahmin edilen satırdır.

**Adım 6 — Doğrula.**

| Satır | Logit (3 değer) | Köşegen | Kayıp (görüntü→metin) |
|---|---|---|---|
| 1 | 1,80, 0,20, 0,40 | 1,80 | 0,3705 |
| 2 | 0,60, 1,40, 0,20 | 1,40 | 0,5599 |
| 3 | 0,40, 1,40, 1,20 | 1,20 | 0,9824 |

Görüntüden metne ortalama `0,6376`. Metinden görüntüye (sütunlar): `0,4368`, `0,8334`, `0,5973`, ortalama `0,6225`. Simetrik kayıp `(0,6376 + 0,6225)/2 = 0,6301`. Sıfır atış tahmini, her görüntü için benzerlik matrisinde en büyük değerin sütununu seçmektir. Birinci satırın en büyüğü birinci sütundadır (`0,9`), ikinci satırın en büyüğü ikinci sütundadır (`0,7`), üçüncü satırın en büyüğü ise ikinci sütundadır (`0,7`, doğru sınıf `0,6` ile üçüncü sütunda). Tahminler 1-tabanlı `[1, 2, 2]`dir: üçüncü görüntü bir sıfır atış hatası yapıyor. Betik aynı tahmini (0-tabanlı `[0, 1, 1]`) verir.

**Bunu AI'sız yazabilir misin?** Üçüncü satırı `(0,2, 0,3, 0,9)` yap ve hem simetrik kaybı hem sıfır atış tahminini yeniden hesapla. Kaybın düşmesi, tahminin düzelmesiyle aynı yönde mi?

### Örnek 4 (★★★): Çöken bir eğitimi loglardan teşhis etmek

Bir ekip iki SimSiam koşusu çalıştırıyor. Koşu A stop-gradient kullanıyor, koşu B kullanmıyor. Ekip her 500 adımda projeksiyon çıktısının std ölçütünü ve etiketli kümede k-NN doğruluğunu kaydetmiş. Aşağıdaki tablo, bu bölümün t03 koşusundan alınmış gerçek değerler (yalnızca seçilmiş adımlar):

| Adım | A: std | A: k-NN | B: std | B: k-NN |
|---|---|---|---|---|
| 500 | 0,809 | 0,451 | 0,017 | 0,481 |
| 2000 | 0,878 | 0,388 | 0,007 | 0,484 |
| 6000 | 0,916 | 0,380 | 0,002 | 0,513 |

Soru: hangi koşu çöküyor, çöküş ne zaman başladı ve ekip neyi yanlış okumuş olabilir?

**Adım 1 — Anla.** Kayıp, çökmenin kanıtı değildir: çökmüş bir gösterimde kayıp da düşük olabilir. Bu yüzden gösterimin istatistiklerine (std) ve bilgi içeriğine (k-NN) birlikte bakmak gerekir.

**Adım 2 — Örnekle.** Std ölçütü 1'e yakınsa gösterim boyutları eşit dağılmıştır; sıfıra yaklaşırsa tek bir yöne çökmüştür. k-NN ise etiketli örneklerin ne kadarının gösterimde ayrışabildiğini söyler; şans düzeyi bu problemde `0,25`.

**Adım 3 — Kaba çöz.** İlk kayıtta hangi koşu çökmüş? Hangisinde std zamanla düşüyor? İki koşunun k-NN'i arasında bir fark var mı?

**Adım 4 — Örüntü.** B koşusunda std ilk kayıtta, yani 500. adımda, zaten `0,017`. A'da std `0,81`-`0,92` bandında. k-NN ise A'da `0,38`-`0,45`, B'de `0,48`-`0,51` arasında; yani k-NN, çöken koşuyu daha iyi gösteriyor gibi! Bu bir tuzak. B'de çökme projeksiyon başlığında gerçekleşmiş, kodlayıcı çıktısı bu yüzden kısmen korunmuş. Std ölçütü çökmeyi yakalıyor; k-NN'e tek başına güvenen bir ekip B'yi seçerdi.

**Adım 5 — İyileştir.** Düzeltme, B'de stop-gradient'i geri koymaktır (`ortak73.py` içindeki `simsiam_kayip` fonksiyonunda `durdur=True`; 73.7'de gördük). Ayrıca eğitim boyunca std ölçütünü izleyen, eşiğin altına düşünce uyaran bir kontrol eklemek gerekir. k-NN bu kontrolün yerini tutamaz.

**Adım 6 — Doğrula.** Düzeltilmiş koşuda std'nin `0,9` civarında kaldığını ve k-NN'in korunduğunu gösteren bir kontrol yap. Ardından kayıp eğrisinin tek başına neden yeterli olmadığını bir cümleyle açıkla.

**Bunu AI'sız yazabilir misin?** Bir SimCLR koşusunda aynı tabloyu bekle. Sıcaklık çok küçük seçildiğinde (`τ = 0,05`) hangi ölçütlerin değişmesini beklersin ve neden?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçlarına (kod tamamlayıcılar, sohbet modelleri) başvurmak yasak. Kodu, bu bölümde verilen betikleri kapatarak, kendi başına yaz. Bir yöntemin neden çalıştığını ya da çalışmadığını anlamadan kodu kopyalamak, bu bölümün ölçtüğü şeyin tam tersidir.
:::

### Proje 1 (★★): Sıfırdan SimCLR, doğrusal yoklama ve k-NN paketi

**Amaç.** Bu bölümdeki SimCLR hattını, kitaptaki betiklere bakmadan, kendi kodunla yeniden kur ve ölçüm paketini de senin yazman gereken bir sürüm olarak tamamla.

**Yapılacak.** Sentetik şekil üreticisini (`synth73.py`) ya da kendi üreticini kullan. Etiketsiz bir havuzda SimCLR'ı eğit; ardından sınıf başına 10, 50, 100 ve 500 etiketle doğrusal yoklama ve k-NN ölçümü yap. Üç tohumla çalıştır. Son olarak artırma ablasyonu yap: en az üç artırmayı (kırpma, renk, gri) tek tek kapat ve etkisini tabloya koy.

**Beklenen davranış.** Üç tohumun ortalaması ve sapması ile bir etiket eğrisi; SimCLR'ın etiket az olduğunda rastgele ağın üzerine çıkması; ablasyonda en az bir artırmanın kapatılmasıyla doğrulukta görünür bir düşüş.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Kayıp için `F.cross_entropy` ile maskelenmiş benzerlik matrisi kullan; test ayrımını en başta yap ve test kümesini hiçbir karar için kullanma. Yoklama için özellikleri standartlaştır ve lojistik regresyon çalıştır. Kod yazmadan önce hangi sayıların hangi kümeden geldiğini bir tabloya yaz.

**Başarı kriterleri.**
1. NT-Xent'in vektörleştirilmiş sürümü, döngülü referansla `10⁻⁶` altı farkla eşleşiyor.
2. n = 500 için SimCLR doğrusal yoklaması, rastgele ağdan belirgin biçimde yüksek (fark üç tohum sapmasının en az üç katı).
3. Ablasyon tablosunda her kapatılan artırma için bir sayı ve bir yorum var.
4. Her sonuç üç tohumla raporlanmış; tek tohumlu bir karşılaştırma açıkça işaretlenmiş.

### Proje 2 (★★★): Sentetik görüntü–metin verisinde mini-CLIP

**Amaç.** Kendi üreteçinle ürettiğin görüntü–metin çiftlerinde küçük bir CLIP eğit ve üç şeyi ölç: sıfır atışlı sınıflandırma, bileşimsel genelleme ve çift yönlü geri getirme.

**Yapılacak.** Eğitim kümesinden belirli bir kombinasyonu (ör. "mavi üçgen") tamamen çıkar. Simetrik kontrastif kayıpla eğit. Ardından (a) sınıf adlarından gelen istemlerle sıfır atışlı sınıflandırma yap, (b) eğitimde görülmemiş kombinasyonda doğruluğu ölç, (c) 500 örnekli bir galeride Recall@1 ve Recall@5'i hesapla, (d) üç farklı istem şablonunun sonucunu karşılaştır. Naif ve maskeli hedef arasındaki farkı da göster.

**Beklenen davranış.** Sıfır atışlı doğruluk, şans düzeyinin (1/16) üstünde; görülmemiş kombinasyonda görülmüş olanlardan düşük ama şanstan yüksek; istem şablonu sonucu değiştiriyor; maskeli hedef, aynı açıklamaya sahip örneklerin çatışmasını azaltıyor.

**Önerilen yaklaşım (ipucu).** Metin kodlayıcıyı kelime düzeyinde kur, sabit uzunlukta diziye doldur ve dolgu belirtecini ortalamadan çıkar. Benzerlik matrisi için kosinüs kullan, sıcaklığı öğrenilebilir bir parametre yap ve birim küreye normalleştir. Galeride açıklama dizgisinin eşitliğini başarı ölçütü olarak kullan.

**Başarı kriterleri.**
1. Eğitim kümesinde görülmemiş kombinasyonun test kümesindeki sayısını (ve bu nedenle eğitim-test ayrımını) raporda göster.
2. Sıfır atış ve geri getirme sonuçlarının hepsi şans düzeyiyle birlikte verilmiş.
3. İstem şablonu karşılaştırmasında bir şablonun neden daha iyi olduğu için bir açıklama var; ya da neden fark yok.
4. Modalite boşluğunun büyüklüğü bir sayı olarak raporlanmış ve eşleşen ile rastgele çiftlerin benzerlikleri karşılaştırılmış.

### Ek Alıştırmalar

Aşağıdaki sorular cevapsızdır. Önce kendi cevabını yaz, sonra bölümdeki ilgili kısmı oku.

1. ★ Bir görüntünün iki artırılmış kopyası neden pozitif çift sayılır, ama aynı sınıftan iki farklı görüntü neden (çoğu zaman) negatif sayılır? Bu varsayımın bozulduğu iki durum ver.
2. ★ Sıcaklık `τ`yu `0,01` yaparsan softmax'in gradyanı nereye yoğunlaşır? Bu neden eğitimi kararsız yapabilir?
3. ★★ 4 çift içeren bir batch'te NT-Xent'in rastgele gömmeler için beklenen değeri nedir? `log(2N − 1)` ifadesini türet.
4. ★★ SimSiam'da stop-gradient olmadan kayıp hangi noktada minimuma ulaşır ve bu noktada gösterim neye benzer?
5. ★★ "Doğrusal yoklama neyi ölçer, neyi ölçmez?" Bir gösterimin doğrusal yoklamada düşük, k-NN'de yüksek çıkmasının bir nedenini ver.
6. ★★ Hizalama küçük, tekdüzelik büyük bir gösterim nasıl görünür? Böyle bir gösterimin sınıfları ayırmada neden başarısız olabileceğini açıkla.
7. ★★ Dönüşüm tahmini ön görevinde neden yönlendirilmiş bir veri kümesi gerekir? Bu, öz-denetimli görevlerin genel ilkesi hakkında ne söyler?
8. ★★★ Maskeli görüntü modelinde maskeleme oranını yüzde 75'ten yüzde 15'e çıkarırsan görevin zorluğu ve gösterimin ne yönde değişmesini beklersin?
9. ★★★ Bir CLIP eğitiminde iki açıklama aynı anlamda ama farklı kelimelerle yazılmışsa (ör. "kırmızı daire" ve "daire, kırmızı") ne olur? Bunun sıfır atış tahminini nasıl etkilediğini tartış.
10. ★★★ Kontrastif kayıpta batch boyutu büyüdükçe `log N` tavanı yükselir. Bu neden her zaman daha iyi gösterim anlamına gelmez?
11. ★★★ (Mülakat) "Kontrastif öğrenme neden negatif örnek ister?" sorusuna çökme kavramını kullanarak, üç cümleyle cevap ver.
12. ★★★ (Mülakat) "CLIP sıfır atışlı nasıl sınıflandırır?" sorusunu sınıf adlarından istemler, benzerlik ve arg max kavramlarıyla anlat; sonra bir sınırlılığını söyle.

## Kod Okuma Egzersizi: PyTorch'un çapraz entropisi

Bu bölümde NT-Xent'i `F.cross_entropy` ile hesapladık ve InfoNCE'nin bir çapraz entropi olduğunu söyledik. Bu iddiayı kaynakta kontrol etmek, kendi kaybını güvenle yazmanın ilk adımıdır. Aşağıdaki kesit, kurulu PyTorch 2.6.0+cu124 sürümünün `torch/nn/functional.py` dosyasından birebir alınmıştır (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\nn\functional.py`, satır 3494 civarı). Kesit yalnızca dönüşü veren çağrıyı içerir; fonksiyonun geri kalanı (belge dizgisi ve eski `size_average` yolu) kısaltılmıştır.

```python
    if size_average is not None or reduce is not None:
        reduction = _Reduction.legacy_get_string(size_average, reduce)
    return torch._C._nn.cross_entropy_loss(
        input,
        target,
        weight,
```

**Sorular — cevaplamadan geçme:**

1. `cross_entropy` bir `log_softmax` ile bir `nll_loss` mi çağırıyor, yoksa tek bir C++ çekirdeği mi? Bu kesitte bunu görebiliyor musun? Görmüyorsan bir sonraki adım ne olurdu?
2. `target` argümanı bir sınıf indeksi tensörü ya da olasılık dağılımı olabilir. NT-Xent'te hedef indeksidir; bu, bizim kullandığımız biçimin hangisi olduğunu söylüyor mu?
3. `reduction` varsayılanı `'mean'`dir. NT-Xent'te `2N` çapanın kaybını ortalamak için bu varsayılanı kullandık; bu bizim kayıp tanımımızla tam olarak eşleşiyor mu?
4. `ignore_index` gibi parametreler, maskelenmiş köşegen yerine neden kullanılmadı? Köşegeni `−10⁹` ile doldurmanın bu parametreye göre avantajı ve tehlikesi nedir?
5. `label_smoothing` parametresi, SimCLR'da kullanılan bir çözüm mü? Kaybın hedef dağılımını nasıl değiştirir?
6. Bu kesitte `weight` argümanı yerel değişkenlerde mi tanımlanmış? Kaybın hangi kısmı bunu bir sınıf ağırlığı olarak kullanabilir?

## Bölüm Özeti

- Öz-denetimli öğrenme, etiketi verinin kendisinden üretir. İyi bir temsil değişmezlik, ayrıştırılabilirlik ve aktarılabilirlik ister; bunları etiket olmadan ölçmek için doğrusal yoklama, k-NN ve az etiketle ince ayar kullanılır.
- Her yöntem etiket sayısına göre bir eğriyle raporlanmalıdır. SimCLR, 6000 adım ön eğitimle, doğrusal yoklamada n = 500'de `0,909`, rastgele ağda `0,390` doğruluk verdi. Sıfırdan denetimli eğitim, sınıf başına 10 etiketle `0,378`'de kalırken, SimCLR başlatmalı ince ayar `0,503`e çıktı; sınıf başına 50 etiketten itibaren denetimli eğitim yetişti.
- Eğitim adım sayısı, sonuçları belirleyen bir değişkendir: SimCLR 2000 adımda belirgin biçimde geride kaldı, 6000 adımda ise yerine oturdu.
- Dönüşüm tahmini, girdinin doğal bir yönü yoksa şans üstüne çıkabilir; bu bir öğrenilmiş anlam değildir ve konum ızgarasındaki bir artefakttan gelebilir. Bir ön görevin bilgi taşıdığını kontrol etmek gerekir.
- InfoNCE, bir softmax çapraz entropisidir; karşılıklı bilgi için bir alt sınır verir ve `log N` ile tavanlıdır. Sıcaklık zor negatiflerin ağırlığını belirler; bu veride `τ = 0,05`-`0,1` en iyi sonucu verdi.
- Negatifsiz SimSiam'da stop-gradient olmadan projeksiyon çıktısının std ölçütü `0,002`ye düştü; kodlayıcının k-NN'i ise `0,5` civarında kaldı. Çökme, kayıp eğrisinden ve k-NN'den değil, std ölçütünden görülebiliyor.
- Hizalama ve tekdüzelik birlikte okunmalıdır: rastgele ağ hizalamada iyi, tekdüzelikte kötü; VICReg tekdüzelikte en iyi, ama yoklamada SimCLR'ın çok gerisinde.
- Artırma, pozitif çifti tanımlar. Bu veride kırpma kaldırılınca yoklama arttı, renk ve gri tonlama kaldırılınca düştü; renk bozma kapalıyken şekil yoklaması belirgin biçimde azaldı (kısa yol).
- SimCLR gürültüye karşı kırılgan: σ = 0,1 gürültüde doğruluk şans düzeyine indi. Kontrast değişmezliği ise kısmen öğrenilmiş.
- Mini-CLIP, sentetik görüntü–metin çiftlerinde sıfır atışlı sınıflandırmada `0,84`-`0,91` doğruluk verdi; görülmemiş renk–şekil bileşiminde (121 görüntü) `0,47`, şans `0,06`. Naif ve maskeli hedef arasında bu veride anlamlı fark çıkmadı.

**Sonraki bölümde:** Bölüm 74, Pekiştirmeli Öğrenme. Bu bölümde gösterimi etiketsiz veriden öğrendik; orada ise bir ajan, ortamla etkileşerek ödülden öğrenecek. Bellman denklemini Bölüm 16'da DP olarak gördüğümüz yerden başlayarak Q-learning, DQN ve politika gradyanı yöntemlerine geçeceğiz. Ödülün bir "etiket" olmadığını, ve bir ajanın kendi verisini topladığını göreceğiz; bu fark, öz-denetimli öğrenmenin varsayımlarından ne kadar uzak olduğumuzu gösterecek.

::: mulakat
1. Kontrastif öğrenmede negatif örnekler olmadan kayıp hangi çözüme yakınsar, ve bu çözüm neden kullanışsızdır? Negatiflerin bu çözümü nasıl cezalandırdığını açıkla.
2. InfoNCE kaybını bir softmax çapraz entropisi olarak nasıl yazarsın? Hedef dağılım nedir ve aday sayısı `N` kayıp ile karşılıklı bilgi arasındaki bağı nasıl etkiler?
3. Sıcaklık `τ`yu küçültmek, zor negatiflerin gradyanını nasıl değiştirir? Çok küçük bir `τ` neden kararsızlığa yol açabilir?
4. SimSiam stop-gradient olmadan neden çöker? Stop-gradient'in hedefi sabit bir vektör gibi davranmaya zorlaması bu çöküşü nasıl önler?
5. Bir modelin doğrusal yoklamada düşük, k-NN'de yüksek doğruluk vermesi ne anlama gelir? Bu iki ölçütün neden farklı bilgileri ölçtüğünü açıkla.
6. CLIP sıfır atışlı sınıflandırmada hangi bilgiyi kullanır ve hangi durumda, sınıf adının istemi ile görüntü arasındaki benzerlik yanıltıcı olur?
7. Bir veri kümesinde renk ve sınıf arasında güçlü bir korelasyon varsa, öz-denetimli bir gösterimin renge bağımlı olmadığını nasıl doğrularsın?
8. Öz-denetimli bir gösterimi savunma sanayiinde bir İHA hedef sınıflandırıcısı için kullanmadan önce, hangi bağımsız test ve sağlamlık kontrollerini yapmalısın?
:::
