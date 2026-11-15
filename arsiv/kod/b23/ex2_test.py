import random, sys
from ex2_eski import alarm_karari as eski
from ex2_yeni import alarm_karari as yeni

def deger(rng, lo, hi):
    r = rng.random()
    if r < 0.1:
        return None
    if r < 0.2:
        return rng.uniform(lo - 100, hi + 100)  # sinir disi
    return rng.uniform(lo, hi)

if __name__ == "__main__":
    rng = random.Random(42)
    uyusmayan = 0
    toplam = 0
    for _ in range(20000):
        olcum = None if rng.random() < 0.05 else (
            deger(rng, 300.0, 420.0), deger(rng, 20.0, 80.0))
        son = rng.uniform(0.0, 200.0)
        simdi = rng.uniform(0.0, 300.0)
        toplam += 1
        a = eski(olcum, son, simdi)
        b = yeni(olcum, son, simdi)
        if a != b:
            uyusmayan += 1
            if uyusmayan <= 2:
                print("OLCUM", olcum, "eski", a, "yeni", b)
    print("toplam", toplam, "uyusmayan", uyusmayan)
    sys.exit(0)
