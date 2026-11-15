# b34_ornek2.py: hiç görev almamış uçaklar ve NULL tuzağı
import sqlite3
import sys

SORGULAR = {
    "LEFT JOIN": """
        SELECT u.id FROM ucak u
        LEFT JOIN gorev g ON g.ucak_id = u.id
        WHERE g.id IS NULL ORDER BY u.id""",
    "NOT IN": """
        SELECT u.id FROM ucak u
        WHERE u.id NOT IN (SELECT ucak_id FROM gorev)
        ORDER BY u.id""",
    "NOT EXISTS": """
        SELECT u.id FROM ucak u
        WHERE NOT EXISTS (SELECT 1 FROM gorev g
                          WHERE g.ucak_id = u.id)
        ORDER BY u.id""",
}


def kucuk_kume():
    c = sqlite3.connect(":memory:")
    c.executescript("""
    CREATE TABLE ucak (id INTEGER PRIMARY KEY);
    CREATE TABLE gorev (id INTEGER PRIMARY KEY, ucak_id INTEGER);
    INSERT INTO ucak VALUES (1), (2), (3);
    INSERT INTO gorev VALUES (1, 1), (2, NULL), (3, 1);
    """)
    for ad, sql in SORGULAR.items():
        print("küçük %-10s:" % ad, c.execute(sql).fetchall())
    c.close()


if __name__ == "__main__":
    kucuk_kume()
    c = sqlite3.connect(sys.argv[1])
    for ad, sql in SORGULAR.items():
        sonuc = [r[0] for r in c.execute(sql)]
        print("veri %-10s: %d uçak" % (ad, len(sonuc)))
    print(
        "NULL'lu görev sayısı:",
        c.execute(
            "SELECT COUNT(*) FROM gorev WHERE ucak_id IS NULL"
        ).fetchone()[0],
    )
