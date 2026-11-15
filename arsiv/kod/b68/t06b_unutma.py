# -*- coding: utf-8 -*-
"""Bölüm 68.9 ek deney: LSTM unutma kapısı sapması 1 ile başlatılır
(Jozefowicz ve ark. 2015, genel bilgi). PyTorch'ta kapı sırası i,f,g,o
olduğundan unutma kapısının sapması bias_ih_l0[H:2H]'dir. Eğitim
8000 adım; T = 40 ve 80; 3 tohum; CPU."""
import time
import numpy as np
import torch
import torch.nn.functional as F
from ortak import Tekrarli

torch.set_num_threads(4)


def gorev(n, T, rng):
    s = rng.choice([-1.0, 1.0], size=n)
    X = np.zeros((n, T, 1), np.float32)
    X[:, 0, 0] = s
    X[:, 1:, 0] = 0.1 * rng.normal(size=(n, T - 1))
    return torch.tensor(X), torch.tensor((s > 0).astype(np.float32))


def dogruluk(model, X, y):
    model.eval()
    with torch.no_grad():
        p = (model(X)[:, 0] > 0).float()
    return (p == y).float().mean().item()


def calistir(T, tohum, adim=8000, unutma_sapma=1.0):
    torch.manual_seed(tohum)
    rng = np.random.default_rng(100 + tohum)
    model = Tekrarli("lstm", 1, h=16, cikis=1)
    H = 16
    if unutma_sapma is not None:
        with torch.no_grad():
            model.rnn.bias_ih_l0[H:2 * H].fill_(unutma_sapma)
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


print("LSTM, unutma kapisi sapmasi = 1, 8000 adim")
print("%-4s %s" % ("T", "test dogrulugu (3 tohum)"))
t0 = time.time()
for T in (40, 80):
    acc = [calistir(T, s) for s in (1, 2, 3)]
    print("%-4d %.3f +- %.3f  [%s]" % (
        T, np.mean(acc), np.std(acc, ddof=1),
        " ".join("%.3f" % a for a in acc)))
print("toplam sure: %.0f s" % (time.time() - t0))
