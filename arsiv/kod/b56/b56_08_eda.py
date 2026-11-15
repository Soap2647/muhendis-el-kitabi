import csv, os
import numpy as np
import pandas as pd
from ihadata import uret

df, tr = uret(56)
print("satir, sutun:", df.shape)
print("eksik sayisi:")
print(df.isna().sum()[lambda s: s > 0].to_dict())
print("sicaklik = -999 :", int((df.sicaklik_c == -999).sum()))
print("arac_id ham degerler:", df.arac_id.nunique())
print("gorev ham degerler:")
print("  " + ", ".join(sorted(df.gorev.unique())))
print("hata_kodu ham degerler:")
degerler = sorted(df.hata_kodu.unique())
print("  " + ", ".join("'%s'" % v for v in degerler))
print("zaman bicimi (Z):", int(df.zaman.str.endswith("Z").sum()),
      " (+03:00):", int(df.zaman.str.endswith("+03:00").sum()))
print("tam kopya satir:", int(df.duplicated().sum()))
print("ariza orani: %.4f" % df.ariza.mean())

ft = df.irtifa.values
print("irtifa <200 (m benzeri):", int((ft < 200).sum()),
      " >200:", int((ft >= 200).sum()))
bins = np.arange(0, 1400, 50)
sayi, _ = np.histogram(ft, bins=bins)
print("histogram tepe baslari (50 m kutu):",
      [int(bins[k]) for k in range(1, len(sayi) - 1)
       if sayi[k] > sayi[k - 1] and sayi[k] >= sayi[k + 1]
       and sayi[k] > 500])

tr_ft = tr.birim_ft.values
print("ft satirlari (truth):", int(tr_ft.sum()))
print("arac medyan irtifa:")
med = (df.assign(a=df.arac_id.str.strip().str.upper())
         .groupby("a")["irtifa"].median().round(1))
for k in range(0, 10, 2):
    print("  %-7s %6.1f   %-7s %6.1f" % (
        med.index[k], med.iloc[k], med.index[k + 1], med.iloc[k + 1]))

yol = os.path.join("D:/Mevcut Projeler/Kitap/engine/veri",
                   "b56_irtifa_dagilim.csv")
with open(yol, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["irtifa", "birim_ft"])
    for a, b in zip(ft, tr_ft):
        w.writerow(["%.3f" % a, int(b)])
print("csv: b56_irtifa_dagilim.csv")

kirlilik = df.loc[df.ucus_no == 3]
for kol in ["batarya_v", "titresim_g", "sicaklik_c"]:
    eks = df[kol].isna()
    print("%-12s eksikken ariza %.4f  dolu iken %.4f" % (
        kol, df.loc[eks, "ariza"].mean(),
        df.loc[~eks, "ariza"].mean()))
print("ucus 3 satir:", len(kirlilik),
      " ariza:", int(kirlilik.ariza.sum()))
