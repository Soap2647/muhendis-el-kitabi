# -*- coding: utf-8 -*-
"""Bolum 56 - Veriyle Çalışmak diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV dosyalarını okur:
  b56_dongu_olcum.csv     döngü ve vektör süreleri (şekil 56.2)
  b56_irtifa_dagilim.csv  ham irtifa ve birim bayrağı (şekil 56.6)
  b56_aykiri_ucus.csv     tek uçuşun irtifa serisi (şekil 56.7)
  b56_eksik_olcum.csv     eksik veri yöntemleri (şekil 56.8)
  b56_olcek_knn.csv       ölçekleme ve k-NN doğruluğu (şekil 56.10)
Diğer şekiller analitik olarak çizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _cizgi_hazirla(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(axis="y", color=RULE, linewidth=0.6)
    ax.set_axisbelow(True)


def sekil_bellek(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.text(0.2, 5.6, "Bellekte düz dizi (a, 3×4, int32; her hücre 4 bayt)",
            fontsize=10, color=INK, weight="bold")
    xs = [0.3 + 0.78 * k for k in range(12)]
    gorunum = {1, 2, 5, 6, 9, 10}
    for k in range(12):
        ana = FILL[1] if k in gorunum else FILL[0]
        _box(ax, xs[k], 4.2, 0.72, 0.8, str(k), fill=ana,
             edge=EDGE[1] if k in gorunum else EDGE[0], fs=10)
        ax.text(xs[k] + 0.36, 4.05, "%d" % (4 * k), ha="center",
                fontsize=7, color=MUTED)
    ax.text(0.2, 3.55, "bayt ofseti (hücrenin altında)", fontsize=8,
            color=MUTED)
    ax.text(0.2, 2.9, "a[:, 1:3]: görünüm (aynı bellek)",
            fontsize=9, color=EDGE[1], weight="bold")
    for k, deger in enumerate([1, 2, 5, 6, 9, 10]):
        _box(ax, 0.3 + 0.78 * k, 2.2, 0.72, 0.55, str(deger),
             fill=FILL[1], edge=EDGE[1], fs=9)
    ax.text(0.2, 1.7, "a[[0,2]]: gelişmiş indeksleme, yeni bellek",
            fontsize=9, color=ACCENT, weight="bold")
    for k, deger in enumerate([0, 1, 2, 3, 8, 9, 10, 11]):
        _box(ax, 0.3 + 0.78 * k, 0.9, 0.72, 0.55, str(deger),
             fill=FILL[3], edge=ACCENT, fs=9)
    _save(fig, path)


def sekil_olcum(path):
    veri = _oku("b56_dongu_olcum.csv")
    n = np.array([float(r["n"]) for r in veri])
    d = np.array([float(r["dongu_s"]) for r in veri])
    v = np.array([float(r["vektor_s"]) for r in veri])
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.loglog(n, d, "o-", color=ACCENT, lw=1.8, label="Python döngüsü")
    ax.loglog(n, v, "s-", color=EDGE[0], lw=1.8,
              label="NumPy vektörleştirilmiş")
    for x, a, b in zip(n, d, v):
        ax.annotate("%.0f×" % (a / b), (x, a), textcoords="offset points",
                    xytext=(6, 6), fontsize=8, color=MUTED)
    ax.set_xlabel("dizi uzunluğu n", color=INK)
    ax.set_ylabel("süre (saniye, medyan)", color=INK)
    ax.legend(frameon=False, fontsize=9)
    _cizgi_hazirla(ax)
    fig.tight_layout()
    _save(fig, path)


def sekil_yayin(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ornekler = [
        ("(3, 4)", "(4,)", "(3, 4)", FILL[1], EDGE[1]),
        ("(3, 1)", "(1, 4)", "(3, 4)", FILL[1], EDGE[1]),
        ("(5,)", "(5, 1)", "(5, 5)", FILL[3], ACCENT),
    ]
    ax.text(0.2, 9.4, "Şekil hizalama: sağdan eşleştir, 1 her boyuta uyar",
            fontsize=10, weight="bold", color=INK)
    for i, (a, b, c, f, e) in enumerate(ornekler):
        y = 6.8 - i * 2.5
        ax.text(0.3, y + 0.9, "A = %s" % a, fontsize=10, color=INK)
        ax.text(3.2, y + 0.9, "B = %s" % b, fontsize=10, color=INK)
        ax.text(6.0, y + 0.9, "sonuç = %s" % c, fontsize=10,
                color=e, weight="bold")
        _box(ax, 0.3, y - 0.4, 2.2, 0.6, "A: sağdan hizalı", fill=FILL[0],
             edge=EDGE[0], fs=8)
        _box(ax, 3.2, y - 0.4, 2.2, 0.6, "B: sağdan hizalı", fill=FILL[0],
             edge=EDGE[0], fs=8)
        _box(ax, 6.0, y - 0.4, 2.2, 0.6, "çıktı: " + c, fill=f, edge=e,
             fs=9, bold=True)
    ax.text(0.3, 0.4, "Kural: (5,)+(5,1) → (5,5). Ortalamayı (5,1) "
            "şeklinde tutmazsak tüm çiftler hesaplanır.",
            fontsize=8, color=MUTED)
    _save(fig, path)


def sekil_split(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 0.2, 2.2, 2.6, 1.6, "ham tablo\n(arac_id, hiz)", fill=FILL[0],
         edge=EDGE[0], fs=10)
    gruplar = ["IHA-01", "IHA-02", "IHA-03"]
    ort = ["ort(hız)", "ort(hız)", "ort(hız)"]
    for k, g in enumerate(gruplar):
        y = 4.3 - k * 1.4
        _box(ax, 4.0, y, 2.4, 1.0, "grup: " + g, fill=FILL[1],
             edge=EDGE[1], fs=9)
        _arrow(ax, 2.8, 3.0, 4.0, y + 0.5, col=MUTED, lw=1.0)
        _box(ax, 7.4, y, 2.6, 1.0, "ortalama hız\n" + ort[k],
             fill=FILL[2], edge=EDGE[2], fs=9)
        _arrow(ax, 6.4, y + 0.5, 7.4, y + 0.5, col=MUTED, lw=1.0)
    _box(ax, 11.0, 2.2, 2.8, 1.6, "birleşik tablo\n(araç başına 1 satır)",
         fill=FILL[4], edge=EDGE[4], fs=9)
    ax.text(0.2, 0.3, "split: anahtara göre böl  ·  apply: her grupta "
            "işlem yap  ·  combine: sonuçları birleştir", fontsize=8,
            color=MUTED)
    _save(fig, path)


def sekil_merge(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.text(0.2, 7.5, "Sol tablo (A, A, B, C) ile sağ tablo (A, A, A, B) "
            "birleşince", fontsize=10, weight="bold", color=INK)
    _box(ax, 0.3, 4.6, 3.2, 2.2, "sol\narac: A, A, B, C", fill=FILL[0],
         edge=EDGE[0], fs=9)
    _box(ax, 4.2, 4.6, 3.2, 2.2, "sağ\narac: A, A, A, B", fill=FILL[1],
         edge=EDGE[1], fs=9)
    _box(ax, 8.2, 4.6, 5.4, 2.2,
         "anahtar A: 2 × 3 = 6 satır\nanahtar B: 1 × 1 = 1 satır\n"
         "anahtar C: yalnız solda", fill=FILL[3], edge=ACCENT, fs=9)
    cikti = [("inner", "7 satır", "yalnız ortak anahtarlar"),
             ("left", "8 satır", "sol tümü, C'nin sağı NaN"),
             ("outer", "8 satır", "iki tablonun tümü")]
    for k, (ad, sayi, aciklama) in enumerate(cikti):
        x = 0.3 + k * 4.6
        _box(ax, x, 1.0, 4.2, 2.6, "how=%s\n%s\n%s" % (ad, sayi,
             aciklama), fill=FILL[2], edge=EDGE[2], fs=9)
    _arrow(ax, 1.9, 4.6, 2.4, 3.6, col=MUTED, lw=1.0)
    _arrow(ax, 5.8, 4.6, 2.4, 3.6, col=MUTED, lw=1.0)
    ax.text(0.3, 0.4, "validate=\"many_to_one\" bu tabloda hata verir: "
            "sağda anahtar tekil değil.", fontsize=8, color=MUTED)
    _save(fig, path)


def sekil_mft(path):
    veri = _oku("b56_irtifa_dagilim.csv")
    x = np.array([float(r["irtifa"]) for r in veri])
    b = np.array([int(r["birim_ft"]) for r in veri])
    bins = np.arange(0, 1000, 10)
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.hist([x[b == 0], x[b == 1]], bins=bins, stacked=True,
            color=[EDGE[0], ACCENT],
            label=["m birimi (v1 yazılım)", "ft birimi (v2 yazılım)"])
    ax.set_xlabel("ham irtifa değeri (birim karışık)", color=INK)
    ax.set_ylabel("satır sayısı", color=INK)
    ust = ax.get_ylim()[1]
    ax.text(150, ust * 0.92, "≈ 120 m tepesi", fontsize=9, color=EDGE[0])
    ax.text(420, ust * 0.55, "≈ 400 ft tepesi\n(≈ 122 m)", fontsize=9,
            color=ACCENT)
    ax.legend(frameon=False, fontsize=9)
    _cizgi_hazirla(ax)
    fig.tight_layout()
    _save(fig, path)


def sekil_aykiri(path):
    veri = _oku("b56_aykiri_ucus.csv")
    adim = np.array([int(r["adim"]) for r in veri])
    irt = np.array([float(r["irtifa"]) for r in veri])
    gps = np.array([int(r["gps"]) for r in veri])
    ariza = np.array([int(r["ariza"]) for r in veri])
    alt = float(veri[0]["alt"])
    ust = float(veri[0]["ust"])
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.axhspan(alt, ust, color=FILL[1], alpha=0.8,
               label="global IQR sınırları")
    ax.fill_between(adim, 0, 1, where=ariza == 1,
                    transform=ax.get_xaxis_transform(), color=RULE,
                    alpha=0.6, label="arıza penceresi (etiket 1)")
    ax.plot(adim, irt, color=EDGE[0], lw=1.2, label="irtifa (m)")
    ax.scatter(adim[gps == 1], irt[gps == 1], marker="x", s=60,
               color=ACCENT, label="GPS sıçraması (gerçek)")
    ax.set_xlabel("uçuş içinde adım (2 sn)", color=INK)
    ax.set_ylabel("irtifa (m)", color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    _cizgi_hazirla(ax)
    fig.tight_layout()
    _save(fig, path)


def sekil_eksik(path):
    veri = _oku("b56_eksik_olcum.csv")
    mekler = ["MCAR", "MAR", "MNAR"]
    yontemler = ["silme", "ortalama", "medyan", "knn"]
    renk = [MUTED, EDGE[0], EDGE[2], EDGE[1]]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    genislik = 0.2
    for j, yo in enumerate(yontemler):
        vals = []
        for mek in mekler:
            r = [q for q in veri if q["mekanizma"] == mek
                 and q["yontem"] == yo][0]
            vals.append(float(r["sd_orani"]))
        ax.bar(np.arange(3) + (j - 1.5) * genislik, vals, genislik,
               color=renk[j], label=yo)
    ax.axhline(np.sqrt(0.8), color=ACCENT, ls="--", lw=1.2,
               label="ortalama doldurmanın beklenen oranı √0,8 = 0,894")
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(mekler)
    ax.set_ylim(0.7, 1.1)
    ax.set_ylabel("std(doldurulmuş) / std(gerçek)", color=INK)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center")
    _cizgi_hazirla(ax)
    fig.tight_layout()
    _save(fig, path)


def sekil_dongusel(path):
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(-1.6, 3.8)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")
    t = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.cos(t), np.sin(t), color=RULE, lw=2)
    for h in range(24):
        a = 2 * np.pi * h / 24 - np.pi / 2
        x, y = np.cos(a), np.sin(a)
        vurgu = h in (0, 23)
        ax.scatter(x, y, s=120 if vurgu else 40,
                   color=ACCENT if vurgu else EDGE[0], zorder=3)
        if h % 3 == 0 or vurgu:
            ax.text(1.18 * x, 1.18 * y, "%02d" % h, ha="center",
                    va="center", fontsize=8, color=INK)
    ax.text(0.0, 0.0, "saat\n(döngüsel)", ha="center", va="center",
            fontsize=9, color=MUTED)
    ax.text(1.9, 0.9, "sin/cos kodlama:\n23 ile 0 yan yanadır",
            fontsize=9, color=INK)
    ax.text(1.9, 0.1, "ham fark |23 − 0| = 23", fontsize=9, color=MUTED)
    ax.text(1.9, -0.6, "çember üzerinde uzaklık ≈ 0,261", fontsize=9,
            color=ACCENT)
    _save(fig, path)


def sekil_olcek(path):
    veri = _oku("b56_olcek_knn.csv")
    ad = [r["olcekleme"] for r in veri]
    acc = np.array([float(r["dogruluk"]) for r in veri])
    sd = np.array([float(r["std"]) for r in veri])
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.bar(ad, acc, yerr=sd, capsize=5,
           color=[MUTED, EDGE[0], EDGE[1], EDGE[2]])
    for k, v in enumerate(acc):
        ax.text(k, v + 0.03, "%.3f" % v, ha="center", fontsize=9,
                color=INK)
    ax.set_ylim(0.8, 1.02)
    ax.set_ylabel("k-NN doğruluğu (5 katlı CV)", color=INK)
    _cizgi_hazirla(ax)
    fig.tight_layout()
    _save(fig, path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sekil_bellek(os.path.join(OUT, "b56_bellek.png"))
    sekil_olcum(os.path.join(OUT, "b56_olcum.png"))
    sekil_yayin(os.path.join(OUT, "b56_yayin.png"))
    sekil_split(os.path.join(OUT, "b56_split_apply.png"))
    sekil_merge(os.path.join(OUT, "b56_merge.png"))
    sekil_mft(os.path.join(OUT, "b56_mft.png"))
    sekil_aykiri(os.path.join(OUT, "b56_aykiri.png"))
    sekil_eksik(os.path.join(OUT, "b56_eksik.png"))
    sekil_dongusel(os.path.join(OUT, "b56_dongusel.png"))
    sekil_olcek(os.path.join(OUT, "b56_olcek.png"))
    print("10 sekil uretildi")
