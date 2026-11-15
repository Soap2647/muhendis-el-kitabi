# -*- coding: utf-8 -*-
"""Bolum 28 - 'File System & I/O' diyagramlari.

Olcum sekilleri engine/veri/ altindaki CSV dosyalarini okur:
  b28_tampon.csv      read() tampon boyutu olcumu
  b28_fsync_ham.csv   fsync / fdatasync / yalniz yazma gecikmeleri
  b28_epoll.csv       poll ve epoll icin hazir-fd olcekleme olcumu
Diger sekiller bolumdeki ornek degerlerden cizilir.
"""
import csv
import os
import sys
from collections import defaultdict

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


def _yol(ad):
    return os.path.join(OUT, "b28_%s.png" % ad)


def _tuval(w, h, xl=14, yl=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl)
    ax.set_ylim(0, yl)
    ax.axis("off")
    return fig, ax


def _oku_csv(ad):
    with open(os.path.join(VERI, ad), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. G/C yigini: istek yukaridan asagiya iner -------------------------- #
def katmanlar():
    fig, ax = _tuval(9.6, 6.6, xl=14, yl=9.6)
    katman = [
        ("Kullanıcı programı", "printf, fgets, fwrite", FILL[0], EDGE[0],
         "Bellek içi işlev çağrısı"),
        ("stdio tamponu (FILE)", "kullanıcı alanında tampon", FILL[1],
         EDGE[1], "Yazma burada birikir, diske inmez"),
        ("Sistem çağrısı", "read, write, fsync: çekirdek sınırı", FILL[2],
         EDGE[2], "Kullanıcıdan çekirdeğe geçiş"),
        ("VFS", "inode, dentry, file nesneleri", FILL[0], EDGE[0],
         "Ad çözme ve dosya sistemine yönlendirme"),
        ("Sayfa önbelleği", "dosya verisinin RAM kopyası", FILL[1],
         EDGE[1], "Okumalar çoğunlukla buradan karşılanır"),
        ("Blok katmanı", "I/O zamanlayıcı ve kuyruklar", FILL[2], EDGE[2],
         "Sıralama, birleştirme, zamanlama"),
        ("Aygıt sürücüsü", "disk, SSD ya da NVMe denetleyicisi", FILL[3],
         EDGE[3], "Gerçek aygıt gecikmesi"),
    ]
    for i, (baslik, alt, fill, edge, not_) in enumerate(katman):
        y = 8.2 - i * 1.2
        _box(ax, 0.5, y, 6.4, 0.85, baslik + "\n" + alt, fill, edge,
             fs=9.2)
        ax.text(7.3, y + 0.42, not_, va="center", fontsize=9, color=INK)
        if i < len(katman) - 1:
            _arrow(ax, 3.7, y, 3.7, y - 0.35, col=MUTED, lw=1.0)
    ax.text(7.0, 9.35, "İstek yukarıdan aşağıya iner; her katman bir "
            "öncekinin ardından çalışır", ha="center", fontsize=9.2,
            color=MUTED)
    return _save(fig, _yol("katmanlar"))


# 2. fd tablosu, acik dosya tablosu, inode -------------------------- #
def fd_tablolar():
    fig, ax = _tuval(9.6, 5.6, xl=14, yl=8.6)
    ax.text(2.1, 8.2, "Süreç tablosu (fd)", ha="center", fontsize=9.6,
            weight="bold", color=INK)
    ax.text(7.0, 8.2, "Açık dosya tablosu", ha="center", fontsize=9.6,
            weight="bold", color=INK)
    ax.text(11.9, 8.2, "inode tablosu", ha="center", fontsize=9.6,
            weight="bold", color=INK)

    _box(ax, 0.3, 6.1, 3.6, 0.8, "Ana süreç: fd 3", FILL[0], EDGE[0],
         fs=9.2)
    _box(ax, 0.3, 4.6, 3.6, 0.8, "Çocuk süreç (fork): fd 3", FILL[1],
         EDGE[1], fs=9.2)
    _box(ax, 0.3, 2.1, 3.6, 0.8, "Ana süreç: fd 4", FILL[0], EDGE[0],
         fs=9.2)

    _box(ax, 5.0, 4.5, 4.0, 1.5,
         "Açık dosya X\nofset = 10, O_RDONLY\nsayaç = 2", FILL[2],
         EDGE[2], fs=9.0)
    _box(ax, 5.0, 1.9, 4.0, 1.2,
         "Açık dosya Y\nofset = 5, O_RDONLY\nsayaç = 1", FILL[2],
         EDGE[2], fs=9.0)

    _box(ax, 10.2, 3.2, 3.6, 1.6,
         "inode 44341\nboyut = 26 bayt\nbağlantı = 1", FILL[3], EDGE[3],
         fs=9.0)
    _box(ax, 10.2, 0.9, 3.6, 0.9, "inode 44285", FILL[3], EDGE[3],
         fs=9.0)

    _arrow(ax, 3.9, 6.5, 5.0, 5.6, col=MUTED, lw=1.1)
    _arrow(ax, 3.9, 5.0, 5.0, 5.2, col=MUTED, lw=1.1)
    _arrow(ax, 3.9, 2.5, 5.0, 2.5, col=MUTED, lw=1.1)
    _arrow(ax, 9.0, 5.25, 10.2, 4.3, col=MUTED, lw=1.1)
    _arrow(ax, 9.0, 2.5, 10.2, 1.4, col=MUTED, lw=1.1)

    ax.text(7.0, 0.35, "fork sonrası iki süreç aynı açık dosyayı paylaşır "
            "(ofset ortak); ayrı open() ayrı ofset verir",
            ha="center", fontsize=8.6, color=MUTED)
    return _save(fig, _yol("fd_tablolar"))


# 3. Tampon boyutu olcumu (gercek veri) ----------------------------- #
def tampon_olcum():
    rows = [r for r in _oku_csv("b28_tampon.csv") if r["tur"] == "read"]
    boyut = [int(r["boyut"]) for r in rows]
    sure = [float(r["sure_ms"]) for r in rows]
    fg = [float(r["sure_ms"]) for r in _oku_csv("b28_tampon.csv")
          if r["tur"] == "stdio_fgetc"][0]

    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.loglog(boyut, sure, "o-", color=ACCENT, lw=1.8, ms=5,
              label="read() ile okuma")
    ax.axhline(fg, color=EDGE[1], ls="--", lw=1.2)
    ax.text(1.2, fg * 1.12, "stdio fgetc: %.1f ms" % fg, fontsize=8.8,
            color=EDGE[1])
    for b, s in zip(boyut, sure):
        if b in (1, 4096, 65536):
            ax.annotate("%.2f ms" % s, (b, s), textcoords="offset points",
                        xytext=(6, 6), fontsize=8.5, color=INK)
    ax.set_xlabel("read() tampon boyutu (bayt, log)", color=INK)
    ax.set_ylabel("süre (ms, log)", color=INK)
    ax.set_title("8 MiB dosyanın okunması: tampon boyutuna göre süre",
                 fontsize=10.5, color=INK)
    ax.grid(True, which="both", color=RULE, lw=0.6)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    for s in ax.spines.values():
        s.set_color(MUTED)
    return _save(fig, _yol("tampon_olcum"))


# 4. fsync gecikmesi (gercek veri) ----------------------------------- #
def fsync_olcum():
    d = defaultdict(list)
    for r in _oku_csv("b28_fsync_ham.csv"):
        d[r["mod"]].append(float(r["us"]))
    sira = [("yalniz_write", "yalnız yazma"), ("fdatasync", "fdatasync"),
            ("fsync", "fsync")]
    veri = [d[k] for k, _ in sira]
    etik = [e for _, e in sira]

    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    kutu = ax.boxplot(veri, patch_artist=True,
                      showfliers=True, widths=0.5,
                      flierprops=dict(marker=".", markersize=3,
                                      markerfacecolor=MUTED,
                                      markeredgecolor=MUTED))
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(etik)
    for p, c in zip(kutu["boxes"], [FILL[1], FILL[2], FILL[3]]):
        p.set_facecolor(c)
        p.set_edgecolor(EDGE[2])
    for m in kutu["medians"]:
        m.set_color(ACCENT)
    ax.set_yscale("log")
    ax.set_ylabel("4 KiB yazma süresi (µs, log)", color=INK)
    ax.set_title("Her yazmadan sonra kalıcılık: gecikme dağılımı "
                 "(300 tur)", fontsize=10.5, color=INK)
    ax.grid(True, axis="y", which="both", color=RULE, lw=0.6)
    for s in ax.spines.values():
        s.set_color(MUTED)
    return _save(fig, _yol("fsync_olcum"))


# 5. Atomik guncelleme zaman cizelgesi ------------------------------- #
def atomik_zaman():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.0)
    adimlar = [
        ("1. tmp'ye yaz", "yarım veri", "yapi.conf = ESKI", FILL[0],
         EDGE[0]),
        ("2. tam yaz", "kalıcı değil", "yapi.conf = ESKI", FILL[0],
         EDGE[0]),
        ("3. fsync(tmp)", "veri diske iner", "yapi.conf = ESKI", FILL[1],
         EDGE[1]),
        ("4. rename()", "tek adım geçiş", "yapi.conf = YENI",
         FILL[2], EDGE[2]),
        ("5. fsync(dizin)", "rename kalıcı olur", "yapi.conf = YENI",
         FILL[3], EDGE[3]),
    ]
    for i, (ad, alt, durum, fill, edge) in enumerate(adimlar):
        x = 0.2 + i * 2.75
        _box(ax, x, 3.8, 2.1, 1.3, ad + "\n" + alt, fill, edge, fs=8.4)
        _box(ax, x, 1.5, 2.1, 0.9, durum, "#ffffff", MUTED, fs=8.4)
        if i < len(adimlar) - 1:
            _arrow(ax, x + 2.1, 4.45, x + 2.75, 4.45, col=MUTED, lw=1.1)
    ax.text(7.0, 0.7, "Çökme 1, 2 ya da 3. adımda olursa yapi.conf eski "
            "sağlam hâlinde kalır.", ha="center", fontsize=8.8, color=MUTED)
    ax.text(7.0, 0.2, "Çökme 4. adımdan sonra olursa yeni dosya görünür.",
            ha="center", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("atomik_zaman"))


