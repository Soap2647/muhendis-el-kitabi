# -*- coding: utf-8 -*-
# b67_07_unet.py: sifirdan U-Net (anlamsal segmentasyon), atlama
# baglantisi ablasyonu, CE + Dice kaybi. 4 sinif: arka plan, daire,
# kare, ucgen. Test: tohum 777 (500 sahne), egitim: tohum 0.
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy import ndimage
from b67_veri import veri_seti

C = 4
AYGIT = "cuda"
KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def blok(giris, cikis):
    """Iki 3x3 konvolusyon + BatchNorm + ReLU."""
    return nn.Sequential(
        nn.Conv2d(giris, cikis, 3, 1, 1, bias=False),
        nn.BatchNorm2d(cikis), nn.ReLU(inplace=True),
        nn.Conv2d(cikis, cikis, 3, 1, 1, bias=False),
        nn.BatchNorm2d(cikis), nn.ReLU(inplace=True))


class UNet(nn.Module):
    """Kodlayici 96 -> 48 -> 24 -> 12; cozucu 12 -> 24 -> 48 -> 96.
    atlama=True: kodlayici ozellikleri cozucuye birlestirilir."""

    def __init__(self, atlama=True):
        super().__init__()
        self.atlama = atlama
        self.e1 = blok(1, 16)
        self.e2 = blok(16, 32)
        self.e3 = blok(32, 64)
        self.orta = blok(64, 128)
        self.havuz = nn.MaxPool2d(2)
        self.u3 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.d3 = blok(128 if atlama else 64, 64)
        self.u2 = nn.ConvTranspose2d(64, 32, 2, 2)
        self.d2 = blok(64 if atlama else 32, 32)
        self.u1 = nn.ConvTranspose2d(32, 16, 2, 2)
        self.d1 = blok(32 if atlama else 16, 16)
        self.son = nn.Conv2d(16, C, 1)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.havuz(e1))
        e3 = self.e3(self.havuz(e2))
        b = self.orta(self.havuz(e3))
        d = self.u3(b)
        d = self.d3(torch.cat([d, e3], 1) if self.atlama else d)
        d = self.u2(d)
        d = self.d2(torch.cat([d, e2], 1) if self.atlama else d)
        d = self.u1(d)
        d = self.d1(torch.cat([d, e1], 1) if self.atlama else d)
        return self.son(d)


def kayip(logit, y):
    """Piksel basina CE + arka plan haric yumusak Dice."""
    ce = F.cross_entropy(logit, y)
    p = torch.softmax(logit, 1)
    oh = F.one_hot(y, C).permute(0, 3, 1, 2).float()
    kesisim = (p * oh).sum((0, 2, 3))
    toplam = p.sum((0, 2, 3)) + oh.sum((0, 2, 3))
    dice = (2 * kesisim + 1) / (toplam + 1)
    return ce + (1 - dice[1:].mean())


def egit(seed, X, Y, atlama, epoch=30, bs=32):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = UNet(atlama).to(AYGIT)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3,
                            weight_decay=1e-4)
    adim = int(np.ceil(len(X) / bs))
    sch = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=2e-3, total_steps=epoch * adim)
    Xt = torch.tensor(X, device=AYGIT)
    Yt = torch.tensor(Y, device=AYGIT)
    model.train()
    for _ in range(epoch):
        perm = torch.randperm(len(X), generator=g)
        for i in range(0, len(X), bs):
            idx = perm[i:i + bs].to(AYGIT)
            L = kayip(model(Xt[idx]), Yt[idx])
            opt.zero_grad()
            L.backward()
            opt.step()
            sch.step()
    return model.eval()


@torch.no_grad()
def tahmin(model, X):
    out = []
    for i in range(0, len(X), 100):
        xb = torch.tensor(X[i:i + 100], device=AYGIT)
        out.append(model(xb).argmax(1).cpu().numpy())
    return np.concatenate(out)


def sinir_bandi(y, genislik=2):
    """Gercek maskede sinir piksellerinin genislik-2 komsulugu."""
    e = np.zeros(y.shape, bool)
    e[:, 1:] |= y[:, 1:] != y[:, :-1]
    e[:, :-1] |= y[:, :-1] != y[:, 1:]
    e[1:, :] |= y[1:, :] != y[:-1, :]
    e[:-1, :] |= y[:-1, :] != y[1:, :]
    return np.stack([ndimage.binary_dilation(m, iterations=genislik)
                     for m in e])


def olcu(p, y):
    """mIoU (4 sinif), foreground Dice ve sinir bandi dogrulugu."""
    kar = np.zeros((C, C), np.int64)
    np.add.at(kar, (y.ravel(), p.ravel()), 1)
    tp = np.diag(kar).astype(float)
    fp = kar.sum(0) - tp
    fn = kar.sum(1) - tp
    iou = tp / np.maximum(tp + fp + fn, 1)
    dice = 2 * tp[1:] / np.maximum(2 * tp[1:] + fp[1:] + fn[1:], 1)
    band = sinir_bandi(y)
    sinir = float((p[band] == y[band]).mean())
    return float(iou.mean()), float(dice.mean()), sinir, iou


if __name__ == "__main__":
    print("GPU:", torch.cuda.get_device_name(0))
    Xtr, _, Str = veri_seti(2000, seed=0)
    Xte, _, Ste = veri_seti(500, seed=777)
    satirlar = ["atlama,tohum,mIoU,dice_on_plan,sinir_bandi"]
    for atlama in (True, False):
        ad = "atlamali" if atlama else "atlamasiz"
        for seed in (1, 2, 3):
            t0 = time.time()
            model = egit(seed, Xtr, Str, atlama)
            sure = time.time() - t0
            miou_tr, _, _, _ = olcu(tahmin(model, Xtr[:300]),
                                    Str[:300])
            p = tahmin(model, Xte)
            miou, dice, sinir, iou = olcu(p, Ste)
            print("%-10s tohum %d: test mIoU=%.4f  Dice(on)=%.4f  "
                  "sinir bandi=%.4f  [egitim mIoU=%.4f]  (%.0f s)"
                  % (ad, seed, miou, dice, sinir, miou_tr, sure))
            print("           sinif IoU (arka, daire, kare, ucgen):",
                  np.round(iou, 3).tolist())
            satirlar.append("%s,%d,%.4f,%.4f,%.4f"
                            % (ad, seed, miou, dice, sinir))
            if atlama and seed == 1:
                np.savez_compressed(
                    os.path.join(VERI, "b67_unet_ornek.npz"),
                    gercek=Ste[:6], tahmin=p[:6], X=Xte[:6, 0])
    with open(os.path.join(VERI, "b67_unet.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
