import csv
import os
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (KFold, StratifiedKFold,
                                     GroupKFold, cross_val_score,
                                     train_test_split)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

HERE = os.path.dirname(os.path.abspath(__file__))

def secim_sizintisi(seed):
    # Gercek sinyal yok: X ve y bagimsiz. Dogru tahmin oranı 0.5.
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(100, 5000))
    y = np.repeat([0, 1], 50)
    rng.shuffle(y)
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    model = LogisticRegression(max_iter=1000)
    # SIZINTILI: 20 oznitelik tum veriyle seçilir, sonra CV
    Xs = SelectKBest(f_classif, k=20).fit_transform(X, y)
    sizinti = cross_val_score(model, Xs, y, cv=cv).mean()
    # DOGRU: secim, her egitim katinin icinde yapilir
    pipe = make_pipeline(SelectKBest(f_classif, k=20), model)
    dogru = cross_val_score(pipe, X, y, cv=cv).mean()
    return sizinti, dogru

def kopya_sizintisi(seed):
    # Her ornegin birebir bir kopyasi var (ayni satirlar)
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(200, 20))
    y = rng.integers(0, 2, 200)
    XX, yy = np.vstack([X, X]), np.concatenate([y, y])
    gg = np.concatenate([np.arange(200), np.arange(200)])
    Xtr, Xte, ytr, yte = train_test_split(
        XX, yy, test_size=0.25, random_state=seed)
    sizinti = KNeighborsClassifier(1).fit(Xtr, ytr).score(Xte, yte)
    tr, te = next(GroupKFold(4).split(XX, yy, gg))
    dogru = KNeighborsClassifier(1).fit(XX[tr], yy[tr]).score(
        XX[te], yy[te])
    return sizinti, dogru

def grup_sizintisi(seed):
    # 40 kisi, kisi basina 25 ornek; etiket kisiye bagli ve rastgele
    rng = np.random.default_rng(seed)
    kimlik = rng.normal(0, 3, (40, 50))
    g = np.repeat(np.arange(40), 25)
    X = kimlik[g] + rng.normal(0, 1, (1000, 50))
    y = rng.integers(0, 2, 40)[g]
    model = KNeighborsClassifier(1)
    rast = KFold(4, shuffle=True, random_state=seed)
    sizinti = cross_val_score(model, X, y, cv=rast).mean()
    dogru = cross_val_score(model, X, y, cv=GroupKFold(4),
                            groups=g).mean()
    return sizinti, dogru

SEEDS = range(20)
sonuc = []
for ad, fn in [("secim", secim_sizintisi), ("kopya", kopya_sizintisi),
               ("grup", grup_sizintisi)]:
    s = np.array([fn(sd) for sd in SEEDS])
    for j, yontem in enumerate(["sizintili", "dogru"]):
        m, sd = s[:, j].mean(), s[:, j].std(ddof=1)
        sonuc.append((ad, yontem, m, sd))
        print("%-6s %-10s ort=%.3f  ss=%.3f" % (ad, yontem, m, sd))

with open(os.path.join(HERE, "veri", "b54_sizinti.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["deney", "yontem", "ortalama", "ss"])
    w.writerows([(a, b, "%.4f" % c, "%.4f" % d)
                 for a, b, c, d in sonuc])
