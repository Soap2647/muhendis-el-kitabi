# -*- coding: utf-8 -*-
"""Bolum 75: PTQ, QAT, PyTorch dinamik int8 (3 tohum).
"""

import copy, io, os, csv, time, statistics as st
import numpy as np
import torch
import torch.nn as nn
from b75_ortak import (
    veri,
    mlp_t,
    egit,
    dogruluk,
    simetrik_olcek,
    qdq,
    SahteKuantFn,
    TOHUMLAR,
)

CIKTI = "D:/Mevcut Projeler/Kitap/engine/veri/b75_bit_dogruluk.csv"


class ActQ(nn.Module):
    """Girdi aktivasyonunu sabit (kalibre) olcekle kuantize eder.
    """

    def __init__(self, s, bits):
        super().__init__()
        self.register_buffer("s", s)
        self.bits = bits

    def forward(self, x):
        return qdq(x, self.s, self.bits)


class QATLinear(nn.Module):
    """Egitim sirasinda sahte kuantizasyon: agirlik (kanal basina) +
    girdi.
    """

    def __init__(self, lin, wbits, abits, sa):
        super().__init__()
        self.weight = nn.Parameter(lin.weight.data.clone())
        self.bias = nn.Parameter(lin.bias.data.clone())
        self.wbits, self.abits, self.sa = wbits, abits, sa

    def forward(self, x):
        s = simetrik_olcek(
            self.weight.detach(), self.wbits, kanal=True
        )
        w = SahteKuantFn.apply(self.weight, s, self.wbits)
        if self.abits and self.abits < 32:
            x = SahteKuantFn.apply(x, self.sa, self.abits)
        return nn.functional.linear(x, w, self.bias)


def girdi_olcekleri(base, Xcal, p, bits=8):
    """Her Linear'in girdisi icin simetrik olcek: max (p=1.0) ya da
    yuzdelik.
    """
    lv = 2 ** (bits - 1) - 1
    lins = [i for i, l in enumerate(base) if isinstance(l, nn.Linear)]
    biriken = {i: [] for i in lins}
    kancalar = [
        base[i].register_forward_pre_hook(
            lambda m, g, i=i: biriken[i].append(
                g[0].detach().abs().flatten()
            )
        )
        for i in lins
    ]
    with torch.no_grad():
        base(Xcal)
    for k in kancalar:
        k.remove()
    olcekler = {}
    for i in lins:
        v = torch.cat(biriken[i])
        q = v.max() if p >= 1.0 else torch.quantile(v, p)
        olcekler[i] = (q.clamp_min(1e-8) / lv).reshape(())
    return olcekler


def ptq(base, wbits, abits, kanal, Xcal, p=1.0):
    """abits=32 ya da None: aktivasyon kuantizasyonu yok."""
    akt = abits is not None and abits < 32
    m = copy.deepcopy(base)
    sa = girdi_olcekleri(base, Xcal, p, abits) if akt else {}
    katman = []
    for i, l in enumerate(m):
        if isinstance(l, nn.Linear):
            if wbits < 32:
                s = simetrik_olcek(l.weight.data, wbits, kanal)
                l.weight.data = qdq(l.weight.data, s, wbits)
            if akt:
                katman.append(ActQ(sa[i], abits))
        katman.append(l)
    return nn.Sequential(*katman)


def qat(base, wbits, abits, Xcal, Xtr, ytr, tohum):
    akt = abits < 32
    sa = girdi_olcekleri(base, Xcal, 0.999, abits) if akt else {}
    katman = []
    for i, l in enumerate(base):
        if isinstance(l, nn.Linear):
            katman.append(QATLinear(l, wbits, abits, sa.get(i)))
        else:
            katman.append(l)
    m = nn.Sequential(*katman)
    egit(m, Xtr, ytr, epoch=20, lr=1e-4, tohum=tohum)
    return m


def agirlik_bayt(model, wbits):
    bayt = 0
    for l in model:
        if isinstance(l, (nn.Linear, QATLinear)):
            bayt += l.weight.numel() * wbits / 8 + l.bias.numel() * 4
    return bayt


