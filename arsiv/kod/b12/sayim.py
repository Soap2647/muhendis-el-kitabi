import random
import math
import sys
import bisect

random.seed(42)
sys.setrecursionlimit(10000)

print("== 1. Lineer arama: ortalama karşılaştırma (n+1)/2 ==")
for n in (10, 100, 1000):
    arr = random.sample(range(10 * n), n)
    toplam = 0
    denemeler = 20000
    for _ in range(denemeler):
        idx = random.randrange(n)
        hedef = arr[idx]
        k = 0
        for x in arr:
            k += 1
            if x == hedef:
                break
        toplam += k
    print(f"n={n:5d}  ortalama={toplam / denemeler:9.2f}  (n+1)/2={(n + 1) / 2:9.2f}")

print()
print("== 2. Naif hızlı sıralama, ilk eleman pivot, sıralı girdi ==")
def qs_karsilastirma(a):
    sayac = [0]
    def qs(lo, hi):
        if hi - lo <= 1:
            return
        sayac[0] += hi - lo - 1
        p = a[lo]
        i = lo + 1
        for j in range(lo + 1, hi):
            if a[j] < p:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[lo], a[i - 1] = a[i - 1], a[lo]
        qs(lo, i - 1)
        qs(i, hi)
    qs(0, len(a))
    return sayac[0]

for n in (100, 1000):
    print(f"n={n:5d}  sirali={qs_karsilastirma(list(range(n))):9d}  "
          f"n(n-1)/2={n * (n - 1) // 2:9d}")

print()
print("== 3. İkili sayaç: n artış toplam bit çevirme ==")
for n in (1000, 100000):
    bits = [0] * 40
    flips = 0
    for _ in range(n):
        i = 0
        while bits[i] == 1:
            bits[i] = 0
            flips += 1
            i += 1
        bits[i] = 1
        flips += 1
    print(f"n={n:7d}  toplam={flips:8d}  toplam/n={flips / n:.4f}  "
          f"2n={2 * n}")

print()
print("== 4. Heapify: sift-down takas sayısı (rastgele girdi) ==")
def heapify_takas(a):
    takas = 0
    n = len(a)
    for s in range(n // 2 - 1, -1, -1):
        i = s
        while True:
            sol, sag = 2 * i + 1, 2 * i + 2
            en = i
            if sol < n and a[sol] < a[en]:
                en = sol
            if sag < n and a[sag] < a[en]:
                en = sag
            if en == i:
                break
            a[i], a[en] = a[en], a[i]
            takas += 1
            i = en
    return takas

for n in (1000, 10000, 100000):
    a = [random.randrange(10**9) for _ in range(n)]
    t = heapify_takas(a)
    print(f"n={n:6d}  takas={t:7d}  takas/n={t / n:.4f}")

print()
print("== 5. Üst sınır: perfect ağaç, Σ h*2^(H-h) ==")
for H in (3, 4, 10):
    toplam = sum(h * 2 ** (H - h) for h in range(H + 1))
    n = 2 ** (H + 1) - 1
    print(f"H={H:2d} n={n:5d} en kötü takas (üst sınır)={toplam:5d} "
          f"toplam/n={toplam / n:.4f}")

print()
print("== 6. Master Theorem sayısal kontrol: T(n)=2T(n/2)+n^2 ==")
def T2(n):
    if n <= 1:
        return 1
    return 2 * T2(n // 2) + n * n
for k in (4, 8, 12, 16):
    n = 2 ** k
    print(f"n=2^{k:<2d}  T(n)/n^2={T2(n) / (n * n):.6f}")

print()
print("== 7. T(n)=2T(n/2)+n, T(1)=1: T(n) = n*log2(n) + n ? ==")
def T1(n):
    if n <= 1:
        return 1
    return 2 * T1(n // 2) + n
for k in (1, 3, 5, 10):
    n = 2 ** k
    print(f"n={n:5d}  T(n)={T1(n):7d}  n*log2(n)+n={n * k + n:7d}")

print()
print("== 8. Tournament maksimum: karşılaştırma sayısı ==")
def maks_bol(a, lo, hi, sayac):
    if hi - lo == 1:
        return a[lo]
    orta = (lo + hi) // 2
    sol = maks_bol(a, lo, orta, sayac)
    sag = maks_bol(a, orta, hi, sayac)
    sayac[0] += 1
    return sol if sol >= sag else sag
for n in (8, 1000, 1024):
    a = [random.randrange(10**6) for _ in range(n)]
    s = [0]
    m = maks_bol(a, 0, n, s)
    print(f"n={n:5d}  karsilastirma={s[0]:5d}  n-1={n - 1:5d}  "
          f"max_ok={m == max(a)}")

print()
print("== 9. Özyineleme derinliği limiti ==")
print("sys.getrecursionlimit() =", sys.getrecursionlimit())
def derin(n):
    return 0 if n == 0 else 1 + derin(n - 1)
en_buyuk = 0
for n in range(100, 5000, 1):
    try:
        derin(n)
        en_buyuk = n
    except RecursionError:
        break
print("ilk RecursionError olan n (taramada):", n)

print()
print("== 10. Büyüme tablosu: işlem sayısı (log2 hesabı) ==")
for n in (10, 100, 1000, 10**6):
    lg = math.log2(n)
    print(f"n={n:>8d} log2n={lg:7.2f} nlog2n={n * lg:14.1f} "
          f"n^2={n * n:>14d} 2^n={'%.3e' % (2.0 ** n) if n <= 1000 else 'cok buyuk'}")
