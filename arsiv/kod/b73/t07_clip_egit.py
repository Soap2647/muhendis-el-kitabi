# -*- coding: utf-8 -*-
"""Bolum 73 - t07: mini-CLIP egitimi (sentetik goruntu-metin
ciftleri).

Egitim kumesinde (mavi, ucgen) kombinasyonu HIC yoktur (bilesimsel
genelleme testi icin). Iki varyant:
  naif   : ayni aciklamali ornekler birbirinin negatifi sayilir,
  maskeli: ayni aciklamali ornekler pozitif kabul edilir (yumusak
  hedef).
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from synth73 import KELIMELER, UZUN, aciklama, belirtec, ornekler
from ortak73 import AYG, Enkoder, tekrar

CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ckpt")
MAVI, UCGEN = 2, 2
izin = {(r, s) for r in range(4) for s in range(4)} - {(MAVI, UCGEN)}
rng = np.random.default_rng(75)
Xp, R, S, B, K = ornekler(20000, rng, izin=izin)
METIN = [aciklama(R[i], B[i], S[i], K[i]) for i in range(len(R))]
TOK = np.array([belirtec(m) for m in METIN])
CID = R * 40 + B * 20 + S * 5 + K  # ayni aciklama <=> ayni kimlik


class GoruntuKod(nn.Module):
    def __init__(self):
        super().__init__()
        self.govde = Enkoder()
        self.cik = nn.Linear(256, 128)

    def forward(self, x):
        return self.cik(self.govde(x))


class MetinKod(nn.Module):
    def __init__(self, V, d=128):
        super().__init__()
        self.gom = nn.Embedding(V, d, padding_idx=0)
        self.konum = nn.Parameter(0.02 * torch.randn(1, UZUN, d))
        self.kod = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d, 4, 256, batch_first=True),
            2,
            enable_nested_tensor=False,
        )
        self.cik = nn.Linear(d, 128)

    def forward(self, ids):
        pad = ids == 0
        h = self.kod(
            self.gom(ids) + self.konum, src_key_padding_mask=pad
        )
        keep = (~pad).float().unsqueeze(-1)
        ort = (h * keep).sum(1) / keep.sum(1).clamp(min=1.0)
        return self.cik(ort)


@tekrar()
def egit_clip(maskeli, adim=4000, bs=256, tohum=0):
    torch.manual_seed(tohum)
    gk = GoruntuKod().to(AYG)
    mk = MetinKod(len(KELIMELER)).to(AYG)
    ls = nn.Parameter(
        torch.tensor(float(np.log(1 / 0.07)), device=AYG)
    )
    ps = list(gk.parameters()) + list(mk.parameters()) + [ls]
    opt = torch.optim.Adam(ps, lr=3e-4)
    X = torch.as_tensor(Xp, device=AYG)
    T = torch.as_tensor(TOK, device=AYG)
    C = torch.as_tensor(CID, device=AYG)
    gk.train()
    mk.train()
    for _ in range(adim):
        idx = torch.randint(0, len(X), (bs,), device=AYG)
        zi = F.normalize(gk(X[idx]), dim=1)
        zt = F.normalize(mk(T[idx]), dim=1)
        logit = ls.exp().clamp(max=100.0) * (zi @ zt.t())
        if maskeli:
            P = (C[idx][:, None] == C[idx][None, :]).float()
        else:
            P = torch.eye(bs, device=AYG)
        P = P / P.sum(1, keepdim=True)
        kayip = (
            -(P * F.log_softmax(logit, 1)).sum(1).mean() / 2
            - (P * F.log_softmax(logit.t(), 1)).sum(1).mean() / 2
        )
        opt.zero_grad(set_to_none=True)
        kayip.backward()
        opt.step()
    gk.eval()
    mk.eval()
    return gk, mk


if __name__ == "__main__":
    print("kalan benzersiz aciklama:", len(set(METIN)))
    print(
        "egitim cifti:",
        len(METIN),
        " (mavi ucgen yok:",
        not np.any((R == MAVI) & (S == UCGEN)),
        ")",
    )
    for ad, maskeli in (("naif", False), ("maskeli", True)):
        gk, mk = egit_clip(maskeli)
        torch.save(
            {"gk": gk.state_dict(), "mk": mk.state_dict()},
            os.path.join(CK, "clip_%s.pt" % ad),
        )
        print(ad, "kaydedildi", flush=True)
