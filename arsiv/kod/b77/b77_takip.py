# -*- coding: utf-8 -*-
"""SQLite tabanli deney takipcisi (MLflow'un kucuk bir benzeri).

Her deney icin: kod surumu (git commit), veri ozeti, parametreler,
metrikler ve artefakt ozetleri tek bir veritabaninda tutulur.
"""
import datetime
import os
import sqlite3
import subprocess

import joblib
import numpy as np
from sklearn.metrics import roc_auc_score

from b77_veri import ozet
from b77_telemetri import model_kur

SEMA = """
CREATE TABLE IF NOT EXISTS deney (
  id INTEGER PRIMARY KEY, ad TEXT, zaman TEXT,
  git TEXT, veri TEXT, ortam TEXT);
CREATE TABLE IF NOT EXISTS parametre (
  deney INTEGER, anahtar TEXT, deger TEXT);
CREATE TABLE IF NOT EXISTS metrik (
  deney INTEGER, anahtar TEXT, deger REAL);
CREATE TABLE IF NOT EXISTS artefakt (
  deney INTEGER, yol TEXT, sha256 TEXT);
"""


def git_commit(kod="."):
    """Kod deposunun HEAD commit'ini okur; depo yoksa 'yok' doner."""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=kod,
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "yok"


class Takip:
    def __init__(self, dosya):
        self.db = sqlite3.connect(dosya)
        self.db.executescript(SEMA)

    def baslat(self, ad, veri_ozeti, kod, ortam=""):
        zaman = datetime.datetime.now().isoformat(timespec="seconds")
        cur = self.db.execute(
            "INSERT INTO deney (ad, zaman, git, veri, ortam) "
            "VALUES (?, ?, ?, ?, ?)",
            (ad, zaman, git_commit(kod), veri_ozeti, ortam))
        self.db.commit()
        return cur.lastrowid

    def parametre(self, deney, d):
        self.db.executemany("INSERT INTO parametre VALUES (?, ?, ?)",
                            [(deney, k, str(v))
                            for k, v in d.items()])
        self.db.commit()

    def metrik(self, deney, anahtar, deger):
        self.db.execute("INSERT INTO metrik VALUES (?, ?, ?)",
                        (deney, anahtar, float(deger)))
        self.db.commit()

    def artefakt(self, deney, yol):
        self.db.execute("INSERT INTO artefakt VALUES (?, ?, ?)",
                        (deney, yol, ozet(yol)))
        self.db.commit()

    def sirala(self, metrik):
        """Deneyleri metriğe göre azalan sırada listeler."""
        sorgu = """
        SELECT d.id, d.ad, d.git, d.veri,
          (SELECT deger FROM parametre p
            WHERE p.deney = d.id AND p.anahtar = 'C') AS C,
          (SELECT deger FROM metrik m
            WHERE m.deney = d.id AND m.anahtar = ?) AS skor
        FROM deney d ORDER BY skor DESC"""
        return self.db.execute(sorgu, (metrik,)).fetchall()

    def gecersiz(self, guncel_veri):
        """Veri ozeti degismis (artik gecersiz) deneyleri listeler."""
        return self.db.execute(
            "SELECT id, ad FROM deney WHERE veri != ?",
            (guncel_veri,)).fetchall()


def csv_yaz(yol, X, y):
    with open(yol, "w", encoding="utf-8") as f:
        f.write("sicaklik,akim,gerilim,dongu,etiket\n")
        for satir, e in zip(X, y):
            f.write(",".join("%.4f" % v for v in satir) + ",%d\n" % e)


def csv_oku(yol):
    d = np.loadtxt(yol, delimiter=",", skiprows=1)
    return d[:, :4], d[:, 4].astype(int)


def kod_deposu(yol="calisma/kod"):
    """Egitim betigini iceren gecici bir git deposu hazirlar."""
    if os.path.exists(os.path.join(yol, ".git")):
        return yol
    os.makedirs(yol, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=yol, check=True)
    ep = os.path.join(yol, "egitim.py")
    with open(ep, "w", encoding="utf-8") as f:
        f.write("# egitim betigi (surum 1)\n")
    subprocess.run(["git", "add", "."], cwd=yol, check=True)
    subprocess.run(["git", "-c", "user.name=b77",
                    "-c", "user.email=b77@example.com",
                    "commit", "-q", "-m", "egitim betigi"],
                   cwd=yol, check=True)
    return yol


if __name__ == "__main__":
    from b77_veri import ekle
    from b77_telemetri import uret
    if os.path.exists("calisma/takip.db"):
        os.remove("calisma/takip.db")
    kod = kod_deposu()
    rng = np.random.default_rng(42)
    csv_yaz("calisma/egitim.csv", *uret(3000, rng))
    csv_yaz("calisma/test.csv", *uret(2000, np.random.default_rng(7)))
    v_egitim = ekle("calisma/egitim.csv")
    Xe, ye = csv_oku("calisma/egitim.csv")
    Xt, yt = csv_oku("calisma/test.csv")

    takip = Takip("calisma/takip.db")
    for C in [0.01, 0.1, 1.0, 10.0]:
        d = takip.baslat("lojistik", v_egitim, kod)
        takip.parametre(d, {"C": C, "tohum": 42, "model": "lojistik"})
        m = model_kur(C).fit(Xe, ye)
        takip.metrik(d, "egitim_auc",
                     roc_auc_score(ye, m.predict_proba(Xe)[:, 1]))
        takip.metrik(d, "test_auc",
                     roc_auc_score(yt, m.predict_proba(Xt)[:, 1]))
        yol = "calisma/model_%d.joblib" % d
        joblib.dump(m, yol)
        takip.artefakt(d, yol)

    print("%-3s %-8s %-8s %-8s %-9s %-9s" %
          ("id", "C", "git", "veri", "egitim", "test"))
    for satir in takip.sirala("test_auc"):
        did, ad, git, veri, C, skor = satir
        egitim = takip.db.execute(
            "SELECT deger FROM metrik WHERE deney=? AND "
            "anahtar='egitim_auc'", (did,)).fetchone()[0]
        print("%-3d %-8s %-8s %-8s %-9.4f %-9.4f" %
              (did, C, git[:7], veri[:8], egitim, skor))
