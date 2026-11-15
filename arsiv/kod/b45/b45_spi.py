# -*- coding: utf-8 -*-
"""b45_spi.py: SPI tam cift yonlu kaydirma, CPOL/CPHA kipleri.

Model: yarim periyot = 1 birim. Ana (master) SCK'yi uretir; 8 bit
icin 16 kenar vardir (t = 1..16). Kablo gecikmesiz kabul edilir.
Her cihaz SCK'yi KENDI CPOL'una gore yorumlar:
  - "onde gelen kenar": bosta seviyeden aktif seviyeye gecis,
  - CPHA=0: uydu/ana, onde gelen kenarda ORNEKLER, arkada veri
    degistirir; CPHA=1: tersi.
Veri degisimi ile ornekleme ayni anda olursa bit BELIRSIZ (X)
sayilir (kurulum/tutma ihlali). SIMULASYONDUR; gercek olcum degildir.
"""
import csv
import random
import sys

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def kenarlar(sck_cpol):
    """(t, yeni_seviye) listesi; t = 1..16. Ilk seviye sck_cpol."""
    liste, seviye = [], sck_cpol
    for t in range(1, 17):
        seviye ^= 1
        liste.append((t, seviye))
    return liste


def cihaz_kenarlari(sck_cpol, cihaz_cpol):
    """Cihazin gordugu (t, onde_mi) listesi."""
    aktif = 1 - cihaz_cpol           # cihazin 'aktif' seviyesi
    return [(t, seviye == aktif) for t, seviye in kenarlar(sck_cpol)]


def ornek_zamanlari(sck_cpol, cihaz_cpol, cihaz_cpha):
    """Cihazin verileri okudugu kenarlar (ilk 8 tanesi)."""
    k = cihaz_kenarlari(sck_cpol, cihaz_cpol)
    hedef = (cihaz_cpha == 0)        # CPHA=0: onde gelen kenar
    return [t for t, onde in k if onde == hedef][:8]


def hazir_zamanlari(sck_cpol, cihaz_cpol, cihaz_cpha):
    """Cihazin kendi bitini hatta koydugu anlar (bit 0..7)."""
    k = cihaz_kenarlari(sck_cpol, cihaz_cpol)
    if cihaz_cpha == 0:
        # CPHA=0: ilk bit SCK baslamadan (t=0) hazir, sonra arka kenarlar
        return [0] + [t for t, onde in k if not onde][:7]
    return [t for t, onde in k if onde][:8]


def bit_oku(hazir, bitler, t):
    """t aninda hattaki bit. Degisim anindaki ornek: 'X' (belirsiz)."""
    if t in hazir:
        return "X"
    son = 0
    for i, th in enumerate(hazir):
        if th < t:
            son = bitler[i]
    return son


def degistir(bayt_a, bayt_b, kip_a, kip_b, sck_cpol=None):
    """Ana (kip_a) ve uydu (kip_b) kipleri. kip=(cpol, cpha).

    Donus: (ana_aldi, uydu_aldi); her biri 8 karakterli dizi veya
    bayt. Belirsiz bit varsa None doner.
    """
    if sck_cpol is None:
        sck_cpol = kip_a[0]
    ba = [(bayt_a >> (7 - i)) & 1 for i in range(8)]
    bb = [(bayt_b >> (7 - i)) & 1 for i in range(8)]
    h_a = hazir_zamanlari(sck_cpol, *kip_a)
    h_b = hazir_zamanlari(sck_cpol, *kip_b)
    o_a = ornek_zamanlari(sck_cpol, *kip_a)
    o_b = ornek_zamanlari(sck_cpol, *kip_b)
    uydu_aldi = [bit_oku(h_a, ba, t) for t in o_b]   # uydu, ana'dan
    ana_aldi = [bit_oku(h_b, bb, t) for t in o_a]    # ana, uydudan
    def bayta(L):
        if "X" in L:
            return None
        return sum(b << (7 - i) for i, b in enumerate(L))
    return bayta(ana_aldi), bayta(uydu_aldi)


KIPLER = [(0, 0), (0, 1), (1, 0), (1, 1)]


if __name__ == "__main__":
    rnd = random.Random(45)
    print("kip  orneklem kenarlari (t) ve veri hazirlama (t)")
    for kip in KIPLER:
        print("%s  %s  %s" % (kip, ornek_zamanlari(0, *kip),
                              hazir_zamanlari(0, *kip)))
    for kip in KIPLER:
        for _ in range(300):
            a, b = rnd.randrange(256), rnd.randrange(256)
            r = degistir(a, b, kip, kip)
            assert r == (b, a), (kip, a, b, r)
    print("ayni kip: 4 kip x 300 rastgele cift: TAMAM")
    print("\nkarisik kip (ana, uydu) -> ana aldi / uydu aldi:")
    for ka in KIPLER:
        for kb in KIPLER:
            if ka == kb:
                continue
            r = degistir(0xA5, 0x3C, ka, kb)
            print(ka, kb, [("%02X" % x if x is not None else "X")
                           for x in r])
    # CPOL farki ile CPHA farki ayni ornekleme kenarlarini mi veriyor?
    ayni = ornek_zamanlari(0, 1, 0) == ornek_zamanlari(0, 0, 1)
    print("\n(cpol=1,cpha=0) ve (cpol=0,cpha=1) ayni orneklem mi:", ayni)
    print("CPOL XOR CPHA = 1 olan kipler ayni orneklem kenarlarina sahip")
    if "--yaz" in sys.argv:
        yol = VERI + "/b45_spi_ornek.csv"
        with open(yol, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["cpol", "cpha", "kenar_t", "seviye", "onde",
                        "ornek", "hazir"])
            for kip in KIPLER:
                # eslesik kip: SCK bosta seviyesi = CPOL (ana ve uydu ayni)
                ors = set(ornek_zamanlari(kip[0], *kip))
                hz = set(hazir_zamanlari(kip[0], *kip))
                for t, seviye in kenarlar(kip[0]):
                    onde = dict(cihaz_kenarlari(kip[0], kip[0]))[t]
                    w.writerow([kip[0], kip[1], t, seviye, int(onde),
                                int(t in ors), int(t in hz)])
        print("CSV yazildi:", yol)
