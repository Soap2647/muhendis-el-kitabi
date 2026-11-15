# -*- coding: utf-8 -*-
"""Bolum 31 - 'Socket Programming' diyagramlari.

Olcum sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b31_modeller.csv   altı sunucu modelinin istek/s ve gecikme olcumu
  b31_udp.csv        durdur-bekle UDP, kayip oranina gore olcum
Diger sekiller bolumdeki ornek degerlerden cizilir.
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
    return os.path.join(OUT, "b31_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. Sunucu / istemci cagri sirasi ------------------------------------- #
def yasam_dongusu():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.4)
    ax.text(2.6, 8.05, "Sunucu", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ax.text(11.4, 8.05, "İstemci", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    sun = ["socket()", "bind(): port ata", "listen(): kuyruk",
           "accept(): bağlantı al", "recv() / send()", "close()"]
    ist = ["socket()", "connect(): el sıkışma", "send() / recv()",
           "close()"]
    ys = [7.2, 6.2, 5.2, 4.2, 3.2, 2.2]
    for i, t in enumerate(sun):
        _box(ax, 0.4, ys[i], 4.6, 0.62, t, FILL[0], EDGE[0], fs=9.5)
        if i < len(sun) - 1:
            _arrow(ax, 2.7, ys[i], 2.7, ys[i + 1] + 0.62, col=MUTED,
                   lw=1.0)
    yi = [7.2, 4.2, 3.2, 2.2]
    for i, t in enumerate(ist):
        _box(ax, 9.0, yi[i], 4.6, 0.62, t, FILL[1], EDGE[1], fs=9.5)
        if i < len(ist) - 1:
            _arrow(ax, 11.3, yi[i], 11.3, yi[i + 1] + 0.62, col=MUTED,
                   lw=1.0)
    _arrow(ax, 9.0, 4.51, 5.0, 4.51, col=ACCENT_L, lw=1.2)
    ax.text(7.0, 4.75, "3 yollu el sıkışma", ha="center", fontsize=8.6,
            color=ACCENT_L)
    _arrow(ax, 5.0, 3.5, 9.0, 3.5, col=ACCENT, lw=1.2, rad=0.0)
    _arrow(ax, 9.0, 3.2, 5.0, 3.2, col=ACCENT, lw=1.2, rad=0.0)
    ax.text(7.0, 3.62, "veri akışı", ha="center", fontsize=8.6,
            color=ACCENT)
    ax.text(7.0, 1.2, "Sunucu 'close' yaparsa karşı taraf recv'de 0 görür\n"
            "(FIN). İki taraf da kapatır; kapatan taraf TIME_WAIT'e girer.",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("yasam"))


# 2. Bayt akisi: mesaj siniri yok ------------------------------------- #
def bayt_akisi():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=8.4)
    ax.text(0.3, 8.0, "Üst: iki gönderim, tek alım", fontsize=9.6,
            weight="bold", color=INK)
    _box(ax, 0.4, 6.8, 3.6, 0.7, 'send("ilk mesaj")', FILL[0], EDGE[0],
         fs=9.2)
    _box(ax, 4.4, 6.8, 4.4, 0.7, 'send("ikinci mesaj")', FILL[0],
         EDGE[0], fs=9.2)
    _box(ax, 0.4, 5.5, 8.4, 0.7, "alıcı tamponu: ilk mesajikinci mesaj",
         FILL[2], EDGE[2], fs=9.2)
    _arrow(ax, 2.2, 6.8, 2.2, 6.2, col=MUTED, lw=1.0)
    _arrow(ax, 6.6, 6.8, 6.6, 6.2, col=MUTED, lw=1.0)
    _arrow(ax, 4.6, 5.5, 4.6, 4.8, col=MUTED, lw=1.0)
    _box(ax, 1.0, 4.0, 7.2, 0.6,
         'recv(4096) → "ilk mesajikinci mesaj"', FILL[3], EDGE[3],
         fs=9.2)
    ax.text(0.3, 3.4, "Alt: tek 10 000 baytlık gönderim, recv(1024)",
            fontsize=9.6, weight="bold", color=INK)
    _box(ax, 0.4, 2.5, 13.2, 0.6, "10 000 bayt (tek send)", FILL[1],
         EDGE[1], fs=9.2)
    for i in range(10):
        x = 0.4 + i * 1.32
        _box(ax, x, 1.3, 1.2, 0.6, "1024", FILL[4], EDGE[4], fs=8.6)
        _arrow(ax, x + 0.6, 2.5, x + 0.6, 1.9, col=MUTED, lw=0.8)
    ax.text(7.0, 0.7, "10 ayrı recv: sınır yok, yalnız bayt sayısı var",
            ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("akis"))


# 3. Cerceveleme: uzunluk onekli ve ayracli ----------------------------- #
def cerceve_duzeni():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=7.4)
    ax.text(0.3, 6.9, "Uzunluk önekli (4 bayt ağ sıralı + yük)",
            fontsize=9.6, weight="bold", color=INK)
    _box(ax, 0.4, 5.6, 3.6, 0.9, "uzunluk = 3\n00 00 00 03", FILL[0],
         EDGE[0], fs=9)
    _box(ax, 4.0, 5.6, 4.8, 0.9, "yük = 3 bayt\n61 62 63  (\"abc\")",
         FILL[1], EDGE[1], fs=9)
    ax.text(0.3, 4.9, "Sonraki çerçeve aynı biçimde başlar; alıcı önce "
            "4 bayt okur.", fontsize=8.6, color=MUTED)
    ax.text(0.3, 3.9, "Ayraçlı (satır sonu)", fontsize=9.6,
            weight="bold", color=INK)
    _box(ax, 0.4, 2.6, 3.0, 0.9, "birinci", FILL[2], EDGE[2], fs=9)
    _box(ax, 3.4, 2.6, 0.9, 0.9, "\\n", FILL[2], EDGE[2], fs=9)
    _box(ax, 4.3, 2.6, 4.0, 0.9, "ikinci satır", FILL[2], EDGE[2], fs=9)
    _box(ax, 8.3, 2.6, 0.9, 0.9, "\\n", FILL[2], EDGE[2], fs=9)
    ax.text(0.3, 1.8, "Ayraç bayt olarak aranır; yük içinde ayraç "
            "bulunursa kaçış (escape) gerekir.", fontsize=8.6,
            color=MUTED)
    ax.text(0.3, 1.1, "Her iki yöntemde de alıcı tamponu tutar: kısa "
            "okumada yarım çerçeve beklenir.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("cerceve"))


# 4. Sunucu modelleri: kavramsal karsilastirma ------------------------- #
def model_kiyas():
    fig, ax = _tuval(9.6, 6.2, xl=14, yl=9.4)
    basliklar = ["Model", "Ne çalışır?", "Bekleme", "Ölçek sınırı"]
    kolon = [0.3, 2.9, 7.0, 10.3]
    genislik = [2.5, 4.0, 3.2, 3.4]
    for x, w, b in zip(kolon, genislik, basliklar):
        _box(ax, x, 8.4, w, 0.6, b, FILL[0], EDGE[0], fs=9.2, bold=True)
    satirlar = [
        ("iteratif", "tek iş parçacığı", "bloklayıcı", "tek istemci"),
        ("fork", "bağlantı başına süreç", "çekirdek", "süreç maliyeti"),
        ("thread", "bağlantı başına iş pars.", "çekirdek", "GIL, yığın"),
        ("havuz", "sabit işçi, bağlantı işi", "çekirdek", "işçi sayısı"),
        ("epoll", "tek iş parçacığı olay döngüsü", "çoğullama",
         "CPU'da tek çekirdek"),
        ("asyncio", "tek iş parçacığı görev döngüsü", "çoğullama",
         "CPU'da tek çekirdek"),
    ]
    for r, satir in enumerate(satirlar):
        y = 7.5 - r * 1.15
        for c, (x, w, metin) in enumerate(zip(kolon, genislik, satir)):
            fill = FILL[(r % 4) + 1] if c == 0 else "white"
            _box(ax, x, y, w, 0.9, metin, fill, RULE, fs=8.8,
                 bold=(c == 0))
    ax.text(7.0, 0.5, "Ölçüm sonuçları bölümde (Şekil 31.7) ve ortamda "
            "değişir.", ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("modeller_kiyas"))


# 5. Model olcumu: istek/s ve p99 (CSV) ------------------------------ #
def model_olcum():
    veri = _oku_csv("b31_modeller.csv")
    modeller = ["iteratif", "fork", "thread", "havuz", "epoll", "asyncio"]
    renk = [MUTED, ACCENT, EDGE[0], EDGE[2], EDGE[1], EDGE[4]]
    bicim = ["o", "s", "^", "D", "v", "P"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for m, r, b in zip(modeller, renk, bicim):
        satir = [s for s in veri if s["model"] == m]
        n = [int(s["n"]) for s in satir]
        ist = [float(s["istek_s"]) for s in satir]
        p99 = [float(s["p99_ms"]) for s in satir]
        a1.plot(n, ist, marker=b, color=r, lw=1.6, ms=5, label=m)
        a2.plot(n, p99, marker=b, color=r, lw=1.6, ms=5, label=m)
    for a, yl, bas in ((a1, "istek/s (log)", "Verim"),
                       (a2, "p99 gecikme, ms (log)", "Kuyruk gecikmesi")):
        a.set_xscale("log", base=2)
        a.set_yscale("log")
        a.set_xlabel("eşzamanlı bağlantı n (log₂)", color=INK)
        a.set_ylabel(yl, color=INK)
        a.set_title(bas, fontsize=10.2, color=INK)
        a.grid(True, which="both", color=RULE, lw=0.6)
        a.set_xticks([1, 16, 64, 256])
        a.set_xticklabels(["1", "16", "64", "256"])
        for s in a.spines.values():
            s.set_color(MUTED)
    a1.legend(loc="upper left", fontsize=7.8, frameon=False)
    fig.tight_layout()
    return _save(fig, _yol("model_olcum"))


# 6. UDP durdur-bekle zaman cizelgesi ---------------------------------- #
def udp_zaman():
    fig, ax = _tuval(9.6, 6.0, xl=14, yl=9.0)
    xg, xa = 2.2, 11.8
    ax.plot([xg, xg], [0.6, 8.3], color=ACCENT_L, lw=1.4)
    ax.plot([xa, xa], [0.6, 8.3], color=ACCENT_L, lw=1.4)
    ax.text(xg, 8.6, "Gönderici", ha="center", fontsize=10,
            weight="bold", color=INK)
    ax.text(xa, 8.6, "Alıcı", ha="center", fontsize=10, weight="bold",
            color=INK)
    ax.text(7.0, 8.6, "zaman ↓", ha="center", fontsize=9, color=MUTED)
    adim = [
        (7.6, xg, xa, "veri(sıra=0)", ACCENT, "-"),
        (6.9, xa, xg, "onay(0)", EDGE[1], "-"),
        (5.9, xg, xa, "veri(0) — KAYIP", ACCENT, "--"),
        (5.2, None, None, "zaman aşımı 50 ms", MUTED, None),
        (4.5, xg, xa, "veri(0) yeniden", ACCENT, "-"),
        (3.8, xa, xg, "onay(0) — KAYIP", EDGE[1], "--"),
        (3.1, None, None, "zaman aşımı 50 ms", MUTED, None),
        (2.4, xg, xa, "veri(0) yeniden", ACCENT, "-"),
        (1.7, xa, xg, "onay(0)", EDGE[1], "-"),
    ]
    for y, x1, x2, metin, renk, stil in adim:
        if x1 is None:
            ax.text(xg + 0.4, y, metin, fontsize=8.6, color=renk,
                    va="center")
            continue
        _arrow(ax, x1, y, x2, y, col=renk, lw=1.4)
        if stil == "--":
            ax.plot([(x1 + x2) / 2], [y], marker="x", color=ACCENT,
                    ms=11, mew=2)
        ax.text((x1 + x2) / 2, y + 0.25, metin, ha="center", fontsize=8.6,
                color=renk)
    ax.text(7.0, 0.8, "Sıra biti 0 ile 1 arasında değişir; alıcı yinelenen "
            "veriyi teslim etmez, yeniden onaylar.", ha="center",
            fontsize=8.4, color=MUTED)
    return _save(fig, _yol("udp_zaman"))


# 7. epoll sunucu durum diyagrami -------------------------------------- #
def epoll_durum():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=9.0)
    _box(ax, 0.3, 7.0, 3.0, 0.9, "Dinleme soketi\nEPOLLIN", FILL[0],
         EDGE[0], fs=9)
    _box(ax, 4.2, 7.0, 3.0, 0.9, "accept: tüm\nbekleyenler", FILL[1],
         EDGE[1], fs=9)
    _box(ax, 8.1, 7.0, 3.0, 0.9, "Bağlantı kaydı\nEPOLLIN", FILL[2],
         EDGE[2], fs=9)
    _box(ax, 4.2, 4.6, 3.0, 0.9, "oku: recv döngüsü\nçerçevele",
         FILL[3], EDGE[3], fs=9)
    _box(ax, 8.1, 4.6, 3.0, 0.9, "giden dolu mu?", FILL[4], EDGE[4],
         fs=9)
    _box(ax, 8.1, 2.2, 3.0, 0.9, "EPOLLIN|EPOLLOUT\nkısmi yazma",
         FILL[2], EDGE[2], fs=9)
    _box(ax, 4.2, 2.2, 3.0, 0.9, "EOF: giden boşsa\nkapat", FILL[3],
         EDGE[3], fs=9)
    _box(ax, 0.3, 2.2, 3.0, 0.9, "close()\n(kaydı sil)", FILL[0],
         EDGE[0], fs=9)
    _arrow(ax, 3.3, 7.45, 4.2, 7.45)
    _arrow(ax, 7.2, 7.45, 8.1, 7.45)
    _arrow(ax, 9.6, 6.95, 9.6, 5.6, col=MUTED)
    ax.text(9.75, 6.2, "EPOLLIN olayı", fontsize=8.4, color=MUTED)
    _arrow(ax, 8.1, 5.05, 7.2, 5.05)
    _arrow(ax, 9.6, 4.55, 9.6, 3.2, col=ACCENT)
    ax.text(9.75, 3.7, "evet", fontsize=8.4, color=ACCENT)
    _arrow(ax, 8.1, 2.65, 7.2, 2.65, col=ACCENT)
    ax.text(7.3, 3.3, "EPOLLOUT", fontsize=8.4, color=ACCENT)
    _arrow(ax, 5.7, 4.55, 5.7, 3.2, col=MUTED)
    ax.text(5.85, 3.7, "EOF", fontsize=8.4, color=MUTED)
    _arrow(ax, 4.2, 2.65, 3.3, 2.65)
    ax.text(0.3, 0.9, "Giden tamponu boşalınca EPOLLOUT kaldırılır; "
            "yoksa döngü sürekli uyanır.", fontsize=8.6, color=MUTED)
    ax.text(0.3, 0.3, "Hayır dalı: giden boşsa EPOLLIN'e dönülür.",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("epoll_durum"))


# 8. Telemetri paket duzeni -------------------------------------------- #
def telemetri_duzeni():
    alanlar = [("sürüm", 1, "1"), ("tür", 1, "0x01"), ("sıra", 4, "u32"),
               ("zaman_ms", 4, "u32"), ("enlem", 4, "i32 ×1e-7"),
               ("boylam", 4, "i32 ×1e-7"), ("irtifa", 4, "i32 cm"),
               ("batarya", 2, "u16 mV"), ("CRC-32", 4, "u32")]
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=9.4)
    ofs = 0
    olcek = 8.0 / 28.0
    renkler = [FILL[0], FILL[1], FILL[2], FILL[3], FILL[4]]
    kenar = [EDGE[0], EDGE[1], EDGE[2], EDGE[3], EDGE[4]]
    for i, (ad, n, not_) in enumerate(alanlar):
        y = 8.0 - i * 0.9
        x = 3.2 + ofs * olcek
        w = n * olcek
        _box(ax, x, y, w, 0.62, "", renkler[i % 5], kenar[i % 5])
        ax.text(0.3, y + 0.31, "%s (%d B)" % (ad, n), fontsize=8.8,
                va="center", color=INK)
        ax.text(x + w + 0.12, y + 0.31, "ofset %d · %s" % (ofs, not_),
                fontsize=8.2, va="center", color=MUTED)
        ofs += n
    ax.text(7.0, 0.3, "Toplam 28 bayt. CRC, ilk 24 baytın (gövdenin) "
            "üzerinde hesaplanır.", ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("telemetri"))


# 9. UDP kayip olcumu (CSV) -------------------------------------------- #
def udp_olcum():
    veri = _oku_csv("b31_udp.csv")
    p = [float(s["kayip_p"]) * 100 for s in veri]
    gon = [int(s["gonderim"]) for s in veri]
    yen = [int(s["yeniden"]) for s in veri]
    sur = [float(s["sure_s"]) for s in veri]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    a1.plot(p, gon, "o-", color=ACCENT, lw=1.8, ms=5, label="gönderim")
    a1.plot(p, yen, "s--", color=EDGE[1], lw=1.6, ms=5,
            label="yeniden iletim")
    a1.set_xlabel("kayıp oranı (%)", color=INK)
    a1.set_ylabel("paket sayısı (200 mesaj)", color=INK)
    a1.set_title("Kayıp arttıkça gönderim artar", fontsize=10, color=INK)
    a1.legend(loc="upper left", fontsize=8.4, frameon=False)
    a2.plot(p, sur, "o-", color=ACCENT_L, lw=1.8, ms=5)
    a2.set_xlabel("kayıp oranı (%)", color=INK)
    a2.set_ylabel("toplam süre (s)", color=INK)
    a2.set_title("Süre: zaman aşımı sayısıyla doğru orantılı",
                 fontsize=10, color=INK)
    for a in (a1, a2):
        a.grid(True, color=RULE, lw=0.6)
        for s in a.spines.values():
            s.set_color(MUTED)
    fig.tight_layout()
    return _save(fig, _yol("udp_olcum"))


# 10. Bayt sirasi: bellek ve ag ---------------------------------------- #
def bayt_sirasi():
    fig, ax = _tuval(9.6, 4.2, xl=14, yl=7.2)
    ax.text(0.3, 6.6, "Ana makine (little-endian) bellek: 0x1F90 = 8080",
            fontsize=9.6, weight="bold", color=INK)
    for i, b in enumerate(["90", "1F"]):
        _box(ax, 0.6 + i * 1.6, 5.2, 1.3, 0.8, b, FILL[0], EDGE[0],
             fs=10)
    ax.text(4.0, 5.6, "düşük adres → yüksek adres", fontsize=8.4,
            color=MUTED, va="center")
    _arrow(ax, 7.0, 5.6, 9.0, 5.6, col=ACCENT, lw=1.6)
    ax.text(8.0, 6.0, "htons()", fontsize=8.8, color=ACCENT,
            ha="center")
    ax.text(9.2, 6.2, "", fontsize=8)
    ax.text(0.3, 4.2, "Ağ (big-endian) sırası: aynı değer, ters bayt",
            fontsize=9.6, weight="bold", color=INK)
    for i, b in enumerate(["1F", "90"]):
        _box(ax, 0.6 + i * 1.6, 2.8, 1.3, 0.8, b, FILL[1], EDGE[1],
             fs=10)
    ax.text(4.0, 3.2, "ağa önce en anlamlı bayt gider", fontsize=8.4,
            color=MUTED, va="center")
    ax.text(0.3, 1.6, "Kural: ağ üzerinde giden her çok baytlık sayı "
            "htons/htonl ile çevrilir;", fontsize=8.6, color=MUTED)
    ax.text(0.3, 1.0, "alıcı ntohs/ntohl ile geri çevirir. Bayt "
            "sırası bir sözleşmedir.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("bayt_sirasi"))


if __name__ == "__main__":
    for f in (yasam_dongusu, bayt_akisi, cerceve_duzeni, model_kiyas,
              model_olcum, udp_zaman, epoll_durum, telemetri_duzeni,
              udp_olcum, bayt_sirasi):
        print(f())
