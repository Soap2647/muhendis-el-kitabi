# -*- coding: utf-8 -*-
"""Benzersiz ve tekrar eden satırları karıştırıp algoritma farkını ara."""
import random, subprocess, sys
def satir_sayisi(a, x, algo):
    out = subprocess.run(["git", "-c", "core.autocrlf=false", "diff",
                          "--no-index", "--unified=0",
                          "--diff-algorithm=" + algo, a, x],
                         capture_output=True).stdout.decode("utf-8")
    return [l for l in out.splitlines() if l.startswith(("+", "-"))
            and not l.startswith(("+++", "---"))]
random.seed(38)
sayac = 0
for deneme in range(int(sys.argv[1])):
    n = random.randint(14, 22)
    eski = []
    for i in range(n):
        r = random.random()
        if r < 0.3:
            eski.append("}")
        elif r < 0.45:
            eski.append("")
        else:
            eski.append("u%02d = %d;" % (i, i))
    yeni = list(eski)
    # küçük bir blok taşı: 3-4 satırlık bir parçayı başka yere koy
    bas = random.randrange(0, n - 4)
    blok = yeni[bas:bas + 4]
    del yeni[bas:bas + 4]
    hedef = random.randrange(0, len(yeni))
    yeni[hedef:hedef] = blok
    open("e.c", "w", encoding="utf-8").write("\n".join(eski) + "\n")
    open("y.c", "w", encoding="utf-8").write("\n".join(yeni) + "\n")
    sonuc = {a: satir_sayisi("e.c", "y.c", a)
             for a in ("myers", "patience", "histogram")}
    if len({len(v) for v in sonuc.values()}) > 1:
        sayac += 1
        if sayac == 1:
            print("deneme", deneme)
            print("eski:", eski)
            print("yeni:", yeni)
            for a, v in sonuc.items():
                print(a, len(v))
print("uzunluk farkli sonuc:", sayac)
