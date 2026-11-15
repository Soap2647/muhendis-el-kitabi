# -*- coding: utf-8 -*-
# Bolum 60 - olcum deneyleri (b60_sifirdan.py ile ayni klasorde).
# CSV'ler ./veri/ altina yazilir; tohumlar sabittir.
import os
import time
import numpy as np
from sklearn.svm import SVC, LinearSVC
from sklearn.datasets import (load_breast_cancer, make_moons,
                              make_circles, make_blobs,
                              make_classification, load_digits)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.kernel_approximation import RBFSampler
from sklearn.kernel_ridge import KernelRidge
from b60_sifirdan import (pegasos_dogrusal, smo_basit, rff_olustur,
                          rff_donustur, krr_fit, krr_tahmin)

os.makedirs("veri", exist_ok=True)


def csv_yaz(ad, bas, satirlar):
    with open(os.path.join("veri", ad), "w", encoding="utf-8") as f:
        f.write(",".join(bas) + "\n")
        for r in satirlar:
            f.write(",".join(str(x) for x in r) + "\n")


Xb, yb = load_breast_cancer(return_X_y=True)
yb = 2 * yb - 1.0

# ---- 1. Dort nokta: en buyuk marj ----
X4 = np.array([[2., 1.], [2., 3.], [0., 1.], [-1., 0.]])
y4 = np.array([1, 1, -1, -1.])
s4 = SVC(kernel="linear", C=1e6).fit(X4, y4)
w4 = s4.coef_[0]
b4 = round(float(s4.intercept_[0]), 4)
print("[1] w=", np.round(w4, 4), "b=", b4)
print("[1] SV=", s4.support_, "marj=",
      round(2 / np.linalg.norm(w4), 4))
print("[1] alpha*y=", np.round(s4.dual_coef_[0], 4))

# ---- 2. Ayrilabilir blob: marj ve destek vektorleri ----
Xbl, ybl = make_blobs(n_samples=20, centers=[[0, 0], [3, 3]],
                      cluster_std=0.6, random_state=1)
ybl = 2 * ybl - 1.0
sm = SVC(kernel="linear", C=1000).fit(Xbl, ybl)
svmask = np.zeros(len(ybl), int)
svmask[sm.support_] = 1
wm = sm.coef_[0]
b5 = round(float(sm.intercept_[0]), 4)
print("[2] w=", np.round(wm, 4), "b=", b5)
print("[2] marj=", round(2 / np.linalg.norm(wm), 4),
      "SV=", svmask.sum())
csv_yaz("b60_marj_veri.csv", ["x1", "x2", "y", "sv"],
        [[round(Xbl[i, 0], 4), round(Xbl[i, 1], 4), int(ybl[i]),
          svmask[i]] for i in range(len(ybl))])
csv_yaz("b60_marj_hat.csv", ["w1", "w2", "b", "marj"],
        [[wm[0], wm[1], sm.intercept_[0], 2 / np.linalg.norm(wm)]])

# ---- 3. C taramasi (gurultulu dogrusal veri, 5 tohum) ----
print("[3] C taramasi")
tab, hatlar = [], []
for Cv in [0.01, 0.1, 1, 10, 100]:
    nsv, marj, tr, te = [], [], [], []
    for sd in range(5):
        X, y = make_classification(
            n_samples=200, n_features=2, n_redundant=0,
            n_informative=2,
            n_clusters_per_class=1, flip_y=0.1, class_sep=1.0,
            random_state=sd)
        y = 2 * y - 1.0
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=sd)
        m = SVC(kernel="linear", C=Cv).fit(Xtr, ytr)
        nsv.append(m.n_support_.sum())
        marj.append(2 / np.linalg.norm(m.coef_[0]))
        tr.append(np.mean(m.predict(Xtr) == ytr))
        te.append(np.mean(m.predict(Xte) == yte))
        if sd == 0:
            hatlar.append([Cv, m.coef_[0][0], m.coef_[0][1],
                           m.intercept_[0]])
            csv_yaz("b60_c_veri.csv", ["x1", "x2", "y"],
                    [[a, b, 2 * int(c) - 1]
                     for (a, b), c in zip(X, y)])
    print("  C=%g SV=%.1f marj=%.3f egitim=%.3f test=%.3f+-%.3f"
          % (Cv, np.mean(nsv), np.mean(marj), np.mean(tr),
             np.mean(te), np.std(te)))
    tab.append([Cv, np.mean(nsv), np.mean(marj), np.mean(tr),
                np.mean(te), np.std(te)])
