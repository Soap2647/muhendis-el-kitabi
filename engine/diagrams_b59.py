# -*- coding: utf-8 -*-
"""Bölüm 59 - Ağaçlar & Ensemble diyagramları.

Ölçüm grafikleri engine/veri/ altındaki CSV dosyalarını okur:
  b59_bolme_2b.csv       2B veri ve kutular (şekil 59.1)
  b59_derinlik.csv       derinliğe göre hata (şekil 59.3)
  b59_karar_siniri.csv   iki ağacın karar sınırı (şekil 59.4)
  b59_korelasyon.csv     korelasyon ve varyans (şekil 59.5)
  b59_rf_agac.csv        rastgele orman ağaç sayısı (şekil 59.6)
  b59_gbm_adim.csv       gradyan artırma adımları (şekil 59.7)
  b59_gbm_egri.csv       öğrenme oranı ve ağaç sayısı (şekil 59.8)
  b59_onem.csv           önem ölçütleri (şekil 59.9)
  b59_model_karsilastirma.csv   model kıyası (şekil 59.10)
Gini/entropi eğrisi analitik formüllerle çizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sekil_agac_bolme(path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.6),
                                 gridspec_kw={"width_ratios": [1, 1.05]})
    a1.set_xlim(0, 10)
    a1.set_ylim(0, 10)
    a1.axis("off")
    _box(a1, 3.4, 8.0, 3.2, 1.2, "kök\nx₁ ≤ t₁ ?", fill=FILL[0],
         edge=EDGE[0], fs=9)
    _box(a1, 0.4, 5.0, 3.2, 1.2, "x₂ ≤ t₂ ?", fill=FILL[1],
         edge=EDGE[1], fs=9)
    _box(a1, 6.4, 5.0, 3.2, 1.2, "yaprak: 1", fill=FILL[2],
         edge=EDGE[2], fs=9)
    _box(a1, 0.4, 1.8, 2.2, 1.2, "yaprak: 0", fill=FILL[4],
         edge=EDGE[4], fs=9)
    _box(a1, 3.2, 1.8, 2.2, 1.2, "yaprak: 1", fill=FILL[2],
         edge=EDGE[2], fs=9)
    _arrow(a1, 4.4, 8.0, 2.0, 6.2, col=ACCENT_L)
    _arrow(a1, 6.0, 8.0, 8.0, 6.2, col=ACCENT_L)
    _arrow(a1, 1.4, 5.0, 1.2, 3.0, col=ACCENT_L)
    _arrow(a1, 2.6, 5.0, 4.2, 3.0, col=ACCENT_L)
    a1.text(1.5, 4.1, "evet", fontsize=8, color=MUTED)
    a1.text(3.8, 4.1, "hayır", fontsize=8, color=MUTED)
    a1.set_title("Ağaç (şematik): her düğüm bir soru", fontsize=10, color=INK)
    rows = _oku("b59_bolme_2b.csv")
    for r in rows:
        if r["tur"] == "nokta":
            col = EDGE[0] if r["etiket"] == "0" else ACCENT
            a2.scatter(float(r["x1"]), float(r["x2"]), s=12, color=col,
                       alpha=0.75, edgecolors="none", zorder=3)
    for r in rows:
        if r["tur"] == "kutu":
            x0, x1 = float(r["x1"]), float(r["x2"])
            y0, y1 = float(r["x3"]), float(r["x4"])
            a2.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0,
                         fill=False, edgecolor=MUTED, lw=1.1, ls="--"))
    a2.set_xlim(-1.5, 2.5)
    a2.set_ylim(-1.0, 1.5)
    a2.set_xlabel("x₁")
    a2.set_ylabel("x₂")
    a2.set_title("Eksene paralel bölmeler (derinlik 3)", fontsize=10,
                 color=INK)
    _save(fig, path)


def sekil_gini_entropi(path):
    p = np.linspace(0.001, 0.999, 400)
    gini = 2 * p * (1 - p)
    ent = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    hata = np.minimum(p, 1 - p)
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.plot(p, ent, color=EDGE[0], lw=2.2, label="entropi (bit)")
    ax.plot(p, gini, color=ACCENT, lw=2.2, label="Gini")
    ax.plot(p, hata * 2, color=MUTED, lw=1.5, ls="--",
            label="yanlış sınıflama (×2)")
    ax.axvline(0.5, color=RULE, lw=0.9)
    ax.set_xlabel("pozitif sınıf olasılığı p")
    ax.set_ylabel("safsızlık")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper center")
    _save(fig, path)


def sekil_derinlik(path):
    rows = _oku("b59_derinlik.csv")
    d = [int(r["derinlik"]) for r in rows]
    etr = [float(r["egitim_ort"]) for r in rows]
    ets = [float(r["egitim_ss"]) for r in rows]
    tr = [float(r["test_ort"]) for r in rows]
    tss = [float(r["test_ss"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.errorbar(d, etr, yerr=ets, color=EDGE[0], marker="o", ms=5,
                capsize=3, label="eğitim hatası")
    ax.errorbar(d, tr, yerr=tss, color=ACCENT, marker="s", ms=5,
                capsize=3, label="test hatası")
    ax.set_xlabel("ağaç derinliği")
    ax.set_ylabel("sınıflama hatası")
    ax.set_xticks(d)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9)
    _save(fig, path)


def sekil_karar_kararsiz(path):
    from sklearn.datasets import make_moons
    rows = _oku("b59_karar_siniri.csv")
    x1 = np.array([float(r["x1"]) for r in rows])
    x2 = np.array([float(r["x2"]) for r in rows])
    ta = np.array([int(r["tam_agac"]) for r in rows])
    ya = np.array([int(r["alt_ornek_agac"]) for r in rows])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.4), sharey=True)
    nx = len(np.unique(x1))
    ny = len(np.unique(x2))
    X1 = x1.reshape(ny, nx)
    X2 = x2.reshape(ny, nx)
    cm = ListedColormap(["#EEF1F4", "#F4EAE7"])
    Xm, ym = make_moons(n_samples=400, noise=0.3, random_state=59)
    for ax, z, bas in [(a1, ta, "tam veri (300 örnek)"),
                       (a2, ya, "rastgele %50 alt örnek")]:
        ax.pcolormesh(X1, X2, z.reshape(ny, nx), cmap=cm,
                      shading="auto", zorder=0)
        ax.scatter(Xm[:, 0], Xm[:, 1], c=ym,
                   cmap=ListedColormap([EDGE[0], ACCENT]), s=10,
                   zorder=3, edgecolors="none")
        ax.set_title("Ağaç: " + bas, fontsize=10, color=INK)
        ax.set_xlabel("x₁")
        ax.set_xlim(-1.5, 2.5)
        ax.set_ylim(-1.0, 1.5)
    a1.set_ylabel("x₂")
    _save(fig, path)


def sekil_korelasyon(path):
    rows = _oku("b59_korelasyon.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    renk = {"0.0": EDGE[0], "0.3": EDGE[1], "0.6": EDGE[2],
            "0.9": ACCENT}
    for rho in ["0.0", "0.3", "0.6", "0.9"]:
        sat = [r for r in rows if r["rho"] == rho]
        B = np.array([float(r["B"]) for r in sat])
        fo = np.array([float(r["formul"]) for r in sat])
        si = np.array([float(r["simulasyon"]) for r in sat])
        ax.plot(B, fo, color=renk[rho], lw=1.8,
                label="ρ = %s" % rho.replace(".", ","))
        ax.plot(B, si, "o", color=renk[rho], ms=4)
    ax.set_xscale("log")
    ax.set_xlabel("ağaç sayısı B (log ölçek)")
    ax.set_ylabel("ortalamanın varyansı")
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9)
    ax.text(1.2, 0.05, "çizgi: formül; nokta: simülasyon", fontsize=8,
            color=MUTED)
    _save(fig, path)


def sekil_rf_agac(path):
    rows = _oku("b59_rf_agac.csv")
    B = [int(r["agac_sayisi"]) for r in rows]
    m = [float(r["test_hata_ort"]) for r in rows]
    s = [float(r["test_hata_ss"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.errorbar(B, m, yerr=s, color=ACCENT, marker="o", ms=5, capsize=3)
    ax.set_xscale("log")
    ax.set_xlabel("ağaç sayısı B (log ölçek)")
    ax.set_ylabel("test hatası (5 tohum)")
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    _save(fig, path)


def sekil_gbm_adim(path):
    rows = _oku("b59_gbm_adim.csv")
    x = np.array([float(r["x"]) for r in rows])
    y = np.array([float(r["y"]) for r in rows])
    F = {k: np.array([float(r[k]) for r in rows])
         for k in ["F0", "F1", "F2", "F3", "r0", "r1", "r2"]}
    o = np.argsort(x)
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 7.0))
    (a, b), (c, d) = axs
    a.scatter(x, y, color=EDGE[0], s=16, label="veri")
    a.plot(x[o], F["F0"][o], color=ACCENT, lw=2, label="F₀ (ortalama)")
    a.set_title("(a) başlangıç: F₀", fontsize=10)
    b.scatter(x, F["r0"], color=EDGE[0], s=16, label="artık r₀")
    b.plot(x[o], (F["F1"] - F["F0"])[o], color=ACCENT, lw=2,
           label="h₁ (ilk ağaç)")
    b.axhline(0, color=RULE, lw=0.8)
    b.set_title("(b) artık ve ilk ağacın uyumu", fontsize=10)
    c.scatter(x, y, color=EDGE[0], s=16, label="veri")
    c.plot(x[o], F["F1"][o], color=EDGE[1], lw=2, label="F₁")
    c.scatter(x, F["r1"], color=EDGE[0], s=10, marker="x",
              label="artık r₁")
    c.plot(x[o], (F["F2"] - F["F1"])[o], color=ACCENT, lw=2,
           label="h₂ (ikinci ağaç)")
    c.set_title("(c) ikinci adım: yeni artık", fontsize=10)
    d.scatter(x, y, color=EDGE[0], s=16, label="veri")
    d.plot(x[o], F["F3"][o], color=ACCENT, lw=2.2, label="F₃")
    d.set_title("(d) üç adım sonra: F₃", fontsize=10)
    for ax in axs.ravel():
        ax.set_xlabel("x")
        ax.grid(color=RULE, lw=0.5, alpha=0.6)
        ax.legend(frameon=True, facecolor="white", edgecolor=RULE,
                  fontsize=8, loc="upper right")
    fig.subplots_adjust(hspace=0.42, wspace=0.22)
    _save(fig, path)


def sekil_gbm_eta(path):
    rows = _oku("b59_gbm_egri.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    renk = {"1.0": ACCENT, "0.3": EDGE[2], "0.1": EDGE[1],
            "0.03": EDGE[0]}
    for eta in ["1.0", "0.3", "0.1", "0.03"]:
        sat = [r for r in rows if r["eta"] == eta]
        T = np.array([int(r["agac_sayisi"]) for r in sat])
        m = np.array([float(r["test_mse_ort"]) for r in sat])
        ax.plot(T, m, color=renk[eta], lw=1.8,
                label="öğrenme oranı η = %s" % eta.replace(".", ","))
    ax.set_xlabel("ağaç sayısı T")
    ax.set_ylabel("test ortalama kare hatası")
    ax.set_ylim(1.5, 8)
    ax.grid(color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=9)
    _save(fig, path)


def sekil_onem(path):
    rows = _oku("b59_onem.csv")[:9]
    isim = [r["oznitelik"].replace("remainder__", "")
            .replace("onehotencoder__", "") for r in rows]
    saf = [float(r["safsizlik_onemi"]) for r in rows]
    per = [float(r["permutasyon_onemi"]) for r in rows]
    y = np.arange(len(isim))[::-1]
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.barh(y + 0.2, saf, height=0.38, color=EDGE[0],
            label="safsızlık önemi (eğitim)")
    ax.barh(y - 0.2, per, height=0.38, color=ACCENT,
            label="permütasyon önemi (test, AUC düşüşü)")
    ax.set_yticks(y)
    ax.set_yticklabels(isim, fontsize=9)
    for i, n in enumerate(isim):
        if n == "seri_no":
            ax.get_yticklabels()[i].set_color(ACCENT)
            ax.get_yticklabels()[i].set_weight("bold")
    ax.axvline(0, color=RULE, lw=0.8)
    ax.set_xlabel("önem")
    ax.grid(axis="x", color=RULE, lw=0.5, alpha=0.6)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _save(fig, path)


def sekil_model(path):
    rows = _oku("b59_model_karsilastirma.csv")
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 4.6), sharey=True)
    for ax, ad in zip(axs, ["meme kanseri", "IHA bakim"]):
        sat = [r for r in rows if r["veri"] == ad]
        isim = [r["model"] for r in sat]
        auc = np.array([float(r["auc_ort"]) for r in sat])
        ss = np.array([float(r["auc_ss"]) for r in sat])
        y = np.arange(len(isim))[::-1]
        ax.barh(y, auc, xerr=ss,
                color=[MUTED if "taban" in n else EDGE[0] for n in isim],
                height=0.6, capsize=3)
        ax.set_yticks(y)
        ax.set_yticklabels(isim, fontsize=9)
        ax.set_xlim(0.4, 1.02)
        ax.set_title("%s (test AUC)" % ad, fontsize=10, color=INK)
        ax.grid(axis="x", color=RULE, lw=0.5, alpha=0.6)
    _save(fig, path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sekil_agac_bolme(os.path.join(OUT, "b59_agac_bolme.png"))
    sekil_gini_entropi(os.path.join(OUT, "b59_gini_entropi.png"))
    sekil_derinlik(os.path.join(OUT, "b59_derinlik.png"))
    sekil_karar_kararsiz(os.path.join(OUT, "b59_karar_kararsiz.png"))
    sekil_korelasyon(os.path.join(OUT, "b59_korelasyon.png"))
    sekil_rf_agac(os.path.join(OUT, "b59_rf_agac.png"))
    sekil_gbm_adim(os.path.join(OUT, "b59_gbm_adim.png"))
    sekil_gbm_eta(os.path.join(OUT, "b59_gbm_eta.png"))
    sekil_onem(os.path.join(OUT, "b59_onem.png"))
    sekil_model(os.path.join(OUT, "b59_model_karsilastirma.png"))
    print("tamam")
