# -*- coding: utf-8 -*-
"""Bölüm 36 - 'Formal Diller' diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV dosyalarını okur:
  b36_redos.csv      (a+)+b, naif geri izleme adımları ve Python re süresi
  b36_thompson.csv   Thompson NFA simülasyonunun doğrusal süresi
Diğer şekiller bölümdeki örnek değerlerden (DFA, NFA, PDA, TM izleri)
ve engine/src altındaki Doruk lexer kaynağından çizilir.
"""
import csv
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")
MONO = {"family": "DejaVu Sans Mono"}


def _yol(ad):
    return os.path.join(OUT, "b36_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _durum(ax, x, y, metin, kabul=False, r=0.42, fs=11, renk=None):
    """Otomat durumu: daire; kabul durumunda çift halka."""
    kenar = renk or ACCENT_L
    ax.add_patch(Circle((x, y), r, facecolor=FILL[0], edgecolor=kenar,
                        linewidth=1.3, zorder=3))
    if kabul:
        ax.add_patch(Circle((x, y), r - 0.09, facecolor="none",
                            edgecolor=kenar, linewidth=1.0, zorder=3))
    ax.text(x, y, metin, ha="center", va="center", fontsize=fs,
            color=INK, zorder=4)


def _kenar(ax, x1, y1, x2, y2, etiket, rad=0.0, dx=0.0, dy=0.0,
           col=ACCENT, fs=10):
    """Düz/eğri kenar ve etiket; etiket kenardan (dx, dy) kadar kaydırılır."""
    _arrow(ax, x1, y1, x2, y2, col=col, rad=rad, lw=1.3)
    if etiket:
        mx, my = (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy
        ax.text(mx, my, etiket, ha="center", va="center", fontsize=fs,
                color=col, zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                          edgecolor="none"))


def _dongu(ax, x, y, etiket, yon=1, fs=10, col=ACCENT):
    """Kendi üzerine dönen kenar (yon=1 yukarı, -1 aşağı)."""
    ax.add_patch(FancyBboxPatch((x - 0.3, y + yon * 0.42), 0.6, 0.01,
                                boxstyle="square,pad=0", fill=False,
                                edgecolor="none"))
    _arrow(ax, x - 0.25, y + yon * 0.38, x + 0.25, y + yon * 0.38,
           col=col, rad=-yon * 0.9, lw=1.3)
    ax.text(x, y + yon * 0.98, etiket, ha="center", va="center",
            fontsize=fs, color=col)


# 1. Üç'e bölünebilirlik DFA'sı ---------------------------------------- #
def dfa_uc_bolunme():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7)
    ax.text(7.0, 6.7, "Değer mod 3: yeni değer = (2 · eski + bit) mod 3",
            ha="center", fontsize=10, color=MUTED)
    ax.annotate("", xy=(1.6, 2.7), xytext=(0.2, 2.7),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.3))
    _durum(ax, 2.6, 2.7, "r0", kabul=True)
    _durum(ax, 7.0, 5.0, "r1")
    _durum(ax, 11.4, 2.7, "r2")
    _kenar(ax, 2.9, 3.05, 6.7, 4.75, "1", rad=-0.25, dx=-0.45, dy=0.55)
    _kenar(ax, 6.7, 4.55, 2.9, 2.85, "1", rad=-0.25, dx=-0.15, dy=-0.95)
    _kenar(ax, 7.3, 4.75, 11.1, 2.95, "0", rad=-0.25, dx=0.35, dy=0.95)
    _kenar(ax, 11.1, 2.85, 7.3, 4.55, "0", rad=-0.25, dx=0.55, dy=-0.7)
    _dongu(ax, 2.6, 2.7, "0", yon=-1)
    _dongu(ax, 11.4, 2.7, "1", yon=-1)
    ax.text(7.0, 1.2, "Yalnız 3 durum; her durum bir kalan (mod 3) değeri "
            "taşır.", ha="center", fontsize=9.5, color=MUTED)
    ax.text(7.0, 0.5, "r0 kabul durumudur: değer 3'ün katıdır.",
            ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("dfa_uc"))


