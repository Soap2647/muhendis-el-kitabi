# -*- coding: utf-8 -*-
"""Deney 4: FGSM/PGD ile saglamlik olcumu, gradyan maskeleme
ornegi ve PGD ile cekismeli egitim (degerlendirme amacli)."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from b78_ortak import (
    SEEDS,
    veri_hazirla,
    MLP,
    egit,
    pgd,
    dogruluk,
    csv_yaz,
)

EPSLER = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
AT_EPS, AT_ADIM = 0.10, 7


class Olcekli(nn.Module):
    """Logitleri k ile carpar: argmax degismez, softmax doyar."""

    def __init__(self, m, k):
        super().__init__()
        self.m, self.k = m, k

    def forward(self, x):
        return self.m(x) * self.k


def at_kayip(model, xb, yb, ep, E):
    """Madry tarzi: her grupta PGD ornegiyle egit."""
    xa = pgd(
        model,
        xb.numpy(),
        yb.numpy(),
        AT_EPS,
        adim_say=AT_ADIM,
        seed=int(np.random.randint(10**6)),
    )
    model.train()
    return F.cross_entropy(model(torch.tensor(xa)), yb)


def eps_egrisi(model, X, y, saldiri, kayip="ce"):
    out = []
    for e in EPSLER:
        if e == 0.0:
            out.append(dogruluk(model, X, y))
            continue
        if saldiri == "FGSM":
            Xa = pgd(
                model,
                X,
                y,
                e,
                adim_say=1,
                adim=e,
                rastgele=False,
                kayip=kayip,
            )
        else:
            Xa = pgd(model, X, y, e, adim_say=40, kayip=kayip)
        out.append(dogruluk(model, Xa, y))
    return out


def main():
    D = veri_hazirla()
    X, y = D["Xte"], D["yte"]
    satirlar = []
    print("1) Standart model: eps'a gore dogruluk (ce kaybi)")
    print("tohum saldiri  " + "  ".join("%.2f" % e for e in EPSLER))
    for s in SEEDS:
        std = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        for sal in ["FGSM", "PGD"]:
            c = eps_egrisi(std, X, y, sal)
            print(
                "%5d %-6s " % (s, sal)
                + "  ".join("%.3f" % v for v in c)
            )
            for e, v in zip(EPSLER, c):
                satirlar.append((s, "standart", sal, e, "%.4f" % v))
    print("\n2) Gradyan maskeleme ornegi (tohum 0, k = 10^4)")
    std = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=0)
    mas = Olcekli(std, 1e4)
    xt, yt = torch.tensor(X), torch.tensor(y)
    xt.requires_grad_(True)
    kayip = -torch.log(
        torch.softmax(mas(xt), 1).gather(1, yt[:, None]).squeeze(1)
    )
    (gx,) = torch.autograd.grad(kayip.sum(), xt)
    sifir = float((gx.abs().sum(1) == 0).float().mean())
    print(
        "  naif kaybin girdi gradyani tam sifir orani: %.3f" % sifir
    )
    for ad, mod, sal_kay, rast, a in [
        ("standart", std, "ce", False, 1),
        ("maskeli", mas, "naif", False, 1),
        ("maskeli", mas, "naif", True, 40),
        ("maskeli", mas, "marj", True, 40),
    ]:
        for e in [0.05, 0.10]:
            Xa = pgd(
                mod,
                X,
                y,
                e,
                adim_say=a,
                kayip=sal_kay,
                rastgele=rast,
                adim=(e if a == 1 else None),
            )
            v = dogruluk(mod, Xa, y)
            ad2 = "FGSM" if a == 1 else "PGD"
            if sal_kay == "naif":
                ad2 += "-naif"
            elif sal_kay == "marj":
                ad2 += "-marj"
            print(
                "  %-8s %-10s eps=%.2f  dogruluk=%.3f"
                % (ad, ad2, e, v)
            )
            satirlar.append(
                (0, "maskeleme_" + ad, ad2, e, "%.4f" % v)
            )
    print("\n3) PGD ile cekismeli egitim (eps = 0.10, 7 adim)")
    print("tohum  model     temiz   eps=0.05  eps=0.10  eps=0.20")
    for s in SEEDS:
        at = egit(
            MLP(0.2), D["Xtr"], D["ytr"], seed=s, kayip=at_kayip
        )
        std = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=s)
        for ad, m in [("standart", std), ("PGD-AT", at)]:
            c = eps_egrisi(m, X, y, "PGD")
            print(
                "%5d  %-8s %.3f   %.3f    %.3f    %.3f"
                % (s, ad, c[0], c[2], c[3], c[5])
            )
            for e, v in zip(EPSLER, c):
                satirlar.append((s, ad, "PGD", e, "%.4f" % v))
    csv_yaz(
        "b78_saglamlik.csv",
        ["tohum", "model", "saldiri", "eps", "dogruluk"],
        satirlar,
    )


if __name__ == "__main__":
    main()
