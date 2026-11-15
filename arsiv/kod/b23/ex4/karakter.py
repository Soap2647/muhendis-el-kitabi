import hashlib
import importlib
import json
import random
import sys


def girdi_uret(rng):
    satirlar = []
    for _ in range(rng.randint(0, 25)):
        r = rng.random()
        if r < 0.05:
            satirlar.append("   ")
        elif r < 0.08:
            satirlar.append("# yorum satiri")
        elif r < 0.12:
            satirlar.append("ALFA;12;abc;V")
        elif r < 0.15:
            satirlar.append("BETA;xy;1.0;V")
        elif r < 0.18:
            satirlar.append("GAMA;5;2.0;kV")
        else:
            cihaz = rng.choice(["ALFA", "BETA", "GAMA", "DELTA"])
            zaman = str(rng.randint(0, 999))
            deger = "%.4f" % rng.uniform(2.0, 4.5)
            if rng.random() < 0.3:
                deger = "%.1f" % rng.uniform(2000, 4500)
            birim = rng.choice(["V", "V", "mV"])
            satirlar.append(";".join([cihaz, zaman, deger, birim]))
    return satirlar


def ozet(modul_adi):
    modul = importlib.import_module(modul_adi)
    rng = random.Random(42)
    sonuc = []
    for _ in range(300):
        cikti = modul.rapor_uret(girdi_uret(rng))
        ham = cikti.encode("utf-8")
        sonuc.append(hashlib.sha256(ham).hexdigest())
    return sonuc


if __name__ == "__main__":
    if sys.argv[1] == "--kaydet":
        ozetler = ozet(sys.argv[2])
        with open("golden.json", "w", encoding="utf-8") as f:
            json.dump(ozetler, f)
        print("kaydedildi:", sys.argv[2], len(ozetler))
    else:
        with open("golden.json", encoding="utf-8") as f:
            beklenen = json.load(f)
        gercek = ozet(sys.argv[1])
        bozuk = [i for i, (a, b) in enumerate(zip(beklenen, gercek))
                 if a != b]
        print("sinanan:", len(gercek), "bozuk:", len(bozuk),
              "ilk:", bozuk[:3])
