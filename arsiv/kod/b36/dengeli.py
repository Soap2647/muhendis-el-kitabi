# Yığınlı tanıyıcı (PDA mantığı): üç tür parantez dengesi.
from itertools import product
import random

KARSI = {")": "(", "]": "[", "}": "{"}


def yigin_tani(s):
    """Kabul/red ve her adımda (harf, yığın) izi döndürür."""
    yigin, iz = [], []
    for c in s:
        if c in "([{":
            yigin.append(c)
        elif c in KARSI:
            if not yigin or yigin[-1] != KARSI[c]:
                iz.append((c, "".join(yigin) + " <- HATA"))
                return False, iz
            yigin.pop()
        else:
            raise ValueError("bilinmeyen harf %r" % c)
        iz.append((c, "".join(yigin)))
    return (not yigin), iz


def yeniden_yaz(s):
    """Bağımsız oracle: (), [], {} çiftlerini tekrar tekrar sil."""
    while True:
        t = s.replace("()", "").replace("[]", "").replace("{}", "")
        if t == s:
            return s == ""
        s = t


def dogrula(seed=36, n_rastgele=5000):
    sinanan = 0
    for n in range(0, 7):
        for t in product("()[]{}", repeat=n):
            w = "".join(t)
            assert yigin_tani(w)[0] == yeniden_yaz(w), w
            sinanan += 1
    rng = random.Random(seed)
    for _ in range(n_rastgele):
        n = rng.randint(0, 30)
        w = "".join(rng.choice("()[]{}") for _ in range(n))
        assert yigin_tani(w)[0] == yeniden_yaz(w), w
        sinanan += 1
    return sinanan


if __name__ == "__main__":
    for w in ["{[()]}", "([)]", "((]"]:
        ok, iz = yigin_tani(w)
        print(w, "kabul" if ok else "red")
        for harf, yigin in iz:
            print("   %s  yığın=%r" % (harf, yigin))
    print("sinanan:", dogrula())
