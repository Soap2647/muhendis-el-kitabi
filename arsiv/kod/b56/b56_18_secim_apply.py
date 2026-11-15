import time
import warnings
import numpy as np
import pandas as pd
from sklearn.feature_selection import (SelectKBest, RFE,
                                       SelectFromModel,
                                       mutual_info_classif)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (StratifiedGroupKFold,
                                     cross_val_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from ihadata import uret, kayit_tablosu
from temizle import temizle
from ozellik import ozellik_tablosu, SAYISAL

warnings.filterwarnings("ignore")
df, _ = uret(56)
t = ozellik_tablosu(temizle(df, kayit_tablosu())[0])
X = t[SAYISAL]
y = t["ariza"].values
g = t["ucus_no"].values
cv = StratifiedGroupKFold(5, shuffle=True, random_state=56)


def bilgi(a, b):
    return mutual_info_classif(a, b, random_state=56)


def hat(ad, sec):
    p = make_pipeline(SimpleImputer(strategy="median",
                                    add_indicator=True),
                      StandardScaler(), sec,
                      LogisticRegression(max_iter=3000))
    s = cross_val_score(p, X, y, groups=g, cv=cv,
                        scoring="average_precision")
    print("%-26s AP %.3f+-%.3f" % (ad, s.mean(), s.std()))
    return p


hat("hepsi (secim yok)", SelectKBest(bilgi, k="all"))
filtre = hat("filtre (karsilikli bilgi)",
             SelectKBest(bilgi, k=5))
hat("sarmalayici (RFE)", RFE(LogisticRegression(max_iter=3000),
                             n_features_to_select=5))
hat("gomulu (L1)", SelectFromModel(LogisticRegression(
    penalty="l1", solver="liblinear", C=0.1)))

# Secilen oznitelikleri isimleriyle yaz
adimlar = make_pipeline(SimpleImputer(strategy="median",
                                      add_indicator=True),
                        StandardScaler(),
                        SelectKBest(bilgi, k=5)).fit(X, y)
isimler = adimlar[0].get_feature_names_out(SAYISAL)
secilen = adimlar[2].get_support()
print("filtre secilen:")
for ad in isimler[secilen]:
    print("  ", ad)
Z = StandardScaler().fit_transform(
    SimpleImputer(strategy="median", add_indicator=True)
    .fit_transform(X))
l1 = LogisticRegression(penalty="l1", solver="liblinear", C=0.1)
l1.fit(Z, y)
print("L1 sifir olmayan katsayi:", int((l1.coef_ != 0).sum()),
      "/", Z.shape[1])
rfe = RFE(LogisticRegression(max_iter=3000),
          n_features_to_select=5).fit(Z, y)
print("RFE secilen:")
for ad in isimler[rfe.support_]:
    print("  ", ad)
