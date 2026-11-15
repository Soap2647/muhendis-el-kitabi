# -*- coding: utf-8 -*-
# b33_3_cebir.py: küçük bir ilişkisel cebir motoru
import random
import sqlite3


class Iliski:
    """Nitelikler + demetler. Küme anlamı: yinelenen yok."""

    def __init__(self, nitelikler, demetler=()):
        self.n = tuple(nitelikler)
        self.d = []
        for t in demetler:
            t = tuple(t)
            assert len(t) == len(self.n)
            if t not in self.d:
                self.d.append(t)

    def sut(self, ad):
        return self.n.index(ad)

    def satir(self, t):
        return dict(zip(self.n, t))


def sigma(r, kosul):
    """Seçme: koşulu sağlayan demetleri tut."""
    return Iliski(r.n, [t for t in r.d if kosul(r.satir(t))])


def pi(r, nitelikler):
    """İzdüşüm: istenen sütunlar, yinelenenler atılır."""
    idx = [r.sut(a) for a in nitelikler]
    return Iliski(nitelikler, [tuple(t[i] for i in idx) for t in r.d])


def birlesim(r, s):
    assert r.n == s.n
    return Iliski(r.n, r.d + s.d)


def fark(r, s):
    assert r.n == s.n
    kume = set(s.d)
    return Iliski(r.n, [t for t in r.d if t not in kume])


def kartezyen(r, s):
    assert not set(r.n) & set(s.n)
    return Iliski(r.n + s.n, [t + u for t in r.d for u in s.d])


def dogal_birlestirme(r, s):
    """Ortak niteliklerde eşit olan demet çiftleri."""
    ortak = [a for a in r.n if a in s.n]
    ek = [a for a in s.n if a not in r.n]
    sonuc = []
    for t in r.d:
        for u in s.d:
            if all(t[r.sut(a)] == u[s.sut(a)] for a in ortak):
                sonuc.append(t + tuple(u[s.sut(a)] for a in ek))
    return Iliski(r.n + tuple(ek), sonuc)


def yeniden_adlandir(r, eski, yeni):
    return Iliski(tuple(yeni if a == eski else a for a in r.n),
                  r.d)


# ---- Küçük örnek ----
ogr = Iliski(("no", "ad"), [(1, "Ayşe"), (2, "Mert"), (1, "Ayşe")])
print("ogr (yinelenen atildi):", ogr.d)
print("pi(ad):", pi(ogr, ["ad"]).d)
kay = Iliski(("no", "ders"), [(1, "VT"), (1, "OS"), (2, "VT")])
print("ogr |x| kay:", dogal_birlestirme(ogr, kay).d)

# ---- Rastgele verilerle SQLite karşılaştırması (tohum 33) ----
rnd = random.Random(33)
R = Iliski(("og", "ders"), [(rnd.randint(1, 8), rnd.choice("ABCD"))
                            for _ in range(30)])
R2 = Iliski(("og", "ders"), [(rnd.randint(1, 8), rnd.choice("ABCD"))
                             for _ in range(30)])
S = Iliski(("ders", "hoca"), [(rnd.choice("ABCDE"),
                               rnd.choice("XYZ")) for _ in range(12)])
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE R(og, ders)")
db.execute("CREATE TABLE R2(og, ders)")
db.execute("CREATE TABLE S(ders, hoca)")
db.executemany("INSERT INTO R VALUES (?,?)", R.d)
db.executemany("INSERT INTO R2 VALUES (?,?)", R2.d)
db.executemany("INSERT INTO S VALUES (?,?)", S.d)


def sql(sorgu):
    return db.execute(sorgu).fetchall()


def esit(a, b):
    return sorted(a.d) == sorted(set(b))


print()
print("sigma og>4 :", esit(sigma(R, lambda s: s["og"] > 4),
      sql("SELECT og, ders FROM R WHERE og > 4")))
print("pi ders    :", esit(pi(R, ["ders"]),
      sql("SELECT ders FROM R")))
print("R |x| S    :", esit(dogal_birlestirme(R, S),
      sql("SELECT og, ders, hoca FROM R NATURAL JOIN S")))
print("R u R2     :", esit(birlesim(R, R2),
      sql("SELECT og, ders FROM R UNION "
          "SELECT og, ders FROM R2")))
print("R - R2     :", esit(fark(R, R2),
      sql("SELECT og, ders FROM R EXCEPT "
          "SELECT og, ders FROM R2")))
kart = kartezyen(yeniden_adlandir(R, "ders", "rd"), S)
print("R x S      :", len(kart.d) == sql(
    "SELECT COUNT(*) FROM (SELECT DISTINCT og, ders FROM R) "
    "CROSS JOIN (SELECT DISTINCT ders, hoca FROM S)")[0][0])
print("sqlite", sqlite3.sqlite_version)
