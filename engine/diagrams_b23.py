# -*- coding: utf-8 -*-
"""Bolum 23 - 'Clean Code' diyagramlari.

Olcum grafigi (karmasiklik_olcum) engine/veri/b23_karmasiklik.csv
dosyasini okur; o CSV, bolumdeki ornek kodlarin karmasiklik aracindan
uretilmistir. Diger sekiller bolumdeki ornek degerlerden cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "gorseller")
KARMA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "veri", "b23_karmasiklik.csv")


def _yol(ad):
    return os.path.join(OUT, "b23_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. Adlandirma: ad, okurun zihninde ne kadar is birakir ------------- #
def adlandirma_zihin():
    fig, ax = _tuval(9.6, 4.0, xl=14, yl=6.4)
    ax.text(3.4, 6.0, "Kötü ad: f(k, e, m)", ha="center", fontsize=10.5,
            color=ACCENT, weight="bold")
    _box(ax, 0.6, 4.6, 5.6, 0.8, "f(k, e, m)", FILL[3], EDGE[3],
         fs=10.5)
    sorular = ["k nedir? liste mi, kayıt mı?",
               "e eşik mi, başka bir şey mi?",
               "m bir mod mu, bayrak mı?"]
    ust = 4.6
    for i, metin in enumerate(sorular):
        y = 3.5 - i * 1.0
        _arrow(ax, 3.4, ust, 3.4, y + 0.7, col=MUTED, lw=1.0)
        _box(ax, 0.6, y, 5.6, 0.7, metin, FILL[2], EDGE[2], fs=9.2)
        ust = y
    ax.text(3.4, 0.25, "Okur kodu okumadan önce üç soruyu çözmek zorunda",
            ha="center", fontsize=9, color=MUTED)

    ax.text(10.6, 6.0, "İyi ad: kritik_ozet(...)", ha="center",
            fontsize=10.5, color=EDGE[1], weight="bold")
    _box(ax, 7.8, 4.6, 5.6, 0.8, "kritik_ozet(ham_kayitlar, esik, mod)",
         FILL[1], EDGE[1], fs=9.6)
    _arrow(ax, 10.6, 4.6, 10.6, 4.2, col=EDGE[1], lw=1.0)
    _box(ax, 7.8, 3.5, 5.6, 0.7, "Ad, ne yaptığını söylüyor",
         FILL[1], EDGE[1], fs=9.4)
    _arrow(ax, 10.6, 3.5, 10.6, 3.2, col=EDGE[1], lw=1.0)
    _box(ax, 7.8, 2.5, 5.6, 0.7, "Parametreler de anlam taşıyor",
         FILL[1], EDGE[1], fs=9.4)
    ax.text(10.6, 0.25, "Aynı bilgi, bir bakışta",
            ha="center", fontsize=9, color=MUTED)
    ax.plot([7.0, 7.0], [0.8, 5.6], color=RULE, lw=1.0)
    return _save(fig, _yol("adlandirma_zihin"))


# 2. Koruma cumleleri: ic ice if piramidi -> duz akis ---------------- #
def koruma_duzlestirme():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=7.4)
    ax.text(3.3, 7.0, "Önce: iç içe if (derinlik 6)", ha="center",
            fontsize=10.5, color=ACCENT, weight="bold")
    katman = ["olcum var mı?", "gerilim var mı?", "aralık içinde mi?",
              "sıcaklık var mı?", "sıcaklık > 60?", "bekleme doldu mu?"]
    for i, metin in enumerate(katman):
        x = 0.3 + i * 0.45
        _box(ax, x, 6.0 - i * 0.9, 6.0 - i * 0.45, 0.7,
             metin, FILL[i % 4], EDGE[i % 4], fs=8.8)
    ax.text(3.3, 0.3, "Her katman bir önceki koşulun içinde: okur "
            "altı kapanışı takip eder", ha="center", fontsize=8.6,
            color=MUTED)
    ax.plot([7.0, 7.0], [0.7, 6.9], color=RULE, lw=1.0)

    ax.text(10.6, 7.0, "Sonra: koruma cümleleri (derinlik 2)",
            ha="center", fontsize=10.5, color=EDGE[1], weight="bold")
    yeni = ["olcum None -> VERI_YOK", "gerilim None -> VERI_EKSIK",
            "aralık dışı -> GERILIM_HATASI", "sıcaklık None -> VERI_EKSIK",
            "sıcaklık > 60 -> KRITIK/SESSIZ", "sıcaklık > 45 -> UYARI",
            "aksi halde -> NORMAL"]
    for i, metin in enumerate(yeni):
        _box(ax, 7.6, 6.2 - i * 0.82, 6.0, 0.6, metin, FILL[1], EDGE[1],
             fs=8.6)
    ax.text(10.6, 0.3, "Her koşul tek satır, tek anlam; sıra önemli",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("koruma_duzlestirme"))


# 3. Dongusel karmasiklik: kontrol akis grafi ----------------------- #
def cfg_alarm():
    fig, ax = _tuval(9.6, 6.4, xl=14, yl=9.4)
    satir = [8.4, 7.3, 6.2, 5.1, 4.0, 2.9, 1.8, 0.7]
    kutu_h = 0.6
    karar = [
        (8.4, "D1: olcum None?"),
        (7.3, "D2: gerilim None?"),
        (6.2, "D3: aralık dışı?"),
        (5.1, "D4: sıcaklık None?"),
        (4.0, "D5: sıcaklık > 60?"),
        (2.9, "D7: sıcaklık > 45?"),
    ]
    for y, metin in karar:
        _box(ax, 0.6, y - kutu_h / 2, 3.6, kutu_h, metin, FILL[0],
             EDGE[0], fs=9)
    # D6: sicaklik > 60 iken bekleme suresi doldu mu?
    _box(ax, 5.4, 4.0 - kutu_h / 2, 3.2, kutu_h, "D6: bekleme doldu?",
         FILL[0], EDGE[0], fs=9)
    cikis = [
        (8.4, "VERI_YOK"), (7.3, "VERI_EKSIK"), (6.2, "GERILIM_HATASI"),
        (5.1, "VERI_EKSIK"), (4.0, "KRITIK"), (2.9, "SESSIZ"),
        (1.8, "UYARI"), (0.7, "NORMAL"),
    ]
    for y, metin in cikis:
        _box(ax, 10.2, y - kutu_h / 2, 3.4, kutu_h, metin, FILL[1],
             EDGE[1], fs=9)
    # D1..D4: evet -> ilgili cikis, hayir -> altindaki karar
    for i in range(4):
        y = satir[i]
        _arrow(ax, 4.2, y, 10.2, y, col=ACCENT_L, lw=1.0)
        ax.text(7.0, y + 0.1, "evet", fontsize=7.6, color=ACCENT_L,
                ha="center")
        _arrow(ax, 2.4, y - 0.3, 2.4, satir[i + 1] + 0.3, col=MUTED,
               lw=1.0)
        ax.text(2.6, (y + satir[i + 1]) / 2, "hayır", fontsize=7.6,
                color=MUTED, va="center")
    # D5: evet -> D6 ; hayir -> D7
    _arrow(ax, 4.2, 4.0, 5.4, 4.0, col=ACCENT_L, lw=1.0)
    ax.text(4.8, 4.25, "evet", fontsize=7.6, color=ACCENT_L, ha="center")
    _arrow(ax, 2.4, 3.7, 2.4, 3.2, col=MUTED, lw=1.0)
    ax.text(2.6, 3.45, "hayır", fontsize=7.6, color=MUTED, va="center")
    # D6: evet -> KRITIK ; hayir -> SESSIZ
    _arrow(ax, 8.6, 4.0, 10.2, 4.0, col=ACCENT_L, lw=1.0)
    ax.text(9.4, 4.25, "evet", fontsize=7.6, color=ACCENT_L, ha="center")
    _arrow(ax, 8.6, 3.7, 10.2, 2.9, col=ACCENT_L, lw=1.0)
    ax.text(9.3, 3.15, "hayır", fontsize=7.6, color=ACCENT_L)
    # D7: evet -> UYARI ; hayir -> NORMAL
    _arrow(ax, 4.2, 2.9, 10.2, 1.8, col=ACCENT_L, lw=1.0)
    ax.text(7.2, 2.25, "evet", fontsize=7.6, color=ACCENT_L)
    _arrow(ax, 4.2, 2.6, 10.2, 0.7, col=ACCENT_L, lw=1.0)
    ax.text(7.2, 1.2, "hayır", fontsize=7.6, color=ACCENT_L)
    ax.text(7.0, 9.0, "Karar noktası 7, çıkış yolu 8: "
            "döngüsel karmaşıklık = 7 + 1 = 8",
            ha="center", fontsize=9.6, color=INK, weight="bold")
    return _save(fig, _yol("cfg_alarm"))


# 4. Refactoring guvenlik agi dongusu ------------------------------- #
def guvenlik_dongusu():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.4)
    _box(ax, 0.6, 5.6, 4.0, 1.0, "1. Eski davranışı kaydet\n"
         "(karakterizasyon testi)", FILL[0], EDGE[0], fs=9.4)
    _box(ax, 9.4, 5.6, 4.0, 1.0, "2. Tek ve küçük bir\n"
         "dönüşüm uygula", FILL[2], EDGE[2], fs=9.4)
    _box(ax, 9.4, 1.2, 4.0, 1.0, "3. Testi çalıştır", FILL[1],
         EDGE[1], fs=9.8, bold=True)
    _box(ax, 0.6, 1.2, 4.0, 1.0, "Çıktı kayıtla aynı mı?", FILL[4],
         EDGE[4], fs=9.4)
    _arrow(ax, 4.6, 6.1, 9.4, 6.1, col=ACCENT_L, lw=1.4)
    _arrow(ax, 11.4, 5.6, 11.4, 2.2, col=ACCENT_L, lw=1.4)
    _arrow(ax, 9.4, 1.7, 4.6, 1.7, col=ACCENT_L, lw=1.4)
    _arrow(ax, 2.6, 2.2, 2.6, 5.6, col=ACCENT, lw=1.4)
    ax.text(2.8, 3.9, "evet: adımı tut,\nbir sonrakine geç", fontsize=8.8,
            color=EDGE[1], va="center")
    ax.text(11.6, 3.9, "hayır: geri al\nve adımı küçült", fontsize=8.8,
            color=ACCENT, va="center")
    ax.text(7.0, 0.3, "Her döngü küçük olmalı: hata olursa suçlu, son adımdır",
            ha="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("guvenlik_dongusu"))


# 5. Kod kokusu -> refactoring haritasi ----------------------------- #
def koku_haritasi():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=9.0)
    eslesme = [
        ("Uzun fonksiyon", "Extract Function (Fonksiyonu Çıkar)"),
        ("Uzun parametre listesi", "Introduce Parameter Object"),
        ("Sihirli sayı", "Replace Magic Number with Constant"),
        ("İlkel takıntısı (tuple[3])", "Replace Primitive with Object"),
        ("Kopya kod (DRY ihlali)", "Extract / Consolidate Function"),
        ("Ölü kod", "Remove Dead Code"),
        ("Yorum kokusu (ne'yi anlatan)", "Rename + yorumu sil"),
        ("Tip koşullarının zinciri", "Replace Conditional with Polymorphism"),
    ]
    ax.text(3.0, 8.5, "Koku", ha="center", fontsize=10.5, weight="bold",
            color=INK)
    ax.text(10.6, 8.5, "Giderme yolu", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    for i, (koku, cozum) in enumerate(eslesme):
        y = 7.6 - i * 0.9
        _box(ax, 0.3, y - 0.3, 5.4, 0.6, koku, FILL[3], EDGE[3], fs=9.2)
        _box(ax, 8.3, y - 0.3, 5.4, 0.6, cozum, FILL[1], EDGE[1], fs=9.0)
        _arrow(ax, 5.8, y, 8.2, y, col=MUTED, lw=1.0)
    ax.text(7.0, 0.3, "Koku bir belirtidir; giderme davranışı korumalı "
            "ve testle doğrulanmalı", ha="center", fontsize=8.8,
            color=MUTED)
    return _save(fig, _yol("koku_haritasi"))


# 6. Olcum grafigi: karmasiklik once/sonra (CSV) -------------------- #
def karmasiklik_olcum():
    with open(KARMA_CSV, encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    ornekler = []
    for r in satirlar:
        if r["surum"] == "eski":
            ornekler.append(r["ornek"])
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    grup = list(range(len(ornekler)))
    genislik = 0.2
    seriler = [("cc", "eski", "döngüsel (eski)", EDGE[3], FILL[3]),
               ("cc", "yeni", "döngüsel (yeni)", EDGE[0], FILL[0]),
               ("bilissel", "eski", "bilişsel (eski)", EDGE[3], "#E6C9C6"),
               ("bilissel", "yeni", "bilişsel (yeni)", EDGE[0], "#C9D5E0")]
    for k, (alan, surum, etiket, kenar, dolgu) in enumerate(seriler):
        degerler = []
        for ornek in ornekler:
            kayit = [r for r in satirlar
                     if r["ornek"] == ornek and r["surum"] == surum][0]
            degerler.append(int(kayit[alan]))
        xs = [g + (k - 1.5) * genislik for g in grup]
        bar = ax.bar(xs, degerler, width=genislik, color=dolgu,
                     edgecolor=kenar, lw=1.0, label=etiket)
        for b, d in zip(bar, degerler):
            ax.text(b.get_x() + b.get_width() / 2, d + 0.4, str(d),
                    ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(grup)
    ax.set_xticklabels(["Örnek 1 (★)\nad + çıkarma", "Örnek 2 (★★)\n"
                        "koruma cümleleri", "Örnek 4 (★★★)\nparçalama"],
                       fontsize=9)
    ax.set_ylabel("ölçü değeri", fontsize=9.5, color=INK)
    ax.set_title("En karmaşık fonksiyonun ölçümü: önce ve sonra",
                 fontsize=11, color=INK, weight="bold")
    ax.legend(fontsize=8.5, frameon=False, ncol=2, loc="upper right")
    ax.set_ylim(0, 31)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8.5)
    fig.tight_layout()
    return _save(fig, _yol("karmasiklik_olcum"))


# 7. goto ile merkezi cikis: akis ----------------------------------- #
def goto_cikis():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=7.6)
    adimlar = ["fopen", "fread sihir", "fread n", "malloc", "fread veri",
               "fclose; return 0"]
    for i, a in enumerate(adimlar):
        x = 0.3 + i * 2.3
        renk = 1 if i == len(adimlar) - 1 else 0
        _box(ax, x, 5.4, 2.0, 0.8, a, FILL[renk], EDGE[renk], fs=8.6)
        if i < len(adimlar) - 1:
            _arrow(ax, x + 2.0, 5.8, x + 2.3, 5.8, col=ACCENT_L, lw=1.1)
    _box(ax, 4.9, 2.9, 4.2, 0.8, "cik_dosya:  fclose(f);  return durum;",
         FILL[3], EDGE[3], fs=8.6)
    _box(ax, 9.6, 1.1, 4.1, 0.8, "cik_tampon:  free(tampon);",
         FILL[2], EDGE[2], fs=8.6)
    _arrow(ax, 6.0, 5.4, 6.4, 3.7, col=ACCENT, lw=1.1)
    ax.text(3.0, 4.2, "hata: sihir, n, malloc", fontsize=8.2, color=ACCENT)
    _arrow(ax, 10.5, 5.4, 10.5, 1.9, col=ACCENT, lw=1.0)
    ax.text(10.7, 3.6, "veri okunamadı", fontsize=8.2, color=ACCENT)
    _arrow(ax, 9.6, 1.5, 9.1, 3.2, col=ACCENT, lw=1.0, rad=-0.2)
    ax.text(0.4, 1.4, "Tek çıkış noktası: her kaynak tam bir kez\n"
            "serbest bırakılır. Etiket adı yapılacak işi söyler.",
            fontsize=8.8, color=INK, va="center")
    return _save(fig, _yol("goto_cikis"))


if __name__ == "__main__":
    for f in (adlandirma_zihin, koruma_duzlestirme, cfg_alarm,
              guvenlik_dongusu, koku_haritasi, karmasiklik_olcum,
              goto_cikis):
        print(f())
