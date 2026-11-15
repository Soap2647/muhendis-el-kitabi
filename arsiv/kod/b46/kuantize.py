# -*- coding: utf-8 -*-
"""float32 -> int8 kuantizasyon, tamsayi referans, C aktarimi.

Afin esleme:  r = S * (q - Z),  q in [-128, 127]
Girdi: asimetrik, katman basina; kalibrasyon min/maks ya da yuzdelik.
Agirliklar: simetrik (Z = 0). 1. katmanda kanal basina olcek, 2.
katmanda tek olcek (logit'ler ayni olcekte olsun diye).
Yeniden olcekleme: m = S_in * S_w / S_cikis = M0 / 2^rs, M0 Q31.
"""
import math
import os
import numpy as np
from telemetri import veri_seti
from egit import ozellik_matrisi

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
f32 = np.float32


def asimetrik(lo, hi):
    """int8 icin (S, Z). Sifir her zaman temsil edilir."""
    lo = min(float(lo), 0.0)
    hi = max(float(hi), 0.0)
    if hi - lo < 1e-9:
        hi = lo + 1e-6
    S = f32((hi - lo) / 255.0)
    Z = int(np.clip(np.round(-128 - lo / float(S)), -128, 127))
    return S, Z


def simetrik_olcek(W, eksen=None):
    """Simetrik int8 olcegi: S = max|W| / 127 (Z = 0)."""
    if eksen is None:
        return f32(np.abs(W).max() / 127.0)
    return f32(np.abs(W).max(axis=eksen) / 127.0)


def agirlik_kuantize(W, S):
    Sb = S if np.ndim(S) == 0 else S[:, None]
    q = np.round(W / Sb)
    return np.clip(q, -127, 127).astype(np.int64)


def m_ayristir(m):
    """m (0,1) -> (M0, rs): m ~ M0 / 2^rs, M0 in [2^30, 2^31)."""
    mant, e = math.frexp(m)
    M0 = int(round(mant * 2 ** 31))
    if M0 == 2 ** 31:
        M0 //= 2
        e += 1
    rs = 31 - e
    assert rs >= 1, "rs < 1: m cok buyuk"
    return M0, rs


def kalibre_et(W1, b1, Xn, kalib="minmax"):
    """Egitim verisinin float32 ileri gecisiyle araliklar."""
    a1 = np.maximum(Xn @ W1.T + b1, 0.0)
    if kalib == "minmax":
        aralik_x = (Xn.min(), Xn.max())
        aralik_a = (a1.min(), a1.max())
    else:  # yuzdelik: uc noktalar kirpilir
        aralik_x = tuple(np.percentile(Xn, [0.1, 99.9]))
        aralik_a = tuple(np.percentile(a1, [0.1, 99.9]))
    return aralik_x, aralik_a


def modeli_kuantize(p, Xn_train, kalib="minmax", kanal_basina=True):
    W1, b1, W2, b2 = p["W1"], p["b1"], p["W2"], p["b2"]
    (lo_x, hi_x), (lo_a, hi_a) = kalibre_et(W1, b1, Xn_train, kalib)
    S_in, Z_in = asimetrik(lo_x, hi_x)
    S_a1, Z_a1 = asimetrik(lo_a, hi_a)
    if kanal_basina:
        S_w1 = simetrik_olcek(W1, eksen=1)
    else:
        S_w1 = np.full(W1.shape[0], simetrik_olcek(W1), dtype=f32)
    S_w2 = simetrik_olcek(W2)
    W1q = agirlik_kuantize(W1, S_w1)
    W2q = agirlik_kuantize(W2, S_w2)
    # Onyargi: b_q = b / (S_in*S_w). Z_in terimi onyargiya katlanir:
    # sum (x - Z) w + b_q = sum x w + (b_q - Z * sum w)
    B1q = np.round(b1.astype(np.float64)
                   / (S_in * S_w1.astype(np.float64)))
    B1f = B1q.astype(np.int64) - Z_in * W1q.sum(axis=1)
    B2q = np.round(b2.astype(np.float64)
                   / (float(S_a1) * float(S_w2)))
    B2f = B2q.astype(np.int64) - Z_a1 * W2q.sum(axis=1)
    M1, RS1 = [], []
    for i in range(W1.shape[0]):
        m = float(S_in) * float(S_w1[i]) / float(S_a1)
        M0, rs = m_ayristir(m)
        M1.append(M0)
        RS1.append(rs)
    return dict(S_in=S_in, Z_in=Z_in, S_a1=S_a1, Z_a1=Z_a1,
                S_w1=S_w1, S_w2=S_w2, W1q=W1q, W2q=W2q, B1f=B1f,
                B2f=B2f, M1=np.array(M1, dtype=np.int64),
                RS1=np.array(RS1, dtype=np.int64),
                mu=p["mu"], sd=p["sd"])


