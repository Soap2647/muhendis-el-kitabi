# b57_06_cv_derinlik.py
# Cross-validation derinligi: k, tekrarli CV, ic ice CV, zaman serisi
import os
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (GridSearchCV, KFold, LeaveOneOut,
                                     RepeatedStratifiedKFold,
                                     StratifiedKFold, TimeSeriesSplit,
                                     cross_val_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

# ---------- 1) k secimi: yanlilik ve tahmin degiskenligi ----------
veri = load_breast_cancer()
X, y = veri.data, veri.target
model = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=2000))

print("k    ort skor   std (30 bolme tohumu)")
for k in [2, 5, 10, 20]:
    skorlar = []
    for sd in range(30):
        cv = StratifiedKFold(k, shuffle=True, random_state=sd)
        skorlar.append(cross_val_score(model, X, y, cv=cv).mean())
    skorlar = np.array(skorlar)
    print("%2d   %.4f     %.4f" % (k, skorlar.mean(), skorlar.std()))

# LOO: bolme rastgeleligi yok; tek bir deterministik sonuc
loo = cross_val_score(model, X, y, cv=LeaveOneOut()).mean()
print("LOO  %.4f     (deterministik, tek sonuc)" % loo)

# ---------- 2) Tekrarli CV: bolme sansini azaltmak ----------
tekrar = RepeatedStratifiedKFold(n_splits=5, n_repeats=10,
                                 random_state=57)
skor_t = cross_val_score(model, X, y, cv=tekrar)
print("\n5-kat x 10 tekrar: %d skor, ort %.4f, std %.4f"
      % (len(skor_t), skor_t.mean(), skor_t.std()))
print("10 tekrarin kendi ortalamalarinin std = %.4f"
      % (skor_t.reshape(10, 5).mean(axis=1).std()))
print("Not: tekrarlar ayni veriyi kullanir; bagimsiz ornek degildir.")

# ---------- 3) Ic ice CV: iyimserlik olcumu ----------
# Gurultu verisi: gercek sinyal yok. Dogru tahmin: ~%50.
Cgrid = {"logisticregression__C": 10.0 ** np.arange(-3, 4)}
iyimser, dogru = [], []
for sd in range(20):
    rng = np.random.default_rng(sd)
    Xg = rng.normal(size=(100, 200))
    yg = np.repeat([0, 1], 50)
    rng.shuffle(yg)
    p = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=2000))
    dis = StratifiedKFold(5, shuffle=True, random_state=sd)
    ara = StratifiedKFold(5, shuffle=True, random_state=100 + sd)
    # Iç içe DEGIL: ayni katlarla hem C secimi hem skor
    gs = GridSearchCV(p, Cgrid, cv=dis).fit(Xg, yg)
    iyimser.append(gs.best_score_)
    # Ic ice: dis katlar hic gorulmemis test, C ic katlarda secilir
    gs2 = GridSearchCV(p, Cgrid, cv=ara)
    dogru.append(cross_val_score(gs2, Xg, yg, cv=dis).mean())
iyimser, dogru = np.array(iyimser), np.array(dogru)
print("\nGurultu verisi, 20 tohum, 13 C degeri:")
print("ic ice OLMAYAN (best_score_) ort = %.4f" % iyimser.mean())
print("ic ice (dogru)               ort = %.4f" % dogru.mean())
print("iyimserlik (fark)            ort = %.4f"
      % (iyimser - dogru).mean())
print("ilk 5 tohum (olmayan / ic ice):")
for sd in range(5):
    print("  %d   %.3f   %.3f" % (sd, iyimser[sd], dogru[sd]))

# ---------- 4) Zaman serisi CV: gelecek gecmisi goremez ----------
t = np.arange(20)
zs = TimeSeriesSplit(n_splits=4)
print("\nTimeSeriesSplit(4) on 20 zaman adimi:")
for tr, te in zs.split(t):
    assert tr.max() < te.min()     # egitim her zaman testten once
    print("egitim %2d..%2d   test %2d..%2d" % (
        tr.min(), tr.max(), te.min(), te.max()))
print("Egitim her zaman testten once: assert gecti.")
# Karistirilmis KFold ise gelecek verisi egitime girer:
kf = KFold(4, shuffle=True, random_state=0)
gelecek_sizinti = [bool(np.any(tr > te.max()))
                   for tr, te in kf.split(t)]
print("Karistirilmis KFold'da gelecek egitime girer mi?",
      gelecek_sizinti)

# Sekil verisi: ic ice / olmayan iyimserlik
os.makedirs(VERI, exist_ok=True)
yol = os.path.join(VERI, "b57_ic_ice_cv.csv")
with open(yol, "w", encoding="utf-8") as f:
    f.write("tohum,ic_ice_olmayan,ic_ice\n")
    for sd in range(20):
        f.write("%d,%.5f,%.5f\n" % (sd, iyimser[sd], dogru[sd]))
print("\nIc ice CV verisi yazildi:", os.path.basename(yol))
