"""Küçük bir mutasyon test aracı (Bölüm 39, Örnek 4).

Kullanım:  python mutasyon.py HEDEF.py TESTDOSYASI.py
Her mutant (kaynağa tek bir küçük değişiklik) ayrı bir geçici
dizinde çalıştırılır. Test paketi başarısız olursa mutant
'öldürüldü' sayılır; hepsi geçerse 'hayatta kaldı'.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile

ZITLAR = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
          ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
          ast.Add: ast.Sub, ast.Sub: ast.Add}
BOOL_ZITLAR = {ast.And: ast.Or, ast.Or: ast.And}


def sahalar(agac):
    """Mutasyon yapılabilecek düğümleri sırayla listeler."""
    liste = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Compare):
            for i, op in enumerate(dugum.ops):
                if type(op) in ZITLAR:
                    liste.append(("cmp", dugum, i))
        elif isinstance(dugum, ast.BinOp):
            if type(dugum.op) in ZITLAR:
                liste.append(("bin", dugum, None))
        elif isinstance(dugum, ast.BoolOp):
            if type(dugum.op) in BOOL_ZITLAR:
                liste.append(("bool", dugum, None))
        elif (isinstance(dugum, ast.Constant)
              and type(dugum.value) is int):
            liste.append(("sabit", dugum, None))
    liste.sort(key=lambda s: (s[1].lineno, s[1].col_offset, s[0]))
    return liste


def mutantlar(kaynak):
    """(açıklama, mutant_kaynağı) çiftlerini üretir."""
    ilk = ast.parse(kaynak)
    sayi = len(sahalar(ilk))
    for k in range(sayi):
        agac = ast.parse(kaynak)
        tur, dugum, i = sahalar(agac)[k]
        if tur == "cmp":
            eski = type(dugum.ops[i]).__name__
            dugum.ops[i] = ZITLAR[type(dugum.ops[i])]()
            yeni = type(dugum.ops[i]).__name__
        elif tur == "bin":
            eski = type(dugum.op).__name__
            dugum.op = ZITLAR[type(dugum.op)]()
            yeni = type(dugum.op).__name__
        elif tur == "bool":
            eski = type(dugum.op).__name__
            dugum.op = BOOL_ZITLAR[type(dugum.op)]()
            yeni = type(dugum.op).__name__
        else:
            eski = str(dugum.value)
            dugum.value = dugum.value + 1
            yeni = str(dugum.value)
        ast.fix_missing_locations(agac)
        aciklama = "satır %d: %s -> %s" % (dugum.lineno, eski, yeni)
        yield aciklama, ast.unparse(agac) + "\n"


def calistir(hedef, testdosyasi, zaman_siniri=60):
    """Her mutant için (açıklama, öldü_mü) listesi döndürür."""
    with open(hedef, encoding="utf-8") as f:
        kaynak = f.read()
    sonuc = []
    for aciklama, mutant in mutantlar(kaynak):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, os.path.basename(hedef)), "w",
                      encoding="utf-8") as f:
                f.write(mutant)
            hedef_test = os.path.join(tmp, "test_suite.py")
            shutil.copy(testdosyasi, hedef_test)
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "-x",
                     "--no-header", "-p", "no:cacheprovider"],
                    cwd=tmp, capture_output=True,
                    timeout=zaman_siniri)
                oldu = r.returncode != 0
            except subprocess.TimeoutExpired:
                oldu = True
        sonuc.append((aciklama, oldu))
    return sonuc


if __name__ == "__main__":
    hedef, test = sys.argv[1], sys.argv[2]
    satirlar = calistir(hedef, test)
    for aciklama, oldu in satirlar:
        print("%-28s %s" % (aciklama,
                            "ÖLDÜ" if oldu else "HAYATTA"))
    olen = sum(1 for _, o in satirlar if o)
    print("Toplam: %d, öldürülen: %d, skor: %.1f%%" % (
        len(satirlar), olen, 100.0 * olen / len(satirlar)))
