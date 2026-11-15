# -*- coding: utf-8 -*-
"""Bölüm 9 — 'Hash Table' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def hash_basic(path):
    """Anahtar → hash → indeks → kova."""
    fig, ax = plt.subplots(figsize=(9.8, 4.0))
    ax.set_xlim(0, 14.2); ax.set_ylim(0, 6.0); ax.axis("off")
    ax.text(7.1, 5.65, "Temel fikir: elemanı ARAMA — yerini HESAPLA",
            ha="center", fontsize=10.6, color=INK, weight="bold")
    # anahtarlar
    anahtarlar = ["\"Mert\"", "\"Ada\"", "\"Can\""]
    for i, a in enumerate(anahtarlar):
        _box(ax, 0.4, 3.9 - i*0.95, 2.0, 0.72, a, FILL[0], EDGE[0],
             fs=9.5, bold=True)
    ax.text(1.4, 5.05, "anahtar", ha="center", fontsize=8.6, color=MUTED,
            weight="bold")
    # hash fonksiyonu
    _box(ax, 3.1, 2.35, 2.3, 2.3, "", FILL[2], EDGE[2])
    ax.text(4.25, 3.85, "h(anahtar)", ha="center", fontsize=9.6, color=EDGE[2],
            weight="bold", **MONO)
    ax.text(4.25, 3.35, "hash\nfonksiyonu", ha="center", fontsize=8.4,
            color=INK)
    ax.text(4.25, 2.7, "% M", ha="center", fontsize=9.2, color=EDGE[2],
            **MONO)
    for i in range(3):
        _arrow(ax, 2.45, 4.26 - i*0.95, 3.05, 3.5, col=MUTED, lw=1.2)
    # tablo
    ax.text(9.6, 5.22, "tablo (M = 5 kova)", ha="center", fontsize=8.6,
            color=MUTED, weight="bold")
    icerik = {0: "", 1: "\"Ada\"", 2: "", 3: "\"Mert\"", 4: "\"Can\""}
    for i in range(5):
        v = icerik[i]
        _box(ax, 8.3, 4.35 - i*0.78, 2.6, 0.66, v,
             FILL[1] if v else "#FFFFFF", EDGE[1] if v else RULE,
             fs=9.5, bold=bool(v))
        ax.text(7.62, 4.35 - i*0.78 + 0.33, str(i), ha="right",
                va="center", fontsize=9, color=MUTED, **MONO)
    _arrow(ax, 5.5, 3.5, 8.25, 4.68, col=EDGE[2], lw=1.3)
    _arrow(ax, 5.5, 3.5, 8.25, 3.12, col=EDGE[2], lw=1.3)
    _arrow(ax, 5.5, 3.5, 8.25, 2.34, col=EDGE[2], lw=1.3)
    ax.text(6.85, 4.35, "indeks", ha="center", fontsize=8.2, color=EDGE[2])
    ax.text(11.2, 3.5, "Erişim tek adımda:\nO(1) ortalama", ha="left",
            va="center", fontsize=9, color=EDGE[1], weight="bold")
    ax.text(7.1, 0.9, 'sozluk["Mert"]  →  h("Mert") = 8823  →  8823 % 5 = 3  '
            '→  kova 3',
            ha="center", fontsize=9.4, color=INK, **MONO)
    ax.text(7.1, 0.35, "Dizi indeksi gibi doğrudan yer buluyoruz — ama indeksi "
            "veri kendisi belirliyor.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def birthday_paradox(path):
    """Çakışma kaçınılmaz: doğum günü paradoksu eğrisi."""
    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    M = 365
    n = np.arange(1, 81)
    # en az bir çakışma olasılığı
    p = 1 - np.exp(np.cumsum(np.log(1 - np.arange(0, 80) / M)))
    ax.plot(n, p, color=EDGE[3], lw=2.2)
    ax.axhline(0.5, color=MUTED, ls="--", lw=1.0)
    ax.axvline(23, color=EDGE[0], ls="--", lw=1.0)
    ax.plot([23], [p[22]], "o", color=EDGE[0], ms=6)
    ax.annotate("23 kişi → %50 çakışma!",
                xy=(23, p[22]), xytext=(31, 0.36),
                fontsize=9, color=EDGE[0], weight="bold",
                arrowprops=dict(arrowstyle="-|>", color=EDGE[0], lw=1.2))
    ax.annotate("57 kişi → %99", xy=(57, p[56]), xytext=(50, 0.72),
                fontsize=8.6, color=MUTED,
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0))
    ax.set_xlabel("tabloya eklenen anahtar sayısı (M = 365 kova)", fontsize=9)
    ax.set_ylabel("en az bir çakışma olasılığı", fontsize=9)
    ax.set_title("Çakışma sezgiden ÇOK daha erken gelir "
                 "(doğum günü paradoksu)",
                 fontsize=10.4, color=INK, fontweight="bold")
    ax.set_ylim(0, 1.02)
    ax.tick_params(labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)
    fig.tight_layout()
    return _save(fig, path)


def chaining(path):
    """Zincirleme: her kova bir bağlı liste."""
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 5.6); ax.axis("off")
    ax.text(7.0, 5.25, "Zincirleme (chaining): çakışanlar aynı kovada "
            "bir listede birikir",
            ha="center", fontsize=10.4, color=INK, weight="bold")
    kovalar = [
        (0, []),
        (1, ["Ada"]),
        (2, []),
        (3, ["Mert", "Efe", "Ela"]),
        (4, ["Can"]),
    ]
    for i, (idx, icerik) in enumerate(kovalar):
        y = 4.25 - i*0.82
        _box(ax, 1.3, y, 1.5, 0.68, str(idx), "#F7F6F2", RULE, fs=9.5,
             bold=True, tcol=MUTED)
        for j, v in enumerate(icerik):
            x = 3.2 + j*2.3
            _box(ax, x, y, 1.85, 0.68, v, FILL[1], EDGE[1], fs=9.2, bold=True)
            if j == 0:
                _arrow(ax, 2.85, y + 0.34, x - 0.05, y + 0.34, col=MUTED,
                       lw=1.2)
            else:
                _arrow(ax, x - 0.45, y + 0.34, x - 0.05, y + 0.34,
                       col=EDGE[1], lw=1.2)
        if not icerik:
            ax.text(3.3, y + 0.34, "boş", ha="left", va="center", fontsize=8.4,
                    color=MUTED, style="italic")
    ax.text(11.0, 3.42, "kova 3'te 3 çakışma\n→ o kovada arama O(3)", ha="left",
            va="center", fontsize=8.8, color=EDGE[3])
    ax.text(7.0, 0.55, "Ortalama zincir uzunluğu = yük faktörü α = n / M. "
            "Arama maliyeti O(1 + α).",
            ha="center", fontsize=9.2, color=ACCENT, weight="bold")
    ax.text(7.0, 0.12, "Silme kolaydır (listeden çıkar), ama her düğüm ayrı "
            "bellek → cache dostu değil.",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


def open_addressing(path):
    """Doğrusal sondalama, kümelenme ve mezar taşı."""
    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    ax.set_xlim(0, 14.2); ax.set_ylim(-0.45, 6.2); ax.axis("off")
    ax.text(7.1, 5.85, "Açık adresleme: çakışınca BAŞKA bir kova ara — "
            "her şey tek dizide",
            ha="center", fontsize=10.4, color=INK, weight="bold")
    # üst: doğrusal sondalama
    ax.text(0.4, 5.15, "Doğrusal sondalama: dolu ise bir sağa bak "
            "(i+1, i+2, ...)", fontsize=8.8, color=EDGE[0], weight="bold")
    icerik = ["", "Ada", "Mert", "Efe", "", "Can", "", ""]
    for i, v in enumerate(icerik):
        vurgu = v in ("Mert", "Efe")
        _box(ax, 1.0 + i*1.62, 3.85, 1.5, 0.75, v,
             FILL[3] if vurgu else (FILL[1] if v else "#FFFFFF"),
             EDGE[3] if vurgu else (EDGE[1] if v else RULE),
             fs=9, bold=bool(v))
        ax.text(1.0 + i*1.62 + 0.75, 3.55, str(i), ha="center", fontsize=8,
                color=MUTED, **MONO)
    ax.annotate("", xy=(1.0 + 3*1.62 + 0.75, 4.74), xytext=(1.0 + 2*1.62 + 0.75, 4.74),
                arrowprops=dict(arrowstyle="-|>", color=EDGE[3], lw=1.4))
    ax.text(1.0 + 4*1.62 + 0.2, 4.74, "Efe de 2'ye düştü → 3'e kaydı",
            ha="left", va="center", fontsize=8.2, color=EDGE[3])
    ax.text(7.1, 3.05, "Bitişik dolu bloklar büyüdükçe aramalar uzar: "
            "birincil kümelenme (primary clustering)",
            ha="center", fontsize=8.6, color=EDGE[3], style="italic")
    # alt: mezar taşı
    ax.text(0.4, 2.45, "SİLME TUZAĞI: kovayı boşaltırsan arama zinciri kopar "
            "→ mezar taşı bırak", fontsize=8.8, color=EDGE[2], weight="bold")
    icerik2 = ["", "Ada", "✗", "Efe", "", "Can", "", ""]
    for i, v in enumerate(icerik2):
        mezar = (v == "✗")
        _box(ax, 1.0 + i*1.62, 1.15, 1.5, 0.75, v,
             FILL[2] if mezar else (FILL[1] if v else "#FFFFFF"),
             EDGE[2] if mezar else (EDGE[1] if v else RULE),
             fs=9, bold=bool(v))
    ax.text(1.0 + 2*1.62 + 0.75, 0.82, "mezar taşı", ha="center", fontsize=7.8,
            color=EDGE[2], weight="bold")
    ax.text(4.15, 0.32, "\"burada bir şey vardı,\naramaya devam et\"",
            ha="left", va="center", fontsize=8.4, color=EDGE[2])
    ax.text(7.1, -0.22, "Bedeli: tek dizi → cache dostu ve bellek verimli. "
            "Yükü α < 0.7 tutmak şart.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def load_factor(path):
    """Yük faktörü arttıkça beklenen sonda sayısı."""
    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    a = np.linspace(0.01, 0.95, 300)
    zincir = 1 + a
    dogrusal = 0.5 * (1 + 1.0 / (1 - a))
    ax.plot(a, zincir, color=EDGE[1], lw=2.2, label="zincirleme: 1 + α")
    ax.plot(a, dogrusal, color=EDGE[3], lw=2.2,
            label="doğrusal sondalama: ½(1 + 1/(1−α))")
    for esik, renk, etiket in [(2/3, EDGE[0], "Python: 2/3"),
                               (0.75, EDGE[2], "Java: 0.75")]:
        ax.axvline(esik, color=renk, ls="--", lw=1.1)
        ax.text(esik - 0.01, 9.3, etiket, rotation=90, fontsize=8,
                color=renk, ha="right", va="top", weight="bold")
    ax.set_xlabel("yük faktörü  α = n / M", fontsize=9)
    ax.set_ylabel("ortalama sonda sayısı", fontsize=9)
    ax.set_title("Yük faktörü kritiktir: α → 1 iken maliyet PATLAR",
                 fontsize=10.4, color=INK, fontweight="bold")
    ax.set_ylim(0, 10)
    ax.legend(fontsize=8.4, frameon=False, loc="upper left")
    ax.tick_params(labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)
    fig.tight_layout()
    return _save(fig, path)


def rehashing(path):
    """Yeniden hash'leme: tablo büyüyünce herkes yeniden dağıtılır."""
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 5.2); ax.axis("off")
    ax.text(7.0, 4.85, "Yeniden hash'leme (rehashing): M değişince "
            "TÜM anahtarlar yeni yerlerine taşınır",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    ax.text(2.4, 4.15, "ESKİ: M = 4, α = 0.75", ha="center", fontsize=8.8,
            color=EDGE[3], weight="bold")
    eski = ["Can", "Ada", "", "Mert"]
    for i, v in enumerate(eski):
        _box(ax, 1.0 + i*0.0, 3.3 - i*0.72, 2.8, 0.62, v,
             FILL[3] if v else "#FFFFFF", EDGE[3] if v else RULE,
             fs=9.2, bold=bool(v))
        ax.text(0.75, 3.3 - i*0.72 + 0.31, str(i), ha="right", va="center",
                fontsize=8.4, color=MUTED, **MONO)
    _arrow(ax, 4.1, 2.4, 5.5, 2.4, col=ACCENT, lw=1.8)
    ax.text(4.8, 2.72, "M × 2", ha="center", fontsize=9, color=ACCENT,
            weight="bold", **MONO)
    ax.text(4.8, 1.95, "hepsi yeniden\nhesaplanır", ha="center", fontsize=7.8,
            color=MUTED)
    ax.text(8.3, 4.15, "YENİ: M = 8, α = 0.375", ha="center", fontsize=8.8,
            color=EDGE[1], weight="bold")
    yeni = ["", "Ada", "", "Mert", "", "", "Can", ""]
    for i, v in enumerate(yeni):
        _box(ax, 6.9, 3.66 - i*0.44, 2.8, 0.38, v,
             FILL[1] if v else "#FFFFFF", EDGE[1] if v else RULE,
             fs=8.4, bold=bool(v))
        ax.text(6.65, 3.66 - i*0.44 + 0.19, str(i), ha="right", va="center",
                fontsize=7.6, color=MUTED, **MONO)
    ax.text(10.2, 2.3, "Tek bir ekleme O(n) sürer\nama n ekleme için toplam "
            "iş O(n)\n→ AMORTİZE O(1)", ha="left", va="center",
            fontsize=9, color=ACCENT, weight="bold")
    ax.text(7.0, 0.35, "Bölüm 7'deki dinamik dizi büyütmesinin aynısı — "
            "aynı geometrik seri, aynı sonuç.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(hash_basic(os.path.join(out, "b09_temel.png")))
    print(birthday_paradox(os.path.join(out, "b09_dogumgunu.png")))
    print(chaining(os.path.join(out, "b09_zincir.png")))
    print(open_addressing(os.path.join(out, "b09_acik.png")))
    print(load_factor(os.path.join(out, "b09_yuk.png")))
    print(rehashing(os.path.join(out, "b09_rehash.png")))
