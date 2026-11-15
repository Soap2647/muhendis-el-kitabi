# -*- coding: utf-8 -*-
"""Bölüm 41.7 - Önbellek damgası (stampede) ve tekil uçuş.

Senaryo: önbellekte anahtar yok (ya da TTL doldu). 1000 iş parçacığı
aynı anda aynı anahtarı ister. Kaynak (veritabanı) 0,2 s sürer.
Naif: her iş parçacığı kaynağa gider. Tekil uçuş: bir anahtar için
yalnızca bir istek kaynağa gider, diğerleri onu bekler (istek
birleştirme).
"""

import threading
import time


class Onbellek:
    def __init__(self):
        self.veri = {}
        self.kilit = threading.Lock()
        self.kaynak_cagrisi = 0
        self.sayac_kilit = threading.Lock()

    def kaynaktan_oku(self, anahtar):
        with self.sayac_kilit:
            self.kaynak_cagrisi += 1
        time.sleep(0.2)  # yavaş veritabanı (simülasyon)
        return "deger-" + anahtar

    def naif(self, anahtar):
        if anahtar in self.veri:
            return self.veri[anahtar]
        d = self.kaynaktan_oku(anahtar)
        self.veri[anahtar] = d
        return d


#@@
class TekilUcus(Onbellek):
    def __init__(self):
        super().__init__()
        self.uclar = {}  # anahtar -> Event (uçuştaki istek)

    def al(self, anahtar):
        if anahtar in self.veri:
            return self.veri[anahtar]
        with self.kilit:
            if anahtar in self.veri:
                return self.veri[anahtar]
            olay = self.uclar.get(anahtar)
            benim = olay is None
            if benim:
                olay = threading.Event()
                self.uclar[anahtar] = olay
        if not benim:
            olay.wait()  # başkası getiriyor, bekle
            return self.veri[anahtar]
        try:
            d = self.kaynaktan_oku(anahtar)
            self.veri[anahtar] = d
        finally:
            with self.kilit:
                del self.uclar[anahtar]
            olay.set()
        return d


#@@
def kos(sinif, metot, n=1000):
    o = sinif()
    bariyer = threading.Barrier(n)
    sonuc = [None] * n

    def is_parcacigi(k):
        bariyer.wait()  # hepsi aynı anda başlasın
        f = getattr(o, metot)
        sonuc[k] = f("urun-42")

    thr = [
        threading.Thread(target=is_parcacigi, args=(k,))
        for k in range(n)
    ]
    for t in thr:
        t.start()
    for t in thr:
        t.join()
    return o.kaynak_cagrisi, len(set(sonuc))


#@@
if __name__ == "__main__":
    c1, d1 = kos(Onbellek, "naif")
    print(
        "naif          : kaynak çağrısı = %d, farklı yanıt = %d"
        % (c1, d1)
    )
    c2, d2 = kos(TekilUcus, "al")
    print(
        "tekil uçuş    : kaynak çağrısı = %d, farklı yanıt = %d"
        % (c2, d2)
    )
