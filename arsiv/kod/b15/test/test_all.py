import sys, random, itertools
sys.path.insert(0, "C:/Users/merty/AppData/Local/Temp/b15/kod")
from geri_izleme import (altkumeler, tekrarsiz_permutasyonlar,
                         kombinasyonlar, kombinasyon_toplami)
from vezir import budamali_say, budamasiz_say, cozumler, guvenli_son
from sudoku import ayristir, coz, gecerli, PULMACALAR
from ayristirici import hesapla, AyristiHatasi
from labirent import kose_yol_sayisi, yol_bul, HARITA

random.seed(42)
# 1 altkume
for n in range(0, 8):
    a = list(range(1, n + 1))
    s = altkumeler(a)
    ref = [list(c) for k in range(n + 1) for c in itertools.combinations(a, k)]
    assert sorted(map(tuple, s)) == sorted(map(tuple, ref)), n
    assert len(s) == 2 ** n
# altkume: bos liste
assert altkumeler([]) == [[]]
print("altkume ok")
# 2 tekrarsiz permutasyon
for _ in range(300):
    n = random.randint(0, 6)
    a = [random.randint(0, 3) for _ in range(n)]
    s = tekrarsiz_permutasyonlar(a)
    ref = sorted(set(itertools.permutations(a)))
    assert sorted(map(tuple, s)) == ref, a
    assert len(s) == len(set(map(tuple, s)))
assert tekrarsiz_permutasyonlar([]) == [[]]
assert len(tekrarsiz_permutasyonlar([1, 1, 2, 2])) == 6
assert len(tekrarsiz_permutasyonlar([1, 2, 3])) == 6
print("permutasyon ok")
# 3 kombinasyon
for n in range(0, 8):
    for k in range(0, n + 2):
        s = kombinasyonlar(n, k)
        ref = [list(c) for c in itertools.combinations(range(1, n + 1), k)]
        assert s == ref, (n, k)
print("kombinasyon ok")
# 4 kombinasyon toplami: referans = tekrarli kombinasyonlar
def ref_toplam(adaylar, hedef):
    a = sorted(adaylar)
    out = []
    for k in range(1, hedef // a[0] + 1):
        for c in itertools.combinations_with_replacement(a, k):
            if sum(c) == hedef:
                out.append(list(c))
    if hedef == 0:
        out.append([])
    return out
for _ in range(120):
    m = random.randint(1, 5)
    adaylar = random.sample(range(1, 9), m)
    hedef = random.randint(0, 14)
    if hedef == 0:
        continue
    r1, d1 = kombinasyon_toplami(adaylar, hedef, True)
    r2, d2 = kombinasyon_toplami(adaylar, hedef, False)
    ref = ref_toplam(adaylar, hedef)
    assert sorted(map(tuple, r1)) == sorted(map(tuple, ref)), (adaylar, hedef)
    assert sorted(map(tuple, r2)) == sorted(map(tuple, ref)), (adaylar, hedef)
    assert d1 <= d2
print("kombinasyon toplami ok")
print("kt ornek", kombinasyon_toplami([2, 3, 6, 7], 7))
# 5 vezir
for n in range(1, 9):
    c, d = budamali_say(n)
    c2, d2 = budamasiz_say(n)
    assert c == c2, n
    assert all(guvenli_son(s) for s in cozumler(n)) if n > 0 else True
    assert len(cozumler(n)) == c
print("vezir ok", [budamali_say(n)[0] for n in range(1, 9)])
# 6 sudoku: gecerli cozum + ayni cozum iki modda
for ad, m in PULMACALAR.items():
    t1 = ayristir(m); c1, d1, a1 = coz(t1, False, 10**7)
    t2 = ayristir(m); c2, d2, a2 = coz(t2, True, 10**7)
    assert gecerli(c1, m) and gecerli(c2, m)
    assert c1 == c2   # tek cozum varsayimi (bulmacalar tek cozumlu)
print("sudoku ok")
# 7 parser: Python eval ile karsilastir (bolme yok)
def rastgele(d):
    if d == 0 or random.random() < 0.3:
        return str(random.randint(0, 20))
    r = random.random()
    if r < 0.15:
        return "-" + rastgele(d - 1)
    if r < 0.4:
        return "(" + rastgele(d - 1) + ")"
    op = random.choice("+-*")
    return rastgele(d - 1) + " " + op + " " + rastgele(d - 1)
for _ in range(2000):
    e = rastgele(5)
    assert hesapla(e) == eval(e), e
for e in ["7 / 2", "1 / 4 * 4"]:
    assert hesapla(e) == eval(e.replace("/", "/"))
for bad in ["(2 + 3", "", "8 / (4 - 4)", "2 $ 3", "2 3", ")"]:
    try:
        hesapla(bad)
        raise SystemExit("hata bekleniyordu: " + bad)
    except AyristiHatasi:
        pass
print("parser ok")
# parser max derinlik
def maks_derinlik():
    lo, hi = 1, 2000
    while lo < hi:
        orta = (lo + hi + 1) // 2
        try:
            hesapla("(" * orta + "1" + ")" * orta)
            lo = orta
        except RecursionError:
            hi = orta - 1
    return lo
print("max parantez derinligi:", maks_derinlik())
# 8 labirent: yol gecerli mi
yol = yol_bul(HARITA)
for (a, b), (c, d) in zip(yol, yol[1:]):
    assert abs(a - c) + abs(b - d) == 1 and HARITA[c][d] != "#"
assert yol[0] == (0, 0) and yol[-1] == (4, 6)
print("labirent ok")
print("tum testler gecti")
