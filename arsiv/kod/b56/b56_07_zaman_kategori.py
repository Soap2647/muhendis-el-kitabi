import pandas as pd
from ihadata import uret

df, tr = uret(56)
ist = df.loc[df.arac_id == "IHA-05", "zaman"].iloc[0]
print("yerel saat (IHA-05, ilk satir):", ist)
try:
    pd.to_datetime(pd.Series(["2026-03-01T06:00:00Z",
                              "2026-03-01 09:00:00+03:00"]))
except ValueError as e:
    print("hata:", str(e)[:60])
zaman = pd.to_datetime(df["zaman"], format="ISO8601", utc=True)
print("ISO8601 + utc dtype:", zaman.dtype, " ilk:", zaman.iloc[0])
print("ayni an (UTC):",
      zaman[df.arac_id == "IHA-05"].iloc[0])

uc = df[df.ucus_no == 1].copy()
uc.index = zaman[uc.index]
uc = uc.sort_index()
ort = uc[["irtifa", "batarya_v"]].resample("20s").mean()
print("20 sn yeniden ornekleme satir sayisi:", len(ort))
print("ilk iki satir:")
print(ort.head(2).round(2).to_string())

kayan = uc["sicaklik_c"].rolling("60s", closed="left").mean()
print("gecmis 60 sn ortalamasi ilk degerleri:",
      kayan.iloc[:3].round(2).tolist())

bellek_obj = df["arac_id"].memory_usage(deep=True)
bellek_cat = df["arac_id"].astype("category").memory_usage(deep=True)
print("arac_id object bellek (byte):", bellek_obj)
print("arac_id category bellek (byte):", bellek_cat)
print("oran:", round(bellek_obj / bellek_cat, 1))
