# ornek_i2c.py: I2C cekme direnci sinirlari ve RC yukselme suresi.
import math

def rmax(tr_max, cb):
    return tr_max / (0.8473 * cb)

def rmin(vdd, vol, iol):
    return (vdd - vol) / iol

def yukselme(r, c, vdd=3.3):
    """Sayisal: V(t)=VDD(1-e^(-t/RC)); %30 ile %70 arasi sure."""
    tau, dt = r * c, r * c / 20000.0
    t, t30, t70 = 0.0, None, None
    while t70 is None:
        v = vdd * (1 - math.exp(-t / tau))
        if t30 is None and v >= 0.3 * vdd:
            t30 = t
        if v >= 0.7 * vdd:
            t70 = t
        t += dt
    return t70 - t30

if __name__ == "__main__":
    print("Rmin = %.0f ohm" % rmin(3.3, 0.4, 3e-3))
    print("Rmax (hizli, 300 ns, 400 pF) = %.0f ohm" %
          rmax(300e-9, 400e-12))
    print("Rmax (standart, 1000 ns, 400 pF) = %.0f ohm" %
          rmax(1000e-9, 400e-12))
    tr = yukselme(4700, 100e-12)
    print("R=4,7k C=100 pF: tr = %.1f ns" % (tr * 1e9))
    rc = 0.8473 * 4700 * 1e-10 * 1e9
    print("0,8473 RC        = %.1f ns" % rc)
