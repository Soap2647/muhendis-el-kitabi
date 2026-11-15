# -*- coding: utf-8 -*-
"""Bolum 71 - Gercek model uzerinde gecikme olcumu (TTFT,
p50/p95/p99)."""

import random
import time

import numpy as np
import torch

from lm71 import TEMP, kv_bos
from lm71 import KucukGPT

torch.set_num_threads(4)
durum = torch.load(TEMP + "/lm71.pt", weights_only=False)
kars = durum["kars"]
m = KucukGPT(len(kars))
m.load_state_dict(durum["durum"])
m.eval()


@torch.no_grad()
def istek(prompt_len, uret, rng):
    """Bir istek: prefill, sonra uret belirtek (KV onbellekli).
    Dondurur: (TTFT ms, belirtek basina sureler ms)."""
    x = torch.randint(0, len(kars), (1, prompt_len), generator=rng)
    kv = kv_bos(m)
    t0 = time.perf_counter()
    logit = m(x, kv, 0)
    s = int(logit[0, -1].argmax())
    ttft = (time.perf_counter() - t0) * 1000
    sureler, pos = [], prompt_len
    for _ in range(uret - 1):
        t1 = time.perf_counter()
        logit = m(torch.tensor([[s]]), kv, pos)
        s = int(logit[0, -1].argmax())
        sureler.append((time.perf_counter() - t1) * 1000)
        pos += 1
    return ttft, sureler


if __name__ == "__main__":
    rng = torch.Generator().manual_seed(71)
    pyrng = random.Random(71)
    ttfts, tok, toplam = [], [], []
    for _ in range(60):
        P = pyrng.randint(16, 128)
        t, s = istek(P, 32, rng)
        ttfts.append(t)
        tok += s
        toplam.append(t + sum(s))
    ttfts = np.array(ttfts)
    tok = np.array(tok)
    toplam = np.array(toplam)
    print(
        "istek=60, uretilen=32 belirtek/istek, P in [16,128], seed 71"
    )
    print("%-22s %9s %9s %9s" % ("olcut (ms)", "p50", "p95", "p99"))
    for ad, v in [
        ("TTFT", ttfts),
        ("belirtek basi (TPOT)", tok),
        ("toplam istek", toplam),
    ]:
        print(
            "%-22s %9.2f %9.2f %9.2f"
            % (
                ad,
                np.percentile(v, 50),
                np.percentile(v, 95),
                np.percentile(v, 99),
            )
        )
