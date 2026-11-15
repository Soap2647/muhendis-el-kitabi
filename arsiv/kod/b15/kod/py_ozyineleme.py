import sys


def derin(n):
    return 0 if n == 0 else 1 + derin(n - 1)


def topla(n, birikim=0):
    if n == 0:
        return birikim
    return topla(n - 1, birikim + n)


def en_buyuk_derin():
    lo, hi = 1, 100000
    while lo < hi:
        orta = (lo + hi + 1) // 2
        try:
            derin(orta)
            lo = orta
        except RecursionError:
            hi = orta - 1
    return lo


if __name__ == "__main__":
    print("getrecursionlimit =", sys.getrecursionlimit())
    print("en buyuk derin(n) =", en_buyuk_derin())
    for n in (500, 5000):
        try:
            print("topla(%d) =" % n, topla(n))
        except RecursionError as hata:
            print("topla(%d): RecursionError: %s" % (n, hata))
