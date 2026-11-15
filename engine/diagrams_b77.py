# -*- coding: utf-8 -*-
"""Bolum 77 - MLOps diyagramlari.

Olcum grafikleri (77.8, 77.9) engine/veri/b77_*.csv dosyalarindan okunur;
bu CSV'leri b77 deney betikleri uretir. Kavramsal sekiller veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import math
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _fig, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tuval(w, h, xl, yl):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.axis("off")
    return fig, ax


def ok(ax, x1, y1, x2, y2, kesik=False, col=ACCENT):
    """Kutu kenarindan kenarina ok; dogrudan iki nokta arasinda."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4,
                                linestyle="--" if kesik else "-",
                                shrinkA=0, shrinkB=0))


# --------------------------------------------------------------------------- #
def teknik_borc(path):
    """Sculley'in (2015) tarzi: ML kodu kucuk, cevresindeki altyapi buyuk."""
    fig, ax = tuval(9.6, 5.6, (0, 16), (0, 10))
    cevre = [(0.4, 7.4, "Veri toplama"), (4.2, 8.4, "Veri doğrulama"),
             (8.2, 8.4, "Özellik çıkarma"),
             (11.9, 7.4, "Kaynak yönetimi"), (11.9, 4.3, "Süreç yönetimi"),
             (11.9, 1.2, "İzleme"), (8.2, 0.4, "Sunum / servis"),
             (4.2, 0.4, "Analiz araçları"), (0.4, 1.2, "Yapılandırma"),
             (0.4, 4.3, "Veri altyapısı")]
    for x, y, t in cevre:
        ax.plot([x + 1.7, 8.0], [y + 0.5, 5.0], color=RULE, lw=1.0,
                zorder=0)
    for x, y, t in cevre:
        _box(ax, x, y, 3.4, 1.0, t, FILL[0], EDGE[0], fs=9.5)
    _box(ax, 6.0, 3.9, 4.0, 2.2, "ML kodu\n(küçük bir kutu)",
         FILL[2], EDGE[2], fs=11, bold=True)
    return _save(fig, path)


def yasam_dongusu(path):
    fig, ax = tuval(9.6, 5.4, (0, 10), (0, 10))
    dugumler = [(90, "1. Problem\ntanımı"), (30, "2. Veri\n(toplama, sürüm)"),
                (-30, "3. Eğitim\n(deney takibi)"),
                (-90, "4. Değerlendirme\n(kalite kapısı)"),
                (-150, "5. Dağıtım\n(kayıt defteri)"),
                (150, "6. İzleme\n(kayma, metrikler)")]
    konum = []
    for i, (aci, metin) in enumerate(dugumler):
        x = 5 + 3.2 * math.cos(math.radians(aci))
        y = 5 + 3.3 * math.sin(math.radians(aci))
        konum.append((x, y))
        _box(ax, x - 1.45, y - 0.6, 2.9, 1.2, metin, FILL[i % 5],
             EDGE[i % 5], fs=9.5, bold=True)
    for i in range(6):
        x1, y1 = konum[i]
        x2, y2 = konum[(i + 1) % 6]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=ACCENT,
                                    lw=1.5, shrinkA=44, shrinkB=44))
    ax.text(5, 5.0, "sürekli döngü", ha="center", va="center",
            fontsize=10, color=MUTED, style="italic")
    return _save(fig, path)


