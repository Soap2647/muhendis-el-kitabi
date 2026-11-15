# -*- coding: utf-8 -*-
"""Mini dili: sözcüksel çözümleme ve AST düğümleri."""
import re
from dataclasses import dataclass


class HataDerleme(Exception):
    """Derleme hatasi: konum (satir, sutun) tasir."""

    def __init__(self, mesaj, satir, sutun):
        super().__init__(f"{satir}:{sutun}  {mesaj}")
        self.satir = satir
        self.sutun = sutun


ANAHTAR = {"let", "fn", "if", "else", "while", "return",
           "print", "true", "false"}
DESEN = re.compile(r"""
    (?P<bos>[ \t\r]+)
  | (?P<yeni>\n)
  | (?P<sayı>\d+)
  | (?P<kimlik>[A-Za-z_]\w*)
  | (?P<op>==|!=|<=|>=|[-+*/%<>=(){};,])
""", re.VERBOSE)


@dataclass
class Tok:
    tur: str        # "let", "SAYI", "KIMLIK", "==", "EOF", ...
    lexem: str
    satir: int
    sutun: int


def tokenize(kaynak):
    toks, satir, bas, i = [], 1, 0, 0
    while i < len(kaynak):
        m = DESEN.match(kaynak, i)
        if m is None:
            raise HataDerleme(f"tanınmayan karakter {kaynak[i]!r}",
                              satir, i - bas + 1)
        grup, metin = m.lastgroup, m.group()
        sut = i - bas + 1
        if grup == "yeni":
            satir, bas = satir + 1, m.end()
        elif grup == "bos":
            pass
        elif grup == "kimlik" and metin in ANAHTAR:
            toks.append(Tok(metin, metin, satir, sut))
        elif grup == "kimlik":
            toks.append(Tok("KIMLIK", metin, satir, sut))
        elif grup == "sayı":
            toks.append(Tok("SAYI", metin, satir, sut))
        else:
            toks.append(Tok(metin, metin, satir, sut))
        i = m.end()
    toks.append(Tok("EOF", "", satir, i - bas + 1))
    return toks


# ---------------- AST ----------------
# Her dugum, kaynak konumu (satir, sutun) tasir. Yorum: Turkce adlar
@dataclass
class Sayi:          # tam sayi ve dogru/yanlis sabitleri
    deger: object; satir: int = 0; sutun: int = 0

@dataclass
class Degisken:      # slot: analizci doldurur
    ad: str; satir: int = 0; sutun: int = 0; slot: int = -1

@dataclass
class Ikili:         # a op b
    op: str; sol: object; sag: object; satir: int = 0; sutun: int = 0

@dataclass
class Tekli:         # -a
    op: str; ey: object; satir: int = 0; sutun: int = 0

@dataclass
class Cagri:         # f(a, b)
    ad: str; args: list; satir: int = 0; sutun: int = 0

@dataclass
class Let:           # let x = e;
    ad: str; ifade: object
    satir: int = 0; sutun: int = 0; slot: int = -1

@dataclass
class Ata:           # x = e;
    ad: str; ifade: object
    satir: int = 0; sutun: int = 0; slot: int = -1

@dataclass
class Yaz:           # print e;
    ifade: object

@dataclass
class Eger:          # if (k) {..} else {..}
    kosul: object; dal: list; dal_degil: list

@dataclass
class Dongu:         # while (k) {..}
    kosul: object; govde: list

@dataclass
class Don:           # return e;
    ifade: object; satir: int = 0; sutun: int = 0

@dataclass
class Fonksiyon:     # fn ad(p...) {..}
    ad: str; params: list; govde: list
    satir: int = 0; sutun: int = 0; nlocals: int = 0

@dataclass
class Ifade:         # e;  (yalniz yan etki icin)
    ifade: object
