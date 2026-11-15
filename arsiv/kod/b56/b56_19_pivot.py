import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle

df, _ = uret(56)
t = temizle(df, kayit_tablosu())[0]
ozet = t.groupby(["arac_id", "gorev"])["ariza"].mean().unstack()
print("pivot (arac x gorev, arizali oran):")
print(ozet.round(3).head(3).to_string())

ornek = t[["zaman", "irtifa", "batarya_v"]].head(2)
uzun = pd.melt(ornek, id_vars="zaman", var_name="olcum",
               value_name="deger")
print("melt (genis -> uzun):")
print("genis:", ornek.shape, " uzun:", uzun.shape)
print(uzun.round(2).to_string(index=False))
