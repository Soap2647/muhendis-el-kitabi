# veri_uret.py - Bolum 52 sekilleri icin olcum CSV'leri (kitap disi yardimci)
import numpy as np
VERI = "engine/veri/"
PEN = ["dikdortgen", "hann", "hamming", "blackman"]

def pen(ad, N):
    m = np.arange(N); a = 2*np.pi*m/(N-1)
    return {"dikdortgen": np.ones(N), "hann": 0.5-0.5*np.cos(a),
            "hamming": 0.54-0.46*np.cos(a),
            "blackman": 0.42-0.5*np.cos(a)+0.08*np.cos(2*a)}[ad]

# 1) nicemleme: olculen SNR, N = 2..16
def nicemle(x, N):
    adim = 2.0 ** (1 - N)
    return np.clip(adim * np.round(x / adim), -1.0, 1.0 - adim)
rng = np.random.default_rng(52)
faz = rng.uniform(0, 2 * np.pi)
t = np.arange(200_000) / 200_000.0
x = np.sin(2 * np.pi * 37 * t + faz)
ps = np.mean(x ** 2)
satirlar = []
for N in range(2, 17):
    e = nicemle(x, N) - x
    satirlar.append([N, 10*np.log10(ps / np.mean(e**2)), 6.02*N + 1.76])
np.savetxt(VERI + "b52_nicemleme.csv", np.array(satirlar), delimiter=",",
           header="N,snr_olculen_db,snr_teorik_db", comments="", fmt="%.4f")

# 2) DFT: 64 nokta, 125 Hz (tam kutu) ve 130 Hz (kesirli)
fs, N = 1000.0, 64
n = np.arange(N)
f = np.arange(N) * fs / N
tam = np.abs(np.fft.fft(np.cos(2*np.pi*125*n/fs)))
kes = np.abs(np.fft.fft(np.cos(2*np.pi*130*n/fs)))
np.savetxt(VERI + "b52_dft.csv", np.column_stack([f, tam, kes]),
           delimiter=",", header="f_hz,tam_kutu,kesirli", comments="",
           fmt="%.5f")

# 3) pencereler: zaman sekli (N = 128) ve 100,5 Hz tonun dB spektrumu
N2, fs2 = 128, 1000.0
x0 = np.cos(2*np.pi*100.5*np.arange(N2)/fs2)
zaman = [np.arange(N2)] + [pen(ad, N2) for ad in PEN]
spek = []
for ad in PEN:
    S = np.abs(np.fft.rfft(x0 * pen(ad, N2), n=16*N2))
    spek.append(20*np.log10(S/S.max() + 1e-12))
fz = np.arange(16*N2//2 + 1) * fs2 / (16*N2)
np.savetxt(VERI + "b52_pencere_zaman.csv", np.column_stack(zaman),
           delimiter=",", header="n,dikdortgen,hann,hamming,blackman",
           comments="", fmt="%.5f")
np.savetxt(VERI + "b52_pencere_spektrum.csv", np.column_stack([fz] + spek),
           delimiter=",", header="f_hz,dikdortgen,hann,hamming,blackman",
           comments="", fmt="%.4f")

# 4) ayrilma: iki karmasik ton vadisi (dB), kutu sayisina gore
fs3, N3 = 1000.0, 64
t3 = np.arange(N3) - (N3 - 1) / 2
f1 = 300.0
def vadi(w, kutu):
    f2 = f1 + kutu * fs3 / N3
    x = np.exp(2j*np.pi*f1*t3/fs3) + np.exp(2j*np.pi*f2*t3/fs3)
    S = lambda ff: abs(np.sum(w * x * np.exp(-2j*np.pi*ff*t3/fs3)))
    return 20*np.log10(S((f1+f2)/2) / min(S(f1), S(f2)))
kutular = np.arange(0.5, 3.51, 0.05)
tablo = [kutular] + [[vadi(pen(ad, N3), k) for k in kutular] for ad in PEN]
np.savetxt(VERI + "b52_ayrilma.csv", np.column_stack(tablo), delimiter=",",
           header="kutu,dikdortgen_db,hann_db,hamming_db,blackman_db",
           comments="", fmt="%.4f")

# 5) zayif ton (152 Hz, -60 dB), N = 256, fs = 1024
fs4, N4 = 1024.0, 256
m4 = np.arange(N4)
guclu = np.cos(2*np.pi*101*m4/fs4)
zayif = 0.001 * np.cos(2*np.pi*152*m4/fs4)
with open(VERI + "b52_zayif_ton.csv", "w", encoding="utf-8") as fh:
    fh.write("pencere,sizinti_db,toplam_db\n")
    for ad in PEN:
        w = pen(ad, N4)
        Sg = np.abs(np.fft.rfft(guclu * w))
        Sb = np.abs(np.fft.rfft((guclu + zayif) * w))
        ref = Sg.max()
        fh.write(f"{ad},{20*np.log10(Sg[38]/ref):.4f},"
                 f"{20*np.log10(Sb[38]/ref):.4f}\n")
print("veriler yazildi")