def icerik_adresli(path):
    fig, ax = tuval(9.6, 5.4, (0, 10), (0, 6))
    _box(ax, 0.2, 4.2, 2.6, 1.2, "telemetri.csv\n(büyük dosya)",
         FILL[0], EDGE[0], fs=9.5)
    _box(ax, 3.7, 4.2, 2.4, 1.2, "SHA-256\nözeti: 8d71...",
         FILL[2], EDGE[2], fs=9.5)
    _box(ax, 6.6, 4.2, 3.2, 1.2,
         "depo/8d/7116f4...\n(içerik, bir kez)", FILL[1], EDGE[1], fs=9.5)
    ok(ax, 2.8, 4.8, 3.7, 4.8)
    ok(ax, 6.1, 4.8, 6.6, 4.8)
    _box(ax, 0.2, 1.2, 3.2, 1.4,
         "telemetri.csv.veri\n(işaretçi: yol, sha256, boyut)",
         FILL[3], EDGE[3], fs=9)
    ok(ax, 1.5, 4.2, 1.5, 2.6, kesik=True, col=MUTED)
    ax.text(1.6, 3.35, "yazılır", fontsize=8.5, color=MUTED)
    _box(ax, 4.2, 1.2, 2.8, 1.4, "git deposu\n(yalnız işaretçi)",
         FILL[1], EDGE[1], fs=9.5)
    ok(ax, 3.4, 1.9, 4.2, 1.9)
    _box(ax, 7.6, 1.2, 2.2, 1.4, "geri yükleme\n(özet yeniden\nhesaplanır)",
         FILL[4], EDGE[4], fs=8.5)
    ok(ax, 8.2, 4.2, 8.7, 2.6, kesik=True, col=MUTED)
    ax.text(8.85, 3.2, "bozulma\nkontrolü", fontsize=8.5, color=MUTED)
    return _save(fig, path)


def deney_modeli(path):
    fig, ax = tuval(9.6, 6.4, (0, 10), (0, 7))
    _box(ax, 0.2, 3.9, 3.2, 2.9,
         "deney\nid (anahtar)\nad\nzaman\ngit (commit)\nveri (özet)\nortam",
         FILL[0], EDGE[0], fs=9.5)
    _box(ax, 6.2, 4.5, 3.4, 1.9,
         "parametre\ndeney (yabancı)\nanahtar\ndeğer", FILL[2], EDGE[2],
         fs=9.5)
    _box(ax, 6.2, 2.0, 3.4, 1.9,
         "metrik\ndeney (yabancı)\nanahtar\ndeğer (sayı)", FILL[1],
         EDGE[1], fs=9.5)
    _box(ax, 0.2, 0.3, 3.2, 2.2,
         "artefakt\ndeney (yabancı)\nyol\nsha256", FILL[3], EDGE[3], fs=9.5)
    ok(ax, 3.4, 5.4, 6.2, 5.4, col=ACCENT_L)
    ok(ax, 3.4, 4.6, 6.2, 3.0, col=ACCENT_L)
    ok(ax, 1.8, 3.9, 1.8, 2.5, col=ACCENT_L)
    ax.text(3.6, 5.6, "1 : N", fontsize=8.5, color=MUTED)
    ax.text(3.6, 3.3, "1 : N", fontsize=8.5, color=MUTED)
    ax.text(1.95, 2.9, "1 : N", fontsize=8.5, color=MUTED)
    return _save(fig, path)


def kalite_kapisi(path):
    fig, ax = tuval(9.6, 5.2, (0, 10), (0, 6))
    ust = [(0.2, "Kod\n(git commit)", FILL[0], EDGE[0]),
           (2.2, "Veri\ndoğrulama", FILL[2], EDGE[2]),
           (4.2, "Eğitim\n(tohum, deney)", FILL[1], EDGE[1]),
           (6.2, "Ölçütler\n(baz ile kıyas)", FILL[4], EDGE[4]),
           (8.3, "Kalite\nkapısı", FILL[3], EDGE[3])]
    for x, t, f, e in ust:
        _box(ax, x, 4.2, 1.6, 1.3, t, f, e, fs=8.8)
    for x in [1.8, 3.8, 5.8, 7.8]:
        ok(ax, x, 4.85, x + 0.4, 4.85)
    _box(ax, 6.2, 1.1, 1.8, 1.3, "Kayıt defteri\n(staging)",
         FILL[1], EDGE[1], fs=8.8)
    _box(ax, 3.0, 1.1, 2.0, 1.3, "Üretim\n(production)",
         FILL[0], EDGE[0], fs=8.8, bold=True)
    _box(ax, 0.2, 1.1, 2.0, 1.3, "RED: yayın\nyok", FILL[3], EDGE[3],
         fs=8.8, bold=True)
    ok(ax, 8.7, 4.2, 7.4, 2.4)
    ax.text(8.1, 3.3, "geçti", fontsize=8.5, color=MUTED)
    ok(ax, 6.2, 1.75, 5.0, 1.75)
    ok(ax, 3.0, 1.75, 2.2, 1.75, kesik=True, col=MUTED)
    ok(ax, 3.0, 4.2, 1.6, 2.4, kesik=True, col=MUTED)
    ax.text(0.2, 3.0, "veri hatası: eğitim\nbaşlamadan durur",
            fontsize=8.2, color=MUTED)
    ax.text(2.6, 2.5, "kapı reddeder", fontsize=8.2, color=MUTED)
    return _save(fig, path)


