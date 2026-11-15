# -*- coding: utf-8 -*-
"""BatchNorm'un 4 orneklik batch uzerinde ileri ve geri gecisi."""

import numpy as np
from egitim_np import bn_ileri, bn_geri

x = np.array([[1.0], [3.0], [5.0], [7.0]])
gamma, beta = np.array([2.0]), np.array([1.0])
y, cache, mu, var = bn_ileri(x, gamma, beta)
print("mu = %.4f   sigma^2 = %.4f" % (mu[0], var[0]))
print("xhat =", np.round(cache[0].ravel(), 4))
print("y    =", np.round(y.ravel(), 4))
dy = np.array([[1.0], [0.0], [0.0], [0.0]])
dx, dgamma, dbeta = bn_geri(dy, cache)
print("dgamma = %.4f   dbeta = %.4f" % (dgamma[0], dbeta[0]))
print("dx =", np.round(dx.ravel(), 4))
print("sum(dx) = %.2e  (BN gradyani toplami sifirdir)" % dx.sum())
