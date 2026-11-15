# -*- coding: utf-8 -*-
"""Bölüm 11 — 'Graph' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import math
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

OLCEK = 0.72      # inç / birim: x ve y aynı ölçekte -> daireler bozulmaz
R = 0.28          # düğüm yarıçapı (birim)

# Ortak örnek graf G1 (yönsüz): 0-1, 0-2, 1-3, 2-3, 3-4, 5-6
G1_KENAR = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (5, 6)]
POS5 = {0: (2.0, 3.9), 1: (1.0, 2.5), 2: (3.0, 2.5), 3: (2.0, 1.2),
        4: (3.6, 1.2)}


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


def _yon(ax, a, b, col=MUTED, lw=1.4, etiket=None, dx=0.0, dy=0.0):
    """Yönlü kenar: ok, daire kenarında biter; etiket orta noktaya."""
    (x1, y1), (x2, y2) = a, b
    d = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    _arrow(ax, x1 + ux * R, y1 + uy * R, x2 - ux * R, y2 - uy * R,
           col=col, lw=lw)
    if etiket:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, etiket, ha="center",
                va="center", fontsize=8.8, color=INK, weight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


def _etiket(ax, a, b, metin, dx=0.0, dy=0.0, renk=INK):
    ax.text((a[0] + b[0]) / 2 + dx, (a[1] + b[1]) / 2 + dy, metin,
            ha="center", va="center", fontsize=8.8, color=renk, weight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


def _dugum(ax, p, metin, dolgu=FILL[0], kenar=EDGE[0], fs=9.6, tcol=INK):
    ax.add_patch(Circle(p, R, facecolor=dolgu, edgecolor=kenar, lw=1.3,
                        zorder=3))
    ax.text(p[0], p[1], metin, ha="center", va="center", fontsize=fs,
            color=tcol, weight="bold", zorder=4)


def _shift(pos, ox):
    return {k: (x + ox, y) for k, (x, y) in pos.items()}


# --------------------------------------------------------------------------- #
def terminoloji(path):
    """G1'in 0-4 parçası: düğüm, kenar, derece, yol, döngü."""
    fig, ax = _tuval(12.0, 5.4)
    cevrim = {(0, 1), (1, 3), (2, 3), (0, 2)}
    for a, b in [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]:
        renk = ACCENT if (a, b) in cevrim else MUTED
        _kenar(ax, POS5[a], POS5[b], col=renk, lw=2.4 if renk == ACCENT else 1.3)
    for k, p in POS5.items():
        dolgu, kenar = (FILL[0], EDGE[0])
        if k == 4:
            dolgu, kenar = (FILL[1], EDGE[1])
        _dugum(ax, p, str(k), dolgu, kenar)
    satirlar = [
        (4.7, "Düğüm (node): 0, 1, 2, 3, 4", True, INK),
        (4.1, "Kenar (edge): 0-1, 0-2, 1-3, 2-3, 3-4", False, INK),
        (3.5, "Derece: derece(3) = 3  (komşuları 1, 2, 4)", False, INK),
        (2.9, "Yol: 4 - 3 - 1 - 0   (3 kenar)", False, INK),
        (2.3, "Döngü (kırmızı): 0 - 1 - 3 - 2 - 0", True, ACCENT),
        (1.7, "Bağlantılı: evet, tek bileşen", False, INK),
        (1.1, "Döngü içerdiği için ağaç değildir.", False, MUTED),
    ]
    for y, metin, kalin, renk in satirlar:
        ax.text(5.2, y, metin, ha="left", va="center", fontsize=9.2,
                color=renk, weight="bold" if kalin else "normal")
    return _save(fig, path)


def yonlu_agirlikli(path):
    """Sol: yönlü, ağırlıklı (tek yön). Sağ: aynı düğümler, yönsüz."""
    fig, ax = _tuval(13.4, 5.2)
    sol = {"A": (0.9, 2.6), "B": (3.6, 4.1), "C": (3.6, 1.1), "D": (6.3, 2.6)}
    sag = _shift(sol, 6.6)
    ax.text(3.2, 4.9, "Yönlü ve ağırlıklı (tek yön)", ha="center",
            fontsize=9.6, color=INK, weight="bold")
    ax.text(9.8, 4.9, "Yönsüz (iki yön de geçerli)", ha="center",
            fontsize=9.6, color=INK, weight="bold")
    ayrit = [("A", "B", "4", 0.0, 0.3), ("A", "C", "2", 0.0, -0.3),
             ("C", "B", "1", -0.45, 0.0), ("B", "D", "5", 0.45, 0.0),
             ("C", "D", "8", 0.0, -0.3)]
    for a, b, w, dx, dy in ayrit:
        _yon(ax, sol[a], sol[b], col=ACCENT if (a, b) == ("A", "C") else MUTED,
             lw=1.6, etiket=w, dx=dx, dy=dy)
        _kenar(ax, sag[a], sag[b], col=MUTED, lw=1.4)
        _etiket(ax, sag[a], sag[b], w, dx, dy)
    for k, p in sol.items():
        _dugum(ax, p, k)
    for k, p in sag.items():
        _dugum(ax, p, k)
    return _save(fig, path)


