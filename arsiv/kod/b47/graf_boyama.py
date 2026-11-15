# -*- coding: utf-8 -*-
# graf_boyama.py - derece, Konigsberg, tac graf ve acgozlu boyama.


def derece(n, kenarlar):
    d = [0] * n
    for u, v in kenarlar:
        d[u] += 1
        d[v] += 1
    return d


def tac_graf(m):
    """i ~ m+j, i != j: iki parcali, boyama sayisi 2."""
    kom = [[] for _ in range(2 * m)]
    for i in range(m):
        for j in range(m):
            if i != j:
                kom[i].append(m + j)
                kom[m + j].append(i)
    return kom


def acgozlu_boya(n, kom, sira):
    renk = [-1] * n
    for u in sira:
        yasak = {renk[v] for v in kom[u] if renk[v] != -1}
        c = 0
        while c in yasak:
            c += 1
        renk[u] = c
    return renk


if __name__ == "__main__":
    kon = [(0, 1), (0, 1), (0, 2), (0, 2), (0, 3), (1, 3), (2, 3)]
    print("Konigsberg dereceleri:", derece(4, kon))
    m = 3
    kom = tac_graf(m)
    kotu = [0, 3, 1, 4, 2, 5]
    iyi = [0, 1, 2, 3, 4, 5]
    rk = acgozlu_boya(2 * m, kom, kotu)
    ri = acgozlu_boya(2 * m, kom, iyi)
    print("kotu sira:", rk, "->", max(rk) + 1, "renk")
    print("iyi sira: ", ri, "->", max(ri) + 1, "renk")
