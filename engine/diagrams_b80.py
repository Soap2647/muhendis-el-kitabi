# -*- coding: utf-8 -*-
"""Bolum 80 sekilleri: bitirme sistemi (uctan uca hat).
Olcum sekilleri engine/veri/b80_*.csv ve b80_ornek_sahne.npz
dosyalarindan okunur (Temp'e bagimlilik yok)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import csv
import os
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(HERE, "veri")
GOR = os.path.join(HERE, "..", "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def yol(ad):
    return os.path.join(GOR, ad)


def sekil_mimari():
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ust = [("Veri üretimi\n(sentetik sahne,\nvideo, OOD)", 0),
           ("Eğitim\n(GPU, 3 tohum)", 1),
           ("Değerlendirme\n(mAP, MOTA)", 2),
           ("Dışa aktarma\n(BN katlama,\nONNX, int8)", 3),
           ("Edge çıkarım\nhattı (CPU)", 4),
           ("Operatör\niz listesi +\nguvence", 5)]
    for metin, i in ust:
        renk = FILL[2] if i == 5 else FILL[0]
        kenar = EDGE[2] if i == 5 else EDGE[0]
        _box(ax, 0.2 + i * 2.3, 4.7, 1.9, 1.7, metin, fill=renk,
             edge=kenar, fs=8.5)
    for i in range(5):
        _arrow(ax, 2.1 + i * 2.3, 5.55, 2.5 + i * 2.3, 5.55,
               col=ACCENT, lw=1.4)
    _box(ax, 0.3, 1.2, 6.0, 1.7, "İzleme: PSI ve KS (girdi, skor),\n"
         "performans (3 pencere gecikmeli etiket)", fill=FILL[3],
         edge=EDGE[3], fs=9)
    _box(ax, 7.7, 1.2, 6.0, 1.7, "Yeniden eğitim tetiği\n"
         "(iki ardışık alarm, insan onayı)", fill=FILL[4],
         edge=EDGE[4], fs=9)
    _arrow(ax, 12.6, 4.65, 10.2, 2.95, col=MUTED, lw=1.2, rad=0.2)
    _arrow(ax, 6.3, 2.05, 7.65, 2.05, col=ACCENT, lw=1.4)
    _arrow(ax, 7.7, 2.6, 3.4, 4.6, col=MUTED, lw=1.2, rad=-0.25)
    ax.text(0.3, 3.55, "geri bildirim: yeni veri ve yeni sürüm",
            fontsize=8.5, color=MUTED)
    _save(fig, yol("b80_mimari.png"))


def sekil_hat():
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    adimlar = [
        ("Kare\n96x96 uint8", "sensör çıktısı"),
        ("Ön işleme\nfloat32 [0,1]", "normalizasyon"),
        ("Dedektör\nONNX int8", "çıktı 12x12x2x8"),
        ("Kod çözme\n+ NMS", "kutu, skor, sınıf"),
        ("Takipçi\nKalman + Macar", "iz kimliği"),
        ("Güvence\nskor, uyum", "otomatik / doğrulat"),
    ]
    for i, (metin, alt) in enumerate(adimlar):
        x = 0.2 + i * 2.3
        _box(ax, x, 3.0, 1.9, 1.6, metin, fill=FILL[i % 2],
             edge=EDGE[0], fs=8.5)
        ax.text(x + 0.95, 2.5, alt, ha="center", va="top", fontsize=7.5,
                color=MUTED)
        if i < len(adimlar) - 1:
            _arrow(ax, x + 1.9, 3.8, x + 2.25, 3.8, col=ACCENT, lw=1.3)
    ax.text(0.2, 1.1, "Her kutu bir sözleşmedir: biçim, veri türü ve "
            "aralık belirtilir.", fontsize=8.5, color=INK)
    ax.text(0.2, 0.5, "Güvence katmanı hem tespiti hem izi denetler; "
            "operatöre iz listesi yalnızca otomatik alarmlar için gider.",
            fontsize=8.5, color=INK)
    _save(fig, yol("b80_hat.png"))


def sekil_sahneler():
    d = np.load(os.path.join(VERI, "b80_ornek_sahne.npz"))
    satir = [("test", "Nominal (test)"), ("drift", "Operasyonel kayma"),
             ("ood", "OOD (kuş benzeri)")]
    fig, axes = plt.subplots(3, 3, figsize=(7.4, 7.8))
    for r, (ad, baslik) in enumerate(satir):
        for c in range(3):
            a = axes[r, c]
            a.imshow(d[ad + "_img"][c], cmap="gray", vmin=0, vmax=1)
            for j in range(8):
                if d[ad + "_gc"][c, j] < 0:
                    continue
                x1, y1, x2, y2 = d[ad + "_gt"][c, j]
                a.add_patch(plt.Rectangle((x1 - 0.5, y1 - 0.5), x2 - x1,
                                          y2 - y1, fill=False,
                                          edgecolor="#47624A", lw=1.1))
            a.set_xticks([])
            a.set_yticks([])
            if c == 0:
                a.set_ylabel(baslik, fontsize=8.5)
    fig.text(0.02, 0.01, "Yeşil kutu: etiketli nesne. OOD satırında "
             "kuş benzeri şekillerin etiketi yoktur.", fontsize=8,
             color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, yol("b80_sahneler.png"))


def sekil_tespit():
    d = np.load(os.path.join(VERI, "b80_ornek_sahne.npz"))
    satir = [("test", "Nominal (test)"), ("drift", "Operasyonel kayma"),
             ("ood", "OOD (kuş benzeri)")]
    fig, axes = plt.subplots(3, 3, figsize=(7.4, 7.8))
    for r, (ad, baslik) in enumerate(satir):
        for c in range(3):
            a = axes[r, c]
            a.imshow(d[ad + "_img"][c], cmap="gray", vmin=0, vmax=1)
            for j in range(8):
                if d[ad + "_gc"][c, j] >= 0:
                    x1, y1, x2, y2 = d[ad + "_gt"][c, j]
                    a.add_patch(plt.Rectangle((x1 - 0.5, y1 - 0.5),
                                              x2 - x1, y2 - y1,
                                              fill=False,
                                              edgecolor="#47624A",
                                              lw=0.9, ls="--"))
                if d[ad + "_dsk"][c, j] >= 0:
                    x1, y1, x2, y2 = d[ad + "_dk"][c, j]
                    a.add_patch(plt.Rectangle((x1 - 0.5, y1 - 0.5),
                                              x2 - x1, y2 - y1,
                                              fill=False,
                                              edgecolor="#8A2D2B",
                                              lw=1.2))
                    a.text(x1, y1 - 1.2, "%.2f" % d[ad + "_dsk"][c, j],
                           fontsize=6.5, color="#8A2D2B")
            a.set_xticks([])
            a.set_yticks([])
            if c == 0:
                a.set_ylabel(baslik, fontsize=8.5)
    fig.text(0.02, 0.01, "Kırmızı: tespit (skor >= 0,30). Kesikli yeşil: "
             "gerçek kutu.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    _save(fig, yol("b80_tespit.png"))


def sekil_karsilastirma():
    onnx = oku("b80_onnx.csv")
    gec = oku("b80_gecikme.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    yontemler = ["pytorch", "onnx_fp32", "onnx_int8"]
    kumeler = ["test", "drift", "ood"]
    genislik = 0.26
    for i, k in enumerate(kumeler):
        for j, y in enumerate(yontemler):
            v = [float(r["map50"]) for r in onnx
                 if r["yontem"] == y and r["kume"] == k][0]
            a1.bar(i + (j - 1) * genislik, v, genislik,
                   color=[EDGE[0], EDGE[1], ACCENT][j],
                   label=y if i == 0 else None)
            a1.text(i + (j - 1) * genislik, v + 0.01, "%.3f" % v,
                    ha="center", fontsize=6.5, rotation=90)
    a1.set_xticks(range(3))
    a1.set_xticklabels(["nominal", "kayma", "OOD"])
    a1.set_ylim(0.6, 1.0)
    a1.set_ylabel("mAP@0.5")
    a1.set_title("(a) Doğruluk", fontsize=10)
    a1.legend(fontsize=7.5, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.12), frameon=False)
    konf = [("fp32", 4), ("int8", 4), ("fp32", 1), ("int8", 1)]
    for i, (m, t) in enumerate(konf):
        v = [r for r in gec if r["model"] == m and r["asama"] == "toplam"
             and int(r["threads"]) == t][0]
        p50, p95 = float(v["p50_ms"]), float(v["p95_ms"])
        a2.bar(i, p50, 0.6, color=[EDGE[0], ACCENT, EDGE[0], ACCENT][i])
        a2.errorbar(i, p50, yerr=[[0], [p95 - p50]], color=INK, capsize=3)
        a2.text(i, p95 + 0.05, "%.2f" % p50, ha="center", fontsize=7.5)
    a2.set_xticks(range(4))
    a2.set_xticklabels(["fp32\n4 iş p.", "int8\n4 iş p.",
                        "fp32\n1 iş p.", "int8\n1 iş p."], fontsize=8)
    a2.set_ylabel("kare süresi (ms), p50 ve p95")
    a2.set_ylim(0, 1.45)
    a2.set_title("(b) Gecikme (CPU, uçtan uca)", fontsize=10)
    fig.tight_layout()
    _save(fig, yol("b80_karsilastirma.png"))


def sekil_bilesen():
    rows = oku("b80_gecikme_bilesen.csv")
    asamalar = ["on_isleme", "cikarim", "son_isleme", "takip", "guvence"]
    renk = [FILL[4], ACCENT_L, EDGE[2], EDGE[1], MUTED]
    senaryo = ["4_thread", "1_thread"]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    etiket = ["96x96, 4 iş parçacığı", "96x96, 1 iş parçacığı"]
    for i, s in enumerate(senaryo):
        sol = 0.0
        for a, c in zip(asamalar, renk):
            v = [float(r["p50_ms"]) for r in rows
                 if r["senaryo"] == s and r["asama"] == a][0]
            ax.barh(i, v, left=sol, color=c, edgecolor="white", height=0.55,
                    label=a if i == 0 else None)
            if v > 0.1:
                ax.text(sol + v / 2, i, "%.2f" % v, ha="center",
                        va="center", fontsize=7.5)
            sol += v
        ax.text(sol + 0.02, i, "p50 toplamı %.2f ms" % sol, va="center",
                fontsize=8)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(etiket, fontsize=8.5)
    ax.set_xlabel("kare başına süre, p50 (ms)")
    ax.set_xlim(0, 2.2)
    ax.legend(fontsize=7.5, ncol=5, loc="upper center",
              bbox_to_anchor=(0.5, 1.2), frameon=False)
    fig.tight_layout()
    _save(fig, yol("b80_bilesen.png"))


def sekil_takip():
    rows = oku("b80_takip_iz.csv")
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    renkler = [ACCENT, EDGE[0], EDGE[1], EDGE[2], EDGE[4], INK]
    for r in rows:
        if r["tip"] != "gt":
            continue
        t = int(r["kare"])
        cx = (float(r["x1"]) + float(r["x2"])) / 2
        ax.plot(t, cx, ".", color="#BBBBBB", ms=3.5)
    for r in rows:
        if r["tip"] != "iz":
            continue
        t = int(r["kare"])
        cx = (float(r["x1"]) + float(r["x2"])) / 2
        k = int(r["id"]) % len(renkler)
        ax.plot(t, cx, "o", color=renkler[k], ms=2.6)
    ax.plot([], [], ".", color="#BBBBBB", label="gerçek (GT)")
    for k in range(4):
        ax.plot([], [], "o", color=renkler[k], ms=4,
                label="iz %d" % (k + 1))
    ax.set_xlabel("kare")
    ax.set_ylabel("kutu merkezinin x konumu (piksel)")
    ax.legend(fontsize=7.5, ncol=5, loc="upper center",
              bbox_to_anchor=(0.5, 1.15), frameon=False)
    ax.text(3, 6, "Nesneler 0 ve 1 yaklaşık 35. karede kesişir; "
            "kimlik değişimi riski.", fontsize=7.5, color=MUTED)
    fig.tight_layout()
    _save(fig, yol("b80_takip.png"))


def sekil_guvence():
    rows = oku("b80_guvence.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    for kural, c, ls in [("tek_skor", EDGE[0], "-"),
                         ("topluluk", ACCENT, "-")]:
        sat = [r for r in rows if r["kural"] == kural and
               r["kume"] == "test"]
        x = [float(r["tau"]) for r in sat]
        a1.plot(x, [float(r["kapsama"]) for r in sat], color=c, ls=ls,
                label=kural)
        sat2 = [r for r in rows if r["kural"] == kural and
                r["kume"] == "ood"]
        a2.plot(x, [float(r["yanlis_alarm_gor"]) for r in sat2],
                color=c, ls=ls, label=kural)
    kor_ood = [r for r in rows if r["kural"] == "korumasiz"
               and r["kume"] == "ood"][0]
    kor_test = [r for r in rows if r["kural"] == "korumasiz"
                and r["kume"] == "test"][0]
    a2.axhline(float(kor_ood["yanlis_alarm_gor"]), color=MUTED, ls=":",
               lw=1.2)
    a1.axhline(float(kor_test["kapsama"]), color=MUTED, ls=":", lw=1.2)
    a1.set_xlabel("skor eşiği (tau)")
    a1.set_ylabel("kapsama (test, GT oranı)")
    a1.set_title("(a) Kapsama", fontsize=10)
    a1.legend(fontsize=8, loc="lower left")
    a2.set_xlabel("skor eşiği (tau)")
    a2.set_ylabel("OOD: görüntü başına yanlış alarm")
    a2.set_title("(b) Yanlış alarm", fontsize=10)
    a2.set_yscale("symlog", linthresh=0.1)
    fig.tight_layout()
    _save(fig, yol("b80_guvence.png"))


def sekil_drift():
    rows = oku("b80_izleme.csv")
    w = np.array([int(r["pencere"]) for r in rows])
    psi = np.array([float(r["psi"]) for r in rows])
    ksp = np.array([float(r["ks_p"]) for r in rows])
    mapE = np.array([float(r["map_eski"]) for r in rows])
    mapY = np.array([float(r["map_yeni"] or "nan") for r in rows])
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9.6, 6.2),
                                     sharex=True)
    for a in (a1, a2, a3):
        a.axvspan(20, 30, color=FILL[2], alpha=0.8, lw=0)
        a.axvline(24, color=ACCENT, lw=1.0, ls="--")
    a1.plot(w, psi, "-o", ms=3, color=EDGE[0])
    a1.axhline(0.2, color=ACCENT, ls=":", lw=1)
    a1.set_ylabel("PSI (girdi)")
    a2.semilogy(w, np.clip(ksp, 1e-6, 1), "-o", ms=3, color=EDGE[1])
    a2.axhline(0.01, color=ACCENT, ls=":", lw=1)
    a2.set_ylabel("KS p (skor)")
    a3.plot(w, mapE, "-o", ms=3, color=EDGE[0], label="eski model")
    a3.plot(w, mapY, "-s", ms=3, color=ACCENT, label="yeni model")
    a3.axhline(0.9341, color=MUTED, ls=":", lw=1)
    a3.set_ylabel("mAP@0.5")
    a3.set_xlabel("pencere (200 sahne)")
    a3.legend(fontsize=7.5, loc="lower left")
    a1.text(21, 2.6, "kayma (20-30)", fontsize=7.5, color=INK)
    a1.text(11.0, 1.6, "yeniden eğitim tetiği: pencere 24\n"
            "(kesikli çizgi)", fontsize=7.5, color=ACCENT)
    fig.tight_layout()
    _save(fig, yol("b80_drift.png"))


def sekil_kitap():
    satirlar = [
        ("I", "Programlama temelleri", "Python ile veri üretimi ve deney betikleri"),
        ("II", "Problem çözme ve hata ayıklama", "hata ayıklama, etiket hatası ayıklaması"),
        ("III", "Veri yapıları", "Kutu listeleri, izler, bağlı bileşenler"),
        ("IV", "Algoritmalar", "NMS, Macar eşleştirme, AP integrali"),
        ("V", "OOP ve tasarım", "izleyici, kayıt defteri arayüzleri"),
        ("VI", "İşletim sistemi", "önbellek ve çıkarım iş parçacığı"),
        ("VII", "Ağ", "kavramsal: sensör akışı ve operatör arayüzü"),
        ("VIII", "Veritabanı", "deney takipçisi (SQLite), kayıt defteri"),
        ("IX", "Derleyici", "ONNX grafı, operatör eşlemesi"),
        ("X", "Yazılım mühendisliği", "sürümleme (SHA-256), tekrarlanabilirlik"),
        ("XI", "Gömülü sistem", "Cortex-M sınıfı bellek bütçesi"),
        ("XII", "Matematik", "IoU, Kalman, PSI, KS testi"),
        ("XIII", "Sinyal ve paralel", "kare hattı, iş parçacığı sayısı"),
        ("XIV", "Makine öğrenmesi", "değerlendirme, eşik seçimi, takip"),
        ("XV", "Derin öğrenme", "MiniYolo, eğitim, BN katlama"),
        ("XVI", "ML mühendisliği", "kuantizasyon, güvence, izleme"),
    ]
    fig, ax = plt.subplots(figsize=(9.6, 7.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 17.2)
    ax.axis("off")
    ax.text(0.1, 16.9, "Kısım", fontsize=8.5, weight="bold", color=INK)
    ax.text(1.2, 16.9, "Konu", fontsize=8.5, weight="bold", color=INK)
    ax.text(4.6, 16.9, "Bitirme sistemindeki karşılığı", fontsize=8.5,
            weight="bold", color=INK)
    for i, (no, ad, kar) in enumerate(satirlar):
        y = 15.9 - i
        fill = FILL[i % 2]
        ax.add_patch(plt.Rectangle((0.0, y - 0.42), 10, 0.84,
                                   facecolor=fill, edgecolor="none"))
        ax.text(0.1, y, no, va="center", fontsize=8.2, color=ACCENT)
        ax.text(1.2, y, ad, va="center", fontsize=8.2, color=INK)
        ax.text(4.6, y, kar, va="center", fontsize=8.0, color=INK)
    _save(fig, yol("b80_kitap_haritasi.png"))


def main():
    sekil_mimari()
    sekil_hat()
    sekil_sahneler()
    sekil_tespit()
    sekil_karsilastirma()
    sekil_bilesen()
    sekil_takip()
    sekil_guvence()
    sekil_drift()
    sekil_kitap()


if __name__ == "__main__":
    main()
