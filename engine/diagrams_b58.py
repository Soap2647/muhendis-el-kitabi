# -*- coding: utf-8 -*-
"""Bolum 58 - Dogrusal modeller diyagramlari.

Olcum grafikleri engine/veri/b58_*.csv dosyalarini okur (bu CSV'ler
b58_*.py deneylerinin ciktisidir). Geometri ve sigmoid sekilleri analitik
formuldan cizilir.
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

RENK_SINIF = [EDGE[0], EDGE[1], EDGE[2]]


def _yol(ad):
    return os.path.join(OUT, "b58_%s.png" % ad)


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ax_stil(ax, baslik):
    ax.set_title(baslik, fontsize=11, color=INK, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8, colors=MUTED)


def olcekleme():
    rows = _oku("b58_olcekleme.csv")
    adim = np.array([float(r["adim"]) for r in rows])
    ham = np.array([float(r["ham_kayip_farki"]) for r in rows])
    std = np.array([float(r["std_kayip_farki"]) for r in rows])
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.semilogy(adim, ham, color=ACCENT, lw=1.8,
                label="ham öznitelikler (koşul sayısı ~230)")
    ax.semilogy(adim, std, color=EDGE[0], lw=1.8,
                label="standartlaştırılmış (koşul sayısı ~22)")
    ax.axhline(1e-2, color=MUTED, lw=0.8, ls="--")
    ax.text(18000, 1.3e-2, "fark = 10⁻²", fontsize=8, color=MUTED,
            ha="right")
    ax.set_xlabel("gradyan inişi adımı", color=MUTED)
    ax.set_ylabel("kayıp farkı (kayıp − optimum)", color=MUTED)
    ax.legend(fontsize=9, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper right")
    _ax_stil(ax, "Ölçeklemenin gradyan inişine etkisi (diyabet verisi)")
    fig.tight_layout()
    return _save(fig, _yol("olcekleme"))


def artik():
    rows = _oku("b58_artik.csv")
    t1 = [float(r["tahmin"]) for r in rows if r["tahmin"]]
    a1 = [float(r["artik"]) for r in rows if r["artik"]]
    t2 = [float(r["sentetik_tahmin"]) for r in rows if r["sentetik_tahmin"]]
    a2 = [float(r["sentetik_artik"]) for r in rows if r["sentetik_artik"]]
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    axs[0].scatter(t1, a1, s=10, color=EDGE[0], alpha=0.7)
    axs[1].scatter(t2, a2, s=10, color=ACCENT, alpha=0.7)
    for ax in axs:
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xlabel("tahmin", color=MUTED)
        ax.set_ylabel("artık (gerçek − tahmin)", color=MUTED)
    _ax_stil(axs[0], "Diyabet verisi: yayılım sabit")
    _ax_stil(axs[1], "Sentetik: varyans tahminle büyüyor")
    fig.tight_layout()
    return _save(fig, _yol("artik"))


def l1_l2_kisit():
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.6))
    w_star = np.array([1.5, 0.2])                # kısıtsız optimum
    th = np.linspace(0, 2 * np.pi, 400)
    for ax, ad in ((axs[0], "L2: çember ‖w‖₂ ≤ 1"),
                   (axs[1], "L1: elmas ‖w‖₁ ≤ 1")):
        for r in (0.4, 0.8, 1.2, 1.6):      # kayip eslik egrileri
            ax.plot(w_star[0] + r * np.cos(th), w_star[1] + r * np.sin(th),
                    color=RULE, lw=1.0)
        if "L2" in ad:
            ax.fill(np.cos(th), np.sin(th), color=FILL[1], alpha=0.8)
            ax.plot(np.cos(th), np.sin(th), color=EDGE[1], lw=1.8)
            # Kisit cemberinde w* 'a en yakin nokta
            p = w_star / np.linalg.norm(w_star)
            nokta = "çözüm (%.2f, %.2f)\nseyrek değil" % (p[0], p[1])
        else:
            kose = np.array([[1, 0], [0, 1], [-1, 0], [0, -1], [1, 0]])
            ax.fill(kose[:, 0], kose[:, 1], color=FILL[2], alpha=0.8)
            ax.plot(kose[:, 0], kose[:, 1], color=EDGE[2], lw=1.8)
            p = np.array([1.0, 0.0])
            nokta = "köşe (1, 0):\nw₂ tam sıfır"
        ax.plot(*w_star, "o", color=INK, ms=4)
        ax.text(w_star[0] + 0.05, w_star[1] + 0.12, "w* (kısıtsız)",
                fontsize=8, color=INK)
        ax.plot(*p, "o", color=ACCENT, ms=6)
        ax.annotate(nokta, p, xytext=(p[0] - 0.9, p[1] - 0.95),
                    fontsize=8, color=ACCENT,
                    arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8))
        ax.set_xlim(-1.4, 2.2)
        ax.set_ylim(-1.3, 1.5)
        ax.set_aspect("equal")
        ax.axhline(0, color=MUTED, lw=0.5)
        ax.axvline(0, color=MUTED, lw=0.5)
        ax.set_xlabel("w₁", color=MUTED)
        ax.set_ylabel("w₂", color=MUTED)
        _ax_stil(ax, ad)
    fig.tight_layout()
    return _save(fig, _yol("l1_l2_kisit"))


def duzenlilestirme_yolu():
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for ax, dosya, xl, ad, sutun in (
            (axs[0], "b58_ridge_yol.csv", "log₁₀ α (Ridge)",
             "Ridge: katsayılar α ile küçülür", "alpha"),
            (axs[1], "b58_lasso_yol.csv", "log₁₀ λ (Lasso)",
             "Lasso: bazı katsayılar tam sıfıra iner", "lambda")):
        rows = _oku(dosya)
        x = np.log10([float(r[sutun]) for r in rows])
        for j in range(10):
            y = [float(r["w%d" % j]) for r in rows]
            ax.plot(x, y, lw=1.2, color=plt.cm.tab10(j))
        ax.axhline(0, color=MUTED, lw=0.6)
        ax.set_xlabel(xl, color=MUTED)
        ax.set_ylabel("standart katsayı", color=MUTED)
        _ax_stil(ax, ad)
    fig.tight_layout()
    return _save(fig, _yol("duzenlilestirme_yolu"))


def coklu_dogrusallik():
    rows = _oku("b58_coklu.csv")
    a = np.array([[float(r[k]) for k in ("ols_b1", "ols_b2")] for r in rows])
    b = np.array([[float(r[k]) for k in ("ridge_b1", "ridge_b2")]
                  for r in rows])
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    axs[0].scatter(a[:, 0], a[:, 1], s=8, color=ACCENT, alpha=0.6)
    axs[0].set_xlim(-20, 22)
    axs[0].set_ylim(-20, 22)
    axs[1].scatter(b[:, 0], b[:, 1], s=8, color=EDGE[0], alpha=0.6)
    axs[1].set_xlim(0.85, 1.15)
    axs[1].set_ylim(0.85, 1.15)
    for ax in axs:
        ax.axhline(1, color=MUTED, lw=0.5, ls="--")
        ax.axvline(1, color=MUTED, lw=0.5, ls="--")
        ax.set_xlabel("β₁", color=MUTED)
        ax.set_ylabel("β₂", color=MUTED)
        ax.set_aspect("equal")
    _ax_stil(axs[0], "OLS: 300 veri kümesi, dağılım çok geniş")
    _ax_stil(axs[1], "Ridge (α = 1): aynı veriler, dar küme")
    fig.tight_layout()
    return _save(fig, _yol("coklu_dogrusallik"))


def sigmoid_logodds():
    z = np.linspace(-6, 6, 400)
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    axs[0].plot(z, 1 / (1 + np.exp(-z)), color=ACCENT, lw=2)
    axs[0].axhline(0.5, color=MUTED, lw=0.6, ls="--")
    axs[0].axvline(0, color=MUTED, lw=0.6, ls="--")
    axs[0].set_xlabel("z = wᵀx + b", color=MUTED)
    axs[0].set_ylabel("p = σ(z)", color=MUTED)
    _ax_stil(axs[0], "Sigmoid: doğrusal skoru olasılığa çevirir")
    xs = np.linspace(-2, 4, 100)
    b0, w1 = -1.2, 0.8                      # Ornek 58.3: z = -1.2 + 0.8x
    axs[1].plot(xs, b0 + w1 * xs, color=EDGE[0], lw=2)
    for xv in (0, 1, 2):
        zv = b0 + w1 * xv
        pv = 1 / (1 + np.exp(-zv))
        axs[1].plot(xv, zv, "o", color=ACCENT, ms=5)
        axs[1].annotate("p = %.3f" % pv, (xv, zv), xytext=(xv + 0.15, zv - 0.35),
                        fontsize=8, color=INK)
    axs[1].axhline(0, color=MUTED, lw=0.6, ls="--")
    axs[1].set_xlabel("özniteliğin değeri x", color=MUTED)
    axs[1].set_ylabel("log-odds = w x + b", color=MUTED)
    axs[1].text(-1.9, 1.6, "eğim w = 0,8: x 1 artınca "
                "log-odds 0,8 artar;\nodds 2,23 katına çıkar",
                fontsize=8, color=INK)
    _ax_stil(axs[1], "Log-odds doğrusaldır: eğim = katsayı")
    fig.tight_layout()
    return _save(fig, _yol("sigmoid_logodds"))


def lojistik_karar():
    rows = _oku("b58_lojistik2d.csv")
    x = np.array([[float(r["x1"]), float(r["x2"])] for r in rows])
    y = np.array([int(r["y"]) for r in rows])
    wr = _oku("b58_lojistik2d_w.csv")[0]
    b, w1, w2 = float(wr["b"]), float(wr["w1"]), float(wr["w2"])
    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    gx, gy = np.meshgrid(np.linspace(-4, 4, 300), np.linspace(-4, 4, 300))
    olasilik = 1 / (1 + np.exp(-(b + w1 * gx + w2 * gy)))
    ax.contourf(gx, gy, olasilik, levels=[0, 0.5, 1],
                colors=[FILL[0], FILL[2]], alpha=0.9)
    ax.contour(gx, gy, olasilik, levels=[0.25, 0.5, 0.75],
               colors=[MUTED, ACCENT, MUTED], linewidths=[0.7, 1.6, 0.7],
               linestyles=["--", "-", "--"])
    ax.scatter(x[y == 0, 0], x[y == 0, 1], s=14, color=EDGE[0],
               label="sınıf 0")
    ax.scatter(x[y == 1, 0], x[y == 1, 1], s=14, color=EDGE[2],
               marker="^", label="sınıf 1")
    ax.set_xlabel("x₁", color=MUTED)
    ax.set_ylabel("x₂", color=MUTED)
    ax.legend(fontsize=9, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper left")
    _ax_stil(ax, "Lojistik karar sınırı (kırmızı: p = 0,5; kesikli: 0,25/0,75)")
    fig.tight_layout()
    return _save(fig, _yol("lojistik_karar"))


def ayrilabilir_patlama():
    rows = _oku("b58_ayrilabilir.csv")
    k = np.array([float(r["adim"]) for r in rows])
    n0 = np.array([float(r["norm_lambda0"]) for r in rows])
    n1 = np.array([float(r["norm_lambda001"]) for r in rows])
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.semilogx(k, n0, color=ACCENT, lw=1.8, label="ceza yok (λ = 0)")
    ax.semilogx(k, n1, color=EDGE[0], lw=1.8, label="L2 ceza (λ = 0,01)")
    ax.set_xlabel("gradyan inişi adımı (log ölçek)", color=MUTED)
    ax.set_ylabel("‖w‖ (sapma hariç)", color=MUTED)
    ax.legend(fontsize=9, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper left")
    _ax_stil(ax, "Ayrılabilir veride ‖w‖: cezasız büyür, L2 sınırlar")
    fig.tight_layout()
    return _save(fig, _yol("ayrilabilir_patlama"))


def softmax_bolge():
    rows = _oku("b58_softmax2d.csv")
    x = np.array([[float(r["x1"]), float(r["x2"])] for r in rows])
    y = np.array([int(r["y"]) for r in rows])
    wr = _oku("b58_softmax2d_w.csv")
    W = np.array([[float(r["w1"]), float(r["w2"])] for r in wr]).T
    b = np.array([float(r["b"]) for r in wr])
    gx, gy = np.meshgrid(np.linspace(-6, 6, 400), np.linspace(-4, 7, 400))
    G = np.stack([gx.ravel(), gy.ravel()], axis=1)
    tahmin = np.argmax(G @ W + b, axis=1).reshape(gx.shape)
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    ax.contourf(gx, gy, tahmin, levels=[-0.5, 0.5, 1.5, 2.5],
                colors=[FILL[0], FILL[1], FILL[2]], alpha=0.95)
    for k in range(3):
        ax.scatter(x[y == k, 0], x[y == k, 1], s=14, color=RENK_SINIF[k],
                   label="sınıf %d" % k)
    ax.set_xlabel("x₁", color=MUTED)
    ax.set_ylabel("x₂", color=MUTED)
    ax.legend(fontsize=9, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper left")
    _ax_stil(ax, "Softmax karar bölgeleri: üç sınıf, doğrusal sınırlar")
    fig.tight_layout()
    return _save(fig, _yol("softmax_bolge"))


def huber_aykiri():
    veri = _oku("b58_huber_veri.csv")
    x = np.array([float(r["x"]) for r in veri])
    y = np.array([float(r["y"]) for r in veri])
    cizgi = _oku("b58_huber_cizgi.csv")
    xx = np.linspace(0, 10, 50)
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.scatter(x, y, s=12, color=MUTED, alpha=0.7, label="veri (5% aykırı)")
    stil = {"MSE": (ACCENT, "-"), "LAD": (EDGE[2], "--"),
            "Huber": (EDGE[1], "-"), "Gercek": (INK, ":")}
    etiket = {"MSE": "MSE (OLS)", "LAD": "LAD (MAE)", "Huber": "Huber",
              "Gercek": "gerçek doğru"}
    for r in cizgi:
        renk, ls = stil[r["ad"]]
        ax.plot(xx, float(r["kesim"]) + float(r["egim"]) * xx,
                color=renk, ls=ls, lw=1.8, label=etiket[r["ad"]])
    ax.set_xlim(0, 10)
    ax.set_ylim(-2, 30)
    ax.set_xlabel("x", color=MUTED)
    ax.set_ylabel("y", color=MUTED)
    ax.legend(fontsize=9, frameon=True, framealpha=1.0, facecolor="white",
              edgecolor=RULE, loc="upper left")
    _ax_stil(ax, "Aykırı değerler: MSE sapar, Huber ve LAD dayanır")
    fig.tight_layout()
    return _save(fig, _yol("huber_aykiri"))


if __name__ == "__main__":
    for fn in (olcekleme, artik, l1_l2_kisit, duzenlilestirme_yolu,
               coklu_dogrusallik, sigmoid_logodds, lojistik_karar,
               ayrilabilir_patlama, softmax_bolge, huber_aykiri):
        print(fn())
