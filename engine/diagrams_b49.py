# -*- coding: utf-8 -*-
"""Bolum 49 - Olasilik & Istatistik diyagramlari.

Olcum grafikleri engine/veri/ altindaki CSV dosyalarini okur:
  b49_mlt.csv        Merkezi limit teoremi histogramlari (b49_d_limit)
  b49_mc_pi.csv      Monte Carlo pi hatasi (b49_d_limit)
  b49_mle.csv        Ustel log-olabilirlik egrisi (b49_f_kestirim)
  b49_bootstrap.csv  Bootstrap ortalama dagilimi (b49_g_guven)
  b49_kapsama.csv    Guven araligi kapsama orani (b49_g_guven)
Diger sekiller analitik formuller ve sabit degerlerle cizilir.
"""
import csv
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b49_%s.png" % ad)


def _csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tuval(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    return fig, ax


# --------------------------------------------------------------------------- #
def bayes_agac():
    """Frekans ağacı: 10 000 olay, 200 gerçek tehdit, %95 / %3 alarm."""
    fig, ax = _tuval(9.6, 4.6)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    _box(ax, 5.2, 6.8, 3.6, 0.9, "10 000 olay", FILL[0], EDGE[0],
         fs=11, bold=True)
    _box(ax, 1.2, 4.2, 3.2, 0.9, "Gerçek tehdit: 200", FILL[3], EDGE[3],
         fs=10.5)
    _box(ax, 9.2, 4.2, 3.6, 0.9, "Tehdit değil: 9 800", FILL[1], EDGE[1],
         fs=10.5)
    _arrow(ax, 6.2, 6.8, 2.8, 5.1, col=ACCENT_L)
    _arrow(ax, 7.8, 6.8, 11.0, 5.1, col=ACCENT_L)
    _box(ax, 0.2, 1.4, 2.6, 0.9, "Alarm: 190", FILL[3], EDGE[3], fs=10)
    _box(ax, 3.4, 1.4, 2.6, 0.9, "Alarm yok: 10", FILL[0], EDGE[0], fs=10)
    _box(ax, 7.6, 1.4, 2.6, 0.9, "Alarm: 294", FILL[2], EDGE[2], fs=10)
    _box(ax, 10.8, 1.4, 2.9, 0.9, "Alarm yok: 9 506", FILL[1], EDGE[1],
         fs=10)
    _arrow(ax, 2.2, 4.2, 1.5, 2.3, col=ACCENT_L)
    _arrow(ax, 2.8, 4.2, 4.6, 2.3, col=ACCENT_L)
    _arrow(ax, 10.6, 4.2, 8.9, 2.3, col=ACCENT_L)
    _arrow(ax, 11.2, 4.2, 12.2, 2.3, col=ACCENT_L)
    ax.text(7.0, 0.55,
            "Alarm verildi: 190 + 294 = 484 olay. Bunların 190'ı gerçek.\n"
            "P(tehdit | alarm) = 190 / 484 = 0,39",
            ha="center", va="center", fontsize=10.5, color=INK)
    return _save(fig, _yol("bayes_agac"))


def kesikli_dagilim():
    """Binom, Poisson, geometrik kutle fonksiyonlari (2x2)."""
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 6.2))
    k = np.arange(0, 21)
    binom = stats.binom.pmf(k, 20, 0.05)
    axs[0, 0].bar(k, binom, color=FILL[0], edgecolor=EDGE[0])
    axs[0, 0].set_title("Binom(20; 0,05): paket kaybı", fontsize=10.5)
    k2 = np.arange(0, 13)
    axs[0, 1].bar(k2, stats.poisson.pmf(k2, 3.0), color=FILL[1],
                  edgecolor=EDGE[1])
    axs[0, 1].set_title("Poisson(3): saatte kayıp sayısı", fontsize=10.5)
    k3 = np.arange(1, 31)
    axs[1, 0].bar(k3, stats.geom.pmf(k3, 0.1), color=FILL[2],
                  edgecolor=EDGE[2])
    axs[1, 0].set_title("Geometrik(0,1): ilk başarıya deneme",
                        fontsize=10.5)
    axs[1, 1].bar(k, stats.binom.pmf(k, 20, 0.5), color=FILL[4],
                  edgecolor=EDGE[4])
    axs[1, 1].set_title("Binom(20; 0,5): simetrik örnek", fontsize=10.5)
    for a in axs.flat:
        a.set_ylabel("P(X = k)", fontsize=9)
        a.set_xlabel("k", fontsize=9)
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(labelsize=8.5)
    fig.tight_layout()
    return _save(fig, _yol("kesikli"))


