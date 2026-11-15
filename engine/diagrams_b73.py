# -*- coding: utf-8 -*-
"""Bolum 73 - Temsil Ogrenme & Self-Supervised diyagramlari.

Kavramsal sekiller veri okumaz. Olcum grafikleri engine/veri/b73_*.csv
dosyalarindan okunur; bu CSV'leri deney betikleri uretir (Temp altindaki
b73 klasoru: t01..t10 ve ortak73.py).
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tuval(w=9.6, h=4.6, xl=14, yl=7):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def yontem_haritasi(path):
    fig, ax = tuval(10, 5.4, 14, 8)
    ax.text(7, 7.6, "Temsil öğrenme: etiketsiz veriden gösterim",
            ha="center", fontsize=11, color=INK, weight="bold")
    _box(ax, 0.2, 5.2, 3.0, 1.5, "Denetimli\n(etiket şart)", FILL[2],
         EDGE[2], fs=10)
    _box(ax, 0.2, 2.6, 3.0, 1.8, "Oz-denetimli\n(etiket verinin\nkendisinden)",
         FILL[0], EDGE[0], fs=10)
    ailer = [
        ("Bağlam / maskeleme", "BERT, MAE\n(Bölüm 70, 73.4)", FILL[1], EDGE[1]),
        ("Dönüşüm tahmini", "döndürme tahmini\n(73.3)", FILL[1], EDGE[1]),
        ("Kontrastif", "SimCLR, MoCo\n(73.5-73.6)", FILL[3], EDGE[3]),
        ("Negatifsiz", "SimSiam, BYOL,\nVICReg (73.7)", FILL[3], EDGE[3]),
        ("Çok modlu", "CLIP\n(73.10)", FILL[4], EDGE[4]),
    ]
    for i, (b, t, f, e) in enumerate(ailer):
        y = 6.6 - i * 1.15
        _box(ax, 4.2, y - 0.5, 2.5, 0.95, b, f, e, fs=9, bold=True)
        _box(ax, 7.1, y - 0.5, 2.4, 0.95, t, f, e, fs=8)
        _arrow(ax, 3.3, 3.5, 4.1, y, col=MUTED, lw=1.0)
    _box(ax, 10.2, 4.0, 3.5, 2.4,
         "Ölçüm:\n1. doğrusal yoklama\n2. k-NN\n3. az etiketle ince ayar",
         FILL[2], EDGE[2], fs=9)
    _arrow(ax, 9.7, 5.2, 10.1, 5.2, col=ACCENT, lw=1.2)
    ax.text(0.2, 0.25, "Gösterim (temsil) bir sonraki göreve taşınır.",
            fontsize=9, color=MUTED)
    return _save(fig, os.path.join(GORSEL, path))


def simclr_mimari(path):
    fig, ax = tuval(10, 4.8, 14, 7)
    _box(ax, 0.1, 4.6, 1.9, 1.3, "x\ngörüntü", FILL[0], EDGE[0], fs=10)
    _box(ax, 2.5, 5.4, 2.2, 1.0, "artırma t₁\n(kırpma, renk)",
         FILL[2], EDGE[2], fs=9)
    _box(ax, 2.5, 3.6, 2.2, 1.0, "artırma t₂\n(kırpma, renk)",
         FILL[2], EDGE[2], fs=9)
    _box(ax, 5.2, 5.2, 1.9, 1.5, "kodlayıcı f\n(CNN)", FILL[1], EDGE[1],
         fs=9)
    _box(ax, 5.2, 3.2, 1.9, 1.5, "kodlayıcı f\n(aynı ağırlık)",
         FILL[1], EDGE[1], fs=9)
    _box(ax, 7.8, 5.2, 1.7, 1.5, "projeksiyon\ng (MLP)", FILL[4], EDGE[4],
         fs=9)
    _box(ax, 7.8, 3.2, 1.7, 1.5, "projeksiyon\ng (MLP)", FILL[4], EDGE[4],
         fs=9)
    _box(ax, 10.2, 5.0, 1.7, 1.0, "z₁", FILL[3], EDGE[3], fs=10)
    _box(ax, 10.2, 3.4, 1.7, 1.0, "z₂", FILL[3], EDGE[3], fs=10)
    _box(ax, 12.2, 3.6, 1.7, 2.4, "NT-Xent\nkaybı\n(pozitif =\nçift)",
         FILL[3], EDGE[3], fs=9)
    _arrow(ax, 2.0, 5.2, 2.5, 5.9, col=MUTED, lw=1.1)
    _arrow(ax, 2.0, 5.0, 2.5, 4.1, col=MUTED, lw=1.1)
    _arrow(ax, 4.7, 5.9, 5.2, 5.9, col=MUTED, lw=1.1)
    _arrow(ax, 4.7, 4.1, 5.2, 3.9, col=MUTED, lw=1.1)
    _arrow(ax, 7.1, 5.9, 7.8, 5.9, col=MUTED, lw=1.1)
    _arrow(ax, 7.1, 3.9, 7.8, 3.9, col=MUTED, lw=1.1)
    _arrow(ax, 9.5, 5.9, 10.2, 5.5, col=MUTED, lw=1.1)
    _arrow(ax, 9.5, 3.9, 10.2, 3.9, col=MUTED, lw=1.1)
    _arrow(ax, 11.9, 5.5, 12.2, 5.0, col=MUTED, lw=1.1)
    _arrow(ax, 11.9, 3.9, 12.2, 4.4, col=MUTED, lw=1.1)
    ax.text(5.2, 1.6, "Kayıptan sonra temsil h = f(x) kullanılır; g atılır.",
            fontsize=9, color=ACCENT)
    ax.text(5.2, 0.9, "Ağırlıklar iki kolda paylaşılır (siyam yapısı).",
            fontsize=9, color=MUTED)
    return _save(fig, os.path.join(GORSEL, path))


def clip_sema(path):
    fig, ax = tuval(10, 4.6, 14, 7)
    _box(ax, 0.2, 4.4, 2.6, 1.4, "görüntü\n(32×32 RGB)", FILL[0], EDGE[0],
         fs=9)
    _box(ax, 0.2, 1.4, 2.6, 1.4, "metin\n(\"kırmızı büyük daire\n"
         "sol üstte\")", FILL[0], EDGE[0], fs=8)
    _box(ax, 3.6, 4.4, 2.6, 1.4, "görüntü\nkodlayıcı", FILL[1], EDGE[1],
         fs=9)
    _box(ax, 3.6, 1.4, 2.6, 1.4, "metin\nkodlayıcı (transformer)",
         FILL[1], EDGE[1], fs=9)
    _box(ax, 7.0, 2.9, 2.6, 1.6, "ortak gömme\nuzayı (birim küre)",
         FILL[4], EDGE[4], fs=9)
    _box(ax, 10.6, 2.9, 3.2, 1.6, "simetrik kayıp:\ngörüntü→metin\n"
         "+ metin→görüntü", FILL[3], EDGE[3], fs=8)
    _arrow(ax, 2.8, 5.1, 3.6, 5.1, col=MUTED, lw=1.1)
    _arrow(ax, 2.8, 2.1, 3.6, 2.1, col=MUTED, lw=1.1)
    _arrow(ax, 6.2, 5.1, 7.0, 4.3, col=MUTED, lw=1.1)
    _arrow(ax, 6.2, 2.1, 7.0, 3.1, col=MUTED, lw=1.1)
    _arrow(ax, 9.6, 3.7, 10.6, 3.7, col=MUTED, lw=1.1)
    ax.text(0.2, 0.5, "Sıfır atış: sınıf adlarından istemler gömülür; görüntü "
            "en yakın istemi seçer.", fontsize=9, color=MUTED)
    return _save(fig, os.path.join(GORSEL, path))


if __name__ == "__main__":
    print(yontem_haritasi("b73_yontemler.png"))
    print(simclr_mimari("b73_simclr.png"))
    print(clip_sema("b73_clip_sema.png"))
