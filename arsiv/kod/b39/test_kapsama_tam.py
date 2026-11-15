from kapsama_ornek import etiket, ortalama


def test_ortalama_bos():
    assert ortalama([]) == 0.0


def test_ortalama_esit_degerler():
    assert ortalama([2, 2]) == 2


def test_etiket_pozitif():
    assert etiket(5) == "pozitif"


def test_etiket_pozitif_degil():
    assert etiket(-1) == "sifir"
