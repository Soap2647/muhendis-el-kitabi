# -*- coding: utf-8 -*-
"""Bölüm 68 - Dizi Modelleri & Zaman Serisi diyagramları.

Ölçüm grafikleri engine/veri/b68_*.csv dosyalarından okunur; bu dosyalar
arsiv/kod/b68 içindeki t00-t13 betiklerinin çıktısıdır. Kavramsal şekiller
(açılmış RNN, LSTM hücresi, nedensel genişletilmiş konvolüsyon) veri
okumaz.
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


def kol(rows, ad):
    return np.array([float(r[ad]) for r in rows])


def tuval(w, h, xl, yl):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.axis("off")
    return fig, ax


# ---------------------------------------------------------------- 68.1
def bilesen_acf(path):
    """Şekil 68.1: zaman serisi bileşenleri ve otokorelasyon."""
    b = oku("b68_bilesen.csv")
    a = oku("b68_acf.csv")
    t = kol(b, "t")[:300]
    fig, (x1, x2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    x1.plot(t, kol(b, "seri")[:300], color=INK, lw=0.9, label="gözlem")
    x1.plot(t, kol(b, "trend")[:300], color=ACCENT, lw=1.6, ls="--",
            label="trend")
    x1.plot(t, (kol(b, "trend") + kol(b, "mevsim"))[:300],
            color=EDGE[0], lw=1.2, label="trend + mevsim")
    x1.set_xlabel("zaman adımı")
    x1.set_title("Bileşenler (ilk 300 adım)", fontsize=10)
    x1.legend(fontsize=8, frameon=False, loc="upper left")
    k = kol(a, "gecikme")
    x2.vlines(k, 0, kol(a, "acf_seri"), color=ACCENT_L, lw=2.2)
    x2.plot(k, kol(a, "acf_beyaz"), "o", ms=2.5, color=MUTED,
            label="beyaz gürültü")
    bant = kol(a, "bant")[0]
    x2.axhline(bant, color=ACCENT, ls=":", lw=1)
    x2.axhline(-bant, color=ACCENT, ls=":", lw=1)
    x2.set_xlabel("gecikme (adım)")
    x2.set_ylabel("otokorelasyon")
    x2.legend(fontsize=8, frameon=False, loc="upper right")
    x2.set_title("ACF (koyu çubuk: trend+mevsim)", fontsize=10)
    fig.tight_layout()
    return _save(fig, path)


# ---------------------------------------------------------------- 68.2
def bolme_sizinti(path):
    """Şekil 68.2: rastgele ve zamana göre test kümeleri, kNN hatası."""
    m = oku("b68_bolme_maske.csv")
    s = oku("b68_bolme_sonuc.csv")
    hb = kol(m, "hb")
    rt = kol(m, "rastgele_test")
    zt = kol(m, "zaman_test")
    fig, (x1, x2) = plt.subplots(
        2, 1, figsize=(9.6, 4.6), gridspec_kw={"height_ratios": [1, 1.2]})
    x1.scatter(hb[rt == 1], np.full(int(rt.sum()), 1.0), s=3,
               color=ACCENT, label="rastgele bölmenin testi")
    x1.scatter(hb[zt == 1], np.full(int(zt.sum()), 0.0), s=3,
               color=ACCENT_L, label="zamana göre bölmenin testi")
    x1.axvline(14400, color=MUTED, ls="--", lw=1)
    x1.text(14450, 1.35, "eğitim sonu", fontsize=8, color=MUTED)
    x1.set_yticks([0, 1])
    x1.set_yticklabels(["zamana", "rastgele"], fontsize=8)
    x1.set_ylim(-0.5, 1.6)
    x1.set_xlabel("hedef zaman indeksi")
    x1.legend(fontsize=7.5, frameon=False, loc="lower left", ncol=2)
    x1.set_title("Test noktalarının zaman ekseninde dağılımı",
                 fontsize=10)
    etiket = ["kNN\nzaman", "kNN\nrastgele", "Doğrusal\nzaman",
              "Doğrusal\nrastgele"]
    knn = [float(r["mae"]) for r in s if r["yontem"] == "kNN (k=5)"]
    dog = [float(r["mae"]) for r in s if r["yontem"] == "Doğrusal"]
    vals = [knn[0], knn[1], dog[0], dog[1]]
    renk = [ACCENT_L, ACCENT, ACCENT_L, ACCENT]
    x2.bar(range(4), vals, color=renk, width=0.6)
    for i, v in enumerate(vals):
        x2.text(i, v + 0.004, "%.3f" % v, ha="center", fontsize=8)
    x2.set_xticks(range(4))
    x2.set_xticklabels(etiket, fontsize=8)
    x2.set_ylabel("test MAE (A)")
    x2.set_ylim(0, 0.27)
    x2.set_title("Aynı model, iki bölme: rastgele bölme düşük hata verir",
                 fontsize=9.5)
    fig.tight_layout()
    return _save(fig, path)


# ---------------------------------------------------------------- 68.3
def rnn_acilim(path):
    """Şekil 68.3: RNN'in zaman içinde açılımı (kavramsal)."""
    fig, ax = tuval(9.6, 3.6, (0, 14), (0, 7))
    xs = [3.0, 6.9, 10.8]
    girdi = ["$x_{t-1}$", "$x_t$", "$x_{t+1}$"]
    cikti = ["$y_{t-1}$", "$y_t$", "$y_{t+1}$"]
    gizli = ["$h_{t-1}$", "$h_t$"]
    for i, x in enumerate(xs):
        _box(ax, x - 1.0, 2.6, 2.0, 1.6, "RNN\nhücresi", fill=FILL[0],
             edge=EDGE[0], fs=10)
        _arrow(ax, x, 0.9, x, 2.6, col=EDGE[1], lw=1.4)
        _arrow(ax, x, 4.2, x, 5.5, col=EDGE[1], lw=1.4)
        ax.text(x, 0.4, girdi[i], ha="center", fontsize=10)
        ax.text(x, 5.8, cikti[i], ha="center", fontsize=10)
    for i in range(len(xs) - 1):
        _arrow(ax, xs[i] + 1.0, 3.4, xs[i + 1] - 1.0, 3.4, col=ACCENT,
               lw=1.4)
        ax.text((xs[i] + xs[i + 1]) / 2, 3.7, gizli[i], ha="center",
                fontsize=10)
    _arrow(ax, 0.6, 3.4, xs[0] - 1.0, 3.4, col=ACCENT, lw=1.4)
    ax.text(0.5, 3.8, "$h_{t-2}$", fontsize=10)
    _arrow(ax, xs[-1] + 1.0, 3.4, 13.4, 3.4, col=ACCENT, lw=1.4)
    ax.text(12.9, 3.8, "...", fontsize=12, ha="center")
    ax.text(4.9, 1.7, "$W_x$", fontsize=10, color=ACCENT_L)
    ax.text(8.8, 4.6, "$W_h$", fontsize=10, color=ACCENT_L)
    ax.text(3.4, 4.8, "$W_y$", fontsize=10, color=ACCENT_L)
    ax.text(7.0, 6.6, "aynı üç ağırlık matrisi her adımda kullanılır",
            ha="center", fontsize=9, color=MUTED)
    return _save(fig, path)


