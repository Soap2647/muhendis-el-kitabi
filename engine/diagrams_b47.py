# -*- coding: utf-8 -*-
"""Bolum 47 - Ayrik Matematik diyagramlari.

Seri verisi: engine/veri/b47_derangement.csv (n, D_n, oran, 1/e).
Diger sekiller kavramsal semalar ve sayim sonuclaridir; sayilar
kod icinde yeniden hesaplanir.
"""
import csv
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b47_%s.png" % ad)


def _tuval(w, h, xl=10, yl=10):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def kapi_devre():
    fig, ax = _tuval(9.6, 4.6, 14, 7)
    ax.text(0.3, 6.6, "De Morgan: ¬(a ∧ b) = ¬a ∨ ¬b",
            fontsize=11, color=INK, weight="bold")
    # Sol devre: a, b -> VE -> DEĞİL
    _box(ax, 0.5, 3.6, 1.2, 0.8, "a", FILL[0], EDGE[0])
    _box(ax, 0.5, 1.6, 1.2, 0.8, "b", FILL[0], EDGE[0])
    _box(ax, 3.0, 2.5, 1.6, 1.4, "VE", FILL[1], EDGE[1], bold=True)
    _box(ax, 5.6, 2.8, 1.6, 0.9, "DEĞİL", FILL[3], EDGE[3], bold=True)
    _arrow(ax, 1.7, 4.0, 3.0, 3.4, col=EDGE[0])
    _arrow(ax, 1.7, 2.0, 3.0, 2.9, col=EDGE[0])
    _arrow(ax, 4.6, 3.2, 5.6, 3.2, col=EDGE[0])
    _arrow(ax, 7.2, 3.2, 8.0, 3.2, col=ACCENT)
    ax.text(8.1, 3.2, "¬(a∧b)", fontsize=11, va="center", color=ACCENT)
    # Sağ devre: ¬a, ¬b -> VEYA
    _box(ax, 9.0, 4.2, 1.0, 0.7, "¬a", FILL[2], EDGE[2], bold=True)
    _box(ax, 9.0, 0.6, 1.0, 0.7, "¬b", FILL[2], EDGE[2], bold=True)
    _box(ax, 10.9, 2.0, 1.4, 1.4, "VEYA", FILL[1], EDGE[1], bold=True)
    _box(ax, 12.7, 2.4, 1.0, 0.6, "çıkış", FILL[4], EDGE[4])
    _arrow(ax, 10.0, 4.5, 10.9, 3.2, col=EDGE[2])
    _arrow(ax, 10.0, 1.0, 10.9, 2.3, col=EDGE[2])
    _arrow(ax, 12.3, 2.7, 12.7, 2.7, col=EDGE[1])
    ax.text(0.5, 0.3, "Doğruluk tablosu: a, b ∈ {0,1}; iki devrenin "
            "çıkışı her girişte aynıdır.", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("kapi_devre"))


def hasse():
    fig, ax = _tuval(9.6, 5.0, 10, 8)
    konum = {1: (5, 0.8), 2: (3, 2.9), 3: (7, 2.9), 4: (2, 5.0),
             6: (6, 5.0), 12: (5, 7.1)}
    kenar = [(1, 2), (1, 3), (2, 4), (2, 6), (3, 6), (4, 12), (6, 12)]
    for a, b in kenar:
        x1, y1 = konum[a]
        x2, y2 = konum[b]
        ax.plot([x1, x2], [y1 + 0.35, y2 - 0.35], color=EDGE[0],
                lw=1.6, zorder=1)
    for sayi, (x, y) in konum.items():
        _box(ax, x - 0.5, y - 0.35, 1.0, 0.7, str(sayi), FILL[0],
             ACCENT, fs=13, bold=True)
    ax.text(0.3, 7.8, "12'nin bölenleri: kısmi sıra (Hasse diyagramı)",
            fontsize=11, weight="bold", color=INK)
    ax.text(0.3, 0.3, "Kenar a → b: a | b ve aralarında başka bölen yok.",
            fontsize=9.5, color=MUTED)
    return _save(fig, _yol("hasse"))