# 2. NFA ve alt küme yapısı -------------------------------------------- #
def nfa_altkume():
    fig, ax = _tuval(9.8, 4.7, xl=14, yl=7.4)
    ax.text(3.6, 6.9, "NFA: (a|b)*abb", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ax.text(10.4, 6.9, "Alt küme yapısı: DFA", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    x = [0.9, 2.6, 4.3, 6.0]
    for i, xi in enumerate(x):
        _durum(ax, xi, 4.6, "q%d" % i, kabul=(i == 3), r=0.36, fs=10)
    ax.annotate("", xy=(0.45, 4.6), xytext=(-0.1, 4.6),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
    _kenar(ax, 1.26, 4.6, 2.24, 4.6, "a", fs=9.5)
    _kenar(ax, 2.96, 4.6, 3.94, 4.6, "b", fs=9.5)
    _kenar(ax, 4.66, 4.6, 5.64, 4.6, "b", fs=9.5)
    _dongu(ax, 0.9, 4.6, "a, b", yon=1, fs=9)
    ax.text(3.6, 3.5, "q0 -a-> {q0, q1}; q0 -b-> {q0}", ha="center",
            fontsize=8.6, color=MUTED)
    # DFA: dört durum, kare düzeni
    p = {"{0}": (9.0, 4.9), "{0,1}": (12.4, 4.9),
         "{0,2}": (12.4, 2.3), "{0,3}": (9.0, 2.3)}
    for ad, (xx, yy) in p.items():
        _durum(ax, xx, yy, ad, kabul=(ad == "{0,3}"), r=0.52, fs=8.6)
    _kenar(ax, 9.52, 4.9, 11.88, 4.9, "a", fs=9, dy=0.3)
    _kenar(ax, 11.95, 4.35, 11.95, 2.85, "b", fs=9, dx=-0.3)
    _kenar(ax, 12.85, 2.85, 12.85, 4.35, "a", fs=9, dx=0.35)
    _kenar(ax, 11.88, 2.3, 9.52, 2.3, "b", fs=9, dy=-0.3)
    _kenar(ax, 9.0, 2.82, 9.0, 4.38, "b", fs=9, dx=-0.3)
    _kenar(ax, 9.52, 2.5, 11.88, 4.75, "a", fs=9, dx=0.2, dy=-0.15)
    _dongu(ax, 9.0, 4.9, "b", yon=1, fs=9)
    _dongu(ax, 12.4, 4.9, "a", yon=1, fs=9)
    ax.text(7.0, 0.7, "Her DFA durumu, NFA'nın o anda olabileceği durum "
            "kümesidir.", ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("nfa_altkume"))


# 3. Thompson parçaları ------------------------------------------------ #
def thompson_parcalar():
    fig, ax = _tuval(9.6, 6.6, xl=14, yl=9.6)
    ax.text(3.5, 9.2, "harf a", ha="center", fontsize=10, weight="bold")
    ax.text(10.5, 9.2, "birleştirme ab", ha="center", fontsize=10,
            weight="bold")
    ax.text(3.5, 4.5, "birleşim a|b", ha="center", fontsize=10,
            weight="bold")
    ax.text(10.5, 4.5, "yıldız a*", ha="center", fontsize=10,
            weight="bold")
    # harf
    _durum(ax, 1.4, 7.8, "s", r=0.38)
    _durum(ax, 5.6, 7.8, "t", kabul=True, r=0.38)
    _kenar(ax, 1.8, 7.8, 5.2, 7.8, "a", fs=10)
    # birleştirme
    _durum(ax, 8.2, 7.8, "s1", r=0.36, fs=9)
    _durum(ax, 10.6, 7.8, "t1", r=0.36, fs=9)
    _durum(ax, 12.9, 7.8, "t2", kabul=True, r=0.36, fs=9)
    _kenar(ax, 8.56, 7.8, 10.24, 7.8, "a", fs=9)
    _kenar(ax, 10.96, 7.8, 12.54, 7.8, "b", fs=9)
    # birleşim
    _durum(ax, 1.4, 2.5, "s", r=0.36, fs=9)
    _durum(ax, 3.2, 3.6, "x1", r=0.36, fs=9)
    _durum(ax, 3.2, 1.4, "x2", r=0.36, fs=9)
    _durum(ax, 5.6, 3.6, "y1", r=0.36, fs=9)
    _durum(ax, 5.6, 1.4, "y2", r=0.36, fs=9)
    _durum(ax, 7.5, 2.5, "t", kabul=True, r=0.36, fs=9)
    _kenar(ax, 1.76, 2.7, 2.84, 3.5, "ε", fs=8.5)
    _kenar(ax, 1.76, 2.3, 2.84, 1.5, "ε", fs=8.5)
    _kenar(ax, 3.56, 3.6, 5.24, 3.6, "a", fs=9)
    _kenar(ax, 3.56, 1.4, 5.24, 1.4, "b", fs=9)
    _kenar(ax, 5.96, 3.5, 7.14, 2.7, "ε", fs=8.5)
    _kenar(ax, 5.96, 1.5, 7.14, 2.3, "ε", fs=8.5)
    # yıldız
    _durum(ax, 8.4, 2.5, "s", r=0.36, fs=9)
    _durum(ax, 9.9, 2.5, "x1", r=0.36, fs=9)
    _durum(ax, 11.4, 2.5, "x2", r=0.36, fs=9)
    _durum(ax, 12.9, 2.5, "t", kabul=True, r=0.36, fs=9)
    _kenar(ax, 8.76, 2.5, 9.54, 2.5, "ε", fs=8.5)
    _kenar(ax, 10.26, 2.5, 11.04, 2.5, "a", fs=9)
    _kenar(ax, 11.76, 2.5, 12.54, 2.5, "ε", fs=8.5)
    _kenar(ax, 8.4, 2.86, 12.9, 2.86, "ε", rad=-0.35, fs=8.5)
    _kenar(ax, 11.4, 2.14, 9.9, 2.14, "ε", rad=-0.45, fs=8.5)
    ax.text(7.0, 0.3, "Her parça tek başlangıç ve tek bitiş durumu taşır;"
            " parçalar ε ile birleşir.", ha="center", fontsize=8.8,
            color=MUTED)
    return _save(fig, _yol("thompson"))


# 4. Minimizasyon: çift parite -> minimal DFA ------------------------- #
def minimizasyon():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.4)
    ax.text(3.6, 6.9, "Ön: 4 durum (a-parite, b-parite)", ha="center",
            fontsize=10, weight="bold")
    ax.text(10.4, 6.9, "Sonra: 2 durum (yalnız a-parite)", ha="center",
            fontsize=10, weight="bold")
    p = {"00": (1.6, 4.9), "10": (5.6, 4.9), "01": (1.6, 1.8),
         "11": (5.6, 1.8)}
    for ad, (xx, yy) in p.items():
        _durum(ax, xx, yy, "(%s)" % ad, kabul=(ad[0] == "0"), r=0.5,
               fs=9)
    _kenar(ax, 2.12, 4.9, 5.08, 4.9, "a", fs=9)
    _kenar(ax, 5.08, 4.5, 2.12, 4.5, "a", rad=-0.2, fs=9, dx=0, dy=0.35)
    _kenar(ax, 1.6, 4.4, 1.6, 2.3, "b", fs=9, dx=-0.5)
    _kenar(ax, 5.6, 4.4, 5.6, 2.3, "b", fs=9, dx=0.5)
    _kenar(ax, 2.12, 1.8, 5.08, 1.8, "a", fs=9)
    _kenar(ax, 5.08, 1.4, 2.12, 1.4, "a", rad=-0.2, fs=9, dx=0, dy=-0.35)
    # minimal
    _durum(ax, 9.2, 4.9, "E", kabul=True, r=0.55, fs=11)
    _durum(ax, 12.6, 4.9, "O", r=0.55, fs=11)
    _kenar(ax, 9.75, 4.9, 12.05, 4.9, "a", rad=-0.2, fs=9, dy=0.45)
    _kenar(ax, 12.05, 4.5, 9.75, 4.5, "a", rad=-0.2, fs=9, dy=-0.5)
    _dongu(ax, 9.2, 4.9, "b", yon=1, fs=9)
    _dongu(ax, 12.6, 4.9, "b", yon=1, fs=9)
    ax.text(7.0, 0.7, "Denk durumlar: (0,0)~(0,1) ve (1,0)~(1,1). "
            "Kabul: a-parite çift.", ha="center", fontsize=9.3,
            color=MUTED)
    ax.text(7.0, 0.1, "Kabul kararı yalnız a-pariteye bağlı; b-parite"
            " ayrışım yaratmaz.", ha="center", fontsize=9.3, color=MUTED)
    return _save(fig, _yol("minimizasyon"))


# 5. Katastrofik geri izleme ölçümü (CSV) ------------------------------ #
def redos_olcum():
    with open(os.path.join(VERI, "b36_redos.csv"), encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    with open(os.path.join(VERI, "b36_thompson.csv"), encoding="utf-8") as f:
        thm = list(csv.DictReader(f))
    n = [int(s["n"]) for s in satirlar]
    adim = [int(s["naif_adim"]) for s in satirlar]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    a1.semilogy(n, adim, "o-", color=ACCENT, lw=1.6, ms=4,
                label="naif geri izleme (adım)")
    ref = [adim[0] * 2 ** ((x - n[0]) / 1.0) for x in n]
    a1.semilogy(n, ref, "--", color=MUTED, lw=1.0,
                label="2^n referansı (ölçek)")
    a1.set_xlabel("girdi uzunluğu n ('a' sayısı)", color=INK)
    a1.set_ylabel("adım sayısı (log)", color=INK)
    a1.set_title("(a+)+b: üstel artış", fontsize=10, color=INK)
    a1.legend(fontsize=8, frameon=False)
    a1.grid(color=RULE, lw=0.6)
    tn = [int(s["n"]) for s in thm]
    tm = [float(s["thompson_ms"]) for s in thm]
    a2.plot(tn, tm, "s-", color=ACCENT_L, lw=1.6, ms=4,
            label="Thompson simülasyonu")
    a2.set_xlabel("girdi uzunluğu n", color=INK)
    a2.set_ylabel("süre (ms)", color=INK)
    a2.set_title("Aynı desen: doğrusal büyüme", fontsize=10, color=INK)
    a2.legend(fontsize=8, frameon=False)
    a2.grid(color=RULE, lw=0.6)
    for a in (a1, a2):
        a.tick_params(colors=INK, labelsize=8)
        for s in a.spines.values():
            s.set_color(RULE)
    fig.tight_layout()
    return _save(fig, _yol("redos"))


# 6. Belirsiz gramer: iki türetme ağacı ------------------------------- #
def _agac(ax, agac, x0, y0, dx, dy, bitis):
    """Ağacı ((X, alt...) demetleri) tepeden aşağı çizer; yaprak x'leri
    sıradan verilir. Döndürdüğü değer (x, y) düğüm konumudur."""
    sayac = [0]

    def yerlestir(dugum, derinlik):
        if isinstance(dugum, str):
            x = x0 + sayac[0] * dx
            sayac[0] += 1
            return x, y0 - derinlik * dy, dugum, []
        etiket, cocuklar = dugum[0], dugum[1]
        ilk = []
        for c in cocuklar:
            ilk.append(yerlestir(c, derinlik + 1))
        x = sum(c[0] for c in ilk) / len(ilk)
        return x, y0 - derinlik * dy, etiket, ilk

    def ciz(dugum):
        x, y, etiket, cocuklar = dugum
        for c in cocuklar:
            _arrow(ax, x, y - 0.1, c[0], c[1] + 0.1, col=MUTED, lw=0.9)
        renk = FILL[1] if isinstance(etiket, str) and len(etiket) == 1 \
            and etiket.isalpha() is False else FILL[0]
        ax.add_patch(Circle((x, y), 0.19, facecolor=renk,
                            edgecolor=EDGE[0] if etiket in "nE" or
                            etiket == "E" else EDGE[2], lw=1.0, zorder=3))
        ax.text(x, y, etiket, ha="center", va="center", fontsize=9,
                color=INK, zorder=4, family="DejaVu Sans")
        for c in cocuklar:
            ciz(c)

    kok = yerlestir(agac, 0)
    ciz(kok)
    return kok


def turetme_agaclari():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.6))
    # Ağaç 1: (n + (n * n))
    t1 = ("E", (("E", ("n",)), "+",
                ("E", (("E", ("n",)), "*", ("E", ("n",))))))
    # Ağaç 2: ((n + n) * n)
    t2 = ("E", (("E", (("E", ("n",)), "+", ("E", ("n",)))), "*",
                ("E", ("n",))))
    for ax, t, ad in ((a1, t1, "Ağaç 1: n + (n * n)"),
                      (a2, t2, "Ağaç 2: (n + n) * n")):
        ax.set_xlim(-0.6, 4.6)
        ax.set_ylim(-3.7, 0.9)
        ax.axis("off")
        ax.set_title(ad, fontsize=10, color=INK)
        _agac(ax, t, 0.0, 0.0, 1.0, 0.85, None)
    fig.tight_layout()
    return _save(fig, _yol("turetme"))


# 7. Chomsky hiyerarşisi ---------------------------------------------- #
def chomsky():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=8.4)
    ax.add_patch(FancyBboxPatch((0.3, 0.3), 13.4, 7.8,
                 boxstyle="round,pad=0.02,rounding_size=0.3",
                 facecolor=FILL[4], edgecolor=EDGE[4], lw=1.2))
    ax.text(1.0, 7.5, "Özyinelemeli sayılabilir (Turing makinesi)",
            fontsize=9.8, color=INK, weight="bold")
    ax.text(1.0, 7.0, "örnek: 'bu program durur mu?' kümesi  (dil değil"
            " tanıma sınırı)", fontsize=8.6, color=MUTED)
    ax.add_patch(FancyBboxPatch((1.0, 0.9), 11.6, 5.7,
                 boxstyle="round,pad=0.02,rounding_size=0.3",
                 facecolor=FILL[2], edgecolor=EDGE[2], lw=1.2))
    ax.text(1.7, 6.2, "Bağlama duyarlı (doğrusal sınırlı otomat)",
            fontsize=9.6, color=INK, weight="bold")
    ax.text(1.7, 5.7, "örnek: a^n b^n c^n", fontsize=8.6, color=MUTED)
    ax.add_patch(FancyBboxPatch((2.0, 1.8), 9.6, 3.4,
                 boxstyle="round,pad=0.02,rounding_size=0.3",
                 facecolor=FILL[1], edgecolor=EDGE[1], lw=1.2))
    ax.text(2.7, 4.75, "Bağlamdan bağımsız (yığınlı otomat, PDA)",
            fontsize=9.4, color=INK, weight="bold")
    ax.text(2.7, 4.3, "örnek: a^n b^n;  dengeli parantez", fontsize=8.6,
            color=MUTED)
    ax.add_patch(FancyBboxPatch((3.0, 2.3), 7.6, 1.5,
                 boxstyle="round,pad=0.02,rounding_size=0.25",
                 facecolor=FILL[0], edgecolor=EDGE[0], lw=1.2))
    ax.text(3.7, 3.4, "Düzenli (DFA = NFA = düzenli ifade)", fontsize=9.2,
            color=INK, weight="bold")
    ax.text(3.7, 2.85, "örnek: (a|b)*abb;  ikili sayı 3'e bölünebilir",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("chomsky"))


