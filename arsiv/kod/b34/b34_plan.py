# b34_plan.py: indeks kullanım kuralları, gerçek planlarla
import os
import shutil
import sqlite3
import sys
import tempfile

kopya = os.path.join(tempfile.mkdtemp(), "plan.db")
shutil.copyfile(sys.argv[1], kopya)
c = sqlite3.connect(kopya)
c.execute("CREATE INDEX ix_tel_uz ON telemetri(ucus_id, zaman_sn)")
c.execute("CREATE INDEX ix_uk ON ucak(kuyruk)")
SORGULAR = [
    "WHERE ucus_id = 5 AND zaman_sn > 600",
    "WHERE zaman_sn = 600",
    "WHERE ucus_id + 0 = 5",
    "WHERE ucus_id BETWEEN 5 AND 9 ORDER BY zaman_sn",
    "WHERE ucus_id = 5 ORDER BY zaman_sn",
]
for kosul in SORGULAR:
    plan = c.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM telemetri " + kosul
    ).fetchall()
    print(kosul)
    for satir in plan:
        print("    ", satir[3])
for kosul in [
    "WHERE kuyruk = 'UA-001'",
    "WHERE kuyruk LIKE 'UA-00%'",
    "WHERE kuyruk LIKE '%001'",
]:
    print("ucak", kosul)
    print(
        "    ",
        c.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM ucak " + kosul
        ).fetchone()[3],
    )
c.execute("PRAGMA case_sensitive_like = ON")
print("case_sensitive_like = ON, ucak LIKE 'UA-00%':")
print(
    "    ",
    c.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM ucak "
        "WHERE kuyruk LIKE 'UA-00%'"
    ).fetchone()[3],
)
c.close()
