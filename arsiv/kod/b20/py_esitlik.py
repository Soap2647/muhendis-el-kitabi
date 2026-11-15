# __eq__ / __hash__ sozlesmesi ve referans semantigi
class Nokta:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __eq__(self, diger):
        return (self.x, self.y) == (diger.x, diger.y)

try:
    {Nokta(1, 2)}
except TypeError as e:
    print("TypeError:", e)
print("__hash__ =", Nokta.__hash__)

class Nokta2:                       # hash'i de tanimla: ayni (x,y) ayni h
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __eq__(self, d):
        return (self.x, self.y) == (d.x, d.y)
    def __hash__(self):
        return hash((self.x, self.y))

a, b = Nokta2(1, 2), Nokta2(1, 2)
print("esit:", a == b, " ayni hash:", hash(a) == hash(b))
kume = {a}
print("b kumede mi:", b in kume)
a.x = 99                            # kumeye koyduktan sonra degistirdik
print("eski degere bakinca:", Nokta2(1, 2) in kume,
      "| iceriden:", a in kume)

# Referans semantigi: liste ve kopyalar
satir = [1, 2]
ic = [satir, satir]                 # ayni listenin iki etiketi
ic[0].append(3)
print("ic:", ic)
s = [[1], [2]]
sig = s.copy()                      # sig kabuk kopya: ic listeler paylasilir
sig[0].append(9)
print("s:", s)
import copy
derin = copy.deepcopy(s)
derin[0].append(7)
print("s (derin sonrasi):", s, " derin:", derin)
