# -*- coding: utf-8 -*-
# b62_06_fuzyon_bayes.py: (1) tumleyen filtre = sabit kazancli Kalman,
# (2) cok sensorlu birlestirme (sirali = yigin), (3) Bayesci
# dogrusal regresyon (kapali form, Ridge = MAP), (4) MH dogrulama.
import numpy as np

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


# ---------- (1) IMU + GPS: tumleyen filtre ve Kalman ----------
def senaryo_imu_gps(n=600, dt=0.1, seed=62):
    rng = np.random.default_rng(seed)
    v = 5.0
    x = np.zeros(n)
    for k in range(1, n):
        x[k] = x[k - 1] + v * dt + rng.normal(0, 0.05)
    v_imu = v + 0.2 + rng.normal(0, 0.5, n)  # sabit yanlilik 0,2
    z_gps = x + rng.normal(0, 2.0, n)  # sigma = 2 m
    return x, v_imu, z_gps, dt


def tumleyen(v_imu, z, dt, alpha, x0=0.0):
    x = np.zeros(len(z))
    x[0] = x0
    for k in range(1, len(z)):
        x[k] = alpha * (x[k - 1] + v_imu[k] * dt) + (1 - alpha) * z[k]
    return x


def kalman_1b(v_imu, z, dt, Q, R, x0=0.0, P0=100.0):
    x, P = x0, P0
    out, K_ler = np.zeros(len(z)), np.zeros(len(z))
    out[0] = x
    for k in range(1, len(z)):
        x = x + v_imu[k] * dt  # tahmin (IMU ile)
        P = P + Q
        K = P / (P + R)  # kazanc
        x = x + K * (z[k] - x)  # guncelleme (GPS ile)
        P = (1 - K) * P
        out[k], K_ler[k] = x, K
    return out, K_ler


def tumleyen_ve_kalman():
    x, v_imu, z, dt = senaryo_imu_gps()
    Q, R = 0.0025, 4.0
    kal, K = kalman_1b(v_imu, z, dt, Q, R)
    # sabit kazanc: Riccati'nin durgun hali (P- ve P iterasyonu)
    P = 100.0
    for _ in range(2000):
        Pm = P + Q
        Kss = Pm / (Pm + R)
        P = (1 - Kss) * Pm
    alpha = 1 - Kss
    tum = tumleyen(v_imu, z, dt, alpha, x0=kal[0])
    print(
        "[Fuzyon] Kalman K (son adim) = %.5f, K_ss = %.5f"
        % (K[-1], Kss)
    )
    print("[Fuzyon] tumleyen alpha = 1 - K_ss = %.5f" % alpha)
    print(
        "[Fuzyon] RMS  ham GPS  = %.3f m"
        % np.sqrt(np.mean((z - x) ** 2))
    )
    print(
        "[Fuzyon] RMS  Kalman   = %.3f m"
        % np.sqrt(np.mean((kal - x) ** 2))
    )
    print(
        "[Fuzyon] RMS  tumleyen = %.3f m"
        % np.sqrt(np.mean((tum - x) ** 2))
    )
    print(
        "[Fuzyon] tumleyen-Kalman, 400. adimdan sonra fark: %.2e"
        % np.abs(tum[400:] - kal[400:]).max()
    )


# ---------- (2) Cok sensorlu olcum birlestirme ----------
def guncelle_kalman(x, P, z, H, R):
    S = H @ P @ H.T + R
    K = P @ H.T @ np.linalg.inv(S)
    x = x + K @ (z - H @ x)
    P = (np.eye(len(x)) - K @ H) @ P
    return x, P


def cok_sensor():
    rng = np.random.default_rng(7)
    x0 = rng.normal(size=3)
    P0 = np.diag([2.0, 1.0, 0.5])
    H1 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    H2 = np.array([[0.0, 1.0, 1.0]])
    R1 = np.diag([0.5, 0.8])
    R2 = np.array([[0.3]])
    z1 = rng.normal(size=2)
    z2 = rng.normal(size=1)
    # sirali: once 1, sonra 2
    x_s, P_s = guncelle_kalman(x0, P0, z1, H1, R1)
    x_s, P_s = guncelle_kalman(x_s, P_s, z2, H2, R2)
    # yigin: tek adimda iki olcum birlikte
    H = np.vstack([H1, H2])
    R = np.block([[R1, np.zeros((2, 1))], [np.zeros((1, 2)), R2]])
    x_y, P_y = guncelle_kalman(x0, P0, np.concatenate([z1, z2]), H, R)
    print(
        "\n[Cok sensor] sirali ve yigin farki (x): %.2e, (P): %.2e"
        % (np.abs(x_s - x_y).max(), np.abs(P_s - P_y).max())
    )


