# matmul_hiz.py: saf Python ucgen dongu ile NumPy matmul hiz olcumu
import csv
import sys
import time
import numpy as np


def saf_carpim(A, B):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C


def en_iyi(f, tekrar):
    zamanlar = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        zamanlar.append(time.perf_counter() - t0)
    return min(zamanlar)


rng = np.random.default_rng(42)
satirlar = []
print("   n   python_ms   numpy_us     oran")
for n in [16, 32, 64, 128, 256]:
    A = rng.standard_normal((n, n))
    B = rng.standard_normal((n, n))
    Al, Bl = A.tolist(), B.tolist()
    tp = en_iyi(lambda: saf_carpim(Al, Bl), 1 if n >= 128 else 3)
    tn = en_iyi(lambda: A @ B, 20)
    assert np.allclose(np.array(saf_carpim(Al, Bl)), A @ B)
    print("%4d  %9.3f  %10.2f  %8.0f"
          % (n, tp * 1e3, tn * 1e6, tp / tn))
    satirlar.append((n, tp, tn))
if len(sys.argv) > 1:
    with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "python_s", "numpy_s"])
        for n, tp, tn in satirlar:
            w.writerow([n, "%.8f" % tp, "%.8f" % tn])
