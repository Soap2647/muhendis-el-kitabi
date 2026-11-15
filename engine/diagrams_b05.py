# -*- coding: utf-8 -*-
"""Bölüm 5 — 'Problemi Parçala' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def problem_cycle(path):
    """Altı adımlı problem çözme döngüsü."""
    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    ax.set_xlim(0, 13.2); ax.set_ylim(0, 6.9); ax.axis("off")
    steps = [
        ("1. ANLA", "girdi · çıktı\nkısıtlar", EDGE[0], FILL[0]),
        ("2. ÖRNEKLE", "elle çalıştır\nkenar durumlar", EDGE[1], FILL[1]),
        ("3. KABA ÇÖZ", "çalışan bir şey\nyaz (yavaş olsun)", EDGE[2], FILL[2]),
        ("4. ÖRÜNTÜ BUL", "bu neye\nbenziyor?", EDGE[4], FILL[4]),
        ("5. İYİLEŞTİR", "darboğazı\nkaldır", EDGE[3], FILL[3]),
        ("6. DOĞRULA", "test + karmaşıklık\nelle iz sür", EDGE[0], FILL[0]),
    ]
    x0, w, gap = 0.35, 1.95, 0.18
    y = 3.4
    for i, (ad, alt, edge, fill) in enumerate(steps):
        x = x0 + i * (w + gap)
        _box(ax, x, y, w, 1.5, "", fill, edge)
        ax.text(x + w/2, y + 1.12, ad, ha="center", fontsize=9.4,
                color=edge, weight="bold")
        ax.text(x + w/2, y + 0.45, alt, ha="center", fontsize=7.8, color=INK)
        if i < 5:
            _arrow(ax, x + w + 0.01, y + 0.75, x + w + gap - 0.02, y + 0.75,
                   col=MUTED, lw=1.4)
    # geri dönüş okları: 4→3 ve 6→1
    ax.annotate("", xy=(x0 + 2*(w+gap) + w/2, y - 0.12),
                xytext=(x0 + 3*(w+gap) + w/2, y - 0.12),
                arrowprops=dict(arrowstyle="-|>", color=EDGE[4], lw=1.3,
                                connectionstyle="arc3,rad=0.45"))
    ax.text(x0 + 2.6*(w+gap) + w/2, y - 1.15, "örüntü tutmadı:\nyeni açıdan bak",
            ha="center", fontsize=7.6, color=EDGE[4], style="italic")
    ax.annotate("", xy=(x0 + w/2, y + 1.56),
                xytext=(x0 + 5*(w+gap) + w/2, y + 1.56),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4,
                                connectionstyle="bar,fraction=0.14"))
    ax.text(6.6, 6.62, "test patladı ya da çok yavaş: baştan — ama artık daha çok şey biliyorsun",
            ha="center", fontsize=8.4, color=ACCENT, style="italic")
    ax.text(6.6, 0.85, "Bu bir çizgi değil, döngüdür. Tıkandığın her yerde bir önceki adıma dön.",
            ha="center", fontsize=9.2, color=INK, weight="bold")
    return _save(fig, path)


def complexity_bands(path):
    """n kısıtından izin verilen karmaşıklığa geçiş tablosu (görsel)."""
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    ax.set_xlim(0, 13.0); ax.set_ylim(-0.5, 8.6); ax.axis("off")
    rows = [
        ("n ≤ 12",            "O(n!)",        "tüm permütasyonlar", EDGE[3]),
        ("n ≤ 25",            "O(2ⁿ)",        "tüm alt kümeler",    EDGE[3]),
        ("n ≤ 500",           "O(n³)",        "üç iç içe döngü",    EDGE[2]),
        ("n ≤ 5 000",         "O(n²)",        "iki iç içe döngü",   EDGE[2]),
        ("n ≤ 10⁶",           "O(n log n)",   "sıralama, böl-yönet", EDGE[1]),
        ("n ≤ 10⁸",           "O(n)",         "tek geçiş",          EDGE[1]),
        ("n > 10⁸ / 10¹⁸",    "O(log n), O(1)", "ikili arama, formül", EDGE[0]),
    ]
    ax.text(6.5, 8.15, "Kısıt sana algoritmayı söyler:  ~10⁸ işlem ≈ 1 saniye",
            ha="center", fontsize=10.4, color=INK, weight="bold")
    y = 7.3
    ax.text(1.6, y, "KISIT", ha="center", fontsize=8.6, color=MUTED, weight="bold")
    ax.text(4.9, y, "İZİN VERİLEN KARMAŞIKLIK", ha="center", fontsize=8.6,
            color=MUTED, weight="bold")
    ax.text(9.9, y, "TİPİK YAKLAŞIM", ha="center", fontsize=8.6, color=MUTED,
            weight="bold")
    ax.plot([0.3, 12.7], [y - 0.25, y - 0.25], color=RULE, lw=1)
    y -= 0.35
    for kisit, karm, ornek, edge in rows:
        y -= 0.95
        _box(ax, 0.4, y, 2.4, 0.75, kisit, "#FFFFFF", RULE, fs=9.6, tcol=INK)
        _box(ax, 3.1, y, 3.6, 0.75, karm, FILL[EDGE.index(edge)], edge,
             fs=10.2, bold=True, tcol=edge)
        ax.text(7.1, y + 0.37, ornek, ha="left", va="center", fontsize=9,
                color=MUTED)
    ax.text(6.5, -0.28,
            "Tersten oku: n = 100 000 görüyorsan O(n²) çözümün 10¹⁰ işlem demektir — daha yazmadan elenir.",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    return _save(fig, path)


def bruteforce_vs_hash(path):
    """İki Toplam: O(n²) çift döngü vs O(n) tek geçiş + hash."""
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    ax.set_xlim(0, 13.0); ax.set_ylim(0, 6.0); ax.axis("off")
    dizi = [2, 7, 11, 15, 1]
    hedef = 9
    # --- sol: brute force ---
    ax.text(3.2, 5.6, "KABA KUVVET — her çifti dene", ha="center", fontsize=9.6,
            color=EDGE[3], weight="bold")
    for i, v in enumerate(dizi):
        _box(ax, 0.5 + i*1.1, 3.9, 1.0, 0.8, str(v), FILL[0], EDGE[0],
             fs=10.5, bold=True)
    # eşleşme okları (i=0 ile hepsini dene)
    for j in range(1, 5):
        ax.annotate("", xy=(1.0 + j*1.1, 3.8), xytext=(1.0, 3.8),
                    arrowprops=dict(arrowstyle="-", color=EDGE[3], lw=0.9,
                                    alpha=0.45,
                                    connectionstyle="arc3,rad=-0.45"))
    ax.text(3.2, 2.55, "0-1, 0-2, 0-3, 0-4,\n1-2, 1-3, 1-4,  2-3, ...",
            ha="center", fontsize=8.4, color=MUTED, **MONO)
    _box(ax, 1.35, 1.35, 3.7, 0.8, "n(n−1)/2 çift  →  O(n²)", FILL[3], EDGE[3],
         fs=10, bold=True, tcol=EDGE[3])
    ax.plot([6.5, 6.5], [0.8, 5.2], color=RULE, lw=1)
    # --- sağ: hash ---
    ax.text(9.9, 5.6, "TEK GEÇİŞ — \"eşimi gördüm mü?\"", ha="center",
            fontsize=9.6, color=EDGE[1], weight="bold")
    for i, v in enumerate(dizi):
        vurgu = (i == 1)
        _box(ax, 7.0 + i*1.1, 3.9, 1.0, 0.8, str(v),
             FILL[1] if vurgu else "#FFFFFF", EDGE[1] if vurgu else RULE,
             fs=10.5, bold=True, tcol=INK)
    ax.text(8.1, 4.95, "şu an", ha="center", fontsize=7.8, color=EDGE[1])
    _arrow(ax, 8.1, 4.85, 8.1, 4.75, col=EDGE[1], lw=1.2)
    _box(ax, 7.2, 2.4, 4.3, 1.1, "", PAPER_BG := "#F7F6F2", RULE)
    ax.text(9.35, 3.22, "sözlük (görülenler):  {2 → 0}", ha="center",
            fontsize=8.8, color=INK, **MONO)
    ax.text(9.5, 2.72, "9 − 7 = 2 → sözlükte VAR → cevap (0,1)",
            ha="center", fontsize=7.8, color=EDGE[1], **MONO)
    _box(ax, 7.9, 1.35, 3.1, 0.8, "n adım  →  O(n)", FILL[1], EDGE[1],
         fs=10, bold=True, tcol=EDGE[1])
    ax.text(6.5, 0.35, "Takas: fazladan O(n) bellek karşılığında n kat hız. Optimizasyon çoğu zaman bir takastır.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def sliding_window(path):
    """Kayan pencere: üç anlık görüntü."""
    fig, ax = plt.subplots(figsize=(10.2, 4.4))
    ax.set_xlim(0, 14.6); ax.set_ylim(0, 6.4); ax.axis("off")
    s = "abcabcbb"
    snaps = [
        (0, 2, "pencere büyüyor: 'abc' (3)", EDGE[1]),
        (0, 3, "'a' tekrarı! sol kenar ilerler", EDGE[3]),
        (1, 3, "'bca' (3) — tekrar geçerli", EDGE[1]),
    ]
    y = 5.0
    for sol, sag, aciklama, edge in snaps:
        for i, ch in enumerate(s):
            icinde = sol <= i <= sag
            _box(ax, 1.9 + i*0.92, y, 0.84, 0.72, ch,
                 FILL[1] if icinde else "#FFFFFF",
                 edge if icinde else RULE, fs=11, bold=icinde,
                 tcol=INK if icinde else MUTED)
        ax.text(1.6, y + 0.36, "sol=%d sağ=%d" % (sol, sag), ha="right",
                va="center", fontsize=8, color=MUTED, **MONO)
        ax.text(9.6, y + 0.36, aciklama, ha="left", va="center", fontsize=8.6,
                color=edge)
        y -= 1.5
    ax.text(7.3, 6.05, "Kayan pencere: iki kenar da SAĞA gider, hiçbiri geri dönmez  →  toplam O(n)",
            ha="center", fontsize=9.6, color=INK, weight="bold")
    ax.text(7.3, 0.5,
            "İpucu: \"ardışık alt dizi/dizgi\" + \"en uzun/en kısa\" görürsen ilk düşüneceğin desen budur.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def two_pointers(path):
    """İki işaretçi: sıralı dizide uçlardan ortaya."""
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    ax.set_xlim(0, 12.0); ax.set_ylim(0, 4.8); ax.axis("off")
    dizi = [1, 3, 4, 6, 8, 11, 15]
    for i, v in enumerate(dizi):
        _box(ax, 1.6 + i*1.25, 2.4, 1.15, 0.85, str(v), FILL[0], EDGE[0],
             fs=11, bold=True)
    # sol ve sağ işaretçi
    _arrow(ax, 2.18, 1.85, 2.18, 2.32, col=EDGE[1], lw=1.6)
    ax.text(2.18, 1.55, "sol", ha="center", fontsize=9, color=EDGE[1],
            weight="bold", **MONO)
    _arrow(ax, 9.68, 1.85, 9.68, 2.32, col=EDGE[3], lw=1.6)
    ax.text(9.68, 1.55, "sağ", ha="center", fontsize=9, color=EDGE[3],
            weight="bold", **MONO)
    ax.text(6.0, 4.4, "Sıralı dizide hedef = 10 arıyoruz", ha="center",
            fontsize=9.8, color=INK, weight="bold")
    ax.text(6.0, 3.85, "toplam = 1 + 15 = 16 > 10  →  sağ'ı sola çek (küçült)",
            ha="center", fontsize=9, color=MUTED, **MONO)
    ax.text(6.0, 0.85, "toplam büyükse sağ--, küçükse sol++  →  her adımda bir eleman elenir: O(n)",
            ha="center", fontsize=9, color=EDGE[1])
    ax.text(6.0, 0.3, "Sıralılık, aramayı yarıya indiren bir BİLGİDİR — bedava gelmez, ama geldiyse kullan.",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


def ds_decision_tree(path):
    """Veri yapısı seçim karar ağacı."""
    fig, ax = plt.subplots(figsize=(9.4, 6.8))
    ax.set_xlim(0, 13.4); ax.set_ylim(-0.6, 11.4); ax.axis("off")
    ax.text(6.7, 11.0, "\"Hangi veri yapısını seçmeliyim?\"  —  önce ihtiyacını sor",
            ha="center", fontsize=10.6, color=INK, weight="bold")
    sorular = [
        ("Anahtarla erişim var mı?\n(\"ada göre bul\")", "Hash tablosu\ndict / map", EDGE[0]),
        ("Yalnız üyelik / benzersizlik?\n(\"gördüm mü?\")", "Küme\nset", EDGE[0]),
        ("İndeksle erişim + sıra?\n(\"i. eleman\")", "Dizi / dinamik dizi\narray, list", EDGE[1]),
        ("Yalnız uçlardan giriş-çıkış?\n(son giren / ilk giren)", "Yığın veya Kuyruk\nstack, queue, deque", EDGE[1]),
        ("Hep en küçük/büyük lazım?\n(öncelikli işlem)", "Yığın (heap)\npriority queue", EDGE[2]),
        ("Sıralı tut + aralık sorgusu?\n(\"5 ile 9 arası\")", "Dengeli arama ağacı\nBST / AVL", EDGE[2]),
        ("Önek/otomatik tamamlama?\n(\"me ile başlayanlar\")", "Trie\n(önek ağacı)", EDGE[4]),
        ("Nesneler arası İLİŞKİ var mı?\n(yol, bağlantı, bağımlılık)", "Çizge (graph)\nkomşuluk listesi", EDGE[3]),
    ]
    spine_x = 0.85
    y = 10.2
    for soru, cevap, edge in sorular:
        y -= 1.24
        ax.plot([spine_x, spine_x], [y + 0.55, 10.3], color=RULE, lw=1.1, zorder=0)
        ax.plot([spine_x, 1.5], [y + 0.55, y + 0.55], color=RULE, lw=1.1, zorder=0)
        _box(ax, 1.5, y, 5.5, 1.05, soru, "#FFFFFF", RULE, fs=8.6, tcol=INK)
        _arrow(ax, 7.05, y + 0.52, 7.75, y + 0.52, col=edge, lw=1.4)
        _box(ax, 7.8, y, 4.4, 1.05, cevap, FILL[EDGE.index(edge)], edge,
             fs=8.8, bold=True, tcol=edge)
    ax.text(6.7, -0.38,
            "Birden çok \"evet\" varsa yapıları BİRLEŞTİR: sözlük + yığın, dizi + hash… (Örnek 4'te yapacağız)",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(problem_cycle(os.path.join(out, "b05_cycle.png")))
    print(complexity_bands(os.path.join(out, "b05_bands.png")))
    print(bruteforce_vs_hash(os.path.join(out, "b05_twosum.png")))
    print(sliding_window(os.path.join(out, "b05_window.png")))
    print(two_pointers(os.path.join(out, "b05_pointers.png")))
    print(ds_decision_tree(os.path.join(out, "b05_dstree.png")))
