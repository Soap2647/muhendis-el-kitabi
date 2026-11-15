# deney4_karsilastirma.py -- model kiyasi, onem, kismi bagimlilik
import csv, os, time, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.inspection import permutation_importance, partial_dependence
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from uav import uav_veri
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
KAT = ["gorev", "ortam"]

def modeller():
    return {
        "taban (cogunluk)": DummyClassifier(strategy="prior"),
        "lojistik": make_pipeline(StandardScaler(),
                                  LogisticRegression(max_iter=2000)),
        "MLP (32)": make_pipeline(StandardScaler(),
            MLPClassifier((32,), max_iter=1000, random_state=0,
                          early_stopping=True)),
        "rastgele orman": RandomForestClassifier(n_estimators=300,
                                                 random_state=0,
                                                 n_jobs=-1),
        "HistGB": HistGradientBoostingClassifier(random_state=0),
        "XGBoost": XGBClassifier(n_estimators=300, learning_rate=0.05,
                                 max_depth=4, random_state=0, n_jobs=4),
        "LightGBM": LGBMClassifier(n_estimators=300, learning_rate=0.05,
                                   max_depth=4, random_state=0,
                                   verbose=-1, n_jobs=4),
    }

def ayir_pipe(m, katli, df):
    if katli:
        ct = make_column_transformer(
            (OneHotEncoder(handle_unknown="ignore"), KAT),
            remainder="passthrough")
        return make_pipeline(ct, m)
    return m

def sayisal_df(X_df):
    return X_df

print("== 1. Model kiyasi (5 tohum; test; ort +- ss)")
sonuclar = []
# veri 1: breast cancer (sayisal)
bc = load_breast_cancer(as_frame=True)
veriler = {"meme kanseri": (bc.frame.drop(columns="target"),
                            bc.frame["target"].values, False),
           "IHA bakim": None}
df_u, y_u, p_u = uav_veri(p_dondur=True)
for ad in ["meme kanseri", "IHA bakim"]:
    if ad == "meme kanseri":
        X = bc.frame.drop(columns="target"); y = bc.frame["target"].values
        katli = False
    else:
        X = df_u.drop(columns=["seri_no"]); y = y_u
        katli = True
    for mad, m0 in modeller().items():
        acc, auc, ll, sure = [], [], [], []
        for sd in range(5):
            a, b, c, d = train_test_split(X, y, test_size=0.3,
                                          random_state=sd, stratify=y)
            m = ayir_pipe(modeller()[mad], katli, a)
            t0 = time.perf_counter()
            m.fit(a, c)
            sure.append(time.perf_counter() - t0)
            p = m.predict_proba(b)[:, 1]
            acc.append(accuracy_score(d, (p >= 0.5).astype(int)))
            auc.append(roc_auc_score(d, p))
            ll.append(log_loss(d, p))
        sonuclar.append((ad, mad, np.mean(acc), np.std(acc),
                         np.mean(auc), np.std(auc), np.mean(ll),
                         np.mean(sure)))
        print("%-13s %-17s acc=%.4f+-%.4f AUC=%.4f+-%.4f "
              "logloss=%.4f sure=%.3fs" % sonuclar[-1])
with open(os.path.join(VERI, "b59_model_karsilastirma.csv"), "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["veri", "model", "dogruluk_ort", "dogruluk_ss",
                "auc_ort", "auc_ss", "logloss_ort", "sure_ort_s"])
    for r in sonuclar:
        w.writerow([r[0], r[1]] + ["%.5f" % v for v in r[2:]])

print("\n== 1b. Ulasilabilir tavan (gercek p ile AUC) ve CV ayari")
print("gercek olasilik p ile AUC (tavan): %.4f"
      % roc_auc_score(y_u, p_u))
from sklearn.model_selection import GridSearchCV
izgara = {"max_depth": [2, 3, 4], "n_estimators": [100, 300],
          "learning_rate": [0.03, 0.1]}
ayarlar = [("XGBoost", XGBClassifier(random_state=0, n_jobs=4),
            "xgbclassifier"),
           ("LightGBM", LGBMClassifier(random_state=0, verbose=-1,
                                       n_jobs=4), "lgbmclassifier")]
for ad, base, on in ayarlar:
    acc, auc = [], []
    for sd in range(5):
        a, b, c, d = train_test_split(df_u, y_u, test_size=0.3,
                                      random_state=sd, stratify=y_u)
        m = ayir_pipe(base, True, a)
        gs = GridSearchCV(m, {on + "__" + k: v
                              for k, v in izgara.items()},
                          cv=3, scoring="roc_auc")
        gs.fit(a, c)
        p = gs.predict_proba(b)[:, 1]
        acc.append(accuracy_score(d, (p >= 0.5).astype(int)))
        auc.append(roc_auc_score(d, p))
    print("%-9s CV ayarli: acc=%.4f+-%.4f AUC=%.4f+-%.4f"
          % (ad, np.mean(acc), np.std(acc), np.mean(auc), np.std(auc)))

print("\n== 2. Oznitelik onemi: safsizlik vs permutasyon (seri_no)")
X = df_u.copy(); y = y_u
a, b, c, d = train_test_split(X, y, test_size=0.3, random_state=0,
                              stratify=y)
ct = make_column_transformer((OneHotEncoder(handle_unknown="ignore"),
                              KAT), remainder="passthrough")
Xa = ct.fit_transform(a)
Xb = ct.transform(b)
isimler = list(ct.get_feature_names_out())
rf = RandomForestClassifier(n_estimators=300, random_state=0,
                            n_jobs=-1).fit(Xa, c)
imp = rf.feature_importances_
pi = permutation_importance(rf, Xb, d, n_repeats=20, random_state=0,
                            scoring="roc_auc")
sira = np.argsort(-imp)
print("%-28s %10s %10s" % ("oznitelik", "safsizlik", "permut."))
satirlar = []
for i in sira:
    satirlar.append((isimler[i], imp[i], pi.importances_mean[i],
                     pi.importances_std[i]))
for s in satirlar:
    print("%-28s %10.4f %10.4f" % (s[0], s[1], s[2]))
with open(os.path.join(VERI, "b59_onem.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["oznitelik", "safsizlik_onemi", "permutasyon_onemi",
                "permutasyon_ss"])
    for s in satirlar:
        w.writerow([s[0], "%.5f" % s[1], "%.5f" % s[2], "%.5f" % s[3]])

print("\n== 3. Kismi bagimlilik: titresim_rms (HistGB)")
maske = np.array([not n.endswith("seri_no") for n in isimler])
hg = HistGradientBoostingClassifier(random_state=0).fit(Xa[:, maske], c)
j = [n for n in np.array(isimler)[maske]].index(
    "remainder__titresim_rms")
pdp = partial_dependence(hg, Xa[:, maske], features=[j],
                         grid_resolution=8, kind="average", response_method="predict_proba", method="brute")
for g, v in zip(pdp["grid_values"][0], pdp["average"][0]):
    print("titresim=%.3f  ortalama olasilik=%.4f" % (g, v))
