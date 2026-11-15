# -*- coding: utf-8 -*-
"""Bolum 52 - DSP Temelleri diyagramlari.

Olcum grafikleri engine/veri/ altindaki CSV dosyalarini okur:
  b52_nicemleme.csv     SNR olculen ve 6,02N+1,76 (sekil 52.2)
  b52_dft.csv           DFT buyuklukleri, tam ve kesirli kutu (sekil 52.4)
  b52_pencere_zaman.csv, b52_pencere_spektrum.csv  (sekil 52.5)
  b52_ayrilma.csv       iki ton vadisi, pencereye gore (sekil 52.5)
  b52_zayif_ton.csv     zayif ton sizinti karsilastirmasi (sekil 52.5)
  b52_spektrogram.csv   chirp spektrogrami (sekil 52.6)
  b52_frekans.csv       FIR/IIR frekans yanitlari (sekil 52.7)
  b52_imu.csv           IMU egim kestirimi (sekil 52.9)
  b52_eslesik.csv       eslesik filtre cikisi (sekil 52.10)
Diger sekiller analitik formullerle cizilir.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_save, ACCENT, ACCENT_L, INK, MUTED, RULE, EDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gorseller")
VERI = os.path.join(HERE, "veri")
RENK = [ACCENT, ACCENT_L, EDGE[1], EDGE[2]]


def _eksen(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=RULE, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def ornekleme_ortusme(path):
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    t = np.linspace(0, 1.0, 2000)                       # ms
    ax.plot(t, np.sin(2*np.pi*7*t), color=ACCENT_L, lw=1.3,
            label="7 kHz sinüs (sürekli)")
    ax.plot(t, np.sin(2*np.pi*3*t), color=ACCENT, lw=1.1, ls="--",
            label="3 kHz sinüs")
    n = np.arange(11)                                   # fs = 10 kHz
    ax.plot(n / 10.0, np.sin(2*np.pi*7*n / 10.0), "o", color=ACCENT_L,
            ms=5, label="10 kHz örnekleri (7 kHz)")
    ax.plot(n / 10.0, np.sin(2*np.pi*3*n / 10.0), "x", color=ACCENT,
            ms=6, mew=1.6, label="örnekler, 3 kHz ile aynı")
    ax.set_xlabel("zaman (ms)", color=INK)
    ax.set_ylabel("genlik", color=INK)
    ax.legend(frameon=False, fontsize=9, loc="upper center",
              bbox_to_anchor=(0.5, -0.2), ncol=2)
    ax.set_ylim(-1.45, 1.35)
    _eksen(ax)
    return _save(fig, os.path.join(OUT, "b52_ornekleme_ortusme.png"))


def nicemleme_snr(path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    t = np.linspace(0, 1, 800)
    x = np.sin(2*np.pi*t)
    N = 3
    adim = 2.0 ** (1 - N)
    q = np.clip(adim * np.round(x / adim), -1, 1 - adim)
    a1.plot(t, x, color=MUTED, lw=1.0, label="gerçek sinüs")
    a1.step(t, q, where="mid", color=ACCENT, lw=1.4,
            label="3 bit (8 seviye)")
    a1.set_xlabel("zaman (periyot)", color=INK)
    a1.set_ylabel("genlik", color=INK)
    a1.legend(frameon=False, fontsize=9, loc="upper right")
    _eksen(a1)
    d = np.loadtxt(os.path.join(VERI, "b52_nicemleme.csv"), delimiter=",",
                   skiprows=1)
    a2.plot(d[:, 0], d[:, 2], color=MUTED, lw=1.2, ls="--",
            label="6,02N + 1,76 dB")
    a2.plot(d[:, 0], d[:, 1], "o-", color=ACCENT, ms=4, lw=1.2,
            label="ölçülen SNR")
    a2.set_xlabel("bit sayısı N", color=INK)
    a2.set_ylabel("SNR (dB)", color=INK)
    a2.legend(frameon=False, fontsize=9, loc="upper left")
    _eksen(a2)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_nicemleme_snr.png"))


def konvolusyon_kaydirma(path):
    x = np.array([1.0, 2.0, 3.0, 4.0])
    h = np.array([1.0, -1.0, 2.0])
    fig, eksenler = plt.subplots(1, 3, figsize=(9.6, 3.2), sharey=True)
    for ax, n in zip(eksenler, (2, 3, 4)):
        k = np.arange(len(x))
        ax.stem(k, x, linefmt=ACCENT_L, markerfmt="o", basefmt=" ")
        kh = n - np.arange(len(h))                     # h[n-k] icin k
        ax.stem(kh, h, linefmt=ACCENT, markerfmt="s", basefmt=" ")
        ax.set_title(f"n = {n}", fontsize=10, color=INK)
        ax.set_xticks(range(0, 6))
        ax.set_xlabel("k", color=INK)
        _eksen(ax)
    eksenler[0].set_ylabel("değer", color=INK)
    fig.text(0.5, -0.02, "mavi: x[k]   bordo: h[n−k] (ters çevrilip kaydırılmış)",
             ha="center", fontsize=9, color=INK)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_konvolusyon_kaydirma.png"))


def dft_spektrum(path):
    d = np.loadtxt(os.path.join(VERI, "b52_dft.csv"), delimiter=",",
                   skiprows=1)
    f, tam, kes = d[:32, 0], d[:32, 1], d[:32, 2]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.4), sharey=True)
    a1.stem(f, tam, linefmt=ACCENT_L, markerfmt="o", basefmt=" ")
    a1.set_title("125 Hz (tam kutu, k = 8)", fontsize=10, color=INK)
    a2.stem(f, kes, linefmt=ACCENT, markerfmt="o", basefmt=" ")
    a2.set_title("130 Hz (kesirli, kutular arasında)", fontsize=10,
                 color=INK)
    for ax in (a1, a2):
        ax.set_xlabel("frekans (Hz)", color=INK)
        _eksen(ax)
    a1.set_ylabel("|X[k]|", color=INK)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_dft_spektrum.png"))


def pencere_sizinti(path):
    fig, eks = plt.subplots(2, 2, figsize=(9.6, 6.4))
    adlar = ["dikdörtgen", "Hann", "Hamming", "Blackman"]
    z = np.loadtxt(os.path.join(VERI, "b52_pencere_zaman.csv"),
                   delimiter=",", skiprows=1)
    s = np.loadtxt(os.path.join(VERI, "b52_pencere_spektrum.csv"),
                   delimiter=",", skiprows=1)
    a = eks[0, 0]
    for i, ad in enumerate(adlar):
        a.plot(z[:, 0], z[:, i + 1], color=RENK[i % 4], lw=1.2, label=ad)
    a.set_title("(a) pencere şekilleri (N = 128)", fontsize=10, color=INK)
    a.set_xlabel("örnek", color=INK)
    a.legend(frameon=False, fontsize=8)
    _eksen(a)
    a = eks[0, 1]
    msk = (s[:, 0] >= 80) & (s[:, 0] <= 120)
    for i, ad in enumerate(adlar):
        a.plot(s[msk, 0], s[msk, i + 1], color=RENK[i % 4], lw=1.2, label=ad)
    a.set_title("(b) 100,5 Hz tonun spektrumu", fontsize=10, color=INK)
    a.set_xlabel("frekans (Hz)", color=INK)
    a.set_ylabel("dB (tepeye göre)", color=INK)
    a.set_ylim(-90, 2)
    a.legend(frameon=False, fontsize=8)
    _eksen(a)
    a = eks[1, 0]
    v = np.loadtxt(os.path.join(VERI, "b52_ayrilma.csv"), delimiter=",",
                   skiprows=1)
    for i, ad in enumerate(adlar):
        a.plot(v[:, 0], v[:, i + 1], color=RENK[i % 4], lw=1.2, label=ad)
    a.axhline(-3, color=MUTED, ls="--", lw=0.9)
    a.set_title("(c) iki ton vadisi (−3 dB eşiği)", fontsize=10, color=INK)
    a.set_xlabel("ton aralığı (kutu)", color=INK)
    a.set_ylabel("vadi (dB)", color=INK)
    a.set_ylim(-40, 3)
    a.legend(frameon=False, fontsize=8, loc="lower right")
    _eksen(a)
    a = eks[1, 1]
    zt = np.genfromtxt(os.path.join(VERI, "b52_zayif_ton.csv"), delimiter=",",
                       skip_header=1, dtype=None, encoding="utf-8")
    x = np.arange(len(zt))
    gen = 0.36
    a.bar(x - gen / 2, [r[1] for r in zt], gen, color=MUTED,
          label="yalnız sızıntı")
    a.bar(x + gen / 2, [r[2] for r in zt], gen, color=ACCENT,
          label="sızıntı + zayıf ton")
    a.axhline(-60, color=INK, ls=":", lw=1)
    a.text(1.5, -57, "zayıf ton −60 dB", fontsize=8, ha="center", color=INK)
    a.set_xticks(x)
    a.set_xticklabels(adlar, fontsize=8)
    a.set_title("(d) 152 Hz kutusu (N = 256)", fontsize=10, color=INK)
    a.set_ylabel("dB", color=INK)
    a.set_ylim(-95, 0)
    a.legend(frameon=False, fontsize=8, loc="lower left", ncol=2)
    _eksen(a)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_pencere_sizinti.png"))


def spektrogram(path):
    d = np.loadtxt(os.path.join(VERI, "b52_spektrogram.csv"), delimiter=",",
                   skiprows=1)
    tz = np.unique(d[:, 0])
    fz = np.unique(d[:, 1])
    M = d[:, 2].reshape(len(tz), len(fz)).T
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    im = ax.imshow(np.clip(M, -60, 0), origin="lower", aspect="auto",
                   extent=[tz[0], tz[-1], fz[0], fz[-1]], cmap="magma")
    ax.plot(tz, 50 + 175 * tz, color="white", lw=0.8, ls="--",
            label="gerçek frekans")
    ax.set_xlabel("zaman (s)", color=INK)
    ax.set_ylabel("frekans (Hz)", color=INK)
    ax.legend(frameon=False, fontsize=9, loc="upper left",
              labelcolor="white")
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_label("dB", color=INK)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_spektrogram.png"))


def filtre_frekans(path):
    d = np.loadtxt(os.path.join(VERI, "b52_frekans.csv"), delimiter=",",
                   skiprows=1)
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    etiket = ["hareketli ortalama (M = 5)", "pencereli sinc FIR (31 katsayı)",
              "üstel düzleştirme (EMA, 20 Hz)",
              "Butterworth 2. derece (100 Hz)"]
    for i, e in enumerate(etiket):
        ax.plot(d[:, 0], d[:, i + 1], color=RENK[i], lw=1.4, label=e)
    ax.axhline(-3, color=MUTED, ls="--", lw=0.9)
    ax.set_xlabel("frekans (Hz)", color=INK)
    ax.set_ylabel("|H(f)| (dB)", color=INK)
    ax.set_ylim(-60, 5)
    ax.set_xlim(0, 500)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    _eksen(ax)
    return _save(fig, os.path.join(OUT, "b52_filtre_frekans.png"))


def kutup_sifir(path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 4.2))
    alfa = 1 - np.exp(-2 * np.pi * 20 / 1000)
    th = np.linspace(0, 2 * np.pi, 300)
    b, a = signal.butter(2, 0.2)
    panel = [("(a) EMA: kutup z = 1 − α", np.array([1 - alfa]),
              np.array([0.0])),
             ("(b) Butterworth 2. derece", np.roots(a), np.roots(b))]
    for ax, (baslik, kutup, sifir) in zip((a1, a2), panel):
        ax.plot(np.cos(th), np.sin(th), color=MUTED, lw=0.9)
        ax.plot(kutup.real, kutup.imag, "x", color=ACCENT, ms=9, mew=2,
                label="kutup")
        ax.plot(sifir.real, sifir.imag, "o", mfc="none", color=ACCENT_L,
                ms=8, mew=1.5, label="sıfır")
        ax.axhline(0, color=RULE, lw=0.6)
        ax.axvline(0, color=RULE, lw=0.6)
        ax.set_aspect("equal")
        ax.set_xlim(-1.25, 1.25)
        ax.set_ylim(-1.25, 1.25)
        ax.set_title(baslik, fontsize=10, color=INK)
        ax.set_xlabel("Re z", color=INK)
        ax.set_ylabel("Im z", color=INK)
        ax.legend(frameon=False, fontsize=8, loc="lower right")
        _eksen(ax)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_kutup_sifir.png"))


def imu_tumleyen(path):
    d = np.loadtxt(os.path.join(VERI, "b52_imu.csv"), delimiter=",",
                   skiprows=1)
    t, gercek, ham, ema, jiro, comp = d.T
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    m = t <= 20
    a1.plot(t[m], ham[m], color=RULE, lw=0.8, label="ivmeölçer ham")
    a1.plot(t[m], gercek[m], color=INK, lw=1.4, label="gerçek eğim")
    a1.plot(t[m], comp[m], color=ACCENT, lw=1.3, label="tümleyen filtre")
    a1.set_xlabel("zaman (s)", color=INK)
    a1.set_ylabel("eğim (derece)", color=INK)
    a1.legend(frameon=False, fontsize=8, loc="lower right")
    _eksen(a1)
    a2.plot(t, jiro - gercek, color=ACCENT_L, lw=1.2,
            label="jiroskop integrali (sürüklenir)")
    a2.plot(t, comp - gercek, color=ACCENT, lw=1.2, label="tümleyen filtre")
    a2.set_xlabel("zaman (s)", color=INK)
    a2.set_ylabel("hata (derece)", color=INK)
    a2.legend(frameon=False, fontsize=8, loc="upper left")
    _eksen(a2)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_imu_tumleyen.png"))


def eslesik_filtre(path):
    d = np.loadtxt(os.path.join(VERI, "b52_eslesik.csv"), delimiter=",",
                   skiprows=1)
    t, r, c = d.T
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.2, 5.0), sharex=True)
    a1.plot(t * 1000, r, color=MUTED, lw=0.6)
    a1.set_ylabel("alıcı", color=INK)
    a1.set_title("(a) gürültülü alıcı sinyali (SNR = −5 dB)", fontsize=10,
                 color=INK)
    _eksen(a1)
    a2.plot(t * 1000, c, color=ACCENT, lw=1.0)
    tepe = np.argmax(c)
    a2.axvline(t[tepe] * 1000, color=ACCENT_L, ls="--", lw=0.9)
    a2.text(t[tepe] * 1000 + 0.6, 0.85, "tepe", color=ACCENT_L, fontsize=9)
    a2.set_xlabel("zaman (ms)", color=INK)
    a2.set_ylabel("eşleşik çıkış", color=INK)
    a2.set_title("(b) eşleşik filtre çıkışı (normalize)", fontsize=10,
                 color=INK)
    _eksen(a2)
    fig.tight_layout()
    return _save(fig, os.path.join(OUT, "b52_eslesik_filtre.png"))


if __name__ == "__main__":
    ciktilar = [
        ornekleme_ortusme(None),
        nicemleme_snr(None),
        konvolusyon_kaydirma(None),
        dft_spektrum(None),
        pencere_sizinti(None),
        spektrogram(None),
        filtre_frekans(None),
        kutup_sifir(None),
        imu_tumleyen(None),
        eslesik_filtre(None),
    ]
    for c in ciktilar:
        print(c)
