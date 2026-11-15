# -*- coding: utf-8 -*-
# b33_9_seri.py: çakışma serileştirilebilirliği
import itertools
import random


def cakisma_kenarlari(s):
    """s: [(islem, 'R' ya da 'W', nesne)], zaman sırasıyla.
    Farklı işlemler aynı nesneye erişir ve en az biri W ise
    çakışırlar; kenar, önce gelenden sonra gelene gider."""
    kenar = set()
    for i, j in itertools.combinations(range(len(s)), 2):
        ti, ai, xi = s[i]
        tj, aj, xj = s[j]
        if ti != tj and xi == xj and "W" in (ai, aj):
            kenar.add((ti, tj))
    return kenar


def dongu_var_mi(kenar, dugumler):
    komsu = {d: [b for a, b in kenar if a == d] for d in dugumler}
    durum = {d: 0 for d in dugumler}   # 0 yeni, 1 yolda, 2 bitti

    def ara(d):
        durum[d] = 1
        for e in komsu[d]:
            if durum[e] == 1:
                return True
            if durum[e] == 0 and ara(e):
                return True
        durum[d] = 2
        return False

    return any(durum[d] == 0 and ara(d) for d in dugumler)


def seri_olabilir_mi(s):
    """Kaba kuvvet: bir seri sıra tüm kenarları koruyor mu?"""
    kenar = cakisma_kenarlari(s)
    dugum = sorted({t for t, _, _ in s})
    for p in itertools.permutations(dugum):
        konum = {t: k for k, t in enumerate(p)}
        if all(konum[a] < konum[b] for a, b in kenar):
            return True
    return False


def goster(ad, s):
    dizi = " ".join("%s%d(%s)" % (a, t, x) for t, a, x in s)
    k = sorted(cakisma_kenarlari(s))
    dugum = sorted({t for t, _, _ in s})
    print(ad, dizi)
    print("   kenarlar:", k, " dongu:", dongu_var_mi(k, dugum))


if __name__ == "__main__":
    # S1: kayıp güncelleme (lost update)
    S1 = [(1, "R", "X"), (2, "R", "X"),
          (1, "W", "X"), (2, "W", "X")]
    # S2: iki işlem farklı verilerle; seri eşdeğer
    S2 = [(1, "R", "A"), (1, "W", "A"), (2, "R", "A"),
          (2, "W", "A"), (1, "R", "B"), (1, "W", "B")]
    goster("S1:", S1)
    goster("S2:", S2)
    print("S1 seri olabilir mi:", seri_olabilir_mi(S1))
    print("S2 seri olabilir mi:", seri_olabilir_mi(S2))

    # Doğrulama: iki yöntem her rastgele programda uyuşmalı.
    rnd = random.Random(33)
    uyusan = bozuk = 0
    for _ in range(3000):
        n = rnd.randint(3, 6)
        s = [(rnd.randint(1, 3), rnd.choice("RW"),
              rnd.choice("XYZ")) for _ in range(n)]
        dugum = sorted({t for t, _, _ in s})
        graf = not dongu_var_mi(sorted(cakisma_kenarlari(s)), dugum)
        if graf == seri_olabilir_mi(s):
            uyusan += 1
        else:
            bozuk += 1
    print("3000 rastgele: uyusan=%d uyusmayan=%d" % (uyusan, bozuk))
