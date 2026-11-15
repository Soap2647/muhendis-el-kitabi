# -*- coding: utf-8 -*-
"""Bölüm 68.7: TCN'in alıcı alanı ve nedenselliği ölçülüyor."""
import torch
import torch.nn as nn
from ortak import TCN

torch.manual_seed(0)
torch.set_num_threads(4)
L = 160
for dil in [(1, 2, 4, 8), (1, 2, 4, 8, 16)]:
    net = TCN(1, kanal=8, k=3, dil=dil)
    RF = net.alici_alan()
    x = torch.randn(1, L, 1, requires_grad=True)
    y = net(x)[0, 0]                       # son adımın çıktısı
    g, = torch.autograd.grad(y, x)
    etki = g[0, :, 0].abs()
    ilk = (etki > 0).nonzero().min().item()  # en eski etkili girdi
    gecikme = L - 1 - ilk                  # en uzak etkili gecikme
    print("dilation=%s" % (dil,))
    print("  formul alici alan = 1 + 2(k-1) sum(d) = %d" % RF)
    print("  olculen en uzak etkili gecikme   = %d (RF-1 = %d)"
          % (gecikme, RF - 1))
    print("  parametre sayisi (kanal=8)       = %d"
          % sum(p.numel() for p in net.parameters()))

# Nedensellik: gelecekteki girdiyi değiştirmek geçmiş çıktıyı
# değiştirmemeli. Tüm zaman adımlarındaki gizli çıktıyı kullanırız.
net = TCN(1, kanal=8, k=3, dil=(1, 2, 4, 8)).eval()
x = torch.randn(1, L, 1)
x2 = x.clone()
x2[0, 60:, 0] += 5.0                       # t >= 60 değişti
with torch.no_grad():
    h1 = net.bloklar(x.transpose(1, 2))
    h2 = net.bloklar(x2.transpose(1, 2))
fark = (h1 - h2).abs().amax(dim=(0, 1))    # her adım için
print("nedensellik: t<60 için en büyük fark = %.2e"
      % fark[:60].max().item())
print("t>=60 için en büyük fark           = %.2e"
      % fark[60:].max().item())
print("LSTM (H=32, I=4) param = %d, TCN (kanal=32, C=4) param = %d"
      % (sum(p.numel() for p in nn.LSTM(4, 32).parameters()),
         sum(p.numel() for p in TCN(4, 32).parameters())))
