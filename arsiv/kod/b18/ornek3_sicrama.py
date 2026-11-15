# ornek3_sicrama.py: Jump Game II. a[i] = i'den en fazla kac adim
# ilerlenebilir. Hedef n-1'e en az kac sicrama? Tek gecisli acgozlu
# cozum; BFS ile kaba dogrulama (dugumler = indeksler).
import random
from collections import deque


def en_az_sicrama(a, izle=False):
    n = len(a)
    sicrama, simdiki_son, en_uzak = 0, 0, 0
    for i in range(n - 1):
        en_uzak = max(en_uzak, i + a[i])
        if i == simdiki_son:
            sicrama += 1
            simdiki_son = en_uzak
        if izle:
            print("i=%d a=%d en_uzak=%d sicrama=%d son=%d"
                  % (i, a[i], en_uzak, sicrama, simdiki_son))
        if simdiki_son >= n - 1:
            break
    return sicrama


def bfs_kaba(a):
    n = len(a)
    if n == 1:
        return 0
    dist = [-1] * n
    dist[0] = 0
    kuyruk = deque([0])
    while kuyruk:
        i = kuyruk.popleft()
        for j in range(i + 1, min(n - 1, i + a[i]) + 1):
            if dist[j] == -1:
                dist[j] = dist[i] + 1
                kuyruk.append(j)
    return dist[n - 1]


def main():
    ornek = [2, 3, 1, 1, 4]
    print("dizi:", ornek)
    print("izleme:")
    sonuc = en_az_sicrama(ornek, izle=True)
    print("en az sicrama:", sonuc, "| BFS:", bfs_kaba(ornek))
    rnd = random.Random(42)
    hata = atlanan = 0
    for _ in range(300):
        n = rnd.randint(1, 10)
        a = [rnd.randint(0, 4) for _ in range(n)]
        b = bfs_kaba(a)
        if b == -1:
            atlanan += 1       # hedefe ulasilamaz: kapsam disi
            continue
        if en_az_sicrama(a) != b:
            hata += 1
    print("300 dizi (ulasilamayan atlanan):", atlanan,
          "hata:", hata)


if __name__ == "__main__":
    main()
