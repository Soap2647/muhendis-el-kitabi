# -*- coding: utf-8 -*-
"""Bölüm 66 - t06: transfer öğrenme (kendi kendine ön eğitim).

Gerçek ImageNet ağırlığı kullanılmaz (indirme yasak). Bunun yerine:
  1) Kaynak alan: 8 sınıf, temiz sentetik şekiller, 1500/sınıf ->
  ön eğitim.
  2) Hedef alan: 4 sınıf, gürültülü/bulanık; sınıf başına n örnek ile
     üç yöntem:  sıfırdan | özellik çıkarıcı (gövde dondurulmuş)
                 | ince ayar (gövde düşük öğrenme oranıyla).
Ön eğitim tek tohumla yapılır; hedef ince ayar 5 tohumla tekrarlanır.
"""

import csv
import os
import time
import numpy as np
import torch
from synth import hedef_veri, kaynak_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ADIM = 1000
Xs, ys = hedef_veri(300, 99)
Xs_g, ys_g = tensor(Xs, ys)

# 1) Ön eğitim (kaynak alan, 8 sınıf)
Xk, yk = kaynak_veri(1500, 7)
Xk_g, yk_g = tensor(Xk, yk)
Xkt, ykt = kaynak_veri(200, 8)
Xkt_g, ykt_g = tensor(Xkt, ykt)
torch.manual_seed(7)
on = Kucuk(K=8).to(DEV)
t0 = time.perf_counter()
egit(on, Xk_g, yk_g, adim=3000, tohum=7)
torch.cuda.synchronize()
print("Ön eğitim süresi: %.1f s" % (time.perf_counter() - t0))
print("Kaynak alan test doğruluğu: %.4f" % dogruluk(on, Xkt_g, ykt_g))
ON_SD = {
    k: v.clone()
    for k, v in on.state_dict().items()
    if not k.startswith("bas.")
}


def govde_yukle(model):
    model.load_state_dict(ON_SD, strict=False)
    return model


sonuc = []
for n in (10, 25, 50, 100, 300):
    for tohum in range(5):
        Xt, yt = hedef_veri(n, 200 + tohum)
        Xt_g, yt_g = tensor(Xt, yt)

        # a) sıfırdan
        torch.manual_seed(tohum)
        m = Kucuk().to(DEV)
        egit(m, Xt_g, yt_g, adim=ADIM, tohum=tohum)
        sonuc.append(("sifirdan", n, tohum, dogruluk(m, Xs_g, ys_g)))

        # b) özellik çıkarıcı: gövde donuk (BN de eval modunda)
        torch.manual_seed(tohum)
        m = govde_yukle(Kucuk().to(DEV))
        for p in m.ozellik.parameters():
            p.requires_grad_(False)
        egit(m, Xt_g, yt_g, adim=ADIM, tohum=tohum, sabit=[m.ozellik])
        sonuc.append(("ozellik", n, tohum, dogruluk(m, Xs_g, ys_g)))

        # c) ince ayar: gövde 1e-4, baş 1e-3 (katman başına öğrenme
        # oranı)
        torch.manual_seed(tohum)
        m = govde_yukle(Kucuk().to(DEV))
        grup = [
            {"params": m.ozellik.parameters(), "lr": 1e-4},
            {"params": m.bas.parameters(), "lr": 1e-3},
        ]
        egit(m, Xt_g, yt_g, adim=ADIM, tohum=tohum, grup_lr=grup)
        sonuc.append(("ince_ayar", n, tohum, dogruluk(m, Xs_g, ys_g)))
    print(
        "sınıf başına %3d ->  " % n
        + "  ".join(
            "%s %.3f"
            % (
                yo,
                np.mean(
                    [s[3] for s in sonuc if s[0] == yo and s[1] == n]
                ),
            )
            for yo in ("sifirdan", "ozellik", "ince_ayar")
        )
    )

print("\nTest doğruluğu, ortalama ± sapma (5 tohum):")
for n in (10, 25, 50, 100, 300):
    satir = []
    for yo in ("sifirdan", "ozellik", "ince_ayar"):
        v = [s[3] for s in sonuc if s[0] == yo and s[1] == n]
        satir.append(
            "%s %.3f±%.3f" % (yo, np.mean(v), np.std(v, ddof=1))
        )
    print("n=%3d  " % n + "  ".join(satir))

os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_transfer.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["yontem", "n_sinif", "tohum", "dogruluk"])
    for s in sonuc:
        w.writerow([s[0], s[1], s[2], "%.4f" % s[3]])
