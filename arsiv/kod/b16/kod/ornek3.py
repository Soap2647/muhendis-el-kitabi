# ornek3.py: kelime bolme (word break) ve geri kurma
import random


def kelime_bol(s, sozluk):
    n = len(s)
    kaynak = [None] * (n + 1)   # kaynak[i]: s[:i] icin kesim noktasi
    kaynak[0] = -1              # bos onek bolunebilir
    for i in range(1, n + 1):
        for j in range(i):
            if kaynak[j] is not None and s[j:i] in sozluk:
                kaynak[i] = j
                break
    if kaynak[n] is None:
        return None, kaynak
    parcalar, i = [], n
    while i > 0:
        j = kaynak[i]
        parcalar.append(s[j:i])
        i = j
    return parcalar[::-1], kaynak


def tum_bolmeler(s, sozluk):
    if s == "":
        return [[]]
    sonuc = []
    for i in range(1, len(s) + 1):
        if s[:i] in sozluk:
            for kalan in tum_bolmeler(s[i:], sozluk):
                sonuc.append([s[:i]] + kalan)
    return sonuc


def main():
    sozluk = {"yazi", "yazilim", "muhendis", "ligi", "li", "gi"}
    s = "yazilimmuhendisligi"
    parcalar, kaynak = kelime_bol(s, sozluk)
    print("bolme:", parcalar)
    erisim = {i: k for i, k in enumerate(kaynak) if k is not None}
    print("kaynak:", erisim)
    print("yok:", kelime_bol("yazilimx", sozluk)[0])
    rnd = random.Random(42)
    harfler = "abc"
    hata = 0
    for _ in range(300):
        sz = {"".join(rnd.choice(harfler)
                      for _ in range(rnd.randint(1, 3)))
              for _ in range(rnd.randint(1, 5))}
        t = "".join(rnd.choice(harfler)
                    for _ in range(rnd.randint(0, 8)))
        p, _ = kelime_bol(t, sz)
        var = len(tum_bolmeler(t, sz)) > 0
        if (p is not None) != var:
            hata += 1
        if p is not None and ("".join(p) != t or
                              any(w not in sz for w in p)):
            hata += 1
    print("300 rastgele ornek, hata:", hata)


if __name__ == "__main__":
    main()
