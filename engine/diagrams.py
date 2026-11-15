# -*- coding: utf-8 -*-
"""
Diyagram üretimi (matplotlib). Kitabın renk paletiyle uyumlu, vektörel
görünümlü PNG'ler üretir. İnternetten görsel indirmek yerine her diyagram
içeriğe birebir çizilir: telif temiz, stil tutarlı.

Her fonksiyon bir PNG dosyası yazar ve yolu döndürür.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.font_manager as fm
import os

# palet (kitap motoruyla aynı — v2 "yayınevi": bastırılmış tonlar)
ACCENT  = "#8A2D2B"   # bordo
ACCENT_L= "#3E566B"   # arduvaz
INK     = "#1F1F1D"
MUTED   = "#75716A"
RULE    = "#D8D4CC"
FILL    = ["#EFF1F4", "#EDF1EC", "#F5F1E4", "#F4EAE7", "#EFECF3"]
EDGE    = ["#3E566B", "#47624A", "#8A6B2D", "#8A2D2B", "#5C4A6E"]

_DEJAVU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts",
                       "DejaVuSans.ttf")
try:
    fm.fontManager.addfont(_DEJAVU)
    plt.rcParams["font.family"] = "DejaVu Sans"
except Exception:
    pass
plt.rcParams["font.size"] = 11


def _fig(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, fill=FILL[0], edge=ACCENT, fs=11, tcol=INK, bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.1, edgecolor=edge, facecolor=fill, mutation_aspect=1)
    ax.add_patch(p)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
            color=tcol, weight="bold" if bold else "normal", wrap=True)


def _arrow(ax, x1, y1, x2, y2, col=ACCENT, style="-|>", lw=1.6, rad=0.0):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=16,
                        linewidth=lw, color=col,
                        connectionstyle="arc3,rad=%s" % rad)
    ax.add_patch(a)


def _save(fig, path, dpi=200):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.06,
                facecolor="white")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
def memory_layout(path):
    """Bir sürecin bellek düzeni: yüksek adres -> düşük adres."""
    fig, ax = _fig(6.4, 7.6)
    segs = [
        ("Stack (Yığın)",  "yerel değişkenler, fonksiyon çağrıları\naşağı doğru büyür ↓", FILL[3], EDGE[3]),
        ("↓   ...   ↑",    "boş alan", "#ffffff", RULE),
        ("Heap (Öbek)",    "malloc / new ile ayrılan bellek\nyukarı doğru büyür ↑", FILL[1], EDGE[1]),
        ("BSS / Data",     "global ve static değişkenler", FILL[2], EDGE[2]),
        ("Text (Kod)",     "makine kodu (salt-okunur)", FILL[0], EDGE[0]),
    ]
    y = 8.7
    heights = [1.7, 0.9, 1.7, 1.2, 1.2]
    ax.text(5, 9.5, "Yüksek adres  (0xFFFF…)", ha="center", fontsize=9.5, color=MUTED)
    for (title, sub, fill, edge), h in zip(segs, heights):
        y -= h
        if fill == "#ffffff":            # boş alan (gap) satırı — sade ve ortalı
            ax.text(5, y + (h-0.12)/2, "boş alan  (kullanılmayan)",
                    ha="center", va="center", fontsize=9, color=MUTED, style="italic")
            ax.annotate("", xy=(5, y + h - 0.28), xytext=(5, y + h - 0.02),
                        arrowprops=dict(arrowstyle="-|>", color=EDGE[3], lw=1.3))
            ax.annotate("", xy=(5, y + 0.28), xytext=(5, y + 0.02),
                        arrowprops=dict(arrowstyle="-|>", color=EDGE[1], lw=1.3))
            continue
        _box(ax, 1.2, y, 7.6, h - 0.12, "", fill, edge)
        ax.text(1.5, y + (h-0.12) - 0.28, title, ha="left", va="top",
                fontsize=12, weight="bold", color=edge)
        ax.text(1.5, y + 0.30, sub, ha="left", va="bottom", fontsize=8.6, color=INK)
    ax.text(5, y - 0.35, "Düşük adres  (0x0000…)", ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, path)


def fetch_decode_execute(path):
    """CPU komut döngüsü: fetch -> decode -> execute -> (writeback) döngüsü."""
    fig, ax = _fig(8.6, 3.4)
    labels = ["Fetch\n(Getir)", "Decode\n(Çöz)", "Execute\n(Yürüt)", "Writeback\n(Yaz)"]
    xs = [0.4, 2.85, 5.3, 7.75]
    w, h, y = 2.0, 1.7, 4.6
    for i, (lb, x) in enumerate(zip(labels, xs)):
        _box(ax, x, y, w, h, lb, FILL[i % 5], EDGE[i % 5], fs=11.5, bold=True)
        if i < 3:
            _arrow(ax, x + w, y + h/2, xs[i+1], y + h/2)
    # geri dönüş oku
    _arrow(ax, xs[-1] + w/2, y, xs[0] + w/2, y, col=MUTED, rad=-0.35, lw=1.4)
    ax.text(5.0, 2.7, "bir sonraki komut (PC ← PC + 1)", ha="center",
            fontsize=9, color=MUTED, style="italic")
    ax.set_ylim(2, 7)
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(memory_layout(os.path.join(out, "_ornek_memory.png")))
    print(fetch_decode_execute(os.path.join(out, "_ornek_cpu.png")))
