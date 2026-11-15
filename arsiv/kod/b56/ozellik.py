# -*- coding: utf-8 -*-
"""Bolum 56 oznitelik uretimi. Kural: t aninda yalnizca t ve oncesi
kullanilir (gecmis pencere). Gelecek degerler asla girmez."""
import numpy as np
import pandas as pd

SAYISAL = ["irtifa", "hiz", "batarya_v", "akim_a", "sicaklik_c",
           "titresim_g", "guc_w", "sic_ort30", "sic_fark",
           "tit_max30",
           "volt_fark", "irt_fark", "saat_sin", "saat_cos"]
KATEGORIK = ["gorev"]


def ozellik_tablosu(t):
    t = t.sort_values(["ucus_no", "zaman"]).copy()
    g = t.groupby("ucus_no", sort=False)
    gec = lambda c, w, f: g[c].transform(
        lambda s: getattr(s.shift(1).rolling(w, min_periods=5), f)())
    t["guc_w"] = t["batarya_v"] * t["akim_a"]
    t["sic_ort30"] = gec("sicaklik_c", 30, "mean")
    t["sic_fark"] = t["sicaklik_c"] - t["sic_ort30"]
    t["tit_max30"] = gec("titresim_g", 30, "max")
    t["volt_fark"] = t["batarya_v"] - gec("batarya_v", 30, "mean")
    t["irt_fark"] = t["irtifa"] - gec("irtifa", 10, "median")
    saat = t["zaman"].dt.hour + t["zaman"].dt.minute / 60
    t["saat_sin"] = np.sin(2 * np.pi * saat / 24)
    t["saat_cos"] = np.cos(2 * np.pi * saat / 24)
    return t


def gecmis_olmayan_pencere(t):
    """Yanlis (sizdiran) surum: merkezi pencere, gelecegi de gorur."""
    t = t.sort_values(["ucus_no", "zaman"]).copy()
    g = t.groupby("ucus_no", sort=False)
    t["sic_ort30"] = g["sicaklik_c"].transform(
        lambda s: s.rolling(31, center=True, min_periods=5).mean())
    return t
