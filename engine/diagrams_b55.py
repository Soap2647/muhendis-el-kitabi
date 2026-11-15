# -*- coding: utf-8 -*-
"""Bölüm 55 - ML için Kalkülüs & Otomatik Türev diyagramları.

Ölçüm grafikleri engine/veri/ altındaki CSV dosyalarını okur:
  b55_kayip.csv     MLP eğitim kaybı (şekil 55.7)
  b55_karar.csv     karar sınırı ızgarası (şekil 55.8)
  b55_veri.csv      eğitim verisi (şekil 55.8)
  b55_hiz.csv       skaler ve vektörel dönem süresi (şekil 55.9)
  b55_kaybolan.csv  sigmoid zincirinde gradyan (şekil 55.10)
  b55_graf.csv      hesap grafiği değerleri (şekil 55.4)
Diğer şekiller analitik formüllerle çizilir.
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


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _vir(x):
    # Ondalık virgül (Türkçe yazım)
    return ("%.4f" % x).replace(".", ",")


def sekil_teget(path):
    x = np.linspace(-0.3, 2.3, 300)
    f = x ** 3 - 2 * x
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.plot(x, f, color=EDGE[0], lw=2.2)
    ax.plot(x, x - 2, color=ACCENT, lw=1.6, ls="--")
    ax.plot([1.0], [-1.0], "o", color=ACCENT, ms=7)
    ax.plot([1.4], [1.4 ** 3 - 2.8], "o", color=EDGE[0], ms=6)
    ax.plot([1.4, 1.4], [1.4 - 2, 1.4 ** 3 - 2.8], color=MUTED, lw=1.2)
    ax.text(1.02, -1.45, "(1, −1): f(1) = −1", color=INK, fontsize=10)
    ax.text(1.55, -2.35, "teğet: y = x − 2 (eğim f′(1) = 1)", color=ACCENT,
            fontsize=10)
    ax.text(1.44, -0.25, "gerçek fark", color=MUTED, fontsize=9)
    ax.text(0.0, 2.6, "f(x) = x³ − 2x", color=EDGE[0], fontsize=11,
            weight="bold")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.axhline(0, color=RULE, lw=0.8)
    ax.axvline(0, color=RULE, lw=0.8)
    ax.set_ylim(-3, 3.2)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    _save(fig, path)


def sekil_zincir(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 0.4, 3.6, 2.0, 1.2, "girdi\nx", fill=FILL[0], edge=EDGE[0])
    _box(ax, 4.2, 3.6, 3.2, 1.2, "iç fonksiyon\nu = h(x) = x²",
         fill=FILL[1], edge=EDGE[1], fs=10)
    _box(ax, 9.4, 3.6, 3.6, 1.2, "dış fonksiyon\nf = g(u) = sin u",
         fill=FILL[2], edge=EDGE[2], fs=10)
    _arrow(ax, 2.4, 4.2, 4.2, 4.2)
    _arrow(ax, 7.4, 4.2, 9.4, 4.2)
    ax.text(3.3, 4.6, "h′(x) = 2x", ha="center", color=ACCENT, fontsize=10)
    ax.text(8.4, 4.6, "g′(u) = cos u", ha="center", color=ACCENT,
            fontsize=10)
    _box(ax, 3.2, 1.0, 7.6, 1.5,
         "df/dx = g′(h(x)) · h′(x) = cos(x²) · 2x",
         fill=FILL[4], edge=ACCENT, fs=11, bold=True)
    ax.text(0.4, 2.9, "ileri geçiş: değerler soldan sağa; geri geçiş: "
            "türevler sağdan sola çarpılır", color=MUTED, fontsize=9)
    _save(fig, path)


def sekil_karsilastirma(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.axis("off")
    satirlar = [
        ["Yöntem", "Sonuç", "Doğruluk", "Maliyet (n girdi)", "Risk"],
        ["Sembolik", "Kapalı ifade", "Tam (kesin)", "İfade şişebilir",
         "Ağ büyüyünce\nifade patlar"],
        ["Sayısal (fark)", "Yaklaşık sayı", "Yuvarlama\nhatası",
         "n + 1 ileri geçiş", "h seçimi\nhassas"],
        ["Otomatik (ters)", "Sayı, her\nçalıştırmada", "Makine\nkesinliği",
         "~1 ileri + 1 geri\n(skaler çıktı)", "Kontrol akışı\nile uyumlu"],
    ]
    tablo = ax.table(cellText=satirlar, loc="center", cellLoc="left")
    tablo.auto_set_font_size(False)
    tablo.set_fontsize(10)
    tablo.scale(1.0, 2.3)
    for (r, c), hucre in tablo.get_celld().items():
        hucre.set_edgecolor(RULE)
        if r == 0:
            hucre.set_facecolor(ACCENT_L)
            hucre.set_text_props(color="white", weight="bold")
        elif r == 3:
            hucre.set_facecolor(FILL[1])
        else:
            hucre.set_facecolor("white")
    _save(fig, path)


def sekil_hesap_grafi(path):
    veri = {r["ad"]: r for r in _oku("b55_graf.csv")}

    def yazi(ad, baslik):
        r = veri[ad]
        return "%s\nveri %s\ngrad %s" % (baslik, _vir(float(r["veri"])),
                                         _vir(float(r["grad"])))

    fig, ax = plt.subplots(figsize=(9.6, 4.9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")
    konum = {"a": (0.8, 4.2), "b": (0.8, 1.2), "c": (3.9, 2.6),
             "t": (6.6, 2.6), "s": (3.9, 5.6), "f": (9.6, 4.2)}
    basliklar = {"a": "a (girdi)", "b": "b (girdi)", "c": "c = a·b",
                 "t": "t = tanh(c)", "s": "s = a + b", "f": "f = s·t"}
    for ad, (x, y) in konum.items():
        dolgu = FILL[0] if ad in "ab" else FILL[2] if ad == "f" else FILL[1]
        _box(ax, x - 0.1, y - 0.55, 2.4, 1.2, yazi(ad, basliklar[ad]),
             fill=dolgu, edge=EDGE[0], fs=9)
    # İleri kenarlar (düz)
    for kaynak, hedef in [("a", "c"), ("b", "c"), ("c", "t"), ("a", "s"),
                          ("b", "s"), ("s", "f"), ("t", "f")]:
        x1, y1 = konum[kaynak][0] + 2.3, konum[kaynak][1]
        x2, y2 = konum[hedef][0] - 0.1, konum[hedef][1]
        _arrow(ax, x1, y1, x2, y2, col=EDGE[0], lw=1.1)
    ax.text(0.2, 6.6, "ileri geçiş: değerler soldan sağa",
            color=EDGE[0], fontsize=10)
    ax.text(0.2, 0.2, "geri geçiş: grad değerleri sağdan sola, "
            "çıkış grad = 1", color=ACCENT, fontsize=10)
    fig.tight_layout()
    _save(fig, path)


def sekil_maliyet(path):
    n = np.arange(1, 51)
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.plot(n, n, color=EDGE[0], lw=2.0,
            label="ileri mod, m = 1: n geçiş")
    ax.plot(n, np.ones_like(n), color=ACCENT, lw=2.0,
            label="ters mod, m = 1: 1 geri geçiş")
    ax.plot(n, np.full_like(n, 10), color=EDGE[1], lw=1.6, ls="--",
            label="ters mod, m = 10: 10 geri geçiş")
    ax.set_xlabel("girdi sayısı n (parametre sayısı)")
    ax.set_ylabel("geçiş sayısı")
    ax.set_title("Jacobian satırları için maliyet", color=INK, fontsize=11)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_xlim(1, 50)
    ax.set_ylim(0, 52)
    _save(fig, path)


def sekil_birikim(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 0.6, 3.6, 1.8, 1.0, "a = 2", fill=FILL[0], edge=EDGE[0],
         bold=True)
    _box(ax, 0.6, 0.9, 1.8, 1.0, "b = 3", fill=FILL[0], edge=EDGE[0],
         bold=True)
    _box(ax, 4.6, 2.2, 2.2, 1.2, "m = a·b = 6", fill=FILL[1],
         edge=EDGE[1], bold=True)
    _box(ax, 8.6, 2.2, 2.6, 1.2, "f = m + a = 8", fill=FILL[2],
         edge=EDGE[2], bold=True)
    _arrow(ax, 2.4, 4.1, 4.6, 3.0, col=EDGE[0])
    _arrow(ax, 2.4, 1.4, 4.6, 2.4, col=EDGE[0])
    _arrow(ax, 6.8, 2.8, 8.6, 2.8, col=EDGE[0])
    _arrow(ax, 2.4, 4.4, 8.6, 3.4, col=ACCENT, rad=-0.35)
    ax.text(2.7, 3.05, "yol 1 (a→m→f): b·1 = 3", color=MUTED, fontsize=9,
            ha="left")
    ax.text(6.0, 5.4, "yol 2 (a→f, doğrudan): 1", color=ACCENT, fontsize=10,
            ha="center")
    _box(ax, 2.4, 0.0, 7.6, 0.75,
         "a.grad = 3 + 1 = 4   (+= ile; = yazılsaydı yalnızca 1 ya da 3)",
         fill=FILL[4], edge=ACCENT, fs=9.5, bold=True)
    _save(fig, path)


def sekil_kayip(path):
    veri = _oku("b55_kayip.csv")
    d = [int(r["donem"]) for r in veri]
    k = [float(r["kayip"]) for r in veri]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.plot(d, k, color=EDGE[0], lw=2.0)
    ax.set_xlabel("dönem (tam parti gradyan inişi)")
    ax.set_ylabel("ortalama kare hata kaybı")
    ax.set_title("Skaler motorla eğitilen MLP: kayıp eğrisi", color=INK,
                 fontsize=11)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.annotate("son: %s" % _vir(k[-1]), xy=(d[-1], k[-1]),
                xytext=(d[-1] - 110, k[-1] + 0.35), color=ACCENT,
                fontsize=9, arrowprops=dict(arrowstyle="->", color=ACCENT))
    _save(fig, path)


def sekil_karar(path):
    grid = _oku("b55_karar.csv")
    x1 = sorted({float(r["x1"]) for r in grid})
    x2 = sorted({float(r["x2"]) for r in grid})
    Z = np.array([float(r["cikis"]) for r in grid]).reshape(len(x1),
                                                           len(x2))
    XX, YY = np.meshgrid(x1, x2, indexing="ij")
    veri = _oku("b55_veri.csv")
    pozitif = [(float(r["x1"]), float(r["x2"])) for r in veri
               if float(r["y"]) > 0]
    negatif = [(float(r["x1"]), float(r["x2"])) for r in veri
               if float(r["y"]) < 0]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.contourf(XX, YY, Z, levels=[-99, 0, 99],
                colors=[FILL[2], FILL[0]], alpha=0.9)
    ax.contour(XX, YY, Z, levels=[0], colors=[INK], linewidths=1.4)
    p = np.array(pozitif)
    q = np.array(negatif)
    ax.scatter(p[:, 0], p[:, 1], s=18, color=EDGE[1], label="y = +1")
    ax.scatter(q[:, 0], q[:, 1], s=18, color=ACCENT, label="y = −1")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_title("Karar sınırı: kendi motorla eğitilmiş MLP",
                 color=INK, fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    _save(fig, path)


def sekil_hiz(path):
    veri = {r["yontem"]: float(r["donem_saniye"]) for r in _oku(
        "b55_hiz.csv")}
    ad = ["skaler (Deger)", "vektörel (NumPy)"]
    deg = [veri["skaler"], veri["vektorel"]]
    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    cub = ax.bar(ad, deg, color=[EDGE[0], ACCENT], width=0.5)
    ax.set_yscale("log")
    ax.set_ylabel("bir dönem süresi (s, log ölçek)")
    ax.set_title("Aynı MLP, aynı veri, aynı ağırlıklar", color=INK,
                 fontsize=11)
    ax.grid(axis="y", color=RULE, lw=0.5, alpha=0.6)
    for c, v in zip(cub, deg):
        ax.text(c.get_x() + c.get_width() / 2, v * 1.25,
                (("%.4f s" if v > 0.001 else "%.6f s") % v).replace(".", ","),
                ha="center",
                fontsize=10, color=INK)
    ax.text(0.78, 0.55, "fark: yaklaşık %d kat\n(makineye bağlı)"
            % round(deg[0] / deg[1]), transform=ax.transAxes,
            ha="center", color=ACCENT, fontsize=10)
    _save(fig, path)


def sekil_kaybolan(path):
    veri = _oku("b55_kaybolan.csv")
    n = [int(r["derinlik"]) for r in veri]
    g = [float(r["otomatik"]) for r in veri]
    ust = [0.25 ** k for k in n]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.semilogy(n, g, "o-", color=EDGE[0], ms=4, lw=1.6,
                label="dh_n/dx (otomatik)")
    ax.semilogy(n, ust, "--", color=ACCENT, lw=1.3,
                label="üst sınır 0,25ⁿ")
    ax.set_xlabel("sigmoid katman sayısı n")
    ax.set_ylabel("girdiye göre gradyan (log ölçek)")
    ax.set_title("Sigmoid zincirinde kaybolan gradyan (x = 0,5)",
                 color=INK, fontsize=11)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    _save(fig, path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sekil_teget(os.path.join(OUT, "b55_teget.png"))
    sekil_zincir(os.path.join(OUT, "b55_zincir_akis.png"))
    sekil_karsilastirma(os.path.join(OUT, "b55_turev_yontemleri.png"))
    sekil_hesap_grafi(os.path.join(OUT, "b55_hesap_grafi.png"))
    sekil_maliyet(os.path.join(OUT, "b55_ileri_ters_maliyet.png"))
    sekil_birikim(os.path.join(OUT, "b55_gradyan_birikimi.png"))
    sekil_kayip(os.path.join(OUT, "b55_kayip_egrisi.png"))
    sekil_karar(os.path.join(OUT, "b55_karar_siniri.png"))
    sekil_hiz(os.path.join(OUT, "b55_hiz.png"))
    sekil_kaybolan(os.path.join(OUT, "b55_kaybolan_gradyan.png"))
    print("tamam")
