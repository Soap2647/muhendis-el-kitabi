# -*- coding: utf-8 -*-
"""Bolum 22 - 'Design Patterns' diyagramlari.

Bu bolumde olcum verisi yoktur; tum sekiller bolumdeki kod ve
ornek degerlerden cizilir.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "gorseller")


def _yol(ad):
    return os.path.join(OUT, "b22_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _cizgi(ax, x1, y1, x2, y2, col=MUTED):
    """Kesikli (zayıf) bağlantı: ok ucu olmadan çizgi."""
    ax.plot([x1, x2], [y1, y2], color=col, lw=1.2, ls=(0, (4, 3)))


# 1. Fabrika: kayit tablosu ve arayuz ------------------------------- #
def factory_yapi():
    fig, ax = _tuval(9.6, 4.6, 14, 6.4)
    _box(ax, 4.6, 5.2, 4.8, 0.8, "SensorFabrika.olustur(ad)",
         FILL[0], EDGE[0], fs=10.5, bold=True)
    _box(ax, 0.4, 2.7, 3.6, 1.5,
         "Kayıt tablosu\n\"termistor\" -> Termistor\n\"nem\" -> Nem",
         FILL[2], EDGE[2], fs=9.5)
    _box(ax, 5.6, 2.8, 3.6, 0.9, "Sensor (arayüz)\noku()",
         FILL[1], EDGE[1], fs=10)
    _box(ax, 10.4, 3.9, 3.2, 0.7, "Termistor", FILL[3], EDGE[3], fs=10)
    _box(ax, 10.4, 2.3, 3.2, 0.7, "Nem", FILL[3], EDGE[3], fs=10)
    _arrow(ax, 6.6, 5.2, 6.8, 3.7, col=ACCENT)
    ax.text(7.0, 4.5, "döndürür", fontsize=9, color=INK)
    _arrow(ax, 5.0, 5.2, 2.6, 4.2, col=ACCENT_L)
    ax.text(3.2, 4.9, "ad ile ara", fontsize=9, color=INK)
    _arrow(ax, 9.2, 3.25, 10.4, 4.25, col=ACCENT_L)
    _arrow(ax, 9.2, 3.25, 10.4, 2.65, col=ACCENT_L)
    ax.text(8.7, 4.5, "kalıtım", fontsize=9, color=INK)
    ax.text(7.0, 0.9,
            "Yeni sensör: sınıfı yaz, kayıt ekle. Fabrikanın kodu değişmez.",
            ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("factory_yapi"))


# 2. Builder: zincir ve dogrulama ----------------------------------- #
def builder_akis():
    fig, ax = _tuval(9.6, 3.8, 14, 5.2)
    ax.text(7.0, 4.6, "Her adım kendini döndürür; alanlar tek tek atanır",
            ha="center", fontsize=10.5, color=INK, weight="bold")
    adimlar = ["AyarInsaatcisi()", ".hiz(12)", ".irtifa(120)",
               ".kayit(True)", ".build()"]
    xs = [0.2, 2.9, 5.6, 8.3, 11.0]
    for i, (x, a) in enumerate(zip(xs, adimlar)):
        fill = FILL[0] if i < 4 else FILL[1]
        edge = EDGE[0] if i < 4 else EDGE[1]
        _box(ax, x, 2.6, 2.4, 0.9, a, fill, edge, fs=10)
        if i < 4:
            _arrow(ax, x + 2.4, 3.05, xs[i + 1], 3.05, col=MUTED)
    _box(ax, 10.4, 0.5, 3.2, 1.2,
         "UcusAyar\ndoğrulama: hız 0..30,\nbatarya 0..100",
         FILL[3], EDGE[3], fs=9)
    _arrow(ax, 12.2, 2.6, 12.0, 1.8, col=ACCENT)
    ax.text(3.0, 1.6, "Ara aşamada nesne henüz geçersiz; dışarı verilmez.",
            fontsize=9, color=MUTED)
    return _save(fig, _yol("builder_akis"))


# 3. Singleton: gizli baglanti ve enjeksiyon ------------------------- #
def singleton_di():
    fig, ax = _tuval(9.6, 4.8, 14, 6.6)
    ax.text(3.6, 6.0, "Gizli bağımlılık (singleton)", ha="center",
            fontsize=10.5, color=INK, weight="bold")
    ax.text(10.6, 6.0, "Bağımlılık enjeksiyonu", ha="center",
            fontsize=10.5, color=INK, weight="bold")
    _box(ax, 0.4, 3.6, 2.6, 0.8, "Modül A", FILL[0], EDGE[0], fs=10)
    _box(ax, 0.4, 2.0, 2.6, 0.8, "Modül B", FILL[0], EDGE[0], fs=10)
    _box(ax, 4.4, 2.6, 2.8, 1.4,
         "Yapilandirma\n(tek örnek, global)", FILL[3], EDGE[3], fs=10)
    _arrow(ax, 3.0, 4.0, 4.4, 3.5, col=ACCENT)
    _arrow(ax, 3.0, 2.4, 4.4, 3.0, col=ACCENT)
    ax.text(3.2, 4.2, "doğrudan erişir", fontsize=8.5, color=INK)
    _box(ax, 8.6, 4.4, 3.2, 0.8, "Ana program / test", FILL[1], EDGE[1],
         fs=10)
    _box(ax, 8.6, 2.9, 3.2, 0.8, "Kaydedici(depo)", FILL[1], EDGE[1],
         fs=10)
    _box(ax, 8.6, 1.4, 3.2, 0.8, "depo: gerçek ya da sahte", FILL[2],
         EDGE[2], fs=9.5)
    _arrow(ax, 10.2, 4.4, 10.2, 3.7, col=ACCENT_L)
    ax.text(10.35, 4.0, "enjekte eder", fontsize=8.5, color=INK)
    _arrow(ax, 10.2, 2.9, 10.2, 2.2, col=ACCENT_L)
    ax.text(0.4, 0.6, "Test: her testte yeni, boş depo; sıra bağımsız.",
            fontsize=9, color=MUTED)
    return _save(fig, _yol("singleton_di"))


# 4. Adapter ------------------------------------------------------- #
def adapter_yapi():
    fig, ax = _tuval(9.6, 4.2, 14, 5.8)
    _box(ax, 0.4, 3.4, 2.8, 0.9, "olc(sensor)", FILL[0], EDGE[0], fs=10)
    _box(ax, 4.6, 3.4, 3.0, 0.9, "Sicaklik (hedef)\ncelsius()",
         FILL[1], EDGE[1], fs=10)
    _box(ax, 4.6, 0.7, 3.0, 0.9, "Uyarlayici (adapter)\ncelsius()",
         FILL[3], EDGE[3], fs=9.5)
    _box(ax, 9.6, 0.7, 3.8, 0.9, "EskiSurucu (uyarlanan)\nadc_oku(kanal)",
         FILL[2], EDGE[2], fs=9.5)
    _arrow(ax, 3.2, 3.85, 4.6, 3.85, col=ACCENT)
    _arrow(ax, 6.1, 1.6, 6.1, 3.4, col=ACCENT_L)
    ax.text(6.3, 2.4, "uygular", fontsize=9, color=INK)
    _arrow(ax, 7.6, 1.15, 9.6, 1.15, col=ACCENT_L)
    ax.text(7.8, 1.5, "içinde tutar", fontsize=9, color=INK)
    ax.text(10.5, 2.3, "ham ADC (0..4095)", fontsize=9, color=MUTED)
    return _save(fig, _yol("adapter_yapi"))


# 5. Decorator zinciri -------------------------------------------- #
def decorator_zincir():
    fig, ax = _tuval(9.6, 4.6, 14, 6.2)
    ax.text(7.0, 5.6, "Her katman aynı arayüzü (oku) uygular ve bir alt "
            "katmana sarar", ha="center", fontsize=10, color=INK,
            weight="bold")
    adlar = ["Istemci", "Onbellek", "Olcum", "Yeniden", "Ham (donanım)"]
    notlar = ["ilk değeri saklar", "ic çağrının\nsüresini biriktirir",
              "IOError'da yeniden\ndener", "gerçek okuma"]
    xs = [0.2, 2.9, 5.6, 8.3, 11.0]
    for i, (x, a) in enumerate(zip(xs, adlar)):
        fill = FILL[0] if i == 0 else (FILL[2] if i == 4 else FILL[1])
        edge = EDGE[0] if i == 0 else (EDGE[2] if i == 4 else EDGE[1])
        _box(ax, x, 3.4, 2.4, 0.9, a, fill, edge, fs=10)
        if i < 4:
            _arrow(ax, x + 2.4, 3.95, xs[i + 1], 3.95, col=ACCENT)
            _arrow(ax, xs[i + 1], 3.55, x + 2.4, 3.55, col=MUTED)
            ax.text(x + 1.25 + 0.0, 4.5, "oku()", fontsize=8.5,
                    ha="center", color=INK)
            ax.text(x + 1.25, 3.05, "değer", fontsize=8.5, ha="center",
                    color=MUTED)
        if 1 <= i <= 4:
            ax.text(xs[i] + 1.2, 2.2, notlar[i - 1], fontsize=8.3,
                    ha="center", va="top", color=INK)
    ax.text(7.0, 0.3, "Sarma sırası dışarıdan içeriye: önbellek en dışta "
            "olduğu için tekrar çağrılar ölçülmez.", ha="center",
            fontsize=8.8, color=MUTED)
    return _save(fig, _yol("decorator_zincir"))


# 6. Facade -------------------------------------------------------- #
def facade_yapi():
    fig, ax = _tuval(9.6, 4.6, 14, 6.4)
    _box(ax, 0.4, 2.7, 2.6, 1.0, "Istemci", FILL[0], EDGE[0], fs=10)
    _box(ax, 4.0, 2.7, 3.0, 1.0, "TelemetriFasad\ngonder()", ACCENT_L,
         ACCENT_L, fs=10, tcol="white", bold=True)
    alt = ["Ayristirici.coz()", "Dogrulayici.gecerli_mi()",
           "Sikistirici.paketle()", "Gonderici.yolla()"]
    ys = [4.8, 3.5, 2.2, 0.9]
    for y, a, i in zip(ys, alt, range(4)):
        _box(ax, 8.6, y, 4.8, 0.85, a, FILL[1 + i % 3], EDGE[1 + i % 3],
             fs=10)
        _arrow(ax, 7.0, 3.2, 8.6, y + 0.42, col=MUTED)
    _arrow(ax, 3.0, 3.2, 4.0, 3.2, col=ACCENT)
    ax.text(7.0, 5.9, "İstemci yalnızca fasadı bilir; alt sistemler "
            "değişse de istemci değişmez", ha="center", fontsize=9.5,
            color=INK)
    return _save(fig, _yol("facade_yapi"))


# 7. Strategy ------------------------------------------------------ #
def strategy_yapi():
    fig, ax = _tuval(9.6, 4.6, 14, 6.4)
    _box(ax, 0.4, 2.3, 3.4, 1.5,
         "Filtreleyici (baglam)\nstrateji\nuygula()", FILL[0], EDGE[0],
         fs=9.8)
    _box(ax, 5.2, 2.5, 3.2, 1.0, "Strateji (arayüz)\nf(pencere)",
         FILL[1], EDGE[1], fs=9.8)
    _arrow(ax, 3.8, 3.05, 5.2, 3.0, col=ACCENT)
    ax.text(3.9, 3.35, "kullanır", fontsize=8.5, color=INK)
    for y, a, i in [(4.3, "ortalama", 1), (2.9, "medyan", 2),
                    (1.5, "ustel", 3)]:
        _box(ax, 9.6, y, 3.6, 0.8, a, FILL[i + 1], EDGE[i + 1], fs=10)
        _arrow(ax, 8.4, 3.0, 9.6, y + 0.4, col=ACCENT_L)
    ax.text(7.0, 0.5, "Çalışma zamanında strateji değişir; Bölüm 13'teki "
            "sıralama karşılaştırıcısı aynı fikirdir.", ha="center",
            fontsize=9, color=MUTED)
    return _save(fig, _yol("strategy_yapi"))


# 8. Observer: akis ve zayif referans ------------------------------ #
def observer_akis():
    fig, ax = _tuval(9.6, 4.8, 14, 6.4)
    _box(ax, 0.4, 2.6, 3.2, 1.3, "Konu\nbildir(değer)", FILL[0], EDGE[0],
         fs=10.5, bold=True)
    _box(ax, 8.4, 4.4, 3.8, 0.8, "Alarm: kritik (eşik 80)", FILL[1],
         EDGE[1], fs=10)
    _box(ax, 8.4, 2.6, 3.8, 0.8, "Alarm: geçici (eşik 0)", FILL[1],
         EDGE[1], fs=10)
    _box(ax, 8.4, 0.8, 3.8, 0.8, "silinmiş gözlemci", "white", RULE,
         fs=10, tcol=MUTED)
    _arrow(ax, 3.6, 3.5, 8.4, 4.8, col=ACCENT, rad=0.0)
    _arrow(ax, 3.6, 3.2, 8.4, 3.0, col=ACCENT)
    _cizgi(ax, 3.6, 3.0, 8.4, 1.2, col=MUTED)
    ax.text(6.4, 1.2, "zayıf referans\n(ölü ise atlanır)", fontsize=8.5,
            color=MUTED, ha="center")
    ax.text(4.6, 4.75, "bildirim (olay)", fontsize=9, color=INK)
    ax.text(7.0, 0.1, "Bildirim sırasında kopya üzerinde gezilir; "
            "abonelik değişse de liste bozulmaz.", ha="center",
            fontsize=8.8, color=MUTED)
    return _save(fig, _yol("observer_akis"))


# 9. Command: geri al ve yinele yiginlari ------------------------- #
def command_yigin():
    fig, ax = _tuval(9.6, 4.8, 14, 6.4)
    ax.text(3.0, 5.7, "Geri al yığını", ha="center", fontsize=10.5,
            color=INK, weight="bold")
    ax.text(11.0, 5.7, "Yinele (ileri) yığını", ha="center", fontsize=10.5,
            color=INK, weight="bold")
    geri = ["ekle(Merhaba)", "ekle( dunya)"]
    ileri = ["sil(5)"]
    for i, s in enumerate(geri):
        _box(ax, 0.8, 0.6 + i * 0.9, 4.4, 0.75, s, FILL[1], EDGE[1],
             fs=10)
    ax.text(0.8, 2.55, "tepe ↑", fontsize=9, color=MUTED)
    for i, s in enumerate(ileri):
        _box(ax, 8.8, 0.6 + i * 0.9, 4.4, 0.75, s, FILL[2], EDGE[2],
             fs=10)
    _box(ax, 5.2, 4.2, 3.6, 0.9, "metin = \"Merhaba dunya\"", FILL[0],
         EDGE[0], fs=9.8)
    _arrow(ax, 5.4, 2.0, 8.6, 2.0, col=ACCENT, rad=-0.25)
    ax.text(7.0, 2.85, "geri(): tepeyi çek, geri_al(),\nileri yığınına it",
            ha="center", fontsize=8.8, color=INK)
    _arrow(ax, 8.6, 1.2, 5.4, 1.2, col=ACCENT_L, rad=-0.25)
    ax.text(7.0, 0.35, "yinele(): tersi", ha="center", fontsize=8.8,
            color=INK)
    return _save(fig, _yol("command_yigin"))


# 10. State: IHA ucus modlari --------------------------------------- #
def state_ucus():
    fig, ax = _tuval(9.6, 4.8, 14, 6.4)
    xs = [0.8, 4.2, 7.6, 11.0]
    adlar = ["YERDE", "KALKIS", "SEYIR", "INIS"]
    for i, (x, a) in enumerate(zip(xs, adlar)):
        _box(ax, x, 2.6, 2.6, 1.0, a, FILL[i], EDGE[i], fs=11, bold=True)
    olaylar = ["kalkis_emri", "irtifa_ulasti", "inis_emri"]
    for i, o in enumerate(olaylar):
        _arrow(ax, xs[i] + 2.6, 3.1, xs[i + 1], 3.1, col=ACCENT)
        ax.text(xs[i] + 3.4, 3.8, o, ha="center", fontsize=8.8, color=INK)
    _arrow(ax, 12.3, 2.6, 2.1, 2.6, col=ACCENT_L, rad=-0.28)
    ax.text(7.0, 0.75, "pist_temas", ha="center", fontsize=9, color=INK)
    _box(ax, 0.2, 4.9, 4.4, 0.7, "X: YERDE + inis_emri reddedilir",
         "white", ACCENT, fs=9, tcol=ACCENT)
    ax.plot([2.4, 2.4], [4.9, 3.6], color=ACCENT, lw=1.2, ls=(0, (4, 3)))
    ax.text(7.0, 5.7, "Geçersiz geçiş hata verir ve durum değişmez",
            ha="center", fontsize=9.5, color=MUTED)
    return _save(fig, _yol("state_ucus"))


# 11. Kalip secim karar agaci --------------------------------------- #
def karar_agaci():
    fig, ax = _tuval(9.6, 6.2, 14, 8.6)
    _box(ax, 0.4, 4.6, 2.6, 1.2, "Hangi sorun?", FILL[0], EDGE[0],
         fs=11, bold=True)
    dallar = [
        ("Nesne nasıl kurulur?", 4.85 + 2.25, [
            ("çok parametre: Builder", 7.6),
            ("tür seçimi: Factory", 6.85),
            ("tek örnek: DI (singleton değil)", 6.1)]),
        ("Arayüz ve yapı\nnasıl bağlanır?", 4.85, [
            ("uyumsuz arayüz: Adapter", 5.1),
            ("ek davranış sarma: Decorator", 4.35),
            ("karmaşık alt sistem: Facade", 3.6)]),
        ("Davranış nasıl değişir?", 2.025, [
            ("algoritma değişimi: Strategy", 2.9),
            ("olay bildirimi: Observer", 2.15),
            ("geri al / yinele: Command", 1.4),
            ("durum geçişleri: State", 0.65)]),
    ]
    for d, (metin, cy, yaprak) in enumerate(dallar):
        _box(ax, 3.8, cy - 0.5, 3.4, 1.0, metin, FILL[d + 1],
             EDGE[d + 1], fs=9.5)
        _arrow(ax, 3.0, 5.2, 3.8, cy, col=MUTED)
        for k, (yt, yy) in enumerate(yaprak):
            _box(ax, 8.0, yy, 5.6, 0.5, yt, "white", EDGE[d + 1], fs=9.5)
            _arrow(ax, 7.2, cy, 8.0, yy + 0.25, col=MUTED)
    return _save(fig, _yol("karar_agaci"))


if __name__ == "__main__":
    for f in (factory_yapi, builder_akis, singleton_di, adapter_yapi,
              decorator_zincir, facade_yapi, strategy_yapi, observer_akis,
              command_yigin, state_ucus, karar_agaci):
        print(f())
