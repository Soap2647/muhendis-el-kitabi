# -*- coding: utf-8 -*-
"""Bölüm 7 — 'Array & Linked List' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def array_layout(path):
    """Dizi: bitişik bellek + adres aritmetiği."""
    fig, ax = plt.subplots(figsize=(9.4, 3.6))
    ax.set_xlim(0, 13.4); ax.set_ylim(0, 5.2); ax.axis("off")
    ax.text(6.7, 4.85, "int dizi[6];    her eleman 4 bayt, HEPSİ YAN YANA",
            ha="center", fontsize=10.2, color=INK, **MONO)
    vals = [10, 20, 30, 40, 50, 60]
    x0, w = 1.5, 1.72
    for i, v in enumerate(vals):
        vurgu = (i == 3)
        _box(ax, x0 + i*w, 2.5, w - 0.09, 0.95, str(v),
             FILL[3] if vurgu else FILL[0], EDGE[3] if vurgu else EDGE[0],
             fs=11.5, bold=True)
        ax.text(x0 + i*w + (w-0.09)/2, 3.72, "dizi[%d]" % i, ha="center",
                fontsize=8.4, color=MUTED, **MONO)
        ax.text(x0 + i*w + (w-0.09)/2, 2.15, "0x%X" % (0x1000 + 4*i),
                ha="center", fontsize=8, color=MUTED, **MONO)
    ax.annotate("", xy=(x0 + 3*w + 0.8, 1.95), xytext=(x0 + 3*w + 0.8, 1.35),
                arrowprops=dict(arrowstyle="-|>", color=EDGE[3], lw=1.4))
    ax.text(6.7, 1.05, "&dizi[3]  =  taban + 3 × 4  =  0x1000 + 12  =  0x100C",
            ha="center", fontsize=9.6, color=EDGE[3], weight="bold", **MONO)
    ax.text(6.7, 0.4, "Adres tek çarpma-toplama ile bulunur — dizinin O(1) erişimi "
            "bu formülden gelir, sihirden değil.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def cache_locality(path):
    """Satır-major gezinme vs sütun-major: cache line etkisi."""
    fig, ax = plt.subplots(figsize=(9.8, 4.4))
    ax.set_xlim(0, 14.2); ax.set_ylim(0, 6.8); ax.axis("off")
    ax.text(7.1, 6.45, "Aynı matris, aynı işlem sayısı — 5-10 kat hız farkı",
            ha="center", fontsize=10.4, color=INK, weight="bold")
    n = 5
    cell = 0.62
    # sol: satır sırasıyla (iyi)
    ox = 1.0
    ax.text(ox + n*cell/2, 4.95, "SATIR sırayla gez (iyi)", ha="center",
            fontsize=9.2, color=EDGE[1], weight="bold")
    for r in range(n):
        for c in range(n):
            _box(ax, ox + c*cell, 4.3 - r*cell, cell - 0.05, cell - 0.05, "",
                 FILL[1] if r == 1 else "#FFFFFF", EDGE[1] if r == 1 else RULE)
    ax.annotate("", xy=(ox + n*cell - 0.06, 4.3 - cell + 0.28),
                xytext=(ox + 0.06, 4.3 - cell + 0.28),
                arrowprops=dict(arrowstyle="-|>", color=EDGE[1], lw=1.8))
    ax.text(ox + n*cell/2, 0.95, "bellekte YAN YANA\n→ bir cache satırı = birkaç eleman\n"
            "→ her getirme birden çok işe yarar",
            ha="center", fontsize=8.2, color=INK)
    # orta: bellek şeridi
    ax.text(7.1, 4.95, "bellekteki gerçek sıra (satır-major)", ha="center",
            fontsize=8.6, color=MUTED)
    for i in range(10):
        renk = EDGE[1] if 5 <= i < 10 else RULE
        _box(ax, 4.95 + i*0.42, 4.05, 0.38, 0.42, "",
             FILL[1] if 5 <= i < 10 else "#FFFFFF", renk)
    ax.text(7.1, 3.72, "satır 0        satır 1", ha="center", fontsize=7.8,
            color=MUTED, **MONO)
    ax.text(7.1, 2.95, "cache satırı (64 bayt)\ntek seferde gelir", ha="center",
            fontsize=8.2, color=EDGE[2], weight="bold")
    _box(ax, 6.0, 2.35, 2.2, 0.42, "", FILL[2], EDGE[2])
    # sağ: sütun sırasıyla (kötü)
    ox2 = 10.5
    ax.text(ox2 + n*cell/2, 4.95, "SÜTUN sırayla gez (kötü)", ha="center",
            fontsize=9.2, color=EDGE[3], weight="bold")
    for r in range(n):
        for c in range(n):
            _box(ax, ox2 + c*cell, 4.3 - r*cell, cell - 0.05, cell - 0.05, "",
                 FILL[3] if c == 1 else "#FFFFFF", EDGE[3] if c == 1 else RULE)
    ax.annotate("", xy=(ox2 + cell + 0.28, 4.3 - (n-1)*cell + 0.06),
                xytext=(ox2 + cell + 0.28, 4.3 + cell - 0.34),
                arrowprops=dict(arrowstyle="-|>", color=EDGE[3], lw=1.8))
    ax.text(ox2 + n*cell/2, 0.95, "bellekte ATLAYARAK\n→ her erişim yeni cache satırı\n"
            "→ getirilenin çoğu boşa gider",
            ha="center", fontsize=8.2, color=INK)
    ax.text(7.1, 0.28, "Big-O ikisine de O(n²) der. Fark, Big-O'nun görmediği "
            "sabit çarpanlardadır (Bölüm 25).",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    return _save(fig, path)


def growth_amortized(path):
    """İkiye katlayarak büyüme: tek tek maliyet vs amortize ortalama."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.4))
    n = 64
    maliyet = []
    kapasite = 1
    for i in range(1, n + 1):
        if i > kapasite:                 # dolunca ikiye katla + kopyala
            maliyet.append(1 + kapasite)
            kapasite *= 2
        else:
            maliyet.append(1)
    kum = np.cumsum(maliyet) / np.arange(1, n + 1)
    ax1.bar(range(1, n + 1), maliyet, color=EDGE[0], width=0.9)
    ax1.set_title("Tek bir ekleme maliyeti", fontsize=9.5, color=INK)
    ax1.set_xlabel("kaçıncı ekleme", fontsize=8.4)
    ax1.set_ylabel("iş miktarı", fontsize=8.4)
    ax1.tick_params(labelsize=7.6)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.text(30, 26, "sivri uçlar = kopyalama\n(2'nin kuvvetlerinde)",
             fontsize=7.8, color=EDGE[3])
    ax2.plot(range(1, n + 1), kum, color=EDGE[1], lw=2)
    ax2.axhline(3, color=EDGE[3], ls="--", lw=1.2)
    ax2.text(20, 3.25, "≈ 3 (sabit!)", fontsize=8.4, color=EDGE[3], weight="bold")
    ax2.set_ylim(0, 6)
    ax2.set_title("Ekleme başına ORTALAMA maliyet", fontsize=9.5, color=INK)
    ax2.set_xlabel("ekleme sayısı", fontsize=8.4)
    ax2.tick_params(labelsize=7.6)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Amortize O(1): tek tek pahalı, ortalamada sabit",
                 fontsize=10.4, color=INK, fontweight="bold", y=1.02)
    fig.tight_layout()
    return _save(fig, path)


