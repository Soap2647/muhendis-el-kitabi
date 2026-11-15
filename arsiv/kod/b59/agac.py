# agac.py -- sifirdan karar agaci (CART): siniflandirma ve regresyon
import numpy as np


class Dugum:
    def __init__(self, derinlik, n, deger):
        self.derinlik = derinlik   # kokten uzaklik
        self.n = n                 # bu dugume dusen ornek sayisi
        self.deger = deger         # yaprak: olasilik veya ortalama
        self.ozellik = None        # bolunen ozellik indeksi
        self.esik = None           # bolme esigi: x <= esik -> sol
        self.sol = None
        self.sag = None


def saf_matris(C, olcut):
    # C: (m, k) sinif sayilari. Her satir icin safsizlik.
    n = C.sum(axis=1, keepdims=True)
    p = C / np.maximum(n, 1)
    if olcut == "gini":
        return 1.0 - np.sum(p * p, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(p > 0, p * np.log2(p), 0.0)
    return -np.sum(t, axis=1)


def en_iyi_bolme_siniflama(x, y, k, olcut, min_yaprak):
    # Sirala, sonra kumulatif sayimla tum esikleri tek geciste bul.
    s = np.argsort(x, kind="stable")
    xs, ys = x[s], y[s]
    n = len(xs)
    E = np.zeros((n, k))
    E[np.arange(n), ys] = 1.0
    sol = np.cumsum(E, axis=0)[:-1]        # ilk i+1 ornek sola
    sag = E.sum(axis=0) - sol
    nl = np.arange(1, n, dtype=float)
    nr = n - nl
    ust = saf_matris(E.sum(axis=0, keepdims=True), olcut)[0]
    agirlikli = (nl * saf_matris(sol, olcut)
                 + nr * saf_matris(sag, olcut)) / n
    kazanc = ust - agirlikli
    gecerli = ((xs[1:] > xs[:-1]) & (nl >= min_yaprak)
               & (nr >= min_yaprak))
    kazanc = np.where(gecerli, kazanc, -np.inf)
    i = int(np.argmax(kazanc))
    if not np.isfinite(kazanc[i]):
        return None
    return kazanc[i], (xs[i] + xs[i + 1]) / 2


def en_iyi_bolme_regresyon(x, y, min_yaprak):
    # MSE: kareler toplamini (SSE) kumulatif toplamlarla hesapla.
    s = np.argsort(x, kind="stable")
    xs, ys = x[s], y[s]
    n = len(xs)
    nl = np.arange(1, n, dtype=float)
    nr = n - nl
    T1, T2 = ys.sum(), (ys * ys).sum()
    sl, kl = np.cumsum(ys)[:-1], np.cumsum(ys * ys)[:-1]
    sr, kr = T1 - sl, T2 - kl
    sse_ust = T2 - T1 * T1 / n
    sse = (kl - sl * sl / nl) + (kr - sr * sr / nr)
    kazanc = sse_ust - sse
    gecerli = ((xs[1:] > xs[:-1]) & (nl >= min_yaprak)
               & (nr >= min_yaprak))
    kazanc = np.where(gecerli, kazanc, -np.inf)
    i = int(np.argmax(kazanc))
    if not np.isfinite(kazanc[i]):
        return None
    return kazanc[i], (xs[i] + xs[i + 1]) / 2


class KararAgaci:
    def __init__(self, mod="sinif", olcut="gini", max_derinlik=None,
                 min_bolme=2, min_yaprak=1, max_ozellik=None,
                 rng=None, k=None):
        self.mod = mod
        self.olcut = olcut
        self.max_derinlik = max_derinlik
        self.min_bolme = min_bolme
        self.min_yaprak = min_yaprak
        self.max_ozellik = max_ozellik
        if rng is None:
            rng = np.random.default_rng(0)
        self.rng = rng
        self.k = k

    def fit(self, X, y):
        if self.mod == "sinif" and self.k is None:
            self.k = int(y.max()) + 1
        self.kok = self._buyut(X, y, 0)
        return self

    def _yaprak(self, y):
        if self.mod == "sinif":
            return np.bincount(y, minlength=self.k) / len(y)
        return float(y.mean())

    def _saf(self, y):
        if self.mod == "sinif":
            return np.all(y == y[0])
        return np.ptp(y) == 0

    def _bol(self, x, y):
        if self.mod == "sinif":
            return en_iyi_bolme_siniflama(x, y, self.k,
                                          self.olcut, self.min_yaprak)
        return en_iyi_bolme_regresyon(x, y, self.min_yaprak)

    def _buyut(self, X, y, d):
        dugum = Dugum(d, len(y), self._yaprak(y))
        if (len(y) < self.min_bolme or self._saf(y)
                or (self.max_derinlik is not None
                    and d >= self.max_derinlik)):
            return dugum
        adaylar = np.arange(X.shape[1])
        if self.max_ozellik is not None:
            adaylar = self.rng.choice(adaylar, self.max_ozellik,
                                      replace=False)
        en = None
        for j in adaylar:
            sonuc = self._bol(X[:, j], y)
            if sonuc is not None and (en is None or sonuc[0] > en[0]):
                en = (sonuc[0], j, sonuc[1])
        if en is None or en[0] <= 1e-12:
            return dugum
        _, j, t = en
        sol = X[:, j] <= t
        dugum.ozellik, dugum.esik = j, t
        dugum.sol = self._buyut(X[sol], y[sol], d + 1)
        dugum.sag = self._buyut(X[~sol], y[~sol], d + 1)
        return dugum

    def _yaprak_bul(self, x):
        d = self.kok
        while d.sol is not None:
            d = d.sol if x[d.ozellik] <= d.esik else d.sag
        return d

    def olasilik(self, X):
        return np.array([self._yaprak_bul(x).deger for x in X])

    def tahmin(self, X):
        if self.mod == "sinif":
            return np.argmax(self.olasilik(X), axis=1)
        return self.olasilik(X)

    def yaprak_sayisi(self):
        def say(d):
            if d.sol is None:
                return 1
            return say(d.sol) + say(d.sag)
        return say(self.kok)

    def derinlik(self):
        def en_derin(d):
            if d.sol is None:
                return d.derinlik
            return max(en_derin(d.sol), en_derin(d.sag))
        return en_derin(self.kok)
