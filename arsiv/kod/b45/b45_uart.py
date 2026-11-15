# -*- coding: utf-8 -*-
"""b45_uart.py: UART (8N1 / 8E1) bit duzeyi simulasyonu.

Verici hatti kesin zamanla surer; alici baslangic kenarina senkronlanir
ve her bit ortasinda orneklenir. Alicinin bit suresi Tr = T * (1 + d):
d > 0 alicinin daha yavas, d < 0 daha hizli saydigi anlamina gelir.
Sonuclar SIMULASYON ciktisidir; gercek bir hat olcumu degildir.
"""
import csv
import os

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def cerceve_bitleri(bayt, parite=None):
    """Baslangic(0), 8 veri biti (LSB once), istege bagli eslik, dur(1)."""
    bitler = [0] + [(bayt >> i) & 1 for i in range(8)]
    if parite == "even":
        bitler.append(sum(bitler[1:]) & 1)     # cift eslik
    elif parite == "odd":
        bitler.append((sum(bitler[1:]) + 1) & 1)
    bitler.append(1)                            # dur biti
    return bitler


def seviye(t, bitler, T):
    """Hat seviyesi t aninda (t=0: baslangic kenari). Bosta 1."""
    k = int(t // T)
    if t < 0 or k >= len(bitler):
        return 1
    return bitler[k]


def coz(bayt, d=0.0, parite=None):
    """Bayti alici tarafinda ornekleyerek geri okur.

    Donus: (cozulen_bayt veya None, cerceve_hatasi_var_mi)
    """
    T = 1.0
    bitler = cerceve_bitleri(bayt, parite)
    Tr = T * (1.0 + d)
    ornekler = []
    for k in range(len(bitler)):
        t = (k + 0.5) * Tr
        ornekler.append(seviye(t, bitler, T))
    if ornekler[0] != 0:
        return None, True
    veri_bitleri = ornekler[1:9]
    val = sum(b << i for i, b in enumerate(veri_bitleri))
    hata = False
    son = ornekler[-1]
    if son != 1:
        hata = True                            # durdurma biti 0: cerceve
    if parite:
        pb = ornekler[9]
        beklenen = sum(veri_bitleri) & 1
        if parite == "odd":
            beklenen ^= 1
        if pb != beklenen:
            hata = True
    return val, hata


def tolerans_sup(parite=None):
    """Tum 256 bayt dogru cozuluyorsa d'nin pozitif ve negatif sinirlari."""
    adim = 0.0001
    def hepsi_ok(d):
        for b in range(256):
            v, h = coz(b, d, parite)
            if v != b or h:
                return False
        return True
    poz = 0.0
    while poz < 0.2 and hepsi_ok(poz + adim):
        poz += adim
    neg = 0.0
    while neg > -0.2 and hepsi_ok(neg - adim):
        neg -= adim
    return poz, neg


def csv_yaz(yol, satirlar, basliklar):
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)


if __name__ == "__main__":
    import sys
    yazma = "--yaz" in sys.argv
    # 1) Sinirsiz hatasiz gidis-donus (d = 0)
    assert all(coz(b, 0.0) == (b, False) for b in range(256))
    print("d=0: 256 bayt hatasiz: TAMAM")
    # 2) Eslik: tek bit bozulmasi yakalanir
    bitler = cerceve_bitleri(0x4B, "even")
    bozuk = list(bitler)
    bozuk[3] ^= 1
    T = 1.0
    sonuc = [seviye((k + 0.5) * T, bozuk, T) for k in range(len(bozuk))]
    vv = sum(b << i for i, b in enumerate(sonuc[1:9]))
    pb_ok = (sum(sonuc[1:9]) & 1) == sonuc[9]
    print("eslik: bozuk bit 0x%02X, eslik tutarli mi=%s" % (vv, pb_ok))
    # 3) Baud toleransi
    for par in (None, "even"):
        p, n = tolerans_sup(par)
        print("parite=%-5s  d+ = %+.2f%%   d- = %+.2f%%" %
              (par, p * 100, n * 100))
    print("teorik: 0.5/9.5 = %.2f%%" % (100 * 0.5 / 9.5))
    if yazma:
        # Sekil 1: 0x4B cercevesi, 20 ornek/bit
        bitler = cerceve_bitleri(0x4B)
        satir = []
        for i in range(len(bitler) * 20):
            t = i / 20.0
            satir.append(["%.3f" % t, seviye(t, bitler, 1.0)])
        csv_yaz(os.path.join(VERI, "b45_uart_iz.csv"), satir,
                ["t_bit", "seviye"])
        # Sekil 2: ornekleme kaymasi (d = 0, +4%, -4%, +6%)
        satir = []
        for k in range(10):
            satir.append([k, "%.3f" % ((k + 0.5)),
                          "%.3f" % ((k + 0.5) * 1.04),
                          "%.3f" % ((k + 0.5) * 0.96),
                          "%.3f" % ((k + 0.5) * 1.06)])
        csv_yaz(os.path.join(VERI, "b45_uart_kayma.csv"), satir,
                ["bit", "d0", "d_plus4", "d_minus4", "d_plus6"])
        # Sekil 3: d taramasi (bayt basari orani)
        satir = []
        d = -0.08
        while d <= 0.0801:
            ok = sum(1 for b in range(256)
                     if coz(b, d) == (b, False))
            satir.append(["%.2f" % (d * 100), "%.4f" % (ok / 256)])
            d += 0.0025
        csv_yaz(os.path.join(VERI, "b45_uart_baud.csv"), satir,
                ["d_yuzde", "basari"])
        print("CSV yazildi:", VERI)
