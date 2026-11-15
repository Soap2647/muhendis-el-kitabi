# -*- coding: utf-8 -*-
"""
Bölüm 70 - Skip-gram + negatif örnekleme (word2vec, Mikolov 2013),
sıfırdan NumPy.
Öğrenilen giriş gömmeleri: v (merkez), çıktı gömmeleri: u (bağlam).
Çıktılar: engine/veri/b70_gomme_pca.csv, konsol: en yakın komşular."""

import csv, os, re
from collections import Counter
import numpy as np

K = os.path.dirname(os.path.abspath(__file__))
VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
rng = np.random.default_rng(0)
metin = open(
    os.path.join(K, "korpus_egitim.txt"), encoding="utf-8"
).read()
kelimeler = re.findall(
    r"\w+", metin.replace("İ", "i").replace("I", "ı").lower()
)
say = Counter(kelimeler)
sozluk = [w for w, c in say.most_common() if c >= 5]
dizin = {w: i for i, w in enumerate(sozluk)}
seq = np.array([dizin[w] for w in kelimeler if w in dizin])
Vw, D, PENCERE, NEG, EPOK, BATCH, LR = (
    len(sozluk),
    100,
    2,
    5,
    5,
    1024,
    0.01,
)
print("sözcük=%d sözlük(min5)=%d boyut=%d" % (len(kelimeler), Vw, D))
v = (rng.random((Vw, D)) - 0.5) / D
u = np.zeros((Vw, D))
p_neg = np.array([say[w] for w in sozluk], dtype=float) ** 0.75
p_neg /= p_neg.sum()
sig = lambda z: 1 / (1 + np.exp(-np.clip(z, -30, 30)))
for ep in range(EPOK):
    # Çiftler: her (merkez, bağlam) çifti, ±PENCERE içinde
    ms, cs = [], []
    for off in range(1, PENCERE + 1):
        ms += [seq[:-off], seq[off:]]
        cs += [seq[off:], seq[:-off]]
    M = np.concatenate(ms)
    C = np.concatenate(cs)
    sira = rng.permutation(len(M))
    M, C = M[sira], C[sira]
    kayip, n = 0.0, 0
    lr = LR * (1 - ep / EPOK)
    for i in range(0, len(M), BATCH):
        mc, oc = M[i : i + BATCH], C[i : i + BATCH]
        neg = rng.choice(Vw, size=(len(mc), NEG), p=p_neg)
        vc = v[mc]  # (B, D)
        uo = u[oc]  # (B, D)
        un = u[neg]  # (B, K, D)
        s_pos = sig(np.sum(vc * uo, 1))  # σ(u_o · v_c)
        s_neg = sig(np.einsum("bd,bkd->bk", vc, un))  # σ(u_n · v_c)
        g_pos = (s_pos - 1)[:, None]
        g_neg = s_neg[:, :, None]
        grad_v = g_pos * uo + np.sum(g_neg * un, 1)
        grad_uo = g_pos * vc
        grad_un = g_neg * vc[:, None, :]
        np.add.at(v, mc, -lr * grad_v)
        np.add.at(u, oc, -lr * grad_uo)
        np.add.at(u, neg.reshape(-1), -lr * grad_un.reshape(-1, D))
        kayip += (
            -np.log(s_pos + 1e-10).sum()
            - np.log(1 - s_neg + 1e-10).sum()
        )
        n += len(mc)
    print(
        "epoch %d  ortalama kayıp/çift=%.4f  (lr=%.4f)"
        % (ep + 1, kayip / n, lr)
    )
np.save(os.path.join(K, "gomme_v.npy"), v)
json_sozluk = sozluk
open(
    os.path.join(K, "gomme_sozluk.txt"), "w", encoding="utf-8"
).write("\n".join(sozluk))

# Ortak yönü çıkar (anizotropi): ortalama vektörü düş, sonra normalize
# et
vm = v - v.mean(0)
norm = vm / np.linalg.norm(vm, axis=1, keepdims=True)


def komsu(w, k=6):
    i = dizin[w]
    s = norm @ norm[i]
    s[i] = -1
    idx = np.argsort(-s)[:k]
    return [(sozluk[j], round(float(s[j]), 3)) for j in idx]


for w in [
    "model",
    "gömme",
    "kayıp",
    "dikkat",
    "tokenizasyon",
    "kelime",
    "sinir",
    "eğitim",
]:
    if w in dizin:
        print("%-14s -> %s" % (w, komsu(w)))
    else:
        print("%-14s sözlükte yok" % w)

# PCA (SVD) ile 2B izdüşüm: en sık 120 sözcük
ilk = 120
X = norm[:ilk] - norm[:ilk].mean(0)
U, S, Vt = np.linalg.svd(X, full_matrices=False)
Z = X @ Vt[:2].T
oran = (S[:2] ** 2).sum() / (S**2).sum()
print("PCA ilk iki bileşen açıklanan varyans = %.3f" % oran)
with open(
    os.path.join(VERI, "b70_gomme_pca.csv"),
    "w",
    encoding="utf-8",
    newline="",
) as f:
    cw = csv.writer(f)
    cw.writerow(["sozcuk", "x", "y"])
    for j in range(ilk):
        cw.writerow(
            [
                sozluk[j],
                round(float(Z[j, 0]), 5),
                round(float(Z[j, 1]), 5),
            ]
        )
