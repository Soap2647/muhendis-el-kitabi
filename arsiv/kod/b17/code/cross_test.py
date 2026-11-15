# cross_test.py - Algoritmalari birbirine ve bagimsiz
# referanslara karsi
# sinar. Tum rastgele veriler random.Random(42) ile uretilir.
import graphlib
import itertools
import random

from bellman import bellman_ford
from bipartite import iki_renkli
from dijkstra import INF, bfs_mesafe, dijkstra, zero_one_bfs
from floyd import floyd
from mst import UnionFind, kruskal, prim
from tarjan import kopru_eklem, tarjan_scc
from topo import dag_en_kisa, dfs_topo, kahn


def yonlu_kenarlar(rng, n, p, lo, hi):
    """(u, v, w) listesi; her yonlu cift en fazla bir kez."""
    return [(u, v, rng.randint(lo, hi)) for u in range(n)
            for v in range(n) if u != v and rng.random() < p]


def komsu(n, kenarlar):
    adj = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        adj[u].append((v, w))
    return adj


def matris(n, kenarlar):
    w = [[INF] * n for _ in range(n)]
    for i in range(n):
        w[i][i] = 0
    for u, v, c in kenarlar:
        w[u][v] = min(w[u][v], c)
    return w


def test_1_negatifsiz():
    """Dijkstra = Bellman-Ford = Floyd (negatif kenar yok)."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 12)
        k = yonlu_kenarlar(rng, n, 0.3, 0, 9)
        s = rng.randrange(n)
        d1, _ = dijkstra(n, komsu(n, k), s)
        d2, _ = bellman_ford(n, k, s)
        fd = floyd(n, matris(n, k))[0]
        ok += d1 == d2 == fd[s]
    print(f"Test 1 Dijkstra = BF = Floyd: {ok}/{top}")


def test_2_negatif():
    """Negatif kenar: BF None <=> kaynaktan negatif dongu erisilir."""
    rng, ok, top, dongulu = random.Random(42), 0, 200, 0
    for _ in range(top):
        n = rng.randint(2, 8)
        k = yonlu_kenarlar(rng, n, 0.35, -2, 9)
        s = rng.randrange(n)
        fd = floyd(n, matris(n, k))[0]
        beklenen = any(fd[s][v] < INF and fd[v][v] < 0
                       for v in range(n))
        sonuc = bellman_ford(n, k, s)
        dongulu += beklenen
        if sonuc is None:
            ok += beklenen
        else:
            ok += (not beklenen) and sonuc[0] == fd[s]
    print(f"Test 2 BF negatif dongu: {ok}/{top} (dongulu {dongulu})")


def test_3_bfs():
    """BFS = Dijkstra (w=1); 0-1 BFS = Dijkstra (w in {0,1})."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 15)
        k1 = yonlu_kenarlar(rng, n, 0.2, 1, 1)
        k2 = yonlu_kenarlar(rng, n, 0.2, 0, 1)
        s = rng.randrange(n)
        a = (bfs_mesafe(n, komsu(n, k1), s)
             == dijkstra(n, komsu(n, k1), s)[0])
        b = (zero_one_bfs(n, komsu(n, k2), s)
             == dijkstra(n, komsu(n, k2), s)[0])
        ok += a and b
    print(f"Test 3 BFS ve 0-1 BFS: {ok}/{top}")


def rastgele_bagli(rng, n):
    """Once rastgele bir agac, sonra ek kenarlar: her zaman bagli."""
    k = [(rng.randrange(v), v, rng.randint(1, 5))
         for v in range(1, n)]
    for _ in range(n):
        u, v = rng.sample(range(n), 2)
        k.append((u, v, rng.randint(1, 5)))
    return k                               # (u, v, w)


def test_4_mst():
    """Kruskal = Prim (toplam agirlik); n-1 kenar; dugumler bagli."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(2, 15)
        k = rastgele_bagli(rng, n)
        adj = [[] for _ in range(n)]
        for u, v, w in k:
            adj[u].append((v, w))
            adj[v].append((u, w))
        t1, s1 = kruskal(n, [(w, u, v) for u, v, w in k])
        t2, s2 = prim(n, adj)
        uf = UnionFind(n)
        for u, v, _ in s1:
            uf.birlestir(u, v)
        bagli = len({uf.bul(x) for x in range(n)}) == 1
        ok += (t1 == t2 and len(s1) == n - 1
               and len(s2) == n - 1 and bagli)
    print(f"Test 4 Kruskal = Prim: {ok}/{top}")


def test_5_sinir():
    """Sinir durumlari: bos graf, tek dugum, ulasilamayan dugum,
    esit agirlik."""
    print("Test 5 sinir durumlari:")
    print("  kruskal(0, [])       =", kruskal(0, []))
    print("  prim(0, [])          =", prim(0, []))
    print("  dijkstra(1,[[]],0)   =", dijkstra(1, [[]], 0)[0])
    print("  floyd(1, [[0]])      =", floyd(1, [[0]])[0])
    print("  tarjan_scc(1,[[]])   =", tarjan_scc(1, [[]]))
    print("  kahn(0, [])          =", kahn(0, []))
    print("  ulasilamayan dugum   =",
          dijkstra(3, [[(1, 4)], [], []], 0)[0])
    print("  esit agirlik Kruskal =",
          kruskal(3, [(1, 0, 1), (1, 1, 2), (1, 0, 2)]))


def test_6_scc():
    """Tarjan SCC = karsilikli erisilebilirlik (transitif kapanis)."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 10)
        k = yonlu_kenarlar(rng, n, 0.25, 1, 1)
        adj = [[] for _ in range(n)]
        for u, v, _ in k:
            adj[u].append(v)
        w = matris(n, k)
        r = [[i == j or w[i][j] < INF for j in range(n)]
             for i in range(n)]
        for m in range(n):
            for i in range(n):
                for j in range(n):
                    r[i][j] = r[i][j] or (r[i][m] and r[m][j])
        beklenen = {frozenset(v for v in range(n)
                              if r[u][v] and r[v][u])
                    for u in range(n)}
        bulunan = {frozenset(c) for c in tarjan_scc(n, adj)}
        ok += beklenen == bulunan
    print(f"Test 6 Tarjan SCC: {ok}/{top}")


