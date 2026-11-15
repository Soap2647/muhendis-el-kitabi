# fib_olcum.py: naif, memo ve tablo; cagri sayilari
import functools
import sys

sayac = {"naif": 0, "memo": 0}


def fib_naif(n):
    sayac["naif"] += 1
    if n < 2:
        return n
    return fib_naif(n - 1) + fib_naif(n - 2)


@functools.cache
def fib_memo(n):
    sayac["memo"] += 1           # yalnizca gercek hesapta artar
    if n < 2:
        return n
    return fib_memo(n - 1) + fib_memo(n - 2)


def fib_tablo(n):
    t = [0, 1] + [0] * max(0, n - 1)
    for i in range(2, n + 1):
        t[i] = t[i - 1] + t[i - 2]
    return t[n]


def main():
    print("Python", sys.version.split()[0])
    for n in (10, 20, 30):
        sayac["naif"] = sayac["memo"] = 0
        fib_memo.cache_clear()
        a = fib_naif(n)
        b = fib_memo(n)
        c = fib_tablo(n)
        assert a == b == c
        print(f"n={n:2d} fib={a:>7d} naif_cagri={sayac['naif']:>8d}"
              f" memo_hesap={sayac['memo']:>3d}")
    # Yigin derinligi: memo n kadar ic ice cagri yapar
    fib_memo.cache_clear()
    for n in (900, 1200):
        try:
            fib_memo(n)
            print(f"memo n={n}: tamam")
        except RecursionError:
            print(f"memo n={n}: RecursionError")
        fib_memo.cache_clear()
    print("tablo n=1200 basamak:", len(str(fib_tablo(1200))))
    print("recursion limit:", sys.getrecursionlimit())


if __name__ == "__main__":
    main()
