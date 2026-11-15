# -*- coding: utf-8 -*-
"""Bölüm 70 - Kelime torbası ve TF-IDF, sıfırdan; sklearn ile eşleşme;
aynı görev için TF-IDF + lojistik regresyon (baseline)."""

import json, math, os, re
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

K = os.path.dirname(os.path.abspath(__file__))
par = json.load(
    open(os.path.join(K, "paragraflar.json"), encoding="utf-8")
)
bol = json.load(
    open(os.path.join(K, "bolum_bolme.json"), encoding="utf-8")
)


def kucuk(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def belirtec(s):
    return re.findall(r"(?u)\b\w\w+\b", kucuk(s))


tr_m = [par[i]["metin"] for i in bol["egitim"]]
te_m = [par[i]["metin"] for i in bol["test"]]
ytr = np.array([par[i]["kisim"] for i in bol["egitim"]])
yte = np.array([par[i]["kisim"] for i in bol["test"]])


# --- Sıfırdan kelime torbası + TF-IDF (sklearn varsayılanı: smooth
# idf, l2) ---
def tfidf_fit(docs):
    kelimeler = sorted({w for d in docs for w in set(belirtec(d))})
    dizin = {w: j for j, w in enumerate(kelimeler)}
    n = len(docs)
    df = Counter(w for d in docs for w in set(belirtec(d)))
    idf = np.array(
        [math.log((1 + n) / (1 + df[w])) + 1 for w in kelimeler]
    )
    return dizin, idf


def tfidf_donustur(docs, dizin, idf):
    X = np.zeros((len(docs), len(dizin)))
    for i, d in enumerate(docs):
        for w, c in Counter(belirtec(d)).items():
            if w in dizin:
                X[i, dizin[w]] = c
    X = X * idf
    norm = np.sqrt((X**2).sum(1, keepdims=True))
    return X / np.where(norm == 0, 1, norm)


dizin, idf = tfidf_fit(tr_m)
Xtr = tfidf_donustur(tr_m, dizin, idf)
Xte = tfidf_donustur(te_m, dizin, idf)
vec = TfidfVectorizer(
    token_pattern=r"(?u)\b\w\w+\b", preprocessor=kucuk
)
Str = vec.fit_transform(tr_m).toarray()
Ste = vec.transform(te_m).toarray()
print(
    "sözlük: sıfırdan=%d sklearn=%d"
    % (len(dizin), len(vec.vocabulary_))
)
# Sütun sırası farklı olabilir: sklearn sözlüğüyle hizala
sira = [
    dizin[w]
    for w, _ in sorted(vec.vocabulary_.items(), key=lambda t: t[1])
]
A = Xtr[:, sira]
print(
    "eğitim matrisi maks. mutlak fark = %.2e" % np.abs(A - Str).max()
)
print(
    "sınama  matrisi maks. mutlak fark = %.2e"
    % np.abs(Xte[:, sira] - Ste).max()
)
print(
    "seyreklik (sıfır oranı, eğitim) = %.4f" % (1 - (Str > 0).mean())
)

# --- Baseline sınıflandırıcı ---
ayrik = np.bincount(ytr, minlength=15).argmax()
print(
    "çoğunluk sınıfı baseline: test doğruluk=%.4f"
    % accuracy_score(yte, np.full_like(yte, ayrik))
)
lr = LogisticRegression(C=10.0, max_iter=3000)
lr.fit(Str, ytr)
tah = lr.predict(Ste)
print(
    "TF-IDF + lojistik (C=10): test doğruluk=%.4f  makro-F1=%.4f"
    % (accuracy_score(yte, tah), f1_score(yte, tah, average="macro"))
)
print(
    "eğitim doğruluğu (bilgi amaçlı, eğitim skoru)=%.4f"
    % lr.score(Str, ytr)
)
