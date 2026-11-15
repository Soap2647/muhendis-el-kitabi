"""İkili arama (Bölüm 14). Biri hatalı, biri doğru iki sürüm."""


def ikili_arama_hatali(xs, hedef):
    """HATA: döngü koşulu '<' (olmalı '<='). Tek elemanlı dizide
    ya da aranan değer son adayken döngü hiç ona bakmaz."""
    lo, hi = 0, len(xs) - 1
    while lo < hi:
        orta = (lo + hi) // 2
        if xs[orta] == hedef:
            return orta
        if xs[orta] < hedef:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1


def ikili_arama(xs, hedef):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        orta = (lo + hi) // 2
        if xs[orta] == hedef:
            return orta
        if xs[orta] < hedef:
            lo = orta + 1
        else:
            hi = orta - 1
    return -1
