# -*- coding: utf-8 -*-
"""Bolum 18 - 'Greedy' diyagramlari.

Sekillerdeki veriler, bolumdeki programlarla ayni mantikla hesaplanir
(etkinlik listesi, karsi ornekler, Huffman agaci, sirt cantasi,
Dijkstra cizgesi). Metin kutulari tuval icinde kalir, ust uste binmez.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Ellipse
import heapq
import math
import os
from collections import Counter

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "gorseller")
_ORNEK_METIN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "bolumler", "bolum_16.md")


def _cubuk(ax, x1, x2, y, h, metin, fill, edge, fs=8.6, tcol=INK):
    ax.add_patch(Rectangle((x1, y), x2 - x1, h, facecolor=fill,
                           edgecolor=edge, lw=1.0, zorder=2))
    ax.text((x1 + x2) / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=fs, color=tcol, zorder=3)


# ---------------------------------------------------------------- 1
def aktivite(path):
    """Etkinlik secimi: bitisine gore sirali, secilenler vurgulu."""
    t = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10),
         (8, 11)]
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(-2.6, 12.6)
    ax.set_ylim(-1.0, len(t) + 0.2)
    ax.axis("off")
    son = float("-inf")
    for r, (s, e) in enumerate(sorted(t, key=lambda x: x[1])):
        y = len(t) - 1 - r + 0.12
        secildi = s >= son
        fill = FILL[3] if secildi else FILL[0]
        edge = ACCENT if secildi else MUTED
        ax.text(-0.25, y + 0.25, "(%d,%d)" % (s, e), ha="right",
                va="center", fontsize=9, color=INK)
        ax.add_patch(Rectangle((s, y), e - s, 0.6, facecolor=fill,
                               edgecolor=edge, lw=1.2, zorder=2))
        ax.text(s + (e - s) / 2, y + 0.3,
                "seçildi" if secildi else "çakışıyor", ha="center",
                va="center", fontsize=8.2,
                color=ACCENT if secildi else MUTED, zorder=3)
        if secildi:
            son = e
            ax.plot([e, e], [-0.3, y + 0.6], ls="--", lw=0.9,
                    color=ACCENT_L, zorder=1)
    for x in range(0, 13, 2):
        ax.text(x, -0.45, str(x), ha="center", fontsize=8, color=MUTED)
    ax.plot([0, 12], [-0.25, -0.25], color=RULE, lw=0.9)
    ax.text(6.0, -0.95, "zaman", ha="center", fontsize=8.5, color=MUTED)
    return _save(fig, path)


# ---------------------------------------------------------------- 2
def _kaba_kume(a):
    n, en_iyi, kume = len(a), 0, []
    for m in range(1 << n):
        sec = sorted(a[i] for i in range(n) if m >> i & 1)
        if all(sec[i + 1][0] >= sec[i][1] for i in range(len(sec) - 1)):
            if len(sec) > en_iyi:
                en_iyi, kume = len(sec), sec
    return kume


def karsi_ornek(path):
    """Uc acgozlu kuralin karsi ornekleri: acgozlu ve optimum satirlar."""
    ornekler = [
        ("a) başlangıca göre: (0,10) seçilir", [(0, 10), (1, 2), (3, 4)],
         [(0, 10)]),
        ("b) en kısa önce: (2,4) yüzünden iki komşu kaybedilir",
         [(0, 3), (2, 4), (3, 5)], [(2, 4)]),
    ]
    c = [(2, 8), (3, 10), (6, 11), (8, 13), (11, 15), (14, 20), (18, 27),
         (20, 24), (22, 27)]
    ac = [(6, 11), (11, 15), (20, 24)]
    ornekler.append(("c) az çakışma: 9 aralıkta 3 seçilir, 4 mümkündür",
                     c, ac))
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xlim(-0.2, 28.5)
    ax.set_ylim(1.2, 9.6)
    ax.axis("off")
    y = 9.0
    for baslik, girdi, acg in ornekler:
        kume = _kaba_kume(girdi)
        ax.text(0, y, baslik, fontsize=9.4, color=INK, weight="bold",
                va="center")
        y -= 0.7
        for etiket, sec, fill, edge in (
                ("açgözlü", acg, FILL[3], ACCENT),
                ("optimum", kume, FILL[1], EDGE[1])):
            ax.text(-0.12, y + 0.22, etiket, ha="right", va="center",
                    fontsize=8.6, color=MUTED)
            for s, e in sec:
                _cubuk(ax, s, e, y, 0.44, "%d-%d" % (s, e), fill, edge,
                       fs=7.8)
            y -= 0.62
        y -= 0.5
    return _save(fig, path)


# ---------------------------------------------------------------- 3
def degis_tokus(path):
    """Degis-tokus argumani: optimum O'dan ilk elemani g1 ile degistir."""
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.text(0.2, 7.3, "Optimum O:", fontsize=10, color=INK, weight="bold")
    for i, lab in enumerate(["o1", "o2", "o3", "...", "ok"]):
        _box(ax, 2.4 + i * 1.5, 6.6, 1.2, 0.9, lab,
             fill=FILL[0] if i else FILL[3], edge=EDGE[0] if i else ACCENT,
             fs=10, bold=True)
    ax.text(0.2, 4.2, "Açgözlü g1:", fontsize=10, color=INK,
            weight="bold")
    _box(ax, 2.4, 3.7, 1.2, 0.9, "g1", fill=FILL[1], edge=EDGE[1],
         fs=10, bold=True)
    ax.text(4.0, 4.15, "bitişi en erken (e(g1) ≤ e(o1))", fontsize=8.6,
            color=MUTED, va="center")
    _arrow(ax, 3.0, 6.6, 3.0, 4.6, col=ACCENT, rad=0.0)
    ax.text(3.15, 5.55, "o1 yerine g1", fontsize=8.6, color=ACCENT,
            va="center")
    ax.text(0.2, 1.9, "O' = O - o1 + g1:", fontsize=10, color=INK,
            weight="bold")
    for i, lab in enumerate(["g1", "o2", "o3", "...", "ok"]):
        _box(ax, 2.4 + i * 1.5, 1.3, 1.2, 0.9, lab,
             fill=FILL[1] if i == 0 else FILL[0],
             edge=EDGE[1] if i == 0 else EDGE[0], fs=10, bold=True)
    ax.text(9.7, 0.45, "o2, o3 ... değişmedi; geçerli ve |O'| = |O|",
            fontsize=8.4, color=MUTED, ha="right")
    return _save(fig, path)


