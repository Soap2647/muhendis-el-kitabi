# Kaynak yonetimi: with (RAII karsiligi) ve __del__ guvenilirligi
import gc
import os
import tempfile

class KaynakYoneticisi:
    def __init__(self, ad):
        self.ad = ad
    def __enter__(self):
        print("edin:", self.ad)
        return self
    def __exit__(self, tip, deger, iz):
        print("birak:", self.ad, "(istisna:", tip is not None, ")")
        return False                 # istisnayi yutma

try:
    with KaynakYoneticisi("dosya") as k:
        raise ValueError("kasitli hata")
except ValueError as e:
    print("disariya cikti:", e)

class Dugum:
    def __init__(self, ad):
        self.ad = ad
        self.komsu = None
    def __del__(self):
        print("__del__:", self.ad)

print("-- dongu yok:")
d = Dugum("tek")
del d                                # refcount 0 -> hemen cagrilir

print("-- dongu var, gc kapali:")
gc.disable()
a, b = Dugum("a"), Dugum("b")
a.komsu, b.komsu = b, a              # dongu
del a, b
print("  del yapildi, __del__ henuz yok")
gc.collect()
print("  gc.collect() sonrasi")
gc.enable()
