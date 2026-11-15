# -*- coding: utf-8 -*-
"""Bolum 46 - Edge AI & TinyML diyagramlari.

Olcum grafikleri engine/veri/b46_*.csv dosyalarini okur:
  b46_bit_dogruluk.csv, b46_butce.csv, b46_boyut.csv, b46_anomali.csv
Diger sekiller kavramsal semalardir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b46_%s.png" % ad)


def _tuval(w, h, xl=10, yl=10):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------------- #
def spektrum():
    """Bulut - uc - MCU spektrumu (kaba mertebeler)."""
    fig, ax = _tuval(9.6, 4.6, 10, 6.4)
    kol = [
        ("Bulut", "GPU sunucu", FILL[0], EDGE[0],
         "Güç: kW mertebesi\nGecikme: ağa bağlı, yüzlerce ms\n"
         "Bellek: GB - TB\nBağlantı: sürekli gerekli"),
        ("Uç (edge)", "Gömülü bilgisayar + NPU", FILL[1], EDGE[1],
         "Güç: W mertebesi\nGecikme: milisaniye\n"
         "Bellek: GB (LPDDR)\nBağlantı: isteğe bağlı"),
        ("MCU (TinyML)", "Cortex-M4 / M7", FILL[2], EDGE[2],
         "Güç: mW mertebesi\nGecikme: mikro - milisaniye\n"
         "Bellek: KB (RAM), MB (flash)\nBağlantı: gerekmez"),
    ]
    x0 = [0.2, 3.5, 6.8]
    for (ad, alt, f, e, metin), x in zip(kol, x0):
        _box(ax, x, 4.6, 3.0, 1.1, ad, fill=f, edge=e, fs=12, bold=True)
        ax.text(x + 1.5, 4.25, alt, ha="center", fontsize=9.5,
                color=MUTED)
        _box(ax, x, 1.5, 3.0, 2.5, metin, fill="white", edge=e, fs=9.5)
    _arrow(ax, 0.4, 0.95, 9.6, 0.95, col=ACCENT_L, lw=1.4)
    ax.text(5.0, 0.45, "kaynak azalır, gecikme ve gizlilik yerellik "
            "kazanır", ha="center", fontsize=9.5, color=INK)
    return _save(fig, _yol("spektrum"))


def hat():
    """Egit -> disa aktar -> kuantize -> C dizisi -> derle -> dogrula."""
    fig, ax = _tuval(9.6, 3.2, 10, 4.2)
    adim = [("1. Eğit", "numpy, float32"),
            ("2. Dışa aktar", "ağırlık, ölçek"),
            ("3. Kuantize", "int8, M0 ve rs"),
            ("4. C dizisi", "model_int8.h"),
            ("5. Derle", "Cortex-M4 gcc"),
            ("6. Doğrula", "bit-tam, boyut")]
    w, g = 1.42, 0.2
    for k, (ad, alt) in enumerate(adim):
        x = 0.1 + k * (w + g)
        f = FILL[0] if k < 3 else FILL[1]
        e = EDGE[0] if k < 3 else EDGE[1]
        _box(ax, x, 1.4, w, 1.5, ad + "\n" + alt, fill=f, edge=e,
             fs=8.3, bold=False)
        if k < len(adim) - 1:
            _arrow(ax, x + w + 0.02, 2.15, x + w + g - 0.02, 2.15,
                   col=ACCENT, lw=1.3)
    ax.text(5.0, 0.7, "Eğitim masaüstünde, çıkarım MCU üzerinde; "
            "köprü C dizisidir", ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("hat"))


def qformat():
    """Q1.15: 16 bit, isaret + 15 kesir biti."""
    fig, ax = _tuval(9.6, 3.0, 10, 5.0)
    w = 0.56
    x0 = 0.35
    for k in range(16):
        bit = 15 - k
        x = x0 + k * w
        if bit == 15:
            f, e, t = FILL[3], EDGE[3], "S"
        else:
            f, e, t = FILL[0], EDGE[0], "b%d" % bit
        _box(ax, x, 2.0, w - 0.03, 0.9, t, fill=f, edge=e, fs=8.5)
        if bit == 15:
            lab = "-1"
        else:
            lab = "2^%d" % (bit - 15)
        ax.text(x + (w - 0.03) / 2, 1.65, lab, ha="center",
                fontsize=7.5, color=MUTED)
    ax.text(x0 + 0.5 * w, 3.35, "işaret", ha="center", fontsize=8.5,
            color=ACCENT)
    ax.text(x0 + 9 * w, 3.35, "kesir (15 bit): 2^-1 ... 2^-15",
            ha="center", fontsize=9, color=INK)
    ax.text(5.0, 0.9, "değer = -1·S + Σ b_k·2^(k-15)   aralık: "
            "[-1, 1 - 2^-15]", ha="center", fontsize=9.5, color=INK)
    return _save(fig, _yol("qformat"))


def affin():
    """r = S (q - Z): gercek eksen ve tamsayi eksen eslemesi."""
    fig, ax = _tuval(9.6, 4.2, 10, 6.0)
    lo, hi = -0.4, 2.3
    S = (hi - lo) / 255.0
    Z = -90
    gx0, gx1 = 1.0, 9.0          # gercek eksen (lo..hi)
    qx0, qx1 = 1.0, 9.0          # tamsayi eksen (-128..127)
    yr, yq = 4.2, 1.6
    ax.plot([gx0, gx1], [yr, yr], color=ACCENT_L, lw=3)
    ax.plot([qx0, qx1], [yq, yq], color=ACCENT, lw=3)
    ax.text(gx0 - 0.15, yr + 0.35, "gerçek r  (lo = %.1f)" % lo,
            ha="left", fontsize=9.5, color=INK)
    ax.text(gx1 + 0.15, yr + 0.35, "hi = %.1f" % hi, ha="right",
            fontsize=9.5, color=INK)
    ax.text(qx0 - 0.15, yq - 0.6, "q = -128", ha="left",
            fontsize=9.5, color=INK)
    ax.text(qx1 + 0.15, yq - 0.6, "q = 127", ha="right",
            fontsize=9.5, color=INK)
    zx = gx0 + (0 - lo) / (hi - lo) * (gx1 - gx0)
    ax.plot([zx], [yr], "o", color=INK, ms=6)
    ax.text(zx, yr + 0.75, "r = 0", ha="center", fontsize=9.5,
            color=INK)
    qz = qx0 + (Z + 128) / 255.0 * (qx1 - qx0)
    ax.plot([qz], [yq], "s", color=INK, ms=6)
    ax.text(qz, yq - 1.2, "q = Z = %d" % Z, ha="center",
            fontsize=9.5, color=INK)
    for gx, qx in [(gx0, qx0), (gx1, qx1), (zx, qz)]:
        ax.plot([gx, qx], [yr - 0.05, yq + 0.05], ls="--", lw=1.0,
                color=MUTED)
    ax.text(5.0, 0.35, "S = (hi - lo) / 255 = %.5f,   r = S·(q - Z)"
            % S, ha="center", fontsize=10, color=INK)
    return _save(fig, _yol("affin"))


def gemm():
    """int8 katman: birikim, yeniden olcekleme, kirpma."""
    fig, ax = _tuval(9.6, 3.0, 10, 4.4)
    adim = [("x_q\nint8 girdi", FILL[0], EDGE[0]),
            ("W_q\nint8 ağırlık", FILL[0], EDGE[0]),
            ("Birikim\nint32: b + Σ w·x", FILL[2], EDGE[2]),
            ("Yeniden ölçek\n(M0·acc) >> rs", FILL[1], EDGE[1]),
            ("+ Z, kırp\n[-128, 127]", FILL[1], EDGE[1]),
            ("a_q\nint8 çıktı", FILL[0], EDGE[0])]
    w, g = 1.32, 0.27
    for k, (t, f, e) in enumerate(adim):
        x = 0.1 + k * (w + g)
        _box(ax, x, 1.5, w, 1.6, t, fill=f, edge=e, fs=8.5)
        if k < len(adim) - 1:
            _arrow(ax, x + w + 0.02, 2.3, x + w + g - 0.02, 2.3,
                   col=ACCENT, lw=1.3)
    ax.text(5.0, 0.8, "Birikim int32'de yapılır; kayan nokta yalnız "
            "ölçek sabitlerinde (derleme zamanında) bulunur",
            ha="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("gemm"))


def bit_grafik():
    rows = _oku("b46_bit_dogruluk.csv")
    bits = [int(r["bit"]) for r in rows]
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    seri = [("dogruluk_yalniz_agirlik", "yalnız ağırlık", MUTED, "o"),
            ("dogruluk_minmax", "ağırlık+aktivasyon, min/maks", ACCENT,
             "s"),
            ("dogruluk_yuzdelik", "ağırlık+aktivasyon, yüzdelik",
             ACCENT_L, "^")]
    for anahtar, ad, renk, mk in seri:
        y = [float(r[anahtar]) for r in rows]
        ax.plot(bits, y, marker=mk, color=renk, lw=1.8, label=ad)
    ax.set_xlabel("bit genişliği", color=INK)
    ax.set_ylabel("test doğruluğu", color=INK)
    ax.set_xticks(bits)
    ax.set_xlim(8.3, 1.7)
    ax.set_ylim(0.2, 1.02)
    ax.grid(True, color=RULE, lw=0.6)
    ax.legend(fontsize=8.5, frameon=False, loc="lower left")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("bit_dogruluk"))


def butce_grafik():
    rows = _oku("b46_butce.csv")
    rows = [r for r in rows if r["katman"] != "toplam"]
    ad = [r["katman"] for r in rows]
    f32 = [int(r["bayt_f32"]) for r in rows]
    i8 = [int(r["bayt_int8"]) for r in rows]
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    x = np.arange(len(ad))
    ax.bar(x - 0.19, f32, 0.36, color=FILL[0], edgecolor=EDGE[0],
           label="float32")
    ax.bar(x + 0.19, i8, 0.36, color=FILL[3], edgecolor=EDGE[3],
           label="int8 modeli")
    for xi, a, b in zip(x, f32, i8):
        ax.text(xi - 0.19, a + 12, str(a), ha="center", fontsize=8.5)
        ax.text(xi + 0.19, b + 12, str(b), ha="center", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(ad, fontsize=9)
    ax.set_ylabel("bayt", color=INK)
    ax.legend(frameon=False, fontsize=9)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("butce"))


def flash_ram():
    rows = _oku("b46_boyut.csv")
    by = {r["bilesen"]: r for r in rows}
    ad = ["düz C", "DSP (SMLAD)"]
    kod = [int(by["kod_ve_sabitler"]["duz_c_bayt"]),
           int(by["kod_ve_sabitler"]["dsp_bayt"])]
    mdl = [int(by["model_parametreleri"]["duz_c_bayt"]),
           int(by["model_parametreleri"]["dsp_bayt"])]
    orn = [int(by["ornek_pencereler"]["duz_c_bayt"]),
           int(by["ornek_pencereler"]["dsp_bayt"])]
    ram = [int(by["durum_ve_tamponlar"]["duz_c_bayt"]),
           int(by["durum_ve_tamponlar"]["dsp_bayt"])]
    fig, ax = plt.subplots(figsize=(7.6, 3.0))
    y = np.arange(2)
    ax.barh(y, kod, color=FILL[0], edgecolor=EDGE[0], label="kod")
    ax.barh(y, mdl, left=kod, color=FILL[1], edgecolor=EDGE[1],
            label="model parametreleri")
    left2 = [a + b for a, b in zip(kod, mdl)]
    ax.barh(y, orn, left=left2, color=FILL[2], edgecolor=EDGE[2],
            label="örnek pencereler (demo)")
    for yi, k, m, o, r in zip(y, kod, mdl, orn, ram):
        tot = k + m + o
        ax.text(tot + 40, yi, "flash %d B   RAM %d B" % (tot, r),
                va="center", fontsize=9, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(ad, fontsize=9.5)
    ax.set_xlabel("bayt (flash)", color=INK)
    ax.set_xlim(0, 5200)
    ax.invert_yaxis()
    ax.legend(frameon=False, fontsize=8.5, loc="upper center",
              bbox_to_anchor=(0.5, -0.24), ncol=3)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("flash_ram"))


def anomali_grafik():
    rows = _oku("b46_anomali.csv")
    y = np.array([int(r["etiket"]) for r in rows])
    sf = np.array([float(r["skor_f32"]) for r in rows])
    si = np.array([float(r["skor_int8"]) for r in rows])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.6),
                                 gridspec_kw={"width_ratios": [1.2, 1]})
    bins = np.linspace(min(sf), max(sf), 45)
    a1.hist(sf[y == 0], bins=bins, color=EDGE[0], alpha=0.75,
            label="normal")
    a1.hist(sf[y == 1], bins=bins, color=ACCENT, alpha=0.75,
            label="anomali")
    a1.axvline(0.0, color=INK, lw=1.0, ls="--")
    a1.set_xlabel("skor = logit1 - logit0 (float32)", color=INK)
    a1.set_ylabel("pencere sayısı", color=INK)
    a1.legend(frameon=False, fontsize=8.5)
    a2.scatter(sf[y == 0], si[y == 0], s=5, color=EDGE[0], alpha=0.6)
    a2.scatter(sf[y == 1], si[y == 1], s=5, color=ACCENT, alpha=0.6)
    lim = [min(sf.min(), si.min()), max(sf.max(), si.max())]
    a2.plot(lim, lim, color=INK, lw=0.8, ls="--")
    a2.set_xlabel("float32 skoru", color=INK)
    a2.set_ylabel("int8 skoru (dekuantize)", color=INK)
    for a in (a1, a2):
        for sp in ["top", "right"]:
            a.spines[sp].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("anomali"))


def takas():
    """Doğruluk - gecikme - bellek/enerji üçgeni."""
    fig, ax = _tuval(8.4, 5.4, 10, 8.4)
    ucgen = np.array([[5.0, 7.0], [1.2, 1.4], [8.8, 1.4]])
    ax.fill(ucgen[:, 0], ucgen[:, 1], color=FILL[4], alpha=0.6)
    ax.plot(list(ucgen[:, 0]) + [ucgen[0, 0]],
            list(ucgen[:, 1]) + [ucgen[0, 1]],
            color=ACCENT_L, lw=2.0)
    ax.text(5.0, 7.45, "Doğruluk", ha="center", fontsize=12,
            weight="bold", color=INK)
    ax.text(0.6, 0.85, "Gecikme (zaman)", ha="left", fontsize=12,
            weight="bold", color=INK)
    ax.text(9.4, 0.85, "Bellek ve enerji", ha="right", fontsize=12,
            weight="bold", color=INK)
    ax.text(5.0, 4.05, "bit, budama, model boyu\n"
            "takası belirler", ha="center",
            fontsize=9.5, color=INK)
    ax.text(5.0, 2.75, "bit düşer: bellek ve gecikme düşer,",
            ha="center", fontsize=8.6, color=MUTED)
    ax.text(5.0, 2.35, "doğruluk da düşer (ölçüm: 8 -> 2 bit)",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("takas"))


def main():
    yollar = [spektrum(), hat(), qformat(), affin(), gemm(),
              bit_grafik(), butce_grafik(), flash_ram(),
              anomali_grafik(), takas()]
    for p in yollar:
        print(os.path.normpath(p))


if __name__ == "__main__":
    main()
