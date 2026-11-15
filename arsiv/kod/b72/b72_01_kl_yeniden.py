# -*- coding: utf-8 -*-
"""Bolum 72.7: KL'nin kapali formu, yeniden parametrelendirme
hilesi ve ELBO'nun log p(x) alt siniri oldugunun sayisal
dogrulamasi."""
import math
import torch
from torch.distributions import Normal, kl_divergence

torch.manual_seed(0)


def kl_kapali(mu, sig):
    """KL(N(mu, sig^2) || N(0, 1)), nat cinsinden."""
    return 0.5 * (sig**2 + mu**2 - 1.0 - math.log(sig**2))


def kl_mc(mu, sig, n=2_000_000):
    """Ayni KL'yi Monte Carlo ile: E_q[log q(z) - log p(z)]."""
    q = Normal(mu, sig)
    p = Normal(0.0, 1.0)
    z = q.sample((n,))
    return (q.log_prob(z) - p.log_prob(z)).mean().item()


print("== 1. KL: kapali form, MC ve torch ==")
for mu, sig in [(1.5, 0.5), (0.0, 1.0), (-0.8, 2.0)]:
    k = kl_kapali(mu, sig)
    m = kl_mc(mu, sig)
    t = kl_divergence(Normal(mu, sig), Normal(0.0, 1.0)).item()
    print(f"mu={mu:+.2f} s={sig:.2f} kapali={k:.6f} "
          f"MC={m:.6f} torch={t:.6f}")

print()
print("== 2. Yeniden parametrelendirme: gradyan geciyor mu? ==")
mu = torch.tensor(0.5, requires_grad=True)
sig = torch.tensor(0.8, requires_grad=True)
z_s = Normal(mu, sig).sample((100_000,))
print("sample():  z.requires_grad =", z_s.requires_grad)
try:
    ((z_s - 2.0) ** 2).mean().backward()
except RuntimeError as hata:
    print("sample() ile geri yayilim: HATA ->", type(hata).__name__)

z_r = Normal(mu, sig).rsample((100_000,))
print("rsample(): z.requires_grad =", z_r.requires_grad)
kayip = ((z_r - 2.0) ** 2).mean()
kayip.backward()
print(f"d kayip/d mu  = {mu.grad.item():+.4f}  "
      f"(kapali: 2(mu-2) = -3)")
print(f"d kayip/d sig = {sig.grad.item():+.4f}  "
      f"(kapali: 2 sig = 1.6)")

print()
print("== 3. ELBO <= log p(x): tek boyutlu dogrusal Gauss ==")
x = 1.0
# Model: p(z) = N(0,1), p(x|z) = N(z,1)  =>  p(x) = N(0,2)
log_px = Normal(0.0, math.sqrt(2.0)).log_prob(torch.tensor(x)).item()
print(f"log p(x) kesin = {log_px:.6f}")


def rec_kapali(m, s):
    """E_q[log N(x; z, 1)] kapali form: E[(x-z)^2] = (x-m)^2 + s^2."""
    return -0.5 * math.log(2 * math.pi) - 0.5 * ((x - m) ** 2 + s**2)


def elbo(m, s):
    return rec_kapali(m, s) - kl_kapali(m, s)


q = Normal(0.3, 0.9)
z = q.rsample((1_000_000,))
rec_mc = Normal(z, 1.0).log_prob(torch.tensor(x)).mean().item()
print(f"rec MC (0.3, 0.9) = {rec_mc:.6f}  "
      f"kapali = {rec_kapali(0.3, 0.9):.6f}")

for m, s in [(0.0, 1.0), (0.3, 0.9), (0.5, 0.5**0.5), (0.8, 0.5)]:
    e = elbo(m, s)
    print(f"q: m={m:.2f} s={s:.4f} ELBO={e:.6f} "
          f"bosluk={log_px - e:.6f}")
