# mst.py - Union-Find (yol sikistirma + rank), Kruskal ve Prim.
import heapq


class UnionFind:
    def __init__(self, n):
        self.ata = list(range(n))
        self.rank = [0] * n

    def bul(self, x):
        kok = x
        while self.ata[kok] != kok:           # 1. gecis: koku bul
            kok = self.ata[kok]
        while self.ata[x] != kok:             # 2. gecis: sikistir
            sonraki = self.ata[x]
            self.ata[x] = kok
            x = sonraki
        return kok

    def birlestir(self, a, b):
        ra, rb = self.bul(a), self.bul(b)
        if ra == rb:
            return False                      # ayni kume: dongu olur
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra                   # kucugu buyuge bagla
        self.ata[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(n, kenarlar):
    """kenarlar: [(agirlik, u, v)], yonsuz.
    Donus: (toplam, secilen)."""
    uf = UnionFind(n)
    toplam, secilen = 0, []
    for w, u, v in sorted(kenarlar):          # en ucuzdan basla
        if uf.birlestir(u, v):
            toplam += w
            secilen.append((u, v, w))
    return toplam, secilen


def prim(n, adj):
    """adj[u] = [(v, w)], yonsuz: her kenar iki yone de yazilir.
    Baglantisiz grafta yalnizca 0'in bileseni kapsanir."""
    if n == 0:
        return 0, []
    bitti = [False] * n
    toplam, secilen = 0, []
    yigin = [(0, 0, -1)]              # (agirlik, dugum, ebeveyn)
    while yigin:
        w, u, p = heapq.heappop(yigin)
        if bitti[u]:
            continue
        bitti[u] = True
        if p != -1:
            toplam += w
            secilen.append((p, u, w))
        for v, wv in adj[u]:
            if not bitti[v]:
                heapq.heappush(yigin, (wv, v, u))
    return toplam, secilen


if __name__ == "__main__":
    kenarlar = [(4, 0, 1), (3, 0, 2), (1, 1, 2), (2, 1, 3),
                (4, 2, 3), (5, 2, 4), (8, 3, 4), (9, 3, 5),
                (3, 4, 5)]
    n = 6
    adj = [[] for _ in range(n)]
    for w, u, v in kenarlar:
        adj[u].append((v, w))
        adj[v].append((u, w))
    print("Kruskal:", kruskal(n, kenarlar))
    print("Prim   :", prim(n, adj))
