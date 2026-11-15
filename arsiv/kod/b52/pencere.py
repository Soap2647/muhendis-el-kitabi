# pencere.py - Bolum 52.6: pencereleme, sizinti, ayrilma, doldurma
import numpy as np

def pencere(ad, N):
    n = np.arange(N)
    a = 2 * np.pi * n / (N - 1)
    if ad == "dikdortgen": return np.ones(N)
    if ad == "hann":       return 0.5 - 0.5 * np.cos(a)
    if ad == "hamming":    return 0.54 - 0.46 * np.cos(a)
    if ad == "blackman":
        return 0.42 - 0.5*np.cos(a) + 0.08*np.cos(2*a)

PEN = ["dikdortgen", "hann", "hamming", "blackman"]

# A: yan lob ve ana lob (N=128, fs=1000, 100,5 Hz tek ton)
fs, N = 1000.0, 128
n = np.arange(N)
x0 = np.cos(2 * np.pi * 100.5 * n / fs)
print("A. pencere      yan lob (dB)   ana lob (kutu)")
for ad in PEN:
    S = np.abs(np.fft.rfft(x0 * pencere(ad, N), n=16 * N))
    d = 20 * np.log10(S / S.max())
    tepe = int(np.argmax(d))
    k = tepe
    while d[k + 1] < d[k]:
        k += 1
    print(f"   {ad:<12} {d[k:].max():10.1f}   {2*(k-tepe)/16:12.2f}")

# B: zayif ton sizinti altinda mi? N=256, fs=1024
fs2, N2 = 1024.0, 256
m = np.arange(N2)
guclu = np.cos(2*np.pi*101*m/fs2)
zayif = 0.001 * np.cos(2*np.pi*152*m/fs2)
print("\nB. pencere      sizinti (dB)   sizinti+zayif (dB)")
for ad in PEN:
    w = pencere(ad, N2)
    Sg = np.abs(np.fft.rfft(guclu * w))
    Sb = np.abs(np.fft.rfft((guclu + zayif) * w))
    ref = Sg.max()
    print(f"   {ad:<12} {20*np.log10(Sg[38]/ref):10.1f}"
          f"   {20*np.log10(Sb[38]/ref):14.1f}")

# C: iki esit tonun ayrilma esigi (vadi <= -3 dB)
fs3, N3 = 1000.0, 64
t = np.arange(N3) - (N3 - 1) / 2       # pencere merkezine gore zaman
f1 = 300.0
def vadi(w, kutu):
    f2 = f1 + kutu * fs3 / N3
    x = np.exp(2j*np.pi*f1*t/fs3) + np.exp(2j*np.pi*f2*t/fs3)
    S = lambda f: abs(np.sum(w * x * np.exp(-2j*np.pi*f*t/fs3)))
    return 20*np.log10(S((f1+f2)/2) / min(S(f1), S(f2)))
print("\nC. pencere      ayrilma esigi (kutu, vadi <= -3 dB)")
for ad in PEN:
    w = pencere(ad, N3)
    for kutu in np.arange(0.5, 4.0, 0.05):
        if vadi(w, kutu) <= -3:
            print(f"   {ad:<12} {kutu:8.2f}")
            break

# D: sifir doldurma. Tepe okuma hatasi kuculur.
t_ = np.arange(64)
for f0 in (100.0, 104.0):
    x = np.cos(2*np.pi*f0*t_/1000.0)
    print(f"\nD. {f0:.0f} Hz, N=64:", end=" ")
    for pad in (1, 16):
        S = np.abs(np.fft.rfft(x, n=pad*64))
        print(f"pad {pad:2d} -> {np.argmax(S)*1000/(pad*64):7.2f} Hz",
              end="  ")
    print()
