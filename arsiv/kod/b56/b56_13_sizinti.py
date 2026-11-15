import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle
from ozellik import ozellik_tablosu, gecmis_olmayan_pencere
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score

df, tr = uret(56)
temiz, _ = temizle(df, kayit_tablosu())
ozel = ozellik_tablosu(temiz)

rng = np.random.default_rng(56)
def gelecek_testi(fn, adet=40):
    ok, bozuk = 0, 0
    sayilan = 0
    secimler = rng.choice(len(ozel), adet, replace=False)
    for k in secimler:
        t_satir = ozel.loc[k]
        bas = ozel.index[ozel.ucus_no == t_satir.ucus_no]
        if k not in bas or k == bas[-1]:
            continue
        ust = bas[bas > k]
        pert = temiz.copy()
        pert.loc[ust, "sicaklik_c"] = (pert.loc[ust, "sicaklik_c"]
                                       + 500)
        pert.loc[ust, "titresim_g"] = 9.0
        sayilan += 1
        a = fn(temiz).loc[k, "sic_ort30"]
        b = fn(pert).loc[k, "sic_ort30"]
        if np.isnan(a) and np.isnan(b):
            ok += 1
        elif abs(a - b) < 1e-9:
            ok += 1
        else:
            bozuk += 1
    return ok, bozuk, sayilan

print("gecmis pencere  (ok, bozuk):",
      gelecek_testi(lambda t: ozellik_tablosu(t)))
print("merkezi pencere (ok, bozuk):",
      gelecek_testi(gecmis_olmayan_pencere))

# hedef kodlama: ucus_no uzerinden naif ve out-of-fold karsilastirma
ucus = temiz["ucus_no"].values
y = temiz["ariza"].values
global_ort = y.mean()
naif = pd.Series(y).groupby(ucus).transform("mean").values
print("naif hedef kodlama AUC (kendi etiketi dahil): %.3f"
      % roc_auc_score(y, naif))
oof = np.full(len(y), global_ort)
for tr_i, te_i in GroupKFold(5).split(y, y, ucus):
    harita = pd.Series(y[tr_i]).groupby(ucus[tr_i]).mean()
    oof[te_i] = pd.Series(ucus[te_i]).map(harita).fillna(
        global_ort).values
print("out-of-fold hedef kodlama AUC:     %.3f"
      % roc_auc_score(y, oof))