def matris(path):
    """Sol: 7x7 komşuluk matrisi. Sağ: aynı G1 grafı."""
    fig, ax = _tuval(13.4, 6.1)
    x0, top, h = 0.9, 5.0, 0.48
    ax.text(2.5, 5.75, "Komşuluk matrisi", ha="center", fontsize=9.6,
            color=INK, weight="bold")
    m = [[0] * 7 for _ in range(7)]
    for a, b in G1_KENAR:
        m[a][b] = m[b][a] = 1
    for c in range(7):
        ax.text(x0 + (c + 0.5) * h, top + 0.22, str(c), ha="center",
                va="center", fontsize=8.6, color=MUTED)
    for r in range(7):
        ax.text(x0 - 0.25, top - (r + 0.5) * h, str(r), ha="center",
                va="center", fontsize=8.6, color=MUTED)
        for c in range(7):
            v = m[r][c]
            _box(ax, x0 + c * h + 0.03, top - (r + 1) * h + 0.03, h - 0.06,
                 h - 0.06, str(v), FILL[1] if v else "#FFFFFF",
                 EDGE[1] if v else RULE, fs=8.8, bold=bool(v))
    pos7 = {0: (8.3, 4.2), 1: (7.3, 2.8), 2: (9.3, 2.8), 3: (8.3, 1.5),
            4: (9.9, 1.5), 5: (11.0, 4.2), 6: (12.5, 4.2)}
    ax.text(10.4, 5.75, "Aynı graf G1", ha="center", fontsize=9.6,
            color=INK, weight="bold")
    for a, b in G1_KENAR:
        _kenar(ax, pos7[a], pos7[b])
    for k, p in pos7.items():
        _dugum(ax, p, str(k))
    return _save(fig, path)


def liste(path):
    """Komşuluk listesi: her düğümün bağlı listesi (başa ekleme sırası)."""
    fig, ax = _tuval(11.2, 6.2)
    ax.text(5.6, 6.0, "Komşuluk listesi (başa ekleme sırası)", ha="center",
            fontsize=9.6, color=INK, weight="bold")
    komsu = {0: [2, 1], 1: [3, 0], 2: [3, 0], 3: [4, 2, 1], 4: [3],
             5: [6], 6: [5]}
    for u in range(7):
        y = 5.2 - u * 0.72
        _box(ax, 0.4, y - 0.25, 0.8, 0.5, str(u), FILL[3], EDGE[3],
             fs=9.4, bold=True)
        x = 1.7
        prev = (1.2, y)
        for v in komsu[u]:
            _arrow(ax, prev[0], y, x, y, col=EDGE[0], lw=1.3)
            _box(ax, x, y - 0.25, 0.7, 0.5, str(v), FILL[0], EDGE[0],
                 fs=9.4, bold=True)
            prev = (x + 0.7, y)
            x += 1.1
        _arrow(ax, prev[0], y, x, y, col=MUTED, lw=1.2)
        ax.text(x + 0.55, y, "NULL", ha="center", va="center", fontsize=8.4,
                color=MUTED)
    return _save(fig, path)


def gezinme(path):
    """G1 üzerinde DFS (sol) ve BFS (sağ) ağaçları; sıra numaraları."""
    fig, ax = _tuval(13.4, 5.8)
    dfs_agac = {(0, 2), (2, 3), (3, 4), (1, 3)}
    bfs_agac = {(0, 2), (0, 1), (2, 3), (3, 4)}
    paneller = [
        (0.0, "DFS: 0 2 3 4 1", dfs_agac, {0: 1, 2: 2, 3: 3, 4: 4, 1: 5}),
        (6.7, "BFS: 0 2 1 3 4", bfs_agac, {0: 1, 2: 2, 1: 3, 3: 4, 4: 5}),
    ]
    for ox, baslik, agac, sira in paneller:
        pos = _shift(POS5, ox)
        ax.text(ox + 3.0, 5.3, baslik, ha="center", fontsize=10,
                color=INK, weight="bold")
        for a, b in [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]:
            if (a, b) in agac or (b, a) in agac:
                _kenar(ax, pos[a], pos[b], col=ACCENT, lw=2.4)
            else:
                _kenar(ax, pos[a], pos[b], col=RULE, lw=1.4)
        for k, p in pos.items():
            _dugum(ax, p, str(k), FILL[0], EDGE[0])
            ax.text(p[0] + 0.42, p[1] + 0.36, "#%d" % sira[k], ha="left",
                    va="bottom", fontsize=8.6, color=ACCENT, weight="bold")
    ax.text(6.7, 0.15, "Kırmızı kenarlar gezinmenin ağacını (tree edge) gösterir.",
            ha="center", fontsize=8.8, color=MUTED, style="italic")
    return _save(fig, path)


