# deney1b.py -- bag (tie) kontrolu ve alfa secimi (yalnizca egitim, CV)
import numpy as np
from agac import KararAgaci
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier

X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)

def gini_toplam(model_yaprak_sayilari):
    return model_yaprak_sayilari

print("== Egitim safsizligi toplami (agirlikli Gini, yapraklar)")
for d in [2, 3, 4, 5]:
    s = DecisionTreeClassifier(max_depth=d, random_state=0).fit(Xtr, ytr)
    t = s.tree_
    leaves = t.children_left == -1
    sk_top = np.sum(t.weighted_n_node_samples[leaves]
                    * t.impurity[leaves])
    # benim agacim: yaprak Gini'lerini ayni sekilde topla
    m = KararAgaci(max_derinlik=d).fit(Xtr, ytr)
    tot = 0.0
    def gez(dg, Xs, ys):
        global tot
        if dg.sol is None:
            p = dg.deger
            n = len(ys)
            tot += n * (1 - np.sum(p * p))
            return
        L = Xs[:, dg.ozellik] <= dg.esik
        gez(dg.sol, Xs[L], ys[L]); gez(dg.sag, Xs[~L], ys[~L])
    gez(m.kok, Xtr, ytr)
    print("d=%d  sk=%.4f  benim=%.4f" % (d, sk_top, tot))

print("\n== Alfa secimi: yalnizca egitim verisinde 5-katli CV")
path = DecisionTreeClassifier(random_state=0).cost_complexity_pruning_path(
    Xtr, ytr)
alfalar = np.unique(np.round(path.ccp_alphas[:-1], 5))
skorlar = []
for a in alfalar:
    cv = cross_val_score(DecisionTreeClassifier(ccp_alpha=a, random_state=0),
                         Xtr, ytr, cv=5)
    skorlar.append(cv.mean())
i = int(np.argmax(skorlar))
print("CV en iyi alfa=%.5f, CV dogruluk=%.4f" % (alfalar[i], skorlar[i]))
t = DecisionTreeClassifier(ccp_alpha=alfalar[i], random_state=0).fit(Xtr, ytr)
print("secilen alfa ile test=%.4f yaprak=%d" % (t.score(Xte, yte),
      t.get_n_leaves()))
t0 = DecisionTreeClassifier(random_state=0).fit(Xtr, ytr)
print("budamasiz test=%.4f yaprak=%d" % (t0.score(Xte, yte),
      t0.get_n_leaves()))
