# g04_amp.py: fp32 / fp16 AMP / bf16 AMP hız ve bellek ölçümü.
# Çıktı: engine/veri/b65_amp.csv
import csv, os, statistics, time
import torch
import torch.nn as nn

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
torch.manual_seed(0)


def model():
    return nn.Sequential(
        nn.Linear(4096, 4096), nn.ReLU(),
        nn.Linear(4096, 4096), nn.ReLU(),
        nn.Linear(4096, 10)).to(dev)


def adim(mod_kip, batch):
    net = model()
    opt = torch.optim.SGD(net.parameters(), lr=1e-3)
    x = torch.randn(batch, 4096, device=dev)
    y = torch.randint(0, 10, (batch,), device=dev)
    lossf = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=(mod_kip == "fp16"))

    def step():
        opt.zero_grad(set_to_none=True)
        kip_dt = torch.float16
        if mod_kip == "bf16":
            kip_dt = torch.bfloat16
        on = mod_kip != "fp32"
        with torch.autocast("cuda", dtype=kip_dt, enabled=on):
            loss = lossf(net(x), y)
        if mod_kip == "fp16":
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            loss.backward()
            opt.step()
        return loss

    for _ in range(10):
        step()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    step()
    torch.cuda.synchronize()
    bellek = torch.cuda.max_memory_allocated() / 2**20
    sureler = []
    for _ in range(3):
        t0 = time.perf_counter()
        for _ in range(20):
            step()
        torch.cuda.synchronize()
        sureler.append((time.perf_counter() - t0) / 20)
    del net, opt
    torch.cuda.empty_cache()
    return statistics.median(sureler) * 1000, bellek


sonuc = []
for batch in [256, 1024]:
    for kip in ["fp32", "fp16", "bf16"]:
        ms, mb = adim(kip, batch)
        sonuc.append((batch, kip, ms, mb))
        print("batch=%4d %s  adım=%8.2f ms  tepe bellek=%7.1f MB"
              % (batch, kip, ms, mb))

with open(os.path.join(KOK, "b65_amp.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["batch", "kip", "adim_ms", "tepe_bellek_mb"])
    for r in sonuc:
        w.writerow([r[0], r[1], "%.3f" % r[2], "%.1f" % r[3]])
