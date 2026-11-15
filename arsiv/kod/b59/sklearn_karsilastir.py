# sklearn_karsilastir.py -- benim agacim ile sklearn DecisionTree
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from agac import KararAgaci

X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
for d in [2, 3, 4, 5, None]:
    benim = KararAgaci(max_derinlik=d).fit(Xtr, ytr)
    sk = DecisionTreeClassifier(max_depth=d, random_state=0)
    sk.fit(Xtr, ytr)
    pb = benim.tahmin(Xte)
    ps = sk.predict(Xte)
    print("derinlik=%-4s benim=%.4f sklearn=%.4f yaprak=%d/%d "
          "ayni=%d/%d" % (d, np.mean(pb == yte), sk.score(Xte, yte),
          benim.yaprak_sayisi(), sk.get_n_leaves(),
          np.sum(pb == ps), len(ps)))

# Esitlik bagi: kokun sag cocugundaki iki adayin kazanci
from agac import en_iyi_bolme_siniflama
benim = KararAgaci(max_derinlik=2).fit(Xtr, ytr)
kok = benim.kok
alt = Xtr[:, kok.ozellik] > kok.esik
for j in [11, 21]:
    kz = en_iyi_bolme_siniflama(Xtr[alt, j], ytr[alt], 2, "gini", 1)
    print("ozellik %2d kazanc=%.5f esik=%.3f" % (j, kz[0], kz[1]))
