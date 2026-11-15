# b57_01_metrikler.py
# Karisiklik matrisi ve siniflandirma metrikleri: sifirdan + sklearn
import numpy as np
from sklearn import metrics as M
from sklearn.datasets import load_breast_cancer, load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def karisiklik(gercek, tahmin, siniflar):
    """K[i, j]: gercek i, tahmin j olan ornek sayisi."""
    idx = {s: i for i, s in enumerate(siniflar)}
    K = np.zeros((len(siniflar), len(siniflar)), dtype=int)
    for g, t in zip(gercek, tahmin):
        K[idx[g], idx[t]] += 1
    return K


def bol(a, b):
    return float(a) / float(b) if b > 0 else 0.0


def f_beta(p, r, beta=1.0):
    b2 = beta * beta
    return bol((1 + b2) * p * r, b2 * p + r)


def sinif_metrikleri(K):
    """Her sinif icin TP, FP, FN, kesinlik, duyarlilik, F1."""
    tp = np.diag(K).astype(float)
    fp = K.sum(axis=0) - tp          # sutun toplami - TP
    fn = K.sum(axis=1) - tp          # satir toplami - TP
    p = np.array([bol(a, b) for a, b in zip(tp, tp + fp)])
    r = np.array([bol(a, b) for a, b in zip(tp, tp + fn)])
    f1 = np.array([f_beta(a, b) for a, b in zip(p, r)])
    return tp, fp, fn, p, r, f1


def ortalamalar(K):
    """Makro, mikro, agirlikli ortalamalar (P, R, F1)."""
    tp, fp, fn, p, r, f1 = sinif_metrikleri(K)
    destek = K.sum(axis=1)
    w = destek / destek.sum()
    mp = bol(tp.sum(), tp.sum() + fp.sum())   # mikro kesinlik
    mr = bol(tp.sum(), tp.sum() + fn.sum())   # mikro duyarlilik
    return {
        "makro_F1": f1.mean(),
        "mikro_F1": f_beta(mp, mr),
        "agirlikli_F1": (w * f1).sum(),
        "makro_kesinlik": p.mean(),
        "mikro_kesinlik": mp,
        "agirlikli_kesinlik": (w * p).sum(),
    }


def kappa(K):
    """Cohen kappa: gozlenen uyum, sansa bagli uyumla duzeltilmis."""
    n = K.sum()
    po = np.trace(K) / n
    pe = (K.sum(axis=0) * K.sum(axis=1)).sum() / float(n) ** 2
    return (po - pe) / (1 - pe)


def mcc_ikili(tp, tn, fp, fn):
    """Matthews korelasyon katsayisi: -1..+1, 0 = rastgele."""
    pay = float(tp) * tn - float(fp) * fn
    payda = np.sqrt(float(tp + fp) * (tp + fn)
                    * (tn + fp) * (tn + fn))
    return pay / payda if payda > 0 else 0.0


# ---------- 1) Ikili siniflandirma: meme kanseri verisi ----------
veri = load_breast_cancer()
# sklearn'de hedef 0 = kotu huylu (malignant). Pozitif sinifi
# "kotu huylu" yapiyoruz: tespit etmek istedigimiz sey bu.
y = (veri.target == 0).astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(
    veri.data, y, test_size=0.3, stratify=y, random_state=57)
model = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=1000))
model.fit(X_tr, y_tr)
skor = model.predict_proba(X_te)[:, 1]
tahmin = (skor >= 0.5).astype(int)

K = karisiklik(y_te, tahmin, [0, 1])
tp, fp, fn, tn = K[1, 1], K[0, 1], K[1, 0], K[0, 0]
print("Karisiklik matrisi (satir=gercek, sutun=tahmin)")
print("           tahmin:0  tahmin:1")
print("gercek:0 %9d %9d" % (K[0, 0], K[0, 1]))
print("gercek:1 %9d %9d" % (K[1, 0], K[1, 1]))
print("TP=%d FP=%d FN=%d TN=%d" % (tp, fp, fn, tn))

acc = (tp + tn) / K.sum()
pre = bol(tp, tp + fp)
rec = bol(tp, tp + fn)
spe = bol(tn, tn + fp)
f1 = f_beta(pre, rec, 1.0)
f2 = f_beta(pre, rec, 2.0)
f05 = f_beta(pre, rec, 0.5)
mcc = mcc_ikili(tp, tn, fp, fn)
kap = kappa(K)

print("\nScratch metrikler (ikili):")
print("dogruluk   %.4f" % acc)
print("kesinlik   %.4f" % pre)
print("duyarlilik %.4f" % rec)
print("ozgulluk   %.4f" % spe)
print("F1         %.4f  F2 %.4f  F0.5 %.4f" % (f1, f2, f05))
print("MCC        %.4f" % mcc)
print("kappa      %.4f" % kap)

