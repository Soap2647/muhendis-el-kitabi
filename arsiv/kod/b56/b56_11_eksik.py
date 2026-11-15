import csv, os
import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.impute import KNNImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

X, y = load_diabetes(return_X_y=True)
n = len(y)
age, bmi = X[:, 0], X[:, 2]
rank_age = age.argsort().argsort() / (n - 1)
rank_bmi = bmi.argsort().argsort() / (n - 1)

def maske(mek, rng, p=0.2):
    if mek == "MCAR":                    # tamamen rastgele
        pr = np.full(n, p)
    elif mek == "MAR":                   # yasa bagli (gozlenen)
        pr = 2 * p * rank_age
    else:                                # MNAR: bmi'ye bagli
        pr = 2 * p * rank_bmi
    return rng.random(n) < pr

def yontemler(Xm):
    out = {}
    obs = ~np.isnan(Xm[:, 2])
    out["silme"] = Xm[obs, 2]
    for ad, sta in [("ortalama", "mean"), ("medyan", "median")]:
        v = Xm[:, 2].copy()
        v[~obs] = np.nanmean(v) if sta == "mean" else np.nanmedian(v)
        out[ad] = v
    out["knn"] = KNNImputer(n_neighbors=5).fit_transform(Xm)[:, 2]
    return out, obs

print("%-6s %-10s %8s %8s %8s" % ("mek.", "yontem", "sd oran",
                                  "sapma", "kor(y)"))
sonuc = {}
for mek in ["MCAR", "MAR", "MNAR"]:
    acc = {}
    for s in range(200):
        rng = np.random.default_rng(s)
        m = maske(mek, rng)
        Xm = X.copy()
        Xm[m, 2] = np.nan
        out, obs = yontemler(Xm)
        for k, v in out.items():
            yy = y[obs] if k == "silme" else y
            sd_r = v.std() / bmi.std()
            sap = (v.mean() - bmi.mean()) / bmi.std()
            kor = np.corrcoef(v, yy)[0, 1]
            acc.setdefault(k, []).append((sd_r, sap, kor))
    for k, vals in acc.items():
        a = np.array(vals).mean(axis=0)
        print("%-6s %-10s %8.3f %8.2f %8.3f"
              % (mek, k, a[0], a[1], a[2]))
        sonuc[(mek, k)] = a

kayip_ind = []
for s in range(30):
    rng = np.random.default_rng(s)
    m = maske("MNAR", rng)
    Xm = X.copy()
    Xm[m, 2] = np.nan
    tr_i = np.arange(n) < int(0.7 * n)
    med = np.nanmedian(Xm[tr_i, 2])
    b = np.where(np.isnan(Xm[:, 2]), med, Xm[:, 2])
    ind = np.isnan(Xm[:, 2]).astype(float)
    r1 = LinearRegression().fit(b[tr_i, None], y[tr_i])
    r2 = LinearRegression().fit(np.c_[b, ind][tr_i], y[tr_i])
    kayip_ind.append((
        r2_score(y[~tr_i], r1.predict(b[~tr_i, None])),
        r2_score(y[~tr_i], r2.predict(np.c_[b, ind][~tr_i]))))
kayip_ind = np.array(kayip_ind).mean(axis=0)
print("MNAR test R2 (sadece bmi): %.3f" % kayip_ind[0])
print("MNAR test R2 (bmi+indikator): %.3f" % kayip_ind[1])

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_eksik_olcum.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["mekanizma", "yontem", "sd_orani", "sapma",
                "korelasyon"])
    for (mek, k), a in sonuc.items():
        w.writerow([mek, k, "%.4f" % a[0], "%.4f" % a[1],
                    "%.4f" % a[2]])
print("csv yazildi")