# ---------------------------------------------------------------- 4
def sweep_oda(path):
    """Aralik bolumleme: oda seritleri ve ayni anda aktif aralik sayisi."""
    a = [(1, 4), (2, 6), (3, 5), (5, 8), (6, 10), (7, 9), (9, 12)]
    oda = {(1, 4): 0, (5, 8): 0, (9, 12): 0, (2, 6): 1, (7, 9): 1,
           (3, 5): 2, (6, 10): 2}
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(9.6, 5.2),
                                 gridspec_kw={"height_ratios": [2.2, 1.3]})
    ax.set_xlim(0, 12.6)
    ax.set_ylim(-0.4, 3.5)
    ax.axis("off")
    renk = [(FILL[3], ACCENT), (FILL[1], EDGE[1]), (FILL[2], EDGE[2])]
    for s, e in a:
        r = oda[(s, e)]
        fill, edge = renk[r]
        y = 2.5 - r
        _cubuk(ax, s, e, y, 0.7, "[%d,%d)" % (s, e), fill, edge, fs=8.6)
    for r in range(3):
        ax.text(-0.1, 2.85 - r, "oda %d" % r, ha="right", va="center",
                fontsize=8.8, color=MUTED)
    for x in range(0, 13, 1):
        ax.text(x, -0.25, str(x), ha="center", fontsize=7.8, color=MUTED)
    t = [x / 10 for x in range(0, 125)]
    aktif = [sum(1 for s, e in a if s <= x < e) for x in t]
    bx.step(t, aktif, where="post", color=ACCENT, lw=1.6)
    bx.axhline(3, ls="--", lw=0.9, color=ACCENT_L)
    bx.text(12.4, 3.15, "derinlik = 3 = oda sayısı", ha="right",
            fontsize=8.6, color=ACCENT_L)
    bx.set_xlim(0, 12.6)
    bx.set_ylim(0, 3.8)
    bx.set_ylabel("aktif", fontsize=8.8, color=MUTED)
    bx.set_xlabel("zaman", fontsize=8.8, color=MUTED)
    bx.tick_params(labelsize=7.8, colors=MUTED)
    for sp in ("top", "right"):
        bx.spines[sp].set_visible(False)
    fig.subplots_adjust(hspace=0.35)
    return _save(fig, path)


