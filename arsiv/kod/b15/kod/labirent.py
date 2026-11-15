"""Labirent: geri izleme ile yol bulma ve kendini kesmeyen
yollari sayma."""

YONLER = [(0, 1), (1, 0), (0, -1), (-1, 0)]

HARITA = [
    "S#.....",
    ".#.###.",
    ".#...#.",
    ".####.#",
    "......E",
]


def konum(harita, isaret):
    for r, satir in enumerate(harita):
        if isaret in satir:
            return r, satir.index(isaret)
    raise ValueError("isaret yok: " + isaret)


def yol_bul(harita):
    n, m = len(harita), len(harita[0])
    bas = konum(harita, "S")
    son = konum(harita, "E")
    ziyaret = set()
    yol = []

    def dfs(r, c):
        yol.append((r, c))
        if (r, c) == son:
            return True
        ziyaret.add((r, c))
        for dr, dc in YONLER:
            nr, nc = r + dr, c + dc
            if (0 <= nr < n and 0 <= nc < m
                    and harita[nr][nc] != "#"
                    and (nr, nc) not in ziyaret):
                if dfs(nr, nc):
                    return True
        ziyaret.discard((r, c))
        yol.pop()                   # cikmaz: geri al
        return False

    if dfs(*bas):
        return yol
    return None


def kose_yol_sayisi(k):
    """k x k dugumlu izgarada (0,0)'dan (k-1,k-1)'a
    kendini kesmeyen yollarin sayisi."""
    ziyaret = set()
    say = [0]

    def dfs(r, c):
        if (r, c) == (k - 1, k - 1):
            say[0] += 1
            return
        ziyaret.add((r, c))
        for dr, dc in YONLER:
            nr, nc = r + dr, c + dc
            if (0 <= nr < k and 0 <= nc < k
                    and (nr, nc) not in ziyaret):
                dfs(nr, nc)
        ziyaret.discard((r, c))

    dfs(0, 0)
    return say[0]


if __name__ == "__main__":
    for k in range(2, 6):
        print("%d x %d dugum: %6d yol" % (k, k, kose_yol_sayisi(k)))
    yol = yol_bul(HARITA)
    print("yol uzunlugu:", len(yol) - 1, "adim")
    izgara = [list(s) for s in HARITA]
    for r, c in yol:
        if izgara[r][c] == ".":
            izgara[r][c] = "*"
    for satir in izgara:
        print("".join(satir))
