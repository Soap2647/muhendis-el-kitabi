# bipartite.py - BFS ile iki renkli (2-renklendirme) kontrolu.
from collections import deque


def iki_renkli(n, adj):
    """adj: yonsuz komsuluk listesi. Donus: (True, renk) ya da
    (False, (u, v)): ayni renkli iki komsu (cakisan kenar)."""
    renk = [-1] * n
    for s in range(n):
        if renk[s] != -1:
            continue
        renk[s] = 0
        kuyruk = deque([s])
        while kuyruk:
            u = kuyruk.popleft()
            for v in adj[u]:
                if renk[v] == -1:
                    renk[v] = 1 - renk[u]    # komsu: karsit renk
                    kuyruk.append(v)
                elif renk[v] == renk[u]:
                    return False, (u, v)     # cakisma: tek dongu
    return True, renk


if __name__ == "__main__":
    def graf(n, kenar):
        adj = [[] for _ in range(n)]
        for u, v in kenar:
            adj[u].append(v)
            adj[v].append(u)
        return adj

    dort_dongu = graf(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    bes_dongu = graf(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
    print("C4 :", iki_renkli(4, dort_dongu))
    print("C5 :", iki_renkli(5, bes_dongu))
