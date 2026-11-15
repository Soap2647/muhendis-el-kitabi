# -*- coding: utf-8 -*-
"""Senaryo kopyalarini uretir (once_A1, once_A2, sonra_A, once_B, sonra_B).

Calistirma: python senaryo_uret.py  (kod_b21 klasorunde)
"""
import os
import shutil

KOK = os.path.dirname(os.path.abspath(__file__))
SEN = os.path.join(KOK, "senaryo")


def kopya(kaynak, hedef):
    if os.path.exists(hedef):
        shutil.rmtree(hedef)
    shutil.copytree(os.path.join(KOK, kaynak), hedef,
                    ignore=shutil.ignore_patterns("__pycache__"))


def edit(yol, eski, yeni):
    with open(yol, encoding="utf-8") as f:
        s = f.read()
    assert s.count(eski) == 1, (yol, s.count(eski), eski[:50])
    with open(yol, "w", encoding="utf-8") as f:
        f.write(s.replace(eski, yeni))


def p(*a):
    return os.path.join(SEN, *a)


if __name__ == "__main__":
    os.makedirs(SEN, exist_ok=True)
    # A1: yalnizca uretici degisir (4'lu demet)
    kopya("once", p("once_A1"))
    edit(p("once_A1", "olcum.py"),
         "sonuc.append((tur, deger, birim))",
         "sonuc.append((tur, deger, birim, 1.0))")
    # A2: uretici + tuketici + testler birlikte
    kopya("once", p("once_A2"))
    edit(p("once_A2", "olcum.py"),
         "sonuc.append((tur, deger, birim))",
         "sonuc.append((tur, deger, birim, 1.0))")
    edit(p("once_A2", "rapor.py"), "sayilar = [d for _, d, _ in olcumler]",
         "sayilar = [d for _, d, _, _ in olcumler]")
    edit(p("once_A2", "rapor.py"), "for t, d, b in olcumler]",
         "for t, d, b, _ in olcumler]")
    edit(p("once_A2", "rapor.py"), "for t, d, _ in olcumler",
         "for t, d, _, _ in olcumler")
    edit(p("once_A2", "test_telemetri.py"), "(tur, deger, birim), = ",
         "(tur, deger, birim, _), = ")
    edit(p("once_A2", "test_telemetri.py"), "(_, deger, birim), = ",
         "(_, deger, birim, _), = ")
    # sonra_A: sozlesmeye varsayilanli yeni alan
    kopya("sonra", p("sonra_A"))
    edit(p("sonra_A", "sozlesme.py"), "    esik: float | None = None\n",
         "    esik: float | None = None\n    guven: float = 1.0\n")
    # once_B: basinc turu (3 dosya)
    kopya("once", p("once_B"))
    edit(p("once_B", "olcum.py"),
         "        else:\n            raise ValueError",
         '        elif tur == "basinc":\n'
         '            deger, birim = ham * 0.05, "kPa"\n'
         "        else:\n            raise ValueError")
    edit(p("once_B", "rapor.py"),
         'if t == "termistor" and d > 80.0]',
         'if (t == "termistor" and d > 80.0) or '
         '(t == "basinc" and d > 110.0)]')
    edit(p("once_B", "app.py"),
         'SENSORLER = [("termistor", 1), ("gerilim", 2)]',
         'SENSORLER = [("termistor", 1), ("gerilim", 2), ("basinc", 3)]')
    # sonra_B: yeni dosya + import + yapilandirma
    kopya("sonra", p("sonra_B"))
    shutil.copy(os.path.join(KOK, "sonra_ek", "basinc.py"),
                p("sonra_B", "basinc.py"))
    edit(p("sonra_B", "app.py"),
         "import sensorler  #",
         "import basinc  # noqa: F401\nimport sensorler  #")
    edit(p("sonra_B", "app.py"),
         'YAPILANDIRMA = [("termistor", 1), ("gerilim", 2)]',
         'YAPILANDIRMA = [("termistor", 1), ("gerilim", 2), ("basinc", 3)]')
    print("senaryolar uretildi:", sorted(os.listdir(SEN)))
