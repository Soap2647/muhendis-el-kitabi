# -*- coding: utf-8 -*-
"""Bolum 61 - Cozumlu ornekler icin elle izlenebilir sayisal izler."""
import numpy as np

np.set_printoptions(precision=4, suppress=True)


def ornek_kmeans():
    print("== 1B k-means (k=2), X = [1, 2, 4, 8, 9, 11]")
    X = np.array([1.0, 2.0, 4.0, 8.0, 9.0, 11.0])
    C = np.array([1.0, 4.0])
    for t in range(1, 5):
        d = np.abs(X[:, None] - C[None, :])
        y = np.argmin(d, axis=1)
        J_eski = float(((X - C[y]) ** 2).sum())
        Cn = np.array([X[y == j].mean() for j in range(2)])
        print("iter %d: merkez=%s atama=%s J=%.2f"
              % (t, C, y + 1, J_eski))
        if np.allclose(Cn, C):
            print("  yakinsadi, merkez=%s J=%.4f" % (C, J_eski))
            break
        C = Cn
        J_yeni = float(((X - C[y]) ** 2).sum())
        print("   guncelleme sonrasi merkez=%s J=%.4f" % (C, J_yeni))


def pdf(x, m, s2):
    fark = (x - m) ** 2
    return np.exp(-fark / (2 * s2)) / np.sqrt(2 * np.pi * s2)


def ornek_em_1b():
    print("== 1B iki bilesenli GMM, bir EM iterasyonu")
    X = np.array([1.0, 2.0, 4.0, 8.0, 9.0, 11.0])
    mu = np.array([2.0, 9.0])
    sig2 = np.array([4.0, 4.0])
    pi = np.array([0.5, 0.5])
    N = np.column_stack([pi[j] * pdf(X, mu[j], sig2[j])
                         for j in range(2)])
    tot = N.sum(axis=1)
    R = N / tot[:, None]
    print("log-olabilirlik (E oncesi) = %.6f" % np.log(tot).sum())
    print("x      pi1*N1        pi2*N2        r1       r2")
    for i, x in enumerate(X):
        print("%-6.1f %-13.6f %-13.6f %-8.4f %-8.4f" % (
            x, N[i, 0], N[i, 1], R[i, 0], R[i, 1]))
    Nk = R.sum(axis=0)
    pi_y = Nk / len(X)
    mu_y = (R * X[:, None]).sum(axis=0) / Nk
    sig_y = (R * (X[:, None] - mu_y[None, :]) ** 2).sum(axis=0) / Nk
    print("Nk = %s" % Nk)
    print("yeni pi = %s" % pi_y)
    print("yeni mu = %s" % mu_y)
    print("yeni sigma^2 = %s" % sig_y)
    N2 = np.column_stack([pi_y[j] * pdf(X, mu_y[j], sig_y[j])
                          for j in range(2)])
    print("log-olabilirlik (M sonrasi) = %.6f"
          % np.log(N2.sum(axis=1)).sum())


def ornek_pca():
    print("== 2x2 kovaryans ile PCA")
    X = np.array([[1, 2], [2, 3], [3, 5], [4, 4], [5, 6]],
                 dtype=float)
    mu = X.mean(axis=0)
    Z = X - mu
    print("ortalama =", mu)
    print("merkezlenmis Z:\n", Z)
    S = Z.T @ Z / (len(X) - 1)
    print("kovaryans S:\n", S)
    lam, V = np.linalg.eigh(S)
    idx = np.argsort(lam)[::-1]
    lam, V = lam[idx], V[:, idx]
    print("ozdegerler =", lam)
    print("ozvektorler (sutun):\n", V)
    print("aciklanan oran =", lam / lam.sum())
    _, s, Vt = np.linalg.svd(Z, full_matrices=False)
    print("SVD: sigma^2/(n-1) =", s ** 2 / (len(X) - 1))
    print("SVD ana yon (Vt[0]) =", Vt[0])
    print("merkezlenmemis SVD ana yon:",
          np.linalg.svd(X, full_matrices=False)[2][0])


def ornek_mahalanobis():
    print("== Mahalanobis ile iki aday")
    S = np.array([[1.0, 0.9], [0.9, 1.0]])
    Si = np.linalg.inv(S)
    mu = np.zeros(2)
    adaylar = [("A", np.array([2.0, 2.0])),
               ("B", np.array([2.0, -1.5]))]
    for ad, x in adaylar:
        d_ok = np.linalg.norm(x - mu)
        d_m = np.sqrt((x - mu) @ Si @ (x - mu))
        print("%s x=%s Oklid=%.4f Mahalanobis=%.4f" % (
            ad, x, d_ok, d_m))
    print("Sigma^-1 =\n", Si)


if __name__ == "__main__":
    ornek_kmeans()
    ornek_em_1b()
    ornek_pca()
    ornek_mahalanobis()
