def parantezler(n):
    sonuc = []

    def dfs(yol, acik, kapali):
        if len(yol) == 2 * n:
            sonuc.append("".join(yol))
            return
        if acik < n:
            yol.append("(")
            dfs(yol, acik + 1, kapali)
            yol.pop()
        if kapali < acik:
            yol.append(")")
            dfs(yol, acik, kapali + 1)
            yol.pop()

    dfs([], 0, 0)
    return sonuc


if __name__ == "__main__":
    print(parantezler(3))
    for n in range(1, 6):
        print(n, len(parantezler(n)))
