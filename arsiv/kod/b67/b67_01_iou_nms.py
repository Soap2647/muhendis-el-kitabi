# -*- coding: utf-8 -*-
# b67_01_iou_nms.py: kutu donusumu, IoU, GIoU, NMS, Soft-NMS.
# Sifirdan yazilmis surumleri torchvision ile karsilastirir.
import numpy as np
import torch
from torchvision.ops import box_iou as tv_iou
from torchvision.ops import nms as tv_nms
from torchvision.ops import batched_nms as tv_bnms


def xywh_to_xyxy(c):
    """(cx, cy, w, h) -> (x1, y1, x2, y2)."""
    c = np.asarray(c, dtype=np.float64)
    return np.stack([c[:, 0] - c[:, 2] / 2, c[:, 1] - c[:, 3] / 2,
                     c[:, 0] + c[:, 2] / 2, c[:, 1] + c[:, 3] / 2], 1)


def xyxy_to_xywh(b):
    """(x1, y1, x2, y2) -> (cx, cy, w, h)."""
    b = np.asarray(b, dtype=np.float64)
    w, h = b[:, 2] - b[:, 0], b[:, 3] - b[:, 1]
    return np.stack([b[:, 0] + w / 2, b[:, 1] + h / 2, w, h], 1)


def alan(b):
    """Dejenere kutularda (negatif genislik) alan 0 sayilir."""
    return np.clip(b[:, 2] - b[:, 0], 0, None) * \
        np.clip(b[:, 3] - b[:, 1], 0, None)


def kesisim_birlik(a, b):
    """Kesisim ve birlik alanlari, (N,M) matrisler olarak."""
    x1 = np.maximum(a[:, None, 0], b[None, :, 0])
    y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2])
    y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    birlik = alan(a)[:, None] + alan(b)[None, :] - inter
    return inter, birlik


def iou_matris(a, b):
    """a: (N,4), b: (M,4) -> (N,M) IoU. Birlik 0 ise IoU = 0."""
    inter, birlik = kesisim_birlik(a, b)
    return np.where(birlik > 0,
                    inter / np.maximum(birlik, 1e-12), 0.0)


def giou_matris(a, b):
    """GIoU = IoU - (C - B) / C; C kapsayan kutunun alani."""
    inter, birlik = kesisim_birlik(a, b)
    iou = np.where(birlik > 0, inter / np.maximum(birlik, 1e-12), 0.0)
    x1 = np.minimum(a[:, None, 0], b[None, :, 0])
    y1 = np.minimum(a[:, None, 1], b[None, :, 1])
    x2 = np.maximum(a[:, None, 2], b[None, :, 2])
    y2 = np.maximum(a[:, None, 3], b[None, :, 3])
    c = (x2 - x1) * (y2 - y1)
    return np.where(c > 0,
                    iou - (c - birlik) / np.maximum(c, 1e-12), iou)


def nms(kutular, skorlar, esik):
    """Acgozlu NMS. IoU > esik olan kutular bastirilir."""
    sira = np.argsort(-skorlar, kind="stable")
    tutulan = []
    while sira.size > 0:
        i = sira[0]
        tutulan.append(i)
        if sira.size == 1:
            break
        iou = iou_matris(kutular[i:i + 1], kutular[sira[1:]])[0]
        sira = sira[1:][iou <= esik]
    return np.array(tutulan, dtype=np.int64)


def sinif_nms(kutular, skorlar, siniflar, esik):
    """Sinif basina NMS: farkli siniflar birbirini bastirmaz.
    Ofset numarasi: her sinifin kutularini ayri bir koordinat
    bolgesine kaydirir (torchvision batched_nms da ayni fikri)."""
    if len(kutular) == 0:
        return np.zeros(0, dtype=np.int64)
    ofset = siniflar[:, None].astype(np.float64) * (
        kutular.max() + 1.0)
    tutulan = nms(kutular + ofset, skorlar, esik)
    return tutulan


def soft_nms(kutular, skorlar, sigma=0.5, esik_min=0.001):
    """Gauss Soft-NMS: bastirma yerine skoru IoU'ya gore azaltir."""
    skor = skorlar.astype(np.float64).copy()
    kalan = np.arange(len(skor))
    sirali, yeni = [], []
    while kalan.size > 0:
        m = int(np.argmax(skor[kalan]))
        i = kalan[m]
        sirali.append(i)
        yeni.append(skor[i])
        kalan = np.delete(kalan, m)
        if kalan.size == 0:
            break
        iou = iou_matris(kutular[i:i + 1], kutular[kalan])[0]
        skor[kalan] *= np.exp(-(iou ** 2) / sigma)
        kalan = kalan[skor[kalan] >= esik_min]
    return np.array(sirali), np.array(yeni)


