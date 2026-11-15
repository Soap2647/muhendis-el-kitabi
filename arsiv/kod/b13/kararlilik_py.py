kayitlar = [("Ali", 3), ("Ayse", 1), ("Mert", 3), ("Zeynep", 1)]
print(sorted(kayitlar, key=lambda k: k[1]))
print(sorted(kayitlar, key=lambda k: k[1], reverse=True))
