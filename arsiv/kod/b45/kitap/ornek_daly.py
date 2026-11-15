# ornek_daly.py: Daly 13 bayt yanitini iki farkli sekilde coz.
def toplama8(v):
    return sum(v) & 0xFF

def yanit_90(volt, akim, soc):
    g = [0xA5, 0x01, 0x90, 0x08] + [0] * 8
    v, a, s = int(volt * 10), int(akim * 10) + 30000, int(soc * 10)
    g[4], g[5] = v >> 8, v & 0xFF
    g[8], g[9] = a >> 8, a & 0xFF
    g[10], g[11] = s >> 8, s & 0xFF
    g.append(toplama8(g))
    return g

def main_c_hucre(g):                     # main.c'deki hucre satiri
    return ((g[4] << 8) | g[5]) / 1000.0

def yanit_95(kare, mv):
    g = [0xA5, 0x01, 0x95, 0x08, kare]
    for m in mv:
        g += [m >> 8, m & 0xFF]
    g += [0] * (12 - len(g))
    g.append(toplama8(g))
    return g

if __name__ == "__main__":
    g = yanit_90(52.3, -12.5, 87.4)
    print("yanit :", " ".join("%02X" % x for x in g))
    print("toplama dogru:", toplama8(g[:12]) == g[12])
    h = list(g)
    h[4], h[5] = h[5], h[4]              # volt baytlari yer degisti
    print("yer degisimi, toplama dogru:", toplama8(h[:12]) == h[12])
    print("  gerilim = %.1f V" % (((h[4] << 8) | h[5]) / 10.0))
    k = yanit_95(1, [3300, 3287, 3312])
    print("0x95 yanit:", " ".join("%02X" % x for x in k))
    print("  main.c hucre = %.3f V" % main_c_hucre(k))
    print("  dogru hucre1 = %.3f V" % (((k[5] << 8) | k[6]) / 1000.0))
