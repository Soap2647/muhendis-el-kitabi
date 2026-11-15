# -*- coding: utf-8 -*-
# aimd_sim.py - cwnd'nin RTT adımlarındaki evrimi (AIMD).
# Model (Reno benzeri, sadeleştirilmiş):
#   - yavaş başlangıç: cwnd < ssthresh ise her RTT'de iki katına çıkar
#   - kaçınma: cwnd >= ssthresh ise her RTT'de +1
#   - kayıp: cwnd KAPASITE'yi aşınca (deterministik)
#     kayıpta ssthresh = cwnd/2 ve cwnd = ssthresh
# Rastgele kayıp kullanılmadığı için sonuç her çalıştırmada aynıdır.
# Kullanım: python aimd_sim.py <çıktı.csv>
import csv
import sys

RTT_SAYISI = 120
KAPASITE = 40        # yol kapasitesi (paket cinsinden), örnek değer
SSTHRESH_BASLANGIC = 32


def simule_et():
    cwnd = 1
    ssthresh = SSTHRESH_BASLANGIC
    satirlar = []
    for rtt in range(RTT_SAYISI):
        if cwnd > KAPASITE:
            # kayıp: o andaki cwnd kaydedilir, sonra azalır
            satirlar.append((rtt, cwnd, ssthresh, 1))
            ssthresh = max(cwnd // 2, 2)
            cwnd = ssthresh
            continue
        satirlar.append((rtt, cwnd, ssthresh, 0))
        if cwnd < ssthresh:
            cwnd = cwnd * 2
        else:
            cwnd = cwnd + 1
    return satirlar


if __name__ == "__main__":
    cikti = sys.argv[1] if len(sys.argv) > 1 else "b29_aimd.csv"
    veri = simule_et()
    with open(cikti, "w", newline="", encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["rtt", "cwnd", "ssthresh", "kayip"])
        yaz.writerows(veri)
    kayip_anlari = [r for r, _, _, k in veri if k]
    print("satır:", len(veri), "kayıp RTT'leri:", kayip_anlari)
    print("ilk 12 satır (rtt, cwnd, ssthresh, kayip):")
    for s in veri[:12]:
        print("  ", s)
