# b34_join.py: JOIN türleri, LEFT JOIN + WHERE tuzağı, öz birleşim
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])


def say(sql):
    return c.execute(sql).fetchone()[0]


print(
    "INNER:",
    say(
        "SELECT COUNT(*) FROM ucak u JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "LEFT :",
    say(
        "SELECT COUNT(*) FROM ucak u LEFT JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "RIGHT:",
    say(
        "SELECT COUNT(*) FROM ucak u RIGHT JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "FULL :",
    say(
        "SELECT COUNT(*) FROM ucak u FULL JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "CROSS:", say("SELECT COUNT(*) FROM ussler a CROSS JOIN ussler b")
)
print(
    "WHERE ile filtre:",
    say(
        "SELECT COUNT(*) FROM ucak u LEFT JOIN gorev g "
        "ON g.ucak_id = u.id WHERE g.durum = 'iptal'"
    ),
)
print(
    "ON ile filtre   :",
    say(
        "SELECT COUNT(*) FROM ucak u LEFT JOIN gorev g "
        "ON g.ucak_id = u.id AND g.durum = 'iptal'"
    ),
)
print("öz birleşim (ekipman -> üst):")
for ad, ust in c.execute(
    "SELECT c.ad, p.ad FROM ekipman c "
    "LEFT JOIN ekipman p ON p.id = c.ust_id "
    "WHERE c.id IN (1, 7, 15) ORDER BY c.id"
):
    print("  %-10s -> %s" % (ad, ust))
