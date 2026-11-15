# -*- coding: utf-8 -*-
"""
Şekil/tablo CSV'leri: ince ayar özeti (3 tohum) ve ölçekleme
noktaları.
"""

import csv, json, os, re, statistics as st
from collections import defaultdict

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
rows = [
    json.loads(l)
    for l in open(
        os.path.join(K, "sonuc_ince_ayar.jsonl"), encoding="utf-8"
    )
]
g = defaultdict(list)
for r in rows:
    g[(r["mod"], r["r"])].append(r)
sira = [
    ("sifirdan", 0),
    ("tam", 0),
    ("dogrusal", 0),
    ("lora", 1),
    ("lora", 2),
    ("lora", 4),
    ("lora", 8),
    ("lora", 16),
]
with open(
    os.path.join(VERI, "b70_ince_ayar.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(
        [
            "yontem",
            "r",
            "egitilebilir",
            "toplam",
            "test_acc_ort",
            "test_acc_sd",
            "test_f1_ort",
            "lm_once",
            "lm_sonra_ort",
            "lm_adaptor_kapali",
        ]
    )
    for k in sira:
        v = g[k]
        ta = [x["test_acc"] for x in v]
        lm_s = [x["lm_ppl_sonra"] for x in v]
        lm_k = [x["lm_ppl_adaptor_kapali"] for x in v]
        cw.writerow(
            [
                k[0],
                k[1],
                v[0]["egitilebilir"],
                v[0]["toplam"],
                round(st.mean(ta), 4),
                round(st.stdev(ta), 4),
                round(st.mean(x["test_f1"] for x in v), 4),
                v[0]["lm_ppl_once"] if k[0] != "sifirdan" else "",
                round(st.mean(lm_s), 3) if k[0] != "sifirdan" else "",
                round(st.mean(lm_k), 3) if k[0] == "lora" else "",
            ]
        )
print("ince ayar CSV yazildi")
# Ölçekleme: ad, parametre, veri (token), en iyi doğrulama ppl, test
# ppl
adlar = [
    ("olcek_d64", "d=64,L=2"),
    ("ana", "d=128,L=4 (ana)"),
    ("olcek_d192", "d=192,L=6"),
    ("olcek_f125", "veri %12.5"),
    ("olcek_f25", "veri %25"),
    ("olcek_f50", "veri %50"),
]
with open(
    os.path.join(VERI, "b70_olcek.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(
        [
            "ad",
            "parametre",
            "egitim_token",
            "dogrulama_ppl",
            "test_ppl",
        ]
    )
    for tag, ad in adlar:
        fn = os.path.join(K, "egri_%s_0.csv" % tag)
        s = open(
            os.path.join(
                K,
                (
                    "out_%s.txt" % tag
                    if tag != "ana"
                    else "out_ana_0.txt"
                ),
            ),
            encoding="utf-8",
        ).read()
        m = re.search(
            r"parametre=(\d+).*?doğrulama ppl=([\d.]+)\s+test "
            r"ppl=([\d.]+)",
            s,
        )
        frac = 1.0
        if "f125" in tag:
            frac = 0.125
        if "f25" in tag:
            frac = 0.25
        if "f50" in tag:
            frac = 0.5
        cw.writerow(
            [
                ad,
                m.group(1),
                int(int(frac * (782840 // 129)) * 129),
                m.group(2),
                m.group(3),
            ]
        )
        print(ad, m.groups())
