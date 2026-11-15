# -*- coding: utf-8 -*-
"""Bolum 17 - 'Graph Algoritmalari' diyagramlari.

Sayilar ve izler, bolumdeki programlarla ayni algoritmalardan uretilir:
DFS zaman damgalari (dfs.c), topolojik sıra (topo.py), iki renk
(bipartite.py), SCC ve köprü/eklem (tarjan.py), Dijkstra adimlari ve
negatif kenar (dijkstra.py, bellman.py), Bellman-Ford turlari, Floyd
matrisleri (floyd.py), Union-Find ağaçlari (mst.py), MST (mst.py) ve
A* ile Dijkstra genisletmeleri (astar.py).
"""
import heapq
import math
import os
import random
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import ACCENT, ACCENT_L, INK, MUTED, RULE, FILL, EDGE, _save

INF = float("inf")
GRI_KOYU = "#9A958B"


# ----- yardimcilar ----------------------------------------------------------
def _tuval(w, h, xl, yl):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _dugum(ax, p, etiket, fill=FILL[0], edge=EDGE[0], r=0.36, fs=10.5,
           alt=None, alt_fs=7.6, alt_konum="alt"):
    x, y = p
    ax.add_patch(Circle((x, y), r, facecolor=fill, edgecolor=edge,
                        lw=1.4, zorder=3))
    ax.text(x, y, etiket, ha="center", va="center", fontsize=fs,
            color=INK, weight="bold", zorder=4)
    if alt:
        if alt_konum == "ust":
            ax.text(x, y + r + 0.12, alt, ha="center", va="bottom",
                    fontsize=alt_fs, color=MUTED, zorder=4)
        elif alt_konum == "sol":
            ax.text(x - r - 0.12, y, alt, ha="right", va="center",
                    fontsize=alt_fs, color=MUTED, zorder=4)
        else:
            ax.text(x, y - r - 0.14, alt, ha="center", va="top",
                    fontsize=alt_fs, color=MUTED, zorder=4)


def _kenar(ax, p, q, col=EDGE[0], rad=0.0, lw=1.6, ls="-", etiket=None,
           etiket_t=0.5, r=0.36, etiket_dy=0.0):
    a = FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13,
                        linewidth=lw, color=col, linestyle=ls,
                        shrinkA=20, shrinkB=20,
                        connectionstyle="arc3,rad=%s" % rad, zorder=2)
    ax.add_patch(a)
    if etiket is not None:
        mx = p[0] + (q[0] - p[0]) * etiket_t
        my = p[1] + (q[1] - p[1]) * etiket_t + etiket_dy
        ax.text(mx, my, str(etiket), ha="center", va="center", fontsize=9,
                color=col, zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", fc="white",
                          ec="none"))


def _cizgi(ax, p, q, col=EDGE[0], lw=1.6, ls="-", etiket=None, dy=0.0):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=col, lw=lw, ls=ls, zorder=2)
    if etiket is not None:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dy, str(etiket),
                ha="center", va="center", fontsize=9, color=col, zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))


def _baslik(ax, metin, y=None):
    ax.text(0.02, 0.98 if y is None else y, metin, transform=ax.transAxes,
            ha="left", va="top", fontsize=10.5, color=INK, weight="bold")


