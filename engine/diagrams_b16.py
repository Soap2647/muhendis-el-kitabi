# -*- coding: utf-8 -*-
"""Bolum 16 - 'Dynamic Programming' diyagramlari.

Tablolardaki sayilar, bolumdeki programlarla ayni algoritmadan hesaplanir
(ornek degerler: 0/1 sirt cantasi W=7, LCS 'ABCBDAB'/'BDCABA', edit
'kitten'/'sitting', matris zinciri p=[30,35,15,5,10,20,25]).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import bisect
import os

from diagrams import (_arrow, _save, ACCENT, INK, MUTED,
                      RULE, FILL, EDGE)


def _hucre(ax, x, y, w, h, metin, fill="white", edge=RULE, tcol=INK,
           bold=False, fs=9.2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                           lw=1.0, zorder=2))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=fs, color=tcol, zorder=3,
            weight="bold" if bold else "normal")


# ----- algoritmalar (kitaptaki programlarla ayni mantik) -----------------
def fib_naif_cagri(n, sayac):
    sayac[0] += 1
    if n < 2:
        return n
    return fib_naif_cagri(n - 1, sayac) + fib_naif_cagri(n - 2, sayac)


def tablo_01(agirlik, deger, W):
    n = len(agirlik)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = agirlik[i - 1], deger[i - 1]
        for c in range(W + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c and dp[i - 1][c - w] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - w] + v
    return dp


def knap_yol(dp, agirlik, W):
    # Geri izleme: (i, c) hucrelerinin sirasi
    yol, c = [(len(agirlik), W)], W
    for i in range(len(agirlik), 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            c -= agirlik[i - 1]
        yol.append((i - 1, c))
    return yol


def lcs_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def lcs_yol(dp, a, b):
    i, j, yol = len(a), len(b), [(len(a), len(b))]
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            i, j = i - 1, j - 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
        yol.append((i, j))
    return yol


def edit_tablo(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j],
                                   dp[i][j - 1])
    return dp


def edit_yol(dp, a, b):
    i, j, yol = len(a), len(b), [(len(a), len(b))]
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            i -= 1
        else:
            j -= 1
        yol.append((i, j))
    return yol


def matris_m(p):
    n = len(p) - 1
    m = [[0] * n for _ in range(n)]
    for uz in range(2, n + 1):
        for i in range(n - uz + 1):
            j = i + uz - 1
            m[i][j] = min(m[i][k] + m[k + 1][j] + p[i] * p[k + 1] * p[j + 1]
                          for k in range(i, j))
    return m


# ----- sekiller ------------------------------------------------------------
def fib_agac(path):
    """fib(5) yigin agaci; tekrar eden dugumler kirmizi."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(-1.0, 6.4)
    ax.axis("off")
    yaprak = {"x": 0}

    def yerlestir(n, d):
        # Dugumun (x, y, n, cocuklar) bilgisini dondurur
        if n < 2:
            x = yaprak["x"] + 0.6
            yaprak["x"] += 1.25
            cocuk = []
        else:
            cocuk = [yerlestir(n - 1, d + 1), yerlestir(n - 2, d + 1)]
            x = (cocuk[0][0] + cocuk[1][0]) / 2
        return (x, 5.9 - d * 1.3, n, cocuk)

    def ciz(dugum):
        x, y, n, cocuk = dugum
        for c in cocuk:
            _arrow(ax, x, y - 0.25, c[0], c[1] + 0.27, col=MUTED, lw=1.0)
        tekrarli = n in (2, 3)
        ax.add_patch(Circle((x, y), 0.27,
                            facecolor=FILL[3] if tekrarli else FILL[0],
                            edgecolor=ACCENT if tekrarli else EDGE[0],
                            lw=1.3, zorder=3))
        ax.text(x, y, f"{n}", ha="center", va="center", fontsize=9.5,
                color=INK, weight="bold", zorder=4)
        for c in cocuk:
            ciz(c)

    kok = yerlestir(5, 0)
    ciz(kok)
    ax.text(0.2, -0.75, "Düğümdeki sayı n'dir (fib(n)). Kırmızılar birden "
            "çok kez hesaplanır: fib(3) 2 kez, fib(2) 3 kez.",
            fontsize=8.6, color=INK, ha="left")
    return _save(fig, path)


