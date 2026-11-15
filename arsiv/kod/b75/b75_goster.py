# -*- coding: utf-8 -*-
"""Bolum 75: olcum CSV'lerini tablo olarak basar (yeniden olcmez).

Kullanim: python b75_goster.py olcum | mimari
"""
import csv
import sys

VERI = "D:/Mevcut Projeler/Kitap/engine/veri/"


def oku(ad):
    with open(VERI + ad, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def olcum():
    print("B     AI (FLOP/bayt)  olculen GFLOP/s  tavan  sinir")
    for r in oku("b75_roofline.csv"):
        print("%-5s %12s %15s %9s  %s" % (
            r["B"], r["ai"], r["gflops"], r["sinir"],
            r["sinir_turu"]))
    print("")
    print("model          B   medyan (ms)  p95 (ms)")
    for r in oku("b75_dinamik_gecikme.csv"):
        print("%-14s %-3s %11s %9s" % (
            r["model"], r["B"], r["medyan_ms"], r["p95_ms"]))


def mimari():
    print("model                 parametre        MAC  medyan  p95")
    for r in oku("b75_mimari.csv"):
        print("%-20s %10s %12s %7s %7s" % (
            r["model"], r["parametre"], r["mac"],
            r["medyan_ms"], r["p95_ms"]))


if __name__ == "__main__":
    {"olcum": olcum, "mimari": mimari}[sys.argv[1]]()
