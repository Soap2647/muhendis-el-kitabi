# -*- coding: utf-8 -*-
"""Bolum 25 - 'Bellek Hiyerarsisi' diyagramlari.

Olcum sekilleri engine/veri/b25_*.csv dosyalarini okur. Bu CSV'ler
bolumdeki C programlarinin (kovalama, satir, tlb, matris) ve
/proc/self/maps ciktisinin kaydidir. Diger sekiller bolumdeki sayisal
ornekleri (adres, sayfa tablosu indeksleri, malloc parcasi) cizer.
"""
import csv
import os
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,  # noqa
                      MUTED, RULE, FILL, EDGE)

OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b25_%s.png" % ad)


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. Hiyerarsi: kapasite arttikca gecikme artar ---------------------- #
def piramit(path):
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=7.6)
    katman = [
        ("Yazmaçlar", "onlarca bayt", "~0,3 ns", "genel bilgi"),
        ("L1 önbellek", "32 KB", "0,82 ns", "ölçüm"),
        ("L2 önbellek", "512 KB", "2,5 ns", "ölçüm"),
        ("L3 önbellek", "16 MB (paylaşımlı)", "~10 ns", "ölçüm, 1-4 MB"),
        ("DRAM", "15 GB (bu makine)", "110-130 ns", "ölçüm, 64+ MB"),
        ("SSD (NVMe)", "terabayt ölçeği", "~100 µs", "genel bilgi"),
        ("Ağ (aynı veri merkezi)", "sınırsız", "~0,5 ms", "genel bilgi"),
    ]
    fills = [FILL[4], FILL[0], FILL[1], FILL[2], FILL[3], FILL[0], FILL[4]]
    edges = [EDGE[4], EDGE[0], EDGE[1], EDGE[2], EDGE[3], EDGE[0], EDGE[4]]
    ax.text(11.2, 7.25, "gecikme (yaklaşık)", fontsize=9.5,
            color=MUTED, weight="bold")
    for i, (ad, kap, gec, kayn) in enumerate(katman):
        y = 6.35 - i * 0.92
        w = 3.4 + 0.85 * i
        x = 5.0 - w / 2
        _box(ax, x, y, w, 0.72, "%s  ·  %s" % (ad, kap),
             fills[i], edges[i], fs=9.2)
        ax.text(11.2, y + 0.46, gec, fontsize=10.5, color=INK,
                weight="bold", va="center")
        ax.text(11.2, y + 0.16, kayn, fontsize=8.2, color=MUTED,
                va="center")
    ax.text(0.2, 0.25, "Yukarı: küçük, hızlı, pahalı.  "
            "Aşağı: büyük, yavaş, ucuz.", fontsize=9, color=MUTED)
    _save(fig, path)


# 2. Adres bolunmesi: etiket | kume | ofset --------------------------- #
def adres_bolunme(path):
    adr = 0x7F3A12C4B5E8
    etiket = adr >> 12
    kume = (adr >> 6) & 63
    ofs = adr & 63
    fig, ax = _tuval(9.6, 3.6, xl=14, yl=5.2)
    ax.text(7.0, 4.85, "48 bitlik sanal adres, 32 KB, 8 yol, 64 bayt satır",
            ha="center", fontsize=10, color=INK, weight="bold")
    _box(ax, 0.6, 2.4, 7.4, 1.2, "etiket  (bit 47-12, 36 bit)",
         FILL[0], EDGE[0], fs=10)
    _box(ax, 8.1, 2.4, 3.0, 1.2, "küme  (bit 11-6, 6 bit)",
         FILL[1], EDGE[1], fs=9.5)
    _box(ax, 11.2, 2.4, 2.4, 1.2, "ofset (5-0)",
         FILL[2], EDGE[2], fs=9.5)
    ax.text(4.3, 1.9, "0x%x" % etiket, ha="center", fontsize=9.5,
            color=ACCENT, family="monospace")
    ax.text(9.6, 1.9, "%d" % kume, ha="center", fontsize=9.5,
            color=ACCENT, family="monospace")
    ax.text(12.4, 1.9, "%d" % ofs, ha="center", fontsize=9.5,
            color=ACCENT, family="monospace")
    ax.text(7.0, 1.1, "adres 0x%012X  →  küme %d'deki %d. bayt"
            % (adr, kume, ofs), ha="center", fontsize=9.5, color=INK)
    ax.text(7.0, 0.45, "ofset 2^6 = 64 bayt satırı seçer; küme 2^6 = 64 "
            "kümeden birini seçer;\n"
            "etiket geri kalan bitler, satırın kimliğidir.",
            ha="center", fontsize=8.8, color=MUTED, va="center")
    _save(fig, path)


