# mlp_skaler.py: deger.py üzerine kurulu MLP ve tam döngülü eğitim.
# Her parametre tek tek Deger; geri yayılım deger.geri() ile çalışır.
from deger import Deger
from ortak import veri_uret, agirlik_uret


class Noron:
    def __init__(self, w, b, tanh_mi):
        self.w = [Deger(v) for v in w]
        self.b = Deger(b)
        self.tanh_mi = tanh_mi

    def __call__(self, x):
        z = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        return z.tanh() if self.tanh_mi else z


class Katman:
    def __init__(self, W, b, tanh_mi):
        giris = len(W)
        self.noronlar = [Noron([W[i][j] for i in range(giris)],
                               b[j], tanh_mi)
                         for j in range(len(b))]

    def __call__(self, x):
        return [n(x) for n in self.noronlar]


class MLP:
    # katmanlar: [(W, b), ...]. Gizli katmanlar tanh, çıkış doğrusal.
    def __init__(self, katmanlar):
        son = len(katmanlar) - 1
        self.katmanlar = [Katman(W, b, k < son)
                          for k, (W, b) in enumerate(katmanlar)]

    def __call__(self, x):
        for k in self.katmanlar:
            x = k(x)
        return x

    def parametreler(self):
        p = []
        for k in self.katmanlar:
            for n in k.noronlar:
                p.extend(n.w)
                p.append(n.b)
        return p


def kayip(model, X, Y):
    # Ortalama kare hata: (1/N) sum (out - y)^2
    toplam = Deger(0.0)
    for x, y in zip(X, Y):
        out = model(x)[0]
        toplam = toplam + (out - y) ** 2
    return toplam * (1.0 / len(X))


def dogruluk(model, X, Y):
    dogru = sum(1 for x, y in zip(X, Y)
                if (model(x)[0].veri > 0) == (y > 0))
    return dogru / len(X)


def egit(katmanlar, X, Y, donem, ogrenme_orani):
    model = MLP(katmanlar)
    params = model.parametreler()
    gecmis = []
    for _ in range(donem):
        L = kayip(model, X, Y)
        # gradyanlar birikir; her dönem sıfırlanır
        for p in params:
            p.grad = 0.0
        L.geri()
        # gradyan inişi: w <- w - eta * dL/dw
        for p in params:
            p.veri -= ogrenme_orani * p.grad
        gecmis.append(L.veri)
    return model, gecmis


BOYUTLAR = [2, 8, 8, 1]
DONEM = 600
ORANI = 0.1

if __name__ == "__main__":
    X, Y = veri_uret()
    katmanlar = agirlik_uret(BOYUTLAR)
    print("parametre sayisi:", len(MLP(katmanlar).parametreler()))
    model, gecmis = egit(katmanlar, X, Y, DONEM, ORANI)
    for d in [0, 100, 200, 300, 400, 500, 599]:
        print("donem %3d  kayip %.6f" % (d, gecmis[d]))
    print("son kayip %.6f, dogruluk %.3f"
          % (gecmis[-1], dogruluk(model, X, Y)))
    with open("olcum_kayip.csv", "w", encoding="utf-8") as f:
        f.write("donem,kayip\n")
        for d, v in enumerate(gecmis):
            f.write("%d,%.8f\n" % (d, v))
