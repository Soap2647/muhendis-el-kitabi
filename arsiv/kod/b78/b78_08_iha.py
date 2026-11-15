# -*- coding: utf-8 -*-
"""Deney 8: calisma zamani guvence katmani (OOD + belirsizlik +
conformal + reddetme/geri donus) ile sentetik hedef akisi testi."""

import numpy as np
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    ood_uret,
    softmax_np,
    logit_np,
    feat_np,
    topluluk_egit,
    csv_yaz,
)
from b78_01_ood import mahalanobis_fit, mahalanobis_skor
from b78_03_conformal import konformal_esik

ALFA = 0.10
BOZULMA_SIGMA = 0.35


def H(q):
    return -np.sum(q * np.log(q + 1e-12), axis=-1)


def olcum(models, X, mu, prec):
    """Mahalanobis (ilk uye, ozellik uzayi), ortalama olasilik ve
    epistemik belirsizlik (karsilikli bilgi, MI)."""
    P = np.stack([softmax_np(logit_np(m, X)) for m in models])
    ort = P.mean(0)
    mi = H(ort) - H(P).mean(0)
    mah = mahalanobis_skor(feat_np(models[0], X), mu, prec)
    return ort, mah, mi


def main():
    D = veri_hazirla()
    gur, lek = ood_uret(len(D["Xte"]))
    satirlar = []
    print(
        "tohum politika        ID    bozuk   OOD    tehlikeli  hata"
    )
    for s in SEEDS:
        ens = topluluk_egit(D, s)
        mu, prec = mahalanobis_fit(
            feat_np(ens[0], D["Xtr"]), D["ytr"]
        )
        rng = np.random.default_rng(50 + s)
        Xb = np.clip(
            D["Xte"] + rng.normal(0, BOZULMA_SIGMA, D["Xte"].shape),
            0,
            1,
        )
        Xo = np.r_[gur[:180], lek[:180]]
        X = np.r_[D["Xte"], Xb, Xo].astype(np.float32)
        tur = np.r_[
            np.zeros(len(D["Xte"])),
            np.ones(len(Xb)),
            2 * np.ones(len(Xo)),
        ]
        y = np.r_[D["yte"], D["yte"], -np.ones(len(Xo), int)]
        # esikler yalnizca dogrulama (ID) ve kalibrasyon kumesinden
        Pva, Dva, Mva = olcum(ens, D["Xva"], mu, prec)
        Pca, _, _ = olcum(ens, D["Xca"], mu, prec)
        e_esik = np.percentile(Dva, 5)
        m_esik = np.percentile(Mva, 95)
        q = konformal_esik(Pca, D["yca"], ALFA)
        P, D2, M = olcum(ens, X, mu, prec)
        kume = (1.0 - P) <= q
        boy = kume.sum(1)
        hata = (P.argmax(1) != y) & (tur < 2)
        kural = {
            "koruma yok": np.ones(len(X), bool),
            "OOD": D2 >= e_esik,
            "OOD+MI": (D2 >= e_esik) & (M <= m_esik),
            "OOD+MI+konf.": (D2 >= e_esik)
            & (M <= m_esik)
            & (boy == 1),
        }
        for ad, kab in kural.items():
            k_id = kab[tur == 0].mean()
            k_bz = kab[tur == 1].mean()
            k_oo = kab[tur == 2].mean()
            # tehlikeli kabul: yanlis sinif kabulu veya OOD kabulu
            tehlikeli = np.mean(kab & (hata | (tur == 2)))
            kabul_hata = tehlikeli / max(kab.mean(), 1e-12)
            satirlar.append(
                (
                    s,
                    ad,
                    "%.4f" % k_id,
                    "%.4f" % k_bz,
                    "%.4f" % k_oo,
                    "%.4f" % tehlikeli,
                    "%.4f" % kabul_hata,
                )
            )
            print(
                "%5d %-13s %.3f    %.3f       %.3f     %.3f"
                "     %.3f"
                % (s, ad, k_id, k_bz, k_oo, tehlikeli, kabul_hata)
            )
    csv_yaz(
        "b78_iha.csv",
        [
            "tohum",
            "politika",
            "kabul_id",
            "kabul_bozuk",
            "kabul_ood",
            "tehlikeli",
            "kabul_hata",
        ],
        satirlar,
    )


if __name__ == "__main__":
    main()
