# -*- coding: utf-8 -*-
"""Deney 5: sertifikali saglamlik. (A) rastgele duzgunlestirme,
(B) IBP: sifirdan sinir yayilimi, dogrulama ve IBP egitimi."""

import numpy as np
import torch
import torch.nn.functional as F
from scipy.stats import beta, norm
from b78_ortak import SEEDS, veri_hazirla, MLP, egit, pgd, csv_yaz

SIGMA = 0.25  # Gauss gurultu olcegi (piksel birimi, L2)
IBP_EPS = 0.03  # IBP egitiminde L-inf yaricapi
EPS_IBP = [0.005, 0.01, 0.02, 0.03]


def gurultu_kayip(model, xb, yb, ep, E):
    xn = xb + SIGMA * torch.randn_like(xb)
    return F.cross_entropy(model(xn), yb)


def ibp_torch(model, x, eps):
    """Egitim icin tensor surumu: [x - eps, x + eps] kutusunun
    logit sinirlari. Her dogrusal katmanda orta/yaricap."""
    lo, hi = x - eps, x + eps
    for lin, relu in [
        (model.f1, True),
        (model.f2, True),
        (model.cik, False),
    ]:
        orta, yar = (hi + lo) / 2, (hi - lo) / 2
        orta = lin(orta)
        yar = yar @ lin.weight.abs().T
        lo, hi = orta - yar, orta + yar
        if relu:
            lo, hi = lo.clamp(min=0), hi.clamp(min=0)
    return lo, hi


def ibp_kayip(model, xb, yb, ep, E):
    """Gowal tarzi karma kayip: kappa 1 -> 0.5, eps 0 -> IBP_EPS."""
    r = min(1.0, ep / (0.5 * E))
    eps, kap = IBP_EPS * r, 1.0 - 0.5 * r
    lo, hi = ibp_torch(model, xb, eps)
    kotu = torch.where(F.one_hot(yb, 10).bool(), lo, hi)
    return kap * F.cross_entropy(model(xb), yb) + (
        1 - kap
    ) * F.cross_entropy(kotu, yb)


def ibp_np(agirliklar, lo, hi):
    """Sifirdan numpy IBP: W, b katman listesi; ReLU sonrasi."""
    son = len(agirliklar) - 1
    for k, (W, b) in enumerate(agirliklar):
        orta, yar = (lo + hi) / 2, (hi - lo) / 2
        orta = orta @ W.T + b
        yar = yar @ np.abs(W).T
        lo, hi = orta - yar, orta + yar
        if k < son:
            lo, hi = np.maximum(lo, 0), np.maximum(hi, 0)
    return lo, hi


def agirliklar_np(model):
    return [
        (
            l.weight.detach().double().numpy(),
            l.bias.detach().double().numpy(),
        )
        for l in [model.f1, model.f2, model.cik]
    ]


def sertifiye(lo, hi, y):
    """Dogru sinifin alt siniri, diger siniflarin ust sinirlarindan
    buyukse ornek sertifikalidir."""
    idx = np.arange(len(y))
    ust = hi.copy()
    ust[idx, y] = -np.inf
    return lo[idx, y] > ust.max(1)


def rs_sertifika(model, x, n0=100, n=1000, alfa=0.001, rng=None):
    """Cohen (2019) yaklasimi: secim ornekleri ile sinifi sec,
    tahmin ornekleriyle pA alt sinirini Clopper-Pearson ile bul."""

    def oy(k):
        g = rng.normal(0, SIGMA, size=(k, 64)).astype(np.float32)
        with torch.no_grad():
            tahmin = model(torch.tensor(x + g)).argmax(1).numpy()
        return np.bincount(tahmin, minlength=10)

    c = int(oy(n0).argmax())
    k = int(oy(n)[c])
    pa = beta.ppf(alfa, k, n - k + 1) if k > 0 else 0.0
    if pa < 0.5:
        return -1, 0.0  # cekimser
    return c, SIGMA * norm.ppf(pa)