def pascal():
    fig, ax = _tuval(9.6, 5.2, 14, 10)
    renk = [FILL[0], FILL[1], FILL[2], FILL[3], FILL[4]]
    for n in range(7):
        for k in range(n + 1):
            x = 7 - n * 1.0 + 2 * k
            y = 9.0 - n * 1.1
            val = math.comb(n, k)
            fill = renk[val % len(renk)] if val > 1 else FILL[0]
            _box(ax, x - 0.42, y - 0.36, 0.84, 0.72, str(val), fill,
                 EDGE[0] if n != 6 else ACCENT, fs=10,
                 bold=(n == 6))
    ax.text(0.3, 1.2, "Satır toplamı 2^n: 1, 2, 4, 8, 16, 32, 64, 128.",
            fontsize=10, color=INK)
    ax.text(0.3, 0.5, "Bordo çerçeve: n = 6 satırı (C(6,k) = 1, 6, 15, "
            "20, 15, 6, 1).", fontsize=10, color=MUTED)
    return _save(fig, _yol("pascal"))


def icerme_venn():
    fig, ax = _tuval(9.6, 5.2, 10, 9.5)
    merkez = {"A": (3.2, 3.8), "B": (6.8, 3.8), "C": (5.0, 6.2)}
    renk = {"A": (FILL[0], EDGE[0]), "B": (FILL[1], EDGE[1]),
            "C": (FILL[2], EDGE[2])}
    for ad in "ABC":
        c = Circle(merkez[ad], 2.1, facecolor=renk[ad][0],
                   edgecolor=renk[ad][1], alpha=0.7, lw=1.4)
        ax.add_patch(c)
        x, y = merkez[ad]
        ax.text(x, y, "", fontsize=1)
    # Bölge sayıları: 1..1000 içinde (2|x), (3|x), (5|x)
    say = {}
    for x in range(1, 1001):
        key = (x % 2 == 0, x % 3 == 0, x % 5 == 0)
        say[key] = say.get(key, 0) + 1
    bolge = [
        ((1.9, 3.4), (True, False, False)),
        ((8.1, 3.4), (False, True, False)),
        ((5.0, 7.6), (False, False, True)),
        ((5.0, 3.0), (True, True, False)),
        ((3.6, 5.6), (True, False, True)),
        ((6.4, 5.6), (False, True, True)),
        ((5.0, 4.7), (True, True, True)),
        ((0.9, 0.9), (False, False, False)),
    ]
    for (x, y), key in bolge:
        ax.text(x, y, str(say.get(key, 0)), ha="center",
                va="center", fontsize=11, weight="bold", color=INK)
    ax.text(0.2, 9.0, "A: 2'ye bölünen   B: 3'e bölünen   "
            "C: 5'e bölünen", fontsize=10.5, color=INK)
    ax.text(0.2, 0.2, "1..1000 içinde 2, 3 veya 5'e bölünenler: 734. "
            "Dış bölge: 266", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("icerme_venn"))


def derangement():
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ns, orans = [], []
    with open(os.path.join(VERI, "b47_derangement.csv"),
              encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ns.append(int(r["n"]))
            orans.append(float(r["oran"]))
    ax.plot(ns, orans, "o-", color=EDGE[0], lw=1.6, ms=5,
            label="D_n / n!")
    ax.axhline(1 / math.e, color=ACCENT, ls="--", lw=1.3,
               label="1/e ≈ 0.36788")
    ax.set_xlabel("n", color=INK)
    ax.set_ylabel("D_n / n!", color=INK)
    ax.set_title("Bozuk permütasyon oranı 1/e'ye yakınsar", color=INK)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("derangement"))


