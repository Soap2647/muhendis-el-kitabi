# -*- coding: utf-8 -*-
"""Adam'in ilk uc adimini elle izlemek icin: tek parametre."""

import numpy as np
from egitim_np import adam_adim

theta, m, v, t = 1.0, 0.0, 0.0, 0
gradyanlar = [0.5, -0.2, 0.1]
print("adim     g       m        v        m_hat    v_hat    theta")
for g in gradyanlar:
    theta, m, v, t = adam_adim(theta, g, m, v, t, lr=0.1)
    m_hat = m / (1 - 0.9**t)
    v_hat = v / (1 - 0.999**t)
    print(
        "%d  %+.2f  %.5f  %.6f  %.5f  %.5f  %.6f"
        % (t, g, m, v, m_hat, v_hat, theta)
    )
