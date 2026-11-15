# orman.py -- torbalama (bagging) ve rastgele orman, sifirdan
import numpy as np
from agac import KararAgaci


class Torba:
    # max_ozellik=None: saf torbalama; sayi verilirse rastgele orman
    def __init__(self, B=50, max_ozellik=None, seed=0):
        self.B = B
        self.max_ozellik = max_ozellik
        self.seed = seed

    def fit(self, X, y):
        self.k = int(y.max()) + 1
        rng = np.random.default_rng(self.seed)
        n = len(y)
        self.agaclar = []
        # OOB olasilik toplami ve oy sayisi
        self.oob_toplam = np.zeros((n, self.k))
        self.oob_say = np.zeros(n)
        for _ in range(self.B):
            ornek = rng.integers(0, n, n)         # iadeli ornekleme
            disarda = np.setdiff1d(np.arange(n), ornek)
            agac = KararAgaci(max_ozellik=self.max_ozellik, rng=rng,
                              k=self.k)
            agac.fit(X[ornek], y[ornek])
            self.agaclar.append(agac)
            if len(disarda) > 0:
                p = agac.olasilik(X[disarda])
                self.oob_toplam[disarda] += p
                self.oob_say[disarda] += 1
        return self

    def olasilik(self, X):
        return sum(a.olasilik(X) for a in self.agaclar) / self.B

    def tahmin(self, X):
        return np.argmax(self.olasilik(X), axis=1)

    def oob_hatasi(self, y):
        var = self.oob_say > 0
        pred = np.argmax(self.oob_toplam[var], axis=1)
        return np.mean(pred != y[var]), var.mean()
