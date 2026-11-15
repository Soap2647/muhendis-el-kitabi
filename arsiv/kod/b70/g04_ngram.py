# -*- coding: utf-8 -*-
"""
Bölüm 70 - n-gram dil modelleri (sayım + Laplace/add-k) ve perplexity.
Aynı token dizileri (g03) üzerinde; GPT ile adil karşılaştırma."""

import math, os
from collections import Counter, defaultdict
import numpy as np

K = os.path.dirname(os.path.abspath(__file__))
V = 2149
tr = np.load(os.path.join(K, "tok_egitim.npy")).tolist()
va = np.load(os.path.join(K, "tok_dogrulama.npy")).tolist()
te = np.load(os.path.join(K, "tok_test.npy")).tolist()


def egit(dizi, n):
    """n-gram sayımları: bağlam -> {sonraki token: sayı}."""
    say = defaultdict(Counter)
    for i in range(n - 1, len(dizi)):
        say[tuple(dizi[i - n + 1 : i])][dizi[i]] += 1
    toplam = {h: sum(c.values()) for h, c in say.items()}
    return say, toplam


def ppl(model, dizi, n, k):
    say, toplam = model
    nll, m = 0.0, 0
    for i in range(n - 1, len(dizi)):
        h = tuple(dizi[i - n + 1 : i]) if n > 1 else ()
        c = say[h][dizi[i]] if h in say else 0
        t = toplam.get(h, 0)
        p = (c + k) / (t + k * V)
        nll -= math.log(p)
        m += 1
    return math.exp(nll / m)


sonuc = {}
for n in [1, 2, 3]:
    model = egit(tr, n)
    en_iyi = None
    for k in [1.0, 0.1, 0.01, 0.001]:
        p = ppl(model, va, n, k)
        if en_iyi is None or p < en_iyi[1]:
            en_iyi = (k, p)
    k = en_iyi[0]
    pt = ppl(model, te, n, k)
    sonuc[n] = (k, en_iyi[1], pt)
    print(
        "n=%d  add-k en iyi k=%g  doğrulama ppl=%.2f  test ppl=%.2f"
        % (n, k, en_iyi[1], pt)
    )
    if n == 1:
        pl = ppl(model, va, n, 1.0)
        print("n=1 Laplace (k=1) doğrulama ppl=%.2f" % pl)
    if n == 3:
        pl = ppl(model, va, n, 1.0)
        print("n=3 Laplace (k=1) doğrulama ppl=%.2f" % pl)

import csv

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
with open(
    os.path.join(VERI, "b70_ngram.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(["model", "dogrulama_ppl", "test_ppl", "k"])
    for n in [1, 2, 3]:
        k, pv, pt = sonuc[n]
        cw.writerow(["%d-gram" % n, round(pv, 3), round(pt, 3), k])
