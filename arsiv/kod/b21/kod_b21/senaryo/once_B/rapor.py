# -*- coding: utf-8 -*-
"""ONCE: istatistik, bicim, dosya yazma ve alarm tek sinifta."""
from olcum import olcumleri_oku


class RaporYoneticisi:
    def __init__(self, sensorler, yol):
        self.sensorler = sensorler
        self.yol = yol

    def calistir(self):
        olcumler = olcumleri_oku(self.sensorler)
        if not olcumler:
            raise ValueError("olcum yok")
        sayilar = [d for _, d, _ in olcumler]
        ort = sum(sayilar) / len(sayilar)
        satirlar = ["%-10s %8.2f %s" % (t, d, b)
                    for t, d, b in olcumler]
        satirlar.append("ORT %.2f" % ort)
        with open(self.yol, "w", encoding="utf-8") as f:
            f.write("\n".join(satirlar) + "\n")
        alarmlar = ["ALARM: %s %.2f" % (t, d) for t, d, _ in olcumler
                    if (t == "termistor" and d > 80.0) or (t == "basinc" and d > 110.0)]
        return ort, alarmlar