def testler():
    print("== Kenar durumlari (IoU) ==")
    k = np.array([[0, 0, 10, 10.0]])
    durum = {
        "ayni kutu": (k, k),
        "hic ortusmuyor": (k, np.array([[20, 20, 30, 30.0]])),
        "yalnizca kenar temas": (k, np.array([[10, 0, 20, 10.0]])),
        "ic ice (1 / 4 kare)": (np.array([[0, 0, 4, 4.0]]),
                                np.array([[1, 1, 3, 3.0]])),
        "dejenere (genislik 0)": (k, np.array([[5, 5, 5, 9.0]])),
        "iki dejenere": (np.array([[2, 2, 2, 2.0]]),
                         np.array([[2, 2, 2, 2.0]])),
    }
    for ad, (a, b) in durum.items():
        print("%-24s IoU=%.4f  GIoU=%.4f" % (
            ad, iou_matris(a, b)[0, 0], giou_matris(a, b)[0, 0]))
    print("\n== torchvision karsilastirmasi (rastgele, tohum 0) ==")
    rng = np.random.default_rng(0)
    xy = rng.uniform(0, 100, (300, 2))
    wh = rng.uniform(1, 40, (300, 2))
    A = np.hstack([xy, xy + wh])
    B = np.hstack([rng.uniform(0, 100, (250, 2)),
                   rng.uniform(0, 100, (250, 2))])
    B[:, 2:] = B[:, :2] + rng.uniform(1, 40, (250, 2))
    ours = iou_matris(A, B)
    tv = tv_iou(torch.tensor(A, dtype=torch.float32),
                torch.tensor(B, dtype=torch.float32)).numpy()
    print("maks |fark| IoU: %.2e" % np.abs(ours - tv).max())
    print("IoU > 0 olan cift sayisi:", int((ours > 0).sum()))


def nms_ornegi():
    print("\n== NMS ornegi (altı kutu) ==")
    kutu = np.array([
        [10, 10, 50, 50], [12, 12, 52, 52], [60, 60, 100, 100],
        [58, 58, 98, 98], [10, 60, 40, 90], [30, 30, 70, 70]], float)
    skor = np.array([0.90, 0.85, 0.80, 0.75, 0.70, 0.65])
    print("IoU(1,2) = %.4f  IoU(3,4) = %.4f" % (
        iou_matris(kutu[0:1], kutu[1:2])[0, 0],
        iou_matris(kutu[2:3], kutu[3:4])[0, 0]))
    for esik in (0.5, 0.1):
        t = nms(kutu, skor, esik)
        print("esik=%.1f tutulan indisler: %s" % (esik, t.tolist()))
    ref = tv_nms(torch.tensor(kutu, dtype=torch.float32),
                 torch.tensor(skor, dtype=torch.float32), 0.5).numpy()
    print("torchvision nms(0.5):", ref.tolist())
    sn, ss = soft_nms(kutu, skor, sigma=0.5)
    print("soft-NMS sirasi:", sn.tolist())
    print("soft-NMS skorlari:", np.round(ss, 4).tolist())


def rastgele_karsilastirma():
    print("\n== NMS ve sinif-NMS: torchvision ile birebir mi? ==")
    rng = np.random.default_rng(1)
    eslesen, toplam = 0, 0
    for _ in range(200):
        n = int(rng.integers(5, 60))
        xy = rng.uniform(0, 80, (n, 2))
        K = np.hstack([xy, xy + rng.uniform(4, 30, (n, 2))])
        s = rng.uniform(0, 1, n)
        for esik in (0.3, 0.5, 0.7):
            ours = nms(K, s, esik)
            ref = tv_nms(torch.tensor(K, dtype=torch.float32),
                         torch.tensor(s, dtype=torch.float32), esik)
            eslesen += int(np.array_equal(ours, ref.numpy()))
            toplam += 1
    print("tek sinif: %d / %d koşu birebir ayni" % (eslesen, toplam))
    eslesen = 0
    for _ in range(100):
        n = int(rng.integers(5, 40))
        xy = rng.uniform(0, 80, (n, 2))
        K = np.hstack([xy, xy + rng.uniform(4, 30, (n, 2))])
        s = rng.uniform(0, 1, n)
        c = rng.integers(0, 3, n)
        ours = sinif_nms(K, s, c, 0.5)
        ref = tv_bnms(torch.tensor(K, dtype=torch.float32),
                      torch.tensor(s, dtype=torch.float32),
                      torch.tensor(c), 0.5).numpy()
        eslesen += int(np.array_equal(ours, ref))
    print("sinif-NMS: %d / 100 koşu birebir ayni" % eslesen)


if __name__ == "__main__":
    testler()
    nms_ornegi()
    rastgele_karsilastirma()