# 6. inode, veri bloklari, dizin girdileri -------------------------- #
def inode_bloklar():
    fig, ax = _tuval(9.6, 5.4, xl=14, yl=8.6)
    ax.text(3.0, 8.2, "inode 44341 (meta veri)", ha="center",
            fontsize=9.6, weight="bold", color=INK)
    _box(ax, 0.4, 4.4, 5.2, 3.4,
         "tür: düzenli dosya\nizin: 0644 (rw-r--r--)\n"
         "sahip: merty\nboyut: 14 bayt\nbağlantı sayısı: 2\n"
         "zaman: atime, mtime, ctime\nveri bloğu işaretçisi",
         FILL[0], EDGE[0], fs=9.0)
    ax.text(10.6, 8.2, "Veri bloğu (4 KiB)", ha="center", fontsize=9.6,
            weight="bold", color=INK)
    _box(ax, 8.4, 5.4, 4.4, 1.2, "merhaba dunya\n(14 bayt, kalan boş)",
         FILL[1], EDGE[1], fs=9.0)
    _arrow(ax, 5.6, 6.2, 8.4, 6.0, col=ACCENT, lw=1.3)

    ax.text(7.0, 3.6, "Dizin bloğu: ad → inode eşlemesi", ha="center",
            fontsize=9.6, weight="bold", color=INK)
    girdi = [("a.txt", "44341"), ("b.txt", "44341"), ("s.txt", "44345")]
    for i, (ad, ino) in enumerate(girdi):
        x = 0.6 + i * 4.5
        _box(ax, x, 1.5, 2.2, 0.9, ad, FILL[2], EDGE[2], fs=9.2)
        _box(ax, x + 2.5, 1.5, 1.8, 0.9, "inode " + ino, FILL[3], EDGE[3],
             fs=8.8)
        _arrow(ax, x + 2.2, 1.95, x + 2.5, 1.95, col=MUTED, lw=1.0)
    ax.text(7.0, 0.5, "Dizin de bir dosyadır: içeriği ad ile inode numarası "
            "çiftleridir. Dosya adı inode'da durmaz.", ha="center",
            fontsize=8.6, color=MUTED)
    return _save(fig, _yol("inode_bloklar"))


