# sched_sim.py: CPU zamanlayıcı simülatörü (birim-tick, tek CPU).
# Algoritmalar: FCFS, SJF (kesintisiz), SRTF (kesintili SJF),
# Öncelik (kesintisiz), Round Robin (q), MLFQ (3 seviye + boost).
# Her tick bir CPU birimi. Süreç: (ad, varış, süre, öncelik).
# Çalıştırma: python sched_sim.py   -> sonuçları yazar ve CSV üretir.
import csv
import itertools
import os
import random
import textwrap
from collections import deque

SUREC = [  # kitap örneği
    {"ad": "P1", "varis": 0, "sure": 24, "oncelik": 3},
    {"ad": "P2", "varis": 0, "sure": 3,  "oncelik": 1},
    {"ad": "P3", "varis": 0, "sure": 3,  "oncelik": 2},
]


def kesintisiz(sur, sec):
    """Süreç bitene kadar bırakılmaz. sec: hazır -> seçilen."""
    kalan = {p["ad"]: p["sure"] for p in sur}
    bitti, tl, t, cur = set(), [], 0, None
    while len(bitti) < len(sur):
        if cur is None:
            hazir = [p for p in sur if p["ad"] not in bitti
                     and p["varis"] <= t]
            if not hazir:
                tl.append(None)
                t += 1
                continue
            cur = sec(hazir)
        tl.append(cur["ad"])
        kalan[cur["ad"]] -= 1
        t += 1
        if kalan[cur["ad"]] == 0:
            bitti.add(cur["ad"])
            cur = None
    return tl


def fcfs(sur):
    def sec(h):
        return min(h, key=lambda p: p["varis"])
    return kesintisiz(sur, sec)


def sjf(sur):
    def sec(h):
        return min(h, key=lambda p: (p["sure"], p["varis"]))
    return kesintisiz(sur, sec)


def oncelik(sur):
    def sec(h):
        return min(h, key=lambda p: (p["oncelik"], p["varis"]))
    return kesintisiz(sur, sec)


def srtf(sur):
    """Her tick en kısa kalan süreli hazır süreç çalışır."""
    kalan = {p["ad"]: p["sure"] for p in sur}
    tl, t = [], 0
    while any(v > 0 for v in kalan.values()):
        hazir = [p for p in sur
                 if p["varis"] <= t and kalan[p["ad"]] > 0]
        if not hazir:
            tl.append(None)
        else:
            sec = min(hazir,
                      key=lambda p: (kalan[p["ad"]], p["varis"]))
            tl.append(sec["ad"])
            kalan[sec["ad"]] -= 1
        t += 1
    return tl


def round_robin(sur, q):
    """Yeni varışlar, kesilen süreçten ÖNCE kuyruğa girer."""
    kalan = {p["ad"]: p["sure"] for p in sur}
    eklendi, kuyruk, tl = set(), deque(), []
    t, cur, dilim = 0, None, 0
    while any(v > 0 for v in kalan.values()):
        for p in sur:
            if p["varis"] == t and p["ad"] not in eklendi:
                kuyruk.append(p["ad"])
                eklendi.add(p["ad"])
        if cur is not None and (dilim == q or kalan[cur] == 0):
            if kalan[cur] > 0:
                kuyruk.append(cur)
            cur = None
        if cur is None:
            if not kuyruk:
                tl.append(None)
                t += 1
                continue
            cur, dilim = kuyruk.popleft(), 0
        tl.append(cur)
        kalan[cur] -= 1
        dilim += 1
        t += 1
    return tl


def mlfq(sur, kuantum=(2, 4, 8), boost=20):
    """Çok seviyeli geri beslemeli kuyruk. Tam dilim kullanan süreç
    bir alt seviyeye iner; her 'boost' tick'te hepsi en üste çıkar."""
    n = len(kuantum)
    kuy = [deque() for _ in range(n)]
    kalan = {p["ad"]: p["sure"] for p in sur}
    seviye, eklendi, tl = {}, set(), []
    t, cur, dilim = 0, None, 0
    while any(v > 0 for v in kalan.values()):
        for p in sur:
            if p["varis"] == t and p["ad"] not in eklendi:
                kuy[0].append(p["ad"])
                seviye[p["ad"]] = 0
                eklendi.add(p["ad"])
        if t > 0 and t % boost == 0:
            for k in range(1, n):
                while kuy[k]:
                    ad = kuy[k].popleft()
                    seviye[ad] = 0
                    kuy[0].append(ad)
        if cur is not None:
            L = seviye[cur]
            if kalan[cur] == 0:
                cur = None
            elif any(kuy[k] for k in range(L)):   # üst seviye hazır
                kuy[L].append(cur)
                cur = None
            elif dilim == kuantum[L]:             # dilim doldu: indir
                seviye[cur] = min(L + 1, n - 1)
                kuy[seviye[cur]].append(cur)
                cur = None
        if cur is None:
            for k in range(n):
                if kuy[k]:
                    cur, dilim = kuy[k].popleft(), 0
                    break
        if cur is None:
            tl.append(None)
            t += 1
            continue
        tl.append(cur)
        kalan[cur] -= 1
        dilim += 1
        t += 1
    return tl


