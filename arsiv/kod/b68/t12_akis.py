# -*- coding: utf-8 -*-
"""Bölüm 68.11: akış (streaming) çıkarımı. (1) Durumlu GRU ve TCN
tamponu toplu (batch) sonuçla eşleşiyor mu? (2) Adım başına gecikme
ve bellek; ölçüm bu makinede, CPU'da yapılır."""
import time
import numpy as np
import torch
import torch.nn as nn
from ortak import TCN

torch.set_num_threads(4)
torch.manual_seed(0)
T, C = 300, 4
x = torch.randn(1, T, C)

# (1a) GRU: toplu ve adım adım (gizli durum taşınarak)
gru = nn.GRU(C, 16, batch_first=True).eval()
with torch.no_grad():
    toplu, _ = gru(x)
    h = torch.zeros(1, 1, 16)
    adim = []
    for t in range(T):
        y, h = gru(x[:, t:t + 1], h)
        adim.append(y[:, 0])
    adim = torch.stack(adim, dim=1)
print("GRU  toplu ve adim farki = %.2e" % (toplu - adim).abs().max())

# (1b) TCN: son RF örneklik kaydırmalı tampon; baş kısmı sıfır
tcn = TCN(C, 32, 3, (1, 2, 4, 8)).eval()
RF = tcn.alici_alan()
with torch.no_grad():
    tam = tcn.bloklar(x.transpose(1, 2)).transpose(1, 2)
    tampon = torch.zeros(1, RF, C)
    fark = []
    for t in range(T):
        tampon = torch.cat([tampon[:, 1:], x[:, t:t + 1]], dim=1)
        y = tcn.bloklar(tampon.transpose(1, 2))[:, :, -1]
        fark.append((y - tam[:, t]).abs().max().item())
fark = torch.tensor(fark)
print("TCN  t<%d en buyuk fark   = %.2e"
      % (RF - 1, fark[:RF - 1].max()))
print("TCN  t>=%d en buyuk fark  = %.2e  (RF=%d)"
      % (RF - 1, fark[RF - 1:].max(), RF))

# (2) Gecikme: adım başına ortanca süre (mikro saniye)
def olc(fn, adim_say=2000, tekrar=5):
    sonuc = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        for _ in range(adim_say):
            fn()
        sonuc.append((time.perf_counter() - t0) / adim_say)
    return np.median(sonuc) * 1e6

xt = torch.randn(1, 1, C)
hh = torch.zeros(1, 1, 16)
gru32 = nn.GRU(C, 32, batch_first=True).eval()
hh32 = torch.zeros(1, 1, 32)
lstm = nn.LSTM(C, 32, batch_first=True).eval()
lh = (torch.zeros(1, 1, 32), torch.zeros(1, 1, 32))
buf = torch.zeros(1, RF, C)
with torch.no_grad():
    g16 = olc(lambda: gru(xt, hh))
    g32 = olc(lambda: gru32(xt, hh32))
    l32 = olc(lambda: lstm(xt, lh))
    t_adim = olc(lambda: tcn.bloklar(
        torch.cat([buf[:, 1:], xt], dim=1).transpose(1, 2)), 500)
print("adim basi sure (us, medyan):")
print("  GRU  H=16 : %7.1f" % g16)
print("  GRU  H=32 : %7.1f" % g32)
print("  LSTM H=32 : %7.1f" % l32)
print("  TCN  tampon(RF=%d): %7.1f" % (RF, t_adim))

# (3) Bellek: parametre ve float32/int8 boyutu
def say(m):
    return sum(q.numel() for q in m.parameters())
gru16 = nn.GRU(C, 16)
print("GRU(I=4,H=16) parametre = %d; float32=%d B, int8~%d B"
      % (say(gru16), 4 * say(gru16), say(gru16)))
print("TCN tampon bellegi (RF x C float32) = %d B" % (RF * C * 4))
