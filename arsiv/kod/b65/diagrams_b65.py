# -*- coding: utf-8 -*-
"""Bölüm 65 - PyTorch Derinlemesine diyagramları.

Ölçüm grafikleri engine/veri/b65_*.csv dosyalarını okur (bu dosyalar
GPU deneylerinin çıktısıdır). Mimari ve akış şekilleri veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _fig, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fl(rows, k):
    return np.array([float(r[k]) for r in rows])


def depolama(path):
    # Storage: tek boyutlu bellek; x ve x.t() aynı hücrelere bakar.
    fig, ax = _fig(9.6, 4.6)
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.2)
    ax.text(0.2, 5.8, "Storage (düz bellek): x ve x.t() aynı 12 hücreyi kullanır",
            fontsize=10.5, color=INK, weight="bold")
    for i in range(12):
        _box(ax, 0.4 + i * 0.92, 4.2, 0.8, 0.8, str(i), fill=FILL[0],
             edge=EDGE[0], fs=10)
    ax.text(0.4, 3.8, "adres 0", fontsize=8.5, color=MUTED)
    ax.text(11.0, 3.8, "adres 11", fontsize=8.5, color=MUTED, ha="right")
    ax.text(0.2, 3.1, "x = arange(12).reshape(3, 4): stride (4, 1), offset 0",
            fontsize=9.5, color=INK)
    ax.text(0.2, 2.6, "  x[i, j] adresi = i·4 + j·1", fontsize=9.5,
            color=ACCENT_L)
    ax.text(0.2, 1.8, "y = x.t(): stride (1, 4), aynı storage, kopya yok",
            fontsize=9.5, color=INK)
    ax.text(0.2, 1.3, "  y[i, j] adresi = i·1 + j·4   ->   y[1, 2] = hücre 9",
            fontsize=9.5, color=ACCENT_L)
    ax.text(0.2, 0.6, "y.view(-1) hata verir (bitişik değil); "
            "y.contiguous() yeni storage ayırır.",
            fontsize=9.5, color=MUTED)
    fig.tight_layout()
    return _save(fig, path)


def grad_grafi(path):
    # f = tanh((a*b + a)/10): grad_fn zinciri, ileri yön ve geri yön.
    fig, ax = _fig(9.6, 4.4)
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.2)
    ax.text(0.2, 5.9, "f = tanh((a·b + a) / 10): hesap grafiği ve grad_fn zinciri",
            fontsize=10.5, color=INK, weight="bold")
    _box(ax, 0.2, 4.5, 1.8, 0.8, "a (yaprak)", fill=FILL[1], edge=EDGE[1])
    _box(ax, 0.2, 1.2, 1.8, 0.8, "b (yaprak)", fill=FILL[1], edge=EDGE[1])
    _box(ax, 2.5, 2.9, 1.9, 0.8, "MulBackward0", fill=FILL[0], edge=EDGE[0])
    _box(ax, 5.0, 2.9, 1.9, 0.8, "AddBackward0", fill=FILL[0], edge=EDGE[0])
    _box(ax, 7.5, 2.9, 1.9, 0.8, "DivBackward0", fill=FILL[0], edge=EDGE[0])
    _box(ax, 10.0, 2.9, 1.9, 0.8, "TanhBackward0", fill=FILL[3],
         edge=EDGE[3])
    _arrow(ax, 2.0, 4.8, 2.5, 3.5, col=EDGE[0])
    _arrow(ax, 2.0, 1.6, 2.5, 3.1, col=EDGE[0])
    _arrow(ax, 4.4, 3.3, 5.0, 3.3, col=EDGE[0])
    _arrow(ax, 2.0, 5.0, 5.0, 3.6, col=EDGE[0], rad=-0.25)
    _arrow(ax, 6.9, 3.3, 7.5, 3.3, col=EDGE[0])
    _arrow(ax, 9.4, 3.3, 10.0, 3.3, col=EDGE[0])
    # geri geçiş (backward): bordo oklar, ters yönde
    _arrow(ax, 10.0, 2.7, 9.4, 2.7, col=ACCENT, lw=1.1)
    _arrow(ax, 7.5, 2.7, 6.9, 2.7, col=ACCENT, lw=1.1)
    _arrow(ax, 5.0, 2.7, 4.4, 2.7, col=ACCENT, lw=1.1)
    _arrow(ax, 2.5, 2.7, 2.0, 2.4, col=ACCENT, lw=1.1)
    ax.text(0.2, 0.6, "Siyah oklar ileri yönü, bordo oklar geri geçişi (backward) "
            "gösterir.", fontsize=8.5, color=MUTED)
    ax.text(0.2, 0.1, "a.grad = 0,223622   b.grad = 0,111811   (f = 0,664037)",
            fontsize=9, color=ACCENT_L)
    fig.tight_layout()
    return _save(fig, path)


def matmul_egri(path):
    satir = oku("b65_matmul.csv")
    n = fl(satir, "n")
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.loglog(n, fl(satir, "cpu_s"), "-o", color=EDGE[0], label="CPU")
    ax.loglog(n, fl(satir, "gpu_s"), "-s", color=EDGE[1],
              label="GPU (veri zaten GPU'da)")
    ax.loglog(n, fl(satir, "gpu_kopya_s"), "--^", color=EDGE[2],
              label="GPU + CPU'dan kopya")
    ax.set_xlabel("matris boyutu n (n × n, float32)")
    ax.set_ylabel("süre (saniye, log)")
    ax.set_title("Matris çarpımı: boyuta göre CPU ve GPU süresi",
                 fontsize=10.5)
    ax.grid(color=RULE, lw=0.6, which="both")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return _save(fig, path)


def senkron(path):
    s = oku("b65_senkron.csv")
    k = oku("b65_kopya.csv")
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    ad = [r["olcum"] for r in s]
    deg = [float(r["sure_s"]) * 1000 for r in s]
    etiket = {"yanlis_senkronsuz": "senkronsuz\n(yanlış)",
              "senkron_sonrasi_toplam": "senk. sonrası\ntoplam",
              "dogru_synchronize": "synchronize\n(doğru)",
              "cuda_event": "CUDA event\n(GPU süresi)"}
    renk = [ACCENT, EDGE[0], EDGE[1], EDGE[2]]
    axs[0].bar(range(len(ad)), deg, color=renk)
    axs[0].set_xticks(range(len(ad)))
    axs[0].set_xticklabels([etiket[a] for a in ad], fontsize=8)
    axs[0].set_ylabel("ms / matmul (n = 3072)")
    axs[0].set_title("Zamanlama: senkronizasyon ne ölçer?", fontsize=10)
    for i, v in enumerate(deg):
        axs[0].text(i, v + 0.15, "%.3f" % v, ha="center", fontsize=8.5)
    mb = fl(k, "mb")
    axs[1].plot(mb, fl(k, "pageable_s") * 1000, "-o", color=EDGE[0],
                label="sayfalanabilir (pageable)")
    axs[1].plot(mb, fl(k, "pinned_s") * 1000, "-s", color=EDGE[1],
                label="pinned (kilitli)")
    axs[1].set_xlabel("kopyalanan veri (MB)")
    axs[1].set_ylabel("ms (CPU -> GPU)")
    axs[1].set_title("Kopya: pinned bellek daha hızlı", fontsize=10)
    axs[1].legend(frameon=False, fontsize=8.5)
    axs[1].grid(color=RULE, lw=0.6)
    axs[0].grid(color=RULE, lw=0.6, axis="y")
    fig.tight_layout()
    return _save(fig, path)


def veri_hatti(path):
    s = oku("b65_veri.csv")
    etiket = ["w=0", "w=1", "w=2", "w=4", "w=4\npinned", "w=8\npinned"]
    bek = fl(s, "veri_bekleme_s")
    gpu = fl(s, "gpu_adim_s")
    x = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.bar(x, bek, color=ACCENT, label="GPU veri beklerken (CPU'dan)")
    ax.bar(x, gpu, bottom=bek, color=EDGE[1],
           label="GPU'da adım (ileri+geri+adım)")
    for i in range(len(s)):
        ax.text(i, bek[i] + gpu[i] + 0.02, "%.2f s" % (bek[i] + gpu[i]),
                ha="center", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, fontsize=9)
    ax.set_ylabel("bir epoch süresi (s)")
    ax.set_title("DataLoader: worker sayısı ve GPU'nun boşta beklemesi",
                 fontsize=10.5)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.grid(color=RULE, lw=0.6, axis="y")
    fig.tight_layout()
    return _save(fig, path)


def amp(path):
    s = oku("b65_amp.csv")
    kipler = ["fp32", "fp16", "bf16"]
    renkler = [EDGE[0], EDGE[1], EDGE[2]]
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    w = 0.26
    for j, batch in enumerate(["256", "1024"]):
        rows = [r for r in s if r["batch"] == batch]
        for i, kip in enumerate(kipler):
            r = [q for q in rows if q["kip"] == kip][0]
            x = j + (i - 1) * w
            lab = kip if j == 0 else None
            axs[0].bar(x, float(r["adim_ms"]), w, color=renkler[i], label=lab)
            axs[1].bar(x, float(r["tepe_bellek_mb"]), w, color=renkler[i],
                       label=lab)
    axs[0].set_title("Adım süresi (ms)", fontsize=10)
    axs[1].set_title("Tepe bellek (MB)", fontsize=10)
    axs[0].set_ylim(0, 30)
    axs[1].set_ylim(0, 400)
    for ax in axs:
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["batch 256", "batch 1024"])
        ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper center")
        ax.grid(color=RULE, lw=0.6, axis="y")
    fig.tight_layout()
    return _save(fig, path)


def bellek(path):
    s = [r for r in oku("b65_bellek.csv") if r["durum"] == "tamam"]
    kipler = [("fp32", EDGE[0], "-o", "fp32"),
              ("fp16", EDGE[1], "-s", "fp16 AMP"),
              ("ckpt", EDGE[3], "-^", "fp32 + checkpoint")]
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for kip, renk, mark, lab in kipler:
        rows = [r for r in s if r["kip"] == kip]
        b = fl(rows, "batch")
        axs[0].plot(b, fl(rows, "tepe_bellek_mb"), mark, color=renk, label=lab)
        axs[1].plot(b, fl(rows, "adim_ms"), mark, color=renk, label=lab)
    for ax, yl in ((axs[0], "tepe bellek (MB)"), (axs[1], "adım süresi (ms)")):
        ax.set_xscale("log", base=2)
        ax.set_xlabel("batch boyutu (log2)")
        ax.set_ylabel(yl)
        ax.grid(color=RULE, lw=0.6)
        ax.legend(frameon=False, fontsize=8.5)
    axs[0].set_title("Aktivasyon belleği batch ile büyür", fontsize=10)
    axs[1].set_title("Checkpoint: bellek düşer, süre artar", fontsize=10)
    fig.tight_layout()
    return _save(fig, path)


def nn_agac(path):
    fig, ax = _fig(9.6, 5.0)
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.4)
    _box(ax, 0.3, 4.9, 2.6, 0.9, "Ag (nn.Module)", fill=FILL[4],
         edge=EDGE[4], bold=True)
    _box(ax, 0.3, 2.9, 2.6, 0.9, "ust (Sequential)", fill=FILL[0],
         edge=EDGE[0])
    _box(ax, 0.3, 0.9, 2.6, 0.9, "cikis (Linear)", fill=FILL[0],
         edge=EDGE[0])
    _arrow(ax, 1.6, 4.9, 1.6, 3.8, col=EDGE[0])
    _arrow(ax, 1.6, 2.9, 1.6, 1.8, col=EDGE[0])
    kids = [("0: Linear(64,32)", "parametre: weight, bias", FILL[1], EDGE[1]),
            ("1: BatchNorm1d(32)", "parametre + buffer", FILL[2], EDGE[2]),
            ("2: ReLU", "parametresiz", FILL[0], EDGE[0]),
            ("3: Dropout(0.5)", "parametresiz (eval'de kapalı)", FILL[0],
             EDGE[0])]
    for i, (a, b, f, e) in enumerate(kids):
        y = 4.6 - i * 1.05
        _box(ax, 4.2, y, 3.5, 0.8, a, fill=f, edge=e, fs=9.5)
        ax.text(7.9, y + 0.4, b, fontsize=8.5, color=MUTED, va="center")
        _arrow(ax, 2.9, 3.35, 4.2, y + 0.4, col=RULE, lw=1.0)
    ax.text(4.2, 0.4, "state_dict anahtarları: ust.0.weight, ust.0.bias,",
            fontsize=8.5, color=INK)
    ax.text(4.2, 0.0, "ust.1.weight/bias, ust.1.running_mean/var,",
            fontsize=8.5, color=INK)
    ax.text(4.2, -0.4, "cikis.weight, cikis.bias", fontsize=8.5, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def egitim_akis(path):
    fig, ax = _fig(9.6, 5.2)
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.6)
    _box(ax, 0.2, 5.4, 2.4, 0.8, "1. Tohum ve veri", fill=FILL[4],
         edge=EDGE[4])
    _box(ax, 3.2, 5.4, 2.6, 0.8, "2. Model, opt, zamanlayıcı",
         fill=FILL[4], edge=EDGE[4], fs=9)
    _box(ax, 6.4, 5.4, 2.6, 0.8, "3. Cihaza taşı (device)", fill=FILL[4],
         edge=EDGE[4], fs=9)
    _arrow(ax, 2.6, 5.8, 3.2, 5.8, col=EDGE[4])
    _arrow(ax, 5.8, 5.8, 6.4, 5.8, col=EDGE[4])
    _box(ax, 0.2, 3.3, 2.4, 0.8, "mini-batch al", fill=FILL[0],
         edge=EDGE[0])
    _box(ax, 3.2, 3.3, 2.6, 0.8, "ileri geçiş + kayıp", fill=FILL[0],
         edge=EDGE[0])
    _box(ax, 6.4, 3.3, 2.6, 0.8, "zero_grad, backward", fill=FILL[0],
         edge=EDGE[0])
    _box(ax, 9.4, 3.3, 2.4, 0.8, "opt.step()", fill=FILL[0],
         edge=EDGE[0])
    _arrow(ax, 7.7, 5.4, 1.4, 4.1, col=ACCENT_L, rad=0.0)
    _arrow(ax, 2.6, 3.7, 3.2, 3.7, col=EDGE[0])
    _arrow(ax, 5.8, 3.7, 6.4, 3.7, col=EDGE[0])
    _arrow(ax, 9.0, 3.7, 9.4, 3.7, col=EDGE[0])
    _arrow(ax, 10.6, 3.3, 10.6, 2.5, col=EDGE[0])
    _box(ax, 6.4, 1.6, 5.4, 0.8, "epoch sonu: sched.step(), eval, "
         "metrik log", fill=FILL[2], edge=EDGE[2], fs=9)
    _arrow(ax, 10.6, 2.5, 9.6, 2.4, col=EDGE[2])
    _box(ax, 0.2, 1.6, 5.4, 0.8, "doğrulama (eval, no_grad): "
         "val kayıp ve doğruluk", fill=FILL[1], edge=EDGE[1], fs=9)
    _arrow(ax, 6.4, 2.0, 5.6, 2.0, col=EDGE[2])
    _box(ax, 0.2, 0.2, 5.4, 0.8, "en iyi model + checkpoint\n"
         "(model, opt, zamanlayıcı, epoch, RNG)", fill=FILL[3], edge=EDGE[3],
         fs=8.5)
    _box(ax, 6.4, 0.2, 5.4, 0.8, "test: yalnızca bir kez, son model",
         fill=FILL[1], edge=EDGE[1], fs=9)
    _arrow(ax, 2.9, 1.6, 2.9, 1.0, col=EDGE[3])
    fig.tight_layout()
    return _save(fig, path)


def profil(path):
    s = oku("b65_profil.csv")[:8]
    isim = [r["operator"].replace("aten::", "") for r in s][::-1]
    gpu = fl(s, "gpu_us_adim")[::-1]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.barh(range(len(s)), gpu, color=EDGE[0])
    ax.set_yticks(range(len(s)))
    ax.set_yticklabels(isim, fontsize=8.5)
    for i, v in enumerate(gpu):
        ax.text(v + 15, i, "%.0f" % v, va="center", fontsize=8.5)
    ax.set_xlabel("GPU süresi, adım başına (µs)")
    ax.set_title("torch.profiler: CNN eğitim adımında en pahalı operatörler",
                 fontsize=10)
    ax.grid(color=RULE, lw=0.6, axis="x")
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    yollar = [
        depolama(os.path.join(GORSEL, "b65_depolama.png")),
        grad_grafi(os.path.join(GORSEL, "b65_grad_grafi.png")),
        matmul_egri(os.path.join(GORSEL, "b65_matmul.png")),
        senkron(os.path.join(GORSEL, "b65_senkron.png")),
        veri_hatti(os.path.join(GORSEL, "b65_veri_hatti.png")),
        amp(os.path.join(GORSEL, "b65_amp.png")),
        bellek(os.path.join(GORSEL, "b65_bellek.png")),
        nn_agac(os.path.join(GORSEL, "b65_nn_agac.png")),
        egitim_akis(os.path.join(GORSEL, "b65_egitim_akis.png")),
        profil(os.path.join(GORSEL, "b65_profil.png")),
    ]
    for y in yollar:
        print(y)