def bilesen(path):
    """G1 iki bileşene ayrılır: {0,1,2,3,4} ve {5,6}."""
    fig, ax = _tuval(10.0, 5.4)
    pos = dict(POS5)
    pos[5] = (6.0, 3.9)
    pos[6] = (7.6, 3.9)
    for a, b in G1_KENAR:
        _kenar(ax, pos[a], pos[b], col=MUTED, lw=1.3)
    for k, p in pos.items():
        if k <= 4:
            _dugum(ax, p, str(k), FILL[0], EDGE[0])
        else:
            _dugum(ax, p, str(k), FILL[1], EDGE[1])
    ax.text(2.3, 0.35, "bileşen 1: {0, 1, 2, 3, 4}", ha="center", fontsize=9.2,
            color=EDGE[0], weight="bold")
    ax.text(6.8, 2.6, "bileşen 2:\n{5, 6}", ha="center", va="center",
            fontsize=9.2, color=EDGE[1], weight="bold")
    return _save(fig, path)


def modelleme(path):
    """Üç bakış: bağımlılık (DAG), durum uzayı, sensör ağı arızası."""
    fig, ax = _tuval(14.0, 5.8)
    # (a) derleme bağımlılığı: hedef -> bağımlılık
    ox = 0.0
    ax.text(ox + 2.3, 5.45, "a) Derleme bağımlılığı", ha="center",
            fontsize=9.4, color=INK, weight="bold")
    kutu = {"app": (2.3, 4.5), "main.o": (1.0, 3.0), "util.o": (3.6, 3.0),
            "main.c": (0.7, 1.5), "util.h": (2.3, 1.5), "util.c": (3.9, 1.5)}
    kenar = [("app", "main.o"), ("app", "util.o"), ("main.o", "main.c"),
             ("main.o", "util.h"), ("util.o", "util.h"), ("util.o", "util.c")]
    for a, b in kenar:
        (x1, y1), (x2, y2) = kutu[a], kutu[b]
        _arrow(ax, x1, y1 - 0.27, x2, y2 + 0.27, col=MUTED, lw=1.2)
    for k, (x, y) in kutu.items():
        _box(ax, x - 0.62, y - 0.25, 1.24, 0.5, k, FILL[0], EDGE[0],
             fs=8.8, bold=True)
    # (b) durum uzayı
    ox = 4.8
    ax.text(ox + 2.3, 5.45, "b) Durum uzayı", ha="center", fontsize=9.4,
            color=INK, weight="bold")
    durum = {"S0": (ox + 2.3, 4.2), "S1": (ox + 2.3, 2.7), "S2": (ox + 2.3, 1.2)}
    etiket = {"S0": "S0: kapalı, anahtar yok", "S1": "S1: kapalı, anahtar var",
              "S2": "S2: açık, anahtar var"}
    for k, (x, y) in durum.items():
        _box(ax, x - 1.15, y - 0.27, 2.3, 0.54, etiket[k], FILL[2], EDGE[2],
             fs=8.2, bold=True)
    _arrow(ax, ox + 2.3, 4.2 - 0.27, ox + 2.3, 2.7 + 0.27, col=EDGE[2], lw=1.3)
    ax.text(ox + 3.5, 3.45, "anahtarı al", ha="left", va="center",
            fontsize=8.4, color=INK)
    _arrow(ax, ox + 1.6, 2.7 + 0.27, ox + 1.6, 4.2 - 0.27, col=MUTED, lw=1.1)
    ax.text(ox + 0.9, 3.45, "bırak", ha="right", va="center", fontsize=8.4,
            color=MUTED)
    _arrow(ax, ox + 2.3, 2.7 - 0.27, ox + 2.3, 1.2 + 0.27, col=EDGE[2], lw=1.3)
    ax.text(ox + 3.5, 1.95, "kapıyı aç", ha="left", va="center",
            fontsize=8.4, color=INK)
    # (c) sensör ağı: gateway arızası
    ox = 9.6
    ax.text(ox + 2.2, 5.45, "c) Gateway arızası", ha="center", fontsize=9.4,
            color=INK, weight="bold")
    s = {"G": (ox + 2.2, 3.0), "s1": (ox + 0.5, 4.5), "s2": (ox + 2.2, 4.6),
         "s3": (ox + 3.9, 3.0), "s4": (ox + 3.9, 1.3), "s5": (ox + 2.2, 1.0)}
    for a, b in [("G", "s1"), ("G", "s2"), ("G", "s3"), ("s3", "s4"),
                 ("s4", "s5")]:
        _kenar(ax, s[a], s[b], col=MUTED, lw=1.3)
    for k, p in s.items():
        if k == "G":
            _dugum(ax, p, "G", FILL[3], EDGE[3], fs=9.0)
        else:
            _dugum(ax, p, k, FILL[0], EDGE[0], fs=8.6)
    ax.text(ox + 2.2, 0.25, "G silinirse: {s1}, {s2}, {s3,s4,s5}",
            ha="center", fontsize=8.4, color=ACCENT, weight="bold")
    return _save(fig, path)


