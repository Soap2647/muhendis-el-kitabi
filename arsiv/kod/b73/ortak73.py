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
