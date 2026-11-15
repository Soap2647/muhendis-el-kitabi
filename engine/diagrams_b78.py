# -*- coding: utf-8 -*-
"""Bolum 78 - Guvenilir & guvenli AI diyagramlari.

Olcum grafikleri engine/veri/b78_*.csv dosyalarindan okunur; bu CSV'leri
deney betikleri uretir (b78_01 ... b78_08). Kavramsal sekiller veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def boyut_kutusu(ax, x, y, w, h, baslik, alt, renk):
    _box(ax, x, y + h * 0.52, w, h * 0.46, baslik, fill=FILL[renk],
         edge=EDGE[renk], fs=10.5, bold=True)
    ax.text(x + w / 2, y + h * 0.24, alt, ha="center", va="center",
            fontsize=8.6, color=MUTED, wrap=True)


def guvenilir_boyutlar(path):
    """Guvenilir AI'nin yedi boyutu: merkez ve iki grup kutusu."""
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    _box(ax, 2.6, 8.2, 4.8, 1.3, "Güvenilir yapay zekâ", fill=FILL[0],
         edge=ACCENT, fs=12.5, bold=True)
    ust = [("Doğruluk", "test kümesinde ölçülür"),
           ("Sağlamlık", "bozulma ve saldırı altında"),
           ("Kalibrasyon", "güven, doğruluğa uymalı"),
           ("Açıklanabilirlik", "karar gerekçesi denetlenir")]
    alt = [("Adalet", "gruplar arası hata farkı"),
           ("Güvenlik", "zehirleme, saldırı, sızıntı"),
           ("İzlenebilirlik", "veri, sürüm ve denetim izi")]
    ax.text(0.2, 6.55, "Model davranışı", fontsize=9.5, color=INK,
            weight="bold")
    for i, (b, a) in enumerate(ust):
        boyut_kutusu(ax, 0.2 + i * 2.45, 4.6, 2.2, 1.7, b, a, i % 4)
    ax.text(0.2, 3.2, "Toplum ve süreç", fontsize=9.5, color=INK,
            weight="bold")
    for i, (b, a) in enumerate(alt):
        boyut_kutusu(ax, 0.2 + i * 3.3, 0.4, 3.0, 1.7, b, a, (i + 1) % 4)
    return _save(fig, path)


def ood_skor(path):
    """OOD skor dagilimlari (ust uc panel) ve AUROC (alt sag)."""
    sk = oku("b78_ood_skor.csv")
    au = oku("b78_ood_auroc.csv")
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 6.6))
    yontemler = [("MSP", "Maks. softmax"), ("Enerji", "Enerji skoru"),
                 ("Mahalanobis", "Mahalanobis")]
    for k, (ad, baslik) in enumerate(yontemler):
        ax = axs.ravel()[k]
        id_s = [float(r["skor"]) for r in sk
                if r["yontem"] == ad and r["grup"] == "id"]
        oo_s = [float(r["skor"]) for r in sk
                if r["yontem"] == ad and r["grup"] == "ood"]
        ax.hist(id_s, bins=30, alpha=0.7, color=EDGE[0],
                label="gerçek rakam (ID)")
        ax.hist(oo_s, bins=30, alpha=0.7, color=EDGE[3],
                label="sentetik OOD")
        ax.set_title(baslik, fontsize=10.5, color=INK)
        ax.set_xlabel("skor (yüksek = içeride)", fontsize=8.5)
        ax.set_ylabel("örnek sayısı", fontsize=8.5)
        ax.tick_params(labelsize=8)
        ax.legend(fontsize=7.5, frameon=False)
    ax = axs[1, 1]
    isim = ["MSP", "Enerji", "Mahalanobis"]
    ort, sd = [], []
    for ad in isim:
        v = [float(r["auroc"]) for r in au
             if r["yontem"] == ad and r["ood_turu"] == "birlesik"]
        ort.append(np.mean(v))
        sd.append(np.std(v))
    ax.bar(range(3), ort, yerr=sd, color=[FILL[0], FILL[2], FILL[1]],
           edgecolor=[EDGE[0], EDGE[2], EDGE[1]], capsize=4)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["MSP", "Enerji", "Mahal."], fontsize=8.5)
    ax.set_ylim(0.5, 1.02)
    ax.axhline(0.5, color=MUTED, lw=0.8, ls="--")
    ax.set_title("AUROC (3 tohum, ort. ± sd)", fontsize=10.5, color=INK)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return _save(fig, path)


