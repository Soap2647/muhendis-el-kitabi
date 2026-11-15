# floyd.py - Floyd-Warshall: tum ciftler icin en kisa yollar (DP).
INF = float("inf")


def floyd(n, w):
    """w[i][j]: kenar agirligi (yoksa INF), w[i][i] = 0.
    Donus: (dist, sonraki); sonraki[i][j], i'den j'ye giden yolun ilk
    adimidir (yol yoksa -1)."""
    dist = [row[:] for row in w]
    sonraki = [[j if w[i][j] < INF else -1 for j in range(n)]
               for i in range(n)]
    for k in range(n):                 # ara dugum k: en dis dongu
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    sonraki[i][j] = sonraki[i][k]
    return dist, sonraki


def yol(sonraki, i, j):
    """sonraki tablosundan i -> j yolunu cikarir."""
    if sonraki[i][j] == -1:
        return []
    p = [i]
    while i != j:
        i = sonraki[i][j]
        p.append(i)
    return p


def floyd_yanlis(n, w):
    """YANLIS siralama: k dongusu en icte. Karsi ornek icin."""
    dist = [row[:] for row in w]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist


if __name__ == "__main__":
    # Kenarlar: 0->1, 1->3, 3->2 (hepsi 1). Yol: 0 -> 1 -> 3 -> 2
    n = 4
    w = [[INF] * n for _ in range(n)]
    for i in range(n):
        w[i][i] = 0
    w[0][1] = 1
    w[1][3] = 1
    w[3][2] = 1
    dist, sonraki = floyd(n, w)
    print("Dogru dist:")
    for satir in dist:
        print("  ", satir)
    print("0 -> 2 yolu:", yol(sonraki, 0, 2))
    print("Yanlis siralama dist:")
    for satir in floyd_yanlis(n, w):
        print("  ", satir)
