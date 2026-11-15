# -*- coding: utf-8 -*-
"""Bolum 71 - Toplu isleme: statik ve surekli (continuous) batching
simulasyonu."""

import csv
import os

import numpy as np

from ortak import VERI

A_MS, C_MS = 8.0, 0.6  # varsayim: adim_suresi(b) = A + C*b  (ms)
G = 50  # istek basina uretilen belirtek sayisi
N = 4000
SEED = 71


def adim(b):
    return A_MS + C_MS * b


def statik(lam, B, rng):
    arr = np.cumsum(rng.exponential(1000.0 / lam, N))
    t, i, gecikme, son = 0.0, 0, [], 0.0
    while i < N:
        t = max(t, arr[i])
        grup = []
        while i < N and arr[i] <= t and len(grup) < B:
            grup.append(arr[i])
            i += 1
        bit = t + G * adim(len(grup))
        gecikme += [bit - a for a in grup]
        t = bit
        son = bit
    return son, gecikme


def surekli(lam, B, rng):
    arr = np.cumsum(rng.exponential(1000.0 / lam, N))
    t, i, aktif, gecikme = 0.0, 0, [], []
    while i < N or aktif:
        if not aktif and i < N and arr[i] > t:
            t = arr[i]
        while i < N and arr[i] <= t and len(aktif) < B:
            aktif.append([arr[i], G])
            i += 1
        t += adim(len(aktif))
        for r in aktif:
            r[1] -= 1
        gecikme += [t - r[0] for r in aktif if r[1] == 0]
        aktif = [r for r in aktif if r[1] > 0]
    return t, gecikme


def ozet(son, gecikme):
    g = np.array(gecikme)
    return {
        "verim": N * G / son * 1000,
        "p50": np.percentile(g, 50),
        "p95": np.percentile(g, 95),
        "p99": np.percentile(g, 99),
    }


if __name__ == "__main__":
    satirlar = []
    print(
        "%-8s %3s %5s %10s %9s %9s %9s"
        % ("mod", "B", "lam", "verim", "p50", "p95", "p99")
    )
    for mod, fn in [("statik", statik), ("surekli", surekli)]:
        for B in [8, 32]:
            for lam in [5, 10, 15, 20, 25]:
                rng = np.random.default_rng(SEED)
                son, g = fn(lam, B, rng)
                o = ozet(son, g)
                print(
                    "%-8s %3d %5d %10.0f %9.0f %9.0f %9.0f"
                    % (
                        mod,
                        B,
                        lam,
                        o["verim"],
                        o["p50"],
                        o["p95"],
                        o["p99"],
                    )
                )
                satirlar.append(
                    {
                        "mod": mod,
                        "B": B,
                        "lam": lam,
                        "verim": round(o["verim"], 1),
                        "p50": round(o["p50"], 1),
                        "p95": round(o["p95"], 1),
                        "p99": round(o["p99"], 1),
                    }
                )
    with open(
        os.path.join(VERI, "b71_batching.csv"),
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