# 7. Sabit ve sembolik baglar --------------------------------------- #
def baglar():
    fig, ax = _tuval(9.6, 5.0, xl=14, yl=7.4)
    ax.text(3.4, 7.0, "Sabit bağ (ln a.txt b.txt)", ha="center",
            fontsize=10, weight="bold", color=ACCENT)
    _box(ax, 0.4, 5.0, 2.4, 0.8, "a.txt", FILL[0], EDGE[0], fs=9.4)
    _box(ax, 0.4, 3.3, 2.4, 0.8, "b.txt", FILL[0], EDGE[0], fs=9.4)
    _box(ax, 4.2, 3.9, 2.6, 1.3, "inode 44341\nbağlantı = 2", FILL[3],
         EDGE[3], fs=9.2)
    _arrow(ax, 2.8, 5.4, 4.2, 4.8, col=MUTED, lw=1.1)
    _arrow(ax, 2.8, 3.7, 4.2, 4.2, col=MUTED, lw=1.1)
    ax.text(3.4, 2.3, "İki ad aynı inode'a bakar.\nBiri silinirse veri "
            "kalır.", ha="center", fontsize=8.6, color=MUTED)

    ax.text(10.6, 7.0, "Sembolik bağ (ln -s a.txt s.txt)", ha="center",
            fontsize=10, weight="bold", color=EDGE[1])
    _box(ax, 8.2, 5.0, 2.4, 0.8, "s.txt", FILL[1], EDGE[1], fs=9.4)
    _box(ax, 8.2, 3.3, 2.4, 0.8, "içerik: \"a.txt\"", FILL[2], EDGE[2],
         fs=8.6)
    _box(ax, 12.0, 3.9, 1.8, 1.3, "inode\n44345", FILL[3], EDGE[3],
         fs=9.0)
    _arrow(ax, 9.4, 5.0, 9.4, 4.1, col=MUTED, lw=1.1)
    _arrow(ax, 10.6, 3.6, 12.0, 4.2, col=MUTED, lw=1.1, rad=0.0)
    ax.text(10.6, 2.3, "Hedefin adı metin olarak tutulur.\nHedef "
            "silinirse bağ kırılır.", ha="center", fontsize=8.6,
            color=MUTED)
    return _save(fig, _yol("baglar"))


