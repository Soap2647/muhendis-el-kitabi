# -*- coding: utf-8 -*-
"""Bölüm 70 - Bayt çifti kodlaması (BPE), sıfırdan.

Yalnızca standart kütüphane kullanır. Birleştirme kuralları metinden
öğrenilir; kodlama, öğrenilen kuralları sırayla uygular; çözme, sembol
dizilerini yeniden birleştirir. Ön işleme (pretokenization) metni
kelime ve noktalama parçalarına böler; her parçanın başındaki boşluk
parçanın bir parçası olarak tutulur, böylece kodla-çöz tam olarak
orijinal metni verir.
"""

import re
from collections import Counter, defaultdict

DESEN = re.compile(r" ?\w+| ?[^\w\s]+|\s+")


def on_isle(metin):
    return DESEN.findall(metin)


def egit(metin, birlestirme):
    """En sık çifti tekrar tekrar birleştirerek kuralları öğrenir."""
    frekans = Counter(on_isle(metin))
    parca = {
        w: list(w) for w in frekans
    }  # her kelime bir sembol listesi
    cift = Counter()  # çift -> toplam frekans
    konum = defaultdict(set)  # çift -> o çifti içeren kelimeler
    for w, f in frekans.items():
        s = parca[w]
        for a, b in zip(s, s[1:]):
            cift[(a, b)] += f
            konum[(a, b)].add(w)
    kurallar = []
    for _ in range(birlestirme):
        if not cift:
            break
        # Eşitlikte sözlük sırası: sonuç her çalıştırmada aynı olsun.
        en = max(cift, key=lambda p: (cift[p], p))
        if cift[en] <= 0:
            break
        kurallar.append(en)
        yeni = en[0] + en[1]
        for w in list(konum[en]):
            f, s = frekans[w], parca[w]
            for a, b in zip(s, s[1:]):  # eski çiftleri düş
                cift[(a, b)] -= f
            t, i = [], 0
            while i < len(s):  # soldan sağa birleştir
                if i + 1 < len(s) and (s[i], s[i + 1]) == en:
                    t.append(yeni)
                    i += 2
                else:
                    t.append(s[i])
                    i += 1
            parca[w] = t
            for a, b in zip(t, t[1:]):  # yeni çiftleri ekle
                cift[(a, b)] += f
                konum[(a, b)].add(w)
    return kurallar


class BPE:
    """Öğrenilmiş kurallarla kodlayan ve çözen tokenizer."""

    def __init__(self, metin, birlestirme):
        self.alfabe = sorted(set(metin))
        self.kurallar = egit(metin, birlestirme)
        self._kur()

    @classmethod
    def yukle(cls, alfabe, kurallar):
        """
        Kaydedilmiş alfabe ve kurallardan tokenizer'ı yeniden kurar.
        """
        b = cls.__new__(cls)
        b.alfabe = list(alfabe)
        b.kurallar = [tuple(p) for p in kurallar]
        b._kur()
        return b

    def _kur(self):
        self.sozluk = {}
        for c in self.alfabe:
            self.sozluk.setdefault(c, len(self.sozluk))
        for a, b in self.kurallar:
            self.sozluk.setdefault(a + b, len(self.sozluk))
        self.ters = {i: s for s, i in self.sozluk.items()}
        self.sira = {p: i for i, p in enumerate(self.kurallar)}
        self.unk = len(self.sozluk)  # alfabe dışı karakter için
        self.onbellek = {}

    def boyut(self):
        return len(self.sozluk) + 1

    def _parcala(self, w):
        if w in self.onbellek:
            return self.onbellek[w]
        s = list(w)
        while len(s) > 1:
            aday = [
                (self.sira[(a, b)], i)
                for i, (a, b) in enumerate(zip(s, s[1:]))
                if (a, b) in self.sira
            ]
            if not aday:
                break
            _, i = min(aday)  # en erken öğrenilen kural
            s[i : i + 2] = [s[i] + s[i + 1]]
        self.onbellek[w] = s
        return s

    def kodla(self, metin):
        ids = []
        for w in on_isle(metin):
            for sembol in self._parcala(w):
                ids.append(self.sozluk.get(sembol, self.unk))
        return ids

    def coz(self, ids):
        return "".join(self.ters.get(i, "") for i in ids)
