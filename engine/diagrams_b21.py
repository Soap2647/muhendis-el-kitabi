# -*- coding: utf-8 -*-
"""Bolum 21 - 'SOLID' diyagramlari.

Olcum sekilleri (import grafi, etki sayaci) engine/veri altindaki
b21_*.csv dosyalarini okur; diger sekiller bolumdeki ornek kodlardan
elle cizilir.
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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b21_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. SRP: once tek sinif, sonra orkestrator + tek isli moduller -------- #
def srp_sorumluluk():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.6)
    ax.text(2.4, 6.3, "Önce: tek sınıf, 5 sorumluluk", ha="center",
            fontsize=9.6, weight="bold", color=ACCENT)
    _box(ax, 0.3, 0.3, 4.6, 5.6, "", FILL[3], ACCENT, fs=9)
    isler = ["1. veri: sensörleri oku", "2. istatistik: ortalama",
             "3. biçim: satır metni", "4. dosya: open / write",
             "5. alarm: eşik kontrolü"]
    for i, t in enumerate(isler):
        _box(ax, 0.6, 4.6 - i * 0.98, 4.0, 0.72, t, FILL[0], EDGE[0],
             fs=9)
    ax.text(10.2, 6.3, "Sonra: orkestratör + tek işli modüller",
            ha="center", fontsize=9.6, weight="bold", color=EDGE[1])
    _box(ax, 5.9, 4.5, 3.4, 1.0, "RaporYoneticisi\n(sadece sırayla çağırır)",
         FILL[1], EDGE[1], fs=8.8, bold=True)
    alt = [("istatistik.py", 5.7, 2.1), ("bicim.py", 8.0, 2.1),
           ("alarm.py", 10.3, 2.1)]
    for ad, x, y in alt:
        _box(ax, x, y, 2.1, 0.85, ad, FILL[2], EDGE[2], fs=9)
        _arrow(ax, 7.6, 4.5, x + 1.05, y + 0.85, col=ACCENT_L, rad=0.0)
    _box(ax, 5.9, 0.4, 6.4, 0.9,
         "sensörler (olc)  ·  dosya yazımı orkestratörde", FILL[4],
         EDGE[4], fs=8.8)
    ax.text(7.1, 0.0, "her modül tek bir değişim nedenine sahip",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("srp_sorumluluk"))


# 2. OCP: if zinciri vs kayit tablosu ---------------------------------- #
def ocp_kayit():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.6)
    ax.text(3.4, 6.3, "Önce: her yeni tür bu zinciri değiştirir",
            ha="center", fontsize=10, weight="bold", color=ACCENT)
    _box(ax, 0.3, 0.6, 6.2, 5.0, "", FILL[3], ACCENT, fs=9)
    satirlar = ["if tur == \"termistor\":", "    ...kalibre et",
                "elif tur == \"gerilim\":", "    ...kalibre et",
                "elif tur == \"basinc\":   <- eklendi", "    ...kalibre et",
                "else: raise ValueError"]
    for i, t in enumerate(satirlar):
        ax.text(0.7, 5.1 - i * 0.6, t, fontsize=9.2, family="monospace",
                color=ACCENT if "eklendi" in t else INK, va="center")
    ax.text(10.6, 6.3, "Sonra: kayıt tablosu", ha="center", fontsize=10,
            weight="bold", color=EDGE[1])
    _box(ax, 8.2, 4.4, 5.2, 0.9, "kayit.SENSORLER (sözlük)", FILL[1],
         EDGE[1], fs=9.5, bold=True)
    girdiler = [("\"termistor\" → TermistorSensor", 3.0),
                ("\"gerilim\" → GerilimSensor", 2.0),
                ("\"basinc\" → BasincSensor  (yeni dosya)", 1.0)]
    ax.plot([7.7, 7.7], [4.85, 1.15], color=ACCENT_L, lw=1.6)
    ax.plot([8.2, 7.7], [4.85, 4.85], color=ACCENT_L, lw=1.6)
    for t, y in girdiler:
        _box(ax, 8.2, y - 0.2, 5.2, 0.7, t, FILL[0], EDGE[0], fs=8.8)
        _arrow(ax, 7.7, y + 0.15, 8.2, y + 0.15, col=ACCENT_L, rad=0.0)
    ax.text(10.8, 0.25, "çekirdek kod değişmez; yeni tür yeni dosyadır",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("ocp_kayit"))


# 3. LSP: Kare, Dikdortgen ve sozlesme kurallari ------------------------ #
def lsp_sozlesme():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.0)
    _box(ax, 0.4, 4.9, 3.6, 1.0, "Dikdörtgen\nen, boy", FILL[0], EDGE[0],
         fs=10, bold=True)
    _box(ax, 0.4, 2.3, 3.6, 1.0, "Kare\nkenar", FILL[2], EDGE[2], fs=10,
         bold=True)
    _arrow(ax, 2.2, 3.3, 2.2, 5.0, col=ACCENT_L, style="-|>", rad=0.0)
    ax.text(2.35, 4.0, "miras", fontsize=8.6, color=MUTED)
    _box(ax, 0.4, 0.4, 3.6, 1.4,
         "en_ayarla(4) sonrası\nbeklenen 12, gerçek 16", FILL[3], ACCENT,
         fs=9, tcol=ACCENT)
    _arrow(ax, 2.2, 1.8, 2.2, 2.3, col=ACCENT, rad=0.0)
    ax.text(4.5, 6.6, "LSP sözleşme kuralları (Liskov & Wing)", fontsize=10,
            weight="bold", color=INK)
    kurallar = [("Önkoşul", "alt sınıf, üst sınıftan daha güçlü\nönkoşul koyamaz"),
                ("Sonkoşul", "alt sınıf, üst sınıfın garantisini\nzayıflatamaz"),
                ("Değişmez", "üst sınıfın değişmezleri\nkorunmalıdır"),
                ("Tarihçe", "durum değişimi üst sınıfın\nizin verdiği ölçüde olmalı")]
    for i, (ad, aciklama) in enumerate(kurallar):
        y = 5.4 - i * 1.25
        _box(ax, 4.6, y - 0.1, 2.2, 0.85, ad, FILL[1], EDGE[1], fs=9.5,
             bold=True)
        ax.text(7.1, y + 0.32, aciklama, fontsize=8.8, color=INK,
                va="center")
    return _save(fig, _yol("lsp_sozlesme"))


# 4. ISP: sisik arayuz vs kucuk arayuzler ------------------------------- #
def isp_arayuz():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.6)
    ax.text(3.0, 6.2, "Şişkin: Cihaz (3 metot)", ha="center", fontsize=10,
            weight="bold", color=ACCENT)
    _box(ax, 0.3, 3.8, 5.4, 1.9,
         "oku()\nkalibre(k)\nfirmware_guncelle(dosya)", FILL[3], ACCENT,
         fs=9.5, tcol=INK)
    _box(ax, 0.3, 0.6, 5.4, 2.2,
         "SaltOkunurTermistor\nkalibre  → NotImplementedError\n"
         "firmware → NotImplementedError", FILL[0], EDGE[0], fs=9, tcol=ACCENT)
    _arrow(ax, 3.0, 2.8, 3.0, 3.8, col=ACCENT, rad=0.0)
    ax.text(3.2, 3.2, "3 metodu da uygulamak zorunda", fontsize=8.6, color=ACCENT)
    ax.text(10.0, 6.2, "Küçük: Okunabilir / Kalibre", ha="center",
            fontsize=10, weight="bold", color=EDGE[1])
    _box(ax, 7.6, 4.0, 2.4, 1.2, "Okunabilir\noku()", FILL[1], EDGE[1],
         fs=9.5)
    _box(ax, 10.4, 4.0, 2.4, 1.2, "Kalibre\nkalibre(k)", FILL[1], EDGE[1],
         fs=9.5)
    _box(ax, 7.6, 1.3, 2.4, 1.2, "olc_ve_kaydet\n(kaynak)", FILL[2],
         EDGE[2], fs=9.2)
    _arrow(ax, 8.8, 2.5, 8.8, 4.0, col=EDGE[2], rad=0.0)
    _box(ax, 10.4, 1.3, 2.4, 1.2, "SaltOkunur\nTermistor", FILL[0],
         EDGE[0], fs=9.2)
    _arrow(ax, 11.6, 2.5, 8.9, 4.0, col=MUTED, style="-|>", rad=0.25)
    ax.text(11.8, 3.4, "yapısal\nuyum", fontsize=8.2, color=MUTED,
            ha="center")
    return _save(fig, _yol("isp_arayuz"))


# 5. DIP: bagimlilik yonunun tersine donmesi --------------------------- #
def dip_yon():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.0)
    ax.text(3.2, 6.6, "Önce: üst → alt (somut)", ha="center", fontsize=10,
            weight="bold", color=ACCENT)
    _box(ax, 1.0, 4.7, 4.4, 1.1, "TelemetriHatti", FILL[3], ACCENT,
         fs=10, bold=True)
    _box(ax, 1.0, 1.4, 4.4, 1.1, "TermistorSurucu (somut)", FILL[0],
         EDGE[0], fs=10)
    _arrow(ax, 3.2, 4.7, 3.2, 2.5, col=ACCENT, rad=0.0)
    ax.text(3.4, 3.5, "doğrudan bağımlılık", fontsize=8.6, color=ACCENT)
    ax.text(10.2, 6.6, "Sonra: üst ve alt, soyutlamaya bağlı", ha="center",
            fontsize=10, weight="bold", color=EDGE[1])
    _box(ax, 8.0, 4.7, 4.4, 1.1, "TelemetriHatti", FILL[1], EDGE[1],
         fs=10, bold=True)
    _box(ax, 8.0, 2.5, 4.4, 1.0, "Okunabilir (soyutlama)", FILL[2],
         EDGE[2], fs=10, bold=True)
    _box(ax, 8.0, 0.4, 2.0, 1.0, "TermistorSurucu", FILL[0], EDGE[0],
         fs=8.8)
    _box(ax, 10.4, 0.4, 2.0, 1.0, "SahteSensor", FILL[4], EDGE[4],
         fs=8.8)
    _arrow(ax, 10.2, 4.7, 10.2, 3.5, col=EDGE[1], rad=0.0)
    _arrow(ax, 9.0, 1.4, 9.2, 2.5, col=EDGE[2], style="-|>", rad=0.0)
    _arrow(ax, 11.4, 1.4, 11.2, 2.5, col=EDGE[2], style="-|>", rad=0.0)
    ax.text(13.25, 3.0, "ok yönü\ntersine", fontsize=8.6, color=MUTED,
            ha="center")
    return _save(fig, _yol("dip_yon"))


# 6. Import grafi (olcum: b21_kenarlar.csv + b21_baglilik.csv) ---------- #
def import_grafigi():
    kenarlar = _oku("b21_kenarlar.csv")
    metrik = _oku("b21_baglilik.csv")
    fig, ax = _tuval(9.6, 5.0, xl=14.4, yl=7.0)
    konum = {
        "once": {"app": (2.6, 5.6), "rapor": (2.6, 3.4),
                 "olcum": (2.6, 1.2)},
        "sonra": {"app": (9.7, 6.0), "sensorler": (6.4, 3.9),
                  "rapor": (9.7, 3.9), "kayit": (6.4, 6.0),
                  "sozlesme": (6.4, 1.6), "alarm": (9.7, 1.6),
                  "bicim": (12.9, 1.6), "istatistik": (12.9, 3.9)},
    }
    ax.text(2.6, 6.6, "Önce (3 modül)", ha="center", fontsize=10.5,
            weight="bold", color=ACCENT)
    ax.text(10.0, 6.8, "Sonra (8 modül)", ha="center", fontsize=10.5,
            weight="bold", color=EDGE[1])
    hw, hh = 1.3, 0.45
    for surum, konumlar in konum.items():
        for k in kenarlar:
            if k["surum"] != surum:
                continue
            x1, y1 = konumlar[k["kaynak"]]
            x2, y2 = konumlar[k["hedef"]]
            dx, dy = x2 - x1, y2 - y1
            kk = min(hw / abs(dx) if dx else 9e9,
                     hh / abs(dy) if dy else 9e9)
            _arrow(ax, x1 + kk * dx, y1 + kk * dy,
                   x2 - kk * dx, y2 - kk * dy,
                   col=MUTED, lw=1.1, rad=0.0)
        for m in metrik:
            if m["surum"] != surum:
                continue
            x, y = konumlar[m["modul"]]
            etiket = "%s\nCa=%s Ce=%s I=%s" % (
                m["modul"], m["ca"], m["ce"], m["i"].replace(".", ","))
            renk = ACCENT if surum == "once" else EDGE[1]
            _box(ax, x - 1.3, y - 0.45, 2.6, 0.9, etiket,
                 FILL[3] if surum == "once" else FILL[1], renk, fs=7.8,
                 tcol=INK)
    ax.text(7.2, 0.1, "Ca: bu modüle bağlı modül sayısı (gelen ok)   "
            "Ce: bu modülün bağlı olduğu modül sayısı (giden ok)",
            ha="center", fontsize=7.6, color=MUTED)
    return _save(fig, _yol("import_grafigi"))


# 7. Etki sayaci (b21_etki.csv) ---------------------------------------- #
def etki_olcum():
    veri = _oku("b21_etki.csv")
    etiket = {"once_A1": "A: önce\nyalnız üretici",
              "once_A2": "A: önce\ntam değişiklik",
              "sonra_A": "A: sonra\nalan eklendi",
              "once_B": "B: önce\nyeni tür",
              "sonra_B": "B: sonra\nyeni tür"}
    satirlar = [r for r in veri if r["senaryo"] in etiket]
    x = list(range(len(satirlar)))
    dosya = [int(r["degisen_dosya"]) for r in satirlar]
    kirilan = [int(r["kirilan_test"]) for r in satirlar]
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    w = 0.38
    b1 = ax.bar([i - w / 2 for i in x], dosya, w, color=EDGE[0],
                label="değişen dosya")
    b2 = ax.bar([i + w / 2 for i in x], kirilan, w, color=ACCENT,
                label="kırılan test (5 testten)")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08,
                    "%d" % b.get_height(), ha="center", fontsize=9,
                    color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([etiket[r["senaryo"]] for r in satirlar],
                       fontsize=8.4)
    ax.set_ylabel("adet")
    ax.set_ylim(0, 5.2)
    ax.grid(True, axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8.8, loc="upper right")
    fig.tight_layout()
    fig.savefig(_yol("etki_olcum"), dpi=200, facecolor="white")
    plt.close(fig)
    return _yol("etki_olcum")


# 8. C: fonksiyon isaretci tablosu (file_operations, null/zero) -------- #
def fops_tablo():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=7.6)
    ax.text(7.0, 7.3, "struct file_operations alanları ve iki sürücünün "
            "doldurduğu değerler", ha="center", fontsize=10.2,
            weight="bold", color=INK)
    basliklar = [("alan (struct)", 0.4, 3.4), ("null_fops", 4.0, 4.9),
                 ("zero_fops", 9.2, 4.4)]
    for ad, x, w in basliklar:
        _box(ax, x, 6.0, w, 0.8, ad, FILL[1], EDGE[1], fs=9.8, bold=True)
    satirlar = [
        ("llseek", "null_lseek", "zero_lseek → null_lseek (#define)"),
        ("read", "read_null", "read_zero"),
        ("write", "write_null", "write_zero → write_null (#define)"),
        ("read_iter", "read_iter_null", "read_iter_zero"),
        ("write_iter", "write_iter_null", "write_iter_zero → write_iter_null"),
        ("mmap", "NULL", "mmap_zero"),
        ("splice_write", "splice_write_null", "NULL"),
        ("uring_cmd", "uring_cmd_null", "NULL"),
    ]
    for i, (alan, n, z) in enumerate(satirlar):
        y = 5.0 - i * 0.6
        _box(ax, 0.4, y, 3.4, 0.5, alan, FILL[0], EDGE[0], fs=8.8)
        renk_n = MUTED if n == "NULL" else INK
        renk_z = MUTED if z == "NULL" else INK
        _box(ax, 4.0, y, 4.9, 0.5, n, FILL[4] if n == "NULL" else "white",
             RULE, fs=8.6, tcol=renk_n)
        _box(ax, 9.2, y, 4.4, 0.5, z, FILL[4] if z == "NULL" else "white",
             RULE, fs=8.1, tcol=renk_z)
    ax.text(7.0, 0.2, "NULL: sürücü bu işlemi desteklemez; çekirdek NULL "
            "kontrolü yapar, ya da hata döndürür", ha="center",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("fops_tablo"))


if __name__ == "__main__":
    for f in (srp_sorumluluk, ocp_kayit, lsp_sozlesme, isp_arayuz,
              dip_yon, import_grafigi, etki_olcum, fops_tablo):
        print(f())
