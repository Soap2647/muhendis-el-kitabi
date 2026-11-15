# -*- coding: utf-8 -*-
# b67_06_pr_ornek.py: sinif basina PR egrisi ve AP (CNN ve taban),
# sekil icin ornek tespit verisinin disari aktarimi.
import os
import pickle
import numpy as np
from b67_veri import veri_seti, SINIFLAR
from b67_02_ap import eslestir, pr_egrisi, ap_hesapla
from b67_04_yolo_mini import VERI, KLASOR
from b67_05_taban_hata import klasik_tespit


def sinif_pr(tahmin, Y, sinif, esik=0.5):
    """Tek sinif icin skor sirali PR ve AP (tum noktalar)."""
    skor, tp, ngt = [], [], 0
    for (tk, ts, tc), objs in zip(tahmin, Y):
        gk = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        gc = np.array([o["cls"] for o in objs], int)
        mg, mt = gc == sinif, tc == sinif
        ngt += int(mg.sum())
        kk, ss = tk[mt], ts[mt]
        sira = np.argsort(-ss, kind="stable")
        kk, ss = kk[sira], ss[sira]
        skor.append(ss)
        tp.append(eslestir(kk, gk[mg], esik))
    skor = np.concatenate(skor)
    tp = np.concatenate(tp)
    p, r = pr_egrisi(skor, tp, ngt)
    return p, r, ap_hesapla(skor, tp, ngt, "tum")


if __name__ == "__main__":
    Xte, Yte, _ = veri_seti(500, seed=777)
    taban = [klasik_tespit(img[0]) for img in Xte]
    with open(os.path.join(KLASOR, "cnn_pred.pkl"), "rb") as f:
        cnn = pickle.load(f)  # yerel, kendi urettigimiz ara dosya

    satirlar = ["yontem,sinif,recall,precision"]
    for ad, tah in (("cnn", cnn), ("taban", taban)):
        print("== %s: sinif basina AP (tum noktalar) ==" % ad)
        aplar = []
        for s, isim in enumerate(SINIFLAR):
            p, r, ap = sinif_pr(tah, Yte, s)
            aplar.append(ap)
            print("%-6s AP = %.4f  (son recall = %.3f)"
                  % (isim, ap, r[-1] if len(r) else 0.0))
            for ri, pi in zip(r[::5], p[::5]):
                satirlar.append("%s,%s,%.4f,%.4f"
                                % (ad, isim, ri, pi))
        print("mAP@0.5 = %.4f\n" % np.mean(aplar))

    with open(os.path.join(VERI, "b67_pr_egri.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")

    # Sekil icin: ilk 6 test sahnesi, kutular ve sinif adlari
    ornek = [0, 1, 2, 3, 4, 5]
    sat = ["gorsel,tur,sinif,skor,x1,y1,x2,y2"]
    for i in ornek:
        for o in Yte[i]:
            x1, y1, x2, y2 = o["box"]
            sat.append("%d,gercek,%s,1.00,%d,%d,%d,%d"
                       % (i, SINIFLAR[o["cls"]], x1, y1, x2, y2))
        kk, ss, cc = cnn[i]
        for b, s_, c in zip(kk, ss, cc):
            if s_ >= 0.5:
                sat.append("%d,cnn,%s,%.2f,%d,%d,%d,%d" % (
                    i, SINIFLAR[c], s_, b[0], b[1], b[2], b[3]))
    with open(os.path.join(VERI, "b67_tespit_ornek.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(sat) + "\n")
    np.savez_compressed(os.path.join(VERI, "b67_ornek_sahne.npz"),
                        X=Xte[ornek, 0])
    print("ornek satir sayisi:", len(sat) - 1)
    print("kaydedildi: engine/veri/b67_pr_egri.csv,")
    print("            engine/veri/b67_tespit_ornek.csv")
