# b57_ornek3.py: maliyet matrisine gore en iyi esik
import numpy as np

p = np.array([0.90, 0.70, 0.55, 0.40, 0.30, 0.20, 0.10, 0.05])
y = np.array([1, 1, 0, 1, 0, 0, 1, 0])
c_fp, c_fn = 1, 4
t_star = c_fp / (c_fp + c_fn)
print("c_FP = %d, c_FN = %d, t* = %.3f" % (c_fp, c_fn, t_star))
print("esik   beklenen   gozlenen")
print("       maliyet    maliyet")
for t in [0.05, 0.15, 0.20, 0.25, 0.35, 0.50, 0.80]:
    karar = p >= t
    # Beklenen maliyet: olasiliklari dogru kabul ederek
    bek = np.sum(karar * (1 - p) * c_fp
                 + (~karar) * p * c_fn) / len(p)
    # Gozlenen maliyet: gercek etiketlerle
    fp = int(np.sum(karar & (y == 0)))
    fn = int(np.sum(~karar & (y == 1)))
    goz = (c_fp * fp + c_fn * fn) / len(p)
    print("%.2f   %.4f     %.4f" % (t, bek, goz))
