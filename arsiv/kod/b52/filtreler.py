# filtreler.py - Bolum 52.8: FIR ve IIR filtreler, frekans yaniti
import numpy as np
from scipy import signal

fs = 1000.0

# FIR 1: hareketli ortalama (M = 5), y[n] = (1/M) sum x[n-k]
M = 5
b_ma = np.ones(M) / M
x = np.zeros(12)
x[3] = 1.0                              # birim durtu
y = signal.lfilter(b_ma, [1.0], x)
print("MA5 durtu yaniti:", np.round(y[:8], 3))

# FIR 2: pencereli sinc alcak geciren, N = 31, fc = 100 Hz
def sinc_fir(N, fc_norm):
    n = np.arange(N) - (N - 1) / 2
    h = 2 * fc_norm * np.sinc(2 * fc_norm * n)
    h = h * np.hamming(N)
    return h / np.sum(h)                # DC kazanci = 1

N, fc = 31, 100.0 / fs
h = sinc_fir(N, fc)
print("\nsinc FIR katsayi toplami =", round(h.sum(), 6))
ref = signal.firwin(N, 2 * fc, window="hamming")
print("firwin ile fark (max) =", f"{np.max(np.abs(h - ref)):.2e}")
print("simetri (dogrusal faz):", np.allclose(h, h[::-1]))
print("grup gecikmesi (ornek) =", (N - 1) / 2)

# IIR 1: ustel duzlestirme (EMA), fc = 20 Hz
fc_e = 20.0
alfa = 1 - np.exp(-2 * np.pi * fc_e / fs)
xr = np.random.default_rng(52).standard_normal(500)
y_dongu = np.zeros_like(xr)
onceki = 0.0
for i, v in enumerate(xr):
    onceki = alfa * v + (1 - alfa) * onceki
    y_dongu[i] = onceki
y_lf = signal.lfilter([alfa], [1.0, -(1 - alfa)], xr)
print("\nalfa =", round(alfa, 5), " dongu - lfilter (max) =",
      f"{np.max(np.abs(y_dongu - y_lf)):.1e}")
w, H = signal.freqz([alfa], [1.0, -(1 - alfa)], worN=4096, fs=fs)
i3 = np.argmin(np.abs(20 * np.log10(np.abs(H)) + 3))
print("EMA -3 dB frekansi ~", round(w[i3], 2), "Hz (istenen 20 Hz)")
gd = signal.group_delay(([alfa], [1.0, -(1 - alfa)]),
                        w=[0.0001], fs=fs)
print("EMA DC grup gecikmesi ~", round(gd[1][0], 2), "ornek;",
      "teori (1-a)/a =", round((1 - alfa) / alfa, 2))

# IIR 2: Butterworth 2. derece, Wn = 100 Hz / (fs/2)
b_bw, a_bw = signal.butter(2, 100.0 / (fs / 2))
kutup = np.roots(a_bw)
print("\nButterworth b =", np.round(b_bw, 5))
print("Butterworth a =", np.round(a_bw, 5))
print("kutuplar:", np.round(kutup, 4),
      " |kutup| =", np.round(np.abs(kutup), 4))

# frekans yaniti tablosu (sekil icin)
f = np.arange(0, 501, 2.0)
tablo = [f]
for b, a in ((b_ma, [1.0]), (h, [1.0]), ([alfa], [1.0, -(1 - alfa)]),
             (b_bw, a_bw)):
    _, Hf = signal.freqz(b, a, worN=f, fs=fs)
    tablo.append(20 * np.log10(np.maximum(np.abs(Hf), 1e-6)))
np.savetxt("engine/veri/b52_frekans.csv", np.column_stack(tablo),
           delimiter=",",
           header="f_hz,ma5_db,fir31_db,ema20_db,bw2_db",
           comments="", fmt="%.4f")
