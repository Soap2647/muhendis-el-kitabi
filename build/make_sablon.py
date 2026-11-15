# -*- coding: utf-8 -*-
"""Örnek şablon PDF'ini üretir ve sayfaları PNG önizlemeye render eder."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import diagrams
from md_render import render_markdown
from kitap_engine import build_pdf, build_styles, part_divider
from reportlab.platypus import PageBreak

def main():
    gors = os.path.join(ROOT, "gorseller")
    # 1) örnek diyagramları üret
    diagrams.memory_layout(os.path.join(gors, "_ornek_memory.png"))
    diagrams.fetch_decode_execute(os.path.join(gors, "_ornek_cpu.png"))

    # 2) markdown'ı oku ve story üret
    S = build_styles()
    with open(os.path.join(ROOT, "bolumler", "sablon.md"), encoding="utf-8") as f:
        md = f.read()
    meta, story = render_markdown(md, base_dir=ROOT, S=S)

    # kısım ayraç sayfasını başa koy (recto örneği)
    full = part_divider("I", "Programlama Temelleri", S) + [PageBreak()] + story

    out_pdf = os.path.join(ROOT, "build", "sablon_ornek.pdf")
    build_pdf(out_pdf, full, running_title="Mühendis El Kitabı  ·  Şablon")
    print("PDF:", out_pdf)

    # 3) sayfaları PNG'ye render et (görsel doğrulama)
    import fitz
    doc = fitz.open(out_pdf)
    prev = os.path.join(ROOT, "build", "preview")
    os.makedirs(prev, exist_ok=True)
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=110)
        pix.save(os.path.join(prev, "sayfa_%02d.png" % i))
    print("Sayfa sayısı:", doc.page_count)
    print("Önizleme:", prev)

if __name__ == "__main__":
    main()
