# -*- coding: utf-8 -*-
"""Ornek 1: parcali akis icinde cerceve okuma izi."""
from b31_cerceve import ParcaliSoket, cerceve_al


class IzliSoket(ParcaliSoket):
    def recv(self, n):
        b = super().recv(n)
        print("  recv(%d) -> %r" % (n, b))
        return b


parcalar = [b"\x00\x00", b"\x00\x05he", b"l", b"lo\x00\x00\x00",
            b"\x02w", b"o"]
s = IzliSoket(parcalar)
for no in (1, 2):
    print("cerceve %d:" % no)
    print("  yuk = %r" % cerceve_al(s))
