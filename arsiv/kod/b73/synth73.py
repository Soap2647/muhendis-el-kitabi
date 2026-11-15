# -*- coding: utf-8 -*-
"""Bolum 73 - sentetik goruntu ve Turkce aciklama ureticisi.

Her ornek: 32x32 RGB, bir renk, bir boyut, bir sekil, bir konum.
Aciklama ayni parametrelerden kurulur: "kirmizi buyuk daire sol
ustte".
"""

import numpy as np

RENK_AD = ["kırmızı", "yeşil", "mavi", "sarı"]
RENK_RGB = np.array(
    [
        [0.90, 0.10, 0.10],
        [0.10, 0.75, 0.20],
        [0.15, 0.30, 0.95],
        [0.95, 0.85, 0.10],
    ],
    np.float32,
)
SEKIL_AD = ["daire", "kare", "üçgen", "artı"]
BOYUT_AD = ["küçük", "büyük"]
BOYUT_R = np.array([5.0, 9.0], np.float32)
KONUM_AD = [
    "sol üstte",
    "sağ üstte",
    "sol altta",
    "sağ altta",
    "ortada",
]
KONUM_XY = np.array(
    [[9, 9], [23, 9], [9, 23], [23, 23], [16, 16]], np.float32
)

Y, X = np.mgrid[0:32, 0:32].astype(np.float32)


def maske(sekil, r, th, dx, dy):
    c, s = np.cos(th), np.sin(th)
    xr = c * dx + s * dy
    yr = -s * dx + c * dy
    if sekil == 0:  # daire
        return xr**2 + yr**2 <= r * r
    if sekil == 1:  # kare
        return (np.abs(xr) <= 0.8 * r) & (np.abs(yr) <= 0.8 * r)
    if sekil == 2:  # üçgen
        return (np.abs(yr) <= 0.8 * r) & (
            np.abs(xr) <= (yr + 0.8 * r) / 2
        )
    return ((np.abs(xr) <= 0.3 * r) & (np.abs(yr) <= r)) | (  # artı
        (np.abs(yr) <= 0.3 * r) & (np.abs(xr) <= r)
    )


def ciz(rng, r_i, b_i, s_i, k_i, gurultu=0.03, dik=False):
    jx, jy = rng.uniform(-1.5, 1.5, 2)
    th = rng.uniform(0, 2 * np.pi)
    if dik:
        th = 0.0
    r = BOYUT_R[b_i] * rng.uniform(0.9, 1.1)
    m = maske(
        s_i,
        r,
        th,
        X - (KONUM_XY[k_i, 0] + jx),
        Y - (KONUM_XY[k_i, 1] + jy),
    )
    bg = (
        rng.uniform(0.15, 0.35, 3).astype(np.float32).reshape(3, 1, 1)
    )
    col = RENK_RGB[r_i].reshape(3, 1, 1)
    img = bg + m[None] * (col - bg)
    img = img + gurultu * rng.standard_normal(img.shape).astype(
        np.float32
    )
    return np.clip(img, 0, 1)


def ornekler(
    n,
    rng,
    izin=None,
    sekil_sabit=None,
    sekil_renk=None,
    p_kural=0.0,
    dik=False,
):
    """n ornek uretir. izin: (renk, sekil) cift kumesi (None: hepsi).
    sekil_sabit: tum sekiller bu deger (siniflandirma etiketi icin).
    sekil_renk: sekle ozgu renk ipucu (kisa yol deneyi), p_kural
    olasilikla.
    """
    X_out = np.zeros((n, 3, 32, 32), np.float32)
    R = np.zeros(n, int)
    S = np.zeros(n, int)
    B = np.zeros(n, int)
    K = np.zeros(n, int)
    i = 0
    while i < n:
        s = (
            sekil_sabit
            if sekil_sabit is not None
            else rng.integers(4)
        )
        r = rng.integers(4)
        if sekil_renk is not None and rng.random() < p_kural:
            r = sekil_renk[s]
        if izin is not None and (r, s) not in izin:
            continue
        b = rng.integers(2)
        k = rng.integers(5)
        X_out[i] = ciz(rng, r, b, s, k, dik=dik)
        R[i], S[i], B[i], K[i] = r, s, b, k
        i += 1
    return X_out, R, S, B, K


def aciklama(r, b, s, k):
    return "%s %s %s %s" % (
        RENK_AD[r],
        BOYUT_AD[b],
        SEKIL_AD[s],
        KONUM_AD[k],
    )


KELIMELER = ["<pad>"] + sorted(
    set(" ".join(RENK_AD + BOYUT_AD + SEKIL_AD + KONUM_AD).split())
)
KIMLIK = {w: i for i, w in enumerate(KELIMELER)}
UZUN = 5


def belirtec(metin):
    ids = [KIMLIK[w] for w in metin.split()][:UZUN]
    return ids + [0] * (UZUN - len(ids))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    Xs, R, S, B, K = ornekler(8, rng)
    for i in range(8):
        print(aciklama(R[i], B[i], S[i], K[i]), Xs[i].mean().round(3))
    print(KELIMELER, len(KELIMELER))
    print(belirtec(aciklama(0, 1, 2, 3)))
