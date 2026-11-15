# -*- coding: utf-8 -*-
"""Bölüm 66 - t00: görüntü tensörü şekilleri ve tam bağlı katmanın
maliyeti."""

import numpy as np
import torch

# 1) Görüntü düzenleri: NumPy/OpenCV (H, W, C), PyTorch (C, H, W)
img = np.random.default_rng(0).integers(
    0, 256, (32, 32, 3), dtype=np.uint8
)
print("NumPy (H, W, C):", img.shape, img.dtype)
x = img.transpose(2, 0, 1).astype(np.float32) / 255.0
print(
    "PyTorch (C, H, W):", x.shape, x.dtype, "aralık", x.min(), x.max()
)
batch = torch.tensor(x[None])
print("Batch (N, C, H, W):", tuple(batch.shape))

# 2) Tam bağlı katmanın ağırlık sayısı: giriş = H*W*C, çıkış = 1000
# gizli birim
for ad, h, w, c in (
    ("32x32 gri (bu bölüm)", 32, 32, 1),
    ("224x224 RGB (ImageNet)", 224, 224, 3),
):
    giris = h * w * c
    agirlik = giris * 1000 + 1000
    print(
        "%-22s girdi %6d, ilk katman %10d parametre"
        % (ad, giris, agirlik)
    )