# ---------------------------------------------------------------- 68.4
def gradyan_adim(path):
    """Şekil 68.4: adım sayısına göre Jacobian çarpımının normu."""
    g = oku("b68_gradyan_adim.csv")
    T = kol(g, "T")
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    stil = [(EDGE[1], "ρ = 0,9"), (INK, "ρ = 1,0"), (ACCENT, "ρ = 1,1")]
    for (c, et), ad in zip(stil, ["rho_0.9", "rho_1.0", "rho_1.1"]):
        ax.semilogy(T, kol(g, ad), color=c, lw=1.8, label=et)
    ax.semilogy(T, 0.9 ** T, color=MUTED, lw=0.9, ls=":",
                label="0,9$^T$ (referans)")
    ax.set_xlabel("adım sayısı T")
    ax.set_ylabel("||∂h$_T$/∂h$_0$||$_2$ (medyan)")
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    return _save(fig, path)


# ---------------------------------------------------------------- 68.5
def lstm_hucre(path):
    """Şekil 68.5: LSTM hücresi (kavramsal)."""
    fig, ax = tuval(9.6, 4.8, (0, 14), (0, 9.2))
    ust = 6.4
    _arrow(ax, 0.4, ust, 13.0, ust, col=INK, lw=2.0)     # hücre durumu
    ax.text(0.2, ust + 0.5, "$c_{t-1}$", fontsize=10)
    ax.text(12.9, ust + 0.5, "$c_t$", fontsize=10)
    for x, sym in [(2.6, "×"), (5.8, "+")]:
        ax.add_patch(plt.Circle((x, ust), 0.38, facecolor="white",
                                edgecolor=ACCENT, lw=1.4))
        ax.text(x, ust, sym, ha="center", va="center", fontsize=12)
    ax.add_patch(plt.Circle((5.8, 4.7), 0.38, facecolor="white",
                            edgecolor=ACCENT, lw=1.4))
    ax.text(5.8, 4.7, "×", ha="center", va="center", fontsize=12)
    # kapılar: f, i, g, o
    kapi = [(2.6, "σ\nunutma $f$", EDGE[0]), (4.6, "σ\ngiriş $i$", EDGE[1]),
            (6.8, "tanh\naday $g$", EDGE[2]), (10.0, "σ\nçıkış $o$", EDGE[4])]
    _arrow(ax, 0.9, 1.0, 10.6, 1.0, col=MUTED, lw=0.8, style="-")
    ax.text(0.2, 0.35, "$[h_{t-1}, x_t]$", fontsize=9)
    for x, et, e in kapi:
        _box(ax, x - 0.9, 2.3, 1.8, 1.1, et, fill=FILL[0], edge=e, fs=8.5)
        _arrow(ax, x, 1.0, x, 2.3, col=e, lw=1.2, style="-")
    _arrow(ax, 2.6, 3.4, 2.6, 5.95, col=EDGE[0], lw=1.2)     # f -> ×
    _arrow(ax, 4.6, 3.4, 5.6, 4.35, col=EDGE[1], lw=1.2)     # i -> ⊗
    _arrow(ax, 6.8, 3.4, 6.0, 4.35, col=EDGE[2], lw=1.2)     # g -> ⊗
    _arrow(ax, 5.8, 5.07, 5.8, 6.0, col=ACCENT, lw=1.2)      # ⊗ -> +
    _box(ax, 9.6, 6.9, 2.0, 0.9, "$\\tanh(c_t)$", fill=FILL[2],
         edge=EDGE[2], fs=9)
    _arrow(ax, 9.6, ust, 9.6, 6.9, col=INK, lw=1.0)           # c -> tanh
    _arrow(ax, 10.0, 3.4, 11.6, 3.95, col=EDGE[4], lw=1.2)    # o -> ⊙
    ax.add_patch(plt.Circle((11.9, 4.3), 0.38, facecolor="white",
                            edgecolor=ACCENT, lw=1.4))
    ax.text(11.9, 4.3, "×", ha="center", va="center", fontsize=12)
    _arrow(ax, 10.6, 7.35, 11.6, 4.7, col=EDGE[2], lw=1.2)    # tanh -> ×
    _arrow(ax, 11.9, 4.68, 11.9, 8.3, col=ACCENT, lw=1.6)     # h_t
    ax.text(12.1, 8.6, "$h_t$", fontsize=10)
    return _save(fig, path)


