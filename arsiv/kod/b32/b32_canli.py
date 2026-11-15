# -*- coding: utf-8 -*-
"""b32_canli.py: iki HTTP sunucusunu yalnizca 127.0.0.1 uzerinde
calistirip ayni kotu istegi gonderir ve hayatta kalmayi olcer.

Kullanim: python b32_canli.py
"""

import os
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KOTU = b"PO\xadT / HTTP/1.1\r\n\r\n"    # yontemde ASCII disi bayt
IYI = (b"GET /index.html HTTP/1.1\r\nHost: x\r\n"
       b"Connection: close\r\n\r\n")


def bos_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def bekle(port, sure=5.0):
    son = time.time() + sure
    while time.time() < son:
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            return True
        except OSError:
            time.sleep(0.1)
    return False


def istek(port, veri):
    try:
        with socket.create_connection(("127.0.0.1", port), 2) as s:
            s.sendall(veri)
            s.settimeout(2)
            return s.recv(200)
    except OSError as e:
        return b"HATA: " + type(e).__name__.encode()


def dene(ad, dosya):
    kok = tempfile.mkdtemp(prefix="b32canli_")
    with open(os.path.join(kok, "index.html"), "w") as f:
        f.write("<p>merhaba</p>")
    port = bos_port()
    p = subprocess.Popen([sys.executable, os.path.join(HERE, dosya),
                          kok, str(port)],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if not bekle(port):
        print(ad, "sunucu baslamadi")
        p.kill()
        return
    kotu_cevap = istek(port, KOTU)
    time.sleep(0.3)
    olu = p.poll() is not None
    iyi_cevap = b"" if olu else istek(port, IYI)
    print("%-22s kotu istek -> %r" % (ad, kotu_cevap[:24]))
    if olu:
        p.wait(timeout=5)
        hata = p.stderr.read().decode("utf-8", "replace").strip()
        son = hata.splitlines()[-1] if hata else "?"
        print("%-22s SUNUCU OLDU (cikis=%d)" % (ad, p.returncode))
        print("%-22s son satir: %s" % ("", son.split(":")[0]))
    else:
        durum = iyi_cevap.split(b"\r\n", 1)[0]
        print("%-22s hayatta; sonraki iyi istek -> %r" % (ad, durum))
        p.kill()
    p.wait(timeout=5)


if __name__ == "__main__":
    dene("ozgun (b32_http_ham)", "b32_http_ham.py")
    dene("sagmlastirilmis", "b32_http_sag.py")
