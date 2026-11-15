"""MC/DC denetçisi: karar (A and B) or C için test kümesini sınar.

Bir koşulun MC/DC kapsamı: o koşulu yalnız değiştiren ve kararın
sonucunu da değiştiren bir test çifti kümede bulunmalıdır.
"""
from itertools import combinations, product

KOSUL_ADLARI = ["A", "B", "C"]


def karar(a, b, c):
    return (a and b) or c


def ac(metin):
    """'TTF' -> (True, True, False)"""
    return tuple(ch == "T" for ch in metin)


def etiket(v):
    return "".join("T" if x else "F" for x in v)


def bagimsiz_cift(kume, i):
    """Koşul i için bağımsız etkisi gösteren bir (x, y) çifti."""
    for x, y in combinations(kume, 2):
        fark = [k for k in range(3) if x[k] != y[k]]
        if fark == [i] and karar(*x) != karar(*y):
            return x, y
    return None


def rapor(kume):
    print("test kümesi:", " ".join(etiket(v) for v in kume))
    tamam = True
    for i, ad in enumerate(KOSUL_ADLARI):
        cift = bagimsiz_cift(kume, i)
        if cift is None:
            tamam = False
            print("  %s: KAPSANMADI" % ad)
        else:
            x, y = cift
            print("  %s: %s -> %s  (sonuç %s -> %s)" % (
                ad, etiket(x), etiket(y),
                "T" if karar(*x) else "F",
                "T" if karar(*y) else "F"))
    print("  MC/DC:", "TAM" if tamam else "EKSİK")
    return tamam


def en_kucuk_kumeler(boyut_ust=8):
    """Tüm 8 girdi üzerinde MC/DC sağlayan en küçük kümeleri bul."""
    evren = list(product([True, False], repeat=3))
    for n in range(1, boyut_ust + 1):
        bulunan = []
        for kume in combinations(evren, n):
            if all(bagimsiz_cift(kume, i) for i in range(3)):
                bulunan.append(kume)
        if bulunan:
            return n, bulunan
    return None, []


if __name__ == "__main__":
    print("El ile türetilen küme:")
    el = [ac("TTF"), ac("FTF"), ac("TFF"), ac("TFT")]
    rapor(el)
    print()
    print("Eksik küme (TFT çıkarıldı):")
    rapor(el[:3])
    print()
    n, kumeler = en_kucuk_kumeler()
    print("En küçük MC/DC kümesi boyutu:", n)
    print("Bu boyutta bulunan küme sayısı:", len(kumeler))
    for k in kumeler[:3]:
        print("  ", " ".join(etiket(v) for v in k))
