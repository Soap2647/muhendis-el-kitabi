# kl_ce.py: çapraz entropi, KL ıraksaması, asimetri, perplexity
# ve iki Gauss arasındaki KL'nin kapalı biçimi (VAE'deki terim).
import math
import random

def entropi(p):
    return -sum(x * math.log2(x) for x in p if x > 0)

def capraz(p, q):
    # H(p, q) = -sum p log2 q. q = 0 ve p > 0 ise sonsuz.
    t = 0.0
    for x, y in zip(p, q):
        if x > 0:
            if y == 0:
                return math.inf
            t -= x * math.log2(y)
    return t

def kl(p, q):
    # D_KL(p || q) = sum p log2(p/q) = H(p,q) - H(p)
    t = 0.0
    for x, y in zip(p, q):
        if x > 0:
            if y == 0:
                return math.inf
            t += x * math.log2(x / y)
    return t

def gauss_kl_nat(mu, sigma):
    # KL(N(mu, s^2) || N(0,1)) = 0.5 (s^2 + mu^2 - 1 - ln s^2), nat
    s2 = sigma * sigma
    return 0.5 * (s2 + mu * mu - 1.0 - math.log(s2))

def gauss_kl_sayisal(mu, sigma, aralik=12.0, n=200000):
    # Aynı integrali dikdörtgen kuralıyla sayısal olarak hesapla.
    def pdf(x, m, s):
        ust = math.exp(-0.5 * ((x - m) / s) ** 2)
        return ust / (s * math.sqrt(2 * math.pi))
    h = 2 * aralik / n
    t = 0.0
    for i in range(n):
        x = -aralik + (i + 0.5) * h
        p = pdf(x, mu, sigma)
        q = pdf(x, 0.0, 1.0)
        if p > 0:
            t += p * math.log(p / q) * h
    return t

def main():
    p = [0.9, 0.1]
    q = [0.5, 0.5]
    print("KL(p||q) = %.4f bit" % kl(p, q))
    print("KL(q||p) = %.4f bit" % kl(q, p))
    # Sıfır olasılık: q'da olmayan olay p'de varsa KL sonsuz olur.
    print("KL([0.5,0.5] || [1,0]) = %s" % kl([0.5, 0.5], [1.0, 0.0]))
    print("KL([1,0] || [0.5,0.5]) = %.4f"
          % kl([1.0, 0.0], [0.5, 0.5]))
    # Çapraz entropi = H(p) + KL(p||q)
    print("H(p)=%.4f  H(p,q)=%.4f  H(p)+KL=%.4f" % (
        entropi(p), capraz(p, q), entropi(p) + kl(p, q)))
    # Sıfır kütleli destek: forward ve reverse KL asimetrisi
    p2 = [0.5, 0.5, 0.0, 0.0]          # destek: 1. ve 2. sınıf
    q_tek = [1.0, 0.0, 0.0, 0.0]       # yalnızca 1. sınıfta
    q_kapsa = [0.5, 0.4, 0.1, 0.0]     # destekte yayılır
    print("KL(p||tek)   = %s" % kl(p2, q_tek))
    print("KL(tek||p)   = %.4f" % kl(q_tek, p2))
    print("KL(p||kapsa) = %.4f" % kl(p2, q_kapsa))
    print("KL(kapsa||p) = %s" % kl(q_kapsa, p2))
    # Gibbs eşitsizliği: 2000 rastgele çift için KL < 0 olmamalı.
    rnd = random.Random(51)
    en_kucuk = math.inf
    for _ in range(2000):
        a = [rnd.random() + 1e-9 for _ in range(4)]
        b = [rnd.random() + 1e-9 for _ in range(4)]
        sa, sb = sum(a), sum(b)
        a = [v / sa for v in a]
        b = [v / sb for v in b]
        en_kucuk = min(en_kucuk, kl(a, b))
    print("2000 rastgele cift, en kucuk KL = %.2e" % en_kucuk)
    # Gauss KL: kapalı biçim ile sayısal integral karşılaştırması
    for mu, s in [(0.0, 1.0), (1.5, 0.7), (-0.8, 2.0)]:
        kap = gauss_kl_nat(mu, s)
        say = gauss_kl_sayisal(mu, s)
        print("N(%.1f, %.1f^2): kapali=%.6f sayisal=%.6f nat" % (
            mu, s, kap, say))
    # Perplexity: 2^H; 50 000 kelimelik düzgün model
    print("perplexity (duzgun, 50000): %.0f" % 2 ** math.log2(50000))
    print("perplexity (3.0 bit/simge):  %.1f" % 2 ** 3.0)


if __name__ == "__main__":
    main()
