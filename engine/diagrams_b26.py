# -*- coding: utf-8 -*-
"""Bölüm 26 - 'Process & Thread' diyagramları.

Ölçüm şekilleri engine/veri/ altındaki CSV'leri okur:
  b26_gantt.csv    -> zamanlayıcı simülatörü (sched_sim.py)
  b26_baglam.csv   -> sistem çağrısı / bağlam / oluşturma ölçümü
  b26_gil.csv      -> GIL thread/process ölçümü (gil_olcum.py)
Diğer şekiller bölümdeki örnek değerlerden çizilir.
"""
import csv
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")


def _yol(ad):
    return os.path.join(OUT, "b26_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. Program ve süreç -------------------------------------------------- #
def program_surec(path):
    fig, ax = _tuval(10.0, 5.2, 14, 7.2)
    ax.text(3.0, 6.7, "Disk: ./msh (ikili dosya)", ha="center",
            fontsize=11, weight="bold", color=INK)
    _box(ax, 0.6, 4.6, 4.8, 1.5, "kod (text)\nbaşlangıç verisi (data)\n"
         "sıfırlanmış veri (bss)", fill=FILL[0], edge=EDGE[0], fs=10)
    _box(ax, 0.6, 2.4, 4.8, 1.8, "ELF başlığı\nsembol tablosu\n"
         "yükleyici için bilgi", fill=FILL[4], edge=EDGE[4], fs=10)
    ax.text(3.0, 1.7, "Program: pasif bir dosya, CPU'da çalışmaz",
            ha="center", fontsize=9.5, color=MUTED)

    _arrow(ax, 5.6, 4.0, 7.0, 4.0, col=ACCENT, lw=2.0)
    ax.text(6.3, 4.4, "exec()", ha="center", fontsize=10, color=ACCENT)
    ax.text(6.3, 3.5, "yükler", ha="center", fontsize=9, color=MUTED)

    ax.text(9.4, 6.7, "Bellek: çalışan süreç (örnek)", ha="center",
            fontsize=11, weight="bold", color=INK)
    bolgeler = [("stack (yukarı büyür)", FILL[2], EDGE[2], 5.4),
                ("boş alan", "#FFFFFF", RULE, 4.6),
                ("heap (aşağı büyür)", FILL[1], EDGE[1], 3.8),
                ("data + bss", FILL[0], EDGE[0], 3.0),
                ("text (makine kodu)", FILL[3], EDGE[3], 2.2)]
    for metin, f, e, y in bolgeler:
        _box(ax, 7.3, y, 4.1, 0.7, metin, fill=f, edge=e, fs=9.5)

    _box(ax, 11.8, 2.2, 2.0, 3.9,
         "PCB\nPID\ndurum\nPC, SP\nCR3\naçık dosyalar",
         fill=FILL[4], edge=EDGE[4], fs=8.5)
    ax.text(12.8, 1.6, "(Linux: task_struct)", ha="center", fontsize=8.5,
            color=MUTED)
    _save(fig, path)


# 2. Süreç durumları --------------------------------------------------- #
def durum_makinesi(path):
    fig, ax = _tuval(10.5, 5.2, 14, 6.4)
    _box(ax, 0.4, 3.4, 2.4, 1.2, "YENİ\n(oluşturuldu)", fill=FILL[0],
         edge=EDGE[0], fs=10)
    _box(ax, 4.0, 3.4, 2.4, 1.2, "HAZIR\n(READY)", fill=FILL[1],
         edge=EDGE[1], fs=10)
    _box(ax, 7.4, 3.4, 2.6, 1.2, "ÇALIŞIYOR\n(RUNNING)", fill=FILL[2],
         edge=EDGE[2], fs=10, bold=True)
    _box(ax, 4.0, 0.6, 2.4, 1.2, "BEKLİYOR\n(WAITING)", fill=FILL[3],
         edge=EDGE[3], fs=10)
    _box(ax, 11.4, 3.4, 2.4, 1.2, "ZOMBİ\n(bitti, PCB\nduruyor)",
         fill=FILL[3], edge=EDGE[3], fs=9)
    _arrow(ax, 2.8, 4.0, 4.0, 4.0)
    ax.text(3.4, 4.5, "fork()", ha="center", fontsize=9, color=MUTED)
    _arrow(ax, 6.4, 4.3, 7.4, 4.3, col=ACCENT)
    ax.text(6.9, 4.9, "seçti", ha="center", fontsize=8.5, color=ACCENT)
    _arrow(ax, 7.4, 3.7, 6.4, 3.7, col=ACCENT_L)
    ax.text(6.9, 2.9, "dilim bitti\nkesildi", ha="center", fontsize=8.5,
            color=ACCENT_L)
    _arrow(ax, 8.6, 3.4, 6.4, 1.8, col=ACCENT_L, rad=0.1)
    ax.text(9.6, 1.9, "G/Ç veya olay\nbekleniyor", ha="left",
            fontsize=8.5, color=ACCENT_L)
    _arrow(ax, 4.4, 1.8, 4.6, 3.4, col=ACCENT_L, rad=0.0)
    ax.text(2.2, 2.4, "olay gerçekleşti", ha="center", fontsize=8.5,
            color=ACCENT_L)
    _arrow(ax, 10.0, 4.0, 11.4, 4.0, col=ACCENT)
    ax.text(10.7, 4.5, "exit()", ha="center", fontsize=8.5, color=ACCENT)
    ax.text(12.6, 2.4, "wait() ile toplanır:\nPCB serbest bırakılır",
            ha="center", fontsize=8.5, color=MUTED)
    _save(fig, path)


# 3. fork ve kopyala-yazarken-kopyala ------------------------------- #
def fork_cow(path):
    fig, ax = _tuval(10.5, 5.0, 14, 7)
    ax.text(3.5, 6.6, "(a) fork() hemen sonra", ha="center",
            fontsize=10.5, weight="bold")
    _box(ax, 0.4, 4.3, 2.4, 1.2, "ebeveyn\nsayaç=10", fill=FILL[0],
         edge=EDGE[0], fs=9.5)
    _box(ax, 4.6, 4.3, 2.4, 1.2, "çocuk\n(kopya)", fill=FILL[1],
         edge=EDGE[1], fs=9.5)
    _box(ax, 2.2, 1.4, 2.6, 1.2, "fiziksel çerçeve F1\nsayaç = 10",
         fill=FILL[2], edge=EDGE[2], fs=9.5)
    _arrow(ax, 1.6, 4.3, 2.8, 2.6, col=EDGE[0])
    _arrow(ax, 5.8, 4.3, 4.4, 2.6, col=EDGE[1])
    ax.text(5.6, 3.2, "ikisi de salt-okunur", fontsize=8.5,
            color=ACCENT, ha="left")

    ax.text(10.4, 6.6, "(b) çocuk yazdıktan sonra", ha="center",
            fontsize=10.5, weight="bold")
    _box(ax, 8.2, 4.3, 2.4, 1.2, "ebeveyn\nsayaç=10", fill=FILL[0],
         edge=EDGE[0], fs=9.5)
    _box(ax, 11.2, 4.3, 2.4, 1.2, "çocuk\nsayaç=15", fill=FILL[1],
         edge=EDGE[1], fs=9.5)
    _box(ax, 7.6, 1.4, 2.6, 1.2, "F1\nsayaç = 10", fill=FILL[2],
         edge=EDGE[2], fs=9.5)
    _box(ax, 10.8, 1.4, 2.6, 1.2, "F2 (kopya)\nsayaç = 15",
         fill=FILL[3], edge=EDGE[3], fs=9.5)
    _arrow(ax, 9.4, 4.3, 8.9, 2.6, col=EDGE[0])
    _arrow(ax, 12.4, 4.3, 12.1, 2.6, col=EDGE[1])
    ax.text(10.4, 0.7, "Yazma sayfa hatası: çekirdek F2'yi ayırır;\n"
            "yalnızca yazan süreç yeni kopyaya bağlanır",
            ha="center", fontsize=8.5, color=MUTED)
    _save(fig, path)


# 4. Süreç ağacı ------------------------------------------------------- #
def fork_agaci(path):
    """fork_agac.c'nin üç turu. Kenar etiketi = tur no."""
    fig, ax = _tuval(10.6, 6.0, 14, 7.4)
    kon = {"P0": (7.0, 6.1), "P1": (3.0, 4.4), "P2": (7.0, 4.4),
           "P4": (11.0, 4.4), "P3": (1.6, 2.7), "P5": (4.6, 2.7),
           "P6": (7.0, 2.7), "P7": (1.6, 0.9)}
    kenarlar = [("P0", "P1", 1), ("P0", "P2", 2), ("P1", "P3", 2),
                ("P0", "P4", 3), ("P1", "P5", 3), ("P2", "P6", 3),
                ("P3", "P7", 3)]
    for ana, cocuk, tur in kenarlar:
        (x1, y1), (x2, y2) = kon[ana], kon[cocuk]
        ax.plot([x1, x2], [y1 - 0.35, y2 + 0.35], color=MUTED, lw=1.0,
                zorder=0)
        ax.text((x1 + x2) / 2.0 + 0.15, (y1 + y2) / 2.0, "tur %d" % tur,
                fontsize=8, color=ACCENT_L, ha="left")
    for ad, (x, y) in kon.items():
        f = FILL[1] if ad == "P0" else FILL[0]
        e = EDGE[1] if ad == "P0" else EDGE[0]
        _box(ax, x - 0.6, y - 0.35, 1.2, 0.7, ad, fill=f, edge=e, fs=10,
             bold=(ad == "P0"))
    ax.text(9.2, 1.4, "tur 1: 1 → 2 süreç,  2 satır\n"
            "tur 2: 2 → 4 süreç,  4 satır\n"
            "tur 3: 4 → 8 süreç,  8 satır\n"
            "tamponsuz toplam: 14 satır", fontsize=8.5, color=INK,
            va="center")
    ax.text(7.0, 0.1, "Her kutu bir süreç. Her ebeveyn her turda fork "
            "yapar; çocuk 0 döndürür.", ha="center", fontsize=8.5,
            color=MUTED)
    _save(fig, path)


# 5. Boru hattı dosya tanımlayıcı tablosu ---------------------------- #
def boru_fd(path):
    fig, ax = _tuval(10.6, 5.8, 14, 8)
    ax.text(3.5, 7.6, "dup2 öncesi (grep süreci)", ha="center",
            fontsize=10, weight="bold")
    satirlar_once = ["0  klavye (stdin)", "1  ekran (stdout)",
                     "2  stderr", "3  p1 okuma ucu", "4  p1 yazma ucu",
                     "5  p2 okuma ucu", "6  p2 yazma ucu"]
    for i, s in enumerate(satirlar_once):
        _box(ax, 0.6, 6.4 - i * 0.78, 5.8, 0.6, s, fill=FILL[0],
             edge=EDGE[0], fs=8.5)
    ax.text(10.8, 7.6, "dup2 sonrası (grep)", ha="center",
            fontsize=10, weight="bold")
    satirlar_sonra = ["0  p1 okuma ucu  (dup2: p1 okuma → 0)",
                      "1  p2 yazma ucu  (dup2: p2 yazma → 1)",
                      "2  stderr", "3  p1 okuma (kapatılır)",
                      "4  p1 yazma (kapatılır)", "5  p2 okuma (kapatılır)",
                      "6  p2 yazma (kapatılır)"]
    for i, s in enumerate(satirlar_sonra):
        f = FILL[1] if i in (0, 1, 2) else FILL[3]
        e = EDGE[1] if i in (0, 1, 2) else EDGE[3]
        _box(ax, 7.6, 6.4 - i * 0.78, 6.2, 0.6, s, fill=f, edge=e, fs=7.6)
    _arrow(ax, 6.6, 3.9, 7.5, 3.9, col=ACCENT, lw=2.0)
    ax.text(7.0, 4.3, "dup2", ha="center", fontsize=9, color=ACCENT)
    ax.text(7.0, 0.5, "Kapatma: dup2 sonrası kopyalar gereksizdir; yazma "
            "ucu açık kalırsa\nokuyan süreç dosya sonu (EOF) alamaz ve "
            "askıda kalır.", ha="center", fontsize=8.5, color=MUTED)
    _save(fig, path)


# 6-7. Gantt şemaları -------------------------------------------------- #
RENK = {"P1": FILL[0], "P2": FILL[1], "P3": FILL[2], "P4": FILL[4],
        "A": FILL[0], "B": FILL[1], "C": FILL[2], "D": FILL[4],
        "E": FILL[3], "F": FILL[3]}
KENAR = {"P1": EDGE[0], "P2": EDGE[1], "P3": EDGE[2], "P4": EDGE[4],
         "A": EDGE[0], "B": EDGE[1], "C": EDGE[2], "D": EDGE[4],
         "E": EDGE[3], "F": EDGE[3]}


def _gantt_satirlari(ornek, algoritmalar, path, baslik, xmax,
                     ortalamalar):
    rows = [r for r in _csv("b26_gantt.csv") if r["ornek"] == ornek]
    h = 1.2 * len(algoritmalar) + 1.8
    fig, ax = plt.subplots(figsize=(10.2, h))
    ax.set_xlim(-0.6, xmax + 0.6)
    ax.set_ylim(-0.4, len(algoritmalar) + 0.2)
    ax.axis("off")
    ax.text(xmax / 2.0, len(algoritmalar) + 0.05, baslik,
            ha="center", fontsize=10.5, weight="bold", color=INK)
    for k, algo in enumerate(algoritmalar):
        y = len(algoritmalar) - 1 - k
        ax.text(-0.4, y + 0.3, algo, ha="right", va="center",
                fontsize=9.5, color=INK)
        for r in rows:
            if r["algoritma"] != algo:
                continue
            bas, son = int(r["bas"]), int(r["son"])
            surec = r["surec"]
            ax.add_patch(Rectangle((bas, y), son - bas, 0.7,
                                   facecolor=RENK.get(surec, FILL[0]),
                                   edgecolor=KENAR.get(surec, EDGE[0]),
                                   lw=1.0))
            ax.text((bas + son) / 2.0, y + 0.35, surec, ha="center",
                    va="center", fontsize=9, color=INK)
        ax.text(xmax + 0.5, y + 0.35, ortalamalar[algo], ha="left",
                va="center", fontsize=8.5, color=MUTED)
    for t in range(0, xmax + 1, 2):
        ax.text(t, -0.25, str(t), ha="center", fontsize=8, color=MUTED)
    _save(fig, path)


def gantt_kitap(path):
    _gantt_satirlari("kitap", ["FCFS", "SJF", "RR q=4"], path,
                     "Kitap örneği: P1=24, P2=3, P3=3 (hepsi t=0)",
                     30,
                     {"FCFS": "ort. bekl. 17,00", "SJF": "ort. bekl. 3,00",
                      "RR q=4": "ort. bekl. 5,67"})


def gantt_altili(path):
    _gantt_satirlari("altili", ["RR q=2", "MLFQ"], path,
                     "Altılı örnek: RR (q=2) ve MLFQ Gantt şeması",
                     28,
                     {"RR q=2": "ort. bekl. 9,67",
                      "MLFQ": "ort. bekl. 10,83"})


# 8. Bağlam ve sistem çağrısı maliyeti -------------------------------- #
def maliyet_grafigi(path):
    rows = _csv("b26_baglam.csv")

    def med(ad):
        v = [float(r["deger_ns"]) for r in rows if r["olcum"] == ad]
        return statistics.median(v)

    etiket = [
        ("sistem çağrısı (getppid)", med("syscall_getppid")),
        ("boru ping-pong (iş parçacığı)", med("pingpong_is_cpu0")),
        ("boru ping-pong (süreç)", med("pingpong_surec_cpu0")),
        ("iş parçacığı oluştur+bekle", med("olustur_is")),
        ("süreç oluştur (fork)+bekle", med("olustur_surec")),
    ]
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    y = list(range(len(etiket)))[::-1]
    degerler = [v / 1000.0 for _, v in etiket]        # mikrosaniye
    renk = [FILL[1], FILL[0], FILL[0], FILL[2], FILL[3]]
    kenar = [EDGE[1], EDGE[0], EDGE[0], EDGE[2], EDGE[3]]
    ax.barh(y, degerler, color=renk, edgecolor=kenar, height=0.6)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([e for e, _ in etiket], fontsize=9.5)
    for yi, v in zip(y, degerler):
        metin = ("%.2f µs" % v) if v < 10 else ("%.1f µs" % v)
        ax.text(v * 1.15, yi, metin.replace(".", ","), va="center",
                fontsize=9, color=INK)
    ax.set_xlabel("ortalama süre (mikrosaniye, log ölçek)", fontsize=9.5)
    ax.set_xlim(0.1, 800)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=RULE, lw=0.6)
    ax.set_axisbelow(True)
    _save(fig, path)


