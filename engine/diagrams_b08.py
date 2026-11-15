# -*- coding: utf-8 -*-
"""Bölüm 8 — 'Stack & Queue' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def stack_lifo(path):
    """Yığın: push/pop hep aynı uçtan (LIFO)."""
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 5.6); ax.axis("off")
    ax.text(7.0, 5.25, "Yığın (stack): ekleme de çıkarma da TEK uçtan — "
            "son giren ilk çıkar (LIFO)",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    durumlar = [
        ("push(A)", ["A"]),
        ("push(B)", ["A", "B"]),
        ("push(C)", ["A", "B", "C"]),
        ("pop() → C", ["A", "B"]),
    ]
    x0 = 0.9
    for k, (islem, icerik) in enumerate(durumlar):
        x = x0 + k * 3.35
        ax.text(x + 0.85, 4.55, islem, ha="center", fontsize=9.4,
                color=EDGE[0] if "push" in islem else EDGE[3],
                weight="bold", **MONO)
        # kap
        ax.plot([x, x], [1.05, 3.95], color=MUTED, lw=1.4)
        ax.plot([x + 1.7, x + 1.7], [1.05, 3.95], color=MUTED, lw=1.4)
        ax.plot([x, x + 1.7], [1.05, 1.05], color=MUTED, lw=1.4)
        for i, v in enumerate(icerik):
            ust = (i == len(icerik) - 1)
            _box(ax, x + 0.12, 1.15 + i*0.82, 1.46, 0.72, v,
                 FILL[3] if ust else FILL[0], EDGE[3] if ust else EDGE[0],
                 fs=11, bold=True)
        if icerik:
            ty = 1.15 + (len(icerik) - 1)*0.82 + 0.36
            _arrow(ax, x + 2.32, ty, x + 1.78, ty, col=EDGE[3], lw=1.3)
            ax.text(x + 2.42, ty, "tepe", ha="left", va="center",
                    fontsize=7.8, color=EDGE[3], weight="bold")
    ax.text(7.0, 0.45, "Erişimi kısıtlamak bir kayıp değil, bir GÜVENCEDİR: "
            "tek uç = O(1) işlem + hatasız kullanım.",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    return _save(fig, path)


def call_stack(path):
    """Çağrı yığını: çerçeveler, dönüş adresi, özyineleme."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 7.0); ax.axis("off")
    ax.text(7.0, 6.65, "faktoriyel(3) çağrısı sırasında yığın — her çağrı bir ÇERÇEVE",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    cerceveler = [
        ("main()", "n yok · dönüş: OS", FILL[0], EDGE[0]),
        ("faktoriyel(3)", "n=3 · dönüş: main+1", FILL[1], EDGE[1]),
        ("faktoriyel(2)", "n=2 · dönüş: fakt+1", FILL[2], EDGE[2]),
        ("faktoriyel(1)", "n=1 · taban durum", FILL[3], EDGE[3]),
    ]
    y = 1.15
    for ad, alt, fill, edge in cerceveler:
        _box(ax, 1.6, y, 5.2, 1.12, "", fill, edge)
        ax.text(1.95, y + 0.74, ad, ha="left", fontsize=9.6, color=edge,
                weight="bold", **MONO)
        ax.text(1.95, y + 0.28, alt, ha="left", fontsize=8, color=INK)
        y += 1.24
    ax.annotate("", xy=(1.15, 5.15), xytext=(1.15, 1.2),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.5))
    ax.text(0.75, 3.2, "büyüme yönü", rotation=90, ha="center", va="center",
            fontsize=8, color=MUTED)
    _arrow(ax, 7.55, 4.95, 6.9, 4.95, col=EDGE[3], lw=1.5)
    ax.text(7.7, 4.95, "SP (yığın tepesi)", ha="left", va="center",
            fontsize=8.6, color=EDGE[3], weight="bold", **MONO)
    notlar = [
        ("Her çerçevede ne var?", INK, True),
        ("· parametreler (n)", MUTED, False),
        ("· yerel değişkenler", MUTED, False),
        ("· DÖNÜŞ ADRESİ — nereye geri döneceğim", EDGE[3], False),
        ("", MUTED, False),
        ("return: çerçeve atılır, SP geri iner,", INK, False),
        ("dönüş adresine atlanır.", INK, False),
        ("", MUTED, False),
        ("Taban durum yoksa yığın büyür ve", EDGE[3], True),
        ("çarpar: stack overflow.", EDGE[3], True),
    ]
    yy = 4.30
    for metin, renk, kalin in notlar:
        if metin:
            ax.text(7.7, yy, metin, ha="left", fontsize=8.2, color=renk,
                    weight="bold" if kalin else "normal")
        yy -= 0.355
    ax.text(7.0, 0.4, "Bölüm 1'de \"stack segmenti\" demiştik; işte içi. "
            "Bölüm 15'te özyinelemeyi bu resimle çözeceğiz.",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


def queue_fifo(path):
    """Kuyruk: naif dizi sorunu ve dairesel çözüm."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 6.6); ax.axis("off")
    ax.text(7.0, 6.3, "Kuyruk (queue): arkadan girer, önden çıkar — "
            "ilk giren ilk çıkar (FIFO)",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    # naif
    ax.text(0.5, 5.5, "NAİF DİZİ: çıkarınca herkesi sola kaydır  →  O(n)",
            fontsize=9, color=EDGE[3], weight="bold")
    for i, v in enumerate(["A", "B", "C", "", ""]):
        _box(ax, 1.4 + i*1.35, 4.0, 1.22, 0.78, v,
             FILL[0] if v else "#FFFFFF", EDGE[0] if v else RULE,
             fs=11, bold=True)
    _arrow(ax, 1.0, 4.39, 1.35, 4.39, col=EDGE[3], lw=1.4)
    ax.text(0.9, 4.39, "çık", ha="right", va="center", fontsize=8.2,
            color=EDGE[3], **MONO)
    ax.annotate("", xy=(2.0, 3.72), xytext=(4.6, 3.72),
                arrowprops=dict(arrowstyle="-|>", color=EDGE[3], lw=1.3))
    ax.text(4.9, 3.72, "hepsi kayıyor", ha="left", va="center", fontsize=8.2,
            color=EDGE[3])
    _arrow(ax, 8.2, 4.39, 7.85, 4.39, col=MUTED, lw=1.4)
    ax.text(8.35, 4.39, "gir", ha="left", va="center", fontsize=8.2,
            color=MUTED, **MONO)
    # dairesel
    ax.text(0.5, 3.35, "DAİRESEL DİZİ: iki indeks sarar, kaydırma YOK  →  O(1)",
            fontsize=9, color=EDGE[1], weight="bold")
    for i in range(8):
        dolu = i in (5, 6, 7, 0)
        etiket = {5: "A", 6: "B", 7: "C", 0: "D"}.get(i, "")
        _box(ax, 1.4 + i*1.35, 1.55, 1.22, 0.78, etiket,
             FILL[1] if dolu else "#FFFFFF", EDGE[1] if dolu else RULE,
             fs=11, bold=True)
        ax.text(1.4 + i*1.35 + 0.61, 1.2, str(i), ha="center", fontsize=7.6,
                color=MUTED, **MONO)
    _arrow(ax, 1.4 + 5*1.35 + 0.61, 2.75, 1.4 + 5*1.35 + 0.61, 2.4,
           col=EDGE[0], lw=1.4)
    ax.text(1.4 + 5*1.35 + 0.61, 2.92, "bas", ha="center", fontsize=8,
            color=EDGE[0], weight="bold", **MONO)
    _arrow(ax, 1.4 + 1*1.35 + 0.61, 2.75, 1.4 + 1*1.35 + 0.61, 2.4,
           col=EDGE[3], lw=1.4)
    ax.text(1.4 + 1*1.35 + 0.61, 2.92, "kuyruk", ha="center", fontsize=8,
            color=EDGE[3], weight="bold", **MONO)
    ax.text(7.0, 0.55, "Bölüm 7'nin dairesel tamponu, kuyruğun doğal gerçeklemesidir: "
            "(i + 1) % BOYUT",
            ha="center", fontsize=9, color=ACCENT, weight="bold", **MONO)
    return _save(fig, path)


def bfs_layers(path):
    """BFS: kuyruk sayesinde katman katman gezinme."""
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 6.2); ax.axis("off")
    ax.text(7.0, 5.85, "Kuyruk = katman katman keşif. BFS'in \"en kısa yol\" "
            "bulmasının tek sebebi budur.",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    import numpy as _np
    dugumler = {"A": (2.2, 4.3), "B": (4.6, 5.0), "C": (4.6, 3.6),
                "D": (7.0, 5.0), "E": (7.0, 3.6), "F": (9.4, 4.3)}
    kenarlar = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "E"),
                ("D", "F"), ("E", "F")]
    katman = {"A": 0, "B": 1, "C": 1, "D": 2, "E": 2, "F": 3}
    renkler = [EDGE[3], EDGE[0], EDGE[1], EDGE[2]]
    dolgular = [FILL[3], FILL[0], FILL[1], FILL[2]]
    for a, b in kenarlar:
        x1, y1 = dugumler[a]; x2, y2 = dugumler[b]
        ax.plot([x1, x2], [y1, y2], color=RULE, lw=1.3, zorder=0)
    for ad, (x, y) in dugumler.items():
        k = katman[ad]
        c = plt.Circle((x, y), 0.38, facecolor=dolgular[k],
                       edgecolor=renkler[k], lw=1.6, zorder=3)
        ax.add_patch(c)
        ax.text(x, y, ad, ha="center", va="center", fontsize=11,
                color=renkler[k], weight="bold", zorder=4)
    for k, (x, lab) in enumerate([(2.2, "katman 0"), (4.6, "katman 1"),
                                  (7.0, "katman 2"), (9.4, "katman 3")]):
        ax.text(x, 2.75, lab, ha="center", fontsize=8.2, color=renkler[k],
                weight="bold")
    _box(ax, 1.5, 1.15, 10.4, 1.0, "", "#F7F6F2", RULE)
    ax.text(1.85, 1.86, "kuyruk zamanla:", ha="left", fontsize=8.4,
            color=MUTED, weight="bold")
    ax.text(1.85, 1.42, "[A]  →  [B, C]  →  [C, D]  →  [D, E]  →  [E, F]  →  [F]  →  []",
            ha="left", fontsize=9.2, color=INK, **MONO)
    ax.text(7.0, 0.5, "Yığın kullansaydın derine dalardın (DFS) ve bulduğun yol "
            "en kısa OLMAYABİLİRDİ.",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    return _save(fig, path)


def deque_diagram(path):
    """Deque: iki uçtan da O(1)."""
    fig, ax = plt.subplots(figsize=(9.6, 3.2))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 4.6); ax.axis("off")
    ax.text(7.0, 4.25, "Deque (çift uçlu kuyruk): her iki uçtan da ekleme ve "
            "çıkarma O(1)",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    for i, v in enumerate(["A", "B", "C", "D"]):
        _box(ax, 4.4 + i*1.35, 2.0, 1.22, 0.85, v, FILL[0], EDGE[0],
             fs=11.5, bold=True)
    _arrow(ax, 3.1, 2.72, 4.3, 2.72, col=EDGE[1], lw=1.6)
    ax.text(3.0, 2.72, "sola ekle", ha="right", va="center", fontsize=8.4,
            color=EDGE[1], weight="bold")
    _arrow(ax, 4.3, 2.12, 3.1, 2.12, col=EDGE[3], lw=1.6)
    ax.text(3.0, 2.12, "soldan çıkar", ha="right", va="center", fontsize=8.4,
            color=EDGE[3], weight="bold")
    _arrow(ax, 10.9, 2.72, 9.85, 2.72, col=EDGE[1], lw=1.6)
    ax.text(11.0, 2.72, "sağa ekle", ha="left", va="center", fontsize=8.4,
            color=EDGE[1], weight="bold")
    _arrow(ax, 9.85, 2.12, 10.9, 2.12, col=EDGE[3], lw=1.6)
    ax.text(11.0, 2.12, "sağdan çıkar", ha="left", va="center", fontsize=8.4,
            color=EDGE[3], weight="bold")
    ax.text(7.0, 1.25, "Yığın da kuyruk da deque'in kısıtlanmış hâlidir. "
            "Python: collections.deque",
            ha="center", fontsize=9, color=INK, **MONO)
    ax.text(7.0, 0.6, "Kayan pencerede maksimumu O(n)'de tutmak, sıra geçmişi, "
            "geri-ileri gezinme — hep deque işidir.",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


def monotonic_stack(path):
    """Monotonik yığın: sonraki büyük eleman."""
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.set_xlim(0, 14.0); ax.set_ylim(0, 6.6); ax.axis("off")
    ax.text(7.0, 6.25, "Monotonik yığın: \"benden büyüğü gelince cevabım "
            "bulundu\" — her eleman bir kez girer, bir kez çıkar",
            ha="center", fontsize=9.8, color=INK, weight="bold")
    dizi = [2, 1, 2, 4, 3]
    for i, v in enumerate(dizi):
        _box(ax, 1.6 + i*1.5, 5.05, 1.32, 0.72, str(v), FILL[0], EDGE[0],
             fs=11, bold=True)
        ax.text(1.6 + i*1.5 + 0.66, 4.75, "i=%d" % i, ha="center", fontsize=7.6,
                color=MUTED, **MONO)
    adimlar = [
        ("i=0, v=2", "yığın boş → 2'yi it", "[2]", EDGE[0]),
        ("i=1, v=1", "1 < 2 → sadece it", "[2, 1]", EDGE[0]),
        ("i=2, v=2", "2 > 1 → 1'in cevabı = 2, çıkar; sonra it", "[2, 2]", EDGE[3]),
        ("i=3, v=4", "4 > 2, 4 > 2 → ikisinin cevabı = 4", "[4]", EDGE[3]),
        ("i=4, v=3", "3 < 4 → sadece it", "[4, 3]", EDGE[0]),
    ]
    y = 4.05
    for baslik, aciklama, yigin, renk in adimlar:
        ax.text(1.0, y, baslik, ha="left", va="center", fontsize=8.4,
                color=renk, weight="bold", **MONO)
        ax.text(3.3, y, aciklama, ha="left", va="center", fontsize=8.4,
                color=INK)
        ax.text(13.6, y, yigin, ha="right", va="center", fontsize=8.4,
                color=MUTED, **MONO)
        y -= 0.66
    ax.text(7.0, 0.62, "Toplam iş: n itme + en fazla n çıkarma  →  O(n)  "
            "(kaba kuvvet O(n²) olurdu)",
            ha="center", fontsize=9.2, color=ACCENT, weight="bold")
    ax.text(7.0, 0.15, "İçeride while var ama toplam maliyet doğrusal — "
            "Bölüm 7'deki amortize akıl yürütmenin aynısı.",
            ha="center", fontsize=8.4, color=MUTED, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(stack_lifo(os.path.join(out, "b08_stack.png")))
    print(call_stack(os.path.join(out, "b08_callstack.png")))
    print(queue_fifo(os.path.join(out, "b08_queue.png")))
    print(bfs_layers(os.path.join(out, "b08_bfs.png")))
    print(deque_diagram(os.path.join(out, "b08_deque.png")))
    print(monotonic_stack(os.path.join(out, "b08_monotonic.png")))
