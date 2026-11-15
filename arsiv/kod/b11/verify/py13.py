n = 7
kenarlar = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (5, 6)]
komsu = {u: set() for u in range(n)}
for u, v in kenarlar:
    komsu[u].add(v)
    komsu[v].add(u)
for u in range(n):
    print(u, len(komsu[u]), sorted(komsu[u]))
print("toplam derece:", sum(len(s) for s in komsu.values()))
print("2|E| =", 2 * len(kenarlar))