# ---------------------------------------------------------------- 68.6
def uzun_bagimlilik(path):
    """Şekil 68.6: uzun bağımlılık görevinde T'ye göre doğruluk."""
    r = oku("b68_uzun_bagimlilik.csv")
    modeller = [("rnn", "RNN", ACCENT), ("lstm", "LSTM", EDGE[0]),
                ("gru", "GRU", EDGE[1])]
    Ts = [10, 20, 40, 80]
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    for key, et, c in modeller:
        ort, sd = [], []
        for T in Ts:
            v = [float(x["dogruluk"]) for x in r
                 if x["model"] == key and int(x["T"]) == T]
            ort.append(np.mean(v))
            sd.append(np.std(v, ddof=1))
        ax.errorbar(Ts, ort, yerr=sd, color=c, marker="o", lw=1.6,
                    capsize=3, label=et)
    ax.axhline(0.5, color=MUTED, ls=":", lw=1)
    ax.text(84, 0.5, "şans", va="center", fontsize=8, color=MUTED)
    ax.set_xscale("log")
    ax.set_xticks(Ts)
    ax.set_xticklabels([str(t) for t in Ts])
    ax.set_xlabel("dizi uzunluğu T (adım)")
    ax.set_ylabel("test doğruluğu (3 tohum)")
    ax.set_ylim(0.4, 1.05)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    fig.tight_layout()
    return _save(fig, path)


