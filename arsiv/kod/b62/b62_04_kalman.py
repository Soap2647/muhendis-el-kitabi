# -*- coding: utf-8 -*-
# b62_04_kalman.py: Kalman filtresi sifirdan. (1) 1B ornek izi,
# (2) 2B sabit hiz (DWNA) hedef takibi, (3) NEES/NIS tutarlilik,
# (4) eksik olcum, (5) Q/R ayari, (6) filterpy karsilastirmasi.
import numpy as np

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def tahmin(x, P, F, Q):
    """Tahmin adimi: x- = F x, P- = F P F^T + Q."""
    return F @ x, F @ P @ F.T + Q


def guncelle(x, P, z, H, R):
    """Guncelleme adimi. Joseph bicimi P'yi kararli tutar."""
    nu = z - H @ x  # inovasyon (yenilik)
    S = H @ P @ H.T + R  # inovasyon kovaryansi
    K = P @ H.T @ np.linalg.inv(S)  # Kalman kazanci
    x = x + K @ nu
    IKH = np.eye(len(x)) - K @ H
    P = IKH @ P @ IKH.T + K @ R @ K.T
    return x, P, K, nu, S


def ornek4_iz():
    """1B rastgele yuruyus: x_k = x_{k-1} + w, z_k = x_k + v."""
    x, P = np.array([0.0]), np.array([[10.0]])
    Q, R = 0.1, 1.0
    zs = [2.0, 1.5, 3.0]
    print("adim    x-      P-      K       nu      x^      P")
    for k, z in enumerate(zs, 1):
        xm, Pm = tahmin(x, P, np.array([[1.0]]), np.array([[Q]]))
        x, P, K, nu, S = guncelle(
            xm, Pm, np.array([z]), np.array([[1.0]]), np.array([[R]])
        )
        print(
            "%d  %7.4f %7.4f %7.4f %7.4f %7.4f %7.4f"
            % (k, xm[0], Pm[0, 0], K[0, 0], nu[0], x[0], P[0, 0])
        )
        # Iki Gauss'un carpimi: 1/P = 1/P- + 1/R
        assert abs(1 / P[0, 0] - (1 / Pm[0, 0] + 1 / R)) < 1e-9


def model_b(dt=1.0, q=0.5, sigma=5.0):
    """2B sabit hiz, durum = [px, py, vx, vy]; ivme gurultusu DWNA."""
    F = np.array(
        [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]],
        float,
    )
    G = np.array(
        [[dt**2 / 2, 0], [0, dt**2 / 2], [dt, 0], [0, dt]], float
    )
    Q = q * G @ G.T  # sigma_a^2 = q
    H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], float)
    R = sigma**2 * np.eye(2)
    return F, G, Q, H, R


def simule(n, F, G, q, sigma, rng, x0=(0, 0, 20, 5)):
    """Gercek yorunge (ivme gurultulu) ve gurultulu olcumler."""
    x = np.array(x0, float)
    xs, zs = [], []
    for _ in range(n):
        a = rng.normal(0, np.sqrt(q), 2)
        x = F @ x + G @ a
        xs.append(x.copy())
        zs.append(x[:2] + rng.normal(0, sigma, 2))
    return np.array(xs), np.array(zs)


def filtrele(zs, F, Q, H, R, sigma, eksik=None):
    """Kalman takibi. eksik: olcumsuz adimlarin bool dizisi."""
    x = np.array([zs[0][0], zs[0][1], 0.0, 0.0])
    P = np.diag([sigma**2, sigma**2, 100.0, 100.0])
    xs, Ps, nees, nis = [], [], [], []
    for k in range(len(zs)):
        if k > 0:
            x, P = tahmin(x, P, F, Q)
        if eksik is not None and eksik[k]:
            xs.append(x.copy())
            Ps.append(P.copy())
            continue
        x, P, K, nu, S = guncelle(x, P, zs[k], H, R)
        xs.append(x.copy())
        Ps.append(P.copy())
        nis.append(float(nu @ np.linalg.solve(S, nu)))
    return np.array(xs), np.array(Ps), np.array(nis)


def rms(a, b):
    return float(np.sqrt(np.mean(np.sum((a - b) ** 2, axis=-1))))


def tutarlilik(n_kosu=50, n=100):
    """NEES (4 boyut) ve NIS (2 boyut) ortalamalari; dogru modelde
    NEES ~ 4 ve NIS ~ 2 beklenir."""
    F, G, Q, H, R = model_b()
    sonuc = {"dogru": [], "kucuk_q": []}
    for kosu in range(n_kosu):
        rng = np.random.default_rng(1000 + kosu)
        xt, zs = simule(n, F, G, 0.5, 5.0, rng)
        for ad, qm in [("dogru", 0.5), ("kucuk_q", 0.005)]:
            Qm = model_b(q=qm)[2]
            xs, Ps, nis = filtrele(zs, F, Qm, H, R, 5.0)
            e = xt - xs
            nees = [
                float(e[k] @ np.linalg.solve(Ps[k], e[k]))
                for k in range(n)
            ]
            sonuc[ad].append([np.mean(nees), np.mean(nis)])
    for ad in sonuc:
        a = np.array(sonuc[ad]).mean(axis=0)
        print(
            "[Tutarlilik] %-8s NEES=%.3f (4)  NIS=%.3f (2)"
            % (ad, a[0], a[1])
        )


