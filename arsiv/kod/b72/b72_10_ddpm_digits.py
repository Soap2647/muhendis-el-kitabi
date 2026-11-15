# -*- coding: utf-8 -*-
"""Bolum 72.9: load_digits uzerinde kucuk U-Net ile DDPM egitimi ve
DDIM ile adim sayisina gore kalite. Olcutler: mini-FID, kesinlik/
geri cagirma, sinif entropisi, ezber orani ve ornekleme suresi."""
import csv
import time
import numpy as np
import torch
from b72_veri import digits_bol, clf_yukle, OUT, VERI
from b72_difuzyon import zamanlama, UNet8, egit, ornekle_ddpm, \
    ornekle_ddim
from b72_metrik import tam_olcut

T = 200
ITER = 6000
N = 1000
torch.manual_seed(0)

xtr, ytr, xte, yte = digits_bol(seed=0)
clf = clf_yukle(xtr, ytr)
beta, alfa, abar = zamanlama(T, "kosinus")
net = UNet8(k=32)
print("abar_T (kosinus, T=200) =", f"{abar[T]:.3e}")
print("U-Net parametre sayisi:",
      sum(p.numel() for p in net.parameters()))
print(f"== DDPM egitimi: kosinus takvimi, T={T}, {ITER} iterasyon ==")
Xs = (xtr * 2 - 1).reshape(-1, 1, 8, 8)
kg = egit(net, Xs, T, abar, ITER, batch=128, lr=2e-3, seed=0)
print(f"kayip ort. ilk 500: {np.mean(kg[:500]):.4f}  "
      f"son 500: {np.mean(kg[-500:]):.4f}")
torch.save(net.state_dict(), OUT + "/ddpm_unet.pt")
net.eval()


def geri(x):
    """[-1,1] uzayindan [0,1] piksel uzayina."""
    return ((x.numpy() + 1) / 2).clip(0, 1).reshape(len(x), 64)


satirlar = []
print()
print("== Ornekleme yontemi ve adim sayisi (N=1000) ==")
print("yontem      adim  mini-FID  kesin.  geri-c.  "
      "entropi  ezber  ms/ornek")
ornek_ddpm = None
for yontem, S in [("DDPM", T), ("DDIM", 5), ("DDIM", 10),
                  ("DDIM", 20), ("DDIM", 50), ("DDIM", 100),
                  ("DDIM", 200)]:
    t0 = time.perf_counter()
    if yontem == "DDPM":
        x = ornekle_ddpm(net, N, (1, 8, 8), T, beta, abar, clip=1.0,
                         seed=1)
    else:
        x = ornekle_ddim(net, N, (1, 8, 8), T, abar, S, clip=1.0,
                         seed=1)
    ms = (time.perf_counter() - t0) / N * 1e3
    g = geri(x)
    o = tam_olcut(g, xtr, clf, xte)
    print(f"{yontem:<10} {S:>4}  {o['fid']:8.2f}  "
          f"{o['precision']:.3f}"
          f"   {o['recall']:.3f}   {o['entropi']:.3f}"
          f"  {o['ezber']:.3f}"
          f"  {ms:7.3f}")
    satirlar.append([yontem, S, f"{o['fid']:.4f}",
                     f"{o['precision']:.4f}", f"{o['recall']:.4f}",
                     f"{o['entropi']:.4f}", f"{o['ezber']:.4f}",
                     f"{ms:.4f}"])
    if yontem == "DDPM":
        ornek_ddpm = g

np.save(OUT + "/ddpm_ornek.npy", ornek_ddpm)
with open(OUT + "/zaman_ddpm.txt", "w") as f:
    f.write(satirlar[0][-1])
with open(VERI + "/b72_adim_kalite.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "fid", "precision", "recall",
                "entropi", "ezber", "ms"])
    w.writerows(satirlar)
print("CSV yazildi:", VERI + "/b72_adim_kalite.csv")