# 8. PDA yığını: { [ ( ) ] } ------------------------------------------ #
def pda_yigin():
    adimlar = [("{", ["{"]), ("[", ["{", "["]), ("(", ["{", "[", "("]),
               (")", ["{", "["]), ("]", ["{"]), ("}", [])]
    fig, ax = _tuval(9.6, 4.9, xl=14, yl=8.2)
    ax.text(7.0, 7.8, "Girdi: { [ ( ) ] }  ->  her adımda yığının durumu",
            ha="center", fontsize=10, color=INK, weight="bold")
    for i, (harf, yigin) in enumerate(adimlar):
        x = 1.0 + i * 2.2
        ax.text(x + 0.5, 7.1, harf, ha="center", fontsize=12,
                family="DejaVu Sans Mono", color=ACCENT)
        ax.plot([x - 0.2, x + 1.1], [6.7, 6.7], color=RULE, lw=0.8)
        for k, s in enumerate(yigin):
            _box(ax, x, 1.0 + k * 0.85, 0.9, 0.7, s, FILL[1], EDGE[1],
                 fs=12, bold=True)
    ax.text(7.0, 0.4, "Kapanış harfi yığının tepesiyle eşleşmezse "
            "dizge reddedilir.", ha="center", fontsize=9.2, color=MUTED)
    return _save(fig, _yol("pda_yigin"))


