# -*- coding: utf-8 -*-
"""Bölüm 41.2 - SLO aritmetiği ve bileşen kullanılabilirliği.
Tohum: 41. Çalıştırma: python b41_erisilebilirlik.py
"""

import random

YIL_SAAT = 365 * 24


def kesinti_saat(hedef):
    """Yıllık izin verilen kesinti süresi (saat)."""
    return (1 - hedef) * YIL_SAAT


def metin(dakika):
    """Dakikayı okunur birime çevirir."""
    if dakika >= 60:
        return "%.2f saat" % (dakika / 60)
    if dakika >= 1:
        return "%.2f dakika" % dakika
    return "%.1f saniye" % (dakika * 60)


print("SLO       yıllık kesinti      30 günlük kesinti")
for h in (0.99, 0.999, 0.9995, 0.9999, 0.99999):
    yil = (1 - h) * YIL_SAAT * 60  # dakika
    ay = (1 - h) * 30 * 24 * 60  # dakika
    print("%-9.5f %-19s %s" % (h, metin(yil), metin(ay)))
print("%%99.9 hata bütçesi (30 gün): %.1f dakika"
      % ((1 - 0.999) * 30 * 24 * 60))


# Seri ve paralel bileşenler

#@@
def seri(*a):
    p = 1.0
    for x in a:
        p *= x
    return p


def paralel(*a):
    q = 1.0
    for x in a:
        q *= 1 - x
    return 1 - q


print()
print("seri (0,999 x 3)         = %.6f" % seri(0.999, 0.999, 0.999))
print("paralel (0,99 x 2)       = %.6f" % paralel(0.99, 0.99))
print("paralel (0,99 x 3)       = %.6f" % paralel(0.99, 0.99, 0.99))

# Monte Carlo: anlık görüntü modeli (her bileşen bağımsız açık/kapalı)
rnd = random.Random(41)

#@@
N = 1000000


def mc_sistem(olasiliklar_seri, yedek_p, yedek_sayi):
    """Seri zincir: her yazma/okuma adımı bir 'seri' bileşen.
    Yedekli blok: yedek_sayi tane bağımsız kopya, biri açıksa yeter.
    """
    ok = 0
    for _ in range(N):
        tamam = True
        for p in olasiliklar_seri:
            if rnd.random() >= p:
                tamam = False
                break
        if tamam:
            kopya_ok = False
            for _ in range(yedek_sayi):
                if rnd.random() < yedek_p:
                    kopya_ok = True
                    break
            if not kopya_ok:
                tamam = False
        if tamam:
            ok += 1
    return ok / N


#@@
if __name__ == "__main__":
    # Örnek: 0,999'luk iki seri bileşen + 0,99'luk 2 kopyalı blok
    teo = seri(0.999, 0.999) * paralel(0.99, 0.99)
    olc = mc_sistem([0.999, 0.999], 0.99, 2)
    print()
    print("iki seri + 2 kopyalı blok")
    print("teorik = %.6f" % teo)
    print("olçülen (1e6 deneme) = %.6f" % olc)
