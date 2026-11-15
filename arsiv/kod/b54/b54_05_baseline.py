import csv
import os
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import (StratifiedKFold, learning_curve,
                                     train_test_split)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))

# Dengesizlik paradoksu: %5 pozitif (ör. sahte alarm / nadir ariza)
rng = np.random.default_rng(54)
y_nadir = (rng.random(10000) < 0.05).astype(int)
tahmin = np.zeros_like(y_nadir)          # hep "0" diyen model
print("nadir olay orani:", y_nadir.mean().round(4))
print("hep-0 modelinin dogrulugu:",
      round(accuracy_score(y_nadir, tahmin), 4))
print("dengeli dogruluk (hep-0):",
      round(balanced_accuracy_score(y_nadir, tahmin), 4))

# Gerçek veri: Wisconsin meme kanseri (paketle gelir, indirilmez)
veri = load_breast_cancer()
X, y = veri.data, veri.target
print("\nsekil:", X.shape, " sinif sayilari:", np.bincount(y))
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=54)

modeller = {
    "hep-cogunluk": DummyClassifier(strategy="most_frequent"),
    "rastgele-oran": DummyClassifier(strategy="stratified",
                                     random_state=54),
    "lojistik": make_pipeline(StandardScaler(),
                              LogisticRegression(max_iter=1000)),
}
sonuc = []
print("\nTEST kumesi (bir kez):  model  dogruluk  dengeli_dogruluk")
for ad, m in modeller.items():
    m.fit(X_tr, y_tr)
    t = m.predict(X_te)
    a, b = accuracy_score(y_te, t), balanced_accuracy_score(y_te, t)
    sonuc.append((ad, a, b))
    print("  %-14s %8.4f  %10.4f" % (ad, a, b))

cv = StratifiedKFold(5, shuffle=True, random_state=54)
boyutlar, egitim, dogrulama = learning_curve(
    make_pipeline(StandardScaler(),
                  LogisticRegression(max_iter=1000)),
    X_tr, y_tr, cv=cv, train_sizes=np.linspace(0.1, 1.0, 10),
    scoring="accuracy")
print("\negitim boyutu  egitim_skor  dogrulama_skor(CV)")
for n, e, v in zip(boyutlar, egitim.mean(1), dogrulama.mean(1)):
    print("%8d   %11.4f   %14.4f" % (n, e, v))

with open(os.path.join(HERE, "veri", "b54_baseline.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["model", "dogruluk", "dengeli_dogruluk"])
    w.writerows([(a, "%.4f" % b, "%.4f" % c) for a, b, c in sonuc])
with open(os.path.join(HERE, "veri", "b54_ogrenme_egrisi.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["egitim_boyutu", "egitim_skor", "cv_skor"])
    w.writerows([(n, "%.4f" % e, "%.4f" % v) for n, e, v in
                 zip(boyutlar, egitim.mean(1), dogrulama.mean(1))])
