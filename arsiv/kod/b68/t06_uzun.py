# -*- coding: utf-8 -*-
"""Bölüm 68.3: uzun bağımlılık görevi. İlk adımdaki işaret (+1/-1)
T-1 adım sonra tahmin edilir. RNN, LSTM, GRU; 3 tohum; CPU."""
import time
import numpy as np
import torch
import torch.nn.functional as F
from ortak import Tekrarli, yaz_csv

torch.set_num_threads(4)


def gorev(n, T, rng):
    s = rng.choice([-1.0, 1.0], size=n)
    X = np.zeros((n, T, 1), np.float32)
    X[:, 0, 0] = s
    X[:, 1:, 0] = 0.1 * rng.normal(size=(n, T - 1))   # gürültü
    return torch.tensor(X), torch.tensor((s > 0).astype(np.float32))


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        p = (model(X)[:, 0] > 0).float()
    return (p == y).float().mean().item()


def calistir(tip, T, tohum, adim=2500):
    torch.manual_seed(tohum)
    rng = np.random.default_rng(100 + tohum)
    model = Tekrarli(tip, 1, h=16, cikis=1)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    for _ in range(adim):
        X, y = gorev(64, T, rng)
        model.train()
        opt.zero_grad()
        kayip = F.binary_cross_entropy_with_logits(model(X)[:, 0], y)
        kayip.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    Xt, yt = gorev(2000, T, np.random.default_rng(999 + tohum))
    return dogruluk(model, Xt, yt)


satir = []
print("%-5s %-4s %s" % ("model", "T", "test doğruluğu (3 tohum)"))
t0 = time.time()
for tip in ("rnn", "lstm", "gru"):
    for T in (10, 20, 40, 80):
        acc = [calistir(tip, T, s) for s in (1, 2, 3)]
        for s, a in zip((1, 2, 3), acc):
            satir.append((tip, T, s, round(a, 4)))
        print("%-5s %-4d %.3f +- %.3f  [%s]" % (
            tip, T, np.mean(acc), np.std(acc, ddof=1),
            " ".join("%.3f" % a for a in acc)))
print("toplam sure: %.0f s" % (time.time() - t0))
yaz_csv("b68_uzun_bagimlilik.csv",
         ["model", "T", "tohum", "dogruluk"], satir)