csv_yaz("b60_c_tarama.csv",
        ["C", "sv", "marj", "egitim", "test", "test_sd"], tab)
csv_yaz("b60_c_hat.csv", ["C", "w1", "w2", "b"], hatlar)

# ---- 4. Pegasos yakinsamasi (5 tohum) ----
C = 1.0
print("[4] Pegasos (meme kanseri, olcekli, C=1, 5 tohum)")
for ep in [50, 200, 1000, 3000]:
    gap, acc, sure = [], [], []
    for sd in range(5):
        Xtr, Xte, ytr, yte = train_test_split(
            Xb, yb, test_size=0.3, stratify=yb, random_state=sd)
        sc = StandardScaler().fit(Xtr)
        Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)

        def obj(w, b):
            return (0.5 * w @ w
                    + C * np.maximum(0,
                                     1 - ytr * (Xtr @ w + b)).sum())

        ref = SVC(kernel="linear", C=C, tol=1e-8).fit(Xtr, ytr)
        oref = obj(ref.coef_[0], ref.intercept_[0])
        t0 = time.time()
        w, b = pegasos_dogrusal(Xtr, ytr, C, epoch=ep, seed=sd)
        sure.append(time.time() - t0)
        gap.append(100 * (obj(w, b) - oref) / oref)
        acc.append(np.mean(np.sign(Xte @ w + b) == yte))
    print("  epoch=%d bosluk%%=%.3f+-%.3f test=%.4f+-%.4f sure=%.2fs"
          % (ep, np.mean(gap), np.std(gap), np.mean(acc),
             np.std(acc), np.mean(sure)))

# ---- 5. Basit SMO ve sklearn (moons, gamma=1, C=1) ----
print("[5] SMO vs SVC(rbf)")
for sd in range(5):
    Xm, ym = make_moons(n_samples=200, noise=0.25, random_state=sd)
    ym = 2 * ym - 1.0
    K = rbf_kernel(Xm, gamma=1.0)
    al, bb = smo_basit(K, ym, 1.0, seed=sd)
    ref = SVC(kernel="rbf", gamma=1.0, C=1.0, tol=1e-6).fit(Xm, ym)
    a_sk = np.zeros(len(ym))
    a_sk[ref.support_] = np.abs(ref.dual_coef_[0])

    def dual(a):
        return 0.5 * (a * ym) @ K @ (a * ym) - a.sum()

    f_my = K @ (al * ym) + bb
    f_sk = ref.decision_function(Xm)
    isaret = np.mean(np.sign(f_my) == np.sign(f_sk))
    print("  t%d dual SMO=%.4f sk=%.4f SV=%d/%d isaret=%.3f"
          % (sd, dual(al), dual(a_sk), np.sum(al > 1e-8),
             len(ref.support_), isaret))

# ---- 6. Daire: 2B -> 3B ----
Xc, yc = make_circles(n_samples=300, factor=0.5, noise=0.05,
                      random_state=0)
yc = 2 * yc - 1.0
zc = Xc[:, 0] ** 2 + Xc[:, 1] ** 2
csv_yaz("b60_daire.csv", ["x1", "x2", "z", "y"],
        [[Xc[i, 0], Xc[i, 1], zc[i], int(yc[i])]
         for i in range(len(yc))])
A, B, cA, cB = train_test_split(Xc, yc, test_size=0.3,
                                stratify=yc, random_state=0)
