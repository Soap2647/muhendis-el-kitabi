# -*- coding: utf-8 -*-
"""Windows'ta numba CUDA icin DLL yollarini ayarlar.

CUDA Toolkit yoksa pip ile gelen nvidia-* paketleri kullanilir:
  nvidia-cuda-nvcc-cu12 (libNVVM), nvidia-cuda-runtime-cu12 (cudart).
numba 'cudart.dll' arar; pip paketi 'cudart64_12.dll' getirir,
bu yuzden adi degistirilmis bir kopya cudashim/ altina konur.
"""

import os
import shutil
import nvidia

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = list(nvidia.__path__)[0]
os.environ["CUDA_PATH"] = os.path.join(BASE, "cuda_nvcc")
os.add_dll_directory(os.path.join(BASE, "cuda_nvcc", "nvvm", "bin"))

SHIM = os.path.join(HERE, "cudashim")
os.makedirs(SHIM, exist_ok=True)
_hedef = os.path.join(SHIM, "cudart.dll")
if not os.path.exists(_hedef):
    shutil.copy(
        os.path.join(BASE, "cuda_runtime", "bin", "cudart64_12.dll"),
        _hedef,
    )
os.add_dll_directory(SHIM)
