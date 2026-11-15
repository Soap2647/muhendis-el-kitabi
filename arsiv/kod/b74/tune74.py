# -*- coding: utf-8 -*-
"""Bolum 74 - DQN ayar denemesi (ayar tohumlari 10 ve 11).

Kullanim: python tune74.py '{"LR": 0.0005, "HEDEF_GUNCELLE": 250}'
Degerlendirme tohumlari (0-4) bu betikte kullanilmaz.
"""

import json
import sys

import dqn74

cfg = json.loads(sys.argv[1])
for k, v in cfg.items():
    setattr(dqn74, k, v)
son, enb = [], []
for t in (10, 11):
    r = dqn74.calistir(("tam", t))
    son.append(round(r["son"]))
    enb.append(round(max(g for _, g in r["egri"])))
for k, v in cfg.items():
    print("  %s = %s" % (k, v))
print("  son (tohum 10, 11) =", son)
print("  en yuksek (tohum 10, 11) =", enb)
