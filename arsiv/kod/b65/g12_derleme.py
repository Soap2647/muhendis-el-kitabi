# g12_derleme.py: torch.compile, torch.export ve torch.jit.trace.
import os

import torch
import torch.nn as nn

torch.manual_seed(0)
net = nn.Sequential(nn.Linear(1024, 1024), nn.GELU(),
                    nn.Linear(1024, 1024), nn.GELU(),
                    nn.Linear(1024, 10)).cuda().eval()
x = torch.randn(64, 1024, device="cuda")

with torch.no_grad():
    try:
        cnet = torch.compile(net)
        cnet(x)
        print("torch.compile (inductor) çalıştı")
    except Exception as e:
        print("torch.compile BAŞARISIZ:", type(e).__name__,
              str(e).splitlines()[0][:60])
    # Grafik yakalama, Triton gerektirmeyen 'eager' arka ucuyla.
    c = torch.compile(net, backend="eager")
    print("eager backend fark:", (c(x) - net(x)).abs().max().item())

# torch.export: grafik yakalama (CPU üzerinde, dışa aktarım için).
cpu = nn.Sequential(nn.Linear(16, 8), nn.ReLU(),
                    nn.Linear(8, 2)).eval()
ex = torch.export.export(cpu, (torch.randn(4, 16),))
print("\ntorch.export grafiği (ilk düğümler):")
for n in list(ex.graph.nodes)[:6]:
    print("  ", n.op, n.target if n.op != "placeholder" else n.name)
print("export/eager fark:",
      (ex.module()(torch.ones(4, 16))
       - cpu(torch.ones(4, 16))).abs().max().item())

# TorchScript trace ve kaydet/yükle.
yol = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "model.pt")
tr = torch.jit.trace(cpu, torch.randn(4, 16))
tr.save(yol)
yuk = torch.jit.load(yol)
t = torch.randn(4, 16)
print("jit trace yükle farkı:", (yuk(t) - cpu(t)).abs().max().item())
print("model.pt bayt:", os.path.getsize(yol))
