# -*- coding: utf-8 -*-
"""Bolum 53 - 'Paralel & Eşzamanlı Programlama' diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV'leri okur:
  b53_amdahl_s000.csv, b53_amdahl_s010.csv -> güçlü ölçekleme (olcek.c)
  b53_gustafson_s010.csv                    -> zayıf ölçekleme (olcek.c)
  b53_bant.csv                              -> triad bant genişliği (bant.c)
  b53_gantt.csv                             -> zamanlama (zamanlama.c, p=8)
  b53_blas.csv                              -> NumPy matmul (b53_blas.py)
Diğer şekiller kavramsal ya da bölümdeki değerlerden çizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")
MONO = {"family": "DejaVu Sans Mono"}


def oku(ad):
    """CSV'yi oku; '#' ile başlayan açıklama satırlarını atla."""
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        satirlar = [s for s in f if "," in s and not s.startswith("#")]
    return list(csv.DictReader(satirlar))


def amdahl(s, p):
    return 1.0 / (s + (1.0 - s) / p)


def gustafson(s, p):
    return s + (1.0 - s) * p


# ---------------------------------------------------------------- Şekil 1
def sekil1_esz_par(path):
    """Eşzamanlılık (tek çekirdekte geçişmeli) ve paralellik (iki çekirdek)."""
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.text(0.2, 5.6, "Eşzamanlılık: tek çekirdek, geçişli çalışma",
            fontsize=11, weight="bold", color=INK)
    ax.text(0.2, 2.9, "Paralellik: iki çekirdek, gerçekten aynı anda",
            fontsize=11, weight="bold", color=INK)
    # Tek çekirdek satırı: A ve B dönüşümlü
    ax.text(0.2, 4.7, "çekirdek 0", fontsize=9, color=MUTED)
    dilimler = [("A", 1.8, 0), ("B", 3.6, 1), ("A", 5.4, 0),
                ("B", 7.2, 1), ("A", 9.0, 0), ("B", 10.8, 1)]
    for ad, x, k in dilimler:
        _box(ax, x, 4.35, 1.6, 0.7, "görev " + ad,
             fill=FILL[k], edge=EDGE[k], fs=9)
    # Paralel iki satır
    ax.text(0.2, 2.1, "çekirdek 0", fontsize=9, color=MUTED)
    ax.text(0.2, 1.3, "çekirdek 1", fontsize=9, color=MUTED)
    _box(ax, 1.8, 1.95, 4.8, 0.7, "görev A (tamamı)", fill=FILL[0],
         edge=EDGE[0], fs=9)
    _box(ax, 1.8, 1.15, 4.8, 0.7, "görev B (tamamı)", fill=FILL[1],
         edge=EDGE[1], fs=9)
    ax.text(7.2, 1.5, "Aynı süre içinde iki iş bitiyor.",
            fontsize=9.5, color=INK, va="center")
    ax.text(0.2, 0.25, "Eşzamanlılık bir yapı sorunudur (birden çok iş "
            "ilerliyor); paralellik bir çalıştırma özelliğidir.",
            fontsize=9, color=MUTED)
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 2
def sekil2_amdahl_gustafson(path):
    """Teorik eğriler ve ölçülen noktalar."""
    p = np.linspace(1, 16, 200)
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    ax = axs[0]
    ax.plot(p, p, color=MUTED, lw=1, ls="--", label="ideal (S = p)")
    for s, c in ((0.0, EDGE[0]), (0.10, ACCENT)):
        ax.plot(p, amdahl(s, p), color=c, lw=1.8,
                label=f"Amdahl, s={s:.2f}")
    veri = oku("b53_amdahl_s010.csv")
    px = [float(r["p"]) for r in veri]
    py = [float(r["hizlanma"]) for r in veri]
    ax.scatter(px, py, color=ACCENT, s=22, zorder=5, label="ölçüm, s=0,10")
    ax.set_xlabel("iş parçacığı sayısı p")
    ax.set_ylabel("hızlanma S(p)")
    ax.set_title("Güçlü ölçekleme (sabit iş)", fontsize=10)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    ax = axs[1]
    ax.plot(p, p, color=MUTED, lw=1, ls="--", label="ideal")
    ax.plot(p, gustafson(0.10, p), color=EDGE[0], lw=1.8,
            label="Gustafson, s=0,10")
    veri = oku("b53_gustafson_s010.csv")
    px = [float(r["p"]) for r in veri]
    py = [float(r["olceklenmis_hizlanma"]) for r in veri]
    ax.scatter(px, py, color=ACCENT, s=22, zorder=5, label="ölçüm")
    ax.set_xlabel("iş parçacığı sayısı p")
    ax.set_ylabel("ölçeklenmiş hızlanma")
    ax.set_title("Zayıf ölçekleme (iş p ile büyür)", fontsize=10)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    for a in axs:
        a.grid(alpha=0.25)
    fig.tight_layout()
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 3
def sekil3_olcum_verim(path):
    """Ölçülen hızlanma ve verim: güçlü (s=0; s=0,10) ve zayıf."""
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    ax = axs[0]
    for ad, etiket, c in (("b53_amdahl_s000.csv", "güçlü s=0", EDGE[0]),
                          ("b53_amdahl_s010.csv", "güçlü s=0,10", ACCENT)):
        v = oku(ad)
        p = [float(r["p"]) for r in v]
        ax.plot(p, [float(r["verim"]) for r in v], "o-", ms=3.5,
                color=c, lw=1.5, label=etiket)
    v = oku("b53_gustafson_s010.csv")
    ax.plot([float(r["p"]) for r in v], [float(r["verim"]) for r in v],
            "s-", ms=3.5, color=EDGE[1], lw=1.5, label="zayıf s=0,10")
    ax.axvline(8, color=MUTED, lw=0.8, ls=":")
    ax.text(8.2, 0.12, "8 fiziksel\nçekirdek", fontsize=7.5, color=MUTED)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("p")
    ax.set_ylabel("verim E(p) = S(p)/p")
    ax.set_title("Verim: p arttıkça düşer", fontsize=10)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    ax.grid(alpha=0.25)
    ax = axs[1]
    v = oku("b53_amdahl_s010.csv")
    p = np.array([float(r["p"]) for r in v])
    S = np.array([float(r["hizlanma"]) for r in v])
    p, S = p[1:], S[1:]                  # p=1 için Karp-Flatt tanımsız
    e = (1 / S - 1 / p) / (1 - 1 / p)
    ax.plot(p, e, "o-", ms=4, color=ACCENT, lw=1.6)
    ax.axhline(0.10, color=EDGE[0], lw=1, ls="--")
    ax.text(10, 0.108, "tasarlanan s = 0,10", fontsize=8, color=EDGE[0])
    ax.set_xlabel("p")
    ax.set_ylabel("Karp-Flatt e(p)")
    ax.set_title("Ölçülen seri kesir (Karp-Flatt)", fontsize=10)
    ax.set_ylim(0, 0.2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 4
def sekil4_is_aciklik(path):
    """Paralel toplam için iş-açıklık DAG'ı (8 eleman, 3 seviye)."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    xs = [0.9 + 1.5 * i for i in range(8)]
    # yaprak düğümler: girdi değerleri
    for i, x in enumerate(xs):
        _box(ax, x - 0.55, 0.4, 1.1, 0.6, f"a{i}", fill=FILL[0],
             edge=EDGE[0], fs=9)
    # seviye 1 (4 toplama)
    l1 = [(xs[2*i] + xs[2*i+1]) / 2 for i in range(4)]
    for i, x in enumerate(l1):
        _box(ax, x - 0.55, 2.0, 1.1, 0.6, "+", fill=FILL[1],
             edge=EDGE[1], fs=10, bold=True)
        _arrow(ax, xs[2*i], 1.0, x, 2.0, col=MUTED, lw=1)
        _arrow(ax, xs[2*i+1], 1.0, x, 2.0, col=MUTED, lw=1)
    l2 = [(l1[0] + l1[1]) / 2, (l1[2] + l1[3]) / 2]
    for i, x in enumerate(l2):
        _box(ax, x - 0.55, 3.4, 1.1, 0.6, "+", fill=FILL[2],
             edge=EDGE[2], fs=10, bold=True)
        _arrow(ax, l1[2*i], 2.6, x, 3.4, col=MUTED, lw=1)
        _arrow(ax, l1[2*i+1], 2.6, x, 3.4, col=MUTED, lw=1)
    kok = (l2[0] + l2[1]) / 2
    _box(ax, kok - 0.6, 4.8, 1.2, 0.6, "kök", fill=FILL[3],
         edge=ACCENT, fs=9.5, bold=True)
    _arrow(ax, l2[0], 4.0, kok, 4.8, col=MUTED, lw=1)
    _arrow(ax, l2[1], 4.0, kok, 4.8, col=MUTED, lw=1)
    ax.text(12.3, 5.2, "T1 = 7 toplama\n(tek işlemci)", fontsize=9,
            color=INK, va="center")
    ax.text(12.3, 3.7, "T∞ = 3 seviye\n(sonsuz işlemci)", fontsize=9,
            color=INK, va="center")
    ax.text(12.3, 2.2, "Paralellik\nT1 / T∞ = 7/3 ≈ 2,3", fontsize=9,
            color=INK, va="center")
    ax.text(0.3, 0.05, "Her kutu bir toplama; oklar veri bağımlılığıdır. "
            "Aynı seviyedeki toplamalar bağımsızdır.", fontsize=8.5,
            color=MUTED)
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 5
def sekil5_indirgeme(path):
    """Paralel indirgeme ağacı: 8 elemanın ağaçla toplanması, seviye seviye."""
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    vals = [3, 1, 7, 0, 4, 1, 6, 3]
    xs = [0.9 + 1.6 * i for i in range(8)]
    seviyeler = [vals]
    cur = vals[:]
    while len(cur) > 1:
        cur = [cur[2*i] + cur[2*i+1] for i in range(len(cur) // 2)]
        seviyeler.append(cur)
    yler = [0.5, 1.7, 2.9, 4.1]
    merkezler = [xs]                     # her seviyenin x merkezleri
    for s, y in enumerate(yler):
        m = len(seviyeler[s])
        if s > 0:
            onceki = merkezler[s - 1]
            merkezler.append([(onceki[2*i] + onceki[2*i+1]) / 2
                              for i in range(m)])
        for i in range(m):
            x = merkezler[s][i]
            _box(ax, x - 0.5, y, 1.0, 0.55, str(seviyeler[s][i]),
                 fill=FILL[min(s, 4)], edge=EDGE[min(s, 4)], fs=9.5,
                 bold=(s == len(yler) - 1))
            if s > 0:
                for j in (2*i, 2*i+1):
                    _arrow(ax, merkezler[s-1][j], yler[s-1] + 0.55,
                           x, y, col=MUTED, lw=0.9)
    ax.text(0.2, 5.25, "Seviye 0: yapraklar   |   her seviyede toplamalar "
            "aynı anda yapılır",
            fontsize=9, color=INK)
    ax.text(0.2, 0.05, "8 elemanlı toplam 3 seviyede biter (log2 8 = 3). "
            "Seri toplam 7 adım sürer.", fontsize=8.5, color=MUTED)
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 6
def sekil6_blelloch(path):
    """Blelloch tarama: yukarı süpürme ve aşağı süpürme adımları."""
    # b53_scan.py'nin doğrulanmış izi (girdi [3,1,7,0,4,1,6,3]).
    izler = [
        ("yukari", 1, [3, 4, 7, 7, 4, 5, 6, 9]),
        ("yukari", 2, [3, 4, 7, 11, 4, 5, 6, 14]),
        ("yukari", 4, [3, 4, 7, 11, 4, 5, 6, 25]),
        ("asagi", 4, [3, 4, 7, 0, 4, 5, 6, 11]),
        ("asagi", 2, [3, 0, 7, 4, 4, 11, 6, 16]),
        ("asagi", 1, [0, 3, 4, 11, 11, 15, 16, 22]),
    ]
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    n = 8
    ax.set_xlim(-2.4, n + 0.6)
    ax.set_ylim(-0.4, len(izler) + 0.6)
    ax.axis("off")
    for k, (tur, d, durum) in enumerate(izler):
        y = len(izler) - k - 0.5
        ax.text(-2.3, y, f"{tur}  d={d}", fontsize=8.5, va="center",
                color=INK)
        for i, v in enumerate(durum):
            col = FILL[1] if tur == "yukari" else FILL[2]
            ax.add_patch(Rectangle((i, y - 0.35), 0.9, 0.7, facecolor=col,
                                   edgecolor=RULE, lw=0.8))
            ax.text(i + 0.45, y, str(v), ha="center", va="center",
                    fontsize=8.5, color=INK)
    ax.text(0, len(izler) + 0.25, "indeks 0..7 (sütunlar)", fontsize=8,
            color=MUTED)
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 7
def sekil7_gantt(path):
    """Statik, dinamik ve guided zamanlama: iş parçacığı zaman çizelgesi."""
    v = oku("b53_gantt.csv")
    turler = ["statik", "dinamik8", "guided"]
    fig, axs = plt.subplots(3, 1, figsize=(9.6, 6.0), sharex=True)
    renk = plt.get_cmap("tab10")
    for ax, tur in zip(axs, turler):
        satir = [r for r in v if r["zamanlama"] == tur]
        for r in satir:
            t = int(r["thread"])
            s = float(r["baslangic_ms"])
            e = float(r["bitis_ms"])
            ax.barh(t, e - s, left=s, height=0.8, color=renk(t % 10),
                    edgecolor="none")
        ax.set_yticks(range(8))
        ax.set_ylabel("thread", fontsize=8)
        ax.set_title(tur, fontsize=9, loc="left")
        ax.grid(alpha=0.2, axis="x")
    axs[-1].set_xlabel("zaman (ms)")
    fig.suptitle("p=8, 512 dengesiz iş; boş alan = bekleme",
                 fontsize=10, y=0.995)
    fig.tight_layout()
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 8
def sekil8_bant(path):
    """Triad bant genişliği: çekirdek sayısı arttıkça doyma."""
    v = oku("b53_bant.csv")
    p = [float(r["p"]) for r in v]
    med = [float(r["medyan_gbs"]) for r in v]
    lo = [float(r["min_gbs"]) for r in v]
    hi = [float(r["max_gbs"]) for r in v]
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    ax.fill_between(p, lo, hi, color=FILL[0], edgecolor="none")
    ax.plot(p, med, "o-", ms=4, color=ACCENT, lw=1.7, label="medyan")
    ax.axhline(max(med), color=MUTED, lw=0.8, ls=":")
    ax.text(1.1, max(med) + 0.8, f"doyum ≈ {max(med):.0f} GB/s",
            fontsize=8.5, color=MUTED)
    ax.set_xlabel("iş parçacığı sayısı p")
    ax.set_ylabel("triad bant genişliği (GB/s)")
    ax.set_ylim(0, 40)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout()
    _save(fig, path)


# ---------------------------------------------------------------- Şekil 9
def sekil9_roofline(path):
    """Roofline: bant tavanı, tepe işlem tavanı ve ölçülen noktalar."""
    bant = max(float(r["medyan_gbs"]) for r in oku("b53_bant.csv"))
    blas = oku("b53_blas.csv")
    tepe = max(float(r["gflops"]) for r in blas)
    x = np.logspace(-2, 3, 300)
    y = np.minimum(bant * x, tepe)
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.loglog(x, y, color=INK, lw=2)
    ridge = tepe / bant
    ax.axvline(ridge, color=MUTED, lw=0.8, ls=":")
    ax.text(ridge * 1.1, 2.6, f"köşe\n{ridge:.1f} flop/bayt",
            fontsize=8, color=MUTED)
    tri_ai = 2 / 24
    mm_ai = 2 * 2048**3 / (3 * 2048**2 * 8)
    ax.scatter([tri_ai], [bant * tri_ai], color=ACCENT, s=36, zorder=5)
    ax.text(tri_ai * 1.25, bant * tri_ai * 0.62,
            f"triad (AI=0,083)\n{bant * tri_ai:.1f} GFLOPS",
            fontsize=8, color=ACCENT)
    ax.scatter([mm_ai], [tepe], color=EDGE[0], s=36, zorder=5)
    ax.text(mm_ai * 0.25, tepe * 1.12,
            f"matmul (AI≈{mm_ai:.0f})\n{tepe:.0f} GFLOPS",
            fontsize=8, color=EDGE[0])
    ax.set_xlabel("aritmetik yoğunluk (flop/bayt)")
    ax.set_ylabel("performans (GFLOPS)")
    ax.set_title("Roofline: bellek tavanı ve işlem tavanı", fontsize=10)
    ax.grid(alpha=0.25, which="both")
    ax.set_xlim(0.03, 1000)
    ax.set_ylim(1, 600)
    fig.tight_layout()
    _save(fig, path)


# --------------------------------------------------------------- Şekil 10
def sekil10_cpu_gpu(path):
    """CPU ve GPU mimarisi: az güçlü çekirdek vs çok sayıda hafif iş parçacığı."""
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.4))
    for ax in axs:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
    ax = axs[0]
    ax.text(5, 9.5, "CPU: az sayıda güçlü çekirdek", ha="center",
            fontsize=10, weight="bold", color=INK)
    for i in range(4):
        for j in range(2):
            _box(ax, 0.6 + i * 2.3, 6.2 - j * 2.4, 2.0, 1.9,
                 "çekirdek\nbüyük önbellek\nkontrol", fill=FILL[0],
                 edge=EDGE[0], fs=7)
    _box(ax, 0.6, 0.6, 8.8, 1.2, "paylaşılan L3 ve bellek denetleyicisi",
         fill=FILL[2], edge=EDGE[2], fs=8.5)
    ax = axs[1]
    ax.text(5, 9.5, "GPU: binlerce hafif iş parçacığı", ha="center",
            fontsize=10, weight="bold", color=INK)
    for i in range(4):
        for j in range(3):
            _box(ax, 0.6 + i * 2.3, 5.9 - j * 1.6, 2.0, 1.3,
                 "SM\n(warp)", fill=FILL[1], edge=EDGE[1], fs=7)
    _box(ax, 0.6, 0.6, 8.8, 1.2, "global bellek (yüksek bant, yüksek gecikme)",
         fill=FILL[2], edge=EDGE[2], fs=8.5)
    fig.tight_layout()
    _save(fig, path)


def main():
    os.makedirs(OUT, exist_ok=True)
    sekil1_esz_par(os.path.join(OUT, "b53_esz_par.png"))
    sekil2_amdahl_gustafson(os.path.join(OUT, "b53_amdahl_gustafson.png"))
    sekil3_olcum_verim(os.path.join(OUT, "b53_olcum_verim.png"))
    sekil4_is_aciklik(os.path.join(OUT, "b53_is_aciklik.png"))
    sekil5_indirgeme(os.path.join(OUT, "b53_indirgeme.png"))
    sekil6_blelloch(os.path.join(OUT, "b53_blelloch.png"))
    sekil7_gantt(os.path.join(OUT, "b53_zamanlama_gantt.png"))
    sekil8_bant(os.path.join(OUT, "b53_bant_doyma.png"))
    sekil9_roofline(os.path.join(OUT, "b53_roofline.png"))
    sekil10_cpu_gpu(os.path.join(OUT, "b53_cpu_gpu.png"))


if __name__ == "__main__":
    main()
