# nfa.py: ε-NFA, ε-kapanış ve alt küme yapısı (NFA -> DFA)
import random
from itertools import product

EPS = ""                               # ε: boş harf


class NFA:
    def __init__(self, Q, Sigma, delta, q0, F):
        self.Q, self.Sigma = set(Q), set(Sigma)
        self.delta = {k: set(v) for k, v in delta.items()}
        self.q0, self.F = q0, set(F)

    def ileri(self, S, c):
        """S'den c harfiyle gidilen durumlar (kapanışsız)."""
        out = set()
        for q in S:
            out |= self.delta.get((q, c), set())
        return out

    def eps_kapanis(self, S):
        """S'ten yalnız ε-kenarlarla ulaşılanlar (S dahil)."""
        yigin, kap = list(S), set(S)
        while yigin:
            q = yigin.pop()
            for p in self.delta.get((q, EPS), set()):
                if p not in kap:
                    kap.add(p)
                    yigin.append(p)
        return frozenset(kap)

    def kabul(self, w):
        S = self.eps_kapanis({self.q0})
        for c in w:
            S = self.eps_kapanis(self.ileri(S, c))
        return bool(S & self.F)


def alt_kume(nfa):
    """DFA durumları NFA durum kümeleridir."""
    bas = nfa.eps_kapanis({nfa.q0})
    durumlar, yigin, delta = {bas}, [bas], {}
    while yigin:
        S = yigin.pop()
        for c in sorted(nfa.Sigma):
            T = nfa.eps_kapanis(nfa.ileri(S, c))   # boş olabilir
            delta[(S, c)] = T
            if T not in durumlar:
                durumlar.add(T)
                yigin.append(T)
    F = {S for S in durumlar if S & nfa.F}
    return bas, durumlar, delta, F


def ad(S):
    return "{" + ",".join(str(q) for q in sorted(S)) + "}"


def tablo(nfa):
    """Alt küme tablosu: her DFA durumu ve geçişleri."""
    bas, Q, delta, F = alt_kume(nfa)
    for S in sorted(Q, key=lambda s: (len(s), sorted(s))):
        satir = [ad(S)]
        for c in sorted(nfa.Sigma):
            satir.append("%s->%s" % (c, ad(delta[(S, c)])))
        satir.append("kabul" if S in F else "")
        print("  ".join(satir).rstrip())


def abb_nfa():
    """(a|b)*abb icin elle kurulmus NFA (ε yok)."""
    delta = {(0, "a"): {0, 1}, (0, "b"): {0}, (1, "b"): {2},
             (2, "b"): {3}}
    return NFA(range(4), "ab", delta, 0, {3})


def rastgele_nfa(rng, n, sigma="ab"):
    delta = {}
    for q in range(n):
        for c in sigma:
            for p in range(n):
                if rng.random() < 0.3:
                    delta.setdefault((q, c), set()).add(p)
        for p in range(n):
            if rng.random() < 0.1:
                delta.setdefault((q, EPS), set()).add(p)
    F = {q for q in range(n) if rng.random() < 0.3} or {n - 1}
    return NFA(range(n), sigma, delta, 0, F)


def dogrula(seed=36, n_nfa=200):
    """Rastgele NFA'lar ve kısa dizgilerle eşdeğerlik testi."""
    rng = random.Random(seed)
    sinanan = 0
    for _ in range(n_nfa):
        nfa = rastgele_nfa(rng, rng.randint(2, 6))
        bas, Q, delta, F = alt_kume(nfa)
        for uz in range(9):
            for t in product("ab", repeat=uz):
                w, S = "".join(t), bas
                for c in w:
                    S = delta[(S, c)]
                assert (S in F) == nfa.kabul(w), w
                sinanan += 1
    return sinanan


def ailesi_n(n):
    """Sondan n. harf 'a' olan dizgiler: NFA n+1, DFA 2^n."""
    delta = {(0, "a"): {0, 1}, (0, "b"): {0}}
    for i in range(1, n):
        delta[(i, "a")] = {i + 1}
        delta[(i, "b")] = {i + 1}
    return NFA(range(n + 1), "ab", delta, 0, {n})


if __name__ == "__main__":
    tablo(abb_nfa())
    print("sinanan dizge:", dogrula())
    for n in range(1, 9):
        Q = alt_kume(ailesi_n(n))[1]
        print("n=%d NFA=%d DFA=%d" % (n, n + 1, len(Q)))
