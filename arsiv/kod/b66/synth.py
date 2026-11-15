# -*- coding: utf-8 -*-
"""Bölüm 66: sentetik geometrik şekil üreticisi (32x32, gri tonlu).

Gerçek veri indirilmez. Her şekil; konum, boyut, dönüş ve parlaklığı
rastgele değişen bir sınıftır. Kaynak alanı (8 sınıf) ile hedef alanı
(4 sınıf, daha gürültülü ve bulanık) ayrı parametrelerle üretilir.
"""

import numpy as np

ORTA = 15.5
KAYNAK_SINIF = [
    "daire",
    "kare",
    "ucgen",
    "arti",
    "x",
    "elips",
    "cubuk",
    "cift_daire",
]
HEDEF_SINIF = [0, 1, 2, 3]  # daire, kare, üçgen, artı


def _sekil(k, xp, yp, s):
    """k. şeklin maskesi. (xp, yp): şekil merkezine göre döndürülmüş
    koordinatlar."""
    if k == 0:  # daire
        return xp**2 + yp**2 < s**2
    if k == 1:  # kare
        return np.maximum(np.abs(xp), np.abs(yp)) < 0.8 * s
    if k == 2:  # üçgen (dışbükey çokgen)
        A = (0.0, -s)
        B = (0.866 * s, 0.5 * s)
        C = (-0.866 * s, 0.5 * s)

        def kenar(P, Q):
            return (Q[0] - P[0]) * (yp - P[1]) - (Q[1] - P[1]) * (
                xp - P[0]
            )

        c1, c2, c3 = kenar(A, B), kenar(B, C), kenar(C, A)
        return ((c1 >= 0) & (c2 >= 0) & (c3 >= 0)) | (
            (c1 <= 0) & (c2 <= 0) & (c3 <= 0)
        )
    if k == 3:  # artı
        w = 0.25 * s
        return ((np.abs(xp) < w) & (np.abs(yp) < s)) | (
            (np.abs(yp) < w) & (np.abs(xp) < s)
        )
    if k == 4:  # X (artının 45° dönüşü)
        u = (xp + yp) / np.sqrt(2)
        v = (xp - yp) / np.sqrt(2)
        w = 0.25 * s
        return ((np.abs(u) < w) & (np.abs(v) < s)) | (
            (np.abs(v) < w) & (np.abs(u) < s)
        )
    if k == 5:  # elips
        return (xp / s) ** 2 + (yp / (0.55 * s)) ** 2 < 1
    if k == 6:  # çubuk
        return (np.abs(yp) < 0.2 * s) & (np.abs(xp) < s)
    if k == 7:  # iki daire
        r = 0.5 * s
        return ((xp - 0.6 * s) ** 2 + yp**2 < r**2) | (
            (xp + 0.6 * s) ** 2 + yp**2 < r**2
        )
    raise ValueError(k)


def uret(
    n_sinif,
    tohum,
    siniflar,
    gurultu=0.05,
    olcek=(0.18, 0.30),
    konum=3.0,
    bulanik=False,
    kontrast=(0.6, 1.0),
):
    """n_sinif: her sınıftan örnek sayısı. Dönüş: X (N,1,32,32), y
    (N,)."""
    rng = np.random.default_rng(tohum)
    y = np.repeat(np.arange(len(siniflar)), n_sinif)
    sinif = np.array(siniflar)[y]
    N = len(y)
    s = rng.uniform(*olcek, N) * 32
    th = rng.uniform(0, 2 * np.pi, N)
    cx = ORTA + rng.uniform(-konum, konum, N)
    cy = ORTA + rng.uniform(-konum, konum, N)
    yy, xx = np.mgrid[0:32, 0:32].astype(np.float64)
    dx = xx[None] - cx[:, None, None]
    dy = yy[None] - cy[:, None, None]
    c = np.cos(th)[:, None, None]
    sn = np.sin(th)[:, None, None]
    xp = c * dx + sn * dy
    yp = -sn * dx + c * dy
    S = s[:, None, None]
    maske = np.zeros((N, 32, 32), dtype=bool)
    for k in set(siniflar):
        idx = np.where(sinif == k)[0]
        maske[idx] = _sekil(k, xp[idx], yp[idx], S[idx])
    on = rng.uniform(*kontrast, N)
    arka = rng.uniform(0.0, 0.2, N)
    img = arka[:, None, None] + (on - arka)[:, None, None] * maske
    img = img + rng.normal(0, gurultu, img.shape)
    if bulanik:
        p = np.pad(img, ((0, 0), (1, 1), (1, 1)), mode="edge")
        img = (
            sum(
                p[:, i : i + 32, j : j + 32]
                for i in range(3)
                for j in range(3)
            )
            / 9.0
        )
    img = np.clip(img, 0, 1).astype(np.float32)[:, None]
    return img, y


def hedef_veri(n_sinif, tohum, konum=3.0):
    """Hedef alan: 4 sınıf, gürültülü ve bulanık görüntüler."""
    return uret(
        n_sinif,
        tohum,
        HEDEF_SINIF,
        gurultu=0.15,
        olcek=(0.16, 0.28),
        konum=konum,
        bulanik=True,
        kontrast=(0.5, 1.0),
    )


def kaynak_veri(n_sinif, tohum):
    """Kaynak alan (ön eğitim): 8 sınıf, temiz görüntüler."""
    return uret(n_sinif, tohum, list(range(8)), gurultu=0.05)


def kaydir(X, dx, dy):
    """Görüntüyü (dx, dy) piksel kaydırır; boşluklar sıfırla dolar."""
    Y = np.zeros_like(X)
    H, W = X.shape[-2:]
    Y[
        ..., max(dy, 0) : H + min(dy, 0), max(dx, 0) : W + min(dx, 0)
    ] = X[
        ...,
        max(-dy, 0) : H + min(-dy, 0),
        max(-dx, 0) : W + min(-dx, 0),
    ]
    return Y
