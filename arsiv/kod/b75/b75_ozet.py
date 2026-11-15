# -*- coding: utf-8 -*-
"""Bolum 75: CSV'lerden ozet tablolar (ortalama +- sapma, 3 tohum)."""
import csv
import statistics as st

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"


def oku(ad):
    with open(VERI + ad, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ozet(satirlar, anahtar, alan):
    for ad in dict.fromkeys(r[anahtar] for r in satirlar):
        d = [float(r[alan]) for r in satirlar if r[anahtar] == ad]
        print("%-24s %.4f +- %.4f  (n=%d)"
              % (ad, st.mean(d), st.pstdev(d), len(d)))


if __name__ == "__main__":
    print("== Damitma (test dogrulugu) ==")
    ozet(oku("b75_damitma.csv"), "yontem", "dogruluk")
    print("== Seyreklik (budama sonrasi / ince ayarli) ==")
    s = oku("b75_seyreklik.csv")
    for o in dict.fromkeys(r["oran"] for r in s):
        b = [float(r["budamasiz"]) for r in s if r["oran"] == o]
        i = [float(r["ince_ayar"]) for r in s if r["oran"] == o]
        print("oran %-5s budamasiz %.4f+-%.4f ince %.4f+-%.4f" % (
            o, st.mean(b), st.pstdev(b), st.mean(i), st.pstdev(i)))
