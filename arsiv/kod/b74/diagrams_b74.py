# -*- coding: utf-8 -*-
"""Bolum 74 - Pekistirmeli ogrenme diyagramlari.

Olcum grafikleri engine/veri/b74_*.csv dosyalarindan okunur; bu CSV'leri
deney betikleri uretir (Temp altindaki b74 klasoru). Kavramsal sekiller
veri okumaz.
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


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bant(ax, x, ort, sd, renk, etiket, ls="-"):
    ax.plot(x, ort, color=renk, lw=1.8, ls=ls, label=etiket)
    ax.fill_between(x, ort - sd, ort + sd, color=renk, alpha=0.18, lw=0)


def ajan_ortam(yol):
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 1.0, 3.6, 3.6, 1.4, "Ajan\n(politika π)", fill=FILL[0],
         edge=EDGE[0], fs=12, bold=True)
    _box(ax, 9.4, 3.6, 3.6, 1.4, "Ortam\n(geçiş P, ödül R)", fill=FILL[1],
         edge=EDGE[1], fs=12, bold=True)
    _arrow(ax, 4.7, 4.5, 9.3, 4.5, col=ACCENT, rad=0.0)
    ax.text(7.0, 4.75, "eylem  $a_t$", ha="center", fontsize=11, color=INK)
    _arrow(ax, 9.3, 3.9, 4.7, 3.9, col=ACCENT_L, rad=0.0)
    ax.text(7.0, 3.35, "durum  $s_{t+1}$,  ödül  $r_{t+1}$", ha="center",
            fontsize=11, color=INK)
    ax.text(7.0, 1.6, "Her adımda: ajan gözlemler, eylem seçer, ortam yanıt "
            "verir.\nAmaç, beklenen toplam indirimli ödülü en büyütmek.",
            ha="center", fontsize=10.5, color=MUTED)
    return _save(fig, os.path.join(GORSEL, yol))


def bandit(yol):
    veri = oku("b74_bandit.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for ad, renk in (("eps-acgozlu (0,1)", EDGE[3]), ("UCB1", EDGE[0]),
                     ("Thompson", EDGE[1])):
        satir = [r for r in veri if r["algoritma"] == ad]
        t = np.array([int(r["t"]) for r in satir])
        m = np.array([float(r["ort"]) for r in satir])
        s = np.array([float(r["sd"]) for r in satir])
        bant(ax, t, m, s, renk, ad)
    ax.set_xlabel("adım t")
    ax.set_ylabel("birikmiş pişmanlık R(t)")
    ax.set_title("Haydut: 5 tohumun ortalaması ± 1 sapma (K=5, T=2000)",
                 fontsize=11)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def izgara_deger(yol):
    veri = oku("b74_grid_v.csv")
    n = 5
    V = np.zeros((n, n))
    pi = np.zeros((n, n), dtype=int)
    for r in veri:
        V[int(r["satir"]), int(r["sutun"])] = float(r["V"])
        pi[int(r["satir"]), int(r["sutun"])] = int(r["politika"])
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(V, cmap="cividis")
    for i in range(n):
        for j in range(n):
            ax.text(j, i - 0.24, "%.2f" % V[i, j], ha="center",
                    va="center", color="white", fontsize=8.5)
            if i * n + j == n * n - 1:
                continue
            dr, dc = [(-0.28, 0), (0, 0.28), (0.28, 0), (0, -0.28)][pi[i, j]]
            ax.annotate("", xy=(j + dc, i + 0.12 + dr),
                        xytext=(j - dc, i + 0.12 - dr),
                        arrowprops=dict(arrowstyle="-|>", color=ACCENT,
                                        lw=1.6))
    ax.add_patch(plt.Rectangle((n - 1.5, n - 1.5), 1, 1, fill=False,
                               ec=ACCENT, lw=2.4))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("5×5 ızgara: V* (renk, sayı) ve optimal eylem (ok)\n"
                 "kayganlık 0,1; γ = 0,9; hedef sağ-alt köşe",
                 fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="V*(s)")
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def vi_yakinsama(yol):
    veri = oku("b74_vi_gamma.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0))
    renkler = {"0.50": EDGE[1], "0.90": EDGE[0], "0.99": EDGE[3]}
    for senaryo, ax, baslik in (
            ("izgara", axes[0], "5×5 ızgara (hedef mutlak)"),
            ("dongu", axes[1], "tek durum, ödül +1 (sonsuz döngü)")):
        for g, renk in renkler.items():
            satir = [r for r in veri if r["senaryo"] == senaryo
                     and r["gamma"] == g]
            k = np.array([int(r["iter"]) for r in satir])
            kal = np.array([float(r["kalinti"]) for r in satir])
            ax.semilogy(k, kal, color=renk, lw=1.8, label="γ = %s" % g)
            if senaryo == "dongu":
                gv = float(g)
                ax.semilogy(k, gv ** k, color=renk, ls=":", lw=1.0)
        ax.set_xlabel("değer iterasyonu adımı k")
        ax.set_title(baslik, fontsize=10)
        ax.grid(color=RULE, lw=0.6, which="both")
        ax.set_ylim(1e-9, 2)
    axes[0].set_ylabel("kalıntı  max|V_{k+1} − V_k|")
    axes[1].text(60, 3e-1, "tek durum: kalıntı = γ^k (kesikli çizgiyle "
                 "örtüşür)", fontsize=9, color=MUTED)
    axes[0].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def ucurum(yol):
    yollar = oku("b74_cliff_yol.csv")
    egriler = oku("b74_cliff_egri.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.0),
                             gridspec_kw={"width_ratios": [1.1, 1.0]})
    ax = axes[0]
    H, W = 4, 12
    ax.set_xlim(-0.5, W - 0.5)
    ax.set_ylim(H - 0.5, -0.5)
    for r in range(H):
        for c in range(W):
            renk = FILL[3] if (r == 3 and 1 <= c <= 10) else "white"
            ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                       fc=renk, ec=RULE, lw=0.8))
    ax.text(0, 3, "B", ha="center", va="center", fontsize=10)
    ax.text(11, 3, "H", ha="center", va="center", fontsize=10)
    for yontem, renk, dx in (("sarsa", EDGE[1], -0.12),
                             ("qlearn", ACCENT, 0.12)):
        p = [(int(r["r"]), int(r["c"])) for r in yollar
             if r["yontem"] == yontem]
        xs = [c + dx for _, c in p]
        ys = [r + dx for r, _ in p]
        ax.plot(xs, ys, color=renk, lw=2.2,
                label="SARSA" if yontem == "sarsa" else "Q-learning")
    ax.legend(frameon=False, fontsize=8, loc="upper left",
              bbox_to_anchor=(0.0, -0.02))
    ax.set_title("Açgözlü yol (tohum 0)", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    ax2 = axes[1]
    for yontem, renk, ad in (("sarsa", EDGE[1], "SARSA"),
                             ("qlearn", ACCENT, "Q-learning")):
        satir = [r for r in egriler if r["yontem"] == yontem]
        b = np.array([int(r["bolum"]) for r in satir])
        m = np.array([float(r["ort"]) for r in satir])
        s = np.array([float(r["sd"]) for r in satir])
        bant(ax2, b, m, s, renk, ad)
    ax2.set_xlabel("bölüm")
    ax2.set_ylabel("eğitim getirisi (10'lu ortalama)")
    ax2.set_title("Ödül eğrileri, ε = 0,1, 5 tohum", fontsize=10)
    ax2.grid(color=RULE, lw=0.6)
    ax2.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def dqn(yol):
    veri = oku("b74_dqn_egri.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for ad, renk, ls in (("tam", EDGE[0], "-"), ("double", EDGE[1], "-"),
                         ("hedef_yok", EDGE[3], "--"),
                         ("replay_yok", EDGE[2], "--")):
        satir = [r for r in veri if r["yapi"] == ad]
        a = np.array([int(r["adim"]) for r in satir])
        m = np.array([float(r["ort"]) for r in satir])
        s = np.array([float(r["sd"]) for r in satir])
        bant(ax, a, m, s, renk, ad, ls=ls)
    ax.set_xlabel("ortam adımı")
    ax.set_ylabel("değerlendirme getirisi (ε = 0)")
    ax.set_title("DQN, kendi CartPole'umuz: 5 tohum, ortalama ± 1 sapma",
                 fontsize=10)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, ncol=2)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def reinforce(yol):
    veri = oku("b74_pg_varyans.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    for ad, renk in (("taban_yok", EDGE[3]), ("taban_var", EDGE[1])):
        satir = [r for r in veri if r["yontem"] == ad]
        it = np.array([int(r["iter"]) for r in satir])
        m = np.array([float(r["var_ort"]) for r in satir])
        s = np.array([float(r["var_sd"]) for r in satir])
        ax.semilogy(it, m, color=renk, lw=1.8, label=ad.replace("_", " "))
        ax.fill_between(it, np.maximum(m - s, 1e-12), m + s, color=renk,
                        alpha=0.18, lw=0)
    ax.set_xlabel("REINFORCE iterasyonu")
    ax.set_ylabel("parametre başına gradyan varyansı")
    ax.set_title("Gradyan kestiriminin varyansı (5 tohum, M = 10 batch, 20 iterasyonda bir)",
                 fontsize=10)
    ax.grid(color=RULE, lw=0.6, which="both")
    ax.legend(frameon=False)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def ppo_kirpma(yol):
    eps = 0.2
    r = np.linspace(0.4, 1.6, 400)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0), sharey=True)
    for ax, A, baslik in ((axes[0], 1.0, "avantaj A > 0"),
                          (axes[1], -1.0, "avantaj A < 0")):
        ham = r * A
        kirp = np.clip(r, 1 - eps, 1 + eps) * A
        vekil = np.minimum(ham, kirp)
        ax.plot(r, ham, color=MUTED, ls=":", lw=1.2, label="r·A (ham)")
        ax.plot(r, vekil, color=ACCENT, lw=2.2, label="min(r·A, kırpılmış)")
        ax.axvline(1 - eps, color=RULE, lw=1)
        ax.axvline(1 + eps, color=RULE, lw=1)
        ax.set_xlabel("oran r(θ) = π_θ(a|s) / π_θ_eski(a|s)")
        ax.set_title(baslik, fontsize=10)
        ax.grid(color=RULE, lw=0.6)
    axes[0].set_ylabel("vekil amaç")
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def iha_yorunge(yol):
    veri = oku("b74_iha_yorunge.csv")
    t = np.array([float(r["t"]) for r in veri])
    ref = np.array([float(r["referans"]) for r in veri])
    w = np.array([float(r["ruzgar"]) for r in veri])
    fig, axes = plt.subplots(2, 1, figsize=(9.4, 6.0), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1.0]})
    ax = axes[0]
    ax.plot(t, ref, color=MUTED, ls="--", lw=1.2, label="hedef h_ref")
    for kol, ad, renk in (("pid_h", "PID", EDGE[3]),
                          ("nom_h", "PPO (nominal eğitim)", EDGE[2]),
                          ("dr_h", "PPO (alan rastgeleleştirme)", EDGE[1])):
        y = np.array([float(r[kol]) for r in veri])
        ax.plot(t, y, color=renk, lw=1.8, label=ad)
    ax.set_ylabel("irtifa h [m]")
    ax.set_title("Kütle +%20, rüzgâr ×1,5 (DR aralığı içinde), tohum 3001",
                 fontsize=10)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper right", ncol=2)
    ax2 = axes[1]
    ax2.plot(t, w, color=ACCENT_L, lw=1.4, label="rüzgâr ivmesi [m/s²]")
    ax2.set_xlabel("zaman t [s]")
    ax2.set_ylabel("rüzgâr")
    ax2.grid(color=RULE, lw=0.6)
    ax2.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


def alan_kaymasi(yol):
    veri = oku("b74_iha_dr.csv")
    alfa = np.array(sorted({float(r["alfa"]) for r in veri}))
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for ad, renk, ls, kay in (("PID", MUTED, "--", 0.0),
                              ("PPO-nom", EDGE[3], "-", -0.012),
                              ("PPO-DR", EDGE[1], "-", 0.012)):
        satir = [r for r in veri if r["kontrolcu"] == ad]
        satir.sort(key=lambda r: float(r["alfa"]))
        m = np.array([float(r["ort"]) for r in satir])
        s = np.array([float(r["sd"]) for r in satir])
        ax.errorbar(alfa + kay, m, yerr=s, color=renk, ls=ls, marker="o",
                    ms=5, lw=1.8, capsize=3, label=ad)
    pk = oku("b74_pid_ki.csv")
    satir = [r for r in pk if abs(float(r["ki"]) - 0.02) < 1e-9]
    satir.sort(key=lambda r: float(r["alfa"]))
    ax.plot([float(r["alfa"]) + 0.0 for r in satir],
            [float(r["basari"]) for r in satir], color=ACCENT_L, ls=":",
            marker="s", ms=4, lw=1.6, label="PID (ki = 0,02)")
    ax.axvspan(0, 1.0, color=FILL[1], alpha=0.5, lw=0)
    ax.set_xlabel("kayma şiddeti α (0 = nominal; 1 = DR aralığının dışı)")
    ax.set_ylabel("başarı oranı (100 bölüm)")
    ax.set_ylim(-0.05, 1.08)
    ax.set_title("Parametre kayması altında başarı (5 eğitim tohumu)",
                 fontsize=10)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    fig.tight_layout()
    return _save(fig, os.path.join(GORSEL, yol))


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    print(ajan_ortam("b74_ajan_ortam.png"))
    print(bandit("b74_bandit_pismanlik.png"))
    print(izgara_deger("b74_izgara_deger.png"))
    print(vi_yakinsama("b74_vi_yakinsama.png"))
    print(ucurum("b74_ucurum.png"))
    print(dqn("b74_dqn_egri.png"))
    print(reinforce("b74_reinforce_varyans.png"))
    print(ppo_kirpma("b74_ppo_kirpma.png"))
    print(iha_yorunge("b74_iha_yorunge.png"))
    print(alan_kaymasi("b74_alan_kaymasi.png"))
