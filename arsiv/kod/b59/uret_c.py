# uret_c.py -- agaci C koduna cevir, test girdisi ve Python cevabi yaz
import numpy as np
from agac import KararAgaci
from c_uret import c_kodu_uret, esigi_float32_yap
from uav import uav_veri

df, y = uav_veri()
X = df[["titresim_rms", "motor_sicaklik", "ucus_saati"]].values
X = X.astype(np.float32)
agac = KararAgaci(max_derinlik=3).fit(X[:3000], y[:3000])
esigi_float32_yap(agac.kok)            # C ile ayni (float32) esikler
with open("agac_gomulu.c", "w", encoding="utf-8", newline="\n") as f:
    f.write(c_kodu_uret(agac.kok, ozellik_say=3))
print("yaprak:", agac.yaprak_sayisi(), " derinlik:", agac.derinlik())

r = np.random.default_rng(59)
lo, hi = X.min(axis=0), X.max(axis=0)
G = (lo + (hi - lo) * r.random((20000, 3))).astype(np.float32)
with open("girdi2.txt", "w") as f:
    for row in G:
        f.write("%.9g %.9g %.9g\n" % tuple(row))
py = agac.tahmin(G.astype(np.float64)).astype(int)
with open("py_cikti2.txt", "w") as f:
    f.write("\n".join(str(v) for v in py) + "\n")
print("python sinif 1 sayisi:", int(py.sum()))