# 3. Kume iliskili onbellek: bir kume, sekiz yol ----------------------- #
def kume_iliskili(path):
    rnd = random.Random(42)
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.4)
    ax.text(7.0, 7.1, "Küme ilişkili önbellek: 64 küme x 8 yol "
            "(örnek değerler)", ha="center", fontsize=10,
            color=INK, weight="bold")
    hedef = 5
    for k in range(8):
        y = 5.9 - k * 0.66
        ax.text(0.9, y + 0.22, "küme %2d" % k, fontsize=8.8,
                color=ACCENT if k == hedef else MUTED,
                weight="bold" if k == hedef else "normal",
                va="center", ha="left")
        for w in range(8):
            x = 2.6 + w * 0.92
            tag = "%03X" % rnd.randrange(0x1000)
            fill = FILL[3] if k == hedef else FILL[0]
            edge = EDGE[3] if k == hedef else RULE
            _box(ax, x, y, 0.84, 0.52, tag, fill, edge, fs=7.8,
                 tcol=INK)
    ax.text(2.6 + 3.5 * 0.92, 6.55, "yol 0 ... yol 7", ha="center",
            fontsize=8.8, color=MUTED)
    ax.text(10.2, 3.25, "adresin küme\nbitleri 5'i seçer:\netiketi 8 yolda\n"
            "arar. Bulursa isabet,\nbulamazsa kaçırma.",
            fontsize=8.5, color=INK, va="center")
    _save(fig, path)


