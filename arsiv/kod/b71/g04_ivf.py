# -*- coding: utf-8 -*-
"""Bolum 71 - Kaba kuvvet ve IVF (ters dosya) ile yaklasik arama."""

import csv
import os
import time

import numpy as np

from ortak import VERI

SEED = 71
N, D, KUME, SORGU, K = 200_000, 64, 200, 500, 10
NLIST = 256


def veri_uret(rng, n, merkezler, gurultu):
    kume = rng.integers(0, len(merkezler), size=n)
    x = merkezler[kume] + gurultu * rng.standard_normal((n, D))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    return x.astype(np.float32)


def kmeans(x, k, rng, iter_sayisi=12):
    """Lloyd algoritmasi; baslangic merkezleri rastgele veri
    noktalari."""
    c = x[rng.choice(len(x), size=k, replace=False)].copy()
    for _ in range(iter_sayisi):
        # |x - c|^2 = |x|^2 - 2 x.c + |c|^2 ; |x|^2 sabit, atilabilir
        uzaklik = -2.0 * (x @ c.T) + np.sum(c * c, axis=1)
        etiket = np.argmin(uzaklik, axis=1)
        for j in range(k):
            m = etiket == j
            if m.any():
                c[j] = x[m].mean(axis=0)
    uzaklik = -2.0 * (x @ c.T) + np.sum(c * c, axis=1)
    return c, np.argmin(uzaklik, axis=1)


def ivf_kur(x, c, etiket):
    listeler = [[] for _ in range(len(c))]
    sira = np.argsort(etiket, kind="stable")
    sinir = np.searchsorted(etiket[sira], np.arange(len(c) + 1))
    for j in range(len(c)):
        listeler[j] = sira[sinir[j] : sinir[j + 1]]
    return listeler


def ara_ivf(q, x, c, listeler, nprobe):
    merkez_skor = c @ q
    secilen = np.argpartition(-merkez_skor, nprobe - 1)[:nprobe]
    aday = np.concatenate([listeler[j] for j in secilen])
    skor = x[aday] @ q
    ust = np.argpartition(-skor, K - 1)[:K]
    ust = ust[np.argsort(-skor[ust])]
    return aday[ust], len(aday)


def ara_kaba(q_all, x):
    skor = q_all @ x.T
    return np.argsort(-skor, axis=1)[:, :K]


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    merkezler = rng.standard_normal((KUME, D)).astype(np.float32)
    merkezler /= np.linalg.norm(merkezler, axis=1, keepdims=True)
    x = veri_uret(rng, N, merkezler, 0.35)
    q = veri_uret(
        np.random.default_rng(SEED + 1), SORGU, merkezler, 0.35
    )
    gercek = ara_kaba(q, x)
    t0 = time.perf_counter()
    for i in range(SORGU):
        ara_kaba(q[i : i + 1], x)
    kaba_ms = (time.perf_counter() - t0) * 1000 / SORGU
    c, etiket = kmeans(x, NLIST, np.random.default_rng(SEED))
    listeler = ivf_kur(x, c, etiket)
    boyutlar = np.array([len(l) for l in listeler])
    print(
        "N=%d d=%d nlist=%d  liste boyu: ort=%.0f maks=%d min=%d"
        % (
            N,
            D,
            NLIST,
            boyutlar.mean(),
            boyutlar.max(),
            boyutlar.min(),
        )
    )
    print("kaba kuvvet: %.3f ms/sorgu" % kaba_ms)
    satirlar = [
        {
            "nprobe": 0,
            "recall10": 1.0,
            "taranan_oran": 1.0,
            "ms_sorgu": round(kaba_ms, 3),
        }
    ]
    print(
        "%7s %9s %12s %10s"
        % ("nprobe", "recall@10", "taranan(%)", "ms/sorgu")
    )
    for nprobe in [1, 2, 4, 8, 16, 32, 64]:
        t0 = time.perf_counter()
        isabet, taranan = 0, 0
        for i in range(SORGU):
            bulunan, t = ara_ivf(q[i], x, c, listeler, nprobe)
            isabet += len(set(bulunan) & set(gercek[i]))
            taranan += t
        ms = (time.perf_counter() - t0) * 1000 / SORGU
        rec = isabet / (SORGU * K)
        oran = taranan / (SORGU * N)
        print(
            "%7d %9.3f %12.2f %10.3f" % (nprobe, rec, 100 * oran, ms)
        )
        satirlar.append(
            {
                "nprobe": nprobe,
                "recall10": round(rec, 4),
                "taranan_oran": round(oran, 4),
                "ms_sorgu": round(ms, 3),
            }
        )
    with open(
        os.path.join(VERI, "b71_ivf.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
