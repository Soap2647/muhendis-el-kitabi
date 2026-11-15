# -*- coding: utf-8 -*-
"""Bolum 75: kalibrasyon verisindeki tek bir aykiri ornegin etkisi."""

import torch
from b75_ortak import veri, mlp_t, egit, dogruluk, TOHUMLAR
from b75_nicemleme import girdi_olcekleri, ptq


def main():
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        temiz = Xtr[-200:].clone()
        kirli = temiz.clone()
        kirli[0] = 8.0  # tek bir asiri girdi (normal: 0..1)
        for ad, cal in [("temiz", temiz), ("aykiri", kirli)]:
            for ab in [8, 4]:
                for p in [1.0, 0.999, 0.99]:
                    s = girdi_olcekleri(base, cal, p, ab)
                    m = ptq(base, 8, ab, True, cal, p)
                    acc = dogruluk(m, Xte, yte)
                    print(
                        "tohum %d  A%d  kalibrasyon=%-6s p=%-6s  "
                        "olcek_katman2=%.4f  acc=%.4f"
                        % (t, ab, ad, p, float(s[2]), acc)
                    )


if __name__ == "__main__":
    main()
