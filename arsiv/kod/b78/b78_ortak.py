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
