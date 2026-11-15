# Kirilgan taban sinif: set alt sinifi, toplu metot tekil add'i
# cagirir mi?
class SayanKume(set):
    def __init__(self, *a):
        super().__init__(*a)
        self.eklenen = 0

    def add(self, x):
        self.eklenen += 1
        super().add(x)


s = SayanKume()
s.add(1)
print("add ile:", s.eklenen)
s.update([2, 3, 4])
print("update sonrasi eklenen:", s.eklenen, "| kume:", sorted(s))


# bilesim: ici bir set, her seyi biz yonetiriz
class SayanBilesik:
    def __init__(self):
        self._k = set()
        self.eklenen = 0

    def ekle(self, x):
        self.eklenen += 1
        self._k.add(x)

    def ekle_toplu(self, xs):
        for x in xs:
            self.ekle(x)                # tek giris noktasi


s2 = SayanBilesik()
s2.ekle(1)
s2.ekle_toplu([2, 3, 4])
print("bilesik eklenen:", s2.eklenen)
