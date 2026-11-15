# -*- coding: utf-8 -*-
"""Bölüm 41.6 - Yeniden deneme: sürü etkisi (thundering herd).

Senaryo: 1000 istemci t=0'da aynı anda başarısız olur (sunucu 2 s
kapalı). Sunucu t >= 2 s'de açılır, kapasitesi 200 istek/s'dir
(10 ms'de 2 istek). Kapasiteyi aşan istekler reddedilir ve istemci
geri çekilme (backoff) ile yeniden dener. En fazla 12 deneme.
Üç strateji: sabit (jitter yok), tam jitter, ayrışık jitter.
Tohum: 41. Çıktı: engine/veri/b41_jitter.csv
"""

import csv
import heapq
import random

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TICK = 0.01  # simülasyon adımı (s)
SUNUCU_ACILIS = 2.0  # sunucu bu andan sonra hizmet verir (s)
KAPASITE = 2  # tick başına kabul edilen istek (200/s)
ISTEMCI = 1000
TABAN = 1.0  # ilk geri çekilme (s)
TAVAN = 30.0  # geri çekilme üst sınırı (s)
MAKS = 12  # en fazla deneme sayısı
KOVA = 0.1  # sayım kovası (s)
SURE = 120.0


#@@
def bekleme(strateji, k, onceki, rnd):
    """k: şimdiye kadarki başarısızlık sayısı (>= 1)."""
    if strateji == "sabit":
        return min(TAVAN, TABAN * 2 ** (k - 1)), None
    if strateji == "tam":
        ust = min(TAVAN, TABAN * 2 ** (k - 1))
        return rnd.uniform(0, ust), None
    if strateji == "ayrisik":
        # ayrışık jitter: önceki beklemeye göre yeni aralık
        s = min(TAVAN, rnd.uniform(TABAN, onceki * 3))
        return s, s
    raise ValueError(strateji)


#@@
def kos(strateji, rnd):
    olay = [(0.0, i) for i in range(ISTEMCI)]
    heapq.heapify(olay)
    deneme = [0] * ISTEMCI
    onceki = [TABAN] * ISTEMCI
    kovalar = {}
    toplam = basarili = vazgecen = 0
    son = 0.0

#@@
    adim = int(round(SURE / TICK))

#@@
    for s in range(adim):
        t = s * TICK
        istekler = []
        while olay and olay[0][0] <= t + 1e-9:
            istekler.append(heapq.heappop(olay)[1])
        if not istekler:
            continue
        kova = int(t / KOVA + 1e-9)
        kovalar[kova] = kovalar.get(kova, 0) + len(istekler)
        toplam += len(istekler)
        kabul = (
            set(istekler[:KAPASITE]) if t >= SUNUCU_ACILIS else set()
        )
        for i in istekler:
            if i in kabul:
                basarili += 1
                son = t
                continue
            deneme[i] += 1
            if deneme[i] >= MAKS:
                vazgecen += 1
                continue
            d, yeni = bekleme(strateji, deneme[i], onceki[i], rnd)
            if yeni is not None:
                onceki[i] = yeni
            heapq.heappush(olay, (t + d, i))

#@@
    tepe = max(kovalar.values())
    ilk_sn = int(1.0 / KOVA)  # t=0 ilk başarısızlık patlamasını dışla
    tepe_sonra = max(v for k, v in kovalar.items() if k >= ilk_sn)
    bekleyen = len(olay)
    return (
        toplam,
        basarili,
        vazgecen,
        bekleyen,
        son,
        tepe,
        tepe_sonra,
        kovalar,
    )


#@@
if __name__ == "__main__":
    satirlar = []
    print(
        "strateji  toplam  basarili  vazgecen  bekleyen  son_s"
        "  tepe  tepe_1s_sonra"
    )
    for strateji in ("sabit", "tam", "ayrisik"):
        rnd = random.Random(41)
        top, bas, vaz, bek, son, tepe, tepe_s, kov = kos(
            strateji, rnd
        )
        print(
            "%-9s %7d %9d %9d %9d %6.2f %5d %8d"
            % (strateji, top, bas, vaz, bek, son, tepe, tepe_s)
        )
        for k in range(int(SURE / KOVA)):
            satirlar.append(
                [strateji, "%.1f" % (k * KOVA), kov.get(k, 0)]
            )
    with open(
        VERI + "/b41_jitter.csv", "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        w.writerow(["strateji", "zaman_s", "istek_100ms"])
        w.writerows(satirlar)
