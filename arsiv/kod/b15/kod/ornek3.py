IZGARA = [
    ["A", "B", "C", "E"],
    ["S", "F", "C", "S"],
    ["A", "D", "E", "E"],
]


def var_mi(izgara, kelime):
    n, m = len(izgara), len(izgara[0])
    ziyaret = [[False] * m for _ in range(n)]

    def dfs(r, c, k):
        if k == len(kelime):
            return True
        if not (0 <= r < n and 0 <= c < m):
            return False
        if ziyaret[r][c] or izgara[r][c] != kelime[k]:
            return False
        ziyaret[r][c] = True
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            if dfs(r + dr, c + dc, k + 1):
                return True
        ziyaret[r][c] = False
        return False

    for r in range(n):
        for c in range(m):
            if dfs(r, c, 0):
                return True
    return False


if __name__ == "__main__":
    for kelime in ("ABCCED", "SEE", "ABCB"):
        print(kelime, var_mi(IZGARA, kelime))