def linked_list_insert(path):
    """Bağlı listede araya ekleme: işaretçi cerrahisi."""
    fig, ax = plt.subplots(figsize=(9.4, 4.0))
    ax.set_xlim(0, 13.4); ax.set_ylim(-0.5, 6.0); ax.axis("off")
    ax.text(6.7, 5.65, "Araya ekleme: SIRA ÖNEMLİ — önce yeni düğümü bağla, sonra zinciri kopar",
            ha="center", fontsize=9.8, color=INK, weight="bold")

    def dugum(x, y, val, fill=FILL[0], edge=EDGE[0]):
        _box(ax, x, y, 1.55, 0.85, "", fill, edge)
        ax.plot([x + 1.02, x + 1.02], [y, y + 0.85], color=edge, lw=1)
        ax.text(x + 0.51, y + 0.42, str(val), ha="center", va="center",
                fontsize=11, color=INK, weight="bold")
        ax.text(x + 1.28, y + 0.42, "→", ha="center", va="center",
                fontsize=9, color=MUTED)

    # ÖNCE
    ax.text(0.4, 4.75, "ÖNCE:", fontsize=9, color=MUTED, weight="bold")
    for i, v in enumerate([10, 20, 30]):
        dugum(1.6 + i*2.6, 4.15, v)
        if i < 2:
            _arrow(ax, 3.15 + i*2.6, 4.57, 4.1 + i*2.6, 4.57, col=MUTED, lw=1.4)
    ax.text(9.6, 4.57, "NULL", ha="left", va="center", fontsize=9,
            color=MUTED, **MONO)
    _arrow(ax, 8.75, 4.57, 9.45, 4.57, col=MUTED, lw=1.4)
    # SONRA
    ax.text(0.4, 2.95, "SONRA:", fontsize=9, color=MUTED, weight="bold")
    dugum(1.6, 2.35, 10)
    dugum(6.8, 2.35, 20)
    dugum(9.4, 2.35, 30)
    dugum(4.2, 0.75, 15, FILL[3], EDGE[3])       # yeni düğüm
    ax.text(4.98, 0.28, "yeni düğüm", ha="center", fontsize=8.2,
            color=EDGE[3], weight="bold")
    _arrow(ax, 3.15, 2.6, 4.3, 1.62, col=EDGE[3], lw=1.5)
    ax.text(3.25, 1.95, "2", ha="center", fontsize=8.4, color=EDGE[3],
            weight="bold")
    _arrow(ax, 5.72, 1.5, 6.7, 2.5, col=EDGE[3], lw=1.5)
    ax.text(6.35, 1.85, "1", ha="center", fontsize=8.4, color=EDGE[3],
            weight="bold")
    _arrow(ax, 8.35, 2.77, 9.3, 2.77, col=MUTED, lw=1.4)
    ax.text(6.7, -0.25, "Sıra ters olsaydı (önce kopar, sonra bağla) listenin "
            "kuyruğunu KAYBEDERDİN.",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    return _save(fig, path)


def sentinel(path):
    """Nöbetçi düğüm: kenar durumu yok eden tasarım."""
    fig, ax = plt.subplots(figsize=(9.4, 3.4))
    ax.set_xlim(0, 13.4); ax.set_ylim(-0.55, 5.0); ax.axis("off")
    ax.text(6.7, 4.65, "Nöbetçi (sentinel): \"boş liste\" ile \"başa ekleme\" özel durumlarını siler",
            ha="center", fontsize=9.8, color=INK, weight="bold")

    def dugum(x, y, val, fill=FILL[0], edge=EDGE[0], w=1.4):
        _box(ax, x, y, w, 0.8, str(val), fill, edge, fs=10.5, bold=True)

    ax.text(0.4, 3.55, "NÖBETÇİSİZ:", fontsize=8.8, color=EDGE[3], weight="bold")
    ax.text(2.9, 3.15, "bas →", fontsize=9, color=MUTED, **MONO)
    for i, v in enumerate([10, 20]):
        dugum(4.2 + i*2.0, 2.75, v)
        if i:
            _arrow(ax, 5.7, 3.15, 6.1, 3.15, col=MUTED, lw=1.3)
    _arrow(ax, 3.9, 3.15, 4.15, 3.15, col=MUTED, lw=1.3)
    ax.text(8.6, 3.15, "if (bas == NULL) { ... } else { ... }",
            ha="left", va="center", fontsize=8.2, color=EDGE[3], **MONO)

    ax.text(0.4, 1.75, "NÖBETÇİLİ:", fontsize=8.8, color=EDGE[1], weight="bold")
    ax.text(2.9, 1.35, "bas →", fontsize=9, color=MUTED, **MONO)
    dugum(4.2, 0.95, "—", FILL[1], EDGE[1])
    ax.text(4.9, 0.6, "nöbetçi\n(veri yok)", ha="center", fontsize=7.4,
            color=EDGE[1])
    for i, v in enumerate([10, 20]):
        dugum(6.2 + i*2.0, 0.95, v)
    _arrow(ax, 3.9, 1.35, 4.15, 1.35, col=MUTED, lw=1.3)
    _arrow(ax, 5.65, 1.35, 6.15, 1.35, col=MUTED, lw=1.3)
    _arrow(ax, 7.65, 1.35, 8.15, 1.35, col=MUTED, lw=1.3)
    ax.text(10.4, 1.35, "her zaman tek yol", ha="left", va="center",
            fontsize=8.2, color=EDGE[1], **MONO)
    return _save(fig, path)


def doubly_circular(path):
    """Çift yönlü ve dairesel liste."""
    fig, ax = plt.subplots(figsize=(9.4, 3.8))
    ax.set_xlim(0, 13.4); ax.set_ylim(0.2, 5.6); ax.axis("off")
    ax.text(3.4, 5.2, "ÇİFT YÖNLÜ (doubly)", ha="center", fontsize=9.6,
            color=EDGE[0], weight="bold")
    for i, v in enumerate([10, 20, 30]):
        _box(ax, 0.5 + i*2.15, 3.5, 1.85, 0.9, str(v), FILL[0], EDGE[0],
             fs=11, bold=True)
        if i:
            x = 0.5 + i*2.15
            _arrow(ax, x - 0.28, 4.15, x - 0.02, 4.15, col=MUTED, lw=1.3)
            _arrow(ax, x - 0.02, 3.75, x - 0.28, 3.75, col=EDGE[3], lw=1.3)
    ax.text(3.4, 3.05, "next →   ← prev", ha="center", fontsize=8.4,
            color=MUTED, **MONO)
    ax.text(3.4, 2.45, "Düğüm elindeyse silme O(1):\nkomşuları birbirine bağla",
            ha="center", fontsize=8.4, color=INK)
    ax.plot([7.3, 7.3], [1.2, 5.0], color=RULE, lw=1)
    # dairesel
    ax.text(10.4, 5.2, "DAİRESEL (circular)", ha="center", fontsize=9.6,
            color=EDGE[4], weight="bold")
    import numpy as _np
    cx, cy, r = 10.4, 3.2, 1.15
    for k in range(4):
        a = _np.pi/2 - k*_np.pi/2
        x, y = cx + r*_np.cos(a), cy + r*_np.sin(a)
        _box(ax, x - 0.44, y - 0.26, 0.88, 0.52, str((k+1)*10), FILL[4],
             EDGE[4], fs=9, bold=True)
    for k in range(4):
        a1 = _np.pi/2 - k*_np.pi/2 - 0.42
        a2 = _np.pi/2 - (k+1)*_np.pi/2 + 0.42
        ax.annotate("", xy=(cx + r*_np.cos(a2), cy + r*_np.sin(a2)),
                    xytext=(cx + r*_np.cos(a1), cy + r*_np.sin(a1)),
                    arrowprops=dict(arrowstyle="-|>", color=EDGE[4], lw=1.3,
                                    connectionstyle="arc3,rad=-0.28"))
    ax.text(10.4, 1.05, "Son düğüm başa döner: NULL yok.\nSıra (round-robin), "
            "oynatma listesi, zamanlayıcı.",
            ha="center", fontsize=8.4, color=INK)
    return _save(fig, path)


def ring_buffer(path):
    """Dairesel tampon: sabit dizi + baş/kuyruk indeksleri."""
    fig, ax = plt.subplots(figsize=(9.4, 3.8))
    ax.set_xlim(0, 13.4); ax.set_ylim(0, 5.6); ax.axis("off")
    ax.text(6.7, 5.2, "Dairesel tampon (ring buffer): sabit boyutlu dizi, "
            "dairesel gezinen iki indeks",
            ha="center", fontsize=9.8, color=INK, weight="bold")
    n = 8
    x0, w = 1.9, 1.2
    dolu = {2: "A", 3: "B", 4: "C"}
    for i in range(n):
        v = dolu.get(i, "")
        _box(ax, x0 + i*w, 3.0, w - 0.08, 0.9, v,
             FILL[1] if v else "#FFFFFF", EDGE[1] if v else RULE,
             fs=11, bold=True, tcol=INK)
        ax.text(x0 + i*w + (w-0.08)/2, 2.65, str(i), ha="center", fontsize=8,
                color=MUTED, **MONO)
    _arrow(ax, x0 + 2*w + 0.56, 4.35, x0 + 2*w + 0.56, 3.98, col=EDGE[0], lw=1.5)
    ax.text(x0 + 2*w + 0.56, 4.55, "bas (oku)", ha="center", fontsize=8.4,
            color=EDGE[0], weight="bold", **MONO)
    _arrow(ax, x0 + 5*w + 0.56, 4.35, x0 + 5*w + 0.56, 3.98, col=EDGE[3], lw=1.5)
    ax.text(x0 + 5*w + 0.56, 4.55, "kuyruk (yaz)", ha="center", fontsize=8.4,
            color=EDGE[3], weight="bold", **MONO)
    ax.annotate("", xy=(x0 + 0.2, 2.35), xytext=(x0 + n*w - 0.3, 2.35),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.2,
                                connectionstyle="bar,fraction=-0.09"))
    ax.text(6.7, 1.62, "sondan taşınca başa sarar:   indeks = (indeks + 1) % BOYUT",
            ha="center", fontsize=9.4, color=ACCENT, weight="bold", **MONO)
    ax.text(6.7, 0.95, "Bellek ayırma YOK, kaydırma YOK: ekleme ve çıkarma O(1). "
            "Klavye tamponu, ses akışı,",
            ha="center", fontsize=8.6, color=INK)
    ax.text(6.7, 0.5, "UART alım tamponu, üretici-tüketici kuyruğu — MertOS'ta ve "
            "her gömülü sistemde vardır.",
            ha="center", fontsize=8.6, color=INK)
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(array_layout(os.path.join(out, "b07_array.png")))
    print(cache_locality(os.path.join(out, "b07_cache.png")))
    print(growth_amortized(os.path.join(out, "b07_growth.png")))
    print(linked_list_insert(os.path.join(out, "b07_insert.png")))
    print(sentinel(os.path.join(out, "b07_sentinel.png")))
    print(doubly_circular(os.path.join(out, "b07_doubly.png")))
    print(ring_buffer(os.path.join(out, "b07_ring.png")))
