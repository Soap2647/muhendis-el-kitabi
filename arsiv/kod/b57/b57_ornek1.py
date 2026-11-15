# b57_ornek1.py: karisiklik matrisinden metrikler (elle + sklearn)
import numpy as np
from sklearn import metrics as M

TP, FN, FP, TN = 18, 6, 9, 167        # 200 kayit
N = TP + FN + FP + TN
print("N = %d, gercek pozitif = %d" % (N, TP + FN))

dogruluk = (TP + TN) / N
kesinlik = TP / (TP + FP)
duyarlilik = TP / (TP + FN)
ozgulluk = TN / (TN + FP)
f1 = 2 * kesinlik * duyarlilik / (kesinlik + duyarlilik)
f2 = 5 * kesinlik * duyarlilik / (4 * kesinlik + duyarlilik)
pay = TP * TN - FP * FN
payda = np.sqrt((TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
mcc = pay / payda
pe = ((TP + FP) * (TP + FN) + (TN + FN) * (TN + FP)) / N ** 2
kappa = (dogruluk - pe) / (1 - pe)

print("dogruluk   = %.4f" % dogruluk)
print("kesinlik   = %.4f" % kesinlik)
print("duyarlilik = %.4f" % duyarlilik)
print("ozgulluk   = %.4f" % ozgulluk)
print("F1         = %.4f" % f1)
print("F2         = %.4f" % f2)
print("MCC        = %.4f" % mcc)
print("kappa      = %.4f" % kappa)
print("hep 0 diyen dogruluk = %.4f" % ((TN + FP) / N))

# sklearn ile kontrol: ayni sayilardan etiket dizileri
y = np.r_[np.ones(TP + FN), np.zeros(FP + TN)].astype(int)
t = np.r_[np.ones(TP), np.zeros(FN),
           np.ones(FP), np.zeros(TN)].astype(int)
assert abs(M.accuracy_score(y, t) - dogruluk) < 1e-12
assert abs(M.f1_score(y, t) - f1) < 1e-12
assert abs(M.fbeta_score(y, t, beta=2) - f2) < 1e-12
assert abs(M.matthews_corrcoef(y, t) - mcc) < 1e-12
assert abs(M.cohen_kappa_score(y, t) - kappa) < 1e-12
print("sklearn ile birebir eslesti.")
