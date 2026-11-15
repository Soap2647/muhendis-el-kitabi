# -*- coding: utf-8 -*-
"""Ornek 1: PSI'nin elle hesabi (dort kutu, kagit kalemiyle)."""
import math

e = [0.25, 0.25, 0.25, 0.25]    # referans oranlari
a = [0.40, 0.30, 0.20, 0.10]    # yeni pencerenin oranlari
terimler = [(ai - ei) * math.log(ai / ei) for ai, ei in zip(a, e)]
for k, t in enumerate(terimler, 1):
    print("kutu %d: (a-e) ln(a/e) = %+.4f" % (k, t))
print("PSI = %.4f" % sum(terimler))
