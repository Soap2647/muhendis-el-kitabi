# -*- coding: utf-8 -*-
"""Bolum 35 - 'NoSQL' diyagramlari.

Olcum sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b35_bloom.csv        Bloom yanlis pozitif: teorik ve olculen
  b35_tutarli_hash.csv naif hash%N ve tutarli halka: tasinan oran, yuk
  b35_quorum.csv       quorum (R, W, N=3) bayat okuma olasiligi
  b35_zaman.csv        delta-of-delta zaman damgasi: bit / nokta
Diger sekiller bolumdeki kavramsal ornekten cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b35_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _stil(ax):
    for s in ax.spines.values():
        s.set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=8.5)


# 1. NoSQL aileri: karar haritasi ----------------------------------- #
def aileler():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=9.6)
    _box(ax, 3.9, 8.1, 6.2, 0.9,
         "Verinin şekli ve erişim deseni nasıl?", FILL[0], EDGE[0],
         fs=10, bold=True)
    aile = [
        ("Anahtar-değer", "Redis, RocksDB", "Önbellek, oturum,\nsayaç",
         FILL[1], EDGE[1]),
        ("Belge", "MongoDB", "Değişken yapılı JSON,\nbirlikte okunan veri",
         FILL[2], EDGE[2]),
        ("Geniş sütun", "Cassandra, HBase", "Yoğun yazma, satır\nanahtarına göre",
         FILL[3], EDGE[3]),
        ("Graf", "Neo4j", "İlişki gezintisi,\nöneri, yol bulma",
         FILL[4], EDGE[4]),
        ("Zaman serisi", "InfluxDB, TimescaleDB", "Telemetri, metrik;\nzaman aralığı sorgusu",
         FILL[0], EDGE[0]),
    ]
    xs = [0.2, 2.95, 5.7, 8.45, 11.2]
    for x, (ad, ornek, ne, fill, edge) in zip(xs, aile):
        _arrow(ax, 7.0, 8.1, x + 1.3, 6.85, col=MUTED, lw=0.9)
        _box(ax, x, 3.7, 2.6, 3.1,
             ad + "\n\n" + ornek + "\n\n" + ne, fill, edge, fs=8.4)
    ax.text(7.0, 2.7, "İlişkisel model (Bölüm 33-34) çoğu iş için hâlâ "
            "varsayılandır:", ha="center", fontsize=9, color=INK)
    ax.text(7.0, 1.9, "ilişki, tutarlılık ve esnek sorgu ister misin? "
            "Önce ona bak.", ha="center", fontsize=9, color=INK)
    ax.text(7.0, 0.9, "NoSQL, belirli bir erişim deseni için bazı "
            "özellikleri (tutarlılık, JOIN, şema) feda eder.",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("aileler"))


# 2. B+ agaci ve LSM yazma yolu ------------------------------------- #
def bplus_lsm():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=9.0)
    ax.text(3.4, 8.55, "B+ ağacı: yerinde güncelleme", ha="center",
            fontsize=9.6, weight="bold", color=INK)
    ax.text(10.6, 8.55, "LSM: hep sona ekle", ha="center", fontsize=9.6,
            weight="bold", color=INK)
    sol = ["Kökten yaprağa in\n(birkaç disk sayfası)",
           "Yaprak sayfasını oku\n(rastgele G/Ç)",
           "Kaydı yerinde değiştir",
           "Sayfayı yaz\n(rastgele G/Ç)",
           "Dolarsa sayfayı böl"]
    sag = ["Günlüğe ekle (WAL)\n(sıralı yazma)",
           "Memtable'a koy\n(RAM, sıralı değil)",
           "Dolunca SSTable'a yaz\n(sıralı, değişmez dosya)",
           "Arka planda birleştir\n(compaction)",
           "Eski dosyaları sil"]
    for i in range(5):
        y = 7.0 - i * 1.5
        fill_s = FILL[0] if i % 2 == 0 else FILL[1]
        edge_s = EDGE[0] if i % 2 == 0 else EDGE[1]
        _box(ax, 0.4, y, 5.6, 0.95, sol[i], fill_s, edge_s, fs=8.6)
        _box(ax, 8.0, y, 5.6, 0.95, sag[i], FILL[2], EDGE[2], fs=8.6)
        if i < 4:
            _arrow(ax, 3.2, y, 3.2, y - 0.55, col=MUTED, lw=0.9)
            _arrow(ax, 10.8, y, 10.8, y - 0.55, col=MUTED, lw=0.9)
    ax.plot([6.9, 6.9], [0.2, 8.1], color=RULE, lw=1.0)
    ax.text(7.0, 0.1, "B+ ağacı yazmayı rastgele sayfalara dağıtır; LSM "
            "yazmayı sıralı bir dosyaya toplar.", ha="center",
            fontsize=8.4, color=MUTED)
    return _save(fig, _yol("bplus_lsm"))


# 3. LSM seviyeleri ve birlestirme ----------------------------------- #
def lsm_seviye():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=9.4)
    _box(ax, 0.4, 7.4, 3.6, 1.1, "memtable (RAM)\nen yeni kayıtlar",
         FILL[2], EDGE[2], fs=9)
    ax.text(0.4, 6.75, "Yazma buraya düşer", fontsize=8.4, color=MUTED)
    ax.text(4.8, 8.7, "Seviye 0: çakışan aralıklar (en yeni önce okunur)",
            fontsize=8.8, color=INK)
    l0 = [("T-9", "[b .. z]"), ("T-8", "[c .. p]"), ("T-7", "[a .. m]")]
    for i, (ad, rng) in enumerate(l0):
        _box(ax, 4.8 + i * 1.75, 6.6, 1.6, 1.25,
             ad + "\n" + rng, FILL[0], EDGE[0], fs=8.8)
    ax.text(4.8, 5.9, "Aralıklar üst üste biner: okuma birden çok "
            "tabloya bakar", fontsize=8.2, color=MUTED)
    ax.text(4.8, 4.6, "Seviye 1: aralıklar ayrık, sıralı",
            fontsize=8.8, color=INK)
    l1 = [("S-1", "[a .. f]"), ("S-2", "[g .. m]"), ("S-3", "[n .. z]")]
    for i, (ad, rng) in enumerate(l1):
        _box(ax, 4.8 + i * 2.85, 2.9, 2.6, 1.25,
             ad + "\n" + rng, FILL[1], EDGE[1], fs=8.8)
    _arrow(ax, 12.3, 6.5, 12.3, 4.35, col=ACCENT, lw=1.6)
    ax.text(12.5, 5.35, "birleştirme", fontsize=8.6, color=ACCENT)
    _arrow(ax, 4.0, 7.9, 4.75, 7.2, col=MUTED, lw=1.0)
    ax.text(0.4, 1.7, "Okuma sırası: memtable -> seviye 0 (yeniden "
            "eskiye) -> seviye 1.", fontsize=8.6, color=INK)
    ax.text(0.4, 0.9, "Birleştirme, aynı anahtarın eski kopyalarını ve "
            "silinmiş anahtarların mezar taşlarını atar.",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("lsm_seviye"))


# 4. Bloom bit dizisi (kavramsal) ------------------------------------ #
def bloom_bit():
    fig, ax = _tuval(9.6, 4.2, xl=14, yl=7.4)
    m = 16
    dolu = {1, 3, 6, 11, 13}  # A ve B eklendi (k = 3)
    x0, w = 0.6, 0.8
    for i in range(m):
        fill = EDGE[0] if i in dolu else "#ffffff"
        tcol = "#ffffff" if i in dolu else INK
        _box(ax, x0 + i * w, 4.3, w * 0.92, 0.9, str(1 if i in dolu else 0),
             fill, EDGE[0], fs=9, tcol=tcol, bold=True)
        ax.text(x0 + i * w + w * 0.46, 3.95, str(i), ha="center",
                fontsize=7.6, color=MUTED)
    ax.text(0.6, 6.7, "Ekleme: A -> {1, 6, 13}, B -> {3, 6, 11}",
            fontsize=9, color=INK)
    ax.text(0.6, 6.05, "Sorgu C -> {2, 6, 9}: 2. bit 0, kesinlikle yok",
            fontsize=9, color=INK)
    ax.text(0.6, 5.4, "Sorgu D -> {3, 6, 13}: hepsi 1, muhtemelen var "
            "(yanlış pozitif)", fontsize=9, color=ACCENT)
    for c, colr in ((2, MUTED), (3, ACCENT), (6, ACCENT), (13, ACCENT)):
        _arrow(ax, x0 + c * w + w * 0.46, 3.55, x0 + c * w + w * 0.46,
               3.35, col=colr, lw=1.2)
    ax.text(0.6, 2.7, "Hata yalnızca tek yönlüdür: 0 gören her zaman "
            "doğru 'yok' der.", fontsize=8.8, color=MUTED)
    ax.text(0.6, 2.0, "Bit silinemez: silme için sayaçlı varyant (counting "
            "Bloom) gerekir.", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("bloom_bit"))


# 5. Bloom yanlis pozitif: teorik ve olculen (CSV) ------------------- #
def bloom_olcum():
    rows = _oku_csv("b35_bloom.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    renk = {"4": EDGE[0], "8": EDGE[2], "10": ACCENT, "16": EDGE[4]}
    for oran in ("4", "8", "10", "16"):
        sat = [r for r in rows if r["m_n"] == oran]
        ks = [int(r["k"]) for r in sat]
        th = [float(r["teorik"]) for r in sat]
        ol = [float(r["olculen"]) for r in sat]
        ax.semilogy(ks, th, "-", color=renk[oran], lw=1.5,
                    label="m/n = %s (teorik)" % oran)
        ax.semilogy(ks, ol, "o", color=renk[oran], ms=4.5)
    ax.set_xlabel("hash fonksiyonu sayısı k", color=INK)
    ax.set_ylabel("yanlış pozitif oranı (log)", color=INK)
    ax.set_title("n = 10 000, 100 000 yok-sorgusu: çizgi teorik, nokta ölçüm",
                 fontsize=10, color=INK)
    ax.set_xticks(range(1, 11))
    ax.grid(True, which="both", color=RULE, lw=0.6)
    ax.legend(loc="lower left", fontsize=8.5, frameon=False)
    _stil(ax)
    return _save(fig, _yol("bloom_olcum"))


# 6. Tutarli hash halkasi ------------------------------------------- #
def halka():
    import math
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-3.9, 3.7)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Hash halkası (0 ile 2^32 arası, sarılı)", fontsize=10,
                 color=INK, weight="bold", pad=22)
    ax.add_patch(Circle((0, 0), 2.6, fill=False, ec=MUTED, lw=1.4))
    renk = {"A": EDGE[0], "B": EDGE[1], "C": EDGE[2], "D": EDGE[3]}
    gercek = {"A": 90, "B": 0, "C": 270, "D": 180}
    noktalar = []  # (açı, etiket, düğüm)
    for ad, aci in gercek.items():
        for j, dl in enumerate((-22, 22)):
            noktalar.append((aci + dl, "%s%d" % (ad, j + 1), ad))
    for aci, etk, ad in noktalar:
        t = math.radians(aci)
        x, y = 2.6 * math.cos(t), 2.6 * math.sin(t)
        ax.add_patch(Circle((x, y), 0.13, fc="white", ec=renk[ad], lw=1.2))
        ax.text(x * 1.2, y * 1.2, etk, ha="center", va="center",
                fontsize=8, color=renk[ad])
    for ad, aci in gercek.items():
        t = math.radians(aci)
        x, y = 2.6 * math.cos(t), 2.6 * math.sin(t)
        ax.add_patch(Circle((x, y), 0.22, fc=renk[ad], ec=renk[ad]))
        ax.text(x * 1.42, y * 1.42, "düğüm " + ad, ha="center",
                va="center", fontsize=9, weight="bold", color=INK)
    # Anahtar konumu -> saat yönünde (açı azalan) ilk sanal düğüm
    sirali = sorted(noktalar, key=lambda p: -p[0])
    for aci, etk in ((75, "k1"), (200, "k2"), (300, "k3")):
        sahip = sirali[0]
        for p in sirali:
            if p[0] < aci:
                sahip = p
                break
        t = math.radians(aci)
        kx, ky = 2.6 * math.cos(t), 2.6 * math.sin(t)
        ax.plot([kx], [ky], marker="s", ms=6, color=INK)
        ix, iy = 1.75 * math.cos(t), 1.75 * math.sin(t)
        ax.text(ix, iy, "%s -> %s" % (etk, sahip[2]), fontsize=8.6,
                color=INK, ha="center", va="center")
    ax.text(0, -3.55, "Anahtar, konumundan saat yönünde ilk sanal "
            "düğüme gider.", ha="center", fontsize=8.5, color=MUTED)
    return _save(fig, _yol("halka"))


# 7. Tasinan oran ve yuk dengesi (CSV) ------------------------------ #
def tasinan():
    rows = _oku_csv("b35_tutarli_hash.csv")
    etiket, tas, cvs, ideal = [], [], [], []
    for r in rows:
        if r["yontem"] == "naif":
            etiket.append("naif\nhash%N")
        else:
            etiket.append("halka\nv=%s" % r["vnode"])
        tas.append(float(r["tasinan"]))
        cvs.append(float(r["yuk_cv"]))
        ideal.append(float(r["ideal"]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    x = range(len(etiket))
    renk = [ACCENT] + [EDGE[0]] * (len(etiket) - 1)
    a1.bar(x, tas, color=renk, width=0.62)
    a1.axhline(ideal[0], color=MUTED, ls="--", lw=1.1)
    a1.text(len(etiket) - 0.5, ideal[0] + 0.02, "ideal 1/11",
            ha="right", fontsize=8.3, color=MUTED)
    a1.set_xticks(list(x))
    a1.set_xticklabels(etiket, fontsize=7.6)
    a1.set_ylabel("taşınan anahtar oranı", color=INK)
    a1.set_title("10 -> 11 düğüm", fontsize=9.6, color=INK)
    a2.bar(x, cvs, color=renk, width=0.62)
    a2.set_xticks(list(x))
    a2.set_xticklabels(etiket, fontsize=7.6)
    a2.set_ylabel("yük dağılımı (CV, düşük iyi)", color=INK)
    a2.set_title("düğümler arası yük dengesi", fontsize=9.6, color=INK)
    for a in (a1, a2):
        _stil(a)
        a.grid(True, axis="y", color=RULE, lw=0.6)
    fig.tight_layout()
    return _save(fig, _yol("tasinan"))


# 8. Cogaltma modelleri ------------------------------------------- #
def cogaltma():
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.6))
    for a in axs:
        a.set_xlim(0, 10)
        a.set_ylim(0, 8)
        a.axis("off")
    # lider-takipçi
    a = axs[0]
    a.set_title("Lider-takipçi", fontsize=9.6, color=INK)
    _box(a, 3.2, 5.6, 3.6, 1.4, "Lider\nyazmalar buradan", FILL[0],
         EDGE[0], fs=8.2)
    _box(a, 0.4, 1.4, 3.6, 1.4, "Takipçi 1\nokuma", FILL[1], EDGE[1],
         fs=8.2)
    _box(a, 6.0, 1.4, 3.6, 1.4, "Takipçi 2\nokuma", FILL[1], EDGE[1],
         fs=8.2)
    _arrow(a, 5.0, 7.9, 5.0, 7.1, col=MUTED, lw=0.9)
    a.text(5.25, 7.5, "yazma", fontsize=7.8, color=MUTED)
    _arrow(a, 4.2, 5.6, 2.4, 2.9, col=MUTED, lw=1.0)
    _arrow(a, 5.8, 5.6, 7.6, 2.9, col=MUTED, lw=1.0)
    a.text(5.0, 0.4, "Yazma tek noktadan geçer", ha="center",
           fontsize=7.8, color=MUTED)
    # cok lider
    a = axs[1]
    a.set_title("Çok lider", fontsize=9.6, color=INK)
    _box(a, 0.4, 3.4, 3.8, 1.6, "Lider 1\n(Ankara)", FILL[2], EDGE[2],
         fs=8.2)
    _box(a, 5.8, 3.4, 3.8, 1.6, "Lider 2\n(İzmir)", FILL[2], EDGE[2],
         fs=8.2)
    _arrow(a, 4.2, 4.2, 5.8, 4.2, col=ACCENT, lw=1.3, style="<|-|>")
    a.text(5.0, 2.4, "iki yerde aynı anahtar\nfarklı değer: çakışma",
           ha="center", fontsize=7.8, color=ACCENT)
    a.text(5.0, 0.5, "Çakışma çözümü gerekir", ha="center", fontsize=7.8,
           color=MUTED)
    # lidersiz
    a = axs[2]
    a.set_title("Lidersiz", fontsize=9.6, color=INK)
    _box(a, 3.4, 6.0, 3.2, 1.2, "İstemci", FILL[3], EDGE[3], fs=8.2)
    for i, x in enumerate((0.2, 3.5, 6.8)):
        _box(a, x, 2.0, 2.9, 1.3, "Kopya %d" % (i + 1), FILL[1], EDGE[1],
             fs=8.2)
        _arrow(a, 5.0, 5.95, x + 1.45, 3.4, col=MUTED, lw=0.9)
    a.text(5.0, 0.9, "W kopya yazar, R kopya okur", ha="center",
           fontsize=7.8, color=MUTED)
    a.text(5.0, 0.3, "R + W > N ise okuma yazmayı görür", ha="center",
           fontsize=7.8, color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("cogaltma"))


# 9. Quorum bayat okuma (CSV) ------------------------------------- #
def quorum():
    rows = _oku_csv("b35_quorum.csv")
    etiket = ["R=%s, W=%s" % (r["R"], r["W"]) for r in rows]
    th = [float(r["teorik"]) for r in rows]
    ol = [float(r["olculen"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    x = list(range(len(rows)))
    ax.bar([i - 0.2 for i in x], th, width=0.38, color=EDGE[0],
           label="teorik C(N-W,R)/C(N,R)")
    ax.bar([i + 0.2 for i in x], ol, width=0.38, color=ACCENT,
           label="200 000 denemede ölçüm")
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, fontsize=8.6)
    ax.set_ylabel("bayat okuma olasılığı", color=INK)
    ax.set_title("N = 3: yazma tamamlandıktan hemen sonra okuma",
                 fontsize=9.8, color=INK)
    ax.set_ylim(0, 0.8)
    for i, (t, r) in enumerate(zip(th, rows)):
        if int(r["R"]) + int(r["W"]) > int(r["N"]):
            ax.text(i, 0.04, "R+W>N", ha="center", fontsize=8,
                    color=ACCENT)
    ax.grid(True, axis="y", color=RULE, lw=0.6)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False)
    _stil(ax)
    return _save(fig, _yol("quorum"))


# 10. Delta-of-delta zaman damgasi (CSV) ------------------------- #
def zaman_dod():
    rows = _oku_csv("b35_zaman.csv")
    etiket = [r["senaryo"].replace(", ", ",\n") for r in rows]
    bpn = [float(r["bit_nokta"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    x = list(range(len(rows)))
    ax.bar(x, bpn, width=0.55, color=EDGE[0])
    ax.axhline(64, color=ACCENT, ls="--", lw=1.2)
    ax.text(len(rows) - 0.55, 62, "ham 64 bit", ha="right", va="top",
            fontsize=8.4, color=ACCENT)
    for i, v in enumerate(bpn):
        ax.text(i, v + 1.2, "%.2f" % v, ha="center", fontsize=8.4,
                color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, fontsize=7.8)
    ax.set_ylabel("nokta başına bit", color=INK)
    ax.set_ylim(0, 72)
    ax.set_title("Zaman damgası dizisinin delta-of-delta sıkıştırması",
                 fontsize=9.8, color=INK)
    ax.grid(True, axis="y", color=RULE, lw=0.6)
    _stil(ax)
    return _save(fig, _yol("zaman_dod"))


if __name__ == "__main__":
    for f in (aileler, bplus_lsm, lsm_seviye, bloom_bit, bloom_olcum,
              halka, tasinan, cogaltma, quorum, zaman_dod):
        print(f())
