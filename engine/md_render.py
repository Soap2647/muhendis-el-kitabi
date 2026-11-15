# -*- coding: utf-8 -*-
"""
Markdown süperset -> reportlab story dönüştürücü (v2).

Desteklenen sözdizimi
---------------------
Ön bilgi (dosya başı):
    %% kisim_no: I
    %% kisim_ad: Programlama Temelleri
    %% bolum_no: 1
    %% baslik: Bilgisayar Nasıl Düşünür

Bloklar:
    ## Başlık            -> H2 (bordo bölüm numarası + altında ince çizgi)
    ### Başlık           -> H3
    #### Başlık          -> H4
    ```c ... ```         -> kod kartı; dil: c/cpp/python/bash
    ```term ... ```      -> terminal kutusu ('$ ' komut satırı olur)
    ::: dikkat|ipucu|baglanti|not|mulakat ... :::  -> çağrı kutusu
    ![Şekil 1.1: açıklama](gorseller/x.png)        -> şekil + açıklama
    | a | b |            -> booktabs tablo (ikinci satır |---|---|)
    - madde / 1. madde   -> listeler
    ---                  -> ince yatay çizgi
    <<sayfa>>            -> sayfa atlatma

Kompozisyon kuralları
---------------------
  * Başlıklar keep-with-next: ardındaki ilk içerik bloğuyla tek parça.
  * Başlık öncesi asgari boş alan şartı (CondPageBreak): H2 ~8.5cm,
    H3 ~5.8cm, H4 ~4.2cm, "Çözüm:" gibi etiketler ~3.6cm. Sayfa dibinde
    bölüm başlatılmaz.
  * Gruplar düzleştirilir — iç içe KeepTogether reportlab'da düzeni bozar.
"""
import re
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, CondPageBreak,
)
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth

from kitap_engine import (
    build_styles, inline, esc, code_card, terminal_box, callout, figure, rule,
    chapter_header, ACCENT, DARK, MUTED, RULE, RULE_DARK, A4, INNER_M, OUTER_M,
)

# Başlık seviyesi -> sayfada gereken asgari boş alan (12pt gövdeye göre)
NEED_SPACE = {"h2": 9.5*cm, "h3": 6.8*cm, "h4": 5.0*cm, "label": 4.2*cm}
# Tanıtım paragrafı + bölünebilir bloğun ilk 6 satırı için gereken alan
GLUE_SPLIT_NEED = 7.0*cm

_SECNUM = re.compile(r"^(\d+(?:\.\d+)*)([.)]?\s+)(.*)$")


def _parse_front_matter(lines):
    meta = {}
    i = 0
    while i < len(lines) and lines[i].strip().startswith("%%"):
        m = re.match(r"%%\s*([\w]+)\s*:\s*(.*)$", lines[i].strip())
        if m:
            meta[m.group(1)] = m.group(2).strip()
        i += 1
    return meta, i


def _heading_markup(text, accent_hex):
    """Başlıktaki '1.2' gibi bölüm numarasını bordoya boyar."""
    m = _SECNUM.match(text)
    if m:
        return ('<font color="%s">%s</font>%s%s'
                % (accent_hex, esc(m.group(1)), m.group(2),
                   inline(m.group(3), hyphen=False)))
    return inline(text, hyphen=False)


_CELL_PAD = 10 + 2          # sol+sağ dolgu (5+5) + yuvarlama payı
TABLE_WARNINGS = []         # sığdırılamayan tablolar (derleme sonunda raporlanır)


def _cell_widths(text, font, size, code_size):
    """Hücre metni için (en uzun bölünmez parçanın genişliği, tek satır
    genişliği). `kod` parçaları Mono ile ölçülür; uzun kod ifadeleri (dosya
    yolu gibi) "/" noktalarında bölünebilir sayılır."""
    bold = font if font.endswith("-Bold") else font + "-Bold"
    longest = full = 0.0
    for seg in re.split(r"(`[^`]+`)", text):
        if not seg:
            continue
        if seg.startswith("`"):
            body = seg[1:-1]
            f, s = "Mono", code_size
            words = body.split() if len(body) > 18 else [body]
            words = [p for w in words for p in re.split(r"(?<=/)", w) if p]
            full += stringWidth(body, f, s)
        else:
            f, s = (bold if "**" in seg else font), size
            words = re.sub(r"[*]", "", seg).split()
            full += stringWidth(re.sub(r"[*]", "", seg), f, s)
        for w in words:
            longest = max(longest, stringWidth(w, f, s))
    return longest, full


