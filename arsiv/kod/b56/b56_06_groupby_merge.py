import warnings
import pandas as pd
from ihadata import uret, kayit_tablosu

df, tr = uret(56)
df["arac_id"] = df["arac_id"].str.strip().str.upper()
df = df.drop_duplicates(subset=["arac_id", "zaman"])
ozet = (df.groupby("arac_id", as_index=False)
          .agg(satir=("hiz", "size"),
               ucus=("ucus_no", "nunique"),
               batarya_ort=("batarya_v", "mean"),
               sicak_maks=("sicaklik_c", "max"),
               ariza_oran=("ariza", "mean")))
print(ozet.round(3).to_string(index=False))

son = df.groupby("ucus_no")["ariza"].transform("max")
print("ucus ariza isareti sayisi (transform):", int(son.sum()))

sol = pd.DataFrame({"ucus_no": [1, 2, 3, 4],
                    "arac": ["A", "A", "B", "C"]})
sag = pd.DataFrame({"arac": ["A", "A", "A", "B"],
                    "firmware": ["v1", "v2", "v3", "v1"]})
for tip in ["inner", "left", "outer"]:
    print(tip, len(sol.merge(sag, on="arac", how=tip)))
try:
    sol.merge(sag, on="arac", validate="many_to_one")
except pd.errors.MergeError as e:
    print("validate hatasi:", str(e)[:50])
kayit = kayit_tablosu()
birlesik = df.merge(kayit, on="arac_id", how="left",
                    validate="many_to_one")
print("satir once/sonra:", len(df), len(birlesik))
