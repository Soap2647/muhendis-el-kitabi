# -*- coding: utf-8 -*-
"""Bolum 19 - 'Divide & Conquer' diyagramlari.

Olcum grafigi (karatsuba_olcum) engine/veri altindaki karatsuba.py ciktisini
okur; diger sekiller bolumdeki ornek degerlerden cizilir.
"""
import csv
import os
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "gorseller")
OLCUM_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "veri", "b19_karatsuba_olcum.csv")


def _yol(ad):
    return os.path.join(OUT, "b19_%s.png" % ad)


def _cell(ax, x, y, w, h, metin, fill="white", edge=RULE, fs=10,
          bold=False, tcol=INK):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                           lw=1.0, zorder=2))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=fs, color=tcol, zorder=3,
            weight="bold" if bold else "normal")


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. Bol-coz-birlestir sablonu ---------------------------------------- #
def dc_sablon():
    fig, ax = _tuval(9.6, 4.4)
    _box(ax, 5.0, 4.9, 4.0, 0.8, "Problem: n eleman", FILL[0], EDGE[0],
         fs=11, bold=True)
    _box(ax, 1.6, 2.7, 3.6, 0.8, "Sol alt problem: n/2", FILL[1],
         EDGE[1], fs=10.5)
    _box(ax, 8.8, 2.7, 3.6, 0.8, "Sağ alt problem: n/2", FILL[1],
         EDGE[1], fs=10.5)
    _box(ax, 1.6, 0.6, 3.6, 0.8, "Temel durum",
         FILL[2], EDGE[2], fs=10)
    _box(ax, 8.8, 0.6, 3.6, 0.8, "Temel durum",
         FILL[2], EDGE[2], fs=10)
    _arrow(ax, 6.4, 4.9, 3.4, 3.5, col=ACCENT_L, rad=0.12)
    _arrow(ax, 7.6, 4.9, 10.6, 3.5, col=ACCENT_L, rad=-0.12)
    _arrow(ax, 3.4, 2.7, 3.4, 1.4, col=MUTED)
    _arrow(ax, 10.6, 2.7, 10.6, 1.4, col=MUTED)
    _arrow(ax, 3.2, 1.4, 3.2, 2.7, col=ACCENT, rad=0.0)
    _arrow(ax, 10.8, 1.4, 10.8, 2.7, col=ACCENT, rad=0.0)
    _arrow(ax, 3.6, 3.5, 6.2, 4.9, col=ACCENT, rad=-0.12)
    _arrow(ax, 10.4, 3.5, 7.8, 4.9, col=ACCENT, rad=0.12)
    ax.text(6.4, 3.25, "birlestir (maliyet burada)", ha="center",
            bbox=dict(fc="white", ec="none", pad=1),
            fontsize=9.5, color=ACCENT, style="italic")
    ax.text(0.15, 3.1, "böl ve\nözyinele", ha="left", fontsize=8.6,
            color=MUTED, va="center")
    return _save(fig, _yol("dc_sablon"))


# 2. Ozyineleme agaci: T(n) = 2T(n/2) + n log n, n = 16 -------------- #
def ozyineleme_agaci():
    import math
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.2)
    n = 16
    satirlar = []
    toplam = 0
    for i in range(0, 4):
        dugum = 2 ** i
        boy = n // dugum
        maliyet = dugum * boy * int(math.log2(boy))
        toplam += maliyet
        satirlar.append((i, dugum, boy, maliyet))
    y0 = 5.6
    for i, dugum, boy, maliyet in satirlar:
        y = y0 - i * 1.35
        ax.text(0.2, y + 0.3, "seviye %d" % i, fontsize=9.5,
                color=INK, va="center", weight="bold")
        w = min(2.2, 8.0 / dugum)
        gap = 0.25
        total = dugum * w + (dugum - 1) * gap
        x0 = 2.4 + (8.0 - total) / 2
        for k in range(dugum):
            x = x0 + k * (w + gap)
            _box(ax, x, y, w, 0.6, "n=%d" % boy, FILL[i % 4],
                 EDGE[i % 4], fs=9)
        ax.text(12.9, y + 0.3, "= %d" % maliyet, fontsize=10,
                color=ACCENT, va="center", weight="bold")
    ax.text(2.6, 0.3, "Her seviyenin toplam maliyeti n(log n - i):"
            " 64, 48, 32, 16", fontsize=9, color=MUTED, va="center")
    ax.text(6.6, 0.85, "T(16) = 64 + 48 + 32 + 16 = %d" % toplam,
            fontsize=9, color=INK, va="center", ha="center")
    return _save(fig, _yol("ozyineleme_agaci"))


