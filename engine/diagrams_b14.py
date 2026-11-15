# -*- coding: utf-8 -*-
"""Bölüm 14 — 'Arama' için diyagramlar.

Grafikler, bölümdeki programların kullandığı algoritmalarla hesaplanan
değerlerden çizilir (sabit tohum: random.seed(42)). Sayılar, bölüm metnindeki
terminal çıktılarıyla birebir aynı algoritmadan gelir.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import random
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def _ayar(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(True, color=RULE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)


def _hucre(ax, x, y, w, h, metin, fill, edge, lw=1.1, tcol=INK, bold=True):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                           lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=9.5, color=tcol, weight="bold" if bold else "normal",
            zorder=3)


# ----- bölümdeki algoritmalar (metindeki kodla aynı mantık) ----------------
def gun_sayisi(agirliklar, kapasite):
    gun, yuk = 1, 0
    for w in agirliklar:
        if yuk + w > kapasite:
            gun += 1
            yuk = 0
        yuk += w
    return gun


def ustel_ara(oku, x, iz):
    sinir = 1
    iz.append(sinir)
    while oku(sinir) < x:
        sinir *= 2
        iz.append(sinir)
    lo, hi = sinir // 2, sinir
    while lo < hi:
        orta = lo + (hi - lo) // 2
        iz.append(orta)
        if oku(orta) < x:
            lo = orta + 1
        else:
            hi = orta
    return lo


def ikili(a, x):
    lo, hi, say = 0, len(a) - 1, 0
    while lo <= hi:
        say += 1
        orta = (lo + hi) // 2
        if a[orta] == x:
            return orta, say
        if a[orta] < x:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1, say


def enterpolasyon(a, x):
    lo, hi, say = 0, len(a) - 1, 0
    while lo <= hi and a[lo] <= x <= a[hi]:
        say += 1
        if a[hi] == a[lo]:
            pos = lo
        else:
            pos = lo + (x - a[lo]) * (hi - lo) // (a[hi] - a[lo])
        if a[pos] == x:
            return pos, say
        if a[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1, say


def min_adim(a):
    """Döndürülmüş dizide min arama; (konum, adım)."""
    lo, hi, adim = 0, len(a) - 1, 0
    while lo < hi:
        orta = lo + (hi - lo) // 2
        adim += 1
        if a[orta] > a[hi]:
            lo = orta + 1
        elif a[orta] < a[hi]:
            hi = orta
        else:
            hi -= 1
    return lo, adim


# --------------------------------------------------------------------------- #
def ikili_aralik(path):
    """Şekil 14.1: ikili aramada [lo, hi) aralığının daralması ve değişmez."""
    a = [2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91, 99]
    x = 56
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(0.3, 9.5, "Hedef x = %d  ·  dizi sıralı, n = %d" % (x, len(a)),
            fontsize=10, color=INK, weight="bold")
    adimlar = [(0, 12), (7, 12), (7, 9)]
    etiket = [
        "adım 0: orta = 6, a[6] = 38 < 56  →  lo = 7",
        "adım 1: orta = 9, a[9] = 72 >= 56  →  hi = 9",
        "adım 2: orta = 8, a[8] = 56 = x  →  bulundu",
    ]
    y_satir = [6.9, 4.1, 1.3]
    x0, w = 0.6, 0.98
    for s, (lo, hi) in enumerate(adimlar):
        y = y_satir[s]
        for i, v in enumerate(a):
            xi = x0 + i * w
            if i < lo:
                fill, edge = FILL[0], EDGE[0]
            elif i >= hi:
                fill, edge = FILL[3], EDGE[3]
            else:
                fill, edge = "#FFFFFF", MUTED
            tcol = INK
            if i == (lo + hi) // 2 and lo < hi:
                edge = ACCENT
            _hucre(ax, xi, y, w * 0.92, 0.9, str(v), fill, edge,
                   lw=2.2 if (i == (lo + hi) // 2 and lo < hi) else 1.1,
                   tcol=tcol)
            ax.text(xi + w * 0.46, y - 0.3, str(i), ha="center",
                    va="center", fontsize=7.5, color=MUTED)
        ax.text(x0, y + 1.12, "[lo, hi) = [%d, %d)" % (lo, hi),
                fontsize=8.8, color=INK, weight="bold")
        ax.text(x0, y - 0.82, etiket[s], fontsize=8.6, color=INK)
    ax.text(0.3, 0.05, "mavi: x'ten küçük (a[i] < x)     "
            "kırmızı: x'e eşit ya da büyük     beyaz: belirsiz [lo, hi)",
            fontsize=8.2, color=MUTED)
    return _save(fig, path)


def sinir(path):
    """Şekil 14.2: alt sınır, üst sınır ve eşit aralık."""
    a = [1, 2, 2, 2, 3, 5, 5, 8]
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    x0, w = 0.7, 1.3
    yb, hb = 2.9, 1.0
    ax.add_patch(Rectangle((x0 + 1 * w, yb - 0.25), 3 * w, hb + 0.5,
                           facecolor=FILL[1], edgecolor="none", zorder=1))
    for i, v in enumerate(a):
        xi = x0 + i * w
        fill = FILL[1] if 1 <= i <= 3 else "#FFFFFF"
        _hucre(ax, xi, yb, w * 0.92, hb, str(v), fill,
               EDGE[1] if 1 <= i <= 3 else MUTED)
        ax.text(xi + w * 0.46, yb - 0.4, str(i), ha="center", va="center",
                fontsize=8, color=MUTED)
    ax.text(x0 + 4 * w, 1.1, "x = 2 için eşit aralık [1, 4): sayı = 3",
            fontsize=9.2, color=EDGE[1], weight="bold", ha="center")
    _arrow(ax, x0 + 1.2 * w, 5.3, x0 + 1 * w + 0.46 * w, yb + hb + 0.1,
           col=ACCENT, lw=1.6)
    ax.text(x0 + 1.2 * w, 5.45, "alt sınır: ilk a[i] >= 2  →  i = 1",
            fontsize=9, color=ACCENT, weight="bold", ha="left")
    _arrow(ax, x0 + 4.9 * w, 4.5, x0 + 4 * w + 0.46 * w, yb + hb + 0.1,
           col=EDGE[0], lw=1.6)
    ax.text(x0 + 4.9 * w, 4.7, "üst sınır: ilk a[i] > 2  →  i = 4",
            fontsize=9, color=EDGE[0], weight="bold", ha="left")
    return _save(fig, path)


def monoton(path):
    """Şekil 14.3: monoton yüklem F...F T...T ve ilk T."""
    fig, ax = plt.subplots(figsize=(9.2, 3.2))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    ax.text(0.2, 4.7, "p(i): i*i >= 50   (i = 0 … 9)", fontsize=10,
            color=INK, weight="bold")
    x0, w = 0.9, 1.05
    for i in range(10):
        dogru = i * i >= 50
        fill = FILL[3] if dogru else FILL[0]
        edge = ACCENT if dogru else EDGE[0]
        _hucre(ax, x0 + i * w, 2.4, w * 0.92, 0.95,
               "T" if dogru else "F", fill, edge)
        ax.text(x0 + i * w + w * 0.46, 2.0, str(i), ha="center",
                va="center", fontsize=8, color=MUTED)
    xk = x0 + 8 * w + w * 0.46
    _arrow(ax, xk, 4.05, xk, 3.42, col=ACCENT, lw=1.6)
    ax.text(xk, 4.2, "ilk T = 8", ha="center", fontsize=9.5,
            color=ACCENT, weight="bold")
    ax.text(0.9, 0.35, "F ... F  T ... T : tek bir geçiş noktası var; "
            "ikili arama bunu bulur.", fontsize=8.8, color=INK)
    return _save(fig, path)


def cevap(path):
    """Şekil 14.4: kapasite arttıkça gün sayısı azalır (monoton)."""
    w = list(range(1, 11))
    kap = np.arange(10, 56)
    gunler = [gun_sayisi(w, int(c)) for c in kap]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.step(kap, gunler, where="post", color=ACCENT, lw=2.0, zorder=3)
    ax.axhline(5, color=EDGE[0], lw=1.2, ls="--", zorder=2)
    ax.text(55, 5.15, "D = 5 gün", ha="right", fontsize=9, color=EDGE[0],
            weight="bold")
    ax.axvline(15, color=MUTED, lw=1.0, ls=":")
    ax.text(15.6, 9.2, "min kapasite = 15", fontsize=9.2, color=INK,
            weight="bold")
    ax.set_xlabel("kapasite C", color=INK, fontsize=9.5)
    ax.set_ylabel("gerekli gün sayısı", color=INK, fontsize=9.5)
    ax.set_title("Kapasite arttıkça gün sayısı azalır: cevap uzayı monoton",
                 color=INK, fontsize=10.2, weight="bold", loc="left")
    ax.set_ylim(0, 11)
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def dondurulmus(path):
    """Şekil 14.5: döndürülmüş dizi ve tekrarlarda en kötü durum."""
    a = [4, 5, 6, 7, 0, 1, 2]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.0))
    cols = [ACCENT if v == 0 else EDGE[0] for v in a]
    ax1.bar(range(len(a)), a, color=cols, width=0.65, zorder=3)
    for i, v in enumerate(a):
        ax1.text(i, v + 0.15, str(v), ha="center", fontsize=8.8, color=INK)
    ax1.set_xticks(range(len(a)))
    ax1.set_xlabel("indeks", color=INK, fontsize=9)
    ax1.set_ylabel("değer", color=INK, fontsize=9)
    ax1.set_title("Döndürülmüş dizi: minimum 4. indekste",
                  color=INK, fontsize=9.6, weight="bold", loc="left")
    _ayar(ax1)
    ns = [8, 16, 32, 64, 128, 256, 512, 1024]
    farkli = []
    for n in ns:
        enb = 0
        for k in range(n):
            arr = [(i + k) % n for i in range(n)]
            _, adim = min_adim(arr)
            enb = max(enb, adim)
        farkli.append(enb)
    tek = [n - 1 for n in ns]
    ax2.plot(ns, farkli, "o-", color=EDGE[1], lw=2.0,
             label="farklı elemanlar (en kötü)")
    ax2.plot(ns, tek, "s-", color=ACCENT, lw=2.0,
             label="tekrar: [0,1,...,1] (adım = n−1)")
    ax2.set_xscale("log", base=2)
    ax2.set_yscale("log", base=2)
    ax2.set_xlabel("n", color=INK, fontsize=9)
    ax2.set_ylabel("en fazla döngü turu", color=INK, fontsize=9)
    ax2.set_title("Tekrarlar O(log n)'yi O(n)'e düşürür",
                  color=INK, fontsize=9.6, weight="bold", loc="left")
    ax2.legend(frameon=False, fontsize=8.2, loc="upper left")
    _ayar(ax2)
    fig.tight_layout()
    return _save(fig, path)


def matris(path):
    """Şekil 14.6: sağ üst köşeden yürüyüş (x = 20, bulunamaz)."""
    m = [[1, 4, 7, 11, 15],
         [2, 5, 8, 12, 19],
         [3, 6, 9, 16, 22],
         [10, 13, 14, 17, 24]]
    ziyaret = [(0, 4), (1, 4), (2, 4), (2, 3), (3, 3)]
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.set_xlim(-0.2, 5.6)
    ax.set_ylim(4.7, -0.9)
    ax.axis("off")
    for i in range(4):
        for j in range(5):
            if (i, j) in ziyaret:
                fill, edge = FILL[2], EDGE[2]
            else:
                fill, edge = "#FFFFFF", MUTED
            _hucre(ax, j, i, 0.92, 0.92, str(m[i][j]), fill, edge)
    for k in range(len(ziyaret) - 1):
        (i1, j1), (i2, j2) = ziyaret[k], ziyaret[k + 1]
        if i2 == i1 + 1:             # aşağı: alt kenardan üst kenara
            x1, y1, x2, y2 = j1 + 0.46, i1 + 0.92, j2 + 0.46, i2
        else:                        # sola: sol kenardan sağ kenara
            x1, y1, x2, y2 = j1, i1 + 0.46, j2 + 0.92, i2 + 0.46
        _arrow(ax, x1, y1, x2, y2, col=ACCENT, lw=1.8)
        ax.patches[-1].set_zorder(5)     # oklar hücrelerin üstünde
    for k, (i, j) in enumerate(ziyaret):
        ax.text(j + 0.1, i + 0.22, str(k + 1), fontsize=8.5,
                color=ACCENT, weight="bold", zorder=6)
    ax.text(0.0, -0.55, "x = 20. Sağ üst köşeden başla: büyükse sola, "
            "küçükse aşağı.", fontsize=9, color=INK)
    ax.text(0.0, 4.95, "Ziyaret sırası: (0,4) → (1,4) → (2,4) → (2,3) → "
            "(3,3); 5 adım", fontsize=8.6, color=ACCENT, weight="bold")
    return _save(fig, path)


def ustel(path):
    """Şekil 14.7: üstel arama konum dizisi (x = 3000, p = 1000)."""
    oku = lambda i: 3 * i
    iz = []
    konum = ustel_ara(oku, 3000, iz)
    assert konum == 1000
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    n_ust = 0
    for k, p in enumerate(iz):
        renk = EDGE[0] if k < 11 else EDGE[1]
        if k < 11:
            n_ust += 1
        ax.scatter(k + 1, p, s=38, color=renk, zorder=3)
    ax.axhline(1000, color=ACCENT, lw=1.2, ls="--", zorder=2)
    ax.text(1.0, 1150, "aranan konum 1000 (sabit çizgi)", va="bottom",
            fontsize=8.8, color=ACCENT, weight="bold")
    ax.set_yscale("log", base=2)
    ax.set_xlabel("sonda sırası (oku çağrısı)", color=INK, fontsize=9.5)
    ax.set_ylabel("sorgulanan indeks (log₂)", color=INK, fontsize=9.5)
    ax.set_title("Üstel arama: önce 1, 2, 4, … (mavi), sonra ikili (yeşil)",
                 color=INK, fontsize=10.0, weight="bold", loc="left")
    ax.set_xlim(0, len(iz) + 4)
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def olcum(path):
    """Şekil 14.8: ortalama sonda sayısı (ölçülen veriden)."""
    random.seed(42)
    ns1 = [1000, 3000, 10000, 30000, 100000, 300000, 1000000]
    ik1, en1 = [], []
    for n in ns1:
        a = sorted(random.sample(range(10 ** 9), n))
        sor = [random.choice(a) for _ in range(2000)]
        ik1.append(sum(ikili(a, x)[1] for x in sor) / len(sor))
        en1.append(sum(enterpolasyon(a, x)[1] for x in sor) / len(sor))
    ns2 = [10, 20, 30, 40, 50, 60]
    ik2, en2 = [], []
    for n in ns2:
        a = [2 ** i for i in range(n)]
        ik2.append(sum(ikili(a, x)[1] for x in a) / n)
        en2.append(sum(enterpolasyon(a, x)[1] for x in a) / n)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.2))
    ax1.plot(ns1, ik1, "o-", color=EDGE[0], lw=2.0, label="ikili arama")
    ax1.plot(ns1, en1, "s-", color=ACCENT, lw=2.0, label="interpolasyon")
    ax1.set_xscale("log")
    ax1.set_xlabel("n (log ölçek)", color=INK, fontsize=9)
    ax1.set_ylabel("ortalama sonda sayısı", color=INK, fontsize=9)
    ax1.set_title("Tekdüzen veri: interpolasyon kazanır",
                  color=INK, fontsize=9.6, weight="bold", loc="left")
    ax1.legend(frameon=False, fontsize=8.6, loc="upper left")
    _ayar(ax1)
    ax2.plot(ns2, ik2, "o-", color=EDGE[0], lw=2.0, label="ikili arama")
    ax2.plot(ns2, en2, "s-", color=ACCENT, lw=2.0, label="interpolasyon")
    ax2.set_xlabel("n (2^i dizisi)", color=INK, fontsize=9)
    ax2.set_ylabel("ortalama sonda sayısı", color=INK, fontsize=9)
    ax2.set_title("Üssel veri: interpolasyon doğrusal büyür",
                  color=INK, fontsize=9.6, weight="bold", loc="left")
    ax2.legend(frameon=False, fontsize=8.6, loc="upper left")
    _ayar(ax2)
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(ikili_aralik, "b14_ikili_aralik.png"),
                   (sinir, "b14_sinir.png"),
                   (monoton, "b14_monoton.png"),
                   (cevap, "b14_cevap.png"),
                   (dondurulmus, "b14_dondurulmus.png"),
                   (matris, "b14_matris.png"),
                   (ustel, "b14_ustel.png"),
                   (olcum, "b14_olcum.png")]:
        print(fn(os.path.join(out, ad)))
