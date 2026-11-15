# gil_olcum.py: CPU-bağlı ve G/Ç-bağlı (simüle) işlerde
# thread ve process karşılaştırması.
# Python 3.12 (CPython, GIL'li). Çalıştırma: python gil_olcum.py
# Çıktı: engine\veri\b26_gil.csv (senaryo, tekrar, sure_s)
import csv
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def cpu_is(n):
    """Saf Python döngüsü: GIL'i tutar, CPU'yu tek başına kullanır."""
    s = 0
    for i in range(n):
        s += (i * i) % 7
    return s


def io_is(saniye):
    """G/Ç beklemesi taklidi: time.sleep GIL'i bırakır."""
    time.sleep(saniye)
    return saniye


def sure_olc(fn, argumanlar, havuz_sinifi, isci):
    if havuz_sinifi is None:              # sıralı referans
        t0 = time.perf_counter()
        for a in argumanlar:
            fn(a)
        return time.perf_counter() - t0
    with havuz_sinifi(max_workers=isci) as ex:
        list(ex.map(fn, [argumanlar[0]] * isci))  # süreçleri başlat
        t0 = time.perf_counter()
        list(ex.map(fn, argumanlar))
        return time.perf_counter() - t0


def main():
    rnd = random.Random(26)
    cpu_args = [rnd.randint(3_000_000, 5_000_000) for _ in range(8)]
    io_args = [0.2] * 8
    print("mantıksal çekirdek:", os.cpu_count(), "| Python:",
          sys.version.split()[0])
    senaryolar = [
        ("cpu_sirali", cpu_is, cpu_args, None, 1),
        ("cpu_thread4", cpu_is, cpu_args, ThreadPoolExecutor, 4),
        ("cpu_process4", cpu_is, cpu_args, ProcessPoolExecutor, 4),
        ("io_sirali", io_is, io_args, None, 1),
        ("io_thread8", io_is, io_args, ThreadPoolExecutor, 8),
        ("io_process8", io_is, io_args, ProcessPoolExecutor, 8),
    ]
    satirlar = []
    for tekrar in range(1, 4):
        for ad, fn, args, havuz, isci in senaryolar:
            s = sure_olc(fn, args, havuz, isci)
            satirlar.append({"senaryo": ad, "tekrar": tekrar,
                             "sure_s": round(s, 3)})
            print("%-14s tekrar=%d  %.3f s" % (ad, tekrar, s))
    yol = r"D:\Mevcut Projeler\Kitap\engine\veri\b26_gil.csv"
    with open(yol, "w", newline="", encoding="utf-8") as f:
        alanlar = ["senaryo", "tekrar", "sure_s"]
        w = csv.DictWriter(f, fieldnames=alanlar)
        w.writeheader()
        w.writerows(satirlar)
    print("CSV:", yol)


if __name__ == "__main__":
    main()
