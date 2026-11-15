# -*- coding: utf-8 -*-
"""Bolum 72.9: kosullu difuzyon ve sinifsiz yonlendirme (classifier-
free guidance) 2B halka uzerinde. Kosul: hedef mod (0..7); kosulsuz
anahtar: 8. Egitimde kosul %10 oraninda dusurulur."""
import csv
import numpy as np
import torch
from b72_veri import halka_veri, mod_olcutu, MERKEZ, VERI, OUT
from b72_difuzyon import (zamanlama, MLP2D, egit, ornekle_ddpm)

T = 100
NC = 8
ITER = 15000
torch.manual_seed(0)

beta, alfa, abar = zamanlama(T, "lineer")
X, k = halka_veri(20000, np.random.default_rng(3), sigma=0.02)
model = MLP2D(tdim=32, nc=NC)
print(f"== Kosullu egitim: {ITER} iterasyon, kosul dusurme = %10 ==")
kg = egit(model, X, T, abar, ITER, batch=512, lr=1e-3,
          etiket=k, p_dusur=0.1, seed=0, nc=NC)
print(f"kayip ort. ilk 500: {np.mean(kg[:500]):.4f}  "
      f"son 500: {np.mean(kg[-500:]):.4f}")
torch.save(model.state_dict(), OUT + "/cfg2d.pt")
model.eval()

# Her hedef mod icin 250 ornek; isabet = en yakin merkez hedef ve
# merkeze 0,2 icinde.
print()
print("== Yonlendirme olcegi w: hedef moda uzaklik ==")
print("(veri: sigma=0.02; radyal ort. ~0,025, sd ~0,015)")
print("w     isabet        hq      r_ort (hedef)  r_sd (hedef)")
satirlar = []
for w in [0.0, 1.0, 3.0]:
    isabet, hqs, ro, rs = [], [], [], []
    for h in range(NC):
        c = torch.full((250,), h, dtype=torch.long)
        x = ornekle_ddpm(model, 250, (2,), T, beta, abar, c=c, w=w,
                         nc=NC, clip=3.0, seed=100 + h).numpy()
        d = np.linalg.norm(x[:, None, :] - MERKEZ[None], axis=2)
        en = d.argmin(1)
        yakin = d.min(1) <= 0.2
        isabet.append(float(((en == h) & yakin).mean()))
        hqs.append(float(yakin.mean()))
        dh = np.linalg.norm(x - MERKEZ[h], axis=1)
        sec = dh <= 0.2
        ro.append(float(dh[sec].mean()))
        rs.append(float(dh[sec].std()))
    print(f"{w:<4}  {np.mean(isabet):.3f} +- {np.std(isabet):.3f}"
          f"  {np.mean(hqs):.3f}  {np.mean(ro):.4f}         "
          f"{np.mean(rs):.4f}")
    satirlar.append([w, f"{np.mean(isabet):.4f}",
                     f"{np.mean(hqs):.4f}",
                     f"{np.mean(ro):.4f}", f"{np.mean(rs):.4f}"])

with open(VERI + "/b72_cfg2d.csv", "w", newline="",
          encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["w", "isabet", "hq", "r_ort", "r_sd"])
    wr.writerows(satirlar)
print("CSV yazildi.")
