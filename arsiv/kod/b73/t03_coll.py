# -*- coding: utf-8 -*-
"""Bolum 73 - t03: cokme (collapse) izleme.

SimSiam stop-gradient ile ve stop-gradient olmadan; referans olarak
SimCLR. Her 500 adimda: projeksiyon ciktisinin SimSiam std olcusu ve
500 ornekli etiketli kumede k-NN dogrulugu (test kumesinde olcum).
"""

import csv
import os
import torch
from ortak73 import AYG, egit, knn, ozellik, std_olcu, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
kayit = []


def izle(ad):
    def cagri(adim, enc, bas):
        bas.eval()
        with torch.no_grad():
            z = (
                bas(enc(torch.as_tensor(Tx, device=AYG)))
                .cpu()
                .numpy()
            )
        bas.train()
        f_t, f_l = ozellik(enc, Tx), ozellik(enc, Lx)
        enc.train()
        kayit.append((ad, adim, std_olcu(z), knn(f_l, Ly, f_t, Ts)))
        print(
            ad,
            adim,
            "std=%.3f knn=%.3f" % (kayit[-1][2], kayit[-1][3]),
            flush=True,
        )

    return cagri


for ad, yontem, durdur in (
    ("simsiam_dur", "simsiam", True),
    ("simsiam_dursuz", "simsiam", False),
    ("simclr", "simclr", True),
):
    enc = egit(yontem, Ux, 0, durdur=durdur, geri_cagri=izle(ad))
    torch.save(enc.state_dict(), os.path.join(CK, "%s_s0.pt" % ad))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_cokme.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "std", "knn"])
    for r in kayit:
        w.writerow([r[0], r[1], "%.4f" % r[2], "%.4f" % r[3]])
