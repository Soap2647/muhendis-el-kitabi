# -*- coding: utf-8 -*-
"""Deney 11: izgara arama vs rastgele arama (Bergstra-Bengio 2012,
genel bilgi). Once 7 (lr) x 6 (dropout) = 42 yapilandirma, her biri
2 tohumla, 15 epoch; dogrulama skoru kaydedilir. Arama simulasyonu
bu onceden hesaplanmis tablo uzerinde yapilir:
  - izgara: lr 3 noktada x dropout 3 noktada = 9 yapilandirma
  - rastgele: 9 yapilandirma, tablodan tekrarsiz rastgele
Her arama 300 kez tekrarlanir; secilen (dogrulamada en iyi)
yapilandirmanin
TEST skoru raporlanir. Test skoru secimde KULLANILMAZ."""

import itertools
import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import veri, mlp, egit, csv_yaz

D = veri()
LR = [10**e for e in np.linspace(-4, -1, 7)]
DO = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
SEEDS2 = [20, 21]

tablo = {}
satir = []
for lr, do in itertools.product(range(7), range(6)):
    va, te = [], []
    for s in SEEDS2:
        torch.manual_seed(s)
        m = mlp(gizli=128, dropout=DO[do])
        opt = torch.optim.Adam(m.parameters(), lr=LR[lr])
        h = egit(m, opt, D, epochs=15, batch=32, seed=s)
        va.append(h["val_acc"])
        te.append(h["test_acc"])
    tablo[(lr, do)] = (np.mean(va), np.mean(te))
    satir.append(
        (LR[lr], DO[do], "%.4f" % np.mean(va), "%.4f" % np.mean(te))
    )
    print(
        "lr=%.1e dropout=%.1f  val=%.4f test=%.4f"
        % (LR[lr], DO[do], np.mean(va), np.mean(te))
    )
csv_yaz(
    "b64_arama_tablo.csv", satir, ["lr", "dropout", "val", "test"]
)

rng = np.random.default_rng(64)
izgara = [(a, b) for a in (0, 3, 6) for b in (0, 2, 5)]
kumeler = list(tablo.keys())


def sec(konf):
    return max(konf, key=lambda k: tablo[k][0])


rs = []
for _ in range(300):
    idx = rng.choice(len(kumeler), size=9, replace=False)
    rs.append(tablo[sec([kumeler[i] for i in idx])][1])
ig_all = [tablo[sec(izgara)][1]]
en_iyi_test = max(t for _, t in tablo.values())
print(
    "\nTum tablonun en iyi TEST skoru (referans): %.4f" % en_iyi_test
)
print("Izgara (9 yapilandirma)  secilen test = %.4f" % ig_all[0])
print(
    "Rastgele (9, 300 tekrar) secilen test ort = %.4f" % np.mean(rs)
)
print(
    "  sd = %.4f, en kotu = %.4f" % (np.std(rs, ddof=1), np.min(rs))
)
lr_etki = np.ptp([tablo[(a, 0)][0] for a in range(7)])
do_etki = np.ptp([tablo[(3, b)][0] for b in range(6)])
print(
    "Dogrulama skor araligi: lr boyunca=%.4f, dropout boyunca=%.4f"
    % (lr_etki, do_etki)
)
