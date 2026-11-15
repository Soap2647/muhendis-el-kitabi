import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def varyant(X, y, cv, olcek_tum, secim_tum):
    model = LogisticRegression(max_iter=1000)
    if olcek_tum:
        X = StandardScaler().fit_transform(X)
    if secim_tum:
        X = SelectKBest(f_classif, k=20).fit_transform(X, y)
        return cross_val_score(model, X, y, cv=cv).mean()
    adimlar = []
    if not olcek_tum:
        adimlar.append(StandardScaler())
    adimlar += [SelectKBest(f_classif, k=20), model]
    boru = make_pipeline(*adimlar)
    return cross_val_score(boru, X, y, cv=cv).mean()

print("tohum  V1:hepsi  V2:olcek  V3:secim  V4:temiz")
ort = np.zeros(4)
for sd in range(20):
    rng = np.random.default_rng(sd)
    X = rng.normal(size=(100, 5000))
    y = np.repeat([0, 1], 50)
    rng.shuffle(y)
    cv = StratifiedKFold(5, shuffle=True, random_state=sd)
    r = [varyant(X, y, cv, True, True),     # ikisi de sizinti
         varyant(X, y, cv, True, False),    # yalnizca secim doğru
         varyant(X, y, cv, False, True),    # yalnizca olcek doğru
         varyant(X, y, cv, False, False)]   # ikisi de doğru
    ort += np.array(r) / 20
    if sd < 5:
        print("%5d   %.3f   %.3f   %.3f   %.3f" % (sd, *r))
print("ortalama (20 tohum):", np.round(ort, 3))
