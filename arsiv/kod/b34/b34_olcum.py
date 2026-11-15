# b34_olcum.py: indeks, yazma ve N+1 ölçümleri (tohum: 34)
import csv
import os
import random
import sqlite3
import statistics
import sys
import tempfile
import time

from b34_sema import kur
from sqlalchemy import ForeignKey, create_engine, event, func, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)


def medyan_ms(fn, tekrar):
    sure = []
    for i in range(tekrar):
        t0 = time.perf_counter()
        fn(i)
        sure.append((time.perf_counter() - t0) * 1000.0)
    return round(statistics.median(sure), 4)


def yaz_csv(yol, satirlar, basliklar):
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)


def indeks_olcumu(db, cikti):
    r = random.Random(34)
    ucuslar = [r.randint(1, 8072) for _ in range(50)]
    aracler = [r.randint(1, 55) for _ in range(50)]
    con = sqlite3.connect(db)
    sorgular = {
        "telemetri_ucus_zaman": (
            "SELECT zaman_sn, gerilim_v FROM telemetri "
            "WHERE ucus_id = ? AND zaman_sn BETWEEN 600 AND 3600",
            ucuslar,
            [None, "ix_tel_uz ON telemetri(ucus_id, zaman_sn)"],
        ),
        "gorev_ucak_durum": (
            "SELECT COUNT(*) FROM gorev "
            "WHERE ucak_id = ? AND durum = 'tamam'",
            aracler,
            [None, "ix_g_ud ON gorev(ucak_id, durum)"],
        ),
        "gorev_ucak_tarih": (
            "SELECT id FROM gorev WHERE ucak_id = ? "
            "AND baslangic >= '2026-01-01'",
            aracler,
            [
                None,
                "ix_g_ub ON gorev(ucak_id, baslangic)",
                "ix_g_bu ON gorev(baslangic, ucak_id)",
            ],
        ),
    }
    satirlar = []
    for ad, (sql, parametreler, indeksler) in sorgular.items():
        for tanim in indeksler:
            ix = tanim.split(" ")[0] if tanim else ""
            if tanim:
                con.execute("CREATE INDEX %s" % tanim)
            ms = medyan_ms(
                lambda i: con.execute(
                    sql, (parametreler[i % 50],)
                ).fetchall(),
                50,
            )
            satirlar.append((ad, ix or "yok", ms))
            if tanim:
                con.execute("DROP INDEX %s" % ix)
    yaz_csv(
        os.path.join(cikti, "b34_indeks_olcum.csv"),
        satirlar,
        ["sorgu", "indeks", "medyan_ms"],
    )
    con.close()
    for s in satirlar:
        print("%-22s %-22s %9.4f ms" % s)


def yazma_olcumu(tmp, cikti):
    p = os.path.join(tmp, "yazma.db")
    satirlar = []
    for kip in ("otomatik", "tek_islem"):

        def koş(i, kip=kip):
            if os.path.exists(p):
                os.remove(p)
            c = sqlite3.connect(p, autocommit=True)
            c.execute(
                "CREATE TABLE kayit (id INTEGER PRIMARY KEY, "
                "ucus_id INTEGER, zaman_sn INTEGER, "
                "gerilim_v REAL)"
            )
            if kip == "tek_islem":
                c.execute("BEGIN")
            for k in range(1000):
                c.execute(
                    "INSERT INTO kayit (ucus_id, zaman_sn, "
                    "gerilim_v) VALUES (?, ?, ?)",
                    (k % 50, k * 300, 24.5),
                )
            if kip == "tek_islem":
                c.execute("COMMIT")
            c.close()

        ms = medyan_ms(koş, 5 if kip == "otomatik" else 9)
        satirlar.append(("ekle_1000_satir", kip, ms))
        print("%-18s %-10s %10.2f ms" % ("ekle_1000_satir", kip, ms))
    # indeksin yazma maliyeti: 100 000 satır tek işlemde
    for k, ixler in enumerate(
        [
            [],
            ["ucus_id"],
            ["ucus_id", "zaman_sn"],
            ["ucus_id", "zaman_sn", "gerilim_v"],
        ]
    ):

        def koş2(i, ixler=ixler):
            if os.path.exists(p):
                os.remove(p)
            c = sqlite3.connect(p)
            c.execute(
                "CREATE TABLE kayit (id INTEGER PRIMARY KEY, "
                "ucus_id INTEGER, zaman_sn INTEGER, "
                "gerilim_v REAL)"
            )
            for c_ad in ixler:
                c.execute(
                    "CREATE INDEX ix_%s ON kayit(%s)" % (c_ad, c_ad)
                )
            c.executemany(
                "INSERT INTO kayit (ucus_id, zaman_sn, "
                "gerilim_v) VALUES (?, ?, ?)",
                ((j % 50, j * 300, 24.5) for j in range(100000)),
            )
            c.commit()
            c.close()

        ms = medyan_ms(koş2, 9)
        satirlar.append(
            ("100k_satir_%d_indeks" % len(ixler), "tek_islem", ms)
        )
        print(
            "%-18s %-10s %10.2f ms"
            % ("100k_%d_indeks" % len(ixler), "tek_islem", ms)
        )
    yaz_csv(
        os.path.join(cikti, "b34_yazma_olcum.csv"),
        satirlar,
        ["senaryo", "kip", "medyan_ms"],
    )


