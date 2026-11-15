# -*- coding: utf-8 -*-
"""Bolum 61 - Uygulamalar (SENTETIK veri).

IHA telemetrisi, batarya hucresi ve renk paleti nicemleme.
"""
import warnings

import numpy as np
from sklearn.cluster import KMeans
from sklearn.covariance import MinCovDet
from sklearn.datasets import load_sample_image
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import adjusted_rand_score, roc_auc_score
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

MODLAR = {
    "seyir": ([22.0, 0.0, 0.0, 2.0, 18.0, 0.20], 1.0),
    "tirmanis": ([18.0, 3.0, 0.0, 10.0, 30.0, 0.25], 1.0),
    "donus": ([20.0, 0.0, 25.0, 3.0, 24.0, 0.35], 1.2),
    "alcalis": ([19.0, -3.0, 0.0, -8.0, 12.0, 0.20], 1.0),
}
STD = np.array([0.8, 0.4, 1.5, 1.0, 1.2, 0.02])
# Hiz ve akim, titresim ile birlikte degisir (koordineli)
KORELASYON = np.array([
    [1.0, 0.1, 0.0, 0.0, 0.6, 0.2],
    [0.1, 1.0, 0.0, 0.3, 0.1, 0.0],
    [0.0, 0.0, 1.0, 0.2, 0.0, 0.3],
    [0.0, 0.3, 0.2, 1.0, 0.0, 0.0],
    [0.6, 0.1, 0.0, 0.0, 1.0, 0.5],
    [0.2, 0.0, 0.3, 0.0, 0.5, 1.0],
])


def iha_verisi(seed=61, n_mod=1000, n_ano=20):
    """Sentetik telemetri: 4 mod, her biri n_mod normal pencere.

    Anomali turleri (her biri n_ano pencere):
    motor (akim artar, hiz duser), kanat (yatis oynar)
    ve sensor donmasi (titresim sabit kalir).
    """
    rng = np.random.default_rng(seed)
    cov = np.outer(STD, STD) * KORELASYON
    X, y_mod = [], []
    for j, (ad, (mu, olcek)) in enumerate(MODLAR.items()):
        Z = rng.multivariate_normal(mu, cov * olcek ** 2, size=n_mod)
        X.append(Z)
        y_mod += [j] * n_mod
    Xn = np.vstack(X)
    y_mod = np.array(y_mod)
    Xa, ya = [], []
    base = np.array(MODLAR["seyir"][0])
    # motor: akim yukselir, titresim artar, hiz duser
    Z = rng.multivariate_normal(base, cov, size=n_ano)
    Z[:, 4] += 4.0
    Z[:, 5] += 0.07
    Z[:, 0] -= 1.5
    Xa.append(Z)
    ya += ["motor"] * n_ano
    # kanat: yatis oynar, titresim artar
    Z = rng.multivariate_normal(base, cov, size=n_ano)
    Z[:, 2] += rng.choice([-1, 1], size=n_ano) * 4.0
    Z[:, 5] += 0.06
    Xa.append(Z)
    ya += ["kanat"] * n_ano
    # donma: titresim sabit deger (noktada normal)
    Z = rng.multivariate_normal(base, cov, size=n_ano)
    Z[:, 5] = base[5]
    Xa.append(Z)
    ya += ["donma"] * n_ano
    Xa = np.vstack(Xa)
    return Xn, y_mod, Xa, np.array(ya)


def bolum_a_ucus_modlari():
    Xn, ym, Xa, ya = iha_verisi()
    sc = StandardScaler().fit(Xn)
    Zn = sc.transform(Xn)
    print("A) sentetik telemetri: %d normal pencere, 4 mod" % len(Xn))
    km = KMeans(n_clusters=4, n_init=10, random_state=61).fit(Zn)
    gm = GaussianMixture(n_components=4, n_init=5, random_state=61)
    lab_gm = gm.fit(Zn).predict(Zn)
    for ad, lab in [("k-means k=4", km.labels_), ("GMM k=4", lab_gm)]:
        print("   %-12s ARI(mod)=%.4f siluet=%.4f" % (
            ad, adjusted_rand_score(ym, lab),
            silhouette_score(Zn, lab)))
    print("   (siluet, gercek mod etiketi kullanilmadan hesaplanir)")
    return sc, Zn


def egitim_mcd_skor(mcd, X):
    return mcd.mahalanobis(X)


