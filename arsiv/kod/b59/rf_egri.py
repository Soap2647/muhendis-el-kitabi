# rf_egri.py -- sklearn RF: agac sayisina gore test hatasi (5 tohum)
import csv
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def veri(sd):
    X, y = make_classification(n_samples=1200, n_features=20,
                               n_informative=6, n_redundant=4,
                               n_clusters_per_class=2, flip_y=0.05,
                               random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd,
                            stratify=y)


satirlar = []
for B in [1, 2, 5, 10, 20, 50, 100, 200]:
    e = []
    for sd in range(5):
        Xtr, Xte, ytr, yte = veri(sd)
        rf = RandomForestClassifier(n_estimators=B, random_state=sd,
                                    n_jobs=-1).fit(Xtr, ytr)
        e.append(1 - rf.score(Xte, yte))
    satirlar.append((B, np.mean(e), np.std(e)))
    print("B=%3d  test hatasi %.4f +- %.4f" % satirlar[-1])
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_rf_agac.csv",
          "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["agac_sayisi", "test_hata_ort", "test_hata_ss"])
    w.writerows(satirlar)
