import random
from ex1_eski import f
from ex1_yeni import kritik_ozet

def uret(rng):
    kayitlar = []
    for z in range(rng.randint(0, 30)):
        g = None if rng.random() < 0.08 else rng.uniform(60, 100)
        s = None if rng.random() < 0.08 else rng.uniform(20, 90)
        kayitlar.append((float(z), g, s, rng.choice([0, 1, 1])))
    return kayitlar

def calistir(fn, *a):
    try:
        return ("ok", fn(*a))
    except ValueError as e:
        return ("hata", str(e))

if __name__ == "__main__":
    rng = random.Random(42)
    sayac = {"toplam": 0, "dolu": 0, "uyusmayan": 0}
    for _ in range(5000):
        kay = uret(rng)
        esik = rng.uniform(55, 95)
        for mod in ("ortalama", "liste", "bilinmeyen"):
            sayac["toplam"] += 1
            eski = calistir(f, kay, esik, mod)
            yeni = calistir(kritik_ozet, kay, esik, mod)
            if eski[1] is not None and eski[0] == "ok":
                sayac["dolu"] += 1
            if eski != yeni:
                sayac["uyusmayan"] += 1
    print("toplam:", sayac["toplam"], "dolu:", sayac["dolu"],
          "uyusmayan:", sayac["uyusmayan"])