def dagitim_kaliplari(path):
    fig, ax = tuval(9.6, 6.4, (0, 10), (0, 7.5))
    satirlar = [
        (6.1, "Gölge (shadow)", "aday, trafiğin kopyasını alır;\nyanıt kullanıcıya gitmez",
         "yanıt yok"),
        (3.9, "Kanarya", "trafiğin %2'si adaya gider;\nkötüyse geri dönülür",
         "%2 trafik"),
        (1.7, "A/B testi", "kullanıcılar rastgele iki kola\nayrılır, metrikler kıyaslanır",
         "%50 atama"),
    ]
    for y, ad, aciklama, etiket in satirlar:
        ax.text(0.2, y + 0.55, ad, fontsize=9.5, weight="bold", color=INK)
        ax.text(0.2, y - 0.45, aciklama, fontsize=7.6, color=MUTED,
                va="top")
        _box(ax, 3.3, y - 0.35, 1.2, 0.7, "İstek", FILL[0], EDGE[0],
             fs=8.5)
        _box(ax, 5.0, y - 0.35, 1.4, 0.7, "Yönlendirici", FILL[2],
             EDGE[2], fs=8)
        _box(ax, 6.95, y + 0.25, 1.5, 0.7, "Taban model", FILL[1],
             EDGE[1], fs=8)
        _box(ax, 6.95, y - 0.85, 1.5, 0.7, "Aday model", FILL[3],
             EDGE[3], fs=8)
        ok(ax, 4.5, y, 5.0, y)
        ok(ax, 6.4, y + 0.2, 6.95, y + 0.6, col=ACCENT_L)
        ok(ax, 6.4, y - 0.2, 6.95, y - 0.5, kesik=True, col=MUTED)
        ax.text(8.6, y - 0.1, "kullanıcı", fontsize=7.5, color=MUTED)
        ax.text(5.0, y - 0.95, etiket, fontsize=7.2, color=MUTED,
                ha="left")
    return _save(fig, path)


def drift_turleri(path):
    fig, ax = tuval(9.6, 4.2, (0, 10), (0, 6))
    kartlar = [
        (0.2, "Kovaryat kayması", "p(x) değişir\np(y|x) aynı",
         "Sensör ısındı: girdi\ndağılımı kaydı"),
        (3.5, "Etiket kayması", "p(y) değişir\np(x|y) aynı",
         "Arıza oranı kışta\nyükseldi"),
        (6.8, "Kavram kayması", "p(y|x) değişir",
         "Aynı girdi artık\nbaşka sonuç veriyor"),
    ]
    for i, (x, ad, formul, ornek) in enumerate(kartlar):
        _box(ax, x, 0.4, 3.0, 5.2, "", FILL[i], EDGE[i])
        ax.text(x + 1.5, 5.1, ad, ha="center", fontsize=10.5,
                weight="bold", color=EDGE[i])
        ax.text(x + 1.5, 3.6, formul, ha="center", va="center",
                fontsize=10, color=INK)
        ax.text(x + 1.5, 1.6, "Örnek:\n" + ornek, ha="center",
                va="center", fontsize=8.6, color=MUTED)
    return _save(fig, path)


