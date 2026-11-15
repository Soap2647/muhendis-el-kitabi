# -*- coding: utf-8 -*-
"""Bolum 51 - Bilgi Teorisi diyagramlari.

Olcum grafikleri engine/veri/ altindaki CSV dosyalarini okur:
  b51_harf.csv          Turkce harf olasiliklari (sekil 51.3)
  b51_metin_entropi.csv Harf ve bayt entropi duzeyleri (sekil 51.4)
  b51_kodlama.csv       Entropi, Huffman, aritmetik kodlama (sekil 51.5)
  b51_ber.csv           Kodsuz, tekrar(3) ve Hamming(7,4) BER (sekil 51.10)
Diger sekiller analitik formullerle (sabit degerlerle) cizilir.
"""
import csv
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _h2(p):
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def _ax(w=8.4, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=INK, labelsize=9.5)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)
    return fig, ax


# --------------------------------------------------------------------------- #
def ikili_entropi(path):
    """H(p) egrisi: p=0.5'te en yuksek (1 bit), uc isaretli nokta."""
    fig, ax = _ax(7.4, 3.9)
    p = np.linspace(0.0, 1.0, 400)
    h = np.array([_h2(x) for x in p])
    ax.plot(p, h, color=ACCENT, lw=2.2)
    ax.fill_between(p, h, color=FILL[3], alpha=0.6)
    for x, lab, yx, yy in [(0.5, "p = 0,5: H = 1 bit", 0.53, 1.05),
                           (0.9, "p = 0,9: H = 0,469 bit", 0.6, 0.3),
                           (0.11, "p = 0,11: H = 0,500 bit", 0.14, 0.62)]:
        ax.plot([x], [_h2(x)], "o", color=EDGE[0], ms=6)
        ax.annotate(lab, (x, _h2(x)), xytext=(yx, yy),
                    fontsize=9.5, color=INK)
    ax.set_xlabel("olasılık p", color=INK, fontsize=10)
    ax.set_ylabel("H(p)  [bit]", color=INK, fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.12)
    return _save(fig, os.path.join(OUT, "b51_ikili_entropi.png"))


