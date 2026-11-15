# -*- coding: utf-8 -*-
"""
Mühendis El Kitabı — PDF üretim motoru (v2, "yayınevi" tasarımı).

Tasarım dili: klasik teknik basım. Siyaha yakın metin, TEK vurgu rengi
(bordo), köşesiz sessiz kutular, booktabs tablolar, cömert beyaz alan.
Renk cümbüşü ve yuvarlak köşeli "slayt" görünümü bilinçli olarak yok.

Kompozisyon garantileri (motora gömülü):
  - Paragraf ve kod bloğu sayfa arasında bölünmez.
  - Başlık, ardındaki ilk içerik bloğundan kopamaz (keep-with-next) ve
    sayfanın dibinde başlayamaz (bölüm başına asgari alan şartı).
  - Şekil ile açıklaması aynı sayfada kalır.
  - İçerik, üst/alt bilgi bandına asla taşamaz.
  - Türkçe heceleme (soft-hyphen) ile iki yana yaslı metinde düzgün satır sonları.
"""
import os
import re as _re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Image, Flowable, PageBreak, CondPageBreak, HRFlowable,
)

# --------------------------------------------------------------------------- #
#  Yollar
# --------------------------------------------------------------------------- #
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")

# --------------------------------------------------------------------------- #
#  Palet — sıcak siyah + tek bordo vurgu + sıcak griler
# --------------------------------------------------------------------------- #
INK       = colors.HexColor("#1F1F1D")   # gövde metni (sıcak siyah)
DARK      = colors.HexColor("#4A463F")   # koyu gri (tablo çizgileri, şekil no)
MUTED     = colors.HexColor("#75716A")   # ikincil metin, üst/alt bilgi
FAINT     = colors.HexColor("#A8A29A")   # satır numarası, en silik
ACCENT    = colors.HexColor("#8A2D2B")   # bordo — TEK vurgu rengi
RULE      = colors.HexColor("#D8D4CC")   # ince çizgiler
RULE_DARK = colors.HexColor("#B9B4AA")

PAPER     = colors.HexColor("#F7F6F2")   # kod/kutu zemini (sıcak kâğıt)
CODE_BORD = colors.HexColor("#DBD7CF")

TERM_BG   = colors.HexColor("#1A1C20")
TERM_TX   = colors.HexColor("#D9D9D2")
TERM_DIM  = colors.HexColor("#8F949B")

INLINE_CODE = colors.HexColor("#8A2D2B")   # satır içi kod — vurguyla aynı aile

# Çağrı kutuları: hepsi aynı sessiz zemin; tür yalnız sol çizgi + etiket
# rengiyle ayrılır (bastırılmış, "kitap" tonları).
BOX = {
    "DIKKAT":   (PAPER, colors.HexColor("#8A2D2B"), "⚠", "DİKKAT"),
    "IPUCU":    (PAPER, colors.HexColor("#47624A"), "✦", "İPUCU"),
    "BAGLANTI": (PAPER, colors.HexColor("#3E566B"), "→", "BAĞLANTI"),
    "NOT":      (PAPER, colors.HexColor("#8A6B2D"), "✎", "NOT"),
    "MULAKAT":  (PAPER, colors.HexColor("#5C4A6E"), "★", "MÜLAKAT KÖŞESİ"),
}

# Söz dizimi renkleri (bastırılmış)
SYN_KW   = colors.HexColor("#2E4E7E")
SYN_STR  = colors.HexColor("#40684A")
SYN_COM  = colors.HexColor("#948E83")
SYN_NUM  = colors.HexColor("#35589A")
SYN_PRE  = colors.HexColor("#7A5230")
SYN_TYPE = colors.HexColor("#5B3A78")

# --------------------------------------------------------------------------- #
#  Font kaydı
# --------------------------------------------------------------------------- #
_FONTS_READY = False

