# -*- coding: utf-8 -*-
"""Bolum 73 - t05: artirma ablasyonu, tau ve batch taramasi (tohum 0).

Her kosu 3000 adim SimCLR on egitimidir (CPU; GPU Bolum 76'ya
ayrildi).
Referans yapilandirma (tam artirma, tau = 0.2, batch = 256) bir kez
egitilir ve artirma, tau ve batch tablolarinda kullanilir.
Olcum: n = 100 ve n = 500 (sinif basina) dogrusal yoklama; k-NN (n =
500).
"""

import csv
import os
import numpy as np
from ortak73 import TUM, egit, knn, ozellik, yoklama, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ADIM = 3000
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def olc(enc):
    Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
    return (
        yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
        yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
        knn(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
    )


sonuc = []


def kaydet(grup, deger, enc):
    p100, p500, k = olc(enc)
    sonuc.append((grup, deger, p100, p500, k))
    print(grup, deger, "%.3f %.3f %.3f" % (p100, p500, k), flush=True)


YOK = {"kirp": False, "renk": False, "gri": False, "flip": False}
ref = egit("simclr", Ux, 0, adim=ADIM)
kaydet("artirma", "tam", ref)
for ad, cfg in (
    ("kirpma_yok", {**TUM, "kirp": False}),
    ("renk_yok", {**TUM, "renk": False}),
    ("gri_yok", {**TUM, "gri": False}),
    ("aynalama_yok", {**TUM, "flip": False}),
    ("hicbiri", YOK),
):
    kaydet("artirma", ad, egit("simclr", Ux, 0, cfg=cfg, adim=ADIM))

for tau in (0.05, 0.1, 0.5, 1.0):
    kaydet("tau", str(tau), egit("simclr", Ux, 0, tau=tau, adim=ADIM))
kaydet("tau", "0.2", ref)

for bs in (64, 512):
    kaydet("batch", str(bs), egit("simclr", Ux, 0, bs=bs, adim=ADIM))
kaydet("batch", "256", ref)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_ablasyon.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(
        ["grup", "deger", "yoklama100", "yoklama500", "knn500"]
    )
    for s in sonuc:
        w.writerow(
            [s[0], s[1], "%.4f" % s[2], "%.4f" % s[3], "%.4f" % s[4]]
        )
