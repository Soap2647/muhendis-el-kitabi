# ex4.py: en yakin nokta cifti, bol-fethet izi (Ornek 4)
import math


def mesafe(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def kaba(P):
    en = (math.inf, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = mesafe(P[i], P[j])
            if d < en[0]:
                en = (d, (P[i], P[j]))
    return en


def iz(px, derin=0):
    n = len(px)
    pad = "  " * derin
    if n <= 3:
        d, c = kaba(px)
        print(pad + "taban n=%d d=%.3f" % (n, d))
        return d, c, sorted(px, key=lambda p: p[1])
    mid = n // 2
    xm = px[mid][0]
    dl, cl, yl = iz(px[:mid], derin + 1)
    dr, cr, yr = iz(px[mid:], derin + 1)
    d, c = (dl, cl) if dl <= dr else (dr, cr)
    y = sorted(yl + yr, key=lambda p: p[1])
    serit = [p for p in y if abs(p[0] - xm) < d]
    once = d
    for i, p in enumerate(serit):
        for q in serit[i + 1:]:
            if q[1] - p[1] >= d:
                break
            dd = mesafe(p, q)
            if dd < d:
                d, c = dd, (p, q)
    print(pad + "n=%d xm=%d dL=%.3f dR=%.3f delta=%.3f serit=%d"
          % (n, xm, dl, dr, once, len(serit)))
    return d, c, y


if __name__ == "__main__":
    P = [(1, 7), (4, 2), (6, 9), (8, 4), (9, 1), (12, 8), (13, 3),
         (15, 6)]
    px = sorted(P)
    d, c, _ = iz(px)
    print("en yakin:", c, "mesafe = %.3f" % d)
    assert abs(d - kaba(P)[0]) < 1e-12
