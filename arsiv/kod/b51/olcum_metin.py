# olcum_metin.py: kitabın bölüm metinlerinde harf ve bayt entropisi;
# 0., 1., 2. dereceden (koşullu) entropi karşılaştırması.
# Kullanım: python olcum_metin.py <bolumler klasörü> <veri klasörü>
import csv
import glob
import hashlib
import math
import os
import re
import sys
from collections import Counter

ALFA = "abcçdefgğhıijklmnoöprsştuüvyz"   # 29 Türkçe harf
SON_BOLUM = 46                           # ölçüm 1..46 üzerinde

def tr_kucuk(s):
    # Türkçe büyük/küçük harf: I -> ı, İ -> i
    # (Python'un varsayılanı yanlış)
    return s.replace("I", "ı").replace("İ", "i").lower()

def duz_metin(md):
    # Kod bloklarını, tabloları, şekil satırlarını, kutu işaretlerini
    # at.
    cikti, kodda = [], False
    for satir in md.splitlines():
        if satir.startswith("```"):
            kodda = not kodda
            continue
        if kodda or satir.startswith(("|", "![", "%%", ":::")):
            continue
        cikti.append(satir)
    return "\n".join(cikti)

def entropi_sayim(sayac):
    # Ölçülen (plug-in) entropi: H = -sum (c/n) log2 (c/n)
    n = sum(sayac.values())
    return -sum(c / n * math.log2(c / n) for c in sayac.values())

def kosullu(dizi, k):
    # H(X_k | X_1..X_{k-1}) = H(k-gram) - H((k-1)-gram)
    if k == 1:
        return entropi_sayim(Counter(dizi))
    n = len(dizi) - k + 1
    kgram = Counter(tuple(dizi[i:i + k]) for i in range(n))
    onceki = Counter(tuple(dizi[i:i + k - 1])
                     for i in range(len(dizi) - k + 1))
    return entropi_sayim(kgram) - entropi_sayim(onceki)

def main(kok, veri):
    dosyalar = []
    for yol in sorted(glob.glob(os.path.join(kok, "bolum_*.md"))):
        no = int(re.search(r"bolum_(\d+)\.md", yol).group(1))
        if no <= SON_BOLUM:
            dosyalar.append(yol)
    ham = b""
    for yol in dosyalar:
        with open(yol, "rb") as f:
            ham += f.read()
    print("dosya sayisi:", len(dosyalar))
    ozet = hashlib.sha256(ham).hexdigest()[:16]
    print("corpus sha256:", ozet, "...")
    metin = duz_metin("\n".join(open(y, encoding="utf-8").read()
                                for y in dosyalar))
    harf = [c for c in tr_kucuk(metin) if c in ALFA]
    print("harf sayisi:", len(harf), " farkli harf:", len(set(harf)))
    print("ust sinir log2(29) = %.4f" % math.log2(29))
    olc = [("harf", "H0 (bagimsiz)", kosullu(harf, 1)),
           ("harf", "H(X2|X1)", kosullu(harf, 2)),
           ("harf", "H(X3|X1X2)", kosullu(harf, 3))]
    bayt = list(metin.encode("utf-8"))
    olc += [("bayt", "H0 (bagimsiz)", kosullu(bayt, 1)),
            ("bayt", "H(X2|X1)", kosullu(bayt, 2))]
    print("%-6s %-14s %s" % ("alfabe", "model", "bit/simge"))
    for a, m, h in olc:
        print("%-6s %-14s %.4f" % (a, m, h))
    print("duz metin bayt: %d, bayt/harf: %.3f"
          % (len(bayt), len(bayt) / len(harf)))
    # CSV 1: harf sıklıkları (şekil 51.x için)
    n = len(harf)
    sayac = Counter(harf)
    yol = os.path.join(veri, "b51_harf.csv")
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["harf", "sayi", "olasilik", "ozbilgi_bit"])
        for h in ALFA:
            c = sayac.get(h, 0)
            w.writerow([h, c, "%.6f" % (c / n),
                        "%.4f" % (-math.log2(c / n))])
    # CSV 2: entropi düzeyleri
    with open(os.path.join(veri, "b51_metin_entropi.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alfabe", "model", "bit_per_simge"])
        for a, m, h in olc:
            w.writerow([a, m, "%.4f" % h])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