def belirsizlik_kalibrasyon(path):
    """Guvenilirlik diyagrami (sol) ve ECE / epistemik AUROC (sag)."""
    kb = oku("b78_kalibrasyon.csv")
    bl = oku("b78_belirsizlik.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    renk = {"Tek model": EDGE[0], "Sicaklik": EDGE[2],
            "MC dropout": EDGE[3], "Topluluk": EDGE[1]}
    a1.plot([0, 1], [0, 1], color=MUTED, lw=0.9, ls="--")
    for k, (yon, c) in enumerate(renk.items()):
        satirlar = [r for r in kb if r["yontem"] == yon
                    and int(r["sayi"]) >= 5]
        g = [float(r["guven"]) for r in satirlar]
        d = [float(r["dogruluk"]) for r in satirlar]
        n = [int(r["sayi"]) for r in satirlar]
        a1.scatter(np.array(g) + (k - 1.5) * 0.006, d,
                   s=np.array(n) * 0.9, color=c, alpha=0.75,
                   label=yon)
    a1.set_xlabel("ortalama güven (kutu başına, n ≥ 5)", fontsize=8.5)
    a1.set_ylabel("ortalama doğruluk", fontsize=8.5)
    a1.set_title("Güvenilirlik diyagramı (tohum 0)", fontsize=10,
                 color=INK)
    a1.legend(fontsize=7.5, frameon=False, loc="upper left")
    a1.tick_params(labelsize=8)
    yon = list(renk)
    ece = [np.mean([float(r["ece"]) for r in bl if r["yontem"] == y])
           for y in yon]
    ece_sd = [np.std([float(r["ece"]) for r in bl if r["yontem"] == y])
              for y in yon]
    x = np.arange(len(yon))
    a2.bar(x, ece, yerr=ece_sd, color=[renk[y] for y in yon], alpha=0.8,
           capsize=3)
    a2.set_xticks(x)
    a2.set_xticklabels(["Tek", "Sıcaklık", "MC", "Topluluk"],
                       fontsize=8.5)
    a2.set_ylabel("ECE (düşük iyi)", fontsize=8.5)
    a2.set_title("Kalibrasyon hatası, 3 tohum", fontsize=10, color=INK)
    a2.tick_params(labelsize=8)
    fig.tight_layout()
    return _save(fig, path)


def conformal_kapsama(path):
    """Kapsama - nominal (sol) ve kume boyu / tekil oran (sag)."""
    cf = oku("b78_conformal.csv")
    alfalar = sorted({float(r["alfa"]) for r in cf})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    kap, kap_sd, boy, tek = [], [], [], []
    for a in alfalar:
        s = [r for r in cf if float(r["alfa"]) == a]
        k = [float(r["kapsama"]) for r in s]
        kap.append(np.mean(k))
        kap_sd.append(np.std(k))
        boy.append(np.mean([float(r["kume_boyu"]) for r in s]))
        tek.append(np.mean([float(r["tekil_oran"]) for r in s]))
    nom = [1 - a for a in alfalar]
    a1.plot([0.6, 1.0], [0.6, 1.0], color=MUTED, ls="--", lw=0.9)
    a1.errorbar(nom, kap, yerr=kap_sd, fmt="o", color=EDGE[0], capsize=3)
    a1.set_xlabel("nominal kapsama (1 - α)", fontsize=8.5)
    a1.set_ylabel("ölçülen kapsama (test)", fontsize=8.5)
    a1.set_title("Kapsama garantisi", fontsize=10, color=INK)
    a1.tick_params(labelsize=8)
    a2.plot(alfalar, boy, "o-", color=EDGE[3], label="ortalama küme boyu")
    a2.plot(alfalar, tek, "s-", color=EDGE[1], label="tekil küme oranı")
    a2.set_xlabel("α", fontsize=8.5)
    a2.set_title("Küme boyu ve belirsizlik", fontsize=10, color=INK)
    a2.legend(fontsize=7.5, frameon=False)
    a2.tick_params(labelsize=8)
    fig.tight_layout()
    return _save(fig, path)


def risk_kapsam(path):
    """Risk-kapsam egrisi, iki siralama, 3 tohum ortalamasi."""
    rk = oku("b78_riskkapsam.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    for yon, c, ls in [("maks_olasilik", EDGE[0], "-"),
                       ("kume_boyu", EDGE[3], "--")]:
        d = defaultdict(list)
        for r in rk:
            if r["yontem"] == yon:
                d[float(r["kapsam"])].append(float(r["risk"]))
        ks = sorted(d)
        ax.plot(ks, [np.mean(d[k]) for k in ks], ls, color=c, marker="o",
                ms=3.5, lw=1.4, label=yon.replace("_", " "))
    ax.set_xlabel("kapsam (kabul edilen oranı)", fontsize=8.5)
    ax.set_ylabel("risk (kabul edilenlerde hata)", fontsize=8.5)
    ax.invert_xaxis()
    ax.set_title("Risk-kapsam eğrisi (3 tohum ortalaması)", fontsize=10,
                 color=INK)
    ax.legend(fontsize=8, frameon=False)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return _save(fig, path)


