def ters_sayisi(a):
    """Ters cevrim (i < j ve a[i] > a[j]) sayisi, merge sort ile."""
    def ayir(v):
        if len(v) < 2:
            return v, 0
        orta = len(v) // 2
        sol, c1 = ayir(v[:orta])
        sag, c2 = ayir(v[orta:])
        birlesik = []
        i = j = c = 0
        while i < len(sol) and j < len(sag):
            if sol[i] <= sag[j]:
                birlesik.append(sol[i])
                i += 1
            else:
                birlesik.append(sag[j])
                j += 1
                c += len(sol) - i
        birlesik += sol[i:] + sag[j:]
        return birlesik, c1 + c2 + c
    return ayir(list(a))[1]


if __name__ == "__main__":
    print(ters_sayisi([2, 4, 1, 3, 5]))
    print(ters_sayisi([3, 1, 2]))
    print(ters_sayisi([1, 2, 3, 4]))
    print(ters_sayisi([4, 3, 2, 1]))
