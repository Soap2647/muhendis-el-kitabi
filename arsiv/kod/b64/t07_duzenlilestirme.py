# -*- coding: utf-8 -*-
"""Deney 7: dropout, agirlik azaltma, etiket yumusatma,
erken durdurma.

Her varyant 5 tohumla. 'Egitim dogrulugu' egitim kumesinde (cikarim
modu) olculur; test sonucu ayri, hic secimde kullanilmamis kumedendir.
"""

import numpy as np
import torch
import torch.nn.functional as F
from ortak64 import (
    veri,
    mlp,
    egit,
    olc,
    csv_yaz,
    SEEDS,
    ortalama_sapma,
)


def ece(model, X, y, kutu=15):
    """Beklenen kalibrasyon hatasi (ECE): guven ile dogruluk farki."""
    model.eval()
    with torch.no_grad():
        p = F.softmax(model(X), dim=1)
    guven, tahmin = p.max(1)
    dogru = (tahmin == y).float()
    e = 0.0
    for b in range(kutu):
        lo, hi = b / kutu, (b + 1) / kutu
        m = (guven > lo) & (guven <= hi)
        if m.any():
            e += m.float().mean().item() * abs(
                dogru[m].mean().item() - guven[m].mean().item()
            )
    return e


D = veri()
VARYANT = {
    "temel (dropout 0, wd 0)": dict(dropout=0.0, wd=0.0, ls=0.0),
    "dropout 0.2": dict(dropout=0.2, wd=0.0, ls=0.0),
    "dropout 0.5": dict(dropout=0.5, wd=0.0, ls=0.0),
    "AdamW wd=0.1": dict(dropout=0.0, wd=0.1, ls=0.0),
    "etiket yumusatma 0.1": dict(dropout=0.0, wd=0.0, ls=0.1),
}
satir = []
print("256x2 MLP, Adam lr=1e-3, batch 32, 60 epoch, 5 tohum")
print("(test kumesi: 360 ornek; egitim dogrulugu: cikarim modu)\n")
for ad, c in VARYANT.items():
    tr_acc, te_acc, ec, en_iyi = [], [], [], []
    for s in SEEDS:
        torch.manual_seed(s)
        m = mlp(gizli=256, dropout=c["dropout"])
        if c["wd"] > 0:
            opt = torch.optim.AdamW(
                m.parameters(), lr=1e-3, weight_decay=c["wd"]
            )
        else:
            opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        h = egit(m, opt, D, epochs=60, batch=32, seed=s, ls=c["ls"])
        m.eval()
        with torch.no_grad():
            tr_acc.append(
                (m(D[0]).argmax(1) == D[1]).float().mean().item()
            )
        te_acc.append(h["test_acc"])
        ec.append(ece(m, D[4], D[5]))
        en_iyi.append(h["en_iyi_ep"])
    a, sa = ortalama_sapma(tr_acc)
    b, sb = ortalama_sapma(te_acc)
    e, se = ortalama_sapma(ec)
    print("%-24s egitim=%.4f+-%.4f" % (ad, a, sa))
    print("%24s test=%.4f+-%.4f ECE=%.4f+-%.4f" % ("", b, sb, e, se))
    print("%24s en iyi ep (val)=%s" % ("", en_iyi))
    satir.append(
        (
            ad,
            "%.4f" % a,
            "%.4f" % b,
            "%.4f" % sb,
            "%.4f" % e,
            "%.4f" % se,
        )
    )
csv_yaz(
    "b64_duzenlilestirme.csv",
    satir,
    [
        "varyant",
        "egitim_acc",
        "test_ort",
        "test_sd",
        "ece_ort",
        "ece_sd",
    ],
)
