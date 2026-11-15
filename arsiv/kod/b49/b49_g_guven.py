# -*- coding: utf-8 -*-
"""Bolum 49 - G: Guven araliklari, t dagilimi, bootstrap, kapsama.

Veri: engine/veri/b44_gecikme.csv (Bolum 44 cevrim duzeyi benzetimi).
Cikti: engine/veri/b49_kapsama.csv, engine/veri/b49_bootstrap.csv
"""

import csv
import os
import math
import random

import numpy as np
from scipy import stats

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)


def gecikme(tur, kaynak):
    with open(VERI + "/b44_gecikme.csv", encoding="utf-8") as f:
        return [
            float(r["gecikme_cevrim"])
            for r in csv.DictReader(f)
            if r["tur"] == tur and r["kaynak"] == kaynak
        ]


def ort_s(v):
    n = len(v)
    m = sum(v) / n
    s = math.sqrt(sum((t - m) ** 2 for t in v) / (n - 1))
    return m, s


def normal_ve_t_ga(v, guven=0.95):
    n = len(v)
    m, s = ort_s(v)
    z = stats.norm.ppf(0.5 + guven / 2)
    t = stats.t.ppf(0.5 + guven / 2, n - 1)
    h_z = z * s / math.sqrt(n)
    h_t = t * s / math.sqrt(n)
    print("n=%d ort=%.3f s=%.3f" % (n, m, s))
    print("  z-GA: [%.3f, %.3f]  (z=%.4f)" % (m - h_z, m + h_z, z))
    print(
        "  t-GA: [%.3f, %.3f]  (t=%.4f, sd=%d)"
        % (m - h_t, m + h_t, t, n - 1)
    )
    lo, hi = stats.t.interval(
        guven, n - 1, loc=m, scale=s / math.sqrt(n)
    )
    print("  scipy t-GA: [%.3f, %.3f]" % (lo, hi))


def bootstrap_ga(v, B=10_000, seed=49):
    """Yuzdelik bootstrap: her yeniden orneklemde ortalama."""
    rnd = random.Random(seed)
    n = len(v)
    dagilim = []
    for _ in range(B):
        ornek = [v[rnd.randrange(n)] for _ in range(n)]
        dagilim.append(sum(ornek) / n)
    dagilim.sort()
    lo = dagilim[int(0.025 * B)]
    hi = dagilim[int(0.975 * B) - 1]
    return lo, hi, dagilim


def kapsama(seed=49, tekrar=100_000):
    """Gercek ortalama bilinir; %95 GA'larin ne kadari icerir?"""
    rng = np.random.default_rng(seed)
    satirlar = [["n", "dagilim", "z_kapsama", "t_kapsama"]]
    for dag in ("normal", "ustel"):
        for n in (5, 10, 30):
            if dag == "normal":
                x = rng.normal(0.0, 1.0, (tekrar, n))
                mu = 0.0
            else:
                x = rng.exponential(1.0, (tekrar, n))
                mu = 1.0
            m = x.mean(axis=1)
            s = x.std(axis=1, ddof=1)
            se = s / math.sqrt(n)
            zc = stats.norm.ppf(0.975)
            tc = stats.t.ppf(0.975, n - 1)
            kz = np.mean(np.abs(m - mu) <= zc * se)
            kt = np.mean(np.abs(m - mu) <= tc * se)
            print(
                "%-6s n=%2d  z-kapsama=%.4f  t-kapsama=%.4f"
                % (dag, n, kz, kt)
            )
            satirlar.append([n, dag, "%.4f" % kz, "%.4f" % kt])
    return satirlar


def main():
    v = gecikme("kesme", "TIM")
    normal_ve_t_ga(v[:10])  # ilk 10 gozlem: kucuk ornek
    print("-- Tam ornek (n=283), ayni yontemle")
    normal_ve_t_ga(v)
    lo, hi, dag = bootstrap_ga(v)
    print(
        "Yuzdelik bootstrap GA (ortalama, B=10000): [%.3f, %.3f]"
        % (lo, hi)
    )
    with open(
        VERI + "/b49_bootstrap.csv", "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        w.writerow(["ortalama"])
        for t in dag:
            w.writerow(["%.4f" % t])
    satirlar = kapsama()
    with open(
        VERI + "/b49_kapsama.csv", "w", encoding="utf-8", newline=""
    ) as f:
        csv.writer(f).writerows(satirlar)
    print("b49_kapsama.csv ve b49_bootstrap.csv yazildi")


if __name__ == "__main__":
    main()