# ---------------------------------------------------------------- 5
def fraksiyon(path):
    """Kesirli ve 0/1 sirt cantasi: ayni esyalar, farkli sonuc."""
    es = [(10, 60), (20, 100), (30, 120)]
    W = 50
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.set_xlim(-8.8, 58)
    ax.set_ylim(-0.9, 3.7)
    ax.axis("off")
    cizim = [
        ("kesirli", [(0, 10, FILL[3], ACCENT, "E1 (10) = 60"),
                     (10, 30, FILL[1], EDGE[1], "E2 (20) = 100"),
                     (30, 50, FILL[2], EDGE[2], "E3 kesir 20/30 = 80")],
         "toplam 240"),
        ("0/1", [(0, 0, FILL[0], EDGE[0], ""),
                 (0, 20, FILL[1], EDGE[1], "E2 = 100"),
                 (20, 50, FILL[2], EDGE[2], "E3 = 120")],
         "toplam 220"),
    ]
    y = 2.1
    for ad, parca, toplam in cizim:
        ax.text(-0.9, y + 0.5, ad, ha="right", va="center", fontsize=9.6,
                color=INK, weight="bold")
        for s, e, fill, edge, metin in parca:
            if e > s:
                _cubuk(ax, s, e, y, 1.0, metin, fill, edge, fs=8.4)
        ax.text(51.2, y + 0.5, toplam, va="center", fontsize=9.2,
                color=ACCENT, weight="bold")
        y -= 1.6
    ax.plot([W, W], [-0.9, 2.9], ls="--", lw=1.0, color=ACCENT)
    ax.text(W, 3.3, "kapasite W = 50", ha="center", fontsize=8.8,
            color=ACCENT)
    for x in (0, 10, 20, 30, 40, 50):
        ax.text(x, -1.05, str(x), ha="center", fontsize=7.8, color=MUTED)
    ax.text(0.0, 3.3, "ağırlık birimi ->", fontsize=8.4, color=MUTED)
    return _save(fig, path)


# ---------------------------------------------------------------- 6
def huffman_adim(path):
    """Huffman: 'abracadabra' icin orman durumlari, adim adim."""
    durumlar = [
        ("Adım 0", [("a:5", 0), ("b:2", 0), ("r:2", 0), ("c:1", 0),
                    ("d:1", 0)]),
        ("Adım 1: c+d", [("a:5", 0), ("b:2", 0), ("r:2", 0),
                         ("(cd):2", 1)]),
        ("Adım 2: b+r", [("a:5", 0), ("(cd):2", 0), ("(br):4", 1)]),
        ("Adım 3: (cd)+(br)", [("a:5", 0), ("((cd)(br)):6", 1)]),
        ("Adım 4: a+(...)", [("kök:11", 1)]),
    ]
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    for k, (baslik, kutular) in enumerate(durumlar):
        x = 0.2 + k * 2.0
        ax.text(x + 0.85, 5.9, baslik, ha="center", fontsize=7.8,
                color=INK, weight="bold")
        for i, (metin, yeni) in enumerate(kutular):
            fill = FILL[3] if yeni else FILL[0]
            edge = ACCENT if yeni else EDGE[0]
            _box(ax, x, 4.8 - i * 0.9, 1.7, 0.7, metin, fill=fill,
                 edge=edge, fs=8.2, bold=bool(yeni))
        if k < len(durumlar) - 1:
            _arrow(ax, x + 1.8, 3.0, x + 2.0, 3.0, col=MUTED, lw=1.2)
    ax.text(5.0, 0.5, "bordo: o adımda oluşan düğüm. "
            "En küçük iki frekans her adımda birleşir.",
            ha="center", fontsize=8.4, color=MUTED)
    return _save(fig, path)


