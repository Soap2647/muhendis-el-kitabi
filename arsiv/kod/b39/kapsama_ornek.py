def etiket(x):
    s = "sifir"
    if x is not None and x > 0:
        s = "pozitif"
    return s


def ortalama(xs):
    if not xs:
        return 0.0
    return sum(xs) // len(xs)   # HATA: tam bölme, ondalık kaybolur
