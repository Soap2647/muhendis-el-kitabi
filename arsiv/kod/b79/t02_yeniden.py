# -*- coding: utf-8 -*-
"""Deney 2: Bolum 64.4 iddiasinin yeniden uretimi.

Iddia (Bolum 64.4, metinden): "Dogrulamada en yuksek skoru veren
AdamW, testte de Adam'dan biraz yuksek cikti; ama bu fark sapmalar
icinde kaliyor."

Kurulum Bolum 64.4 anlatimindan alindi (piksel olcegi 1/16 icin
Bolum 64 veri tanimi): load_digits, %60/%20/%20 katmanli bolme,
2 gizli katman x 128 ReLU, 30 epoch, batch 32. Ogrenme orani
1e-4 ... 1e-1 izgarasindan, yalnizca dogrulamada (tohum 10,11,12)
secilir. Secilen lr ile test kumesi tohum 0..4'te olculur.
Eslestirilmis fark: ayni tohumda AdamW - Adam.
"""
import numpy as np
from ortak79 import veri, egit, csv_yaz, t_testi, bootstrap_gven

D = veri()
LRS = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
SECIM = [10, 11, 12]
TEST = [0, 1, 2, 3, 4]

AYAR = {
    "Adam": dict(opt="adam", wd=0.0),
    "AdamW": dict(opt="adamw", wd=0.01),
}

secilen = {}
print("Adim 1: lr secimi (yalnizca dogrulama, tohum 10-12)")
for ad, a in AYAR.items():
    skor = {}
    for lr in LRS:
        v = [egit(s, lr=lr, D=D, **a)[0] for s in SECIM]
        skor[lr] = np.mean(v)
        print("  %-6s lr=%-7g dogr=%.4f" % (ad, lr, skor[lr]))
    secilen[ad] = max(skor, key=skor.get)
    print("  secim %-6s lr=%g" % (ad, secilen[ad]))

print("Adim 2: test (tohum 0-4, secilen lr)")
test = {ad: [] for ad in AYAR}
for ad, a in AYAR.items():
    for s in TEST:
        test[ad].append(egit(s, lr=secilen[ad], D=D, **a)[1])
    x = np.array(test[ad])
    print("  %-6s test ort=%.4f sd=%.4f"
          % (ad, x.mean(), x.std(ddof=1)))

fark = np.array(test["AdamW"]) - np.array(test["Adam"])
ort, t, p = t_testi(fark)
gl, gh = bootstrap_gven(fark)
print("fark (AdamW-Adam) ort=%+.4f  t=%.3f  p=%.3f" % (ort, t, p))
print("bootstrap %%95 GA: [%+.4f, %+.4f]" % (gl, gh))

satir = []
for i, s in enumerate(TEST):
    satir.append((s, "%.4f" % test["Adam"][i],
                  "%.4f" % test["AdamW"][i], "%.4f" % fark[i]))
csv_yaz("b79_yeniden.csv", satir,
        ["tohum", "adam_test", "adamw_test", "fark"])
