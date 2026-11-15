# -*- coding: utf-8 -*-
# ornek1.py - 1+2+...+n formulunun tumevarimla denetimi.


def toplam(n):
    s = 0
    for i in range(1, n + 1):
        s += i
    return s


def formul(n):
    return n * (n + 1) // 2


if __name__ == "__main__":
    print("n  toplam  formul")
    for n in range(1, 6):
        print(n, toplam(n), formul(n))
    print("taban (n=1):", formul(1) == 1)
    adim = all(formul(k + 1) - formul(k) == k + 1
               for k in range(1000))
    print("adim (k<1000):", adim)
    print("n<=1000 icin toplam == formul:",
          all(toplam(n) == formul(n) for n in range(1, 1001)))