m2 = LinearSVC(C=1.0, max_iter=20000).fit(A, cA)
ZA = np.c_[A, A[:, 0] ** 2 + A[:, 1] ** 2]
ZB = np.c_[B, B[:, 0] ** 2 + B[:, 1] ** 2]
m3 = LinearSVC(C=1.0, max_iter=20000).fit(ZA, cA)
print("[6] 2B test=%.3f  3B test=%.3f"
      % (np.mean(m2.predict(B) == cB), np.mean(m3.predict(ZB) == cB)))

# ---- 7. Polinom cekirdek: (x.z+1)^2 = phi(x).phi(z) ----
def phi(x):
    x1, x2 = x
    r2 = np.sqrt(2.0)
    return np.array([1, r2 * x1, r2 * x2, x1 * x1, x2 * x2,
                     r2 * x1 * x2])


rng = np.random.default_rng(1)
mf = 0.0
for _ in range(1000):
    x, z = rng.normal(size=2), rng.normal(size=2)
    mf = max(mf, abs((x @ z + 1) ** 2 - phi(x) @ phi(z)))
print("[7] maks fark = %.2e" % mf)
x, z = np.array([1., 2.]), np.array([3., -1.])
print("[7] k(x,z)=", (x @ z + 1) ** 2,
      " phi(x).phi(z)=", round(phi(x) @ phi(z), 10))

# ---- 8. Mercer: Gram ozdegerleri ----
xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
Krbf = rbf_kernel(xs[:, None], gamma=1.0)
Kbad = -(xs[:, None] - xs[None, :]) ** 2
e1 = np.sort(np.linalg.eigvalsh(Krbf))[::-1]
e2 = np.sort(np.linalg.eigvalsh(Kbad))[::-1]
print("[8] RBF ozdegerler:", np.round(e1, 5))
print("[8] -(x-z)^2 ozdeger:", np.round(e2, 4) + 0.0)
print("[8] iz =", round(float(np.trace(Kbad)), 4))
csv_yaz("b60_mercer.csv", ["sira", "rbf", "gecersiz"],
        [[i + 1, e1[i], e2[i]] for i in range(len(xs))])

# ---- 9. RBF gamma x C izgarasi (moons) ----
Xm, ym = make_moons(n_samples=200, noise=0.25, random_state=0)
ym = 2 * ym - 1.0
A, B, cA, cB = train_test_split(Xm, ym, test_size=0.3,
                                stratify=ym, random_state=0)
with open(os.path.join("veri", "b60_moons.csv"), "w") as f:
    f.write("x1,x2,y,egitim\n")
    for X_, y_, e in [(A, cA, 1), (B, cB, 0)]:
        for (a, b), c in zip(X_, y_):
            f.write("%.4f,%.4f,%d,%d\n" % (a, b, int(c), e))
gx = np.linspace(-2.0, 3.0, 40)
gy = np.linspace(-1.5, 2.0, 40)
GX, GY = np.meshgrid(gx, gy)
grid = np.c_[GX.ravel(), GY.ravel()]
izg, skor = [], []
print("[9] RBF izgarasi (test: 5 tohum ortalamasi)")
for g in [0.1, 1.0, 10.0]:
    for Cv in [0.1, 1.0, 100.0]:
        m = SVC(kernel="rbf", gamma=g, C=Cv).fit(A, cA)
        f = m.decision_function(grid)
        izg += [[g, Cv, round(a, 4), round(b, 4), round(c, 4)]
                for (a, b), c in zip(grid, f)]
        tr, te = [], []
        for sd in range(5):
            P, Q, cP, cQ = train_test_split(
                Xm, ym, test_size=0.3, stratify=ym, random_state=sd)
            mm = SVC(kernel="rbf", gamma=g, C=Cv).fit(P, cP)
            tr.append(np.mean(mm.predict(P) == cP))
            te.append(np.mean(mm.predict(Q) == cQ))
        skor.append([g, Cv, round(np.mean(tr), 4),
                     round(np.mean(te), 4), round(np.std(te), 4),
                     m.n_support_.sum()])
        print("  g=%g C=%g egitim=%.3f test=%.3f+-%.3f SV=%d"
              % (g, Cv, np.mean(tr), np.mean(te), np.std(te),
                 m.n_support_.sum()))
