# bellman.py - Bellman-Ford: negatif kenar ve negatif dongu tespiti.
# Ayni grafta Dijkstra'nin negatif kenarda neden yanlis sonuc
# verdigini de gosterir.
from dijkstra import INF, dijkstra, yol_kur


def bellman_ford(n, kenarlar, kaynak):
    """kenarlar: [(u, v, w)]. Donus: (dist, ebeveyn); kaynaktan
    erisilebilir bir negatif dongu varsa None."""
    dist = [INF] * n
    ebeveyn = [-1] * n
    if n == 0:
        return dist, ebeveyn
    dist[kaynak] = 0
    for _ in range(n - 1):             # V - 1 tur
        degisti = False
        for u, v, w in kenarlar:
            if dist[u] + w < dist[v]:  # INF + w = INF: atlanir
                dist[v] = dist[u] + w
                ebeveyn[v] = u
                degisti = True
        if not degisti:
            break                      # erken durma
    for u, v, w in kenarlar:           # V. tur: hala gevsetiliyor mu?
        if dist[u] + w < dist[v]:
            return None                # negatif dongu erisilebilir
    return dist, ebeveyn


if __name__ == "__main__":
    # A=0, B=1, C=2, D=3: A->B 1, A->C 5, C->B -10, B->D 1
    kenarlar = [(0, 1, 1), (0, 2, 5), (2, 1, -10), (1, 3, 1)]
    n = 4
    adj = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        adj[u].append((v, w))
    d1, _ = dijkstra(n, adj, 0)
    print("Dijkstra :", d1)
    d2, e2 = bellman_ford(n, kenarlar, 0)
    print("Bellman  :", d2)
    print("Yol D    :", yol_kur(e2, 3))
    # B->C (1) ekleyince C->B->C dongusu: -10 + 1 = -9 < 0
    donguly = kenarlar + [(1, 2, 1)]
    print("Negatif dongu:", bellman_ford(n, donguly, 0))
