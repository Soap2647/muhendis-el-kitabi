# -*- coding: utf-8 -*-
"""
Bölüm 70 - Derlem hazırlığı: kitabın kendi metninden düz metin
külliyatı.

Kullanım:  python g01_korpus.py
Çıktılar (bu klasörde):
  paragraflar.json : [{"n": bölüm, "kisim": 0..14, "metin": "..."}]
  bolum_bolme.json : {"egitim": [...], "dogrulama": [...], "test":
  [...]}
Bölme bölüm düzeyindedir: n % 7 == 3 test, n % 7 == 5 doğrulama,
kalanı eğitim.
Böylece aynı bölümün paragrafları iki kümeye birden düşmez (sızıntı
yok).
"""

import glob
import json
import os
import re

KITAP = "D:/Mevcut Projeler/Kitap/bolumler"
KLASOR = os.path.dirname(os.path.abspath(__file__))
ROMEN = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
    "XIII",
    "XIV",
    "XV",
    "XVI",
]
# Snapshot: yalnızca bu tarihte var olan bölümler (68, 69, 70
# yazılıyor).
BOLUMLER = list(range(1, 68))


def temizle(md):
    """İşaretlemeyi at; yalnızca doğal dil cümlelerini bırak."""
    satirlar = []
    kod = False
    for s in md.splitlines():
        if s.startswith("```"):
            kod = not kod
            continue
        if kod:
            continue
        t = s.strip()
        if not t or t.startswith("%%") or t.startswith("|"):
            continue
        if t.startswith("![") or t.startswith("---"):
            continue
        if t.startswith("::: ") or t == ":::":
            continue
        if t.startswith("#"):
            t = t.lstrip("#").strip()
        t = re.sub(r"https?://\S+", " ", t)
        t = re.sub(r"`([^`]*)`", r"\1", t)
        t = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", t)
        t = re.sub(
            r"\$[^$]*\$", " ", t
        )  # satır içi LaTeX yoksa bile güvenli
        t = re.sub(r"^\s*(\d+\.|-)\s+", "", t)
        satirlar.append(t)
    metin = "\n".join(satirlar)
    metin = re.sub(r"[ \t]+", " ", metin)
    return metin


def kisim_no(md):
    m = re.search(r"%% kisim_no:\s*([IVXL]+)", md)
    if not m:
        return None
    return ROMEN.index(m.group(1))


def main():
    paragraflar = []
    for n in BOLUMLER:
        yol = os.path.join(KITAP, "bolum_%02d.md" % n)
        md = open(yol, encoding="utf-8").read()
        k = kisim_no(md)
        assert k is not None, n
        metin = temizle(md)
        for p in metin.split("\n"):
            p = p.strip()
            if len(p) >= 150:
                paragraflar.append({"n": n, "kisim": k, "metin": p})
    bolme = {"egitim": [], "dogrulama": [], "test": []}
    for i, p in enumerate(paragraflar):
        r = p["n"] % 7
        anahtar = (
            "test"
            if r == 3
            else ("dogrulama" if r == 5 else "egitim")
        )
        bolme[anahtar].append(i)
    with open(
        os.path.join(KLASOR, "paragraflar.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(paragraflar, f, ensure_ascii=False)
    with open(
        os.path.join(KLASOR, "bolum_bolme.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(bolme, f)
    # Düz metin külliyatı: eğitim+doğrulama+test bölümlerinin
    # birleşimi (ayrı dosyalar)
    for anahtar in ("egitim", "dogrulama", "test"):
        with open(
            os.path.join(KLASOR, "korpus_%s.txt" % anahtar),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                "\n".join(
                    paragraflar[i]["metin"] for i in bolme[anahtar]
                )
            )
    print("paragraf:", len(paragraflar))
    for anahtar in bolme:
        ch = sum(len(paragraflar[i]["metin"]) for i in bolme[anahtar])
        print(
            "%-10s paragraf=%6d karakter=%9d"
            % (anahtar, len(bolme[anahtar]), ch)
        )
    kis = {}
    for p in paragraflar:
        kis[p["kisim"]] = kis.get(p["kisim"], 0) + 1
    print(
        "kısım dağılımı (paragraf):",
        [kis.get(k, 0) for k in range(15)],
    )


if __name__ == "__main__":
    main()
