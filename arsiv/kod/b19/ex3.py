# ex3.py: 1234 x 5678 Karatsuba izi (Ornek 3)
def kar_adim(x, y, ust=True):
    if x < 100 and y < 100:
        return x * y
    m = 100                              # 10^2 ile bol
    a1, a0 = divmod(x, m)
    b1, b0 = divmod(y, m)
    z0 = kar_adim(a0, b0, False)
    z2 = kar_adim(a1, b1, False)
    z1 = kar_adim(a0 + a1, b0 + b1, False) - z0 - z2
    if ust:
        print("a1=%d a0=%d b1=%d b0=%d" % (a1, a0, b1, b0))
        print("z0=%d z1=%d z2=%d" % (z0, z1, z2))
    return z2 * m * m + z1 * m + z0


if __name__ == "__main__":
    s = kar_adim(1234, 5678)
    print("1234 * 5678 =", s, "| dogrudan =", 1234 * 5678)
    assert s == 1234 * 5678
