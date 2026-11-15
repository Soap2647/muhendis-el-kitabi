# altuzay.py: dort temel alt uzay (sutun, satir, bos, sol bos)
import numpy as np

A = np.array([[1.0, 2.0, 3.0],
              [2.0, 4.0, 6.0],
              [1.0, 0.0, 1.0]])
m, n = A.shape
r = np.linalg.matrix_rank(A)
print("rank(A) =", r, " m =", m, " n =", n)

# bos uzay N(A): A x = 0 cozumleri, SVD'nin sag tekil vektorleri
U, s, Vt = np.linalg.svd(A)
N = Vt[r:].T                       # n x (n - r)
print("N(A) boyutu =", N.shape[1])
print("N(A) tabani (sutun):", np.round(N[:, 0], 4))
print("A N = 0 ?", np.allclose(A @ N, 0))

# sol bos uzay N(A^T): A^T y = 0
Nl = U[:, r:]                      # m x (m - r)
print("N(A^T) boyutu =", Nl.shape[1], " A^T y = 0 ?",
      np.allclose(A.T @ Nl, 0))

# sutun uzayi C(A) ile bos uzayin dik olmasi
C = U[:, :r]
print("C(A) ile N(A^T) dik ?", np.allclose(C.T @ Nl, 0))

# A x = b cozulebilir mi? b in C(A) ise evet
b_iyi = A @ np.array([1.0, 0.0, 1.0])
b_kotu = np.array([1.0, 0.0, 0.0])
for ad, b in [("b_iyi", b_iyi), ("b_kotu", b_kotu)]:
    yon = Nl.T @ b                 # sol bos uzaydaki bilesen
    print(ad, "cozulebilir mi ?", np.allclose(yon, 0))
