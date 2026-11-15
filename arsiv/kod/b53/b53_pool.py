# -*- coding: utf-8 -*-
"""b53_pool.py - surec havuzu: chunksize, serilestirme, is buyuklugu.

Calistirma: python -I b53_pool.py
Windows'ta multiprocessing 'spawn' kullanir: ana kod MUTLAKA
if __name__ == "__main__" blogu icinde olmali.
Cikti: engine\\veri\\b53_pool.csv (deney, parametre, tekrar, sure_s)
"""
import csv
import statistics
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HAVUZ = 8
TEKRAR = 3
CIKTI = "b53_pool.csv"


def hafif(x):
    return (x * x) % 1000003


def agir(n):
    s = 0
    for k in range(n):
        s += k * k % 7
    return s


def dizi_ile(dizi):
    return float(dizi.sum())


def uret_ile(args):
    tohum, boyut = args
    return float(np.random.default_rng(tohum).random(boyut).sum())


def olc(fn, girdi, ex, chunk):
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        list(ex.map(fn, girdi, chunksize=chunk))
        zs.append(time.perf_counter() - t0)
    return statistics.median(zs)


if __name__ == "__main__":
    satirlar = []

    def kaydet(deney, parametre, sure):
        satirlar.append((deney, parametre, sure))
        print(f"{deney:<12s} {str(parametre):<14s} {sure:8.4f} s")

    # 0. Havuz kurulum maliyeti (Windows: yeni yorumlayici acilir).
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
            list(ex.map(hafif, range(HAVUZ)))
        zs.append(time.perf_counter() - t0)
    kaydet("kurulum", "8 surec", statistics.median(zs))

    # 1. chunksize etkisi: 100000 hafif is.
    N = 100000
    girdi = list(range(N))
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        sum(hafif(x) for x in girdi)
        zs.append(time.perf_counter() - t0)
    seri_ref = statistics.median(zs)
    kaydet("seri", N, seri_ref)
    varsayilan, kalan = divmod(N, HAVUZ * 4)     # Pool.map formulu
    if kalan:
        varsayilan += 1
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        list(ex.map(hafif, range(HAVUZ)))         # isinma
        for c in (1, 10, 100, 1000, 10000, varsayilan):
            kaydet("chunksize", c, olc(hafif, girdi, ex, c))

    # 2. Is buyuklugu: 200 agir is, her biri 200000 dongu.
    agir_girdi = [200000] * 200
    zs = []
    for _ in range(TEKRAR):
        t0 = time.perf_counter()
        for n in agir_girdi:
            agir(n)
        zs.append(time.perf_counter() - t0)
    kaydet("agir_seri", "200x200000", statistics.median(zs))
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        list(ex.map(agir, [1000] * HAVUZ))
        kaydet("agir_surec", "200x200000",
               olc(agir, agir_girdi, ex, 4))

    # 3. Serilestirme: 8 MB dizi argumanla mi, surecte mi?
    boyut = 1000000
    tohumlar = list(range(50))
    diziler = [np.random.default_rng(t).random(boyut)
               for t in tohumlar]
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        list(ex.map(uret_ile, [(0, 10)] * HAVUZ))
        kaydet("arg_dizi", "50x8MB",
               olc(dizi_ile, diziler, ex, 1))
        kaydet("surec_uret", "50 tohum",
               olc(uret_ile, [(t, boyut) for t in tohumlar], ex, 1))
    # Dogruluk: iki yol da ayni toplamlari vermeli.
    ref = [float(d.sum()) for d in diziler]
    with ProcessPoolExecutor(max_workers=HAVUZ) as ex:
        a = list(ex.map(dizi_ile, diziler))
        b = list(ex.map(uret_ile, [(t, boyut) for t in tohumlar]))
    print("dogruluk (arg):", a == ref, " (uret):", b == ref)

    with open(CIKTI, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["deney", "parametre", "tekrar", "sure_s"])
        for deney, parametre, sure in satirlar:
            w.writerow([deney, parametre, TEKRAR, f"{sure:.6f}"])
    print("CSV:", CIKTI)
