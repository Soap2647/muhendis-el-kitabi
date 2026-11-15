# -*- coding: utf-8 -*-
"""Tek is: olcumleri metin satirlarina cevirmek."""


def metin(olcumler, ort):
    satirlar = ["%-10s %8.2f %s" % (o.tur, o.deger, o.birim)
                for o in olcumler]
    satirlar.append("ORT %.2f" % ort)
    return "\n".join(satirlar) + "\n"
