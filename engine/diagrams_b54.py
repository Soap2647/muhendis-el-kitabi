# -*- coding: utf-8 -*-
"""Bolum 54 - ML'e Giris & Pipeline diyagramlari.

Olcum grafikleri engine/veri/b54_*.csv dosyalarini okur:
  b54_polinom_uyum.csv, b54_polinom_nokta.csv, b54_polinom_hata.csv,
  b54_ogrenme_egrisi.csv, b54_sizinti.csv, b54_baseline.csv
Kavram sekilleri (kural/ogrenme, tur haritasi, bolme, akis) analitik
olarak cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tuval(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    return fig, ax


def kural_vs_ogrenme(path):
    fig, ax = _tuval(9.6, 5.2)
    ax.text(0.2, 9.4, "Kural tabanlı program", fontsize=12, weight="bold",
            color=INK)
    _box(ax, 0.2, 7.0, 2.2, 1.4, "Girdi\n(sensör ölçümü)", FILL[0], EDGE[0])
    _box(ax, 3.2, 6.8, 3.6, 1.8,
         "Elle yazılmış kurallar\nsıcaklık > 85: alarm", FILL[3], EDGE[3])
    _box(ax, 7.6, 7.0, 2.2, 1.4, "Çıktı\nalarm / normal", FILL[1], EDGE[1])
    _arrow(ax, 2.4, 7.7, 3.2, 7.7)
    _arrow(ax, 6.8, 7.7, 7.6, 7.7)
    ax.plot([0.2, 9.8], [5.6, 5.6], color=RULE, lw=1)
    ax.text(0.2, 4.9, "Öğrenilen program", fontsize=12, weight="bold",
            color=INK)
    _box(ax, 0.2, 1.2, 2.2, 2.4, "Veri\n(girdi, etiket)\nçiftleri",
         FILL[2], EDGE[2])
    _box(ax, 3.2, 1.0, 3.6, 2.8,
         "Öğrenme algoritması\nkayıp + optimizasyon\nθ ← θ − η∇L",
         FILL[0], EDGE[0])
    _box(ax, 7.6, 1.2, 2.2, 2.4, "Öğrenilen f_θ\nparametreler θ\n(tahmin)",
         FILL[1], EDGE[1])
    _arrow(ax, 2.4, 2.4, 3.2, 2.4)
    _arrow(ax, 6.8, 2.4, 7.6, 2.4)
    return _save(fig, path)


def ml_turleri(path):
    fig, ax = _tuval(9.6, 5.6)
    _box(ax, 3.2, 8.6, 3.6, 0.9, "Makine öğrenmesi", FILL[0], EDGE[0],
         fs=12, bold=True)
    dallar = [
        ("Denetimli", "etiketli veri",
         "sınıflandırma,\nregresyon\nBölüm 58-60"),
        ("Denetimsiz", "etiketsiz veri", "kümeleme, PCA\nBölüm 61"),
        ("Yarı denetimli", "az etiket, çok\netiketsiz veri",
         "sözde-etiket,\ntutarlılık"),
        ("Öz-denetimli", "etiketi veriden\ntüret",
         "maskeli modelleme,\ncontrastive\nBölüm 73"),
        ("Pekiştirmeli", "ödül sinyali",
         "MDP, Q-öğrenme,\nPPO\nBölüm 74"),
    ]
    for i, (ad, alt, son) in enumerate(dallar):
        x = 0.2 + i * 1.96
        _arrow(ax, 5.0, 8.6, x + 0.88, 7.2, col=MUTED, lw=1.0)
        _box(ax, x, 5.6, 1.76, 1.6, "%s\n%s" % (ad, alt), FILL[i % 5],
             EDGE[i % 5], fs=9.5)
        _box(ax, x, 2.4, 1.76, 2.0, son, "#ffffff", RULE, fs=8.5,
             tcol=INK)
    ax.text(5, 1.5, "Etiket var mı, yok mu, yoksa bir ödül mü var?\n"
            "İlk soru, hangi yöntem ailesinin kullanılacağını belirler.",
            ha="center", fontsize=9, color=MUTED)
    return _save(fig, path)


def polinom_uyum(path):
    uyum = _oku("b54_polinom_uyum.csv")
    nokta = _oku("b54_polinom_nokta.csv")
    x = np.linspace(0, 1, 201)
    fig, eksen = plt.subplots(2, 2, figsize=(9.6, 6.6), sharey=True)
    baslik = {1: "(a) derece 1: eksik uydurma",
              3: "(b) derece 3: dengeli",
              9: "(c) derece 9: aşırı uydurma",
              12: "(d) derece 12: kenarlarda patlama"}
    for ax, d in zip(eksen.flat, (1, 3, 9, 12)):
        ax.plot(x, np.sin(2 * np.pi * x), color=MUTED, ls="--", lw=1.0,
                label="gerçek sin(2πx)")
        satir = [r for r in uyum if int(r["derece"]) == d]
        ax.plot([float(r["x"]) for r in satir],
                [float(r["y"]) for r in satir], color=ACCENT, lw=1.8,
                label="uyum")
        ax.scatter([float(r["x"]) for r in nokta],
                   [float(r["y"]) for r in nokta], s=14, color=INK,
                   zorder=3, label="eğitim (30)")
        ax.set_ylim(-1.8, 1.8)
        ax.set_title(baslik[d], fontsize=10.5)
        ax.grid(color=RULE, lw=0.6)
        ax.set_xlabel("x")
    eksen[0, 0].set_ylabel("y")
    eksen[1, 0].set_ylabel("y")
    eksen[0, 0].legend(fontsize=8, loc="lower left", frameon=False)
    fig.tight_layout()
    return _save(fig, path)


def polinom_hata(path):
    satir = _oku("b54_polinom_hata.csv")
    d = [int(r["derece"]) for r in satir]
    tr = [float(r["egitim_rmse"]) for r in satir]
    va = [float(r["dogrulama_rmse"]) for r in satir]
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.plot(d, tr, "o-", color=ACCENT_L, label="eğitim RMSE")
    ax.plot(d, va, "s-", color=ACCENT, label="doğrulama RMSE")
    en = int(np.argmin(va))
    ax.axvline(d[en], color=MUTED, ls=":", lw=1.2)
    ax.text(d[en] + 0.2, 0.47, "doğrulamada en iyi: %d" % d[en],
            fontsize=9, color=INK)
    ax.text(1.1, 0.02, "eksik uydurma", fontsize=9, color=MUTED)
    ax.text(8.0, 0.02, "aşırı uydurma", fontsize=9, color=MUTED)
    ax.set_xlabel("polinom derecesi")
    ax.set_ylabel("RMSE")
    ax.set_xticks(d)
    ax.set_ylim(0, 0.55)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    return _save(fig, path)


def ogrenme_egrisi(path):
    satir = _oku("b54_ogrenme_egrisi.csv")
    n = [int(r["egitim_boyutu"]) for r in satir]
    e = [float(r["egitim_skor"]) for r in satir]
    v = [float(r["cv_skor"]) for r in satir]
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.plot(n, e, "o-", color=ACCENT_L, label="eğitim skoru")
    ax.plot(n, v, "s-", color=ACCENT, label="CV doğrulama skoru")
    ax.fill_between(n, v, e, color=FILL[2], alpha=0.8)
    ax.set_xlabel("eğitim kümesi büyüklüğü (örnek)")
    ax.set_ylabel("doğruluk")
    ax.set_ylim(0.93, 1.005)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()
    return _save(fig, path)


def kfold_semasi(path):
    fig, ax = _tuval(9.6, 4.6)
    for i in range(5):
        y = 7.9 - i * 1.25
        ax.text(0.2, y + 0.4, "%d. kat" % (i + 1), fontsize=10,
                color=INK, va="center")
        for j in range(5):
            if i == j:
                _box(ax, 1.6 + j * 1.6, y, 1.45, 0.8, "test",
                     FILL[3], EDGE[3], fs=9, bold=True)
            else:
                _box(ax, 1.6 + j * 1.6, y, 1.45, 0.8, "eğitim",
                     FILL[0], EDGE[0], fs=9)
        ax.text(9.8, y + 0.4, "s%d" % (i + 1), fontsize=10, color=INK,
                va="center", ha="right")
    ax.text(5, 0.6, "Skor = (s₁ + … + s₅) / 5. Her örnek bir kez test, "
            "dört kez eğitimde.", ha="center", fontsize=9.5, color=INK)
    return _save(fig, path)


def zaman_grup(path):
    fig, ax = _tuval(9.6, 6.2)
    ax.text(0.1, 9.6, "(a) Zaman serisi: geleceği geçmişten tahmin et",
            fontsize=10.5, weight="bold", color=INK)
    rast = {1, 4, 6, 9, 11}
    ax.text(0.1, 8.25, "rastgele bölme\n(yanlış: gelecek eğitimde)",
            fontsize=8.5, color=MUTED, va="center")
    for t in range(12):
        _box(ax, 2.6 + t * 0.6, 8.0, 0.55, 0.5, str(t),
             FILL[3] if t in rast else FILL[0],
             EDGE[3] if t in rast else EDGE[0], fs=8)
    ax.text(0.1, 6.95, "ileriye doğru bölme\n(doğru)", fontsize=8.5,
            color=MUTED, va="center")
    for t in range(12):
        test = t >= 9
        _box(ax, 2.6 + t * 0.6, 6.7, 0.55, 0.5, str(t),
             FILL[3] if test else FILL[1], EDGE[3] if test else EDGE[1],
             fs=8)
    ax.text(0.1, 5.3, "(b) Grup bölme: aynı kişi tek tarafta kalsın",
            fontsize=10.5, weight="bold", color=INK)
    ax.text(0.1, 4.0, "rastgele bölme\n(kişiler iki tarafta)",
            fontsize=8.5, color=MUTED, va="center")
    for t in range(12):
        k = t // 3
        test = (t % 4 == 0)
        _box(ax, 2.6 + t * 0.6, 3.6, 0.55, 0.5, "K%d" % (k + 1),
             FILL[3] if test else FILL[0], EDGE[3] if test else EDGE[0],
             fs=7.5)
    ax.text(0.1, 2.3, "GroupKFold\n(K2 bütün test)", fontsize=8.5,
            color=MUTED, va="center")
    for t in range(12):
        k = t // 3
        test = (k == 1)
        _box(ax, 2.6 + t * 0.6, 2.0, 0.55, 0.5, "K%d" % (k + 1),
             FILL[3] if test else FILL[1], EDGE[3] if test else EDGE[1],
             fs=7.5)
    return _save(fig, path)


def sizinti_sonuc(path):
    satir = _oku("b54_sizinti.csv")
    deney = [("secim", "öznitelik seçimi"), ("kopya", "kopya örnek"),
             ("grup", "grup sızıntısı")]
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    x = np.arange(len(deney))
    for j, (yontem, renk, ad) in enumerate(
            [("sizintili", ACCENT, "sızıntılı (yanlış)"),
             ("dogru", EDGE[1], "doğru bölme / pipeline")]):
        m, s = [], []
        for kod, _ in deney:
            r = [q for q in satir if q["deney"] == kod
                 and q["yontem"] == yontem][0]
            m.append(float(r["ortalama"]))
            s.append(float(r["ss"]))
        konum = x + (j - 0.5) * 0.36
        ax.bar(konum, m, 0.34, yerr=s, color=renk, capsize=4, label=ad)
        for xi, mi, si in zip(konum, m, s):
            ax.text(xi, mi + si + 0.025, "%.2f" % mi, ha="center",
                    fontsize=9)
    ax.axhline(0.5, color=MUTED, ls="--", lw=1.0,
               label="şans düzeyi (0,5)")
    ax.set_xticks(x)
    ax.set_xticklabels([d[1] for d in deney])
    ax.set_ylabel("CV doğruluğu (20 tohum ortalaması)")
    ax.set_ylim(0, 1.2)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=3)
    fig.tight_layout()
    return _save(fig, path)


def baseline_karsilastirma(path):
    satir = _oku("b54_baseline.csv")
    dog = [float(r["dogruluk"]) for r in satir]
    den = [float(r["dengeli_dogruluk"]) for r in satir]
    x = np.arange(len(satir))
    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    b1 = ax.bar(x - 0.19, dog, 0.36, color=ACCENT_L, label="doğruluk")
    b2 = ax.bar(x + 0.19, den, 0.36, color=ACCENT,
                label="dengeli doğruluk")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02,
                    "%.2f" % b.get_height(), ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(["hep çoğunluk\n(baseline)",
                        "rastgele oran\n(baseline)", "lojistik\nregresyon"])
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("test kümesi skoru")
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    return _save(fig, path)


def pipeline_akis(path):
    fig, ax = _tuval(9.6, 5.6)
    ust = ["1  Veri toplama", "2  Keşif (EDA)", "3  Bölme (ÖNCE!)",
           "4  Ön işleme\n(yalnız eğitimden\nöğren)", "5  Model eğitimi"]
    alt = ["6  Değerlendirme\n(test: bir kez)", "7  Hata analizi",
           "8  Dağıtım", "9  İzleme\n(dağılım kayması)",
           "10  Yeni veri\n→ geri besleme"]
    xs = [0.2, 2.2, 4.2, 6.2, 8.2]
    for i, (x, m) in enumerate(zip(xs, ust)):
        sil = i == 2
        _box(ax, x, 6.6, 1.7, 1.4, m, FILL[3] if sil else FILL[0],
             ACCENT if sil else EDGE[0], fs=8.5, bold=sil)
        if i < 4:
            _arrow(ax, x + 1.7, 7.3, xs[i + 1], 7.3)
    for i, (x, m) in enumerate(zip(reversed(xs), alt)):
        _box(ax, x, 3.0, 1.7, 1.4, m, FILL[1], EDGE[1], fs=8.5)
        if i < 4:
            _arrow(ax, x, 3.7, xs[3 - i] + 1.7, 3.7)
    _arrow(ax, 9.05, 6.6, 9.05, 4.4, col=MUTED, lw=1.2)
    _arrow(ax, 0.2, 3.7, 0.2, 6.6, col=MUTED, lw=1.2)
    ax.text(5, 1.5, "Bölme (3), ön işlemeden (4) önce gelir: aksi halde "
            "test bilgisi eğitime sızar.", ha="center", fontsize=9,
            color=INK)
    ax.text(5, 0.7, "Oklar akışı gösterir; 10 → 1 hattı yeni veriyle "
            "yeniden eğitimi temsil eder.", ha="center", fontsize=8.5,
            color=MUTED)
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn, ad in [
        (kural_vs_ogrenme, "b54_kural_vs_ogrenme.png"),
        (ml_turleri, "b54_ml_turleri.png"),
        (polinom_uyum, "b54_polinom_uyum.png"),
        (polinom_hata, "b54_polinom_hata.png"),
        (ogrenme_egrisi, "b54_ogrenme_egrisi.png"),
        (kfold_semasi, "b54_kfold_semasi.png"),
        (zaman_grup, "b54_zaman_grup.png"),
        (sizinti_sonuc, "b54_sizinti_sonuc.png"),
        (baseline_karsilastirma, "b54_baseline.png"),
        (pipeline_akis, "b54_pipeline_akis.png"),
    ]:
        print(fn(os.path.join(OUT, ad)))
