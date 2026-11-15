# -*- coding: utf-8 -*-
"""Bölüm 70 - Çözümlü örnekler için el hesapları, kodla doğrulama:
(a) 4 belirteçlik derlemde bigram + Laplace ve perplexity;
(b) gömme tablosu = one-hot × matris (satır seçimi)."""

import math
from collections import Counter

# (a) Derlem: a b a c ; sözlük V = 3 (a, b, c)
derlem = ["a", "b", "a", "c"]
V = 3
bigram = Counter(zip(derlem, derlem[1:]))
baglam = Counter(derlem[:-1])
print("bigram sayımları:", dict(bigram))
print("bağlam sayımları:", dict(baglam))


def p_lap(sonraki, once):
    return (bigram[(once, sonraki)] + 1) / (baglam[once] + V)


cumle = ["a", "b", "a", "c"]
olasiliklar = [
    p_lap(cumle[i + 1], cumle[i]) for i in range(len(cumle) - 1)
]
print("P(b|a) =", p_lap("b", "a"), " P(a|b) =", p_lap("a", "b"))
print("P(c|a) =", p_lap("c", "a"), " P(a|a) =", p_lap("a", "a"))
print("adım olasılıkları:", olasiliklar)
ce = -sum(math.log2(p) for p in olasiliklar) / len(olasiliklar)
print("çapraz entropi (bit/belirteç) =", round(ce, 4))
print("perplexity = 2^H =", round(2**ce, 4))

# (b) Gömme: one-hot × W satır seçimi
W = [[0.2, -0.5], [1.0, 0.3], [-0.7, 0.9]]  # V=3, d=2
onehot = [0, 1, 0]  # 'b' belirteci
carpim = [
    sum(onehot[i] * W[i][j] for i in range(3)) for j in range(2)
]
print("one-hot x W =", carpim, " satır =", W[1])
