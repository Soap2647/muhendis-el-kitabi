# ornek_oob.py -- 6 ornekli bootstrap ve OOB kumesi (sabit tohum)
import numpy as np

rng = np.random.default_rng(59)
n = 6
for b in range(3):
    ornek = rng.integers(0, n, n)           # iadeli ornekleme
    sayim = np.bincount(ornek, minlength=n)
    oob = np.setdiff1d(np.arange(n), ornek)  # secilmeyenler
    print("agac %d: ornek=%s" % (b + 1, ornek.tolist()))
    print("        sayim=%s  OOB=%s" % (sayim.tolist(), oob.tolist()))
print("tek ornegin bir bootstrapte secilmeme olasiligi: %.4f"
      % ((1 - 1 / n) ** n))
