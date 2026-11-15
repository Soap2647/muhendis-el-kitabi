# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 0: ortam ve ilk cekirdek (vektor toplama)."""
import _cudaenv  # noqa: F401  (Windows DLL yollari)
import numpy as np
import torch
from numba import cuda


@cuda.jit
def topla(x, y, out):
    i = cuda.grid(1)
    if i < out.size:
        out[i] = x[i] + y[i]


def main():
    print("torch:", torch.__version__)
    print("torch CUDA:", torch.cuda.is_available())
    dev = cuda.get_current_device()
    print("numba GPU:", dev.name.decode())
    print("compute capability:", dev.compute_capability)
    n = 1 << 20
    x = cuda.to_device(np.arange(n, dtype=np.float32))
    y = cuda.to_device(np.ones(n, dtype=np.float32))
    out = cuda.device_array(n, dtype=np.float32)
    topla[(n + 255) // 256, 256](x, y, out)
    sonuc = out.copy_to_host()
    dogru = np.allclose(sonuc, np.arange(n, dtype=np.float32) + 1)
    print("n =", n, "dogru:", dogru)
    print("ilk 4 deger:", sonuc[:4])


if __name__ == "__main__":
    main()
