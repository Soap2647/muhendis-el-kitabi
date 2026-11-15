from collections import deque
import string

def komsular(kelime, kume):
    for i in range(len(kelime)):
        for c in string.ascii_lowercase:
            aday = kelime[:i] + c + kelime[i + 1:]
            if aday != kelime and aday in kume:
                yield aday

def merdiven(bas, hedef, kume):
    onceki = {bas: None}
    kuyruk = deque([bas])
    while kuyruk:
        u = kuyruk.popleft()
        if u == hedef:
            yol = []
            while u is not None:
                yol.append(u)
                u = onceki[u]
            return yol[::-1]
        for v in komsular(u, kume):
            if v not in onceki:
                onceki[v] = u
                kuyruk.append(v)
    return None

kume = {"kar", "bar", "bas", "tas", "kas", "kat", "tat", "mat"}
yol = merdiven("kar", "tas", kume)
print(" -> ".join(yol), "(%d adim)" % (len(yol) - 1))
print(merdiven("kar", "yok", kume))
