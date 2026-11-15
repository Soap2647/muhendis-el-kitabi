# -*- coding: utf-8 -*-
"""Bolum 45 - 'Iletisim Protokolleri (UART/SPI/I2C)' diyagramlari.

Simulasyon sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b45_uart_iz.csv, b45_uart_kayma.csv, b45_uart_baud.csv
  b45_spi_ornek.csv, b45_i2c_iz.csv, b45_i2c_olay.csv,
  b45_i2c_tahkim.csv, b45_can_tahkim.csv
Diger sekiller bolumdeki ornek degerlerden cizilir; bit doldurma ve
COBS ornekleri burada kucuk saf fonksiyonlarla yeniden hesaplanir.
Tum veriler SIMULASYONDUR.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")
MONO = {"family": "DejaVu Sans Mono"}


def _yol(ad):
    return os.path.join(OUT, "b45_%s.png" % ad)


def _csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fig(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    return fig, ax


def _temiz(ax):
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)


# ------------------------------------------------------------- Sekil 1
def uart_iz():
    rows = _csv("b45_uart_iz.csv")
    t = [float(r["t_bit"]) for r in rows]
    s = [int(r["seviye"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.step(t, s, where="post", color=ACCENT, lw=2.0)
    ax.set_ylim(-0.6, 1.9)
    ax.set_xlim(-0.2, 11.2)
    ax.set_yticks([0, 1])
    ax.set_xlabel("zaman (bit süresi cinsinden)")
    for k in range(0, 12):
        ax.axvline(k, color=RULE, lw=0.8, zorder=0)
    etiket = ["başlangıç", "D0", "D1", "D2", "D3", "D4", "D5", "D6",
              "D7", "dur"]
    for k, e in enumerate(etiket):
        ax.text(k + 0.5, 1.6, e, ha="center", fontsize=10,
                color=ACCENT_L, weight="bold")
    bits = [0, 1, 1, 0, 1, 0, 0, 1, 0, 1]
    for k, b in enumerate(bits):
        ax.text(k + 0.5, -0.4, str(b), ha="center", fontsize=10,
                color=INK, **MONO)
    ax.text(10.6, 0.5, "boşta: 1", fontsize=8, color=MUTED, ha="center")
    ax.set_title("0x4B baytının 8N1 çerçevesi (LSB önce)", fontsize=11,
                 color=INK, loc="left")
    fig.tight_layout()
    return _save(fig, _yol("uart_iz"))


# ------------------------------------------------------------- Sekil 2
def uart_kayma():
    kayma = _csv("b45_uart_kayma.csv")
    baud = _csv("b45_uart_baud.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.9),
                                 gridspec_kw={"width_ratios": [1.25, 1]})
    seriler = [("d0", "0 %"), ("d_plus4", "+4 %"),
               ("d_minus4", "-4 %"), ("d_plus6", "+6 %")]
    for y, (kol, ad) in enumerate(seriler):
        ylev = 3 - y
        for k in range(10):
            a1.add_patch(plt.Rectangle((k, ylev - 0.22), 1, 0.44,
                                       facecolor=FILL[0], edgecolor=RULE,
                                       lw=0.6))
        for r in kayma:
            t = float(r[kol])
            k = int(r["bit"])
            icerde = (k <= t < k + 1)
            a1.plot([t], [ylev], "o", ms=5,
                    color=(ACCENT_L if icerde else ACCENT))
        a1.text(-0.3, ylev, ad, ha="right", va="center", fontsize=10,
                color=INK)
    a1.set_xlim(-0.2, 10.5)
    a1.set_ylim(-0.6, 3.6)
    a1.set_yticks([])
    a1.set_xlabel("bit penceresi (kutu) ve örnek anı (nokta)")
    a1.set_title("Örnek anı kayması", fontsize=10, loc="left")
    _temiz(a1)
    xs = [float(r["d_yuzde"]) for r in baud]
    ys = [float(r["basari"]) for r in baud]
    a2.plot(xs, ys, color=ACCENT, lw=1.8)
    for x0 in (-5.26, 5.26):
        a2.axvline(x0, color=MUTED, ls="--", lw=0.9)
    a2.text(5.4, 0.45, "+5,26 %", fontsize=9, color=MUTED)
    a2.text(-5.1, 0.45, "-5,26 %", fontsize=9, color=MUTED, ha="right")
    a2.set_xlabel("saat sapması d (%)")
    a2.set_ylabel("256 baytın doğru çözülme oranı")
    a2.set_title("Tolerans taraması", fontsize=10, loc="left")
    a2.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    return _save(fig, _yol("uart_kayma"))


# ------------------------------------------------------------- Sekil 3
def spi_kipler():
    rows = _csv("b45_spi_ornek.csv")
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 5.2), sharex=True)
    for idx, kip in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
        ax = axs[idx // 2][idx % 2]
        kr = [r for r in rows if int(r["cpol"]) == kip[0] and
              int(r["cpha"]) == kip[1]]
        t = [int(r["kenar_t"]) for r in kr]
        s = [int(r["seviye"]) for r in kr]
        ax.step([0] + t, [kip[0]] + s, where="post", color=ACCENT, lw=1.8)
        for r in kr:
            tt = int(r["kenar_t"])
            if int(r["ornek"]):
                ax.plot([tt], [1.45], marker="v", color=ACCENT_L, ms=7)
            if int(r["hazir"]):
                ax.plot([tt], [-0.45], marker="s", color=MUTED, ms=5)
        ax.set_ylim(-0.8, 1.8)
        ax.set_yticks([0, 1])
        ax.set_title("CPOL=%d, CPHA=%d" % kip, fontsize=10, loc="left")
        ax.set_xticks(range(0, 17, 2))
    axs[1][0].set_xlabel("yarım periyot (SCK kenarı)")
    axs[1][1].set_xlabel("yarım periyot (SCK kenarı)")
    fig.text(0.01, 0.005,
             "▼ uydu örnekler     ■ veri hazırlanır     "
             "SCK boştayken seviyesi = CPOL",
             fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _save(fig, _yol("spi_kipler"))


# ------------------------------------------------------------- Sekil 4
def i2c_devre():
    fig, ax = _fig(9.6, 4.6)
    ax.plot([0.5, 9.5], [9.2, 9.2], color=INK, lw=1.2)
    ax.text(0.5, 9.45, "VDD (3,3 V)", fontsize=10, color=INK)
    # SCL icin direnc (solda), SDA icin direnc
    ax.plot([0.9, 0.9], [9.2, 7.6], color=INK, lw=1.2)
    ax.plot([2.5, 2.5], [9.2, 7.6], color=INK, lw=1.2)
    _box(ax, 0.4, 6.7, 1.0, 0.9, "Rp\n4,7 kΩ", fill=FILL[2],
         edge=EDGE[2], fs=8)
    _box(ax, 2.0, 6.7, 1.0, 0.9, "Rp\n4,7 kΩ", fill=FILL[2],
         edge=EDGE[2], fs=8)
    ax.plot([0.9, 0.9], [6.7, 3.6], color=INK, lw=1.2)
    ax.plot([2.5, 2.5], [6.7, 6.0], color=INK, lw=1.2)
    ax.plot([2.5, 9.3], [6.0, 6.0], color=ACCENT, lw=2.2)
    ax.text(9.4, 6.0, "SDA", fontsize=10, color=ACCENT, va="center")
    ax.plot([0.9, 9.3], [3.6, 3.6], color=ACCENT_L, lw=2.2)
    ax.text(9.4, 3.6, "SCL", fontsize=10, color=ACCENT_L, va="center")
    _box(ax, 0.6, 0.9, 3.4, 1.6,
         "ANA (master)\nSDA ve SCL'i çeker\nya da bırakır",
         fill=FILL[0], edge=EDGE[0], fs=9)
    _box(ax, 5.6, 0.9, 3.4, 1.6,
         "UYDU (slave)\nACK için SDA'yı çeker",
         fill=FILL[1], edge=EDGE[1], fs=9)
    ax.plot([1.4, 1.4], [2.5, 3.6], color=EDGE[0], lw=1.6)
    ax.plot([3.4, 3.4], [2.5, 6.0], color=EDGE[0], lw=1.6)
    ax.plot([6.4, 6.4], [2.5, 3.6], color=EDGE[1], lw=1.6)
    ax.plot([8.4, 8.4], [2.5, 6.0], color=EDGE[1], lw=1.6)
    ax.text(5.0, 0.45,
            "Açık-drenaj: her aygıt yalnızca 0'a çeker (NMOS). Hat, "
            "çekme direnciyle 1 olur.",
            ha="center", fontsize=9, color=INK)
    ax.text(5.0, 0.0,
            "tr ≈ 0,8473·R·Cb      Rmax = tr_max / (0,8473·Cb)",
            ha="center", fontsize=9, color=MUTED, **MONO)
    ax.set_ylim(-0.4, 10)
    return _save(fig, _yol("i2c_devre"))


# ------------------------------------------------------------- Sekil 5
def i2c_iz():
    rows = _csv("b45_i2c_iz.csv")
    olaylar = _csv("b45_i2c_olay.csv")
    t = [int(r["t"]) for r in rows]
    scl = [int(r["scl"]) for r in rows]
    sda = [int(r["sda"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.step(t, [v + 2.2 for v in scl], where="post", color=ACCENT_L,
            lw=1.6)
    ax.step(t, sda, where="post", color=ACCENT, lw=1.6)
    ax.text(t[0] - 2, 3.2, "SCL", fontsize=10, color=ACCENT_L, ha="right")
    ax.text(t[0] - 2, 1.0, "SDA", fontsize=10, color=ACCENT, ha="right")
    for r in olaylar:
        tt = int(r["t"])
        etiket = r["olay"]
        if etiket.startswith(("START", "STOP", "NACK", "KAYIP")):
            ax.axvline(tt, color=MUTED, ls=":", lw=0.9)
            ax.text(tt + 1, 4.1, etiket.split()[0], fontsize=8,
                    color=INK, rotation=90, va="bottom")
    ax.set_ylim(-0.4, 4.9)
    ax.set_yticks([])
    ax.set_xlim(t[0] - 3, max(t) + 1)
    ax.set_xlabel("adım (yarım bit)")
    ax.set_title("Yaz (0x10 <- 0x5A, 0x6B), tekrarlanan START, oku (2 bayt)",
                 fontsize=10, loc="left")
    _temiz(ax)
    fig.tight_layout()
    return _save(fig, _yol("i2c_iz"))


# ------------------------------------------------------------- Sekil 6
def i2c_tahkim():
    rows = _csv("b45_i2c_tahkim.csv")
    t = [int(r["t"]) for r in rows]
    a = [1 - int(r["ana_a_cek"]) for r in rows]
    b = [1 - int(r["ana_b_cek"]) for r in rows]
    hat = [int(r["sda"]) for r in rows]
    kayip = None
    for x, y, z in zip(t, b, hat):
        if y == 1 and z == 0:
            kayip = x
            break
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.step(t, [v + 2.4 for v in a], where="post", color=ACCENT_L,
            lw=1.6)
    ax.step(t, [v + 1.2 for v in b], where="post", color=ACCENT, lw=1.6)
    ax.step(t, hat, where="post", color=INK, lw=2.0)
    ax.text(t[0] - 1, 2.9, "ana A istek", ha="right", fontsize=9,
            color=ACCENT_L)
    ax.text(t[0] - 1, 1.7, "ana B istek", ha="right", fontsize=9,
            color=ACCENT)
    ax.text(t[0] - 1, 0.5, "hat (AND)", ha="right", fontsize=9,
            color=INK)
    if kayip is not None:
        ax.axvline(kayip, color=MUTED, ls="--", lw=0.9)
        ax.text(kayip + 0.6, 3.9, "B 1 yazdı, hat 0 okudu: B kaybeder",
                fontsize=9, color=INK)
    ax.set_ylim(-0.3, 4.4)
    ax.set_yticks([])
    ax.set_xlim(t[0] - 1, max(t) + 1)
    ax.set_xlabel("adım (yarım bit)")
    _temiz(ax)
    ax.set_title("Tahkim: 0xA0 ile 0xA2 aynı anda yazılıyor",
                 fontsize=10, loc="left")
    fig.tight_layout()
    return _save(fig, _yol("i2c_tahkim"))


# ------------------------------------------------------------- Sekil 7
def can_tahkim():
    rows = _csv("b45_can_tahkim.csv")
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    basliklar = ["bit", "A (0x123)", "B (0x0A5)", "C (0x3F0)", "hat",
                 "kaybeden"]
    xs = [0.6, 2.4, 4.4, 6.4, 8.0, 9.2]
    for x, b in zip(xs, basliklar):
        ax.text(x, 5.3, b, fontsize=10, weight="bold", color=INK,
                ha="center")
    for i, r in enumerate(rows[:5]):
        y = 4.3 - i * 0.85
        vals = [r["bit"], r["A"], r["B"], r["C"], r["hat"], r["kaybeden"]]
        for j, v in enumerate(vals):
            if j in (1, 2, 3, 4):
                dominant = (v == "0")
                fill = ACCENT if dominant else FILL[0]
                tcol = "white" if dominant else INK
                ax.add_patch(plt.Rectangle((xs[j] - 0.6, y - 0.32), 1.2,
                                           0.64, facecolor=fill,
                                           edgecolor=EDGE[0], lw=0.8))
                ax.text(xs[j], y, v, fontsize=11, color=tcol,
                        ha="center", va="center", **MONO)
            else:
                ax.text(xs[j], y, v if v else "-", fontsize=10,
                        ha="center", va="center", color=INK)
    ax.text(5.0, 0.35,
            "koyu = baskın (0); açık = çekinik (1). Çekinik gönderip hat 0 "
            "okuyan düğüm kaybeder.",
            ha="center", fontsize=9, color=MUTED)
    fig.tight_layout()
    return _save(fig, _yol("can_tahkim"))


# ------------------------------------------------------------- Sekil 8
def _doldur(bitler):
    cikis, kosu, son, ekler = [], 0, None, []
    for b in bitler:
        cikis.append(b)
        kosu = kosu + 1 if b == son else 1
        son = b
        if kosu == 5:
            ekler.append(len(cikis))
            cikis.append(1 - b)
            son, kosu = 1 - b, 1
    return cikis, ekler


def can_doldurma():
    girdi = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1]
    cikis, ekler = _doldur(girdi)
    fig, ax = plt.subplots(figsize=(9.6, 3.2))
    ax.set_xlim(-2.2, 19.5)
    ax.set_ylim(0, 4)
    ax.axis("off")
    for i, b in enumerate(girdi):
        ax.text(i, 2.9, str(b), ha="center", va="center", fontsize=12,
                color=INK, **MONO)
    ax.text(-2.0, 2.9, "girdi", ha="right", va="center", fontsize=10,
            color=INK)
    for i, b in enumerate(cikis):
        ekli = i in ekler
        if ekli:
            ax.add_patch(plt.Rectangle((i - 0.45, 0.85), 0.9, 0.9,
                                       facecolor=FILL[2], edgecolor=EDGE[2],
                                       lw=1.2))
        ax.text(i, 1.3, str(b), ha="center", va="center", fontsize=12,
                color=ACCENT if ekli else INK,
                weight="bold" if ekli else "normal", **MONO)
    ax.text(-2.0, 1.3, "gönderilen", ha="right", va="center", fontsize=10,
            color=INK)
    ax.text(8.5, 0.2,
            "sarı kutu: eklenen (dolgu) bit. 5 ardışık aynı bitten sonra "
            "zıt bit.",
            ha="center", fontsize=9, color=MUTED)
    ax.set_title("Bit doldurma (bit-stuffing) örneği", fontsize=10,
                 loc="left")
    fig.tight_layout()
    return _save(fig, _yol("can_doldurma"))


# ------------------------------------------------------------- Sekil 9
def _cobs(girdi):
    cikis, kod_yeri, kod = [0], 0, 1
    for b in girdi:
        if b == 0:
            cikis[kod_yeri] = kod
            kod_yeri = len(cikis)
            cikis.append(0)
            kod = 1
        else:
            cikis.append(b)
            kod += 1
    cikis[kod_yeri] = kod
    return cikis


def cobs_kodlama():
    girdi = [0x11, 0x22, 0x00, 0x33]
    kodlu = _cobs(girdi)
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    ax.set_xlim(-1.2, 10.5)
    ax.set_ylim(-0.6, 4.4)
    ax.axis("off")
    ax.text(-1.1, 3.2, "girdi", ha="left", fontsize=10, color=INK)
    for i, b in enumerate(girdi):
        x = 0.4 + i * 1.5
        _box(ax, x - 0.5, 2.6, 1.0, 0.9, "%02X" % b,
             fill=(FILL[3] if b == 0 else FILL[0]),
             edge=(ACCENT if b == 0 else EDGE[0]), fs=11,
             bold=(b == 0))
    ax.text(-1.1, 1.0, "kodlu", ha="left", fontsize=10, color=INK)
    for i, b in enumerate(kodlu):
        x = 0.4 + i * 1.5
        kod = i in (0, 3)
        _box(ax, x - 0.5, 0.4, 1.0, 0.9, "%02X" % b,
             fill=(FILL[2] if kod else FILL[1]),
             edge=(EDGE[2] if kod else EDGE[1]), fs=11, bold=kod)
    ax.text(0.4 + 4 * 1.5, 1.9, "sonlandırıcı 0x00 kodlu veride yok",
            fontsize=9, color=MUTED, ha="left")
    _arrow(ax, 0.4 + 2 * 1.5, 2.5, 0.4 + 3 * 1.5, 1.4, col=ACCENT,
           rad=-0.25, lw=1.2)
    ax.text(0.4 + 2 * 1.5 - 0.6, 2.25, "sıfır -> kod", fontsize=9,
            color=ACCENT, ha="right")
    ax.text(-1.1, -0.45,
            "Sarı: kod baytları (blok uzunluğu). Son blok kendi kodunu taşır.",
            fontsize=9, color=MUTED, ha="left")
    return _save(fig, _yol("cobs"))


# ------------------------------------------------------------ Sekil 10
def ev_akis():
    fig, ax = _fig(9.6, 5.6)
    _box(ax, 0.2, 7.9, 2.9, 1.5, "Daly BMS\n13 bayt, sağlamalı\nUART",
         fill=FILL[0], edge=EDGE[0], fs=8)
    _box(ax, 0.2, 5.2, 2.9, 1.5, "Kelly motor sürücüsü\nUART (4/8 bayt)",
         fill=FILL[0], edge=EDGE[0], fs=8)
    _box(ax, 0.2, 2.5, 2.9, 1.5, "GPIO: sinyal, far,\nvites (PB0-2, PC0-2)",
         fill=FILL[0], edge=EDGE[0], fs=8)
    _box(ax, 3.9, 4.2, 2.9, 2.6,
         "STM32F4 (main.c)\n200 ms döngü\nJSON satırı, ~119 bayt",
         fill=FILL[1], edge=EDGE[1], fs=9, bold=True)
    _box(ax, 7.4, 6.6, 2.4, 1.6, "Pi 5: telemetri.py\nSeri -> RFD900X",
         fill=FILL[2], edge=EDGE[2], fs=8)
    _box(ax, 7.4, 3.6, 2.4, 1.6, "Pi 5: kadran.py\nSeri -> WebSocket",
         fill=FILL[2], edge=EDGE[2], fs=8)
    _box(ax, 7.4, 0.5, 2.4, 1.6, "Tarayıcı dashboard\n(WebSocket istemcisi)",
         fill=FILL[4], edge=EDGE[4], fs=8)
    _arrow(ax, 3.1, 8.6, 3.9, 6.6, col=ACCENT)
    _arrow(ax, 3.1, 5.9, 3.9, 5.9, col=ACCENT)
    _arrow(ax, 3.1, 3.3, 3.9, 4.8, col=ACCENT)
    _arrow(ax, 6.8, 6.6, 7.4, 7.2, col=ACCENT)
    _arrow(ax, 6.8, 5.0, 7.4, 4.4, col=ACCENT)
    _arrow(ax, 8.6, 3.6, 8.6, 2.1, col=ACCENT)
    ax.text(0.2, 1.9, "STM32 -> Pi: UART3, 115200 baud, yayın 5 Hz",
            fontsize=8, color=MUTED)
    ax.text(0.2, 1.2, "Pi üzerinde iki servis aynı /dev/ttyAMA2 hattını",
            fontsize=8, color=MUTED)
    ax.text(0.2, 0.7, "okur: aynı anda çalışırsa bayt bölüşülür (uyarı).",
            fontsize=8, color=MUTED)
    return _save(fig, _yol("ev_akis"))


def main():
    yollar = [uart_iz(), uart_kayma(), spi_kipler(), i2c_devre(),
              i2c_iz(), i2c_tahkim(), can_tahkim(), can_doldurma(),
              cobs_kodlama(), ev_akis()]
    for y in yollar:
        print(y)


if __name__ == "__main__":
    main()
