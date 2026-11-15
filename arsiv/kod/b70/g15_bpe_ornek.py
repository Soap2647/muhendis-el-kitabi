# -*- coding: utf-8 -*-
"""
Bölüm 70 - Elle izlenen BPE örneği: 4 kelimelik derlem, üç birleştirme
adımı.
"""

from collections import Counter
from bpe_sifirdan import egit, on_isle

metin = "kod kodu koda kod"
frek = Counter(on_isle(metin))
print("ön işleme parçaları:", dict(frek))
parca = {w: list(w) for w in frek}


def ciftler(parca):
    c = Counter()
    for w, s in parca.items():
        for a, b in zip(s, s[1:]):
            c[(a, b)] += frek[w]
    return c


for adim in range(1, 4):
    c = ciftler(parca)
    en = max(c, key=lambda p: (c[p], p))
    print(
        "adım %d: en sık çift %r sayı=%d | sayımlar: %s"
        % (
            adim,
            en,
            c[en],
            sorted(
                ((k, v) for k, v in c.items()),
                key=lambda t: (-t[1], t[0]),
            )[:5],
        )
    )
    yeni = en[0] + en[1]
    for w, s in parca.items():
        t, i = [], 0
        while i < len(s):
            if i + 1 < len(s) and (s[i], s[i + 1]) == en:
                t.append(yeni)
                i += 2
            else:
                t.append(s[i])
                i += 1
        parca[w] = t
    print("   durum:", {w: s for w, s in parca.items()})
print("egit(…,3) =", egit(metin, 3))
