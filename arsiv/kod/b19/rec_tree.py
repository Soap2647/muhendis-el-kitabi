# rec_tree.py: T(n) = 2T(n/2) + n log2 n icin olcek kontrolu
import math
from functools import lru_cache


@lru_cache(maxsize=None)
def T(n):
    if n <= 1:
        return 0.0
    return 2 * T(n // 2) + n * math.log2(n)


if __name__ == "__main__":
    print("   k      n        T(n)    T(n)/(n log^2 n)")
    for k in (4, 8, 12, 16, 20):
        n = 2 ** k
        print("%3d %7d %12.0f %12.4f"
              % (k, n, T(n), T(n) / (n * math.log2(n) ** 2)))
