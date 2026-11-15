# -*- coding: utf-8 -*-
"""Bölüm 15 — 'Recursion & Backtracking' için diyagramlar.

Ağaç şekilleri, bölümdeki algoritmaların ürettiği gerçek düğümlerden
çizilir; ölçüm grafikleri bölümdeki programların çıktılarıdır.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
from collections import Counter

from diagrams import (_box, _arrow, _save, ACCENT, INK, MUTED,
                      RULE, FILL, EDGE)


def _ayar(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(True, axis="y", color=RULE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)


# ----- ağaç yerleşimi ------------------------------------------------------
class Dugum:
    def __init__(self, etiket, cocuklar=None, stil="normal"):
        self.etiket = etiket
        self.cocuklar = cocuklar or []
        self.stil = stil
        self.budanan = 0
        self.x = 0.0
        self.y = 0.0


def _tum(kok):
    liste = [kok]
    for c in kok.cocuklar:
        liste.extend(_tum(c))
    return liste


def _yerlestir(kok, genislik, yukseklik):
    """Yapraklar soldan saga esit aralikla; ic dugum, cocuklarinin
    ortalamasina. Derinlik yukaridan asagiya."""
    yapraklar = []
    maks_seviye = [0]

    def gez(d, seviye):
        maks_seviye[0] = max(maks_seviye[0], seviye)
        d.y = seviye
        if not d.cocuklar:
            yapraklar.append(d)
            d.x = float(len(yapraklar) - 1)
        else:
            for c in d.cocuklar:
                gez(c, seviye + 1)
            d.x = sum(c.x for c in d.cocuklar) / len(d.cocuklar)

    gez(kok, 0)
    n = max(len(yapraklar) - 1, 1)
    maks = maks_seviye[0] or 1
    for d in _tum(kok):
        d.x = genislik * d.x / n
        d.y = yukseklik * (1 - d.y / maks)
    return yapraklar


def _kenar(ax, a, b, kesik=False):
    if kesik:
        ax.plot([a.x, b.x], [a.y, b.y], color=MUTED, lw=1.0,
                linestyle=(0, (3, 2)), zorder=1)
    else:
        ax.plot([a.x, b.x], [a.y, b.y], color=EDGE[0], lw=1.2, zorder=1)


def _dugum_ciz(ax, d, w=0.9, h=0.5, fs=8.2):
    renk = {"normal": (FILL[0], EDGE[0]),
            "cozum": (FILL[1], EDGE[1]),
            "tekrar": (FILL[2], EDGE[2]),
            "çıkmaz": (FILL[3], EDGE[3])}
    fill, edge = renk.get(d.stil, renk["normal"])
    ax.add_patch(Rectangle((d.x - w / 2, d.y - h / 2), w, h,
                           facecolor=fill, edgecolor=edge, lw=1.0,
                           zorder=2))
    ax.text(d.x, d.y, d.etiket, ha="center", va="center", fontsize=fs,
            color=INK, zorder=3)


# ----- 1. Cagri yigini cerceveleri ----------------------------------------
def cagri_yigini(path):
    """Şekil 15.1: faktoriyel(4) çağrı yığını. Ofsetler, bölümdeki
    cerceve.c çıktısındaki değerlerdir (her çerçeve 80 bayt)."""
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    cerceveler = [
        ("main()", "dönüş: işletim sistemi", FILL[4], EDGE[4], 7.4,
         None),
        ("faktoriyel(4)", "n = 4   dönüş: main", FILL[0], EDGE[0], 6.0,
         "0 bayt"),
        ("faktoriyel(3)", "n = 3   dönüş: faktoriyel(4)", FILL[0],
         EDGE[0], 4.6, "80 bayt"),
        ("faktoriyel(2)", "n = 2   dönüş: faktoriyel(3)", FILL[0],
         EDGE[0], 3.2, "160 bayt"),
        ("faktoriyel(1)", "n = 1   dönüş: faktoriyel(2)", FILL[3],
         EDGE[3], 1.8, "240 bayt"),
    ]
    for ad, sub, fill, edge, y, ofs in cerceveler:
        ax.add_patch(Rectangle((1.0, y), 6.6, 1.1, facecolor=fill,
                               edgecolor=edge, lw=1.2))
        ax.text(1.3, y + 0.78, ad, fontsize=9.4, weight="bold",
                color=edge, va="center")
        ax.text(1.3, y + 0.32, sub, fontsize=8.0, color=INK,
                va="center")
        if ofs:
            ax.text(7.2, y + 0.55, ofs, fontsize=8.2, color=MUTED,
                    va="center", ha="right")
    ax.text(0.2, 8.6, "Yüksek adres (yığın tabanı)", fontsize=8.4,
            color=MUTED, style="italic")
    ax.text(0.2, 1.2, "Düşük adres (yığın tepesi, sp)", fontsize=8.4,
            color=MUTED, style="italic")
    _arrow(ax, 8.6, 7.2, 8.6, 1.6, col=MUTED, lw=1.2)
    ax.text(8.8, 4.4, "çağrılar\naşağı\nbüyür", fontsize=8.2,
            color=MUTED, va="center", ha="left")
    return _save(fig, path)


# ----- 2. Fibonacci ozyineleme agaci --------------------------------------
def _fib_kok(n):
    if n < 2:
        return Dugum("fib(%d)=%d" % (n, n))
    return Dugum("fib(%d)" % n, [_fib_kok(n - 1), _fib_kok(n - 2)])


def fib_agac(path):
    """Şekil 15.2: fib(5) özyineleme ağacı; tekrar eden düğümler sarı."""
    kok = _fib_kok(5)
    dugumler = _tum(kok)
    sayim = Counter(d.etiket for d in dugumler)
    for d in dugumler:
        if sayim[d.etiket] > 1:
            d.stil = "tekrar"
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    _yerlestir(kok, 9.0, 4.2)
    for d in dugumler:
        for c in d.cocuklar:
            _kenar(ax, d, c)
    for d in dugumler:
        _dugum_ciz(ax, d, w=1.12, h=0.42, fs=7.4)
    ax.set_xlim(-0.7, 9.7)
    ax.set_ylim(-0.4, 5.0)
    ax.axis("off")
    ax.text(-0.6, 4.95, "Sarı düğümler tekrar eden çağrılardır: "
            "fib(3) 2 kez, fib(2) 3 kez, fib(1) 5 kez, fib(0) 3 kez.\n"
            "Toplam çağrı: 15.", fontsize=8.2, color=INK, va="top")
    return _save(fig, path)


# ----- 3. Alt kume durum uzayi agaci --------------------------------------
def alt_kume_agac(path):
    """Şekil 15.3: {1, 2, 3} için alt küme durum uzayı."""
    def kur(i, secili):
        if i == 3:
            etiket = "{" + ", ".join(map(str, secili)) + "}"
            return Dugum(etiket, stil="cozum")
        atla = kur(i + 1, secili)
        sec = kur(i + 1, secili + [i + 1])
        return Dugum("a%d" % (i + 1), [atla, sec])

    kok = kur(0, [])
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    _yerlestir(kok, 9.0, 4.0)
    for d in _tum(kok):
        for c in d.cocuklar:
            _kenar(ax, d, c)
    for d in _tum(kok):
        _dugum_ciz(ax, d, w=0.84, h=0.42, fs=7.6)
    ax.set_xlim(-0.6, 9.6)
    ax.set_ylim(-0.4, 4.9)
    ax.axis("off")
    ax.text(-0.5, 4.85, "Her düzey bir elemanla ilgili karar: a_i "
            "seçilir (sağ dal) ya da atlanır (sol dal).",
            fontsize=8.2, color=INK, va="top")
    return _save(fig, path)


# ----- 4. Tekrarli permutasyon agaci --------------------------------------
def permutasyon_agac(path):
    """Şekil 15.4: [1, 1, 2] için tekrarsız permütasyon ağacı.
    Kesik kutu: tekrar nedeniyle atlanan dal."""
    a = [1, 1, 2]

    def kur(yol, kullanildi):
        if len(yol) == len(a):
            return Dugum(" ".join(map(str, yol)), stil="cozum")
        cocuklar = []
        for i in range(len(a)):
            if kullanildi[i]:
                continue
            if i > 0 and a[i] == a[i - 1] and not kullanildi[i - 1]:
                cocuklar.append(Dugum("atla (i=%d)" % i, stil="çıkmaz"))
                continue
            kullanildi[i] = True
            cocuklar.append(kur(yol + [a[i]], kullanildi))
            kullanildi[i] = False
        return Dugum(" ".join(map(str, yol)) or "kök", cocuklar)

    kok = kur([], [False] * len(a))
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    _yerlestir(kok, 9.0, 4.0)
    for d in _tum(kok):
        for c in d.cocuklar:
            _kenar(ax, d, c, kesik=(c.stil == "çıkmaz"))
    for d in _tum(kok):
        _dugum_ciz(ax, d, w=1.18, h=0.42, fs=7.6)
    ax.set_xlim(-0.8, 9.8)
    ax.set_ylim(-0.4, 4.9)
    ax.axis("off")
    ax.text(-0.7, 4.85, "Eleman sıralı; önceki kopya kullanılmadan "
            "aynı değer tekrar seçilmez.", fontsize=8.2, color=INK,
            va="top")
    return _save(fig, path)


# ----- 5. Budanmis N-Queens agaci (n = 4) ----------------------------------
def _guvenli(yerler, satir, sutun):
    for r, c in enumerate(yerler):
        if c == sutun or abs(c - sutun) == satir - r:
            return False
    return True


def _nq_kok(n):
    """Yalnizca ziyaret edilen dugumler. Her dugumun 'budanan' alani,
    o satirda guvensiz olup hic ziyaret edilmeyen sutun sayisidir."""
    yerler = []

    def kur(satir):
        if satir == n:
            return Dugum("çözüm " + "".join(str(c + 1) for c in yerler),
                         stil="cozum")
        cocuklar = []
        budanan = 0
        for s in range(n):
            if _guvenli(yerler, satir, s):
                yerler.append(s)
                cocuklar.append(kur(satir + 1))
                yerler.pop()
            else:
                budanan += 1
        if cocuklar:
            d = Dugum("", cocuklar)
        else:
            d = Dugum("çıkmaz", stil="çıkmaz")
        d.budanan = budanan
        return d

    kok = kur(0)
    return kok, sum(d.budanan for d in _tum(kok))


def budama_agac(path):
    """Şekil 15.5: N = 4 için budanmış N-Queens ağacı. Kesik çizgi ve
    x işareti, o düğümde budanan (ziyaret edilmeyen) sütunlardır."""
    kok, budanan = _nq_kok(4)
    kok.etiket = "kök"
    dugumler = _tum(kok)
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    _yerlestir(kok, 9.0, 4.2)
    for d in dugumler:
        for c in d.cocuklar:
            _kenar(ax, d, c)
        k_say = d.budanan
        for k in range(k_say):
            dx = -0.5 + 1.0 * k / max(k_say - 1, 1)
            tx, ty = d.x + dx, d.y - 0.55
            ax.plot([d.x, tx], [d.y, ty], color=MUTED, lw=0.9,
                    linestyle=(0, (3, 2)), zorder=1)
            ax.text(tx, ty, "x", ha="center", va="center", fontsize=8,
                    color=MUTED, zorder=3)
    for d in dugumler:
        if d.etiket == "":
            ax.add_patch(plt.Circle((d.x, d.y), 0.07, color=EDGE[0],
                                    zorder=3))
        elif d.stil == "cozum":
            _dugum_ciz(ax, d, w=1.3, h=0.4, fs=6.8)
        else:
            _dugum_ciz(ax, d, w=0.9, h=0.4, fs=6.8)
    ax.set_xlim(-0.8, 9.8)
    ax.set_ylim(-0.6, 5.0)
    ax.axis("off")
    ax.text(-0.7, 4.95, "Satır satır ilerle; güvensiz sütunlar (x) "
            "budanır. Ziyaret edilen düğüm: %d." % len(dugumler),
            fontsize=8.2, color=INK, va="top")
    return _save(fig, path)


# ----- 6. 8-vezir cozum tahtasi ------------------------------------------
def vezir8(path):
    """Şekil 15.6: [0, 4, 7, 5, 2, 6, 1, 3] (ilk çözüm)."""
    yerler = [0, 4, 7, 5, 2, 6, 1, 3]
    n = 8
    fig, ax = plt.subplots(figsize=(5.2, 5.4))
    for r in range(n):
        for c in range(n):
            renk = FILL[0] if (r + c) % 2 == 0 else "#ffffff"
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=renk,
                                   edgecolor=RULE, lw=0.8))
    for r, c in enumerate(yerler):
        ax.add_patch(plt.Circle((c + 0.5, r + 0.5), 0.33,
                                color=ACCENT, zorder=3))
    ax.set_xlim(0, n)
    ax.set_ylim(n, 0)
    ax.set_aspect("equal")
    ax.set_xticks([i + 0.5 for i in range(n)])
    ax.set_xticklabels(["%d" % (i + 1) for i in range(n)], fontsize=8,
                       color=MUTED)
    ax.set_yticks([i + 0.5 for i in range(n)])
    ax.set_yticklabels(["%d" % (i + 1) for i in range(n)], fontsize=8,
                       color=MUTED)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return _save(fig, path)


# ----- 7. Budamali / budamasiz dugum sayisi -------------------------------
def budama_olcum(path):
    """Şekil 15.7: N-Queens düğüm sayısı (vezir.py çıktısı, log ölçek)."""
    ns = [4, 5, 6, 7, 8]
    budamali = [17, 54, 153, 552, 2057]
    budamasiz = [65, 326, 1957, 13700, 109601]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    x = list(range(len(ns)))
    w = 0.38
    ax.bar([i - w / 2 for i in x], budamali, w, color=EDGE[0],
           label="budamalı")
    ax.bar([i + w / 2 for i in x], budamasiz, w, color=ACCENT,
           label="budamasız")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(["N=%d" % n for n in ns], fontsize=9)
    ax.set_ylabel("düğüm sayısı (log)", fontsize=9, color=INK)
    for i in x:
        ax.text(i - w / 2, budamali[i] * 1.12, str(budamali[i]),
                ha="center", fontsize=7.6, color=INK)
        ax.text(i + w / 2, budamasiz[i] * 1.12, str(budamasiz[i]),
                ha="center", fontsize=7.6, color=INK)
    ax.set_title("Budama, düğüm sayısını N arttıkça daha da düşürür",
                 fontsize=9.6, color=INK, loc="left", weight="bold")
    ax.legend(frameon=False, fontsize=8.6, loc="upper left")
    _ayar(ax)
    ax.set_ylim(10, 2e5)
    fig.tight_layout()
    return _save(fig, path)


# ----- 8. Sudoku dugum sayisi olcumu --------------------------------------
def sudoku_olcum(path):
    """Şekil 15.8: iki bulmaca, naif sıra ve MRV (sudoku.py çıktısı)."""
    etiket = ["kolay bulmaca", "zor bulmaca"]
    naif = [4209, 49559]
    mrv = [52, 10102]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    x = [0, 1]
    w = 0.36
    ax.bar([i - w / 2 for i in x], naif, w, color=EDGE[0],
           label="naif sıra")
    ax.bar([i + w / 2 for i in x], mrv, w, color=ACCENT,
           label="MRV (en kısıtlı hücre)")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, fontsize=9)
    ax.set_ylabel("düğüm sayısı (log)", fontsize=9, color=INK)
    for i in x:
        ax.text(i - w / 2, naif[i] * 1.12, str(naif[i]), ha="center",
                fontsize=8, color=INK)
        ax.text(i + w / 2, mrv[i] * 1.12, str(mrv[i]), ha="center",
                fontsize=8, color=INK)
    ax.set_title("Sezgi, düğüm sayısını düşürür", fontsize=9.6,
                 color=INK, loc="left", weight="bold")
    ax.legend(frameon=False, fontsize=8.6, loc="upper right")
    _ayar(ax)
    ax.set_ylim(10, 2e5)
    fig.tight_layout()
    return _save(fig, path)


# ----- 9. Geri izleme dongusu ---------------------------------------------
def geri_izleme_dongu(path):
    """Şekil 15.9: seç - keşfet - geri al döngüsü ve kesme noktaları."""
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 0.3, 3.9, 2.4, 1.2, "1. Seç\nyol.append(v)", FILL[0],
         EDGE[0], fs=9.2)
    _box(ax, 3.8, 3.9, 2.6, 1.2, "2. Keşfet\nözyinelemeli çağrı",
         FILL[1], EDGE[1], fs=9.2)
    _box(ax, 7.3, 3.9, 2.4, 1.2, "3. Geri al\nyol.pop()", FILL[3],
         EDGE[3], fs=9.2)
    _arrow(ax, 2.7, 4.5, 3.8, 4.5)
    _arrow(ax, 6.4, 4.5, 7.3, 4.5)
    _box(ax, 0.3, 0.4, 2.8, 1.1, "Çözüm mü?\nkaydet, dön", FILL[2],
         EDGE[2], fs=8.8)
    _box(ax, 3.7, 0.4, 2.8, 1.1, "Geçersiz mi?\nbudama (dön)", FILL[4],
         EDGE[4], fs=8.8)
    _box(ax, 7.1, 0.4, 2.6, 1.1, "Aday kalmadı:\ngeri dön", FILL[3],
         EDGE[3], fs=8.8)
    _arrow(ax, 1.7, 3.9, 1.7, 1.5, col=MUTED, lw=1.1)
    _arrow(ax, 5.1, 3.9, 5.1, 1.5, col=MUTED, lw=1.1)
    _arrow(ax, 8.4, 3.9, 8.4, 1.5, col=MUTED, lw=1.1)
    ax.text(0.3, 5.7, "Her düzeyde seç, keşfet, geri al. Alt kutular, "
            "her düğümde yapılan kontroller.", fontsize=8.6, color=INK,
            va="top")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(cagri_yigini, "b15_cagri_yigini.png"),
                   (fib_agac, "b15_fib_agac.png"),
                   (alt_kume_agac, "b15_alt_kume_agac.png"),
                   (permutasyon_agac, "b15_permutasyon_agac.png"),
                   (budama_agac, "b15_budama_agac.png"),
                   (vezir8, "b15_vezir8.png"),
                   (budama_olcum, "b15_budama_olcum.png"),
                   (sudoku_olcum, "b15_sudoku_olcum.png"),
                   (geri_izleme_dongu, "b15_geri_izleme_dongu.png")]:
        print(fn(os.path.join(out, ad)))