def oklid():
    fig, ax = _tuval(9.6, 4.4, 12, 7)
    adimlar = [("240 = 5 · 46 + 10", "10"), ("46 = 4 · 10 + 6", "6"),
               ("10 = 1 · 6 + 4", "4"), ("6 = 1 · 4 + 2", "2"),
               ("4 = 2 · 2 + 0", "0")]
    ax.text(0.3, 6.4, "gcd(240, 46): her adımda kalan küçülür",
            fontsize=11, weight="bold", color=INK)
    for i, (metin, kal) in enumerate(adimlar):
        y = 5.0 - i * 0.95
        _box(ax, 0.4, y - 0.3, 5.0, 0.6, metin, FILL[0], EDGE[0],
             fs=11)
        son = kal == "0"
        _box(ax, 6.1, y - 0.3, 1.8, 0.6, "kalan " + kal,
             FILL[1] if son else FILL[2], EDGE[1] if son else EDGE[2],
             fs=10.5, bold=True)
        if i < len(adimlar) - 1:
            _arrow(ax, 3.0, y - 0.32, 3.0, y - 0.63, col=MUTED, lw=1.1)
    ax.text(8.2, 0.9, "Son sıfır olmayan kalan\n= 2 = gcd", fontsize=10,
            color=ACCENT, va="center")
    return _save(fig, _yol("oklid"))


def konigsberg():
    fig, ax = _tuval(9.6, 5.2, 10, 8)
    p = {0: (5.0, 3.6), 1: (2.0, 6.2), 2: (2.0, 1.2), 3: (8.2, 3.6)}
    ad = {0: "A (ada)\nd=5", 1: "B\nd=3", 2: "C\nd=3", 3: "D\nd=3"}
    kenar = [((0, 1), 0.0), ((0, 1), 0.7), ((0, 2), 0.0),
             ((0, 2), -0.7), ((0, 3), 0.0), ((1, 3), 0.0),
             ((2, 3), 0.0)]
    for (u, v), buk in kenar:
        x1, y1 = p[u]
        x2, y2 = p[v]
        if buk == 0.0:
            ax.plot([x1, x2], [y1, y2], color=EDGE[0], lw=1.8, zorder=1)
        else:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy)
            nx, ny = -dy / L, dx / L
            cx, cy = mx + nx * buk * 2.2, my + ny * buk * 2.2
            ts = [i / 40 for i in range(41)]
            xs = [(1 - s) ** 2 * x1 + 2 * (1 - s) * s * cx + s * s * x2
                  for s in ts]
            ys = [(1 - s) ** 2 * y1 + 2 * (1 - s) * s * cy + s * s * y2
                  for s in ts]
            ax.plot(xs, ys, color=EDGE[0], lw=1.8, zorder=1)
    for k, (x, y) in p.items():
        _box(ax, x - 0.75, y - 0.45, 1.5, 0.9, ad[k], FILL[0], ACCENT,
             fs=11, bold=True)
    ax.text(0.3, 7.6, "Königsberg: 7 köprü, her köprü bir kez geçilecek",
            fontsize=10.5, color=INK, weight="bold")
    ax.text(0.3, 0.2, "Dereceler: A=5, B=3, C=3, D=3. Tek dereceli 4 "
            "düğüm var: Euler yolu yok.", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("konigsberg"))


def euler_formul():
    fig, ax = _tuval(9.6, 5.0, 10, 8)
    A, B, C, D = (1.0, 1.0), (8.0, 1.0), (4.5, 7.0), (4.5, 3.2)
    kenar = [(A, B), (B, C), (C, A), (D, A), (D, B), (D, C)]
    for u, v in kenar:
        ax.plot([u[0], v[0]], [u[1], v[1]], color=EDGE[0], lw=1.8,
                zorder=1)
    for ad, (x, y) in zip("ABCD", (A, B, C, D)):
        _box(ax, x - 0.35, y - 0.3, 0.7, 0.6, ad, FILL[0], ACCENT,
             fs=12, bold=True)
    for ad, (x, y) in [("F1 dış", (1.2, 6.2)), ("F2", (4.5, 1.9)),
                       ("F3", (2.6, 3.2)), ("F4", (6.4, 3.2))]:
        ax.text(x, y, ad, fontsize=10, color=ACCENT, ha="center")
    ax.text(0.2, 7.9, "K4 düzlemsel gösterim: V=4, E=6, F=4",
            fontsize=10.5, color=INK, weight="bold")
    ax.text(0.2, 0.3, "Euler: V − E + F = 4 − 6 + 4 = 2", fontsize=10.5,
            color=INK)
    return _save(fig, _yol("euler_formul"))


