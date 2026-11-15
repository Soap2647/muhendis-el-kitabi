# aritmetik.py: tamsayı aritmetik kodlayıcı
# (Witten, Neal, Cleary 1987).
# Olasılıklar tamsayı frekanslarla verilir. Toplam 2^30'u geçmemeli.
import random

BITS = 32
TOP = (1 << BITS) - 1
CEYREK = 1 << (BITS - 2)        # First
YARIM = 2 * CEYREK              # Half
UCTE = 3 * CEYREK               # Third

def kumulatif(frek):
    kum = [0]
    for f in frek:
        kum.append(kum[-1] + f)
    return kum

class Kodlayici:
    def __init__(self, frek):
        self.kum = kumulatif(frek)
        self.toplam = self.kum[-1]
        self.bits = []
        self.bekleyen = 0           # ters bit beklentisi (underflow)

    def _yaz(self, b):
        self.bits.append(b)
        self.bits.extend([1 - b] * self.bekleyen)
        self.bekleyen = 0

    def kodla(self, mesaj):
        low, high = 0, TOP
        for s in mesaj:
            aralik = high - low + 1
            high = low + aralik * self.kum[s + 1] // self.toplam - 1
            low = low + aralik * self.kum[s] // self.toplam
            while True:
                if high < YARIM:
                    self._yaz(0)
                elif low >= YARIM:
                    self._yaz(1)
                    low -= YARIM
                    high -= YARIM
                elif low >= CEYREK and high < UCTE:
                    self.bekleyen += 1
                    low -= CEYREK
                    high -= CEYREK
                else:
                    break
                low = 2 * low
                high = 2 * high + 1
        self.bekleyen += 1
        self._yaz(0 if low < CEYREK else 1)
        return self.bits

class Dekodlayici:
    def __init__(self, frek, bits):
        self.kum = kumulatif(frek)
        self.toplam = self.kum[-1]
        self.bits = bits
        self.konum = 0
        self.deger = 0
        for _ in range(BITS):
            self.deger = 2 * self.deger + self._oku()

    def _oku(self):
        # Bit dizisi bittiğinde 0 okunur (kodlayıcı sonunu kapatır).
        var = self.konum < len(self.bits)
        b = self.bits[self.konum] if var else 0
        self.konum += 1
        return b

    def coz(self, n):
        low, high = 0, TOP
        cikti = []
        for _ in range(n):
            aralik = high - low + 1
            c = ((self.deger - low + 1) * self.toplam - 1) // aralik
            s = 0
            while self.kum[s + 1] <= c:
                s += 1
            cikti.append(s)
            high = low + aralik * self.kum[s + 1] // self.toplam - 1
            low = low + aralik * self.kum[s] // self.toplam
            while True:
                if high < YARIM:
                    pass
                elif low >= YARIM:
                    self.deger -= YARIM
                    low -= YARIM
                    high -= YARIM
                elif low >= CEYREK and high < UCTE:
                    self.deger -= CEYREK
                    low -= CEYREK
                    high -= CEYREK
                else:
                    break
                low = 2 * low
                high = 2 * high + 1
                self.deger = 2 * self.deger + self._oku()
        return cikti

def sına():
    rnd = random.Random(51)
    tamam = 0
    for frek in ([90, 5, 5], [1, 1, 1, 1], [7, 3, 1, 9, 2]):
        for n in (0, 1, 2, 50, 2000):
            mesaj = [rnd.choices(range(len(frek)), weights=frek)[0]
                     for _ in range(n)]
            bits = Kodlayici(frek).kodla(mesaj)
            geri = Dekodlayici(frek, bits).coz(n)
            assert geri == mesaj, (frek, n)
            tamam += 1
    # Tek simge tekrarı (ortalama uzunluk 0'a yakın olmalı)
    mesaj = [0] * 5000
    bits = Kodlayici([999, 1]).kodla(mesaj)
    assert Dekodlayici([999, 1], bits).coz(5000) == mesaj
    print("gidis-donus denemesi: %d/%d tamam" % (tamam, tamam))
    print("5000 'a' simgesi: %d bit" % len(bits))

def main():
    sına()
    # Çarpık kaynak: entropi 0.569 bit, Huffman en az 1 bit
    frek = [900, 50, 50]
    rnd = random.Random(51)
    mesaj = [rnd.choices([0, 1, 2], weights=frek)[0]
             for _ in range(20000)]
    bits = Kodlayici(frek).kodla(mesaj)
    print("bit/simge: %.4f" % (len(bits) / len(mesaj)))

if __name__ == "__main__":
    main()
