# -*- coding: utf-8 -*-
# b67_08b_kesisim.py: kesisen cift (GT 0 ve GT 1) icin kimlik
# degisimi (IDSW). (a) 20 videoda GT basina IDSW toplami,
# (b) tohum 107'de GT 0 ve 1'in atanan kimlikleri (sekil icin).
import os
import numpy as np
from scipy.optimize import linear_sum_assignment
from b67_veri import video
from b67_01_iou_nms import iou_matris
from b67_08_takip import Izleyici, MODLAR, VERI, mota


def idsw_gt(cikti, kareler):
    """GT kimligi -> IDSW sayisi (CLEAR MOT ile ayni kural)."""
    son, sayim = {}, {}
    for izler, kare in zip(cikti, kareler):
        gk = np.array(kare["gt"], float).reshape(-1, 4)
        gid = kare["gt_id"]
        if not izler or len(gk) == 0:
            continue
        ik = np.array([b for _, b in izler])
        iid = [i for i, _ in izler]
        iou = iou_matris(gk, ik)
        gecer = iou >= 0.5
        r, s = linear_sum_assignment(np.where(gecer, -iou, 1e6))
        for a, b in zip(r, s):
            if gecer[a, b]:
                k = gid[a]
                if k in son and son[k] != iid[b]:
                    sayim[k] = sayim.get(k, 0) + 1
                son[k] = iid[b]
    return sayim


if __name__ == "__main__":
    toplam = {m: [0, 0, 0] for m in MODLAR}
    for seed in range(100, 120):
        kareler = video(seed)
        for m in MODLAR:
            izci = Izleyici(m)
            cikti = [izci.guncelle(k["det"], k["skor"])
                     for k in kareler]
            s = idsw_gt(cikti, kareler)
            toplam[m][0] += s.get(0, 0)
            toplam[m][1] += s.get(1, 0)
            toplam[m][2] += sum(v for k, v in s.items()
                                if k not in (0, 1))
    print("20 video: kesisen cift (GT 0, 1) ve diger IDSW toplami:")
    satirlar = ["yontem,gt0_idsw,gt1_idsw,diger_idsw"]
    for m in MODLAR:
        g0, g1, d = toplam[m]
        print("%-13s GT0=%2d  GT1=%2d  diger=%2d" % (m, g0, g1, d))
        satirlar.append("%s,%d,%d,%d" % (m, g0, g1, d))
    with open(os.path.join(VERI, "b67_kesisim_ozet.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")

    # Sekil icin: tohum 107, GT 0 ve 1'in atanan iz kimlikleri
    kareler = video(107)
    satirlar = ["yontem,kare,gt_id,cx,cy,iz_id"]
    for m in MODLAR:
        izci = Izleyici(m)
        cikti = [izci.guncelle(k["det"], k["skor"]) for k in kareler]
        _, _, _, _, kayit = mota(cikti, kareler)
        for t, kare in enumerate(kareler):
            for g in (0, 1):
                if g in kare["gt_id"]:
                    k = kare["gt_id"].index(g)
                    b = kare["gt"][k]
                    cx = (b[0] + b[2]) / 2
                    cy = (b[1] + b[3]) / 2
                    satirlar.append("%s,%d,%d,%.1f,%.1f,%d" % (
                        m, t, g, cx, cy, kayit[t].get(g, -1)))
    with open(os.path.join(VERI, "b67_kesisim.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
    print("kaydedildi: b67_kesisim_ozet.csv, b67_kesisim.csv")