# ---------------------------------------------------------------- 68.7
def tcn_yigin(path):
    """Şekil 68.7: nedensel genişletilmiş konvolüsyon yığını (kavramsal).
    Her katmanda tek konvolüsyon (K=3); d = 1, 2, 4, 8."""
    fig, ax = tuval(9.6, 4.4, (0, 14), (0, 10))
    xs = 1.6 + np.arange(9) * 1.4
    katman = [("girdi", 0.6), ("d=1", 2.4), ("d=2", 4.2), ("d=4", 6.0),
              ("d=8", 7.8)]
    for ad, y in katman:
        ax.text(0.05, y + 0.25, ad, fontsize=9, color=INK)
        for x in xs:
            ax.add_patch(plt.Circle((x, y + 0.3), 0.15, facecolor="white",
                                    edgecolor=INK, lw=0.9))
    hedef = 8
    for li, d in enumerate([1, 2, 4, 8], 1):
        ykat, yonc = katman[li][1], katman[li - 1][1]
        for k in (0, 1, 2):
            kaynak = hedef - k * d
            if kaynak < 0:
                continue
            _arrow(ax, xs[kaynak], yonc + 0.46, xs[hedef], ykat + 0.14,
                   col=EDGE[1], lw=0.9)
    ax.text(xs[hedef], 9.0, "$y_t$", ha="center", fontsize=10)
    ax.text(0.05, 9.2, "her ok: K=3 konvolüsyonun bir girdisi",
            fontsize=8, color=MUTED)
    ax.text(0.05, 0.05, "nedensel: $y_t$ yalnızca $x_{t}$ ve geçmiş "
            "girdilere bağlı", fontsize=8, color=MUTED)
    return _save(fig, path)


# ---------------------------------------------------------------- 68.8
def tahmin_karsilastir(path):
    """Şekil 68.8: gerçek ve tahmin (ilk 150 test adımı), MAE."""
    o = oku("b68_tahmin_ornek.csv")
    t = kol(o, "adim")[:150]
    fig, (x1, x2) = plt.subplots(1, 2, figsize=(9.6, 3.6),
                                 gridspec_kw={"width_ratios": [1.6, 1]})
    x1.plot(t, kol(o, "gercek")[:150], color=INK, lw=1.4, label="gerçek")
    x1.plot(t, kol(o, "AR")[:150], color=MUTED, lw=1.0, label="AR")
    x1.plot(t, kol(o, "GRU")[:150], color=EDGE[1], lw=1.0, label="GRU")
    x1.plot(t, kol(o, "TCN")[:150], color=ACCENT, lw=1.0, ls="--",
            label="TCN")
    x1.set_xlabel("test adımı (ilk 150)")
    x1.set_ylabel("akım (A)")
    x1.legend(fontsize=8, frameon=False, ncol=2)
    x1.set_title("Tohum 11, 1 adım ileri", fontsize=10)
    tb = oku("b68_tahmin.csv")
    modeller = ["naif", "hareketli ort. (10)", "AR(40)", "RNN", "LSTM",
                "GRU", "TCN"]
    etiket = ["naif", "hareketli", "AR(40)", "RNN", "LSTM", "GRU", "TCN"]
    ort, sd = [], []
    for md in modeller:
        v = [float(r["mae"]) for r in tb if r["model"] == md]
        ort.append(np.mean(v))
        sd.append(np.std(v, ddof=1) if len(v) > 1 else 0.0)
    renk = [MUTED, MUTED, ACCENT_L, EDGE[1], EDGE[0], EDGE[1], ACCENT]
    x2.barh(range(len(modeller)), ort, xerr=sd, color=renk, height=0.6,
            capsize=2)
    x2.set_yticks(range(len(modeller)))
    x2.set_yticklabels(etiket, fontsize=8)
    x2.invert_yaxis()
    x2.set_xlabel("test MAE (A), 3 tohum")
    x2.set_title("Hata", fontsize=10)
    fig.tight_layout()
    return _save(fig, path)


