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
