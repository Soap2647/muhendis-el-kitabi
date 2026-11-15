# vek.py: vektor, nokta carpim, norm, kosinus benzerligi, izdusum
import numpy as np

u = np.array([3.0, 4.0])
v = np.array([4.0, -3.0])

print("u + v   =", u + v)
print("2 * u   =", 2 * u)
print("u . v   =", u @ v)
print("|u|_2   =", np.linalg.norm(u))
print("|u|_1   =", np.linalg.norm(u, 1))
print("|u|_inf =", np.linalg.norm(u, np.inf))


def kosinus(a, b):
    return (a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))


def izdusum(a, b):
    # a vektorunun b dogrultusundaki izdusumu
    return (a @ b) / (b @ b) * b


e1 = np.array([1.0, 0.0])
print("izdusum(u, e1)  =", izdusum(u, e1))
print("kosinus(u, v)   =", round(kosinus(u, v), 6))

# belge benzerligi: kelime sayim vektorleri
a = np.array([2.0, 1.0, 0.0, 3.0])
b = 2 * a                       # ayni icerik, iki kat uzunluk
c = np.array([1.0, 0.0, 0.0, 0.0])
print("kosinus(a, 2a)  =", round(kosinus(a, b), 6))
print("kosinus(a, c)   =", round(kosinus(a, c), 6))
