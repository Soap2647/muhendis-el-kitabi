# -*- coding: utf-8 -*-
"""Bolum 32 - 'Guvenlik' diyagramlari.

Tum sekiller kavramsaldir: savunma kavramlarini gosterir, saldiri
adimi icermez. Olcum verisi okumazlar; sayisal sonuclar ilgili
bolumde terminal ciktilariyla verilir.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")


def _yol(ad):
    return os.path.join(OUT, "b32_%s.png" % ad)


def _tuval(w, h, xl=14, yl=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. CIA ve tamamlayicilar ------------------------------------------ #
def cia():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=7.6)
    ax.text(7, 7.2, "Temel üçlü (CIA)", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ust = [("Gizlilik", "confidentiality", "yetkisiz okunamaz"),
           ("Bütünlük", "integrity", "yetkisiz değiştirilemez"),
           ("Erişilebilirlik", "availability", "yetkiliye açık kalır")]
    for i, (tr, en, aciklama) in enumerate(ust):
        x = 0.6 + i * 4.5
        _box(ax, x, 4.8, 4.0, 1.5, "%s\n(%s)" % (tr, en), FILL[0],
             EDGE[0], fs=10, bold=True)
        ax.text(x + 2.0, 4.4, aciklama, ha="center", fontsize=8.8,
                color=MUTED)
    ax.text(7, 3.6, "Tamamlayıcı özellikler", ha="center",
            fontsize=10.5, weight="bold", color=INK)
    alt = [("Kimlik doğrulama", "authentication"),
           ("Yetkilendirme", "authorization"),
           ("İnkâr edilemezlik", "non-repudiation")]
    for i, (tr, en) in enumerate(alt):
        x = 0.6 + i * 4.5
        _box(ax, x, 1.7, 4.0, 1.4, "%s\n(%s)" % (tr, en), FILL[1],
             EDGE[1], fs=10)
    ax.text(7, 0.9, "Bir sistem bu altı özelliği birlikte sağlamadıkça "
            "güvenli sayılmaz.", ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("cia"))


# 2. Derinlemesine savunma ------------------------------------------ #
def katmanlar():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.6)
    seviyeler = [
        ("Ağ çevresi: port kısıtı, güvenlik duvarı, hız sınırı", FILL[0],
         EDGE[0]),
        ("Protokol: sürüm, sıra numarası, HMAC/AEAD", FILL[1], EDGE[1]),
        ("Uygulama: girdi doğrulama, yol denetimi, kaçış", FILL[2],
         EDGE[2]),
        ("Bellek: sınır denetimi, derleyici ve OS korumaları", FILL[3],
         EDGE[3]),
        ("Veri: en az ayrıcalık, şifreleme, günlük", FILL[4], EDGE[4]),
    ]
    for i, (metin, dolgu, kenar) in enumerate(seviyeler):
        inset = 0.35 + i * 0.85
        p_x, p_y = inset, inset
        p_w, p_h = 14 - 2 * inset, 8.6 - 2 * inset
        _box(ax, p_x, p_y, p_w, p_h, "", dolgu, kenar, fs=8)
        ax.text(p_x + 0.25, 8.6 - inset - 0.3, metin, fontsize=8.8,
                color=INK, va="center")
    ax.text(7.0, 4.25, "Korunan varlık: telemetri · komut · anahtar",
            ha="center", va="center", fontsize=9.6, weight="bold",
            color=INK)
    return _save(fig, _yol("katmanlar"))


# 3. Tuzlu KDF ile parola saklama ----------------------------------- #
def parola():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=8.2)
    ax.text(0.3, 7.7, "Kayıt", fontsize=10, weight="bold", color=INK)
    _box(ax, 0.4, 6.0, 2.4, 0.9, "parola", FILL[0], EDGE[0], fs=9.6)
    _box(ax, 3.6, 6.0, 2.4, 0.9, "rastgele tuz\n(16 bayt)", FILL[1],
         EDGE[1], fs=8.8)
    _box(ax, 6.8, 6.0, 2.8, 0.9, "KDF (scrypt)\nn, r, p", FILL[2],
         EDGE[2], fs=8.8)
    _box(ax, 10.6, 6.0, 3.1, 0.9, "kayıt: tuz + özet", FILL[4],
         EDGE[4], fs=9.2)
    _arrow(ax, 2.8, 6.45, 3.6, 6.45, col=ACCENT_L)
    _arrow(ax, 6.0, 6.45, 6.8, 6.45, col=ACCENT_L)
    _arrow(ax, 9.6, 6.45, 10.6, 6.45, col=ACCENT_L)
    ax.text(0.3, 4.6, "Doğrulama", fontsize=10, weight="bold", color=INK)
    _box(ax, 0.4, 2.9, 2.4, 0.9, "girilen parola", FILL[0], EDGE[0],
         fs=9.2)
    _box(ax, 3.6, 2.9, 2.4, 0.9, "kayıttaki tuz", FILL[1], EDGE[1],
         fs=9.2)
    _box(ax, 6.8, 2.9, 2.8, 0.9, "KDF (aynı n, r, p)", FILL[2],
         EDGE[2], fs=8.8)
    _box(ax, 10.6, 2.9, 3.1, 0.9, "sabit zamanlı karşılaştır", FILL[3],
         EDGE[3], fs=8.8)
    _arrow(ax, 2.8, 3.35, 3.6, 3.35, col=ACCENT_L)
    _arrow(ax, 6.0, 3.35, 6.8, 3.35, col=ACCENT_L)
    _arrow(ax, 9.6, 3.35, 10.6, 3.35, col=ACCENT_L)
    ax.text(12.15, 2.2, "eşleşti: kabul\nfarklı: red", ha="center",
            fontsize=8.6, color=MUTED, va="top")
    ax.text(0.3, 1.2, "Tuz gizli değildir; amacı aynı parolaların aynı "
            "özeti vermesini engellemektir.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("parola"))


# 4. HMAC ile butunluk ---------------------------------------------- #
def hmac():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=7.6)
    ax.text(0.3, 6.9, "Gönderen", fontsize=10, weight="bold", color=INK)
    _box(ax, 0.4, 5.2, 2.6, 0.9, "gövde (24 bayt)", FILL[0], EDGE[0],
         fs=9.2)
    _box(ax, 0.4, 3.7, 2.6, 0.9, "anahtar K", FILL[3], EDGE[3], fs=9.2)
    _box(ax, 4.0, 4.4, 2.6, 1.2, "HMAC-SHA256", FILL[2], EDGE[2],
         fs=9.6, bold=True)
    _box(ax, 7.6, 4.6, 2.2, 0.8, "etiket (16 bayt)", FILL[1], EDGE[1],
         fs=8.8)
    _arrow(ax, 3.0, 5.65, 4.0, 5.1, col=ACCENT_L)
    _arrow(ax, 3.0, 4.15, 4.0, 4.7, col=ACCENT_L)
    _arrow(ax, 6.6, 5.0, 7.6, 5.0, col=ACCENT_L)
    ax.text(0.3, 2.6, "Alıcı", fontsize=10, weight="bold", color=INK)
    _box(ax, 0.4, 0.9, 2.6, 0.9, "gelen gövde", FILL[0], EDGE[0],
         fs=9.2)
    _box(ax, 4.0, 0.9, 2.6, 0.9, "aynı K ile HMAC", FILL[2], EDGE[2],
         fs=9.0)
    _box(ax, 7.6, 0.9, 2.6, 0.9, "karşılaştır", FILL[4], EDGE[4],
         fs=9.2)
    _box(ax, 11.0, 0.9, 2.7, 0.9, "kabul / red", FILL[1], EDGE[1],
         fs=9.2)
    _arrow(ax, 3.0, 1.35, 4.0, 1.35, col=ACCENT_L)
    _arrow(ax, 6.6, 1.35, 7.6, 1.35, col=ACCENT_L)
    _arrow(ax, 10.2, 1.35, 11.0, 1.35, col=ACCENT_L)
    _arrow(ax, 8.9, 4.6, 8.9, 1.8, col=MUTED, lw=1.1, style="-")
    ax.text(9.1, 3.1, "gelen etiket", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("hmac"))


# 5. AEAD girdileri ve ciktilari ------------------------------------ #
def aead():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=7.8)
    girdiler = [("anahtar K (gizli)", FILL[3], EDGE[3]),
                ("nonce N (benzersiz, 96 bit)", FILL[0], EDGE[0]),
                ("düz metin P (gizli)", FILL[2], EDGE[2]),
                ("ek veri A (doğrulanır)", FILL[1], EDGE[1])]
    for i, (metin, dolgu, kenar) in enumerate(girdiler):
        _box(ax, 0.4, 6.0 - i * 1.35, 3.8, 0.95, metin, dolgu, kenar,
             fs=8.8)
    _box(ax, 5.2, 3.4, 3.3, 1.8, "AEAD\nşifrele + doğrula", FILL[4],
         ACCENT, fs=10, bold=True)
    for i in range(4):
        y = 6.0 - i * 1.35 + 0.47
        _arrow(ax, 4.2, y, 5.2, 4.3 if i < 2 else 4.2, col=ACCENT_L,
               lw=1.0)
    _box(ax, 9.6, 5.3, 4.0, 1.0, "şifreli metin C\n(|P| bayt)", FILL[2],
         EDGE[2], fs=9.0)
    _box(ax, 9.6, 3.6, 4.0, 1.0, "etiket T\n(16 bayt)", FILL[1],
         EDGE[1], fs=9.0)
    _arrow(ax, 8.5, 4.6, 9.6, 5.8, col=ACCENT_L)
    _arrow(ax, 8.5, 4.2, 9.6, 4.1, col=ACCENT_L)
    ax.text(0.4, 0.9, "Çözme: C, T, N, A, K girdileri. T tutmazsa hiçbir "
            "düz metin üretilmez.", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("aead"))


# 6. TLS 1.3 el sikismasi (kavramsal) ------------------------------- #
def tls_el():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=9.2)
    ax.text(2.6, 8.8, "İstemci", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ax.text(11.4, 8.8, "Sunucu", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ax.plot([2.6, 2.6], [1.0, 8.4], color=RULE, lw=1.2, ls="--")
    ax.plot([11.4, 11.4], [1.0, 8.4], color=RULE, lw=1.2, ls="--")
    adimlar = [
        (7.6, "ClientHello: sürümler, şifre takımları, key_share", "sag"),
        (6.5, "ServerHello: seçilen şifre, key_share", "sol"),
        (5.3, "Sertifika, CertificateVerify, Finished (şifreli)", "sol"),
        (4.2, "Finished (şifreli)", "sag"),
        (3.0, "Uygulama verisi (şifreli, doğrulanmış)", "cift"),
    ]
    for y, metin, yon in adimlar:
        if yon == "sag":
            _arrow(ax, 2.7, y, 11.3, y, col=ACCENT_L)
            ax.text(7.0, y + 0.22, metin, ha="center", fontsize=8.6,
                    color=INK)
        elif yon == "sol":
            _arrow(ax, 11.3, y, 2.7, y, col=ACCENT_L)
            ax.text(7.0, y + 0.22, metin, ha="center", fontsize=8.6,
                    color=INK)
        else:
            _arrow(ax, 2.7, y, 11.3, y, col=ACCENT_L, style="<|-|>")
            ax.text(7.0, y + 0.22, metin, ha="center", fontsize=8.6,
                    color=INK)
    ax.text(7.0, 1.5, "Anahtar paylaşımı (ECDHE) ve doğrulama, tek bir "
            "gidiş-dönüşte (1-RTT) yapılır.", ha="center", fontsize=8.6,
            color=MUTED)
    return _save(fig, _yol("tls_el"))


# 7. Sertifika zinciri ---------------------------------------------- #
def zincir():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.2)
    _box(ax, 0.4, 4.6, 4.2, 1.5, "Kök CA\n(güvenilen depoda)", FILL[0],
         EDGE[0], fs=9.6, bold=True)
    _box(ax, 4.9, 4.6, 4.2, 1.5, "Ara CA\n(kök tarafından imzalı)",
         FILL[1], EDGE[1], fs=9.2)
    _box(ax, 9.4, 4.6, 4.2, 1.5, "Yaprak: example.com\n(SAN: alan adı)",
         FILL[2], EDGE[2], fs=9.2)
    _arrow(ax, 9.4, 5.35, 9.1, 5.35, col=ACCENT_L)
    _arrow(ax, 4.9, 5.35, 4.6, 5.35, col=ACCENT_L)
    ax.text(2.5, 4.1, "imza ↑", ha="center", fontsize=8.6, color=MUTED)
    ax.text(7.1, 4.1, "imza ↑", ha="center", fontsize=8.6, color=MUTED)
    ax.text(0.4, 3.3, "Doğrulama yukarı doğru yürür:", fontsize=9.6,
            weight="bold", color=INK)
    kontroller = ["zincirdeki her imza", "geçerlilik tarihleri",
                  "isim (SAN) eşleşmesi", "iptal durumu (CRL/OCSP)"]
    for i, k in enumerate(kontroller):
        _box(ax, 0.4 + i * 3.45, 1.0, 3.2, 1.3, k, FILL[4], EDGE[4],
             fs=8.8)
    return _save(fig, _yol("zincir"))


# 8. Bellek hata siniflari ve araclar ------------------------------- #
def bellek():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=9.2)
    basliklar = ["Hata sınıfı", "Çalışma zamanı", "Derleme zamanı",
                 "Önleme"]
    xs = [0.3, 3.6, 7.0, 10.3]
    genislik = [3.2, 3.3, 3.2, 3.5]
    for x, w, b in zip(xs, genislik, basliklar):
        _box(ax, x, 8.0, w, 0.7, b, FILL[4], EDGE[4], fs=9.4, bold=True)
    satirlar = [
        ("Tampon taşması", "ASan", "-Wall, -fanalyzer",
         "sınırlı API, boyut"),
        ("Serbest bırakılmış bellek", "ASan", "-fanalyzer",
         "sahiplik, NULL"),
        ("Çift serbest bırakma", "ASan", "-fanalyzer",
         "tek sahip noktası"),
        ("Tamsayı taşması", "UBSan (işaretli)", "derleyici uyarısı",
         "__builtin_*_overflow"),
        ("Biçim dizesi", "—", "-Wformat-security",
         "sabit biçim dizesi"),
    ]
    for r, satir in enumerate(satirlar):
        y = 6.6 - r * 1.35
        for c, (x, w) in enumerate(zip(xs, genislik)):
            dolgu = FILL[0] if c == 0 else FILL[r % 2 + 1]
            kenar = EDGE[0] if c == 0 else RULE
            _box(ax, x, y, w, 1.1, satir[c], dolgu, kenar, fs=8.6,
                 bold=(c == 0))
    return _save(fig, _yol("bellek"))


# 9. Korumalarin asamalari -------------------------------------------- #
def koruma():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.4)
    asamalar = [("Hatanın etkisi:\nbellek bozulması", 0.4),
                ("Kontrol akışının\netkilenmesi", 4.9),
                ("Çalıştırma ve\netki", 9.4)]
    for metin, x in asamalar:
        _box(ax, x, 6.6, 4.2, 1.2, metin, FILL[0], EDGE[0], fs=9.4,
             bold=True)
    _arrow(ax, 4.6, 7.2, 4.9, 7.2, col=ACCENT_L)
    _arrow(ax, 9.1, 7.2, 9.4, 7.2, col=ACCENT_L)
    kolonlar = [
        [("FORTIFY (sınır denetimli kopya)", FILL[2], EDGE[2]),
         ("Yığın kanaryası (bozulma tespiti)", FILL[2], EDGE[2])],
        [("ASLR / PIE (adres tahmini zor)", FILL[1], EDGE[1]),
         ("RELRO (tablo yazmaya kapalı)", FILL[1], EDGE[1])],
        [("NX (veri bölgesi çalışmaz)", FILL[3], EDGE[3]),
         ("Hata düzeltilmedikçe kalır", FILL[4], EDGE[4])],
    ]
    for c, grup in enumerate(kolonlar):
        x = 0.4 + c * 4.5
        for r, (metin, d, k) in enumerate(grup):
            _box(ax, x, 3.9 - r * 1.7, 4.2, 1.2, metin, d, k, fs=9.0)
    ax.text(7.0, 0.7, "Her koruma bir aşamayı zorlaştırır; hiçbiri hatayı "
            "düzeltmez.", ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("koruma"))


# 10. Fuzzing dongusu ------------------------------------------------- #
def fuzz():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.8)
    adimlar = [
        (0.6, 6.4, "tohum (geçerli örnek)"),
        (4.9, 6.4, "mutasyon (sabit tohum)"),
        (9.2, 6.4, "hedefi çalıştır"),
        (9.2, 2.6, "sözleşme denetimi"),
        (4.9, 2.6, "en kısa örneği sakla"),
        (0.6, 2.6, "düzelt ve yeniden çalıştır"),
    ]
    for x, y, metin in adimlar:
        _box(ax, x, y, 4.2, 1.2, metin, FILL[0], EDGE[0], fs=9.4)
    _arrow(ax, 4.8, 7.0, 4.9, 7.0, col=ACCENT_L)
    _arrow(ax, 9.1, 7.0, 9.2, 7.0, col=ACCENT_L)
    _arrow(ax, 11.3, 6.4, 11.3, 3.8, col=ACCENT_L)
    _arrow(ax, 9.2, 3.2, 9.1, 3.2, col=ACCENT_L)
    _arrow(ax, 4.9, 3.2, 4.8, 3.2, col=ACCENT_L)
    _arrow(ax, 2.7, 3.8, 2.7, 6.4, col=ACCENT_L)
    ax.text(7.0, 4.9, "ihlal yoksa: yeni\nmutasyon", ha="center",
            fontsize=8.6, color=MUTED)
    ax.text(7.0, 1.2, "ihlal varsa (beklenmeyen istisna, çökme, sanitizer "
            "hatası)\n→ yeniden üretici kaydedilir; düzeltmeden sonra aynı "
            "tohumla tekrar çalıştırılır.", ha="center", fontsize=8.4,
            color=MUTED)
    return _save(fig, _yol("fuzz"))


if __name__ == "__main__":
    for f in (cia, katmanlar, parola, hmac, aead, tls_el, zincir, bellek,
              koruma, fuzz):
        print(f())
