# -*- coding: utf-8 -*-
"""Bolum 20 - 'OOP Temelleri' diyagramlari.

Olcum grafikleri (sanal cagri, __dict__/__slots__) engine/veri altindaki
CSV dosyalarindan okunur; diger sekiller bolumdeki ornek degerlerden cizilir.
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

KOK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KOK, "..", "gorseller")
VERI = os.path.join(KOK, "veri")


def _yol(ad):
    return os.path.join(OUT, "b20_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _hucre(ax, x, y, w, h, metin, fill="white", edge=RULE, fs=9.5,
           bold=False, tcol=INK):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                           lw=1.0, zorder=2))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=fs, color=tcol, zorder=3,
            weight="bold" if bold else "normal")


# 1. Elle vtable (C) ve derleyici vtable'i (C++) --------------------- #
def elle_vtable():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.4)
    ax.text(3.5, 7.0, "C: elle kurulmuş tablo", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ax.text(10.5, 7.0, "C++: derleyicinin kurduğu vtable", ha="center",
            fontsize=10.5, weight="bold", color=INK)
    _box(ax, 0.4, 4.9, 3.0, 1.2, "Daire nesnesi\nvt | r", FILL[0],
         EDGE[0], fs=9.5)
    _box(ax, 0.4, 2.6, 3.0, 1.4, "SekilVT tablosu\nalan | yazdir",
         FILL[2], EDGE[2], fs=9.5)
    _box(ax, 4.4, 4.8, 2.7, 0.8, "daire_alan()", FILL[1], EDGE[1], fs=9)
    _box(ax, 4.4, 2.9, 2.7, 0.8, "daire_yazdir()", FILL[1], EDGE[1], fs=9)
    _arrow(ax, 1.9, 4.9, 1.9, 4.0, col=ACCENT)
    _arrow(ax, 3.4, 3.3, 4.4, 5.2, col=ACCENT_L, rad=-0.1)
    _arrow(ax, 3.4, 2.9, 4.4, 3.3, col=ACCENT_L, rad=0.1)
    ax.text(0.4, 1.7, "vt->alan(s): tablodan adres okunur,\n"
            "sonra dolaylı çağrı yapılır.", fontsize=8.6, color=MUTED,
            va="center")
    _box(ax, 7.9, 4.9, 3.0, 1.2, "Daire nesnesi\nvptr | r", FILL[0],
         EDGE[0], fs=9.5)
    _hucre(ax, 7.9, 2.4, 3.0, 2.0, "", fill=FILL[2], edge=EDGE[2])
    for k, metin in enumerate(["yazdir", "alan",
                               "~Daire (silme)", "~Daire (tam)"]):
        _hucre(ax, 8.0, 2.5 + k * 0.45, 2.8, 0.4, metin, fill="white",
               edge=RULE, fs=8.6, bold=(metin in ("alan", "yazdir")))
    _arrow(ax, 9.4, 4.9, 9.4, 4.45, col=ACCENT)
    ax.text(7.9, 1.7, "vptr, tablodaki 'alan' girdisine işaret eder;\n"
            "ilk iki girdi yıkıcılar için ayrılmıştır (Itanium ABI).",
            fontsize=8.6, color=MUTED, va="center")
    ax.plot([6.9, 6.9], [0.6, 6.7], color=RULE, lw=1.0)
    return _save(fig, _yol("elle_vtable"))


# 2. Nesne bellek duzeni: sizeof ve dolgu ---------------------------- #
def nesne_duzeni():
    fig, ax = _tuval(9.6, 3.6, xl=14, yl=5.2)
    satirlar = [
        ("Sekil (soyut)", [("vptr", 8, FILL[0])], "sizeof = 8"),
        ("Daire", [("vptr", 8, FILL[0]), ("r (double)", 8, FILL[1])],
         "sizeof = 16"),
        ("Taban", [("vptr", 8, FILL[0]), ("kimlik", 4, FILL[1]),
                   ("dolgu", 4, "white")], "sizeof = 16"),
        ("Tureyen", [("vptr", 8, FILL[0]), ("kimlik", 4, FILL[1]),
                     ("ek", 4, FILL[2])], "ek: kuyruk dolgusunda"),
    ]
    for i, (ad, parcalar, not_) in enumerate(satirlar):
        y = 3.6 - i * 0.9
        ax.text(0.2, y + 0.3, ad, fontsize=9.5, weight="bold", va="center",
                color=INK)
        x = 2.6
        for metin, bayt, fill in parcalar:
            w = bayt * 0.5
            _hucre(ax, x, y, w, 0.6, metin, fill=fill, edge=EDGE[0],
                   fs=8.4, tcol=INK if fill != "white" else MUTED)
            x += w
        ax.text(x + 0.2, y + 0.3, not_, fontsize=8.6, color=ACCENT,
                va="center")
    ax.text(2.6, 0.25, "0. bayt", fontsize=8, color=MUTED, ha="left")
    ax.text(2.6 + 8 * 0.5, 0.25, "8. bayt", fontsize=8, color=MUTED,
            ha="center")
    ax.text(2.6 + 16 * 0.5, 0.25, "16. bayt", fontsize=8, color=MUTED,
            ha="center")
    return _save(fig, _yol("nesne_duzeni"))


# 3. Elmas kalitim ve MRO ------------------------------------------- #
def elmas_mro():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.0)
    _box(ax, 5.0, 5.4, 2.6, 0.9, "A\nhazirla()", FILL[0], EDGE[0],
         fs=10, bold=True)
    _box(ax, 1.2, 3.2, 2.6, 0.9, "B\nhazirla()", FILL[1], EDGE[1], fs=10)
    _box(ax, 8.8, 3.2, 2.6, 0.9, "C\nhazirla()", FILL[2], EDGE[2], fs=10)
    _box(ax, 5.0, 1.0, 2.6, 0.9, "D\nhazirla()", FILL[3], EDGE[3],
         fs=10, bold=True)
    # oklar kalitim yonunde: cocuktan ebeveyne
    _arrow(ax, 2.5, 4.1, 5.0, 5.6, col=ACCENT_L, rad=0.0)
    _arrow(ax, 10.1, 4.1, 7.6, 5.6, col=ACCENT_L, rad=0.0)
    _arrow(ax, 5.0, 1.9, 3.0, 3.2, col=ACCENT, rad=0.0)
    _arrow(ax, 7.6, 1.9, 9.5, 3.2, col=ACCENT, rad=0.0)
    ax.text(7.0, 0.25, "D.__mro__ = [D, B, C, A, object]",
            ha="center", fontsize=10.5, color=ACCENT, weight="bold")
    ax.text(0.3, 6.4, "Kalıtım (is-a)\nokları", fontsize=8.8,
            color=MUTED, va="center")
    ax.text(10.6, 1.2, "super(), MRO'daki\nbir sonraki sınıfı\nçağırır",
            fontsize=8.4, color=MUTED, va="center")
    return _save(fig, _yol("elmas_mro"))


# 4. Sig ve derin kopya: bellek resmi -------------------------------- #
def sig_derin():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=6.5)
    ax.text(3.4, 6.1, "Sığ kopya (varsayılan)", ha="center", fontsize=10.5,
            weight="bold")
    ax.text(10.6, 6.1, "Derin kopya (Rule of 5)", ha="center",
            fontsize=10.5, weight="bold")
    _box(ax, 0.4, 4.3, 2.0, 0.9, "a: veri_", FILL[0], EDGE[0], fs=9.5)
    _box(ax, 0.4, 2.6, 2.0, 0.9, "b: veri_", FILL[0], EDGE[0], fs=9.5)
    _box(ax, 4.4, 3.3, 2.3, 1.2, "\"MertOS\\0\"\n(tek bellek)", FILL[3],
         EDGE[3], fs=9.2)
    _arrow(ax, 2.4, 4.75, 4.4, 4.0, col=ACCENT, rad=0.1)
    _arrow(ax, 2.4, 3.05, 4.4, 3.8, col=ACCENT, rad=-0.1)
    ax.text(3.4, 2.4, "yıkıcı a: free\nyıkıcı b: free  (ÇİFT!)",
            fontsize=8.8, color=ACCENT, ha="center", va="center")
    _box(ax, 7.8, 4.3, 2.0, 0.9, "a: veri_", FILL[1], EDGE[1], fs=9.5)
    _box(ax, 7.8, 2.6, 2.0, 0.9, "b: veri_", FILL[1], EDGE[1], fs=9.5)
    _box(ax, 11.3, 4.3, 2.3, 0.9, "\"MertOS\\0\"", FILL[1], EDGE[1],
         fs=9.2)
    _box(ax, 11.3, 2.6, 2.3, 0.9, "\"MertOS\\0\"", FILL[1], EDGE[1],
         fs=9.2)
    _arrow(ax, 9.8, 4.75, 11.3, 4.75, col=ACCENT_L)
    _arrow(ax, 9.8, 3.05, 11.3, 3.05, col=ACCENT_L)
    ax.text(10.6, 1.8, "her yıkıcı kendi belleğini serbest bırakır",
            fontsize=8.8, color=ACCENT_L, ha="center")
    return _save(fig, _yol("sig_derin"))


# 5. Nesne dilimleme (slicing) ------------------------------------- #
def dilimleme():
    fig, ax = _tuval(9.6, 3.8, xl=14, yl=5.6)
    _box(ax, 0.4, 2.4, 4.4, 2.2, "", FILL[0], EDGE[0])
    ax.text(2.6, 4.25, "Tureyen nesnesi (16 bayt)", ha="center",
            fontsize=9.5, weight="bold")
    _hucre(ax, 0.8, 2.7, 1.3, 0.9, "vptr", fill=FILL[0], fs=9)
    _hucre(ax, 2.1, 2.7, 1.0, 0.9, "kimlik", fill=FILL[1], fs=9)
    _hucre(ax, 3.1, 2.7, 1.5, 0.9, "ek = 99", fill=FILL[2], fs=9)
    _box(ax, 5.2, 2.4, 3.4, 2.2, "", FILL[1], EDGE[1])
    ax.text(6.9, 4.25, "Taban kopyası (değerle)", ha="center", fontsize=9.5,
            weight="bold")
    _hucre(ax, 5.6, 2.7, 1.3, 0.9, "vptr (Taban)", fill=FILL[0], fs=8)
    _hucre(ax, 6.9, 2.7, 1.4, 0.9, "kimlik = 7", fill=FILL[1], fs=9)
    _arrow(ax, 4.9, 3.5, 5.2, 3.5, col=ACCENT, lw=2.0)
    ax.text(5.05, 3.95, "dilim", fontsize=8.6, color=ACCENT, ha="center")
    _box(ax, 9.4, 2.4, 4.2, 2.2, "", "white", MUTED)
    ax.text(11.5, 4.25, "Kayıp", ha="center", fontsize=9.5, color=ACCENT,
            weight="bold")
    ax.text(11.5, 3.2, "ek üyesi ve\nTureyen::ad() kayboldu", ha="center",
            va="center", fontsize=9, color=INK)
    ax.text(7.0, 0.9, "Değerle alan Taban içinde tür ve ek bilgisi "
            "kaybolur.\nReferansla (const Taban&) alınca sanal çağrı "
            "Tureyen::ad()'a gider.",
            ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("dilimleme"))


# 6. Kalitim mi bilesim mi: kirilgan taban sinif -------------------- #
def bilesim_kalitim():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.4)
    ax.text(3.5, 7.0, "Kalıtım: set'ten türetilmiş", ha="center",
            fontsize=10.5, weight="bold")
    ax.text(10.5, 7.0, "Bileşim: içinde set var", ha="center",
            fontsize=10.5, weight="bold")
    _box(ax, 1.4, 5.0, 4.2, 1.0, "SayanKume(set)\nadd: sayaç++, super",
         FILL[0], EDGE[0], fs=9.2)
    _box(ax, 1.4, 2.9, 4.2, 1.0, "update([2,3,4])\nadd çağrılmaz (C içi)",
         FILL[3], EDGE[3], fs=9.2)
    ax.text(3.5, 1.9, "beklenen 4, gerçek 1", ha="center", fontsize=9.5,
            color=ACCENT, weight="bold")
    _box(ax, 8.0, 5.0, 4.8, 1.0, "SayanBileşik\nekle: sayaç++, _k.add",
         FILL[1], EDGE[1], fs=9.2)
    _box(ax, 8.0, 2.9, 4.8, 1.0, "ekle_toplu(xs)\n-> her eleman ekle()",
         FILL[2], EDGE[2], fs=9.2)
    _arrow(ax, 12.6, 3.9, 12.6, 5.0, col=ACCENT_L)
    ax.text(10.6, 1.9, "tek giriş noktası: beklenen 4", ha="center",
            fontsize=9.5, color=ACCENT_L, weight="bold")
    ax.plot([7.0, 7.0], [0.9, 6.6], color=RULE, lw=1.0)
    return _save(fig, _yol("bilesim_kalitim"))


# 7. RAII: edinim ileri, birakma geri (yigin) ----------------------- #
def raii_yigin():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=6.6)
    ax.text(3.2, 6.2, "Kurulum (edinim)", ha="center", fontsize=10,
            weight="bold")
    ax.text(10.6, 6.2, "Yıkım (birakma, ters sıra)", ha="center",
            fontsize=10, weight="bold")
    adimlar = ["kilit-A al", "dosya aç", "kilit-B al", "iş (istisna!)"]
    for i, a in enumerate(adimlar):
        y = 4.8 - i * 1.0
        _box(ax, 1.4, y, 3.6, 0.7, a, FILL[i % 4], EDGE[i % 4], fs=9.2)
        if i < 3:
            _arrow(ax, 3.2, y, 3.2, y - 0.3, col=MUTED)
    cikis = ["kilit-B bırak", "dosya kapat", "kilit-A bırak"]
    for i, a in enumerate(cikis):
        y = 4.8 - i * 1.0
        _box(ax, 8.6, y, 3.8, 0.7, a, FILL[(i + 1) % 4], EDGE[(i + 1) % 4],
             fs=9.2)
        if i < 2:
            _arrow(ax, 10.5, y, 10.5, y - 0.3, col=ACCENT)
    _arrow(ax, 5.2, 3.0, 8.6, 3.0, col=ACCENT, lw=1.6)
    ax.text(6.9, 3.35, "istisna: yığın\nters yönde açılır", ha="center",
            fontsize=8.6, color=ACCENT)
    ax.text(7.0, 0.5, "Her birakma, o an açık olan en son edinilen "
            "kaynaktır (LIFO).", ha="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("raii_yigin"))


# 8. Olcum: __dict__ vs __slots__ (CSV) ------------------------------ #
def bellek_olcum():
    xs, dict_b, slot_b = [], [], []
    with open(os.path.join(VERI, "b20_bellek_olcum.csv"),
              encoding="utf-8") as f:
        for satir in csv.DictReader(f):
            xs.append(int(satir["n"]))
            dict_b.append(float(satir["dict_bayt"]))
            slot_b.append(float(satir["slots_bayt"]))
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.semilogx(xs, dict_b, marker="o", color=ACCENT, lw=1.8,
                label="dict (__dict__, varsayılan)")
    ax.semilogx(xs, slot_b, marker="s", color=ACCENT_L, lw=1.8,
                label="slots (__slots__)")
    ax.set_xlabel("nesne sayısı n (log)")
    ax.set_ylabel("bayt / nesne (tracemalloc)")
    ax.set_ylim(0, 140)
    ax.grid(True, color=RULE, lw=0.6)
    ax.legend(frameon=False, loc="center right")
    ax.set_title("Python: nesne başına bellek (CPython 3.12.10)", color=INK)
    for x, y in ((xs[-1], dict_b[-1]), (xs[-1], slot_b[-1])):
        ax.annotate("%.0f" % y, (x, y), textcoords="offset points",
                    xytext=(6, 4), fontsize=9, color=INK)
    fig.tight_layout()
    return _save(fig, _yol("bellek_olcum"))


# 9. Olcum: sanal cagri maliyeti (CSV, log-log) ---------------------- #
def sanal_olcum():
    seri = {}
    with open(os.path.join(VERI, "b20_sanal_olcum.csv"),
              encoding="utf-8") as f:
        for satir in csv.DictReader(f):
            anahtar = (satir["yontem"], satir["dagitim"])
            seri.setdefault(anahtar, []).append(
                (int(satir["n"]), float(satir["ms"])))
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    stiller = {
        ("etiketli", "tek_tur"): (ACCENT_L, "o", "-",
                                  "etiketli (dal), tek tür"),
        ("sanal", "tek_tur"): (ACCENT, "s", "-", "sanal, tek tür"),
        ("etiketli", "karisik"): (ACCENT_L, "o", "--",
                                  "etiketli (dal), karışık"),
        ("sanal", "karisik"): (ACCENT, "s", "--", "sanal, karışık"),
    }
    for anahtar, (renk, mark, ls, etiket) in stiller.items():
        veri = sorted(seri[anahtar])
        ax.loglog([v[0] for v in veri], [v[1] for v in veri], color=renk,
                  marker=mark, ls=ls, lw=1.8, label=etiket)
    ax.set_xlabel("dizi uzunluğu n (log)")
    ax.set_ylabel("bir tur süresi, ms (log)")
    ax.grid(True, which="both", color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("Sanal çağrı maliyeti: C++ -O2, medyan 5 çalıştırma",
                 color=INK)
    fig.tight_layout()
    return _save(fig, _yol("sanal_olcum"))


# 10. Kural secimi: Rule of 0 / 3 / 5 ------------------------------- #
def kural_secimi():
    fig, ax = _tuval(9.6, 4.8, xl=14, yl=7.4)
    _box(ax, 4.2, 5.9, 5.6, 0.9, "Sınıf bir kaynak sahibi mi?\n"
         "(ham işaretçi, dosya, kilit...)", FILL[0], EDGE[0], fs=9.2,
         bold=True)
    _box(ax, 0.4, 3.3, 4.2, 1.3, "Hayır: Rule of 0\nhiçbir özel üye "
         "yazma;\nüyeler kendini yönetsin", FILL[1], EDGE[1], fs=8.8)
    _box(ax, 5.0, 3.3, 4.2, 1.3, "Evet: Rule of 5\nyıkıcı + kopya kur. +\n"
         "kopya atama + taşıma kur. +\ntaşıma atama", FILL[2], EDGE[2],
         fs=8.8)
    _box(ax, 9.6, 3.3, 4.0, 1.3, "Kopya anlamsız mı?\nKopyayı sil\n"
         "(delete), taşımaya izin ver", FILL[3], EDGE[3], fs=8.8)
    _arrow(ax, 7.0, 5.9, 2.5, 4.6, col=ACCENT_L, rad=0.1)
    _arrow(ax, 7.0, 5.9, 7.0, 4.6, col=ACCENT)
    _arrow(ax, 7.0, 5.9, 11.6, 4.6, col=ACCENT_L, rad=-0.1)
    _arrow(ax, 7.0, 3.3, 7.0, 2.1, col=MUTED)
    ax.text(7.0, 1.4, "Kaynak yönetimini bir sınıfa (unique_ptr, "
            "std::vector, Dizgi)\ndevret; sınıfın kendisi yıkıcı "
            "yazmasın.", ha="center", fontsize=8.8, color=MUTED)
    ax.text(3.0, 4.9, "hayır", fontsize=8.8, color=ACCENT_L)
    ax.text(7.3, 5.2, "evet", fontsize=8.8, color=ACCENT)
    ax.text(10.4, 4.9, "hayır", fontsize=8.8, color=ACCENT_L)
    return _save(fig, _yol("kural_secimi"))


if __name__ == "__main__":
    for f in (elle_vtable, nesne_duzeni, elmas_mro, sig_derin, dilimleme,
              bilesim_kalitim, raii_yigin, bellek_olcum, sanal_olcum,
              kural_secimi):
        print(f())
