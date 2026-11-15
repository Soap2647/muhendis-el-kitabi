import sqlite3


class OlcumDeposu:
    """Sensör ölçümlerini SQLite dosyasında tutar (Bölüm 34)."""

    def __init__(self, yol):
        self.con = sqlite3.connect(yol)
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS olcum ("
            " id INTEGER PRIMARY KEY,"
            " sensor INTEGER NOT NULL,"
            " deger REAL NOT NULL)")

    def ekle(self, sensor, deger):
        with self.con:
            self.con.execute(
                "INSERT INTO olcum(sensor, deger) VALUES (?, ?)",
                (sensor, deger))

    def son(self, sensor, n):
        cur = self.con.execute(
            "SELECT deger FROM olcum WHERE sensor = ? "
            "ORDER BY id DESC LIMIT ?", (sensor, n))
        return [satir[0] for satir in cur]

    def kapat(self):
        self.con.close()
