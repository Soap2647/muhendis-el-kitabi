# solve_inv.py: inv(A) @ b ile solve(A, b): hiz ve dogruluk
import time
import numpy as np

rng = np.random.default_rng(42)
for n in [200, 800, 2000]:
    A = rng.standard_normal((n, n))
    x_gercek = rng.standard_normal(n)
    b = A @ x_gercek
    t0 = time.perf_counter()
    x1 = np.linalg.solve(A, b)
    t1 = time.perf_counter()
    x2 = np.linalg.inv(A) @ b
    t2 = time.perf_counter()
    e1 = np.max(np.abs(x1 - x_gercek))
    e2 = np.max(np.abs(x2 - x_gercek))
    print("n=%4d  solve: %7.4f s, hata %.1e | "
          "inv@b: %7.4f s, hata %.1e"
          % (n, t1 - t0, e1, t2 - t1, e2))
