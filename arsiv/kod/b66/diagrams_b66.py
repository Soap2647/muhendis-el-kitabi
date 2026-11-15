# -*- coding: utf-8 -*-
"""Bölüm 66 - CNN & Bilgisayarlı Görü diyagramları.

Ölçüm grafikleri ve görsel deney çıktıları engine/veri/b66_* dosyalarından
okunur (bunlar arsiv/kod/b66 içindeki t01-t09 betiklerinin çıktısıdır).
Kavramsal şekiller (kayan pencere, im2col, artık blok) veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec

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


def izgara(ax, x0, y0, n, m, h=0.45, vals=None, vurgu=None, bos=None,
           fs=8, renk=None):
    """n satır, m sütun hücre ızgarası; sol-alt köşe (x0, y0)."""
    for r in range(n):
        for c in range(m):
            x = x0 + c * h
            y = y0 + (n - 1 - r) * h
            fc = FILL[0]
            if bos and (r, c) in bos:
                fc = "#FFFFFF"
            if vurgu and (r, c) in vurgu:
                fc = vurgu[(r, c)]
            ax.add_patch(Rectangle((x, y), h, h, facecolor=fc,
                                   edgecolor=EDGE[0], lw=0.8))
            if vals is not None:
                ax.text(x + h / 2, y + h / 2, str(vals[r][c]), ha="center",
                        va="center", fontsize=fs, color=INK)


# --------------------------------------------------------------------------- #
def kayan_pencere(path):
    """Şekil: P ve S'nin çıktı boyutuna etkisi (elle çizilmiş ızgara)."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    # (a) P=1, S=1: 5x5 girdi, 1 dolgu -> 7x7; 3x3 pencere merkezde
    h = 0.42
    bos = {(r, c) for r in range(7) for c in range(7)
           if r in (0, 6) or c in (0, 6)}
    vurgu = {(r, c): "#D9DEE6" for r in range(1, 4) for c in range(1, 4)}
    izgara(ax, 0.6, 3.0, 7, 7, h=h, bos=bos, vurgu=vurgu)
    ax.text(0.6 + 3.5 * h, 2.4, "(a) girdi 5×5, dolgu P=1 (beyaz çerçeve)",
            ha="center", fontsize=9, color=INK)
    _arrow(ax, 4.35, 6.0, 6.25, 6.0, col=ACCENT, lw=1.4)
    izgara(ax, 6.6, 4.0, 5, 5, h=0.5)
    ax.text(6.6 + 2.5 * 0.5, 3.3, "çıktı 5×5\nS=1, K=3, P=1",
            ha="center", fontsize=9, color=INK)
    # (b) P=0, S=2: 7x7 girdi -> 3x3 çıktı; pencereler 2 hücre atlar
    izgara(ax, 11.5, 3.0, 7, 7, h=h,
           vurgu={(r, c): "#D9DEE6" for r in range(0, 3) for c in range(0, 3)})
    ax.add_patch(Rectangle((11.5 + 2 * h, 3.0 + 4 * h), 3 * h, 3 * h,
                           fill=False, edgecolor=ACCENT, lw=1.6, ls="--"))
    ax.add_patch(Rectangle((11.5 + 4 * h, 3.0 + 2 * h), 3 * h, 3 * h,
                           fill=False, edgecolor=ACCENT, lw=1.6, ls="--"))
    ax.text(11.5 + 3.5 * h, 2.4, "(b) girdi 7×7, P=0, S=2 (kesikli: ikinci pencereler)",
            ha="center", fontsize=9, color=INK)
    _arrow(ax, 15.0, 6.0, 16.6, 6.0, col=ACCENT, lw=1.4)
    izgara(ax, 16.9, 5.2, 3, 3, h=0.5)
    ax.text(16.9 + 1.5 * 0.5, 4.5, "çıktı 3×3\n⌊(7−3)/2⌋+1 = 3",
            ha="center", fontsize=9, color=INK)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def im2col(path):
    """Şekil: im2col dönüşümü ve konvolüsyonun tek matris çarpımına indirgenmesi."""
    girdi = np.arange(16).reshape(4, 4)
    kern = np.array([[1, 0, -1], [1, 0, -1], [1, 0, -1]])
    cols = []
    for i in range(2):
        for j in range(2):
            cols.append(girdi[i:i + 3, j:j + 3].reshape(-1))
    cols = np.array(cols)
    cikis = cols @ kern.reshape(-1)
    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 8.6)
    ax.axis("off")
    izgara(ax, 0.5, 3.6, 4, 4, h=0.6,
           vals=[[str(v) for v in row] for row in girdi], fs=10)
    ax.text(0.5 + 2 * 0.6, 3.0, "girdi 4×4", ha="center", fontsize=10)
    _arrow(ax, 3.2, 5.0, 4.4, 5.0, col=ACCENT, lw=1.3)
    vurgu = {(r, c): "#EFD9D6" for r in range(4) for c in range(9)}
    izgara(ax, 4.6, 1.0, 4, 9, h=0.42,
           vals=[[str(v) for v in row] for row in cols.tolist()],
           vurgu=None, fs=7)
    ax.text(4.6 + 4.5 * 0.42, 0.45, "im2col: her satır bir pencere (4 × 9)",
            ha="center", fontsize=9)
    _arrow(ax, 8.9, 3.0, 10.0, 3.0, col=ACCENT, lw=1.3)
    izgara(ax, 10.3, 2.2, 9, 1, h=0.42,
           vals=[["1"], ["0"], ["-1"], ["1"], ["0"], ["-1"], ["1"], ["0"],
                 ["-1"]], fs=8)
    ax.text(10.3 + 0.21, 1.6, "çekirdek\n(9 × 1)", ha="center", fontsize=9)
    _arrow(ax, 11.8, 3.0, 13.0, 3.0, col=ACCENT, lw=1.3)
    izgara(ax, 13.4, 3.4, 2, 2, h=0.6,
           vals=[[str(cikis[0]), str(cikis[1])],
                 [str(cikis[2]), str(cikis[3])]], fs=10)
    ax.text(13.4 + 0.6, 3.0, "çıktı 2×2\n(4 × 1 olarak)", ha="center",
            va="top", fontsize=9)
    _box(ax, 15.8, 5.4, 3.9, 2.3,
         "Dönüşüm sonrası:\nbir matris çarpımı\nZ = cols · w + b",
         fill=FILL[1], edge=EDGE[1], fs=10)
    _box(ax, 15.8, 1.4, 3.9, 2.6,
         "Geri geçiş:\ndW = colsᵀ · dY\ndcols = dY · wᵀ\n(col2im ile topla)",
         fill=FILL[2], edge=EDGE[2], fs=10)
    _save(fig, path)
    return path, cikis


