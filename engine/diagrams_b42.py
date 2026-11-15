# -*- coding: utf-8 -*-
"""Bölüm 42 - 'Docker & Deployment' diyagramları.

Ölçüm verisi okuyan şekil (dağıtım zaman çizelgesi) engine/veri/
b42_dagitim.csv dosyasını okur; o dosya dagitim_strateji.py'nin çıktısıdır.
Diğer şekiller bölümdeki kavramsal yapıdan ve doğrulanmış değerlerden çizilir.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "gorseller")
VERI = os.path.join(BASE, "veri")
MONO = {"family": "DejaVu Sans Mono"}


def _yol(ad):
    return os.path.join(OUT, "b42_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


# 1. Sanal makine ile konteyner katmanları ------------------------------ #
def vm_konteyner():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.4)
    ax.text(3.4, 8.0, "Sanal makine", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    ax.text(10.6, 8.0, "Konteyner", ha="center", fontsize=10.5,
            weight="bold", color=INK)
    _box(ax, 0.4, 6.7, 2.9, 0.8, "Uygulama A", FILL[0], EDGE[0], fs=9)
    _box(ax, 3.5, 6.7, 2.9, 0.8, "Uygulama B", FILL[0], EDGE[0], fs=9)
    _box(ax, 0.4, 5.5, 6.0, 0.8, "Konuk işletim sistemi çekirdeği (VM "
         "başına ayrı)", FILL[2], EDGE[2], fs=9)
    _box(ax, 0.4, 4.3, 6.0, 0.8, "Sanal donanım ve hipervizör", FILL[3],
         EDGE[3], fs=9)
    _box(ax, 0.4, 3.1, 6.0, 0.8, "Fiziksel donanım", FILL[4], EDGE[4],
         fs=9)
    _box(ax, 7.6, 6.7, 2.9, 0.8, "Uygulama A", FILL[0], EDGE[0], fs=9)
    _box(ax, 10.7, 6.7, 2.9, 0.8, "Uygulama B", FILL[0], EDGE[0], fs=9)
    _box(ax, 7.6, 5.5, 6.0, 0.8, "Kütüphaneler (imaj katmanları)", FILL[1],
         EDGE[1], fs=9)
    _box(ax, 7.6, 4.3, 6.0, 0.8, "Konteyner motoru ve ad alanları",
         FILL[3], EDGE[3], fs=9)
    _box(ax, 7.6, 3.1, 6.0, 0.8, "Ana makine çekirdeği (paylaşılır)",
         FILL[2], EDGE[2], fs=9)
    _box(ax, 7.6, 1.9, 6.0, 0.8, "Fiziksel donanım", FILL[4], EDGE[4],
         fs=9)
    ax.text(7.0, 1.0, "VM her biri için tam çekirdek taşır. Konteyner "
            "ana makinenin çekirdeğini paylaşır.", ha="center",
            fontsize=8.6, color=MUTED)
    ax.text(7.0, 0.4, "Bu yüzden konteyner Linux'ta hızlı açılır; Linux "
            "dışında bir çekirdek için VM gerekir.", ha="center",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("vm_konteyner"))


# 2. Ad alanları ve cgroup ----------------------------------------------- #
def ad_alanlari():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=9.0)
    ust = [("PID ad alanı\n(kendi PID 1'i)", 0.2),
           ("Mount ad alanı\n(kendi dosya ağacı)", 2.95),
           ("Ağ ad alanı\n(kendi arayüzleri)", 5.7),
           ("UTS ad alanı\n(kendi hostname)", 8.45),
           ("IPC ad alanı\n(kendi SysV/POSIX)", 11.2)]
    for i, (metin, x) in enumerate(ust):
        _box(ax, x, 6.8, 2.6, 1.1, metin, FILL[i % 4], EDGE[i % 4], fs=8.0)
        _arrow(ax, x + 1.3, 6.8, 6.1, 4.85, col=MUTED, lw=0.9)
    _box(ax, 4.6, 3.8, 4.8, 1.0, "Süreç (ör. nginx, python)", FILL[0],
         EDGE[0], fs=9.4, bold=True)
    _box(ax, 0.3, 1.5, 3.0, 1.1, "Kullanıcı ad alanı\n(uid 0 içeride,\n"
         "dışarıda 1000)", FILL[1], EDGE[1], fs=8.2)
    _arrow(ax, 1.8, 2.6, 4.6, 3.95, col=MUTED, lw=0.9)
    _box(ax, 6.0, 1.5, 7.7, 1.1, "cgroup v2: cpu.max, memory.max, "
         "pids.max\n(kaynak sınırı; ad alanı değil, ayrı bir denetim)",
         FILL[2], EDGE[2], fs=8.4)
    _arrow(ax, 9.9, 2.6, 7.4, 3.8, col=ACCENT, lw=1.1)
    ax.text(7.0, 0.5, "Ad alanı 'ne görür' sorusunu, cgroup 'ne kadar "
            "kullanır' sorusunu yanıtlar.", ha="center", fontsize=8.6,
            color=MUTED)
    return _save(fig, _yol("ad_alanlari"))


# 3. OverlayFS katmanları ------------------------------------------------ #
def overlay():
    fig, ax = _tuval(9.6, 5.2, xl=14, yl=8.2)
    _box(ax, 0.4, 6.1, 8.2, 1.2, "birleşik görünüm (merged): süreç bunu "
         "görür", FILL[0], EDGE[0], fs=9.4, bold=True)
    _box(ax, 0.4, 3.7, 8.2, 1.2, "üst katman (upper): yazılabilir; "
         "değişiklikler ve silme işaretleri", FILL[2], EDGE[2], fs=9)
    _box(ax, 0.4, 1.3, 8.2, 1.2, "alt katman (lower): salt okunur imaj "
         "katmanları", FILL[1], EDGE[1], fs=9)
    _arrow(ax, 4.5, 4.95, 4.5, 6.05, col=MUTED, lw=1.1)
    _arrow(ax, 4.5, 2.5, 4.5, 3.65, col=MUTED, lw=1.1)
    ax.text(4.7, 5.4, "birleştirilir", fontsize=8.6, color=MUTED)
    _box(ax, 9.3, 3.7, 4.4, 3.6, "whiteout\n\nÜst katmanda 0/0 karakter\n"
         "aygıtı: alt katmandaki\ndosya bu yolda silinmiş\ndemektir. Alt\n"
         "katman değişmez.", FILL[3], EDGE[3], fs=8.4)
    ax.text(0.4, 0.5, "Yazma, alt katmana değil üst katmana gider "
            "(kopyala-yazarken-kopyala).", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("overlay"))


# 4. İmaj katmanları ve içerik adresi ----------------------------------- #
def imaj_katman():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=8.6)
    ax.text(0.4, 8.1, "İmaj = manifest + katman arşivleri", fontsize=10,
            weight="bold", color=INK)
    _box(ax, 0.4, 6.5, 6.4, 1.0, "manifest: katman özetleri + "
         "yapılandırma", FILL[0], EDGE[0], fs=9)
    kat = [("katman 4: RUN make (ikili)", FILL[3], EDGE[3]),
           ("katman 3: COPY . . (kaynak)", FILL[2], EDGE[2]),
           ("katman 2: RUN apt-get install", FILL[1], EDGE[1]),
           ("katman 1: FROM gcc:13 (temel)", FILL[4], EDGE[4])]
    for i, (metin, f, e) in enumerate(kat):
        y = 4.9 - i * 1.15
        _box(ax, 0.4, y, 6.4, 0.9, metin, f, e, fs=9)
        ax.text(7.0, y + 0.45, "özet = sha256(arşiv baytları)",
                fontsize=8.4, color=MUTED, va="center")
    ax.text(0.4, 0.4, "Aynı arşiv baytları aynı özeti verir; özet "
            "değişirse katman farklıdır.", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("imaj_katman"))


# 5. Önbellek geçersizleşmesi (model çıktısı) ---------------------------- #
def onbellek():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.6)
    a = [("FROM gcc:13", "CACHED"), ("WORKDIR /src", "CACHED"),
         ("COPY . .", "REBUILT"), ("RUN apt-get install", "REBUILT"),
         ("RUN make", "REBUILT")]
    b = [("FROM gcc:13", "CACHED"), ("WORKDIR /src", "CACHED"),
         ("COPY deps.txt .", "CACHED"), ("RUN apt-get install", "CACHED"),
         ("COPY . .", "REBUILT"), ("RUN make", "REBUILT")]
    for col, (x, baslik, satir) in enumerate(
            [(0.4, "A: kaynak önce kopyalanır", a),
             (7.2, "B: bağımlılık önce kopyalanır", b)]):
        ax.text(x + 3.0, 8.0, baslik, ha="center", fontsize=9.6,
                weight="bold", color=INK)
        for r, (tal, dur) in enumerate(satir):
            y = 7.0 - r * 1.05
            f, e = (FILL[1], EDGE[1]) if dur == "CACHED" else (FILL[3],
                                                             EDGE[3])
            _box(ax, x, y, 4.0, 0.8, tal, f, e, fs=8.8)
            ax.text(x + 4.3, y + 0.4, dur, va="center", fontsize=8.6,
                    weight="bold", color=e)
    ax.text(7.0, 0.7, "Kaynak değişti (crc32_arac.c). Yeşil: önbellekten, "
            "bordo: yeniden derlendi.", ha="center", fontsize=8.6,
            color=MUTED)
    ax.text(7.0, 0.2, "Veri: katman_onbellek.py çıktısı (model).",
            ha="center", fontsize=8.2, color=MUTED)
    return _save(fig, _yol("onbellek"))


# 6. Çok aşamalı derleme ------------------------------------------------- #
def cok_asama():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.0)
    _box(ax, 0.3, 2.0, 5.8, 3.5, "1. aşama: derle\n\ngcc:13 imajı\n"
         "gcc -static ...\nçıktı: /cikti/crc32_arac\n\n(derleyici, başlık,\n"
         "kabuk burada kalır)", FILL[0], EDGE[0], fs=9)
    _box(ax, 8.0, 2.0, 5.7, 3.5, "2. aşama: scratch\n\nyalnız tek ikili\n"
         "/crc32_arac (785 KB)\nUSER 65532:65532\n\n(kabuk yok, libc yok)",
         FILL[1], EDGE[1], fs=9)
    _arrow(ax, 6.1, 3.75, 7.9, 3.75, col=ACCENT, lw=1.6)
    ax.text(7.0, 4.15, "COPY --from=derle", ha="center", fontsize=8.6,
            color=ACCENT)
    ax.text(7.0, 1.3, "Son imaj yalnızca çalışma zamanı bağımlılıklarını "
            "taşır. Statik bağlama bunu mümkün kılar.", ha="center",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("cok_asama"))


# 7. Compose servis grafiği --------------------------------------------- #
def compose_graf():
    fig, ax = _tuval(9.6, 5.8, xl=14, yl=9.0)
    ax.add_patch(FancyBboxPatch((0.3, 0.6), 4.4, 7.8, boxstyle="round,"
                                "pad=0.02,rounding_size=0.2", fill=False,
                                edgecolor=MUTED, linestyle="--", lw=1.0))
    ax.text(2.5, 8.1, "dis ağı (dış dünya)", ha="center", fontsize=8.6,
            color=MUTED)
    ax.add_patch(FancyBboxPatch((5.2, 0.6), 8.5, 7.8, boxstyle="round,"
                                "pad=0.02,rounding_size=0.2", fill=False,
                                edgecolor=ACCENT_L, linestyle="--", lw=1.0))
    ax.text(9.45, 8.1, "ic ağı (internal: true, dışa kapalı)",
            ha="center", fontsize=8.6, color=ACCENT_L)
    _box(ax, 0.8, 5.2, 3.6, 1.2, "proxy (nginx)\nyayın: 8080 -> 80",
         FILL[0], EDGE[0], fs=9)
    _box(ax, 6.0, 4.9, 3.4, 1.2, "api (Python)\nexpose: 8080", FILL[1],
         EDGE[1], fs=9)
    _box(ax, 10.2, 4.9, 3.2, 1.2, "db (Postgres 16)\nhealthcheck", FILL[2],
         EDGE[2], fs=9)
    _box(ax, 6.0, 1.6, 3.4, 1.0, "api kökü: salt okunur\ntmpfs: /tmp",
         FILL[4], EDGE[4], fs=8.4)
    _box(ax, 10.2, 1.6, 3.2, 1.0, "veri (adlandırılmış\nhacim)", FILL[3],
         EDGE[3], fs=8.4)
    _arrow(ax, 4.4, 5.8, 6.0, 5.5, col=ACCENT, lw=1.4)
    _arrow(ax, 9.4, 5.5, 10.2, 5.5, col=ACCENT_L, lw=1.4)
    ax.text(9.8, 6.3, "depends_on\nservice_healthy", fontsize=7.6,
            color=ACCENT_L, ha="center")
    _arrow(ax, 11.8, 4.9, 11.8, 2.6, col=MUTED, lw=0.9)
    ax.text(12.0, 3.6, "hacim", fontsize=8.2, color=MUTED)
    ax.text(7.0, 0.1, "Sırlar ./secrets/db_parola.txt üzerinden, ortam "
            "değişkeni olmadan verilir.", ha="center", fontsize=8.2,
            color=MUTED)
    return _save(fig, _yol("compose_graf"))


# 8. CI hattı ------------------------------------------------------------ #
def ci_hatti():
    fig, ax = _tuval(9.6, 4.4, xl=14, yl=4.9)
    adimlar = [("commit /\nPR", "git push"), ("lint", "ci.sh lint"),
               ("testler", "ci.sh testler"), ("kapsama\n%80", "ci.sh\nkapsama"),
               ("statik\nderle", "ci.sh derle"), ("imaj\n(zorunlu)",
                                                    "ci.sh imaj"),
               ("artefakt +\netiket", "upload")]
    for i, (ad, komut) in enumerate(adimlar):
        x = 0.25 + i * 2.0
        _box(ax, x, 3.0, 1.7, 1.3, ad, FILL[i % 4], EDGE[i % 4], fs=8.8,
             bold=True)
        ax.text(x + 0.85, 2.5, komut, ha="center", fontsize=7.4,
                family="DejaVu Sans Mono", color=MUTED)
        if i < len(adimlar) - 1:
            _arrow(ax, x + 1.7, 3.65, x + 2.0, 3.65, col=MUTED, lw=1.0)
    ax.text(7.0, 1.2, "Her adım bir kapıdır: biri başarısız olursa sonraki "
            "adımlar çalışmaz.", ha="center", fontsize=8.6, color=MUTED)
    ax.text(7.0, 0.5, "Aynı betik (ci.sh) hem yerelde hem CI iş akışında "
            "çağrılır.", ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("ci_hatti"))


# 9. Dağıtım zaman çizelgesi (ölçüm/model verisi: CSV) ------------------- #
def dagitim_zaman():
    satirlar = []
    with open(os.path.join(VERI, "b42_dagitim.csv"), encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    stratejiler = ["yeniden_olustur", "mavi_yesil", "yuvarlanan"]
    etiket = {"yeniden_olustur": "Yeniden oluştur",
              "mavi_yesil": "Mavi-yeşil", "yuvarlanan": "Yuvarlanan"}
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=8.2)
    N = 4
    for r, st in enumerate(stratejiler):
        y = 6.1 - r * 2.0
        ax.text(0.3, y + 0.35, etiket[st], fontsize=9.4, weight="bold",
                color=INK, va="center")
        seri = [s for s in satirlar if s["strateji"] == st]
        for s in seri:
            t = int(s["tik"])
            x = 3.0 + t * 1.75
            v1, v2 = int(s["v1"]), int(s["v2"])
            w = 1.5
            ax.add_patch(plt.Rectangle((x, y), w, 0.7, facecolor="white",
                                       edgecolor=RULE, lw=0.8))
            if int(s["kesinti"]) == 1:
                ax.add_patch(plt.Rectangle((x, y), w, 0.7, facecolor=FILL[3],
                                           edgecolor=ACCENT, lw=1.0))
                ax.text(x + w / 2, y + 0.35, "kesinti", ha="center",
                        va="center", fontsize=7.6, color=ACCENT)
            else:
                ax.add_patch(plt.Rectangle((x, y), w * v1 / N, 0.7,
                                           facecolor=EDGE[0], lw=0))
                ax.add_patch(plt.Rectangle((x + w * v1 / N, y), w * v2 / N,
                                           0.7, facecolor=EDGE[1], lw=0))
            ax.text(x + w / 2, y - 0.25, "t%d:%d" % (t, int(s["toplam"])),
                    ha="center", fontsize=7.2, color=MUTED)
    for t in range(6):
        ax.text(3.0 + t * 1.75 + 0.75, 7.6, "tik %d" % t, ha="center",
                fontsize=8.2, color=MUTED)
    ax.add_patch(plt.Rectangle((0.3, 0.6), 0.35, 0.35, facecolor=EDGE[0]))
    ax.text(0.8, 0.78, "v1 hizmette", fontsize=8.2, color=MUTED, va="center")
    ax.add_patch(plt.Rectangle((3.3, 0.6), 0.35, 0.35, facecolor=EDGE[1]))
    ax.text(3.8, 0.78, "v2 hizmette", fontsize=8.2, color=MUTED, va="center")
    ax.text(6.6, 0.78, "etiket tN:M = tik N'de toplam pod M", fontsize=8.2,
            color=MUTED, va="center")
    return _save(fig, _yol("dagitim_zaman"))


# 10. Uzlaştırma döngüsü ------------------------------------------------- #
def uzlastirma_dongu():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.6)
    _box(ax, 4.9, 6.9, 4.2, 1.0, "istenen durum\n(3 kopya)", FILL[0],
         EDGE[0], fs=9.2, bold=True)
    _box(ax, 9.4, 3.6, 4.2, 1.0, "gözlenen durum\n(pod listesi)", FILL[1],
         EDGE[1], fs=9.2, bold=True)
    _box(ax, 4.9, 0.6, 4.2, 1.0, "fark: istenen - gözlenen", FILL[2],
         EDGE[2], fs=9.2, bold=True)
    _box(ax, 0.4, 3.6, 4.2, 1.0, "eylem: oluştur / sil", FILL[3],
         EDGE[3], fs=9.2, bold=True)
    _arrow(ax, 9.1, 7.2, 11.5, 4.7, col=ACCENT, lw=1.3, rad=-0.2)
    _arrow(ax, 11.5, 3.5, 9.1, 1.4, col=ACCENT, lw=1.3, rad=-0.2)
    _arrow(ax, 4.9, 1.1, 2.5, 3.5, col=ACCENT, lw=1.3, rad=-0.2)
    _arrow(ax, 2.5, 4.7, 4.9, 7.2, col=ACCENT, lw=1.3, rad=-0.2)
    ax.text(7.0, 3.9, "her tikte\ntekrar", ha="center", fontsize=8.8,
            color=MUTED)
    ax.text(7.0, 0.1, "Döngü, gözlenen durumu istenene yaklaştırır; kendisi "
            "bir kez çalışıp bitmez.", ha="center", fontsize=8.4,
            color=MUTED)
    return _save(fig, _yol("uzlastirma"))


if __name__ == "__main__":
    for f in (vm_konteyner, ad_alanlari, overlay, imaj_katman, onbellek,
              cok_asama, compose_graf, ci_hatti, dagitim_zaman,
              uzlastirma_dongu):
        print(f())
