# -*- coding: utf-8 -*-
"""Bolum 73 - t11: Cozumlu Ornekler'in sayisal dogrulamasi.

(a) Hizalama ve tekduzelik: 4 noktali el ornegi (dagilmis / cokmus).
(b) 3x3 goruntu-metin benzerlik matrisi: simetrik kayip ve sifir atis.
Tum sayilar elle hesaplanabilir; betik bu elle hesaplari dogrular.
"""

import math
import numpy as np


def hizalama(u, v):
    return float(np.mean(np.sum((u - v) ** 2, axis=1)))


def tekduzelik(z, t=2.0):
    n = len(z)
    d2 = np.sum((z[:, None] - z[None]) ** 2, axis=-1)
    iu = np.triu_indices(n, 1)
    return float(np.log(np.mean(np.exp(-t * d2[iu]))))


print("(a) el ornegi, dagilmis kume")
u = np.array([[1.0, 0.0], [0.0, 1.0]])
v = np.array([[0.8, 0.6], [-0.6, 0.8]])
z = np.vstack([u, v])
print("hizalama   = %.4f" % hizalama(u, v))
print("tekduzelik = %.4f" % tekduzelik(z))
d2 = np.sum((z[:, None] - z[None]) ** 2, axis=-1)
print(
    "ikili uzakliklar kare (ust ucgen):",
    np.round(d2[np.triu_indices(4, 1)], 2),
)

print("\n(a') cokmus kume: tum noktalar (1, 0)")
u2 = np.array([[1.0, 0.0], [1.0, 0.0]])
v2 = np.array([[1.0, 0.0], [1.0, 0.0]])
z2 = np.vstack([u2, v2])
print("hizalama   = %.4f" % hizalama(u2, v2))
print("tekduzelik = %.4f" % tekduzelik(z2))

print("\n(b) 3x3 benzerlik matrisi, sicaklik tau = 0.5")
S = np.array([[0.9, 0.1, 0.2], [0.3, 0.7, 0.1], [0.2, 0.7, 0.6]])
L = S / 0.5
print("logit matrisi:")
print(np.round(L, 2))


def ce_satir(M):
    """Her satir icin -log softmax(hedef = kosegen)."""
    out = []
    for i in range(M.shape[0]):
        m = M[i].max()
        lse = m + math.log(np.sum(np.exp(M[i] - m)))
        out.append(lse - M[i, i])
    return np.array(out)


kg = ce_satir(L)
kt = ce_satir(L.T)
print(
    "goruntu->metin kayiplari:",
    np.round(kg, 4),
    "ortalama = %.4f" % kg.mean(),
)
print(
    "metin->goruntu kayiplari:",
    np.round(kt, 4),
    "ortalama = %.4f" % kt.mean(),
)
print("simetrik kayip = %.4f" % ((kg.mean() + kt.mean()) / 2))

print("\nsifir atis: her goruntu icin en yuksek benzerlik")
print("tahmin (goruntu -> sinif):", np.argmax(S, axis=1))