# 9. Süreç ve iş parçacığı bellek resmi ------------------------------ #
def bellek_resmi(path):
    fig, ax = _tuval(10.6, 5.6, 14, 8)
    ax.text(3.4, 7.6, "İki süreç: iki ayrı adres uzayı", ha="center",
            fontsize=10.5, weight="bold")
    for i, x in enumerate([0.4, 3.0]):
        _box(ax, x, 1.0, 2.3, 0.9, "text", fill=FILL[3], edge=EDGE[3],
             fs=9)
        _box(ax, x, 2.0, 2.3, 0.9, "data/bss", fill=FILL[0],
             edge=EDGE[0], fs=9)
        _box(ax, x, 3.0, 2.3, 0.9, "heap", fill=FILL[1], edge=EDGE[1],
             fs=9)
        _box(ax, x, 4.4, 2.3, 1.2, "stack", fill=FILL[2], edge=EDGE[2],
             fs=9)
        ax.text(x + 1.15, 5.9, "süreç %d" % (i + 1), ha="center",
                fontsize=9.5, weight="bold")
    ax.text(3.4, 0.2, "Bellek kopyalanır veya ayrılır: biri öbürünün "
            "sayfasını görmez", ha="center", fontsize=8.5, color=MUTED)

    ax.text(10.4, 7.6, "Bir süreç, iki iş parçacığı", ha="center",
            fontsize=10.5, weight="bold")
    _box(ax, 8.2, 1.0, 4.6, 0.9, "text (paylaşılır)", fill=FILL[3],
         edge=EDGE[3], fs=9)
    _box(ax, 8.2, 2.0, 4.6, 0.9, "data/bss (paylaşılır)", fill=FILL[0],
         edge=EDGE[0], fs=9)
    _box(ax, 8.2, 3.0, 4.6, 0.9, "heap (paylaşılır)", fill=FILL[1],
         edge=EDGE[1], fs=9)
    _box(ax, 8.2, 4.2, 2.2, 1.6, "yığın A\nyazmaçlar A\nTLS A",
         fill=FILL[2], edge=EDGE[2], fs=8.5)
    _box(ax, 10.6, 4.2, 2.2, 1.6, "yığın B\nyazmaçlar B\nTLS B",
         fill=FILL[4], edge=EDGE[4], fs=8.5)
    ax.text(10.4, 6.2, "PID aynı, TID farklı", ha="center", fontsize=9,
            color=MUTED)
    ax.text(10.4, 0.2, "Yığın ve yazmaçlar ayrı; geri kalan her şey "
            "paylaşılır", ha="center", fontsize=8.5, color=MUTED)
    _save(fig, path)


