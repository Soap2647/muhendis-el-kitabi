# -*- coding: utf-8 -*-
"""b31_udp.py: UDP uzerinde durdur-bekle guvenilir aktarim
ve CRC'li telemetri paketi. Gercek UDP soketleri, yalnizca loopback.

Kullanim:
  python b31_udp.py test                # telemetri + iz tablosu
  python b31_udp.py olc CSV_YOLU        # kayip oranina gore olcum
"""

import random
import socket
import struct
import sys
import threading
import time
import zlib

VERI, ONAY = 0, 1
BASLIK = struct.Struct("!BB")  # tur, sira biti (0/1)
ZAMAN_ASIMI = 0.05  # saniye
MAKS_YENIDEN = 200  # emniyet siniri

# ---- Telemetri paketi: 24 bayt govde + 4 bayt CRC-32 ------ #
TELE_GOVDE = struct.Struct("!BBIIiiiH")  # surum, tur, sira, zaman,
# enlem, boylam, irtifa, batarya
TELE = struct.Struct("!BBIIiiiHI")  # govde + crc (28 bayt)


def telemetri_paketi(
    sira, zaman_ms, enlem, boylam, irtifa_cm, batarya_mv
):
    govde = TELE_GOVDE.pack(
        1, 0x01, sira, zaman_ms, enlem, boylam, irtifa_cm, batarya_mv
    )
    return govde + struct.pack("!I", zlib.crc32(govde))


def telemetri_coz(p):
    if len(p) != TELE.size:
        raise ValueError("uzunluk hatali: %d" % len(p))
    govde, (crc,) = p[: TELE_GOVDE.size], struct.unpack("!I", p[-4:])
    if zlib.crc32(govde) != crc:
        raise ValueError("CRC uyusmuyor")
    surum, tur, sira, zm, enl, boy, irt, bat = TELE_GOVDE.unpack(
        govde
    )
    if surum != 1 or tur != 0x01:
        raise ValueError("bilinmeyen surum/tur")
    return {
        "sira": sira,
        "zaman_ms": zm,
        "enlem": enl / 1e7,
        "boylam": boy / 1e7,
        "irtifa_m": irt / 100.0,
        "batarya_V": bat / 1000.0,
    }


# ---- Durdur-bekle: gonderici ve alici ---------------------- #


def gonderici(alici_port, mesajlar, kayip_p, tohum, iz):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    s.settimeout(ZAMAN_ASIMI)
    rnd = random.Random(tohum)
    sira = 0
    yeniden = gonderim = 0
    for i, m in enumerate(mesajlar):
        deneme = 0
        while True:
            deneme += 1
            gonderim += 1
            if rnd.random() < kayip_p:
                iz.append(("kayip", i, sira, deneme))
            else:
                s.sendto(
                    BASLIK.pack(VERI, sira) + m,
                    ("127.0.0.1", alici_port),
                )
                iz.append(("gonder", i, sira, deneme))
            try:
                while True:  # yanlis siradaki onayi at
                    cevap, _ = s.recvfrom(64)
                    tur, osira = BASLIK.unpack(cevap[:2])
                    if tur == ONAY and osira == sira:
                        break
                iz.append(("onay", i, sira, deneme))
                break
            except socket.timeout:
                yeniden += 1
                iz.append(("zaman_asimi", i, sira, deneme))
                if deneme >= MAKS_YENIDEN:
                    raise RuntimeError("cok fazla yeniden iletim")
        sira ^= 1
    s.close()
    return gonderim, yeniden


def alici(s, adet, kayip_p, tohum, sonuc):
    s.settimeout(0.3)  # sessizlik = gonderici bitti
    rnd = random.Random(tohum)
    beklenen = 0
    teslim, kopya = [], 0
    adres = None
    while True:
        try:
            paket, adres = s.recvfrom(2048)
        except socket.timeout:
            break
        tur, sira = BASLIK.unpack(paket[:2])
        if tur != VERI:
            continue
        if sira == beklenen:
            teslim.append(paket[2:])
            beklenen ^= 1
        else:
            kopya += 1  # yinelenen veri: teslim etme
        if rnd.random() >= kayip_p:  # onayin kaybi da simule edilir
            s.sendto(BASLIK.pack(ONAY, sira), adres)
    # Son onay kaybolursa gonderici yeniden ister; alici, 0.3 sn
    # sessizlige kadar dinler ve yinelenen veriyi yeniden onaylar.
    s.close()
    sonuc.extend([teslim, kopya])


def aktar(mesajlar, kayip_p, tohum=31, iz=None):
    iz = [] if iz is None else iz
    dinle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dinle.bind(("127.0.0.1", 0))  # alici once baglanir
    port = dinle.getsockname()[1]
    sonuc = []
    t = threading.Thread(
        target=alici,
        args=(dinle, len(mesajlar), kayip_p, tohum + 1, sonuc),
    )
    t.start()
    t0 = time.perf_counter()
    gonderim, yeniden = gonderici(port, mesajlar, kayip_p, tohum, iz)
    t.join()
    sure = time.perf_counter() - t0
    teslim, kopya = sonuc
    return {
        "teslim": teslim,
        "gonderim": gonderim,
        "yeniden": yeniden,
        "kopya": kopya,
        "sure": sure,
    }


def test():
    # 1) Telemetri paketi: gidis-donus ve bit bozulmasi
    p = telemetri_paketi(
        7, 123456, int(40.9 * 1e7), int(29.0 * 1e7), 15230, 22300
    )
    print("telemetri boyutu: %d bayt" % len(p))
    for k, v in telemetri_coz(p).items():
        print("  %s = %s" % (k, v))
    bozuk = bytearray(p)
    bozuk[10] ^= 0x04  # tek bit
    try:
        telemetri_coz(bytes(bozuk))
        print("bozuk: kabul edildi (beklenmiyordu)")
    except ValueError as e:
        print("bozuk paket reddedildi:", e)

    # 2) Kucuk stop-and-wait ornegi, %30 kayip, iz tablosu
    mesajlar = [("veri-%02d" % i).encode() for i in range(8)]
    iz = []
    r = aktar(mesajlar, 0.30, tohum=31, iz=iz)
    assert r["teslim"] == mesajlar, "sira/icerik hatali"
    print("\nIz (ilk 12 olay):")
    print(
        "%-12s %-4s %-4s %-6s" % ("olay", "mesaj", "sira", "deneme")
    )
    for olay in iz[:12]:
        print("%-12s %-4d %-4d %-6d" % olay)
    print(
        "\nmesaj=%d gonderim=%d yeniden=%d kopya=%d sure=%.2f s"
        % (
            len(mesajlar),
            r["gonderim"],
            r["yeniden"],
            r["kopya"],
            r["sure"],
        )
    )
    print("TESLIM DOGRU: sira ve icerik birebir ayni")


def olc(csv_yolu):
    satirlar = ["kayip_p,mesaj,gonderim,yeniden,kopya,sure_s"]
    mesajlar = [("%04d" % i).encode() * 4 for i in range(200)]
    for kayip in [0.0, 0.05, 0.10, 0.20, 0.30]:
        r = aktar(mesajlar, kayip, tohum=31)
        assert r["teslim"] == mesajlar
        satir = "%.2f,%d,%d,%d,%d,%.3f" % (
            kayip,
            len(mesajlar),
            r["gonderim"],
            r["yeniden"],
            r["kopya"],
            r["sure"],
        )
        print(satir, flush=True)
        satirlar.append(satir)
    with open(csv_yolu, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "test":
        test()
    elif kip == "olc":
        olc(sys.argv[2])
