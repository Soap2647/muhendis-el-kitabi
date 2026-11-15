# -*- coding: utf-8 -*-
"""Deney 3: bolunmus conformal ve secici tahmin (risk-kapsam)."""

import numpy as np
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    topluluk_egit,
    softmax_np,
    logit_np,
    csv_yaz,
)

ALFALAR = [0.01, 0.05, 0.10, 0.20, 0.30]


def konformal_esik(p_cal, y_cal, alpha):
    """Sinif-temelli skor s = 1 - p(dogru sinif). Sonlu ornek
    duzeltmesi: k = ceil((n + 1)(1 - alpha)) inci kucuk skor."""
    n = len(y_cal)
    s = np.sort(1.0 - p_cal[np.arange(n), y_cal])
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return float(s[k - 1]) if k <= n else np.inf


def konformal_kume(p, q):
    """C(x) = {k : 1 - p_k(x) <= q}; boolean matris (n, K)."""
    return (1.0 - p) <= q


def risk_kapsam(guven, hatali, izgara):
    """Kabul oranina gore risk (kabul edilenlerde hata orani)."""
    n = len(hatali)
    out = []
    for k in izgara:
        m = max(1, int(np.ceil(k * n)))
        sec = np.argsort(-guven, kind="stable")[:m]
        out.append((k, hatali[sec].mean()))
    return out


def main():
    D = veri_hazirla()
    print(
        "Bolunme: egitim %d, dogrulama %d, kalibrasyon %d, test %d"
        % (len(D["ytr"]), len(D["yva"]), len(D["yca"]), len(D["yte"]))
    )
    izgara = np.round(np.linspace(1.0, 0.3, 15), 3)
    satirlar, rk, tekrar_say = [], [], []
    for s in SEEDS:
        ens = topluluk_egit(D, s)
        Pca = np.mean(
            [softmax_np(logit_np(m, D["Xca"])) for m in ens], 0
        )
        Pte = np.mean(
            [softmax_np(logit_np(m, D["Xte"])) for m in ens], 0
        )
        for a in ALFALAR:
            q = konformal_esik(Pca, D["yca"], a)
            K = konformal_kume(Pte, q)
            kap = K[np.arange(len(D["yte"])), D["yte"]].mean()
            boy = K.sum(1)
            satirlar.append(
                (
                    s,
                    a,
                    "%.4f" % kap,
                    "%.4f" % boy.mean(),
                    "%.4f" % (boy == 1).mean(),
                    "%.4f" % (1 - a),
                )
            )
        # secici tahmin: guven = maks. olasilik; alt. = kume boyu
        hatali = (Pte.argmax(1) != D["yte"]).astype(float)
        boy = konformal_kume(
            Pte, konformal_esik(Pca, D["yca"], 0.10)
        ).sum(1)
        for yon, anahtar in [
            ("maks_olasilik", Pte.max(1)),
            ("kume_boyu", -boy + Pte.max(1)),
        ]:
            for k, r in risk_kapsam(anahtar, hatali, izgara):
                rk.append((s, yon, "%.3f" % k, "%.4f" % r))
        if s == 0:
            # sonlu ornek: 200 rastgele kalibrasyon/test bolmesi
            P = np.r_[Pca, Pte]
            y = np.r_[D["yca"], D["yte"]]
            rng = np.random.default_rng(1)
            for _ in range(200):
                perm = rng.permutation(len(y))
                i_c, i_t = (
                    perm[: len(D["yca"])],
                    perm[len(D["yca"]) :],
                )
                q = konformal_esik(P[i_c], y[i_c], 0.10)
                K = konformal_kume(P[i_t], q)
                tekrar_say.append(
                    K[np.arange(len(i_t)), y[i_t]].mean()
                )
    print("\nalfa  nominal  kapsama(ort+-sd)  kume_boyu  tekil")
    for a in ALFALAR:
        r = np.array(
            [
                [float(x[2]), float(x[3]), float(x[4])]
                for x in satirlar
                if x[1] == a
            ]
        )
        print(
            "%.2f   %.2f     %.4f +- %.4f    %.3f      %.3f"
            % (
                a,
                1 - a,
                r[:, 0].mean(),
                r[:, 0].std(),
                r[:, 1].mean(),
                r[:, 2].mean(),
            )
        )
    t = np.array(tekrar_say)
    print("\n200 yeniden bolme (alfa = 0.10, tohum 0):")
    print("  kapsama ort = %.4f  sd = %.4f" % (t.mean(), t.std()))
    print(
        "  en dusuk = %.4f  %%5 = %.4f  %%95 = %.4f"
        % (t.min(), np.percentile(t, 5), np.percentile(t, 95))
    )
    print(
        "  nominal 0.90 altinda kalan bolme: %d / 200"
        % (t < 0.9).sum()
    )
    print("\nRisk-kapsam (tohum 0, maks_olasilik ve kume_boyu):")
    for yon in ["maks_olasilik", "kume_boyu"]:
        r = [x for x in rk if x[0] == 0 and x[1] == yon]
        for x in r[::4]:
            print("  %-14s kapsam %s  risk %s" % (yon, x[2], x[3]))
    csv_yaz(
        "b78_conformal.csv",
        [
            "tohum",
            "alfa",
            "kapsama",
            "kume_boyu",
            "tekil_oran",
            "nominal",
        ],
        satirlar,
    )
    csv_yaz(
        "b78_conformal_tekrar.csv",
        ["kapsama"],
        [("%.5f" % v,) for v in t],
    )
    csv_yaz(
        "b78_riskkapsam.csv",
        ["tohum", "yontem", "kapsam", "risk"],
        rk,
    )


if __name__ == "__main__":
    main()