# ---------------------------------------------------------------- 68.9
def cok_adim(path):
    """Şekil 68.9: özyinelemeli ve doğrudan çok adımlı tahmin hatası."""
    c = oku("b68_cok_adim.csv")
    k = kol(c, "k")
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    ax.plot(k, kol(c, "ar_rec"), color=MUTED, lw=1.4, marker="o", ms=3,
            label="AR, özyinelemeli")
    ax.plot(k, kol(c, "ar_dir"), color=ACCENT_L, lw=1.4, marker="s",
            ms=3, label="AR, doğrudan")
    ax.plot(k, kol(c, "gru_rec"), color=ACCENT, lw=1.4, marker="o",
            ms=3, label="GRU, özyinelemeli")
    ax.plot(k, kol(c, "gru_dir"), color=EDGE[1], lw=1.4, marker="s",
            ms=3, label="GRU, doğrudan")
    ax.set_xlabel("ufuk k (adım ileri)")
    ax.set_ylabel("test MAE (A)")
    ax.set_xticks(range(1, 11))
    ax.legend(fontsize=8, frameon=False, ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, path)


# --------------------------------------------------------------- 68.10
def anomali(path):
    """Şekil 68.10: bağlamsal artık, eşik ve enjekte arızalar."""
    a = oku("b68_anomali.csv")
    e = oku("b68_anomali_esik.csv")
    esik = {r["detektor"]: float(r["esik"]) for r in e}
    t = kol(a, "t")
    et = kol(a, "etiket")
    m = (t >= 21000) & (t < 23000)
    art = np.abs(kol(a, "baglam"))
    ma = kol(a, "baglam_ma20")
    fig, (x1, x2) = plt.subplots(2, 1, figsize=(9.6, 4.8), sharex=True)
    x1.plot(t[m], art[m], color=INK, lw=0.6, label="|artık| (bağlamsal)")
    x1.axhline(esik["bağlamsal"], color=ACCENT, ls="--", lw=1,
               label="eşik (doğrulama, 0,9995)")
    ust = float(np.max(art[m]))
    x1.fill_between(t[m], 0, ust, where=(et[m] == 1), color=ACCENT,
                    alpha=0.12, lw=0, label="enjekte arıza")
    x1.set_ylabel("|artık| (A)")
    x1.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=3)
    x1.set_title("Bağlamsal artık: kayma ve sıçrama", fontsize=10)
    x2.plot(t[m], ma[m], color=EDGE[1], lw=1.0,
            label="MA20 (ortalama artık)")
    x2.axhline(esik["bağlamsal MA20"], color=ACCENT, ls="--", lw=1)
    x2.fill_between(t[m], -0.3, 0.6, where=(et[m] == 1), color=ACCENT,
                    alpha=0.12, lw=0)
    x2.set_xlabel("test zaman indeksi")
    x2.set_ylabel("MA20 (A)")
    x2.set_ylim(-0.3, 0.6)
    x2.legend(fontsize=7.5, frameon=False, loc="upper left")
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    yollar = [
        bilesen_acf(os.path.join(GORSEL, "b68_bilesen_acf.png")),
        bolme_sizinti(os.path.join(GORSEL, "b68_bolme_sizinti.png")),
        rnn_acilim(os.path.join(GORSEL, "b68_rnn_acilim.png")),
        gradyan_adim(os.path.join(GORSEL, "b68_gradyan_adim.png")),
        lstm_hucre(os.path.join(GORSEL, "b68_lstm_hucre.png")),
        uzun_bagimlilik(os.path.join(GORSEL, "b68_uzun_bagimlilik.png")),
        tcn_yigin(os.path.join(GORSEL, "b68_tcn_yigin.png")),
        tahmin_karsilastir(os.path.join(GORSEL, "b68_tahmin.png")),
        cok_adim(os.path.join(GORSEL, "b68_cok_adim.png")),
        anomali(os.path.join(GORSEL, "b68_anomali.png")),
    ]
    for y in yollar:
        print(y)
