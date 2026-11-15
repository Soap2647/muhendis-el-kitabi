import numpy as np

a = np.arange(12, dtype=np.int32).reshape(3, 4)
print("dtype:", a.dtype, " shape:", a.shape)
print("strides (bayt):", a.strides, " itemsize:", a.itemsize)
print("a[1,2] bellek ofseti:", 1 * 16 + 2 * 4, "bayt")
print("ravel()[6] == a[1,2]:", a.ravel()[6] == a[1, 2])
print("T strides:", a.T.strides)
dilim = a[:, 1:3]
print("dilim strides:", dilim.strides)
print("dilim paylasim:", np.shares_memory(a, dilim))
f = a[[0, 2]]
print("gelismis indeks paylasim:", np.shares_memory(a, f))
m = a[a > 5]
print("maske paylasim:", np.shares_memory(a, m))
print("reshape paylasim:", np.shares_memory(a, a.reshape(4, 3)))
print("T.reshape paylasim:", np.shares_memory(a, a.T.reshape(-1)))
