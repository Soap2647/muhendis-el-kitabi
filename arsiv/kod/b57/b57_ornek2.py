# b57_ornek2.py: 6 ornekle ROC noktalari, AUC ve Mann-Whitney
import numpy as np
from sklearn import metrics as M

skor = np.array([0.95, 0.85, 0.70, 0.60, 0.40, 0.20])
y = np.array([1, 0, 1, 1, 0, 0])
P, N = y.sum(), len(y) - y.sum()
print("P = %d, N = %d" % (P, N))
print("esik   TP  FP   TPR     FPR")
tp = fp = 0
noktalar = [(0.0, 0.0)]
for e in np.sort(skor)[::-1]:
    tp = np.sum((skor >= e) & (y == 1))
    fp = np.sum((skor >= e) & (y == 0))
    noktalar.append((fp / N, tp / P))
    print("%.2f   %d   %d   %.3f   %.3f"
          % (e, tp, fp, tp / P, fp / N))

x = np.array([p[0] for p in noktalar])
yy = np.array([p[1] for p in noktalar])
auc = np.sum((x[1:] - x[:-1]) * (yy[1:] + yy[:-1]) / 2)
print("AUC (yamuk) = %.4f  (= 7/9 = %.4f)" % (auc, 7 / 9))

poz, neg = skor[y == 1], skor[y == 0]
cift = [(a > b) + 0.5 * (a == b) for a in poz for b in neg]
print("Mann-Whitney: %d/9 = %.4f" % (sum(cift), np.mean(cift)))
assert abs(auc - M.roc_auc_score(y, skor)) < 1e-12
assert abs(np.mean(cift) - auc) < 1e-12
print("sklearn roc_auc_score ile birebir.")
