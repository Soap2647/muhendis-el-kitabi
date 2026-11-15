# -*- coding: utf-8 -*-
# b58_12_gomulu.py: lojistik modeli C'ye aktar, int8'e kuantize et,
# WSL gcc ile derle, Python sonuclariyla karsilastir.
import os
import subprocess

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from b58_core import logistik_newton, sigmoid

TEMP = "C:/Users/merty/AppData/Local/Temp/b58"
veri = load_breast_cancer()
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, veri.target, test_size=0.2, stratify=veri.target,
    random_state=58)
mu, sd = X_tr.mean(0), X_tr.std(0)
Z, Zt = (X_tr - mu) / sd, (X_te - mu) / sd
w_all, _ = logistik_newton(Z, y_tr, lam=1.0 / len(y_tr))
b, w = w_all[0], w_all[1:]
d = len(w)

# Python referansi (float64)
p_py = sigmoid(Zt @ w + b)

# Simetrik int8 kuantizasyon: olcek = max|w| / 127
olcek = np.max(np.abs(w)) / 127.0
wq = np.clip(np.round(w / olcek), -127, 127).astype(np.int8)
p_q8_py = sigmoid(Zt @ (wq.astype(float) * olcek) + b)
print("kuantizasyon olcegi = %.6f, max|w - olcek*wq| = %.2e"
      % (olcek, np.max(np.abs(w - olcek * wq))))
print("Python: float ile int8 olasilik farki (max) = %.2e"
      % np.max(np.abs(p_py - p_q8_py)))
print("bellek: float agirliklar %d bayt, int8 agirliklar %d bayt"
      % (4 * d, d))


# Baslik dosyalari
def dizi(ad, tip, degerler, bicim="%.9g"):
    satirlar = [", ".join(bicim % v for v in degerler[i:i + 6])
                for i in range(0, len(degerler), 6)]
    return "static const %s %s[%d] = {\n    %s\n};\n" % (
        tip, ad, len(degerler), ",\n    ".join(satirlar))


with open(os.path.join(TEMP, "b58_model.h"), "w",
          encoding="utf-8") as f:
    f.write("/* otomatik uretildi: b58_12_gomulu.py */\n")
    f.write("#define D 30\n")
    f.write(dizi("W", "float", list(w.astype(np.float32))))
    f.write("static const float B = %.9g;\n" % b)
    f.write(dizi("WQ", "int8_t", [int(v) for v in wq], "%d"))
    f.write("static const float OLCEK = %.9g;\n" % olcek)

with open(os.path.join(TEMP, "b58_test.h"), "w",
          encoding="utf-8") as f:
    f.write("/* otomatik uretildi: test kumesi */\n")
    f.write("#define NT %d\n" % len(Zt))
    f.write("static const float XT[%d][30] = {\n" % len(Zt))
    for row in Zt.astype(np.float32):
        f.write("  {" + ", ".join("%.9g" % v for v in row) + "},\n")
    f.write("};\n")

# WSL gcc ile derle: -O2 -Wall -Wextra -std=c11
yol = "/mnt/c/Users/merty/AppData/Local/Temp/b58"
komut = ("cd %s && gcc -O2 -Wall -Wextra -std=c11 b58_main.c "
         "b58_tahmin.c -o b58_main -lm && ./b58_main") % yol
env = dict(os.environ, MSYS_NO_PATHCONV="1")
sonuc = subprocess.run(["wsl", "bash", "-c", komut],
                       capture_output=True, text=True, env=env)
print("derleme/calistirma kodu:", sonuc.returncode)
if sonuc.stderr.strip():
    print("stderr:", sonuc.stderr.strip()[:500])
satirlar = [s.split() for s in sonuc.stdout.strip().split("\n")]
pf = np.array([float(s[1]) for s in satirlar])
pq = np.array([float(s[2]) for s in satirlar])
print("C float ile Python arasinda max fark = %.2e"
      % np.max(np.abs(pf - p_py)))
print("C int8 ile Python int8 arasinda max fark = %.2e"
      % np.max(np.abs(pq - p_q8_py)))
print("test dogrulugu: float = %.4f, int8 = %.4f"
      % (np.mean((pf > 0.5) == y_te), np.mean((pq > 0.5) == y_te)))
print("float ve int8 karar uyumu = %.4f"
      % np.mean((pf > 0.5) == (pq > 0.5)))
