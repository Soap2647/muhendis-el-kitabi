# b34_ornek4.py: rapor sorgusu, plan ve indeks (geniş ve dar)
import shutil
import sqlite3
import statistics
import sys
import textwrap
import time

GENIS = """
SELECT g.ucak_id, COUNT(*) AS ornek,
       ROUND(AVG(t.gerilim_v), 3) AS ort_ger,
       SUM(CASE WHEN t.gerilim_v < 23.0 THEN 1 ELSE 0 END) AS dusuk
FROM gorev g
JOIN ucus x ON x.gorev_id = g.id
JOIN telemetri t ON t.ucus_id = x.id
WHERE g.durum = 'tamam' AND g.baslangic >= '2026-01-01'
GROUP BY g.ucak_id
ORDER BY dusuk DESC, g.ucak_id
LIMIT 5
"""
DAR = """
SELECT COUNT(*), ROUND(AVG(t.gerilim_v), 3),
       SUM(CASE WHEN t.gerilim_v < 23.0 THEN 1 ELSE 0 END)
FROM gorev g
JOIN ucus x ON x.gorev_id = g.id
JOIN telemetri t ON t.ucus_id = x.id
WHERE g.ucak_id = 7 AND g.baslangic >= '2026-03-01'
  AND g.baslangic < '2026-04-01'
"""


def plan(c, sql, baslik):
    print("--", baslik)
    for satir in c.execute("EXPLAIN QUERY PLAN " + sql):
        print(
            textwrap.fill(
                satir[3],
                70,
                initial_indent="   ",
                subsequent_indent="       ",
            )
        )


def olc(c, sql, n=7):
    sure = []
    for _ in range(n):
        t0 = time.perf_counter()
        sonuc = c.execute(sql).fetchall()
        sure.append((time.perf_counter() - t0) * 1000)
    return statistics.median(sure), sonuc


if __name__ == "__main__":
    kopya = "b34_rapor_kopya.db"
    shutil.copyfile(sys.argv[1], kopya)
    c = sqlite3.connect(kopya)
    for ad, sql in [("geniş", GENIS), ("dar", DAR)]:
        plan(c, sql, ad + " sorgu, indeks yokken")
        ms, s0 = olc(c, sql)
        print("medyan: %.3f ms" % ms)
    c.execute(
        "CREATE INDEX ix_gorev_ucak_bas ON gorev(ucak_id, baslangic)"
    )
    c.execute(
        "CREATE INDEX ix_gorev_durum ON gorev(durum, baslangic)"
    )
    c.execute("CREATE INDEX ix_ucus_gorev ON ucus(gorev_id)")
    c.execute("CREATE INDEX ix_tel_ucus ON telemetri(ucus_id)")
    for ad, sql in [("geniş", GENIS), ("dar", DAR)]:
        plan(c, sql, ad + " sorgu, indeksler sonrası")
        ms, s1 = olc(c, sql)
        print("medyan: %.3f ms" % ms)
        print("sonuç aynı mı:", olc(c, sql, 1)[1] == s1)
    print("dar sonuç:", s1)
    c.close()
