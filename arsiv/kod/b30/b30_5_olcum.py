# -*- coding: utf-8 -*-
"""b30_5_olcum.py: DNS ve HTTP gecikme olcumleri.

Uretir: engine/veri/b30_dns.csv     (ham UDP DNS sorgu suresi)
        engine/veri/b30_bilesen.csv (WSL curl -w zamanlamasi)
Kullanim: python b30_5_olcum.py
"""
import csv
import os
import random
import socket
import statistics
import subprocess
import time
from b30_1_dns_ham import sorgu_kur, yanit_ayristir

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
random.seed(30)


def dns_suresi(sunucu, ad, n):
    sonuc = []
    for _ in range(n):
        q = sorgu_kur(ad, 1, kimlik=random.randint(0, 0xFFFF))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        t0 = time.perf_counter()
        s.sendto(q, (sunucu, 53))
        y, _ = s.recvfrom(4096)
        sonuc.append((time.perf_counter() - t0) * 1000)
        s.close()
        assert yanit_ayristir(y)["rcode"] == 0
    return sonuc


def curl_bilesen(url, n):
    satirlar = []
    bicim = ("%{time_namelookup} %{time_connect} "
             "%{time_appconnect} %{time_starttransfer} "
             "%{time_total}")
    for _ in range(n):
        cmd = ["wsl", "curl", "-s", "-o", "/dev/null", "-w",
               bicim, url]
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=30).stdout.split()
        dns, tcp, tls, ttfb, top = (float(x) for x in out)
        satirlar.append((dns, tcp - dns, tls - tcp, ttfb - tls, top))
    return satirlar


if __name__ == "__main__":
    with open(os.path.join(VERI, "b30_dns.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sunucu", "deneme", "sure_ms"])
        for sunucu in ["1.1.1.1", "8.8.8.8"]:
            olcum = dns_suresi(sunucu, "example.com", 20)
            for i, v in enumerate(olcum, 1):
                w.writerow([sunucu, i, "%.2f" % v])
            print("%-8s medyan=%.2f ms  min=%.2f  maks=%.2f" % (
                sunucu, statistics.median(olcum), min(olcum),
                max(olcum)))
    bilesen = curl_bilesen("https://example.com/", 10)
    with open(os.path.join(VERI, "b30_bilesen.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["deneme", "dns_s", "tcp_s", "tls_s",
                    "ttfb_s", "toplam_s"])
        for i, row in enumerate(bilesen, 1):
            w.writerow([i] + ["%.4f" % x for x in row])
    for k, ad in enumerate(["dns", "tcp", "tls", "ttfb", "toplam"]):
        print("%-7s medyan=%.4f s" % (
            ad, statistics.median(r[k] for r in bilesen)))