def register_fonts():
    global _FONTS_READY
    if _FONTS_READY:
        return
    reg = [
        ("Serif",        "DejaVuSerif.ttf"),
        ("Serif-Bold",   "DejaVuSerif-Bold.ttf"),
        ("Serif-It",     "DejaVuSerif-Italic.ttf"),
        ("Serif-BoldIt", "DejaVuSerif-BoldItalic.ttf"),
        ("Sans",         "DejaVuSans.ttf"),
        ("Sans-Bold",    "DejaVuSans-Bold.ttf"),
        ("Sans-It",      "DejaVuSans-Oblique.ttf"),
        ("Sans-BoldIt",  "DejaVuSans-BoldOblique.ttf"),
        ("Mono",         "DejaVuSansMono.ttf"),
        ("Mono-Bold",    "DejaVuSansMono-Bold.ttf"),
        ("Mono-It",      "DejaVuSansMono-Oblique.ttf"),
        ("Mono-BoldIt",  "DejaVuSansMono-BoldOblique.ttf"),
    ]
    for name, fn in reg:
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fn)))
    pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold",
                                  italic="Serif-It", boldItalic="Serif-BoldIt")
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold",
                                  italic="Sans-It", boldItalic="Sans-BoldIt")
    pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold",
                                  italic="Mono-It", boldItalic="Mono-BoldIt")
    _FONTS_READY = True

# --------------------------------------------------------------------------- #
#  Türkçe yardımcılar
# --------------------------------------------------------------------------- #
# Başlıklarda geçen İngilizce terimler: bunlarda i→I (İ değil).
_EN_WORDS = set("""
dynamic programming recursion backtracking linked list hash table tree
graph stack queue array sorting design patterns pattern clean code thread
process file system socket api docker deployment bare metal bare-metal edge
tinyml pipeline transformer transformers generative llm rl mlops pytorch
cnn rnn lstm gru nlp oop solid git dsp nosql sql http dns dhcp tcp ip osi
divide conquer greedy master theorem big binary search heap trie dijkstra
kernel svm ensemble self-supervised supervised attention diffusion gpu
cuda engine machine learning deep neural network networks embedded
interrupt timer debugging debug clean architecture test testing driven
""".split())

def tr_upper(s):
    """Türkçe'ye doğru büyük harf: i→İ, ı→I. İngilizce terimler
    (_EN_WORDS) olağan büyük harfe çevrilir: 'Dynamic' → 'DYNAMIC'."""
    def up(m):
        w = m.group(0)
        if w.lower() in _EN_WORDS:
            return w.upper()
        return w.replace("i", "İ").replace("ı", "I").upper()
    return _re.sub(r"[^\s&·/,()]+", up, s)

_VOWELS = set("aeıioöuüAEIİOÖUÜâîûÂÎÛ")
_WORD_RE = _re.compile(r"[A-Za-zçğıöşüÇĞİÖŞÜâîûÂÎÛ]{8,}")
SHY = "­"   # soft hyphen

def _tr_syllable_breaks(word):
    """Türkçe hece sınırları: ünlüler arası ünsüz kümesinde son ünsüzden
    önce bölünür (a-ra-ba, an-la, Türk-çe); bitişik ünlüler arada (sa-at)."""
    idx = [i for i, c in enumerate(word) if c in _VOWELS]
    if len(idx) < 2:
        return []
    breaks = []
    for a, b in zip(idx, idx[1:]):
        gap = b - a - 1
        breaks.append(b if gap == 0 else b - 1)
    return breaks

def tr_hyphenate_word(word):
    """Kelimeye soft-hyphen yerleştirir (baş/son 2 karakter korunur)."""
    breaks = _tr_syllable_breaks(word)
    if not breaks:
        return word
    out, prev = [], 0
    for br in breaks:
        if br >= 2 and (len(word) - br) >= 2 and (br - prev) >= 1:
            out.append(word[prev:br]); prev = br
    out.append(word[prev:])
    return SHY.join(out) if len(out) > 1 else word

def hyphenate_text(t):
    """Metindeki uzun (≥8) saf-harf kelimelere soft-hyphen ekler."""
    return _WORD_RE.sub(lambda m: tr_hyphenate_word(m.group()), t)

