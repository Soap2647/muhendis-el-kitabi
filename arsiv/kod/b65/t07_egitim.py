# t07_egitim.py: kanonik eğitim döngüsü, checkpoint ile devam,
# gradyan birikimi eşdeğerliği. Çıktı: engine/veri/b65_egitim.csv
import csv, os, random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = "C:/Users/merty/AppData/Local/Temp/b65/ck.pt"


def tohumla(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)


X, y = load_digits(return_X_y=True)
X = torch.tensor(X / 16.0, dtype=torch.float32)
y = torch.tensor(y)
Xtr, Xgec, ytr, ygec = train_test_split(X, y, test_size=0.3,
                                        stratify=y, random_state=0)
Xva, Xte, yva, yte = train_test_split(Xgec, ygec, test_size=0.5,
                                      stratify=ygec, random_state=0)


def model():
    return nn.Sequential(nn.Linear(64, 128), nn.ReLU(),
                         nn.Dropout(0.1), nn.Linear(128, 10))


def dogruluk(net, X_, y_):
    net.eval()
    with torch.no_grad():
        return (net(X_).argmax(1) == y_).float().mean().item()


def egit(net, opt, sched, dl, bas, son,
         ck_yolu=None, log=None, gen=None):
    lossf = nn.CrossEntropyLoss()
    for ep in range(bas, son):
        net.train()
        toplam = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            l = lossf(net(xb), yb)
            l.backward()
            opt.step()
            toplam += l.item() * len(xb)
        lr = opt.param_groups[0]["lr"]      # bu epoch'ta kullanılan
        sched.step()
        net.eval()
        with torch.no_grad():
            vl = lossf(net(Xva), yva).item()
        va = dogruluk(net, Xva, yva)
        if log is not None:
            log.append((ep + 1, toplam / len(dl.dataset), vl, va, lr))
        if ck_yolu:
            torch.save({"model": net.state_dict(),
                        "opt": opt.state_dict(),
                        "sched": sched.state_dict(),
                        "epoch": ep + 1,
                        "rng_torch": torch.get_rng_state(),
                        "rng_gen": gen.get_state() if gen else None},
                       ck_yolu)
    return net


def kur(seed):
    tohumla(seed)
    net = model()
    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=3,
                                            gamma=0.5)
    gen = torch.Generator().manual_seed(seed)
    dl = DataLoader(TensorDataset(Xtr, ytr), batch_size=64,
                    shuffle=True, generator=gen)
    return net, opt, sched, dl, gen


# 1) Kesintisiz 8 epoch.
net, opt, sched, dl, gen = kur(0)
log = []
egit(net, opt, sched, dl, 0, 8, log=log, gen=gen)
ref = {k: v.clone() for k, v in net.state_dict().items()}
print("epoch  egitim_kayip  val_kayip  val_dogr  lr")
for r in log:
    print("%5d  %12.4f  %9.4f  %8.4f  %.5f" % r)
with open(os.path.join(KOK, "b65_egitim.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["epoch", "egitim_kayip", "val_kayip", "val_dogruluk",
                "lr"])
    for r in log:
        w.writerow([r[0], "%.5f" % r[1], "%.5f" % r[2], "%.4f" % r[3],
                    "%.6f" % r[4]])
print("test doğruluğu (kesintisiz, bir kez):",
      "%.4f" % dogruluk(net, Xte, yte))

# 2) 4 epoch + checkpoint, sonra YENİ nesnelerle 4 epoch daha.
net, opt, sched, dl, gen = kur(0)
egit(net, opt, sched, dl, 0, 4, ck_yolu=CK, gen=gen)
net2, opt2, sched2, _, _ = kur(123)         # farklı başlangıç
ck = torch.load(CK, weights_only=True)
net2.load_state_dict(ck["model"])
opt2.load_state_dict(ck["opt"])
sched2.load_state_dict(ck["sched"])
torch.set_rng_state(ck["rng_torch"])
gen2 = torch.Generator()
gen2.set_state(ck["rng_gen"])
dl2 = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True,
                 generator=gen2)
egit(net2, opt2, sched2, dl2, ck["epoch"], 8, gen=gen2)
fark = max((ref[k] - v).abs().max().item()
           for k, v in net2.state_dict().items())
print("\ncheckpoint sonrası en büyük parametre farkı:", fark)

# 3) Yanlış devam: RNG durumu yüklenmezse.
net3, opt3, sched3, _, _ = kur(123)
ck = torch.load(CK, weights_only=True)
net3.load_state_dict(ck["model"]); opt3.load_state_dict(ck["opt"])
sched3.load_state_dict(ck["sched"])
dl3 = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True,
                 generator=torch.Generator().manual_seed(0))
egit(net3, opt3, sched3, dl3, ck["epoch"], 8)
fark3 = max((ref[k] - v).abs().max().item()
            for k, v in net3.state_dict().items())
print("RNG yüklenmeden devam, en büyük fark: %.3e" % fark3)

# 4) Gradyan birikimi: 4 x 64 mikro-batch == 256 batch (dropout yok).
torch.set_default_dtype(torch.float64)
tohumla(0)
A = nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Linear(32, 10))
B = nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Linear(32, 10))
B.load_state_dict(A.state_dict())
xb, yb = Xtr[:256].double(), ytr[:256]
lossf = nn.CrossEntropyLoss()
lossf(A(xb), yb).backward()                 # tek büyük batch
for i in range(4):
    mx = xb[i * 64:(i + 1) * 64]
    my = yb[i * 64:(i + 1) * 64]
    (lossf(B(mx), my) / 4).backward()       # 1/4 ölçekleme şart
fk = max((pa.grad - pb.grad).abs().max().item()
         for pa, pb in zip(A.parameters(), B.parameters()))
print("birikim (doğru 1/4): en büyük gradyan farkı: %.3e" % fk)
for p in B.parameters():
    p.grad = None
for i in range(4):
    (lossf(B(xb[i*64:(i+1)*64]), yb[i*64:(i+1)*64])).backward()
fk2 = max((pa.grad - pb.grad).abs().max().item()
          for pa, pb in zip(A.parameters(), B.parameters()))
print("birikim (ölçeksiz):  en büyük gradyan farkı: %.3e" % fk2)
torch.set_default_dtype(torch.float32)
