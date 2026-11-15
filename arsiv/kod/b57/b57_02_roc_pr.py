# b57_02_roc_pr.py
# ROC ve PR egrileri sifirdan; AUC = Mann-Whitney; dengesizlik
import os
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


def esik_sayaclari(y, skor):
    """Her farkli skor esigi icin TP ve FP sayilari."""
    sira = np.argsort(-skor, kind="mergesort")
    y_s, s_s = y[sira], skor[sira]
    # Ayni skorlu ornekler tek bir esik olusturur: grup sonlari
    son = np.r_[np.where(np.diff(s_s))[0], len(s_s) - 1]
    tp = np.cumsum(y_s)[son]
    fp = (son + 1) - tp
    return s_s[son], tp, fp


def roc_noktalari(y, skor):
    P, N = y.sum(), len(y) - y.sum()
    _, tp, fp = esik_sayaclari(y, skor)
    tpr = np.r_[0.0, tp / P]
    fpr = np.r_[0.0, fp / N]
    return fpr, tpr


def pr_noktalari(y, skor):
    P = y.sum()
    _, tp, fp = esik_sayaclari(y, skor)
    precision = tp / (tp + fp)
    recall = tp / P
    return precision, recall


def roc_naif(y, skor):
    """O(n*u) kaba kuvvet: her esik icin tum ornekleri tara."""
    P, N = y.sum(), len(y) - y.sum()
    fpr, tpr = [0.0], [0.0]
    for t in np.unique(skor)[::-1]:
        tahmin = skor >= t
        tpr.append(np.sum(tahmin & (y == 1)) / P)
        fpr.append(np.sum(tahmin & (y == 0)) / N)
    return np.array(fpr), np.array(tpr)


def auc_trapez(fpr, tpr):
    return np.trapezoid(tpr, fpr)


def ortalama_kesinlik(precision, recall):
    """AP = sum (R_n - R_{n-1}) * P_n, R_0 = 0 (sklearn tanimi)."""
    r_onc = np.r_[0.0, recall[:-1]]
    return np.sum((recall - r_onc) * precision)


def auc_mann_whitney(y, skor):
    """P(pozitif skor > negatif skor) + 0.5 * P(esit)."""
    poz, neg = skor[y == 1], skor[y == 0]
    fark = poz[:, None] - neg[None, :]
    return ((fark > 0).sum() + 0.5 * (fark == 0).sum()) / (
        len(poz) * len(neg))


# ---------- 1) Kucuk ornek: elle izlenebilir ----------
y_k = np.array([1, 0, 1, 1, 0, 0, 1, 0])
s_k = np.array([0.9, 0.8, 0.7, 0.7, 0.4, 0.3, 0.2, 0.1])
fpr_k, tpr_k = roc_noktalari(y_k, s_k)
print("Kucuk ornek: esik, TPR, FPR")
esikler, tp, fp = esik_sayaclari(y_k, s_k)
for e, a, b in zip(esikler, tpr_k[1:], fpr_k[1:]):
    print("%.2f   %.3f   %.3f" % (e, a, b))
print("AUC (yamuk)      = %.4f" % auc_trapez(fpr_k, tpr_k))
print("AUC (Mann-Whitney)= %.4f" % auc_mann_whitney(y_k, s_k))
print("sklearn roc_auc   = %.4f" % M.roc_auc_score(y_k, s_k))
assert abs(auc_trapez(fpr_k, tpr_k)
           - M.roc_auc_score(y_k, s_k)) < 1e-12

# ---------- 2) Rastgele 400 ornek: uc yol ayni ----------
rng = np.random.default_rng(57)
y_r = rng.integers(0, 2, 400)
s_r = rng.normal(loc=0.8 * y_r, scale=1.0)   # pozitifler biraz yuksek
a1 = auc_trapez(*roc_noktalari(y_r, s_r))
a2 = auc_mann_whitney(y_r, s_r)
a3 = M.roc_auc_score(y_r, s_r)
print("\nRastgele 400 ornek:")
print("yamuk %.6f  MW %.6f  sklearn %.6f" % (a1, a2, a3))
assert abs(a1 - a2) < 1e-12 and abs(a2 - a3) < 1e-12

# Kaba kuvvet ve siralama ayni eglriyi uretiyor mu?
f_n, t_n = roc_naif(y_r, s_r)
f_s, t_s = roc_noktalari(y_r, s_r)
print("kaba kuvvet ile siralama ayni nokta sayisi: %d = %d"
      % (len(f_n), len(f_s)))
assert np.allclose(f_n, f_s) and np.allclose(t_n, t_s)
fs_sk, ts_sk, _ = M.roc_curve(y_r, s_r, drop_intermediate=False)
assert np.allclose(fs_sk, f_s) and np.allclose(ts_sk, t_s)
print("sklearn roc_curve(drop_intermediate=False) ile birebir.")
# Sklearn 1.8 cekirdek sayaclari (confusion_matrix_at_thresholds)
tns, fps_sk, fns, tps_sk, esik_sk = M.confusion_matrix_at_thresholds(
    y_r, s_r)
