# -*- coding: utf-8 -*-
"""Bölüm 63.15: MLP'nin int8 tamsayı çıkarımı (Bölüm 46 hattı)."""
import os
import numpy as np
from sinir import VERI, veri_yukle

P = np.load(os.path.join(VERI, "b63_model.npz"))
(Xt, Yt, yt), _, (Xs, Ys, ys) = veri_yukle()
W = [P["W1"], P["W2"], P["W3"]]
B = [P["b1"], P["b2"], P["b3"]]


def float_ileri(X):
    H = X
    for i in range(3):
        H = H @ W[i] + B[i]
        if i < 2:
            H = np.maximum(0, H)
    return H


def nicem(maks):
    return maks / 127.0 if maks > 0 else 1.0


def kalibre():
    """Gizli katman aktivasyonlarının ölçeği, eğitim kümesinden."""
    sx = 1.0 / 127.0                    # girdi 0..1 aralığında
    sh = []
    H = Xt
    for i in range(2):
        H = np.maximum(0, H @ W[i] + B[i])
        sh.append(nicem(H.max()))
    return sx, sh


def int8_ileri(X, sx, sh):
    sw = [nicem(np.abs(w).max()) for w in W]
    xq = np.clip(np.round(X / sx), 0, 127).astype(np.int32)
    s_in = sx
    for i in range(3):
        Wq = np.clip(np.round(W[i] / sw[i]), -127, 127)
        Wq = Wq.astype(np.int32)
        bq = np.round(B[i] / (s_in * sw[i])).astype(np.int32)
        acc = xq @ Wq + bq          # tamsayı çarpma, int32 toplama
        if i < 2:
            # yeniden ölçekle ve ReLU'yu kırpma ile uygula
            xq = np.clip(np.round(acc * (s_in * sw[i]) / sh[i]),
                         0, 127).astype(np.int32)
            s_in = sh[i]
        else:
            return acc * (s_in * sw[i])  # son katman: ölçekli logit


if __name__ == "__main__":
    sx, sh = kalibre()
    fl = float_ileri(Xs)
    iq = int8_ileri(Xs, sx, sh)
    af = float(np.mean(fl.argmax(1) == ys))
    ai = float(np.mean(iq.argmax(1) == ys))
    uyum = float(np.mean(fl.argmax(1) == iq.argmax(1)))
    print("Test doğruluğu float32 = %.3f" % af)
    print("Test doğruluğu int8    = %.3f" % ai)
    print("Tahmin uyumu (float vs int8) = %.3f" % uyum)
    sayi = sum(w.size for w in W)
    nb = sum(b.size for b in B)
    print("Ağırlık sayısı = %d, bias sayısı = %d"
          % (sayi, nb))
    print("float32 ağırlık+bias bellek = %d bayt" % (4 * (sayi + nb)))
    print("int8 ağırlık + int32 bias = %d bayt" % (sayi + 4 * nb))
