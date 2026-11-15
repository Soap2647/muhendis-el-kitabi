# -*- coding: utf-8 -*-
"""Bölüm 70 - LoRA (düşük ranklı uyarlama), sıfırdan.

Donmuş W (d_çıkış x d_giriş) yerine öğrenilen güncelleme:
    y = W x + (alpha / r) * B (A x)
A: r x d_giriş (Gauss ile başlar), B: d_çıkış x r (sıfır ile başlar).
B sıfırla başladığı için eğitimin başında çıktı, taban modelle
aynıdır.
"""

import math
import torch
import torch.nn as nn


class LoRALinear(nn.Module):
    def __init__(self, taban, r, alpha):
        super().__init__()
        self.taban = taban
        for p in self.taban.parameters():
            p.requires_grad = False  # W ve sapma donmuş
        self.r = r
        self.olcek = alpha / r
        giris = taban.in_features
        self.A = nn.Parameter(
            torch.randn(r, giris) / math.sqrt(giris)
        )
        self.B = nn.Parameter(torch.zeros(taban.out_features, r))
        self.acik = True  # adaptör etkin mi?

    def forward(self, x):
        if not self.acik:  # adaptör kapalı: yalnızca taban W
            return self.taban(x)
        delta = (x @ self.A.t()) @ self.B.t()
        return self.taban(x) + self.olcek * delta

    @torch.no_grad()
    def birlestir(self):
        """W' = W + (alpha/r) B A: çıkarımda ek gecikme kalmaz."""
        yeni = nn.Linear(
            self.taban.in_features,
            self.taban.out_features,
            bias=self.taban.bias is not None,
        )
        yeni.weight.copy_(
            self.taban.weight + self.olcek * (self.B @ self.A)
        )
        if self.taban.bias is not None:
            yeni.bias.copy_(self.taban.bias)
        return yeni


def lora_uygula(model, r, alpha=16.0, hedefler=("qkv", "proj")):
    """
    Her blokta dikkat katmanındaki seçilmiş doğrusal katmanları sarar.
    """
    for blok in model.bloklar:
        for ad in hedefler:
            taban = getattr(blok.dikkat, ad)
            setattr(blok.dikkat, ad, LoRALinear(taban, r, alpha))
    return model


def lora_parametreleri(model):
    return [
        p
        for n, p in model.named_parameters()
        if n.endswith((".A", ".B"))
    ]


def egitilebilir_say(model):
    return sum(
        p.numel() for p in model.parameters() if p.requires_grad
    )


def adaptor_durumu(model, acik):
    """
    Tüm LoRA katmanlarında adaptörü açar (True) ya da kapatır (False).
    """
    for m in model.modules():
        if isinstance(m, LoRALinear):
            m.acik = acik