# --------------------------------------------------------------------------- #
#  Stiller
# --------------------------------------------------------------------------- #
def build_styles():
    register_fonts()
    S = {}
    # Tipografi, kitap spesifikasyonuna göre: gövde 12pt serif, kod 10'a
    # yakın mono. (Daha küçük punto denendi; Mert 12pt sözleşmesini istiyor.)
    S["body"] = ParagraphStyle(
        "body", fontName="Serif", fontSize=12, leading=17.2, textColor=INK,
        alignment=TA_JUSTIFY, spaceAfter=7)
    S["body_first"] = ParagraphStyle("body_first", parent=S["body"])
    S["h1"] = ParagraphStyle(
        "h1", fontName="Sans-Bold", fontSize=21, leading=25, textColor=INK,
        spaceBefore=4, spaceAfter=10)
    S["h2"] = ParagraphStyle(
        "h2", fontName="Sans-Bold", fontSize=15.4, leading=19, textColor=INK,
        spaceBefore=18, spaceAfter=3.5)
    S["h3"] = ParagraphStyle(
        "h3", fontName="Sans-Bold", fontSize=12.9, leading=16.2, textColor=INK,
        spaceBefore=13, spaceAfter=4)
    S["h4"] = ParagraphStyle(
        "h4", fontName="Serif-Bold", fontSize=11.8, leading=15.6, textColor=INK,
        spaceBefore=10, spaceAfter=3)
    S["caption"] = ParagraphStyle(
        "caption", fontName="Sans", fontSize=9.2, leading=12.8, textColor=MUTED,
        alignment=TA_CENTER, spaceBefore=5, spaceAfter=2)
    S["code"] = ParagraphStyle(
        "code", fontName="Mono", fontSize=9.6, leading=13.5, textColor=INK)
    S["gutter"] = ParagraphStyle(
        "gutter", fontName="Mono", fontSize=8.8, leading=13.5, textColor=FAINT,
        alignment=TA_RIGHT)
    S["term"] = ParagraphStyle(
        "term", fontName="Mono", fontSize=9.6, leading=13.7, textColor=TERM_TX)
    S["callout"] = ParagraphStyle(
        "callout", fontName="Serif", fontSize=11, leading=15.6, textColor=INK)
    S["callout_item"] = ParagraphStyle(
        "callout_item", parent=S["callout"], leftIndent=16, bulletIndent=0,
        bulletFontName="Serif", bulletFontSize=11)
    S["callout_title"] = ParagraphStyle(
        "callout_title", fontName="Sans-Bold", fontSize=9.4, leading=12.2)
    S["bullet"] = ParagraphStyle(
        "bullet", parent=S["body"], leftIndent=15, bulletIndent=3, spaceAfter=3,
        alignment=TA_LEFT)
    S["list_num"] = ParagraphStyle(
        "list_num", parent=S["body"], leftIndent=19, bulletIndent=3, spaceAfter=3,
        alignment=TA_LEFT)
    S["kicker"] = ParagraphStyle(
        "kicker", fontName="Sans", fontSize=9.2, leading=12.2, textColor=MUTED)
    S["chap_label"] = ParagraphStyle(
        "chap_label", fontName="Sans-Bold", fontSize=10.5, leading=13,
        textColor=ACCENT, spaceBefore=16)
    S["chap_title"] = ParagraphStyle(
        "chap_title", fontName="Sans-Bold", fontSize=25, leading=29.5,
        textColor=INK, spaceBefore=3)
    # eski anahtarlar (geriye dönük uyumluluk)
    S["chap_num"] = S["chap_label"]
    S["part_kicker"] = ParagraphStyle(
        "part_kicker", fontName="Sans", fontSize=10.5, leading=14, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=4)
    S["part_num"] = ParagraphStyle(
        "part_num", fontName="Sans-Bold", fontSize=84, leading=88, textColor=ACCENT,
        alignment=TA_CENTER)
    S["part_title"] = ParagraphStyle(
        "part_title", fontName="Sans-Bold", fontSize=23, leading=28, textColor=INK,
        alignment=TA_CENTER, spaceBefore=10)
    S["table_cell"] = ParagraphStyle(
        "table_cell", fontName="Serif", fontSize=10.4, leading=13.8, textColor=INK)
    S["table_head"] = ParagraphStyle(
        "table_head", fontName="Sans-Bold", fontSize=9.9, leading=13,
        textColor=INK)
    return S

