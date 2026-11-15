# -*- coding: utf-8 -*-
"""b32_girdi.py: guvenilmeyen girdiyle bbas etme ornekleri.

Komut enjeksiyonu gosterimi yalnizca zararsiz bir yazdirma komutu
kullanir. Enjeksiyon yukleri 'echo' ile sinirlidir.

Kullanim:
  python b32_girdi.py komut     # liste argumani ve shell=True farki
  python b32_girdi.py yol       # kok dizin denetimi tablosu
  python b32_girdi.py html      # HTML kacisi
  python b32_girdi.py test
"""

import html
import os
import subprocess
import sys
import tempfile

PY = sys.executable
YAZ = "import sys; print(sys.argv[1])"


def komut_liste(girdi):
    """Dogru: arguman listesi; kabuk yorumu yok."""
    s = subprocess.run([PY, "-c", YAZ, girdi],
                       capture_output=True, text=True)
    return s.stdout.strip()


def komut_kabuk(girdi):
    """YANLIS: girdi kabuk komutunun parcasi olur."""
    s = subprocess.run('"%s" -c "%s" %s' % (PY, YAZ, girdi),
                       shell=True, capture_output=True, text=True)
    return s.stdout.strip().splitlines()


def guvenli_yol(kok, istek):
    """Istegi kok dizin altina cozer; kokten cikarsa None doner."""
    if "\x00" in istek:
        return None                       # NUL baytli yol
    kok_gercek = os.path.realpath(kok)    # sembolik baglari da cozer
    aday = os.path.realpath(
        os.path.join(kok_gercek, istek.lstrip("/\\")))
    try:
        ortak = os.path.commonpath([kok_gercek, aday])
    except ValueError:                    # farkli surucu (C: ve D:)
        return None
    if ortak != kok_gercek:
        return None
    return aday


def yol_naif(kok, istek):
    """YANLIS: yalnizca birlestirir; sonuc kokten cikabilir."""
    return os.path.normpath(os.path.join(kok, istek.lstrip("/")))


def html_sayfa(ad):
    return "<p>Merhaba, %s</p>" % html.escape(ad, quote=True)


def komut():
    print("liste biciminde:", komut_liste("merhaba & echo ENJEKTE"))
    print("shell=True    :", komut_kabuk("merhaba & echo ENJEKTE"))


def yol():
    kok = tempfile.mkdtemp(prefix="b32kok_")
    tablo = ["a.txt", "alt/b.txt", "../gizli.txt", "/../gizli.txt",
             "..\\gizli.txt", "C:\\Windows\\win.ini", "a\x00b.txt"]
    print("%-22s %-10s %s" % ("istek", "naif", "guvenli (kokte mi?)"))
    for t in tablo:
        n = yol_naif(kok, t)
        g = guvenli_yol(kok, t)
        durum = "red" if g is None else "kabul"
        naif_kok = os.path.commonpath([os.path.realpath(kok),
                                       os.path.realpath(n)]) == \
            os.path.realpath(kok)
        print("%-22r %-10s %s" % (t,
                                 "kokte" if naif_kok else "KOKTEN",
                                 durum))


def html_goster():
    print(html_sayfa("<script>alert(1)</script>"))
    print(html_sayfa("Ayse & Ali"))


def test():
    hata = 0

    def dogru(ad, kosul):
        nonlocal hata
        print(("GECTI " if kosul else "KALDI ") + ad)
        if not kosul:
            hata += 1

    dogru("liste: girdi tek arguman",
          komut_liste("a & echo X") == "a & echo X")
    dogru("shell=True: enjeksiyon satiri ayri cikti",
          komut_kabuk("a & echo X")[-1] == "X")
    kok = tempfile.mkdtemp(prefix="b32t_")
    dogru("normal yol kabul", guvenli_yol(kok, "a.txt") is not None)
    dogru("../ red", guvenli_yol(kok, "../x") is None)
    dogru("kok ile baslayan mutlak red",
          guvenli_yol(kok, "/../x") is None)
    dogru("NUL bayt red", guvenli_yol(kok, "a\x00b") is None)
    dogru("kok icinde alt dizin kabul",
          guvenli_yol(kok, "alt/x/y.txt") is not None)
    dogru("naif yol kokten cikiyor", not yol_naif(kok, "../x")
          .startswith(os.path.realpath(kok) + os.sep))
    dogru("HTML: script etiketi kacar",
          "&lt;script&gt;" in html_sayfa("<script>"))
    dogru("HTML: tirnak kacar",
          "&quot;" in html_sayfa('"'))
    print("hata sayisi:", hata)
    return hata


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "komut":
        komut()
    elif kip == "yol":
        yol()
    elif kip == "html":
        html_goster()
    elif kip == "test":
        sys.exit(1 if test() else 0)
    else:
        print("kullanim: komut | yol | html | test")
        sys.exit(2)
