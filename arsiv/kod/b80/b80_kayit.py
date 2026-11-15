# -*- coding: utf-8 -*-
# b80_kayit.py: ch80 deney sonuclarini Bolum 77'nin deney takipcisine
# (SQLite) yazar. Her tohum icin bir deney: parametreler, metrikler,
# model dosyasi artefakt olarak SHA-256 ozetiyle kaydedilir.
import csv
import os
from b77_takip import Takip

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def satirlar():
    with open(
        os.path.join(VERI, "b80_detektor.csv"), encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))


def main():
    db = Takip(os.path.join(KLASOR, "deney.db"))
    rows = satirlar()
    for seed in (1, 2, 3):
        ad = "b80_yolo_t%d" % seed
        d = db.baslat(
            ad,
            "b80_veri:egitim3000:seed0",
            KLASOR,
            "torch-2.6.0+cu124",
        )
        db.parametre(
            d,
            {
                "tohum": seed,
                "epoch": 60,
                "bs": 64,
                "lr_max": 2e-3,
                "egitim_sahne": 3000,
            },
        )
        for r in rows:
            if r["yontem"] == "cnn" and int(r["tohum"]) == seed:
                db.metrik(d, r["kume"] + "_map50", r["map50"])
                db.metrik(d, r["kume"] + "_map5095", r["map5095"])
        db.artefakt(d, os.path.join(KLASOR, "yolo_t%d.pt" % seed))
    print(
        "kayit sayisi:",
        db.db.execute("SELECT COUNT(*) FROM deney").fetchone()[0],
    )
    for satir in db.sirala("test_map50"):
        print(
            "id=%d ad=%s test_map50=%.4f"
            % (satir[0], satir[1], satir[5])
        )


if __name__ == "__main__":
    main()
