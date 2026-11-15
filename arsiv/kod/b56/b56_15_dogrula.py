import numpy as np
import pandas as pd
from ihadata import uret, kayit_tablosu
from temizle import temizle
from dogrula import kontrol

df, tr = uret(56)
sema = {"zaman": "object", "arac_id": "object",
        "irtifa": "float", "batarya_v": "float"}
aralik = {"irtifa": (0, 500), "batarya_v": (18, 27),
          "sicaklik_c": (-40, 120)}
benz = [["arac_id", "zaman"]]
eksik = {"batarya_v": 0.05, "sicaklik_c": 0.03}
ref = df.iloc[:20000][["irtifa", "batarya_v"]]

print("HAM veri:")
for ad, ok in kontrol(df, sema, aralik, benz, eksik, ref):
    print("  [%s] %s" % ("OK" if ok else "!!", ad))
temiz, _ = temizle(df, kayit_tablosu())
print("TEMIZ veri:")
ref_t = temiz.iloc[:20000][["irtifa", "batarya_v"]]
sema_t = dict(sema, zaman="datetime64")
for ad, ok in kontrol(temiz, sema_t, aralik, benz, eksik, ref_t):
    print("  [%s] %s" % ("OK" if ok else "!!", ad))
