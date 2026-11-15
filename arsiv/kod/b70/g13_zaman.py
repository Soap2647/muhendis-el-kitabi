# -*- coding: utf-8 -*-
"""
Bölüm 70 - Zamanlama: eğitim adımı ve KV önbelleksiz üretim (token/s).
Yalnızca GPU boşken çalıştırılır; nvidia-smi durumu başta ve sonda
yazılır."""

import os, statistics, subprocess, time
import torch
from gpt_b70 import MiniGPT

K = os.path.dirname(os.path.abspath(__file__))


def gpu():
    return subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used",
            "--format=csv,noheader",
        ],
        capture_output=True,
        text=True,
    ).stdout.strip()


print("başlangıç GPU:", gpu())
dev = torch.device("cuda")
torch.manual_seed(0)
m = MiniGPT(2149, ctx=128, d=128, L=4, bas=4, dusme=0.1).to(dev)
opt = torch.optim.AdamW(m.parameters(), lr=1e-4)
scaler = torch.amp.GradScaler("cuda")
x = torch.randint(0, 2149, (32, 128), device=dev)
y = torch.randint(0, 2149, (32, 128), device=dev)


def adim():
    with torch.autocast("cuda", dtype=torch.float16):
        _, k = m(x, y)
    opt.zero_grad()
    scaler.scale(k).backward()
    scaler.step(opt)
    scaler.update()


for _ in range(30):
    adim()
torch.cuda.synchronize()
olcumler = []
for _ in range(3):
    t0 = time.time()
    for _ in range(200):
        adim()
    torch.cuda.synchronize()
    olcumler.append(1000 * (time.time() - t0) / 200)
print(
    "eğitim adımı (batch 32 x ctx 128, AMP): ms = %s, medyan=%.2f"
    % ([round(v, 2) for v in olcumler], statistics.median(olcumler))
)
m.eval()
with torch.no_grad():
    idx = torch.randint(0, 2149, (1, 16), device=dev)
    for _ in range(20):
        idx = torch.cat(
            [
                idx,
                m(idx[:, -128:])[0][:, -1].argmax(-1, keepdim=True),
            ],
            1,
        )
    torch.cuda.synchronize()
    t0 = time.time()
    for _ in range(200):
        idx = torch.cat(
            [
                idx,
                m(idx[:, -128:])[0][:, -1].argmax(-1, keepdim=True),
            ],
            1,
        )
    torch.cuda.synchronize()
print(
    "üretim (KV önbelleksiz, bağlam<=128): %.2f ms/token = "
    "%.1f token/s"
    % (1000 * (time.time() - t0) / 200, 200 / (time.time() - t0))
)
print("bitiş GPU:", gpu())
