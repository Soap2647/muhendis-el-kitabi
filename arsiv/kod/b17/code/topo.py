# topo.py - Topolojik siralama: Kahn (derece+kuyruk) ve DFS.
from collections import deque

INF = float("inf")


def kahn(n, adj):
    """adj[u] = [v, ...]. Donus: (sira, dongu_var).
    Dongu varsa sira tum dugumleri icermez."""
    derece = [0] * n
    for u in range(n):
        for v in adj[u]:
            derece[v] += 1
    kuyruk = deque(u for u in range(n) if derece[u] == 0)
    sira = []
    while kuyruk:
        u = kuyruk.popleft()
        sira.append(u)
        for v in adj[u]:
            derece[v] -= 1
            if derece[v] == 0:
                kuyruk.append(v)
    return sira, len(sira) != n


def dfs_topo(n, adj):
    """Donus: (sira, None) ya da dongu varsa (None, (u, v)), v griyken
    u'dan gorulen geri kenar."""
    renk = [0] * n                     # 0 beyaz, 1 gri, 2 siyah
    bitis = []
    dongu = [None]

    def ziyaret(u):
        renk[u] = 1
        for v in adj[u]:
            if dongu[0] is not None:
                return
            if renk[v] == 1:           # gri: geri kenar, dongu!
                dongu[0] = (u, v)
                return
            if renk[v] == 0:
                ziyaret(v)
        renk[u] = 2
        bitis.append(u)                # cikis: sonuncu biten ilk

    for u in range(n):
        if renk[u] == 0:
            ziyaret(u)
    if dongu[0] is not None:
        return None, dongu[0]
    return bitis[::-1], None


def dag_en_kisa(n, adj, kaynak):
    """adj[u] = [(v, w)]; yalnizca DAG. Donus: dist listesi."""
    komsu = [[v for v, _ in adj[u]] for u in range(n)]
    sira, dongulu = kahn(n, komsu)
    if dongulu:
        raise ValueError("graf DAG degil")
    dist = [INF] * n
    dist[kaynak] = 0
    for u in sira:                     # topolojik sirada tek gecis
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist


if __name__ == "__main__":
    ad = ["Programlama", "Matematik", "Veri Yapilari", "Algoritmalar",
          "Isletim Sist.", "Ag", "Derleyici", "Bitirme"]
    kenar = [(0, 2), (0, 4), (2, 3), (1, 3), (4, 5), (2, 6), (3, 6),
             (3, 7), (5, 7), (6, 7)]
    adj = [[] for _ in ad]
    for u, v in kenar:
        adj[u].append(v)
    sira, dongulu = kahn(len(ad), adj)
    print("Kahn :", [ad[u] for u in sira], "dongu:", dongulu)
    sira, dongu = dfs_topo(len(ad), adj)
    print("DFS  :", [ad[u] for u in sira], "dongu:", dongu)
    adj[6].append(0)                   # Derleyici -> Programlama
    sira, dongulu = kahn(len(ad), adj)
    print("Dongulu Kahn: sira", sira, "dongu:", dongulu)
    sira, dongu = dfs_topo(len(ad), adj)
    print("Dongulu DFS : sira", sira, "geri kenar:", dongu)
