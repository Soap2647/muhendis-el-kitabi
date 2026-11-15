# -*- coding: utf-8 -*-
"""Bolum 75: 64-32-10 MLP'nin int8 MCU surumu icin
agirliklari ve test vektorlerini C basligina yazar; referans ayni
float32 islem sirasiyla gecen tamsayi sonuclarini uretir."""

import os, sys
import numpy as np
import torch

sys.path.insert(0, "C:/Users/merty/AppData/Local/Temp/b75")
from b75_ortak import veri, mlp_t, egit, dogruluk

HERE = os.path.dirname(os.path.abspath(__file__))


def yuvarla(v):
    """Sifirdan uzaga yuvarlama (C'deki round_away ile birebir)."""
    v = np.asarray(v, dtype=np.float32)
    return np.where(
        v >= 0,
        np.floor(v + np.float32(0.5)),
        -np.floor(-v + np.float32(0.5)),
    ).astype(np.int32)


def kirp8(v):
    return np.clip(v, -127, 127).astype(np.int32)


def olcek(x):
    """Simetrik tensor olcegi: max|x| / 127."""
    return np.float32(np.max(np.abs(x)) / 127.0)


def main():
    Xtr, ytr, Xte, yte = veri(0)
    m = mlp_t(0, gizli=(32,))
    egit(m, Xtr, ytr, tohum=0)
    m.eval()
    print("fp32 test dogruluk: %.4f" % dogruluk(m, Xte, yte))
    W1 = m[0].weight.detach().numpy().astype(np.float32)
    b1 = m[0].bias.detach().numpy().astype(np.float32)
    W2 = m[2].weight.detach().numpy().astype(np.float32)
    b2 = m[2].bias.detach().numpy().astype(np.float32)
    # Kalibrasyon: egitim verisinin son 200 ornegi (test verisi degil)
    Xcal = Xtr[-200:].numpy().astype(np.float32)
    sx = np.float32(1.0 / 127.0)  # girdi (0..1) -> int8
    sw1, sw2 = olcek(W1), olcek(W2)
    h = np.maximum(Xcal @ W1.T + b1, 0)
    sa = olcek(h)  # gizli aktivasyon olcegi
    Wq1 = kirp8(yuvarla(W1 / sw1))
    Wq2 = kirp8(yuvarla(W2 / sw2))
    bq1 = yuvarla(b1 / (sx * sw1))
    bq2 = yuvarla(b2 / (sa * sw2))
    M1 = np.float32(sx * sw1 / sa)  # yeniden olcekleme carpani

    # Referans: int8 ileri gecis (C ile ayni islem sirasi)
    def ileri(xq):
        acc1 = xq.astype(np.int32) @ Wq1.T.astype(np.int32) + bq1
        v = acc1.astype(np.float32) * M1
        hq = np.maximum(kirp8(yuvarla(v)), 0)
        acc2 = hq @ Wq2.T.astype(np.int32) + bq2
        return acc2

    Xq = kirp8(yuvarla(Xte.numpy() / sx))
    logit = np.array(
        [ileri(Xq[i : i + 1])[0] for i in range(len(Xq))]
    )
    etiket = logit.argmax(1)
    print("int8 test dogruluk: %.4f" % (etiket == yte.numpy()).mean())
    # C basligi: agirliklar
    with open(
        os.path.join(HERE, "model_w.h"), "w", encoding="utf-8"
    ) as f:
        f.write("/* otomatik uretildi: gen_mcu.py */\n")
        f.write(
            "#define M1_BOYUT 64\n#define H_BOYUT 32\n#define "
            "C_BOYUT 10\n"
        )
        f.write("static const int8_t W1[32][64] = {\n")
        for r in Wq1:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write(
            "};\nstatic const int32_t B1[32] = {"
            + ",".join(str(int(v)) for v in bq1)
            + "};\n"
        )
        f.write("static const int8_t W2[10][32] = {\n")
        for r in Wq2:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write(
            "};\nstatic const int32_t B2[10] = {"
            + ",".join(str(int(v)) for v in bq2)
            + "};\n"
        )
        f.write("static const float M1 = %.9gf;\n" % float(M1))
    # C basligi: test vektorleri (ilk 50), beklenen logit ve etiket
    n = 50
    with open(
        os.path.join(HERE, "test_vektor.h"), "w", encoding="utf-8"
    ) as f:
        f.write(
            "/* otomatik uretildi: gen_mcu.py */\n#define N_TEST 50\n"
        )
        f.write("static const int8_t XT[N_TEST][64] = {\n")
        for r in Xq[:n]:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write(
            "};\nstatic const int32_t YT[N_TEST] = {"
            + ",".join(str(int(v)) for v in yte.numpy()[:n])
            + "};\n"
        )
        f.write("static const int32_t LT[N_TEST][10] = {\n")
        for r in logit[:n]:
            f.write("  {" + ",".join(str(int(v)) for v in r) + "},\n")
        f.write("};\n")
    print("yazildi: model_w.h, test_vektor.h")


if __name__ == "__main__":
    torch.set_num_threads(4)
    main()
