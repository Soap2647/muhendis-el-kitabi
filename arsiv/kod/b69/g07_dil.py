# -*- coding: utf-8 -*-
"""Bölüm 69 - Karakter düzeyi decoder-only dil modeli."""

import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tr69 import Model, tohum

KOK = "D:/Mevcut Projeler/Kitap"
T = 64  # bağlam uzunluğu
BATCH = 32
ADIM = 1500
TOHUMLAR = [0, 1, 2]


def korpus():
    """Kitabın bölümlerinden düz metin (kod ve tablo atılır)."""
    satirlar, kod = [], False
    for no in ["48", "51"]:
        yol = os.path.join(KOK, "bolumler", "bolum_%s.md" % no)
        for s in open(yol, encoding="utf-8"):
            s = s.strip()
            if s.startswith("```"):
                kod = not kod
                continue
            if kod or not s or s[0] in "#|%!:-$":
                continue
            satirlar.append(s)
    metin = " ".join(satirlar)
    return metin.replace("**", "").replace("`", "")


def egit(model, veri, rng, lr, isinma, adim=ADIM):
    opt = torch.optim.AdamW(
        model.parameters(), lr=lr, weight_decay=0.01
    )

    def cizelge(a):
        if a < isinma:  # doğrusal ısınma
            return (a + 1) / isinma
        ilerleme = (a - isinma) / max(1, adim - isinma)
        return 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * ilerleme))

    sched = torch.optim.lr_scheduler.LambdaLR(opt, cizelge)
    kayip_son = []
    for a in range(adim):
        i = rng.integers(0, len(veri) - T - 1, size=BATCH)
        x = torch.stack([veri[k : k + T] for k in i])
        y = torch.stack([veri[k + 1 : k + T + 1] for k in i])
        model.train()
        loss = F.cross_entropy(
            model(x).reshape(-1, model.cikis.out_features),
            y.reshape(-1),
        )
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if a >= adim - 100:
            kayip_son.append(float(loss))
    return float(np.mean(kayip_son)) if kayip_son else float("nan")


def ppl(model, veri):
    """Pencereleri üst üste binmeden değerlendir."""
    model.eval()
    xs, ys = [], []
    for i in range(0, len(veri) - T - 1, T):
        xs.append(veri[i : i + T])
        ys.append(veri[i + 1 : i + T + 1])
    x, y = torch.stack(xs), torch.stack(ys)
    with torch.no_grad():
        kayip = 0.0
        for b in range(0, len(x), 64):
            lo = model(x[b : b + 64])
            kayip += float(
                F.cross_entropy(
                    lo.reshape(-1, lo.shape[-1]),
                    y[b : b + 64].reshape(-1),
                    reduction="sum",
                )
            )
    return math.exp(kayip / y.numel())


def bigram_ppl(egitim, dogrulama, V, alfa=0.1):
    C = np.full((V, V), alfa)
    for a, b in zip(egitim[:-1], egitim[1:]):
        C[a, b] += 1
    P = C / C.sum(axis=1, keepdims=True)
    nll = -np.log(P[dogrulama[:-1], dogrulama[1:]]).mean()
    return math.exp(nll)


@torch.no_grad()
def uret(model, sozluk, karakterler, baslangic, n, sicaklik, seed):
    model.eval()
    gen = torch.Generator().manual_seed(seed)
    ctx = torch.tensor([sozluk[c] for c in baslangic])[None]
    for _ in range(n):
        lo = model(ctx[:, -T:])[0, -1] / sicaklik
        p = torch.softmax(lo, dim=-1)
        nxt = torch.multinomial(p, 1, generator=gen)
        ctx = torch.cat([ctx, nxt[None]], dim=1)
    return "".join(karakterler[int(i)] for i in ctx[0])


if __name__ == "__main__":
    metin = korpus()
    karakterler = sorted(set(metin))
    V = len(karakterler)
    sozluk = {c: i for i, c in enumerate(karakterler)}
    veri = torch.tensor([sozluk[c] for c in metin], dtype=torch.long)
    n = int(0.9 * len(veri))
    egitim, dogrulama = veri[:n], veri[n:]
    print("Metin uzunluğu: %d karakter, sözlük: %d" % (len(metin), V))
    print("Eğitim: %d, doğrulama: %d karakter" % (n, len(dogrulama)))
    bp = bigram_ppl(egitim.numpy(), dogrulama.numpy(), V)
    print("Bigram taban çizgisi (doğrulama perplexity): %.3f" % bp)

    konfig = [
        ("pre-norm + ısınma (ana)", "pre", 200, 3e-3),
        ("pre-norm, ısınma yok", "pre", 0, 3e-3),
        ("post-norm + ısınma", "post", 200, 3e-3),
        ("post-norm, ısınma yok", "post", 0, 3e-3),
    ]
    ana = None
    for ad, norm, isinma, lr in konfig:
        vals, egit_kay = [], []
        for s in TOHUMLAR:
            tohum(s)
            model = Model(
                V,
                d=64,
                h=4,
                L=2,
                maxT=T,
                konum="sin",
                norm=norm,
                cift=False,
                drop=0.1,
            )
            t0 = time.time()
            ek = egit(
                model,
                egitim,
                np.random.default_rng(s),
                lr,
                max(isinma, 1),
            )
            p = ppl(model, dogrulama)
            vals.append(p)
            egit_kay.append(ek)
            print(
                "%-24s t=%d ppl=%.3f kayip=%.3f %.0fs"
                % (ad, s, p, ek, time.time() - t0)
            )
            if s == 0 and norm == "pre" and isinma == 200:
                ana = model
        v = np.array(vals)
        print(
            ">> %s: ppl %.3f ± %.3f" % (ad, v.mean(), v.std(ddof=1))
        )
    print(
        "Parametre sayısı (ana model):",
        sum(p.numel() for p in ana.parameters()),
    )
    print("--- Örnek üretim (ana model, tohum 0) ---")
    istem = metin[n : n + 20]  # doğrulama metninden istem
    for sic in [0.7, 1.0]:
        cik = uret(ana, sozluk, karakterler, istem, 120, sic, seed=3)
        duz = cik.replace("\n", " ")
        print("sicaklik=%.1f:" % sic)
        for k in range(0, len(duz), 70):
            print(duz[k : k + 70])
