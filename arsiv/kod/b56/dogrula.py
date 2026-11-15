# -*- coding: utf-8 -*-
"""Bolum 56: kucuk bir veri dogrulayici (sema, aralik, benzersizlik,
eksiklik, dagilim kaymasi). Her kural bir (ad, sonuc) doner."""
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def kontrol(df, sema, aralik, benzersiz, en_fazla_eksik,
            referans=None,
            kayma_p=0.01):
    bulgular = []
    for kolon, tur in sema.items():                       # 1. sema
        ok = (kolon in df.columns
              and str(df[kolon].dtype).startswith(tur))
        bulgular.append(("sema:" + kolon, ok))
    for kolon, (lo, hi) in aralik.items():                # 2. aralik
        v = pd.to_numeric(df[kolon], errors="coerce").dropna()
        disi = int(((v < lo) | (v > hi)).sum())
        bulgular.append(("aralik:%s disi=%d" % (kolon, disi),
                         disi == 0))
    for anahtar in benzersiz:                              # 3. tekil
        d = int(df.duplicated(subset=anahtar).sum())
        bulgular.append(("tekil:%s kopya=%d" % ("+".join(anahtar), d),
                         d == 0))
    for kolon, oran in en_fazla_eksik.items():             # 4. eksik
        e = float(df[kolon].isna().mean())
        bulgular.append(("eksik:%s %.3f" % (kolon, e), e <= oran))
    if referans is not None:                               # 5. kayma
        for kolon in referans.columns:
            if kolon in df.columns and np.issubdtype(
                    df[kolon].dtype, np.number):
                a = referans[kolon].dropna()
                b = df[kolon].dropna()
                p = ks_2samp(a, b).pvalue
                bulgular.append(("kayma:%s p=%.4f" % (kolon, p),
                                 p >= kayma_p))
    return bulgular
