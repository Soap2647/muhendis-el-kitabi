# -*- coding: utf-8 -*-
# b80_egit.py: uc tohumlu MiniYolo egitimi (GPU), klasik taban ve
# test / operasyonel (drift) / OOD degerlendirmesi. Sayilar CSV'ye.
import os
import pickle
import time
import numpy as np
import torch
from scipy.ndimage import label, find_objects
from b80_veri import veri_seti, EGITIM, NOMINAL, DRIFT, DRIFT_AGIR
from b67_04_yolo_mini import (
    hedef_tensorleri,
    egit,
    tahmin,
    degerlendir,
)

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TOHUMLAR = [1, 2, 3]
ESIK_KLASIK = 0.45  # sabit esik (elle secildi)
DOLULUK = {0: 0.785, 1: 1.0, 2: 0.5}  # daire, kare, ucgen


def klasik(img):
    """Esikleme + bagli bilesenler. Sinif: kutu icindeki doluluk
    oranina gore en yakin sekil. Skor: bilesenin ort. parlakligi."""
    etk, _ = label(img > ESIK_KLASIK)
    kut, skor, cls = [], [], []
    for k, sl in enumerate(find_objects(etk), 1):
        maske = etk[sl] == k
        alan = int(maske.sum())
        if alan < 15:
            continue
        doluluk = alan / maske.size
        c = min(DOLULUK, key=lambda c: abs(doluluk - DOLULUK[c]))
        kut.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])
        skor.append(float(img[sl][maske].mean()))
        cls.append(c)
    return (
        np.array(kut, float).reshape(-1, 4),
        np.array(skor),
        np.array(cls, int),
    )


def main():
    print("GPU:", torch.cuda.get_device_name(0))
    Xtr, Ytr = veri_seti(3000, seed=0, ayar=EGITIM)
    kumeler = {
        "val": veri_seti(300, seed=5, ayar=EGITIM),
        "test": veri_seti(500, seed=777, ayar=NOMINAL),
        "drift": veri_seti(500, seed=888, ayar=DRIFT),
        "agir": veri_seti(500, seed=890, ayar=DRIFT_AGIR),
        "ood": veri_seti(500, seed=999, ayar=NOMINAL, kus=1),
    }
    satirlar = []  # (yontem, tohum, kume, m50, m)
    for ad, (X, Y) in kumeler.items():
        pred = [klasik(img) for img in X[:, 0]]
        m50, m5095 = degerlendir(pred, Y)
        satirlar.append(("klasik", 0, ad, m50, m5095))
        print(
            "klasik %-6s mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
            % (ad, m50, m5095)
        )
    ptr, otg, ctr = hedef_tensorleri(Ytr)
    tahminler = {}
    for seed in TOHUMLAR:
        t0 = time.time()
        model = egit(seed, Xtr, ptr, otg, ctr, epoch=60)
        sure = time.time() - t0
        torch.save(
            model.state_dict(),
            os.path.join(KLASOR, "yolo_t%d.pt" % seed),
        )
        for ad, (X, Y) in kumeler.items():
            pred = tahmin(model, X)
            tahminler[(seed, ad)] = pred
            m50, m5095 = degerlendir(pred, Y)
            satirlar.append(("cnn", seed, ad, m50, m5095))
            print(
                "tohum %d %-6s mAP@0.5=%.4f  mAP@[.5:.95]=%.4f"
                % (seed, ad, m50, m5095)
            )
        print("tohum %d egitim suresi: %.0f s" % (seed, sure))
    with open(os.path.join(KLASOR, "tahminler.pkl"), "wb") as f:
        pickle.dump(tahminler, f)
    with open(
        os.path.join(VERI, "b80_detektor.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("yontem,tohum,kume,map50,map5095\n")
        for s in satirlar:
            f.write("%s,%d,%s,%.4f,%.4f\n" % s)
    print("\nOzet (cnn: 3 tohum ort. +- ss):")
    for ad in kumeler:
        a = np.array(
            [s[3] for s in satirlar if s[0] == "cnn" and s[2] == ad]
        )
        b = np.array(
            [s[4] for s in satirlar if s[0] == "cnn" and s[2] == ad]
        )
        print(
            "%-6s mAP@0.5 = %.4f +- %.4f | mAP@[.5:.95] = %.4f"
            % (ad, a.mean(), a.std(ddof=1), b.mean())
        )


if __name__ == "__main__":
    main()
