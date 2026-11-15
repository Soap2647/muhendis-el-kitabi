# -*- coding: utf-8 -*-
# b62_05_ekf_pf.py: Radar olcumlu hedef takibi. EKF (Jacobian ile
# dogrusallastirma) ve parcacik filtresi (sistematik yeniden
# ayni senaryoda karsilastirma. Kalman modeli b62_04'ten.
import time
import numpy as np
from b62_04_kalman import model_b, simule, tahmin, guncelle

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
RADAR = np.array([0.0, 0.0])  # radar konumu (orijin)


def radar_olc(x):
    """Menzil r = sqrt(px^2+py^2), yon acisi theta = atan2(py, px)."""
    dx, dy = x[0] - RADAR[0], x[1] - RADAR[1]
    return np.array([np.hypot(dx, dy), np.arctan2(dy, dx)])


def radar_jakobiyen(x):
    """h(x) icin 2x4 Jacobian (durum [px,py,vx,vy])."""
    dx, dy = x[0] - RADAR[0], x[1] - RADAR[1]
    r2 = dx * dx + dy * dy
    r = np.sqrt(r2)
    return np.array(
        [[dx / r, dy / r, 0, 0], [-dy / r2, dx / r2, 0, 0]]
    )


def aci_sar(a):
    """Aciyi [-pi, pi) araligina getirir (inovasyonda sart)."""
    return (a + np.pi) % (2 * np.pi) - np.pi


def ekf(zs, F, Q, R, x0, P0):
    x, P = x0.copy(), P0.copy()
    xs = []
    for k in range(len(zs)):
        if k > 0:
            x, P = tahmin(x, P, F, Q)
        H = radar_jakobiyen(x)
        nu = zs[k] - radar_olc(x)
        nu[1] = aci_sar(nu[1])
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)
        x = x + K @ nu
        IKH = np.eye(4) - K @ H
        P = IKH @ P @ IKH.T + K @ R @ K.T
        xs.append(x.copy())
    return np.array(xs)


def sistematik_yeniden_ornekle(agirlik, rng):
    """Sistematik yeniden ornekleme: tek u0, N esit aralik."""
    n = len(agirlik)
    konum = (rng.random() + np.arange(n)) / n
    kum = np.cumsum(agirlik)
    kum[-1] = 1.0
    return np.searchsorted(kum, konum)


def parcacik(zs, F, Q, R, x0, P0, N, rng):
    parc = rng.multivariate_normal(x0, P0, size=N)
    w = np.full(N, 1.0 / N)
    Lq = np.linalg.cholesky(Q + 1e-12 * np.eye(4))
    Ri = np.linalg.inv(R)
    xs, ess_log = [], []
    for k in range(len(zs)):
        if k > 0:
            parc = parc @ F.T + rng.standard_normal((N, 4)) @ Lq.T
        # olabilirlik: log w += log N(z; h(x), R), aci farki sarmali
        dx = parc[:, 0] - RADAR[0]
        dy = parc[:, 1] - RADAR[1]
        nu = np.column_stack(
            [
                zs[k][0] - np.hypot(dx, dy),
                aci_sar(zs[k][1] - np.arctan2(dy, dx)),
            ]
        )
        logw = -0.5 * np.einsum("ni,ij,nj->n", nu, Ri, nu)
        logw += np.log(w + 1e-300)
        logw -= logw.max()
        w = np.exp(logw)
        w /= w.sum()
        ess_log.append(1.0 / np.sum(w**2))
        xs.append(w @ parc)
        idx = sistematik_yeniden_ornekle(w, rng)
        parc = parc[idx]
        w = np.full(N, 1.0 / N)
    return np.array(xs), np.array(ess_log)


def senaryo(
    seed, n=60, x_bas=(-60.0, 8.0, 3.0, -1.0), rad_sig=(3.0, 1.5)
):
    """Hedef radara yakin gecer; radar acisi dogrusal olmayan.
    Gercek model: sabit hiz + kucuk ivme gurultusu (b62_04 ile ayni).
    """
    F, G, Q, H, R_k = model_b(q=0.5, sigma=5.0)
    rng = np.random.default_rng(seed)
    xt = np.zeros((n, 4))
    x = np.array(x_bas, float)
    for k in range(n):
        x = F @ x + G @ rng.normal(0, np.sqrt(0.5), 2)
        xt[k] = x
    rad_sigma = np.array([rad_sig[0], np.radians(rad_sig[1])])
    zs = np.array(
        [
            radar_olc(xt[k]) + rng.normal(0, rad_sigma)
            for k in range(n)
        ]
    )
    for k in range(n):
        zs[k][1] = aci_sar(zs[k][1])
    R = np.diag(rad_sigma**2)
    return xt, zs, F, Q, R


