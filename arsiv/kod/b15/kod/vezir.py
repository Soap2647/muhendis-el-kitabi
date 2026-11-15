"""N vezir: budamali ve budamasiz geri izleme."""


def guvenli(yerler, satir, sutun):
    for r, c in enumerate(yerler):
        if c == sutun or abs(c - sutun) == satir - r:
            return False
    return True


def cozumler(n):
    sonuc = []
    yerler = []

    def dfs(satir):
        if satir == n:
            sonuc.append(yerler[:])
            return
        for s in range(n):
            if guvenli(yerler, satir, s):
                yerler.append(s)
                dfs(satir + 1)
                yerler.pop()

    dfs(0)
    return sonuc


def budamali_say(n):
    """Dugum sayisi: her cagri bir dugum."""
    cozum = [0]
    dugum = [0]
    yerler = []

    def dfs(satir):
        dugum[0] += 1
        if satir == n:
            cozum[0] += 1
            return
        for s in range(n):
            if guvenli(yerler, satir, s):
                yerler.append(s)
                dfs(satir + 1)
                yerler.pop()

    dfs(0)
    return cozum[0], dugum[0]


def budamasiz_say(n):
    """Her satira farkli sutun koy (sutun cakismasi budanmaz),
    capraz kontrolu yalnizca yaprakta yap."""
    cozum = [0]
    dugum = [0]
    kullanildi = [False] * n
    yerler = []

    def dfs(satir):
        dugum[0] += 1
        if satir == n:
            if guvenli_son(yerler):
                cozum[0] += 1
            return
        for s in range(n):
            if not kullanildi[s]:
                kullanildi[s] = True
                yerler.append(s)
                dfs(satir + 1)
                yerler.pop()
                kullanildi[s] = False

    dfs(0)
    return cozum[0], dugum[0]


def guvenli_son(yerler):
    n = len(yerler)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(yerler[i] - yerler[j]) == j - i:
                return False
    return True


if __name__ == "__main__":
    print("N  cozum  budamali  budamasiz")
    for n in range(4, 9):
        c1, d1 = budamali_say(n)
        c2, d2 = budamasiz_say(n)
        print("%d %6d %9d %10d" % (n, c1, d1, d2))
    print("ilk cozum (n=8):", cozumler(8)[0])
