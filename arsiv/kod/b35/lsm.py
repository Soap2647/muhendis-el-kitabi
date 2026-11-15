# -*- coding: utf-8 -*-
"""Küçük LSM anahtar-değer deposu (Bölüm 35.4).

memtable (RAM, dict) -> flush -> SSTable (diskte sıralı dosya)
SSTable: bloklara bölünmüş, bellekte seyrek indeks + Bloom filtresi.
Silme: mezar taşı (değeri None olan kayıt). Birleştirme: tüm
tabloları tek tabloda toplar, en yeni kayıt kazanır, mezar taşları
(tüm tablolar birleştiğinde artık gizleyecek eski kayıt yoktur)
atılır.
WAL bu sürümde yok; Kendin Yap Projesi 1'de eklenecek.
"""
import bisect
import json
import os

from bloom import BloomFilter


class SSTable:
    BLOK = 16  # blok başına kayıt sayısı

    def __init__(self, yol, kayitlar, m, k, say):
        # kayitlar: anahtara göre sıralı [(anahtar, deger)]
        self.yol = yol
        self.bloom = BloomFilter(m, k)
        self.seyrek = []  # her blok için (ilk_anahtar, bas, son)
        bas = 0
        with open(yol, "wb") as f:
            for i, (anahtar, deger) in enumerate(kayitlar):
                if i % self.BLOK == 0:
                    if self.seyrek:
                        self.seyrek[-1][2] = f.tell()
                    self.seyrek.append([anahtar, f.tell(), None])
                f.write(json.dumps([anahtar, deger]).encode() + b"\n")
                self.bloom.ekle(anahtar)
            if self.seyrek:
                self.seyrek[-1][2] = f.tell()
        self.bayt = os.path.getsize(yol)
        self.ilk = [b[0] for b in self.seyrek]
        say["disk_yazma"] += self.bayt

    def oku(self, anahtar, bloom_kullan, say):
        # Dönüş: None (tabloda yok) ya da (True, deger)
        if bloom_kullan and not self.bloom.icerir(anahtar):
            say["bloom_red"] += 1
            return None
        i = bisect.bisect_right(self.ilk, anahtar) - 1
        if i < 0:
            return None
        _, bas, son = self.seyrek[i]
        say["sorgu_disk_okuma"] += 1
        with open(self.yol, "rb") as f:
            f.seek(bas)
            veri = f.read(son - bas)
        for satir in veri.splitlines():
            k, v = json.loads(satir.decode())
            if k == anahtar:
                return (True, v)
        say["bloom_yanlis"] += 1  # filtre "var" dedi, yoktu
        return None

    def tum_kayitlar(self, say):
        say["birlestirme_okuma"] += self.bayt
        kayitlar = []
        with open(self.yol, "rb") as f:
            for satir in f.read().splitlines():
                k, v = json.loads(satir.decode())
                kayitlar.append((k, v))
        return kayitlar


class LSM:
    def __init__(self, dizin, esik=64, m=4096, k=4,
                 bloom_kullan=True):
        self.dizin = dizin
        os.makedirs(dizin, exist_ok=True)
        self.memtable = {}
        self.esik = esik
        self.m, self.k = m, k
        self.bloom_kullan = bloom_kullan
        self.tablolar = []  # eskiden yeniye sıralı
        self.sira = 0
        self.say = {"kullanici": 0, "disk_yazma": 0,
                    "sorgu_disk_okuma": 0,
                    "bloom_red": 0, "bloom_yanlis": 0,
                    "birlestirme_okuma": 0}

    def put(self, anahtar, deger):
        self.say["kullanici"] += len(anahtar) + len(deger)
        self.memtable[anahtar] = deger
        self._kontrol()

    def sil(self, anahtar):
        self.say["kullanici"] += len(anahtar)
        self.memtable[anahtar] = None  # mezar taşı
        self._kontrol()

    def get(self, anahtar):
        if anahtar in self.memtable:
            return self.memtable[anahtar]
        for t in reversed(self.tablolar):  # en yeni tablo önce
            r = t.oku(anahtar, self.bloom_kullan, self.say)
            if r is not None:
                return r[1]
        return None

    def _kontrol(self):
        if len(self.memtable) >= self.esik:
            self.flush()

    def _yeni_tablo(self, kayitlar):
        yol = os.path.join(self.dizin, "%06d.sst" % self.sira)
        self.sira += 1
        return SSTable(yol, kayitlar, self.m, self.k, self.say)

    def flush(self):
        if not self.memtable:
            return
        kayitlar = sorted(self.memtable.items())
        self.tablolar.append(self._yeni_tablo(kayitlar))
        self.memtable = {}

    def birlestir(self):
        self.flush()
        if len(self.tablolar) <= 1:
            return
        birlesik = {}
        for t in self.tablolar:  # eskiden yeniye: yeni olan kazanır
            for k, v in t.tum_kayitlar(self.say):
                birlesik[k] = v
        kayitlar = [(k, v) for k, v in sorted(birlesik.items())
                    if v is not None]
        for t in self.tablolar:
            os.remove(t.yol)
        self.tablolar = []
        if kayitlar:
            self.tablolar.append(self._yeni_tablo(kayitlar))

    def tablo_sayisi(self):
        return len(self.tablolar)