def git_dag(path):
    """Commit DAG'ı: her commit ebeveynine (parent) ok çizer."""
    fig, ax = _tuval(10.2, 4.8)
    pos = {"A": (1.4, 2.6), "B": (3.4, 2.6), "C": (5.4, 3.6),
           "M": (7.6, 3.6), "D": (5.4, 1.4)}
    kenar = [("B", "A"), ("C", "B"), ("M", "C"), ("M", "D"), ("D", "B")]
    for a, b in kenar:
        _yon(ax, pos[a], pos[b], col=MUTED, lw=1.4)
    for k, p in pos.items():
        dolgu, kn = (FILL[3], EDGE[3]) if k == "M" else (FILL[0], EDGE[0])
        _dugum(ax, p, k, dolgu, kn)
    ax.text(7.6, 4.45, "main", ha="center", fontsize=9, color=ACCENT,
            weight="bold")
    ax.text(5.4, 0.55, "feature", ha="center", fontsize=9, color=ACCENT,
            weight="bold")
    ax.text(9.0, 2.6, "Oklar çocuktan\nebeveyne gösterir.\nM iki ebeveynli:\nbirleştirme.",
            ha="left", va="center", fontsize=8.6, color=INK)
    return _save(fig, path)


def kelime(path):
    """Kelime merdiveni: kelimeler düğüm, tek harf farkı kenar; yol vurgulu."""
    fig, ax = _tuval(12.0, 6.0)
    kume = ["kar", "bar", "bas", "tas", "kas", "kat", "tat", "mat"]
    pos = {"kar": (1.2, 2.6), "bar": (1.2, 5.0), "kas": (3.8, 3.8),
           "kat": (3.8, 1.4), "bas": (6.4, 5.0), "tas": (6.4, 3.8),
           "tat": (6.4, 1.4), "mat": (5.1, 0.3)}
    kenar = []
    for i in range(len(kume)):
        for j in range(i + 1, len(kume)):
            a, b = kume[i], kume[j]
            if sum(x != y for x, y in zip(a, b)) == 1:
                kenar.append((a, b))
    yol = {("kar", "kas"), ("kas", "tas")}
    for a, b in kenar:
        if (a, b) in yol or (b, a) in yol:
            _kenar(ax, pos[a], pos[b], col=ACCENT, lw=2.6)
        else:
            _kenar(ax, pos[a], pos[b], col=MUTED, lw=1.3)
    ETIKET = {"bas": "baş", "tas": "taş", "kas": "kaş"}
    for k, p in pos.items():
        if k in ("kar", "kas", "tas"):
            _dugum(ax, p, ETIKET.get(k, k), FILL[3], EDGE[3], fs=8.8)
        else:
            _dugum(ax, p, ETIKET.get(k, k), FILL[0], EDGE[0], fs=8.8)
    ax.text(9.6, 4.6, "Yol: kar - kaş - taş", ha="left", fontsize=9.4,
            color=ACCENT, weight="bold")
    ax.text(9.6, 3.9, "2 adım (BFS en kısa)", ha="left", fontsize=9.0,
            color=INK)
    ax.text(9.6, 2.9, "Kenar: tek harf farkı", ha="left", fontsize=9.0,
            color=INK)
    ax.text(9.6, 2.3, "%d kenar, %d düğüm" % (len(kenar), len(kume)),
            ha="left", fontsize=9.0, color=INK)
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    for fn, ad in [(terminoloji, "b11_terminoloji.png"),
                   (yonlu_agirlikli, "b11_yonlu_agirlikli.png"),
                   (matris, "b11_matris.png"),
                   (liste, "b11_liste.png"),
                   (gezinme, "b11_gezinme.png"),
                   (bilesen, "b11_bilesen.png"),
                   (modelleme, "b11_modelleme.png"),
                   (git_dag, "b11_git_dag.png"),
                   (kelime, "b11_kelime.png")]:
        print(fn(os.path.join(out, ad)))
