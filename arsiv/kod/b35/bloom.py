# -*- coding: utf-8 -*-
"""Bloom filtresi: m bit, k hash fonksiyonu (Bölüm 35.6)."""
import hashlib
import math


class BloomFilter:
    def __init__(self, m, k):
        self.m = m
        self.k = k
        self.bitler = bytearray((m + 7) // 8)

    def _konumlar(self, anahtar):
        # Tek bir 128 bitlik özetten iki hash üret (çift hash):
        # h_i = (h1 + i * h2) mod m. Kirsch-Mitzenmacher tekniği.
        ozet = hashlib.blake2b(anahtar.encode("utf-8"),
                               digest_size=16).digest()
        h1 = int.from_bytes(ozet[:8], "little")
        h2 = int.from_bytes(ozet[8:], "little") | 1
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def ekle(self, anahtar):
        for p in self._konumlar(anahtar):
            self.bitler[p >> 3] |= 1 << (p & 7)

    def icerir(self, anahtar):
        # False: kesinlikle yok. True: muhtemelen var.
        for p in self._konumlar(anahtar):
            if not (self.bitler[p >> 3] >> (p & 7)) & 1:
                return False
        return True


def teorik_yanlis_pozitif(m, n, k):
    return (1.0 - math.exp(-k * n / m)) ** k


def optimal_k(m, n):
    return max(1, round((m / n) * math.log(2)))
