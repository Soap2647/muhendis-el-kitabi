# -*- coding: utf-8 -*-
"""Bolum 60 - SVM ve cekirdek yontemleri diyagramlari.

Olcum grafikleri engine/veri/b60_*.csv dosyalarini okur (bu CSV'ler
kitap deneyinin ciktisidir). Geometri ve kayip sekilleri analitik
formullerden cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_save, ACCENT, ACCENT_L, INK, MUTED, RULE, FILL,
                      EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")

POZ = EDGE[0]      # arduvaz: pozitif sinif
NEG = ACCENT       # bordo: negatif sinif


def _yol(ad):
    return os.path.join(OUT, "b60_%s.png" % ad)


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _stil(ax, baslik=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8, colors=MUTED)
    if baslik:
        ax.set_title(baslik, fontsize=10, color=INK, loc="left")


def _cizgi(ax, w1, w2, b, c, **kw):
    """w1 x + w2 y + b = c dogrusunu cizer (x araligi icin ax.get_xlim)."""
    x0, x1 = ax.get_xlim()
    xs = np.array([x0, x1])
    if abs(w2) < 1e-12:
        ax.axvline(-(b - c) / w1, **kw)
        return
    ys = (c - b - w1 * xs) / w2
    ax.plot(xs, ys, **kw)


def ayirici_genis_marj():
    """Sekil 60.1: birden cok ayirici, yalnizca biri en genis marjli."""
    A, B = (2.0, 1.0), (2.0, 3.0)
    C, D = (0.0, 1.0), (-1.0, 0.0)
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.set_xlim(-2.0, 4.6)
    ax.set_ylim(-1.2, 3.8)
    for x0, ad, ha in [(0.5, "c = 0,5: marj 1,0", "right"),
                       (1.5, "c = 1,5: marj 1,0", "left")]:
        ax.axvline(x0, color=MUTED, lw=1.1, ls=":")
        ax.text(x0 + (-0.04 if ha == "right" else 0.04), 3.62, ad,
                fontsize=7.8, color=MUTED, ha=ha, va="center")
    ax.axvspan(0.0, 2.0, color=FILL[2], alpha=0.8, zorder=0)
    ax.axvline(1.0, color=ACCENT, lw=2.0)
    ax.annotate("en geniş: c = 1, marj 2,0\n(w = (1, 0), b = −1)",
                xy=(1.0, 0.2), xytext=(2.6, -0.6), fontsize=8.5,
                color=ACCENT, va="center",
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.9))
    for p in [A, B]:
        ax.scatter(*p, s=80, color=POZ, zorder=3)
    for p in [C, D]:
        ax.scatter(*p, s=80, color=NEG, marker="s", zorder=3)
    ax.annotate("A", A, xytext=(8, 4), textcoords="offset points", fontsize=9)
    ax.annotate("B", B, xytext=(8, 4), textcoords="offset points", fontsize=9)
    ax.annotate("C", C, xytext=(-14, 6), textcoords="offset points", fontsize=9)
    ax.annotate("D", D, xytext=(-14, 6), textcoords="offset points", fontsize=9)
    ax.text(-1.9, 3.5, "● pozitif (+1)   ■ negatif (−1)", fontsize=8.5,
            color=INK)
    ax.set_xlabel("x₁", color=MUTED)
    ax.set_ylabel("x₂", color=MUTED)
    _stil(ax, "Birçok doğru ayırıyor; yalnızca biri en geniş marjlı")
    fig.tight_layout()
    return _save(fig, _yol("en_genis_marj"))


def marj_destek():
    """Sekil 60.2: destek vektorleri, marj bandi ve f = +-1 cizgileri."""
    rows = _oku("b60_marj_veri.csv")
    h = _oku("b60_marj_hat.csv")[0]
    w1, w2, b = float(h["w1"]), float(h["w2"]), float(h["b"])
    marj = float(h["marj"])
    X = np.array([[float(r["x1"]), float(r["x2"])] for r in rows])
    y = np.array([int(r["y"]) for r in rows])
    sv = np.array([int(r["sv"]) for r in rows]).astype(bool)
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.set_xlim(X[:, 0].min() - 0.8, X[:, 0].max() + 0.8)
    ax.set_ylim(X[:, 1].min() - 0.8, X[:, 1].max() + 0.8)
    _cizgi(ax, w1, w2, b, 0.0, color=INK, lw=1.6)
    _cizgi(ax, w1, w2, b, 1.0, color=ACCENT, lw=1.0, ls="--")
    _cizgi(ax, w1, w2, b, -1.0, color=ACCENT, lw=1.0, ls="--")
    ax.scatter(X[y > 0, 0], X[y > 0, 1], s=46, color=POZ, zorder=3)
    ax.scatter(X[y < 0, 0], X[y < 0, 1], s=46, color=NEG, marker="s", zorder=3)
    ax.scatter(X[sv, 0], X[sv, 1], s=190, facecolors="none", edgecolors=INK,
               linewidths=1.4, zorder=4)
    ax.text(0.02, 0.97,
            "karar sınırı: f = 0\nmarj çizgileri: f = ±1\n"
            "marj = 2/‖w‖ = %.2f\ndaire: destek vektörü (%d adet)"
            % (marj, sv.sum()),
            transform=ax.transAxes, va="top", fontsize=8.5, color=INK)
    ax.set_xlabel("x₁", color=MUTED)
    ax.set_ylabel("x₂", color=MUTED)
    _stil(ax, "Marj bandı ve destek vektörleri (sert marj, C = 1000)")
    fig.tight_layout()
    return _save(fig, _yol("marj_destek"))


def c_etkisi():
    """Sekil 60.3: C'nin marj ve hata dengesi (4 panel, ayni veri)."""
    veri = _oku("b60_c_veri.csv")
    hat = {float(r["C"]): r for r in _oku("b60_c_hat.csv")}
    X = np.array([[float(r["x1"]), float(r["x2"])] for r in veri])
    y = np.array([int(r["y"]) for r in veri])
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 7.2))
    for ax, Cv in zip(axs.ravel(), [0.01, 0.1, 1.0, 100.0]):
        r = hat[Cv]
        w1, w2, b = float(r["w1"]), float(r["w2"]), float(r["b"])
        ax.set_xlim(X[:, 0].min() - 0.5, X[:, 0].max() + 0.5)
        ax.set_ylim(X[:, 1].min() - 0.5, X[:, 1].max() + 0.5)
        _cizgi(ax, w1, w2, b, 0.0, color=INK, lw=1.5)
        _cizgi(ax, w1, w2, b, 1.0, color=ACCENT, lw=0.9, ls="--")
        _cizgi(ax, w1, w2, b, -1.0, color=ACCENT, lw=0.9, ls="--")
        ax.scatter(X[y > 0, 0], X[y > 0, 1], s=16, color=POZ)
        ax.scatter(X[y < 0, 0], X[y < 0, 1], s=16, color=NEG, marker="s")
        marj = 2 / np.hypot(w1, w2)
        ax.text(0.03, 0.04, "C = %g, marj = %.2f" % (Cv, marj),
                transform=ax.transAxes, fontsize=8.5, color=INK)
        _stil(ax)
    fig.suptitle("C'nin etkisi: küçük C geniş marj, büyük C dar marj",
                 fontsize=10.5, color=INK, x=0.02, ha="left")
    fig.tight_layout()
    return _save(fig, _yol("c_etkisi"))


