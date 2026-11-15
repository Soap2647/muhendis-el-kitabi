# g09_tekrar.py: GPU tekrarlanabilirligi ve AMP'nin dogrulugu.
# Çıktı: engine/veri/b65_tekrar.csv
import csv, os, statistics
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
satir = []

# (a) Atomik toplama: aynı tohum, aynı girdi, 6 tekrar.
def atomik():
    torch.manual_seed(0)
    idx = torch.randint(0, 8, (2_000_000,), device=dev)
    deg = torch.randn(2_000_000, device=dev)
    out = torch.zeros(8, device=dev)
    out.index_add_(0, idx, deg)
    return out.cpu()

sonuc = [atomik() for _ in range(6)]
farkli = len({tuple(s.tolist()) for s in sonuc})
print("index_add_ (GPU), 6 koşu, farklı sonuç sayısı:", farkli)
satir.append(("index_add_ varsayilan", farkli))
torch.use_deterministic_algorithms(True)
sonuc = [atomik() for _ in range(6)]
farkli = len({tuple(s.tolist()) for s in sonuc})
print("index_add_ deterministic=True, farklı sonuç:", farkli)
satir.append(("index_add_ deterministic", farkli))
torch.use_deterministic_algorithms(False)

# (b) Konvolüsyon geri yayılımı: iki koşu bit düzeyinde aynı mı?
def conv_gradyan():
    torch.manual_seed(0)
    c = nn.Conv2d(16, 32, 3, padding=1).to(dev)
    x = torch.randn(64, 16, 32, 32, device=dev)
    c(x).sum().backward()
    return c.weight.grad.clone().cpu()

torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = True
g1, g2 = conv_gradyan(), conv_gradyan()
print("conv (deterministic=True) bit aynı mı:", torch.equal(g1, g2))
satir.append(("conv deterministic bit-aynı",
             int(torch.equal(g1, g2))))

# (c) AMP doğruluğu: 3 tohum, fp32 vs fp16 AMP; test doğruluğu ayrıca.
X, y = load_digits(return_X_y=True)
X = torch.tensor(X / 16.0, dtype=torch.float32)
y = torch.tensor(y)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2,
                                      stratify=y, random_state=0)
Xtr, ytr = Xtr.to(dev), ytr.to(dev)
Xte, yte = Xte.to(dev), yte.to(dev)

def egit(seed, amp):
    torch.manual_seed(seed)
    net = nn.Sequential(nn.Linear(64, 256), nn.ReLU(),
                        nn.Linear(256, 10)).to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    sc = torch.amp.GradScaler("cuda", enabled=amp)
    lossf = nn.CrossEntropyLoss()
    for ep in range(30):
        perm = torch.randperm(len(Xtr), device=dev)
        for i in range(0, len(Xtr), 64):
            b = perm[i:i + 64]
            with torch.autocast("cuda", dtype=torch.float16,
                                enabled=amp):
                l = lossf(net(Xtr[b]), ytr[b])
            opt.zero_grad()
            sc.scale(l).backward()
            sc.step(opt)
            sc.update()
    net.eval()
    with torch.no_grad():
        tr = (net(Xtr).argmax(1) == ytr).float().mean().item()
        te = (net(Xte).argmax(1) == yte).float().mean().item()
    return tr, te

for amp in (False, True):
    trs, tes = [], []
    for s in range(3):
        tr, te = egit(s, amp)
        trs.append(tr); tes.append(te)
    ad = "fp16-AMP" if amp else "fp32"
    print("%-9s eğitim=%.4f±%.4f  TEST=%.4f±%.4f"
          % (ad, statistics.mean(trs), statistics.pstdev(trs),
             statistics.mean(tes), statistics.pstdev(tes)))
    satir.append((ad + " egitim_dogruluk",
                  "%.4f" % statistics.mean(trs)))
    satir.append((ad + " test_dogruluk",
                  "%.4f+-%.4f" % (statistics.mean(tes),
                                  statistics.pstdev(tes))))

with open(os.path.join(KOK, "b65_tekrar.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["olcum", "deger"])
    for r in satir:
        w.writerow(r)
