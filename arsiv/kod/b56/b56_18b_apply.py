import time
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle

df, _ = uret(56)
t = temizle(df, kayit_tablosu())[0]
ser = pd.Series(t["sicaklik_c"].fillna(0).values[:50000])


def olc(fn, tekrar=7):
    zaman = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        fn()
        zaman.append(time.perf_counter() - t0)
    return float(np.median(zaman))


print("apply ile vektorlestirme (5 * 10^4 satir):")
a = olc(lambda: ser.apply(lambda v: 2 * v + 1))
b = olc(lambda: 2 * ser + 1)
print("apply: %.4f s  vektor: %.6f s  oran: %.0f"
      % (a, b, a / b))
