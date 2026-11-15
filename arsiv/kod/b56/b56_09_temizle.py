import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import gorev_normalize, hata_normalize, temizle

df, tr = uret(56)
kayit = kayit_tablosu()
print("gorev naif (lower) taninmayan:",
      int(gorev_normalize(df["gorev"], naif=True).isna().sum()))
print("gorev dogru taninmayan:",
      int(gorev_normalize(df["gorev"]).isna().sum()))
print("hata_kodu sonrasi:",
      hata_normalize(df["hata_kodu"]).value_counts().to_dict())

temiz, rap = temizle(df, kayit)
print("rapor:")
for k, v in rap.items():
    print("  %-18s %8d" % (k, v))
kept = temiz["kaynak"].values
print("kalan kopya (olmali 0):", int(tr.kopya.values[kept].sum()))
print("ft donusum dogrulama:",
      bool((tr.birim_ft.values[kept] ==
            temiz.firmware.eq("v2_ft").values).all()))
print("sicaklik -999 kalan:", int((temiz.sicaklik_c == -999).sum()))
print("temiz satir:", len(temiz), " kalan NaN irtifa:",
      int(temiz.irtifa.isna().sum()))
gps_say = int(tr.gps.values[kept].sum())
gps_yakalanan = int((tr.gps.values[kept] &
                     temiz.irtifa.isna().values).sum())
print("gps gercek:", gps_say, " yakalanan:", gps_yakalanan)

sayisal = ["irtifa", "hiz", "batarya_v", "akim_a", "sicaklik_c",
           "titresim_g", "ariza"]
print("temiz ozet (ortalama, std, min, maks):")
print(temiz[sayisal].agg(["mean", "std", "min", "max"]).round(2)
      .to_string())
print("ariza ile korelasyon:")
print(temiz[sayisal].corr()["ariza"].round(3).to_string())
