# -*- coding: utf-8 -*-
"""Bolum 30 - 'HTTP, DNS, DHCP' diyagramlari.

Olcum sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b30_bilesen.csv       WSL curl -w zamanlama bilesenleri (gecikme cubugu)
  b30_dns_ornek_yanit.hex  sabit bir DNS yanit baytlari (isaretci sekli)
Diger sekiller bolumdeki ornek degerlerden cizilir.
"""
import csv
import os
import statistics
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


def _yol(ad):
    return os.path.join(OUT, "b30_%s.png" % ad)


def _tuval(w, h, xl=14, yl=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _yazi(ax, x, y, s, fs=9, renk=INK, ha="center", bold=False):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=renk,
            weight="bold" if bold else "normal")


def _cizgi(ax, x, y0, y1):
    ax.plot([x, x], [y0, y1], color=RULE, lw=1.2, ls="--", zorder=0)


# 1. DNS hiyerarsisi: kok -> TLD -> yetkili ---------------------------- #
def dns_hiyerarsi():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=9.4)
    _box(ax, 0.3, 3.9, 2.9, 1.1, "Özyinelemeli\nçözümleyici", FILL[0],
         EDGE[0], fs=9.5, bold=True)
    _yazi(ax, 1.75, 3.5, "istemcinin ayarladığı DNS", fs=8, renk=MUTED)
    _box(ax, 5.3, 6.9, 3.2, 1.1, "Kök  ( . )\n13 kök sunucu adı",
         FILL[3], EDGE[3], fs=9.2, bold=True)
    _box(ax, 5.3, 3.9, 3.2, 1.1, "TLD: com\n(.com için yetkili)",
         FILL[2], EDGE[2], fs=9.2, bold=True)
    _box(ax, 5.3, 0.9, 3.2, 1.1, "example.com\n(yetkili sunucu)",
         FILL[1], EDGE[1], fs=9.2, bold=True)
    _box(ax, 9.7, 0.9, 3.9, 1.1, "www.example.com\n(CNAME ya da A)",
         FILL[4], EDGE[4], fs=9, bold=False)
    _arrow(ax, 6.9, 6.9, 6.9, 5.0, col=MUTED, lw=1.2)
    _arrow(ax, 6.9, 3.9, 6.9, 2.0, col=MUTED, lw=1.2)
    _arrow(ax, 8.5, 1.45, 9.7, 1.45, col=MUTED, lw=1.2)
    _yazi(ax, 7.6, 5.95, "NS: com", fs=8, renk=MUTED)
    _yazi(ax, 7.6, 2.95, "NS: example.com", fs=8, renk=MUTED)
    _arrow(ax, 3.2, 4.45, 5.3, 7.3, col=ACCENT, lw=1.4)
    _arrow(ax, 3.2, 4.45, 5.3, 4.45, col=ACCENT, lw=1.4)
    _arrow(ax, 3.2, 4.2, 5.3, 1.5, col=ACCENT, lw=1.4, rad=0.25)
    _yazi(ax, 4.05, 6.4, "1. kök?", fs=8, renk=ACCENT)
    _yazi(ax, 4.05, 4.75, "2. com?", fs=8, renk=ACCENT)
    _yazi(ax, 3.9, 2.1, "3. example.com?", fs=8, renk=ACCENT)
    _yazi(ax, 7.0, 8.55, "Ad, sağdan sola (sondan başa) okunur:  "
          "www.example.com.  →  com.  →  example.com.",
          fs=8.3, renk=MUTED)
    return _save(fig, _yol("dns_hiyerarsi"))


# 2. Ozyinelemeli cozumleme zaman cizelgesi ---------------------------- #
def dns_cozumleme():
    fig, ax = _tuval(9.6, 6.6, xl=14, yl=10.2)
    isimler = [(1.1, "İstemci"), (4.1, "Çözümleyici"), (7.1, "Kök (.)"),
               (9.9, "TLD (com)"), (12.7, "Yetkili\n(example.com)")]
    for x, ad in isimler:
        _box(ax, x - 1.05, 9.0, 2.1, 0.85, ad, FILL[0], EDGE[0], fs=8.6,
             bold=True)
        _cizgi(ax, x, 0.5, 8.9)
    adimlar = [
        (1.1, 4.1, 8.0, "1. example.com A?", ACCENT),
        (4.1, 7.1, 7.0, "2. example.com A?  (kök bilmez)", ACCENT),
        (7.1, 4.1, 6.05, "NS: com sunucuları", MUTED),
        (4.1, 9.9, 5.1, "3. example.com A?", ACCENT),
        (9.9, 4.1, 4.15, "NS: example.com sunucuları", MUTED),
        (4.1, 12.7, 3.2, "4. example.com A?", ACCENT),
        (12.7, 4.1, 2.25, "A = 104.20.23.154  (TTL 300)", MUTED),
        (4.1, 1.1, 1.3, "5. A = 104.20.23.154", ACCENT),
    ]
    for x1, x2, y, s, renk in adimlar:
        _arrow(ax, x1, y, x2, y, col=renk, lw=1.5)
        mx = (x1 + x2) / 2
        _yazi(ax, mx, y + 0.27, s, fs=8.2, renk=renk)
    _box(ax, 0.3, 0.05, 9.4, 0.55,
         "Önbellekte kayıt varsa 2-4 adımlar atlanır. TTL dolunca yenilenir.",
         FILL[2], EDGE[2], fs=8, tcol=INK)
    return _save(fig, _yol("dns_cozumleme"))