# ----- 1. DFS zaman damgalari ve kenar turleri -----------------------------
def dfs_zaman(path):
    fig, ax = _tuval(9.6, 5.6, (0, 11), (0, 7.4))
    P = {0: (1.6, 4.8), 1: (4.4, 6.3), 2: (7.2, 4.8), 3: (4.4, 3.0),
         4: (6.8, 1.3), 5: (9.6, 1.3)}
    zd = {0: "1/8", 1: "2/5", 2: "3/4", 3: "6/7", 4: "9/12", 5: "10/11"}
    _kenar(ax, P[0], P[1], EDGE[0], etiket="ağaç")
    _kenar(ax, P[1], P[2], EDGE[0], etiket="ağaç")
    _kenar(ax, P[2], P[0], ACCENT, rad=0.30, lw=1.9, etiket="geri",
           etiket_dy=0.35)
    _kenar(ax, P[0], P[3], EDGE[0], etiket="ağaç", etiket_t=0.45)
    _kenar(ax, P[3], P[2], EDGE[2], lw=1.9, etiket="çapraz", etiket_t=0.5)
    _kenar(ax, P[0], P[2], EDGE[1], rad=-0.22, lw=1.9, etiket="ileri",
           etiket_dy=-0.6)
    _kenar(ax, P[4], P[5], EDGE[0], etiket="ağaç")
    for u in P:
        _dugum(ax, P[u], str(u), alt="d/f=" + zd[u], alt_fs=8.2)
    # lejant
    lej = [("ağaç", EDGE[0]), ("geri (döngü)", ACCENT),
           ("ileri", EDGE[1]), ("çapraz", EDGE[2])]
    for i, (ad, c) in enumerate(lej):
        x = 0.6 + i * 2.5
        ax.plot([x, x + 0.7], [0.45, 0.45], color=c, lw=2.2)
        ax.text(x + 0.85, 0.45, ad, va="center", fontsize=9.2, color=INK)
    _baslik(ax, "DFS zaman damgalari ve kenar turleri")
    fig.tight_layout()
    return _save(fig, path)


# ----- 2. Topolojik sira -----------------------------------------------------
def topo_sira(path):
    fig, ax = _tuval(10.2, 5.4, (0, 12), (0, 8.2))
    ad = ["Programlama", "Matematik", "Veri Yap.", "Algoritmalar",
          "İşletim", "Ag", "Derleyiçi", "Bitirme"]
    kenar = [(0, 2), (0, 4), (2, 3), (1, 3), (4, 5), (2, 6), (3, 6),
             (3, 7), (5, 7), (6, 7)]
    sira = [0, 1, 2, 4, 3, 5, 6, 7]          # Kahn ciktisi (topo.py)
    konum = {0: (1.2, 5.6), 1: (1.2, 1.9), 2: (3.7, 6.9), 4: (3.7, 4.2),
             3: (6.2, 3.4), 5: (6.4, 5.8), 6: (8.6, 5.0), 7: (10.7, 3.4)}
    for u, v in kenar:
        _kenar(ax, konum[u], konum[v], EDGE[0], rad=0.0, lw=1.4)
    for u in konum:
        k = sira.index(u) + 1
        _dugum(ax, konum[u], str(k), fill=FILL[1], edge=EDGE[1], r=0.34)
        ax.text(konum[u][0], konum[u][1] - 0.62, ad[u], ha="center",
                va="top", fontsize=8.6, color=INK)
    _baslik(ax, "Kahn ile sıralama: daire içi sayı, işlenme sırası")
    fig.tight_layout()
    return _save(fig, path)


# ----- 3. Iki renk ------------------------------------------------------------
def iki_renk(path):
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for ax in axs:
        ax.set_xlim(-1.9, 1.9)
        ax.set_ylim(-1.9, 1.9)
        ax.set_aspect("equal")
        ax.axis("off")
    # C4: 4 dugum kare; renkler kosegen olarak
    p4 = [(-0.9, 0.9), (0.9, 0.9), (0.9, -0.9), (-0.9, -0.9)]
    renk4 = [0, 1, 0, 1]
    ax = axs[0]
    for u, v in [(0, 1), (1, 2), (2, 3), (3, 0)]:
        _cizgi(ax, p4[u], p4[v], EDGE[0])
    for i, p in enumerate(p4):
        c = FILL[2] if renk4[i] == 0 else FILL[4]
        _dugum(ax, p, str(i), fill=c, edge=EDGE[2] if renk4[i] == 0 else EDGE[4])
    _baslik(ax, "C4: 2-renklenebilir")
    # C5: 5 dugum; BFS ile renklendirilirken (2,3) kenari cakisir
    p5 = [(0, 1.45), (1.38, 0.45), (0.85, -1.15), (-0.85, -1.15), (-1.38, 0.45)]
    renk5 = [0, 1, 0, 1, 1]
    ax = axs[1]
    kenarlar5 = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
    for u, v in kenarlar5:
        if {u, v} == {2, 3}:
            _cizgi(ax, p5[u], p5[v], ACCENT, lw=2.2, ls="--")
        else:
            _cizgi(ax, p5[u], p5[v], EDGE[0])
    for i, p in enumerate(p5):
        c = FILL[2] if renk5[i] == 0 else FILL[4]
        _dugum(ax, p, str(i), fill=c, edge=EDGE[2] if renk5[i] == 0 else EDGE[4])
    ax.text(0.2, -0.45, "çakışma\n(2,3)", color=ACCENT, fontsize=9,
            ha="left", va="center")
    _baslik(ax, "C5: tek sayıda kenarlı döngü")
    fig.tight_layout()
    return _save(fig, path)


