# -*- coding: utf-8 -*-
"""Bolum 71 - Seyrek (BM25), yogun (LSA) ve

melez (RRF) geri getirme."""

import csv
import math
import os

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from g01_parca import (
    SORULAR,
    bolumleri_oku,
    sabit_parcalar,
    baslik_parcalari,
    duzlestir,
)
from ortak import belirtecler, bm25_indeks, bm25_skor
from ortak import VERI

KOK5 = 5
K_LIST = [1, 3, 5]
RRF_K = 60


def parcalar(ad, boyut):
    """ad: 'sabit' (ortusmesiz), 'sabit20' (%20 ortusme), 'baslik'."""
    sonuc = []
    for n, pars in bolumleri_oku():
        duz = " ".join(p for _, p in pars)
        if ad == "sabit":
            sonuc += sabit_parcalar(duz, boyut, 0, n)
        elif ad == "sabit20":
            sonuc += sabit_parcalar(duz, boyut, boyut // 5, n)
        else:
            sonuc += baslik_parcalari(pars, n, boyut)
    return sonuc


def alaka_kumeleri(parca_listesi):
    """Her soru icin kanitin gectigi parcalarin indeks kumesi."""
    norm = [duzlestir(p["metin"]) for p in parca_listesi]
    rel = []
    for soru, kanit in SORULAR:
        k = duzlestir(kanit)
        rel.append({i for i, m in enumerate(norm) if k in m})
    return rel


def sirala(skor):
    return np.argsort(-skor, kind="stable")


def rr_ve_geri(skor, rel):
    """Ilk alakali parcanin sirasi (1-tabanli) ve nDCG@5 (ikili
    alaka)."""
    sira = sirala(skor)
    if not rel:
        return float("inf"), 0.0
    konum = [i + 1 for i, d in enumerate(sira) if d in rel]
    rr = konum[0] if konum else float("inf")
    dcg = 0.0
    for i, d in enumerate(sira[:5]):
        if d in rel:
            dcg += 1.0 / math.log2(i + 2)
    idcg = sum(
        1.0 / math.log2(i + 2) for i in range(min(5, len(rel)))
    )
    return rr, dcg / idcg


def ozet(rrs, ndcgs):
    rr = np.array(rrs)
    out = {}
    for k in K_LIST:
        out["R@%d" % k] = float(np.mean(rr <= k))
    out["MRR"] = float(np.mean(np.where(np.isinf(rr), 0, 1.0 / rr)))
    out["nDCG5"] = float(np.mean(ndcgs))
    return out


def lsa_gomme(metinler, sorgular_metin, bilesen=128):
    vek = TfidfVectorizer(
        analyzer=lambda s: belirtecler(s, KOK5), sublinear_tf=True
    )
    X = vek.fit_transform(metinler)
    svd = TruncatedSVD(n_components=bilesen, random_state=71)
    D = svd.fit_transform(X)
    D = D / (np.linalg.norm(D, axis=1, keepdims=True) + 1e-12)
    Q = svd.transform(vek.transform(sorgular_metin))
    Q = Q / (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-12)
    return Q @ D.T


def rrf(*sira_listeleri, n):
    skor = np.zeros(n)
    for skor_dizisi in sira_listeleri:
        sira = sirala(skor_dizisi)
        for r, d in enumerate(sira):
            skor[d] += 1.0 / (RRF_K + r + 1)
    return skor


def degerlendir(parca_listesi, rel, ad_etiket, boyut_etiket):
    metinler = [p["metin"] for p in parca_listesi]
    N = len(metinler)
    sorgu_metni = [s for s, _ in SORULAR]
    ham_idx = bm25_indeks([belirtecler(m) for m in metinler])
    kok_idx = bm25_indeks([belirtecler(m, KOK5) for m in metinler])
    lsa = lsa_gomme(metinler, sorgu_metni)
    sonuclar = {}
    yontemler = {
        "rastgele": [],
        "BM25 ham": [],
        "BM25 kök5": [],
        "LSA (128)": [],
        "melez RRF": [],
    }
    ndcg = {k: [] for k in yontemler}
    for qi, (soru, _) in enumerate(SORULAR):
        r = rel[qi]
        rng = np.random.default_rng(71 + qi)
        skorlar = {
            "rastgele": rng.random(N),
            "BM25 ham": np.array(
                bm25_skor(ham_idx, belirtecler(soru))
            ),
            "BM25 kök5": np.array(
                bm25_skor(kok_idx, belirtecler(soru, KOK5))
            ),
            "LSA (128)": lsa[qi],
        }
        skorlar["melez RRF"] = rrf(
            skorlar["BM25 kök5"], skorlar["LSA (128)"], n=N
        )
        for y, s in skorlar.items():
            rr, nd = rr_ve_geri(s, r)
            yontemler[y].append(rr)
            ndcg[y].append(nd)
    for y in yontemler:
        sonuclar[y] = ozet(yontemler[y], ndcg[y])
    return sonuclar, yontemler, ndcg


def tablo_yaz(baslik, sonuclar):
    print(baslik)
    print(
        "%-12s %6s %6s %6s %7s %7s"
        % ("yontem", "R@1", "R@3", "R@5", "MRR", "nDCG5")
    )
    for y, s in sonuclar.items():
        print(
            "%-12s %6.3f %6.3f %6.3f %7.3f %7.3f"
            % (y, s["R@1"], s["R@3"], s["R@5"], s["MRR"], s["nDCG5"])
        )


if __name__ == "__main__":
    kayitlar = []
    deneyler = [
        ("sabit", 150),
        ("sabit", 300),
        ("sabit20", 300),
        ("sabit", 600),
        ("sabit20", 600),
        ("sabit", 1200),
        ("baslik", 300),
        ("baslik", 600),
        ("baslik", 1200),
    ]
    for ad, boyut in deneyler:
        pl = parcalar(ad, boyut)
        rel = alaka_kumeleri(pl)
        kanitsiz = sum(1 for r in rel if not r)
        s, _, _ = degerlendir(pl, rel, ad, boyut)
        tablo_yaz(
            "== %s-%d: %d parca, kanit bolunmesi (kayip) = %d/%d"
            % (ad, boyut, len(pl), kanitsiz, len(SORULAR)),
            s,
        )
        for y, v in s.items():
            kayitlar.append(
                {
                    "strateji": ad,
                    "boyut": boyut,
                    "parca": len(pl),
                    "yontem": y,
                    "kayip": kanitsiz,
                    **{k: round(x, 4) for k, x in v.items()},
                }
            )
    with open(
        os.path.join(VERI, "b71_parca_recall.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(kayitlar[0].keys()))
        w.writeheader()
        w.writerows(kayitlar)
