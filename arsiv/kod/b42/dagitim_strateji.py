# -*- coding: utf-8 -*-
# dagitim_strateji.py: üç dağıtım stratejisinin ZAMAN MODELİ.
# N = 4 kopya; pod açılışı 2 tik sürer. Tik bir zaman adımıdır,
# gerçek saniye değildir. Çıktı CSV'dir (engine/veri/ için).
import csv
import os
import sys

N = 4
ACILIS = 2
TIKLER = 6


class Pod:
    def __init__(self, surum, t):
        self.surum = surum
        self.hazir_t = t + ACILIS

    def hazir(self, t):
        return t >= self.hazir_t


def sayim(pods, t, hizmet):
    """Trafiği alan sürümün hazır pod sayısı; diğeri 0 sayılır."""
    v1 = sum(1 for p in pods if p.surum == "v1" and p.hazir(t))
    v2 = sum(1 for p in pods if p.surum == "v2" and p.hazir(t))
    if hizmet == "v1":
        v2 = 0
    elif hizmet == "v2":
        v1 = 0
    return (v1, v2, len(pods))


def yeniden_olustur():
    """Önce v1 tamamen silinir, sonra v2 başlatılır."""
    pods = [Pod("v2", 0) for _ in range(N)]
    return [sayim(pods, t, None) for t in range(TIKLER)]


def mavi_yesil():
    """v2 tam kapasiteyle açılır. t=2'de trafik geçer,
    t=3'te v1 kaldırılır."""
    pods = [Pod("v1", -10) for _ in range(N)]
    pods += [Pod("v2", 0) for _ in range(N)]
    kayit = []
    for t in range(TIKLER):
        if t == 3:
            pods = [p for p in pods if p.surum == "v2"]
        hizmet = "v1" if t < 2 else "v2"
        kayit.append(sayim(pods, t, hizmet))
    return kayit


def yuvarlanan():
    """maxSurge=1, maxUnavailable=1: N=4 için en az 3 hazır pod."""
    pods = [Pod("v1", -10) for _ in range(N)]
    olusturulan, kayit = 0, []
    for t in range(TIKLER):
        if len(pods) < N + 1 and olusturulan < N:
            pods.append(Pod("v2", t))
            olusturulan += 1
        hazir = sum(1 for p in pods if p.hazir(t))
        eskiler = [p for p in pods if p.surum == "v1"]
        if eskiler and hazir - 1 >= N - 1:
            pods.remove(eskiler[0])
        kayit.append(sayim(pods, t, None))
    return kayit


def ana():
    csv_yolu = sys.argv[1] if len(sys.argv) > 1 else "b42_dagitim.csv"
    satirlar = []
    for ad, fn in (("yeniden_olustur", yeniden_olustur),
                   ("mavi_yesil", mavi_yesil),
                   ("yuvarlanan", yuvarlanan)):
        print(ad)
        print("  tik  v1  v2  toplam  kesinti")
        for t, (v1, v2, top) in enumerate(fn()):
            kes = 1 if v1 + v2 == 0 else 0
            print("  %-4d %-3d %-3d %-7d %d" % (t, v1, v2, top, kes))
            satirlar.append([ad, t, v1, v2, top, kes])
    with open(csv_yolu, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["strateji", "tik", "v1", "v2", "toplam",
                    "kesinti"])
        w.writerows(satirlar)
    print("yazildi:", os.path.basename(csv_yolu))


if __name__ == "__main__":
    ana()
