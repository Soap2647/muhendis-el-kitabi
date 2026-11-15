# -*- coding: utf-8 -*-
"""Kod satırı genişlik denetçisi.

Kod kartındaki satırlar çerçeveye sığmazsa reportlab onları sarmalar ve
dizgi bozulur (devam satırı sola yapışır, satır numarası hizası kayar).
Bu betik, markdown kaynaklarındaki ``` bloklarını tarayıp sınırı aşan
satırları dosya/satır numarasıyla raporlar.

Kullanım:  python build/check_code_width.py [bolumler/bolum_05.md ...]
"""
import sys, glob, os
sys.stdout.reconfigure(encoding="utf-8")

# Ölçüm: içerik genişliği 453.5pt; oluk + dolgular ~48pt; Mono 9.6pt'de
# karakter genişliği 0.602*9.6 = 5.78pt  ->  ~70 karakter sığar.
MAX_KOD = 70      # satır numaralı kod kartı
MAX_TERM = 74     # terminal kutusu (oluk yok, dolgu 11+11)


def check(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    sorunlar = []
    icinde, sinir, blok_basi = False, MAX_KOD, 0
    for no, satir in enumerate(lines, 1):
        s = satir.strip()
        if s.startswith("```"):
            if not icinde:
                icinde = True
                dil = s[3:].strip().lower()
                sinir = MAX_TERM if dil in ("term", "cikti", "output", "console") else MAX_KOD
                blok_basi = no
            else:
                icinde = False
            continue
        if icinde and len(satir) > sinir:
            sorunlar.append((no, len(satir), satir[:56]))
    if sorunlar:
        print("%s — %d uzun satır:" % (os.path.basename(path), len(sorunlar)))
        for no, uz, onizleme in sorunlar:
            print("   satır %4d (%d kr): %s…" % (no, uz, onizleme))
    return sorunlar


if __name__ == "__main__":
    hedefler = sys.argv[1:] or sorted(glob.glob("bolumler/bolum_*.md"))
    toplam = 0
    for p in hedefler:
        toplam += len(check(p))
    print("TOPLAM uzun kod satırı:", toplam)
