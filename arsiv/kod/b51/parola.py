# parola.py: parola entropisi H = L log2(N) (düzgün, bağımsız seçim)
# ve varsayımsal bir saldırganın tüm uzayı tarama süresi.
import math

HIZ = 1e10   # varsayımsal tahmin hızı: saniyede 10^10 deneme

def entropi_bit(uzunluk, alfabe):
    return uzunluk * math.log2(alfabe)

def ortalama_sure_yil(bit):
    # Ortalama: uzayın yarısını tarama (2^bit / 2 deneme)
    saniye = 2 ** bit / 2 / HIZ
    return saniye / (365.25 * 24 * 3600)

def main():
    ornekler = [
        ("8 küçük harf (a-z)", 8, 26),
        ("8 harf+rakam (a-zA-Z0-9)", 8, 62),
        ("12 yazdırılabilir ASCII", 12, 95),
        ("6 kelime, 7776'lık liste", 6, 7776),
    ]
    print("%-28s %8s %10s" % ("parola", "bit", "yil"))
    for ad, n, a in ornekler:
        b = entropi_bit(n, a)
        print("%-28s %8.1f %10.3g" % (ad, b, ortalama_sure_yil(b)))


if __name__ == "__main__":
    main()
