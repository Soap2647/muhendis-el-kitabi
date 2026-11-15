# Nesne basina bellek (tracemalloc): dict ve slots karsilastirmasi
import csv
import tracemalloc


class Nokta:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class NoktaS:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


def olc(sinif, n):
    tracemalloc.start()
    liste = [sinif(i, i) for i in range(n)]
    anlik, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del liste
    return anlik / n


with open("bellek_olcum.csv", "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "dict_bayt", "slots_bayt"])
    for n in [10**3, 10**4, 10**5, 10**6]:
        w.writerow([n, "%.1f" % olc(Nokta, n),
                    "%.1f" % olc(NoktaS, n)])
print("yazildi")