# ----- 4. SCC ve kopru/eklem --------------------------------------------------
def scc_kopru(path):
    fig, axs = plt.subplots(1, 2, figsize=(10.2, 4.6))
    for ax in axs:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.04,
                        wspace=0.05)
    ax = axs[0]
    P = {0: (1.2, 5.6), 1: (2.6, 6.6), 2: (2.6, 4.6),
         3: (5.0, 5.6), 4: (6.3, 6.6), 5: (6.3, 4.6),
         6: (8.6, 5.6), 7: (9.2, 3.6)}
    grp = {0: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2}
    ken = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3),
           (5, 6), (6, 7), (7, 6)]
    for u, v in ken:
        if grp[u] == grp[v]:
            _kenar(ax, P[u], P[v], EDGE[0], rad=0.18, lw=1.4, r=0.3)
        else:
            _kenar(ax, P[u], P[v], MUTED, lw=1.4, r=0.3)
    for u in P:
        _dugum(ax, P[u], str(u), fill=FILL[grp[u]], edge=EDGE[grp[u]],
               r=0.3, fs=10)
    _baslik(ax, "(a) Güçlü bağlı bileşenler (Tarjan)")
    ax = axs[1]
    Q = {0: (5.0, 6.2), 1: (2.2, 6.6), 2: (2.2, 4.4), 3: (6.6, 4.2),
         4: (8.6, 2.6), 5: (6.2, 2.2)}
    bag = [(0, 1), (0, 2), (0, 3)]
    tum = [(0, 1), (0, 2), (0, 3), (3, 4), (4, 5), (5, 3)]
    for u, v in tum:
        if (u, v) in bag:
            _cizgi(ax, Q[u], Q[v], ACCENT, lw=3.0)
        else:
            _cizgi(ax, Q[u], Q[v], EDGE[0], lw=1.5)
    for u in Q:
        fill = FILL[2] if u in (0, 3) else FILL[0]
        _dugum(ax, Q[u], str(u), fill=fill,
               edge=ACCENT if u in (0, 3) else EDGE[0], r=0.3, fs=10)
    ax.add_patch(Circle(Q[0], 0.44, fill=False, ec=ACCENT, lw=1.2, ls="--"))
    ax.add_patch(Circle(Q[3], 0.44, fill=False, ec=ACCENT, lw=1.2, ls="--"))
    ax.text(3.6, 7.2, "kalın: köprü (bağ.)", color=ACCENT, fontsize=9)
    ax.text(0.2, 0.9, "eklem: 0 ve 3 (kesikli halka)", color=INK,
            fontsize=9, ha="left")
    _baslik(ax, "(b) Köprü ve eklem noktaları")
    return _save(fig, path)


# ----- 5. Dijkstra adimlari ---------------------------------------------------
DJ_P = {0: (1.0, 3.0), 1: (4.0, 5.2), 2: (3.4, 3.0), 3: (7.0, 4.6),
        4: (9.0, 2.4), 5: (6.0, 0.8)}
