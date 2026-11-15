# -*- coding: utf-8 -*-
"""Bolum 76 - GPU programlama ve dagitik egitim diyagramlari.

Olcum grafikleri engine/veri/b76_*.csv dosyalarindan okunur; bu CSV'leri
deney betikleri uretir (b76_01 ... b76_09). Kavramsal sekiller veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import math
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _fig, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def kare(ax, x, y, s, renk, kenar=None):
    ax.add_patch(Rectangle((x, y), s, s, facecolor=renk,
                           edgecolor=kenar or EDGE[0], lw=0.6))


# --------------------------------------------------------------------------- #
def cpu_gpu(path):
    fig, ax = _fig(9.6, 4.6)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10)
    ax.text(4.5, 9.3, "CPU: gecikmeyi düşür", ha="center", fontsize=11,
            weight="bold", color=INK)
    for i in range(4):
        _box(ax, 0.8 + i * 2.0, 6.0, 1.7, 2.4, "çekirdek", FILL[0],
             EDGE[0], fs=9)
    _box(ax, 0.8, 3.6, 7.5, 1.9, "büyük önbellek (L2/L3)", FILL[2],
         EDGE[2], fs=10)
    _box(ax, 0.8, 1.0, 7.5, 2.0, "dal tahmini, sıra dışı yürütme", FILL[4],
         EDGE[4], fs=10)
    ax.text(15.0, 9.3, "GPU: verimi büyüt", ha="center", fontsize=11,
            weight="bold", color=INK)
    for r in range(6):
        for c in range(10):
            kare(ax, 11.3 + c * 0.7, 5.9 - r * 0.62, 0.5, FILL[1], EDGE[1])
    _box(ax, 11.3, 1.0, 7.2, 2.0, "global bellek (yüksek bant genişliği)",
         FILL[2], EDGE[2], fs=10)
    ax.text(10.0, 7.6, "SIMT\nwarp = 32", ha="center", va="center",
            fontsize=9, color=MUTED)
    _arrow(ax, 8.9, 5.0, 11.0, 5.0, col=ACCENT, lw=1.2)
    _save(fig, path)
    return path


def izgara_blok_warp(path):
    fig, ax = _fig(9.6, 4.4)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10)
    ax.text(2.6, 9.4, "ızgara (grid)", ha="center", fontsize=11,
            weight="bold", color=INK)
    for r in range(3):
        for c in range(4):
            _box(ax, 0.3 + c * 1.1, 6.6 - r * 1.8, 0.9, 1.3,
                 f"B({c},{r})", FILL[0], EDGE[0], fs=7)
    ax.text(9.2, 9.4, "blok (256 iş parçacığı)", ha="center", fontsize=11,
            weight="bold", color=INK)
    for r in range(4):
        for c in range(8):
            kare(ax, 6.6 + c * 0.56, 6.0 - r * 0.6, 0.46, FILL[2], EDGE[2])
    ax.text(9.2, 3.5, "8 warp × 32 iş parçacığı", ha="center",
            fontsize=9, color=MUTED)
    ax.text(16.2, 9.4, "warp (32 iş parçacığı)", ha="center", fontsize=11,
            weight="bold", color=INK)
    for r in range(2):
        for c in range(16):
            kare(ax, 12.9 + c * 0.38, 6.9 - r * 0.5, 0.32, FILL[3], EDGE[3])
    ax.text(16.2, 5.0, "tüm iş parçacıkları aynı komutu\n"
            "aynı anda yürütür (SIMT)", ha="center", fontsize=9, color=INK)
    _box(ax, 12.9, 1.8, 6.8, 2.4,
         "dallanma: warp içinde iki yol varsa\nher yol sırayla çalışır",
         FILL[4], EDGE[4], fs=9)
    _arrow(ax, 4.9, 6.0, 6.3, 6.0, col=ACCENT, lw=1.2)
    _arrow(ax, 12.0, 6.0, 12.7, 6.0, col=ACCENT, lw=1.2)
    _save(fig, path)
    return path


def bellek_hiyerarsisi(path):
    fig, ax = _fig(9.6, 4.6)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10)
    seviyeler = [
        ("yazmaçlar (kayıt)", "iş parçacığı başına, en hızlı", FILL[0],
         EDGE[0]),
        ("paylaşılan bellek (shared)", "blok içinde, programcı yönetir",
         FILL[1], EDGE[1]),
        ("L1 / L2 önbellek", "donanım yönetir, sektör 32 B", FILL[2],
         EDGE[2]),
        ("global bellek (VRAM)", "6 GB, ölçülen ~280 GB/s", FILL[3],
         EDGE[3]),
        ("ana bellek (CPU, PCIe)", "GPU'dan erişim pahalı", FILL[4],
         EDGE[4]),
    ]
    for k, (ad, not_, f, e) in enumerate(seviyeler):
        y = 8.2 - k * 1.6
        _box(ax, 0.4, y - 0.5, 10.6, 1.0, ad, f, e, fs=10, bold=True)
        ax.text(11.5, y, not_, ha="left", va="center", fontsize=9,
                color=MUTED)
    ax.text(0.4, 0.5, "üstteki katman küçük ve hızlı; alttaki büyük ve yavaş",
            ha="left", fontsize=9, color=INK)
    _save(fig, path)
    return path


def bant_adimli(path):
    veri = oku("b76_bellek_adimli.csv")
    kopya = {r["islem"]: float(r["gbps"]) for r in oku("b76_kopya_bant.csv")}
    s = [int(r["adim"]) for r in veri]
    fay = [float(r["faydali_gbps"]) for r in veri]
    cek = [float(r["cekilen_gbps"]) for r in veri]
    fig, ax = plt.subplots(figsize=(9.2, 4.3))
    ax.plot(s, fay, "o-", color=ACCENT, lw=1.8, label="faydalı bayt (GB/s)")
    ax.plot(s, cek, "s--", color=ACCENT_L, lw=1.8,
            label="çekilen bayt, sektörle (GB/s)")
    ax.axhline(kopya["cihaz_kopya"], color=MUTED, ls=":", lw=1.3,
               label="ölçülen kopya ~%.0f GB/s" % kopya["cihaz_kopya"])
    ax.axhline(336, color=RULE, ls="-", lw=6, alpha=0.4,
               label="teorik tepe ~336 GB/s (genel bilgi)")
    ax.set_xscale("log", base=2)
    ax.set_xticks(s)
    ax.set_xticklabels([str(x) for x in s])
    ax.set_xlabel("adım s (i. iş parçacığı x[i·s] okur)")
    ax.set_ylabel("GB/s")
    ax.set_ylim(0, 380)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8.5, loc="center right", frameon=False,
              bbox_to_anchor=(1.0, 0.42))
    fig.tight_layout()
    _save(fig, path)
    return path


def indirgeme(path):
    veri = [r for r in oku("b76_indirgeme.csv") if r["ms"]]
    ad = [r["varyant"] for r in veri]
    ms = [float(r["ms"]) for r in veri]
    fig, ax = plt.subplots(figsize=(9.2, 3.9))
    renk = [EDGE[3], EDGE[2], EDGE[1], EDGE[0], MUTED][:len(ms)]
    cub = ax.barh(ad, ms, color=renk)
    for b, v in zip(cub, ms):
        ax.text(v + 0.01, b.get_y() + b.get_height() / 2,
                f"{v:.3f} ms", va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("medyan süre (ms), n = 2^24 float32 (64 MB)")
    ax.set_xlim(0, max(ms) * 1.25)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    _save(fig, path)
    return path


def matmul_roofline(path):
    veri = oku("b76_matmul.csv")
    kopya = {r["islem"]: float(r["gbps"]) for r in oku("b76_kopya_bant.csv")}
    bw = kopya["cihaz_kopya"]
    gf = [float(r["gflops"]) for r in veri]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0),
                                 gridspec_kw={"width_ratios": [1, 1.25]})
    renk = [EDGE[3], EDGE[1], EDGE[0]]
    a1.bar(range(len(gf)), gf, color=renk)
    a1.set_xticks(range(len(gf)))
    a1.set_xticklabels(["naif", "tiled\n(T=16)", "cuBLAS"], fontsize=9)
    for i, v in enumerate(gf):
        a1.text(i, v + 120, f"{v:.0f}", ha="center", fontsize=9)
    a1.set_ylabel("GFLOP/s (N = 2048, FP32)")
    a1.set_ylim(0, max(gf) * 1.18)
    a1.grid(axis="y", alpha=0.3)
    x = [0.0625 * 2 ** k for k in range(0, 13)]
    tepe = gf[2]
    a2.plot(x, [min(tepe, bw * xi) for xi in x], color=INK, lw=1.6)
    a2.axhline(tepe, color=MUTED, ls=":", lw=1.2)
    a2.text(0.1, tepe * 1.12, "pratik tepe (cuBLAS ölçümü)", fontsize=8,
            color=MUTED)
    for ai, g, et, c in [(0.25, gf[0], "naif", EDGE[3]),
                         (4.0, gf[1], "tiled", EDGE[1])]:
        a2.scatter([ai], [g], s=60, color=c, zorder=3)
        a2.annotate(et, (ai, g), textcoords="offset points",
                    xytext=(8, -12), fontsize=9)
    a2.set_xscale("log", base=2)
    a2.set_yscale("log")
    a2.set_xlabel("aritmetik yoğunluk (flop/bayt)")
    a2.set_ylabel("GFLOP/s")
    a2.set_xlim(0.0625, 64)
    a2.set_ylim(40, 16000)
    a2.grid(alpha=0.3, which="both")
    fig.tight_layout()
    _save(fig, path)
    return path


def halka(path):
    fig, ax = _fig(9.6, 5.2)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10)
    konum = {0: (10.0, 8.0), 1: (16.0, 5.0), 2: (10.0, 2.0), 3: (4.0, 5.0)}
    for i, (x, y) in konum.items():
        _box(ax, x - 1.4, y - 0.55, 2.8, 1.1, f"düğüm {i}", FILL[0],
             EDGE[0], fs=10, bold=True)
    for i in range(4):
        j = (i + 1) % 4
        (x1, y1), (x2, y2) = konum[i], konum[j]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy)
        ox, oy = 0.5 * dy / n, -0.5 * dx / n
        _arrow(ax, x1 + dx * 0.3 + ox, y1 + dy * 0.3 + oy,
               x2 - dx * 0.3 + ox, y2 - dy * 0.3 + oy, col=ACCENT, lw=1.4)
    ax.text(10.0, 5.0, "her adımda M/N\nparça komşuya", ha="center",
            va="center", fontsize=9, color=MUTED)
    ax.text(10.0, 9.7, "halka: her düğüm yalnızca komşusuna gönderir (N = 4)",
            ha="center", fontsize=10, color=INK, weight="bold")
    ax.text(10.0, 0.3, "1. faz azaltma, N−1 adım; 2. faz dağıtma, N−1 adım;"
            " gönderim 2(N−1)/N·M", ha="center", fontsize=9, color=INK)
    _save(fig, path)
    return path


def zero_bellek(path):
    veri = [r for r in oku("b76_zero.csv") if r["n"] == "4"]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.1))
    for ax, model in zip(axes, ["1.3B", "7B"]):
        satir = [r for r in veri if r["model"] == model]
        x = list(range(4))
        p = [float(r["parametre_gb"]) for r in satir]
        g = [float(r["gradyan_gb"]) for r in satir]
        o = [float(r["optimizer_gb"]) for r in satir]
        ax.bar(x, p, color=FILL[0], edgecolor=EDGE[0], label="parametre")
        ax.bar(x, g, bottom=p, color=FILL[1], edgecolor=EDGE[1],
               label="gradyan")
        alt = [a + b for a, b in zip(p, g)]
        ax.bar(x, o, bottom=alt, color=FILL[2], edgecolor=EDGE[2],
               label="Adam durumu")
        top = [a + b + c for a, b, c in zip(p, g, o)]
        for xi, t in zip(x, top):
            ax.text(xi, t + max(top) * 0.02, f"{t:.1f}", ha="center",
                    fontsize=9)
        ax.axhline(6.0, color=ACCENT, ls="--", lw=1.3)
        ax.text(-0.45, 6.0 + max(top) * 0.02, "6 GB", color=ACCENT,
                fontsize=8.5, ha="left")
        ax.set_xticks(x)
        ax.set_xticklabels(["DDP\n(aşama 0)", "ZeRO-1", "ZeRO-2",
                            "ZeRO-3"], fontsize=9)
        ax.set_title(f"{model} parametre, N = 4", fontsize=10)
        ax.set_ylabel("GPU başına GB (fp32 + Adam)")
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8, frameon=False, loc="upper right")
    fig.tight_layout()
    _save(fig, path)
    return path


def boru_hatti(path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0),
                                 gridspec_kw={"width_ratios": [1.25, 1]})
    p, m = 4, 4
    for s in range(p):
        for j in range(m):
            a1.add_patch(Rectangle((s + j, p - 1 - s), 0.92, 0.8,
                                   facecolor=FILL[2], edgecolor=EDGE[2]))
            a1.text(s + j + 0.46, p - 1 - s + 0.4, f"M{j + 1}", ha="center",
                    va="center", fontsize=8)
    a1.set_xlim(-0.2, p + m)
    a1.set_ylim(-0.3, p + 0.1)
    a1.set_yticks([p - 1 - s + 0.4 for s in range(p)])
    a1.set_yticklabels([f"aşama {s + 1}" for s in range(p)], fontsize=9)
    a1.set_xlabel("zaman dilimi t (ileri geçiş)")
    a1.set_title("p = 4, m = 4: boş hücreler kabarcıktır", fontsize=9.5)
    a1.grid(alpha=0.2)
    veri = [r for r in oku("b76_halka_kabarcik.csv") if r["tur"] == "kabarcik"]
    m_l = [int(r["b"]) for r in veri]
    sim = [float(r["c"]) for r in veri]
    a2.plot(m_l, sim, "o", color=ACCENT, label="ızgara sayımı")
    xs = list(range(1, 33))
    a2.plot(xs, [(4 - 1) / (x + 4 - 1) for x in xs], color=INK, lw=1.2,
            label="(p−1)/(m+p−1)")
    a2.set_xlabel("mikro-batch sayısı m (p = 4)")
    a2.set_ylabel("kabarcık oranı")
    a2.set_xscale("log", base=2)
    a2.set_ylim(0, 0.85)
    a2.grid(alpha=0.3)
    a2.legend(fontsize=8.5, frameon=False)
    fig.tight_layout()
    _save(fig, path)
    return path


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    print(cpu_gpu(os.path.join(GORSEL, "b76_cpu_gpu.png")))
    print(izgara_blok_warp(os.path.join(GORSEL, "b76_izgara_blok_warp.png")))
    print(bellek_hiyerarsisi(os.path.join(GORSEL,
                                          "b76_bellek_hiyerarsisi.png")))
    print(bant_adimli(os.path.join(GORSEL, "b76_adimli_bant.png")))
    print(indirgeme(os.path.join(GORSEL, "b76_indirgeme.png")))
    print(matmul_roofline(os.path.join(GORSEL, "b76_matmul_roofline.png")))
    print(halka(os.path.join(GORSEL, "b76_halka_allreduce.png")))
    print(zero_bellek(os.path.join(GORSEL, "b76_zero_bellek.png")))
    print(boru_hatti(os.path.join(GORSEL, "b76_boru_hatti.png")))
