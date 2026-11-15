# -*- coding: utf-8 -*-
"""Bolum 64 - Eğitimin Sanatı diyagramları.

Ölçüm grafikleri engine/veri/b64_*.csv dosyalarını okur (bu dosyalar
b64 deneylerinin çıktısıdır). Şema şekilleri (BatchNorm ve dropout)
içeriğe göre çizilir.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, ACCENT_L, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")
RENK = [EDGE[0], EDGE[1], EDGE[2], EDGE[3], EDGE[4]]


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fl(rows, k):
    return np.array([float(r[k]) for r in rows])


def yorunge(yol):
    rows = oku("b64_yorunge.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    xs = np.linspace(-4.5, 0.5, 200)
    ys = np.linspace(-1.2, 1.2, 200)
    X, Y = np.meshgrid(xs, ys)
    Z = 0.5 * (X ** 2 + 10 * Y ** 2)
    a1.contour(X, Y, Z, levels=np.geomspace(0.01, 12, 14),
               colors=RULE, linewidths=0.8)
    for ad, c in zip(["SGD", "Momentum", "Adam"], RENK):
        sat = [r for r in rows if r["optimizer"] == ad]
        x, y = fl(sat, "x"), fl(sat, "y")
        a1.plot(x, y, "-o", color=c, ms=2.5, lw=1.2, label=ad)
        f = fl(sat, "f")
        a2.semilogy(np.arange(len(f)), f, color=c, lw=1.6, label=ad)
    a1.plot(0, 0, "*", color=INK, ms=10)
    a1.set_xlabel("x")
    a1.set_ylabel("y")
    a1.set_title("Kayıp yüzeyi ve yörüngeler (f = ½(x² + 10y²))",
                 fontsize=9, color=INK)
    a1.legend(fontsize=8, frameon=False)
    a2.set_xlabel("adım")
    a2.set_ylabel("f (log)")
    a2.set_title("Adım adım kayıp", fontsize=9, color=INK)
    a2.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    _save(fig, yol)


def optim_egri(yol):
    rows = oku("b64_optim_egri.csv")
    adlar = []
    for r in rows:
        if r["optimizer"] not in adlar:
            adlar.append(r["optimizer"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for k, ad in enumerate(adlar):
        sat = [r for r in rows if r["optimizer"] == ad]
        ep = np.arange(1, len(sat) + 1)
        m = fl(sat, "vacc_ort")
        s = fl(sat, "vacc_sd")
        c = RENK[k % len(RENK)] if k < 5 else [ACCENT, MUTED][k - 5]
        a1.plot(ep, m, color=c, lw=1.5, label=ad)
        a1.fill_between(ep, m - s, m + s, color=c, alpha=0.12, lw=0)
    a1.set_ylim(0.85, 1.0)
    a1.set_xlabel("epoch")
    a1.set_ylabel("doğrulama doğruluğu (5 tohum)")
    a1.set_title("Eğriler: ortalama ± sapma", fontsize=9, color=INK)
    a1.legend(fontsize=7, frameon=False, ncol=2)
    son = []
    for ad in adlar:
        sat = [r for r in rows if r["optimizer"] == ad]
        son.append((fl(sat, "vacc_ort")[-1], fl(sat, "vacc_sd")[-1]))
    y = np.arange(len(adlar))
    a2.barh(y, [s[0] for s in son], xerr=[s[1] for s in son],
            color=[FILL[1] if i % 2 else FILL[0] for i in range(len(adlar))],
            edgecolor=EDGE[0], capsize=3)
    a2.set_yticks(y)
    a2.set_yticklabels(adlar, fontsize=8)
    a2.set_xlim(0.9, 1.0)
    a2.set_xlabel("son epoch doğrulama doğruluğu")
    a2.set_title("Son değer (seçilen lr ile)", fontsize=9, color=INK)
    fig.tight_layout()
    _save(fig, yol)


def gurultu_batch(yol):
    g = oku("b64_gurultu.csv")
    b = oku("b64_batch.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    bx, gy = fl(g, "batch"), fl(g, "gurultu")
    a1.loglog(bx, gy, "o-", color=ACCENT, lw=1.6, label="ölçüm")
    ref = gy[0] * (bx[0] / bx)
    a1.loglog(bx, ref, "--", color=MUTED, lw=1.0,
              label="1/batch referansı")
    a1.set_xlabel("batch boyutu")
    a1.set_ylabel("E||g_batch − g||²")
    a1.set_title("Gradyan gürültüsü batch ile azalır", fontsize=9,
                 color=INK)
    a1.legend(fontsize=8, frameon=False)
    for mod, c, ls in [("sabit_lr=0.1", EDGE[0], "-"),
                       ("dogrusal_olcek", EDGE[3], "--")]:
        sat = [r for r in b if r["mod"] == mod]
        bs = sorted(set(int(r["batch"]) for r in sat))
        mu, sd = [], []
        for bb in bs:
            v = [float(r["test_acc"]) for r in sat if int(r["batch"]) == bb]
            mu.append(np.mean(v))
            sd.append(np.std(v, ddof=1))
        a2.errorbar(bs, mu, yerr=sd, color=c, ls=ls, marker="o", capsize=3,
                    label=mod)
    a2.set_xscale("log", base=2)
    a2.set_xlabel("batch boyutu (30 epoch, SGD)")
    a2.set_ylabel("test doğruluğu (5 tohum)")
    a2.set_title("Batch boyutu ve öğrenme oranı birlikte", fontsize=9,
                 color=INK)
    a2.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    _save(fig, yol)


def lr_aralik(yol):
    rows = oku("b64_lr_aralik.csv")
    lr = fl(rows, "lr")
    ema = fl(rows, "kayip_ema")
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    ax.semilogx(lr, ema, color=ACCENT, lw=1.8)
    km = int(np.argmin(ema))
    ax.axvline(lr[km], color=EDGE[0], ls="--", lw=1.0)
    ax.annotate("en düşük kayıp\nlr = %.2g" % lr[km],
                xy=(lr[km], ema[km]), xytext=(lr[km] / 80, ema[km] + 6),
                fontsize=8, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
    ax.axvline(lr[km] / 10, color=EDGE[1], ls=":", lw=1.2)
    ax.text(lr[km] / 10 * 1.1, 60, "önerilen\n(÷10)", fontsize=8,
            color=EDGE[1])
    ax.set_ylim(0, 120)
    ax.set_xlabel("öğrenme oranı (logaritmik, adım başına artar)")
    ax.set_ylabel("EMA kayıp (düzeltilmiş)")
    ax.set_title("LR aralık testi: kayıp hangi lr'de patlıyor?",
                 fontsize=9, color=INK)
    fig.tight_layout()
    _save(fig, yol)


def takvimler(yol):
    rows = oku("b64_takvim.csv")
    t = fl(rows, "adim")
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.6))
    a = axes.ravel()
    for ad, c in [("sabit", MUTED), ("basamak", EDGE[0]),
                  ("ustel", EDGE[1]), ("kosinus", EDGE[2]),
                  ("isinma_kosinus", EDGE[3])]:
        a[0].plot(t, fl(rows, ad), color=c, lw=1.5, label=ad)
    a[0].set_title("Takvim şekilleri (lr0 = 0,01, 300 adım)", fontsize=9,
                   color=INK)
    a[0].set_xlabel("adım")
    a[0].set_ylabel("öğrenme oranı")
    a[0].legend(fontsize=7, frameon=False, ncol=2, loc="lower left")
    tk = oku("b64_takvim_test.csv")
    names = [r["takvim"] for r in tk]
    mu = fl(tk, "test_ort")
    sd = fl(tk, "test_sd")
    a[1].errorbar(range(len(names)), mu, yerr=sd, fmt="o", color=EDGE[0],
                  capsize=5, ms=7)
    a[1].set_xticks(range(len(names)))
    a[1].set_xticklabels(names, fontsize=8)
    a[1].set_xlim(-0.5, len(names) - 0.5)
    a[1].set_ylabel("test doğruluğu")
    a[1].set_title("MLP, Adam, test doğruluğu (5 tohum)", fontsize=9,
                   color=INK)
    d = oku("b64_isinma_derin.csv")
    mods = [r["mod"] for r in d]
    tp = fl(d, "ilk3_tepe")
    son = fl(d, "son_egitim_kayip")
    x = np.arange(len(mods))
    a[2].bar(x - 0.18, tp, 0.36, color=FILL[3], edgecolor=EDGE[3],
             label="ilk 3 epoch tepe kaybı")
    a[2].bar(x + 0.18, son, 0.36, color=FILL[0], edgecolor=EDGE[0],
             label="son egitim kaybı")
    a[2].set_xticks(x)
    a[2].set_xticklabels(mods, fontsize=8)
    a[2].set_title("12 katman, Adam lr=0,01: ısınmanın etkisi",
                   fontsize=9, color=INK)
    a[2].legend(fontsize=7, frameon=False, loc="upper right")
    a[2].set_ylim(0, 2.8)
    a[3].axis("off")
    a[3].text(0.02, 0.85, "Okuma notu", fontsize=10, color=INK,
              weight="bold")
    a[3].text(0.02, 0.62,
              "Isınma, başlangıçta lr'yi 0'dan\n"
              "hedefe doğrusal çıkarır. Adam'ın ikinci\n"
              "moment tahmini birkaç adım gerektirir;\n"
              "derin ağda bu süre dolmadan büyük adım\n"
              "kayıbı yükseltir.", fontsize=8.5, color=INK,
              va="top")
    fig.tight_layout()
    _save(fig, yol)


def baslatma(yol):
    rows = oku("b64_baslatma.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    kombo = [("kucuk", "küçük (0,01)", MUTED, "-"),
             ("xavier", "Xavier", EDGE[2], "-"),
             ("he", "He", EDGE[0], "-"),
             ("he+BN", "He + BN", EDGE[1], "--")]
    for ad, lab, c, ls in kombo:
        sat = [r for r in rows if r["init"] == ad]
        k = fl(sat, "katman")
        a1.semilogy(k, fl(sat, "aktivasyon_std"), color=c, ls=ls, lw=1.6,
                    marker="o", ms=2.5, label=lab)
        a2.semilogy(k, fl(sat, "gradyan_norm"), color=c, ls=ls, lw=1.6,
                    marker="o", ms=2.5, label=lab)
    a1.set_xlabel("katman")
    a1.set_ylabel("aktivasyon std (log)")
    a1.set_title("İleri geçiş: sinyal nerede sönüyor?", fontsize=9,
                 color=INK)
    a1.legend(fontsize=8, frameon=False)
    a2.set_xlabel("katman")
    a2.set_ylabel("ağırlık gradyanı normu (log)")
    a2.set_title("Geri geçiş: gradyan nerede kayboluyor?", fontsize=9,
                 color=INK)
    a2.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    _save(fig, yol)


def sema(yol):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.6))
    for ax in (a1, a2):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")
    a1.set_title("BatchNorm (eğitim): batch istatistikleri", fontsize=9,
                 color=INK)
    _box(a1, 0.3, 7.6, 3.0, 1.4, "girdi x\n(N × D)", FILL[0], EDGE[0],
         fs=9)
    _box(a1, 4.0, 7.6, 2.8, 1.4, "μ, σ²\n(sütun ort.)", FILL[1], EDGE[1],
         fs=9)
    _box(a1, 0.3, 4.6, 3.0, 1.4, "x̂ = (x − μ)/√(σ²+ε)", FILL[2], EDGE[2],
         fs=9)
    _box(a1, 4.0, 4.6, 2.8, 1.4, "y = γ x̂ + β", FILL[3], EDGE[3], fs=9)
    _box(a1, 7.3, 4.6, 2.5, 1.4, "sonraki\nkatman", FILL[4], EDGE[4],
         fs=9)
    _box(a1, 4.0, 1.4, 2.8, 1.8, "hareketli ort.\nμ_run, σ²_run\n(çıkarım için)",
         FILL[0], EDGE[0], fs=8)
    _arrow(a1, 1.8, 7.6, 1.8, 6.0, col=EDGE[0])
    _arrow(a1, 3.3, 8.3, 4.0, 8.3, col=EDGE[0])
    _arrow(a1, 3.3, 5.3, 4.0, 5.3, col=EDGE[0])
    _arrow(a1, 6.8, 5.3, 7.3, 5.3, col=EDGE[0])
    a1.text(0.3, 2.6, "Dağılımı normalize et, sonra\nγ ve β ile öğrenilebilir\n"
            "ölçek/kaydırma ver.", fontsize=8, color=INK, va="top")
    a2.set_title("Dropout: eğitim ve çıkarım", fontsize=9, color=INK)
    _box(a2, 0.3, 7.4, 3.0, 1.6, "eğitim:\nrastgele maske\nm ~ Bernoulli(1−p)",
         FILL[1], EDGE[1], fs=8.5)
    _box(a2, 4.0, 7.4, 3.2, 1.6, "y = x · m / (1−p)\nbeklenen değer = x",
         FILL[3], EDGE[3], fs=8.5)
    _box(a2, 0.3, 3.4, 3.0, 1.6, "çıkarım:\ndropout kapalı\n(model.eval())",
         FILL[0], EDGE[0], fs=8.5)
    _box(a2, 4.0, 3.4, 3.2, 1.6, "y = x\n(maske yok, ölçek yok)",
         FILL[2], EDGE[2], fs=8.5)
    _arrow(a2, 3.3, 8.2, 4.0, 8.2, col=EDGE[1])
    _arrow(a2, 3.3, 4.2, 4.0, 4.2, col=EDGE[0])
    a2.text(0.3, 1.6, "Ters ölçekleme (1/(1−p)) eğitimde\nyapılır; çıkarım aynı kalır.\n"
            "Model.eval() unutulursa çıkarımda\nmaske yine uygulanır.",
            fontsize=8, color=INK, va="top")
    fig.tight_layout()
    _save(fig, yol)


def klip_artik(yol):
    k = oku("b64_klip.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for mod, c in [("kirpmasiz", EDGE[3]), ("kirpmali", EDGE[1])]:
        sat = [r for r in k if r["mod"] == mod]
        a = fl(sat, "adim")
        a1.semilogy(a, fl(sat, "gradyan_norm"), color=c, lw=1.2,
                    label=mod)
        a2.plot(a, fl(sat, "kayip"), color=c, lw=1.4, label=mod)
    a1.axhline(1.0, color=MUTED, ls=":", lw=1.0)
    a1.text(4, 0.62, "max_norm = 1", fontsize=8, color=MUTED)
    a1.set_xlabel("adım")
    a1.set_ylabel("gradyan normu (kırpmadan önce, log)")
    a1.set_title("20 katman, SGD lr=0,5: norm", fontsize=9, color=INK)
    a1.legend(fontsize=8, frameon=False)
    a2.set_xlabel("adım")
    a2.set_ylabel("mini-batch kaybı")
    a2.set_title("Kayıp: kırpma ile öğrenme sürüyor", fontsize=9,
                 color=INK)
    a2.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    _save(fig, yol)


def teshis(yol):
    rows = oku("b64_teshis.csv")
    vakalar = [("A_yuksek_lr", "A: yüksek lr (SGD 2,0)"),
               ("B_dusuk_lr", "B: düşük lr (SGD 1e-4)"),
               ("C_asiri_uydurma", "C: aşırı uydurma (100 örnek)"),
               ("D_yetersiz", "D: yetersiz (2 birim)"),
               ("E_sizinti", "E: veri sızıntısı"),
               ("F_etiket_karisik", "F: etiketlerin %31'i yanlış")]
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.4))
    for a, (vk, baslik) in zip(axes.ravel(), vakalar):
        sat = [r for r in rows if r["vaka"] == vk]
        ep = fl(sat, "epoch")
        a.plot(ep, fl(sat, "tr_loss"), color=ACCENT, lw=1.5,
               label="eğitim kaybı")
        a.plot(ep, fl(sat, "va_loss"), color=EDGE[0], lw=1.5,
               ls="--", label="doğrulama kaybı")
        a.set_title(baslik, fontsize=9, color=INK)
        a.set_xlabel("epoch", fontsize=8)
        a.set_ylabel("kayıp", fontsize=8)
        a.tick_params(labelsize=7)
        if vk == "E_sizinti":
            a.set_yscale("log")
    axes[0, 0].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    _save(fig, yol)


def arama(yol):
    rows = oku("b64_arama_tablo.csv")
    lrs = sorted(set(float(r["lr"]) for r in rows))
    dos = sorted(set(float(r["dropout"]) for r in rows))
    Z = np.zeros((len(dos), len(lrs)))
    for r in rows:
        i = dos.index(float(r["dropout"]))
        j = lrs.index(float(r["lr"]))
        Z[i, j] = float(r["val"])
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    im = ax.imshow(Z, origin="lower", aspect="auto", cmap="YlOrBr",
                   vmin=0.1, vmax=1.0)
    ax.set_xticks(range(len(lrs)))
    ax.set_xticklabels(["%.0e" % v for v in lrs], fontsize=8)
    ax.set_yticks(range(len(dos)))
    ax.set_yticklabels(["%.1f" % v for v in dos], fontsize=8)
    ax.set_xlabel("öğrenme oranı (log aralıkta 7 değer)")
    ax.set_ylabel("dropout oranı")
    izg_x = [0, 3, 6]
    izg_y = [0, 2, 5]
    for i in izg_y:
        for j in izg_x:
            ax.plot(j, i, "s", mfc="none", mec=ACCENT, ms=13, mew=1.5)
    for i in range(len(dos)):
        for j in range(len(lrs)):
            ax.text(j, i, "%.2f" % Z[i, j], ha="center", va="center",
                    fontsize=6.5,
                    color="white" if Z[i, j] > 0.6 else INK)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03,
                 label="doğrulama doğruluğu")
    ax.set_title("Izgara (kırmızı kare) 9 noktada tarar; lr en önemli boyut",
                 fontsize=9, color=INK)
    fig.tight_layout()
    _save(fig, yol)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    yorunge(os.path.join(GORSEL, "b64_yorunge.png"))
    optim_egri(os.path.join(GORSEL, "b64_optim_egri.png"))
    gurultu_batch(os.path.join(GORSEL, "b64_gurultu_batch.png"))
    lr_aralik(os.path.join(GORSEL, "b64_lr_aralik.png"))
    takvimler(os.path.join(GORSEL, "b64_takvimler.png"))
    baslatma(os.path.join(GORSEL, "b64_baslatma.png"))
    sema(os.path.join(GORSEL, "b64_bn_dropout_sema.png"))
    klip_artik(os.path.join(GORSEL, "b64_klip.png"))
    teshis(os.path.join(GORSEL, "b64_teshis_katalog.png"))
    arama(os.path.join(GORSEL, "b64_arama_isi.png"))
    print("tamam")
