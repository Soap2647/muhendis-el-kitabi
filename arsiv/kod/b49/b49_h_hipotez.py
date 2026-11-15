# -*- coding: utf-8 -*-
"""Bolum 49 - H: Hipotez testi, p-degeri, permutasyon, coklu test.
A/B tasarimi ve guc."""

import math
import random

from scipy import stats


def welch_t(a, b):
    """Welch t-istatistigi ve serbestlik derecesi (Satterthwaite)."""
    na, nb = len(a), len(b)
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    se2 = va / na + vb / nb
    t = (ma - mb) / math.sqrt(se2)
    df = se2**2 / (
        (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    )
    p = 2 * stats.t.sf(abs(t), df)  # iki yonlu p-degeri
    return t, df, p


def permutasyon(a, b, B=10_000, seed=49):
    """Iki orneklik permutasyon testi (ortalama farki)."""
    rnd = random.Random(seed)
    gozlenen = abs(sum(a) / len(a) - sum(b) / len(b))
    havuz = a + b
    na = len(a)
    say = 0
    for _ in range(B):
        rnd.shuffle(havuz)
        fark = abs(
            sum(havuz[:na]) / na - sum(havuz[na:]) / (len(havuz) - na)
        )
        if fark >= gozlenen:
            say += 1
    return gozlenen, (say + 1) / (B + 1)


def cokluk_karsilastirma(deney=20_000, k=20, seed=49):
    """k test, H0 dogru: en az birinin p<0.05 olma orani."""
    rnd = random.Random(seed)
    en_az_bir = 0
    bonf = 0
    for _ in range(deney):
        pv = []
        for _ in range(k):
            x = [rnd.gauss(0, 1) for _ in range(30)]
            m = sum(x) / 30
            s = math.sqrt(sum((t - m) ** 2 for t in x) / 29)
            t = m / (s / math.sqrt(30))
            pv.append(2 * stats.t.sf(abs(t), 29))
        if min(pv) < 0.05:
            en_az_bir += 1
        if min(pv) < 0.05 / k:
            bonf += 1
    return en_az_bir / deney, bonf / deney


def ab_orneklem(p1, p2, alfa=0.05, guc=0.80):
    """Iki oran icin orneklem buyuklugu (grup basina)."""
    za = stats.norm.ppf(1 - alfa / 2)
    zb = stats.norm.ppf(guc)
    pb = (p1 + p2) / 2
    pay = za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(
        p1 * (1 - p1) + p2 * (1 - p2)
    )
    return math.ceil((pay / (p2 - p1)) ** 2)


def guc_simulasyonu(n, delta, deney=10_000, seed=49):
    """Iki kosullu normal: sapma delta. Guc = P(p < 0.05 | H1)."""
    rnd = random.Random(seed)
    hit = 0
    for _ in range(deney):
        a = [rnd.gauss(0, 1) for _ in range(n)]
        b = [rnd.gauss(delta, 1) for _ in range(n)]
        _, _, p = welch_t(a, b)
        hit += p < 0.05
    return hit / deney


def main():
    # Ornek: iki kucuk olcum serisi (rastgele, tohum 49).
    rnd = random.Random(49)
    a = [rnd.gauss(10.0, 2.0) for _ in range(12)]
    b = [rnd.gauss(12.0, 2.0) for _ in range(12)]
    t, df, p = welch_t(a, b)
    print("Welch: t=%.4f df=%.3f p=%.5f" % (t, df, p))
    tt = stats.ttest_ind(a, b, equal_var=False)
    print("scipy: t=%.4f p=%.5f" % (tt.statistic, tt.pvalue))
    g, pp = permutasyon(a, b)
    print("Permutasyon: gozlenen fark=%.4f p=%.4f" % (g, pp))

    en, bonf = cokluk_karsilastirma()
    print(
        "20 test, H0 dogru: p<0.05 orani = %.4f (teorik %.4f)"
        % (en, 1 - 0.95**20)
    )
    print("Bonferroni (0.05/20): en az bir hata = %.4f" % bonf)

    n = ab_orneklem(0.10, 0.12)
    print("A/B: p1=0.10 p2=0.12 -> grup basina n = %d" % n)
    print(
        "Guc simulasyonu (n=%d, delta fark=0.8 sigma): %.3f"
        % (25, guc_simulasyonu(25, 0.8))
    )


if __name__ == "__main__":
    main()