def ayar_deneyi(n_kosu=50, n=100):
    """Gercek q=0.5, sigma=5. Model q ve R olcegi degisince RMS."""
    F, G, Q, H, R = model_b()
    qs = [0.005, 0.05, 0.5, 5.0, 50.0]
    olcekler = [0.25, 1.0, 4.0]
    tablo = np.zeros((len(qs), len(olcekler)))
    for kosu in range(n_kosu):
        rng = np.random.default_rng(2000 + kosu)
        xt, zs = simule(n, F, G, 0.5, 5.0, rng)
        for i, qm in enumerate(qs):
            for j, sc in enumerate(olcekler):
                _, _, Qm, Hm, Rm = model_b(
                    q=qm, sigma=5.0 * np.sqrt(sc)
                )
                xs, _, _ = filtrele(
                    zs, F, Qm, Hm, Rm, 5.0 * np.sqrt(sc)
                )
                tablo[i, j] += rms(xs[:, :2], xt[:, :2]) / n_kosu
    print(
        "\n[Ayar] ort. RMS (m); satir q, sutun R olcegi 0.25 / 1 / 4"
    )
    for i, qm in enumerate(qs):
        print("q=%7.3f  %.3f  %.3f  %.3f" % (qm, *tablo[i]))
    satirlar = ["q,r025,r1,r4"]
    for i, qm in enumerate(qs):
        satirlar.append("%g,%.5f,%.5f,%.5f" % (qm, *tablo[i]))
    with open(VERI + "/b62_qr_ayar.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


def takip_ve_eksik(n=100):
    F, G, Q, H, R = model_b()
    rng = np.random.default_rng(62)
    xt, zs = simule(n, F, G, 0.5, 5.0, rng)
    xs, Ps, nis = filtrele(zs, F, Q, H, R, 5.0)
    print("\n[Takip] ham olcum RMS = %.3f m" % rms(zs, xt[:, :2]))
    print(
        "[Takip] filtre RMS    = %.3f m" % rms(xs[:, :2], xt[:, :2])
    )
    satirlar = ["k,tx,ty,zx,zy,fx,fy"]
    for k in range(n):
        satirlar.append(
            "%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f"
            % (
                k,
                xt[k, 0],
                xt[k, 1],
                zs[k, 0],
                zs[k, 1],
                xs[k, 0],
                xs[k, 1],
            )
        )
    with open(
        VERI + "/b62_takip_yorunge.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")
    # Eksik olcum: 40-59 arasi yalnizca tahmin
    eksik = np.zeros(n, bool)
    eksik[40:60] = True
    xe, Pe, _ = filtrele(zs, F, Q, H, R, 5.0, eksik=eksik)
    print("[Eksik] 20 adim olcum yok: pozisyon belirsizligi (iz P)")
    for k in [39, 45, 55, 59, 65]:
        print(
            "   k=%d  sqrt(trP_konum)=%.2f  hata=%.2f"
            % (
                k,
                np.sqrt(np.trace(Pe[k][:2, :2])),
                np.linalg.norm(xe[k, :2] - xt[k, :2]),
            )
        )


def filterpy_karsilastir(n=100):
    import filterpy
    from filterpy.kalman import KalmanFilter

    F, G, Q, H, R = model_b()
    rng = np.random.default_rng(62)
    xt, zs = simule(n, F, G, 0.5, 5.0, rng)
    xs, _, _ = filtrele(zs, F, Q, H, R, 5.0)
    kf = KalmanFilter(dim_x=4, dim_z=2)
    kf.x = np.array([[zs[0][0]], [zs[0][1]], [0.0], [0.0]])
    kf.F, kf.H, kf.Q, kf.R = F, H, Q, R
    kf.P = np.diag([25.0, 25.0, 100.0, 100.0])
    fp = []
    for k in range(n):
        if k > 0:
            kf.predict()
        kf.update(zs[k])
        fp.append(kf.x.ravel().copy())
    fp = np.array(fp)
    print(
        "\n[filterpy %s] en buyuk fark (kendi - filterpy): %.2e"
        % (filterpy.__version__, np.abs(xs - fp).max())
    )


if __name__ == "__main__":
    print("== 1B ornek izi ==")
    ornek4_iz()
    print("\n== 2B takip ve tutarlilik ==")
    takip_ve_eksik()
    tutarlilik()
    ayar_deneyi()
    filterpy_karsilastir()
