# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 5: akislar ile kopya/hesap ortusmesi."""

import _cudaenv  # noqa: F401
import csv
import os
import time
import torch
from olcum import medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
ITER = 2  # hesap/kopya sureleri ~esit (olcum)


def isle(v):
    # Hesap yogun is: bellek trafigine kiyasla cok aritmetik
    for _ in range(ITER):
        v = v * 1.0000001 + 0.0000003
        v = torch.sin(v) * 0.5 + v * 0.5
    return v


def seri(gh, gd_out, parca, m):
    # Her parca: kopya -> hesap -> geri kopya, tek akista sirayla
    for i in range(parca):
        s = slice(i * m, (i + 1) * m)
        gd = gh[s].to("cuda", non_blocking=True)
        gd = isle(gd)
        gd_out[s].copy_(gd, non_blocking=True)
    torch.cuda.synchronize()


def ortusen(gh, gd_out, parca, m, akislar):
    # Parcalari farkli akislarda calistir: kopya ve hesap ortusebilir
    for i in range(parca):
        s = slice(i * m, (i + 1) * m)
        ak = akislar[i % len(akislar)]
        with torch.cuda.stream(ak):
            gd = gh[s].to("cuda", non_blocking=True)
            gd = isle(gd)
            gd_out[s].copy_(gd, non_blocking=True)
    torch.cuda.synchronize()


def main():
    torch.manual_seed(76)
    parca, m = 8, 1 << 22  # 8 parca x 4M eleman
    toplam = parca * m
    gh = torch.randn(
        toplam
    ).pin_memory()  # sabitlenmis (pinned) bellek
    gd_out = torch.empty(toplam, device="cuda")
    # Dogruluk: iki yol da ayni sonucu vermeli
    seri(gh, gd_out, parca, m)
    ref = gd_out.clone()
    akislar = [torch.cuda.Stream() for _ in range(3)]
    ortusen(gh, gd_out, parca, m, akislar)
    fark = (ref - gd_out).abs().max().item()
    print(f"toplam eleman = {toplam}, parca = {parca}, akis = 3")
    print(f"max fark (seri - ortusen) = {fark:.1e}")

    t_seri, _, _ = medyan_ms_torch(
        lambda: seri(gh, gd_out, parca, m), tekrar=7, isinma=2
    )
    t_ort, _, _ = medyan_ms_torch(
        lambda: ortusen(gh, gd_out, parca, m, akislar),
        tekrar=7,
        isinma=2,
    )
    # Yalnizca hesabin suresi (kopya yok): ust sinir olcegi
    gd = torch.randn(m, device="cuda")
    t_hesap, _, _ = medyan_ms_torch(
        lambda: isle(gd), tekrar=7, isinma=2
    )
    t_hesap_tum = t_hesap * parca
    # Olcek kontrolu: parca basina H2D kopya ve hesap suresi
    t_kopya, _, _ = medyan_ms_torch(
        lambda: gh[:m].to("cuda", non_blocking=True),
        tekrar=7,
        isinma=2,
    )
    print(f"parca H2D kopya : {t_kopya:6.3f} ms")
    print(f"parca hesap     : {t_hesap:6.3f} ms")
    print(f"seri            : {t_seri:8.2f} ms")
    print(f"ortusen (3 akis): {t_ort:8.2f} ms")
    print(f"hizlanma        : {t_seri / t_ort:6.2f}x")
    print(f"yalniz hesap    : {t_hesap_tum:8.2f} ms")
    with open(
        os.path.join(VERI, "b76_akis.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms"])
        w.writerow(["seri", round(t_seri, 3)])
        w.writerow(["ortusen_3_akis", round(t_ort, 3)])
        w.writerow(["yalniz_hesap", round(t_hesap_tum, 3)])


if __name__ == "__main__":
    main()
