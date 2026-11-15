# deney2b_torba.py -- bagging, OOB, rastgele orman (sifirdan vs sklearn)
import time, csv, os
import numpy as np
from orman import Torba
from agac import KararAgaci
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"

def veri(sd):
    X, y = make_classification(n_samples=1200, n_features=20,
            n_informative=6, n_redundant=4, n_clusters_per_class=2,
            flip_y=0.05, random_state=sd)
    return train_test_split(X, y, test_size=0.3, random_state=sd,
                            stratify=y)

print("== Tek agac (benim) vs torbalama vs rastgele orman")
print("(3 tohum; test hatasi ve OOB hatasi ortalama +- ss)")
sonuc = {}
for sd in range(3):
    Xtr, Xte, ytr, yte = veri(sd)
    t = KararAgaci().fit(Xtr, ytr)
    sonuc.setdefault(("tek", 1), []).append(np.mean(t.tahmin(Xte) != yte))
    for B in [5, 25, 50]:
        t0 = time.perf_counter()
        tb = Torba(B=B, seed=sd).fit(Xtr, ytr)
        sure = time.perf_counter() - t0
        oob, kaps = tb.oob_hatasi(ytr)
        sonuc.setdefault(("torba", B), []).append(
            (np.mean(tb.tahmin(Xte) != yte), oob, sure))
        tr = Torba(B=B, max_ozellik=4, seed=sd).fit(Xtr, ytr)
        oobr, _ = tr.oob_hatasi(ytr)
        sonuc.setdefault(("rf", B), []).append(
            (np.mean(tr.tahmin(Xte) != yte), oobr))
for key, v in sonuc.items():
    if key[0] == "tek":
        a = np.array(v)
        print("tek agac            test=%.4f +- %.4f"
              % (a.mean(), a.std()))
    else:
        a = np.array(v)
        extra = ""
        if key[0] == "torba":
            extra = "  sure=%.2fs" % a[:, 2].mean()
            a = a[:, :2]
        print("%-6s B=%3d  test=%.4f +- %.4f   OOB=%.4f +- %.4f%s"
              % (key[0], key[1], a[:, 0].mean(), a[:, 0].std(),
                 a[:, 1].mean(), a[:, 1].std(), extra))

print("\n== sklearn OOB karsilastirma (tohum 0, B=50)")
Xtr, Xte, ytr, yte = veri(0)
bg = BaggingClassifier(DecisionTreeClassifier(), n_estimators=50,
                       oob_score=True, random_state=0).fit(Xtr, ytr)
rf = RandomForestClassifier(n_estimators=50, oob_score=True,
                            random_state=0).fit(Xtr, ytr)
print("sk bagging OOB dogruluk=%.4f test=%.4f"
      % (bg.oob_score_, bg.score(Xte, yte)))
print("sk RF      OOB dogruluk=%.4f test=%.4f"
      % (rf.oob_score_, rf.score(Xte, yte)))
print("benim OOB hatasi (tohum 0, RF B=50) = %.4f"
      % Torba(B=50, max_ozellik=4, seed=0).fit(Xtr, ytr).oob_hatasi(ytr)[0])

print("\n== sklearn RF: agac sayisi - test hatasi (5 tohum)")
rows = []
for B in [1, 2, 5, 10, 20, 50, 100, 200]:
    e = []
    for sd in range(5):
        Xtr, Xte, ytr, yte = veri(sd)
        rf = RandomForestClassifier(n_estimators=B, random_state=sd,
                                    n_jobs=-1).fit(Xtr, ytr)
        e.append(1 - rf.score(Xte, yte))
    rows.append((B, np.mean(e), np.std(e)))
    print("B=%3d  test hatasi %.4f +- %.4f" % rows[-1])
with open(os.path.join(VERI, "b59_rf_agac.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["agac_sayisi", "test_hata_ort", "test_hata_ss"])
    w.writerows(rows)
