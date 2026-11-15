# -*- coding: utf-8 -*-
"""b32_3_aead_imza.py: AEAD ile sifreleme+dogrulama ve Ed25519 imza.

Kriptografi algoritmasi bu dosyada YAZILMAZ; `cryptography` paketinin
(OpenSSL tabanli) AESGCM, ChaCha20Poly1305 ve Ed25519 kullanilir.

Kullanim:
  python b32_3_aead_imza.py goster
  python b32_3_aead_imza.py test
"""

import os
import sys

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import (
    AESGCM, ChaCha20Poly1305)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)


def sifrele(anahtar_sinifi, anahtar, yuk, ek_veri):
    """Rastgele 96 bit nonce; cikti = nonce + sifreli + etiket."""
    nonce = os.urandom(12)
    sifreli = anahtar_sinifi(anahtar).encrypt(nonce, yuk, ek_veri)
    return nonce + sifreli


def coz(anahtar_sinifi, anahtar, paket, ek_veri):
    nonce, sifreli = paket[:12], paket[12:]
    # Etiket tutmazsa InvalidTag: hic duz metin uretilmez
    return anahtar_sinifi(anahtar).decrypt(nonce, sifreli, ek_veri)


def goster():
    anahtar = AESGCM.generate_key(bit_length=256)
    yuk = b"enlem=39.0 boylam=32.9 batarya=11980"
    ek = b"sira=7;tur=1"          # sifrelenmez ama dogrulanir
    p = sifrele(AESGCM, anahtar, yuk, ek)
    print("duz metin: %d bayt" % len(yuk))
    print("paket    : %d bayt (12 nonce + %d sifreli+etiket)"
          % (len(p), len(p) - 12))
    print("etiket   : son 16 bayt, sifreli kisim: %d bayt"
          % (len(p) - 12 - 16))
    print("cozuldu  :", coz(AESGCM, anahtar, p, ek) == yuk)
    bozuk = bytearray(p)
    bozuk[20] ^= 0x01
    try:
        coz(AESGCM, anahtar, bytes(bozuk), ek)
        print("bozuk sifreli kabul (hata!)")
    except InvalidTag:
        print("sifreli kisimda 1 bit: InvalidTag (red)")
    try:
        coz(AESGCM, anahtar, p, b"sira=8;tur=1")
        print("ek veri degisti: kabul (hata!)")
    except InvalidTag:
        print("ek veri (sira) degisti: InvalidTag (red)")
    cp = sifrele(ChaCha20Poly1305, os.urandom(32),
                 yuk, ek)
    print("ChaCha20-Poly1305 paket: %d bayt" % len(cp))

    ozel = Ed25519PrivateKey.generate()
    acik = ozel.public_key()
    mesaj = b"komut: hedef=WP-7"
    imza = ozel.sign(mesaj)
    print("Ed25519 imza: %d bayt" % len(imza))
    acik.verify(imza, mesaj)
    print("imza dogrulandi")
    try:
        acik.verify(imza, b"komut: hedef=WP-8")
        print("degisen mesaj kabul (hata!)")
    except InvalidSignature:
        print("degisen mesaj: InvalidSignature (red)")


def test():
    hata = 0

    def dogru(ad, kosul):
        nonlocal hata
        print(("GECTI " if kosul else "KALDI ") + ad)
        if not kosul:
            hata += 1

    for ad, sinif, uzunluk in [("AES-GCM", AESGCM, 32),
                               ("ChaCha20", ChaCha20Poly1305, 32)]:
        k = os.urandom(uzunluk)          # 256 bit anahtar
        p = sifrele(sinif, k, b"merhaba", b"baslik")
        dogru(ad + " gidis-donus",
              coz(sinif, k, p, b"baslik") == b"merhaba")
        dogru(ad + " boyut = 12 + 7 + 16", len(p) == 35)
        b = bytearray(p)
        b[15] ^= 0x80
        try:
            coz(sinif, k, bytes(b), b"baslik")
            dogru(ad + " bozulma red", False)
        except InvalidTag:
            dogru(ad + " bozulma red", True)
        try:
            coz(sinif, k, p, b"baska")
            dogru(ad + " ek veri red", False)
        except InvalidTag:
            dogru(ad + " ek veri red", True)
        try:
            coz(sinif, os.urandom(32), p, b"baslik")
            dogru(ad + " yanlis anahtar red", False)
        except InvalidTag:
            dogru(ad + " yanlis anahtar red", True)

    ozel = Ed25519PrivateKey.generate()
    acik = ozel.public_key()
    imza = ozel.sign(b"abc")
    acik.verify(imza, b"abc")
    dogru("Ed25519 dogru mesaj", True)
    try:
        acik.verify(imza, b"abd")
        dogru("Ed25519 degisen mesaj red", False)
    except InvalidSignature:
        dogru("Ed25519 degisen mesaj red", True)
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
