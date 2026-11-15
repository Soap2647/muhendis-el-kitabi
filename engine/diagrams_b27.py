# -*- coding: utf-8 -*-
"""Bolum 27 - Senkronizasyon diyagramlari.

Olcum grafikleri engine/veri/b27_kilit_olcum.csv ve
engine/veri/b27_false_sharing.csv dosyalarini okur. Oncelik
terslemesi zaman cizelgesi b27_oncelik_sim.py ciktisindan alinmistir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b27_%s.png" % ad)


def _tuval(w, h, xl=10, yl=10):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. sayac++ serpistirmesi ------------------------------------------ #
def rmw_serpistirme():
    fig, ax = _tuval(9.6, 5.4, xl=10, yl=11)
    ax.text(2.6, 10.5, "İş parçacığı 1", ha="center", fontsize=10.5,
            color=ACCENT_L, weight="bold")
    ax.text(7.4, 10.5, "İş parçacığı 2", ha="center", fontsize=10.5,
            color=EDGE[2], weight="bold")
    ax.text(0.15, 9.7, "zaman", fontsize=9, color=MUTED, rotation=90,
            va="center")
    adimlar = [
        (1, "oku: r1 = sayac  (0)", 2.6, FILL[0], EDGE[0]),
        (2, "oku: r2 = sayac  (0)", 7.4, FILL[2], EDGE[2]),
        (3, "artır: r1 = r1 + 1  (1)", 2.6, FILL[0], EDGE[0]),
        (4, "artır: r2 = r2 + 1  (1)", 7.4, FILL[2], EDGE[2]),
        (5, "yaz: sayac = r1  (1)", 2.6, FILL[0], EDGE[0]),
        (6, "yaz: sayac = r2  (1)  <- ilk yazmayı EZER", 7.4, FILL[3],
         ACCENT),
    ]
    for n, metin, x, fill, edge in adimlar:
        y = 8.6 - (n - 1) * 1.25
        _box(ax, x - 2.25, y, 4.5, 0.85, metin, fill, edge, fs=9.2)
    # serpistirme oklari (zaman ekseni)
    for n in range(5):
        y = 8.6 - n * 1.25
        ax.annotate("", xy=(0.45, y - 0.55), xytext=(0.45, y + 0.1),
                    arrowprops=dict(arrowstyle="-|>", color=RULE, lw=1.2))
    ax.text(5.0, 0.8, "Beklenen sayac = 2,  gerçek sayac = 1",
            ha="center", fontsize=10.5, color=ACCENT, weight="bold")
    ax.text(5.0, 0.2, "İki artış, tek artış olarak yazıldı: bir güncelleme "
            "kayboldu", ha="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("rmw_serpistirme"))


# 2. store buffering ------------------------------------------------- #
def store_buffering():
    fig, ax = _tuval(9.6, 5.0, xl=10, yl=9)
    _box(ax, 0.6, 6.8, 3.2, 1.0, "Çekirdek 1", FILL[0], EDGE[0], fs=10,
         bold=True)
    _box(ax, 6.2, 6.8, 3.2, 1.0, "Çekirdek 2", FILL[2], EDGE[2], fs=10,
         bold=True)
    _box(ax, 0.6, 4.6, 3.2, 1.0, "Tampon 1: x = 1", FILL[1], EDGE[1],
         fs=9.2)
    _box(ax, 6.2, 4.6, 3.2, 1.0, "Tampon 2: y = 1", FILL[1], EDGE[1],
         fs=9.2)
    _box(ax, 3.2, 1.0, 3.6, 1.2, "Bellek: x = 0, y = 0", FILL[4],
         EDGE[4], fs=10, bold=True)
    _arrow(ax, 2.2, 6.8, 2.2, 5.6, col=EDGE[0], lw=1.2)
    _arrow(ax, 7.8, 6.8, 7.8, 5.6, col=EDGE[2], lw=1.2)
    # yukleme: bellekten, tampon bypass'i (store'lar henüz bellekte degil)
    _arrow(ax, 3.2, 1.6, 0.9, 6.8, col=ACCENT, lw=1.3, rad=-0.2)
    _arrow(ax, 6.8, 1.6, 9.1, 6.8, col=ACCENT, lw=1.3, rad=0.2)
    ax.text(0.1, 2.5, "r1 = y  -> 0", fontsize=10, color=ACCENT,
            weight="bold")
    ax.text(7.9, 2.5, "r2 = x  -> 0", fontsize=10, color=ACCENT,
            weight="bold")
    ax.text(5.0, 8.3, "x = 1  yazar, sonra  r1 = y  okur",
            ha="center", fontsize=9.5, color=INK)
    ax.text(5.0, 0.2, "(r1, r2) = (0, 0): her iki okuma da eski değeri "
            "gördü", ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("store_buffering"))


# 3. acquire / release ----------------------------------------------- #
def acq_rel():
    fig, ax = _tuval(9.6, 4.6, xl=10, yl=9)
    ax.text(2.3, 8.4, "Üretici", ha="center", fontsize=11, color=EDGE[0],
            weight="bold")
    ax.text(7.7, 8.4, "Tüketici", ha="center", fontsize=11, color=EDGE[1],
            weight="bold")
    _box(ax, 0.5, 6.2, 3.6, 1.0, "veri = 42", FILL[0], EDGE[0], fs=10.5)
    _box(ax, 0.5, 4.3, 3.6, 1.2, "bayrak.store(1,\nrelease)", FILL[0],
         EDGE[0], fs=10)
    _box(ax, 5.9, 6.2, 3.6, 1.2, "while bayrak.load(\nacquire) == 0",
         FILL[1], EDGE[1], fs=9.8)
    _box(ax, 5.9, 4.3, 3.6, 1.0, "oku: r = veri", FILL[1], EDGE[1],
         fs=10.5)
    _arrow(ax, 2.3, 6.2, 2.3, 5.5, col=EDGE[0], lw=1.2)
    _arrow(ax, 4.1, 4.9, 5.9, 6.7, col=ACCENT, lw=1.9, rad=0.0)
    _arrow(ax, 7.7, 6.2, 7.7, 5.3, col=EDGE[1], lw=1.2)
    ax.text(5.6, 3.6, "eşleşir:\nyayın -> görünür", ha="center",
            fontsize=8.8, color=ACCENT, weight="bold")
    ax.text(5.0, 1.8, "release, önceki yazmaları (veri = 42) acquire'dan "
            "sonra görünür kılar.", ha="center", fontsize=9.2, color=INK)
    ax.text(5.0, 1.0, "relaxed'da bu sıralama garantisi yoktur.",
            ha="center", fontsize=9.2, color=MUTED)
    return _save(fig, _yol("acq_rel"))


# 4. kilit maliyeti olcumu (CSV) ------------------------------------- #
def _oku_ozet(yol, anahtar):
    """veri/*.csv ozet dosyasi: (grup, thread) -> medyan_ns."""
    ozet = {}
    with open(yol, encoding="utf-8") as f:
        for satir in csv.DictReader(f):
            k = (satir[anahtar], int(satir["thread"]))
            ozet[k] = float(satir["medyan_ns"])
    return ozet


def kilit_olcum():
    yol = os.path.join(VERI, "b27_kilit_olcum.csv")
    ozet = _oku_ozet(yol, "mod")
    modlar = [("atomik", "atomik (fetch_add)", EDGE[1]),
              ("mutex", "pthread_mutex", EDGE[0]),
              ("ttas", "TTAS spin", EDGE[2]),
              ("tas", "TAS spin", ACCENT)]
    iplikler = [1, 2, 4, 8, 16]
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    for mod, etiket, renk in modlar:
        med = [ozet[(mod, t)] for t in iplikler]
        ax.plot(iplikler, med, marker="o", color=renk, lw=1.8,
                label=etiket)
    ax.set_xscale("log", base=2)
    ax.set_xticks(iplikler)
    ax.set_xticklabels([str(t) for t in iplikler])
    ax.set_xlabel("İş parçacığı sayısı", color=INK)
    ax.set_ylabel("İşlem başına süre (ns, düşük = iyi)", color=INK)
    ax.set_title("Kilit maliyeti: 16 mantıksal çekirdek, medyan 5 çalışma",
                 fontsize=10.5, color=INK)
    ax.grid(True, color=RULE, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    fig.tight_layout()
    return _save(fig, _yol("kilit_olcum"))


# 5. sinirli tampon + condvar ---------------------------------------- #
def tampon_condvar():
    fig, ax = _tuval(9.6, 4.8, xl=10, yl=8.2)
    _box(ax, 0.3, 2.9, 2.6, 2.0, "Üreticiler\n(P thread)", FILL[0],
         EDGE[0], fs=10)
    _box(ax, 3.7, 2.7, 2.6, 2.4, "mutex\n(tek kilit)", FILL[3],
         EDGE[3], fs=10, bold=True)
    _box(ax, 7.1, 2.9, 2.6, 2.0, "Tüketiciler\n(C thread)", FILL[1],
         EDGE[1], fs=10)
    # tampon hucreleri
    for i in range(8):
        ax.add_patch(Rectangle((0.6 + i * 1.1, 0.25), 1.0, 0.9,
                               facecolor=FILL[2], edgecolor=EDGE[2],
                               lw=1.0))
    ax.text(0.6, 1.4, "Tampon (dairesel, kapasite 16)", fontsize=9.5,
            color=INK, weight="bold")
    _arrow(ax, 2.9, 3.9, 3.7, 3.9, col=EDGE[0], lw=1.3)
    _arrow(ax, 6.3, 3.9, 7.1, 3.9, col=EDGE[1], lw=1.3)
    _box(ax, 3.4, 1.9, 1.5, 0.6, "dolu_değil", FILL[3], EDGE[3], fs=8.5)
    _box(ax, 5.1, 1.9, 1.5, 0.6, "bos_degil", FILL[3], EDGE[3], fs=8.5)
    _arrow(ax, 4.15, 2.7, 4.15, 2.55, col=EDGE[3], lw=1.0)
    _arrow(ax, 5.85, 2.7, 5.85, 2.55, col=EDGE[3], lw=1.0)
    ax.text(5.0, 6.7, "pthread_cond_wait kilidi bırakır, uyanınca geri "
            "alır", ha="center", fontsize=9.2, color=MUTED)
    return _save(fig, _yol("tampon_condvar"))


# 6. kaynak tahsis grafi (deadlock dongusu) -------------------------- #
def kaynak_grafi():
    fig, ax = _tuval(9.0, 5.0, xl=10, yl=8)
    _box(ax, 0.6, 5.2, 2.6, 1.3, "İş parçacığı T1", FILL[0], EDGE[0],
         fs=10, bold=True)
    _box(ax, 6.8, 5.2, 2.6, 1.3, "İş parçacığı T2", FILL[2], EDGE[2],
         fs=10, bold=True)
    _box(ax, 0.6, 1.2, 2.6, 1.3, "Kilit A", FILL[1], EDGE[1], fs=10,
         bold=True)
    _box(ax, 6.8, 1.2, 2.6, 1.3, "Kilit B", FILL[4], EDGE[4], fs=10,
         bold=True)
    # T1 kilit A'ya sahip (kilit -> is parcacigi)
    _arrow(ax, 1.9, 2.5, 1.9, 5.2, col=EDGE[1], lw=1.7)
    ax.text(2.1, 3.7, "sahip", fontsize=9, color=EDGE[1])
    # T2 kilit B'ye sahip
    _arrow(ax, 8.1, 2.5, 8.1, 5.2, col=EDGE[4], lw=1.7)
    ax.text(8.3, 3.7, "sahip", fontsize=9, color=EDGE[4])
    # T1 -> B bekliyor
    _arrow(ax, 3.3, 5.8, 6.8, 2.0, col=ACCENT, lw=1.7, rad=0.25)
    ax.text(4.6, 3.6, "bekliyor", fontsize=9, color=ACCENT, weight="bold")
    # T2 -> A bekliyor
    _arrow(ax, 6.8, 5.8, 3.3, 2.0, col=ACCENT, lw=1.7, rad=0.25)
    ax.text(4.4, 5.9, "bekliyor", fontsize=9, color=ACCENT, weight="bold")
    ax.text(5.0, 0.3, "Döngü var: T1 -> B -> T2 -> A -> T1. "
            "Kimse ilerleyemez.", ha="center", fontsize=9.5, color=INK)
    return _save(fig, _yol("kaynak_grafi"))


# 7. yemek yiyen filozoflar ------------------------------------------ #
def filozof():
    import math
    fig, ax = _tuval(7.6, 6.6, xl=10, yl=10)
    ax.set_aspect("equal")
    merkez = (5.0, 5.2)
    yaricap = 3.1
    for i in range(5):
        aci = math.pi / 2 + 2 * math.pi * i / 5
        px = merkez[0] + yaricap * math.cos(aci)
        py = merkez[1] + yaricap * math.sin(aci)
        ax.add_patch(Circle((px, py), 0.75, facecolor=FILL[1],
                            edgecolor=EDGE[1], lw=1.2))
        ax.text(px, py, "P%d" % i, ha="center", va="center", fontsize=10,
                weight="bold", color=INK)
        # catal: iki filozof arasinda, ortada
        aci2 = aci + math.pi / 5
        cx = merkez[0] + (yaricap - 1.45) * math.cos(aci2)
        cy = merkez[1] + (yaricap - 1.45) * math.sin(aci2)
        ax.add_patch(Circle((cx, cy), 0.28, facecolor=ACCENT, lw=0))
        # P_i ile P_(i+1) arasindaki catal, P_(i+1)'in sol catali (i+1)
        ax.text(cx, cy - 0.62, "ç%d" % ((i + 1) % 5), ha="center",
                fontsize=8.5,
                color=ACCENT, weight="bold")
    ax.text(5.0, 5.2, "Herkes\nsol çatalını\naldı", ha="center",
            va="center", fontsize=10, color=INK)
    ax.text(5.0, 0.6, "Sağ çatal herkeste alınmak için bekliyor: "
            "kilitlenme", ha="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("filozof"))


# 8. oncelik terslemesi zaman cizelgesi ------------------------------ #
def oncelik_zaman():
    # b27_oncelik_sim.py ciktisi (tick = 1 birim)
    kalitimsiz = {"L": [(0, 2), (6, 7)], "M": [(2, 6)], "H": [(8, 9)]}
    kalitimli = {"L": [(0, 3)], "H": [(4, 5)], "M": [(6, 10)]}
    kilit_bekleme = {"kalitimsiz": (1, 7), "kalitimli": (1, 3)}
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 5.0), sharex=True)
    renk = {"L": EDGE[1], "M": EDGE[2], "H": ACCENT}
    for ax, veri, baslik, anahtar in (
            (axes[0], kalitimsiz, "Öncelik kalıtımı YOK",
             "kalitimsiz"),
            (axes[1], kalitimli, "Öncelik kalıtımı VAR",
             "kalitimli")):
        satirlar = ["H", "M", "L"]
        for k, gorev in enumerate(satirlar):
            y = 2 - k
            for a, b in veri.get(gorev, []):
                ax.broken_barh([(a, b - a)], (y - 0.3, 0.6),
                               facecolors=renk[gorev], edgecolors="none")
        bas, son = kilit_bekleme[anahtar]
        ax.broken_barh([(bas, son - bas)], (1.75, 0.5),
                       facecolors="none", edgecolors=ACCENT, hatch="///",
                       lw=0.8)
        ax.set_yticks([2, 1, 0])
        ax.set_yticklabels(["H (3)", "M (2)", "L (1)"], fontsize=9)
        ax.set_title(baslik, fontsize=10, loc="left", color=INK)
        ax.set_xlim(0, 10)
        ax.set_ylim(-0.6, 2.7)
        ax.grid(True, axis="x", color=RULE, lw=0.7)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[1].set_xlabel("zaman (tick)", color=INK)
    axes[0].text(0.1, 2.45, "Taralı alan: H kilidi bekliyor (6 tick)",
                 fontsize=9, color=ACCENT, weight="bold")
    axes[1].text(0.1, 2.45, "Taralı alan: H kilidi bekliyor (2 tick)",
                 fontsize=9, color=ACCENT, weight="bold")
    fig.tight_layout()
    return _save(fig, _yol("oncelik_zaman"))


# 9. sahte paylasim olcumu (CSV) ------------------------------------- #
def false_sharing():
    yol = os.path.join(VERI, "b27_false_sharing.csv")
    ozet = _oku_ozet(yol, "yerlesim")
    iplikler = [1, 2, 4, 8, 16]
    bitisik = [ozet[("bitisik", t)] for t in iplikler]
    ayri = [ozet[("ayri", t)] for t in iplikler]
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    x = range(len(iplikler))
    genislik = 0.38
    b1 = ax.bar([i - genislik / 2 for i in x], bitisik, genislik,
                color=ACCENT, label="Bitişik (aynı önbellek satırı)")
    b2 = ax.bar([i + genislik / 2 for i in x], ayri, genislik,
                color=EDGE[0], label="64 bayt hizalı (ayrı satır)")
    for bar, deger in list(zip(b1, bitisik)) + list(zip(b2, ayri)):
        ax.text(bar.get_x() + bar.get_width() / 2, deger + 1.5,
                "%.1f" % deger, ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(t) for t in iplikler])
    ax.set_xlabel("İş parçacığı sayısı (her biri kendi sayacını artırır)",
                  color=INK)
    ax.set_ylabel("İşlem başına süre (ns)", color=INK)
    ax.set_title("Sahte paylaşım: aynı işi, farklı bellek yerleşimi",
                 fontsize=10.5, loc="left", color=INK)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", color=RULE, lw=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return _save(fig, _yol("false_sharing"))


# 10. ABA senaryosu -------------------------------------------------- #
def aba_senaryo():
    fig, ax = _tuval(9.6, 5.6, xl=10, yl=10)
    adimlar = [
        ("1) Başlangıç", "A -> B -> C", FILL[0], EDGE[0]),
        ("2) T1 A'yı ve B'yi okudu,\n    duraklatıldı", "T1: eski=A, "
         "sonraki=B", FILL[2], EDGE[2]),
        ("3) T2: A ve B'yi çıkardı,\n    A'yı geri itti", "A -> C",
         FILL[1], EDGE[1]),
        ("4) T1 CAS(head, A, B)\n    başarılı: head = B", "B -> C\n"
         "(A kayboldu)", FILL[3], ACCENT),
        ("5) T2 B'yi geri itti", "B -> B  (DÖNGÜ)", FILL[3], ACCENT),
    ]
    for k, (baslik, yigin, fill, edge) in enumerate(adimlar):
        x = 0.3 + (k % 3) * 3.3
        y = 6.3 if k < 3 else 2.2
        _box(ax, x, y, 3.0, 2.4, "", fill, edge)
        ax.text(x + 0.15, y + 2.05, baslik, fontsize=8.2, color=INK,
                va="center", weight="bold")
        ax.text(x + 1.5, y + 0.9, "head: " + yigin, fontsize=8.8,
                ha="center", va="center", color=INK)
    ax.text(0.4, 1.2, "Etiketsiz head: 4. adımda CAS yalnız işaretçi "
            "değerine bakar; A'nın yeniden gelmesi bunu fark edilmez kılar.",
            fontsize=8.6, color=MUTED)
    ax.text(0.4, 0.5, "Etiketli head: 4. adımda etiket 0 -> 3 olduğu için "
            "CAS başarısız olur.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("aba"))


if __name__ == "__main__":
    for f in (rmw_serpistirme, store_buffering, acq_rel, kilit_olcum,
              tampon_condvar, kaynak_grafi, filozof, oncelik_zaman,
              false_sharing, aba_senaryo):
        print(f())
