import csv, os
import numpy as np
from scipy.stats import skew
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import (StandardScaler, MinMaxScaler,
                                   RobustScaler, PowerTransformer)

X, y = load_breast_cancer(return_X_y=True)
cv = StratifiedKFold(5, shuffle=True, random_state=56)
print("kNN (k=5) olcekleme karsilastirmasi, 5 katli CV:")
satir = []
adaylar = [("olceksiz", None), ("standart", StandardScaler()),
           ("min-max", MinMaxScaler()), ("robust", RobustScaler())]
for ad, sc in adaylar:
    adim = [] if sc is None else [sc]
    p = make_pipeline(*adim, KNeighborsClassifier(n_neighbors=5))
    s = cross_val_score(p, X, y, cv=cv)
    print("  %-10s %.4f +- %.4f" % (ad, s.mean(), s.std()))
    satir.append((ad, "%.4f" % s.mean(), "%.4f" % s.std()))
for ad, sc in [("olceksiz", None), ("standart", StandardScaler())]:
    adim = [] if sc is None else [sc]
    p = make_pipeline(*adim, DecisionTreeClassifier(max_depth=4,
                                                    random_state=56))
    s = cross_val_score(p, X, y, cv=cv)
    print("agac (%s) %.4f" % (ad, s.mean()))

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_olcek_knn.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["olcekleme", "dogruluk", "std"])
    w.writerows(satir)

print("--- donusum ---")
rng = np.random.default_rng(56)
gelir = rng.lognormal(mean=3.0, sigma=0.8, size=5000)
print("carpiklik ham: %.3f  log1p: %.3f" % (
    skew(gelir), skew(np.log1p(gelir))))
pt = PowerTransformer(method="box-cox")
bc = pt.fit_transform(gelir.reshape(-1, 1)).ravel()
print("box-cox lambda: %.3f  carpiklik: %.3f" % (
    pt.lambdas_[0], skew(bc)))

saat = np.array([0, 23])
ang = 2 * np.pi * saat / 24
nokta = np.c_[np.cos(ang), np.sin(ang)]     # saat -> cember
print("dongusel (sin,cos) 23 ile 0 mesafesi:",
      round(float(np.linalg.norm(nokta[0] - nokta[1])), 4))

x1 = rng.standard_normal(2000)
x2 = rng.standard_normal(2000)
t = x1 * x2 + 0.1 * rng.standard_normal(2000)
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score as cvs
r_dogrusal = cvs(LinearRegression(), np.c_[x1, x2], t, cv=5).mean()
X_etk = np.c_[x1, x2, x1 * x2]
r_etk = cvs(LinearRegression(), X_etk, t, cv=5).mean()
print("R2 dogrusal: %.3f  etkilesimli: %.3f" % (r_dogrusal, r_etk))