# --------------------------------------------------------------------------- #
#  Metin kaçışı ve satır içi biçimleme
# --------------------------------------------------------------------------- #
# DejaVu'da bulunmayan yaygın emojiler -> güvenli tek-renkli glyph
_EMOJI_MAP = {
    "⭐": "★", "\U0001f31f": "★",
    "✅": "✓", "☑": "✓", "✔": "✓",
    "❌": "✗", "✖": "✗",
    "\U0001f4a1": "✦",
    "\U0001f517": "→", "\U0001f449": "→",
    "\U0001f4dd": "✎", "✏": "✎",
    "\U0001f9e9": "★",
    "\U0001f680": "»", "\U0001f4cc": "•",
    "\U0001f3af": "◎", "\U0001f525": "‼",
}
_STRIP = {0xFE0F, 0xFE0E, 0x200D, 0x20E3}

def sanitize(t):
    if not t:
        return t
    out = []
    for ch in t:
        if ord(ch) in _STRIP:
            continue
        out.append(_EMOJI_MAP.get(ch, ch))
    return "".join(out)

def esc(t):
    t = sanitize(t)
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

_INLINE_CODE = _re.compile(r"`([^`]+)`")
_BOLD = _re.compile(r"\*\*([^*]+)\*\*")
_ITAL = _re.compile(r"(?<![\*\w])\*([^*\n]+)\*(?!\*)")

# DejaVu Serif'te olmayan semboller — gövdede Sans'a sarılır (tofu önlemi)
_SANS_SYMBOLS = "★☆✓✗✘⚠✦✎‼◎▲▸▶◀◆●▪♦§⇒"

def _serif_eksik_kumesi():
    """DejaVu Serif'te glifi olmayan ama Sans'ta olan karakterler.
    Gövde metninde bunlar otomatik Sans'a sarılır (kutu/tofu çıkmaz)."""
    try:
        from fontTools.ttLib import TTFont
        _d = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "fonts")
        serif = set(TTFont(os.path.join(_d, "DejaVuSerif.ttf"))
                    .getBestCmap())
        sans = set(TTFont(os.path.join(_d, "DejaVuSans.ttf"))
                   .getBestCmap())
        return serif, sans
    except Exception:
        return None, None

_SERIF_CMAP, _SANS_CMAP = _serif_eksik_kumesi()

def _wrap_symbols(s):
    if _SERIF_CMAP is None:                 # fontTools yoksa eski liste
        for ch in _SANS_SYMBOLS:
            if ch in s:
                s = s.replace(ch, '<font face="Sans">%s</font>' % ch)
        return s
    out = []
    for ch in s:
        o = ord(ch)
        if o > 127 and o not in _SERIF_CMAP and o in _SANS_CMAP:
            out.append('<font face="Sans">%s</font>' % ch)
        else:
            out.append(ch)
    return "".join(out)

# reportlab kusuru: soft-hyphen içeren kelime + boşluk + AÇILIŞ tag'i
# dizilişinde aradaki boşluk yutulur. Çare: açılış tag'inden hemen önceki
# kelimenin soft-hyphen'lerini kaldır (yalnız o kelime hecelemesiz kalır).
_SHY_BEFORE_TAG = _re.compile("([^\\s<>]*" + SHY + "[^\\s<>]*)(?=\\s+<)")

def _fix_shy_tag_boundary(markup):
    return _SHY_BEFORE_TAG.sub(lambda m: m.group(1).replace(SHY, ""), markup)

_CODE_PH = _re.compile("\x01(\\d+)\x02")

# Düz metin matematikteki alt/üst indisler: x_{t−1}, g_k, e^{z}, 2^10.
# Kod parçaları bu noktada yer tutucudadır, onlara dokunulmaz.
_LET = "A-Za-zα-ωΑ-Ωθλμσπ"
_SUB_BRACE = _re.compile(r"(?<=[%s0-9)\]'*̀-ͯ])_\{([^{}\n]{1,24})\}" % _LET)
_SUP_BRACE = _re.compile(r"(?<=[%s0-9)\]'*])\^\{([^{}\n]{1,24})\}" % _LET)
_SUB_ONE = _re.compile(r"(?<![\w_])([%s][̀-ͯ]?)_([A-Za-z0-9α-ω]{1,3})(?![\w])"
                       % _LET)
