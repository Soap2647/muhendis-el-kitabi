# deney5_rf_ayni.py -- ayni 3 tohumda benim RF'im vs sklearn RF (B=50)
import time, numpy as np
from orman import Torba
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def veri(sd):
    X, y = make_classification(n_samples=1200, n_features=20,
            n_informative=6, n_redundant=4, n_clusters_per_class=2,
            flip_y=0.05, random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd,
                            stratify=y)

b_hata, s_hata, b_sure, s_sure = [], [], [], []
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    t0 = time.perf_counter()
    rf = Torba(B=50, max_ozellik=4, seed=sd).fit(Xtr, ytr)
    b_sure.append(time.perf_counter() - t0)
    b_hata.append(np.mean(rf.tahmin(Xte) != yte))
    t0 = time.perf_counter()
    sk = RandomForestClassifier(n_estimators=50, random_state=sd,
                                n_jobs=1).fit(Xtr, ytr)
    s_sure.append(time.perf_counter() - t0)
    s_hata.append(1 - sk.score(Xte, yte))
print("benim RF  test hatasi %.4f +- %.4f  sure %.2f s"
      % (np.mean(b_hata), np.std(b_hata), np.mean(b_sure)))
print("sklearn   test hatasi %.4f +- %.4f  sure %.2f s"
      % (np.mean(s_hata), np.std(s_hata), np.mean(s_sure)))
print("tohum bazinda benim:", np.round(b_hata, 4))
print("tohum bazinda sklearn:", np.round(s_hata, 4))
