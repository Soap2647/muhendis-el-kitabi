# -*- coding: utf-8 -*-
"""Bölüm 79 - Makale okuma ve araştırma yöntemi diyagramları.

Ölçüm grafikleri engine/veri/b79_*.csv dosyalarından okunur;
bu CSV'leri deney betikleri üretir (t01 ... t06).
Kavramsal şekiller veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def uc_gecis(path):
    """Makale okumanın üç geçişi.
    Her geçiş bir öncekinin üstüne kurulur."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    adimlar = [
        ("1. Geçiş: haritalama",
          "başlık, özet, şekiller,\nsonuç tabloları", 0),
        ("2. Geçiş: yöntem",
          "veri, baseline, ayarlar,\ndeney düzeni", 1),
        ("3. Geçiş: ayrıntı",
          "denklemler, kod, ek,\nyeniden üretim", 2),
    ]
    for ad, alt, i in adimlar:
        x = 0.4 + i * 4.6
        _box(ax, x, 3.1, 4.0, 1.5, ad, fill=FILL[i], edge=EDGE[i],
             fs=11.5, bold=True)
        ax.text(x + 2.0, 2.2, alt, ha="center", va="center",
                fontsize=9.4, color=MUTED)
        if i < 2:
            _arrow(ax, x + 4.0, 3.85, x + 4.6, 3.85,
                   col=ACCENT, lw=1.8)
    _box(ax, 3.0, 0.2, 8.0, 1.0,
         "Karar: oku, not al, bir sonraki geçişe gerek var mı?",
         fill=FILL[4], edge=EDGE[4], fs=10.5)
    return _save(fig, path)


def makale_anatomi(path):
    """Makalenin parçaları ve her parçanın okurken sorduğu soru."""
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    _box(ax, 4.2, 6.6, 5.6, 1.1, "İddia (katkı)", fill=FILL[0],
         edge=ACCENT, fs=12, bold=True)
    parcalar = [
        ("Yöntem", "ne yapıldı,\nnasıl", 0.3, 4.1),
        ("Deney düzeni", "veri, bölme,\ntohum sayısı", 4.9, 4.1),
        ("Baseline", "karşılaştırılan\nbasit yöntem", 9.5, 4.1),
        ("Ablation", "hangi bileşen\nsonucu taşıyor", 0.3, 1.6),
        ("Sınırlamalar", "neyi kontrol\netmedi", 4.9, 1.6),
        ("Kod ve veri", "yeniden üretilebilir\nmi", 9.5, 1.6),
    ]
    for ad, alt, x, y in parcalar:
        _box(ax, x, y, 4.1, 1.5, ad, fill=FILL[2], edge=EDGE[2],
             fs=11, bold=True)
        ax.text(x + 2.05, y - 0.45, alt, ha="center", va="center",
                fontsize=8.8, color=MUTED)
        _arrow(ax, x + 2.05, y + 1.5, 7.0, 6.6, col=RULE, lw=1.0)
    ax.text(7.0, 0.35, "Her parça iddiayla bağlantılı olmalı; "
            "bağlantı yoksa iddia desteği zayıftır.",
            ha="center", fontsize=9.2, color=INK)
    return _save(fig, path)


def tohum_fark(path):
    """Aynı yöntemin iki koşusu arasındaki fark dağılımı (Deney 1)."""
    satir = oku("b79_tohum_fark.csv")
    f = np.array([float(r["fark"]) for r in satir])
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.hist(f * 100, bins=np.arange(-1.6, 1.6, 0.2), color=FILL[0],
            edgecolor=EDGE[0], lw=1.0)
    ax.axvline(0, color=ACCENT, lw=1.6)
    ax.axvline(1.0, color=MUTED, lw=1.0, ls="--")
    ax.axvline(-1.0, color=MUTED, lw=1.0, ls="--")
    ax.text(1.05, ax.get_ylim()[1] * 0.92, "+1 puan", color=MUTED,
            fontsize=9)
    ax.text(-1.05, ax.get_ylim()[1] * 0.92, "-1 puan", color=MUTED,
            fontsize=9, ha="right")
    ax.set_xlabel("Test doğruluğu farkı (yüzde puan), aynı yöntem",
                  color=INK)
    ax.set_ylabel("Çift sayısı (100 çift)", color=INK)
    ax.set_title("Tohum gürültüsü: aynı yöntemin iki koşusu",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)


def guc_egrisi(path):
    """Tohum sayısına göre saptanabilir fark (Deney 4)."""
    satir = oku("b79_guc.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    renk = {"0.005": ACCENT_L, "0.010": EDGE[1], "0.020": ACCENT}
    for d in ["0.005", "0.010", "0.020"]:
        s = [r for r in satir if r["delta"] == d]
        n = [int(r["n"]) for r in s]
        g = [float(r["guc"]) for r in s]
        ax.plot(n, g, "o-", color=renk[d], lw=1.8,
                label="gerçek fark %.3f" % float(d))
    ax.axhline(0.8, color=MUTED, lw=1.0, ls="--")
    ax.text(20.3, 0.82, "güç = 0,80", color=MUTED,
            fontsize=9, ha="right")
    ax.set_xlabel("Her yöntemde tohum sayısı (n)", color=INK)
    ax.set_ylabel("Güç (doğru fark saptama olasılığı)", color=INK)
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=9.5)
    ax.set_title("Güç analizi: σ = 0,0030 ölçülmüş",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)


