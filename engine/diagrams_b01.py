# -*- coding: utf-8 -*-
"""Bölüm 1 — 'Bilgisayar Nasıl Düşünür' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge
import numpy as np
import os

from diagrams import (_fig, _box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)


def bit_place_values(path, bits="01000101"):
    """Bir byte'ın basamak değerleri ve onluk karşılığı."""
    fig, ax = plt.subplots(figsize=(8.6, 3.2))
    ax.set_xlim(0, 8.8); ax.set_ylim(0, 4); ax.axis("off")
    places = [128, 64, 32, 16, 8, 4, 2, 1]
    x0 = 0.3
    total = 0
    for i, (b, pv) in enumerate(zip(bits, places)):
        gap = 0.3 if i == 4 else 0
        x = x0 + i * 1.02 + gap
        on = (b == "1")
        fill = FILL[0] if on else "#ffffff"
        edge = EDGE[0] if on else RULE
        _box(ax, x, 1.5, 0.9, 1.1, b, fill, edge, fs=20, bold=True,
             tcol=EDGE[0] if on else MUTED)
        ax.text(x + 0.45, 2.85, "bit %d" % (7 - i), ha="center", fontsize=8.5, color=MUTED)
        ax.text(x + 0.45, 1.15, str(pv), ha="center", fontsize=10.5,
                color=EDGE[0] if on else MUTED, weight="bold" if on else "normal")
        if on:
            total += pv
    terms = " + ".join(str(p) for b, p in zip(bits, places) if b == "1")
    ax.text(4.5, 0.45, "%s  =  %d   (onluk)      →      ASCII: '%s'"
            % (terms, total, chr(total) if 32 <= total < 127 else "?"),
            ha="center", fontsize=12, color=INK, weight="bold")
    ax.text(4.5, 3.55, "İkilik sayı:  %s" % (bits[:4] + " " + bits[4:]),
            ha="center", fontsize=11, color=ACCENT, weight="bold")
    return _save(fig, path)


def twos_complement_circle(path):
    """4-bit iki'ye tümleyen — dairesel 'sayaç' modeli."""
    fig, ax = plt.subplots(figsize=(6.2, 6.4))
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.55, 1.78); ax.axis("off")
    ax.set_aspect("equal")
    R = 1.12
    n = 16
    signed = list(range(0, 8)) + list(range(-8, 0))
    for k in range(n):
        ang = np.pi/2 - 2*np.pi*k/n          # 0 tepe, saat yönü
        x, y = R*np.cos(ang), R*np.sin(ang)
        b = format(k, "04b")
        neg = signed[k] < 0
        col = EDGE[3] if neg else EDGE[0]
        ax.text(x*1.28, y*1.28, b, ha="center", va="center", fontsize=9.5,
                color=col, family="DejaVu Sans Mono")
        ax.text(x*0.82, y*0.82, "%+d" % signed[k] if signed[k] != 0 else "0",
                ha="center", va="center", fontsize=11, color=col, weight="bold")
        ax.plot([R*0.95*np.cos(ang)], [R*0.95*np.sin(ang)], "o", ms=3, color=col)
    # +7 -> -8 sıçraması (taşma sınırı)
    a1 = np.pi/2 - 2*np.pi*7/n
    a2 = np.pi/2 - 2*np.pi*8/n
    ax.add_patch(Wedge((0, 0), 1.0, np.degrees(a2), np.degrees(a1),
                       width=0.06, color=EDGE[3], alpha=0.5))
    ax.text(0, 0.06, "4-bit", ha="center", fontsize=12, color=INK, weight="bold")
    ax.text(0, -0.16, "iki'ye tümleyen", ha="center", fontsize=9.5, color=MUTED)
    ax.annotate("taşma sınırı\n0111 → 1000\n(+7 → −8)", xy=(0.98, 0.0),
                xytext=(1.55, -0.55), fontsize=8.6, color=EDGE[3], ha="left",
                arrowprops=dict(arrowstyle="-|>", color=EDGE[3], lw=1.2))
    ax.text(0, 1.66, "en soldaki bit 1 ise → negatif", ha="center",
            fontsize=9, color=MUTED, style="italic")
    return _save(fig, path)


