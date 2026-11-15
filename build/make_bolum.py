# -*- coding: utf-8 -*-
"""Bir bölümü PDF'e basar ve sayfaları PNG önizlemeye render eder.

Kullanım:  python build/make_bolum.py 1
"""
import os, sys, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

from md_render import render_markdown
from kitap_engine import build_pdf, build_styles


def slug(s):
    s = s.replace("ı", "i").replace("İ", "i").replace("ş", "s").replace("Ş", "s")
    s = s.replace("ğ", "g").replace("Ğ", "g").replace("ç", "c").replace("Ç", "c")
    s = s.replace("ö", "o").replace("Ö", "o").replace("ü", "u").replace("Ü", "u")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s


def main(no):
    nn = "%02d" % int(no)
    md_path = os.path.join(ROOT, "bolumler", "bolum_%s.md" % nn)
    with open(md_path, encoding="utf-8") as f:
        md = f.read()

    S = build_styles()
    meta, story = render_markdown(md, base_dir=ROOT, S=S)
    import md_render
    for w in md_render.TABLE_WARNINGS:
        print("TABLO UYARISI (kelime sığmadı, hecelendi):", w)

    # Yeni kısmın ilk bölümüyse: ayraç sayfası (recto) en başa
    if meta.get("kisim_ayrac", "").strip().lower() in ("evet", "var", "yes", "1"):
        from kitap_engine import part_divider
        from reportlab.platypus import PageBreak
        story = (part_divider(meta.get("kisim_no", ""), meta.get("kisim_ad", ""), S)
                 + [PageBreak()] + story)

    kis = slug(meta.get("kisim_ad", "bolum"))
    out_pdf = os.path.join(ROOT, "pdf", "bolum_%s_%s.pdf" % (nn, kis))
    chap = "Bölüm %s · %s" % (meta.get("bolum_no", nn), meta.get("baslik", ""))
    build_pdf(out_pdf, story, book_title="Mühendis El Kitabı", chapter_label=chap)
    print("PDF:", out_pdf)

    import fitz
    doc = fitz.open(out_pdf)
    prev = os.path.join(ROOT, "build", "preview_b%s" % nn)
    os.makedirs(prev, exist_ok=True)
    for f in os.listdir(prev):
        os.remove(os.path.join(prev, f))
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=110).save(os.path.join(prev, "s_%02d.png" % i))
    print("Sayfa sayısı:", doc.page_count)
    print("Önizleme:", prev)
    return doc.page_count


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else 1)
