# eslesik.py - Bolum 52.10: eslesik filtre ile darbe tespiti
# (SENTETIK veri) ve Doppler hesabi
import numpy as np

fs = 50_000.0                           # 50 kHz
Tp = 0.002                              # 2 ms darbe
t = np.arange(int(Tp * fs)) / fs
L = t.size                              # 100 ornek
k = (6000 - 2000) / (2 * Tp)            # 2 kHz -> 6 kHz cikirtma
sablon = np.cos(2*np.pi*(2000*t + k*t**2))
eslesik = sablon[::-1]                  # h[n] = s[L-1-n]

def sigma2_snr(snr_db):
    """SNR = 0,5 / sigma^2 (cos sinyalinin ortalama gucu 0,5)."""
    return 0.5 / 10 ** (snr_db / 10)

def tespit(snr_db, deneme=200, seed=52):
    """Gecikme tahmini: eslesik filtre ve ham genlik."""
    rng = np.random.default_rng(seed)
    basari_m = basari_h = 0
    for _ in range(deneme):
        d = int(rng.integers(300, 1200))
        r = np.zeros(2000)
        r[d:d + L] += sablon
        r += rng.normal(0, np.sqrt(sigma2_snr(snr_db)), r.size)
        c = np.convolve(r, eslesik)
        tahmin_m = int(np.argmax(c)) - (L - 1)
        tahmin_h = int(np.argmax(np.abs(r)))
        basari_m += abs(tahmin_m - d) <= 1
        basari_h += abs(tahmin_h - d) <= 1
    return basari_m / deneme, basari_h / deneme

print(f"sablon enerjisi = {np.sum(sablon**2):.2f}  (L/2 = {L/2})")
print("SNR (dB)   eslesik dogru   ham genlik dogru")
for snr in (-15, -10, -5, 0):
    pm, ph = tespit(snr)
    print(f"{snr:8d}   {pm:12.3f}   {ph:16.3f}")

# Doppler: f_d = 2 v f0 / c (yaklasan hedef icin pozitif)
c_isik, c_ses = 3.0e8, 1500.0
print("\nRadar (10 GHz, 30 m/s):  f_d =",
      round(2 * 30 * 10e9 / c_isik, 1), "Hz")
print("Sonar (40 kHz, 10 m/s):  f_d =",
      round(2 * 10 * 40e3 / c_ses, 1), "Hz")

# sekil verisi: SNR = -5 dB, darbe 700. ornekte
rng = np.random.default_rng(52)
r = np.zeros(2000)
r[700:700 + L] += sablon
r += rng.normal(0, np.sqrt(sigma2_snr(-5)), r.size)
c = np.convolve(r, eslesik)
np.savetxt("engine/veri/b52_eslesik.csv",
           np.column_stack([np.arange(r.size) / fs, r,
                            c[:r.size] / np.max(np.abs(c))]),
           delimiter=",", header="t_s,alici,eslesik_cikis",
           comments="", fmt="%.6f")
