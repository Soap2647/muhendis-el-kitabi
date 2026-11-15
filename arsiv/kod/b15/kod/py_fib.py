import sys

cagri = 0


def fib(n):
    global cagri
    cagri += 1
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


if __name__ == "__main__":
    for n in (5, 10, 20, 25):
        cagri = 0
        sonuc = fib(n)
        print("fib(%2d) = %6d  cagri = %8d" % (n, sonuc, cagri))
    cagri = 0
    fib(30)
    print("fib(30) cagri =", cagri)
