# duzen.py: bellek duzeni, yayinlama (broadcasting) ve einsum
import time
import numpy as np

n = 2000
A = np.random.default_rng(42).standard_normal((n, n))   # C duzeni
# Fortran duzeni (sutun oncelikli)
F = np.asfortranarray(A)


def satir_tara(M):
    s = 0.0
    for i in range(n):
        s += M[i, :].sum()          # bitisik bellek
    return s


def sutun_tara(M):
    s = 0.0
    for j in range(n):
        s += M[:, j].sum()          # adim = n * 8 bayt
    return s


def olc(f, M):
    en_kisa = float("inf")
    for _ in range(5):
        t0 = time.perf_counter()
        f(M)
        en_kisa = min(en_kisa, time.perf_counter() - t0)
    return en_kisa


print("C duzeni    satir: %.4f s  sutun: %.4f s"
      % (olc(satir_tara, A), olc(sutun_tara, A)))
print("F duzeni    satir: %.4f s  sutun: %.4f s"
      % (olc(satir_tara, F), olc(sutun_tara, F)))

a = np.arange(3)
b = np.arange(3).reshape(3, 1)
print("a + b (3,)+(3,1) ->", (a + b).shape)
print(a + b)

X = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 9.0],
              [7.0, 8.0, 1.0]])
dogru = X - X.mean(axis=0)          # sutun ortalamasi
yanlis = X - X.mean(axis=1)         # satir ortalamasi, yanlis eksen
print("dogru: sutun ort. sifir ?", np.allclose(dogru.mean(axis=0), 0))
print("yanlis: sutun ort. sifir ?",
      np.allclose(yanlis.mean(axis=0), 0))

B = np.arange(6.0).reshape(2, 3)
C = np.arange(12.0).reshape(3, 4)
print("einsum == @ ?",
      np.allclose(np.einsum("ik,kj->ij", B, C), B @ C))
u = np.array([1.0, 2.0, 3.0])
v = np.array([10.0, 20.0])
print("dis carpim (einsum):")
print(np.einsum("i,j->ij", u, v))
# (batch, kanal, yukseklik, genislik)
batch = np.zeros((8, 3, 32, 32))
print("tensor sekli:", batch.shape, " eleman:", batch.size)
print("ortalama kanal basina:", batch.mean(axis=(0, 2, 3)).shape)
