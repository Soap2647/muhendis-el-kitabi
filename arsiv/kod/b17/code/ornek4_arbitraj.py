# ornek4_arbitraj.py - Doviz arbitraji: log donusumu + negatif dongu.
# Kur degerleri ornektir; gercek piyasa kuru degildir.
import math

PB = ["USD", "EUR", "GBP"]
EPS = 1e-12


def negatif_dongu(n, kenar, tur_izi=True):
    """kenar: [(u, v, w)]. Tum dugumler 0'dan baslar
    (sanal kaynak gibi).
    Negatif dongu varsa dugumlerini dondurur, yoksa None."""
    dist = [0.0] * n
    ebeveyn = [-1] * n
    for t in range(1, n):                       # n-1 tur
        for u, v, w in kenar:
            if dist[u] + w < dist[v] - EPS:
                dist[v] = dist[u] + w
                ebeveyn[v] = u
        if tur_izi:
            print(f"  tur {t}:", [round(x, 4) for x in dist])
    for u, v, w in kenar:               # n. tur: gevserse dongu var
        if dist[u] + w < dist[v] - EPS:
            x = v
            for _ in range(n):          # n adim geri: dongunun icinde
                x = ebeveyn[x]
            dongu, y = [x], ebeveyn[x]
            while y != x:
                dongu.append(y)
                y = ebeveyn[y]
            dongu.append(x)
            return dongu[::-1]
    return None


def senaryo(ad, kurlar):
    print(f"== {ad} ==")
    kenar = [(u, v, -math.log(r)) for u, v, r in kurlar]
    for (u, v, _), (_, _, r) in zip(kenar, kurlar):
        print(f"  {PB[u]}->{PB[v]} kur {r}  "
              f"-ln(kur) = {-math.log(r):.4f}")
    dongu = negatif_dongu(len(PB), kenar)
    if dongu is None:
        print("  Negatif dongu yok: arbitraj yok.")
        return
    carpim = 1.0
    for a, b in zip(dongu, dongu[1:]):
        carpim *= next(r for u, v, r in kurlar if (u, v) == (a, b))
    print("  Dongu:", " -> ".join(PB[u] for u in dongu))
    print(f"  Dongu boyunca kur carpimi = {carpim:.4f}")


if __name__ == "__main__":
    senaryo("Arbitrajli", [(0, 1, 0.90), (1, 2, 0.90), (2, 0, 1.50)])
    senaryo("Arbitrajsiz", [(0, 1, 0.90), (1, 2, 0.90), (2, 0, 1.10)])
