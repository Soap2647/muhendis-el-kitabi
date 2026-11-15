# -*- coding: utf-8 -*-
# b80_guvence.py: guvence katmani. Her tespit iki kurala gore
# 'otomatik alarm' (operatore dogrudan gider) ya da 'operatore
# dogrulat' olarak ayrilir:
#   tek_skor : skor >= tau
#   topluluk : skor >= tau VE tohum 2 ile 3 da ayni sinifta ortusen
#              bir tespit uretir (IoU >= 0.5, skor >= 0.3)
# Esik yalnizca dogrulama kumesinde secilir (kesinlik >= 0.90 kosulu,
# kapsama en yuksek). Test ve OOD kumeleri sonra okunur.
import os
import pickle
import numpy as np
from b80_veri import veri_seti, EGITIM, NOMINAL, DRIFT
from b67_01_iou_nms import iou_matris

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
TAUS = np.round(np.arange(0.05, 0.96, 0.05), 2)
KESINLIK_HEDEF = 0.90


def uyum(d1, d2):
    """d1'in her tespiti icin d2'de ayni sinifli, IoU >= 0.5 ve skor
    >= 0.3 olan bir tespit var mi? (bool dizisi)"""
    kut1, _, cls1 = d1
    kut2, skor2, cls2 = d2
    out = np.zeros(len(kut1), bool)
    if len(kut1) == 0 or len(kut2) == 0:
        return out
    iou = iou_matris(kut1, kut2)
    ok = (
        (cls1[:, None] == cls2[None, :])
        & (iou >= 0.5)
        & (skor2[None, :] >= 0.3)
    )
    return ok.any(axis=1)


def tp_maske(kut, skor, cls, gk, gc):
    """Skora gore azalan sirada acgozlu eslesme; TP mask'i (kumulatif
    degil, her tespit icin)."""
    tp = np.zeros(len(kut), bool)
    if len(kut) == 0 or len(gk) == 0:
        return tp
    kullanildi = np.zeros(len(gk), bool)
    iou = iou_matris(kut, gk)
    for i in np.argsort(-skor, kind="stable"):
        aday = np.where((~kullanildi) & (gc == cls[i]), iou[i], -1.0)
        j = int(np.argmax(aday))
        if aday[j] >= 0.5:
            tp[i] = True
            kullanildi[j] = True
    return tp


def maske_uret(pred, kural, tau, tohum_preds):
    """Gorsel basina otomatik alarm maskeleri."""
    maskeler = []
    for i, (kut, skor, cls) in enumerate(pred):
        m = skor >= tau
        if kural == "topluluk":
            a = uyum((kut, skor, cls), tohum_preds[0][i]) & uyum(
                (kut, skor, cls), tohum_preds[1][i]
            )
            m = m & a
        maskeler.append(m)
    return maskeler


def olc(pred, Y, maskeler):
    """Donus: kesinlik, kapsama, gorsel basina yanlis alarm."""
    n_oto = tp = gt_say = 0
    for (kut, skor, cls), objs, m in zip(pred, Y, maskeler):
        gk = np.array([o["box"] for o in objs], float).reshape(-1, 4)
        gc = np.array([o["cls"] for o in objs], int)
        gt_say += len(gc)
        idx = np.where(m)[0]
        t = tp_maske(kut[idx], skor[idx], cls[idx], gk, gc)
        n_oto += len(idx)
        tp += int(t.sum())
    kesinlik = tp / n_oto if n_oto else float("nan")
    kapsama = tp / max(gt_say, 1)
    yanlis = (n_oto - tp) / len(Y)
    return kesinlik, kapsama, yanlis


def main():
    tahminler = pickle.load(
        open(os.path.join(KLASOR, "tahminler.pkl"), "rb")
    )
    kumeler = {
        "val": veri_seti(300, seed=5, ayar=EGITIM),
        "test": veri_seti(500, seed=777, ayar=NOMINAL),
        "drift": veri_seti(500, seed=888, ayar=DRIFT),
        "ood": veri_seti(500, seed=999, ayar=NOMINAL, kus=1),
    }
    # tohum 1 bir kayit; tohum 2 ve 3 uyum icin
    sonuc = []
    secim = {}
    for kural in ["tek_skor", "topluluk"]:
        # esik secimi: yalnizca dogrulama
        en_iyi = None
        for tau in TAUS:
            Xv, Yv = kumeler["val"]
            t2 = tahminler[(2, "val")]
            t3 = tahminler[(3, "val")]
            m = maske_uret(
                tahminler[(1, "val")], kural, tau, [t2, t3]
            )
            k, c, y = olc(tahminler[(1, "val")], Yv, m)
            sonuc.append((kural, "val", tau, k, c, y))
            if not np.isnan(k) and k >= KESINLIK_HEDEF:
                if en_iyi is None or c > en_iyi[1]:
                    en_iyi = (tau, c)
        secim[kural] = en_iyi[0] if en_iyi else None
        print(
            "%s: dogrulamada secilen tau = %s" % (kural, secim[kural])
        )
    # Korumasiz referans: tum tespitler otomatik (tau = 0.05)
    for ad, (X, Y) in kumeler.items():
        if ad == "val":  # dogrulama zaten yukarida
            continue
        for kural in ["tek_skor", "topluluk"]:
            for tau in TAUS:
                m = maske_uret(
                    tahminler[(1, ad)],
                    kural,
                    tau,
                    [tahminler[(2, ad)], tahminler[(3, ad)]],
                )
                k, c, y = olc(tahminler[(1, ad)], Y, m)
                sonuc.append((kural, ad, tau, k, c, y))
        m = [np.ones(len(p[1]), bool) for p in tahminler[(1, ad)]]
        k, c, y = olc(tahminler[(1, ad)], Y, m)
        sonuc.append(("korumasiz", ad, 0.0, k, c, y))
    with open(
        os.path.join(VERI, "b80_guvence.csv"), "w", encoding="utf-8"
    ) as f:
        f.write("kural,kume,tau,kesinlik,kapsama,yanlis_alarm_gor\n")
        for kural, ad, tau, k, c, y in sonuc:
            f.write(
                "%s,%s,%.2f,%.4f,%.4f,%.4f\n"
                % (kural, ad, tau, k, c, y)
            )
    print("\nSecilen esiklerle (test ve OOD):")
    for kural in ["tek_skor", "topluluk"]:
        tau = secim[kural]
        for ad in ["test", "drift", "ood"]:
            X, Y = kumeler[ad]
            m = maske_uret(
                tahminler[(1, ad)],
                kural,
                tau,
                [tahminler[(2, ad)], tahminler[(3, ad)]],
            )
            k, c, y = olc(tahminler[(1, ad)], Y, m)
            print(
                "%-9s %-5s tau=%.2f kesinlik=%.3f kapsama=%.3f "
                "yanlis/gorsel=%.3f" % (kural, ad, tau, k, c, y)
            )
    for ad in ["test", "ood"]:
        X, Y = kumeler[ad]
        m = [np.ones(len(p[1]), bool) for p in tahminler[(1, ad)]]
        k, c, y = olc(tahminler[(1, ad)], Y, m)
        print(
            "korumasiz %-5s kesinlik=%.3f kapsama=%.3f "
            "yanlis/gorsel=%.3f" % (ad, k, c, y)
        )


if __name__ == "__main__":
    main()
