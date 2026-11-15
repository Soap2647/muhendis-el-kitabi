# -*- coding: utf-8 -*-
"""Bölüm 66 - t09: CNN ne öğrendi? Filtreler, özellik haritaları,
Grad-CAM,
karışıklık matrisi ve en kötü hatalar. Model: hedef alan,
800/sınıf, tohum 0.
"""

import csv
import os
import numpy as np
import torch
import torch.nn.functional as F
from synth import hedef_veri
from ortak import DEV, tensor, Kucuk, egit, dogruluk

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
Xt, yt = hedef_veri(800, 401)
Xs, ys = hedef_veri(300, 99)
Xt_g, yt_g = tensor(Xt, yt)
Xs_g, ys_g = tensor(Xs, ys)
torch.manual_seed(0)
model = Kucuk().to(DEV)
egit(model, Xt_g, yt_g, adim=1500, tohum=0)
model.eval()
print("Test doğruluğu: %.4f" % dogruluk(model, Xs_g, ys_g))

# 1) Karışıklık matrisi
with torch.no_grad():
    tahmin = torch.cat(
        [
            model(Xs_g[i : i + 256]).softmax(1)
            for i in range(0, len(ys), 256)
        ]
    )
pred = tahmin.argmax(1).cpu().numpy()
K = 4
M = np.zeros((K, K), dtype=int)
for g, p in zip(ys, pred):
    M[g, p] += 1
print("\nKarışıklık matrisi (satır: gerçek, sütun: tahmin):")
print(M)
os.makedirs(VERI, exist_ok=True)
with open(
    os.path.join(VERI, "b66_karisiklik.csv"),
    "w",
    newline="",
    encoding="utf-8",
) as f:
    w = csv.writer(f)
    w.writerow(["gercek", "tahmin", "sayi"])
    for i in range(K):
        for j in range(K):
            w.writerow([i, j, M[i, j]])

# 2) İlk katman filtreleri ve özellik haritaları
filtre = (
    model.ozellik[0][0].weight.detach().cpu().numpy()[:, 0]
)  # (16,3,3)
kayit = {}


def kanca(ad):
    def f(_, __, out):
        kayit[ad] = out.detach()

    return f


h1 = model.ozellik[0][2].register_forward_hook(kanca("f1"))
h2 = model.ozellik[2].register_forward_hook(kanca("f3"))
ornek = Xs_g[:1]
with torch.no_grad():
    model(ornek)
h1.remove()
h2.remove()
print(
    "\nİlk katman filtre şekli: %s\nf1 %s, f3 %s"
    % (
        filtre.shape,
        tuple(kayit["f1"].shape),
        tuple(kayit["f3"].shape),
    )
)
f1 = kayit["f1"][0].cpu().numpy()  # (16,32,32)
f3 = kayit["f3"][0].cpu().numpy()  # (64,8,8)


# 3) Grad-CAM (sıfırdan): son konvolüsyon çıktısının sınıf skoruna
# göre
# ağırlıklı toplamı; ağırlık = o kanalın gradyanının uzamsal
# ortalaması.
def gradcam(girdi, sinif=None):
    aktivasyon = {}

    def kanca_f(_, __, out):
        aktivasyon["a"] = out
        out.register_hook(lambda gr: aktivasyon.__setitem__("g", gr))

    h = model.ozellik[2].register_forward_hook(kanca_f)
    logit = model(girdi)
    h.remove()
    if sinif is None:
        sinif = logit.argmax(1)
    skor = logit.gather(1, sinif[:, None]).sum()
    model.zero_grad()
    skor.backward()
    A, G = aktivasyon["a"], aktivasyon["g"]
    agirlik = G.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((agirlik * A).sum(1, keepdim=True))
    cam = F.interpolate(
        cam, size=(32, 32), mode="bilinear", align_corners=False
    )[:, 0]
    cam = cam / (cam.amax(dim=(1, 2), keepdim=True) + 1e-8)
    return cam.detach().cpu().numpy(), sinif.detach().cpu().numpy()


# Her sınıftan doğru tahmin edilmiş birer örnek
dogru_idx = [
    int(np.where((ys == c) & (pred == c))[0][0]) for c in range(K)
]
cam_d, _ = gradcam(Xs_g[dogru_idx])

# En kötü hatalar: yanlış tahmin, en yüksek güvenle
yanlis = np.where(pred != ys)[0]
guven = tahmin.cpu().numpy()[yanlis, pred[yanlis]]
en_kotu = yanlis[np.argsort(-guven)[:4]]
cam_y, _ = gradcam(
    Xs_g[en_kotu], sinif=torch.tensor(pred[en_kotu], device=DEV)
)
print(
    "\nGrad-CAM: doğru örnekler (gerçek sınıflar %s)" % ys[dogru_idx]
)
print("En kötü 4 hata (gerçek, tahmin, güven):")
for g_, t_, c_ in zip(
    ys[en_kotu], pred[en_kotu], guven[np.argsort(-guven)[:4]]
):
    print("  gerçek %d, tahmin %d, güven %.3f" % (g_, t_, c_))

np.savez(
    os.path.join(VERI, "b66_gorsel.npz"),
    filtre=filtre,
    f1=f1,
    f3=f3,
    girdi_ornek=Xs[0, 0],
    dogru_img=Xs[dogru_idx, 0],
    dogru_cam=cam_d,
    dogru_sinif=ys[dogru_idx],
    yanlis_img=Xs[en_kotu, 0],
    yanlis_cam=cam_y,
    yanlis_gercek=ys[en_kotu],
    yanlis_tahmin=pred[en_kotu],
    yanlis_guven=guven[np.argsort(-guven)[:4]],
)
