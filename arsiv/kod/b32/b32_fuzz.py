# -*- coding: utf-8 -*-
"""b32_fuzz.py: sabit tohumlu mutasyon tabanli fuzzer.

Hedefler (kendi kodumuz):
  cerceve  : Bolum 31 uzunluk onekli cerceve okuyucusu (cerceve_al)
  telemetri: Bolum 31 CRC'li telemetri cozucusu (telemetri_coz)
  hmac     : Bolum 32 HMAC'li telemetri alicisi (Alici.al)
  http     : Bolum 30 HTTP sunucusunun baglanti isleyicisi

Beklenen red istisnalari (ValueError, EOFError) sayilmaz.
Diger her istisna bir HATA olarak raporlanir.
sayilmaz. Diger her istisna bir HATA olarak raporlanir.

Kullanim:
  python b32_fuzz.py ham     # Bolum 30 ozgun sunucusu
  python b32_fuzz.py sag     # sagmlastirilmis surum
  python b32_fuzz.py csv YOL # sonuc tablosunu CSV olarak yazar
"""

import contextlib
import io
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TOHUM = 32
YINELEME = 20000


class SahteSoket:
    """Parcali okuma: recv(n) en fazla bir parca dondurur."""

    def __init__(self, parcalar):
        self.parcalar = [bytearray(p) for p in parcalar]

    def recv(self, n):
        if not self.parcalar:
            return b""
        ilk = self.parcalar[0]
        k = min(n, len(ilk))
        cikti = bytes(ilk[:k])
        del ilk[:k]
        if not ilk:
            self.parcalar.pop(0)
        return cikti


class SahteBaglanti:
    """HTTP isleyicisi icin: makefile, sendall, close."""

    def __init__(self, veri):
        self.okuma = io.BytesIO(veri)
        self.yazilan = bytearray()

    def makefile(self, _mod):
        return self.okuma

    def settimeout(self, _t):
        pass

    def sendall(self, b):
        self.yazilan += b

    def close(self):
        pass


def mutasyon(r, veri, tohumlar):
    """Rastgele bir mutasyon uygular; bazen baska tohumdan parca."""
    b = bytearray(veri) if veri else bytearray(b"\x00")
    secim = r.randrange(7)
    if secim == 0 and b:                      # bayt degistir
        b[r.randrange(len(b))] = r.randrange(256)
    elif secim == 1:                          # bayt ekle
        b.insert(r.randrange(len(b) + 1), r.randrange(256))
    elif secim == 2 and b:                    # bayt sil
        del b[r.randrange(len(b))]
    elif secim == 3 and b:                    # kes
        del b[r.randrange(len(b)):]
    elif secim == 4:                          # ozel karakterler
        i = r.randrange(len(b) + 1)
        b[i:i] = r.choice(
            [b"\r\n", b" ", b":", b"\xff\xfe", b"\x00", b"/../"])
    elif secim == 5:                          # tekrar eden blok
        i = r.randrange(len(b) + 1)
        b[i:i] = b[i:i + r.randrange(1, 40)]
    else:                                     # baska tohumdan parca
        baska = r.choice(tohumlar)
        i = r.randrange(len(b) + 1)
        b[i:] = baska[r.randrange(len(baska) + 1):]
    return bytes(b)


def tara(ad, hedef, tohumlar, beklenen, yineleme=YINELEME):
    """Hedefi yineleme kez calistirir; beklenmeyen istisnalari sayar.

    beklenen: hedefin bilerek firlatabilecegi istisna sinifi demeti.
    Bu demet bos ise hedef istemci girdisinde istisna sizdirmamali."""
    r = random.Random(TOHUM)
    beklenmeyen = {}
    ornek = {}
    for _ in range(yineleme):
        girdi = mutasyon(r, r.choice(tohumlar), tohumlar)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                hedef(girdi)
        except beklenen:
            pass                              # sozlesmedeki red
        except Exception as e:                # beklenmeyen -> HATA
            tur = type(e).__name__
            beklenmeyen[tur] = beklenmeyen.get(tur, 0) + 1
            # en kisa yeniden uretici girdiyi sakla
            if tur not in ornek or len(girdi) < len(ornek[tur][0]):
                ornek[tur] = (girdi, str(e)[:60])
    return beklenmeyen, ornek


def hedef_cerceve(girdi):
    import b31_cerceve as c
    # Girdiyi 1-3 parcaya bolerek kisa okuma simule edilir
    r = random.Random(len(girdi))
    kesim = sorted(r.randrange(len(girdi) + 1) for _ in range(2))
    parcalar = [girdi[:kesim[0]], girdi[kesim[0]:kesim[1]],
                girdi[kesim[1]:]]
    c.cerceve_al(SahteSoket([p for p in parcalar if p]))


