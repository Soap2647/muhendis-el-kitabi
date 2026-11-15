# -*- coding: utf-8 -*-
"""Bolum 29 - 'OSI & TCP/IP' diyagramlari.

Olcum sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b29_aimd.csv   AIMD simulasyonu (aimd_sim.py)
  b29_nagle.csv  Nagle / TCP_NODELAY olcumu (nagle_olcum.py)
Diger sekiller bolumdeki ornek degerlerden cizilir.
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

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b29_%s.png" % ad)


def _tuval(w, h, xl=14, yl=10):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _kutu(ax, x, y, w, h, metin, k=0, fs=10, kalin=False, bold=False):
    _box(ax, x, y, w, h, metin, fill=FILL[k % 5], edge=EDGE[k % 5],
         fs=fs, bold=bold or kalin)


# 1. OSI ve TCP/IP katmanlari ----------------------------------------------- #
def osi_tcpip():
    fig, ax = _tuval(9.6, 6.4)
    osi = [
        ("7. Uygulama", "HTTP, DNS, SMTP"),
        ("6. Sunum", "biçim, şifreleme (genel)"),
        ("5. Oturum", "oturum yönetimi (genel)"),
        ("4. Taşıma", "TCP, UDP"),
        ("3. Ağ", "IPv4, IPv6, ICMP"),
        ("2. Veri bağı", "Ethernet, Wi-Fi, ARP"),
        ("1. Fiziksel", "kablo, sinyal, bit"),
    ]
    ax.text(3.0, 9.9, "OSI (7 katman)", ha="center", fontsize=11, weight="bold",
            color=INK)
    ax.text(10.7, 9.9, "TCP/IP (4 katman)", ha="center", fontsize=11,
            weight="bold", color=INK)
    for i, (ad, ornek) in enumerate(osi):
        y = 8.6 - i * 1.15
        _kutu(ax, 0.4, y, 5.2, 0.95, ad + "\n" + ornek, k=i % 5, fs=9)
    # TCP/IP sütunu: uygulama (OSI 7-5), taşıma (4), internet (3),
    # ağ erişimi (OSI 2-1). Kutular OSI satırlarıyla aynı hizada.
    _kutu(ax, 7.9, 6.3, 5.6, 3.25,
          "Uygulama\nHTTP, DNS (Bölüm 30)\nsoketler (Bölüm 31)", k=0, fs=9)
    _kutu(ax, 7.9, 5.15, 5.6, 0.95, "Taşıma\nTCP, UDP", k=3, fs=9)
    _kutu(ax, 7.9, 4.0, 5.6, 0.95, "İnternet\nIPv4, IPv6, ICMP", k=4, fs=9)
    _kutu(ax, 7.9, 1.7, 5.6, 2.1,
          "Ağ erişimi\nEthernet, Wi-Fi, ARP\nfiziksel katman", k=1, fs=9)
    # eşleşme çizgileri (OSI satırının orta hizası)
    for y in [7.925, 5.625, 3.925, 3.325]:
        ax.plot([5.6, 7.9], [y, y], color=MUTED, lw=1.0)
    ax.text(6.75, 0.25, "Sağdaki dört katman, soldaki yedi katmanın birleşik karşılığıdır.",
            ha="center", fontsize=8.5, color=MUTED)
    return _save(fig, _yol("osi_tcpip"))


# 2. Kapsulleme: bayt bayt iç ice ----------------------------------------- #
def kapsulleme():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6)
    x = 0.6
    parcalar = [
        ("Ethernet\nbaşlığı\n14 bayt", 1.9, 0),
        ("IPv4\nbaşlığı\n20 bayt", 2.0, 1),
        ("TCP\nbaşlığı\n20 bayt", 2.0, 2),
        ("HTTP isteği\n(yük, değişken)", 4.2, 3),
        ("Ethernet\nFCS\n4 bayt", 1.7, 4),
    ]
    konumlar = []
    for metin, w, k in parcalar:
        _box(ax, x, 2.8, w, 1.5, metin, fill=FILL[k], edge=EDGE[k], fs=9)
        konumlar.append((x, x + w))
        x += w
    ax.text(0.6, 5.2, "Üstten aşağıya: her katman kendi başlığını önüne ekler.",
            fontsize=9, color=INK)
    # parantezler (altta)
    tcp_bas, tcp_son = konumlar[2][0], konumlar[3][1]
    ip_bas, ip_son = konumlar[1][0], konumlar[3][1]
    eth_bas, eth_son = konumlar[0][0], konumlar[4][1]
    for (a, b, y, metin, renk) in [
        (tcp_bas, tcp_son, 2.2, "TCP segmenti: başlık + yük", EDGE[2]),
        (ip_bas, ip_son, 1.6, "IP paketi: başlık + segment", EDGE[1]),
        (eth_bas, eth_son, 1.0, "Ethernet çerçevesi: başlık + paket + FCS", EDGE[0]),
    ]:
        ax.plot([a + 0.05, b - 0.05], [y, y], color=renk, lw=1.6)
        ax.plot([a + 0.05, a + 0.05], [y, y + 0.12], color=renk, lw=1.6)
        ax.plot([b - 0.05, b - 0.05], [y, y + 0.12], color=renk, lw=1.6)
        ax.text((a + b) / 2, y - 0.3, metin, ha="center", fontsize=9, color=INK)
    ax.text(0.6, 0.1, "Alıcı tersini yapar: her katman kendi başlığını okur, çıkarır, "
            "üst katmana verir.", fontsize=8.5, color=MUTED)
    return _save(fig, _yol("kapsulleme"))


# 3. Baslik bit cetvelleri ------------------------------------------------- #
def _alan_serit(ax, x0, y, olcek, alanlar, h=0.8, fs=7.5):
    x = x0
    for i, (ad, bit) in enumerate(alanlar):
        w = bit * olcek
        ax.add_patch(Rectangle((x, y), w, h, facecolor=FILL[i % 5],
                               edgecolor=EDGE[i % 5], lw=0.9))
        ax.text(x + w / 2, y + h / 2, ad, ha="center", va="center",
                fontsize=fs, color=INK)
        x += w


def _cetvel(ax, x0, y, olcek, bitler):
    for b in bitler:
        ax.text(x0 + b * olcek, y, str(b), ha="center", va="bottom",
                fontsize=7, color=MUTED)


def basliklar():
    fig, ax = _tuval(9.6, 7.6, xl=14, yl=11.2)
    olcek = 0.2
    ax.text(0.4, 10.9, "IPv4 başlığı (20 bayt)", fontsize=10, weight="bold",
            color=INK)
    ax.text(7.4, 10.9, "TCP başlığı (20 bayt, seçenek yok)", fontsize=10,
            weight="bold", color=INK)
    _cetvel(ax, 0.4, 10.15, olcek, [0, 8, 16, 24, 31])
    _cetvel(ax, 7.4, 10.15, olcek, [0, 8, 16, 24, 31])
    ipv4 = [
        [("Sür.", 4), ("IHL", 4), ("DSCP/ECN", 8), ("Toplam uzunluk", 16)],
        [("Kimlik", 16), ("Bayrak", 3), ("Parça ofseti", 13)],
        [("TTL", 8), ("Protokol", 8), ("Sağlama", 16)],
        [("Kaynak IP", 32)],
        [("Hedef IP", 32)],
    ]
    tcp = [
        [("Kaynak port", 16), ("Hedef port", 16)],
        [("Sıra numarası", 32)],
        [("Onay numarası", 32)],
        [("Ofset", 4), ("Ayr.", 4), ("Bayraklar", 8), ("Pencere", 16)],
        [("Sağlama", 16), ("Acil işaretçi", 16)],
    ]
    ys = [9.2, 8.2, 7.2, 6.2, 5.2]
    for satir, y in zip(ipv4, ys):
        _alan_serit(ax, 0.4, y, olcek, satir, h=0.8)
    for satir, y in zip(tcp, ys):
        _alan_serit(ax, 7.4, y, olcek, satir, h=0.8)
    ax.text(0.4, 4.6, "IHL: başlık uzunluğu 32 bitlik sözcük sayısı (5 = 20 bayt)",
            fontsize=8, color=MUTED)
    ax.text(7.4, 4.6, "Ofset: başlık uzunluğu (5 = 20 bayt, 6 = 24 bayt)",
            fontsize=8, color=MUTED)
    # UDP
    ax.text(0.4, 3.6, "UDP başlığı (8 bayt)", fontsize=10, weight="bold", color=INK)
    _alan_serit(ax, 0.4, 2.7, olcek, [("Kaynak port", 16), ("Hedef port", 16)])
    _alan_serit(ax, 0.4, 1.8, olcek, [("Uzunluk", 16), ("Sağlama", 16)])
    # Ethernet
    ax.text(0.4, 1.0, "Ethernet çerçeve başlığı (14 bayt)", fontsize=10,
            weight="bold", color=INK)
    _alan_serit(ax, 0.4, 0.2, 0.12, [("Hedef MAC (48)", 48),
                                    ("Kaynak MAC (48)", 48),
                                    ("EtherType (16)", 16)], h=0.7)
    ax.text(7.4, 2.9, "Her kutunun genişliği bit sayısıyla orantılıdır.",
            fontsize=8.5, color=MUTED)
    ax.text(7.4, 2.4, "Ağ başlıkları büyük uçtur (ağ bayt sırası, Bölüm 1.5).",
            fontsize=8.5, color=MUTED)
    return _save(fig, _yol("basliklar"))


# 4. Alt ag bolme ---------------------------------------------------------- #
def alt_ag():
    fig, ax = _tuval(9.6, 5.4)
    ax.text(0.3, 9.2, "192.168.10.0/24 ağı, /26 ile dört parçaya bölünür",
            fontsize=11, weight="bold", color=INK)
    blok = [("192.168.10.0/26\n\nilk .1\nson .62\nyayın .63", 0),
            ("192.168.10.64/26\n\nilk .65\nson .126\nyayın .127", 1),
            ("192.168.10.128/26\n\nilk .129\nson .190\nyayın .191", 2),
            ("192.168.10.192/26\n\nilk .193\nson .254\nyayın .255", 3)]
    for i, (metin, k) in enumerate(blok):
        x = 0.3 + i * 3.4
        _box(ax, x, 5.9, 3.2, 2.0, metin, fill=FILL[k], edge=EDGE[k], fs=9,
             bold=(i == 1))
    # vurgu: 192.168.10.77 hangi bloğa düşer
    ax.add_patch(Rectangle((3.7, 5.9), 3.2, 2.0, fill=False, edgecolor=ACCENT,
                           lw=2.4))
    ax.text(5.3, 5.45, "192.168.10.77 bu bloğa düşer", ha="center",
            fontsize=9.5, color=ACCENT, weight="bold")
    _arrow(ax, 5.3, 5.6, 5.3, 5.95, col=ACCENT, lw=1.4)
    ax.text(0.3, 4.4, "Her /26 bloğu 2^(32-26) = 64 adres içerir: 62 host, 1 ağ, 1 yayın.",
            fontsize=9, color=INK)
    ax.text(0.3, 3.7, "Ağ adresi = IP AND maske; yayın adresi = ağ OR (NOT maske).",
            fontsize=9, color=INK)
    ax.text(0.3, 3.0, "Maske /26: 255.255.255.192, son oktette 11000000 (ikilik).",
            fontsize=9, color=INK)
    return _save(fig, _yol("alt_ag"))


# 5. En uzun onek eslesmesi ------------------------------------------------ #
def lpm():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=10)
    x0, olcek = 4.6, 8.6 / 32.0
    ax.text(0.3, 9.6, "Hedef 10.1.2.130 için önek çubukları (her çubuk ilk p biti kapsar)",
            fontsize=10, weight="bold", color=INK)
    for b in [0, 8, 16, 24, 32]:
        ax.text(x0 + b * olcek, 8.7, str(b), ha="center", fontsize=8, color=MUTED)
    ax.plot([x0, x0 + 8.6], [8.45, 8.45], color=RULE, lw=0.8)
    oneki = [
        ("0.0.0.0/0  -> eth0 (varsayılan)", 0, 0),
        ("10.0.0.0/8  -> vpn0", 8, 1),
        ("10.1.0.0/16  -> vpn1", 16, 2),
        ("10.1.2.0/24  -> ofis-lan", 24, 3),
        ("10.1.2.128/25  -> sensor-ag", 25, 4),
    ]
    for i, (metin, p, k) in enumerate(oneki):
        y = 7.5 - i * 0.95
        ax.text(0.3, y + 0.22, metin, fontsize=9, va="center",
                color=ACCENT if p == 25 else INK, weight="bold" if p == 25 else "normal")
        genislik = max(p * olcek, 0.12)
        renk = ACCENT if p == 25 else FILL[1]
        kenar = ACCENT if p == 25 else MUTED
        ax.add_patch(Rectangle((x0, y), genislik, 0.45, facecolor=renk,
                               edgecolor=kenar, lw=1.0))
        ax.text(x0 + genislik + 0.1, y + 0.22, "/%d" % p, va="center",
                fontsize=8.5, color=INK)
    ax.text(x0, 2.6, "Bu hedefi kapsayan beş önek var; en uzun (/25) kazanır.",
            fontsize=9.5, color=INK)
    ax.text(x0, 1.9, "Tablo sırası önemsiz: karar yalnızca önek uzunluğuna bakar.",
            fontsize=9, color=MUTED)
    ax.text(x0, 1.2, "Varsayılan yol (/0) her hedefi kapsar; en son başvurulan çaredir.",
            fontsize=9, color=MUTED)
    return _save(fig, _yol("lpm"))


# 6. TCP durum makinesi ---------------------------------------------------- #
def tcp_durum():
    fig, ax = _tuval(9.6, 7.0, xl=14, yl=10)
    G = 1.0   # yarı genişlik
    H = 0.4   # yarı yükseklik
    dugum = {
        "CLOSED": (1.6, 8.6, 0), "LISTEN": (1.6, 6.4, 0),
        "SYN_SENT": (4.6, 8.6, 0), "SYN_RCVD": (4.6, 6.4, 0),
        "ESTABLISHED": (7.6, 6.4, 1), "FIN_WAIT_1": (7.6, 8.6, 2),
        "FIN_WAIT_2": (10.6, 8.6, 2), "TIME_WAIT": (10.6, 6.4, 2),
        "CLOSE_WAIT": (7.6, 4.2, 3), "LAST_ACK": (10.6, 4.2, 3),
        "CLOSED_SON": (12.9, 1.9, 0),
    }
    for ad, (x, y, k) in dugum.items():
        metin = "CLOSED" if ad == "CLOSED_SON" else ad
        _box(ax, x - G, y - H, 2 * G, 2 * H, metin, fill=FILL[k], edge=EDGE[k],
             fs=9, bold=(ad == "ESTABLISHED"))

    # Oklar: kenarlardan kenarlara, kutuların içine girmeden
    oklar = [
        ((2.6, 8.6), (3.6, 8.6), "1"),
        ((1.6, 8.2), (1.6, 6.8), "2"),
        ((2.6, 6.4), (3.6, 6.4), "3"),
        ((5.6, 8.2), (6.8, 6.8), "4"),
        ((5.6, 6.4), (6.6, 6.4), "5"),
        ((7.6, 6.8), (7.6, 8.2), "6"),
        ((8.6, 8.6), (9.6, 8.6), "7"),
        ((10.6, 8.2), (10.6, 6.8), "8"),
        ((7.6, 6.0), (7.6, 4.6), "9"),
        ((8.6, 4.2), (9.6, 4.2), "10"),
        ((11.6, 3.9), (12.3, 2.3), "11"),
        ((11.6, 6.2), (13.0, 2.3), "12"),
    ]
    for (x1, y1), (x2, y2), no in oklar:
        _arrow(ax, x1, y1, x2, y2, col=INK, lw=1.2)
    etiketler = [
        (3.1, 8.95, "1"), (1.1, 7.5, "2"), (3.1, 6.75, "3"), (6.0, 7.6, "4"),
        (6.1, 6.75, "5"), (7.95, 7.5, "6"), (9.1, 8.95, "7"), (10.95, 7.5, "8"),
        (7.95, 5.2, "9"), (9.1, 4.55, "10"), (12.1, 3.0, "11"), (12.6, 4.7, "12"),
    ]
    for x, y, no in etiketler:
        ax.text(x, y, no, ha="center", va="center", fontsize=8.5, color=ACCENT,
                weight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.5))

    satirlar = [
        "1  CLOSED -> SYN_SENT    aktif açma: SYN gönder",
        "2  CLOSED -> LISTEN      pasif açma: listen()",
        "3  LISTEN -> SYN_RCVD    SYN al: SYN+ACK gönder",
        "4  SYN_SENT -> ESTABLISHED   SYN+ACK al: ACK gönder",
        "5  SYN_RCVD -> ESTABLISHED   ACK al",
        "6  ESTABLISHED -> FIN_WAIT_1   close(): FIN gönder",
        "7  FIN_WAIT_1 -> FIN_WAIT_2   ACK al",
        "8  FIN_WAIT_2 -> TIME_WAIT    FIN al: ACK gönder",
        "9  ESTABLISHED -> CLOSE_WAIT  FIN al: ACK gönder",
        "10 CLOSE_WAIT -> LAST_ACK     close(): FIN gönder",
        "11 LAST_ACK -> CLOSED         ACK al",
        "12 TIME_WAIT -> CLOSED        2MSL süresi dolar",
    ]
    for i, s in enumerate(satirlar):
        ax.text(0.4, 3.5 - i * 0.27, s, fontsize=8.2, color=INK,
                family="DejaVu Sans Mono")
    ax.text(0.4, 0.25, "Üst satır: açılış ve aktif kapanış. TIME_WAIT yalnızca aktif kapatan tarafta oluşur.",
            fontsize=7.8, color=MUTED)
    return _save(fig, _yol("tcp_durum"))


# 7. El sikisma ve kapanis zaman cizelgesi ------------------------------ #
def el_sikisma():
    fig, ax = _tuval(9.6, 7.0, xl=14, yl=10.4)
    ist, sun = 3.7, 11.6
    ax.text(ist, 10.0, "İstemci", ha="center", fontsize=11, weight="bold", color=INK)
    ax.text(sun, 10.0, "Sunucu", ha="center", fontsize=11, weight="bold", color=INK)
    ax.plot([ist, ist], [0.9, 9.6], color=MUTED, lw=1.0, ls="--")
    ax.plot([sun, sun], [0.9, 9.6], color=MUTED, lw=1.0, ls="--")
    mesajlar = [
        (8.8, "right", "SYN  seq=x", "1. Üçlü el sıkışma"),
        (7.9, "left", "SYN+ACK  seq=y  ack=x+1", None),
        (7.0, "right", "ACK  ack=y+1", None),
        (5.8, "right", "veri  seq=x+1  (n bayt)", "Veri"),
        (4.9, "left", "ACK  ack=x+1+n", None),
        (3.7, "right", "FIN  seq=u", "2. Dörtlü kapanış"),
        (2.8, "left", "ACK  ack=u+1", None),
        (2.0, "left", "FIN  seq=v", None),
        (1.1, "right", "ACK  ack=v+1", None),
    ]
    for y, yon, metin, baslik in mesajlar:
        if yon == "right":
            _arrow(ax, ist + 0.05, y, sun - 0.05, y, col=ACCENT, lw=1.4)
            ax.text((ist + sun) / 2, y + 0.18, metin, ha="center", fontsize=8.8,
                    color=INK)
        else:
            _arrow(ax, sun - 0.05, y, ist + 0.05, y, col=ACCENT_L, lw=1.4)
            ax.text((ist + sun) / 2, y + 0.18, metin, ha="center", fontsize=8.8,
                    color=INK)
        if baslik:
            ax.text(0.35, y + 0.18, baslik, fontsize=8.5, color=MUTED,
                    weight="bold", ha="left")
    ax.text(ist + 0.2, 0.35, "TIME_WAIT (2MSL)", ha="left", fontsize=8.5,
            color=ACCENT, weight="bold")
    ax.text(sun + 0.2, 0.35, "CLOSED", ha="left", fontsize=8.5, color=MUTED)
    return _save(fig, _yol("el_sikisma"))


# 8. Kayan pencere --------------------------------------------------------- #
def kayan_pencere():
    fig, ax = _tuval(9.6, 4.0, xl=14, yl=6)
    n = 14
    x0, w = 0.5, 0.85
    for i in range(n):
        seg = i + 1
        if seg <= 3:
            k, metin = 4, "%d" % seg
        elif seg <= 7:
            k, metin = 1, "%d" % seg
        elif seg <= 9:
            k, metin = 2, "%d" % seg
        else:
            k, metin = 4, "%d" % seg
        _box(ax, x0 + i * w, 2.7, w * 0.92, 1.1, metin, fill=FILL[k],
             edge=EDGE[k], fs=9)
    # kutu etiketleri
    ax.text(x0 + 1.5 * w, 4.6, "onaylandı", ha="center", fontsize=9, color=MUTED)
    ax.text(x0 + 5.5 * w, 4.6, "gönderildi, onay bekliyor", ha="center",
            fontsize=9, color=ACCENT_L)
    ax.text(x0 + 8.5 * w, 4.6, "gönderilebilir", ha="center", fontsize=9,
            color=EDGE[2])
    ax.text(x0 + 11.5 * w, 4.6, "pencere dışı", ha="center", fontsize=9, color=MUTED)
    # imler
    una = x0 + 3 * w
    nxt = x0 + 7 * w
    edge = x0 + 9 * w
    for x, metin in [(una, "SND.UNA"), (nxt, "SND.NXT"), (edge, "UNA + pencere")]:
        ax.plot([x, x], [2.4, 2.1], color=INK, lw=1.2)
        ax.text(x, 1.7, metin, ha="center", fontsize=8.5, color=INK, weight="bold")
    ax.text(0.5, 0.9, "Sayılar segment numarasıdır; gerçek TCP'de sayılar bayt cinsindendir.",
            fontsize=8.5, color=MUTED)
    return _save(fig, _yol("kayan_pencere"))


# 9. AIMD testere disi ----------------------------------------------------- #
def aimd_grafik():
    veri = _oku_csv("b29_aimd.csv")
    rtt = [int(r["rtt"]) for r in veri]
    cw = [int(r["cwnd"]) for r in veri]
    ss = [int(r["ssthresh"]) for r in veri]
    kayip = [int(r["rtt"]) for r in veri if r["kayip"] == "1"]
    kayip_y = [int(r["cwnd"]) for r in veri if r["kayip"] == "1"]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.plot(rtt, cw, color=ACCENT, lw=1.8, label="cwnd (pencere, paket)")
    ax.plot(rtt, ss, color=ACCENT_L, lw=1.2, ls="--", label="ssthresh")
    ax.axhline(40, color=MUTED, lw=0.9, ls=":")
    ax.text(1, 43.5, "yol kapasitesi (40)", ha="left", fontsize=8.5, color=MUTED)
    ax.scatter(kayip, kayip_y, marker="x", s=60, color=INK, zorder=3,
               label="kayıp (çarpımsal azalma)")
    ax.set_xlabel("RTT adımı")
    ax.set_ylabel("pencere (paket)")
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 58)
    ax.grid(True, color=RULE, lw=0.6)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper center", ncol=3, fontsize=8.5, frameon=False)
    return _save(fig, _yol("aimd"))


# 10. Nagle olcumu -------------------------------------------------------- #
def nagle_grafik():
    veri = _oku_csv("b29_nagle.csv")
    etiket = []
    deger = []
    for r in veri:
        ad = r["senaryo"].strip('"')
        etiket.append(ad.replace(": ", ":\n", 1))
        deger.append(float(r["medyan_ms"]))
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    renk = [FILL[0], ACCENT, EDGE[1]]
    kenar = [EDGE[0], ACCENT, EDGE[1]]
    cubuklar = ax.bar(range(len(deger)), deger, color=renk, edgecolor=kenar,
                      width=0.55)
    ax.set_yscale("log")
    ax.set_ylim(0.01, 200)
    ax.set_xticks(range(len(deger)))
    ax.set_xticklabels(etiket, fontsize=8.5)
    ax.set_ylabel("bir tur medyanı (ms, log)")
    for c, d in zip(cubuklar, deger):
        ax.text(c.get_x() + c.get_width() / 2, d * 1.25, "%.3f ms" % d,
                ha="center", fontsize=9, color=INK)
    ax.grid(True, axis="y", color=RULE, lw=0.6)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    return _save(fig, _yol("nagle"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in [osi_tcpip, kapsulleme, basliklar, alt_ag, lpm, tcp_durum,
              el_sikisma, kayan_pencere, aimd_grafik, nagle_grafik]:
        print(f.__name__, "->", f())
