# -*- coding: utf-8 -*-
"""Bolum 73 - t08: mini-CLIP olcumleri.

Sifir atisli sekil siniflandirmasi (istem sablonu etkisi), renk+sekil
bilesimi (goerulmemis mavi ucgen dahil), geri getirme (Recall@k, 500
ornekli galeri), modalite boslugu ve goruntu ozellikleri uzerinde
dogrusal yoklama. Her iki egitim varyanti (naif ve maskeli) olculur.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth73 import KELIMELER, RENK_AD, SEKIL_AD, aciklama, belirtec
from ortak73 import AYG, ozellik, yoklama, yukle
from t07_clip_egit import GoruntuKod, MetinKod

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
d = yukle()
Tx, Tr, Ts, Tb, Tk = d["Tx"], d["Tr"], d["Ts"], d["Tb"], d["Tk"]
Lx, Ly = d["Lx"], d["Ly"]
MAVI, UCGEN = 2, 2
gorulmemis = (Tr == MAVI) & (Ts == UCGEN)


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


def yukle_clip(ad):
    p = torch.load(
        os.path.join(CK, "clip_%s.pt" % ad),
        map_location=AYG,
        weights_only=True,
    )
    gk = GoruntuKod().to(AYG)
    mk = MetinKod(len(KELIMELER)).to(AYG)
    gk.load_state_dict(p["gk"])
    mk.load_state_dict(p["mk"])
    return gk.eval(), mk.eval()


def gom_emb(gk, X):
    with torch.no_grad():
        z = gk(torch.as_tensor(X, device=AYG))
    return F.normalize(z, dim=1).cpu().numpy()


def metin_emb(mk, cumleler):
    ids = torch.as_tensor(
        np.array([belirtec(c) for c in cumleler]), device=AYG
    )
    with torch.no_grad():
        z = mk(ids)
    return F.normalize(z, dim=1).cpu().numpy()


def sinif_emb(mk, istemler):
    """Her sinif icin istem gomesi (birim vektor); liste -> (C, d)."""
    return metin_emb(mk, istemler)


def en_yakin(I, T):
    return (I @ T.T).argmax(1)


def olcum(ad):
    gk, mk = yukle_clip(ad)
    satirlar = []
    I = gom_emb(gk, Tx)

    # 1) sekil siniflandirmasi: istem sablonu etkisi
    sablonlar = [
        "{s}",
        "büyük {s}",
        "{s} ortada",
        "küçük {s} sol üstte",
    ]
    for sb in sablonlar:
        T = sinif_emb(mk, [sb.format(s=s) for s in SEKIL_AD])
        dog = (en_yakin(I, T) == Ts).mean()
        satirlar.append(("sekil_sablon", sb, dog))

    # 2) bilesimsel genelleme: 16 sinif (renk x sekil)
    sinif_ad = [(r, s) for r in range(4) for s in range(4)]
    T1 = sinif_emb(
        mk, ["%s %s" % (RENK_AD[r], SEKIL_AD[s]) for r, s in sinif_ad]
    )
    T2 = []
    for r, s in sinif_ad:
        ornek = [
            aciklama(r, b, s, k) for b in range(2) for k in range(5)
        ]
        v = metin_emb(mk, ornek).mean(0)
        T2.append(v / np.linalg.norm(v))
    T2 = np.array(T2)
    yc = Tr * 4 + Ts
    for ad2, T in (("renk_sekil", T1), ("tam_cumle_topluluk", T2)):
        p = en_yakin(I, T)
        ok = p == yc
        satirlar.append(
            ("bilesim", ad2 + "_gorulen", ok[~gorulmemis].mean())
        )
        satirlar.append(
            ("bilesim", ad2 + "_gorulmemis", ok[gorulmemis].mean())
        )

    # 3) geri getirme: 500 ornekli galeri
    n = 500
    caps = [aciklama(Tr[i], Tb[i], Ts[i], Tk[i]) for i in range(n)]
    Ig = I[:n]
    Tg = metin_emb(mk, caps)
    Sm = Ig @ Tg.T
    for k in (1, 5):
        i2t = np.mean(
            [
                any(
                    caps[j] == caps[i] for j in np.argsort(-Sm[i])[:k]
                )
                for i in range(n)
            ]
        )
        t2i = np.mean(
            [
                any(
                    caps[i] == caps[j]
                    for i in np.argsort(-Sm[:, j])[:k]
                )
                for j in range(n)
            ]
        )
        satirlar.append(
            ("geri_getirme", "gorsel_metin_R@%d" % k, i2t)
        )
        satirlar.append(
            ("geri_getirme", "metin_gorsel_R@%d" % k, t2i)
        )

    # 4) modalite boslugu
    fark = np.linalg.norm(Ig.mean(0) - Tg.mean(0))
    eslesen = np.mean(np.diag(Sm))
    rast = np.mean(
        [
            Sm[i, j]
            for i in range(n)
            for j in range(n)
            if caps[i] != caps[j]
        ]
    )
    satirlar.append(("modalite", "ort_vektor_farki", fark))
    satirlar.append(("modalite", "eslesen_cos", eslesen))
    satirlar.append(("modalite", "rastgele_cos", rast))

    # 5) goruntu ozellikleri uzerinde dogrusal yoklama (sekil)
    Fl, Ft = ozellik(gk.govde, Lx), ozellik(gk.govde, Tx)
    for m in (100, 500):
        satirlar.append(
            (
                "yoklama",
                "n%d" % m,
                yoklama(Fl[alt(m)], Ly[alt(m)], Ft, Ts),
            )
        )
    return satirlar, Sm[:4, :4], caps[:4]


if __name__ == "__main__":
    tum = []
    for ad in ("naif", "maskeli"):
        sat, mat, ornek = olcum(ad)
        for s in sat:
            tum.append((ad,) + s[:2] + ("%.4f" % s[2],))
            print(ad, s[0], s[1], "%.4f" % s[2], flush=True)
        if ad == "maskeli":
            os.makedirs(VERI, exist_ok=True)
            with open(
                os.path.join(VERI, "b73_clip_matris.csv"),
                "w",
                newline="",
                encoding="utf-8",
            ) as f:
                w = csv.writer(f)
                w.writerow(["ornek"] + ["%d" % i for i in range(4)])
                for i in range(4):
                    w.writerow(
                        [ornek[i]] + ["%.4f" % v for v in mat[i]]
                    )
            for o in ornek:
                print("ornek:", o, flush=True)
    os.makedirs(VERI, exist_ok=True)
    with open(
        os.path.join(VERI, "b73_clip.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "grup", "olcut", "deger"])
        for r in tum:
            w.writerow(list(r))
    print("gorulmemis test ornegi sayisi:", int(gorulmemis.sum()))