# 9. Turing makinesi: ikili +1 bant izi -------------------------------- #
def tm_bant():
    delta = {("q0", "0"): ("0", "R", "q0"), ("q0", "1"): ("1", "R", "q0"),
             ("q0", "_"): ("_", "L", "q1"), ("q1", "1"): ("0", "L", "q1"),
             ("q1", "0"): ("1", "L", "dur"), ("q1", "_"): ("1", "L", "dur")}
    bant = dict(enumerate("1011"))
    kafa, durum, iz = 0, "q0", []
    iz.append((dict(bant), kafa, durum))
    while durum != "dur":
        s = bant.get(kafa, "_")
        yaz, h, yeni = delta[(durum, s)]
        bant[kafa] = yaz
        kafa += 1 if h == "R" else -1
        durum = yeni
        iz.append((dict(bant), kafa, durum))
    araligi = range(-1, 6)
    fig, ax = _tuval(9.6, 6.2, xl=14, yl=9.6)
    ax.text(7.0, 9.25, "1011 (=11) + 1: bant ve başlık (her satır bir adım)",
            ha="center", fontsize=10, color=INK, weight="bold")
    for r, (b, k, q) in enumerate(iz):
        y = 8.2 - r * 0.72
        ax.text(0.6, y, "%s" % q, ha="left", va="center", fontsize=9.5,
                color=MUTED, family="DejaVu Sans Mono")
        for c, i in enumerate(araligi):
            x = 2.0 + c * 1.5
            sembol = b.get(i, "_")
            _box(ax, x, y - 0.3, 1.2, 0.6, sembol, FILL[0],
                 ACCENT if i == k else RULE, fs=12, bold=(i == k))
    ax.text(7.0, 0.25, "Başlık (kırmızı kare) sağa-sola gider; 'dur' "
            "durumunda makine durur.", ha="center", fontsize=9.2,
            color=MUTED)
    return _save(fig, _yol("tm_bant"))


