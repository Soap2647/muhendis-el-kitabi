# -*- coding: utf-8 -*-
# b33_5_normal.py: anomaliler, BCNF, kayıpsızlık, korunum
import itertools
import sqlite3

from b33_4_fd import fd, kapanis, aday_anahtarlar
from b33_4_fd import bcnf_ihlalleri

R = ("ogr_no ogr_ad bolum baskan ders_kodu ders_ad "
     "not_").split()
F = [fd(["ogr_no"], ["ogr_ad", "bolum"]),
     fd(["bolum"], ["baskan"]),
     fd(["ders_kodu"], ["ders_ad"]),
     fd(["ogr_no", "ders_kodu"], ["not_"])]
print("aday anahtar:", [sorted(k) for k in aday_anahtarlar(R, F)])

# ---- Kötü tasarım: tek tablo ----
db = sqlite3.connect(":memory:")
db.execute("""CREATE TABLE ogrenci_ders(
    ogr_no INTEGER NOT NULL, ogr_ad TEXT, bolum TEXT,
    baskan TEXT, ders_kodu TEXT NOT NULL, ders_ad TEXT,
    not_ INTEGER, PRIMARY KEY (ogr_no, ders_kodu))""")
db.executemany("INSERT INTO ogrenci_ders VALUES (?,?,?,?,?,?,?)", [
    (1, "Ayşe", "BM", "Dr. X", "VT", "Veritabanı", 88),
    (1, "Ayşe", "BM", "Dr. X", "OS", "İşletim Sis.", 75),
    (2, "Mert", "BM", "Dr. X", "VT", "Veritabanı", 91),
    (3, "Ali", "EE", "Dr. Y", "DEV", "Devre", 60)])
db.execute("UPDATE ogrenci_ders SET baskan='Dr. Z' "
           "WHERE ogr_no=1 AND ders_kodu='VT'")
print("guncelleme anomalisi:", db.execute(
    "SELECT DISTINCT bolum, baskan FROM ogrenci_ders "
    "WHERE bolum='BM'").fetchall())
try:
    db.execute("INSERT INTO ogrenci_ders(ogr_no,ders_kodu,ders_ad) "
               "VALUES (NULL,'MAT101','Matematik')")
except sqlite3.IntegrityError as e:
    print("ekleme anomalisi:", e)
db.execute("DELETE FROM ogrenci_ders WHERE ogr_no=3")
print("silme anomalisi (Ali):", db.execute(
    "SELECT COUNT(*) FROM ogrenci_ders "
    "WHERE ogr_ad='Ali'").fetchone()[0])


def bcnf_ayir(S, F):
    """İhlal bulunca S'yi X+ ve S-(X+ - X) olarak böler."""
    S = frozenset(S)
    ihlal = bcnf_ihlalleri(S, F)
    if not ihlal:
        return [S]
    X, _ = ihlal[0]
    X = frozenset(X)
    Xp = kapanis(X, F) & S
    R1, R2 = Xp, S - (Xp - X)
    return bcnf_ayir(R1, F) + bcnf_ayir(R2, F)


def kayipsiz_mi(R, ayrik, F):
    """Tablo (chase) testi: bir satır tümüyle 'a' olursa kayıpsız."""
    idx = {a: i for i, a in enumerate(R)}
    T = [[("a", a) if a in S else ("b", i, a) for a in R]
         for i, S in enumerate(ayrik)]
    degisti = True
    while degisti:
        degisti = False
        for X, Y in F:
            for r1, r2 in itertools.combinations(T, 2):
                if not all(r1[idx[a]] == r2[idx[a]] for a in X):
                    continue
                for a in Y:
                    k = idx[a]
                    if r1[k] != r2[k]:
                        yeni = min(r1[k], r2[k])
                        eski = max(r1[k], r2[k])
                        for satir in T:
                            if satir[k] == eski:
                                satir[k] = yeni
                        degisti = True
    return any(all(h[0] == "a" for h in s) for s in T)


def korunuyor_mu(F, ayrik):
    """Her FD için: Z := X; ayrıklar üzerinden genişlet; Y ⊆ Z?"""
    for X, Y in F:
        Z = set(X)
        degisti = True
        while degisti:
            degisti = False
            for S in ayrik:
                yeni = kapanis(Z & S, F) & S
                if not yeni <= Z:
                    Z |= yeni
                    degisti = True
        if not set(Y) <= Z:
            return False
    return True


if __name__ == "__main__":
    ayrik = bcnf_ayir(R, F)
    print("BCNF ayrisimi:")
    for S in ayrik:
        print("  ", sorted(S))
    print("kayipsiz:", kayipsiz_mi(R, ayrik, F),
          " korunuyor:", korunuyor_mu(F, ayrik))
    # Kayıp örneği: AB->C ve C->B; BCNF bağımlılığı kaybeder.
    RA, FA = "A B C".split(), [fd("AB", "C"), fd("C", "B")]
    ayrikA = bcnf_ayir(RA, FA)
    print("A,B,C ayrisimi:", [sorted(S) for S in ayrikA])
    print("  kayipsiz:", kayipsiz_mi(RA, ayrikA, FA),
          " korunuyor:", korunuyor_mu(FA, ayrikA))
    # Kayıplı ayrışım: ortak nitelik C'ye bağlı değil.
    print("kayipli {A,C},{B,C}:", kayipsiz_mi(
        "A B C".split(), [{"A", "C"}, {"B", "C"}], [fd("A", "B")]))
