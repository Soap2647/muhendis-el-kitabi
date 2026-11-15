# blas_bilgi.py: NumPy'nin altindaki BLAS/LAPACK kutuphanesini oku
import numpy as np

yapi = np.show_config(mode="dicts")
bagli = yapi["Build Dependencies"]
for ad in ["blas", "lapack"]:
    print(ad, "->", bagli[ad]["name"], bagli[ad]["version"])
print("numpy", np.__version__)
