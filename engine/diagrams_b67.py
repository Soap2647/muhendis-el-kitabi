# -*- coding: utf-8 -*-
"""Bölüm 67 - Nesne Tespiti, Segmentasyon & Takip diyagramları.

Ölçüm grafikleri ve örnek sahneler engine/veri/b67_* dosyalarından
okunur (bunlar b67 betiklerinin çıktısıdır). Kavramsal şekiller
(IoU geometrisi, NMS, anchor ızgarası, U-Net mimarisi) veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from scipy import ndimage
from diagrams import _box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED, RULE, FILL, EDGE

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(KLASOR, "veri")
SINIF = ["daire", "kare", "üçgen"]
SINIF_CSV = ["daire", "kare", "ucgen"]  # CSV'de ASCII ad
SRENK = ["#3E566B", "#47624A", "#8A6B2D"]
MASKE_RENK = ListedColormap(["#1F1F1D", "#3E566B", "#47624A", "#8A6B2D"])


def _csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f
                                   if not line.startswith("#")))


def _kutu(ax, b, renk, ls="-", lw=1.6, etiket=None):
    x1, y1, x2, y2 = b
    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False,
                           edgecolor=renk, linewidth=lw, linestyle=ls))
    if etiket:
        ax.text(x1, y1 - 1.2, etiket, color=renk, fontsize=7.5,
                weight="bold", va="top")


def _gorsel(ax, img, baslik):
    ax.imshow(img, cmap="gray", vmin=0, vmax=1, extent=(0, 96, 96, 0))
    ax.set_title(baslik, fontsize=10, color=INK)
    ax.set_xticks([])
    ax.set_yticks([])


def gorev_turleri(path):
    """Ayni sahne uzerinde alti gorev turu: cikti biciminin farki."""
    npz = np.load(os.path.join(VERI, "b67_unet_ornek.npz"))
    img, seg = npz["X"][0], npz["gercek"][0]
    gt = [r for r in _csv("b67_tespit_ornek.csv")
          if r["gorsel"] == "0" and r["tur"] == "gercek"]
    fig, axs = plt.subplots(2, 3, figsize=(9.6, 6.6))
    axs = axs.ravel()
    _gorsel(axs[0], img, "Sınıflandırma: tek etiket")
    axs[0].text(48, 50, "sahne: %s" % "daire / kare / üçgen karışık",
                ha="center", color=INK, fontsize=8.5,
                bbox=dict(fc="white", ec=RULE))
    _gorsel(axs[1], img, "Yerelleştirme: tek kutu")
    b = gt[0]
    _kutu(axs[1], [int(b["x1"]), int(b["y1"]), int(b["x2"]),
                   int(b["y2"])], SRENK[0], etiket=b["sinif"])
    _gorsel(axs[2], img, "Tespit: her nesne için kutu + sınıf")
    for b in gt:
        k = SINIF_CSV.index(b["sinif"])
        _kutu(axs[2], [int(b["x1"]), int(b["y1"]), int(b["x2"]),
                       int(b["y2"])], SRENK[k], etiket=b["sinif"])
    _gorsel(axs[3], img, "Anlamsal segmentasyon: piksel sınıfı")
    axs[3].imshow(seg, cmap=MASKE_RENK, vmin=0, vmax=3, alpha=0.45,
                  extent=(0, 96, 96, 0))
    _gorsel(axs[4], img, "Örnek segmentasyonu: her nesne ayrı")
    bile = np.zeros(seg.shape, int)
    k = 0
    for c in (1, 2, 3):
        etk, n = ndimage.label(seg == c)
        for i in range(1, n + 1):
            k += 1
            bile[etk == i] = k
    axs[4].imshow(np.ma.masked_where(bile == 0, bile % 6), cmap="tab10",
                  alpha=0.5, extent=(0, 96, 96, 0))
    _gorsel(axs[5], img, "Takip: aynı kimlik, kareler arası")
    for i, (x, y) in enumerate([(14, 70), (34, 60), (54, 52)]):
        _kutu(axs[5], [x, y, x + 14, y + 14], ACCENT, ls="--",
              lw=1.1)
        axs[5].text(x + 7, y + 7, "7", color=ACCENT, fontsize=9,
                    ha="center", va="center", weight="bold")
    _arrow(axs[5], 21, 60, 61, 48, col=ACCENT, lw=1.2)
    fig.tight_layout()
    return _save(fig, path)


def iou_geometri(path):
    """Iki kutunun kesisimi ve birligi: (10,10,50,50) ve (12,12,52,52)."""
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.set_xlim(0, 62)
    ax.set_ylim(0, 62)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")
    ax.add_patch(Rectangle((12, 12), 38, 38, color=FILL[4], alpha=0.8))
    ax.add_patch(Rectangle((10, 10), 40, 40, fill=False,
                           edgecolor=SRENK[0], lw=2))
    ax.add_patch(Rectangle((12, 12), 40, 40, fill=False,
                           edgecolor=ACCENT, lw=2, linestyle="--"))
    ax.text(31, 31, "kesişim\n38 × 38 = 1444", ha="center",
            va="center", fontsize=9, color=INK, weight="bold")
    ax.text(5, 8, "A (10,10,50,50)\nalan 1600", fontsize=9,
            color=SRENK[0])
    ax.text(41, 58, "B (12,12,52,52)\nalan 1600", fontsize=9,
            color=ACCENT, ha="left")
    ax.text(1, 58, "birlik = 1600 + 1600 − 1444 = 1756\n"
            "IoU = 1444 / 1756 = 0.822", fontsize=9.5, color=INK)
    ax.set_title("Kesişim ve birlik: IoU = kesişim / birlik",
                 fontsize=11, color=INK, loc="left")
    return _save(fig, path)


def nms_sekil(path):
    """Alti kutu: NMS oncesi ve sonrasi (esik 0.5)."""
    kut = [((10, 10, 50, 50), "A 0.90"), ((12, 12, 52, 52), "B 0.85"),
           ((60, 60, 100, 100), "C 0.80"), ((58, 58, 98, 98), "D 0.75"),
           ((10, 60, 40, 90), "E 0.70"), ((30, 30, 70, 70), "F 0.65")]
    tutulan = {"A", "C", "E", "F"}
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.6))
    for ax, baslik in zip(axs, ["NMS öncesi: 6 kutu", "NMS sonrası (IoU > 0,5 bastır)"]):
        ax.set_xlim(0, 110)
        ax.set_ylim(110, 0)
        ax.set_aspect("equal")
        ax.set_title(baslik, fontsize=10, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
    for (b, et) in kut:
        _kutu(axs[0], b, SRENK[0], etiket=et, lw=1.4)
    for (b, et) in kut:
        if et[0] in tutulan:
            _kutu(axs[1], b, ACCENT, etiket=et, lw=1.6)
        else:
            _kutu(axs[1], b, MUTED, ls=":", lw=1.0)
    axs[1].text(56, 106, "B (IoU 0,822 ile A) ve D (0,822 ile C) bastırıldı",
                fontsize=7.5, color=MUTED, ha="left")
    fig.tight_layout()
    return _save(fig, path)


def pr_egri(path):
    """Sinif basina PR egrisi (CNN) ve AP degerleri; veri CSV'den."""
    satir = [r for r in _csv("b67_pr_egri.csv") if r["yontem"] == "cnn"]
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for k, isim in enumerate(SINIF):
        s = [r for r in satir if r["sinif"] == SINIF_CSV[k]]
        r_ = np.array([float(x["recall"]) for x in s])
        p_ = np.array([float(x["precision"]) for x in s])
        ax.step(r_, p_, where="post", color=SRENK[k], lw=1.8,
                label="%s" % isim)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Recall (duyarlılık)")
    ax.set_ylabel("Precision (kesinlik)")
    ax.grid(color=RULE, lw=0.6)
    ax.legend(loc="lower left", fontsize=9, frameon=False)
    ax.set_title("CNN: sınıf başına PR eğrisi, IoU ≥ 0,5 (test)",
                 fontsize=10.5, color=INK, loc="left")
    return _save(fig, path)


