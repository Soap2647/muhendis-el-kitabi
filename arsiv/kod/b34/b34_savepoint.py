# b34_savepoint.py: işlem içinde SAVEPOINT ile kısmi geri alma
import sqlite3

c = sqlite3.connect(":memory:", isolation_level=None)
c.execute(
    "CREATE TABLE bakim_log (id INTEGER PRIMARY KEY, "
    "aciklama TEXT)"
)


def say():
    return c.execute("SELECT COUNT(*) FROM bakim_log").fetchone()[0]


c.execute("BEGIN")
c.execute(
    "INSERT INTO bakim_log (aciklama) VALUES ('motor kontrolü')"
)
c.execute("SAVEPOINT kisim")
c.execute(
    "INSERT INTO bakim_log (aciklama) VALUES ('pervane değişimi')"
)
c.execute("INSERT INTO bakim_log (aciklama) VALUES ('hatalı kayıt')")
print("savepoint içinde kayıt:", say())
c.execute("ROLLBACK TO kisim")
print("ROLLBACK TO sonrası   :", say())
c.execute("RELEASE kisim")
c.execute("COMMIT")
print("COMMIT sonrası        :", say())
print("işlem açık mı         :", c.in_transaction)