def boyut_bayt(model):
    tampon = io.BytesIO()
    torch.save(model.state_dict(), tampon)
    return tampon.getbuffer().nbytes


def main():
    satirlar = []
    for t in TOHUMLAR:
        Xtr, ytr, Xte, yte = veri(t)
        Xcal = Xtr[-200:]
        base = mlp_t(t)
        egit(base, Xtr, ytr, tohum=t)
        fp = dogruluk(base, Xte, yte)
        P = sum(p.numel() for p in base.parameters())
        dinamik = torch.ao.quantization.quantize_dynamic(
            copy.deepcopy(base), {nn.Linear}, dtype=torch.qint8
        )
        if t == 0:
            s_max = girdi_olcekleri(base, Xcal, 1.0)
            s_p = girdi_olcekleri(base, Xcal, 0.999)
            for i in s_max:
                print(
                    "katman %d girdi olcegi: max=%.4f "
                    "p99.9=%.4f oran=%.1f"
                    % (i, s_max[i], s_p[i], float(s_max[i] / s_p[i]))
                )
        yontemler = [
            ("fp32", 32, 32, None),
            ("PTQ_w8_kanal", 8, 32, dict(kanal=True)),
            ("PTQ_w8a8_tensor_max", 8, 8, dict(kanal=False, p=1.0)),
            (
                "PTQ_w8a8_tensor_p999",
                8,
                8,
                dict(kanal=False, p=0.999),
            ),
            ("PTQ_w4_tensor", 4, 32, dict(kanal=False)),
            ("PTQ_w4_kanal", 4, 32, dict(kanal=True)),
            ("QAT_w4_kanal", 4, 32, "qat"),
            ("PTQ_w3_kanal", 3, 32, dict(kanal=True)),
            ("QAT_w3_kanal", 3, 32, "qat"),
            ("PTQ_w2_kanal", 2, 32, dict(kanal=True)),
            ("QAT_w2_kanal", 2, 32, "qat"),
            ("PTQ_w4a8_kanal_p999", 4, 8, dict(kanal=True, p=0.999)),
            ("QAT_w4a8_kanal", 4, 8, "qat"),
            ("PyTorch_dinamik_int8", 8, 8, "dyn"),
        ]
        for ad, wb, ab, opt in yontemler:
            if ad == "fp32":
                m, acc = base, fp
                bayt = P * 4
            elif opt == "dyn":
                m = dinamik
                acc = dogruluk(m, Xte, yte)
                bayt = boyut_bayt(m)
            elif opt == "qat":
                m = qat(base, wb, ab, Xcal, Xtr, ytr, t)
                acc = dogruluk(m, Xte, yte)
                bayt = agirlik_bayt(m, wb)
            else:
                m = ptq(
                    base,
                    wb,
                    ab,
                    opt["kanal"],
                    Xcal,
                    opt.get("p", 1.0),
                )
                acc = dogruluk(m, Xte, yte)
                bayt = agirlik_bayt(m, wb)
            satirlar.append(
                dict(
                    yontem=ad,
                    wbit=wb,
                    abit=ab,
                    tohum=t,
                    dogruluk=round(acc, 4),
                    bayt=int(bayt),
                )
            )
            print(
                "tohum %d  %-22s acc=%.4f  bayt=%d"
                % (t, ad, acc, bayt)
            )
    os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
    with open(CIKTI, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
    print("CSV yazildi:", CIKTI)
    print("\nOzet (ortalama +- sapma, 3 tohum):")
    for ad in dict.fromkeys(s["yontem"] for s in satirlar):
        d = [s["dogruluk"] for s in satirlar if s["yontem"] == ad]
        b = [s["bayt"] for s in satirlar if s["yontem"] == ad][0]
        print(
            "%-22s %.4f +- %.4f  bayt=%d"
            % (ad, st.mean(d), st.pstdev(d), b)
        )


if __name__ == "__main__":
    t0 = time.time()
    main()
    print("sure: %.1f s" % (time.time() - t0))
