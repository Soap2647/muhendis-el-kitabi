def ikili_say(n, x, sayac):
    """Bilinen n uzunluklu 3*i dizisinde x'in ilk konumu (ikili)."""
    lo, hi = 0, n
    while lo < hi:
        sayac[0] += 1
        orta = lo + (hi - lo) // 2
        if 3 * orta < x:
            lo = orta + 1
        else:
            hi = orta
    return lo


def ustel_ara(oku, x, sayac):
    """oku(i): sonsuz artan dizinin i. elemanı. x'in ilk konumu."""
    sinir = 1
    while oku(sinir, sayac) < x:
        sinir *= 2
    lo, hi = sinir // 2, sinir
    while lo < hi:
        orta = lo + (hi - lo) // 2
        if oku(orta, sayac) < x:
            lo = orta + 1
        else:
            hi = orta
    return lo


def sonsuz_dizi(i, sayac):
    """0, 3, 6, ... dizisinin i. elemanı; erişimler sayılır."""
    sayac[0] += 1
    return 3 * i


if __name__ == "__main__":
    print("konum | ustel adim | ikili adim (n = 2^21)")
    for p in [0, 1, 2, 10, 1000, 10**6]:
        x = 3 * p
        s1, s2 = [0], [0]
        k1 = ustel_ara(sonsuz_dizi, x, s1)
        k2 = ikili_say(2**21, x, s2)
        assert k1 == p == k2
        print("%5d | %10d | %10d" % (p, s1[0], s2[0]))
