# kosul.py: kosul sayisi, Hilbert matrisi ve kayip basamaklar
import numpy as np


def hilbert(n):
    i = np.arange(n)
    return 1.0 / (i[:, None] + i[None, :] + 1)


print(" n     kappa(H)   kayip_bas.  hata(solve)   hata(inv)")
for n in range(2, 13, 2):
    H = hilbert(n)
    x_gercek = np.ones(n)
    b = H @ x_gercek
    x1 = np.linalg.solve(H, b)
    x2 = np.linalg.inv(H) @ b
    kappa = np.linalg.cond(H)
    e1 = np.max(np.abs(x1 - x_gercek))
    e2 = np.max(np.abs(x2 - x_gercek))
    kayip = np.log10(kappa)
    print("%2d  %10.2e  %8.2f  %11.2e  %11.2e"
          % (n, kappa, kayip, e1, e2))
