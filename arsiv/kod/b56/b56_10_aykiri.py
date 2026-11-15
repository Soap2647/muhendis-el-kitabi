import csv
import os
import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle

df, tr = uret(56)
temiz, _ = temizle(df, kayit_tablosu(), tr, aykiri_sil=False)
kept = temiz["kaynak"].values
gps_t = pd.Series(tr.gps.values[kept], index=temiz.index)
ariza = temiz["ariza"]
x = temiz["irtifa"].dropna()

# 1) Tum veri uzerinde IQR
q1, q3 = x.quantile([0.25, 0.75])
iqr = q3 - q1
alt, ust = q1 - 1.5 * iqr, q3 + 1.5 * iqr
f_iqr = (temiz.irtifa < alt) | (temiz.irtifa > ust)

# 2) Tum veri uzerinde robust z (medyan ve MAD)
med = x.median()
mad = (x - med).abs().median()
f_z = (temiz.irtifa - x.mean()).abs() / x.std() > 3
f_rz = (0.6745 * (temiz.irtifa - med) / mad).abs() > 3.5

# 3) Ucus ici robust z (bu uçusun kendi medyani)
ref_med = temiz.groupby("ucus_no")["irtifa"].transform("median")
sapma = (temiz.irtifa - ref_med).abs()
ref_mad = sapma.groupby(temiz["ucus_no"]).transform("median")
f_frz = (0.6745 * (temiz.irtifa - ref_med) / ref_mad).abs() > 3.5

print("Q1=%.1f Q3=%.1f IQR=%.1f" % (q1, q3, iqr))
print("alt=%.1f ust=%.1f" % (alt, ust))
print("medyan=%.1f MAD=%.2f" % (med, mad))
print("ort=%.1f ss=%.2f" % (x.mean(), x.std()))
print("%-18s %6s %6s %6s %6s" % ("yontem", "bayrak", "gps",
                                 "ariza", "digeri"))
for ad, f in [("global z (3 ss)", f_z), ("global IQR", f_iqr),
              ("global robust z", f_rz),
              ("ucus-ici robust z", f_frz)]:
    print("%-18s %6d %6d %6d %6d" % (
        ad, int(f.sum()), int((f & gps_t).sum()),
        int((f & (ariza == 1)).sum()),
        int((f & (gps_t == 0) & (ariza == 0)).sum())))

print("nedensel bayrak = gps:",
      int((temiz.nedensel_bayrak & gps_t).sum()), "/",
      int(temiz.nedensel_bayrak.sum()))

# Grafik icin bir arizali ucus seç ve CSV'ye yaz
hedef = None
for u in sorted(temiz.ucus_no.unique()):
    g = temiz[temiz.ucus_no == u]
    if g.ariza.sum() > 0 and g.arac_id.iloc[0] == "IHA-01":
        hedef = u
        break
g = temiz[temiz.ucus_no == hedef]
yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_aykiri_ucus.csv")
with open(yol, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["adim", "irtifa", "gps", "ariza", "iqr", "alt",
                "ust"])
    for k, (i, r) in enumerate(g.iterrows()):
        w.writerow([k, "%.3f" % r.irtifa, int(gps_t.loc[i]),
                    int(r.ariza), int(f_iqr.loc[i]),
                    "%.3f" % alt, "%.3f" % ust])
print("ornek ucus:", hedef, "satir:", len(g))