def bilesen_sayisi(n, kenar):
    adj = [[] for _ in range(n)]
    for u, v in kenar:
        adj[u].append(v)
        adj[v].append(u)
    gorulen, sayi = [False] * n, 0
    for s in range(n):
        if not gorulen[s]:
            sayi += 1
            yig = [s]
            gorulen[s] = True
            while yig:
                x = yig.pop()
                for y in adj[x]:
                    if not gorulen[y]:
                        gorulen[y] = True
                        yig.append(y)
    return sayi


def test_7_kopru_eklem():
    """Kopru: silince bilesen artar. Eklem: dugum silince
    bilesen artar."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(2, 9)
        adaylar = [(rng.randrange(n), rng.randrange(n))
                   for _ in range(rng.randint(1, 2 * n))]
        kenar = sorted({tuple(sorted(e)) for e in adaylar
                        if e[0] != e[1]})
        adj = [[] for _ in range(n)]
        for u, v in kenar:
            adj[u].append(v)
            adj[v].append(u)
        kop, ekl = kopru_eklem(n, adj)
        b0 = bilesen_sayisi(n, kenar)
        beklenen_kop = sorted(e for e in kenar
                              if bilesen_sayisi(
                                  n, [f for f in kenar if f != e])
                              > b0)
        beklenen_ekl = sorted(u for u in range(n)
                              if bilesen_sayisi(
                                  n, [e for e in kenar if u not in e])
                              - 1 > b0)
        ok += kop == beklenen_kop and ekl == beklenen_ekl
    print(f"Test 7 kopru ve eklem: {ok}/{top}")


def test_8_topo():
    """Kahn ve DFS: gecerli siralar; dongu tespiti graphlib ile
    ayni."""
    rng, ok, top = random.Random(42), 0, 200
    for _ in range(top):
        n = rng.randint(1, 10)
        dag = rng.random() < 0.5
        k = [(u, v) for u in range(n) for v in range(n)
             if u != v and rng.random() < 0.3 and (not dag or u < v)]
        adj = [[] for _ in range(n)]
        for u, v in k:
            adj[u].append(v)
        sira_k, dk = kahn(n, adj)
        sira_d, dd = dfs_topo(n, adj)
        ts = graphlib.TopologicalSorter(
            {v: [u for u, w in k if w == v] for v in range(n)})
        try:
            ts.prepare()
            gd = False
        except graphlib.CycleError:
            gd = True
        gecerli = True
        if not dk and not dd:
            for sira in (sira_k, sira_d):
                poz = {u: i for i, u in enumerate(sira)}
                gecerli = gecerli and all(poz[u] < poz[v]
                                          for u, v in k)
        ok += (dk == gd == (dd is not None)) and gecerli
    print(f"Test 8 topolojik siralama: {ok}/{top}")


def test_9_dag_ve_iki_renk():
    """DAG'da en kisa yol = BF (negatif kenar serbest); 2-renk
    brute force ile karsilastirilir."""
    rng, ok, top, ok2 = random.Random(42), 0, 200, 0
    for _ in range(top):
        n = rng.randint(1, 10)
        k = [(u, v, rng.randint(-3, 9)) for u in range(n)
             for v in range(u + 1, n)
             if rng.random() < 0.35]
        s = rng.randrange(n)
        ok += (dag_en_kisa(n, komsu(n, k), s)
               == bellman_ford(n, k, s)[0])
    for _ in range(top):
        n = rng.randint(1, 9)
        k = [(u, v) for u in range(n) for v in range(u + 1, n)
             if rng.random() < 0.3]
        adj = [[] for _ in range(n)]
        for u, v in k:
            adj[u].append(v)
            adj[v].append(u)
        beklenen = any(all(c[u] != c[v] for u, v in k)
                       for c in itertools.product((0, 1), repeat=n))
        ok2 += iki_renkli(n, adj)[0] == beklenen
    print(f"Test 9 DAG en kisa yol: {ok}/{top}; "
          f"iki renkli: {ok2}/{top}")


if __name__ == "__main__":
    test_1_negatifsiz()
    test_2_negatif()
    test_3_bfs()
    test_4_mst()
    test_5_sinir()
    test_6_scc()
    test_7_kopru_eklem()
    test_8_topo()
    test_9_dag_ve_iki_renk()