# 3. Hizli us: x^13 -> x^6 -> x^3 -> x^1 -> x^0 ----------------------- #
def hizli_us():
    fig, ax = _tuval(9.6, 3.4, xl=14, yl=5)
    ustler = [13, 6, 3, 1, 0]
    xs = [0.4, 3.0, 5.6, 8.2, 10.8]
    notlar = ["tek: kare ve x ile çarp", "çift: sadece kare",
              "tek: kare ve x ile çarp", "tek: kare ve x ile çarp",
              "temel: 1"]
    for i, (u, x) in enumerate(zip(ustler, xs)):
        _box(ax, x, 2.9, 1.9, 0.9, "x^%d" % u, FILL[i % 4],
             EDGE[i % 4], fs=11, bold=True)
        if i < len(ustler) - 1:
            _arrow(ax, x + 1.9, 3.35, xs[i + 1], 3.35, col=ACCENT)
            ax.text(x + 2.2, 3.7, "n//2", fontsize=9, color=ACCENT,
                    ha="center")
        ax.text(x + 0.95, 2.45, notlar[i], fontsize=7.6, color=MUTED,
                ha="center", va="top")
    ax.text(7.0, 1.2, "13 = 1101 (ikili). Her adımda bir bit okunur; "
            "çağrı sayısı ~log2(n)", fontsize=9, color=INK,
            ha="center")
    return _save(fig, _yol("hizli_us"))


# 4. Karatsuba: 4 carpim -> 3 carpim ---------------------------------- #
def karatsuba():
    fig, ax = _tuval(9.6, 4.2, xl=14, yl=6.5)
    ax.text(7.0, 6.1, "a = a1*B + a0,   b = b1*B + b0   (B = 10^m)",
            ha="center", fontsize=10.5, color=INK, weight="bold")
    ax.text(0.2, 4.3, "Okul yöntemi\n4 çarpım", fontsize=10,
            color=ACCENT, va="center", weight="bold")
    urunler = ["a1*b1", "a1*b0", "a0*b1", "a0*b0"]
    for i, u in enumerate(urunler):
        _box(ax, 3.2 + i * 2.6, 4.0, 2.2, 0.7, u, FILL[3], EDGE[3],
             fs=10.5)
    ax.text(0.2, 1.7, "Karatsuba\n3 çarpım", fontsize=10,
            color=EDGE[0], va="center", weight="bold")
    _box(ax, 3.2, 1.4, 2.8, 0.8, "z2 = a1*b1", FILL[0], EDGE[0], fs=10.5)
    _box(ax, 6.4, 1.4, 2.8, 0.8, "z0 = a0*b0", FILL[0], EDGE[0], fs=10.5)
    _box(ax, 9.6, 1.4, 3.9, 0.8, "z1 = (a0+a1)(b0+b1)-z0-z2",
         FILL[0], EDGE[0], fs=9.2)
    ax.text(7.0, 0.7, "a0*b1 + a1*b0 = z1 (tek çarpım, çıkarmalar "
            "ucuz)", ha="center", fontsize=9.2, color=MUTED)
    return _save(fig, _yol("karatsuba"))


