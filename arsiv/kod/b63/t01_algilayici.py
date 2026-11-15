# -*- coding: utf-8 -*-
"""Bölüm 63.2: algılayıcı; AND öğrenir, XOR öğrenmez."""
import csv, os
import numpy as np
from sinir import VERI

X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
YAND = np.array([0, 0, 0, 1])
YXOR = np.array([0, 1, 1, 0])


def egit(y, epoch=1000, eta=1.0, iz=False):
    w, b = np.zeros(2), 0.0
    hatalar = []
    for ep in range(epoch):
        hata = 0
        for x, t in zip(X, y):
            s = x @ w + b
            tah = int(s >= 0)
            g = t - tah                  # -1, 0 ya da +1
            if iz and ep == 0:
                print("  x=%s t=%d s=%+.1f tah=%d g=%+d w=%s b=%+.1f"
                      % (x.astype(int), t, s, tah, g, w, b))
            if g != 0:
                w = w + eta * g * x
                b = b + eta * g
                hata += 1
        hatalar.append(hata)
        if hata == 0:
            break
    return w, b, hatalar


def izgara_en_iyi(y):
    """Tüm (w1, w2, b) ızgarasında en az hatalı çizgi."""
    en = (99, None)
    for w1 in np.arange(-2, 2.01, 0.1):
        for w2 in np.arange(-2, 2.01, 0.1):
            for b in np.arange(-2, 2.01, 0.1):
                tah = (X @ np.array([w1, w2]) + b >= 0).astype(int)
                e = int(np.sum(tah != y))
                if e < en[0]:
                    en = (e, (w1, w2, b))
    return en


def csv_yaz(yol, satirlar, baslik):
    with open(yol, "w", newline="", encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(baslik)
        yz.writerows(satirlar)


if __name__ == "__main__":
    print("AND, ilk epoch izi:")
    w, b, h = egit(YAND, iz=True)
    print("AND: w=%s b=%+.1f, epoch sayısı=%d, hatalar=%s"
          % (w, b, len(h), h))
    wa, ba = w, b
    print("XOR, 1000 epoch:")
    wx, bx, hx = egit(YXOR, epoch=1000)
    print("XOR: son hata=%d, en küçük epoch hatası=%d"
          % (hx[-1], min(hx)))
    print("XOR son epochların hataları:", hx[-5:])
    e, (a1, a2, a3) = izgara_en_iyi(YXOR)
    print("XOR ızgara araması en az hata=%d, w=(%.1f,%.1f) b=%.1f"
          % (e, a1, a2, a3))
    nok = []
    for x, ya, yx in zip(X, YAND, YXOR):
        nok.append(["AND", x[0], x[1], ya])
        nok.append(["XOR", x[0], x[1], yx])
    csv_yaz(os.path.join(VERI, "b63_algilayici_nokta.csv"), nok,
            ["senaryo", "x1", "x2", "y"])
    csv_yaz(os.path.join(VERI, "b63_algilayici_cizgi.csv"),
            [["AND", wa[0], wa[1], ba, 0],
             ["XOR", wx[0], wx[1], bx, hx[-1]],
             ["XOR_izgara", a1, a2, a3, e]],
            ["senaryo", "w1", "w2", "b", "hata"])
