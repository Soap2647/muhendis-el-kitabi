# dijkstra.py - BFS (agirliksiz), 0-1 BFS ve Dijkstra (ikili heap).
import heapq
from collections import deque

INF = float("inf")


def bfs_mesafe(n, adj, kaynak):
    """Agirliksiz graf: kenar sayisi cinsinden mesafeler."""
    dist = [INF] * n
    if n == 0:
        return dist
    dist[kaynak] = 0
    kuyruk = deque([kaynak])
    while kuyruk:
        u = kuyruk.popleft()
        for v, _ in adj[u]:
            if dist[v] == INF:
                dist[v] = dist[u] + 1
                kuyruk.append(v)
    return dist


def zero_one_bfs(n, adj, kaynak):
    """Agirliklar yalnizca 0 ya da 1 ise, deque ile O(V + E)."""
    dist = [INF] * n
    if n == 0:
        return dist
    dist[kaynak] = 0
    dq = deque([kaynak])
    while dq:
        u = dq.popleft()
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                if w == 0:
                    dq.appendleft(v)   # 0 maliyet: basa
                else:
                    dq.append(v)       # 1 maliyet: sona
    return dist


def dijkstra(n, adj, kaynak):
    """adj[u] = [(v, w), ...], w >= 0. Donus: (dist, ebeveyn)."""
    dist = [INF] * n
    ebeveyn = [-1] * n
    if n == 0:
        return dist, ebeveyn
    bitti = [False] * n
    dist[kaynak] = 0
    yigin = [(0, kaynak)]
    while yigin:
        d, u = heapq.heappop(yigin)
        if bitti[u]:
            continue                   # tembel silme: eski kayit
        bitti[u] = True
        for v, w in adj[u]:
            yeni = d + w
            if yeni < dist[v]:
                dist[v] = yeni
                ebeveyn[v] = u
                heapq.heappush(yigin, (yeni, v))
    return dist, ebeveyn


def yol_kur(ebeveyn, hedef):
    """Ebeveyn dizisinden kaynak->hedef yolunu geri kurar.
    Hedef erisilemezse de bir liste doner; caller dist'e bakmali."""
    yol = []
    u = hedef
    while u != -1:
        yol.append(u)
        u = ebeveyn[u]
    return yol[::-1]


if __name__ == "__main__":
    kenarlar = [(0, 1, 7), (0, 2, 9), (0, 5, 14), (1, 2, 10),
                (1, 3, 15), (2, 3, 11), (2, 5, 2), (3, 4, 6),
                (5, 4, 9)]
    n = 6
    adj = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        adj[u].append((v, w))
    dist, ebeveyn = dijkstra(n, adj, 0)
    for t in range(n):
        print(f"{t}: mesafe={dist[t]:>2}  yol={yol_kur(ebeveyn, t)}")
    print("BFS (kenar sayisi):", bfs_mesafe(n, adj, 0))
