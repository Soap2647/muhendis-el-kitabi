# katsayi_q15.py - 5 tap alcak geciren FIR katsayilari, Q15'e cevrim
import numpy as np
from scipy import signal

# hamming penceresi, DC kazanci 1
b = signal.firwin(5, 0.4)
q = np.round(b * 2**15).astype(int)
print("float b :", np.round(b, 6))
print("Q15 q   :", q.tolist())
print("sum b   =", round(b.sum(), 6), "  sum q =", q.sum())
print("sum|b|  =", round(np.abs(b).sum(), 6))
print("kuantizasyon hatasi (max) =",
      f"{np.max(np.abs(q / 2**15 - b)):.2e}")