# ---------- (3) Bayesci dogrusal regresyon ----------
def bayes_lin(Phi, y, alpha, beta):
    """Onsel N(0, alpha^-1 I), olabilirlik N(Phi w, beta^-1 I)."""
    S_N = np.linalg.inv(
        alpha * np.eye(Phi.shape[1]) + beta * Phi.T @ Phi
    )
    m_N = beta * S_N @ Phi.T @ y
    return m_N, S_N


def ozellik(x):
    return np.column_stack([np.ones_like(x), x])


def bayes_bant():
    alpha, beta = 2.0, 1.0 / 0.3**2
    rng = np.random.default_rng(62)
    grid = np.linspace(-1, 1, 101)
    satirlar = ["N,x,ort,ss"]
    nokta = ["N,x,y"]
    for N in [2, 10, 50]:
        x = rng.uniform(-1, 1, N)
        y = 0.5 + 1.2 * x + rng.normal(0, 0.3, N)
        Phi = ozellik(x)
        m_N, S_N = bayes_lin(Phi, y, alpha, beta)
        G = ozellik(grid)
        ort = G @ m_N
        ss = np.sqrt(1 / beta + np.sum((G @ S_N) * G, axis=1))
        print(
            "N=%2d  m_N=(%.3f, %.3f)  tahmin belirsizligi x=0,9: %.3f"
            % (N, m_N[0], m_N[1], ss[95])
        )
        for g, o, s in zip(grid, ort, ss):
            satirlar.append("%d,%.4f,%.5f,%.5f" % (N, g, o, s))
        for a, b in zip(x, y):
            nokta.append("%d,%.4f,%.4f" % (N, a, b))
    with open(
        VERI + "/b62_bayes_bant.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    with open(
        VERI + "/b62_bayes_nokta.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(nokta) + "\n")


def ridge_esdegeri():
    from sklearn.linear_model import Ridge

    alpha, beta = 2.0, 1.0 / 0.3**2
    rng = np.random.default_rng(62)
    x = rng.uniform(-1, 1, 50)
    y = 0.5 + 1.2 * x + rng.normal(0, 0.3, 50)
    Phi = ozellik(x)
    m_N, _ = bayes_lin(Phi, y, alpha, beta)
    lam = alpha / beta
    w_r = np.linalg.solve(Phi.T @ Phi + lam * np.eye(2), Phi.T @ y)
    sk = Ridge(alpha=lam, fit_intercept=False).fit(Phi, y).coef_
    print("\n[MAP=Ridge] lambda = alpha/beta = %.5f" % lam)
    print("  sonsal ortalama m_N     :", np.round(m_N, 6))
    print("  Ridge kapali form       :", np.round(w_r, 6))
    print("  sklearn Ridge           :", np.round(sk, 6))


# ---------- (4) Metropolis-Hastings ile dogrulama ----------
def mh(Phi, y, alpha, beta, n=20000, adim=0.12, seed=1):
    rng = np.random.default_rng(seed)

    def log_post(w):
        r = y - Phi @ w
        return -0.5 * beta * r @ r - 0.5 * alpha * w @ w

    w = np.zeros(2)
    lp = log_post(w)
    zincir, kabul = np.zeros((n, 2)), 0
    for t in range(n):
        aday = w + rng.normal(0, adim, 2)
        lp_a = log_post(aday)
        if np.log(rng.random()) < lp_a - lp:
            w, lp = aday, lp_a
            kabul += 1
        zincir[t] = w
    return zincir[2000:], kabul / n


def mh_dogrulama():
    alpha, beta = 2.0, 1.0 / 0.3**2
    rng = np.random.default_rng(62)
    x = rng.uniform(-1, 1, 50)
    y = 0.5 + 1.2 * x + rng.normal(0, 0.3, 50)
    Phi = ozellik(x)
    m_N, S_N = bayes_lin(Phi, y, alpha, beta)
    zincir, kabul = mh(Phi, y, alpha, beta)
    print(
        "\n[MH] kabul orani = %.3f, ornek sayisi = %d"
        % (kabul, len(zincir))
    )
    print(
        "  MH ort       :",
        np.round(zincir.mean(axis=0), 4),
        " kapali form:",
        np.round(m_N, 4),
    )
    print("  MH kovaryans :", np.round(np.cov(zincir.T), 5).tolist())
    print("  kapali S_N   :", np.round(S_N, 5).tolist())


if __name__ == "__main__":
    print("== (1) Tumleyen filtre ve Kalman ==")
    tumleyen_ve_kalman()
    cok_sensor()
    print("\n== (3) Bayesci dogrusal regresyon ==")
    bayes_bant()
    ridge_esdegeri()
    print("\n== (4) MCMC dogrulama ==")
    mh_dogrulama()
