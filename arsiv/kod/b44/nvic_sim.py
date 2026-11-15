# -*- coding: utf-8 -*-
"""Cevrim-duzeyi kesme denetleyicisi benzetimi (NVIC benzeri).

BENZETIM: Gercek bir MCU olcumu degildir. Zamanlamalar modelde
varsayilandir: ENTRY = 12 (kabul ve yiginlama), EXIT = 10 (cikis),
TAIL = 6 (kuyruk zinciri). Kucuk sayi = yuksek oncelik.
"""
import csv
import random
import statistics

ENTRY, EXIT, TAIL = 12, 10, 6
YOK = 99                      # calisan kesme yok: ana dongu


def simule(olaylar, ufuk, kuyruk=True, gec=True):
    """olaylar: [(varis, ad, oncelik, govde)]. Doner: (izler, gec)."""
    bekle = []                # bekleyen ornekler
    kalan = sorted(olaylar)
    yigin = []                # calisan ya da kesilmis isleyiciler
    faz, hedef, rem = "THREAD", None, 0
    izler, gecikmeler = [], []

    def en_iyi(esik):
        aday = [b for b in bekle if b["p"] < esik]
        if not aday:
            return None
        return min(aday, key=lambda b: (b["p"], b["v"]))

    def ust():
        return yigin[-1]["p"] if yigin else YOK

    for t in range(ufuk):
        while kalan and kalan[0][0] == t:
            v, ad, p, g = kalan.pop(0)
            bekle.append({"v": v, "ad": ad, "p": p, "g": g})
        if faz in ("THREAD", "HANDLER"):
            b = en_iyi(ust())
            if b is not None:               # kabul: yiginlama
                bekle.remove(b)
                hedef, faz, rem = b, "ENTRY", ENTRY
        if faz == "ENTRY" and gec:
            b = en_iyi(min(ust(), hedef["p"]))
            if b is not None:               # gec gelen: daha onemli
                bekle.remove(b)
                bekle.append(hedef)
                hedef = b
        if faz == "THREAD":
            izler.append((t, "T", ""))
        elif faz == "ENTRY":
            izler.append((t, "E", hedef["ad"]))
            rem -= 1
            if rem == 0:
                faz = "HANDLER"
                hedef["kalan"] = hedef["g"]
                gecikmeler.append((hedef["ad"], t + 1 - hedef["v"]))
                yigin.append(hedef)
                hedef = None
        elif faz == "HANDLER":
            ust_is = yigin[-1]
            izler.append((t, "H", ust_is["ad"]))
            ust_is["kalan"] -= 1
            if ust_is["kalan"] == 0:
                yigin.pop()
                if kuyruk:                  # kuyruk zinciri
                    aday = en_iyi(ust())
                    if aday is not None:
                        bekle.remove(aday)
                        hedef, faz, rem = aday, "TAIL", TAIL
                        continue
                faz, rem = "EXIT", EXIT
        elif faz == "EXIT":
            izler.append((t, "X", ""))
            rem -= 1
            if rem == 0:
                faz = "HANDLER" if yigin else "THREAD"
        elif faz == "TAIL":
            izler.append((t, "L", hedef["ad"]))
            rem -= 1
            if rem == 0:
                faz = "HANDLER"
                hedef["kalan"] = hedef["g"]
                gecikmeler.append((hedef["ad"], t + 1 - hedef["v"]))
                yigin.append(hedef)
                hedef = None
    return izler, gecikmeler


SENARYO = {
    "ic_ice": [(0, "UART", 2, 40), (20, "ADC", 1, 15)],
    "kuyruk_zinciri": [(0, "TIM", 1, 10), (5, "UART", 2, 8)],
    "gec_gelen": [(0, "UART", 2, 20), (4, "ADC", 1, 6)],
}


def rastgele_yuk(tohum, ufuk):
    """Uc kaynak, Poisson varisler (ortalama aralik ile)."""
    rnd = random.Random(tohum)
    kaynak = [("ADC", 1, 400, 20, 40), ("UART", 2, 250, 30, 60),
              ("TIM", 3, 1000, 80, 120)]
    olaylar = []
    for ad, p, ort, lo, hi in kaynak:
        t = 0.0
        while True:
            t += rnd.expovariate(1.0 / ort)
            if t >= ufuk:
                break
            olaylar.append((int(t), ad, p, rnd.randint(lo, hi)))
    return olaylar


def yoklama(varislar, periyot):
    """Yoklama: bir sonraki yoklama anina kadar bekleme."""
    return [(periyot - v % periyot) % periyot for v in varislar]


if __name__ == "__main__":
    print("== Senaryolar (ENTRY=12 EXIT=10 TAIL=6) ==")
    tum = []
    for ad, olay in SENARYO.items():
        izler, gec = simule(olay, 80)
        print("-- %s --" % ad)
        for k, g in gec:
            print("  %-6s kabul gecikmesi = %3d cevrim" % (k, g))
        tum += [(ad, t, e, n) for t, e, n in izler]
    print("== Kuyruk zinciri kapali (B) ==")
    _, g = simule(SENARYO["kuyruk_zinciri"], 80, kuyruk=False)
    for k, v in g:
        print("  %-6s gecikme = %3d cevrim" % (k, v))
    print("== Gec gelen kapali (C) ==")
    _, g = simule(SENARYO["gec_gelen"], 80, gec=False)
    for k, v in g:
        print("  %-6s gecikme = %3d cevrim" % (k, v))

    print("== Rastgele yuk: 300000 cevrim, tohum=44 ==")
    olaylar = rastgele_yuk(44, 300000)
    _, gec = simule(olaylar, 300000)
    adc = [v for k, v in gec if k == "ADC"]
    tum_k = [v for k, v in gec]
    yok = yoklama([o[0] for o in olaylar if o[1] == "ADC"], 200)
    for ad, d in (("kesme ADC", adc), ("kesme tum", tum_k),
                  ("yoklama ADC (P=200)", yok)):
        p95 = sorted(d)[int(0.95 * (len(d) - 1))]
        print("%-20s n=%5d ort=%6.1f p95=%4d max=%4d" % (
            ad, len(d), statistics.mean(d), p95, max(d)))

    # Sekiller icin CSV dosyalari: calisma dizinine yazilir
    with open("b44_nvic_senaryo.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["senaryo", "zaman", "etiket", "ad"])
        w.writerows(tum)
    with open("b44_gecikme.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tur", "kaynak", "gecikme_cevrim"])
        for ad, v in gec:
            w.writerow(["kesme", ad, v])
        for v in yok:
            w.writerow(["yoklama", "ADC", v])