def yeniden_uretim(path):
    """İddia ile ölçüm: tohum başına AdamW - Adam farkı (Deney 2)."""
    satir = oku("b79_yeniden.csv")
    f = np.array([float(r["fark"]) for r in satir]) * 100
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    x = np.arange(len(f))
    ax.axhspan(-0.17, 0.33, color=FILL[1], alpha=0.8)
    ax.text(4.4, 0.42, "%95 GA (bootstrap): [-0,17; +0,33] puan",
            ha="right", fontsize=9, color=EDGE[1])
    ax.axhline(0, color=ACCENT, lw=1.5)
    ax.scatter(x, f, s=60, color=ACCENT_L, zorder=3)
    ax.axhline(f.mean(), color=INK, lw=1.2, ls="--")
    ax.text(4.4, f.mean() - 0.12, "ortalama +0,06 puan",
            ha="right", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(["tohum %d" % i for i in range(len(f))])
    ax.set_ylabel("AdamW - Adam (yüzde puan)", color=INK)
    ax.set_title("Bölüm 64.4 iddiası: fark sapmalar içinde mi?",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)


def ablation(path):
    """2x2x2 ablation: sekiz koşulun ortalama testi (Deney 3)."""
    satir = oku("b79_ablation.csv")
    sirali = sorted(satir, key=lambda r: float(r["test_ort"]))
    ad = [r["kosul"] for r in sirali]
    v = np.array([float(r["test_ort"]) for r in sirali])
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.barh(ad, v, color=FILL[0], edgecolor=EDGE[0], lw=1.4)
    ax.set_xlim(0.96, 0.99)
    for i, val in enumerate(v):
        ax.text(val + 0.0003, i, "%.4f" % val,
                va="center", fontsize=9)
    ax.set_xlabel("Test doğruluğu (5 tohum ortalaması)", color=INK)
    ax.set_title("Ablation: BN etkisi görünür, dropout etkisi küçük",
                 color=INK, fontsize=12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return _save(fig, path)


def coklu_karsilastirma(path):
    """Kötü ve iyi şekil: aynı veri, iki farklı eksen (Deney 5)."""
    satir = oku("b79_coklu.csv")
    ad = ["ham", "bonferroni", "holm"]
    f = {r["duzeltme"]: float(r["fwer"]) for r in satir}
    v = [f[a] for a in ad]
    fig, (sol, sag) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    sol.bar(ad, v, color=FILL[3], edgecolor=EDGE[3])
    sol.set_ylim(0.0275, 0.0285)
    sol.set_title("Kötü: kesik eksen, fark abartılı", color=INK,
                  fontsize=10.5)
    sol.set_ylabel("FWER", color=INK)
    sag.bar(ad, v, color=FILL[1], edgecolor=EDGE[1])
    sag.axhline(0.05, color=ACCENT, lw=1.4, ls="--")
    sag.text(2.45, 0.058, "alfa = 0,05", color=ACCENT, fontsize=9,
             ha="right")
    sag.set_ylim(0, 0.7)
    for i, val in enumerate(v):
        sag.text(i, val + 0.015, "%.3f" % val,
                 ha="center", fontsize=9)
    sag.set_title("İyi: sıfırdan, eşik görünür",
                  color=INK, fontsize=10.5)
    sag.set_ylabel("FWER", color=INK)
    for a in (sol, sag):
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.tight_layout()
    return _save(fig, path)


def arastirma_dongu(path):
    """Hipotez -> deney -> sonuç -> karar döngüsü."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")
    dugumler = [
        ("Hipotez", "iddia, ölçülebilir\nbeklenti", 0.6, 4.3, 0),
        ("Deney", "tek değişken,\n3+ tohum", 4.9, 4.3, 1),
        ("Sonuç", "güven aralığı,\nnegatif sonuç dahil", 9.2, 4.3, 2),
        ("Karar", "kabul, red ya da\nyeni hipotez", 4.9, 0.6, 3),
    ]
    for ad, alt, x, y, i in dugumler:
        _box(ax, x, y, 3.9, 1.6, ad, fill=FILL[i], edge=EDGE[i],
             fs=12, bold=True)
        ax.text(x + 1.95, y - 0.45, alt, ha="center", va="center",
                fontsize=8.8, color=MUTED)
    _arrow(ax, 4.5, 5.1, 4.9, 5.1, col=ACCENT, lw=1.8)
    _arrow(ax, 8.8, 5.1, 9.2, 5.1, col=ACCENT, lw=1.8)
    _arrow(ax, 11.15, 3.9, 8.8, 1.6, col=ACCENT, lw=1.8)
    _arrow(ax, 4.9, 1.4, 2.5, 3.9, col=ACCENT, lw=1.8)
    ax.text(7.0, 3.1,
            "Karar yeni hipotez doğuruyorsa döngü tekrar eder",
            ha="center", fontsize=9, color=MUTED)
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    uc_gecis(os.path.join(GORSEL, "b79_uc_gecis.png"))
    makale_anatomi(os.path.join(GORSEL, "b79_makale_anatomi.png"))
    tohum_fark(os.path.join(GORSEL, "b79_tohum_fark.png"))
    guc_egrisi(os.path.join(GORSEL, "b79_guc_egrisi.png"))
    yeniden_uretim(os.path.join(GORSEL, "b79_yeniden_uretim.png"))
    ablation(os.path.join(GORSEL, "b79_ablation.png"))
    coklu_karsilastirma(
        os.path.join(GORSEL, "b79_coklu_karsilastirma.png"))
    arastirma_dongu(os.path.join(GORSEL, "b79_arastirma_dongu.png"))
    print("tamam")
