# -*- coding: utf-8 -*-
# b62_01_nb.py: Naive Bayes sifirdan: Gauss ve multinomial,
# Laplace duzeltmesi, log-uzay, sklearn ile eslestirme, varsayim
# bozulmasi (kalibrasyon) ve NB / lojistik ogrenme egrisi.
import re
import numpy as np
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


# ---------- 1) Gauss naive Bayes (sifirdan) ----------
class GaussNB:
    """Her sinif ve her ozellik icin Gauss; sklearn ile ayni varyans
    duzeltmesi (var_smoothing * max varyans)."""

    def fit(self, X, y):
        self.sinif = np.unique(y)
        eps = 1e-9 * X.var(axis=0).max()  # sklearn'deki epsilon_
        self.log_prior = np.log([np.mean(y == c) for c in self.sinif])
        self.mu = np.array(
            [X[y == c].mean(axis=0) for c in self.sinif]
        )
        self.var = (
            np.array([X[y == c].var(axis=0) for c in self.sinif])
            + eps
        )
        return self

    def joint_log(self, X):
        """log p(y) + sum_j log N(x_j; mu_yj, var_yj), boyut n x C."""
        out = []
        for k in range(len(self.sinif)):
            ll = (
                -0.5 * np.log(2 * np.pi * self.var[k])
                - 0.5 * (X - self.mu[k]) ** 2 / self.var[k]
            )
            out.append(self.log_prior[k] + ll.sum(axis=1))
        return np.column_stack(out)

    def predict(self, X):
        return self.sinif[np.argmax(self.joint_log(X), axis=1)]


def gauss_deney():
    X, y = load_breast_cancer(return_X_y=True)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.3, random_state=62, stratify=y
    )
    mine = GaussNB().fit(Xtr, ytr)
    sk = GaussianNB().fit(Xtr, ytr)
    J1 = mine.joint_log(Xte)
    J2 = sk.predict_joint_log_proba(Xte)
    print("[Gauss] en buyuk log-fark:", float(np.abs(J1 - J2).max()))
    print(
        "[Gauss] dogruluk sifirdan:",
        round(float(np.mean(mine.predict(Xte) == yte)), 4),
    )
    print(
        "[Gauss] dogruluk sklearn :",
        round(float(np.mean(sk.predict(Xte) == yte)), 4),
    )


# ---------- 2) Multinomial NB ve Turkce metin ----------
SPAM_TRAIN = [
    "Tebrikler! Bedava hediye kazandınız, hemen tıklayın",
    "Ücretsiz kredi fırsatı yalnızca bugün geçerli",
    "Bedava bonus için hemen kaydol ve kazan",
    "Acil indirim! Bedava kargo için tıkla",
    "Ödülünüzü almak için hemen kaydolun",
    "Para kazanmanın en kolay yolu burada",
    "Sadece bugün özel fırsat, indirim tıkla",
    "Tebrikler, çekilişi kazandınız, ödül için kaydol",
    "Bedava kredi ve hediye için tıklayın",
    "İNDİRİM: bedava kargo, hemen kaydol",
]
NORMAL_TRAIN = [
    "Toplantı yarın saat onda başlıyor",
    "Proje raporunu cuma gününe kadar gönderir misin",
    "Yarın derse gelecek misin, notlar paylaşıldı",
    "Sunum dosyasını güncelledim, lütfen kontrol et",
    "Akşam yemeğe çıkalım mı",
    "Laboratuvar raporu için veri setini ekledim",
    "Hocanın ofis saati yarın öğleden sonra",
    "Kodu gözden geçirdim, birkaç yorum yazdım",
    "Vize sonuçları sisteme yüklendi",
    "Bu hafta sonu projeyi birlikte çalışalım",
]
SPAM_TEST = [
    "Bedava kredi için hemen tıkla",
    "Tebrikler, ödül kazandınız! Kaydol",
    "İNDİRİM fırsatı kaçmadan tıkla",
    "Hemen kaydol, bedava hediye",
]
NORMAL_TEST = [
    "Yarın toplantı için rapor gönderir misin",
    "Vize notları sisteme yüklendi mi",
    "Sunum için veri setini kontrol ettim",
    "Akşam projeyi birlikte gözden geçirelim",
]


def tokenize(s):
    """Turkce kucuk harf: once I->i ve İ->i, sonra lower()."""
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return re.findall(r"[a-zçğıöşü]+", s)


def tokenize_naive(s):
    """Yanlis yol: dogrudan lower(). 'İ' birlesik nokta uretir."""
    return re.findall(r"[a-zçğıöşü]+", s.lower())


