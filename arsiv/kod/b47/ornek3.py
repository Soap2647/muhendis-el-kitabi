# -*- coding: utf-8 -*-
# ornek3.py - 1..1000 icinde 2, 3 veya 5'e bolunenler.
N = 1000

if __name__ == "__main__":
    print("tekli :", N // 2, N // 3, N // 5)
    print("ikili :", N // 6, N // 10, N // 15)
    print("uclu  :", N // 30)
    formul = N // 2 + N // 3 + N // 5 - N // 6 - N // 10 - N // 15 \
        + N // 30
    print("formul:", formul)
    kaba = sum(1 for x in range(1, N + 1)
               if x % 2 == 0 or x % 3 == 0 or x % 5 == 0)
    print("kaba  :", kaba)
    print("hicbirine bolunmeyen:", N - kaba)
