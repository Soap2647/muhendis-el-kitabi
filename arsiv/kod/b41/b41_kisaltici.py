# -*- coding: utf-8 -*-
"""Bölüm 41.9 - URL kısaltıcı: ID üretimi ve base62 kodlama.

1) base62 kodlama/çözme (0-9, a-z, A-Z; 62 karakter).
2) Sayaç: uzunluk büyümesi.
3) Kırpılmış hash: doğum günü çakışmaları (tohum 41).
4) Snowflake tarzı üretici: 41 bit zaman | 10 bit makine |
   12 bit sıra.
"""

import hashlib
import random
import threading

ALFABE = (
    "0123456789abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)


#@@
def kodla(n):
    if n == 0:
        return ALFABE[0]
    s = []
    while n > 0:
        n, r = divmod(n, 62)
        s.append(ALFABE[r])
    return "".join(reversed(s))


def coz(s):
    n = 0
    for ch in s:
        n = n * 62 + ALFABE.index(ch)
    return n


#@@
def sayac_uzunlugu():
    print("Sayaç -> kod uzunluğu (base62)")
    for n in (1, 61, 62, 3843, 3844, 10**6, 10**9):
        print(
            "%12d -> %-8s (%d karakter)"
            % (n, kodla(n), len(kodla(n)))
        )
    print(
        "Kontrol: coz(kodla(n)) == n:",
        all(coz(kodla(n)) == n for n in range(100000)),
    )


#@@
def hash_cakisma(n=10**6, bit=32):
    rnd = random.Random(41)
    N = 2**bit
    degerler = set()
    for i in range(n):
        url = "https://ornek.com/s/%d-%d" % (i, rnd.randrange(10**9))
        h = hashlib.sha256(url.encode()).digest()
        degerler.add(int.from_bytes(h[: bit // 8], "big"))
    cakisan = n - len(degerler)
    beklenen = n - N * (1 - (1 - 1 / N) ** n)
    print()
    print("Kırpılmış hash, %d bit, %d URL" % (bit, n))
    print("ölçülen çakışan kayıt : %d" % cakisan)
    print("beklenen (doğum günü) : %.1f" % beklenen)


#@@
class SnowflakeTarzi:
    """Tek makinede sıra + zaman; makineler koordinasyonsuz."""

    ZAMAN_BIT, MAKINE_BIT, SIRA_BIT = 41, 10, 12
    SIRA_MAKS = (1 << 12) - 1

    def __init__(self, makine, saat_ms):
        self.makine = makine & ((1 << 10) - 1)
        self.saat = saat_ms
        self.son = -1
        self.sira = 0
        self.kilit = threading.Lock()

    def al(self):
        with self.kilit:
            ms = self.saat()
            if ms == self.son:
                self.sira = (self.sira + 1) & self.SIRA_MAKS
                if self.sira == 0:
                    raise RuntimeError("bu ms'de sıra taştı")
            else:
                self.sira = 0
            self.son = ms
            return (ms << 22) | (self.makine << 12) | self.sira


#@@
def snowflake_demo():
    print()
    print("Snowflake tarzı üretici (sabit saat, 4 makine)")
    saat = {"ms": 1000}
    makineler = [
        SnowflakeTarzi(m, lambda: saat["ms"]) for m in range(4)
    ]
    idler = set()
    toplam = 0
    for ms in range(1000, 1100):
        saat["ms"] = ms
        for u in makineler:
            for _ in range(250):
                idler.add(u.al())
                toplam += 1
    print("üretilen = %d, tekil = %d" % (toplam, len(idler)))
    ornek = makineler[2]
    saat["ms"] = 5000
    x = ornek.al()
    print("örnek ID : %d" % x)
    print("base62   : %s (%d karakter)" % (kodla(x), len(kodla(x))))
    print("zaman    : %d ms" % (x >> 22))
    print("makine   : %d" % ((x >> 12) & 1023))
    print("sıra     : %d" % (x & 4095))


#@@
if __name__ == "__main__":
    sayac_uzunlugu()
    hash_cakisma()
    snowflake_demo()
