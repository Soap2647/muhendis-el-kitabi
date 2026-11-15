# -*- coding: utf-8 -*-
"""Bolum 71 ortak yardimcilari: korpus, parcalama, belirteclestirme,
BM25."""

import glob
import math
import os
import re
from collections import Counter

KOK = "D:/Mevcut Projeler/Kitap"
BOLUM = os.path.join(KOK, "bolumler")
VERI = os.path.join(KOK, "engine", "veri")
# Bolum 70 ve sonrasi yazilirken degisebilir; tekrarlanabilirlik icin
# korpus 1..69 ile sinirli tutulur.
SON_BOLUM = 69


def kitap_dosyalari():
    dosyalar = []
    for yol in sorted(glob.glob(os.path.join(BOLUM, "bolum_*.md"))):
        n = int(re.search(r"bolum_(\d+)", yol).group(1))
        if n <= SON_BOLUM:
            dosyalar.append((n, yol))
    return dosyalar


def duz_metin(satirlar):
    """Kod bloklarini ve ::: kutu isaretlerini atar, markdown
    isaretlerini siler."""
    cikti, kod = [], False
    for s in satirlar:
        if s.startswith("```"):
            kod = not kod
            continue
        if (
            kod
            or s.startswith(":::")
            or s.startswith("![")
            or s.startswith("%%")
        ):
            continue
        if s.startswith("|"):
            continue
        s = re.sub(r"`([^`]*)`", r"\1", s)
        s = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", s)
        s = re.sub(r"^#+\s*", "", s)
        s = re.sub(r"^\s*(\d+\.|-)\s+", "", s)
        cikti.append(s.strip())
    return [s for s in cikti if s]


def bolumleri_oku():
    """Dondurur: [(bolum_no, baslik, [(bolum_basligi, paragraf),
    ...])]."""
    sonuc = []
    for n, yol in kitap_dosyalari():
        with open(yol, encoding="utf-8") as f:
            satirlar = f.read().split("\n")
        bolum_baslik = ""
        bloklar = []
        kod = False
        tampon = []
        for s in satirlar:
            if s.startswith("```"):
                kod = not kod
                continue
            if kod:
                continue
            if s.startswith("## ") or s.startswith("### "):
                if tampon:
                    bloklar.append((bolum_baslik, " ".join(tampon)))
                    tampon = []
                bolum_baslik = re.sub(r"^#+\s*", "", s).strip()
                continue
            if not s.strip():
                if tampon:
                    bloklar.append((bolum_baslik, " ".join(tampon)))
                    tampon = []
                continue
            if s.startswith(("%%", "![", ":::", "|")):
                continue
            tampon.append(s.strip())
        if tampon:
            bloklar.append((bolum_baslik, " ".join(tampon)))
        temiz = []
        for b, p in bloklar:
            p = re.sub(r"`([^`]*)`", r"\1", p)
            p = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", p)
            if len(p) > 20:
                temiz.append((b, p))
        sonuc.append((n, temiz))
    return sonuc


def dk_notu(metin):
    """Kucuk harf, Turkce uyumlu: I->i degil, I->ı ve İ->i."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


def belirtecler(metin, on_ek=None):
    """Harf/rakam dizileri. on_ek verilirse her belirtec o uzunlukla
    kesilir
    (Turkce icin basit bir kok yaklasimi: ilk 5 harf)."""
    ham = re.findall(r"[a-zçğıöşü0-9]+", dk_notu(metin))
    if on_ek:
        ham = [t[:on_ek] for t in ham]
    return ham


def bm25_indeks(belgeler, k1=1.5, b=0.75):
    """Belgeler: belirtec listeleri.

    Sozluk: terim -> [(belge, tf)]."""
    N = len(belgeler)
    uzunluk = [len(d) for d in belgeler]
    ort = sum(uzunluk) / N
    ters = {}
    for i, d in enumerate(belgeler):
        for t, c in Counter(d).items():
            ters.setdefault(t, []).append((i, c))
    idf = {}
    for t, liste in ters.items():
        n_t = len(liste)
        idf[t] = math.log((N - n_t + 0.5) / (n_t + 0.5) + 1.0)
    return {
        "ters": ters,
        "idf": idf,
        "uzunluk": uzunluk,
        "ort": ort,
        "k1": k1,
        "b": b,
        "N": N,
    }


def bm25_skor(indeks, sorgu_belirtecleri):
    """Her belge icin BM25 skoru (sorgudaki tekrarlar sayilir)."""
    skor = [0.0] * indeks["N"]
    k1, b, ort = indeks["k1"], indeks["b"], indeks["ort"]
    for t in sorgu_belirtecleri:
        if t not in indeks["ters"]:
            continue
        idf = indeks["idf"][t]
        for i, tf in indeks["ters"][t]:
            payda = tf + k1 * (1 - b + b * indeks["uzunluk"][i] / ort)
            skor[i] += idf * tf * (k1 + 1) / payda
    return skor
