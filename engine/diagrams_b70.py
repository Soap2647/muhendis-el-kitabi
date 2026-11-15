# -*- coding: utf-8 -*-
"""Bölüm 70 - NLP & Dil Modelleri diyagramları.

Ölçüm grafikleri engine/veri/b70_*.csv dosyalarından okunur (bunlar
Temp\\b70 betiklerinin çıktısıdır: g02, g04, g07, g10, g11, g14). Kavramsal
şekiller (tokenizasyon düzeyleri, LoRA şeması) veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import math
import os
import numpy as np
import matplotlib.pyplot as plt
from diagrams import _box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED, RULE, FILL, EDGE

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(KLASOR, "veri")
GORSEL = os.path.join(KLASOR, "..", "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def yol(ad):
    return os.path.join(GORSEL, ad)


def tokenizasyon_duzeyleri(path):
    """Şekil 70.1: aynı cümlenin üç farklı parçalanışı."""
    satir = {r["duzey"]: r for r in oku("b70_ornek_tokenler.csv")}
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    yerler = [("karakter", 5.4), ("sozcuk", 3.0), ("alt-sozcuk(BPE)", 0.6)]
    etiket = {"karakter": "Karakter", "sozcuk": "Sözcük",
              "alt-sozcuk(BPE)": "Alt-sözcük (BPE)"}
    for duzey, y in yerler:
        r = satir[duzey]
        parcalar = r["parcalar"].split("|")
        ax.text(0.1, y + 1.05, "%s: %s parça" % (etiket[duzey], r["parca_sayisi"]),
                fontsize=10.5, color=INK, weight="bold")
        x = 0.1
        genislik = 13.6 / max(len(parcalar), 1)
        for i, p in enumerate(parcalar):
            w = min(genislik * 0.9, 0.5 + 0.45 * len(p.replace(" ", "_")))
            if duzey == "karakter":
                w = 0.52
            if x + w > 13.9:
                break
            _box(ax, x, y, w, 0.9, p.replace(" ", "␣") if duzey != "sozcuk" else p,
                 fill=FILL[0] if i % 2 == 0 else FILL[1], edge=EDGE[0],
                 fs=8.5 if duzey == "karakter" else 9.5)
            x += w + 0.05
    fig.tight_layout()
    return _save(fig, path)


def bpe_takas(path):
    """Şekil 70.2: birleştirme sayısı -> sözlük boyutu ve kelime başına token."""
    r = oku("b70_bpe_takas.csv")
    m = [int(x["birlestirme"]) for x in r]
    sz = [int(x["sozluk"]) for x in r]
    kt = [float(x["kar_token"]) for x in r]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.plot(sz, kt, marker="o", color=ACCENT, lw=1.8)
    for x, y, mm in zip(sz, kt, m):
        ax.annotate("%d" % mm, (x, y), textcoords="offset points", xytext=(4, 6),
                    fontsize=8.5, color=MUTED)
    ax.set_xscale("log")
    ax.set_xlabel("Sözlük boyutu (log ölçek)", color=INK)
    ax.set_ylabel("Ortalama karakter / token", color=INK)
    ax.grid(color=RULE, lw=0.6)
    ax.set_title("Birleştirme sayısı (nokta etiketi) arttıkça sözlük büyür,\n"
                 "token başına karakter artar; sınama metni (test bölümleri)",
                 fontsize=10, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def sozluk_buyume(path):
    """Şekil 70.3: sözcük sözlüğü büyümesi ve OOV oranı."""
    r = oku("b70_sozluk_buyume.csv")
    oran = [100 * float(x["oran"]) for x in r]
    soz = [int(x["sozluk"]) for x in r]
    oov = [float(x["oov_yuzde"]) for x in r]
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.bar(oran, soz, width=7, color=FILL[0], edgecolor=EDGE[0])
    ax.set_xlabel("Eğitim derleminin oranı (%)", color=INK)
    ax.set_ylabel("Tekil sözcük sayısı", color=INK)
    ax2 = ax.twinx()
    ax2.plot(oran, oov, marker="o", color=ACCENT, lw=1.8)
    ax2.set_ylabel("OOV oranı (%)", color=ACCENT)
    ax2.set_ylim(0, 30)
    for x, y in zip(oran, oov):
        ax2.annotate("%.1f" % y, (x, y), textcoords="offset points", xytext=(0, 7),
                     ha="center", fontsize=8.5, color=ACCENT)
    ax.set_title("Sözcük sözlüğü büyür, yine de test sözcüklerinin bir kısmı dışarıda kalır",
                 fontsize=10, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def dil_takas(path):
    """Şekil 70.4: tokenizer ve metin dilinin kelime başına token maliyeti."""
    r = oku("b70_dil_takas.csv")
    adlar = [x["tokenizer_metin"] for x in r]
    tks = [float(x["token_sozcuk"]) for x in r]
    unk = [float(x["unk_yuzde"]) for x in r]
    renk = [EDGE[1], EDGE[1], EDGE[3], EDGE[3]]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.bar(range(len(adlar)), tks, color=[FILL[1], FILL[1], FILL[3], FILL[3]],
           edgecolor=renk)
    ax.set_xticks(range(len(adlar)))
    ax.set_xticklabels(adlar, fontsize=9)
    for i, (t, u) in enumerate(zip(tks, unk)):
        ax.text(i, t + 0.08, "%.2f token/sözcük\nunk %%%.2f" % (t, u), ha="center",
                fontsize=8.5, color=INK)
    ax.set_ylim(0, 5.6)
    ax.set_ylabel("Sözcük başına token", color=INK)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_title("Aynı Türkçe metin: Türkçe tokenizer ile İngilizce tokenizer karşılaştırması",
                 fontsize=10, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def gomme_pca(path):
    """Şekil 70.5: skip-gram gömmelerinin ilk iki PCA bileşeni (en sık 120 sözcük)."""
    r = oku("b70_gomme_pca.csv")
    x = np.array([float(a["x"]) for a in r])
    y = np.array([float(a["y"]) for a in r])
    w = [a["sozcuk"] for a in r]
    fig, ax = plt.subplots(figsize=(9.6, 6.2))
    ax.scatter(x, y, s=18, color=ACCENT_L, alpha=0.7)
    secilen = [i for i, s in enumerate(w) if s in {
        "eğitim", "test", "doğruluk", "kaybı", "model", "gradyan", "kelime", "tahmin",
        "sinir", "ağırlık", "sayı", "veri", "kod", "öğrenme", "bölüm", "dikkat"}]
    for i in secilen:
        ax.annotate(w[i], (x[i], y[i]), textcoords="offset points", xytext=(4, 3),
                    fontsize=9, color=INK)
    ax.set_xlabel("PCA bileşen 1", color=INK)
    ax.set_ylabel("PCA bileşen 2", color=INK)
    ax.grid(color=RULE, lw=0.6)
    ax.set_title("Skip-gram gömmeleri (100 boyut), en sık 120 sözcüğün 2B izdüşümü",
                 fontsize=10, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def gpt_egri(path):
    """Şekil 70.6: eğitim kaybı ve doğrulama perplexity'si; n-gram tabanları."""
    r = oku("b70_gpt_egri.csv")
    ng = {x["model"]: float(x["test_ppl"]) for x in oku("b70_ngram.csv")}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    for tohum, renk in zip(["0", "1", "2"], [ACCENT, ACCENT_L, EDGE[1]]):
        s = [x for x in r if x["tohum"] == tohum]
        a = [int(x["adim"]) for x in s]
        a1.plot(a, [float(x["egitim_kayip"]) for x in s], color=renk, lw=1.3,
                label="tohum %s" % tohum)
        a2.plot(a, [float(x["dogrulama_ppl"]) for x in s], color=renk, lw=1.3,
                label="tohum %s" % tohum)
    for ad, deger, stil in [("1-gram", ng["1-gram"], ":"), ("2-gram", ng["2-gram"], "--"),
                            ("3-gram", ng["3-gram"], "-.")]:
        a2.axhline(deger, color=MUTED, lw=1.0, ls=stil)
        a2.text(1500, deger, "%s: %.0f " % (ad, deger), va="bottom", ha="right", fontsize=8.5, color=MUTED)
    a2.set_yscale("log")
    a1.set_title("Eğitim kaybı (çapraz entropi, nat)", fontsize=10, color=INK)
    a2.set_title("Doğrulama perplexity'si (log)", fontsize=10, color=INK)
    for a in (a1, a2):
        a.set_xlabel("Adım", color=INK)
        a.grid(color=RULE, lw=0.6)
    a1.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    return _save(fig, path)


