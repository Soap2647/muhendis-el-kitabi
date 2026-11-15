# -*- coding: utf-8 -*-
"""Bölüm 4 — 'Terminal & Araçlar' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
import os

from diagrams import (_fig, _box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def fs_tree(path):
    """Linux dizin ağacının önemli durakları."""
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 10); ax.axis("off")
    _box(ax, 0.5, 8.6, 1.0, 0.9, "/", FILL[3], EDGE[3], fs=13, bold=True)
    ax.text(1.9, 9.05, "kök: her şey buradan dallanır", fontsize=8.6,
            color=MUTED, va="center", style="italic")
    rows = [
        ("bin",  None),
        ("etc",  "sistem ayar dosyaları"),
        ("home", None),               # açıklaması mert kutusundan sonra
        ("usr",  "kurulu yazılımlar, kütüphaneler"),
        ("tmp",  "geçici dosyalar (yeniden başlatınca uçar)"),
        ("dev",  "aygıtlar: diskler, terminaller — dosya gibi!"),
        ("var",  "loglar, değişken veriler (/var/log)"),
    ]
    anno = {"bin": "temel komutlar (ls, cp, bash)"}
    trunk_x = 1.0
    y = 8.0
    for ad, acik in rows:
        y -= 1.02
        ax.plot([trunk_x, trunk_x], [y + 0.45, 8.55], color=RULE, lw=1.2, zorder=0)
        ax.plot([trunk_x, 1.7], [y + 0.45, y + 0.45], color=RULE, lw=1.2, zorder=0)
        _box(ax, 1.7, y, 1.6, 0.82, "/" + ad, FILL[0], EDGE[0], fs=10, bold=True)
        if ad == "home":
            # /home'un çocuğu aynı satırda sağda: /home/mert
            ax.plot([3.3, 3.9], [y + 0.41, y + 0.41], color=EDGE[1], lw=1.2, zorder=0)
            _box(ax, 3.9, y, 2.1, 0.82, "/home/mert", FILL[1], EDGE[1],
                 fs=9.5, bold=True)
            ax.text(6.25, y + 0.41, "senin evin — kısaltması:  ~",
                    fontsize=8.8, color=MUTED, va="center")
        elif acik:
            ax.text(3.6, y + 0.41, acik, fontsize=8.8, color=MUTED, va="center")
        elif ad in anno:
            ax.text(3.6, y + 0.41, anno[ad], fontsize=8.8, color=MUTED, va="center")
    return _save(fig, path)


def streams_pipe(path):
    """stdin/stdout/stderr ve boru hattı."""
    fig, ax = plt.subplots(figsize=(8.8, 3.9))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.4); ax.axis("off")
    # üst: üç akış
    _box(ax, 4.4, 3.6, 3.0, 1.1, "program\n(süreç)", FILL[0], EDGE[0], fs=9.5, bold=True)
    _arrow(ax, 1.9, 4.15, 4.35, 4.15, col=EDGE[1], lw=1.6)
    ax.text(1.7, 4.15, "klavye", ha="right", va="center", fontsize=9, color=EDGE[1])
    ax.text(3.1, 4.42, "stdin (0)", ha="center", fontsize=8.4, color=EDGE[1], **MONO)
    _arrow(ax, 7.4, 4.35, 9.9, 4.35, col=EDGE[0], lw=1.6)
    ax.text(10.1, 4.35, "ekran", ha="left", va="center", fontsize=9, color=EDGE[0])
    ax.text(8.6, 4.62, "stdout (1)", ha="center", fontsize=8.4, color=EDGE[0], **MONO)
    _arrow(ax, 7.4, 3.85, 9.9, 3.55, col=EDGE[3], lw=1.6)
    ax.text(10.1, 3.5, "ekran (hatalar)", ha="left", va="center", fontsize=9, color=EDGE[3])
    ax.text(8.6, 3.4, "stderr (2)", ha="center", fontsize=8.4, color=EDGE[3], **MONO)
    # alt: boru
    ax.text(6.0, 2.55, 'ls -l  |  grep ".c"     — boru: soldakinin stdout\'u sağdakinin stdin\'i olur',
            ha="center", fontsize=9.2, color=INK, **MONO)
    _box(ax, 1.6, 0.7, 2.2, 1.0, "ls -l", FILL[0], EDGE[0], fs=10, bold=True)
    _box(ax, 5.0, 0.7, 1.9, 1.0, "boru\n(pipe)", FILL[2], EDGE[2], fs=8.8, bold=True)
    _box(ax, 8.0, 0.7, 2.4, 1.0, 'grep ".c"', FILL[0], EDGE[0], fs=10, bold=True)
    _arrow(ax, 3.8, 1.2, 4.95, 1.2, col=MUTED, lw=1.6)
    _arrow(ax, 6.9, 1.2, 7.95, 1.2, col=MUTED, lw=1.6)
    ax.text(4.37, 1.5, "stdout", ha="center", fontsize=7.8, color=MUTED, **MONO)
    ax.text(7.45, 1.5, "stdin", ha="center", fontsize=7.8, color=MUTED, **MONO)
    return _save(fig, path)


def gcc_pipeline(path):
    """gcc'nin dört aşaması: önişlem → derleme → assembly → bağlama."""
    fig, ax = plt.subplots(figsize=(11.8, 3.5))
    ax.set_xlim(0, 20.0); ax.set_ylim(0, 5.0); ax.axis("off")
    files = [("kaynak.c", "C kaynak"), ("kaynak.i", "saf C\n(#'ler açılmış)"),
             ("kaynak.s", "assembly"), ("kaynak.o", "makine kodu\n(nesne)"),
             ("uygulama", "çalıştırılabilir")]
    tools = [("Ön işlemci", "-E", EDGE[0]), ("Derleyici", "-S", EDGE[1]),
             ("Assembler", "-c", EDGE[2]), ("Bağlayıcı", "", EDGE[3])]
    fx = [0.2, 4.6, 9.0, 13.4, 17.8]
    tx = [2.6, 7.0, 11.4, 15.8]
    y = 2.6
    for i, (ad, sub) in enumerate(files):
        col = EDGE[3] if i == 4 else MUTED
        fill = FILL[3] if i == 4 else "#FFFFFF"
        _box(ax, fx[i], y, 1.9, 1.0, ad, fill, col if i in (0, 4) else RULE,
             fs=9.5, bold=True, tcol=INK)
        ax.text(fx[i] + 0.95, y - 0.32, sub, ha="center", va="top", fontsize=7.6,
                color=MUTED)
    for i, (ad, bayrak, col) in enumerate(tools):
        _box(ax, tx[i], y + 0.06, 1.5, 0.88, ad, FILL[i % 5], col, fs=8.2, bold=True)
        _arrow(ax, fx[i] + 1.92, y + 0.5, tx[i] - 0.05, y + 0.5, col=MUTED, lw=1.3)
        _arrow(ax, tx[i] + 1.52, y + 0.5, fx[i+1] - 0.07, y + 0.5, col=MUTED, lw=1.3)
        if bayrak:
            ax.text(tx[i] + 0.75, y + 1.25, "gcc " + bayrak, ha="center",
                    fontsize=8.4, color=col, **MONO)
    # kütüphaneler bağlayıcıya
    _box(ax, 14.6, 0.3, 3.6, 0.78, "kütüphaneler (libc: printf...)",
         FILL[4], EDGE[4], fs=7.8)
    _arrow(ax, 16.55, 1.1, 16.6, 2.62, col=EDGE[4], lw=1.3)
    ax.text(10.0, 4.5, "gcc kaynak.c -o uygulama   =   bu dört aşamanın tamamı",
            ha="center", fontsize=10, color=INK, **MONO)
    return _save(fig, path)