def bolum_b_anomali(sc, Zn):
    Xn, ym, Xa, ya = iha_verisi(seed=62, n_mod=1000, n_ano=20)
    Ztr = sc.transform(Xn)
    rng = np.random.default_rng(63)
    idx = rng.permutation(len(Ztr))
    egitim, dogrulama = Ztr[idx[:3000]], Ztr[idx[3000:]]
    Za = sc.transform(Xa)
    print("B) anomali tespiti: egitim = yalnizca normal ucuslar")
    print("   test: 1000 normal + 60 anomali (3 tur)")
    Zt = np.vstack([dogrulama, Za])
    y = np.r_[np.zeros(len(dogrulama)), np.ones(len(Za))].astype(int)

    mcd = MinCovDet(random_state=61).fit(egitim)
    s_mcd = mcd.mahalanobis(Zt)
    gmm = GaussianMixture(n_components=4, n_init=5,
                          random_state=61).fit(egitim)
    s_gmm = -gmm.score_samples(Zt)
    iforest = IsolationForest(n_estimators=200, max_samples=256,
                              random_state=61).fit(egitim)
    s_if = -iforest.score_samples(Zt)
    pca = PCA(n_components=4).fit(egitim)
    Rt = Zt - pca.mean_
    C = pca.components_
    res = np.linalg.norm(Rt - Rt @ C.T @ C, axis=1)
    print("   AUC Mahalanobis (MCD, tek Gauss) = %.4f" %
          roc_auc_score(y, s_mcd))
    print("   AUC GMM(k=4) -llh                = %.4f" %
          roc_auc_score(y, s_gmm))
    print("   AUC Isolation Forest             = %.4f" %
          roc_auc_score(y, s_if))
    print("   AUC PCA artigi (4 bilesen)       = %.4f" %
          roc_auc_score(y, res))
    print("   esik: egitimin %99'u; tur bazinda tespit orani:")
    tur = np.r_[np.array(["normal"] * len(dogrulama)), ya]
    adaylar = [
        ("Mahal", s_mcd, egitim_mcd_skor(mcd, egitim)),
        ("GMM", s_gmm, -gmm.score_samples(egitim)),
        ("IF", s_if, -iforest.score_samples(egitim))]
    for ad, skor, sk_egit in adaylar:
        esik = np.quantile(sk_egit, 0.99)
        alarm = skor > esik
        satir = []
        for t in ["normal", "motor", "kanat", "donma"]:
            satir.append("%s=%.3f" % (t, alarm[tur == t].mean()))
        print("   %-5s %s" % (ad, "  ".join(satir)))
    return egitim, Zt, y, ya, gmm, iforest


def bolum_c_yanlis_alarm_butcesi(egitim, Zt, y, gmm):
    print("C) yanlis alarm butcesi: GMM, 2 s pencere, 1 saat=1800")
    s_e = -gmm.score_samples(egitim)
    s_t = -gmm.score_samples(Zt)
    for oran in [0.01, 0.001]:
        esik = np.quantile(s_e, 1 - oran)
        alarm = s_t > esik
        fa = alarm[y == 0].mean()
        print("   hedef %.3f: esik=%.3f normal alarm=%.5f" % (
            oran, esik, fa))
        print("   saatte yanlis alarm=%.2f tespit=%.3f" % (
            fa * 1800, alarm[y == 1].mean()))


def bolum_d_batarya_hucresi():
    """Sentetik EV batarya modulu: 96 hucre, 3 olcum (V, R, T)."""
    rng = np.random.default_rng(64)
    n = 96
    V = rng.normal(3.62, 0.004, n)
    R = rng.normal(20.0, 0.6, n)
    T = rng.normal(31.0, 0.5, n)
    R[17] += 9.0                       # yuksek ic direnc, V normal
    V[62] -= 0.05
    T[62] += 4.0                       # dusuk V ve yuksek T birlikte
    X = np.column_stack([V, R, T])
    print("D) sentetik batarya modulu: 96 hucre (V, R, T)")
    med = np.median(X, axis=0)
    mad = 1.4826 * np.median(np.abs(X - med), axis=0)
    rz = np.abs(X - med) / mad
    skor = rz.max(axis=1)
    top_rz = np.argsort(-skor)[:3]
    print("   robust z en yuksek 3:", top_rz,
          np.round(skor[top_rz], 2))
    mcd = MinCovDet(random_state=61).fit(X)
    d = mcd.mahalanobis(X)
    top_m = np.argsort(-d)[:3]
    print("   MCD Mahalanobis^2 en yuksek 3:", top_m,
          np.round(d[top_m], 1))
    print("   gercek anomali indeksleri: 17 ve 62")


def bolum_e_renk_paleti():
    img = load_sample_image("china.jpg").astype(np.float64) / 255.0
    h, w, _ = img.shape
    P = img.reshape(-1, 3)
    rng = np.random.default_rng(61)
    alt = P[rng.choice(len(P), size=5000, replace=False)]
    km = KMeans(n_clusters=16, n_init=3, random_state=61).fit(alt)
    palet = km.cluster_centers_
    d2 = ((P[:, None, :] - palet[None, :, :]) ** 2).sum(axis=2)
    etiket = np.argmin(d2, axis=1)
    R = palet[etiket].reshape(h, w, 3)
    mse = np.mean((img - R) ** 2)
    psnr = 10 * np.log10(1.0 / mse)
    bit_orj = h * w * 24
    bit_q = h * w * 4 + 16 * 24
    print("E) renk paleti: %dx%d piksel, k=16" % (w, h))
    print("   PSNR = %.2f dB" % psnr)
    print("   piksel basina: 24 bit -> 4 bit (+ palet 16x24 bit)")
    print("   toplam bit: %d -> %d" % (bit_orj, bit_q))
    print("   oran = %.2f" % (bit_orj / bit_q))


if __name__ == "__main__":
    sc, Zn = bolum_a_ucus_modlari()
    egitim, Zt, y, ya, gmm, iforest = bolum_b_anomali(sc, Zn)
    bolum_c_yanlis_alarm_butcesi(egitim, Zt, y, gmm)
    bolum_d_batarya_hucresi()
    bolum_e_renk_paleti()
