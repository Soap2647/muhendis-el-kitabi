# -*- coding: utf-8 -*-
"""Bolum 37 - 'Derleyici Nasil Calisir' diyagramlari.

Olcum sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b37_zaman.csv   agac yorumcusu / VM / hizli VM suresi (Mini dili)
  b37_ir.csv      IR optimizasyon gecislerinin komut sayisi
Diger sekiller bolumdeki gercek calistirma ciktilarindan cizilir.
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
    return os.path.join(OUT, "b37_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------------------- #
def boru_hatti():
    fig, ax = _tuval(9.6, 3.6, 14, 5.4)
    ust = [("Kaynak\nmetin", 0.2), ("Sözcüksel\nçözümleme", 2.2),
           ("Ayrıştırma\n(AST)", 4.2), ("Anlamsal\nanaliz", 6.2),
           ("Ara gösterim\n(IR)", 8.2), ("Optimizasyon", 10.2)]
    for metin, x in ust:
        _box(ax, x, 3.2, 1.7, 1.2, metin, FILL[0], EDGE[0], fs=9.6)
    for x in [1.9, 3.9, 5.9, 7.9, 9.9]:
        _arrow(ax, x, 3.8, x + 0.3, 3.8, col=ACCENT_L)
    _box(ax, 10.2, 1.0, 1.7, 1.2, "Kod üretimi\n(bayt kodu / asm)",
         FILL[1], EDGE[1], fs=9.0)
    _box(ax, 6.2, 1.0, 1.7, 1.2, "Çalıştırma\n(VM / makine)",
         FILL[1], EDGE[1], fs=9.0)
    _arrow(ax, 11.05, 3.2, 11.05, 2.25, col=ACCENT_L)
    _arrow(ax, 10.0, 1.6, 7.95, 1.6, col=ACCENT_L)
    ax.text(0.2, 4.9, "ÖN UÇ: dile özgü (kaynak -> AST)", fontsize=9.4,
            weight="bold", color=EDGE[0])
    ax.text(8.2, 0.55, "ARKA UÇ: hedefe özgü (IR -> kod)", fontsize=9.4,
            weight="bold", color=EDGE[1])
    ax.text(0.2, 0.55, "Orta katman ara gösterim üzerinde çalışır; "
            "dil ve hedef bağımsızdır.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("boru_hatti"))


# --------------------------------------------------------------------------- #
def agac_karsilastir():
    fig, ax = _tuval(9.6, 4.6, 14, 6.6)
    ax.text(0.2, 6.2, "Somut sözdizimi ağacı (CST)", fontsize=9.6, weight="bold", color=INK)
    cst = [(2.2, 5.0, "ifade"), (1.0, 4.0, "toplama"),
           (3.4, 4.0, "+"), (0.2, 3.0, "carpma"), (1.9, 3.0, "..."),
           (0.2, 2.0, "birincil"), (0.2, 1.0, "2")]
    for x, y, t in cst:
        _box(ax, x, y, 0.95 if len(t) < 4 else 1.25, 0.6, t, FILL[2],
             EDGE[2], fs=8.4)
    _arrow(ax, 2.65, 5.0, 1.45, 4.6, col=MUTED, lw=1.0)
    _arrow(ax, 2.65, 5.0, 3.85, 4.6, col=MUTED, lw=1.0)
    _arrow(ax, 1.45, 4.0, 0.7, 3.6, col=MUTED, lw=1.0)
    _arrow(ax, 0.7, 3.0, 0.7, 2.6, col=MUTED, lw=1.0)
    _arrow(ax, 0.7, 2.0, 0.7, 1.6, col=MUTED, lw=1.0)
    ax.text(0.2, 0.75, "Parantez, öncelik katmanları ve birincil düğümler",
            fontsize=8.2, color=MUTED)
    ax.text(0.2, 0.45, "ağaçta ayrı düğüm olur.", fontsize=8.2, color=MUTED)
    ax.text(0.2, 0.12, "Ağacın tamamı çok daha büyük; yalnız bir kısmı çizildi.",
            fontsize=8.2, color=MUTED)
    ax.text(7.6, 6.2, "Soyut sözdizimi ağacı (AST)", fontsize=9.6,
            weight="bold", color=INK)
    _box(ax, 9.3, 4.9, 1.0, 0.6, "+", FILL[1], EDGE[1], fs=10, bold=True)
    _box(ax, 7.9, 3.4, 1.0, 0.6, "2", FILL[1], EDGE[1], fs=10)
    _box(ax, 10.6, 3.4, 1.0, 0.6, "*", FILL[1], EDGE[1], fs=10, bold=True)
    _box(ax, 9.6, 1.9, 1.0, 0.6, "3", FILL[1], EDGE[1], fs=10)
    _box(ax, 11.8, 1.9, 1.0, 0.6, "+", FILL[1], EDGE[1], fs=10, bold=True)
    _box(ax, 11.1, 0.5, 0.9, 0.6, "4", FILL[1], EDGE[1], fs=10)
    _box(ax, 12.5, 0.5, 0.9, 0.6, "1", FILL[1], EDGE[1], fs=10)
    for x1, y1, x2, y2 in [(9.8, 4.9, 8.4, 4.0), (9.8, 4.9, 11.1, 4.0),
                           (11.1, 3.4, 10.1, 2.5), (11.1, 3.4, 12.3, 2.5),
                           (12.3, 1.9, 11.55, 1.1), (12.3, 1.9, 12.95, 1.1)]:
        _arrow(ax, x1, y1, x2, y2, col=ACCENT, lw=1.1)
    ax.text(7.6, 0.25, "Yalnız anlamlı işlemler kalır (7 düğüm).",
            fontsize=8.2, color=MUTED)
    return _save(fig, _yol("agac"))


# --------------------------------------------------------------------------- #
def pratt():
    fig, ax = _tuval(9.6, 4.2, 14, 6.0)
    ax.text(0.2, 5.6, "Bağlama güçleri (Mini)", fontsize=9.6,
            weight="bold", color=INK)
    seviyeler = [("== !=", 10), ("< <= > >=", 20), ("+ -", 30),
                 ("* / %", 40), ("tekli -", 50), ("çağrı ( )", 60)]
    for i, (op, g) in enumerate(seviyeler):
        y = 4.6 - i * 0.62
        w = 0.07 * g
        _box(ax, 0.2, y, w, 0.5, "", FILL[i % 5], EDGE[i % 5])
        ax.text(0.3 + w, y + 0.25, f"{op}   güç {g}", fontsize=8.6,
                va="center", color=INK, family=MONO["family"])
    ax.text(0.2, 0.25, "Büyük güç = daha sıkı bağlanır.", fontsize=8.4,
            color=MUTED)
    ax.text(5.4, 5.6, "2 + 3 * (4 - 1) ağacı", fontsize=9.6,
            weight="bold", color=INK)
    d = [(9.0, 4.6, "+"), (7.0, 3.3, "2"), (11.0, 3.3, "*"),
         (10.0, 2.0, "3"), (12.2, 2.0, "-"), (11.2, 0.7, "4"),
         (13.1, 0.7, "1")]
    for x, y, t in d:
        _box(ax, x - 0.4, y - 0.3, 0.8, 0.6, t, FILL[0], EDGE[0],
             fs=10, bold=t in "+*-")
    for a, b in [(0, 1), (0, 2), (2, 3), (2, 4), (4, 5), (4, 6)]:
        _arrow(ax, d[a][0], d[a][1] - 0.3, d[b][0], d[b][1] + 0.3,
               col=ACCENT, lw=1.1)
    ax.text(5.4, 0.15, "Sağ taraf: ifade(güç) ile özyinelemeli çağrılır.",
            fontsize=8.2, color=MUTED)
    return _save(fig, _yol("pratt"))


# --------------------------------------------------------------------------- #
def kapsam_yigini():
    fig, ax = _tuval(9.6, 4.2, 14, 6.0)
    ax.text(0.2, 5.6, "Kod", fontsize=9.6, weight="bold", color=INK)
    kod = ["let x = 1;", "if (true) {", "  let x = 5;", "  print x;",
           "}", "print x;"]
    for i, s in enumerate(kod):
        ax.text(0.3, 5.0 - i * 0.55, s, fontsize=9.0, color=INK,
                family=MONO["family"])
    ax.text(5.0, 5.6, "Sembol tablosu yığını (satır 3 anında)",
            fontsize=9.6, weight="bold", color=INK)
    _box(ax, 5.0, 0.6, 4.4, 1.0, "küresel kapsam\nx -> slot 0 (değer 1)",
         FILL[0], EDGE[0], fs=9.0)
    _box(ax, 5.0, 1.9, 4.4, 1.0, "if-bloğu kapsamı\nx -> slot 1 (değer 5)",
         FILL[2], EDGE[2], fs=9.0)
    ax.text(5.0, 3.25, "Arama: en üstten (içten) başla; "
            "ilk bulunan kazanır.", fontsize=8.6, color=MUTED)
    _arrow(ax, 9.5, 2.5, 9.5, 3.1, col=ACCENT, lw=1.4)
    ax.text(9.6, 2.8, "bul(x)", fontsize=8.4, color=ACCENT)
    ax.text(5.0, 0.2, "Blok bitince üst kapsam: x=5 kaybolur, "
            "print x 1 yazar.", fontsize=8.4, color=MUTED)
    return _save(fig, _yol("kapsam"))


# --------------------------------------------------------------------------- #
def temel_bloklar():
    # blok_bol(ornek) ciktisi (ir_opt.py): B0..B4, B2 olu blok
    fig, ax = _tuval(9.6, 5.0, 14, 6.6)
    ax.text(0.2, 6.3, "Temel bloklar ve kontrol akış grafiği (IR örneği, "
            "optimizasyondan önce)", fontsize=9.4, weight="bold", color=INK)
    _box(ax, 0.3, 2.9, 3.4, 2.7, "B0\nx = 2 * 3\nt1 = x + 4\n"
         "y = t1 * a\nt2 = 5 * 5\nif_false t2 goto L1", FILL[0], EDGE[0],
         fs=8.2)
    _box(ax, 4.4, 4.9, 2.4, 0.9, "B1\ngoto L2", FILL[2], EDGE[2], fs=8.2)
    _box(ax, 4.4, 1.8, 2.4, 0.9, "B2 (ölü)\ny = 0", FILL[3], EDGE[3],
         fs=8.2)
    _box(ax, 7.8, 2.9, 2.6, 1.1, "B3\nL1:\nprint y", FILL[1], EDGE[1],
         fs=8.2)
    _box(ax, 11.2, 4.9, 2.6, 1.1, "B4\nL2:\nprint x", FILL[4], EDGE[4],
         fs=8.2)
    _arrow(ax, 3.7, 5.3, 4.4, 5.3, col=ACCENT, lw=1.3)
    ax.text(3.2, 5.6, "doğru:\ndüşer", fontsize=7.8, color=ACCENT,
            ha="center")
    _arrow(ax, 3.7, 3.7, 7.8, 3.4, col=ACCENT, lw=1.3)
    ax.text(5.6, 3.9, "yanlış: atla", fontsize=7.8, color=ACCENT)
    _arrow(ax, 6.8, 5.3, 11.2, 5.3, col=ACCENT, lw=1.3)
    ax.text(9.0, 5.6, "goto L2", fontsize=7.8, color=ACCENT, ha="center")
    _arrow(ax, 6.8, 2.2, 7.8, 3.0, col=MUTED, lw=1.0)
    _arrow(ax, 10.4, 3.5, 11.6, 4.9, col=MUTED, lw=1.0)
    ax.text(0.3, 1.5, "Kenarlar: 4 gerçek + 1 ölü blok kenarı (B2 -> B3).",
            fontsize=8.4, color=MUTED)
    ax.text(0.3, 0.9, "N = 5 blok, E = 5 kenar, P = 1: V(G) = E - N + 2P "
            "= 2.", fontsize=8.4, color=MUTED)
    ax.text(0.3, 0.3, "B2'ye giden hiçbir atlama yok; ölü kod eleme bunu "
            "siler.", fontsize=8.4, color=MUTED)
    return _save(fig, _yol("temel_blok"))


def ssa_phi():
    fig, ax = _tuval(9.6, 4.2, 14, 6.0)
    ax.text(0.2, 5.6, "SSA: her değişken yalnız bir kez atanır",
            fontsize=9.6, weight="bold", color=INK)
    _box(ax, 0.6, 3.6, 3.6, 1.2, "if (c)\nx1 = 1", FILL[0], EDGE[0],
         fs=9.2)
    _box(ax, 5.2, 3.6, 3.6, 1.2, "else\nx2 = 2", FILL[1], EDGE[1], fs=9.2)
    _box(ax, 2.6, 1.2, 4.6, 1.3, "birleşme\nx3 = φ(x1, x2)", FILL[3],
         EDGE[3], fs=9.6, bold=True)
    _arrow(ax, 2.4, 3.6, 4.2, 2.5, col=ACCENT, lw=1.3)
    _arrow(ax, 7.0, 3.6, 5.8, 2.5, col=ACCENT, lw=1.3)
    ax.text(9.6, 2.3, "φ, hangi kenardan\ngelindiğine göre\nx1 ya da "
            "x2 seçer.", fontsize=8.6, color=MUTED, va="center")
    ax.text(0.6, 0.3, "φ bir makine komutu değildir; kayıt tahsisinde "
            "birleşme noktasını\nçözmek için bir kavramdır (genel bilgi).",
            fontsize=8.2, color=MUTED)
    return _save(fig, _yol("ssa_phi"))


# --------------------------------------------------------------------------- #
def optimizasyon():
    satirlar = _oku_csv("b37_ir.csv")
    etiket, deger = [], []
    for r in satirlar:
        if r["tur"] == "0":
            etiket.append("başlangıç")
            deger.append(int(r["komut_sayisi"]))
        else:
            kisa = {"sabit_katla": "sabit", "erisilemez_sil": "erişilemez",
                    "gereksiz_atlama_sil": "atlama", "etiket_sil": "etiket",
                    "olu_atama_sil": "ölü atama"}[r["gecis"]]
            etiket.append(f"{r['tur']}. {kisa}")
            deger.append(int(r["komut_sayisi"]))
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    x = range(len(deger))
    ax.bar(x, deger, color=[EDGE[0] if i == 0 else ACCENT for i in x])
    for i, v in enumerate(deger):
        ax.text(i, v + 0.15, str(v), ha="center", fontsize=8.6, color=INK)
    ax.set_xticks(list(x))
    ax.set_xticklabels(etiket, rotation=35, ha="right", fontsize=8.0)
    ax.set_ylabel("komut sayısı (etiket hariç)", fontsize=9)
    ax.set_title("IR optimizasyonu: her geçişten sonra komut sayısı "
                 "(ölçüm: b37_ir.csv)", fontsize=10, color=INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("optimizasyon"))


# --------------------------------------------------------------------------- #
def yigin_izi():
    # iz_vm.py ciktisi: fn kare(x) { return x*x; } print kare(3) + 1;
    adimlar = [
        ("PUSH 3", [3], "__main__"),
        ("CALL kare", [], "kare x=3"),
        ("LOAD 0", [3], "kare"),
        ("LOAD 0", [3, 3], "kare"),
        ("MUL", [9], "kare"),
        ("RET", [9], "__main__"),
        ("PUSH 1", [9, 1], "__main__"),
        ("ADD", [10], "__main__"),
        ("PRINT", [], "__main__"),
    ]
    fig, ax = _tuval(9.6, 5.0, 14, 7.0)
    ax.text(0.2, 6.6, "Yığın ve çerçeve izi: kare(3) + 1", fontsize=9.6,
            weight="bold", color=INK)
    for i, (op, y, cer) in enumerate(adimlar):
        yy = 5.6 - i * 0.56
        ax.text(0.2, yy, f"{op:9}", fontsize=8.4, va="center",
                family=MONO["family"], color=INK)
        ax.text(2.3, yy, cer, fontsize=8.0, va="center", color=MUTED)
        for j, v in enumerate(y):
            _box(ax, 4.6 + j * 0.62, yy - 0.22, 0.55, 0.44, str(v),
                 FILL[0], EDGE[0], fs=8.4)
    ax.text(4.6, 0.3, "Sağda: komuttan SONRAKİ yığın (üstü en sağda).", fontsize=8.0, color=MUTED)
    return _save(fig, _yol("yigin_izi"))


# --------------------------------------------------------------------------- #
def baglayici():
    fig, ax = _tuval(9.6, 4.6, 14, 6.6)
    ax.text(0.2, 6.2, "prog.o (nesne): adresler boş",
            fontsize=9.4, weight="bold", color=INK)
    _box(ax, 0.3, 3.4, 4.0, 2.3,
         "main  (.text ofseti 0x0)\n  call kare_topla   <- 0x13\n"
         "  call printf       <- 0x29", FILL[0], EDGE[0], fs=8.6)
    ax.text(0.3, 2.8, "yer değiştirme (relocation): R_X86_64_PLT32\n"
            "ofset 0x13 -> kare_topla, ofset 0x29 -> printf",
            fontsize=7.9, color=MUTED, va="top")
    _arrow(ax, 4.5, 4.5, 5.5, 4.5, col=ACCENT, lw=1.6)
    ax.text(5.0, 5.0, "bağla", fontsize=9.0, ha="center", color=ACCENT)
    ax.text(5.8, 6.2, "prog (çalıştırılabilir)",
            fontsize=9.4, weight="bold", color=INK)
    _box(ax, 5.8, 3.4, 4.0, 2.3,
         "main         0x1149\nkare_topla   0x117d\nsabit        0x119a\n"
         "printf       PLT (libc)", FILL[1], EDGE[1], fs=8.6)
    ax.text(5.8, 2.8, "call'un hedefi artık kare_topla'nın gerçek adresi;\n"
            "printf libc.so.6 içinde, çalışma anında çözülür.",
            fontsize=7.9, color=MUTED, va="top")
    ax.text(0.3, 0.7, "Kaynak: nm, readelf -r (ofsetler gerçek çıktıdan).",
            fontsize=8.2, color=MUTED)
    ax.text(0.3, 0.25, "Statik bağlamada printf de çalışma dosyasına gömülür "
            "(prog_static ~785 KB, prog ~16 KB).", fontsize=8.2, color=MUTED)
    return _save(fig, _yol("baglayici"))


# --------------------------------------------------------------------------- #
def olcum():
    satirlar = _oku_csv("b37_zaman.csv")
    n = [int(r["n"]) for r in satirlar]
    agac = [float(r["agac_s"]) for r in satirlar]
    vm = [float(r["vm_s"]) for r in satirlar]
    hizli = [float(r["vm_hizli_s"]) for r in satirlar]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.plot(n, agac, "o-", color=EDGE[0], label="ağaç yorumcusu")
    ax.plot(n, vm, "s-", color=ACCENT, label="bayt kodu VM (naif)")
    ax.plot(n, hizli, "^-", color=EDGE[1], label="bayt kodu VM (hızlı)")
    ax.set_xlabel("döngü sayısı n", fontsize=9)
    ax.set_ylabel("en iyi süre (s), 3 tekrar", fontsize=9)
    ax.set_title("Mini: aynı programın yürütme süresi (CPython 3.12.10)",
                 fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8.6)
    ax.grid(color=RULE, lw=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("olcum"))


if __name__ == "__main__":
    for f in (boru_hatti, agac_karsilastir, pratt, kapsam_yigini,
              temel_bloklar, ssa_phi, optimizasyon, yigin_izi,
              baglayici, olcum):
        print(f())