# sklearn ile birebir karsilastirma
esit = [
    ("dogruluk", acc, M.accuracy_score(y_te, tahmin)),
    ("kesinlik", pre, M.precision_score(y_te, tahmin)),
    ("duyarlilik", rec, M.recall_score(y_te, tahmin)),
    ("ozgulluk", spe, M.recall_score(y_te, tahmin, pos_label=0)),
    ("F1", f1, M.f1_score(y_te, tahmin)),
    ("F2", f2, M.fbeta_score(y_te, tahmin, beta=2)),
    ("F0.5", f05, M.fbeta_score(y_te, tahmin, beta=0.5)),
    ("MCC", mcc, M.matthews_corrcoef(y_te, tahmin)),
    ("kappa", kap, M.cohen_kappa_score(y_te, tahmin)),
]
print("\nsklearn ile karsilastirma:")
en_buyuk = 0.0
for ad, bizim, sk in esit:
    en_buyuk = max(en_buyuk, abs(bizim - sk))
    print("%-11s bizim %.6f  sklearn %.6f" % (ad, bizim, sk))
print("en buyuk fark: %.2e" % en_buyuk)
assert en_buyuk < 1e-9
assert np.array_equal(K, M.confusion_matrix(y_te, tahmin))

# Dengesizlik: her zaman "iyi huylu" diyen tahminci
sabit = np.zeros_like(y_te)
print("\nHer zaman 'iyi huylu' diyen tahminci:")
print("dogruluk = %.4f  MCC = %.4f  kappa = %.4f" % (
    M.accuracy_score(y_te, sabit),
    M.matthews_corrcoef(y_te, sabit),
    M.cohen_kappa_score(y_te, sabit)))

# ---------- 2) Cok sinifli: el yazisi rakamlari (10 sinif) ----------
d = load_digits()
Xd_tr, Xd_te, yd_tr, yd_te = train_test_split(
    d.data, d.target, test_size=0.3, stratify=d.target,
    random_state=57)
md = make_pipeline(StandardScaler(),
                    LogisticRegression(max_iter=2000))
md.fit(Xd_tr, yd_tr)
td = md.predict(Xd_te)
Kd = karisiklik(yd_te, td, list(range(10)))
o = ortalamalar(Kd)
print("\nCok sinifli (10 rakam): makro/mikro/agirlikli")
for ad in ["makro_kesinlik", "mikro_kesinlik", "agirlikli_kesinlik",
           "makro_F1", "mikro_F1", "agirlikli_F1"]:
    print("%-20s %.4f" % (ad, o[ad]))
print("dogruluk             %.4f" % M.accuracy_score(yd_te, td))
print("kappa                %.4f" % kappa(Kd))
print("MCC (cok sinif)      %.4f" % M.matthews_corrcoef(yd_te, td))

# sklearn ile eslesme (average parametresi)
sk_makro = M.f1_score(yd_te, td, average="macro")
sk_mikro = M.f1_score(yd_te, td, average="micro")
sk_agir = M.f1_score(yd_te, td, average="weighted")
assert abs(o["makro_F1"] - sk_makro) < 1e-9
assert abs(o["mikro_F1"] - sk_mikro) < 1e-9
assert abs(o["agirlikli_F1"] - sk_agir) < 1e-9
assert abs(o["mikro_F1"] - M.accuracy_score(yd_te, td)) < 1e-12
print("\nsklearn makro/mikro/agirlikli F1 ile birebir eslesti.")
print("Mikro F1 = dogruluk (tek etiketli cok sinifta).")

# Dilim: her sinifin F1'i, en zayif olanlar
_, _, _, _, _, f1s = sinif_metrikleri(Kd)
sira = np.argsort(f1s)[:3]
print("En zayif 3 sinif (F1):", [(int(i), round(float(f1s[i]), 3))
                                  for i in sira])

# Sekil verisi: karisiklik matrisi (ikili, meme kanseri test kumesi)
import os as _os
_veri = r"D:\Mevcut Projeler\Kitap\engine\veri"
_os.makedirs(_veri, exist_ok=True)
with open(_os.path.join(_veri, "b57_karisiklik.csv"), "w",
          encoding="utf-8") as _f:
    _f.write("gercek,tahmin,sayi\n")
    for _i in range(2):
        for _j in range(2):
            _f.write("%d,%d,%d\n" % (_i, _j, K[_i, _j]))

# Dengesiz cok sinifli oyuncak: makro ve mikro farki
K3 = np.array([[90, 5, 0], [3, 2, 0], [0, 1, 4]])
o3 = ortalamalar(K3)
print("\nOyuncak 3 sinif (satir=gercek):")
for ad in ["makro_F1", "mikro_F1", "agirlikli_F1"]:
    print("%-14s %.4f" % (ad, o3[ad]))
y3 = np.concatenate([np.full(K3[i].sum(), i) for i in range(3)])
t3 = np.concatenate(
    [np.repeat(np.arange(3), K3[i]) for i in range(3)])
sk = M.f1_score(y3, t3, average="macro")
assert abs(o3["makro_F1"] - sk) < 1e-9
sk = M.f1_score(y3, t3, average="micro")
assert abs(o3["mikro_F1"] - sk) < 1e-9
assert abs(o3["agirlikli_F1"]
           - M.f1_score(y3, t3, average="weighted")) < 1e-9
acc3 = M.accuracy_score(y3, t3)
print("Dogruluk = %.4f (mikro F1 ile ayni)" % acc3)
