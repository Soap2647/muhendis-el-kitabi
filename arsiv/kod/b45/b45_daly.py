# -*- coding: utf-8 -*-
"""b45_daly.py: Daly BMS 13 baytlik cerceve analizi.

1) main.c'deki cozumleme mantigi (birebir) ve ESPHome daly_bms.cpp'ye
   gore dogru cozumleme yan yana.
2) Sagalama: 8 bit toplam (Daly) ve CRC-16/CCITT-FALSE, rastgele
   hata enjeksiyonunda yakalama oranlari (sabit tohum 45).
SIMULASYONDUR: cerceveler sentetik BMS yanitlarıdır.
"""
import random
from b45_crc import crc16_ccitt_false, toplama8


def istek(komut):
    p = [0xA5, 0x40, komut, 0x08] + [0] * 8
    p.append(toplama8(p))
    return bytes(p)


def yanit(komut, deger):
    """Sentetik BMS yaniti (adres 0x01). deger: komuta gore sozluk."""
    g = [0xA5, 0x01, komut, 0x08] + [0] * 8
    if komut == 0x90:
        v = int(round(deger["volt"] * 10))
        akim = int(round(deger["akim"] * 10)) + 30000
        soc = int(round(deger["soc"] * 10))
        g[4:6] = [v >> 8, v & 0xFF]
        g[8:10] = [akim >> 8, akim & 0xFF]
        g[10:12] = [soc >> 8, soc & 0xFF]
    elif komut == 0x92:
        g[4] = deger["tmax"] + 40
        g[5] = deger["tmax_no"]
        g[6] = deger["tmin"] + 40
        g[7] = deger["tmin_no"]
    elif komut == 0x95:
        g[4] = deger["kare"]
        for i, mv in enumerate(deger["hucreler"][:3]):
            g[5 + 2 * i] = mv >> 8
            g[6 + 2 * i] = mv & 0xFF
    g.append(toplama8(g))
    return bytes(g)


def main_c_coz(g, komut):
    """main.c'nin ayni satirlari (Python'a aktarim)."""
    if komut == 0x90:
        volt = ((g[4] << 8) | g[5]) / 10.0
        bat = ((g[10] << 8) | g[11]) // 10
        return {"volt": volt, "bat": bat}
    if komut == 0x92:
        return {"btemp": g[4] - 40}
    if komut == 0x95:                      # main.c: 'hucre'
        return {"hucre": ((g[4] << 8) | g[5]) / 1000.0}
    raise ValueError


def esphome_coz(g, komut):
    """ESPHome daly_bms.cpp'ye gore dogru alan ofsetleri."""
    if komut == 0x90:
        volt = ((g[4] << 8) | g[5]) / 10.0
        soc = ((g[10] << 8) | g[11]) / 10.0
        return {"volt": volt, "soc": soc}
    if komut == 0x92:
        return {"tmax": g[4] - 40, "tmin": g[6] - 40}
    if komut == 0x95:
        kare = g[4]
        hucreler = [((g[5 + 2 * i] << 8) | g[6 + 2 * i]) / 1000.0
                    for i in range(3)]
        return {"kare": kare, "hucre1": hucreler[0]}
    raise ValueError


def toplama_dogrula(g):
    return toplama8(g[:12]) == g[12]


def gonderim_ornegi():
    g = yanit(0x90, {"volt": 52.3, "akim": -12.5, "soc": 87.4})
    return g


def tohum_ile_deney(n=20000, tohum=45):
    rnd = random.Random(tohum)
    sonuc = {"tek_bit": [0, 0], "yer_degisimi": [0, 0],
             "iki_bayt_rast": [0, 0], "rast_cerceve": [0, 0]}
    for _ in range(n):
        g = bytearray(yanit(0x90, {"volt": rnd.uniform(40, 60),
                                   "akim": rnd.uniform(-50, 50),
                                   "soc": rnd.uniform(0, 100)}))
        orijinal = bytes(g)
        # 1) tek bit (rastgele konum, 12 veri baytı)
        h = bytearray(orijinal)
        p = rnd.randrange(12)
        h[p] ^= 1 << rnd.randrange(8)
        sonuc["tek_bit"][0] += 1
        if not toplama_dogrula(h):
            sonuc["tek_bit"][1] += 1
        # 2) iki farkli baytin yer degisimi (4..11 arasinda)
        h = bytearray(orijinal)
        i, j = rnd.sample(range(4, 12), 2)
        if h[i] != h[j]:
            h[i], h[j] = h[j], h[i]
            sonuc["yer_degisimi"][0] += 1
            if not toplama_dogrula(h):
                sonuc["yer_degisimi"][1] += 1
        # 3) iki baytta rastgele farkli degerler (toplamı tutmayan)
        h = bytearray(orijinal)
        for k in rnd.sample(range(12), 2):
            h[k] = rnd.randrange(256)
        if bytes(h) != orijinal:
            sonuc["iki_bayt_rast"][0] += 1
            if not toplama_dogrula(h):
                sonuc["iki_bayt_rast"][1] += 1
        # 4) tamamen rastgele 13 bayt
        h = bytes(rnd.randrange(256) for _ in range(13))
        sonuc["rast_cerceve"][0] += 1
        if not toplama_dogrula(h):
            sonuc["rast_cerceve"][1] += 1
    return sonuc


