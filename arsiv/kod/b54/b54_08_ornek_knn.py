import numpy as np

X = np.array([[1, 1], [2, 1], [1, 2], [2, 3], [3, 1],
              [5, 4], [6, 5], [5, 6], [4, 5], [6, 2]], float)
y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
q = np.array([4.0, 3.0])
k = 3

d2 = ((X - q) ** 2).sum(axis=1)       # kare mesafe (kok gerekmez)
sira = np.argsort(d2, kind="stable")
print(" sira  nokta      d^2  etiket")
for r, i in enumerate(sira, 1):
    print("%5d  (%g,%g)  %5g  %6d"
          % (r, X[i, 0], X[i, 1], d2[i], y[i]))
komsu = sira[:k]
oy = y[komsu].sum()
print("k=%d komsu etiketleri: %s" % (k, y[komsu]))
print("oylama: 1 oy = %d, 0 oy = %d -> tahmin %d"
      % (oy, k - oy, int(oy > k / 2)))