def olcek(path):
    """Şekil 70.7: ölçekleme (log-log): parametre ve veriye göre test perplexity."""
    r = oku("b70_olcek.csv")
    n = np.array([float(x["parametre"]) for x in r])
    d = np.array([float(x["egitim_token"]) for x in r])
    p = np.array([float(x["test_ppl"]) for x in r])
    adlar = [x["ad"] for x in r]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    m_model = np.array([i for i, a in enumerate(adlar) if not a.startswith("veri")])
    m_veri = np.array([i for i, a in enumerate(adlar) if a.startswith("veri") or "ana" in a])
    a1.scatter(n[m_model], p[m_model], color=ACCENT, s=26)
    for i in m_model:
        a1.annotate(adlar[i], (n[i], p[i]), textcoords="offset points", xytext=(4, 4),
                    fontsize=8, color=INK)
    if len(m_model) >= 2:
        katsayi = np.polyfit(np.log(n[m_model]), np.log(p[m_model]), 1)
        xs = np.linspace(n[m_model].min(), n[m_model].max(), 50)
        a1.plot(xs, np.exp(np.polyval(katsayi, np.log(xs))), color=MUTED, lw=1.0, ls="--")
        a1.set_title("Model boyutu (eğim %.2f)" % katsayi[0], fontsize=10, color=INK)
    m3 = [i for i in range(len(r)) if "veri" in adlar[i] or "ana" in adlar[i]]
    a2.scatter(d[m3], p[m3], color=ACCENT_L, s=26)
    for i in range(len(r)):
        if "veri" in adlar[i] or adlar[i].startswith("veri"):
            a2.annotate(adlar[i], (d[i], p[i]), textcoords="offset points", xytext=(4, 4),
                        fontsize=8, color=INK)
    m2 = np.array([i for i in range(len(r)) if "veri" in adlar[i] or "ana" in adlar[i]])
    katsayi2 = np.polyfit(np.log(d[m2]), np.log(p[m2]), 1)
    xs = np.linspace(d[m2].min(), d[m2].max(), 50)
    a2.plot(xs, np.exp(np.polyval(katsayi2, np.log(xs))), color=MUTED, lw=1.0, ls="--")
    a2.set_title("Eğitim token sayısı (eğim %.2f)" % katsayi2[0], fontsize=10, color=INK)
    for a in (a1, a2):
        a.set_xscale("log")
        a.set_yscale("log")
        a.set_ylabel("Test perplexity", color=INK)
        a.grid(color=RULE, lw=0.6)
    a1.set_xlabel("Parametre sayısı", color=INK)
    a2.set_xlabel("Eğitim token sayısı", color=INK)
    fig.tight_layout()
    return _save(fig, path)