def surekli_dagilim():
    """Üstel ve normal için PDF ve CDF (2x2)."""
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 6.2))
    x = np.linspace(0, 8, 400)
    lam = 0.5
    axs[0, 0].plot(x, lam * np.exp(-lam * x), color=ACCENT, lw=2)
    axs[0, 0].set_title("Üstel(0,5) yoğunluk f(x)", fontsize=10.5)
    axs[0, 1].plot(x, 1 - np.exp(-lam * x), color=ACCENT_L, lw=2)
    axs[0, 1].set_title("Üstel(0,5) birikimli F(x)", fontsize=10.5)
    z = np.linspace(-4, 4, 400)
    axs[1, 0].plot(z, stats.norm.pdf(z), color=ACCENT, lw=2)
    axs[1, 0].set_title("Normal(0,1) yoğunluk f(z)", fontsize=10.5)
    axs[1, 1].plot(z, stats.norm.cdf(z), color=ACCENT_L, lw=2)
    axs[1, 1].set_title("Normal(0,1) birikimli F(z)", fontsize=10.5)
    for a in axs.flat:
        a.grid(alpha=0.25, color=RULE)
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(labelsize=8.5)
    axs[0, 0].text(3.6, 0.36, "f(x) = λ exp(−λx)", fontsize=9,
                   color=INK)
    fig.tight_layout()
    return _save(fig, _yol("surekli"))


def mlt_histogram():
    """Üstel(1) ortalamaları: n arttıkça normale yakınsama (2x2)."""
    veri = _csv("b49_mlt.csv")
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 6.2))
    z = np.linspace(-4, 4, 300)
    for a, n in zip(axs.flat, (1, 2, 5, 30)):
        satir = [r for r in veri if int(r["n"]) == n]
        merk = np.array([float(r["merkez"]) for r in satir])
        yog = np.array([float(r["yogunluk"]) for r in satir])
        a.bar(merk, yog, width=0.2, color=FILL[0], edgecolor=EDGE[0])
        a.plot(z, stats.norm.pdf(z), color=ACCENT, lw=1.8)
        a.set_title("n = %d" % n, fontsize=10.5)
        a.set_xlim(-4, 4)
        a.set_ylim(0, 1.1)
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(labelsize=8.5)
    fig.text(0.5, 0.01, "Standartlaştırılmış ortalama (Üstel(1) örnekleri)"
             " - kırmızı: N(0,1)", ha="center", fontsize=9.5, color=INK)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _save(fig, _yol("mlt"))


def monte_carlo_hata():
    veri = _csv("b49_mc_pi.csv")
    n = np.array([float(r["n"]) for r in veri])
    rms = np.array([float(r["rms_hata"]) for r in veri])
    fig, ax = _tuval(8.6, 4.6)
    ax.loglog(n, rms, "o-", color=ACCENT, lw=1.8, ms=5,
              label="Ölçülen RMS hata")
    ref = rms[0] * (n / n[0]) ** -0.5
    ax.loglog(n, ref, "--", color=MUTED, lw=1.4,
              label="eğim −1/2 referansı")
    ax.set_xlabel("örnek sayısı n", fontsize=10)
    ax.set_ylabel("|π tahmini − π|  (RMS, 20 tekrar)", fontsize=10)
    ax.grid(alpha=0.25, color=RULE, which="both")
    ax.legend(frameon=False, fontsize=9.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("mc_hata"))


def mle_log_olabilirlik():
    veri = _csv("b49_mle.csv")
    lam = np.array([float(r["lambda"]) for r in veri])
    ll = np.array([float(r["log_olabilirlik"]) for r in veri])
    fig, ax = _tuval(8.6, 4.4)
    ax.plot(lam, ll, color=ACCENT, lw=2)
    tepe = float(veri[0]["kapali_mle"])
    ax.axvline(tepe, color=ACCENT_L, ls="--", lw=1.2)
    ax.axvline(0.5, color=MUTED, ls=":", lw=1.2)
    ax.text(tepe + 0.02, ll.min() + 0.15 * (ll.max() - ll.min()),
            "MLE = n / Σx = %.4f" % tepe, fontsize=9.5, color=INK)
    ax.text(0.5 - 0.02, ll.min() + 0.05 * (ll.max() - ll.min()),
            "gerçek 0,5", fontsize=9, color=MUTED, ha="right")
    ax.set_xlabel("λ", fontsize=10)
    ax.set_ylabel("log-olabilirlik ℓ(λ)", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("mle"))


def beta_guncelleme():
    """Beta(2,2) onselinden sonsala: 0 ve 10 gozlem sonrasi."""
    fig, ax = _tuval(9.0, 4.4)
    p = np.linspace(0.001, 0.999, 500)
    cizgiler = [
        (2, 2, "önsel Beta(2,2)", MUTED, ":"),
        (3, 2, "1 başarı sonrası Beta(3,2)", EDGE[0], "-"),
        (5, 9, "3 başarı, 10 denemeden sonra Beta(5,9)", ACCENT, "-"),
    ]
    for a, b, et, renk, stil in cizgiler:
        ax.plot(p, stats.beta.pdf(p, a, b), color=renk, lw=2, ls=stil,
                label=et)
    ax.set_xlabel("p (başarı olasılığı)", fontsize=10)
    ax.set_ylabel("yoğunluk", fontsize=10)
    ax.legend(frameon=False, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("beta"))


