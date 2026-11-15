# g08_veri.py: DataLoader num_workers, pin_memory ve GPU'nun veri
# beklemesi. Çıktı: engine/veri/b65_veri.csv
import csv, os, time
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from scipy import ndimage
from sklearn.datasets import load_digits

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"


class DigitGenis(Dataset):
    # 1797 rakamı 32x32'ye büyütür; her örnek için rastgele döndürme
    # ve bulanıklaştırma yapar. Bu işlem CPU'da çalışır: bilerek
    # pahalı tutuldu ki worker etkisi ölçülebilsin.
    def __init__(self, n):
        X, y = load_digits(return_X_y=True)
        X = X.reshape(-1, 8, 8) / 16.0
        self.X = np.stack([ndimage.zoom(im, 4, order=1) for im in X])
        self.y = y
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        rng = np.random.default_rng(i)
        k = i % len(self.X)
        im = ndimage.rotate(self.X[k], rng.uniform(-20, 20),
                            reshape=False, order=1)
        im = ndimage.gaussian_filter(im, 0.8)
        im = im + rng.normal(0, 0.02, im.shape)
        return torch.from_numpy(im).float()[None], int(self.y[k])


def ag():
    return torch.nn.Sequential(
        torch.nn.Conv2d(1, 16, 3, padding=1), torch.nn.ReLU(),
        torch.nn.MaxPool2d(2),
        torch.nn.Conv2d(16, 32, 3, padding=1), torch.nn.ReLU(),
        torch.nn.MaxPool2d(2),
        torch.nn.Flatten(), torch.nn.Linear(32 * 8 * 8, 10))


def turu(workers, pin, dev):
    torch.manual_seed(0)
    ds = DigitGenis(4096)
    dl = DataLoader(ds, batch_size=64, shuffle=True,
                    num_workers=workers, pin_memory=pin,
                    persistent_workers=workers > 0)
    net = ag().to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    bekleme = 0.0
    gpu_sure = 0.0
    adim = 0
    for ep in range(2):          # 1. tur ısınma (worker başlatma)
        if ep == 1:
            t_ep = time.perf_counter()
            bekleme = 0.0
            gpu_sure = 0.0
            adim = 0
        t_once = time.perf_counter()
        it = iter(dl)
        while True:
            t0 = time.perf_counter()
            try:
                x, y = next(it)
            except StopIteration:
                break
            bekleme += time.perf_counter() - t0
            t1 = time.perf_counter()
            x = x.to(dev, non_blocking=pin)
            y = y.to(dev, non_blocking=pin)
            loss = torch.nn.functional.cross_entropy(net(x), y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            torch.cuda.synchronize() if dev.type == "cuda" else None
            gpu_sure += time.perf_counter() - t1
            adim += 1
    toplam = time.perf_counter() - t_ep
    return toplam, bekleme, gpu_sure, adim


if __name__ == "__main__":
    dev = torch.device("cuda")
    satir = []
    for w, pin in [(0, False), (1, False), (2, False), (4, False),
                   (4, True), (8, True)]:
        toplam, bek, gsu, adim = turu(w, pin, dev)
        satir.append((w, pin, toplam, bek, gsu, adim))
        print("workers=%d pin=%-5s tur=%6.2f s  veri_bekleme=%6.2f s"
              % (w, pin, toplam, bek))
        print("  gpu_adim=%5.2f s  adim=%d" % (gsu, adim))
    with open(os.path.join(KOK, "b65_veri.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["workers", "pin", "tur_s", "veri_bekleme_s",
                     "gpu_adim_s", "adim"])
        for r in satir:
            wr.writerow([r[0], r[1], "%.3f" % r[2], "%.3f" % r[3],
                         "%.3f" % r[4], r[5]])
