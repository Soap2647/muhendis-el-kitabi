# g13_alt_tasma.py: fp16'da küçük gradyanın kaybı ve ölçekleme.
import torch
g = torch.tensor([1e-8, 3e-6, 1e-4])      # tipik küçük gradyanlar
print("fp32 :", [f"{v:.4g}" for v in g.tolist()])
print("fp16 :", [f"{v:.4g}" for v in g.half().float().tolist()])
s = 2.0 ** 16                    # GradScaler başlangıç ölçeği
gs = (g * s).half()
geri = (gs.float() / s).tolist()
print("fp16 (x 2^16):", [f"{v:.4g}" for v in geri])
print("fp16 en küçük normal:", torch.finfo(torch.float16).tiny)
print("fp16 en küçük alt normal:",
      torch.tensor(2.0 ** -24, dtype=torch.float16).item())
