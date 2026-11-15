import warnings
import pandas as pd

s1 = pd.Series([1, 2, 3], index=["a", "b", "c"])
s2 = pd.Series([10, 20, 30], index=["b", "c", "d"])
print("indeks hizalama (s1 + s2):")
print((s1 + s2).to_dict())

df = pd.DataFrame({"x": [5, 6, 7]}, index=[10, 20, 30])
print("loc[20]:", df.loc[20, "x"], " iloc[1]:", df.iloc[1]["x"])
df2 = pd.DataFrame({"x": [5, 6, 7]}, index=[1, 2, 3])
print("df2.loc[1] (etiket):", df2.loc[1, "x"],
      " df2.iloc[1] (konum):", df2.iloc[1]["x"])

d = pd.DataFrame({"a": [1, -1, 2], "b": [0, 0, 0]})
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    d[d.a > 0]["b"] = 9
    print("zincir atama -> b:", d.b.tolist())
    print("uyari:", [x.category.__name__ for x in w])
d.loc[d.a > 0, "b"] = 9
print("loc ile atama -> b:", d.b.tolist())

e = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
bir_kopya = e[["x"]].copy()
bir_kopya.loc[0, "x"] = -1.0
print("kopya uzerinde degisiklik, e:", e.x.tolist())
