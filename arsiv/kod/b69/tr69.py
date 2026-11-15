# -*- coding: utf-8 -*-
"""Bölüm 69 ortak kütüphanesi: attention, blok, Transformer.

nn.Transformer ya da nn.MultiheadAttention KULLANILMAZ. Tüm
projeksiyonlar, bölmeler, maskeler ve konum kodlamaları buradadır.
"""

import math
import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # bu bölümde yalnızca CPU

import numpy as np
import torch
import torch.nn as nn


def tohum(s):
    np.random.seed(s)
    torch.manual_seed(s)


def sinuzoidal(T, d):
    """Vaswani 2017 sinüzoidal konum kodlaması, (T, d) boyutlu."""
    poz = np.arange(T)[:, None]
    i = np.arange(d // 2)[None, :]
    aci = poz / (10000.0 ** (2 * i / d))
    pe = np.zeros((T, d))
    pe[:, 0::2] = np.sin(aci)
    pe[:, 1::2] = np.cos(aci)
    return torch.tensor(pe, dtype=torch.float32)


def rotasyon(x, taban=10000.0):
    """RoPE: (x_2i, x_2i+1) çiftleri konuma göre döndürülür.

    x boyutu (B, h, T, dh). Çiftler birbirine komşu indekslerdir.
    """
    T, dh = x.shape[-2], x.shape[-1]
    i = torch.arange(dh // 2, dtype=x.dtype)
    teta = taban ** (-2 * i / dh)
    aci = torch.arange(T, dtype=x.dtype)[:, None] * teta[None, :]
    c, s = torch.cos(aci), torch.sin(aci)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    o1 = x1 * c - x2 * s
    o2 = x1 * s + x2 * c
    return torch.stack([o1, o2], dim=-1).flatten(-2)


class Dikkat(nn.Module):
    """Çok başlı ölçekli nokta çarpımı attention."""

    def __init__(self, d, h):
        super().__init__()
        assert d % h == 0
        self.h, self.dh = h, d // h
        self.wq = nn.Linear(d, d)
        self.wk = nn.Linear(d, d)
        self.wv = nn.Linear(d, d)
        self.wo = nn.Linear(d, d)
        self.son_A = None

    def _bol(self, z):
        """(B, T, d) -> (B, h, T, dh): başlara bölme."""
        B, T, _ = z.shape
        return z.view(B, T, self.h, self.dh).transpose(1, 2)

    def forward(self, xq, xkv, maske=None, rope=False):
        B, T, d = xq.shape
        q = self._bol(self.wq(xq))
        k = self._bol(self.wk(xkv))
        v = self._bol(self.wv(xkv))
        if rope:
            q, k = rotasyon(q), rotasyon(k)
        s = q @ k.transpose(-2, -1) / math.sqrt(self.dh)
        if maske is not None:
            s = s.masked_fill(~maske, float("-inf"))
        A = torch.softmax(s, dim=-1)
        o = (A @ v).transpose(1, 2).reshape(B, T, d)  # birleştir
        self.son_A = A.detach()
        return self.wo(o), A


class Blok(nn.Module):
    """Transformer bloğu: attention, (varsa) çapraz attention, MLP."""

    def __init__(self, d, h, norm, drop, capraz):
        super().__init__()
        self.norm = norm
        self.oz = Dikkat(d, h)
        self.ln1 = nn.LayerNorm(d)
        self.capraz = Dikkat(d, h) if capraz else None
        self.ln2 = nn.LayerNorm(d)
        self.ff = nn.Sequential(
            nn.Linear(d, 4 * d), nn.GELU(), nn.Linear(4 * d, d)
        )
        self.ln3 = nn.LayerNorm(d)
        self.drop = nn.Dropout(drop)

    def forward(self, x, enc=None, maske=None, rope=False):
        if self.norm == "pre":
            h = self.ln1(x)
            x = x + self.drop(self.oz(h, h, maske, rope)[0])
            if self.capraz is not None:
                x = x + self.drop(self.capraz(self.ln2(x), enc)[0])
            x = x + self.drop(self.ff(self.ln3(x)))
        else:  # post-norm: artık, sonra LayerNorm
            x = self.ln1(x + self.drop(self.oz(x, x, maske, rope)[0]))
            if self.capraz is not None:
                x = self.ln2(x + self.drop(self.capraz(x, enc)[0]))
            x = self.ln3(x + self.drop(self.ff(x)))
        return x


class Model(nn.Module):
    """Encoder-decoder (cift=True) ya da yalnız decoder."""

    def __init__(
        self,
        V,
        d=64,
        h=4,
        L=2,
        maxT=32,
        konum="sin",
        norm="pre",
        cift=False,
        drop=0.0,
    ):
        super().__init__()
        self.konum, self.norm, self.cift = konum, norm, cift
        self.emb = nn.Embedding(V, d)
        if konum == "sin":
            self.register_buffer("pe", sinuzoidal(maxT, d))
        if konum == "ogr":
            self.pos = nn.Embedding(maxT, d)
        if cift:
            self.enc = nn.ModuleList(
                [Blok(d, h, norm, drop, False) for _ in range(L)]
            )
            self.enc_son = (
                nn.LayerNorm(d) if norm == "pre" else nn.Identity()
            )
        self.dec = nn.ModuleList(
            [Blok(d, h, norm, drop, cift) for _ in range(L)]
        )
        self.dec_son = (
            nn.LayerNorm(d) if norm == "pre" else nn.Identity()
        )
        self.cikis = nn.Linear(d, V)

    def _konum(self, h):
        T = h.shape[1]
        if self.konum == "sin":
            return h + self.pe[:T]
        if self.konum == "ogr":
            return h + self.pos(torch.arange(T))
        return h  # "rope" ve "yok": eklenmez

    def kodla(self, src):
        h = self._konum(self.emb(src))
        for b in self.enc:  # maske yok: çift yönlü
            h = b(h, rope=self.konum == "rope")
        return self.enc_son(h)

    def forward(self, x, src=None):
        T = x.shape[1]
        maske = torch.tril(torch.ones(T, T, dtype=torch.bool))
        enc = self.kodla(src) if self.cift else None
        h = self._konum(self.emb(x))
        for b in self.dec:  # nedensel maske
            h = b(h, enc=enc, maske=maske, rope=self.konum == "rope")
        return self.cikis(self.dec_son(h))


@torch.no_grad()
def greedy_seq2seq(model, src, n_out, bos=1):
    """Açgözlü (greedy) çözme: her adımda en olası belirteci seç."""
    model.eval()
    ys = torch.full((src.shape[0], 1), bos, dtype=torch.long)
    for _ in range(n_out):
        logits = model(ys, src)
        ys = torch.cat([ys, logits[:, -1:].argmax(-1)], dim=1)
    return ys[:, 1:]
