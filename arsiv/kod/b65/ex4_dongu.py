# ex4_dongu.py: Çözümlü Örnek 4 - yavaş ve düzeltilmiş döngü.
# Worker başlatma süresi ölçüme girmez: DataLoader bir kez kurulur,
# bir ısınma epoch'u koşulur, sonra yalnızca epoch süresi alınır.
import statistics
import time

import torch
from torch.utils.data import DataLoader

from g08_veri import DigitGenis, ag


def epoch_yavas(dl, net, opt, dev):
    lossf = torch.nn.CrossEntropyLoss()
    toplam = 0.0
    for x, y in dl:
        x, y = x.to(dev), y.to(dev)
        out = net(x)
        loss = lossf(out, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        toplam += loss.item()                # her adımda senkron
        tahmin = out.argmax(1).cpu().numpy()  # her adımda kopya
        _ = (tahmin == y.cpu().numpy()).mean()
    return toplam


def epoch_hizli(dl, net, opt, dev):
    lossf = torch.nn.CrossEntropyLoss()
    toplam = torch.zeros((), device=dev)
    for x, y in dl:
        x = x.to(dev, non_blocking=True)
        y = y.to(dev, non_blocking=True)
        out = net(x)
        loss = lossf(out, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        toplam += loss.detach()              # senkron yok
    return toplam.item()


if __name__ == "__main__":
    dev = torch.device("cuda")
    torch.manual_seed(0)
    ds = DigitGenis(4096)
    dl_y = DataLoader(ds, batch_size=64, shuffle=True,
                      num_workers=0)
    dl_h = DataLoader(ds, batch_size=64, shuffle=True, num_workers=4,
                      pin_memory=True, persistent_workers=True)
    sonuc = {}
    for ad, fn, dl in (("yavas", epoch_yavas, dl_y),
                       ("hizli", epoch_hizli, dl_h)):
        net = ag().to(dev)
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        fn(dl, net, opt, dev)                # ısınma
        torch.cuda.synchronize()
        sure = []
        for _ in range(3):
            t0 = time.perf_counter()
            fn(dl, net, opt, dev)
            torch.cuda.synchronize()
            sure.append(time.perf_counter() - t0)
        sonuc[ad] = statistics.median(sure)
        print("%-6s medyan epoch = %.3f s  (tekrarlar: %s)"
              % (ad, sonuc[ad], ", ".join("%.3f" % s for s in sure)))
    print("oran yavas/hizli = %.2f"
          % (sonuc["yavas"] / sonuc["hizli"]))
