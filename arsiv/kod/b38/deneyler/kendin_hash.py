# -*- coding: utf-8 -*-
"""Git nesne hash'lerini git'e sormadan Python'da hesaplar."""
import hashlib
import subprocess


def git(*args):
    sonuc = subprocess.run(["git"] + list(args), check=True,
                           capture_output=True)
    return sonuc.stdout.decode().strip()


def nesne_hash(tur, govde):
    # Başlık "<tür> <boyut>\0", ardından gövde; SHA-1 özeti.
    baslik = b"%s %d\x00" % (tur, len(govde))
    return hashlib.sha1(baslik + govde).hexdigest()


# 1) Blob: dosyanın ham baytları
mat_c = open("mat.c", "rb").read()
blob_c = nesne_hash(b"blob", mat_c)
blob_h = git("hash-object", "mat.h")

# 2) Tree: "<mod> <ad>\0<20 baytlık ham hash>" girdileri
#    Girdiler ada göre sıralanır (git bunu bekler).
girdiler = [
    (b"100644", b"mat.c", bytes.fromhex(blob_c)),
    (b"100644", b"mat.h", bytes.fromhex(blob_h)),
]
girdiler.sort(key=lambda g: g[1])
agac = b"".join(m + b" " + ad + b"\x00" + h
                for m, ad, h in girdiler)
tree = nesne_hash(b"tree", agac)

# 3) Commit: düz metin gövde
kimlik = "Kitap Deneme <deneme@example.com>"
zaman = "1768113000 +0300"   # 2026-01-11 09:30:00 +0300
ebeveyn = "dda4f894a869ae52258f8d7f424747d7835ece42"
govde = ("tree %s\nparent %s\nauthor %s %s\n"
         "committer %s %s\n\nkup eklendi\n"
         % (tree, ebeveyn, kimlik, zaman, kimlik, zaman))
commit = nesne_hash(b"commit", govde.encode())

# Karşılaştırma: Python ile git aynı hash'i üretmeli
for ad, benim, gitin in [
        ("blob", blob_c, git("hash-object", "mat.c")),
        ("tree", tree, git("rev-parse", "main^{tree}")),
        ("commit", commit, git("rev-parse", "main"))]:
    print("%-7s python=%s  git=%s  %s"
          % (ad, benim[:12], gitin[:12],
             "EŞLEŞTİ" if benim == gitin else "FARKLI"))