def _table_widths(rows, S, scale):
    """Verilen yazı ölçeğinde (minw, natw) kolon genişlikleri."""
    ncol = len(rows[0])
    minw = [0.0] * ncol
    natw = [0.0] * ncol
    for ri, r in enumerate(rows):
        st = S["table_head"] if ri == 0 else S["table_cell"]
        for ci in range(ncol):
            c = r[ci] if ci < len(r) else ""
            lw, fw = _cell_widths(c, st.fontName, st.fontSize * scale,
                                  10.3 * scale)
            minw[ci] = max(minw[ci], lw + _CELL_PAD)
            natw[ci] = max(natw[ci], fw + _CELL_PAD)
    minw = [max(m, 1.2*cm) for m in minw]
    natw = [max(n, m) for n, m in zip(natw, minw)]
    return minw, natw


def _scaled(style, scale):
    if scale == 1.0:
        return style
    from reportlab.lib.styles import ParagraphStyle
    return ParagraphStyle(style.name + "_%d" % int(scale * 100), parent=style,
                          fontSize=style.fontSize * scale,
                          leading=style.leading * scale)


def _make_table(rows, S):
    """Booktabs tarzı tablo: dikey çizgi yok, zebra yok; üstte/altta kalın,
    başlık altında ince çizgi.

    Kolon genişliği: her kolon en az, içindeki EN UZUN KELİMEYİ tek satıra
    sığdıracak kadar geniştir (kelime ortadan bölünmez). Kalan alan, tek satır
    doğal genişliğe ne kadar ihtiyaç duyulduğuna göre dağıtılır. En uzun
    kelimeler bile toplam genişliğe sığmıyorsa tablo heceleme ile dizilir
    (kelime tire ile bölünür, harf ortasından değil) ve uyarı kaydedilir."""
    header = rows[0]
    body = rows[1:]
    avail = A4[0] - INNER_M - OUTER_M
    hyphen = False
    # sığmazsa önce yazıyı küçült (%90, %80); heceleme yalnız son çare
    for scale in (1.0, 0.9, 0.8):
        minw, natw = _table_widths(rows, S, scale)
        if sum(minw) <= avail:
            break
    if sum(natw) <= avail:
        # her şey tek satıra sığar: artan alanı orantılı dağıt
        extra = avail - sum(natw)
        widths = [n + extra * n / sum(natw) for n in natw]
    elif sum(minw) <= avail:
        need = [n - m for n, m in zip(natw, minw)]
        extra = avail - sum(minw)
        tot = sum(need) or 1.0
        widths = [m + extra * d / tot for m, d in zip(minw, need)]
    else:
        hyphen = True
        TABLE_WARNINGS.append(" | ".join(h[:20] for h in header))
        widths = [avail * m / sum(minw) for m in minw]
    st_h = _scaled(S["table_head"], scale)
    st_c = _scaled(S["table_cell"], scale)
    code_size = 'size="%.1f"' % (10.3 * scale)

    def par(c, st):
        return Paragraph(inline(c, hyphen=hyphen)
                         .replace('size="10.3"', code_size), st)
    data = [[par(c, st_h) for c in header]]
    for r in body:
        data.append([par(c, st_c) for c in r])
    tbl = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    style = [
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, DARK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, DARK),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, 0), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5.5),
    ]
    tbl.setStyle(TableStyle(style))
    if len(data) <= 10:
        return KeepTogether([Spacer(1, 3), tbl, Spacer(1, 9)])
    return [Spacer(1, 3), tbl, Spacer(1, 9)]


def _flatten(fl):
    """KeepTogether'ları açarak düz flowable listesi döndürür (iç içe
    KeepTogether reportlab'da her grubu ayrı sayfaya iterek düzeni bozar)."""
    if isinstance(fl, KeepTogether):
        inner = getattr(fl, "_content", None) or getattr(fl, "_flowables", [])
        res = []
        for x in inner:
            res.extend(_flatten(x))
        return res
    return [fl]