# 10. GIL ölçümü ------------------------------------------------------- #
def gil_grafigi(path):
    rows = _csv("b26_gil.csv")
    senaryolar = ["cpu_sirali", "cpu_thread4", "cpu_process4",
                  "io_sirali", "io_thread8", "io_process8"]
    etiket = ["CPU\nsıralı", "CPU\niş parçacığı x4", "CPU\nsüreç x4",
              "G/Ç\nsıralı", "G/Ç\niş parçacığı x8", "G/Ç\nsüreç x8"]
    ort, hata = [], []
    for s in senaryolar:
        v = [float(r["sure_s"]) for r in rows if r["senaryo"] == s]
        ort.append(statistics.mean(v))
        hata.append((max(v) - min(v)) / 2.0)
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    renk = [FILL[0], FILL[2], FILL[1], FILL[0], FILL[2], FILL[1]]
    kenar = [EDGE[0], EDGE[2], EDGE[1], EDGE[0], EDGE[2], EDGE[1]]
    x = list(range(len(senaryolar)))
    ax.bar(x, ort, yerr=hata, color=renk, edgecolor=kenar, capsize=4,
           width=0.62)
    for xi, v in zip(x, ort):
        ax.text(xi, v + 0.12, ("%.2f sn" % v).replace(".", ","),
                ha="center", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, fontsize=9)
    ax.set_ylabel("süre (sn), 3 tekrarın ortalaması", fontsize=9.5)
    ax.set_ylim(0, 3.0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)
    _save(fig, path)


def main():
    program_surec(_yol("program_surec"))
    durum_makinesi(_yol("durum_makinesi"))
    fork_cow(_yol("fork_cow"))
    fork_agaci(_yol("fork_agaci"))
    boru_fd(_yol("boru_fd"))
    gantt_kitap(_yol("gantt_kitap"))
    gantt_altili(_yol("gantt_altili"))
    maliyet_grafigi(_yol("maliyet"))
    bellek_resmi(_yol("bellek_resmi"))
    gil_grafigi(_yol("gil"))
    print("tamam: 10 şekil")


if __name__ == "__main__":
    main()