def lora_semasi(path):
    """Şekil 70.8: LoRA'nın W + (alpha/r) B A yapısı (kavramsal)."""
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    _box(ax, 0.3, 3.2, 1.6, 1.4, "girdi\nx (d)", fill=FILL[0], edge=EDGE[0], fs=10)
    _box(ax, 4.4, 5.2, 3.0, 1.4, "W (d×d)\ndonuk, eğitilmez", fill=FILL[4],
         edge=EDGE[4], fs=10)
    _box(ax, 4.4, 1.2, 2.2, 1.4, "A (r×d)\nGauss", fill=FILL[1], edge=EDGE[1], fs=10)
    _box(ax, 7.4, 1.2, 2.2, 1.4, "B (d×r)\nsıfır", fill=FILL[1], edge=EDGE[1], fs=10)
    _box(ax, 10.4, 1.2, 2.3, 1.4, "×(α/r)", fill=FILL[2], edge=EDGE[2], fs=10)
    _box(ax, 10.9, 5.2, 2.6, 1.4, "toplam\ny", fill=FILL[0], edge=EDGE[0], fs=10, bold=True)
    _arrow(ax, 1.9, 3.9, 4.4, 5.9, col=EDGE[4], rad=0.0)
    _arrow(ax, 1.9, 3.5, 4.4, 1.9, col=EDGE[1], rad=0.0)
    _arrow(ax, 6.6, 1.9, 7.4, 1.9, col=EDGE[1])
    _arrow(ax, 9.6, 1.9, 10.4, 1.9, col=EDGE[2])
    _arrow(ax, 7.4, 5.9, 10.9, 5.9, col=EDGE[4])
    _arrow(ax, 12.7, 2.6, 12.2, 5.2, col=EDGE[2], rad=0.0)
    ax.text(0.3, 0.6, "Eğitilen parametre: 2·r·d (A ve B).  Tam matris: d² (W).",
            fontsize=9.5, color=INK)
    ax.text(0.3, 7.2, "y = W x + (α/r) · B (A x)", fontsize=12, color=INK, weight="bold")
    return _save(fig, path)