# --------------------------------------------------------------------------- #
def venn_iliski(path):
    """H(X), H(Y), I(X;Y) ve H(X,Y) cercevesi; sensor ornegi degerleri."""
    hx, hy, hxy = 1.4851, 1.1382, 2.3206
    i = hx + hy - hxy
    fig, ax = plt.subplots(figsize=(8.0, 4.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.add_patch(Rectangle((0.3, 0.3), 9.4, 5.4, fill=False,
                           ec=MUTED, lw=1.2, ls="--"))
    ax.text(0.6, 5.45, "H(X,Y) = %.4f bit" % hxy, fontsize=10.5,
            color=INK)
    ax.add_patch(Circle((3.9, 2.9), 2.3, color=EDGE[0], alpha=0.22))
    ax.add_patch(Circle((6.1, 2.9), 2.0, color=EDGE[1], alpha=0.22))
    ax.add_patch(Circle((3.9, 2.9), 2.3, fill=False, ec=EDGE[0], lw=1.6))
    ax.add_patch(Circle((6.1, 2.9), 2.0, fill=False, ec=EDGE[1], lw=1.6))
    ax.text(2.6, 4.9, "H(X) = %.4f" % hx, fontsize=10.5, color=EDGE[0],
            weight="bold")
    ax.text(7.2, 4.9, "H(Y) = %.4f" % hy, fontsize=10.5, color=EDGE[1],
            weight="bold", ha="right")
    ax.text(2.3, 2.6, "H(X|Y)", fontsize=10.5, color=INK, ha="center")
    ax.text(2.3, 2.2, "%.4f" % (hxy - hy), fontsize=10.5, color=INK,
            ha="center")
    ax.text(5.0, 2.8, "I(X;Y)", fontsize=10.5, color=ACCENT, ha="center",
            weight="bold")
    ax.text(5.0, 2.35, "%.4f" % i, fontsize=10.5, color=ACCENT,
            ha="center", weight="bold")
    ax.text(7.2, 1.6, "H(Y|X) = %.4f" % (hxy - hx), fontsize=10,
            color=INK, ha="center")
    return _save(fig, os.path.join(OUT, "b51_venn_iliski.png"))


# --------------------------------------------------------------------------- #
def harf_frekans(path):
    """Turkce harf olasilik dagilimi (CSV), azalan siralama."""
    satirlar = _oku("b51_harf.csv")
    satirlar.sort(key=lambda r: -float(r["olasilik"]))
    harf = [r["harf"] for r in satirlar]
    p = [float(r["olasilik"]) for r in satirlar]
    h0 = -sum(x * math.log2(x) for x in p)
    fig, ax = _ax(9.0, 3.9)
    renk = [EDGE[0] if x > 0.02 else FILL[4] for x in p]
    ax.bar(range(len(p)), [100 * x for x in p], color=renk,
           edgecolor=EDGE[0], lw=0.5)
    ax.set_xticks(range(len(p)))
    ax.set_xticklabels(harf, fontsize=9.5)
    ax.set_ylabel("olasılık  [%]", color=INK, fontsize=10)
    ax.text(len(p) - 1, 11.5, "H0 = %.3f bit/harf" % h0, ha="right",
            fontsize=10, color=ACCENT)
    ax.text(len(p) - 1, 10.2, "(üst sınır log2 29 = 4,858)", ha="right",
            fontsize=9, color=MUTED)
    ax.set_ylim(0, 12.5)
    return _save(fig, os.path.join(OUT, "b51_harf_frekans.png"))


# --------------------------------------------------------------------------- #
def entropi_duzeyleri(path):
    """Harf ve bayt icin 0. ve 1./2. derece (kosullu) entropi."""
    satirlar = _oku("b51_metin_entropi.csv")
    etiket = []
    deger = []
    for r in satirlar:
        etiket.append("%s  %s" % (r["alfabe"], r["model"]))
        deger.append(float(r["bit_per_simge"]))
    fig, ax = _ax(8.6, 3.6)
    renk = [EDGE[0] if e.startswith("harf") else EDGE[2] for e in etiket]
    y = np.arange(len(deger))
    ax.barh(y, deger, color=renk, alpha=0.85, height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(etiket, fontsize=9.5)
    ax.invert_yaxis()
    for yi, v in zip(y, deger):
        ax.text(v + 0.05, yi, "%.3f" % v, va="center", fontsize=9.5,
                color=INK)
    ax.axvline(math.log2(29), color=ACCENT, ls="--", lw=1.1)
    ax.text(math.log2(29) + 0.05, -0.45,
            "log2 29 = 4,858", color=ACCENT, fontsize=9)
    ax.set_xlabel("bit / simge", color=INK, fontsize=10)
    ax.set_xlim(0, 5.8)
    ax.grid(axis="x", color=RULE, lw=0.6)
    ax.grid(axis="y", visible=False)
    return _save(fig, os.path.join(OUT, "b51_entropi_duzeyleri.png"))


# --------------------------------------------------------------------------- #
def kodlama_karsilastirma(path):
    """Entropi, Huffman ve aritmetik kodlama: uc kaynak (CSV)."""
    satirlar = _oku("b51_kodlama.csv")
    adlar = ["çarpık 3 simge", "dört simge", "Türkçe harf"]
    fig, ax = _ax(8.6, 4.0)
    genislik = 0.26
    x = np.arange(len(satirlar))
    seri = [("entropi H", "entropi_bit", EDGE[0]),
            ("Huffman L", "huffman_bit", EDGE[2]),
            ("aritmetik", "aritmetik_bit", ACCENT)]
    for k, (ad, anahtar, renk) in enumerate(seri):
        vals = [float(r[anahtar]) for r in satirlar]
        ax.bar(x + (k - 1) * genislik, vals, genislik, color=renk,
               label=ad, alpha=0.9)
        for xi, v in zip(x, vals):
            ax.text(xi + (k - 1) * genislik, v + 0.05, "%.3f" % v,
                    ha="center", fontsize=8.2, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(adlar, fontsize=10)
    ax.set_ylabel("bit / simge", color=INK, fontsize=10)
    ax.set_ylim(0, 5.3)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    return _save(fig, os.path.join(OUT, "b51_kodlama_karsilastirma.png"))


# --------------------------------------------------------------------------- #
def kl_asimetri(path):
    """KL(p||q) ve KL(q||p): iki dagilim, asimetri."""
    p, q = [0.9, 0.1], [0.5, 0.5]
    kpq = sum(a * math.log2(a / b) for a, b in zip(p, q) if a > 0)
    kqp = sum(a * math.log2(a / b) for a, b in zip(q, p) if a > 0)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 3.6),
                                 gridspec_kw={"width_ratios": [1.1, 1]})
    x = np.arange(2)
    a1.bar(x - 0.18, p, 0.36, color=EDGE[0], label="p")
    a1.bar(x + 0.18, q, 0.36, color=ACCENT, label="q")
    a1.set_xticks(x)
    a1.set_xticklabels(["yazı (0)", "tura (1)"], fontsize=10)
    a1.set_ylim(0, 1.05)
    a1.set_title("dağılımlar", fontsize=10.5, color=INK)
    a1.legend(frameon=False, fontsize=9.5)
    a2.bar([0, 1], [kpq, kqp], 0.5, color=[EDGE[0], ACCENT])
    a2.set_xticks([0, 1])
    a2.set_xticklabels(["KL(p||q)", "KL(q||p)"], fontsize=10)
    for xi, v in zip([0, 1], [kpq, kqp]):
        a2.text(xi, v + 0.02, "%.3f bit" % v, ha="center", fontsize=10)
    a2.set_ylim(0, 0.9)
    a2.set_title("ıraksama (bit)", fontsize=10.5, color=INK)
    for a in (a1, a2):
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(colors=INK, labelsize=9.5)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b51_kl_asimetri.png"))


# --------------------------------------------------------------------------- #
def softmax_kayip(path):
    """Ikili (iki sinif) softmax: kayip ve gradyan, dogru sinif logiti z0."""
    z0 = np.linspace(-3, 5, 300)
    kayip = np.log(1 + 2 * np.exp(-z0))           # diger iki logit 0
    p0 = 1 / (1 + 2 * np.exp(-z0))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 3.6))
    a1.plot(z0, kayip, color=ACCENT, lw=2.0)
    a1.set_xlabel("doğru sınıfın logiti z0", color=INK, fontsize=9.5)
    a1.set_ylabel("L = ln(1 + 2e^(−z0))  [nat]", color=INK, fontsize=9.5)
    a1.set_title("çapraz entropi kaybı", fontsize=10.5, color=INK)
    a2.plot(z0, p0 - 1, color=EDGE[0], lw=2.0, label="dL/dz0 = p0 − 1")
    a2.plot(z0, (1 - p0) / 2, color=EDGE[2], lw=2.0,
            label="dL/dz1 = p1  (diğer iki sınıf)")
    a2.axhline(0, color=MUTED, lw=0.8)
    a2.set_xlabel("doğru sınıfın logiti z0", color=INK, fontsize=9.5)
    a2.set_title("gradyan dL/dz0 = p0 − 1", fontsize=10.5, color=INK)
    a2.legend(frameon=False, fontsize=8.8, loc="upper right")
    for a in (a1, a2):
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(colors=INK, labelsize=9)
        a.grid(axis="y", color=RULE, lw=0.6)
        a.set_axisbelow(True)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b51_softmax_kayip.png"))


