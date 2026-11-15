# -*- coding: utf-8 -*-
"""Isinma + kosinus takviminin secilen adimlardaki degerleri."""

from egitim_np import lr_isinma_kosinus

W, T, lr_max = 30, 300, 0.01
for t in [0, 1, 15, 29, 30, 165, 299]:
    lr = lr_isinma_kosinus(t, W, T, lr_max, 0.0)
    print("adim %3d   lr = %.6f" % (t, lr))
