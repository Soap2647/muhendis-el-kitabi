# -*- coding: utf-8 -*-
"""Kısım I genişletmesi için ek diyagramlar (B1..B4)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def endianness(path):
    """0x1A2B3C4D'nin bellekte LE ve BE dizilişi."""
    fig, ax = plt.subplots(figsize=(8.8, 3.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.8); ax.axis("off")
    ax.text(6.0, 4.45, "uint32_t x = 0x1A2B3C4D;   — aynı sayı, iki diziliş",
            ha="center", fontsize=10, color=INK, **MONO)
    addrs = ["0x1000", "0x1001", "0x1002", "0x1003"]
    le = ["4D", "3C", "2B", "1A"]
    be = ["1A", "2B", "3C", "4D"]
    for panel, (title, data, edge, note) in enumerate([
            ("Little-endian (x86, çoğu ARM)", le, EDGE[0],
             "küçük ucu (4D) küçük adrese"),
            ("Big-endian (ağ baytı sırası)", be, EDGE[3],
             "büyük ucu (1A) küçük adrese")]):
        x0 = 0.6 + panel * 6.0
        ax.text(x0 + 2.3, 3.6, title, ha="center", fontsize=9.3,
                color=edge, weight="bold")
        for i, b in enumerate(data):
            _box(ax, x0 + i * 1.18, 1.9, 1.05, 0.95, b,
                 FILL[0] if panel == 0 else FILL[3], edge, fs=11, bold=True)
            ax.text(x0 + i * 1.18 + 0.52, 1.55, addrs[i], ha="center",
                    fontsize=7.6, color=MUTED, **MONO)
        ax.text(x0 + 2.3, 0.85, note, ha="center", fontsize=8.4,
                color=MUTED, style="italic")
    return _save(fig, path)


def ieee754(path):
    """32-bit float (IEEE-754) alan düzeni: -6.25 örneği."""
    fig, ax = plt.subplots(figsize=(9.6, 3.0))
    ax.set_xlim(0, 13.6); ax.set_ylim(0, 4.0); ax.axis("off")
    ax.text(6.8, 3.6, "float f = -6.25;    →    (-1)^işaret × 1.mantis × 2^(üs-127)",
            ha="center", fontsize=9.6, color=INK, **MONO)
    # işaret 1 bit
    _box(ax, 0.6, 1.7, 0.85, 1.0, "1", FILL[3], EDGE[3], fs=11, bold=True)
    ax.text(1.02, 1.35, "işaret\n(1 bit)", ha="center", va="top", fontsize=7.8,
            color=EDGE[3])
    # üs 8 bit
    us = "10000001"
    for i, b in enumerate(us):
        _box(ax, 1.75 + i * 0.72, 1.7, 0.62, 1.0, b, FILL[2], EDGE[2],
             fs=9.5, bold=True)
    ax.text(4.55, 1.35, "üs = 129  →  129-127 = 2   (8 bit)", ha="center",
            va="top", fontsize=7.8, color=EDGE[2])
    # mantis 23 bit (kısaltılmış gösterim)
    man = ["1", "0", "0", "1", "0", "0", "0", "…", "0"]
    for i, b in enumerate(man):
        _box(ax, 7.75 + i * 0.62, 1.7, 0.54, 1.0, b, FILL[1], EDGE[1],
             fs=9, bold=b != "…")
    ax.text(10.5, 1.35, "mantis = 1001…  →  1.1001₂   (23 bit)", ha="center",
            va="top", fontsize=7.8, color=EDGE[1])
    ax.text(6.8, 0.42, "-6.25 = -110.01₂ = -1.1001₂ × 2²   →   işaret=1, üs=2+127, mantis=1001…",
            ha="center", fontsize=8.6, color=MUTED, **MONO)
    return _save(fig, path)


def c_file_io(path):
    """C dosya G/Ç: program ↔ FILE* tamponu ↔ disk."""
    fig, ax = plt.subplots(figsize=(8.8, 3.0))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.0); ax.axis("off")
    _box(ax, 0.6, 1.5, 2.8, 1.3, "programın\n(değişkenler)", FILL[0], EDGE[0],
         fs=9.3, bold=True)
    _box(ax, 4.6, 1.5, 2.8, 1.3, "FILE* tamponu\n(RAM'de)", FILL[2], EDGE[2],
         fs=9.3, bold=True)
    _box(ax, 8.6, 1.5, 2.8, 1.3, "disk\n(kalıcı dosya)", FILL[1], EDGE[1],
         fs=9.3, bold=True)
    _arrow(ax, 3.45, 2.45, 4.55, 2.45, col=EDGE[2], lw=1.6)
    _arrow(ax, 4.55, 1.85, 3.45, 1.85, col=EDGE[2], lw=1.6)
    ax.text(4.0, 2.75, "fprintf / fwrite", ha="center", fontsize=7.8,
            color=EDGE[2], **MONO)
    ax.text(4.0, 1.18, "fgets / fread", ha="center", fontsize=7.8,
            color=EDGE[2], **MONO)
    _arrow(ax, 7.45, 2.45, 8.55, 2.45, col=EDGE[1], lw=1.6)
    _arrow(ax, 8.55, 1.85, 7.45, 1.85, col=EDGE[1], lw=1.6)
    ax.text(8.0, 2.75, "fflush / fclose", ha="center", fontsize=7.8,
            color=EDGE[1], **MONO)
    ax.text(8.0, 1.18, "işletim sistemi", ha="center", fontsize=7.8,
            color=MUTED, **MONO)
    ax.text(6.0, 3.55, "fopen sözleşmeyi açar, fclose tamponu boşaltıp kapatır",
            ha="center", fontsize=9.4, color=INK, style="italic")
    ax.text(6.0, 0.5, "fclose çağrılmazsa tampondaki son yazılanlar diske hiç inmeyebilir!",
            ha="center", fontsize=8.6, color=EDGE[3])
    return _save(fig, path)