def boyama():
    fig, ax = _tuval(9.6, 4.8, 14, 7)
    m = 3
    renkler = ["#8A2D2B", "#3E566B", "#8A6B2D", "#47624A"]
    kotu = [0, 3, 1, 4, 2, 5]
    iyi = [0, 1, 2, 3, 4, 5]
    for baslik, sira, x0 in (("Kötü sıra: 3 renk", kotu, 0.5),
                             ("İyi sıra: 2 renk", iyi, 7.2)):
        kom = {u: [] for u in range(2 * m)}
        for i in range(m):
            for j in range(m):
                if i != j:
                    kom[i].append(m + j)
                    kom[m + j].append(i)
        renk = [-1] * (2 * m)
        for u in sira:
            yasak = {renk[v] for v in kom[u] if renk[v] != -1}
            c = 0
            while c in yasak:
                c += 1
            renk[u] = c
        ax.text(x0 + 2.2, 6.3, baslik, ha="center", fontsize=11,
                weight="bold", color=INK)
        pos = {}
        for i in range(m):
            pos[i] = (x0 + 0.7, 5.2 - i * 1.7)
            pos[m + i] = (x0 + 3.7, 5.2 - i * 1.7)
        for u in range(m):
            for v in kom[u]:
                ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                        color=RULE, lw=1.1, zorder=0)
        for u in range(2 * m):
            x, y = pos[u]
            ax.add_patch(Circle((x, y), 0.36,
                                facecolor=renkler[renk[u]],
                                edgecolor=INK, lw=0.6, zorder=2))
            ax.text(x, y, str(u), ha="center", va="center", fontsize=9,
                    color="white", weight="bold", zorder=3)
    ax.text(0.3, 0.3, "Taç graf: i ~ m+j, i≠j. Boyama sayısı 2 ama kötü "
            "sıra 3 renk kullanır.", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("boyama"))


def pnp():
    fig, ax = _tuval(9.6, 5.0, 10, 8)
    ax.add_patch(Ellipse((4.0, 4.0), 7.2, 6.2, fill=False,
                         edgecolor=EDGE[0], lw=1.8))
    ax.add_patch(Ellipse((6.6, 3.8), 6.4, 5.2, fill=False,
                         edgecolor=EDGE[3], lw=1.5, ls="--"))
    ax.add_patch(Ellipse((1.9, 3.6), 2.6, 3.0, facecolor=FILL[1],
                         edgecolor=EDGE[1], lw=1.5, alpha=0.9))
    ax.add_patch(Ellipse((5.9, 3.4), 2.6, 2.4, facecolor=FILL[2],
                         edgecolor=EDGE[2], lw=1.5, alpha=0.9))
    ax.text(1.9, 3.5, "P", fontsize=13, weight="bold", ha="center")
    ax.text(5.9, 3.4, "NP-tam", fontsize=11, weight="bold",
            ha="center")
    ax.text(4.0, 6.6, "NP", fontsize=13, weight="bold", ha="center")
    ax.text(8.3, 2.5, "NP-zor" + chr(10) + "(NP-tam olmayan" + chr(10)            + "kısım NP dışında)",
            fontsize=9, ha="center", va="center", color=ACCENT)
    ax.text(0.3, 0.3, "P ⊆ NP. P ≠ NP varsayımı altında NP-tam ile P "
            "ayrıktır. Hamilton yolu NP-tam.", fontsize=9.2, color=MUTED)
    return _save(fig, _yol("pnp"))


if __name__ == "__main__":
    for f in (kapi_devre, hasse, pascal, icerme_venn, derangement,
              oklid, konigsberg, euler_formul, boyama, pnp):
        print(f())
