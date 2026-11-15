# -*- coding: utf-8 -*-
"""Bolum 71 - Referans tabanli degerlendirme: EM, icerme, token-F1."""

import re
from collections import Counter

import numpy as np

from g01_parca import SORULAR
from g02_geri_getirme import alaka_kumeleri, parcalar
from ortak import belirtecler, bm25_indeks, bm25_skor


def normalize(s):
    return " ".join(re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", s.lower()))


def f1(tahmin, altin):
    t, g = normalize(tahmin).split(), normalize(altin).split()
    ortak = sum((Counter(t) & Counter(g)).values())
    if ortak == 0:
        return 0.0
    hassasiyet, duyarlilik = ortak / len(t), ortak / len(g)
    return 2 * hassasiyet * duyarlilik / (hassasiyet + duyarlilik)


def en_iyi_cumle(parca, soru):
    """Soru kelimelerini en cok kapsayan cumle (ham belirtec)."""
    q = set(belirtecler(soru))
    cumleler = re.split(r"(?<=[.!?])\s+", parca)
    return max(cumleler, key=lambda c: len(q & set(belirtecler(c))))


if __name__ == "__main__":
    pl = parcalar("baslik", 600)
    idx = bm25_indeks([belirtecler(p["metin"], 5) for p in pl])
    em, icerme, f1s = [], [], []
    for soru, kanit in SORULAR:
        skor = bm25_skor(idx, belirtecler(soru, 5))
        ust = int(np.argmax(skor))
        tahmin = en_iyi_cumle(pl[ust]["metin"], soru)
        em.append(normalize(tahmin) == normalize(kanit))
        icerme.append(normalize(kanit) in normalize(tahmin))
        f1s.append(f1(tahmin, kanit))
    f1s = np.array(f1s)
    rng = np.random.default_rng(71)
    orneklem = [
        f1s[rng.integers(0, len(f1s), len(f1s))].mean()
        for _ in range(10000)
    ]
    lo, hi = np.percentile(orneklem, [2.5, 97.5])
    print(
        "soru=%d  EM=%.3f  icerme=%.3f  F1=%.3f  (%%95 GA %.3f-%.3f)"
        % (
            len(SORULAR),
            np.mean(em),
            np.mean(icerme),
            f1s.mean(),
            lo,
            hi,
        )
    )
