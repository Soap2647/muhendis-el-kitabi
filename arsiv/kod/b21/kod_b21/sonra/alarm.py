# -*- coding: utf-8 -*-
"""Tek is: esigi asan olcumler icin alarm satiri uretmek."""


def alarmlar(olcumler):
    return ["ALARM: %s %.2f" % (o.tur, o.deger) for o in olcumler
            if o.esik is not None and o.deger > o.esik]
