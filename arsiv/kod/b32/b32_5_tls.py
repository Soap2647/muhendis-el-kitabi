# -*- coding: utf-8 -*-
"""b32_5_tls.py: TLS dogrulama davranisi ve sertifika okuma.

Bolum 1 (yerel, deterministik): kendinden imzali bir sertifika ile
  - varsayilan baglam: reddeder,
  - dogrulamayi kapatma: kabul eder (tehlikeli),
  - sertifikayi guvenilen kok olarak verme: kabul eder (dogru yol).
Bolum 2 (salt okuma): example.com'un sunucu sertifikasinin alanlarini
  okur. Tek bir TLS el sikismasi yapilir; veri gonderilmez.

Kullanim:
  python b32_5_tls.py yerel
  python b32_5_tls.py ornek      # internet gerekir
  python b32_5_tls.py test
"""

import datetime
import ipaddress
import os
import socket
import ssl
import sys
import tempfile
import threading

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def kendinden_sertifika(dizin):
    anahtar = ec.generate_private_key(ec.SECP256R1())
    ad = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                       "localhost")])
    simdi = datetime.datetime.now(datetime.timezone.utc)
    sert = (x509.CertificateBuilder()
            .subject_name(ad).issuer_name(ad)
            .public_key(anahtar.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(simdi - datetime.timedelta(minutes=5))
            .not_valid_after(simdi + datetime.timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address(
                    "127.0.0.1"))]), critical=False)
            .add_extension(x509.BasicConstraints(ca=True,
                                                 path_length=None),
                           critical=True)
            .sign(anahtar, hashes.SHA256()))
    cert_yol = os.path.join(dizin, "cert.pem")
    anah_yol = os.path.join(dizin, "anahtar.pem")
    with open(cert_yol, "wb") as f:
        f.write(sert.public_bytes(serialization.Encoding.PEM))
    with open(anah_yol, "wb") as f:
        f.write(anahtar.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
    return cert_yol, anah_yol


def sunucu_baslat(cert_yol, anah_yol):
    """Tek baglanti kabul eden TLS sunucusu. Port'u dondurur."""
    bag = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    bag.load_cert_chain(cert_yol, anah_yol)
    dinle = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dinle.bind(("127.0.0.1", 0))
    dinle.listen(4)
    port = dinle.getsockname()[1]

    def calis():
        for _ in range(3):              # uc istemci denemesi
            try:
                ham, _ = dinle.accept()
            except OSError:
                return
            try:
                with bag.wrap_socket(ham, server_side=True) as s:
                    s.recv(16)
            except (ssl.SSLError, OSError):
                pass                # istemci el sikismayi reddetti
            finally:
                ham.close()
        dinle.close()

    threading.Thread(target=calis, daemon=True).start()
    return port


def dene(ad, baglam, port):
    try:
        with socket.create_connection(("127.0.0.1", port),
                                      timeout=5) as ham:
            with baglam.wrap_socket(ham,
                                    server_hostname="localhost") as s:
                print("%-34s KABUL  (surum %s)" % (ad, s.version()))
                return True
    except ssl.SSLCertVerificationError as e:
        print("%-34s RED    (%s)" % (ad, e.verify_message))
        return False
    except (ssl.SSLError, OSError) as e:
        print("%-34s HATA   (%s)" % (ad, e))
        return False


def yerel(dizin=None):
    dizin = dizin or tempfile.mkdtemp(prefix="b32tls_")
    cert_yol, anah_yol = kendinden_sertifika(dizin)
    sonuc = {}
    port = sunucu_baslat(cert_yol, anah_yol)
    sonuc["varsayilan"] = dene("varsayilan baglam",
                               ssl.create_default_context(), port)
    port = sunucu_baslat(cert_yol, anah_yol)
    tehlikeli = ssl.create_default_context()
    tehlikeli.check_hostname = False
    tehlikeli.verify_mode = ssl.CERT_NONE
    sonuc["kapali"] = dene("dogrulama kapali (TEHLIKELI)",
                           tehlikeli, port)
    port = sunucu_baslat(cert_yol, anah_yol)
    dogru = ssl.create_default_context(cafile=cert_yol)
    sonuc["kok"] = dene("sertifika guvenilen kok olarak", dogru, port)
    return sonuc


def sertifika_oku(host, port=443):
    """Yalnizca okuma: el sikisma, sertifika alanlari, kapanis."""
    baglam = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=10) as ham:
        with baglam.wrap_socket(ham, server_hostname=host) as s:
            c = s.getpeercert()
            surum, sifre = s.version(), s.cipher()[0]
    def ad_listesi(seq):
        return ", ".join("%s=%s" % (k, v)
                         for grup in seq for k, v in grup)
    print("host         :", host)
    print("TLS surumu   :", surum)
    print("sifre paketi :", sifre)
    cn = lambda seq: [v for g in seq for k, v in g
                      if k == "commonName"][0]
    print("konu (CN)    :", cn(c["subject"]))
    print("veren (CN)  :", cn(c["issuer"]))
    print("gecerlilik   :", c["notBefore"], "->", c["notAfter"])
    san = [v for k, v in c.get("subjectAltName", ()) if k == "DNS"]
    print("SAN (ilk 3)  :", ", ".join(san[:3]),
          "(toplam %d)" % len(san))


def test():
    hata = 0
    dizin = tempfile.mkdtemp(prefix="b32tls_t_")
    sonuc = yerel(dizin)

    def dogru(ad, kosul):
        nonlocal hata
        print(("GECTI " if kosul else "KALDI ") + ad)
        if not kosul:
            hata += 1

    dogru("varsayilan baglam reddeder", sonuc["varsayilan"] is False)
    dogru("dogrulama kapaliyken kabul (zafiyet)",
          sonuc["kapali"] is True)
    dogru("kok olarak verilen sertifika kabul", sonuc["kok"] is True)
    print("hata sayisi:", hata)
    return hata


if __name__ == "__main__":
    kip = sys.argv[1] if len(sys.argv) > 1 else "test"
    if kip == "yerel":
        yerel()
    elif kip == "ornek":
        sertifika_oku("example.com")
    elif kip == "test":
        sys.exit(1 if test() else 0)
    else:
        print("kullanim: yerel | ornek | test")
        sys.exit(2)
