# g10_amp_kontrol.py: aynı tohum, fp32 ile fp16-AMP ağırlık farkı.
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
dev = torch.device("cuda")
X, y = load_digits(return_X_y=True)
X = torch.tensor(X / 16.0, dtype=torch.float32).to(dev)
y = torch.tensor(y).to(dev)


def egit(amp):
    torch.manual_seed(0)
    net = nn.Sequential(nn.Linear(64, 256), nn.ReLU(),
                        nn.Linear(256, 10)).to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    sc = torch.amp.GradScaler("cuda", enabled=amp)
    lossf = nn.CrossEntropyLoss()
    for ep in range(3):
        perm = torch.randperm(len(X), device=dev)
        for i in range(0, len(X), 64):
            b = perm[i:i + 64]
            with torch.autocast("cuda", dtype=torch.float16,
                                enabled=amp):
                l = lossf(net(X[b]), y[b])
            opt.zero_grad()
            sc.scale(l).backward()
            sc.step(opt)
            sc.update()
    return net


a = egit(False)
b = egit(True)
print("fp32 vs AMP en büyük ağırlık farkı:",
      max((p - q).abs().max().item()
          for p, q in zip(a.parameters(), b.parameters())))
