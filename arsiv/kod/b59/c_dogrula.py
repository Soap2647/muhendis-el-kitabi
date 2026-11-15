# c_dogrula.py -- agac -> C -> ASan testi -> ARM Cortex-M4 boyutu
import os, subprocess
import numpy as np
from agac import KararAgaci
from c_uret import c_kodu_uret, esigi_float32_yap
from uav import uav_veri

ARM = ("C:/ST/STM32CubeIDE_1.19.0/STM32CubeIDE/plugins/"
       "com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32."
       "13.3.rel1.win32_1.0.0.202411081344/tools/bin")
BU = "/mnt/c/Users/merty/AppData/Local/Temp/b59"
os.environ["MSYS_NO_PATHCONV"] = "1"

df, y = uav_veri()
ozellik = ["titresim_rms", "motor_sicaklik", "ucus_saati"]
X = df[ozellik].values.astype(np.float32)
ag = KararAgaci(max_derinlik=3).fit(X[:3000], y[:3000])
esigi_float32_yap(ag.kok)
with open("agac_gomulu.c", "w", encoding="utf-8", newline="\n") as f:
    f.write(c_kodu_uret(ag.kok, ozellik_say=3))
print("yaprak:", ag.yaprak_sayisi(), "derinlik:", ag.derinlik())

r = np.random.default_rng(59)
lo, hi = X.min(axis=0), X.max(axis=0)
G = (lo + (hi - lo) * r.random((20000, 3))).astype(np.float32)
py = ag.tahmin(G.astype(np.float64)).astype(int)
with open("girdi2.txt", "w") as f:
    for row in G:
        f.write("%.9g %.9g %.9g\n" % tuple(row))
with open("py_cikti2.txt", "w") as f:
    f.write("\n".join(str(v) for v in py) + "\n")

sonuc = subprocess.run(
    ["wsl", "gcc", "-O2", "-Wall", "-Wextra", "-std=c11",
     "-fsanitize=address,undefined", BU + "/harness.c",
     BU + "/agac_gomulu.c", "-o", BU + "/harness_asan"],
    capture_output=True, text=True)
print("host derleme:", sonuc.returncode, sonuc.stderr.strip()[:200])
with open("girdi2.txt") as fi, open("c_cikti2.txt", "w") as fo, \
        open("asan2.txt", "w") as fe:
    p = subprocess.run(["wsl", BU + "/harness_asan"], stdin=fi,
                       stdout=fo, stderr=fe)
print("calisma kodu:", p.returncode, "asan satir:",
      sum(1 for _ in open("asan2.txt")))
a = open("py_cikti2.txt").read().split()
b = open("c_cikti2.txt").read().split()
print("girdi:", len(a), "C:", len(b), "uyusmayan:",
      sum(x != z for x, z in zip(a, b)), "C sinif1:", b.count("1"))
for ad in ["agac_gomulu"]:
    subprocess.run([ARM + "/arm-none-eabi-gcc.exe", "-mcpu=cortex-m4",
                    "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv4-sp-d16",
                    "-Os", "-std=c11", "-c", ad + ".c", "-o", ad + ".o"])
    subprocess.run([ARM + "/arm-none-eabi-size.exe", ad + ".o"])
