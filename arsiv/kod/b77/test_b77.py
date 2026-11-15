# -*- coding: utf-8 -*-
"""Birim testleri. Calistirma: python -m pytest -q test_b77.py"""
import os

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from b77_ab import gerekli_n, guc_sim
from b77_drift import psi
from b77_kapi import kapi, veri_denetle
from b77_kayit import KayitDefteri
from b77_servis import ozellik_donustur, servis_donusumu
from b77_telemetri import model_kur, uret
from b77_veri import dogrula, ekle, getir, ozet

OZ = ["sicaklik", "akim", "gerilim", "dongu"]


def test_ozet_ayni_icerik_ayni_ozet(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("1,2\n")
    b.write_text("1,2\n")
    assert ozet(str(a)) == ozet(str(b))


def test_ayni_icerik_tek_nesne(tmp_path):
    depo = str(tmp_path / "depo")
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("x\n")
    b.write_text("x\n")
    assert ekle(str(a), depo) == ekle(str(b), depo)
    assert len(list((tmp_path / "depo").glob("*/*"))) == 1


def test_bozulma_yakalanir(tmp_path):
    depo = str(tmp_path / "depo")
    a = tmp_path / "a.csv"
    a.write_text("x\n")
    d = ekle(str(a), depo)
    with open(os.path.join(depo, d[:2], d[2:]), "ab") as f:
        f.write(b"y")
    assert dogrula(str(a) + ".veri", depo) is False
    with pytest.raises(IOError):
        getir(str(a) + ".veri", str(tmp_path / "geri.csv"), depo)


def test_psi_ayni_dagilim_kucuk():
    rng = np.random.default_rng(0)
    assert psi(rng.normal(size=5000), rng.normal(size=5000)) < 0.02


def test_psi_kayma_esigi_asar():
    rng = np.random.default_rng(0)
    assert psi(rng.normal(size=5000),
               rng.normal(1.0, size=5000)) > 0.2


def test_veri_denetle_sutun_ve_aralik():
    X, _ = uret(200, np.random.default_rng(1))
    df = pd.DataFrame(X, columns=OZ)
    assert veri_denetle(df) == []
    assert any("eksik sutun" in h
               for h in veri_denetle(df.drop(columns="akim")))
    df.loc[0, "akim"] = 999.0
    assert any("aralik disi" in h for h in veri_denetle(df))


def test_kapi_ayni_model_gecer():
    rng = np.random.default_rng(2)
    X, y = uret(1500, rng)
    Xs, ys = uret(1000, rng)
    p = model_kur().fit(X, y).predict_proba(Xs)[:, 1]
    gecti, _, _ = kapi(ys, p, p, B=200, rng=np.random.default_rng(0))
    assert gecti


def test_kapi_ozellik_eksik_adayi_reddeder():
    rng = np.random.default_rng(3)
    X, y = uret(2000, rng)
    Xs, ys = uret(2000, rng)
    eski = model_kur().fit(X, y).predict_proba(Xs)[:, 1]
    yeni = model_kur().fit(X[:, 1:], y).predict_proba(Xs[:, 1:])[:, 1]
    gecti, _, _ = kapi(ys, yeni, eski, B=300,
                       rng=np.random.default_rng(0))
    assert not gecti


def test_kayit_geri_al(tmp_path):
    kd = KayitDefteri(str(tmp_path / "kayit"))
    X, y = uret(300, np.random.default_rng(4))
    for i in range(3):
        n = kd.kaydet("m", model_kur(1.0).fit(X, y), i, "v")
        kd.asama_ata("m", n, "production")
    assert kd.geri_al("m") == 2
    assert [s["asama"] for s in kd.idx["m"]] == \
        ["arsiv", "production", "geri_alindi"]


def test_servis_olcek_yok_farkli():
    X, _ = uret(100, np.random.default_rng(5))
    sc = StandardScaler().fit(X)
    assert np.allclose(ozellik_donustur(X, sc), sc.transform(X))
    assert not np.allclose(servis_donusumu(X, sc, "olcek_yok"),
                           sc.transform(X))


def test_ab_formul_ve_simulasyon():
    n = gerekli_n(0.05, 0.06)
    assert 8100 <= n <= 8200
    assert abs(guc_sim(0.05, 0.06, n, deneme=4000) - 0.8) < 0.03
