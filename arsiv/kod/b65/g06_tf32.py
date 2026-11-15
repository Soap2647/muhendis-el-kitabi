# g06_tf32.py: TF32 hız ve hassasiyet farkı; OOM yakalama.
# Çıktı: engine/veri/b65_tf32.csv
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.manual_seed(0)
n = 4096
a = torch.randn(n, n)
b = torch.randn(n, n)
ref = (a.double() @ b.double())            # referans: float64 (CPU)
satir = []
for tf32 in (False, True):
    torch.backends.cuda.matmul.allow_tf32 = tf32
    ag, bg = a.to(dev), b.to(dev)
    # Isınma: GPU saat hızı yükselsin.
    for _ in range(20):
        c = ag @ bg
    torch.cuda.synchronize()
    sureler = []
    for _ in range(5):
        t0 = time.perf_counter()
        for _ in range(10):
            c = ag @ bg
        torch.cuda.synchronize()
        sureler.append((time.perf_counter() - t0) / 10)
    sure = sorted(sureler)[2]              # medyan
    rel = ((c.cpu().double() - ref).norm() / ref.norm()).item()
    ad = "tf32" if tf32 else "fp32"
    satir.append((ad, sure, rel))
    print("%s  süre=%.5f s  göreli hata=%.3e  TFLOPS=%.2f"
          % (ad, sure, rel, 2 * n ** 3 / sure / 1e12))

with open(os.path.join(KOK, "b65_tf32.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kip", "sure_s", "goreli_hata"])
    for r in satir:
        w.writerow([r[0], "%.6f" % r[1], "%.3e" % r[2]])
