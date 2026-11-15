# -*- coding: utf-8 -*-
"""Bolum 72.9: 2B halka uzerinde difuzyon. (A) takvimler ve ileri
surecin kapali formu, (B) gurultu tahmincisi egitimi, (C) DDPM ve
DDIM ornekleme, mod kapsami. Ciktilar engine/veri/b72_diff2d.npz."""
import math
import numpy as np
import torch
torch.set_num_threads(2)
from b72_veri import halka_veri, mod_olcutu, VERI, OUT
from b72_difuzyon import (zamanlama, MLP2D, egit, ornekle_ddpm,
                          ornekle_ddim)

T = 100
ITER = 15000
torch.manual_seed(0)

# ---------- (A) takvimler ve ileri surecin kapali formu ----------
beta_l, alfa_l, abar_l = zamanlama(T, "lineer")
beta_k, alfa_k, abar_k = zamanlama(T, "kosinus")
print("== A. Gurultu takvimleri: abar_t = prod(1 - beta_s) ==")
print("t     lineer abar_t   kosinus abar_t")
for t in [1, 10, 25, 50, 75, 100]:
    print(f"{t:<4}  {abar_l[t]:.6f}      {abar_k[t]:.6f}")
print(f"beta_1..beta_T araligi (lineer): {beta_l[1]:.4f} .. "
      f"{beta_l[T]:.4f}")
print(f"abar_T lineer = {abar_l[T]:.2e}  (sinyal neredeyse yok)")

# Kapali form dogrulamasi: q(x_t|x_0) ortalama = sqrt(abar) x0,
# varyans = 1 - abar
t = 50
x0 = np.array([2.0, 0.0], dtype=np.float32)
rng = np.random.default_rng(0)
eps = rng.standard_normal((200000, 2)).astype(np.float32)
xt = math.sqrt(abar_l[t]) * x0 + math.sqrt(1 - abar_l[t]) * eps
print()
print(f"== Kapali form kontrolu: t={t}, x0={x0.tolist()} ==")
print("ortalama MC:", xt.mean(0).round(4).tolist())
print("ortalama kapali:",
      (math.sqrt(abar_l[t]) * x0).round(4).tolist())
print("varyans MC:", xt.var(0).round(4).tolist())
print(f"varyans kapali: {1 - abar_l[t]:.4f}")

# ---------- (B) egitim ----------
xr, _ = halka_veri(20000, np.random.default_rng(2), sigma=0.02)
model = MLP2D(tdim=32)
print()
print(f"== B. Gurultu tahmincisi egitimi: {ITER} iterasyon ==")
kg = egit(model, xr, T, abar_l, ITER, batch=512, lr=1e-3, seed=0)
print(f"kayip ort. ilk 500: {np.mean(kg[:500]):.4f}  "
      f"son 500: {np.mean(kg[-500:]):.4f}")
torch.save(model.state_dict(), OUT + "/diff2d.pt")

# ---------- (C) ornekleme ve mod kapsami ----------
model.eval()
N = 2000
print()
print("== C. Ornekleme (2000 ornek; "
      "mod = merkeze 0,2 icinde >=%1) ==")
print("yontem            adim   modes   hq (merkeze 0,2 icinde)")
rows = []
x_ddpm = ornekle_ddpm(model, N, (2,), T, beta_l, abar_l,
                      clip=3.0, seed=1)
mo, hq = mod_olcutu(x_ddpm.numpy())
print(f"DDPM (ancestral)  {T:>4}   {mo:>3}     {hq:.3f}")
rows.append(("DDPM", T, mo, hq))
for S in [10, 20, 100]:
    xd = ornekle_ddim(model, N, (2,), T, abar_l, S, clip=3.0, seed=1)
    mo, hq = mod_olcutu(xd.numpy())
    print(f"DDIM (eta=0)      {S:>4}   {mo:>3}     {hq:.3f}")
    rows.append(("DDIM", S, mo, hq))

# ---------- Figur verisi: ileri ve ters surec ----------
ring, _ = halka_veri(500, np.random.default_rng(5), sigma=0.02)
fwd_t = [0, 25, 50, 75, 100]
fwd = []
for t in fwd_t:
    e = np.random.default_rng(10 + t).standard_normal(ring.shape)
    fwd.append(math.sqrt(abar_l[t]) * ring
               + math.sqrt(1 - abar_l[t]) * e)
rev_t = [100, 75, 50, 25, 1]
rev = {}


def anlik(tt, x):
    if tt in rev_t:
        rev[tt] = x.numpy().copy()


_ = ornekle_ddpm(model, 500, (2,), T, beta_l, abar_l, clip=3.0,
                 anlik=anlik, seed=2)
np.savez(VERI + "/b72_diff2d.npz",
         fwd=np.stack(fwd).astype(np.float32),
         rev=np.stack([rev[t] for t in rev_t]).astype(np.float32),
         rev_t=np.array(rev_t), fwd_t=np.array(fwd_t),
         ring=ring)
import csv
with open(VERI + "/b72_diff2d_adim.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "modes", "hq"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], f"{r[3]:.4f}"])
print("Ciktilar yazildi.")
