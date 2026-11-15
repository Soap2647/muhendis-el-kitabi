# -*- coding: utf-8 -*-
"""Bolum 75 cozumlu ornek sayilarini dogrular (Ornek 1-4)."""
import numpy as np

# Ornek 1: tensor kuantizasyonu (simetrik ve asimetrik, int8)
x = np.array([-1.00, -0.35, 0.00, 0.60, 2.40])
s_sim = np.abs(x).max() / 127
q_sim = np.clip(np.round(x / s_sim), -127, 127).astype(int)
xh_sim = q_sim * s_sim
print("sim s=%.6f q=%s" % (s_sim, q_sim.tolist()))
print("sim hata=%s" % np.round(xh_sim - x, 5).tolist())
s_as = (x.max() - x.min()) / 255
z = int(np.round(-x.min() / s_as)) - 128
q_as = np.clip(np.round(x / s_as) + z, -128, 127).astype(int)
xh_as = (q_as - z) * s_as
print("asim s=%.6f z=%d q=%s" % (s_as, z, q_as.tolist()))
print("asim hata=%s" % np.round(xh_as - x, 5).tolist())
print("sim MSE=%.3e asim MSE=%.3e"
      % (np.mean((xh_sim - x) ** 2), np.mean((xh_as - x) ** 2)))

# Ornek 2: BatchNorm katlamasi (skaler)
W, b, gam, bet, mu, var, eps = 0.5, 0.1, 2.0, -0.3, 0.2, 0.04, 1e-5
xi = 1.3
bn = gam * ((W * xi + b) - mu) / np.sqrt(var + eps) + bet
s = gam / np.sqrt(var + eps)
Wf, bf = W * s, (b - mu) * s + bet
print("s=%.6f W'=%.6f b'=%.6f" % (s, Wf, bf))
print("BN=%.6f katli=%.6f fark=%.2e"
      % (bn, Wf * xi + bf, abs(bn - (Wf * xi + bf))))

# Ornek 3: roofline (512x512 Linear, tepe 20 GFLOP/s, bant 8 GB/s)
tepe, bant = 20.0, 8.0
esik = tepe / bant
print("esik AI=%.2f" % esik)
for B in [1, 4, 5, 6, 16]:
    fl = 2.0 * B * 512 * 512
    by = 4.0 * (512 * 512 + 2 * B * 512)
    ai = fl / by
    tur = "bellek" if ai < esik else "hesap"
    print("B=%-2d FLOP=%d bayt=%d AI=%.3f %s"
          % (B, fl, by, ai, tur))

# Ornek 4: edge hedef butcesi (varsayimsal 1,2 milyon parametre)
FLASH_KB = 256
SAAT = 168e6
BUTCE_CEVRIM = 5e-3 * SAAT
c = 2  # varsayim: MAC basina 2 cevrim (olculmedi)
print(
    "butce cevrim=%.0f MAC_tavan=%.0f"
    % (BUTCE_CEVRIM, BUTCE_CEVRIM / c)
)
aday = [
    ("ogretmen fp32", 1_200_000, 32, 1_200_000),
    ("ogretmen int8", 1_200_000, 8, 1_200_000),
    ("budama %70 + int8 (yogun)", 1_200_000, 8, 360_000),
    ("yapisal %50 + damitma int8", 120_000, 8, 120_000),
]
for ad, p, bit, mac in aday:
    kb = p * bit / 8 / 1024
    ms = mac * c / SAAT * 1e3
    print("%-26s %8.1f KB %9d MAC %6.2f ms %s"
          % (ad, kb, mac, ms, "evet" if kb <= FLASH_KB else "hayir"))
