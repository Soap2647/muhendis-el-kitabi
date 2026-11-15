# b57_03_esik_maliyet.py
# Maliyet temelli esik secimi ve calisma noktasi (Neyman-Pearson)
import os
import numpy as np
from sklearn import metrics as M
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
rng = np.random.default_rng(57)

# Gercek olasilik modeli bilinen: lojistik. Kalibre olasiliklar.
n = 300000
X = rng.normal(size=(n, 3))
w = np.array([1.2, -0.8, 0.5])
b = -5.6
p_gercek = 1.0 / (1.0 + np.exp(-(X @ w + b)))
y = (rng.random(n) < p_gercek).astype(int)
print("Pozitif orani: %.4f" % y.mean())

c_fp, c_fn = 1.0, 50.0          # yanlis alarm 1, kacan tespit 50
t_teori = c_fp / (c_fp + c_fn)  # kalibre olasiliklarda en iyi esik
print("Teorik esik t* = c_FP/(c_FP+c_FN) = 1/51 = %.5f" % t_teori)


def maliyet(p, y, t):
    """Ornek basina beklenen maliyet, esik t'de."""
    tahmin = p >= t
    fp = np.sum(tahmin & (y == 0))
    fn = np.sum(~tahmin & (y == 1))
    return (c_fp * fp + c_fn * fn) / len(y)


# 1) Gercek olasiliklar uzerinde esik taramasi
esikler = np.linspace(0.001, 0.2, 2000)
mal_gercek = np.array([maliyet(p_gercek, y, t) for t in esikler])
en_iyi = esikler[np.argmin(mal_gercek)]
print("Gercek olasilikla taramada en iyi esik: %.4f" % en_iyi)
print("Bu esikteki maliyet: %.5f" % mal_gercek.min())
print("t* = 0.0196'daki maliyet: %.5f"
      % maliyet(p_gercek, y, t_teori))

# 2) Ogrenilmis model: lojistik regresyon (egitim/test ayrimi)
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.4, random_state=57, stratify=y)
model = LogisticRegression(C=1e6, max_iter=5000).fit(X_tr, y_tr)
p_mod = model.predict_proba(X_te)[:, 1]
print("\nModelin katsayilari:", np.round(model.coef_[0], 3),
      "b=%.3f" % model.intercept_[0])

mal_mod = np.array([maliyet(p_mod, y_te, t) for t in esikler])
en_iyi_mod = esikler[np.argmin(mal_mod)]
print("Model olasiliklariyla en iyi esik (test): %.4f" % en_iyi_mod)
print("Bu esikteki maliyet: %.5f" % mal_mod.min())
print("t* = 0.0196'daki maliyet (test): %.5f" % maliyet(p_mod, y_te,
                                                         t_teori))

# 3) Calisma noktasi: FPR en fazla %1 iken en yuksek tespit
fpr, tpr, esik_roc = M.roc_curve(y_te, p_mod, drop_intermediate=False)
uygun = fpr <= 0.01
i = np.argmax(np.where(uygun, tpr, -1))
print("\nFPR <= 0.01 kisitinda en yuksek TPR = %.4f" % tpr[i])
print("Bu nokta icin esik = %.4f (FPR=%.5f)" % (esik_roc[i], fpr[i]))

# 4) Esik tablosu
print("\n  esik    TPR     FPR    maliyet/ornek")
for t in [0.005, 0.01, 0.0196, 0.05, 0.1, 0.2]:
    tah = p_mod >= t
    tp = np.sum(tah & (y_te == 1))
    fp = np.sum(tah & (y_te == 0))
    P = y_te.sum()
    N = len(y_te) - P
    print("%6.4f  %6.3f  %6.4f   %10.5f" % (
        t, tp / P, fp / N, maliyet(p_mod, y_te, t)))

# Sklearn ile dogrulama: en iyi esikte TP/FP sayilari
t = en_iyi_mod
tah = p_mod >= t
assert np.sum(tah & (y_te == 1)) == np.sum((p_mod >= t) & (y_te == 1))
assert abs(M.recall_score(y_te, tah.astype(int))
           - np.sum(tah & (y_te == 1)) / y_te.sum()) < 1e-12

# Maliyet egrisi verisi (sekil icin)
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_esik_maliyet.csv")
ilk = np.geomspace(0.001, 0.2, 300)
with open(yol, "w", encoding="utf-8") as f:
    f.write("esik,maliyet_model,maliyet_gercek\n")
    for t in ilk:
        f.write("%.6f,%.6f,%.6f\n" % (t, maliyet(p_mod, y_te, t),
                                      maliyet(p_gercek, y, t)))
print("\nMaliyet verisi yazildi:", os.path.basename(yol))
