# -*- coding: utf-8 -*-
# ag_hesap.py - alt ağ, LPM ve IPv4 sağlama toplamı
# toplamı. Her sonuç Python'un ipaddress modülüyle karşılaştırılır.
import ipaddress
import random


# ---------- 1. IPv4 adresini 32 bitlik tamsayıya çevirme ----------
def ip_sayi(metin):
    parca = [int(x) for x in metin.split(".")]
    sayi = 0
    for p in parca:
        sayi = (sayi << 8) | p
    return sayi


def sayi_ip(s):
    return ".".join(str((s >> sh) & 0xFF) for sh in (24, 16, 8, 0))


# ---------- 2. Alt ağ hesabı (elle yapılan işlemin kodu) ----------
def alt_ag(cidr):
    ag, uz = cidr.split("/")
    p = int(uz)
    maske = (0xFFFFFFFF << (32 - p)) & 0xFFFFFFFF
    ip = ip_sayi(ag)
    ag_adresi = ip & maske
    yayin = ag_adresi | (~maske & 0xFFFFFFFF)
    toplam = 1 << (32 - p)
    if p == 32:
        host = 1
        ilk = son = ag_adresi
    elif p == 31:
        host = 2   # RFC 3021: /31 nokta-nokta bağlantı
        ilk, son = ag_adresi, yayin
    else:
        host = toplam - 2
        ilk, son = ag_adresi + 1, yayin - 1
    return {"ag": sayi_ip(ag_adresi), "maske": sayi_ip(maske),
            "ilk": sayi_ip(ilk), "son": sayi_ip(son),
            "yayin": sayi_ip(yayin), "host": host}


def alt_ag_dogrula(cidr):
    n = ipaddress.ip_network(cidr, strict=False)
    if n.prefixlen >= 31:
        ilk, son = n.network_address, n.broadcast_address
        if n.prefixlen == 32:
            ilk = son = n.network_address
        host = n.num_addresses if n.prefixlen == 31 else 1
    else:
        ilk = n[1]
        son = n[-2]
        host = n.num_addresses - 2
    return {"ag": str(n.network_address), "maske": str(n.netmask),
            "ilk": str(ilk), "son": str(son),
            "yayin": str(n.broadcast_address), "host": host}


# ---------- 3. En uzun önek eşleşmesi: ikili trie ----------
class Dugum:
    __slots__ = ("cocuk", "hedef")

    def __init__(self):
        self.cocuk = [None, None]
        self.hedef = None


class YonlendirmeTrie:
    def __init__(self):
        self.kok = Dugum()

    def ekle(self, cidr, hedef):
        ag, uz = cidr.split("/")
        p = int(uz)
        ip = ip_sayi(ag)
        dugum = self.kok
        for i in range(p):
            bit = (ip >> (31 - i)) & 1
            if dugum.cocuk[bit] is None:
                dugum.cocuk[bit] = Dugum()
            dugum = dugum.cocuk[bit]
        dugum.hedef = hedef

    def bul(self, adres):
        ip = ip_sayi(adres)
        dugum = self.kok
        son_eslesme = dugum.hedef   # /0: varsayılan yol
        for i in range(32):
            bit = (ip >> (31 - i)) & 1
            dugum = dugum.cocuk[bit]
            if dugum is None:
                break
            if dugum.hedef is not None:
                son_eslesme = dugum.hedef   # daha uzun eşleşme
        return son_eslesme


TABLO = [
    ("0.0.0.0/0", "eth0 üzerinden 172.21.192.1 (varsayılan)"),
    ("172.21.192.0/20", "eth0 (doğrudan bağlı)"),
    ("10.0.0.0/8", "vpn0"),
    ("10.1.0.0/16", "vpn1"),
    ("10.1.2.0/24", "ofis-lan"),
    ("10.1.2.128/25", "sensor-ag"),
]


def lpm_brute(adres, tablo):
    ip = ipaddress.ip_address(adres)
    en_iyi, en_uz = None, -1
    for cidr, hedef in tablo:
        n = ipaddress.ip_network(cidr)
        if ip in n and n.prefixlen > en_uz:
            en_iyi, en_uz = hedef, n.prefixlen
    return en_iyi


# ---------- 4. IPv4 başlık saglama toplamı (RFC 1071) ----------
def saglama(bayt):
    if len(bayt) % 2:
        bayt += b"\x00"
    toplam = 0
    for i in range(0, len(bayt), 2):
        toplam += (bayt[i] << 8) | bayt[i + 1]
    while toplam >> 16:
        toplam = (toplam & 0xFFFF) + (toplam >> 16)
    return (~toplam) & 0xFFFF


if __name__ == "__main__":
    print("== 1. Alt ağ hesabı ==")
    for c in ["192.168.10.77/26", "10.1.2.200/25", "172.21.200.9/20",
              "192.168.1.1/31", "10.0.0.5/32"]:
        e = alt_ag(c)
        d = alt_ag_dogrula(c)
        durum = "UYUMLU" if all(str(e[k]) == str(d[k]) for k in e) else "FARKLI"
        print("%s  [%s]" % (c, durum))
        print("  ağ=%s  yayın=%s  maske=%s" % (e["ag"], e["yayin"], e["maske"]))
        print("  ilk=%s  son=%s  host=%d" % (e["ilk"], e["son"], e["host"]))

    print()
    print("== 2. Yönlendirme tablosu ve LPM ==")
    trie = YonlendirmeTrie()
    for cidr, hedef in TABLO:
        trie.ekle(cidr, hedef)
    for adres in ["10.1.2.130", "10.1.2.5", "10.1.9.9", "10.9.9.9",
                  "172.21.205.116", "8.8.8.8"]:
        print("%-16s -> %s" % (adres, trie.bul(adres)))

    print()
    print("== 3. Rastgele 20000 adresle trie ve kaba kuvvet karşılaştırması ==")
    random.seed(29)
    uyusmayan = 0
    for _ in range(20000):
        ip = random.getrandbits(32)
        adres = sayi_ip(ip)
        if trie.bul(adres) != lpm_brute(adres, TABLO):
            uyusmayan += 1
    print("uyuşmayan sonuç sayısı:", uyusmayan)

    print()
    print("== 4. IPv4 sağlama toplamı ==")
    # Wikipedia "IPv4 header checksum" örneği (saglama alanı 0 iken):
    baslik = bytes.fromhex("450000730000400040110000c0a80001c0a800c7")
    cs = saglama(baslik)
    print("hesaplanan saglama   : 0x%04x" % cs)
    tamam = baslik[:10] + bytes([cs >> 8, cs & 0xFF]) + baslik[12:]
    print("doğrulama (0 olmalı) : 0x%04x" % saglama(tamam))