def py_exception(path):
    """İstisnanın çağrı yığınında yukarı tırmanışı."""
    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.2); ax.axis("off")
    frames = [
        ("main()\ntry/except BURADA", FILL[1], EDGE[1], 0.6),
        ("oku_ve_topla()\n(yakalamıyor)", FILL[0], EDGE[0], 2.05),
        ("int(\"abc\")\nValueError DOĞAR", FILL[3], EDGE[3], 3.5),
    ]
    for text, fill, edge, y in frames:
        _box(ax, 1.0, y, 3.6, 1.25, text, fill, edge, fs=8.8, bold=True)
    for y1, y2 in ((3.5, 3.3), (2.05, 1.85)):
        pass
    _arrow(ax, 4.8, 3.9, 4.8, 2.75, col=EDGE[3], lw=1.8)
    _arrow(ax, 4.8, 2.45, 4.8, 1.3, col=EDGE[3], lw=1.8)
    ax.text(5.15, 2.6, "istisna yukarı\ntırmanır", fontsize=8.6, color=EDGE[3],
            va="center")
    _box(ax, 7.6, 0.6, 3.6, 1.25, "except ValueError:\nburada YAKALANIR",
         FILL[1], EDGE[1], fs=8.8, bold=True)
    _arrow(ax, 4.65, 1.2, 7.55, 1.2, col=EDGE[1], lw=1.8)
    ax.text(8.2, 3.2, "Yakalayan çıkmazsa:\nprogram düşer,\ntraceback basılır",
            ha="center", fontsize=8.6, color=MUTED)
    ax.text(6.0, 4.85, "raise anı: kontrol, ilk uygun except bulunana dek çerçeve çerçeve geri sarar",
            ha="center", fontsize=9.2, color=INK, style="italic")
    return _save(fig, path)


def slicing_ruler(path):
    """Dilimleme cetveli: pozitif/negatif indeksler ve s[1:4]."""
    fig, ax = plt.subplots(figsize=(8.4, 3.0))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.0); ax.axis("off")
    s = "MERTOS"
    x0, w, y = 2.4, 1.15, 1.6
    for i, ch in enumerate(s):
        sel = 1 <= i < 4
        _box(ax, x0 + i * w, y, w - 0.08, 1.0, ch,
             FILL[3] if sel else FILL[0], EDGE[3] if sel else EDGE[0],
             fs=12, bold=True)
        ax.text(x0 + i * w + (w - 0.08) / 2, y + 1.35, str(i), ha="center",
                fontsize=9, color=EDGE[2], **MONO)
        ax.text(x0 + i * w + (w - 0.08) / 2, y - 0.35, str(i - 6), ha="center",
                fontsize=9, color=MUTED, **MONO)
    ax.text(1.7, y + 1.35, "indeks:", ha="right", fontsize=8.4, color=EDGE[2])
    ax.text(1.7, y - 0.35, "negatif:", ha="right", fontsize=8.4, color=MUTED)
    ax.text(6.0, 3.55, 's = "MERTOS"      s[1:4] → "ERT"      (başlangıç dahil, bitiş HARİÇ)',
            ha="center", fontsize=9.4, color=INK, **MONO)
    ax.text(6.0, 0.5, 's[-2:] → "OS"      s[::2] → "MRO"      s[::-1] → "SOTREM"',
            ha="center", fontsize=9.2, color=MUTED, **MONO)
    return _save(fig, path)


