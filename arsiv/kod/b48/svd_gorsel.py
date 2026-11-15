# svd_gorsel.py: SVD ile rank-k goruntu yaklasimi ve sikistirma orani
import csv
import sys
import numpy as np


def sentetik_gorsel(n=128, seed=42):
    # yumusak degisim + daire + cizgiler + hafif gurultu (0..1)
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n] / n
    g = 0.5 * x + 0.3 * y
    g += 0.4 * (((x - 0.6) ** 2 + (y - 0.4) ** 2) < 0.06)
    g += 0.2 * np.sin(18 * np.pi * x) * (y > 0.7)
    g += 0.02 * rng.standard_normal((n, n))
    return np.clip(g, 0.0, 1.0)


def rank_k(A, k):
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    return (U[:, :k] * s[:k]) @ Vt[:k]


def sikistirma_orani(m, n, k):
    # U: m x k, s: k, V^T: k x n  ->  k (m + n + 1) sayi
    return k * (m + n + 1) / (m * n)


A = sentetik_gorsel()
m, n = A.shape
s = np.linalg.svd(A, compute_uv=False)
print("tekil degerler: s1=%.3f s2=%.3f s128=%.2e"
      % (s[0], s[1], s[-1]))
print(" k   bagil_hata   s_(k+1)   oran(%)")
satirlar = []
for k in [1, 2, 4, 8, 16, 32, 64]:
    Ak = rank_k(A, k)
    hata = np.linalg.norm(A - Ak) / np.linalg.norm(A)
    oran = 100 * sikistirma_orani(m, n, k)
    sigma = s[k]                     # Eckart-Young: s_{k+1}
    print("%3d   %10.4f   %12.4e   %7.2f"
          % (k, hata, sigma, oran))
    satirlar.append((k, hata, oran))
if len(sys.argv) > 1:                # csv'yi kitap sekilleri icin yaz
    with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["k", "bagil_hata", "oran_yuzde"])
        for k, h, o in satirlar:
            w.writerow([k, "%.6f" % h, "%.4f" % o])
print("pinv testi (lstsq ile):",
      np.allclose(np.linalg.pinv(A),
                  np.linalg.lstsq(A, np.eye(m), rcond=None)[0]))
