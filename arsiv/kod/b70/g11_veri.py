# -*- coding: utf-8 -*-
"""
Şekiller için CSV'ler: tokenizasyon örneği, GPT eğrileri, n-gram
tabanı.
"""

import csv, json, os, re
import numpy as np
from bpe_sifirdan import BPE

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
bj = json.load(
    open(os.path.join(K, "bpe_b70.json"), encoding="utf-8")
)
b = BPE.yukle(bj["alfabe"], bj["kurallar"])
cumle = "Dil modeli bir sonraki tokeni tahmin eder."
bp = [b.ters[i] for i in b.kodla(cumle)]
with open(
    os.path.join(VERI, "b70_ornek_tokenler.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(["duzey", "parca_sayisi", "parcalar"])
    cw.writerow(["karakter", len(cumle), "|".join(cumle)])
    cw.writerow(
        [
            "sozcuk",
            len(re.findall(r"\w+", cumle)) + 1,
            "|".join(re.findall(r"\w+|[^\w\s]", cumle)),
        ]
    )
    cw.writerow(["alt-sozcuk(BPE)", len(bp), "|".join(bp)])
# GPT eğrileri (üç tohum): adım, eğitim kaybı, doğrulama ppl
rows = []
for s in range(3):
    for r in csv.DictReader(
        open(os.path.join(K, "egri_ana_%d.csv" % s), encoding="utf-8")
    ):
        rows.append(
            [
                s,
                int(r["adim"]),
                round(float(r["egitim_kayip"]), 5),
                round(float(r["dogrulama_ppl"]), 4),
            ]
        )
with open(
    os.path.join(VERI, "b70_gpt_egri.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(["tohum", "adim", "egitim_kayip", "dogrulama_ppl"])
    cw.writerows(rows)
print("egri satir", len(rows))
print(bp)
