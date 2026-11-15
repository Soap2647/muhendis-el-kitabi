# -*- coding: utf-8 -*-
"""Bölüm 69 - Dizi ters çevirme: Transformer konum türleri ve LSTM."""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tr69 import Model, greedy_seq2seq, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
V, BOS, EOS = 16, 1, 2  # 3..15 arasi semboller
ADIM = 2000
EGITIM_L = (4, 12)  # egitimde uzunluk 4..12
TEST_L = [4, 8, 12, 16, 20, 24]  # 13 ve sonrasi: egitim disi
TOHUMLAR = [0, 1, 2]


class LSTMAy(nn.Module):
    """Bölüm 68'deki tipte LSTM encoder-decoder (dikkatsiz)."""

    def __init__(self, d=64, hid=128):
        super().__init__()
        self.emb = nn.Embedding(V, d)
        self.enc = nn.LSTM(d, hid, batch_first=True)
        self.dec = nn.LSTM(d, hid, batch_first=True)
        self.cikis = nn.Linear(hid, V)

    def forward(self, x, src):
        _, durum = self.enc(self.emb(src))  # sabit boyutlu bağlam
        h, _ = self.dec(self.emb(x), durum)
        return self.cikis(h)


def grup(rng, L, n):
    src = rng.integers(3, V, size=(n, L))
    tin = np.concatenate([np.full((n, 1), BOS), src[:, ::-1]], axis=1)
    tout = np.concatenate(
        [src[:, ::-1], np.full((n, 1), EOS)], axis=1
    )
    return (torch.tensor(src), torch.tensor(tin), torch.tensor(tout))


def egit(model, rng):
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    # ilk 100 adımda öğrenme oranı doğrusal artar, sonra sabit kalır
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda a: min(1.0, (a + 1) / 100)
    )
    for _ in range(ADIM):
        L = int(rng.integers(EGITIM_L[0], EGITIM_L[1] + 1))
        src, tin, tout = grup(rng, L, 64)
        model.train()
        logits = model(tin, src)
        loss = F.cross_entropy(
            logits.reshape(-1, V), tout.reshape(-1)
        )
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
    return float(loss)


def dogruluk(model, L, n=300):
    """Dizi düzeyi doğruluk: EOS dahil tüm belirteçler doğru mu?"""
    src, _, tout = grup(np.random.default_rng(1000 + L), L, n)
    tahmin = greedy_seq2seq(model, src, L + 1)
    return float((tahmin == tout).all(dim=1).float().mean())


def dikkat_analizi(model, L=10, n=200):
    """Başlar ne yapıyor? Önceki belirteç, kendisi ve ters köşegen."""
    src, tin, _ = grup(np.random.default_rng(7), L, n)
    model.eval()
    with torch.no_grad():
        model(tin, src)
    A_enc = model.enc[0].oz.son_A  # (B, h, L, L)
    A_cap = model.dec[-1].capraz.son_A  # (B, h, L+1, L)
    print("baş | enc:önceki | enc:kendisi | çapraz:ters köşegen")
    for h in range(A_enc.shape[1]):
        onceki = float(A_enc[:, h, 1:, :].diagonal(-1, -2, -1).mean())
        kendi = float(A_enc[:, h].diagonal(0, -2, -1).mean())
        ters = float(
            torch.stack(
                [A_cap[:, h, t, L - 1 - t] for t in range(L)]
            ).mean()
        )
        print(
            "%3d | %11.3f | %11.3f | %19.3f"
            % (h, onceki, kendi, ters)
        )
    satirlar = []
    for h in range(A_cap.shape[1]):
        for t in range(A_cap.shape[2]):
            for j in range(L):
                satirlar.append(
                    [h, t, j, "%.4f" % float(A_cap[0, h, t, j])]
                )
    with open(
        os.path.join(VERI, "b69_attn_ters.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["bas", "satir", "sutun", "agirlik"])
        w.writerows(satirlar)


def main():
    sonuc = {}
    parametre = {}
    sure = {}
    modeller = {}
    konfig = {
        "Transformer sinüzoidal": dict(konum="sin"),
        "Transformer öğrenilen": dict(konum="ogr"),
        "Transformer RoPE": dict(konum="rope"),
        "Transformer konumsuz": dict(konum="yok"),
    }
    for ad, kw in list(konfig.items()) + [("LSTM (dikkatsiz)", None)]:
        sonuc[ad] = {L: [] for L in TEST_L}
        sure[ad] = []
        for s in TOHUMLAR:
            tohum(s)
            if kw is None:
                model = LSTMAy()
            else:
                model = Model(
                    V,
                    d=64,
                    h=4,
                    L=2,
                    maxT=32,
                    cift=True,
                    norm="pre",
                    **kw
                )
            parametre[ad] = sum(p.numel() for p in model.parameters())
            t0 = time.time()
            son = egit(model, np.random.default_rng(s))
            sure[ad].append(time.time() - t0)
            for L in TEST_L:
                sonuc[ad][L].append(dogruluk(model, L))
            print(
                "%-24s tohum=%d son_kayip=%.4f sure=%.0fs"
                % (ad, s, son, sure[ad][-1])
            )
            if s == 0 and kw is not None and kw["konum"] == "sin":
                modeller["sin"] = model
    print()
    print("Parametre sayisi ve sure ortalamasi:")
    for ad in sonuc:
        print(
            "%-24s %7d  %5.0fs"
            % (ad, parametre[ad], np.mean(sure[ad]))
        )
    print()
    print("Dizi düzeyi doğruluk (ortalama±sapma, 3 tohum)")
    kisa = ["sin", "ogr", "RoPE", "yok", "LSTM"]
    print("L    " + " ".join("%-11s" % k for k in kisa))
    satirlar = []
    for L in TEST_L:
        hucre = []
        for ad in sonuc:
            v = np.array(sonuc[ad][L])
            hucre.append("%.3f±%.3f" % (v.mean(), v.std(ddof=1)))
            satirlar.append(
                [ad, L, "%.4f" % v.mean(), "%.4f" % v.std(ddof=1)]
            )
        print("%-4d " % L + " ".join("%-11s" % h for h in hucre))
    with open(
        os.path.join(VERI, "b69_uzunluk.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["model", "L", "ortalama", "sapma"])
        w.writerows(satirlar)
    print()
    print("Dikkat analizi (sinüzoidal, tohum 0, L=10):")
    dikkat_analizi(modeller["sin"])


if __name__ == "__main__":
    main()
