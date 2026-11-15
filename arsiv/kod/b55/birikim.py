# birikim.py: gradyan birikimi. f = a*b + a, a = 2, b = 3.
# a iki yolda kullanılır; doğru sonuç katkıların toplamıdır.
import deger
from deger import Deger, topo


def calistir(birik):
    deger.BIRIKIR = birik
    a = Deger(2.0)
    b = Deger(3.0)
    m = a * b          # yol 1: a'dan m'ye
    f = m + a          # yol 2: a'dan doğrudan f'ye
    f.geri()
    print("BIRIKIR = %s" % birik)
    print("%-6s %8s %8s" % ("dugum", "veri", "grad"))
    for v in topo(f)[::-1]:
        ad = v._islem if v._islem else "girdi"
        print("%-6s %8.2f %8.2f" % (ad, v.veri, v.grad))
    print("")
    return a.grad, b.grad


if __name__ == "__main__":
    print("beklenen: df/da = b + 1 = 4, df/db = a = 2")
    print("")
    da, db = calistir(True)
    print("dogru   : a.grad = %.1f, b.grad = %.1f" % (da, db))
    da, db = calistir(False)
    print("hatali  : a.grad = %.1f, b.grad = %.1f" % (da, db))
    deger.BIRIKIR = True