def anchor_izgara(path):
    """12x12 izgara, GT kutusu ve iki anchor; ofset kodlamasi."""
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.set_xlim(-2, 98)
    ax.set_ylim(98, -2)
    ax.set_aspect("equal")
    for g in range(13):
        ax.axhline(8 * g, color=RULE, lw=0.7, zorder=0)
        ax.axvline(8 * g, color=RULE, lw=0.7, zorder=0)
    ax.add_patch(Rectangle((48, 40), 8, 8, color=FILL[2], alpha=0.9))
    ax.text(52, 44, "hücre\n(6,5)", ha="center", va="center", fontsize=7.5)
    cx, cy = 52, 44
    _kutu(ax, [cx - 8, cy - 11, cx + 8, cy + 11], ACCENT, lw=2.2)
    ax.text(cx + 9, cy - 11, "GT: 16×22", color=ACCENT, fontsize=8)
    _kutu(ax, [cx - 5, cy - 5, cx + 5, cy + 5], SRENK[1], ls="--", lw=1.3)
    ax.text(cx + 6, cy + 5.5, "a1 (10×10)", color=SRENK[1], fontsize=7.5)
    _kutu(ax, [cx - 10, cy - 10, cx + 10, cy + 10], SRENK[2], ls="--",
          lw=1.3)
    ax.text(cx - 9, cy + 13, "a2 (20×20)", color=SRENK[2], fontsize=7.5)
    ax.plot([cx], [cy], "o", color=INK, ms=3)
    ax.text(3, 3, "ox = cx/8 − gx = 52/8 − 6 = 0,50", fontsize=8.5, color=INK)
    ax.text(3, 93, "oy = cy/8 − gy = 44/8 − 5 = 0,50    tw = log(16/20)",
            fontsize=8.5, color=INK)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("12×12 ızgara (S = 8 px), anchor ve ofset",
                 fontsize=10.5, color=INK, loc="left")
    return _save(fig, path)


