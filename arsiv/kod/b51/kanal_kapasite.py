# kanal_kapasite.py: BSC kapasitesi C = 1 - H(p), veri işleme
# eşitsizliği (iki BSC'nin zinciri) ve Shannon-Hartley
# C = B log2(1 + S/N).
import math
import random

def h2(p):
    # İkili entropi (bit)
    if p in (0.0, 1.0):
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)

def bsc_karsilikli(p):
    # Düzgün girdi, BSC(p): I(X;Y) = H(Y) - H(Y|X) = 1 - H(p)
    # Ortak tablodan hesaplayıp formülle karşılaştır.
    ortak = {(0, 0): 0.5 * (1 - p), (0, 1): 0.5 * p,
             (1, 0): 0.5 * p, (1, 1): 0.5 * (1 - p)}
    py = {y: sum(v for (x, yy), v in ortak.items() if yy == y)
          for y in (0, 1)}
    hy = -sum(v * math.log2(v) for v in py.values() if v > 0)
    hyx = -sum(v * math.log2(v / 0.5)
               for v in ortak.values() if v > 0)
    return hy - hyx

def zincir(p1, p2):
    # X -> Y (BSC p1) -> Z (BSC p2): Z'nin çapraz olma olasılığı
    return p1 * (1 - p2) + (1 - p1) * p2

def simule_zincir(p1, p2, n=200000, tohum=51):
    # Örnek tabanlı I(X;Z) tahmini (plug-in)
    rnd = random.Random(tohum)
    sayim = {}
    for _ in range(n):
        x = rnd.randrange(2)
        y = x ^ (rnd.random() < p1)
        z = y ^ (rnd.random() < p2)
        sayim[(x, z)] = sayim.get((x, z), 0) + 1
    px = {0: 0.0, 1: 0.0}
    pz = {0: 0.0, 1: 0.0}
    for (x, z), c in sayim.items():
        px[x] += c / n
        pz[z] += c / n
    i = 0.0
    for (x, z), c in sayim.items():
        pxz = c / n
        i += pxz * math.log2(pxz / (px[x] * pz[z]))
    return i

def main():
    print("BSC kapasitesi C(p) = 1 - H(p)")
    for p in [0.0, 0.01, 0.05, 0.11, 0.5]:
        print("p=%.2f  C=%.4f  I(formul)=%.4f" % (
            p, 1 - h2(p), bsc_karsilikli(p)))
    print("--- veri isleme esitsizligi: I(X;Z) <= I(X;Y) ---")
    p1 = 0.05
    for p2 in [0.0, 0.05, 0.2]:
        iy = 1 - h2(p1)
        iz = 1 - h2(zincir(p1, p2))
        sim = simule_zincir(p1, p2)
        print("p2=%.2f  I(X;Y)=%.4f  I(X;Z)=%.4f  simulasyon=%.4f" % (
            p2, iy, iz, sim))
    print("--- Shannon-Hartley: C = B log2(1 + S/N) ---")
    for b_mhz, snr_db in [(1, 0), (1, 10), (10, 10), (10, 20)]:
        snr = 10 ** (snr_db / 10)
        c = b_mhz * 1e6 * math.log2(1 + snr)
        print("B=%2d MHz, SNR=%2d dB -> C = %.2f Mbit/s" % (
            b_mhz, snr_db, c / 1e6))
    # Ters soru: 5 Mbit/s için gereken bant genişliği (SNR = 10 dB)
    snr = 10 ** (10 / 10)
    b = 5e6 / math.log2(1 + snr)
    print("5 Mbit/s icin gereken B = %.3f MHz (SNR 10 dB)"
          % (b / 1e6))


if __name__ == "__main__":
    main()
