import numpy as np

def normalize_et(v):
    v -= v.mean()          # yerinde degistirir
    return v

x = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
dilim = x[1:4]             # gorunum
normalize_et(dilim)
print("dilim sonrasi x:", x)

y = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
kopya = y[[1, 2, 3]]       # gelismis indeks: kopya
normalize_et(kopya)
print("kopya sonrasi y:", y)

def normalize_guvenli(v):
    return v - v.mean()    # yeni dizi uretir

z = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
sonuc = normalize_guvenli(z[1:4])
print("guvenli: z =", z, " sonuc =", np.round(sonuc, 3))
