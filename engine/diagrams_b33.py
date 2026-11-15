# -*- coding: utf-8 -*-
"""Bölüm 33 - 'İlişkisel Model' diyagramları.

Ölçüm verisi okunmaz; şekiller bölümdeki örnek değerlerden çizilir
(FD kapanış izi, B+ ağacı bölünmesi, sayfa düzeni, anomali zamanları).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
MONO = {"family": "DejaVu Sans Mono"}


def _yol(ad):
    return os.path.join(OUT, "b33_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _hucre(ax, x, y, w, h, metin, fill="white", bold=False, fs=10):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fill,
                               edgecolor=RULE, linewidth=1))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=fs, color=INK, weight="bold" if bold else "normal")


# 1. Tablo terminolojisi ------------------------------------------------- #
def terminoloji():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.6)
    ad = ["no", "ad", "eposta", "yas"]
    satirlar = [["1", "Ayşe", "a@x.com", "21"],
                ["2", "Mert", "m@x.com", "20"],
                ["3", "Ali", "ali@x.com", "23"]]
    x0, y0, w, h = 3.4, 1.5, 2.0, 0.62
    for j, a in enumerate(ad):
        _hucre(ax, x0 + j * w, y0 + 3 * h, w, h, a, FILL[0], True, 11)
    for i, s in enumerate(satirlar):
        for j, v in enumerate(s):
            _hucre(ax, x0 + j * w, y0 + (2 - i) * h, w, h, v)
    ax.text(x0 + 4 * w / 2, y0 + 4 * h + 0.35, "ilişki (tablo)",
            ha="center", va="center", fontsize=11, color=ACCENT,
            weight="bold")
    ax.text(x0 + 4 * w + 0.2, y0 + 3.5 * h, "nitelik = sütun",
            ha="left", va="center", fontsize=10, color=ACCENT_L)
    ax.text(x0 + 4 * w + 0.2, y0 + 1.5 * h, "demet = satır",
            ha="left", va="center", fontsize=10, color=ACCENT_L)
    ax.text(x0 + 4 * w + 0.2, y0 + 0.5 * h,
            "alan = bir niteliğin\nizin verilen değerleri",
            ha="left", va="center", fontsize=9.5, color=ACCENT_L)
    ax.text(x0, y0 - 0.55, "şema: öğrenci(no, ad, eposta, yas)",
            ha="left", va="center", fontsize=10, color=INK)
    ax.text(x0, y0 - 1.15, "Küme anlamındaki ilişkide yinelenen demet "
            "yoktur.", ha="left", va="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("terminoloji"))


# 2. Birincil ve yabancı anahtar -------------------------------------------- #
def anahtar_fk():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.2)
    x0, w, h = 1.0, 2.1, 0.6
    # öğrenci (üstte)
    ax.text(x0 + w, 5.95, "öğrenci", ha="center", fontsize=11,
            color=ACCENT_L, weight="bold")
    for j, a in enumerate(["no (PK)", "ad"]):
        _hucre(ax, x0 + j * w, 4.7, w, h, a, FILL[0], True, 10)
    for i, v in enumerate([["1", "Ayşe"], ["2", "Mert"]]):
        for j, t in enumerate(v):
            _hucre(ax, x0 + j * w, 4.1 - i * h, w, h, t)
    # kayıt (altta)
    ax.text(x0 + w, 2.85, "kayıt", ha="center", fontsize=11,
            color=ACCENT_L, weight="bold")
    for j, a in enumerate(["ogr_no (FK)", "id (PK)", "ders"]):
        _hucre(ax, x0 + j * w, 2.1, w, h, a,
               FILL[2] if j == 0 else FILL[0], True, 10)
    for i, v in enumerate([["1", "10", "VT"], ["1", "11", "OS"]]):
        for j, t in enumerate(v):
            _hucre(ax, x0 + j * w, 1.5 - i * h, w, h, t)
    # yabancı anahtar oku: sol kenardan yukarı kıvrılır
    _arrow(ax, x0 - 0.05, 2.4, x0 - 0.05, 5.0, col=ACCENT, rad=-0.25)
    ax.text(x0 - 0.3, 3.7, "FK", ha="right", va="center",
            fontsize=10, color=ACCENT, weight="bold")
    # açıklamalar (sağda)
    notlar = [
        ("Birincil anahtar (PK)", "Her satırı tekil kılar; NULL olamaz."),
        ("Yabancı anahtar (FK)", "kayıt.ogr_no, öğrenci.no'ya işaret eder."),
        ("Kural", "Var olmayan bir öğrenciye kayıt eklenemez."),
    ]
    for k, (baslik, metin) in enumerate(notlar):
        y = 4.9 - k * 1.25
        ax.text(8.0, y, baslik, ha="left", fontsize=10.5,
                color=ACCENT, weight="bold")
        ax.text(8.0, y - 0.45, metin, ha="left", fontsize=9.5, color=INK)
    return _save(fig, _yol("anahtar_fk"))


# 3. İlişkisel cebir işlemleri ------------------------------------------- #
def cebir():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=7.6)
    ops = [
        ("σ  seçme", "satırları koşula göre süz", "σ yaş>20 (öğrenci)"),
        ("π  izdüşüm", "sütunları seç, yinelenenleri at", "π ad (öğrenci)"),
        ("ρ  yeniden adlandırma", "nitelik ya da ilişki adını değiştir",
         "ρ ad→isim (öğrenci)"),
        ("⋈  birleştirme", "ortak nitelikte eşleşen demetler",
         "öğrenci ⋈ kayıt"),
        ("∪  birleşim", "iki ilişkinin demetlerini topla",
         "R ∪ S"),
        ("−  fark", "birinde var, diğerinde yok", "R − S"),
        ("×  kartezyen", "her demeti her demetle eşle",
         "R × S"),
    ]
    for k, (sim, aciklama, ornek) in enumerate(ops):
        col, satir = k % 2, k // 2
        x = 0.4 + col * 6.9
        y = 5.8 - satir * 1.45
        _box(ax, x, y - 0.5, 6.3, 1.2, "", FILL[k % 5], EDGE[k % 5])
        ax.text(x + 0.25, y + 0.25, sim, ha="left", va="center",
                fontsize=12, color=INK, weight="bold")
        ax.text(x + 0.25, y - 0.22, aciklama, ha="left", va="center",
                fontsize=9.5, color=INK)
        ax.text(x + 6.05, y + 0.25, ornek, ha="right", va="center",
                fontsize=9.5, color=MUTED)
    ax.text(7.0, 0.35, "Her işlem bir ya da iki ilişki alır ve yine bir "
            "ilişki döndürür (kapanma).", ha="center", fontsize=10,
            color=ACCENT)
    return _save(fig, _yol("cebir"))


# 4. ER diyagramı: öğrenci - ders ---------------------------------------- #
def er_diyagrami():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.2)

    def varlik(x, y, ad, nitelikler):
        _box(ax, x, y, 3.0, 2.0, "", FILL[0], EDGE[0])
        ax.text(x + 1.5, y + 1.65, ad, ha="center", va="center",
                fontsize=11, weight="bold", color=INK)
        ax.plot([x, x + 3.0], [y + 1.3, y + 1.3], color=RULE, lw=1)
        ax.text(x + 1.5, y + 0.6, nitelikler, ha="center", va="center",
                fontsize=9.5, color=INK)

    varlik(0.6, 2.4, "Öğrenci", "no (anahtar)\nad, bölüm")
    varlik(10.4, 2.4, "Ders", "kod (anahtar)\nad, kredi")
    # ilişki: elmas
    cx, cy = 7.0, 3.4
    elmas = Polygon([(cx - 1.6, cy), (cx, cy + 1.0), (cx + 1.6, cy),
                     (cx, cy - 1.0)], closed=True, facecolor=FILL[2],
                    edgecolor=EDGE[2], lw=1.2)
    ax.add_patch(elmas)
    ax.text(cx, cy, "alır", ha="center", va="center", fontsize=11,
            weight="bold", color=INK)
    ax.plot([3.6, cx - 1.6], [3.4, 3.4], color=INK, lw=1.2)
    ax.plot([cx + 1.6, 10.4], [3.4, 3.4], color=INK, lw=1.2)
    ax.text(4.0, 3.65, "N", ha="center", fontsize=12, weight="bold")
    ax.text(10.0, 3.65, "M", ha="center", fontsize=12, weight="bold")
    # ilişki niteliği: not
    ax.plot([cx, cx], [cy - 1.0, 1.6], color=INK, lw=1.0, ls="--")
    _box(ax, cx - 0.9, 0.7, 1.8, 0.8, "not", FILL[1], EDGE[1], fs=11)
    ax.text(7.0, 6.5, "Bir öğrenci birçok ders alır, bir ders birçok "
            "öğrenciye açılır: N:M", ha="center", fontsize=10,
            color=ACCENT)
    return _save(fig, _yol("er_diyagrami"))


# 5. Normal formlar: adımlar ----------------------------------------------- #
def normal_formlar():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.2)
    adimlar = [
        ("Ham tablo", ["tek tabloda", "her şey;", "anomaliler var"], FILL[3]),
        ("1NF", ["her hücre", "tek değer;", "tekrar grup yok"], FILL[0]),
        ("2NF", ["kısmi bağımlılık", "yok: ogr_ad,", "ders_ad ayrılır"], FILL[1]),
        ("3NF", ["geçişli bağımlılık", "yok: bolum →", "baskan ayrılır"], FILL[2]),
        ("BCNF", ["her belirleyici", "süper anahtar", "olur"], FILL[4]),
    ]
    w, h, gap = 2.36, 2.8, 0.36
    for k, (ad, satirlar, fill) in enumerate(adimlar):
        x = 0.25 + k * (w + gap)
        _box(ax, x, 2.6, w, h, "", fill, EDGE[k % 5])
        ax.text(x + w / 2, 4.9, ad, ha="center", va="center",
                fontsize=12, weight="bold", color=INK)
        for r, metin in enumerate(satirlar):
            ax.text(x + w / 2, 4.15 - r * 0.5, metin, ha="center",
                    va="center", fontsize=8.6, color=INK)
        if k < len(adimlar) - 1:
            _arrow(ax, x + w + 0.03, 4.0, x + w + gap - 0.03, 4.0,
                   col=ACCENT, lw=1.4)
    ax.text(7.0, 1.7, "Her adım, bir önceki adımın bıraktığı bir "
            "bağımlılık türünü ortadan kaldırır.", ha="center",
            fontsize=10, color=ACCENT)
    ax.text(7.0, 1.0, "Ayrıştırma kayıpsız olmalı; bağımlılıklar "
            "mümkünse korunmalı (Bölüm 33.9).", ha="center",
            fontsize=9.5, color=MUTED)
    return _save(fig, _yol("normal_formlar"))


# 6. FD kapanış izi: {B,D}+ ----------------------------------------------- #
def fd_kapanis():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.6)
    nitelik = list("ABCDEG")
    adimlar = [
        ("başlangıç  X = {B, D}", set("BD"), None),
        ("D → EG uygulanır", set("BDEG"), "D → EG"),
        ("BE → C uygulanır", set("BCDEG"), "BE → C"),
        ("CE → AG uygulanır", set("ABCDEG"), "CE → AG"),
    ]
    x0, y_ust, dh = 4.4, 6.0, 1.45
    for s_idx, (etiket, kume, fd_ad) in enumerate(adimlar):
        y = y_ust - s_idx * dh
        ax.text(0.4, y, etiket, ha="left", va="center", fontsize=10,
                color=INK)
        for j, a in enumerate(nitelik):
            dolu = a in kume
            _hucre(ax, x0 + j * 1.2, y - 0.3, 1.2, 0.6, a,
                   FILL[2] if dolu else "white", bold=dolu, fs=12)
        if fd_ad:
            ax.text(x0 + 6 * 1.2 + 0.25, y, "kullanılan: " + fd_ad,
                    ha="left", va="center", fontsize=9.5, color=ACCENT)
    ax.text(0.4, 0.45, "Sonuç: {B, D}+ = {A, B, C, D, E, G} (tüm şema). "
            "Yani {B, D} bir süper anahtardır.", ha="left", fontsize=9.5,
            color=MUTED)
    return _save(fig, _yol("fd_kapanis"))


# 7. B+ ağacı: yaprak bölünmesi ve ayırıcının kopyalanması ---------------- #
def bplus_bolunme():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.2)
    # (a) yaprak taştı
    ax.text(3.0, 6.4, "(a) yaprak m = 3 anahtarı aştı",
            ha="center", fontsize=10.5, weight="bold", color=ACCENT_L)
    for j, v in enumerate(["5", "6", "10", "20"]):
        _hucre(ax, 0.7 + j * 1.0, 4.4, 1.0, 0.7, v,
               FILL[3] if j < 4 else FILL[0], bold=True, fs=11)
    ax.text(3.0, 3.6, "yapraklar arası bağ: sonraki = (yok)",
            ha="center", fontsize=9, color=MUTED)
    _arrow(ax, 4.9, 4.75, 6.0, 4.75, col=ACCENT, lw=1.6)
    # (b) bölünme
    ax.text(10.4, 6.4, "(b) bölünme ve kopyalama",
            ha="center", fontsize=10.5, weight="bold", color=ACCENT_L)
    _hucre(ax, 9.2, 5.5, 2.4, 0.7, "10", FILL[2], bold=True, fs=11)
    for j, v in enumerate(["5, 6", "10, 20"]):
        _hucre(ax, 8.1 + j * 2.7, 3.7, 2.2, 0.7, v, FILL[0], bold=True,
               fs=11)
    _arrow(ax, 10.4, 5.5, 9.2, 4.4, col=ACCENT, lw=1.4)
    _arrow(ax, 10.4, 5.5, 11.6, 4.4, col=ACCENT, lw=1.4)
    _arrow(ax, 10.35, 4.05, 10.75, 4.05, col=ACCENT_L, lw=1.2)
    ax.text(10.55, 3.45, "sonraki", ha="center", fontsize=9,
            color=ACCENT_L)
    ax.text(7.0, 1.6, "Yaprak bölünürken ayırıcı (10) yukarı KOPYALANIR "
            "ve sağ yaprağın ilk anahtarıdır.", ha="center", fontsize=9.8,
            color=ACCENT)
    ax.text(7.0, 0.9, "İç düğüm bölünürken ayırıcı yukarı İTİLİR "
            "(bir daha aşağıda görünmez).", ha="center", fontsize=9.8,
            color=MUTED)
    return _save(fig, _yol("bplus_bolunme"))


# 8. Sayfa düzeni (SQLite B-ağaç sayfası) ---------------------------------- #
def sayfa_duzen():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=7.8)
    x, w = 2.6, 4.8
    parcalar = [
        (6.7, 0.7, "dosya başlığı (100 bayt, yalnız 1. sayfa)", FILL[4]),
        (6.0, 0.6, "sayfa başlığı (8 ya da 12 bayt)", FILL[1]),
        (5.2, 0.8, "hücre işaretçi dizisi (2 bayt/hücre)", FILL[2]),
        (3.8, 1.4, "boş alan", "white"),
        (2.2, 1.6, "hücre içeriği (sonda başlar)", FILL[0]),
    ]
    for y, h, metin, fill in parcalar:
        _hucre(ax, x, y, w, h, metin, fill, fs=10)
    _arrow(ax, x + w + 0.2, 5.2, x + w + 0.2, 3.9, col=ACCENT, lw=1.2)
    _arrow(ax, x + w + 0.2, 2.2, x + w + 0.2, 3.8, col=ACCENT, lw=1.2)
    ax.text(x + w + 0.4, 4.6, "hücre işaretçileri\naşağı büyür",
            ha="left", va="center", fontsize=9, color=ACCENT)
    ax.text(x + w + 0.4, 3.0, "hücre içerikleri\nyukarı büyür",
            ha="left", va="center", fontsize=9, color=ACCENT)
    ax.text(x - 0.2, 1.0, "toplam: sayfa boyutu (örnek: 4096 bayt)",
            ha="left", va="center", fontsize=10, color=INK)
    ax.text(x - 0.2, 0.4, "tablo ağacında yaprak: 0x0D; iç: 0x05. "
            "İndeks ağacında yaprak: 0x0A; iç: 0x02.",
            ha="left", va="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("sayfa_duzen"))


# 9. WAL akışı ------------------------------------------------------------- #
def wal_akis():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=7.0)
    kutular = [
        (0.4, "Uygulama\nCOMMIT"),
        (3.6, "Sayfa önbelleği\n(RAM)"),
        (6.8, "WAL dosyası\n(çerçeveler)"),
        (10.0, "Ana dosya\n(veritabanı)"),
    ]
    for k, (x, metin) in enumerate(kutular):
        _box(ax, x, 3.2, 2.6, 1.4, "", FILL[k % 5], EDGE[k % 5])
        ax.text(x + 1.3, 3.9, metin, ha="center", va="center", fontsize=10,
                color=INK, linespacing=1.4)
    _arrow(ax, 3.0, 3.9, 3.6, 3.9, col=ACCENT, lw=1.4)
    _arrow(ax, 6.2, 3.9, 6.8, 3.9, col=ACCENT, lw=1.4)
    _arrow(ax, 9.4, 3.9, 10.0, 3.9, col=ACCENT, lw=1.4)
    ax.text(0.4, 2.45, "1. Değişiklik önce WAL dosyasına çerçeve "
            "olarak yazılır.", ha="left", fontsize=9.5, color=INK)
    ax.text(0.4, 1.95, "2. COMMIT: commit çerçevesi fsync ile diske "
            "iner (Bölüm 28.7).", ha="left", fontsize=9.5, color=INK)
    ax.text(0.4, 1.45, "3. Checkpoint: WAL içeriği ana dosyaya "
            "aktarılır.", ha="left", fontsize=9.5, color=INK)
    ax.text(0.4, 0.7, "Açılışta: yalnızca commit edilmiş çerçeveler "
            "yeniden oynatılır.", ha="left", fontsize=10, color=ACCENT)
    return _save(fig, _yol("wal_akis"))


# 10. Eşzamanlılık anomalileri: zaman çizelgeleri -------------------------- #
def _zaman(ax, y, etiket, olaylar, x0=2.2, x1=13.4):
    ax.plot([x0, x1], [y, y], color=RULE, lw=2)
    ax.text(x0 - 0.2, y, etiket, ha="right", va="center", fontsize=10,
            color=INK, weight="bold")
    for x, metin in olaylar:
        ax.plot([x], [y], "o", color=ACCENT, ms=6)
        ax.text(x, y + 0.3, metin, ha="center", va="bottom", fontsize=9,
                color=INK)


def anomaliler():
    fig, ax = _tuval(9.6, 6.4, xl=14, yl=10.0)
    bloklar = [
        (9.6, "Kirli okuma: T2, commit edilmemiş veriyi görür",
         [(3.5, "X := 5 yaz"), (9.0, "ROLLBACK")],
         [(6.2, "X oku = 5")]),
        (6.4, "Tekrarlanamayan okuma: aynı satır iki okumada farklı",
         [(3.5, "X oku = 1"), (10.4, "X oku = 2")],
         [(6.4, "X := 2; COMMIT")]),
        (3.2, "Hayalet: aynı koşul iki sorguda farklı satır sayısı",
         [(3.5, "yas>20: 3 satır"), (10.4, "yas>20: 4 satır")],
         [(6.4, "INSERT yas=25; COMMIT")]),
    ]
    for top, baslik, t1, t2 in bloklar:
        ax.text(0.4, top, baslik, ha="left", va="center", fontsize=10.5,
                color=ACCENT, weight="bold")
        _zaman(ax, top - 1.0, "T1", t1)
        _zaman(ax, top - 2.2, "T2", t2)
    return _save(fig, _yol("anomaliler"))


if __name__ == "__main__":
    for f in (terminoloji, anahtar_fk, cebir, er_diyagrami,
              normal_formlar, fd_kapanis, bplus_bolunme, sayfa_duzen,
              wal_akis, anomaliler):
        print(f())
