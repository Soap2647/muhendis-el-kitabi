# -*- coding: utf-8 -*-
# b58_09_poisson.py: Poisson regresyonu (GLM, log baglanti) sifirdan
import numpy as np
from sklearn.linear_model import PoissonRegressor
from b58_core import poisson_irls

# Sentetik: saatte paket kaybi sayisi. Sicaklik (x1), titresim (x2).
rng = np.random.default_rng(58)
n = 2000
X = rng.normal(0, 1, (n, 2))  # standartlastirilmis
beta_gercek = np.array([0.3, 0.6, -0.4])  # sapma, x1, x2
eta = beta_gercek[0] + X @ beta_gercek[1:]
y = rng.poisson(np.exp(eta))
ntr = 1500
Xtr, Xte, ytr, yte = X[:ntr], X[ntr:], y[:ntr], y[ntr:]
Atr = np.hstack([np.ones((ntr, 1)), Xtr])
Ate = np.hstack([np.ones((n - ntr, 1)), Xte])
print(
    "ortalama sayim (egitim) = %.3f, varyans = %.3f"
    % (ytr.mean(), ytr.var(ddof=1))
)

w, adim = poisson_irls(Atr, ytr)
print("IRLS adim = %d, w = %s" % (adim, np.round(w, 4)))

sk = PoissonRegressor(alpha=0.0, tol=1e-10, max_iter=10000).fit(
    Xtr, ytr
)
print(
    "max|w - w_sk| = %.2e"
    % np.max(np.abs(np.concatenate([[sk.intercept_], sk.coef_]) - w))
)


def sapma(y_, mu_):
    # Poisson sapmasi: 2 * sum(y ln(y/mu) - (y - mu)), 0 ln 0 = 0
    t = np.where(
        y_ > 0, y_ * np.log(np.where(y_ > 0, y_, 1) / mu_), 0.0
    )
    return np.mean(2 * (t - (y_ - mu_)))


mu_te = np.exp(Ate @ w)
mu_sabit = np.full(len(yte), ytr.mean())
print(
    "test sapma: model = %.4f, baseline (sabit) = %.4f"
    % (sapma(yte, mu_te), sapma(yte, mu_sabit))
)
print(
    "test MAE:   model = %.4f, baseline = %.4f"
    % (np.mean(np.abs(yte - mu_te)), np.mean(np.abs(yte - mu_sabit)))
)
print(
    "oran e^beta (x1, +1 SD) = %.4f, (x2, +1 SD) = %.4f"
    % (np.exp(w[1]), np.exp(w[2]))
)

# Dagilim uyumu: Pearson dispersiyon (~1 olmali)
mu_tr = np.exp(Atr @ w)
p = Atr.shape[1]
disp = np.sum((ytr - mu_tr) ** 2 / mu_tr) / (ntr - p)
print("Pearson dispersiyon (gercek model) = %.3f" % disp)

# Asiri yayilim: hiz rastgele (Gamma karisimi, ortalama 1, shape 2)
G = rng.gamma(shape=2.0, scale=0.5, size=n)
y2 = rng.poisson(np.exp(eta) * G)
y2tr = y2[:ntr]
w2, _ = poisson_irls(Atr, y2tr)
mu2 = np.exp(Atr @ w2)
disp2 = np.sum((y2tr - mu2) ** 2 / mu2) / (ntr - p)
print(
    "asiri yayilim: Pearson dispersiyon = %.3f (beklenen ~1+mu/2)"
    % disp2
)
print(
    "ortalama mu = %.3f, 1 + ortalama(mu)/2 = %.3f"
    % (mu2.mean(), 1 + mu2.mean() / 2)
)
