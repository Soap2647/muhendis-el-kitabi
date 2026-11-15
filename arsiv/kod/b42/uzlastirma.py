# -*- coding: utf-8 -*-
# uzlastirma.py: uzlaştırma döngüsünün (reconciliation loop) modeli.
# Denetleyici istenen durumla (kopya sayısı) gözlenen durumu
# (pod listesi) karşılaştırır, farkı kapatan eylemleri üretir.
import itertools

_sayac = itertools.count(1)


class Pod:
    def __init__(self):
        self.ad = "pod-%d" % next(_sayac)
        self.saglikli = True


def uzlastir(istenen, pods):
    """Tek tur: sağlıksızı sil, eksiği ekle, fazlayı sil."""
    eylemler = []
    for p in list(pods):
        if not p.saglikli:
            pods.remove(p)
            eylemler.append("-" + p.ad)
    while len(pods) < istenen:
        p = Pod()
        pods.append(p)
        eylemler.append("+" + p.ad)
    while len(pods) > istenen:
        p = pods.pop()
        eylemler.append("-" + p.ad)
    return eylemler


def senaryo():
    pods, istenen = [], 3
    print("tik olay                 istenen mevcut eylemler")
    for t in range(1, 9):
        olay = "-"
        if t == 1:
            olay = "ilk durum"
        elif t == 4:
            olay = "pod-2 sağlıksız"
            for p in pods:
                if p.ad == "pod-2":
                    p.saglikli = False
        elif t == 6:
            olay = "istenen 3 -> 5"
            istenen = 5
        elif t == 8:
            olay = "pod-4 elle silindi"
            pods[:] = [p for p in pods if p.ad != "pod-4"]
        eylemler = uzlastir(istenen, pods)
        print("%-3d %-19s %-7d %-6d %s"
              % (t, olay, istenen, len(pods),
                 ", ".join(eylemler) or "(yok)"))


if __name__ == "__main__":
    senaryo()
