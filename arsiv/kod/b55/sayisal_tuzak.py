# sayisal_tuzak.py: log(0), softmax taşması ve log-sum-exp.
import math

import numpy as np


def softmax_naif(z):
    e = np.exp(z)                       # büyük z'de taşar
    return e / e.sum()


def lse(z):
    m = max(z)                          # en büyük değeri çıkar
    return m + math.log(sum(math.exp(v - m) for v in z))


if __name__ == "__main__":
    # 1) log(0)
    try:
        math.log(0.0)
    except ValueError as e:
        print("math.log(0.0): ValueError:", e)
    with np.errstate(divide="ignore"):
        print("np.log(0.0)  :", np.log(0.0))

    # 2) Softmax taşması
    try:
        math.exp(1000.0)
    except OverflowError as e:
        print("math.exp(1000): OverflowError:", e)
    z = np.array([1000.0, 999.0, 998.0])
    with np.errstate(over="ignore", invalid="ignore"):
        print("naif softmax :", softmax_naif(z))
    m = z.max()
    kararli = np.exp(z - m) / np.exp(z - m).sum()
    print("kararli      :", np.round(kararli, 6))

    # 3) Çapraz entropi: p_y underflow olunca -log(0)
    zc = [0.0, -800.0]
    y = 1
    with np.errstate(over="ignore", invalid="ignore",
                     divide="ignore"):
        p = np.exp(zc) / np.exp(zc).sum()
    with np.errstate(divide="ignore"):
        print("p (naif)     :", p, " -log p_y =", -np.log(p[y]))
    print("lse tabanli  : L =", lse(zc) - zc[y])
