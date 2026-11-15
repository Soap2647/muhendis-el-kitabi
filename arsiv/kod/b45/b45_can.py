# -*- coding: utf-8 -*-
"""b45_can.py: CAN 2.0A (11 bit kimlik) bit duzeyi simulasyonu.

Baskin (dominant) = 0, cekinik (recessive) = 1. Hat, dugumlerden
herhangi biri 0 surdugunde 0'dir (wired-AND). Bit doldurma, CRC-15
ve bit duzeyi tahkim gerceklenir. SIMULASYONDUR; gercek bir CAN
denetleyicisi ya da osiloskop olcumu degildir.
"""
import csv
import random

CRC15_POLI = 0x4599


def crc15(bitler):
    """CAN CRC-15: bit bit, baslangic 0."""
    crc = 0
    for bit in bitler:
        geri = ((crc >> 14) & 1) ^ bit
        crc = (crc << 1) & 0x7FFF
        if geri:
            crc ^= CRC15_POLI
    return crc


def doldur(bitler):
    """5 ardisik ayni bitten sonra zit bit ekler."""
    cikis, kosu, son = [], 0, None
    for b in bitler:
        cikis.append(b)
        kosu = kosu + 1 if b == son else 1
        son = b
        if kosu == 5:
            cikis.append(1 - b)
            son, kosu = 1 - b, 1
    return cikis


def doldurma_coz(sbitler):
    """Doldurulmus bit listesinden orijinali cikarir.
    6 ardisik ayni bit goruldugunde ValueError (doldurma hatasi)."""
    cikis, kosu, son = [], 0, None
    i = 0
    while i < len(sbitler):
        b = sbitler[i]
        cikis.append(b)
        kosu = kosu + 1 if b == son else 1
        son = b
        i += 1
        if kosu == 5:
            if i >= len(sbitler):
                break
            s = sbitler[i]
            if s == b:
                raise ValueError("doldurma hatasi: 6 ardisik bit")
            i += 1
            son, kosu = s, 1
    return cikis


def kare_bitleri(kimlik, veri):
    """SOF..veri alani (CRC oncesi) bit listesi."""
    bitler = [0]                                  # SOF
    bitler += [(kimlik >> (10 - i)) & 1 for i in range(11)]
    bitler += [0, 0, 0]                           # RTR, IDE, r0
    dlc = len(veri)
    bitler += [(dlc >> (3 - i)) & 1 for i in range(4)]
    for b in veri:
        bitler += [(b >> (7 - i)) & 1 for i in range(8)]
    return bitler


def kare_tam(kimlik, veri):
    """Doldurulmus SOF..CRC bitleri + sabit kuyruk (CRC sınırı,
    ACK, EOF). ACK 'slot' ve ACK sınırı burada cekinik (1) yazilir;
    alici slotu baskinlastirabilir (bu modelde yok sayilir)."""
    govde = kare_bitleri(kimlik, veri)
    crc = crc15(govde)
    crc_bitleri = [(crc >> (14 - i)) & 1 for i in range(15)]
    doldurulmus = doldur(govde + crc_bitleri)
    kuyruk = [1] + [1, 1] + [1] * 7               # CRC sinir, ACK, ...
    return doldurulmus + kuyruk, len(doldurulmus)


def tahkim(kimlikler):
    """Ayni anda baslayan dugumler. Dondurur: (kazanan_indeks, adimlar).

    Her adimda hat = AND(gonderilen bitler). Cekinik gonderip hat 0
    okuyan dugum kaybeder ve susar."""
    # Tahkim alani: SOF + 11 bit kimlik + RTR (13 bit), dolgulu
    akislar = []
    for k in kimlikler:
        ham = [0] + [(k >> (10 - i)) & 1 for i in range(11)] + [0]
        akislar.append(doldur(ham))
    aktif = list(range(len(kimlikler)))
    adimlar = []
    for idx in range(max(len(a) for a in akislar)):
        # Gosterim icin tum dugumlerin bitleri; hat yalnizca aktiflerden
        gonder = {d: (akislar[d][idx] if idx < len(akislar[d]) else 1)
                  for d in range(len(kimlikler))}
        hat = min(gonder[d] for d in aktif)    # 0 baskin
        kaybeden = [d for d in aktif if gonder[d] == 1 and hat == 0]
        adimlar.append((idx, dict(gonder), hat, kaybeden))
        aktif = [d for d in aktif if d not in kaybeden]
        if len(aktif) == 1:
            break
    return aktif, adimlar


def rastgele_test(tohum=45, n=2000):
    rnd = random.Random(tohum)
    for _ in range(n):
        m = rnd.randint(1, 160)
        x = [rnd.randrange(2) if rnd.random() < 0.7 else 1
             for _ in range(m)]
        y = doldur(x)
        assert doldurma_coz(y) == x
        for i in range(len(y) - 5):
            if all(y[i + j] == y[i] for j in range(6)):
                raise AssertionError("6 ardisik ayni bit")
    return n


def hata_tespit_orani(tohum=45, n=4000, bit_sayisi=1):
    """Gecerli kareye bit_sayisi rastgele ters cevirme. Donus: oran."""
    rnd = random.Random(tohum)
    tespit = 0
    for _ in range(n):
        kimlik = rnd.randrange(2048)
        veri = bytes(rnd.randrange(256) for _ in range(rnd.randint(0, 8)))
        kare, govde_n = kare_tam(kimlik, veri)
        bozuk = list(kare)
        konumlar = rnd.sample(range(govde_n), bit_sayisi)
        for p in konumlar:
            bozuk[p] ^= 1
        try:
            cozulmus = doldurma_coz(bozuk[:govde_n])
            crc_ok = crc15(cozulmus[:-15]) == \
                int("".join(map(str, cozulmus[-15:])), 2)
            if not crc_ok:
                tespit += 1
        except ValueError:
            tespit += 1
    return tespit / n


if __name__ == "__main__":
    import sys
    print("CRC-15 sifir kalan testi:", end=" ")
    rnd = random.Random(45)
    m = [rnd.randrange(2) for _ in range(60)]
    c = crc15(m)
    print(crc15(m + [(c >> (14 - i)) & 1 for i in range(15)]) == 0)
    print("doldurma/cozme rastgele test: %d gecti" % rastgele_test())
    print("\nTahkim: 0x123 (A), 0x0A5 (B), 0x3F0 (C) ayni anda")
    kaz, adimlar = tahkim([0x123, 0x0A5, 0x3F0])
    for idx, g, hat, kay in adimlar:
        if kay:
            print("  bit %2d: A=%d B=%d C=%d hat=%d  kaybeden: %s" % (
                idx, g[0], g[1], g[2], hat,
                ",".join("ABC"[k] for k in kay)))
    print("  kazanan: %s (kimlik 0x0A5, en kucuk)" % "ABC"[kaz[0]])
    for bit_say in (1, 2, 3):
        print("tespit orani (%d bit ters, 4000 kare): %.4f" %
              (bit_say, hata_tespit_orani(bit_sayisi=bit_say)))
    if "--yaz" in sys.argv:
        veri = "D:/Mevcut Projeler/Kitap/engine/veri/b45_can_tahkim.csv"
        kaz, adimlar = tahkim([0x123, 0x0A5, 0x3F0])
        with open(veri, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["bit", "A", "B", "C", "hat", "kaybeden"])
            for idx, g, hat, kay in adimlar:
                w.writerow([idx, g[0], g[1], g[2], hat,
                            "".join("ABC"[k] for k in kay)])
        print("CSV yazildi:", veri)
