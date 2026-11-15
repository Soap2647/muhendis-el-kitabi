# gomulu_test.py -- agaci uret, C'ye yaz, Python ile karsilastir
import numpy as np, os, subprocess
from agac import KararAgaci
from c_uret import c_kodu_uret, esigi_float32_yap
from uav import uav_veri
df, y = uav_veri()
ozellikler = ["titresim_rms", "motor_sicaklik", "ucus_saati"]
X = df[ozellikler].values.astype(np.float32)
agac = KararAgaci(max_derinlik=3).fit(X[:3000], y[:3000])
esigi_float32_yap(agac.kok)
kod = c_kodu_uret(agac.kok, ozellik_say=3, sinif=2)
with open("agac_gomulu.c", "w", encoding="utf-8", newline="\n") as f:
    f.write(kod)
print("uretilen C satir sayisi:", kod.count("\n"))
print("yaprak sayisi:", agac.yaprak_sayisi(),
      "derinlik:", agac.derinlik())
# Test: Python tahmini (float32 girdi, float32 esik)
Xt = X[3000:]
py = agac.tahmin(Xt.astype(np.float64)).astype(int)
with open("girdi.txt", "w") as f:
    for row in Xt:
        f.write("%.9g %.9g %.9g\n" % tuple(row))
with open("py_cikti.txt", "w") as f:
    for v in py:
        f.write("%d\n" % v)
print("test ornek sayisi:", len(py), " Python sinif 1 orani: %.4f"
      % py.mean())
