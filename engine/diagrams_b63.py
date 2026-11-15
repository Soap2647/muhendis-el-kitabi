# -*- coding: utf-8 -*-
"""Bölüm 63 - Sinir Ağı Sıfırdan diyagramları.

Ölçüm grafikleri engine/veri/b63_*.csv dosyalarını okur (bu dosyalar
temp deneylerinin çıktısıdır). Mimari ve akış şekilleri veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _fig, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fl(rows, k):
    return np.array([float(r[k]) for r in rows])


def algilayici(path):
    nok = oku("b63_algilayici_nokta.csv")
    cizgi = {r["senaryo"]: r for r in oku("b63_algilayici_cizgi.csv")}
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for ax, sen, baslik in ((axs[0], "AND", "AND: doğrusal ayrılabilir"),
                            (axs[1], "XOR", "XOR: ayrılamaz")):
        pts = [r for r in nok if r["senaryo"] == sen]
        for r in pts:
            x, y, t = float(r["x1"]), float(r["x2"]), int(r["y"])
            ax.scatter([x], [y], s=260, c=ACCENT if t else "white",
                       edgecolors=INK, zorder=3)
        if sen == "AND":
            c = cizgi["AND"]
            w1, w2, b = float(c["w1"]), float(c["w2"]), float(c["b"])
            hat = "w = (%.0f, %.0f), b = %.0f" % (w1, w2, b)
        else:
            c = cizgi["XOR_izgara"]
            w1, w2, b = float(c["w1"]), float(c["w2"]), float(c["b"])
            hat = "en iyi çizgi: %s yanlış" % c["hata"]
        xs = np.linspace(-0.3, 1.3, 50)
        if abs(w2) > 1e-9:
            ys = -(w1 * xs + b) / w2
            ax.plot(xs, ys, color=ACCENT_L, lw=1.6)
        ax.set_xlim(-0.4, 1.4)
        ax.set_ylim(-0.4, 1.4)
        ax.set_aspect("equal")
        ax.set_xlabel("x1")
        ax.set_ylabel("x2")
        ax.set_title(baslik, fontsize=11)
        ax.text(0.5, -0.32, hat, ha="center", fontsize=9, color=MUTED)
        ax.grid(color=RULE, lw=0.6)
    fig.tight_layout()
    return _save(fig, path)


def mlp_mimari(path):
    fig, ax = _fig(9.6, 4.6)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    kutular = [
        (0.3, 2.0, "Girdi\nx", "(B, 64)", FILL[0], EDGE[0]),
        (2.6, 2.0, "Doğrusal\n64 → 128", "(B, 128)", FILL[1], EDGE[1]),
        (4.9, 2.0, "ReLU", "(B, 128)", FILL[2], EDGE[2]),
        (7.2, 2.0, "Doğrusal\n128 → 64", "(B, 64)", FILL[1], EDGE[1]),
        (9.5, 2.0, "ReLU", "(B, 64)", FILL[2], EDGE[2]),
        (11.8, 2.0, "Doğrusal\n64 → 10", "(B, 10)", FILL[3], EDGE[3]),
    ]
    for x, y, metin, sekil, f, e in kutular:
        _box(ax, x, y, 1.8, 1.8, metin, fill=f, edge=e, fs=9)
        ax.text(x + 0.9, y - 0.35, sekil, ha="center", fontsize=8.5,
                color=MUTED)
    for i in range(len(kutular) - 1):
        x1 = kutular[i][0] + 1.8
        x2 = kutular[i + 1][0]
        _arrow(ax, x1, 2.9, x2, 2.9, col=INK, lw=1.2)
    ax.text(7.0, 5.0, "Gizli katmanlar: afin dönüşüm + doğrusal olmayan "
            "aktivasyon", ha="center", fontsize=10, color=INK)
    ax.text(7.0, 0.6, "Sapmalar (b) her Doğrusal katmanda vardır; "
            "toplam 17.226 parametre", ha="center", fontsize=9,
            color=MUTED)
    ax.axis("off")
    return _save(fig, path)


def aktivasyon(path):
    rows = oku("b63_aktivasyon.csv")
    x = fl(rows, "x")
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 6.4))
    axs[0, 0].plot(x, fl(rows, "sigmoid"), color=EDGE[0], label="sigmoid")
    axs[0, 0].plot(x, fl(rows, "tanh"), color=EDGE[3], label="tanh")
    axs[0, 1].plot(x, fl(rows, "relu"), color=EDGE[1], label="ReLU")
    axs[0, 1].plot(x, fl(rows, "leaky"), color=EDGE[2], label="Leaky ReLU")
    axs[0, 1].plot(x, fl(rows, "gelu"), color=EDGE[4], label="GELU")
    axs[1, 0].plot(x, fl(rows, "d_sigmoid"), color=EDGE[0],
                   label="sigmoid'")
    axs[1, 0].plot(x, fl(rows, "d_tanh"), color=EDGE[3], label="tanh'")
    axs[1, 1].plot(x, fl(rows, "d_relu"), color=EDGE[1], label="ReLU'")
    axs[1, 1].plot(x, fl(rows, "d_leaky"), color=EDGE[2], label="Leaky'")
    axs[1, 1].plot(x, fl(rows, "d_gelu"), color=EDGE[4], label="GELU'")
    basliklar = ["Değer: sigmoid ve tanh", "Değer: ReLU ailesi",
                 "Türev: sigmoid ve tanh", "Türev: ReLU ailesi"]
    for ax, b in zip(axs.flat, basliklar):
        ax.set_title(b, fontsize=10.5)
        ax.grid(color=RULE, lw=0.6)
        ax.legend(fontsize=8.5, frameon=False)
        ax.axhline(0, color=MUTED, lw=0.5)
    for ax in axs[1]:
        ax.set_xlabel("z")
    fig.tight_layout()
    return _save(fig, path)


def yaklasim(path):
    egri = oku("b63_yaklasim_egri.csv")
    rm = oku("b63_yaklasim_rmse.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    x = fl(egri, "x")
    axs[0].plot(x, fl(egri, "hedef"), color=INK, lw=2.2, label="hedef")
    for k, c in (("h2", EDGE[2]), ("h8", EDGE[1]), ("h32", EDGE[3])):
        axs[0].plot(x, fl(egri, k), color=c, lw=1.2,
                    label="gizli %s" % k[1:])
    axs[0].set_title("Tohum 0: yayılmış kıvrım başlatması", fontsize=10.5)
    axs[0].set_xlabel("x")
    axs[0].set_ylabel("f(x)")
    axs[0].legend(fontsize=8.5, frameon=False)
    axs[0].grid(color=RULE, lw=0.6)
    for baslatma, c, ad in (("sifir_sapma", EDGE[0], "sıfır sapma"),
                            ("yayilmis", EDGE[3], "yayılmış kıvrım")):
        sat = [r for r in rm if r["baslatma"] == baslatma]
        h = fl(sat, "gizli_birim")
        axs[1].errorbar(h, fl(sat, "test_rmse"), yerr=fl(sat, "test_sapma"),
                        color=c, marker="o", capsize=3, label=ad)
    axs[1].set_xscale("log", base=2)
    axs[1].set_xticks([2, 8, 32])
    axs[1].set_xticklabels(["2", "8", "32"])
    axs[1].set_xlabel("gizli birim sayısı")
    axs[1].set_ylabel("dizi RMSE (5 tohum)")
    axs[1].set_title("Kapasite ve başlatma", fontsize=10.5)
    axs[1].legend(fontsize=8.5, frameon=False)
    axs[1].grid(color=RULE, lw=0.6)
    fig.tight_layout()
    return _save(fig, path)


def geri_yayilim(path):
    fig, ax = _fig(9.6, 4.4)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.4)
    ust = [("X\n(B,64)", 0.2), ("Z1 = XW1+b1\n(B,128)", 2.9),
           ("H1 = ReLU(Z1)\n(B,128)", 5.6), ("Z2\n(B,64)", 8.3),
           ("Z3 = logit\n(B,10)", 11.0)]
    for metin, x in ust:
        _box(ax, x, 5.6, 2.3, 1.6, metin, fill=FILL[0], edge=EDGE[0],
             fs=8.5)
    for i in range(len(ust) - 1):
        _arrow(ax, ust[i][1] + 2.3, 6.4, ust[i + 1][1], 6.4, col=INK,
               lw=1.2)
    ax.text(7.0, 7.9, "İleri geçiş: girdiden kayba", ha="center",
            fontsize=10, color=INK)
    alt = [("dL/dZ3 = (P−Y)/B\n(B,10)", 11.0),
           ("dW3 = H2ᵀ δ3\n(64,10)", 8.3),
           ("δ2 = (δ3 W3ᵀ)⊙ReLU'\n(B,64)", 5.6),
           ("dW2 = H1ᵀ δ2\n(128,64)", 2.9),
           ("δ1 = (δ2 W2ᵀ)⊙ReLU'\n(B,128)", 0.2)]
    for metin, x in alt:
        _box(ax, x, 1.2, 2.3, 1.8, metin, fill=FILL[3], edge=EDGE[3],
             fs=7.5)
    for i in range(len(alt) - 1):
        _arrow(ax, alt[i][1], 2.1, alt[i + 1][1] + 2.3, 2.1, col=ACCENT,
               lw=1.2)
    ax.text(7.0, 0.3, "Geri geçiş: kayıptan girdiye; her dW şekli W ile "
            "aynıdır", ha="center", fontsize=9, color=MUTED)
    ax.axis("off")
    return _save(fig, path)


def baslatma(path):
    rows = oku("b63_baslatma_dagilim.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    renk = {"sifir": MUTED, "kucuk": EDGE[0], "buyuk": EDGE[3],
            "xavier": EDGE[2], "he": EDGE[1]}
    for y, c in renk.items():
        sat = [r for r in rows if r["baslatma"] == y]
        katman = np.arange(1, len(sat) + 1)
        std = np.maximum(fl(sat, "std"), 1e-6)
        axs[0].semilogy(katman, std, marker="o", color=c, label=y)
        axs[1].plot(katman, fl(sat, "sifir_orani"), marker="o", color=c,
                    label=y)
    axs[0].set_title("Aktivasyon std (log)", fontsize=10.5)
    axs[0].set_xlabel("gizli katman")
    axs[1].set_title("Sıfır aktivasyon oranı", fontsize=10.5)
    axs[1].set_xlabel("gizli katman")
    axs[1].set_ylim(0, 1)
    for ax in axs:
        ax.set_xticks([1, 2, 3])
        ax.grid(color=RULE, lw=0.6)
        ax.legend(fontsize=8.5, frameon=False, loc="best")
    fig.tight_layout()
    return _save(fig, path)


def egri(path):
    rows = oku("b63_egri.csv")
    ep = fl(rows, "epoch")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    axs[0].plot(ep, fl(rows, "egitim_kayip"), color=EDGE[0],
                label="eğitim kaybı")
    axs[0].plot(ep, fl(rows, "dogrulama_kayip"), color=EDGE[3],
                label="doğrulama kaybı")
    axs[0].set_yscale("log")
    axs[0].set_title("Kayıp (log ölçek)", fontsize=10.5)
    axs[1].plot(ep, fl(rows, "egitim_dogruluk"), color=EDGE[0],
                label="eğitim doğruluğu")
    axs[1].plot(ep, fl(rows, "dogrulama_dogruluk"), color=EDGE[3],
                label="doğrulama doğruluğu")
    axs[1].set_title("Doğruluk", fontsize=10.5)
    for ax in axs:
        ax.set_xlabel("epoch")
        ax.grid(color=RULE, lw=0.6)
        ax.legend(fontsize=8.5, frameon=False)
    fig.tight_layout()
    return _save(fig, path)


def karisiklik(path):
    rows = oku("b63_karisiklik.csv")
    K = np.array([[int(r[k]) for k in r if k != "gercek"] for r in rows])
    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    im = ax.imshow(K, cmap="Greys")
    for i in range(10):
        for j in range(10):
            if K[i, j] > 0:
                ax.text(j, i, str(K[i, j]), ha="center", va="center",
                        fontsize=8, color="white" if K[i, j] > 20 else INK)
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.set_xlabel("tahmin")
    ax.set_ylabel("gerçek")
    ax.set_title("Test kümesi karışıklık matrisi (360 örnek)",
                 fontsize=10.5)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    return _save(fig, path)


def agirlik_pca(path):
    ag = oku("b63_agirlik.csv")
    pc = oku("b63_pca.csv")
    fig = plt.figure(figsize=(9.6, 4.6))
    gs = GridSpec(4, 9, figure=fig, wspace=0.12, hspace=0.25)
    for j in range(16):
        r = ag[j]
        v = np.array([float(r["p%d" % i]) for i in range(64)])
        v = v.reshape(8, 8)
        ax = fig.add_subplot(gs[j // 4, j % 4])
        ax.imshow(v, cmap="RdBu_r",
                  vmin=-np.abs(v).max(), vmax=np.abs(v).max())
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("birim %d" % j, fontsize=7)
    ax2 = fig.add_subplot(gs[:, 5:])
    cmap = plt.cm.tab10.colors
    z = np.array([[float(r["pc1"]), float(r["pc2"]), int(r["sinif"])]
                  for r in pc])
    for c in range(10):
        m = z[:, 2] == c
        ax2.scatter(z[m, 0], z[m, 1], s=10, color=cmap[c],
                    label=str(c))
    ax2.set_title("Gizli temsilin PCA izdüşümü (test)", fontsize=10)
    ax2.set_xlabel("PC1")
    ax2.set_ylabel("PC2")
    ax2.legend(fontsize=7, ncol=2, frameon=False, markerscale=1.5)
    ax2.grid(color=RULE, lw=0.6)
    return _save(fig, path)


def batch(path):
    rows = oku("b63_batch.csv")
    b = fl(rows, "batch")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    axs[0].loglog(b, fl(rows, "epoch_ms"), marker="o", color=EDGE[0])
    axs[0].set_xlabel("batch boyutu")
    axs[0].set_ylabel("bir epoch süresi (ms)")
    axs[0].set_title("Süre (CPU, NumPy)", fontsize=10.5)
    axs[1].semilogx(b, fl(rows, "ornek_s"), marker="o", color=EDGE[1])
    axs[1].set_xlabel("batch boyutu")
    axs[1].set_ylabel("örnek / saniye")
    axs[1].set_title("Verim", fontsize=10.5)
    for ax in axs:
        ax.grid(color=RULE, lw=0.6)
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    yollar = [
        algilayici(os.path.join(GORSEL, "b63_algilayici.png")),
        mlp_mimari(os.path.join(GORSEL, "b63_mlp_mimari.png")),
        aktivasyon(os.path.join(GORSEL, "b63_aktivasyon.png")),
        yaklasim(os.path.join(GORSEL, "b63_yaklasim.png")),
        geri_yayilim(os.path.join(GORSEL, "b63_geri_yayilim.png")),
        baslatma(os.path.join(GORSEL, "b63_baslatma.png")),
        egri(os.path.join(GORSEL, "b63_egri.png")),
        karisiklik(os.path.join(GORSEL, "b63_karisiklik.png")),
        agirlik_pca(os.path.join(GORSEL, "b63_agirlik_pca.png")),
        batch(os.path.join(GORSEL, "b63_batch.png")),
    ]
    for y in yollar:
        print(y)
