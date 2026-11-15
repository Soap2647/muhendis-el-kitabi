# dijkstra_negatif.py: Dijkstra'nin acgozlu secimi negatif kenarda
# neden bozulur? Kucuk bir cizgede Dijkstra ve Bellman-Ford sonucunu
# karsilastirir; rastgele DAG'lerde (dongu yok) istatistik verir.
import heapq
import random

INF = float("inf")


def dijkstra(n, kenarlar, s):
    komsu = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        komsu[u].append((v, w))
    dist = [INF] * n
    dist[s] = 0
    kesin = [False] * n
    yigin = [(0, s)]
    while yigin:
        d, u = heapq.heappop(yigin)
        if kesin[u]:
            continue
        kesin[u] = True           # bir kez kesinlesen dugum degismez
        for v, w in komsu[u]:
            if not kesin[v] and d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(yigin, (dist[v], v))
    return dist


def bellman_ford(n, kenarlar, s):
    dist = [INF] * n
    dist[s] = 0
    for _ in range(n - 1):
        for u, v, w in kenarlar:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist


def main():
    # 0 = S, 1 = X, 2 = Y
    cizge = [(0, 1, 5), (0, 2, 6), (2, 1, -3)]
    print("Dijkstra     :", dijkstra(3, cizge, 0))
    print("Bellman-Ford :", bellman_ford(3, cizge, 0))
    rnd = random.Random(42)
    hata_pozitif = hata_negatif = 0
    for _ in range(300):
        n = rnd.randint(3, 7)
        kenar = []
        for u in range(n):
            for v in range(u + 1, n):
                if rnd.random() < 0.5:
                    kenar.append((u, v, rnd.randint(1, 9)))
        if dijkstra(n, kenar, 0) != bellman_ford(n, kenar, 0):
            hata_pozitif += 1
        neg = [(u, v, rnd.randint(-3, 6)) for u, v, _ in kenar]
        if dijkstra(n, neg, 0) != bellman_ford(n, neg, 0):
            hata_negatif += 1
    print("300 DAG, pozitif kenar, hata:", hata_pozitif)
    print("300 DAG, negatif kenar, hata:", hata_negatif)


if __name__ == "__main__":
    main()