DJ_K = [(0, 1, 7), (0, 2, 9), (0, 5, 14), (1, 2, 10), (1, 3, 15),
        (2, 3, 11), (2, 5, 2), (3, 4, 6), (5, 4, 9)]


def dijkstra_adim(path):
    adj = {u: [] for u in range(6)}
    for u, v, w in DJ_K:
        adj[u].append((v, w))
    fig, axs = plt.subplots(2, 2, figsize=(10.0, 7.4))
    kesin_adim = [1, 3, 4, 6]             # kac dugum islendikten sonra
    for ax, adet in zip(axs.flat, kesin_adim):
        dist = [INF] * 6
        dist[0] = 0
        bitti = [False] * 6
        yig = [(0, 0)]
        islenen = []
        while yig and len(islenen) < adet:
            d, u = heapq.heappop(yig)
            if bitti[u]:
                continue
            bitti[u] = True
            islenen.append(u)
            for v, w in adj[u]:
                if d + w < dist[v]:
                    dist[v] = d + w
                    heapq.heappush(yig, (dist[v], v))
        ax.set_xlim(-0.2, 10.2)
        ax.set_ylim(-0.4, 6.4)
        ax.set_aspect("equal")
        ax.axis("off")
        for u, v, w in DJ_K:
            kesin = bitti[u] and bitti[v]
            _kenar(ax, DJ_P[u], DJ_P[v], EDGE[1] if kesin else MUTED,
                   lw=1.5, etiket=w, r=0.34,
                   etiket_t={(0, 5): 0.62}.get((u, v), 0.5))
        for u in range(6):
            if bitti[u]:
                fill, edge = FILL[1], EDGE[1]
            elif dist[u] < INF:
                fill, edge = FILL[2], EDGE[2]
            else:
                fill, edge = "white", RULE
            etiket = str(u)
            alt = "d=%s" % (dist[u] if dist[u] < INF else "inf")
            _dugum(ax, DJ_P[u], etiket, fill=fill, edge=edge, r=0.34,
                   alt=alt, alt_fs=8.4,
                   alt_konum={1: "ust", 3: "ust"}.get(u, "alt"))
        _baslik(ax, ("Son durum: tüm düğümler kesin" if adet == 6 else
                     "%d düğüm işlendi: %s" % (
                         len(islenen), ", ".join(str(x) for x in islenen))))
    fig.text(0.5, 0.01, "Yeşil: işlendi (kesin); sarı: tahmin; "
             "gri: henüz yok", ha="center", fontsize=9.2, color=MUTED)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05,
                        wspace=0.06, hspace=0.12)
    return _save(fig, path)


# ----- 6. Negatif kenar: Dijkstra yanlis, Bellman-Ford dogru -----------------
def negatif_kenar(path):
    fig, axs = plt.subplots(1, 2, figsize=(10.0, 4.2))
    P = {0: (1.0, 2.6), 1: (4.0, 4.1), 2: (4.0, 1.1), 3: (7.2, 2.6)}
    kenar = [(0, 1, 1), (0, 2, 5), (2, 1, -10), (1, 3, 1)]
    for ax in axs:
        ax.set_xlim(0, 8.6)
        ax.set_ylim(0, 5.6)
        ax.set_aspect("equal")
        ax.axis("off")
    sol = {"sol": ({0: "0", 1: "-5", 2: "5", 3: "2"},
                   "Dijkstra: D=2 (yanlış)", ACCENT),
           "sag": ({0: "0", 1: "-5", 2: "5", 3: "-4"},
                   "Bellman-Ford: D=-4 (doğru)", EDGE[1])}
    for ax, anahtar in zip(axs, ["sol", "sag"]):
        vals, baslik, renk = sol[anahtar]
        for u, v, w in kenar:
            _kenar(ax, P[u], P[v], EDGE[0], lw=1.5, etiket=w, r=0.36)
        for u in P:
            _dugum(ax, P[u], "ABCD"[u] + "\n" + vals[u], fill=FILL[0],
                   edge=renk if u == 3 else EDGE[0], r=0.4, fs=9.4)
        _baslik(ax, baslik)
    axs[0].text(0.2, 0.25, "B, 1. adımda işlendi;\nC->B ile -5 yazıldı ama\n"
                "B'den D'ye yeniden gevşetilmedi.", fontsize=8.6,
                color=INK, ha="left", va="bottom")
    fig.tight_layout()
    return _save(fig, path)


