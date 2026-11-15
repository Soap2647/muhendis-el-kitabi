# g07_oom.py: (a) Windows sysmem fallback ile sınırsız görünen bellek,
# (b) set_per_process_memory_fraction ile gerçek OOM yakalama.
# Çıktı: engine/veri/b65_oom.csv
import csv, os, time
import torch
KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")


def dene(batch):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    try:
        net = torch.nn.Sequential(*[torch.nn.Sequential(
            torch.nn.Linear(1024, 1024), torch.nn.ReLU())
            for _ in range(24)]).to(dev)
        x = torch.randn(batch, 1024, device=dev)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        net(x).sum().backward()
        torch.cuda.synchronize()
        sonuc = (torch.cuda.max_memory_allocated() / 2**20,
                 time.perf_counter() - t0, "sığdı")
    except torch.cuda.OutOfMemoryError:
        sonuc = (float("nan"), float("nan"), "OOM")
    net = x = None
    torch.cuda.empty_cache()
    return sonuc


satir = []
print("(a) sınır yok, kart 6143 MB:")
for batch in [16384, 65536, 131072]:
    mb, s, d = dene(batch)
    satir.append(("sinirsiz", batch, mb, s, d))
    print("  batch=%6d tepe=%8.0f MB süre=%6.2f s %s"
          % (batch, mb, s, d))

torch.cuda.set_per_process_memory_fraction(0.25)   # ~1536 MB sınır
print("(b) bellek sınırı %25 (~1536 MB):")
for batch in [4096, 16384]:
    mb, s, d = dene(batch)
    satir.append(("sinir_25yuzde", batch, mb, s, d))
    print("  batch=%6d tepe=%8.0f MB süre=%6.2f s %s"
          % (batch, mb, s, d))

with open(os.path.join(KOK, "b65_oom.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kosul", "batch", "tepe_mb", "sure_s", "durum"])
    for r in satir:
        w.writerow([r[0], r[1], "" if r[2] != r[2] else "%.0f" % r[2],
                    "" if r[3] != r[3] else "%.3f" % r[3], r[4]])
