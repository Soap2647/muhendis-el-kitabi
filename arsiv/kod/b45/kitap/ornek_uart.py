# ornek_uart.py: 8N1 UART'in saat sapmasi toleransi (simulasyon).
def cerceve(bayt):
    bitler = [0] + [(bayt >> i) & 1 for i in range(8)] + [1]
    return bitler

def coz(bayt, d):
    bitler = cerceve(bayt)
    tr = 1.0 + d                         # alici bit suresi (T = 1)
    ornek = []
    for k in range(len(bitler)):
        t = (k + 0.5) * tr               # bit ortasi
        ornek.append(bitler[int(t)] if t < len(bitler) else 1)
    if ornek[0] != 0 or ornek[9] != 1:
        return None
    return sum(b << i for i, b in enumerate(ornek[1:9]))

def hepsi_dogru(d):
    return all(coz(b, d) == b for b in range(256))

def sinir(yon):
    d, adim = 0.0, 0.0001 * yon
    while hepsi_dogru(d + adim):
        d += adim
    return d

if __name__ == "__main__":
    print("0x4B cerceve:", "".join(map(str, cerceve(0x4B))))
    print("d=0 -> 0x4B:", "%02X" % coz(0x4B, 0.0))
    print("d=+4%% -> 0x4B: %02X" % coz(0x4B, 0.04))
    print("tolerans +: %+.2f %%" % (sinir(1) * 100))
    print("tolerans -: %+.2f %%" % (sinir(-1) * 100))
    print("teorik 0,5/9,5 = %.2f %%" % (0.5 / 9.5 * 100))
