# -*- coding: utf-8 -*-
"""Bolum 72 sekilleri: uretken model aileleri, autoencoder/VAE
mimarisi, PCA karsilastirmasi, kodek egrileri, VAE gizil uzayi, GAN
mod cokmesi, difuzyon surecleri, digits uretimleri, adim-kalite,
aile karsilastirmasi. Olcum verisi engine/veri/b72_*'den okunur."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import csv
import os
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK,
                      MUTED, RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOR = os.path.join(ROOT, "gorseller")
VERI = os.path.join(HERE, "veri")
RENK = [EDGE[0], EDGE[1], EDGE[2], EDGE[3], EDGE[4]]


def oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tuval(ax, xl=(0, 10), yl=(0, 6)):
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.axis("off")


# --------------------------------------------------------------- Sekil 72.1
def aileler_harita(yol):
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    tuval(ax, (0, 14), (0, 7))
    _box(ax, 4.9, 6.0, 4.2, 0.8, "Üretken modeller\np(x) ya da p(x, y)",
         FILL[0], EDGE[0], fs=10.5, bold=True)
    aileler = [
        ("Otoregresif", "p(x)=Π p(x_i|x_<i)\nBölüm 70",
         FILL[1], EDGE[1]),
        ("Gizil\ndeğişkenli", "z → x, ELBO\nAE, VAE (bu bölüm)",
         FILL[2], EDGE[2]),
        ("Çekişmeli", "Üretici ↔\nayırt edici\nGAN (bu bölüm)",
         FILL[3], EDGE[3]),
        ("Akış\n(flow)", "Tersinir dönüşüm\nkesin olabilirlik\n(genel bilgi)",
         FILL[4], EDGE[4]),
        ("Skor /\ndifüzyon", "Gürültü giderme\nDDPM, DDIM\n(bu bölüm)",
         FILL[0], EDGE[0]),
    ]
    xs = [0.2, 2.9, 5.6, 8.3, 11.0]
    for (ad, metin, f, e), x in zip(aileler, xs):
        _arrow(ax, 7.0, 6.0, x + 1.25, 4.6, col=ACCENT_L, lw=1.2)
        _box(ax, x, 2.6, 2.5, 2.0, ad + "\n" + metin, f, e, fs=7.6)
    ax.text(0.2, 1.4, "Her ailenin ortak sorusu: yeni bir örnek nasıl "
            "üretilir, ve\nüretilen örnek ne kadar gerçek ve ne kadar "
            "çeşitli?", fontsize=9.5, color=INK, va="center")
    ax.text(0.2, 0.5, "Kalıp: ayırt edici p(y|x) (Bölüm 62) → üretken "
            "p(x) ya da p(x, y)", fontsize=9.5, color=MUTED, va="center")
    _save(fig, os.path.join(GOR, "b72_aileler_harita.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.2
def ae_vae_mimari(yol):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    tuval(a1, (0, 10), (0, 7))
    tuval(a2, (0, 10), (0, 7))
    a1.set_title("Autoencoder: darboğaz", fontsize=10.5, color=INK)
    _box(a1, 0.3, 2.9, 2.0, 1.2, "x\n(64 piksel)", FILL[0], EDGE[0],
         fs=9)
    _box(a1, 3.2, 2.9, 2.2, 1.2, "Kodlayıcı\nf_φ", FILL[1], EDGE[1],
         fs=9)
    _box(a1, 6.1, 2.9, 1.7, 1.2, "z\n(gizil)", FILL[2], EDGE[2], fs=9,
         bold=True)
    _box(a1, 8.1, 2.9, 1.7, 1.2, "x̂", FILL[0], EDGE[0], fs=10)
    _arrow(a1, 2.3, 3.5, 3.2, 3.5)
    _arrow(a1, 5.4, 3.5, 6.2, 3.5)
    _arrow(a1, 7.7, 3.5, 8.1, 3.5)
    a1.text(5.0, 2.1, "Çözücü g_θ", fontsize=8.6, color=MUTED,
            ha="center")
    a1.text(5.0, 1.4, "L = ||x − g_θ(f_φ(x))||²", fontsize=9.5,
            ha="center", color=INK)
    a1.text(5.0, 0.6, "gizil boyut < girdi boyutu: sıkıştırma",
            fontsize=8.6, ha="center", color=MUTED)

    tuval(a2, (0, 10), (0, 7))
    a2.set_title("VAE: yeniden parametrelendirme", fontsize=10.5,
                 color=INK)
    _box(a2, 0.2, 2.9, 1.7, 1.2, "x", FILL[0], EDGE[0], fs=10)
    _box(a2, 2.4, 3.9, 1.9, 0.9, "μ(x)", FILL[1], EDGE[1], fs=9)
    _box(a2, 2.4, 2.0, 1.9, 0.9, "log σ²(x)", FILL[1], EDGE[1], fs=9)
    _box(a2, 4.8, 3.9, 2.0, 0.9, "ε ~ N(0, I)", FILL[4], EDGE[4], fs=9)
    _box(a2, 4.6, 2.9, 2.4, 0.9, "z = μ + σ⊙ε", FILL[2], EDGE[2],
         fs=8.5, bold=True)
    _box(a2, 7.6, 2.9, 2.2, 1.2, "x̂ ~ p(x|z)", FILL[0], EDGE[0], fs=8.5)
    _arrow(a2, 1.9, 3.7, 2.4, 4.3)
    _arrow(a2, 1.9, 3.3, 2.4, 2.5)
    _arrow(a2, 4.3, 4.3, 4.6, 4.3)
    _arrow(a2, 4.3, 2.5, 4.6, 3.2)
    _arrow(a2, 7.0, 3.35, 7.6, 3.35)
    a2.text(5.0, 1.4, "L = −E[log p(x|z)] + KL(q(z|x) ‖ N(0,I))",
            fontsize=9, ha="center", color=INK)
    a2.text(5.0, 0.6, "ε dışarıda: gradyan μ ve σ'dan geçer",
            fontsize=8.6, ha="center", color=MUTED)
    _save(fig, os.path.join(GOR, "b72_ae_vae_mimari.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.3
def pca_ae(yol):
    rows = oku_csv("b72_pca_ae.csv")
    k = np.array([float(r["k"]) for r in rows])
    pm = np.array([float(r["pca_mse"]) for r in rows])
    am = np.array([float(r["ae_mse"]) for r in rows])
    asd = np.array([float(r["ae_sd"]) for r in rows])
    ac = np.array([float(r["aci_deg"]) for r in rows])
    acsd = np.array([float(r["aci_sd"]) for r in rows])
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 3.8))
    a.plot(k, pm, "o-", color=EDGE[0], lw=1.6, label="PCA")
    a.errorbar(k, am, yerr=asd, fmt="s--", color=ACCENT, lw=1.2,
               capsize=3, label="Doğrusal AE (3 tohum)")
    a.set_xlabel("gizil boyut k", color=INK)
    a.set_ylabel("test MSE", color=INK)
    a.set_xticks(k)
    a.set_title("(a) Yeniden yapılandırma hatası", fontsize=10,
                color=INK)
    a.legend(fontsize=8.5, frameon=False)
    b.errorbar(k, ac, yerr=acsd, fmt="o-", color=EDGE[1], capsize=3)
    b.set_xlabel("gizil boyut k", color=INK)
    b.set_ylabel("en büyük ana açı (derece)", color=INK)
    b.set_xticks(k)
    b.set_title("(b) Alt uzay farkı (0° = aynı uzay)", fontsize=10,
                color=INK)
    for ax in (a, b):
        ax.grid(alpha=0.25, color=RULE)
        ax.tick_params(colors=MUTED)
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_pca_ae.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.4
def kodek_oran(yol):
    rows = oku_csv("b72_kodek.csv")

    def seri(codec, p, alan):
        pts = sorted([r for r in rows if r["codec"] == codec and
                      float(r["p"]) == p], key=lambda r: float(r["R"]))
        return ([float(r["R"]) for r in pts],
                [float(r[alan]) for r in pts],
                [float(r[alan + "_sd"]) for r in pts])

    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 3.9))
    stiller = {"AE": ("o-", ACCENT), "PCA": ("s-", EDGE[0]),
               "DCT": ("^-", EDGE[2])}
    for codec, (st, c) in stiller.items():
        x, y, e = seri(codec, 0.0, "mse")
        a.errorbar(x, y, yerr=e, fmt=st, color=c, capsize=2,
                   label=codec, lw=1.4, ms=4)
        x, y, e = seri(codec, 0.0, "acc")
        b.errorbar(x, y, yerr=e, fmt=st, color=c, capsize=2,
                   label=codec + " (p=0)", lw=1.4, ms=4)
        x, y, e = seri(codec, 0.05, "acc")
        b.plot(x, y, "--", color=c, lw=1.1, alpha=0.8,
               label=codec + " (p=0,05)")
    a.set_yscale("log")
    a.set_xlabel("bit bütçesi R = 16 · b (bit / görüntü)", color=INK)
    a.set_ylabel("test MSE (log)", color=INK)
    a.set_title("(a) Bozulma: bit bütçesine göre", fontsize=10,
                color=INK)
    a.legend(fontsize=8, frameon=False)
    b.set_xlabel("bit bütçesi R = 16 · b (bit / görüntü)", color=INK)
    b.set_ylabel("sınıflandırıcı doğruluğu", color=INK)
    b.set_title("(b) Görev doğruluğu: kanal gürültüsüz ve p=0,05",
                fontsize=10, color=INK)
    b.legend(fontsize=6.8, frameon=False, ncol=2)
    for ax in (a, b):
        ax.grid(alpha=0.25, color=RULE)
        ax.tick_params(colors=MUTED)
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_kodek_oran.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.5
def vae_gizil(yol):
    d = np.load(os.path.join(VERI, "b72_vae2d.npz"))
    fig = plt.figure(figsize=(9.6, 6.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.55])
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, :])
    sc = a.scatter(d["mu2"][:, 0], d["mu2"][:, 1], c=d["y2"],
                   cmap="tab10", s=6, alpha=0.8)
    a.set_title("(a) 2B gizil uzay (test ortalamaları)", fontsize=10,
                color=INK)
    a.set_xlabel("z₁", color=INK)
    a.set_ylabel("z₂", color=INK)
    a.grid(alpha=0.2, color=RULE)
    g = d["grid"]
    mosaik = np.ones((15 * 9, 15 * 9))
    for i in range(15):
        for j in range(15):
            mosaik[i * 9:i * 9 + 8, j * 9:j * 9 + 8] = g[i, j]
    b.imshow(mosaik, cmap="gray", vmin=0, vmax=1)
    b.set_title("(b) Gizil ızgara çözümü (z ∈ [−2, 2]²)", fontsize=10,
                color=INK)
    b.axis("off")
    e = d["ezgi"]
    seri = np.ones((8, 10 * 9))
    for i in range(10):
        seri[:, i * 9:i * 9 + 8] = e[i]
    c.imshow(seri, cmap="gray", vmin=0, vmax=1)
    c.set_title("(c) Gizil uzayda doğrusal enterpolasyon: "
                "etiket 0 → etiket 7", fontsize=10, color=INK)
    c.axis("off")
    _save(fig, os.path.join(GOR, "b72_vae_gizil.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.6
def gan_mod(yol):
    rows = oku_csv("b72_gan_mod.csv")
    ornek = np.load(os.path.join(VERI, "b72_gan_ornek.npz"))
    fig = plt.figure(figsize=(9.6, 6.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.0])
    a = fig.add_subplot(gs[0, :])
    ad = {"doyan": "minimaks (doyan)", "dogal": "doymayan",
          "dogal_yl": "doymayan, G lr=1e-3", "wgan": "WGAN-GP"}
    renk = {"doyan": EDGE[0], "dogal": EDGE[1], "dogal_yl": ACCENT,
            "wgan": EDGE[2]}
    for v in ["doyan", "dogal", "dogal_yl", "wgan"]:
        xs = sorted({int(r["iterasyon"]) for r in rows})
        ort = []
        for it in xs:
            m = [float(r["modes"]) for r in rows
                 if r["varyant"] == v and int(r["iterasyon"]) == it]
            ort.append(np.mean(m))
        a.plot(xs, ort, "-", color=renk[v], lw=1.6, label=ad[v])
    a.set_xlabel("üretici iterasyonu", color=INK)
    a.set_ylabel("kapsanan mod sayısı (0–8)", color=INK)
    a.set_ylim(-0.2, 8.5)
    a.set_title("(a) Mod kapsamı eğitim boyunca (3 tohum ortalaması)",
                fontsize=10, color=INK)
    a.legend(fontsize=8, frameon=False, ncol=2)
    a.grid(alpha=0.25, color=RULE)
    for i, v in enumerate(["doyan", "dogal_yl", "wgan"]):
        ax = fig.add_subplot(gs[1, i])
        x = ornek[v]
        ax.scatter(x[:, 0], x[:, 1], s=2, color=renk[v], alpha=0.6)
        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)
        ax.set_aspect("equal")
        ax.set_title("(%s) %s" % ("bcd"[i], ad[v]), fontsize=8.8,
                     color=INK)
        ax.tick_params(labelsize=7, colors=MUTED)
        ax.grid(alpha=0.2, color=RULE)
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_gan_modcoek.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.7
def difuzyon_2d(yol):
    d = np.load(os.path.join(VERI, "b72_diff2d.npz"))
    fig, axes = plt.subplots(2, 5, figsize=(9.6, 4.4))
    for j, t in enumerate(d["fwd_t"]):
        ax = axes[0, j]
        x = d["fwd"][j]
        ax.scatter(x[:, 0], x[:, 1], s=2, color=EDGE[0], alpha=0.6)
        ax.set_title("ileri  t=%d" % t, fontsize=8.5, color=INK)
    for j, t in enumerate(d["rev_t"]):
        ax = axes[1, j]
        x = d["rev"][j]
        ax.scatter(x[:, 0], x[:, 1], s=2, color=ACCENT, alpha=0.6)
        ax.set_title("ters  t=%d" % t, fontsize=8.5, color=INK)
    for ax in axes.ravel():
        ax.set_xlim(-3.2, 3.2)
        ax.set_ylim(-3.2, 3.2)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=6, colors=MUTED)
        ax.grid(alpha=0.2, color=RULE)
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_difuzyon_2d.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.8
def digits_uretim(yol):
    d = np.load(os.path.join(VERI, "b72_digits_izgara.npz"))
    sira = [("gercek", "Gerçek test"), ("vae", "VAE (d=8)"),
            ("dcgan", "DCGAN"), ("ddpm", "DDPM (T=200)")]
    fig, axes = plt.subplots(1, 4, figsize=(9.6, 3.0))
    for ax, (k, ad) in zip(axes, sira):
        x = d[k]
        m = np.ones((4 * 9, 4 * 9))
        for i in range(4):
            for j in range(4):
                m[i * 9:i * 9 + 8, j * 9:j * 9 + 8] = x[i * 4 + j]
        ax.imshow(m, cmap="gray", vmin=0, vmax=1)
        ax.set_title(ad, fontsize=9.5, color=INK)
        ax.axis("off")
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_digits_uretim.png"))
    plt.close(fig)


# --------------------------------------------------------------- Sekil 72.9
def adim_kalite(yol):
    rows = oku_csv("b72_adim_kalite.csv")
    ddim = [r for r in rows if r["yontem"] == "DDIM"]
    ddpm = [r for r in rows if r["yontem"] == "DDPM"][0]
    s = np.array([int(r["adim"]) for r in ddim])
    fid = np.array([float(r["fid"]) for r in ddim])
    pr = np.array([float(r["precision"]) for r in ddim])
    rc = np.array([float(r["recall"]) for r in ddim])
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 3.7))
    a.plot(s, fid, "o-", color=ACCENT, label="DDIM (η=0)")
    a.plot([int(ddpm["adim"])], [float(ddpm["fid"])], "D",
           color=EDGE[0], ms=7, label="DDPM (ancestral, T=200)")
    a.set_xscale("log")
    a.set_xlabel("örnekleme adım sayısı", color=INK)
    a.set_ylabel("mini-FID (düşük = iyi)", color=INK)
    a.set_title("(a) Adım sayısı ve Fréchet mesafesi", fontsize=10,
                color=INK)
    a.legend(fontsize=8, frameon=False)
    b.plot(s, pr, "o-", color=EDGE[1], label="kesinlik")
    b.plot(s, rc, "s-", color=EDGE[2], label="geri çağırma")
    b.set_xscale("log")
    b.set_xlabel("örnekleme adım sayısı", color=INK)
    b.set_ylabel("oran", color=INK)
    b.set_title("(b) Kesinlik ve geri çağırma (DDIM)", fontsize=10,
                color=INK)
    b.legend(fontsize=8, frameon=False)
    for ax in (a, b):
        ax.grid(alpha=0.25, color=RULE)
        ax.tick_params(colors=MUTED)
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_adim_kalite.png"))
    plt.close(fig)


# -------------------------------------------------------------- Sekil 72.10
def aile_karsilastirma(yol):
    rows = oku_csv("b72_aileler.csv")
    ad = [r["aile"] for r in rows]
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 5.4))
    bar_r = [EDGE[0], EDGE[1], EDGE[2], "#B9B4AA"]
    metrik = [("fid", "mini-FID (düşük = iyi)"),
              ("precision", "kesinlik (yüksek = iyi)"),
              ("recall", "geri çağırma (yüksek = iyi)"),
              ("ms", "ms / örnek (CPU, toplu, log)")]
    for ax, (k, baslik) in zip(axes.ravel(), metrik):
        v = np.array([float(r[k]) for r in rows])
        if k == "ms":
            v = np.where(v > 0, v, np.nan)
        ax.bar(range(len(ad)), v, color=bar_r)
        ax.set_xticks(range(len(ad)))
        ax.set_xticklabels(ad, fontsize=7.5, rotation=12)
        ax.set_title(baslik, fontsize=9, color=INK)
        ax.tick_params(colors=MUTED, labelsize=7)
        ax.grid(alpha=0.25, color=RULE, axis="y")
        if k == "ms":
            ax.set_yscale("log")
    fig.tight_layout()
    _save(fig, os.path.join(GOR, "b72_aile_karsilastirma.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(GOR, exist_ok=True)
    aileler_harita(None)
    ae_vae_mimari(None)
    pca_ae(None)
    kodek_oran(None)
    vae_gizil(None)
    gan_mod(None)
    difuzyon_2d(None)
    digits_uretim(None)
    adim_kalite(None)
    aile_karsilastirma(None)
    print("10 sekil uretildi.")
