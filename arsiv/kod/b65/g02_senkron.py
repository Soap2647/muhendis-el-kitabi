# g02_senkron.py: GPU zamanlaması, senkronizasyon ve kopya maliyeti.
# Çıktı: engine/veri/b65_senkron.csv, engine/veri/b65_kopya.csv
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
x = torch.randn(3072, 3072, device=dev)
for _ in range(5):
    y = x @ x
torch.cuda.synchronize()

# 1) Yanlış ölçüm: senkronizasyon yok, çağrı süresi ölçülür.
t0 = time.perf_counter()
for _ in range(20):
    y = x @ x
t_yanlis = (time.perf_counter() - t0) / 20
torch.cuda.synchronize()
t_bitis = (time.perf_counter() - t0) / 20

# 2) Doğru ölçüm: önce ve sonra senkronize et.
torch.cuda.synchronize()
t0 = time.perf_counter()
for _ in range(20):
    y = x @ x
torch.cuda.synchronize()
t_dogru = (time.perf_counter() - t0) / 20

# 3) CUDA event ile GPU'nun kendi süresi.
e1 = torch.cuda.Event(enable_timing=True)
e2 = torch.cuda.Event(enable_timing=True)
e1.record()
for _ in range(20):
    y = x @ x
e2.record()
torch.cuda.synchronize()
t_event = e1.elapsed_time(e2) / 1000 / 20

print("yanlış (senkronsuz çağrı):  %.6f s" % t_yanlis)
print("senkron sonrası toplam:     %.6f s" % t_bitis)
print("doğru (synchronize ile):    %.6f s" % t_dogru)
print("CUDA event (GPU süresi):    %.6f s" % t_event)

# 4) Küçük işlemler: her adımda .item() senkronizasyonu.
s = torch.zeros(1, device=dev)
t0 = time.perf_counter()
for _ in range(2000):
    s += 1
torch.cuda.synchronize()
t_toplu = (time.perf_counter() - t0) / 2000
t0 = time.perf_counter()
for _ in range(2000):
    s += 1
    _ = s.item()
t_item = (time.perf_counter() - t0) / 2000
print("\n2000 küçük işlem, adım başına:")
print("  senkronsuz:            %.2f us" % (t_toplu * 1e6))
print("  her adımda .item():    %.2f us" % (t_item * 1e6))

# 5) Kopya: sayfalanabilir (pageable) ve pinned bellek.
boyut = [1, 4, 16, 64]
kopya = []
for mb in boyut:
    n = mb * 1024 * 1024 // 4
    h = torch.randn(n)
    hp = h.pin_memory()
    d = torch.empty(n, device=dev)
    def kop(src, nb):
        d.copy_(src, non_blocking=nb)
    for _ in range(3):
        kop(h, False)
    torch.cuda.synchronize()
    r = []
    for src, nb in ((h, False), (hp, True)):
        t0 = time.perf_counter()
        for _ in range(10):
            kop(src, nb)
        torch.cuda.synchronize()
        r.append((time.perf_counter() - t0) / 10)
    kopya.append((mb, r[0], r[1]))
    print("%3d MB  pageable=%.5f s  pinned=%.5f s"
          % (mb, r[0], r[1]))
    print("     GB/s: pageable=%.2f  pinned=%.2f"
          % (mb / 1024 / r[0], mb / 1024 / r[1]))

with open(os.path.join(KOK, "b65_senkron.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["olcum", "sure_s"])
    w.writerow(["yanlis_senkronsuz", "%.8f" % t_yanlis])
    w.writerow(["senkron_sonrasi_toplam", "%.8f" % t_bitis])
    w.writerow(["dogru_synchronize", "%.8f" % t_dogru])
    w.writerow(["cuda_event", "%.8f" % t_event])
with open(os.path.join(KOK, "b65_kopya.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["mb", "pageable_s", "pinned_s"])
    for r in kopya:
        w.writerow([r[0], "%.8f" % r[1], "%.8f" % r[2]])
