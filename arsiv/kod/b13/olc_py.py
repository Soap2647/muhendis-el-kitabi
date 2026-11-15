# olc_py.py: sorted() icin girdi turune gore en iyi sure
import random
import time


def en_iyi(fonk, tekrar=3):
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fonk()
        en = min(en, time.perf_counter() - t0)
    return en


n = 10 ** 6
random.seed(42)
rast = [random.randrange(10 ** 6) for _ in range(n)]
sirali = sorted(rast)
ters = sirali[::-1]
tekrar = [random.randrange(10) for _ in range(n)]

print(f"n = {n}")
for ad, veri in [("rastgele", rast), ("sirali", sirali),
                 ("ters", ters), ("10 deger", tekrar)]:
    s = en_iyi(lambda: sorted(veri))
    print(f"{ad:<10} {s * 1000:9.2f} ms")

kayitlar = [("Ali", 3), ("Ayse", 1), ("Mert", 3), ("Zeynep", 1)]
print(sorted(kayitlar, key=lambda k: k[1]))