# --------------------------------------------------------------------------- #
def bsc_ve_shannon(path):
    """Sol: BSC kapasitesi C(p) = 1 - H(p). Sag: Shannon-Hartley."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.7))
    p = np.linspace(0.0, 0.5, 300)
    c = 1 - np.array([_h2(x) for x in p])
    a1.plot(p, c, color=ACCENT, lw=2.0)
    a1.fill_between(p, c, color=FILL[3], alpha=0.5)
    a1.set_xlabel("çapraz olma olasılığı p", color=INK, fontsize=9.5)
    a1.set_ylabel("C(p)  [bit / kanal kullanımı]", color=INK, fontsize=9)
    a1.set_title("BSC kapasitesi", fontsize=10.5, color=INK)
    a1.set_ylim(0, 1.05)
    snr_db = np.linspace(-5, 30, 200)
    snr = 10 ** (snr_db / 10)
    for b_mhz, renk in [(1, EDGE[0]), (10, ACCENT)]:
        cc = b_mhz * np.log2(1 + snr)
        a2.plot(snr_db, cc, color=renk, lw=2.0,
                label="B = %d MHz" % b_mhz)
    a2.axhline(5, color=MUTED, ls="--", lw=1.0,
               label="5 Mbit/s gereksinimi")
    a2.set_xlabel("SNR  [dB]", color=INK, fontsize=9.5)
    a2.set_ylabel("C  [Mbit/s]", color=INK, fontsize=9.5)
    a2.set_title("Shannon-Hartley", fontsize=10.5, color=INK)
    a2.legend(frameon=False, fontsize=9, loc="upper left")
    for a in (a1, a2):
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
        a.tick_params(colors=INK, labelsize=9)
        a.grid(axis="y", color=RULE, lw=0.6)
        a.set_axisbelow(True)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b51_bsc_shannon.png"))


# --------------------------------------------------------------------------- #
def hamming_venn(path):
    """Hamming(7,4): uc esitlik cemberi; konum 1..7 ve veri/eslik bitleri."""
    fig, ax = plt.subplots(figsize=(6.6, 5.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9.4)
    ax.axis("off")
    merkez = [(3.6, 3.7), (6.4, 3.7), (5.0, 6.2)]
    adlar = ["p1 kapsamı", "p2 kapsamı", "p3 kapsamı"]
    for (x, y), renk, ad in zip(merkez, EDGE[:3], adlar):
        ax.add_patch(Circle((x, y), 2.5, color=renk, alpha=0.13))
        ax.add_patch(Circle((x, y), 2.5, fill=False, ec=renk, lw=1.6))
    ax.text(0.4, 1.0, "P1: konum 1, 3, 5, 7", fontsize=9.5,
            color=EDGE[0])
    ax.text(6.9, 1.0, "P2: konum 2, 3, 6, 7", fontsize=9.5,
            color=EDGE[1])
    ax.text(5.0, 9.0, "P3: konum 4, 5, 6, 7", fontsize=9.5,
            color=EDGE[2], ha="center")
    etiket = [
        (2.0, 3.0, "p1\n(konum 1)"),
        (8.0, 3.0, "p2\n(konum 2)"),
        (5.0, 7.9, "p3\n(konum 4)"),
        (5.0, 2.5, "d1\n(konum 3)"),
        (3.4, 5.6, "d2\n(konum 5)"),
        (6.6, 5.6, "d3\n(konum 6)"),
        (5.0, 4.9, "d4\n(konum 7)"),
    ]
    for x, y, t in etiket:
        ax.text(x, y, t, ha="center", va="center", fontsize=9,
                color=INK, weight="bold" if "d" in t[:1] else "normal")
    return _save(fig, os.path.join(OUT, "b51_hamming_venn.png"))


# --------------------------------------------------------------------------- #
def kodsuz_kodlu_ber(path):
    """BER-p (log-log): kodsuz, tekrar(3), Hamming(7,4) (CSV)."""
    satirlar = _oku("b51_ber.csv")
    p = [float(r["p"]) for r in satirlar]
    fig, ax = _ax(7.6, 4.2)
    ax.grid(True, which="both", color=RULE, lw=0.5)
    # Sifir BER log olcekte cizilemez: sifir degerler atlanir.
    for anahtar, bicim, renk, ad in [
            ("kodsuz", "o-", MUTED, "kodsuz (oran 1)"),
            ("tekrar3", "s-", EDGE[2], "tekrar(3) (oran 1/3)"),
            ("hamming74", "^-", ACCENT, "Hamming(7,4) (oran 4/7)")]:
        nokta = [(float(r["p"]), float(r[anahtar])) for r in satirlar
                 if float(r[anahtar]) > 0]
        ax.plot([a for a, _ in nokta], [b for _, b in nokta], bicim,
                color=renk, label=ad)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("kanal hata olasılığı p", color=INK, fontsize=10)
    ax.set_ylabel("bit hata oranı (BER)", color=INK, fontsize=10)
    ax.set_xlim(0.0008, 0.2)
    ax.set_ylim(1e-6, 0.3)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    return _save(fig, os.path.join(OUT, "b51_kodsuz_kodlu_ber.png"))


if __name__ == "__main__":
    ciktilar = [
        ikili_entropi(None),
        venn_iliski(None),
        harf_frekans(None),
        entropi_duzeyleri(None),
        kodlama_karsilastirma(None),
        kl_asimetri(None),
        softmax_kayip(None),
        bsc_ve_shannon(None),
        hamming_venn(None),
        kodsuz_kodlu_ber(None),
    ]
    for c in ciktilar:
        print(c)