class MultiNB:
    """Multinomial NB, Laplace (alpha) duzeltmeli, sifirdan."""

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y):
        self.sinif = np.unique(y)
        self.log_prior = np.log([np.mean(y == c) for c in self.sinif])
        sayim = np.array([X[y == c].sum(axis=0) for c in self.sinif])
        duz = sayim + self.alpha
        self.log_theta = np.log(duz) - np.log(
            duz.sum(axis=1, keepdims=True)
        )
        return self

    def joint_log(self, X):
        """log p(y) + sum_w x_w log theta_yw  (matris carpimi)."""
        return X @ self.log_theta.T + self.log_prior

    def predict(self, X):
        return self.sinif[np.argmax(self.joint_log(X), axis=1)]


def sozluk_ve_sayim(docs, sozluk):
    X = np.zeros((len(docs), len(sozluk)))
    for i, d in enumerate(docs):
        for w in tokenize(d):
            if w in sozluk:
                X[i, sozluk[w]] += 1
    return X


def metin_deney():
    docs = SPAM_TRAIN + NORMAL_TRAIN
    y = np.array([1] * len(SPAM_TRAIN) + [0] * len(NORMAL_TRAIN))
    test_docs = SPAM_TEST + NORMAL_TEST
    yt = np.array([1] * len(SPAM_TEST) + [0] * len(NORMAL_TEST))
    sozluk = {
        w: i
        for i, w in enumerate(
            sorted({w for d in docs for w in tokenize(d)})
        )
    }
    print("[Metin] sozluk boyutu:", len(sozluk))
    print("[Metin] 'indirim' var mi:", "indirim" in sozluk)
    print(
        "[Metin] naive lower:",
        tokenize_naive("İNDİRİM"),
        " dogru:",
        tokenize("İNDİRİM"),
    )
    X = sozluk_ve_sayim(docs, sozluk)
    Xt = sozluk_ve_sayim(test_docs, sozluk)
    mine = MultiNB(alpha=1.0).fit(X, y)
    sk = MultinomialNB(alpha=1.0).fit(X, y)
    print(
        "[Metin] log theta farki (sifirdan - sklearn):",
        float(np.abs(mine.log_theta - sk.feature_log_prob_).max()),
    )
    print(
        "[Metin] log-olasilik farki:",
        float(
            np.abs(
                mine.joint_log(Xt) - sk.predict_joint_log_proba(Xt)
            ).max()
        ),
    )
    print("[Metin] tahminler (sifirdan):", mine.predict(Xt).tolist())
    print("[Metin] dogru etiketler     :", yt.tolist())
    print(
        "[Metin] test dogrulugu:",
        float(np.mean(mine.predict(Xt) == yt)),
    )
    # Laplace etkisi: 'kredi' yalnizca spam'de geciyor
    w = sozluk["kredi"]
    for a in [0.0, 1.0]:
        with np.errstate(divide="ignore"):
            m = MultiNB(alpha=a).fit(X, y)
        print(
            "[Laplace] alpha=%.0f  log theta(kredi|normal)=%s"
            % (a, m.log_theta[0, w])
        )
    # Alt tasma: 500 kelimelik mesaj, her biri p=0,1
    p = np.full(500, 0.1)
    print("[Log] carpim 0,1^500 =", float(np.prod(p)))
    print(
        "[Log] log toplam     =", round(float(np.sum(np.log(p))), 3)
    )


def proba(J):
    """Log-olasilik matrisinden olasilik (log-toplam-exp kararli)."""
    J = J - J.max(axis=1, keepdims=True)
    P = np.exp(J)
    return P / P.sum(axis=1, keepdims=True)


def ece(p1, y, bins=10):
    """Beklenen kalibrasyon hatasi (guven araliklarina gore)."""
    guven = np.maximum(p1, 1 - p1)
    dogru = ((p1 >= 0.5).astype(int) == y).astype(float)
    kenar = np.linspace(0.5, 1.0, bins + 1)
    toplam = 0.0
    for a, b in zip(kenar[:-1], kenar[1:]):
        m = (
            (guven >= a) & (guven <= b)
            if a == 0.5
            else ((guven > a) & (guven <= b))
        )
        if m.any():
            toplam += m.mean() * abs(
                dogru[m].mean() - guven[m].mean()
            )
    return toplam


def iki_sinif(n, rho, rng):
    """Iki sinif, ortak kovaryans (rho). Sinif ortalamalari +-0,6."""
    y = rng.integers(0, 2, n)
    isaret = np.where(y == 1, 1.0, -1.0)[:, None]
    kov = np.array([[1.0, rho], [rho, 1.0]])
    X = 0.6 * isaret + rng.multivariate_normal([0, 0], kov, size=n)
    return X, y


