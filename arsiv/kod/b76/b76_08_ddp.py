# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 8: DDP (gloo, 2 surec) esdegerligi."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP

DUNYA = 2  # surec sayisi (dunya boyutu)
ADIM = 5  # egitim adimi
LR = 0.1


def model_kur():
    torch.manual_seed(76)  # her surec ayni baslangic agirliklari
    return nn.Sequential(
        nn.Linear(16, 32), nn.ReLU(), nn.Linear(32, 1)
    )


def veri():
    g = torch.Generator().manual_seed(76)
    x = torch.randn(256, 16, generator=g)
    y = torch.sin(x[:, :1]) + 0.1 * torch.randn(256, 1, generator=g)
    return x, y


def calistir(rank, depo):
    # Windows'ta libuv yok: TCP yerine dosya deposu (file://)
    dist.init_process_group(
        "gloo", init_method=depo, rank=rank, world_size=DUNYA
    )
    x, y = veri()
    parca = x.shape[0] // DUNYA
    xy = x[rank * parca : (rank + 1) * parca]  # yerel mini-batch
    yy = y[rank * parca : (rank + 1) * parca]

    ddp = DDP(model_kur())
    ref = model_kur()  # tek surec referansi
    ref.load_state_dict(ddp.module.state_dict())
    kayip = nn.MSELoss()
    opt_d = torch.optim.SGD(ddp.parameters(), lr=LR)
    opt_r = torch.optim.SGD(ref.parameters(), lr=LR)

    # 1) Gradyan karsilastirmasi (tek adim)
    ddp.zero_grad()
    kayip(ddp(xy), yy).backward()  # all-reduce burada
    ref.zero_grad()
    kayip(ref(x), y).backward()  # tum batch
    fark_g = max(
        (a.grad - b.grad).abs().max().item()
        for a, b in zip(ddp.parameters(), ref.parameters())
    )

    # 2) ADIM adim egitim ve agirlik karsilastirmasi
    for _ in range(ADIM):
        opt_d.zero_grad()
        kayip(ddp(xy), yy).backward()
        opt_d.step()
        opt_r.zero_grad()
        kayip(ref(x), y).backward()
        opt_r.step()
    fark_w = max(
        (a - b).abs().max().item()
        for a, b in zip(ddp.parameters(), ref.parameters())
    )
    if rank == 0:
        print(
            f"surec sayisi = {DUNYA}, yerel batch = {parca}, "
            f"toplam = {x.shape[0]}"
        )
        print(f"max |grad_ddp - grad_tek| (1. adim) = {fark_g:.2e}")
        print(
            f"max |w_ddp - w_tek| ({ADIM} adim sonra) = {fark_w:.2e}"
        )
        print(
            f"son kayip (tek surec) = "
            f"{kayip(ref(x), y).item():.6f}"
        )
    dist.destroy_process_group()


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    depo_yol = os.path.join(HERE, "ddp_depo.tmp")
    if os.path.exists(depo_yol):
        os.remove(depo_yol)
    depo = "file:///" + depo_yol.replace("\\", "/")
    mp.spawn(calistir, args=(depo,), nprocs=DUNYA, join=True)
