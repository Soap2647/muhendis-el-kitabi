# -*- coding: utf-8 -*-
"""Deney 6: test kumesinde secim (secici raporlama).

Havuzdan (Deney 1, tohum 0..199) iki kume alinir:
  - Secim kumesi: tohum 0..99, 20 "konfigurasyon" x 5 tohum.
  - Taze kume:    tohum 100..199, ayni 20 gruba karsilik gelen 5'erli.
Hepsi AYNI yontem: 20 konfigurasyon arasinda gercek fark yok.

(a) Test ortalamasina gore en iyisi secilip "raporlanirsa" ne olur?
(b) Ayni grubun taze tohumlardaki testi ne veriyor?
(c) Dogrulamaya gore secilen grubun testi ne veriyor?
"""
import os
import numpy as np
from ortak79 import csv_yaz, VERI

pool = np.genfromtxt(os.path.join(VERI, "b79_tohum_havuz.csv"),
                     delimiter=",", skip_header=1)
tohum, dog, te = pool[:, 0], pool[:, 1], pool[:, 2]

K = 20
grup = lambda lo, x: np.array([x[lo + 5 * k: lo + 5 * k + 5].mean()
                               for k in range(K)])
te_sec = grup(0, te)          # secim kumesi test ortalamalari
dog_sec = grup(0, dog)        # secim kumesi dogrulama ortalamalari
te_taze = grup(100, te)       # taze tohumlardaki test ortalamalari

k_te = int(np.argmax(te_sec))
k_dog = int(np.argmax(dog_sec))
print("20 konfigurasyon, gercek fark yok")
print("(a) test'e gore secilen: secim-test = %.4f" % te_sec[k_te])
print("    ayni grubun taze tohum testi    = %.4f" % te_taze[k_te])
print("(c) dogrulamaya gore secilen: taze test = %.4f"
      % te_taze[k_dog])
print("tum 20 grup, taze test ort = %.4f  (dogru tahmin)"
      % te_taze.mean())
print("secim kumesinde max-ort fark = %+.4f"
      % (te_sec[k_te] - te_sec.mean()))
csv_yaz("b79_secim.csv",
        [("test_secimi", "%.4f" % te_sec[k_te],
          "%.4f" % te_taze[k_te]),
         ("dogrulama_secimi", "%.4f" % te_sec[k_dog],
          "%.4f" % te_taze[k_dog]),
         ("tum_gruplar_ort", "%.4f" % te_sec.mean(),
          "%.4f" % te_taze.mean())],
        ["secim_olcutu", "secim_kumesi_test", "taze_test"])
