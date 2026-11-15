# b34_kilit.py: kayıp güncelleme, iyimser kilit, kilitlenme ve WAL
import os
import sqlite3
import tempfile
import threading
import time

p = os.path.join(tempfile.mkdtemp(prefix="b34_"), "kilit.db")


def kur():
    c = sqlite3.connect(p, autocommit=True)
    c.execute("DROP TABLE IF EXISTS sayac")
    c.execute(
        "CREATE TABLE sayac (id INTEGER PRIMARY KEY, "
        "deger INTEGER NOT NULL, surum INTEGER NOT NULL DEFAULT 0)"
    )
    c.execute("INSERT INTO sayac (id, deger) VALUES (1, 100)")
    return c


def kayip_guncelleme():
    print("== kayıp güncelleme (kilit yok) ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, autocommit=True)
    da = a.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[0]
    db_ = b.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[
        0
    ]
    print("A okudu:", da)
    print("B okudu:", db_)
    a.execute("UPDATE sayac SET deger=? WHERE id=1", (da + 10,))
    print("A yazdı (+10):", da + 10)
    b.execute("UPDATE sayac SET deger=? WHERE id=1", (db_ + 5,))
    print("B yazdı (+5):", db_ + 5, "-> beklenen 115")
    son = a.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[
        0
    ]
    print("son değer:", son)
    a.close()
    b.close()


def iyimser_kilit():
    print("== iyimser kilit (surum sütunu) ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, autocommit=True)
    ra = a.execute(
        "SELECT deger, surum FROM sayac WHERE id=1"
    ).fetchone()
    rb = b.execute(
        "SELECT deger, surum FROM sayac WHERE id=1"
    ).fetchone()
    print("A okudu:", ra)
    print("B okudu:", rb)
    n = a.execute(
        "UPDATE sayac SET deger=?, surum=surum+1 "
        "WHERE id=1 AND surum=?",
        (ra[0] + 10, ra[1]),
    ).rowcount
    print("A yazdı: satır =", n)
    n = b.execute(
        "UPDATE sayac SET deger=?, surum=surum+1 "
        "WHERE id=1 AND surum=?",
        (rb[0] + 5, rb[1]),
    ).rowcount
    print("B yazdı: satır =", n, "-> çakışma, yeniden okunuyor")
    rb = b.execute(
        "SELECT deger, surum FROM sayac WHERE id=1"
    ).fetchone()
    print("B yeniden okudu:", rb)
    n = b.execute(
        "UPDATE sayac SET deger=?, surum=surum+1 "
        "WHERE id=1 AND surum=?",
        (rb[0] + 5, rb[1]),
    ).rowcount
    print("B yazdı: satır =", n)
    print(
        "son değer:",
        a.execute(
            "SELECT deger, surum FROM sayac " "WHERE id=1"
        ).fetchone(),
    )
    a.close()
    b.close()


def kilitlenme():
    print("== kilitlenme (rollback journal) ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, timeout=0, autocommit=True)
    a.execute("BEGIN IMMEDIATE")
    a.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
    print("A BEGIN IMMEDIATE ve yazdı, commit yok")
    try:
        b.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
        print("B yazdı")
    except sqlite3.OperationalError as e:
        print("B yazamadı:", e)
    a.execute("COMMIT")
    a.close()
    b.close()
    print("== kilitlenme: busy_timeout ile bekleme ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    a.execute("BEGIN IMMEDIATE")
    a.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
    sonuc = []

    def b_is():
        b = sqlite3.connect(p, timeout=5, autocommit=True)
        b.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
        sonuc.append("B yazdı (bekledi)")
        b.close()

    t = threading.Thread(target=b_is)
    t.start()
    time.sleep(0.5)
    print("A commit ediyor")
    a.execute("COMMIT")
    t.join()
    print(sonuc[0])
    print(
        "son değer:",
        a.execute("SELECT deger FROM sayac").fetchone()[0],
    )
    a.close()


def wal():
    print("== WAL: okuyucu yazıcıyı engellemez ==")
    kur()
    c = sqlite3.connect(p, autocommit=True)
    print(
        "journal_mode:",
        c.execute("PRAGMA journal_mode=WAL").fetchone()[0],
    )
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, timeout=0, autocommit=True)
    a.execute("BEGIN IMMEDIATE")
    a.execute("UPDATE sayac SET deger=999 WHERE id=1")
    print(
        "B okudu (A commit etmedi):",
        b.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[0],
    )
    try:
        b.execute("UPDATE sayac SET deger=1 WHERE id=1")
    except sqlite3.OperationalError as e:
        print("B yazamadı:", e)
    a.execute("COMMIT")
    print(
        "A commit sonrası B okudu:",
        b.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[0],
    )
    for x in (a, b, c):
        x.close()


if __name__ == "__main__":
    kayip_guncelleme()
    iyimser_kilit()
    kilitlenme()
    wal()
