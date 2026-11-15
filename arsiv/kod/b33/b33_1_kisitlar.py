# -*- coding: utf-8 -*-
# b33_1_kisitlar.py: NOT NULL, UNIQUE, CHECK, yabancı anahtar
import sqlite3


def dene(bag, sql, args=()):
    try:
        bag.execute(sql, args)
        return "tamam"
    except sqlite3.IntegrityError as e:
        return "HATA: " + str(e)


SEMA = """
CREATE TABLE ogrenci(
  no     INTEGER PRIMARY KEY,
  ad     TEXT NOT NULL,
  eposta TEXT UNIQUE,
  yas    INTEGER CHECK (yas BETWEEN 15 AND 80));
CREATE TABLE kayit(
  id     INTEGER PRIMARY KEY,
  ogr_no INTEGER NOT NULL REFERENCES ogrenci(no)
         ON DELETE CASCADE,
  ders   TEXT NOT NULL,
  UNIQUE (ogr_no, ders));
CREATE TABLE tez(
  id     INTEGER PRIMARY KEY,
  ogr_no INTEGER REFERENCES ogrenci(no)
         ON DELETE RESTRICT);
"""

print("sqlite", sqlite3.sqlite_version)
c = sqlite3.connect(":memory:")
fk = c.execute("PRAGMA foreign_keys").fetchone()[0]
print("foreign_keys (varsayilan):", fk)
c.execute("PRAGMA foreign_keys = ON")
c.executescript(SEMA)
c.execute("INSERT INTO ogrenci VALUES (1,'Ayşe','a@x.com',21)")
c.execute("INSERT INTO ogrenci VALUES (2,'Mert','m@x.com',20)")
c.execute("INSERT INTO kayit(ogr_no,ders) VALUES (1,'VT')")
c.execute("INSERT INTO kayit(ogr_no,ders) VALUES (1,'OS')")
c.execute("INSERT INTO tez(ogr_no) VALUES (2)")

ekle = "INSERT INTO ogrenci VALUES (%s)"
print("NOT NULL :", dene(c, ekle % "3,NULL,'b',20"))
print("UNIQUE   :", dene(c, ekle % "3,'Ali','a@x.com',20"))
print("CHECK    :", dene(c, ekle % "4,'Veli','v@x',10"))
kay = "INSERT INTO kayit(ogr_no,ders) VALUES (%s)"
print("FK yok   :", dene(c, kay % "99,'AG'"))
print("UNIQUE(c):", dene(c, kay % "1,'VT'"))

# Aynı yabancı anahtar, FK kapalıyken sessizce kabul edilir.
d = sqlite3.connect(":memory:")
d.executescript(SEMA)
print("FK kapali:", dene(d, kay % "99,'AG'"))

print("--- silme davranisi ---")
c.execute("DELETE FROM ogrenci WHERE no = 1")
n = c.execute("SELECT COUNT(*) FROM kayit").fetchone()[0]
print("kayit satiri (CASCADE):", n)
print("silme (RESTRICT):",
      dene(c, "DELETE FROM ogrenci WHERE no = 2"))
