# -*- coding: utf-8 -*-
"""b32_2_hmac_telemetri.py: Bolum 31 telemetrisine HMAC ekleme.

Bolum 31'deki paket: govde 24 bayt + CRC-32 (toplam 28 bayt).
Bu modulde govde ayni, son 4 baytlik CRC yerine 16 baytlik HMAC-SHA256
etiketi kullanilir (toplam 40 bayt). Sira numarasi govdede oldugu icin
etiketin kapsamindadir: degistirilemez ve tekrar oynatilamaz.

Kullanim:
  python b32_2_hmac_telemetri.py goster   # ornek paket ve red tablosu
  python b32_2_hmac_telemetri.py test     # dogrulama testleri
"""

import hashlib
import hmac
import struct
import sys
import zlib

# Ornek anahtar. Uretimde bu deger kod icinde BULUNMAZ; bkz. 32.3.
ANAHTAR = bytes(range(32))

GOVDE = struct.Struct("!BBIIiiiH")   # surum, tur, sira, zaman, ...
ETIKET_BOY = 16                      # HMAC-SHA256, 128 bit
PAKET_BOY = GOVDE.size + ETIKET_BOY  # 24 + 16 = 40
SURUM = 2
TUR_TELE = 1


def paketle(anahtar, sira, zaman, enlem, boylam, irtifa, batarya):
    govde = GOVDE.pack(SURUM, TUR_TELE, sira, zaman,
                       enlem, boylam, irtifa, batarya)
    etiket = hmac.new(anahtar, govde, hashlib.sha256).digest()
    return govde + etiket[:ETIKET_BOY]


class Alici:
    """Etiket dogrular, sira numarasi ilerlemiyorsa reddeder."""

    def __init__(self, anahtar):
        self.anahtar = anahtar
        self.son_sira = -1
        self.red = {"bicim": 0, "etiket": 0, "tekrar": 0}

    def al(self, p):
        if len(p) != PAKET_BOY:
            self.red["bicim"] += 1
            return None
        govde, etiket = p[:GOVDE.size], p[GOVDE.size:]
        beklenen = hmac.new(self.anahtar, govde,
                            hashlib.sha256).digest()[:ETIKET_BOY]
        # Sabit zamanli karsilastirma: zamanlama sizintisini onler
        if not hmac.compare_digest(beklenen, etiket):
            self.red["etiket"] += 1
            return None
        surum, tur, sira, zaman, enlem, boylam, irtifa, batarya = \
            GOVDE.unpack(govde)
        if surum != SURUM or tur != TUR_TELE:
            self.red["bicim"] += 1
            return None
        if sira <= self.son_sira:          # tekrar oynatma (replay)
            self.red["tekrar"] += 1
            return None
        self.son_sira = sira
        return {"sira": sira, "zaman": zaman, "enlem": enlem,
                "boylam": boylam, "irtifa": irtifa,
                "batarya": batarya}


# ---- Karsilastirma icin yalnizca CRC-32 kullanan eski duzen ---- #
def crc_paketle(govde):
    return govde + struct.pack("!I", zlib.crc32(govde))


def crc_kabul(p):
    """Yalnizca CRC kontrol eden alici: govdeyi kabul eder."""
    govde, crc = p[:-4], struct.unpack("!I", p[-4:])[0]
    return zlib.crc32(govde) == crc


def crc_sahtele(p, ofset, yeni_bayt):
    """Govdeyi degistirip CRC'yi yeniden hesaplar. CRC bir anahtar
    olmadigi icin bunu herkes yapabilir: CRC butunluk degil, hata
    algilamadir."""
    govde = bytearray(p[:-4])
    govde[ofset] = yeni_bayt
    return crc_paketle(bytes(govde))


def goster():
    p = paketle(ANAHTAR, 7, 123456, 390000000,
                329000000, 15200, 11980)
    print("paket boyu: %d bayt (govde %d + etiket %d)"
          % (len(p), GOVDE.size, ETIKET_BOY))
    print("hex  :", p[:20].hex(" "))
    print("      ", p[20:].hex(" "))
    a = Alici(ANAHTAR)
    print("ilk teslim:", a.al(p) is not None)
    print("ayni paket tekrar:", a.al(p) is None)
    bozuk = bytearray(p)
    bozuk[GOVDE.size - 1] ^= 0x01        # batarya alaninin bir biti
    print("bit bozulmus:", a.al(bytes(bozuk)) is None)
    print("red sayaclari:", a.red)
    sahte_govde = GOVDE.pack(SURUM, TUR_TELE, 8, 123457, 390000000,
                             329000000, 15200, 11980)
    print("etiketsiz sahte govde reddedildi:",
          a.al(sahte_govde + p[GOVDE.size:]) is None)
    c = crc_paketle(p[:GOVDE.size])
    s = crc_sahtele(c, 10, 0x10)         # enlem alani
    print("CRC ile sahte paket kabul:", crc_kabul(s))


def test():
    hata = 0

    def dogru(ad, kosul):
        nonlocal hata
        print(("GECTI " if kosul else "KALDI ") + ad)
        if not kosul:
            hata += 1

    p = paketle(ANAHTAR, 1, 1000, 1, 2, 3, 4)
    dogru("boyut 40 bayt", len(p) == PAKET_BOY)
    dogru("gecerli paket kabul", Alici(ANAHTAR).al(p) is not None)
    # Her bit tek tek degistirilir; hepsi reddedilmeli
    kac_kabul = 0
    for i in range(PAKET_BOY * 8):
        b = bytearray(p)
        b[i // 8] ^= 1 << (i % 8)
        if Alici(ANAHTAR).al(bytes(b)) is not None:
            kac_kabul += 1
    dogru("320 tek-bit bozulmanin hepsi red (kabul=%d)" % kac_kabul,
          kac_kabul == 0)
    yanlis = Alici(bytes(32))
    dogru("yanlis anahtar red", yanlis.al(p) is None)
    a = Alici(ANAHTAR)
    dogru("ilk paket kabul", a.al(p) is not None)
    dogru("ayni paket (replay) red", a.al(p) is None)
    p2 = paketle(ANAHTAR, 0, 1, 1, 2, 3, 4)
    dogru("geri sira (0 < 1) red", a.al(p2) is None)
    dogru("kisa paket red", a.al(p[:-1]) is None)
    dogru("sira ilerleyince kabul",
          a.al(paketle(ANAHTAR, 2, 1, 1, 2, 3, 4)) is not None)
    c = crc_paketle(p[:GOVDE.size])
    s = crc_sahtele(c, 10, 0x10)
    dogru("CRC'li sahte paket kabul ediliyor (zafiyet gosterimi)",
          crc_kabul(s))
    print("hata sayisi:", hata)
    return hata


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "goster":
        goster()
    elif kip == "test":
        sys.exit(1 if test() else 0)
    else:
        print("kullanim: goster | test")
        sys.exit(2)
