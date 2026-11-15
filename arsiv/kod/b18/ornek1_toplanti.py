# ornek1_toplanti.py: en fazla toplanti (activity selection).
# Bitis zamanina gore sirala; baslangici son bitisten once olani
# atla.
import random


def en_fazla_toplanti(t):
    secilen, son = [], float("-inf")
    for s, e in sorted(t, key=lambda x: x[1]):
        if s >= son:
            secilen.append((s, e))
            son = e
    return secilen


def kaba(t):
    # tum altkumeler; en buyuk uyumlu olanin boyutu ve kumesi
    n, en_iyi, kume = len(t), 0, []
    for maske in range(1 << n):
        sec = sorted(t[i] for i in range(n) if maske >> i & 1)
        if all(sec[i + 1][0] >= sec[i][1]
               for i in range(len(sec) - 1)):
            if len(sec) > en_iyi:
                en_iyi, kume = len(sec), sec
    return en_iyi, kume


def main():
    t = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10),
         (8, 11)]
    print("toplantilar:", t[:4])
    print("            ", t[4:])
    son = float("-inf")
    for s, e in sorted(t, key=lambda x: x[1]):
        karar = "secildi" if s >= son else "cakisiyor"
        print("  (%d,%2d) son=%5s -> %s" % (s, e, son, karar))
        if s >= son:
            son = e
    print("secilen    :", en_fazla_toplanti(t))
    print("kaba kuvvet:", kaba(t)[0])
    rnd = random.Random(42)
    hata = ihlal = 0
    for _ in range(300):
        n = rnd.randint(1, 9)
        a = []
        for _ in range(n):
            s = rnd.randint(0, 15)
            a.append((s, s + rnd.randint(1, 6)))
        g = en_fazla_toplanti(a)
        boyut, kume = kaba(a)
        if len(g) != boyut:
            hata += 1
        # onde kalma: k. bitis, optimum kumesinin k. bitisinden once
        # ya da ona esit olmali
        ge = sorted(e for _, e in g)
        oe = sorted(e for _, e in kume)
        if any(x > y for x, y in zip(ge, oe)):
            ihlal += 1
    print("300 rastgele ornek, optimumdan farkli:", hata)
    print("300 rastgele ornek, onde kalma ihlali:", ihlal)


if __name__ == "__main__":
    main()