csv_yaz("b60_rbf_izgara.csv", ["gamma", "C", "gx", "gy", "f"], izg)
csv_yaz("b60_rbf_skor.csv",
        ["gamma", "C", "egitim", "test_ort", "test_sd", "sv"], skor)

# ---- 10. Kernel ridge: sifirdan ve sklearn ----
rng = np.random.default_rng(0)
Xr = np.sort(rng.uniform(0, 6, 80))[:, None]
yr = np.sin(Xr[:, 0]) + 0.1 * rng.normal(size=80)
Kr = rbf_kernel(Xr, gamma=0.5)
al = krr_fit(Kr, yr, 0.1)
kr = KernelRidge(alpha=0.1, kernel="rbf", gamma=0.5).fit(Xr, yr)
print("[10] KRR max fark = %.2e"
      % np.abs(krr_tahmin(Kr, al) - kr.predict(Xr)).max())

# ---- 11. Egitim suresi ve n ----
print("[11] SVC(rbf) egitim suresi")
rows = []
for n in [500, 1000, 2000, 4000, 8000]:
    X, y = make_classification(n_samples=n, n_features=20,
                               n_informative=10, random_state=0)
    ts = []
    for _ in range(3 if n <= 2000 else 1):
        t0 = time.time()
        m = SVC(kernel="rbf", C=1.0, gamma="scale").fit(X, y)
        ts.append(time.time() - t0)
    rows.append([n, round(float(np.median(ts)), 4),
                 int(m.n_support_.sum()), round(8 * n * n / 1e6, 1)])
    print("  n=%d sure=%.4fs SV=%d Gram=%.1fMB" % tuple(rows[-1]))
ln_n = np.log([r[0] for r in rows])
ln_t = np.log([r[1] for r in rows])
print("  egim(tum)=%.3f egim(n<=4000)=%.3f"
      % (np.polyfit(ln_n, ln_t, 1)[0],
         np.polyfit(ln_n[:4], ln_t[:4], 1)[0]))
csv_yaz("b60_olcek_sure.csv", ["n", "sure_s", "sv", "gram_mb"], rows)

# ---- 12. Rastgele Fourier oznitelikleri ----
A, _, _, _ = train_test_split(Xb, yb, test_size=0.3,
                              stratify=yb, random_state=0)
sc = StandardScaler().fit(A)
Z = sc.transform(A)[:200]
gam = 1.0 / Z.shape[1]
Kex = rbf_kernel(Z, gamma=gam)
rows = []
print("[12] RFF yaklasim hatasi (en buyuk mutlak fark)")
for D in [5, 10, 25, 50, 100, 250, 500, 1000, 2000]:
    eb, es = [], []
    for sd in range(5):
        W, bb = rff_olustur(Z.shape[1], D, gam, seed=sd)
        Phi = rff_donustur(Z, W, bb)
        eb.append(np.abs(Phi @ Phi.T - Kex).max())
        rs = RBFSampler(gamma=gam, n_components=D, random_state=sd)
        P = rs.fit(Z).transform(Z)
        es.append(np.abs(P @ P.T - Kex).max())
    rows.append([D, round(np.mean(eb), 5), round(np.std(eb), 5),
                 round(np.mean(es), 5), round(np.std(es), 5)])
    print("  D=%d bizim=%.5f+-%.5f sk=%.5f+-%.5f" % tuple(rows[-1]))
csv_yaz("b60_rff.csv",
        ["D", "bizim_ort", "bizim_sd", "sklearn_ort", "sklearn_sd"],
        rows)
print("[12b] RFF ile siniflandirma (gamma=1/30)")
for D in [10, 50, 200, 1000]:
    acc = []
    for sd in range(5):
        A, B, cA, cB = train_test_split(Xb, yb, test_size=0.3,
                                        stratify=yb, random_state=sd)
        sc = StandardScaler().fit(A)
        A2, B2 = sc.transform(A), sc.transform(B)
        W, bb = rff_olustur(A2.shape[1], D, gam, seed=sd)
        m = LinearSVC(C=1.0, max_iter=20000).fit(
            rff_donustur(A2, W, bb), cA)
        acc.append(np.mean(m.predict(rff_donustur(B2, W, bb)) == cB))
    print("  D=%d test=%.4f+-%.4f" % (D, np.mean(acc), np.std(acc)))
