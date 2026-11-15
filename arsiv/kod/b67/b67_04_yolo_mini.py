# -*- coding: utf-8 -*-
# b67_04_yolo_mini.py: tek asamali (YOLO tarzi) mini dedektor.
# 12x12 izgara, hucre basina 2 anchor, 3 sinif. Sentetik veri,
# GPU egitimi. Egitim: tohum 0 (2000 sahne); test: tohum 777 (500).
import os
import time
import pickle
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b67_veri import veri_seti
from b67_03_anchor import hedefle, ANCHORS, S, yolo_coz
from b67_01_iou_nms import sinif_nms, xywh_to_xyxy
from b67_02_ap import map_hesapla, coco_tarzi_map

G, A, C = 12, 2, 3
AYGIT = "cuda"
KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
GX, GY = np.meshgrid(np.arange(G), np.arange(G))


def cbr(giris, cikis, adim):
    return nn.Sequential(
        nn.Conv2d(giris, cikis, 3, adim, 1, bias=False),
        nn.BatchNorm2d(cikis), nn.ReLU(inplace=True))


class MiniYolo(nn.Module):
    """96x96 gri girdi -> (B, G, G, A, 5+C). Adim 8 (3 kez /2)."""

    def __init__(self):
        super().__init__()
        self.govde = nn.Sequential(cbr(1, 16, 2), cbr(16, 32, 2),
                                   cbr(32, 64, 2), cbr(64, 64, 1))
        self.bas = nn.Conv2d(64, A * (5 + C), 1)

    def forward(self, x):
        y = self.bas(self.govde(x))
        b, _, g, _ = y.shape      # izgara boyutu girdiden okunur
        return y.view(b, A, 5 + C, g, g).permute(0, 3, 4, 1, 2)


def hedef_tensorleri(Y):
    """Kutu listesinden egitim hedefleri. Ofsetler (sigmoid uzayi) ve
    log-olcekli genislik/yukseklik hedefleri olarak saklanir."""
    n = len(Y)
    poz = np.zeros((n, G, G, A), bool)
    otg = np.zeros((n, G, G, A, 4), np.float32)
    cls = np.zeros((n, G, G, A), np.int64)
    for i, objs in enumerate(Y):
        kut = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        c = np.array([o["cls"] for o in objs], int)
        p, h, s, _ = hedefle(kut, c, G)
        poz[i], cls[i] = p, s
        otg[i, ..., 0:2] = 1 / (1 + np.exp(-h[..., 0:2]))
        otg[i, ..., 2:4] = h[..., 2:4]
    return poz, otg, cls


def kayip(out, poz, otg, cls):
    """Nesnellik (BCE, pozitiflere x3 agirlik) + kutu (MSE, x5)
    + sinif (CE). Kutu ve sinif kaybi yalnizca pozitif hucrelerde."""
    obj = out[..., 4]
    agirlik = torch.tensor(3.0, device=out.device)
    l_obj = F.binary_cross_entropy_with_logits(
        obj, poz.float(), pos_weight=agirlik)
    pb = out[..., :4][poz]
    tb = otg[poz]
    l_box = F.mse_loss(torch.sigmoid(pb[:, 0:2]), tb[:, 0:2]) + \
        F.mse_loss(pb[:, 2:4], tb[:, 2:4])
    l_cls = F.cross_entropy(out[..., 5:][poz], cls[poz])
    return l_obj + 5.0 * l_box + l_cls


def egit(seed, X, poz, otg, cls, epoch=60, bs=64):
    torch.manual_seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = MiniYolo().to(AYGIT)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3,
                            weight_decay=1e-4)
    adim = int(np.ceil(len(X) / bs))
    sch = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=2e-3, total_steps=epoch * adim)
    Xt = torch.tensor(X, device=AYGIT)
    Pt = torch.tensor(poz, device=AYGIT)
    Ot = torch.tensor(otg, device=AYGIT)
    Ct = torch.tensor(cls, device=AYGIT)
    model.train()
    for _ in range(epoch):
        perm = torch.randperm(len(X), generator=g)
        for i in range(0, len(X), bs):
            idx = perm[i:i + bs].to(AYGIT)
            out = model(Xt[idx])
            L = kayip(out, Pt[idx], Ot[idx], Ct[idx])
            opt.zero_grad()
            L.backward()
            opt.step()
            sch.step()
    return model.eval()


