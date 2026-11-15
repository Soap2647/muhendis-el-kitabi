# medyan.py: deterministik O(n) secim (medyanlarin medyani)
import random
import time


def sec(dizi, k):
    """Sirali dizinin k. elemani (0 tabanli), kotu durumda O(n)."""
    n = len(dizi)
    if n <= 5:
        return sorted(dizi)[k]
    # 1) 5'erli gruplarin medyanlari
    medyanlar = []
    for i in range(0, n, 5):
        grup = sorted(dizi[i:i + 5])
        medyanlar.append(grup[len(grup) // 2])
    # 2) medyanlarin medyani (ozyinelemeli): pivot
    piv = sec(medyanlar, (len(medyanlar) - 1) // 2)
    # 3) pivota gore uc parcaya bol
    sol = [x for x in dizi if x < piv]
    orta = [x for x in dizi if x == piv]
    sag = [x for x in dizi if x > piv]
    # 4) hangi parcada?
    if k < len(sol):
        return sec(sol, k)
    if k < len(sol) + len(orta):
        return piv
    return sec(sag, k - len(sol) - len(orta))


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(1, 80)
        a = [rnd.randint(0, 15) for _ in range(n)]   # cok tekrar
        s = sorted(a)
        for k in range(n):
            assert sec(a, k) == s[k]
    print("300 rastgele dizi, tum k: sec == sorted()[k] (tekrarli)")
    a = [rnd.random() for _ in range(10 ** 5)]
    t0 = time.perf_counter()
    m = sec(a, len(a) // 2)
    t1 = time.perf_counter()
    s = sorted(a)[len(a) // 2]
    t2 = time.perf_counter()
    print("n = 10^5 medyan: sec %.3f s, sorted %.3f s"
          % (t1 - t0, t2 - t1))
    print("ayni deger:", m == s)
