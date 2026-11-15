# -*- coding: utf-8 -*-
"""Basılı kitapta gözle bakmadan yakalanabilecek dizgi kusurlarını tarar.

Kullanım:  python build/check_print.py            (tüm pdf/bolum_*.pdf)
           python build/check_print.py 67 68      (yalnız bu bölümler)

Kontroller
  A  sızan biçim işareti   : **, ``, ##, <b>, &amp;, |---, [[, ](, \\ufffd ...
  B  kelime ortasından kırık: satır harfle bitiyor, sonraki satır küçük harfle
     başlıyor ve birleşimi metindeki bir kelime ya da sözlükte yok ama
     ikisi ayrı ayrı da kelime değil (tablo hücresi bölünmesi tipik örnek)
  C  aşırı geniş kelime boşluğu (iki yana yaslı satırda boşluk > 3.2 em)
  D  boşa giden sayfa: bölüm sonu değilken sayfanın %55'inden fazlası boş
  E  şekil açıklaması yetim: sayfa "Şekil N.M" açıklamasıyla başlıyor
Çıktı: bölüm başına sayaç + ilk örnekler; build/print_rapor.txt'ye tam liste.
"""
import glob, os, re, sys
from collections import Counter, defaultdict
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = re.compile(r"\*\*|``|^#{1,4}\s|<b>|</b>|<i>|&amp;|&lt;|&gt;|\|-{3}"
                 r"|\]\(|�|\\\(|\\\[|%%|_\{|\^\{|\\frac|\\sum|\\cdot",
                 re.M)
WORD = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüâîû]+")


def is_mono(font):
    return "Mono" in font


def lines_of(page):
    """(y, x0, x1, metin, font, size, spans) — kod (Mono) satırları hariç."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans or all(is_mono(s["font"]) for s in spans):
                continue
            txt = "".join(s["text"] for s in ln["spans"])
            out.append((ln["bbox"][1], ln["bbox"][0], ln["bbox"][2], txt,
                        spans[0]["font"], spans[0]["size"], spans, b["number"]))
    return out


def scan(pdf, vocab):
    doc = fitz.open(pdf)
    res = defaultdict(list)
    n = doc.page_count
    for pi in range(n):
        page = doc[pi]
        # kod (Mono) dışındaki metin; kod içinde ** ve [[ meşrudur
        text = "\n".join(
            "".join(s["text"] for s in ln["spans"] if not is_mono(s["font"]))
            for b in page.get_text("dict")["blocks"]
            for ln in b.get("lines", []))
        for m in ART.finditer(text):
            ctx = text[max(0, m.start() - 25): m.end() + 25].replace("\n", " ")
            res["A"].append((pi + 1, ctx))
        L = lines_of(page)
        # B: aynı blokta ardışık satırlar
        for (y, x0, x1, t, f, s, sp, bn), (y2, _, _, t2, f2, _, _, bn2) in zip(L, L[1:]):
            if bn != bn2:
                continue
            a = WORD.findall(t)
            b = WORD.findall(t2)
            if not a or not b or not t.rstrip()[-1:].isalpha():
                continue
            if not t2.lstrip()[:1].islower():
                continue
            w1, w2 = a[-1], b[0]
            joined = (w1 + w2).lower()
            if (joined in vocab and w1.lower() not in vocab
                    and len(w1) > 1):
                res["B"].append((pi + 1, "%s|%s" % (w1, w2)))
        # C: geniş boşluk
        for (y, x0, x1, t, f, s, sp, bn) in L:
            if "Serif" not in f:
                continue
            ws = page.get_text("words", clip=fitz.Rect(x0, y, x1, y + s))
            ws = [w for w in ws if abs(w[1] - y) < s]
            ws.sort(key=lambda w: w[0])
            for w, w2 in zip(ws, ws[1:]):
                if w2[0] - w[2] > 3.2 * s:
                    res["C"].append((pi + 1, t.strip()[:70]))
                    break
        # D: boş sayfa (son 2 sayfa ve ilk sayfa hariç)
        if 0 < pi < n - 2 and L is not None:
            blocks = [b for b in page.get_text("dict")["blocks"]]
            if blocks:
                bottom = max(b["bbox"][3] for b in blocks)
                h = page.rect.height
                # altbilgi (sayfa no) hariç gövde alanı ~ 0.08h..0.88h
                body_bottom = max((b["bbox"][3] for b in blocks
                                   if b["bbox"][3] < 0.9 * h), default=0)
                if body_bottom and (0.88 * h - body_bottom) / (0.8 * h) > 0.55:
                    nxt = doc[pi + 1].get_text().strip().split("\n")[:2]
                    res["D"].append((pi + 1, " / ".join(nxt)[:70]))
        # E: sayfa başında yetim şekil açıklaması
        head = [l for l in L if l[0] < page.rect.height * 0.2]
        if head and re.match(r"Şekil \d+\.\d+:", head[0][3].strip()):
            res["E"].append((pi + 1, head[0][3].strip()[:60]))
    return n, res


def build_vocab():
    v = set()
    for p in glob.glob(os.path.join(ROOT, "bolumler", "bolum_*.md")):
        for w in WORD.findall(open(p, encoding="utf-8").read()):
            v.add(w.lower())
    return v


def main(args):
    pdfs = sorted(glob.glob(os.path.join(ROOT, "pdf", "bolum_*.pdf")))
    if args:
        want = {"%02d" % int(a) for a in args}
        pdfs = [p for p in pdfs if os.path.basename(p)[6:8] in want]
    vocab = build_vocab()
    total = Counter()
    rapor = []
    for p in pdfs:
        n, res = scan(p, vocab)
        c = {k: len(v) for k, v in res.items()}
        total.update(c)
        name = os.path.basename(p)[:8]
        if c:
            print(name, n, "s", " ".join("%s=%d" % kv for kv in sorted(c.items())))
        for k in sorted(res):
            for pg, ctx in res[k]:
                rapor.append("%s s%-3d %s  %s" % (name, pg, k, ctx))
    with open(os.path.join(ROOT, "build", "print_rapor.txt"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(rapor))
    print("TOPLAM", dict(total))


if __name__ == "__main__":
    main(sys.argv[1:])
