# -*- coding: utf-8 -*-
"""RM ve EDF zamanlanabilirlik analizi (tam sayi zamanli).

Gorev (C, T): islem suresi C, periyot T, son teslim D = T.
  U = toplam(C/T)
  RM siniri (Liu & Layland 1973): n(2^(1/n) - 1)  (yeterli)
  RTA: R = C_i + toplam ceil(R/T_j) * C_j  (j: daha yuksek oncelik)
  EDF (kesilebilir, D = T): U <= 1 yeter ve gerekir.
"""
import csv
import math
import random


def rms_siniri(n):
    return n * (2 ** (1.0 / n) - 1)


def kullanim(gorevler):
    return sum(c / t for c, t in gorevler)


def rta(gorevler):
    """Periyoda gore sirala (RM). Her gorev icin yanit suresi."""
    sirali = sorted(gorevler, key=lambda g: g[1])
    sonuc = []
    for i, (c, t) in enumerate(sirali):
        r = c
        while True:
            yeni = c + sum(math.ceil(r / tj) * cj
                           for cj, tj in sirali[:i])
            if yeni == r:
                break
            r = yeni
            if r > t:                           # yakinsamadi
                break
        sonuc.append((c, t, r if r <= t else None))
    return sonuc


def rta_uygun(gorevler):
    return all(r is not None for _, _, r in rta(gorevler))


def simule(gorevler, politika):
    """Kesilebilir RM ya da EDF. Doner: (kacirilan, dilimler)."""
    ufuk = math.lcm(*[t for _, t in gorevler])
    isler, kacan, dilim = [], 0, []
    for t in range(ufuk):
        for idx, (c, p) in enumerate(gorevler):
            if t % p == 0:
                isler.append([c, t + p, idx])   # kalan, son, no
        for j in isler:
            if j[0] > 0 and t >= j[1]:
                kacan += 1                      # son teslim kacti
                j[0] = 0
        isler = [j for j in isler if j[0] > 0]
        etiket = None
        if isler:
            if politika == "RM":
                sec = min(isler,
                          key=lambda j: (gorevler[j[2]][1], j[1]))
            else:
                sec = min(isler,
                          key=lambda j: (j[1], gorevler[j[2]][1]))
            sec[0] -= 1
            etiket = sec[2]
        if dilim and dilim[-1][2] == etiket and dilim[-1][1] == t:
            dilim[-1] = (dilim[-1][0], t + 1, etiket)
        else:
            dilim.append((t, t + 1, etiket))
    for j in isler:                             # donem sonu kacaklari
        if j[0] > 0 and ufuk >= j[1]:
            kacan += 1
    return kacan, dilim


def rastgele_kumeler(tohum, adet=1000, n=3):
    """UUniFast (Bini & Buttazzo 2005) ile rastgele kume."""
    rnd = random.Random(tohum)
    kumeler = []
    for _ in range(adet):
        kalan = rnd.uniform(0.6, 1.0)
        us = []
        for i in range(1, n):
            sonraki = kalan * rnd.random() ** (1.0 / (n - i))
            us.append(kalan - sonraki)
            kalan = sonraki
        us.append(kalan)
        kumeler.append([(max(1, round(u * t)), t) for u, t in
                        ((u, rnd.randint(4, 40)) for u in us)])
    return kumeler


if __name__ == "__main__":
    ornek = [(1, 4), (2, 6), (3, 12)]
    print("== Ornek 1:", ornek)
    print("U = %.4f  RM siniri = %.4f" % (kullanim(ornek),
                                         rms_siniri(3)))
    print("RTA:", rta(ornek))
    print("RM kacirilan:", simule(ornek, "RM")[0])
    ornek2 = [(2, 5), (4, 7)]
    print("== Ornek 2:", ornek2, "U = %.4f" % kullanim(ornek2))
    print("RTA:", rta(ornek2))
    print("RM kacirilan:", simule(ornek2, "RM")[0])
    print("EDF kacirilan:", simule(ornek2, "EDF")[0])
    print("== 1000 rastgele kume, n=3, tohum=44 ==")
    sayac = {"RM siniri": 0, "RTA": 0, "EDF U<=1": 0, "sim RM": 0,
             "RTA-sim ters": 0, "EDF sim": 0, "EDF-U ters": 0}
    for g in rastgele_kumeler(44):
        u, ok_rta = kullanim(g), rta_uygun(g)
        ok_sim = simule(g, "RM")[0] == 0
        sayac["RM siniri"] += u <= rms_siniri(3)
        sayac["RTA"] += ok_rta
        sayac["EDF U<=1"] += u <= 1.0
        sayac["sim RM"] += ok_sim
        sayac["RTA-sim ters"] += ok_rta != ok_sim
        ok_edf = simule(g, "EDF")[0] == 0
        sayac["EDF sim"] += ok_edf
        sayac["EDF-U ters"] += ok_edf != (u <= 1.0)
    for k, v in sayac.items():
        print("%-13s %4d / 1000" % (k, v))
    with open("b44_rms_zaman.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["senaryo", "bas", "son", "gorev"])
        for ad, g, pol in (("RM_ornek1", ornek, "RM"),
                           ("RM_ornek2", ornek2, "RM"),
                           ("EDF_ornek2", ornek2, "EDF")):
            for bas, son, et in simule(g, pol)[1]:
                w.writerow([ad, bas, son,
                            "" if et is None else et + 1])
