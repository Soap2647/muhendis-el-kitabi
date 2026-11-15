import sys, random, itertools, math
sys.path.insert(0, "C:/Users/merty/AppData/Local/Temp/b15/kod")
from ornek4 import ifadeler
from ornek2 import parantezler
from ornek3 import var_mi, IZGARA
from ornek1 import us
from json_derinlik import derinlik, anahtar_say
random.seed(42)
for _ in range(400):
    n = random.randint(1, 6)
    rakam = "".join(random.choice("0123456789") for _ in range(n))
    hedef = random.randint(-20, 60)
    # brute force: her aralik icin +,-,*, ve bosluk (birlestirme) yok:
    # tum ayrimlar ve operator dizileri
    bulunan = set()
    for ayrim in range(2 ** (n - 1)):
        parcalar = [rakam[0]]
        for k in range(1, n):
            if ayrim >> (k - 1) & 1:
                parcalar.append(rakam[k])
            else:
                parcalar[-1] += rakam[k]
        if any(len(p) > 1 and p[0] == "0" for p in parcalar):
            continue
        for ops in itertools.product("+-*", repeat=len(parcalar) - 1):
            s = parcalar[0]
            for o, p in zip(ops, parcalar[1:]):
                s += o + p
            if eval(s) == hedef:
                bulunan.add(s)
    got = set(ifadeler(rakam, hedef))
    assert got == bulunan, (rakam, hedef, got ^ bulunan)
print("ornek4 brute-force ok")
for n in range(0, 8):
    assert len(parantezler(n)) == math.comb(2 * n, n) // (n + 1)
print("catalan ok")
for k in range(0, 20):
    assert us(3, k) == 3 ** k and us(2, k) == 2 ** k
print("us ok")
assert var_mi(IZGARA, "ABCCED") and not var_mi(IZGARA, "ABCB")
print("kelime ok")
v = {"a": []}
assert derinlik([]) == 1 and derinlik(5) == 0 and derinlik({}) == 1
print("json ok")
