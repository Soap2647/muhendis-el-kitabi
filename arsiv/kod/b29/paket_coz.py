# -*- coding: utf-8 -*-
# paket_coz.py - Ethernet + IPv4 + TCP/UDP çerçevesini elle üretir ve
# baytlarını struct ile çözer. Sağlama toplamlarını doğrular.
import struct

# ---------- yardımcılar ----------
def saglama(bayt):
    if len(bayt) % 2:
        bayt += b"\x00"
    toplam = sum((bayt[i] << 8) | bayt[i + 1]
                 for i in range(0, len(bayt), 2))
    while toplam >> 16:
        toplam = (toplam & 0xFFFF) + (toplam >> 16)
    return (~toplam) & 0xFFFF


def ip_bayt(metin):
    return bytes(int(x) for x in metin.split("."))


def mac_bayt(metin):
    return bytes(int(x, 16) for x in metin.split(":"))


def mac_metin(b):
    return ":".join("%02x" % x for x in b)


def ip_metin(b):
    return ".".join(str(x) for x in b)


BAYRAKLAR = [(0x01, "FIN"), (0x02, "SYN"), (0x04, "RST"),
             (0x08, "PSH"), (0x10, "ACK"), (0x20, "URG")]


def bayrak_metni(f):
    return "|".join(ad for bit, ad in BAYRAKLAR if f & bit) or "-"


# ---------- çerçeve üretimi ----------
def tcp_bolumu(kaynak_ip, hedef_ip, sport, dport, seq, ack, bayrak,
               pencere, secenekler=b"", veri=b""):
    ofset = (20 + len(secenekler)) // 4
    ust = struct.pack("!HHIIBBHHH", sport, dport, seq, ack,
                      ofset << 4, bayrak, pencere, 0, 0)
    ust += secenekler + veri
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 6, len(ust)))
    cs = saglama(sahte + ust)
    return ust[:16] + struct.pack("!H", cs) + ust[18:]


def udp_bolumu(kaynak_ip, hedef_ip, sport, dport, veri):
    uzunluk = 8 + len(veri)
    ust = struct.pack("!HHHH", sport, dport, uzunluk, 0) + veri
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 17, uzunluk))
    cs = saglama(sahte + ust) or 0xFFFF   # 0 "sağlama yok" demektir
    return ust[:6] + struct.pack("!H", cs) + ust[8:]


def ipv4_paketi(kaynak_ip, hedef_ip, protokol, yuk,
                ttl=64, kimlik=0x1C46):
    toplam = 20 + len(yuk)
    baslik = struct.pack("!BBHHHBBH4s4s", 0x45, 0, toplam, kimlik,
                         0x4000, ttl, protokol, 0,
                         ip_bayt(kaynak_ip), ip_bayt(hedef_ip))
    cs = saglama(baslik)
    baslik = baslik[:10] + struct.pack("!H", cs) + baslik[12:]
    return baslik + yuk


def ethernet_cercevesi(hedef_mac, kaynak_mac, ethertype, yuk):
    return mac_bayt(hedef_mac) + mac_bayt(kaynak_mac) + \
        struct.pack("!H", ethertype) + yuk


# ---------- çözümleme ----------
def coz_ethernet(c):
    hedef, kaynak, tip = struct.unpack("!6s6sH", c[:14])
    return {"hedef": mac_metin(hedef), "kaynak": mac_metin(kaynak),
            "tip": tip}, c[14:]


def coz_ipv4(p):
    surum_ihl = p[0]
    surum, ihl = surum_ihl >> 4, surum_ihl & 0x0F
    baslik_bayt = ihl * 4
    (_, dscp, toplam, kimlik, bayrak_ofset, ttl, proto, cs,
     kaynak, hedef) = struct.unpack("!BBHHHBBH4s4s", p[:20])
    dogrulama = saglama(p[:baslik_bayt])     # alan doğru ise 0 döner
    return {"surum": surum, "ihl": ihl, "baslik_bayt": baslik_bayt,
            "toplam": toplam, "kimlik": kimlik,
            "df": (bayrak_ofset >> 14) & 1, "ttl": ttl,
            "proto": proto,
            "sag_cs": cs, "sag_ok": dogrulama == 0,
            "kaynak": ip_metin(kaynak), "hedef": ip_metin(hedef)}, \
        p[baslik_bayt:toplam]


def coz_tcp(seg, kaynak_ip, hedef_ip):
    (sport, dport, seq, ack, ofset_rez, bayrak, pencere, cs, acil) = \
        struct.unpack("!HHIIBBHHH", seg[:20])
    ofset = (ofset_rez >> 4) * 4
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 6, len(seg)))
    return {"sport": sport, "dport": dport, "seq": seq, "ack": ack,
            "ofset": ofset, "bayrak": bayrak_metni(bayrak),
            "pencere": pencere, "sag_cs": cs,
            "sag_ok": saglama(sahte + seg) == 0,
            "secenek": seg[20:ofset]}, seg[ofset:]


