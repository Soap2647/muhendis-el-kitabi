# -*- coding: utf-8 -*-
"""Bolum 75: bilgi damitma. Buyuk ogretmen (512-512) -> kucuk ogrenci
(32 gizli noron). Ogrenci: sifirdan (CE) ve damitma (T = 2, 4, 8)."""

import copy
import csv
import os
import torch
import torch.nn.functional as F
from b75_ortak import veri, mlp, mlp_t, egit, dogruluk, TOHUMLAR

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def damit_egit(
    ogrenci, X, y, ogretmen_logit, T, alfa, epoch=60, lr=1e-3, tohum=0
):
    """L = (1 - alfa) * CE(y, s) + alfa * T^2 * KL(p_t^T || p_s^T)."""
    torch.manual_seed(tohum)
    opt = torch.optim.Adam(ogrenci.parameters(), lr=lr)
    n = len(X)
    for _ in range(epoch):
        perm = torch.randperm(n)
        for i in range(0, n, 64):
            idx = perm[i : i + 64]
            s = ogrenci(X[idx])
            ce = F.cross_entropy(s, y[idx])
            kl = F.kl_div(
                F.log_softmax(s / T, dim=1),
                F.softmax(ogretmen_logit[idx] / T, dim=1),
                reduction="batchmean",
            )
            kayip = (1 - alfa) * ce + alfa * T * T * kl
            opt.zero_grad()
            kayip.backward()
            opt.step()
    return ogrenci


def parametre(m):
    return sum(p.numel() for p in m.parameters())


def main():
    satirlar = []
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        ogretmen = mlp_t(t, gizli=(512, 512))
        egit(ogretmen, Xtr, ytr, tohum=t)
        ogretmen.eval()
        with torch.no_grad():
            zt = ogretmen(Xtr)
        ogr_acc = dogruluk(ogretmen, Xte, yte)
        ogr_p = parametre(ogretmen)
        satirlar.append(
            dict(
                yontem="ogretmen_512_512",
                tohum=t,
                dogruluk=round(ogr_acc, 4),
                parametre=ogr_p,
            )
        )
        # Sifirdan egitilmis ogrenci (ayni mimari, sadece CE)
        sif = mlp_t(t, gizli=(32,))
        egit(sif, Xtr, ytr, tohum=t)
        satirlar.append(
            dict(
                yontem="ogrenci_sifirdan",
                tohum=t,
                dogruluk=round(dogruluk(sif, Xte, yte), 4),
                parametre=parametre(sif),
            )
        )
        for T in [2, 4, 8]:
            o = mlp_t(t, gizli=(32,))
            damit_egit(o, Xtr, ytr, zt, T=T, alfa=0.5, tohum=t)
            satirlar.append(
                dict(
                    yontem="ogrenci_damitma_T%d" % T,
                    tohum=t,
                    dogruluk=round(dogruluk(o, Xte, yte), 4),
                    parametre=parametre(o),
                )
            )
        for s in satirlar[-5:]:
            print(
                s["yontem"], s["tohum"], s["dogruluk"], s["parametre"]
            )
    yol = os.path.join(VERI, "b75_damitma.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yol)


if __name__ == "__main__":
    torch.set_num_threads(4)
    main()
