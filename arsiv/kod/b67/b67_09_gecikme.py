# -*- coding: utf-8 -*-
# b67_09_gecikme.py: gecikme olcumu. GPU'da dedektor (ag ileri gecis
# ve son isleme), CPU'da takipci. Girdi boyutu ve karisik hassasiyet
# (fp16) karsilastirilir. Olcumden once GPU'nun bos oldugu dogrulanir.
import os
import subprocess
import time
import numpy as np
import torch
from b67_04_yolo_mini import MiniYolo, decode, AYGIT, VERI, KLASOR
from b67_veri import video, veri_seti
from b67_08_takip import Izleyici

N_OLCUM, N_ISINMA = 200, 30


def gpu_durumu():
    return subprocess.run(
        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
         "--format=csv,noheader"],
        capture_output=True, text=True).stdout.strip()


def ag_suresi(model, boyut, fp16=False):
    """Yalnizca ag ileri gecisi; her olcum CUDA senkronizasyonlu."""
    x = torch.rand(1, 1, boyut, boyut, device=AYGIT)
    sure = []
    with torch.no_grad(), torch.autocast("cuda", torch.float16,
                                         enabled=fp16):
        for _ in range(N_ISINMA):
            model(x)
        torch.cuda.synchronize()
        for _ in range(N_OLCUM):
            t0 = time.perf_counter()
            model(x)
            torch.cuda.synchronize()
            sure.append(time.perf_counter() - t0)
    sure = np.array(sure) * 1e3
    return float(np.median(sure)), float(np.percentile(sure, 90))


def son_isleme_suresi(model, X):
    """Gercek 96 px sahnelerde karar + NMS suresi (CPU), ms."""
    with torch.no_grad():
        ham = model(torch.tensor(X[:1], device=AYGIT)).cpu().numpy()
    sure = []
    for _ in range(N_OLCUM):
        t0 = time.perf_counter()
        decode(ham)
        sure.append(time.perf_counter() - t0)
    return float(np.median(np.array(sure) * 1e3))


def takipci_suresi():
    """macar_tum takipcisi, kare basina CPU suresi (ms)."""
    kareler = video(seed=100)
    izci = Izleyici("macar_tum")
    t0 = time.perf_counter()
    for k in kareler:
        izci.guncelle(k["det"], k["skor"])
    return (time.perf_counter() - t0) * 1e3 / len(kareler)


if __name__ == "__main__":
    print("GPU durumu (olcum oncesi):", gpu_durumu())
    model = MiniYolo().to(AYGIT)
    # yalnizca tensor sozlugu yukleniyor (weights_only=True)
    model.load_state_dict(torch.load(
        os.path.join(KLASOR, "yolo_t1.pt"), map_location=AYGIT,
        weights_only=True))
    model.eval()
    X, _, _ = veri_seti(8, seed=777)
    print("GPU adi:", torch.cuda.get_device_name(0))
    satirlar = ["boyut,hassasiyet,ag_medyan_ms,ag_p90_ms,fps"]
    for boyut in (96, 192, 384):
        for fp16 in (False, True):
            med, p90 = ag_suresi(model, boyut, fp16)
            ad = "fp16" if fp16 else "fp32"
            print("%3d px  %s  ag medyan=%.2f ms  p90=%.2f ms  "
                  "(~%.0f FPS)" % (boyut, ad, med, p90, 1000 / med))
            satirlar.append("%d,%s,%.3f,%.3f,%.1f"
                            % (boyut, ad, med, p90, 1000 / med))
    son = son_isleme_suresi(model, X)
    tak = takipci_suresi()
    print("son isleme (96 px, NMS dahil) medyan = %.3f ms" % son)
    print("takipci (macar_tum, CPU) kare basina = %.3f ms" % tak)
    print("GPU durumu (olcum sonrasi):", gpu_durumu())
    with open(os.path.join(VERI, "b67_gecikme.csv"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
        f.write("# son_isleme_ms=%.3f, takipci_ms=%.3f\n"
                % (son, tak))
