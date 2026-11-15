# -*- coding: utf-8 -*-
# Ogrenme orani, zikzak ve optimizer karsilastirmasi (sabit tohum yok:
# deterministik yontemler).
import csv
import numpy as np
from b50_core import (kuad, kuad_g, kot, kot_g, rosen, rosen_g, gd,
                      momentum, nesterov, adagrad, rmsprop, adam)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"
np.seterr(all="ignore")


def kalici(fk, esik=1e-6):
    """Esigin altina inip kalan ilk adim; yoksa None."""
    kotu = np.where(np.asarray(fk) >= esik)[0]
    if len(kotu) == 0:
        return 0
    if kotu[-1] == len(fk) - 1:
        return None
    return int(kotu[-1]) + 1


# 2) Zikzak: kot (kappa=100). GD eta=0.0099 ~ 2/(lmin+lmax); momentum
N = 1200
y_gd = gd(kot_g, [1.0, 1.0], 0.0099, N)
y_mo = momentum(kot_g, [1.0, 1.0], 0.0165, N, beta=0.67)
for ad, y in (("GD", y_gd), ("Momentum", y_mo)):
    fk = np.array([kot(x) for x in y])
    adim = kalici(fk, 1e-8)
    print("%-9s adim(f<1e-8)=%s  f(100)=%.3e" % (ad, adim, fk[100]))
with open(VERI + "b50_zikzak.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["yontem", "adim", "x", "y"])
    for ad, y in (("GD", y_gd), ("Momentum", y_mo)):
        for k, p in enumerate(y[:150]):
            w.writerow([ad, k, "%.6f" % p[0], "%.6f" % p[1]])

# 3) Rosenbrock ve kot: her yontem icin eta izgarasi (oracle ayari)
izgara = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1]
yontemler = {
    "GD": lambda g, x0, e, n: gd(g, x0, e, n),
    "Momentum": lambda g, x0, e, n: momentum(g, x0, e, n, 0.9),
    "Nesterov": lambda g, x0, e, n: nesterov(g, x0, e, n, 0.9),
    "AdaGrad": lambda g, x0, e, n: adagrad(g, x0, e, n),
    "RMSProp": lambda g, x0, e, n: rmsprop(g, x0, e, n),
    "Adam": lambda g, x0, e, n: adam(g, x0, e, n),
}
N = 20000
sonuc = {}
for pad, f, g, x0 in (("Rosenbrock", rosen, rosen_g, [-1.2, 1.0]),
                      ("kot", kot, kot_g, [1.0, 1.0])):
    print("\n==", pad, "(x0 =", x0, ", N =", N, ")")
    print("yontem    eta     f(sonuc)      adim(f<1e-6)")
    for ad, fn in yontemler.items():
        en = None
        for e in izgara:
            y = fn(g, x0, e, N)
            fk = np.array([f(x) for x in y])
            if not np.all(np.isfinite(fk)):
                continue
            a = kalici(fk)
            skor = (a if a is not None else 10 ** 9, fk[-1])
            if en is None or skor < en[0]:
                en = (skor, e, fk[-1], y, fk, a)
        skor, e, son, y, fk, adim = en
        print("%-9s %-6.0e %-13.3e %s" % (ad, e, son, adim))
        sonuc[(pad, ad)] = (e, y, fk)

# yorunge ve kayip-adim verisi
with open(VERI + "b50_optimizer_yorunge.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["problem", "yontem", "adim", "x", "y"])
    for (pad, ad), (e, y, fk) in sonuc.items():
        lim = 3000 if pad == "Rosenbrock" else 60
        for k, p in enumerate(y[:lim]):
            if k % 3 == 0 or k < 60:
                w.writerow([pad, ad, k, "%.6f" % p[0], "%.6f" % p[1]])
with open(VERI + "b50_kayip_adim.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["problem", "yontem", "adim", "f"])
    for (pad, ad), (e, y, fk) in sonuc.items():
        for k in range(0, len(fk), 50):
            w.writerow([pad, ad, k, "%.6e" % fk[k]])

