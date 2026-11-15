# -*- coding: utf-8 -*-
"""Deney 10: tek batch'e asiri uydurma testi ve kasitli hatalar.

Ayni 32 ornek, ayni model, ayni optimizer; yalnizca bir hata enjekte
edilir. Dogru kod sifira yakin kayip vermeli; hata varsa belirti olcu-
lur. Tohum 0."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from ortak64 import veri, mlp, csv_yaz

D = veri()
Xtr, ytr = D[0][:32], D[1][:32]
ADIM = 500


def kos(ad, hata=None, adim=ADIM):
    torch.manual_seed(0)
    m = mlp(gizli=128)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    x, y = Xtr, ytr
    if hata == "etiket_kaydi":
        y = ytr[
            torch.randperm(
                32, generator=torch.Generator().manual_seed(3)
            )
        ]
    gecmis = []
    for k in range(adim):
        if hata != "zero_grad_yok":
            opt.zero_grad()
        out = m(x)
        if hata == "cift_softmax":
            out = torch.softmax(out, 1)
        loss = F.cross_entropy(out, y)
        loss.backward()
        opt.step()
        if k % 100 == 0 or k == adim - 1:
            gecmis.append((k, loss.item()))
    acc = (m(x).argmax(1) == y).float().mean().item()
    print("%-13s %s" % (ad, " ".join("%d:%.3f" % g for g in gecmis)))
    print("%-13s dogruluk=%.3f" % ("", acc))
    return gecmis, acc


print("Tek batch testi (32 ornek, Adam 1e-3, 500 adim):")
sat = []
for ad, hata in [
    ("dogru", None),
    ("cift_softmax", "cift_softmax"),
    ("etiket_kaydi", "etiket_kaydi"),
    ("zero_grad_yok", "zero_grad_yok"),
]:
    gec, acc = kos(ad, hata)
    for k, l in gec:
        sat.append((ad, k, "%.6f" % l))
csv_yaz("b64_tek_batch.csv", sat, ["vaka", "adim", "kayip"])

# Eval modu unutulursa: dropout ve BN
torch.manual_seed(0)
m = mlp(gizli=256, dropout=0.5)
opt = torch.optim.Adam(m.parameters(), lr=1e-3)
Xa, ya = veri()[0], veri()[1]
for ep in range(10):
    m.train()
    for i in range(0, len(Xa), 32):
        opt.zero_grad()
        F.cross_entropy(m(Xa[i : i + 32]), ya[i : i + 32]).backward()
        opt.step()
Xv = veri()[2]
m.train()  # eval() unutuldu
p1 = m(Xv).argmax(1)
p2 = m(Xv).argmax(1)
print(
    "\nDropout acik (eval unutuldu): tahmin farki = %d / 360"
    % (p1 != p2).sum().item()
)
m.eval()
q1 = m(Xv).argmax(1)
q2 = m(Xv).argmax(1)
print(
    "Dogru eval modu: iki tahmin arasi fark = %d"
    % (q1 != q2).sum().item()
)

torch.manual_seed(0)
bn = mlp(gizli=128, bn=True)
opt = torch.optim.Adam(bn.parameters(), lr=1e-3)
for ep in range(10):
    bn.train()
    for i in range(0, len(Xa), 32):
        opt.zero_grad()
        F.cross_entropy(bn(Xa[i : i + 32]), ya[i : i + 32]).backward()
        opt.step()
bn.train()
t_mod = bn(Xv).argmax(1)
bn.eval()
e_mod = bn(Xv).argmax(1)
print(
    "BN: train modunda ve eval modunda tahmin farki = %d / 360"
    % (t_mod != e_mod).sum().item()
)
bn.train()
ya_acc = (bn(Xv).argmax(1) == veri()[3]).float().mean().item()
bn.eval()
yb_acc = (bn(Xv).argmax(1) == veri()[3]).float().mean().item()
print(
    "BN dogrulama dogrulugu: train modunda=%.4f, eval modunda=%.4f"
    % (ya_acc, yb_acc)
)
