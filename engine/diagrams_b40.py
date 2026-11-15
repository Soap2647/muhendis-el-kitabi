# -*- coding: utf-8 -*-
"""Bolum 40 - 'API Tasarimi' diyagramlari.

Olcum sekli engine/veri/b40_kova.csv dosyasini okur (jeton kovasi
durumu). Diger sekiller bolumdeki ornek degerlerden cizilir.
"""
import csv
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
VERI = os.path.join(BASE, "veri")
MONO = {"family": "DejaVu Sans Mono"}


def _yol(ad):
    return os.path.join(OUT, "b40_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. Uc API turu ------------------------------------------------------ #
def api_turleri():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.6)
    baslik = ["Kütüphane API'si", "Ağ API'si (HTTP)",
              "Donanım / sürücü API'si"]
    ornek = ["fopen(), json.dumps()\nçağrı, aynı süreç içinde",
             "GET /ihalar/1\nistek ve yanıt, ağ üzerinde",
             "write(fd, ...), ioctl()\nçekirdek ve aygıt sürücüsü"]
    for i, (b, o) in enumerate(zip(baslik, ornek)):
        x = 0.3 + i * 4.6
        _box(ax, x, 4.7, 4.2, 1.0, b, FILL[i], EDGE[i], fs=10.5,
             bold=True)
        _box(ax, x, 2.4, 4.2, 1.7, o, FILL[4], EDGE[4], fs=9.5)
        _arrow(ax, x + 2.1, 4.7, x + 2.1, 4.1, col=MUTED, lw=1.0)
    _box(ax, 0.3, 0.4, 13.4, 1.2,
         "Hepsi bir SÖZLEŞMEDİR: girdi, çıktı, hata ve yan etkiler",
         FILL[3], ACCENT, fs=11, bold=True, tcol=ACCENT)
    return _save(fig, _yol("api_turleri"))


# 2. Kaynak hiyerarsisi --------------------------------------------- #
def kaynak_hiyerarsi():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.2)
    seviyeler = [
        ("/ihalar", "koleksiyon: GET, POST", FILL[0], EDGE[0]),
        ("/ihalar/{id}", "öğe: GET, PUT, PATCH, DELETE", FILL[1], EDGE[1]),
        ("/ihalar/{id}/gorevler", "alt koleksiyon: GET, POST",
         FILL[2], EDGE[2]),
    ]
    for i, (yol, aciklama, f, e) in enumerate(seviyeler):
        y = 5.3 - i * 2.0
        _box(ax, 0.6 + i * 1.0, y, 5.2, 1.1, yol, f, e, fs=11,
             bold=True, tcol=INK)
        ax.text(6.1 + i * 1.0, y + 0.55, aciklama, fontsize=9.5,
                color=MUTED, va="center")
        if i < len(seviyeler) - 1:
            _arrow(ax, 1.6 + i * 1.0, y, 1.6 + i * 1.0, y - 0.9 + 0.0,
                   col=MUTED, lw=1.0)
    ax.text(0.6, 0.6, "Kural: isim çoğul ve kaynak adıdır; fiil yoktur. "
            "Yöntem işi anlatır.", fontsize=9.5, color=INK)
    return _save(fig, _yol("kaynak_hiyerarsi"))


