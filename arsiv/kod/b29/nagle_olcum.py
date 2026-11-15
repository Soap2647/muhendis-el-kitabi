# -*- coding: utf-8 -*-
# nagle_olcum.py - Nagle ve gecikmeli onay etkisini loopback'te ölçer.
# Tur: istemci 4 bayt ve sonra 60 bayt yazar (küçük iki yazı), sunucu
# 64 baytın tamamını okuyunca 1 bayt yanıt verir. Süre = bir tur.
import socket
import statistics
import threading
import time

TUR = 40
MESAJ = 64
BASLIK = 4


def tam_oku(s, n):
    parca = bytearray()
    while len(parca) < n:
        b = s.recv(n - len(parca))
        if not b:
            raise EOFError("bağlantı kapandı")
        parca += b
    return bytes(parca)


def sunucu(port, hazir):
    dinleyici = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dinleyici.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dinleyici.bind(("127.0.0.1", port))
    dinleyici.listen(1)
    hazir.set()
    baglanti, _ = dinleyici.accept()
    with baglanti:
        for _ in range(TUR):
            tam_oku(baglanti, MESAJ)
            baglanti.sendall(b"K")
    dinleyici.close()


SONUCLAR = []


def olc(ad, port, nodelay, iki_yazi):
    hazir = threading.Event()
    t = threading.Thread(target=sunucu, args=(port, hazir))
    t.start()
    hazir.wait()
    istemci = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if nodelay:
        istemci.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    istemci.connect(("127.0.0.1", port))
    sureler = []
    govde = b"x" * (MESAJ - BASLIK)
    for _ in range(TUR):
        t0 = time.perf_counter()
        if iki_yazi:
            istemci.sendall(b"h" * BASLIK)
            istemci.sendall(govde)
        else:
            istemci.sendall(b"h" * BASLIK + govde)
        tam_oku(istemci, 1)
        sureler.append((time.perf_counter() - t0) * 1000.0)
    istemci.close()
    t.join()
    kalan = sureler[5:]  # ilk turlar bağlantı gürültüsü
    med = statistics.median(kalan)
    SONUCLAR.append((ad, med, statistics.mean(kalan)))
    print("%-30s medyan=%8.3f ms ort=%8.3f ms" % (
        ad, statistics.median(kalan), statistics.mean(kalan)))


if __name__ == "__main__":
    import csv
    import sys
    olc("A: tek yazı (Nagle fark etmez)", 9041, False, False)
    olc("B: iki yazı, Nagle AÇIK", 9042, False, True)
    olc("C: iki yazı, TCP_NODELAY", 9043, True, True)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", newline="",
                  encoding="utf-8") as f:
            yaz = csv.writer(f)
            yaz.writerow(["senaryo", "medyan_ms", "ortalama_ms"])
            for ad, med, ort in SONUCLAR:
                yaz.writerow([ad, "%.3f" % med, "%.3f" % ort])
