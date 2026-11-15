# mst_kesme.py: kesme ozelligini kucuk rastgele cizgelerde dogrular.
# Her kesim (S, V - S) icin, kesimi gecen en hafif kenar e, bazi
# minimum yayan agacta yer alir mi? Tum yayan agaclar kaba kuvvetle
# listelenir (n <= 5, bu yuzden denemek ucuzdur).
import itertools
import random


def bagli(n, kenarlar):
    komsu = {i: [] for i in range(n)}
    for u, v, _ in kenarlar:
        komsu[u].append(v)
        komsu[v].append(u)
    gorulen, yigin = {0}, [0]
    while yigin:
        x = yigin.pop()
        for y in komsu[x]:
            if y not in gorulen:
                gorulen.add(y)
                yigin.append(y)
    return len(gorulen) == n


def minimum_yayan_agaclar(n, kenarlar):
    en_az, agaclar = None, []
    for sec in itertools.combinations(kenarlar, n - 1):
        if bagli(n, sec):
            w = sum(k[2] for k in sec)
            if en_az is None or w < en_az:
                en_az, agaclar = w, [sec]
            elif w == en_az:
                agaclar.append(sec)
    return agaclar


def main():
    rnd = random.Random(42)
    kesim_testi = ihlal = minimum_olmayan = 0
    for _ in range(300):
        n = rnd.randint(3, 5)
        tum = list(itertools.combinations(range(n), 2))
        m = rnd.randint(n, len(tum))
        secilen = rnd.sample(tum, m)
        kenarlar = [(u, v, rnd.randint(1, 6)) for u, v in secilen]
        if not bagli(n, kenarlar):
            continue
        msts = minimum_yayan_agaclar(n, kenarlar)
        for maske in range(1, (1 << n) - 1):
            S = {i for i in range(n) if maske >> i & 1}
            C = [k for k in kenarlar if (k[0] in S) != (k[1] in S)]
            en_hafif = min(k[2] for k in C)
            for k in C:
                bulundu = any(k in t for t in msts)
                if k[2] == en_hafif:
                    kesim_testi += 1
                    if not bulundu:
                        ihlal += 1
                elif not bulundu:
                    minimum_olmayan += 1
    print("kesim testi (en hafif kenar):", kesim_testi)
    print("ihlal (hicbir MST'de yok):", ihlal)
    print("minimum olmayan kenar, MST'de yok:", minimum_olmayan)


if __name__ == "__main__":
    main()