# 3. Yontem ve idempotentlik tablosu ------------------------------- #
def yontem_tablosu():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=6.8)
    satirlar = [
        ("GET", "Evet", "Evet", "Hayır", "200"),
        ("POST", "Hayır", "Hayır", "Evet", "201 + Location"),
        ("PUT", "Hayır", "Evet", "Evet, tam nesne", "200 ya da 204"),
        ("PATCH", "Hayır", "Hayır (genelde)", "Evet, kısmi", "200"),
        ("DELETE", "Hayır", "Evet", "Hayır", "204"),
    ]
    basl = ["Yöntem", "Güvenli", "İdempotent", "İstek gövdesi",
            "Tipik kod"]
    xs = [0.2, 2.2, 4.5, 7.2, 10.5]
    gen = [2.0, 2.3, 2.7, 3.3, 3.3]
    for x, w, t in zip(xs, gen, basl):
        _box(ax, x, 5.7, w - 0.1, 0.8, t, FILL[1], EDGE[1], fs=10,
             bold=True)
    for r, sat in enumerate(satirlar):
        y = 4.7 - r * 0.95
        for c, (x, w, t) in enumerate(zip(xs, gen, sat)):
            fill = FILL[0] if c == 0 else FILL[4]
            _box(ax, x, y, w - 0.1, 0.8, t, fill, RULE, fs=9.5,
                 bold=(c == 0), tcol=INK)
    ax.text(0.2, 0.25, "İdempotent: aynı istek bir ya da on kez gelince "
            "durum aynıdır (30.6).", fontsize=9, color=MUTED)
    return _save(fig, _yol("yontem_tablosu"))


# 4. Offset ve keyset sayfalama --------------------------------------- #
def sayfalama():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=8.6)
    senaryolar = [
        ("offset, silme", [10, 9, 8], [6, 5, 4], 7, "atlandı"),
        ("offset, ekleme", [10, 9, 8], [8, 7, 6], 8, "çift"),
        ("keyset, silme", [10, 9, 8], [7, 6, 5], None, ""),
        ("keyset, ekleme", [10, 9, 8], [7, 6, 5], None, ""),
    ]
    for r, (ad, s1, s2, bad, durum) in enumerate(senaryolar):
        y = 7.0 - r * 1.85
        ax.text(0.2, y + 0.45, ad, fontsize=10, weight="bold", color=INK)
        for k, idler in enumerate((s1, s2)):
            x0 = 2.6 + k * 3.9
            ax.text(x0, y + 0.45, "sayfa %d" % (k + 1), fontsize=8.5,
                    color=MUTED)
            for j, v in enumerate(idler):
                hl = (k == 1 and v == bad)
                f = FILL[3] if hl else FILL[0]
                e = ACCENT if hl else EDGE[0]
                _box(ax, x0 + j * 1.1, y - 0.3, 0.95, 0.6, str(v), f, e,
                     fs=9.5, bold=hl, tcol=ACCENT if hl else INK)
        if bad is not None:
            ax.text(10.5, y + 0.05, "%d %s" % (bad, durum), fontsize=9,
                    color=ACCENT, va="center")
    return _save(fig, _yol("sayfalama"))


# 5. Idempotency-Key akisi -------------------------------------------- #
def idempotent_akis():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.6)
    _box(ax, 0.2, 2.4, 3.2, 1.8, "İstemci\nPOST + Idempotency-Key",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 4.0, 2.4, 3.4, 1.8,
         "Sunucu\n(kullanıcı, anahtar)\nvar mı?", FILL[2], EDGE[2], fs=9)
    _arrow(ax, 3.4, 3.3, 4.0, 3.3, col=MUTED, lw=1.2)
    sonuc = [
        ("Hayır: oluştur, özeti ve yanıtı kaydet\n→ 201 Created",
         FILL[1], EDGE[1], 4.6),
        ("Evet, özet aynı: kayıtlı yanıtı dön\n"
         "→ 201 + Idempotent-Replayed", FILL[4], EDGE[4], 2.6),
        ("Evet, özet farklı: reddet\n→ 422 Unprocessable Entity",
         FILL[3], EDGE[3], 0.6),
    ]
    for metin, f, e, y in sonuc:
        _box(ax, 8.3, y, 5.5, 1.3, metin, f, e, fs=8.8)
        _arrow(ax, 7.4, 3.3, 8.3, y + 0.65, col=MUTED, lw=1.0)
    return _save(fig, _yol("idempotent_akis"))


