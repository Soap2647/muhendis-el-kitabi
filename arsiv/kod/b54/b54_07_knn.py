import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier

def knn_tahmin(X_tr, y_tr, X_te, k):
    # Tum uzakliklar: (n_test, n_train) matrisi
    D = np.sqrt(((X_te[:, None, :] - X_tr[None, :, :]) ** 2).sum(-1))
    komsu = np.argsort(D, axis=1)[:, :k]    # en yakin k komsu
    oy = y_tr[komsu].mean(axis=1)           # ikili oylama
    return (oy >= 0.5).astype(int)          # k tek ise berabere yok

def olcekle(X_tr, X_te):
    # Olcekleyici yalnizca egitim kismindan ogrenir
    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    return (X_tr - mu) / sd, (X_te - mu) / sd

veri = load_breast_cancer()
X_tr, _, y_tr, _ = train_test_split(
    veri.data, veri.target, test_size=0.2, stratify=veri.target,
    random_state=54)

# k secimi: sadece egitim verisinde 5 katli CV
cv = StratifiedKFold(5, shuffle=True, random_state=54)
print("k   CV dogruluk (sifirdan)")
skor = {}
for k in range(1, 32, 2):
    dogru = []
    for tr, va in cv.split(X_tr, y_tr):
        A, B = olcekle(X_tr[tr], X_tr[va])   # kat-ici olcekleme
        tahmin = knn_tahmin(A, y_tr[tr], B, k)
        dogru.append(np.mean(tahmin == y_tr[va]))
    skor[k] = np.mean(dogru)
    print("%2d  %.4f" % (k, skor[k]))
k_en_iyi = max(skor, key=skor.get)
print("secilen k:", k_en_iyi)

# Dogrulama: sklearn ile ayni tahminler mi?
A, B = olcekle(X_tr, X_tr)
sk = KNeighborsClassifier(n_neighbors=k_en_iyi).fit(A, y_tr)
ayni = np.mean(knn_tahmin(A, y_tr, B, k_en_iyi) == sk.predict(B))
print("sifirdan ve sklearn tahmin uyumu:", ayni)
