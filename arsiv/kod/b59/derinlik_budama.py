# derinlik_budama.py -- derinlik egrisi ve budama (ccp_alpha)
import csv
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from agac import KararAgaci

X, y = load_breast_cancer(return_X_y=True)
print("== Derinlik: egitim ve test hatasi (5 tohum)")
satirlar = []
for d in range(1, 11):
    etr, ete = [], []
    for sd in range(5):
        a, b, c, e = train_test_split(X, y, test_size=0.3,
                                      random_state=sd, stratify=y)
        m = KararAgaci(max_derinlik=d).fit(a, c)
        etr.append(np.mean(m.tahmin(a) != c))
        ete.append(np.mean(m.tahmin(b) != e))
    satirlar.append((d, np.mean(etr), np.std(etr),
                     np.mean(ete), np.std(ete)))
    print("d=%2d egitim %.4f +- %.4f  test %.4f +- %.4f"
          % satirlar[-1])
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_derinlik.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derinlik", "egitim_ort", "egitim_ss", "test_ort",
                "test_ss"])
    w.writerows(satirlar)

print("\n== Budama: alfa secimi (yalnizca egitim verisinde CV)")
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
yol = DecisionTreeClassifier(random_state=0)
alfalar = yol.cost_complexity_pruning_path(Xtr, ytr).ccp_alphas
alfalar = np.unique(np.round(alfalar[:-1], 5))
cv = [cross_val_score(DecisionTreeClassifier(ccp_alpha=a,
      random_state=0), Xtr, ytr, cv=5).mean() for a in alfalar]
i = int(np.argmax(cv))
t = DecisionTreeClassifier(ccp_alpha=alfalar[i], random_state=0)
t.fit(Xtr, ytr)
print("secilen alfa=%.5f  CV=%.4f" % (alfalar[i], cv[i]))
print("secilen alfa ile test=%.4f yaprak=%d"
      % (t.score(Xte, yte), t.get_n_leaves()))
t0 = DecisionTreeClassifier(random_state=0).fit(Xtr, ytr)
print("budamasiz test=%.4f yaprak=%d"
      % (t0.score(Xte, yte), t0.get_n_leaves()))
