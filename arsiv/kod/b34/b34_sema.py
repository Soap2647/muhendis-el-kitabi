# b34_sema.py: İHA filo şeması ve sabit tohumlu veri
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

DDL = """
CREATE TABLE ussler (
  id INTEGER PRIMARY KEY,
  ad TEXT NOT NULL UNIQUE,
  kapasite INTEGER NOT NULL
);
CREATE TABLE baglanti (
  kaynak INTEGER NOT NULL REFERENCES ussler(id),
  hedef INTEGER NOT NULL REFERENCES ussler(id),
  mesafe_km REAL NOT NULL,
  PRIMARY KEY (kaynak, hedef)
);
CREATE TABLE ucak (
  id INTEGER PRIMARY KEY,
  kuyruk TEXT NOT NULL UNIQUE,
  tip TEXT NOT NULL,
  us_id INTEGER REFERENCES ussler(id),
  uretim_yili INTEGER NOT NULL,
  durum TEXT NOT NULL
);
CREATE TABLE gorev (
  id INTEGER PRIMARY KEY,
  ucak_id INTEGER REFERENCES ucak(id),
  baslangic TEXT NOT NULL,
  gorev_tipi TEXT NOT NULL,
  durum TEXT NOT NULL
);
CREATE TABLE ucus (
  id INTEGER PRIMARY KEY,
  gorev_id INTEGER NOT NULL REFERENCES gorev(id),
  kalkis TEXT NOT NULL,
  sure_dk INTEGER NOT NULL
);
CREATE TABLE telemetri (
  id INTEGER PRIMARY KEY,
  ucus_id INTEGER NOT NULL REFERENCES ucus(id),
  zaman_sn INTEGER NOT NULL,
  irtifa_m REAL,
  gerilim_v REAL NOT NULL
);
CREATE TABLE ekipman (
  id INTEGER PRIMARY KEY,
  ust_id INTEGER REFERENCES ekipman(id),
  ad TEXT NOT NULL
);
CREATE TABLE bakim (
  id INTEGER PRIMARY KEY,
  ucak_id INTEGER NOT NULL REFERENCES ucak(id),
  ekipman_id INTEGER NOT NULL REFERENCES ekipman(id),
  tarih TEXT NOT NULL,
  maliyet_tl REAL NOT NULL
);
"""

USSLER = [
    "Ana Üs",
    "Kuzey Üs",
    "Doğu Üs",
    "Batı Üs",
    "Güney Üs",
    "Sahil Üs",
    "Dağ Üs",
    "Ova Üs",
    "Liman Üs",
    "Ara İst. A",
    "Ara İst. B",
    "Kapalı Üs",
]
EKIPMAN = [  # (id, ust_id, ad): kök İHA, alt sistemler, bileşenler
    (1, None, "İHA"),
    (2, 1, "Motor"),
    (3, 1, "Aviyonik"),
    (4, 1, "Güç"),
    (5, 1, "Gövde"),
    (6, 1, "Haberleşme"),
    (7, 2, "Pervane"),
    (8, 2, "Şanzıman"),
    (9, 2, "Yakıt pompası"),
    (10, 3, "IMU"),
    (11, 3, "GPS"),
    (12, 3, "Uçuş bilgisayarı"),
    (13, 4, "Batarya"),
    (14, 4, "Regülatör"),
    (15, 13, "Hücre A"),
    (16, 13, "Hücre B"),
    (17, 5, "Kanat"),
    (18, 5, "Kuyruk"),
    (19, 6, "Veri linki"),
    (20, 6, "Anten"),
]


