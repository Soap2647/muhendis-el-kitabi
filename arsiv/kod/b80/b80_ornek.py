# -*- coding: utf-8 -*-
# b80_ornek.py: sekiller icin ornek sahneleri ve seed-1 tespitlerini
# engine/veri/b80_ornek_sahne.npz dosyasina yazar (deterministik).
import os
import pickle
import numpy as np
from b80_veri import veri_seti, NOMINAL, DRIFT
from b67_01_iou_nms import iou_matris

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def paketle(X, Y, pred, n=3):
    """n goruntu: goruntu, gt kutu (-1 dolgu), tespit (skor>=0.3)."""
    img = X[:n, 0]
    gt = -np.ones((n, 8, 4))
    gcls = -np.ones((n, 8), int)
    dk = -np.ones((n, 8, 4))
    dsk = -np.ones((n, 8))
    dcl = -np.ones((n, 8), int)
    for i in range(n):
        for j, o in enumerate(Y[i][:8]):
            gt[i, j] = o["box"]
            gcls[i, j] = o["cls"]
        kut, skor, cls = pred[i]
        m = np.where(skor >= 0.3)[0][:8]
        dk[i, : len(m)] = kut[m]
        dsk[i, : len(m)] = skor[m]
        dcl[i, : len(m)] = cls[m]
    return img, gt, gcls, dk, dsk, dcl


def main():
    tah = pickle.load(
        open(os.path.join(KLASOR, "tahminler.pkl"), "rb")
    )
    cikti = {}
    for ad, seed_k, ayar_kus in [
        ("test", 777, 0),
        ("drift", 888, 0),
        ("ood", 999, 1),
    ]:
        X, Y = veri_seti(
            500,
            seed=seed_k,
            ayar=DRIFT if ad == "drift" else NOMINAL,
            kus=ayar_kus,
        )
        img, gt, gc, dk, dsk, dcl = paketle(X, Y, tah[(1, ad)])
        cikti[ad + "_img"] = img
        cikti[ad + "_gt"] = gt
        cikti[ad + "_gc"] = gc
        cikti[ad + "_dk"] = dk
        cikti[ad + "_dsk"] = dsk
        cikti[ad + "_dc"] = dcl
    np.savez_compressed(
        os.path.join(VERI, "b80_ornek_sahne.npz"), **cikti
    )
    print("yazildi: b80_ornek_sahne.npz (%d dizi)" % len(cikti))


if __name__ == "__main__":
    main()