# 8. FAT zinciri (semasal) ------------------------------------------ #
def fat_zincir():
    fig, ax = _tuval(9.6, 4.6, xl=14, yl=7.4)
    ax.text(7.0, 7.0, "FAT tablosu (şematik örnek, gerçek disk değil)",
            ha="center", fontsize=10, weight="bold", color=INK)
    kumeler = [(2, "3"), (3, "5"), (4, "boş"), (5, "EOF"), (6, "boş"),
               (7, "bozuk")]
    deger_fill = {"boş": FILL[4], "EOF": FILL[1], "bozuk": FILL[3]}
    for i, (kume, deger) in enumerate(kumeler):
        x = 0.6 + i * 2.2
        _box(ax, x, 3.2, 1.6, 0.9, "küme %d" % kume, FILL[0], EDGE[0],
             fs=8.6)
        f = deger_fill.get(deger, FILL[2])
        e = EDGE[3] if deger == "bozuk" else EDGE[2]
        _box(ax, x, 1.5, 1.6, 0.9, "→ " + deger, f, e, fs=8.6)
    # zincir oklari: 2 -> 3 -> 5 -> EOF
    _arrow(ax, 2.2, 3.65, 2.8, 3.65, col=ACCENT, lw=1.6)
    _arrow(ax, 4.4, 4.3, 7.2, 4.3, col=ACCENT, lw=1.6, rad=-0.5)
    ax.text(0.6, 0.7, "Dizin girdisi: rapor.txt, ilk küme = 2. "
            "Zincir: 2 → 3 → 5 → EOF.", fontsize=8.8, color=MUTED)
    ax.text(0.6, 0.2, "Dosya boyu ve bölünmüş küme sayısı, FAT girdilerini "
            "okuyarak bulunur.", fontsize=8.8, color=MUTED)
    return _save(fig, _yol("fat_zincir"))


