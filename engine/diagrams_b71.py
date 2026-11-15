# -*- coding: utf-8 -*-
"""Bolum 71 - LLM sistemleri diyagramlari.

Olcum grafikleri engine/veri/b71_*.csv dosyalarindan okunur; bu CSV'leri
deney betikleri uretir (Temp altindaki b71 klasoru). Kavramsal sekiller
veri okumaz.
"""
import matplotlib
matplotlib.use("Agg")
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

from diagrams import (ACCENT, EDGE, FILL, INK, MUTED, RULE,
                      _arrow, _box, _save)

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VERI = os.path.join(KOK, "engine", "veri")
GORSEL = os.path.join(KOK, "gorseller")


def oku(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tuval(w=9.6, h=4.6, xl=14, yl=7):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def mimari(path):
    fig, ax = tuval(10, 4.6, 14, 7)
    _box(ax, 0.2, 4.6, 2.4, 1.2, "Kullanıcı\nistemi", FILL[0], EDGE[0],
         fs=10)
    _box(ax, 3.2, 4.6, 2.8, 1.2, "Girdi işleme\nrol, şablon, bütçe",
         FILL[1], EDGE[1], fs=9)
    _box(ax, 6.6, 4.6, 2.8, 1.2, "Geri getirme (RAG)\nBM25 + yoğun + RRF",
         FILL[2], EDGE[2], fs=9)
    _box(ax, 10.1, 4.6, 3.6, 1.2, "Model\ntokenizer → GPT → örnekleyici",
         FILL[3], EDGE[3], fs=9)
    _box(ax, 0.2, 1.4, 3.2, 1.6,
         "Çıktı doğrulama\nşema, yeniden deneme,\nkaynak kontrolü",
         FILL[4], EDGE[4], fs=9)
    _box(ax, 4.4, 1.4, 3.2, 1.6, "Araçlar\nhesap, arama, API\n(izin listesi)",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 8.6, 1.4, 5.1, 1.6,
         "Servis katmanı\nKV önbelleği, toplu işleme,\nakış, hız sınırı, günlük",
         FILL[1], EDGE[1], fs=9)
    _arrow(ax, 2.6, 5.2, 3.2, 5.2, col=MUTED)
    _arrow(ax, 6.0, 5.2, 6.6, 5.2, col=MUTED)
    _arrow(ax, 9.4, 5.2, 10.1, 5.2, col=MUTED)
    _arrow(ax, 11.9, 4.6, 10.4, 3.0, col=ACCENT, rad=0.1)
    _arrow(ax, 7.3, 4.6, 6.0, 3.0, col=ACCENT, rad=-0.1)
    _arrow(ax, 4.5, 4.6, 2.5, 3.0, col=ACCENT, rad=0.1)
    _arrow(ax, 3.5, 1.9, 4.4, 2.2, col=MUTED)
    _arrow(ax, 6.2, 1.4, 8.6, 1.9, col=MUTED)
    ax.text(0.2, 0.6, "Değerlendirme (eval) her katmanın çıktısını ölçer ve "
            "regresyonda uyarır.", fontsize=9, color=MUTED)
    return _save(fig, path)


def rag_hatti(path):
    fig, ax = tuval(10, 4.0, 14.4, 6)
    kutular = [
        (0.2, "Belgeler\nkitap, notlar"),
        (2.55, "Parçalama\nsabit / başlık"),
        (4.9, "İndeks\nBM25 + vektör"),
        (7.25, "Sorgu\nkök + gömme"),
        (9.6, "Melez sıralama\nRRF"),
        (11.95, "Bağlam\nbütçesi"),
    ]
    for x, m in kutular:
        _box(ax, x, 3.9, 1.8, 1.4, m, FILL[0], EDGE[0], fs=8)
    for i in range(len(kutular) - 1):
        _arrow(ax, kutular[i][0] + 1.8, 4.6, kutular[i + 1][0], 4.6,
               col=MUTED)
    _box(ax, 9.6, 1.2, 4.2, 1.5, "Model: cevap + kaynak (bölüm no)\n"
         "kaynakla tutarlılık kontrolü", FILL[3], EDGE[3], fs=9)
    _arrow(ax, 12.8, 3.9, 12.0, 2.7, col=ACCENT, rad=0.2)
    ax.text(0.2, 1.8, "Çevrimdışı: indeks bir kez kurulur.\n"
            "Çevrimiçi: her sorgu bu hattan geçer.", fontsize=9,
            color=MUTED, va="center")
    return _save(fig, path)


def parca_recall(path):
    satir = oku("b71_parca_recall.csv")
    etiket, bm, ml = [], [], []
    for s in satir:
        if s["yontem"] == "BM25 kök5":
            etiket.append("%s-%s" % (s["strateji"], s["boyut"]))
            bm.append(float(s["R@5"]))
        if s["yontem"] == "melez RRF":
            ml.append(float(s["R@5"]))
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    x = np.arange(len(etiket))
    ax.bar(x - 0.2, bm, 0.4, color=EDGE[0], label="BM25 (kök5)")
    ax.bar(x + 0.2, ml, 0.4, color=EDGE[2], label="Melez RRF")
    ax.set_xticks(x)
    ax.set_xticklabels(etiket, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Recall@5", color=INK)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    return _save(fig, path)


def ivf_takas(path):
    satir = oku("b71_ivf.csv")
    kaba = [s for s in satir if s["nprobe"] == "0"][0]
    ivf = [s for s in satir if s["nprobe"] != "0"]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    x = [float(s["ms_sorgu"]) for s in ivf]
    y = [float(s["recall10"]) for s in ivf]
    ax.plot(x, y, "o-", color=EDGE[0], lw=1.6, label="IVF (nprobe artıyor)")
    for s, xx, yy in zip(ivf, x, y):
        ax.annotate("np=" + s["nprobe"], (xx, yy),
                    textcoords="offset points", xytext=(5, -10),
                    fontsize=8, color=MUTED)
    ax.scatter([float(kaba["ms_sorgu"])], [1.0], color=ACCENT, zorder=5,
               s=40, label="kaba kuvvet (tam tarama)")
    ax.set_xlabel("sorgu başına süre (ms, CPU)", color=INK)
    ax.set_ylabel("recall@10", color=INK)
    ax.set_ylim(0, 1.05)
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    return _save(fig, path)


def ajan_dongusu(path):
    fig, ax = tuval(10, 4.4, 14, 7)
    _box(ax, 0.3, 4.4, 2.8, 1.4, "Düşün\nplan + karar", FILL[0], EDGE[0],
         fs=10)
    _box(ax, 4.6, 4.4, 2.8, 1.4, "Eylem\nizinli araç seç", FILL[1],
         EDGE[1], fs=10)
    _box(ax, 8.9, 4.4, 2.8, 1.4, "Gözlem\nveri, talimat değil", FILL[2],
         EDGE[2], fs=10)
    _arrow(ax, 3.1, 5.1, 4.6, 5.1, col=MUTED)
    _arrow(ax, 7.4, 5.1, 8.9, 5.1, col=MUTED)
    _arrow(ax, 10.3, 4.4, 1.7, 4.4, col=ACCENT, rad=0.35)
    ax.text(5.3, 3.3, "döngü: en fazla N adım, bütçe ve zaman aşımı",
            ha="center", fontsize=9, color=MUTED)
    kat = [("İzin listesi: araç bu görevde tanımlı mı?", FILL[0], EDGE[0]),
           ("Girdi doğrulama: şema, aralık, kaçış", FILL[1], EDGE[1]),
           ("Yan etki: kullanıcı onayı şart", FILL[3], EDGE[3]),
           ("Günlük ve iz: her çağrı kayda geçer", FILL[4], EDGE[4])]
    for i, (m, f, e) in enumerate(kat):
        _box(ax, 0.3 + i * 3.45, 0.5, 3.1, 1.3, m, f, e, fs=8.5)
    ax.text(0.3, 2.1, "Güvenlik katmanları (eylemden önce)", fontsize=9,
            color=INK)
    return _save(fig, path)


def enjeksiyon_tehdit(path):
    fig, ax = tuval(10, 4.8, 14, 8)
    _box(ax, 0.3, 5.6, 3.0, 1.4, "Kullanıcı\n(güvenilir talimat)", FILL[1],
         EDGE[1], fs=9)
    _box(ax, 0.3, 2.6, 3.0, 1.4, "Belge deposu\n(güvenilmez veri)", FILL[3],
         EDGE[3], fs=9)
    _box(ax, 5.2, 4.0, 3.0, 1.8,
         "Model + bağlam\ntalimat ile veri ayrımı\nzayıf nokta",
         FILL[2], EDGE[2], fs=9)
    _box(ax, 9.6, 5.6, 4.0, 1.4, "Araçlar (yan etkili)\nizin listesi yoksa risk",
         FILL[3], EDGE[3], fs=9)
    _box(ax, 9.6, 2.6, 4.0, 1.4, "Çıktı ve günlük\nsızıntı, PII kontrolü",
         FILL[4], EDGE[4], fs=9)
    _arrow(ax, 3.3, 6.3, 5.2, 5.4, col=MUTED)
    _arrow(ax, 3.3, 3.3, 5.2, 4.5, col=ACCENT)
    _arrow(ax, 8.2, 5.0, 9.6, 6.1, col=ACCENT)
    _arrow(ax, 8.2, 4.4, 9.6, 3.4, col=MUTED)
    ax.text(0.3, 1.5, "Kırmızı ok: güvenilmez veriden gelen etki yolu",
            fontsize=9, color=ACCENT)
    ax.text(0.3, 0.9, "Savunmalar: veriyi talimattan ayır, araç izinleri "
            "en az yetki,", fontsize=9, color=INK)
    ax.text(0.3, 0.4, "yan etkiye onay, çıktı denetimi.", fontsize=9,
            color=INK)
    return _save(fig, path)


def prefill_decode(path):
    satir = oku("b71_prefill_decode.csv")
    p = [s["P"] for s in satir]
    pre = [float(s["prefill_ms"]) for s in satir]
    dec = [float(s["decode_onbellek_ms"]) for s in satir]
    fs = [float(s["decode_onbelleksiz_ms"]) for s in satir]
    x = np.arange(len(p))
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.bar(x - 0.27, pre, 0.27, color=EDGE[0],
           label="prefill (P belirteç, tek geçiş)")
    ax.bar(x, dec, 0.27, color=EDGE[1],
           label="decode, KV önbellekli (1 belirteç)")
    ax.bar(x + 0.27, fs, 0.27, color=EDGE[3],
           label="decode, önbelleksiz (tüm dizi)")
    ax.set_xticks(x)
    ax.set_xticklabels(["P=" + v for v in p])
    ax.set_ylabel("süre (ms, CPU)", color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)
    return _save(fig, path)


def kv_bellek(path):
    satir = oku("b71_kv_bellek.csv")
    T = [float(s["T"]) for s in satir]
    mha = [float(s["MHA_GB"]) for s in satir]
    gqa = [float(s["GQA8_GB"]) for s in satir]
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.plot(T, mha, "o-", color=ACCENT, label="KV: çok başlı (32 kafa)")
    ax.plot(T, gqa, "s-", color=EDGE[1],
            label="KV: GQA (8 anahtar-değer kafası)")
    ax.axhline(14.0, color=MUTED, ls="--", lw=1)
    ax.text(T[0], 15.0, "7B sınıfı model, fp16 ağırlıklar ≈ 14 GB",
            fontsize=8, color=MUTED)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("bağlam uzunluğu T (belirteç)", color=INK)
    ax.set_ylabel("bellek (GB), tek dizi", color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.grid(color=RULE, lw=0.6)
    return _save(fig, path)


def kuantizasyon(path):
    satir = oku("b71_kuantizasyon.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    for s in satir:
        b = float(s["bayt"]) / 1024
        d = float(s["delta"])
        renk = ACCENT if "int4" in s["yontem"] else EDGE[0]
        ax.scatter(b, d, s=50, color=renk)
        ax.annotate(s["yontem"], (b, d), textcoords="offset points",
                    xytext=(6, 4), fontsize=8, color=INK)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("ağırlık belleği (KB)", color=INK)
    ax.set_ylabel("test bpc artışı (fp32'ye göre)", color=INK)
    ax.grid(color=RULE, lw=0.6)
    return _save(fig, path)


def batching(path):
    satir = oku("b71_batching.csv")
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    stiller = [("statik", "8", "o--", EDGE[3]),
               ("statik", "32", "s--", EDGE[3]),
               ("surekli", "8", "o-", EDGE[0]),
               ("surekli", "32", "s-", EDGE[0])]
    for mod, B, st, c in stiller:
        v = [s for s in satir if s["mod"] == mod and s["B"] == B]
        x = [float(s["verim"]) for s in v]
        y = [float(s["p95"]) for s in v]
        ax.plot(x, y, st, color=c, lw=1.4, ms=5,
                label="%s, B=%s" % (mod, B))
    ax.set_xlabel("verim (belirteç/sn)", color=INK)
    ax.set_ylabel("p95 gecikme (ms, günlük ölçek)", color=INK)
    ax.set_yscale("log")
    ax.grid(color=RULE, lw=0.6)
    ax.legend(frameon=False, fontsize=8)
    return _save(fig, path)


if __name__ == "__main__":
    os.makedirs(GORSEL, exist_ok=True)
    for f in [mimari, rag_hatti, parca_recall, ivf_takas, ajan_dongusu,
              enjeksiyon_tehdit, prefill_decode, kv_bellek, kuantizasyon,
              batching]:
        print(f.__name__, f(os.path.join(GORSEL, "b71_%s.png" % f.__name__)))
