# lis.py: en uzun artan altdizi, O(n^2) ve sabir (O(n log n))
import bisect
import itertools
import random


def lis_n2(a):
    n = len(a)
    L = [1] * n                 # L[i]: a[i]'de biten en uzun LIS
    for i in range(n):
        for j in range(i):
            if a[j] < a[i] and L[j] + 1 > L[i]:
                L[i] = L[j] + 1
    return max(L, default=0)


def lis_nlogn(a, izle=False):
    kuyruk = []                 # kuyruk[k]: k+1 uzunluk icin en kucuk
    for x in a:
        k = bisect.bisect_left(kuyruk, x)
        if k == len(kuyruk):
            kuyruk.append(x)
        else:
            kuyruk[k] = x
        if izle:
            print(f"  x={x:2d} -> {kuyruk}")
    return len(kuyruk)


def kaba(a):
    best = 0
    for k in range(len(a) + 1):
        for alt in itertools.combinations(a, k):
            if all(alt[i] < alt[i + 1] for i in range(len(alt) - 1)):
                best = max(best, k)
    return best


def main():
    a = [3, 1, 4, 1, 5, 9, 2, 6]
    print("dizi:", a)
    print("sabir izi:")
    print("LIS (n^2):", lis_n2(a),
          " LIS (n log n):", lis_nlogn(a, True))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        x = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 9))]
        if not (lis_n2(x) == lis_nlogn(x) == kaba(x)):
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
