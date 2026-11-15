# ornek_spi.py: SPI CPOL/CPHA kiplerinde orneklem ve hazirlama anlari.
def kenarlar(sck_cpol):
    seviye, liste = sck_cpol, []
    for t in range(1, 17):
        seviye ^= 1
        liste.append((t, seviye))
    return liste

def anlar(sck_cpol, cpol, cpha):
    aktif = 1 - cpol                    # cihazin 'aktif' seviyesi
    onde = [t for t, s in kenarlar(sck_cpol) if s == aktif]
    arka = [t for t, s in kenarlar(sck_cpol) if s != aktif]
    if cpha == 0:
        return onde[:8], [0] + arka[:7]
    return arka[:8], onde[:8]

def degistir(a, b, ka, kb):
    """Ana (ka) ve uydu (kb) kipi; belirsiz bit 'X'."""
    sck = ka[0]
    ora, hra = anlar(sck, *ka)
    orb, hrb = anlar(sck, *kb)
    ba = [(a >> (7 - i)) & 1 for i in range(8)]
    bb = [(b >> (7 - i)) & 1 for i in range(8)]
    def oku(hazir, bits, t):
        if t in hazir:
            return "X"
        son = 0
        for i, th in enumerate(hazir):
            if th < t:
                son = bits[i]
        return son
    uydu = [oku(hra, ba, t) for t in orb]
    ana = [oku(hrb, bb, t) for t in ora]
    f = lambda L: "X" if "X" in L else "%02X" % sum(
        v << (7 - i) for i, v in enumerate(L))
    return f(ana), f(uydu)

if __name__ == "__main__":
    kipler = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for kb in kipler:
        print("ana (0,0) uydu %s -> ana alir, uydu alir: %s" % (
            kb, degistir(0xA5, 0x3C, (0, 0), kb)))
    print("ana (0,0), uydu (0,0):",
          degistir(0xA5, 0x3C, (0, 0), (0, 0)))
