# -*- coding: utf-8 -*-
"""pre-commit denetimi: sahnelenmiş (indeksteki) içeriğe bakar."""
import re
import subprocess
import sys

SATIR_LIMITI = 80
BUYUK_DOSYA = 1024 * 1024      # 1 MB
METIN = (".py", ".c", ".h", ".md", ".txt", ".cpp")
SIR = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS erişim anahtarı benzeri"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
     "özel anahtar"),
]


def git(*args):
    sonuc = subprocess.run(["git"] + list(args), check=True,
                           capture_output=True)
    return sonuc.stdout


def sahnelenmis_dosyalar():
    cikti = git("diff", "--cached", "--name-only",
                "--diff-filter=ACM")
    return cikti.decode("utf-8").splitlines()


def denetle_dosya(yol):
    hatalar = []
    icerik = git("show", ":" + yol)   # indeksteki bayt dizisi
    if len(icerik) > BUYUK_DOSYA:
        return ["%s: 1 MB'tan büyük (%d bayt)" % (yol, len(icerik))]
    if not yol.endswith(METIN):
        return hatalar
    metin = icerik.decode("utf-8", errors="replace")
    for no, satir in enumerate(metin.splitlines(), 1):
        if len(satir) > SATIR_LIMITI:
            hatalar.append("%s:%d satır %d karakter"
                           % (yol, no, len(satir)))
        for desen, ad in SIR:
            if desen.search(satir):
                hatalar.append("%s:%d olası sır: %s"
                               % (yol, no, ad))
    return hatalar


def main():
    hatalar = []
    for yol in sahnelenmis_dosyalar():
        hatalar += denetle_dosya(yol)
    for h in hatalar:
        print("HATA", h)
    if hatalar:
        print("Commit reddedildi: %d sorun." % len(hatalar))
        return 1
    print("pre-commit: temiz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