def permissions(path):
    """chmod: rwx bitleri → sekizlik sayı (754 örneği)."""
    fig, ax = plt.subplots(figsize=(8.8, 3.4))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.6); ax.axis("off")
    ax.text(6.0, 4.2, "-rwxr-xr--   →   chmod 754   (Bölüm 1'in bitleri iş başında)",
            ha="center", fontsize=9.8, color=INK, **MONO)
    groups = [("sahip (u)", "rwx", "111", "7", EDGE[1]),
              ("grup (g)", "r-x", "101", "5", EDGE[2]),
              ("diğerleri (o)", "r--", "100", "4", EDGE[3])]
    for gi, (ad, harf, bits, okt, edge) in enumerate(groups):
        x0 = 0.8 + gi * 3.9
        ax.text(x0 + 1.55, 3.35, ad, ha="center", fontsize=9, color=edge,
                weight="bold")
        for i, (h, b) in enumerate(zip(harf, bits)):
            _box(ax, x0 + i * 1.06, 1.9, 0.95, 0.9,
                 h if h != "-" else "–", FILL[0] if b == "1" else "#FFFFFF",
                 edge if b == "1" else RULE, fs=10.5, bold=True,
                 tcol=INK if b == "1" else MUTED)
            ax.text(x0 + i * 1.06 + 0.47, 1.55, b, ha="center", fontsize=8.6,
                    color=edge if b == "1" else MUTED, **MONO)
        ax.text(x0 + 1.55, 0.85, "%s₂ = %s" % (bits, okt), ha="center",
                fontsize=9.6, color=edge, weight="bold", **MONO)
    ax.text(6.0, 0.25, "r=4  w=2  x=1  → topla:  rwx=7,  r-x=5,  r--=4",
            ha="center", fontsize=8.8, color=MUTED, **MONO)
    return _save(fig, path)


def git_remote(path):
    """Yerel depo ↔ uzak depo (origin/GitHub)."""
    fig, ax = plt.subplots(figsize=(8.8, 3.4))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.6); ax.axis("off")
    _box(ax, 0.7, 1.5, 3.6, 1.9, "", FILL[0], EDGE[0])
    ax.text(2.5, 3.05, "SENİN MAKİNEN", ha="center", fontsize=8.6,
            color=EDGE[0], weight="bold")
    ax.text(2.5, 2.45, "çalışma dizini\n+ yerel depo (.git)", ha="center",
            fontsize=8.8, color=INK)
    _box(ax, 7.7, 1.5, 3.6, 1.9, "", FILL[1], EDGE[1])
    ax.text(9.5, 3.05, "UZAK DEPO (origin)", ha="center", fontsize=8.6,
            color=EDGE[1], weight="bold")
    ax.text(9.5, 2.45, "GitHub / GitLab /\nşirket sunucusu", ha="center",
            fontsize=8.8, color=INK)
    _arrow(ax, 4.4, 2.75, 7.6, 2.75, col=EDGE[2], lw=1.8)
    ax.text(6.0, 3.05, "git push  (commit'lerini gönder)", ha="center",
            fontsize=8.4, color=EDGE[2], **MONO)
    _arrow(ax, 7.6, 1.95, 4.4, 1.95, col=EDGE[4], lw=1.8)
    ax.text(6.0, 1.6, "git pull = fetch + merge  (yenilikleri al)", ha="center",
            fontsize=8.4, color=EDGE[4], **MONO)
    ax.text(6.0, 0.6, "ilk kopya: git clone URL   —   depo + tüm tarih tek komutla iner",
            ha="center", fontsize=8.8, color=MUTED, **MONO)
    ax.text(6.0, 4.25, "commit yereldir; push edene kadar kimse görmez",
            ha="center", fontsize=9.4, color=INK, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(endianness(os.path.join(out, "b01_endian.png")))
    print(ieee754(os.path.join(out, "b01_ieee754.png")))
    print(c_file_io(os.path.join(out, "b02_file_io.png")))
    print(py_exception(os.path.join(out, "b03_exception.png")))
    print(slicing_ruler(os.path.join(out, "b03_slicing.png")))
    print(permissions(os.path.join(out, "b04_permissions.png")))
    print(git_remote(os.path.join(out, "b04_git_remote.png")))
