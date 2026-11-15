# -*- coding: utf-8 -*-
"""Bolum 56 temizleme adimlari. Her kural tek yerde durur."""
import numpy as np
import pandas as pd

GOREV = {"keşif": "kesif", "kesif": "kesif",
         "gözetleme": "gozetleme", "gozetleme": "gozetleme"}
HATA_ESLESME = {"": "YOK", "OK": "YOK", "HATA": "HATA",
                "E17": "E17", "E21": "E21"}


def gorev_normalize(s, naif=False):
    if naif:                                  # yanlis: sadece lower
        t = s.str.strip().str.lower()
    else:                                      # Turkce-duyarli yol
        t = s.str.strip().str.casefold().str.replace("\u0307", "",
                                                    regex=False)
    return t.map(GOREV)


def hata_normalize(s):
    t = s.fillna("").str.strip().str.upper()
    return t.map(HATA_ESLESME).fillna("DIGER")


def temizle(df, kayit, tr=None, aykiri_sil=True):
    """Ham tabloyu temizler. tr verilirse (sadece test icin) dogrulama
    bayraklarini doner. Kaynak satir numarasi her zaman korunur."""
    rap = {}
    df = df.copy()
    df["kaynak"] = np.arange(len(df))
    df["arac_id"] = df["arac_id"].str.strip().str.upper()
    df["gorev"] = gorev_normalize(df["gorev"])
    df["hata_kodu"] = hata_normalize(df["hata_kodu"])
    df["zaman"] = pd.to_datetime(df["zaman"], format="ISO8601",
                                 utc=True)
    rap["gorev_taninmayan"] = int(df["gorev"].isna().sum())
    dup = df.duplicated(subset=["arac_id", "zaman"], keep="first")
    rap["kopya_silindi"] = int(dup.sum())
    df = df.loc[~dup]
    df = df.merge(kayit, on="arac_id", how="left",
                  validate="many_to_one")
    ft = df["firmware"].eq("v2_ft")
    df.loc[ft, "irtifa"] = df.loc[ft, "irtifa"] / 3.28084
    rap["birim_donusum"] = int(ft.sum())
    df.loc[df["sicaklik_c"].eq(-999), "sicaklik_c"] = np.nan
    df.loc[~df["sicaklik_c"].between(-40, 120), "sicaklik_c"] = np.nan
    df = df.sort_values(["ucus_no", "zaman"]).reset_index(drop=True)
    ref = (df.groupby("ucus_no")["irtifa"]
             .transform(lambda s: s.shift(1).rolling(5, min_periods=3)
                        .median()))
    sapma = (df["irtifa"] - ref).abs() > 100
    rap["nedensel_aykiri"] = int(sapma.sum())
    df["nedensel_bayrak"] = sapma
    if aykiri_sil:
        df.loc[sapma, "irtifa"] = np.nan
    return df, rap