_SUP_ONE = _re.compile(r"(?<=[%s0-9)])\^(−?-?[0-9]{1,3}|[A-Za-zα-ω])(?![\w])"
                       % _LET)


def _mark_scripts(t):
    t = _SUB_BRACE.sub(lambda m: "\x03%s\x04" % m.group(1), t)
    t = _SUP_BRACE.sub(lambda m: "\x05%s\x06" % m.group(1), t)
    t = _SUB_ONE.sub(lambda m: "%s\x03%s\x04" % (m.group(1), m.group(2)), t)
    t = _SUP_ONE.sub(lambda m: "\x05%s\x06" % m.group(1), t)
    return t


def inline(t, hyphen=True):
    """Markdown satır içi -> reportlab markup.

    `kod` parçaları önce yer tutucuya alınır; kalın/italik/heceleme TAM metin
    üzerinde çalışır (böylece **kalın içinde `kod`** olsa da ** çifti eşleşir);
    en sonda kod parçaları Mono <font> olarak geri konur."""
    codes = []
    def stash(m):
        codes.append(m.group(1))
        return "\x01%d\x02" % (len(codes) - 1)
    t = _INLINE_CODE.sub(stash, t)
    t = _mark_scripts(t)
    if hyphen:
        t = hyphenate_text(t)
    t = esc(t)
    t = (t.replace("\x03", "<sub>").replace("\x04", "</sub>")
          .replace("\x05", "<super>").replace("\x06", "</super>"))
    t = _BOLD.sub(r"<b>\1</b>", t)
    t = _ITAL.sub(r"<i>\1</i>", t)
    t = _wrap_symbols(t)
    def unstash(m):
        seg = codes[int(m.group(1))]
        body = esc(seg)
        if len(seg) <= 18:          # kısa ifade satır sonunda bölünmesin
            body = body.replace(" ", "\u00a0")
        return ('<font face="Mono" size="10.3" color="%s">%s</font>'
                % (INLINE_CODE.hexval(), body))
    t = _CODE_PH.sub(unstash, t)
    return _fix_shy_tag_boundary(t)

# --------------------------------------------------------------------------- #
#  Basit syntax highlight (C / C++ / Python / bash)
# --------------------------------------------------------------------------- #
_KEYWORDS = {
    "c": set("auto break case char const continue default do double else enum extern "
             "float for goto if int long register return short signed sizeof static "
             "struct switch typedef union unsigned void volatile while include define "
             "NULL".split()),
    "cpp": set("auto break case catch char class const constexpr continue default delete "
               "do double else enum explicit extern float for friend goto if inline int "
               "long namespace new operator private protected public return short signed "
               "sizeof static struct switch template this throw try typedef typename union "
               "unsigned using virtual void volatile while bool true false nullptr".split()),
    "python": set("and as assert async await break class continue def del elif else except "
                  "finally for from global if import in is lambda nonlocal not or pass raise "
                  "return try while with yield True False None self".split()),
    "bash": set("if then else elif fi for while do done case esac function in return echo "
                "export local read cd".split()),
}
_TYPES = set("int char float double void long short unsigned signed size_t uint8_t uint16_t "
             "uint32_t uint64_t int8_t int16_t int32_t int64_t bool struct FILE".split())

_TOKEN = _re.compile(r"""
    (?P<com>//[^\n]*|\#[^\n]*)                 |
    (?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*') |
    (?P<num>\b\d+\.?\d*\b)                      |
    (?P<pre>^\s*\#\s*\w+)                       |
    (?P<id>[A-Za-z_]\w*)                        |
    (?P<ws>\s+)                                 |
    (?P<other>.)
""", _re.VERBOSE)

def _color_span(txt, col):
    return '<font color="%s">%s</font>' % (col.hexval(), txt)

