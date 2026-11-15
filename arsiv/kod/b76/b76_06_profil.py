# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 6: profiler ile cekirdek sayimi ve CUDA graph."""

import _cudaenv  # noqa: F401
import csv
import os
import torch
from torch import nn
from torch.profiler import profile, ProfilerActivity
from torch.utils._python_dispatch import TorchDispatchMode
from olcum import medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"


class IslemSayaci(TorchDispatchMode):
    """Her aten islemini (ileri+geri) sayar."""

    def __init__(self):
        super().__init__()
        self.n = 0

    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        self.n += 1
        return func(*args, **(kwargs or {}))


def profil_mlp():
    torch.manual_seed(76)
    model = nn.Sequential(
        nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 10)
    ).cuda()
    x = torch.randn(32, 64, device="cuda")
    y = torch.randint(0, 10, (32,), device="cuda")
    kayip = nn.CrossEntropyLoss()

    def adim():
        model.zero_grad(set_to_none=True)
        kayip(model(x), y).backward()
        with torch.no_grad():
            for p in model.parameters():
                p.sub_(0.01 * p.grad)

    for _ in range(5):
        adim()
    torch.cuda.synchronize()
    with IslemSayaci() as sayac:
        adim()
    torch.cuda.synchronize()
    print(f"Bir egitim adiminda {sayac.n} aten islemi")
    t_adim, _, _ = medyan_ms_torch(adim, tekrar=15)
    print(f"Adim suresi (CUDA olaylari, medyan): {t_adim:.3f} ms")
    # Not: bu Windows kurulumunda profiler GPU cekirdek etkinligi
    # kaydetmedi; bu yuzden CPU tarafi tablosu ve olay zamanlamasi
    # kullanilir.
    with profile(activities=[ProfilerActivity.CPU]) as prof:
        for _ in range(20):
            adim()
        torch.cuda.synchronize()
    print("ad                             cagri   kendi CPU ms")
    satir = sorted(
        prof.key_averages(), key=lambda e: -e.self_cpu_time_total
    )[:6]
    for e in satir:
        print(
            f"{e.key[:30]:<30} {e.count:6d} "
            f"{e.self_cpu_time_total / 1000:12.3f}"
        )
    return sayac.n, t_adim


def kucuk_isler(x, adet=200):
    # 200 kucuk elemanter islem: her biri ayri bir cekirdek baslatma
    for _ in range(adet):
        x = x * 1.0001 + 0.0001
    return x


def cuda_graph_karsilastirma():
    x = torch.zeros(1024, device="cuda")
    # Isinma: graph yakalamadan once yan akista calistir
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        for _ in range(3):
            kucuk_isler(x)
    torch.cuda.current_stream().wait_stream(s)
    graf = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graf):
        cikis = kucuk_isler(x)
    t_eager, _, _ = medyan_ms_torch(lambda: kucuk_isler(x), tekrar=15)
    t_graf, _, _ = medyan_ms_torch(lambda: graf.replay(), tekrar=15)
    dogru = torch.allclose(cikis, kucuk_isler(x))
    print(f"\n200 kucuk islem (1024 eleman):")
    print(f"  eager (her islem ayri baslatma): {t_eager:.3f} ms")
    print(f"  CUDA graph replay              : {t_graf:.3f} ms")
    print(f"  hizlanma: {t_eager / t_graf:.2f}x   dogruluk: {dogru}")
    return t_eager, t_graf


def main():
    islem, t_adim = profil_mlp()
    t_e, t_g = cuda_graph_karsilastirma()
    with open(
        os.path.join(VERI, "b76_profil.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["olcum", "deger"])
        w.writerow(["adim_basina_aten_islemi", islem])
        w.writerow(["adim_ms", round(t_adim, 4)])
        w.writerow(["eager_ms", round(t_e, 4)])
        w.writerow(["graph_ms", round(t_g, 4)])


if __name__ == "__main__":
    main()
