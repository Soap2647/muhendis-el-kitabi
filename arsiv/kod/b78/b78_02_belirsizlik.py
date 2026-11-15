# -*- coding: utf-8 -*-
"""Deney 2: kalibrasyon ve belirsizlik (sicaklik, MC, topluluk)."""

import numpy as np
from scipy.optimize import minimize_scalar
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    ood_uret,
    MLP,
    egit,
    softmax_np,
    logit_np,
    topluluk_egit,
    ece,
    guvenilirlik_kutulari,
    auroc,
    csv_yaz,
)


def sicaklik_bul(z_va, y_va):
    """Dogrulama kumesinde NLL'i en kucuk yapan T."""

    def nll(log_t):
        p = softmax_np(z_va / np.exp(log_t))
        return -np.mean(np.log(p[np.arange(len(y_va)), y_va] + 1e-12))

    r = minimize_scalar(
        nll, bounds=(np.log(0.05), np.log(10.0)), method="bounded"
    )
    return float(np.exp(r.x))


def mc_dropout(model, X, T=30, seed=0):
    """Egitimdeki dropout'u test aninda acik tut; T gecis."""
    import torch

    torch.manual_seed(seed + 7)
    model.train()
    with torch.no_grad():
        P = [
            softmax_np(model(torch.tensor(X)).numpy())
            for _ in range(T)
        ]
    model.eval()
    return np.stack(P)


def ayristir(P):
    """P: (T, n, K). Toplam = H[ortalama]; aleatorik = ort(H);
    epistemik = toplam - aleatorik (karsilikli bilgi)."""

    def H(q):
        return -np.sum(q * np.log(q + 1e-12), axis=-1)

    ort = P.mean(0)
    toplam = H(ort)
    ale = H(P).mean(0)
    return ort, ale, toplam - ale


def main():
    D = veri_hazirla()
    gur, lek = ood_uret(len(D["Xte"]))
    Xo = np.r_[gur, lek]
    satirlar, kutular = [], []
    print("yontem         acc    ECE    AUROC(guven)  AUROC(epi)")
    for s in SEEDS:
        base = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        zva = logit_np(base, D["Xva"])
        T = sicaklik_bul(zva, D["yva"])
        ens = topluluk_egit(D, s)
        sonuc = {}
        # tek model
        p_te = softmax_np(logit_np(base, D["Xte"]))
        p_oo = softmax_np(logit_np(base, Xo))
        sonuc["Tek model"] = (p_te, p_oo, None, None)
        # sicaklik olcekleme
        sonuc["Sicaklik"] = (
            softmax_np(logit_np(base, D["Xte"]) / T),
            softmax_np(logit_np(base, Xo) / T),
            None,
            None,
        )
        # MC dropout
        Pt = mc_dropout(base, D["Xte"])
        Po = mc_dropout(base, Xo)
        ort_t, ale_t, epi_t = ayristir(Pt)
        ort_o, ale_o, epi_o = ayristir(Po)
        sonuc["MC dropout"] = (
            ort_t,
            ort_o,
            (ale_t, epi_t),
            (ale_o, epi_o),
        )
        # derin topluluk (M = 5)
        Et = np.stack(
            [softmax_np(logit_np(m, D["Xte"])) for m in ens]
        )
        Eo = np.stack([softmax_np(logit_np(m, Xo)) for m in ens])
        ort_t, ale_t, epi_t = ayristir(Et)
        ort_o, ale_o, epi_o = ayristir(Eo)
        sonuc["Topluluk"] = (
            ort_t,
            ort_o,
            (ale_t, epi_t),
            (ale_o, epi_o),
        )
        n_te = len(D["Xte"])
        for yon, (pt, po, bt, bo) in sonuc.items():
            acc = (pt.argmax(1) == D["yte"]).mean()
            e = ece(pt, D["yte"])
            a_g = auroc(pt.max(1), po.max(1))
            if bt is not None:
                a_e = auroc(-bt[1], -bo[1])
                ale_id, epi_id = bt[0].mean(), bt[1].mean()
                ale_ood, epi_ood = bo[0].mean(), bo[1].mean()
            else:
                a_e, ale_id, epi_id, ale_ood, epi_ood = (
                    "",
                    "",
                    "",
                    "",
                    "",
                )
            satirlar.append(
                (
                    s,
                    yon,
                    "%.4f" % acc,
                    "%.4f" % e,
                    "%.4f" % a_g,
                    "%.4f" % a_e if a_e != "" else "",
                    "%.5f" % ale_id if ale_id != "" else "",
                    "%.5f" % epi_id if epi_id != "" else "",
                    "%.5f" % ale_ood if ale_ood != "" else "",
                    "%.5f" % epi_ood if epi_ood != "" else "",
                )
            )
            if s == 0:
                for lo, hi, g, d, k in guvenilirlik_kutulari(
                    pt, D["yte"]
                ):
                    kutular.append(
                        (
                            yon,
                            "%.4f" % lo,
                            "%.4f" % hi,
                            "%.4f" % g,
                            "%.4f" % d,
                            k,
                        )
                    )
            ae = "%.3f" % a_e if a_e != "" else "   -  "
            print(
                "%-13s %.3f  %.4f  %.3f         %s   (tohum %d)"
                % (yon, acc, e, a_g, ae, s)
            )
        print("  sicaklik T =", round(T, 3), " test n =", n_te)
    print("\nOrtalama +- sapma (3 tohum):")
    for yon in ["Tek model", "Sicaklik", "MC dropout", "Topluluk"]:
        r = [x for x in satirlar if x[1] == yon]
        ec = np.array([float(x[3]) for x in r])
        ag = np.array([float(x[4]) for x in r])
        ae = [float(x[5]) for x in r if x[5] != ""]
        txt = "%.3f +- %.3f" % (ag.mean(), ag.std())
        if ae:
            txt += "  epi %.3f +- %.3f" % (np.mean(ae), np.std(ae))
        print(
            "%-11s ECE %.4f +- %.4f  AUROC %s"
            % (yon, ec.mean(), ec.std(), txt)
        )
    csv_yaz(
        "b78_belirsizlik.csv",
        [
            "tohum",
            "yontem",
            "acc",
            "ece",
            "auroc_guven",
            "auroc_epi",
            "ale_id",
            "epi_id",
            "ale_ood",
            "epi_ood",
        ],
        satirlar,
    )
    csv_yaz(
        "b78_kalibrasyon.csv",
        ["yontem", "alt", "ust", "guven", "dogruluk", "sayi"],
        kutular,
    )


if __name__ == "__main__":
    main()
