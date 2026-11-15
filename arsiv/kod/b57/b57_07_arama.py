# b57_07_arama.py
# Izgara vs rastgele arama; dogrulamaya asiri uyum (secim yanliligi)
import os
import numpy as np

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


# ---------- 1) Izgara mi, rastgele mi? ----------
# Amac: g(x, y) = -(x - 0.3)^2 - 0.05 (y - 0.6)^2. Yalnizca x onemli
# (sekil: boyut x etkili, boyut y az etkili). Butce: 9 deneme.
def g(x, y):
    return -(x - 0.3) ** 2 - 0.05 * (y - 0.6) ** 2


OPT = g(0.3, 0.6)                      # = 0 (en iyi deger)
rng = np.random.default_rng(57)
tekrar = 2000
izgara_pay = np.linspace(0, 1, 3)      # 3 x 3 = 9 nokta
izgara_x, izgara_y = np.meshgrid(izgara_pay, izgara_pay)
izgara_en = g(izgara_x, izgara_y).max()
izgara_ptk = []
rastgele_ptk = []
for _ in range(tekrar):
    # Izgara: sabit, her tekrarda ayni (deterministik)
    izgara_ptk.append(OPT - izgara_en)
    # Rastgele: 9 bagimsiz uniform nokta
    xr, yr = rng.uniform(size=9), rng.uniform(size=9)
    rastgele_ptk.append(OPT - g(xr, yr).max())
izgara_ptk = np.array(izgara_ptk)
rastgele_ptk = np.array(rastgele_ptk)
print("Butce = 9 deneme; ptk = en iyiden fark (kucuk iyi)")
print("Izgara (3x3): ptk = %.5f" % izgara_ptk.mean())
print("Rastgele (9) : ort ptk = %.5f, medyan = %.5f"
      % (rastgele_ptk.mean(), np.median(rastgele_ptk)))
print("Rastgele daha iyi olma orani: %.3f"
      % np.mean(rastgele_ptk < izgara_ptk[0]))
# Ayni 9 noktada onemli boyuttaki ayri deger sayisi
print("Izgarada x icin ayri deger: %d, rastgelede: 9"
      % len(np.unique(izgara_x)))

# ---------- 2) Dogrulamaya asiri uyum: secim yanliligi ----------
# Tum M konfigurasyonun GERCEK skoru 0.5 (hicbiri ise yaramiyor).
# Gozlenen dogrulama skoru: 0.5 + gurultu, n_val = 200 ornek.
n_val = 200
s = np.sqrt(0.5 * 0.5 / n_val)   # ikili dogruluk std hatasi
n_test = 2000
s_test = np.sqrt(0.5 * 0.5 / n_test)
print("\nGercek skor 0.5. Dogrulama std = %.4f" % s)
print("M     secilen dogrulama skoru   secilenin test skoru")
satirlar = []
for M in [1, 10, 100, 1000]:
    sec_val, sec_test = [], []
    for _ in range(1000):
        val = 0.5 + rng.normal(scale=s, size=M)
        i = np.argmax(val)                     # en iyi dogrulama
        sec_val.append(val[i])
        # bagimsiz test kumesi
        sec_test.append(0.5 + rng.normal(scale=s_test))
    print("%4d  %.4f                    %.4f"
          % (M, np.mean(sec_val), np.mean(sec_test)))
    satirlar.append((M, np.mean(sec_val), np.mean(sec_test)))

# Teorik kontrol: M normalin maksimumunun beklenen degeri (yaklasik)
# M=10: ~1.54 std; M=100: ~2.51 std; M=1000: ~3.24 std
print("beklenen sapma (std cinsinden) M=10: 1.54, M=100: 2.51")

# ---------- 3) Ornek: tek bir deneme ile bir cok deneme ----------
bir = 0.5 + rng.normal(scale=s)
print("\nTek deneme dogrulama skoru: %.4f" % bir)
print("1000 denemede en iyi (dogrulama): %.4f"
      % (0.5 + rng.normal(scale=s, size=1000).max()))

os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_asiri_uyum.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("M,secilen_dogrulama,secilen_test\n")
    for M, v, t in satirlar:
        f.write("%d,%.5f,%.5f\n" % (M, v, t))
print("Asiri uyum verisi yazildi:", os.path.basename(yol))

# Sekil verisi: 9 izgara ve 9 rastgele nokta (ayri tohum, tek deneme)
_r2 = np.random.default_rng(7)
_xr, _yr = _r2.uniform(size=9), _r2.uniform(size=9)
with open(os.path.join(VERI, "b57_arama_noktalar.csv"), "w",
          encoding="utf-8") as _f:
    _f.write("yontem,x,y\n")
    for _a, _b in zip(izgara_x.ravel(), izgara_y.ravel()):
        _f.write("izgara,%.5f,%.5f\n" % (_a, _b))
    for _a, _b in zip(_xr, _yr):
        _f.write("rastgele,%.5f,%.5f\n" % (_a, _b))
