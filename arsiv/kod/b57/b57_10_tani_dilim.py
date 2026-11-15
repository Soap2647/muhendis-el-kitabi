# b57_10_tani_dilim.py
# Ogrenme egrisi tanisi (sapma/varyans) ve dilim bazli hata analizi
import os
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import load_breast_cancer, load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (StratifiedKFold, learning_curve,
                                     train_test_split)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- 1) Ogrenme egrisi: uc tani ----------
d = load_digits()
X, y = d.data, d.target
cv = StratifiedKFold(5, shuffle=True, random_state=57)
boyutlar = np.linspace(0.1, 1.0, 6)
modeller = [
    ("yuksek sapma", make_pipeline(
        StandardScaler(), LogisticRegression(C=1e-4, max_iter=2000))),
    ("yuksek varyans", DecisionTreeClassifier(random_state=57)),
    ("dengeli", make_pipeline(
        StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))),
]
satirlar = []
for ad, m in modeller:
    n_tr, tr_skor, va_skor = learning_curve(
        m, X, y, cv=cv, train_sizes=boyutlar, scoring="accuracy")
    print("\n%s" % ad)
    print("  n_egitim  egitim   dogrulama  (std)")
    for n_i, a, b in zip(n_tr, tr_skor.mean(1), va_skor.mean(1)):
        s = va_skor[list(n_tr).index(n_i)].std()
        print("  %6d    %.3f    %.3f      %.3f" % (n_i, a, b, s))
        satirlar.append((ad, n_i, a, b, s))
    print("  son boy: egitim-dogrulama farki = %.3f"
          % (tr_skor[-1].mean() - va_skor[-1].mean()))

# Yuksek varyans: 1-NN, cok az veriyle ezber
X_s, _, y_s, _ = train_test_split(X, y, train_size=200,
                                  stratify=y, random_state=57)
knn = KNeighborsClassifier(n_neighbors=1)
print("\n1-NN, 200 ornek: egitim = %.3f"
      % knn.fit(X_s, y_s).score(X_s, y_s))

# ---------- 2) Dilim bazli hata analizi ----------
v = load_breast_cancer()
yb = (v.target == 0).astype(int)     # 1 = kotu huylu (pozitif)
Xb_tr, Xb_te, yb_tr, yb_te = train_test_split(
    v.data, yb, test_size=0.3, stratify=yb, random_state=57)
mb = make_pipeline(StandardScaler(),
                   LogisticRegression(max_iter=2000))
mb.fit(Xb_tr, yb_tr)
tb = mb.predict(Xb_te)
print("\nGenel: dogruluk %.4f, duyarlilik %.4f"
      % (M.accuracy_score(yb_te, tb), M.recall_score(yb_te, tb)))

# Dilim: "mean radius" (ozellik 0) ceyreklerine gore
r = Xb_te[:, 0]
kenar = np.quantile(r, [0.25, 0.5, 0.75])
dilim = np.digitize(r, kenar)
print("\nDilim (mean radius ceyreklerine gore) - test:")
print("dilim  sinir-aralik          n   dogruluk  "
      "duyarlilik  pozitif")
for k in range(4):
    m = dilim == k
    if k == 0:
        aralik = "< %.2f" % kenar[0]
    elif k == 3:
        aralik = ">= %.2f" % kenar[2]
    else:
        aralik = "[%.2f, %.2f)" % (kenar[k - 1], kenar[k])
    print("%d     %-18s %4d   %.4f     %.4f      %3d" % (
        k, aralik, m.sum(), M.accuracy_score(yb_te[m], tb[m]),
        M.recall_score(yb_te[m], tb[m], zero_division=0),
        yb_te[m].sum()))

# Ortalama tek basina yaniltir: en kotu dilimin karisikligi
en_kotu = min(range(4), key=lambda k: M.recall_score(
    yb_te[dilim == k], tb[dilim == k], zero_division=0))
m = dilim == en_kotu
print("\nEn kotu dilim: %d. Karisiklik (satir=gercek, sutun=tahmin):"
      % en_kotu)
print(M.confusion_matrix(yb_te[m], tb[m], labels=[0, 1]))

# En guvenli yanlislar: pozitif iken dusuk olasilik verilenler
p_pos = mb.predict_proba(Xb_te)[:, 1]
kacan = np.where((yb_te == 1) & (tb == 0))[0]
kacan = kacan[np.argsort(p_pos[kacan])][:3]
print("\nKacan 3 pozitif (en dusuk olasilik): p =",
      np.round(p_pos[kacan], 3))

# ---------- Sekil verisi ----------
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_ogrenme_egrisi.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("model,n_egitim,egitim,dogrulama,std\n")
    for ad, n_i, a, b, s in satirlar:
        f.write("%s,%d,%.5f,%.5f,%.5f\n" % (ad, n_i, a, b, s))
print("\nOgrenme egrisi verisi yazildi:", os.path.basename(yol))
