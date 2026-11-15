# g05_bellek.py: aktivasyon belleği, OOM, checkpointing ve AMP bellek.
# Çıktı: engine/veri/b65_bellek.csv
import csv, os, time
import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint_sequential

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.backends.cuda.matmul.allow_tf32 = False
torch.manual_seed(0)
DERIN, GENIS = 24, 1024


def ag():
    katman = []
    for _ in range(DERIN):
        katman += [nn.Linear(GENIS, GENIS), nn.ReLU()]
    return nn.Sequential(*katman, nn.Linear(GENIS, 10)).to(dev)


def olc(batch, kip, dene=True):
    net = ag()
    opt = torch.optim.SGD(net.parameters(), lr=1e-4)
    x = torch.randn(batch, GENIS, device=dev)
    y = torch.randint(0, 10, (batch,), device=dev)
    lossf = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=(kip == "fp16"))

    def step():
        opt.zero_grad(set_to_none=True)
        if kip == "ckpt":
            # 24 doğrusal+ReLU çifti 6 bloğa bölünür; blok girdileri
            # saklanır, iç aktivasyonlar ileri geçişte silinir.
            out = checkpoint_sequential(net, 6, x,
                                        use_reentrant=False)
            loss = lossf(out, y)
            loss.backward()
            opt.step()
            return
        with torch.autocast("cuda", dtype=torch.float16,
                            enabled=(kip == "fp16")):
            loss = lossf(net(x), y)
        if kip == "fp16":
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            loss.backward()
            opt.step()

    try:
        step()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        step()
        torch.cuda.synchronize()
        bellek = torch.cuda.max_memory_allocated() / 2**20
        t0 = time.perf_counter()
        for _ in range(5):
            step()
        torch.cuda.synchronize()
        sure = (time.perf_counter() - t0) / 5 * 1000
        sonuc = (bellek, sure, "tamam")
    except torch.cuda.OutOfMemoryError:
        sonuc = (float("nan"), float("nan"), "OOM")
    del net, opt
    torch.cuda.empty_cache()
    return sonuc


satir = []
for batch in [128, 256, 512, 1024, 2048, 4096]:
    for kip in ["fp32", "fp16", "ckpt"]:
        mb, ms, durum = olc(batch, kip)
        satir.append((batch, kip, mb, ms, durum))
        print("batch=%5d %-5s tepe=%8.1f MB  adım=%8.2f ms  %s"
              % (batch, kip, mb, ms, durum))

with open(os.path.join(KOK, "b65_bellek.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["batch", "kip", "tepe_bellek_mb", "adim_ms", "durum"])
    for r in satir:
        w.writerow([r[0], r[1], "%.1f" % r[2] if r[2] == r[2] else "",
                    "%.2f" % r[3] if r[3] == r[3] else "", r[4]])
