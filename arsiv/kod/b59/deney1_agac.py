# deney1_agac.py -- sifir CART dogrulama, hiz, derinlik, budama, kararsizlik
import time, csv, os
import numpy as np
from agac import KararAgaci, en_iyi_bolme_siniflama
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.datasets import make_moons

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"

def naif_en_iyi(x, y, k):
    # O(n^2): her aday esik icin tum ornekleri yeniden say
    u = np.unique(x)
    best = (-np.inf, None)
    def gini(c):
        n = c.sum()
        return 1.0 - np.sum((c / n) ** 2) if n else 0.0
    ust = gini(np.bincount(y, minlength=k).astype(float))
    n = len(y)
    for i in range(len(u) - 1):
        t = (u[i] + u[i + 1]) / 2
        sol = x <= t
        cl = np.bincount(y[sol], minlength=k).astype(float)
        cr = np.bincount(y[~sol], minlength=k).astype(float)
        g = ust - (cl.sum() * gini(cl) + cr.sum() * gini(cr)) / n
        if g > best[0]:
            best = (g, t)
    return best

print("== 1. Hizli bolme == naif bolme (rastgele 2000 deneme)")
rng = np.random.default_rng(59)
esles = 0
for _ in range(2000):
    n = rng.integers(2, 40)
    x = rng.integers(0, 8, n).astype(float)   # bilerek cok bag
    y = rng.integers(0, 3, n)
    a = en_iyi_bolme_siniflama(x, y, 3, "gini", 1)
    b = naif_en_iyi(x, y, 3)
    if a is None and b[1] is None:
        esles += 1
    elif a is not None and b[1] is not None and \
            abs(a[0] - b[0]) < 1e-12 and abs(a[1] - b[1]) < 1e-12:
        esles += 1
print("eslesen deneme: %d / 2000" % esles)

print("\n== 2. Hiz: tek ozellik, n buyudukce (sabit tohum)")
for n in [500, 1000, 2000, 4000]:
    x = rng.normal(size=n)
    y = (x + rng.normal(0, 0.5, n) > 0).astype(int)
    t = time.perf_counter(); en_iyi_bolme_siniflama(x, y, 2, "gini", 1)
    tf = time.perf_counter() - t
    t = time.perf_counter(); naif_en_iyi(x, y, 2)
    tn = time.perf_counter() - t
    print("n=%5d  hizli %.5f s  naif %.4f s  oran %.0fx" % (n, tf, tn, tn / tf))

print("\n== 3. Benim agacim vs sklearn (breast cancer, test=%30)")
X, y = load_breast_cancer(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                      random_state=59, stratify=y)
for d in [2, 3, 4, 5, None]:
    m = KararAgaci(max_derinlik=d).fit(Xtr, ytr)
    s = DecisionTreeClassifier(max_depth=d, random_state=0).fit(Xtr, ytr)
    pm, ps = m.tahmin(Xte), s.predict(Xte)
    print("derinlik=%-4s benim test=%.4f sk test=%.4f  yaprak %d/%d  "
          "ayni tahmin %d/%d" % (d, (pm == yte).mean(), s.score(Xte, yte),
          m.yaprak_sayisi(), s.get_n_leaves(), np.sum(pm == ps), len(ps)))

print("\n== 4. Derinlik egrisi: egitim ve test hatasi (5 tohum)")
rows = []
for d in range(1, 11):
    etr, ete = [], []
    for sd in range(5):
        a, b, c, e = train_test_split(X, y, test_size=0.3,
                                      random_state=sd, stratify=y)
        m = KararAgaci(max_derinlik=d).fit(a, c)
        etr.append(np.mean(m.tahmin(a) != c))
        ete.append(np.mean(m.tahmin(b) != e))
    rows.append((d, np.mean(etr), np.std(etr), np.mean(ete), np.std(ete)))
    print("d=%2d  egitim hatasi %.4f +- %.4f   test hatasi %.4f +- %.4f"
          % rows[-1])
with open(os.path.join(VERI, "b59_derinlik.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["derinlik", "egitim_ort", "egitim_ss", "test_ort",
                "test_ss"])
    w.writerows(rows)

print("\n== 5. Budama: cost-complexity yolu (sklearn ccp_alpha)")
sk = DecisionTreeClassifier(random_state=0)
path = sk.cost_complexity_pruning_path(Xtr, ytr)
rows = []
for a in path.ccp_alphas[:-1]:
    t = DecisionTreeClassifier(ccp_alpha=a, random_state=0).fit(Xtr, ytr)
    rows.append((a, t.get_n_leaves(), t.score(Xtr, ytr), t.score(Xte, yte)))
for r in rows[::max(1, len(rows) // 8)]:
    print("alpha=%.5f yaprak=%3d egitim=%.4f test=%.4f" % r)
best = max(rows, key=lambda r: r[3])
print("en iyi test: alpha=%.5f yaprak=%d test=%.4f" % (best[0],
      best[1], best[3]))
with open(os.path.join(VERI, "b59_budama.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["alpha", "yaprak", "egitim_dogruluk", "test_dogruluk"])
    w.writerows(rows)

print("\n== 6. Kararsizlik: 50 alt ornekte kok bolunmesi")
Xm, ym = make_moons(n_samples=400, noise=0.3, random_state=59)
Xa, Xb, ya, yb = train_test_split(Xm, ym, test_size=0.3, random_state=59)
kok_ozellik, kok_esik = [], []
for sd in range(50):
    r = np.random.default_rng(sd)
    idx = r.choice(len(Xa), size=int(0.5 * len(Xa)), replace=False)
    t = DecisionTreeClassifier(max_depth=3, random_state=0)
    t.fit(Xa[idx], ya[idx])
    kok_ozellik.append((int(t.tree_.feature[0]),
                        round(float(t.tree_.threshold[0]), 2)))
vals, cnt = np.unique(np.array(kok_ozellik), axis=0, return_counts=True)
for v, c in sorted(zip(map(tuple, vals), cnt), key=lambda z: -z[1])[:6]:
    print("kok bolme ozellik=%d esik=%.2f : %d / 50" % (v[0], v[1], c))
print("farkli kok bolme sayisi:", len(vals))
