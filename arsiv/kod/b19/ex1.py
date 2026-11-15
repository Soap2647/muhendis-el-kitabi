# ex1.py: 3^13 mod 1000 hesabinin iz tablosu (Ornek 1)
def us_iz(x, n, m, derin=0):
    if n == 0:
        print("  " * derin + "n=0: sonuc = 1")
        return 1 % m
    yarim = us_iz(x, n // 2, m, derin + 1)
    kare = yarim * yarim % m
    sonuc = kare
    if n % 2 == 1:
        sonuc = kare * x % m
    print("  " * derin + "n=%d: yarim=%d kare=%d sonuc=%d"
          % (n, yarim, kare, sonuc))
    return sonuc


if __name__ == "__main__":
    print("3^13 mod 1000 (izli cagri):")
    s = us_iz(3, 13, 1000)
    print("sonuc =", s, "| pow ile =", pow(3, 13, 1000))
    assert s == pow(3, 13, 1000)
