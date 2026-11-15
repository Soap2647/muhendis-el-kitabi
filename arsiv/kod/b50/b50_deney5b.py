# -*- coding: utf-8 -*-
# PID kazanc ayari, IHA enerji, sensor kalibrasyonu.
import csv
import itertools
import numpy as np
from scipy.optimize import minimize, minimize_scalar

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"

# ---- 3) PID: G(s) = 2/(1.5s+1), ISE ile kazanc ayari ----
def sim_pid(kp, ki, kd, dt=0.01, T=8.0):
    K, tau = 2.0, 1.5
    y, integ, e_onceki = 0.0, 0.0, 0.0
    ise = 0.0
    cab = 0.0
    for _ in range(int(T / dt)):
        e = 1.0 - y
        integ += e * dt
        turev = (e - e_onceki) / dt
        u = np.clip(kp * e + ki * integ + kd * turev, -10.0, 10.0)
        e_onceki = e
        y += dt * (K * u - y) / tau
        ise += e * e * dt
        cab += u * u * dt
    return ise, cab


def maliyet(p):
    if np.any(np.asarray(p) < 0):
        return 1e6
    ise, cab = sim_pid(*p)
    return ise + 0.01 * cab


r0 = minimize(maliyet, [1.0, 0.5, 0.1], method="Nelder-Mead",
              options={"xatol": 1e-4, "fatol": 1e-6, "maxiter": 400})
kp, ki, kd = r0.x
print("\nPID (Nelder-Mead): Kp=%.4f Ki=%.4f Kd=%.4f J=%.5f"
      % (kp, ki, kd, r0.fun))
ise, cab = sim_pid(kp, ki, kd)
print("  ISE=%.5f  kontrol cabasi=%.3f" % (ise, cab))
ise, cab = sim_pid(1.0, 0.0, 0.0)
print("sadece P (Kp=1.0): ISE=%.5f  kontrol cabasi=%.3f" % (ise, cab))

# ---- 4) IHA rota enerjisi: E(v) = P0 d/v + k d v^2 ----
P0, kk, dd, Tmax = 50.0, 0.02, 2000.0, 150.0
E = lambda v: P0 * dd / v + kk * dd * v * v
v_ac = (P0 / (2 * kk)) ** (1 / 3)
v_min = dd / Tmax
r1 = minimize_scalar(E, bounds=(v_min, 40.0), method="bounded",
                     options={"xatol": 1e-10})
print("\nIHA: v*(kisitsiz)=%.4f m/s  v_min=%.4f m/s" % (v_ac, v_min))
print("IHA kisitli optimum: v=%.4f E=%.2f J (kisit aktif)"
      % (r1.x, r1.fun))
print("E(v*) kisitsiz = %.2f J (ihlal eder: T=%.1f s)"
      % (E(v_ac), dd / v_ac))

# ---- 5) Sensor kalibrasyonu: en kucuk kareler ----
rng4 = np.random.default_rng(4)
T_ = np.linspace(0, 100, 25)
ham = 120.0 + 3.1 * T_ + 0.004 * T_ ** 2 + rng4.normal(0, 0.5, 25)
A1 = np.column_stack([np.ones_like(T_), T_])
A2 = np.column_stack([np.ones_like(T_), T_, T_ ** 2])
c1 = np.linalg.lstsq(A1, ham, rcond=None)[0]
c2 = np.linalg.lstsq(A2, ham, rcond=None)[0]
print("\nkalibrasyon dogrusal: b=%.4f a=%.4f  RMS=%.4f"
      % (c1[0], c1[1], np.sqrt(np.mean((A1 @ c1 - ham) ** 2))))
print("kalibrasyon ikinci der.: c0=%.4f c1=%.4f c2=%.6f RMS=%.4f"
      % (c2[0], c2[1], c2[2], np.sqrt(np.mean((A2 @ c2 - ham) ** 2))))
print("kosul sayisi (A2): %.3e" % np.linalg.cond(A2))
A3 = np.column_stack([np.ones_like(T_), T_ / 100, (T_ / 100) ** 2])
print("olceklenmis (T/100) kosul sayisi: %.3e" % np.linalg.cond(A3))

