# kaybolan.py: sigmoid zincirinde gradyanın derinlikle küçülmesi.
# h_0 = x, h_k = sigma(h_{k-1}). Ters modla dh_n/dx ve kapalı çarpımı
# prod_k h_k (1 - h_k) karşılaştırılır.
from deger import Deger


def sigmoid(z):
    return 1 / (1 + (-z).exp())


def zincir(x0, derinlik):
    x = Deger(x0)
    h = x
    carpim = 1.0
    for _ in range(derinlik):
        h = sigmoid(h)
        carpim *= h.veri * (1 - h.veri)   # sigma'(z) = s (1 - s)
    h.geri()
    return x.grad, carpim


if __name__ == "__main__":
    print("%8s %14s %14s" % ("derinlik", "otomatik", "carpim"))
    satirlar = []
    for n in range(1, 31):
        otomatik, carpim = zincir(0.5, n)
        satirlar.append((n, otomatik, carpim))
        if n in (1, 2, 3, 5, 10, 15, 20, 30):
            print("%8d %14.4e %14.4e" % (n, otomatik, carpim))
    with open("olcum_kaybolan.csv", "w", encoding="utf-8") as f:
        f.write("derinlik,otomatik,carpim\n")
        for n, a, c in satirlar:
            f.write("%d,%.10e,%.10e\n" % (n, a, c))