class ShrinkKeep(KeepTogether):
    """KeepTogether + şekil küçültme: grup bulunduğu sayfaya sığmıyor ama
    içindeki şekil(ler) en fazla %35 küçültülünce sığıyorsa, şekli küçültüp
    grubu bu sayfada bırakır. Böylece "tanıtım paragrafı + büyük şekil"
    bir sonraki sayfaya kaçıp arkasında yarım sayfa boşluk bırakmaz."""
    MIN_SCALE = 0.65

    def split(self, aW, aH):
        from reportlab.platypus import Image
        imgs = [f for f in self._content if isinstance(f, Image)]
        if imgs:
            H = sum(f.wrap(aW, aH)[1] + f.getSpaceBefore()
                    + f.getSpaceAfter() for f in self._content)
            if H > aH:
                ih = sum(f.drawHeight for f in imgs)
                fix = H - ih
                room = aH - fix - 4
                if ih > 0 and room >= self.MIN_SCALE * ih:
                    k = room / ih
                    for f in imgs:
                        f.drawWidth *= k
                        f.drawHeight *= k
                        f._width, f._height = f.drawWidth, f.drawHeight
                    return list(self._content)
        return KeepTogether.split(self, aW, aH)

def apply_keep_with_next(story):
    """`_keep_next` işaretli başlık/etiketleri sonraki ilk içerik bloğuyla tek
    (düz) KeepTogether'da birleştirir ve grubun önüne asgari-alan şartı koyar
    (CondPageBreak). Böylece başlık ne yalnız kalır ne sayfa dibinde başlar."""
    out = []
    i, n = 0, len(story)
    while i < n:
        f = story[i]
        if getattr(f, "_keep_next", False):
            need = getattr(f, "_need_space", NEED_SPACE["h4"])
            group = list(_flatten(f))
            j = i + 1
            while j < n:
                g = story[j]
                need = max(need, getattr(g, "_need_space", 0))
                group.extend(_flatten(g))
                j += 1
                if isinstance(g, Spacer):
                    continue                    # boşlukları yut, içerik ara
                if getattr(g, "_keep_next", False):
                    continue                    # ardışık başlıkları zincirle
                break                           # ilk gerçek içerik eklendi
            out.append(CondPageBreak(need))
            out.append(ShrinkKeep(group))
            i = j
        else:
            out.append(f)
            i += 1
    return out


