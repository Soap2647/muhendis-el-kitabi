# -*- coding: utf-8 -*-
"""Bölüm 2 — 'C Dili' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import os

from diagrams import (_fig, _box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def pointer_basics(path):
    """Değişken, adresi ve onu gösteren işaretçi."""
    fig, ax = plt.subplots(figsize=(8.2, 3.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    # bellek şeridi
    ax.text(0.4, 3.45, "BELLEK", fontsize=9, color=MUTED, weight="bold")
    # x değişkeni
    _box(ax, 1.2, 1.6, 2.2, 1.1, "", FILL[0], EDGE[0])
    ax.text(2.3, 2.45, "int x", ha="center", fontsize=10, color=EDGE[0], weight="bold")
    ax.text(2.3, 1.98, "42", ha="center", fontsize=13, color=INK, weight="bold", **MONO)
    ax.text(2.3, 1.28, "adres: 0x7ffe...9c40", ha="center", fontsize=8.3,
            color=MUTED, **MONO)
    # p işaretçisi
    _box(ax, 6.6, 1.6, 2.6, 1.1, "", FILL[3], EDGE[3])
    ax.text(7.9, 2.45, "int *p", ha="center", fontsize=10, color=EDGE[3], weight="bold")
    ax.text(7.9, 1.98, "0x7ffe...9c40", ha="center", fontsize=9.5, color=INK, **MONO)
    ax.text(7.9, 1.28, "adres: 0x7ffe...9c48", ha="center", fontsize=8.3,
            color=MUTED, **MONO)
    # ok: p'nin degeri x'in adresi
    _arrow(ax, 6.55, 2.15, 3.5, 2.15, col=EDGE[3], rad=0.25, lw=1.6)
    ax.text(5.0, 3.0, "p = &x   →   p, x'i \"gösterir\"", ha="center", fontsize=9.5,
            color=INK, style="italic")
    ax.text(5.0, 0.45, "*p ile p'nin gösterdiği kutuya ulaşırsın: *p == 42",
            ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, path)


def pointer_arith(path):
    """int dizisi üzerinde işaretçi aritmetiği: p+1 bir ELEMAN ilerler."""
    fig, ax = plt.subplots(figsize=(8.6, 3.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    vals = [10, 20, 30, 40, 50]
    x0, w, y, h = 1.0, 1.6, 1.7, 1.0
    for i, v in enumerate(vals):
        _box(ax, x0 + i*w, y, w - 0.06, h, str(v), FILL[0], EDGE[0], fs=12, bold=True)
        ax.text(x0 + i*w + (w-0.06)/2, y + h + 0.25, "dizi[%d]" % i,
                ha="center", fontsize=8.6, color=MUTED, **MONO)
        ax.text(x0 + i*w + (w-0.06)/2, y - 0.3, "0x%X" % (0x1000 + 4*i),
                ha="center", fontsize=8.2, color=MUTED, **MONO)
    # p, p+1, p+2 okları
    for k, lab in ((0, "p"), (1, "p+1"), (3, "p+3")):
        cx = x0 + k*w + (w-0.06)/2
        _arrow(ax, cx, 0.85, cx, 1.55, col=EDGE[3], lw=1.5)
        ax.text(cx, 0.55, lab, ha="center", fontsize=9.5, color=EDGE[3],
                weight="bold", **MONO)
    ax.text(5.0, 3.35, "int dizisinde her adım 4 bayt: p+1 \"bir sonraki int\" demek,"
            " bir sonraki bayt değil", ha="center", fontsize=9.3, color=INK,
            style="italic")
    return _save(fig, path)


def string_memory(path):
    """C string'i: char dizisi + '\\0' sonlandırıcı."""
    fig, ax = plt.subplots(figsize=(8.2, 2.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.4); ax.axis("off")
    chars = ["M", "e", "r", "t", "\\0", "?", "?"]
    x0, w, y, h = 1.2, 1.1, 1.2, 1.0
    for i, c in enumerate(chars):
        junk = (c == "?")
        term = (c == "\\0")
        fill = "#FFFFFF" if junk else (FILL[3] if term else FILL[0])
        edge = RULE if junk else (EDGE[3] if term else EDGE[0])
        tcol = MUTED if junk else (EDGE[3] if term else INK)
        _box(ax, x0 + i*w, y, w - 0.08, h, c, fill, edge, fs=11.5, bold=not junk,
             tcol=tcol)
        ax.text(x0 + i*w + (w-0.08)/2, y - 0.3, "[%d]" % i, ha="center",
                fontsize=8.2, color=MUTED, **MONO)
    ax.text(5.0, 2.85, 'char ad[7] = "Mert";   →   strlen(ad) == 4',
            ha="center", fontsize=9.6, color=INK, **MONO)
    ax.text(x0 + 4*w + 0.47, 2.45, "sonlandırıcı", ha="center", fontsize=8.3,
            color=EDGE[3], style="italic")
    ax.text(x0 + 5.5*w + 0.4, 2.45, "kullanılmayan", ha="center", fontsize=8.3,
            color=MUTED, style="italic")
    return _save(fig, path)


def stack_frames(path):
    """Fonksiyon çağrısı sırasında stack: main -> kare_al -> dönüş."""
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.6); ax.axis("off")
    cols = [
        ("1) main çalışıyor", [("main çerçevesi\nn = 5", FILL[0], EDGE[0])]),
        ("2) kare_al(5) çağrıldı", [("kare_al çerçevesi\nx = 5, sonuc = 25\n+ dönüş adresi",
                                     FILL[1], EDGE[1]),
                                    ("main çerçevesi\nn = 5", FILL[0], EDGE[0])]),
        ("3) kare_al döndü", [("main çerçevesi\nn = 5, k = 25", FILL[0], EDGE[0])]),
    ]
    x0s = [0.5, 3.7, 6.9]
    for (title, frames), x0 in zip(cols, x0s):
        ax.text(x0 + 1.3, 5.25, title, ha="center", fontsize=9.3, color=INK,
                weight="bold")
        # taban çizgisi
        y = 0.9
        ax.plot([x0, x0 + 2.6], [y, y], color=MUTED, lw=1.2)
        for text, fill, edge in reversed(frames):
            hh = 1.15 if "\n" not in text or text.count("\n") < 2 else 1.55
            _box(ax, x0, y, 2.6, hh, text, fill, edge, fs=8.4)
            y += hh + 0.12
        ax.annotate("", xy=(x0 - 0.25, 3.6), xytext=(x0 - 0.25, 1.2),
                    arrowprops=dict(arrowstyle="-|>", color=RULE, lw=1))
    ax.text(0.16, 2.4, "büyüme", rotation=90, fontsize=7.8, color=MUTED)
    ax.text(5.0, 0.28, "Her çağrı yığına bir çerçeve ekler; dönüş o çerçeveyi tek hamlede atar.",
            ha="center", fontsize=9.3, color=MUTED, style="italic")
    return _save(fig, path)