def highlight_line(line, lang):
    lang = (lang or "").lower()
    if lang in ("c++", "cxx", "hpp", "cc"):
        lang = "cpp"
    if lang in ("py",):
        lang = "python"
    if lang in ("sh", "shell", "console"):
        lang = "bash"
    kw = _KEYWORDS.get(lang, set())

    def sp(s):
        return esc(s).replace(" ", "&nbsp;")

    out = []
    for m in _TOKEN.finditer(line):
        k = m.lastgroup
        v = m.group()
        if k == "com":
            out.append(_color_span(sp(v), SYN_COM)); continue
        if k == "pre":
            out.append(_color_span(sp(v), SYN_PRE)); continue
        if k == "str":
            out.append(_color_span(sp(v), SYN_STR)); continue
        if k == "num":
            out.append(_color_span(sp(v), SYN_NUM)); continue
        if k == "id":
            if v in kw:
                out.append(_color_span(sp(v), SYN_KW))
            elif v in _TYPES:
                out.append(_color_span(sp(v), SYN_TYPE))
            else:
                out.append(sp(v))
            continue
        if k == "ws":
            out.append(v.replace(" ", "&nbsp;").replace("\t", "&nbsp;"*4)); continue
        out.append(sp(v))
    return "".join(out) if out else "&nbsp;"

# --------------------------------------------------------------------------- #
#  Bileşenler
# --------------------------------------------------------------------------- #
class CodeTable(Table):
    """Kod kartı tablosu: sayfa sonunda bölünürse her parçada en az
    MIN_SATIR satır kalır (tek satırlık 'yetim' kod parçası olmaz)."""
    MIN_SATIR = 6

    def split(self, availWidth, availHeight):
        parts = Table.split(self, availWidth, availHeight)
        if len(parts) < 2:
            return parts
        n = len(self._cellvalues)
        n0 = len(parts[0]._cellvalues)
        if n0 < self.MIN_SATIR:
            return []                      # tümünü sonraki sayfaya it
        if n - n0 < self.MIN_SATIR:
            hedef = n - self.MIN_SATIR     # ilk parçaya düşecek satır
            if hedef < self.MIN_SATIR:
                return []
            h = sum(self._rowHeights[:hedef]) + 0.5
            parts = Table.split(self, availWidth, h)
        return parts


def code_card(code, lang="", S=None, show_lines=True, keep=True):
    """Satır numaralı kod kartı — köşesiz, kâğıt zemin, ince çerçeve."""
    S = S or build_styles()
    lines = code.rstrip("\n").split("\n")
    rows = []
    for i, ln in enumerate(lines, 1):
        code_par = Paragraph(highlight_line(ln, lang), S["code"])
        if show_lines:
            rows.append([Paragraph(str(i), S["gutter"]), code_par])
        else:
            rows.append([code_par])
    if show_lines:
        tbl = CodeTable(rows, colWidths=[24, None], hAlign="LEFT")
        style = [
            ("BACKGROUND", (0, 0), (-1, -1), PAPER),
            ("BOX", (0, 0), (-1, -1), 0.5, CODE_BORD),
            ("LINEAFTER", (0, 0), (0, -1), 0.5, CODE_BORD),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, -1), 3),
            ("RIGHTPADDING", (0, 0), (0, -1), 5),
            ("LEFTPADDING", (1, 0), (1, -1), 8),
            ("RIGHTPADDING", (1, 0), (1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 1.1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.1),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
        ]
    else:
        tbl = CodeTable(rows, colWidths=[None], hAlign="LEFT")
        style = [
            ("BACKGROUND", (0, 0), (-1, -1), PAPER),
            ("BOX", (0, 0), (-1, -1), 0.5, CODE_BORD),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 1.1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.1),
        ]
    tbl.setStyle(TableStyle(style))
    tbl.spaceAfter = 7          # sayfa sonunda kendiliğinden düşer
    block = [tbl]
    # Kısa bloklar bölünmez; uzunlar sayfa sonunda (her parçada >= 6 satır)
    # bölünür. Eskiden 42 satıra kadar her blok bütün tutuluyordu ve bu,
    # sayfaların yarısının boş kalmasına yol açıyordu.
    if keep and len(lines) <= KEEP_MAX_LINES:
        return KeepTogether(block)
    return block

KEEP_MAX_LINES = 12

