# -*- coding: utf-8 -*-
"""Bolum 72.4-72.5: derin AE (load_digits), gurultu giderici AE ve
sentetik sensor sinyalinde yeniden yapilandirma hatasiyla anomali
tespiti (PCA tabanli karsilastirma ile)."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
from b72_veri import digits_bol

TOHUMLAR = [0, 1, 2]


def mlp_ae(giris, gizil, gizli=128, cikis_sig=True):
    enc = nn.Sequential(nn.Linear(giris, gizli), nn.ReLU(),
                        nn.Linear(gizli, gizil))
    son = [nn.Linear(gizil, gizli), nn.ReLU(),
           nn.Linear(gizli, giris)]
    if cikis_sig:
        son.append(nn.Sigmoid())
    return enc, nn.Sequential(*son)


def egit(enc, dec, X, hedef, epoch, seed, gurultu=0.0, lr=1e-3):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(list(enc.parameters()) +
                           list(dec.parameters()), lr=lr)
    n = len(X)
    for _ in range(epoch):
        p = torch.randperm(n)
        for i in range(0, n, 128):
            b = p[i:i + 128]
            g = X[b]
            if gurultu > 0:
                g = g + gurultu * torch.randn_like(g)
            kayip = ((dec(enc(g)) - hedef[b]) ** 2).mean()
            opt.zero_grad()
            kayip.backward()
            opt.step()
    return enc, dec


def mse(a, b):
    return float(((a - b) ** 2).mean())


# ---------- (a) derin AE ve PCA (k=8) ----------
xtr, ytr, xte, yte = digits_bol(seed=0)
Xtr, Xte = torch.tensor(xtr), torch.tensor(xte)
print("== (a) Derin AE (64-128-8-128-64) vs PCA k=8, test MSE ==")
pca = PCA(n_components=8).fit(xtr)
pca_mse = mse(pca.inverse_transform(pca.transform(xte)), xte)
derin = []
for s in TOHUMLAR:
    enc, dec = mlp_ae(64, 8)
    enc, dec = egit(enc, dec, Xtr, Xtr, 200, s)
    with torch.no_grad():
        derin.append(mse(dec(enc(Xte)).numpy(), xte))
print(f"PCA k=8        : {pca_mse:.5f}")
print(f"Derin AE (ort) : {np.mean(derin):.5f} +- {np.std(derin):.5f}"
      f"  (3 tohum)")

# ---------- (b) gurultu giderici AE ----------
print()
print("== (b) Gurultu giderici AE: gurultulu test -> temiz test ==")
sigma = 0.3
rng = np.random.default_rng(123)
gur_te = (xte + sigma * rng.standard_normal(xte.shape))
gur_te = gur_te.astype(np.float32)
Gte = torch.tensor(gur_te)
sonuc_normal, sonuc_gd = [], []
for s in TOHUMLAR:
    enc, dec = mlp_ae(64, 16, cikis_sig=True)
    enc, dec = egit(enc, dec, Xtr, Xtr, 200, s)
    with torch.no_grad():
        sonuc_normal.append(mse(dec(enc(Gte)).numpy(), xte))
    enc2, dec2 = mlp_ae(64, 16, cikis_sig=True)
    enc2, dec2 = egit(enc2, dec2, Xtr, Xtr, 200, s, gurultu=sigma)
    with torch.no_grad():
        sonuc_gd.append(mse(dec2(enc2(Gte)).numpy(), xte))
print(f"Normal AE (gurultulu girdi): {np.mean(sonuc_normal):.5f}"
      f" +- {np.std(sonuc_normal):.5f}")
print(f"Gurultu giderici AE        : {np.mean(sonuc_gd):.5f}"
      f" +- {np.std(sonuc_gd):.5f}")
print(f"Gurultulu girdinin kendisi : {mse(gur_te, xte):.5f}")

# ---------- (c) sentetik sensor sinyali: anomali tespiti ----------
L = 128
t = np.arange(L) / L


def normal_pencere(rng):
    f1 = rng.uniform(3, 5)
    f2 = rng.uniform(10, 12)
    a1 = rng.uniform(0.9, 1.1)
    a2 = rng.uniform(0.4, 0.6)
    ph = rng.uniform(0, 2 * np.pi)
    s = a1 * np.sin(2 * np.pi * f1 * t) + a2 * np.sin(
        2 * np.pi * f2 * t + ph)
    return s + rng.normal(0, 0.05, L)


def anomali_pencere(rng, tur):
    s = normal_pencere(rng)
    if tur == 0:      # tek noktada sicrama (spike)
        i = rng.integers(10, L - 10)
        s[i] += rng.choice([-1, 1]) * rng.uniform(1.0, 1.5)
    elif tur == 1:    # frekans kaymasi: bilesen 17 cevrime cikar
        s = s + 0.6 * np.sin(2 * np.pi * 17 * t + rng.uniform(0, 6))
    else:             # yavas kayma (dogrusal trend)
        s = s + rng.uniform(0.6, 1.0) * (t - 0.5) * 2
    return s


rng = np.random.default_rng(0)
Ntr, Nval, Nte = 2000, 500, 500
X_tr = np.stack([normal_pencere(rng) for _ in range(Ntr)])
X_val = np.stack([normal_pencere(rng) for _ in range(Nval)])
X_te_n = np.stack([normal_pencere(rng) for _ in range(Nte)])
tur_te = rng.integers(0, 3, Nte)
X_te_a = np.stack([anomali_pencere(rng, k) for k in tur_te])
X_te = np.concatenate([X_te_n, X_te_a]).astype(np.float32)
y_te = np.concatenate([np.zeros(Nte), np.ones(Nte)]).astype(int)
tur_all = np.concatenate([np.full(Nte, -1), tur_te])

Str = torch.tensor(X_tr, dtype=torch.float32)
Sval = torch.tensor(X_val, dtype=torch.float32)
Ste = torch.tensor(X_te)
ortalama = Str.mean(0)
ssd = Str.std()
Ztr = (Str - ortalama) / ssd
Zval = (Sval - ortalama) / ssd
Zte = (Ste - ortalama) / ssd


def ae_skor(enc, dec, Z):
    with torch.no_grad():
        r = dec(enc(Z))
    return ((r - Z) ** 2).mean(1).numpy()


print()
print("== (c) Sensor anomalisi: esik = normal dogrulamanin %99'u ==")
print(f"Egitim: {Ntr} normal pencere; test: {Nte} normal + "
      f"{Nte} anomali")
print("tur: 0 spike, 1 frekans kaymasi, 2 kayma")
print("model        AUC    prec   recall  F1    tur0  tur1  tur2")
sonuc = {"AE": [], "PCA": []}
for s in TOHUMLAR:
    enc, dec = mlp_ae(128, 8, gizli=32, cikis_sig=False)
    Zt = Ztr.clone()
    enc, dec = egit(enc, dec, Zt, Zt, 150, s, lr=1e-3)
    sk_val = ae_skor(enc, dec, Zval)
    sk_te = ae_skor(enc, dec, Zte)
    p_ae = PCA(n_components=8).fit(Ztr.numpy())
    z_val = Zval.numpy()
    z_te = Zte.numpy()
    r_val = ((p_ae.inverse_transform(p_ae.transform(z_val)) - z_val)
             ** 2).mean(1)
    r_te = ((p_ae.inverse_transform(p_ae.transform(z_te)) - z_te)
            ** 2).mean(1)
    sonuc["AE"].append((sk_val, sk_te))
    sonuc["PCA"].append((r_val, r_te))

for ad in ["AE", "PCA"]:
    aucs, precs, recs, f1s, turler = [], [], [], [], []
    for sval, ste in sonuc[ad]:
        esik = np.quantile(sval, 0.99)
        tahmin = (ste > esik).astype(int)
        tp = ((tahmin == 1) & (y_te == 1)).sum()
        fp = ((tahmin == 1) & (y_te == 0)).sum()
        fn = ((tahmin == 0) & (y_te == 1)).sum()
        pr = tp / max(tp + fp, 1)
        rc = tp / max(tp + fn, 1)
        f1 = 2 * pr * rc / max(pr + rc, 1e-12)
        aucs.append(roc_auc_score(y_te, ste))
        precs.append(pr)
        recs.append(rc)
        f1s.append(f1)
        turler.append([tahmin[tur_all == k].mean() for k in range(3)])
    tm = np.mean(turler, 0)
    print(f"{ad:<12} {np.mean(aucs):.3f}  {np.mean(precs):.3f}"
          f"  {np.mean(recs):.3f}   {np.mean(f1s):.3f}"
          f"  {tm[0]:.2f}  {tm[1]:.2f}  {tm[2]:.2f}")
print("(degerler 3 tohumun ortalamasi; tur-x sutunu: "
      "o turun tespit orani)")
