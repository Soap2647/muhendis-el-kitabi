# minimize.py: DFA minimizasyonu (tablo doldurma) ve doğrulama
import random
from itertools import product
from dfa import DFA


def erisilebilir(d):
    """q0'dan okunabilen durumlar (BFS)."""
    gor, kuyruk = {d.q0}, [d.q0]
    while kuyruk:
        q = kuyruk.pop(0)
        for c in d.Sigma:
            p = d.delta[(q, c)]
            if p not in gor:
                gor.add(p)
                kuyruk.append(p)
    return gor


def tablo_doldur(d):
    """ayrik[(p, q)] = True ise p ve q ayrışabilir (simetrik)."""
    Q = sorted(erisilebilir(d))
    ayrik = {}
    for i, p in enumerate(Q):          # 1. adım: kabul/red ayrımı
        for q in Q[:i]:
            ayrik[(q, p)] = ayrik[(p, q)] = (p in d.F) != (q in d.F)
    degisti = True                     # 2. adım: yayılım
    while degisti:
        degisti = False
        for i, p in enumerate(Q):
            for q in Q[:i]:
                if ayrik[(q, p)]:
                    continue
                for c in d.Sigma:
                    a, b = d.delta[(q, c)], d.delta[(p, c)]
                    if a != b and ayrik[(a, b)]:
                        ayrik[(q, p)] = ayrik[(p, q)] = True
                        degisti = True
                        break
    return Q, ayrik


def minimize(d):
    """Denk durumları tek temsilciye indirir."""
    Q, ayrik = tablo_doldur(d)
    temsil = {}
    for q in Q:
        temsil[q] = q
        for p in Q[:Q.index(q)]:
            if not ayrik[(p, q)]:
                temsil[q] = temsil[p]
                break
    rep = sorted(set(temsil.values()))
    delta = {(t, c): temsil[d.delta[(t, c)]]
             for t in rep for c in d.Sigma}
    F = {t for t in rep if t in d.F}
    return DFA(rep, d.Sigma, delta, temsil[d.q0], F)


def _son(d, q, w):
    for c in w:
        q = d.delta[(q, c)]
    return q


def imza_sayisi(d, L):
    """|w| <= L dizgilerin kabul vektörü: ayrık sınıf sayısı."""
    dizgiler = ["".join(t) for k in range(L + 1)
                for t in product(sorted(d.Sigma), repeat=k)]
    imzalar = set()
    for q in erisilebilir(d):
        imzalar.add(tuple(_son(d, q, w) in d.F for w in dizgiler))
    return len(imzalar)


def parite_dfa():
    """a-paritesi x b-paritesi: 4 durum; minimal olan 2."""
    delta = {}
    for x in (0, 1):
        for y in (0, 1):
            delta[((x, y), "a")] = (1 - x, y)
            delta[((x, y), "b")] = (x, 1 - y)
    Q = [(x, y) for x in (0, 1) for y in (0, 1)]
    return DFA(Q, "ab", delta, (0, 0), {(0, 0), (0, 1)})


def rastgele_dfa(rng, n, sigma="ab"):
    delta = {(q, c): rng.randrange(n)
             for q in range(n) for c in sigma}
    F = {q for q in range(n) if rng.random() < 0.4} or {0}
    return DFA(range(n), sigma, delta, 0, F)


def dogrula(seed=36, n_dfa=300):
    rng = random.Random(seed)
    for _ in range(n_dfa):
        n = rng.randint(2, 9)
        d = rastgele_dfa(rng, n)
        m = minimize(d)
        # Moore: n durumlu DFA'da |w| <= n-2 yeter; n-1 ile güvenli.
        assert len(m.Q) == imza_sayisi(d, max(n - 1, 1)), n
        for uz in range(9):            # aynı dili tanımalı
            for t in product("ab", repeat=uz):
                w = "".join(t)
                assert d.kabul(w) == m.kabul(w), w
    return n_dfa


if __name__ == "__main__":
    d = parite_dfa()
    m = minimize(d)
    print("ön durum:", len(d.Q), " minimal:", len(m.Q))
    Q, ayrik = tablo_doldur(d)
    for i, p in enumerate(Q):
        for q in Q[:i]:
            print(q, p, "AYRIK" if ayrik[(q, p)] else "denk")
    print("dogrulanan DFA:", dogrula())
