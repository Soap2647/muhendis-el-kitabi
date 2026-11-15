# -*- coding: utf-8 -*-
# b33_2_null.py: NULL ve üç değerli mantık
import sqlite3

c = sqlite3.connect(":memory:")


def q(ifade):
    return c.execute("SELECT " + ifade).fetchone()[0]


def goster(v):
    if v is None:
        return "UNKNOWN"
    return "DOĞRU" if v else "YANLIŞ"


print("sqlite", sqlite3.sqlite_version)
print("NULL = NULL   ->", goster(q("NULL = NULL")))
print("NULL IS NULL  ->", goster(q("NULL IS NULL")))
print()
print("DOĞRU AND ?   ->", goster(q("1 AND NULL")))
print("YANLIŞ AND ?  ->", goster(q("0 AND NULL")))
print("DOĞRU OR ?    ->", goster(q("1 OR NULL")))
print("YANLIŞ OR ?   ->", goster(q("0 OR NULL")))
print("NOT ?         ->", goster(q("NOT NULL")))
print()

c.execute("CREATE TABLE n(x INTEGER)")
c.executemany("INSERT INTO n VALUES (?)", [(1,), (2,), (None,)])


def say(sorgu):
    return c.execute(sorgu).fetchone()[0]


print("x = NULL satir   :",
      say("SELECT COUNT(*) FROM n WHERE x = NULL"))
print("x IS NULL satir  :",
      say("SELECT COUNT(*) FROM n WHERE x IS NULL"))
print("x <> 1 satir     :",
      say("SELECT COUNT(*) FROM n WHERE x <> 1"))
print("COUNT(*)         :", say("SELECT COUNT(*) FROM n"))
print("COUNT(x)         :", say("SELECT COUNT(x) FROM n"))
print("AVG(x)           :", say("SELECT AVG(x) FROM n"))
print()
# Tuzak: NOT IN listesinde NULL varsa sonuç bilinmiyor olur.
print("3 NOT IN (1,2)      ->", goster(q("3 NOT IN (1, 2)")))
print("3 NOT IN (1,2,NULL) ->", goster(q("3 NOT IN (1, 2, NULL)")))
print("NULL'lu alt sorgu satir:",
      say("SELECT COUNT(*) FROM n "
          "WHERE 3 NOT IN (SELECT x FROM n)"))
