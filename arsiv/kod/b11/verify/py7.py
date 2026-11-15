graf = {
    0: {1, 2},
    1: {0, 3},
    2: {0, 3},
    3: {1, 2, 4},
    4: {3},
}
print(graf[3])           # {1, 2, 4}
print(len(graf[3]))      # 3: derece
print(4 in graf[3])      # True: kenar var mi?
print(sorted(graf[0]))   # [1, 2]
