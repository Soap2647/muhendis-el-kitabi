# -*- coding: utf-8 -*-
"""Bölüm 41 - 'System Design' diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV dosyalarını okur:
  b41_yuk_dengeleme.csv  yük dengeleme politikaları, p99 - rho
  b41_pot.csv            100 sunucuda rastgele ve iki seçim
  b41_mm1.csv            M/M/1 teorik ve ölçülen W
  b41_jitter.csv         yeniden deneme istek sayımı (100 ms kova)
Diğer şekiller bölümdeki değerlerden çizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b41_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. Tasarım süreci ----------------------------------------------------- #
def tasarim_sureci():
    fig, ax = _tuval(9.6, 3.6, xl=14, yl=5)
    adimlar = ["1. Gereksinim", "2. Kısıt ve\nölçek", "3. Tahmin",
               "4. Üst düzey\ntasarım", "5. Derin dalış",
               "6. Darboğaz ve\ntakas"]
    xs = [0.3, 2.6, 4.9, 7.2, 9.5, 11.8]
    for x, metin in zip(xs, adimlar):
        _box(ax, x, 2.3, 2.0, 1.2, metin, FILL[0], EDGE[0], fs=9.5)
    for i in range(len(xs) - 1):
        _arrow(ax, xs[i] + 2.0, 2.9, xs[i + 1], 2.9, col=MUTED, lw=1.2)
    ax.plot([12.8, 12.8, 8.2], [3.55, 4.25, 4.25], color=ACCENT, lw=1.2)
    _arrow(ax, 8.2, 4.25, 8.2, 3.55, col=ACCENT, lw=1.2)
    ax.text(10.5, 4.45, "takas değişirse geri dön", ha="center",
            fontsize=8.5, color=ACCENT)
    ax.text(7.0, 1.4, "Her adım somut bir sayı ister: istek/s, p99 "
            "gecikme (ms), kabul edilen hata oranı.", ha="center",
            fontsize=9, color=INK)
    return _save(fig, _yol("tasarim_sureci"))


# 2. Seri ve paralel kullanılabilirlik ---------------------------------- #
def kullanilabilirlik():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.2)
    ax.text(0.3, 6.8, "Seri: üç bileşen, her biri 0,999 (hepsi çalışmalı)",
            fontsize=10, color=INK, weight="bold")
    xs = [0.4, 4.6, 8.8]
    for x, m in zip(xs, ["A  0,999", "B  0,999", "C  0,999"]):
        _box(ax, x, 5.0, 3.0, 1.0, m, FILL[0], EDGE[0], fs=10)
    _arrow(ax, 3.4, 5.5, 4.6, 5.5, col=MUTED)
    _arrow(ax, 7.6, 5.5, 8.8, 5.5, col=MUTED)
    ax.text(0.4, 4.2, "toplam = 0,999 x 0,999 x 0,999 = 0,99700",
            fontsize=9.5, color=ACCENT)

    ax.text(0.3, 3.4, "Paralel: iki kopya, her biri 0,99 (biri yeter)",
            fontsize=10, color=INK, weight="bold")
    _box(ax, 0.4, 0.8, 2.4, 1.0, "İstek", FILL[2], EDGE[2], fs=10)
    _box(ax, 4.4, 1.9, 3.0, 0.9, "Kopya 1  0,99", FILL[1], EDGE[1],
         fs=10)
    _box(ax, 4.4, 0.4, 3.0, 0.9, "Kopya 2  0,99", FILL[1], EDGE[1],
         fs=10)
    _box(ax, 9.4, 1.2, 2.6, 0.9, "Yanıt", FILL[2], EDGE[2], fs=10)
    _arrow(ax, 2.8, 1.3, 4.4, 2.35, col=MUTED)
    _arrow(ax, 2.8, 1.1, 4.4, 0.85, col=MUTED)
    _arrow(ax, 7.4, 2.35, 9.4, 1.8, col=MUTED)
    _arrow(ax, 7.4, 0.85, 9.4, 1.5, col=MUTED)
    ax.text(0.4, 0.0, "1 - (1 - 0,99)^2 = 0,9999", fontsize=9.5,
            color=ACCENT)
    return _save(fig, _yol("kullanilabilirlik"))


# 3. Kapasite tahmin tablosu ------------------------------------------- #
def kapasite_tablo():
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    ax.axis("off")
    satirlar = [
        ["Paket/s (filo)", "40 İHA x 100 Hz", "4 000 /s"],
        ["Ham bayt/s", "4 000 x 256 bayt", "1,024 MB/s"],
        ["Ham bit/s", "1,024 MB/s x 8", "8,19 Mbit/s"],
        ["Tepe (2 kat)", "8,19 x 2", "16,38 Mbit/s"],
        ["Ham depolama/gün", "1,024 MB/s x 86 400 s", "88,5 GB"],
        ["Sıkıştırılmış/gün", "88,5 / 5 (varsayım)", "17,7 GB"],
        ["Sıkıştırılmış/yıl", "17,7 x 365", "6,5 TB"],
        ["Paket başı süre bütçesi", "1 / 4 000 s", "250 µs"],
    ]
    tablo = ax.table(cellText=satirlar,
                     colLabels=["Ölçü", "Hesap", "Sonuç"],
                     loc="center", cellLoc="left",
                     colWidths=[0.34, 0.38, 0.22])
    tablo.auto_set_font_size(False)
    tablo.set_fontsize(9.5)
    tablo.scale(1.0, 1.55)
    for (r, c), hucre in tablo.get_celld().items():
        hucre.set_edgecolor(RULE)
        if r == 0:
            hucre.set_facecolor(FILL[0])
            hucre.get_text().set_weight("bold")
            hucre.get_text().set_color(INK)
        else:
            hucre.set_facecolor("white")
            hucre.get_text().set_color(INK)
    return _save(fig, _yol("kapasite_tablo"))


# 4. Yük dengeleme: p99 - rho ve iki seçim ----------------------------- #
POL = [("rr", "sırayla (rr)", MUTED, "o"),
       ("wrr", "ağırlıklı", EDGE[0], "s"),
       ("rastgele", "rastgele", EDGE[2], "^"),
       ("enaz", "en az bağlantı", ACCENT, "D"),
       ("pot", "iki seçimin gücü (d=2)", EDGE[1], "v"),
       ("erken", "en erken bitiş (bilgi)", EDGE[4], "P")]


def yuk_dengeleme():
    veri = _oku_csv("b41_yuk_dengeleme.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                 gridspec_kw={"width_ratios": [1.6, 1]})
    for kod, ad, renk, mark in POL:
        s = [r for r in veri if r["politika"] == kod]
        rho = [float(r["rho"]) for r in s]
        p99 = [float(r["p99"]) for r in s]
        a1.plot(rho, p99, color=renk, marker=mark, ms=4.5, lw=1.4,
                label=ad)
    a1.set_yscale("log")
    a1.set_xlabel("yük oranı rho (toplam hıza göre)", color=INK)
    a1.set_ylabel("p99 gecikme (birim iş, log)", color=INK)
    a1.set_title("Heterojen küme (hızlar 1,1,1,1,2,2,0,5,0,5)",
                 fontsize=9.2, color=INK)
    a1.axvline(0.444, color=MUTED, ls="--", lw=0.9)
    a1.text(0.455, 120, "rr ve rastgele\nrho > 0,44 için kararsız",
            fontsize=7.5, color=MUTED)
    a1.legend(loc="upper left", fontsize=6.8, frameon=False)

    pot = _oku_csv("b41_pot.csv")
    ad = {"rastgele": "rastgele", "pot": "iki seçim (d=2)"}
    x = np.arange(len(pot))
    kuy = [int(r["maks_k"]) for r in pot]
    a2.bar(x, kuy, color=[EDGE[2], EDGE[1]], width=0.5)
    for i, v in enumerate(kuy):
        a2.text(i, v + 1.2, str(v), ha="center", fontsize=8.5,
                color=INK)
    a2.set_xticks(x)
    a2.set_xticklabels([ad[r["politika"]] for r in pot], fontsize=8)
    a2.set_ylabel("en uzun kuyruk (iş sayısı)", color=INK)
    a2.set_title("100 sunucu, rho = 0,9", fontsize=9.2, color=INK)
    for a in (a1, a2):
        a.grid(True, which="both", color=RULE, lw=0.6)
        for s in a.spines.values():
            s.set_color(MUTED)
    fig.tight_layout()
    return _save(fig, _yol("yuk_dengeleme"))


# 5. Önbellek katmanları ----------------------------------------------- #
def onbellek_katman():
    fig, ax = _tuval(9.6, 3.8, xl=14, yl=5.4)
    adlar = ["İstemci\nönbelleği", "CDN\n(kenar)", "Ters vekil\nönbellek",
             "Uygulama\nönbelleği", "Veritabanı"]
    gec = ["yerel: 0 ms", "coğrafi: ms\nmertebesi", "~1 ms (tipik)",
           "~0,5 ms (ağ, tipik)", "~20 ms (varsayım)"]
    renk = [FILL[1], FILL[1], FILL[2], FILL[2], FILL[3]]
    kenar = [EDGE[1], EDGE[1], EDGE[2], EDGE[2], EDGE[3]]
    xs = [0.3, 3.0, 5.7, 8.4, 11.1]
    for x, a, r, k in zip(xs, adlar, renk, kenar):
        _box(ax, x, 2.6, 2.3, 1.4, a, r, k, fs=9)
    for i in range(4):
        _arrow(ax, xs[i] + 2.3, 3.3, xs[i + 1], 3.3, col=MUTED, lw=1.2)
    for x, g in zip(xs, gec):
        ax.text(x + 1.15, 1.8, g, ha="center", va="center", fontsize=8,
                color=INK)
    ax.text(7.0, 0.7, "Sistemin ortasına inen her isabet, arkadaki "
            "katmanın yükünü azaltır.", ha="center", fontsize=9,
            color=ACCENT)
    return _save(fig, _yol("onbellek_katman"))


# 6. M/M/1 gecikme - kullanım ------------------------------------------ #
def mm1_egri():
    veri = _oku_csv("b41_mm1.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    rho = np.linspace(0.01, 0.985, 400)
    ax.plot(rho, 1 / (1 - rho), color=MUTED, lw=1.6,
            label="teorik  W = 1 / (1 - rho)")
    rr = [float(r["rho"]) for r in veri]
    wo = [float(r["w_olculen"]) for r in veri]
    ax.plot(rr, wo, "o", color=ACCENT, ms=7, label="simülasyon (ölçülen)")
    for x, y in zip(rr, wo):
        ax.annotate("%.2f: %.1f" % (x, y), (x, y), textcoords="offset "
                    "points", xytext=(8, -4), fontsize=8.5, color=INK)
    ax.set_yscale("log")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.8, 300)
    ax.set_xlabel("kullanım oranı rho = lambda / mu", color=INK)
    ax.set_ylabel("ortalama sistemdeki süre W (birim hizmet, log)",
                  color=INK, fontsize=9)
    ax.grid(True, which="both", color=RULE, lw=0.6)
    ax.legend(loc="upper left", fontsize=8.5, frameon=False)
    for s in ax.spines.values():
        s.set_color(MUTED)
    fig.tight_layout()
    return _save(fig, _yol("mm1_egri"))


# 7. Retry + jitter: sürü etkisi --------------------------------------- #
def jitter_surusu():
    veri = _oku_csv("b41_jitter.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    seri = [("sabit", "sabit geri çekilme (jitter yok)", ACCENT, "-"),
            ("tam", "tam jitter", EDGE[0], "--"),
            ("ayrisik", "ayrışık jitter", EDGE[1], ":")]
    for kod, ad, renk, stil in seri:
        s = [r for r in veri if r["strateji"] == kod]
        t = [float(r["zaman_s"]) for r in s]
        y = [int(r["istek_100ms"]) for r in s]
        ax.plot(t, y, color=renk, ls=stil, lw=1.6, label=ad)
    ax.axvline(2.0, color=MUTED, lw=0.9)
    ax.text(2.2, 880, "sunucu açılır", fontsize=8.5, color=MUTED)
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 1150)
    ax.set_xlabel("zaman (s)", color=INK)
    ax.set_ylabel("istek sayısı / 100 ms", color=INK)
    ax.grid(True, color=RULE, lw=0.6)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False)
    for s in ax.spines.values():
        s.set_color(MUTED)
    fig.tight_layout()
    return _save(fig, _yol("jitter_surusu"))


# 8. Devre kesici durum makinesi --------------------------------------- #
def devre_kesici():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.4)
    _box(ax, 0.4, 2.8, 3.6, 1.8, "KAPALI\nİstek geçer,\nhatalar sayılır",
         FILL[1], EDGE[1], fs=9.5, bold=True)
    _box(ax, 9.4, 4.9, 4.2, 1.9, "AÇIK\nİstek reddedilir\n(hızlı hata)",
         FILL[3], EDGE[3], fs=9.5, bold=True)
    _box(ax, 9.4, 0.7, 4.2, 1.9, "YARI AÇIK\nTek deneme isteği",
         FILL[2], EDGE[2], fs=9.5, bold=True)
    _arrow(ax, 4.0, 4.1, 9.4, 5.6, col=ACCENT, rad=0.0)
    ax.text(5.2, 5.6, "ardışık hata ≥ eşik", fontsize=8.5,
            color=ACCENT)
    _arrow(ax, 11.5, 4.9, 11.5, 2.6, col=ACCENT, rad=0.0)
    ax.text(11.7, 3.7, "bekleme süresi doldu", fontsize=8.5,
            color=ACCENT)
    _arrow(ax, 9.4, 1.5, 4.0, 3.5, col=MUTED, rad=0.0)
    ax.text(5.4, 1.45, "deneme başarılı: sayaç sıfırlanır", fontsize=8.5,
            color=INK)
    _arrow(ax, 10.2, 2.6, 10.2, 4.9, col=MUTED, rad=0.0)
    ax.text(10.0, 3.75, "deneme hata", fontsize=8, color=MUTED,
            ha="right")
    return _save(fig, _yol("devre_kesici"))


# 9. URL kısaltıcı mimarisi -------------------------------------------- #
def url_kisaltici():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.4)
    _box(ax, 0.3, 4.6, 2.2, 1.2, "İstemci", FILL[0], EDGE[0], fs=10)
    _box(ax, 3.2, 4.6, 2.4, 1.2, "Yük dengeleyici", FILL[0], EDGE[0],
         fs=9.5)
    _box(ax, 6.3, 4.6, 2.4, 1.2, "Uygulama\n(durumsuz) x n", FILL[1],
         EDGE[1], fs=9.5)
    _box(ax, 10.6, 5.6, 3.2, 1.1, "ID üretici (Snowflake)", FILL[2],
         EDGE[2], fs=9)
    _box(ax, 10.6, 3.6, 3.2, 1.1, "Önbellek (LRU / Redis)", FILL[2],
         EDGE[2], fs=9)
    _box(ax, 10.6, 1.6, 3.2, 1.1, "Veritabanı: kod -> URL", FILL[3],
         EDGE[3], fs=9)
    _arrow(ax, 2.5, 5.2, 3.2, 5.2, col=MUTED)
    _arrow(ax, 5.6, 5.2, 6.3, 5.2, col=MUTED)
    _arrow(ax, 8.7, 5.6, 10.6, 6.1, col=MUTED)
    _arrow(ax, 8.7, 5.2, 10.6, 4.1, col=MUTED)
    _arrow(ax, 8.7, 4.8, 10.6, 2.2, col=MUTED)
    ax.text(0.3, 2.9, "GET /aB3x  ->  yönlendirme (301 / 302)\n"
            "Location: uzun URL", fontsize=9, color=INK)
    ax.text(0.3, 1.5, "Okuma ağırlıklı: yazma seyrek, önbellek isabeti\n"
            "veritabanı yükünü düşürür.", fontsize=9, color=ACCENT)
    return _save(fig, _yol("url_kisaltici"))


# 10. İHA telemetri sistemi --------------------------------------------- #
def iha_telemetri():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.6)
    _box(ax, 0.2, 2.6, 3.4, 4.0, "", FILL[0], EDGE[0])
    ax.text(1.9, 6.25, "İHA (uç)", ha="center", fontsize=10,
            weight="bold", color=INK)
    _box(ax, 0.4, 4.3, 3.0, 0.9, "Sensörler\n(IMU, GPS, motor)",
         FILL[0], EDGE[0], fs=8.5)
    _box(ax, 0.4, 2.9, 3.0, 0.9, "Tampon + WAL\n(kayıp önleme)",
         FILL[1], EDGE[1], fs=8.5)
    _box(ax, 5.4, 2.6, 3.4, 4.0, "", FILL[1], EDGE[1])
    ax.text(7.1, 6.25, "Yer istasyonu", ha="center", fontsize=10,
            weight="bold", color=INK)
    ax.text(7.1, 4.6, "birleştirme (sıra, tekrar)\ngerçek zamanlı "
            "önbellek\nson değer, kısa TTL", ha="center", va="center",
            fontsize=8.5, color=INK)
    _box(ax, 10.4, 2.6, 3.4, 4.0, "", FILL[2], EDGE[2])
    ax.text(12.1, 6.25, "Merkez", ha="center", fontsize=10,
            weight="bold", color=INK)
    ax.text(12.1, 4.6, "zaman serisi deposu\ndownsampling\nsaklama "
            "politikası", ha="center", va="center", fontsize=8.5,
            color=INK)
    _arrow(ax, 3.6, 5.6, 5.4, 5.6, col=ACCENT, lw=1.6)
    ax.text(4.5, 6.0, "telemetri", ha="center", fontsize=8,
            color=ACCENT)
    ax.text(4.5, 5.2, "kayıp olabilir", ha="center", fontsize=7.5,
            color=ACCENT)
    _arrow(ax, 8.8, 5.6, 10.4, 5.6, col=ACCENT, lw=1.6)
    ax.text(9.6, 6.0, "arşiv", ha="center", fontsize=8, color=ACCENT)
    _arrow(ax, 5.4, 3.4, 3.6, 3.4, col=MUTED, lw=1.2)
    ax.text(4.5, 3.75, "komut", ha="center", fontsize=8, color=MUTED)
    ax.text(4.5, 2.95, "kimlik, onay,\nzaman aşımı", ha="center",
            va="center", fontsize=7.5, color=MUTED)
    ax.text(7.0, 1.4, "Telemetri kaybolabilir; komut kanalı ayrı ve "
            "onaylıdır.", ha="center", fontsize=9, color=INK)
    return _save(fig, _yol("iha_telemetri"))


def main():
    yollar = [tasarim_sureci(), kullanilabilirlik(), kapasite_tablo(),
              yuk_dengeleme(), onbellek_katman(), mm1_egri(),
              jitter_surusu(), devre_kesici(), url_kisaltici(),
              iha_telemetri()]
    for y in yollar:
        print(y)


if __name__ == "__main__":
    main()
