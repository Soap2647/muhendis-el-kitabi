# -*- coding: utf-8 -*-
"""b30_1_dns_ham.py: Ham UDP DNS sorgusu kurar, yaniti ayristirir.

Kullanim: python b30_1_dns_ham.py [ad] [sunucu]
"""
import socket
import struct
import sys
import time


def etiket_bayt(ad):
    """example.com icin: 7 example 3 com 0 (uzunluk onekli)."""
    cikti = b""
    for parca in ad.rstrip(".").split("."):
        b = parca.encode("ascii")
        cikti += bytes([len(b)]) + b
    return cikti + b"\0"


def sorgu_kur(ad, qtype=1, kimlik=0x1A2B):
    """12 baytlik baslik + soru bolumu."""
    bayrak = 0x0100                   # RD: ozyinelemeli iste
    baslik = struct.pack(">HHHHHH", kimlik, bayrak, 1, 0, 0, 0)
    soru = etiket_bayt(ad) + struct.pack(">HH", qtype, 1)
    return baslik + soru


def ad_coz(veri, i):
    """Sikistirmali adi okur. Donus: (ad, sonraki ofset)."""
    parcalar, atlandi, son, sayac = [], False, 0, 0
    while True:
        uz = veri[i]
        if uz & 0xC0 == 0xC0:         # isaretci: 2 bayt
            if not atlandi:
                son = i + 2           # ana akis burada devam eder
            i = ((uz & 0x3F) << 8) | veri[i + 1]
            atlandi = True
            sayac += 1
            if sayac > 20:
                raise ValueError("isaretci dongusu")
            continue
        if uz == 0:
            i += 1
            break
        parcalar.append(veri[i + 1:i + 1 + uz].decode("ascii"))
        i += 1 + uz
    return ".".join(parcalar), (son if atlandi else i)


def rdata_coz(veri, tip, i, uz):
    """Kayit verisini (RDATA) tipine gore yorumlar."""
    rd = veri[i:i + uz]
    if tip == 1:                      # A
        return socket.inet_ntop(socket.AF_INET, rd)
    if tip == 28:                     # AAAA
        return socket.inet_ntop(socket.AF_INET6, rd)
    if tip in (2, 5):                 # NS, CNAME: tek ad
        return ad_coz(veri, i)[0]
    if tip == 15:                     # MX: oncelik + ad
        onc = struct.unpack(">H", rd[:2])[0]
        return "%d %s" % (onc, ad_coz(veri, i + 2)[0] or ".")
    return rd.hex()


def yanit_ayristir(veri):
    kimlik, bayrak, qd, an, _, _ = struct.unpack(">HHHHHH", veri[:12])
    i = 12
    for _ in range(qd):               # soru bolumu
        _, i = ad_coz(veri, i)
        i += 4                        # QTYPE + QCLASS
    kayitlar = []
    for _ in range(an):
        ad, i = ad_coz(veri, i)
        tip, sinif, ttl, uz = struct.unpack(">HHIH", veri[i:i + 10])
        i += 10
        kayitlar.append((ad, tip, ttl, rdata_coz(veri, tip, i, uz)))
        i += uz
    return {"kimlik": kimlik, "rcode": bayrak & 0xF,
            "kayitlar": kayitlar}


def sorgula(ad, sunucu, qtype=1):
    q = sorgu_kur(ad, qtype)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3.0)
    t0 = time.perf_counter()
    s.sendto(q, (sunucu, 53))
    yanit, _ = s.recvfrom(4096)
    s.close()
    return q, yanit, (time.perf_counter() - t0) * 1000


def hex_satir(b):
    for i in range(0, len(b), 16):
        print("  %04x  %s" % (i, b[i:i + 16].hex(" ")))


if __name__ == "__main__":
    ad = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    sunucu = sys.argv[2] if len(sys.argv) > 2 else "1.1.1.1"
    q, yanit, sure = sorgula(ad, sunucu)
    print("Sorgu (%d bayt):" % len(q))
    hex_satir(q)
    print("Yanit (%d bayt, %.1f ms):" % (len(yanit), sure))
    hex_satir(yanit)
    r = yanit_ayristir(yanit)
    print("kimlik=0x%04X rcode=%d" % (r["kimlik"], r["rcode"]))
    for ad_, tip, ttl, deger in r["kayitlar"]:
        print("  %s tip=%d TTL=%d -> %s" % (ad_, tip, ttl, deger))
    print("socket.getaddrinfo (IPv4):")
    kume = {x[4][0]
            for x in socket.getaddrinfo(ad, 80, socket.AF_INET)}
    print("  ", sorted(kume))
