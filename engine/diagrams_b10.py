# -*- coding: utf-8 -*-
"""Bölüm 10 — 'Tree' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import math
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}
OLCEK = 0.72      # inç / birim: x ve y aynı ölçekte -> daireler bozulmaz
R = 0.28          # düğüm yarıçapı (birim)

# Ortak örnek ağaç (BST): 8 kökü; sol 3, sağ 10
T = (8, (3, (1, None, None),
            (6, (4, None, None), (7, None, None))),
        (10, None, (14, (13, None, None), None)))


def _tuval(xr, yr, olcek=OLCEK):
    fig = plt.figure(figsize=(xr * olcek, yr * olcek))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xr)
    ax.set_ylim(0, yr)
    ax.axis("off")
    return fig, ax


def _kenar(ax, a, b, col=MUTED, lw=1.3):
    (x1, y1), (x2, y2) = a, b
    d = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    ax.plot([x1 + ux * R, x2 - ux * R], [y1 + uy * R, y2 - uy * R],
            color=col, lw=lw, zorder=1, solid_capstyle="round")


def _dugum(ax, p, metin, dolgu=FILL[0], kenar=EDGE[0], fs=9.6, tcol=INK):
    ax.add_patch(Circle(p, R, facecolor=dolgu, edgecolor=kenar, lw=1.3,
                        zorder=3))
    ax.text(p[0], p[1], metin, ha="center", va="center", fontsize=fs,
            color=tcol, weight="bold", zorder=4)


def _yerlesim(agac, x0, x1, ust, dy):
    """İkili ağaç -> (pos, kenarlar). pos: yol -> (x, y, değer).
    x: inorder sırası (eşit aralıklı), y: derinlik. Yol: 'L'/'R' dizgisi."""
    sira = []

    def gez(d, yol, dep):
        if d is None:
            return
        gez(d[1], yol + "L", dep + 1)
        sira.append((yol, d[0], dep))
        gez(d[2], yol + "R", dep + 1)

    gez(agac, "", 0)
    n = len(sira)
    pos = {}
    for k, (yol, v, dep) in enumerate(sira):
        x = x0 + k * (x1 - x0) / (n - 1) if n > 1 else (x0 + x1) / 2
        pos[yol] = (x, ust - dep * dy, v)
    kenarlar = [(y, y + c) for y in pos for c in ("L", "R") if y + c in pos]
    return pos, kenarlar


def _agac_ciz(ax, agac, x0, x1, ust, dy, stil=None, kstil=None):
    """stil: yol -> (dolgu, kenar). kstil: (ata, çocuk) -> renk."""
    pos, kenarlar = _yerlesim(agac, x0, x1, ust, dy)
    for a, b in kenarlar:
        renk = (kstil or {}).get((a, b), MUTED)
        _kenar(ax, pos[a][:2], pos[b][:2], col=renk,
               lw=2.4 if renk != MUTED else 1.3)
    for yol, (x, y, v) in pos.items():
        dolgu, kenar = (stil or {}).get(yol, (FILL[0], EDGE[0]))
        _dugum(ax, (x, y), str(v), dolgu, kenar)
    return pos


def _yigin_ciz(ax, dizi, x0, x1, ust, dy, stil=None, kstil=None):
    """Dizi gösterimi: i. düğümün derinliği floor(log2(i+1)).
    Seviyedeki sırası k = i - (2^d - 1); x, seviyeyi 2^d dilime böler."""
    n = len(dizi)
    pos = {}
    for i in range(n):
        d = (i + 1).bit_length() - 1
        k = i - (2 ** d - 1)
        pos[i] = (x0 + (k + 0.5) * (x1 - x0) / (2 ** d), ust - d * dy)
    for i in range(n):
        for c in (2 * i + 1, 2 * i + 2):
            if c < n:
                renk = (kstil or {}).get((i, c), MUTED)
                _kenar(ax, pos[i], pos[c], col=renk,
                       lw=2.4 if renk != MUTED else 1.3)
    for i in range(n):
        dolgu, kenar = (stil or {}).get(i, (FILL[0], EDGE[0]))
        _dugum(ax, pos[i], str(dizi[i]), dolgu, kenar)
    return pos


# --------------------------------------------------------------------------- #
def terminoloji(path):
    """Kök, iç düğüm, yaprak, derinlik ve yükseklik."""
    fig, ax = _tuval(12, 5.4)
    ax.text(6.0, 5.1, "Ağaç terminolojisi", ha="center", fontsize=10.6,
            color=INK, weight="bold")
    P = {"A": (3.2, 4.1), "B": (1.6, 2.9), "C": (4.8, 2.9),
         "D": (0.8, 1.7), "E": (2.4, 1.7), "F": (4.8, 1.7),
         "G": (0.8, 0.5)}
    for a, b in [("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"),
                 ("C", "F"), ("D", "G")]:
        _kenar(ax, P[a], P[b])
    stil = {"A": (FILL[3], EDGE[3]),
            "B": (FILL[0], EDGE[0]), "C": (FILL[0], EDGE[0]),
            "D": (FILL[0], EDGE[0]),
            "E": (FILL[1], EDGE[1]), "F": (FILL[1], EDGE[1]),
            "G": (FILL[1], EDGE[1])}
    for k, p in P.items():
        _dugum(ax, p, k, *stil[k])
    lejant = [(4.1, "A: kök (derinlik 0)", FILL[3], EDGE[3]),
              (3.2, "B, C, D: iç düğüm (en az bir çocuk)", FILL[0], EDGE[0]),
              (2.3, "E, F, G: yaprak (hiç çocuğu yok)", FILL[1], EDGE[1])]
    for y, metin, dolgu, kenar in lejant:
        _dugum(ax, (6.5, y), "", dolgu, kenar)
        ax.text(7.1, y, metin, ha="left", va="center", fontsize=9, color=INK)
    for y, metin in [(1.4, "E'nin derinliği = 2 (kökten kenar sayısı)"),
                     (0.8, "D'nin yüksekliği = 1 (en uzun alt yol)"),
                     (0.2, "Ağacın yüksekliği = 3 (A-B-D-G)")]:
        ax.text(7.1, y, metin, ha="left", va="center", fontsize=9,
                color=ACCENT if "Ağacın" in metin else INK,
                weight="bold" if "Ağacın" in metin else "normal")
    return _save(fig, path)


def gezinme(path):
    """Aynı ağaç üzerinde dört gezinme sırası."""
    def ino(d):
        return [] if d is None else ino(d[1]) + [d[0]] + ino(d[2])

    def pre(d):
        return [] if d is None else [d[0]] + pre(d[1]) + pre(d[2])

    def post(d):
        return [] if d is None else post(d[1]) + post(d[2]) + [d[0]]

    def lvl(d):
        kuyruk, cikti = ([d] if d else []), []
        while kuyruk:
            x = kuyruk.pop(0)
            cikti.append(x[0])
            kuyruk += [c for c in (x[1], x[2]) if c]
        return cikti

    assert ino(T) == [1, 3, 4, 6, 7, 8, 10, 13, 14]
    assert pre(T) == [8, 3, 1, 6, 4, 7, 10, 14, 13]
    assert post(T) == [1, 4, 7, 6, 3, 13, 14, 10, 8]
    assert lvl(T) == [8, 3, 10, 1, 6, 14, 4, 7, 13]

    fig, ax = _tuval(14, 5.4)
    ax.text(7.0, 5.12, "Aynı ağaç, dört gezinme", ha="center", fontsize=10.6,
            color=INK, weight="bold")
    _agac_ciz(ax, T, 0.8, 6.4, 4.5, 1.12)
    satirlar = [
        (4.3, "inorder: sol, kök, sağ", ino(T), FILL[0], EDGE[0]),
        (3.1, "preorder: kök, sol, sağ", pre(T), FILL[1], EDGE[1]),
        (1.9, "postorder: sol, sağ, kök", post(T), FILL[2], EDGE[2]),
        (0.7, "level-order: seviye seviye", lvl(T), FILL[3], EDGE[3]),
    ]
    for yc, etiket, seq, dolgu, kenar in satirlar:
        ax.text(7.0, yc + 0.42, etiket, ha="left", va="bottom", fontsize=9,
                color=kenar, weight="bold")
        for j, v in enumerate(seq):
            _box(ax, 7.0 + j * 0.7, yc - 0.27, 0.6, 0.54, str(v), dolgu,
                 kenar, fs=9.4, bold=True)
    return _save(fig, path)


def bst_arama(path):
    """BST'de arama yolu (7 aranıyor) ve ekleme yolu (5)."""
    fig, ax = _tuval(13, 5.4)
    ax.text(6.5, 5.12, "BST'de arama: her düğümde tek karşılaştırma",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    stil = {"": (FILL[3], EDGE[3]), "L": (FILL[3], EDGE[3]),
            "LR": (FILL[3], EDGE[3]), "LRR": (FILL[1], EDGE[1])}
    kstil = {("", "L"): ACCENT, ("L", "LR"): ACCENT, ("LR", "LRR"): ACCENT}
    _agac_ciz(ax, T, 0.6, 6.6, 4.5, 1.05, stil=stil, kstil=kstil)
    satirlar = [
        (4.45, "ara(7) adımları:", True, INK),
        (3.9, "  8:  7 < 8  ->  sola git", False, INK),
        (3.45, "  3:  7 > 3  ->  sağa git", False, INK),
        (3.0, "  6:  7 > 6  ->  sağa git", False, INK),
        (2.55, "  7:  eşit   ->  BULUNDU", True, EDGE[1]),
        (1.7, "ekle(5) aynı yolu izler: 8'de sola,", False, MUTED),
        (1.25, "3'te sağa, 6'da sola; boş yere", False, MUTED),
        (0.8, "yaprak olarak yerleşir.", False, MUTED),
    ]
    for y, metin, kalin, renk in satirlar:
        ax.text(7.6, y, metin, ha="left", va="center", fontsize=9,
                color=renk, weight="bold" if kalin else "normal",
                **MONO)
    return _save(fig, path)


def bst_silme(path):
    """BST silmenin üç durumu: yaprak, tek çocuk, iki çocuk (inorder halef)."""
    fig, ax = _tuval(14, 9.6, olcek=0.72)
    ax.text(0.3, 9.3, "ÖNCE", ha="left", fontsize=9.4, color=MUTED,
            weight="bold")
    ax.text(0.3, 4.62, "SONRA", ha="left", fontsize=9.4, color=MUTED,
            weight="bold")
    ornekler = [
        ("(a) yaprak silme", 2.4,
         (8, (3, None, None), (10, None, None)),
         (8, None, (10, None, None)),
         {"L": (FILL[3], EDGE[3])}, {},
         "yaprak: sadece kes"),
        ("(b) tek çocuklu", 7.0,
         (8, (3, (1, None, None), None), (10, None, None)),
         (8, (1, None, None), (10, None, None)),
         {"L": (FILL[3], EDGE[3])}, {},
         "tek çocuk: çocuğu\nyukarı al"),
        ("(c) iki çocuklu", 11.6,
         (8, (3, (1, None, None), (6, (4, None, None), None)),
          (10, None, None)),
         (8, (4, (1, None, None), (6, None, None)), (10, None, None)),
         {"L": (FILL[3], EDGE[3]), "LRL": (FILL[2], EDGE[2])},
         {"L": (FILL[2], EDGE[2])},
         "iki çocuk: inorder halef\n(4) kopyalanır, halef silinir"),
    ]
    for baslik, cx, once, sonra, st1, st2, not_ in ornekler:
        ax.text(cx, 8.75, baslik, ha="center", fontsize=9.4, color=INK,
                weight="bold")
        hw = 1.7
        _agac_ciz(ax, once, cx - hw, cx + hw, 8.0, 1.0, stil=st1)
        _agac_ciz(ax, sonra, cx - hw, cx + hw, 3.9, 0.9, stil=st2)
        ax.text(cx, 1.45, not_, ha="center", va="top", fontsize=8.6,
                color=MUTED, style="italic")
    ax.plot([0.3, 13.7], [4.3, 4.3], color=RULE, lw=0.9)
    return _save(fig, path)


def dengesiz(path):
    """Sıralı eklemede BST bağlı listeye döner; dengeli ağaç kısadır."""
    fig, ax = _tuval(14, 5.8)
    zincir = (1, None, (2, None, (3, None, (4, None, (5, None, None)))))
    denge = (3, (2, (1, None, None), None), (4, None, (5, None, None)))
    _agac_ciz(ax, zincir, 0.6, 6.2, 4.6, 0.9,
              stil={}, kstil={("", "R"): ACCENT, ("R", "RR"): ACCENT,
                              ("RR", "RRR"): ACCENT,
                              ("RRR", "RRRR"): ACCENT})
    _agac_ciz(ax, denge, 8.2, 13.4, 4.6, 1.0,
              stil={"": (FILL[1], EDGE[1])},
              kstil={("", "L"): EDGE[1], ("", "R"): EDGE[1]})
    ax.text(3.4, 5.4, "1, 2, 3, 4, 5 sırayla eklendi", ha="center",
            fontsize=9.4, color=ACCENT, weight="bold")
    ax.text(10.8, 5.4, "3, 2, 4, 1, 5 sırayla eklendi", ha="center",
            fontsize=9.4, color=EDGE[1], weight="bold")
    ax.plot([7.1, 7.1], [0.4, 5.1], color=RULE, lw=0.9)
    ax.text(3.4, 0.5, "yükseklik 4 (= n-1)  ->  arama O(n)", ha="center",
            fontsize=9, color=ACCENT, weight="bold")
    ax.text(10.8, 0.5, "yükseklik 2  ->  arama O(log n)", ha="center",
            fontsize=9, color=EDGE[1], weight="bold")
    return _save(fig, path)


def avl_tek(path):
    """AVL tek rotasyonlar: LL (sağa döndür) ve RR (sola döndür)."""
    fig, ax = _tuval(14, 6.0)
    ax.text(7.0, 5.62, "Tek rotasyonlar: LL ve RR", ha="center",
            fontsize=10.4, color=INK, weight="bold")
    kok = {"": (FILL[3], EDGE[3])}
    tepe = {"": (FILL[1], EDGE[1])}
    panel = [
        (1.9, (30, (20, (10, None, None), None), None), kok,
         "LL: önce", "bf(30) = +2 (dengesiz)"),
        (5.4, (20, (10, None, None), (30, None, None)), tepe,
         "LL: sağa döndür", "20 kök oldu, yükseklik 2"),
        (8.9, (10, None, (20, None, (30, None, None))), kok,
         "RR: önce", "bf(10) = -2 (dengesiz)"),
        (12.4, (20, (10, None, None), (30, None, None)), tepe,
         "RR: sola döndür", "20 kök oldu, yükseklik 2"),
    ]
    for cx, agac, stil, baslik, alt in panel:
        ax.text(cx, 4.95, baslik, ha="center", fontsize=9.4, color=INK,
                weight="bold")
        _agac_ciz(ax, agac, cx - 1.2, cx + 1.2, 4.2, 1.0, stil=stil)
        ax.text(cx, 1.15, alt, ha="center", fontsize=8.8, color=MUTED,
                style="italic")
    ax.text(7.0, 0.25, "Rotasyon sırası korur: inorder çıktı (10 20 30) "
            "değişmez.", ha="center", fontsize=8.8, color=ACCENT,
            weight="bold")
    return _save(fig, path)


def avl_cift(path):
    """Çift rotasyonlar: LR ve RL, her biri iki adım."""
    fig, ax = _tuval(14, 6.0)
    ax.text(7.0, 5.62, "Çift rotasyonlar: LR ve RL (iki adım)",
            ha="center", fontsize=10.4, color=INK, weight="bold")
    kok = {"": (FILL[3], EDGE[3])}
    ara = {"": (FILL[3], EDGE[3]), "L": (FILL[2], EDGE[2])}
    son = {"": (FILL[1], EDGE[1])}
    paneller = [
        (1.2, (30, (10, None, (20, None, None)), None), kok,
         "(1) LR: önce", "10'un sağı ağır"),
        (3.5, (30, (20, (10, None, None), None), None), ara,
         "(2) 10'da sola döndür", "şimdi LL durumu"),
        (5.83, (20, (10, None, None), (30, None, None)), son,
         "(3) 30'da sağa döndür", "20 kök, denge tamam"),
        (8.17, (10, None, (30, (20, None, None), None)), kok,
         "(1) RL: önce", "30'un solu ağır"),
        (10.5, (10, None, (20, None, (30, None, None))), ara,
         "(2) 30'da sağa döndür", "şimdi RR durumu"),
        (12.8, (20, (10, None, None), (30, None, None)), son,
         "(3) 10'da sola döndür", "20 kök, denge tamam"),
    ]
    for cx, agac, stil, baslik, alt in paneller:
        ax.text(cx, 4.95, baslik, ha="center", fontsize=8.2, color=INK,
                weight="bold")
        _agac_ciz(ax, agac, cx - 0.7, cx + 0.7, 4.2, 1.0, stil=stil)
        ax.text(cx, 1.15, alt, ha="center", fontsize=8.2, color=MUTED,
                style="italic")
    ax.plot([6.9, 6.9], [0.5, 5.2], color=RULE, lw=0.9)
    return _save(fig, path)


def heap(path):
    """Min-heap: ağaç görünümü ve dizi gösterimi."""
    fig, ax = _tuval(14, 6.0)
    ax.text(7.0, 5.62, "Min-heap: ağaç ve dizi, aynı yapının iki yüzü",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    dizi = [2, 4, 3, 8, 6, 5, 9]
    stil = {0: (FILL[1], EDGE[1])}
    _yigin_ciz(ax, dizi, 0.4, 6.2, 4.7, 1.05, stil=stil)
    ax.text(7.1, 4.75, "dizi (indeks altta)", ha="left", fontsize=9,
            color=MUTED, weight="bold")
    for i, v in enumerate(dizi):
        x = 7.1 + i * 0.92
        _box(ax, x, 3.45, 0.82, 0.72, str(v),
             FILL[1] if i == 0 else FILL[0],
             EDGE[1] if i == 0 else EDGE[0], fs=10, bold=True)
        ax.text(x + 0.41, 3.1, str(i), ha="center", va="center",
                fontsize=8.6, color=MUTED, **MONO)
    for y, metin in [(2.25, "sol çocuk  : 2i + 1"),
                     (1.75, "sağ çocuk  : 2i + 2"),
                     (1.25, "ebeveyn    : (i - 1) // 2"),
                     (0.6, "her ebeveyn ≤ çocukları (min-heap)")]:
        ax.text(7.1, y, metin, ha="left", va="center", fontsize=9,
                color=INK, **MONO)
    return _save(fig, path)


def heap_sift(path):
    """Kökten çıkarmadan sonra sift-down: üç adım."""
    fig, ax = _tuval(14, 5.6)
    adimlar = [
        ([9, 4, 3, 8, 6, 5], "1) son eleman köke geldi",
         {0: (FILL[3], EDGE[3])}, {}),
        ([3, 4, 9, 8, 6, 5], "2) 9, küçük çocuk 3 ile takas",
         {0: (FILL[2], EDGE[2]), 2: (FILL[3], EDGE[3])},
         {(0, 2): ACCENT}),
        ([3, 4, 5, 8, 6, 9], "3) 9, 5 ile takas: yaprak, bitti",
         {2: (FILL[2], EDGE[2]), 5: (FILL[3], EDGE[3])},
         {(2, 5): ACCENT}),
    ]
    bolgeler = [(0.3, 4.5), (5.0, 9.2), (9.7, 13.7)]
    for (x0, x1), (dizi, baslik, stil, kstil) in zip(bolgeler, adimlar):
        ax.text((x0 + x1) / 2, 5.1, baslik, ha="center", fontsize=8.8,
                color=INK, weight="bold")
        _yigin_ciz(ax, dizi, x0, x1, 4.0, 0.95, stil=stil, kstil=kstil)
        ax.text((x0 + x1) / 2, 1.2, str(dizi), ha="center", fontsize=8.8,
                color=MUTED, **MONO)
    ax.text(7.0, 0.35, "Sift-down her adımda 9'u bir alt seviyeye indirir "
            "ve sonunda heap'i geri kurar.", ha="center", fontsize=8.6,
            color=ACCENT, weight="bold")
    return _save(fig, path)


def trie(path):
    """Kelimeler: el, ela, ev, eve, evde. Yeşil düğümler kelime sonudur."""
    fig, ax = _tuval(12, 5.6, olcek=0.75)
    ax.text(5.0, 5.25, "Trie: her kenar bir karakter", ha="center",
            fontsize=10.4, color=INK, weight="bold")
    P = {"kok": (4.2, 4.65), "e": (4.2, 3.6), "l": (2.2, 2.55),
         "v": (6.2, 2.55), "a": (2.2, 1.5), "e2": (5.0, 1.5),
         "d": (7.4, 1.5), "e3": (7.4, 0.5)}
    kenarlar = [("kok", "e"), ("e", "l"), ("e", "v"), ("l", "a"),
                ("v", "e2"), ("v", "d"), ("d", "e3")]
    for a, b in kenarlar:
        _kenar(ax, P[a], P[b])
    harf = {"kok": "kök", "e": "e", "l": "l", "v": "v", "a": "a",
            "e2": "e", "d": "d", "e3": "e"}
    son = {"l", "a", "v", "e2", "e3"}
    for k, p in P.items():
        if k == "kok":
            _dugum(ax, p, "kök", FILL[3], EDGE[3], fs=8.2)
        elif k in son:
            _dugum(ax, p, harf[k], FILL[1], EDGE[1])
        else:
            _dugum(ax, p, harf[k], FILL[0], EDGE[0])
    ax.add_patch(Circle((9.0, 3.25), 0.16, facecolor=FILL[1], edgecolor=EDGE[1],
                        lw=1.2))
    ax.text(9.35, 3.25, "kelime sonu", ha="left", va="center", fontsize=8.8,
            color=INK)
    ax.text(9.0, 2.45, "kelimeler:", ha="left", fontsize=8.8, color=INK,
            weight="bold")
    ax.text(9.0, 1.95, "el, ela, ev, eve, evde", ha="left", fontsize=8.6,
            color=INK, **MONO)
    ax.text(9.0, 1.2, "'ev' önekinde yalnız\nv dalı gezilir.",
            ha="left", va="center", fontsize=8.4, color=MUTED, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(terminoloji, "b10_terminoloji.png"),
                   (gezinme, "b10_gezinme.png"),
                   (bst_arama, "b10_bst_arama.png"),
                   (bst_silme, "b10_bst_silme.png"),
                   (dengesiz, "b10_dengesiz.png"),
                   (avl_tek, "b10_avl_tek.png"),
                   (avl_cift, "b10_avl_cift.png"),
                   (heap, "b10_heap.png"),
                   (heap_sift, "b10_heap_sift.png"),
                   (trie, "b10_trie.png")]:
        print(fn(os.path.join(out, ad)))
