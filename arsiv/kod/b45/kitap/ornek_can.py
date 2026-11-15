# ornek_can.py: CAN CRC-15, bit doldurma ve tahkim (ideal hat).
def crc15(bitler):
    crc = 0
    for bit in bitler:
        geri = ((crc >> 14) & 1) ^ bit
        crc = (crc << 1) & 0x7FFF
        if geri:
            crc ^= 0x4599
    return crc

def doldur(bitler):
    cikis, kosu, son = [], 0, None
    for b in bitler:
        cikis.append(b)
        kosu = kosu + 1 if b == son else 1
        son = b
        if kosu == 5:
            cikis.append(1 - b)
            son, kosu = 1 - b, 1
    return cikis

def bits_of(k):
    return [(k >> (10 - i)) & 1 for i in range(11)]

def tahkim(kimlikler):
    akis = [doldur([0] + bits_of(k) + [0]) for k in kimlikler]
    aktif = list(range(len(kimlikler)))
    for idx in range(13):
        gonderen = {d: akis[d][idx] for d in aktif}
        hat = min(gonderen.values())     # 0 baskin
        kaybeden = [d for d in aktif if gonderen[d] == 1 and hat == 0]
        if kaybeden:
            print("bit %2d  hat=%d  kaybeden=%s" % (
                idx, hat, ",".join("0x%03X" % kimlikler[d]
                                   for d in kaybeden)))
        aktif = [d for d in aktif if d not in kaybeden]
        if len(aktif) == 1:
            break
    return kimlikler[aktif[0]]

if __name__ == "__main__":
    bits = [1, 0, 1, 1, 0, 0, 1]
    print("crc15 =", hex(crc15(bits)))
    print("kalan sifir:", crc15(bits + [(crc15(bits) >> (14 - i)) & 1
                                       for i in range(15)]) == 0)
    x = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1]
    print("girdi    ", "".join(map(str, x)))
    print("doldurulm", "".join(map(str, doldur(x))))
    print("kazanan = 0x%03X" % tahkim([0x123, 0x0A5, 0x3F0]))
