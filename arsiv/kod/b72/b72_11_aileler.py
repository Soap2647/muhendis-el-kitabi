# -*- coding: utf-8 -*-
"""Bolum 72.10: uretken model aileleri (VAE, DCGAN, DDPM) ayni veri
(digits) uzerinde; mini-FID, kesinlik/geri cagirma, sinif entropisi,
ezber orani ve ornekleme suresi.
Gercek test kumesi referans satiri."""
import csv
import numpy as np
from b72_veri import digits_bol, clf_yukle, OUT, VERI
from b72_metrik import tam_olcut

xtr, ytr, xte, yte = digits_bol(seed=0)
clf = clf_yukle(xtr, ytr)


def sure(ad):
    with open(OUT + "/zaman_%s.txt" % ad) as f:
        return float(f.read())


ailer = [
    ("VAE (d=8)", np.load(OUT + "/vae_ornek.npy"), sure("vae")),
    ("DCGAN", np.load(OUT + "/dcgan_ornek.npy"), sure("dcgan")),
    ("DDPM (T=200)", np.load(OUT + "/ddpm_ornek.npy"), sure("ddpm")),
    ("Gercek test", xte, 0.0),
]

print("== Ailer karsilastirmasi (digits, N=1000; test icin N=360) ==")
print("aile            mini-FID  kesin.  geri-c.  "
      "entropi  ezber  ms/ornek")
satirlar = []
for ad, x, ms in ailer:
    o = tam_olcut(x, xtr, clf, xte)
    print(f"{ad:<15} {o['fid']:8.2f}  {o['precision']:.3f}   "
          f"{o['recall']:.3f}   {o['entropi']:.3f}  {o['ezber']:.3f}"
          f"  {ms:.4f}")
    satirlar.append([ad, f"{o['fid']:.4f}", f"{o['precision']:.4f}",
                     f"{o['recall']:.4f}", f"{o['entropi']:.4f}",
                     f"{o['ezber']:.4f}", f"{ms:.6f}"])

with open(VERI + "/b72_aileler.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["aile", "fid", "precision", "recall", "entropi",
                "ezber", "ms"])
    w.writerows(satirlar)

# Izgara: her aileden 16 ornek + 16 gercek (figur icin)
rng = np.random.default_rng(0)
gercek = xte[rng.choice(len(xte), 16, replace=False)]
np.savez(VERI + "/b72_digits_izgara.npz",
         vae=ailer[0][1][:16].reshape(16, 8, 8),
         dcgan=ailer[1][1][:16].reshape(16, 8, 8),
         ddpm=ailer[2][1][:16].reshape(16, 8, 8),
         gercek=gercek.reshape(16, 8, 8))
print("CSV ve izgara yazildi.")