# 10. Doruk lexer durum diyagramı (kaynaktan çıkarılmış) --------------- #
def doruk_lexer():
    fig, ax = _tuval(9.8, 6.6, xl=14, yl=9.8)
    ax.text(7.0, 9.45, "Doruk lexer: durumlar (Lexer.cpp, sonrakiToken)",
            ha="center", fontsize=10, color=INK, weight="bold")
    _durum(ax, 1.0, 4.6, "başla", r=0.5, fs=8.6)
    _durum(ax, 4.4, 7.6, "SAYI", kabul=True, r=0.5, fs=8.4)
    _durum(ax, 7.6, 8.7, "NOKTA", r=0.5, fs=8)
    _durum(ax, 11.0, 8.7, "ONDALIK", kabul=True, r=0.64, fs=7.4)
    _durum(ax, 7.6, 6.4, "ÜS", r=0.5, fs=8.4)
    _durum(ax, 4.4, 4.6, "KİMLİK", kabul=True, r=0.5, fs=7.6)
    _durum(ax, 7.6, 4.6, "METİN", r=0.5, fs=8.4)
    _durum(ax, 11.0, 4.6, "METİN_LIT", kabul=True, r=0.64, fs=6.6)
    _durum(ax, 4.4, 1.6, "OP", kabul=True, r=0.5, fs=8.4)
    _durum(ax, 7.6, 1.6, "ÇİFT", kabul=True, r=0.5, fs=8)
    _kenar(ax, 1.5, 4.9, 3.95, 7.2, "rakam", fs=8.4, dx=-0.55, dy=0.3)
    _kenar(ax, 4.85, 7.8, 7.15, 8.5, "'.'", fs=8.4, dy=0.35)
    _kenar(ax, 8.1, 8.7, 10.5, 8.7, "rakam", fs=8.4, dy=0.3)
    _dongu(ax, 4.4, 7.6, "rakam", yon=1, fs=8.2)
    _kenar(ax, 4.85, 7.4, 7.15, 6.6, "e / E", fs=8.4, dx=-0.2, dy=-0.35)
    _kenar(ax, 8.1, 6.5, 10.6, 8.4, "± / rakam", fs=8.2, dx=0.3, dy=-0.45)
    _kenar(ax, 1.5, 4.6, 3.9, 4.6, "harf, _, UTF-8", fs=8.2, dy=0.3)
    _dongu(ax, 4.4, 4.6, "devam", yon=1, fs=8.2)
    _kenar(ax, 8.1, 4.6, 10.5, 4.6, "kapanış tırnağı", fs=8.2, dy=0.3)
    _dongu(ax, 7.6, 4.6, "karakter", yon=-1, fs=8.2)
    _kenar(ax, 1.2, 4.1, 7.2, 4.2, "", rad=0.3)
    ax.text(4.9, 3.25, "\" veya '", ha="center", fontsize=8.2, color=ACCENT)
    _kenar(ax, 1.2, 4.2, 3.9, 1.95, "+ - * / = ! < >", fs=8.2, dx=-1.3,
           dy=-0.5)
    _kenar(ax, 4.9, 1.6, 7.1, 1.6, "ikinci karakter", fs=8.2, dy=0.3)
    ax.text(7.0, 0.5, "Boşluk ve yorumlar atlanır. Çift halka = kabul "
            "durumu. '&' ve '|' tek başına hata üretir.", ha="center",
            fontsize=8.4, color=MUTED)
    return _save(fig, _yol("doruk_lexer"))


if __name__ == "__main__":
    for f in (dfa_uc_bolunme, nfa_altkume, thompson_parcalar, minimizasyon,
              redos_olcum, turetme_agaclari, chomsky, pda_yigin, tm_bant,
              doruk_lexer):
        print(f.__name__, "->", f())