def olc(sur, tl):
    """Tick dizisinden bekleme, dönüş ve yanıt sürelerini hesaplar."""
    sonuc = {}
    for p in sur:
        idx = [i for i, a in enumerate(tl) if a == p["ad"]]
        bit = idx[-1] + 1
        ilk = idx[0]
        donus = bit - p["varis"]
        sonuc[p["ad"]] = {"bitis": bit, "donus": donus,
                          "bekleme": donus - p["sure"],
                          "yanit": ilk - p["varis"]}
    n = len(sur)
    sonuc["ORT_BEKLEME"] = sum(sonuc[p["ad"]]["bekleme"]
                               for p in sur) / n
    return sonuc


def gantt_satirlari(tl):
    """Ardışık aynı tick'leri tek parça (ad, baş, son) yapar."""
    parca, bas = [], 0
    for i in range(1, len(tl) + 1):
        if i == len(tl) or tl[i] != tl[bas]:
            parca.append((tl[bas] or "-", bas, i))
            bas = i
    return parca


def ozet_yaz(ad, tl, sur):
    o = olc(sur, tl)
    metin = "  ".join(
        "%s[%d-%d)" % (x, b, s) for x, b, s in gantt_satirlari(tl))
    satirlar = textwrap.wrap(metin, width=66)
    print("%-8s" % ad, satirlar[0])
    for devam in satirlar[1:]:
        print(" " * 8, devam)
    print("         bekleme: " + ", ".join(
        "%s=%d" % (p["ad"], o[p["ad"]]["bekleme"]) for p in sur),
        " ORT=%.2f" % o["ORT_BEKLEME"])
    return o


def brute_force_sjf(sur):
    """Tüm sıralı planlarda en iyi ortalama bekleme (varış=0)."""
    en_iyi = None
    for sira in itertools.permutations(sur):
        t, top = 0, 0
        for p in sira:
            top += t
            t += p["sure"]
        if en_iyi is None or top < en_iyi:
            en_iyi = top
    return en_iyi / len(sur)


def main():
    print("== Kitap örneği: P1=24, P2=3, P3=3 (hepsi t=0) ==")
    ornek = {
        "FCFS": fcfs(SUREC),
        "SJF": sjf(SUREC),
        "RR q=4": round_robin(SUREC, 4),
    }
    for ad, tl in ornek.items():
        ozet_yaz(ad, tl, SUREC)

    print("\n== Klasik örnek A: kesintisiz SJF (Silberschatz) ==")
    A = [{"ad": "P1", "varis": 0, "sure": 8, "oncelik": 1},
         {"ad": "P2", "varis": 1, "sure": 4, "oncelik": 1},
         {"ad": "P3", "varis": 2, "sure": 9, "oncelik": 1},
         {"ad": "P4", "varis": 3, "sure": 5, "oncelik": 1}]
    ozet_yaz("SJF", sjf(A), A)
    ozet_yaz("SRTF", srtf(A), A)

    rnd = random.Random(26)
    print("\n== 500 rastgele örnek: SJF = brute-force optimum ==")
    hata = 0
    for _ in range(500):
        n = rnd.randint(2, 6)
        s = [{"ad": "P%d" % i, "varis": 0,
              "sure": rnd.randint(1, 12), "oncelik": 1}
             for i in range(n)]
        if abs(olc(s, sjf(s))["ORT_BEKLEME"]
               - brute_force_sjf(s)) > 1e-9:
            hata += 1
    print("SJF farkı (hata sayısı):", hata)

    print("\n== Altılı süreç: 7 algoritma, aynı iş yükü ==")
    S6 = [{"ad": "A", "varis": 0, "sure": 5, "oncelik": 2},
          {"ad": "B", "varis": 1, "sure": 3, "oncelik": 1},
          {"ad": "C", "varis": 2, "sure": 8, "oncelik": 3},
          {"ad": "D", "varis": 3, "sure": 2, "oncelik": 2},
          {"ad": "E", "varis": 9, "sure": 4, "oncelik": 1},
          {"ad": "F", "varis": 10, "sure": 6, "oncelik": 3}]
    tablo = [("FCFS", fcfs(S6)), ("SJF", sjf(S6)), ("SRTF", srtf(S6)),
             ("Öncelik", oncelik(S6)), ("RR q=2", round_robin(S6, 2)),
             ("RR q=4", round_robin(S6, 4)),
             ("MLFQ", mlfq(S6))]
    satirlar = []
    for ad, tl in tablo:
        o = ozet_yaz(ad, tl, S6)
        for p in S6:
            satirlar.append({"algoritma": ad, "surec": p["ad"],
                             "varis": p["varis"], "sure": p["sure"],
                             "bekleme": o[p["ad"]]["bekleme"],
                             "donus": o[p["ad"]]["donus"],
                             "yanit": o[p["ad"]]["yanit"]})
    veri = r"D:\Mevcut Projeler\Kitap\engine\veri"
    os.makedirs(veri, exist_ok=True)
    yol = os.path.join(veri, "b26_zamanlama.csv")
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)

    # Gantt verisi (şekil için): örnek, algoritma, süreç, baş, son
    gantt = []
    gruplar = [("kitap", ornek), ("altili", dict(tablo))]
    for ornek_ad, algo_tl in gruplar:
        for algo, tl in algo_tl.items():
            for ad, bas, son in gantt_satirlari(tl):
                if ad != "-":
                    gantt.append({"ornek": ornek_ad,
                                  "algoritma": algo,
                                  "surec": ad, "bas": bas,
                                  "son": son})
    gyol = os.path.join(veri, "b26_gantt.csv")
    with open(gyol, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gantt[0].keys()))
        w.writeheader()
        w.writerows(gantt)
    print("\nCSV:", yol)
    print("Gantt CSV:", gyol)


if __name__ == "__main__":
    main()
