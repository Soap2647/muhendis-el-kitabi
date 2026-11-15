# matris.py: matris zinciri carpimi (aralik DP) ve kontrol
import random

INF = 10 ** 18


def matris_zinciri(p):
    # A_i (0 tabanli, ekranda A{i+1}): boyut p[i] x p[i+1]; len(p)=n+1
    n = len(p) - 1
    m = [[0] * n for _ in range(n)]   # m[i][j]: en az maliyet
    s = [[0] * n for _ in range(n)]   # s[i][j]: en iyi bolme noktasi
    for uzunluk in range(2, n + 1):
        for i in range(n - uzunluk + 1):
            j = i + uzunluk - 1
            m[i][j] = INF
            for k in range(i, j):
                q = m[i][k] + m[k + 1][j] + p[i] * p[k + 1] * p[j + 1]
                if q < m[i][j]:
                    m[i][j] = q
                    s[i][j] = k
    return m, s


def parantez(s, i, j):
    if i == j:
        return f"A{i + 1}"
    k = s[i][j]
    return f"({parantez(s, i, k)} x {parantez(s, k + 1, j)})"


def tum_agaclar(p, i, j):
    # Tum parantezlemeleri (Catalan sayisi kadar) uretir:
    # (maliyet, ifade) ciftleri
    if i == j:
        return [(0, f"A{i + 1}")]
    sonuc = []
    for k in range(i, j):
        for c1, e1 in tum_agaclar(p, i, k):
            for c2, e2 in tum_agaclar(p, k + 1, j):
                c = c1 + c2 + p[i] * p[k + 1] * p[j + 1]
                sonuc.append((c, f"({e1} x {e2})"))
    return sonuc


def main():
    p = [30, 35, 15, 5, 10, 20, 25]     # A1..A6
    m, s = matris_zinciri(p)
    print("en az skaler carpim:", m[0][-1])
    print("parantezleme:", parantez(s, 0, len(p) - 2))
    rnd = random.Random(42)
    hata = 0
    for _ in range(200):
        n = rnd.randint(1, 6)
        q = [rnd.randint(1, 9) for _ in range(n + 1)]
        m, _ = matris_zinciri(q)
        en_az = min(c for c, _ in tum_agaclar(q, 0, n - 1))
        if n >= 1 and m[0][n - 1] != en_az:
            hata += 1
    print("200 rastgele ornek (tum agaclar), hata:", hata)


if __name__ == "__main__":
    main()
