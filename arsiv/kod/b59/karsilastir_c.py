# karsilastir_c.py -- C ciktisi ile Python ciktisini karsilastir
a = open("py_cikti2.txt").read().split()
b = open("c_cikti2.txt").read().split()
fark = sum(1 for x, y in zip(a, b) if x != y)
print("ornek: %d  C: %d  uyusmayan: %d  C sinif1: %d"
      % (len(a), len(b), fark, b.count("1")))
