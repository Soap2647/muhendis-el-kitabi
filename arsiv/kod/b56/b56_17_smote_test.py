import numpy as np
from dengesiz import smote

rng = np.random.default_rng(56)
X = np.vstack([rng.normal(0, 1, (300, 2)),
               rng.normal(2, 0.5, (30, 2))])
y = np.r_[np.zeros(300, int), np.ones(30, int)]
Xs, ys = smote(X, y, np.random.default_rng(1), oran=0.5, k=5)
print("once: poz=%d neg=%d" % ((y == 1).sum(), (y == 0).sum()))
print("sonra: poz=%d neg=%d" % ((ys == 1).sum(), (ys == 0).sum()))

yeni = Xs[len(X):]
poz = X[y == 1]
lo, hi = poz.min(axis=0), poz.max(axis=0)
kutu = ((yeni >= lo - 1e-12) & (yeni <= hi + 1e-12)).all()
print("yeni ornekler azinlik kutusunda mi:", bool(kutu))


def dogrusal_mi(p, poz):
    """p, iki azinlik noktasinin [0,1] karisiminda mi?"""
    for a in poz:
        for b in poz:
            d = b - a
            if np.dot(d, d) == 0:
                continue
            t = np.dot(p - a, d) / np.dot(d, d)
            if 0 <= t <= 1 and np.allclose(a + t * d, p, atol=1e-9):
                return True
    return False


sayi = sum(dogrusal_mi(p, poz) for p in yeni)
print("yeni orneklerden karisim olan:", sayi, "/", len(yeni))
