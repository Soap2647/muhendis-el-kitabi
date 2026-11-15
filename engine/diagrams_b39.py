# -*- coding: utf-8 -*-
"""Bolum 39 - 'Test Yazma' diyagramlari.

Olcum sekli engine/veri/b39_mutasyon.csv dosyasini okur (mutasyon
testi skorlari: zayif, orta, guclu_v1, guclu_v2). Diger sekiller
bolumdeki ornek degerlerden cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b39_%s.png" % ad)


def _tuval(w, h, xl=14, yl=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. Test piramidi ve test kupasi ------------------------------------- #
def piramit():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=8)
    ax.text(3.4, 7.55, "Test piramidi (önerilen)", ha="center",
            fontsize=10.5, weight="bold", color=INK)
    ax.text(10.6, 7.55, "Test kupası (kaçınılacak)", ha="center",
            fontsize=10.5, weight="bold", color=INK)
    # piramit: dar ust, genis taban
    _box(ax, 2.7, 6.2, 1.4, 0.8, "Uçtan uca", FILL[3], EDGE[3], fs=8.5)
    _box(ax, 2.0, 4.7, 2.8, 0.8, "Entegrasyon", FILL[2], EDGE[2], fs=9)
    _box(ax, 0.6, 2.8, 5.6, 1.1, "Birim testleri (çoğu)", FILL[1],
         EDGE[1], fs=9.5, bold=True)
    ax.text(3.4, 1.9, "hızlı, ucuz, çok", ha="center", fontsize=8.5,
            color=MUTED)
    # kupa: genis ust, dar taban
    _box(ax, 8.4, 6.2, 4.4, 0.8, "El ile uçtan uca (çok)", FILL[3],
         EDGE[3], fs=8.5)
    _box(ax, 9.0, 4.7, 3.2, 0.8, "Az entegrasyon", FILL[2], EDGE[2],
         fs=9)
    _box(ax, 9.9, 2.8, 1.4, 1.1, "Birim\n(az)", FILL[1], EDGE[1],
         fs=9)
    ax.text(10.6, 1.9, "yavaş, kırılgan", ha="center", fontsize=8.5,
            color=MUTED)
    return _save(fig, _yol("piramit"))


# 2. AAA yapisi -------------------------------------------------------- #
def aaa():
    fig, ax = _tuval(9.6, 3.8, xl=14, yl=6.2)
    etiketler = [("Düzenle (Arrange)", "girdiyi ve nesneleri kur"),
                 ("Eylem (Act)", "tek bir işlemi çağır"),
                 ("Doğrula (Assert)", "beklenen sonucu sına")]
    for i, (baslik, alt) in enumerate(etiketler):
        x = 0.4 + i * 4.6
        _box(ax, x, 3.2, 4.0, 1.5, baslik, FILL[i], EDGE[i], fs=10,
             bold=True)
        ax.text(x + 2.0, 2.75, alt, ha="center", fontsize=8.8,
                color=MUTED)
        if i < 2:
            _arrow(ax, x + 4.0, 3.95, x + 4.6, 3.95, col=MUTED, lw=1.3)
    ax.text(7.0, 1.6, "tek davranış = tek Eylem; Doğrula birden çok olabilir",
            ha="center", fontsize=9, color=INK)
    ax.text(7.0, 0.7, "ad: ne_olur_nerede_ne_beklenir (ör. "
            "test_stok_yetersizse_hata_verir)", ha="center",
            fontsize=8.5, color=MUTED)
    return _save(fig, _yol("aaa"))


# 3. Test ikizleri ----------------------------------------------------- #
def ikizler():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=9.2)
    basliklar = ["Tür", "Ne yapar?", "Neyi doğrular?"]
    xs = [0.3, 3.2, 8.5]
    gen = [2.7, 5.0, 5.2]
    for x, g, b in zip(xs, gen, basliklar):
        ax.text(x + g / 2, 8.6, b, ha="center", fontsize=9.5,
                weight="bold", color=INK)
    satirlar = [
        ("Dummy", "sadece doldurulur, kullanılmaz", "hiçbir şey"),
        ("Stub", "önceden hazır yanıt döner", "çıktının kendisi"),
        ("Spy", "gerçek ya da sahte, çağrıları kaydeder",
         "çağrı var mı, ne ile"),
        ("Mock", "beklentiyi önceden kurar", "çağrı beklentisi"),
        ("Fake", "çalışan hafif gerçeklik (bellek deposu)",
         "durum ve davranış"),
    ]
    for i, (ad, ne, neyi) in enumerate(satirlar):
        y = 7.3 - i * 1.45
        f = FILL[i % 5]
        e = EDGE[i % 5]
        _box(ax, xs[0], y, gen[0], 1.05, ad, f, e, fs=10, bold=True)
        _box(ax, xs[1], y, gen[1], 1.05, ne, f, e, fs=8.6)
        _box(ax, xs[2], y, 5.3, 1.05, neyi, f, e, fs=8.6)
    ax.text(7.0, 0.3, "Fake ve Stub çoğu zaman durumu doğrular; Mock "
            "fazla kullanılırsa uygulamaya bağlanır.",
            ha="center", fontsize=8.5, color=MUTED)
    return _save(fig, _yol("ikizler"))


# 4. Kapsama: CFG uzerinde satir vs dal --------------------------------- #
def kapsama():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=9.0)
    _box(ax, 0.4, 7.5, 4.0, 0.9, 's = "sifir"', FILL[0], EDGE[0],
         fs=9.5)
    _box(ax, 0.4, 5.6, 4.0, 1.2,
         "if x is not None\n and x > 0:", FILL[2], EDGE[2], fs=9)
    _box(ax, 0.4, 3.5, 4.0, 0.9, 's = "pozitif"', FILL[1], EDGE[1],
         fs=9.5)
    _box(ax, 0.4, 1.4, 4.0, 0.9, "return s", FILL[0], EDGE[0], fs=9.5)
    _arrow(ax, 2.4, 7.5, 2.4, 6.8, col=MUTED, lw=1.2)
    _arrow(ax, 2.4, 5.6, 2.4, 4.4, col=EDGE[1], lw=2.2)
    _arrow(ax, 2.4, 3.5, 2.4, 2.3, col=MUTED, lw=1.2)
    # eksik dal: if kutusunun sagindan, kenarlarin disindan return'e
    ax.plot([4.4, 5.0, 5.0], [6.2, 6.2, 1.85], color=ACCENT, lw=1.6)
    _arrow(ax, 5.0, 1.85, 4.4, 1.85, col=ACCENT, lw=1.6)
    ax.text(5.2, 3.7, "False dalı\n(3->5)\nçalışmadı", fontsize=8.6,
            color=ACCENT, va="center")
    ax.text(2.6, 4.9, "True (5 ile test edildi)", fontsize=8.4,
            color=EDGE[1], va="center")
    # sag taraf: sonuc tablosu
    _box(ax, 7.6, 5.4, 6.0, 2.8,
         "Satır kapsamı: 9/9 (%100)\n"
         "Dal yönü: 4'ün 3'ü (%75)\n\n"
         "Birleşik ölçü (raporda): %92\n(12 / 13 = satır + dal yönü)",
         FILL[1], EDGE[1], fs=9.8)
    ax.text(7.6, 4.6, "İki ölçü de aynı kodu ölçer; yalnızca dal ölçüsü\n"
            "'if' kararının iki yolunu da sınar.", fontsize=8.6,
            color=MUTED, va="top")
    ax.text(7.6, 2.4, "Not: Python'da 'and' kısa devre yaptığı için\n"
            "alt koşulların her biri ayrıca ölçülmez (MC/DC, 39.12).",
            fontsize=8.4, color=MUTED, va="top")
    return _save(fig, _yol("kapsama"))


# 5. Mutasyon dongusu -------------------------------------------------- #
def mutasyon_dongusu():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=9)
    _box(ax, 0.4, 6.4, 3.4, 1.2, "Kaynak kod\n(tarih.py)", FILL[0],
         EDGE[0], fs=9.5, bold=True)
    _box(ax, 5.3, 6.4, 3.6, 1.2, "Mutant üret\n(tek küçük değişiklik)",
         FILL[2], EDGE[2], fs=9.2)
    _box(ax, 10.3, 6.4, 3.3, 1.2, "Test paketini\nçalıştır", FILL[1],
         EDGE[1], fs=9.2)
    _arrow(ax, 3.8, 7.0, 5.3, 7.0, col=MUTED)
    _arrow(ax, 8.9, 7.0, 10.3, 7.0, col=MUTED)
    _box(ax, 10.3, 3.2, 3.3, 1.4, "Bir test\nbaşarısız mı?", FILL[4],
         EDGE[4], fs=9.2)
    _arrow(ax, 11.95, 6.4, 11.95, 4.6, col=MUTED)
    _box(ax, 5.3, 3.2, 3.6, 1.4, "EVET: mutant öldü\n(paket yakaladı)",
         FILL[1], EDGE[1], fs=9.2)
    _box(ax, 0.4, 3.2, 3.4, 1.4, "HAYIR: mutant hayatta\n(boşluk var)",
         FILL[3], EDGE[3], fs=9.2)
    _arrow(ax, 10.3, 3.9, 8.9, 3.9, col=MUTED)
    _arrow(ax, 5.3, 3.9, 3.8, 3.9, col=MUTED)
    _box(ax, 0.4, 0.4, 13.2, 1.8,
         "Skor = öldürülen mutant / toplam mutant. Hayatta kalan her "
         "mutant için\nya yeni bir test yaz ya da mutantın eşdeğer "
         "(davranışı değiştirmeyen) olduğunu kanıtla.",
         FILL[0], EDGE[0], fs=9.2)
    _arrow(ax, 1.9, 3.2, 1.9, 2.4, col=MUTED)
    return _save(fig, _yol("mutasyon_dongu"))


# 6. Mutasyon skoru grafigi (CSV) -------------------------------------- #
def mutasyon_skor():
    with open(os.path.join(VERI, "b39_mutasyon.csv"),
              encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    adlar = {"zayif": "Zayıf\n(3 test)",
             "orta": "Orta\n(sınır değerler)",
             "guclu_v1": "Güçlü v1\n(gün 32 yok)",
             "guclu_v2": "Güçlü v2\n(düzeltilmiş)"}
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    x = list(range(len(satirlar)))
    skor = [float(s["skor_yuzde"]) for s in satirlar]
    renk = [FILL[0], FILL[2], FILL[3], FILL[1]]
    kenar = [EDGE[0], EDGE[2], EDGE[3], EDGE[1]]
    ax.bar(x, skor, color=renk, edgecolor=kenar, linewidth=1.2,
           width=0.6)
    for xi, s, sat in zip(x, skor, satirlar):
        ax.text(xi, s + 2, "%.1f%%\n(%s/%s)" % (
            s, sat["oldurulen"], sat["mutant"]),
            ha="center", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([adlar[s["paket"]] for s in satirlar], fontsize=9)
    ax.set_ylim(0, 118)
    ax.set_ylabel("Mutasyon skoru (%)", fontsize=10, color=INK)
    ax.axhline(100, color=RULE, lw=1, ls="--", zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK)
    ax.set_title("Aynı modül (tarih.py), 36 mutant, dört test paketi",
                 fontsize=10.5, color=INK, loc="left")
    return _save(fig, _yol("mutasyon_skor"))


# 7. Ozellik tabanli test: kucultme zinciri ----------------------------- #
def kucultme():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=8)
    ornekler = ["[194, -85]", "[0, -85]", "[0, 85]", "[0, 1]"]
    x0 = 0.4
    w = 2.9
    for i, o in enumerate(ornekler):
        x = x0 + i * 3.4
        fill = FILL[3] if i == 0 else (FILL[2] if i < 3 else FILL[1])
        edge = EDGE[3] if i == 0 else (EDGE[2] if i < 3 else EDGE[1])
        _box(ax, x, 4.5, w, 1.3, "xs = %s" % o, fill, edge,
             fs=10, tcol=INK)
        if i < 3:
            _arrow(ax, x + w, 5.15, x + 3.4, 5.15, col=MUTED, lw=1.4)
    ax.text(0.4, 6.3, "Bulunan ilk karşı örnek (büyük, gürültülü)",
            fontsize=9, color=ACCENT, va="bottom")
    ax.text(13.4, 6.3, "Küçültülmüş (en küçük)", fontsize=9,
            color=EDGE[1], va="bottom", ha="right")
    ax.text(7.0, 3.5, "Her adımda özellik hâlâ başarısız; kök neden: "
            "tam bölme (//)", ha="center", fontsize=9, color=INK)
    _box(ax, 0.4, 0.5, 13.2, 2.2,
         "Beklenen: ortalama(xs) == statistics.fmean(xs)\n"
         "Gerçek:   ortalama([0, 1]) = 0, beklenen 0.5\n"
         "Hypothesis, başarısız girdiyi küçültüp en küçük karşı "
         "örneği raporlar.",
         FILL[0], EDGE[0], fs=9.2)
    return _save(fig, _yol("kucultme"))


# 8. TDD dongusu ------------------------------------------------------- #
def tdd():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=9)
    cx = 7.0
    _box(ax, 4.9, 6.6, 4.2, 1.3, "KIRMIZI\nBaşarısız bir test yaz",
         FILL[3], EDGE[3], fs=9.5, bold=True)
    _box(ax, 0.6, 1.4, 4.2, 1.3, "YEŞİL\nEn basit kodla geçir",
         FILL[1], EDGE[1], fs=9.5, bold=True)
    _box(ax, 9.2, 1.4, 4.2, 1.3, "YENİDEN DÜZENLE\nTestler yeşil kalsın",
         FILL[0], EDGE[0], fs=9.2, bold=True)
    _arrow(ax, 8.9, 7.2, 11.4, 2.8, col=MUTED, lw=1.6, rad=-0.25)
    _arrow(ax, 9.2, 2.05, 4.8, 2.05, col=MUTED, lw=1.6)
    _arrow(ax, 2.7, 2.8, 5.1, 6.6, col=MUTED, lw=1.6, rad=-0.25)
    ax.text(cx, 4.4, "döngü\nkısa tutulur\n(dakikalar)", ha="center",
            va="center", fontsize=8.8, color=MUTED)
    ax.text(7.0, 0.35, "Kırmızıyı görmeden yazılan test bir şey "
            "kanıtlamaz.", ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("tdd"))


# 9. Kararsiz test nedenleri ------------------------------------------- #
def kararsiz():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=9.6)
    kose = [
        (0.4, 5.0, "Zamanlama", FILL[3], EDGE[3],
         "sleep ile yarış: yük\naltında kayar\n\nÇözüm: olay (event) ya da\n"
         "zaman aşımlı bekleme"),
        (7.2, 5.0, "Sıra bağımlılığı", FILL[2], EDGE[2],
         "test_oku, test_yaz'a\nbağlı; ters sırada kırılır\n\nÇözüm: her test "
         "kendi\ndurumunu kurar (fixture)"),
        (0.4, 0.4, "Rastgelelik", FILL[4], EDGE[4],
         "tohumsuz random: her\nkoşuda farklı sonuç\n\nÇözüm: "
         "random.Random(42)"),
        (7.2, 0.4, "Paylaşılan durum", FILL[1], EDGE[1],
         "global liste, dosya ya da\nveritabanı diğer testlerde\n"
         "kalır\n\nÇözüm: tmp_path, temiz\nveritabanı, izolasyon"),
    ]
    for x, y, baslik, f, e, govde in kose:
        _box(ax, x, y, 6.4, 4.1, "", f, e)
        ax.text(x + 3.2, y + 3.65, baslik, ha="center", fontsize=10,
                weight="bold", color=INK)
        ax.text(x + 0.3, y + 3.0, govde, fontsize=8.6, color=INK,
                va="top")
    return _save(fig, _yol("kararsiz"))


# 10. MC/DC tablosu ----------------------------------------------------- #
def mcdc():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=10.5)
    basliklar = ["No", "A", "B", "C", "(A ve B) veya C", "Seçildi mi?"]
    xs = [0.3, 1.9, 3.5, 5.1, 6.7, 10.2]
    gen = [1.5, 1.5, 1.5, 1.5, 3.4, 3.2]
    for x, g, b in zip(xs, gen, basliklar):
        ax.text(x + g / 2, 9.8, b, ha="center", fontsize=9, weight="bold",
                color=INK)
    satirlar = [("1", "T", "T", "T", "T"),
                ("2", "T", "T", "F", "T"),
                ("3", "T", "F", "T", "T"),
                ("4", "T", "F", "F", "F"),
                ("5", "F", "T", "T", "T"),
                ("6", "F", "T", "F", "F"),
                ("7", "F", "F", "T", "T"),
                ("8", "F", "F", "F", "F")]
    secilen = {"TTF", "FTF", "TFF", "TFT"}
    y = 8.7
    for no, a, b, c, k in satirlar:
        kodu = a + b + c
        vurgu = kodu in secilen
        f = FILL[1] if vurgu else FILL[0]
        e = EDGE[1] if vurgu else RULE
        for x, g, metin in zip(xs[:4], gen[:4], [no, a, b, c]):
            _box(ax, x, y, g, 0.8, metin, f, e, fs=9, bold=vurgu)
        _box(ax, xs[4], y, gen[4], 0.8, k, f, e, fs=9, bold=vurgu)
        _box(ax, xs[5], y, gen[5], 0.8,
             "seçildi (%s)" % kodu if vurgu else "-", f, e, fs=8.8,
             bold=vurgu)
        y -= 1.0
    ax.text(7.0, 0.6, "Dört seçilmiş test (yeşil) her koşulu, yalnız o "
            "koşulun değiştiği bir\nçiftle bağımsız etkisini gösterir.",
            ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("mcdc"))


if __name__ == "__main__":
    yollar = [piramit(), aaa(), ikizler(), kapsama(), mutasyon_dongusu(),
              mutasyon_skor(), kucultme(), tdd(), kararsiz(), mcdc()]
    for y in yollar:
        print("yazildi:", os.path.normpath(y))
