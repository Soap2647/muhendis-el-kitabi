# -*- coding: utf-8 -*-
"""Bölüm 12 — 'Algoritma Analizi' için diyagramlar.

Grafikler gerçek fonksiyonlardan ve bölümdeki deneylerin (bkz. metin)
ölçtüğü değerlerden çizilir. Ölçüm verisi burada sabit olarak yazılmıştır;
değerler, Windows 11 / AMD Ryzen 7 6800H / Python 3.12.10 ve WSL gcc 13.3
koşularından alınmıştır.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
import math
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


# --------------------------------------------------------------------------- #
def buyume(path):
    """Büyüme eğrileri: log n, n, n log n, n^2, 2^n (log ölçekli y)."""
    n = np.arange(2, 31, dtype=float)
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    seri = [
        ("log n", np.log2(n), EDGE[0]),
        ("n", n, EDGE[1]),
        ("n log n", n * np.log2(n), EDGE[2]),
        ("n²", n ** 2, EDGE[3]),
        ("2ⁿ", 2.0 ** n, EDGE[4]),
    ]
    for ad, y, c in seri:
        ax.plot(n, y, color=c, lw=2.0, zorder=3)
        ax.text(30.4, y[-1], ad, color=c, va="center", fontsize=9.5,
                weight="bold")
    ax.set_yscale("log")
    ax.set_ylim(0.5, 1e9)
    ax.set_xlim(1, 31.5)
    ax.set_xlabel("girdi boyutu n", color=INK, fontsize=9.5)
    ax.set_ylabel("işlem sayısı (log ölçek)", color=INK, fontsize=9.5)
    ax.set_title("Büyüme eğrileri: aynı eksende yalnızca eğimin farkı",
                 color=INK, fontsize=10.5, weight="bold", loc="left")
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def asimptotik(path):
    """f(n) = 3n^2 + 5n + 2 : 3n^2 <= f <= 10n^2 for n >= 1."""
    n = np.linspace(0.3, 6, 400)
    f = 3 * n ** 2 + 5 * n + 2
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.fill_between(n, 3 * n ** 2, 10 * n ** 2, color=FILL[0], zorder=1)
    ax.plot(n, 10 * n ** 2, color=EDGE[0], lw=1.4, ls="--", zorder=2)
    ax.plot(n, 3 * n ** 2, color=EDGE[0], lw=1.4, ls=":", zorder=2)
    ax.plot(n, f, color=ACCENT, lw=2.4, zorder=3)
    ax.axvline(1, color=MUTED, lw=1.0, ls="-", zorder=2)
    ax.text(5.9, 10 * 5.9 ** 2 - 4, "10n²  (c₂ = 10)", color=EDGE[0],
            ha="right", fontsize=9.2, weight="bold")
    ax.text(5.9, 3 * 5.9 ** 2 - 12, "3n²  (c₁ = 3)", color=EDGE[0],
            ha="right", fontsize=9.2, weight="bold")
    ax.text(5.9, f[-1] + 6, "f(n) = 3n² + 5n + 2", color=ACCENT,
            ha="right", fontsize=9.6, weight="bold")
    ax.text(1.12, 210, "n₀ = 1", color=INK, fontsize=9.2)
    ax.text(0.4, 300,"c₁·n² ≤ f(n) ≤ c₂·n²\nbu bant n ≥ n₀ için geçerli",
            color=INK, fontsize=9.0, ha="left")
    ax.set_xlim(0.3, 6)
    ax.set_ylim(0, 380)
    ax.set_xlabel("n", color=INK, fontsize=9.5)
    ax.set_ylabel("değer", color=INK, fontsize=9.5)
    ax.set_title("Θ(n²): f, iki parabolün arasında kalır",
                 color=INK, fontsize=10.5, weight="bold", loc="left")
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def agac(path):
    """T(n)=2T(n/2)+n, n=8: her seviye toplam işi n."""
    fig, ax = plt.subplots(figsize=(10.4, 4.9))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6)
    ax.axis("off")
    seviyeler = [
        (5.0, [("n", 5.2)]),
        (3.8, [("n/2", 2.6), ("n/2", 7.6)]),
        (2.6, [("n/4", 1.4), ("n/4", 4.0), ("n/4", 6.4), ("n/4", 9.0)]),
        (1.4, [("1", 0.6 + 1.25 * i) for i in range(8)]),
    ]
    for k, (y, nodes) in enumerate(seviyeler):
        for metin, x in nodes:
            c = EDGE[k % 5]
            ax.add_patch(Circle((x, y), 0.24, facecolor=FILL[k % 5],
                                edgecolor=c, lw=1.3, zorder=3))
            ax.text(x, y, metin, ha="center", va="center", fontsize=8.6,
                    color=INK, weight="bold", zorder=4)
    # kenarlar
    for k in range(len(seviyeler) - 1):
        y1, n1 = seviyeler[k]
        y2, n2 = seviyeler[k + 1]
        for i, (_, x1) in enumerate(n1):
            for j in (2 * i, 2 * i + 1):
                x2 = n2[j][1]
                ax.plot([x1, x2], [y1 - 0.24, y2 + 0.24], color=MUTED,
                        lw=1.1, zorder=1)
    etiketler = ["seviye 0: 1 düğüm, iş n",
                 "seviye 1: 2 düğüm, iş 2·(n/2) = n",
                 "seviye 2: 4 düğüm, iş 4·(n/4) = n",
                 "seviye 3: 8 yaprak, iş 8·1 = n"]
    for (y, _), e in zip(seviyeler, etiketler):
        ax.text(14.9, y, e, ha="right", va="center", fontsize=8.6,
                color=INK)
    ax.text(0.2, 0.35,
            "log₂ 8 = 3, yani 4 seviye; toplam n·(log₂ n + 1) = 32 (n=8, T(1)=1)",
            fontsize=8.6, color=ACCENT, weight="bold")
    ax.text(0.2, 5.9, "T(n) = 2T(n/2) + n  özyineleme ağacı",
            fontsize=10.2, color=INK, weight="bold")
    return _save(fig, path)


def master(path):
    """Master Teoremi üç durum: f(n) ile n^c karşılaştırması (log-log)."""
    n = np.logspace(0.3, 3, 300)
    c = 1.0
    paneller = [
        ("Durum 1: f(n) < n^c", n ** 0.5, "f = O(n^(c−ε))",
         "T(n) = Θ(n^c)  →  Θ(n)"),
        ("Durum 2: f(n) = n^c", n * 1.0, "f = Θ(n^c log^k n), k = 0",
         "T(n) = Θ(n^c log n)  →  Θ(n log n)"),
        ("Durum 3: f(n) > n^c", n ** 2, "f = Ω(n^(c+ε)) ve düzenlilik",
         "T(n) = Θ(f(n))  →  Θ(n²)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.9), sharey=True)
    for ax, (baslik, f, kosul, sonuc) in zip(axes, paneller):
        ax.plot(n, n, color=MUTED, lw=1.6, ls="--", zorder=2,
                label="n^c (c = 1)")
        ax.plot(n, f, color=ACCENT, lw=2.2, zorder=3, label="f(n)")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(baslik, color=INK, fontsize=9.6, weight="bold",
                     loc="left")
        ax.text(1.6, 5e5, kosul, fontsize=8.2, color=INK, ha="left")
        ax.text(1.6, 1.5e5, sonuc, fontsize=8.2, color=ACCENT,
                weight="bold", ha="left")
        ax.set_xlim(1.5, 1000)
        ax.set_ylim(0.1, 1e6)
        ax.set_xlabel("n", color=INK, fontsize=9)
        _ayar(ax)
    axes[0].set_ylabel("iş (log ölçek)", color=INK, fontsize=9)
    fig.suptitle("a = 2, b = 2, c = 1: kırmızı f(n), gri kesik n^c",
                 color=INK, fontsize=10.2, weight="bold", x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, path)


def loglog(path):
    """Gerçek ölçüm (zaman.py çıktısı) ve log-log eğimleri."""
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    # O(n) toplam (Python döngüsü), ms
    n1 = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288,
          1048576]
    t1 = [0.0991, 0.1932, 0.3845, 0.7876, 1.6559, 3.2288, 6.5193,
          13.1143, 25.6688]
    # O(n log n) sorted, ms
    n2 = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288,
          1048576]
    t2 = [0.2573, 0.5814, 1.3184, 2.9326, 6.6666, 15.0228, 34.8705,
          84.0846, 199.1795]
    # O(n^2) çift karşılaştırma, ms
    n3 = [250, 500, 1000, 2000]
    t3 = [2.1329, 9.3036, 38.3996, 155.3930]
    # O(1) sözlük, 100000 arama, ms
    n4 = [1024, 4096, 16384, 65536, 262144, 1048576]
    t4 = [3.7525, 3.9102, 5.3402, 7.8214, 22.7870, 33.1729]

    ax.loglog(n1, t1, "o-", color=EDGE[0], lw=1.8, ms=4.5,
              label="O(n) toplam  (eğim 1,01)")
    ax.loglog(n2, t2, "s-", color=EDGE[2], lw=1.8, ms=4.5,
              label="O(n log n) sorted  (eğim 1,20)")
    ax.loglog(n3, t3, "^-", color=ACCENT, lw=1.8, ms=5,
              label="O(n²) çift  (eğim 2,06)")
    ax.loglog(n4, t4, "D--", color=EDGE[4], lw=1.4, ms=4,
              label="O(1) sözlük araması  (eğim 0,34)")
    ax.set_xlabel("n (log ölçek)", color=INK, fontsize=9.5)
    ax.set_ylabel("en iyi süre, ms (log ölçek)", color=INK, fontsize=9.5)
    ax.set_title("Dört işlem, dört eğim; O(1)'in eğimi neden sıfır değil?",
                 color=INK, fontsize=10.2, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=8.4, loc="lower right")
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def amortize(path):
    """Dinamik dizi: +1 büyüme ile ×2 büyümenin n ekleme başına maliyeti."""
    def toplam_plus1(n):
        kopya = sum(range(n))            # her eklemede tüm eleman kopyalanır
        return (n + kopya) / n

    def toplam_x2(n):
        kopya, kap, boy = 0, 1, 0
        for _ in range(n):
            if boy == kap:
                kopya += boy
                kap *= 2
            boy += 1
        return (n + kopya) / n

    ns = np.arange(1, 1025)
    p1 = np.array([toplam_plus1(int(k)) for k in ns])
    p2 = np.array([toplam_x2(int(k)) for k in ns])
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.plot(ns, p1, color=ACCENT, lw=2.0, label="kapasite +1 (her seferinde kopya)")
    ax.plot(ns, p2, color=EDGE[1], lw=2.0, label="kapasite ×2 (amortize O(1))")
    ax.set_xscale("log")
    ax.set_xlabel("ekleme sayısı n (log ölçek)", color=INK, fontsize=9.5)
    ax.set_ylabel("ekleme başına ortalama iş", color=INK, fontsize=9.5)
    ax.set_title("Toplam iş / n: ×2 büyümede sabit kalır",
                 color=INK, fontsize=10.4, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=8.8, loc="upper left")
    ax.set_yscale("log")
    ax.set_ylim(1, 1000)
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def sabit_carpan(path):
    """100n ile n^2: n = 100 kesişimi; büyük n'de karesel daha kötü."""
    n = np.linspace(1, 300, 400)
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.plot(n, 100 * n, color=EDGE[0], lw=2.0, label="100n  (büyük sabit)")
    ax.plot(n, n ** 2, color=ACCENT, lw=2.0, label="n²  (küçük sabit)")
    ax.axvline(100, color=MUTED, lw=1.0, ls=":")
    ax.text(106, 2000, "n = 100'de kesişim", fontsize=8.8, color=INK)
    ax.text(120, 62000, "n > 100 ise n² daha pahalı", fontsize=8.8,
            color=ACCENT, weight="bold")
    ax.set_xlabel("n", color=INK, fontsize=9.5)
    ax.set_ylabel("işlem sayısı (doğrusal ölçek)", color=INK, fontsize=9.5)
    ax.set_title("Sabit çarpan, küçük n'de belirleyicidir",
                 color=INK, fontsize=10.4, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=8.8, loc="upper left")
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