def varsayim_deney():
    print("\n[Varsayim] 20 tohum, n_egitim=2000, n_test=4000")
    for rho in [0.0, 0.9]:
        sonuc = {"NB": [], "LR": []}
        for s in range(20):
            rng = np.random.default_rng(s)
            Xa, ya = iki_sinif(2000, rho, rng)
            Xb, yb = iki_sinif(4000, rho, rng)
            nb = GaussNB().fit(Xa, ya)
            lr = LogisticRegression(max_iter=1000).fit(Xa, ya)
            for ad, p1 in [
                ("NB", proba(nb.joint_log(Xb))[:, 1]),
                ("LR", lr.predict_proba(Xb)[:, 1]),
            ]:
                sonuc[ad].append(
                    [
                        np.mean((p1 >= 0.5) == yb),
                        np.mean((p1 - yb) ** 2),
                        ece(p1, yb),
                        np.mean(np.maximum(p1, 1 - p1)),
                    ]
                )
        for ad in ["NB", "LR"]:
            a = np.array(sonuc[ad])
            print(
                "rho=%.1f %s  dogruluk=%.4f  Brier=%.4f  ECE=%.4f"
                "  ort.guven=%.4f" % (rho, ad, *a.mean(axis=0))
            )


def varsayim_kopya():
    print("\n[Kopya] bagimsiz veri (rho=0), x1 kac kez kopyalaniyor")
    for k in [1, 2, 4, 8]:
        sonuc = []
        for s in range(20):
            rng = np.random.default_rng(100 + s)
            Xa, ya = iki_sinif(2000, 0.0, rng)
            Xb, yb = iki_sinif(4000, 0.0, rng)
            Xa2 = np.column_stack(
                [Xa[:, [0]].repeat(k, axis=1), Xa[:, 1]]
            )
            Xb2 = np.column_stack(
                [Xb[:, [0]].repeat(k, axis=1), Xb[:, 1]]
            )
            p1 = proba(GaussNB().fit(Xa2, ya).joint_log(Xb2))[:, 1]
            sonuc.append(
                [
                    np.mean((p1 >= 0.5) == yb),
                    np.mean((p1 - yb) ** 2),
                    ece(p1, yb),
                    np.mean(np.maximum(p1, 1 - p1)),
                ]
            )
        a = np.array(sonuc).mean(axis=0)
        print(
            "k=%d  dogruluk=%.4f  Brier=%.4f  ECE=%.4f  guven=%.4f"
            % (k, *a)
        )


def ogrenme_egrisi():
    X, y = load_breast_cancer(return_X_y=True)
    Xh, Xte, yh, yte = train_test_split(
        X, y, test_size=0.25, random_state=62, stratify=y
    )
    boyutlar = [10, 20, 40, 80, 160, 320]
    satirlar = ["n,nb_ort,nb_ss,lr_ort,lr_ss"]
    print("\n[Egri] n, NB ort (ss), LR ort (ss); 30 alt kume")
    for n in boyutlar:
        nb_a, lr_a = [], []
        for s in range(30):
            rng = np.random.default_rng(1000 * n + s)
            while True:
                idx = rng.choice(len(Xh), n, replace=False)
                if len(np.unique(yh[idx])) == 2:
                    break
            nb_a.append(
                np.mean(
                    GaussianNB().fit(Xh[idx], yh[idx]).predict(Xte)
                    == yte
                )
            )
            lr = make_pipeline(
                StandardScaler(), LogisticRegression(max_iter=1000)
            )
            lr_a.append(
                np.mean(lr.fit(Xh[idx], yh[idx]).predict(Xte) == yte)
            )
        nb_a, lr_a = np.array(nb_a), np.array(lr_a)
        print(
            "n=%3d  NB %.4f (%.4f)   LR %.4f (%.4f)"
            % (n, nb_a.mean(), nb_a.std(), lr_a.mean(), lr_a.std())
        )
        satirlar.append(
            "%d,%.5f,%.5f,%.5f,%.5f"
            % (n, nb_a.mean(), nb_a.std(), lr_a.mean(), lr_a.std())
        )
    with open(
        VERI + "/b62_nb_lr_ogrenme.csv", "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    print("== 1) Gauss NB ==")
    gauss_deney()
    print("\n== 2) Multinomial NB (Turkce metin) ==")
    metin_deney()
    print("\n== 3) Varsayim bozulmasi ==")
    varsayim_deney()
    varsayim_kopya()
    print("\n== 4) Ogrenme egrisi ==")
    ogrenme_egrisi()