def kur(yol, seed=34):
    if os.path.exists(yol):
        os.remove(yol)
    con = sqlite3.connect(yol)
    con.executescript(DDL)
    r = random.Random(seed)
    con.executemany(
        "INSERT INTO ussler VALUES (?,?,?)",
        [
            (i + 1, ad, r.randint(4, 20))
            for i, ad in enumerate(USSLER)
        ],
    )
    # 1..11 birbirine bağlı; 12 (Kapalı Üs) yalnızca çıkış verir
    kenar = {(12, 1)}
    for a in range(1, 12):
        for b in r.sample(range(1, 12), 3):
            if a != b:
                kenar.add((a, b))
    con.executemany(
        "INSERT INTO baglanti VALUES (?,?,?)",
        [
            (a, b, round(r.uniform(40, 400), 1))
            for a, b in sorted(kenar)
        ],
    )
    tipler = ["KESIF", "TAARRUZ", "LOJISTIK"]
    ucak = []
    for i in range(1, 61):
        yil = r.randint(2016, 2025) if i <= 55 else 2025
        durum = r.choices(
            ["hazir", "bakimda", "devre_disi"], [7, 2, 1]
        )[0]
        ucak.append(
            (
                i,
                "UA-%03d" % i,
                r.choice(tipler),
                r.randint(1, 11),
                yil,
                durum,
            )
        )
    con.executemany("INSERT INTO ucak VALUES (?,?,?,?,?,?)", ucak)

    # 9000 görev; %3'ü henüz uçağa atanmamış (NULL), %8'i iptal
    bas = datetime(2025, 1, 1)
    gorev, ucus, tel = [], [], []
    for g in range(1, 9001):
        t = bas + timedelta(minutes=r.randrange(0, 60 * 24 * 630))
        ucak_id = None if r.random() < 0.03 else r.randint(1, 55)
        durum = "iptal" if r.random() < 0.08 else "tamam"
        gorev.append(
            (
                g,
                ucak_id,
                t.strftime("%Y-%m-%d %H:%M"),
                r.choice(["KESIF", "GOZETLEME", "ISARET"]),
                durum,
            )
        )
        if durum == "tamam" and ucak_id is not None:
            kalkis = t + timedelta(minutes=r.randint(0, 30))
            sure = r.randint(20, 240)
            uid = len(ucus) + 1
            ucus.append(
                (uid, g, kalkis.strftime("%Y-%m-%d %H:%M"), sure)
            )
            dusuk = r.random() < 0.03  # %3 uçuşta gerilim çöküşü
            for zs in range(0, sure * 60 + 1, 300):  # 5 dk örnek
                f = zs / (sure * 60)
                irt = 120 * min(1.0, 6 * f, 6 * (1 - f)) + r.gauss(
                    0, 3
                )
                ger = 25.2 - 3.0 * f + r.gauss(0, 0.05)
                if dusuk and 0.4 < f < 0.6:
                    ger -= 1.5
                tel.append(
                    (
                        len(tel) + 1,
                        uid,
                        zs,
                        None if r.random() < 0.02 else round(irt, 1),
                        round(ger, 2),
                    )
                )
    con.executemany("INSERT INTO gorev VALUES (?,?,?,?,?)", gorev)
    con.executemany("INSERT INTO ucus VALUES (?,?,?,?)", ucus)
    con.executemany("INSERT INTO telemetri VALUES (?,?,?,?,?)", tel)

    con.executemany("INSERT INTO ekipman VALUES (?,?,?)", EKIPMAN)
    bakim = [
        (
            i,
            r.randint(1, 60),
            r.randint(1, 20),
            "%04d-%02d-%02d"
            % (
                r.choice([2025, 2026]),
                r.randint(1, 12),
                r.randint(1, 28),
            ),
            round(r.uniform(500, 50000), 2),
        )
        for i in range(1, 801)
    ]
    con.executemany("INSERT INTO bakim VALUES (?,?,?,?,?)", bakim)
    con.commit()
    return con


if __name__ == "__main__":
    con = kur(sys.argv[1] if len(sys.argv) > 1 else "iha.db")
    for t in [
        "ussler",
        "baglanti",
        "ucak",
        "gorev",
        "ucus",
        "telemetri",
        "ekipman",
        "bakim",
    ]:
        n = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("%-10s %8d" % (t, n))
    con.close()
