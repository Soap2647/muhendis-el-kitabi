# -*- coding: utf-8 -*-
"""Dizgi denetçisi — bir PDF'i tarar ve şunları raporlar:

1) KENAR İHLALİ: içerik üst/alt bilgi bandına taşıyor mu?
   İçerik çerçevesi: y ∈ [TOP_M, H - BOT_M]  (üst bilgi ve sayfa no hariç)
2) ÖKSÜZ BAŞLIK: sayfanın son bölgesinde (dip ~%22) başlayan başlık var mı
   ve altında yeterli içerik yok mu?

Kullanım: python build/check_layout.py pdf/bolum_01_*.pdf
"""
import sys, glob, os
import fitz
sys.stdout.reconfigure(encoding="utf-8")

PT = 72 / 25.4  # mm -> pt
TOP_M = 2.5 * 10 * PT      # 70.87
BOT_M = 2.5 * 10 * PT
H = 841.89
FRAME_TOP = TOP_M                 # içerik bu satırın ALTINDA olmalı
FRAME_BOT = H - BOT_M             # içerik bu satırın ÜSTÜNDE olmalı
TOL = 1.5

def check(path):
    doc = fitz.open(path)
    problems = []
    for pno, page in enumerate(doc, 1):
        d = page.get_text("dict")
        # --- kenar ihlali (metin) ---
        for block in d["blocks"]:
            if block["type"] != 0:
                # görüntü bloğu
                x0, y0, x1, y1 = block["bbox"]
                if y0 < FRAME_TOP - TOL and y1 > FRAME_TOP:
                    problems.append((pno, "GÖRSEL üst bandı kesiyor (y0=%.0f)" % y0))
                if y1 > FRAME_BOT + TOL and y0 < FRAME_BOT:
                    problems.append((pno, "GÖRSEL alt bandı kesiyor (y1=%.0f)" % y1))
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    txt = span["text"].strip()
                    if not txt:
                        continue
                    in_header = y1 <= FRAME_TOP - 3          # üst bilgi bölgesi
                    is_pageno = (txt.isdigit() and y0 >= FRAME_BOT + 14)
                    if in_header or is_pageno:
                        continue
                    # üst indis (küçük punto) ilk satırda ~2 pt yükselir;
                    # üst bilgi çizgisine ulaşmaz, kusur sayılmaz
                    sup_ok = (span["flags"] & 1 or span["size"] < 10.5) and y0 >= FRAME_TOP - 4
                    if y0 < FRAME_TOP - TOL and not sup_ok:
                        problems.append((pno, "METİN üst banda taşmış: %r y0=%.0f"
                                         % (txt[:30], y0)))
                    if y1 > FRAME_BOT + TOL:
                        problems.append((pno, "METİN alt banda taşmış: %r y1=%.0f"
                                         % (txt[:30], y1)))
        # --- öksüz başlık ---
        # başlık tespiti: Sans-Bold (DejaVuSans-Bold) ve punto >= 10.4
        heads = []
        last_content_y = 0
        for block in d["blocks"]:
            if block["type"] != 0:
                x0, y0, x1, y1 = block["bbox"]
                last_content_y = max(last_content_y, y1)
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    if not txt or span["bbox"][3] <= FRAME_TOP - 3:
                        continue
                    if txt.isdigit() and span["bbox"][1] >= FRAME_BOT + 14:
                        continue
                    last_content_y = max(last_content_y, span["bbox"][3])
                    if ("Sans-Bold" in span["font"] and span["size"] >= 10.4):
                        heads.append((span["bbox"][1], span["bbox"][3], txt))
        # sayfa içeriğinin dip sınırından başlık dibine bakılır
        for (hy0, hy1, txt) in heads:
            if hy0 > FRAME_BOT - 0.22 * (FRAME_BOT - FRAME_TOP):
                # başlığın altındaki içerik miktarı
                below = last_content_y - hy1
                if below < 60:   # ~4 satırdan az
                    problems.append((pno, "ÖKSÜZ BAŞLIK dipte: %r (altında %.0fpt içerik)"
                                     % (txt[:40], below)))
    if problems:
        print("SORUN (%d):" % len(problems))
        for pno, msg in problems:
            print("  sayfa %2d: %s" % (pno, msg))
    else:
        print("TEMİZ: kenar ihlali ve öksüz başlık yok.")
    print("Toplam sayfa:", doc.page_count)
    return problems

if __name__ == "__main__":
    pat = sys.argv[1] if len(sys.argv) > 1 else "pdf/*.pdf"
    for p in glob.glob(pat):
        print("==", os.path.basename(p))
        check(p)