def terminal_box(text, S=None, keep=True):
    """Koyu terminal kutusu — köşesiz, sade."""
    S = S or build_styles()
    lines = text.rstrip("\n").split("\n")
    rebuilt = []
    for l in lines:
        if l.startswith("$ "):
            rebuilt.append('<font color="%s">$</font>&nbsp;%s'
                           % (TERM_DIM.hexval(), esc(l[2:]).replace(" ", "&nbsp;")))
        elif l.strip() == "":
            rebuilt.append("&nbsp;")
        else:
            rebuilt.append(esc(l).replace(" ", "&nbsp;"))
    if len(rebuilt) <= KEEP_MAX_LINES:
        par = Paragraph("<br/>".join(rebuilt), S["term"])
        tbl = Table([[par]], colWidths=[None], hAlign="LEFT")
        pad = [("TOPPADDING", (0, 0), (-1, -1), 8),
               ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    else:
        # uzun çıktı: satır başına bir satır, sayfa sonunda bölünebilir
        tbl = CodeTable([[Paragraph(r, S["term"])] for r in rebuilt],
                        colWidths=[None], hAlign="LEFT")
        pad = [("TOPPADDING", (0, 0), (-1, -1), 0),
               ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
               ("TOPPADDING", (0, 0), (-1, 0), 8),
               ("BOTTOMPADDING", (0, -1), (-1, -1), 8)]
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TERM_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
    ] + pad))
    tbl.spaceAfter = 7
    block = [tbl]
    if keep and len(rebuilt) <= KEEP_MAX_LINES:
        return KeepTogether(block)
    return block

def callout(kind, text, S=None):
    """Sessiz çağrı kutusu: kâğıt zemin, tür rengi yalnız sol çizgi + etikette."""
    S = S or build_styles()
    bg, tone, symbol, label = BOX.get(kind.upper(), BOX["NOT"])
    title = Paragraph(
        '<font color="%s"><font face="Sans" size="10">%s</font>'
        '&nbsp;&nbsp;<b>%s</b></font>' % (tone.hexval(), esc(symbol), esc(label)),
        S["callout_title"])
    if isinstance(text, str):
        text = [("", text)]
    rows = [[title], [Spacer(1, 3.5)]]
    for k, (mark, t) in enumerate(text):
        if k:
            rows.append([Spacer(1, 3)])
        if mark:
            sym = "•" if mark in "-*•" else mark
            rows.append([Paragraph(inline(t), S["callout_item"],
                                   bulletText=sym)])
        else:
            rows.append([Paragraph(inline(t), S["callout"])])
    inner = Table(rows, colWidths=[None])
    inner.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    outer = Table([[inner]], colWidths=[None], hAlign="LEFT")
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 1.6, tone),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    outer.spaceAfter = 8
    return KeepTogether([outer])

def figure(img_path, caption, S=None, max_w=None):
    """Şekil + açıklama, birlikte tutulur. 'Şekil X.Y:' öneki koyulaştırılır."""
    S = S or build_styles()
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(img_path).getSize()
    avail = max_w or (A4[0] - 3*cm - 2*cm)
    w = min(avail, iw)
    h = w * ih / iw
    max_h = A4[1] - 2.5*cm - 2.5*cm - 3*cm
    if h > max_h:
        h = max_h
        w = h * iw / ih
    img = Image(img_path, width=w, height=h)
    img.hAlign = "CENTER"
    cap_txt = caption
    m = _re.match(r"^(Şekil\s+[\d.]+:)\s*(.*)$", caption)
    if m:
        cap_txt = ('<b><font color="%s">%s</font></b> %s'
                   % (DARK.hexval(), esc(m.group(1)), inline(m.group(2), hyphen=False)))
    else:
        cap_txt = inline(caption, hyphen=False)
    cap_st = ParagraphStyle("caption_son", parent=S["caption"],
                            spaceAfter=9)
    cap = Paragraph(cap_txt, cap_st)
    img.spaceBefore = 4
    return KeepTogether([img, cap])

def rule(width="100%", thickness=0.5, color=RULE, space_before=2, space_after=8,
         h_align="LEFT"):
    return HRFlowable(width=width, thickness=thickness, color=color,
                      spaceBefore=space_before, spaceAfter=space_after,
                      hAlign=h_align)

