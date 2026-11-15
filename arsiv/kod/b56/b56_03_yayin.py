import numpy as np

def yayin_sekli(s1, s2):
    # sag hizala; her eksende boyutlar esit ya da biri 1 olmali
    n = max(len(s1), len(s2))
    p1 = (1,) * (n - len(s1)) + tuple(s1)
    p2 = (1,) * (n - len(s2)) + tuple(s2)
    out = []
    for a, b in zip(p1, p2):
        if a == b or b == 1:
            out.append(a)
        elif a == 1:
            out.append(b)
        else:
            raise ValueError("uyumsuz: %d ve %d" % (a, b))
    return tuple(out)

print("(3,4)+(4,)  ->", yayin_sekli((3, 4), (4,)))
print("(3,1)+(1,4) ->", yayin_sekli((3, 1), (1, 4)))
print("(5,)+(5,1)  ->", yayin_sekli((5,), (5, 1)))
print("(8,1,6)+(7,1)->", end=" ")
try:
    print(yayin_sekli((8, 1, 6), (7, 1)))
except ValueError as e:
    print("hata:", e)

rng = np.random.default_rng(56)
def rastgele_sekil():
    boy = rng.integers(1, 4)
    return tuple(int(rng.integers(1, 4)) for _ in range(boy))

uyusan = 0
for _ in range(2000):
    s1, s2 = rastgele_sekil(), rastgele_sekil()
    try:
        bizim = yayin_sekli(s1, s2)
    except ValueError:
        bizim = None
    try:
        numpy_s = tuple(np.broadcast_shapes(s1, s2))
    except ValueError:
        numpy_s = None
    uyusan += (bizim == numpy_s)
print("2000 rastgele sekil cifti, uyusan:", uyusan)

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
sutun = x.reshape(5, 1)
print("x - x.mean(), x (5,):", (x - x.mean()).shape)
print("x - sutun ->", (x - sutun).shape)
print("dogru (keepdims):", (sutun - sutun.mean(axis=0)).shape)

b = np.broadcast_to(np.arange(3), (1000, 3))
print("broadcast_to sekil:", b.shape, " strides:", b.strides)
print("kopya mi:", not np.shares_memory(b, np.arange(3)))
