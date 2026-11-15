# FIRST ve FOLLOW kümeleri (sabit noktaya kadar).
EPS = "ε"
G = {
    "E":  [["T", "E'"]],
    "E'": [["+", "T", "E'"], [EPS]],
    "T":  [["F", "T'"]],
    "T'": [["*", "F", "T'"], [EPS]],
    "F":  [["(", "E", ")"], ["id"]],
}
BAS = "E"


def ilk_dizi(seq, first):
    """Bir sembol dizisinin FIRST kümesi (ε dahil olabilir)."""
    sonuc = set()
    for X in seq:
        if X == EPS:
            continue
        f = first[X] if X in G else {X}
        sonuc |= f - {EPS}
        if EPS not in f:
            return sonuc
    sonuc.add(EPS)                 # her sembol ε türetebiliyorsa
    return sonuc


def ilk_kumeleri(G):
    first = {A: set() for A in G}
    degisti = True
    while degisti:
        degisti = False
        for A, uretimler in G.items():
            for u in uretimler:
                yeni = ilk_dizi(u, first)
                if not yeni <= first[A]:
                    first[A] |= yeni
                    degisti = True
    return first


def takip_kumeleri(G, bas, first):
    follow = {A: set() for A in G}
    follow[bas].add("$")
    degisti = True
    while degisti:
        degisti = False
        for A, uretimler in G.items():
            for u in uretimler:
                for i, B in enumerate(u):
                    if B not in G:
                        continue
                    kalan = ilk_dizi(u[i + 1:], first)
                    yeni = follow[B] | (kalan - {EPS})
                    if EPS in kalan:
                        yeni |= follow[A]
                    if yeni != follow[B]:
                        follow[B] = yeni
                        degisti = True
    return follow


if __name__ == "__main__":
    first = ilk_kumeleri(G)
    follow = takip_kumeleri(G, BAS, first)
    for A in G:
        print("FIRST(%s) = %s" % (A, sorted(first[A])))
    for A in G:
        print("FOLLOW(%s) = %s" % (A, sorted(follow[A])))