def render_markdown(md_text, base_dir="", S=None):
    """(meta, story) döndürür. base_dir: görsel yollarının kökü."""
    import os
    S = S or build_styles()
    raw = md_text.replace("\r\n", "\n").split("\n")
    meta, start = _parse_front_matter(raw)
    lines = raw[start:]

    story = []
    if meta.get("bolum_no"):
        part_label = "Kısım %s — %s" % (meta.get("kisim_no", ""), meta.get("kisim_ad", ""))
        story += chapter_header(part_label.strip(" —"), meta["bolum_no"],
                                meta.get("baslik", ""), S)

    i = 0
    n = len(lines)
    para_buf = []

    def emit(x, glue_prev=False):
        """code_card gibi liste de dönebilen bileşenleri güvenle ekle.

        glue_prev: blok KeepTogether boyutundaysa, hemen önceki gövde
        paragrafı bu bloğun tanıtımı sayılır ve blokla birlikte tutulur
        ("Aşağıdaki kod..." deyip kodun sonraki sayfaya kaçması yasak)."""
        if glue_prev and isinstance(x, KeepTogether) and story:
            prev = story[-1]
            if getattr(prev, "_is_para", False):
                prev._keep_next = True
                prev._need_space = max(getattr(prev, "_need_space", 0),
                                       NEED_SPACE["label"])
        elif glue_prev and isinstance(x, list) and story:
            # bölünebilir uzun blok: tanıtım paragrafı + bloğun ilk ~6
            # satırı aynı sayfaya sığmıyorsa paragraf yeni sayfada başlar;
            # blok bütün halinde ileri itilmez (yarım boş sayfa olmaz)
            prev = story[-1]
            if getattr(prev, "_is_para", False):
                story.insert(len(story) - 1, CondPageBreak(GLUE_SPLIT_NEED))
        if isinstance(x, list):
            story.extend(x)
        else:
            story.append(x)

    def flush_para():
        if para_buf:
            txt = " ".join(x.strip() for x in para_buf).strip()
            if txt:
                kt = KeepTogether(Paragraph(inline(txt), S["body"]))
                kt._is_para = True
                # tümü kalın tek etiket satırı (ör. "**Çözüm:**") -> sonrakiyle tut
                if txt.startswith("**") and txt.endswith("**") and txt.count("**") == 2:
                    kt._keep_next = True
                    kt._need_space = NEED_SPACE["label"]
                story.append(kt)
            para_buf.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            flush_para(); i += 1; continue

        if stripped == "<<sayfa>>":
            flush_para(); story.append(PageBreak()); i += 1; continue

        if stripped == "---":
            flush_para(); story.append(rule()); i += 1; continue

        # başlıklar
        m = re.match(r"^(#{2,4})\s+(.*)$", stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            key = {2: "h2", 3: "h3", 4: "h4"}[lvl]
            head = Paragraph(_heading_markup(m.group(2), ACCENT.hexval()), S[key])
            head._keep_next = True
            head._need_space = NEED_SPACE[key]
            story.append(head)
            if key == "h2":
                r = rule(thickness=0.5, color=RULE_DARK, space_before=1.5,
                         space_after=7)
                r._keep_next = True
                story.append(r)
            i += 1; continue

        # kod / terminal blokları
        m = re.match(r"^```(\w*)\s*$", stripped)
        if m:
            flush_para()
            lang = m.group(1).lower()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            code = "\n".join(buf)
            if lang in ("term", "cikti", "output", "console"):
                emit(terminal_box(code, S), glue_prev=True)
            else:
                emit(code_card(code, lang, S), glue_prev=True)
            continue

        # çağrı kutusu
        m = re.match(r"^:::\s*(\w+)\s*$", stripped)
        if m:
            flush_para()
            kind = m.group(1)
            i += 1
            buf = []
            while i < n and lines[i].strip() != ":::":
                buf.append(lines[i]); i += 1
            i += 1
            # bloklara ayır: boş satır paragraf böler; "1." / "-" maddesi
            # yeni madde başlatır; diğer satırlar öncekine eklenir
            blocks = []
            for raw in buf:
                t = raw.strip()
                if not t:
                    blocks.append(None); continue
                mm = re.match(r"^(\d+[.)]|[-*•])\s+(.*)$", t)
                if mm:
                    blocks.append([mm.group(1), mm.group(2)])
                elif blocks and blocks[-1] is not None:
                    blocks[-1][1] += " " + t
                else:
                    blocks.append(["", t])
            blocks = [(m_, t_) for b_ in blocks if b_ for m_, t_ in [b_]]
            emit(callout(kind, blocks, S))
            continue

        # şekil
        m = re.match(r"^!\[(.*?)\]\((.*?)\)\s*$", stripped)
        if m:
            flush_para()
            cap, path = m.group(1), m.group(2)
            full = path if os.path.isabs(path) else os.path.join(base_dir, path)
            emit(figure(full, cap, S), glue_prev=True)
            i += 1; continue

        # tablo
        if stripped.startswith("|") and i+1 < n and re.match(r"^\|[\s:\-\|]+\|\s*$", lines[i+1].strip()):
            flush_para()
            rows = []
            def cells(l):
                return [c.strip() for c in l.strip().strip("|").split("|")]
            rows.append(cells(lines[i])); i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i])); i += 1
            emit(_make_table(rows, S), glue_prev=True)
            continue

        # madde imli liste
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                story.append(Paragraph(inline(item), S["bullet"], bulletText="•"))
                i += 1
            story.append(Spacer(1, 4))
            continue

        # numaralı liste
        if re.match(r"^\d+\.\s+", stripped):
            flush_para()
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                mm = re.match(r"^(\d+)\.\s+(.*)$", lines[i].strip())
                story.append(Paragraph(inline(mm.group(2)), S["list_num"],
                                       bulletText=mm.group(1) + "."))
                i += 1
            story.append(Spacer(1, 4))
            continue

        para_buf.append(line)
        i += 1

    flush_para()
    story = apply_keep_with_next(story)
    return meta, story