def make_dag(path):
    """Make'in bağımlılık grafı: yalnız değişen yeniden derlenir."""
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")
    _box(ax, 0.9, 3.9, 1.9, 0.85, "main.c", "#FFFFFF", MUTED, fs=9.5, bold=True)
    _box(ax, 3.4, 3.9, 1.9, 0.85, "mat.h", FILL[2], EDGE[2], fs=9.5, bold=True)
    _box(ax, 5.9, 3.9, 1.9, 0.85, "mat.c", "#FFFFFF", MUTED, fs=9.5, bold=True)
    _box(ax, 1.9, 2.2, 1.9, 0.85, "main.o", FILL[0], EDGE[0], fs=9.5, bold=True)
    _box(ax, 5.2, 2.2, 1.9, 0.85, "mat.o", FILL[0], EDGE[0], fs=9.5, bold=True)
    _box(ax, 3.5, 0.5, 2.3, 0.85, "uygulama", FILL[3], EDGE[3], fs=9.5, bold=True)
    _arrow(ax, 1.85, 3.85, 2.6, 3.1, col=MUTED, lw=1.3)
    _arrow(ax, 4.1, 3.85, 3.1, 3.1, col=EDGE[2], lw=1.3)
    _arrow(ax, 4.6, 3.85, 5.9, 3.1, col=EDGE[2], lw=1.3)
    _arrow(ax, 6.85, 3.85, 6.35, 3.1, col=MUTED, lw=1.3)
    _arrow(ax, 2.85, 2.15, 4.2, 1.4, col=MUTED, lw=1.3)
    _arrow(ax, 6.15, 2.15, 5.1, 1.4, col=MUTED, lw=1.3)
    ax.text(9.6, 3.4, "make'in sorusu:\n\"hedef, bağımlılığından\neski mi?\"",
            ha="center", fontsize=8.8, color=INK)
    ax.text(9.6, 1.5, "mat.h değişti →\nmain.o, mat.o ve uygulama\nyeniden; BAŞKA HİÇBİR ŞEY",
            ha="center", fontsize=8.4, color=EDGE[3])
    return _save(fig, path)


