# ornek2_gecikme.py - Yonlendiriciler arasi en dusuk gecikmeli yol.
import heapq

INF = float("inf")
AD = ["R0", "R1", "R2", "R3", "R4", "R5"]


def en_kisa(n, kenar, kaynak, hedef):
    """Dijkstra + ebeveyn dizisi. Her adimin izini yazar."""
    adj = [[] for _ in range(n)]
    for u, v, w in kenar:              # yonsuz: iki yone de
        adj[u].append((v, w))
        adj[v].append((u, w))
    dist = [INF] * n
    ebeveyn = [-1] * n
    bitti = [False] * n
    dist[kaynak] = 0
    yigin = [(0, kaynak)]
    while yigin:
        d, u = heapq.heappop(yigin)
        if bitti[u]:
            continue
        bitti[u] = True
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                ebeveyn[v] = u
                heapq.heappush(yigin, (dist[v], v))
        print(f"  {AD[u]} islendi (d={d}); dist =",
              [x if x < INF else "inf" for x in dist])
    yol = []
    u = hedef
    while u != -1:
        yol.append(AD[u])
        u = ebeveyn[u]
    return dist[hedef], yol[::-1]


if __name__ == "__main__":
    kenar = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 5), (2, 3, 8),
             (3, 4, 3), (2, 4, 12), (4, 5, 1), (3, 5, 6)]
    gecikme, yol = en_kisa(6, kenar, 0, 5)
    print("R0 -> R5 gecikme:", gecikme, "ms; yol:", " - ".join(yol))