def drift_akis(path):
    veri = oku("b77_drift_seri.csv")
    s = [r for r in veri if r["tohum"] == "11"]
    x = np.array([int(r["pencere"]) for r in s])
    psi = np.array([float(r["psi_max"]) for r in s])
    alan = np.array([float(r["alan_auc"]) for r in s])
    auc = np.array([float(r["auc"]) for r in s])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.6, 6.0), sharex=True)
    a1.plot(x, psi, color=ACCENT_L, lw=1.2, label="en büyük PSI")
    a1.axhline(0.2, color=ACCENT, ls="--", lw=1.0, label="PSI eşiği 0,2")
    a1.axhline(0.05, color=MUTED, ls=":", lw=1.0,
               label="PSI eşiği 0,05")
    a1.set_ylabel("PSI")
    a1.set_ylim(0, 1.1)
    a1.legend(fontsize=8, frameon=False, loc="upper left")
    a2.plot(x, alan, color=EDGE[1], lw=1.2,
            label="alan sınıflandırıcısı AUC")
    a2.axhline(0.6, color=ACCENT, ls="--", lw=1.0, label="eşik 0,6")
    a2.plot(x, auc, color=MUTED, lw=0.9, alpha=0.8,
            label="model AUC (pencere)")
    a2.set_ylabel("AUC")
    a2.set_ylim(0.4, 1.0)
    a2.set_xlabel("pencere (her biri 600 örnek)")
    a2.legend(fontsize=8, frameon=False, loc="center left")
    for a in (a1, a2):
        a.axvline(60, color=INK, lw=0.8, ls=":")
        a.axvline(90, color=INK, lw=0.8, ls=":")
        a.grid(alpha=0.25)
    a1.text(61, 0.95, "ortam kayması (60)", fontsize=8.5, color=INK)
    a1.text(91, 0.8, "kavram kayması (90)", fontsize=8.5, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def servis_carpikligi(path):
    veri = oku("b77_servis_auc.csv")
    varyant = ["dogru", "olcek_yok", "birim", "yuvarlama"]
    adlar = ["doğru", "ölçek yok", "birim\n(A → mA)", "gerilim\n(yuvarlama)"]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ort, tahmin = [], []
    for i, v in enumerate(varyant):
        satir = [r for r in veri if r["varyant"] == v]
        aucs = [float(r["auc"]) for r in satir]
        ort.append(np.mean(aucs))
        tahmin.append(np.mean([float(r["tahmin_degisimi"]) for r in satir]))
        ax.bar(i, np.mean(aucs), width=0.55, color=FILL[i % 5],
               edgecolor=EDGE[i % 5], lw=1.1)
        ax.plot([i] * len(aucs), aucs, "o", color=ACCENT, ms=5)
        ax.text(i, np.mean(aucs) + 0.03,
                "%.3f" % np.mean(aucs), ha="center", fontsize=9)
        ax.text(i, 0.07, "tahmin değişimi\n%%%.0f" % (100 * tahmin[-1]),
                ha="center", fontsize=8, color=MUTED)
    ax.axhline(0.5, color=MUTED, ls=":", lw=1.0)
    ax.text(1.5, 0.51, "rastgele (0,5)", fontsize=7.5, color=MUTED,
            ha="center", va="bottom")
    ax.set_xticks(range(4))
    ax.set_xticklabels(adlar, fontsize=9)
    ax.set_ylabel("test AUC (3 tohum ortalaması)")
    ax.set_ylim(0, 1.08)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    print(teknik_borc(os.path.join(GORSEL, "b77_teknik_borc.png")))
    print(yasam_dongusu(os.path.join(GORSEL, "b77_yasam_dongusu.png")))
    print(icerik_adresli(os.path.join(GORSEL, "b77_icerik_adresli.png")))
    print(deney_modeli(os.path.join(GORSEL, "b77_deney_modeli.png")))
    print(kalite_kapisi(os.path.join(GORSEL, "b77_kalite_kapisi.png")))
    print(dagitim_kaliplari(os.path.join(GORSEL, "b77_dagitim.png")))
    print(drift_turleri(os.path.join(GORSEL, "b77_drift_turleri.png")))
    print(drift_akis(os.path.join(GORSEL, "b77_drift_akis.png")))
    print(servis_carpikligi(os.path.join(GORSEL, "b77_servis_carpikligi.png")))
