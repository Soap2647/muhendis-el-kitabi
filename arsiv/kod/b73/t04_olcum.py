# -*- coding: utf-8 -*-
"""Bolum 73 - t04: hizalama, tekduzelik, k-NN, yoklama ve t-SNE.

Tohum 0. Pikseller, rastgele ag, SimCLR, VICReg ve SimSiam (stop-
grad).
Hizalama icin ayni testten iki artirilmis gorunum (sabit tohum).
"""

import csv
import os
import numpy as np
import torch
from sklearn.manifold import TSNE
from ortak73 import (
    AYG,
    TUM,
    Enkoder,
    artir,
    egit,
    hizalama_tekduzelik,
    knn,
    ozellik,
    yoklama,
    yukle,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
i100 = np.concatenate(
    [np.arange(c * 500, c * 500 + 100) for c in range(4)]
)

torch.manual_seed(123)
Tg = torch.as_tensor(Tx, device=AYG)
V1 = artir(Tg, TUM).cpu().numpy()
V2 = artir(Tg, TUM).cpu().numpy()


def yukle_enc(yol):
    e = Enkoder().to(AYG)
    e.load_state_dict(
        torch.load(
            os.path.join(CK, yol), map_location=AYG, weights_only=True
        )
    )
    return e.eval()


encs = {
    "rastgele": egit("rastgele", Ux, 0),
    "simclr": yukle_enc("simclr_s0.pt"),
    "vicreg": egit("vicreg", Ux, 0),
    "simsiam": yukle_enc("simsiam_dur_s0.pt"),
}

satirlar = []
a, u = hizalama_tekduzelik(
    V1.reshape(len(V1), -1),
    V2.reshape(len(V2), -1),
    Tx.reshape(len(Tx), -1),
)
Fl = Lx.reshape(len(Lx), -1)
Ft = Tx.reshape(len(Tx), -1)
satirlar.append(
    (
        "piksel",
        a,
        u,
        knn(Fl, Ly, Ft, Ts),
        yoklama(Fl[i100], Ly[i100], Ft, Ts),
    )
)
print("piksel  hiz=%.4f tek=%.4f" % satirlar[-1][1:3], flush=True)
for ad, enc in encs.items():
    a, u = hizalama_tekduzelik(
        ozellik(enc, V1), ozellik(enc, V2), ozellik(enc, Tx)
    )
    Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
    satirlar.append(
        (
            ad,
            a,
            u,
            knn(Fl, Ly, Ft, Ts),
            yoklama(Fl[i100], Ly[i100], Ft, Ts),
        )
    )
    print(
        "%-8s hiz=%.4f tek=%.4f" % ((ad,) + satirlar[-1][1:3]),
        flush=True,
    )

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_hizalama.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(
        ["yontem", "hizalama", "tekduzelik", "knn500", "yoklama100"]
    )
    for s in satirlar:
        w.writerow(
            [
                s[0],
                "%.4f" % s[1],
                "%.4f" % s[2],
                "%.4f" % s[3],
                "%.4f" % s[4],
            ]
        )

# t-SNE: 1000 test ornegi, sekle gore renk
rng = np.random.default_rng(73)
idx = rng.choice(len(Tx), 1000, replace=False)
izdusum = [("piksel", Tx.reshape(len(Tx), -1)[idx])]
for ad in ("rastgele", "simclr", "vicreg", "simsiam"):
    izdusum.append((ad, ozellik(encs[ad], Tx)[idx]))
with open(
    os.path.join(VERI, "b73_tsne.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "x", "y", "sekil"])
    for ad, F in izdusum:
        p = TSNE(
            n_components=2, perplexity=30, init="pca", random_state=0
        ).fit_transform(F)
        for (x, y), s in zip(p, Ts[idx]):
            w.writerow([ad, "%.3f" % x, "%.3f" % y, int(s)])
        print("tsne %s tamam" % ad, flush=True)
