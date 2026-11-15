# -*- coding: utf-8 -*-
"""Bolum 73 - t06: on-gorev (pretext) deneyleri.

(a) Dondurme tahmini (Gidaris 2018 fikri): yonlendirilmis (dik)
sekiller
    ve rastgele donmus sekiller. Dondurme tahmini bir isaret
    gerektirir.
(b) Kucuk maskeli goruntu modeli (MAE fikri): 4x4 yamalar, %75
maskeleme,
    piksel yeniden olusturma. Kucuk bir transformer ile.
Her iki gorev icin: dogrusal yoklama (n = 100, 500 / sinif).
"""

import csv
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak73 import AYG, Enkoder, ozellik, yoklama, yukle, tekrar
from synth73 import ornekler

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
d = yukle()
Ux, Lx, Ly, Tx, Ts = d["Ux"], d["Lx"], d["Ly"], d["Tx"], d["Ts"]
Ud = ornekler(20000, np.random.default_rng(74), dik=True)[0]
Tdik = ornekler(2000, np.random.default_rng(7401), dik=True)[0]


def alt(n):
    return np.concatenate(
        [np.arange(c * 500, c * 500 + n) for c in range(4)]
    )


@tekrar()
def dondur_egit(X_np, tohum, adim=3000, bs=64):
    torch.manual_seed(tohum)
    enc = Enkoder().to(AYG)
    bas = nn.Linear(256, 4).to(AYG)
    X = torch.as_tensor(X_np, device=AYG)
    opt = torch.optim.Adam(
        list(enc.parameters()) + list(bas.parameters()), lr=1e-3
    )
    enc.train()
    etiket = torch.arange(4, device=AYG).repeat_interleave(bs)
    for _ in range(adim):
        xb = X[torch.randint(0, len(X), (bs,), device=AYG)]
        xs = torch.cat([torch.rot90(xb, k, (2, 3)) for k in range(4)])
        loss = F.cross_entropy(bas(enc(xs)), etiket)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return enc.eval(), bas


def dondur_dogruluk(enc, bas, X_np):
    xs = torch.as_tensor(X_np, device=AYG)
    dogru = 0
    with torch.no_grad():
        for k in range(4):
            tahmin = bas(enc(torch.rot90(xs, k, (2, 3)))).argmax(1)
            dogru += (tahmin == k).sum().item()
    return dogru / (4 * len(X_np))


class MaskeliModel(nn.Module):
    """Yama (4x4x3 = 48 boyut) -> 64 belirtec; kodlayici 16 gorunur
    yama,
    kod cozucu tum dizi (maske belirteci ile); kayip maskeli
    yamalarda.
    """

    def __init__(self, d=128, maske=0.75):
        super().__init__()
        self.maske = maske
        self.gom = nn.Linear(48, d)
        self.konum = nn.Parameter(0.02 * torch.randn(1, 64, d))
        self.mb = nn.Parameter(torch.zeros(1, 1, d))
        self.kod = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d, 4, 256, batch_first=True),
            2,
            enable_nested_tensor=False,
        )
        self.coz = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d, 4, 256, batch_first=True),
            1,
            enable_nested_tensor=False,
        )
        self.cik = nn.Linear(d, 48)

    @staticmethod
    def yama(x):
        n = x.shape[0]
        return (
            x.reshape(n, 3, 8, 4, 8, 4)
            .permute(0, 2, 4, 1, 3, 5)
            .reshape(n, 64, 48)
        )

    def forward(self, x):
        P = self.yama(x)
        n = P.shape[0]
        k = int(64 * (1 - self.maske))
        sira = torch.rand(n, 64, device=x.device).argsort(1)
        gor, mas = sira[:, :k], sira[:, k:]
        h = self.gom(P) + self.konum
        z = self.kod(
            torch.gather(
                h, 1, gor.unsqueeze(-1).expand(-1, -1, h.shape[-1])
            )
        )
        full = self.mb.expand(n, 64, h.shape[-1]).scatter(
            1, gor.unsqueeze(-1).expand(-1, -1, z.shape[-1]), z
        )
        rec = self.cik(self.coz(full + self.konum))
        m = torch.ones(n, 64, device=x.device).scatter(1, gor, 0.0)
        return (((rec - P) ** 2).mean(-1) * m).sum() / m.sum()

    def ozellik(self, x):
        P = self.yama(x)
        return self.kod(self.gom(P) + self.konum).mean(1)


@tekrar()
def maske_egit(X_np, tohum, adim=3000, bs=256):
    torch.manual_seed(tohum)
    m = MaskeliModel().to(AYG)
    X = torch.as_tensor(X_np, device=AYG)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    m.train()
    for _ in range(adim):
        xb = X[torch.randint(0, len(X), (bs,), device=AYG)]
        loss = m(xb)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return m.eval()


def maske_ozellik(m, X_np):
    out = []
    with torch.no_grad():
        for i in range(0, len(X_np), 500):
            xb = torch.as_tensor(X_np[i : i + 500], device=AYG)
            out.append(m.ozellik(xb).cpu().numpy())
    return np.concatenate(out)


satirlar = []
enc, bas = dondur_egit(Ud, 0)
satirlar.append(
    (
        "dondurme_dik",
        "rotasyon_dogruluk",
        dondur_dogruluk(enc, bas, Tdik),
    )
)
Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
satirlar.append(
    (
        "dondurme_dik",
        "yoklama100",
        yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
    )
)
satirlar.append(
    (
        "dondurme_dik",
        "yoklama500",
        yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
    )
)
for r in satirlar[-3:]:
    print("%-18s %-18s %.4f" % r, flush=True)

enc, bas = dondur_egit(Ux, 0)
satirlar.append(
    (
        "dondurme_rastgele",
        "rotasyon_dogruluk",
        dondur_dogruluk(enc, bas, Tx),
    )
)
Fl, Ft = ozellik(enc, Lx), ozellik(enc, Tx)
satirlar.append(
    (
        "dondurme_rastgele",
        "yoklama100",
        yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
    )
)
satirlar.append(
    (
        "dondurme_rastgele",
        "yoklama500",
        yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
    )
)
for r in satirlar[-3:]:
    print("%-18s %-18s %.4f" % r, flush=True)

for ad, egit_fn in (
    ("maske", lambda: maske_egit(Ux, 0)),
    ("maske_rastgele", lambda: MaskeliModel().to(AYG).eval()),
):
    m = egit_fn()
    Fl, Ft = maske_ozellik(m, Lx), maske_ozellik(m, Tx)
    satirlar.append(
        (
            ad,
            "yoklama100",
            yoklama(Fl[alt(100)], Ly[alt(100)], Ft, Ts),
        )
    )
    satirlar.append(
        (
            ad,
            "yoklama500",
            yoklama(Fl[alt(500)], Ly[alt(500)], Ft, Ts),
        )
    )
    for r in satirlar[-2:]:
        print("%-18s %-18s %.4f" % r, flush=True)

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b73_on_gorev.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["gorev", "olcut", "deger"])
    for s in satirlar:
        w.writerow([s[0], s[1], "%.4f" % s[2]])
