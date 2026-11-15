# b57_09_ab_erken_bakma.py
# A/B testinde erken bakma (peeking): yanlis pozitif
import os
import numpy as np

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- Orneklem buyuklugu formulu (Bolum 49) ----------
p1, p2 = 0.10, 0.12
za, zb = 1.96, 0.8416
pbar = (p1 + p2) / 2
n_grup = ((za * np.sqrt(2 * pbar * (1 - pbar))
           + zb * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
          / (p2 - p1)) ** 2
print("Grup basina n = %.1f  (yukari yuvarla: %d)"
      % (n_grup, int(np.ceil(n_grup))))

# ---------- Erken bakma simulasyonu: gercek fark YOK ----------
# A ve B ayni oranli (p = 0.10). Toplam N = 10000 ornek / grup.
# Her chunk 100 ornek; 100 chunk = 100 "bakis" noktasi araligi.
rng = np.random.default_rng(57)
N, p = 10000, 0.10
chunk_n = 100
chunks = N // chunk_n                 # 100 bakis araligi
tekrar = 4000
alpha_z = 1.959964                    # iki yonlu, alfa = 0.05

# Her tekrar icin her chunk'taki basari sayisi (A ve B)
basari_a = rng.binomial(chunk_n, p, size=(tekrar, chunks))
basari_b = rng.binomial(chunk_n, p, size=(tekrar, chunks))
kum_a = np.cumsum(basari_a, axis=1)
kum_b = np.cumsum(basari_b, axis=1)


def z_istatistik(xa, xb, na, nb):
    pa, pb = xa / na, xb / nb
    pp = (xa + xb) / (na + nb)
    se = np.sqrt(pp * (1 - pp) * (1 / na + 1 / nb))
    return np.where(se > 0, (pa - pb) / np.where(se > 0, se, 1), 0.0)


def yanlis_pozitif(K):
    """K esit bakis; herhangi birinde |z| > 1.96 ise anlamli."""
    adim = chunks // K
    bakis = np.arange(adim, chunks + 1, adim)     # chunk sonlari
    n_bakis = bakis * chunk_n                  # ornek sayisi
    xa = kum_a[:, bakis - 1]
    xb = kum_b[:, bakis - 1]
    z = z_istatistik(xa, xb, n_bakis, n_bakis)
    anlamli = np.any(np.abs(z) > alpha_z, axis=1)
    return anlamli.mean()


print("\nBakis sayisi K    yanlis pozitif orani (hedef 0.05)")
sonuc = []
for K in [1, 2, 5, 10, 20, 50, 100]:
    fpr = yanlis_pozitif(K)
    sonuc.append((K, fpr))
    print("%3d              %.3f" % (K, fpr))

# K=1 (sabit orneklem) gercek alfa ~0.05 olmali
assert abs(sonuc[0][1] - 0.05) < 0.01

# Sabit orneklemde (yalnizca son bakis) z dagilimi kontrolu
z_son = z_istatistik(kum_a[:, -1], kum_b[:, -1], N, N)
print("\nSon bakis z std = %.3f (N(0,1) icin 1.000)" % z_son.std())

# Sekil verisi
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_erken_bakma.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("bakis_sayisi,yanlis_pozitif\n")
    for K, fpr in sonuc:
        f.write("%d,%.5f\n" % (K, fpr))
print("Erken bakma verisi yazildi:", os.path.basename(yol))
