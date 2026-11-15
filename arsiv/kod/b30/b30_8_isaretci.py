# -*- coding: utf-8 -*-
"""b30_8_isaretci.py: Kayitli bir DNS yanitinda ad sikistirma izi.

Ag gerektirmez; ayni bayt dizisi her calistirmada ayni sonucu verir.
Kullanim: python b30_8_isaretci.py
"""
from b30_1_dns_ham import yanit_ayristir

HEX = ("1a 2b 81 80 00 01 00 02 00 00 00 00 07 65 78 61 "
       "6d 70 6c 65 03 63 6f 6d 00 00 01 00 01 c0 0c 00 "
       "01 00 01 00 00 00 57 00 04 68 14 17 9a c0 0c 00 "
       "01 00 01 00 00 00 57 00 04 ac 42 93 f3")
VERI = bytes.fromhex(HEX)


def ad_izle(veri, i):
    """ad_coz'un adim adim izlenen surumu: sadece yazdirir."""
    print("  ofset %d'den ad okunuyor" % i)
    while True:
        uz = veri[i]
        if uz & 0xC0 == 0xC0:                     # isaretci
            hedef = ((uz & 0x3F) << 8) | veri[i + 1]
            print("  %2d: %02x %02x  isaretci -> ofset %d"
                  % (i, uz, veri[i + 1], hedef))
            i = hedef
        elif uz == 0:
            print("  %2d: 00       ad sonu" % i)
            return
        else:
            etiket = veri[i + 1:i + 1 + uz].decode("ascii")
            print("  %2d: %02x       etiket \"%s\"" % (i, uz, etiket))
            i += 1 + uz


if __name__ == "__main__":
    print("Yanit: %d bayt" % len(VERI))
    print("Birinci yanit kaydinin adi (ofset 29):")
    ad_izle(VERI, 29)
    r = yanit_ayristir(VERI)
    print("kimlik=0x%04X rcode=%d kayit=%d" % (
        r["kimlik"], r["rcode"], len(r["kayitlar"])))
    for ad, tip, ttl, deger in r["kayitlar"]:
        print("  %s tip=%d TTL=%d -> %s" % (ad, tip, ttl, deger))
