# astar.py - Izgarada A* ve Dijkstra karsilastirmasi.
# izgara[r][c] = 0: engel; >= 1: o hucreye girmenin maliyeti.
import heapq
import random

INF = float("inf")


def a_star(izgara, bas, hedef, sezgisel=True):
    """Donus: (maliyet, genisletilen_dugum_sayisi). sezgisel=False ise
    h = 0 alinir ve algoritma Dijkstra'ya donusur."""
    R, C = len(izgara), len(izgara[0])

    def h(r, c):
        if not sezgisel:
            return 0
        return abs(r - hedef[0]) + abs(c - hedef[1])   # Manhattan

    g = {bas: 0}
    kapali = set()
    yigin = [(h(*bas), 0, bas)]               # (f = g + h, g, dugum)
    genis = 0
    while yigin:
        _, gu, (r, c) = heapq.heappop(yigin)
        if (r, c) in kapali:
            continue
        kapali.add((r, c))
        genis += 1
        if (r, c) == hedef:
            return gu, genis
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and izgara[nr][nc] > 0:
                yeni = gu + izgara[nr][nc]
                if yeni < g.get((nr, nc), INF):
                    g[(nr, nc)] = yeni
                    f = yeni + h(nr, nc)
                    heapq.heappush(yigin, (f, yeni, (nr, nc)))
    return INF, genis


def rastgele_izgara(n, rng, p_engel=0.2):
    izgara = [[0 if rng.random() < p_engel else rng.randint(1, 5)
               for _ in range(n)] for _ in range(n)]
    izgara[0][0] = izgara[n - 1][n - 1] = 1    # bas ve hedef bos
    return izgara


if __name__ == "__main__":
    rng = random.Random(42)
    hedef = (19, 19)
    izgara = rastgele_izgara(20, rng)
    # ulasilabilir bir izgara bulana kadar yeniden uret
    while a_star(izgara, (0, 0), hedef)[0] == INF:
        izgara = rastgele_izgara(20, rng)
    m1, g1 = a_star(izgara, (0, 0), hedef, sezgisel=True)
    m2, g2 = a_star(izgara, (0, 0), hedef, sezgisel=False)
    print("A*      : maliyet", m1, " genisletilen", g1)
    print("Dijkstra: maliyet", m2, " genisletilen", g2)
