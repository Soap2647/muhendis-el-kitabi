"""Dört test paketinin mutasyon skorunu CSV'ye yazar (Bölüm 39)."""
import csv
import os
import sys

from mutasyon import calistir

KOK = os.path.dirname(os.path.abspath(__file__))
CIKTI = sys.argv[1]
PAKETLER = [("zayif", "mutasyon/test_zayif.py"),
            ("orta", "mutasyon/test_orta.py"),
            ("guclu_v1", "mutasyon/test_guclu_v1.py"),
            ("guclu_v2", "mutasyon/test_guclu_v2.py")]

satirlar = []
for ad, yol in PAKETLER:
    sonuc = calistir(os.path.join(KOK, "tarih.py"),
                     os.path.join(KOK, yol))
    toplam = len(sonuc)
    olen = sum(1 for _, o in sonuc if o)
    skor = 100.0 * olen / toplam
    satirlar.append([ad, toplam, olen, "%.1f" % skor])
    print(ad, toplam, olen, "%.1f" % skor, flush=True)

with open(CIKTI, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["paket", "mutant", "oldurulen", "skor_yuzde"])
    w.writerows(satirlar)
print("yazıldı:", CIKTI)