# ----- 7. Bellman-Ford turlari --------------------------------------------------
def bellman_tur(path):
    kenar = [(1, 3, 1), (0, 1, 1), (0, 2, 5), (2, 1, -10)]
    n = 4
    dist = [INF] * n
    dist[0] = 0
    satirlar = [("başlangıç", list(dist), [])]
    for t in (1, 2):
        degisen = []
        for u, v, w in kenar:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                degisen.append(v)
        satirlar.append(("tur %d" % t, list(dist), degisen))
    fig, ax = plt.subplots(figsize=(7.4, 2.8))
    ax.axis("off")
    hucre = []
    for ad, deg, degisen in satirlar:
        hucre.append([ad] + ["inf" if x == INF else str(x) for x in deg])
    tablo = ax.table(cellText=hucre,
                     colLabels=["tur", "A", "B", "C", "D"],
                     loc="center", cellLoc="center")
    tablo.auto_set_font_size(False)
    tablo.set_fontsize(10.5)
    tablo.scale(1.0, 1.9)
    for (satir, sutun), c in tablo.get_celld().items():
        c.set_edgecolor(RULE)
        if satir == 0:
            c.set_facecolor(FILL[0])
            c.set_text_props(weight="bold", color=INK)
        elif sutun >= 1 and satir >= 1:
            _, deg, degisen = satirlar[satir - 1]
            if (sutun - 1) in degisen:
                c.set_facecolor(FILL[2])
                c.set_text_props(weight="bold", color=ACCENT)
            else:
                c.set_facecolor("white")
        else:
            c.set_facecolor("white")
    ax.set_title("Bellman-Ford: kenar sırası (1,3), (0,1), (0,2), (2,1)",
                 fontsize=10.5, color=INK, pad=6)
    fig.tight_layout()
    return _save(fig, path)


# ----- 8. Floyd-Warshall matrisleri -----------------------------------------------
def floyd_matris(path):
    n = 4
    kenar = [(0, 1, 1), (1, 3, 1), (3, 2, 1)]
    w = [[INF] * n for _ in range(n)]
    for i in range(n):
        w[i][i] = 0
    for u, v, c in kenar:
        w[u][v] = c
    d = [row[:] for row in w]
    gecen = []                          # gecen[k]: k. dongu bittikten sonra
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
        gecen.append([row[:] for row in d])
    paneller = [("başlangıç", w, None),
                ("k = 1 sonrasi", gecen[1], gecen[0]),
                ("k = 2 sonrasi", gecen[2], gecen[1]),
                ("k = 3 sonrasi", gecen[3], gecen[2])]
    fig, axs = plt.subplots(1, 4, figsize=(11.4, 3.4))
    for ax, (baslik, m, onceki) in zip(axs, paneller):
        ax.axis("off")
        ax.set_xlim(-0.6, n - 0.4)
        ax.set_ylim(n - 0.4, -0.6)
        for i in range(n):
            for j in range(n):
                degisti = onceki is not None and m[i][j] != onceki[i][j]
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1,
                                       facecolor=FILL[2] if degisti else "white",
                                       edgecolor=RULE, lw=1))
                s = "inf" if m[i][j] == INF else str(m[i][j])
                ax.text(j, i, s, ha="center", va="center", fontsize=10,
                        color=ACCENT if degisti else INK,
                        weight="bold" if degisti else "normal")
        ax.set_title(baslik, fontsize=10, color=INK, pad=6)
    fig.text(0.5, 0.02, "Sarı hücreler: önceki panele gore değişen degerler. "
             "k = 3 olmadan 0 -> 2 yolu bulunamaz.", ha="center",
             fontsize=9.2, color=MUTED)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return _save(fig, path)