def fib_dag(path):
    """Memo'nun alt problem DAG'ı: her düğüm tek kez hesaplanır."""
    fig, ax = plt.subplots(figsize=(9.6, 3.7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    x0, dx, y = 1.0, 2.3, 3.0
    for n in range(6):
        x = x0 + n * dx
        ax.add_patch(Circle((x, y), 0.45, facecolor=FILL[1],
                            edgecolor=EDGE[1], lw=1.4, zorder=3))
        ax.text(x, y, f"fib({n})", ha="center", va="center", fontsize=8.6,
                color=INK, weight="bold", zorder=4)
    for n in range(2, 6):
        x = x0 + n * dx
        _arrow(ax, x - 0.42, y + 0.2, x - dx + 0.42, y + 0.2,
               col=EDGE[0], rad=-0.45, lw=1.3)
        _arrow(ax, x - 0.2, y - 0.4, x - 2 * dx + 0.3, y - 0.4,
               col=ACCENT, rad=0.45, lw=1.3)
    ax.text(0.4, 5.2, "Mavi ok: fib(n) -> fib(n-1). Kırmızı ok: fib(n) -> "
            "fib(n-2).", fontsize=9.0, color=INK, ha="left")
    ax.text(0.4, 0.6, "Her düğüm bir kez hesaplanır: n = 5 için 6 "
            "alt problem, 8 bağımlılık kenarı.", fontsize=9.0,
            color=INK, ha="left")
    return _save(fig, path)


def olcum(path):
    """Naif çağrı sayısı ile memo hesap sayısı, log ölçek."""
    ns = list(range(1, 26))
    naif = []
    for n in ns:
        sayac = [0]
        fib_naif_cagri(n, sayac)
        naif.append(sayac[0])
    memo = [n + 1 for n in ns]
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    ax.semilogy(ns, naif, "o-", color=ACCENT, lw=1.9, ms=4.2,
                label="naif özyineleme (çağrı sayısı)")
    ax.semilogy(ns, memo, "s-", color=EDGE[0], lw=1.9, ms=4.2,
                label="memo (gerçek hesap sayısı)")
    ax.set_xlabel("n", color=INK, fontsize=9)
    ax.set_ylabel("işlem sayısı (log)", color=INK, fontsize=9)
    ax.set_title("Fibonacci: naif üstel, memo doğrusal büyür",
                 color=INK, fontsize=9.6, weight="bold", loc="left")
    ax.grid(True, color=RULE, lw=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8.6, loc="upper left")
    fig.tight_layout()
    return _save(fig, path)


def knap(path):
    agirlik, deger, W = [1, 3, 4, 5], [1, 4, 5, 7], 7
    dp = tablo_01(agirlik, deger, W)
    yol = set(knap_yol(dp, agirlik, W))
    secilen = {(i, c) for (i, c) in yol
               if i > 0 and dp[i][c] != dp[i - 1][c]}
    fig, ax = plt.subplots(figsize=(9.6, 4.3))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.6, 6.1)
    ax.axis("off")
    x0, y0, w, h = 2.4, 0.4, 1.05, 0.7
    for c in range(W + 1):
        ax.text(x0 + c * w + w / 2, 5.45, f"c={c}", ha="center",
                fontsize=8.4, color=INK)
    for i in range(len(agirlik) + 1):
        y = y0 + (len(agirlik) - i) * h
        lab = "0 eşya" if i == 0 else f"ilk {i}"
        ax.text(x0 - 0.12, y + h / 2, lab, ha="right", va="center",
                fontsize=8.4, color=INK)
        for c in range(W + 1):
            fill = "white"
            if (i, c) in secilen:
                fill = FILL[3]
            elif (i, c) in yol:
                fill = FILL[1]
            _hucre(ax, x0 + c * w, y, w, h, str(dp[i][c]), fill=fill,
                   edge=ACCENT if (i, c) in secilen else RULE,
                   bold=(i, c) in secilen)
    ax.text(0.1, -0.4, "Bordo: eşya alındı (dp[i][c] != dp[i-1][c]). "
            "Açık yeşil: geri izleme yolu.", fontsize=8.4, color=INK,
            ha="left")
    return _save(fig, path)


def _izgara(ax, a, b, dp, yol, x0, y0, w, h, ustyazi):
    for j, ch in enumerate(b):
        ax.text(x0 + (j + 1) * w + w / 2, 5.6, ch, ha="center",
                fontsize=9.2, color=INK, weight="bold")
    for i in range(len(a) + 1):
        y = y0 + (len(a) - i) * h
        if i > 0:
            ax.text(x0 + w / 2 - 0.85, y + h / 2, a[i - 1], ha="center",
                    va="center", fontsize=9.2, color=INK, weight="bold")
        for j in range(len(b) + 1):
            fill = "white"
            if (i, j) in yol:
                fill = FILL[3] if (i, j) == (len(a), len(b)) else FILL[1]
            _hucre(ax, x0 + j * w, y, w, h, str(dp[i][j]), fill=fill,
                   edge=ACCENT if (i, j) in yol else RULE,
                   bold=(i, j) in yol)
    ax.text(0.2, -0.45, ustyazi, fontsize=8.6, color=INK, ha="left")


def lcs(path):
    a, b = "ABCBDAB", "BDCABA"
    dp = lcs_tablo(a, b)
    yol = set(lcs_yol(dp, a, b))
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.7, 6.2)
    ax.axis("off")
    _izgara(ax, a, b, dp, yol, 3.2, 0.2, 1.0, 0.62,
            "Yeşil yol: geri izleme (LCS = BCBA). Eşleşen harfte "
            "köşegen adım atılır.")
    return _save(fig, path)


