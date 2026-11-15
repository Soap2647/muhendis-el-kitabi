# matris_turev.py: matris kalkülüsü kurallarını sayısal denetler.
# Tohum sabit (rastgele matrisler için); el ile örnek sabit sayılar.
import numpy as np


def sayisal_grad(f, A, h=1e-6):
    # Matris girdi için merkezi fark; sonuç A ile aynı şekilde.
    G = np.zeros_like(A, dtype=float)
    for idx in np.ndindex(A.shape):
        Ap, Am = A.copy(), A.copy()
        Ap[idx] += h
        Am[idx] -= h
        G[idx] = (f(Ap) - f(Am)) / (2 * h)
    return G


def softmax(z):
    e = np.exp(z - np.max(z))
    return e / e.sum()


def denetim():
    rng = np.random.default_rng(55)
    print("Kural, sayisal hata:")

    # 1) d(a^T x)/dx = a
    a = rng.normal(size=4)
    x = rng.normal(size=4)
    g = sayisal_grad(lambda v: a @ v, x)
    print("  d(a^T x)/dx = a      %.1e" % np.abs(g - a).max())

    # 2) d(x^T A x)/dx = (A + A^T) x
    A = rng.normal(size=(4, 4))
    g = sayisal_grad(lambda v: v @ A @ v, x)
    hata = np.abs(g - (A + A.T) @ x).max()
    print("  d(x^T A x)/dx        %.1e" % hata)

    # 3) d||Wx - y||^2 / dW = 2 (Wx - y) x^T   (W: 2x3)
    W = rng.normal(size=(2, 3))
    xv = rng.normal(size=3)
    yv = rng.normal(size=2)
    r = W @ xv - yv
    g = sayisal_grad(lambda M: np.sum((M @ xv - yv) ** 2), W)
    print("  d||Wx-y||^2/dW       %.1e  (sekil: %s)"
          % (np.abs(g - 2 * np.outer(r, xv)).max(), g.shape))

    # 4) Doğrusal katman y = Wx + b: dy/dx = W (Jacobian)
    b = rng.normal(size=2)
    J = sayisal_grad_vek(lambda v: W @ v + b, xv)
    print("  dy/dx (Jacobian) = W %.1e" % np.abs(J - W).max())

    # 5) Softmax Jacobian'ı: dp_i/dz_j = p_i (delta_ij - p_j)
    z = rng.normal(size=3)
    p = softmax(z)
    Jsm = np.diag(p) - np.outer(p, p)
    Jnum = sayisal_grad_vek(softmax, z)
    hata = np.abs(Jsm - Jnum).max()
    print("  softmax J = diag(p)-pp^T %.1e" % hata)

    # 6) Çapraz entropi + softmax: dL/dz = p - y
    y = np.zeros(3)
    y[1] = 1.0
    L = lambda zz: -np.log(softmax(zz)[1])
    gL = sayisal_grad_vek(lambda zz: np.array([L(zz)]), z).ravel()
    print("  dL/dz = p - y        %.1e" % np.abs(gL - (p - y)).max())


def sayisal_grad_vek(f, x, h=1e-6):
    # Vektör -> vektör fonksiyonun Jacobian'ı: satır i, dy_i/dx_j.
    x = np.asarray(x, dtype=float)
    cols = []
    for j in range(x.size):
        xp, xm = x.copy(), x.copy()
        xp[j] += h
        xm[j] -= h
        fp, fm = np.atleast_1d(f(xp)), np.atleast_1d(f(xm))
        cols.append((fp - fm) / (2 * h))
    return np.stack(cols, axis=1)


def ornek3():
    # Çözümlü Örnek 3 ile aynı sayılar: W 2x3, x 3, y 2, b = 0.
    W = np.array([[1.0, 2.0, 0.0], [0.0, 1.0, -1.0]])
    x = np.array([1.0, 0.0, 2.0])
    y = np.array([0.0, 1.0])
    r = W @ x - y
    L = np.sum(r ** 2)
    grad = 2 * np.outer(r, x) + 0.0   # -0.0 yerine 0.0 yazdirmak icin
    print("Wx =", W @ x, " r = Wx - y =", r)
    print("L = ||r||^2 =", L)
    print("dL/dW =")
    print(grad)
    g = sayisal_grad(lambda M: np.sum((M @ x - y) ** 2), W)
    print("sayisal fark = %.1e" % np.abs(g - grad).max())


if __name__ == "__main__":
    denetim()
    print()
    ornek3()
