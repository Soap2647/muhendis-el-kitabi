# -*- coding: utf-8 -*-
"""Bolum 71 - KV onbellegi.

Esdegerlik, prefill/decode suresi, bellek."""

import csv
import os
import time

import torch

from lm71 import CTX, D, H, KAT, KucukGPT, TEMP, kv_bos
from ortak import VERI

torch.set_num_threads(4)
durum = torch.load(TEMP + "/lm71.pt", weights_only=False)
kars = durum["kars"]
m = KucukGPT(len(kars))
m.load_state_dict(durum["durum"])
m.eval()


@torch.no_grad()
def uret_onbellekli(istem, n):
    kv = kv_bos(m)
    x = torch.tensor([istem])
    logit = m(x, kv, 0)  # prefill
    pos = len(istem)
    cikti = []
    for _ in range(n):
        s = int(logit[0, -1].argmax())
        cikti.append(s)
        logit = m(torch.tensor([[s]]), kv, pos)  # decode, T = 1
        pos += 1
    return cikti


@torch.no_grad()
def uret_onbelleksiz(istem, n):
    seq = list(istem)
    cikti = []
    for _ in range(n):
        logit = m(torch.tensor([seq]))  # tum diziyi yeniden isle
        s = int(logit[0, -1].argmax())
        cikti.append(s)
        seq.append(s)
    return cikti


if __name__ == "__main__":
    metin = "Attention skoru ölçeklenir ve "
    istem = [kars.index(c) for c in metin]
    a = uret_onbellekli(istem, 120)
    b = uret_onbelleksiz(istem, 120)
    print("esdeger (120 belirtec, greedy):", a == b)
    print(
        "uretilen:",
        "".join(kars[i] for i in a[:60]).replace("\n", " "),
    )

    print("\nprefill ve decode suresi (ms, CPU, 4 is parcacigi)")
    satirlar = []
    print(
        "%5s %10s %12s %14s"
        % ("P", "prefill", "decode_onb", "decode_onbsz")
    )
    for P in [32, 64, 128, 192]:
        x = torch.randint(0, len(kars), (1, P))
        t0 = time.perf_counter()
        for _ in range(5):
            kv = kv_bos(m)
            m(x, kv, 0)
        pre = (time.perf_counter() - t0) * 1000 / 5
        kv = kv_bos(m)
        m(x, kv, 0)
        t0 = time.perf_counter()
        for j in range(20):
            m(torch.tensor([[1]]), kv, P + j)
        dec = (time.perf_counter() - t0) * 1000 / 20
        t0 = time.perf_counter()
        for _ in range(20):
            m(torch.cat([x, torch.tensor([[1]])], dim=1))
        full = (time.perf_counter() - t0) * 1000 / 20
        print("%5d %10.2f %12.3f %14.3f" % (P, pre, dec, full))
        satirlar.append(
            {
                "P": P,
                "prefill_ms": round(pre, 3),
                "decode_onbellek_ms": round(dec, 4),
                "decode_onbelleksiz_ms": round(full, 4),
            }
        )
    with open(
        os.path.join(VERI, "b71_prefill_decode.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)

    print("\nKV bellek formulu: 2 * L * kafa * d_bas * T * bayt")
    print(
        "kucuk model, T=256, fp32:",
        2 * KAT * H * (D // H) * 256 * 4,
        "bayt",
    )
    tablo = []
    for T in [1024, 4096, 8192, 32768]:
        mha = 2 * 32 * 32 * 128 * T * 2
        gqa = 2 * 32 * 8 * 128 * T * 2
        tablo.append(
            {
                "T": T,
                "MHA_GB": round(mha / 2**30, 3),
                "GQA8_GB": round(gqa / 2**30, 3),
            }
        )
        print(
            "7B sinifi (L=32, H=32, d=128, fp16) T=%6d: "
            "MHA %.2f GB  GQA(8) %.2f GB"
            % (T, mha / 2**30, gqa / 2**30)
        )
    with open(
        os.path.join(VERI, "b71_kv_bellek.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(tablo[0].keys()))
        w.writeheader()
        w.writerows(tablo)
