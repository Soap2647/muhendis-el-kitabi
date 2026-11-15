# b57_ornek4.py: iki modelin eslestirilmis McNemar testi
import math
from scipy.stats import binomtest

a, b, c, d = 31, 7, 2, 0   # a: ikisi dogru; b, c: uyumsuz
n = a + b + c + d
print("Tablo: a=%d b=%d c=%d d=%d, n=%d" % (a, b, c, d, n))
print("Model 1 dogruluk = %.4f" % ((a + b) / n))
print("Model 2 dogruluk = %.4f" % ((a + c) / n))
print("Fark (1-2)       = %.4f" % ((b - c) / n))

chi2 = (abs(b - c) - 1) ** 2 / (b + c)
p_ki = math.erfc(math.sqrt(chi2 / 2))
print("chi2 (sureklilik duzeltmeli) = %.4f, p = %.4f" % (chi2, p_ki))

m = b + c
alt = sum(math.comb(m, k) for k in range(min(b, c) + 1))
p_tam = min(1.0, 2 * alt / 2 ** m)
print("tam binom: X ~ Bin(%d, 0.5), P(X<=%d) = %d/%d"
      % (m, min(b, c), alt, 2 ** m))
print("tam iki yonlu p = %.4f" % p_tam)
print("scipy binomtest = %.4f" % binomtest(min(b, c), m, 0.5).pvalue)
