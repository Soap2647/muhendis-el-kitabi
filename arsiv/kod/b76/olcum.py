# -*- coding: utf-8 -*-
"""Ortak zamanlama yardimcilari: CUDA olaylariyla medyan sure (ms)."""

import statistics
import torch


def medyan_ms_torch(fn, tekrar=15, isinma=3):
    """fn() calisma suresinin medyani; CUDA olaylariyla olculur."""
    for _ in range(isinma):
        fn()
    torch.cuda.synchronize()
    sure = []
    for _ in range(tekrar):
        a = torch.cuda.Event(enable_timing=True)
        b = torch.cuda.Event(enable_timing=True)
        a.record()
        fn()
        b.record()
        b.synchronize()
        sure.append(a.elapsed_time(b))
    return statistics.median(sure), min(sure), max(sure)


def medyan_ms_numba(cuda, fn, tekrar=15, isinma=3):
    """Numba cekirdekleri icin ayni olcum (cuda.event)."""
    for _ in range(isinma):
        fn()
    cuda.synchronize()
    sure = []
    for _ in range(tekrar):
        a = cuda.event(timing=True)
        b = cuda.event(timing=True)
        a.record()
        fn()
        b.record()
        b.synchronize()
        sure.append(cuda.event_elapsed_time(a, b))
    return statistics.median(sure), min(sure), max(sure)
