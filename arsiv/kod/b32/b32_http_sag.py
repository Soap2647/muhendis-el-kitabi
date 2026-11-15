# -*- coding: utf-8 -*-
"""b32_http_sag.py: Bolum 30 HTTP sunucusunun sagmlastirilmis surumu.

Ozgun surumden farklar (Bolum 32.8):
  1. Ayristirma hatalari HttpHata ile tasinir; durum kodu bir int'tir.
     Ozgun surum UnicodeDecodeError'u int() ile cozmeye calisiyordu.
  2. Her ASCII cozme adimi denetlenir; cozulemeyen bayt 400 olur.
  3. Yol denetimi realpath ile yapilir: sembolik baglar da cozulur.
  4. Ana dongu her baglantiyi ayri korur: bir baglanti hatasi tum
     sunucuyu durdurmaz.

Kullanim: python b32_http_sag.py KOK PORT [MAKS_BAGLANTI]
"""
import hashlib
import mimetypes
import os
import socket
import sys

KOK = os.path.realpath(sys.argv[1]) if len(sys.argv) > 1 else ""
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 0
MAKS = int(sys.argv[3]) if len(sys.argv) > 3 else 0  # 0 = sinirsiz
MAKS_BASLIK = 8192

DURUM = {200: "OK", 304: "Not Modified", 400: "Bad Request",
         404: "Not Found", 405: "Method Not Allowed",
         431: "Request Header Fields Too Large"}


class HttpHata(Exception):
    """Istemci hatasi: durum kodu istisnanin kendisinde tasinir."""

    def __init__(self, kod):
        super().__init__(kod)
        self.kod = kod


def _ascii(bayt):
    try:
        return bayt.decode("ascii")
    except UnicodeDecodeError:
        raise HttpHata(400)


def istek_oku(f):
    """Istek basligini okur: (yontem, yol, surum, basliklar)."""
    satir = f.readline(MAKS_BASLIK + 1)
    if not satir:
        return None                       # istemci baglantiyi kapatti
    if len(satir) > MAKS_BASLIK:
        raise HttpHata(431)
    satir = satir.rstrip(b"\r\n")
    parcalar = satir.split(b" ")
    if len(parcalar) != 3 or not parcalar[2].startswith(b"HTTP/1."):
        raise HttpHata(400)
    yontem, yol, surum = (_ascii(p) for p in parcalar)
    basliklar, toplam = {}, len(satir)
    while True:
        satir = f.readline(MAKS_BASLIK + 1)
        toplam += len(satir)
        if toplam > MAKS_BASLIK:
            raise HttpHata(431)
        satir = satir.rstrip(b"\r\n")
        if not satir:                     # bos satir: baslik bitti
            break
        ad, sep, deger = satir.partition(b":")
        if not sep:
            raise HttpHata(400)
        anahtar = _ascii(ad.strip().lower())
        basliklar[anahtar] = deger.strip().decode("latin-1")
    return yontem, yol, surum, basliklar


def dosya_yolu(yol):
    """URL yolunu KOK altindaki gercek dosya yoluna cevirir.

    realpath sembolik baglari cozer; boylece KOK icindeki bir bag
    disari gosteriyorsa da reddedilir. URL cozme (%2e%2e gibi) bu
    sunucuda yapilmaz; yapilirsa denetim ayni tekrarlanmali."""
    yol = yol.split("?", 1)[0]
    if yol.endswith("/"):
        yol += "index.html"
    aday = os.path.realpath(os.path.join(KOK, yol.lstrip("/")))
    try:
        ortak = os.path.commonpath([KOK, aday])
    except ValueError:                    # farkli surucu
        return None
    if ortak != KOK:
        return None
    return aday if os.path.isfile(aday) else None


def cevap_yaz(conn, kod, basliklar, govde, sadece_bas=False):
    satirlar = ["HTTP/1.1 %d %s" % (kod, DURUM[kod])]
    satirlar += ["%s: %s" % kv for kv in basliklar]
    if kod != 304:
        satirlar.append("Content-Length: %d" % len(govde))
    veri = ("\r\n".join(satirlar) + "\r\n\r\n").encode("latin-1")
    conn.sendall(veri)
    if govde and not sadece_bas and kod != 304:
        conn.sendall(govde)


def istegi_isle(conn, yontem, yol, surum, basliklar):
    kapat = (basliklar.get("connection", "").lower() == "close"
             or surum == "HTTP/1.0")
    ek = [("Connection", "close" if kapat else "keep-alive")]
    if yontem not in ("GET", "HEAD"):
        ek.append(("Allow", "GET, HEAD"))
        cevap_yaz(conn, 405, ek, b"")
        return True
    dosya = dosya_yolu(yol)
    if dosya is None:
        cevap_yaz(conn, 404, ek, "404 Bulunamadi\n".encode("utf-8"))
        return kapat
    with open(dosya, "rb") as d:
        govde = d.read()
    etag = '"%s"' % hashlib.sha256(govde).hexdigest()[:16]
    ek += [("ETag", etag), ("Cache-Control", "max-age=60")]
    istemci = basliklar.get("if-none-match", "")
    if istemci and etag in [x.strip() for x in istemci.split(",")]:
        cevap_yaz(conn, 304, ek, b"")
        return kapat
    tip = mimetypes.guess_type(dosya)[0] or "application/octet-stream"
    ek += [("Content-Type", tip)]
    cevap_yaz(conn, 200, ek, govde, sadece_bas=(yontem == "HEAD"))
    return kapat


def baglanti_isle(conn, adres):
    conn.settimeout(5.0)
    f = conn.makefile("rb")
    try:
        while True:
            try:
                istek = istek_oku(f)
            except HttpHata as e:
                cevap_yaz(conn, e.kod, [("Connection", "close")], b"")
                return
            except socket.timeout:
                return
            if istek is None:
                return
            yontem, yol, surum, basliklar = istek
            kapat = istegi_isle(conn, yontem, yol, surum, basliklar)
            print("%s %s %s" % (adres[0], yontem, yol), flush=True)
            if kapat:
                return
    finally:
        f.close()
        conn.close()


if __name__ == "__main__":
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", PORT))
    srv.listen(16)
    print("dinleniyor 127.0.0.1:%d kok=%s" % (PORT, KOK), flush=True)
    sayac = 0
    while MAKS == 0 or sayac < MAKS:
        conn, adres = srv.accept()
        try:
            baglanti_isle(conn, adres)
        except Exception as e:      # savunma derinligi: katman 4
            print("baglanti hatasi:", type(e).__name__,
                  file=sys.stderr, flush=True)
        sayac += 1
    srv.close()