# 6. ETag ile iyimser kilitleme ------------------------------------- #
def etag_akis():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=6.8)
    _box(ax, 0.2, 2.6, 3.2, 1.8, "GET /ihalar/1\nYanıt: ETag = e1",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 4.0, 2.6, 3.4, 1.8, "PUT /ihalar/1\nIf-Match: ?",
         FILL[2], EDGE[2], fs=9)
    _arrow(ax, 3.4, 3.5, 4.0, 3.5, col=MUTED, lw=1.2)
    sonuc = [
        ("If-Match yok: kayıt yenilenmez\n→ 428 Precondition Required",
         FILL[4], EDGE[4], 5.0),
        ("If-Match = e1: güncelle\n→ 200 + yeni ETag e2",
         FILL[1], EDGE[1], 2.9),
        ("If-Match eşleşmiyor: başkası değiştirdi\n"
         "→ 412 Precondition Failed", FILL[3], EDGE[3], 0.8),
    ]
    for metin, f, e, y in sonuc:
        _box(ax, 8.3, y, 5.5, 1.3, metin, f, e, fs=8.8)
        _arrow(ax, 7.4, 3.5, 8.3, y + 0.65, col=MUTED, lw=1.0)
    return _save(fig, _yol("etag_akis"))


# 7. Token bucket durumu (CSV'den) ---------------------------------- #
def kova_durum():
    with open(os.path.join(VERI, "b40_kova.csv"), encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    t = [float(r["zaman_s"]) for r in satirlar]
    j = [float(r["jeton"]) for r in satirlar]
    izin = [int(r["izin"]) for r in satirlar]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.step(t, j, where="post", color=EDGE[0], lw=1.6)
    ax.axhline(3.0, color=MUTED, ls="--", lw=1.0)
    ax.text(2.2, 3.12, "kapasite = 3", color=MUTED, va="bottom",
            fontsize=9)
    gorulen = {}
    for ti, ji, ok in zip(t, j, izin):
        # Ayni andaki olaylari yana kaydir ki ust uste binmesin
        k = gorulen.get(ti, 0)
        gorulen[ti] = k + 1
        ax.scatter([ti + 0.05 * k], [ji], s=46, zorder=3,
                   color=EDGE[1] if ok else ACCENT,
                   edgecolors=INK, linewidths=0.5)
    ax.set_xlabel("zaman (s)", color=INK)
    ax.set_ylabel("kovadaki jeton", color=INK)
    ax.set_ylim(-0.3, 3.6)
    ax.set_xlim(-0.2, 3.4)
    ax.set_xticks([0, 0.5, 1.0, 1.2, 2.0, 3.0])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.scatter([], [], color=EDGE[1], label="izin verildi")
    ax.scatter([], [], color=ACCENT, label="reddedildi (429)")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    return _save(fig, _yol("kova_durum"))


# 8. Surumleme stratejileri ----------------------------------------- #
def surum_stratejileri():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=6.8)
    kol = [
        ("URL", "/v2/ihalar", "+ Açık ve önbelleğe uygun\n"
         "- URL'ler çoğalır"),
        ("Başlık", "X-Api-Version: 2", "+ URL temiz kalır\n"
         "- Önbellek ve test zor"),
        ("İçerik anlaşması", "Accept: application/\n"
         "vnd.ihafilo.v2+json", "+ REST'e en uygun\n"
         "- Öğrenmesi zor, istemci az"),
    ]
    for i, (ad, ornek, art) in enumerate(kol):
        x = 0.3 + i * 4.6
        _box(ax, x, 5.0, 4.2, 0.9, ad, FILL[i], EDGE[i], fs=11,
             bold=True)
        _box(ax, x, 3.0, 4.2, 1.6, ornek, FILL[4], EDGE[4], fs=9.5,
             tcol=INK)
        ax.text(x + 0.2, 2.3, art, fontsize=9, color=INK, va="top")
    ax.text(0.3, 0.3, "Her yöntemde kural aynı: alan eklemek güvenli, "
            "kaldırmak ya da anlamını değiştirmek yıkıcı.",
            fontsize=9.2, color=ACCENT)
    return _save(fig, _yol("surum_stratejileri"))


