# ornek_gbm.py -- 5 noktada 3 adimlik gradyan artirma izi (eta=0.5)
import numpy as np
from agac import KararAgaci

x = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
y = np.array([2.0, 2.2, 1.8, 4.1, 4.3])
eta = 0.5
F = np.full(5, y.mean())
print("F0 =", np.round(F, 4).tolist())
for t in range(3):
    r = y - F                 # artik (negatif gradyan)
    agac = KararAgaci(mod="regresyon", max_derinlik=1,
                      min_yaprak=1).fit(x, r)
    h = agac.olasilik(x)  # yaprak ortalamalari
    F = F + eta * h
    print("adim %d: r=%s" % (t + 1, np.round(r, 2).tolist()))
    print("        h=%s" % np.round(h, 3).tolist())
    print("        F=%s" % np.round(F, 3).tolist())