# ----- 9. Union-Find: yol sikistirma --------------------------------------------
def uf_sikistirma(path):
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.8))
    for ax in axs:
        ax.set_xlim(-0.6, 4.6)
        ax.set_ylim(-0.4, 6.4)
        ax.set_aspect("equal")
        ax.axis("off")
    # (a) zincir: ata = [1, 2, 3, 4, 5, 5]; kok 5
    ax = axs[0]
    L = {i: (1.0, 5.6 - i * 1.0) for i in range(6)}
    for i in range(5):
        _kenar(ax, L[i], L[i + 1], EDGE[0], lw=1.4, r=0.3)
    for i in range(6):
        _dugum(ax, L[i], str(i), fill=FILL[2] if i == 5 else FILL[0],
               edge=ACCENT if i == 5 else EDGE[0], r=0.3, fs=9.8)
    ax.set_title("(a) find(0) öncesi: zincir", fontsize=10, color=INK, pad=4)
    # (b) find(0) sonrasi: herkes dogrudan koke
    ax = axs[1]
    R = {i: (0.2 + i * 0.85, 5.4) for i in range(5)}
    R[5] = (2.2, 0.8)
    for i in range(5):
        _kenar(ax, R[i], R[5], EDGE[0], lw=1.4, r=0.3)
    for i in range(6):
        _dugum(ax, R[i], str(i), fill=FILL[2] if i == 5 else FILL[0],
               edge=ACCENT if i == 5 else EDGE[0], r=0.3, fs=9.8)
    ax.set_title("(b) find(0) sonrasi: sıkıştırılmış", fontsize=10,
                 color=INK, pad=4)
    fig.tight_layout()
    return _save(fig, path)


# ----- 10. Kruskal ve Prim ----------------------------------------------------
MST_P = {0: (1.0, 4.5), 1: (4.0, 6.5), 2: (4.0, 2.5), 3: (7.0, 6.5),
         4: (7.2, 1.2), 5: (9.6, 4.5)}
MST_K = [(4, 0, 1), (3, 0, 2), (1, 1, 2), (2, 1, 3), (4, 2, 3),
         (5, 2, 4), (8, 3, 4), (9, 3, 5), (3, 4, 5)]