esik_b, tp_b, fp_b = esik_sayaclari(y_r, s_r)
assert np.allclose(tps_sk, tp_b) and np.allclose(fps_sk, fp_b)
assert np.allclose(esik_sk, esik_b)
print("TP/FP dizileri ve esikler confusion_matrix_at_thresholds")
print("ile ayni.")

# ---------- 3) Dengesiz veri: %1 pozitif ----------
X, y = make_classification(
    n_samples=100000, n_features=20, n_informative=6, n_redundant=2,
    weights=[0.99], flip_y=0.0, class_sep=1.0, random_state=57,
    shuffle=False)
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=57)
print("\nDengesiz veri: pozitif orani train=%.4f test=%.4f"
      % (y_tr.mean(), y_te.mean()))

# Model A: tum oznitelikler. Model B: yalnizca ilk 3 oznitelik.
mA = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=1000))
mB = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=1000))
mA.fit(X_tr, y_tr)
mB.fit(X_tr[:, :3], y_tr)
sA = mA.predict_proba(X_te)[:, 1]
sB = mB.predict_proba(X_te[:, :3])[:, 1]

print("\nModel        ROC-AUC    PR-AUC (AP)   taban (oran)")
satirlar = []
for ad, s in [("A (20 oznitelik)", sA), ("B (3 oznitelik)", sB)]:
    fpr, tpr = roc_noktalari(y_te, s)
    pre, rec = pr_noktalari(y_te, s)
    roc = auc_trapez(fpr, tpr)
    ap = ortalama_kesinlik(pre, rec)
    assert abs(roc - M.roc_auc_score(y_te, s)) < 1e-9
    assert abs(ap - M.average_precision_score(y_te, s)) < 1e-9
    print("%-16s %.4f     %.4f        %.4f"
          % (ad, roc, ap, y_te.mean()))
    satirlar.append((ad, fpr, tpr, rec, pre))

print("\nScratch ROC-AUC ve AP sklearn roc_auc_score ve")
print("average_precision_score ile birebir eslesti.")

# ROC farki, AP farki: hangisi daha cok ayiriyor?
roc_A = M.roc_auc_score(y_te, sA)
roc_B = M.roc_auc_score(y_te, sB)
ap_A = M.average_precision_score(y_te, sA)
ap_B = M.average_precision_score(y_te, sB)
print("\nFark (A - B): ROC-AUC %.4f, AP %.4f"
      % (roc_A - roc_B, ap_A - ap_B))

# Dogru pozitif sayisi ve FP: %1 de 100 kisiden 1 pozitif
P_test = y_te.sum()
N_test = len(y_te) - P_test
print("Test: P=%d N=%d. Yanlis alarm orani %%1 olsa bile"
      % (P_test, N_test))
print("%.0f negatif ornekte %.0f yanlis alarm demek."
      % (N_test, 0.01 * N_test))

# Ayni model A, pozitifleri %50 yapilmis (dengeli) veride
X2, y2 = make_classification(
    n_samples=20000, n_features=20, n_informative=6, n_redundant=2,
    weights=[0.5], flip_y=0.0, class_sep=1.0, random_state=57,
    shuffle=False)
X2_tr, X2_te, y2_tr, y2_te = train_test_split(
    X2, y2, test_size=0.3, stratify=y2, random_state=57)
mD = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=1000))
mD.fit(X2_tr, y2_tr)
sD = mD.predict_proba(X2_te)[:, 1]
print("\nDengeli veri (%50 pozitif), ayni tur model:")
print("ROC-AUC %.4f  AP %.4f  taban %.4f"
      % (M.roc_auc_score(y2_te, sD),
         M.average_precision_score(y2_te, sD), y2_te.mean()))

# ---------- Egri verisi (sekil icin) ----------
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_roc_pr_egri.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("model,fpr,tpr,recall,precision\n")
    for ad, fpr, tpr, rec, pre in satirlar:
        ad_kisa = "A" if ad.startswith("A") else "B"
        # ROC ve PR noktalari farkli uzunlukta; ayri yazilir
        # Dosya boyutu icin ~300 noktaya seyreltilmis
        k_roc = max(1, len(fpr) // 300)
        for a, b in list(zip(fpr, tpr))[::k_roc]:
            f.write("%s,%.6f,%.6f,,\n" % (ad_kisa, a, b))
        k_pr = max(1, len(rec) // 300)
        for r, p in list(zip(rec, pre))[::k_pr]:
            f.write("%s,,,%.6f,%.6f\n" % (ad_kisa, r, p))
print("\nEgri verisi yazildi:", os.path.basename(yol))

# Sekil verisi: 8 ornekli kucuk ornek, esik bazinda
_e, _tp, _fp = esik_sayaclari(y_k, s_k)
with open(os.path.join(VERI, "b57_kucuk_ornek.csv"), "w",
          encoding="utf-8") as _f:
    _f.write("esik,tpr,fpr,kesinlik,duyarlilik\n")
    _P, _N = y_k.sum(), len(y_k) - y_k.sum()
    for _a, _t, _b in zip(_e, _tp, _fp):
        _f.write("%.2f,%.5f,%.5f,%.5f,%.5f\n" % (
            _a, _t / _P, _b / _N, _t / (_t + _b), _t / _P))
