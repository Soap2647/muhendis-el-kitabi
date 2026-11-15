import random
random.seed(42)

# Ornek 1
def sayac_b(n):
    s = 0
    for i in range(n):
        for j in range(i):
            s += 1
    for k in range(n):
        s += 1
    return s

print("Ornek1 n, ikinci-ic, dis, toplam, n(n+1)/2")
for n in range(1, 6):
    ic = n * (n - 1) // 2
    print(n, ic, n, sayac_b(n), n * (n + 1) // 2)

# Ornek 2: cok-pop yigini, potansiyel = eleman sayisi
class YiginCokPop:
    def __init__(self):
        self.veri = []
    def push(self, x):
        self.veri.append(x)
        return 1
    def multipop(self, k):
        c = 0
        while self.veri and c < k:
            self.veri.pop()
            c += 1
        return c

y = YiginCokPop()
islemler = [("push", 1), ("push", 2), ("push", 3), ("push", 4),
            ("multipop", 3), ("push", 5), ("multipop", 10)]
phi_onc = 0
toplam_gercek = toplam_am = 0
print("Ornek2")
for ad, arg in islemler:
    if ad == "push":
        g = y.push(arg)
    else:
        g = y.multipop(arg)
    phi_son = len(y.veri)
    am = g + phi_son - phi_onc
    toplam_gercek += g
    toplam_am += am
    print(ad, arg, "gercek", g, "phi", phi_onc, "->", phi_son, "amort", am)
    phi_onc = phi_son
print("toplam gercek", toplam_gercek, "toplam amort", toplam_am)

# Ornek 3: tournament maksimum
cagri = [0]
def maks_bol(a, lo, hi, seviye, sayac):
    if hi - lo == 1:
        return a[lo]
    orta = (lo + hi) // 2
    sol = maks_bol(a, lo, orta, seviye + 1, sayac)
    sag = maks_bol(a, orta, hi, seviye + 1, sayac)
    sayac[seviye] = sayac.get(seviye, 0) + 1
    return sol if sol >= sag else sag
a = [3, 9, 1, 7, 4, 8, 2, 6]
s = {}
m = maks_bol(a, 0, 8, 0, s)
print("Ornek3 max", m, "karsilastirma seviyeye gore", s, "toplam", sum(s.values()))

# Ornek 4: heapify seviye tablosu n=15 (perfect, H=3)
H = 3
print("Ornek4 yukseklik h, dugum sayisi, h*dugum")
toplam = 0
for h in range(H + 1):
    d = 2 ** (H - h)
    toplam += h * d
    print(h, d, h * d)
print("toplam", toplam)