def lora_rank(path):
    """Şekil 70.9: LoRA rank'ına göre test doğruluğu ve eğitilebilir parametre."""
    r = [x for x in oku("b70_ince_ayar.csv") if x["yontem"] == "lora"]
    rk = [int(x["r"]) for x in r]
    acc = [float(x["test_acc_ort"]) for x in r]
    sd = [float(x["test_acc_sd"]) for x in r]
    par = [int(x["egitilebilir"]) for x in r]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.errorbar(rk, acc, yerr=sd, marker="o", color=ACCENT, lw=1.8, capsize=3,
                label="test doğruluğu (3 tohum)")
    ax.set_xscale("log", base=2)
    ax.set_xticks(rk)
    ax.set_xticklabels([str(k) for k in rk])
    ax.set_xlabel("LoRA rank (r), log₂ ölçek", color=INK)
    ax.set_ylabel("Test doğruluğu", color=INK)
    ax.grid(color=RULE, lw=0.6)
    ax2 = ax.twinx()
    ax2.plot(rk, par, marker="s", color=ACCENT_L, lw=1.2, ls="--",
             label="eğitilebilir parametre")
    ax2.set_yscale("log")
    ax2.set_ylabel("Eğitilebilir parametre (log)", color=ACCENT_L)
    ax.set_title("Rank arttıkça parametre artar; doğruluk belirgin biçimde değişmez",
                 fontsize=10, color=INK)
    fig.tight_layout()
    return _save(fig, path)


def unutma(path):
    """Şekil 70.10: ön-eğitim (sonraki token) perplexity'si, yöntemlere göre."""
    r = oku("b70_ince_ayar.csv")
    taban = float([x for x in r if x["lm_once"]][0]["lm_once"])
    etiket, deger, renk = [], [], []
    for x in r:
        if x["yontem"] == "sifirdan":
            continue
        if x["yontem"] == "lora":
            etiket.append("LoRA %s\nadaptör açık" % x["r"])
            deger.append(float(x["lm_sonra_ort"]))
            renk.append(FILL[3])
            etiket.append("LoRA %s\nadaptör kapalı" % x["r"])
            deger.append(float(x["lm_adaptor_kapali"]))
            renk.append(FILL[1])
        elif x["yontem"] == "tam":
            etiket.append("Tam ince\nayar")
            deger.append(float(x["lm_sonra_ort"]))
            renk.append(FILL[3])
        elif x["yontem"] == "dogrusal":
            etiket.append("Linear\nprobe")
            deger.append(float(x["lm_sonra_ort"]))
            renk.append(FILL[1])
    fig, ax = plt.subplots(figsize=(10.4, 4.8))
    ax.bar(range(len(deger)), deger, color=renk, edgecolor=EDGE[0])
    ax.axhline(taban, color=ACCENT, ls="--", lw=1.0)
    ax.text(len(deger) - 0.5, taban * 1.06, "ince ayardan önce: %.1f" % taban,
            ha="right", fontsize=8.5, color=ACCENT)
    ax.set_yscale("log")
    ax.set_xticks(range(len(etiket)))
    ax.set_xticklabels(etiket, fontsize=8)
    ax.set_xlabel("Yöntem (LoRA: rank r; adaptör açık/kapalı)", color=INK)
    ax.set_ylabel("Ön-eğitim doğrulama ppl (log)", color=INK)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_title("Felaket unutma: sınıflandırma ince ayarı sonrası dil modelleme",
                 fontsize=10, color=INK)
    fig.tight_layout()
    return _save(fig, path)


if __name__ == "__main__":
    print(tokenizasyon_duzeyleri(yol("b70_tokenizasyon_duzeyleri.png")))
    print(bpe_takas(yol("b70_bpe_takas.png")))
    print(sozluk_buyume(yol("b70_sozluk_buyume.png")))
    print(dil_takas(yol("b70_dil_takas.png")))
    print(gomme_pca(yol("b70_gomme_pca.png")))
    print(gpt_egri(yol("b70_gpt_egri.png")))
    print(olcek(yol("b70_olcek.png")))
    print(lora_semasi(yol("b70_lora_semasi.png")))
    print(lora_rank(yol("b70_lora_rank.png")))
    print(unutma(yol("b70_unutma.png")))
