# -*- coding: utf-8 -*-
# b33_8_acid.py: atomiklik (geri alma) ve çökme kurtarma
import os
import sqlite3
import subprocess
import sys

YOL = "b33_acid.db"


def sifirla(modu):
    for f in (YOL, YOL + "-wal", YOL + "-shm", YOL + "-journal"):
        if os.path.exists(f):
            os.remove(f)
    db = sqlite3.connect(YOL)
    db.execute("PRAGMA journal_mode = %s" % modu)
    db.execute("CREATE TABLE hesap(ad TEXT PRIMARY KEY, "
               "bakiye INTEGER CHECK (bakiye >= 0))")
    db.execute("INSERT INTO hesap VALUES ('A', 100), ('B', 50)")
    db.commit()
    db.close()


def transfer(db, a, b, miktar, kesinti=False):
    """A'dan düş, B'ye ekle. Aradaki kesinti iki yarıyı ayırır."""
    with db:                              # commit ya da rollback
        db.execute("UPDATE hesap SET bakiye=bakiye-? WHERE ad=?",
                   (miktar, a))
        if kesinti:
            raise RuntimeError("yarıda kesildi")
        db.execute("UPDATE hesap SET bakiye=bakiye+? WHERE ad=?",
                   (miktar, b))


# ---- 1. İçeride hata: yarım transfer geri alınır ----
sifirla("DELETE")
db = sqlite3.connect(YOL)
try:
    transfer(db, "A", "B", 30, kesinti=True)
except RuntimeError as e:
    print("hata:", e)
print("bakiyeler:",
      db.execute("SELECT ad, bakiye FROM hesap").fetchall())
print("toplam:", db.execute(
    "SELECT SUM(bakiye) FROM hesap").fetchone()[0])
db.close()


# ---- 2. Süreç çöker: commit edilmemiş işlem geri alınır ----
COCUK = r'''
import os, sqlite3, sys
yol, n, kip = sys.argv[1], int(sys.argv[2]), sys.argv[3]
db = sqlite3.connect(yol)
for i in range(n):
    db.execute("INSERT INTO kayit(v) VALUES (?)", ("x" * 200,))
if kip == "commit":
    db.commit()
else:
    print("  cocuk: ana=%d bayt, -journal=%s, -wal=%s" % (
        os.path.getsize(yol), os.path.exists(yol + "-journal"),
        os.path.exists(yol + "-wal") and
        os.path.getsize(yol + "-wal")))
    sys.stdout.flush()
os._exit(3)     # temiz kapanış yok: süreç anında ölür
'''


def cocuk_calistir(modu, n, kip):
    sifirla(modu)
    db = sqlite3.connect(YOL)
    db.execute("CREATE TABLE kayit(id INTEGER PRIMARY KEY, v TEXT)")
    db.commit()
    db.close()
    sys.stdout.flush()
    r = subprocess.run([sys.executable, "-c", COCUK, YOL,
                        str(n), kip])
    db = sqlite3.connect(YOL)
    sayi = db.execute("SELECT COUNT(*) FROM kayit").fetchone()[0]
    db.close()
    return r.returncode, sayi


for modu in ("DELETE", "WAL"):
    for kip in ("kesik", "commit"):
        kod, sayi = cocuk_calistir(modu, 20000, kip)
        print("%-6s %-7s cikis=%d kayit=%d"
              % (modu, kip, kod, sayi))
print("sqlite", sqlite3.sqlite_version)
