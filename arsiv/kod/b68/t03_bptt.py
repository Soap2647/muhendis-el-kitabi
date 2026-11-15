# -*- coding: utf-8 -*-
"""Bölüm 68.6: skaler RNN'in elle izi, NumPy ile BPTT ve gradient
check."""
import numpy as np

# ---- 1. Skaler RNN: h_t = tanh(wx*x_t + wh*h_{t-1} + b) ----
wx, wh, b = 0.5, 0.8, 0.0
x = [1.0, 0.0, -1.0]
h = [0.0]                                  # h_0 = 0
for t, xt in enumerate(x, 1):
    h.append(np.tanh(wx * xt + wh * h[-1] + b))
    print("h_%d = tanh(%.1f*%.1f + %.1f*%.4f) = %.4f"
          % (t, wx, xt, wh, h[t - 1], h[t]))

# ---- 2. Skaler BPTT: L = 0.5*(h_3 - d)^2, d = 0,5 ----
d = 0.5
dL_dh3 = h[3] - d
g_wh = 0.0
g_wx = 0.0
dh_next = dL_dh3                           # dL/dh_t
for t in (3, 2, 1):
    da = dh_next * (1 - h[t] ** 2)         # tanh'(a_t) = 1 - h_t^2
    g_wh += da * h[t - 1]
    g_wx += da * x[t - 1]
    dh_next = da * wh                      # dL/dh_{t-1}
print("dL/dwh = %.6f   dL/dwx = %.6f" % (g_wh, g_wx))

def kayip(wx_, wh_):
    hh = 0.0
    for xt in x:
        hh = np.tanh(wx_ * xt + wh_ * hh + b)
    return 0.5 * (hh - d) ** 2

eps = 1e-6
sayi_wh = (kayip(wx, wh + eps) - kayip(wx, wh - eps)) / (2 * eps)
sayi_wx = (kayip(wx + eps, wh) - kayip(wx - eps, wh)) / (2 * eps)
print("sayisal dL/dwh = %.6f   dL/dwx = %.6f" % (sayi_wh, sayi_wx))
print("bagil hata wh: %.2e  wx: %.2e" % (
    abs(g_wh - sayi_wh) / max(abs(g_wh), 1e-12),
    abs(g_wx - sayi_wx) / max(abs(g_wx), 1e-12)))

# ---- 3. Vektör RNN, her adımda kayıp, gradient check ----
def ileri(p, X):
    H = p["Wh"].shape[0]
    hs = np.zeros((len(X) + 1, H))
    for t in range(len(X)):
        hs[t + 1] = np.tanh(p["Wx"] @ X[t] + p["Wh"] @ hs[t] + p["b"])
    Y = hs[1:] @ p["Wy"].T + p["by"]
    return hs, Y

def kayip_v(p, X, D):
    _, Y = ileri(p, X)
    return 0.5 * np.sum((Y - D) ** 2)

def geri(p, X, D):
    hs, Y = ileri(p, X)
    T, H = len(X), p["Wh"].shape[0]
    dY = Y - D                             # dL/dy_t
    g = {k: np.zeros_like(v) for k, v in p.items()}
    g["Wy"] = dY.T @ hs[1:]
    g["by"] = dY.sum(axis=0)
    dh_next = np.zeros(H)                  # gelecekten gelen gradyan
    for t in reversed(range(T)):
        dh = dY[t] @ p["Wy"] + dh_next     # ileri ve geri katkı
        da = dh * (1 - hs[t + 1] ** 2)
        g["Wx"] += np.outer(da, X[t])
        g["Wh"] += np.outer(da, hs[t])
        g["b"] += da
        dh_next = p["Wh"].T @ da
    return g

rng = np.random.default_rng(0)
H, I, O, T = 3, 2, 1, 5
p = {"Wx": rng.normal(0, 0.5, (H, I)),
     "Wh": rng.normal(0, 0.5, (H, H)),
     "b": np.zeros(H),
     "Wy": rng.normal(0, 0.5, (O, H)),
     "by": np.zeros(O)}
X = rng.normal(size=(T, I))
D = rng.normal(size=(T, O))
g = geri(p, X, D)
en_kotu = 0.0
for ad in p:
    e = np.zeros_like(p[ad])
    dene = []
    for idx in np.ndindex(p[ad].shape):
        orj = p[ad][idx]
        p[ad][idx] = orj + 1e-6; lp = kayip_v(p, X, D)
        p[ad][idx] = orj - 1e-6; lm = kayip_v(p, X, D)
        p[ad][idx] = orj
        dene.append((lp - lm) / 2e-6)
    e = np.array(dene).reshape(p[ad].shape)
    pay = np.abs(g[ad] - e)
    bagil = pay / np.maximum(np.abs(g[ad]) + np.abs(e), 1e-12)
    en_kotu = max(en_kotu, bagil.max())
    print("%-3s  en büyük bağıl hata = %.2e" % (ad, bagil.max()))
print("GENEL en büyük bağıl hata = %.2e" % en_kotu)
