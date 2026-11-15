# -*- coding: utf-8 -*-
"""Bölüm 68.10: kodlayıcı-kod çözücü GRU. Öğretmen zorlaması
(teacher forcing) ile eğitilen model, çıkarımda kendi tahminini
kullanınca ne olur? Tohum 11, 12, 13; CPU."""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak import iha_telemetri, HEDEF, mae, yaz_csv

n, W, H = 24000, 32, 10
ntr, nva = int(0.6 * n), int(0.8 * n)


class Seq2Seq(nn.Module):
    def __init__(self, h=32):
        super().__init__()
        self.enc = nn.GRU(1, h, batch_first=True)
        self.dec = nn.GRUCell(1, h)
        self.cik = nn.Linear(h, 1)

    def forward(self, x, hedef=None):
        _, h = self.enc(x)
        h = h[0]
        giris = x[:, -1, :]          # son gözlenen değer
        cikti = []
        for k in range(H):
            h = self.dec(giris, h)
            yk = self.cik(h)
            cikti.append(yk)
            giris = hedef[:, k:k + 1] if hedef is not None else yk
        return torch.cat(cikti, dim=1)


def pencere(x, i_lo, i_hi):
    i = np.arange(i_lo, i_hi)
    X = x[i[:, None] + np.arange(W)][:, :, None]
    Y = x[i[:, None] + W + np.arange(H)]
    return (torch.tensor(X, dtype=torch.float32),
            torch.tensor(Y, dtype=torch.float32))


def egit(tf, tohum, epoch=15):
    torch.manual_seed(tohum)
    rng = np.random.default_rng(tohum)
    Xtr, Ytr = pencere(u, 0, ntr - W - H + 1)
    m = Seq2Seq()
    opt = torch.optim.Adam(m.parameters(), lr=2e-3)
    for _ in range(epoch):
        m.train()
        sira = rng.permutation(len(Xtr))
        for b in range(0, len(sira), 128):
            j = sira[b:b + 128]
            opt.zero_grad()
            p = m(Xtr[j], Ytr[j] if tf else None)
            F.mse_loss(p, Ytr[j]).backward()
            nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step()
    return m


def olc(m, tf):
    Xte, Yte = pencere(u, nva - W, n - W - H + 1)
    m.eval()
    with torch.no_grad():
        p = m(Xte, Yte if tf else None).numpy()
    g = Yte.numpy()
    return mae(g * sd + mu, p * sd + mu)


satir = []
print("%-26s %8s %8s %8s" % ("egitim / test", "tohum11", "tohum12",
                             "tohum13"))
sonuc = {}
for tohum in (11, 12, 13):
    s = iha_telemetri(n, seed=tohum)[:, HEDEF]
    mu, sd = s[:ntr].mean(), s[:ntr].std()
    u = (s - mu) / sd
    for ad, tf, tt in [("TF egitim, serbest test", True, False),
                       ("TF egitim, TF test (iyimser)", True, True),
                       ("serbest egitim, serbest test", False,
                        False)]:
        m = egit(tf, tohum)
        a = olc(m, tt)
        sonuc.setdefault(ad, []).append(a)
        satir.append((tohum, ad, round(a, 5)))
for ad, v in sonuc.items():
    print("%-26s %8.4f %8.4f %8.4f" % (ad, *v))
yaz_csv("b68_tf.csv", ["tohum", "senaryo", "mae"], satir)
