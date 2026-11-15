# -*- coding: utf-8 -*-
"""Bölüm 63.10-63.12: load_digits'te MLP eğitimi ve değerlendirme."""
import csv, os
import numpy as np
from sinir import (VERI, ReLU, SoftmaxCE, Ag, Dogrusal, mlp,
                   ileri_geri, sgd_adim, veri_yukle, mini_batch,
                   log_softmax)

(Xt, Yt, yt), (Xv, Yv, yv), (Xs, Ys, ys) = veri_yukle()


def kayip_dogruluk(ag, X, Y, y):
    lp = log_softmax(ag.ileri(X))
    return -np.mean(np.sum(Y * lp, axis=1)), float(np.mean(
        lp.argmax(axis=1) == y))


def yap(kur, seed, lr, epoch=200, lam=0.0, sabir=None):
    """Eğitir; sabir verilirse en iyi doğrulama kaybındaki ağırlıklar
    geri yüklenir."""
    rng = np.random.default_rng(seed)
    ag = kur(rng)
    kayip = SoftmaxCE()
    en = {"vl": np.inf, "w": None, "ep": 0}
    gecmis = []
    for ep in range(1, epoch + 1):
        for idx in mini_batch(len(yt), 32, rng):
            ileri_geri(ag, kayip, Xt[idx], Yt[idx])
            sgd_adim(ag, lr, lam)
        tl, ta = kayip_dogruluk(ag, Xt, Yt, yt)
        vl, va = kayip_dogruluk(ag, Xv, Yv, yv)
        gecmis.append((ep, tl, vl, ta, va))
        if vl < en["vl"]:
            en.update(vl=vl, ep=ep, w=[(k.W.copy(), k.b.copy())
                                       for k in ag.parametreler()])
        if sabir and ep - en["ep"] >= sabir:
            break
    if sabir:
        for k, (W, b) in zip(ag.parametreler(), en["w"]):
            k.W, k.b = W, b
    return ag, gecmis, en["ep"] if sabir else epoch


def lojistik(rng):
    return Ag([Dogrusal(64, 10, rng, "he")])


def mlp_kur(rng):
    return mlp([64, 128, 64, 10], ReLU, rng, "he")


