# etkinlik_kurallar.py: etkinlik secimi icin dort acgozlu kural,
# kaba kuvvet referansi ve karsi ornekler. Aralik [s, e) yari acik.
import random


def uygun(s, son):
    return s >= son


def bitis_sirali(a):
    secilen, son = [], float("-inf")
    for s, e in sorted(a, key=lambda x: x[1]):
        if uygun(s, son):
            secilen.append((s, e))
            son = e
    return secilen


def baslangic_sirali(a):
    secilen, son = [], float("-inf")
    for s, e in sorted(a, key=lambda x: x[0]):
        if uygun(s, son):
            secilen.append((s, e))
            son = e
    return secilen


def cakisir(x, y):
    return x[0] < y[1] and y[0] < x[1]


def en_kisa_once(a):
    secilen = []
    for x in sorted(a, key=lambda x: x[1] - x[0]):
        if not any(cakisir(x, y) for y in secilen):
            secilen.append(x)
    return sorted(secilen)


def en_az_cakisma(a):
    kalan, secilen = list(a), []
    while kalan:
        def cakisma_sayisi(x):
            return sum(1 for y in kalan
                       if y is not x and cakisir(x, y))
        x = min(kalan, key=cakisma_sayisi)
        secilen.append(x)
        kalan = [y for y in kalan if not cakisir(x, y)]
    return sorted(secilen)


def kaba(a):
    n, en_iyi = len(a), 0
    for maske in range(1 << n):
        sec = sorted(a[i] for i in range(n) if maske >> i & 1)
        if all(uygun(sec[i + 1][0], sec[i][1])
               for i in range(len(sec) - 1)):
            en_iyi = max(en_iyi, len(sec))
    return en_iyi


def rastgele(rnd):
    n = rnd.randint(1, 8)
    a = []
    for _ in range(n):
        s = rnd.randint(0, 14)
        a.append((s, s + rnd.randint(1, 5)))
    return a


def yazdir(liste):
    for i in range(0, len(liste), 4):
        print("   ", liste[i:i + 4])


def kucult(a, hatali):
    changed = True
    while changed:
        changed = False
        for i in range(len(a)):
            b = a[:i] + a[i + 1:]
            if hatali(b):
                a, changed = b, True
                break
    return a


def main():
    kurallar = [("bitis", bitis_sirali),
                ("baslangic", baslangic_sirali),
                ("en kisa", en_kisa_once),
                ("az cakisma", en_az_cakisma)]
    for el in ([(0, 10), (1, 2), (3, 4)], [(0, 3), (2, 4), (3, 5)]):
        print("elle ornek:", el, "optimum", kaba(el))
        for ad, f in kurallar:
            print("   %-11s -> %s" % (ad, f(el)))
    rnd = random.Random(42)
    testler = [rastgele(rnd) for _ in range(500)]
    for ad, f in kurallar:
        hata, ilk = 0, None
        for a in testler:
            if len(f(a)) != kaba(a):
                hata += 1
                if ilk is None:
                    ilk = a
        print("%-11s hata: %3d / 500" % (ad, hata))
        if ilk is not None:
            print("   ilk karsi ornek (n=%d):" % len(ilk))
            yazdir(ilk)
            print("   secilen", len(f(ilk)), "optimum", kaba(ilk))
    # az cakisma icin: 500 ornekte hata yok; genis arama (tohum 11)
    rnd = random.Random(11)
    for _ in range(200000):
        n = rnd.randint(3, 12)
        a = []
        for _ in range(n):
            s = rnd.randint(0, 25)
            a.append((s, s + rnd.randint(1, 9)))
        if len(en_az_cakisma(a)) != len(bitis_sirali(a)):
            break
    print("az cakisma, genis arama ilk karsi ornek (n=%d):" % len(a))
    k = kucult(a, lambda x: len(en_az_cakisma(x)) != kaba(x))
    print("   kucultulmus (n=%d):" % len(k))
    yazdir(sorted(k))
    print("   secilen", len(en_az_cakisma(k)), "optimum", kaba(k))


if __name__ == "__main__":
    main()
