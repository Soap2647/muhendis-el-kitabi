# -*- coding: utf-8 -*-
# b80_veri.py: Bolum 67'nin sentetik sahne ureticisinin genisletilmis
# hali. Sekil maskeleri b67_veri._sekil'den gelir. Eklenenler: isik,
# gurultu, bulaniklik, olcek kaymasi, OOD (kus benzeri) nesneler ve
# video dizileri. Her sey tohumla tekrarlanabilir.
import numpy as np
from scipy.ndimage import gaussian_filter
from b67_veri import _sekil

# Ayar: her sahne icin bu araliklardan orneklenir.
# bul = (olasilik, sigma_alt, sigma_ust): bulaniklik ihtimali.
EGITIM = dict(
    bg=(0.15, 0.40),
    par=(0.55, 1.00),
    gur=(0.01, 0.06),
    bul=(0.4, 0.5, 1.0),
    olcek=(0.9, 1.1),
)
NOMINAL = EGITIM  # ayni dagilim, farkli tohum (sahne duzeyi)
# Operasyonel kayma: arka plan parlar (sis, yansima), kontrast biraz
# duser, gurultu artar, kamera hafif bulanir, hedefler uzaklasir.
DRIFT = dict(
    bg=(0.30, 0.45),
    par=(0.60, 0.90),
    gur=(0.04, 0.07),
    bul=(1.0, 0.8, 1.2),
    olcek=(0.80, 0.95),
)
# Sert kayma (kontrol): ayirt edilemez seviyeye iner.
DRIFT_AGIR = dict(
    bg=(0.40, 0.55),
    par=(0.45, 0.65),
    gur=(0.06, 0.09),
    bul=(1.0, 1.0, 1.4),
    olcek=(0.75, 0.90),
)


def kus_maske(s, cx, cy, xx, yy):
    """Kus benzeri OOD sekli: iki yatay elipsin birlesimi (kanat)."""
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    e1 = ((dx + 0.35 * s) / (0.42 * s)) ** 2 + (dy / (0.14 * s)) ** 2
    e2 = ((dx - 0.35 * s) / (0.42 * s)) ** 2 + (dy / (0.14 * s)) ** 2
    return (e1 <= 1) | (e2 <= 1)


def sahne(rng, ayar, boyut=96, nmin=0, nmax=5, kus=0):
    """Bir sahne. Donus: img (HxW float32), nesneler (etiketli)."""
    H = W = boyut
    o = boyut / 96.0
    yy, xx = np.mgrid[0:H, 0:W]
    bg = rng.uniform(*ayar["bg"])
    gur = rng.uniform(*ayar["gur"])
    n = int(rng.integers(nmin, nmax + 1))
    adaylar = []  # (sinif, maske, parlaklik, ood)
    for k in range(n + kus):
        ood = k >= n
        s = rng.uniform(8, 24) * o * rng.uniform(*ayar["olcek"])
        cx = rng.uniform(s / 2 + 1, W - s / 2 - 1)
        cy = rng.uniform(s / 2 + 1, H - s / 2 - 1)
        par = rng.uniform(*ayar["par"])
        if ood:
            adaylar.append(
                (-1, kus_maske(s, cx, cy, xx, yy), par, True)
            )
        else:
            sek = int(rng.integers(0, 3))
            adaylar.append(
                (sek, _sekil(sek, s, cx, cy, xx, yy), par, False)
            )
    img = np.full((H, W), bg)
    gorunur = np.full((H, W), -1, dtype=np.int64)
    for k, (sek, m, par, ood) in enumerate(adaylar):
        gorunur[m] = k  # sonra cizilen onceki nesneyi ortar
        img[m] = par
    p, lo, hi = ayar["bul"]
    if rng.uniform() < p:
        img = gaussian_filter(img, rng.uniform(lo, hi))
    img = np.clip(img + gur * rng.standard_normal((H, W)), 0, 1)
    nesneler = []
    for k, (sek, m, par, ood) in enumerate(adaylar):
        if ood:
            continue  # OOD nesnesinin etiketi yok
        mk = gorunur == k
        alan = int(mk.sum())
        if alan < 15 * o * o:  # cok ortulu: kutu etiketi yok
            continue
        ys, xs = np.where(mk)
        box = [
            int(xs.min()),
            int(ys.min()),
            int(xs.max()) + 1,
            int(ys.max()) + 1,
        ]
        nesneler.append({"cls": sek, "box": box, "alan": alan})
    return img.astype(np.float32), nesneler