def kayip_karsilastirma():
    """Sekil 60.4: 0-1, mentese, lojistik ve kare kayip (z = y f(x))."""
    z = np.linspace(-2.0, 2.5, 500)
    zero_one = (z < 0).astype(float)
    hinge = np.maximum(0.0, 1.0 - z)
    logistic = np.log(1.0 + np.exp(-z))
    kare = (1.0 - z) ** 2
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.step(z, zero_one, where="mid", color=MUTED, lw=1.8,
            label="0-1 kaybı (türevi yok)")
    ax.plot(z, hinge, color=ACCENT, lw=2.0, label="menteşe (SVM)")
    ax.plot(z, logistic, color=POZ, lw=2.0, label="lojistik (Bölüm 58)")
    ax.plot(z, kare, color=EDGE[1], lw=1.6, ls="--", label="kare (regresyon)")
    ax.axvline(1.0, color=RULE, lw=1.0)
    ax.text(1.04, 1.5, "z = 1: marj sınırı", fontsize=8, color=MUTED)
    ax.set_xlim(-2.0, 2.5)
    ax.set_ylim(-0.1, 4.0)
    ax.set_xlabel("z = y·f(x)  (doğru tahmin için z > 0)", color=MUTED)
    ax.set_ylabel("kayıp", color=MUTED)
    ax.legend(fontsize=8.5, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper right")
    _stil(ax, "Sınıflandırma kayıpları: menteşe, 0-1'in dışbükey üst sınırı")
    fig.tight_layout()
    return _save(fig, _yol("kayip_karsilastirma"))


def daire_esleme():
    """Sekil 60.5: daire verisi, 2B ve (x1, x2, x1^2 + x2^2) uzayinda."""
    rows = _oku("b60_daire.csv")
    x1 = np.array([float(r["x1"]) for r in rows])
    x2 = np.array([float(r["x2"]) for r in rows])
    z = np.array([float(r["z"]) for r in rows])
    y = np.array([int(r["y"]) for r in rows])
    fig = plt.figure(figsize=(9.6, 4.4))
    ax = fig.add_subplot(1, 2, 1)
    ax.scatter(x1[y > 0], x2[y > 0], s=14, color=POZ)
    ax.scatter(x1[y < 0], x2[y < 0], s=14, color=NEG, marker="s")
    ax.set_aspect("equal")
    ax.set_title("(a) 2B: doğru ayıramaz", fontsize=10, color=INK, loc="left")
    ax.set_xlabel("x₁", color=MUTED)
    ax.set_ylabel("x₂", color=MUTED)
    _stil(ax)
    ax3 = fig.add_subplot(1, 2, 2, projection="3d")
    ax3.scatter(x1[y > 0], x2[y > 0], z[y > 0], s=10, color=POZ)
    ax3.scatter(x1[y < 0], x2[y < 0], z[y < 0], s=10, color=NEG, marker="s")
    gx, gy = np.meshgrid(np.linspace(-1.3, 1.3, 2), np.linspace(-1.3, 1.3, 2))
    ax3.plot_surface(gx, gy, np.full_like(gx, 0.4), alpha=0.25, color=ACCENT_L)
    ax3.set_title("(b) (x₁, x₂, z): düzlem ayırır", fontsize=10, color=INK,
                  loc="left")
    ax3.set_xlabel("x₁", fontsize=8)
    ax3.set_ylabel("x₂", fontsize=8)
    ax3.set_zlabel("z = x₁²+x₂²", fontsize=8)
    ax3.tick_params(labelsize=7)
    fig.tight_layout()
    return _save(fig, _yol("daire_esleme"))


def rbf_izgara():
    """Sekil 60.6: RBF gamma x C izgarasi; karar sinirlari ve test skoru."""
    izg = _oku("b60_rbf_izgara.csv")
    skor = {(float(r["gamma"]), float(r["C"])): r for r in _oku("b60_rbf_skor.csv")}
    nokta = _oku("b60_moons.csv")
    px = np.array([float(r["x1"]) for r in nokta])
    py = np.array([float(r["x2"]) for r in nokta])
    py_y = np.array([int(r["y"]) for r in nokta])
    gx = np.linspace(-2.0, 3.0, 40)
    gy = np.linspace(-1.5, 2.0, 40)
    fig, axs = plt.subplots(3, 3, figsize=(9.6, 9.0))
    for k, (g, Cv) in enumerate([(g, Cv) for g in [0.1, 1.0, 10.0]
                                 for Cv in [0.1, 1.0, 100.0]]):
        ax = axs.ravel()[k]
        rs = [r for r in izg if float(r["gamma"]) == g and float(r["C"]) == Cv]
        F = np.array([float(r["f"]) for r in rs]).reshape(40, 40)
        ax.contourf(gx, gy, F, levels=[-50, 0, 50], colors=[FILL[3], FILL[0]],
                    alpha=0.9)
        ax.contour(gx, gy, F, levels=[0.0], colors=[INK], linewidths=1.0)
        ax.scatter(px[py_y > 0], py[py_y > 0], s=6, color=POZ)
        ax.scatter(px[py_y < 0], py[py_y < 0], s=6, color=NEG, marker="s")
        s = skor[(g, Cv)]
        ax.set_title("γ=%g, C=%g\ntest %.3f, SV %s" % (
            g, Cv, float(s["test_ort"]), s["sv"]), fontsize=8, color=INK,
            loc="left")
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(RULE)
    fig.suptitle("RBF SVM: γ (satır) ve C (sütun) etkisi, ay veri seti",
                 fontsize=10.5, color=INK, x=0.02, ha="left")
    fig.tight_layout()
    return _save(fig, _yol("rbf_izgara"))


def mercer_ozdeger():
    """Sekil 60.7: gecerli (RBF) ve gecersiz (-(x-z)^2) cekirdek Gram ozdegerleri."""
    rows = _oku("b60_mercer.csv")
    sira = np.array([int(r["sira"]) for r in rows])
    rbf = np.array([float(r["rbf"]) for r in rows])
    bad = np.array([float(r["gecersiz"]) for r in rows])
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    w = 0.38
    ax.bar(sira - w / 2, rbf, width=w, color=POZ, label="RBF (γ=1): geçerli")
    ax.bar(sira + w / 2, bad, width=w, color=NEG,
           label="−(x−z)²: geçersiz")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel("özdeğer sırası", color=MUTED)
    ax.set_ylabel("özdeğer", color=MUTED)
    ax.set_xticks(sira)
    ax.legend(fontsize=8.5, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper right")
    ax.text(3.3, -20.5, "negatif özdeğer: Mercer\nkoşulu sağlanmıyor",
            fontsize=8, color=NEG)
    _stil(ax, "Gram matrisi özdeğerleri (5 nokta: 0, 1, 2, 3, 4)")
    fig.tight_layout()
    return _save(fig, _yol("mercer_ozdeger"))


def olcek_sure():
    """Sekil 60.8: egitim suresi ile n (log-log), n^2 referans egimi."""
    rows = _oku("b60_olcek_sure.csv")
    n = np.array([float(r["n"]) for r in rows])
    t = np.array([float(r["sure_s"]) for r in rows])
    egim = np.polyfit(np.log(n), np.log(t), 1)[0]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.loglog(n, t, "o", color=ACCENT, ms=6, label="ölçüm (medyan)")
    xs = np.array([n.min(), n.max()])
    ax.loglog(xs, t[0] * (xs / n[0]) ** egim, color=ACCENT_L, lw=1.4,
              label="en küçük kareler eğimi = %.2f" % egim)
    ax.loglog(xs, t[0] * (xs / n[0]) ** 2, color=MUTED, lw=1.0, ls="--",
              label="referans: n²")
    ax.set_xlabel("örnek sayısı n (log)", color=MUTED)
    ax.set_ylabel("eğitim süresi (s, log)", color=MUTED)
    ax.legend(fontsize=8.5, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper left")
    _stil(ax, "RBF SVM eğitim süresi: n arttıkça yaklaşık n²")
    fig.tight_layout()
    return _save(fig, _yol("olcek_sure"))


def rff_hata():
    """Sekil 60.9: RFF yaklasim hatasi D'ye gore (log-log)."""
    rows = _oku("b60_rff.csv")
    D = np.array([float(r["D"]) for r in rows])
    b1 = np.array([float(r["bizim_ort"]) for r in rows])
    b1s = np.array([float(r["bizim_sd"]) for r in rows])
    b2 = np.array([float(r["sklearn_ort"]) for r in rows])
    b2s = np.array([float(r["sklearn_sd"]) for r in rows])
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.errorbar(D, b1, yerr=b1s, fmt="o-", color=ACCENT, ms=5, lw=1.4,
                capsize=3, label="kendi RFF (NumPy)")
    ax.errorbar(D, b2, yerr=b2s, fmt="s--", color=POZ, ms=4, lw=1.0,
                capsize=3, label="sklearn RBFSampler")
    xs = np.array([D.min(), D.max()])
    c = b1[D == 100][0] * np.sqrt(100)
    ax.loglog(xs, c / np.sqrt(xs), color=MUTED, lw=1.0, ls=":",
              label="referans: 1/√D")
    ax.set_xlabel("öznitelik sayısı D (log)", color=MUTED)
    ax.set_ylabel("en büyük çekirdek hatası (log)", color=MUTED)
    ax.legend(fontsize=8.5, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper right")
    _stil(ax, "Rastgele Fourier özniteliklerinde yaklaşım hatası (5 tohum)")
    fig.tight_layout()
    return _save(fig, _yol("rff_hata"))


def olcekleme_etki():
    """Sekil 60.10: olcekleme oncesi/sonrasi test dogrulugu (eslestirilmis tohumlar)."""
    rows = _oku("b60_olcekleme.csv")
    ham = np.array([float(r["olceksiz"]) for r in rows])
    olc = np.array([float(r["olcekli"]) for r in rows])
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    for a, b in zip(ham, olc):
        ax.plot([0, 1], [a, b], color=RULE, lw=1.0, zorder=1)
    ax.scatter(np.zeros_like(ham), ham, s=34, color=NEG, zorder=3,
               label="ölçeklenmemiş")
    ax.scatter(np.ones_like(olc), olc, s=34, color=POZ, marker="s", zorder=3,
               label="StandardScaler (yalnız eğitimden)")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ölçeklenmemiş", "ölçekli"], color=MUTED)
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylabel("test doğruluğu", color=MUTED)
    ax.legend(fontsize=8.5, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="lower right")
    _stil(ax, "RBF SVM: ölçeklemenin etkisi (meme kanseri, 10 tohum)")
    fig.tight_layout()
    return _save(fig, _yol("olcekleme_etki"))


if __name__ == "__main__":
    for f in [ayirici_genis_marj, marj_destek, c_etkisi, kayip_karsilastirma,
              daire_esleme, rbf_izgara, mercer_ozdeger, olcek_sure,
              rff_hata, olcekleme_etki]:
        print(f())