def hedef_telemetri(girdi):
    import b31_udp as u
    u.telemetri_coz(girdi)


def hedef_hmac(girdi):
    import b32_2_hmac_telemetri as h
    h.Alici(h.ANAHTAR).al(girdi)


def hedef_http(girdi, surum):
    kok = os.path.realpath(KOK[surum])
    if surum == "ham":
        import b32_http_ham as s
    else:
        import b32_http_sag as s
    s.KOK = kok
    s.baglanti_isle(SahteBaglanti(girdi), ("127.0.0.1", 0))


KOK = {}


def tohumlar_http():
    return [b"GET / HTTP/1.1\r\nHost: x\r\n\r\n",
            b"GET /a.txt HTTP/1.1\r\nConnection: close\r\n\r\n",
            b"HEAD /index.html HTTP/1.0\r\n\r\n",
            b"POST / HTTP/1.1\r\n\r\n",
            b"GET /../x HTTP/1.1\r\n\r\n"]


def tohumlar_cerceve():
    import struct
    return [struct.pack("!I", n) + b"x" * n for n in (0, 1, 5, 40)]


def tohumlar_telemetri():
    import b31_udp as u
    return [u.telemetri_paketi(1, 2, 3, 4, 5, 6),
            u.telemetri_paketi(9, 0, -1, -2, 300, 4000)]


def tohumlar_hmac():
    import b32_2_hmac_telemetri as h
    return [h.paketle(h.ANAHTAR, 1, 2, 3, 4, 5, 6),
            h.paketle(h.ANAHTAR, 9, 0, -1, -2, 300, 4000)]


def calistir(surum):
    global KOK
    kok = tempfile.mkdtemp(prefix="b32fz_")
    with open(os.path.join(kok, "index.html"), "w") as f:
        f.write("<p>x</p>")
    with open(os.path.join(kok, "a.txt"), "w") as f:
        f.write("a")
    KOK = {surum: kok}
    # Bolum 30 sunucusu modul yuklenirken sys.argv[1] (KOK) bekler
    sys.argv = ["b32_fuzz", kok, "8080"]
    sonuc = []
    hedefler = [
        # (ad, hedef, tohumlar, sozlesmedeki red istisnalari)
        ("cerceve", hedef_cerceve, tohumlar_cerceve(),
         (ValueError, EOFError)),
        ("telemetri", hedef_telemetri, tohumlar_telemetri(),
         (ValueError,)),
        ("hmac", hedef_hmac, tohumlar_hmac(), ()),
        ("http", lambda g: hedef_http(g, surum), tohumlar_http(), ()),
    ]
    for ad, f, t, beklenen in hedefler:
        b, o = tara(ad, f, t, beklenen)
        sonuc.append((ad, b, o))
    return sonuc


def yaz(sonuc, yol, surum):
    with open(yol, "w", encoding="utf-8", newline="\n") as f:
        f.write("surum,hedef,istisna,sayi\n")
        for ad, b, _ in sonuc:
            if not b:
                f.write("%s,%s,yok,0\n" % (surum, ad))
            for tur, n in b.items():
                f.write("%s,%s,%s,%d\n" % (surum, ad, tur, n))


def main(args):
    if not args or args[0] not in ("ham", "sag", "csv"):
        print("kullanim: ham | sag | csv YOL")
        return 2
    if args[0] == "csv":
        # Iki surum da calisir; sonuclar tek tabloya yazilir
        h = calistir("ham")
        g = calistir("sag")
        with open(args[1], "w", encoding="utf-8", newline="\n") as f:
            f.write("hedef,yineleme,ozgun,sagmlastirilmis\n")
            for (ad, bh, _), (_, bg, _) in zip(h, g):
                f.write("%s,%d,%d,%d\n" % (
                    ad, YINELEME, sum(bh.values()), sum(bg.values())))
        for ad, bh, _ in h:
            print("%-10s ozgun=%d" % (ad, sum(bh.values())))
        for ad, bg, _ in g:
            print("%-10s sag=%d" % (ad, sum(bg.values())))
        return 0
    surum = args[0]
    sonuc = calistir(surum)
    print("surum=%s, yineleme=%d, tohum=%d"
          % (surum, YINELEME, TOHUM))
    toplam = 0
    for ad, b, o in sonuc:
        if not b:
            print("%-10s beklenmeyen istisna yok" % ad)
        for tur, n in b.items():
            toplam += n
            girdi, mesaj = o[tur]
            print("%-9s %-11s x%-5d" % (ad, tur, n))
            print("  ornek: %r" % (girdi,))
            print("           mesaj: %s" % mesaj)
    print("toplam beklenmeyen istisna:", toplam)
    return 1 if toplam else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
