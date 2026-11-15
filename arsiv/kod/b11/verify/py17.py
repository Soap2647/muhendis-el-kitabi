from collections import deque

def bagli_mi(n, kenarlar):
    komsu = [[] for _ in range(n)]
    for u, v in kenarlar:
        komsu[u].append(v)
        komsu[v].append(u)
    gorulen = {0}
    kuyruk = deque([0])
    while kuyruk:
        u = kuyruk.popleft()
        for v in komsu[u]:
            if v not in gorulen:
                gorulen.add(v)
                kuyruk.append(v)
    return len(gorulen) == n

def agac_mi(n, kenarlar):
    return bagli_mi(n, kenarlar) and len(kenarlar) == n - 1

print(agac_mi(5, [(0, 1), (1, 2), (1, 3), (1, 4)]))
print(agac_mi(4, [(0, 1), (1, 2), (2, 0), (2, 3)]))
print(agac_mi(5, [(0, 1), (1, 2), (0, 2), (3, 4)]))
