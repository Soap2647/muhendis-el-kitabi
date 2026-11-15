# -*- coding: utf-8 -*-
"""Bölüm 41.4 - Yük dengeleme stratejileri: ayrık olay simülasyonu.

Model: istekler Poisson süreciyle gelir (oran lambda). Her istek
ortalama 1 birimlik iş taşır; i. sunucu hızı mu_i ile işler, yani
hizmet süresi iş/mu_i. Her sunucu FIFO kuyruğa sahiptir. Yönlendirme,
istek geldiği anda yapılır (dağıtım sonradan değişmez).
Tohum: 41. Çıktılar: engine/veri/b41_yuk_dengeleme.csv,
engine/veri/b41_pot.csv
"""

import csv
import random
from collections import deque

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ISTEK = 100000


#@@
def simule(mus, lam, politika, rnd, istek=ISTEK):
    n = len(mus)
    deq = [
        deque() for _ in range(n)
    ]  # sunucudaki tamamlanma zamanları
    serbest = [0.0] * n  # FIFO'da son işin bitişi
    agirlik = [int(m * 2) for m in mus]  # WRR için tamsayı ağırlık
    cur = [0] * n
    toplam_w = sum(agirlik)
    rr = 0
    t = 0.0
    gecikmeler = []
    enb_kuyruk = 0

    def kuyruk(i, now):
        dq = deq[i]
        while dq and dq[0] <= now:
            dq.popleft()
        return len(dq)

#@@
    for _ in range(istek):
        t += rnd.expovariate(lam)
        if politika == "rr":
            i = rr
            rr = (rr + 1) % n
        elif politika == "wrr":
            for j in range(n):
                cur[j] += agirlik[j]
            i = max(range(n), key=lambda j: cur[j])
            cur[i] -= toplam_w
        elif politika == "rastgele":
            i = rnd.randrange(n)
        elif politika == "enaz":
            i = min(range(n), key=lambda j: (kuyruk(j, t), j))
        elif politika == "pot":
            a, b = rnd.sample(range(n), 2)
            i = a if kuyruk(a, t) <= kuyruk(b, t) else b
        elif politika == "erken":
            i = min(range(n), key=lambda j: (max(t, serbest[j]), j))
        else:
            raise ValueError(politika)

        for j in range(n):
            kj = kuyruk(j, t)
            if kj > enb_kuyruk:
                enb_kuyruk = kj

        boyut = rnd.expovariate(1.0)
        baslangic = max(t, serbest[i])
        bitis = baslangic + boyut / mus[i]
        serbest[i] = bitis
        deq[i].append(bitis)
        gecikmeler.append(bitis - t)

#@@
    gecikmeler.sort()
    p = lambda q: gecikmeler[int(q * (len(gecikmeler) - 1))]
    ort = sum(gecikmeler) / len(gecikmeler)
    return ort, p(0.5), p(0.99), enb_kuyruk


#@@
POLITIKALAR = ["rr", "wrr", "rastgele", "enaz", "pot", "erken"]

#@@
if __name__ == "__main__":
    # 1) Heterojen küme: 4 x hız 1, 2 x hız 2, 2 x hız 0,5
    mus = [1.0] * 4 + [2.0] * 2 + [0.5] * 2
    toplam_mu = sum(mus)
    satirlar = []
    print(
        "Heterojen küme, toplam hız = %.1f, istek = %d"
        % (toplam_mu, ISTEK)
    )
    print("rho  politika   ort     p50     p99     maks_kuyruk")
    for rho in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        for pol in POLITIKALAR:
            rnd = random.Random(41)
            lam = rho * toplam_mu
            ort, p50, p99, mk = simule(mus, lam, pol, rnd)
            print(
                "%.2f %-10s %7.3f %7.3f %8.3f %6d"
                % (rho, pol, ort, p50, p99, mk)
            )
            satirlar.append(
                [
                    rho,
                    pol,
                    "%.5f" % ort,
                    "%.5f" % p50,
                    "%.5f" % p99,
                    mk,
                ]
            )
    with open(
        VERI + "/b41_yuk_dengeleme.csv",
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.writer(f)
        w.writerow(["rho", "politika", "ort", "p50", "p99", "maks_k"])
        w.writerows(satirlar)

#@@
    # 2) Homojen 100 sunucu: iki seçimin gücü
    print()
    print("Homojen 100 sunucu, rho = 0,9, istek = %d" % 30000)
    print("politika   maks_kuyruk  p99")
    satirlar = []
    for pol in ("rastgele", "pot"):
        rnd = random.Random(41)
        ort, p50, p99, mk = simule(
            [1.0] * 100, 90.0, pol, rnd, istek=30000
        )
        print("%-10s %11d  %.3f" % (pol, mk, p99))
        satirlar.append([pol, mk, "%.5f" % p99])
    with open(
        VERI + "/b41_pot.csv", "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.writer(f)
        w.writerow(["politika", "maks_k", "p99"])
        w.writerows(satirlar)