# 9. Protobuf bayt duzeni ------------------------------------------- #
def protobuf_bayt():
    fig, ax = _tuval(9.6, 3.6, xl=14, yl=5.2)
    hucreler = [
        ("08", "anahtar\nalan 1", FILL[0], EDGE[0]),
        ("96 01", "değer\n150", FILL[1], EDGE[1]),
        ("10", "anahtar\nalan 2", FILL[0], EDGE[0]),
        ("05", "zigzag\n(-3)=5", FILL[2], EDGE[2]),
        ("22", "anahtar\nalan 4", FILL[0], EDGE[0]),
        ("02", "uzunluk\n2", FILL[4], EDGE[4]),
        ("45 56", "\"EV\"", FILL[3], EDGE[3]),
    ]
    x = 0.2
    for kod, etiket, f, e in hucreler:
        w = 1.9 if len(kod) > 2 else 1.2
        _box(ax, x, 2.2, w, 1.0, kod, f, e, fs=10, tcol=INK, bold=True)
        ax.text(x + w / 2, 1.9, etiket, fontsize=8.2, color=INK,
                ha="center", va="top", linespacing=1.3)
        x += w + 0.3
    ax.text(0.2, 4.4, "message Telemetri { uint32 id = 1; "
            "sint32 sicaklik = 2; string ad = 4; }", fontsize=9.2,
            color=MUTED, **MONO)
    return _save(fig, _yol("protobuf_bayt"))


# 10. ABI kirilmasi: struct duzeni ---------------------------------- #
def abi_duzen():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.8)
    olcek = 0.5           # her bayt 0.5 birim genislikte

    def bayt_seridi(y, alanlar, toplam):
        for ad, bas, son, f, e in alanlar:
            _box(ax, 0.6 + bas * olcek, y, (son - bas) * olcek - 0.04,
                 1.0, ad, f, e, fs=8.6, tcol=INK)

    bayt_seridi(4.4, [
        ("id (int)", 0, 4, FILL[0], EDGE[0]),
        ("dolgu", 4, 8, FILL[4], EDGE[4]),
        ("deger (double)", 8, 16, FILL[1], EDGE[1]),
    ], 16)
    ax.text(0.6, 5.7, "v1: sizeof = 16 bayt", fontsize=10,
            weight="bold", color=INK)
    bayt_seridi(1.9, [
        ("id (int)", 0, 4, FILL[0], EDGE[0]),
        ("dolgu", 4, 8, FILL[4], EDGE[4]),
        ("deger (double)", 8, 16, FILL[1], EDGE[1]),
        ("durum (int)", 16, 20, FILL[3], EDGE[3]),
        ("dolgu", 20, 24, FILL[4], EDGE[4]),
    ], 24)
    ax.text(0.6, 3.2, "v2: sizeof = 24 bayt", fontsize=10,
            weight="bold", color=INK)
    x16 = 0.6 + 16 * olcek
    ax.plot([x16, x16], [1.6, 5.2], color=ACCENT, lw=1.6, ls="--")
    ax.text(x16 + 0.15, 0.7, "eski istemcinin ayırdığı son sınır (16)",
            fontsize=9, color=ACCENT)
    ax.text(0.6, 0.2, "v2 kütüphanesi offset 16'ya yazar: "
            "eski istemcinin yapısının dışı", fontsize=9, color=MUTED)
    return _save(fig, _yol("abi_duzen"))


if __name__ == "__main__":
    for f in (api_turleri, kaynak_hiyerarsi, yontem_tablosu, sayfalama,
              idempotent_akis, etag_akis, kova_durum, surum_stratejileri,
              protobuf_bayt, abi_duzen):
        print(f())
