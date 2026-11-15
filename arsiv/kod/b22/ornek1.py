# ornek1.py: komut yiginleriyle geri al / yinele izi (Ornek 1)
from komut import Editor, ekle, sil


def yaz(ad, ed):
    print("%-9s metin=%-15r geri=%d ileri=%d"
          % (ad, ed.metin, len(ed._geri), len(ed._ileri)))


if __name__ == "__main__":
    ed = Editor()
    ed.yap(ekle(ed, "Merhaba"))
    yaz("ekle", ed)
    ed.yap(ekle(ed, " dunya"))
    yaz("ekle", ed)
    ed.yap(sil(ed, 5))
    yaz("sil 5", ed)
    ed.geri()
    yaz("geri", ed)
    ed.geri()
    yaz("geri", ed)
    ed.yinele()
    yaz("yinele", ed)
    ed.yap(ekle(ed, "!"))
    yaz("ekle", ed)
    print("yinele ->", ed.yinele())
    yaz("son", ed)
    assert ed.metin == "Merhaba dunya!"