def konum_rms(xs, xt):
    return float(
        np.sqrt(np.mean(np.sum((xs[:, :2] - xt[:, :2]) ** 2, 1)))
    )


def ilk_durum(zs, R):
    """Ilk tahmin: ilk olcumden konum, hiz belirsiz."""
    r, th = zs[0]
    x0 = np.array([r * np.cos(th), r * np.sin(th), 0.0, 0.0])
    P0 = np.diag([25.0, 25.0, 25.0, 25.0])
    return x0, P0


def karsilastir(kosu=30, **sk):
    n = 60
    ekf_h, pf_h, pf_t = [], [], []
    for s in range(kosu):
        xt, zs, F, Q, R = senaryo(3000 + s, n, **sk)
        x0, P0 = ilk_durum(zs, R)
        ekf_h.append(konum_rms(ekf(zs, F, Q, R, x0, P0), xt))
        t0 = time.time()
        xp, _ = parcacik(
            zs, F, Q, R, x0, P0, 1000, np.random.default_rng(s)
        )
        pf_t.append(time.time() - t0)
        pf_h.append(konum_rms(xp, xt))
    ekf_h, pf_h = np.array(ekf_h), np.array(pf_h)
    print("\n[EKF vs PF] %d kosu, N=1000, n=%d adim" % (kosu, n))
    print(
        "EKF konum RMS: ort %.3f  medyan %.3f  en kotu %.3f"
        % (ekf_h.mean(), np.median(ekf_h), ekf_h.max())
    )
    print(
        "PF  konum RMS: ort %.3f  medyan %.3f  en kotu %.3f"
        % (pf_h.mean(), np.median(pf_h), pf_h.max())
    )
    print("PF kosu suresi ort: %.2f s" % np.mean(pf_t))


def parcacik_sayisi(kosu=30):
    n = 60
    print("\n[N etkisi] PF konum RMS, ESS ort.")
    satirlar = ["N,rms_ort,rms_ss,ess_ort"]
    for N in [10, 50, 200, 1000, 5000]:
        rm, ess = [], []
        for s in range(kosu):
            xt, zs, F, Q, R = senaryo(3000 + s, n)
            x0, P0 = ilk_durum(zs, R)
            xp, e = parcacik(
                zs, F, Q, R, x0, P0, N, np.random.default_rng(100 + s)
            )
            rm.append(konum_rms(xp, xt))
            ess.append(e.mean())
        rm = np.array(rm)
        print(
            "N=%5d  RMS %.3f (ss %.3f)  ESS ort %.1f"
            % (N, rm.mean(), rm.std(), np.mean(ess))
        )
        satirlar.append(
            "%d,%.5f,%.5f,%.3f"
            % (N, rm.mean(), rm.std(), np.mean(ess))
        )
    with open(VERI + "/b62_pf_N.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


def radar_iz(seed=3000):
    """Tek kosu: gercek, EKF ve PF yorungeleri (sekil icin CSV)."""
    n = 60
    xt, zs, F, Q, R = senaryo(seed, n)
    x0, P0 = ilk_durum(zs, R)
    xe = ekf(zs, F, Q, R, x0, P0)
    xp, _ = parcacik(
        zs, F, Q, R, x0, P0, 1000, np.random.default_rng(seed)
    )
    satirlar = ["k,tx,ty,ex,ey,px,py"]
    for k in range(n):
        satirlar.append(
            "%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f"
            % (
                k,
                xt[k, 0],
                xt[k, 1],
                xe[k, 0],
                xe[k, 1],
                xp[k, 0],
                xp[k, 1],
            )
        )
    with open(VERI + "/b62_radar_iz.csv", "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
    print(
        "\n[Tek kosu] EKF RMS %.3f, PF RMS %.3f"
        % (konum_rms(xe, xt), konum_rms(xp, xt))
    )


if __name__ == "__main__":
    print("== EKF vs PF ==")
    karsilastir(30)
    karsilastir(30, x_bas=(-12.0, 4.0, 2.0, 0.0), rad_sig=(3.0, 5.0))
    print("\n== Parcacik sayisi ==")
    parcacik_sayisi(30)
    radar_iz(3000)
