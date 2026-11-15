# -*- coding: utf-8 -*-
"""Bolum 71 - Kucuk karakter duzeyi decoder-only model (sifirdan)."""

import math
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

from ortak import bolumleri_oku

TEMP = "C:/Users/merty/AppData/Local/Temp/b71"
CTX, D, H, KAT = 256, 128, 4, 2


def metin_al():
    """Kitabin duz metni (Bolum 1-69). Kod ve kutular atilmistir."""
    parcalar = []
    for n, pars in bolumleri_oku():
        parcalar.append(" ".join(p for _, p in pars))
    return "\n".join(parcalar)


class Blok(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1 = nn.LayerNorm(D)
        self.qkv = nn.Linear(D, 3 * D, bias=False)
        self.wo = nn.Linear(D, D, bias=False)
        self.ln2 = nn.LayerNorm(D)
        self.w1 = nn.Linear(D, 4 * D, bias=False)
        self.w2 = nn.Linear(4 * D, D, bias=False)

    def forward(self, x, kv=None, baslangic=0):
        B, T, _ = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(D, dim=2)
        q = q.view(B, T, H, D // H).transpose(1, 2)
        k = k.view(B, T, H, D // H).transpose(1, 2)
        v = v.view(B, T, H, D // H).transpose(1, 2)
        if kv is not None:
            # KV onbellegi: gecmis k, v ile birlestir
            if kv["k"] is not None:
                k = torch.cat([kv["k"], k], dim=2)
                v = torch.cat([kv["v"], v], dim=2)
            kv["k"], kv["v"] = k, v
        S = k.shape[2]
        skor = q @ k.transpose(-2, -1) / math.sqrt(D // H)
        # Nedensel maske: sorgu konumu i, anahtar konumu j <=
        # baslangic+i
        maske = torch.ones(T, S, dtype=torch.bool).tril(
            diagonal=S - T
        )
        skor = skor.masked_fill(~maske, float("-inf"))
        a = torch.softmax(skor, dim=-1) @ v
        a = a.transpose(1, 2).reshape(B, T, D)
        x = x + self.wo(a)
        x = x + self.w2(F.gelu(self.w1(self.ln2(x))))
        return x


class KucukGPT(nn.Module):
    def __init__(self, V):
        super().__init__()
        self.emb = nn.Embedding(V, D)
        self.pos = nn.Embedding(CTX, D)
        self.bloklar = nn.ModuleList([Blok() for _ in range(KAT)])
        self.ln_f = nn.LayerNorm(D)

    def forward(self, idx, kvler=None, baslangic=0):
        B, T = idx.shape
        konum = torch.arange(baslangic, baslangic + T)
        x = self.emb(idx) + self.pos(konum)
        for i, b in enumerate(self.bloklar):
            x = b(x, None if kvler is None else kvler[i], baslangic)
        x = self.ln_f(x)
        # Ag cikisi bagli (weight tying): cikis matrisi gomme
        # tablosudur
        return x @ self.emb.weight.T


def kv_bos(model):
    return [{"k": None, "v": None} for _ in model.bloklar]


def parametre_sayisi(model):
    return sum(p.numel() for p in model.parameters())