def tespit_sonuc(path):
    """Sentetik test sahneleri: GT (yesil kesik) ve CNN (kirmizi)."""
    npz = np.load(os.path.join(VERI, "b67_unet_ornek.npz"))
    X = npz["X"]
    satir = _csv("b67_tespit_ornek.csv")
    fig, axs = plt.subplots(2, 3, figsize=(9.6, 6.6))
    for i, ax in enumerate(axs.ravel()):
        _gorsel(ax, X[i], "Test sahnesi %d" % (i + 1))
        for r in satir:
            if r["gorsel"] != str(i):
                continue
            b = [int(r["x1"]), int(r["y1"]), int(r["x2"]), int(r["y2"])]
            if r["tur"] == "gercek":
                _kutu(ax, b, "#2E7D32", ls="--", lw=1.1)
            else:
                _kutu(ax, b, ACCENT, lw=1.6,
                      etiket="%s %.2f" % (r["sinif"], float(r["skor"])))
    fig.text(0.5, 0.005, "Yeşil kesik: gerçek kutu   Kırmızı: CNN (skor ≥ 0,5)",
             ha="center", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return _save(fig, path)


def unet_mimari(path):
    """U-Net: kodlayici, orta katman, cozucu ve atlama baglantilari."""
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    enc = [(0.6, 6.6, "96×96×16"), (2.6, 5.2, "48×48×32"),
           (4.6, 3.8, "24×24×64")]
    for k, (x, y, t) in enumerate(enc):
        _box(ax, x, y, 1.9, 0.9, "kodlayıcı\n" + t, FILL[0], EDGE[0],
             fs=8)
    _box(ax, 6.8, 2.4, 1.9, 0.9, "orta\n12×12×128", FILL[3], EDGE[3],
         fs=8)
    dec = [(9.0, 3.8, "24×24×64"), (11.0, 5.2, "48×48×32"),
           (12.2, 6.6, "96×96×16")]
    for k, (x, y, t) in enumerate(dec):
        _box(ax, x - 0.1, y, 1.9, 0.9, "çözücü\n" + t, FILL[1], EDGE[1],
             fs=8)
    for k in range(2):
        _arrow(ax, enc[k][0] + 1.9, enc[k][1] + 0.45,
               enc[k + 1][0], enc[k + 1][1] + 0.45)
    _arrow(ax, enc[2][0] + 1.9, enc[2][1] + 0.45, 6.8, 2.85)
    _arrow(ax, 8.7, 2.85, dec[0][0] - 0.1, dec[0][1] + 0.45)
    _arrow(ax, dec[0][0] + 1.8, dec[0][1] + 0.45, dec[1][0] - 0.1,
           dec[1][1] + 0.45)
    _arrow(ax, dec[1][0] + 1.8, dec[1][1] + 0.45, dec[2][0] - 0.1,
           dec[2][1] + 0.45)
    for k in range(3):
        _arrow(ax, enc[k][0] + 1.9, enc[k][1] + 0.1, dec[2 - k][0] - 0.1,
               dec[2 - k][1] + 0.1, col=EDGE[2], rad=0.0, lw=1.1,
               style="->")
    ax.text(7.2, 0.9, "atlama bağlantısı (kodlayıcı → çözücü, birleştirme)",
            color=EDGE[2], fontsize=8.5, ha="center")
    ax.text(0.4, 0.3, "Girdi 1×96×96  →  çıktı 4×96×96 (arka plan + 3 sınıf)",
            fontsize=8.5, color=INK)
    ax.set_title("U-Net (kodlayıcı–çözücü + atlama bağlantıları)",
                 fontsize=10.5, color=INK, loc="left")
    return _save(fig, path)


def segmentasyon(path):
    """Girdi, gercek maske ve tahmin (atlamali U-Net, tohum 1)."""
    npz = np.load(os.path.join(VERI, "b67_unet_ornek.npz"))
    X, g, t = npz["X"], npz["gercek"], npz["tahmin"]
    fig, axs = plt.subplots(3, 3, figsize=(7.4, 7.6))
    for r, i in enumerate([0, 1, 2]):
        _gorsel(axs[r, 0], X[i], "Girdi" if r == 0 else "")
        axs[r, 1].imshow(g[i], cmap=MASKE_RENK, vmin=0, vmax=3,
                         extent=(0, 96, 96, 0))
        axs[r, 2].imshow(t[i], cmap=MASKE_RENK, vmin=0, vmax=3,
                         extent=(0, 96, 96, 0))
        for c in (1, 2):
            axs[r, c].set_xticks([])
            axs[r, c].set_yticks([])
        if r == 0:
            axs[r, 1].set_title("Gerçek maske", fontsize=10)
            axs[r, 2].set_title("Tahmin", fontsize=10)
    fig.text(0.5, 0.01, "Renkler: arka plan (koyu), daire, kare, üçgen",
             ha="center", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return _save(fig, path)


def takip_kesisim(path):
    """Kesisen yorunge (tohum 107): GT 0 ve 1 ve kimlik atamalari."""
    satir = _csv("b67_kesisim.csv")
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 7.0))
    ax = axs[0, 0]
    for g, renk in ((0, SRENK[0]), (1, ACCENT)):
        s = [r for r in satir if r["yontem"] == "macar_iou"
             and int(r["gt_id"]) == g]
        x = [float(r["cx"]) for r in s]
        y = [float(r["cy"]) for r in s]
        ax.plot(x, y, "-", color=renk, lw=1.6, label="GT %d" % g)
        ax.plot(x[0], y[0], "o", color=renk, ms=4)
    ax.set_xlim(0, 200)
    ax.set_ylim(200, 0)
    ax.set_aspect("equal")
    ax.set_xlabel("x (px)")
    ax.set_ylabel("y (px)")
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("(a) Kesişen yörüngeler (tohum 107)", fontsize=10,
                 color=INK, loc="left")
    for ax, mod, baslik in ((axs[0, 1], "macar_iou", "(b) Macar IoU"),
                            (axs[1, 0], "macar_tum", "(c) Macar, tüm tespitler"),
                            (axs[1, 1], "byte", "(d) ByteTrack tarzı")):
        for g, renk, ls in ((0, SRENK[0], "-"), (1, ACCENT, "--")):
            s = [r for r in satir if r["yontem"] == mod
                 and int(r["gt_id"]) == g]
            k = np.array([int(r["kare"]) for r in s], float)
            iz = np.array([float(r["iz_id"]) for r in s])
            iz[iz < 0] = np.nan
            ax.plot(k, iz, ls, color=renk, lw=1.8,
                    label="GT %d" % g)
        ax.set_xlabel("kare")
        ax.set_ylabel("atanan iz kimliği")
        ids = sorted({int(float(r["iz_id"])) for r in satir
                      if r["yontem"] == mod and int(float(r["iz_id"])) >= 0})
        ax.set_ylim(min(ids) - 1, max(ids) + 1)
        ax.set_yticks(ids)
        ax.grid(color=RULE, lw=0.6)
        ax.legend(frameon=False, fontsize=8, loc="center right")
        ax.set_title(baslik, fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    return _save(fig, path)


def cozunurluk_fps(path):
    """Girdi boyutu ve hassasiyete gore ag gecikmesi; kare butcesi."""
    satirlar, son, tak = [], 0.0, 0.0
    with open(os.path.join(VERI, "b67_gecikme.csv"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                parca = line.lstrip("# ").split(",")
                son = float(parca[0].split("=")[1])
                tak = float(parca[1].split("=")[1])
            elif line[:1].isdigit():
                satirlar.append(line.split(","))
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for ad, renk in (("fp32", SRENK[0]), ("fp16", ACCENT)):
        s = [r for r in satirlar if r[1] == ad]
        axs[0].plot([int(r[0]) for r in s], [float(r[2]) for r in s],
                    "s--" if ad == "fp32" else "o-", color=renk,
                    label=ad, ms=7 if ad == "fp32" else 5)
    axs[0].axhline(1000 / 30, color=MUTED, ls=":", lw=1.2)
    axs[0].text(100, 1000 / 30 + 0.08, "30 FPS bütçesi (33,3 ms)",
                fontsize=8, color=MUTED)
    axs[0].set_xlabel("girdi kenarı (px)")
    axs[0].set_ylabel("ağ ileri geçişi (ms, medyan)")
    axs[0].set_xticks([96, 192, 384])
    axs[0].set_ylim(0, 40)
    axs[0].legend(frameon=False, fontsize=9)
    axs[0].set_title("Ağ gecikmesi", fontsize=10, color=INK, loc="left")
    ag96 = float([r for r in satirlar if r[0] == "96" and r[1] == "fp32"][0][2])
    etiket = ["dedektör\n(fp32, 96 px)", "son işleme\n(NMS, 96 px)",
              "takipçi\n(CPU)"]
    axs[1].bar(etiket, [ag96, son, tak],
               color=[FILL[0], FILL[2], FILL[1]],
               edgecolor=[SRENK[0], SRENK[2], SRENK[1]])
    axs[1].set_ylabel("kare başına (ms)")
    axs[1].set_title("Kare bütçesi: aşamalar", fontsize=10, color=INK,
                     loc="left")
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(KLASOR, "..", "gorseller")
    isler = [
        (gorev_turleri, "gorev_turleri"), (iou_geometri, "iou_geometri"),
        (nms_sekil, "nms"), (pr_egri, "pr_egri"),
        (anchor_izgara, "anchor_izgara"), (tespit_sonuc, "tespit_sonuc"),
        (unet_mimari, "unet_mimari"), (segmentasyon, "segmentasyon"),
        (takip_kesisim, "takip_kesisim"),
        (cozunurluk_fps, "cozunurluk_fps"),
    ]
    for fn, ad in isler:
        print(fn(os.path.join(out, "b67_%s.png" % ad)))
