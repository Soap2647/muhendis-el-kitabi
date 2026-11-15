import math
import numpy as np

M = np.array([[1, 2, 3, 4],
              [5, 6, 7, 8],
              [9, 10, 11, 12]])
print("M.sum(axis=0):", M.sum(axis=0), " sekil:", M.sum(axis=0).shape)
print("M.sum(axis=1):", M.sum(axis=1), " sekil:", M.sum(axis=1).shape)

x = np.array([-2.0, 0.5, 3.0, -1.0, 4.0])
print("np.where:", np.where(x > 0, x, 0.0))
print("maske sayisi:", int((x > 0).sum()),
      " pozitif ort:", x[x > 0].mean())

v = np.array([1.0, np.nan, 3.0])
print("mean (NaN):", v.mean(), " nanmean:", np.nanmean(v))
print("nan == nan:", np.nan == np.nan, " isnan:", np.isnan(v))
print("nan yayilimi (max):", np.array([1, np.nan]).max())

n = 10**7
x32 = np.full(n, 0.1, dtype=np.float32)
ardisik = np.add.accumulate(x32)[-1]     # soldan saga birikim
ciftli = np.sum(x32, dtype=np.float64)   # genisletilmis toplam
pairwise = np.sum(x32)                   # ikili (pairwise) toplam
print("float32 ardisik birikim :", float(ardisik))
print("float32 np.sum          :", float(pairwise))
print("float64 birikim         :", float(ciftli))
print("gercek (fsum, 10^7*0.1f):", math.fsum(x32.astype(np.float64)))

for dt in (np.int8, np.int64, np.float32, np.float64):
    a = np.zeros(10**6, dtype=dt)
    print("%-8s %9.2f MB" % (np.dtype(dt).name, a.nbytes / 1e6))
