# b57_04_kalibrasyon.py
# Olasilik kalitesi: log-kayip, Brier, ECE, guvenilirlik diyagrami
import os
import numpy as np
from sklearn import metrics as M
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
rng = np.random.default_rng(57)


def uret(n):
    X = rng.normal(size=(n, 4))
    w = np.array([1.0, -1.0, 0.6, 0.0])
    p = 1.0 / (1.0 + np.exp(-(X @ w - 0.8)))   # gercek olasilik
    y = (rng.random(n) < p).astype(int)
    return X, y, p


def log_kayip(y, p):
    eps = np.finfo(float).eps
    p = np.clip(p, eps, 1 - eps)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def brier(y, p):
    return np.mean((p - y) ** 2)


def ece(y, p, kutu=10):
    """Beklenen kalibrasyon hatasi (ECE): kutu basina fark."""
    kenar = np.linspace(0, 1, kutu + 1)
    toplam = 0.0
    for a, b in zip(kenar[:-1], kenar[1:]):
        m = (p > a) & (p <= b) if a > 0 else (p >= a) & (p <= b)
        if m.sum() > 0:
            fark = abs(p[m].mean() - y[m].mean())
            toplam += m.sum() / len(p) * fark
    return toplam


def guvenilirlik(y, p, kutu=10):
    """Her kutu icin (ort tahmin, gozlenen oran, sayi)."""
    kenar = np.linspace(0, 1, kutu + 1)
    satirlar = []
    for a, b in zip(kenar[:-1], kenar[1:]):
        m = (p > a) & (p <= b) if a > 0 else (p >= a) & (p <= b)
        if m.sum() > 0:
            satirlar.append((p[m].mean(), y[m].mean(), int(m.sum())))
    return satirlar


# Gercek olasilik bilinir: kalibre model "gercek p" kullanilir.
X_tr, y_tr, _ = uret(3000)
X_te, y_te, p_te = uret(60000)
print("Pozitif orani (test): %.4f" % y_te.mean())

# 1) Kalibre model: dogru lojistik model (ozellikler bilinir)
lr = LogisticRegression(C=1e6, max_iter=5000).fit(X_tr, y_tr)
p_lr = lr.predict_proba(X_te)[:, 1]

# 2) Asiri guvenli model: kucuk veriyle derin gradyan artirma
gb = GradientBoostingClassifier(n_estimators=400, learning_rate=1.0,
                                max_depth=4, random_state=57)
gb.fit(X_tr, y_tr)
p_gb = gb.predict_proba(X_te)[:, 1]

# 3) Platt (sigmoid) ve izotonik kalibrasyon: AYNI gradyan modeli,
#    ayri bir kalibrasyon kumesiyle (X_ka). Model dondurulur.
X_ka, y_ka, _ = uret(3000)
cal_p = CalibratedClassifierCV(FrozenEstimator(gb),
                               method="sigmoid").fit(X_ka, y_ka)
cal_i = CalibratedClassifierCV(FrozenEstimator(gb),
                               method="isotonic").fit(X_ka, y_ka)
p_pl = cal_p.predict_proba(X_te)[:, 1]
p_iz = cal_i.predict_proba(X_te)[:, 1]

modeller = [("gercek-lojistik", p_lr), ("gradyan-artirma", p_gb),
            ("platt", p_pl), ("izotonik", p_iz)]
print("\nModel              log-kayip   Brier    ECE    ROC-AUC")
for ad, p in modeller:
    print("%-18s %8.4f  %7.4f  %6.4f  %7.4f" % (
        ad, log_kayip(y_te, p), brier(y_te, p), ece(y_te, p),
        M.roc_auc_score(y_te, p)))

# sklearn ile birebir karsilastirma
for ad, p in modeller:
    assert abs(log_kayip(y_te, p) - M.log_loss(y_te, p)) < 1e-9
    assert abs(brier(y_te, p) - M.brier_score_loss(y_te, p)) < 1e-12
print("\nLog-kayip ve Brier sklearn ile birebir eslesti.")

# Gercek olasiliklar (oracle): en iyi mumkun kalibrasyon
print("oracle (gercek p) log-kayip: %.4f  Brier: %.4f  ECE: %.4f" % (
    log_kayip(y_te, p_te), brier(y_te, p_te), ece(y_te, p_te)))

# Monoton donusum ROC-AUC'yi degistirmez: Platt icin tam esitlik
print("\nROC-AUC Platt - ham: %.2e" % (
    M.roc_auc_score(y_te, p_pl) - M.roc_auc_score(y_te, p_gb)))
print("ROC-AUC izotonik - ham: %.2e" % (
    M.roc_auc_score(y_te, p_iz) - M.roc_auc_score(y_te, p_gb)))
print("Izotonik ciktida benzersiz olasilik sayisi: %d (ham: %d)" % (
    len(np.unique(p_iz)), len(np.unique(p_gb))))

# Guvenilirlik tablosu: asiri guvenli model
print("\nGuvenilirlik (gradyan artirma): ort tahmin, gozlenen, sayi")
for a, b, c in guvenilirlik(y_te, p_gb):
    print("%.3f   %.3f   %6d" % (a, b, c))

# Sekil verisi
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_kalibrasyon.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("model,ort_tahmin,gozlenen,sayi\n")
    for ad in ["gradyan-artirma", "platt"]:
        p = dict(modeller)[ad]
        for a, b, c in guvenilirlik(y_te, p):
            f.write("%s,%.5f,%.5f,%d\n" % (ad, a, b, c))
print("\nKalibrasyon verisi yazildi:", os.path.basename(yol))
