# -*- coding: utf-8 -*-
"""Bölüm 69 - Attention'ın süre ve bellek maliyeti, KV önbelleği."""

import csv
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from tr69 import Dikkat, Model, tohum

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
V = 50


@torch.no_grad()
def adim_onbellekli(model, x_son, t, onb):
    """Tek belirteç: yalnız yeni q; k, v önbellekten gelir."""
    h = model.emb(x_son) + model.pe[t]
    for i, b in enumerate(model.dec):
        n = b.ln1(h)
        q = b.oz._bol(b.oz.wq(n))
        k = b.oz._bol(b.oz.wk(n))
        v = b.oz._bol(b.oz.wv(n))
        if onb[i] is None:
            onb[i] = (k, v)
        else:
            onb[i] = (
                torch.cat([onb[i][0], k], 2),
                torch.cat([onb[i][1], v], 2),
            )
        K, Vv = onb[i]
        A = torch.softmax(
            q @ K.transpose(-2, -1) / math.sqrt(b.oz.dh), -1
        )
        o = (A @ Vv).transpose(1, 2).reshape(1, 1, -1)
        h = h + b.oz.wo(o)
        h = h + b.ff(b.ln3(h))
    return model.cikis(model.dec_son(h))[:, 0]


@torch.no_grad()
def onbellekli(model, ctx, n):
    P = ctx.shape[1]
    onb = [None] * len(model.dec)
    for t in range(P):  # istemi tek tek işle
        lo = adim_onbellekli(model, ctx[:, t : t + 1], t, onb)
    seq = ctx
    for t in range(P, P + n):
        nxt = lo.argmax(-1, keepdim=True)
        seq = torch.cat([seq, nxt], 1)
        lo = adim_onbellekli(model, nxt, t, onb)
    return seq, lo


@torch.no_grad()
def onbellegiz(model, ctx, n):
    seq = ctx
    for _ in range(n):  # her adımda tüm diziyi yeniden
        lo = model(seq)[:, -1]
        seq = torch.cat([seq, lo.argmax(-1, keepdim=True)], 1)
    return seq, model(seq)[:, -1]


def eslesme():
    print(
        "--- KV önbelleği: aynı çıktı mı? (rastgele ağırlık) ---"
    )
    tohum(0)
    model = Model(
        V,
        d=64,
        h=4,
        L=2,
        maxT=512,
        konum="sin",
        norm="pre",
        cift=False,
        drop=0.0,
    ).eval()
    ctx = torch.randint(0, V, (1, 8))
    s1, lo1 = onbellekli(model, ctx, 200)
    s2, lo2 = onbellegiz(model, ctx, 200)
    print("belirteç dizileri aynı:", bool(torch.equal(s1, s2)))
    print(
        "son adım logit farkı: %.2e" % float((lo1 - lo2).abs().max())
    )


def sure_olc(f, tekrar=5):
    zamanlar = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        zamanlar.append(time.perf_counter() - t0)
    zamanlar.sort()
    return zamanlar[len(zamanlar) // 2]  # medyan


def kv_hizi():
    print("--- Üretim süresi: önbelleksiz ve önbellekli (P=8) ---")
    tohum(0)
    model = Model(
        V,
        d=64,
        h=4,
        L=2,
        maxT=1024,
        konum="sin",
        norm="pre",
        cift=False,
        drop=0.0,
    ).eval()
    ctx = torch.randint(0, V, (1, 8))
    satirlar = []
    print("   N  onbelleksiz_s  onbellekli_s  hizlanma")
    for N in [64, 128, 256, 512]:
        s_on = sure_olc(lambda: onbellekli(model, ctx, N), 3)
        s_ob = sure_olc(lambda: onbellegiz(model, ctx, N), 3)
        print(
            "%4d  %13.3f  %12.3f  %8.1fx"
            % (N, s_ob, s_on, s_ob / s_on)
        )
        satirlar.append([N, "%.4f" % s_ob, "%.4f" % s_on])
    with open(
        os.path.join(VERI, "b69_kv.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["N", "onbellegiz_s", "onbellekli_s"])
        w.writerows(satirlar)


def olcek():
    print("--- Tek dikkat katmanı: süre ve skor matrisi belleği ---")
    tohum(0)
    m = Dikkat(64, 4).eval()
    satirlar = []
    print("    T  sure_ms  skor_matrisi_MB (h=4, float32)")
    for T in [64, 128, 256, 512, 1024, 2048]:
        x = torch.randn(1, T, 64)
        with torch.no_grad():
            s = sure_olc(lambda: m(x, x, None, False), 5) * 1000
        mb = 4 * T * T * 4 / 1e6
        print("%5d  %7.2f  %10.2f" % (T, s, mb))
        satirlar.append([T, "%.3f" % s, "%.2f" % mb])
    with open(
        os.path.join(VERI, "b69_olcek.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["T", "sure_ms", "matris_MB"])
        w.writerows(satirlar)


if __name__ == "__main__":
    print("torch iş parçacığı sayısı:", torch.get_num_threads())
    eslesme()
    kv_hizi()
    olcek()