ex = []
for sd in range(5):
    A, B, cA, cB = train_test_split(Xb, yb, test_size=0.3,
                                    stratify=yb, random_state=sd)
    sc = StandardScaler().fit(A)
    ex.append(np.mean(SVC(kernel="rbf", gamma=gam, C=1.0)
                      .fit(sc.transform(A), cA)
                      .predict(sc.transform(B)) == cB))
print("  tam RBF SVC test=%.4f+-%.4f" % (np.mean(ex), np.std(ex)))

# ---- 13. Olcekleme etkisi (RBF SVC, 10 tohum) ----
ham, olc = [], []
for sd in range(10):
    Xtr, Xte, ytr, yte = train_test_split(
        Xb, yb, test_size=0.3, stratify=yb, random_state=sd)
    ham.append(np.mean(SVC(C=1).fit(Xtr, ytr).predict(Xte) == yte))
    sc = StandardScaler().fit(Xtr)
    olc.append(np.mean(SVC(C=1).fit(sc.transform(Xtr), ytr)
                       .predict(sc.transform(Xte)) == yte))
print("[13] olceksiz=%.4f+-%.4f olcekli=%.4f+-%.4f"
      % (np.mean(ham), np.std(ham), np.mean(olc), np.std(olc)))
csv_yaz("b60_olcekleme.csv", ["tohum", "olceksiz", "olcekli"],
        [[s, round(ham[s], 4), round(olc[s], 4)] for s in range(10)])

# ---- 14. Rakamlar: OvO (SVC) vs OvR (LinearSVC) ----
dg = load_digits()
A, B, cA, cB = train_test_split(dg.data, dg.target, test_size=0.3,
                                stratify=dg.target, random_state=0)
sc = StandardScaler().fit(A)
A, B = sc.transform(A), sc.transform(B)
svc = SVC(kernel="rbf", C=1.0, gamma="scale").fit(A, cA)
lsv = LinearSVC(C=1.0, max_iter=20000).fit(A, cA)
print("[14] SVC(rbf) test=%.4f  LinearSVC(OvR) test=%.4f"
      % (np.mean(svc.predict(B) == cB),
         np.mean(lsv.predict(B) == cB)))
print("  ikili siniflandirici: OvO=45, OvR=10")

# ---- 15. Dengesiz veri: class_weight ----
print("[15] dengesiz veri (95/5), lineer SVC, 5 tohum")
ba0, ba1, r0, r1 = [], [], [], []
for sd in range(5):
    X, y = make_classification(n_samples=3000, n_features=10,
                               weights=[0.95, 0.05], flip_y=0.01,
                               class_sep=0.8, random_state=sd)
    A, B, cA, cB = train_test_split(X, y, test_size=0.3,
                                    stratify=y, random_state=sd)
    sc = StandardScaler().fit(A)
    A, B = sc.transform(A), sc.transform(B)
    m0 = SVC(kernel="linear", C=1.0).fit(A, cA)
    m1 = SVC(kernel="linear", C=1.0,
             class_weight="balanced").fit(A, cA)
    ba0.append(balanced_accuracy_score(cB, m0.predict(B)))
    ba1.append(balanced_accuracy_score(cB, m1.predict(B)))
    r0.append(np.mean(m0.predict(B)[cB == 1] == 1))
    r1.append(np.mean(m1.predict(B)[cB == 1] == 1))
print("  agirliksiz dengeli=%.4f+-%.4f geri-cagirma=%.4f"
      % (np.mean(ba0), np.std(ba0), np.mean(r0)))
print("  balanced   dengeli=%.4f+-%.4f geri-cagirma=%.4f"
      % (np.mean(ba1), np.std(ba1), np.mean(r1)))
