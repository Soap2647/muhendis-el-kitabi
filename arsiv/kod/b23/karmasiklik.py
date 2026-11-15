# karmasiklik.py: fonksiyon basina satir, parametre, derinlik, CC
import ast
import sys

KARAR = (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler,
         ast.comprehension, ast.Assert)
DERIN = (ast.If, ast.For, ast.While, ast.With, ast.Try)


def cc_hesapla(dugum):
    """McCabe: 1 + karar noktalari (BoolOp'ta her ek islem +1)."""
    sayi = 1
    for d in ast.walk(dugum):
        if isinstance(d, KARAR):
            sayi += 1
        elif isinstance(d, ast.BoolOp):
            sayi += len(d.values) - 1
    return sayi


def derinlik(dugum, seviye=0):
    en_derin = seviye
    for c in ast.iter_child_nodes(dugum):
        if isinstance(c, DERIN):
            en_derin = max(en_derin, derinlik(c, seviye + 1))
        else:
            en_derin = max(en_derin, derinlik(c, seviye))
    return en_derin


def bilissel_hesapla(dugum, seviye=0):
    """Ic ice yapiyi cezalandiran sayim (bilissel benzeri)."""
    puan = 0
    for c in ast.iter_child_nodes(dugum):
        if isinstance(c, ast.If):
            puan += 1 + seviye
            if c.orelse and not (len(c.orelse) == 1
                                 and isinstance(c.orelse[0], ast.If)):
                puan += 1
            puan += bilissel_hesapla(c, seviye + 1)
        elif isinstance(c, (ast.For, ast.While)):
            puan += 1 + seviye
            puan += bilissel_hesapla(c, seviye + 1)
        elif isinstance(c, ast.BoolOp):
            puan += len(c.values) - 1
            puan += bilissel_hesapla(c, seviye)
        else:
            puan += bilissel_hesapla(c, seviye)
    return puan


def tara(yol):
    with open(yol, encoding="utf-8") as f:
        agac = ast.parse(f.read(), filename=yol)
    sonuc = []
    for d in ast.walk(agac):
        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)):
            satir = d.end_lineno - d.lineno + 1
            param = len(d.args.args) + len(d.args.kwonlyargs)
            sonuc.append((yol, d.name, satir, param,
                          derinlik(d), cc_hesapla(d),
                          bilissel_hesapla(d)))
    return sonuc


if __name__ == "__main__":
    print("%-22s %5s %4s %4s %4s %5s" % ("fonksiyon", "satir", "par",
                                         "der", "cc", "bilis"))
    for yol in sys.argv[1:]:
        for _, ad, s, p, dr, c, b in tara(yol):
            print("%-22s %5d %4d %4d %4d %5d" % (ad, s, p, dr, c, b))
