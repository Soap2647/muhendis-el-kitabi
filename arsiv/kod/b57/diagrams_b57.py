# -*- coding: utf-8 -*-
"""Bolum 57 - Degerlendirme & Deney Tasarimi diyagramlari.

Olcum grafikleri engine/veri/b57_*.csv dosyalarini okur:
  b57_karisiklik.csv, b57_kucuk_ornek.csv, b57_roc_pr_egri.csv,
  b57_esik_maliyet.csv, b57_kalibrasyon.csv, b57_ic_ice_cv.csv,
  b57_arama_noktalar.csv, b57_asiri_uyum.csv,
  b57_ogrenme_egrisi.csv, b57_erken_bakma.csv
Kavram sekilleri (karisiklik matrisi, arama noktalari) veriden
ya da analitik formulden cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _save, ACCENT, ACCENT_L, INK, MUTED,
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


def _eksen(ax):
    for a in ["top", "right"]:
        ax.spines[a].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(True, color=RULE, lw=0.6)
    ax.set_axisbelow(True)


# --------------------------------------------------------------- #
def karisiklik(path):
    """Karisiklik matrisi ve metrik formulleri."""
    K = np.zeros((2, 2), int)
    for r in _oku("b57_karisiklik.csv"):
        K[int(r["gercek"]), int(r["tahmin"])] = int(r["sayi"])
    tn, fp, fn, tp = K[0, 0], K[0, 1], K[1, 0], K[1, 1]
    fig, ax = _tuval(9.6, 4.8)
    hucre = [
        (2.0, 5.0, "TN = %d" % tn, "iyi huylu, dogru", FILL[1], EDGE[1]),
        (4.4, 5.0, "FP = %d" % fp, "yanlis alarm", FILL[3], EDGE[3]),
        (2.0, 2.5, "FN = %d" % fn, "kacan tespit", FILL[3], EDGE[3]),
        (4.4, 2.5, "TP = %d" % tp, "kotu huylu, dogru", FILL[1], EDGE[1]),
    ]
    for x, y, ad, alt, f, e in hucre:
        _box(ax, x, y, 2.2, 2.0, ad + "\n" + alt, fill=f, edge=e,
             fs=11, bold=True)
    ax.text(3.1, 7.5, "Tahmin: 0 (iyi)", ha="center", fontsize=10,
            color=MUTED)
    ax.text(5.5, 7.5, "Tahmin: 1 (kotu)", ha="center", fontsize=10,
            color=MUTED)
    ax.text(1.8, 6.0, "Gercek 0", ha="right", va="center",
            fontsize=10, color=MUTED)
    ax.text(1.8, 3.5, "Gercek 1", ha="right", va="center",
            fontsize=10, color=MUTED)
    n = K.sum()
    acc = (tp + tn) / n
    pre = tp / (tp + fp)
    rec = tp / (tp + fn)
    spe = tn / (tn + fp)
    f1 = 2 * pre * rec / (pre + rec)
    satir = [
        "Dogruluk   = (TP+TN)/N = %.3f" % acc,
        "Kesinlik   = TP/(TP+FP) = %.3f" % pre,
        "Duyarlilik = TP/(TP+FN) = %.3f" % rec,
        "Ozgulluk   = TN/(TN+FP) = %.3f" % spe,
        "F1 = 2PR/(P+R)          = %.3f" % f1,
    ]
    for i, s in enumerate(satir):
        ax.text(6.2, 7.2 - i * 0.9, s, fontsize=8.8, color=INK,
                family="DejaVu Sans Mono", va="center")
    ax.text(6.2, 2.4, "Kesinlik: tahmin ettigimizin kaci dogru?",
            fontsize=9, color=MUTED, va="center")
    ax.text(6.2, 1.8, "Duyarlilik: gercegin kaci yakalandi?",
            fontsize=9, color=MUTED, va="center")
    _save(fig, path)
    return path


def kucuk_roc_pr(path):
    """8 ornekli kucuk ornekte esik taramasi: ROC ve PR."""
    rows = _oku("b57_kucuk_ornek.csv")
    fpr = [0.0] + [float(r["fpr"]) for r in rows]
    tpr = [0.0] + [float(r["tpr"]) for r in rows]
    prec = [float(r["kesinlik"]) for r in rows]
    rec = [float(r["duyarlilik"]) for r in rows]
    esik = [r["esik"] for r in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    _eksen(a1)
    a1.plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1)
    a1.step(fpr, tpr, where="post", color=ACCENT, lw=2)
    a1.scatter(fpr[1:], tpr[1:], color=ACCENT, s=28, zorder=3)
    for x, y, e in zip(fpr[1:], tpr[1:], esik):
        a1.annotate(e, (x, y), textcoords="offset points",
                    xytext=(6, -10), fontsize=8, color=INK)
    a1.set_xlim(-0.03, 1.03)
    a1.set_ylim(-0.03, 1.05)
    a1.set_xlabel("Yanlis pozitif orani (FPR)", color=INK)
    a1.set_ylabel("Dogru pozitif orani (TPR)", color=INK)
    a1.set_title("ROC: AUC = 0,6875 (yamuk)", fontsize=11,
                 color=INK)
    _eksen(a2)
    a2.plot(rec, prec, color=ACCENT_L, lw=2, marker="o", ms=5)
    a2.set_xlim(-0.03, 1.03)
    a2.set_ylim(0.0, 1.05)
    a2.set_xlabel("Duyarlilik (recall)", color=INK)
    a2.set_ylabel("Kesinlik (precision)", color=INK)
    ap = sum((r - rp) * q for r, rp, q in
             zip(rec, [0.0] + rec[:-1], prec))
    a2.set_title("PR: ortalama kesinlik (AP) = %s"
                 % ("%.4f" % ap).replace(".", ","),
                 fontsize=11, color=INK)
    fig.tight_layout()
    _save(fig, path)
    return path


def dengesiz_roc_pr(path):
    """%1 pozitif veride ROC ve PR: ayni modeller, farkli gorunum."""
    rows = _oku("b57_roc_pr_egri.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    renk = {"A": ACCENT, "B": ACCENT_L}
    _eksen(a1)
    a1.plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1)
    for m in ["A", "B"]:
        x = [float(r["fpr"]) for r in rows
             if r["model"] == m and r["fpr"] != ""]
        y = [float(r["tpr"]) for r in rows
             if r["model"] == m and r["fpr"] != ""]
        a1.plot(x, y, color=renk[m], lw=2,
                label="model %s" % m)
    a1.set_xlabel("FPR", color=INK)
    a1.set_ylabel("TPR", color=INK)
    a1.set_title("ROC (AUC: A 0,937 / B 0,685)", fontsize=10.5,
                 color=INK)
    a1.legend(frameon=False, fontsize=9, loc="lower right")
    _eksen(a2)
    a2.axhline(0.01, ls="--", color=MUTED, lw=1)
    a2.text(0.02, 0.03, "taban: %1 pozitif", fontsize=8.5, color=MUTED)
    for m in ["A", "B"]:
        x = [float(r["recall"]) for r in rows
             if r["model"] == m and r["recall"] != ""]
        y = [float(r["precision"]) for r in rows
             if r["model"] == m and r["recall"] != ""]
        a2.plot(x, y, color=renk[m], lw=2, label="model %s" % m)
    a2.set_xlim(0, 1.02)
    a2.set_ylim(0, 1.02)
    a2.set_xlabel("Duyarlilik", color=INK)
    a2.set_ylabel("Kesinlik", color=INK)
    a2.set_title("PR (AP: A 0,570 / B 0,210)", fontsize=10.5,
                 color=INK)
    a2.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    _save(fig, path)
    return path


def esik_maliyet(path):
    """Ornek basina beklenen maliyet, esik boyunca."""
    rows = _oku("b57_esik_maliyet.csv")
    e = np.array([float(r["esik"]) for r in rows])
    mm = np.array([float(r["maliyet_model"]) for r in rows])
    mg = np.array([float(r["maliyet_gercek"]) for r in rows])
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    _eksen(ax)
    ax.semilogx(e, mg, color=MUTED, lw=1.5, ls="--",
                label="gercek olasiliklar")
    ax.semilogx(e, mm, color=ACCENT, lw=2, label="lojistik model")
    t = 1 / 51
    ax.axvline(t, color=EDGE[1], lw=1.2)
    ax.text(t * 1.08, mm.max() * 0.93, "t* = 1/51 = 0,0196",
            fontsize=9.5, color=EDGE[1])
    i = np.argmin(mm)
    ax.scatter([e[i]], [mm[i]], color=ACCENT, zorder=4, s=36)
    ax.annotate("en dusuk maliyet", (e[i], mm[i]),
                textcoords="offset points", xytext=(10, -22),
                fontsize=9, color=INK)
    ax.set_xlabel("Karar esigi t (log olcek)", color=INK)
    ax.set_ylabel("Ornek basina maliyet (c_FP=1, c_FN=50)", color=INK)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    _save(fig, path)
    return path


def kalibrasyon(path):
    """Guvenilirlik diyagramlari: once (asiri guvenli) ve sonra."""
    rows = _oku("b57_kalibrasyon.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.4))
    for ax, ad, baslik in [
            (a1, "gradyan-artirma", "once: gradyan artirma"),
            (a2, "platt", "sonra: Platt (sigmoid)")]:
        _eksen(ax)
        r = [x for x in rows if x["model"] == ad]
        p = np.array([float(x["ort_tahmin"]) for x in r])
        y = np.array([float(x["gozlenen"]) for x in r])
        n = np.array([float(x["sayi"]) for x in r])
        ax.plot([0, 1], [0, 1], ls="--", color=MUTED, lw=1)
        ax.scatter(p, y, s=18 + 60 * n / n.max(), color=ACCENT,
                   alpha=0.85, zorder=3)
        ax.plot(p, y, color=ACCENT, lw=1.2)
        ece = np.sum(n * np.abs(p - y)) / n.sum()
        ax.text(0.04, 0.9, "ECE = %.3f" % ece, fontsize=10,
                color=INK)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Ortalama tahmin", color=INK)
        ax.set_ylabel("Gozlenen pozitif orani", color=INK)
        ax.set_title(baslik, fontsize=11, color=INK)
    fig.tight_layout()
    _save(fig, path)
    return path


def ic_ice_cv(path):
    """Ic ice olmayan ve ic ice CV skorlari, tohum basina."""
    rows = _oku("b57_ic_ice_cv.csv")
    t = np.array([int(r["tohum"]) for r in rows])
    a = np.array([float(r["ic_ice_olmayan"]) for r in rows])
    b = np.array([float(r["ic_ice"]) for r in rows])
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    _eksen(ax)
    ax.hlines(t, b, a, color=RULE, lw=2, zorder=1)
    ax.scatter(a, t, color=ACCENT, s=36, zorder=3,
               label="ic ice DEGIL (best_score_)")
    ax.scatter(b, t, color=ACCENT_L, s=36, zorder=3,
               label="ic ice (dogru)")
    ax.axvline(0.5, ls="--", color=MUTED, lw=1)
    ax.text(0.502, 19.3, "gercek skor 0,5", fontsize=9, color=MUTED)
    ax.set_xlabel("Dogruluk (gurultu verisi)", color=INK)
    ax.set_ylabel("Tohum", color=INK)
    ax.set_xlim(0.44, 0.67)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()
    _save(fig, path)
    return path


def arama_noktalari(path):
    """Izgara ve rastgele arama: 9 deneme, ayni fonksiyon."""
    rows = _oku("b57_arama_noktalar.csv")
    xx, yy = np.meshgrid(np.linspace(0, 1, 200), np.linspace(0, 1, 200))
    zz = -(xx - 0.3) ** 2 - 0.05 * (yy - 0.6) ** 2
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    cs = ax.contourf(xx, yy, zz, levels=12, cmap="Greys")
    ax.contour(xx, yy, zz, levels=12, colors=RULE, linewidths=0.5)
    gi = [r for r in rows if r["yontem"] == "izgara"]
    rr = [r for r in rows if r["yontem"] == "rastgele"]
    ax.scatter([float(r["x"]) for r in gi], [float(r["y"]) for r in gi],
               marker="s", s=70, color=ACCENT, zorder=4,
               label="izgara (3 x 3)")
    ax.scatter([float(r["x"]) for r in rr], [float(r["y"]) for r in rr],
               marker="o", s=60, color=ACCENT_L, zorder=4,
               label="rastgele (9)")
    ax.scatter([0.3], [0.6], marker="*", s=220, color=EDGE[2],
               zorder=5, label="en iyi nokta")
    ax.set_xlabel("x (onemli boyut)", color=INK)
    ax.set_ylabel("y (az onemli boyut)", color=INK)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=9, loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=3)
    cb = fig.colorbar(cs, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("g(x, y)", color=INK)
    fig.tight_layout()
    _save(fig, path)
    return path


def asiri_uyum(path):
    """Dogrulamada en iyiyi secmek: secim yanliligi."""
    rows = _oku("b57_asiri_uyum.csv")
    m = np.array([int(r["M"]) for r in rows])
    v = np.array([float(r["secilen_dogrulama"]) for r in rows])
    t = np.array([float(r["secilen_test"]) for r in rows])
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    _eksen(ax)
    ax.semilogx(m, v, marker="o", color=ACCENT, lw=2,
                label="secilenin dogrulama skoru")
    ax.semilogx(m, t, marker="o", color=ACCENT_L, lw=2,
                label="secilenin test skoru")
    ax.axhline(0.5, ls="--", color=MUTED, lw=1)
    ax.text(20, 0.487, "gercek skor 0,5", fontsize=9, color=MUTED)
    for x, y in zip(m, v):
        ax.annotate("%.3f" % y, (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8.5,
                    color=INK)
    ax.set_xlabel("Denenen konfigurasyon sayisi M (log)", color=INK)
    ax.set_ylabel("Skor", color=INK)
    ax.set_ylim(0.48, 0.66)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    _save(fig, path)
    return path


def ogrenme_egrisi(path):
    """Tani: yuksek sapma, yuksek varyans, dengeli + receteler."""
    rows = _oku("b57_ogrenme_egrisi.csv")
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
    ad_list = [("yuksek sapma", "Yuksek sapma (underfit)"),
               ("yuksek varyans", "Yuksek varyans (overfit)"),
               ("dengeli", "Dengeli model")]
    for ax, (ad, baslik) in zip(axes.ravel()[:3], ad_list):
        _eksen(ax)
        r = [x for x in rows if x["model"] == ad]
        n = np.array([float(x["n_egitim"]) for x in r])
        tr = np.array([float(x["egitim"]) for x in r])
        va = np.array([float(x["dogrulama"]) for x in r])
        sd = np.array([float(x["std"]) for x in r])
        ax.plot(n, tr, marker="o", color=ACCENT_L, lw=2,
                label="egitim")
        ax.plot(n, va, marker="o", color=ACCENT, lw=2,
                label="dogrulama")
        ax.fill_between(n, va - sd, va + sd, color=ACCENT, alpha=0.12)
        ax.set_ylim(0.1, 1.02)
        ax.set_title(baslik, fontsize=10.5, color=INK)
        ax.set_xlabel("Egitim ornegi", color=INK)
        ax.set_ylabel("Dogruluk", color=INK)
        ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    ax = axes.ravel()[3]
    ax.axis("off")
    metin = [
        ("Yuksek sapma", "Iki egri de dusuk ve yakin.\n"
         "Daha karmasik model, daha iyi\noznitelik. Veri isine yaramaz."),
        ("Yuksek varyans", "Aralik buyuk, egitim 1,0.\n"
         "Daha fazla veri, duzenlilestirme,\nmodel sadelestirme."),
        ("Dengeli", "Aralik kucuk, dogrulama yuksek.\n"
         "Son ayar ve hata analizine gec."),
    ]
    for i, (b, t) in enumerate(metin):
        y = 0.9 - i * 0.32
        ax.text(0.02, y, b, fontsize=10.5, weight="bold", color=INK,
                transform=ax.transAxes, va="top")
        ax.text(0.02, y - 0.07, t, fontsize=9.2, color=INK,
                transform=ax.transAxes, va="top")
    fig.tight_layout()
    _save(fig, path)
    return path


def erken_bakma(path):
    """Erken bakma: gercek fark yokken yanlis pozitif orani."""
    rows = _oku("b57_erken_bakma.csv")
    k = [r["bakis_sayisi"] for r in rows]
    f = np.array([float(r["yanlis_pozitif"]) for r in rows])
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    _eksen(ax)
    x = np.arange(len(k))
    ax.bar(x, f, color=[ACCENT if v > 0.1 else ACCENT_L for v in f],
           width=0.6, zorder=3)
    for xi, v in zip(x, f):
        ax.text(xi, v + 0.012, "%.3f" % v, ha="center", fontsize=9,
                color=INK)
    ax.axhline(0.05, ls="--", color=EDGE[1], lw=1.2,
               label="hedef alfa = 0,05")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_xticks(x)
    ax.set_xticklabels(k)
    ax.set_xlabel("Bakis sayisi (K)", color=INK)
    ax.set_ylabel("Yanlis pozitif orani", color=INK)
    ax.set_ylim(0, 0.44)
    fig.tight_layout()
    _save(fig, path)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sekiller = [
        ("karisiklik", karisiklik),
        ("kucuk_roc_pr", kucuk_roc_pr),
        ("dengesiz_roc_pr", dengesiz_roc_pr),
        ("esik_maliyet", esik_maliyet),
        ("kalibrasyon", kalibrasyon),
        ("ic_ice_cv", ic_ice_cv),
        ("arama_noktalari", arama_noktalari),
        ("asiri_uyum", asiri_uyum),
        ("ogrenme_egrisi", ogrenme_egrisi),
        ("erken_bakma", erken_bakma),
    ]
    for ad, fn in sekiller:
        yol = os.path.join(OUT, "b57_%s.png" % ad)
        fn(yol)
        print("yazildi:", os.path.normpath(yol))