# 4. Isaretci kovalama: basamak grafigi ------------------------------ #
def kovalama(path):
    veri = _oku("b25_kovalama.csv")
    x = [float(r["boyut_bayt"]) for r in veri]
    y = [float(r["ns_erisim"]) for r in veri]
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.semilogx(x, y, marker="o", ms=3.2, lw=1.6, color=ACCENT)
    for v, etiket in [(32 * 1024, "L1 32 KB"),
                      (512 * 1024, "L2 512 KB"),
                      (16 * 2 ** 20, "L3 16 MB (nominal)")]:
        ax.axvline(v, color=MUTED, ls="--", lw=0.9)
        ax.text(v * 1.07, 132, etiket, fontsize=8.5, color=MUTED,
                va="top")
    for xv, yv, metin in [(12e3, 2.6, "L1 ~0,82 ns"),
                          (1.2e5, 5.4, "L2 ~2,5 ns"),
                          (2.4e6, 15.5, "L3 ~10 ns"),
                          (1.5e7, 130, "")]:
        if metin:
            ax.text(xv, yv, metin, fontsize=9, color=INK)
    ax.text(1.4e8, 62, "DRAM ~120 ns", fontsize=9, color=INK,
            ha="center")
    ax.set_xlabel("dizi boyutu (bayt, log ölçek)")
    ax.set_ylabel("ns / erişim")
    ax.set_ylim(0, 140)
    ax.grid(True, which="major", color=RULE, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    _save(fig, path)


# 5. Adim taramasi: satir boyu ---------------------------------------- #
def satir_tarama(path):
    veri = _oku("b25_satir.csv")
    x = [float(r["adim_bayt"]) for r in veri]
    y = [float(r["ns_erisim"]) for r in veri]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.semilogx(x, y, marker="s", ms=4, lw=1.6, color=ACCENT_L,
                base=2)
    ax.axvline(64, color=ACCENT, ls="--", lw=1.0)
    ax.text(9, 3.7, "satır = 64 bayt\n(sysfs: coherency_line_size)",
            fontsize=8.8, color=ACCENT, va="top")
    ax.set_xlabel("adım (bayt, log2 ölçek)")
    ax.set_ylabel("ns / erişim")
    ax.set_ylim(0, 5.2)
    ax.grid(True, color=RULE, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    _save(fig, path)


# 6. Dort seviyeli sayfa tablosu yuruyusu ----------------------------- #
def sayfa_yuruyusu(path):
    fig, ax = _tuval(9.6, 4.0, xl=14, yl=6.2)
    ax.text(7.0, 5.85, "x86-64 dört seviyeli sayfa tablosu yürüyüşü",
            ha="center", fontsize=10, color=INK, weight="bold")
    # (kutu adi, ust metin, bit araligi, indeks)
    seviyeler = [
        ("CR3", "", "tablo tabanı", ""),
        ("PML4", "", "bit 47-39", "181"),
        ("PDPT", "", "bit 38-30", "358"),
        ("PD", "", "bit 29-21", "48"),
        ("PT", "", "bit 20-12", "310"),
        ("çerçeve", "", "bit 11-0 ofset", "672"),
    ]
    xs = [0.2, 2.4, 4.6, 6.8, 9.0, 11.2]
    for i, (ad, _ust, bit, idx) in enumerate(seviyeler):
        metin = ad if not idx else "%s\n[%s]" % (ad, idx)
        if ad == "çerçeve":
            metin = "çerçeve\n+ ofset %s" % idx
        _box(ax, xs[i], 2.6, 1.9, 1.5, metin,
             FILL[i % 5], EDGE[i % 5], fs=9.2)
        ax.text(xs[i] + 0.95, 2.25, bit, ha="center", fontsize=8.2,
                color=MUTED)
        if i < 5:
            _arrow(ax, xs[i] + 1.9, 3.35, xs[i + 1], 3.35,
                   col=ACCENT, lw=1.4)
    ax.text(7.0, 1.2, "Sanal adres 0x5AD9861362A0 (bu çalıştırmada heap). "
            "Her indeks 9 bit (512 girdi),\nher girdi 8 bayt: tablo 4 KB'a "
            "sığar. Ofset 672 = 0x2A0.",
            ha="center", fontsize=8.8, color=INK, va="center")
    ax.text(7.0, 0.25, "Her tablo bellekte bir sayfadır; CR3 onun fiziksel "
            "adresini tutar.", ha="center", fontsize=8.5, color=MUTED)
    _save(fig, path)


# 7. TLB: ayni onbellek yuku, farkli sayfa sayisi ---------------------- #
def tlb_cubuk(path):
    veri = _oku("b25_tlb.csv")
    etiket = {"sikli": "sıkı\n256 sayfa", "seyrek": "seyrek\n16384 sayfa",
              "buyuk": "seyrek +\n2 MB sayfa (32)"}
    x = list(range(len(veri)))
    y = [float(r["ns_erisim"]) for r in veri]
    renk = [FILL[1], FILL[3], FILL[2]]
    kenar = [EDGE[1], EDGE[3], EDGE[2]]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.bar(x, y, width=0.52, color=renk, edgecolor=kenar, lw=1.2)
    for i, v in enumerate(y):
        ax.text(i, v + 0.6, "%.1f ns" % v, ha="center", fontsize=10,
                color=INK, weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([etiket[r["duzen"]] for r in veri], fontsize=9.5)
    ax.set_ylabel("ns / erişim (işaretçi kovalama)")
    ax.set_ylim(0, 30)
    ax.grid(True, axis="y", color=RULE, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    _save(fig, path)


# 8. Surec adres uzayi haritasi -------------------------------------- #
def adres_haritasi(path):
    satirlar = _oku("b25_maps.csv")
    gruplar = []
    for r in satirlar:
        ad = r["ad"]
        if gruplar and gruplar[-1][0] == ad:
            gruplar[-1][2] = r["son"]
            gruplar[-1][3] += 1
        else:
            gruplar.append([ad, r["bas"], r["son"], 1])
    ad_metin = {"adr": "adr (kod, rodata, data, bss)",
                "[heap]": "[heap]  (malloc küçük bloklar)",
                "(anonim)": "anonim eşleme (1 MB malloc, mmap)",
                "libc.so.6": "libc.so.6 (paylaşımlı kütüphane)",
                "ld-linux-x86-64.so.2": "ld-linux (yükleyici)",
                "[stack]": "[stack]  (yığın)",
                "[vvar]": "[vvar]  (çekirdek verisi)",
                "[vdso]": "[vdso]  (çekirdek hızlı çağrılar)"}
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ust = gruplar  # kucukten buyuge: alt = dusuk adres
    h = 8.4 / len(ust)
    for i, (ad, bas, son, sayi) in enumerate(ust):
        y = 0.8 + i * h
        renk = FILL[i % 5]
        kenar = EDGE[i % 5]
        etiket = ad_metin.get(ad, ad)
        if ad == "(anonim)" and sayi > 1:
            etiket = "anonim (kütüphane veri/bss alanları)"
        _box(ax, 0.6, y + 0.04, 6.2, h - 0.08, etiket, renk, kenar, fs=8.6)
        ax.text(7.2, y + h / 2, "0x%s - 0x%s" % (bas, son),
                fontsize=8.6, color=INK, family="monospace",
                va="center")
        ax.text(7.2, y + h / 2 - 0.36, "%d bölge" % sayi, fontsize=7.8,
                color=MUTED, va="center")
    ax.text(0.6, 9.5, "Yüksek adresler (üstte) - düşük adresler (altta)",
            fontsize=9.5, color=MUTED)
    ax.text(0.6, 0.25, "Bölge yükseklikleri eşit çizildi; boyutlar "
            "orantılı değildir.", fontsize=8.5, color=MUTED)
    _save(fig, path)


# 9. malloc parca duzeni ---------------------------------------------- #
def malloc_parca(path):
    fig, ax = _tuval(9.6, 4.2, xl=14, yl=6.2)
    ax.text(7.0, 5.85, "glibc (x86-64): malloc(25) -> parça 48 bayt, "
            "kullanılabilir 40 bayt", ha="center", fontsize=10,
            color=INK, weight="bold")
    x0, olcek = 0.9, 0.16          # 1 bayt = 0.16 birim
    def X(b):
        return x0 + b * olcek
    _box(ax, X(0), 2.9, 8 * olcek, 1.0, "önceki\nboyut", FILL[4],
         EDGE[4], fs=7.5)
    _box(ax, X(8), 2.9, 8 * olcek, 1.0, "boyut\n|P", FILL[4],
         EDGE[4], fs=7.5)
    _box(ax, X(16), 2.9, 32 * olcek, 1.0, "kullanıcı verisi (32 bayt)",
         FILL[0], EDGE[0], fs=8.2)
    _box(ax, X(48), 2.9, 8 * olcek, 1.0, "B'nin\nönceki boyut", FILL[2],
         EDGE[2], fs=6.4)
    _box(ax, X(56), 2.9, 8 * olcek, 1.0, "B'nin\nboyut", FILL[4],
         EDGE[4], fs=6.4)
    ax.annotate("", xy=(X(16), 2.45), xytext=(X(56), 2.45),
                arrowprops=dict(arrowstyle="<->", color=ACCENT, lw=1.3))
    ax.text(X(36), 2.05, "kullanılabilir = 40 bayt (ofset 16 - 56)",
            ha="center", fontsize=8.8, color=ACCENT)
    ax.annotate("", xy=(X(0), 4.25), xytext=(X(48), 4.25),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.0))
    ax.text(X(24), 4.45, "parça A: 48 bayt (başlık 16 + veri 32 bayt)",
            ha="center", fontsize=8.6, color=MUTED)
    ax.text(X(0), 1.2, "malloc'un döndürdüğü işaretçi = parçanın başı + 16.",
            fontsize=8.8, color=INK)
    ax.text(X(0), 0.6, "Örtüşme: A'nın kullanılabilir alanının son 8 baytı, "
            "B'nin 'önceki boyut' alanıyla aynı yerdedir;\nbu yüzden "
            "kullanılabilir = parça - 8.",
            fontsize=8.5, color=MUTED)
    _save(fig, path)


# 10. Blok matris carpimi: olcum -------------------------------------- #
def matris_cubuk(path):
    veri = _oku("b25_matris.csv")
    x = list(range(len(veri)))
    y = [float(r["saniye"]) for r in veri]
    etiket = {"ijk": "ijk\n(sütun okuma)", "ikj": "ikj\n(satır okuma)",
              "blok": "blok 32x32\n(önbellek kutusu)"}
    renk = [FILL[3], FILL[0], FILL[1]]
    kenar = [EDGE[3], EDGE[0], EDGE[1]]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.barh(x, y, height=0.5, color=renk, edgecolor=kenar, lw=1.2)
    for i, v in enumerate(y):
        ax.text(v + 0.12, i, "%.2f s" % v, va="center", fontsize=10,
                color=INK, weight="bold")
    ax.set_yticks(x)
    ax.set_yticklabels([etiket[r["varyant"]] for r in veri], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("süre (saniye), N = 1024, medyan (3 deneme)")
    ax.set_xlim(0, 8)
    ax.grid(True, axis="x", color=RULE, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    _save(fig, path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    piramit(_yol("piramit"))
    adres_bolunme(_yol("adres_bolunme"))
    kume_iliskili(_yol("kume_iliskili"))
    kovalama(_yol("kovalama_basamak"))
    satir_tarama(_yol("satir_tarama"))
    sayfa_yuruyusu(_yol("sayfa_yuruyusu"))
    tlb_cubuk(_yol("tlb"))
    adres_haritasi(_yol("adres_haritasi"))
    malloc_parca(_yol("malloc_parca"))
    matris_cubuk(_yol("matris"))
    print("tamam: 10 sekil")
