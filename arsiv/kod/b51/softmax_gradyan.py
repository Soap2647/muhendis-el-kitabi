# softmax_gradyan.py: softmax + çapraz entropi kaybı, sayısal
# kararlılık (log-sum-exp) ve gradyanın sayısal denetimi.
# Birim: nat (ln).
import math
import random

def softmax_naif(z):
    e = [math.exp(v) for v in z]          # büyük z'de taşar
    s = sum(e)
    return [v / s for v in e]

def lse(z):
    # log-sum-exp: ln sum exp(z_i), en büyük değer çıkarılarak
    m = max(z)
    return m + math.log(sum(math.exp(v - m) for v in z))

def softmax(z):
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]

def kayip(z, y):
    # Tek örnek, tek sıcak etiket y (sınıf indeksi):
    # L = -ln p_y = lse(z) - z_y
    return lse(z) - z[y]

def gradyan(z, y):
    # dL/dz_i = p_i - [i == y]  (softmax + çapraz entropinin sadeliği)
    p = softmax(z)
    return [p[i] - (1.0 if i == y else 0.0) for i in range(len(z))]

def gradyan_sayisal(z, y, h=1e-5):
    # Merkezi fark: (L(z+h e_i) - L(z-h e_i)) / 2h
    g = []
    for i in range(len(z)):
        zp = list(z); zm = list(z)
        zp[i] += h; zm[i] -= h
        g.append((kayip(zp, y) - kayip(zm, y)) / (2 * h))
    return g

def main():
    # 1) Taşma: büyük logitler
    z_buyuk = [1000.0, 999.0, 998.0]
    try:
        softmax_naif(z_buyuk)
        print("naif softmax: taşma yok")
    except OverflowError as e:
        print("naif softmax hata verdi:", e)
    print("kararlı softmax:", [round(v, 6) for v in softmax(z_buyuk)])
    print("kararlı kayıp (y=0): %.6f" % kayip(z_buyuk, 0))
    # 2) Düşük olasılık: ln 0 hatası; kararlı log-softmax çalışır
    z_fark = [0.0, -800.0]
    e = [math.exp(v) for v in z_fark]
    p_naif = [v / sum(e) for v in e]
    print("naif p:", p_naif)
    try:
        print("naif ln p_1 =", math.log(p_naif[1]))
    except ValueError as err:
        print("naif ln p_1 hata:", err)
    print("kararlı ln p_1 = %.1f" % (z_fark[1] - lse(z_fark)))
    # 3) Çalışılmış örnek: 3 sınıf, y = 0
    z = [2.0, 0.5, -1.0]
    p = softmax(z)
    print("logit:", z, " p:", [round(v, 4) for v in p])
    print("kayip = %.4f nat" % kayip(z, 0))
    print("gradyan (p - y):", [round(v, 4) for v in gradyan(z, 0)])
    # 4) Gradyan denetimi (sabit tohum): 500 rastgele z, 3 sınıf
    rnd = random.Random(51)
    en_buyuk = 0.0
    for _ in range(500):
        zz = [rnd.uniform(-3, 3) for _ in range(3)]
        y = rnd.randrange(3)
        a = gradyan(zz, y)
        s = gradyan_sayisal(zz, y)
        fark = max(abs(u - v) for u, v in zip(a, s))
        en_buyuk = max(en_buyuk, fark)
    print("500 rastgele z icin max |analitik - sayisal| = %.2e"
          % en_buyuk)
    # 5) Etiket yumuşatma: hedef dağılımı yumuşat
    eps, k = 0.1, 3
    yum = [(1 - eps) * (i == 0) + eps / k for i in range(k)]
    print("yumusatilmis hedef:", [round(v, 4) for v in yum])


if __name__ == "__main__":
    main()
