# kiyas.py -- modellerin test performansi (5 tohum, ayni bolunmeler)
import csv
import time
import warnings
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from uav import uav_veri

warnings.filterwarnings("ignore")
KAT = ["gorev", "ortam"]


def modeller():
    return {
        "taban": DummyClassifier(strategy="prior"),
        "lojistik": make_pipeline(StandardScaler(),
                                  LogisticRegression(max_iter=2000)),
        "MLP(32)": make_pipeline(StandardScaler(),
            MLPClassifier((32,), max_iter=1000, random_state=0,
                          early_stopping=True)),
        "RF": RandomForestClassifier(n_estimators=300, random_state=0,
                                     n_jobs=-1),
        "HistGB": HistGradientBoostingClassifier(random_state=0),
        "XGBoost": XGBClassifier(n_estimators=300, max_depth=4,
                                 learning_rate=0.05, random_state=0,
                                 n_jobs=4),
        "LightGBM": LGBMClassifier(n_estimators=300, max_depth=4,
                                   learning_rate=0.05, random_state=0,
                                   verbose=-1, n_jobs=4),
    }


def kat_donustur(m):
    # Kategorik sutunlar icin one-hot kodlama (sadece UAV verisinde)
    ct = make_column_transformer(
        (OneHotEncoder(handle_unknown="ignore"), KAT),
        remainder="passthrough")
    return make_pipeline(ct, m)


df, y_u = uav_veri()
bc = load_breast_cancer(as_frame=True)
veriler = [
    ("meme kanseri", bc.frame.drop(columns="target"),
     bc.frame["target"].values, False),
    ("IHA bakim", df.drop(columns=["seri_no"]), y_u, True),
]
satirlar = []
for ad, X, y, katli in veriler:
    print("== %s" % ad)
    for mad in modeller():
        acc, auc, sure = [], [], []
        for sd in range(5):
            a, b, c, d = train_test_split(X, y, test_size=0.3,
                                          random_state=sd, stratify=y)
            m = modeller()[mad]
            if katli:
                m = kat_donustur(m)
            t0 = time.perf_counter()
            m.fit(a, c)
            sure.append(time.perf_counter() - t0)
            p = m.predict_proba(b)[:, 1]
            acc.append(accuracy_score(d, (p >= 0.5).astype(int)))
            auc.append(roc_auc_score(d, p))
        satirlar.append((ad, mad, np.mean(acc), np.std(acc),
                         np.mean(auc), np.std(auc), np.mean(sure)))
        print("%-8s acc=%.4f+-%.4f  AUC=%.4f+-%.4f  sure=%.3fs"
              % satirlar[-1][1:])
with open("D:/Mevcut Projeler/Kitap/engine/veri/"
          "b59_model_karsilastirma.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["veri", "model", "dogruluk_ort", "dogruluk_ss",
                "auc_ort", "auc_ss", "sure_ort_s"])
    for r in satirlar:
        w.writerow([r[0], r[1]] + ["%.5f" % v for v in r[2:]])
