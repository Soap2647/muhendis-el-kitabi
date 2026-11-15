# g11_profil.py: torch.profiler ile GPU operatör maliyeti.
# Çıktı: engine/veri/b65_profil.csv
import csv, os
import torch
import torch.nn as nn
from torch.profiler import profile, ProfilerActivity
KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.manual_seed(0)
net = nn.Sequential(
    nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
    nn.Flatten(), nn.Linear(64 * 8 * 8, 256), nn.ReLU(),
    nn.Linear(256, 10)).to(dev)
opt = torch.optim.Adam(net.parameters(), 1e-3)
x = torch.randn(256, 1, 32, 32, device=dev)
y = torch.randint(0, 10, (256,), device=dev)
lossf = nn.CrossEntropyLoss()


def adim():
    opt.zero_grad()
    lossf(net(x), y).backward()
    opt.step()


for _ in range(10):
    adim()
torch.cuda.synchronize()
acts = [ProfilerActivity.CPU, ProfilerActivity.CUDA]
with profile(activities=acts) as p:
    for _ in range(5):
        adim()
    torch.cuda.synchronize()
tablo = p.key_averages()
kaba = sorted(tablo, key=lambda e: e.self_device_time_total,
              reverse=True)[:8]
print("%-34s %10s %10s %6s" % ("operatör", "GPU us/adım",
                                 "CPU us/adım", "çağrı"))
satir = []
for e in kaba:
    ad = e.key[:34]
    us = e.self_device_time_total / 5
    cpu = e.self_cpu_time_total / 5
    print("%-34s %10.1f %10.1f %6d" % (ad, us, cpu, e.count // 5))
    satir.append((ad, "%.1f" % us, "%.1f" % cpu, e.count // 5))
with open(os.path.join(KOK, "b65_profil.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["operator", "gpu_us_adim", "cpu_us_adim",
                "cagri_adim"])
    w.writerows(satir)