def edit(path):
    a, b = "kitten", "sitting"
    dp = edit_tablo(a, b)
    yol = set(edit_yol(dp, a, b))
    fig, ax = plt.subplots(figsize=(9.6, 4.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.7, 6.2)
    ax.axis("off")
    _izgara(ax, a, b, dp, yol, 3.2, 0.2, 1.0, 0.6,
            "Yeşil yol: kitten -> sitting, maliyet 3 (k->s, e->i, ekle g).")
    return _save(fig, path)


def lis_sabir(path):
    """LIS n log n: her adimda kuyruk dizisi."""
    a = [3, 1, 4, 1, 5, 9, 2, 6]
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    ax.text(0.2, 9.1, "x", fontsize=9, color=INK, weight="bold")
    ax.text(1.4, 9.1, "kuyruk[k]: k+1 uzunlukta en küçük son eleman",
            fontsize=9, color=INK, weight="bold")
    kuyruk = []
    for satir, x in enumerate(a):
        y = 8.2 - satir * 0.98
        ax.text(0.5, y + 0.31, f"{x}", ha="center", fontsize=10,
                color=INK, weight="bold")
        pos = bisect.bisect_left(kuyruk, x)
        if pos == len(kuyruk):
            kuyruk.append(x)
            tip = "sona eklendi"
        else:
            kuyruk[pos] = x
            tip = "değiştirildi"
        for idx, deger in enumerate(kuyruk):
            vurgu = idx == pos
            _hucre(ax, 1.4 + idx * 1.0, y, 0.9, 0.62, str(deger),
                   fill=ACCENT if vurgu else "white",
                   edge=ACCENT if vurgu else RULE,
                   tcol="white" if vurgu else INK, bold=vurgu)
        ax.text(1.4 + len(kuyruk) * 1.0 + 0.25, y + 0.31, tip, fontsize=8.6,
                color=MUTED, va="center")
    return _save(fig, path)


def matris(path):
    """Matris zinciri: m[i][j] tablosu; köşegenler uzunluğa göre."""
    p = [30, 35, 15, 5, 10, 20, 25]
    m = matris_m(p)
    n = len(p) - 1
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.7, 6.4)
    ax.axis("off")
    x0, y0, w, h = 2.4, 0.4, 1.35, 0.72
    for j in range(n):
        ax.text(x0 + j * w + w / 2, 5.9, f"A{j + 1}", ha="center",
                fontsize=9, color=INK, weight="bold")
    for i in range(n):
        y = y0 + (n - 1 - i) * h
        ax.text(x0 - 0.2, y + h / 2, f"A{i + 1}", ha="right",
                va="center", fontsize=9, color=INK, weight="bold")
        for j in range(n):
            x = x0 + j * w
            if j < i:
                _hucre(ax, x, y, w, h, "", fill="#FAFAF8", edge=RULE)
                continue
            uz = j - i + 1
            if uz == n:
                fill = FILL[0]
            elif uz % 2 == 0:
                fill = FILL[1]
            else:
                fill = FILL[2]
            kok = (i, j) == (0, n - 1)
            _hucre(ax, x, y, w, h, str(m[i][j]), fill=fill,
                   edge=ACCENT if kok else RULE, bold=kok)
    ax.text(0.2, -0.45, "Köşegen: tek matris (0). Renkler zincir uzunluğuna "
            "göre; kırmızı çerçeve: tüm zincir.", fontsize=8.6, color=INK,
            ha="left")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(fib_agac, "b16_fib_agac.png"),
                   (fib_dag, "b16_fib_dag.png"),
                   (olcum, "b16_olcum.png"),
                   (knap, "b16_knap_tablo.png"),
                   (lcs, "b16_lcs_tablo.png"),
                   (edit, "b16_edit_tablo.png"),
                   (lis_sabir, "b16_lis_sabir.png"),
                   (matris, "b16_matris_aralik.png")]:
        print(fn(os.path.join(out, ad)))