def veri_seti(n, seed, ayar=EGITIM, boyut=96, nmin=0, nmax=5, kus=0):
    """n sahneden X (n,1,H,W) ve etiket listesi uretir."""
    rng = np.random.default_rng(seed)
    X = np.zeros((n, 1, boyut, boyut), dtype=np.float32)
    Y = []
    for i in range(n):
        img, nes = sahne(rng, ayar, boyut, nmin, nmax, kus)
        X[i, 0] = img
        Y.append(nes)
    return X, Y


def video(seed, T=120, ayar=NOMINAL, kus=1):
    """Dort nesne + bir kus (OOD) hareket eder. Nesne 0 ve 1 ayni
    bolgede kesisir (kimlik degisimi riski). Her kare: goruntu, gt_id,
    gt (xyxy) ve sinif. Kus nesnesinin kimligi gt'ye girmez."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:96, 0:96]
    # x, y, vx, vy, boyut, sinif, parlaklik, t0, t1
    nes = [
        [12.0, 30.0, 1.0, 0.2, 14, 0, 0.90, 0, T],
        [84.0, 34.0, -1.0, 0.0, 14, 1, 0.80, 0, T],
        [48.0, 70.0, 0.0, -0.6, 12, 2, 0.85, 0, T],
        [20.0, 80.0, 1.2, -0.4, 10, 1, 0.75, 10, 90],
    ]
    for _ in range(kus):  # OOD: sinif -1, gt'ye girmez
        nes.append([0.0, 55.0, 1.4, 0.0, 16, -1, 0.70, 5, T])
    kareler = []
    for t in range(T):
        img = np.full((96, 96), rng.uniform(*ayar["bg"]))
        gt_id, gt, cls = [], [], []
        for k, d in enumerate(nes):
            x, y, vx, vy, s, sek, par, t0, t1 = d
            if not (t0 <= t < t1):
                continue
            x += vx
            y += vy
            d[0], d[1] = x, y
            d[2] += (
                0.01 * rng.standard_normal()
            )  # kucuk ivme gurultusu
            d[3] += 0.01 * rng.standard_normal()
            if sek < 0:
                m = kus_maske(s, x, y, xx, yy)
            else:
                m = _sekil(sek, s, x, y, xx, yy)
            img[m] = par
        p, lo, hi = ayar["bul"]
        if rng.uniform() < p:
            img = gaussian_filter(img, rng.uniform(lo, hi))
        img = np.clip(
            img + ayar["gur"][1] * rng.standard_normal((96, 96)), 0, 1
        ).astype(np.float32)
        for k, d in enumerate(nes):
            if d[5] < 0 or not (d[7] <= t < d[8]):
                continue
            x, y, s = d[0], d[1], d[4]
            kutu = [
                int(round(x - s / 2)),
                int(round(y - s / 2)),
                int(round(x + s / 2)),
                int(round(y + s / 2)),
            ]
            # gorunur alan >= %50 ise etiketlenir
            kirpik = [
                max(kutu[0], 0),
                max(kutu[1], 0),
                min(kutu[2], 96),
                min(kutu[3], 96),
            ]
            tam = (kutu[2] - kutu[0]) * (kutu[3] - kutu[1])
            gorunur_a = max(kirpik[2] - kirpik[0], 0) * max(
                kirpik[3] - kirpik[1], 0
            )
            if gorunur_a < 0.5 * tam:
                continue
            gt_id.append(k)
            gt.append(kirpik)
            cls.append(d[5])
        kareler.append(
            {"img": img, "gt_id": gt_id, "gt": gt, "cls": cls}
        )
    return kareler


if __name__ == "__main__":
    X, Y = veri_seti(200, seed=0)
    print(
        "sahne:",
        X.shape,
        "ort. nesne:",
        round(np.mean([len(y) for y in Y]), 2),
    )
    print(
        "sinif:",
        np.bincount([o["cls"] for y in Y for o in y]).tolist(),
    )
    X, Y = veri_seti(200, seed=888, ayar=DRIFT)
    print("drift ort. piksel:", round(float(X.mean()), 3))
    X, Y = veri_seti(200, seed=0)
    print("nominal ort. piksel:", round(float(X.mean()), 3))