def git_areas(path):
    """git'in üç alanı: çalışma dizini → sahne → depo."""
    fig, ax = plt.subplots(figsize=(8.8, 3.0))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.0); ax.axis("off")
    _box(ax, 0.6, 1.5, 2.9, 1.35, "Çalışma dizini\n(dosyaların)", FILL[0], EDGE[0],
         fs=9, bold=True)
    _box(ax, 4.6, 1.5, 2.9, 1.35, "Sahne\n(staging / index)", FILL[2], EDGE[2],
         fs=9, bold=True)
    _box(ax, 8.6, 1.5, 2.9, 1.35, "Depo\n(.git — kalıcı tarih)", FILL[1], EDGE[1],
         fs=9, bold=True)
    _arrow(ax, 3.5, 2.4, 4.55, 2.4, col=EDGE[2], lw=1.7)
    ax.text(4.03, 2.72, "git add", ha="center", fontsize=8.8, color=EDGE[2], **MONO)
    _arrow(ax, 7.5, 2.4, 8.55, 2.4, col=EDGE[1], lw=1.7)
    ax.text(8.03, 2.72, "git commit", ha="center", fontsize=8.8, color=EDGE[1], **MONO)
    _arrow(ax, 8.9, 1.15, 3.2, 1.15, col=MUTED, lw=1.2)
    ax.text(6.05, 0.62, "git restore / checkout  (tarihten geri getir)",
            ha="center", fontsize=8.2, color=MUTED, **MONO)
    ax.text(6.0, 3.62, "commit = sahnedekilerin kalıcı fotoğrafı",
            ha="center", fontsize=9.2, color=INK, style="italic")
    return _save(fig, path)


def _commit(ax, x, y, label, col, fill):
    c = Circle((x, y), 0.34, facecolor=fill, edgecolor=col, lw=1.6, zorder=3)
    ax.add_patch(c)
    ax.text(x, y, label, ha="center", va="center", fontsize=9, weight="bold",
            color=col, zorder=4, **MONO)


def git_merge_rebase(path):
    """merge vs rebase: aynı dallar, iki farklı tarih."""
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.0); ax.axis("off")
    # --- merge paneli ---
    ax.text(0.4, 5.55, "git merge — iki çizgi birleşir, tarih ÇATALLI kalır",
            fontsize=9.3, color=INK, weight="bold")
    my, fy = 4.6, 3.5
    for x, lab in ((1.0, "A"), (2.3, "B"), (3.6, "C")):
        _commit(ax, x, my, lab, EDGE[0], FILL[0])
    for x, lab in ((3.0, "D"), (4.3, "E")):
        _commit(ax, x, fy, lab, EDGE[1], FILL[1])
    _commit(ax, 5.6, my, "M", EDGE[3], FILL[3])
    ax.plot([1.34, 1.96], [my, my], color=EDGE[0], lw=1.5)
    ax.plot([2.64, 3.26], [my, my], color=EDGE[0], lw=1.5)
    ax.plot([3.94, 5.26], [my, my], color=EDGE[0], lw=1.5)
    ax.plot([2.53, 2.77], [my - 0.26, fy + 0.26], color=EDGE[1], lw=1.5)
    ax.plot([3.34, 3.96], [fy, fy], color=EDGE[1], lw=1.5)
    ax.plot([4.55, 5.38], [fy + 0.2, my - 0.24], color=EDGE[1], lw=1.5)
    ax.text(6.2, my, "← M: iki ebeveynli birleşme commit'i", fontsize=8.4,
            color=MUTED, va="center")
    ax.text(1.0, my + 0.62, "main", fontsize=8, color=EDGE[0], **MONO)
    ax.text(3.0, fy - 0.62, "özellik", fontsize=8, color=EDGE[1], **MONO)
    # --- rebase paneli ---
    ax.text(0.4, 2.35, "git rebase — commit'ler taşınıp yeniden yazılır, tarih DÜZ olur",
            fontsize=9.3, color=INK, weight="bold")
    ry = 1.3
    seq = [("A", EDGE[0], FILL[0]), ("B", EDGE[0], FILL[0]), ("C", EDGE[0], FILL[0]),
           ("D'", EDGE[1], FILL[1]), ("E'", EDGE[1], FILL[1])]
    for i, (lab, col, fill) in enumerate(seq):
        x = 1.0 + i * 1.3
        _commit(ax, x, ry, lab, col, fill)
        if i:
            ax.plot([x - 1.3 + 0.34, x - 0.34], [ry, ry], color=col, lw=1.5)
    ax.text(7.3, ry, "← D', E': aynı değişiklik, YENİ kimlik", fontsize=8.4,
            color=MUTED, va="center")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(fs_tree(os.path.join(out, "b04_fs_tree.png")))
    print(streams_pipe(os.path.join(out, "b04_streams.png")))
    print(gcc_pipeline(os.path.join(out, "b04_gcc.png")))
    print(make_dag(os.path.join(out, "b04_make.png")))
    print(git_areas(os.path.join(out, "b04_git_areas.png")))
    print(git_merge_rebase(os.path.join(out, "b04_git_merge.png")))
