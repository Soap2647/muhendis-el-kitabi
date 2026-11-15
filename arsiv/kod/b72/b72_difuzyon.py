# -*- coding: utf-8 -*-
"""Gurultu giderme difuzyon modeli icin ortak parcalar: takvim,
gurultu tahmincisi aglari, egitim ve iki ornekleme yontemi
(DDPM ve DDIM). t = 0 temiz veri, t = T tam gurultu."""
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def zamanlama(T, tur="lineer"):
    """beta_t, alfa_t, abar_t dizileri; indeks t = 0..T.
    beta[0] kullanilmaz (x_0 icin yok)."""
    if tur == "lineer":
        b = np.linspace(1e-4, 0.2, T)
    else:
        adim = np.arange(T + 1) / T
        f = np.cos((adim + 0.008) / 1.008 * np.pi / 2) ** 2
        ab = f / f[0]
        b = np.minimum(1 - ab[1:] / ab[:-1], 0.999)
    beta = np.concatenate([[0.0], b])
    alfa = 1.0 - beta
    alfa[0] = 1.0
    abar = np.cumprod(alfa)
    return beta, alfa, abar


def sinus_gomme(t, dim):
    """Adim numarasi icin sinuzoidal zaman gomulmesi."""
    yari = dim // 2
    f = torch.exp(-math.log(10000.0) * torch.arange(yari) / yari)
    a = t.float()[:, None] * f[None]
    return torch.cat([torch.sin(a), torch.cos(a)], 1)


class MLP2D(nn.Module):
    """2B veri icin gurultu tahmincisi. nc>0 ise sinif kosulu
    (nc indeksi 'kosulsuz' anahtarıdır)."""

    def __init__(self, tdim=32, nc=0, h=256):
        super().__init__()
        self.tdim = tdim
        self.nc = nc
        self.cemb = nn.Embedding(nc + 1, tdim) if nc > 0 else None
        giris = 2 + tdim + (tdim if nc > 0 else 0)
        self.net = nn.Sequential(
            nn.Linear(giris, h), nn.SiLU(),
            nn.Linear(h, h), nn.SiLU(),
            nn.Linear(h, h), nn.SiLU(),
            nn.Linear(h, 2))

    def forward(self, x, t, c=None):
        parca = [x, sinus_gomme(t, self.tdim)]
        if self.cemb is not None:
            parca.append(self.cemb(c))
        return self.net(torch.cat(parca, 1))


class Blok(nn.Module):
    def __init__(self, cin, cout, tch):
        super().__init__()
        self.c1 = nn.Conv2d(cin, cout, 3, padding=1)
        self.n1 = nn.GroupNorm(8, cout)
        self.t = nn.Linear(tch, cout)
        self.c2 = nn.Conv2d(cout, cout, 3, padding=1)
        self.n2 = nn.GroupNorm(8, cout)

    def forward(self, x, te):
        h = F.silu(self.n1(self.c1(x)))
        h = h + self.t(te)[:, :, None, None]
        return F.silu(self.n2(self.c2(h)))


class UNet8(nn.Module):
    """8x8 goruntuler icin kucuk U-Net: 8x8 -> 4x4 -> 8x8, atlama
    baglantisi, zaman gomulmesi her blokta eklenir."""

    def __init__(self, k=32, tdim=64):
        super().__init__()
        self.tdim = tdim
        self.tm = nn.Sequential(nn.Linear(tdim, 128), nn.SiLU(),
                                nn.Linear(128, 128))
        self.giris = nn.Conv2d(1, k, 3, padding=1)
        self.b1 = Blok(k, k, 128)
        self.asagi = nn.Conv2d(k, 2 * k, 4, 2, 1)
        self.b2 = Blok(2 * k, 2 * k, 128)
        self.yukari = nn.ConvTranspose2d(2 * k, k, 4, 2, 1)
        self.b3 = Blok(2 * k, k, 128)
        self.cikis = nn.Conv2d(k, 1, 3, padding=1)

    def forward(self, x, t, c=None):
        te = self.tm(sinus_gomme(t, self.tdim))
        h1 = self.b1(self.giris(x), te)
        h2 = self.b2(self.asagi(h1), te)
        u = self.yukari(h2)
        h3 = self.b3(torch.cat([u, h1], 1), te)
        return self.cikis(h3)


