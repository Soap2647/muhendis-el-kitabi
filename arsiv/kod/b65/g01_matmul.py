# g01_matmul.py: CPU ve GPU matris çarpım süresi, boyuta göre.
# Çıktı: engine/veri/b65_matmul.csv. Isınma koşusu ve senkronizasyon.
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
torch.manual_seed(0)
torch.set_num_threads(os.cpu_count())
dev = torch.device("cuda")


def olc(fn, tekrar, senk):
    # Zamanlama: GPU işi asenkron olduğundan senkronize etmeden
    # süre ölçülmez. Ortalama tekrar üzerinden.
    fn()
    if senk:
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(tekrar):
        fn()
    if senk:
        torch.cuda.synchronize()
    return (time.perf_counter() - t0) / tekrar


satirlar = []
for n in [32, 64, 128, 256, 512, 1024, 2048, 3072]:
    a = torch.randn(n, n)
    b = torch.randn(n, n)
    ag, bg = a.to(dev), b.to(dev)
    tekrar_cpu = max(2, int(2e8 // (2 * n ** 3)) + 1)
    tekrar_gpu = max(5, int(2e9 // (2 * n ** 3)) + 1)
    tcpu = olc(lambda: a @ b, min(tekrar_cpu, 50), False)
    tgpu = olc(lambda: ag @ bg, tekrar_gpu, True)
    # Gerçek hesap: CPU'dan GPU'ya kopya dahil süre.
    tkop = olc(lambda: (a.to(dev) @ bg), tekrar_gpu, True)
    satirlar.append((n, tcpu, tgpu, tkop))
    print("n=%5d  cpu=%10.6f s  gpu=%10.6f s  gpu+kopya=%10.6f s"
          % (n, tcpu, tgpu, tkop))

with open(os.path.join(KOK, "b65_matmul.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "cpu_s", "gpu_s", "gpu_kopya_s"])
    for r in satirlar:
        w.writerow([r[0], "%.8f" % r[1], "%.8f" % r[2],
                    "%.8f" % r[3]])
