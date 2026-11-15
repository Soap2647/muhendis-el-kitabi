# -*- coding: utf-8 -*-
"""Bolum 72.12: sentetik veriyle veri artirma. Az veri (%10 = 144
ornek) sinifiricisi; (B) cVAE ornekleri (etiketli), (C) DDPM
ornekleri (etiketsiz; kucuk alt kume ile etiketlenir, guven > 0,9).
Test: 360 gercek ornek. 3 tohum."""
import csv
import numpy as np
from sklearn.model_selection import train_test_split
from b72_veri import digits_bol, sinif_egit, tahmin, OUT, VERI

xtr, ytr, xte, yte = digits_bol(seed=0)
cv = np.load(OUT + "/cvae_ornek.npz")
ddpm = np.load(OUT + "/ddpm_ornek.npy")
TOHUMLAR = [0, 1, 2]
rows = {"A: yalniz gercek (%10)": [], "B: + cVAE (500, etiketli)": [],
        "C: + DDPM (etiketlenmis, guven>0,9)": [],
        "D: tam egitim (%100, referans)": []}
kabul = []

for s in TOHUMLAR:
    sub_x, _, sub_y, _ = train_test_split(
        xtr, ytr, train_size=0.1, stratify=ytr, random_state=s)
    # cVAE: sinif basina 50 ornek
    idx = np.concatenate([np.where(cv["y"] == c)[0][:50]
                          for c in range(10)])
    cx, cy = cv["x"][idx], cv["y"][idx]
    # DDPM: alt kumeyle egitilmis etiketleyici, guven > 0,9
    etik = sinif_egit(sub_x, sub_y, seed=s)
    import torch
    with torch.no_grad():
        p = torch.softmax(etik(torch.tensor(ddpm)), 1).numpy()
    ok = p.max(1) > 0.9
    dx, dy = ddpm[ok][:500], p.argmax(1)[ok][:500]
    kabul.append(int(ok.sum()))
    kosullar = {
        "A: yalniz gercek (%10)": (sub_x, sub_y),
        "B: + cVAE (500, etiketli)": (
            np.concatenate([sub_x, cx]), np.concatenate([sub_y, cy])),
        "C: + DDPM (etiketlenmis, guven>0,9)": (
            np.concatenate([sub_x, dx]), np.concatenate([sub_y, dy])),
        "D: tam egitim (%100, referans)": (xtr, ytr),
    }
    for ad, (x, y) in kosullar.items():
        m = sinif_egit(x, y, seed=s)
        rows[ad].append(float((tahmin(m, xte) == yte).mean()))
    print(f"tohum {s}: DDPM guven>0,9 kabul = {ok.sum()} / 1000",
          flush=True)

print()
print("== Sinif dogrulugu (test 360, 3 tohum) ==")
out = []
for ad, v in rows.items():
    v = np.array(v)
    print(f"{ad:<38} {v.mean():.4f} +- {v.std():.4f}")
    out.append([ad, f"{v.mean():.4f}", f"{v.std():.4f}"])
print("DDPM kabul sayilari:", kabul)
with open(VERI + "/b72_artirma.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kosul", "dogruluk", "sd"])
    w.writerows(out)
print("CSV yazildi.")
