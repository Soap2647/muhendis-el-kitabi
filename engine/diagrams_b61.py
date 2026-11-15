# -*- coding: utf-8 -*-
"""Bolum 61 - Denetimsiz Ogrenme diyagramlari.

Olcum grafikleri engine/veri/b61_*.csv dosyalarini okur (bu dosyalar
b61_01 ... b61_07 deneylerinin ciktisidir). Dendrogram sekli 10 noktalik
sabit tohumlu bir ornekten olusur.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse

from diagrams import ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE, _save

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")
RENK = [EDGE[0], EDGE[1], EDGE[2], EDGE[3], EDGE[4]]


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fl(rows, k):
    return np.array([float(r[k]) for r in rows])


def kmeans_iter(yol):
    iz = oku("b61_kmeans_iz.csv")
    mer = oku("b61_kmeans_merkez.csv")
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
    for ax, t in zip(axes.ravel(), range(4)):
        sat = [r for r in iz if int(r["iter"]) == t]
        x, y = fl(sat, "x"), fl(sat, "y")
        k = np.array([int(r["kume"]) for r in sat])
        for j in range(3):
            m = k == j
            ax.scatter(x[m], y[m], s=26, color=RENK[j], alpha=0.75,
                       edgecolor="none")
        cm = [r for r in mer if int(r["iter"]) == t]
        for r in cm:
            ax.scatter([float(r["cx"])], [float(r["cy"])], marker="X",
                       s=170, color=RENK[int(r["kume"])],
                       edgecolor=INK, linewidth=1.0, zorder=5)
        ax.set_title("Adım %d: atama, sonra merkez güncellemesi" % (t + 1),
                     fontsize=10, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(RULE)
    fig.tight_layout()
    _save(fig, yol)


def kpp_dagilim(yol):
    rows = oku("b61_kmeans_init.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    rast = fl([r for r in rows if r["yontem"] == "rastgele"], "sse")
    kpp = fl([r for r in rows if r["yontem"] == "kmeanspp"], "sse")
    en_iyi = min(rast.min(), kpp.min())
    bins = np.linspace(en_iyi - 1, max(rast.max(), kpp.max()) + 1, 40)
    a1.hist(rast, bins=bins, color=EDGE[3], alpha=0.6,
            label="rastgele başlangıç")
    a1.hist(kpp, bins=bins, color=EDGE[1], alpha=0.6,
            label="k-means++")
    a1.axvline(en_iyi, color=INK, linestyle="--", linewidth=1)
    a1.set_xlabel("son SSE (amaç değeri)", color=INK)
    a1.set_ylabel("tohum sayısı (her yöntem 200)", color=INK)
    a1.legend(frameon=False, fontsize=9)
    a1.set_title("200 tohumda son SSE dağılımı", fontsize=10, color=INK)
    oran_r = 100 * np.mean(rast > en_iyi + 1e-6)
    oran_k = 100 * np.mean(kpp > en_iyi + 1e-6)
    a2.bar(["rastgele", "k-means++"], [oran_r, oran_k],
           color=[EDGE[3], EDGE[1]], width=0.5)
    for i, v in enumerate([oran_r, oran_k]):
        a2.text(i, v + 0.3, "%%%.1f" % v, ha="center", fontsize=10,
                color=INK)
    a2.set_ylabel("en iyi olmayan çalışma (%)", color=INK)
    a2.set_title("Yerel minimuma takılma oranı", fontsize=10, color=INK)
    a2.set_ylim(0, max(oran_r, oran_k) + 3)
    fig.tight_layout()
    _save(fig, yol)


def dirsek_siluet(yol):
    rows = oku("b61_dirsek.csv")
    k = np.array([int(r["k"]) for r in rows])
    ine = fl(rows, "inertia")
    sil_rows = [r for r in rows if r["siluet"] != ""]
    ks = np.array([int(r["k"]) for r in sil_rows])
    sil = fl(sil_rows, "siluet")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    a1.plot(k, ine, marker="o", color=EDGE[0])
    a1.axvline(4, color=ACCENT, linestyle="--", linewidth=1)
    a1.set_xlabel("küme sayısı k", color=INK)
    a1.set_ylabel("inertia (SSE)", color=INK)
    a1.set_title("Dirsek yöntemi", fontsize=10, color=INK)
    a2.plot(ks, sil, marker="o", color=EDGE[1])
    a2.axvline(4, color=ACCENT, linestyle="--", linewidth=1)
    a2.set_xlabel("küme sayısı k", color=INK)
    a2.set_ylabel("ortalama siluet", color=INK)
    a2.set_title("Siluet skoru", fontsize=10, color=INK)
    fig.tight_layout()
    _save(fig, yol)


def halka(yol):
    km = oku("b61_halka.csv")
    db = oku("b61_dbscan_halka.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.9))
    x, y = fl(km, "x"), fl(km, "y")
    e = np.array([int(r["kmeans"]) for r in km])
    for j in range(2):
        m = e == j
        a1.scatter(x[m], y[m], s=10, color=RENK[j], edgecolor="none")
    a1.set_title("k-means (k=2): halkayı ikiye kesiyor", fontsize=10,
                 color=INK)
    x2, y2 = fl(db, "x"), fl(db, "y")
    l2 = np.array([int(r["etiket"]) for r in db])
    gur = l2 == -1
    a2.scatter(x2[gur], y2[gur], s=10, color=MUTED, edgecolor="none",
               label="gürültü")
    for j in np.unique(l2[~gur]):
        m = l2 == j
        a2.scatter(x2[m], y2[m], s=10, color=RENK[int(j)],
                   edgecolor="none")
    a2.set_title("DBSCAN (ε=0,15, minPts=5): iki halka", fontsize=10,
                 color=INK)
    for a in (a1, a2):
        a.set_xticks([])
        a.set_yticks([])
        a.set_aspect("equal")
    fig.tight_layout()
    _save(fig, yol)


def dendrogram(yol):
    from scipy.cluster.hierarchy import dendrogram as dg, linkage
    from sklearn.datasets import make_blobs
    X, _ = make_blobs(n_samples=24, centers=[[0, 0], [5, 0]],
                      cluster_std=0.5, random_state=61)
    rng = np.random.default_rng(61)
    kopru = np.column_stack([np.linspace(1.0, 4.0, 6),
                             rng.normal(0, 0.1, 6)])
    Z = np.vstack([X, kopru])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    for ax, bag, baslik in [(a1, "single", "Tek bağlantı (single)"),
                            (a2, "ward", "Ward bağlantısı")]:
        L = linkage(Z, method=bag)
        dg(L, ax=ax, no_labels=True, color_threshold=0,
           above_threshold_color=ACCENT_L)
        ax.set_title(baslik, fontsize=10, color=INK)
        ax.set_ylabel("birleşme uzaklığı", color=INK)
        ax.set_xticks([])
    fig.tight_layout()
    _save(fig, yol)


def ellips(ax, mu, S, renk):
    vals, vecs = np.linalg.eigh(S)
    yon = vecs[:, 1]
    aci = np.degrees(np.arctan2(yon[1], yon[0]))
    for s in [1, 2]:
        w, h = 2 * s * np.sqrt(vals[1]), 2 * s * np.sqrt(vals[0])
        ax.add_patch(Ellipse(mu, w, h, angle=aci, fill=False,
                             edgecolor=renk, linewidth=1.6 if s == 2 else 0.9,
                             linestyle="-" if s == 2 else "--"))


def gmm_em(yol):
    bil = oku("b61_gmm_bilesen.csv")
    par = oku("b61_gmm_parametre.csv")
    llh = oku("b61_em_llh.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.9))
    x, y = fl(bil, "x"), fl(bil, "y")
    k = np.array([int(r["kume"]) for r in bil])
    for j in range(3):
        m = k == j
        a1.scatter(x[m], y[m], s=10, color=RENK[j], alpha=0.6,
                   edgecolor="none")
    for r in par:
        j = int(r["bilesen"])
        mu = np.array([float(r["mu_x"]), float(r["mu_y"])])
        S = np.array([[float(r["s11"]), float(r["s12"])],
                      [float(r["s12"]), float(r["s22"])]])
        ellips(a1, mu, S, RENK[j])
        a1.scatter([mu[0]], [mu[1]], marker="+", s=80, color=INK)
    a1.set_title("GMM bileşenleri: 1σ kesik, 2σ düz", fontsize=10,
                 color=INK)
    a1.set_xticks([])
    a1.set_yticks([])
    it = fl(llh, "iter")
    v = fl(llh, "llh")
    a2.plot(it, v, marker="o", ms=3, color=EDGE[0])
    a2.set_xlabel("EM iterasyonu", color=INK)
    a2.set_ylabel("log-olabilirlik", color=INK)
    a2.set_title("Log-olabilirlik hiç azalmıyor", fontsize=10, color=INK)
    a2.set_xlim(-1, it.max() + 1)
    fig.tight_layout()
    _save(fig, yol)


def boyut_laneti(yol):
    rows = oku("b61_boyut_laneti.csv")
    d = fl(rows, "d")
    o = fl(rows, "oran")
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    ax.loglog(d, o, marker="o", color=ACCENT)
    ax.set_xlabel("boyut d (log ölçek)", color=INK)
    ax.set_ylabel("(Dmaks − Dmin) / Dmin (log)", color=INK)
    ax.set_title("500 rastgele noktada en uzak ve en yakın uzaklık farkı",
                 fontsize=10, color=INK)
    for dd, oo in zip(d, o):
        if dd in (1, 10, 100, 1000):
            ax.annotate("%.2f" % oo, (dd, oo), textcoords="offset points",
                        xytext=(0, 7), ha="center", fontsize=9, color=INK)
    ax.grid(True, color=RULE, linewidth=0.6)
    fig.tight_layout()
    _save(fig, yol)


def pca_digits(yol):
    var = oku("b61_pca_varyans.csv")
    k = fl(var, "k")
    kum = fl(var, "kumulatif")
    d2 = oku("b61_pca_digits2d.csv")
    x, y = fl(d2, "x"), fl(d2, "y")
    r = np.array([int(v["rakam"]) for v in d2])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    a1.plot(k, kum, color=EDGE[0])
    a1.axhline(0.90, color=MUTED, linestyle="--", linewidth=0.8)
    a1.axhline(0.95, color=MUTED, linestyle=":", linewidth=0.8)
    a1.set_xlabel("bileşen sayısı k", color=INK)
    a1.set_ylabel("kümülatif açıklanan varyans", color=INK)
    a1.set_title("digits: 64 boyuttan k bileşen", fontsize=10, color=INK)
    cm = plt.cm.tab10
    for j in range(10):
        m = r == j
        a2.scatter(x[m], y[m], s=6, color=cm(j), alpha=0.7,
                   edgecolor="none")
    a2.set_title("digits: ilk 2 ana bileşen (64 → 2)", fontsize=10,
                 color=INK)
    a2.set_xticks([])
    a2.set_yticks([])
    fig.tight_layout()
    _save(fig, yol)


def tsne(yol):
    kl = {int(r["perplexity"]): float(r["kl"]) for r in oku("b61_tsne_kl.csv")}
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.4))
    cm = plt.cm.tab10
    for ax, p in zip(axes.ravel()[:3], [5, 30, 50]):
        rows = oku("b61_tsne_digits_p%d.csv" % p)
        x, y = fl(rows, "x"), fl(rows, "y")
        r = np.array([int(v["rakam"]) for v in rows])
        for j in range(10):
            m = r == j
            ax.scatter(x[m], y[m], s=6, color=cm(j), alpha=0.75,
                       edgecolor="none")
        ax.set_title("digits, perplexity=%d (KL=%.3f)" % (p, kl[p]),
                     fontsize=10, color=INK)
    ax = axes.ravel()[3]
    rows = oku("b61_tsne_gurultu_etiket.csv")
    x, y = fl(rows, "x"), fl(rows, "y")
    k = np.array([int(r["kume"]) for r in rows])
    for j in range(8):
        m = k == j
        ax.scatter(x[m], y[m], s=8, color=cm(j), alpha=0.8,
                   edgecolor="none")
    ax.set_title("saf gürültü, k-means k=8: sahte kümeler", fontsize=10,
                 color=INK)
    for a in axes.ravel():
        a.set_xticks([])
        a.set_yticks([])
    fig.tight_layout()
    _save(fig, yol)


def anomali(yol):
    nok = oku("b61_anomali_nokta.csv")
    har = oku("b61_anomali_harita.csv")
    gx = fl(har, "x")
    gy = fl(har, "y")
    m2 = fl(har, "mahal2")
    ifs = fl(har, "if_skor")
    n = int(np.sqrt(len(gx)))
    X = gx.reshape(n, n)
    Y = gy.reshape(n, n)
    x, y = fl(nok, "x"), fl(nok, "y")
    e = np.array([int(v["etiket"]) for v in nok])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    a1.contour(X, Y, np.sqrt(m2).reshape(n, n), levels=[1, 2, 3],
               colors=EDGE[0], linewidths=0.9)
    th = np.linspace(0, 2 * np.pi, 200)
    for rad in [2.0, 3.0]:
        a1.plot(rad * np.cos(th), rad * np.sin(th), linestyle=":",
                color=MUTED, linewidth=1.0)
    a1.scatter(x[e == 0], y[e == 0], s=6, color=MUTED, alpha=0.6,
               edgecolor="none")
    a1.scatter(x[e == 1], y[e == 1], s=14, color=ACCENT, edgecolor="none")
    a1.set_title("Mahalanobis (düz) ve Öklid (kesik) eş-uzaklık",
                 fontsize=9, color=INK)
    a1.set_aspect("equal")
    im = a2.imshow(ifs.reshape(n, n), extent=[-4, 4, -4, 4], origin="lower",
                   cmap="YlOrBr", vmin=0.35, vmax=0.65, aspect="equal")
    a2.scatter(x[e == 0], y[e == 0], s=5, color=INK, alpha=0.45,
               edgecolor="none")
    a2.scatter(x[e == 1], y[e == 1], s=14, color=ACCENT, edgecolor="none")
    a2.set_title("Isolation Forest skoru (sarı-koyu: yüksek = anomali)",
                 fontsize=9, color=INK)
    fig.colorbar(im, ax=a2, fraction=0.046, pad=0.03)
    for a in (a1, a2):
        a.set_xlim(-4, 4)
        a.set_ylim(-4, 4)
        a.set_xticks([])
        a.set_yticks([])
    fig.tight_layout()
    _save(fig, yol)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    kmeans_iter(os.path.join(GORSEL, "b61_kmeans_iter.png"))
    kpp_dagilim(os.path.join(GORSEL, "b61_kpp_dagilim.png"))
    dirsek_siluet(os.path.join(GORSEL, "b61_dirsek_siluet.png"))
    halka(os.path.join(GORSEL, "b61_halka_kmeans_dbscan.png"))
    dendrogram(os.path.join(GORSEL, "b61_dendrogram.png"))
    gmm_em(os.path.join(GORSEL, "b61_gmm_em.png"))
    boyut_laneti(os.path.join(GORSEL, "b61_boyut_laneti.png"))
    pca_digits(os.path.join(GORSEL, "b61_pca_digits.png"))
    tsne(os.path.join(GORSEL, "b61_tsne.png"))
    anomali(os.path.join(GORSEL, "b61_anomali.png"))
    print("tamam")
