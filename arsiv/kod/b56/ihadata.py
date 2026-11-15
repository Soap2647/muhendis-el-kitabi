# -*- coding: utf-8 -*-
"""Sentetik IHA ucus gunlugu uretici (Bolum 56). Tohum: 56.

Gercek veri degildir. Ogrenme icin bilerek kirletilmis bir veri
kumesidir; kirlilikler truth tablosunda isaretlenir."""
import numpy as np
import pandas as pd

ARACLAR = ["IHA-%02d" % i for i in range(1, 11)]
FT_ARACLAR = {"IHA-07", "IHA-08", "IHA-09", "IHA-10"}  # v2: ft
IST_ARACLAR = {"IHA-05", "IHA-06"}                     # +03:00
BASLANGIC = pd.Timestamp("2026-03-01 06:00:00")        # UTC
UCUS_PER = 20


def _ucus(rng, arac, ariza, tf, n):
    """Tek bir ucusun ham sinyalleri ve kirli etiketleri."""
    i = np.arange(n)
    if ariza:
        r = np.clip((i - (tf - 120)) / 120, 0, 1)   # oncul rampa
    else:
        r = np.zeros(n)
    sic = (36 + rng.normal(0, 1.5) + 2.5 * rng.standard_normal(n)
           + 3 * r)
    volt = 24.6 - 0.002 * i - 0.15 * r + 0.05 * rng.standard_normal(n)
    akim = (11 + 2 * np.sin(i / 25) + 1.0 * r
            + 0.5 * rng.standard_normal(n))
    tit = 0.15 + 0.03 * np.abs(rng.standard_normal(n)) + 0.03 * r
    irt = 120 + 12 * np.sin(i / 40) + 1.5 * rng.standard_normal(n)
    if ariza:                                       # gercek olay
        irt = irt - 45 * np.clip((i - (tf - 8)) / 8, 0, 1)
    hiz = 14 + 0.6 * rng.standard_normal(n)
    return r, sic, volt, akim, tit, irt, hiz


def uret(seed=56):
    rng = np.random.default_rng(seed)
    satirlar, truth = [], []
    ucus_no = 0
    for arac in ARACLAR:
        for _ in range(UCUS_PER):
            ucus_no += 1
            ariza = rng.random() < 0.25
            tf = int(rng.integers(200, 290)) if ariza else -1
            n = tf + 1 if ariza else int(rng.integers(206, 297))
            i = np.arange(n)
            r, sic, volt, akim, tit, irt, hiz = _ucus(
                rng, arac, ariza, tf, n)
            gorev = rng.choice(["Keşif", "kesif", "gözetleme",
                                "Gözetleme", "KEŞİF"],
                               p=[.3, .2, .2, .15, .15])
            hk = np.where(rng.random(n) < 0.6, "", "OK")
            hk = hk.astype(object)
            hata = rng.random(n) < 0.002
            hk[hata] = rng.choice(["HATA", "hata", "Hata "],
                                  hata.sum())
            if ariza:                               # olaya bagli kod
                kod = rng.choice(["E17", "e17", "E17 ", "E21"])
                hk[(i >= tf - 3) & (i <= tf + 5)] = kod
            y = ((i >= tf - 30) & (i <= tf)).astype(int)
            # ---- kirlilikler ----
            if arac in FT_ARACLAR:
                irt = irt * 3.28084
            gps = rng.random(n) < 0.003
            irt[gps] += 900
            sen = rng.random(n) < 0.005
            sic[sen] = -999
            sic[rng.random(n) < 0.05] = np.nan
            volt_nan = (volt < 24.2) & (rng.random(n) < 0.35)
            volt[volt_nan] = np.nan
            tit_nan = (gorev == "gözetleme") & (rng.random(n) < 0.25)
            tit = np.where(tit_nan, np.nan, tit)
            t0 = BASLANGIC + pd.Timedelta(minutes=45 * ucus_no)
            for j in range(n):
                tu = t0 + pd.Timedelta(seconds=2 * j)
                if arac in IST_ARACLAR:
                    z = (tu + pd.Timedelta(hours=3)).strftime(
                        "%Y-%m-%d %H:%M:%S") + "+03:00"
                else:
                    z = tu.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                satirlar.append((z, arac, ucus_no, str(gorev), irt[j],
                                 hiz[j], volt[j], akim[j], sic[j],
                                 tit[j], str(hk[j]), y[j]))
                truth.append((arac in FT_ARACLAR, bool(gps[j]),
                              bool(sen[j]), False))
    cols = ["zaman", "arac_id", "ucus_no", "gorev", "irtifa", "hiz",
            "batarya_v", "akim_a", "sicaklik_c", "titresim_g",
            "hata_kodu", "ariza"]
    df = pd.DataFrame(satirlar, columns=cols)
    tr = pd.DataFrame(truth, columns=["birim_ft", "gps", "sentinel",
                                      "kopya"])
    # ---- yinelenen kayitlar: kopya ve kucuk harfli/bosluklu kimlik
    rng2 = np.random.default_rng(seed + 1)
    kop = rng2.choice(len(df), size=int(0.015 * len(df)),
                      replace=False)
    yak = rng2.choice(len(df), size=int(0.005 * len(df)),
                      replace=False)
    d1 = df.iloc[kop].copy()
    d2 = df.iloc[yak].copy()
    d2["arac_id"] = d2["arac_id"].str.lower() + " "
    t1 = tr.iloc[kop].copy()
    t1["kopya"] = True
    t2 = tr.iloc[yak].copy()
    t2["kopya"] = True
    df = pd.concat([df, d1, d2], ignore_index=True)
    tr = pd.concat([tr, t1, t2], ignore_index=True)
    return df, tr


def kayit_tablosu():
    """Arac kayit tablosu: firmware ve istasyon (merge icin)."""
    return pd.DataFrame({
        "arac_id": ARACLAR,
        "firmware": ["v2_ft" if a in FT_ARACLAR else "v1_m"
                     for a in ARACLAR],
        "istasyon": ["IST" if a in IST_ARACLAR else "ANK"
                     for a in ARACLAR]})
