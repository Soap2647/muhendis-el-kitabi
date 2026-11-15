# vektor.py: aynı MLP, NumPy matrisleriyle ve elle türetilmiş
# gradyanlarla yazılır. Skaler motorla karşılaştırılır.
import time

import numpy as np

from mlp_skaler import BOYUTLAR, DONEM, ORANI, MLP, egit, kayip
from ortak import veri_uret, agirlik_uret


def ileri(katmanlar, X):
    # A[k] katman k'nin girdisi; A[k+1] çıktısı. Son katman doğrusal.
    A = [X]
    a = X
    son = len(katmanlar) - 1
    for k, (W, b) in enumerate(katmanlar):
        z = a @ W + b
        a = np.tanh(z) if k < son else z
        A.append(a)
    return A


def kayip_ve_gradyan(katmanlar, X, Y):
    # Geri yayılım: d = dL/dz; dW = girdi^T d, db = sum d.
    N = X.shape[0]
    A = ileri(katmanlar, X)
    out = A[-1]
    L = np.mean((out - Y) ** 2)
    d = 2.0 * (out - Y) / N                  # dL/dout, şekil (N, 1)
    grad = [None] * len(katmanlar)
    for k in reversed(range(len(katmanlar))):
        W, _ = katmanlar[k]
        grad[k] = (A[k].T @ d, d.sum(axis=0))
        if k > 0:
            # dL/d(girdi) = d W^T; tanh'nin türevi 1 - a^2
            d = (d @ W.T) * (1.0 - A[k] ** 2)
    return L, grad


def egit_vektor(katmanlar, X, Y, donem, lr):
    katmanlar = [(W.copy(), b.copy()) for W, b in katmanlar]
    gecmis = []
    for _ in range(donem):
        L, grad = kayip_ve_gradyan(katmanlar, X, Y)
        gecmis.append(float(L))
        katmanlar = [(W - lr * dW, b - lr * db)
                     for (W, b), (dW, db) in zip(katmanlar, grad)]
    return katmanlar, gecmis


def numpy_al(katmanlar):
    return [(np.array(W, dtype=float), np.array(b, dtype=float))
            for W, b in katmanlar]


def skaler_agirlik(model):
    # Skaler değerleri (giris, cikis) biçimli dizilere çevirir.
    sonuc = []
    for k in model.katmanlar:
        giris = len(k.noronlar[0].w)
        W = np.array([[n.w[i].veri for n in k.noronlar]
                      for i in range(giris)])
        b = np.array([n.b.veri for n in k.noronlar])
        sonuc.append((W, b))
    return sonuc


def skaler_gradyan(model):
    sonuc = []
    for k in model.katmanlar:
        giris = len(k.noronlar[0].w)
        dW = np.array([[n.w[i].grad for n in k.noronlar]
                       for i in range(giris)])
        db = np.array([n.b.grad for n in k.noronlar])
        sonuc.append((dW, db))
    return sonuc


def en_buyuk_fark(p, q):
    # Katman listelerindeki (W, b) çiftlerinin en büyük mutlak farkı.
    return max(np.abs(u - v).max()
               for (W1, b1), (W2, b2) in zip(p, q)
               for u, v in [(W1, W2), (b1, b2)])


def olc(f, tekrar=3):
    en_iyi = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        en_iyi = min(en_iyi, time.perf_counter() - t0)
    return en_iyi


if __name__ == "__main__":
    Xl, Yl = veri_uret()
    katman0 = agirlik_uret(BOYUTLAR)
    X = np.array(Xl, dtype=float)
    Y = np.array(Yl, dtype=float).reshape(-1, 1)
    K0 = numpy_al(katman0)

    # 1) Aynı ağırlıklarda gradyan karşılaştırması
    L_vek, g_vek = kayip_ve_gradyan(K0, X, Y)
    model = MLP(katman0)
    L_skl = kayip(model, Xl, Yl)
    for p in model.parametreler():
        p.grad = 0.0
    L_skl.geri()
    g_skl = skaler_gradyan(model)
    en_buyuk = en_buyuk_fark(g_vek, g_skl)
    print("ilk kayip: vektor %.10f, skaler %.10f"
          % (L_vek, L_skl.veri))
    print("gradyan en buyuk fark: %.2e" % en_buyuk)

    # 2) Eğitim: 300 dönem, aynı oran; sonuçları karşılaştır
    K, gecmis = egit_vektor(K0, X, Y, DONEM, ORANI)
    m_skl, gecmis_skl = egit(katman0, Xl, Yl, DONEM, ORANI)
    fark_w = en_buyuk_fark(K, skaler_agirlik(m_skl))
    print("son kayip: vektor %.6f, skaler %.6f" % (gecmis[-1],
                                                 gecmis_skl[-1]))
    print("%d donem sonunda en buyuk agirlik farki: %.2e"
          % (DONEM, fark_w))

    # 3) Hız ölçümü (makineye bağlıdır)
    t_skl = olc(lambda: egit(katman0, Xl, Yl, 1, ORANI), tekrar=3)
    t_vek = olc(lambda: egit_vektor(K0, X, Y, DONEM, ORANI),
                tekrar=3) / DONEM
    print("skaler donem suresi  : %.4f s" % t_skl)
    print("vektor donem suresi  : %.6f s" % t_vek)
    print("hiz orani            : %.0f kat" % (t_skl / t_vek))
    with open("olcum_hiz.csv", "w", encoding="utf-8") as f:
        f.write("yontem,donem_saniye\n")
        f.write("skaler,%.6f\n" % t_skl)
        f.write("vektorel,%.8f\n" % t_vek)

    # 4) Sonuç: doğruluk ve karar sınırı ızgarası
    dog = np.mean(np.sign(ileri(K, X)[-1]).ravel() == Y.ravel())
    print("vektor modelin dogrulugu: %.3f" % dog)
    with open("olcum_karar.csv", "w", encoding="utf-8") as f:
        f.write("x1,x2,cikis\n")
        for x1 in np.linspace(-1.5, 2.5, 60):
            for x2 in np.linspace(-1.0, 1.5, 60):
                c = ileri(K, np.array([[x1, x2]]))[-1][0, 0]
                f.write("%.4f,%.4f,%.6f\n" % (x1, x2, c))
    with open("olcum_veri.csv", "w", encoding="utf-8") as f:
        f.write("x1,x2,y\n")
        for (x1, x2), y in zip(Xl, Yl):
            f.write("%.6f,%.6f,%d\n" % (x1, x2, y))
