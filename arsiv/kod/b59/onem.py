# onem.py -- safsizlik onemi, permutasyon onemi ve kismi bagimlilik
import csv
import warnings
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.inspection import partial_dependence
from uav import uav_veri

warnings.filterwarnings("ignore")
df, y = uav_veri()
a, b, c, d = train_test_split(df, y, test_size=0.3, random_state=0,
                              stratify=y)
ct = make_column_transformer(
    (OneHotEncoder(handle_unknown="ignore"), ["gorev", "ortam"]),
    remainder="passthrough")
Xa = ct.fit_transform(a)
Xb = ct.transform(b)
isim = [s.split("__")[-1] for s in ct.get_feature_names_out()]
rf = RandomForestClassifier(n_estimators=300, random_state=0,
                            n_jobs=-1).fit(Xa, c)
saf = rf.feature_importances_
per = permutation_importance(rf, Xb, d, n_repeats=20, random_state=0,
                             scoring="roc_auc")
sira = np.argsort(-saf)
print("%-18s %10s %12s" % ("oznitelik", "safsizlik", "permutasyon"))
for i in sira:
    print("%-18s %10.4f %12.4f"
          % (isim[i], saf[i], per.importances_mean[i]))
with open("D:/Mevcut Projeler/Kitap/engine/veri/b59_onem.csv", "w",
          newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["oznitelik", "safsizlik_onemi", "permutasyon_onemi",
                "permutasyon_ss"])
    for i in sira:
        w.writerow([isim[i], "%.5f" % saf[i],
                    "%.5f" % per.importances_mean[i],
                    "%.5f" % per.importances_std[i]])

# Kismi bagimlilik: titresim_rms (seri_no olmadan, HistGB)
maske = np.array([n != "seri_no" for n in isim])
hg = HistGradientBoostingClassifier(random_state=0)
hg.fit(Xa[:, maske], c)
j = list(np.array(isim)[maske]).index("titresim_rms")
pdp = partial_dependence(hg, Xa[:, maske], features=[j],
                         grid_resolution=8, kind="average",
                         response_method="predict_proba",
                         method="brute")
for g, v in zip(pdp["grid_values"][0], pdp["average"][0]):
    print("titresim=%.3f  ortalama olasilik=%.4f" % (g, v))
