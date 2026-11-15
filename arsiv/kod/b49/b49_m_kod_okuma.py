# -*- coding: utf-8 -*-
"""Bolum 49 - Kod Okuma yardimcisi: sayisal kararlilik."""

import statistics as st


def naif_varyans(veri):
    """Tek gecisli formul: (sum x^2 - (sum x)^2 / n) / (n - 1)."""
    n = len(veri)
    sx = sum(veri)
    sxx = sum(x * x for x in veri)
    return (sxx - sx * sx / n) / (n - 1)


def iki_gecis(veri):
    m = sum(veri) / len(veri)
    return sum((x - m) ** 2 for x in veri) / (len(veri) - 1)


if __name__ == "__main__":
    veri = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    print("statistics.variance = %r" % st.variance(veri))
    print("naif tek gecis      = %r" % naif_varyans(veri))
    print("iki gecis (float)   = %r" % iki_gecis(veri))
