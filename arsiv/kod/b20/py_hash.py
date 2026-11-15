# __eq__ / __hash__ sozlesmesi (Bolum 9 hash tablosu ile baglanti)
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


# hash'i de tanimli: esit -> ayni hash
class Nokta2:
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
# kumeye koyduktan sonra degistirdik
a.x = 99
print("eski degere bakinca:", Nokta2(1, 2) in kume,
      "| iceriden:", a in kume)
