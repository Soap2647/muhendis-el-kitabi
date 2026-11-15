# lsq.py: en kucuk kareler: normal denklem, QR, lstsq
import numpy as np

rng = np.random.default_rng(42)
t = np.linspace(0.0, 1.0, 60)
irtifa = 120 + 80 * t - 40 * t**2 + rng.normal(0, 0.5, t.size)

for d in [3, 6, 10]:
    A = np.vander(t, d + 1, increasing=True)   # 1, t, t^2, ...
    x_norm = np.linalg.solve(A.T @ A, A.T @ irtifa)
    Q, R = np.linalg.qr(A)
    x_qr = np.linalg.solve(R, Q.T @ irtifa)
    x_ls = np.linalg.lstsq(A, irtifa, rcond=None)[0]
    print("derece %2d  cond(A)=%8.2e  cond(A^T A)=%8.2e"
          % (d, np.linalg.cond(A), np.linalg.cond(A.T @ A)))
    fark_n = np.max(np.abs(x_norm - x_ls))
    fark_q = np.max(np.abs(x_qr - x_ls))
    print("   fark(normal, lstsq)=%8.2e  fark(QR, lstsq)=%8.2e"
          % (fark_n, fark_q))
