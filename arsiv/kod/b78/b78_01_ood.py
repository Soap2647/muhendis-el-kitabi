# -*- coding: utf-8 -*-
"""Deney 1: dagilim disi (OOD) skorlari: MSP, enerji, Mahalanobis."""

import numpy as np
from scipy.special import logsumexp
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    ood_uret,
    MLP,
    egit,
    softmax_np,
    logit_np,
    feat_np,
    auroc,
    fpr95,
    csv_yaz,
)


def mahalanobis_fit(Ftr, ytr):
    """Sinif ortalamalari + ortak kovaryans (Bolum 61, GMM)."""
    mu = np.stack([Ftr[ytr == c].mean(0) for c in range(10)])
    artik = Ftr - mu[ytr]
    sigma = artik.T @ artik / len(Ftr)
    prec = np.linalg.pinv(sigma + 1e-3 * np.eye(sigma.shape[0]))
    return mu, prec


def mahalanobis_skor(Fz, mu, prec):
    """En yakin sinifa karesel uzaklik; yuksek = icerida."""
    d = []
    for c in range(10):
        r = Fz - mu[c]
        d.append(np.einsum("ij,jk,ik->i", r, prec, r))
    return -np.min(np.stack(d, axis=1), axis=1)


def skorlar(model, X, mu, prec):
    z = logit_np(model, X)
    return {
        "MSP": softmax_np(z).max(1),
        "Enerji": logsumexp(z, axis=1),
        "Mahalanobis": mahalanobis_skor(feat_np(model, X), mu, prec),
    }


def main():
    D = veri_hazirla()
    gur, lek = ood_uret(len(D["Xte"]))
    turler = {
        "gurultu": gur,
        "leke": lek,
        "birlesik": np.r_[gur, lek],
    }
    satirlar, dagilim = [], []
    print("tohum  test_dogruluk")
    for s in SEEDS:
        model = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        acc = (logit_np(model, D["Xte"]).argmax(1) == D["yte"]).mean()
        print("%5d  %13.4f" % (s, acc))
        Ftr = feat_np(model, D["Xtr"])
        mu, prec = mahalanobis_fit(Ftr, D["ytr"])
        s_id = skorlar(model, D["Xte"], mu, prec)
        for tur, Xo in turler.items():
            s_ood = skorlar(model, Xo, mu, prec)
            for yon in s_id:
                a = auroc(s_id[yon], s_ood[yon])
                f = fpr95(s_id[yon], s_ood[yon])
                satirlar.append((s, yon, tur, "%.4f" % a, "%.4f" % f))
                if tur == "birlesik" and s == 0:
                    dagilim += [(yon, "id", v) for v in s_id[yon]]
                    dagilim += [(yon, "ood", v) for v in s_ood[yon]]
    print("\nOOD ayrisma (birlesik, 3 tohum ortalama +- sapma)")
    print("yontem        AUROC          FPR@95")
    for yon in ["MSP", "Enerji", "Mahalanobis"]:
        a = np.array(
            [
                float(r[3])
                for r in satirlar
                if r[1] == yon and r[2] == "birlesik"
            ]
        )
        f = np.array(
            [
                float(r[4])
                for r in satirlar
                if r[1] == yon and r[2] == "birlesik"
            ]
        )
        print(
            "%-12s  %.3f +- %.3f   %.3f +- %.3f"
            % (yon, a.mean(), a.std(), f.mean(), f.std())
        )
    print("\nOOD turu bazinda AUROC (3 tohum ortalama):")
    for tur in turler:
        for yon in ["MSP", "Enerji", "Mahalanobis"]:
            a = [
                float(r[3])
                for r in satirlar
                if r[1] == yon and r[2] == tur
            ]
            print("%-9s %-12s %.3f" % (tur, yon, np.mean(a)))
    csv_yaz(
        "b78_ood_auroc.csv",
        ["tohum", "yontem", "ood_turu", "auroc", "fpr95"],
        satirlar,
    )
    csv_yaz(
        "b78_ood_skor.csv",
        ["yontem", "grup", "skor"],
        [(a, b, "%.6f" % c) for a, b, c in dagilim],
    )


if __name__ == "__main__":
    main()
