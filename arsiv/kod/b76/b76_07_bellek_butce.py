# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 7: egitimde bellek butcesi (fp32, Adam)."""

import _cudaenv  # noqa: F401
import csv
import os
import torch
from torch import nn

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
MB = 1024**2


def bellek():
    return torch.cuda.memory_allocated() / MB


def main():
    torch.manual_seed(76)
    torch.cuda.reset_peak_memory_stats()
    # 4 katman, her biri 4096 x 4096 + sapma: ~67.1 M parametre
    model = nn.Sequential(*[nn.Linear(4096, 4096) for _ in range(4)])
    P = sum(p.numel() for p in model.parameters())
    model = model.cuda()
    opt = torch.optim.Adam(model.parameters(), lr=1e-4)
    x = torch.randn(8, 4096, device="cuda")  # kucuk batch
    print(f"parametre sayisi P = {P / 1e6:.2f} M")
    print(f"beklenen (fp32, Adam): 16 P bayt = {16 * P / MB:.1f} MB")
    print()
    print("asama                         ayrilan MB   P basina bayt")
    satirlar = []
    a0 = bellek()
    satirlar.append(("model parametreleri", a0))
    loss = model(x).pow(2).mean()
    loss.backward()
    a1 = bellek()
    satirlar.append(("+ gradyanlar", a1))
    opt.step()
    a2 = bellek()
    satirlar.append(("+ Adam m ve v (ilk adim)", a2))
    opt.zero_grad(set_to_none=True)
    a3 = bellek()
    satirlar.append(("zero_grad(None) sonrasi", a3))
    for ad, deger in satirlar:
        print(f"{ad:<29} {deger:10.1f}   {deger * MB / P:8.2f}")
    tepe = torch.cuda.max_memory_allocated() / MB
    print(f"\nTepe (max_memory_allocated): {tepe:.1f} MB")
    print(
        "Aktivasyon ve tamponlar tepe-ayrilan farkina girer."
    )

    # Sinir sinamasi: 6 GB kartta 12 GB'lik dolu tensor.
    # Bu makinede (WDDM) hata vermedi; metinde yorumlanir.
    del model, opt, x, loss
    torch.cuda.empty_cache()
    libre, toplam = torch.cuda.mem_get_info()
    print(
        "\nVRAM bos/toplam: "
        f"{libre / 1024 ** 3:.2f} / {toplam / 1024 ** 3:.2f} GB"
    )
    try:
        t = torch.zeros(
            12 * 1024**3 // 4, dtype=torch.float32, device="cuda"
        )
        print(
            "12 GB dolduruldu; ayrilan: "
            f"{torch.cuda.memory_allocated() / 1024 ** 3:.1f} GB"
        )
        del t
    except torch.OutOfMemoryError as hata:
        print("OOM:", str(hata).split("\n")[0][:100])
    torch.cuda.empty_cache()

    with open(
        os.path.join(VERI, "b76_bellek_butce.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["asama", "mb", "bayt_per_param"])
        for ad, deger in satirlar:
            w.writerow(
                [ad, round(deger, 2), round(deger * MB / P, 3)]
            )
        w.writerow(["tepe", round(tepe, 2), round(tepe * MB / P, 3)])
        w.writerow(["P", P, ""])
    zt = zero_tablo()
    print("\nZeRO: GPU basina bellek (GB), fp32 + Adam")
    print("model  N  asama  parametre  gradyan  optimizer  toplam")
    for r in zt:
        print(
            f"{r[0]:<6}{r[1]:<3}{r[2]:<7}{r[3]:9.3f}{r[4]:9.3f}"
            f"{r[5]:11.3f}{r[6]:8.3f}"
        )
    with open(
        os.path.join(VERI, "b76_zero.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(
            [
                "model",
                "n",
                "asama",
                "parametre_gb",
                "gradyan_gb",
                "optimizer_gb",
                "toplam_gb",
            ]
        )
        w.writerows(zt)


def zero_tablo():
    """ZeRO asamalarina gore GPU basina bellek (GB, 10^9 bayt).
    fp32+Adam: parametre 4, gradyan 4, Adam (m, v) 8 bayt/param.
    Asama 0: tam kopya. 1: Adam bolunur. 2: + gradyan bolunur.
    3: + parametre. Karisik hassasiyette (2+2+12) yine 16 bayt.
    """
    satirlar = []
    for ad, P in [("1.3B", 1.3e9), ("7B", 7e9)]:
        for n in [1, 4, 8]:
            for asama in [0, 1, 2, 3]:
                w = 4 * P / 1e9
                g = 4 * P / 1e9
                o = 8 * P / 1e9
                if asama == 0:
                    wg, gg, og = w, g, o
                elif asama == 1:
                    wg, gg, og = w, g, o / n
                elif asama == 2:
                    wg, gg, og = w, g / n, o / n
                else:
                    wg, gg, og = w / n, g / n, o / n
                satirlar.append(
                    (
                        ad,
                        n,
                        asama,
                        round(wg, 3),
                        round(gg, 3),
                        round(og, 3),
                        round(wg + gg + og, 3),
                    )
                )
    return satirlar


if __name__ == "__main__":
    main()
