# -*- coding: utf-8 -*-
"""Bolum 73 - olcum sekilleri. Veri engine/veri/b73_*.csv dosyalarindan
okunur (deney betikleri uretir). Kavramsal sekiller diagrams_b73.py'de."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from diagrams import ACCENT, EDGE, FILL, INK, MUTED, RULE, _save
from diagrams_b73 import GORSEL, VERI, oku
import csv
import os


def _cek(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def etiket_egrisi(path):
    rows = _cek("b73_etiket_egri.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    stil = {"piksel": (MUTED, ":", "ham piksel"),
            "pca": (MUTED, "-.", "PCA(50)"),
            "rastgele": (MUTED, "--", "rastgele ağ"),
            "simclr": (ACCENT, "-", "SimCLR"),
            "vicreg": (EDGE[0], "-", "VICReg"),
            "simsiam": (EDGE[2], "-", "SimSiam"),
            "simclr_ince": (EDGE[1], "-", "SimCLR + ince ayar"),
            "denetimli": (EDGE[4], "-", "denetimli (sıfırdan)")}
    ns = [10, 50, 100, 500]
    for yo, (c, ls, lab) in stil.items():
        ort, sd = [], []
        for n in ns:
            v = [float(r["dogruluk"]) for r in rows
                 if r["yontem"] == yo and int(r["n_sinif"]) == n]
            ort.append(np.mean(v))
            sd.append(np.std(v, ddof=1) if len(v) > 1 else 0.0)
        ort, sd = np.array(ort), np.array(sd)
        ax.plot(ns, ort, ls, color=c, lw=1.8, marker="o", ms=4, label=lab)
        if np.any(sd > 0):
            ax.fill_between(ns, ort - sd, ort + sd, color=c, alpha=0.15,
                            lw=0)
    ax.axhline(0.25, color=RULE, lw=1)
    ax.text(10.5, 0.255, "şans (4 sınıf)", fontsize=8, color=MUTED)
    ax.set_xscale("log")
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel("sınıf başına etiket sayısı (log eksen)")
    ax.set_ylabel("test doğruluğu")
    ax.set_ylim(0.2, 1.0)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
    return _save(fig, os.path.join(GORSEL, path))


def tau_batch(path):
    rows = _cek("b73_ablasyon.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    tau = [r for r in rows if r["grup"] == "tau"]
    tau.sort(key=lambda r: float(r["deger"]))
    tv = np.array([float(r["deger"]) for r in tau])
    y100 = np.array([float(r["yoklama100"]) for r in tau])
    y500 = np.array([float(r["yoklama500"]) for r in tau])
    a1.semilogx(tv, y500, "o-", color=ACCENT, label="n = 500")
    a1.semilogx(tv, y100, "s--", color=EDGE[0], label="n = 100")
    a1.set_xlabel("sıcaklık τ (log)")
    a1.set_ylabel("yoklama doğruluğu")
    a1.grid(alpha=0.25)
    a1.legend(frameon=False, fontsize=8)
    bat = [r for r in rows if r["grup"] == "batch"]
    bat.sort(key=lambda r: int(r["deger"]))
    lab = [r["deger"] for r in bat]
    b500 = [float(r["yoklama500"]) for r in bat]
    a2.bar(lab, b500, color=[FILL[0], FILL[1], FILL[2]], edgecolor=EDGE[0])
    a2.set_ylim(0.0, 1.0)
    a2.set_xlabel("batch boyutu (adım sayısı sabit)")
    a2.set_ylabel("yoklama doğruluğu (n = 500)")
    for i, v in enumerate(b500):
        a2.text(i, v + 0.02, "%.3f" % v, ha="center", fontsize=8)
    a2.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, path))


def artirma_grafik(path):
    rows = [r for r in _cek("b73_ablasyon.csv") if r["grup"] == "artirma"]
    y100 = [float(r["yoklama100"]) for r in rows]
    y500 = [float(r["yoklama500"]) for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.bar(x - 0.2, y100, 0.4, color=EDGE[0], label="n = 100")
    ax.bar(x + 0.2, y500, 0.4, color=ACCENT, label="n = 500")
    for i in range(len(rows)):
        ax.text(x[i] - 0.2, y100[i] + 0.01, "%.2f" % y100[i], ha="center",
                fontsize=7)
        ax.text(x[i] + 0.2, y500[i] + 0.01, "%.2f" % y500[i], ha="center",
                fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(["tam", "kırpma\nyok", "renk\nyok", "gri\nyok",
                        "aynalama\nyok", "hiçbiri"], fontsize=9)
    ax.set_ylabel("yoklama doğruluğu")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25, axis="y")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    return _save(fig, os.path.join(GORSEL, path))


def cokme_grafik(path):
    rows = _cek("b73_cokme.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.9))
    stil = {"simsiam_dur": (EDGE[1], "SimSiam (stop-gradient)"),
            "simsiam_dursuz": (ACCENT, "SimSiam (stop-gradient yok)"),
            "simclr": (MUTED, "SimCLR (referans)")}
    for yo, (c, lab) in stil.items():
        s = [r for r in rows if r["yontem"] == yo]
        a = [int(r["adim"]) for r in s]
        a1.plot(a, [float(r["std"]) for r in s], "o-", color=c, ms=3,
                label=lab)
        a2.plot(a, [float(r["knn"]) for r in s], "o-", color=c, ms=3,
                label=lab)
    a1.set_ylim(-0.05, 1.15)
    a1.set_xlabel("adım")
    a1.set_ylabel("std ölçütü (1 = çökme yok)")
    a2.set_xlabel("adım")
    a2.set_ylabel("k-NN doğruluğu (n = 500)")
    a2.set_ylim(0.2, 1.0)
    for a in (a1, a2):
        a.grid(alpha=0.25)
    a1.legend(frameon=False, fontsize=7, loc="center right")
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, path))


def hizalama_grafik(path):
    rows = _cek("b73_hizalama.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ad = {"piksel": "ham piksel", "rastgele": "rastgele ağ",
          "simclr": "SimCLR", "vicreg": "VICReg", "simsiam": "SimSiam"}
    renk = {"piksel": MUTED, "rastgele": MUTED, "simclr": ACCENT,
            "vicreg": EDGE[0], "simsiam": EDGE[1]}
    for r in rows:
        x, y = float(r["hizalama"]), float(r["tekduzelik"])
        ax.scatter(x, y, s=70, color=renk[r["yontem"]], zorder=3)
        ax.annotate("%s (k-NN %.2f)" % (ad[r["yontem"]],
                                        float(r["knn500"])),
                    (x, y), textcoords="offset points", xytext=(7, 4),
                    fontsize=8)
    ax.set_xlabel("hizalama (küçük = iyi)")
    ax.set_ylabel("tekdüzelik (küçük = iyi)")
    ax.grid(alpha=0.25)
    return _save(fig, os.path.join(GORSEL, path))


def tsne_grafik(path):
    rows = _cek("b73_tsne.csv")
    yontemler = ["piksel", "rastgele", "simclr", "vicreg"]
    ad = {"piksel": "ham piksel", "rastgele": "rastgele ağ",
          "simclr": "SimCLR", "vicreg": "VICReg"}
    fig, axs = plt.subplots(2, 2, figsize=(8.6, 7.4))
    renk = [ACCENT, EDGE[0], EDGE[1], EDGE[2]]
    sek = ["daire", "kare", "üçgen", "artı"]
    for ax, yo in zip(axs.ravel(), yontemler):
        s = [r for r in rows if r["yontem"] == yo]
        for k in range(4):
            p = np.array([(float(r["x"]), float(r["y"])) for r in s
                          if int(r["sekil"]) == k])
            ax.scatter(p[:, 0], p[:, 1], s=8, color=renk[k], label=sek[k])
        ax.set_title(ad[yo], fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    axs[0, 0].legend(frameon=False, fontsize=8, markerscale=2)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, path))


def clip_sonuc(path):
    mat = _cek("b73_clip_matris.csv")
    rows = _cek("b73_clip.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                 gridspec_kw={"width_ratios": [1, 1.25]})
    M = np.array([[float(r[str(i)]) for i in range(4)] for r in mat])
    im = a1.imshow(M, cmap="RdBu_r", vmin=-0.3, vmax=1.0)
    a1.set_xticks(range(4))
    a1.set_yticks(range(4))
    a1.set_yticklabels([r["ornek"].replace(" ", chr(10)) for r in mat], fontsize=7)
    for i in range(4):
        for j in range(4):
            a1.text(j, i, "%.2f" % M[i, j], ha="center", va="center",
                    fontsize=8, color=INK)
    a1.set_title("benzerlik matrisi (maskeli)", fontsize=9)
    fig.colorbar(im, ax=a1, fraction=0.046)
    grup = [("renk_sekil_gorulen", "renk+şekil\ngörülen"),
            ("renk_sekil_gorulmemis", "renk+şekil\ngörülmemiş"),
            ("tam_cumle_topluluk_gorulen", "topluluk\ngörülen"),
            ("tam_cumle_topluluk_gorulmemis", "topluluk\ngörülmemiş")]
    for k, var in enumerate(["naif", "maskeli"]):
        vals = []
        for o, _ in grup:
            v = [float(r["deger"]) for r in rows if r["varyant"] == var
                 and r["olcut"] == o]
            vals.append(v[0])
        a2.bar(np.arange(4) + (k - 0.5) * 0.36, vals, 0.36,
               color=[MUTED, ACCENT][k], label=var)
    a2.set_xticks(range(4))
    a2.set_xticklabels([t for _, t in grup], fontsize=7)
    a2.axhline(1 / 16, color=RULE, lw=1)
    a2.text(2.6, 1 / 16 + 0.02, "şans (1/16)", fontsize=7, color=MUTED)
    a2.set_ylabel("16 sınıflı doğruluk")
    a2.set_ylim(0, 1.0)
    a2.legend(frameon=False, fontsize=8)
    a2.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, path))


if __name__ == "__main__":
    for f in (etiket_egrisi, tau_batch, artirma_grafik, cokme_grafik,
              hizalama_grafik, tsne_grafik, clip_sonuc):
        print(f.__name__, f("b73_%s.png" % f.__name__.replace("_grafik", "")
                             .replace("_sonuc", "")))
