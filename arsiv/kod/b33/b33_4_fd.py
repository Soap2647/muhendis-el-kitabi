# -*- coding: utf-8 -*-
# b33_4_fd.py: FD kapanışı, aday anahtarlar, BCNF ihlali
from itertools import combinations


def fd(sol, sag):
    """'AB' -> 'C' biçiminde bir bağımlılık."""
    return (frozenset(sol), frozenset(sag))


def kapanis(X, F):
    """X+: X'ten Armstrong kurallarıyla türeyenler."""
    sonuc = set(X)
    degisti = True
    while degisti:
        degisti = False
        for sol, sag in F:
            if sol <= sonuc and not sag <= sonuc:
                sonuc |= sag
                degisti = True
    return frozenset(sonuc)


def altkumeler(R):
    R = sorted(R)
    for k in range(len(R) + 1):
        for c in combinations(R, k):
            yield frozenset(c)


def aday_anahtarlar(R, F):
    """Süper anahtarlardan kendisinden küçüğü olmayanlar."""
    R = frozenset(R)
    sup = [X for X in altkumeler(R) if kapanis(X, F) == R]
    return [X for X in sup if not any(Y < X for Y in sup)]


def bcnf_ihlalleri(R, F):
    """X+, R'nin tamamı değilse ve X'in dışına taşıyorsa ihlal."""
    R = frozenset(R)
    ihlal = []
    for X in altkumeler(R):
        Xp = kapanis(X, F) & R
        if Xp - X and Xp != R:
            ihlal.append((sorted(X), sorted(Xp - X)))
    return ihlal


if __name__ == "__main__":
    R = "ABCDEG"
    F = [fd("AB", "C"), fd("C", "A"), fd("BC", "D"),
         fd("ACD", "B"), fd("D", "EG"), fd("BE", "C"),
         fd("CG", "BD"), fd("CE", "AG")]
    print("{B,D}+ =", "".join(sorted(kapanis("BD", F))))
    print("{A}+   =", "".join(sorted(kapanis("A", F))))
    anah = aday_anahtarlar(R, F)
    print("aday anahtarlar:", ["".join(sorted(k)) for k in anah])
    ih = bcnf_ihlalleri(R, F)
    print("BCNF ihlal sayisi:", len(ih))
    print("ilk 3 ihlal:")
    for x in ih[:3]:
        print(" ", x)
