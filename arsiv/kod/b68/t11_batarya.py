# -*- coding: utf-8 -*-
"""Bölüm 68.10 (uygulama): sentetik batarya hücresi gerilim serisinde
sağlıklı/bozulmuş sınıflandırması. Grup (hücre) bölmesi ile rastgele
pencere bölmesi karşılaştırılır. Tohum 11, 12, 13; CPU."""
import numpy as np
from ortak import Tekrarli, egit, tahmin, yaz_csv

W, ADIM, N_HUCRE = 60, 20, 60


def hucre(rng, bozuk):
    """Dakikada 1 örnek (dt=1 s). Gerilim = OCV(SOC) - I*R + gürültü.
    Bozulmuş hücrede iç direnç R daha büyüktür."""
    n = 3000
    Q = rng.uniform(2.8, 3.2)           # kapasite (Ah), hücreye özgü
    soc = rng.uniform(0.85, 0.95)
    R = (rng.uniform(0.030, 0.036) if bozuk
         else rng.uniform(0.018, 0.024))
    Tamb = rng.uniform(23, 27)
    mu_c = rng.uniform(-0.5, 1.0)          # ortalama akım (A)
    ar = 0.0
    V, I, T = np.zeros(n), np.zeros(n), np.zeros(n)
    for t in range(n):
        ar = 0.95 * ar + rng.normal(0, 0.6)
        I[t] = np.clip(mu_c + ar, -4, 8)
        V[t] = 3.0 + 1.2 * soc - I[t] * R + rng.normal(0, 0.005)
        T[t] = Tamb + 0.8 * I[t] ** 2 * R + rng.normal(0, 0.05)
        soc = np.clip(soc - I[t] / (3600 * Q), 0.0, 1.0)
    return np.column_stack([V, I, T]), bozuk


def pencereler(seriler):
    X, y, g = [], [], []
    for cid, (Z, b) in enumerate(seriler):
        for i in range(0, len(Z) - W + 1, ADIM):
            X.append(Z[i:i + W]); y.append(int(b)); g.append(cid)
    return (np.array(X, np.float32), np.array(y, np.float32),
            np.array(g))


def fiziksel_r(X):
    """Her pencerede V'yi I'ya regrese et; eğim = -R tahmini."""
    out = []
    for w in X:
        A = np.column_stack([np.ones(W), w[:, 1]])
        kat, *_ = np.linalg.lstsq(A, w[:, 0], rcond=None)
        out.append(-kat[1])
    return np.array(out)


def calistir(tohum):
    rng = np.random.default_rng(tohum)
    seriler = [hucre(rng, k >= N_HUCRE // 2) for k in range(N_HUCRE)]
    # grup bölmesi: sınıf içinde hücre tabanlı 70/15/15
    rs = np.random.default_rng(tohum + 1)
    sag = [k for k in range(N_HUCRE // 2)]
    bz = [k for k in range(N_HUCRE // 2, N_HUCRE)]
    rs.shuffle(sag); rs.shuffle(bz)
    grp = {"tr": sag[:21] + bz[:21], "va": sag[21:25] + bz[21:25],
           "te": sag[25:] + bz[25:]}
    Xa, ya, ga = pencereler(seriler)
    res = {}
    # 1) grup bölmesi
    tr = np.isin(ga, grp["tr"]); va = np.isin(ga, grp["va"])
    te = np.isin(ga, grp["te"])
    res["grup"] = deney(Xa, ya, tr, va, te, tohum)
    # 2) rastgele pencere bölmesi (aynı hücreler her yerde)
    perm = rs.permutation(len(Xa))
    k1, k2 = int(0.7 * len(Xa)), int(0.85 * len(Xa))
    tr2 = np.zeros(len(Xa), bool); tr2[perm[:k1]] = True
    va2 = np.zeros(len(Xa), bool); va2[perm[k1:k2]] = True
    te2 = np.zeros(len(Xa), bool); te2[perm[k2:]] = True
    res["rastgele"] = deney(Xa, ya, tr2, va2, te2, tohum)
    # 3) fiziksel özellik: eğim tabanlı eşik (eğitimde seçilir)
    r = fiziksel_r(Xa)
    esikler = np.linspace(0.02, 0.04, 201)
    acc = [np.mean((r[tr] > e) == ya[tr]) for e in esikler]
    e = esikler[int(np.argmax(acc))]
    res["fiziksel R eşiği (grup)"] = (np.mean((r[te] > e) == ya[te]))
    return res


def deney(X, y, tr, va, te, tohum):
    flat = X[tr].reshape(-1, 3)
    mu, sd = flat.mean(0), flat.std(0)
    Xs = (X - mu) / sd
    m = Tekrarli("gru", 3, 32, cikis=1)
    egit(m, Xs[tr], y[tr][:, None], Xs[va], y[va][:, None],
         epoch=30, seed=tohum)
    p = (tahmin(m, Xs[te])[:, 0] > 0.5).astype(int)
    return np.mean(p == y[te])


satir = []
print("%-24s %8s %8s %8s"
      % ("yöntem", "tohum11", "tohum12", "tohum13"))
sonuclar = {}
for tohum in (11, 12, 13):
    for ad, a in calistir(tohum).items():
        sonuclar.setdefault(ad, []).append(a)
        satir.append((tohum, ad, round(float(a), 4)))
for ad, v in sonuclar.items():
    print("%-24s %8.3f %8.3f %8.3f   ort=%.3f" % (ad, *v, np.mean(v)))
yaz_csv("b68_batarya.csv", ["tohum", "yontem", "test_dogruluk"],
         satir)