if __name__ == "__main__":
    # 1) Öğrenme oranı: yalnızca doğrulama kaybına göre (tohum 0)
    print("Öğrenme oranı seçimi (doğrulama kaybı, tohum 0):")
    best = {}
    for lr in (0.01, 0.03, 0.1, 0.3):
        _, g, ep = yap(mlp_kur, 0, lr, 200, sabir=20)
        best[lr] = min(r[2] for r in g)
        print("  MLP lr=%.2f  en iyi dogrulama kaybi=%.4f"
              % (lr, best[lr]))
    lr_m = min(best, key=best.get)
    print("  seçilen MLP lr = %.2f" % lr_m)
    # 2) L2 katsayısı: yalnızca doğrulama kaybına göre
    lam_b = {}
    for lam in (0.0, 1e-4, 1e-3, 1e-2):
        _, g, ep = yap(mlp_kur, 0, lr_m, 200, lam=lam, sabir=20)
        lam_b[lam] = min(r[2] for r in g)
        print("  lambda=%.0e  en iyi dogrulama kaybi=%.4f"
              % (lam, lam_b[lam]))
    # Sıfır dışı λ'lar arasından seçim (λ=0 erken durdurma satırı)
    lam_m = min((l for l in lam_b if l > 0), key=lam_b.get)
    print("  L2 satırı için sıfır dışı en iyi lambda = %g" % lam_m)
    # 3) Final: 5 tohum, yalnızca test kümesi raporlanır
    konf = {
        "lojistik (baseline)": (lojistik, lr_m, 300, 0.0, 20),
        "MLP, düzenlileştirme yok (200 epoch)": (mlp_kur, lr_m, 200,
                                                  0.0, None),
        "MLP, erken durdurma": (mlp_kur, lr_m, 200, 0.0, 20),
        "MLP, L2 + erken durdurma": (mlp_kur, lr_m, 200, lam_m, 20),
    }
    print("\nSonuçlar (5 tohum; test kümesi, ortalama +- sapma):")
    print("%-36s %-14s %-14s" % ("model", "egitim acc", "test acc"))
    sonuc = {}
    erk_ep = []
    for ad, (kur, lr, ep, lam, sb) in konf.items():
        tr, te = [], []
        for seed in range(5):
            ag, g, ep_sec = yap(kur, seed, lr, ep, lam, sb)
            if ad == "MLP, erken durdurma":
                erk_ep.append(ep_sec)
            tr.append(kayip_dogruluk(ag, Xt, Yt, yt)[1])
            te.append(kayip_dogruluk(ag, Xs, Ys, ys)[1])
            if ad.startswith("MLP, düzenlileştirme") and seed == 0:
                egri = g
                egri_t = [r[1] for r in g]
                egri_v = [r[2] for r in g]
            if ad == "MLP, L2 + erken durdurma" and seed == 0:
                model = ag
        sonuc[ad] = te
        print("%-36s %.3f+-%.3f  %.3f+-%.3f" % (
            ad, np.mean(tr), np.std(tr), np.mean(te), np.std(te)))
    print("Tohum bazında test doğruluğu (0..4):")
    for ad, te in sonuc.items():
        print("  %-36s" % ad, " ".join("%.3f" % t for t in te))
    en_ep = int(np.argmin(egri_v))
    print("Egri (tohum 0, MLP): en dusuk dogrulama"
          " kaybi epoch=%d deger=%.4f" % (en_ep + 1,
          egri_v[en_ep]))
    print("200. epoch: eğitim kaybı=%.5f, doğrulama kaybı=%.4f"
          % (egri_t[-1], egri_v[-1]))
    print("Erken durdurma seçilen epoch (tohum 0..4):", erk_ep)
    with open(os.path.join(VERI, "b63_egri.csv"), "w", newline="",
              encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["epoch", "egitim_kayip", "dogrulama_kayip",
                     "egitim_dogruluk", "dogrulama_dogruluk"])
        yz.writerows(egri)
    # 4) Karışıklık matrisi (test, L2 modeli, tohum 0)
    tahmin = model.ileri(Xs).argmax(axis=1)
    K = np.zeros((10, 10), int)
    for g_, t_ in zip(ys, tahmin):
        K[g_, t_] += 1
    with open(os.path.join(VERI, "b63_karisiklik.csv"), "w",
              newline="", encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["gercek"] + ["tahmin_%d" % j for j in range(10)])
        for i in range(10):
            yz.writerow([i] + list(K[i]))
    print("\nTest karışıklık matrisi (satır=gerçek):")
    print(K)
    pairs = [(K[i, j], i, j) for i in range(10) for j in range(10)
             if i != j and K[i, j] > 0]
    for c, i, j in sorted(pairs, reverse=True)[:4]:
        print("  gerçek %d -> tahmin %d : %d" % (i, j, c))
    # 5) İlk katman ağırlıkları (16 birim) ve gizli temsilin PCA'sı
    W1 = model.katmanlar[0].W
    with open(os.path.join(VERI, "b63_agirlik.csv"), "w", newline="",
              encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["birim"] + ["p%d" % i for i in range(64)])
        for j in range(16):
            yz.writerow([j] + list(W1[:, j]))
    H = np.maximum(0, Xs @ model.katmanlar[0].W +
                   model.katmanlar[0].b)
    Hc = H - H.mean(axis=0)
    U, S, Vt = np.linalg.svd(Hc, full_matrices=False)
    Z = Hc @ Vt[:2].T
    oran = (S ** 2 / np.sum(S ** 2))[:2]
    print("\nPCA: ilk iki bileşenin oranı =", np.round(oran, 3))
    with open(os.path.join(VERI, "b63_pca.csv"), "w", newline="",
              encoding="utf-8") as f:
        yz = csv.writer(f)
        yz.writerow(["pc1", "pc2", "sinif"])
        for (a, b), c in zip(Z, ys):
            yz.writerow([a, b, c])
    # 6) Modeli kaydet (kuantizasyon ve PyTorch köprüsü için)
    np.savez(os.path.join(VERI, "b63_model.npz"),
             W1=model.katmanlar[0].W, b1=model.katmanlar[0].b,
             W2=model.katmanlar[2].W, b2=model.katmanlar[2].b,
             W3=model.katmanlar[4].W, b3=model.katmanlar[4].b)
