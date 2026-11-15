# -*- coding: utf-8 -*-
# b62_03_hmm.py: Gizli Markov modeli sifirdan: ileri (olcekli),
# Viterbi (log-uzay), geri algoritma, Baum-Welch (EM); IHA ucus modu
# (kalkis / seyir / inis) sentetik verisi. Kaba kuvvet dogrulamasi.
import itertools
import numpy as np

# Gizli durumlar: 0 = kalkis, 1 = seyir, 2 = inis
# Gozlemler (irtifa degisimi): 0 = dusuyor, 1 = sabit, 2 = yukseliyor
PI = np.array([1.0, 0.0, 0.0])
A = np.array(
    [[0.70, 0.30, 0.00], [0.00, 0.97, 0.03], [0.30, 0.00, 0.70]]
)
B = np.array(
    [[0.20, 0.30, 0.50], [0.15, 0.70, 0.15], [0.60, 0.30, 0.10]]
)


def ornekle(T, pi, A, B, rng):
    """Once gizli durum dizisi, sonra gozlemler (sentetik veri)."""
    K, V = B.shape
    z = np.zeros(T, dtype=int)
    x = np.zeros(T, dtype=int)
    z[0] = rng.choice(K, p=pi)
    for t in range(1, T):
        z[t] = rng.choice(K, p=A[z[t - 1]])
    for t in range(T):
        x[t] = rng.choice(V, p=B[z[t]])
    return z, x


def ileri(obs, pi, A, B):
    """Olcekli ileri algoritma. alpha_hat[t] toplam 1'e normalize,
    c[t] olcek katsayisi; log P(x) = sum log c[t]."""
    T, K = len(obs), len(pi)
    alpha = np.zeros((T, K))
    c = np.zeros(T)
    alpha[0] = pi * B[:, obs[0]]
    c[0] = alpha[0].sum()
    alpha[0] /= c[0]
    for t in range(1, T):
        alpha[t] = (alpha[t - 1] @ A) * B[:, obs[t]]
        c[t] = alpha[t].sum()
        alpha[t] /= c[t]
    return alpha, c


