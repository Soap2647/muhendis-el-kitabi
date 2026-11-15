# -*- coding: utf-8 -*-
"""Bolum 24 deneylerini derler, calistirir ve engine/veri CSV'lerini yazar.

Calisma ortami: WSL2 (Ubuntu 24.04), gcc 13.3, AMD Ryzen 7 6800H.
Her ikili taskset ile tek bir CPU cekirdegine sabitlenir.
"""
import csv
import os
import subprocess

KLASOR = "/mnt/c/Users/merty/AppData/Local/Temp/b24"
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
CPU = "3"


def wsl(komut):
    r = subprocess.run(["wsl", "bash", "-lc",
                        "cd %s && %s" % (KLASOR, komut)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("HATA: %s\n%s" % (komut, r.stderr))
    return r.stdout


def satirlar(metin):
    return [s.split(",") for s in metin.strip().splitlines() if s]


def derle():
    wsl("gcc -O2 -Wall -Wextra -std=c11 -fno-if-conversion "
        "-fno-if-conversion2 -fno-tree-vectorize dal.c -o dal_kontrollu")
    wsl("gcc -O2 -Wall -Wextra -std=c11 dal.c -o dal_dogal")
    wsl("gcc -O2 -Wall -Wextra -std=c11 -fno-tree-vectorize "
        "-fno-tree-slp-vectorize ilp.c -o ilp")
    wsl("gcc -O2 -Wall -Wextra -std=c11 cpu_sayac.c -o cpu_sayac")
    wsl("gcc -O2 -Wall -Wextra -std=c11 abi.c -o abi")
    wsl("gcc -O2 -Wall -Wextra -std=c11 -fno-stack-protector "
        "-fno-asynchronous-unwind-tables kirmizi.c -c -o kirmizi.o")
    for etiket, bayrak in (("", ""),
                           ("_hiz", "-falign-functions=64 -falign-loops=64")):
        wsl("gcc -O2 %s -Wall -Wextra -std=c11 -fno-tree-vectorize "
            "-c axpy_skaler.c -o axpy_skaler%s.o" % (bayrak, etiket))
        wsl("gcc -O3 %s -std=c11 -c simd.c -o simd3%s.o" % (bayrak, etiket))
        wsl("gcc -O2 %s -std=c11 -fno-tree-vectorize -c simd.c "
            "-o simd2%s.o" % (bayrak, etiket))
        wsl("gcc -O3 %s -std=c11 simd3%s.o axpy_skaler%s.o -o simd_o3%s"
            % (bayrak, etiket, etiket, etiket))
        wsl("gcc -O2 %s -std=c11 simd2%s.o axpy_skaler%s.o -o simd_o2%s"
            % (bayrak, etiket, etiket, etiket))
    print("derleme tamam")


def kos(komut, kez):
    out = []
    for _ in range(kez):
        out.append(wsl("taskset -c %s %s" % (CPU, komut)))
    return out


def dal():
    rows = [["derleme", "kosu", "fonksiyon", "dizi", "en_az_ms",
             "medyan_ms", "ns_per_eleman", "toplam"]]
    for ad, etiket in (("dal_kontrollu", "kontrollu"), ("dal_dogal", "dogal")):
        for kosu, cikti in enumerate(kos("./%s %s" % (ad, etiket), 2), 1):
            for r in satirlar(cikti)[1:]:
                rows.append([etiket, str(kosu)] + r[1:])
    yaz("b24_dal_olcum.csv", rows)


def ilp():
    rows = [["derleme", "kosu", "fonksiyon", "akumulator", "en_az_ms",
             "medyan_ms", "ns_per_eleman"]]
    for kosu, cikti in enumerate(kos("./ilp kontrollu", 2), 1):
        for r in satirlar(cikti)[1:]:
            rows.append(["kontrollu", str(kosu)] + r[1:])
    yaz("b24_ilp_olcum.csv", rows)


def simd():
    rows = [["hizalama", "tur", "derleme", "surum", "en_az_ms",
             "ns_per_eleman"]]
    for hiza, etiket in (("hayir", ""), ("evet", "_hiz")):
        for tur in range(1, 6):
            for d in ("o3", "o2"):
                cikti = wsl("taskset -c %s ./simd_%s%s %s"
                            % (CPU, d, etiket, d))
                for r in satirlar(cikti)[1:]:
                    if r[1] == "atlandi":
                        continue
                    rows.append([hiza, str(tur), r[0], r[1], r[2], r[3]])
    yaz("b24_simd_olcum.csv", rows)


def cpu():
    rows = [["kosu", "olcum", "deger"]]
    for kosu in (1, 2):
        cikti = wsl("taskset -c %s ./cpu_sayac" % CPU)
        for r in satirlar(cikti)[1:]:
            rows.append([str(kosu), r[0], r[1]])
    yaz("b24_cpu_olcum.csv", rows)


def yaz(ad, rows):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)
    print(yol, len(rows) - 1, "satir")


if __name__ == "__main__":
    derle()
    dal()
    ilp()
    simd()
    cpu()
