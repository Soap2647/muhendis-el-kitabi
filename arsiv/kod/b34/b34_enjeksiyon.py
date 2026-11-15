# b34_enjeksiyon.py: birleştirme ile parametre bağlama; salt okunur
import sqlite3
import sys

c = sqlite3.connect(":memory:")
c.executescript("""
CREATE TABLE ucak (id INTEGER PRIMARY KEY, kuyruk TEXT, durum TEXT);
INSERT INTO ucak VALUES (1, 'UA-001', 'hazir'),
  (2, 'UA-002', 'bakimda'), (3, 'UA-003', 'devre_disi');
""")


def tehlikeli(kuyruk):
    sql = (
        "SELECT id, kuyruk FROM ucak WHERE kuyruk = '" + kuyruk + "'"
    )
    return c.execute(sql).fetchall()


def guvenli(kuyruk):
    return c.execute(
        "SELECT id, kuyruk FROM ucak WHERE kuyruk = ?", (kuyruk,)
    ).fetchall()


saldiri = "x' OR '1'='1"
print("birleştirme, normal girdi:", tehlikeli("UA-002"))
print("birleştirme, saldırı     :", tehlikeli(saldiri))
print("parametre, normal girdi  :", guvenli("UA-002"))
print("parametre, saldırı       :", guvenli(saldiri))
try:
    tehlikeli("x'; DELETE FROM ucak; --")
except sqlite3.Error as e:
    print("birden fazla deyim:", type(e).__name__)
    print("  mesaj:", e)
print(
    "kayıt sayısı:",
    c.execute("SELECT COUNT(*) FROM ucak").fetchone()[0],
)

ro = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
try:
    ro.execute("DELETE FROM ucak")
except sqlite3.OperationalError as e:
    print("salt okunur bağlantı:", e)
