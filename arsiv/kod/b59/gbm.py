# gbm.py -- gradyan artirma (gradient boosting), sifirdan
import numpy as np
from agac import KararAgaci


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def yaprak_newton(agac, X, g, h):
    # Log-kayip icin yaprak degeri: gamma = sum(g) / sum(h)
    topla = {}
    for i, x in enumerate(X):
        d = agac._yaprak_bul(x)
        a = topla.setdefault(id(d), [d, 0.0, 0.0])
        a[1] += g[i]
        a[2] += h[i]
    for d, sg, sh in topla.values():
        d.deger = sg / sh if sh > 1e-12 else 0.0


class GradyanArtirma:
    def __init__(self, T=100, eta=0.1, derinlik=3,
                 mod="regresyon", min_yaprak=5):
        self.T = T
        self.eta = eta
        self.derinlik = derinlik
        self.mod = mod
        self.min_yaprak = min_yaprak

    def _ag(self):
        return KararAgaci(mod="regresyon",
                          max_derinlik=self.derinlik,
                          min_yaprak=self.min_yaprak)

    def fit(self, X, y, Xv=None, yv=None):
        n = len(y)
        if self.mod == "regresyon":
            self.f0 = float(y.mean())
        else:
            p0 = y.mean()
            self.f0 = float(np.log(p0 / (1 - p0)))
        F = np.full(n, self.f0)
        self.agaclar = []
        if Xv is not None:
            Fv = np.full(len(yv), self.f0)
        self.gecmis = []
        for t in range(self.T):
            if self.mod == "regresyon":
                r = y - F                  # negatif gradyan = artik
                agac = self._ag().fit(X, r)
            else:
                p = sigmoid(F)
                g = y - p                  # -gradyan (log-kayip)
                agac = self._ag().fit(X, g)
                yaprak_newton(agac, X, g, p * (1 - p))
            self.agaclar.append(agac)
            F = F + self.eta * agac.olasilik(X)
            if Xv is not None:
                Fv = Fv + self.eta * agac.olasilik(Xv)
                self.gecmis.append((self._kayip(y, F),
                                    self._kayip(yv, Fv)))
        return self

    def _kayip(self, y, F):
        if self.mod == "regresyon":
            return float(np.mean((y - F) ** 2))
        p = np.clip(sigmoid(F), 1e-12, 1 - 1e-12)
        kayip = y * np.log(p) + (1 - y) * np.log(1 - p)
        return float(-np.mean(kayip))

    def ham(self, X, T=None):
        T = self.T if T is None else T
        F = np.full(len(X), self.f0)
        for agac in self.agaclar[:T]:
            F = F + self.eta * agac.olasilik(X)
        return F

    def tahmin(self, X, T=None):
        F = self.ham(X, T)
        if self.mod == "regresyon":
            return F
        return (sigmoid(F) >= 0.5).astype(int)