def saglamlik(path):
    """Eps'a gore saglam dogruluk (sol); gradyan maskeleme (sag)."""
    sg = oku("b78_saglamlik.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    seri = [("standart", "FGSM", EDGE[3], "--", "standart FGSM"),
            ("standart", "PGD", EDGE[3], "-", "standart PGD"),
            ("PGD-AT", "PGD", EDGE[1], "-", "PGD-AT")]
    for mdl, sal, c, ls, et in seri:
        d = defaultdict(list)
        for r in sg:
            if r["model"] == mdl and r["saldiri"] == sal:
                d[float(r["eps"])].append(float(r["dogruluk"]))
        es = sorted(d)
        m = [np.mean(d[e]) for e in es]
        s = [np.std(d[e]) for e in es]
        a1.errorbar(es, m, yerr=s, fmt="o" + ls, ms=3.2, lw=1.2,
                    color=c, capsize=2, label=et)
    a1.set_xlabel("ε (L∞)", fontsize=8.5)
    a1.set_ylabel("doğruluk", fontsize=8.5)
    a1.set_title("Sağlam doğruluk eğrisi", fontsize=10, color=INK)
    a1.legend(fontsize=7.5, frameon=False)
    a1.tick_params(labelsize=8)
    kat = [("maskeleme_standart", "FGSM", "standart\nFGSM"),
           ("maskeleme_maskeli", "FGSM-naif", "maskeli\nFGSM-naif"),
           ("maskeleme_maskeli", "PGD-naif", "maskeli\nPGD-naif"),
           ("maskeleme_maskeli", "PGD-marj", "maskeli\nPGD-marj")]
    x = np.arange(len(kat))
    for j, e in enumerate([0.05, 0.10]):
        v = []
        for mdl, sal, _ in kat:
            r = [float(q["dogruluk"]) for q in sg if q["model"] == mdl
                 and q["saldiri"] == sal and float(q["eps"]) == e]
            v.append(r[0])
        a2.bar(x + (j - 0.5) * 0.38, v, 0.36,
               color=[FILL[2], FILL[0]][j], edgecolor=EDGE[2 * j],
               label="ε = %.2f" % e)
    a2.set_xticks(x)
    a2.set_xticklabels([k[2] for k in kat], fontsize=7.2)
    a2.set_ylim(0, 1.05)
    a2.set_title("Gradyan maskeleme: sahte güvenlik", fontsize=10,
                 color=INK)
    a2.legend(fontsize=7.5, frameon=False, ncol=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.2))
    a2.tick_params(labelsize=8)
    fig.tight_layout()
    return _save(fig, path)


def ig_izgara(path):
    """4 ornek x 4 yontem: girdi, GxI, IG (sifir taban), IG (gri taban)."""
    ac = oku("b78_aciklama.csv")
    ornekler = []
    for r in ac:
        if r["ornek"] not in ornekler:
            ornekler.append(r["ornek"])
    yontemler = ["girdi", "GxI", "IG_0", "IG_gri"]
    basliklar = ["girdi", "gradyan × girdi", "IG (sıfır taban)",
                 "IG (gri taban)"]
    fig, axs = plt.subplots(4, 4, figsize=(9.6, 9.0))
    for i, o in enumerate(ornekler):
        for j, y in enumerate(yontemler):
            v = np.array([float(r["deger"]) for r in ac
                          if r["ornek"] == o and r["yontem"] == y])
            img = v.reshape(8, 8)
            ax = axs[i, j]
            if y == "girdi":
                ax.imshow(img, cmap="gray_r", vmin=0, vmax=1)
            else:
                m = max(np.abs(img).max(), 1e-9)
                ax.imshow(img, cmap="RdBu_r", vmin=-m, vmax=m)
            ax.set_xticks([])
            ax.set_yticks([])
            if i == 0:
                ax.set_title(basliklar[j], fontsize=8.5, color=INK)
            if j == 0:
                gerc = [r["gercek"] for r in ac if r["ornek"] == o][0]
                ax.set_ylabel("rakam %s" % gerc, fontsize=8.5)
    fig.tight_layout()
    return _save(fig, path)