# 3. DNS mesaj bicimi: basliktan kayitlara ----------------------------- #
def dns_mesaj():
    fig, ax = _tuval(9.6, 5.4, xl=12, yl=9.4)
    olcek = 0.6                          # birim/bayt

    def satir(y, parcalar, baslik):
        _yazi(ax, 0.2, y + 1.05, baslik, fs=9, renk=ACCENT_L, ha="left",
              bold=True)
        x = 0.2
        for i, (ad, bayt, renk) in enumerate(parcalar):
            w = bayt * olcek
            _box(ax, x, y, w - 0.04, 0.7, ad, FILL[renk], EDGE[renk],
                 fs=7.6 if w > 1.1 else 6.8)
            _yazi(ax, x + w / 2, y - 0.25, "%d" % bayt, fs=7.5, renk=MUTED)
            x += w
        return x

    satir(7.5, [("ID\n2", 2, 0), ("Bayraklar\n2", 2, 1),
                ("QDCOUNT\n2", 2, 2), ("ANCOUNT\n2", 2, 3),
                ("NSCOUNT\n2", 2, 4), ("ARCOUNT\n2", 2, 0)],
          "Başlık (12 bayt)")
    satir(4.9, [("QNAME: 7 example 3 com 0\n13 bayt", 13, 1),
                ("QTYPE\n2", 2, 2), ("QCLASS\n2", 2, 3)],
          "Soru bölümü (QDCOUNT = 1)")
    satir(2.3, [("NAME\n2", 2, 4), ("TYPE\n2", 2, 0),
                ("CLASS\n2", 2, 1), ("TTL\n4", 4, 2),
                ("RDLEN\n2", 2, 3), ("RDATA\n4", 4, 4)],
          "Yanıt kaydı (ANCOUNT = 1 ayrı satır)")
    _yazi(ax, 0.2, 0.5, "Bayt sayıları kutuların altında. Her alan ağ "
          "bayt sırasıyla (big-endian) yazılır.", fs=8, renk=MUTED,
          ha="left")
    return _save(fig, _yol("dns_mesaj"))


# 4. Isaretci: c0 0c, ofset 12'deki ada geri doner --------------------- #
def dns_isaretci():
    hexs = open(os.path.join(VERI, "b30_dns_ornek_yanit.hex"),
                encoding="utf-8").read().split()
    b = [int(x, 16) for x in hexs]
    fig, ax = _tuval(9.6, 4.6, xl=34, yl=7.5)
    bas, son = 12, 45
    for k, i in enumerate(range(bas, son)):
        x = 0.1 + k * 0.92
        renk = 0
        if i < 25:
            renk = 1                      # soru: ad
        if 25 <= i < 29:
            renk = 2                      # soru: tip, sınıf
        if i == 29 or i == 30:
            renk = 3                      # işaretçi
        if i > 30:
            renk = 4
        _box(ax, x, 4.5, 0.82, 0.8, "%02x" % b[i], FILL[renk],
             EDGE[renk], fs=7.4, bold=(renk == 3))
        _yazi(ax, x + 0.41, 4.2, "%d" % i, fs=6.2, renk=MUTED)
    _arrow(ax, 0.1 + (29 - bas) * 0.92 + 0.41, 4.5,
           0.1 + (12 - bas) * 0.92 + 0.41, 4.5, col=ACCENT, lw=1.8,
           rad=-0.5)
    _yazi(ax, 6.2, 6.6, "işaretçi 0xC0 0x0C: ofset 0x0C = 12 "
          "(soru adının başı)", fs=8.8, renk=ACCENT, bold=True)
    lejant = [(0.3, "Soru adı (QNAME)", 1), (7.4, "QTYPE, QCLASS", 2),
              (14.5, "İşaretçi (NAME)", 3), (23.0, "Yanıt alanları", 4)]
    for x, s, k in lejant:
        ax.add_patch(plt.Rectangle((x, 1.2), 0.5, 0.5, facecolor=FILL[k],
                                   edgecolor=EDGE[k], lw=1.2))
        _yazi(ax, x + 0.75, 1.45, s, fs=8.3, renk=INK, ha="left")
    return _save(fig, _yol("dns_isaretci"))


