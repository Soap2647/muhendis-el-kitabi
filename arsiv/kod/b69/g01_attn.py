# -*- coding: utf-8 -*-
"""Bölüm 69 - Ölçekli nokta çarpımı attention, sıfırdan (NumPy)."""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # bu bölümde yalnızca CPU
import csv
import numpy as np
import torch
import torch.nn.functional as F

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
np.set_printoptions(precision=4, suppress=True)


def softmax(z, eksen=-1):
    z = z - z.max(axis=eksen, keepdims=True)  # taşmayı önler
    e = np.exp(z)
    return e / e.sum(axis=eksen, keepdims=True)


def attention(Q, K, V, maske=None):
    """softmax(QK^T/sqrt(d_k)) V; maske False -> -inf."""
    dk = Q.shape[-1]
    S = Q @ np.swapaxes(K, -1, -2) / np.sqrt(dk)
    if maske is not None:
        S = np.where(maske, S, -np.inf)
    A = softmax(S, eksen=-1)
    return A @ V, A


def ornek_uc_token():
    print("--- 3 token, d_k = 2 ---")
    Q = np.array([[1, 0], [0, 1], [1, 1]], float)
    K = Q.copy()
    V = np.array([[1, 2], [3, 4], [5, 6]], float)
    print("QK^T =")
    print(Q @ K.T)
    out, A = attention(Q, K, V)
    print("A =")
    print(A)
    print("cikti =")
    print(out)


def sekiller():
    print("--- boyutlar (B=2, T=3, d_k=4, d_v=5) ---")
    rng = np.random.default_rng(0)
    Q = rng.normal(size=(2, 3, 4))
    K = rng.normal(size=(2, 3, 4))
    V = rng.normal(size=(2, 3, 5))
    S = Q @ np.swapaxes(K, -1, -2)
    out, A = attention(Q, K, V)
    print("Q", Q.shape, "K", K.shape, "V", V.shape)
    print("QK^T", S.shape, "A", A.shape, "cikti", out.shape)
    print("her satirin toplami:", np.allclose(A.sum(-1), 1.0))


def torch_eslesme():
    print("--- NumPy ile PyTorch eslesmesi (float64) ---")
    rng = np.random.default_rng(1)
    Q, K, V = (rng.normal(size=(2, 5, 8)) for _ in range(3))
    t = lambda x: torch.tensor(x, dtype=torch.float64)
    out_np, _ = attention(Q, K, V)
    out_t = F.scaled_dot_product_attention(t(Q), t(K), t(V))
    print(
        "maks fark (maskesiz): %.2e"
        % np.abs(out_np - out_t.numpy()).max()
    )
    m = np.tril(np.ones((5, 5), bool))
    out_np, _ = attention(Q, K, V, m)
    out_t = F.scaled_dot_product_attention(
        t(Q), t(K), t(V), is_causal=True
    )
    print(
        "maks fark (nedensel): %.2e"
        % np.abs(out_np - out_t.numpy()).max()
    )


def dk_doyma():
    print("--- d_k'ye gore softmax doyması (T=16, 500 deneme) ---")
    rng = np.random.default_rng(0)
    T, N = 16, 500
    satirlar = []
    print("  d_k  std(ham)  maks_ham  maks_olcekli  H_olcekli/logT")
    for dk in [2, 8, 32, 128, 512]:
        Q = rng.normal(size=(N, T, dk))
        K = rng.normal(size=(N, T, dk))
        ham = Q @ np.swapaxes(K, -1, -2)
        olc = ham / np.sqrt(dk)
        Ah, Ao = softmax(ham), softmax(olc)
        std_ham = ham.std()
        mh = Ah.max(-1).mean()
        mo = Ao.max(-1).mean()
        H = -(Ao * np.log(Ao)).sum(-1).mean() / np.log(T)
        print(
            "%5d  %8.3f  %8.4f  %12.4f  %14.4f"
            % (dk, std_ham, mh, mo, H)
        )
        satirlar.append(
            [
                dk,
                "%.4f" % std_ham,
                "%.4f" % mh,
                "%.4f" % mo,
                "%.4f" % H,
            ]
        )
    return satirlar


if __name__ == "__main__":
    ornek_uc_token()
    sekiller()
    torch_eslesme()
    satirlar = dk_doyma()
    with open(
        os.path.join(VERI, "b69_dk_doyma.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(
            [
                "dk",
                "std_ham",
                "maks_olceksiz",
                "maks_olcekli",
                "entropi_olcekli",
            ]
        )
        w.writerows(satirlar)
