import numpy as np

# Model her ucusa bir ariza olasiligi p veriyor (kalibre varsayiyoruz)
p = np.array([0.01, 0.03, 0.30, 0.60, 0.04, 0.02])
y = np.array([0, 1, 0, 1, 0, 1])       # gercekte ariza (1) oldu mu
c_fn, c_fp = 50, 1          # kacirilan ariza, gereksiz bakim

def maliyet(t):
    karar = (p >= t).astype(int)
    fn = np.sum((karar == 0) & (y == 1))
    fp = np.sum((karar == 1) & (y == 0))
    return fn * c_fn + fp * c_fp, karar

print("ucus    p     y   karar(0.5)  karar(1/51)")
_, k1 = maliyet(0.5)
_, k2 = maliyet(1 / 51)
for i in range(len(p)):
    print("%4d  %5.2f  %3d   %9d   %10d"
          % (i + 1, p[i], y[i], k1[i], k2[i]))
print("toplam maliyet, t=0.5:   ", maliyet(0.5)[0])
print("toplam maliyet, t=1/51:  ", maliyet(1 / 51)[0])

# Tum esikleri tara: en dusuk maliyet nerede?
adaylar = np.unique(np.concatenate([p, [0.0, 1.0]]))
en = min(adaylar, key=lambda t: maliyet(t)[0])
print("en iyi esik (tarama):", round(en, 4),
      " maliyet:", maliyet(en)[0])
