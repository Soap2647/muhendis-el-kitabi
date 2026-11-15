# -*- coding: utf-8 -*-
# b80_izleme.py: operasyonel akista kayma izleme ve yeniden egitim
# tetigi. 60 pencere x 200 sahne. Pencere 0-19 referans (nominal),
# 20-30 arasinda kayma kademeli artar, 30 ve sonrasi tam kayma.
# Girdi kaymasi: PSI (girdi parlakligi). Skor kaymasi: KS (en yuksek
# tespit skoru). Performans: mAP@0.5, 3 pencere gecikmeli etiketle.
import os
import numpy as np
import torch
from scipy.stats import ks_2samp
from b80_veri import sahne, veri_seti, EGITIM, DRIFT
from b67_04_yolo_mini import (
    MiniYolo,
    tahmin,
    degerlendir,
    hedef_tensorleri,
    egit,
)

KLASOR = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
PENCERE = 60
N = 200  # pencere basina sahne
REF = range(0, 20)  # referans pencereler (nominal)
GECIKME = 3  # etiket gecikmesi (pencere)
PSI_ESIK, KS_ESIK, PERF_DUS = 0.2, 0.01, 0.05


def psi(ref, yeni, kutu=10):
    """Populasyon Kararlilik Indeksi (Bolum 77.10 ile ayni)."""
    kenar = np.quantile(ref, np.linspace(0, 1, kutu + 1))
    kenar[0], kenar[-1] = -np.inf, np.inf
    e = np.histogram(ref, kenar)[0] / len(ref)
    a = np.histogram(yeni, kenar)[0] / len(yeni)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def alpha(w):
    """Kayma karisim orani: 0 (referans), 1 (tam kayma)."""
    return float(np.clip((w - 20) / 10.0, 0.0, 1.0))


def pencere(w):
    """Pencere w: N sahne. Her sahne alpha olasiligiyla DRIFT'ten."""
    rng = np.random.default_rng(1000 + w)
    a = alpha(w)
    X = np.zeros((N, 1, 96, 96), np.float32)
    Y = []
    for i in range(N):
        ayar = DRIFT if rng.uniform() < a else EGITIM
        img, nes = sahne(rng, ayar)
        X[i, 0] = img
        Y.append(nes)
    return X, Y


def main():
    model = MiniYolo().to("cuda")
    model.load_state_dict(
        torch.load(os.path.join(KLASOR, "yolo_t1.pt"))
    )
    model.eval()
    veriler, tahminler = [], []
    for w in range(PENCERE):
        X, Y = pencere(w)
        veriler.append((X, Y))
        tahminler.append(tahmin(model, X))
    parlaklik = [v[0].reshape(N, -1).mean(1) for v in veriler]
    skor = [
        np.array([d[1].max() if len(d[1]) else 0.0 for d in t])
        for t in tahminler
    ]
    map_w = [
        degerlendir(tahminler[w], veriler[w][1])[0]
        for w in range(PENCERE)
    ]
    ref_p = np.concatenate([parlaklik[w] for w in REF])
    ref_s = np.concatenate([skor[w] for w in REF])
    ref_map = float(np.mean([map_w[w] for w in REF]))
    satirlar = []
    art_ust = 0
    tetik = None
    for w in range(PENCERE):
        p = psi(ref_p, parlaklik[w])
        ks_p = ks_2samp(ref_s, skor[w]).pvalue
        g_alarm = p > PSI_ESIK
        s_alarm = ks_p < KS_ESIK
        # performans alarmi: etiketler GECIKME pencere sonra gelir
        perf = None
        if w - GECIKME >= 0:
            perf = map_w[w - GECIKME]
        p_alarm = perf is not None and (ref_map - perf) > PERF_DUS
        alarm = g_alarm or s_alarm
        art_ust = art_ust + 1 if alarm else 0
        if tetik is None and art_ust >= 2:
            tetik = w  # iki ardisik alarm -> yeniden egit
        satirlar.append(
            (
                w,
                alpha(w),
                p,
                ks_p,
                map_w[w],
                int(g_alarm),
                int(s_alarm),
                int(p_alarm),
            )
        )
        print(
            "pencere %2d a=%.2f PSI=%.3f KS_p=%.4f mAP=%.4f "
            "girdi=%d skor=%d perf=%d"
            % (
                w,
                alpha(w),
                p,
                ks_p,
                map_w[w],
                g_alarm,
                s_alarm,
                p_alarm,
            )
        )
    print("referans mAP (0-19) = %.4f" % ref_map)
    print("yeniden egitim tetigi: pencere", tetik)
    # Yeniden egitim: karisik (nominal + sert olmayan kayma) veriyle
    if tetik is not None:
        Xa, Ya = veri_seti(1500, seed=2001, ayar=EGITIM)
        Xb, Yb = veri_seti(1500, seed=2002, ayar=DRIFT)
        Xr = np.concatenate([Xa, Xb])
        Yr = Ya + Yb
        ptr, otg, ctr = hedef_tensorleri(Yr)
        yeni = egit(11, Xr, ptr, otg, ctr, epoch=60)
        yeni_map = {}
        for w in range(tetik, PENCERE):
            yeni_map[w] = degerlendir(
                tahmin(yeni, veriler[w][0]), veriler[w][1]
            )[0]
        print(
            "yeni model, pencere %d..%d ort. mAP = %.4f"
            % (tetik, PENCERE - 1, np.mean(list(yeni_map.values())))
        )
        print(
            "eski model ayni pencerelerde = %.4f"
            % np.mean([map_w[w] for w in range(tetik, PENCERE)])
        )
    else:
        yeni_map = {}
    with open(
        os.path.join(VERI, "b80_izleme.csv"), "w", encoding="utf-8"
    ) as f:
        f.write(
            "pencere,alpha,psi,ks_p,map_eski,girdi_alarm,"
            "skor_alarm,perf_alarm,map_yeni\n"
        )
        for s in satirlar:
            w = s[0]
            yn = "%.4f" % yeni_map[w] if w in yeni_map else ""
            f.write(
                "%d,%.2f,%.4f,%.6f,%.4f,%d,%d,%d,%s\n"
                % (s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], yn)
            )


if __name__ == "__main__":
    main()
