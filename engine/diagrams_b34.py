# -*- coding: utf-8 -*-
"""Bölüm 34 - 'SQL Derinlemesine' diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV dosyalarını okur:
  b34_indeks_olcum.csv  indeks öncesi / sonrası medyan süreler
  b34_yazma_olcum.csv   autocommit / tek işlem ve indeks sayısı
  b34_n1_olcum.csv      N+1 ile tek sorgu karşılaştırması
Diğer şekiller bölümdeki örnek değerlerden çizilir.
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
    return os.path.join(OUT, "b34_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _hucre(ax, x, y, w, h, metin, fill="#ffffff", edge=RULE, fs=9.5,
           tcol=INK, bold=False, kalin=0.9):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                           linewidth=kalin))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center",
            fontsize=fs, color=tcol, weight="bold" if bold else "normal")


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. Yazılış ve yürütülme sırası -------------------------------------- #
def yurutme_sirasi():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=7)
    yazilis = ["SELECT", "FROM", "WHERE", "GROUP BY", "HAVING",
               "ORDER BY", "LIMIT"]
    yurutme = ["FROM", "WHERE", "GROUP BY", "HAVING", "SELECT",
               "ORDER BY", "LIMIT"]
    w, g = 1.78, 0.2
    ax.text(0.1, 6.3, "Yazılış sırası (sen yazarsın)", fontsize=10,
            color=MUTED, weight="bold")
    for i, k in enumerate(yazilis):
        x = 0.1 + i * (w + g)
        _box(ax, x, 4.9, w, 0.95, k, FILL[0], MUTED, fs=10)
    ax.text(0.1, 4.3, "Yürütülme sırası (motor çalıştırır)", fontsize=10,
            color=ACCENT, weight="bold")
    for i, k in enumerate(yurutme):
        x = 0.1 + i * (w + g)
        _box(ax, x, 2.9, w, 0.95, k, FILL[3], EDGE[3], fs=10, bold=True)
        if i < len(yurutme) - 1:
            _arrow(ax, x + w, 3.37, x + w + g, 3.37, col=ACCENT, lw=1.3)
    ax.text(0.1, 2.3, "WHERE çalışırken SELECT'teki takma adlar henüz "
            "yoktur.", fontsize=9.5, color=INK)
    ax.text(0.1, 1.7, "Takma ad WHERE'de yazılınca standart SQL bunu "
            "reddeder; SQLite kabul eder.", fontsize=9.5, color=INK)
    ax.text(0.1, 1.1, "Sıralama (ORDER BY) takma adı görür, çünkü SELECT "
            "bitmiştir.", fontsize=9.5, color=INK)
    return _save(fig, _yol("yurutme_sirasi"))


# 2. JOIN türleri: satır eşleşme tabloları ---------------------------- #
def join_turleri():
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.8))
    tablolar = [
        ("INNER JOIN", [(2, 2), (3, 3)]),
        ("LEFT JOIN", [(1, None), (2, 2), (3, 3)]),
        ("RIGHT JOIN", [(2, 2), (3, 3), (None, 4)]),
        ("FULL JOIN", [(1, None), (2, 2), (3, 3), (None, 4)]),
    ]
    for ax, (ad, satirlar) in zip(axes.flat, tablolar):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
        ax.text(5, 9.5, ad, ha="center", fontsize=11.5, weight="bold",
                color=ACCENT)
        _hucre(ax, 1.4, 7.6, 3.0, 0.9, "A.id", FILL[0], EDGE[0],
               bold=True)
        _hucre(ax, 4.4, 7.6, 3.0, 0.9, "B.id", FILL[1], EDGE[1],
               bold=True)
        for i, (a, b) in enumerate(satirlar):
            y = 6.7 - i * 0.9
            fa = "#ffffff" if a is not None else "#F4F1EC"
            fb = "#ffffff" if b is not None else "#F4F1EC"
            _hucre(ax, 1.4, y, 3.0, 0.9,
                   "NULL" if a is None else str(a),
                   fa, RULE, tcol=MUTED if a is None else INK)
            _hucre(ax, 4.4, y, 3.0, 0.9,
                   "NULL" if b is None else str(b),
                   fb, RULE, tcol=MUTED if b is None else INK)
        ax.text(5, 0.6, "%d satır" % len(satirlar), ha="center",
                fontsize=9.5, color=MUTED)
    fig.subplots_adjust(hspace=0.05, wspace=0.05)
    fig.text(0.5, 0.005, "Venn şeması satır çoğalmasını ve NULL "
             "dolgusunu göstermez; satır eşleşme tablosu gösterir.",
             ha="center", fontsize=9, color=MUTED)
    return _save(fig, _yol("join_turleri"))


# 3. Üç değerli mantık ------------------------------------------------- #
def null_mantik():
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0))
    etiket = ["T", "F", "U"]
    AND = {("T", "T"): "T", ("T", "F"): "F", ("T", "U"): "U",
           ("F", "T"): "F", ("F", "F"): "F", ("F", "U"): "F",
           ("U", "T"): "U", ("U", "F"): "F", ("U", "U"): "U"}
    OR = {("T", "T"): "T", ("T", "F"): "T", ("T", "U"): "T",
          ("F", "T"): "T", ("F", "F"): "F", ("F", "U"): "U",
          ("U", "T"): "T", ("U", "F"): "U", ("U", "U"): "U"}
    renk = {"T": FILL[1], "F": FILL[3], "U": FILL[2]}
    for ax, (ad, tablo) in zip(axes, [("AND", AND), ("OR", OR)]):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
        ax.text(5, 9.4, ad, ha="center", fontsize=12, weight="bold",
                color=ACCENT)
        for j, c in enumerate(etiket):
            _hucre(ax, 2.2 + j * 2.1, 7.4, 2.0, 1.0, c, FILL[0], EDGE[0],
                   bold=True, fs=11)
        for i, r in enumerate(etiket):
            _hucre(ax, 0.2, 6.2 - i * 2.1, 2.0, 1.0, r, FILL[0], EDGE[0],
                   bold=True, fs=11)
            for j, c in enumerate(etiket):
                v = tablo[(r, c)]
                _hucre(ax, 2.2 + j * 2.1, 6.2 - i * 2.1, 2.0, 1.0, v,
                       renk[v], RULE, bold=True, fs=11)
    fig.text(0.5, 0.03, "T: doğru, F: yanlış, U: bilinmiyor (NULL). "
             "NOT U = U. WHERE yalnız T satırlarını geçirir.",
             ha="center", fontsize=9.5, color=INK)
    fig.subplots_adjust(wspace=0.1, bottom=0.12)
    return _save(fig, _yol("null_mantik"))


# 4. Özyinelemeli CTE: çalışma tablosu iterasyonu (Fibonacci) -------- #
def ozyinelemeli_cte():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7)
    satirlar = [(1, 0, 1), (2, 1, 1), (3, 1, 2), (4, 2, 3), (5, 3, 5),
                (6, 5, 8)]
    etiket = ["tohum", "1. yineleme", "2. yineleme", "3. yineleme",
              "4. yineleme", "5. yineleme"]
    w, g = 2.0, 0.3
    for i, ((n, a, b), e) in enumerate(zip(satirlar, etiket)):
        x = 0.2 + i * (w + g)
        ax.text(x + w / 2, 5.9, e, ha="center", fontsize=9, color=MUTED)
        _box(ax, x, 3.9, w, 1.5, "n=%d\na=%d\nb=%d" % (n, a, b),
             FILL[i % 3], EDGE[i % 3], fs=10)
        if i < len(satirlar) - 1:
            _arrow(ax, x + w, 4.65, x + w + g, 4.65, col=ACCENT, lw=1.3)
    ax.text(7.0, 2.9, "Her adımda yalnız bir önceki satır kullanılır:",
            ha="center", fontsize=10, color=INK)
    ax.text(7.0, 2.3, "a' = b,   b' = a + b   (n bir artar)", ha="center",
            fontsize=10, color=ACCENT, weight="bold")
    ax.text(7.0, 1.4, "Bu, Bölüm 16.3'teki tabulation tablosunun satır "
            "satır dolmasıyla aynıdır.", ha="center", fontsize=9.5,
            color=MUTED)
    return _save(fig, _yol("ozyinelemeli_cte"))


# 5. Pencere çerçevesi: 5 noktalı hareketli ortalama ------------------ #
def pencere_cercevesi():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=7)
    zaman = [0, 300, 600, 900, 1200, 1500, 1800, 2100, 2400]
    ger = [24.8, 24.6, 24.5, 24.1, 23.9, 23.7, 23.6, 23.2, 23.0]
    w, g = 1.38, 0.1
    x0 = 0.4
    for i, (z, v) in enumerate(zip(zaman, ger)):
        x = x0 + i * (w + g)
        akim = i == 4
        _box(ax, x, 3.0, w, 1.1, ("%.1f" % v).replace(".", ","),
             FILL[3] if akim else FILL[0], ACCENT if akim else EDGE[0],
             fs=10.5, bold=akim)
        ax.text(x + w / 2, 2.6, "%d sn" % z, ha="center", fontsize=8.5,
                color=MUTED)
    xa = x0 + 2 * (w + g) - 0.05
    xb = x0 + 6 * (w + g) + w + 0.05
    ax.plot([xa, xa, xb, xb], [4.35, 4.6, 4.6, 4.35], color=ACCENT,
            lw=1.6)
    ax.text((xa + xb) / 2, 4.85, "ROWS BETWEEN 2 PRECEDING AND "
            "2 FOLLOWING", ha="center", fontsize=9.5, color=ACCENT,
            weight="bold")
    ax.text(x0 + 4 * (w + g) + w / 2, 1.9, "↑ geçerli satır", ha="center",
            fontsize=9.5, color=ACCENT)
    m = sum(ger[2:7]) / 5
    ax.text(7.0, 1.0, "Bu satırın ortalaması: (24,5 + 24,1 + 23,9 + 23,7 "
            "+ 23,6) / 5 = %s" % ("%.2f" % m).replace(".", ","),
            ha="center", fontsize=9.5, color=INK)
    ax.text(7.0, 0.3, "Gerilimler örnek değerlerdir; yalnız kavramı "
            "göstermek için.", ha="center", fontsize=8.5, color=MUTED)
    return _save(fig, _yol("pencere_cercevesi"))


# 6. Bileşik indeks ve en sol önek ------------------------------------ #
def bilesik_indeks():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=8.6)
    girdiler = [(4, 0), (4, 300), (4, 600), (5, 0), (5, 300), (5, 600),
                (5, 900), (6, 0), (6, 300), (7, 0), (7, 600)]
    w, g = 1.18, 0.07
    ax.text(0.2, 8.0, "Dizin sırası: (ucus_id, zaman_sn) — önce ucus_id, "
            "sonra zaman_sn", fontsize=9.8, color=MUTED, weight="bold")
    for i, (u, z) in enumerate(girdiler):
        x = 0.2 + i * (w + g)
        vurgu = u == 5 and 300 <= z <= 900
        _box(ax, x, 5.6, w, 0.9, "(%d, %d)" % (u, z),
             FILL[3] if vurgu else FILL[0],
             ACCENT if vurgu else EDGE[0], fs=8.6, bold=vurgu)
    ax.text(0.2, 4.95, "WHERE ucus_id = 5 AND zaman_sn BETWEEN 300 AND "
            "900: bitişik aralık, tek yerde başlar", fontsize=9.5,
            color=ACCENT)
    ax.text(0.2, 3.6, "WHERE zaman_sn = 600: ucus_id sınırlanmadığı için "
            "aranan değerler dağınık", fontsize=9.5, color=ACCENT_L)
    for i, (u, z) in enumerate(girdiler):
        x = 0.2 + i * (w + g)
        vurgu = z == 600
        _box(ax, x, 2.2, w, 0.9, "(%d, %d)" % (u, z),
             FILL[4] if vurgu else FILL[0],
             ACCENT_L if vurgu else EDGE[0], fs=8.6, bold=vurgu)
    ax.text(0.2, 1.1, "Sonuç: ilk sütun olmadan dizinin tamamı taranır. "
            "En sol önek kuralı, sütun sırasını belirler.",
            fontsize=9.3, color=INK)
    return _save(fig, _yol("bilesik_indeks"))


# 7. İndeks öncesi / sonrası medyan süreler (CSV) ---------------------- #
INDEKS_AD = {
    "telemetri_ucus_zaman": "telemetri: ucus_id, zaman_sn",
    "gorev_ucak_durum": "görev: ucak_id, durum",
    "gorev_ucak_tarih": "görev: ucak_id, baslangic",
}
INDEKS_IX = {
    "yok": "indeks yok",
    "ix_tel_uz": "(ucus_id, zaman_sn)",
    "ix_g_ud": "(ucak_id, durum)",
    "ix_g_ub": "(ucak_id, baslangic)",
    "ix_g_bu": "(baslangic, ucak_id): yanlış sıra",
}


def indeks_olcum():
    satirlar = _oku_csv("b34_indeks_olcum.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    etiket, degerler, renkler = [], [], []
    for s in satirlar:
        etiket.append("%s\n%s" % (INDEKS_AD[s["sorgu"]],
                                  INDEKS_IX[s["indeks"]]))
        degerler.append(float(s["medyan_ms"]))
        renkler.append(ACCENT if s["indeks"] == "yok" else ACCENT_L)
    y = list(range(len(etiket)))
    ax.barh(y, degerler, color=renkler, height=0.62)
    ax.set_xscale("log")
    ax.set_xlim(0.02, 60)
    ax.set_yticks(y)
    ax.set_yticklabels(etiket, fontsize=8.3)
    ax.invert_yaxis()
    for i, v in enumerate(degerler):
        ax.text(v * 1.1, i, ("%.3f ms" % v).replace(".", ","),
                va="center", fontsize=8.5, color=INK)
    ax.set_xlabel("medyan süre (ms, logaritmik ölçek)", color=MUTED)
    for kenar in ("top", "right"):
        ax.spines[kenar].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("indeks_olcum"))


# 8. Yazma: autocommit / tek işlem ve indeks sayısı (CSV) ------------- #
def yazma_olcum():
    satirlar = _oku_csv("b34_yazma_olcum.csv")
    oto = [r for r in satirlar if r["kip"] == "otomatik"][0]
    tek = [r for r in satirlar if r["kip"] == "tek_islem"
           and r["senaryo"].startswith("ekle")][0]
    idx = [r for r in satirlar if r["senaryo"].startswith("100k")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                 gridspec_kw={"width_ratios": [1, 1.5]})
    v1 = [float(oto["medyan_ms"]), float(tek["medyan_ms"])]
    a1.bar([0, 1], v1, color=[ACCENT, ACCENT_L], width=0.55)
    a1.set_yscale("log")
    a1.set_xticks([0, 1])
    a1.set_xticklabels(["her satır\nayrı işlem", "tek işlem"], fontsize=9)
    for i, v in enumerate(v1):
        a1.text(i, v * 1.12, ("%.1f ms" % v).replace(".", ","),
                ha="center", fontsize=9, color=INK)
    a1.set_title("1000 satır ekleme", fontsize=10.5, color=ACCENT)
    a1.set_ylabel("medyan süre (ms, log)", color=MUTED)
    v2 = [float(r["medyan_ms"]) for r in idx]
    a2.bar(range(len(v2)), v2, color=[ACCENT_L] * len(v2), width=0.6)
    a2.set_xticks(range(len(v2)))
    a2.set_xticklabels(["%d indeks" % i for i in range(len(v2))], fontsize=9)
    for i, v in enumerate(v2):
        a2.text(i, v + 5, ("%.0f ms" % v), ha="center", fontsize=9,
                color=INK)
    a2.set_title("100 000 satır, tek işlem: indeks sayısı", fontsize=10.5,
                 color=ACCENT)
    a2.set_ylim(0, max(v2) * 1.18)
    for a in (a1, a2):
        for kenar in ("top", "right"):
            a.spines[kenar].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("yazma_olcum"))


# 9. N+1 karşılaştırması (CSV) ----------------------------------------- #
def n1_olcum():
    satirlar = _oku_csv("b34_n1_olcum.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.3), sharey=True)
    gruplar = [
        (a1, "Ham sqlite3", [
            ("ham_dongu_n1", "döngüde sorgu (N+1)", ACCENT),
            ("ham_tek_join", "tek sorgu (GROUP BY)", ACCENT_L)]),
        (a2, "SQLAlchemy ORM", [
            ("orm_tembel_n1", "tembel yükleme (N+1)", EDGE[3]),
            ("orm_skaler_n1", "döngüde skaler sorgu", EDGE[2]),
            ("orm_selectinload", "selectinload (2 sorgu)", EDGE[1]),
            ("orm_skaler_tek", "tek skaler GROUP BY", EDGE[0])]),
    ]
    for ax, baslik, cizgiler in gruplar:
        for yontem, etk, renk in cizgiler:
            xs = [int(r["ucak_sayisi"]) for r in satirlar
                  if r["yontem"] == yontem]
            ys = [float(r["medyan_ms"]) for r in satirlar
                  if r["yontem"] == yontem]
            ax.plot(xs, ys, marker="o", color=renk, lw=1.6, label=etk)
        ax.set_title(baslik, fontsize=10.5, color=ACCENT)
        ax.set_xlabel("uçak sayısı (N)", color=MUTED)
        ax.set_xticks([10, 30, 60])
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, frameon=False, loc="upper left")
        for kenar in ("top", "right"):
            ax.spines[kenar].set_visible(False)
    a1.set_ylabel("medyan süre (ms)", color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("n1_olcum"))


# 10. Kayıp güncelleme zaman çizelgesi -------------------------------- #
def _adim(ax, x, y, metin, renk, fill, w=3.9):
    _box(ax, x - w / 2, y, w, 1.05, metin, fill, renk, fs=8.6,
         tcol=INK)


def kayip_guncelleme():
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.0))
    for ax in axes:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
        ax.text(2.5, 9.2, "A", ha="center", fontsize=11, weight="bold",
                color=EDGE[0])
        ax.text(7.5, 9.2, "B", ha="center", fontsize=11, weight="bold",
                color=EDGE[1])
        ax.plot([0.5, 0.5], [0.5, 8.7], color=MUTED, lw=1.0)
        ax.text(0.5, 0.2, "zaman", fontsize=8, color=MUTED, ha="left")
    a, b = axes
    a.set_title("kilitsiz: kayıp güncelleme", fontsize=10.5,
                color=ACCENT, pad=2)
    _adim(a, 2.5, 7.4, "oku: değer = 100", EDGE[0], FILL[0])
    _adim(a, 7.5, 6.0, "oku: değer = 100", EDGE[1], FILL[1])
    _adim(a, 2.5, 4.6, "yaz: 100 + 10 = 110", EDGE[0], FILL[0])
    _adim(a, 7.5, 3.2, "yaz: 100 + 5 = 105\n(A'nın +10'u silindi)",
          ACCENT, FILL[3])
    a.text(5, 1.5, "son değer: 105, beklenen: 115", ha="center",
           fontsize=9, color=ACCENT, weight="bold")
    b.set_title("iyimser kilit: sürüm sütunu", fontsize=10.5,
                color=ACCENT, pad=2)
    _adim(b, 2.5, 7.4, "oku: (100, sürüm 0)", EDGE[0], FILL[0])
    _adim(b, 7.5, 6.0, "oku: (100, sürüm 0)", EDGE[1], FILL[1])
    _adim(b, 2.5, 4.6, "yaz WHERE sürüm=0\nsatır = 1 (sürüm 1)", EDGE[0],
          FILL[0])
    _adim(b, 7.5, 3.2, "yaz WHERE sürüm=0\nsatır = 0: çakışma", ACCENT,
          FILL[3])
    _adim(b, 7.5, 1.8, "yeniden oku: (110, 1)\nyaz: satır = 1",
          EDGE[1], FILL[1])
    b.text(5, 0.5, "son değer: 115, sürüm 2", ha="center", fontsize=9,
           color=EDGE[1], weight="bold")
    fig.subplots_adjust(wspace=0.08)
    return _save(fig, _yol("kayip_guncelleme"))


if __name__ == "__main__":
    yollar = [yurutme_sirasi(), join_turleri(), null_mantik(),
              ozyinelemeli_cte(), pencere_cercevesi(), bilesik_indeks(),
              indeks_olcum(), yazma_olcum(), n1_olcum(),
              kayip_guncelleme()]
    for y in yollar:
        print(y)
