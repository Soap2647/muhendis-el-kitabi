# -*- coding: utf-8 -*-
"""Bolum 44 - Kesme & Zamanlayici diyagramlari.

Olcum/simulasyon sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b44_nvic_senaryo.csv    -> nvic_sim.py (cevrim-duzeyi NVIC benzetimi)
  b44_gecikme.csv         -> nvic_sim.py (rastgele yuk, tohum=44)
  b44_setitimer_olcum.csv -> jitter.c (WSL2 / Linux ana bilgisayar olcumu)
  b44_rms_zaman.csv       -> rms_analiz.py (RM / EDF zaman cizelgesi)
Diger sekiller bolumdeki formullerden ve sabit degerlerden cizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")
MONO = {"family": "DejaVu Sans Mono"}


def _yol(ad):
    return os.path.join(OUT, "b44_%s.png" % ad)


def _csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ham_satirlar(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return f.read().split()[1:]


def _eksen(w, h, xl=(0, 10), yl=(0, 10)):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.axis("off")
    return fig, ax


# --------------------------------------------------------------------------
# Sekil 44.1: yoklama mi kesme mi
def yoklama_kesme():
    fig, ax = _eksen(9.6, 4.2, (0, 14), (0, 8))
    ax.text(0.2, 7.5, "Yoklama (polling)", fontsize=12, weight="bold",
            color=INK)
    ax.plot([0.5, 13.5], [5.6, 5.6], color=RULE, lw=2)
    for k in range(0, 8):
        x = 0.8 + k * 1.6
        ax.plot([x, x], [5.3, 5.9], color=INK, lw=1.2)
    ax.text(0.8, 5.0, "bayrak kontrolü", fontsize=9, color=MUTED)
    _arrow(ax, 3.05, 6.7, 3.05, 5.95, col=ACCENT, lw=1.6)
    ax.text(3.2, 6.6, "olay geldi", fontsize=9, color=ACCENT)
    _box(ax, 4.9, 4.45, 1.8, 0.7, "islem", fill=FILL[1], edge=EDGE[1], fs=9)
    ax.text(5.1, 3.9, "gecikme: bir sonraki yoklamaya kadar", fontsize=9,
            color=INK)
    ax.text(0.2, 2.7, "Kesme (interrupt)", fontsize=12, weight="bold",
            color=INK)
    ax.plot([0.5, 13.5], [1.2, 1.2], color=RULE, lw=2)
    _arrow(ax, 3.05, 2.5, 3.05, 1.3, col=ACCENT, lw=1.6)
    ax.text(3.2, 2.4, "olay geldi", fontsize=9, color=ACCENT)
    _box(ax, 3.4, 0.35, 2.4, 0.7, "kesme işleyicisi",
         fill=FILL[1], edge=EDGE[1], fs=9)
    ax.text(6.1, 0.55, "gecikme: birkaç çevrim (donanım kabul eder)",
            fontsize=9, color=INK)
    ax.text(10.9, 4.4, "CPU ana", fontsize=9, color=MUTED)
    ax.text(10.9, 4.0, "işi yapar", fontsize=9, color=MUTED)
    _save(fig, _yol("yoklama_kesme"))


# --------------------------------------------------------------------------
# Sekil 44.3: x86 IDT ile Cortex-M vektor tablosu
def x86_idt_nvic():
    fig, ax = _eksen(9.6, 5.0, (0, 15), (0, 10))
    ax.text(0.3, 9.5, "x86-64: IDT (256 kapı, 16 bayt)", fontsize=11,
            weight="bold", color=INK)
    satirlar = [("vektör 0  bölen-sıfır", "isr_stub_0"),
                ("vektör 14  sayfa hatası", "isr_stub_14"),
                ("vektör 32  IRQ0 zamanlayıcı", "irq_stub_0"),
                ("vektör 33  IRQ1 klavye", "irq_stub_1")]
    for i, (a, b) in enumerate(satirlar):
        y = 7.7 - i * 1.5
        _box(ax, 0.4, y, 3.8, 0.95, a, fill=FILL[0], edge=EDGE[0], fs=8.5)
        _box(ax, 5.1, y, 2.6, 0.95, b, fill=FILL[2], edge=EDGE[2], fs=8.5)
        _arrow(ax, 4.2, y + 0.47, 5.1, y + 0.47, col=ACCENT_L, lw=1.2)
    ax.text(0.4, 1.35, "lidt ile yüklenir; kapı tipi 0x8E = kesme kapısı",
            fontsize=8, color=MUTED)
    ax.text(0.4, 0.9, "(IF bayrağı otomatik silinir)", fontsize=8,
            color=MUTED)
    ax.plot([8.2, 8.2], [0.2, 9.4], color=RULE, lw=1.2)
    ax.text(8.5, 9.5, "Cortex-M4: vektör tablosu", fontsize=11,
            weight="bold", color=INK)
    tab = [("0  MSP başlangıç", "0x08000000"),
           ("1  Reset_Handler", "0x08000004"),
           ("2..15  istisnalar", "NMI, HardFault, SysTick"),
           ("16+28  IRQ28 TIM2", "0x080000B0"),
           ("16+37  IRQ37 USART1", "0x080000D4")]
    for i, (a, b) in enumerate(tab):
        y = 7.7 - i * 1.5
        _box(ax, 8.6, y, 2.7, 0.95, a, fill=FILL[0], edge=EDGE[0], fs=7.5)
        ax.text(11.5, y + 0.47, b, fontsize=7.5, color=INK, va="center",
                **MONO)
    ax.text(8.6, 0.6, "Bit 0 = 1 (Thumb). Tablo bellekte düz bir dizi;\n"
            "NVIC kesme numarasını dizin olarak kullanır.", fontsize=7.5,
            color=MUTED)
    _save(fig, _yol("x86_idt_nvic"))


# --------------------------------------------------------------------------
# Sekil 44.4: NVIC durumlari
def nvic_durum():
    fig, ax = _eksen(9.6, 4.6, (0, 14), (0, 9))
    _box(ax, 0.4, 3.5, 3.0, 1.6, "Pasif\n(inactive)", fill=FILL[0],
         edge=EDGE[0], fs=10, bold=True)
    _box(ax, 5.5, 6.4, 3.0, 1.6, "Bekliyor\n(pending)", fill=FILL[2],
         edge=EDGE[2], fs=10, bold=True)
    _box(ax, 5.5, 0.4, 3.0, 1.6, "Aktif\n(active)", fill=FILL[1],
         edge=EDGE[1], fs=10, bold=True)
    _box(ax, 10.6, 3.5, 3.1, 1.6, "Aktif + bekliyor", fill=FILL[3],
         edge=EDGE[3], fs=10, bold=True)
    _arrow(ax, 3.4, 4.6, 5.5, 7.0, col=ACCENT)
    ax.text(1.2, 7.3, "olay geldi\n(ISPR yazılır)", fontsize=8.5, color=INK)
    _arrow(ax, 7.0, 6.4, 7.0, 2.0, col=ACCENT)
    ax.text(7.2, 4.1, "kabul: öncelik\nve maske geçti", fontsize=8.5,
            color=INK)
    _arrow(ax, 5.5, 1.2, 3.4, 4.2, col=ACCENT_L)
    ax.text(0.6, 1.0, "bitti, bekleyen yok\n(dönüş)", fontsize=8.5,
            color=INK)
    _arrow(ax, 8.5, 1.6, 10.6, 3.9, col=ACCENT_L)
    ax.text(9.6, 1.0, "aynı kesme\nyeniden geldi", fontsize=8.5, color=INK)
    _arrow(ax, 10.6, 4.5, 8.5, 2.2, col=ACCENT_L)
    ax.text(11.4, 6.3, "bitince\ntekrar aktif", fontsize=8.5, color=INK)
    _save(fig, _yol("nvic_durum"))


# --------------------------------------------------------------------------
# Sekil 44.6: senaryo zaman cizelgeleri (CSV)
def ic_ice_kuyruk():
    veri = _csv("b44_nvic_senaryo.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    isimler = ["ic_ice", "kuyruk_zinciri", "gec_gelen"]
    etiket = {"ic_ice": "A: ic ice kesme",
              "kuyruk_zinciri": "B: kuyruk zinciri",
              "gec_gelen": "C: geç gelen kesme"}
    isleyici_renk = {"UART": EDGE[0], "ADC": EDGE[1], "TIM": EDGE[2]}
    faz_renk = {"E": FILL[2], "X": RULE, "L": FILL[4]}
    for satir, s in enumerate(isimler):
        y = 2.6 - satir * 1.0
        for r in [r for r in veri if r["senaryo"] == s]:
            t = int(r["zaman"])
            e = r["etiket"]
            if e == "H":
                renk = isleyici_renk[r["ad"]]
            elif e in faz_renk:
                renk = faz_renk[e]
            else:
                continue
            ax.broken_barh([(t, 1)], (y, 0.8), facecolors=renk)
        ax.text(-1.0, y + 0.4, etiket[s], ha="right", va="center",
                fontsize=9, color=INK)
    ax.set_xlim(0, 60)
    ax.set_ylim(0.2, 3.5)
    ax.set_yticks([])
    ax.set_xlabel("zaman (çevrim)", fontsize=9)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.legend(handles=[Patch(facecolor=FILL[2], label="E: yığınlama"),
                       Patch(facecolor=FILL[4], label="L: kuyruk zinciri"),
                       Patch(facecolor=RULE, label="X: çıkış"),
                       Patch(facecolor=EDGE[0], label="UART"),
                       Patch(facecolor=EDGE[1], label="ADC"),
                       Patch(facecolor=EDGE[2], label="TIM")],
              loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=6,
              fontsize=7.5, frameon=False)
    fig.subplots_adjust(left=0.25, bottom=0.25, top=0.95, right=0.97)
    _save(fig, _yol("ic_ice_kuyruk"))


# --------------------------------------------------------------------------
# Sekil 44.5: yigin cercevesi (bellek)
def yigin_cerceve():
    fig, ax = _eksen(9.6, 5.2, (0, 14), (0, 10))
    ax.text(0.2, 9.5, "Donanımın yığına koyduğu çerçeve (SP'den yukarı)",
            fontsize=10.5, weight="bold", color=INK)
    temel = [("R0", "SP + 0"), ("R1", "SP + 4"), ("R2", "SP + 8"),
             ("R3", "SP + 12"), ("R12", "SP + 16"), ("LR", "SP + 20"),
             ("PC (dönüş adresi)", "SP + 24"), ("xPSR", "SP + 28")]
    for i, (a, b) in enumerate(temel):
        y = 8.1 - i * 0.82
        _box(ax, 0.5, y, 3.4, 0.7, a, fill=FILL[0], edge=EDGE[0], fs=8.5)
        ax.text(4.2, y + 0.35, b, fontsize=8, color=MUTED, va="center",
                **MONO)
    ax.text(0.5, 1.2, "8 kelime = 32 bayt (temel çerçeve)", fontsize=8.5,
            color=INK)
    ax.plot([6.0, 6.0], [0.3, 9.3], color=RULE, lw=1.2)
    ext = [("S0 .. S15 (16 kelime)", "SP + 32 .. +92"),
           ("FPSCR", "SP + 96"), ("ayrilmis", "SP + 100")]
    ax.text(6.3, 9.0, "FPU bağlamı varsa (genişletilmiş çerçeve):",
            fontsize=8.5, color=INK)
    for i, (a, b) in enumerate(ext):
        y = 7.4 - i * 1.25
        _box(ax, 6.5, y, 3.5, 0.9, a, fill=FILL[2], edge=EDGE[2], fs=8.5)
        ax.text(10.2, y + 0.45, b, fontsize=8, color=MUTED, va="center",
                **MONO)
    ax.text(6.3, 2.9, "Toplam: 26 kelime = 104 bayt", fontsize=8.5,
            color=INK)
    ax.text(6.3, 2.2, "Tembel yığınlama: FP yazmaçları ilk FP komutunda\n"
            "gerçekten kaydedilir (genel bilgi, FPCCR.LSPEN).", fontsize=8,
            color=MUTED)
    ax.text(6.3, 0.6, "EXC_RETURN bit 4 = 0 -> genişletilmiş çerçeve",
            fontsize=8, color=MUTED)
    _save(fig, _yol("yigin_cerceve"))


# --------------------------------------------------------------------------
# Sekil 44.7: SPSC halka tamponu
def halka_tampon():
    fig, ax = _eksen(9.6, 4.6, (0, 17), (0, 9))
    bas, kuy = 1, 4
    for i in range(16):
        dolu = bas <= i < kuy
        fill = FILL[1] if dolu else FILL[0]
        _box(ax, 0.4 + i * 1.0, 4.0, 0.92, 0.9, str(i), fill=fill,
             edge=EDGE[0], fs=8)
    _arrow(ax, 1.86, 3.2, 1.86, 3.9, col=ACCENT_L, lw=1.4)
    ax.text(0.5, 2.7, "bas (tüketici yazar)", fontsize=9, color=ACCENT_L)
    _arrow(ax, 4.86, 3.2, 4.86, 3.9, col=ACCENT, lw=1.4)
    ax.text(3.9, 2.7, "kuyruk (üretici yazar)", fontsize=9, color=ACCENT)
    _box(ax, 0.4, 6.8, 7.2, 1.2,
         "Üretici (kesme işleyicisi):\nveri[kuyruk] = b; kuyruk = sonraki",
         fill=FILL[3], edge=EDGE[3], fs=8.5)
    _box(ax, 8.4, 6.8, 7.2, 1.2,
         "Tüketici (ana döngü): b = veri[bas]; bas = sonraki",
         fill=FILL[0], edge=EDGE[0], fs=8.5)
    ax.text(0.4, 1.4, "Kapasite 16, kullanılabilir 15 (boş bir yuva\n"
            "boş/dolu ayrımı için). Her indeks yalnızca bir taraf yazar.",
            fontsize=8.5, color=INK)
    ax.text(9.0, 1.4, "Derlenmiş kodda önce veri (strb), sonra indeks\n"
            "(str) yazılır: tek çekirdekte bu sıra korunur (genel bilgi).",
            fontsize=8.5, color=INK)
    _save(fig, _yol("halka_tampon"))


# --------------------------------------------------------------------------
# Sekil 44.9: zamanlayici blok diyagrami + PWM dalga bicimi
def zamanlayici_pwm():
    fig = plt.figure(figsize=(9.6, 7.0))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 1.0, 1.0])
    ax = fig.add_subplot(gs[0, :])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis("off")
    _box(ax, 0.2, 3.0, 2.4, 1.2, "f_tim\n84 MHz", fill=FILL[0],
         edge=EDGE[0], fs=9)
    _box(ax, 3.4, 3.0, 2.4, 1.2, "PSC\n(+1 bölücü)", fill=FILL[1],
         edge=EDGE[1], fs=9)
    _box(ax, 6.6, 3.0, 2.6, 1.2, "CNT  0..ARR", fill=FILL[1],
         edge=EDGE[1], fs=9)
    _box(ax, 9.9, 3.0, 2.0, 1.2, "karşılaştır\nCCR", fill=FILL[2],
         edge=EDGE[2], fs=9)
    _box(ax, 12.2, 3.0, 1.6, 1.2, "çıkış\nPWM", fill=FILL[3],
         edge=EDGE[3], fs=9)
    _arrow(ax, 2.6, 3.6, 3.4, 3.6, col=ACCENT_L)
    _arrow(ax, 5.8, 3.6, 6.6, 3.6, col=ACCENT_L)
    _arrow(ax, 9.2, 3.6, 9.9, 3.6, col=ACCENT_L)
    _arrow(ax, 11.9, 3.6, 12.2, 3.6, col=ACCENT_L)
    _box(ax, 6.6, 0.4, 2.6, 1.2, "taşma: olay/kesme", fill=FILL[4],
         edge=EDGE[4], fs=8.5)
    _arrow(ax, 7.9, 3.0, 7.9, 1.6, col=ACCENT_L)
    ax.text(0.2, 0.6, "f_guncelleme = f_tim / ((PSC+1)(ARR+1))\n"
            "görev = CCR / (ARR+1)", fontsize=8.5, color=INK, **MONO)
    ax1 = fig.add_subplot(gs[1, 0])
    t = np.linspace(0, 2, 4000)
    duty = np.where((t % 1.0) < 0.375, 1, 0)
    ax1.step(t, duty, where="post", color=ACCENT, lw=1.6)
    ax1.set_ylim(-0.2, 1.4)
    ax1.set_yticks([0, 1])
    ax1.set_xlabel("zaman (ms)", fontsize=8)
    ax1.set_title("1 kHz, görev %37,5 (PSC=1, ARR=41999, CCR=15750)",
                  fontsize=8)
    ax1.tick_params(labelsize=7)
    ax2 = fig.add_subplot(gs[1, 1])
    t2 = np.linspace(0, 40, 8000)
    p = t2 % 20.0
    ax2.step(t2, np.where(p < 1.0, 1, 0), where="post", color=EDGE[0],
             lw=1.4)
    ax2.step(t2, np.where(p < 2.0, 1, 0) + 2.4, where="post",
             color=EDGE[3], lw=1.4)
    ax2.text(41.5, 0.5, "1 ms\n(CCR=3000)", fontsize=7, va="center")
    ax2.text(41.5, 2.9, "2 ms\n(CCR=6000)", fontsize=7, va="center")
    ax2.set_xlim(0, 52)
    ax2.set_ylim(-0.2, 3.8)
    ax2.set_yticks([])
    ax2.set_xlabel("zaman (ms)", fontsize=8)
    ax2.set_title("Servo 50 Hz: 1 ms ve 2 ms darbe", fontsize=8)
    ax2.tick_params(labelsize=7)
    ax3 = fig.add_subplot(gs[2, :])
    frek = np.array([50, 1000, 5000, 20000, 50000])
    arr = np.array([59999, 41999, 16799, 4199, 1679])
    bit = np.log2(arr + 1)
    ax3.semilogx(frek, bit, "o-", color=ACCENT, lw=1.5)
    for f, a in zip(frek, bit):
        ax3.annotate("%.1f bit" % a, (f, a), textcoords="offset points",
                     xytext=(0, 7), ha="center", fontsize=7.5)
    ax3.set_xlabel("PWM frekansı (Hz, log ölçek)", fontsize=8)
    ax3.set_ylabel("çözünürlük (bit)", fontsize=8)
    ax3.set_ylim(8, 18)
    ax3.tick_params(labelsize=7)
    ax3.set_title("Frekans-çözünürlük takası (16 bit ARR, f_tim = 84 MHz)",
                  fontsize=8)
    fig.tight_layout()
    _save(fig, _yol("zamanlayici_pwm"))


# --------------------------------------------------------------------------
# Sekil 44.8: gecikme dagilimi (simulasyon) ve jitter (ana bilgisayar)
def gecikme_dagilim():
    gec = _csv("b44_gecikme.csv")
    kesme = [float(r["gecikme_cevrim"]) for r in gec
             if r["tur"] == "kesme" and r["kaynak"] == "ADC"]
    yok = [float(r["gecikme_cevrim"]) for r in gec
           if r["tur"] == "yoklama"]
    jit = [float(s) - 1000.0 for s in _ham_satirlar("b44_setitimer_olcum.csv")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    bins = np.arange(0, 210, 5)
    a1.hist(yok, bins=bins, color=FILL[2], edgecolor=EDGE[2],
            label="yoklama (P=200)")
    a1.hist(kesme, bins=bins, color=EDGE[0], alpha=0.75,
            label="kesme (ADC)")
    a1.set_xlabel("gecikme (çevrim)", fontsize=8.5)
    a1.set_ylabel("örnek sayısı", fontsize=8.5)
    a1.set_title("(a) Benzetim, 300000 çevrim, tohum=44", fontsize=8.5)
    a1.legend(fontsize=7.5, frameon=False)
    a1.tick_params(labelsize=7.5)
    a2.hist(jit, bins=np.arange(-600, 650, 25), color=EDGE[1], alpha=0.85)
    a2.set_xlabel("aralık - 1000 us (sapma, us)", fontsize=8.5)
    a2.set_title("(b) WSL2 setitimer, 3000 örnek (ana bilgisayar)",
                 fontsize=8.5)
    a2.tick_params(labelsize=7.5)
    fig.tight_layout()
    _save(fig, _yol("kesme_gecikme_dagilim"))


# --------------------------------------------------------------------------
# Sekil 44.10: RM / EDF zaman cizelgesi (CSV)
def rms_zaman():
    veri = _csv("b44_rms_zaman.csv")
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    satirlar = [("RM_ornek1", "RM: (1,4) (2,6) (3,12)"),
                ("RM_ornek2", "RM: (2,5) (4,7)"),
                ("EDF_ornek2", "EDF: (2,5) (4,7)")]
    renk = {"1": EDGE[0], "2": EDGE[1], "3": EDGE[2]}
    for i, (kod, ad) in enumerate(satirlar):
        y = 2.4 - i * 1.0
        for r in veri:
            if r["senaryo"] != kod or r["gorev"] == "":
                continue
            bas, son = int(r["bas"]), int(r["son"])
            ax.broken_barh([(bas, son - bas)], (y, 0.7),
                           facecolors=renk[r["gorev"]], edgecolor="white")
        ax.text(-0.5, y + 0.35, ad, ha="right", va="center", fontsize=8.5,
                color=INK)
    ax.plot([7, 7], [0.1, 3.0], color=ACCENT, lw=1.2, ls="--")
    ax.text(7.4, 3.55, "t=7: (4,7) işinin ilk işi son teslimini kaçırır",
            fontsize=8, color=ACCENT)
    ax.set_xlim(0, 36)
    ax.set_ylim(0.0, 3.8)
    ax.set_xticks(range(0, 37, 6))
    ax.set_yticks([])
    ax.set_xlabel("zaman (birim)", fontsize=8.5)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.legend(handles=[Patch(color=EDGE[0], label="görev 1"),
                       Patch(color=EDGE[1], label="görev 2"),
                       Patch(color=EDGE[2], label="görev 3")],
              loc="upper right", ncol=3, fontsize=7.5, frameon=False,
              bbox_to_anchor=(1.0, 1.04))
    fig.subplots_adjust(left=0.3, top=0.88, bottom=0.2, right=0.97)
    _save(fig, _yol("rms_zaman"))


# --------------------------------------------------------------------------
# Sekil 44.10: super dongu, zamanlayici tetikli, RTOS
def mimari_karsilastirma():
    fig, ax = _eksen(9.6, 4.8, (0, 15), (0, 9))
    ax.text(0.2, 8.6, "A: Süper döngü", fontsize=10, weight="bold",
            color=INK)
    _box(ax, 0.3, 1.0, 4.2, 6.9,
         "while (1) {\n  oku_bms();\n  oku_motor();\n  güncelle();\n"
         "  gönder();\n  HAL_Delay(200);\n}", fill=FILL[0], edge=EDGE[0],
         fs=8)
    ax.text(0.3, 0.3, "hepsi bir akışta; kesme yok", fontsize=8,
            color=MUTED)
    ax.text(5.2, 8.6, "B: Zamanlayıcı tetikli", fontsize=10,
            weight="bold", color=INK)
    _box(ax, 5.3, 5.2, 4.2, 2.4, "TIM kesmesi (200 ms)\nflag = 1",
         fill=FILL[2], edge=EDGE[2], fs=8)
    _box(ax, 5.3, 1.2, 4.2, 3.2, "while (1) {\n  if (flag) { flag=0;\n"
         "    ... }\n  wfi;\n}", fill=FILL[0], edge=EDGE[0], fs=8)
    _arrow(ax, 7.4, 5.2, 7.4, 4.4, col=ACCENT, lw=1.3)
    ax.text(5.3, 0.45, "ana döngü bayrak yoksa uykuda (wfi)", fontsize=8,
            color=MUTED)
    ax.text(10.4, 8.6, "C: RTOS", fontsize=10, weight="bold", color=INK)
    _box(ax, 10.5, 6.0, 4.2, 1.8, "Görev BMS (öncelik 3)",
         fill=FILL[1], edge=EDGE[1], fs=8)
    _box(ax, 10.5, 3.8, 4.2, 1.8, "Görev motor (öncelik 4)",
         fill=FILL[1], edge=EDGE[1], fs=8)
    _box(ax, 10.5, 1.2, 4.2, 2.1, "Zamanlayıcı (SysTick tick)\n"
         "-> en yüksek hazır görev\n-> PendSV ile bağlam değişimi",
         fill=FILL[3], edge=EDGE[3], fs=7.5)
    _save(fig, _yol("superdongu_rtos"))


def main():
    os.makedirs(OUT, exist_ok=True)
    yoklama_kesme()
    x86_idt_nvic()
    nvic_durum()
    ic_ice_kuyruk()
    yigin_cerceve()
    halka_tampon()
    zamanlayici_pwm()
    gecikme_dagilim()
    rms_zaman()
    mimari_karsilastirma()
    print("tamam: 10 şekil")


if __name__ == "__main__":
    main()
