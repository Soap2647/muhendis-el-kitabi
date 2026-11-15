# -*- coding: utf-8 -*-
"""
Bölüm 70 - LoRA küçük örneği (d=4, r=1): ileri geçiş, parametre
sayısı,
birleştirme (merge) eşdeğerliği. Gerçek LoRALinear sınıfı
kullanılır."""

import torch
from lora_b70 import LoRALinear

torch.set_default_dtype(torch.float64)
lin = torch.nn.Linear(4, 4, bias=False)
with torch.no_grad():
    lin.weight.copy_(torch.diag(torch.tensor([1.0, 2.0, 1.0, 0.5])))
lo = LoRALinear(lin, r=1, alpha=2.0)
with torch.no_grad():
    lo.A.copy_(torch.tensor([[0.5, 0.0, 1.0, 0.0]]))
    lo.B.copy_(torch.tensor([[2.0], [0.0], [0.0], [1.0]]))
x = torch.tensor([1.0, 2.0, 0.0, -1.0])
print("W x            =", lin(x).tolist())
print("A x            =", (lo.A @ x).tolist())
print("olcek=alpha/r  =", lo.olcek)
print("delta          =", (lo.olcek * (lo.B @ (lo.A @ x))).tolist())
print("y (adaptor)    =", lo(x).tolist())
print(
    "eğitilebilir: LoRA=%d, tam matris=%d"
    % (lo.A.numel() + lo.B.numel(), lin.weight.numel())
)
w2 = lo.birlestir()
print("W' = W+olcek*BA satırları:")
print(w2.weight.tolist())
print("y (birleşik)   =", w2(x).tolist())
print(
    "maks fark (birleşik - adaptör) = %.3e"
    % (w2(x) - lo(x)).abs().max().item()
)
X = torch.randn(1000, 4)
print(
    "1000 rastgele girdide maks fark = %.3e"
    % (w2(X) - lo(X)).abs().max().item()
)
lo.acik = False
print("adaptör kapalı y =", lo(x).tolist())
