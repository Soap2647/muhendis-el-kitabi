# -*- coding: utf-8 -*-
"""Bolum 72.4: dogrusal autoencoder ile PCA ayni alt uzayi bulur mu?
Veri: load_digits (64 boyut). Her k ve tohum icin test hatasi ve
iki alt uzay arasindaki en buyuk ana aci olculur."""
import csv
import numpy as np
import torch
import torch.nn as nn
from scipy.linalg import subspace_angles
from sklearn.decomposition import PCA
from b72_veri import digits_bol, VERI

KS = [2, 4, 8, 16]
TOHUMLAR = [0, 1, 2]
ADIM = 4000

xtr, ytr, xte, yte = digits_bol(seed=0)
Xtr = torch.tensor(xtr)
Xte = torch.tensor(xte)


def dogrusal_ae(k, seed):
    torch.manual_seed(seed)
    enc = nn.Linear(64, k)
    dec = nn.Linear(k, 64)
    opt = torch.optim.Adam(
        list(enc.parameters()) + list(dec.parameters()), lr=1e-2)
    for _ in range(ADIM):
        kayip = ((dec(enc(Xtr)) - Xtr) ** 2).mean()
        opt.zero_grad()
        kayip.backward()
        opt.step()
    return enc, dec


satirlar = []
print("== Dogrusal AE vs PCA (test MSE, en buyuk ana aci) ==")
print("k    PCA_mse    AE_mse(ort)  AE_sapma   aci_max(ort)")
for k in KS:
    pca = PCA(n_components=k).fit(xtr)
    rec = pca.inverse_transform(pca.transform(xte))
    pca_mse = float(((rec - xte) ** 2).mean())
    ae_mse, acilar = [], []
    for s in TOHUMLAR:
        enc, dec = dogrusal_ae(k, s)
        with torch.no_grad():
            r = dec(enc(Xte)).numpy()
        ae_mse.append(float(((r - xte) ** 2).mean()))
        # Decoder agirliklari (64 x k) ile PCA bilesenleri (64 x k)
        W = dec.weight.detach().numpy()
        P = pca.components_.T
        ac = subspace_angles(W, P)
        acilar.append(float(np.degrees(ac).max()))
    m_ae, s_ae = np.mean(ae_mse), np.std(ae_mse)
    m_ac, s_ac = np.mean(acilar), np.std(acilar)
    print(f"{k:<4} {pca_mse:.6f}  {m_ae:.6f}  {s_ae:.6f}  "
          f"{m_ac:6.3f}+-{s_ac:.3f}")
    satirlar.append([k, pca_mse, m_ae, s_ae, m_ac, s_ac])

with open(VERI + "/b72_pca_ae.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["k", "pca_mse", "ae_mse", "ae_sd", "aci_deg",
                "aci_sd"])
    for r in satirlar:
        w.writerow([f"{v:.6f}" if isinstance(v, float) else v
                    for v in r])
print("CSV yazildi:", VERI + "/b72_pca_ae.csv")
