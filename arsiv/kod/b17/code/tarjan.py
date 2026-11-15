# tarjan.py - Tarjan: guclu bagli bilesen (yonlu), kopru/eklem.
import sys


def tarjan_scc(n, adj):
    """Yonlu graf. Donus: bilesen listesi (her biri sirali)."""
    index = [-1] * n            # ziyaret sirasi
    low = [0] * n               # alt agactan erisilen en kucuk index
    yigin, ycinde = [], [False] * n
    bilesenler = []
    sayac = 0

    def ziyaret(u):
        nonlocal sayac
        index[u] = low[u] = sayac
        sayac += 1
        yigin.append(u)
        ycinde[u] = True
        for v in adj[u]:
            if index[v] == -1:              # agac kenari
                ziyaret(v)
                low[u] = min(low[u], low[v])
            elif ycinde[v]:                 # yiginda: ayni bilesen
                low[u] = min(low[u], index[v])
        if low[u] == index[u]:              # u bir bilesenin koku
            bilesen = []
            while True:
                w = yigin.pop()
                ycinde[w] = False
                bilesen.append(w)
                if w == u:
                    break
            bilesenler.append(sorted(bilesen))

    for u in range(n):
        if index[u] == -1:
            ziyaret(u)
    return bilesenler


def kopru_eklem(n, adj):
    """Yonsuz, basit graf. Donus: (kopruler, eklemler)."""
    disc = [-1] * n            # kesif zamani
    low = [0] * n
    kopruler, eklem = [], set()
    zaman = 0

    def dfs(u, ata):
        nonlocal zaman
        disc[u] = low[u] = zaman
        zaman += 1
        cocuk = 0
        for v in adj[u]:
            if v == ata:                    # ebeveyne kenari atla
                continue
            if disc[v] == -1:
                cocuk += 1
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:        # u'yu asmaz
                    kopruler.append((min(u, v), max(u, v)))
                if ata != -1 and low[v] >= disc[u]:
                    eklem.add(u)
            else:
                low[u] = min(low[u], disc[v])
        if ata == -1 and cocuk > 1:         # kok, 2+ cocuk
            eklem.add(u)

    for u in range(n):
        if disc[u] == -1:
            dfs(u, -1)
    return sorted(kopruler), sorted(eklem)


if __name__ == "__main__":
    print(sys.getrecursionlimit(), "yigin siniri")
    # Yonlu: {0,1,2}, {3,4,5}, {6,7} uc bilesen
    kenar = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5),
             (5, 3), (5, 6), (6, 7), (7, 6)]
    adj = [[] for _ in range(8)]
    for u, v in kenar:
        adj[u].append(v)
    print("SCC:", tarjan_scc(8, adj))
    # Sensor agi: 0 = gateway; s1, s2 yaprak; s3-s4-s5 ucgeni
    kenar = [(0, 1), (0, 2), (0, 3), (3, 4), (4, 5), (5, 3)]
    adj = [[] for _ in range(6)]
    for u, v in kenar:
        adj[u].append(v)
        adj[v].append(u)
    kop, ekl = kopru_eklem(6, adj)
    print("Kopruler :", kop)
    print("Eklemler :", ekl)
