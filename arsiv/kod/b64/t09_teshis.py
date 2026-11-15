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
