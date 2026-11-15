# b57_08_karsilastirma.py
# Iki model farkli mi? McNemar (sifirdan), bootstrap, 5x2 CV
import math
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (StratifiedKFold,
                                     train_test_split)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


def mcnemar(dogru1, dogru2):
    """Eslestirilmis ikili sonuclar. b: 1 dogru, 2 yanlis; c tersi."""
    b = int(np.sum(dogru1 & ~dogru2))
    c = int(np.sum(~dogru1 & dogru2))
    n = b + c
    if n == 0:
        return b, c, 0.0, 1.0
    chi2 = (abs(b - c) - 1) ** 2 / n          # sureklilik duzeltmeli
    p_ki = math.erfc(math.sqrt(chi2 / 2))     # 1 serbestlik derecesi
    # Tam (exact) iki yonlu binom p-degeri: Bin(n, 1/2)
    alt = sum(math.comb(n, k) for k in range(min(b, c) + 1))
    p_tam = min(1.0, 2 * alt / 2 ** n)
    return b, c, chi2, p_ki, p_tam


def bootstrap_fark(d1, d2, B=2000, seed=57):
    """Test ornekleri yeniden orneklenerek fark icin %95 GA."""
    rng = np.random.default_rng(seed)
    n = len(d1)
    fark = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        fark.append(d1[i].mean() - d2[i].mean())
    return np.percentile(fark, [2.5, 97.5])


veri = load_breast_cancer()
y = (veri.target == 0).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, y, test_size=0.3, stratify=y, random_state=57)

m1 = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=2000))
m2 = DecisionTreeClassifier(max_depth=3, random_state=57)
m1.fit(X_tr, y_tr)
m2.fit(X_tr, y_tr)
t1, t2 = m1.predict(X_te), m2.predict(X_te)
d1, d2 = (t1 == y_te), (t2 == y_te)
print("Test ornegi: %d" % len(y_te))
print("Model 1 (lojistik) dogruluk: %.4f" % d1.mean())
print("Model 2 (agac, derinlik 3) dogruluk: %.4f" % d2.mean())

# ---------- McNemar ----------
b, c, chi2, p_ki, p_tam = mcnemar(d1, d2)
print("\nMcNemar: b = %d (1 dogru, 2 yanlis), c = %d" % (b, c))
print("chi2 (sureklilik duzeltmeli) = %.4f, p = %.4f" % (chi2, p_ki))
print("Tam binom p = %.4f" % p_tam)
# Kontrol: scipy (sklearn'in bagimliligi) ile ayni binom p-degeri
from scipy.stats import binomtest
p_sc = binomtest(min(b, c), b + c, 0.5,
                  alternative="two-sided").pvalue
print("scipy binomtest p = %.4f (cross-check)" % p_sc)
assert abs(p_sc - p_tam) < 1e-9
# Yonelim tablosu (karisiklik)
print("\nTablo: model1/model2 (dogru,yanlis):")
print("dogru-dogru %d  dogru-yanlis %d" % (np.sum(d1 & d2), b))
print("yanlis-dogru %d  yanlis-yanlis %d"
      % (c, np.sum(~d1 & ~d2)))

# ---------- Bootstrap farki ----------
lo, hi = bootstrap_fark(d1.astype(float), d2.astype(float))
print("\nDogruluk farki (1-2) = %.4f" % (d1.mean() - d2.mean()))
print("Bootstrap %%95 GA (eslestirilmis yeniden ornekleme): "
      "[%.4f, %.4f]" % (lo, hi))

# ---------- 5x2 CV t-testi (Dietterich 1998) ----------
# 5 tekrar x 2 kat. Her tekrarda iki modelin hata farki.
farklar = []
varyanslar = []
for tekrar in range(5):
    kat = StratifiedKFold(2, shuffle=True, random_state=tekrar)
    p = []
    for tr, te in kat.split(veri.data, y):
        a = make_pipeline(StandardScaler(),
                          LogisticRegression(max_iter=2000)).fit(
            veri.data[tr], y[tr])
        bb = DecisionTreeClassifier(max_depth=3, random_state=57).fit(
            veri.data[tr], y[tr])
        hata_a = np.mean(a.predict(veri.data[te]) != y[te])
        hata_b = np.mean(bb.predict(veri.data[te]) != y[te])
        p.append(hata_a - hata_b)
    p = np.array(p)
    ort = p.mean()
    varyanslar.append((p[0] - ort) ** 2 + (p[1] - ort) ** 2)
    farklar.append(p[0])
t_stat = farklar[0] / math.sqrt(np.mean(varyanslar))
print("\n5x2 CV: t = %.4f (serbestlik 5)" % t_stat)
print("Kritik deger (iki yonlu, %5, df=5) = 2.571")
print("Karar:", "fark anlamli" if abs(t_stat) > 2.571
      else "fark anlamli degil (bu veride)")
print("Not: 5x2 CV katlari bagimsiz degil; t-testi bu yuzden")
print("yaklasik. Ayrintilarini kaynaktan okuyun (Dietterich 1998).")
