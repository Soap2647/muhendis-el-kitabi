# welch_spektrogram.py - Bolum 52.8: Welch PSD ve STFT spektrogrami
import numpy as np
from scipy import signal

def welch(x, fs, L=256):
    """Hann pencereli, %50 cakisan parcalarin ortalamasi."""
    w = np.hanning(L)
    adim = L // 2
    kare = [x[i:i + L] * w for i in range(0, len(x) - L + 1, adim)]
    P = np.mean([np.abs(np.fft.rfft(s)) ** 2 for s in kare], axis=0)
    P = P / (fs * np.sum(w ** 2))
    P[1:-1] *= 2                       # tek tarafli spektrum
    return np.fft.rfftfreq(L, 1 / fs), P

rng = np.random.default_rng(52)
fs = 1000.0
x = rng.standard_normal(2 ** 16)       # beyaz gurultu, sigma = 1
f, P = welch(x, fs)
_, Ps = signal.welch(x, fs, window=np.hanning(256), nperseg=256,
                     noverlap=128, detrend=False)
print("kendi welch ile scipy: max goreli fark =",
      f"{np.max(np.abs(P - Ps) / Ps):.2e}")

# periodogram ile Welch'in gurultu yayilimi (CV = std / ortalama)
w = np.hanning(256)
pg = np.abs(np.fft.rfft(x[:256] * w)) ** 2 / (fs * np.sum(w ** 2))
cv = lambda v: np.std(v[5:-5]) / np.mean(v[5:-5])
print("tek periodogram CV =", f"{cv(pg):.3f}")
print("Welch CV           =", f"{cv(P):.3f}")
print("beklenen PSD = 2 sigma^2 / fs =", 2 / fs)

# spektrogram: lineer cikirtma (chirp) 50 Hz -> 400 Hz, 2 s
fs2, T = 2000.0, 2.0
t = np.arange(int(fs2 * T)) / fs2
f0, f1 = 50.0, 400.0
faz = 2 * np.pi * (f0 * t + (f1 - f0) * t ** 2 / (2 * T))
chirp = np.cos(faz)

def stft(x, N, hop):
    w = np.hanning(N)
    merkez = np.arange(N // 2, len(x) - N // 2, hop)
    S = np.array([np.abs(np.fft.rfft(x[c - N//2:c + N//2] * w))
                  for c in merkez])
    return merkez / fs2, np.fft.rfftfreq(N, 1 / fs2), S

print("\nN    kutu (Hz)  tepe hatasi (Hz)  -3 dB serit (Hz)")
for N in (128, 256, 512):
    tc, fk, S = stft(chirp, N, 64)
    ftrue = f0 + (f1 - f0) * tc / T
    ftep = fk[np.argmax(S, axis=1)]
    esik = S.max(axis=1, keepdims=True) / np.sqrt(2)
    serit = np.mean(np.sum(S >= esik, axis=1)) * fk[1]
    hata = np.mean(np.abs(ftep - ftrue))
    print(f"{N:<5}{fk[1]:8.2f}    {hata:10.2f}"
          f"        {serit:10.1f}")

# spektrogram verisi (sekil icin): 256 ornek, 64 ornek atlama
tc, fk, S = stft(chirp, 256, 64)
dB = 20 * np.log10(S / S.max() + 1e-6)
csv = "engine/veri/b52_spektrogram.csv"
with open(csv, "w", encoding="utf-8") as fh:
    fh.write("t_s,f_hz,db\n")
    for i, tt in enumerate(tc):
        for j, ff in enumerate(fk):
            if ff <= 500:
                fh.write(f"{tt:.4f},{ff:.3f},{dB[i, j]:.2f}\n")
