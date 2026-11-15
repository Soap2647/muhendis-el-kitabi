def ifadeler(rakam, hedef):
    sonuc = []

    def dfs(i, yol, toplam, son):
        if i == len(rakam):
            if toplam == hedef:
                sonuc.append(yol)
            return
        for j in range(i + 1, len(rakam) + 1):
            parca = rakam[i:j]
            if len(parca) > 1 and parca[0] == "0":
                break
            v = int(parca)
            if i == 0:
                dfs(j, parca, v, v)
            else:
                dfs(j, yol + "+" + parca, toplam + v, v)
                dfs(j, yol + "-" + parca, toplam - v, -v)
                dfs(j, yol + "*" + parca,
                    toplam - son + son * v, son * v)

    dfs(0, "", 0, 0)
    return sonuc


if __name__ == "__main__":
    print(ifadeler("123", 6))
    print(ifadeler("232", 8))
    print(ifadeler("105", 5))
