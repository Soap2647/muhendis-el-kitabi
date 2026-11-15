# -*- coding: utf-8 -*-
"""Bolum 72.6: ogrenilmis sikistirma (semantik kodek prototipi).
Gizli kod 16 boyutlu; her boyut b bit ile kuantize edilir; ikili
kanal her biti p olasiligiyla cevirir. Baseline: PCA (16 katsayi) ve
DCT (zigzag 16 katsayi), ayni bit butcesi. Olcu: yeniden yapilandirma
MSE'si ve ayri egitilmis siniflandiricinin dogrulugu."""
import csv
import numpy as np
import torch
import torch.nn as nn
from scipy.fft import dctn, idctn
from sklearn.decomposition import PCA
from b72_veri import digits_bol, clf_yukle, tahmin, VERI

D = 16
BITLER = [1, 2, 3, 4, 6, 8]
PS = [0.0, 0.02, 0.05]
TOHUMLAR = [0, 1, 2]

xtr, ytr, xte, yte = digits_bol(seed=0)
Xtr, Xte = torch.tensor(xtr), torch.tensor(xte)
clf = clf_yukle(xtr, ytr)


def zigzag(n=8):
    idx = [(i, j) for i in range(n) for j in range(n)]
    idx.sort(key=lambda q: (q[0] + q[1],
                            q[1] if (q[0] + q[1]) % 2 else q[0]))
    return idx


ZZ = zigzag()[:D]


def dct_katsayi(X):
    img = X.reshape(-1, 8, 8)
    c = dctn(img, axes=(1, 2), norm="ortho")
    return np.stack([c[:, i, j] for i, j in ZZ], 1)


def dct_geri(K):
    c = np.zeros((len(K), 8, 8))
    for n, (i, j) in enumerate(ZZ):
        c[:, i, j] = K[:, n]
    return idctn(c, axes=(1, 2), norm="ortho").reshape(len(K), 64)


def kuantle(z, lo, hi, b):
    L = 2 ** b
    u = np.clip((z - lo) / (hi - lo), 0, 1 - 1e-9)
    return np.floor(u * L).astype(np.int64)


def coz(idx, lo, hi, b):
    L = 2 ** b
    return lo + (idx + 0.5) / L * (hi - lo)


def kanal(idx, b, p, rng):
    """Her bit bagimsiz p olasiligiyla cevrilir (BSC)."""
    if p == 0:
        return idx
    out = idx.copy()
    for j in range(b):
        maske = (rng.random(idx.shape) < p).astype(np.int64)
        out ^= maske << j
    return out


def ae_egit(seed):
    torch.manual_seed(seed)
    enc = nn.Sequential(nn.Linear(64, 64), nn.ReLU(),
                        nn.Linear(64, D))
    dec = nn.Sequential(nn.Linear(D, 64), nn.ReLU(),
                        nn.Linear(64, 64),
                        nn.Sigmoid())
    opt = torch.optim.Adam(list(enc.parameters()) +
                           list(dec.parameters()), lr=1e-3)
    for _ in range(200):
        p = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), 128):
            b = p[i:i + 128]
            kayip = ((dec(enc(Xtr[b])) - Xtr[b]) ** 2).mean()
            opt.zero_grad()
            kayip.backward()
            opt.step()
    return enc, dec


def olc(rekons):
    mse = float(((rekons - xte) ** 2).mean())
    acc = float((tahmin(clf, rekons) == yte).mean())
    return mse, acc


def kodek_dene(ad, b, p, rng, kod_tr, kod_te, geri):
    lo = np.quantile(kod_tr, 0.001, axis=0)
    hi = np.quantile(kod_tr, 0.999, axis=0)
    idx = kuantle(kod_te, lo, hi, b)
    idx = kanal(idx, b, p, rng)
    zq = coz(idx, lo, hi, b)
    return olc(geri(zq))


# ---- Sinirsiz referanslar ----
pca = PCA(n_components=D).fit(xtr)
pca_tr = pca.transform(xtr)
pca_te = pca.transform(xte)
print("== Referans: kuantizasyonsuz ==")
m, a = olc(pca.inverse_transform(pca_te))
print(f"PCA-16 (float)    : MSE={m:.5f}  dogruluk={a:.4f}")
dtr = dct_katsayi(xtr)
dte = dct_katsayi(xte)
m, a = olc(dct_geri(dte))
print(f"DCT-zigzag-16     : MSE={m:.5f}  dogruluk={a:.4f}")

# ---- Ogrenilmis kodek: 3 tohum ----
AE = {s: ae_egit(s) for s in TOHUMLAR}
ae_tr = {}
ae_te = {}
for s, (enc, dec) in AE.items():
    with torch.no_grad():
        ae_tr[s] = enc(Xtr).numpy()
        ae_te[s] = enc(Xte).numpy()
m_ae, a_ae = [], []
for s, (enc, dec) in AE.items():
    with torch.no_grad():
        m, a = olc(dec(enc(Xte)).numpy())
    m_ae.append(m)
    a_ae.append(a)
print(f"AE-16 (float)     : MSE={np.mean(m_ae):.5f}  "
      f"dogruluk={np.mean(a_ae):.4f}")

# ---- Bit butcesi taramasi ----
satirlar = []
for p in PS:
    for b in BITLER:
        R = D * b
        sonuc = {"AE": [], "PCA": [], "DCT": []}
        for s in TOHUMLAR:
            rng = np.random.default_rng(100 + s)
            dec = AE[s][1]
            geri_ae = lambda z, d=dec: d(torch.tensor(
                z, dtype=torch.float32)).detach().numpy()
            sonuc["AE"].append(kodek_dene(
                "AE", b, p, rng, ae_tr[s], ae_te[s], geri_ae))
            sonuc["PCA"].append(kodek_dene(
                "PCA", b, p, rng, pca_tr, pca_te,
                pca.inverse_transform))
            sonuc["DCT"].append(kodek_dene(
                "DCT", b, p, rng, dtr, dte, dct_geri))
        for ad in ["AE", "PCA", "DCT"]:
            M = np.array([x[0] for x in sonuc[ad]])
            A = np.array([x[1] for x in sonuc[ad]])
            satirlar.append([ad, b, R, p, M.mean(), M.std(),
                             A.mean(), A.std()])

print()
print("== Bit butcesi taramasi (16 boyut, 3 tohum ortalamasi) ==")
for p in PS:
    print(f"-- kanal bit cevirme olasiligi p = {p}")
    print("b  R(bit)  AE_mse   AE_dog   PCA_mse  PCA_dog  "
          "DCT_mse  DCT_dog")
    for b in BITLER:
        r = {x[0]: x for x in satirlar if x[1] == b and x[3] == p}
        print(f"{b:<2} {D * b:<6} {r['AE'][4]:.5f}  {r['AE'][6]:.4f}"
              f"   {r['PCA'][4]:.5f}  {r['PCA'][6]:.4f}"
              f"   {r['DCT'][4]:.5f}  {r['DCT'][6]:.4f}")

with open(VERI + "/b72_kodek.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codec", "b", "R", "p", "mse", "mse_sd", "acc",
                "acc_sd"])
    for r in satirlar:
        w.writerow([r[0], r[1], r[2], r[3]] +
                   [f"{v:.6f}" for v in r[4:]])
print("CSV yazildi:", VERI + "/b72_kodek.csv")
