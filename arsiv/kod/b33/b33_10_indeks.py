# -*- coding: utf-8 -*-
# b33_10_indeks.py: indeks türüne göre sorgu planı
import sqlite3

c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE ogrenci(no INTEGER PRIMARY KEY, "
          "ad TEXT, bolum TEXT)")
c.execute("CREATE INDEX i_ad ON ogrenci(ad)")
c.execute("CREATE INDEX i_ad_bolum ON ogrenci(ad, bolum)")
for q in ["SELECT ad FROM ogrenci WHERE ad = 'x'",
          "SELECT ad, bolum FROM ogrenci WHERE ad = 'x'",
          "SELECT * FROM ogrenci WHERE ad = 'x'"]:
    plan = c.execute("EXPLAIN QUERY PLAN " + q).fetchone()[3]
    print(plan)