# 5. DHCP DORA zaman cizelgesi ----------------------------------------- #
def dhcp_dora():
    fig, ax = _tuval(9.6, 6.4, xl=14, yl=10.2)
    _box(ax, 0.5, 9.0, 3.6, 0.85, "İstemci (yeni cihaz)\nkaynak 0.0.0.0",
         FILL[0], EDGE[0], fs=8.6, bold=True)
    _box(ax, 9.9, 9.0, 3.6, 0.85, "DHCP sunucusu\n192.168.1.1",
         FILL[1], EDGE[1], fs=8.6, bold=True)
    _cizgi(ax, 2.3, 0.6, 8.9)
    _cizgi(ax, 11.7, 0.6, 8.9)
    msj = [
        (2.3, 11.7, 7.8, "1. DISCOVER  (broadcast)\n"
         "0.0.0.0:68 -> 255.255.255.255:67", ACCENT),
        (11.7, 2.3, 5.9, "2. OFFER  yiaddr=192.168.1.50\n"
         "maske, ağ geçidi, DNS, kira 86400 s", ACCENT_L),
        (2.3, 11.7, 4.0, "3. REQUEST  sunucu kimliği = 192.168.1.1\n"
         "(broadcast: diğer sunucular da duyar)", ACCENT),
        (11.7, 2.3, 2.0, "4. ACK  kira onaylandı", ACCENT_L),
    ]
    for x1, x2, y, s, renk in msj:
        _arrow(ax, x1, y, x2, y, col=renk, lw=1.5)
        _yazi(ax, 7.0, y + 0.5, s, fs=8.3, renk=renk)
    _box(ax, 0.4, 0.05, 13.2, 0.8,
         "T1 = kira / 2: yenileme, aynı sunucuya tek yayın REQUEST.   "
         "T2 = kira x 7/8: başka sunuculara yayın.   Kira biterse IP düşer.",
         FILL[2], EDGE[2], fs=8)
    return _save(fig, _yol("dhcp_dora"))


# 6. HTTP istek ve yanit anatomisi ------------------------------------- #
def http_anatomi():
    fig, ax = _tuval(10.4, 6.3, xl=11.6, yl=10)
    _yazi(ax, 2.4, 9.55, "İstek (request)", fs=10, renk=ACCENT, bold=True)
    _yazi(ax, 8.2, 9.55, "Yanıt (response)", fs=10, renk=ACCENT_L,
          bold=True)
    sol = [("GET /ornek/not.txt HTTP/1.1", 0),
           ("Host: example.com", 1),
           ("User-Agent: b30-ham-istemci/1.0", 1),
           ("Accept: text/html", 1),
           ("(boş satır: CRLF)", 3),
           ("(gövde yok: GET)", 2)]
    sag = [("HTTP/1.1 200 OK", 0),
           ("Content-Type: text/plain", 1),
           ("Content-Length: 25", 1),
           ("ETag: \"7932a007eaf77af7\"", 1),
           ("(boş satır: CRLF)", 3),
           ("Bu bir metin dosyasidir.", 2)]
    etiket = {0: "başlangıç", 1: "başlık", 2: "gövde", 3: ""}
    for kolon, x in ((sol, 0.2), (sag, 6.0)):
        for k, (s, t) in enumerate(kolon):
            y = 8.2 - k * 1.35
            fill = [FILL[3], FILL[0], FILL[2], "#ffffff"][t]
            edge = [EDGE[3], EDGE[0], EDGE[2], RULE][t]
            _box(ax, x, y, 4.4, 0.95, s, fill, edge, fs=8.4)
            if etiket[t]:
                _yazi(ax, x + 4.55, y + 0.48, etiket[t], fs=7.4,
                      renk=MUTED, ha="left")
    _yazi(ax, 5.8, 0.35, "Her satır CRLF (\\r\\n) ile biter; başlıklar "
          "bittikten sonra boş bir satır gelir.", fs=8, renk=MUTED)
    return _save(fig, _yol("http_anatomi"))


