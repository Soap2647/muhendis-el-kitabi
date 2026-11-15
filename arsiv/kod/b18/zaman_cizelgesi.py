# zaman_cizelgesi.py: tek makinede is siralama. Her is (p, w, d):
# p islem suresi, w agirlik, d son teslim. Smith kurali (p/w artan)
# toplam agirlikli tamamlama suresini; EDF (d artan) en buyuk
# gecikmeyi minimize eder. Kaba kuvvet: tum siralamalar (n <= 5).
import itertools
import random


def smith(isler):
    return sorted(isler, key=lambda j: j[0] / j[1])


def edf(isler):
    return sorted(isler, key=lambda j: j[2])


def sirali_maliyet(sira):
    t, agirlikli, gecikme = 0, 0, float("-inf")
    for p, w, d in sira:
        t += p
        agirlikli += w * t
        gecikme = max(gecikme, t - d)
    return agirlikli, gecikme


def kaba(isler):
    sonuclar = [sirali_maliyet(s)
                for s in itertools.permutations(isler)]
    return min(s[0] for s in sonuclar), min(s[1] for s in sonuclar)


def main():
    isler = [(3, 1, 4), (2, 5, 6), (4, 2, 12)]
    print("isler (p, w, d):", isler)
    print("smith sirasi:", smith(isler))
    print("  agirlikli:", sirali_maliyet(smith(isler))[0],
          "kaba:", kaba(isler)[0])
    print("edf sirasi  :", edf(isler))
    print("  en buyuk gecikme:", sirali_maliyet(edf(isler))[1],
          "kaba:", kaba(isler)[1])
    rnd = random.Random(42)
    hata_s = hata_e = hata_p = 0
    for _ in range(300):
        n = rnd.randint(1, 5)
        isler = [(rnd.randint(1, 9), rnd.randint(1, 9),
                  rnd.randint(1, 30)) for _ in range(n)]
        w_opt, g_opt = kaba(isler)
        if sirali_maliyet(smith(isler))[0] != w_opt:
            hata_s += 1
        if sirali_maliyet(edf(isler))[1] != g_opt:
            hata_e += 1
        # karsilastirma: yalnizca islem suresine gore (w yok sayilir)
        spt = sorted(isler, key=lambda j: j[0])
        if sirali_maliyet(spt)[0] != w_opt:
            hata_p += 1
    print("300 ornek, smith hatasi:", hata_s)
    print("300 ornek, edf hatasi:", hata_e)
    print("300 ornek, p'ye gore (yanlis) hatasi:", hata_p)


if __name__ == "__main__":
    main()
