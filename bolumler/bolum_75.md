%% kisim_no: XVI
%% kisim_ad: ML Mühendisliği & Araştırma
%% kisim_ayrac: evet
%% bolum_no: 75
%% baslik: Verimli Çıkarım & Edge

## Giriş: Eğitilen modeli gerçek cihaza sığdırmak

Bölüm 74'te bir ajanın ödül sinyalinden nasıl öğrendiğini gördük. Bu bölümde sorunun öbür yarısına bakıyoruz: öğrenilmiş bir model, sahada çalışırken ne kadar bellek, ne kadar enerji ve ne kadar süre harcıyor? Eğitim bir kez yapılır ve büyük bir sunucuda saatler sürebilir. Çıkarım (inference) ise her karede, her saniyede, bir İHA'nın ya da bir arabanın içinde tekrarlanır. Model sahada yavaşsa ya da çok yer kaplıyorsa, doğruluğu ne kadar iyi olursa olsun kullanılamaz.

Bu bölüm bir yanıt setidir. Önce çıkarımın maliyetini sayıyoruz: parametre, işlem ve bellek trafiği. Sonra bu maliyeti düşüren dört ana araca bakıyoruz: **kuantizasyon** (quantization, sayıları daha az bitle göstermek), **budama** (pruning, gereksiz ağırlıkları atmak), **bilgi damıtma** (distillation, büyük bir modelin bilgisini küçük bir modele aktarmak) ve **verimli mimariler** (depthwise separable konvolüsyon gibi daha az işlem yapan yapılar). Bu araçların çıkış noktası Bölüm 46'daki TinyML'dir: orada bir mikrodenetleyiciye 8 bitlik bir MLP'nin nasıl sığdığını gördük. Burada aynı fikri daha geniş ölçüte taşıyacağız.

Savunma sanayiinde bu konu doğrudan hayati. Bir İHA'da hedef tespiti uçakta yapılmak zorundadır, çünkü görüntüyü yere yollamak için bant genişliği yoktur (Bölüm 46'da bu gerekçeyi görmüştük). Uçağın işlemcisi ise sınırlı güç ve ısı bütçesi ile çalışır. Bu yüzden "doğruluk yüzde kaç" sorusu tek başına yetmez; "bu doğruluk, bu gecikmede ve bu enerjide" sorusunu birlikte sormak gerekir. Mert'in EV Dashboard projesi STM32'den gelen sensör verisini taşıyor. Orada ham sayılar yeterliyse, bir sinir ağında aynı sorunun karşılığı modelin hangi bitlerle ve hangi işlemlerle çalıştığıdır.

::: not
Bu bölümdeki her sayı, bir betiğin çıktısıdır. Betikler tam olarak bu bölümde yer alıyor ve sabit tohumlarla (0, 1, 2) yeniden çalıştırılabilir. Ölçüm sayılarının bir kısmı, paylaşımlı bir bilgisayarda ölçüldüğü için koşudan koşuya değişir. Bu yüzden bu bölümde zamanlama sayılarını her zaman "bu koşuda" bağlamıyla veriyoruz ve kesin değer yerine oran ve sıralamaya dikkat etmeni istiyoruz.
:::

## 75.1 Çıkarım maliyet modeli: parametre, işlem, bellek

Bir modelin çıkarım maliyetini üç sayıyla düşünebiliriz. **Parametre sayısı** `P`, modelin belleğe sığması gereken ağırlık miktarını verir. **İşlem sayısı**, genellikle çarpma-toplama (MAC, multiply-accumulate) cinsinden ölçülür; bir MAC, bir çarpma ve bir toplamadan oluşur ve modern donanımda tek bir birim olarak ele alınır. **Bellek trafiği**, işlemler sırasında ağırlıkların ve aktivasyonların bellek ile işlemci arasında kaç bayt taşındığıdır.

Tam bağlı bir katmanı ele alalım. `m` girdi ve `n` çıktı olsun. Ağırlık matrisi `m × n` elemanlıdır ve bir MAC `m · n` tanedir. Batch boyutu `B` olduğunda işlem sayısı `B · m · n` olur, ama ağırlıklar yalnızca bir kez okunur. Bu fark kritik. Batch büyüdükçe her ağırlık okunup birçok örnek için kullanılır; batch 1 olduğunda ise her ağırlık tek bir çarpım için bellekten çekilir.

Bu düşünceyi tek bir oranda toplayabiliriz: **aritmetik yoğunluk** (arithmetic intensity), yani okunan her bayt başına yapılan FLOP sayısı. Bölüm 65'te PyTorch'un profiler çıktısında hangi işlemlerin bellek bağlı, hangilerinin hesap bağlı olduğunu gözlemlemiştik; burada bu ayrımı sayıya dökeceğiz.

Tablo 75.1, tam bağlı 2048 × 2048 bir katmanın batch boyutuna göre aritmetik yoğunluğunu gösterir. Ağırlıklar fp32 (4 bayt) varsayılmıştır.

| Batch B | FLOP | Bayt (ağırlık + girdi + çıktı) | Aritmetik yoğunluk (FLOP/bayt) |
|---|---|---|---|
| 1 | 8,39 · 10⁶ | 16,8 · 10⁶ | 0,50 |
| 16 | 134 · 10⁶ | 17,0 · 10⁶ | 7,88 |
| 256 | 2,15 · 10⁹ | 21,0 · 10⁶ | 102,4 |

Tablodaki FLOP değerleri `2 · B · m · n` ile hesaplandı (bir MAC iki FLOP sayılır). Batch 1'de yoğunluk yaklaşık 0,5'tir: her okunan baytta yarım işlem. Batch 256'da ise yoğunluk 102'ye çıkar. Hangisinin doğru olduğunu anlamak için bir donanım tepesi ve bir bellek bandı bilmek gerekir.

Bu iki sayıyı birleştiren modele **roofline** denir. Bir donanımın performansı, aritmetik yoğunluğa göre iki sınırın altında kalır: düz bir hesap tavanı (tepe FLOP/s) ve eğik bir bellek tavanı (bant genişliği × yoğunluk). Eğimli kısımda işlem bellek sınırlıdır; yatay kısımda hesap sınırlıdır. Ayrım noktası `tepe / bant` oranıdır. Bu oranın üstündeki katmanları hızlandırmak için daha hızlı bir çekirdek gerekir; altındakiler için ise bellekten daha az bayt okumak gerekir.

::: ipucu
Batch 1 çıkarımında çoğu katman bellek sınırlıdır. Bu yüzden edge cihazda batch'i büyütmek çoğu zaman mümkün değildir (her kare hemen işlenmelidir), ama ağırlık baytlarını küçültmek (kuantizasyon) doğrudan kazanç sağlar. Sunucuda ise batch büyüdükçe hesap tavanına yaklaşılır ve kuantizasyon yine de bellek kazancı verir.
:::

Buradaki bir terim karışıklığına dikkat et. "Gecikme" (latency), tek bir girdinin ne kadar sürede sonuçlandığıdır. "Verim" (throughput), birim zamanda kaç girdi işlendiğidir. Batch 1 gecikmeyi, büyük batch ise verimi iyileştirir; ikisi her zaman aynı yönde değişmez. Edge'de genellikle gecikme önemlidir, çünkü karar bir kare içinde verilmelidir.

## 75.2 Ölçüm disiplini ve roofline'ı ölçmek

Çıkarım hızını ölçmek kolay görünür, ama yanlış yapılması çok kolaydır. İlk çalıştırma, önbellek ısınması, işletim sisteminin araya girmesi ve tek bir ölçümün gürültüsü, sonucu kolayca bozar. Bu yüzden üç kuralı alışkanlık hâline getir:

1. **Isınma (warm-up):** Ölçümden önce birkaç tur çalıştır. İlk turlar önbellek ve bellek ayırma nedeniyle yavaştır.
2. **Çok tekrar:** Tek bir ölçüm yerine yüzlerce ölçüm al. Her ölçüm için `time.perf_counter()` kullan; `time.time()` çözünürlüğü küçük süreler için yetmez.
3. **Medyan ve p95:** Ortalama, birkaç yavaş ölçümle kolayca şişer. Medyan tipik davranışı, p95 ise kuyruk gecikmeyi (en kötü %5'i) verir. Gerçek bir sistemde kuyruk, deadline'ı kaçıran kareyi belirler.

Bu üç kuralı tek bir yardımcı fonksiyonda topluyoruz. Aşağıdaki deney ortamı, bölümün geri kalanındaki tüm betikler için ortaktır. Veri olarak sklearn'in `load_digits` kümesini kullanıyoruz: 1797 adet 8 × 8 piksel el yazısı rakam. Küçük ve hızlıdır; ama sahte bir veri değildir, gerçek bir sınıflandırma problemidir. Eğitim ve test ayrımı stratifiedir, test oranı %30'dur. Her deney üç tohumla (0, 1, 2) tekrarlanır ve sonuç ortalama ± sapma olarak verilir.

Ortak modülün ilk kısmı veri ve modeli hazırlar. Model, 64 girdi, iki gizli katman ve 10 çıktıdan oluşan bir MLP'dir. `mlp_t` fonksiyonu, ağırlık başlatmasını tohuma bağlar; bu olmadan aynı kodu iki kez çalıştırmak farklı sonuç verir. Bunu deneme sırasında kendi gözlemimizle fark ettik: tohumsuz çalıştırmalarda doğruluk birkaç binde bir oynuyordu. Bu nedenle bölümdeki her model tohumla kurulur.

```python
# -*- coding: utf-8 -*-
"""Bolum 75 ortak yardimcilari: veri, MLP, egitim, maske, sahte
kuantizasyon.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

torch.set_num_threads(4)
TOHUMLAR = [0, 1, 2]


def veri(tohum=0):
    X, y = load_digits(return_X_y=True)
    X = (X / 16.0).astype(np.float32)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.3, random_state=tohum, stratify=y
    )
    return (
        torch.tensor(Xtr),
        torch.tensor(ytr),
        torch.tensor(Xte),
        torch.tensor(yte),
    )
```

Eğitim fonksiyonu, Adam optimizasyonunu ve isteğe bağlı budama maskesini uygular. Maske, budanmış ağırlıkları her adımdan sonra sıfırda tutar; bunu budama bölümünde kullanacağız.

```python
def mlp(gizli=(256, 128)):
    katmanlar, giris = [], 64
    for g in gizli:
        katmanlar += [nn.Linear(giris, g), nn.ReLU()]
        giris = g
    katmanlar.append(nn.Linear(giris, 10))
    return nn.Sequential(*katmanlar)


def mlp_t(tohum, gizli=(256, 128)):
    """Agirliklari tohuma gore kurulan MLP (tekrarlanabilirlik icin).
    """
    torch.manual_seed(tohum)
    return mlp(gizli)


def egit(model, X, y, epoch=60, lr=1e-3, tohum=0, maskeler=None):
    torch.manual_seed(tohum)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(X)
    for _ in range(epoch):
        perm = torch.randperm(n)
        for i in range(0, n, 64):
            idx = perm[i : i + 64]
            kayip = F.cross_entropy(model(X[idx]), y[idx])
            opt.zero_grad()
            kayip.backward()
            opt.step()
            if maskeler is not None:
                uygula_maske(model, maskeler)
    return model


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        return (model(X).argmax(1) == y).float().mean().item()


def uygula_maske(model, maskeler):
    """maskeler: {katman_indeksi: 0/1 tensoru}; agirlikta sifirlar."""
    with torch.no_grad():
        for idx, m in maskeler.items():
            model[idx].weight.mul_(m)
```

Şimdi kuantizasyon için gereken yardımcılar geliyor. `simetrik_olcek` ölçeği `max|w| / (2^(b−1) − 1)` ile hesaplar; `qdq` (quantize-dequantize) değeri önce tam sayı ızgarasına yuvarlar, sonra geri çarpar. `SahteKuantFn` ise eğitim sırasında kullanılacak düz geçiş tahmincisidir (STE); bu, 75.3'te açıklanacak.

```python
def simetrik_olcek(w, bits, kanal=False):
    lv = 2 ** (bits - 1) - 1
    if kanal:
        mx = w.abs().amax(dim=1, keepdim=True)
    else:
        mx = w.abs().max()
    return mx.clamp_min(1e-8) / lv


def qdq(x, s, bits):
    """Simetrik kuantize et ve geri ac: round(x/s) kirp, sonra s ile
    carp.
    """
    lv = 2 ** (bits - 1) - 1
    return torch.clamp(torch.round(x / s), -lv, lv) * s


class SahteKuantFn(torch.autograd.Function):
    """Ileri: qdq. Geri: duz gecis (STE), asiri degerde sifir."""

    @staticmethod
    def forward(ctx, x, s, bits):
        lv = 2 ** (bits - 1) - 1
        ctx.save_for_backward(x)
        ctx.s, ctx.lv = s, lv
        return torch.clamp(torch.round(x / s), -lv, lv) * s

    @staticmethod
    def backward(ctx, g):
        (x,) = ctx.saved_tensors
        maske = (x.abs() <= ctx.s * ctx.lv).to(g.dtype)
        return g * maske, None, None
```

Son fonksiyon, ölçüm disiplinimizi uygular: önce `isinma` tur, sonra `n` ölçüm alır ve medyanı ile p95'i döndürür.

```python
def zamanla(f, n=300, isinma=30):
    """Olcum disiplini: isinma, n olcum; medyan ve p95 (ms).
    """
    import time

    for _ in range(isinma):
        f()
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        f()
        t.append((time.perf_counter() - t0) * 1e3)
    t = np.array(t)
    return float(np.median(t)), float(np.percentile(t, 95))
```

Roofline'ı ölçmek için iki tavana ihtiyacımız var: tepe FLOP/s ve bellek bant genişliği. Tepe, büyük bir matris çarpımı ile yaklaşık olarak ölçülür; bant genişliği ise büyük bir belleğin kopyalanmasıyla. Bu iki ölçüm kabadır ve açıkça belirtilmelidir: tepe, bir donanımın gerçek tepe değeri değildir, yalnızca bu betiğin ulaşabildiği değerdir. Aşağıdaki betik, bu tavanlara göre her batch için katmanın ölçülen performansını da kaydeder.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: roofline olcumu (tepe, bant, katman
aritmetik yogunlugu) ve dinamik int8 ile fp32 gecikme karsilastirmasi.
"""

import copy
import csv
import os
import time
import numpy as np
import torch
import torch.nn as nn
from b75_ortak import mlp, zamanla

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
```

Bu betik, roofline şeklini ve gecikme karşılaştırmasını üretir. İkinci bölümde, dinamik int8 kuantizasyonun gecikmeye etkisini de ölçer; bunu 75.3'te yeniden göreceğiz.

```python
def tepe_flops():
    """Buyuk matris carpimiyla ulasilan en yuksek GFLOP/s (yaklasik
    tepe).
    """
    a = torch.randn(1024, 1024)
    b = torch.randn(1024, 1024)
    med, _ = zamanla(lambda: a @ b, n=20, isinma=5)
    return 2 * 1024**3 / (med * 1e-3) / 1e9


def bellek_bandi():
    """Buyuk bir kopyalama: okuma + yazma baytlari / sure (GB/s)."""
    x = torch.randn(64 * 1024 * 1024 // 4)  # 64 MB float32
    med, _ = zamanla(lambda: x.clone(), n=20, isinma=5)
    return 2 * x.numel() * 4 / (med * 1e-3) / 1e9
```

```python
def roofline(tepe, bant):
    """Her girdi boyu icin 2048x2048 Linear katmani; AI ve olculen
    GFLOP/s.
    """
    n = 2048
    W = torch.randn(n, n)
    satir = []
    for B in [1, 4, 16, 64, 256, 1024]:
        x = torch.randn(B, n)
        flops = 2.0 * B * n * n
        bayt = 4.0 * (
            n * n + 2 * B * n
        )  # agirlik + girdi + cikti (fp32)
        ai = flops / bayt
        med, _ = zamanla(lambda: x @ W.T, n=60, isinma=10)
        gf = flops / (med * 1e-3) / 1e9
        sinir = min(tepe, bant * ai)
        satir.append(
            dict(
                B=B,
                ai=round(ai, 3),
                gflops=round(gf, 2),
                sinir=round(sinir, 2),
                sure_ms=round(med, 4),
                sinir_turu="bellek" if bant * ai < tepe else "hesap",
            )
        )
        print(
            "B=%-5d AI=%7.3f FLOP/bayt  olculen=%8.2f GFLOP/s  "
            "tavan=%8.2f (%s)"
            % (B, ai, gf, sinir, satir[-1]["sinir_turu"])
        )
    return satir
```

```python
def dinamik_gecikme():
    """2048x2048 MLP: fp32 ve PyTorch dinamik int8 (Linear icin)."""
    torch.manual_seed(0)
    fp = mlp(gizli=(2048, 2048)).eval()
    q = torch.ao.quantization.quantize_dynamic(
        copy.deepcopy(fp), {nn.Linear}, dtype=torch.qint8
    ).eval()
    satir = []
    for B in [1, 32]:
        x = torch.randn(B, 64)
        for ad, m in [("fp32", fp), ("dinamik_int8", q)]:
            with torch.no_grad():
                med, p95 = zamanla(lambda: m(x), n=300, isinma=30)
            satir.append(
                dict(
                    model=ad,
                    B=B,
                    medyan_ms=round(med, 4),
                    p95_ms=round(p95, 4),
                )
            )
            print(
                "%-13s B=%-3d medyan=%.4f ms  p95=%.4f ms"
                % (ad, B, med, p95)
            )
    return satir
```

```python
def yaz(ad, satirlar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yol)


if __name__ == "__main__":
    torch.set_num_threads(4)
    tepe = tepe_flops()
    bant = bellek_bandi()
    print("tepe (olculen, yaklasik): %.1f GFLOP/s" % tepe)
    print("bellek bant genisligi (olculen, kopya): %.1f GB/s" % bant)
    yaz("b75_roofline.csv", roofline(tepe, bant))
    yaz("b75_dinamik_gecikme.csv", dinamik_gecikme())
```

Betiği çalıştırdığında ilk iki satır tepe ve bant değerlerini verir. Bu değerler bu koşunun ölçümüdür ve bir sonraki koşuda değişebilir.

```term
$ python b75_olcum.py
tepe (olculen, yaklasik): 178.8 GFLOP/s
bellek bant genisligi (olculen, kopya): 25.1 GB/s
```

Geri kalan satırlar, her batch için ölçümü ve dinamik int8 karşılaştırmasını içerir. Bunları, CSV dosyalarını okuyup tablo basan `b75_goster.py` ile görüyoruz. Bu betik yeniden ölçüm yapmaz; yalnızca son koşunun CSV'lerini biçimlendirir.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: olcum CSV'lerini tablo olarak basar (yeniden olcmez).

Kullanim: python b75_goster.py olcum | mimari
"""
import csv
import sys

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"


