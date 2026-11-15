# -*- coding: utf-8 -*-
"""b45_telemetri.py: EV telemetri hattı icin sağlamlaştırılmış çerçeve.

Cerceve: [SURUM:1][SIRA:1][YUK:15][CRC16:2, BE]  -> COBS -> 0x00
  YUK (little-endian, 15 bayt):
    spd u16 | bat u8 | volt_x10 u16 | range u16 | btemp i8 | tmp i8
    cell_mv u16 | gear u8 (ASCII) | sigL u8 | sigR u8 | beam u8
  CRC16 = CRC-16/CCITT-FALSE, SURUM ve YUK uzerinden.
Karsilastirma: ayni veri JSON satiri (bugunku hat) ile gurultu
altinda. SIMULASYONDUR; kanal modeli bit ters cevirme (BER).
"""
import json
import random
import struct
import sys

from b45_cobs import cobs_kodla, cobs_coz
from b45_crc import crc16_ccitt_false

SURUM = 1
YUK_FMT = struct.Struct("<HBHHbbHBBBB")     # 15 bayt
assert YUK_FMT.size == 15


def yuk_paketle(d):
    return YUK_FMT.pack(d["spd"], d["bat"], d["volt_x10"], d["range"],
                        d["btemp"], d["tmp"], d["cell_mv"],
                        ord(d["gear"]), d["sigL"], d["sigR"], d["beam"])


def yuk_coz(b):
    (spd, bat, volt, rng, bt, tmp, cell, gear, sl, sr, beam) = \
        YUK_FMT.unpack(b)
    return {"spd": spd, "bat": bat, "volt_x10": volt, "range": rng,
            "btemp": bt, "tmp": tmp, "cell_mv": cell,
            "gear": chr(gear), "sigL": sl, "sigR": sr, "beam": beam}


def cerceve_kodla(d, sira):
    govde = bytes([SURUM, sira & 0xFF]) + yuk_paketle(d)
    c = crc16_ccitt_false(govde)
    ham = govde + bytes([c >> 8, c & 0xFF])
    return cobs_kodla(ham) + b"\x00"


def cerceve_coz(kare):
    """Donus: (sira, yuk) veya ValueError."""
    if not kare or kare[-1] != 0:
        raise ValueError("sonlandirici yok")
    ham = cobs_coz(kare[:-1])
    if len(ham) != 19:
        raise ValueError("uzunluk %d" % len(ham))
    govde, alinan = ham[:17], (ham[17] << 8) | ham[18]
    if crc16_ccitt_false(govde) != alinan:
        raise ValueError("CRC")
    if govde[0] != SURUM:
        raise ValueError("surum")
    return govde[1], yuk_coz(govde[2:])


def ornek_yuk():
    return {"spd": 12, "bat": 87, "volt_x10": 523, "range": 143,
            "btemp": 25, "tmp": -3, "cell_mv": 3300, "gear": "D",
            "sigL": 1, "sigR": 0, "beam": 0}


def json_satiri(d):
    """Bugunku STM32 JSON'una benzer satir (volt, cell: ondalik)."""
    veri = {"spd": d["spd"], "bat": d["bat"],
            "volt": d["volt_x10"] / 10.0, "range": d["range"],
            "btemp": d["btemp"], "tmp": d["tmp"],
            "cell": d["cell_mv"] / 1000.0, "gear": d["gear"],
            "sigL": d["sigL"], "sigR": d["sigR"],
            "beam": "high" if d["beam"] else "low"}
    return (json.dumps(veri, separators=(",", ":")) + "\n").encode()


def rastgele_yuk(rnd):
    return {"spd": rnd.randrange(0, 120), "bat": rnd.randrange(0, 101),
            "volt_x10": rnd.randrange(400, 600),
            "range": rnd.randrange(0, 200),
            "btemp": rnd.randrange(-20, 60),
            "tmp": rnd.randrange(-20, 90),
            "cell_mv": rnd.randrange(2800, 3600),
            "gear": rnd.choice("PRND"), "sigL": rnd.randrange(2),
            "sigR": rnd.randrange(2), "beam": rnd.randrange(2)}


