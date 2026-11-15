import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import (StratifiedKFold,
                                     StratifiedGroupKFold)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from ihadata import uret, kayit_tablosu
from temizle import temizle
from ozellik import ozellik_tablosu, SAYISAL
from dengesiz import smote

df, tr = uret(56)
kayit = kayit_tablosu()
temiz = ozellik_tablosu(temizle(df, kayit)[0])
ham = df.copy()
ham["irt_fark"] = 0.0

RAW_NUM = ["irtifa", "hiz", "batarya_v", "akim_a", "sicaklik_c",
           "titresim_g"]
RAW_CAT = ["gorev", "hata_kodu"]
CLEAN_CAT = ["gorev"]

def pre(num, cat, ind=True):
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median",
                                            add_indicator=ind),
                              StandardScaler()), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])

def boru(num, cat, cw=None, ind=True):
    return make_pipeline(pre(num, cat, ind),
                         LogisticRegression(max_iter=3000,
                                            class_weight=cw))

def kos(ad, X, y, g, cv, fn, mod="normal"):
    auc, ap = [], []
    for tr_i, te_i in cv.split(X, y, g):
        if mod == "normal":
            m = fn().fit(X.iloc[tr_i], y[tr_i])
            pr = m.predict_proba(X.iloc[te_i])[:, 1]
            yt = y[te_i]
        elif mod == "smote_egitim":
            p = fn()[0].fit(X.iloc[tr_i])
            Xs, ys = smote(p.transform(X.iloc[tr_i]), y[tr_i],
                           np.random.default_rng(56))
            m = LogisticRegression(max_iter=3000).fit(Xs, ys)
            pr = m.predict_proba(p.transform(X.iloc[te_i]))[:, 1]
            yt = y[te_i]
        auc.append(roc_auc_score(yt, pr))
        ap.append(average_precision_score(yt, pr))
    print("%-40s AUC %.3f+-%.3f  AP %.3f+-%.3f" % (
        ad, np.mean(auc), np.std(auc), np.mean(ap), np.std(ap)))

def tum_veride_smote(ad, X, y, cv):
    p = pre(SAYISAL, CLEAN_CAT).fit(X)
    Z = p.transform(X)
    Zs, ys = smote(Z, y, np.random.default_rng(56))
    auc, ap = [], []
    for tr_i, te_i in cv.split(Zs, ys):
        m = LogisticRegression(max_iter=3000).fit(Zs[tr_i], ys[tr_i])
        pr = m.predict_proba(Zs[te_i])[:, 1]
        auc.append(roc_auc_score(ys[te_i], pr))
        ap.append(average_precision_score(ys[te_i], pr))
    print("%-40s AUC %.3f+-%.3f  AP %.3f+-%.3f" % (
        ad, np.mean(auc), np.std(auc), np.mean(ap), np.std(ap)))

yt_ = temiz["ariza"].values
gt_ = temiz["ucus_no"].values
yh_ = ham["ariza"].values
gh_ = ham["ucus_no"].values
import warnings
warnings.filterwarnings('ignore', message='The groups')
satir = StratifiedKFold(5, shuffle=True, random_state=56)
grup = StratifiedGroupKFold(5, shuffle=True, random_state=56)

kos("R1 kirli, satir CV, hata dahil", ham, yh_, gh_, satir,
    lambda: boru(RAW_NUM, RAW_CAT))
kos("R2 kirli, grup CV, hata dahil", ham, yh_, gh_, grup,
    lambda: boru(RAW_NUM, RAW_CAT))
kos("R3 kirli, grup CV, hata haric", ham, yh_, gh_, grup,
    lambda: boru(RAW_NUM, ["gorev"]))
kos("R4 temiz, grup CV, hata dahil", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT + ["hata_kodu"]))
kos("R5a temiz, ham ozellik (temizlik etkisi)", temiz, yt_, gt_,
    grup, lambda: boru(RAW_NUM, ["gorev"]))
kos("R5 temiz, grup CV, hata haric", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT))
kos("R5b temiz, eksiklik gostergesi yok", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT, ind=False))
kos("R6 R5 + class_weight=balanced", temiz, yt_, gt_, grup,
    lambda: boru(SAYISAL, CLEAN_CAT, cw="balanced"))
kos("R7 R5 + SMOTE (sadece egitim)", temiz, yt_, gt_, grup,
    lambda: (pre(SAYISAL, CLEAN_CAT),), mod="smote_egitim")
kos("R9 satir CV, SMOTE sadece egitim", temiz, yt_, gt_, satir,
    lambda: (pre(SAYISAL, CLEAN_CAT),), mod="smote_egitim")
kos("R10 satir CV, orneklemesiz", temiz, yt_, gt_, satir,
    lambda: boru(SAYISAL, CLEAN_CAT))
tum_veride_smote("R8 satir CV, SMOTE TUM veride (SIZINTI)",
                 temiz[SAYISAL + CLEAN_CAT], yt_, satir)
