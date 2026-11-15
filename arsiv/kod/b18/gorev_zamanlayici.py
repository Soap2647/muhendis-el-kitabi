# gorev_zamanlayici.py: ayni gorevler arasinda n adim soguma suresi
# olan zamanlayici. Her adimda hazir olan, en cok kalan gorevi
# calistir; hazir yoksa bekle. Sonuc uc yolla dogrulanir: acgozlu
# simulasyon, kapali formul ve tum durumlari tarayan tam arama (BFS).
import heapq
import random
from collections import Counter


def simulasyon(gorevler, n, plan=None):
    kalan = Counter(gorevler)
    yigin = [(-c, g) for g, c in kalan.items()]
    heapq.heapify(yigin)
    bekleme = []              # (hazir_olacagi_an, -kalan, gorev)
    t = 0
    while yigin or bekleme:
        while bekleme and bekleme[0][0] <= t:
            _, c, g = heapq.heappop(bekleme)
            heapq.heappush(yigin, (c, g))
        if yigin:
            c, g = heapq.heappop(yigin)
            if plan is not None:
                plan.append(g)
            if c + 1 < 0:     # kalan sayi bir azaldi
                heapq.heappush(bekleme, (t + n + 1, c + 1, g))
        elif plan is not None:
            plan.append("-")  # bekleme (bos adim)
        t += 1
    return t


def formul(gorevler, n):
    sayac = Counter(gorevler)
    en_cok = max(sayac.values())
    k = sum(1 for c in sayac.values() if c == en_cok)
    return max(len(gorevler), (en_cok - 1) * (n + 1) + k)


def tam_arama(gorevler, n):
    sayac = Counter(gorevler)
    isimler = sorted(sayac)
    kalan0 = tuple(sayac[g] for g in isimler)
    baslangic = (kalan0, (0,) * len(isimler))
    seviye, t = {baslangic}, 0
    while True:
        yeni = set()
        for kalan, sogu in seviye:
            if sum(kalan) == 0:
                return t
            for i in range(len(isimler)):
                if kalan[i] > 0 and sogu[i] == 0:
                    k2 = list(kalan)
                    k2[i] -= 1
                    s2 = [max(x - 1, 0) for x in sogu]
                    s2[i] = n
                    yeni.add((tuple(k2), tuple(s2)))
            # bekleme: hicbir gorev calistirilmaz
            yeni.add((kalan, tuple(max(x - 1, 0) for x in sogu)))
        seviye = yeni
        t += 1


def main():
    gorev = list("AAABBBCC")
    plan = []
    simulasyon(gorev, 2, plan)
    print("n=2 plan:", " ".join(plan))
    for n in (2, 3):
        print("gorevler=%s n=%d" % ("".join(gorev), n))
        print("  simulasyon:", simulasyon(gorev, n),
              "formul:", formul(gorev, n),
              "tam arama:", tam_arama(gorev, n))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        tip = rnd.randint(1, 3)
        m = rnd.randint(1, 8)
        gorev = [rnd.choice("ABC"[:tip]) for _ in range(m)]
        n = rnd.randint(0, 3)
        a = simulasyon(gorev, n)
        if not (a == formul(gorev, n) == tam_arama(gorev, n)):
            hata += 1
    print("300 rastgele ornek, uc yontem uyusmuyor:", hata)


if __name__ == "__main__":
    main()