def struct_padding(path):
    """struct { char a; int b; char c; } — hizalama ve dolgu baytları."""
    fig, ax = plt.subplots(figsize=(8.6, 2.9))
    ax.set_xlim(0, 13); ax.set_ylim(0, 3.8); ax.axis("off")
    cells = [("a", FILL[0], EDGE[0]), ("dolgu", "#FFFFFF", RULE),
             ("dolgu", "#FFFFFF", RULE), ("dolgu", "#FFFFFF", RULE),
             ("b", FILL[1], EDGE[1]), ("b", FILL[1], EDGE[1]),
             ("b", FILL[1], EDGE[1]), ("b", FILL[1], EDGE[1]),
             ("c", FILL[3], EDGE[3]), ("dolgu", "#FFFFFF", RULE),
             ("dolgu", "#FFFFFF", RULE), ("dolgu", "#FFFFFF", RULE)]
    x0, w, y, h = 0.5, 1.0, 1.5, 1.0
    for i, (lab, fill, edge) in enumerate(cells):
        pad = (lab == "dolgu")
        _box(ax, x0 + i*w, y, w - 0.07, h, "" if pad else lab, fill, edge,
             fs=11, bold=True, tcol=INK if not pad else MUTED)
        if pad:
            ax.text(x0 + i*w + (w-0.07)/2, y + h/2, "×", ha="center", va="center",
                    fontsize=10, color=MUTED)
        ax.text(x0 + i*w + (w-0.07)/2, y - 0.3, str(i), ha="center",
                fontsize=8, color=MUTED, **MONO)
    ax.text(6.5, 3.3, "struct { char a; int b; char c; }   →   sizeof = 12  (1+1+1 = 3 değil!)",
            ha="center", fontsize=9.6, color=INK, **MONO)
    ax.text(6.5, 0.5, "int, 4'ün katı adreste başlamak ister; derleyici araya \"dolgu\" (padding) koyar.",
            ha="center", fontsize=9.2, color=MUTED, style="italic")
    return _save(fig, path)


def dangling_pointer(path):
    """free sonrası sarkan işaretçi."""
    fig, ax = plt.subplots(figsize=(8.2, 3.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    # önce
    ax.text(2.4, 3.5, "free(p) ÖNCESİ", ha="center", fontsize=9.3, color=INK, weight="bold")
    _box(ax, 0.7, 1.7, 1.5, 1.0, "p", FILL[3], EDGE[3], fs=11, bold=True)
    _box(ax, 2.9, 1.7, 1.9, 1.0, "heap bloğu\n[42]", FILL[1], EDGE[1], fs=8.6)
    _arrow(ax, 2.2, 2.2, 2.85, 2.2, col=EDGE[3], lw=1.5)
    # sonra
    ax.text(7.5, 3.5, "free(p) SONRASI", ha="center", fontsize=9.3, color=INK, weight="bold")
    _box(ax, 5.8, 1.7, 1.5, 1.0, "p", FILL[3], EDGE[3], fs=11, bold=True)
    _box(ax, 8.0, 1.7, 1.9, 1.0, "geri verildi\n(artık senin değil)", "#FFFFFF", RULE, fs=8.0,
         tcol=MUTED)
    _arrow(ax, 7.3, 2.2, 7.95, 2.2, col=EDGE[3], lw=1.5)
    ax.plot([8.25, 9.65], [1.85, 2.55], color=EDGE[3], lw=2)
    ax.plot([8.25, 2.55+0.0], [0,0], alpha=0)  # no-op
    ax.plot([9.65, 8.25], [1.85, 2.55], color=EDGE[3], lw=2, alpha=0)
    ax.text(5.0, 0.55, "p hâlâ eski adresi tutuyor → sarkan işaretçi (dangling pointer)."
            "  *p artık tanımsız davranış!", ha="center", fontsize=9.2, color=EDGE[3])
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(pointer_basics(os.path.join(out, "b02_pointer.png")))
    print(pointer_arith(os.path.join(out, "b02_ptr_arith.png")))
    print(string_memory(os.path.join(out, "b02_string.png")))
    print(stack_frames(os.path.join(out, "b02_stack.png")))
    print(struct_padding(os.path.join(out, "b02_struct_pad.png")))
    print(dangling_pointer(os.path.join(out, "b02_dangling.png")))
