# -*- coding: utf-8 -*-
"""Bolum 62 - Olasılıksal Modeller & Bayesci ML diyagramlari.

Olcum grafikleri engine/veri/b62_*.csv dosyalarini okur. Diyagramlar
(kutu-ok) sabit cizilir. Temp dizinine bagimlilik yok.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fl(rows, k):
    return np.array([float(r[k]) for r in rows])


def tuval(w=9.6, h=4.0, xl=10, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def ureticiayirici(yol):
    fig, ax = tuval(9.6, 4.2, 14, 7)
    ax.text(3.5, 6.6, "Üretici model", ha="center", fontsize=12,
            weight="bold", color=ACCENT_L)
    _box(ax, 0.6, 4.6, 2.6, 1.0, "veri: (x, y)", fill=FILL[0], edge=EDGE[0])
    _box(ax, 4.0, 4.6, 3.0, 1.0, "p(x | y) ve p(y)\nöğren", fill=FILL[0],
         edge=EDGE[0])
    _box(ax, 0.6, 1.2, 6.4, 1.6,
         "Bayes kuralı:  p(y | x) ∝ p(x | y) p(y)\n"
         "(Naive Bayes burada: p(x | y) = Π p(x_j | y))",
         fill=FILL[1], edge=EDGE[1], fs=10)
    _arrow(ax, 3.2, 5.1, 4.0, 5.1, col=EDGE[0])
    _arrow(ax, 5.5, 4.6, 3.5, 2.8, col=EDGE[0])
    ax.text(10.6, 6.6, "Ayırt edici model", ha="center", fontsize=12,
            weight="bold", color=ACCENT)
    _box(ax, 8.6, 4.6, 4.0, 1.0, "veri: (x, y)", fill=FILL[3], edge=EDGE[3])
    _box(ax, 8.6, 1.2, 4.0, 2.4,
         "p(y | x)\ndoğrudan öğren\n(lojistik regresyon,\nBölüm 58)",
         fill=FILL[3], edge=EDGE[3], fs=10)
    _arrow(ax, 10.6, 4.6, 10.6, 3.7, col=EDGE[3])
    _save(fig, os.path.join(yol))


def nb_lr(yol):
    rows = oku("b62_nb_lr_ogrenme.csv")
    n = fl(rows, "n")
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.errorbar(n, fl(rows, "nb_ort"), yerr=fl(rows, "nb_ss"), marker="o",
                color=EDGE[0], capsize=3, label="Gauss naive Bayes")
    ax.errorbar(n, fl(rows, "lr_ort"), yerr=fl(rows, "lr_ss"), marker="s",
                color=EDGE[3], capsize=3, label="Lojistik regresyon")
    ax.set_xscale("log")
    ax.set_xlabel("eğitim örneği sayısı (log ölçek)")
    ax.set_ylabel("test doğruluğu")
    ax.set_title("Meme kanseri verisi: 30 rastgele alt küme, ort. ± ss",
                 fontsize=11)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False)
    _save(fig, yol)


def bayes_agi(yol):
    fig, ax = tuval(9.6, 4.4, 14, 7)
    _box(ax, 1.0, 4.6, 3.4, 1.4, "F: sensör arızası\nP(F=1) = 0,02",
         fill=FILL[0], edge=EDGE[0], fs=10)
    _box(ax, 9.6, 4.6, 3.4, 1.4, "H: gerçek hedef\nP(H=1) = 0,05",
         fill=FILL[1], edge=EDGE[1], fs=10)
    _box(ax, 5.0, 1.2, 4.0, 1.6, "A: alarm\n(gözlenen değişken)",
         fill=FILL[3], edge=EDGE[3], fs=10)
    _arrow(ax, 2.7, 4.6, 5.8, 2.8, col=ACCENT_L)
    _arrow(ax, 11.3, 4.6, 8.2, 2.8, col=ACCENT_L)
    ax.text(0.8, 2.6, "P(A=1 | F,H) için koşullu tablo:", fontsize=9, color=MUTED)
    ax.text(0.8, 0.25,
            "F=0,H=0: 0,01   F=1,H=0: 0,60   F=0,H=1: 0,90   F=1,H=1: 0,92",
            fontsize=9, color=INK)
    _save(fig, yol)


def hmm_viterbi(yol):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                 gridspec_kw={"width_ratios": [1, 1.25]})
    for ax in (a1, a2):
        ax.axis("off")
    a1.set_xlim(0, 10)
    a1.set_ylim(0, 10)
    a1.set_title("Durum diyagramı (HMM)", fontsize=11, color=INK)
    pos = {"kalkis": (2.0, 7.5), "seyir": (5.5, 7.5), "inis": (8.5, 3.5)}
    isim = {"kalkis": "kalkış", "seyir": "seyir", "inis": "iniş"}
    for k, (x, y) in pos.items():
        a1.add_patch(Circle((x, y), 1.0, fc=FILL[0], ec=EDGE[0], lw=1.2))
        a1.text(x, y, isim[k], ha="center", va="center", fontsize=10)
    _arrow(a1, 3.0, 7.5, 4.5, 7.5, col=ACCENT, rad=0.0)
    a1.text(3.4, 8.2, "0,30", fontsize=9, ha="center")
    _arrow(a1, 6.5, 7.5, 7.7, 4.4, col=ACCENT)
    a1.text(7.5, 6.4, "0,03", fontsize=9)
    a1.text(0.4, 0.8, "Gözlem: irtifa değişimi\n(düşüyor / sabit /"
            " yükseliyor)", fontsize=9, color=MUTED)
    a1.text(0.4, 4.0, "kalkış-kalkış 0,70  seyir-seyir 0,97\n"
            "iniş-iniş 0,70  iniş-kalkış 0,30", fontsize=8, color=MUTED)
    # Viterbi kafesi (trellis): 3 durum x 5 zaman
    a2.set_xlim(0, 11)
    a2.set_ylim(0, 10)
    a2.set_title("Viterbi kafesi (örnek yol vurgulu)", fontsize=11,
                 color=INK)
    durumlar = ["kalkış", "seyir", "iniş"]
    yol_ornek = [0, 0, 1, 1, 1]
    for t in range(5):
        x = 2.0 + t * 1.9
        for s in range(3):
            y = 8.0 - s * 3.0
            on = yol_ornek[t] == s
            a2.add_patch(Circle((x, y), 0.55, fc=ACCENT if on else FILL[0],
                                ec=ACCENT if on else EDGE[0], lw=1.2))
            if t == 0:
                a2.text(0.2, y, durumlar[s], fontsize=8, va="center")
    for t in range(4):
        x1, x2 = 2.0 + t * 1.9, 2.0 + (t + 1) * 1.9
        for s1 in range(3):
            for s2 in range(3):
                y1, y2 = 8.0 - s1 * 3.0, 8.0 - s2 * 3.0
                a2.plot([x1 + 0.55, x2 - 0.55], [y1, y2],
                        color=RULE, lw=0.7, zorder=0)
    for t in range(4):
        x1, x2 = 2.0 + t * 1.9, 2.0 + (t + 1) * 1.9
        y1 = 8.0 - yol_ornek[t] * 3.0
        y2 = 8.0 - yol_ornek[t + 1] * 3.0
        a2.plot([x1 + 0.55, x2 - 0.55], [y1, y2], color=ACCENT, lw=2.0,
                zorder=1)
    for t in range(5):
        a2.text(2.0 + t * 1.9, 0.7, "t=%d" % (t + 1), ha="center",
                fontsize=9)
    a2.text(0.2, 9.4, "Kırmızı: örnek bir durum yolu (illüstrasyon)",
            fontsize=8, color=MUTED)
    _save(fig, yol)


def kalman_dongu(yol):
    fig, ax = tuval(9.6, 4.6, 14, 8)
    _box(ax, 0.6, 4.6, 4.2, 2.4,
         "TAHMİN\nx⁻ = F x̂\nP⁻ = F P Fᵀ + Q", fill=FILL[0],
         edge=EDGE[0], fs=10)
    _box(ax, 5.4, 4.6, 4.2, 2.4,
         "GÜNCELLEME\nK = P⁻Hᵀ(HP⁻Hᵀ+R)⁻¹\nx̂ = x⁻ + K(z − Hx⁻)",
         fill=FILL[1], edge=EDGE[1], fs=9.5)
    _box(ax, 10.2, 4.6, 3.4, 2.4, "yeni ölçüm\nz_k", fill=FILL[3],
         edge=EDGE[3], fs=10)
    _arrow(ax, 4.8, 5.8, 5.4, 5.8, col=ACCENT_L)
    _arrow(ax, 10.2, 5.8, 9.6, 5.8, col=ACCENT_L)
    _arrow(ax, 7.5, 4.6, 7.5, 1.0, col=ACCENT, rad=0.0)
    _arrow(ax, 7.5, 1.0, 2.7, 1.0, col=ACCENT, rad=0.0)
    _arrow(ax, 2.7, 1.0, 2.7, 4.6, col=ACCENT, rad=0.0)
    ax.text(5.0, 0.35, "x̂_k, P_k bir sonraki adıma taşınır (tahmin)",
            fontsize=9.5, color=MUTED, ha="center")
    ax.text(7.7, 2.5, "ölçüm varsa", fontsize=9, color=MUTED)
    _save(fig, yol)


def takip_2b(yol):
    rows = oku("b62_takip_yorunge.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.plot(fl(rows, "tx"), fl(rows, "ty"), color=EDGE[0], lw=2,
            label="gerçek yörünge")
    ax.scatter(fl(rows, "zx"), fl(rows, "zy"), s=10, color=MUTED,
               label="gürültülü ölçüm (GPS/radar)")
    ax.plot(fl(rows, "fx"), fl(rows, "fy"), color=ACCENT, lw=2,
            label="Kalman tahmini")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9)
    _save(fig, yol)


def qr_ayar(yol):
    rows = oku("b62_qr_ayar.csv")
    q = fl(rows, "q")
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    ax.plot(q, fl(rows, "r025"), "o-", color=EDGE[0],
            label="R ölçeği 0,25 (ölçüme fazla güven)")
    ax.plot(q, fl(rows, "r1"), "s-", color=EDGE[1],
            label="R ölçeği 1 (doğru model)")
    ax.plot(q, fl(rows, "r4"), "^-", color=EDGE[3],
            label="R ölçeği 4 (ölçüme az güven)")
    ax.axvline(0.5, color=MUTED, ls="--", lw=1)
    ax.text(0.55, 14.5, "gerçek q = 0,5", fontsize=9, color=MUTED)
    ax.set_xscale("log")
    ax.set_xlabel("model süreç gürültüsü q (log ölçek)")
    ax.set_ylabel("ort. konum RMS (m)")
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    _save(fig, yol)


def radar_iz(yol):
    rows = oku("b62_radar_iz.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.plot(fl(rows, "tx"), fl(rows, "ty"), color=EDGE[0], lw=2,
            label="gerçek")
    ax.plot(fl(rows, "ex"), fl(rows, "ey"), color=ACCENT, lw=1.8,
            label="EKF")
    ax.plot(fl(rows, "px"), fl(rows, "py"), color=EDGE[1], lw=1.4,
            ls="--", label="parçacık filtresi (N=1000)")
    ax.plot([0], [0], marker="*", ms=14, color=INK, label="radar")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9)
    _save(fig, yol)


def pf_n(yol):
    rows = oku("b62_pf_N.csv")
    n = fl(rows, "N")
    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    ax.errorbar(n, fl(rows, "rms_ort"), yerr=fl(rows, "rms_ss"), marker="o",
                color=ACCENT, capsize=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("parçacık sayısı N (log)")
    ax.set_ylabel("ort. konum RMS (m, log)")
    ax.grid(color=RULE, lw=0.6)
    ax.set_title("Parçacık sayısına göre konum hatası (30 koşu)",
                 fontsize=10)
    _save(fig, yol)


def bayes_bant(yol):
    bant = oku("b62_bayes_bant.csv")
    nok = oku("b62_bayes_nokta.csv")
    fig, axs = plt.subplots(1, 3, figsize=(10.0, 3.6), sharey=True)
    for ax, N in zip(axs, [2, 10, 50]):
        satir = [r for r in bant if int(r["N"]) == N]
        x = fl(satir, "x")
        m = fl(satir, "ort")
        s = fl(satir, "ss")
        ax.fill_between(x, m - 2 * s, m + 2 * s, color=FILL[0],
                        edgecolor=EDGE[0], lw=0.6, label="±2σ (tahmin)")
        ax.plot(x, m, color=ACCENT, lw=1.6, label="ortalama")
        ax.plot(x, 0.5 + 1.2 * x, color=MUTED, ls=":", lw=1.2,
                label="gerçek doğru")
        p = [r for r in nok if int(r["N"]) == N]
        ax.scatter(fl(p, "x"), fl(p, "y"), s=12, color=INK, zorder=3)
        ax.set_title("N = %d" % N, fontsize=10)
        ax.set_xlabel("x")
        ax.grid(color=RULE, lw=0.5)
    axs[0].set_ylabel("y")
    axs[0].legend(frameon=False, fontsize=7, loc="upper left")
    _save(fig, yol)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    ureticiayirici(os.path.join(GORSEL, "b62_uretici_ayirici.png"))
    nb_lr(os.path.join(GORSEL, "b62_nb_lr_ogrenme.png"))
    bayes_agi(os.path.join(GORSEL, "b62_bayes_agi.png"))
    hmm_viterbi(os.path.join(GORSEL, "b62_hmm_viterbi.png"))
    kalman_dongu(os.path.join(GORSEL, "b62_kalman_dongu.png"))
    takip_2b(os.path.join(GORSEL, "b62_takip_2b.png"))
    qr_ayar(os.path.join(GORSEL, "b62_qr_ayar.png"))
    radar_iz(os.path.join(GORSEL, "b62_radar_ekf_pf.png"))
    pf_n(os.path.join(GORSEL, "b62_pf_n.png"))
    bayes_bant(os.path.join(GORSEL, "b62_bayes_bant.png"))
    print("tamam")
