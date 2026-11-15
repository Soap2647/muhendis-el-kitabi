# -*- coding: utf-8 -*-
"""FIRST, FOLLOW ve LL(1) tablosu (Bölüm 36 tanımları)."""
EPS = "eps"

def hesapla(gram, bas):
    # eps üretimini bos dizi olarak normallestir
    gram = {a: [[x for x in u if x != EPS] for u in us]
            for a, us in gram.items()}
    nt = set(gram)
    first = {n: set() for n in nt}
    def first_of(seq):
        out = set()
        for x in seq:
            if x not in nt:
                out.add(x); return out, False
            out |= first[x] - {EPS}
            if EPS not in first[x]:
                return out, False
        return out | {EPS}, True
    degisti = True
    while degisti:
        degisti = False
        for a, uretimler in gram.items():
            for u in uretimler:
                f, _ = first_of(u)
                if f - first[a]:
                    first[a] |= f; degisti = True
                bos = all(x in nt and EPS in first[x] for x in u)
                if bos and EPS not in first[a]:
                    first[a].add(EPS); degisti = True
    follow = {n: set() for n in nt}
    follow[bas].add("$")
    degisti = True
    while degisti:
        degisti = False
        for a, uretimler in gram.items():
            for u in uretimler:
                for i, x in enumerate(u):
                    if x not in nt: continue
                    f, eps = first_of(u[i+1:])
                    yeni = (f - {EPS}) | (follow[a] if eps else set())
                    if yeni - follow[x]:
                        follow[x] |= yeni; degisti = True
    tablo, cakisma = {}, []
    for a, uretimler in gram.items():
        for u in uretimler:
            f, eps = first_of(u)
            hedefler = (f - {EPS}) | (follow[a] if eps else set())
            for t in hedefler:
                if (a, t) in tablo:
                    cakisma.append((a, t, tablo[(a, t)], u))
                tablo[(a, t)] = u
    return first, follow, tablo, cakisma

def goster(baslik, gram, bas):
    first, follow, tablo, cak = hesapla(gram, bas)
    print("==", baslik)
    for n in gram:
        print(f"FIRST({n}) = {sorted(first[n])}  "
              f"FOLLOW({n}) = {sorted(follow[n])}")
    print("cakisma sayısi:", len(cak))
    for a, t, u1, u2 in cak:
        print(f"  ({a},{t}): {' '.join(u1)}  vs  {' '.join(u2)}")
    if not cak:
        for (a, t), u in sorted(tablo.items()):
            print(f"  M[{a},{t}] = {a} -> {' '.join(u)}")

sol = {"E": [["E", "+", "T"], ["T"]], "T": [["T", "*", "F"], ["F"]],
       "F": [["(", "E", ")"], ["id"]]}
duz = {"E": [["T", "Ep"]], "Ep": [["+", "T", "Ep"], [EPS]],
       "T": [["F", "Tp"]], "Tp": [["*", "F", "Tp"], [EPS]],
       "F": [["(", "E", ")"], ["id"]]}
if __name__ == "__main__":
    goster("solda ozyinelemeli (LL(1) DEGIL)", sol, "E")
    goster("sol ozyineleme kaldirilmis", duz, "E")
