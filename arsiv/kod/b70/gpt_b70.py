# -*- coding: utf-8 -*-
"""Bölüm 70 - Küçük nedensel (decoder-only) GPT, sıfırdan.

Bölüm 69'daki blokların aynısı: çok başlı nedensel dikkat, önce-
normalizasyon
(pre-LN), GELU'lu MLP ve artık bağlantılar. Ağırlık paylaşımı: girdi
gömmesi ile çıktı başlığı aynı matrisi kullanır.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class CokBasliDikkat(nn.Module):
    def __init__(self, d, bas, ctx, dusme):
        super().__init__()
        self.bas, self.hd = bas, d // bas
        self.qkv = nn.Linear(d, 3 * d)
        self.proj = nn.Linear(d, d)
        self.dusme = nn.Dropout(dusme)
        maske = torch.tril(torch.ones(ctx, ctx)).view(1, 1, ctx, ctx)
        self.register_buffer("maske", maske, persistent=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q = q.view(B, T, self.bas, self.hd).transpose(1, 2)
        k = k.view(B, T, self.bas, self.hd).transpose(1, 2)
        v = v.view(B, T, self.bas, self.hd).transpose(1, 2)
        a = (q @ k.transpose(-2, -1)) / math.sqrt(self.hd)
        a = a.masked_fill(
            self.maske[:, :, :T, :T] == 0, float("-inf")
        )
        a = self.dusme(F.softmax(a, dim=-1))
        y = (a @ v).transpose(1, 2).reshape(B, T, C)
        return self.dusme(self.proj(y))


class Blok(nn.Module):
    def __init__(self, d, bas, ctx, dusme):
        super().__init__()
        self.ln1 = nn.LayerNorm(d)
        self.dikkat = CokBasliDikkat(d, bas, ctx, dusme)
        self.ln2 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(
            nn.Linear(d, 4 * d),
            nn.GELU(),
            nn.Linear(4 * d, d),
            nn.Dropout(dusme),
        )

    def forward(self, x):
        x = x + self.dikkat(self.ln1(x))
        return x + self.mlp(self.ln2(x))


class MiniGPT(nn.Module):
    def __init__(self, sozluk, ctx=128, d=128, L=4, bas=4, dusme=0.1):
        super().__init__()
        self.ctx = ctx
        self.tok = nn.Embedding(sozluk, d)
        self.pos = nn.Embedding(ctx, d)
        self.drop = nn.Dropout(dusme)
        self.bloklar = nn.ModuleList(
            Blok(d, bas, ctx, dusme) for _ in range(L)
        )
        self.ln_f = nn.LayerNorm(d)
        self.head = nn.Linear(d, sozluk, bias=False)
        self.head.weight = self.tok.weight  # ağırlık paylaşımı
        self.apply(self._ilk)

    @staticmethod
    def _ilk(m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.zeros_(m.bias)

    def gizli(self, idx):
        T = idx.shape[1]
        konum = torch.arange(T, device=idx.device)
        x = self.drop(self.tok(idx) + self.pos(konum))
        for blok in self.bloklar:
            x = blok(x)
        return self.ln_f(x)

    def forward(self, idx, hedef=None):
        h = self.gizli(idx)
        logit = self.head(h)
        if hedef is None:
            return logit, None
        kayip = F.cross_entropy(
            logit.reshape(-1, logit.size(-1)), hedef.reshape(-1)
        )
        return logit, kayip


def parametre_say(model):
    return sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )
