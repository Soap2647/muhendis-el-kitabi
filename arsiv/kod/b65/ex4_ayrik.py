# ex4_ayrik.py: Çözümlü Örnek 4 - worker ve senkron etkisinin ayrımı.
import statistics
import time

import torch
from torch.utils.data import DataLoader

from ex4_dongu import epoch_hizli, epoch_yavas
from g08_veri import DigitGenis, ag

if __name__ == "__main__":
    dev = torch.device("cuda")
    torch.manual_seed(0)
    ds = DigitGenis(4096)
    dl0 = DataLoader(ds, batch_size=64, shuffle=True, num_workers=0)
    dl4 = DataLoader(ds, batch_size=64, shuffle=True, num_workers=4,
                     pin_memory=True, persistent_workers=True)
    vaka = [("worker yok + item (yavas)", epoch_yavas, dl0),
            ("worker=4 + item", epoch_yavas, dl4),
            ("worker yok + senkronsuz", epoch_hizli, dl0),
            ("worker=4 + senkronsuz (hizli)", epoch_hizli, dl4)]
    for ad, fn, dl in vaka:
        net = ag().to(dev)
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        fn(dl, net, opt, dev)
        torch.cuda.synchronize()
        sure = []
        for _ in range(3):
            t0 = time.perf_counter()
            fn(dl, net, opt, dev)
            torch.cuda.synchronize()
            sure.append(time.perf_counter() - t0)
        print("%-32s medyan = %.3f s"
              % (ad, statistics.median(sure)))
