# imu_tumleyen.py - Bolum 52.10: IMU egim kestirimi (SENTETIK veri)
import numpy as np

fs, T = 200.0, 60.0
dt = 1.0 / fs
t = np.arange(0, T, dt)
rng = np.random.default_rng(52)

# gercek egim: 10 derece genlikli, 0,1 Hz'lik yavas hareket
theta = 10.0 * np.sin(2 * np.pi * 0.1 * t)
# jiroskop: turev + 0,05 deg/s sapma + gurultu
omega = np.gradient(theta, dt) + 0.05 + rng.normal(0, 0.5, t.size)
# ivmeolcer: gercek egim + 40 Hz titresim + beyaz gurultu
titresim = 2.0 * np.sin(2 * np.pi * 40 * t)
theta_a = theta + titresim + rng.normal(0, 1.0, t.size)

# 1) ivmeolcer, alcak geciren (ustel duzlestirme, fc = 5 Hz)
a = 1 - np.exp(-2 * np.pi * 5.0 / fs)
ema = np.zeros_like(theta_a)
y = theta_a[0]
for i, v in enumerate(theta_a):
    y = a * v + (1 - a) * y
    ema[i] = y

# 2) jiroskop integrali: sapma zamanla birikir
gyro = np.zeros_like(t)
g = 0.0
for i, w in enumerate(omega):
    g += w * dt
    gyro[i] = g

# 3) tumleyen filtre: jiroskop kisa vadede, ivmeolcer uzun vadede
alfa = 0.98
comp = np.zeros_like(t)
c = 0.0
for i in range(t.size):
    c = alfa * (c + omega[i] * dt) + (1 - alfa) * theta_a[i]
    comp[i] = c

def rmse(tahmin):
    k = int(2 * fs)                     # ilk 2 saniye isinma
    return np.sqrt(np.mean((tahmin[k:] - theta[k:]) ** 2))

print("yontem                    RMS hata (derece)")
print(f"ivmeolcer ham             {rmse(theta_a):8.3f}")
print(f"ivmeolcer EMA (5 Hz)      {rmse(ema):8.3f}")
print(f"jiroskop integrali        {rmse(gyro):8.3f}")
print(f"tumleyen (alfa=0,98)      {rmse(comp):8.3f}")

np.savetxt("engine/veri/b52_imu.csv",
           np.column_stack([t, theta, theta_a, ema, gyro, comp]),
           delimiter=",",
           header="t_s,gercek,ivme_ham,ivme_ema,jiro,tumleyen",
           comments="", fmt="%.5f")
