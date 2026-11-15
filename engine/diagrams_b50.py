# -*- coding: utf-8 -*-
"""Bolum 50 - Optimizasyon diyagramlari.

Olcum grafikleri engine/veri/b50_*.csv dosyalarini okur:
  b50_sonlu_fark.csv, b50_ogrenme_orani.csv, b50_zikzak.csv,
  b50_optimizer_yorunge.csv, b50_kayip_adim.csv, b50_tavlama.csv,
  b50_newton_iz.csv
Kontur ve geometri sekilleri analitik formuldan cizilir.
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

RENK = {"GD": ACCENT, "Momentum": ACCENT_L, "Nesterov": EDGE[1],
        "AdaGrad": EDGE[2], "RMSProp": EDGE[4], "Adam": "#222222"}


def _yol(ad):
    return os.path.join(OUT, "b50_%s.png" % ad)


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ax_stil(ax, baslik):
    ax.set_title(baslik, fontsize=11, color=INK, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8, colors=MUTED)


def konveks_yuzey():
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 7.2))
    x = np.linspace(-2.2, 2.2, 400)
    # (a) konveks: kiris egrinin ustunde kalir
    ax = axs[0, 0]
    ax.plot(x, x ** 2, color=INK, lw=1.6)
    a, b, lam = -1.6, 1.4, 0.4
    xm = lam * a + (1 - lam) * b
    ym = lam * a * a + (1 - lam) * b * b
    ax.plot([a, b], [a * a, b * b], color=ACCENT, lw=1.3)
    ax.scatter([xm], [xm * xm], color=EDGE[1], zorder=3)
    ax.scatter([xm], [ym], color=ACCENT, zorder=3)
    ax.annotate("kiriş ≥ eğri", (xm, ym), xytext=(0.2, 3.6),
                fontsize=9, color=ACCENT,
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8))
    ax.set_ylim(-0.3, 4.2)
    _ax_stil(ax, "(a) Konveks: f(x) = x²")
    # (b) konveks degil: iki yerel minimum
    ax = axs[0, 1]
    g = x ** 4 - 3 * x ** 2 + x
    ax.plot(x, g, color=INK, lw=1.6)
    for xv, et in ((-1.30, "yerel"), (1.13, "küresel")):
        yv = xv ** 4 - 3 * xv ** 2 + xv
        ax.scatter([xv], [yv], color=ACCENT, zorder=3)
        ax.annotate(et, (xv, yv), xytext=(xv - 0.25, yv + 1.7),
                    fontsize=9, color=ACCENT)
    ax.set_ylim(-4.2, 6.5)
    _ax_stil(ax, "(b) Konveks değil: iki yerel minimum")
    # (c) 2B konveks kase
    ax = axs[1, 0]
    X, Y = np.meshgrid(np.linspace(-2, 2, 300), np.linspace(-2, 2, 300))
    ax.contour(X, Y, X ** 2 + 3 * Y ** 2, levels=12, colors=ACCENT_L,
               linewidths=0.7)
    ax.scatter([0], [0], color=ACCENT, zorder=3)
    ax.set_aspect("equal")
    _ax_stil(ax, "(c) Konveks kase: tek minimum, yerel = küresel")
    # (d) konveks olmayan yuzey: Rastrigin 2B
    ax = axs[1, 1]
    X2, Y2 = np.meshgrid(np.linspace(-2.5, 2.5, 300),
                         np.linspace(-2.5, 2.5, 300))
    R = (20 + X2 ** 2 + Y2 ** 2 - 10 * np.cos(2 * np.pi * X2)
         - 10 * np.cos(2 * np.pi * Y2))
    ax.contour(X2, Y2, R, levels=18, colors=EDGE[3], linewidths=0.6)
    ax.scatter([0], [0], color=ACCENT, zorder=3)
    ax.set_aspect("equal")
    _ax_stil(ax, "(d) Konveks değil: çok sayıda yerel minimum")
    fig.tight_layout()
    return _save(fig, _yol("konveks_yuzey"))


def ogrenme_orani():
    rows = _oku("b50_ogrenme_orani.csv")
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    X, Y = np.meshgrid(np.linspace(-1.2, 1.2, 300),
                       np.linspace(-1.2, 1.2, 300))
    ax.contour(X, Y, X ** 2 + 10 * Y ** 2, levels=[0.1, 0.5, 1, 2, 4, 8],
               colors=RULE, linewidths=1.0)
    stil = (("0.005", EDGE[0], "η = 0.005: çok küçük, yavaş"),
            ("0.080", EDGE[1], "η = 0.080: uygun, hızlı"),
            ("0.110", ACCENT, "η = 0.110: 2/λmax = 0.1 aşıldı, ıraksıyor"))
    for eta, renk, et in stil:
        pts = [(float(r["x"]), float(r["y"])) for r in rows
               if r["eta"] == eta]
        if eta == "0.110":
            pts = pts[:12]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o",
                color=renk, ms=3, lw=1.2, label=et)
    ax.text(-1.15, -0.45, "η = 0.110 yörüngesi ilk 12 adım;\n"
            "çerçevenin dışına çıkar", fontsize=8, color=ACCENT)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_xlabel("x", color=MUTED)
    ax.set_ylabel("y", color=MUTED)
    ax.set_aspect("equal")
    ax.legend(fontsize=9, frameon=True, framealpha=1.0, facecolor="white", edgecolor=RULE, loc="upper left")
    _ax_stil(ax, "Üç öğrenme oranı, f = x² + 10y² (başlangıç (1, 1))")
    fig.tight_layout()
    return _save(fig, _yol("ogrenme_orani"))


def zikzak():
    rows = _oku("b50_zikzak.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.6), sharey=True)
    X, Y = np.meshgrid(np.linspace(-1.1, 1.1, 300),
                       np.linspace(-1.1, 1.1, 300))
    Z = X ** 2 + 100 * Y ** 2
    for ax, ad, baslik in ((axs[0], "GD", "(a) Düz gradyan inişi"),
                           (axs[1], "Momentum",
                            "(b) Momentum (β = 0.67)")):
        ax.contour(X, Y, Z, levels=[0.01, 0.05, 0.2, 0.6, 1.5],
                   colors=RULE, linewidths=1.0)
        pts = [(float(r["x"]), float(r["y"])) for r in rows
               if r["yontem"] == ad]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-",
                color=RENK[ad], lw=1.1)
        ax.scatter([pts[0][0]], [pts[0][1]], color=INK, zorder=3, s=14)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect("equal")
        _ax_stil(ax, baslik)
    axs[0].set_ylabel("y", color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("zikzak"))


def optimizer_yorunge():
    rows = _oku("b50_optimizer_yorunge.csv")
    fig, axs = plt.subplots(2, 3, figsize=(9.6, 6.6), sharex=True,
                            sharey=True)
    X, Y = np.meshgrid(np.linspace(-1.5, 1.5, 400),
                       np.linspace(-0.6, 1.6, 400))
    Z = (1 - X) ** 2 + 100 * (Y - X ** 2) ** 2
    yontemler = ["GD", "Momentum", "Nesterov", "AdaGrad", "RMSProp",
                 "Adam"]
    for ax, ad in zip(axs.ravel(), yontemler):
        ax.contour(X, Y, Z, levels=np.logspace(-1, 3.2, 12), colors=RULE,
                   linewidths=0.7)
        pts = [(float(r["x"]), float(r["y"])) for r in rows
               if r["problem"] == "Rosenbrock" and r["yontem"] == ad]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-",
                color=RENK[ad], lw=0.9)
        ax.scatter([1], [1], color=INK, marker="*", s=50, zorder=4)
        ax.scatter([-1.2], [1.0], color=INK, s=12, zorder=4)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-0.6, 1.6)
        ax.set_aspect("equal")
        _ax_stil(ax, ad)
    fig.suptitle("Rosenbrock üzerinde yörüngeler (her biri ilk 3000 adım)",
                 fontsize=11, color=INK, x=0.02, ha="left")
    fig.tight_layout()
    return _save(fig, _yol("optimizer_yorunge"))


def kayip_adim():
    rows = _oku("b50_kayip_adim.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.4))
    for ax, pad, baslik in ((axs[0], "Rosenbrock", "(a) Rosenbrock"),
                            (axs[1], "kot",
                             "(b) κ = 100, ikinci dereceden")):
        for ad in ["GD", "Momentum", "Nesterov", "AdaGrad", "RMSProp",
                   "Adam"]:
            pts = [(int(r["adim"]), float(r["f"])) for r in rows
                   if r["problem"] == pad and r["yontem"] == ad]
            ax.semilogy([p[0] for p in pts],
                        [max(p[1], 1e-16) for p in pts],
                        color=RENK[ad], lw=1.1, label=ad)
        ax.set_xlabel("adım", color=MUTED)
        ax.axhline(1e-6, color=MUTED, lw=0.6, ls="--")
        _ax_stil(ax, baslik)
    axs[0].set_ylabel("f(x_k)", color=MUTED)
    axs[0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    return _save(fig, _yol("kayip_adim"))


def sonlu_fark():
    rows = _oku("b50_sonlu_fark.csv")
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    for tip, renk, ls in (("float64", ACCENT, "-"),
                          ("float32", ACCENT_L, "--")):
        sec = [r for r in rows if r["tip"] == tip]
        h = np.array([float(r["h"]) for r in sec])
        ei = np.array([float(r["hata_ileri"]) for r in sec])
        em = np.array([float(r["hata_merkezi"]) for r in sec])
        ax.loglog(h, ei, ls, color=renk, marker="o", ms=3, lw=1.1,
                  label="ileri fark, " + tip)
        ax.loglog(h, em, ls, color=renk, marker="s", ms=3, lw=1.1,
                  alpha=0.55, label="merkezi fark, " + tip)
    hh = np.logspace(-8, -1, 50)
    ax.loglog(hh, 665 * hh, ":", color=MUTED, lw=1.0,
              label="kesme (h/2)·f_xx ≈ 665h")
    ax.set_xlabel("h (adım boyu)", color=MUTED)
    ax.set_ylabel("maks. |sayısal − analitik|", color=MUTED)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    _ax_stil(ax, "Rosenbrock gradyanında sonlu fark hatası")
    fig.tight_layout()
    return _save(fig, _yol("sonlu_fark"))


def lagrange():
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    X, Y = np.meshgrid(np.linspace(0.5, 9.5, 300),
                       np.linspace(0.5, 9.5, 300))
    ax.contour(X, Y, X * Y, levels=[9, 16, 21, 24, 25], colors=EDGE[0],
               linewidths=0.9)
    t = np.linspace(0.5, 9.5, 100)
    ax.plot(t, 10 - t, color=ACCENT, lw=1.6)
    ax.scatter([5], [5], color=INK, zorder=4)
    ax.annotate("(5, 5): teğetlik noktası\n∇f = λ∇g, λ = 2.5",
                (5, 5), xytext=(6.4, 7.8), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
    ax.annotate("", xy=(6.4, 6.4), xytext=(5, 5),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT_L, lw=1.4))
    ax.annotate("", xy=(5.1, 6.5), xytext=(4.3, 5.7),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4))
    ax.text(6.6, 6.0, "∇f = (y, x)", color=ACCENT_L, fontsize=9)
    ax.text(1.1, 2.4, "∇g = (2, 2)\n(sınıra dik)", color=ACCENT,
            fontsize=9)
    ax.text(7.2, 1.4, "2x + 2y = 20", color=ACCENT, fontsize=9)
    ax.set_xlim(0.5, 9.5)
    ax.set_ylim(0.5, 9.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x (kenar)", color=MUTED)
    ax.set_ylabel("y (kenar)", color=MUTED)
    _ax_stil(ax, "Sabit çevrede en büyük alan: teğetlik")
    fig.tight_layout()
    return _save(fig, _yol("lagrange"))


def lp_bolge():
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    kose = np.array([[0, 0], [4, 0], [3, 1], [0, 2]], float)
    ax.add_patch(plt.Polygon(kose, closed=True, facecolor=FILL[1],
                             edgecolor=EDGE[1], lw=1.4))
    xs = np.linspace(0, 5, 100)
    ax.plot(xs, 4 - xs, color=ACCENT_L, lw=1.0)
    ax.plot(xs, (6 - xs) / 3, color=ACCENT_L, lw=1.0)
    xl = np.linspace(0, 5, 50)
    for z, ls in ((4, ":"), (11, "--"), (12, "-")):
        ax.plot(xl, (z - 3 * xl) / 2, ls, color=ACCENT, lw=1.0)
    ax.text(4.3, 3.2, "x + y = 4", color=ACCENT_L, fontsize=9)
    ax.text(3.0, 1.9, "x + 3y = 6", color=ACCENT_L, fontsize=9)
    ax.plot([], [], "-", color=ACCENT, label="3x + 2y = 12 (en iyi)")
    ax.plot([], [], "--", color=ACCENT, label="3x + 2y = 11")
    ax.plot([], [], ":", color=ACCENT, label="3x + 2y = 4")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    for x0, y0 in kose:
        ax.scatter([x0], [y0], color=INK, zorder=4, s=18)
    ax.text(0.12, -0.35, "(0, 0)", fontsize=8, color=INK)
    ax.text(4.12, -0.35, "(4, 0)", fontsize=8, color=INK)
    ax.text(3.12, 1.1, "(3, 1)", fontsize=8, color=INK)
    ax.text(0.12, 2.1, "(0, 2)", fontsize=8, color=INK)
    ax.scatter([4], [0], color=ACCENT, s=60, zorder=5)
    ax.set_xlim(-0.4, 5.2)
    ax.set_ylim(-0.6, 4.6)
    ax.set_aspect("equal")
    ax.set_xlabel("x", color=MUTED)
    ax.set_ylabel("y", color=MUTED)
    _ax_stil(ax, "Uygun bölge çokyüzlüsü ve köşe çözüm")
    fig.tight_layout()
    return _save(fig, _yol("lp_bolge"))


def tavlama():
    rows = _oku("b50_tavlama.csv")
    k = np.array([float(r["adim"]) for r in rows])
    T = np.array([float(r["T"]) for r in rows])
    c = np.array([float(r["maliyet"]) for r in rows])
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    axs[0].semilogy(k, T, color=ACCENT_L, lw=1.2)
    axs[0].set_ylabel("sıcaklık T", color=MUTED)
    _ax_stil(axs[0], "(a) Soğutma takvimi")
    axs[1].plot(k, c, color=ACCENT, lw=0.9)
    axs[1].set_ylabel("tur maliyeti", color=MUTED)
    _ax_stil(axs[1], "(b) Maliyet: yüksek T'de gürültülü")
    for ax in axs:
        ax.set_xlabel("iterasyon", color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("tavlama"))


def newton_karesel():
    rows = _oku("b50_newton_iz.csv")
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for yontem, renk, et in (("newton", ACCENT, "Newton"),
                             ("gd", ACCENT_L, "Gradyan inişi, η = 0.1")):
        sec = [r for r in rows if r["yontem"] == yontem]
        k = [int(r["adim"]) for r in sec]
        e = [max(float(r["hata"]), 1e-17) for r in sec]
        ax.semilogy(k, e, "-o" if yontem == "newton" else "-", ms=4,
                    color=renk, lw=1.2, label=et)
    ax.set_xlabel("iterasyon", color=MUTED)
    ax.set_ylabel("|x_k − √2|", color=MUTED)
    ax.set_xlim(0, 30)
    ax.set_ylim(1e-17, 1)
    ax.legend(fontsize=9, frameon=False)
    _ax_stil(ax, "F(x) = x³/3 − 2x: Newton karesel, GD doğrusal")
    fig.tight_layout()
    return _save(fig, _yol("newton_karesel"))


if __name__ == "__main__":
    for fn in (konveks_yuzey, ogrenme_orani, zikzak, optimizer_yorunge,
               kayip_adim, sonlu_fark, lagrange, lp_bolge, tavlama,
               newton_karesel):
        print(fn())