# 9. G/C modelleri karsilastirmasi ---------------------------------- #
def gg_modelleri():
    fig, ax = _tuval(9.6, 6.2, xl=14, yl=9.0)
    satirlar = [
        ("Engelleyen", "read() veri gelene kadar uyur",
         "uygulama", "read()", "çekirdek: uyut", "veri gelince döner",
         FILL[0], EDGE[0]),
        ("Engellemeyen", "O_NONBLOCK: hemen döner",
         "uygulama", "read()", "çekirdek: hemen dön", "EAGAIN, sonra yokla",
         FILL[1], EDGE[1]),
        ("Çoğullama", "epoll_wait: çok fd, tek bekleme",
         "uygulama", "epoll_wait(n fd)", "çekirdek: hazır listesi",
         "hazır fd'leri oku", FILL[2], EDGE[2]),
        ("Asenkron", "io_uring: gönder, sonra al",
         "uygulama", "SQE gönder", "çekirdek: işi yapar",
         "CQE: tamamlandı", FILL[3], EDGE[3]),
    ]
    for i, (ad, aciklama, uyg, cagri, cek, sonuc, fill, edge) in \
            enumerate(satirlar):
        y = 7.0 - i * 2.0
        ax.text(0.3, y + 0.75, ad, fontsize=10, weight="bold", color=edge)
        ax.text(0.3, y + 0.25, aciklama, fontsize=8.2, color=MUTED)
        _box(ax, 4.4, y, 1.8, 0.8, uyg, FILL[4], EDGE[4], fs=8.6)
        _arrow(ax, 6.2, y + 0.4, 7.0, y + 0.4, col=edge, lw=1.3)
        ax.text(6.6, y + 0.95, cagri, ha="center", fontsize=7.8,
                color=INK)
        _box(ax, 7.0, y, 2.6, 0.8, cek, fill, edge, fs=8.6)
        _arrow(ax, 9.6, y + 0.4, 10.4, y + 0.4, col=edge, lw=1.3)
        _box(ax, 10.4, y, 3.2, 0.8, sonuc, FILL[4], EDGE[4], fs=8.4)
    return _save(fig, _yol("gg_modelleri"))


# 10. epoll / poll olcekleme (gercek veri) -------------------------- #
def epoll_olcek():
    rows = _oku_csv("b28_epoll.csv")
    n = [int(r["n"]) for r in rows]
    tp = [float(r["poll_ns"]) for r in rows]
    te = [float(r["epoll_ns"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    ax.loglog(n, tp, "o-", color=ACCENT, lw=1.8, ms=5,
              label="poll(): her çağrıda n fd taranır")
    ax.loglog(n, te, "s-", color=EDGE[1], lw=1.8, ms=5,
              label="epoll_wait(): yalnız hazır fd")
    for x, y in zip(n, tp):
        if x == 10000:
            ax.annotate("%d ns" % y, (x, y), textcoords="offset points",
                        xytext=(6, 4), fontsize=8.5, color=ACCENT)
    for x, y in zip(n, te):
        if x == 10000:
            ax.annotate("%d ns" % y, (x, y), textcoords="offset points",
                        xytext=(6, -12), fontsize=8.5, color=EDGE[1])
    ax.set_xlabel("izlenen fd sayısı n (pipe okuma ucu, log)", color=INK)
    ax.set_ylabel("çağrı başına süre (ns, log)", color=INK)
    ax.set_title("Tek aktif fd, çok sayıda boş fd: poll ile epoll",
                 fontsize=10.5, color=INK)
    ax.grid(True, which="both", color=RULE, lw=0.6)
    ax.legend(loc="upper left", fontsize=8.8, frameon=False)
    for s in ax.spines.values():
        s.set_color(MUTED)
    return _save(fig, _yol("epoll_olcek"))


if __name__ == "__main__":
    for f in (katmanlar, fd_tablolar, tampon_olcum, fsync_olcum,
              atomik_zaman, inode_bloklar, baglar, fat_zincir,
              gg_modelleri, epoll_olcek):
        print(f())
