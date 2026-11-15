# -*- coding: utf-8 -*-
"""b30_7_dhcp_sema.py: DHCP OFFER paketini cevrimdisi kurar, okur.

Hicbir paket aga gonderilmez. Alanlar RFC 2131 Bolum 2 ve 4.3.
"""
import socket
import struct

MAGIC = bytes([99, 130, 83, 99])          # 0x63825363
MESAJ = {1: "DISCOVER", 2: "OFFER", 3: "REQUEST", 5: "ACK"}


def ip(b):
    return socket.inet_ntoa(b)


def opt(kod, veri):
    return bytes([kod, len(veri)]) + veri


def offer_kur(mac, yeni_ip, sunucu_ip):
    sabit = struct.pack(
        ">BBBBIHH4s4s4s4s16s64s128s",
        2, 1, 6, 0,                     # op=BOOTREPLY, htype, hlen
        0x3903F326, 0, 0x0000,          # xid, secs, flags
        b"\0" * 4,                      # ciaddr
        socket.inet_aton(yeni_ip),      # yiaddr: sunulan IP
        socket.inet_aton(sunucu_ip),    # siaddr: sunucu
        b"\0" * 4,                      # giaddr
        mac + b"\0" * 10,               # chaddr (16 bayt)
        b"", b"")                       # sname, file (bos)
    secenek = opt(53, bytes([2]))                         # OFFER
    secenek += opt(54, socket.inet_aton(sunucu_ip))       # sunucu
    secenek += opt(51, struct.pack(">I", 86400))          # kira
    secenek += opt(1, socket.inet_aton("255.255.255.0"))  # maske
    secenek += opt(3, socket.inet_aton(sunucu_ip))        # gecit
    secenek += opt(6, socket.inet_aton("1.1.1.1"))        # DNS
    secenek += bytes([255])                               # END
    return sabit + MAGIC + secenek


def ayristir(paket):
    op, htype, hlen, hops, xid, secs, flags = struct.unpack(
        ">BBBBIHH", paket[:12])
    if paket[236:240] != MAGIC:
        raise ValueError("sihirli cerez yok")
    secenekler, i = {}, 240
    while i < len(paket):
        kod = paket[i]
        if kod == 255:                  # END
            break
        if kod == 0:                    # PAD
            i += 1
            continue
        uz = paket[i + 1]
        secenekler[kod] = paket[i + 2:i + 2 + uz]
        i += 2 + uz
    return {
        "op": op, "xid": "0x%08X" % xid, "flags": "0x%04X" % flags,
        "yiaddr": ip(paket[16:20]), "siaddr": ip(paket[20:24]),
        "chaddr": paket[28:28 + hlen].hex(":"),
        "mesaj": MESAJ[secenekler[53][0]],
        "maske": ip(secenekler[1]), "ag_gecidi": ip(secenekler[3]),
        "dns": ip(secenekler[6]),
        "kira_s": struct.unpack(">I", secenekler[51])[0],
    }


if __name__ == "__main__":
    p = offer_kur(bytes.fromhex("0a1b2c3d4e5f"), "192.168.1.50",
                  "192.168.1.1")
    print("Paket boyutu: %d bayt" % len(p))
    print("Ilk 32 bayt:")
    for i in range(0, 32, 16):
        print("  %02x  %s" % (i, p[i:i + 16].hex(" ")))
    for ad, deger in ayristir(p).items():
        print("  %-9s = %s" % (ad, deger))
