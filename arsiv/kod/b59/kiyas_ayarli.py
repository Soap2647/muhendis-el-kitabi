# kiyas_ayarli.py -- tavan (gercek p ile AUC) ve CV ile ayarli GBM
import warnings
import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from uav import uav_veri

warnings.filterwarnings("ignore")
KAT = ["gorev", "ortam"]
df, y, p_gercek = uav_veri(p_dondur=True)
print("gercek olasilik p ile AUC (tavan): %.4f"
      % roc_auc_score(y, p_gercek))

izgara = {"max_depth": [2, 3, 4], "n_estimators": [100, 300],
          "learning_rate": [0.03, 0.1]}
X = df.drop(columns=["seri_no"])
for ad, taban, on in [
        ("XGBoost", XGBClassifier(random_state=0, n_jobs=4),
         "xgbclassifier"),
        ("LightGBM", LGBMClassifier(random_state=0, verbose=-1,
                                    n_jobs=4), "lgbmclassifier")]:
    acc, auc = [], []
    for sd in range(5):
        a, b, c, d = train_test_split(X, y, test_size=0.3,
                                      random_state=sd, stratify=y)
        ct = make_column_transformer(
            (OneHotEncoder(handle_unknown="ignore"), KAT),
            remainder="passthrough")
        m = make_pipeline(ct, taban)
        # Ayar yalnizca egitim kumesinde, 3 katli CV ile yapilir
        gs = GridSearchCV(m, {on + "__" + k: v
                              for k, v in izgara.items()},
                          cv=3, scoring="roc_auc")
        gs.fit(a, c)
        p = gs.predict_proba(b)[:, 1]
        acc.append(accuracy_score(d, (p >= 0.5).astype(int)))
        auc.append(roc_auc_score(d, p))
    print("%-8s CV ayarli: acc=%.4f+-%.4f  AUC=%.4f+-%.4f"
          % (ad, np.mean(acc), np.std(acc), np.mean(auc),
             np.std(auc)))