# 7. Her istekte yeni baglanti vs kalici baglanti ---------------------- #
def keepalive():
    fig, ax = _tuval(9.6, 4.9, xl=14, yl=7.4)
    renkler = {"el": FILL[0], "istek": FILL[1], "yanit": FILL[2],
               "kapat": FILL[3]}
    kenar = {"el": EDGE[0], "istek": EDGE[1], "yanit": EDGE[2],
             "kapat": EDGE[3]}

    def hat(y, parcalar, baslik):
        _yazi(ax, 0.1, y + 1.05, baslik, fs=9, renk=ACCENT_L, ha="left",
              bold=True)
        x = 0.1
        for tur, s, w0 in parcalar:
            w = w0 * 0.8
            _box(ax, x, y, w - 0.06, 0.75, s, renkler[tur], kenar[tur],
                 fs=7.4)
            x += w
        return x

    hat(4.8, [("el", "el sıkışma\n(TCP+)", 2.0), ("istek", "GET 1", 1.3),
              ("yanit", "200", 1.3), ("kapat", "kapat", 1.1),
              ("el", "el sıkışma", 2.0), ("istek", "GET 2", 1.3),
              ("yanit", "200", 1.3), ("kapat", "kapat", 1.1),
              ("el", "el sıkışma", 2.0), ("istek", "GET 3", 1.3)],
          "Her istekte yeni bağlantı: 3 istek = 3 el sıkışma")
    hat(1.6, [("el", "el sıkışma", 2.0), ("istek", "GET 1", 1.3),
              ("yanit", "200", 1.3), ("istek", "GET 2", 1.3),
              ("yanit", "200", 1.3), ("istek", "GET 3", 1.3),
              ("yanit", "200", 1.3), ("kapat", "kapat", 1.1)],
          "Kalıcı bağlantı (keep-alive): tek el sıkışma")
    _yazi(ax, 7.0, 0.35, "Yatay eksen zaman. Genişlikler oransal değil; "
          "gösterim için ayarlandı.", fs=7.8, renk=MUTED)
    return _save(fig, _yol("keepalive"))


# 8. ETag ve 304 akisi ------------------------------------------------- #
def etag_akisi():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.6)
    _box(ax, 0.6, 7.8, 2.8, 0.7, "İstemci (önbellek)", FILL[0], EDGE[0],
         fs=8.6, bold=True)
    _box(ax, 10.6, 7.8, 2.8, 0.7, "Sunucu", FILL[1], EDGE[1], fs=8.6,
         bold=True)
    _cizgi(ax, 2.0, 0.6, 7.7)
    _cizgi(ax, 12.0, 0.6, 7.7)
    _arrow(ax, 2.0, 6.9, 12.0, 6.9, col=ACCENT, lw=1.4)
    _yazi(ax, 7.0, 7.2, "1. GET /a.css", fs=8.4, renk=ACCENT)
    _arrow(ax, 12.0, 6.1, 2.0, 6.1, col=ACCENT_L, lw=1.4)
    _yazi(ax, 7.0, 5.75, "200 OK, ETag \"v7\", max-age=60, gövde",
          fs=8.4, renk=ACCENT_L)
    _box(ax, 3.0, 4.8, 8.0, 0.65,
         "60 saniye içinde: taze, ağa çıkılmaz (istek yok)",
         FILL[2], EDGE[2], fs=8.4)
    _arrow(ax, 2.0, 3.6, 12.0, 3.6, col=ACCENT, lw=1.4)
    _yazi(ax, 7.0, 3.95, "2. GET /a.css   If-None-Match: \"v7\"",
          fs=8.4, renk=ACCENT)
    _arrow(ax, 12.0, 2.85, 2.0, 2.85, col=EDGE[1], lw=1.4)
    _yazi(ax, 7.0, 3.1, "304 Not Modified  (gövde yok)", fs=8.4,
          renk=EDGE[1])
    _yazi(ax, 7.0, 2.4, "ETag hâlâ \"v7\": önbellek kopyası yeniden "
          "kullanılır", fs=8.0, renk=MUTED)
    _arrow(ax, 12.0, 1.4, 2.0, 1.4, col=EDGE[3], lw=1.4, rad=0.0)
    _yazi(ax, 7.0, 1.7, "veya 200 OK, yeni ETag \"v8\", yeni gövde",
          fs=8.0, renk=EDGE[3])
    return _save(fig, _yol("etag_akisi"))


