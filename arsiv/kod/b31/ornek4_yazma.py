# -*- coding: utf-8 -*-
"""Ornek 4: kismi yazma ve EPOLLOUT maskesi (sahte soket)."""
from b31_modeller import Baglanti, _yaz


class YavasSoket:
    def __init__(self):
        self.kapasite = 0                 # alicinin bos yeri (bayt)
        self.alinan = bytearray()

    def send(self, veri):
        if self.kapasite == 0:
            raise BlockingIOError()       # EAGAIN karsiligi
        k = min(self.kapasite, len(veri))
        self.alinan += veri[:k]
        self.kapasite -= k
        return k


def maske(b):
    return "EPOLLIN|EPOLLOUT" if b.giden else "EPOLLIN"


s = YavasSoket()
b = Baglanti(s)
b.giden += b"0123456789AB"
for ad, kap in [("1. yazma, 6 bayt yer", 6),
                ("2. yazma, yer yok", 0),
                ("3. alici bosaldi, 6 bayt", 6)]:
    s.kapasite = kap
    _yaz(b)
    print("%s: giden=%d maske=%s alinan=%r"
          % (ad, len(b.giden), maske(b), bytes(s.alinan)))
