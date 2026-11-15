# -*- coding: utf-8 -*-
"""Deney 6: aciklama yontemleri: gradyan x girdi, entegre gradyan,
Shapley (tam ve ornekleme), aciklamanin sanity kontrolu."""

import copy
import itertools
import math
import numpy as np
import torch
from scipy.stats import spearmanr
from b78_ortak import SEEDS, veri_hazirla, MLP, egit, csv_yaz


def z_sinif(model, X, c):
    """Tahmin edilen sinifin logiti (torch, gradyan icin)."""
    return model(X)[:, c]


def gradyan(model, x, c):
    xt = torch.tensor(x, dtype=torch.float32, requires_grad=True)
    z = z_sinif(model, xt[None], c).sum()
    (g,) = torch.autograd.grad(z, xt)
    return g.numpy()


def entegre_gradyan(model, x, c, taban, m=50):
    """Orta nokta Riemann toplami; toplam z(x)-z(taban) vermeli."""
    alf = (np.arange(m) + 0.5) / m
    g = np.zeros_like(x)
    for a in alf:
        g += gradyan(model, taban + a * (x - taban), c)
    return (x - taban) * g / m


def shapley_tum(model, x, c, arka, satir=8):
    """8 satir oyuncu; v(S) = z_c; S satirlari x, digerleri arka.
    256 koalisyonun hepsi: v[mask] tablosu."""
    n = satir
    kopyalar = []
    for mask in range(2**n):
        xs = arka.copy().reshape(8, 8)
        for i in range(n):
            if mask >> i & 1:
                xs[i] = x.reshape(8, 8)[i]
        kopyalar.append(xs.ravel())
    with torch.no_grad():
        Z = model(torch.tensor(np.array(kopyalar, dtype=np.float32)))
    return Z[:, c].numpy().astype(np.float64)


def shapley_exact(V, n=8):
    phi = np.zeros(n)
    for i in range(n):
        for mask in range(2**n):
            if mask >> i & 1:
                continue
            k = bin(mask).count("1")
            w = math.factorial(k) * math.factorial(n - k - 1)
            w /= math.factorial(n)
            phi[i] += w * (V[mask | (1 << i)] - V[mask])
    return phi


def shapley_ornek(V, m, rng, n=8):
    """m rastgele permutasyon; marjinal katkilarin ortalamasi."""
    phi = np.zeros(n)
    for _ in range(m):
        perm = rng.permutation(n)
        mask = 0
        for i in perm:
            yeni = mask | (1 << i)
            phi[i] += V[yeni] - V[mask]
            mask = yeni
    return phi / m


def rastgele_kopya(model, katman, seed=5):
    """Ust katmandan baslayarak 'katman' tane katmani sifirla."""
    m = copy.deepcopy(model)
    torch.manual_seed(seed)
    for L in [m.f1, m.f2, m.cik][3 - katman :]:
        L.reset_parameters()
    m.eval()
    return m


def main():
    D = veri_hazirla()
    model = egit(MLP(0.2), D["Xtr"], D["ytr"], seed=0)
    arka = D["Xtr"].mean(0)
    idx = [int(np.where(D["yte"] == c)[0][0]) for c in [0, 3, 5, 8]]
    satirlar = []
    print("1) Ornekler (test): indeks, gercek sinif, tahmin")
    tahmin = {}
    for i in idx:
        x = D["Xte"][i]
        c = int(
            np.argmax(model(torch.tensor(x[None])).detach().numpy())
        )
        tahmin[i] = c
        print("   %4d  gercek=%d  tahmin=%d" % (i, D["yte"][i], c))
    print("\n2) Entegre gradyan tamlik kontrolu (ornek %d)" % idx[0])
    x = D["Xte"][idx[0]].astype(np.float64)
    c = tahmin[idx[0]]
    with torch.no_grad():
        z_x = model(torch.tensor(x[None].astype(np.float32)))[
            0, c
        ].item()
        z_0 = model(torch.zeros(1, 64))[0, c].item()
    print("   z(x) - z(0) = %.5f" % (z_x - z_0))
    for m in [5, 20, 50, 200]:
        ig = entegre_gradyan(
            model,
            x.astype(np.float32),
            c,
            np.zeros(64, np.float32),
            m,
        )
        print(
            "   m=%3d  sum(IG) = %.5f  hata = %.2e"
            % (m, ig.sum(), abs(ig.sum() - (z_x - z_0)))
        )
    print("\n3) Ornekler uzerinde yontemler")
    for i in idx:
        x = D["Xte"][i]
        c = tahmin[i]
        gxi = x * gradyan(model, x, c)
        ig = entegre_gradyan(model, x, c, np.zeros(64, np.float32))
        ig5 = entegre_gradyan(
            model, x, c, np.full(64, 0.5, np.float32)
        )
        for ad, v in [
            ("girdi", x),
            ("GxI", gxi),
            ("IG_0", ig),
            ("IG_gri", ig5),
        ]:
            for p, val in enumerate(v):
                satirlar.append((i, D["yte"][i], ad, p, "%.6f" % val))
        print(
            "   ornek %4d: GxI en buyuk pikseller %s"
            % (i, np.argsort(-np.abs(gxi))[:4])
        )
    print("\n4) Shapley: tam hesap (256 koalisyon) ve ornekleme")
    x = D["Xte"][idx[0]]
    c = tahmin[idx[0]]
    V = shapley_tum(model, x, c, arka)
    phi = shapley_exact(V)
    deger = " ".join("%.3f" % v for v in phi)
    print("   phi (satir gruplari):", deger)
    print(
        "   verimlilik: sum(phi) = %.4f, v(N)-v({}) = %.4f"
        % (phi.sum(), V[-1] - V[0])
    )
    print("   m   hata_ort   hata_sd   (5 tohum, ornekleme)")
    sk = []
    for m in [5, 20, 50, 200]:
        hata = []
        for t in range(5):
            ph = shapley_ornek(V, m, np.random.default_rng(t))
            hata.append(np.mean(np.abs(ph - phi)))
        hata = np.array(hata)
        print("  %4d   %.4f    %.4f" % (m, hata.mean(), hata.std()))
        sk.append((m, "%.6f" % hata.mean(), "%.6f" % hata.std()))
    print(
        "\n5) Sanity: rastgele agirliklarla aciklama degisiyor mu?"
    )
    print("   katman  Spearman(ort)  sd")
    kayitlar = []
    for katman in [1, 2, 3]:
        rho = []
        m2 = rastgele_kopya(model, katman)
        for i in idx:
            x = D["Xte"][i]
            c = tahmin[i]
            a = x * gradyan(model, x, c)
            b = x * gradyan(m2, x, c)
            rho.append(spearmanr(a, b).correlation)
        rho = np.array(rho)
        print(
            "   %d       %+.3f        %.3f"
            % (katman, rho.mean(), rho.std())
        )
        kayitlar.append(
            (katman, "%.4f" % rho.mean(), "%.4f" % rho.std())
        )
    csv_yaz(
        "b78_aciklama.csv",
        ["ornek", "gercek", "yontem", "piksel", "deger"],
        satirlar,
    )
    csv_yaz("b78_shap.csv", ["m", "hata_ort", "hata_sd"], sk)
    csv_yaz("b78_sanity.csv", ["katman", "spearman", "sd"], kayitlar)


if __name__ == "__main__":
    main()
