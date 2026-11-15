# -*- coding: utf-8 -*-
"""Rastgele (seed=37) ileri atlamalı IR: optimizasyon anlamı korur.

Döngü yok (atlamalar yalnız ileriye): her program sonlanir.
"""
import random
from ir_opt import ayristir, optimize, calistir

DEGISKEN = ["x", "y", "z", "t1", "t2"]


def uret(rng, parca=4, uzunluk=4):
    satir = ["x = 1", "y = 2", "z = 3", "t1 = 0", "t2 = 0"]  # ilk
    def deger():
        return rng.choice(DEGISKEN + ["a", str(rng.randint(-3, 5))])
    for k in range(parca):
        for _ in range(rng.randint(1, uzunluk)):
            r = rng.random()
            if r < 0.4:
                satir.append(f"{rng.choice(DEGISKEN)} = {deger()}")
            elif r < 0.6:
                satir.append(f"{rng.choice(DEGISKEN)} = {deger()} "
                             f"{rng.choice('+-*')} {deger()}")
            elif r < 0.7:
                satir.append(f"print {deger()}")
            elif r < 0.85:    # yalnız ileri atlama
                satir.append(f"if_false {deger()} goto "
                             f"L{rng.randint(k, parca - 1)}")
            else:
                satir.append(f"goto L{rng.randint(k, parca - 1)}")
        satir.append(f"L{k}:")
    satir.append("print x")
    return "\n".join(satir)


def main(n=2000):
    rng = random.Random(37)
    for _ in range(n):
        src = uret(rng)
        girdi = {"a": rng.randint(-4, 4)}
        prog = ayristir(src)
        opt = optimize(prog)
        c1, _ = calistir(prog, girdi)
        c2, _ = calistir(opt, girdi)
        assert c1 == c2, (src, c1, c2)
    return n


if __name__ == "__main__":
    print(main(), "rastgele IR programi: önce = sonra (seed=37)")
