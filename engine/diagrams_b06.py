# -*- coding: utf-8 -*-
"""Bölüm 6 — 'Debugging Sanatı' için diyagramlar."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from diagrams import (_box, _arrow, _save, ACCENT, ACCENT_L, INK, MUTED,
                      RULE, FILL, EDGE)

MONO = {"family": "DejaVu Sans Mono"}


def debug_cycle(path):
    """Beş adımlı hata ayıklama döngüsü."""
    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    ax.set_xlim(0, 13.2); ax.set_ylim(0, 6.9); ax.axis("off")
    steps = [
        ("1. ÜRET", "hatayı istediğin\nan tekrarla", EDGE[0], FILL[0]),
        ("2. İZOLE ET", "arama alanını\nyarıya böl", EDGE[1], FILL[1]),
        ("3. TEŞHİS", "hipotez kur,\ndeneyle sına", EDGE[2], FILL[2]),
        ("4. DÜZELT", "kök nedeni,\nsemptomu değil", EDGE[4], FILL[4]),
        ("5. DOĞRULA", "regresyon testi\nyaz ve koştur", EDGE[3], FILL[3]),
    ]
    x0, w, gap = 0.5, 2.35, 0.22
    y = 3.4
    for i, (ad, alt, edge, fill) in enumerate(steps):
        x = x0 + i * (w + gap)
        _box(ax, x, y, w, 1.5, "", fill, edge)
        ax.text(x + w/2, y + 1.12, ad, ha="center", fontsize=9.6,
                color=edge, weight="bold")
        ax.text(x + w/2, y + 0.45, alt, ha="center", fontsize=8, color=INK)
        if i < 4:
            _arrow(ax, x + w + 0.01, y + 0.75, x + w + gap - 0.02, y + 0.75,
                   col=MUTED, lw=1.4)
    ax.annotate("", xy=(x0 + w/2, y + 1.56),
                xytext=(x0 + 4*(w+gap) + w/2, y + 1.56),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4,
                                connectionstyle="bar,fraction=0.14"))
    ax.text(6.6, 6.62,
            "hipotez çürüdü ya da düzeltme tutmadı: yeni bilgiyle tekrar",
            ha="center", fontsize=8.6, color=ACCENT, style="italic")
    ax.text(6.6, 2.55, "Adım 1'i atlayamazsın: tekrar üretemediğin hatayı düzelttiğini "
            "asla kanıtlayamazsın.",
            ha="center", fontsize=9.2, color=INK, weight="bold")
    ax.text(6.6, 1.75, "Bu döngü Bölüm 5'in problem çözme döngüsünün ikizidir — "
            "burada \"problem\" senin kodundur.",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


def bisection(path):
    """İkili aramayla hata izolasyonu: veri, kod ve tarih üzerinde."""
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    ax.set_xlim(0, 13.4); ax.set_ylim(0, 7.2); ax.axis("off")
    ax.text(6.7, 6.85, "Aynı fikir, üç ayrı eksen: her denemede arama alanını YARIYA böl",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    # 1) veri üzerinde
    ax.text(0.4, 5.9, "VERİ:  10 000 satırlık girdide hangisi çökertiyor?",
            fontsize=8.8, color=EDGE[0], weight="bold")
    genis = 11.6
    for i, (etiket, orani, renk) in enumerate([
            ("10 000 satır — çöküyor", 1.0, EDGE[3]),
            ("5 000 satır — çöküyor", 0.5, EDGE[3]),
            ("2 500 — sorun yok", 0.25, EDGE[1]),
            ("3 750 — çöküyor", 0.375, EDGE[3])]):
        yy = 5.35 - i * 0.62
        _box(ax, 0.5, yy, genis * orani, 0.46, "", FILL[3] if renk == EDGE[3] else FILL[1],
             renk)
        ax.text(0.72, yy + 0.23, etiket, ha="left", va="center", fontsize=7.8,
                color=INK)
    ax.text(5.05, 3.49, "→ hata 2 500 ile 3 750 arasında", ha="left",
            va="center", fontsize=7.8, color=EDGE[3], weight="bold")
    ax.text(6.7, 2.72, "Tek tek arasan 10 000 deneme; ikiye bölerek "
            "log₂(10 000) ≈ 14 deneme.",
            ha="center", fontsize=8.2, color=MUTED, style="italic")
    # 2) tarih üzerinde (git bisect)
    ax.text(0.4, 2.15, "TARİH:  200 commit önce çalışıyordu, hangisi bozdu?",
            fontsize=8.8, color=EDGE[4], weight="bold")
    n = 9
    for i in range(n):
        x = 0.6 + i * 1.42
        if i == 0:
            renk, fill, lab = EDGE[1], FILL[1], "iyi"
        elif i == n - 1:
            renk, fill, lab = EDGE[3], FILL[3], "kötü"
        elif i == 4:
            renk, fill, lab = EDGE[2], FILL[2], "test?"
        else:
            renk, fill, lab = RULE, "#FFFFFF", ""
        _box(ax, x, 1.1, 1.28, 0.62, lab, fill, renk, fs=7.6, bold=bool(lab),
             tcol=INK if lab else MUTED)
        if i:
            ax.plot([x - 0.14, x], [1.41, 1.41], color=RULE, lw=1)
    ax.text(6.7, 0.45, "git bisect start → git bisect bad → git bisect good <commit>  "
            "→ git her adımda ortayı verir",
            ha="center", fontsize=8.2, color=EDGE[4], **MONO)
    return _save(fig, path)


def traceback_anatomy(path):
    """Python traceback'inin anatomisi."""
    fig, ax = plt.subplots(figsize=(9.4, 4.4))
    ax.set_xlim(0, 13.4); ax.set_ylim(0, 6.8); ax.axis("off")
    ax.text(6.7, 6.45, "Traceback'i SONDAN başa oku: hata türü önce, suçlu sonra",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    satirlar = [
        ('Traceback (most recent call last):', MUTED, ""),
        ('  File "analiz.py", line 42, in <module>', INK, "en DIŞ çağrı"),
        ('    sonuc = ortalama(veriler)', MUTED, ""),
        ('  File "analiz.py", line 18, in ortalama', INK, "ara çağrı"),
        ('    return toplam / len(dizi)', MUTED, ""),
        ('ZeroDivisionError: division by zero', EDGE[3], "★ ÖNCE BUNU OKU"),
    ]
    y = 5.5
    _box(ax, 0.5, 1.35, 8.4, 4.55, "", "#1A1C20", "#1A1C20")
    for metin, renk, not_ in satirlar:
        ax.text(0.75, y, metin, ha="left", va="center", fontsize=8.4,
                color="#D9D9D2" if renk in (MUTED, INK) else "#E88",
                **MONO)
        if not_:
            _arrow(ax, 9.05, y, 8.95, y, col=EDGE[3] if "★" in not_ else MUTED,
                   lw=1.2)
            ax.text(9.25, y, not_, ha="left", va="center", fontsize=8.2,
                    color=EDGE[3] if "★" in not_ else MUTED,
                    weight="bold" if "★" in not_ else "normal")
        y -= 0.72
    ax.text(6.7, 0.75, "Sıra: (1) hata türü ve mesajı  (2) EN ALTTAKİ senin dosyan  "
            "(3) o satırdaki değişkenler",
            ha="center", fontsize=8.6, color=INK)
    ax.text(6.7, 0.28, "\"En alttaki kendi dosyam\" kuralı, kütüphane içi çağrılarda "
            "seni doğru yere götürür.",
            ha="center", fontsize=8.2, color=MUTED, style="italic")
    return _save(fig, path)


def tool_matrix(path):
    """Belirti → araç eşlemesi."""
    fig, ax = plt.subplots(figsize=(9.4, 5.4))
    ax.set_xlim(0, 13.4); ax.set_ylim(-0.5, 9.4); ax.axis("off")
    ax.text(6.7, 9.0, "Belirti sana aracı söyler", ha="center", fontsize=10.4,
            color=INK, weight="bold")
    rows = [
        ("Program çöktü (segfault)", "gdb + backtrace, ASan", EDGE[3]),
        ("Bellek sızıntısı / bozulma", "valgrind, AddressSanitizer", EDGE[3]),
        ("Yanlış sonuç, çökme yok", "log + ikili arama + hipotez", EDGE[2]),
        ("Bazen oluyor, bazen değil", "log, ThreadSanitizer, tekrar üret", EDGE[2]),
        ("Yavaş çalışıyor", "profiler (perf, cProfile)", EDGE[0]),
        ("İstisna fırladı (Python)", "traceback + pdb", EDGE[1]),
        ("Ne zaman bozuldu bilmiyorum", "git bisect", EDGE[4]),
        ("Tanımsız davranış şüphesi", "UBSan, -Wall -Wextra", EDGE[3]),
    ]
    y = 8.3
    for belirti, arac, edge in rows:
        y -= 1.0
        _box(ax, 0.5, y, 6.0, 0.8, belirti, "#FFFFFF", RULE, fs=8.8, tcol=INK)
        _arrow(ax, 6.6, y + 0.4, 7.15, y + 0.4, col=edge, lw=1.4)
        _box(ax, 7.2, y, 5.7, 0.8, arac, FILL[EDGE.index(edge)], edge,
             fs=8.8, bold=True, tcol=edge)
    ax.text(6.7, -0.3, "Kural: en ucuz araçla başla (okuma → log), tıkanınca ağır "
            "topu çıkar (gdb, sanitizer).",
            ha="center", fontsize=8.6, color=ACCENT, style="italic")
    return _save(fig, path)


def hypothesis_loop(path):
    """Bilimsel yöntemle teşhis döngüsü."""
    fig, ax = plt.subplots(figsize=(9.0, 3.8))
    ax.set_xlim(0, 12.6); ax.set_ylim(0, 5.4); ax.axis("off")
    ax.text(6.3, 5.05, "Teşhis = bilimsel yöntem. Tahmin etmek değil, SINAMAK.",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    kutular = [
        ("GÖZLEM", "belirti ne?\n\"3. satırda\nçöküyor\"", EDGE[0], FILL[0]),
        ("HİPOTEZ", "\"dizi boş\ngeliyor olmalı\"", EDGE[2], FILL[2]),
        ("TAHMİN", "\"öyleyse len()\n0 basmalı\"", EDGE[4], FILL[4]),
        ("DENEY", "tek değişkeni\nölç / yazdır", EDGE[1], FILL[1]),
    ]
    x0, w, gap = 0.6, 2.6, 0.42
    for i, (ad, alt, edge, fill) in enumerate(kutular):
        x = x0 + i * (w + gap)
        _box(ax, x, 2.0, w, 1.55, "", fill, edge)
        ax.text(x + w/2, 3.15, ad, ha="center", fontsize=9.4, color=edge,
                weight="bold")
        ax.text(x + w/2, 2.45, alt, ha="center", fontsize=7.8, color=INK)
        if i < 3:
            _arrow(ax, x + w + 0.02, 2.78, x + w + gap - 0.04, 2.78,
                   col=MUTED, lw=1.4)
    ax.annotate("", xy=(x0 + w/2, 1.95), xytext=(x0 + 3*(w+gap) + w/2, 1.95),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4,
                                connectionstyle="bar,fraction=-0.055"))
    ax.text(6.3, 0.72, "Hipotez çürüdüyse SEVİN: arama alanı daraldı. "
            "Doğrulandıysa bir katman aşağı in.",
            ha="center", fontsize=8.8, color=ACCENT, style="italic")
    ax.text(6.3, 0.24, "Altın kural: her deneyde TEK bir şeyi değiştir — "
            "yoksa hangisinin işe yaradığını bilemezsin.",
            ha="center", fontsize=8.8, color=INK)
    return _save(fig, path)


def race_condition(path):
    """İki iş parçacığının araya girmesiyle kaybolan güncelleme."""
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    ax.set_xlim(0, 13.0); ax.set_ylim(0, 6.2); ax.axis("off")
    ax.text(6.5, 5.85, "sayac++ tek işlem DEĞİLDİR: oku → artır → yaz",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    ax.plot([2.6, 2.6], [0.9, 5.2], color=RULE, lw=1)
    ax.plot([7.7, 7.7], [0.9, 5.2], color=RULE, lw=1)
    ax.text(1.5, 5.35, "İŞ PARÇACIĞI A", ha="center", fontsize=8.8,
            color=EDGE[0], weight="bold")
    ax.text(5.1, 5.35, "zaman ↓", ha="center", fontsize=8.4, color=MUTED)
    ax.text(10.3, 5.35, "İŞ PARÇACIĞI B", ha="center", fontsize=8.8,
            color=EDGE[4], weight="bold")
    adimlar = [
        ("oku: sayac = 5", None, "A okudu: 5"),
        (None, "oku: sayac = 5", "B de 5 okudu (!)"),
        ("artır: 5 + 1 = 6", None, ""),
        (None, "artır: 5 + 1 = 6", ""),
        ("yaz: sayac = 6", None, ""),
        (None, "yaz: sayac = 6", "iki artış → sonuç 6, 7 değil"),
    ]
    y = 4.75
    for sol, sag, not_ in adimlar:
        if sol:
            _box(ax, 0.4, y - 0.28, 2.05, 0.56, sol, FILL[0], EDGE[0], fs=7.8)
        if sag:
            _box(ax, 7.85, y - 0.28, 2.05, 0.56, sag, FILL[4], EDGE[4], fs=7.8)
        if not_:
            ax.text(10.15, y, not_, ha="left", va="center", fontsize=7.8,
                    color=EDGE[3] if "!" in not_ or "değil" in not_ else MUTED)
        y -= 0.66
    ax.text(6.5, 0.45, "Yarış koşulu: doğruluk, işletim sisteminin zamanlama keyfine "
            "kalmıştır — bu yüzden \"bazen\" bozulur.",
            ha="center", fontsize=8.6, color=MUTED, style="italic")
    return _save(fig, path)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "gorseller")
    print(debug_cycle(os.path.join(out, "b06_cycle.png")))
    print(bisection(os.path.join(out, "b06_bisect.png")))
    print(traceback_anatomy(os.path.join(out, "b06_traceback.png")))
    print(tool_matrix(os.path.join(out, "b06_tools.png")))
    print(hypothesis_loop(os.path.join(out, "b06_hypothesis.png")))
    print(race_condition(os.path.join(out, "b06_race.png")))
