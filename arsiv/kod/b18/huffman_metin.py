# huffman_metin.py: gercek bir metinde bayt bazli Huffman, entropi ve
# gzip karsilastirmasi. Dosya: bolum_16.md (kitabin bolum 16 metni,
# SHA-256 ozetini cikti basar). Huffman basligi (tablo) maliyeti dahil
# DEGIL; yalnizca veri bitleri sayilir.
import gzip
import hashlib
import math
import sys
import zlib
from collections import Counter
from huffman import huffman_agaci, kodlar

DOSYA = sys.argv[1] if len(sys.argv) > 1 else "bolum_16.md"


def main():
    with open(DOSYA, "rb") as f:
        veri = f.read()
    print("dosya:", DOSYA, "boyut:", len(veri), "bayt")
    print("sha256:", hashlib.sha256(veri).hexdigest()[:16], "...")
    print("zlib surumu:", zlib.ZLIB_RUNTIME_VERSION)
    frekans = Counter(veri)
    toplam = len(veri)
    h = -sum((f / toplam) * math.log2(f / toplam)
             for f in frekans.values())
    agac, _ = huffman_agaci({bytes([b]).hex(): f
                             for b, f in frekans.items()})
    tablo = kodlar(agac)
    bit = sum(f * len(tablo[bytes([b]).hex()])
              for b, f in frekans.items())
    gz = len(gzip.compress(veri, compresslevel=9, mtime=0))
    print("farkli bayt sayisi:", len(frekans))
    print("entropi        : %.4f bit/bayt" % h)
    print("huffman (veri) : %.4f bit/bayt" % (bit / toplam))
    print("gzip -9 (tum)  : %.4f bit/bayt" % (gz * 8 / toplam))
    print("sikistirma: huffman %.1f%%, gzip %.1f%%" % (
        100 * bit / 8 / toplam, 100 * gz / toplam))


if __name__ == "__main__":
    main()