class Base(DeclarativeBase):
    pass


class Ucak(Base):
    __tablename__ = "ucak"
    id: Mapped[int] = mapped_column(primary_key=True)
    kuyruk: Mapped[str]
    tip: Mapped[str]
    us_id: Mapped[int | None]
    uretim_yili: Mapped[int]
    durum: Mapped[str]
    gorevler: Mapped[list["Gorev"]] = relationship(
        back_populates="ucak"
    )


class Gorev(Base):
    __tablename__ = "gorev"
    id: Mapped[int] = mapped_column(primary_key=True)
    ucak_id: Mapped[int | None] = mapped_column(ForeignKey("ucak.id"))
    baslangic: Mapped[str]
    gorev_tipi: Mapped[str]
    durum: Mapped[str]
    ucak: Mapped[Ucak | None] = relationship(
        back_populates="gorevler"
    )


def n1_olcumu(db, cikti):
    satirlar = []
    engine = create_engine("sqlite:///" + db)
    con = sqlite3.connect(db)
    sayac = [0]
    con.set_trace_callback(
        lambda sql: sayac.__setitem__(0, sayac[0] + 1)
    )

    @event.listens_for(engine, "before_cursor_execute")
    def say(conn, cur, sql, params, ctx, many):
        sayac[0] += 1

    def ham_dongu(n):
        for uid in range(1, n + 1):
            con.execute(
                "SELECT MAX(x.kalkis) FROM ucus x JOIN gorev g "
                "ON g.id = x.gorev_id WHERE g.ucak_id = ?",
                (uid,),
            ).fetchone()

    def ham_tek(n):
        con.execute(
            "SELECT g.ucak_id, MAX(x.kalkis) FROM ucus x "
            "JOIN gorev g ON g.id = x.gorev_id "
            "WHERE g.ucak_id <= ? GROUP BY g.ucak_id",
            (n,),
        ).fetchall()

    def orm_skaler_n1(n):
        with Session(engine) as s:
            for uid in range(1, n + 1):
                s.scalar(
                    select(func.max(Gorev.baslangic)).where(
                        Gorev.ucak_id == uid
                    )
                )

    def orm_skaler_tek(n):
        with Session(engine) as s:
            s.execute(
                select(Gorev.ucak_id, func.max(Gorev.baslangic))
                .where(Gorev.ucak_id <= n)
                .group_by(Gorev.ucak_id)
            ).all()

    def orm_tembel(n):
        with Session(engine) as s:
            for u in s.scalars(select(Ucak).where(Ucak.id <= n)):
                len(u.gorevler)  # her uçak için ayrı SELECT

    def orm_secmeli(n):
        with Session(engine) as s:
            for u in s.scalars(
                select(Ucak)
                .where(Ucak.id <= n)
                .options(selectinload(Ucak.gorevler))
            ):
                len(u.gorevler)  # iki SELECT, toplam

    for n in (10, 30, 60):
        for ad, fn in [
            ("ham_dongu_n1", ham_dongu),
            ("ham_tek_join", ham_tek),
            ("orm_skaler_n1", orm_skaler_n1),
            ("orm_skaler_tek", orm_skaler_tek),
            ("orm_tembel_n1", orm_tembel),
            ("orm_selectinload", orm_secmeli),
        ]:
            sayac[0] = 0
            fn(n)
            sorgu = sayac[0]
            ms = medyan_ms(lambda i, fn=fn, n=n: fn(n), 20)
            satirlar.append((ad, n, sorgu, ms))
            print(
                "%-16s n=%2d sorgu=%3d %9.3f ms" % (ad, n, sorgu, ms)
            )
    con.close()
    engine.dispose()
    yaz_csv(
        os.path.join(cikti, "b34_n1_olcum.csv"),
        satirlar,
        ["yontem", "ucak_sayisi", "sorgu_sayisi", "medyan_ms"],
    )


if __name__ == "__main__":
    cikti = sys.argv[1] if len(sys.argv) > 1 else "."
    tmp = tempfile.mkdtemp(prefix="b34_")
    db = os.path.join(tmp, "iha.db")
    kur(db)
    print("== indeks ==")
    indeks_olcumu(db, cikti)
    print("== yazma ==")
    yazma_olcumu(tmp, cikti)
    print("== N+1 ==")
    n1_olcumu(db, cikti)
