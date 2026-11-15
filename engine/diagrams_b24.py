# -*- coding: utf-8 -*-
"""Bolum 24 - CPU Mimarisi diyagramlari.

Olcum grafikleri (dal, ILP, SIMD) engine/veri/b24_*.csv dosyalarini okur;
diger sekiller bolumdeki kavramsal semalardan cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b24_%s.png" % ad)


def _tuval(w, h, xl=10, yl=10):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------------------- #
def isa_katman():
    """ISA ile mikromimari arasindaki katman ayrimi."""
    fig, ax = _tuval(9.6, 6.6)
    _box(ax, 1.0, 8.5, 8.0, 1.0,
         "Yazılım: C, C++, Python, Rust", fill=FILL[0], edge=EDGE[0],
         fs=10.5, bold=True)
    _arrow(ax, 5.0, 8.5, 5.0, 7.9, col=MUTED, lw=1.2)
    _box(ax, 1.0, 6.9, 8.0, 0.9,
         "Derleyici ve bağlayıcı: gcc -O2  →  makine kodu", fill=FILL[0],
         edge=EDGE[0], fs=10)
    _arrow(ax, 5.0, 6.9, 5.0, 6.3, col=MUTED, lw=1.2)
    _box(ax, 0.6, 4.6, 8.8, 1.6, "", fill=FILL[3], edge=ACCENT)
    ax.text(5.0, 5.85, "ISA (komut kümesi mimarisi): yazılımın gördüğü sözleşme",
            ha="center", va="center", fontsize=10, color=ACCENT, weight="bold")
    ax.text(5.0, 5.15,
            "komutlar  ·  yazmaçlar  ·  adresleme kipleri  ·  bellek sıralama\n"
            "kurallarının görünümü  ·  ayrıcalık seviyeleri  ·  kesmeler",
            ha="center", va="center", fontsize=8.6, color=INK)
    _arrow(ax, 5.0, 4.6, 5.0, 4.0, col=MUTED, lw=1.2)
    kutular = ["boru hattı", "dal tahmini", "önbellek",
               "süperskalar\nbirimler", "sıra dışı\nyürütme"]
    x = 0.6
    for k in kutular:
        _box(ax, x, 1.9, 1.62, 1.6, k, fill=FILL[1], edge=EDGE[1], fs=8.8)
        x += 1.79
    ax.text(5.0, 3.75, "Mikromimari: aynı ISA'yı farklı donanımda gerçekleştirme",
            ha="center", va="center", fontsize=9.4, color=EDGE[1])
    _arrow(ax, 5.0, 1.9, 5.0, 1.3, col=MUTED, lw=1.2)
    _box(ax, 1.0, 0.25, 8.0, 1.0,
         "Silikon: transistörler ve devreler (aynı ISA, farklı işlemciler)",
         fill=FILL[2], edge=EDGE[2], fs=9.6)
    return _save(fig, _yol("isa_katman"))


def yazmac_haritasi():
    """x86-64 genel amaçlı yazmaçlar ve çağrı kuralındaki rolleri."""
    fig, ax = _tuval(9.6, 6.0)
    ax.text(5.0, 9.6, "x86-64 genel amaçlı yazmaçları (64 bit)",
            ha="center", fontsize=11, color=INK, weight="bold")
    satir = [
        ["rax", "rbx", "rcx", "rdx"],
        ["rsi", "rdi", "rbp", "rsp"],
        ["r8", "r9", "r10", "r11"],
        ["r12", "r13", "r14", "r15"],
    ]
    # (rol metni, grup): grup 0 geçici, 1 argüman, 2 korunan, 3 yığın/çerçeve
    rol = {
        "rax": ("dönüş değeri", 0), "rcx": ("arg 4 (SysV)", 1),
        "rdx": ("arg 3 (SysV)", 1), "rsi": ("arg 2 (SysV)", 1),
        "rdi": ("arg 1 (SysV)", 1), "r8": ("arg 5 (SysV)", 1),
        "r9": ("arg 6 (SysV)", 1), "rbx": ("korunan (callee)", 2),
        "rbp": ("çerçeve; korunan", 3), "rsp": ("yığın işaretçisi", 3),
        "r10": ("geçici (caller)", 0), "r11": ("geçici; syscall bozar", 0),
        "r12": ("korunan (callee)", 2), "r13": ("korunan (callee)", 2),
        "r14": ("korunan (callee)", 2), "r15": ("korunan (callee)", 2),
    }
    renk = {0: FILL[1], 1: FILL[0], 2: FILL[2], 3: FILL[3]}
    kenar = {0: EDGE[1], 1: EDGE[0], 2: EDGE[2], 3: EDGE[3]}
    for i, sat in enumerate(satir):
        for j, ad in enumerate(sat):
            x = 0.5 + j * 2.35
            y = 7.4 - i * 1.65
            _, grp = rol[ad]
            _box(ax, x, y, 2.05, 1.2, "", fill=renk[grp], edge=kenar[grp])
            ax.text(x + 1.025, y + 0.82, ad, ha="center", va="center",
                    fontsize=10.5, weight="bold", color=INK)
            ax.text(x + 1.025, y + 0.32, rol[ad][0], ha="center",
                    va="center", fontsize=7.6, color=INK)
    ax.text(0.5, 0.45,
            "Renkler: mavi = argüman (SysV)  ·  sarı = korunan (callee-saved)\n"
            "pembe = yığın ve çerçeve  ·  yeşil = geçici (caller-saved)\n"
            "eax, ax, al aynı yazmacın alt parçalarıdır: rax'ın düşük 32 biti eax.",
            fontsize=8.4, color=INK, va="center")
    return _save(fig, _yol("yazmac"))


def cagri_cerceve():
    """System V ve Windows x64 çağrı çerçeveleri yan yana."""
    fig, ax = _tuval(9.6, 6.4)
    for x0, baslik, arglar, altlar in (
        (0.4, "System V AMD64 (Linux)",
         "argümanlar: rdi, rsi, rdx, rcx, r8, r9\n5. ve sonrası yığında",
         [("dönüş adresi (8 bayt)", FILL[0], EDGE[0]),
          ("kaydedilen rbp (8 bayt)", FILL[1], EDGE[1]),
          ("yerel değişkenler", FILL[2], EDGE[2]),
          ("kayıtlı korunan yazmaçlar", FILL[1], EDGE[1])]),
        (5.2, "Windows x64",
         "argümanlar: rcx, rdx, r8, r9\n5. argüman 40(%rsp)'de",
         [("dönüş adresi (8 bayt)", FILL[0], EDGE[0]),
          ("gölge alan (32 bayt)", FILL[4], EDGE[4]),
          ("yerel değişkenler", FILL[2], EDGE[2]),
          ("kayıtlı korunan yazmaçlar", FILL[1], EDGE[1])]),
    ):
        ax.text(x0 + 2.0, 9.5, baslik, ha="center", fontsize=10.5,
                weight="bold", color=INK)
        ax.text(x0 + 2.0, 8.6, arglar, ha="center", va="center",
                fontsize=8.2, color=ACCENT_L)
        y = 7.4
        for etiket, fill, edge in altlar:
            _box(ax, x0 + 0.2, y - 0.85, 3.6, 0.8, etiket, fill=fill,
                 edge=edge, fs=8.6)
            y -= 0.95
        ax.text(x0 + 2.0, y - 0.25, "yığın büyür: yüksek adres → düşük adres",
                ha="center", fontsize=7.8, color=MUTED)
    ax.plot([0.2, 9.4], [2.4, 2.4], color=RULE, lw=1.0)
    ax.text(0.5, 1.85,
            "Yaprak fonksiyon (başka fonksiyon çağırmaz) rsp'yi değiştirmeden",
            fontsize=8.6, color=INK)
    ax.text(0.5, 1.45,
            "rsp'nin 128 bayt altını kullanabilir: bu alan kırmızı bölgedir (SysV).",
            fontsize=8.6, color=INK)
    ax.text(0.5, 0.85,
            "Windows x64'te kırmızı bölge yoktur; gölge alan çağıranın ayırdığı\n"
            "32 baytlık alandır. Bu ayrım genel bilgidir; bkz. 24.4.",
            fontsize=8.4, color=MUTED)
    return _save(fig, _yol("cagri"))


def boru_hatti():
    """5 asamali boru hatti: load-use tehlikesi ve balonca."""
    fig, ax = _tuval(9.6, 5.2, xl=10, yl=8)
    renk = {"IF": FILL[0], "ID": FILL[1], "EX": FILL[2], "MEM": FILL[3],
            "WB": FILL[4]}
    kenar = {"IF": EDGE[0], "ID": EDGE[1], "EX": EDGE[2], "MEM": EDGE[3],
             "WB": EDGE[4]}
    satirlar = [
        ("I1: lw  r1, [x]", {1: "IF", 2: "ID", 3: "EX", 4: "MEM", 5: "WB"}),
        ("I2: add r2, r1, r3", {2: "IF", 3: "ID", 4: "bekle", 5: "EX",
                                6: "MEM", 7: "WB"}),
        ("I3: sub r4, r5, r6", {3: "IF", 4: "bekle", 5: "ID", 6: "EX",
                                7: "MEM", 8: "WB"}),
        ("I4: or  r7, r8, r9", {4: "IF", 5: "bekle", 6: "ID", 7: "EX",
                                8: "MEM"}),
    ]
    ax.text(0.2, 7.6, "komut", fontsize=8.6, color=MUTED, weight="bold")
    for c in range(1, 9):
        ax.text(2.75 + (c - 1) * 0.82 + 0.37, 7.6, "c%d" % c, ha="center",
                fontsize=8.2, color=MUTED)
    for r, (ad, h) in enumerate(satirlar):
        y = 6.6 - r * 1.25
        ax.text(0.2, y + 0.3, ad, fontsize=8.4, color=INK, va="center")
        for c, s in h.items():
            x = 2.75 + (c - 1) * 0.82
            if s == "bekle":
                _box(ax, x, y, 0.74, 0.6, "boş", fill="#FFFFFF",
                     edge=RULE, fs=7.4, tcol=MUTED)
            else:
                _box(ax, x, y, 0.74, 0.6, s, fill=renk[s], edge=kenar[s],
                     fs=8.0)
    ax.text(0.3, 1.25,
            "I2 'add' komutu r1'i I1'den bekler. lw'nin verisi MEM aşamasında\n"
            "okunur; add en erken c5'te EX'e girebilir: 1 çevrimlik balonca.\n"
            "Balonca (bubble): boru hattına giren boş bir iş. İletme\n"
            "(forwarding) bu durumda tek başına yetmez.",
            fontsize=8.2, color=INK, va="center")
    return _save(fig, _yol("boru"))


def dal_olcum():
    """Sirali ve sirasiz dizide dal tahmini: ns/eleman."""
    satir = _oku("b24_dal_olcum.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    gruplar = [("dalli, kontrollü\n(-O2, if-conversion kapalı)", "kontrollu", "dalli"),
               ("dalsız, kontrollü\n(maske ile)", "kontrollu", "dalsiz"),
               ("dalli, doğal -O2\n(derleyici cmov üretti)", "dogal", "dalli")]
    x = 0
    xt, xl = [], []
    for baslik, der, fn in gruplar:
        for k, dizi, renk in ((0, "sirasiz", ACCENT), (1, "sirali", ACCENT_L)):
            vals = [float(r["ns_per_eleman"]) for r in satir
                    if r["derleme"] == der and r["fonksiyon"] == fn
                    and r["dizi"] == dizi]
            v = sum(vals) / len(vals)
            ax.bar(x + k * 0.42, v, width=0.38, color=renk,
                   edgecolor=INK, linewidth=0.6)
            ax.text(x + k * 0.42, v + 0.05, "%.2f" % v, ha="center",
                    fontsize=8.6, color=INK)
        xt.append(x + 0.21)
        xl.append(baslik)
        x += 1.3
    ax.set_xticks(xt)
    ax.set_xticklabels(xl, fontsize=8.4)
    ax.set_ylabel("ns / eleman (düşük daha iyi)", fontsize=9)
    ax.set_ylim(0, 2.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(handles=[Rectangle((0, 0), 1, 1, color=ACCENT),
                       Rectangle((0, 0), 1, 1, color=ACCENT_L)],
              labels=["sırasız dizi (rastgele dallar)", "sıralı dizi"],
              fontsize=8.6, frameon=False, loc="upper right")
    ax.set_title("Dal tahmini: aynı toplam, farklı dal örüntüsü (2 koşunun ortalaması)",
                 fontsize=9.6, color=INK)
    fig.tight_layout()
    return _save(fig, _yol("dal"))


def ilp_olcum():
    """Akumulator sayisina gore ns/eleman ve hizlanma."""
    satir = _oku("b24_ilp_olcum.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    sayilar = [1, 2, 4, 8]
    ort = []
    for n in sayilar:
        vals = [float(r["ns_per_eleman"]) for r in satir
                if int(r["akumulator"]) == n]
        ort.append(sum(vals) / len(vals))
    x = list(range(len(sayilar)))
    ax.bar(x, ort, color=[ACCENT, ACCENT_L, EDGE[1], EDGE[4]],
           edgecolor=INK, linewidth=0.6, width=0.55)
    for i, v in enumerate(ort):
        ax.text(i, v + 0.012, "%.3f ns\n%.2f kat" % (v, ort[0] / v),
                ha="center", fontsize=8.6, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(["1 akümülatör\n(bağımlı zincir)", "2", "4", "8"],
                       fontsize=8.6)
    ax.set_ylabel("ns / eleman (düşük daha iyi)", fontsize=9)
    ax.set_ylim(0, 0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Toplama döngüsünde ILP: akümülatör sayısı ve hız (L1'de, double)",
                 fontsize=9.6, color=INK)
    fig.tight_layout()
    return _save(fig, _yol("ilp"))


def simd_serit():
    """Skaler, SSE ve AVX2 ile aynı anda işlenen eleman sayısı."""
    fig, ax = _tuval(9.6, 4.6)
    satirlar = [
        ("skaler (1 float / komut)", 1, FILL[3], EDGE[3]),
        ("SSE (128 bit, 4 float / komut)", 4, FILL[2], EDGE[2]),
        ("AVX2 (256 bit, 8 float / komut)", 8, FILL[1], EDGE[1]),
    ]
    for i, (ad, n, fill, edge) in enumerate(satirlar):
        y = 6.6 - i * 2.0
        ax.text(0.3, y + 0.55, ad, fontsize=9.4, color=INK, weight="bold")
        for k in range(8):
            dolu = k < n
            _box(ax, 0.4 + k * 1.05, y - 0.55, 0.92, 0.9,
                 "a[%d]" % k if dolu else "",
                 fill=fill if dolu else "#FFFFFF",
                 edge=edge if dolu else RULE, fs=8.4)
    ax.text(0.4, 0.45,
            "Aynı 8 float üzerinde: skaler 8 komut, SSE 2 komut, AVX2 1 komut.\n"
            "Her komut bir yazmaçtaki birden çok değeri aynı anda işler.",
            fontsize=8.6, color=INK, va="center")
    return _save(fig, _yol("simd_serit"))


def simd_olcum():
    """Hizali ve hizasiz kosullarda SIMD ve skaler karsilastirma."""
    satir = _oku("b24_simd_olcum.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                 gridspec_kw={"width_ratios": [1.3, 1]})
    etiket = ["skaler", "oto vektör\n(SSE)", "AVX2 + FMA"]
    anahtar = ["skaler", "oto_vektor", "avx2_fma"]
    v = []
    for an in anahtar:
        vals = [float(r["ns_per_eleman"]) for r in satir
                if r["hizalama"] == "evet" and r["derleme"] == "o3"
                and r["surum"] == an]
        v.append(min(vals))
    a1.bar(range(3), v, color=[EDGE[3], EDGE[2], EDGE[1]], edgecolor=INK,
           linewidth=0.6, width=0.55)
    for i, val in enumerate(v):
        a1.text(i, val + 0.005, "%.3f" % val, ha="center", fontsize=8.6)
    a1.set_xticks(range(3))
    a1.set_xticklabels(etiket, fontsize=8.4)
    a1.set_ylabel("ns / eleman", fontsize=9)
    a1.set_ylim(0, 0.27)
    a1.set_title("Hizalı döngüler (-O3)", fontsize=9.4, color=INK)
    a1.spines[["top", "right"]].set_visible(False)
    kat = [("hizasız\n-O3", "hayir", "o3"),
           ("hizasız\n-O2", "hayir", "o2"),
           ("hizalı\n-O3", "evet", "o3"),
           ("hizalı\n-O2", "evet", "o2")]
    w = []
    for _, h, d in kat:
        vals = [float(r["ns_per_eleman"]) for r in satir
                if r["hizalama"] == h and r["derleme"] == d
                and r["surum"] == "skaler"]
        w.append(min(vals))
    a2.bar(range(4), w, color=[ACCENT, ACCENT, ACCENT_L, ACCENT_L],
           edgecolor=INK, linewidth=0.6, width=0.6)
    for i, val in enumerate(w):
        a2.text(i, val + 0.005, "%.3f" % val, ha="center", fontsize=8.4)
    a2.set_xticks(range(4))
    a2.set_xticklabels([k[0] for k in kat], fontsize=7.8)
    a2.set_ylim(0, 0.52)
    a2.set_title("Aynı skaler kod: hizalamanın etkisi", fontsize=9.4, color=INK)
    a2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("simd_olcum"))


def halka():
    """x86 ayricalik halkalari ve ARM EL seviyeleri."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.8),
                                 gridspec_kw={"width_ratios": [1.2, 1]})
    a1.set_xlim(0, 10)
    a1.set_ylim(0, 10)
    a1.axis("off")
    a2.set_xlim(0, 10)
    a2.set_ylim(0, 10)
    a2.axis("off")
    cx, cy = 4.6, 5.0
    for r, fill, edge in ((4.3, FILL[0], EDGE[0]),
                          (3.0, FILL[1], EDGE[1]),
                          (2.0, FILL[2], EDGE[2]),
                          (1.0, FILL[3], EDGE[3])):
        a1.add_patch(Circle((cx, cy), r, facecolor=fill, edgecolor=edge,
                            linewidth=1.2))
    a1.text(cx, cy + 0.2, "Halka 0", ha="center", fontsize=9.2, weight="bold")
    a1.text(cx, cy - 0.35, "çekirdek", ha="center", fontsize=8.4)
    a1.text(cx, 9.6, "Halka 3: kullanıcı programı (CPL = 3)",
            ha="center", fontsize=8.6, color=EDGE[0])
    a1.text(cx, 0.25, "Halka 0: çekirdek (CPL = 0)",
            ha="center", fontsize=8.6, color=EDGE[3])
    a1.set_title("x86-64: ayrıcalık halkaları", fontsize=9.4, color=INK)
    seviyeler = [("EL3", "güvenli monitör (firmware)", FILL[3], EDGE[3]),
                 ("EL2", "hipervizör", FILL[2], EDGE[2]),
                 ("EL1", "işletim sistemi çekirdeği", FILL[1], EDGE[1]),
                 ("EL0", "kullanıcı programı", FILL[0], EDGE[0])]
    for i, (k, a, f, e) in enumerate(seviyeler):
        y = 7.6 - i * 1.8
        _box(a2, 0.6, y, 8.8, 1.4, "", fill=f, edge=e)
        a2.text(1.2, y + 0.7, k, fontsize=10, weight="bold", color=INK,
                va="center")
        a2.text(3.2, y + 0.7, a, fontsize=8.8, color=INK, va="center")
    a2.set_title("ARM (AArch64): Exception Level", fontsize=9.4, color=INK)
    fig.tight_layout()
    return _save(fig, _yol("halka"))


