# -*- coding: utf-8 -*-
"""Bölüm 68.3 ve 68.6: LSTM ileri geçişi (NumPy) ile PyTorch'un
nn.LSTM'i aynı ağırlıklarla eşleşiyor mu; kapı sırası i,f,g,o.
Ayrıca skaler bir LSTM adımının elle hesabı (Örnek 3)."""
import numpy as np
import torch
import torch.nn as nn

sig = lambda z: 1.0 / (1.0 + np.exp(-z))


def lstm_ileri(x, Wih, Whh, bih, bhh):
    """x: (T, I). Kapılar sırayla i, f, g, o (PyTorch sırası)."""
    H = Whh.shape[1]
    h, c = np.zeros(H), np.zeros(H)
    hs = []
    for xt in x:
        a = Wih @ xt + bih + Whh @ h + bhh          # (4H,)
        i = sig(a[0:H])
        f = sig(a[H:2 * H])
        g = np.tanh(a[2 * H:3 * H])
        o = sig(a[3 * H:4 * H])
        c = f * c + i * g                           # hücre "otoyolu"
        h = o * np.tanh(c)
        hs.append(h)
    return np.array(hs), h, c


# ---- 1. Eşleşme testi: I=5, H=32, T=20 (float64) ----
torch.manual_seed(0)
I, H, T = 5, 32, 20
lstm = nn.LSTM(I, H).double()
x = np.random.default_rng(1).normal(size=(T, I))
with torch.no_grad():
    out, (hn, cn) = lstm(torch.tensor(x).unsqueeze(1))
out = out[:, 0].numpy()
hs, h_son, c_son = lstm_ileri(
    x, lstm.weight_ih_l0.detach().numpy(),
    lstm.weight_hh_l0.detach().numpy(),
    lstm.bias_ih_l0.detach().numpy(),
    lstm.bias_hh_l0.detach().numpy())
print("max|h_numpy - h_torch| = %.2e" % np.abs(hs - out).max())
print("max|c_son - c_torch| = %.2e"
      % np.abs(c_son - cn[0, 0].numpy()).max())

# ---- 2. Parametre sayıları (I=5, H=32) ----
def say(m):
    return sum(p.numel() for p in m.parameters())

print("parametre sayisi (I=5, H=32):")
print("  RNN  :", say(nn.RNN(I, H)))
print("  GRU  :", say(nn.GRU(I, H)))
print("  LSTM :", say(nn.LSTM(I, H)))
print("formul LSTM 4(HI+H^2+2H) =", 4 * (H * I + H * H + 2 * H))
print("formul GRU  3(HI+H^2+2H) =", 3 * (H * I + H * H + 2 * H))

# ---- 3. Çift yönlü, 2 katmanlı LSTM şekilleri ----
bl = nn.LSTM(5, 32, num_layers=2, bidirectional=True,
             batch_first=True)
y, (hn2, cn2) = bl(torch.zeros(4, 20, 5))
print("cift yonlu cikti:", tuple(y.shape), " h_n:", tuple(hn2.shape))

# ---- 4. Skaler LSTM adımı (Örnek 3) ----
wih = np.array([[0.5], [0.9], [1.2], [0.7]])     # i, f, g, o
whh = np.array([[0.2], [-0.3], [0.4], [0.1]])
bih = np.array([0.1, 0.2, 0.0, -0.1])
bhh = np.zeros(4)
x1, h0, c0 = np.array([1.0]), 0.5, 0.4
a = wih @ x1 + bih + whh @ np.array([h0]) + bhh
i_, f_, g_, o_ = sig(a[0]), sig(a[1]), np.tanh(a[2]), sig(a[3])
c1 = f_ * c0 + i_ * g_
h1 = o_ * np.tanh(c1)
print("a = %s" % np.round(a, 4))
print("i=%.4f f=%.4f g=%.4f o=%.4f" % (i_, f_, g_, o_))
print("c1=%.4f h1=%.4f" % (c1, h1))
cell = nn.LSTMCell(1, 1).double()
with torch.no_grad():
    cell.weight_ih.copy_(torch.tensor(wih))
    cell.weight_hh.copy_(torch.tensor(whh))
    cell.bias_ih.copy_(torch.tensor(bih))
    cell.bias_hh.copy_(torch.tensor(bhh))
    d64 = torch.float64
    h_t, c_t = cell(torch.tensor([[1.0]], dtype=d64),
                    (torch.tensor([[h0]], dtype=d64),
                     torch.tensor([[c0]], dtype=d64)))
print("torch: h1=%.4f c1=%.4f" % (h_t.item(), c_t.item()))
