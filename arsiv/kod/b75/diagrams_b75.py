# -*- coding: utf-8 -*-
"""Bolum 75 sekilleri: roofline, bit takasi, seyreklik-dogruluk, budama
hizi, damitma semasi ve sonucu, BatchNorm katlama, dagitim hatti, mimari
karsilastirma. Olcum verisi engine/veri/b75_*.csv'den okunur."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import csv
import os
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOR = os.path.join(ROOT, "gorseller")
VERI = os.path.join(HERE, "veri")


def oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tuval(ax, xl=(0, 10), yl=(0, 6)):
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.axis("off")


def stil(ax):
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=RULE, lw=0.6)
    ax.set_axisbelow(True)


# --------------------------------------------------------------- Sekil 75.1
def roofline(yol):
    veri = oku_csv("b75_roofline.csv")
    tepe, bant = 178.8, 25.1          # olculen: GEMM ve kopya testi (son kosu)
    ai = np.logspace(-1, 3, 300)
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    stil(ax)
    ax.loglog(ai, np.minimum(tepe, bant * ai), color=ACCENT, lw=2.2,
              label="tavan: min(tepe, bant x AI)")
    ax.axhline(tepe, color=MUTED, ls="--", lw=1)
    ax.text(0.12, tepe * 1.08, "olculen tepe: %.0f GFLOP/s" % tepe,
            fontsize=9, color=MUTED)
    x = [float(r["ai"]) for r in veri]
    y = [float(r["gflops"]) for r in veri]
    ax.scatter(x, y, s=46, color=EDGE[1], zorder=5,
               label="olculen (2048x2048 Linear)")
    for r in veri:
        ax.annotate("B=%s" % r["B"], (float(r["ai"]), float(r["gflops"])),
                    textcoords="offset points", xytext=(6, -12),
                    fontsize=8.5, color=INK)
    ax.set_xlabel("Aritmetik yogunluk (FLOP/bayt)", color=INK)
    ax.set_ylabel("Performans (GFLOP/s)", color=INK)
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    return _save(fig, yol)


# --------------------------------------------------------------- Sekil 75.2
def bit_takas(yol):
    veri = oku_csv("b75_bit_dogruluk.csv")
    def grup(ad):
        s = [r for r in veri if r["yontem"] == ad]
        d = np.array([float(r["dogruluk"]) for r in s])
        return d.mean(), d.std()
    seri = [("PTQ (kanal basina)", ["PTQ_w4_kanal", "PTQ_w3_kanal",
                                    "PTQ_w2_kanal"], ACCENT, "o-"),
            ("QAT (sahte kuantizasyon)", ["QAT_w4_kanal", "QAT_w3_kanal",
                                          "QAT_w2_kanal"], EDGE[1], "s-")]
    bitler = [4, 3, 2]
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    stil(ax)
    fp = grup("fp32")[0]
    ax.axhline(fp, color=MUTED, ls="--", lw=1)
    ax.text(2.05, fp + 0.004, "fp32: %.3f" % fp, fontsize=9, color=MUTED)
    for ad, anah, renk, bic in seri:
        m = [grup(a)[0] for a in anah]
        s = [grup(a)[1] for a in anah]
        ax.errorbar(bitler, m, yerr=s, fmt=bic, color=renk, capsize=4,
                    lw=2, ms=7, label=ad)
    ax.set_xticks(bitler)
    ax.set_xlabel("Agirlik bit genisligi (aktivasyon fp32)", color=INK)
    ax.set_ylabel("Test dogrulugu (3 tohum)", color=INK)
    ax.set_ylim(0.6, 1.0)
    ax.invert_xaxis()
    ax.legend(loc="lower left", fontsize=9, frameon=False)
    return _save(fig, yol)


# --------------------------------------------------------------- Sekil 75.3
def seyreklik(yol):
    veri = oku_csv("b75_seyreklik.csv")
    oranlar = sorted(set(float(r["oran"]) for r in veri))
    def ort(alan):
        return [np.mean([float(r[alan]) for r in veri
                         if float(r["oran"]) == o]) for o in oranlar]
    def sd(alan):
        return [np.std([float(r[alan]) for r in veri
                        if float(r["oran"]) == o]) for o in oranlar]
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    stil(ax)
    x = np.array(oranlar) * 100
    ax.errorbar(x, ort("budamasiz"), yerr=sd("budamasiz"), fmt="o-",
                color=MUTED, capsize=4, lw=2, label="budama sonrasi (ince ayar yok)")
    ax.errorbar(x, ort("ince_ayar"), yerr=sd("ince_ayar"), fmt="s-",
                color=ACCENT, capsize=4, lw=2, label="ince ayarli (20 epoch, lr 1e-3)")
    ax.set_xlabel("Seyreklik (%) - dogrusal katmanlardaki sifir orani", color=INK)
    ax.set_ylabel("Test dogrulugu", color=INK)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower left", fontsize=9, frameon=False)
    return _save(fig, yol)


# --------------------------------------------------------------- Sekil 75.4
def budama_hiz(yol):
    veri = oku_csv("b75_hiz.csv")
    ad = [r["yontem"] for r in veri]
    med = [float(r["medyan_ms"]) for r in veri]
    p95 = [float(r["p95_ms"]) for r in veri]
    renk = []
    for a in ad:
        if "kanal" in a:
            renk.append(EDGE[1])
        elif "csr" in a:
            renk.append(ACCENT)
        elif "yogun" in a and "yapilandirilmamis" not in a:
            renk.append(MUTED)
        else:
            renk.append(EDGE[2])
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    stil(ax)
    y = np.arange(len(ad))
    ax.barh(y, med, color=renk, height=0.6, edgecolor="white")
    ax.errorbar(med, y, xerr=[np.zeros(len(y)), np.maximum(
        np.array(p95) - np.array(med), 0)], fmt="none", ecolor=INK, capsize=3, lw=0.8)
    ax.set_yticks(y)
    etiket = {"yogun_fp32": "yogun fp32",
              "yapilandirilmis_kanal_50": "kanal budama %50 (yogun)"}
    for a in ad:
        if a.startswith("yapilandirilmamis"):
            p = a.split("_")
            etiket[a] = "budama %%%s, %s" % (p[1], "yogun" if p[2] == "yogun"
                                             else "CSR (seyrek)")
    ax.set_yticklabels([etiket[a] for a in ad], fontsize=8.5, color=INK)
    ax.invert_yaxis()
    for i, v in enumerate(med):
        ax.text(v + 0.03, i, "%.2f ms" % v, va="center", fontsize=8.5, color=INK)
    ax.set_xlabel("Gecikme, medyan (ms), batch=1, 2048 gizli noron", color=INK)
    ax.set_xlim(0, max(med) * 1.25)
    return _save(fig, yol)


# ------------------------------------------------------------ Sekil 75.5/75.6
def damit_semasi(yol):
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    tuval(ax, (0, 14), (0, 6))
    _box(ax, 0.4, 3.9, 3.6, 1.4, "Ogretmen\n512-512 gizli\n301 066 parametre",
         FILL[1], EDGE[1], fs=10, bold=True)
    _box(ax, 0.4, 0.8, 3.6, 1.4, "Egitim verisi\n(gercek etiketler y)",
         FILL[0], EDGE[0], fs=10)
    _box(ax, 5.2, 3.9, 3.6, 1.4, "Yumusak hedef\nsoftmax(z_t / T)",
         FILL[2], EDGE[2], fs=10)
    _box(ax, 5.2, 0.8, 3.6, 1.4, "Sert hedef\ny (one-hot)",
         FILL[0], EDGE[0], fs=10)
    _box(ax, 10.0, 2.3, 3.6, 1.8, "Ogrenci\n32 gizli noron\n2 410 parametre",
         FILL[3], EDGE[3], fs=10, bold=True)
    _arrow(ax, 4.0, 4.6, 5.2, 4.6)
    _arrow(ax, 4.0, 1.5, 5.2, 1.5)
    _arrow(ax, 8.8, 4.6, 10.0, 3.6, rad=-0.15)
    _arrow(ax, 8.8, 1.5, 10.0, 2.6, rad=0.15)
    ax.text(7.0, 5.7, "L = (1 - a) CE(y, s) + a T^2 KL(p_t^T || p_s^T)",
            ha="center", fontsize=10, color=INK, family="DejaVu Sans Mono")
    return _save(fig, yol)


def damit_sonuc(yol):
    veri = oku_csv("b75_damitma.csv")
    sira = ["ogretmen_512_512", "ogrenci_sifirdan", "ogrenci_damitma_T2",
            "ogrenci_damitma_T4", "ogrenci_damitma_T8"]
    etiket = ["ogretmen\n301k", "sifirdan\n2,4k", "damitma\nT=2",
              "damitma\nT=4", "damitma\nT=8"]
    m, s = [], []
    for a in sira:
        d = np.array([float(r["dogruluk"]) for r in veri if r["yontem"] == a])
        m.append(d.mean()); s.append(d.std())
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    stil(ax)
    renk = [MUTED, EDGE[2], ACCENT, ACCENT, ACCENT]
    ax.bar(range(len(sira)), m, yerr=s, color=renk, capsize=4, width=0.6)
    for i, v in enumerate(m):
        ax.text(i, v + 0.012, "%.3f" % v, ha="center", fontsize=9, color=INK)
    ax.set_xticks(range(len(sira)))
    ax.set_xticklabels(etiket, fontsize=9, color=INK)
    ax.set_ylim(0.9, 1.0)
    ax.set_ylabel("Test dogrulugu (3 tohum)", color=INK)
    return _save(fig, yol)


# --------------------------------------------------------------- Sekil 75.7
def bn_katlama(yol):
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    tuval(ax, (0, 14), (0, 5))
    _box(ax, 0.3, 1.6, 2.8, 1.8, "Girdi x\n1 x 8 x 8", FILL[0], EDGE[0], fs=10)
    _box(ax, 3.6, 1.6, 3.0, 1.8, "Conv2d\nW, b", FILL[1], EDGE[1], fs=10)
    _box(ax, 7.1, 1.6, 3.0, 1.8, "BatchNorm\ngamma, beta,\nmu, var", FILL[2], EDGE[2], fs=9.5)
    _box(ax, 10.6, 1.6, 3.1, 1.8, "ReLU", FILL[3], EDGE[3], fs=10)
    _arrow(ax, 3.1, 2.5, 3.6, 2.5); _arrow(ax, 6.6, 2.5, 7.1, 2.5); _arrow(ax, 10.1, 2.5, 10.6, 2.5)
    ax.text(7.0, 0.5, "s = gamma / sqrt(var + eps)   W' = W s   b' = (b - mu) s + beta",
            ha="center", fontsize=9.5, color=INK, family="DejaVu Sans Mono")
    ax.text(7.0, 4.2, "katlama: BatchNorm'u agirliklara gom, tek Conv2d kalsin",
            ha="center", fontsize=10.5, color=ACCENT, weight="bold")
    return _save(fig, yol)


# --------------------------------------------------------------- Sekil 75.8
def dagitim_hatti(yol):
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    tuval(ax, (0, 14), (0, 5))
    kutular = [("PyTorch\neğitim", FILL[0], EDGE[0]),
               ("ONNX\nvarlık", FILL[1], EDGE[1]),
               ("Çalışma zamanı\nORT / TensorRT", FILL[2], EDGE[2]),
               ("Cihaz\nCPU / GPU / MCU", FILL[3], EDGE[3])]
    for i, (t, f, e) in enumerate(kutular):
        _box(ax, 0.4 + i * 3.5, 1.5, 2.6, 1.9, t, f, e, fs=10, bold=True)
        if i < 3:
            _arrow(ax, 3.0 + i * 3.5, 2.45, 3.9 + i * 3.5, 2.45)
    ax.text(2.4, 0.7, "dışa aktarma\n(opset 17)", ha="center", fontsize=8.5, color=MUTED)
    ax.text(5.9, 0.7, "graf optimizasyonu\n+ nicemleme", ha="center", fontsize=8.5, color=MUTED)
    ax.text(9.4, 0.7, "donanıma özgü\nderleme", ha="center", fontsize=8.5, color=MUTED)
    ax.text(7.0, 4.4, "Dağıtım hattı: her adım bir dönüşüm ve bir doğrulama noktasıdır",
            ha="center", fontsize=10.5, color=ACCENT, weight="bold")
    return _save(fig, yol)


# --------------------------------------------------------------- Sekil 75.9
def mimari(yol):
    veri = oku_csv("b75_mimari.csv")
    ad = [r["model"] for r in veri]
    par = np.array([float(r["parametre"]) for r in veri])
    mac = np.array([float(r["mac"]) for r in veri])
    lat = np.array([float(r["medyan_ms"]) for r in veri])
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.9))
    for ax, deger, bas, etiket in [
            (axs[0], par, "Parametre", "parametre (log)"),
            (axs[1], mac, "MAC", "MAC (log)"),
            (axs[2], lat, "Gecikme", "medyan gecikme, ms (log)")]:
        stil(ax)
        ax.barh(range(len(ad)), deger, color=[EDGE[i % 5] for i in range(len(ad))],
                height=0.6)
        ax.set_xscale("log")
        ax.set_yticks(range(len(ad)))
        ax.set_yticklabels(ad if ax is axs[0] else [""] * len(ad), fontsize=8.5, color=INK)
        ax.invert_yaxis()
        ax.set_title(bas, fontsize=10, color=INK)
        ax.set_xlabel(etiket, fontsize=8.5, color=INK)
    fig.tight_layout()
    return _save(fig, yol)


if __name__ == "__main__":
    os.makedirs(GOR, exist_ok=True)
    roofline(os.path.join(GOR, "b75_roofline.png"))
    bit_takas(os.path.join(GOR, "b75_bit_takas.png"))
    seyreklik(os.path.join(GOR, "b75_seyreklik.png"))
    budama_hiz(os.path.join(GOR, "b75_budama_hiz.png"))
    damit_semasi(os.path.join(GOR, "b75_damitma_semasi.png"))
    damit_sonuc(os.path.join(GOR, "b75_damitma_sonuc.png"))
    bn_katlama(os.path.join(GOR, "b75_bn_katlama.png"))
    dagitim_hatti(os.path.join(GOR, "b75_dagitim_hatti.png"))
    mimari(os.path.join(GOR, "b75_mimari.png"))
    print("9 sekil uretildi.")
