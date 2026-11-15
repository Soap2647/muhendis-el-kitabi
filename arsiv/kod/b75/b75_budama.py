# -*- coding: utf-8 -*-
"""Bolum 75: budama. Buyukluk budamasi (sifirdan), seyreklik taramasi,
kubik yinelemeli budama, piyango bileti, kanal budama ve hiz olcumu.
"""

import copy
import csv
import os
import numpy as np
import torch
import torch.nn as nn
from b75_ortak import (
    veri,
    mlp,
    mlp_t,
    egit,
    dogruluk,
    uygula_maske,
    zamanla,
    TOHUMLAR,
)

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
KATMANLAR = (0, 2, 4)  # mlp(): dogrusal katmanlarin indeksleri


def buyukluk_maskesi(W, oran):
    """En kucuk |w| degerlerinin oran kadarini 0 yapan 0/1 maske."""
    k = int(round(oran * W.numel()))
    m = torch.ones_like(W)
    if k > 0:
        en_kucuk = torch.argsort(W.abs().flatten())[:k]
        m.view(-1)[en_kucuk] = 0.0
    return m


def maskeler_olustur(model, oran):
    return {
        i: buyukluk_maskesi(model[i].weight.data, oran)
        for i in KATMANLAR
    }


def seyreklik(model):
    """Dogrusal katmanlardaki sifir oraninin ag geneline gore payi."""
    sifir = toplam = 0
    for i in KATMANLAR:
        W = model[i].weight.data
        sifir += (W == 0).sum().item()
        toplam += W.numel()
    return sifir / toplam


def torch_ile_dogrula():
    """Kendi maskemiz torch prune.l1_unstructured ile ayni mi?
    """
    import torch.nn.utils.prune as prune

    lin = nn.Linear(64, 256)
    W = lin.weight.data.clone()
    m1 = buyukluk_maskesi(W, 0.9)
    prune.l1_unstructured(lin, "weight", amount=0.9)
    print(
        "torch ile maske eslesmesi:", torch.equal(m1, lin.weight_mask)
    )


def kubik(sf, t, T):
    """Zhu & Gupta (2017) kubik seyreklik takvimi (genel bilgi)."""
    return sf * (1 - (1 - t / T) ** 3)


def kanal_buda(model, oran):
    """Gizli katman 0'in en dusuk L1 normlu noronlarini siler; sonraki
    dogrusal katmanin ilgili sutunlari da silinir."""
    W0, b0 = model[0].weight.data, model[0].bias.data
    W2, b2 = model[2].weight.data, model[2].bias.data
    n = W0.shape[0]
    tut = n - int(round(oran * n))
    norm = W0.abs().sum(dim=1)
    idx = torch.argsort(norm, descending=True)[:tut].sort().values
    yeni = mlp(gizli=(tut, W2.shape[0]))
    with torch.no_grad():
        yeni[0].weight.copy_(W0[idx])
        yeni[0].bias.copy_(b0[idx])
        yeni[2].weight.copy_(W2[:, idx])
        yeni[2].bias.copy_(b2)
        yeni[4].weight.copy_(model[4].weight)
        yeni[4].bias.copy_(model[4].bias)
    return yeni


def seyreklik_taramasi(satirlar):
    oranlar = [0.0, 0.5, 0.8, 0.9, 0.95, 0.98]
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        for o in oranlar:
            m = copy.deepcopy(base)
            mk = maskeler_olustur(m, o)
            uygula_maske(m, mk)
            budamasiz = dogruluk(m, Xte, yte)
            if o > 0:
                egit(
                    m,
                    Xtr,
                    ytr,
                    epoch=20,
                    lr=1e-3,
                    tohum=t,
                    maskeler=mk,
                )
            ince = dogruluk(m, Xte, yte)
            satirlar.append(
                dict(
                    oran=o,
                    tohum=t,
                    budamasiz=round(budamasiz, 4),
                    ince_ayar=round(ince, 4),
                    gercek_seyreklik=round(seyreklik(m), 4),
                )
            )
            print(
                "tohum %d oran %.2f  budamasiz=%.4f  ince_ayar=%.4f  "
                "seyreklik=%.3f"
                % (t, o, budamasiz, ince, seyreklik(m))
            )


def yinelemeli_karsilastirma():
    """%95 seyreklik: tek adim (40 epoch) ve 4 adim kubik."""
    sf = 0.95
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        tek = copy.deepcopy(base)
        mk = maskeler_olustur(tek, sf)
        uygula_maske(tek, mk)
        egit(tek, Xtr, ytr, epoch=40, lr=1e-3, tohum=t, maskeler=mk)
        yin = copy.deepcopy(base)
        for s in range(1, 5):
            mk = maskeler_olustur(yin, kubik(sf, s, 4))
            uygula_maske(yin, mk)
            egit(
                yin, Xtr, ytr, epoch=10, lr=1e-3, tohum=t, maskeler=mk
            )
        print(
            "tohum %d  tek_adim=%.4f  yinelemeli=%.4f  "
            "seyreklik=%.3f/%.3f"
            % (
                t,
                dogruluk(tek, Xte, yte),
                dogruluk(yin, Xte, yte),
                seyreklik(tek),
                seyreklik(yin),
            )
        )


