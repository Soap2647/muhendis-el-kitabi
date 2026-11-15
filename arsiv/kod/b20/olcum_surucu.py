# Sanal cagri ve bellek olcumlerini CSV'ye yazar (medyan, 5 tekrar)
import csv, os, statistics, subprocess
KOK = r"D:\Mevcut Projeler\Kitap\engine\veri"
ns = [1 << 14, 1 << 16, 1 << 18, 1 << 20]
satirlar = []
for n in ns:
    sonuc = {}
    for _ in range(5):
        cikti = subprocess.run(
            ["wsl", "bash", "-c",
             "cd /mnt/c/Users/merty/AppData/Local/Temp/b20 && ./sanal_olcum %d" % n],
            capture_output=True, text=True, timeout=110).stdout
        for satir in cikti.splitlines():
            if satir.startswith("#") or satir.count(",") != 2 or "yontem" in satir:
                continue
            yontem, dagitim, ms = satir.split(",")
            sonuc.setdefault((yontem, dagitim), []).append(float(ms))
    for (yontem, dagitim), v in sorted(sonuc.items()):
        satirlar.append([n, yontem, dagitim, "%.4f" % statistics.median(v)])
        print(n, yontem, dagitim, satirlar[-1][3])
with open(os.path.join(KOK, "b20_sanal_olcum.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "yontem", "dagitim", "ms"])
    w.writerows(satirlar)
print("yazildi")
