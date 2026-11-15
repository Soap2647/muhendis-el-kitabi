# -*- coding: utf-8 -*-
"""Bölüm 66: ortak PyTorch yardımcıları (modeller, eğitim, artırma,
ölçüm)."""

import math
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

DEV = torch.device("cuda")
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def tensor(X, y):
    return (
        torch.tensor(X, dtype=torch.float32, device=DEV),
        torch.tensor(y, dtype=torch.long, device=DEV),
    )


def katman(ic, oc, bn):
    L = [nn.Conv2d(ic, oc, 3, padding=1, bias=not bn)]
    if bn:
        L.append(nn.BatchNorm2d(oc))
    return L


class Kucuk(nn.Module):
    """Küçük CNN: 32 -> 16 -> 8 -> 8 (son konvolüsyon), GAP,
    doğrusal."""

    def __init__(self, K=4):
        super().__init__()
        self.ozellik = nn.Sequential(
            nn.Sequential(
                *katman(1, 16, True), nn.ReLU(), nn.MaxPool2d(2)
            ),
            nn.Sequential(
                *katman(16, 32, True), nn.ReLU(), nn.MaxPool2d(2)
            ),
            nn.Sequential(*katman(32, 64, True), nn.ReLU()),
        )
        self.bas = nn.Linear(64, K)

    def forward(self, x):
        h = self.ozellik(x).mean(dim=(2, 3))
        return self.bas(h)


class Mlp(nn.Module):
    """Karşılaştırma: düzleştirilmiş görüntüye tam bağlı ağ."""

    def __init__(self, K=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, K),
        )

    def forward(self, x):
        return self.net(x)


class Bloku(nn.Module):
    """İki konvolüsyonlu blok. artik=True ise x + F(x) (ResNet
    fikri)."""

    def __init__(self, g, bn, artik):
        super().__init__()
        self.c1 = nn.Sequential(*katman(g, g, bn))
        self.c2 = nn.Sequential(*katman(g, g, bn))
        self.artik = artik

    def forward(self, x):
        h = self.c2(F.relu(self.c1(x)))
        if self.artik:
            h = h + x
        return F.relu(h)


class DerinAg(nn.Module):
    """Stem + blok_say * 2 konvolüsyon. Toplam konvolüsyon: 1 +
    2*blok_say."""

    def __init__(self, blok_say, g=32, bn=True, artik=True, K=4):
        super().__init__()
        self.giris = nn.Sequential(*katman(1, g, bn))
        self.bloklar = nn.ModuleList(
            [Bloku(g, bn, artik) for _ in range(blok_say)]
        )
        self.bas = nn.Linear(g, K)

    def forward(self, x):
        h = F.relu(self.giris(x))
        for b in self.bloklar:
            h = b(h)
        return self.bas(h.mean(dim=(2, 3)))


def parametre_say(m):
    return sum(p.numel() for p in m.parameters())


def artir(x):
    """GPU'da toplu artırma: ±15° döndürme, ±%10 ölçek, ±%12 kaydırma,
    yatay ayna (p=0,5), parlaklık/kontrast ve hafif gürültü."""
    B = x.shape[0]
    d = x.device
    ang = (torch.rand(B, device=d) * 2 - 1) * math.radians(15)
    sc = 1 + (torch.rand(B, device=d) * 2 - 1) * 0.10
    tx = (torch.rand(B, device=d) * 2 - 1) * 0.12
    ty = (torch.rand(B, device=d) * 2 - 1) * 0.12
    ayna = 1 - 2 * (torch.rand(B, device=d) < 0.5).float()
    c = torch.cos(ang) / sc
    s = torch.sin(ang) / sc
    theta = torch.stack(
        [
            torch.stack([c * ayna, -s, tx], 1),
            torch.stack([s * ayna, c, ty], 1),
        ],
        1,
    )
    grid = F.affine_grid(theta, list(x.shape), align_corners=False)
    x = F.grid_sample(
        x, grid, align_corners=False, padding_mode="zeros"
    )
    a = 1 + (torch.rand(B, 1, 1, 1, device=d) * 2 - 1) * 0.2
    b = (torch.rand(B, 1, 1, 1, device=d) * 2 - 1) * 0.1
    x = x * a + b + torch.randn_like(x) * 0.02
    return x.clamp(0, 1)


def egit(
    model,
    X,
    y,
    adim,
    bs=64,
    lr=1e-3,
    tohum=0,
    aug=None,
    sabit=None,
    grup_lr=None,
):
    """Adam ile adim kadar adım atar. Dönüş: adım başına kayıp
    listesi.

    sabit: BN katmanları eval modunda kalsın diye verilen modül
    listesi.
    grup_lr: (parametre_listesi, lr) — katman başına öğrenme oranı.
    """
    torch.manual_seed(tohum)
    if grup_lr is None:
        opt = torch.optim.Adam(model.parameters(), lr=lr)
    else:
        opt = torch.optim.Adam(grup_lr, lr=lr)
    n = len(y)
    kay = []
    adim_say = 0
    while adim_say < adim:
        perm = torch.randperm(n, device=DEV)
        for i in range(0, n, bs):
            if adim_say >= adim:
                break
            idx = perm[i : i + bs]
            xb = X[idx]
            if aug is not None:
                xb = aug(xb)
            model.train()
            for m in sabit or []:
                m.eval()
            loss = F.cross_entropy(model(xb), y[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            kay.append(loss.detach())
            adim_say += 1
    return torch.stack(kay).cpu().numpy()


@torch.no_grad()
def dogruluk(model, X, y, bs=512):
    model.eval()
    dogru = 0
    for i in range(0, len(y), bs):
        dogru += (
            (model(X[i : i + bs]).argmax(1) == y[i : i + bs])
            .sum()
            .item()
        )
    return dogru / len(y)


def sure_olc(f, tekrar=3):
    en = np.inf
    for _ in range(tekrar):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        f()
        torch.cuda.synchronize()
        en = min(en, time.perf_counter() - t0)
    return en
