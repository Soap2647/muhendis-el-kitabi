# -*- coding: utf-8 -*-
"""Bolum 73 - t01: NT-Xent kaybinin dogrulanmasi ve tau etkisi.

(a) Vektorlestirilmis nt_xent, dongulu referans gerceklemesiyle
eslesir mi?
(b) El ornegi: 2 pozitif cift, tau = 0.5, benzerlik matrisi ve kayip.
(c) Tau taramasi: pozitifler hizali / rastgele; kayip ne zaman
log(2N-1)?
"""

import math
import numpy as np
import torch
from ortak73 import nt_xent


def dongu(z1, z2, tau):
    """Referans: normalize et; her capa icin
    -log(pozitif / tum digerleri)."""
    z = torch.cat([z1, z2]).double()
    z = [v / v.norm() for v in z]
    n = len(z1)
    toplam = 0.0
    for a in range(2 * n):
        p = (a + n) % (2 * n)
        pay = math.exp(float(z[a] @ z[p]) / tau)
        payda = sum(
            math.exp(float(z[a] @ z[j]) / tau)
            for j in range(2 * n)
            if j != a
        )
        toplam += -math.log(pay / payda)
    return toplam / (2 * n)


torch.manual_seed(73)
z1 = torch.randn(8, 16, dtype=torch.float64)
z2 = z1 + 0.5 * torch.randn(8, 16, dtype=torch.float64)
print("(a) vektorlestirilmis ve dongulu kayip (N = 8, D = 16)")
for tau in (0.1, 0.5):
    v = nt_xent(z1, z2, tau).item()
    r = dongu(z1, z2, tau)
    print(
        "tau=%.1f  vektor=%.10f  dongu=%.10f  fark=%.1e"
        % (tau, v, r, abs(v - r))
    )

print("\n(b) el ornegi: N = 2, birim vektorler, tau = 0.5")
a = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.float64)
b = torch.tensor([[0.8, 0.6], [0.6, 0.8]], dtype=torch.float64)
z = torch.cat([a, b])
print("benzerlik matrisi (sira: a0 a1 b0 b1):")
print(np.round((z @ z.T).numpy(), 2))
print("kayip (vektor) = %.6f" % nt_xent(a, b, 0.5).item())
print("kayip (dongu)  = %.6f" % dongu(a, b, 0.5))

print("\n(c) tau taramasi, N = 128, D = 64, sabit tohum")
rng = np.random.default_rng(73)
n = 128
Z1 = torch.as_tensor(rng.standard_normal((n, 64)))
Zh = torch.as_tensor(Z1.numpy() + 0.1 * rng.standard_normal((n, 64)))
Zr = torch.as_tensor(rng.standard_normal((n, 64)))
print("log(2N-1) = %.4f" % math.log(2 * n - 1))
print("tau    hizali   rastgele")
for tau in (0.05, 0.1, 0.2, 0.5, 1.0):
    print(
        "%.2f   %.4f   %.4f"
        % (
            tau,
            nt_xent(Z1, Zh, tau).item(),
            nt_xent(Z1, Zr, tau).item(),
        )
    )
