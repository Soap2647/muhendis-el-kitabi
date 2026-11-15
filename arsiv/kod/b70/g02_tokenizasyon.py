# -*- coding: utf-8 -*-
"""
Bölüm 70 - Tokenizasyon ölçümleri: karakter, sözcük, OOV, BPE takası,
dil karşılaştırması ve bayt maliyeti. Çıktılar
engine/veri/b70_*.csv."""

import csv, os, re, time
from bpe_sifirdan import BPE

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
oku = lambda a: open(os.path.join(K, a), encoding="utf-8").read()
tr, te, en = (
    oku("korpus_egitim.txt"),
    oku("korpus_test.txt"),
    oku("korpus_en.txt"),
)
n_tr = 500000


def sozcukler(m):
    return re.findall(
        r"\w+", m.replace("İ", "i").replace("I", "ı").lower()
    )


def yaz(ad, basliklar, satirlar):
    with open(
        os.path.join(VERI, ad), "w", encoding="utf-8", newline=""
    ) as f:
        cw = csv.writer(f)
        cw.writerow(basliklar)
        cw.writerows(satirlar)


print(
    "== 1. Karakter ve sözcük istatistikleri (eşit boyut %d) =="
    % n_tr
)
for ad, m in [("Türkçe", tr[:n_tr]), ("İngilizce", en[:n_tr])]:
    w = sozcukler(m)
    print(
        "%-10s karakter=%d sözcük=%d tekil=%d alfabe=%d  "
        "bayt/karakter=%.4f"
        % (
            ad,
            len(m),
            len(w),
            len(set(w)),
            len(set(m)),
            len(m.encode("utf-8")) / len(m),
        )
    )

print(
    "\n== 2. Sözcük düzeyi: sözlük büyümesi ve OOV (sınama: "
    "test bölümleri) =="
)
w_tr, w_te = sozcukler(tr), sozcukler(te)
satirlar = []
for oran in [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]:
    alt = w_tr[: int(len(w_tr) * oran)]
    kume = set(alt)
    oov = sum(1 for x in w_te if x not in kume) / len(w_te)
    satirlar.append((oran, len(alt), len(kume), round(100 * oov, 3)))
    print(
        "eğitim %%%3d  sözcük=%7d  sözlük=%6d  OOV=%%%.2f"
        % (oran * 100, len(alt), len(kume), 100 * oov)
    )
yaz(
    "b70_sozluk_buyume.csv",
    ["oran", "sozcuk", "sozluk", "oov_yuzde"],
    satirlar,
)

print(
    "\n== 3. Alt-sözcük (BPE) takası: eğitim derlemi "
    "üzerinde öğrenildi =="
)
takas = []
for m in [0, 250, 500, 1000, 1500, 2000, 3000]:
    t0 = time.time()
    b = BPE(tr[:n_tr], m)
    sn = time.time() - t0
    ids = b.kodla(te)
    unk = sum(1 for i in ids if i == b.unk) / len(ids)
    # Geri dönüş: yalnızca alfabedeki karakterlerden oluşan metin
    alt = "".join(c for c in te if c in b.alfabe)
    ok = b.coz(b.kodla(alt)) == alt
    kt = len(te) / len(ids)
    takas.append(
        (m, b.boyut(), len(ids), round(kt, 4), round(100 * unk, 4))
    )
    print(
        "birleştirme=%4d sözlük=%5d token=%7d kar/token=%.3f "
        "unk=%%%.3f "
        "geri-dönüş=%s (%.1f sn)"
        % (m, b.boyut(), len(ids), kt, 100 * unk, ok, sn)
    )
yaz(
    "b70_bpe_takas.csv",
    ["birlestirme", "sozluk", "token", "kar_token", "unk_yuzde"],
    takas,
)

print(
    "\n== 4. Dil karşılaştırması: 300 bin karakterle "
    "eğitilmiş tokenizer =="
)
# Eğitim: TR için tr[:300k], EN için en[:300k]. Sınama: TR için te,
# EN için en[300k:] (eğitimde kullanılmayan parça).
bt = BPE(tr[:300000], 1000)
be = BPE(en[:300000], 1000)
satirlar = []
for ad, b, metin in [
    ("TR tok. / TR metin", bt, te),
    ("EN tok. / EN metin", be, en[300000:]),
    ("EN tok. / TR metin", be, te),
    ("TR tok. / EN metin", bt, en[300000:]),
]:
    ids = b.kodla(metin)
    unk = sum(1 for i in ids if i == b.unk) / len(ids)
    kt = len(metin) / len(ids)
    tks = len(ids) / len(sozcukler(metin))
    satirlar.append(
        (
            ad,
            b.boyut(),
            round(kt, 4),
            round(tks, 4),
            round(100 * unk, 4),
        )
    )
    print(
        "%-20s sözlük=%5d kar/token=%.3f token/sözcük=%.3f unk=%%%.3f"
        % (ad, b.boyut(), kt, tks, 100 * unk)
    )
yaz(
    "b70_dil_takas.csv",
    [
        "tokenizer_metin",
        "sozluk",
        "kar_token",
        "token_sozcuk",
        "unk_yuzde",
    ],
    satirlar,
)

print(
    "\n== 5. Bayt düzeyi (UTF-8): Türkçe karakterlerin bayt "
    "maliyeti =="
)
for c in "aığüşöçıİ":
    print(
        "%s U+%04X -> %d bayt" % (c, ord(c), len(c.encode("utf-8")))
    )