def oku(ad):
    with open(VERI + ad, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def olcum():
    print("B     AI (FLOP/bayt)  olculen GFLOP/s  tavan  sinir")
    for r in oku("b75_roofline.csv"):
        print("%-5s %12s %15s %9s  %s" % (
            r["B"], r["ai"], r["gflops"], r["sinir"],
            r["sinir_turu"]))
    print("")
    print("model          B   medyan (ms)  p95 (ms)")
    for r in oku("b75_dinamik_gecikme.csv"):
        print("%-14s %-3s %11s %9s" % (
            r["model"], r["B"], r["medyan_ms"], r["p95_ms"]))


def mimari():
    print("model                 parametre        MAC  medyan  p95")
    for r in oku("b75_mimari.csv"):
        print("%-20s %10s %12s %7s %7s" % (
            r["model"], r["parametre"], r["mac"],
            r["medyan_ms"], r["p95_ms"]))


if __name__ == "__main__":
    {"olcum": olcum, "mimari": mimari}[sys.argv[1]]()
```

```term
$ python b75_goster.py olcum
B     AI (FLOP/bayt)  olculen GFLOP/s  tavan  sinir
1              0.5           12.12     12.54  bellek
4            1.992            39.8     50.01  bellek
16           7.877           97.14    178.75  hesap
64          30.118          187.58    178.75  hesap
256          102.4          217.05    178.75  hesap
1024         256.0           216.9    178.75  hesap

model          B   medyan (ms)  p95 (ms)
fp32           1        0.7197    1.4847
dinamik_int8   1        0.3735      0.61
fp32           32       2.3002     3.647
dinamik_int8   32       1.0812    1.6885
```

Tablo, roofline'ın nasıl okunacağını gösterir. Batch 1 satırında ölçülen 12,1 GFLOP/s, bellek tavanı olan 12,5 GFLOP/s'e çok yakındır: bu katman bellek sınırlıdır. Batch 16'da ölçülen 97 GFLOP/s, tavanın (179 GFLOP/s) hâlâ altındadır; batch 64 ve üzerinde ölçümler tepe tahminini aşar. Bunun nedeni tepe ölçümümüzün kaba olmasıdır: 1024 × 1024 bir matris çarpımını tekrarlayarak ölçtük. Daha büyük bir çekirdek ve daha çok tekrarla tepe daha doğru ölçülür. Bu da ölçümün bir sınırıdır ve ölçümü yorumlarken unutulmamalıdır.



Şekil 75.1 aynı veriyi roofline olarak çizer: yatay eksende aritmetik yoğunluk, dikey eksende ölçülen GFLOP/s.

![Şekil 75.1: Roofline: ölçülen tavanlar ve 2048 × 2048 Linear katmanın batch'e göre ölçümleri](gorseller/b75_roofline.png)

Şekilde sol taraftaki eğimli çizgi bellek tavanıdır, sağdaki yatay çizgi hesap tavanıdır. Batch 1 ve 4 noktaları eğimli kısımdadır; yani bu katmanlar bellekten bayt okumakla sınırlıdır. Bu nedenle edge'de kuantizasyon gibi bayt azaltan yöntemler, tepe FLOP/s'i artırmaktan daha çok kazandırır.

Gecikme ölçümü için dinamik int8 kuantizasyon örneği de ayrıca ölçüldü. Aynı 2048 × 2048 MLP'nin fp32 ve PyTorch'un dinamik int8 sürümü batch 1 ve 32 için karşılaştırıldı.

Bu koşuda dinamik int8, batch 1'de fp32'nin yaklaşık yarısı kadar sürdü. Aynı betiğin önceki koşusunda oran yaklaşık 1,5 kattı. Bu fark, sayının kendisinin değil, ölçümün gürültülü olduğunun işaretidir: yorumlarken kesin değer değil, yön ve büyüklük mertebesi kullanılmalıdır.

Bu bölümde ölçülen tüm sonuçları tek bir yerde özetlemek için aşağıdaki betik CSV dosyalarını okur ve ortalama ± sapma üretir. Diğer bölümlerdeki tablolar bu çıktıdan türetilmiştir.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: CSV'lerden ozet tablolar (ortalama +- sapma, 3 tohum)."""
import csv
import statistics as st

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"


def oku(ad):
    with open(VERI + ad, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ozet(satirlar, anahtar, alan):
    for ad in dict.fromkeys(r[anahtar] for r in satirlar):
        d = [float(r[alan]) for r in satirlar if r[anahtar] == ad]
        print("%-24s %.4f +- %.4f  (n=%d)"
              % (ad, st.mean(d), st.pstdev(d), len(d)))


if __name__ == "__main__":
    print("== Damitma (test dogrulugu) ==")
    ozet(oku("b75_damitma.csv"), "yontem", "dogruluk")
    print("== Seyreklik (budama sonrasi / ince ayarli) ==")
    s = oku("b75_seyreklik.csv")
    for o in dict.fromkeys(r["oran"] for r in s):
        b = [float(r["budamasiz"]) for r in s if r["oran"] == o]
        i = [float(r["ince_ayar"]) for r in s if r["oran"] == o]
        print("oran %-5s budamasiz %.4f+-%.4f ince %.4f+-%.4f" % (
            o, st.mean(b), st.pstdev(b), st.mean(i), st.pstdev(i)))
```

```term
$ python b75_ozet.py
== Damitma (test dogrulugu) ==
ogretmen_512_512         0.9759 +- 0.0030  (n=3)
ogrenci_sifirdan         0.9611 +- 0.0030  (n=3)
ogrenci_damitma_T2       0.9549 +- 0.0017  (n=3)
ogrenci_damitma_T4       0.9537 +- 0.0030  (n=3)
ogrenci_damitma_T8       0.9556 +- 0.0015  (n=3)
== Seyreklik (budama sonrasi / ince ayarli) ==
oran 0.0   budamasiz 0.9728+-0.0009 ince 0.9728+-0.0009
oran 0.5   budamasiz 0.9605+-0.0061 ince 0.9704+-0.0000
oran 0.8   budamasiz 0.8204+-0.0436 ince 0.9728+-0.0023
oran 0.9   budamasiz 0.5179+-0.0319 ince 0.9642+-0.0083
oran 0.95  budamasiz 0.1315+-0.0250 ince 0.8926+-0.0393
oran 0.98  budamasiz 0.1086+-0.0122 ince 0.5124+-0.0748
```

## 75.3 Kuantizasyon: sayıları küçültmek

Bir ağırlık 32 bitlik kayan nokta (fp32) ile tutulduğunda 4 bayt yer tutar. Aynı ağırlığı 8 bitlik tam sayı (int8) ile tutarsak 1 bayt yeter. Bölüm 1'de kayan noktanın işaret, mantis ve üs parçalarından oluştuğunu gördük. Kuantizasyonun fikri, bu esnek gösterimi sabit bir tam sayı ızgarasıyla değiştirmektir. Bir `s` ölçeği seçilir ve her değer `q = round(x / s)` ile bir tam sayıya dönüştürülür. Geri dönüşte `x̂ = s · q` kullanılır. Aradaki fark, yuvarlama hatasıdır.

Simetrik int8 ızgarasında `q` değerleri `−127` ile `127` arasındadır ve sıfır tam olarak temsil edilir. Asimetrik ızgarada bir sıfır noktası (`z`) eklenir ve değer aralığı `[min, max]` tam olarak kapsanır. Simetrik ölçek `s = max|x| / 127` ile bulunur; asimetrik ölçek `s = (max − min) / 255` ile. Hangisinin daha iyi olduğu, değerlerin dağılımına bağlıdır: değerler yalnızca pozitif ya da bir tarafa yığılmışsa simetrik ızgara, yarısını boşa harcar.

Ölçeğin nereden alındığı da önemlidir. **Tensör başına** (per-tensor) ölçekte bir tensördeki bütün değerler tek bir `s` ile kuantize edilir. **Kanal başına** (per-channel) ölçekte her çıkış kanalının kendi `s`'si vardır. Kanal başına ölçek, kanalların büyüklükleri farklıysa çok daha az hata yapar; bunu aşağıdaki deneyde ölçeceğiz.

Bir aktivasyonun ölçeğini nasıl bulacağımız ise kalibrasyon sorusudur. Model eğitim sonrasında donmuş iken birkaç yüz örnekle ileri geçiş yapılır, her katmanın girdisinin değerleri toplanır ve ölçek bu değerlerden çıkarılır. Bu yönteme **sonradan kuantizasyon** (PTQ, post-training quantization) denir: model yeniden eğitilmez.

**Aykırı değerler** burada devreye girer. Bir katmanın girdisinde tek bir çok büyük değer varsa, maksimum (max) kalibrasyonu ölçeği o değere göre büyütür ve diğer bütün değerler birkaç tam sayı basamağına sıkışır. Yüzdelik kalibrasyonda (örneğin %99,9) bu tek değer dikkate alınmaz ve ölçek daha küçük olur; ama o tek değer kırpılır. Hangisinin daha iyi olduğu, aykırı değerin önemine bağlıdır. Aşağıdaki deneyde bunu kasıtlı bir aykırı değerle ölçeceğiz.

Eğitim sırasında kuantizasyonu hesaba katmak için **kuantizasyon farkındalıklı eğitim** (QAT, quantization-aware training) kullanılır. İleri geçişte ağırlık ve aktivasyonlar kuantize edilir (sahte kuantizasyon, fake quantization), ama geri yayılımda yuvarlama işlemi türevlenebilir değildir: `round` fonksiyonunun türevi neredeyse her yerde sıfırdır. Bunu çözmek için **düz geçiş tahmincisi** (STE, straight-through estimator) kullanılır: geri yayılımda yuvarlamayı yokmuş gibi davranır ve gradyanı olduğu gibi geçirir. Ölçü aralığının dışına düşen değerler için gradyan sıfırlanır, çünkü ızgaranın dışındaki değer kırpılmıştır.

Bu bölümde kuantizasyon için beş yöntem karşılaştıracağız:

1. fp32 (referans),
2. PTQ, kanal başına ağırlık ölçeği (aktivasyon fp32),
3. PTQ, tensör başına ve kanal başına ağırlık, aktivasyonlar 8 bit, max ve yüzdelik kalibrasyon,
4. QAT, aynı ızgara ile eğitim sırasında sahte kuantizasyon,
5. PyTorch'un kendi dinamik int8 yolu (`torch.ao.quantization.quantize_dynamic`), gerçek tam sayı işlemleriyle.

Deney, 75.2'deki `b75_ortak.py` modülünü kullanır. Kuantizasyon için bir MLP'yi eğitip tüm bu yöntemleri aynı test kümesinde ölçen betik aşağıda. Betik, PTQ ve QAT yardımcılarını da içerir. `girdi_olcekleri` fonksiyonu, bir katmanın girdisi için max ya da yüzdelik ölçeği, bit genişliğine göre hesaplar. Bu ayrıntı önemlidir: 4 bitlik aktivasyon için ölçek 127 yerine 7 ile bölünmelidir. İlk denememizde bu hatayı yaptık ve sonuçlar mantıksız göründü; düzeltince tutarlı hale geldiler.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: PTQ, QAT, PyTorch dinamik int8 (3 tohum).
"""

import copy, io, os, csv, time, statistics as st
import numpy as np
import torch
import torch.nn as nn
from b75_ortak import (
    veri,
    mlp_t,
    egit,
    dogruluk,
    simetrik_olcek,
    qdq,
    SahteKuantFn,
    TOHUMLAR,
)

CIKTI = "D:/Mevcut Projeler/Kitap/engine/veri/b75_bit_dogruluk.csv"
```

```python
class ActQ(nn.Module):
    """Girdi aktivasyonunu sabit (kalibre) olcekle kuantize eder.
    """

    def __init__(self, s, bits):
        super().__init__()
        self.register_buffer("s", s)
        self.bits = bits

    def forward(self, x):
        return qdq(x, self.s, self.bits)
```

Betiğin başındaki içe aktarmalar ve `ActQ` sınıfı, kuantizasyonu modele iki biçimde bağlar. `ActQ` PTQ'da bir katmanın önüne eklenir ve girdiyi sabit ölçekle kuantize eder. `QATLinear` eğitimde kullanılır: ağırlığı her ileri geçişte kanal başına ölçekle sahte kuantize eder ve STE ile geri yayılım yapar.

```python
class QATLinear(nn.Module):
    """Egitim sirasinda sahte kuantizasyon: agirlik (kanal basina) +
    girdi.
    """

    def __init__(self, lin, wbits, abits, sa):
        super().__init__()
        self.weight = nn.Parameter(lin.weight.data.clone())
        self.bias = nn.Parameter(lin.bias.data.clone())
        self.wbits, self.abits, self.sa = wbits, abits, sa

    def forward(self, x):
        s = simetrik_olcek(
            self.weight.detach(), self.wbits, kanal=True
        )
        w = SahteKuantFn.apply(self.weight, s, self.wbits)
        if self.abits and self.abits < 32:
            x = SahteKuantFn.apply(x, self.sa, self.abits)
        return nn.functional.linear(x, w, self.bias)
```

`girdi_olcekleri` her doğrusal katmanın girdisine bir kanca (hook) takar, kalibrasyon verisini ileri geçirir ve değerlerin max ya da yüzdelik büyüklüğünden ölçek üretir.

```python
def girdi_olcekleri(base, Xcal, p, bits=8):
    """Her Linear'in girdisi icin simetrik olcek: max (p=1.0) ya da
    yuzdelik.
    """
    lv = 2 ** (bits - 1) - 1
    lins = [i for i, l in enumerate(base) if isinstance(l, nn.Linear)]
    biriken = {i: [] for i in lins}
    kancalar = [
        base[i].register_forward_pre_hook(
            lambda m, g, i=i: biriken[i].append(
                g[0].detach().abs().flatten()
            )
        )
        for i in lins
    ]
    with torch.no_grad():
        base(Xcal)
    for k in kancalar:
        k.remove()
    olcekler = {}
    for i in lins:
        v = torch.cat(biriken[i])
        q = v.max() if p >= 1.0 else torch.quantile(v, p)
        olcekler[i] = (q.clamp_min(1e-8) / lv).reshape(())
    return olcekler
```

`ptq` modelin bir kopyasını alır ve ağırlıkları kuantize eder. Aktivasyon kuantizasyonu isteniyorsa her doğrusal katmanın önüne bir `ActQ` ekler. QAT ise ağırlıkları eğitim sırasında kuantize eden katmanlarla modelin yeniden kurulup eğitilmesini sağlar.

```python
def ptq(base, wbits, abits, kanal, Xcal, p=1.0):
    """abits=32 ya da None: aktivasyon kuantizasyonu yok."""
    akt = abits is not None and abits < 32
    m = copy.deepcopy(base)
    sa = girdi_olcekleri(base, Xcal, p, abits) if akt else {}
    katman = []
    for i, l in enumerate(m):
        if isinstance(l, nn.Linear):
            if wbits < 32:
                s = simetrik_olcek(l.weight.data, wbits, kanal)
                l.weight.data = qdq(l.weight.data, s, wbits)
            if akt:
                katman.append(ActQ(sa[i], abits))
        katman.append(l)
    return nn.Sequential(*katman)


def qat(base, wbits, abits, Xcal, Xtr, ytr, tohum):
    akt = abits < 32
    sa = girdi_olcekleri(base, Xcal, 0.999, abits) if akt else {}
    katman = []
    for i, l in enumerate(base):
        if isinstance(l, nn.Linear):
            katman.append(QATLinear(l, wbits, abits, sa.get(i)))
        else:
            katman.append(l)
    m = nn.Sequential(*katman)
    egit(m, Xtr, ytr, epoch=20, lr=1e-4, tohum=tohum)
    return m
```

```python
def agirlik_bayt(model, wbits):
    bayt = 0
    for l in model:
        if isinstance(l, (nn.Linear, QATLinear)):
            bayt += l.weight.numel() * wbits / 8 + l.bias.numel() * 4
    return bayt


def boyut_bayt(model):
    tampon = io.BytesIO()
    torch.save(model.state_dict(), tampon)
    return tampon.getbuffer().nbytes
```

Ana döngü her tohum için modeli eğitir ve yukarıdaki yöntemleri sırayla uygular. Dinamik int8 satırı için model boyutu, durum sözlüğünün (state dict) serileştirilmiş boyutu olarak ölçülür.

```python
def main():
    satirlar = []
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        Xcal = Xtr[-200:]
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        fp = dogruluk(base, Xte, yte)
        P = sum(p.numel() for p in base.parameters())
        dinamik = torch.ao.quantization.quantize_dynamic(
            copy.deepcopy(base), {nn.Linear}, dtype=torch.qint8
        )
        if t == 0:
            s_max = girdi_olcekleri(base, Xcal, 1.0)
            s_p = girdi_olcekleri(base, Xcal, 0.999)
            for i in s_max:
                print(
                    "katman %d girdi olcegi: max=%.4f "
                    "p99.9=%.4f oran=%.1f"
                    % (i, s_max[i], s_p[i], float(s_max[i] / s_p[i]))
                )
```

```python
        yontemler = [
            ("fp32", 32, 32, None),
            ("PTQ_w8_kanal", 8, 32, dict(kanal=True)),
            ("PTQ_w8a8_tensor_max", 8, 8, dict(kanal=False, p=1.0)),
            (
                "PTQ_w8a8_tensor_p999",
                8,
                8,
                dict(kanal=False, p=0.999),
            ),
```

```python
            ("PTQ_w4_tensor", 4, 32, dict(kanal=False)),
            ("PTQ_w4_kanal", 4, 32, dict(kanal=True)),
            ("QAT_w4_kanal", 4, 32, "qat"),
            ("PTQ_w3_kanal", 3, 32, dict(kanal=True)),
            ("QAT_w3_kanal", 3, 32, "qat"),
            ("PTQ_w2_kanal", 2, 32, dict(kanal=True)),
            ("QAT_w2_kanal", 2, 32, "qat"),
            ("PTQ_w4a8_kanal_p999", 4, 8, dict(kanal=True, p=0.999)),
            ("QAT_w4a8_kanal", 4, 8, "qat"),
            ("PyTorch_dinamik_int8", 8, 8, "dyn"),
        ]
```

```python
        for ad, wb, ab, opt in yontemler:
            if ad == "fp32":
                m, acc = base, fp
                bayt = P * 4
            elif opt == "dyn":
                m = dinamik
                acc = dogruluk(m, Xte, yte)
                bayt = boyut_bayt(m)
```

```python
            elif opt == "qat":
                m = qat(base, wb, ab, Xcal, Xtr, ytr, t)
                acc = dogruluk(m, Xte, yte)
                bayt = agirlik_bayt(m, wb)
            else:
                m = ptq(
                    base,
                    wb,
                    ab,
                    opt["kanal"],
                    Xcal,
                    opt.get("p", 1.0),
                )
                acc = dogruluk(m, Xte, yte)
                bayt = agirlik_bayt(m, wb)
            satirlar.append(
                dict(
                    yontem=ad,
                    wbit=wb,
                    abit=ab,
                    tohum=t,
                    dogruluk=round(acc, 4),
                    bayt=int(bayt),
                )
            )
            print(
                "tohum %d  %-22s acc=%.4f  bayt=%d"
                % (t, ad, acc, bayt)
            )
    os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
    with open(CIKTI, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", CIKTI)
    print("\nOzet (ortalama +- sapma, 3 tohum):")
    for ad in dict.fromkeys(s["yontem"] for s in satirlar):
        d = [s["dogruluk"] for s in satirlar if s["yontem"] == ad]
        b = [s["bayt"] for s in satirlar if s["yontem"] == ad][0]
        print(
            "%-22s %.4f +- %.4f  bayt=%d"
            % (ad, st.mean(d), st.pstdev(d), b)
        )
```

```python
if __name__ == "__main__":
    t0 = time.time()
    main()
    print("sure: %.1f s" % (time.time() - t0))
```

Betiğin son hali, üç tohumun ortalama ve sapma özetini yazar. Ayrıntılı satırlar (her tohum ve yöntem için) günlük dosyasında durur; burada ilk üç kalibrasyon ölçeği satırını ve özeti gösteriyoruz.

```term
$ python b75_kuantizasyon.py
katman 0 girdi olcegi: max=0.0079 p99.9=0.0079 oran=1.0
katman 2 girdi olcegi: max=0.0187 p99.9=0.0154 oran=1.2
katman 4 girdi olcegi: max=0.0731 p99.9=0.0610 oran=1.2
```

```term
Ozet (ortalama +- sapma, 3 tohum):
fp32                   0.9728 +- 0.0009  bayt=203304
PTQ_w8_kanal           0.9729 +- 0.0017  bayt=52008
PTQ_w8a8_tensor_max    0.9735 +- 0.0023  bayt=52008
PTQ_w8a8_tensor_p999   0.9735 +- 0.0023  bayt=52008
PTQ_w4_tensor          0.9691 +- 0.0009  bayt=26792
PTQ_w4_kanal           0.9716 +- 0.0023  bayt=26792
QAT_w4_kanal           0.9722 +- 0.0000  bayt=26792
PTQ_w3_kanal           0.9648 +- 0.0040  bayt=20488
QAT_w3_kanal           0.9691 +- 0.0032  bayt=20488
PTQ_w2_kanal           0.7988 +- 0.0537  bayt=14184
QAT_w2_kanal           0.9624 +- 0.0023  bayt=14184
PTQ_w4a8_kanal_p999    0.9722 +- 0.0015  bayt=26792
QAT_w4a8_kanal         0.9722 +- 0.0000  bayt=26792
PyTorch_dinamik_int8   0.9729 +- 0.0017  bayt=56242
sure: 20.0 s
```

Özet tabloda dikkat edilmesi gereken üç şey var. Birincisi, 8 bit'te (PTQ, W8A8 ve dinamik int8) doğruluk fp32'ye neredeyse eşit: 0,9728 ile 0,9735 arasında. İkincisi, 4 bitte tensör başına ölçek kanal başına ölçekten biraz kötü (0,9691 ve 0,9716). Üçüncüsü ve en önemlisi, 2 bitte PTQ çöküyor (0,7988 ± 0,0537) ama QAT aynı bit genişliğinde 0,9624 ± 0,0023 sağlıyor.

Bu sayılar bir ölçüm sınırını da gösterir. Test kümesi 540 örnek içerir. Bu boyutta bir doğruluk oranının standart hatası yaklaşık `√(p(1 − p) / n)` ile bulunur: `p = 0,973` için yaklaşık 0,007, yani 0,7 puan. Bu nedenle 8 bitteki 0,1 puanlık farklar gürültüdür ve bir yöntemin diğerinden "daha iyi" olduğu söylenemez. Gerçek ayrım, 2 bitteki çöküş gibi büyük farklarda çıkar. Bu tür karşılaştırmalarda fark, tohum sapmasından birkaç kat büyük olmalıdır.

Şekil 75.2 aynı sonucu bit genişliğine göre çizer. Yatay eksende bit sayısı, dikey eksende üç tohumun ortalama doğruluğu ve sapması var.

![Şekil 75.2: Doğruluk–bit takası: kanal başına PTQ ve QAT, ağırlık bit genişliğine göre (aktivasyon fp32, 3 tohum)](gorseller/b75_bit_takas.png)

Şekilde iki eğrinin ayrıldığı yer 3 bit ile 2 bit arasıdır. 4 ve 3 bitte PTQ ile QAT arasındaki fark küçük ve gürültü seviyesinde; 2 bitte ise PTQ'nun yeniden eğitilmeden bu ızgaraya uyması mümkün değildir. Ağırlığı yalnızca üç değerle (−s, 0, +s) ifade eden 2 bitlik bir ızgarada, eğitim sırasında ağın bu kısıtı telafi etmesi gerekir. Bu, QAT'ın asıl değeridir: ızgara çok kabaysa, ağ kendini ona göre ayarlamalıdır.

Ağırlıklar için PyTorch'un dinamik int8 yolu da ölçüldü. Bu yolda ağırlıklar kayıtlı olarak int8 tutulur, aktivasyonlar çalışma zamanında hesaplanan ölçekle kuantize edilir ve tam sayı çekirdekleri kullanılır. Doğruluk 0,9729 ± 0,0017 ile fp32'ye yakındır. Boyut ölçümü ise bir not gerektirir: dinamik modelin serileştirilmiş boyutu 56 242 bayttır; fp32 durum sözlüğü (203 304 bayt) bunun yaklaşık dört katıdır. Aradaki fark, ağırlıkların int8 olmasıyla birlikte dinamik modelin paketleme (packing) bilgisinin ve kalan fp32 bias değerlerinin de sayılmasından gelir.

Şimdi aykırı değer sorusuna dönelim. Aşağıdaki betik, kalibrasyon verisine tek bir kasıtlı aykırı örnek ekler (girdi 0 ile 1 yerine 8). Aynı modeli, her iki kalibrasyon ve üç yüzdelik ile, 8 ve 4 bit aktivasyonla ölçer.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: kalibrasyon verisindeki tek bir aykiri ornegin etkisi."""

import torch
from b75_ortak import veri, mlp_t, egit, dogruluk, TOHUMLAR
from b75_kuantizasyon import girdi_olcekleri, ptq
```

```python
def main():
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        temiz = Xtr[-200:].clone()
        kirli = temiz.clone()
        kirli[0] = 8.0  # tek bir asiri girdi (normal: 0..1)
        for ad, cal in [("temiz", temiz), ("aykiri", kirli)]:
            for ab in [8, 4]:
                for p in [1.0, 0.999, 0.99]:
                    s = girdi_olcekleri(base, cal, p, ab)
                    m = ptq(base, 8, ab, True, cal, p)
                    acc = dogruluk(m, Xte, yte)
                    print(
                        "tohum %d  A%d  kalibrasyon=%-6s p=%-6s  "
                        "olcek_katman2=%.4f  acc=%.4f"
                        % (t, ab, ad, p, float(s[2]), acc)
                    )
```

```term
$ python b75_aykiri.py
tohum 0  A8  kalibrasyon=temiz  p=1.0     olcek_katman2=0.0187  acc=0.9704
tohum 0  A8  kalibrasyon=temiz  p=0.999   olcek_katman2=0.0154  acc=0.9704
tohum 0  A8  kalibrasyon=temiz  p=0.99    olcek_katman2=0.0116  acc=0.9704
tohum 0  A4  kalibrasyon=temiz  p=1.0     olcek_katman2=0.3386  acc=0.9667
tohum 0  A4  kalibrasyon=temiz  p=0.999   olcek_katman2=0.2793  acc=0.9722
tohum 0  A4  kalibrasyon=temiz  p=0.99    olcek_katman2=0.2108  acc=0.9667
tohum 0  A8  kalibrasyon=aykiri p=1.0     olcek_katman2=0.2379  acc=0.9667
tohum 0  A8  kalibrasyon=aykiri p=0.999   olcek_katman2=0.0965  acc=0.9722
tohum 0  A8  kalibrasyon=aykiri p=0.99    olcek_katman2=0.0123  acc=0.9722
tohum 0  A4  kalibrasyon=aykiri p=1.0     olcek_katman2=4.3170  acc=0.1000
tohum 0  A4  kalibrasyon=aykiri p=0.999   olcek_katman2=1.7507  acc=0.8500
tohum 0  A4  kalibrasyon=aykiri p=0.99    olcek_katman2=0.2234  acc=0.9667
```

Tohum 0 için ilk ölçeğe bakalım: 4 bitlik aktivasyonda temiz kalibrasyonda `max` ölçeği 0,339, aykırı değer eklenince 4,317 oluyor; yaklaşık on iki kat. Bu, tam sayı ızgarasındaki adım genişliğinin on iki kat büyümesi demektir. Sonuç olarak doğruluk 0,9667'den 0,1000'e düşüyor: model tek bir sınıfa çöküyor. Yüzdelik kalibrasyon (%99,9) aynı değeri 1,75'e indiriyor ve doğruluk 0,85'e çıkıyor; %99 kalibrasyon ise ölçeği 0,22'ye indirip doğruluğu 0,9667'ye geri getiriyor.

Üç tohumun tamamında aynı desen görülüyor (tohum 1 ve 2 için 4 bit'te max kalibrasyonu 0,1000; yüzdelik %99 için 0,9685 ve 0,9741). Bu desen, "aykırı değerlerle baş etmek" için iki kuralı verir. Önce, kalibrasyon verisinin temiz olduğundan emin ol; ama bu her zaman mümkün değildir, bu yüzden ikinci kural önemlidir: yüzdelik kalibrasyon kullan ve düşük bit genişliklerinde aktivasyon ölçeğini mutlaka doğrula. Sekiz bitte bu sorun görünmez, çünkü ızgara yeterince incedir. Dört bitte ise bir örnek bütün modeli bozabilir.

### Büyük dil modelleri ve ürün kuantizasyon (genel bilgi)

Bölüm 71'de bir dil modelinin ağırlıklarını 4 bit'e indirmenin bellek kazancını gördük. Burada bu yöntemlerin gerçek modellerde nasıl çalıştığına kısaca bakıyoruz; bunları bu bölümde çalıştırmadık, yalnızca genel bilgi olarak anlatıyoruz. **GPTQ**, her ağırlık sütununu kuantize ederken kalan ağırlıkları, kuantizasyon hatasını telafi edecek biçimde günceller. **AWQ** ise tersine, aktivasyon büyüklüklerinden hangi kanalların önemli olduğunu etkinlik verisiyle saptar ve o kanalların ölçeğini ayrıca korur. **llama.cpp** bu tür kuantize edilmiş modelleri CPU üzerinde çalıştıran bir C/C++ uygulamasıdır; **TensorRT-LLM** ise NVIDIA GPU'larında aynı işi yapan bir motordur (genel bilgi).

**Ürün kuantizasyon** (product quantization, PQ) ise farklı bir fikirdir ve vektör aramasında kullanılır (Bölüm 71'deki IVF ile birlikte). Bir `d` boyutlu vektörü `m` alt vektöre bölersin. Her alt vektör grubu için k-means (Bölüm 61) ile küçük bir kod kitabı öğrenirsin; vektörün kendisi yerine her alt vektör için kitaptaki en yakın kodun indeksini saklarsın. Bellek hesabı basittir: 128 boyutlu bir fp32 vektör 512 bayttır; 16 alt vektör ve her biri için 8 bitlik indeks kullanırsan vektör 16 bayta iner, yani 32 kat. Bunun bedeli, aramanın yaklaşık olmasıdır: kodlama hatası geri dönülmez.

Bölüm 72'de gördüğümüz kanal gürültüsü ile kuantizasyon hatasının birlikte nasıl ele alınacağı ise bir eğitim sorusudur. Kanal gürültüsüne dayanıklı bir ızgara için eğitim sırasında gürültüyü de modele katmak gerekir; bu, QAT fikrinin bir uzantısıdır ve dayanıklılık konusu Bölüm 78'de robustluk olarak tekrar ele alınacak.

## 75.4 Budama: gereksiz ağırlıkları atmak

Budama fikri basittir: büyük ağırlıklar bilgi taşır, küçük olanlar yaklaşık olarak sıfırdır. En küçük mutlak değerli ağırlıkları sıfırlarsak, model çoğu zaman neredeyse aynı çıktıyı verir. Bölüm 58'de L1 düzenlemesinin ağırlıkları sıfıra çektiğini görmüştük; burada aynı sezgiyi açık bir budama kararına dönüştürüyoruz.

Budamanın iki ana biçimi var. **Yapılandırılmamış budama** (unstructured pruning) her ağırlığı ayrı ayrı sıfırlar; matriste rastgele konumlarda sıfırlar oluşur. **Yapılandırılmış budama** (structured pruning) bütün bir satırı, sütunu ya da kanalı siler; model fiilen daha küçük bir modele dönüşür. İki biçimin çalışma zamanındaki etkisi çok farklıdır ve bu bölümün en önemli dersi buradadır: yapılandırılmamış seyreklik, donanım ona özel destek vermedikçe hızlanma getirmez.

Budamanın kendisi, en küçük değerleri bulup bir maske üretmekle başlar. Aşağıdaki fonksiyon bunu sıfırdan yapar: `|w|` değerlerini sıralar ve en küçük `oran · n` tanesinin konumuna sıfır koyar. Ardından aynı maskeyi PyTorch'un `torch.nn.utils.prune.l1_unstructured` fonksiyonuyla karşılaştırır. Eşleşme, bu fonksiyonun ne yaptığını doğrular. Kaynak kodu, bu bölümün sonundaki Kod Okuma Egzersizi'nde açılacak.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: budama. Buyukluk budamasi (sifirdan), seyreklik taramasi,
kubik yinelemeli budama, piyango bileti, kanal budama ve hiz olcumu.
"""

import copy
import csv
import os
import numpy as np
import torch
import torch.nn as nn
from b75_ortak import (
    veri,
    mlp,
    mlp_t,
    egit,
    dogruluk,
    uygula_maske,
    zamanla,
    TOHUMLAR,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
KATMANLAR = (0, 2, 4)  # mlp(): dogrusal katmanlarin indeksleri


def buyukluk_maskesi(W, oran):
    """En kucuk |w| degerlerinin oran kadarini 0 yapan 0/1 maske."""
    k = int(round(oran * W.numel()))
    m = torch.ones_like(W)
    if k > 0:
        en_kucuk = torch.argsort(W.abs().flatten())[:k]
        m.view(-1)[en_kucuk] = 0.0
    return m
```

Maske fonksiyonu tek bir katmanın ağırlıklarından çalışır. Aşağıdaki iki fonksiyon, seyreklik sayısını ölçer ve torch ile karşılaştırmayı yapar. Kübik takvim ve kanal budama çekirdeği, aşağıdaki deneylerde kullanılır.

```python
def maskeler_olustur(model, oran):
    return {
        i: buyukluk_maskesi(model[i].weight.data, oran)
        for i in KATMANLAR
    }


def seyreklik(model):
    """Dogrusal katmanlardaki sifir oraninin ag geneline gore payi."""
    sifir = toplam = 0
    for i in KATMANLAR:
        W = model[i].weight.data
        sifir += (W == 0).sum().item()
        toplam += W.numel()
    return sifir / toplam


def torch_ile_dogrula():
    """Kendi maskemiz torch prune.l1_unstructured ile ayni mi?
    """
    import torch.nn.utils.prune as prune

    lin = nn.Linear(64, 256)
    W = lin.weight.data.clone()
    m1 = buyukluk_maskesi(W, 0.9)
    prune.l1_unstructured(lin, "weight", amount=0.9)
    print(
        "torch ile maske eslesmesi:", torch.equal(m1, lin.weight_mask)
    )
```

```python
def kubik(sf, t, T):
    """Zhu & Gupta (2017) kubik seyreklik takvimi (genel bilgi)."""
    return sf * (1 - (1 - t / T) ** 3)


def kanal_buda(model, oran):
    """Gizli katman 0'in en dusuk L1 normlu noronlarini siler; sonraki
    dogrusal katmanin ilgili sutunlari da silinir."""
    W0, b0 = model[0].weight.data, model[0].bias.data
    W2, b2 = model[2].weight.data, model[2].bias.data
    n = W0.shape[0]
    tut = n - int(round(oran * n))
    norm = W0.abs().sum(dim=1)
    idx = torch.argsort(norm, descending=True)[:tut].sort().values
    yeni = mlp(gizli=(tut, W2.shape[0]))
    with torch.no_grad():
        yeni[0].weight.copy_(W0[idx])
        yeni[0].bias.copy_(b0[idx])
        yeni[2].weight.copy_(W2[:, idx])
        yeni[2].bias.copy_(b2)
        yeni[4].weight.copy_(model[4].weight)
        yeni[4].bias.copy_(model[4].bias)
    return yeni
```

Budamanın geri kalanı üç soru etrafında döner. Bir seyreklik düzeyinde doğruluk ne kadar düşer? İnce ayar bu kaybı ne kadar geri getirir? Yinelemeli budama, tek adımdaki budamadan daha iyi mi? Ayrıca piyango bileti hipotezi (Frankle ve Carbin, 2019; genel bilgi), budanmış bir ağın başlangıçtaki ağırlıklarla yeniden eğitilmesinin önemini sorgular. Her soru için ayrı bir deney var.

Önce seyreklik taraması. Her tohum için aynı taban model eğitilir; her seyreklik düzeyinde iki sayı alınır: budamadan hemen sonraki doğruluk ve 20 epoch ince ayardan sonraki doğruluk. İnce ayarda öğrenme oranı `1e-3` seçildi. İlk denememizde `1e-4` kullandık ve yüksek seyreklikte toparlanma çok zayıf çıktı (%95'te tohum 0 için yaklaşık 0,35). Bunu bir ayar hatası olarak görüp düzelttik; ama bu, öğrenme oranının sonucu ne kadar değiştirdiğinin de açık bir örneğidir.

```python
def seyreklik_taramasi(satirlar):
    oranlar = [0.0, 0.5, 0.8, 0.9, 0.95, 0.98]
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        for o in oranlar:
            m = copy.deepcopy(base)
            mk = maskeler_olustur(m, o)
            uygula_maske(m, mk)
            budamasiz = dogruluk(m, Xte, yte)
            if o > 0:
                egit(
                    m,
                    Xtr,
                    ytr,
                    epoch=20,
                    lr=1e-3,
                    tohum=t,
                    maskeler=mk,
                )
            ince = dogruluk(m, Xte, yte)
            satirlar.append(
                dict(
                    oran=o,
                    tohum=t,
                    budamasiz=round(budamasiz, 4),
                    ince_ayar=round(ince, 4),
                    gercek_seyreklik=round(seyreklik(m), 4),
                )
            )
            print(
                "tohum %d oran %.2f  budamasiz=%.4f  ince_ayar=%.4f  "
                "seyreklik=%.3f"
                % (t, o, budamasiz, ince, seyreklik(m))
            )
```

Yinelemeli budamada seyreklik, kübik bir takvimle adım adım artırılır (Zhu ve Gupta, 2017; genel bilgi). Her adımda maske güncellenir ve kısa bir ince ayar yapılır. Böylece hedef seyrekliğe tek sıçramada değil, yumuşak bir geçişle ulaşılır. Karşılaştırmada toplam epoch sayısı yaklaşık aynı tutuldu: tek adım 40 epoch, yinelemeli 4 × 10 epoch.

```python
def yinelemeli_karsilastirma():
    """%95 seyreklik: tek adim (40 epoch) ve 4 adim kubik."""
    sf = 0.95
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        tek = copy.deepcopy(base)
        mk = maskeler_olustur(tek, sf)
        uygula_maske(tek, mk)
        egit(tek, Xtr, ytr, epoch=40, lr=1e-3, tohum=t, maskeler=mk)
        yin = copy.deepcopy(base)
        for s in range(1, 5):
            mk = maskeler_olustur(yin, kubik(sf, s, 4))
            uygula_maske(yin, mk)
            egit(
                yin, Xtr, ytr, epoch=10, lr=1e-3, tohum=t, maskeler=mk
            )
        print(
            "tohum %d  tek_adim=%.4f  yinelemeli=%.4f  "
            "seyreklik=%.3f/%.3f"
            % (
                t,
                dogruluk(tek, Xte, yte),
                dogruluk(yin, Xte, yte),
                seyreklik(tek),
                seyreklik(yin),
            )
        )
```

Piyango bileti deneyinde aynı maske iki farklı başlangıçla eğitilir. Birincisinde ağırlıklar, eğitimden önceki başlangıç değerlerine geri sarılır ve maske uygulanır. İkincisinde maske aynı, ama ağırlıklar yeni bir rastgele başlangıçtan alınır. Hipotez birincinin daha iyi olacağını söyler; bunu koşullu olarak ölçüyoruz.

```python
def piyango_bileti():
    """Ayni maske: (a) baslangic agirliklari, (b) rastgele yeniden
    baslat. Ikisini ayni maskeyle yeniden egit."""
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        torch.manual_seed(t)
        theta0 = mlp()
        st0 = copy.deepcopy(theta0.state_dict())
        egit(theta0, Xtr, ytr, tohum=t)
        mk = maskeler_olustur(theta0, 0.8)
        lt = mlp()
        lt.load_state_dict(st0)
        uygula_maske(lt, mk)
        egit(lt, Xtr, ytr, epoch=60, tohum=t, maskeler=mk)
        torch.manual_seed(t + 100)
        ras = mlp()
        uygula_maske(ras, mk)
        egit(ras, Xtr, ytr, epoch=60, tohum=t + 100, maskeler=mk)
        print(
            "tohum %d  bilet(geri sarma)=%.4f  rastgele=%.4f"
            % (t, dogruluk(lt, Xte, yte), dogruluk(ras, Xte, yte))
        )
```

Yapılandırılmış budama için `kanal_buda` fonksiyonu (yukarıda kübik takvimle birlikte görülüyor) birinci gizli katmanın nöronlarını L1 normlarına göre sıralar, en küçük yarısını siler ve bir sonraki katmanın ilgili sütunlarını da kaldırır. Böylece model fiilen küçülür: parametre sayısı ve matris boyutları düşer. Aşağıdaki deney, bu biçimin doğruluğunu ölçer.

```python
def kanal_dogruluk(satirlar):
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        k = kanal_buda(base, 0.5)
        a0 = dogruluk(k, Xte, yte)
        egit(k, Xtr, ytr, epoch=20, lr=1e-3, tohum=t)
        a1 = dogruluk(k, Xte, yte)
        print(
            "tohum %d  kanal %%50: budamasiz=%.4f  ince_ayar=%.4f"
            % (t, a0, a1)
        )
```

Hız ölçümü için seyrek ağırlıklar, `torch.sparse` içindeki CSR (sıkıştırılmış satır seyrekliği) biçimine çevrilir ve ileri geçiş bu biçimle yapılır. CSR, yalnızca sıfır olmayan değerleri ve konumlarını tutar; ama her elemanın konum bilgisi ek bellek ve ek dolaylama (indirection) gerektirir. Bu nedenle seyrek bir matris, yoğun bir matrisle aynı hızda çalışabilir ya da yavaş olabilir. `ileri_csr` bu ileri geçişi uygular ve sonucu yoğun modelle karşılaştırır.

```python
def ileri_csr(Ws, bs, x):
    """Seyrek (CSR) agirliklarla ileri gecis: h = W h + b, ara ReLU.
    """
    h = x.T
    for j, (W, b) in enumerate(zip(Ws, bs)):
        h = torch.sparse.mm(W, h) + b.view(-1, 1)
        if j < len(Ws) - 1:
            h = torch.relu(h)
    return h.T
```

Hız ölçümü, yoğun modeli, yapılandırılmamış %50, %80, %90 ve %95 seyrek modelleri (hem yoğun hem CSR olarak) ve yapılandırılmış %50 kanal budanmış modeli ölçer. Hepsi aynı 2048 gizli nöronlu MLP'den türetilir. Fonksiyonu iki parçada veriyoruz.

```python
def hiz_olcumu():
    torch.manual_seed(0)
    base = mlp(gizli=(2048, 2048)).eval()
    x = torch.randn(1, 64)
    satirlar = []

    def kaydet(ad, model_fn, etkin):
        with torch.no_grad():
            med, p95 = zamanla(model_fn, n=300, isinma=30)
        satirlar.append(
            dict(
                yontem=ad,
                etkin_parametre=etkin,
                medyan_ms=round(med, 4),
                p95_ms=round(p95, 4),
            )
        )
        print(
            "%-26s etkin=%8d medyan=%.4f ms  p95=%.4f ms"
            % (ad, etkin, med, p95)
        )

    toplam = sum(p.numel() for p in base.parameters())
    kaydet("yogun_fp32", lambda: base(x), toplam)
```

```python
    for o in [0.5, 0.8, 0.9, 0.95]:
        s = copy.deepcopy(base)
        mk = maskeler_olustur(s, o)
        uygula_maske(s, mk)
        etkin = sum(int((s[i].weight != 0).sum()) for i in KATMANLAR)
        Ws = [
            (s[i].weight * mk[i]).to_sparse_csr() for i in KATMANLAR
        ]
        bs = [s[i].bias.detach() for i in KATMANLAR]
        with torch.no_grad():
            fark = (ileri_csr(Ws, bs, x) - s(x)).abs().max().item()
        print(
            "seyreklik %.2f  CSR dogrulama en buyuk fark: %.2e"
            % (o, fark)
        )
        kaydet(
            "yapilandirilmamis_%d_yogun" % round(o * 100),
            lambda: s(x),
            etkin,
        )
        kaydet(
            "yapilandirilmamis_%d_csr" % round(o * 100),
            lambda: ileri_csr(Ws, bs, x),
            etkin,
        )
```

```python
    k50 = kanal_buda(base, 0.5).eval()
    kaydet(
        "yapilandirilmis_kanal_50",
        lambda: k50(x),
        sum(p.numel() for p in k50.parameters()),
    )
    return satirlar
```

```python
if __name__ == "__main__":
    torch.set_num_threads(4)
    torch_ile_dogrula()
    satirlar = []
    seyreklik_taramasi(satirlar)
    yaz = os.path.join(VERI, "b75_seyreklik.csv")
    with open(yaz, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yaz)
    yinelemeli_karsilastirma()
    piyango_bileti()
    kanal_dogruluk(satirlar)
    hiz = hiz_olcumu()
    yaz = os.path.join(VERI, "b75_hiz.csv")
    with open(yaz, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hiz[0].keys()))
        w.writeheader()
        w.writerows(hiz)
    print("CSV yazildi:", yaz)
```

Betik, bölümleri sırayla çalıştırır: önce torch ile maske eşleşmesini, sonra her tohum için seyreklik taramasını ve yinelemeli, piyango ve kanal deneylerini, en sonunda hız ölçümünü yazar. Aşağıdaki çıktı, seyreklik ve deney satırlarını gösterir.

```term
$ python b75_budama.py
torch ile maske eslesmesi: True
tohum 0 oran 0.00  budamasiz=0.9722  ince_ayar=0.9722  seyreklik=0.000
tohum 0 oran 0.50  budamasiz=0.9685  ince_ayar=0.9704  seyreklik=0.500
tohum 0 oran 0.80  budamasiz=0.7630  ince_ayar=0.9759  seyreklik=0.800
tohum 0 oran 0.90  budamasiz=0.4852  ince_ayar=0.9759  seyreklik=0.900
tohum 0 oran 0.95  budamasiz=0.1611  ince_ayar=0.9185  seyreklik=0.950
tohum 0 oran 0.98  budamasiz=0.1000  ince_ayar=0.6037  seyreklik=0.980
tohum 1 oran 0.00  budamasiz=0.9741  ince_ayar=0.9741  seyreklik=0.000
tohum 1 oran 0.50  budamasiz=0.9593  ince_ayar=0.9704  seyreklik=0.500
tohum 1 oran 0.80  budamasiz=0.8685  ince_ayar=0.9704  seyreklik=0.800
tohum 1 oran 0.90  budamasiz=0.5074  ince_ayar=0.9593  seyreklik=0.900
tohum 1 oran 0.95  budamasiz=0.1000  ince_ayar=0.8370  seyreklik=0.950
tohum 1 oran 0.98  budamasiz=0.1000  ince_ayar=0.4204  seyreklik=0.980
tohum 2 oran 0.00  budamasiz=0.9722  ince_ayar=0.9722  seyreklik=0.000
tohum 2 oran 0.50  budamasiz=0.9537  ince_ayar=0.9704  seyreklik=0.500
tohum 2 oran 0.80  budamasiz=0.8296  ince_ayar=0.9722  seyreklik=0.800
tohum 2 oran 0.90  budamasiz=0.5611  ince_ayar=0.9574  seyreklik=0.900
tohum 2 oran 0.95  budamasiz=0.1333  ince_ayar=0.9222  seyreklik=0.950
tohum 2 oran 0.98  budamasiz=0.1259  ince_ayar=0.5130  seyreklik=0.980
CSV yazildi: D:/Mevcut Projeler/Kitap/engine/veri\b75_seyreklik.csv
tohum 0  tek_adim=0.9444  yinelemeli=0.9389  seyreklik=0.950/0.950
tohum 1  tek_adim=0.9148  yinelemeli=0.9481  seyreklik=0.950/0.950
tohum 2  tek_adim=0.9500  yinelemeli=0.9315  seyreklik=0.950/0.950
tohum 0  bilet(geri sarma)=0.9741  rastgele=0.9796
tohum 1  bilet(geri sarma)=0.9667  rastgele=0.9648
tohum 2  bilet(geri sarma)=0.9630  rastgele=0.9630
tohum 0  kanal %50: budamasiz=0.8796  ince_ayar=0.9704
tohum 1  kanal %50: budamasiz=0.8889  ince_ayar=0.9722
tohum 2  kanal %50: budamasiz=0.9167  ince_ayar=0.9759
```

Seyreklik taramasının özeti CSV dosyasından türetilmiştir. Burada yalnızca seyreklik satırları alındı.

```term
== Seyreklik (budama sonrasi / ince ayarli) ==
oran 0.0   budamasiz 0.9728+-0.0009 ince 0.9728+-0.0009
oran 0.5   budamasiz 0.9605+-0.0061 ince 0.9704+-0.0000
oran 0.8   budamasiz 0.8204+-0.0436 ince 0.9728+-0.0023
oran 0.9   budamasiz 0.5179+-0.0319 ince 0.9642+-0.0083
oran 0.95  budamasiz 0.1315+-0.0250 ince 0.8926+-0.0393
oran 0.98  budamasiz 0.1086+-0.0122 ince 0.5124+-0.0748
```

Şekil 75.3 aynı sonucu çizer: yatay eksende seyreklik, dikey eksende doğruluk. İki eğri ayrıdır: budamadan hemen sonraki doğruluk ile ince ayarlı doğruluk.

![Şekil 75.3: Seyrekliğe göre test doğruluğu: budama sonrası ve ince ayarlı (3 tohum ortalaması ± sapma)](gorseller/b75_seyreklik.png)

Tablodan üç sonuç çıkar. Birincisi, %50 seyreklik her iki durumda da neredeyse zararsızdır (budamasız 0,9605; ince ayarlı 0,9704). İkincisi, %80 ve %90 seyreklikte budamasız doğruluk çöker (0,82 ve 0,52), ama ince ayar bunu büyük ölçüde geri getirir (0,973 ve 0,964). Üçüncüsü, %95 ve üzerinde 50 bin parametreli bu küçük ağ kapasitesini kaybeder: %95'te ince ayarlı 0,893, %98'de 0,512. Ağda yalnızca birkaç bin ağırlık kaldığında ince ayar bile yetmez.

Yinelemeli budama ile tek adım arasında ise belirgin bir fark yok. %95 seyreklikte tek adım (40 epoch) ortalama 0,9364, yinelemeli (4 × 10 epoch) ortalama 0,9395 verdi. Tohumlar arasında fark işaret değiştiriyor: tohum 0'da tek adım 0,9444 ve yinelemeli 0,9389; tohum 1'de 0,9148 ve 0,9481; tohum 2'de 0,9500 ve 0,9315. Bu küçük ağda yinelemeli budamanın faydası ölçülebilir değil. Büyük ağlarda ve yüksek seyreklikte yinelemeli yöntemin genelde daha güvenli olduğu bilinir (genel bilgi), ama bu bölümün deneyi bunu göstermiyor.

Piyango bileti deneyinde %80 seyreklikte geri sarma ile rastgele başlangıç arasında bir fark yok: ortalama 0,9679 ve 0,9691. Tohum 0'da rastgele başlangıç 0,0055 daha yüksek, tohum 1'de geri sarma 0,0019 daha yüksek, tohum 2'de iki değer eşit (0,9630). Bu, bu küçük MLP ve digits görevinde piyango bileti avantajının görünmediği anlamına gelir. Bunu Frankle ve Carbin'in asıl deneylerine karşı bir çelişki olarak okuma: bizim görevimiz çok kolay ve ağımız çok küçük. Hipotezi sınamak için daha büyük bir ağ ve daha zor bir görev gerekir.

Kanal budama, %50 kanal sildikten sonra budamasız doğrulukta belirgin bir düşüş gösterdi (ortalama 0,8951). Ama 20 epoch ince ayardan sonra ortalama 0,9728'e çıktı; bu, yapılandırılmamış %50 ince ayarlı sonuçla (0,9704) aynı düzeydedir. Yani bu görevde iki budama biçimi doğrulukta eşit. Asıl fark hızda.

Şekil 75.4 hız ölçümünü gösterir. Çubuklar batch 1 gecikmesinin medyanını, uç çizgisi p95'i verir.

![Şekil 75.4: Batch 1 gecikmesi: yoğun, yapılandırılmamış (yoğun ve CSR) ve yapılandırılmış budama (medyan, p95 çizgisi)](gorseller/b75_budama_hiz.png)

Hız satırları aşağıda. Son satır, kanal budamanın CSV çıktısıdır.

```term
yogun_fp32                 etkin= 4349962 medyan=0.8692 ms  p95=1.7585 ms
seyreklik 0.50  CSR dogrulama en buyuk fark: 1.10e-07
yapilandirilmamis_50_yogun etkin= 2172928 medyan=0.9084 ms  p95=1.6651 ms
yapilandirilmamis_50_csr   etkin= 2172928 medyan=1.7151 ms  p95=2.4219 ms
seyreklik 0.80  CSR dogrulama en buyuk fark: 1.40e-08
yapilandirilmamis_80_yogun etkin=  869171 medyan=0.7605 ms  p95=1.5093 ms
yapilandirilmamis_80_csr   etkin=  869171 medyan=0.6992 ms  p95=1.1211 ms
seyreklik 0.90  CSR dogrulama en buyuk fark: 7.45e-09
yapilandirilmamis_90_yogun etkin=  434585 medyan=0.7413 ms  p95=1.4608 ms
yapilandirilmamis_90_csr   etkin=  434585 medyan=0.3898 ms  p95=0.5248 ms
seyreklik 0.95  CSR dogrulama en buyuk fark: 1.86e-09
yapilandirilmamis_95_yogun etkin=  217293 medyan=0.7880 ms  p95=1.6527 ms
yapilandirilmamis_95_csr   etkin=  217293 medyan=0.2583 ms  p95=0.3494 ms
yapilandirilmis_kanal_50   etkin= 2186250 medyan=0.3621 ms  p95=0.8091 ms
CSV yazildi: D:/Mevcut Projeler/Kitap/engine/veri\b75_hiz.csv
```

Ölçümün okunuşu şöyle. Yapılandırılmamış %90 seyrek ağırlıklar **yoğun** biçimde saklandığında (sıfırlarla birlikte) hız değişmez: 0,74 ms, yoğun taban çizgisi 0,87 ms. Taban, koşular arasında 0,88 ile 1,12 ms arasında değişti; bu yüzden oranları bir arada okumak gerekir. CSR ile %50 seyrekliğte gecikme artar (1,72 ms; yoğun 0,91 ms). %80'de başa baş (0,70 ms, yoğun 0,76 ms). %90'da CSR 0,39 ms ile yoğunun yaklaşık iki katı, %95'te 0,26 ms ile üç katı hızlıdır. Yapılandırılmış %50 kanal budama ise aynı koşuda 0,36 ms ile yoğun modelin yaklaşık 2,4 katı hızlı ve yarısı kadar parametre tutuyor.

Buradan çıkan ders şudur. Yapılandırılmamış seyreklik ancak seyreklik yüksekse ve seyrek bir çekirdek kullanılıyorsa hız kazandırır; kazanç da belli bir eşikten sonra başlar. Yapılandırılmış budama ise özel bir çekirdek gerektirmeden modelin gerçekten küçülmesini sağlar. Bu yüzden gömülü cihazlarda çoğu zaman kanal budama tercih edilir. Yapılandırılmamış budamanın dosya boyutunu da azaltmadığını unutma: yoğun saklama biçiminde sıfırlar yine yer kaplar. Bu nokta, Çözümlü Örnek 4'te edge tasarımında belirleyici olacak.

Son bir not: gecikme sayıları koşudan koşuya değişebilir. Bu yüzden sıralama ve oranlar kesin değerlerden daha güvenilirdir. Kesin sayı yerine oran okumak, bu tür ölçümlerin doğru yorumudur.

## 75.5 Bilgi damıtma: büyük öğretmenden küçük öğrenciye

Bir modelin büyüklüğü ile doğruluğu arasında çoğu zaman bir ilişki vardır, ama bu ilişki doğrusal değildir. Büyük bir modelin öğrendiği şey, yalnızca etiketlerde yazan "doğru sınıf" değil, sınıflar arasındaki benzerliklerdir: bir "7" rakamının "1"e değil "9"a daha çok benzediğini. Hinton, Vinyals ve Dean (2015; genel bilgi) bu fazla bilgiyi küçük bir modele aktarmanın bir yolunu önerdi: **bilgi damıtma** (knowledge distillation).

Fikir, öğretmenin çıktı olasılıklarını **sıcaklık** (temperature) `T` ile yumuşatmaktır. Softmax'ı `softmax(z / T)` biçiminde hesapladığımızda, `T > 1` olduğunda olasılık dağılımı düzleşir ve küçük olasılıklar daha görünür olur. Öğrenci, bu yumuşak hedefleri bir KL ıraksaması ile taklit eder. Gerçek etiketler de kaybın bir parçası olarak kalır. Toplam kayıp şöyledir:

L = (1 − a) · CE(y, s) + a · T² · KL(p_öğretmen^T ‖ p_öğrenci^T)

Burada `s` öğrencinin logit'leri, `a` ağırlığı belirleyen bir katsayı (bu bölümde 0,5), `T²` ise sıcaklıkla küçülen gradyanı telafi eden çarpandır. KL ıraksamasının ne olduğunu Bölüm 51'de bilgi teorisi bağlamında gördük; burada onu bir öğretmen dağılımından öğrenci dağılımına olan uzaklık olarak kullanıyoruz.

Bu bölümdeki deneyde öğretmen, 512 × 512 gizli katmanlı (301 066 parametre) bir MLP'dir. Öğrenci ise tek bir 32 nöronluk gizli katmana sahiptir (2 410 parametre). Yani öğrenci yaklaşık 125 kat küçüktür. Öğrenciyi üç yolla eğitiriz: yalnızca gerçek etiketlerle (sıfırdan), ve öğretmenden damıtarak üç farklı sıcaklıkta (T = 2, 4, 8). Şekil 75.5 bu süreci gösterir.

![Şekil 75.5: Bilgi damıtma şeması: öğretmenin yumuşak hedefleri ve gerçek etiketler birlikte öğrenciyi eğitir](gorseller/b75_damitma_semasi.png)

Damıtma fonksiyonu, yukarıdaki kaybı doğrudan uygular. Öğretmenin logit'leri eğitim verisi üzerinde önceden hesaplanır (öğretmen değişmez), sonra öğrenci mini-batch'lerle eğitilir.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: bilgi damitma. Buyuk ogretmen (512-512) -> kucuk ogrenci
(32 gizli noron). Ogrenci: sifirdan (CE) ve damitma (T = 2, 4, 8)."""

import copy
import csv
import os
import torch
import torch.nn.functional as F
from b75_ortak import veri, mlp, mlp_t, egit, dogruluk, TOHUMLAR

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def damit_egit(
    ogrenci, X, y, ogretmen_logit, T, alfa, epoch=60, lr=1e-3, tohum=0
):
    """L = (1 - alfa) * CE(y, s) + alfa * T^2 * KL(p_t^T || p_s^T)."""
    torch.manual_seed(tohum)
    opt = torch.optim.Adam(ogrenci.parameters(), lr=lr)
    n = len(X)
    for _ in range(epoch):
        perm = torch.randperm(n)
        for i in range(0, n, 64):
            idx = perm[i : i + 64]
            s = ogrenci(X[idx])
            ce = F.cross_entropy(s, y[idx])
            kl = F.kl_div(
                F.log_softmax(s / T, dim=1),
                F.softmax(ogretmen_logit[idx] / T, dim=1),
                reduction="batchmean",
            )
            kayip = (1 - alfa) * ce + alfa * T * T * kl
            opt.zero_grad()
            kayip.backward()
            opt.step()
    return ogrenci
```

Aşağıdaki ana fonksiyon her tohum için öğretmeni eğitir, öğrenciyi sıfırdan ve damıtarak eğitir, sonuçları CSV'ye yazar. Aynı ağ mimarisi ve aynı tohum kullanıldığı için karşılaştırma adildir.

```python
def parametre(m):
    return sum(p.numel() for p in m.parameters())
```

```python
def main():
    satirlar = []
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        ogretmen = mlp_t(t, gizli=(512, 512))
        egit(ogretmen, Xtr, ytr, tohum=t)
        ogretmen.eval()
        with torch.no_grad():
            zt = ogretmen(Xtr)
        ogr_acc = dogruluk(ogretmen, Xte, yte)
        ogr_p = parametre(ogretmen)
        satirlar.append(
            dict(
                yontem="ogretmen_512_512",
                tohum=t,
                dogruluk=round(ogr_acc, 4),
                parametre=ogr_p,
            )
        )
```

```python
        # Sifirdan egitilmis ogrenci (ayni mimari, sadece CE)
        sif = mlp_t(t, gizli=(32,))
        egit(sif, Xtr, ytr, tohum=t)
        satirlar.append(
            dict(
                yontem="ogrenci_sifirdan",
                tohum=t,
                dogruluk=round(dogruluk(sif, Xte, yte), 4),
                parametre=parametre(sif),
            )
        )
```

```python
        for T in [2, 4, 8]:
            o = mlp_t(t, gizli=(32,))
            damit_egit(o, Xtr, ytr, zt, T=T, alfa=0.5, tohum=t)
            satirlar.append(
                dict(
                    yontem="ogrenci_damitma_T%d" % T,
                    tohum=t,
                    dogruluk=round(dogruluk(o, Xte, yte), 4),
                    parametre=parametre(o),
                )
            )
        for s in satirlar[-5:]:
            print(
                s["yontem"], s["tohum"], s["dogruluk"], s["parametre"]
            )
```

```python
    yol = os.path.join(VERI, "b75_damitma.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yol)
```

```python
if __name__ == "__main__":
    torch.set_num_threads(4)
    main()
```

Betiğin çıktısı, her tohum için öğretmen ve öğrenci doğruluklarını gösterir.

```term
$ python b75_damitma.py
ogretmen_512_512 0 0.9722 301066
ogrenci_sifirdan 0 0.9648 2410
ogrenci_damitma_T2 0 0.9574 2410
ogrenci_damitma_T4 0 0.9574 2410
ogrenci_damitma_T8 0 0.9574 2410
ogretmen_512_512 1 0.9759 301066
ogrenci_sifirdan 1 0.9574 2410
ogrenci_damitma_T2 1 0.9537 2410
ogrenci_damitma_T4 1 0.9537 2410
ogrenci_damitma_T8 1 0.9537 2410
ogretmen_512_512 2 0.9796 301066
ogrenci_sifirdan 2 0.9611 2410
ogrenci_damitma_T2 2 0.9537 2410
ogrenci_damitma_T4 2 0.95 2410
ogrenci_damitma_T8 2 0.9556 2410
CSV yazildi: D:/Mevcut Projeler/Kitap/engine/veri\b75_damitma.csv
```

Üç tohumun ortalaması CSV'den özetlenir.

```term
== Damitma (test dogrulugu) ==
ogretmen_512_512         0.9759 +- 0.0030  (n=3)
ogrenci_sifirdan         0.9611 +- 0.0030  (n=3)
ogrenci_damitma_T2       0.9549 +- 0.0017  (n=3)
ogrenci_damitma_T4       0.9537 +- 0.0030  (n=3)
ogrenci_damitma_T8       0.9556 +- 0.0015  (n=3)
```

Şekil 75.6 aynı sonucu çubuk grafikle gösterir.

![Şekil 75.6: Öğrenci doğruluğu: öğretmen, sıfırdan eğitilen öğrenci ve üç sıcaklıkta damıtılmış öğrenci (3 tohum ortalaması ± sapma)](gorseller/b75_damitma_sonuc.png)

Sonuç beklediğimiz gibi değil ve bunu olduğu gibi yazıyorum. Öğretmen 0,9759 ile en yüksek doğruluğa sahip. Sıfırdan eğitilmiş öğrenci 0,9611 ile onun hemen altında, ve bu 2 410 parametreli bir model için zaten çok iyi. Damıtılmış öğrenciler ise 0,9537 ile 0,9556 arasında, yani sıfırdan öğrenciden hafifçe **kötü**. Fark, tohum sapmasının (0,0015 ile 0,0030) iki katı kadar, yani küçük ama tutarlı.

Bu sonucu nasıl okumalıyız? Birincisi, bu görev damıtma için uygun bir ölçek değil. Digits 8 × 8'lik ve kolay bir veri kümesi; öğrenci zaten öğretmenin çözdüğü sorunun neredeyse tamamını çözebiliyor. Damıtmanın kazandırdığı şey, öğrencinin öğretmenin "karanlık bilgisini" öğrenmesidir, ama bu görevde öğrenilecek karanlık bilgi çok az. İkincisi, `a = 0,5` ve `T` değerleri ayarlanmadı; bunları test kümesinde en iyi çıkana kadar ayarlasaydık sonuç yapay olurdu. Bu bölümde test kümesini ayar için kullanmamayı tercih ettik. Üçüncüsü, damıtmanın avantajı genellikle daha zor görevlerde ve öğrencinin kapasitesinin öğretmene yakın olmadığı durumlarda görülür; bu deney o koşulları sağlamıyor.

Derste ve mülakatta bu soruya verilecek doğru cevap şudur: damıtma bedava değildir. Öğrenci mimarisi, sıcaklık ve kayıp ağırlığı ayarlanmalı, sonuç ayrı bir doğrulama kümesinde ölçülmeli ve her zaman sıfırdan eğitilmiş aynı boyuttaki modelle karşılaştırılmalıdır. Bu karşılaştırma yapılmadan "damıtma işe yaradı" demek, bu bölümün ölçüm disiplinine aykırıdır.

## 75.6 Verimli mimariler: daha az işlemle daha çok iş

Kuantizasyon ve budama, var olan bir modeli sıkıştırır. Verimli mimariler ise daha baştan daha az işlem yapan yapılar tasarlar. Bölüm 66'da konvolüsyonun 9 çarpma-toplama ile bir piksel hesapladığını ve kanal sayısıyla çarpıldığını görmüştük. Bu maliyet, kanal sayısı arttığında hızla büyür.

**Derinlemesine ayrılabilir konvolüsyon** (depthwise separable convolution) bu maliyeti iki adıma böler. Önce **derinlemesine** (depthwise) konvolüsyonda her kanal kendi `k × k` filtresiyle ayrı ayrı işlenir (kanallar birbirine karışmaz). Sonra **noktasal** (pointwise) `1 × 1` konvolüsyonla kanallar karıştırılır. Standart bir konvolüsyonun MAC sayısı `H · W · C_giriş · C_çıkış · k²` iken, ayrılabilir hali `H · W · (C_giriş · k² + C_giriş · C_çıkış)` olur. Örneğin `k = 3`, `C_giriş = C_çıkış = 64` için ayrılabilir maliyetin standarda oranı `1/k² + 1/C_çıkış = 1/9 + 1/64 ≈ 0,127` olur; yani işlem yaklaşık 7,9 kat azalır. MobileNet ailesi bu fikre dayanır; EfficientNet ise ölçeklemeyi (derinlik, genişlik, çözünürlük) dengeli yapar (genel bilgi).

Bu bölümdeki karşılaştırma iki küçük CNN ile iki hazır ağı içerir: standart ve ayrılabilir bir 8 × 8 CNN, ve torchvision'un 224 × 224 girdili MobileNetV3-Small ve ResNet-18 modelleri. Parametre ve MAC sayıları hook ile ölçülür; gecikme aynı yöntemle (ısınma, medyan, p95) alınır.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: parametre, MAC ve gecikme karsilastirmasi.
Standart konvolusyon ile derinlemesine ayrilabilir konvolusyon
konvolusyon; torchvision MobileNetV3-Small ve ResNet-18 (224x224).
"""

import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tvm
from b75_ortak import mlp, zamanla

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def standart_cnn():
    return nn.Sequential(
        nn.Conv2d(1, 32, 3, padding=1),
        nn.ReLU(),
        nn.Conv2d(32, 64, 3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(64 * 4 * 4, 10),
    )


def ayrilabilir_cnn():
    """Ikinci konvolusyon: 32 kanalli DW 3x3 + 1x1 PW (64 kanal)."""
    return nn.Sequential(
        nn.Conv2d(1, 32, 3, padding=1),
        nn.ReLU(),
        nn.Conv2d(32, 32, 3, padding=1, groups=32),
        nn.ReLU(),
        nn.Conv2d(32, 64, 1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(64 * 4 * 4, 10),
    )
```

```python
def mac_say(model, x):
    """Conv2d ve Linear katmanlarinda MAC: kanca ile cikis boyutundan.
    """
    toplam = [0]

    def kanca(m, g, c):
        # c: cikti tensoru, batch=1 varsayimi (N=1)
        if isinstance(m, nn.Conv2d):
            kh, kw = m.kernel_size
            yer = c.shape[2] * c.shape[3]  # H_cikis * W_cikis
            toplam[0] += (
                m.out_channels
                * yer
                * (m.in_channels // m.groups)
                * kh
                * kw
            )
        elif isinstance(m, nn.Linear):
            konum = int(np.prod(c.shape[1:-1])) if c.dim() > 2 else 1
            toplam[0] += m.in_features * m.out_features * konum

    kancalar = [
        m.register_forward_hook(kanca)
        for m in model.modules()
        if isinstance(m, (nn.Conv2d, nn.Linear))
    ]
    with torch.no_grad():
        model(x)
    for k in kancalar:
        k.remove()
    return toplam[0]
```

```python
def parametre(model):
    return sum(p.numel() for p in model.parameters())


def olc(ad, model, x, n=300, isinma=30):
    model.eval()
    with torch.no_grad():
        med, p95 = zamanla(lambda: model(x), n=n, isinma=isinma)
    return dict(
        model=ad,
        parametre=parametre(model),
        mac=mac_say(model, x),
        giris=str(tuple(x.shape)[1:]),
        medyan_ms=round(med, 4),
        p95_ms=round(p95, 4),
    )
```

```python
if __name__ == "__main__":
    torch.set_num_threads(4)
    torch.manual_seed(0)
    satirlar = []
    satirlar.append(
        olc("MLP_64_256_128_10", mlp().eval(), torch.randn(1, 64))
    )
    satirlar.append(
        olc(
            "CNN_standart",
            standart_cnn().eval(),
            torch.randn(1, 1, 8, 8),
        )
    )
    satirlar.append(
        olc(
            "CNN_ayrilabilir",
            ayrilabilir_cnn().eval(),
            torch.randn(1, 1, 8, 8),
        )
    )
```

```python
    x224 = torch.randn(1, 3, 224, 224)
    satirlar.append(
        olc(
            "MobileNetV3_Small",
            tvm.mobilenet_v3_small(weights=None).eval(),
            x224,
            n=100,
            isinma=10,
        )
    )
    satirlar.append(
        olc(
            "ResNet18",
            tvm.resnet18(weights=None).eval(),
            x224,
            n=60,
            isinma=5,
        )
    )
    for s in satirlar:
        print(s)
    yol = os.path.join(VERI, "b75_mimari.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yol)
```

Betik her model için parametre, MAC ve gecikmeyi CSV'ye yazar. Aşağıdaki tablo bu CSV'yi `b75_goster.py` ile okur; ölçüm bu tablo için yeniden yapılmadı.

```term
$ python b75_goster.py mimari
model                 parametre        MAC  medyan  p95
MLP_64_256_128_10         50826        50432  0.0399  0.0837
CNN_standart              29066      1208320  0.1477  0.3178
CNN_ayrilabilir           13002       178176  0.3376  0.5867
MobileNetV3_Small       2542856     56510400 10.3836 12.7717
ResNet18               11689512   1814073344  27.728  33.807
```

Şekil 75.7 bu verileri üç panelde gösterir: parametre, MAC ve gecikme. Üç panelin de logaritmik ölçekte olduğuna dikkat et; modeller arasındaki fark birkaç büyüklük mertebesi tutar.

![Şekil 75.7: Parametre, MAC ve gecikme: MLP, standart ve ayrılabilir CNN, MobileNetV3-Small ve ResNet-18 (log ölçek)](gorseller/b75_mimari.png)

Tablo iki gözlemi açıkça ortaya koyuyor. Birincisi, ayrılabilir CNN, standart CNN'e göre 6,8 kat daha az MAC yapıyor (178 176'ya karşılık 1 208 320) ve 13 002 parametresi var (standart: 29 066). Ama CPU'da gecikmesi daha **yüksek**: 0,34 ms'ye karşılık 0,15 ms. İkincisi, MobileNetV3-Small, ResNet-18'e göre 32 kat daha az MAC yapıyor (56,5 milyona karşılık 1,81 milyar) ve yaklaşık 2,7 kat daha hızlı (10,4 ms'ye karşılık 27,7 ms). MAC oranı 32, gecikme oranı 2,7: bu iki oran hiçbir zaman birbirine eşit olmuyor.

İlk gözlem, MAC sayısının gecikmenin tek belirleyicisi olmadığını gösterir. Ayrılabilir konvolüsyonun derinlemesine adımı, kanal başına küçük işler yapar; bunlar vektör birimlerini tam kullanamaz ve bellek erişimi düzensizleşir. Ayrıca bu küçük ağda çekirdek başlatma (kernel launch) ve Python yükü, işlemin kendisinden daha büyük olabilir. Bu nedenle "MAC düştü, o hâlde hızlanır" varsayımı yanlış olabilir; doğrusu ölçmektir. Bu, bölümün ölçüm disiplininin en somut nedenidir.

İkinci gözlem, MobileNet'in ResNet'e göre neden daha az kazanç verdiği (ve yine de hızlı olduğu) sorusudur. Bunu bu bölümde ayrıca ölçmedik; olası bir açıklama, parametre sayısının 2,5 milyon ile 11,7 milyon arasında olması ve ara aktivasyon belleğinin farklı olmasıdır. Edge'de MAC ile bellek baytı birlikte okunmalıdır.

Son olarak, gerçek bir gömülü hedef için bu sayılar yeterli değildir: Cortex-M4 gibi bir işlemcide MobileNet'in bile flash ve RAM bütçesi, 224 × 224 girdi ile aşılır. Bu yüzden mikrodenetleyicilerde girdi çözünürlüğünü ve kanal sayısını baştan küçülten ağlar tasarlanır .

## 75.7 Dağıtım biçimleri: eğitimden cihaza

Eğitilmiş bir model çoğu zaman eğitim betiği ve PyTorch çalışma zamanı olmadan çalışmak zorundadır: bir C++ servisinde, bir mobil uygulamada, bir ONNX çalışma zamanında ya da bir mikrodenetleyicide. Bölüm 65'te TorchScript ve `torch.export` ile bu ayrımın ilk adımını atmıştık. Bu bölümde dağıtım hattının tamamına bakıyoruz.

Hattın dört aşaması vardır. **Eğitim** PyTorch'ta yapılır. **Dışa aktarma** modeli bağımsız bir biçime (ONNX) çevirir. **Çalışma zamanı** (ONNX Runtime, TensorRT gibi) bu biçimi hedef donanımda çalıştırır. **Cihaz** ise son donanımdır: CPU, GPU ya da MCU. Her geçişte graf optimizasyonları ve kuantizasyon uygulanabilir; her geçiş ayrıca bir doğrulama noktasıdır.

![Şekil 75.8: Dağıtım hattı: eğitimden cihaza her adım bir dönüşüm ve bir doğrulama noktasıdır](gorseller/b75_dagitim_hatti.png)

Bu hattın en sık yapılan hatası, dışa aktarılan modelin orijinaliyle aynı davrandığını varsaymaktır. Bölüm 65'te söylediğimiz gibi, eğitimde kullanılan ama dışa aktarımda desteklenmeyen bir işlem fark edilmeyebilir. Bu yüzden her aşamada aynı girdiyle sayısal karşılaştırma yapmak gerekir. Aşağıdaki betik bunu yapar: önce bir MLP'yi ONNX'e çevirip ONNX Runtime ile PyTorch'un çıktısını karşılaştırır, sonra PyTorch'un dinamik int8 kuantizasyonunun ONNX karşılığını üretir. İkinci bölümde, bir Conv ve BatchNorm çiftinin nasıl tek bir konvolüsyona katlandığını da gösterir.

ONNX (Open Neural Network Exchange), ağı işlemlerden oluşan bir graf olarak tanımlayan açık bir biçimdir. `torch.onnx.export` bir modeli bu grafa çevirir; `opset_version` işlem kümesinin sürümünü belirler. Bu bölümde 17 kullandık.

Betiğin ilk yarısı MLP'nin dışa aktarımını yapar. Sayısal karşılaştırma için ONNX Runtime'da CPU sağlayıcısı kullanılır. Ayrıca `onnx.checker` ile graf geçerliliği denetlenir.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: ONNX disa aktarma, ONNX Runtime ile sayisal eslesme,
BatchNorm katlama (sifirdan) ve calisma zamani graf optimizasyonu."""

import os
import numpy as np
import torch
import torch.nn as nn
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
from b75_ortak import veri, mlp_t, egit, dogruluk

KLASOR = "C:/Users/merty/AppData/Local/Temp/b75/onnx"
```

```python
def bn_katla(conv, bn):
    """Conv2d + BatchNorm2d (egitim sonrasi, eval modu) -> tek Conv2d.
    s = gamma / sqrt(var + eps); W' = W * s; b' = (b - mu) * s + beta.
    """
    s = bn.weight / torch.sqrt(bn.running_var + bn.eps)
    yeni = nn.Conv2d(
        conv.in_channels,
        conv.out_channels,
        conv.kernel_size,
        stride=conv.stride,
        padding=conv.padding,
        bias=True,
    )
    b = (
        conv.bias
        if conv.bias is not None
        else torch.zeros_like(bn.running_mean)
    )
    with torch.no_grad():
        yeni.weight.copy_(conv.weight * s.view(-1, 1, 1, 1))
        yeni.bias.copy_((b - bn.running_mean) * s + bn.bias)
    return yeni
```

```python
def op_say(yol):
    m = onnx.load(yol)
    sayac = {}
    for n in m.graph.node:
        sayac[n.op_type] = sayac.get(n.op_type, 0) + 1
    return sayac


def ort_calistir(yol, X):
    s = ort.InferenceSession(yol, providers=["CPUExecutionProvider"])
    ad = s.get_inputs()[0].name
    return s.run(None, {ad: X})[0]
```

```python
def mlp_testi():
    print("== 1) MLP: PyTorch -> ONNX -> ONNX Runtime ==")
    Xtr, ytr, Xte, yte = veri(0)
    m = mlp_t(0)
    egit(m, Xtr, ytr, tohum=0)
    m.eval()
    yol = os.path.join(KLASOR, "mlp.onnx")
    torch.onnx.export(
        m,
        torch.randn(1, 64),
        yol,
        opset_version=17,
        input_names=["giris"],
        output_names=["cikis"],
        dynamic_axes={"giris": {0: "B"}, "cikis": {0: "B"}},
        dynamo=False,
    )
```

```python
    onnx.checker.check_model(onnx.load(yol))
    with torch.no_grad():
        py = m(Xte).numpy()
    ox = ort_calistir(yol, Xte.numpy())
    print("en buyuk mutlak fark: %.3e" % np.abs(py - ox).max())
    print(
        "cikti buyuklugu max|y|: %.3f  bagil fark: %.3e"
        % (np.abs(py).max(), np.abs(py - ox).max() / np.abs(py).max())
    )
    print(
        "ONNX dogruluk: %.4f  PyTorch dogruluk: %.4f"
        % (
            (ox.argmax(1) == yte.numpy()).mean(),
            dogruluk(m, Xte, yte),
        )
    )
```

```python
    print("op sayilari:", op_say(yol))
    yol8 = os.path.join(KLASOR, "mlp_int8.onnx")
    quantize_dynamic(yol, yol8, weight_type=QuantType.QInt8)
    o8 = ort_calistir(yol8, Xte.numpy())
    print(
        "ORT dinamik int8 dogruluk: %.4f  boyut: %d -> %d bayt"
        % (
            (o8.argmax(1) == yte.numpy()).mean(),
            os.path.getsize(yol),
            os.path.getsize(yol8),
        )
    )
```

```python
def bn_testi():
    print("== 2) Conv + BatchNorm katlama ==")
    torch.manual_seed(0)
    conv = nn.Conv2d(1, 8, 3, padding=1)
    bn = nn.BatchNorm2d(8)
    with torch.no_grad():  # egitilmis gibi ayarla
        bn.weight.uniform_(0.5, 1.5)
        bn.bias.uniform_(-0.3, 0.3)
        bn.running_mean.uniform_(-0.2, 0.2)
        bn.running_var.uniform_(0.5, 2.0)
    bn.eval()
    conv.eval()
    kat = bn_katla(conv, bn).eval()
    x = torch.randn(4, 1, 8, 8)
    with torch.no_grad():
        fark = (bn(conv(x)) - kat(x)).abs().max().item()
    print("katlama oncesi/sonrasi en buyuk fark: %.3e" % fark)
```

```python
    yol_a = os.path.join(KLASOR, "conv_bn.onnx")
    yol_b = os.path.join(KLASOR, "conv_katli.onnx")
    seq = nn.Sequential(conv, bn)
    torch.onnx.export(
        seq,
        x,
        yol_a,
        opset_version=17,
        dynamo=False,
        do_constant_folding=False,
    )
    torch.onnx.export(
        kat,
        x,
        yol_b,
        opset_version=17,
        dynamo=False,
        do_constant_folding=False,
    )
    print("ONNX (katlanmamis):", op_say(yol_a))
    print("ONNX (katli)      :", op_say(yol_b))
```

```python
    so = ort.SessionOptions()
    so.graph_optimization_level = (
        ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    )
    so.optimized_model_filepath = os.path.join(
        KLASOR, "conv_bn_opt.onnx"
    )
    ort.InferenceSession(
        yol_a, so, providers=["CPUExecutionProvider"]
    )
    print(
        "ORT ENABLE_ALL sonrasi (katlanmamis):",
        op_say(so.optimized_model_filepath),
    )
    oa = ort_calistir(yol_a, x.numpy())
    ob = ort_calistir(yol_b, x.numpy())
    print(
        "ORT: katlanmamis ile katli fark: %.3e"
        % np.abs(oa - ob).max()
    )
```

```python
if __name__ == "__main__":
    torch.set_num_threads(4)
    os.makedirs(KLASOR, exist_ok=True)
    mlp_testi()
    bn_testi()
```

Betik çalıştığında şunları yazar. İlk satır, en büyük mutlak farkı verir; ikinci satır, bu farkın çıktının büyüklüğüne oranını gösterir.

```term
$ python b75_onnx.py
== 1) MLP: PyTorch -> ONNX -> ONNX Runtime ==
en buyuk mutlak fark: 1.144e-05
cikti buyuklugu max|y|: 26.998  bagil fark: 4.239e-07
ONNX dogruluk: 0.9722  PyTorch dogruluk: 0.9722
op sayilari: {'Gemm': 3, 'Relu': 2}
ORT dinamik int8 dogruluk: 0.9704  boyut: 203963 -> 55206 bayt
== 2) Conv + BatchNorm katlama ==
katlama oncesi/sonrasi en buyuk fark: 4.768e-07
ONNX (katlanmamis): {'Conv': 1, 'BatchNormalization': 1}
ONNX (katli)      : {'Conv': 1}
ORT ENABLE_ALL sonrasi (katlanmamis): {'Conv': 1, 'ReorderOutput': 1}
ORT: katlanmamis ile katli fark: 4.768e-07
```

Sonuçlar birkaç nokta içerir. PyTorch ile ONNX Runtime arasındaki en büyük mutlak fark 1,144 · 10⁻⁵'tir. Bu, `1e-5` eşiğinin hemen üstünde bir değer; ama çıktıların büyüklüğü 27 olduğu için bağıl fark `4,2 · 10⁻⁷`'dir ve bu, fp32 aritmetiğinin beklenen hassasiyetidir. Eşiği mutlak fark olarak koyduysak bu sonuç başarısız sayılır; bağıl farkla bakarsak başarılıdır. Betik bir eşik denetimi yapmaz; ama mutlak fark `1e-5` değerinin hemen üstündedir. Gerçek bir sistemde hangi ölçütün kullanılacağına, çıktının ölçeğine göre önceden karar vermek gerekir.

ONNX Runtime'daki dinamik int8 kuantizasyon, dosyayı 203 963 baytan 55 206 bayta düşürüyor (yaklaşık 3,7 kat) ve doğruluğu 0,9722'den 0,9704'e çekiyor. Bu, 540 örnekte iki örnek farktır ve gürültü düzeyindedir.

### Graf optimizasyonu ve BatchNorm katlama

Bir sinir ağı bir graf olarak çalıştırıldığında, birbirini izleyen işlemler (örneğin bir konvolüsyon, ardından BatchNorm, ardından ReLU) her biri ayrı bir çağrı olarak yürütülür ve her ara sonucu belleğe yazar. **Operatör birleştirme** (operator fusion) bu işlemleri tek bir çekirdekte birleştirir: ara bellek yazımı kalkar ve çağrı yükü azalır. Bunun en basit ve en yaygın hâli Conv + BatchNorm katlamasıdır.

Eğitim sonrasında BatchNorm, eğitim boyunca toplanmış ortalama `μ`, varyans `σ²`, ölçek `γ` ve kayma `β` ile sabit bir doğrusal dönüşümdür: `γ · (x − μ) / √(σ² + ε) + β`. Konvolüsyon ise `W · x + b` hesaplar. İkisi ardı ardına uygulandığında, aynı sonuç tek bir konvolüsyonla elde edilebilir:

s = γ / √(σ² + ε)
W' = W · s
b' = (b − μ) · s + β

Bu katlama, çıktıyı değiştirmez; yalnızca grafı küçültür ve BatchNorm'un çalışma zamanındaki maliyetini ortadan kaldırır. Katlamanın doğru olduğunu yukarıdaki betik, rastgele istatistiklerle ayarlanmış bir Conv + BatchNorm çiftinde ölçer: katlamadan önce ve sonra en büyük mutlak fark `4,8 · 10⁻⁷` çıkar. Ayrıca ONNX dışa aktarımında, katlanmamış modelde `BatchNormalization` düğümü görülürken, katlanmış modelde yalnızca `Conv` düğümü kalır. Torch'un dışa aktarıcısı varsayılan olarak sabit katlamayı kendisi yapabilir; bu yüzden katlanmamış modeli görmek için betikte `do_constant_folding=False` kullanıldı.

ONNX Runtime'ın kendi graf optimizasyonu da bu katlamayı yapar. `ORT_ENABLE_ALL` ile kaydedilen optimize edilmiş modelde `Conv` ve `ReorderOutput` düğümleri görülür; `ReorderOutput`, ORT'nin kendi bellek düzeni (NCHWc) dönüşümünden kalır ve bu makineye özgüdür. Yani optimize edilmiş bir model dosyası, başka bir donanımda kullanılmamalıdır. Bu, dağıtımda sık gözden kaçan bir ayrıntıdır.

![Şekil 75.9: Conv ve BatchNorm katlama: istatistikler ağırlıklara gömülür, çıktı değişmez](gorseller/b75_bn_katlama.png)

### TensorRT ve Jetson: kavram ve çalıştırılmamış kod

NVIDIA'nın TensorRT'si, bir ONNX grafını hedef GPU'ya özgü bir motora (engine) derler. Derleme sırasında katman birleştirme, çekirdek seçimi ve hassasiyet seçimi yapılır; FP16 ve INT8 bu aşamada uygulanır. INT8 için derleyici, temsili bir kalibrasyon verisiyle aktivasyon aralıklarını ölçen bir kalibratöre ihtiyaç duyar; bu, PTQ'daki kalibrasyon ile aynı mantıktır. Jetson, aynı yazılım yığınını (JetPack ile birlikte gelen TensorRT dahil) gömülü bir kart üzerinde çalıştıran platformdur (genel bilgi).

Bu bölümde TensorRT ve Jetson üzerinde çalışmadık: makinede NVIDIA GPU'yu paylaşımlı kullanmıyoruz ve TensorRT kurulu değil. Aşağıdaki kod, TensorRT 10 API'si için bir şablondur; **çalıştırılmadı**. Ayrıntılar sürüme göre değişir; üretimde kendi sürümünün belgelerine bak.

```python
# CALISTIRILMADI: TensorRT 10 API sablonu (genel bilgi).
import tensorrt as trt

logger = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(logger)
network = builder.create_network(0)
parser = trt.OnnxParser(network, logger)
with open("mlp.onnx", "rb") as f:
    if not parser.parse(f.read()):
        for k in range(parser.num_errors):
            print(parser.get_error(k))
        raise SystemExit("ONNX ayristirma hatasi")

config = builder.create_builder_config()
config.set_flag(trt.BuilderFlag.FP16)
# INT8 icin kalibrator gerekir:
# config.set_flag(trt.BuilderFlag.INT8)
# config.int8_calibrator = kalibrator
plan = builder.build_serialized_network(network, config)
with open("mlp_fp16.plan", "wb") as f:
    f.write(plan)
```

Bu kodda `parse` başarısız olursa hata mesajlarını yazdırmak önemli bir alışkanlıktır. Çoğu dağıtım hatası, derleme sırasında değil ayrıştırma sırasında ortaya çıkar: ONNX işlem kümesi (opset) sürümü ya da desteklenmeyen bir işlem nedeniyle.

Dağıtımda ikinci bir uyarı da, motorun derlendiği GPU'ya özgü olmasıdır. Bir motoru bir GPU'da derleyip başka bir modelde çalıştırmak genellikle olanaksızdır; bu yüzden hedef donanımın kendisinde derleme yapılır.

## 75.8 Mikrodenetleyici hattı: int8 MLP'den Cortex-M4'e

Bölüm 46'da bir mikrodenetleyicide çalışan bir sinyal sınıflandırıcısının tam hattını gördük: veri, eğitim, kuantizasyon, C çekirdeği, konakta bit-tam doğrulama ve Cortex-M4 derlemesi. Orada modelin çıkarım kodu elle yazılmış bir C dosyasıydı ve bellek haritasını bir bağlayıcı betiği tanımlıyordu. Bu bölümde aynı hattı yalnızca tek bir yeniden ölçeklemeyle, kendi küçük MLP'miz için tekrarlıyoruz. Yeni olan kısım, kuantizasyon ayarlarının C'ye ve Python referansına birebir taşınmasıdır.

Model, 64 girdi, 32 gizli nöron ve 10 çıktıdan oluşan bir MLP'dir (2 410 parametre). Ağırlıklar tensör başına simetrik int8'e çevrilir; girdi `[0, 1]` aralığından `1/127` ölçekle int8'e alınır; gizli aktivasyonların ölçeği eğitim verisinin son 200 örneğinden kalibre edilir. Üretici betik, bu değerleri iki C başlığına yazar: `model_w.h` ağırlıkları ve bias'ları, `test_vektor.h` ise ilk 50 test örneğini ve Python'un beklenen tamsayı logit'lerini içerir. Python'daki yuvarlama ve yeniden ölçekleme, C'deki işlem sırasıyla birebir aynıdır: tamsayı birikim, float32 çarpım, sıfırdan uzağa yuvarlama, ardından ReLU.

Bu eşleşme neden önemli? Bir C çekirdeği yanlış çalıştığında, hatanın nerede olduğunu bilmek zordur: ağırlık mı, ölçek mi, taşma mı, yuvarlama mı? Python referansı ile C'nin logit'lerinin bit bit aynı olması, bu katmanların her birini ayrı ayrı dışlar. Aşağıdaki üretici betik, eğitimden başlayarak bu iki başlığı üretir.

```python
# -*- coding: utf-8 -*-
"""Bolum 75: 64-32-10 MLP'nin int8 MCU surumu icin
agirliklari ve test vektorlerini C basligina yazar; referans ayni
float32 islem sirasiyla gecen tamsayi sonuclarini uretir."""

import os, sys
import numpy as np
import torch

sys.path.insert(0, "C:/Users/merty/AppData/Local/Temp/b75")
from b75_ortak import veri, mlp_t, egit, dogruluk

HERE = os.path.dirname(os.path.abspath(__file__))
```

```python
def yuvarla(v):
    """Sifirdan uzaga yuvarlama (C'deki round_away ile birebir)."""
    v = np.asarray(v, dtype=np.float32)
    return np.where(
        v >= 0,
        np.floor(v + np.float32(0.5)),
        -np.floor(-v + np.float32(0.5)),
    ).astype(np.int32)


def kirp8(v):
    return np.clip(v, -127, 127).astype(np.int32)


def olcek(x):
    """Simetrik tensor olcegi: max|x| / 127."""
    return np.float32(np.max(np.abs(x)) / 127.0)
```

```python
def main():
    Xtr, ytr, Xte, yte = veri(0)
    m = mlp_t(0, gizli=(32,))
    egit(m, Xtr, ytr, tohum=0)
    m.eval()
    print("fp32 test dogruluk: %.4f" % dogruluk(m, Xte, yte))
    W1 = m[0].weight.detach().numpy().astype(np.float32)
    b1 = m[0].bias.detach().numpy().astype(np.float32)
    W2 = m[2].weight.detach().numpy().astype(np.float32)
    b2 = m[2].bias.detach().numpy().astype(np.float32)
    # Kalibrasyon: egitim verisinin son 200 ornegi (test verisi degil)
    Xcal = Xtr[-200:].numpy().astype(np.float32)
    sx = np.float32(1.0 / 127.0)  # girdi (0..1) -> int8
    sw1, sw2 = olcek(W1), olcek(W2)
    h = np.maximum(Xcal @ W1.T + b1, 0)
    sa = olcek(h)  # gizli aktivasyon olcegi
    Wq1 = kirp8(yuvarla(W1 / sw1))
    Wq2 = kirp8(yuvarla(W2 / sw2))
    bq1 = yuvarla(b1 / (sx * sw1))
    bq2 = yuvarla(b2 / (sa * sw2))
    M1 = np.float32(sx * sw1 / sa)  # yeniden olcekleme carpani
```

```python
    # Referans: int8 ileri gecis (C ile ayni islem sirasi)
    def ileri(xq):
        acc1 = xq.astype(np.int32) @ Wq1.T.astype(np.int32) + bq1
        v = acc1.astype(np.float32) * M1
        hq = np.maximum(kirp8(yuvarla(v)), 0)
        acc2 = hq @ Wq2.T.astype(np.int32) + bq2
        return acc2
```

```python
    Xq = kirp8(yuvarla(Xte.numpy() / sx))
    logit = np.array(
        [ileri(Xq[i : i + 1])[0] for i in range(len(Xq))]
    )
    etiket = logit.argmax(1)
    print("int8 test dogruluk: %.4f" % (etiket == yte.numpy()).mean())
```

```python
    # C basligi: agirliklar
    with open(
        os.path.join(HERE, "model_w.h"), "w", encoding="utf-8"
    ) as f:
        f.write("/* otomatik uretildi: gen_mcu.py */\n")
        f.write(
            "#define M1_BOYUT 64\n#define H_BOYUT 32\n#define "
            "C_BOYUT 10\n"
        )
        f.write("static const int8_t W1[32][64] = {\n")
        for r in Wq1:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write(
            "};\nstatic const int32_t B1[32] = {"
            + ",".join(str(int(v)) for v in bq1)
            + "};\n"
        )
        f.write("static const int8_t W2[10][32] = {\n")
        for r in Wq2:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write(
            "};\nstatic const int32_t B2[10] = {"
            + ",".join(str(int(v)) for v in bq2)
            + "};\n"
        )
        f.write("static const float M1 = %.9gf;\n" % float(M1))
```

```python
    # C basligi: test vektorleri (ilk 50), beklenen logit ve etiket
    n = 50
    with open(
        os.path.join(HERE, "test_vektor.h"), "w", encoding="utf-8"
    ) as f:
        f.write(
            "/* otomatik uretildi: gen_mcu.py */\n#define N_TEST 50\n"
        )
        f.write("static const int8_t XT[N_TEST][64] = {\n")
        for r in Xq[:n]:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write(
            "};\nstatic const int32_t YT[N_TEST] = {"
            + ",".join(str(int(v)) for v in yte.numpy()[:n])
            + "};\n"
        )
        f.write("static const int32_t LT[N_TEST][10] = {\n")
        for r in logit[:n]:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write("};\n")
    print("yazildi: model_w.h, test_vektor.h")
```

```python
if __name__ == "__main__":
    torch.set_num_threads(4)
    main()
```

Bu betik yalnızca başlıkları ve referans sonuçlarını yazar. Çalıştırdığında şunu görürsün.

```term
$ python gen_mcu.py
fp32 test dogruluk: 0.9648
int8 test dogruluk: 0.9648
yazildi: model_w.h, test_vektor.h
```

Görülen fp32 ve int8 doğrulukları aynı (0,9648). Bu, test kümesinde 540 örnekte iki doğrulukun da tam olarak aynı sayıda örneği doğru bildiği anlamına gelir; küçük bir model ve tensör başına ölçekle bu beklenen bir sonuçtur.

C çekirdeği, tek bir fonksiyon olarak yazılmıştır: `mlp_cikar`. Birikim için 32 bitlik tamsayı kullanır; 64 girdi ve en büyük 127 · 127 çarpımla bile tamsayı taşması olmaz (64 · 16 129 = 1 032 256, int32 sınırının çok altında). Yeniden ölçekleme bir float32 çarpımdır ve Cortex-M4'ün tek duyarlıklı FPU'su bunu donanımda yapar. Derleyiciye `-ffp-contract=off` verilir, böylece çarpım ile toplama birleştirilip sonuç değiştirilmez.

```c
/* mlp_int8.c - 64-32-10 int8 MLP cikarimi (W8A8, tensor olcegi).
 * Python referansi (gen_mcu.py) ile birebir ayni islem sirasi:
 * tamsayi birikim, float32 yeniden olcekleme, yuvarlama. */
#include <stdint.h>
#include "model_w.h"

static int32_t sat8(int32_t v)
{
    if (v > 127) return 127;
    if (v < -127) return -127;
    return v;
}
```

```c
/* Sifirdan uzaga yuvarlama (round half away from zero). */
static int32_t yuvarla(float v)
{
    if (v >= 0.0f) return (int32_t)(v + 0.5f);
    return -(int32_t)(-v + 0.5f);
}
```

```c
/* x: 64 int8 girdi. logit: 10 skor. Donus: tahmin edilen sinif. */
int mlp_cikar(const int8_t x[64], int32_t logit[10])
{
    int8_t h[H_BOYUT];
    int en = 0;

    for (int j = 0; j < H_BOYUT; ++j) {
        int32_t acc = B1[j];
        for (int i = 0; i < M1_BOYUT; ++i)
            acc += (int32_t)W1[j][i] * (int32_t)x[i];
        int32_t q = sat8(yuvarla((float)acc * M1));
        h[j] = (int8_t)(q > 0 ? q : 0);          /* ReLU */
    }
    for (int k = 0; k < C_BOYUT; ++k) {
        int32_t acc = B2[k];
        for (int j = 0; j < H_BOYUT; ++j)
            acc += (int32_t)W2[k][j] * (int32_t)h[j];
        logit[k] = acc;
    }
    for (int k = 1; k < C_BOYUT; ++k)
        if (logit[k] > logit[en]) en = k;
    return en;
}
```

Konak testi, bu çekirdeği C derleyicisinin ana bilgisayardaki (WSL'de Ubuntu gcc 13.3) sürümüyle derler ve Python'un ürettiği 50 test vektörünü çalıştırır. Derleme AddressSanitizer ve UndefinedBehaviorSanitizer ile yapılır; bunlar bellek hatalarını ve tanımsız davranışı (örneğin tamsayı taşması) çalışma anında yakalar. Konak testi, bir C kodunun Cortex-M4 üzerinde de aynı sonucu vereceğini kanıtlamaz; ama ilk ve en ucuz doğrulama adımıdır.

```c
/* test_host.c - konakta bit-tam dogrulama: logit ve etiket Python ile
 * birebir ayni mi? */
#include <stdio.h>
#include <stdint.h>
#include "model_w.h"
#include "test_vektor.h"

int mlp_cikar(const int8_t x[64], int32_t logit[10]);

int main(void)
{
    int bozuk = 0, dogru = 0;
    for (int t = 0; t < N_TEST; ++t) {
        int32_t lg[C_BOYUT];
        int en = mlp_cikar(XT[t], lg);
        for (int k = 0; k < C_BOYUT; ++k)
            if (lg[k] != LT[t][k]) { bozuk++; break; }
        if (en == YT[t]) dogru++;
    }
    printf("logit eslesmesi: %d/%d\n", N_TEST - bozuk, N_TEST);
    printf("dogru etiket: %d/%d\n", dogru, N_TEST);
    return bozuk != 0;
}
```

Hem konak testini hem de Cortex-M4 derlemesini çalıştıran betik aşağıda. Konakta derleme için WSL'nin gcc'si, hedef derleme için STM32CubeIDE ile gelen ARM GNU araç zinciri (arm-none-eabi-gcc 13.3.1) kullanılır.

```bash
#!/bin/bash
# Bolum 75 MCU hatti: konakta bit-tam test ve Cortex-M4 boyutu.
set -e
cd "$(dirname "$0")"
TB="/c/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins"
TB="$TB/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32"
TB="$TB.13.3.rel1.win32_1.0.0.202411081344/tools/bin"
BAY="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16"
BAY="$BAY -Os -ffp-contract=off -ffunction-sections -fdata-sections"
BAY="$BAY -Wall -Wextra -std=c11"
echo "== konak (WSL gcc, ASan+UBSan) =="
wsl bash -lc "cd /mnt/c/Users/merty/AppData/Local/Temp/b75/mcu && \
gcc -O2 -Wall -Wextra -std=c11 -fsanitize=address,undefined \
mlp_int8.c test_host.c -o test_host && ./test_host"
echo "== Cortex-M4 (arm-none-eabi-gcc 13.3.1) =="
"$TB/arm-none-eabi-gcc.exe" $BAY -c mlp_int8.c -o mlp_int8.o
"$TB/arm-none-eabi-size.exe" -A mlp_int8.o
```

Çıktı şöyle.

```term
$ bash derle.sh
== konak (WSL gcc, ASan+UBSan) ==
logit eslesmesi: 50/50
dogru etiket: 49/50
== Cortex-M4 (arm-none-eabi-gcc 13.3.1) ==
mlp_int8.o  :
section           size   addr
.text                0      0
.data                0      0
.bss                 0      0
.text.mlp_cikar    232      0
.rodata.B2          40      0
.rodata.W2         320      0
.rodata.B1         128      0
.rodata.W1        2048      0
.comment            68      0
.ARM.attributes     52      0
Total             2888
```

Konak testinde 50 test vektörünün 50'sinde logit'ler Python'la birebir aynı (bit düzeyinde); 49'unda tahmin edilen sınıf doğru. Sanitizer'lar hiçbir hata bildirmedi.

Cortex-M4 çıktısı, bölüm boyutlarını verir. `.text.mlp_cikar` çekirdeğin makine kodudur (232 bayt). `.rodata` bölümleri, flash'ta duran sabitlerdir: ağırlıklar 2 048 + 320 bayt, bias'lar 128 + 40 bayt. `.data` ve `.bss` sıfırdır: model RAM'de hiçbir yer kaplamaz. Çıkarım sırasında RAM kullanımı, yığında duran gizli aktivasyon dizisi (32 bayt) ve logit dizisi (40 bayt) ile sınırlıdır. Toplam flash ayakizi yaklaşık 2,8 KB'tır. Bölüm 46'daki tam yazılımın `text` boyutu (3 284 bayt) ise bir başka modele aittir; bu büyüklük sıralamasını görmek için karşılaştırılabilir.

Burada bilerek yapmadığımız bir ölçüm var: **çevrim sayısı**. Konakta doğruluk ölçüldü, boyut ölçüldü; ama bir Cortex-M4'te bir çıkarımın kaç çevrim sürdüğü ölçülmedi. Bunu iki yolla yapabilirsin: gerçek kartta DWT çevrim sayacı ile, ya da Unicorn gibi bir emülatörde talimat sayımı ile. İkisi de bu bölümün kapsamı dışında bırakıldı; okuyucuya bir alıştırma olarak bırakılmıştır (Kendin Yap Projesi 2 buna yakındır).

## 75.9 Edge sistem tasarımı: güç, ısı, kare ve güvenlik

Bu bölüme kadar tek tek araçlara baktık. Gerçek bir edge sistemde ise bu araçlar birbirine bağlı kısıtlar altında seçilir. Bir hedef için dört bütçe birlikte düşünülür: **bellek** (flash ve RAM), **gecikme** (bir kararın ne kadar sürede verildiği), **güç ve ısı** (pil ve soğutma), ve **doğruluk** (görev için kabul edilebilir hata). Bu dört kısıt aynı anda sağlanmalıdır; birini iyileştirmek diğerini bozabilir. Örneğin bir modeli büyütmek doğruluğu artırır ama gecikmeyi ve ısıyı yükseltir.

**Güç ve ısı bütçesi.** Bir batarya ile çalışan cihazda her çıkarım bir enerji harcamasıdır. Enerji, güç ile süreyi çarpar. Bu yüzden yalnızca hızlı değil, aynı zamanda az işlem yapan bir model daha değerlidir: aynı doğrulukta daha az MAC, daha az bellek trafiği demektir. Ayrıca kart ısınınca saat hızını düşüren (throttling) bir mekanizma çalışır; bu, ölçülen gecikmeyi zamanla değiştirir. Bu yüzden ölçüm, soğuk başlangıçta ve sıcak durumda ayrı ayrı yapılmalıdır.

**Kare bütçesi.** Bölüm 67'de bir video akışında kare başına 33,3 milisaniyelik bütçeyi (30 kare/saniye) görmüştük. Bu bütçe, yalnızca model çıkarımını değil, görüntünün alınmasını, ön işlemeyi (yeniden boyutlandırma, normalize etme), çıkarımı, son işlemeyi (NMS gibi) ve bir takip adımını da kapsar. Bu bölümdeki her model için yalnızca "çıkarım süresi" yazmak yetmez: hat boyunca her adımın payı ölçülmelidir. Çoğu zaman ön ve son işleme, modelin kendisinden daha pahalı çıkar; Bölüm 41'de edge tarafındaki ön işlemenin neden önemli olduğunu görmüştük.

**Model güncelleme (OTA).** Sahadaki bir cihazın modeli, güncelleme gerektiğinde uzaktan değiştirilebilir. Bu, üç ilkeyi gerektirir: güncelleme paketinin **imzalanması** ve cihazın imzayı doğrulaması, yeni modelin eskisinin yanında **A/B bölümlerinde** tutulması ve doğrulanamayan bir güncelleme durumunda **geri dönüş** (rollback) yapılabilmesi. Bu, kavramsal bir tanımdır; bu bölümde bir OTA sistemi kurmadık ve kurmak için ayrı bir güvenlik tasarımı gerekir (Bölüm 32'deki kriptografi ve Bölüm 78'deki güvenlik konuları bu tasarımın parçalarıdır).

**Savunma bağlamı: İHA üzerinde çıkarım.** Bir İHA'da çıkarım, üç nedenle uçakta yapılır: bağlantı kopabilir, bant genişliği yetmez ve gecikme kararı geciktirir. Ama bu üç neden, yeni bir zorluk getirir. Birincisi **güvenilirlik**: model, kötü bir girdi (bulanık görüntü, güneş parlaması, eksik kare) karşısında nasıl davranır, bunu bilmeden uçurmak kabul edilemez. Bölüm 78 bu konuyu, belirsizlik tahmini ve robustluk ile işleyecek. İkincisi **deterministik gecikme**: bir kararın en kötü durumda kaç milisaniye süreceği (WCET, en kötü durum yürütme süresi) bilinmelidir; ortalama gecikme yetmez, p95 ve p99 kuyruk değerleri asıl sayılardır. Bu bölümdeki p95 ölçümü tam olarak bu yüzden alınır. Üçüncüsü **sertifikasyon**: havacılık yazılımında, bir yazılımın hangi süreçle doğrulandığı ve hangi kanıtla güvenli olduğu bir gerekliliktir (genel bilgi: havacılık yazılım standartları). Bir sinir ağının bu kanıtı nasıl üreteceği açık bir araştırma sorusudur ve bu bölümün kapsamı dışındadır; Bölüm 78'de ele alınacak.

Bu tasarımların ortak sonucu şudur: edge'de en iyi model, en yüksek doğruluklu model değil, verilen bütçelerin tamamını karşılayan ve bu bütçeleri ölçülmüş biçimde gösteren modeldir. Aşağıdaki dört çözümlü örnek, bu düşünceyi sayılarla yapmanı sağlar.

## Çözümlü Örnekler

Bu bölümde dört örnek var, zorluk sırasıyla ★, ★★, ★★, ★★★. Her örneği önce kendin çöz, sonra adımlarla karşılaştır. Örneklerin sayıları, bu bölümün sonunda verilen `ornek_dogrula.py` betiğiyle doğrulanır.

### Örnek 1 (★): Bir tensörün simetrik ve asimetrik int8 kuantizasyonu

Beş değerli bir tensör ele alalım: `x = [−1,00; −0,35; 0,00; 0,60; 2,40]`. Bunu int8'e (−128 ile 127 arası) iki yoldan kuantize et: simetrik (sıfır noktası 0) ve asimetrik (sıfır noktası `z`). Her iki durumda geri dönüşmüş değerleri ve tensörün ortalama kare hatasını (MSE) hesapla.

**Adım 1 — Anla.** İstenen, her iki yöntem için ölçek `s`, tam sayı değerleri `q`, geri dönüşmüş değerler `x̂` ve MSE. Kuantizasyon kuralı `q = round(x / s)` (asimetrikte `q = round(x / s) + z`), geri dönüşüm `x̂ = s · q` (asimetrikte `x̂ = s · (q − z)`).

**Adım 2 — Örnekle.** `max|x| = 2,40` ve `min x = −1,00`, `max x = 2,40`. Simetrik ızgarada değerler `−127..127`, asimetrikte `−128..127` aralığını kullanır.

**Adım 3 — Kaba çöz.** Simetrik ölçek `s = 2,40 / 127 = 0,018898`. Asimetrik ölçek `s = (2,40 − (−1,00)) / 255 = 3,40 / 255 = 0,013333`; sıfır noktası `z = round(1,00 / 0,013333) − 128 = 75 − 128 = −53`. Simetrik `x / s = [−52,92; −18,52; 0; 31,75; 127,0]`, yuvarlanınca `q = [−53; −19; 0; 32; 127]`. Asimetrik `x / s = [−75; −26,25; 0; 45; 180]`, yuvarlanıp `z` eklenince `q = [−128; −79; −53; −8; 127]`.

**Adım 4 — Örüntü.** Simetrik ızgarada negatif taraf `−127..0` aralığında, ama tensörde yalnızca `−53` ve `−19` kullanılmış; pozitif taraf ise tam kullanılmış (`127`). Asimetrik ızgarada ise 256 seviyenin tamamı `[−1,00; 2,40]` aralığına yayılmış. Bu, asimetrik yöntemin neden daha ince bir ızgara verdiğinin sayısal nedenidir.

**Adım 5 — İyileştir.** Asimetrik yöntem daha az hata verir; ama `z` sıfır değilse çarpım sırasında bir düzeltme terimi gerekir, bu da donanımda ek işlemdir. Bu yüzden pratikte ağırlıklar simetrik (sıfır noktası 0), ReLU sonrası pozitif aktivasyonlar ise asimetrik kuantize edilir. Bölüm 46'da bu ayrımı sabit noktada (Q1.15) görmüştük.

**Adım 6 — Doğrula.** Elle iz tablosu ve bilgisayar sonucu:

| x | q (sim.) | x̂ (sim.) | hata (sim.) | q (asim.) | x̂ (asim.) | hata (asim.) |
|---|---|---|---|---|---|---|
| −1,00 | −53 | −1,00157 | −0,00157 | −128 | −1,00000 | 0,00000 |
| −0,35 | −19 | −0,35906 | −0,00906 | −79 | −0,34667 | 0,00333 |
| 0,00 | 0 | 0,00000 | 0,00000 | −53 | 0,00000 | 0,00000 |
| 0,60 | 32 | 0,60472 | 0,00472 | −8 | 0,60000 | 0,00000 |
| 2,40 | 127 | 2,40000 | 0,00000 | 127 | 2,40000 | 0,00000 |

Ortalama kare hata simetrik için `2,14 · 10⁻⁵`, asimetrik için `2,22 · 10⁻⁶`: asimetrik yaklaşık on kat daha az hata yapıyor. Bu sayılar `ornek_dogrula.py` çıktısıyla aynıdır.

**Bunu AI'sız yazabilir misin?** `x = [−0,50; 0,00; 1,50]` tensörünü asimetrik int8 ile kuantize et: `s`, `z`, `q` ve MSE'yi elle bul. Sonra simetrik sonucu ile karşılaştır: hangisi daha az hata verir ve bunun nedeni hangi değerin aralıktaki konumu?

### Örnek 2 (★★): Bir Conv + BatchNorm çiftinin elle katlanması

Bir konvolüsyon tek bir skaler ağırlıkla `W = 0,5` ve bias `b = 0,1` ile temsil edilsin. Eğitimden sonra bunu izleyen BatchNorm'un parametreleri `γ = 2`, `β = −0,3`, `μ = 0,2`, `σ² = 0,04` ve `ε = 10⁻⁵`. Girdi `x = 1,3`. Katlanmış `W'` ve `b'` değerlerini bul ve iki yolun aynı çıktıyı verdiğini göster.

**Adım 1 — Anla.** İstenen, `W'` ve `b'` ile `W' · x + b'` ile BatchNorm çıktısının (`γ · (W x + b − μ) / √(σ² + ε) + β`) eşit olmasıdır.

**Adım 2 — Örnekle.** `W x + b = 0,5 · 1,3 + 0,1 = 0,75`. BatchNorm girdisi `0,75 − 0,2 = 0,55` olarak merkezlenir.

**Adım 3 — Kaba çöz.** `√(σ² + ε) = √0,04001 = 0,200025`. Ölçek `s = γ / √(σ² + ε) = 2 / 0,200025 = 9,99875`. Katlanmış ağırlık `W' = W · s = 0,5 · 9,99875 = 4,999375`. Katlanmış bias `b' = (b − μ) · s + β = (0,1 − 0,2) · 9,99875 − 0,3 = −1,299875`.

**Adım 4 — Örüntü.** `s`, kanal başına bir ölçektir: BatchNorm'un tüm istatistikleri bu tek çarpanda toplanır. Katlama sonrası ileri geçiş, yalnızca bir çarpma ve bir toplama içerir; BatchNorm'un ayrı bir işlemi kalmaz. Bu dönüşüm yalnızca değerlendirme (eval) modunda geçerlidir, çünkü eğitimde BatchNorm istatistikleri her mini-batch'te değişir.

**Adım 5 — İyileştir.** Katlamayı çoklu kanal ve gerçek bir Conv2d için de uygulayabilirsin: `W'[k] = W[k] · s[k]` ve `b'[k] = (b[k] − μ[k]) · s[k] + β[k]`. Kanal indeksi `k` ayrı ayrı ölçeklenir. Betik de bu formülü `s.view(-1, 1, 1, 1)` ile uygular.

**Adım 6 — Doğrula.**

| Adım | Yol A (ayrı BatchNorm) | Yol B (katlanmış) |
|---|---|---|
| Konvolüsyon çıktısı | W x + b = 0,75 | W' x + b' |
| Merkezleme | 0,75 − 0,2 = 0,55 | 4,999375 · 1,3 = 6,499188 |
| Bölme ve ölçek | 2 · 0,55 / 0,200025 = 5,49931 | — |
| BatchNorm'un kayması | 5,49931 − 0,3 = 5,19931 | 6,499188 − 1,299875 = 5,19931 |

İki yol, `5,199313` değerinde buluşuyor ve farkları `8,9 · 10⁻¹⁶`: yani makine hassasiyetinde aynı. Betik aynı kontrolü bir Conv2d ile yapar ve fark `4,8 · 10⁻⁷` çıkar (fp32 yuvarlama). Bu sonuç `ornek_dogrula.py` çıktısındaki iki sayıyla aynıdır.

**Bunu AI'sız yazabilir misin?** `W = −1`, `b = 0`, `γ = 3`, `β = 1`, `μ = 2`, `σ² = 0,25`, `ε ≈ 0`, `x = 0` için katlanmış `W'` ve `b'` değerlerini bul. BatchNorm'un çıktısını doğrudan hesaplayarak katlamanın doğru olduğunu göster.

### Örnek 3 (★★): Roofline ile hesap mı, bellek mi?

Bir edge CPU'sunun ölçülmüş tepesi 20 GFLOP/s, bellek bant genişliği 8 GB/s. `512 × 512` bir tam bağlı katman (fp32) batch `B` ile çalışıyor. Hangi batch değerinden itibaren katman hesap sınırlı olur? `B = 1`, `B = 4`, `B = 16` için tavanı hesapla.

**Adım 1 — Anla.** İstenen, her `B` için aritmetik yoğunluk `AI`, `AI < tepe / bant` ise bellek sınırlı, değilse hesap sınırlı kararı ve tavan performans `min(tepe, bant · AI)`.

**Adım 2 — Örnekle.** Ayrım noktası `tepe / bant = 20 / 8 = 2,5` FLOP/bayt. `B = 1` için FLOP `2 · 512 · 512 = 524 288`.

**Adım 3 — Kaba çöz.** Bayt sayısı `4 · (512 · 512 + 2 · B · 512)`. `B = 1`: `4 · (262 144 + 1 024) = 1 052 672` bayt, `AI = 524 288 / 1 052 672 = 0,498`. `B = 4`: FLOP `2 097 152`, bayt `1 064 960`, `AI = 1,969`. `B = 16`: FLOP `8 388 608`, bayt `1 114 112`, `AI = 7,529`.

**Adım 4 — Örüntü.** `AI`, batch ile neredeyse doğrusal artar, çünkü ağırlık baytları sabit kalır. `B = 1` ve `B = 4` ayrım noktasının altında (bellek sınırlı); `B = 16` üstünde (hesap sınırlı). Tavan: `B = 1` için `8 · 0,498 = 3,98 GFLOP/s`; `B = 16` için `20 GFLOP/s`.

**Adım 5 — İyileştir.** Eşik batch değerini doğrudan bul: `AI(B) = 2,5` çözülürse `B ≈ 5,1`. Bu yüzden `B = 5` hâlâ bellek sınırlı (`AI = 2,452`), `B = 6` hesap sınırlı (`AI = 2,931`). Edge'de batch 6'ya çıkarmak çoğu zaman mümkün değildir (her kare hemen işlenir); bu durumda tek seçenek ağırlık baytını küçültmektir (kuantizasyon), çünkü bu `AI`'yi doğrudan artırır.

**Adım 6 — Doğrula.**

| B | FLOP | Bayt | AI (FLOP/bayt) | Sınır | Tavan (GFLOP/s) |
|---|---|---|---|---|---|
| 1 | 524 288 | 1 052 672 | 0,498 | bellek | 3,98 |
| 4 | 2 097 152 | 1 064 960 | 1,969 | bellek | 15,75 |
| 5 | 2 621 440 | 1 069 056 | 2,452 | bellek | 19,62 |
| 6 | 3 145 728 | 1 073 152 | 2,931 | hesap | 20,00 |
| 16 | 8 388 608 | 1 114 112 | 7,529 | hesap | 20,00 |

Betik çıktısı (`log_ornek.txt`) aynı `AI` değerlerini verir. Bu bir teorik tavandır. Ölçülen performans bu tavanın altında kalmalıdır: Bölüm 75.2'de batch 1 ve 4 için böyle oldu. Büyük batch'te ölçülen değerler tepe tahminimizi aştı; bu, tepenin kaba ölçümünün bir işaretidir.

**Bunu AI'sız yazabilir misin?** `256 × 256` katmanın aynı donanımda ayrım noktası kaç batch'te? Hangi boyut büyüdükçe ayrım noktası sola kayar ve neden?

### Örnek 4 (★★★): Bir edge hedefi için kuantizasyon, budama ve damıtma karar tasarımı

Bir Cortex-M4 (168 MHz) kartında bir sınıflandırıcı çalıştıracaksın. Kısıtlar: flash en fazla 256 KB, gecikme en fazla 5 ms, test doğruluğu en az %95. Elinde varsayımsal bir öğretmen var: 1,2 milyon parametreli, fp32, MAC sayısı da yaklaşık 1,2 milyon. Hangi araçları, hangi sırayla uygulamalısın? Her aday için flash, MAC, gecikme ve flash kararını hesapla.

**Adım 1 — Anla.** Kısıtlar üç sayı: flash `≤ 256 KB`, gecikme `≤ 5 ms`, doğruluk `≥ %95`. Gecikme, çevrimle hesaplanır: `süre = MAC · c / f`. Varsayım: MAC başına `c = 2` çevrim (ölçülmedi; bir başlangıç tahmini). `f = 168 · 10⁶` Hz. Bütçe `5 · 10⁻³ · 168 · 10⁶ = 840 000` çevrim, yani en fazla `420 000` MAC.

**Adım 2 — Örnekle.** Aday 1: öğretmen fp32. Parametre `1 200 000 · 4` bayt `= 4 688 KB`. Aday 2: öğretmen int8, `1 172 KB`. Aday 3: `%70` yapılandırılmamış budama + int8; ama budanmış ağırlıklar yoğun saklanırsa sıfırlar yine yer kaplar; MAC `0,3 · 1 200 000 = 360 000`. Aday 4: yapısal `%50` kanal budama + damıtma ile 120 000 parametreli bir öğrenci, int8.

**Adım 3 — Kaba çöz.** Aday 1: flash 4 688 KB (aşar). Aday 2: 1 172 KB (aşar). Aday 3: flash yine 1 172 KB (aşar), çünkü dosya boyutu sıfırlara bağlıdır. Aday 4: `120 000 · 1` bayt `= 117 KB` (sığar). Gecikme için MAC'lerin çevrimleri: aday 1 ve 2 için `1 200 000 · 2 = 2 400 000` çevrim, `14,29 ms` (aşar); aday 3 için `720 000` çevrim, `4,29 ms` (sığar ama flash'ta aşar); aday 4 için `240 000` çevrim, `1,43 ms` (sığar).

**Adım 4 — Örüntü.** Yalnızca budama flash'ı düşürmez; budama, dosya boyutunu ancak sıkıştırılmış bir seyrek biçimle azaltır ve bu biçim CSR gibi indeks bilgisi ister. Bu bölümün budama deneyinde de gördük: yoğun saklamada seyreklik hızı değiştirmiyordu. Flash ve gecikmeyi birlikte düşüren tek aday, yapısal budama ile modelin gerçekten küçülmesidir; ardından damıtma ve kuantizasyon birleştiğinde kısıtlar sağlanır.

**Adım 5 — İyileştir.** Aday 4'ü iyileştirmek için doğrulukla ilgili ölçüm şarttır: 120 000 parametrelik öğrencinin doğruluğu bu görevde %95'i geçiyor mu? Bu bölümün digits deneyinde, 2 410 parametreli bir öğrenci %96 civarında doğruluk verdi; ama o görev çok kolay. Gerçek sınıflandırma probleminde, öğrencinin doğruluğu ayrı bir doğrulama kümesinde ölçülmeli ve eşik altındaysa yapısal budama oranı azaltılmalı ya da öğrenci büyütülmelidir. Bu, bütçeler arasındaki bir denge kararıdır.

**Adım 6 — Doğrula.** Betik çıktısı (`log_ornek.txt`) bu adayların sayılarını üretir:

| Aday | Parametre | Flash (KB) | MAC | Süre (ms, c = 2) | Flash ≤ 256 KB |
|---|---|---|---|---|---|
| Öğretmen fp32 | 1 200 000 | 4 687,5 | 1 200 000 | 14,29 | hayır |
| Öğretmen int8 | 1 200 000 | 1 171,9 | 1 200 000 | 14,29 | hayır |
| Budama %70 + int8 (yoğun) | 1 200 000 | 1 171,9 | 360 000 | 4,29 | hayır |
| Yapısal %50 + damıtma int8 | 120 000 | 117,2 | 120 000 | 1,43 | evet |

Dört koşulun tamamı, yalnızca son aday için sağlanır: flash (117 KB ≤ 256 KB), gecikme (1,43 ms ≤ 5 ms) ve doğruluk (ölçülmesi gerekiyor). Gecikmenin `c = 2` varsayımına bağlı olduğunu unutma; gerçek sayı, derleyicinin ürettiği koda ve kartın bellek bekleme durumlarına göre ölçülmeli.

**Bunu AI'sız yazabilir misin?** Aynı kartta 80 ms'lik bir gecikme ve 512 KB flash bütçesi ve `c = 3` varsayımıyla bir tasarım yap: en fazla kaç MAC, ve hangi aday (yukarıdaki dört aday ya da yeni bir tane) bu bütçeye girer? Her adayın flash ve süre değerini ayrı ayrı yaz.

### Doğrulama betiği

Dört örnekteki sayıları üreten betik aşağıdadır. Betik, yalnızca bu örneklerin hesaplarını kontrol eder; bölümün deneylerinden bağımsızdır.

```python
# -*- coding: utf-8 -*-
"""Bolum 75 cozumlu ornek sayilarini dogrular (Ornek 1-4)."""
import numpy as np

# Ornek 1: tensor kuantizasyonu (simetrik ve asimetrik, int8)
x = np.array([-1.00, -0.35, 0.00, 0.60, 2.40])
s_sim = np.abs(x).max() / 127
q_sim = np.clip(np.round(x / s_sim), -127, 127).astype(int)
xh_sim = q_sim * s_sim
print("sim s=%.6f q=%s" % (s_sim, q_sim.tolist()))
print("sim hata=%s" % np.round(xh_sim - x, 5).tolist())
s_as = (x.max() - x.min()) / 255
z = int(np.round(-x.min() / s_as)) - 128
q_as = np.clip(np.round(x / s_as) + z, -128, 127).astype(int)
xh_as = (q_as - z) * s_as
print("asim s=%.6f z=%d q=%s" % (s_as, z, q_as.tolist()))
print("asim hata=%s" % np.round(xh_as - x, 5).tolist())
print("sim MSE=%.3e asim MSE=%.3e"
      % (np.mean((xh_sim - x) ** 2), np.mean((xh_as - x) ** 2)))
```

```python
# Ornek 2: BatchNorm katlamasi (skaler)
W, b, gam, bet, mu, var, eps = 0.5, 0.1, 2.0, -0.3, 0.2, 0.04, 1e-5
xi = 1.3
bn = gam * ((W * xi + b) - mu) / np.sqrt(var + eps) + bet
s = gam / np.sqrt(var + eps)
Wf, bf = W * s, (b - mu) * s + bet
print("s=%.6f W'=%.6f b'=%.6f" % (s, Wf, bf))
print("BN=%.6f katli=%.6f fark=%.2e"
      % (bn, Wf * xi + bf, abs(bn - (Wf * xi + bf))))
```

```python
# Ornek 3: roofline (512x512 Linear, tepe 20 GFLOP/s, bant 8 GB/s)
tepe, bant = 20.0, 8.0
esik = tepe / bant
print("esik AI=%.2f" % esik)
for B in [1, 4, 5, 6, 16]:
    fl = 2.0 * B * 512 * 512
    by = 4.0 * (512 * 512 + 2 * B * 512)
    ai = fl / by
    tur = "bellek" if ai < esik else "hesap"
    print("B=%-2d FLOP=%d bayt=%d AI=%.3f %s"
          % (B, fl, by, ai, tur))
```

```python
# Ornek 4: edge hedef butcesi (varsayimsal 1,2 milyon parametre)
FLASH_KB = 256
SAAT = 168e6
BUTCE_CEVRIM = 5e-3 * SAAT
c = 2  # varsayim: MAC basina 2 cevrim (olculmedi)
print(
    "butce cevrim=%.0f MAC_tavan=%.0f"
    % (BUTCE_CEVRIM, BUTCE_CEVRIM / c)
)
aday = [
    ("ogretmen fp32", 1_200_000, 32, 1_200_000),
    ("ogretmen int8", 1_200_000, 8, 1_200_000),
    ("budama %70 + int8 (yogun)", 1_200_000, 8, 360_000),
    ("yapisal %50 + damitma int8", 120_000, 8, 120_000),
]
for ad, p, bit, mac in aday:
    kb = p * bit / 8 / 1024
    ms = mac * c / SAAT * 1e3
    print("%-26s %8.1f KB %9d MAC %6.2f ms %s"
          % (ad, kb, mac, ms, "evet" if kb <= FLASH_KB else "hayir"))
```

```term
$ python ornek_dogrula.py
sim s=0.018898 q=[-53, -19, 0, 32, 127]
sim hata=[-0.00157, -0.00906, 0.0, 0.00472, 0.0]
asim s=0.013333 z=-53 q=[-128, -79, -53, -8, 127]
asim hata=[0.0, 0.00333, 0.0, 0.0, 0.0]
sim MSE=2.136e-05 asim MSE=2.222e-06
s=9.998750 W'=4.999375 b'=-1.299875
BN=5.199313 katli=5.199313 fark=8.88e-16
esik AI=2.50
B=1  FLOP=524288 bayt=1052672 AI=0.498 bellek
B=4  FLOP=2097152 bayt=1064960 AI=1.969 bellek
B=5  FLOP=2621440 bayt=1069056 AI=2.452 bellek
B=6  FLOP=3145728 bayt=1073152 AI=2.931 hesap
B=16 FLOP=8388608 bayt=1114112 AI=7.529 hesap
butce cevrim=840000 MAC_tavan=420000
ogretmen fp32                4687.5 KB   1200000 MAC  14.29 ms hayir
ogretmen int8                1171.9 KB   1200000 MAC  14.29 ms hayir
budama %70 + int8 (yogun)    1171.9 KB    360000 MAC   4.29 ms hayir
yapisal %50 + damitma int8    117.2 KB    120000 MAC   1.43 ms evet
```

## Kendin Yap Projeleri

::: dikkat
Aşağıdaki projelerde bir yapay zekâ aracından kod üretmeden önce kendi çözümünü yaz. Bu bölümdeki betikler sana bir başlangıç verir; ama projenin amacı, bir kuantizasyon ve dağıtım zincirini kendi elinle kurabilmektir.
:::

### Proje 1 (★★): Kendi int8 çıkarım motorun

**Amaç.** Bu bölümde kuantizasyonu PyTorch'un içinde ve hazır fonksiyonlarla yaptık. Bu projede aynı işi NumPy ile, bir çıkarım motoru gibi, baştan kur. Amacın bir çerçeve kullanmadan kuantizasyon ızgarasının nasıl çalıştığını görmektir.

**Yapılacak.** (1) `b75_ortak.py` ile aynı veriyi ve aynı 64-32-10 MLP mimarisini kullanarak bir model eğit ve ağırlıklarını `.npz` dosyasına kaydet. (2) Yalnızca NumPy ile bir ileri geçiş yaz: tam sayı matris çarpımı, yeniden ölçekleme, yuvarlama ve ReLU. Yeniden ölçekleme ve yuvarlama, bu bölümdeki `gen_mcu.py` ile aynı kurala uymalı. (3) 8 bit ve 4 bit ağırlık için (tensör başına ve kanal başına) test doğruluğunu ölç ve üç tohum için ortalama ± sapma raporla. (4) Sonuçlarını PyTorch'un `quantize_dynamic` çıktısı ve bu bölümdeki PTQ tablosuyla karşılaştır.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Önce tek bir katmanı çöz: bir `64 → 32` katmanı için yalnızca bir vektörün çıktısını hem fp32 hem int8 ile hesapla ve farkı yaz. Sonra katmanı ikinci katmanla birleştir. Yuvarlamada `np.round` kullanırsan, bankacı yuvarlaması (round half to even) farkını gözden kaçırma; bu bölümün C kodu sıfırdan uzağa yuvarlar. Test kümesi 540 örnek içerir; iki doğruluk arasındaki farkın bir örnek düzeyinde olduğunu hesapla ve yorumuna öyle yaz.

**Başarı kriterleri.** (a) 8 bit ağırlık ve aktivasyonla kendi motorunun test doğruluğu, PyTorch PTQ'nun 0,01 (yüzde bir) içinde. (b) Üç tohum için ortalama ve sapma raporlanmış. (c) Yuvarlama kuralının sonuca etkisi, iki farklı yuvarlama ile ölçülmüş ve yorumlanmış. (d) Kod, PyTorch import etmeden çalışıyor.

### Proje 2 (★★★): Cortex-M4'te çevrim sayısını ölç ve çekirdeği hızlandır

**Amaç.** Bölüm 75.8'de çevrim sayısını ölçmedik. Bu projede onu ölç ve bir iyileştirme dene. Hedef, boyut ile hız arasındaki takası bir tabloyla göstermektir.

**Yapılacak.** (1) `mlp_int8.c` için bir çevrim ölçüm yöntemi seç: bir Cortex-M4 kartı varsa DWT çevrim sayacı (DWT->CYCCNT), yoksa Unicorn ile bir emülasyon ve komut sayımı. Ölçüm yöntemini ve sınırlarını yaz. (2) Ölçümü 50 test vektörünün tamamı için yap ve medyanını ver. (3) İç döngüyü, Bölüm 46'daki DSP sürümü gibi, çift kelime (SMLAD gibi) komutlarıyla hızlandırmayı dene; bu, iki 16 bitlik çarpımı tek komutta yapar. (4) Her değişiklik için hız ve kod boyutunu aynı tabloda ver.

**Önerilen yaklaşım (ipucu).** Bölüm 46'daki `tinyml.c` içinde nokta çarpımın iki sürümünü oku (düz C ve DSP sürümü); aynı yapıyı bu modelin iç döngüsüne uygula. Derleyicinin çıktısını (`-S`) incele: iç döngünün gerçekten `smlad` ya da benzeri bir komut üretip üretmediğini doğrula, dilediğin gibi olmayabilir. Bit-tam eşleşmeyi bozmamak için `test_host.c` her değişiklikten sonra çalışmalı.

**Başarı kriterleri.** (a) Çevrim sayısı, kullanılan yöntem (DWT ya da emülatör) ve sürümleriyle birlikte raporlanmış. (b) İyileştirilmiş çekirdek konak testinde 50/50 logit eşleşmesini koruyor. (c) Her değişiklik için çevrim, `.text` boyutu ve kullanılan komutların sayımı tablo hâlinde verilmiş. (d) Bir sonuç "daha hızlı" diye yazıldıysa, bu fark ölçüm gürültüsünden büyük olduğu tekrarlarla gösterilmiş.

### Ek Alıştırmalar

1. ★ (Mülakat) Aritmetik yoğunluk nedir? Aynı 2048 × 2048 katman batch 1 ve batch 64'te neden farklı bir sınıra (bellek ya da hesap) düşer?
2. ★ (Mülakat) Simetrik ve asimetrik kuantizasyon arasındaki fark nedir? Ağırlıklar için hangisi tercih edilir ve neden?
3. ★★ Bir aktivasyonda tek bir aykırı değer, max kalibrasyonunda ölçeği nasıl etkiler? %99,9 yüzdelik kalibrasyonun bedeli ne olabilir?
4. ★★ (Mülakat) Yuvarlama fonksiyonunun türevi neredeyse her yerde sıfırdır. Düz geçiş tahmincisi (STE) bu sorunu nasıl aşar ve gradyanı ne zaman sıfırlar?
5. ★ (Mülakat) Yapılandırılmamış budama, batch 1'de neden her zaman hız getirmez? Hangi koşulda getirir?
6. ★★ Yinelemeli budamanın tek adıma göre avantajını hangi büyüklükteki ağda ve hangi seyreklik düzeyinde beklersin? Bu bölümün küçük ağ deneyi bunu neden gösteremedi?
7. ★★ Bilgi damıtmada `T²` çarpanı neden gereklidir? `T = 1` alırsan gradyanın büyüklüğüne ne olur?
8. ★ (Mülakat) Derinlemesine ayrılabilir konvolüsyonun MAC oranını `k = 5` ve `C_giriş = C_çıkış = 128` için hesapla. MAC'in düşmesi neden her zaman gecikmenin düşmesi anlamına gelmez?
9. ★★ BatchNorm katlaması neden yalnızca değerlendirme (eval) modunda yapılabilir? Eğitimde hangi istatistik her mini-batch'te değişir?
10. ★★★ Bir edge kartında 128 KB flash ve 16 KB RAM var. 64 → 32 → 10 int8 bir MLP için her katmanın girdi ve çıktı aktivasyonlarının toplam baytını hesapla ve RAM'e sığıp sığmadığını yaz. Hangi katman tepe bellek ihtiyacını belirler?
11. ★ (Mülakat) ONNX Runtime ile PyTorch arasındaki `1e-5` mertebesindeki farkın fp32 aritmetiğinden geldiğini nasıl gösterirsin? Mutlak ve bağıl fark neden farklı sonuç verebilir?
12. ★★ Ürün kuantizasyon ile skaler kuantizasyon arasında bellek ve arama maliyeti nasıl değişir? Hangisi büyük bir vektör veritabanında daha uygun olur ve neden?

## Kod Okuma Egzersizi

Bu bölümde budamayı sıfırdan yazdık ve PyTorch'un `l1_unstructured` fonksiyonuyla karşılaştırdık. Şimdi PyTorch'un kendi kodunu oku. Kaynak: PyTorch 2.6.0+cu124, kurulu paketteki `torch/nn/utils/prune.py` dosyası (Python 3.12 site-packages), `L1Unstructured` sınıfının `compute_mask` yöntemi, 509–529. satırlar. Uzun satırlar 70 karakterde sarıldı; yorumların içeriği değişmedi, bir yorum iki satıra bölündü ve `topk` çağrısının argümanları ayrı satırlara alındı.

```python
    def compute_mask(self, t, default_mask):
        # Check that the amount of units to prune is not > than the
        # number of parameters in t
        tensor_size = t.nelement()
        # Compute number of units to prune: amount if int,
        # else amount * tensor_size
        nparams_toprune = _compute_nparams_toprune(
            self.amount, tensor_size
        )
        # This should raise an error if the number of units to prune
        # is larger than the number of units in the tensor
        _validate_pruning_amount(nparams_toprune, tensor_size)

        mask = default_mask.clone(
            memory_format=torch.contiguous_format
        )

        if nparams_toprune != 0:  # k=0 is not supported
            # by torch.kthvalue
            # largest=True --> top k; largest=False --> bottom k
            # Prune the smallest k
            topk = torch.topk(
                torch.abs(t).view(-1),
                k=nparams_toprune,
                largest=False,
            )
            # topk will have .indices and .values
            mask.view(-1)[topk.indices] = 0

        return mask
```

Önce bu kodun bizim `buyukluk_maskesi` fonksiyonumuzla aynı işi yaptığını gör: en küçük `k` mutlak değeri bulup maskede sıfır koyar. Farklar ise ayrıntıda: PyTorch `topk` ile en küçük `k` değeri seçer, biz `argsort` ile tüm dizi sıralar; ve PyTorch mevcut bir `default_mask` ile başlar.

**Sorular — cevaplamadan geçme:**

1. `_compute_nparams_toprune(self.amount, tensor_size)` `amount` bir tam sayıysa ve bir kesirse ne yapar? Bu fonksiyonun kodunu yerel kurulumdan okuyarak bul ve `0,9` için kaç eleman budanacağını hesapla.
2. `torch.topk(..., largest=False)` ile bizim `argsort(...)[:k]` aynı küme eleman seçer mi? Eşit mutlak değerli elemanlar (beraberlik) olduğunda hangisi hangisini seçer, bunu bir küçük örnekte dene.
3. Yorum "k=0 not supported by torch.kthvalue" diyor. Bu koşulu neden koymuşlar? Bizim `buyukluk_maskesi` içinde buna karşılık gelen `if k > 0:` satırı neyi önler?
4. `default_mask.clone(...)` ne işe yarar? Yinelemeli budamada bir önceki maske ile bu yeni maske nasıl birleşir ve neden önceden budanmış konumlar yeniden açılmaz?
5. `mask.view(-1)[topk.indices] = 0` satırında `view(-1)` yerine `reshape(-1)` kullanırsak sonuç değişir mi? Bitişik olmayan bir tensörde (örneğin bir transpozun) ne olur?
6. Torch'un bu yöntemi `t` olarak `weight` mi yoksa `weight_orig` mi alır? Bu bilgi, `torch.nn.utils.prune` ile kurulan bir modelde ağırlığın nasıl güncellendiğini anlamak için neden önemlidir?

## Bölüm Özeti

- Çıkarımın maliyeti parametre, MAC ve bellek trafiğinden oluşur. Aritmetik yoğunluk, bir katmanın bellek ya da hesap sınırlı olduğunu roofline ile gösterir. Batch 1'de çoğu katman bellek sınırlıdır.
- Ölçüm disiplini üç kuraldır: ısınma, çok tekrar ve medyan ile p95. Kesin değerler koşudan koşuya değişebilir; oran ve sıralama daha güvenilirdir.
- Kuantizasyon, sayıları tam sayı ızgarasına çevirir. Simetrik ızgara ağırlıklar için, asimetrik ızgara aktivasyonlar için daha uygundur; kanal başına ölçek hatayı azaltır. Kalibrasyonda aykırı değer, düşük bit genişliğinde modeli çökertebilir (bu bölümde 4 bitte doğruluk 0,10'a indi).
- Sonradan kuantizasyon (PTQ) eğitim gerektirmez ama 2 bitte çöker; kuantizasyon farkındalıklı eğitim (QAT) düz geçiş tahmincisi ile bu ızgaraya uyum sağlar (2 bitte 0,96).
- Budama, yapılandırılmamış seyreklikle sıfırları dağıtır: hız ancak seyrek bir çekirdekle ve yüksek seyreklikte gelir, dosya boyutu ise yoğun saklamada değişmez. Kanal budama modeli gerçekten küçültür ve batch 1'de belirgin hız verir.
- Bilgi damıtma, öğretmenin yumuşak hedeflerini sıcaklıkla öğrenciye aktarır. Bu bölümde, kolay bir görevde, sıfırdan eğitilmiş öğrenciye karşı kazanç görülmedi; yöntemin değeri görevin zorluğuna bağlıdır.
- Verimli mimariler, MAC'i azaltır; ama MAC ile gecikme her zaman orantılı değildir. Ölçmek zorunludur.
- Dağıtım, dışa aktarma, çalışma zamanı ve cihaz aşamalarından oluşur; her aşamada sayısal doğrulama yapılır. Conv + BatchNorm katlaması, çıktıyı değiştirmeden grafı küçültür.
- Edge tasarımı, bellek, gecikme, güç, doğruluk ve güvenilirlik bütçelerinin birlikte sağlanmasıdır. Bir İHA'da ortalama değil kuyruk gecikmesi ve sertifikasyon belirleyicidir.

**Sonraki bölümde:** Bölüm 76, GPU Programlama ve Dağıtık Eğitim ile devam edecek. Bu bölümde modelin çıkarımını tek bir cihazda küçülttük; bir sonraki bölümde ise modelin eğitimini birden çok GPU'ya nasıl yayacağımızı ve bellek hiyerarşisinin bu işi nasıl sınırladığını göreceğiz.

::: mulakat
1. Bir katmanın aritmetik yoğunluğu batch büyüdükçe neden neredeyse doğrusal artar? Bu artış hangi baytların sabit kalmasından gelir?
2. Simetrik kuantizasyonda sıfır noktası neden yoktur ve bu, ağırlıklar için hangi donanım avantajını sağlar?
3. PTQ ile QAT arasındaki fark nedir? 2 bitlik bir ağırlık ızgarasında PTQ neden çöker, QAT neden çökmez?
4. Yapılandırılmamış budama ile yapılandırılmış budama arasındaki farkı, batch 1 gecikmesi ve dosya boyutu açısından açıkla.
5. Bilgi damıtmada öğretmenin yumuşak hedefleri neden gerçek etiketlerden daha fazla bilgi taşıyabilir? Bu bilgi hangi koşulda öğrenciye aktarılamaz?
6. Bir Conv ve BatchNorm çiftini tek bir konvolüsyona katlamak neden eğitimde değil de değerlendirmede yapılır?
7. Bir İHA'da gecikme için ortalama yerine neden p95 ya da p99 kullanılır? Bu bir karar sisteminde hangi riski azaltır?
:::