def main():
    D = veri_hazirla()
    Xe, ye = D["Xte"][:100], D["yte"][:100]
    satirlar = []
    print(
        "A) Rastgele duzgunlestirme (sigma = %.2f, 100 test ornegi)"
        % SIGMA
    )
    r_izg = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    for s in SEEDS:
        m = egit(
            MLP(0.0), D["Xtr"], D["ytr"], seed=s, kayip=gurultu_kayip
        )
        rng = np.random.default_rng(s)
        sonuc = [
            rs_sertifika(m, Xe[i : i + 1], rng=rng)
            for i in range(len(Xe))
        ]
        c = np.array([a for a, _ in sonuc])
        R = np.array([b for _, b in sonuc])
        dogru = c == ye
        cek = []
        for r in r_izg:
            v = float(np.mean(dogru & (R >= r)))
            cek.append(v)
            satirlar.append((s, "rs", "%.2f" % r, "%.4f" % v))
        print(
            "  tohum %d: sertifikali =" % s,
            " ".join("%.2f" % v for v in cek),
            " cekimser = %d" % int((c == -1).sum()),
        )
    print("  r sirasi: " + " ".join("%.1f" % r for r in r_izg))
    print(
        "\nB1) Sifirdan IBP: el ornegi ag (2 girdi, 2 gizli, 2 cikti)"
    )
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]])
    b1 = np.array([0.0, -0.2])
    W2 = np.array([[1.0, 1.0], [-1.0, 0.5]])
    b2 = np.zeros(2)
    el = [(W1, b1), (W2, b2)]
    x0 = np.array([[0.6, 0.4]])
    for eps in [0.10, 0.15]:
        lo, hi = ibp_np(el, x0 - eps, x0 + eps)
        marj_lo = lo[0, 0] - hi[0, 1]
        # kaba kuvvet: 401 x 401 izgarada gercek minimum marj
        g = np.linspace(-eps, eps, 401)
        A, B = np.meshgrid(g, g)
        P = np.stack([x0[0, 0] + A.ravel(), x0[0, 1] + B.ravel()], 1)
        h = np.maximum(P @ W1.T + b1, 0)
        z = h @ W2.T + b2
        kaba = (z[:, 0] - z[:, 1]).min()
        print(
            "  eps=%.2f  IBP alt marj=%+.4f  "
              "kaba kuvvet min marj=%+.4f"
            % (eps, marj_lo, kaba)
        )
    print("\nB2) Dogrulama: sinirlar gercek cikislari kapsiyor mu?")
    rng = np.random.default_rng(0)
    base = egit(MLP(0.0), D["Xtr"], D["ytr"], seed=0)
    ag = agirliklar_np(base)
    ihlal, genislik = 0, []
    for i in range(20):
        x = D["Xte"][i : i + 1].astype(np.float64)
        lo, hi = ibp_np(ag, x - 0.02, x + 0.02)
        U = x + rng.uniform(-0.02, 0.02, size=(5000, 64))
        Z = ibp_np(ag, U, U)[0]
        ihlal += int(np.sum((Z < lo - 1e-9) | (Z > hi + 1e-9)))
        genislik.append(float(np.mean(hi - lo)))
    print(
        "  20 ornek x 5000 rastgele nokta: sinir ihlali = %d" % ihlal
    )
    print(
        "  ortalama kutu genisligi (logit): %.3f" % np.mean(genislik)
    )
    Zt = ibp_torch(base, torch.tensor(D["Xte"][:50]), 0.02)
    lo_n, hi_n = ibp_np(
        ag,
        D["Xte"][:50].astype(np.float64) - 0.02,
        D["Xte"][:50].astype(np.float64) + 0.02,
    )
    fark = max(
        np.abs(Zt[0].detach().numpy() - lo_n).max(),
        np.abs(Zt[1].detach().numpy() - hi_n).max(),
    )
    print("  torch ve numpy IBP en buyuk fark = %.2e" % fark)
    print(
        "\nB3) IBP egitimi (eps_egitim = %.2f) ve sertifikali "
        "dogruluk" % IBP_EPS
    )
    print(
        "tohum model     temiz "
        + " ".join("c%.3f" % e for e in EPS_IBP)
        + " PGD0.02"
    )
    for s in SEEDS:
        for ad, kay in [("standart", None), ("IBP", ibp_kayip)]:
            if kay is None:
                m = egit(MLP(0.0), D["Xtr"], D["ytr"], seed=s)
            else:
                m = egit(
                    MLP(0.0), D["Xtr"], D["ytr"], seed=s, kayip=kay
                )
            ag = agirliklar_np(m)
            temiz = float(
                np.mean(
                    np.argmax(
                        ibp_np(
                            ag,
                            D["Xte"].astype(np.float64),
                            D["Xte"].astype(np.float64),
                        )[0],
                        1,
                    )
                    == D["yte"]
                )
            )
            cert = []
            for e in EPS_IBP:
                lo, hi = ibp_np(ag, D["Xte"] - e, D["Xte"] + e)
                c = sertifiye(lo, hi, D["yte"])
                cert.append(float(c.mean()))
                satirlar.append(
                    (s, ad, "%.3f" % e, "%.4f" % c.mean())
                )
            Xp = pgd(m, D["Xte"], D["yte"], 0.02, adim_say=40)
            pg = float(
                (
                    np.argmax(
                        ibp_np(
                            ag,
                            Xp.astype(np.float64),
                            Xp.astype(np.float64),
                        )[0],
                        1,
                    )
                    == D["yte"]
                ).mean()
            )
            print(
                "%5d %-9s %.3f  " % (s, ad, temiz)
                + "  ".join("%.3f   " % v for v in cert)
                + "%.3f" % pg
            )
    csv_yaz(
        "b78_rs_ibp.csv",
        ["tohum", "yontem", "r_veya_eps", "deger"],
        satirlar,
    )


if __name__ == "__main__":
    main()
