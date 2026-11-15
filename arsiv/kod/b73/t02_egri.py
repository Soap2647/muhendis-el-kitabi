# -*- coding: utf-8 -*-
"""Bolum 73 - t02: etiket sayisina gore dogruluk egrisi (3 tohum).

Yontemler: ham piksel, PCA, rastgele ag, SimCLR, VICReg, SimSiam
(hepsi dogrusal yoklama), denetimli (sifirdan, uctan uca) ve
SimCLR baslatmali ince ayar. Test: 2000 ornek (ayri tohum).
"""

import copy
import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.decomposition import PCA
from ortak73 import (
    AYG,
    TUM,
    Enkoder,
    artir,
    egit,
    ozellik,
    yoklama,
    yukle,
    tekrar,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
os.makedirs(CK, exist_ok=True)
NS = (10, 50, 100, 500)
TOHUM = (0, 1, 2)

d = yukle()
U, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]


def alt(n):
    """Her siniftan ilk n ornek (etiket butcesi)."""
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def sinif_dogruluk(enc, head, X, y):
    enc.eval()
    with torch.no_grad():
        p = head(enc(torch.as_tensor(X, device=AYG))).argmax(1)
    return float((p.cpu().numpy() == y).mean())


@tekrar()
def uctan_uca(
    enc, head, X, y, tohum, adim=3000, bs=64, lr=1e-3, lr_govde=None
):
    """Uctan uca egitim: govde + bas birlikte (artirma ile)."""
    torch.manual_seed(tohum)
    Xt = torch.as_tensor(X, device=AYG)
    yt = torch.as_tensor(y, device=AYG)
    opt = torch.optim.Adam(
        [
            {"params": enc.parameters(), "lr": lr_govde or lr},
            {"params": head.parameters(), "lr": lr},
        ]
    )
    enc.train()
    for _ in range(adim):
        idx = torch.randint(0, len(Xt), (bs,), device=AYG)
        loss = F.cross_entropy(
            head(enc(artir(Xt[idx], TUM))), yt[idx]
        )
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return enc.eval()


def denetimli_sifirdan(X, y, tohum):
    torch.manual_seed(tohum)
    enc = Enkoder().to(AYG)
    head = nn.Linear(256, 4).to(AYG)
    uctan_uca(enc, head, X, y, tohum)
    return sinif_dogruluk(enc, head, Tx, Ts)


def ince_ayar(enc0, X, y, tohum):
    enc = copy.deepcopy(enc0)
    torch.manual_seed(tohum)
    head = nn.Linear(256, 4).to(AYG)
    uctan_uca(enc, head, X, y, tohum, lr_govde=1e-4)
    return sinif_dogruluk(enc, head, Tx, Ts)


sonuc = []
# Deterministik taban cizgiler: ham piksel ve PCA(50)
Pf = U.reshape(len(U), -1)
pca = PCA(50, random_state=0).fit(Pf)
Tpix = Tx.reshape(len(Tx), -1)
for n in NS:
    i = alt(n)
    sonuc.append(
        (
            "piksel",
            n,
            0,
            yoklama(Lx[i].reshape(len(i), -1), Ly[i], Tpix, Ts),
        )
    )
    sonuc.append(
        (
            "pca",
            n,
            0,
            yoklama(
                pca.transform(Lx[i].reshape(len(i), -1)),
                Ly[i],
                pca.transform(Tpix),
                Ts,
            ),
        )
    )
    print("taban n=%d tamam" % n, flush=True)

for tohum in TOHUM:
    for yontem in ("rastgele", "simclr", "vicreg", "simsiam"):
        enc = egit(yontem, U, tohum)
        if yontem == "simclr":
            torch.save(
                enc.state_dict(),
                os.path.join(CK, "simclr_s%d.pt" % tohum),
            )
        Fl = ozellik(enc, Lx)
        Ft = ozellik(enc, Tx)
        for n in NS:
            i = alt(n)
            sonuc.append(
                (yontem, n, tohum, yoklama(Fl[i], Ly[i], Ft, Ts))
            )
        print(yontem, "tohum", tohum, "tamam", flush=True)
        if yontem == "simclr":
            for n in NS:
                i = alt(n)
                sonuc.append(
                    (
                        "simclr_ince",
                        n,
                        tohum,
                        ince_ayar(enc, Lx[i], Ly[i], tohum),
                    )
                )
    for n in NS:
        i = alt(n)
        sonuc.append(
            (
                "denetimli",
                n,
                tohum,
                denetimli_sifirdan(Lx[i], Ly[i], tohum),
            )
        )
    print("tohum", tohum, "denetimli ve ince ayar tamam", flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_etiket_egri.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "n_sinif", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])

print(
    "\nTest dogrulugu, ortalama +- sapma "
    "(tohum sayisi 3; piksel/PCA tek)"
)
for yo in (
    "piksel",
    "pca",
    "rastgele",
    "simclr",
    "vicreg",
    "simsiam",
    "simclr_ince",
    "denetimli",
):
    satir = []
    for n in NS:
        v = [s[3] for s in sonuc if s[0] == yo and s[1] == n]
        if len(v) > 1:
            satir.append(
                "%.3f+-%.3f" % (np.mean(v), np.std(v, ddof=1))
            )
        else:
            satir.append("%.3f      " % v[0])
    print("%-12s" % yo + "  ".join(satir))
print("sutunlar: n = 10, 50, 100, 500 (sinif basina)")
