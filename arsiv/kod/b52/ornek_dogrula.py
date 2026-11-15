# ornek_dogrula.py - Cozumlu Ornek 2 ve 3 dogrulamasi
import numpy as np

# Ornek 2: konvolusyon
x = np.array([1, 2, 3, 4])
h = np.array([1, -1, 2])
print("y =", np.convolve(x, h))

# Ornek 3: 8 noktali DFT, 2,5 kutu tonu
N = 8
n = np.arange(N)
X = np.fft.fft(np.cos(2 * np.pi * 2.5 * n / N))
for k in range(N):
    print(f"k={k} f={k * 1000 / N:6.1f} Hz |X[k]| = {abs(X[k]):.4f}")
D = lambda d: abs(np.sin(np.pi * d) / np.sin(np.pi * d / 8))
print("ana terim |D(0,5)|/2   =", round(0.5 * D(0.5), 4))
print("ikinci terim |D(-4,5)|/2 =", round(0.5 * D(-4.5), 4))
