# -*- coding: utf-8 -*-
"""Bolum 13 - 'Siralama' icin diyagramlar.

Olcum grafigi, bolumdeki C laboratuvarinin (siralama.c, ./siralama olcek)
ciktisindaki sayilardan cizilir. Ornek dizilerin sonuclari, metinde
gosterilenlerle ayni kurallarla bu dosyada hesaplanir.
Olcum ortami: AMD Ryzen 7 6800H, Windows 11, WSL2 gcc 13.3.0 -O2.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
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


def _kutu(ax, x, y, w, h, metin, fill=FILL[0], edge=EDGE[0], fs=9.5,
          bold=False, tcol=INK):
    _box(ax, x - w / 2, y - h / 2, w, h, metin, fill, edge, fs=fs,
         bold=bold, tcol=tcol)


# --------------------------------------------------------------------------- #
def karar_agaci(path):
    """n = 3 için karşılaştırma karar ağacı: 6 yaprak, yükseklik 3."""
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    w, h = 1.7, 0.52
    dugum = [
        (5.0, 5.4, "a < b ?"), (2.6, 4.0, "b < c ?"),
        (8.0, 4.0, "b < c ?"), (3.5, 2.5, "a < c ?"),
        (6.9, 2.5, "a < c ?"),
    ]
    yaprak = [
        (0.9, 2.5, "a < b < c"), (2.4, 1.0, "a < c < b"),
        (4.6, 1.0, "c < a < b"), (6.2, 1.0, "b < a < c"),
        (7.9, 1.0, "b < c < a"), (9.2, 2.5, "c < b < a"),
    ]
    kenar = [
        (5.0, 5.4, 2.6, 4.0, "evet"), (5.0, 5.4, 8.0, 4.0, "hayır"),
        (2.6, 4.0, 0.9, 2.5, "evet"), (2.6, 4.0, 3.5, 2.5, "hayır"),
        (3.5, 2.5, 2.4, 1.0, "evet"), (3.5, 2.5, 4.6, 1.0, "hayır"),
        (8.0, 4.0, 6.9, 2.5, "evet"), (8.0, 4.0, 9.2, 2.5, "hayır"),
        (6.9, 2.5, 6.2, 1.0, "evet"), (6.9, 2.5, 7.9, 1.0, "hayır"),
    ]
    for x1, y1, x2, y2, et in kenar:
        _arrow(ax, x1, y1 - 0.26, x2, y2 + 0.26, col=MUTED, lw=1.2)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.15, my, et, fontsize=8, color=MUTED,
                style="italic", va="center")
    for x, y, t in dugum:
        _kutu(ax, x, y, w, h, t, FILL[0], EDGE[0], fs=10, bold=True)
    for x, y, t in yaprak:
        _kutu(ax, x, y, 1.45, h, t, FILL[1], EDGE[1], fs=9.2, bold=True)
    ax.text(0.2, 0.15,
            "6 yaprak = 3! sıralama; yükseklik >= log2(6) = 2,58, yani 3",
            fontsize=8.6, color=ACCENT, weight="bold")
    return _save(fig, path)


# --------------------------------------------------------------------------- #
def birlestirme(path):
    """Merge sort: [38, 27, 43, 3, 9, 82, 10] bolme ve birlestirme."""
    fig, ax = plt.subplots(figsize=(10.2, 6.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.4, 6.9)
    ax.axis("off")
    seviye = [
        (6.3, [(7.0, 8.0, "38 27 43 3 9 82 10", FILL[0], EDGE[0])]),
        (5.0, [(3.6, 4.6, "38 27 43 3", FILL[1], EDGE[1]),
               (10.2, 3.4, "9 82 10", FILL[1], EDGE[1])]),
        (3.7, [(2.0, 2.2, "38 27", FILL[2], EDGE[2]),
               (4.6, 2.2, "43 3", FILL[2], EDGE[2]),
               (9.0, 2.0, "9 82", FILL[2], EDGE[2]),
               (11.4, 1.4, "10", FILL[2], EDGE[2])]),
        (2.5, [(2.0, 2.2, "27 38", FILL[3], EDGE[3]),
               (4.6, 2.2, "3 43", FILL[3], EDGE[3]),
               (9.0, 2.0, "9 82", FILL[3], EDGE[3]),
               (11.4, 1.4, "10", FILL[3], EDGE[3])]),
        (1.2, [(3.6, 4.6, "3 27 38 43", FILL[4], EDGE[4]),
               (10.2, 3.4, "9 10 82", FILL[4], EDGE[4])]),
        (-0.1, [(7.0, 8.0, "3 9 10 27 38 43 82", FILL[1], EDGE[1])]),
    ]
    # bolme (ust -> alt): gri oklar
    bolme = [(7.0, 6.3, 3.6, 5.0), (7.0, 6.3, 10.2, 5.0),
             (3.6, 5.0, 2.0, 3.7), (3.6, 5.0, 4.6, 3.7),
             (10.2, 5.0, 9.0, 3.7), (10.2, 5.0, 11.4, 3.7)]
    # birlestirme (alt -> ust): bordo oklar
    birlesme = [(2.0, 3.7, 2.0, 2.5), (4.6, 3.7, 4.6, 2.5),
                (9.0, 3.7, 9.0, 2.5), (11.4, 3.7, 11.4, 2.5),
                (2.0, 2.5, 3.6, 1.2), (4.6, 2.5, 3.6, 1.2),
                (9.0, 2.5, 10.2, 1.2), (11.4, 2.5, 10.2, 1.2),
                (3.6, 1.2, 7.0, -0.1), (10.2, 1.2, 7.0, -0.1)]
    for x1, y1, x2, y2 in bolme:
        _arrow(ax, x1, y1 - 0.27, x2, y2 + 0.27, col=MUTED, lw=1.1)
    for x1, y1, x2, y2 in birlesme:
        _arrow(ax, x1, y1 - 0.27, x2, y2 + 0.27, col=ACCENT, lw=1.1)
    for y, grup in seviye:
        for x, w, t, f, e in grup:
            _kutu(ax, x, y, w, 0.52, t, f, e, fs=9.2, bold=True)
    ax.text(0.1, 6.75, "gri: bölme   bordo: birleştirme (sıralı parçalar)",
            fontsize=9.2, color=INK, weight="bold")
    return _save(fig, path)


# --------------------------------------------------------------------------- #
def lomuto(path):
    """Lomuto bolumlemesi: [2, 8, 7, 1, 3, 5, 6, 4], pivot 4."""
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.4)
    ax.axis("off")
    once = [2, 8, 7, 1, 3, 5, 6, 4]
    sonra = [2, 1, 3, 4, 7, 5, 6, 8]
    p = 4
    w, h = 1.0, 0.62
    for satir, (vals, y, baslik) in enumerate([
            (once, 3.0, "bölümleme öncesi (pivot = son eleman 4)"),
            (sonra, 1.2, "bölümleme sonrasi (pivot 4, 3. indekste)")]):
        ax.text(0.1, y + 0.62, baslik, fontsize=9.2, color=INK,
                weight="bold")
        for i, v in enumerate(vals):
            x = 0.9 + i * 1.12
            if satir == 0 and i == 7:
                f, e = FILL[2], EDGE[2]
            elif satir == 1 and i == 3:
                f, e = FILL[2], EDGE[2]
            elif v < p:
                f, e = FILL[1], EDGE[1]
            elif v > p:
                f, e = FILL[3], EDGE[3]
            else:
                f, e = FILL[2], EDGE[2]
            _kutu(ax, x, y, w, h, str(v), f, e, fs=11, bold=True)
    ax.text(0.9, 0.05, "yeşil: < 4     kırmızı: > 4     sarı: pivot",
            fontsize=8.6, color=MUTED)
    return _save(fig, path)


# --------------------------------------------------------------------------- #
def yigin(path):
    """Max-heap ve dizi gosterimi: [16, 14, 10, 8, 7, 9, 3, 2, 4, 1]."""
    dizi = [16, 14, 10, 8, 7, 9, 3, 2, 4, 1]
    konum = {0: (5.0, 5.2), 1: (2.6, 4.0), 2: (7.4, 4.0), 3: (1.3, 2.8),
             4: (3.9, 2.8), 5: (6.2, 2.8), 6: (8.6, 2.8), 7: (0.6, 1.4),
             8: (2.0, 1.4), 9: (3.9, 1.4)}
    fig, ax = plt.subplots(figsize=(9.8, 5.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.0)
    ax.axis("off")
    for i in range(len(dizi)):
        for c in (2 * i + 1, 2 * i + 2):
            if c < len(dizi):
                x1, y1 = konum[i]
                x2, y2 = konum[c]
                _arrow(ax, x1, y1 - 0.3, x2, y2 + 0.3, col=MUTED, lw=1.1)
    for i, v in enumerate(dizi):
        x, y = konum[i]
        _kutu(ax, x, y, 0.8, 0.6, str(v), FILL[0], EDGE[0], fs=10.5,
              bold=True)
        ax.text(x, y - 0.5, "[%d]" % i, fontsize=7.6, color=MUTED,
                ha="center", va="center")
    ax.text(0.1, 5.9, "Max-heap: her ebeveyn çocuklarından büyük",
            fontsize=9.4, color=INK, weight="bold")
    ax.text(7.7, 0.9, "dizi gösterimi:\nebeveyn i, çocuklar 2i+1, 2i+2",
            fontsize=8.2, color=MUTED, va="center")
    return _save(fig, path)


# --------------------------------------------------------------------------- #
def radix(path):
    """LSD radix: birler, onlar, yüzler basamaklarına göre kararlı geçişler."""
    satirlar = [
        ("giriş", [170, 45, 75, 90, 802, 24, 2, 66]),
        ("birler", [170, 90, 802, 2, 24, 45, 75, 66]),
        ("onlar", [802, 2, 24, 45, 66, 170, 75, 90]),
        ("yüzler", [2, 24, 45, 66, 75, 90, 170, 802]),
    ]
    fig, ax = plt.subplots(figsize=(9.8, 4.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    for r, (ad, vals) in enumerate(satirlar):
        y = 4.2 - r * 1.1
        ax.text(0.1, y, ad, fontsize=9.2, color=INK, weight="bold",
                va="center")
        for i, v in enumerate(vals):
            x = 1.9 + i * 1.07
            f, e = (FILL[0], EDGE[0]) if r == 0 else (FILL[1], EDGE[1])
            _kutu(ax, x, y, 0.92, 0.6, str(v), f, e, fs=10, bold=True)
    ax.text(1.9, 0.05, "Her geçiş, bir önceki sırayı o basamağa göre "
            "kararlı dağıtır.", fontsize=8.6, color=MUTED)
    return _save(fig, path)


# --------------------------------------------------------------------------- #
def kararlilik(path):
    """Aynı anahtara sahip kayıtların sırası: kararlı ve kararsız sonuç."""
    giris = ["Ali 3", "Ayse 1", "Mert 3", "Zeynep 1"]
    kararli_s = ["Ayse 1", "Zeynep 1", "Ali 3", "Mert 3"]
    kararsiz_s = ["Ayse 1", "Zeynep 1", "Mert 3", "Ali 3"]
    satirlar = [("giriş", giris, None),
                ("kararlı", kararli_s, [2, 3]),
                ("kararsız", kararsiz_s, [2, 3])]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    for r, (ad, vals, vurgu) in enumerate(satirlar):
        y = 3.5 - r * 1.05
        ax.text(0.1, y, ad, fontsize=9.4, color=INK, weight="bold",
                va="center")
        for i, v in enumerate(vals):
            x = 2.4 + i * 1.95
            f, e = FILL[0], EDGE[0]
            if r > 0 and v.startswith(("Ali", "Mert")):
                f, e = FILL[3], EDGE[3]
            _kutu(ax, x, y, 1.7, 0.55, v, f, e, fs=10, bold=True)
    ax.text(2.4, 0.45, "Anahtarı 3 olan Ali, girişte Mert'ten önce. "
            "Kararlı sonuç bu sırayı korur.", fontsize=8.6, color=MUTED)
    ax.text(2.4, 0.12, "Kararsız sonuç, Mert'i Ali'nin önüne alabilir.",
            fontsize=8.6, color=MUTED)
    return _save(fig, path)


# --------------------------------------------------------------------------- #
def olcum(path):
    """Log-log ölçüm: C laboratuvarı, rastgele girdi (gerçek ölçüm)."""
    n1 = np.array([2000, 4000, 8000, 16000], dtype=float)
    ku = np.array([1.77, 6.98, 29.01, 131.61])
    se = np.array([2.99, 11.99, 49.42, 196.55])
    ek = np.array([0.45, 1.74, 7.14, 29.54])
    n2 = np.array([65536, 131072, 262144, 524288, 1048576], dtype=float)
    bi = np.array([3.77, 8.12, 16.97, 37.01, 77.52])
    hi = np.array([3.99, 7.02, 14.70, 30.65, 69.43])
    yi = np.array([3.40, 7.78, 19.22, 48.61, 132.43])
    ra = np.array([0.93, 1.15, 2.68, 5.39, 13.94])

    def egim(x, y):
        return float(np.polyfit(np.log2(x), np.log2(y), 1)[0])

    from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.2, 4.6))
    for ax, seri, baslik in [
        (a1, [("kabarcık", ku, EDGE[0], "o"), ("seçmeli", se, ACCENT, "s"),
              ("eklemeli", ek, EDGE[1], "^")],
         "O(n^2) grubu, n = 2000 .. 16000"),
        (a2, [("birleştirme", bi, EDGE[0], "o"), ("hızlı-medyan", hi,
                                                   EDGE[2], "s"),
              ("yığın", yi, ACCENT, "^"), ("radix", ra, EDGE[1], "D")],
         "n log n grubu, n = 2^16 .. 2^20"),
    ]:
        for ad, y, c, mk in seri:
            xs = n1 if baslik.startswith("O(n^2)") else n2
            ax.loglog(xs, y, marker=mk, color=c, lw=1.7, ms=4.5,
                      label="%s  (eğim %.2f)" % (ad, egim(xs, y)))
        ax.set_xlabel("n (log ölçek)", color=INK, fontsize=9.2)
        ax.set_title(baslik, color=INK, fontsize=9.6, weight="bold",
                     loc="left")
        ax.legend(frameon=False, fontsize=8.2, loc="upper left")
        _ayar(ax)
        ax.xaxis.set_minor_formatter(NullFormatter())
    a1.set_ylabel("en iyi süre, ms (log ölçek)", color=INK, fontsize=9.2)
    a1.xaxis.set_major_locator(FixedLocator([2000, 4000, 8000, 16000]))
    a1.xaxis.set_major_formatter(FixedFormatter(
        ["2000", "4000", "8000", "16000"]))
    fig.suptitle("Süre eğimleri: n^2 grubu ~2, n log n grubu ~1,0 ile 1,3",
                 color=INK, fontsize=10.2, weight="bold", x=0.02,
                 ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(karar_agaci, "b13_karar_agaci.png"),
                   (birlestirme, "b13_birlestirme.png"),
                   (lomuto, "b13_lomuto.png"),
                   (yigin, "b13_yigin.png"),
                   (radix, "b13_radix.png"),
                   (kararlilik, "b13_kararlilik.png"),
                   (olcum, "b13_olcum.png")]:
        print(fn(os.path.join(out, ad)))