def syscall_yol():
    """Sistem cagrisinin CPU tarafi: kullanici -> cekirdek -> kullanici."""
    fig, ax = _tuval(9.6, 4.4)
    kutular = [
        (0.2, 6.2, "Kullanıcı kodu\n(getppid)", FILL[0], EDGE[0]),
        (2.5, 6.2, "syscall\nrax = 110", FILL[2], EDGE[2]),
        (4.8, 6.2, "entry_SYSCALL_64\nswapgs, yığın", FILL[3], EDGE[3]),
        (7.1, 6.2, "do_syscall_64\nsistem çağrı tablosu", FILL[1], EDGE[1]),
    ]
    for x, y, t, f, e in kutular:
        _box(ax, x, y, 2.1, 1.4, t, fill=f, edge=e, fs=8.6)
    for i in range(3):
        x1 = kutular[i][0] + 2.1
        _arrow(ax, x1 + 0.02, 6.9, kutular[i + 1][0] - 0.02, 6.9,
               col=INK, lw=1.2)
    _box(ax, 4.8, 2.0, 2.1, 1.4, "sysret\nrcx → rip, r11 → rflags",
         fill=FILL[4], edge=EDGE[4], fs=8.4)
    _arrow(ax, 8.15, 6.2, 6.9, 3.4, col=INK, lw=1.2, rad=0.2)
    _arrow(ax, 4.8, 2.7, 2.4, 2.7, col=INK, lw=1.2)
    _box(ax, 0.2, 2.0, 2.1, 1.4, "dönüş değeri\nrax'ta", fill=FILL[0],
         edge=EDGE[0], fs=8.6)
    ax.text(0.2, 0.7,
            "CPL (geçerli ayrıcalık) 3'ten 0'a geçer. Çekirdek işi bitirince\n"
            "sysret ile CPL tekrar 3'e döner ve dönüş değeri rax'ta kalır.",
            fontsize=8.4, color=INK, va="center")
    return _save(fig, _yol("syscall"))


if __name__ == "__main__":
    for f in (isa_katman, yazmac_haritasi, cagri_cerceve, boru_hatti,
              dal_olcum, ilp_olcum, simd_serit, simd_olcum, halka, syscall_yol):
        print(f())
