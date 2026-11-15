# kodlama_olcum.py: entropi, Huffman ve aritmetik kodlamanın bit/simge
# karşılaştırması. Üç kaynak: çarpık ikili-üç simge, dört simge,
# kitabın Türkçe harf akışı (bolum_01..46 düz metni).
# Kullanım: python kodlama_olcum.py <bolumler> <veri klasörü>
import csv
import glob
import os
import random
import re
import sys

from aritmetik import Dekodlayici, Kodlayici
from kraft_huffman import entropi, huffman_uzunluk, ortalama
from olcum_metin import ALFA, SON_BOLUM, duz_metin, tr_kucuk

def harf_akisi(kok):
    parcalar = []
    for yol in sorted(glob.glob(os.path.join(kok, "bolum_*.md"))):
        no = int(re.search(r"bolum_(\d+)\.md", yol).group(1))
        if no <= SON_BOLUM:
            with open(yol, encoding="utf-8") as f:
                parcalar.append(f.read())
    metin = duz_metin("\n".join(parcalar))
    return [c for c in tr_kucuk(metin) if c in ALFA]

def olc(ad, frek, mesaj, p):
    # frek: aritmetik kodlayıcının tamsayı frekansları;
    # p: gerçek olasılıklar (Huffman ve entropi için).
    n = len(mesaj)
    bits = Kodlayici(frek).kodla(mesaj)
    geri = Dekodlayici(frek, bits).coz(n)
    assert geri == mesaj, ad
    h = entropi(p)
    hf = ortalama(p, huffman_uzunluk(p))
    ar = len(bits) / n
    print("%-12s n=%-8d H=%.4f Huff=%.4f arit=%.4f" % (
        ad, n, h, hf, ar))
    return [ad, n, "%.4f" % h, "%.4f" % hf, "%.4f" % ar]

def main(kok, veri):
    satirlar = []
    rnd = random.Random(51)
    # 1) Çarpık kaynak: p = [0.9, 0.05, 0.05]
    p = [0.9, 0.05, 0.05]
    frek = [900, 50, 50]
    m = [rnd.choices(range(3), weights=frek)[0] for _ in range(20000)]
    satirlar.append(olc("carpik3", frek, m, p))
    # 2) Dört simge: p = [0.4, 0.3, 0.2, 0.1]
    p = [0.4, 0.3, 0.2, 0.1]
    frek = [40, 30, 20, 10]
    m = [rnd.choices(range(4), weights=frek)[0] for _ in range(20000)]
    satirlar.append(olc("dort simge", frek, m, p))
    # 3) Türkçe harf akışı: frekanslar tamsayıya ölçeklenir
    #    (toplam yaklaşık 2^16)
    harfler = harf_akisi(kok)
    sira = {h: i for i, h in enumerate(ALFA)}
    m = [sira[h] for h in harfler]
    sayi = [0] * len(ALFA)
    for s in m:
        sayi[s] += 1
    n = len(m)
    frek = [max(1, round(c * 65536 / n)) for c in sayi]
    p = [c / n for c in sayi]
    satirlar.append(olc("Turkce harf", frek, m, p))
    with open(os.path.join(veri, "b51_kodlama.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kaynak", "n", "entropi_bit", "huffman_bit",
                    "aritmetik_bit"])
        w.writerows(satirlar)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