def girdi_kuantize(F, Q):
    """Ham ozellik (float32) -> int8 girdi. C ile ayni sira."""
    v = ((F.astype(f32) - Q["mu"]) / Q["sd"]).astype(f32)
    w = (v / Q["S_in"]).astype(f32)
    q = np.floor(w + f32(0.5)).astype(np.int64) + Q["Z_in"]
    return np.clip(q, -128, 127).astype(np.int64)


def int_ileri(xq, Q):
    """Tam tamsayi cikarim.

    Doner: a1 (int8 degerler), logit (int32)."""
    acc1 = Q["W1q"] @ xq + Q["B1f"]
    y1 = acc1 * Q["M1"] + np.left_shift(np.int64(1), Q["RS1"] - 1)
    y1 = np.right_shift(y1, Q["RS1"])
    a1 = np.clip(y1 + Q["Z_a1"], Q["Z_a1"], 127)
    logit = Q["W2q"] @ a1 + Q["B2f"]
    return a1, logit


def float_ileri(xn, p):
    """Ayni yapi, float32 (kuantizasyon oncesi referans)."""
    a1 = np.maximum(xn @ p["W1"].T + p["b1"], 0.0)
    return a1 @ p["W2"].T + p["b2"]


def float_p(npz):
    return {k: npz[k] for k in ["W1", "b1", "W2", "b2", "mu", "sd"]}


def sinif_metrik(y, tahmin):
    tp = int(((tahmin == 1) & (y == 1)).sum())
    fp = int(((tahmin == 1) & (y == 0)).sum())
    fn = int(((tahmin == 0) & (y == 1)).sum())
    tn = int(((tahmin == 0) & (y == 0)).sum())
    pre = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    return pre, rec, (tn, fp, fn, tp)


def dizi_satirlari(ad, tip, degerler, kesim=66):
    """Degerleri en fazla 70 sutunluk C dizisi satirlarina boler."""
    parcalar = [str(v) for v in degerler]
    satirlar, cur = [], ""
    for k, s in enumerate(parcalar):
        ek = s + (", " if k < len(parcalar) - 1 else "")
        if len(cur) + len(ek) > kesim:
            satirlar.append(cur.rstrip())
            cur = ""
        cur += ek
    satirlar.append(cur.rstrip())
    govde = "\n    ".join(satirlar)
    return "static const %s %s[%d] = {\n    %s\n};\n\n" % (
        tip, ad, len(parcalar), govde)


def disa_aktar(Q, yol):
    """model_int8.h: agirliklar, onyargi, M0, rs, sabitler."""
    W1, W2 = Q["W1q"], Q["W2q"]
    nh, nin = W1.shape
    nout = W2.shape[0]
    out = ["/* Otomatik uretildi: kuantize.py.\n",
           "   Elle degistirmeyin. */\n",
           "#ifndef TM_MODEL_INT8_H\n#define TM_MODEL_INT8_H\n\n",
           "#include <stdint.h>\n\n",
           "#define TM_NIN %d\n#define TM_NH %d\n#define TM_NOUT %d\n"
           % (nin, nh, nout),
           "#define TM_ZIN (%d)\n#define TM_ZA1 (%d)\n\n"
           % (Q["Z_in"], Q["Z_a1"]),
           "static const float TM_SIN = %.9ef;\n\n"
           % float(Q["S_in"])]
    out.append(dizi_satirlari("TM_MU", "float",
                              ["%.9ef" % v for v in Q["mu"]]))
    out.append(dizi_satirlari("TM_SD", "float",
                              ["%.9ef" % v for v in Q["sd"]]))
    out.append(dizi_satirlari("TM_W1", "int8_t", W1.reshape(-1)))
    out.append(dizi_satirlari("TM_B1", "int32_t", Q["B1f"]))
    out.append(dizi_satirlari("TM_M1", "int32_t", Q["M1"]))
    out.append(dizi_satirlari("TM_RS1", "int32_t", Q["RS1"]))
    out.append(dizi_satirlari("TM_W2", "int8_t", W2.reshape(-1)))
    out.append(dizi_satirlari("TM_B2", "int32_t", Q["B2f"]))
    out.append("#endif\n")
    with open(yol, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(out))


