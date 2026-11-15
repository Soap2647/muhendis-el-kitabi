# b34_sira.py: sorgu yürütme sırası ve takma ad davranışı
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])
# 1) WHERE içinde SELECT takma adı: SQLite kabul eder (standart dışı)
print(
    "1)", c.execute("SELECT id AS u FROM ucak WHERE u = 3").fetchall()
)
# 2) Takma ad, aynı adlı sütunu gölgelemez: WHERE temel sütunu görür
print(
    "2)",
    c.execute(
        "SELECT id + 1000 AS id FROM ucak " "WHERE id = 3"
    ).fetchall(),
)
# 3) ORDER BY takma adı görür, çünkü SELECT bitmiştir
print(
    "3)",
    c.execute(
        "SELECT kuyruk, id + 1000 AS yeni FROM ucak "
        "ORDER BY yeni DESC LIMIT 2"
    ).fetchall(),
)
# 4) GROUP BY ve HAVING içinde takma ad (SQLite kabul eder)
print(
    "4)",
    c.execute(
        "SELECT us_id AS u, COUNT(*) AS n FROM ucak "
        "GROUP BY u HAVING n > 5 ORDER BY u "
        "LIMIT 3"
    ).fetchall(),
)
# 5) Standart çözüm: takma adı alt sorguda tanımla
print(
    "5)",
    c.execute(
        "SELECT u FROM (SELECT id AS u FROM ucak) " "WHERE u = 3"
    ).fetchall(),
)