def von_neumann(path):
    """Von Neumann mimarisi — CPU, bellek, G/Ç ortak yol üzerinde."""
    fig, ax = _fig(9.0, 5.4)
    ax.set_xlim(0, 10); ax.set_ylim(0, 6)
    # CPU büyük kutu
    _box(ax, 0.5, 3.0, 4.6, 2.6, "", "#f4f7fb", ACCENT)
    ax.text(2.8, 5.35, "CPU (İşlemci)", ha="center", fontsize=12,
            color=ACCENT, weight="bold")
    _box(ax, 0.8, 4.35, 2.0, 0.8, "Kontrol\nBirimi (CU)", FILL[0], EDGE[0], fs=9.5, bold=True)
    _box(ax, 2.95, 4.35, 2.0, 0.8, "ALU", FILL[1], EDGE[1], fs=10.5, bold=True)
    _box(ax, 0.8, 3.25, 4.15, 0.85, "Yazmaçlar (Registers): PC · IR · SP · R0–Rn · FLAGS",
         FILL[2], EDGE[2], fs=8.6, bold=True)
    # Bellek ve G/Ç
    _box(ax, 6.6, 4.3, 3.0, 1.3, "Ana Bellek\n(RAM)\nkomut + veri", FILL[3], EDGE[3], fs=10, bold=True)
    _box(ax, 6.6, 2.2, 3.0, 1.2, "Giriş / Çıkış\n(I/O)", FILL[4], EDGE[4], fs=10, bold=True)
    # Sistem yolu (bus)
    _box(ax, 0.5, 1.1, 9.1, 0.7, "SİSTEM YOLU  (Adres · Veri · Kontrol yolları)",
         "#eceff3", MUTED, fs=10, bold=True, tcol=INK)
    for x in (2.8, 8.1):
        _arrow(ax, x, 3.0, x, 1.8, col=MUTED, style="<|-|>", lw=1.6)
    ax.text(5.0, 0.5, "Anahtar fikir: komutlar da veriler de aynı bellekte durur.",
            ha="center", fontsize=9.5, color=MUTED, style="italic")
    return _save(fig, path)


def registers(path):
    """Temel CPU yazmaçları ve görevleri."""
    fig, ax = _fig(7.4, 5.0)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    rows = [
        ("PC",    "Program Counter — sıradaki komutun adresi", EDGE[0], FILL[0]),
        ("IR",    "Instruction Register — işlenmekte olan komut", EDGE[1], FILL[1]),
        ("SP",    "Stack Pointer — yığının tepesinin adresi", EDGE[2], FILL[2]),
        ("R0–Rn", "Genel amaçlı yazmaçlar — ara hesaplar", EDGE[4], FILL[4]),
        ("FLAGS", "Durum bayrakları — zero, carry, negative, overflow", EDGE[3], FILL[3]),
    ]
    y = 9.0; h = 1.5
    for name, desc, edge, fill in rows:
        y -= h
        _box(ax, 0.5, y, 2.1, h - 0.25, name, fill, edge, fs=13, bold=True, tcol=edge)
        _box(ax, 2.8, y, 6.7, h - 0.25, desc, "#ffffff", RULE, fs=9.8, tcol=INK)
    ax.text(5, 9.4, "Yazmaçlar: CPU'nun içindeki en hızlı, en küçük bellek",
            ha="center", fontsize=10.5, color=ACCENT, weight="bold")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(bit_place_values(os.path.join(out, "b01_bit_places.png")))
    print(twos_complement_circle(os.path.join(out, "b01_twos.png")))
    print(von_neumann(os.path.join(out, "b01_vonneumann.png")))
    print(registers(os.path.join(out, "b01_registers.png")))
