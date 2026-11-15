# -*- coding: utf-8 -*-
"""b27_gil.py - Python'da x += 1 ve GIL.

Calistirma: python -I b27_gil.py
Not: CPython 3.12.10. GIL, iplik degisimini yalnizca belirli bayt kodu
noktalarinda (ornegin fonksiyon girisi, geri atlama) yoklar.
"""
import dis
import sys
import threading

N = 1000000


def artir_global():
    global sayac
    for _ in range(N):
        sayac += 1


def kimlik(x):
    return x


def artir_cagrili():
    global sayac
    for _ in range(N):
        sayac = sayac + kimlik(1)   # cagri: iplik degisebilecek nokta


def artir_kilitli():
    global sayac
    for _ in range(N):
        with kilit:
            sayac += 1


def kos(hedef, ipler=2):
    global sayac
    sayac = 0
    t = [threading.Thread(target=hedef) for _ in range(ipler)]
    for x in t:
        x.start()
    for x in t:
        x.join()
    return sayac


if __name__ == "__main__":
    print("Python", sys.version.split()[0])
    print("== x += 1 bayt kodu (global):")
    dis.dis(artir_global)
    beklenen = 2 * N
    kilit = threading.Lock()

    sayac = 0
    print("artir_global  : %d (beklenen %d)"
          % (kos(artir_global), beklenen))
    sys.setswitchinterval(1e-6)
    print("artir_global, switchinterval=1us: %d" % kos(artir_global))
    sys.setswitchinterval(0.005)
    print("artir_cagrili : %d (beklenen %d)"
          % (kos(artir_cagrili), beklenen))
    print("artir_kilitli : %d (beklenen %d)"
          % (kos(artir_kilitli), beklenen))