# --------------------------------------------------------------------------- #
def kayma(path):
    rows = oku("b66_kayma.csv")
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    kaymalar = sorted({int(r["kayma"]) for r in rows})
    for model, renk, etiket in (("MLP", EDGE[3], "MLP (düzleştirilmiş girdi, 296 bin parametre)"),
                                ("CNN", EDGE[1], "CNN (konvolüsyon, 24 bin parametre)")):
        ort, sd = [], []
        for dx in kaymalar:
            v = [float(r["dogruluk"]) for r in rows
                 if r["model"] == model and int(r["kayma"]) == dx]
            ort.append(np.mean(v))
            sd.append(np.std(v, ddof=1))
        ort, sd = np.array(ort), np.array(sd)
        ax.plot(kaymalar, ort, "o-", color=renk, lw=2, label=etiket)
        ax.fill_between(kaymalar, ort - sd, ort + sd, color=renk, alpha=0.18)
    ax.set_xlabel("Test görüntüsünün yatay kayması (piksel)", color=INK)
    ax.set_ylabel("Test doğruluğu", color=INK)
    ax.set_ylim(0.0, 1.02)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Eğitim kayma (jitter ±3 px) dışında; 5 tohumun ortalaması ± sapma",
                 fontsize=10, color=MUTED)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def artik_blok(path):
    """Şekil: artık (residual) blok. x + F(x) ve ReLU."""
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 9)
    ax.axis("off")
    _box(ax, 0.4, 3.6, 2.4, 1.6, "girdi x", fill=FILL[0], edge=EDGE[0], fs=10)
    _box(ax, 4.2, 3.6, 3.0, 1.6, "Conv 3×3\nBN, ReLU", fill=FILL[1], edge=EDGE[1], fs=9)
    _box(ax, 8.0, 3.6, 3.0, 1.6, "Conv 3×3\nBN", fill=FILL[1], edge=EDGE[1], fs=9)
    ax.add_patch(plt.Circle((12.4, 4.4), 0.42, facecolor="white",
                            edgecolor=ACCENT, lw=1.6))
    ax.text(12.4, 4.4, "+", ha="center", va="center", fontsize=16, color=ACCENT)
    _box(ax, 13.6, 3.6, 2.6, 1.6, "ReLU", fill=FILL[2], edge=EDGE[2], fs=10)
    _box(ax, 17.2, 3.6, 2.4, 1.6, "çıktı\nF(x)+x", fill=FILL[0], edge=EDGE[0], fs=10)
    _arrow(ax, 2.8, 4.4, 4.2, 4.4)
    _arrow(ax, 7.2, 4.4, 8.0, 4.4)
    _arrow(ax, 11.0, 4.4, 11.98, 4.4)
    _arrow(ax, 12.82, 4.4, 13.6, 4.4)
    _arrow(ax, 16.2, 4.4, 17.2, 4.4)
    # kestirme (identity) bağlantısı
    ax.plot([1.6, 1.6, 12.4], [5.25, 7.6, 7.6], color=ACCENT, lw=1.6)
    _arrow(ax, 12.4, 7.6, 12.4, 4.86, col=ACCENT, lw=1.6)
    ax.text(7.0, 8.0, "kestirme bağlantı (kimlik, parametresiz)",
            ha="center", fontsize=10, color=ACCENT)
    ax.text(10.0, 1.6,
            "F(x) yalnızca bir kalıntı öğrenir; ağ, kimlik eşlemesine\n"
            "yakın bir çözümde kalmak için F(x) → 0 yapabilir.",
            ha="center", fontsize=10, color=INK)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def artik_kayip(path):
    rows = oku("b66_artik_kayip.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.8, 4.0), sharey=True)
    grup = [("BN'li", ["duz_BN", "artik_BN"]),
            ("BN'siz", ["duz_BNsiz", "artik_BNsiz"])]
    for ax, (baslik, var) in zip(axs, grup):
        for v, renk, etiket in ((var[0], EDGE[3], "düz (25 konvolüsyon)"),
                                (var[1], EDGE[1], "artık (25 konvolüsyon)")):
            epochs = sorted({int(r["epoch"]) for r in rows})
            ort, sd = [], []
            for e in epochs:
                vals = [float(r["egitim_kaybi"]) for r in rows
                        if r["varyant"] == v and int(r["epoch"]) == e]
                ort.append(np.mean(vals))
                sd.append(np.std(vals, ddof=1))
            ort, sd = np.array(ort), np.array(sd)
            ax.plot(epochs, ort, "-", color=renk, lw=2, label=etiket)
            ax.fill_between(epochs, ort - sd, ort + sd, color=renk, alpha=0.18)
        ax.set_yscale("log")
        ax.set_title(baslik, fontsize=10, color=INK)
        ax.set_xlabel("Epoch", color=INK)
        ax.grid(color=RULE, lw=0.6, which="both")
        ax.legend(frameon=False, fontsize=8, loc="center right")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axs[0].set_ylabel("Eğitim kaybı (log)", color=INK)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def artirma(path):
    d = np.load(os.path.join(VERI, "b66_artirma_ornek.npz"))
    orj, art = d["orj"], d["art"]
    fig = plt.figure(figsize=(8.8, 3.6))
    gs = GridSpec(4, 8, figure=fig, hspace=0.08, wspace=0.05)
    for c in range(8):
        ax = fig.add_subplot(gs[0, c])
        ax.imshow(orj[c], cmap="gray", vmin=0, vmax=1)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor(EDGE[0])
    for k in range(3):
        for c in range(8):
            ax = fig.add_subplot(gs[k + 1, c])
            ax.imshow(art[k, c], cmap="gray", vmin=0, vmax=1)
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_edgecolor(ACCENT)
    fig.text(0.01, 0.80, "özgün", rotation=90, va="center", fontsize=9)
    fig.text(0.01, 0.30, "artırılmış", rotation=90, va="center", fontsize=9)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def transfer(path):
    rows = oku("b66_transfer.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    ns = sorted({int(r["n_sinif"]) for r in rows})
    stiller = (("sifirdan", EDGE[3], "o-", "sıfırdan"),
               ("ozellik", EDGE[2], "s--", "özellik çıkarıcı (gövde donuk)"),
               ("ince_ayar", EDGE[1], "^-", "ince ayar (gövde 1e-4)"))
    for yontem, renk, bicim, etiket in stiller:
        ort, sd = [], []
        for n in ns:
            v = [float(r["dogruluk"]) for r in rows
                 if r["yontem"] == yontem and int(r["n_sinif"]) == n]
            ort.append(np.mean(v))
            sd.append(np.std(v, ddof=1))
        ort, sd = np.array(ort), np.array(sd)
        ax.plot(ns, ort, bicim, color=renk, lw=2, label=etiket)
        ax.fill_between(ns, ort - sd, ort + sd, color=renk, alpha=0.15)
    ax.set_xscale("log")
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel("Sınıf başına hedef eğitim örneği (log ölçek)", color=INK)
    ax.set_ylabel("Hedef test doğruluğu", color=INK)
    ax.set_ylim(0.2, 1.02)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def filtre_harita(path):
    d = np.load(os.path.join(VERI, "b66_gorsel.npz"))
    filtre, f1, f3, girdi = d["filtre"], d["f1"], d["f3"], d["girdi_ornek"]
    fig = plt.figure(figsize=(9.6, 5.6))
    gs = GridSpec(3, 8, figure=fig, hspace=0.35, wspace=0.12,
                  height_ratios=[1.0, 1.25, 1.25])
    for k in range(16):
        ax = fig.add_subplot(gs[0, k % 8] if k < 8 else gs[1, k % 8])
        v = np.abs(filtre[k]).max()
        ax.imshow(filtre[k], cmap="RdBu_r", vmin=-v, vmax=v)
        ax.set_xticks([]); ax.set_yticks([])
    ax0 = fig.add_subplot(gs[2, 0:2])
    ax0.imshow(girdi, cmap="gray", vmin=0, vmax=1)
    ax0.set_title("girdi", fontsize=9)
    ax0.set_xticks([]); ax0.set_yticks([])
    for k in range(4):
        ax = fig.add_subplot(gs[2, 2 + k])
        ax.imshow(f1[k * 3], cmap="viridis")
        ax.set_title("1. katman %d" % (k * 3), fontsize=8)
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.02, 0.97, "Üstte: ilk katmanın 16 filtresi (3×3, kırmızı pozitif, mavi negatif)",
             fontsize=9, color=INK)
    fig.text(0.02, 0.02, "Altta: girdi ve birinci katman özellik haritalarından dördü",
             fontsize=9, color=INK)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def gradcam(path):
    d = np.load(os.path.join(VERI, "b66_gorsel.npz"))
    fig, axs = plt.subplots(2, 4, figsize=(8.6, 4.8))
    ad = ["daire", "kare", "üçgen", "artı"]
    for c in range(4):
        ax = axs[0, c]
        ax.imshow(d["dogru_img"][c], cmap="gray", vmin=0, vmax=1)
        ax.imshow(d["dogru_cam"][c], cmap="jet", alpha=0.42)
        ax.set_title("gerçek: %s" % ad[int(d["dogru_sinif"][c])],
                     fontsize=8, color=INK)
        ax.set_xticks([]); ax.set_yticks([])
        ax = axs[1, c]
        ax.imshow(d["yanlis_img"][c], cmap="gray", vmin=0, vmax=1)
        ax.imshow(d["yanlis_cam"][c], cmap="jet", alpha=0.42)
        g = int(d["yanlis_gercek"][c]); t = int(d["yanlis_tahmin"][c])
        ax.set_title("gerçek %s, tahmin %s\nolasılık %.2f" % (
            ad[g], ad[t], d["yanlis_guven"][c]), fontsize=7, color=ACCENT)
        ax.set_xticks([]); ax.set_yticks([])
    fig.text(0.01, 0.955, "Doğru tahminler (Grad-CAM, tahmin edilen sınıf)",
             fontsize=9, color=INK)
    fig.text(0.01, 0.47, "En kötü hatalar (yanlış tahmin, en yüksek güven)",
             fontsize=9, color=ACCENT)
    fig.subplots_adjust(hspace=0.55, wspace=0.12, top=0.92, bottom=0.03)
    _save(fig, path)
    return path


# --------------------------------------------------------------------------- #
def bozulma(path):
    rows = oku("b66_bozulma.csv")
    turler = [("gurultu", "Gauss gürültüsü σ"),
              ("bulaniklik", "bulanıklık (kutu filtre tekrarı)"),
              ("karanlik", "parlaklık çarpanı"),
              ("kontrast", "kontrast c")]
    etiket = {"gurultu": ["0", "0,1", "0,2", "0,3", "0,4"],
              "bulaniklik": ["0", "1", "2", "3", "4"],
              "karanlik": ["1,0", "0,7", "0,5", "0,3", "0,15"],
              "kontrast": ["1,0", "0,7", "0,5", "0,3", "0,15"]}
    fig, axs = plt.subplots(2, 2, figsize=(8.8, 6.0))
    for ax, (tur, baslik) in zip(axs.flat, turler):
        ort, sd = [], []
        for sev in range(5):
            v = [float(r["dogruluk"]) for r in rows
                 if r["tur"] == tur and int(r["siddet"]) == sev]
            ort.append(np.mean(v))
            sd.append(np.std(v, ddof=1))
        ort, sd = np.array(ort), np.array(sd)
        x = np.arange(5)
        ax.plot(x, ort, "o-", color=EDGE[1], lw=2)
        ax.fill_between(x, ort - sd, ort + sd, color=EDGE[1], alpha=0.18)
        ax.set_xticks(x)
        ax.set_xticklabels(etiket[tur], fontsize=8)
        ax.set_ylim(0.0, 1.02)
        ax.set_title(baslik, fontsize=9, color=INK)
        ax.grid(color=RULE, lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axs[0, 0].set_ylabel("Test doğruluğu", color=INK)
    axs[1, 0].set_ylabel("Test doğruluğu", color=INK)
    fig.subplots_adjust(hspace=0.45, wspace=0.25)
    _save(fig, path)
    return path


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    g = lambda ad: os.path.join(GORSEL, ad)
    kayan_pencere(g("b66_kayan_pencere.png"))
    im2col(g("b66_im2col.png"))
    kayma(g("b66_kayma.png"))
    artik_blok(g("b66_artik_blok.png"))
    artik_kayip(g("b66_artik_kayip.png"))
    artirma(g("b66_artirma.png"))
    transfer(g("b66_transfer.png"))
    filtre_harita(g("b66_filtre_harita.png"))
    gradcam(g("b66_gradcam.png"))
    bozulma(g("b66_bozulma.png"))
    print("tamam")
