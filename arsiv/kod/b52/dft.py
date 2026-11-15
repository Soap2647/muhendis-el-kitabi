# dft.py - Bolum 52.5: DFT tanimi, O(N^2) gerceklemesi ve FFT
import time
import numpy as np

def dft_dongu(x):
    """X[k] = sum_n x[n] e^{-j 2 pi k n / N}, iki dongu."""
    N = len(x)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        toplam = 0j
        for n in range(N):
            toplam += x[n] * np.exp(-2j * np.pi * k * n / N)
        X[k] = toplam
    return X

fs, N = 1000.0, 64
n = np.arange(N)
x = np.cos(2 * np.pi * 125.0 * n / fs)      # 125 Hz, tam bir kutuda
X = dft_dongu(x)
k_tepe = int(np.argmax(np.abs(X[:N // 2])))
print("tepe kutusu k =", k_tepe,
      " frekans =", k_tepe * fs / N, "Hz")
print("|X[k_tepe]| =", round(abs(X[k_tepe]), 4),
      " (beklenen N/2 =", N // 2, ")")
print("np.fft ile esles:", np.allclose(X, np.fft.fft(x)))

print("\nN      dongu (ms)   np.fft (us)   oran")
rng = np.random.default_rng(52)
for N in (256, 512, 1024, 2048):
    xr = rng.standard_normal(N)
    t0 = time.perf_counter()
    dft_dongu(xr)
    t1 = time.perf_counter()
    for _ in range(200):
        np.fft.fft(xr)
    t2 = time.perf_counter()
    d_ms = (t1 - t0) * 1e3
    f_us = (t2 - t1) / 200 * 1e6
    ora = d_ms * 1e3 / f_us
    print(f"{N:<6} {d_ms:10.1f} {f_us:12.2f} {ora:10.0f}")