# 5. Olcum grafigi: okul, Karatsuba, yerlesik -------------------------- #
def karatsuba_olcum():
    import numpy as np
    satirlar = []
    with open(OLCUM_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            satirlar.append((int(r["limb"]), float(r["okul"]),
                             float(r["karatsuba"]),
                             float(r["yerlesik"])))
    x = np.array([s[0] for s in satirlar])
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.loglog(x, [s[1] for s in satirlar], "o-", color=ACCENT,
              label="okul yöntemi (bizim, Python)")
    ax.loglog(x, [s[2] for s in satirlar], "s-", color=EDGE[0],
              label="Karatsuba (bizim, Python)")
    ax.loglog(x, [s[3] for s in satirlar], "^-", color=EDGE[1],
              label="yerleşik int çarpımı (CPython C)")
    ax.set_xlabel("sayı uzunluğu (limb, 10^4 tabanlı)")
    ax.set_ylabel("süre (saniye)")
    ax.grid(True, which="both", color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=8.8)
    fig.tight_layout()
    fig.savefig(_yol("karatsuba_olcum"), dpi=200, facecolor="white")
    plt.close(fig)
    return _yol("karatsuba_olcum")


# 6. Strassen: 2x2 blok bolme ve 7 carpim ----------------------------- #
def strassen():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=7.4)
    ceyrekler = [["A11", "A12"], ["A21", "A22"]]
    for k, (ad, x0) in enumerate([("A", 0.4), ("B", 4.6), ("C", 8.8)]):
        ax.text(x0 + 1.0, 6.9, ad, fontsize=11, weight="bold",
                ha="center", color=INK)
        for i in range(2):
            for j in range(2):
                etk = "%s%d%d" % (ad, i + 1, j + 1)
                _cell(ax, x0 + j * 1.2, 5.0 - i * 1.2, 1.2, 1.2, etk,
                      fill=FILL[k], edge=EDGE[k], fs=10)
    ax.text(7.0, 3.2, "Strassen: 8 çarpım yerine 7 çarpım (n/2 boyutlu)",
            ha="center", fontsize=10, color=ACCENT, weight="bold")
    lines = [
        "M1 = (A11+A22)(B11+B22)     C11 = M1+M4-M5+M7",
        "M2 = (A21+A22) B11          C12 = M3+M5",
        "M3 = A11 (B12-B22)          C21 = M2+M4",
        "M4 = A22 (B21-B11)          C22 = M1-M2+M3+M6",
        "M5 = (A11+A12) B22",
        "M6 = (A21-A11)(B11+B12)",
        "M7 = (A12-A22)(B21+B22)",
    ]
    for i, t in enumerate(lines):
        ax.text(0.5, 2.6 - i * 0.36, t, fontsize=9.1, family="monospace",
                color=INK, va="center")
    return _save(fig, _yol("strassen"))


# 7. En yakin nokta: serit ve 8 kare ---------------------------------- #
def closest_serit():
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    d = 2.0                               # delta
    xm = 0.0
    ax.add_patch(Rectangle((xm - d, 0), 2 * d, d, facecolor="#F7F7F4",
                           edgecolor=ACCENT, lw=1.4, zorder=1))
    for i in range(4):
        for j in range(2):
            ax.add_patch(Rectangle((xm - d + i * d / 2, j * d / 2),
                                   d / 2, d / 2, facecolor="none",
                                   edgecolor=RULE, lw=0.9, zorder=2))
    ax.plot([xm, xm], [-0.3, d + 0.3], ls="--", color=MUTED, lw=1.0)
    ax.text(xm + 0.08, d + 0.25, "bölme çizgisi", fontsize=8.5,
            color=MUTED)
    p = (-0.25, 0.25)
    ax.plot(*p, "o", color=ACCENT, ms=7, zorder=5)
    ax.text(p[0] - 0.1, p[1] - 0.28, "p", fontsize=10, color=ACCENT,
            weight="bold", ha="right")
    qs = [(-1.6, 0.85), (-0.9, 1.6), (0.6, 0.3), (1.4, 1.1),
          (0.85, 1.75), (-1.2, 1.9), (1.7, 0.2)]
    for q in qs:
        ax.plot(*q, "o", color=EDGE[0], ms=6, zorder=5)
    ax.annotate("", xy=(-d, d * 1.02), xytext=(-d, -0.05),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.9))
    ax.text(-d - 0.12, d * 1.06, "2*delta", fontsize=9, color=MUTED,
            ha="right")
    ax.annotate("", xy=(d, -0.25), xytext=(-d, -0.25),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.9))
    ax.text(0, -0.5, "genişlik 2*delta; her kare delta/2 x delta/2",
            fontsize=8.6, color=MUTED, ha="center")
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-0.9, 2.7)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(2.55, 2.55, "8 kare, her birinde en fazla 1 nokta\n"
            "=> p'nin karşısında en fazla 7 aday",
            fontsize=8.8, color=INK, ha="right", va="top")
    fig.tight_layout()
    fig.savefig(_yol("closest_serit"), dpi=200, facecolor="white")
    plt.close(fig)
    return _yol("closest_serit")