# 9. HTTP/1.1, HTTP/2, HTTP/3 yigin karsilastirmasi -------------------- #
def surum_yigin():
    fig, ax = _tuval(9.6, 6.0, xl=12, yl=9.2)
    sutunlar = [
        ("HTTP/1.1", ["HTTP/1.1 metin mesajlar", "TCP", "IP"],
         "Bağlantı başına sıra. Bir istek\nbitmeden sonraki beklenir.",
         FILL[3], EDGE[3]),
        ("HTTP/2", ["HTTP/2 ikili çerçeve + HPACK", "TLS 1.3",
                    "TCP", "IP"],
         "Tek TCP bağlantısında çoklu akış.\nBir TCP kaybı tüm akışları bekletir.",
         FILL[0], EDGE[0]),
        ("HTTP/3", ["HTTP/3 + QPACK", "QUIC (akışlar + TLS 1.3)", "UDP",
                    "IP"],
         "Bağımsız akışlar. Kayıp yalnız\no akışı bekletir (HOL çözülür).",
         FILL[1], EDGE[1]),
    ]
    for k, (ad, katmanlar, not_, fill, edge) in enumerate(sutunlar):
        x = 0.3 + k * 4.0
        _yazi(ax, x + 1.75, 8.85, ad, fs=10.5, renk=edge, bold=True)
        for j, s in enumerate(katmanlar):
            y = 7.6 - j * 1.05
            _box(ax, x, y, 3.5, 0.8, s, fill, edge, fs=8.2)
        _yazi(ax, x + 1.75, 1.65, not_, fs=7.9, renk=INK)
    _yazi(ax, 6.0, 0.6, "Üstteki katman uygulama, alttaki taşıma. HTTP "
          "anlamı (yöntem, durum kodu, başlık) üç sürümde de aynıdır.",
          fs=7.9, renk=MUTED)
    return _save(fig, _yol("surum_yigin"))


# 10. Sayfa yukleme gecikme bilesenleri (CSV'den) ---------------------- #
def gecikme_bilesen():
    with open(os.path.join(VERI, "b30_bilesen.csv"), encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    # Her olcum: (dns, tcp, tls, ilk_bayt, govde, toplam) saniye cinsinden.
    # ilk_bayt = starttransfer - appconnect; govde = toplam - starttransfer
    kayitlar = []
    for r in satirlar:
        dns, tcp = float(r["dns_s"]), float(r["tcp_s"])
        tls, ilk = float(r["tls_s"]), float(r["ttfb_s"])
        top = float(r["toplam_s"])
        govde = top - (dns + tcp + tls + ilk)
        kayitlar.append((dns, tcp, tls, ilk, govde, top))
    medyan = statistics.median(k[5] for k in kayitlar)
    # Bilesenler toplamla tutarli kalsin diye: toplama en yakin olcum
    temsil = min(kayitlar, key=lambda k: abs(k[5] - medyan))
    toplam_ms = temsil[5] * 1000
    bilesen = [("DNS", temsil[0], FILL[2], EDGE[2]),
               ("TCP el sıkışması", temsil[1], FILL[0], EDGE[0]),
               ("TLS el sıkışması", temsil[2], FILL[3], EDGE[3]),
               ("İlk bayta kadar (istek + sunucu)", temsil[3], FILL[1],
                EDGE[1]),
               ("Gövde aktarımı", temsil[4], FILL[4], EDGE[4])]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, toplam_ms * 1.02)
    ax.set_ylim(-0.6, 3.4)
    ax.axis("off")
    x = 0.0
    for ad, deger, fill, edge in bilesen:
        w = deger * 1000
        ax.add_patch(plt.Rectangle((x, 1.9), w, 1.0, facecolor=fill,
                                   edgecolor=edge, lw=1.2))
        if w >= 12:
            ax.text(x + w / 2, 2.4, "%.0f" % w, ha="center", va="center",
                    fontsize=9, color=INK, weight="bold")
        x += w
    for k, (ad, deger, fill, edge) in enumerate(bilesen):
        y = 1.45 - k * 0.42
        ax.add_patch(plt.Rectangle((0, y - 0.12), 5, 0.24, facecolor=fill,
                                   edgecolor=edge, lw=1.0))
        ax.text(9, y, "%s: %.1f ms" % (ad, deger * 1000), va="center",
                fontsize=8.2, color=INK)
    ax.text(0, 3.1, "example.com (https), 10 ölçüm", ha="left",
            va="center", fontsize=9, color=MUTED)
    ax.text(toplam_ms, 3.1, "Toplam: %.0f ms" % toplam_ms, ha="right",
            va="center", fontsize=9.5, color=ACCENT, weight="bold")
    return _save(fig, _yol("gecikme_bilesen"))


if __name__ == "__main__":
    for f in (dns_hiyerarsi, dns_cozumleme, dns_mesaj, dns_isaretci,
              dhcp_dora, http_anatomi, keepalive, etag_akisi,
              surum_yigin, gecikme_bilesen):
        print(f())
