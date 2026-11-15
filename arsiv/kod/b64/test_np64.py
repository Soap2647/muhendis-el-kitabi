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


def kontrol(ad, fark, esik=1e-6):
    tamam = fark <= esik
    sonuc.append(tamam)
    print(
        "%-38s max fark = %.3e   %s"
        % (ad, fark, "TAMAM" if tamam else "HATA")
    )


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
