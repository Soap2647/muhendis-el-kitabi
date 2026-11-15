# -*- coding: utf-8 -*-
"""Bolum 73 - t09: saglamlik (alan kaymasi) ve gomme tabanli kopya
tespiti.

(a) Siniflandirici temiz egitim verisinin n = 100 / sinif ornegiyle
    egitilir; test kumesi gurultu, kontrast ve bulaniklikla bozulur.
(b) Kopya tespiti: 2000 ornekli galeride her sorgu, ayni resmin
    bozulmus kopyasidir; en yakin komsu dogru mu?
"""

import csv
import os
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from ortak73 import AYG, Enkoder, bozulma, egit, ozellik, yukle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
idx100 = np.concatenate(
    [np.arange(c * 500, c * 500 + 100) for c in range(4)]
)

simclr = Enkoder().to(AYG)
simclr.load_state_dict(
    torch.load(
        os.path.join(CK, "simclr_s0.pt"),
        map_location=AYG,
        weights_only=True,
    )
)
simclr.eval()
rastgele = egit("rastgele", Ux, 0)
ozel = {"piksel": None, "rastgele": rastgele, "simclr": simclr}


def oz(yontem, X):
    if yontem == "piksel":
        return X.reshape(len(X), -1)
    return ozellik(ozel[yontem], X)


def sinif_egit(F, y):
    sc = StandardScaler().fit(F)
    clf = LogisticRegression(max_iter=3000, random_state=0)
    clf.fit(sc.transform(F), y)
    return lambda G, yy: clf.score(sc.transform(G), yy)


BOZ = [
    ("temiz", 0.0),
    ("gurultu", 0.1),
    ("gurultu", 0.2),
    ("gurultu", 0.3),
    ("kontrast", 0.3),
    ("kontrast", 0.6),
    ("bulaniklik", 1),
    ("bulaniklik", 2),
]
rng = np.random.default_rng(77)
satirlar = []
for yontem in ("piksel", "rastgele", "simclr"):
    skor = sinif_egit(oz(yontem, Lx[idx100]), Ly[idx100])
    for tur, s in BOZ:
        Xc = bozulma(Tx, tur, s, rng) if tur != "temiz" else Tx
        acc = skor(oz(yontem, Xc), Ts)
        satirlar.append(("saglamlik", yontem, tur, s, acc))
        print(yontem, tur, s, "%.3f" % acc, flush=True)

# Kopya tespiti: sorgu = galeri ornegi + bozulma; en yakin komsu
# (top-1)
kop = []
for yontem in ("piksel", "rastgele", "simclr"):
    G = oz(yontem, Tx)
    G = G / np.linalg.norm(G, axis=1, keepdims=True)
    for tur, s in (("gurultu", 0.2), ("kontrast", 0.5)):
        Q = bozulma(Tx[:500], tur, s, rng)
        Qf = oz(yontem, Q)
        Qf = Qf / np.linalg.norm(Qf, axis=1, keepdims=True)
        top1 = (np.argmax(Qf @ G.T, axis=1) == np.arange(500)).mean()
        kop.append((yontem, tur, s, top1))
        print("kopya", yontem, tur, s, "%.3f" % top1, flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_saglamlik.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["grup", "yontem", "tur", "siddet", "dogruluk"])
    for r in satirlar:
        w.writerow([r[0], r[1], r[2], r[3], "%.4f" % r[4]])
    for r in kop:
        w.writerow(["kopya", r[0], r[1], r[2], "%.4f" % r[3]])