# ---------------------------------------------------------------- 7
def kesme(path):
    """Kesme ozelligi: e (en hafif gecen kenar) ve T'deki f degisimi."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.add_patch(Ellipse((2.4, 3.2), 3.2, 3.8, facecolor=FILL[0],
                         edgecolor=EDGE[0], lw=1.0))
    ax.add_patch(Ellipse((7.6, 3.2), 3.2, 3.8, facecolor=FILL[2],
                         edgecolor=EDGE[2], lw=1.0))
    ax.text(2.4, 5.3, "S", ha="center", fontsize=12, color=INK,
            weight="bold")
    ax.text(7.6, 5.3, "V - S", ha="center", fontsize=12, color=INK,
            weight="bold")
    p = {"u": (1.5, 3.7), "v": (1.5, 2.4), "x": (8.5, 3.7),
         "y": (8.5, 2.4)}
    # T (MST) icinde kenarlar: u-v, x-y ve kesimi geçen f = v-y
    ax.plot([1.5, 1.5], [3.7, 2.4], lw=2.0, color=EDGE[0], zorder=1)
    ax.plot([8.5, 8.5], [3.7, 2.4], lw=2.0, color=EDGE[0], zorder=1)
    ax.plot([1.5, 8.5], [2.4, 2.4], lw=2.4, color=EDGE[0], zorder=1)
    # e: T'de olmayan, en hafif kesim kenari
    ax.plot([1.5, 8.5], [3.7, 3.7], ls="--", lw=1.8, color=ACCENT,
            zorder=1)
    ax.text(5.0, 3.95, "e", ha="center", fontsize=11, color=ACCENT,
            weight="bold")
    ax.text(5.0, 2.12, "f", ha="center", fontsize=11, color=EDGE[0],
            weight="bold")
    for k, (x, y) in p.items():
        ax.add_patch(Circle((x, y), 0.26, facecolor="white",
                            edgecolor=INK, lw=1.0, zorder=3))
        ax.text(x, y, k, ha="center", va="center", fontsize=10,
                color=INK, zorder=4)
    ax.text(5.0, 0.95, "e: kesimi geçen en hafif kenar; f: T'nin kesim "
            "kenarı, w(f) ≥ w(e).\n"
            "T + e bir döngü oluşturur; f çıkarılırsa "
            "T' = T - f + e, w(T') ≤ w(T).",
            ha="center", va="center", fontsize=8.4, color=INK)
    return _save(fig, path)


# ---------------------------------------------------------------- 8
def _huff_uzunluklar(frekans):
    kuyruk = []
    for sayac, (s, f) in enumerate(sorted(frekans.items())):
        heapq.heappush(kuyruk, (f, sayac, [s]))
    sayac = len(kuyruk)
    uzun = {s: 0 for s in frekans}
    while len(kuyruk) > 1:
        f1, _, g1 = heapq.heappop(kuyruk)
        f2, _, g2 = heapq.heappop(kuyruk)
        for s in g1 + g2:
            uzun[s] += 1
        heapq.heappush(kuyruk, (f1 + f2, sayac, g1 + g2))
        sayac += 1
    return uzun


def entropi_uzunluk(path):
    """Huffman kod uzunlugu ile ideal (-log2 p) uzunlugu: gercek metin."""
    with open(_ORNEK_METIN, "rb") as f:
        veri = f.read()
    frekans = Counter(veri)
    toplam = len(veri)
    en_sik = [b for b, _ in frekans.most_common(12)]
    frekans_hex = {bytes([b]).hex(): f for b, f in frekans.items()}
    uz = _huff_uzunluklar(frekans_hex)
    etiket, ideal, huff = [], [], []
    for b in en_sik:
        p = frekans[b] / toplam
        ideal.append(-math.log2(p))
        huff.append(uz[bytes([b]).hex()])
        if 32 < b < 127:
            etiket.append("'%s'" % chr(b))
        elif b == 32:
            etiket.append("boşluk")
        else:
            etiket.append("0x%02X" % b)
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    x = list(range(len(en_sik)))
    ax.bar([i - 0.2 for i in x], ideal, width=0.4, color=RULE,
           edgecolor=MUTED, lw=0.8, label="-log2 p (ideal)")
    ax.bar([i + 0.2 for i in x], huff, width=0.4, color=ACCENT,
           label="Huffman kod uzunluğu")
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, fontsize=8.2, color=INK)
    ax.set_ylabel("bit", fontsize=9, color=MUTED)
    ax.tick_params(labelsize=8, colors=MUTED)
    ax.legend(fontsize=8.6, frameon=False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("bolum_16.md, bayt frekansı: en sık 12 bayt",
                 fontsize=9, color=MUTED)
    return _save(fig, path)


# ---------------------------------------------------------------- 9
def dijkstra_negatif(path):
    """Negatif kenar: Dijkstra X'i 5 ile kesinler; gercek yol 3."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    konum = {"S": (0.6, 1.2), "Y": (2.8, 2.6), "X": (5.0, 1.2)}
    for ax, baslik, vurgu, deger in (
            (ax1, "Dijkstra X'i 5 ile kesinleştirir", [("S", "X")], "X = 5"),
            (ax2, "Gerçek en kısa: S-Y-X = 6 - 3 = 3",
             [("S", "Y"), ("Y", "X")], "X = 3")):
        ax.set_xlim(-0.2, 5.8)
        ax.set_ylim(0.3, 3.4)
        ax.axis("off")
        ax.set_title(baslik, fontsize=9.2, color=INK)
        # kenar: (u, v, agirlik, etiket konumu)
        kenarlar = [("S", "X", "5", (2.8, 0.95)),
                    ("S", "Y", "6", (1.1, 2.3)),
                    ("Y", "X", "-3", (4.5, 2.3))]
        for u, v, w, (lx, ly) in kenarlar:
            col = ACCENT if (u, v) in vurgu else MUTED
            lw = 2.0 if (u, v) in vurgu else 1.0
            _arrow(ax, konum[u][0], konum[u][1], konum[v][0],
                   konum[v][1], col=col, lw=lw, rad=0.0)
            ax.text(lx, ly, w, fontsize=9.4, color=col, ha="center",
                    weight="bold" if (u, v) in vurgu else "normal")
        for k, (x, y) in konum.items():
            ax.add_patch(Circle((x, y), 0.28, facecolor="white",
                                edgecolor=INK, lw=1.0, zorder=3))
            ax.text(x, y, k, ha="center", va="center", fontsize=10,
                    color=INK, zorder=4)
        ax.text(2.8, 0.5, deger, ha="center", fontsize=10,
                color=ACCENT, weight="bold")
    return _save(fig, path)


if __name__ == "__main__":
    out = _OUT
    for f in (aktivite, karsi_ornek, degis_tokus, sweep_oda, fraksiyon,
              huffman_adim, kesme, entropi_uzunluk, dijkstra_negatif):
        name = f.__name__
        print(f(os.path.join(out, "b18_%s.png" % name)))