def geri(obs, A, B, c):
    """Olcekli geri algoritma; ileri ile ayni olcekleri kullanir."""
    T, K = len(obs), A.shape[0]
    beta = np.zeros((T, K))
    beta[-1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = A @ (B[:, obs[t + 1]] * beta[t + 1]) / c[t + 1]
    return beta


def viterbi(obs, pi, A, B):
    """En olasi gizli yol. Log-uzay: toplam, carpim degil."""
    T, K = len(obs), len(pi)
    with np.errstate(divide="ignore"):
        lpi, lA, lB = np.log(pi), np.log(A), np.log(B)
    delta = np.zeros((T, K))
    psi = np.zeros((T, K), dtype=int)
    delta[0] = lpi + lB[:, obs[0]]
    for t in range(1, T):
        skor = delta[t - 1][:, None] + lA  # (onceki, sonraki)
        psi[t] = np.argmax(skor, axis=0)
        delta[t] = np.max(skor, axis=0) + lB[:, obs[t]]
    yol = np.zeros(T, dtype=int)
    yol[-1] = np.argmax(delta[-1])
    for t in range(T - 1, 0, -1):
        yol[t - 1] = psi[t, yol[t]]
    return yol, delta, psi


def kaba_kuvvet(obs, pi, A, B):
    """Tum K^T yolu tek tek dene: toplam olabilirlik ve en iyi yol."""
    T, K = len(obs), len(pi)
    toplam, en_iyi, en_yol = 0.0, -1.0, None
    for yol in itertools.product(range(K), repeat=T):
        p = pi[yol[0]] * B[yol[0], obs[0]]
        for t in range(1, T):
            p *= A[yol[t - 1], yol[t]] * B[yol[t], obs[t]]
        toplam += p
        if p > en_iyi:
            en_iyi, en_yol = p, yol
    return toplam, np.array(en_yol)


def baum_welch(obs, pi, A, B, iter_sayisi=80):
    """EM: E adimi (gamma, xi) ve M adimi (pi, A, B yeniden tahmini).
    Sifir olan gecisler sifir kalir (yapi korunur)."""
    obs = np.asarray(obs)
    K, V = B.shape
    log_olab = []
    for _ in range(iter_sayisi):
        alpha, c = ileri(obs, pi, A, B)
        beta = geri(obs, A, B, c)
        log_olab.append(np.sum(np.log(c)))
        gamma = alpha * beta
        gamma /= gamma.sum(axis=1, keepdims=True)
        T = len(obs)
        xi = np.zeros((T - 1, K, K))
        for t in range(T - 1):
            m = (
                alpha[t][:, None]
                * A
                * (B[:, obs[t + 1]] * beta[t + 1])[None, :]
            )
            xi[t] = m / m.sum()
        pi = gamma[0]
        A = xi.sum(axis=0) / gamma[:-1].sum(axis=0)[:, None]
        B_yeni = np.zeros((K, V))
        for v in range(V):
            B_yeni[:, v] = gamma[obs == v].sum(axis=0)
        B = B_yeni / gamma.sum(axis=0)[:, None]
    return pi, A, B, np.array(log_olab)


ISIM = ["kalkis", "seyir", "inis"]


def ornek3():
    """Kucuk iki durumlu ornek: tablo (delta, psi) ve geri izleme."""
    pi2 = np.array([0.6, 0.4])
    A2 = np.array([[0.7, 0.3], [0.4, 0.6]])
    B2 = np.array([[0.9, 0.1], [0.2, 0.8]])
    obs2 = [1, 0, 0]
    yol, delta, psi = viterbi(obs2, pi2, A2, B2)
    print("delta (log):\n", np.round(delta, 4))
    print("psi:\n", psi)
    print("en iyi yol:", yol.tolist())
    print("olasilik (dogru):", np.exp(delta[-1]).max().round(6))
    top, en = kaba_kuvvet(obs2, pi2, A2, B2)
    print(
        "kaba kuvvet en iyi yol:",
        en.tolist(),
        " P(x) toplam:",
        round(top, 6),
    )


def uav_deney():
    print("\n[IHA] egitim: T=3000 tohum 62, test: T=600 tohum 63")
    z8, x8 = ornekle(8, PI, A, B, np.random.default_rng(5))
    alpha, c = ileri(x8, PI, A, B)
    top, en = kaba_kuvvet(x8, PI, A, B)
    lp_ileri = round(np.sum(np.log(c)), 10)
    lp_kaba = round(np.log(top), 10)
    print("[dogrulama T=8] log P ileri:", lp_ileri)
    print("[dogrulama T=8] log P kaba:", lp_kaba)
    yol_v = viterbi(x8, PI, A, B)[0].tolist()
    print("[dogrulama T=8] viterbi:", yol_v)
    print("[dogrulama T=8] kaba kuvvet:", en.tolist())
    print("[dogrulama T=8] gercek:", z8.tolist())
    z_tr, x_tr = ornekle(3000, PI, A, B, np.random.default_rng(62))
    z_te, x_te = ornekle(600, PI, A, B, np.random.default_rng(63))
    vit = viterbi(x_te, PI, A, B)[0]
    naif = np.argmax(B[:, x_te], axis=0)
    print(
        "[Dogruluk] Viterbi:",
        round(np.mean(vit == z_te), 4),
        " gozlem basina en iyi durum (naif):",
        round(np.mean(naif == z_te), 4),
    )
    # Baum-Welch: yapisal sifirlar korunur, bozuk baslangic
    A0 = np.array(
        [[0.60, 0.40, 0.00], [0.00, 0.90, 0.10], [0.40, 0.00, 0.60]]
    )
    B0 = np.array(
        [[0.30, 0.40, 0.30], [0.25, 0.50, 0.25], [0.40, 0.35, 0.25]]
    )
    pi_h, A_h, B_h, ll = baum_welch(x_tr, PI, A0, B0, iter_sayisi=150)
    print("[BW] egitim: T=3000, 150 iterasyon, baslangic: A0, B0")
    print("[BW] log P(x) iterasyon boyunca (ilk 6 ve son):")
    print(
        "   ", np.round(ll[:4], 3).tolist(), "...", round(ll[-1], 3)
    )
    print("[BW] monoton artis:", bool(np.all(np.diff(ll) >= -1e-9)))
    print("[BW] ogrenilen A:\n", np.round(A_h, 3))
    print("[BW] ogrenilen B:\n", np.round(B_h, 3))
    vit2 = viterbi(x_te, pi_h, A_h, B_h)[0]
    print(
        "[BW] gercek dogruluk (gercek parametreler):",
        round(np.mean(viterbi(x_te, PI, A, B)[0] == z_te), 4),
    )
    print(
        "[BW] test dogrulugu (ogrenilen parametreler):",
        round(np.mean(vit2 == z_te), 4),
    )


if __name__ == "__main__":
    print("== Ornek 3 (iki durum, T=3) ==")
    ornek3()
    print("\n== IHA ucus modu HMM ==")
    uav_deney()