def coz_udp(seg, kaynak_ip, hedef_ip):
    sport, dport, uzunluk, cs = struct.unpack("!HHHH", seg[:8])
    sahte = (ip_bayt(kaynak_ip) + ip_bayt(hedef_ip) +
             struct.pack("!BBH", 0, 17, uzunluk))
    ok = (cs == 0) or (saglama(sahte + seg[:uzunluk]) == 0)
    return {"sport": sport, "dport": dport, "uzunluk": uzunluk,
            "sag_cs": cs, "sag_ok": ok}, seg[8:uzunluk]


def coz(cerceve):
    eth, yuk = coz_ethernet(cerceve)
    print("Ethernet  hedef=%s kaynak=%s tip=0x%04x" % (
        eth["hedef"], eth["kaynak"], eth["tip"]))
    if eth["tip"] != 0x0800:
        print("  IPv4 değil; çözme durdu.")
        return
    ip, yuk = coz_ipv4(yuk)
    print("IPv4      %s -> %s  ver=%d IHL=%d "
          "(%d bayt) toplam=%d TTL=%d"
          % (ip["kaynak"], ip["hedef"], ip["surum"], ip["ihl"],
             ip["baslik_bayt"], ip["toplam"], ip["ttl"]))
    print("          proto=%d (%s) kimlik=0x%04x DF=%d "
          "sağlama=0x%04x %s"
          % (ip["proto"], {6: "TCP", 17: "UDP"}.get(ip["proto"], "?"),
             ip["kimlik"], ip["df"], ip["sag_cs"],
             "GEÇERLİ" if ip["sag_ok"] else "BOZUK"))
    if ip["proto"] == 6:
        t, veri = coz_tcp(yuk, ip["kaynak"], ip["hedef"])
        print("TCP       %d -> %d seq=%d ack=%d "
              "ofset=%d bayt bayrak=%s"
              % (t["sport"], t["dport"], t["seq"], t["ack"],
                 t["ofset"], t["bayrak"]))
        print("          pencere=%d sağlama=0x%04x %s seçenek=%s"
              % (t["pencere"], t["sag_cs"],
                 "GEÇERLİ" if t["sag_ok"] else "BOZUK",
                 t["secenek"].hex(" ") or "yok"))
        print("          veri=%d bayt" % len(veri))
    elif ip["proto"] == 17:
        u, veri = coz_udp(yuk, ip["kaynak"], ip["hedef"])
        print("UDP       %d -> %d uzunluk=%d sağlama=0x%04x %s"
              % (u["sport"], u["dport"], u["uzunluk"], u["sag_cs"],
                 "GEÇERLİ" if u["sag_ok"] else "BOZUK"))
        print("          veri=%d bayt: %s"
              % (len(veri), veri.hex(" ")))


if __name__ == "__main__":
    # 1. SYN: 10.0.0.5:51514 -> 10.0.0.9:80, MSS=1460 seçenekli
    secenek_mss = bytes([2, 4, 0x05, 0xB4])
    tcp = tcp_bolumu("10.0.0.5", "10.0.0.9", 51514, 80, 1000, 0, 0x02,
                     64240, secenekler=secenek_mss)
    ip = ipv4_paketi("10.0.0.5", "10.0.0.9", 6, tcp)
    syn = ethernet_cercevesi("02:00:00:00:00:09", "02:00:00:00:00:05",
                             0x0800, ip)
    print("== SYN çerçevesi (%d bayt) ==" % len(syn))
    for i in range(0, len(syn), 16):
        print("%04x  %s" % (i, syn[i:i + 16].hex(" ")))
    coz(syn)

    print()
    # 2. Telemetri: UDP 14550, 8 baytlık yük (genel bilgi: MAVLink'in
    # varsayılan GCS UDP portu 14550'dir; bu sadece örnek yüktür).
    udp = udp_bolumu("10.0.0.20", "10.0.0.1", 14550, 14550,
                     bytes(range(8)))
    ip2 = ipv4_paketi("10.0.0.20", "10.0.0.1", 17, udp, ttl=32)
    cerc2 = ethernet_cercevesi("02:00:00:00:00:01",
                               "02:00:00:00:00:20",
                               0x0800, ip2)
    print("== UDP çerçevesi (%d bayt) ==" % len(cerc2))
    coz(cerc2)

    print()
    # 3. Bit bozulması: hedef port 80 -> 81 (1 bit: 0x50 -> 0x51)
    bozuk = bytearray(syn)
    bozuk[14 + 20 + 3] ^= 0x01
    print("== Bozuk çerçeve (hedef port 1 bit değişti) ==")
    coz(bytes(bozuk))
