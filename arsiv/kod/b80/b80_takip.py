# -*- coding: utf-8 -*-
# b80_takip.py: tespit-ile-takip. CNN tespitleri (tohum 1) ve Bolum
# 67'nin izleyicileri. Takip modu SECIMI yalnizca dogrulama
# videolarinda yapilir; test ve operasyonel videolar sonra okunur.
import csv
import os
import numpy as np
import torch
from b80_veri import video, NOMINAL, DRIFT
from b67_04_yolo_mini import MiniYolo, tahmin
from b67_08_takip import Izleyici, mota

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
MODLAR = ["acgozlu_iou", "macar_iou", "macar_tum", "byte"]


def model_yukle(seed):
    m = MiniYolo().to("cuda")
    m.load_state_dict(
        torch.load(os.path.join(KLASOR, "yolo_t%d.pt" % seed))
    )
    return m.eval()


def video_tespitleri(model, kareler):
    X = np.stack([k["img"] for k in kareler])[:, None]
    return tahmin(model, X)


def takip(mod, tespitler, cerceve=False):
    """cerceve=True: merkezi kare disina cikmis izler ciktiya girmez.
    Kaybolan nesnenin izi max_age karesi boyunca yasar; bu filtre
    o artik izleri susturur (iz silinmez, yalnizca cikti kesilir)."""
    izleyici = Izleyici(mod)
    cikti = []
    for kut, skor, _ in tespitler:
        iz = izleyici.guncelle(kut, skor)
        if cerceve:
            iz = [
                (i, b)
                for i, b in iz
                if 0 <= (b[0] + b[2]) / 2 <= 96
                and 0 <= (b[1] + b[3]) / 2 <= 96
            ]
        cikti.append(iz)
    return cikti


def degerlendir(model, videolar, mod, cerceve=False):
    """Videolar uzerinde toplam MOTA, FN, FP, IDSW (birlesik)."""
    fn = fp = idsw = 0
    mt = []
    toplam = 0
    for kareler in videolar:
        tes = video_tespitleri(model, kareler)
        m, f_n, f_p, ids, _ = mota(takip(mod, tes, cerceve), kareler)
        mt.append(m)
        fn += f_n
        fp += f_p
        idsw += ids
        toplam += sum(len(k["gt"]) for k in kareler)
    return {
        "mota": 1 - (fn + fp + idsw) / toplam,
        "fn": fn,
        "fp": fp,
        "idsw": idsw,
        "gt": toplam,
    }


def videolar(baslangic, sayi, ayar, kus=1):
    return [
        video(s, ayar=ayar, kus=kus)
        for s in range(baslangic, baslangic + sayi)
    ]


def main():
    model = model_yukle(1)
    dog = videolar(200, 5, NOMINAL)  # dogrulama
    test = videolar(300, 5, NOMINAL)  # test
    drift = videolar(400, 5, DRIFT)  # operasyonel
    satirlar = []
    for cer in (False, True):
        for mod in MODLAR:
            r = degerlendir(model, dog, mod, cer)
            satirlar.append(("dogrulama", mod, cer, r))
            print(
                "dogrulama cerceve=%d %-12s MOTA=%.4f FN=%d FP=%d "
                "IDSW=%d"
                % (cer, mod, r["mota"], r["fn"], r["fp"], r["idsw"])
            )
    # secim yalnizca dogrulama MOTA'sina gore (test'e bakilmadan)
    en = max(satirlar, key=lambda s: s[3]["mota"])
    secilen, cer_sec = en[1], en[2]
    print(
        "secilen (yalnizca dogrulama): mod=%s cerceve=%d"
        % (secilen, cer_sec)
    )
    sonuc = []
    for ad, kume in [("test", test), ("drift", drift)]:
        for cer in (False, True):
            for mod in MODLAR:
                r = degerlendir(model, kume, mod, cer)
                sonuc.append((ad, mod, cer, r))
                print(
                    "%-6s cer=%d %-12s MOTA=%.4f FN=%d FP=%d "
                    "IDSW=%d (GT=%d)"
                    % (
                        ad,
                        cer,
                        mod,
                        r["mota"],
                        r["fn"],
                        r["fp"],
                        r["idsw"],
                        r["gt"],
                    )
                )
    nl = chr(10)
    with open(
        os.path.join(VERI, "b80_takip.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("kume,mod,cerceve,mota,fn,fp,idsw,gt" + nl)
        for ad, mod, cer, r in satirlar + sonuc:
            f.write(
                "%s,%s,%d,%.4f,%d,%d,%d,%d"
                % (
                    ad,
                    mod,
                    cer,
                    r["mota"],
                    r["fn"],
                    r["fp"],
                    r["idsw"],
                    r["gt"],
                )
                + nl
            )
    # Sekil icin: test videosu 0, secilen yapilandirmayla yorunge
    kareler = test[0]
    tes = video_tespitleri(model, kareler)
    iz = takip(secilen, tes, cer_sec)
    with open(
        os.path.join(VERI, "b80_takip_iz.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("kare,tip,id,x1,y1,x2,y2" + nl)
        for t, k in enumerate(kareler):
            for g, b in zip(k["gt_id"], k["gt"]):
                f.write("%d,gt,%d,%d,%d,%d,%d" % (t, g, *b) + nl)
            for tid, b in iz[t]:
                f.write(
                    "%d,iz,%d,%.1f,%.1f,%.1f,%.1f" % (t, tid, *b) + nl
                )


if __name__ == "__main__":
    main()