def crc_yakalama(n=20000, tohum=45):
    """Ayni hata turleri, CRC-16 ile (yuk = ilk 12 bayt, son 2 = CRC)."""
    rnd = random.Random(tohum)
    kayip = {"yer_degisimi": [0, 0], "iki_bayt_rast": [0, 0]}
    # [toplam, tespit edilen]
    for _ in range(n):
        g = bytearray(yanit(0x90, {"volt": rnd.uniform(40, 60),
                                   "akim": rnd.uniform(-50, 50),
                                   "soc": rnd.uniform(0, 100)}))
        c = crc16_ccitt_false(bytes(g[:12]))
        g[12] = 0
        g = bytes(g[:12]) + bytes([c >> 8, c & 0xFF])
        h = bytearray(g)
        i, j = rnd.sample(range(4, 12), 2)
        if h[i] != h[j]:
            h[i], h[j] = h[j], h[i]
            kayip["yer_degisimi"][0] += 1
            if crc16_ccitt_false(bytes(h[:12])) != \
                    (h[12] << 8 | h[13]):
                kayip["yer_degisimi"][1] += 1
        h = bytearray(g)
        for k in rnd.sample(range(12), 2):
            h[k] = rnd.randrange(256)
        if bytes(h) != g:
            kayip["iki_bayt_rast"][0] += 1
            if crc16_ccitt_false(bytes(h[:12])) != \
                    (h[12] << 8 | h[13]):
                kayip["iki_bayt_rast"][1] += 1
    return kayip


if __name__ == "__main__":
    import sys
    print("Ornek istek 0x90 :", istek(0x90).hex(" "))
    g = gonderim_ornegi()
    print("Ornek yanit 0x90 :", g.hex(" "))
    print("sagalama dogru    :", toplama_dogrula(g))
    print("main.c coz       :", main_c_coz(g, 0x90))
    print("ESPHome coz      :", esphome_coz(g, 0x90))
    # Yer degisimi ornegi: volt baytlari
    h = bytearray(g)
    h[4], h[5] = h[5], h[4]
    print("\nvolt baytlari yer degisince (sum):", toplama_dogrula(h),
          "main.c volt =", main_c_coz(bytes(h), 0x90)["volt"], "V")
    # 0x95: kare numarasi ve hucre
    g95 = yanit(0x95, {"kare": 1, "hucreler": [3300, 3287, 3312]})
    print("\n0x95 yanit:", g95.hex(" "))
    print("  main.c 'hucre' =", main_c_coz(g95, 0x95)["hucre"], "V")
    print("  ESPHome cell1  =", esphome_coz(g95, 0x95)["hucre1"], "V")
    # Sirali kayip: bir bayt dusunce sabit uzunluk okuma kayar
    akis = yanit(0x90, {"volt": 52.3, "akim": 0, "soc": 50}) + \
        yanit(0x92, {"tmax": 25, "tmax_no": 1, "tmin": 24,
                     "tmin_no": 2})
    kayip_akis = akis[1:]                     # ilk bayt kayboldu
    ilk = kayip_akis[:13]
    print("\n1 bayt kaybi: 13 bayt okunca baslik =", ilk[:4].hex(" "))
    print("  toplama dogrulamasi:", toplama_dogrula(ilk))
    s = tohum_ile_deney()
    print("\nToplama8 yakalama (n=20000, tohum=45):")
    for ad, (n, b) in s.items():
        if n:
            print("  %-14s toplam=%5d  tespit=%5d  oran=%.4f" %
                  (ad, n, b, b / n))
    k = crc_yakalama()
    print("CRC-16 yakalama (toplam, tespit):")
    for ad, (n, b) in k.items():
        print("  %-14s toplam=%5d  tespit=%5d  oran=%.4f" %
              (ad, n, b, b / n))
    if "--yaz" in sys.argv:
        import csv
        yol = "D:/Mevcut Projeler/Kitap/engine/veri/b45_daly_hata.csv"
        with open(yol, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["hata_turu", "toplam", "toplama8_tespit",
                        "crc16_tespit"])
            for ad in ["tek_bit", "yer_degisimi", "iki_bayt_rast",
                       "rast_cerceve"]:
                n, b = s[ad]
                kc = k.get(ad)
                w.writerow([ad, n, b,
                            kc[1] if kc else "-"])
        print("CSV yazildi:", yol)
