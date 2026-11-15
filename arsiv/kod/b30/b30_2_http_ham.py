# -*- coding: utf-8 -*-
"""b30_2_http_ham.py: Sunucuya ham HTTP/1.1 GET gonderir.

Okuma amacli tek istek. Yaniti ayristirir, chunked govdeyi cozer.
Kullanim: python b30_2_http_ham.py [sunucu] [port] [yol]
"""
import socket
import sys
from b30_3_chunked import chunked_coz, yanit_ayir

HOST = sys.argv[1] if len(sys.argv) > 1 else "example.com"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 80
YOL = sys.argv[3] if len(sys.argv) > 3 else "/"

istek = ("GET %s HTTP/1.1\r\n"
         "Host: %s\r\n"
         "User-Agent: b30-ham-istemci/1.0\r\n"
         "Accept: text/html\r\n"
         "Connection: close\r\n"
         "\r\n" % (YOL, HOST)).encode("ascii")

print("Gonderilen (%d bayt):" % len(istek))
for satir in istek.split(b"\r\n")[:-2]:
    print(satir.decode("ascii") + "\\r\\n")

s = socket.create_connection((HOST, PORT), timeout=5)
s.sendall(istek)
ham = b""
while True:                  # Connection: close -> EOF = govde bitti
    parca = s.recv(4096)
    if not parca:
        break
    ham += parca
s.close()

durum, basliklar, govde = yanit_ayir(ham)
print("\nYanit toplam %d bayt" % len(ham))
print("Durum satiri:", durum)
for ad in ("content-type", "transfer-encoding", "content-length",
           "cache-control", "etag", "age", "cf-cache-status"):
    if ad in basliklar:
        print("  %-18s: %s" % (ad, basliklar[ad]))

if basliklar.get("transfer-encoding", "").lower() == "chunked":
    cozulmus, artan = chunked_coz(govde)
    print("Chunked govde cozuldu: %d bayt (artan: %d)" %
          (len(cozulmus), len(artan)))
else:
    cozulmus = govde
    print("Govde: %d bayt" % len(govde))
print("Ilk 60 karakter:")
print(cozulmus[:60].decode("utf-8", "replace"))
