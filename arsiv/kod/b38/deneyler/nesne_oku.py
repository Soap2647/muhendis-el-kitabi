# -*- coding: utf-8 -*-
"""Bir git nesnesini .git/objects'ten okuyup çözer."""
import os
import sys
import zlib


def nesneyi_oku(depo, hash_):
    # İlk iki hane dizin, kalanı dosya adıdır.
    yol = os.path.join(depo, ".git", "objects", hash_[:2], hash_[2:])
    with open(yol, "rb") as f:
        ham = zlib.decompress(f.read())
    bas = ham.index(b"\x00")          # başlık "tür boyut" + NUL
    tur, boyut = ham[:bas].split(b" ")
    govde = ham[bas + 1:]
    assert int(boyut) == len(govde), "boyut tutmuyor"
    return tur.decode(), govde


def agaci_listele(govde):
    # Ağaç: "<mod> <ad>\0<20 bayt ham hash>" tekrarları
    i = 0
    while i < len(govde):
        bosluk = govde.index(b" ", i)
        nul = govde.index(b"\x00", bosluk)
        mod = govde[i:bosluk].decode()
        ad = govde[bosluk + 1:nul].decode()
        ham = govde[nul + 1:nul + 21]
        print(mod, ad, ham.hex())
        i = nul + 21


if __name__ == "__main__":
    depo, hash_ = sys.argv[1], sys.argv[2]
    tur, govde = nesneyi_oku(depo, hash_)
    print("tür:", tur, "boyut:", len(govde))
    if tur == "tree":
        agaci_listele(govde)
    else:
        print(govde.decode("utf-8"), end="")