def bit_cevir(bayt_dizisi, ber, rnd):
    """Her bitin ters cevrilme olasiligi ber (bagimsiz)."""
    cikis = bytearray(bayt_dizisi)
    for i in range(len(cikis)):
        for k in range(8):
            if rnd.random() < ber:
                cikis[i] ^= 1 << k
    return bytes(cikis)


def karsilastir(ber, n=20000, tohum=45):
    rnd = random.Random(tohum)
    sayac = {"crc_gecen": 0, "crc_yanlis": 0, "crc_red": 0,
             "json_gecen": 0, "json_yanlis": 0, "json_red": 0}
    for k in range(n):
        d = rastgele_yuk(rnd)
        # --- CRC/COBS hatti
        kare = cerceve_kodla(d, k)
        bozuk = bit_cevir(kare, ber, rnd)
        try:
            sira, y = cerceve_coz(bozuk)
            sayac["crc_gecen"] += 1
            if y != d or sira != (k & 0xFF):
                sayac["crc_yanlis"] += 1
        except ValueError:
            sayac["crc_red"] += 1
        # --- JSON satir hatti (sonlandirici bayt '\n')
        satir = json_satiri(d)
        bozuk = bit_cevir(satir, ber, rnd)
        try:
            v = json.loads(bozuk.decode("utf-8"))
            sayac["json_gecen"] += 1
            beklenen = json.loads(satir.decode())
            if v != beklenen:
                sayac["json_yanlis"] += 1
        except (UnicodeDecodeError, json.JSONDecodeError):
            sayac["json_red"] += 1
    return sayac


def boyut_karsilastirma(n=2000, tohum=45):
    rnd = random.Random(tohum)
    jb = cb = 0
    for k in range(n):
        d = rastgele_yuk(rnd)
        jb += len(json_satiri(d))
        cb += len(cerceve_kodla(d, k))
    return jb / n, cb / n


if __name__ == "__main__":
    d = ornek_yuk()
    kare = cerceve_kodla(d, 7)
    print("yuk (15 bayt):", yuk_paketle(d).hex(" "))
    print("cerceve:", kare.hex(" "), " uzunluk", len(kare))
    print("gidis-donus:", cerceve_coz(kare) == (7, d))
    print("JSON satiri:", json_satiri(d).decode().strip())
    jb, cb = boyut_karsilastirma()
    print("ortalama boyut: JSON %.1f bayt, cerceve %.1f bayt" % (jb, cb))
    # tek bit bozuklugu: CRC yakalar
    bozuk = bytearray(kare)
    bozuk[3] ^= 0x10
    try:
        cerceve_coz(bytes(bozuk))
        print("tek bit bozukluk: KABUL (hata)")
    except ValueError as e:
        print("tek bit bozukluk reddedildi:", e)
    print("\nGurultu (bit basina ters cevirme olasiligi), 20000 kare:")
    for ber in (1e-4, 1e-3, 3e-3):
        s = karsilastir(ber)
        print("BER=%.0e  CRC: gecen=%5d (yanlis=%d) red=%5d | "
              "JSON: gecen=%5d (yanlis=%d) red=%5d" % (
                  ber, s["crc_gecen"], s["crc_yanlis"], s["crc_red"],
                  s["json_gecen"], s["json_yanlis"], s["json_red"]))
    if "--yaz" in sys.argv:
        import csv
        yol = "D:/Mevcut Projeler/Kitap/engine/veri/b45_tel_gurultu.csv"
        with open(yol, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ber", "crc_yanlis", "crc_red", "json_yanlis",
                        "json_red", "n"])
            for ber in (1e-4, 1e-3, 3e-3):
                s = karsilastir(ber)
                w.writerow([ber, s["crc_yanlis"], s["crc_red"],
                            s["json_yanlis"], s["json_red"], 20000])
        print("CSV yazildi:", yol)