def egit(model, veri, T, abar, iters, batch=512, lr=1e-3,
         etiket=None, p_dusur=0.1, seed=0, nc=0):
    """Basitlestirilmis kayip: ||eps - eps_teta(x_t, t)||^2.
    etiket verilirse kosullu egitim; kosulsuz anahtar nc'dir."""
    torch.manual_seed(seed)
    ab = torch.tensor(abar, dtype=torch.float32)
    X = torch.as_tensor(veri, dtype=torch.float32)
    Y = None if etiket is None else torch.as_tensor(etiket)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    n = len(X)
    kayip_gecmisi = []
    for it in range(iters):
        i = torch.randint(0, n, (batch,))
        x0 = X[i]
        t = torch.randint(1, T + 1, (batch,))
        eps = torch.randn_like(x0)
        a = ab[t].view(-1, *([1] * (x0.dim() - 1)))
        xt = a.sqrt() * x0 + (1 - a).sqrt() * eps
        c = None
        if Y is not None:
            c = Y[i].clone()
            c[torch.rand(batch) < p_dusur] = nc
        tahmin = model(xt, t, c)
        kayip = F.mse_loss(tahmin, eps)
        opt.zero_grad()
        kayip.backward()
        opt.step()
        kayip_gecmisi.append(kayip.item())
    return kayip_gecmisi


@torch.no_grad()
def eps_tahmin(model, x, t, c=None, w=0.0, nc=None):
    """Sinifsiz yonlendirme: w>0 ise (1+w) e(x,c) - w e(x,null)."""
    if c is None or w == 0.0:
        return model(x, t, c)
    ec = model(x, t, c)
    eu = model(x, t, torch.full_like(c, nc))
    return (1 + w) * ec - w * eu


@torch.no_grad()
def ornekle_ddpm(model, n, sekil, T, beta, abar, c=None, w=0.0,
                 nc=None, clip=None, anlik=None, seed=0):
    """Ancestral DDPM ornekleme: T adim, her adimda gurultu.
    clip verilirse kirpma x_0 tahmininde yapilir
    (standart uygulama)."""
    torch.manual_seed(seed)
    x = torch.randn(n, *sekil)
    for t in range(T, 0, -1):
        tt = torch.full((n,), t, dtype=torch.long)
        eps = eps_tahmin(model, x, tt, c, w, nc)
        x0 = (x - math.sqrt(1 - abar[t]) * eps) / math.sqrt(abar[t])
        if clip is not None:
            x0 = x0.clamp(-clip, clip)
        ap = abar[t - 1]
        c0 = math.sqrt(ap) * beta[t] / (1 - abar[t])
        ct = math.sqrt(1 - beta[t]) * (1 - ap) / (1 - abar[t])
        x = c0 * x0 + ct * x
        if t > 1:
            var = beta[t] * (1 - ap) / (1 - abar[t])
            x = x + math.sqrt(var) * torch.randn_like(x)
        if anlik is not None:
            anlik(t, x)
    return x


@torch.no_grad()
def ornekle_ddim(model, n, sekil, T, abar, S, c=None, w=0.0,
                 nc=None, clip=None, seed=0):
    """DDIM (eta = 0): deterministik; T adimin S'lik alt kumesinde."""
    torch.manual_seed(seed)
    taus = [0] + list(np.round(np.linspace(0, T, S + 1)[1:])
                      .astype(int))
    x = torch.randn(n, *sekil)
    for i in range(S, 0, -1):
        t, s = taus[i], taus[i - 1]
        tt = torch.full((n,), t, dtype=torch.long)
        eps = eps_tahmin(model, x, tt, c, w, nc)
        x0 = (x - math.sqrt(1 - abar[t]) * eps) / math.sqrt(abar[t])
        if clip is not None:
            x0 = x0.clamp(-clip, clip)
        x = math.sqrt(abar[s]) * x0 + math.sqrt(1 - abar[s]) * eps
    return x
