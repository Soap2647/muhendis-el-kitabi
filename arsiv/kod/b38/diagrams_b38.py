# -*- coding: utf-8 -*-
"""Bölüm 38 - 'Git Derinlemesine' diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV dosyalarını okur:
  b38_delta_zincir.csv  paket içindeki delta zinciri uzunlukları
  b38_paket.csv         gevşek nesne ve paket boyutları
  b38_bisect.csv        git bisect run adımlarındaki kalan aday sayısı
Diğer şekiller bölümdeki deneme depolarının gerçek çıktılarından çizilir.
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
    return os.path.join(OUT, "b38_%s.png" % ad)


def _tuval(w, h, xl=14, yl=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. Nesne modeli: commit -> tree -> blob ---------------------------- #
def nesne_modeli():
    fig, ax = _tuval(9.8, 6.0, xl=14, yl=9)
    ax.text(2.4, 8.55, "commit", ha="center", fontsize=10,
            weight="bold", color=INK)
    ax.text(7.0, 8.55, "tree (dizin)", ha="center", fontsize=10,
            weight="bold", color=INK)
    ax.text(11.6, 8.55, "blob (dosya içeriği)", ha="center",
            fontsize=10, weight="bold", color=INK)
    _box(ax, 0.3, 5.6, 4.2, 2.2,
         "commit a959406…\nağaç: 7df8cc…\nebeveyn: dda4f8…\n"
         "mesaj: kup eklendi", FILL[0], EDGE[0], fs=8.6)
    _box(ax, 0.3, 1.6, 4.2, 2.2,
         "commit dda4f8…\nağaç: d9311b…\nebeveyn: yok\n"
         "mesaj: ilk sürüm", FILL[0], EDGE[0], fs=8.6)
    _box(ax, 5.0, 5.6, 4.0, 2.2,
         "100644 blob 792c31  mat.c\n100644 blob 30c115  mat.h",
         FILL[1], EDGE[1], fs=8.2)
    _box(ax, 5.0, 1.6, 4.0, 2.2,
         "100644 blob 572c16  mat.c\n100644 blob 30c115  mat.h",
         FILL[1], EDGE[1], fs=8.2)
    _box(ax, 9.9, 6.6, 3.8, 1.2, "int kup(int x) {…}\n(yeni mat.c)",
         FILL[2], EDGE[2], fs=8.2)
    _box(ax, 9.9, 3.6, 3.8, 1.2, "int kare(int x);\n(mat.h, ortak)",
         FILL[3], EDGE[3], fs=8.2)
    _box(ax, 9.9, 1.6, 3.8, 1.2, "int kare(int x) {…}\n(eski mat.c)",
         FILL[2], EDGE[2], fs=8.2)
    _arrow(ax, 2.4, 5.6, 2.4, 3.8, col=ACCENT, lw=1.4)
    ax.text(2.6, 4.7, "ebeveyn", fontsize=8, color=MUTED)
    _arrow(ax, 4.5, 6.7, 5.0, 6.7, col=ACCENT_L, lw=1.2)
    _arrow(ax, 4.5, 2.7, 5.0, 2.7, col=ACCENT_L, lw=1.2)
    _arrow(ax, 9.0, 6.9, 9.9, 7.2, col=ACCENT_L, lw=1.2)
    _arrow(ax, 9.0, 6.0, 9.9, 4.4, col=ACCENT_L, lw=1.2)
    _arrow(ax, 9.0, 2.6, 9.9, 2.2, col=ACCENT_L, lw=1.2)
    _arrow(ax, 9.0, 2.2, 9.9, 4.0, col=ACCENT_L, lw=1.2)
    ax.text(0.3, 0.7, "Aynı mat.h içeriği iki commit'te tek bir blob "
            "olarak saklanır.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("nesne_modeli"))


# 2. Referanslar: dal, HEAD, ayrık HEAD ------------------------------ #
def referanslar():
    fig, ax = _tuval(9.8, 4.6, xl=14, yl=7)
    _box(ax, 0.3, 4.0, 2.8, 1.2, "HEAD\nref: refs/heads/main",
         FILL[4], EDGE[4], fs=8.6)
    _box(ax, 4.0, 4.0, 3.6, 1.2, "refs/heads/main\n(dosya ya da packed-refs)",
         FILL[0], EDGE[0], fs=8.4)
    _box(ax, 9.2, 4.0, 4.4, 1.2, "commit a959406\n\"kup eklendi\"",
         FILL[1], EDGE[1], fs=8.6)
    _arrow(ax, 3.1, 4.6, 4.0, 4.6, col=ACCENT, lw=1.4)
    _arrow(ax, 7.6, 4.6, 9.2, 4.6, col=ACCENT, lw=1.4)
    _box(ax, 0.3, 1.0, 2.8, 1.2, "HEAD (ayrık)\n8834243",
         FILL[2], EDGE[2], fs=8.6)
    _box(ax, 9.2, 1.0, 4.4, 1.2, "commit 8834243\n\"a ikinci\"",
         FILL[1], EDGE[1], fs=8.6)
    _arrow(ax, 3.1, 1.6, 9.2, 1.6, col=MUTED, lw=1.1)
    ax.text(5.6, 2.0, "dal adı yok: HEAD doğrudan commit'e işaret eder",
            fontsize=8.2, color=MUTED, ha="center")
    ax.text(5.6, 0.45, "yeni commit'ler bu noktadan ayrılırsa dal\n"
            "ismi olmadığı için yalnızca reflog'da kalır",
            fontsize=8.2, color=MUTED, ha="center")
    ax.text(0.3, 6.3, "Dal = commit'e işaret eden bir dosya. "
            "HEAD = 'şu an neredeyim' işaretçisi.",
            fontsize=8.8, color=INK)
    return _save(fig, _yol("referanslar"))


# 3. Üç ağaç: HEAD, indeks, çalışma dizini --------------------------- #
def uc_agac():
    fig, ax = _tuval(9.8, 4.8, xl=14, yl=7.2)
    kutular = [(0.4, "HEAD (son commit)", "a.txt = v2", FILL[0], EDGE[0]),
               (5.1, "İndeks (sahne)", "a.txt = v3", FILL[1], EDGE[1]),
               (9.8, "Çalışma dizini", "a.txt = v4", FILL[2], EDGE[2])]
    for x, baslik, icerik, fil, edg in kutular:
        _box(ax, x, 3.4, 3.8, 2.0, baslik + "\n" + icerik, fil, edg,
             fs=9.2)
    _arrow(ax, 9.8, 4.4, 8.9, 4.4, col=ACCENT, lw=1.5)
    ax.text(9.35, 5.0, "git add", fontsize=8.6, color=ACCENT,
            ha="center")
    _arrow(ax, 5.1, 4.4, 4.2, 4.4, col=ACCENT, lw=1.5)
    ax.text(4.65, 5.0, "git commit", fontsize=8.6, color=ACCENT,
            ha="center")
    _arrow(ax, 4.2, 3.9, 5.1, 3.9, col=MUTED, lw=1.0)
    ax.text(4.65, 2.85, "git restore --staged", fontsize=7.6,
            color=MUTED, ha="center")
    _arrow(ax, 8.9, 3.9, 9.8, 3.9, col=MUTED, lw=1.0)
    ax.text(9.35, 2.85, "git restore", fontsize=7.6, color=MUTED,
            ha="center")
    ax.text(0.4, 6.4, "Üç ağaç modeli: git her komutu bu üç yer "
            "arasındaki kopyalama olarak görür.",
            fontsize=8.8, color=INK)
    ax.text(0.4, 1.4, "git status, iki karşılaştırmadır: HEAD ↔ indeks "
            "(staged) ve indeks ↔ çalışma dizini (unstaged).",
            fontsize=8.4, color=MUTED)
    return _save(fig, _yol("uc_agac"))


# 4. reset türleri: hangi katman değişir? ---------------------------- #
def reset_tablo():
    fig, ax = _tuval(9.8, 4.4, xl=14, yl=7)
    basliklar = ["Komut", "HEAD", "İndeks", "Çalışma dizini"]
    xs = [0.3, 3.5, 6.6, 9.7]
    gen = [3.1, 3.1, 3.1, 3.4]
    for x, b in zip(xs, basliklar):
        ax.text(x + 1.2, 6.2, b, ha="center", fontsize=9.4,
                weight="bold", color=INK)
    satirlar = [
        ("reset --soft", ("v2 → v1", True), ("v3 (korundu)", False),
         ("v4 (korundu)", False)),
        ("reset --mixed", ("v2 → v1", True), ("v3 → v1", True),
         ("v4 (korundu)", False)),
        ("reset --hard", ("v2 → v1", True), ("v3 → v1", True),
         ("v4 → v1", True)),
    ]
    y = 4.5
    for komut, *hucreler in satirlar:
        _box(ax, xs[0], y, 2.8, 1.0, komut, FILL[4], EDGE[4], fs=9.4,
             bold=True)
        for j, (metin, degisti) in enumerate(hucreler):
            fil = FILL[3] if degisti else FILL[1]
            edg = ACCENT if degisti else EDGE[1]
            _box(ax, xs[j + 1], y, 2.9 if j < 2 else 3.0, 1.0, metin,
                 fil, edg, fs=8.8)
        y -= 1.4
    ax.text(0.3, 0.6, "Kırmızımsı kutu: o komutla değişen katman. "
            "Değerler, Bölüm 38'deki deneme deposunun gerçek çıktısıdır.",
            fontsize=8.2, color=MUTED)
    return _save(fig, _yol("reset_tablo"))


# 5. Hızlı ileri ve üç yollu birleştirme ----------------------------- #
def birlestirme():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 4.2))
    for ax in (a1, a2):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 6.2)
        ax.axis("off")
    a1.text(0.2, 5.9, "Hızlı ileri (fast-forward)", fontsize=9.4,
            weight="bold", color=INK)
    _box(a1, 0.3, 2.6, 1.7, 0.9, "taban", FILL[0], EDGE[0], fs=8.6)
    _box(a1, 2.8, 2.6, 1.9, 0.9, "ozellik-a", FILL[1], EDGE[1], fs=8.4)
    _box(a1, 5.2, 2.6, 1.6, 0.9, "main", FILL[2], EDGE[2], fs=8.6)
    _arrow(a1, 2.0, 3.05, 2.8, 3.05, col=ACCENT, lw=1.3)
    _arrow(a1, 4.7, 3.05, 5.2, 3.05, col=ACCENT, lw=1.3)
    a1.text(0.3, 1.5, "main, ozellik-a'nın ucuna kayar.\n"
            "Yeni birleşme commit'i yok.", fontsize=8.2, color=MUTED)

    a2.text(0.2, 5.9, "Üç yollu birleştirme", fontsize=9.4,
            weight="bold", color=INK)
    _box(a2, 0.2, 2.6, 1.6, 0.9, "taban", FILL[0], EDGE[0], fs=8.6)
    _box(a2, 2.6, 4.4, 2.0, 0.8, "ozellik-b", FILL[1], EDGE[1], fs=8.4)
    _box(a2, 2.6, 0.9, 2.0, 0.8, "main", FILL[2], EDGE[2], fs=8.6)
    _box(a2, 5.2, 2.6, 1.6, 0.9, "birleşme", FILL[3], EDGE[3], fs=8.2)
    _arrow(a2, 1.8, 3.2, 2.6, 4.6, col=ACCENT, lw=1.2)
    _arrow(a2, 1.8, 3.0, 2.6, 1.3, col=ACCENT, lw=1.2)
    _arrow(a2, 4.6, 4.8, 5.2, 3.5, col=ACCENT_L, lw=1.2)
    _arrow(a2, 4.6, 1.3, 5.2, 2.7, col=ACCENT_L, lw=1.2)
    a2.text(0.2, 0.2, "İki ebeveyn; ortak ata (taban) üç ağaçla\n"
            "karşılaştırılır, farkı olmayan taraf elenir.",
            fontsize=8.2, color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("birlestirme"))


# 6. Rebase öncesi ve sonrası: yeni hash'ler ------------------------- #
def rebase():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 4.6))
    for ax in (a1, a2):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.2)
        ax.axis("off")
    a1.text(0.2, 6.8, "Önce", fontsize=10, weight="bold", color=INK)
    a1.text(0.2, 6.3, "main ve ozellik ayrıldı", fontsize=8.4, color=MUTED)
    _box(a1, 0.3, 1.2, 1.6, 0.8, "2dbfdd9\ntaban", FILL[0], EDGE[0], fs=7.8)
    _box(a1, 2.6, 4.9, 1.6, 0.8, "a8e6331\nmain: m1", FILL[2], EDGE[2], fs=7.8)
    _box(a1, 2.6, 0.7, 1.6, 0.8, "66c602d\nb1", FILL[1], EDGE[1], fs=7.8)
    _box(a1, 2.6, 2.6, 1.6, 0.8, "5652564\nc1", FILL[1], EDGE[1], fs=7.8)
    _box(a1, 4.9, 2.6, 1.6, 0.8, "1851908\nd1", FILL[1], EDGE[1], fs=7.8)
    _arrow(a1, 1.9, 1.6, 2.6, 5.2, col=ACCENT_L, lw=1.2)
    _arrow(a1, 1.9, 1.5, 2.6, 1.1, col=ACCENT, lw=1.2)
    _arrow(a1, 4.2, 1.1, 4.2, 2.6, col=ACCENT, lw=1.0)
    _arrow(a1, 4.2, 3.4, 4.9, 3.0, col=ACCENT, lw=1.0)
    a1.text(0.2, 0.1, "Hash'ler: ozellik ucu 1851908", fontsize=7.8,
            color=MUTED)

    a2.text(0.2, 6.8, "Sonra (rebase main)", fontsize=10, weight="bold",
            color=INK)
    a2.text(0.2, 6.3, "aynı içerik, yeni kimlik", fontsize=8.4,
            color=MUTED)
    _box(a2, 0.3, 1.2, 1.6, 0.8, "2dbfdd9\ntaban", FILL[0], EDGE[0], fs=7.8)
    _box(a2, 2.6, 1.2, 1.6, 0.8, "a8e6331\nmain: m1", FILL[2], EDGE[2], fs=7.8)
    _box(a2, 2.6, 2.6, 1.6, 0.8, "48abce4\nb1'", FILL[3], EDGE[3], fs=7.8)
    _box(a2, 2.6, 4.0, 1.6, 0.8, "4df0447\nc1'", FILL[3], EDGE[3], fs=7.8)
    _box(a2, 2.6, 5.4, 1.6, 0.8, "5928776\nd1'", FILL[3], EDGE[3], fs=7.8)
    _arrow(a2, 1.9, 1.6, 2.6, 1.6, col=ACCENT, lw=1.2)
    _arrow(a2, 3.4, 2.0, 3.4, 2.6, col=ACCENT, lw=1.0)
    _arrow(a2, 3.4, 3.4, 3.4, 4.0, col=ACCENT, lw=1.0)
    _arrow(a2, 3.4, 4.8, 3.4, 5.4, col=ACCENT, lw=1.0)
    a2.text(0.2, 0.1, "Eski commit'ler dal olarak erişilemez;\n"
            "yalnızca reflog'da yaşar.", fontsize=7.8, color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("rebase"))


# 7. Delta zinciri ve paket boyutu (ölçüm verisi) -------------------- #
def delta_zinciri():
    zincir = _oku_csv("b38_delta_zincir.csv")
    paket = _oku_csv("b38_paket.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 4.2),
                                 gridspec_kw={"width_ratios": [2.2, 1]})
    x = [int(r["zincir_uzunlugu"]) for r in zincir]
    y = [int(r["nesne_sayisi"]) for r in zincir]
    a1.bar(x, y, color=FILL[0], edgecolor=EDGE[0], linewidth=0.8)
    a1.set_xlabel("delta derinliği (temel nesneye uzaklık)", fontsize=8.6,
                  color=INK)
    a1.set_ylabel("nesne sayısı", fontsize=8.6, color=INK)
    a1.set_title("Delta nesnelerinin derinlik dağılımı", fontsize=9.4,
                 color=INK)
    a1.tick_params(labelsize=7.8)
    a1.spines["top"].set_visible(False)
    a1.spines["right"].set_visible(False)
    a1.text(0.70, 0.80, "sınır (pack.depth): %d" % max(x),
            transform=a1.transAxes, ha="right", fontsize=8.2,
            color=ACCENT)
    etiket = [r["durum"] for r in paket]
    boyut = [int(r["boyut_kib"]) for r in paket]
    renk = [FILL[3], FILL[1]]
    kenar = [ACCENT, EDGE[1]]
    a2.bar(etiket, boyut, color=renk, edgecolor=kenar, linewidth=0.8)
    for i, v in enumerate(boyut):
        a2.text(i, v + 40, "%d KiB" % v, ha="center", fontsize=8.2,
                color=INK)
    a2.set_title("Gevşek ve paketli", fontsize=9.4, color=INK)
    a2.set_ylabel("boyut (KiB)", fontsize=8.6, color=INK)
    a2.set_ylim(0, max(boyut) * 1.25)
    a2.tick_params(labelsize=7.8)
    a2.spines["top"].set_visible(False)
    a2.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, _yol("delta_zinciri"))


# 8. İş akışı karşılaştırması ---------------------------------------- #
def is_akislari():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 4.6))
    for ax in (a1, a2):
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 7.4)
        ax.axis("off")
    # trunk-based: tek ana çizgi, kısa dallar
    a1.text(0.2, 7.0, "Trunk-based", fontsize=10, weight="bold", color=INK)
    a1.plot([0.4, 6.6], [3.2, 3.2], color=ACCENT, lw=2.2)
    for xi in (1.2, 3.0, 4.8):
        a1.plot([xi, xi + 0.8, xi + 0.8], [3.2, 4.4, 3.2], color=ACCENT_L,
                lw=1.4)
        a1.add_patch(plt.Circle((xi + 0.8, 4.4), 0.09, color=ACCENT_L))
    a1.text(0.4, 2.0, "main'e günde birkaç kez küçük birleşme\n"
            "(saatler içinde). Özellik bayrağı ile yarım iş\n"
            "kullanıcıya kapalı tutulur.", fontsize=8.0, color=MUTED)
    # Git Flow: main, develop, feature, release, hotfix
    a2.text(0.2, 7.0, "Git Flow", fontsize=10, weight="bold", color=INK)
    hatlar = [(6.2, "main"), (4.9, "develop"), (3.6, "release"),
              (2.3, "feature")]
    for yy, ad in hatlar:
        a2.plot([1.3, 6.5], [yy, yy], color=RULE, lw=2.0)
        a2.text(0.1, yy, ad, fontsize=7.6, color=INK, va="center")
    a2.plot([1.3, 3.5], [4.9, 2.3], color=ACCENT_L, lw=1.2)
    a2.plot([3.5, 5.5], [2.3, 4.9], color=ACCENT_L, lw=1.2)
    a2.plot([5.5, 5.5], [4.9, 6.2], color=ACCENT, lw=1.2)
    a2.plot([3.5, 3.5], [3.6, 6.2], color=ACCENT, lw=1.2)
    a2.text(0.4, 0.8, "Her hatanın kendi dalı var; sürüm dalları ve\n"
            "hotfix. Ayrıntılı ama yavaş: sürekli teslimde\n"
            "dallar birikip birleşmeyi zorlaştırır.", fontsize=8.0,
            color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("is_akislari"))


# 9. Bisect ikili arama (ölçüm verisi) -------------------------------- #
def bisect_ikili():
    veri = _oku_csv("b38_bisect.csv")
    adim = [int(r["adim"]) for r in veri]
    kalan = [int(r["kalan_aday"]) for r in veri]
    fig, ax = plt.subplots(figsize=(9.8, 4.0))
    ax.bar(adim, kalan, color=FILL[1], edgecolor=EDGE[1], linewidth=0.8)
    for a, k in zip(adim, kalan):
        ax.text(a, k + 1.2, str(k), ha="center", fontsize=8.6, color=INK)
    ax.set_xlabel("bisect adımı (her adımda bir test koşulur)",
                  fontsize=8.8, color=INK)
    ax.set_ylabel("kalan aday commit sayısı", fontsize=8.8, color=INK)
    ax.set_title("128 commit'lik regresyonda git bisect run ilerlemesi",
                 fontsize=9.6, color=INK)
    ax.set_xticks(adim)
    ax.set_ylim(0, 72)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(6.7, 22, "7. adımda kalan aday 0:\nsuçlu commit belirlendi",
            ha="right", fontsize=8.2, color=ACCENT)
    fig.tight_layout()
    return _save(fig, _yol("bisect_ikili"))


# 10. Hook'ların yaşam döngüsündeki yeri ----------------------------- #
def hook_yasam():
    fig, ax = _tuval(9.8, 4.8, xl=14, yl=7.2)
    kutular = [
        (0.3, 4.9, "git add", FILL[4], EDGE[4]),
        (3.0, 4.9, "pre-commit\n(indeks denetimi)", FILL[2], EDGE[2]),
        (6.0, 4.9, "commit-msg\n(mesaj denetimi)", FILL[2], EDGE[2]),
        (9.0, 4.9, "commit oluştu", FILL[1], EDGE[1]),
        (11.9, 4.9, "post-commit", FILL[4], EDGE[4]),
    ]
    for x, y, metin, fil, edg in kutular:
        _box(ax, x, y, 2.5 if x < 11 else 1.9, 1.3, metin, fil, edg,
             fs=8.4)
    for x1, x2 in [(2.8, 3.0), (5.5, 6.0), (8.5, 9.0), (11.5, 11.9)]:
        _arrow(ax, x1, 5.55, x2, 5.55, col=ACCENT, lw=1.3)
    _box(ax, 0.3, 1.2, 2.5, 1.3, "git push", FILL[4], EDGE[4], fs=8.4)
    _box(ax, 3.4, 1.2, 3.0, 1.3, "pre-push\n(yerel kapı)", FILL[2],
         EDGE[2], fs=8.4)
    _box(ax, 7.6, 1.2, 3.6, 1.3, "uzak sunucu\n(CI ve korumalı dal kuralı)",
         FILL[3], EDGE[3], fs=8.2)
    _arrow(ax, 2.8, 1.85, 3.4, 1.85, col=ACCENT, lw=1.3)
    _arrow(ax, 6.4, 1.85, 7.6, 1.85, col=ACCENT, lw=1.3)
    ax.text(0.4, 3.4, "Yerel hook'lar --no-verify ile atlanabilir.\n"
            "Bu yüzden son savunma sunucu tarafında olmalı.",
            fontsize=8.4, color=MUTED)
    ax.text(0.4, 6.7, "Hook'ların yeri: yerel kontroller commit ve push "
            "arasında, sunucu kontrolleri en sonda.",
            fontsize=8.6, color=INK)
    return _save(fig, _yol("hook_yasam"))


if __name__ == "__main__":
    for f in (nesne_modeli, referanslar, uc_agac, reset_tablo,
              birlestirme, rebase, delta_zinciri, is_akislari,
              bisect_ikili, hook_yasam):
        print(f())
