# -*- coding: utf-8 -*-
"""b40_3_sayfalama.py: Offset ve imlec (keyset) sayfalama."""

import base64
import json
import sqlite3


def veritabani():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE ucus (id INTEGER PRIMARY KEY, ad TEXT)")
    db.executemany(
        "INSERT INTO ucus (id, ad) VALUES (?, ?)",
        [(i, "U%02d" % i) for i in range(1, 11)],
    )
    return db


def offset_sayfa(db, sayfa, boyut):
    """OFFSET = (sayfa - 1) * boyut. Sayfa istemcide tutulur."""
    sorgu = "SELECT id FROM ucus ORDER BY id DESC LIMIT ? OFFSET ?"
    return [
        r[0] for r in db.execute(sorgu, (boyut, (sayfa - 1) * boyut))
    ]


def imlec_kodla(son_id):
    ham = json.dumps({"son": son_id}).encode("utf-8")
    return base64.urlsafe_b64encode(ham).decode("ascii")


def imlec_coz(imlec):
    return json.loads(base64.urlsafe_b64decode(imlec))["son"]


def keyset_sayfa(db, imlec, boyut):
    """Son gorulen kaydin id'sinden devam eder: WHERE id < son."""
    if imlec is None:
        sorgu, arg = (
            "SELECT id FROM ucus ORDER BY id DESC LIMIT ?",
            (boyut,),
        )
    else:
        sorgu = (
            "SELECT id FROM ucus WHERE id < ? "
            "ORDER BY id DESC LIMIT ?"
        )
        arg = (imlec_coz(imlec), boyut)
    ids = [r[0] for r in db.execute(sorgu, arg)]
    yeni = imlec_kodla(ids[-1]) if len(ids) == boyut else None
    return ids, yeni


def sil10(db):
    db.execute("DELETE FROM ucus WHERE id = 10")


def ekle11(db):
    db.execute("INSERT INTO ucus (id, ad) VALUES (11, 'U11')")


def offset_iki(degis):
    db = veritabani()
    s1 = offset_sayfa(db, 1, 3)
    degis(db)  # 1. ve 2. sayfa arasinda degisiklik
    return s1, offset_sayfa(db, 2, 3)


def keyset_iki(degis):
    db = veritabani()
    s1, imlec = keyset_sayfa(db, None, 3)
    degis(db)
    s2, _ = keyset_sayfa(db, imlec, 3)
    return s1, s2


if __name__ == "__main__":
    for ad, fn in (
        ("offset, sil", offset_iki),
        ("keyset, sil", keyset_iki),
    ):
        print(ad, "->", fn(sil10))
    for ad, fn in (
        ("offset, ekle", offset_iki),
        ("keyset, ekle", keyset_iki),
    ):
        print(ad, "->", fn(ekle11))
