# Sanal cagri olcumunu 5 kez tekrarlar, medyani CSV'ye yazar.
# Kullanim (sanal_olcum'un oldugu dizinde, WSL'de): python3 medyan.py
import csv
import statistics
import subprocess

NS = [1 << 14, 1 << 16, 1 << 18, 1 << 20]
satirlar = []
for n in NS:
    veri = {}
    for _ in range(5):
        cikti = subprocess.run(["./sanal_olcum", str(n)],
                               capture_output=True, text=True).stdout
        for satir in cikti.splitlines():
            if satir.count(",") != 2 or satir.startswith("yontem"):
                continue
            yontem, dagitim, ms = satir.split(",")
            veri.setdefault((yontem, dagitim), []).append(float(ms))
    for (yontem, dagitim), v in sorted(veri.items()):
        med = statistics.median(v)
        satirlar.append([n, yontem, dagitim, "%.4f" % med])

with open("sanal_olcum.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "yontem", "dagitim", "ms"])
    w.writerows(satirlar)
print("yazildi:", len(satirlar), "satir")
