# __dict__ / __slots__ bayt olcumu (tracemalloc) -> engine/veri CSV
import csv, os, tracemalloc
KOK = r"D:\Mevcut Projeler\Kitap\engine\veri"

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

satirlar = []
for n in [10**3, 10**4, 10**5, 10**6]:
    d = olc(Nokta, n); s = olc(NoktaS, n)
    satirlar.append([n, "%.1f" % d, "%.1f" % s])
    print(n, "%.1f" % d, "%.1f" % s)
with open(os.path.join(KOK, "b20_bellek_olcum.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "dict_bayt", "slots_bayt"])
    w.writerows(satirlar)