def onbellek(path):
    """Aynı O(n) toplam: sıralı ve rastgele erişim (C, 64 MB dizi)."""
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    etiket = ["sıralı erişim  a[i]", "rastgele erişim  a[p[i]]"]
    deger = [3.17, 102.56]
    renk = [EDGE[0], ACCENT]
    y = [1, 0]
    ax.barh(y, deger, color=renk, height=0.5, zorder=3)
    for yi, d in zip(y, deger):
        ax.text(d + 2, yi, f"{d:.2f} ms", va="center", fontsize=9,
                color=INK, weight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(etiket, fontsize=9, color=INK)
    ax.set_xlim(0, 125)
    ax.set_xlabel("en iyi süre (ms), 16.7 milyon eleman", color=INK,
                  fontsize=9)
    ax.set_title("Aynı O(n), farklı önbellek davranışı (≈32 kat)",
                 color=INK, fontsize=10.2, weight="bold", loc="left")
    _ayar(ax)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _save(fig, path)


def heapify(path):
    """Heapify: yükseklik h düğümlerinin toplam takas üst sınırı h·2^(H-h)."""
    H = 10
    hs = np.arange(0, H + 1)
    katki = hs * 2.0 ** (H - hs)
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.bar(hs, katki, color=[FILL[1] if h == 0 else EDGE[1] for h in hs],
           edgecolor=EDGE[1], lw=0.8, zorder=3, width=0.7)
    for h, k in zip(hs, katki):
        if k > 0:
            ax.text(h, k + 12, f"{int(k)}", ha="center", fontsize=8.4,
                    color=INK)
    ax.set_xticks(hs)
    ax.set_xlabel("düğümün yüksekliği h", color=INK, fontsize=9.5)
    ax.set_ylabel("en kötü takas üst sınırı", color=INK, fontsize=9.5)
    toplam = int(katki.sum())
    n = 2 ** (H + 1) - 1
    ax.set_title(f"n = {n}: toplam {toplam} ≈ n (her seviye ayrı ayrı küçülür)",
                 color=INK, fontsize=10.2, weight="bold", loc="left")
    ax.set_ylim(0, katki.max() * 1.15)
    _ayar(ax)
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(buyume, "b12_buyume.png"),
                   (asimptotik, "b12_asimptotik.png"),
                   (agac, "b12_agac.png"),
                   (master, "b12_master.png"),
                   (loglog, "b12_loglog.png"),
                   (amortize, "b12_amortize.png"),
                   (sabit_carpan, "b12_sabit_carpan.png"),
                   (onbellek, "b12_onbellek.png"),
                   (heapify, "b12_heapify.png")]:
        print(fn(os.path.join(out, ad)))