def bootstrap_dagilim():
    veri = _csv("b49_bootstrap.csv")
    dag = np.array([float(r["ortalama"]) for r in veri])
    lo, hi = np.percentile(dag, [2.5, 97.5])
    fig, ax = _tuval(9.0, 4.4)
    ax.hist(dag, bins=60, color=FILL[0], edgecolor=EDGE[0])
    ax.axvline(lo, color=ACCENT, lw=1.6, ls="--")
    ax.axvline(hi, color=ACCENT, lw=1.6, ls="--")
    ax.text(lo - 0.2, ax.get_ylim()[1] * 0.92,
            "%.2f" % lo, ha="right", fontsize=9.5, color=ACCENT)
    ax.text(hi + 0.2, ax.get_ylim()[1] * 0.92,
            "%.2f" % hi, ha="left", fontsize=9.5, color=ACCENT)
    ax.set_xlabel("bootstrap ortalaması (çevrim)", fontsize=10)
    ax.set_ylabel("yeniden örnek sayısı", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("bootstrap"))


def kapsama_grafik():
    veri = _csv("b49_kapsama.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2), sharey=True)
    for a, dag, ad in zip(axs, ("normal", "ustel"),
                          ("Normal anakitle", "Üstel anakitle (çarpık)")):
        satir = [r for r in veri if r["dagilim"] == dag]
        ns = [str(int(r["n"])) for r in satir]
        z = [float(r["z_kapsama"]) for r in satir]
        t = [float(r["t_kapsama"]) for r in satir]
        x = np.arange(len(ns))
        a.bar(x - 0.2, z, 0.38, color=FILL[0], edgecolor=EDGE[0],
              label="z-GA (1,96)")
        a.bar(x + 0.2, t, 0.38, color=FILL[3], edgecolor=EDGE[3],
              label="t-GA")
        a.axhline(0.95, color=INK, ls="--", lw=1.1)
        a.set_xticks(x)
        a.set_xticklabels(["n=" + s for s in ns])
        a.set_title(ad, fontsize=10.5)
        a.set_ylim(0.75, 1.07)
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(labelsize=8.5)
    axs[0].set_ylabel("gerçek değeri içeren GA oranı", fontsize=9.5)
    axs[0].legend(frameon=False, fontsize=8.5, ncol=2, loc="upper center",
                  bbox_to_anchor=(1.0, 1.02))
    fig.tight_layout()
    return _save(fig, _yol("kapsama"))


def p_degeri_hata():
    """H0: Z ~ N(0,1); H1: Z ~ N(delta,1). alfa, beta ve p-degeri."""
    fig, ax = _tuval(9.6, 4.6)
    z = np.linspace(-4, 6, 500)
    delta = 2.8
    ax.plot(z, stats.norm.pdf(z), color=EDGE[0], lw=2,
            label="H0 doğru (sıfır hipotezi)")
    ax.plot(z, stats.norm.pdf(z, delta, 1), color=EDGE[3], lw=2,
            label="H1 doğru (gerçek etki)")
    kr = 1.96
    ax.fill_between(z, 0, stats.norm.pdf(z), where=z >= kr,
                    color=FILL[3], alpha=0.9)
    ax.fill_between(z, 0, stats.norm.pdf(z, delta, 1), where=z < kr,
                    color=FILL[2], alpha=0.9)
    gozlem = 2.3
    ax.axvline(gozlem, color=INK, ls=":", lw=1.2)
    ax.text(gozlem + 0.1, 0.44, "gözlenen z = 2,3", fontsize=9.5,
            color=INK)
    ax.text(3.2, 0.12, "α = 0,05\n(I. tip hata)", fontsize=9.5,
            color=ACCENT, ha="center")
    ax.text(0.2, 0.06, "β\n(II. tip hata)", fontsize=9.5,
            color=INK, ha="center")
    ax.text(-3.9, 0.30, "H0 altında p-değeri:\nP(|Z| ≥ 2,3)",
            fontsize=9.0, color=MUTED, ha="left")
    ax.set_xlabel("test istatistiği z", fontsize=10)
    ax.set_yticks([])
    ax.set_ylim(0, 0.5)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("p_hata"))


def main():
    yollar = [bayes_agac(), kesikli_dagilim(), surekli_dagilim(),
              mlt_histogram(), monte_carlo_hata(), mle_log_olabilirlik(),
              beta_guncelleme(), bootstrap_dagilim(), kapsama_grafik(),
              p_degeri_hata()]
    for p in yollar:
        print(os.path.normpath(p))


if __name__ == "__main__":
    main()
