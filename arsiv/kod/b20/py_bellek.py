# __dict__ ve __slots__: bellek olcumu (tracemalloc)
import sys
import tracemalloc


class Nokta:                  # her nesnede __dict__ (sozluk) var
    def __init__(self, x, y):
        self.x = x
        self.y = y


# __slots__: sabit yuva, __dict__ yok
class NoktaS:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


N = 100_000


def olc(sinif):
    tracemalloc.start()
    liste = [sinif(i, i) for i in range(N)]
    anlik, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return anlik / N, liste


bayt_dict, l1 = olc(Nokta)
bayt_slot, l2 = olc(NoktaS)
print("n = %d nesne" % N)
print("__dict__  : %.1f bayt/nesne (olcum)" % bayt_dict)
print("__slots__ : %.1f bayt/nesne (olcum)" % bayt_slot)
n1, n2 = Nokta(1, 2), NoktaS(1, 2)
print("sys.getsizeof(Nokta) ornek  :", sys.getsizeof(n1),
      "+ __dict__:", sys.getsizeof(n1.__dict__))
print("sys.getsizeof(NoktaS) ornek :", sys.getsizeof(n2))
print("__dict__ var mi?", hasattr(n2, "__dict__"))
try:
    n2.z = 3
except AttributeError as e:
    print("AttributeError:", e)