# --------------------------------------------------------------------------- #
#  Bölüm / Kısım başlıkları
# --------------------------------------------------------------------------- #
def chapter_header(part_label, chap_no, title, S=None):
    """Bölüm açılışı: kısım etiketi, ince çizgi, BÖLÜM N (bordo), büyük başlık,
    kısa kalın bordo bar."""
    S = S or build_styles()
    els = [
        Paragraph(esc(tr_upper(part_label)), S["kicker"]),
        rule(thickness=0.5, color=RULE_DARK, space_before=3, space_after=0),
        Paragraph("BÖLÜM %s" % chap_no, S["chap_label"]),
        Paragraph(esc(title), S["chap_title"]),
        HRFlowable(width="17%", thickness=2.6, color=ACCENT, hAlign="LEFT",
                   spaceBefore=9, spaceAfter=22),
    ]
    return els

def part_divider(part_no, part_title, S=None):
    """Kısım ayraç sayfası (recto), dikey ortalanmış, sade."""
    S = S or build_styles()
    els = [
        Spacer(1, 7.0*cm),
        Paragraph("KISIM", S["part_kicker"]),
        Paragraph(esc(part_no), S["part_num"]),
        Spacer(1, 8),
        HRFlowable(width="12%", thickness=1.0, color=RULE_DARK, hAlign="CENTER",
                   spaceBefore=0, spaceAfter=0),
        Paragraph(esc(part_title), S["part_title"]),
    ]
    return els

# --------------------------------------------------------------------------- #
#  Belge şablonu — aynalı kenar boşlukları, üst bilgi, alt-orta sayfa no
# --------------------------------------------------------------------------- #
TOP_M, BOT_M, INNER_M, OUTER_M = 2.5*cm, 2.5*cm, 3.0*cm, 2.0*cm

class BookDoc(BaseDocTemplate):
    def __init__(self, filename, running_title=None, start_page=1,
                 book_title="Mühendis El Kitabı", chapter_label=None, **kw):
        super().__init__(filename, pagesize=A4,
                         topMargin=TOP_M, bottomMargin=BOT_M,
                         leftMargin=INNER_M, rightMargin=OUTER_M, **kw)
        self.book_title = tr_upper(book_title)
        self.chapter_label = tr_upper(chapter_label or running_title or book_title)
        self._start_page = start_page
        fw = A4[0] - INNER_M - OUTER_M
        fh = A4[1] - TOP_M - BOT_M
        recto = Frame(INNER_M, BOT_M, fw, fh, id="recto",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        verso = Frame(OUTER_M, BOT_M, fw, fh, id="verso",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="recto", frames=[recto], onPage=self._decorate),
            PageTemplate(id="verso", frames=[verso], onPage=self._decorate),
        ])

    def _page_label(self):
        return self._start_page + self.page - 1

    def _decorate(self, canvas, doc):
        canvas.saveState()
        pageno = self._page_label()
        # sayfa numarası — alt orta
        canvas.setFont("Sans", 8.8)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(A4[0] / 2.0, 1.35*cm, str(pageno))
        # üst bilgi (ilk sayfa hariç): harf aralıklı küçük büyük-harf + ince çizgi
        if doc.page > 1:
            is_recto = (pageno % 2 == 1)
            x_in = INNER_M if is_recto else OUTER_M
            x_out = A4[0] - (OUTER_M if is_recto else INNER_M)
            y_text = A4[1] - TOP_M + 0.60*cm
            y_line = A4[1] - TOP_M + 0.40*cm
            canvas.setFont("Sans", 7.2)
            canvas.setFillColor(MUTED)
            if is_recto:
                canvas.drawRightString(x_out, y_text, self.chapter_label,
                                       charSpace=0.7)
            else:
                canvas.drawString(x_in, y_text, self.book_title, charSpace=0.7)
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.4)
            canvas.line(x_in, y_line, x_out, y_line)
        canvas.restoreState()

    def handle_pageBegin(self):
        self._handle_pageBegin()
        pageno = self._page_label()
        self._handle_nextPageTemplate("recto" if pageno % 2 == 1 else "verso")


def build_pdf(filename, story, running_title=None, start_page=1,
              book_title="Mühendis El Kitabı", chapter_label=None):
    register_fonts()
    doc = BookDoc(filename, running_title=running_title, start_page=start_page,
                  book_title=book_title, chapter_label=chapter_label)
    doc.build(story)
    return filename
