# ornekleme.py - Bolum 52.2-52.3: ortusme ve nicemleme
import numpy as np

# --- 52.2: 7 kHz sinyal, fs = 10 kHz ile ornekleniyor
fs = 10_000.0
n = np.arange(12)
t = n / fs
x7 = np.sin(2 * np.pi * 7000 * t)
x3 = np.sin(2 * np.pi * 3000 * t)
print("n    7 kHz         3 kHz")
for k in range(6):
    print(f"{k:<4} {x7[k]:+.6f}    {x3[k]:+.6f}")
print("max|x7 + x3| =", f"{np.max(np.abs(x7 + x3)):.2e}")

# --- 52.3: N bitlik tekduze nicemleyici, tam olcek [-1, 1)
def nicemle(x, N):
    adim = 2.0 ** (1 - N)
    q = adim * np.round(x / adim)
    return np.clip(q, -1.0, 1.0 - adim)

rng = np.random.default_rng(52)
faz = rng.uniform(0, 2 * np.pi)
t = np.arange(200_000) / 200_000.0
x = np.sin(2 * np.pi * 37 * t + faz)
p_sinyal = np.mean(x ** 2)
print("\nN   SNR olculen   6,02N+1,76")
for N in (4, 6, 8, 12, 16):
    e = nicemle(x, N) - x
    snr = 10 * np.log10(p_sinyal / np.mean(e ** 2))
    print(f"{N:<3} {snr:10.2f} dB   {6.02 * N + 1.76:10.2f} dB")
