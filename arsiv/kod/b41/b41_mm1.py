# -*- coding: utf-8 -*-
"""Bölüm 41.5 - M/M/1 kuyruğu: gecikme-kullanım eğrisi.

Model: varış süreci Poisson (oran lambda), hizmet süresi üssel
(oran mu = 1). rho = lambda / mu. Teorik ortalama sistemdeki süre
W = 1 / (mu - lambda), ortalama sistemdeki iş sayısı L = rho/(1-rho).
Ölçüm: Lindley yinelemesi  bekleme_{k+1} = max(0, bekleme_k + hizmet_k
- aralik_{k+1}). L doğrudan zaman integraliyle ölçülür (Little'ın
L = lambda W eşitliğini ayrıca kontrol etmek için).
Tohum: 41 (numpy default_rng). Çıktı: engine/veri/b41_mm1.csv
"""

import csv
import sys

import numpy as np

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ISINMA = 20000  # ilk örnekler atılır (kararlı duruma yaklaşmak için)


def mm1(rho, n, rng):
    lam = rho
    aralik = rng.exponential(1.0 / lam, n)
    hizmet = rng.exponential(1.0, n)
    bekleme = np.empty(n)
    bekleme[0] = 0.0
    b = 0.0
    for k in range(1, n):  # Lindley: sıralı, vektörleşmez
        b = max(0.0, b + hizmet[k - 1] - aralik[k])
        bekleme[k] = b
    varis = np.cumsum(aralik)
    ayrilma = varis + bekleme + hizmet
    sistemde = ayrilma - varis
    return bekleme, varis, ayrilma, sistemde


#@@
def L_olc(varis, ayrilma):
    """Zaman integrali: sistemdeki iş sayısının ortalaması."""
    olaylar = np.concatenate([varis, ayrilma])
    deger = np.concatenate(
        [np.ones_like(varis), -np.ones_like(varis)]
    )
    sira = np.argsort(olaylar, kind="stable")
    olaylar = olaylar[sira]
    deger = deger[sira]
    sayi = np.cumsum(deger)[:-1]
    dt = np.diff(olaylar)
    toplam = olaylar[-1] - olaylar[0]
    return float(np.sum(sayi * dt) / toplam)


#@@
if __name__ == "__main__":
    print(
        "rho   W_teorik   W_olculen   L_teorik  L_olculen  lambda_W"
    )
    satirlar = []
    for rho, n in (
        (0.5, 2000000),
        (0.8, 2000000),
        (0.9, 2000000),
        (0.99, 6000000),
    ):
        rng = np.random.default_rng(41)
        bekleme, varis, ayrilma, sistemde = mm1(rho, n, rng)
        s = sistemde[ISINMA:]
        w_teo = 1.0 / (1.0 - rho)
        l_teo = rho / (1.0 - rho)
        w_olc = float(np.mean(s))
        l_olc = L_olc(varis[ISINMA:], ayrilma[ISINMA:])
        print(
            "%.2f %10.3f %11.3f %10.3f %10.3f %9.3f"
            % (rho, w_teo, w_olc, l_teo, l_olc, rho * w_olc)
        )
        satirlar.append(
            [
                rho,
                n,
                "%.6f" % w_teo,
                "%.6f" % w_olc,
                "%.6f" % l_teo,
                "%.6f" % l_olc,
            ]
        )

#@@
    with open(
        VERI + "/b41_mm1.csv", "w", encoding="utf-8", newline=""
    ) as f:
        wr = csv.writer(f)
        wr.writerow(
            [
                "rho",
                "n",
                "w_teorik",
                "w_olculen",
                "l_teorik",
                "l_olculen",
            ]
        )
        wr.writerows(satirlar)

#@@
    if len(sys.argv) > 1 and sys.argv[1] == "iz":
        rng = np.random.default_rng(41)
        b, v, a, sis = mm1(0.8, 10, rng)
        print()
        print("rho = 0,8 ilk 6 iş (iz)")
        print("is  varis    bekleme  ayrilma     sistemde")
        for k in range(6):
            print(
                "%-3d %7.3f  %7.3f  %10.3f  %8.3f"
                % (k + 1, v[k], b[k], a[k], sis[k])
            )
