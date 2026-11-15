# -*- coding: utf-8 -*-
"""Bölüm 63.15 köprü: aynı MLP'nin PyTorch gradyanı (CPU, float64)."""
import os
import numpy as np
import torch
from sinir import VERI, ReLU, SoftmaxCE, mlp, ileri_geri, veri_yukle

P = np.load(os.path.join(VERI, "b63_model.npz"))
(Xt, Yt, yt), _, _ = veri_yukle()
idx = np.arange(32)
X, Y = Xt[idx], Yt[idx]

# NumPy tarafı: aynı ağırlıklarla
rng = np.random.default_rng(0)
ag = mlp([64, 128, 64, 10], ReLU, rng, "he")
for k, (w, b) in zip(ag.parametreler(), [("W1", "b1"), ("W2", "b2"),
                                          ("W3", "b3")]):
    k.W, k.b = P[w].copy(), P[b].copy()
L_np = ileri_geri(ag, SoftmaxCE(), X, Y)
g_np = [k.dW for k in ag.parametreler()]

# PyTorch tarafı
net = torch.nn.Sequential(
    torch.nn.Linear(64, 128), torch.nn.ReLU(),
    torch.nn.Linear(128, 64), torch.nn.ReLU(),
    torch.nn.Linear(64, 10)).double()
lin = [net[0], net[2], net[4]]
for l, w, b in zip(lin, ["W1", "W2", "W3"], ["b1", "b2", "b3"]):
    with torch.no_grad():
        l.weight.copy_(torch.tensor(P[w].T))
        l.bias.copy_(torch.tensor(P[b]))
x_t = torch.tensor(X)
y_t = torch.tensor(Yt[idx]).argmax(1)
L_t = torch.nn.functional.cross_entropy(net(x_t), y_t)
L_t.backward()

print("Kayıp  NumPy = %.12f" % L_np)
print("Kayıp  Torch = %.12f" % L_t.item())
for l, g in zip(lin, g_np):
    fark = np.max(np.abs(l.weight.grad.numpy().T - g)) / \
        max(np.max(np.abs(g)), 1e-12)
    print("Ağırlık gradyanı göreli fark = %.2e" % fark)
