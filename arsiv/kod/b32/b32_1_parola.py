# -*- coding: utf-8 -*-
"""b32_1_parola.py: cig etkisi ve tuzlu KDF ile parola saklama.

Kullanim:
  python b32_1_parola.py cig     # cig etkisi olcumu
  python b32_1_parola.py sure    # hash suresi olcumu (CSV yazar)
  python b32_1_parola.py test    # dogrulama testleri
"""

import hashlib
import hmac
import os
import sys
import time

N, R, P = 2**14, 8, 1          # scrypt maliyet parametreleri
N_MAKS = 2**20                 # kayittan okunan n icin ust sinir
PBKDF2_TUR = 600_000           # PBKDF2-HMAC-SHA256 tur sayisi


def cig_bit(a, b):
    """Iki girdinin SHA-256 ozetleri arasindaki farkli bit sayisi."""
    x = hashlib.sha256(a).digest()
    y = hashlib.sha256(b).digest()
    return sum(bin(p ^ q).count("1") for p, q in zip(x, y))


def cig():
    # Tek bit degisince ozetin yarisi degisir (256/2=128)
    print("girdi                    ozet farki (bit / 256)")
    for g in [b"merhaba", b"merhabb", b"Merhaba", b"merhaba "]:
        print("%-24r %d" % (g, cig_bit(b"merhaba", g)))
    toplam = 0
    n = 1000
    for i in range(n):
        toplam += cig_bit(b"sayi%d" % i, b"sayi%d" % (i + 1))
    print("1000 ardisik girdi, ortalama fark: %.1f bit"
          % (toplam / n))


def parola_hashle(parola):
    """Rastgele tuzlu scrypt ozeti. Kayit bicimi kendi parametrelerini
    tasir; boylece ileride maliyet artirilabilir."""
    tuz = os.urandom(16)                    # kriptografik rastgele
    ozet = hashlib.scrypt(parola.encode("utf-8"), salt=tuz,
                          n=N, r=R, p=P, dklen=32)
    return "scrypt$%d$%d$%d$%s$%s" % (N, R, P, tuz.hex(), ozet.hex())


def parola_dogrula(parola, kayit):
    try:
        ad, n, r, p, tuz_h, ozet_h = kayit.split("$")
        if ad != "scrypt":
            return False
        n, r, p = int(n), int(r), int(p)
        tuz = bytes.fromhex(tuz_h)
        beklenen = bytes.fromhex(ozet_h)
    except ValueError:
        return False                        # bozuk kayit: reddet
    if not (2 <= n <= N_MAKS) or r < 1 or p < 1:
        return False                        # kayit guvenilmez
    aday = hashlib.scrypt(parola.encode("utf-8"), salt=tuz,
                          n=n, r=r, p=p, dklen=len(beklenen))
    # Sabit zamanli karsilastirma: == ilk farkli baytta durur
    return hmac.compare_digest(aday, beklenen)


def sure():
    parola = "gizli-parola-2026"
    tekrar = {"sha256": 2000, "pbkdf2": 3, "scrypt": 20}
    sonuc = []
    t = time.perf_counter()
    for _ in range(tekrar["sha256"]):
        hashlib.sha256(os.urandom(16) + parola.encode()).digest()
    sonuc.append(("sha256 (tuzlu, tek tur)", "sha256",
                  (time.perf_counter() - t)
                  / tekrar["sha256"] * 1000))
    t = time.perf_counter()
    for _ in range(tekrar["pbkdf2"]):
        hashlib.pbkdf2_hmac("sha256", parola.encode(), os.urandom(16),
                            PBKDF2_TUR)
    sonuc.append(("pbkdf2-hmac-sha256 (600k)", "pbkdf2",
                  (time.perf_counter() - t)
                  / tekrar["pbkdf2"] * 1000))
    t = time.perf_counter()
    for _ in range(tekrar["scrypt"]):
        hashlib.scrypt(parola.encode(), salt=os.urandom(16),
                       n=N, r=R, p=P, dklen=32)
    sonuc.append(("scrypt (n=2^14, r=8, p=1)", "scrypt",
                  (time.perf_counter() - t)
                  / tekrar["scrypt"] * 1000))
    print("%-30s %12s" % ("yontem", "ms/hash"))
    for ad, _, ms in sonuc:
        print("%-30s %12.3f" % (ad, ms))
    veri = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "b32_kdf_olcum.csv")
    with open(veri, "w", encoding="utf-8", newline="\n") as f:
        f.write("yontem,ms_per_hash\n")
        for ad, kisa, ms in sonuc:
            f.write("%s,%.3f\n" % (kisa, ms))


def test():
    hata = 0

    def dogru(ad, kosul):
        nonlocal hata
        print(("GECTI " if kosul else "KALDI ") + ad)
        if not kosul:
            hata += 1

    k = parola_hashle("cok-gizli-42")
    dogru("dogru parola kabul", parola_dogrula("cok-gizli-42", k))
    dogru("yanlis parola red", not parola_dogrula("cok-gizli-43", k))
    dogru("bos parola red", not parola_dogrula("", k))
    k2 = parola_hashle("cok-gizli-42")
    dogru("ayni parola, farkli tuz", k != k2)
    dogru("iki kayit da dogrulanir",
          parola_dogrula("cok-gizli-42", k2))
    parcalar = k.split("$")
    bozuk = parcalar[:5] + [parcalar[5][:-2] + "00"]
    dogru("ozet son bayti degisince red",
          not parola_dogrula("cok-gizli-42", "$".join(bozuk)))
    dogru("bozuk bicim red", not parola_dogrula("x", "scrypt$abc"))
    dogru("hex olmayan tuz red",
          not parola_dogrula("x", "scrypt$16384$8$1$zz$00"))
    dogru("asiri n sinirda red",
          not parola_dogrula("x", "scrypt$1073741824$8$1$00$00"))
    print("hata sayisi:", hata)
    return hata


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "cig":
        cig()
    elif kip == "sure":
        sure()
    elif kip == "test":
        sys.exit(1 if test() else 0)
    else:
        print("kullanim: cig | sure | test")
        sys.exit(2)
