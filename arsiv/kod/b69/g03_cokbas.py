# -*- coding: utf-8 -*-
"""Bölüm 69 - Çok başlı attention: bölme ve parametre."""

import math
import torch
import torch.nn as nn
from tr69 import Dikkat, Blok, tohum

torch.set_default_dtype(torch.float64)


def parametre(modul):
    return sum(p.numel() for p in modul.parameters())


def bolme_testi(d=8, h=2, T=3):
    print("--- Bolme ve birlestirme (d=%d, h=%d) ---" % (d, h))
    tohum(0)
    m = Dikkat(d, h)
    x = torch.randn(1, T, d)
    q = m.wq(x)
    bolunmus = m._bol(q)
    print("wq(x)          :", tuple(q.shape))
    print("_bol(wq(x))    :", tuple(bolunmus.shape), "(B, h, T, dh)")
    # Her baş bağımsız hesaplanır, sonra yan yana konur.
    basli = []
    for j in range(h):
        sl = slice(j * m.dh, (j + 1) * m.dh)
        qj, kj, vj = (
            m.wq(x)[..., sl],
            m.wk(x)[..., sl],
            m.wv(x)[..., sl],
        )
        s = qj @ kj.transpose(-2, -1) / math.sqrt(m.dh)
        basli.append(torch.softmax(s, dim=-1) @ vj)
    birlesik = torch.cat(basli, dim=-1)  # (B, T, d)
    tam, _ = m(x, x)
    print(
        "tek tek baslar birlestirilince fark:",
        float(
            (birlesik @ m.wo.weight.T - (tam - m.wo.bias)).abs().max()
        ),
    )
    print("baslarin cikti boyutu:", tuple(birlesik.shape))


def torch_eslesme(d=64, h=4, T=7):
    print(
        "--- nn.MultiheadAttention ile ayni agirliklarla eslesme ---"
    )
    tohum(1)
    mine = Dikkat(d, h)
    ref = nn.MultiheadAttention(d, h, batch_first=True)
    with torch.no_grad():
        ref.in_proj_weight.copy_(
            torch.cat(
                [mine.wq.weight, mine.wk.weight, mine.wv.weight]
            )
        )
        ref.in_proj_bias.copy_(
            torch.cat([mine.wq.bias, mine.wk.bias, mine.wv.bias])
        )
        ref.out_proj.weight.copy_(mine.wo.weight)
        ref.out_proj.bias.copy_(mine.wo.bias)
    x = torch.randn(2, T, d)
    m = torch.tril(torch.ones(T, T, dtype=torch.bool))
    a, _ = mine(x, x, m)
    b, _ = ref(x, x, x, attn_mask=~m, need_weights=False)
    print("maks farki (nedensel):", float((a - b).abs().max()))


def parametre_sayimi():
    print("--- Parametre sayimi: 4 (d^2 + d) ---")
    for d, h in [(64, 1), (64, 4), (64, 8), (128, 8)]:
        m = Dikkat(d, h)
        print(
            "d=%3d h=%d  gercek=%6d  formul=%6d"
            % (d, h, parametre(m), 4 * (d * d + d))
        )
    print("--- Tam blok (pre-norm, capraz yok), d=64, h=4 ---")
    b = Blok(64, 4, "pre", 0.0, False)
    dikkat = parametre(b.oz)
    mlp = parametre(b.ff)
    norm = parametre(b.ln1) + parametre(b.ln2) + parametre(b.ln3)
    print(
        "dikkat=%d  MLP=%d  LayerNorm=%d  toplam=%d"
        % (dikkat, mlp, norm, parametre(b))
    )


if __name__ == "__main__":
    bolme_testi()
    torch_eslesme()
    parametre_sayimi()
