# -*- coding: utf-8 -*-
"""Bölüm 68 ortak araçları: sentetik telemetri, pencereleme, baz
modeller ve küçük bir eğitim döngüsü. Tüm işler CPU'da yapılır."""
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(4)
VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
DT = 0.1        # İHA telemetrisi 10 Hz
PERIYOT = 600   # bir devriye turu 60 s = 600 örnek
HEDEF = 3       # tahmin edilen kanal: motor akımı


def iha_telemetri(n=24000, seed=11):
    """Sentetik İHA telemetrisi, anomalisiz.
    Kanallar: irtifa (m), hız (m/s), yuvarlanma (derece), akım (A)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    faz = 2 * np.pi * t / PERIYOT
    e = rng.normal(0.0, 1.0, n)
    ruzgar = np.zeros(n)
    for i in range(1, n):                 # AR(1) türbülans
        ruzgar[i] = 0.97 * ruzgar[i - 1] + 0.25 * e[i]
    irtifa = 100 + 0.0015 * t + 6 * np.sin(faz) + 0.6 * ruzgar
    hiz = 15 + 2.5 * np.sin(faz + 0.4) + 0.4 * rng.normal(size=n)
    yuv = 22 * np.sin(faz) + 1.5 * ruzgar + 0.5 * rng.normal(size=n)
    akim = (6 + 0.35 * hiz + 0.05 * np.abs(yuv)
            + 0.15 * rng.normal(size=n))
    return np.stack([irtifa, hiz, yuv, akim], axis=1)


def ariza_ekle(seri, bas, son, seed=5):
    """[bas, son) aralığına arıza enjekte eder, etiket döner.
    (1) 5 tekil akım sıçraması (+3 A).
    (2) 400 örnek boyunca doğrusal artan kayma (en fazla +1,5 A),
        ardından 300 örnek sabit kalır."""
    rng = np.random.default_rng(seed)
    x = seri.copy()
    etiket = np.zeros(len(x), dtype=int)
    konum = rng.choice(np.arange(bas, son - 10), size=5,
                       replace=False)
    for k in konum:
        x[k, HEDEF] += 3.0
        etiket[k] = 1
    d0 = bas + (son - bas) // 2
    seg = np.concatenate([np.linspace(0.0, 1.5, 400),
                          np.full(300, 1.5)])
    m = min(len(seg), len(x) - d0)
    x[d0:d0 + m, HEDEF] += seg[:m]
    etiket[d0:d0 + m] = 1
    return x, etiket


def olcek(Z, ntr):
    """Ortalama ve sapmayı YALNIZCA eğitim satırlarından öğrenir."""
    mu = Z[:ntr].mean(axis=0)
    sd = Z[:ntr].std(axis=0) + 1e-8
    return (Z - mu) / sd, mu, sd


def pencere(Z, W, H=1):
    """X[i] = Z[i:i+W] (tüm kanallar); Y[i] = hedef kanalın
    Z[i+W : i+W+H] değerleri."""
    m = len(Z) - W - H + 1
    X = Z[np.arange(W)[None, :] + np.arange(m)[:, None]]
    Y = Z[np.arange(H)[None, :] + np.arange(m)[:, None] + W, HEDEF]
    return X.astype(np.float32), Y.astype(np.float32)


def veri_bol(Z, W, H, ntr, nva):
    """Pencereleri HEDEFİN konumuna göre üçe böler: eğitim, doğrulama,
    test. Girdi pencereleri bir önceki kümeden taşabilir; bu sızıntı
    değildir, çünkü yalnızca geçmiş değerler kullanılır."""
    X, Y = pencere(Z, W, H)
    hb = np.arange(len(X)) + W
    tr = hb < ntr
    va = (hb >= ntr) & (hb < nva)
    te = hb >= nva
    return (X[tr], Y[tr]), (X[va], Y[va]), (X[te], Y[te])


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def rmse(a, b):
    d = np.asarray(a) - np.asarray(b)
    return float(np.sqrt(np.mean(d ** 2)))


# ---------- baz modeller (ham hedef dizisi s) ----------
def naif_tahmin(s, idx):
    return s[idx - 1]                        # son değer


def mevsimsel_naif(s, idx, P=PERIYOT):
    return s[idx - P]                        # bir periyot önce


def hareketli_ort(s, idx, k=10):
    return np.array([s[t - k:t].mean() for t in idx])


def ar_egit(s, ntr, p):
    """AR(p): s_t = c + a1 s_{t-1} + ... + ap s_{t-p}.
    Katsayılar en küçük kareler ile bulunur."""
    rows = np.arange(p, ntr)
    A = np.column_stack([np.ones(len(rows))]
                        + [s[rows - j] for j in range(1, p + 1)])
    kat, *_ = np.linalg.lstsq(A, s[rows], rcond=None)
    return kat


def ar_1adim(s, kat, idx):
    p = len(kat) - 1
    A = np.column_stack([np.ones(len(idx))]
                        + [s[idx - j] for j in range(1, p + 1)])
    return A @ kat


def ar_sec(s, ntr, nva, dereceler=(1, 2, 5, 10, 20, 40)):
    """Derece seçimi doğrulama MAE'siyle yapılır; test'e bakılmaz."""
    idx_va = np.arange(ntr, nva)
    en = None
    for p in dereceler:
        kat = ar_egit(s, ntr, p)
        h = mae(s[idx_va], ar_1adim(s, kat, idx_va))
        if en is None or h < en[0]:
            en = (h, p, kat)
    return en[1], en[2]


# ---------- sinir ağları ----------
class Tekrarli(nn.Module):
    """RNN, LSTM ya da GRU üzerine doğrusal baş; son gizli durum."""

    def __init__(self, tip, c, h=32, cikis=1):
        super().__init__()
        sinif = {"rnn": nn.RNN, "lstm": nn.LSTM, "gru": nn.GRU}[tip]
        self.rnn = sinif(c, h, batch_first=True)
        self.bas = nn.Linear(h, cikis)

    def forward(self, x):
        cikti, _ = self.rnn(x)
        return self.bas(cikti[:, -1])


class TCNBlok(nn.Module):
    """İki nedensel genişletilmiş konvolüsyon + artık bağlantı."""

    def __init__(self, cgir, ccik, k, d):
        super().__init__()
        self.pad = (k - 1) * d
        self.c1 = nn.Conv1d(cgir, ccik, k, dilation=d)
        self.c2 = nn.Conv1d(ccik, ccik, k, dilation=d)
        self.yan = (nn.Conv1d(cgir, ccik, 1)
                    if cgir != ccik else nn.Identity())

    def forward(self, x):
        h = F.relu(self.c1(F.pad(x, (self.pad, 0))))
        h = self.c2(F.pad(h, (self.pad, 0)))
        return F.relu(h + self.yan(x))


class TCN(nn.Module):
    """Girdi (B, L, C); çıktı son zaman adımından."""

    def __init__(self, c, kanal=32, k=3, dil=(1, 2, 4, 8), cikis=1):
        super().__init__()
        bl, g = [], c
        for d in dil:
            bl.append(TCNBlok(g, kanal, k, d))
            g = kanal
        self.bloklar = nn.Sequential(*bl)
        self.bas = nn.Linear(kanal, cikis)
        self.k, self.dil = k, dil

    def alici_alan(self):
        return 1 + sum(2 * (self.k - 1) * d for d in self.dil)

    def forward(self, x):
        h = self.bloklar(x.transpose(1, 2))
        return self.bas(h[:, :, -1])


def egit(model, Xtr, ytr, Xva, yva, epoch=40, lr=2e-3, bs=128,
         sabir=6, seed=0):
    """Adam + MSE. Doğrulama kaybı en düşük olan ağırlıklar geri
    yüklenir (erken durdurma). Gradyan normu 1.0'da kırpılır."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    Xt, yt = torch.tensor(Xtr), torch.tensor(ytr)
    Xv, yv = torch.tensor(Xva), torch.tensor(yva)
    en = (np.inf, None, -1)
    bekle = 0
    for ep in range(epoch):
        model.train()
        sira = rng.permutation(len(Xt))
        for b in range(0, len(sira), bs):
            j = sira[b:b + bs]
            opt.zero_grad()
            kayip = F.mse_loss(model(Xt[j]), yt[j])
            kayip.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        model.eval()
        with torch.no_grad():
            va = F.mse_loss(model(Xv), yv).item()
        if va < en[0] - 1e-6:
            en = (va, {k: v.clone()
                       for k, v in model.state_dict().items()}, ep)
            bekle = 0
        else:
            bekle += 1
            if bekle >= sabir:
                break
    model.load_state_dict(en[1])
    return en[0], en[2]


def tahmin(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(X)).numpy()


def yaz_csv(yol, basliklar, satirlar):
    os.makedirs(VERI, exist_ok=True)
    with open(os.path.join(VERI, yol), "w", encoding="utf-8") as f:
        f.write(",".join(basliklar) + "\n")
        for r in satirlar:
            f.write(",".join(str(x) for x in r) + "\n")