def mst_cift(path):
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 4.6))
    kruskal_sira = [(1, 2), (1, 3), (0, 2), (4, 5), (2, 4)]
    prim_sira = [(0, 2), (2, 1), (1, 3), (2, 4), (4, 5)]
    for ax, sira, baslik in [(axs[0], kruskal_sira, "(a) Kruskal: kenarlar küçükten"),
                             (axs[1], prim_sira, "(b) Prim: 0'dan büyüyerek")]:
        ax.set_xlim(0, 10.6)
        ax.set_ylim(0, 7.6)
        ax.set_aspect("equal")
        ax.axis("off")
        secili = {tuple(sorted(e)) for e in sira}
        for w, u, v in MST_K:
            key = tuple(sorted((u, v)))
            if key in secili:
                _cizgi(ax, MST_P[u], MST_P[v], ACCENT, lw=2.8)
            else:
                _cizgi(ax, MST_P[u], MST_P[v], RULE, lw=1.3)
            mx = (MST_P[u][0] + MST_P[v][0]) / 2
            my = (MST_P[u][1] + MST_P[v][1]) / 2
            ax.text(mx, my, str(w), fontsize=9, color=INK if key in secili else MUTED,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
        for u in MST_P:
            _dugum(ax, MST_P[u], str(u), fill=FILL[0], edge=EDGE[0], r=0.32)
        for i, e in enumerate(sira, 1):
            mx = (MST_P[e[0]][0] + MST_P[e[1]][0]) / 2
            my = (MST_P[e[0]][1] + MST_P[e[1]][1]) / 2
            ax.text(mx + 0.25, my + 0.42, "#%d" % i, fontsize=8.6,
                    color=ACCENT, weight="bold", ha="center")
        ax.set_title(baslik + "\nToplam = 14", fontsize=10, color=INK, pad=4)
    fig.tight_layout()
    return _save(fig, path)


# ----- 11. A* ve Dijkstra genisletmeleri --------------------------------------
def _astar_iz(izgara, bas, hedef, sezgisel):
    R, C = len(izgara), len(izgara[0])

    def h(r, c):
        return 0 if not sezgisel else abs(r - hedef[0]) + abs(c - hedef[1])

    g = {bas: 0}
    ebeveyn = {}
    kapali = set()
    yig = [(h(*bas), 0, bas)]
    while yig:
        _, gu, (r, c) = heapq.heappop(yig)
        if (r, c) in kapali:
            continue
        kapali.add((r, c))
        if (r, c) == hedef:
            break
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and izgara[nr][nc] > 0:
                yeni = gu + izgara[nr][nc]
                if yeni < g.get((nr, nc), INF):
                    g[(nr, nc)] = yeni
                    ebeveyn[(nr, nc)] = (r, c)
                    heapq.heappush(yig, (yeni + h(nr, nc), yeni, (nr, nc)))
    yol = []
    x = hedef
    while x != bas:
        yol.append(x)
        x = ebeveyn[x]
    yol.append(bas)
    return kapali, yol


def _izgara_uret():
    # astar.py ile ayni tohum ve ayni yeniden uretim kurali
    def uret(rng):
        izg = [[0 if rng.random() < 0.2 else rng.randint(1, 5)
                for _ in range(20)] for _ in range(20)]
        izg[0][0] = izg[19][19] = 1
        return izg
    rng = random.Random(42)
    izg = uret(rng)
    while True:
        k, _ = _astar_iz(izg, (0, 0), (19, 19), True)
        if (19, 19) in k:
            return izg
        izg = uret(rng)


def astar_izgara(path):
    izg = _izgara_uret()
    hedef = (19, 19)
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 5.0))
    for ax, sez, baslik in [(axs[0], True, "A* (Manhattan sezgisel)"),
                            (axs[1], False, "Dijkstra (h = 0)")]:
        kap, yol = _astar_iz(izg, (0, 0), hedef, sez)
        for r in range(20):
            for c in range(20):
                if izg[r][c] == 0:
                    fill = "#3A3733"
                elif (r, c) in yol:
                    fill = ACCENT
                elif (r, c) in kap:
                    fill = FILL[2]
                else:
                    fill = "white"
                ax.add_patch(Rectangle((c, 19 - r), 1, 1, facecolor=fill,
                                       edgecolor=RULE, lw=0.4))
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 20)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("%s: %d düğüm genişletildi" % (baslik, len(kap)),
                     fontsize=10, color=INK, pad=5)
    fig.text(0.5, 0.01, "Kırmızı: bulunan yol; sarı: genişletilen düğümler; "
             "koyu: engel; sol üst: başlangıç, sağ alt: hedef",
             ha="center", fontsize=8.8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gorseller")
    for fn, ad in [(dfs_zaman, "b17_dfs_zaman.png"),
                   (topo_sira, "b17_topo_sira.png"),
                   (iki_renk, "b17_iki_renk.png"),
                   (scc_kopru, "b17_scc_köprü.png"),
                   (dijkstra_adim, "b17_dijkstra_adim.png"),
                   (negatif_kenar, "b17_negatif_kenar.png"),
                   (bellman_tur, "b17_bellman_tur.png"),
                   (floyd_matris, "b17_floyd_matris.png"),
                   (uf_sikistirma, "b17_uf_sikistirma.png"),
                   (mst_cift, "b17_mst_cift.png"),
                   (astar_izgara, "b17_astar_izgara.png")]:
        print(fn(os.path.join(out, ad)))
