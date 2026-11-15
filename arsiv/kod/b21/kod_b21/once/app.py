# -*- coding: utf-8 -*-
"""ONCE: giris noktasi."""
from rapor import RaporYoneticisi

SENSORLER = [("termistor", 1), ("gerilim", 2)]


def main(yol):
    return RaporYoneticisi(SENSORLER, yol).calistir()


if __name__ == "__main__":
    print(main("rapor.txt"))
