# b57_05_regresyon.py
# Regresyon metrikleri, MAPE'nin patlamasi, negatif R2, artiklar
import numpy as np
from sklearn import metrics as M

rng = np.random.default_rng(57)


def mae(y, t):
    return np.mean(np.abs(y - t))


def mse(y, t):
    return np.mean((y - t) ** 2)


def rmse(y, t):
    return np.sqrt(mse(y, t))


def mape(y, t):
    """Yuzde ortalama mutlak hata. y = 0 ise tanimsiz."""
    return np.mean(np.abs((y - t) / y)) * 100


def r2(y, t):
    """1 - SS_res/SS_tot. Model ortalamadan kotuyse negatif olur."""
    ss_res = np.sum((y - t) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return 1 - ss_res / ss_tot


# ---------- 1) Dogrusal veri, heteroskedastik gurultu ----------
n = 400
x = rng.uniform(-3, 3, n)
sd = 0.2 + 0.5 * np.abs(x)              # gurultu x ile buyuyor
y = 2.0 * x + 1.0 + rng.normal(scale=sd)
X = np.c_[np.ones(n), x]
beta = np.linalg.lstsq(X, y, rcond=None)[0]   # kapali form kestirim
t = X @ beta
print("Katsayilar (sabit, egim): %.3f %.3f" % (beta[0], beta[1]))

print("MAE  %.4f" % mae(y, t))
print("MSE  %.4f" % mse(y, t))
print("RMSE %.4f" % rmse(y, t))
print("R2   %.4f" % r2(y, t))
for ad, a, b in [("MAE", mae(y, t), M.mean_absolute_error(y, t)),
                 ("MSE", mse(y, t), M.mean_squared_error(y, t)),
                 ("R2", r2(y, t), M.r2_score(y, t))]:
    assert abs(a - b) < 1e-9, ad
print("sklearn ile birebir eslesti (MAE, MSE, R2).")

# ---------- 2) MAPE: hedef sifira yakinken patlar ----------
yy = np.array([100.0, 50.0, 10.0, 1.0, 0.1, 0.01])
tt = yy + np.array([5.0, -5.0, 1.0, 0.5, 0.1, 0.05])  # ayni mutlak
print("\nHata sabit ama hedef kuculunce APE artiyor:")
for a, b in zip(yy, tt):
    print("y=%8.2f  tahmin=%8.2f  |hata|=%.3f  APE=%8.2f%%"
          % (a, b, abs(a - b), abs(a - b) / a * 100))
print("MAPE (ilk iki satir) = %.2f%%"
      % mape(yy[:2], tt[:2]))
print("MAPE (tum 6 satir)   = %.2f%%" % mape(yy, tt))
sk_mape = M.mean_absolute_percentage_error(yy, tt) * 100
assert abs(mape(yy, tt) - sk_mape) < 1e-6

# ---------- 3) Negatif R2: sabit tahmin bile kotu olabilir ----------
y_test = rng.normal(loc=0.0, scale=1.0, size=500)
y_egitim_ort = 3.0     # egitim verisinin ortalamasi 3 olsun (kayma)
sabit = np.full_like(y_test, y_egitim_ort)
print("\nSabit tahmin (egitim ortalamasi = 3), test ortalamasi = 0:")
print("R2 = %.4f" % r2(y_test, sabit))
assert abs(r2(y_test, sabit) - M.r2_score(y_test, sabit)) < 1e-9
print("R2 sabit tahmin icin ort(test) ile yapilsaydi: %.4f"
      % r2(y_test, np.full_like(y_test, y_test.mean())))

# ---------- 4) Artiklar: heteroskedastisite ----------
artik = y - t
print("\ncorr(artik, x)     = %.4f  (OLS artiklari x ile dik)"
      % np.corrcoef(artik, x)[0, 1])
print("corr(|artik|, |x|) = %.4f  (pozitif: varyans x ile artiyor)"
      % np.corrcoef(np.abs(artik), np.abs(x))[0, 1])
for lo, hi in [(-3, -1), (-1, 1), (1, 3)]:
    m = (x >= lo) & (x < hi)
    print("x in [%2d,%2d): artik sd = %.3f  (gercek sd ort = %.3f)"
          % (lo, hi, artik[m].std(), sd[m].mean()))

# ---------- 5) Kantil (pinball) kaybi ve tahmin araligi ----------
def pinball(y, t, q):
    fark = y - t
    return np.mean(np.maximum(q * fark, (q - 1) * fark))


q = 0.9
print("\nq=0.9 pinball (bizim) = %.4f  sklearn = %.4f" % (
    pinball(y, t, q), M.mean_pinball_loss(y, t, alpha=q)))
sk_pin = M.mean_pinball_loss(y, t, alpha=q)
assert abs(pinball(y, t, q) - sk_pin) < 1e-9

# Artik kantillerinden %80'lik aralik (10. ve 90. kantil)
alt, ust = np.quantile(artik, [0.1, 0.9])
yeni_x = rng.uniform(-3, 3, 4000)
yeni_sd = 0.2 + 0.5 * np.abs(yeni_x)
yeni_y = 2.0 * yeni_x + 1.0 + rng.normal(scale=yeni_sd)
yeni_t = beta[0] + beta[1] * yeni_x
kapsama = np.mean((yeni_y >= yeni_t + alt) & (yeni_y <= yeni_t + ust))
print("Her x icin sabit aralik [%.3f, %.3f]:" % (alt, ust))
print("test kapsama orani = %.3f (hedef 0.80)" % kapsama)
print("Heteroskedastik oldugu icin x'e gore kapsama bozulur:")
for lo, hi in [(-3, -1), (-1, 1), (1, 3)]:
    m = (yeni_x >= lo) & (yeni_x < hi)
    k = np.mean((yeni_y[m] >= yeni_t[m] + alt) &
                (yeni_y[m] <= yeni_t[m] + ust))
    print("  x in [%2d,%2d): kapsama = %.3f" % (lo, hi, k))
