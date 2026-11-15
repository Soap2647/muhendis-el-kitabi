# -*- coding: utf-8 -*-
"""Bölüm 3 — 'Python' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from diagrams import (_fig, _box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def name_vs_box(path):
    """C'nin kutu modeli vs Python'un isim→nesne modeli."""
    fig, ax = plt.subplots(figsize=(8.8, 3.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.8); ax.axis("off")
    # --- sol: C ---
    ax.text(2.7, 4.45, "C: isim = kutunun adı", ha="center", fontsize=10,
            color=INK, weight="bold")
    _box(ax, 0.7, 2.6, 1.8, 1.0, "42", FILL[0], EDGE[0], fs=13, bold=True)
    ax.text(1.6, 3.85, "int x", ha="center", fontsize=9.5, color=EDGE[0], **MONO)
    _box(ax, 3.0, 2.6, 1.8, 1.0, "42", FILL[0], EDGE[0], fs=13, bold=True)
    ax.text(3.9, 3.85, "int y = x", ha="center", fontsize=9.5, color=EDGE[0], **MONO)
    ax.text(2.7, 2.0, "y = x  →  değer KOPYALANIR,\niki ayrı kutu olur",
            ha="center", fontsize=8.6, color=MUTED)
    # ayırıcı
    ax.plot([6.0, 6.0], [0.6, 4.4], color=RULE, lw=1)
    # --- sağ: Python ---
    ax.text(9.2, 4.45, "Python: isim = nesneye etiket", ha="center", fontsize=10,
            color=INK, weight="bold")
    _box(ax, 8.6, 2.5, 2.3, 1.15, "int nesnesi\n42", FILL[1], EDGE[1], fs=9.5, bold=True)
    _box(ax, 6.7, 3.3, 1.0, 0.7, "x", FILL[3], EDGE[3], fs=11, bold=True)
    _box(ax, 6.7, 2.2, 1.0, 0.7, "y", FILL[3], EDGE[3], fs=11, bold=True)
    _arrow(ax, 7.7, 3.62, 8.55, 3.35, col=EDGE[3], lw=1.5, rad=-0.12)
    _arrow(ax, 7.7, 2.52, 8.55, 2.85, col=EDGE[3], lw=1.5, rad=0.12)
    ax.text(9.2, 1.5, "y = x  →  aynı nesneye İKİNCİ etiket,\nkopya yok",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, path)


def aliasing(path):
    """Aynı listeye iki isim: birinden yapılan değişikliği ikisi de görür."""
    fig, ax = plt.subplots(figsize=(8.8, 3.4))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.4); ax.axis("off")
    # ortak liste nesnesi
    _box(ax, 4.6, 2.5, 3.4, 1.1, "liste nesnesi\n[1, 2, 3, 4]", FILL[1], EDGE[1],
         fs=9.5, bold=True)
    _box(ax, 2.4, 3.1, 1.0, 0.7, "a", FILL[3], EDGE[3], fs=11, bold=True)
    _box(ax, 2.4, 2.1, 1.0, 0.7, "b", FILL[3], EDGE[3], fs=11, bold=True)
    _arrow(ax, 3.4, 3.42, 4.55, 3.2, col=EDGE[3], lw=1.5, rad=-0.1)
    _arrow(ax, 3.4, 2.42, 4.55, 2.8, col=EDGE[3], lw=1.5, rad=0.1)
    ax.text(1.15, 2.75, "b = a", ha="center", fontsize=9.5, color=INK, **MONO)
    ax.text(6.3, 1.85, "b.append(4)  →  a da [1,2,3,4] görür!",
            ha="center", fontsize=9, color=EDGE[3], **MONO)
    # kopya
    _box(ax, 9.3, 2.5, 2.3, 1.1, "AYRI nesne\n[1, 2, 3]", FILL[0], EDGE[0],
         fs=9.5, bold=True)
    _box(ax, 9.9, 1.0, 1.0, 0.7, "c", FILL[3], EDGE[3], fs=11, bold=True)
    _arrow(ax, 10.4, 1.7, 10.4, 2.45, col=EDGE[0], lw=1.5)
    ax.text(10.1, 0.55, "c = a.copy()  →  bağımsız", ha="center", fontsize=8.6,
            color=MUTED, **MONO)
    ax.text(4.0, 4.1, "Takma ad (aliasing): kopya sanıp etiket paylaşmak",
            ha="center", fontsize=10, color=INK, weight="bold")
    return _save(fig, path)


def refcount(path):
    """Referans sayacının yaşam döngüsü."""
    fig, ax = plt.subplots(figsize=(8.8, 3.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.2); ax.axis("off")
    stages = [
        ("x = [...]\ny = x", "sayaç = 2", FILL[1], EDGE[1]),
        ("del x", "sayaç = 1", FILL[2], EDGE[2]),
        ("del y", "sayaç = 0", FILL[3], EDGE[3]),
    ]
    x0 = 0.6
    for i, (op, cnt, fill, edge) in enumerate(stages):
        _box(ax, x0 + i*3.0, 1.7, 1.9, 1.35, "liste\nnesnesi\n%s" % cnt,
             fill, edge, fs=8.8, bold=True)
        ax.text(x0 + i*3.0 + 0.95, 3.55, op, ha="center", fontsize=9,
                color=INK, **MONO)
        if i < 2:
            _arrow(ax, x0 + i*3.0 + 2.0, 2.37, x0 + (i+1)*3.0 - 0.1, 2.37,
                   col=MUTED, lw=1.4)
    _arrow(ax, x0 + 8.0, 2.37, x0 + 9.3, 2.37, col=EDGE[3], lw=1.6)
    ax.text(x0 + 10.3, 2.37, "bellek\nGERİ\nverilir", ha="center", va="center",
            fontsize=8.8, color=EDGE[3], weight="bold")
    ax.text(6.0, 0.6, "Sayaç sıfıra düşen nesneyi Python kendisi yok eder — free() çağıran sensin değil, sayaçtır.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def list_internals(path):
    """C dizisi (değerler bitişik) vs Python listesi (işaretçiler bitişik)."""
    fig, ax = plt.subplots(figsize=(8.8, 4.0))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")
    # C
    ax.text(2.9, 4.8, "C: int dizi[4] — değerler bitişik", ha="center",
            fontsize=9.8, color=INK, weight="bold")
    for i, v in enumerate([10, 20, 30, 40]):
        _box(ax, 0.9 + i*1.25, 3.4, 1.12, 0.85, str(v), FILL[0], EDGE[0],
             fs=10.5, bold=True)
    ax.text(2.9, 2.95, "16 bayt, cache dostu", ha="center", fontsize=8.4, color=MUTED)
    # Python
    ax.text(8.6, 4.8, "Python: list — işaretçiler bitişik", ha="center",
            fontsize=9.8, color=INK, weight="bold")
    for i in range(4):
        _box(ax, 6.6 + i*1.25, 3.4, 1.12, 0.85, "ref", FILL[3], EDGE[3], fs=9)
    # nesneler
    objs_x = [6.2, 7.6, 9.0, 10.4]
    for i, v in enumerate([10, 20, 30, 40]):
        _box(ax, objs_x[i], 1.2, 1.25, 0.95, "int\n%d" % v, FILL[1], EDGE[1], fs=8.6)
        _arrow(ax, 6.6 + i*1.25 + 0.56, 3.35, objs_x[i] + 0.62, 2.2,
               col=EDGE[3], lw=1.2)
    ax.text(8.6, 0.55, "her eleman ayrı bir nesne: esnek ama dolaylı — numpy'ın var olma sebebi (Bölüm 48)",
            ha="center", fontsize=8.4, color=MUTED, style="italic")
    return _save(fig, path)


def generator_memory(path):
    """Liste (hepsi bellekte) vs generator (tek eleman, istek üzerine)."""
    fig, ax = plt.subplots(figsize=(8.8, 3.4))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.4); ax.axis("off")
    ax.text(3.1, 4.0, "[x*x for x in range(6)]", ha="center", fontsize=9.5,
            color=INK, **MONO)
    for i, v in enumerate([0, 1, 4, 9, 16, 25]):
        _box(ax, 0.6 + i*0.95, 2.4, 0.85, 0.8, str(v), FILL[0], EDGE[0], fs=9.5,
             bold=True)
    ax.text(3.1, 1.85, "6 değerin HEPSİ aynı anda bellekte", ha="center",
            fontsize=8.6, color=MUTED)
    ax.plot([6.35, 6.35], [0.7, 4.2], color=RULE, lw=1)
    ax.text(9.3, 4.0, "(x*x for x in range(6))", ha="center", fontsize=9.5,
            color=INK, **MONO)
    _box(ax, 7.4, 2.4, 2.0, 0.9, "generator\n(duraklamış kod)", FILL[4], EDGE[4],
         fs=8.6, bold=True)
    _box(ax, 10.3, 2.4, 0.95, 0.9, "9", FILL[1], EDGE[1], fs=11, bold=True)
    _arrow(ax, 9.45, 2.85, 10.25, 2.85, col=EDGE[4], lw=1.5)
    ax.text(9.85, 3.5, "next()", ha="center", fontsize=8.8, color=EDGE[4], **MONO)
    ax.text(9.3, 1.85, "bellekte TEK değer; sıradaki istenince üretilir",
            ha="center", fontsize=8.6, color=MUTED)
    ax.text(6.3, 0.35, "Milyon satırlık veri işlerken fark budur: GB'lar vs birkaç KB (Bölüm 54'ün temeli)",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(name_vs_box(os.path.join(out, "b03_name_object.png")))
    print(aliasing(os.path.join(out, "b03_aliasing.png")))
    print(refcount(os.path.join(out, "b03_refcount.png")))
    print(list_internals(os.path.join(out, "b03_list_internals.png")))
    print(generator_memory(os.path.join(out, "b03_generator.png")))
