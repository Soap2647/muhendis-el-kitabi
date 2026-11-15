# torba_oob.py -- torbalama, RF, OOB ve sklearn kiyasi
import time
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from agac import KararAgaci
from orman import Torba


def veri(sd):
    X, y = make_classification(n_samples=1200, n_features=20,
                               n_informative=6, n_redundant=4,
                               n_clusters_per_class=2, flip_y=0.05,
                               random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd,
                            stratify=y)


print("tohum  tek agac  torba(B=50)  RF(B=50, sqrt=4)  sklearn RF")
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    tek = np.mean(KararAgaci().fit(Xtr, ytr).tahmin(Xte) != yte)
    t0 = time.perf_counter()
    torba = Torba(B=50, seed=sd).fit(Xtr, ytr)
    sure = time.perf_counter() - t0
    rf = Torba(B=50, max_ozellik=4, seed=sd).fit(Xtr, ytr)
    sk = RandomForestClassifier(n_estimators=50, random_state=sd,
                                n_jobs=1).fit(Xtr, ytr)
    print("%5d  %.4f    %.4f       %.4f            %.4f"
          % (sd, tek, np.mean(torba.tahmin(Xte) != yte),
             np.mean(rf.tahmin(Xte) != yte), 1 - sk.score(Xte, yte)))
    print("       OOB(torba)=%.4f  OOB(RF)=%.4f  torba suresi=%.2fs"
          % (torba.oob_hatasi(ytr)[0], rf.oob_hatasi(ytr)[0], sure))