def ibp_yayilim(path):
    """El ornegi agi: x kutusundan IBP aralik yayilimi (eps = 0.10)."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 0.2, 2.2, 2.2, 1.6, "girdi kutusu\nx1 ∈ [0,5; 0,7]\n"
         "x2 ∈ [0,3; 0,5]", fill=FILL[0], edge=EDGE[0], fs=8.4)
    _box(ax, 3.1, 3.7, 2.4, 1.3, "h1 = x1 − x2\n[0; 0,4]",
         fill=FILL[1], edge=EDGE[1], fs=8.4)
    _box(ax, 3.1, 1.0, 2.4, 1.3, "h2 = 0,5x1 + x2 − 0,2\n[0,35; 0,65]",
         fill=FILL[1], edge=EDGE[1], fs=8.4)
    _box(ax, 6.0, 3.7, 1.8, 1.3, "ReLU\n[0; 0,4]", fill=FILL[2],
         edge=EDGE[2], fs=8.4)
    _box(ax, 6.0, 1.0, 1.8, 1.3, "ReLU\n[0,35; 0,65]", fill=FILL[2],
         edge=EDGE[2], fs=8.4)
    _box(ax, 8.1, 3.1, 1.8, 2.3, "çıktı\nz1 ∈ [0,35; 1,05]\n"
         "z2 ∈ [−0,225; 0,325]", fill=FILL[3], edge=EDGE[3], fs=7.8)
    _arrow(ax, 2.4, 3.2, 3.1, 4.3)
    _arrow(ax, 2.4, 2.6, 3.1, 1.7)
    _arrow(ax, 5.5, 4.3, 6.0, 4.3)
    _arrow(ax, 5.5, 1.7, 6.0, 1.7)
    _arrow(ax, 7.8, 4.3, 8.1, 4.3)
    _arrow(ax, 7.8, 1.7, 8.1, 3.6, rad=0.0)
    ax.text(5.0, 0.25, "Sertifika: alt(z1) = 0,35 > üst(z2) = 0,325 → "
            "ε = 0,10 için doğru sınıf sertifikalı",
            ha="center", fontsize=8.6, color=INK)
    return _save(fig, path)


def calisma_zamani(path):
    """Calisma zamani guvence mimarisi: girdi -> sinir -> kapilar -> karar."""
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    _box(ax, 0.1, 2.9, 1.5, 1.2, "girdi\nkare", fill=FILL[0],
         edge=EDGE[0], fs=8.6)
    _box(ax, 2.0, 2.7, 2.2, 1.6, "hedef sınıflandırıcı\n(5 üyeli topluluk)",
         fill=FILL[1], edge=EDGE[1], fs=8.2)
    _box(ax, 4.9, 4.9, 2.3, 1.1, "OOD kapısı\nMahalanobis ≥ eşik",
         fill=FILL[2], edge=EDGE[2], fs=8.0)
    _box(ax, 4.9, 3.1, 2.3, 1.1, "belirsizlik kapısı\nMI ≤ eşik",
         fill=FILL[2], edge=EDGE[2], fs=8.0)
    _box(ax, 4.9, 1.3, 2.3, 1.1, "conformal kapısı\nküme boyu = 1",
         fill=FILL[2], edge=EDGE[2], fs=8.0)
    _box(ax, 7.9, 3.2, 1.9, 1.5, "hepsi geçtiyse\nKABUL\nsınıf + güven",
         fill=FILL[1], edge=EDGE[1], fs=7.8, bold=False)
    _box(ax, 7.9, 0.5, 1.9, 1.5, "herhangi biri\nREDDET\n→ güvenli dönüş",
         fill=FILL[3], edge=EDGE[3], fs=7.8)
    _arrow(ax, 1.6, 3.5, 2.0, 3.5)
    _arrow(ax, 4.2, 3.9, 4.9, 5.4)
    _arrow(ax, 4.2, 3.5, 4.9, 3.6)
    _arrow(ax, 4.2, 3.2, 4.9, 1.9)
    _arrow(ax, 7.2, 5.4, 7.9, 4.3, rad=-0.2)
    _arrow(ax, 7.2, 3.6, 7.9, 3.9)
    _arrow(ax, 7.2, 1.9, 7.9, 1.3, rad=0.2)
    ax.text(5.0, 0.15, "Her karar denetim izine yazılır (girdi özeti, "
            "skorlar, eşikler, sürüm)", ha="center", fontsize=8.4,
            color=MUTED)
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    print(guvenilir_boyutlar(os.path.join(GORSEL,
                                          "b78_guvenilir_boyutlar.png")))
    print(ood_skor(os.path.join(GORSEL, "b78_ood_skor.png")))
    print(belirsizlik_kalibrasyon(os.path.join(GORSEL,
                                               "b78_belirsizlik.png")))
    print(conformal_kapsama(os.path.join(GORSEL,
                                         "b78_conformal_kapsama.png")))
    print(risk_kapsam(os.path.join(GORSEL, "b78_risk_kapsam.png")))
    print(saglamlik(os.path.join(GORSEL, "b78_saglamlik.png")))
    print(ig_izgara(os.path.join(GORSEL, "b78_ig_izgara.png")))
    print(ibp_yayilim(os.path.join(GORSEL, "b78_ibp_yayilim.png")))
    print(calisma_zamani(os.path.join(GORSEL, "b78_calisma_zamani.png")))
