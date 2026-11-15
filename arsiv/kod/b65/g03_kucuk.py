# g03_kucuk.py: küçük tensörlerde kernel başlatma yükü (CPU vs GPU).
# Çıktı: engine/veri/b65_kucuk.csv
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
satir = []
for n in [1, 64, 1024, 16384, 262144]:
    for ad, d in (("cpu", "cpu"), ("gpu", dev)):
        a = torch.randn(n, device=d)
        b = torch.randn(n, device=d)
        k = 2000 if d == "cpu" else 500
        for _ in range(50):
            c = a + b
        if d != "cpu":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(k):
            c = a + b
        if d != "cpu":
            torch.cuda.synchronize()
        us = (time.perf_counter() - t0) / k * 1e6
        satir.append((n, ad, us))
        print("n=%7d  %s  %8.2f us/işlem" % (n, ad, us))
with open(os.path.join(KOK, "b65_kucuk.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "aygit", "us_islem"])
    for r in satir:
        w.writerow([r[0], r[1], "%.3f" % r[2]])
