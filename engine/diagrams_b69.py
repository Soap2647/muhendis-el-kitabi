# -*- coding: utf-8 -*-
"""Bölüm 69 - Attention & Transformer diyagramları.

Ölçüm grafikleri engine/veri/b69_*.csv dosyalarından okunur. Bu dosyaları
deney betikleri üretir (g01 dk_doyma, g04 pe, g06 uzunluk ve attn_ters,
g08 olcek ve kv). Kavramsal şekiller veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tuval(w=9.6, h=4.0, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def darbogaz(path):
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for ax in (a, b):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 6)
        ax.axis("off")
    # Sol: sabit boyutlu bağlam vektörü
    a.set_title("RNN: tek bağlam vektörü", fontsize=11, color=INK)
    for i in range(4):
        x = 0.4 + i * 1.6
        _box(a, x, 0.6, 1.0, 0.7, "x%d" % (i + 1), fill=FILL[0],
             edge=EDGE[0], fs=10)
        _box(a, x, 2.5, 1.0, 0.7, "h%d" % (i + 1), fill=FILL[2],
             edge=EDGE[2], fs=10)
        _arrow(a, x + 0.5, 1.3, x + 0.5, 2.5, col=MUTED, lw=1.2)
        if i < 3:
            _arrow(a, x + 1.0, 2.85, x + 1.6, 2.85, col=MUTED, lw=1.2)
    _box(a, 2.0, 4.5, 2.8, 0.8, "bağlam c", fill=FILL[3], edge=ACCENT,
         fs=10, bold=True)
    _arrow(a, 5.7, 3.25, 4.8, 4.8, col=ACCENT, lw=1.6, rad=-0.2)
    a.text(0.4, 5.6, "Tüm girdi tek vektöre sıkıştırılır",
           fontsize=9, color=MUTED)
    # Sağ: dikkat, her girdi konumuna doğrudan bağlantı
    b.set_title("Dikkat: her konuma doğrudan bağlantı", fontsize=11,
                color=INK)
    for i in range(4):
        x = 0.4 + i * 1.6
        _box(b, x, 0.6, 1.0, 0.7, "h%d" % (i + 1), fill=FILL[2],
             edge=EDGE[2], fs=10)
    _box(b, 2.0, 4.5, 2.8, 0.8, "sorgu q (adım t)", fill=FILL[0],
         edge=EDGE[0], fs=10)
    agirlik = [0.08, 0.62, 0.2, 0.1]
    for i, w in enumerate(agirlik):
        x = 0.9 + i * 1.6
        _arrow(b, 3.4, 4.5, x, 1.35, col=ACCENT, lw=0.6 + 6 * w, rad=0.0)
        b.text(x + 0.5, 0.2, "α=%.2f" % w, fontsize=8, color=ACCENT,
               ha="center")
    b.text(0.4, 5.6, "Her adımda ağırlıklar yeniden hesaplanır",
           fontsize=9, color=MUTED)
    _save(fig, path)


def akis(path):
    fig, ax = tuval(9.6, 4.3, 14, 6.2)
    _box(ax, 0.3, 2.4, 1.8, 1.2, "X\nT × d", fill=FILL[0], edge=EDGE[0],
         fs=10)
    for y, ad in [(4.6, "W_Q"), (2.8, "W_K"), (1.0, "W_V")]:
        _box(ax, 2.7, y, 1.6, 0.8, ad, fill=FILL[2], edge=EDGE[2], fs=10)
        _arrow(ax, 2.1, 3.0, 2.7, y + 0.4, col=MUTED, lw=1.1)
    _box(ax, 5.0, 4.4, 2.0, 1.0, "Q\nT × d_k", fill=FILL[1], edge=EDGE[1],
         fs=10)
    _box(ax, 5.0, 2.6, 2.0, 1.0, "K\nT × d_k", fill=FILL[1], edge=EDGE[1],
         fs=10)
    _box(ax, 5.0, 0.8, 2.0, 1.0, "V\nT × d_v", fill=FILL[1], edge=EDGE[1],
         fs=10)
    _arrow(ax, 4.3, 4.9, 5.0, 4.9, col=MUTED, lw=1.1)
    _arrow(ax, 4.3, 3.1, 5.0, 3.1, col=MUTED, lw=1.1)
    _arrow(ax, 4.3, 1.3, 5.0, 1.3, col=MUTED, lw=1.1)
    _box(ax, 7.6, 3.2, 2.3, 1.4, "QKᵀ / √d_k\nT × T", fill=FILL[3],
         edge=ACCENT, fs=10, bold=True)
    _arrow(ax, 7.0, 4.6, 7.6, 4.2, col=MUTED, lw=1.1)
    _arrow(ax, 7.0, 3.1, 7.6, 3.6, col=MUTED, lw=1.1)
    _box(ax, 10.6, 3.2, 2.5, 1.4, "softmax (satır)\nA: T × T", fill=FILL[0],
         edge=EDGE[0], fs=10)
    _arrow(ax, 9.9, 3.9, 10.6, 3.9, col=ACCENT, lw=1.6)
    _box(ax, 10.6, 0.6, 2.5, 1.2, "A V\nT × d_v", fill=FILL[3],
         edge=ACCENT, fs=10, bold=True)
    _arrow(ax, 11.85, 3.2, 11.85, 1.8, col=ACCENT, lw=1.6)
    _arrow(ax, 7.0, 1.3, 10.6, 1.2, col=MUTED, lw=1.1)
    ax.text(7.6, 5.4, "Ölçekleme: √d_k ile bölünür", fontsize=9,
            color=MUTED)
    _save(fig, path)


def dk_doyma(path):
    rows = oku("b69_dk_doyma.csv")
    dk = np.array([float(r["dk"]) for r in rows])
    std = np.array([float(r["std_ham"]) for r in rows])
    mo = np.array([float(r["maks_olceksiz"]) for r in rows])
    mc = np.array([float(r["maks_olcekli"]) for r in rows])
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    a.loglog(dk, std, "o-", color=ACCENT, label="ölçeklenmemiş skor (ölçülen)")
    a.loglog(dk, np.sqrt(dk), "--", color=MUTED, label="√d_k (kuram)")
    a.axhline(1.0, color=ACCENT_L, lw=1.2, ls=":",
              label="ölçekli skor için hedef 1")
    a.set_xlabel("d_k", color=INK)
    a.set_ylabel("skor standart sapması", color=INK)
    a.legend(fontsize=8, frameon=False)
    a.set_title("Ham skor √d_k ile büyür", fontsize=10, color=INK)
    b.semilogx(dk, mo, "o-", color=ACCENT, label="ölçeklenmemiş")
    b.semilogx(dk, mc, "s-", color=ACCENT_L, label="ölçekli (÷√d_k)")
    b.set_xlabel("d_k", color=INK)
    b.set_ylabel("satır başına en büyük ağırlık", color=INK)
    b.set_ylim(0, 1.0)
    b.legend(fontsize=8, frameon=False, loc="center right")
    b.set_title("Ölçeksiz softmax doyar", fontsize=10, color=INK)
    for ax in (a, b):
        ax.grid(alpha=0.25, color=RULE)
        ax.tick_params(colors=MUTED, labelsize=8)
    fig.tight_layout()
    _save(fig, path)


def maske(path):
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    cmap = ListedColormap([FILL[3], FILL[1]])
    T = 6
    nedensel = np.tril(np.ones((T, T), dtype=int))
    a.imshow(nedensel, cmap=cmap, vmin=0, vmax=1)
    a.set_title("Nedensel maske (sorgu × anahtar)", fontsize=10, color=INK)
    dolgu = np.zeros((5, 5), dtype=int)
    dolgu[:, :3] = 1
    b.imshow(dolgu, cmap=cmap, vmin=0, vmax=1)
    b.set_title("Dolgu maskesi: uzunluk 3 / 5", fontsize=10, color=INK)
    for ax, m in [(a, nedensel), (b, dolgu)]:
        n, k = m.shape
        for i in range(n):
            for j in range(k):
                ax.text(j, i, "1" if m[i, j] else "−∞", ha="center",
                        va="center", fontsize=7, color=INK)
        ax.set_xticks(np.arange(-0.5, k, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
        ax.grid(which="minor", color=RULE, lw=0.8)
        ax.tick_params(which="both", length=0)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("anahtar j", color=INK, fontsize=9)
        ax.set_ylabel("sorgu i", color=INK, fontsize=9)
    fig.tight_layout()
    _save(fig, path)


def cok_bas(path):
    fig, ax = tuval(9.6, 4.2, 14, 6.2)
    _box(ax, 0.2, 2.2, 1.7, 1.8, "X\nT × d", fill=FILL[0], edge=EDGE[0],
         fs=10)
    basliklar = ["Baş 1", "Baş 2", "Baş 3", "Baş 4"]
    for i, ad in enumerate(basliklar):
        y = 4.8 - i * 1.15
        _box(ax, 2.7, y, 2.7, 0.8,
             ad + ": Q, K, V dilimi\nd_k = d/h", fill=FILL[1],
             edge=EDGE[1], fs=8)
        _arrow(ax, 1.9, 3.1, 2.7, y + 0.4, col=MUTED, lw=1.0)
        _arrow(ax, 5.4, y + 0.4, 6.2, 3.3, col=MUTED, lw=1.0)
    _box(ax, 6.2, 2.4, 1.8, 1.8, "Birleştir\nT × d", fill=FILL[3],
         edge=ACCENT, fs=10, bold=True)
    _box(ax, 8.7, 2.7, 2.0, 1.2, "W_O\nd × d", fill=FILL[2], edge=EDGE[2],
         fs=10)
    _arrow(ax, 8.0, 3.3, 8.7, 3.3, col=MUTED, lw=1.2)
    _box(ax, 11.4, 2.7, 2.3, 1.2, "çıktı\nT × d", fill=FILL[0],
         edge=EDGE[0], fs=10)
    _arrow(ax, 10.7, 3.3, 11.4, 3.3, col=MUTED, lw=1.2)
    ax.text(0.2, 0.6, "Dikkat ağırlıkları başlar arasında paylaşılmaz; "
            "her başın kendi A matrisi vardır.", fontsize=8, color=MUTED)
    _save(fig, path)


def konum_isi(path):
    with open(os.path.join(VERI, "b69_pe.csv"), encoding="utf-8") as f:
        pe = np.array([[float(v) for v in line.strip().split(",")]
                       for line in f if line.strip()])
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    im = ax.imshow(pe, cmap="cividis", aspect="auto", vmin=-1, vmax=1)
    ax.set_xlabel("boyut i (çiftler: sin, cos)", color=INK)
    ax.set_ylabel("konum t", color=INK)
    ax.set_title("Sinüzoidal konum kodlaması PE(t, i)", fontsize=10,
                 color=INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("değer", color=INK)
    ax.tick_params(colors=MUTED, labelsize=8)
    fig.tight_layout()
    _save(fig, path)


def pre_post(path):
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.6))
    for ax in (a, b):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 8.2)
        ax.axis("off")

    def cember(ax, y):
        ax.add_patch(Circle((3.0, y), 0.22, fill=True, facecolor="white",
                            edgecolor=INK, lw=1.0, zorder=5))
        ax.text(3.0, y, "+", ha="center", va="center", fontsize=10,
                color=INK, zorder=6)

    # Post-norm: x -> F(x) -> +x -> LN -> FFN -> +x -> LN
    a.set_title("Post-norm: artık, sonra LayerNorm", fontsize=10,
                color=INK)
    _box(a, 2.0, 0.2, 2.0, 0.6, "girdi x", FILL[0], EDGE[0], fs=9)
    _box(a, 2.0, 1.2, 2.0, 0.6, "attention", FILL[1], EDGE[1], fs=9)
    cember(a, 2.5)
    _box(a, 2.0, 3.2, 2.0, 0.6, "LayerNorm", FILL[2], EDGE[2], fs=9)
    _box(a, 2.0, 4.2, 2.0, 0.6, "MLP (4d)", FILL[1], EDGE[1], fs=9)
    cember(a, 5.0)
    _box(a, 2.0, 6.1, 2.0, 0.6, "LayerNorm", FILL[2], EDGE[2], fs=9)
    _arrow(a, 3.0, 0.8, 3.0, 1.2, col=MUTED, lw=1.1)
    _arrow(a, 3.0, 1.8, 3.0, 2.28, col=MUTED, lw=1.1)
    _arrow(a, 3.0, 2.72, 3.0, 3.2, col=MUTED, lw=1.1)
    _arrow(a, 3.0, 3.8, 3.0, 4.2, col=MUTED, lw=1.1)
    _arrow(a, 3.0, 4.8, 3.0, 5.22, col=MUTED, lw=1.1)
    _arrow(a, 3.0, 5.28, 3.0, 6.1, col=MUTED, lw=1.1)
    # artık yolları
    a.plot([2.0, 1.4, 1.4], [0.5, 0.5, 2.5], color=ACCENT, lw=1.2)
    a.annotate("", xy=(2.78, 2.5), xytext=(1.4, 2.5),
               arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.2))
    a.plot([4.0, 4.6, 4.6], [3.5, 3.5, 5.0], color=ACCENT, lw=1.2)
    a.annotate("", xy=(3.22, 5.0), xytext=(4.6, 5.0),
               arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.2))
    # Pre-norm: x -> LN -> F -> +x -> LN -> MLP -> +x
    b.set_title("Pre-norm: önce LayerNorm, artık yol temiz",
                fontsize=10, color=INK)
    _box(b, 2.0, 0.2, 2.0, 0.6, "girdi x", FILL[0], EDGE[0], fs=9)
    _box(b, 2.0, 1.2, 2.0, 0.6, "LayerNorm", FILL[2], EDGE[2], fs=9)
    _box(b, 2.0, 2.2, 2.0, 0.6, "attention", FILL[1], EDGE[1], fs=9)
    cember(b, 3.5)
    _box(b, 2.0, 4.2, 2.0, 0.6, "LayerNorm", FILL[2], EDGE[2], fs=9)
    _box(b, 2.0, 5.2, 2.0, 0.6, "MLP (4d)", FILL[1], EDGE[1], fs=9)
    cember(b, 6.5)
    _arrow(b, 3.0, 0.8, 3.0, 1.2, col=MUTED, lw=1.1)
    _arrow(b, 3.0, 1.8, 3.0, 2.2, col=MUTED, lw=1.1)
    _arrow(b, 3.0, 2.8, 3.0, 3.28, col=MUTED, lw=1.1)
    _arrow(b, 3.0, 3.72, 3.0, 4.2, col=MUTED, lw=1.1)
    _arrow(b, 3.0, 4.8, 3.0, 5.2, col=MUTED, lw=1.1)
    _arrow(b, 3.0, 5.8, 3.0, 6.28, col=MUTED, lw=1.1)
    b.plot([2.0, 1.2, 1.2], [0.5, 0.5, 3.5], color=ACCENT, lw=1.2)
    b.annotate("", xy=(2.78, 3.5), xytext=(1.2, 3.5),
               arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.2))
    b.plot([3.22, 5.0, 5.0], [3.5, 3.5, 6.5], color=ACCENT, lw=1.2)
    b.annotate("", xy=(3.22, 6.5), xytext=(5.0, 6.5),
               arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.2))
    b.text(0.2, 7.5, "Bordo çizgi: artık yolu, hiçbir işlemden geçmez",
           fontsize=8, color=MUTED)
    _save(fig, path)


def attn_isi(path):
    rows = oku("b69_attn_ters.csv")
    bas = sorted({int(r["bas"]) for r in rows})
    fig, eksen = plt.subplots(2, 2, figsize=(9.6, 6.6))
    im = None
    for k, ax in enumerate(eksen.flat):
        sat = [r for r in rows if int(r["bas"]) == bas[k]]
        n_satir = max(int(r["satir"]) for r in sat) + 1
        n_sut = max(int(r["sutun"]) for r in sat) + 1
        M = np.zeros((n_satir, n_sut))
        for r in sat:
            M[int(r["satir"]), int(r["sutun"])] = float(r["agirlik"])
        im = ax.imshow(M, cmap="cividis", vmin=0, vmax=1, aspect="auto")
        ax.set_title("Çapraz attention, baş %d" % (k + 1), fontsize=10,
                     color=INK)
        ax.set_xlabel("kaynak konumu j", color=INK, fontsize=9)
        ax.set_ylabel("çıktı adımı t", color=INK, fontsize=9)
        ax.tick_params(colors=MUTED, labelsize=8)
    fig.subplots_adjust(hspace=0.5, wspace=0.25, right=0.86)
    fig.colorbar(im, ax=eksen.ravel().tolist(), fraction=0.035,
                 pad=0.03, label="dikkat ağırlığı")
    _save(fig, path)


def uzunluk(path):
    rows = oku("b69_uzunluk.csv")
    modeller = []
    for r in rows:
        if r["model"] not in modeller:
            modeller.append(r["model"])
    stil = {
        "Transformer sinüzoidal": (ACCENT, "o", "-"),
        "Transformer öğrenilen": (EDGE[2], "s", "--"),
        "Transformer RoPE": (EDGE[1], "^", "-."),
        "Transformer konumsuz": (MUTED, "x", ":"),
        "LSTM (dikkatsiz)": (EDGE[0], "D", "-"),
    }
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.axvspan(3.5, 12.5, color=FILL[1], alpha=0.6, zorder=0)
    ax.text(4.0, 1.04, "eğitim aralığı (4–12)", fontsize=8, color=MUTED)
    for m in modeller:
        sat = [r for r in rows if r["model"] == m]
        L = np.array([int(r["L"]) for r in sat])
        ort = np.array([float(r["ortalama"]) for r in sat])
        sd = np.array([float(r["sapma"]) for r in sat])
        renk, mark, ls = stil[m]
        ax.errorbar(L, ort, yerr=sd, color=renk, marker=mark, ls=ls,
                    capsize=3, label=m, lw=1.4, ms=5)
    ax.set_xlabel("test dizisi uzunluğu L", color=INK)
    ax.set_ylabel("dizi düzeyi doğruluk", color=INK)
    ax.set_ylim(-0.03, 1.08)
    ax.set_xticks([4, 8, 12, 16, 20, 24])
    ax.grid(alpha=0.25, color=RULE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.legend(fontsize=8, frameon=False, loc="center right")
    _save(fig, path)


def olcek_kv(path):
    olc = oku("b69_olcek.csv")
    kv = oku("b69_kv.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    T = np.array([float(r["T"]) for r in olc])
    s = np.array([float(r["sure_ms"]) for r in olc])
    a.loglog(T, s, "o-", color=ACCENT, label="ölçülen süre")
    ref = s[-1] * (T / T[-1]) ** 2
    a.loglog(T, ref, "--", color=MUTED, label="T² referansı")
    a.set_xlabel("dizi uzunluğu T", color=INK)
    a.set_ylabel("süre (ms)", color=INK)
    a.set_title("Tek attention katmanı (CPU)", fontsize=10, color=INK)
    a.legend(fontsize=8, frameon=False, loc="upper left")
    N = np.array([float(r["N"]) for r in kv])
    ob = np.array([float(r["onbellegiz_s"]) for r in kv])
    on = np.array([float(r["onbellekli_s"]) for r in kv])
    b.loglog(N, ob, "o-", color=MUTED, label="önbelleksiz")
    b.loglog(N, on, "s-", color=ACCENT, label="KV önbellekli")
    b.set_xlabel("üretilen belirteç sayısı N", color=INK)
    b.set_ylabel("süre (s)", color=INK)
    b.set_title("Otoregresif üretim (CPU, P = 8)", fontsize=10, color=INK)
    b.set_xticks([64, 128, 256, 512])
    b.set_xticklabels(["64", "128", "256", "512"])
    b.minorticks_off()
    b.legend(fontsize=8, frameon=False, loc="upper left")
    for ax in (a, b):
        ax.grid(alpha=0.25, color=RULE, which="both")
        ax.tick_params(colors=MUTED, labelsize=8)
    fig.tight_layout()
    _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    darbogaz(os.path.join(GORSEL, "b69_darbogaz.png"))
    akis(os.path.join(GORSEL, "b69_akis.png"))
    dk_doyma(os.path.join(GORSEL, "b69_dk_doyma.png"))
    maske(os.path.join(GORSEL, "b69_maske.png"))
    cok_bas(os.path.join(GORSEL, "b69_cok_bas.png"))
    konum_isi(os.path.join(GORSEL, "b69_konum_isi.png"))
    pre_post(os.path.join(GORSEL, "b69_pre_post.png"))
    attn_isi(os.path.join(GORSEL, "b69_attn_isi.png"))
    uzunluk(os.path.join(GORSEL, "b69_uzunluk.png"))
    olcek_kv(os.path.join(GORSEL, "b69_olcek_kv.png"))
    print("tamam")
