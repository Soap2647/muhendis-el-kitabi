# -*- coding: utf-8 -*-
"""b32_4_rastgele.py: random ile secrets farki, etkin guc.

Bu program kendi jeton uretimimizi olcer: 128 bitlik bir jeton,
16 bitlik bir tohumdan uretilirse etkin guc 128 degil 16 bittir.
Olcum, tohum uzayinin sayimi ile yapilir; baska bir sisteme karsi
kullanilmaz.

Kullanim:
  python b32_4_rastgele.py goster
  python b32_4_rastgele.py test
"""

import random
import secrets
import sys
import time

TOHUM_BIT = 16                 # deney icin kucuk bir tohum uzayi


def zayif_jeton(tohum):
    """YANLIS: random, tohumu bilinen kucuk bir kaynaktan alir."""
    return "%032x" % random.Random(tohum).getrandbits(128)


def guclu_jeton():
    """DOGRU: isletim sistemi CSPRNG'sinden 128 bit."""
    return secrets.token_hex(16)


def tohum_say(hedef_jeton, bit):
    """Tohum uzayini sirayla tarar; etkin gucu olcer."""
    denenen = 0
    for tohum in range(1 << bit):
        denenen += 1
        if zayif_jeton(tohum) == hedef_jeton:
            return tohum, denenen
    return None, denenen


def goster():
    print("random, ayni tohum -> ayni dizi (tekrarlanabilirlik):")
    print("  tohum=42 ilk:", zayif_jeton(42))
    print("  tohum=42 ikinci:", zayif_jeton(42))
    print("secrets, her cagrida farkli:")
    for _ in range(3):
        print("  ", guclu_jeton())
    tohum_gercek = 40123
    hedef = zayif_jeton(tohum_gercek)
    t = time.perf_counter()
    bulunan, sayi = tohum_say(hedef, TOHUM_BIT)
    sure = time.perf_counter() - t
    print("%d-bit tohum uzayinda tarama:" % TOHUM_BIT)
    print("  bulunan tohum=%d, denenen=%d, sure=%.2f s"
          % (bulunan, sayi, sure))
    print("  jetonun nominal gucu: 128 bit; etkin guc: %d bit"
          % TOHUM_BIT)


def test():
    hata = 0

    def dogru(ad, kosul):
        nonlocal hata
        print(("GECTI " if kosul else "KALDI ") + ad)
        if not kosul:
            hata += 1

    dogru("ayni tohum ayni jeton", zayif_jeton(7) == zayif_jeton(7))
    dogru("farkli tohum farkli jeton",
          zayif_jeton(7) != zayif_jeton(8))
    dogru("jeton 32 hex karakter", len(guclu_jeton()) == 32)
    dogru("secrets iki cagri farkli", guclu_jeton() != guclu_jeton())
    hedef = zayif_jeton(777)
    bulunan, _ = tohum_say(hedef, 10)
    dogru("10-bit uzayda tohum bulunur", bulunan == 777)
    bulunan, sayi = tohum_say(hedef, 9)
    dogru("tohum uzayi kucukse bulunamaz",
          bulunan is None and sayi == 512)
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
