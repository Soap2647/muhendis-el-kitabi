# skyline.py: bina siluetleri, D&C birlestirme ve kaba kuvvet
import random


def birlestir(A, B):
    """Iki siluetin noktalarini x'e gore tara; max yukseklik."""
    i = j = 0
    h1 = h2 = 0          # A ve B'nin o andaki yukseklikleri
    sonuc = []
    while i < len(A) or j < len(B):
        xa = A[i][0] if i < len(A) else float("inf")
        xb = B[j][0] if j < len(B) else float("inf")
        x = min(xa, xb)
        if xa == x:
            h1 = A[i][1]
            i += 1
        if xb == x:
            h2 = B[j][1]
            j += 1
        h = max(h1, h2)
        if not sonuc or sonuc[-1][1] != h:  # degisti mi?
            sonuc.append((x, h))
    return sonuc


def sil(binalar):
    """binalar: (sol, yukseklik, sag). Donus: [(x, h), ...]."""
    if not binalar:
        return []
    if len(binalar) == 1:
        L, H, R = binalar[0]
        return [(L, H), (R, 0)]
    mid = len(binalar) // 2
    return birlestir(sil(binalar[:mid]), sil(binalar[mid:]))


def taban_yukseklik(binalar, x):
    """Birim aralik [x, x+1) icin kaba kuvvet yuksekligi."""
    return max((h for L, h, R in binalar if L <= x < R), default=0)


def sil_yukseklik(s, x):
    h = 0
    for xk, hk in s:
        if xk <= x:
            h = hk
        else:
            break
    return h


if __name__ == "__main__":
    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(1, 25)
        binalar = []
        for _ in range(n):
            L = rnd.randint(0, 40)
            R = L + rnd.randint(1, 15)
            binalar.append((L, rnd.randint(1, 30), R))
        s = sil(binalar)
        for x in range(0, 60):
            assert sil_yukseklik(s, x) == taban_yukseklik(binalar, x)
    print("300 rastgele bina seti: D&C siluet == kaba kuvvet")
    ornek = [(1, 11, 5), (2, 6, 7), (3, 13, 9), (12, 7, 16),
             (14, 3, 25), (19, 18, 22), (23, 13, 29), (24, 4, 30)]
    print("Ornek siluet (Bolum 19.10'daki sekil):")
    for x, h in sil(ornek):
        print("x=%2d  h=%2d" % (x, h))