def piyango_bileti():
    """Ayni maske: (a) baslangic agirliklari, (b) rastgele yeniden
    baslat. Ikisini ayni maskeyle yeniden egit."""
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        torch.manual_seed(t)
        theta0 = mlp()
        st0 = copy.deepcopy(theta0.state_dict())
        egit(theta0, Xtr, ytr, tohum=t)
        mk = maskeler_olustur(theta0, 0.8)
        lt = mlp()
        lt.load_state_dict(st0)
        uygula_maske(lt, mk)
        egit(lt, Xtr, ytr, epoch=60, tohum=t, maskeler=mk)
        torch.manual_seed(t + 100)
        ras = mlp()
        uygula_maske(ras, mk)
        egit(ras, Xtr, ytr, epoch=60, tohum=t + 100, maskeler=mk)
        print(
            "tohum %d  bilet(geri sarma)=%.4f  rastgele=%.4f"
            % (t, dogruluk(lt, Xte, yte), dogruluk(ras, Xte, yte))
        )


def kanal_dogruluk(satirlar):
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        k = kanal_buda(base, 0.5)
        a0 = dogruluk(k, Xte, yte)
        egit(k, Xtr, ytr, epoch=20, lr=1e-3, tohum=t)
        a1 = dogruluk(k, Xte, yte)
        print(
            "tohum %d  kanal %%50: budamasiz=%.4f  ince_ayar=%.4f"
            % (t, a0, a1)
        )


def ileri_csr(Ws, bs, x):
    """Seyrek (CSR) agirliklarla ileri gecis: h = W h + b, ara ReLU.
    """
    h = x.T
    for j, (W, b) in enumerate(zip(Ws, bs)):
        h = torch.sparse.mm(W, h) + b.view(-1, 1)
        if j < len(Ws) - 1:
            h = torch.relu(h)
    return h.T


def hiz_olcumu():
    torch.manual_seed(0)
    base = mlp(gizli=(2048, 2048)).eval()
    x = torch.randn(1, 64)
    satirlar = []

    def kaydet(ad, model_fn, etkin):
        with torch.no_grad():
            med, p95 = zamanla(model_fn, n=300, isinma=30)
        satirlar.append(
            dict(
                yontem=ad,
                etkin_parametre=etkin,
                medyan_ms=round(med, 4),
                p95_ms=round(p95, 4),
            )
        )
        print(
            "%-26s etkin=%8d medyan=%.4f ms  p95=%.4f ms"
            % (ad, etkin, med, p95)
        )

    toplam = sum(p.numel() for p in base.parameters())
    kaydet("yogun_fp32", lambda: base(x), toplam)
    for o in [0.5, 0.8, 0.9, 0.95]:
        s = copy.deepcopy(base)
        mk = maskeler_olustur(s, o)
        uygula_maske(s, mk)
        etkin = sum(int((s[i].weight != 0).sum()) for i in KATMANLAR)
        Ws = [
            (s[i].weight * mk[i]).to_sparse_csr() for i in KATMANLAR
        ]
        bs = [s[i].bias.detach() for i in KATMANLAR]
        with torch.no_grad():
            fark = (ileri_csr(Ws, bs, x) - s(x)).abs().max().item()
        print(
            "seyreklik %.2f  CSR dogrulama en buyuk fark: %.2e"
            % (o, fark)
        )
        kaydet(
            "yapilandirilmamis_%d_yogun" % round(o * 100),
            lambda: s(x),
            etkin,
        )
        kaydet(
            "yapilandirilmamis_%d_csr" % round(o * 100),
            lambda: ileri_csr(Ws, bs, x),
            etkin,
        )
    k50 = kanal_buda(base, 0.5).eval()
    kaydet(
        "yapilandirilmis_kanal_50",
        lambda: k50(x),
        sum(p.numel() for p in k50.parameters()),
    )
    return satirlar


if __name__ == "__main__":
    torch.set_num_threads(4)
    torch_ile_dogrula()
    satirlar = []
    seyreklik_taramasi(satirlar)
    yaz = os.path.join(VERI, "b75_seyreklik.csv")
    with open(yaz, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", yaz)
    yinelemeli_karsilastirma()
    piyango_bileti()
    kanal_dogruluk(satirlar)
    hiz = hiz_olcumu()
    yaz = os.path.join(VERI, "b75_hiz.csv")
    with open(yaz, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hiz[0].keys()))
        w.writeheader()
        w.writerows(hiz)
    print("CSV yazildi:", yaz)