# 8. Siluet birlestirme ------------------------------------------------ #
def skyline_birlestir():
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.3), sharey=True)
    A = [(1, 11), (5, 0)]
    B = [(2, 6), (7, 0)]
    S = [(1, 11), (5, 6), (7, 0)]
    for ax, veri, ad, col in ((axs[0], A, "A: bina 1", EDGE[0]),
                              (axs[1], B, "B: bina 2", EDGE[1]),
                              (axs[2], S, "birlesik siluet", ACCENT)):
        xs = [v[0] for v in veri]
        hs = [v[1] for v in veri]
        ax.step(xs, hs, where="post", color=col, lw=2.0)
        ax.fill_between(xs + [xs[-1]], hs + [0], step="post",
                        color=col, alpha=0.12)
        ax.set_title(ad, fontsize=10)
        ax.set_xlim(0, 9)
        ax.set_ylim(0, 13)
        ax.set_xlabel("x", fontsize=9)
        ax.grid(True, color=RULE, lw=0.5)
    axs[0].set_ylabel("yükseklik", fontsize=9)
    fig.tight_layout()
    fig.savefig(_yol("skyline_birlestir"), dpi=200, facecolor="white")
    plt.close(fig)
    return _yol("skyline_birlestir")


# 9. FFT kelebek diyagrami (n = 8) ------------------------------------ #
def fft_kelebek():
    import cmath
    n = 8
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=9.6)
    sira = [0, 4, 2, 6, 1, 5, 3, 7]        # bit-ters sira
    ys = [8.2 - i * 1.0 for i in range(n)]
    for i, k in enumerate(sira):
        ax.text(0.7, ys[i], "x%d" % k, fontsize=9.5, ha="right",
                va="center", color=INK)
    kolon = [1.3, 4.5, 7.7, 10.9]
    for s in range(1, 4):
        half = 2 ** (s - 1)
        for b in range(0, n, 2 * half):
            for k in range(half):
                i, j = b + k, b + k + half
                tw = cmath.exp(-2j * cmath.pi * k / (2 * half))
                ax.plot([kolon[s - 1], kolon[s]], [ys[i], ys[i]],
                        color=MUTED, lw=0.9)
                ax.plot([kolon[s - 1], kolon[s]], [ys[j], ys[i]],
                        color=ACCENT_L, lw=0.9)
                ax.plot([kolon[s - 1], kolon[s]], [ys[i], ys[j]],
                        color=ACCENT_L, lw=0.9)
                ax.plot([kolon[s - 1], kolon[s]], [ys[j], ys[j]],
                        color=MUTED, lw=0.9)
    for i in range(n):
        for c in kolon:
            ax.plot(c, ys[i], "o", ms=3.5, color=INK)
    for s in range(1, 3):
        ax.text(kolon[s], -0.45, "aşama %d" % s, ha="center", fontsize=9,
                color=INK)
    ax.text(kolon[0], -0.45, "giriş", ha="center", fontsize=9, color=INK)
    ax.text(kolon[3], -0.45, "aşama 3 / çıkış", ha="center", fontsize=9,
            color=INK)
    ax.text(7.0, 8.9, "n = 8: 3 aşama, her aşamada 4 kelebek (n/2)",
            ha="center", fontsize=10, color=INK, weight="bold")
    ax.text(7.0, -1.1, "Kelebek: alt kanat = X - w*Y, üst kanat = X + w*Y,"
            " w = e^(-2*pi*i*k/(2*half))", ha="center", fontsize=8.8,
            color=MUTED)
    return _save(fig, _yol("fft_kelebek"))


if __name__ == "__main__":
    for f in (dc_sablon, ozyineleme_agaci, hizli_us, karatsuba,
              karatsuba_olcum, strassen, closest_serit,
              skyline_birlestir, fft_kelebek):
        print(f())
