# b34_kodokuma.py: SQLite optimizer belgesi 2.1 kurallarını sına
import sqlite3

c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE ex1 (a, b, c, d, e)")
c.execute("CREATE INDEX idx_ex1 ON ex1(a, b, c, d)")
ORNEKLER = [
    "a=5 AND b IN (1,2,3) AND d='hello'",
    "a=5 AND b=1 AND c=2 AND d='x'",
    "b IN (1,2,3) AND c NOT NULL AND d='hello'",
    "a=5 OR b IN (1,2,3) OR c NOT NULL OR d='hello'",
    "a>5 AND b=1",
]
for kosul in ORNEKLER:
    plan = c.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM ex1 WHERE " + kosul
    ).fetchall()
    print("WHERE", kosul)
    print("   ->", plan[0][3])