def main():
    Xtr, ytr, Xte, yte = veri_seti()
    Ftr = ozellik_matrisi(Xtr)
    Fte = ozellik_matrisi(Xte)
    p = float_p(np.load(os.path.join(HERE, "model_f32.npz")))
    mu, sd = p["mu"], p["sd"]
    Xn_tr = ((Ftr.astype(f32) - mu) / sd).astype(f32)

    z2_f = float_ileri(((Fte.astype(f32) - mu) / sd).astype(f32), p)
    print("float32 test dogrulugu:      %.4f"
          % (z2_f.argmax(axis=1) == yte).mean())

    variantlar = [("kanal basina, minmax", True, "minmax"),
                  ("katman basina, minmax", False, "minmax"),
                  ("kanal basina, yuzdelik", True, "yuzdelik")]
    for ad, kanal, kal in variantlar:
        Qv = modeli_kuantize(p, Xn_tr, kal, kanal)
        tah = np.array([int_ileri(girdi_kuantize(Fte[i], Qv), Qv)[1]
                        .argmax() for i in range(len(Xte))])
        print("int8 (%-24s) dogruluk: %.4f"
              % (ad, (tah == yte).mean()))
    # Secilen varyant (kanal basina, minmax) C'ye aktarilir
    Q = modeli_kuantize(p, Xn_tr, "minmax", True)

    rows = []
    for i in range(len(Xte)):
        xq = girdi_kuantize(Fte[i], Q)
        a1, lg = int_ileri(xq, Q)
        rows.append((xq, a1, lg))
    lg_int = np.array([r[2] for r in rows]) * float(Q["S_a1"]) \
        * float(Q["S_w2"])
    fark = np.abs(lg_int - z2_f)
    print("max |logit_int8 - logit_f32|: %.4f" % fark.max())
    print("ortalama |fark|:              %.4f" % fark.mean())
    tah = np.array([r[2].argmax() for r in rows])
    print("argmax uyumu (int8 vs f32):   %.4f"
          % (tah == z2_f.argmax(axis=1)).mean())
    pre, rec, cm = sinif_metrik(yte, tah)
    print("int8 anomali: kesinlik %.4f, duyarlilik %.4f" % (pre, rec))
    print("karisiklik (tn, fp, fn, tp):", cm)

    skor_i8 = np.array([r[2][1] - r[2][0] for r in rows]) \
        * float(Q["S_a1"]) * float(Q["S_w2"])
    skor_f = z2_f[:, 1] - z2_f[:, 0]
    with open(os.path.join(VERI, "b46_anomali.csv"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("etiket,skor_f32,skor_int8\n")
        for e, a, b in zip(yte, skor_f, skor_i8):
            fh.write("%d,%.6f,%.6f\n" % (e, a, b))

    disa_aktar(Q, os.path.join(HERE, "model_int8.h"))
    XQ = np.array([r[0] for r in rows])
    BEK = np.array([[yte[i], r[2][0], r[2][1]]
                    for i, r in enumerate(rows)], dtype=np.int32)
    XQ.astype(np.int8).tofile(os.path.join(HERE, "test_xq.bin"))
    BEK.tofile(os.path.join(HERE, "test_beklenen.bin"))
    yol = os.path.join(HERE, "test_ozellik.bin")
    Fte.astype(np.float32).tofile(yol)
    yol = os.path.join(HERE, "test_pencere.bin")
    Xte.astype(np.float32).tofile(yol)
    # Tam aralikli rastgele int8 girdiler (tasma/doygunluk sinamasi)
    rng = np.random.default_rng(46)
    vecs = [np.full(20, -128), np.full(20, 127),
            np.tile([-128, 127], 10)]
    vecs += [rng.integers(-128, 128, 20) for _ in range(997)]
    RXQ = np.array(vecs, dtype=np.int64)
    RBEK = np.array([int_ileri(x, Q)[1] for x in RXQ], dtype=np.int32)
    RXQ.astype(np.int8).tofile(os.path.join(HERE, "test_r_xq.bin"))
    RBEK.tofile(os.path.join(HERE, "test_r_beklenen.bin"))
    print("rastgele vektor:", len(RXQ), "logit araligi:",
          int(RBEK.min()), int(RBEK.max()))
    print("C dosyalari yazildi: model_int8.h, test_*.bin")
    print("S_in=%.6g Z_in=%d S_a1=%.6g Z_a1=%d" % (
        Q["S_in"], Q["Z_in"], Q["S_a1"], Q["Z_a1"]))
    for i, (m0, rs) in enumerate(zip(Q["M1"], Q["RS1"])):
        print("kanal %d: M0 = %d, rs = %d" % (i, m0, rs))


if __name__ == "__main__":
    main()
