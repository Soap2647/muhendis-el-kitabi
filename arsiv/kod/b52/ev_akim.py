# ev_akim.py - Bolum 52.10: EV batarya akimi, gurultu duzlestirme
# (SENTETIK veri: 20 A'den 80 A'e basamak, 4 A gurultu, 50 Hz parazit)
import numpy as np

fs, T = 1000.0, 10.0
t = np.arange(0, T, 1 / fs)
rng = np.random.default_rng(52)
akim = np.where(t < 5.0, 20.0, 80.0)
ham = akim + rng.normal(0, 4.0, t.size) + 3.0 * np.sin(2*np.pi*50*t)

# 100 ms hareketli ortalama (sonlu, nedensel)
M = 100
ma = np.full(t.size, np.nan)
for i in range(M - 1, t.size):
    ma[i] = np.mean(ham[i - M + 1:i + 1])

# 5 Hz ustel duzlestirme
a = 1 - np.exp(-2 * np.pi * 5.0 / fs)
ema = np.zeros_like(ham)
y = ham[0]
for i, v in enumerate(ham):
    y = a * v + (1 - a) * y
    ema[i] = y

kararli = (t > 1) & (t < 4.9)
print("std (1-4,9 s, kararli bolge):")
print(f"  ham   = {np.std(ham[kararli]):6.3f} A")
print(f"  MA100 = {np.std(ma[kararli]):6.3f} A")
print(f"  EMA5  = {np.std(ema[kararli]):6.3f} A")
hedef = 20 + 0.9 * 60                   # basamagin %90'i
for ad, s in (("MA100", ma), ("EMA5", ema)):
    k = np.argmax((t >= 5.0) & (s >= hedef))
    print(f"  {ad}: %90 gecikme = {(t[k] - 5.0) * 1000:6.1f} ms")
