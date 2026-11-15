import numpy as np
from sklearn.model_selection import (KFold, StratifiedKFold,
                                     TimeSeriesSplit)

# 1) El ile k-katlı bölme: sıralı bloklar
n, k = 10, 5
idx = np.arange(n)
bloklar = np.array_split(idx, k)
for i, test in enumerate(bloklar):
    egitim = np.setdiff1d(idx, test)
    print("kat %d  test=%s  egitim=%s" % (i, test, egitim))

# 2) sklearn KFold(shuffle=False) ile aynı mı?
for i, (tr, te) in enumerate(KFold(k).split(idx)):
    assert np.array_equal(te, bloklar[i])
print("KFold ile el yapımı bölme birebir aynı.")

# 3) Dengesiz sınıflar: StratifiedKFold, kat başına sayılar
y = np.array([0] * 8 + [1] * 2)
print("\nStratifiedKFold(2) kat başına (sınıf0, sınıf1):")
for tr, te in StratifiedKFold(2).split(np.zeros(10), y):
    sayi = np.bincount(y[te], minlength=2)
    print("  test sınıf sayıları:", sayi)

# 4) Zaman serisi: gelecek testte, geçmiş eğitimde
t = np.arange(12)
print("\nTimeSeriesSplit(3) — 12 zaman adımı:")
for tr, te in TimeSeriesSplit(3).split(t):
    print("  egitim=%s  test=%s" % (tr, te))
