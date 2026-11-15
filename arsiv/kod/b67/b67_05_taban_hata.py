# -*- coding: utf-8 -*-
# b67_05_taban_hata.py: klasik taban (esikleme + bagli bilesen +
# dolgu orani ile siniflandirma) ve CNN/taban hata analizi.
# Test seti ayni: tohum 777, 500 sahne. CNN tahminleri b67_04'ten.
import os
import pickle
import numpy as np
from scipy import ndimage
from b67_veri import veri_seti
from b67_01_iou_nms import iou_matris
from b67_02_ap import map_hesapla
from b67_04_yolo_mini import gercek, degerlendir, VERI, KLASOR

ESIK = 0.45                        # arka plan ~0.25, nesne >= 0.6
DOLGU = {0: np.pi / 4, 1: 1.0, 2: 0.5}  # daire, kare, ucgen


def klasik_tespit(img):
    """Esikleme, 8-komsuluk bagli bilesen, kutu ve dolgu orani."""
    etiket, _ = ndimage.label(img > ESIK, structure=np.ones((3, 3)))
    kutular, skor, sinif = [], [], []
    for k, sl in enumerate(ndimage.find_objects(etiket), 1):
        ys, xs = sl
        w, h = xs.stop - xs.start, ys.stop - ys.start
        alan = int((etiket[sl] == k).sum())
        if alan < 15:
            continue
        dolgu = alan / (w * h)
        c = min(DOLGU, key=lambda s: abs(DOLGU[s] - dolgu))
        kutular.append([xs.start, ys.start, xs.stop, ys.stop])
        skor.append(alan / 96.0 ** 2)
        sinif.append(c)
    return (np.array(kutular, float).reshape(-1, 4),
            np.array(skor, float), np.array(sinif, int))


def hata_siniflandir(tahmin, Y, esik_skor):
    """Her gercek kutu icin: bulundu, yanlis sinif, yerellestirme,
    kacirildi. Kucuk (<200 px^2) ve buyuk nesneler ayri sayilir."""
    sayac = {"bulundu": [0, 0], "yanlis_sinif": [0, 0],
             "yerellestirme": [0, 0], "kacirildi": [0, 0]}
    fp = 0
    for (tk, ts, tc), objs in zip(tahmin, Y):
        m = ts >= esik_skor
        tk, tc = tk[m], tc[m]
        gk = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        gc = np.array([o["cls"] for o in objs], int)
        iou = iou_matris(gk, tk) if len(tk) else \
            np.zeros((len(gk), 0))
        for i in range(len(gk)):
            alan_i = (gk[i, 2] - gk[i, 0]) * (gk[i, 3] - gk[i, 1])
            kucuk = alan_i < 200
            grup = 1 if kucuk else 0
            if iou.shape[1] == 0:
                sayac["kacirildi"][grup] += 1
                continue
            j = int(np.argmax(iou[i]))
            v = iou[i, j]
            if v >= 0.5 and tc[j] == gc[i]:
                sayac["bulundu"][grup] += 1
            elif v >= 0.5:
                sayac["yanlis_sinif"][grup] += 1
            elif v >= 0.3:
                sayac["yerellestirme"][grup] += 1
            else:
                sayac["kacirildi"][grup] += 1
        if len(tk):
            en_iyi = iou.max(axis=0) if len(gk) else np.zeros(len(tk))
            fp += int((en_iyi < 0.5).sum())
    return sayac, fp


def yazdir(ad, sayac, fp, toplam):
    print("%s (toplam gercek kutu = %d, yanlis pozitif = %d)"
          % (ad, toplam, fp))
    for anahtar, (k, b) in sayac.items():
        print("   %-14s kucuk=%4d  buyuk=%4d" % (anahtar, k, b))


if __name__ == "__main__":
    Xte, Yte, _ = veri_seti(500, seed=777)
    toplam = sum(len(y) for y in Yte)
    gt = gercek(Yte)

    taban = [klasik_tespit(img[0]) for img in Xte]
    _, m50_t = map_hesapla(taban, gt, 0.5, "tum")
    print("Klasik taban: mAP@0.5 = %.4f" % m50_t)
    # pickle: yalnizca bu projenin b67_04 betiginin kendi urettigi,
    # yerel bir ara dosya okunuyor (guvenilmeyen kaynak degil).
    with open(os.path.join(KLASOR, "cnn_pred.pkl"), "rb") as f:
        cnn = pickle.load(f)
    m50_c, mco_c = degerlendir(cnn, Yte)
    print("CNN (tohum 1): mAP@0.5 = %.4f, mAP@[.5:.95] = %.4f"
          % (m50_c, mco_c))

    print("\n== Hata analizi (CNN skor >= 0.50; taban hepsi) ==")
    s_c, fp_c = hata_siniflandir(cnn, Yte, 0.50)
    s_t, fp_t = hata_siniflandir(taban, Yte, 0.0)
    yazdir("CNN", s_c, fp_c, toplam)
    yazdir("Taban", s_t, fp_t, toplam)

    kayit = os.path.join(VERI, "b67_hata_analizi.csv")
    with open(kayit, "w", encoding="utf-8") as f:
        f.write("yontem,kategori,kucuk,buyuk,yanlis_pozitif\n")
        for ad, s, fp in (("cnn", s_c, fp_c), ("taban", s_t, fp_t)):
            for anahtar, (k, b) in s.items():
                f.write("%s,%s,%d,%d,%d\n"
                        % (ad, anahtar, k, b,
                           fp if anahtar == "bulundu" else 0))
    print("\nkaydedildi:", kayit)