def decode(out, esik=0.05, en_cok=100):
    """(N,G,G,A,8) ham cikti -> gorsel basina (kutu, skor, sinif)."""
    sonuc = []
    for o in out:
        obj = 1 / (1 + np.exp(-o[..., 4]))
        e = np.exp(o[..., 5:] - o[..., 5:].max(-1, keepdims=True))
        pr = e / e.sum(-1, keepdims=True)
        sk = obj[..., None] * pr
        gy, gx, a, c = np.where(sk > esik)
        skor = sk[gy, gx, a, c]
        hc = np.stack([gx, gy], 1).astype(float)
        kut = yolo_coz(o[gy, gx, a, :4], hc, ANCHORS[a])
        kut = np.clip(xywh_to_xyxy(kut), 0, 96)
        tut = sinif_nms(kut, skor, c, 0.5)[:en_cok]
        sonuc.append((kut[tut], skor[tut], c[tut]))
    return sonuc


@torch.no_grad()
def tahmin(model, X):
    cikti = []
    for i in range(0, len(X), 128):
        xb = torch.tensor(X[i:i + 128], device=AYGIT)
        cikti.append(model(xb).float().cpu().numpy())
    return decode(np.concatenate(cikti))


def gercek(Y):
    return [(np.array([o["box"] for o in objs], float).reshape(-1, 4),
             np.array([o["cls"] for o in objs], int)) for objs in Y]


def degerlendir(pred, Y):
    """Donus: mAP@0.5 (tum noktalar) ve mAP@[.5:.95] (101 nokta)."""
    gt = gercek(Y)
    _, m50 = map_hesapla(pred, gt, 0.5, "tum")
    m_coco, _ = coco_tarzi_map(pred, gt)
    return m50, m_coco


if __name__ == "__main__":
    print("GPU:", torch.cuda.get_device_name(0))
    Xtr, Ytr, _ = veri_seti(2000, seed=0)
    Xte, Yte, _ = veri_seti(500, seed=777)
    Ptr, Otr, Ctr = hedef_tensorleri(Ytr)
    print("egitim pozitif hucre/gorsel: %.2f"
          % Ptr.reshape(len(Ptr), -1).sum(1).mean())
    satirlar = []
    for seed in (1, 2, 3):
        t0 = time.time()
        model = egit(seed, Xtr, Ptr, Otr, Ctr)
        sure = time.time() - t0
        ap_tr, _ = degerlendir(tahmin(model, Xtr[:300]), Ytr[:300])
        ap_te, coco_te = degerlendir(tahmin(model, Xte), Yte)
        print("tohum %d: egitim mAP@0.5=%.4f | test mAP@0.5=%.4f"
              "  test mAP@[.5:.95]=%.4f  (%.0f s)"
              % (seed, ap_tr, ap_te, coco_te, sure))
        satirlar.append((seed, ap_tr, ap_te, coco_te))
        if seed == 1:
            pred1 = tahmin(model, Xte)
            yol = os.path.join(KLASOR, "cnn_pred.pkl")
            with open(yol, "wb") as f:
                pickle.dump(pred1, f)
            torch.save(model.state_dict(),
                       os.path.join(KLASOR, "yolo_t1.pt"))
    te = np.array([s[2] for s in satirlar])
    co = np.array([s[3] for s in satirlar])
    print("test mAP@0.5 = %.4f +- %.4f" % (te.mean(), te.std(ddof=1)))
    print("test mAP@[.5:.95] = %.4f +- %.4f"
          % (co.mean(), co.std(ddof=1)))
    with open(os.path.join(VERI, "b67_yolo_tohum.csv"), "w",
              encoding="utf-8") as f:
        f.write("tohum,egitim_map50,test_map50,test_map_5095\n")
        for s in satirlar:
            f.write("%d,%.4f,%.4f,%.4f\n" % s)
